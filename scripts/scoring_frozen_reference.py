"""Read-only mathematical reference for the frozen streetview scorer.

This is a publication companion, not a replacement production runner. It takes
already-fitted trusted estimator objects and aligned arrays; it has no fitting,
file-writing, model-loading, or API code. See docs/scoring_paper_methodology.md.
The probability decoder preserves the archived grid/local-search algorithm.
"""

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import ndtr

SCORE_LEVELS = np.arange(11) / 10
SAFETY_COLUMNS = (0, 4, 8)


def visual_scopes(features):
    """Eq. 2: rows must alternate canonical A, B for each point."""
    a, b = features[::2].astype(float), features[1::2].astype(float)
    return [np.c_[(a + b) / 2, abs(a - b)], a, b]


def decode_probabilities(probabilities, decoder):
    """Eqs. 8-10: local score classifier probabilities, never Flash logits."""
    if decoder['kind'] == 'mean':
        return np.clip(probabilities @ SCORE_LEVELS, 0, 1)
    assert decoder['kind'] == 'window'
    sigma = decoder['sigma']
    grid = np.linspace(0, 1, 201)
    mass = ndtr((grid[:, None] + .1 - SCORE_LEVELS) / sigma) - ndtr(
        (grid[:, None] - .1 - SCORE_LEVELS) / sigma
    )
    scores = probabilities @ mass.T
    centers = grid[np.argmax(scores, axis=1)]
    out = []
    for row, center in zip(probabilities, centers):
        def objective(value):
            return -float(row @ (
                ndtr((value + .1 - SCORE_LEVELS) / sigma)
                - ndtr((value - .1 - SCORE_LEVELS) / sigma)
            ))
        lo, hi = max(0, center - .01), min(1, center + .01)
        result = minimize_scalar(
            objective, bounds=(lo, hi), method='bounded',
            options={'xatol': 1e-10},
        )
        out.append(min([float(result.x), lo, hi], key=objective))
    return np.clip(out, 0, 1)


def score_probabilities(classifier, features):
    """Eq. 8: expand observed classes to the fixed 11-level score support."""
    probabilities = np.zeros((len(features), 11))
    if isinstance(classifier, dict):
        probabilities[:, classifier['constant']] = 1
    else:
        probabilities[:, classifier.classes_.astype(int)] = (
            classifier.predict_proba(features)
        )
    return probabilities


def pca_features(preprocess, visual, qwen):
    """Eq. 4: use the saved training-fitted PCA/imputer/scaler only."""
    scope = preprocess['stage']
    part = qwen[:, scope * 4:scope * 4 + 4]
    raw = np.c_[part, ~np.isfinite(part)]
    return preprocess['scaler'].transform(np.c_[
        preprocess['image'].transform(visual[scope]),
        preprocess['imputer'].transform(raw),
    ])


def predict_component(model, visual, qwen, column):
    """Eqs. 5-6: clipped Ridge, raw Flash, affine, or isotonic component."""
    family = model['cfg']['family']
    scope = column // 4
    if family in ['fusion', 'dino']:
        features = visual[scope]
        if family == 'fusion':
            part = qwen[:, scope * 4:scope * 4 + 4]
            features = np.c_[features, part, ~np.isfinite(part)]
        pred = model['regressor'].predict(
            model['preprocess'].transform(features)
        )
    else:
        part = qwen[:, column]
        valid = np.isfinite(part)
        pred = np.full(len(qwen), model['fallback_mean'])
        regressor = model['regressor']
        if family == 'qwen_raw':
            pred[valid] = part[valid]
        elif regressor is not None:
            inputs = part[valid, None] if family == 'qwen_affine' else part[valid]
            pred[valid] = regressor.predict(inputs)
    return np.clip(pred, 0, 1)


def predict_base(model, visual, qwen, column):
    """Eqs. 7, 11-12: recurse through the actual saved model tree."""
    if model['kind'] == 'old':
        return ((1 - model['weight'])
                * predict_component(model['base_model'], visual, qwen, column)
                + model['weight']
                * predict_component(model['candidate_model'], visual, qwen, column))
    base = predict_base(model['baseline_model'], visual, qwen, column)
    features = pca_features(model['preprocess'], visual, qwen)
    if model['kind'] == 'svr':
        candidate = np.clip(model['regressor'].predict(features), 0, 1)
    else:
        assert model['kind'] == 'probability_mix'
        candidate = decode_probabilities(
            score_probabilities(model['classifier'], features), model['decoder']
        )
    return (1 - model['weight']) * base + model['weight'] * candidate


def apply_safety_expert(model, visual_by_kind, qwen, column, base):
    """Eqs. 13-15: hard routing; preserve the base when below threshold."""
    if model['selected']['kind'] == 'baseline':
        return base.copy(), np.zeros(len(base), dtype=bool)
    preprocess = model['preprocess']
    scope = column // 4
    assert scope == preprocess['scope']
    part = qwen[:, scope * 4:scope * 4 + 4]
    raw = np.c_[part, ~np.isfinite(part)]
    features = preprocess['scaler'].transform(np.c_[
        preprocess['image'].transform(visual_by_kind[preprocess['features']][scope]),
        preprocess['imputer'].transform(raw),
    ])
    classifier = model['classifier']
    risk = classifier.predict_proba(features)[:, list(classifier.classes_).index(1)]
    routed = risk >= model['selected']['threshold']
    low = np.clip(model['expert'].predict(features), 0, .3)
    return np.where(routed, low, base), routed


def round_one_decimal(predictions):
    """Eq. 16: the archived half-up arithmetic, not bankers' rounding."""
    return np.floor(predictions * 10 + .5) / 10


def predict_frozen(base_models, safety_models, cls, cls_grid, qwen):
    """Replay frozen objects in the documented 12-column order, without fitting.

    base_models is a list of 12 fitted model dictionaries. safety_models maps
    columns 0, 4 and 8 to their fitted wrapper dictionaries. cls and cls_grid
    have 2*n rows in canonical A/B order; qwen is n*12 with raw NA as NaN.
    """
    visual = {'cls': visual_scopes(cls), 'grid': visual_scopes(cls_grid)}
    base = np.column_stack([
        predict_base(model, visual['cls'], qwen, column)
        for column, model in enumerate(base_models)
    ])
    final = base.copy()
    for column in SAFETY_COLUMNS:
        final[:, column], _ = apply_safety_expert(
            safety_models[column], visual, qwen, column, base[:, column]
        )
    return final, round_one_decimal(final)

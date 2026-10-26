# Streetview Analysis Pipeline

A pipeline for selecting study-area coordinates, identifying side-facing street views, validating image selections, scoring both sides with a frozen VLM/visual-feature mixture, and preparing paired street-side analysis.

**Image selection, 500-point validation and remaining-12,160-point scoring are
complete.** The final frozen scorer uses Flash v2, DINOv2, a supervised mixture
and three low-safety gates/experts. Deliver one-decimal scores and retain
continuous scores. A = selected 0/90-degree image; B = selected 180/270-degree
image throughout images, features and scores.

## Current Scoring Milestone

- [Paper-methods draft: full equations, all 12 model trees and implementation correspondence](docs/scoring_paper_methodology.md)
- [Final canonical method, training, parameters and freeze](docs/scoring_frozen_2026-10-25.md)
- [500-point validation: all 12 targets and raw Flash comparison](docs/validation500_2026-10-25.md)
- [12,160-point completion, local deliverables and independent audit](docs/full_scoring_2026-10-25.md)
- [Separate validation A/B matching diagnostic](docs/ab_dimension_diagnostic_2026-10-25.md)
- [Final component settings and artifact hashes](configs/scoring/flash_v2_dino_canonical_frozen.json)
- [Latest aggregate evidence](results/scoring_2026-10-25/)
- [Prompt and model iteration history](docs/scoring_iterations_2026-10-23.md)
- [Historical base and 200-point test](docs/scoring_method_2026-10-23.md)
- [Historical low-safety development experiment](docs/scoring_low_safety_extension_2026-10-23.md)

The 500-point validation has **405 numeric-reference points (4,860 items)** and
95 all-NA reference points. Fixed A/B automatic results, without diagnostic swaps:

| Frozen canonical output | Numeric pairs | Absolute error <=0.1 | MAE | Absolute error >=0.3 |
|---|---:|---:|---:|---:|
| Raw Flash v2 | 4,843 | 50.73% | 0.1651 | 22.22% |
| Final continuous (primary evaluation precision) | 4,860 | 63.60% | 0.0865 | 2.16% |
| Final one decimal (selected delivery format) | 4,860 | 84.61% | 0.0761 | 3.60% |

Raw Flash has 17 NA items on numeric references; the validation report also
compares the same 4,843 numeric pairs. Rounding changes threshold decisions and
raises both the tolerance hit rate and large-error rate. The historical >70%
continuous hit-rate aspiration is not met by this validation. These are empirical
agreement metrics, not confidence probabilities or exact-match accuracy.

Development/validation point IDs are disjoint, but four image hashes at two
validation points overlap development; all 500 points were retained. The final
canonical model's development regression check also found 16 more rounded large
errors than the earlier noncanonical expert scheme. Both limitations are recorded;
historical 200-point base results are not reassigned to this extension.

The final model was fitted on 488 development points and then reused unchanged
for the 500-point validation and the remaining 12,160 points. The full batch has
**145,920 finite scores per precision**, with canonical identities, frozen files,
forward inference and every delivered value independently verified. No batch
reference scores, retraining or reference-guided A/B matching entered inference.

Images, per-point outputs and fitted coefficients remain private. This public
repository records methods, prompt fragments, hyperparameters, hashes and aggregate
evidence; it is not a turnkey reproduction package or a public data release.

## Earlier Milestones

The final center-point selection and local team handoff are complete under the user's acceptance policy. See the [October 13 milestone report](docs/milestone_2026-10-13.md) for final counts, review decisions, validation, and delivery scope. The data-bearing handoff package is not published in this repository.

The [October 20 VLM pilot report](docs/vlm_pilot_2026-10-20.md) records model options,
versioned prompts, compact versus verbose output, observed token costs, and known
scoring failures. Qwen3.8 Flash is the next-test candidate from a three-point
comparison at that stage, not a validated winner from that pilot. Prior AI-assisted reference scores are not
independent human ground truth. VLM inference uses a cloud API; image-selection
inference remains local.

The [organized-rubric follow-up](docs/vlm_organized_pilot_2026-10-20.md) archives
`v2_organized`, PDF page checks, and a matched v1/v2 comparison. It showed no
consistent gain on the three debugging points; visual grounding and rule
application errors both remain. The next experiments separate those failure
sources rather than assuming cleaner PDF text guarantees better scores.

## Task and Deliverables

Each location has four images named `longitude_latitude_angle_extra.png`, with angles of 0, 90, 180, and 270 degrees. The pipeline processes only coordinates in the study-area point list and selects two images facing the sides of the road.

The angles do not directly identify forward, backward, left, or right relative to the road. The model compares the opposing pairs 0/180 and 90/270; the annotation interface allows any two images to be selected. `side_a` and `side_b` are reference labels, not physical left/right directions.

The image-selection deliverables are a **selection manifest and an image-reading script**, with an optional private image package. Original archives are preserved. The completed scoring stage adds **continuous and one-decimal 12-target CSVs**, including canonical image names and angles; see the [completion record](docs/full_scoring_2026-10-25.md). These data-bearing deliverables remain local rather than being published here. Flash scoring uses a cloud API; DINO extraction and learned fusion run locally.

## Results

| Stage | Sample | Method | Result |
|---|---|---|---|
| Initial experiment | 50 locations | Zero-shot CLIP with opposing-pair selection | 44/50 agreement, 88%; annotation certainty was not systematically recorded |
| Fresh-sample validation | 100 locations | Fixed zero-shot CLIP baseline | Certain: 77/84, 91.7%; uncertain: 8/16, 50% |
| Classifier experiment | The 84 certain locations above | Frozen CLIP features plus logistic regression; five-fold validation grouped by location | Out-of-fold: 81/84, 96.4%; baseline: 77/84 |
| Independent holdout | 30 new locations, excluding the previous 150 locations and identical images | Frozen classifier trained on 84 locations | Certain: 24/25, 96%; uncertain: 2/5, 40% |
| Full center-point selection | 13,660 locations / 54,640 input images | Frozen classifier with human overrides and heuristic review flags | 27,320 references; 11,170 auto-selected locations, 110 human-confirmed, 2,380 needing review |

Agreement requires both selected images at a location to match the human selection, ignoring a/b order. Disagreements on uncertain annotations are not automatically definitive model errors. Small-sample performance does not guarantee full-dataset accuracy.

Full-run counts describe output coverage and review workload, not measured full-dataset accuracy. The inference run took approximately 10.4 minutes on the tested Mac; preparation, validation, and human review are additional work.

## Repository Structure

- `scripts/`: sampling, data inspection, the annotation server, feature extraction, training, evaluation, and image reading.
- `web/`: local annotation interfaces for the 50-, 100-, and 30-location rounds; no images or annotation data.
- `docs/methodology.md`: methods, validation splits, manifest fields, and limitations.
- `docs/iteration_log.md`: the actual experiment sequence, documented retrospectively rather than reconstructed as Git history.
- `docs/roadmap.md`: plans for full-dataset processing, review, and subsequent VLM analysis.
- `results/aggregate_metrics.json`: aggregate results without individual coordinates.
- `prompts/qwen_scoring/`: versioned scoring instructions and the compact response contract; private rubric text is supplied locally.
- `results/vlm_*_2026-10-20.json`: aggregate-only scoring pilot metrics and usage-based cost estimates.
- `results/scoring_2026-10-23/`: supervised development, prompt diagnostics, independent test and DINO-ablation aggregates.
- `configs/scoring/`: selected scoring method specification, component settings and output precision policy.

The experiment scripts retain fixed sample sizes and round-specific directories for traceability. They are not yet a general-purpose batch-processing product.

## Local Setup and Execution

The tested environment is Python 3.12 on an Apple M2 Pro with 16 GB of unified memory, using PyTorch MPS. CPU execution is available on other platforms, but dependency compatibility needs to be verified.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set your private workspace and the directory containing the four original ZIPs.
export STREETVIEW_WORKSPACE="$PWD/workspace"
export STREETVIEW_ARCHIVE_DIR="$STREETVIEW_WORKSPACE/raw"
python scripts/install_annotation_assets.py
# Replace this example filename with your actual study-area XLS filename.
python scripts/inspect_data.py --centers "$STREETVIEW_WORKSPACE/raw/center_points.xls"

# Round 1: sample locations, open the interface, and complete human annotation.
python scripts/prepare_sample.py
python scripts/annotation_server.py --port 8765 --open-browser
# In another terminal with the same environment variables, after annotation:
python scripts/evaluate_clip.py

# Round 2: predict before annotation; model answers remain hidden in the interface.
python scripts/prepare_validation100.py
python scripts/predict_validation100.py
STREETVIEW_ANNOTATION_DIR="$STREETVIEW_WORKSPACE/annotation100" \
  python scripts/annotation_server.py --port 8768 --open-browser
# After annotation:
python scripts/compare_validation100.py
python scripts/train_lightweight.py

# Round 3: independent holdout validation of the trained classifier.
python scripts/prepare_validation30.py
python scripts/predict_validation30.py
STREETVIEW_ANNOTATION_DIR="$STREETVIEW_WORKSPACE/annotation30" \
  python scripts/annotation_server.py --port 8769 --open-browser
# After annotation:
python scripts/compare_validation30.py
```

The first CLIP run downloads the official model weights. Subsequent scripts use the cached model, and inference runs locally. Reproducing the reported study metrics requires the private images and annotations; they are not included in a fresh workspace.

Image-reading examples:

```bash
python scripts/read_selected.py "$STREETVIEW_WORKSPACE/annotation30/annotations.csv"
python scripts/read_selected.py "$STREETVIEW_WORKSPACE/annotation30/annotations.csv" --output "$STREETVIEW_WORKSPACE/selected_images"
```

By default, the reader processes the two images in records with `status=confirmed` or `status=selected`. The latter denotes acceptance under the final-selection policy, not individual human verification. Provisional `needs_review` records in the original manifest require explicit inclusion or finalization before downstream use.

## Full-Dataset Selection

Once the local center-point manifest and frozen classifier are available:

```bash
python scripts/select_full_dataset.py
python scripts/validate_selection_manifest.py "$STREETVIEW_WORKSPACE/full_selection/selection_manifest.csv"
# Validate or read automatically selected images as well as human confirmations:
python scripts/read_selected.py "$STREETVIEW_WORKSPACE/full_selection/selection_manifest.csv" --include-auto
# Include review candidates only when explicitly needed for inspection:
python scripts/read_selected.py "$STREETVIEW_WORKSPACE/full_selection/review_manifest.csv" --include-review
```

Outputs are `selection_manifest.csv`, `review_manifest.csv`, `run_summary.json`, and a local SQLite checkpoint in the private workspace. Rerunning the same command resumes committed batches; changed model, input manifest, annotation files, or review settings require a new output directory. Identical image bytes reuse cached scores.

Each point receives two references. `confirmed` denotes a human-confirmed choice; `auto_selected` denotes an unreviewed model choice; `needs_review` denotes a provisional selection. A point enters review if the classifier pair margin is below the initial heuristic of 0.3, the classifier and fixed zero-shot baseline choose different pairs, or its existing human annotation is uncertain. This threshold is not a calibrated confidence guarantee and uses the classifier's score scale, not CLIP cosine similarity.

Certain choices in rounds 2 and 3 override the model. Round 1 did not systematically record certainty, so its annotations remain in review unless an explicit confirmation is listed in the private `annotation/explicit_certainty.json` file (an array of `road_level:point_id` strings). Original human candidates are preserved in the note field. For model selections, a/b follow ascending angle order; for confirmed annotations, they preserve click order. Neither convention denotes physical left/right.

Original filename extensions do not necessarily identify the actual encoding. The reader preserves original bytes; detect their image format before constructing MIME types for a future VLM API.

## Reviewing Flagged Locations

```bash
python scripts/review_server.py --port 8770
# Open http://127.0.0.1:8770/?batch=1
```

The review page streams all four original images from the ZIP archives, shows the classifier's two selections, and preselects them for confirmation or correction. Review reasons and original model badges remain visible. The 2,380-location queue is presented in 48 batches of up to 50 locations; the first batch follows manifest order rather than a new random sample.

Selections, notes, and confirmation status are saved locally in `review_workspace/labels.json`. Confirmed reviews generate `review_results.csv` and `selection_manifest_reviewed.csv`, applying human overrides to a copy of the full manifest. Unconfirmed drafts and uncertain choices remain provisional. Editing a previously confirmed selection revokes that override until it is confirmed again. Original prediction manifests remain unchanged.

The page supports image zoom, restoring model choices, changing batches, and exporting the updated full manifest. Use `STREETVIEW_REVIEW_DIR` to select another private progress directory. To validate the updated output:

```bash
python scripts/validate_selection_manifest.py "$STREETVIEW_WORKSPACE/review_workspace/selection_manifest_reviewed.csv"
```

## Blind Audit of Unflagged Selections

```bash
python scripts/sample_auto_validation.py
STREETVIEW_ANNOTATION_DIR="$STREETVIEW_WORKSPACE/annotation_auto50" \
  python scripts/annotation_server.py --port 8772 --open-browser
# After completing annotation:
python scripts/compare_auto_validation.py
```

This samples 50 unflagged `auto_selected` locations at random across the eligible pool, rather than assigning equal road-level quotas. Previously annotated or reviewed coordinates and byte-identical images are excluded. Existing classifier predictions are frozen separately and hidden from the labeling interface. Certain and uncertain annotations are evaluated separately. This audit measures agreement within the unflagged subset, not the entire dataset; 50 locations provide only an initial check.

For visual browsing without annotation, copy `web/prediction_browser/index.html` and `app.js` into the local sample directory, retaining its `style.css`. Start the annotation server with `STREETVIEW_PREDICTIONS_FILE` pointing to the matching frozen prediction JSON. The read-only page highlights the two model-selected images and supports navigation and zoom; it does not submit human labels. Once predictions are revealed, subsequent judgments are a visual review rather than a blind accuracy test.

## Final Selection Policy

After visual review, the user chose to retain existing model selections, including unreviewed flagged points, and apply only confirmed human modifications:

```bash
python scripts/finalize_selection.py
python scripts/read_selected.py "$STREETVIEW_WORKSPACE/final_selection/final_selection_manifest.csv"
```

This creates a separate final manifest with all 13,660 locations and 27,320 image references. The initial finalized snapshot applies one confirmed pair modification, records 28 reviewed choices that stayed unchanged, and retains 110 earlier human-confirmed selections. Draft and uncertain review edits do not replace existing choices.

All final records have `status=selected`, meaning accepted for use under this policy. `prior_status`, `original_review_reasons`, and `review_outcome` preserve provenance. Acceptance does not imply that every location was manually verified. Original prediction and review-progress files remain unchanged.

## Data Boundaries

For a portable handoff without installing the project, use `scripts/team_read_selected.py`. It uses only the Python standard library and requires an explicit `--archive-dir` path. The local delivery package renames it to `read_selected.py` and includes the manifest and English instructions.

To create an image-inclusive package for a team drive:

```bash
python scripts/package_selected_images.py --output "$STREETVIEW_WORKSPACE/deliverables/selected_images.zip"
```

This streams unchanged selected image bytes from the original ZIPs into a ZIP64 archive, grouped as `images/road_level_<level>/<point_id>/<original_filename>`. The final CSV and English usage instructions are included. No loose intermediate image copy is created; source sizes and CRCs are checked. The resulting image package stays local and is excluded from Git.

The public repository contains only code, methods, interface templates, and aggregate metrics. Original images, the study-area point table, coordinate manifests, human annotations, per-location predictions, image features, model weights, generated reports, and local environments are excluded.

This repository grants no redistribution rights to the original data. Models and dependencies remain subject to their respective terms.

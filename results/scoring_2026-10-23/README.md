# Aggregate scoring evidence

> Historical experiment archive. Current canonical refit, validation and full
> completion evidence is in [scoring_2026-10-25](../scoring_2026-10-25/).

These files contain aggregate metrics only. No image, coordinate, per-point
reference score, prediction row, split membership or fitted model is published.
Source experiment names and SHA-256 hashes link each extract to a local artifact
without publishing its absolute path. See the [method report](../../docs/scoring_method_2026-10-23.md)
and [iteration history](../../docs/scoring_iterations_2026-10-23.md).

| File | Evaluation scope |
|---|---|
| `initial_supervision.json` | 488-point nested spatial OOF; 5,835 common raw-numeric score items |
| `regression_iterations.json` | Weighting, specialists, constraints and blends; same common-item development comparison |
| `v3_prompt_comparison.json` | Matched V2/V3 on 100 development points; 1,191 common numeric items under the earlier reference |
| `prompt_diagnostics.json` | Separate 12/24/60/100-point diagnostic samples; do not pool or rank across samples |
| `v5_safety_only.json` | 60-point safety-only pilot; 174 numeric pairs out of 180 safety reference items, with NA coverage and failed promotion gate |
| `v2_v6_comparison.json` | Matched 488-point nested spatial OOF; all 5,856 reference items |
| `tolerance.json` | Hit-rate selection and SVR; continuous development OOF |
| `probability.json` | Probability candidates and selected mixture; continuous development OOF |
| `dino_ablation.json` | Same 488-point folds, with/without DINO; both precisions and per-target/per-fold results |
| `independent_test200.json` | Frozen final model, 200-point test; both precisions, all 12 targets, original acceptance checks |

Rate fields are fractions, not percentages: `within_0_1 = 0.8271` means about
82.71%. MAE and RMSE are on the 0–1 score scale. Threshold comparisons use small
floating-point tolerances: error ≤0.10000001 and error ≥0.29999999. The rounded
ablation also verifies the corresponding decisions with integer tenths.

`ccc` is the pooled concordance coefficient. Fields named `macro_ccc`,
`macro_CCC`, `macro_target_ccc` or `macro_target_CCC` in the historical experiments
are the arithmetic mean of the 12 target coefficients. Do not substitute pooled
CCC for target-level agreement; variation between different targets can inflate
the pooled value. Historical field names are retained to avoid silently
changing source meaning.

One-decimal delivery was chosen after reviewing the independent test, while
the rounding rule itself was fixed before that test. The original primary
continuous >70% hit-rate check remains false. The 200-point test has not been
used to fit the selected model or to select the no-DINO ablation, and is now an
evaluated holdout rather than an untouched resource. Full-dataset scoring had
not started at that milestone; it is now complete under the canonical extension.

## October 23 follow-up archive

| File | Evidence scope |
|---|---|
| `conservative_safety.json` | Same 488-point development OOF: caps and raw/base gates |
| `grounded_roi_pilot.json` | Separate 24-point raw-VLM pilot; do not rank against supervised OOF |
| `dino_spatial_grid.json` | Same 488 folds: CLS versus CLS+2x3 patch grid |
| `low_safety_expert.json` | Selected extension; both precisions, 12 targets, folds, bands and failed nonlow guard |
| `ab_dimension_diagnostic.json` | Reference-guided dimension matching on 488+200 already-scored points; not independent accuracy |

The extension was user-selected after accepting the nonlow-safety tradeoff.
At that milestone its all-488 wrapper refit was pending; old independent-test metrics remain
historical base-only evidence. A/B diagnostic gains are not stacked onto the
extension. No validation500 or full-dataset scoring was run by this archive update.

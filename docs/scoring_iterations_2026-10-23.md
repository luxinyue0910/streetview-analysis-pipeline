# Scoring experiments and selection history

This is a retrospective record of local experiments through October 23 UTC.
It does not reconstruct them as historical Git commits. The selected method is
described in [the method report](scoring_method_2026-10-23.md); full-dataset
scoring remains paused. New documentation is in English; archived task prompts
retain their original Chinese language.

## Reading the results correctly

- Compare alternatives on the **same reference version, point set, item mask
  and score precision**. Do not rank a difficult-case pilot against a random
  sample or the 488-point regression experiment.
- Initial prompt experiments used an earlier reference. A replacement team
  reference was subsequently accepted; Flash v2 and prior maintenance
  experiments were re-evaluated. The final supervised results use that accepted
  replacement reference. Older tables are historical, not current benchmarks.
- The eligible reference pool had 773 points, not 1,000 fully eligible training
  points. Spatial isolation produced 488 development points, 85 excluded buffer
  points and the original 200-point holdout. No 500-point validation data were
  used. Twelve targets do not multiply the number of independent points.
- Early regression tables use 5,835 items where raw v2 scores are numeric;
  later tables use all 5,856 reference items with training-only missing-value
  handling. The 21 missing raw scores are not reference zeroes. These slightly
  different denominators are explicitly retained below.
- Development data informed repeated prompt and method choices. Spatial nested
  CV prevents the fitted regression components from seeing their outer labels,
  but cannot undo earlier prompt-development exposure to those points.

## 1. Prompt and model pilots

The [initial pilot](vlm_pilot_2026-10-20.md) compared verbose and compact output,
Qwen model options and measured usage on three points. Flash became the economical
candidate for larger experiments; VL Plus remained an alternative. Three points
were insufficient to establish a general model ranking.

The [organized-rubric experiment](vlm_organized_pilot_2026-10-20.md) made PDF
definitions, bands and constraints explicit by dimension. Cleaner organization
did not consistently improve scores. Errors included both incorrect visual
facts and incorrect mapping from visible facts to scoring bands.

The v3 evidence-aligned prompt added target-location, function and band checks
after auditing the 100-point development set. It was evaluated against v2 on
those same points under the then-current reference; it was not selected as a
general replacement. Its [instruction archive](../prompts/qwen_scoring/v3_evidence_aligned/README.md)
is now marked evaluated rather than leaving the old “unevaluated” status.
VL Plus and image-fact/maintenance-oriented pilots were also explored. Changes
were treated as dimension-specific hypotheses, not as automatic replacements.

After the reference replacement, the fixed 100-point Flash v2 baseline had
52.56% within 0.1, MAE 0.1581 and 19.98% errors ≥0.3 on its 1,191 numeric items;
9 of 1,200 outputs were NA. This diagnostic baseline is not the final test.

## 2. Supervised score calibration and image features

With the point split and spatial buffer fixed, compare a mean predictor, raw
Qwen, per-target Qwen calibration, frozen DINO + Ridge, and DINO + Qwen Ridge.
Calibration learns systematic scoring corrections; image features can help
distinguish scenes that received the same Qwen scores.

| 488-point OOF, continuous; common 5,835 items | Within 0.1 | MAE | Error ≥0.3 |
|---|---:|---:|---:|
| Training-fold mean | 42.31% | 0.1462 | 9.77% |
| Raw Flash v2 | 51.47% | 0.1644 | 22.37% |
| Flash v2 + per-target calibration | 62.33% | 0.1033 | 4.92% |
| DINO + Ridge | 59.81% | 0.1007 | 3.17% |
| DINO + Qwen Ridge | 61.25% | 0.0982 | 2.83% |

The initial fusion did not maximize the tolerance hit rate, but reduced average
and large errors. This motivated a guarded mixture rather than assuming one
regressor would be best for every target. [Aggregate record](../results/scoring_2026-10-23/initial_supervision.json).

## 3. Low-score weighting, specialists and constrained selection

Low-score cases were sometimes pulled toward the middle. Experiments therefore
tested score-band weighting, per-target model selection, and explicit low/high
band constraints. Parameters and weights were chosen inside spatial training
folds; labels were neither stretched nor edited to create more variation.

| 488-point OOF, continuous; common 5,835 items | Within 0.1 | MAE | Error ≥0.3 |
|---|---:|---:|---:|
| Initial fusion | 61.25% | 0.0982 | 2.83% |
| Weighted fusion | 59.59% | 0.1016 | 3.20% |
| Per-target selection by MAE | 64.27% | 0.0955 | 2.91% |
| Selection with low/high-score guards | 64.13% | 0.0963 | 3.32% |
| Blending + large-error guard | 63.08% | 0.0941 | 2.45% |
| Small nonlinear model | 64.13% | 0.0929 | 2.67% |

Weighting helped some low-score safety/greenery cases but did not improve every
metric. MAE-only selection lost low-score greenery quality. Guarded blending
provided a more balanced development tradeoff. The nonlinear model had lower
mean error but worsened low-score greenery; it was not adopted solely because
of its average. A later same-PCA Ridge control limited claims that nonlinearity
itself caused the gains. [Aggregate records](../results/scoring_2026-10-23/regression_iterations.json).

## 4. Additional visual-grounding and explanation experiments

Several diagnostics ran alongside supervised-model development:

| Experiment | Scope | Finding and decision |
|---|---|---|
| Full image + assisted walking-area crop | 12 diagnostic points, safety | MAE improved by about 0.0129, below the fixed 0.02 pilot requirement; one new NA. Did not expand this manually localized crop workflow. |
| Spatial target prompt and safety-only revision | 60-point pilots | Investigated wrong-road/wrong-side attention and rule conflicts. No general replacement was accepted. |
| Structured visible observations | 24 development points | Common-item MAE 0.1829 → 0.1601, but safety worsened and two new safety NAs appeared. Gains were concentrated in greenery/maintenance. |
| Brief explanation vs two-stage observation/scoring | 24 development points | On 274 common items: v2 MAE 0.1869, brief explanation 0.1661, two-stage 0.1755. The brief candidate merited expansion, not deployment. |
| Repaired brief explanation | 60 points | On 715 common items: MAE 0.1571 → 0.1578. Maintenance improved, but aggregate MAE did not and five new NAs appeared. |
| Maintenance calibration probe | 60 points, 180 maintenance items | New raw maintenance scores improved, but after matched affine calibration MAE was 0.0789 versus 0.0772 for v2. Better raw scores did not establish a better calibrated pipeline. |
| Assistant-reviewed visual facts | 20 diagnostic points | Safety/greenery MAE improved on common numeric items, but 15 new NAs appeared. Facts were prepared with access to reference scores, so this was explicitly reference-informed diagnosis, not independent accuracy. |
| Generalized v6 target/evidence prompt | 50 development points | Safety MAE improved 0.1839 → 0.1658; interface worsened 0.1141 → 0.1550. Across all targets, common-item MAE 0.1575 → 0.1590. Did not replace v2. |

More detailed explanations did not ensure correct observations. Visual review
found unsupported facility claims and target-area mistakes. Some pilots used
selected difficult cases, and token output increased in richer-output arms;
their results cannot be extrapolated as population accuracy or current prices.
Selected machine-readable diagnostic aggregates are in
[`prompt_diagnostics.json`](../results/scoring_2026-10-23/prompt_diagnostics.json).

## 5. v2, v6 and both versions in the same supervised workflow

Each arm was separately refitted using the same DINO features, spatial nested
folds and guarded blending. Supplying new prompt scores to an old regressor
would not be a fair comparison. The dual arm also had a larger candidate pool.

| 488-point OOF, continuous; all 5,856 items | Within 0.1 | MAE | Error ≥0.3 |
|---|---:|---:|---:|
| DINO + v2 guarded blend | 63.03% | 0.0942 | 2.44% |
| DINO + v6 guarded blend | 62.19% | 0.0970 | 2.82% |
| DINO + v2 + v6 guarded blend | 63.35% | 0.0938 | 2.37% |

v6 worsened MAE in every outer fold. Adding both versions reduced MAE by only
0.000341 versus v2, with a paired group interval crossing zero. This did not
justify the additional prompt calls. **Keep v2.** Existing v2 scores were reused,
so API call dates/repeat variability were not perfectly controlled.
[Aggregate record](../results/scoring_2026-10-23/v2_v6_comparison.json).

## 6. Optimize tolerance hit rate, then add score probabilities

The next experiments reused the same v2 predictions and DINO features without
new VLM calls. Inner selection prioritized ≤0.1 while retaining error guards.
RBF epsilon-SVR added candidates; it does not directly optimize hit rate.
Score probabilities added expectation and continuous tolerance-window decoders.

| 488-point OOF, continuous; all 5,856 items | Within 0.1 | MAE | Error ≥0.3 |
|---|---:|---:|---:|
| Prior guarded blend | 63.03% | 0.0942 | 2.44% |
| Hit-rate selection without new SVR candidates | 62.88% | 0.0945 | 2.46% |
| Hit-rate selection + SVR | 64.74% | 0.0914 | 2.37% |
| Probability arm | 66.92% | 0.0893 | 3.04% |
| Continuous regression/probability mixture | 66.31% | 0.0897 | 2.51% |

The probability arm had the best hit rate but worse large-error/low-band guards.
The mixture retained more balanced behavior and became the candidate to freeze.
Maintenance retained its previous-stage model family throughout these additions.
[Tolerance record](../results/scoring_2026-10-23/tolerance.json) and
[probability record](../results/scoring_2026-10-23/probability.json).

## 7. Uniform one-decimal output and independent evaluation

Rounding was first examined on development OOF predictions, without retraining
or consulting the 200-point test. The selected mixture's hit rate changed from
66.31% continuous to 81.71% rounded; MAE from 0.0897 to 0.0864; large errors from
2.51% to 4.66%. This is output quantization, not better image recognition.

Freeze the method, select final components within the 488 development points,
and refit those components on all 488. Freeze test predictions before comparing
with the 200 reference rows. Fresh Flash v2 requests produced 600 valid stage
responses; no test reference scores were sent to the API. Earlier interrupted
test-request artifacts were not used for development or score-based reuse.

| Independent 200 points; 2,400 items | Within 0.1 | MAE | Error ≥0.3 |
|---|---:|---:|---:|
| Continuous, primary at test time | 69.75% | 0.0861 | 2.54% |
| One decimal, secondary at test time | 82.71% | 0.0824 | 4.58% |

The primary >70% goal was **not met**; the safety MAE criterion also failed.
The later decision to use decimal delivery does not redefine the test endpoint.
See the [method report](scoring_method_2026-10-23.md) for all 12 targets, intervals
and limitations. The test set is now evaluated, not an untouched tuning resource.

## 8. DINO ablation and final choice

Remove DINO and retrain within the original 488-point nested spatial folds,
keeping the existing continuous-selection and rounding approach. Do not reuse
the 200 test to select the ablation. No additional Qwen requests are needed.

| Development OOF, one decimal | Within 0.1 | MAE | Error ≥0.3 |
|---|---:|---:|---:|
| Selected mixture with DINO | 81.71% | 0.0864 | 4.66% |
| Mixture without DINO | 77.13% | 0.0946 | 6.86% |

All five folds lost hit rate; the largest target loss was Side A greenery
(−11.07 percentage points). Retain DINO. Maintenance changed relatively little;
no per-target removal was selected after inspecting these outer-fold results.

**Final user-selected configuration:** Flash v2 + frozen DINO + supervised
mixture, one-decimal delivery with continuous predictions retained. No full
batch run is authorized by this documentation update. The public artifacts
are aggregate evidence and a method specification; data-bearing experiments
and fitted model files stay private.

# Scoring experiments and selection history

This is a retrospective record of local experiments through October 23 UTC.
It does not reconstruct them as historical Git commits. The selected method is
described in [the updated method report](scoring_low_safety_extension_2026-10-23.md); full-dataset
scoring remains paused. New documentation is in English; archived task prompts
retain their original Chinese language.

**Start here:** [V0–V6 prompt changes and decisions](#1-prompt-evolution-v0v6),
[additional explanation experiments](#4-additional-visual-grounding-and-explanation-experiments),
[v2/v6 with the same supervised workflow](#5-v2-v6-and-both-versions-in-the-same-supervised-workflow),
and [final choice](#8-dino-ablation-and-final-choice).

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

## 1. Prompt evolution: V0–V6

**The final pipeline uses Flash + V2, not V6.** Later versions tested specific
hypotheses; they were not automatic upgrades. V4 and V6 keep the full V2 rubric,
while V5 is a safety-only branch. The table below records what actually changed.
Prompt versions are separate from DINOv2 (the image encoder) and from subsequent
supervised calibration/regression experiments.

| Version and archived instructions | Problem addressed | Concrete change | Evaluation and decision |
|---|---|---|---|
| [V0](../prompts/qwen_scoring/v0) | Establish image scoring with the PDF rules | Original extracted rubric; scores plus target description, visible evidence, rubric anchors, uncertainty and NA reasons | Three-point model pilot with VL Plus and 3.8 Max; verbose starting point, not a validated baseline |
| [V1 compact](../prompts/qwen_scoring/v1_compact) | Reduce output length and cost | Keep rubric and image protocol; return scores + one short evidence sentence per dimension, at most 40 characters | Same three points; VL Plus output tokens fell 76.1%. Retain compact output; Flash became the economical candidate |
| [V2 organized](../prompts/qwen_scoring/v2_organized) | Make PDF rules easier to follow | Group definitions, score bands and hard restrictions by dimension; clean extraction artifacts | Three-point agreement did not improve consistently. Retain as the explicit, reproducible baseline; ultimately selected for the mixed pipeline |
| [V3 evidence aligned](../prompts/qwen_scoring/v3_evidence_aligned/README.md) | Address errors found in the 100-point audit | Add target-location, object-function, evidence-to-band and observability checks; keep full V2 rubric and compact output | Same 100 development points, earlier reference: MAE 0.1572 → 0.1586; within 0.1 49.12% → 48.61%. Not selected |
| [V4 spatial](../prompts/qwen_scoring/v4_spatial/README.md) | Prevent wrong-route and wrong-side judgments | Add per-image categorical observations of walkway, barriers, vehicles, canopy and staying support before scoring | 60-point pilot: MAE 0.1586 → 0.1558, but low-score safety and NA coverage failed promotion checks. Not selected |
| [V5 safety only](../prompts/qwen_scoring/v5_safety_only/README.md) | Isolate difficult safety decisions | Retain only general/safety rubric sections; describe route type, continuity and obstruction; output safety only | 60-point safety pilot: MAE 0.2149 → 0.1736 on 174 numeric pairs, but five new NAs. Not selected |
| [V6 target/evidence](../prompts/qwen_scoring/v6_target_evidence/README.md) | Generalize lessons from visual-grounding and explanation pilots | Five short observation fields, then scores and evidence; keep full V2 rubric | 50-point pilot: safety improved, interface worsened. Later matched 488-point DINO comparison also favored V2. Not selected |

Each arrow is a **within-experiment comparison**, not a comparison with the
previous row. Samples, reference versions and numeric-item masks differ. MAE
is mean absolute error; “within 0.1” means the fraction of evaluated scores
whose absolute difference from the reference is ≤0.1. Missing outputs are
reported separately, because a better numeric-only average can hide lost coverage.

### V0 → V1: shorten the output, preserve the task

V0 requested a substantial explanation alongside each score. V1 removed the
separate target/anchor/uncertainty narrative and retained one short evidence
sentence per dimension, including the reason when a score is NA. The maximum
output allowance changed from 2,200 to 900 tokens; this is a cap, not actual usage.
The rubric, images and independent overall/A/B request protocol stayed the same.

Across nine matched VL Plus requests, actual output tokens fell from 6,198 to
1,482 (76.1%). Scores also changed, so this was not proof of equal accuracy.
The compact pilot compared Flash, VL Plus and 3.7 Plus on only three points;
its reference was an earlier AI-assisted annotation set, not an independent
human gold standard. Flash was retained as an economical experimental candidate,
with VL Plus as an alternative. [Full pilot and usage record](vlm_pilot_2026-10-20.md).

### V1 → V2: reorganize the rubric, not the scoring criteria

V2 places each definition, low/middle/high band and restriction under the correct
scoring dimension. It also removes extraction artifacts and repeated headers.
The authored task instructions, response contract, image bytes and 900-token
limit stayed unchanged. Original PDF pages were checked to preserve rule meaning.

On the same 30 numeric cells across both versions and models, Flash's reference
MAE changed from 0.087 to 0.117; VL Plus changed from 0.133 to 0.147. This small
pilot did **not** demonstrate an accuracy gain from organization. V2 provided a
clear fixed baseline for further development; its eventual selection rests on
later pipeline comparisons, not on winning this pilot.
[Matched experiment](vlm_organized_pilot_2026-10-20.md).

### V2 → V3: align visual evidence with score-band conditions

The 100-point error audit led to explicit checks for:

- **Safety:** locate the actual walking route and evaluate spatial relationships,
  rather than treating the foreground road as the pedestrian target.
- **Interface:** inspect ground-floor access and object function, not just the
  presence of buildings or walls.
- **Greenery/staying:** check both shade coverage and usable staying support;
  avoid raising or lowering a band based on greenery alone.
- **Maintenance:** use visible physical defects and severity, rather than age,
  architectural style or an habitual default score.
- **Scope and visibility:** assess each dimension's observability separately and
  score overall from both images, independently of the side requests.

The full V2 rubric was retained; no few-shot examples or new scoring anchors
were added. On 1,191 common numeric items from the same 100 points under the
**earlier reference**, results were:

| Target dimension, pooled across overall/A/B | V2 MAE | V3 MAE |
|---|---:|---:|
| Safety | 0.1998 | 0.1955 |
| Interface | 0.1074 | 0.1125 |
| Greenery/staying | 0.1572 | 0.1582 |
| Maintenance | 0.1643 | 0.1680 |
| All dimensions | 0.1572 | 0.1586 |

The pooled within-0.1 rate fell from 49.12% to 48.61%. V3 produced numeric values
for all 1,200 items versus V2's 1,191, but improved coverage did not establish
better agreement. Keep V2 as the baseline.
[Aggregate paired comparison](../results/scoring_2026-10-23/v3_prompt_comparison.json).

After the team replaced the reference table, the same fixed 100-point Flash V2
baseline was re-evaluated: within 0.1 **52.56%**, MAE **0.1581**, error ≥0.3
**19.98%**, with 1,191 numeric items and nine NAs. This is a different reference
comparison, not a new prompt gain and not the final independent test.

### V4: require spatial observations before scores

V4 adds categorical observations for each image: the target edge, walkway
continuity, barrier relation, vehicle relation, canopy relation and staying
support. For example, a boundary wall is not automatically traffic protection;
a parked vehicle matters differently when it occupies the walkway; tree canopy
must relate to the walking route rather than merely appear somewhere in view.

The four scores and short evidence remain. Overall requests contain two ordered
observation objects, side requests one. On 710 common numeric items from 60
points, MAE improved from 0.1586 to 0.1558, while within 0.1 changed from 55.21%
to 54.79%. Low-score safety worsened and total NAs rose from five to six.
The improvement was insufficient under the promotion checks.
[Instructions and response contract](../prompts/qwen_scoring/v4_spatial/README.md).

### V5: isolate safety instead of changing all 12 targets

V5 narrows the task to route type, continuity, obstruction and supporting
observations, using only the general principles and safety portion of the V2
rubric. Three calls yield **three safety scores**, not 12; the other nine scores
in composite reports remain V2 outputs.

On 174 numeric safety pairs from 60 points, within 0.1 rose from 50.00% to 57.47%
and MAE fell from 0.2149 to 0.1736. However, safety NAs increased from one to six,
with five new NAs and none resolved. The numeric improvement did not satisfy the
coverage requirement, so this branch was not promoted.
[Instructions and matched metrics](../prompts/qwen_scoring/v5_safety_only/README.md).

### V6: short target-grounded observations, then scores

V6 returns five short observation fields—`target_area`, `walk_route`,
`separation`, `shade`, `staying`—followed by the four scores and short evidence.
It distinguishes physical presence from useful function: whether vegetation
shades the public walking route, whether a barrier separates traffic, and whether
there is usable staying space. It also distinguishes confirmed absence from
unobservable space instead of substituting default low scores for uncertainty.

This generic prompt contains **no per-point reference scores or assistant facts**.
It is distinct from the reference-informed facts diagnostic in section 4. The
full V2 rubric remains; the output cap rises to 3,000 tokens for observations.

In the 50-point pilot, safety MAE improved from 0.1839 to 0.1658, but interface
worsened from 0.1141 to 0.1550; greenery changed from 0.1600 to 0.1633 and
maintenance from 0.1720 to 0.1520. Across 598 common numeric items, MAE changed
from 0.1575 to 0.1590. Better safety/maintenance did not offset the other losses.

V6 was also tested inside the **same supervised DINO workflow**, rather than
being rejected on raw scores alone. On 488 development points, its guarded
mixture had MAE 0.0970 versus V2's 0.0942 and worsened MAE in all five outer folds.
Combining both prompts yielded only a small uncertain gain, with extra calls.
Section 5 provides that matched comparison. These are earlier guarded-mixture
results, not the later final SVR/probability mixture's test performance.
[Exact V6 archive](../prompts/qwen_scoring/v6_target_evidence/README.md).

### What is reproducible, and what was learned

The [prompt archive](../prompts/qwen_scoring/README.md) contains each version's
authored prefix/suffix, parameters, response contract and composed-prompt hashes.
A complete prompt is **prefix + private PDF-derived rubric + suffix**; the short
prefix alone is not the request. V5 first selects its safety section. The
[renderer](../scripts/render_scoring_prompt.py) composes these locally when the
private rubric is supplied. Original PDFs, full private rubric text and per-point
reference data are not published.

All versions use independent overall/A/B calls, temperature 0, thinking disabled
and JSON-object output. Schemas document local response validation; they were not
sent as server-enforced strict schemas. V0 allows 2,200 output tokens, V1–V5 900,
and V6 3,000. More output tokens or better-written evidence do not prove better
visual recognition. Single runs also do not isolate prompt effects from service
variability. The evidence supported **keeping V2 and improving the downstream
supervised mixture**, while preserving rejected branches for future work.

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

The exact authored instructions and response contracts for the numbered branches
are archived as [V4 spatial](../prompts/qwen_scoring/v4_spatial/README.md),
[V5 safety only](../prompts/qwen_scoring/v5_safety_only/README.md), and
[V6 target/evidence](../prompts/qwen_scoring/v6_target_evidence/README.md).
Private rubric text must be supplied locally to reproduce the full prompts.

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

**Earlier frozen configuration (before the low-safety follow-up below):** Flash v2 + frozen DINO + supervised
mixture, one-decimal delivery with continuous predictions retained. No full
batch run is authorized by this documentation update. The public artifacts
are aggregate evidence and a method specification; data-bearing experiments
and fitted model files stay private.

## 9. October 23 follow-up: low-safety errors and routing

After the frozen baseline, compare conservative correction caps, raw/base gates,
a separate grounded-crop pilot, fixed spatial DINO grid features and a two-step
low-only expert. The [follow-up method and results](scoring_low_safety_extension_2026-10-23.md)
record the complete sequence, all 12 targets and the accepted tradeoff.

The user-selected next-validation method retains Flash v2 and the original DINO
mixture, adding a learned low-safety classifier and low-only Ridge expert for
each safety scope. Rounded low-safety within-0.1 rises 56.00% -> 66.67%, while
nonlow safety falls 78.85% -> 77.72%. All-target hit rate rises 81.71% -> 81.88%.
The original 1 pp nonlow guard failed; user selection accepts this tradeoff
rather than retroactively passing it. There is no new independent result and
the all-488 safety-wrapper refit is pending. Validation500 and full batch remain
unrun. The old model's independent 200-point scores cannot be assigned to this extension.

## 10. Separate A/B correspondence diagnosis

A teammate's A/B hypothesis led to visual review and correspondence experiments.
The selected diagnostic exchanges A/B separately per dimension whenever the
count of errors >=0.3 strictly decreases. The latest rule includes 2->1 as well
as 2->0 and 1->0 transitions; whole-side exchange is not adopted here.

On 688 already-scored points, 64 dimension pairs at 61 points qualify. Large
errors fall 383 -> 311 (18.8%), with hit rate 82.00% -> 82.35%. These results use
the base mixture, not the low-safety extension, and are reference-guided posthoc
diagnosis, including the already-evaluated 200 points. They are not independent
accuracy gains or inference rules for unlabelled data. See the [dedicated diagnostic](ab_dimension_diagnostic_2026-10-23.md).

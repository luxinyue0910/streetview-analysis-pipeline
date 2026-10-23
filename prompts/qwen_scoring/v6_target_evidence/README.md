# V6: target-grounded short observations and evidence

**Status: evaluated on 50 development points and then in the 488-point
supervised comparison; not selected. The selected workflow still uses V2.**

V6 returns five short observation strings—`target_area`, `walk_route`,
`separation`, `shade`, and `staying`—followed by four scores and four short
evidence strings. It emphasizes the position and function of visible objects,
distinguishes missing features from unobservable space, and checks that evidence
supports the assigned band. The complete private V2 organized rubric remains
unchanged. Three calls produce 12 scores per point.

This is the generic `target_evidence_v6` arm. It is **not** the separate
`facts_assisted` diagnostic arm, which received per-point, reference-informed
assistant observations. No such facts or reference scores are part of this
archived V6 prompt.

## Recorded evaluation

The 50-point pilot improved safety MAE from 0.1839 to 0.1658, but interface MAE
worsened from 0.1141 to 0.1550. Across 598 common numeric items, MAE changed from
0.1575 to 0.1590. More specific observations did not reliably prevent unsupported
facility claims or target-location mistakes.

The later experiment separately refitted each supervised arm on the same 488
development points and spatial nested folds. The V6 prompt hashes were identical
to those in the 50-point pilot.

| Continuous development OOF; 5,856 items | Within 0.1 | MAE | Error ≥0.3 |
|---|---:|---:|---:|
| DINO + V2 guarded mixture | 63.03% | 0.0942 | 2.44% |
| DINO + V6 guarded mixture | 62.19% | 0.0970 | 2.82% |
| DINO + V2 + V6 guarded mixture | 63.35% | 0.0938 | 2.37% |

V6 worsened MAE in all five outer folds; using both prompt versions yielded a
very small, uncertain gain over V2 and required extra prompt calls. These are
the earlier guarded-mixture results, not the later selected SVR/probability
mixture or its independent test performance. See
[the comparison](../../../results/scoring_2026-10-23/v2_v6_comparison.json) and
[the experiment history](../../../docs/scoring_iterations_2026-10-23.md).

## Reproduction contract

Use the [renderer](../../../scripts/render_scoring_prompt.py) with
`--version v6_target_evidence`, full private V2 rubric text for the chosen stage,
and `--verify-pilot-hash`. Composition does not call the model.

V6 used Flash with temperature 0, thinking disabled, JSON-object output and a
**3,000-token cap**, compared with 900 in the selected final V2 configuration.
Existing V2 scores were reused in the 488-point comparison; model-call dates
and repeat variation were not perfectly controlled.

`response.schema.json` documents the normalized local response contract. The
archived runner converted only a fixed whitelist of numeric score strings to
numbers before validation and preserved raw responses separately; see config.
Other strings and out-of-rubric anchors are not silently repaired. The schema
was not sent to the API as a strict response schema.

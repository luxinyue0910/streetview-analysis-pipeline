# Dimension-wise A/B correspondence diagnostic

A teammate proposed that some large disagreements might come from reversed A/B
correspondence. We tested that explanation separately from improving the scorer.
This document describes **reference-guided posthoc matching**, not automatic
side recognition, repaired ground truth, or new independent-test performance.

## Final rule

For each point, independently for safety, interface, greenery/staying and
maintenance, compare the original and swapped model side scores with the same
unchanged reference pair. Count absolute errors >=0.3 (inclusive). Accept the
swap only if this count strictly decreases: **2->1, 2->0 or 1->0**. On ties,
keep the original mapping. Overall scores never change. No MAE guard is imposed.

This supersedes the stricter first dimension-wise rule that required both
post-swap errors to be <0.3, which missed 2->1 improvements. A still earlier
whole-side exchange moved all four dimensions together; it is not the selected
diagnostic rule. Do not stack these experiments.

Different dimensions may now draw A/B values from different source images.
Consequently the matched columns need per-dimension source tracking and cannot
be represented as one consistent physical A/B pair for formal side-specific
delivery. The original image identities and predictions stay unchanged.

## Population and results

The accepted reference has 773 eligible points. Predictions were available for
688: 488 development OOF points plus the already-evaluated 200 test points.
The 85 spatial-buffer points were not scored. Use the original base mixture's
one-decimal outputs, **not the later low-safety extension**. No new calls or
training were needed.

| Population | Accepted pairs / points | Large errors before -> after | Within 0.1 before -> after | MAE before -> after |
|---|---:|---:|---:|---:|
| Development 488 | 44 / 42 | 273 -> 224 | 81.71% -> 81.98% | 0.08641 -> 0.08514 |
| Already-evaluated 200, descriptive only | 20 / 19 | 110 -> 87 | 82.71% -> 83.25% | 0.08238 -> 0.08021 |
| All 688, descriptive pooled summary | 64 / 61 | 383 -> 311 | 82.00% -> 82.35% | 0.08523 -> 0.08371 |

Of the 64 accepted pairs, 47 are 1->0, eight are 2->0 and nine are 2->1.
The revised rule adds nine pairs to the previous 55, reducing nine additional
large errors (320 -> 311). Relative to original correspondence, 72 large errors
are removed (18.8%); their proportion drops 4.64% -> 3.77%. Points containing
any large error drop 247 -> 210. One accepted pair has increased pair MAE:
the objective is a smaller threshold-error count, not guaranteed improvement
of every metric or both individual sides.

| Side dimension, A+B pooled | Large errors before -> after | Relative reduction |
|---|---:|---:|
| Safety | 130 -> 107 | 17.7% |
| Interface | 107 -> 73 | 31.8% |
| Greenery/staying | 43 -> 32 | 25.6% |
| Maintenance | 19 -> 15 | 21.1% |

## All 12 targets: one decimal, 688 points per target

| Target | Within 0.1, before -> after | MAE, before -> after | Error >=0.3, before -> after | Counts, before -> after |
|---|---:|---:|---:|---:|
| overall_pedestrian_safety | 77.62% -> 77.62% | 0.0987 -> 0.0987 | 4.94% -> 4.94% | 34 -> 34 |
| overall_street_interface | 79.51% -> 79.51% | 0.0906 -> 0.0906 | 4.94% -> 4.94% | 34 -> 34 |
| overall_greenery_staying | 93.17% -> 93.17% | 0.0565 -> 0.0565 | 0.87% -> 0.87% | 6 -> 6 |
| overall_environmental_maintenance | 91.13% -> 91.13% | 0.0628 -> 0.0628 | 1.45% -> 1.45% | 10 -> 10 |
| side_A_pedestrian_safety | 73.55% -> 73.69% | 0.1089 -> 0.1070 | 8.87% -> 6.69% | 61 -> 46 |
| side_A_street_interface | 75.44% -> 76.45% | 0.1016 -> 0.0974 | 6.83% -> 4.65% | 47 -> 32 |
| side_A_greenery_staying | 84.01% -> 84.30% | 0.0769 -> 0.0751 | 2.18% -> 1.31% | 15 -> 9 |
| side_A_environmental_maintenance | 90.84% -> 91.13% | 0.0552 -> 0.0545 | 1.45% -> 1.02% | 10 -> 7 |
| side_B_pedestrian_safety | 73.40% -> 73.84% | 0.1187 -> 0.1169 | 10.03% -> 8.87% | 69 -> 61 |
| side_B_street_interface | 74.56% -> 76.02% | 0.1090 -> 0.1031 | 8.72% -> 5.96% | 60 -> 41 |
| side_B_greenery_staying | 79.94% -> 80.67% | 0.0847 -> 0.0830 | 4.07% -> 3.34% | 28 -> 23 |
| side_B_environmental_maintenance | 90.84% -> 90.70% | 0.0592 -> 0.0590 | 1.31% -> 1.16% | 9 -> 8 |

## What visual review did and did not establish

An earlier reference-informed inspection covered 27 selected suspected points
and 54 originals: five had stronger correspondence concerns; three had mixed
dimension-specific correspondence/scoring concerns; 12 more likely had scoring
problems; five had ambiguous model target sides/multiple sides in view; two lacked
mapping evidence. These were selected cases, not a random reversal-rate sample.
No historical side assignments were conclusively established. Numeric matching
does not prove either the annotator or model had reversed the actual sides.

## Interpretation and future use

This measures how much disagreement can disappear under reference-selected
dimension-wise correspondence. Most large errors remain (311/383). Because the
reference determines which swaps are chosen, these are not model improvements
that can be reproduced on unlabelled points. The 200-point matched numbers must
not replace the original independent-test results. No gains from this table have
been added to the low-safety extension's development scores.

For the future 500-point validation, retain fixed-correspondence predictions and
their primary metrics, and optionally add this labelled posthoc diagnostic as
a separate table. For full-data inference without references, keep original A/B
identity; do not apply this rule. No original data were overwritten.

[Machine-readable rule](../configs/scoring/ab_dimension_diagnostic.json) and
[aggregate results, including every target](../results/scoring_2026-10-23/ab_dimension_diagnostic.json).

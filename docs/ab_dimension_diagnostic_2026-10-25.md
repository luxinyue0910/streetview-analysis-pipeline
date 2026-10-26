# Separate A/B diagnostic on the 405 evaluable validation points

This is **reference-guided posthoc matching**, not an inference stage, improved
blind validation, corrected ground truth or evidence of a physical side reversal.
The automatic [500-point metrics](validation500_2026-10-25.md) and both validation
and full-batch delivery files retain fixed canonical A/B identities.

## Rule and population

Start with the final one-decimal canonical low-safety extension on the 405 points
with numeric reference scores (4,860 items). For each point and each of safety,
interface, greenery/staying and maintenance independently, compare unchanged and
swapped model side pairs with the unchanged reference pair. Adopt a swap only if
the number of absolute errors >=0.3 strictly decreases: 2->1, 2->0 or 1->0.
Ties preserve the original order. Overall scores never change. There is no MAE
guard or <=0.1 guard; either can worsen even when the severe-error count falls.

Test 1,620 point-dimension pairs. Accept 37 pairs at 37 points: 33 transitions
1->0 and four transitions 2->1. Counts by dimension: safety 16, interface 13,
greenery 8, maintenance 0.

## Results

| Target | Within 0.1 before / after | MAE before / after | Error >=0.3 before / after | Count before / after |
|---|---:|---:|---:|---:|
| `ALL` | 84.61% / 84.55% | 0.0761 / 0.0754 | 3.60% / 2.84% | 175 / 138 |
| `pedestrian_safety` | 81.98% / 81.56% | 0.0877 / 0.0867 | 6.34% / 5.02% | 77 / 61 |
| `street_interface` | 81.98% / 81.81% | 0.0847 / 0.0839 | 5.35% / 4.28% | 65 / 52 |
| `greenery_staying` | 81.40% / 81.73% | 0.0773 / 0.0765 | 2.30% / 1.65% | 28 / 20 |
| `environmental_maintenance` | 93.09% / 93.09% | 0.0547 / 0.0547 | 0.41% / 0.41% | 5 / 5 |
| `overall_pedestrian_safety` | 81.98% / 81.98% | 0.0877 / 0.0877 | 7.16% / 7.16% | 29 / 29 |
| `overall_street_interface` | 81.98% / 81.98% | 0.0820 / 0.0820 | 3.70% / 3.70% | 15 / 15 |
| `overall_greenery_staying` | 80.99% / 80.99% | 0.0716 / 0.0716 | 1.73% / 1.73% | 7 / 7 |
| `overall_environmental_maintenance` | 92.35% / 92.35% | 0.0499 / 0.0499 | 0.25% / 0.25% | 1 / 1 |
| `side_A_pedestrian_safety` | 83.95% / 83.21% | 0.0827 / 0.0822 | 6.42% / 4.94% | 26 / 20 |
| `side_A_street_interface` | 80.99% / 80.74% | 0.0889 / 0.0884 | 7.41% / 5.93% | 30 / 24 |
| `side_A_greenery_staying` | 83.21% / 83.21% | 0.0780 / 0.0770 | 3.21% / 1.98% | 13 / 8 |
| `side_A_environmental_maintenance` | 95.80% / 95.80% | 0.0467 / 0.0467 | 0.49% / 0.49% | 2 / 2 |
| `side_B_pedestrian_safety` | 80.00% / 79.51% | 0.0926 / 0.0901 | 5.43% / 2.96% | 22 / 12 |
| `side_B_street_interface` | 82.96% / 82.72% | 0.0832 / 0.0812 | 4.94% / 3.21% | 20 / 13 |
| `side_B_greenery_staying` | 80.00% / 80.99% | 0.0822 / 0.0807 | 1.98% / 1.23% | 8 / 5 |
| `side_B_environmental_maintenance` | 91.11% / 91.11% | 0.0674 / 0.0674 | 0.49% / 0.49% | 2 / 2 |

Across all 12 items, large errors fall 175 -> 138 (21.14% fewer), or 3.60% ->
2.84%. The proportion below 0.3 rises 96.40% -> 97.16%. MAE improves slightly,
but within-0.1 **falls** 84.61% -> 84.55%. These changes optimize the specified
threshold-error count, not every evaluation measure.

Different dimensions can select different source sides, so the matched numbers
cannot describe one consistent pair of physical A/B images. No such matched
columns are used for the final unlabelled batch or the desktop model workbook.
They require reference scores and must remain separate from automatic performance.

The [earlier 688-point diagnostic](ab_dimension_diagnostic_2026-10-23.md) used the
historical base mixture and a different population; do not pool or stack those
gains with this validation diagnostic. For research on actual A/B street
differences, use original canonical predictions, never per-dimension matched
columns. Individual-score validation does not itself validate gap detection.

[Aggregate diagnostic metrics and hashes](../results/scoring_2026-10-25/ab_validation405_diagnostic.json).

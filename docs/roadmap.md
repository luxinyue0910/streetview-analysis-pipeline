# Project status and next analysis

## Completed as of October 25, 2026

- Center-point image selection: 13,660 points and 27,320 selected image references.
  The final selection manifest, local reader and image-inclusive team package
  were delivered privately; source archives remain unchanged.
- Prompt and model development: V0-V6 experiments, calibration, DINO regression,
  supervised mixtures, tolerance/probability stages and low-safety experts.
  The final scorer retains Flash V2 and frozen DINOv2.
- Canonical correspondence: A = selected 0/90-degree image and B = selected
  180/270-degree image. Move images, features and side columns together.
- Final fitting on 488 development points, followed by frozen 500-point
  inference and reference comparison. There are 405 numeric-reference points
  and 95 all-NA reference points; known image overlap limits strict independence.
- Remaining 12,160-point inference: both score precisions completed, with
  145,920 scores each and independent correspondence/forward-replay verification.

See the [final method](scoring_frozen_2026-10-25.md),
[validation report](validation500_2026-10-25.md),
[completion record](full_scoring_2026-10-25.md), and
[iteration history](scoring_iterations_2026-10-23.md).

## Next: paired street-side analysis

Use the original canonical A/B predictions to study absolute side differences
by dimension, road level and spatial context. Preserve continuous scores for
threshold sensitivity and retain the one-decimal delivery as the selected format.
Large score differences are research candidates, not confirmed physical defects;
paired-error performance and spatial dependence need separate evaluation.

Reference-guided dimension-wise A/B swaps remain a
[separate diagnostic](ab_dimension_diagnostic_2026-10-25.md). They are not an
automatic scoring stage and must not be used to manufacture or remove physical
street-side differences in the research dataset.

Future changes to prompts, scoring models or output policy require a separately
versioned experiment. The evaluated 200-point historical test and 500-point
validation are no longer untouched resources. Do not report fitted training
scores as generalization evidence or relabel historical base metrics as final
extension results.

## Public and private scope

This repository publishes code for the earlier selection workflow, prompt
fragments, method specifications, hyperparameters, hashes and aggregate scoring
evidence. Private full rubrics, coordinates, annotations, image features, fitted
scoring weights, local scoring runners and per-point outputs are not distributed.
The scoring archive is not a turnkey public batch launcher.

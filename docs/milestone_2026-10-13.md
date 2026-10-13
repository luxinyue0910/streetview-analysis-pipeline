# Milestone: Final Street-View Selection and Team Handoff

Date: October 13, 2026

The center-point image-selection stage is complete under the user's accepted selection policy. VLM scoring and downstream analysis have not started.

## Scope and Final Output

| Item | Count |
|---|---:|
| Original location groups | 26,295 |
| Original images | 105,180 |
| Center locations retained | 13,660 |
| Center images before direction selection | 54,640 |
| Final image references | 27,320 |

The final CSV contains one row per center location and two selected image references, `side_a` and `side_b`. These names do not establish physical left/right orientation. All center locations and selected ZIP member references were checked.

## Method and Validation

The current selector uses frozen CLIP ViT-B/32 image features followed by an L2-regularized logistic regression classifier. It scores four images and selects the higher-scoring opposing pair. The CLIP encoder was not fine-tuned.

| Evaluation | Certain selections | Uncertain selections |
|---|---|---|
| Fixed zero-shot CLIP on 100 fresh locations | 77/84 agreement, 91.7% | 8/16 agreement, 50% |
| Lightweight classifier, five-fold point-grouped validation | 81/84 out-of-fold agreement, 96.4% | Excluded from training |
| Frozen classifier on 30 independent locations | 24/25 agreement, 96% | 2/5 agreement, 40% |

Both selected images must match the human answer for agreement; a/b ordering is ignored. These small-sample metrics are not a measured full-dataset accuracy rate. The later unflagged-case browser was changed from blind labeling to visible prediction browsing at the user's request, so it is not reported as an additional blind accuracy test.

## Review and Acceptance

The initial full run produced 11,170 automatic selections, 110 earlier human-confirmed selections, and 2,380 review candidates. Review reasons were low classifier pair margin, disagreement with the zero-shot baseline, or existing uncertain annotations. The initial margin cutoff of 0.3 is a review heuristic, not calibrated confidence.

The user confirmed 29 review locations: 28 kept the model pair and one changed the pair. The finalization policy retains all remaining existing selections, including unreviewed flagged cases, applies that one confirmed pair modification, and retains the 110 earlier human-confirmed choices.

Final rows have `status=selected`: accepted for downstream use, not individually human-verified. Prior status, original review reasons, selection source, and review outcome remain in the CSV for traceability. Original images and prediction manifests were not modified.

## Team Handoff

The local handoff ZIP contains exactly:

1. `final_selection_manifest.csv` — 13,660 rows and 27,320 references.
2. `read_selected.py` — a standalone Python standard-library reader.
3. `USAGE.txt` — English setup, validation, export, and VLM-integration instructions.

It contains no original images, source ZIPs, model weights, or environment files. The team must have the same original ZIP archives, with basenames matching the CSV's archive column. The reader can validate references without extraction, read bytes directly for a later VLM, or optionally export selected images. No GPU or model installation is needed for reading.

The packaged reader validated every selected reference and successfully read the first five locations. A manifest checksum is included in the usage instructions. Data-bearing manifests and the handoff ZIP remain local; this public repository contains source code, aggregate results, and documentation only.

## Next Stage

Define VLM scoring dimensions, scales, prompts, and model choice, then read the selected images from the final manifest. Preserve point IDs, side labels, selection provenance, model versions, and scoring configuration in subsequent results. Consider sensitivity analysis using the original review flags.

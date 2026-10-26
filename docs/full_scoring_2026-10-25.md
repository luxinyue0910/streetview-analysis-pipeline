# Remaining 12,160-point scoring: completed

As of October 25, 2026 (America/Los_Angeles), the remaining batch is complete and
independently audited. The recorded completion timestamp is
`2026-10-25T19:47:50.012738+00:00` (UTC).

## Coverage and frozen method

| Item | Count |
|---|---:|
| Final selected center points | 13,660 |
| Training-list points excluded from this batch | 1,000 |
| Validation-list points excluded from this batch | 500 |
| Remaining batch points | 12,160 |
| Selected image references | 24,320 |
| Valid Flash stage responses, three per point | 36,480 |
| Scores per output precision | 145,920 |
| Values checked across both final precisions | 291,840 |

Use the [final canonical frozen method](scoring_frozen_2026-10-25.md): Flash v2,
DINOv2, supervised mixture, low-safety gates/experts and uniform rounding. All
19 frozen artifact files match the validation500 freeze, SHA-256
`acb1db4dd55d768ac9fcdd4553706ef719c18ff8ec3831ce4aa4c66faadf481a`. No new fitting, reference labels or
reference-guided A/B swaps were used. IDs/order match the official remaining
list and are disjoint from both earlier lists. The selection deliverable from
the earlier CLIP task is unchanged.

A = selected 0/90-degree image and B = selected 180/270-degree image. Metadata
normalization reordered 5,965 points before inference. Each image byte hash,
feature row and side score is checked against that identity. This operation is
not the reference-guided diagnostic described separately.

## Completion and independent verification

- All 36,480 stage records are valid and identify `qwen3.8-flash`; raw JSON agrees
  with parsed scores. Requested sampling/output parameters and static prompt
  hashes agree with the freeze.
- Hash all 24,320 original image references; validate filenames, angles, prompt
  and image roles in every stage request. Feature order is A then B per point.
- Final feature shapes are 24,320 x 384 (CLS) and 24,320 x 2,688 (CLS + grid).
  Development parity checks are within 0.001 (CLS maximum difference
  0.00006533; grid difference 0).
- Independently replay all 12 base models and three safety modules from frozen
  weights. Maximum base and final score differences are both **0.0**; routing
  decisions agree exactly. The nine non-safety outputs equal the base outputs.
- Both CSVs have 12,160 unique points and 145,920 finite scores in [0,1]. Compare
  every delivered value with its prediction array and verify uniform rounding.
- Raw Flash contains 2,727 NA items; the frozen mixture supplies numeric final
  predictions using its established policy. Zero final NA does not mean every
  raw VLM observation was available. Safety experts route 3,735 scoring items.

## Resume and concurrency record

The API phase began with eight workers and switched to 16 after explicit user
authorization. A controlled handoff stopped the old writer before acquiring the
same exclusive run lock and starting the new writer. The only runner change was
`workers=8` -> `workers=16`; inference code, model files, prompt text, images,
preprocessing and sampling parameters were unchanged. All **10,300 already saved
valid stage responses** were rehashed and preserved. Cache checks skip valid
stage results; individual retry attempts are retained separately.

The handoff stopped eight in-flight requests, which may incur duplicate charges
if already processed by the provider. Thus 36,480 counts valid final responses,
not all billable attempts. Recorded all-attempt usage is 132,483,213 input tokens
and 4,426,183 output tokens (136,909,396 total); interrupted requests without a
returned usage record are not included. Usage is not a final provider invoice.
No model/parameter change was made to accelerate the run.

## Local team deliverables

| File | Meaning | SHA-256 |
|---|---|---|
| `full12160_one_decimal.csv` | Selected final one-decimal fused output | `3082d6743d178b337c5e5188840ddc7465dd4235a13d109dcaa5b8cd988ad37e` |
| `full12160_continuous.csv` | Same frozen method before rounding | `cfc4a9713350b625c28db6e1b83a7910af8f77e928e98d13faca1b48e718debc` |
| `full12160_flash_v2_raw.csv` | Raw Flash scores, not the final fused delivery | `af622e6d3b9bde0c149b410d704e65126312c827e064d9c688faa0b0b8c5c829` |

`full12160_flash_short_evidence.csv` and English `README.txt` are also retained
locally. The requested desktop `model-12160.xlsx` is a typed numeric conversion
of the final one-decimal CSV: all 12,160 rows, 19 columns and 145,920 scores were
compared with the CSV. No score changed during Excel conversion.

Per-point CSV/XLSX outputs, original images and raw API responses are not uploaded
to this public repository. The [aggregate completion/audit record](../results/scoring_2026-10-25/full12160_completion.json)
contains source and output hashes. Prior runs and source files were not overwritten.

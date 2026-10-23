# Qwen scoring prompt archive

These are versioned Chinese instruction fragments for local streetview scoring.
V0–V2 were used in the October 20 pilots; V3 was subsequently evaluated on
development data and was not selected. The current scoring pipeline retains V2.
Documentation is in English; prompt language is retained to reproduce the
Chinese scoring task.

Each full prompt is `prefix + private rubric text + suffix`, with no extra
separator or normalization. The original PDFs and their extracted text are not
published. Their text hashes and the composed prompt hashes are in each
version's `config.json`.

| Version | Response | Maximum output tokens |
|---|---|---:|
| `v0` | Scores, target description, visible evidence, anchors, uncertainty, NA reasons | 2,200 |
| `v1_compact` | Scores and one evidence sentence per dimension, at most 40 characters | 900 |
| `v2_organized` | Same compact response; PDF rules grouped correctly by dimension | 900 |
| `v3_evidence_aligned` | Same compact response and complete V2 rules; observation and band-condition checks revised after the 100-point development audit; evaluated, not selected | 900 |

The compact version changes output instructions and the token cap; scoring
instructions, rubric text, and stage-specific image inputs remain unchanged.
The instruction fragments are experimental baselines, not validated guidance:
known rule violations remain in the model responses.

`v2_organized` changes only private rubric organization and extraction cleanup.
The task prefix, suffix, response schema, parameters, and image bytes match
`v1_compact`. Both PDFs were checked visually page by page. The
[v2 experiment report](../../docs/vlm_organized_pilot_2026-10-20.md) records the
result, including the absence of a consistent quality gain.

[`v3_evidence_aligned`](v3_evidence_aligned/README.md) retains the complete private
V2 rubrics and adds targeted observation and evidence-to-band checks. It contains
no few-shot examples, introduces no scoring thresholds, and does not change any
active runner default. Its evaluated composed-prompt hashes are now archived in
the version config. The [scoring experiment history](../../docs/scoring_iterations_2026-10-23.md)
describes later prompt diagnostics and why V2 was retained for the final mixture.

To reproduce the organized private rubric text from the original extracts:

```bash
python scripts/organize_scoring_rubrics.py \
  --overall-text /path/to/private/overall_extracted.txt \
  --single-side-text /path/to/private/single_side_extracted.txt \
  --output-dir workspace/vlm/rubrics-v2
python scripts/render_scoring_prompt.py \
  --version v2_organized --stage overall \
  --rubric-text workspace/vlm/rubrics-v2/overall.txt \
  --output workspace/vlm/prompts-v2/overall.txt --verify-pilot-hash
```

The organizer is specific to the source documents and extraction order used
in these pilots. It checks normalized source-character conservation before
adding display headings; that check alone does not prove semantic equivalence,
which also required visual review of the PDF pages. It does not process arbitrary
PDFs and refuses to overwrite an existing output directory.

For each point, make three independent requests with no previous scores in
context: `overall` with both images, `side_A` with image 1, and `side_B` with image
2. A/B are pairing identities; target-side visibility must still be checked.

The original calls requested JSON object mode. A local validator then checked
the response. The JSON Schema here describes the compact response contract;
it was **not** sent as a strict server-side JSON Schema in these pilots.

With authorized local rubric text:

```bash
python scripts/render_scoring_prompt.py \
  --version v1_compact --stage overall \
  --rubric-text /path/to/private/overall_rubric.txt \
  --output workspace/vlm/prompts/overall.txt \
  --verify-pilot-hash
```

Exact verification requires the original extracted text, including its Unicode
characters and line breaks. A different extraction can be used without
`--verify-pilot-hash`, but then the prompt differs from this experiment.

Keep composed prompts, requests, images, per-point outputs, and CSV exports in
the ignored private workspace. Create a new version/output directory for every
experiment; do not reuse results cached under another prompt or model setting.

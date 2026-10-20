# Qwen scoring prompt archive

These are the exact authored Chinese instruction fragments used in the local
October 20 pilots. Documentation is in English; prompt language is retained to
reproduce the Chinese scoring task.

Each full prompt is `prefix + private rubric text + suffix`, with no extra
separator or normalization. The original PDFs and their extracted text are not
published. Their text hashes and the composed prompt hashes are in each
version's `config.json`.

| Version | Response | Maximum output tokens |
|---|---|---:|
| `v0` | Scores, target description, visible evidence, anchors, uncertainty, NA reasons | 2,200 |
| `v1_compact` | Scores and one evidence sentence per dimension, at most 40 characters | 900 |

The compact version changes output instructions and the token cap; scoring
instructions, rubric text, and stage-specific image inputs remain unchanged.
The instruction fragments are experimental baselines, not validated guidance:
known rule violations remain in the model responses.

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

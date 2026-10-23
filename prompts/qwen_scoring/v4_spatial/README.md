# V4: spatial target and visible-relation observations

**Status: evaluated development experiment; not selected.** Based on the V2
organized rubric, not a replacement of the rubric itself.

V4 asks the model to locate the target street edge and distinguish the walking
route, barrier relation, vehicle relation, canopy coverage and staying support
before scoring. Observations use enumerated categories. The overall request
contains two ordered observation objects; a side request contains one.

The four score dimensions and short evidence fields remain. Full V2 rubric
bytes are unchanged. The archive separates authored prefix/suffix instructions
from the privately supplied rubric. `config.json` contains exact full-prompt
hashes, model settings and image/observation counts.

## Recorded evaluation

The 60-point pilot compared a fresh V2 baseline with V4. On 710 common numeric
items out of 720 reference items:

| Prompt | Within 0.1 | MAE | Error ≥0.3 | Total NA outputs |
|---|---:|---:|---:|---:|
| V2 baseline | 55.21% | 0.1586 | 22.11% | 5 |
| V4 spatial | 54.79% | 0.1558 | 21.27% | 6 |

The targeted safety/greenery comparison improved MAE, but low-score safety
worsened and NA coverage did not meet the promotion rule. The pilot did not
justify replacing V2. These are selected development cases, not the independent
200-point test. See the [diagnostic metrics](../../../results/scoring_2026-10-23/prompt_diagnostics.json)
and [experiment history](../../../docs/scoring_iterations_2026-10-23.md).

## Reproduction contract

Use the [prompt renderer](../../../scripts/render_scoring_prompt.py) with
`--version v4_spatial`, the appropriate stage, the full private V2 organized
rubric, and `--verify-pilot-hash`. This composes text only and makes no API call.
The runtime used `qwen3.8-flash`, temperature 0, thinking disabled, JSON-object
output and a 900-token cap.

`response.schema.json` documents the locally validated response structure,
not an API-enforced structured-output schema. The runner also required the
observation count specified by `config.json` for the chosen stage.

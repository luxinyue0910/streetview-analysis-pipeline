# V5: safety-only route diagnosis

**Status: evaluated development experiment; not selected.** This branch was
informed by spatial-target errors, but it does not replace all four dimensions
with a fifth complete scoring prompt.

V5 asks only for `pedestrian_safety`, with observations of route type,
continuity, obstruction and visible supporting evidence. It distinguishes an
independent pedestrian route from shared vehicle space, a missing route, and
an unobservable route. Overall uses two ordered observation objects; a side
uses one. Three stage calls produce **three safety scores per point**, not 12.
The other nine scores in composite pilot reports came from V2, not this prompt.

## Recorded evaluation

The 60-point pilot has 180 possible safety scores. The matched comparison uses
174 numeric pairs:

| Prompt | Within 0.1 | MAE | Error ≥0.3 | Total safety NAs |
|---|---:|---:|---:|---:|
| V2 baseline | 50.00% | 0.2149 | 33.91% | 1 |
| V5 safety only | 57.47% | 0.1736 | 25.29% | 6 |

Numeric safety error improved, but five new NAs and no resolved NA failed the
predefined promotion gate. The numeric subset alone was insufficient to accept
the replacement. See [the aggregate result](../../../results/scoring_2026-10-23/v5_safety_only.json).
This was development diagnosis, not independent testing.

## Reproduction contract

Supply the **full private V2 organized rubric** to the
[renderer](../../../scripts/render_scoring_prompt.py) with
`--version v5_safety_only`. Its documented transformation retains the exact text
before `## 2.2`: the heading, general principles and complete safety definition,
bands and limits. Whitespace is retained. This selects the safety section;
it does not paraphrase or rewrite the PDF rules. An input without exactly one
cutoff heading is rejected. Use `--verify-pilot-hash` to check the composition.

The config records the hash of the transformed private rubric and complete
prompt for each stage. No private rubric bytes are published. The runtime used
Flash, temperature 0, thinking disabled, JSON-object output and 900 output
tokens. The response schema documents local validation; stage-specific
observation counts are recorded in the config.

# V2 organized-rubric pilot and error diagnosis

## Experiment scope

This follows the [initial Qwen pilots](vlm_pilot_2026-10-20.md). The same three
training points, six original images, and independent overall/A/B calls were
used with `qwen3-vl-plus` and `qwen3.8-flash`. There were 18 successful new calls.
No reference scores or sample-specific examples were sent to the models.

`v2_organized` places each definition, low/middle/high band, and hard restriction
under its proper dimension. It removes extraction line breaks and repeated table
headers, normalizes Unicode punctuation and radical glyphs, and adds explicit
section labels. Thus this is a formatting-and-organization intervention, not a
pure permutation of identical tokens. It did not change scoring criteria.

The two original PDFs were rendered and checked visually on all four pages each.
Cross-page restrictions were assigned as follows:

| Scope | Safety | Street interface | Greenery/staying | Maintenance |
|---|---|---|---|---|
| Overall | Pages 1-2 | Pages 2-3 | Page 3 | Pages 3-4 |
| Single side | Pages 1-2 | Pages 2-3 | Page 3 | Page 4 |

All nine numeric anchors were checked in each of eight dimension/scope blocks.
A normalized source-character conservation check verified that source rule text
was not lost or added before new display labels. This mechanical check does not
replace the visual check of rule meaning and chapter assignment.

Task prefix, scope suffix, image bytes/order, output schema, `temperature=0`,
`enable_thinking=false`, and `max_tokens=900` were unchanged. All 18 responses
passed compact formatting checks. Prior experiments and the delivery CSV were
verified unchanged by SHA256. These checks establish traceability and format
validity, not correct scores.

## Matched comparison

The private reference is a previous AI-assisted annotation set, not independent
human ground truth. The table uses the same **30 numeric cells** across both
models, both versions, and the reference. This differs from the earlier
three-model v1 report, which used 31 common cells. The averages should not be
compared across those different denominators.

| Model | Version | Reference mean absolute difference | Exact / 30 | NA / all 36 |
|---|---|---:|---:|---:|
| VL Plus | v1_compact | 0.133 | 10 | 3 |
| VL Plus | v2_organized | 0.147 | 10 | 4 |
| 3.8 Flash | v1_compact | 0.087 | 13 | 0 |
| 3.8 Flash | v2_organized | 0.117 | 9 | 0 |

VL Plus changed 16/36 cells, including one numeric maintenance value becoming
NA. Flash changed 15/36 and retained zero NA. Raw scores were not corrected or
filtered to improve the comparison. NA transitions and factual problems require
separate inspection; numeric-only averages omit them.

There is **no consistent gain in reference agreement in this trial**. That does
not prove that clearer rules reduce task accuracy. There are only three points,
the reference can be wrong, and each version/model was sampled only once. Cells
within a point are correlated. Temperature zero does not guarantee reproducible
outputs; unpinned model aliases and service execution add further uncertainty.

## Cost comparison

Amounts below are CNY for three points, calculated from API-reported usage and
the October 20 Beijing rates archived in the initial report. They are not account
invoices and exclude account promotions/free quota.

| Model | Version | Input | Cached input | Output | With observed cache | Without cache |
|---|---|---:|---:|---:|---:|---:|
| VL Plus | v1 | 37,263 | 0 | 1,482 | 0.052083 | 0.052083 |
| VL Plus | v2 | 33,345 | 0 | 1,507 | 0.048415 | 0.048415 |
| Flash | v1 | 40,788 | 26,624 | 1,057 | 0.016848 | 0.035484 |
| Flash | v2 | 32,403 | 19,456 | 1,112 | 0.015306 | 0.028925 |

Input token counts fell after extraction cleanup; output tokens rose slightly.
Cache hit rates differed, so observed cost differences alone do not isolate
prompt efficiency. Both cache-aware and no-cache calculations are retained.

## What the evidence can and cannot diagnose

**Visual grounding and observation-unit errors are clearly present.** In the
bridge scene, VL Plus's overall evidence claimed public seating not clearly
supported by the image. Flash's overall evidence claimed there were no street
trees even though the second image visibly contained a tree row. A bad factual
premise can lead to a bad score even if the subsequent rule mapping is correct.
Target-side selection and visible extent are additional input/protocol risks.

**Rule application errors are also clearly present.** In the mixed wall/shop
scene, VL Plus raised overall street interface to 0.8 while the clear visual
contrast remained one closed side and one open side. The rubric places that
pattern in the middle band. Earlier outputs also assigned high greenery scores
without establishing separate usable staying support. These errors cannot be
explained solely by unfamiliarity with the visible objects.

**Evidence prose is not an execution trace.** A model can write a plausible
sentence after selecting a score; it does not prove that it actually used that
sentence to choose the score. These are qualitative, inspectable examples, not
a complete adjudication or a quantified error decomposition. The three-point
trial cannot establish which source accounts for most errors.

The working assessment is that visual grounding/target-side identification
dominates some severe ambiguous-scene errors, while anchor compliance remains
a separate issue even in clear scenes. Merely reorganizing the PDF addresses
instruction readability; it does not directly validate visual facts or enforce
score eligibility.

## Proposed next steps; not run in this commit

1. **Measure stability before claiming a prompt gain.** Repeat v1/v2 on the
   diagnostic examples, preferably using pinned model snapshots. Quantify how
   often the same cell changes without changing its prompt. Keep the existing
   three points as known debugging examples, not fresh validation data.
2. **Separate perception from rule mapping in a small diagnostic.** First ask
   for short categorical observations without scores: target side/visibility,
   walkway continuity, actual tree coverage of the walking route, identifiable
   seats or separate staying space, and specific maintenance defects. Review
   these observations against the images. Separately give verified facts to a
   scorer with the same rubric, without supplying reference scores. Errors with
   correct supplied facts indicate rule mapping problems; incorrect image facts
   indicate perception/side-selection problems. This is a diagnostic, not a
   claim that a two-call production pipeline has been validated.
3. **Test an evidence-to-eligibility prompt.** Before selecting a high greenery
   band, require observable evidence of the rubric's greenery/coverage and
   usable seating or independent staying conditions. Middle-band rules for a
   closed/open side contrast must be explicit. Maintenance deductions must cite
   physical defects, not age or aesthetics. Preserve uncertain visibility as
   distinct from confirmed absence; do not force a low score to avoid NA.
4. **Keep diagnostic fields separate from delivery fields.** A short feature
   record and anchor identifier can make contradictions inspectable, but neither
   proves truth. Keep them in internal outputs, measure added tokens, and retain
   the existing 21-column delivery format. No silent score clipping or NA
   replacement should be presented as a prompt improvement.
5. **Evaluate on fresh training-only points.** Use a fixed 20-30 point set with
   reviewed reference scores, distinct from prompt examples and the current
   debugging points. Report dimension/scope agreement, visible-fact errors,
   hard-rule violations, NA decisions, variability, and cost. Reserve the
   500-point validation set for the final selected configuration. Add a few
   verified examples only after an initial zero-shot diagnostic, as a separately
   versioned intervention.

Start with 3.8 Flash and retain VL Plus as the comparator. Change one substantive
component at a time. Do not spend a full-data run on a version that has only
changed its aggregate reference distance on three already-inspected points.

## Reproduction and data boundary

Published artifacts:

- [V2 prompt fragments, configuration and schema](../prompts/qwen_scoring/v2_organized/).
- [Aggregate matched comparison](../results/vlm_organized_pilot_2026-10-20.json),
  with no coordinates or per-point changes.
- A document-specific [rubric organizer](../scripts/organize_scoring_rubrics.py)
  that reproduces the organized text from the original authorized private
  extracts, and the existing versioned prompt composer with v2 support.

The original PDFs, full rubric text, composed prompts containing that text,
images, per-point evidence, annotations, review pages, and API responses remain
private. The prompt configuration includes source and composed hashes plus PDF
page mappings. See the [prompt archive instructions](../prompts/qwen_scoring/README.md)
for local reconstruction. No new production scoring runner or automatic
correction policy is introduced here.

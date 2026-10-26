# Final canonical scoring evidence

Aggregate-only extracts of existing local experiments; no new training, API calls
or reference-based prediction changes were performed for this publication.

| File | Scope |
|---|---|
| `canonical_cv488.json` | Same spatial nested development folds, before/after canonical refit; both precisions and failed regression guard |
| `validation500.json` | 500 prediction rows, 405 numeric reference points; fixed A/B, 12 targets, both precisions, raw NA coverage and matched numeric subset |
| `ab_validation405_diagnostic.json` | Reference-guided per-dimension swaps, strictly reducing >=0.3 counts; separate diagnosis only |
| `full12160_completion.json` | 12,160-point coverage, independent forward replay, correspondence, output hashes and concurrency handoff |
| `methodology_formula_audit.json` | Read-only formula-code checks: 12 fitted trees, three safety wrappers, decoder parity, existing 500-point replay and 20 full-batch points; no new fitting or API requests |

Metric fields ending `_pct` are percentages. `hit_rate` and `severe_rate` in the
canonical CV extract are fractions; its `ccc` is pooled CCC, not macro target CCC.
Thresholds are inclusive <=0.1 and >=0.3 with floating-point tolerance. Rounding
is `floor(10*p+0.5)/10`, never reference-dependent rounding.

Each extract identifies its local source experiment and source-file hash without
publishing absolute private paths. Some source records retain their original UTC
timestamps. Point IDs, coordinates, image names, split membership, reference rows,
per-point predictions, fitted coefficients, private PDFs and API credentials are
not included. Fitted artifact paths contain target names only.

The 500-point list has distinct IDs from development but a known overlap of four
image hashes at two retained points. All-NA reference rows are excluded from
evaluation, not from delivery. Full batch coverage is not measured accuracy.

See [final method](../../docs/scoring_frozen_2026-10-25.md),
[validation](../../docs/validation500_2026-10-25.md),
[completion](../../docs/full_scoring_2026-10-25.md), and
[separate A/B diagnosis](../../docs/ab_dimension_diagnostic_2026-10-25.md).

# V3: evidence-aligned scoring candidate

This version applies findings from a visual audit of all 100 development points.
It was **evaluated on the same 100 development points and not selected** as a
general replacement for V2. It includes no few-shot images or reference scores.
The 200-point stage-check set and final validation set were not used to author it.

The complete private V2 organized rubrics are inserted byte-for-byte between each
prefix and suffix. Definitions, bands, anchors, hard limits, response schema and
inference settings are unchanged. The extra instructions guide observation and
rule application; they do not replace the rubric or create new scoring thresholds.

Changes address actual walking-route geometry, object function, ground-floor
access, both under- and over-scoring of greenery/staying, maintenance severity,
per-dimension observability, and independent overall assessment of both images.
The previous warning against a fixed maintenance score of 0.8 is replaced with
neutral checks of evidence and band conditions. No specific score is a default.

Each request returns four scores plus four short evidence sentences; the three
independent requests yield 12 scores per point. No delivery CSV columns change.
Use `render_scoring_prompt.py --version v3_evidence_aligned` with the same
private rubric texts used by V2. `--verify-pilot-hash` checks the archived
evaluated prompt hashes. Keep rendered full prompts in private internal storage
and use a new output directory for any future experiment. No runner or model
default is switched by archiving this version.

Before claiming improvement, compare against the fixed V2 development baseline,
including per-dimension errors, bias, large errors, NA and evidence accuracy.
Check both favorable and adverse cases; do not expand score variance artificially.
The development set is an optimization set, not independent final validation.
The V3 trial used the reference available at that time; the later accepted
reference replacement and final supervised results are recorded separately in
the [experiment history](../../../docs/scoring_iterations_2026-10-23.md).

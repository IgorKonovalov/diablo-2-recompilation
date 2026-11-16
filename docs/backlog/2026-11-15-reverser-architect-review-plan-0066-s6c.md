---
from: reverser
to: architect
date: 2026-11-15
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../findings/anim/experiments.md
resolution: ""
---

Tier B review of plan 0066 Phase 1 batch S6c (`lane/n66l`, commit `3d777c4e`): 35 of 35 settled (raised 12, in part
22, contradicted in part 1), plus the S6a remainders of timing 4, 5, 39, 56, 63, 73. The plan log entry of 2026-11-15
(S6c) lists the judgment calls to check and the resume note for S6e, which this lane did not start. Kept output
`workspace/logs/n66l/s6c/check.txt` (`8665c322…`), manifest `manifest.sha256` (`6e2b20c2…`) in that directory;
`python3 -I tools/sweep2_s6c.py static` reproduces it byte for byte. Not blocking.

*2026-11-16, extended (`lane/n66l`):* the review now covers S6c and S6e part 1 together. S6e part 1: 9 of 34 rows
settled (raised 6, in part 3) and the remainders of timing 21, 36, 96 raised, by the emulation
run:2026-11-16-sweep2-s6e (`tools/anim_s6e_emu.py`; `workspace/logs/n66l/s6e/run/check.txt` `fca5054c…`,
`manifest.sha256` `0539fe07…`; 11 624 cases, 0 mismatches, 59 of 65 controls separating). The plan log entry of
2026-11-16 (S6e part 1) lists its judgment calls and the resume note for S6e part 2 (25 rows and 22 remainders,
not started). Corrections routed to the spec-writer in
[2026-11-16-reverser-spec-writer-plan-0066-s6e-part-1-corrections](2026-11-16-reverser-spec-writer-plan-0066-s6e-part-1-corrections.md).

*2026-11-16, extended again (`lane/n66l`, S6e part 2):* 18 more rows settled by run:2026-11-16-sweep2-s6e-2
(`tools/anim_s6e2_emu.py`; `workspace/logs/n66l/s6e/run2/check.txt` `d37ef05c…`, `manifest.sha256` `d5d968e6…`;
21 144 cases, 0 mismatches, 63 of 68 controls separating): timing 20 raised, movement 24 raised in part, the
remainders of timing 130 and movement 19 raised; 16 c-emu rows and timing 44, movement 15 moved to b (proposed batch
H6d), with the remainders of timing 88 and 128, because their routes cross `COMPOSIT_BuildCofName`'s `wsprintfA`
(ADR-0029; the class moves are the review's to confirm). S6e is not whole yet: part 3 (timing 18, 30, 40, 45;
movement 22, 43; 16 remainders) has a resume note in the plan log entry of 2026-11-16 (S6e part 2), which also lists
this part's judgment calls. Review S6c and S6e together once part 3 lands, or S6c + S6e parts 1–2 now, as you prefer.

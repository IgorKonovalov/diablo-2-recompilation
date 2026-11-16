---
from: reverser
to: architect
date: 2026-11-16
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../findings/combat/experiments.md
resolution: ""
---

Tier B review of plan 0066 Phase 1 batch S5e part 1 (`lane/n66t`): the combat reduction and to-hit leaf
functions. Emulation run:2026-11-16-sweep2-s5e (`tools/combat_s5e_emu.py`; `workspace/logs/n66t/s5e/run/check.txt`
`100ff7eb…`, `manifest.sha256` `44d94245…`, passes from that directory; 17 300 cases, 0 mismatches, 118 of 127
controls separating, the 9 others named). 23 of the batch's 52 statements settled; outcomes, the remainders, totals,
judgment calls and the resume note for part 2 are in the plan log entry of 2026-11-16 (S5e part 1). Corrections to the
spec-writer in [2026-11-16-reverser-spec-writer-plan-0066-s5e-corrections](2026-11-16-reverser-spec-writer-plan-0066-s5e-corrections.md).
Not blocking.

---
from: reverser
to: reverser
date: 2026-10-17
status: open
context:
  - ../findings/stats/0001-aggregate.md#open-questions
resolution: ""
---

moved from the plan 0041 P1 review follow-ups entry, item (c) (optional; not taken by the `lane/rbs` static sweep, 2026-10-17): an ADR-0015 emulation (`tools/ghidra.sh emutrace`) of `STAT_ByTimeValue` (0x0065CA30) and `sub_00626200_StatEvaluate` cases 6/7 over a declared image, the only route to settle the contradicted op 6/7 lead past `[I]` (no stock path reaches it).

*2026-10-20 (reverser, `lane/p49r`, plan 0049 Phase 1):* not taken. It is optional, no tag depends on it, and it needs
no slot. No plan takes it: it is out of plan 0049 and stays open for a later static lane with Ghidra emulation time.

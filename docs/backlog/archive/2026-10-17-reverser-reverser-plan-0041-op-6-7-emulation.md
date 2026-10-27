---
from: reverser
to: reverser
date: 2026-10-17
status: done
context:
  - ../../findings/stats/0001-aggregate.md#open-questions
resolution: "done 2026-10-27 (lane/p51s, plan 0051 Phase 1b): op 6/7 emulated, 9 000 calls, 0 mismatches, [C] as a code map in [stats/0001 § 10](../../findings/stats/0001-aggregate.md#10-op-6-and-7-under-emulation-run2026-10-27-p51s-emu-plan-0051-phase-1b) (run:2026-10-27-p51s-emu)"
---

moved from the plan 0041 P1 review follow-ups entry, item (c) (optional; not taken by the `lane/rbs` static sweep, 2026-10-17): an ADR-0015 emulation (`tools/ghidra.sh emutrace`) of `STAT_ByTimeValue` (0x0065CA30) and `sub_00626200_StatEvaluate` cases 6/7 over a declared image, the only route to settle the contradicted op 6/7 lead past `[I]` (no stock path reaches it).

*2026-10-20 (reverser, `lane/p49r`, plan 0049 Phase 1):* not taken. It is optional, no tag depends on it, and it needs
no slot. No plan takes it: it is out of plan 0049 and stays open for a later static lane with Ghidra emulation time.

*2026-10-27 (reverser, `lane/p51s`, [plan 0051](../../plans/0051-backlog-sweep-6.md) Phase 1b, no slot):* **done.**
`STAT_ByTimeValue` (6 000 calls) and `sub_00626200_StatEvaluate` cases 6 and 7 (3 000 calls, with
`sub_0061C100_ActTimeOfDay`, `MulDiv`, ops 10, 12 and above 13 between them, nested sources) ran under `tools/ghidra.sh
emutrace` over a declared image. They match `tools/sweep_p51s.py`'s models with 0 mismatches, every branch reached,
0 undeclared reads and 0 stops. Negative controls: the lead's "op 6/7 add nothing" fails 2 110 cases, and op 7 on the
own sum fails 1 103. [C] as a code map (ADR-0015), run:2026-10-27-p51s-emu:
[stats/0001 § 10](../../findings/stats/0001-aggregate.md#10-op-6-and-7-under-emulation-run2026-10-27-p51s-emu-plan-0051-phase-1b),
with the contradicted lead's detail updated. What `owner +0x1C` and its `+0x04` record hold in play stays `[I]` (an
Open question of stats/0001).

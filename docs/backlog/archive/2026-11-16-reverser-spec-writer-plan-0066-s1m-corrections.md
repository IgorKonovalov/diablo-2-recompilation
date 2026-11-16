---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/ai/experiments.md
  - ../../plans/0066-inventory/monsters-ai-machinery.md
  - ../../plans/0066-inventory/monsters-ai-README.md
resolution: "Plan 0066 Phase 3, monsters/ai cluster part 1 (lane/n66ai): items 1–5 in the specs: machinery B7a (the nine helpers) and the entry-point row, an Open questions line for MonSetMode's A1/A2 draws (item 2, [I]), README H4 and machinery T20c raised with row 20 in H1's table, README E8a, README C2a and the worked example ([README](../../specs/monsters/ai/README.md), [machinery](../../specs/monsters/ai/machinery.md))."
---

Phase 3 of plan 0066 (monsters/ai cluster): corrections and refinements found by batch S1m (`lane/n66m1`,
[run:2026-11-16-sweep2-s1m](../../findings/ai/experiments.md#run2026-11-16-sweep2-s1m)), to take when the machinery and
README specs are re-tagged. Not blocking.

1. **Machinery entry points and B7 (inventory machinery row 3).** `MonSetMode` is called directly by nine AI helpers
   besides the five commands of the table: `MonAiWanderNearUnit` (1 561 logged calls), `MonAiMoveToUnitDist` (453),
   `MonAiMoveToPoint` (210), `MonAiWalkToPoint` (198), `MonAiWalkToPointCmd` (134), `MonAiWalkToPointOrStop` (42),
   `MonAiWalkToUnitOrZero` (34), `MonAiIdle` (4), `MonAiWanderRingDirect` (4). B7 groups `WalkZ` and the point forms
   "around `MonAiMove`"; the logs show them commanding through their own `MonSetMode` call. Say so, or scope the
   entry-point row.
2. **Machinery § F, `MonSetMode` (row 55).** 75 A1/A2 commands of `SetModeAtUnit` move the unit's seed 1 or 2 steps
   inside `MonSetMode` with no `SKILLS_SrvStart` logged and no skill of that mode in the class's slots. The draw's
   source is not read; keep the row `[I]` for those and add an open question (route: read the A1/A2 mode start).
3. **Machinery T20c and README H4 (rows 67, 69, README 45).** Row 20 now meets H1: 0x005F283F is told apart by the
   unit's next AID word `+0x14` (59 cleared, 11 kept). T20c's "stays a reading" and H4's "fails none alone" are replaced
   by the `[C]` of the record; H1's table gains row 20.
4. **README E8 (row 36).** States 10 (594 decisions) and 11 (36) occur in the Countess launches of run:2026-11-04-ai-r5
   with no curse cast, so `CurseSetAiState` is not their only setter. E8's claim is untouched; a note avoids reading it
   as the only route.
5. **README C2 and the worked example (rows 18, 47).** 68 of 2 573 last-call `Idle(n)` decisions are followed by an AID
   in mode NU 1 to 7 frames before `fr + n`: another queue wins. State it beside the "next event at `T + n`" reading.

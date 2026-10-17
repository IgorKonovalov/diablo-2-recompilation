---
from: reverser
to: archivist
date: 2026-10-17
status: open
context:
  - ../plans/0041-stats-and-states.md#implementation-log
resolution: ""
---

[2026-10-17] from reverser → archivist: plan 0041 Phase 1, readers for the table docs (not blocking). (a) [ItemStatCost § Record layout](../tables/ItemStatCost.md#record-layout): `ITEMSTATCOST_Load` (0x00637A00) fills the tail: `+0x051` = has dependents (a row with an `op` target, and every row named as an `op base`), `+0x052` = has op inputs, `+0x053` = op 4 or 5, `+0x05E` = the rows whose `op base` is this row, `+0x0DE` in source-row order; it zeroes an `op` outside 1..13 and sets run-time marks `+0x004` bits 5–7 and `+0x005` bit 0 on rows linked to 7, 9, 11; `keepzero` is the byte `+0x050` (`STATLIST_CacheAdd`). (b) [Shrines § Effects](../tables/Shrines.md#effects-plan-0041-phase-0): the code → (stat, state) table `g_ShrineEffects` (0x006E1850) confirms the name pairing for all ten; `Arg0` is the stat value of codes 6, 8–11, 13, 15; `Arg1` the damage % of code 7; `reset × 1200 + 1` frames to re-arm. (c) [States](../tables/States.md): `group` read by `STATE_GroupClear` (0x0056C740); `curse`, `plrstaydeath`, `monstaydeath`, `exp`, `aura` readers in [stats/0002](../findings/stats/0002-states.md); 22 of the 56 unnamed rows placed (§ Phase 0 surprise (f)). (d) [Skills](../tables/Skills.md): `perdelay` (`+0x128`) is the aura period (`SKILLS_NextPeriodicFrame`, min 5); `passiveitype` is the param of the passive stats. (e) [Objects](../tables/Objects.md): wells (OperateFn 22) read `Parm0` re-arm delay, `Parm1` heal in 1/256 of the maximum, `Parm3` bits 0 mana and 1 life. Context: [plan 0041 log](../plans/0041-stats-and-states.md#implementation-log)

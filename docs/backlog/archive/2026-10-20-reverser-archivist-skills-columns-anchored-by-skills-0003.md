---
from: reverser
to: archivist
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0003-handlers.md
  - ../../tables/Skills.md#dispatch-plan-0045-phase-0
resolution: "Done 2026-10-20 (archivist, lane/p46a, plan 0046 P0): Skills srvprgfunc, srvmissilea..c, prgcalc1..3, auraevent*, repeat/leftskill/weapsel, TgtPlaceCheck, petmax/pettype; ItemStatCost itemevent*; States srvactivefunc; PetType group; Missiles Vel/VelLev and SubStart/SubStop, all [I] with skills/0003 links; the do table's users are in Skills § Function index [../tables/Skills.md#function-index-plan-0046-phase-0]"
---

From plan 0045 P1.3 (`lane/p45h`); not blocking. Code readings that can anchor table-doc meanings (each `[I]` in [skills/0003](../../findings/skills/0003-handlers.md); the doc's own tags are yours): Skills `srvprgfunc1..3` index `g_SkillDoFuncs` (§ 1, `COMBAT_PrgFinisher`); `srvmissilea`/`b`/`c` and `prgcalc1..3` are picked by the progressive charge count 1/2/3 (`sub_005D3CF0_SkillSrvMissileByCharge`, `sub_005D3DA0_SkillPrgCalcByCharge`); `auraevent1..3`/`auraeventfunc1..3` register `g_StatEventFuncs` handlers (§ 3); `repeat`, `leftskill`, `weapsel` have no server reader (§ 12); `TgtPlaceCheck` is read by the monster AI's target test `sub_005FD470_MonSkillTargetOk` (§ 12); `petmax` is the pet limit and PetType `group` clears the other types of the group (§ 7). ItemStatCost `itemevent1..2`/`itemeventfunc1..2` register the same handlers (§ 3). States `srvactivefunc` indexes `g_SkillDoFuncs` through `sub_0056D790_StateDoFunc` (146 Armageddon, § 9). Missiles `Vel`/`VelLev` (`+0x9A`/`+0x9B`) are read as bytes by `0x00663270`, and `SubStart`/`SubStop` loop the frame counter of do 5 (§ 6).

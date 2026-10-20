---
from: reverser
to: reverser
date: 2026-10-17
status: done
context:
  - ../../plans/done/0039-backlog-sweep-4.md#implementation-log
resolution: "2026-10-20 (lane/p49r, plan 0049 P1), all five answered. (a) 0x005C09E0 is STATEVENT_Reanimate, itemeventfunc 31 of the item property reanimate (stat 155; Tomb Reaver, Faith), not a skill. (b) FormationSpawn case 5 is never reached: both callers pass owner 0. (e) MissileSpawnOwnedMonster is missile do-function 13, bonewallmaker of Bone Wall. For (a), (b) and (e) see [items/0002 § Plan 0049 Phase 1](../../findings/items/0002-quality-roll.md#plan-0049-phase-1-2026-10-20-static). (c) Mode word 1 is the Battle.net button. (d) A saved corpse loses its stat 13. For (c) and (d) see [player/0001 § Plan 0049 Phase 1](../../findings/player/0001-creation.md#plan-0049-phase-1-2026-10-20-static). Plan 0046 can read (a) from items/0002."
---

[2026-10-17] from reverser → reverser: plan 0039 P1c residues (not blocking, static). (a) Which skill or monster uses `0x005C09E0` (pointer at `0x0073262C`, past the `srvdofunc` table), whose corpse callback `sub_005C07A0_SkillReviveDo` raises an owned monster. (b) The callers of `sub_005B3270_FormationSpawn` (0x0054E1CB in `PresetGroupSpawn`, 0x005B3559) and what its case 5 owner is. (c) The writer meaning of the create-screen mode word `0x007795EC` (1 at 0x00435B31 for client `+0x35E` = 2) that turns on status bit `0x40` by default. (d) Whether a corpse saved with its character keeps stat 13 (the 75 % of the death loss). (e) The identity of the missile behind `sub_005AEDA0_MissileSpawnOwnedMonster` (`0x0073C79C`). Context: [plan 0039 log](../../plans/done/0039-backlog-sweep-4.md#implementation-log)

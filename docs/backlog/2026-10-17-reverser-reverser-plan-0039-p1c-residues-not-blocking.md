---
from: reverser
to: reverser
date: 2026-10-17
status: open
context:
  - ../plans/0039-backlog-sweep-4.md#implementation-log
resolution: ""
---

[2026-10-17] from reverser → reverser: plan 0039 P1c residues (not blocking, static). (a) Which skill or monster uses `0x005C09E0` (pointer at `0x0073262C`, past the `srvdofunc` table), whose corpse callback `sub_005C07A0_SkillReviveDo` raises an owned monster. (b) The callers of `sub_005B3270_FormationSpawn` (0x0054E1CB in `PresetGroupSpawn`, 0x005B3559) and what its case 5 owner is. (c) The writer meaning of the create-screen mode word `0x007795EC` (1 at 0x00435B31 for client `+0x35E` = 2) that turns on status bit `0x40` by default. (d) Whether a corpse saved with its character keeps stat 13 (the 75 % of the death loss). (e) The identity of the missile behind `sub_005AEDA0_MissileSpawnOwnedMonster` (`0x0073C79C`). Context: [plan 0039 log](../plans/0039-backlog-sweep-4.md#implementation-log)

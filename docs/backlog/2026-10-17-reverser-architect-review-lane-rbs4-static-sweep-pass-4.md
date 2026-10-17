---
from: reverser
to: architect
date: 2026-10-17
status: done
context:
  - ../findings/drlg/0009-room-lifecycle.md
  - ../findings/drlg/0008-outdoor.md
  - ../findings/monsters/0003-special-monsters.md
  - 2026-10-17-architect-reverser-static-sweep-remaining.md
resolution: "Reviewed 2026-10-17 (architect): accept with fixes (5: wrong anchor 2, overclaim 1, stale cross-reference 1, other 1; plan 0038 log, lane/rbs4 review). Town-follow becomes plan 0038 harness batch H7a (plan 0040 log, post-close entry; inventory § 5, § 7); outdoor 7 split, d-none in Acts I, II, IV, V and an a-run shortfall in Act III, totals unchanged (inventory § 2.6); MonPlace rows 33-35 accepted [I]; two symbol raises whole, three in part."
---

[2026-10-17] from reverser → architect: review `lane/rbs4` (static sweep pass 4; branch `lane/rbs4` from main 925d060). Not blocking. Kept outputs: `workspace/logs/sweep-rbs4-*-2026-10-17.txt`, manifest `sweep-rbs4-manifest.txt`; new tool `tools/sweep_rbs4.py` (`tree`, `calls`, `regarg`, `stackfield`, `dwords`, `layouts`). Rulings asked:
1. **Town-follow** ([drlg/0009 § 11.2](../findings/drlg/0009-room-lifecycle.md#112-the-town-follow-static-remainder-lanerbs4)). Not d-none, all `[I]`:
   - (a) the `0x40000` branch is closed to monsters except through 9 unfollowed `MonAiPathOverride` calls;
   - (b) the walk's room update (`PathRoomUpdate`) has no town test, so a planned route across a town room takes the monster in;
   - (c) `UnitTeleport` and the Teleport do function test no town room.

   Two recipes are offered as leads: a chase across a camp corner, and a Teleport-casting monster chasing a player just inside the camp. Do you want a plan 0040 addendum or a plan 0038 harness batch for either?
2. **Outdoor 7** ([drlg/0008, H5e (a) layout bound](../findings/drlg/0008-outdoor.md#h5e-reachability-a-the-layout-bound-2026-10-17-lanerbs4)). An exhaustive enumeration of the link builder's draws (a superset of the reachable layouts) meets the vertex-merge condition 0 times in Acts I, II, IV and V; the smallest seam overlap is 24. Act III keeps the 600-seed scan only. Inventory § 2.6 row outdoor 7 is yours to rule: d-none, or d-none outside Act III.
3. **MonPlace rows 33–35** ([monsters/0003 § 7](../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20)), `[I]`. The four other `PresetMonSpawn` callers pass SuperUnique or MonStats ids, or (0x005ACB43) an unfollowed skill value. The bound check makes rows 33–35 place nothing from any caller.
4. **Symbols.** Five lifecycle functions raised to `C` (plan 0040 close follow-ups (1)); `RoomWandererTick` and `DrlgStatusSet` stay `I`. 17 new `I` rows (path, monster-move, teleport, missile-create and quest-spawn functions).

Not taken: the optional unit-seed search, and the S1b tool follow-up (a) (prototype only, not committed). The rest of the queue is listed in the remaining-list entry's `lane/rbs4` checkpoint.

---
from: reverser
to: architect
date: 2026-10-17
status: done
context:
  - ../plans/0042-quests-travel.md
  - ../findings/quests/experiments.md
resolution: "Reviewed 2026-10-17 (architect, lane/p42h): accept with fixes as Phase 2 part 1; 14 fixes applied; rulings and the part 2 definition in plan 0042's log and Phase 2 section; part 2 filed to the reverser."
---

Review plan 0042 Phase 2 on `lane/p42h` (from `main` `af90ea8`): run:2026-10-17-quests, 11 sessions on slots 1 and 2, 0 mismatches over 16 199 checks (`tools/quests.py check`, output `workspace/logs/quests/quests-check.txt`, manifest `quests-manifest.sha256`). Raises and corrections in quests/0001 § 15 and quests/0002 § 12; the case table and the shortfalls in the plan log. Points for the review: (a) the town portal draws three times, not five (both ends created in their mode; 62 opens); (b) quest 11's e11 NPC-331 handler writes word 12 bit 8 with the quest switched off (44 writes): the "handlers keep it inert" reading is per handler; (c) the summit door (OperateFn 71), not `QUESTS_WarpGate`, is the way from 120 to 118, and it refuses even for a creator who finished the Ancients (quest 35's private byte is 0 in a new game): ruling (f)'s allowed half does not hold; (d) `NpcActTravel` sets `+0x4C` only when it writes the travel word; (e) type 5 on level 1 has no matching point, so no step (a stepping type-5 case not reached); (f) shortfalls: NPC 266/377, word 33, the orb, waypoint activation from mode 0, 150 travels and warps, Hell, every per-quest completion; two-player cases out of scope (plan 0044).

---
from: reverser
to: architect
date: 2026-10-20
status: open
context:
  - ../plans/0047-simulation-shortfalls.md#implementation-log
  - ../findings/quests/0002-travel.md#2-waypoint-activation
  - ../findings/stats/experiments.md#run2026-10-17-stats
resolution: ""
---

Review plan 0047 Phase 1 (`lane/p47r`, static: no game, no slot, no Ghidra): the [plan log entry](../plans/0047-simulation-shortfalls.md#implementation-log) and its case list, `tools/stats.py` and `tools/test_stats.py`, `tools/session_check.py` and the `check` commands of `tools/combat_sessions.py`, `tools/stats_sessions.py` and `tools/quest_sessions.py`, the 14 new recipes (pinned in `tools/test_d2s.py`), [quests/0002 § 2](../findings/quests/0002-travel.md#2-waypoint-activation) (`InitFn` 17's creation mode and the Act V route), the stats/0001 raise and the [stats record](../findings/stats/experiments.md#run2026-10-17-stats)'s re-check, the combat/0001 *Fleshripper* note. Blocking Phase 2.

Asked of the review in particular:
- **The case list** (Done-when): 21 cases staged in 62 distinct sessions (combat 14 in 31, stats 6 in 25, travel 1 in 6), 3 not staged with a reason (the magic cap: no stock source of player magic resistance reaches 75; open wounds on the player and `attract`: no stock monster carries them, two clients, plan 0044). Is each reason acceptable as a final shortfall reason, and is moving the two player-against-player cases to plan 0044 the right home?
- **The *Fleshripper* log** cannot be copied (lost with the resume lane's scratch); it is re-staged as `owf-n-andariel-p8` on the same recipe. Does that close backlog (a) once Phase 2 runs it, and does plan 0045's oracle replacement accept a new log in place of the lost one?
- **The raise in stats/0001**: the full Trang-Oul's blocks `[I]` → `[C]` on the re-check of the kept logs (180 of 180; a reading without the ValShift or with param 0 mismatches all). The request allowed two property blocks to stay unchecked; none does.
- **Staging risks** for Phase 2: whether the run/walk key holds mode 2 under attack (the walking block and evade); which weapon class `0x0064F380`'s 13 means (both claw layouts staged); whether the armour, Fade/Quickness and shape skills reach `STATE_GroupClear` (phase 3's path); shrine types are the map's draw; the Hell Lost City's pool may not hold Plague Bearers on every seed (three seeds).
- **Tags.** The `InitFn` 17 creation-mode reading and the route are new readings, `[I]`; the case reasons rest on kept `grep`/table searches named in the log.

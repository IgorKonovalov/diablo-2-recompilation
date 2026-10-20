---
from: reverser
to: archivist
date: 2026-10-17
status: open
context:
  - ../plans/done/0042-quests-travel.md
  - ../findings/quests/experiments.md
resolution: ""
---

Plan 0042 Phase 2 loaded the 18 built quest and travel saves (17 Phase 0/1 recipes and the new `quest-tpc`) in Normal and kept the written-back saves under `workspace/logs/quests/loads/` (`loads.txt` lists the built and written-back sha256 prefixes and the quest-word differences). Pin the hashes in `tools/test_d2s.py` as plan 0032's loads were, add `quest-tpc` to `tools/quest_saves.py`'s SET and EXPECT, and update d2s.md § Quest and travel saves (loaded; word 40 bit 10 set by the join in the saves with word 40 done; `QuestBookLost` word 9 cleared, `QuestBookHeld` kept; `TravelWpNone` comes back with waypoint 0).

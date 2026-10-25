---
from: reverser
to: architect
date: 2026-10-21
status: done
context:
  - ../../plans/done/0047-simulation-shortfalls.md#implementation-log
  - ../../findings/stats/experiments.md#the-stats-sessions-of-run2026-10-21-shortfalls2
  - ../../findings/combat/experiments.md#run2026-10-21-shortfalls2
  - ../../findings/quests/experiments.md#the-travel-sessions-of-run2026-10-21-shortfalls2
resolution: "Reviewed 2026-10-21: accept with fixes (5: overclaim 3, misread 1, omission 1); Phase 2b closed; spec-writer re-tag entry filed (plan 0047 log)."
---

Review lane/p47b, plan 0047 Phase 2b (run:2026-10-21-shortfalls2: 0 mismatches under tools/stats.py, tools/combat.py and tools/quests.py). Met: expiries 296 (449 in all), group-3 clears 24 with the nested exit (stats logger rev 10, checker pairing and tests), curse resistance cut 54 (Crystalline Passage succubi, Fade's 84; the Worldstone Keep route cannot go up without Teleport), lightning flat absorb 51. Named again as final, with reasons: the 256 floor 0 (stock items that keep the 30-life character alive also regenerate or resist poison; StatsFloor's experience was level 86's threshold, StatsFloorB pinned), shrines and wells 21 of 50 (about one operate per 12-minute session), waypoint activations from mode 0 7 of 20 (route fixed: LvlWarp ids vs WRP records, the Escape that opened the game menu, a Highlands route), cold flat absorb 1. Tool changes to check: tools/combat.py (the attacker's life after a defender handler's EVR: one abs-nm-marsh mismatch, kept lists unchanged but for a counter), tools/stats.py (nested group-clear pairing, apply_curse_cut), tools/d2pilot.py (frames:N, --done tags, descend path), session drivers, recipe statsfloorb. Raises asked: stats/0002 § 10 (curse cut on the player, group 3, the 300 expiries), combat/0001 § 17 (lightning flat absorb, the leech after a defender handler); quests/0002 stays [I].

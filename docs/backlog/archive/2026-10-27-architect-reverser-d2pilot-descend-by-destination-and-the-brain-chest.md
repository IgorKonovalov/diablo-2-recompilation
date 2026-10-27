---
from: architect
to: reverser
date: 2026-10-27
status: done
context:
  - ../../findings/items/experiments.md#run2026-10-27-sweep-quest-items
  - ../../findings/items/0010-quest-drops.md#open-questions-h6e2
resolution: "lane/rdp (static): (a) d2pilot farm --descend-to LEVEL (opt-in) picks the warp by its node's destination level and goes back on a wrong arrival; tests in tools/test_d2pilot_descend.py over kept H6e2 logs; reruns eye4c/tome4c/brain4c recipes (not run). (b) the brain chest is in every DS1 of LvlPrest 704; on seed 4914 (DungRm2B, at 10014, 11879) its room was never activated in the copy holding the listed objects, and the pilot's frontier read the other copy; [items/0010 § The brain chest in level 91](../../findings/items/0010-quest-drops.md#the-brain-chest-in-level-91-lanerdp-2026-10-27-static); review [2026-10-27-reverser-architect-lane-rdp-review-descend-to-and-the-brain](2026-10-27-reverser-architect-lane-rdp-review-descend-to-and-the-brain.md)"
---

From the `lane/h6e2` review (plan 0038 H6e2, 2026-10-27). Two of H6e2's failed routes are a pilot limitation, not a model error, and block the rerun of the eye chest and the Lam Esen tome (the shortfalls `bbb`, `qey`): (a) `tools/d2pilot.py farm --descend ROW` takes the first warp of LvlWarp row ROW on the level, but rows 51 (Spider Forest: the Arachnid Lair 84 or the Spider Cavern 85) and 61 (Kurast Bazaar: the Ruined Temple 94 or the Disused Fane 95) serve two destinations each, so `eye4` reached 84 and `tome4` 95. `h6e2_sessions.py`'s `descend(lid, rows)` already knows the target level; give `descend` a destination filter (the `WRP` line's target level, or the Levels `Vis`/`Warp` slot of that warp) and retry the next warp of the row on a wrong arrival. (b) The brain chest (class 406) was never listed in level 91 on map seed 4914 after a full explore (`brain4b`, frontier 0, `objop --obj-mem`): before another session, read whether the chest is placed on every seed (the preset LvlPrest 704 and its object list) or whether `OBJS` misses it (its listing radius). Both feed the H6e1 or a later quest-items rerun; not blocking any review.

---
from: reverser
to: spec-writer
date: 2026-10-18
status: open
context:
  - ../findings/quests/0001-progression.md#16-phase-2-part-2-run2026-10-18-quests2
  - ../findings/quests/0002-travel.md#13-phase-2-part-2-run2026-10-18-quests2
  - ../findings/quests/experiments.md#run2026-10-18-quests2
resolution: ""
---

For plan 0042 Phase 3 (quests spec), once the architect has reviewed Phase 2 part 2 (run:2026-10-18-quests2):
take quests/0001 § 16 and quests/0002 § 13 as the part 2 raises and corrections. In short: the NPC-talk reward steps
reached (Normal, Hell, classic) are `[C]` per row with their call sites; the reward handlers write whether or not the
join switched the quest off (they test the word's bits, not `+0x09`), which narrows § 3's "inert" rule; the steps clear
of a reward is `0x0065C3E0` (bits 2-11, no ClearState); the saved words after Save and Exit are the loaded record
(LoadBytes flag 1 for all three records) plus every server write, word by word; a reward that creates an item or a
hireling draws the game seed inside (an oracle); NPC 266 steps the player seed twice per talk (two quest objects share
its e0 handler), a correction of § 7/§ 11; NPC 377 has no stock placement; warps draw nothing (`[C]`); the Compelling
Orb's counted half is `[C]`. Not blocking until the review rules.

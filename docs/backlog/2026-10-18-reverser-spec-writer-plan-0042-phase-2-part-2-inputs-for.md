---
from: reverser
to: spec-writer
date: 2026-10-18
status: done
context:
  - ../findings/quests/0001-progression.md#16-phase-2-part-2-run2026-10-18-quests2
  - ../findings/quests/0002-travel.md#13-phase-2-part-2-run2026-10-18-quests2
  - ../findings/quests/experiments.md#run2026-10-18-quests2
resolution: "Done (lane/p42s): part 2 rows taken into the Phase 3 drafts on 2026-10-19; the re-tag from part 3 that this entry waited for is done (2026-10-20, with the part 3 inputs entry)."
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

**Released (architect, `lane/p42q` review, 2026-10-19, accept with fixes; plan 0042 log).** Proceed with Phase 3
(plan 0042 Phase 3 *Start*). The corrections are now also written where they correct (quests/0001 § 1, § 3, § 7 word
29, § 10 word 40, § 11). Take the part 2 rows as scoped in the findings, "for the rows and branches reached". Write `[I]`:
ruling (c)'s statements (mode-0 waypoint activation and its object-seed draw, the stepping type-5 lookup, packet 0x48
and word 28, timers and the quest-seed draws not yet logged, death and resurrection, level-entry and item-use steps)
until Phase 2 part 3's review raises them, then re-tag before the Phase 3 review; ruling (b)'s shortfalls stay `[I]`
for good in this plan. NPC 377: state its player-seed draw `[I]` and that no stock data places the NPC. A classic half
stays `[I]` where the handler tests `game +0x70` and only expansion was run.

*2026-10-19 (spec-writer, `lane/p42s`):* taken into the Phase 3 drafts [quests/progression](../specs/quests/progression.md)
and [quests/travel](../specs/quests/travel.md) as scoped: the part 2 rows `[C]` for the branches reached, ruling (c)'s
statements `[I]`, NPC 377 `[I]` and unreachable, the classic half of word 26's 0x4E20 row `[I]`. Left open for the
re-tag from Phase 2 part 3's reviewed raises before the Phase 3 review.

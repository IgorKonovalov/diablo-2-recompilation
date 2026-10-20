---
from: architect
to: reverser
date: 2026-10-19
status: done
context:
  - ../../plans/done/0042-quests-travel.md
  - ../../findings/quests/experiments.md#run2026-10-18-quests2
resolution: "Done: run:2026-10-19-quests3, reviewed 2026-10-20 (lane/p42r, accept with fixes); consumed by the Phase 3 re-tag, reviewed 2026-10-20; plan 0042 closed."
---

Run plan 0042 Phase 2 part 3, the draw-bearing remainder, as defined in the plan ('Phase 2 part 3', ruled at the part 2 review 2026-10-19); the last reproduction pass of the plan, about four hours of game time, at most two slots: run:YYYY-MM-DD-quests3 with 0 mismatches under the part 2 checker, re-checking the 32 logs of parts 1 and 2, over what it reaches of, in priority order: (1) the quest-seed draws reachable by a waypoint hop or a town talk (word 11's eclipse arm on entering 44/45 at state 0 and its timer, with a logger line for 0x00543E10/0x00543F10; Anya's reward draw; the cairn-stone order if a scroll path reaches it; the Dark Wanderer timer and the Zoo if their triggers are reachable the same way, read first); (2) waypoint activation from mode 0 (read when InitFn 17 creates mode 0, then at least 20 activations one hop from a built save, event 1 and the Sync 0 object-seed draw predicted); (3) Meshif west (the stepping type-5 lookup) and Tyrael's Act IV to V travel (word 28, packet 0x48); (4) level-entry (e3) and item-use (e9) quest steps reachable by a waypoint hop or in town, listed from quests/0001 § 7-§ 10 first; (5) a town portal refused in a town, a death and resurrection from QuestDeath within the budget; (6) unit tests in tools/test_quests.py for part 2's checker rules (talk steps, saved words, NPC 266's handler runs, word 40's map) and part 3's. What is not reached is a named shortfall with the reason and stays [I]; no part 4. Carry each correction into the section it corrects (reverser review-fixes 12). Hash every kept log in a manifest.

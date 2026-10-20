---
from: spec-writer
to: architect
date: 2026-10-20
status: done
context:
  - ../../wiki/quests.md
  - ../../specs/quests/README.md
  - 2026-10-20-architect-spec-writer-quests-travel-wiki-page.md
resolution: "Reviewed 2026-10-20 (architect): accept with fixes (17), applied in the review commit on lane/wiki5; entry in plans/done/0042 log."
---

Review `lane/wiki5`: the new wiki page [quests.md](../../wiki/quests.md) ("Quests and travel"), answering
[the wiki entry](2026-10-20-architect-spec-writer-quests-travel-wiki-page.md) (closed). One page, not two:
the travel half is short enough, and the placement rule ties the two halves together. `based_on` the three reviewed
specs at 2026-10-20 (quests/README, quests/progression, quests/travel). Not blocking.

**Sections** (each `##` links its spec section): the big picture (data flow); the quest record (bit grammar, the load
rule, the unused words, the game record); events and their order (event kinds, the forced/unforced split, the NPC
message); the game creator's history (the switch-off pass, "switched off is not inert", the double join of a new
character); how a script is shaped (credits, fail others, the reward pattern, timers); a few quests bit by bit (words 1
and 41 with progression's worked example 3 as a table, word 4 and the stone-order draw, word 11's eclipse, word 26 and
the Harrogath portal, word 37 Anya, word 32 the Dark Wanderer); the quest seed and the player's seed (the draws table,
progression's worked example 1); the quest gates; where a player lands (the Position rule and the free-cell search);
waypoints; changing act (move first, write second; the Harrogath portal, not Tyrael's menu); town portals (the three
draws, travel's worked example); warps, death and joining; real-time waits; what is not known yet; where to read more.
Nine Mermaid diagrams (one packet-beta, three flowcharts, two sequence diagrams, three state diagrams).

**Links added:** [wiki/README](../../wiki/README.md) row 13, the reviewed-spec list (plan 0042, closed 2026-10-20), and
the plan 0042 line dropped from the open-plans list (it is closed); [saves](../../wiki/saves.md) (the quests, waypoints
and NPCs section and *Where to read more*); [items-other-paths](../../wiki/items-other-paths.md) (the quest-drops intro,
which said quest bits are "not modelled": now "an input here", with the link); [randomness](../../wiki/randomness.md)
(*Where to read more*). Not edited because lane/p38s5 holds them: levels.md, monsters.md, objects.md (suggested links
are in the lane's report).

**Points for the review.** (1) The hedges: every `[I]` step restated is said "read from the code"; the Zoo and NPC 377
draws are "not reachable on stock data"; Tyrael's menu lines are said to come from a client screenshot and to be read,
not confirmed. (2) Names (Akara, Warriv, Meshif, Tyrael, Malah, Anya, Cain) are the specs' labels for NPC classes and
are used as labels. (3) The wiki index's open-plans list is still stale for 0039 and 0043 (both in `plans/done/`) and
names none of 0045–0049; left alone as outside this entry.

**Gate:** green at the commit.

---
from: spec-writer
to: spec-writer
date: 2026-11-16
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../wiki/quests.md
  - ../specs/quests/travel.md
resolution: ""
---

Plan 0066 Phase 3 (`lane/n66qr`) re-tagged quests/README, quests/progression and quests/travel (updated 2026-11-16), so
wiki/quests's `based_on` dates are stale (W4). One row is now wrong: the events table's "level change" (near line 114)
says the event is raised when "the player's room moves to another level"; quests/travel § Outputs now states it `[C]`
for a level change within one act only, none for an act change (341 and 87 logged), and Warriv's act change calls quest
object 6's event-3 slot directly (progression § B). Other spec changes the page may restate: C4's first-join restore per
quest, `ClearSteps` at the rewards of words 1, 20, 25 and 35 only among those logged, the game record's second reader,
the free-cell search at other sizes and steps `[C]` by emulation. Refresh the page from the specs. Not blocking.

---
from: architect
to: architect, reverser
date: 2026-11-03
status: done
context:
  - ../../findings/ai/0012-batch11.md#210-rows-145-and-147-and-the-unreferenced-functions
  - ../../findings/archaeology/0002-unreached-rows.md
  - ../../plans/done/0042-quests-travel.md
resolution: "Owner decision 2026-11-03: a phase of plan 0052, Phase 1c, after batch 12's review."
---

Home for the Uber Tristram and Pandemonium event (levels 133-136), found open by the plan 0052 batch 11 check. ai/0012 section 2.10 leaves what drives Uber Diablo, Uber Baal and Uber Mephisto open: rows 145, 146 and 147 think ret 4, and the Uber spawn helpers 0x005E9DD0, 0x005FD0F0, 0x005F7F10, the counter 0x005DD140 and Baal's class-709 teleport have no static reference from the AI table. The 37 class and 3 state immediates of b11-uber.txt (classes 704, 705, 709; state 184) lie outside the AI ranges, in the event handlers that archaeology/0002 section 'The upper bound' calls the Uber Tristram handlers, which plan 0042 left as owner play (closed, no phase) and plan 0052's batches do not read. No plan owns it. Needed from the architect: decide whether it is a phase of plan 0052 (an event batch after the catalogue) or a plan of its own (event handlers, levels 133-136 spawns, the Uber minion counts, the drivers of the Uber thinks); until then it stays an open question in ai/0012 and ai/0008. Not blocking batch 12.

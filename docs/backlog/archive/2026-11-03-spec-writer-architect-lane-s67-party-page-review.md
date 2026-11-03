---
from: spec-writer
to: architect
date: 2026-11-03
status: done
context:
  - ../../plans/0058-party-and-player-count.md
  - ../../plans/0052-monster-ai.md
  - ../../specs/player/party.md
resolution: "Accepted with fixes (6) at Tier A; player/party promoted to reviewed; rulings in the plan 0058 log. Phase 3 may start once the lane merges."
---

Review request, lane/s67 (plan 0058 Phase 2 and the P1c remainder). Please review (1) player/creation G0, the G6 note, J4 and its notes, the constants rows against player/0002 and rulings (a) to (d) of the lane/r58a review. (2) hirelings' call path and G2: entry item (11) asked for a link; I also raised both to [C] as the code's map because player/0002 section 5 states it, take the weaker form if you rule otherwise. (3) docs/specs/player/party.md: the 14 readers, each with its input and owning section; it is status draft, so research-map row player/party says draft spec until you accept. (4) Q446 to Q453: their source cells cite the draft page's notes for coverage and player/creation's sections for the owning statement. (5) G1's 'exp <= 0: return 1' raised to [C] as the map by the wrap-total cases of player/0002 section 6. (6) monsters/special section J's six rows' first calls, items/quest-drops D7, drlg/preset's filters, each ending at its first callee with no reach. Left alone and noted: drlg/maze's own flat '133-136 are unreachable', and the open entry ai-0016-classes-706-708-creator-result, new from main while this lane ran. New entry for the reverser: ai/0012's word b+0x0C called the player count.

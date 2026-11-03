---
from: reverser
to: architect
date: 2026-11-03
status: done
context:
  - ../../plans/0055-server-frame.md
  - ../../findings/frame/0005-dispatchers.md
resolution: "Tier B check 2026-11-03: accept with fixes (3: overclaim 2, omission 1). P2a-ii closed as the static step; Phase 2a stays met in part and closes at Phase 2b's first window that places the 65 hooks; merged into main."
---

Review request, Tier per your ruling: plan 0055 Phase 2a-ii, lane/r55f. Frame/0005, run:2026-11-03-frame-order-2. Of the 74 open hooks 9 close and 65 stay open at every rank; 0 mismatches over 383 349 frames with two or more closed sets, 17 254 separating pairs; Phase 2a's Done-when is not met as written, 118 340 frames remaining. Rulings asked: whether this closes P2a-ii with the remainder moved to Phase 2b; the rule that a hook left open takes every rank; rank 21 for everything outside GameTick, and CreateClassSelect as a judgement root; the stack-block match, read by name only. Totals taken after merging main c34cb3cb.

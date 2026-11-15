---
from: architect
to: reverser, spec-writer
date: 2026-11-04
status: done
context:
  - ../../plans/done/0054-path-search.md
  - ../../findings/path/0007-community-cross-check.md
  - ../../specs/skills/missiles.md
resolution: "2026-11-15, lane/n65h review (plan 0065 Phase 1, Tier A): run:2026-11-15-sweep8-p12, not separated (11 546 Nova MMC, all on the path's cached word, 0 fresh bit-0-only words). Accepted under the owner's ruling of 2026-11-15, option (a): no zero-velocity session. D3 stays [I] and P12 stays in skills/missiles Open questions with the cause named (path/0007); the spec's text is plan 0065 Phase 3."
---

From the lane/r1b review (plan 0054 Phase 1b, Tier A), path/0007 row P12, contradicted. src:pk-walkable-flags-overview (2006, no patch, its author says the list is not final) gives floor flag 01 'allow missiles pass' yes. skills/missiles D3 [I] frees a do-function-1 missile with a CollideType at its own cell on bit 0 or 2 (c & 5 at fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0), with PathCellCollision's cached 0x7FFF test, and bit 0 is the sub-tile's flag 01 (COLL_StampTile ORs the byte unmasked). Both cannot hold for a cell with bit 0 and not bit 2. Reverser, harness: a stock missile of pSrvDoFunc 1 and CollideType 3 crossing a logged bit-0-only cell, with the do function's return, and a control on a free cell; or a second code path that shows why no such cell is reached. No game edit. Spec-writer: until settled, skills/missiles Open questions carries it, D3 stays [I]. Not part of plan 0054's spec: it does not block it. Tier A (verdict lane). Source weak; settle by the run either way.

2026-11-15 reverser (`lane/n65h`, plan 0065 Phase 1): P12 ran (run:2026-11-15-sweep8-p12): not separated, under the owner's ruling (a): a Nova cannot give the fresh bit-0-only word (cached word at path +0x7C non-zero); no zero-velocity session. Plan 0065 log, Phase 1 entry. For the architect to close.

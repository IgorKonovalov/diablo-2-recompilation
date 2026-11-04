---
from: architect
to: reverser, spec-writer
date: 2026-11-04
status: open
context:
  - ../plans/0054-path-search.md
  - ../findings/path/0007-community-cross-check.md
  - ../specs/skills/missiles.md
resolution: ""
---

From the lane/r1b review (plan 0054 Phase 1b, Tier A), path/0007 row P12, contradicted. src:pk-walkable-flags-overview (2006, no patch, its author says the list is not final) gives floor flag 01 'allow missiles pass' yes. skills/missiles D3 [I] frees a do-function-1 missile with a CollideType at its own cell on bit 0 or 2 (c & 5 at fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0), with PathCellCollision's cached 0x7FFF test, and bit 0 is the sub-tile's flag 01 (COLL_StampTile ORs the byte unmasked). Both cannot hold for a cell with bit 0 and not bit 2. Reverser, harness: a stock missile of pSrvDoFunc 1 and CollideType 3 crossing a logged bit-0-only cell, with the do function's return, and a control on a free cell; or a second code path that shows why no such cell is reached. No game edit. Spec-writer: until settled, skills/missiles Open questions carries it, D3 stays [I]. Not part of plan 0054's spec: it does not block it. Tier A (verdict lane). Source weak; settle by the run either way.

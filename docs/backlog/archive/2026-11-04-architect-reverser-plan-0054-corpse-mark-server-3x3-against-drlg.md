---
from: architect
to: reverser
date: 2026-11-04
status: done
context:
  - ../../findings/path/0004-per-event-reproduction.md
  - ../../findings/drlg/0005-collision.md
  - ../../specs/drlg/collision.md
  - ../../plans/done/0054-path-search.md
resolution: "Static part answered, [I]: the plus is the client's copy (0x004B05E3, 0x004B0A05, where run:2026-10-14-collision's dumps sit), the server's call is UnitCorpseColl(unit, 1) at 0x005A65D9, a 3x3 with mask and pattern unchanged; seven callers tabled in [path/0005](../../findings/path/0005-grid-rules.md). drlg/0005 §§ 5, 6 annotated; spec row routed: [entry](2026-11-04-reverser-spec-writer-drlg-collision-server-corpse-3x3-object-hascollisi.md). The run part (per-call lines, hold-out) moves to plan 0054 Phase 2's next kept batch, its step 4."
---

From the lane/p54 review (plan 0054 Phase 2). A disagreement with a reviewed row, ADR-0024. docs/specs/drlg/collision.md § marks gives a dead MonStats2 deadCol 0 monster 'pattern 5 (plus), 0x8000', [C] by run:2026-10-14-collision (dumps at the deadCol tests 0x004B05DB and 0x004B09FB, in the handler 0x004AFF60), and its 'corpse call with argument != 0' row is [I]. The server's live cells in run:2026-11-04-path say otherwise: of the 992 distinct mode-12 monsters of the kept unit lists, 991 hold a full 3x3 of 0x8000 with the unit's mask still 0x100 and pattern 0, 1, 2 or 3, never 5; the one other is class 273 gargoyletrap (deadCol 1), which keeps 0x100; development logs 304 of 304 (workspace/logs/path/review-p54/review.txt § 13). Candidate: UnitCorpseColl(unit, 1) at 0x005A65D9, whose test at 0x005A65CD is not read, reaches the 3x3 at 0x00649FD8 and leaves mask and pattern alone. Do not assume either side wrong. Please: (1) static: read 0x005A65D9's function and the seven callers of 0x00649F70 (0x00461018, 0x004B05E3, 0x004B0A05, 0x004C8963, 0x0057F367, 0x005A65D9, 0x005CAF8E), which copy (client or server) each serves and in what order at a death; whether the 396 deaths of run:2026-10-14-collision were on the client's units; (2) run: in plan 0054 Phase 2's next kept batch, a break at each call printing unit, side, argument, class and the 5x5 cells after it, deadCol 0 and 1 classes both, read-only; the corpse rule as path.py has it now is frozen, so that batch is its hold-out; (3) write drlg/0005 §§ 5, 6 and the Phase 2 conclusion with the copy each statement holds for, and file the spec-writer entry for drlg/collision's rows and the state diagram. The planners are not affected on these logs: the corpse reading changes none of the 361 plans the tie's grid gets wrong.

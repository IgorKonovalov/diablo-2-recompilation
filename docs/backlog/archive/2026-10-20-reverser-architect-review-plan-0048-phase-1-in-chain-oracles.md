---
from: reverser
to: architect
date: 2026-10-20
status: done
context:
  - ../../plans/done/0048-seed-to-world.md#implementation-log
  - ../../findings/chain/0002-retirements.md
  - ../../findings/chain/0001-oracles.md
resolution: "Reviewed 2026-10-20 (architect): accept with fixes (5). Phase 1 done; Phase 2 may start in one slot. Rulings in the plan 0048 log."
---

Review plan 0048 Phase 1 (`lane/p48r`, static, Ghidra copy `ghidra-p48r`, no harness): [chain/0002](../../findings/chain/0002-retirements.md),
`tools/chain.py` (`gen`, `check`, `barrier`), `tools/gdb/chain.gdb`, the model changes in `tools/affixes.py`,
`tools/items_chain.py`, `tools/monspawn.py`, `tools/monstats.py`, `tools/objects.py`, `tools/test_chain.py`, the sections
added to items/0005, monsters/0002, 0003, 0004, objects/0001 and drlg/0002, 8 new symbols, and the plan log entry.
Blocking Phase 2.

Asked of the review in particular:
- **Retired** (chain/0002 Answer): 2, 14, 16, 17 (InitFn 46), 21, 22, 6 and 7 (7 in its seeds and marks; its drop spot
  is a model for 69 of 71, the 2 others taken from the log and counted). Is the "equality chain" acceptable as
  retirement where two checkers share a window (tools/objects.py takes a seed at `OPUX`/`MTX`/`OCX` that
  tools/monspawn.py or tools/tc.py predicts and asserts at the same line), rather than one model carrying the value?
- **Not retired, named with the reason**: 19 (the gate's code read and the logged inputs checked against it on 1 265
  gates, but the room flags `0x30000`/`0x800000`/`0x80` and `LevelRoomCount` still logged: they need `tools/drlg.py`'s
  per-room predictions mapped to the active rooms); 20 (R3 already shows the composed grid equals the snapshot in
  3 871 of 3 998 pass rooms, the residue being unit bits plus 14 cells of object bits; the barrier grid read and probed
  at 258 of 307 grids; the type-11 point's rule known, not carried). Should 19 and 20 move to a follow-up phase before
  Phase 2, or stay Phase 2 inputs?
- **13**: modelled `[I]`, unreached (classes 234 and 267 never created on the kept logs). On the way the reading of
  `tools/monstats.py`'s `oninit` byte was wrong (`+0x02` of a row the `.bin` does not hold), so the old oracle never
  fired; corrected (`+0x04`, `cmp byte [ebx+4], 0` at 0x005D6BA5).
- **Corrections to chain/0001 § 2**: row 17's "47–69 not reached" is wrong for InitFns 54 (7 calls) and 62 (4); row 22's
  creation is a preset unit's (the window's), `[I]` as stated in chain/0002 § 6.
- **chain.gdb** is the composition's loggers in one file; it is not reduced to entry and exit lines, because every
  checker consumes the lines inside each boundary. Phase 2 should rule on its volume before the first session.

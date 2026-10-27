---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../../findings/items/experiments.md#run2026-10-27-sweep-cube
  - ../../findings/items/0008-cube.md#plan-0038-batch-h6a-run2026-10-27-sweep-cube
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (7). Moves cube 16, 44 to d-none stand (re-counted from the tables); cube 39 L491 and L524, 40 L528 and 58 raised in part; per-child copy steps [I] beyond one child; InvPlaceItem bit 0 [C]; the runeword copy's serialiser path cited. Ledger raised 18, in part 8, reclassified 2, shortfall 1: 29. Totals against main ad8b8cd0: static 567, harness 513, blocked 427 (d-none 300), deferred 2, raised 17: 1 526. items/cube ready for Phase 3; the spec-writer entry released. Plan 0038 log, lane/h6a review."
---

Review plan 0038 batch H6a (`cube`; items/cube rows 1, 7, 15–17, 25, 32, 36, 38–40, 43, 44, 51, 53, 54, 58 and the S2c pieces of cube 49 and aff 14; `lane/h6a`), run:2026-10-27-sweep-cube. 8 sessions on slot 1, all kept (expansion and classic, Normal, in town; one Act IV start, one clvl-1 crafting game in its own game directory for the expected fault), logger `tools/gdb/cube.gdb` with `tools/gdb/cube.py` r4, checker `tools/sweep_h6a.py check`: 26 transmutes reproduced by `tools/cube.py`, 27 call chains, 23 `UnitSetEvent` calls, 0 mismatches (`workspace/logs/h6a/check-final.txt` `15e54b63…`; three manifests pass `sha256sum -c` from `workspace/logs/h6a/`). `tools/cube.py` was extended (uns, rep broken/stackable, qty=, the copy children's seed steps, placement bit 0); it still reproduces run:2026-10-15-cube's 182 transmutes, and `sweep_s2c.py cube` is byte-identical. Ledger: raised 22, raised in part 4, reclassified 2 (cube 16, 44 → d-none), shortfall 1 (cube 51): 29; totals against `main` `fd841611`: static 567, harness 517, blocked 423 (d-none 297), deferred 2, raised 17: 1 526. Points to look at: the two d-none moves (no stock `eth` input, no stock `rem` output, `tables.txt`); the crash case (b) of cube 49 (CNULL plus the game's Crash.txt at 0x005C2460) and case (a) d-none (0 of 40 194); the built states (dur, broken, charges via `item_props`, quantity, ethereal unique, socketed unique, quest bits, act byte 131) and what each backs; the ethereal open question answered (cube 38); the refinements (2 game-seed steps per child copied, the runeword copy's prefix 0, InvPlaceItem's bit 0 `[I]`); the 10 symbol raises and 1 new row. Not blocking.

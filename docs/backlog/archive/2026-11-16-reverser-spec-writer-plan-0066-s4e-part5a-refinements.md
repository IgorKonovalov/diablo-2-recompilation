---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../findings/items/0013-grids-belts-stacks.md
  - ../../findings/items/0014-ground-items.md
resolution: "Applied in plan 0066 Phase 3, the stats/items cluster (lane/n66si): items 1–7 in items/inventory and items/use [log](../../plans/done/0066-simulation-inferred-claims-sweep.md)"
---

Plan 0066 batch S4e part 5a (`lane/n66z`, run:2026-11-16-sweep2-s4e-emu part 5a) ran the placement search on full
pages and in sequence, `InvGridFree`, `BeltHoldsSameGroup`, `ItemAutoBeltTest`, `BeltPutItem`, `ItemGroundExpiry`
with quality 9 and `ItemPlaceOnGround` with its flag under emulation. Claims in
[items/0013 § 14](../../findings/items/0013-grids-belts-stacks.md#14-plan-0066-batch-s4e-part-5a-the-search-on-full-pages-and-in-sequence-invgridfree-the-belt-tests-beltputitem-the-ground-expirys-quality-9-and-the-quest-call-run2026-11-16-sweep2-s4e-emu);
rows in the 0066 inventory (items/inventory 22, 23, 47, 48, 55, 63, 81, 84, 87, 98). For Phase 3, not blocking.
Re-tags and refinements to carry into items/inventory (no contradiction):

1. **§ B2.** "A player's search fails only where no spot fits" can be `[C]` (ADR-0015): 779 player cases with a fit
   all return 1, 968 without one all return 0.
2. **§ B5.** "`InvGridFree` tests no bound itself" can be `[C]` (ADR-0015): it tests cell `row × gridX + column` for
   every cell of the rectangle, signed, so a rectangle past the right edge reads the next row's cells (288 of 879
   outside rectangles returned 1). Its convention: EAX the page, ECX the row, DL the width, then column and height.
3. **Worked example, the placement search.** The two sequences are emulated (`seq`), so the paragraph's `[I]` can be
   `[C]` (ADR-0015) with run:2026-11-16-sweep2-s4e-emu.
4. **§ F3.** `[C]` (ADR-0015) for an item the test accepts; add that a null item, a non-item or a row past the Items
   table ends at the error routine (0x00408090), not at 1. `BeltHoldsSameGroup` returns 0 for `isc`/`tsc`, a bad
   signature, a non-item, or a belt page made at another size than 16 × 1, else 1 when one of boxes 0..3 holds the same
   class or potion list. The F3 note "the pickup's belt branch always calls `BeltPlace`" can be `[C]` with the pins.
5. **§ F4.** `BeltPutItem` `[C]` (ADR-0021) to `InvItemRemove`: the box test is unsigned (`> 15` refuses, so −1 does
   too), and a belt page made at another size than 16 × 1 refuses; `numboxes` is not tested.
6. **§ K1.** `+0xC4` ends `| 0x2001003`: bit 0 is set by `UNIT_SetMode` (0x006246B3, 0x006246E3), called with mode 3,
   besides the function's own `0x1002` and `0x2000000`. The flag is EDX, any non-zero value; the quest call is `[C]`
   (ADR-0021) to its entry, after every write, and is followed only by the pops and `ret 0x10`.
7. **§ K2.** Quality 9's `+45000` is `[C]` (ADR-0015); "no stock path makes one" stays `[I]`.

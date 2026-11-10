---
from: reverser
to: spec-writer
date: 2026-11-10
status: done
context:
  - ../../plans/done/0064-clean-room-test.md#implementation-log
  - ../../findings/data/0001-excel-loader.md
  - ../../findings/items/0001-tc-resolution.md
  - ../../specs/data/excel.md
  - ../../specs/items/tc.md
resolution: "data/excel G4 and items/tc § A give the unique/set entry words [I]; items/tc § K gives the load-time Equiv matrix and its walk, the open question struck ([items/tc](../../specs/items/tc.md#k-the-item-type-test--items_istype-and-items_unitistype))."
---

**Spec follow-ups, data/excel G4 and items/tc § A and § K (plan 0064, from the reverser's closed entries parseitemcell-unique-entry-words and itemtypes-equiv-walk-form).** (1) **data/excel G4 and items/tc § A**: for a TreasureClassEx cell that names a unique (flags 0x11) or a set item (0x12), `index` (+0x08, u16) is the items record of the row's base code (0 when the code is no item code) and `aux` (+0x0A, u16) is the name-link hit itself, the uniqueitems or setitems row, with no offset (hits from 1 for uniques, from 0 for sets); `mul=`/`ma=`/`mg=` write the same +0x0A. Source: data/0001 § Plan 0064 (`[I]`, ADR-0010: only the edited forced run reaches it). (2) **items/tc § K (K1 and its open question)**: the type test reads a precomputed n×n bit matrix built once by ITEMS_LoadItemTypes with a depth-first walk (Equiv1 ≤ 0 skips Equiv2, depth bound 124, no visited set); bit 0 is set in every row, so IsType(x, 0) is true for every item; type2 is tested only when non-zero (IsType) or positive (UnitIsType). On the stock table the matrix equals the plain transitive closure plus bit 0 (no cycle, no blank Equiv1 with a set Equiv2, longest chain 4). Source: items/0001 § Plan 0064.

**2026-11-10, spec-writer (`lane/n64y`, plan 0064 Phase 4 part 3): done.** (1) [data/excel G4](../../specs/data/excel.md#g-treasure-classes): the unique and set steps now write `e.index` = the items record of the row's base code (0 on a miss, return untested) and `e.aux` = the hit `i` itself, with the null-link cases and the later `mul=`/`ma=`/`mg=` overwrite, plus a step note; [items/tc § A](../../specs/items/tc.md#a-the-runtime-tc-what-the-resolver-reads): the entry layout's glosses and a step note, `aux + 1` tied to H4. Both `[I]` (ADR-0010, the forced run agrees without raising). What the implementer could not know: whether `aux` is the row or the row − 1, and what `index` holds for a named entry. (2) [items/tc § K](../../specs/items/tc.md#k-the-item-type-test--items_istype-and-items_unitistype): K1 is now the load-time matrix and `TypeIsOf`'s walk (`[I]`), with step notes on bit 0 in every row, the cycle cases, the stock table's shape (`[C]`) and the closure-plus-bit-0 equivalence on stock data (`[I]`); K2/K3 give the guards and the `type2` tests; the *Open questions* `[L]` on the walk's form is struck as answered. What the implementer could not know: that the test is a precomputed matrix, that bit 0 is set for every item, and that `Equiv1` ≤ 0 skips `Equiv2`. Source: [data/0001 § Plan 0064](../../findings/data/0001-excel-loader.md#plan-0064-2026-11-10-the-entry-words-of-a-unique-or-set-cell), [items/0001 § Plan 0064](../../findings/items/0001-tc-resolution.md#plan-0064-2026-11-10-the-item-type-test-and-its-equiv-matrix).

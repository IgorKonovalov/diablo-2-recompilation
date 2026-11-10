---
from: reverser
to: spec-writer
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md#implementation-log
  - ../findings/data/0001-excel-loader.md
  - ../findings/items/0001-tc-resolution.md
  - ../specs/data/excel.md
  - ../specs/items/tc.md
resolution: ""
---

**Spec follow-ups, data/excel G4 and items/tc § A and § K (plan 0064, from the reverser's closed entries parseitemcell-unique-entry-words and itemtypes-equiv-walk-form).** (1) **data/excel G4 and items/tc § A**: for a TreasureClassEx cell that names a unique (flags 0x11) or a set item (0x12), `index` (+0x08, u16) is the items record of the row's base code (0 when the code is no item code) and `aux` (+0x0A, u16) is the name-link hit itself, the uniqueitems or setitems row, with no offset (hits from 1 for uniques, from 0 for sets); `mul=`/`ma=`/`mg=` write the same +0x0A. Source: data/0001 § Plan 0064 (`[I]`, ADR-0010: only the edited forced run reaches it). (2) **items/tc § K (K1 and its open question)**: the type test reads a precomputed n×n bit matrix built once by ITEMS_LoadItemTypes with a depth-first walk (Equiv1 ≤ 0 skips Equiv2, depth bound 124, no visited set); bit 0 is set in every row, so IsType(x, 0) is true for every item; type2 is tested only when non-zero (IsType) or positive (UnitIsType). On the stock table the matrix equals the plain transitive closure plus bit 0 (no cycle, no blank Equiv1 with a set Equiv2, longest chain 4). Source: items/0001 § Plan 0064.

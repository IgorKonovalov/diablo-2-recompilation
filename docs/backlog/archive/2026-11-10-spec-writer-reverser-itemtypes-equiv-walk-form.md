---
from: spec-writer
to: reverser
date: 2026-11-10
status: done
context:
  - ../../specs/items/tc.md#k-the-item-type-test--items_istype-and-items_unitistype
  - ../../tables/ItemTypes.md#open-questions
resolution: "Done 2026-11-10 (lane/n64r): the matrix (+0xC00 stride, +0xC04 bits) is built once by ITEMS_LoadItemTypes (0x00638D80) through sub_00638CD0_ItemTypeIsOf: depth-first, LIFO, Equiv1 <= 0 skips Equiv2, depth bound 124, no visited set (a one-parent cycle hangs; d-edit). Bit 0 is set in every row (t <= 0 returns 1 first), so record 0 is in every type's set, not only blank-parent ones. Stock table: no cycle, longest chain 4, matrix = closure plus bit 0 (tools/itypes_equiv.py). [items/0001 § Plan 0064](../../findings/items/0001-tc-resolution.md#plan-0064-2026-11-10-the-item-type-test-and-its-equiv-matrix); spec follow-up in [plan-0064-item-cell-words-and-equiv-matrix](2026-11-10-reverser-spec-writer-plan-0064-item-cell-words-and-equiv-matrix.md)."
---

Plan 0064 Phase 4 (items/tc § K, the item-type test). The specs now define `ITEMS_IsType` (0x00629A90) and `ITEMS_UnitIsType` (0x00629BB0) as the `Equiv1`/`Equiv2` closure of the item's `type` and `type2` (items/0001 symbol table `[I]`, items/0005 tests (c)–(d) `[C]`). No finding says how the code builds or walks that closure: items/0001 calls it 'the equivalence bitmap', and tables/ItemTypes keeps 'how Equiv1/2 chains are walked (depth, cycles)' `[L]`. Ask (static only): where the bitmap is built (at load, from which loop), how deep the walk goes and what it does on a cycle, and whether record 0 (`None`, the target of every blank `Equiv` cell, data/0004) is put into each blank-parent type's set. Not blocking: stock data has no test for type 0, and the S2 clean-room implementer's transitive closure reproduced the auto TCs. Close with the finding section; spec-writer then raises items/tc K1 and strikes its open question.

*Annotated 2026-11-10 (architect, plan 0064 Phase 4 review), leads from an r2 listing only:* neither function walks at
call time. `ITEMS_IsType` tests one bit of a precomputed matrix, row = the item's type (from 0x00628700), dword stride
`[itemtypes + 0xC00]`, base `[itemtypes + 0xC04]`, bit `t` (mask table 0x006CE268), so depth and cycles are decided
wherever that matrix is built (the item-tables loader, which items/0005's data list names `+0xC00`/`+0xC04`). Then
`type2` (`movsx word [rec + 0x120]`, 0x00629B1C) is tested the same way **only when it is non-zero** (`test eax, eax; je`,
0x00629B23), so a blank `type2` (record 0) adds nothing; and `t` < 0 or ≥ the itemtypes count returns 0 first
(0x00629A99, 0x00629AAA). `ITEMS_UnitIsType` (0x00629BB0) repeats the same matrix test inline. The ask narrows to the
builder of the matrix and whether its row for a blank-`Equiv` type holds bit 0.

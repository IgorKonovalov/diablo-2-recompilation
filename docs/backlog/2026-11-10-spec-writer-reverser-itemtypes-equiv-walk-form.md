---
from: spec-writer
to: reverser
date: 2026-11-10
status: open
context:
  - ../specs/items/tc.md#k-the-item-type-test--items_istype-and-items_unitistype
  - ../tables/ItemTypes.md#open-questions
resolution: ""
---

Plan 0064 Phase 4 (items/tc § K, the item-type test). The specs now define `ITEMS_IsType` (0x00629A90) and `ITEMS_UnitIsType` (0x00629BB0) as the `Equiv1`/`Equiv2` closure of the item's `type` and `type2` (items/0001 symbol table `[I]`, items/0005 tests (c)–(d) `[C]`). No finding says how the code builds or walks that closure: items/0001 calls it 'the equivalence bitmap', and tables/ItemTypes keeps 'how Equiv1/2 chains are walked (depth, cycles)' `[L]`. Ask (static only): where the bitmap is built (at load, from which loop), how deep the walk goes and what it does on a cycle, and whether record 0 (`None`, the target of every blank `Equiv` cell, data/0004) is put into each blank-parent type's set. Not blocking: stock data has no test for type 0, and the S2 clean-room implementer's transitive closure reproduced the auto TCs. Close with the finding section; spec-writer then raises items/tc K1 and strikes its open question.

---
from: architect
to: spec-writer
date: 2026-11-10
status: done
context:
  - ../../plans/done/0064-clean-room-test.md#implementation-log
  - ../../plans/0064-cleanroom/S2.md
  - ../../specs/items/tc.md#i-auto-item-type-tcs-weapn-armon-bown-melen-abown
resolution: "Done 2026-11-10 (lane n64w, plan 0064 P4): new [items/tc § K](../../specs/items/tc.md#k-the-item-type-test--items_istype-and-items_unitistype), the item-type test: K1 the Equiv1/Equiv2 closure, K2 ITEMS_IsType 0x00629A90 (type then type2 through the equivalences, [I], items/0001 symbol table, archaeology/0002 § 5), K3 ITEMS_UnitIsType 0x00629BB0 ([C], items/0005 tests (c)-(d), the GOLD_TYPE run), a blank Equiv stores record 0 ([C], data/0004) and no test here asks for type 0 ([I]); I1 and H8 now call IsType/UnitIsType and link § K, and an I1 note says the weight alone reads the own type. What the implementer could not know: the definition sat only in items/affixes C5c-C5d. The walk's form (depth, cycles, record 0) is a new open question, [reverser entry](2026-11-10-spec-writer-reverser-itemtypes-equiv-walk-form.md); no stock test depends on it."
---

**Spec defect, items/tc (plan 0064 P3 triage, S2 row 11).** items/tc uses the item-type test in I1 ("i is of type t", "not of type 38") and H8 ("through the type-equivalence test"), and items/quality S2 sends its reader here for `IsType` ("the type-equivalence test of items/tc"), but items/tc never defines it. The S2 implementer found the definition only in items/affixes' C5c–C5d note (`ITEMS_UnitIsType`: the `Equiv1`/`Equiv2` closure of the base's `type` and `type2`), a spec outside the slice's list. Ask: define the test once in items/tc (a short subsection or a *Reimplementation notes* bullet: the record test `ITEMS_IsType` 0x00629A90 and the unit test `ITEMS_UnitIsType` 0x00629BB0, `type` then `type2`, the transitive Equiv walk, a blank Equiv as no parent), and point I1 and H8 at it. The answer is already in findings: items/0001 symbol table (`ITEMS_IsType`, "type, then type2, through the equivalence bitmap"), archaeology/0002 line 119 ("of type t read through Equiv1/Equiv2 for both type and type2; type2 changes no count"), and items/affixes' C5c–C5d sources for the unit test. Keep the tags they carry (`[I]` for the record test). Phase 4 of plan 0064.

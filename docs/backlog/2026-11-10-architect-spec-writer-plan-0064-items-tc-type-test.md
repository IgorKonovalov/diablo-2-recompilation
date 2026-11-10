---
from: architect
to: spec-writer
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md#implementation-log
  - ../plans/0064-cleanroom/S2.md
  - ../specs/items/tc.md#i-auto-item-type-tcs-weapn-armon-bown-melen-abown
resolution: ""
---

**Spec defect, items/tc (plan 0064 P3 triage, S2 row 11).** items/tc uses the item-type test in I1 ("i is of type t", "not of type 38") and H8 ("through the type-equivalence test"), and items/quality S2 sends its reader here for `IsType` ("the type-equivalence test of items/tc"), but items/tc never defines it. The S2 implementer found the definition only in items/affixes' C5c–C5d note (`ITEMS_UnitIsType`: the `Equiv1`/`Equiv2` closure of the base's `type` and `type2`), a spec outside the slice's list. Ask: define the test once in items/tc (a short subsection or a *Reimplementation notes* bullet: the record test `ITEMS_IsType` 0x00629A90 and the unit test `ITEMS_UnitIsType` 0x00629BB0, `type` then `type2`, the transitive Equiv walk, a blank Equiv as no parent), and point I1 and H8 at it. The answer is already in findings: items/0001 symbol table (`ITEMS_IsType`, "type, then type2, through the equivalence bitmap"), archaeology/0002 line 119 ("of type t read through Equiv1/Equiv2 for both type and type2; type2 changes no count"), and items/affixes' C5c–C5d sources for the unit test. Keep the tags they carry (`[I]` for the record test). Phase 4 of plan 0064.

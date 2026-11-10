---
from: architect
to: spec-writer
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md#implementation-log
  - ../plans/0064-cleanroom/S2.md
  - ../specs/data/excel.md#g-treasure-classes
resolution: ""
---

**Spec defect, data/excel (plan 0064 P3 triage, S2 row 11).** G2 `BuildAutoTCs` reads "item is of type t" and "item is not of itemtypes record 38" with no definition or link; the definition the S2 implementer needed is in items/affixes' C5c–C5d note, outside the slice. Link both phrases to the definition items/tc will carry (separate entry) and name the function (`ITEMS_IsType` 0x00629A90, as data/0001 line 319 does). Evidence: data/0001 line 319, archaeology/0002 line 119. The G4 unique/set entry words (S2 row 14) wait for the reverser entry plan-0064-parseitemcell-unique-entry-words; take them up here when it closes. Phase 4 of plan 0064.

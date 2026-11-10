---
from: architect
to: spec-writer
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md
  - ../plans/0064-cleanroom/S2.md
resolution: ""
---

Plan 0064 S2 row 12, disputed, settled by a fresh clean-room reader (2026-11-10): it needed two guesses, so the row is a spec defect. items/quality § B step S1 says 'cls ← 1 if ItemTypes[rec.type].Class < 7 else 0 ; signed type, bounds-checked, else 0'. No sentence says whether the Class compare is unsigned (0xFF blank → false) or signed (-1 → true unless the bounds check returns first), and none says the Class byte is the playerclass row index (ama = 0). State both, with the finding's anchor (fn:ITEMS_IsClassSpecific@0x00629F70).

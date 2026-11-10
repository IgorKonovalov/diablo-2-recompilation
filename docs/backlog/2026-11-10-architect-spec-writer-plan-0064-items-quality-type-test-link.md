---
from: architect
to: spec-writer
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md#implementation-log
  - ../plans/0064-cleanroom/S2.md
  - ../specs/items/quality.md
resolution: ""
---

**Spec defect, items/quality (plan 0064 P3 triage, S2 row 11).** S2's step note says `IsType` is "the type-equivalence test of items/tc", and items/tc does not define it (separate entry for items/tc). Once items/tc defines the test, link S2's note to that anchor, and state in one clause that `IsType(item, weap)` walks the Equiv closure of both `type` and `type2` (contrast A2–A5, which read the own `type` only, and S1, which reads the own type's `Class`). Evidence: fn:ITEMS_IsType@0x00629A90 as cited, items/0001 symbol table, archaeology/0002 line 119. Phase 4 of plan 0064.

---
from: architect
to: archivist
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md
  - ../tables/ItemTypes.md
resolution: ""
---

Plan 0064 S2 row 12 probe (2026-11-10): docs/tables/ItemTypes.md contradicts itself for a blank Class cell. The record layout says 'blank → 0xFF', while the Row identity rule says 'A blank reference cell … finds row 0 (None), so it stores 0' (0 is ama's index for Class). Scope the row-identity rule so that it excludes Class, or state the exception there, and check the .bin values for the blank rows.

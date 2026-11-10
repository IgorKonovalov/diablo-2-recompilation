---
from: architect
to: archivist
date: 2026-11-10
status: done
context:
  - ../../plans/0064-clean-room-test.md
  - ../../tables/ItemTypes.md
resolution: "Checked itemtypes.bin byte by byte: a blank Class cell stores 0xFF (85 of 85), as do blank StaffMods (94) and StorePage (28); blank Equiv1/2, Shoots, Quiver, BodyLoc1/2 store 0. [ItemTypes](../../tables/ItemTypes.md) Row identity now states the exception."
---

Plan 0064 S2 row 12 probe (2026-11-10): docs/tables/ItemTypes.md contradicts itself for a blank Class cell. The record layout says 'blank → 0xFF', while the Row identity rule says 'A blank reference cell … finds row 0 (None), so it stores 0' (0 is ama's index for Class). Scope the row-identity rule so that it excludes Class, or state the exception there, and check the .bin values for the blank rows.

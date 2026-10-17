---
from: architect
to: reverser
date: 2026-10-17
status: open
context:
  - ../plans/done/0040-drlg-room-lifecycle.md#implementation-log
  - ../specs/drlg/lifecycle.md#open-questions
resolution: ""
---

[2026-10-17] from architect → reverser: plan 0040 close follow-ups (not blocking). (1) Symbol tags: drlg/lifecycle now leans on sub_0052D240_RoomsDeactivate, sub_005424F0_InactiveMonstersRestore, sub_00542B40_RoomInactiveUnitsRestore, sub_0054F060_RoomWandererTick, sub_0061B490_DrlgRefAdd and sub_0061B4F0_DrlgStatusRecompute as entry points or model steps checked by run:2026-10-17-lifecycle (drlg/0009 § 2 and § 11), all still I in re/symbols.csv; raise those the run and the reading support. (2) The 0x400 restore path: h-highlands saved three monster records of class 522 with record flags 0x540 (0x400, alignment 2, 0x40) at frames 9636, 9828 and 13008, none restored; a session that re-enters such a room would reach the 0x400 drop (lifecycle H2, an Open questions item). The P2 follow-ups (town reachability, champion paths, the flag-1 call in SpecialMonRestore) stay in their own entry.

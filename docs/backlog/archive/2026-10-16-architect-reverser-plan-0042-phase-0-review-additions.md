---
from: architect
to: reverser
date: 2026-10-16
status: done
context:
  - ../../tables/Objects.md#waypoints-and-portals-plan-0042-phase-0
  - ../../plans/0042-quests-travel.md#implementation-log
resolution: "Answered by plan 0042 Phase 1 (lane/p42r, reviewed 2026-10-17): OperateFn 34 named (OBJOP_ArcanePortal); 0x005BCFD0 read (re-opens the Act III bridge, moves nobody), 410 never placed, DurancePortalOperate keeps its name; the Meshif and Durance removal branches read both ways (P2 question 9 runs the counter cases)."
---

[2026-10-16] from architect → reverser: plan 0042 Phase 0 review, additions to the archivist's Phase 1 request above (not blocking). (a) Add `OperateFn` 34 (`0x005846B0`, the Arcane Sanctuary portal 298) to the handlers to name. (b) `sub_00584750_DurancePortalOperate` does not read the class or `Parm0`: it passes the operated unit's level to `sub_00546AC0_DuranceActTravel`, which travels to Act IV only on level 102 and otherwise calls `0x005BCFD0` (unread). Read `0x005BCFD0`, say whether 410 `Siege Control` (record index 410, `.txt` `Id` 408) is placed and operable, and rename the pair in `re/symbols.csv` if the handler serves more than the Durance portal (your call; the name stays until then). (c) The removal branches the `travel-act3`/`act4` saves feed (Meshif `msf`/`vip` at word 10, Durance `qey qhr qbr qf1 qf2` at word 18): give the gate both ways, so Phase 2 can run the counter case (word set, items held) from the same recipe. Context: [Objects § Waypoints and portals](../../tables/Objects.md#waypoints-and-portals-plan-0042-phase-0), [plan 0042 log](../../plans/0042-quests-travel.md#implementation-log)

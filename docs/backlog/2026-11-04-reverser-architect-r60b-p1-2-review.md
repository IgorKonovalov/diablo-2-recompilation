---
from: reverser
to: architect
date: 2026-11-04
status: open
context:
  - ../plans/0060-item-use-inventory.md
  - ../findings/items/0013-grids-belts-stacks.md
resolution: ""
---

Review request (Tier B check), plan 0060 P1.2, lane/r60b. items/0013; run:2026-11-04-inventory-emu: 9 560 cases, 10 families, 0 mismatches: search, belt, rowfor, invrec, beltrec, stackok to the return, place, beltplace at InvGridPut, put at InvItemRemove, merge at UnitSetStat, each a boundary past which nothing is covered. 70 symbols I, none raised. 25 harness cases in § 10. Worth checking: the reading that a cursor item makes the page != 0 test pass (§ 5), the stub at 0x0055E9A0 as no split, the survey's unfollowed table pointers to 0x0065C140 and 0x00660C70, the unread tail of ItemAutoEquipSlot.

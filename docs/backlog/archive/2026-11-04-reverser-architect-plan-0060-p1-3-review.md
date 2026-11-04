---
from: reverser
to: architect
date: 2026-11-04
status: done
context:
  - ../../plans/0060-item-use-inventory.md
  - ../../findings/items/0014-ground-items.md
resolution: "Tier A review, accept with fixes (10); ADR-0029 proposed for the owner; drop's statements and dispatch's pass are [I] until it is decided; Phase 2 may start; entry in plan 0060's log."
---

Plan 0060 P1.3 (lane/r60c): Tier B check of [items/0014](../../findings/items/0014-ground-items.md). run:2026-11-04-ground-emu: 8 families, 8 728 cases, 0 mismatches at the boundaries stated, 33 symbol rows at I, 20 harness cases. Points to weigh: the drop family's allocator runs on a declared pool page with the two lock import slots holding a ret 4 of the image (no instruction patched, locks not evidenced, stated in the finding's head and the run record); a monster's drop's zero expiry is [I] with its scan's scope, Phase 2 case 7 reads it; quests/0002's search corrected, entries filed for the spec-writer and the archivist (expfield.d2).

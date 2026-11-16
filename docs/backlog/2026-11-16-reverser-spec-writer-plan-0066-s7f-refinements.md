---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context:
  - ../findings/frame/0001-tick-and-messages.md#10-plan-0066-batch-s7f-constants-tables-and-the-net-queue-with-a-second-tool-2026-11-16-lanen66o
  - ../findings/path/0001-pathplan-register.md#17-plan-0066-batch-s7f-constants-tables-and-mask-pairs-with-a-second-tool-2026-11-16-lanen66o
  - ../findings/drlg/0009-room-lifecycle.md#15-plan-0066-batch-s7f-the-inactive-records-writerreader-pairs-with-a-second-tool-2026-11-16-lanen66o
resolution: ""
---

Plan 0066 batch S7f (`lane/n66o`) settled 35 rows with a second tool: 27 raised, 8 raised in part, none contradicted.
Not blocking. For Phase 3, a few readings refine what the specs say; none changes a behaviour.

1. **sim/frame, Constants, `unit type → list`:** the table is six dwords, and its readers are 7 scaled loads in 5
   functions: `EventQueueAt`, `EventQueueEveryFrame`, `EventFree` and two list-address helpers 0x00540B30 and
   0x00540B70, not only the two the row names (frame/0001 § 10, row 11).
2. **drlg/lifecycle, the monster record `+0x20`:** AI control `+0x34` is saved in the same branch as `+0x1C`, so only
   when the AI link type `+0x30` is 1; otherwise `+0x20` stays 0. The save also clears AI control `+0x2C` to −1 and
   `+0x34` to 0 (0x0058F4AF–0x0058F4BB) (drlg/0009 § 15, row 42).
3. **drlg/lifecycle, the item record `+0x08`** (`0x00629F20(item)`): no reader in `InactiveItemRestoreOne`,
   `InactiveItemsRestore` or `ActInactiveItemRecsExpire` (drlg/0009 § 15, row 39).
4. **path/search L2:** the 51-pass bound holds for any `h0` (checked over `h0` 0..599, `b1C` 0..255, types 0 and 16),
   so the `h0` ≥ 2 condition can go; the loop also ends at a found node or a full node pool (path/0001 § 17, row 26).
5. **path/search L3:** "the first try keeps the parent's direction" holds for the non-drawing types; under type 16 the
   turn adds a draw (step 18) (path/0001 § 17, row 27).
6. **path/README E4:** the constants are 10 at the five reseed callbacks and 14 at `SkillDo73BlessedHammer`, with
   creation's 4 (path/0001 § 17, row 44).

Each raise's tag change for the spec (the rows' *Route* cells, inventory README § 4 S7f) goes in with the Phase 3 pass.

---
from: reverser
to: reverser, spec-writer
date: 2026-11-04
status: open
context:
  - ../plans/0060-item-use-inventory.md
  - ../findings/items/0017-community-cross-check.md
  - ../specs/items/use.md
  - ../specs/items/inventory.md
resolution: ""
---

From the `lane/r60d` cross-check ([items/0017](../findings/items/0017-community-cross-check.md)), for the review of that finding. Verdict ids are the finding's. No tag moves on any of this.

**To reverser, required cases for a later harness run, both on stock data:**

1. **H3, a mana potion to the hireling.** `src:arreat-summit-potions` says Health, Mana and Rejuvenation potions in the belt go to the hireling; D3's test at `0x00562464`..`0x00562486` passes types 76, 81, 80 (`hpot`, `wpot`, `apot`), and `mpot` is 77. Request `0x26` with the flag, a hireling alive, an expansion game, for `mp1`, `hp1`, `rvs`, `yps`, `wms`; and `0x61` for the same rows on the cursor. Log `ITEMS_UnitIsType`'s three results and whether `ItemUse` is reached with the hireling as user. A wrong reading would show `mp1` reaching `ItemUse`. `rvs` separates whether `ITEMS_UnitIsType` follows `Equiv1`.
2. **H2, a second potion.** Three sources average every second potion over the summed time; 3 of 4 live pairs allocated a new list. Add to the spec's Open question "The blend": pairs of **different tiers** (a pair of equal tiers cannot separate the blend from `v ÷ len`), each list pointer `UNIT_FindStatListByState` returns, the user's lists at the second use, the rates set, and the stat 74 total applied per frame while two lists would run. The last is what separates "not any faster" from two lists at once.

**To reverser, a reading:**

3. **B8, a gap.** `src:maxroll-death` (D2R): at death the belt's upper rows empty into the inventory, then to the ground. The record names `BeltOverflow`'s callers as the body moves' branches (`0x00560C45`, `0x00563D20`) and a "corpse overflow" among `GroundDropCell`'s callers, with no belt rule. Say how a dying player's belt reaches either, and with which row count.

**To spec-writer, on the next pass of the specs:**

4. [items/use](../specs/items/use.md) § Open questions: name the type in "a potion to the mercenary": `mpot` does not pass D3's or D5's test on the reading, against `src:arreat-summit-potions` (H3). In "The blend", add the sources' statement that a second potion is always averaged (H2).
5. [items/use](../specs/items/use.md) F3, F4, one reimplementation note: in 1.14d the class scale is code, with no `charstats` column; `HealthPotionPercent` and `ManaPotionPercent` are D2R's (P3).
6. [items/inventory](../specs/items/inventory.md) § F, or the Belts table doc through its lane: a note that `src:d2dfg-blizzard`'s "Server verification" for the box rectangles is a D2R text, against A2's reading for 1.14d, so a reimplementer adds no server test (B3).
7. [items/inventory](../specs/items/inventory.md) § Open questions: add B8 until the reading in 3 lands.

---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../findings/skills/0002-missiles.md
  - ../../specs/skills/dispatch.md
resolution: "Plan 0066 Phase 3, skills cluster (lane/n66sk): items 1–4 in [skills/dispatch](../../specs/skills/dispatch.md) C7, N2 (the pseudocode rewritten: type 45 test, stackable first, ItemHasDurability, the wrapped sign test) and the § K rows 26 and 27."
---

Plan 0066 batch S2ae part 7 (`lane/n66sa`, run:2026-11-16-sweep2-s2ae7) raised skills/dispatch row 40 (C7,
`ItemChargesOk`) whole and rows 130, 131 (§ K, handlers 26 and 27), 156 (N2) and 181 (§ P, weapon wear) in part. For
Phase 3 to carry when the skills cluster is re-tagged (claims and anchors in
[skills/0002 § 23](../../findings/skills/0002-missiles.md#23-plan-0066-batch-s2ae-part-7-skills_itemchargesok-skillweaponwear-and-handlers-26-and-27-emulated-2026-11-16-lanen66sa)),
the spec says less than the code in these places:

1. **C7.** A null unit or entry is refused (0); no inventory, or an entry whose item guid is −1, passes. The level in
   the layer is `SKILLS_GetSkillLevel(unit, entry, 0)`: the entry's base `+0x28` in `[0, ExpMaxLevel(0)]`, no bonus.
   The inventory walk stops at the first node that is not an item (type 4), which passes like a missing item.
2. **N2.** The function tests the item it is given with `ITEMS_UnitIsType(item, 45)` (the record's type, then its
   second type when > 0); "has durability" is `ItemHasDurability` (record `+0x113` = 0, `+0x112` > 0, stat 73 base
   and value non-zero, stat 152 ≤ 0). The roll is `low mod 100` (unsigned) against the chance as a signed integer,
   and the break test is the sign bit (or zero) of the 32-bit `dur − amount`, not a mathematical `≤ 0` (they differ
   when the subtraction wraps). The stackable branch comes first and does not test durability.
3. **K row 26.** Gates: the golem of type 1, packet `+0x4C` > 0, a `MonsterOwner` that is not dead
   (`UnitIsDead`), the owner's life ≥ 256, a MonStats row with a non-negative `+0x170` skill. The loss is
   `MulDiv(+0x4C, Skills[that skill] +0x158, 100)`; the owner's life becomes `max(life − loss, 256)`.
4. **K row 27.** `v` = stat 150 (layer 0) ≠ 0 is capped at 50 against a player or a monster with MonsterData
   `+0x16` & 0x0C and at 90 against another monster (a negative `v` is not capped); other unit types get nothing.
   The state call carries (unit, other, 0, 1, 750, 0x43, −v, 0x18, 0).

Not blocking.

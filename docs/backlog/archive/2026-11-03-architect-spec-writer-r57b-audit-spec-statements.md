---
from: architect
to: spec-writer
date: 2026-11-03
status: done
context:
  - ../../findings/quirks/0001-community-bugs.md
  - ../../plans/done/0057-quirks-catalogue.md
resolution: "Both statements stated, [I]: [combat/damage step 5 and its note](../../specs/combat/damage.md#a-combat_builddamage-in-order) (the packet's base inside the drain roll) and [combat/to-hit's arPct row](../../specs/combat/to-hit.md#runtime-state) (0 for a monster's melee test, the missile's stat 19 for its line missile). Index Q474 and Q471. lane/s68."
---

From the `lane/r57b` audit, two reviewed statements that the objdump reading of [quirks/0001](../../findings/quirks/0001-community-bugs.md) qualifies. Not blocking; take them with plan 0057 Phase 3 or the next pass over combat.

1. **combat/damage step 5.** `pkt.lifeSteal += Roll(60, 61) × srcdam ÷ 128` and its mana and stamina lines hide the base: `COMBAT_RollElemStat` is given the packet's field and returns it with the roll, and the result is added to the same field, so the field is `field + (field + roll) × srcdam ÷ 128`, and `field + max(field, 0) × srcdam ÷ 128` when the stat is below the roll's floor. [I] (0x0057BA71–0x0057BAF3, 0x0057A8F7–0x0057A905, fn:COMBAT_RollElemStat@0x0057A8E0)
2. **combat/to-hit, the `arPct` input row.** "0 for a monster" holds for its melee test, not for its line missile, which passes the missile's stat 19. [I] (0x005AE05F–0x005AE06F, fn:MISSILE_HitUnit@0x005ADF10, row 17 of the finding)

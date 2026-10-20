---
from: reverser
to: spec-writer
date: 2026-10-20
status: open
context:
  - ../findings/skills/0002-missiles.md
  - ../specs/drlg/collision.md
  - ../specs/combat/README.md
  - ../specs/items/economy.md
resolution: ""
---

Not blocking; for plan 0045 Phase 3 or an earlier fix, from [skills/0002](../findings/skills/0002-missiles.md) (plan 0045 P1.2, all `[I]`):

- [drlg/collision](../specs/drlg/collision.md) *Open questions* "C2's reader": the missile reader of the `0x40` mark would be `CollideType` 7 (mask `0x40`, a `CanDestroy` missile as the target), which no stock row uses (skills/0002 § 4); and missile do function 3 (26 stock rows: the clouds, blizzards, `plaguejavelin`) is a second **writer** of `0x40` (`COLL_CellOrAt` on its cell each frame while its path is still). The placement masks stay as they are. `HitUnit` removes the creation mark (`COLL_SizeUnmark(…, 0x40)`) when a missile ends (§ 5).
- [combat](../specs/combat/README.md) (the missile packet oracle): the weapon terms of a missile are taken **at creation** (§ 3), with 1–3 critical draws on the **owner's** seed for a weapon-share missile; the hit's draw order on the missile's seed is § 6 (up to seven `RNG_RangeB`); the to-hit roll is on the owner's seed with missile stat 19 as the percent bonus (§ 5).
- [items/economy](../specs/items/economy.md) `PLAYER_UseAmmo` gates: the `useAmmo` argument per call site is § 2 (1 at `SKILL_AttackDo` unless the ranged missile is 27, at Throw and Left Hand Throw, and at a few monster and skill functions; 0 at `SKILLS_SrvDo`).
These are inputs; the spec text is yours.

*2026-10-20 (architect, `lane/p45m` review): ruling on the creation-time critical draws, for the combat spec's RNG order.*
The draw sequence was spot-checked on the pinned binary (0x0064A850–0x0064A92D). What the spec should state, all `[I]`
(fn:sub_0064A850_MissileCritRoll@0x0064A850, fn:sub_0064B860_MissileDamageBlock@0x0064B860):

1. **A new event on the owner's seed: missile creation.** `MissileCreate` → `MissileDamageBlock` draws 1–3 inline steps
   on the **owner's** seed when the missile takes a weapon share (Missiles `SrcDamage` ≠ 0 on a Missiles-damage row, or
   the Skills row's `SrcDam` for a skill missile, `SrcDamage` = `0xFF` cancelling it): stat 337 first, **even at 0**, then
   stat 141 when non-zero, then the mastery critical when a weapon is held and it is non-zero, stopping at the first
   success. A `SrcMissDmg` missile draws the same chain on its **source** unit's seed (a missile's own seed) instead.
   Add it to combat/README § B as its own event (B4, or a step before B3), at creation time, not at the hit.
2. **It is not the melee build's chain.** damage.md step 3 is mastery, 337, 141, each only when > 0, inside
   `COMBAT_BuildDamage`; the missile chain has a different order and an unconditional first draw. Do not reuse step 3
   for missiles; state the missile chain where the missile packet is (delivery/damage, wherever phase (3)'s input is).
3. **§ C's `[C]` chaining claim stands** for the paths the 2026-10-16 run reproduced (it is a run result). Add an `[I]`
   note that a weapon-share missile created by the player (bow and crossbow attacks, javelins, throws, `SrcDam` skill
   missiles) inserts these draws between the player's events at its creation frame. Do not state it as the cause of the
   213 resynchronisations; plan 0045 Phase 2 tests that.
4. **Monster owners draw too.** The stat-337 draw happens at 0, so every weapon-share missile of a monster (an archer's
   arrow) steps the monster's seed once or more at creation. B2 and § C's monster chain describe the melee path; scope
   them so ("a monster's melee attack") rather than leave the missile case implied.
5. **rng/seeds** *Open questions* (skill and missile re-seeds): `sub_0059F940_MissilePierceCount` is an
   initialiser-calling site that makes a **local** seed from the owner's base stat 328 and touches no unit seed; it can
   be listed as classified (skills/0002 § 3).

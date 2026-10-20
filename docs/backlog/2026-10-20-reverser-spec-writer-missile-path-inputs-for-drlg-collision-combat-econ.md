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

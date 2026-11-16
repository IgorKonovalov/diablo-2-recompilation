---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context: ["../plans/0066-simulation-inferred-claims-sweep.md", "../findings/skills/0002-missiles.md"]
resolution: ""
---

Plan 0066 batch S2ae part 2 (`lane/n66sa`, run:2026-11-16-sweep2-s2ae2) raised skills/dispatch C4 (rows 36, 37) and
D3 (row 49), and skills/missiles D6 (row 47) and the collide-type filter cells (rows 40–42, 45, 46), with these
refinements for Phase 3 to carry when the skills cluster is re-tagged (claims and anchors in
[skills/0002 § 18](../findings/skills/0002-missiles.md#18-plan-0066-batch-s2ae-part-2-the-mana-checks-and-the-collide-filters-emulated-2026-11-16-lanen66sa)):

1. **C4 / D3, the level:** `lvl` is the entry's base plus `SkillLevelBonus` (the bonus's terms are listed in § 18:
   state 134 + 2, stat 127, own-class stats 83 and 188, stat 97 capped at 3 for the own class and for a non-player
   with base above 0, stat 126 at the row's `+0x1DC` byte, stat 107), clamped to `[0, ExpMaxLevel(0)]`.
2. **D6, the last hit:** the last-hit refusal applies only to a missile whose Missiles row has bit 0 of `+4`
   (`MISSDATA_IsLastHit`).
3. **D6, the friend test:** with no owner it is skipped; an owner that is the candidate counts as not hostile, so it
   is refused unless `CollideFriend`; two players are hostile when the owner's relation node for the candidate has
   bit 3 (`PlayerPairFlags(…, 8)`), others unless both alignments (`UnitAlignGet`) are 0 or both 2.
4. **Type 1 filter:** `UnitAlignGet` is stat 172 of the unit's state-0x69 stat list (0 with none), 2 for any type
   above 1.

Not blocking. The mask cells of the type table stay as tagged (S2ae part 3).

*2026-11-16 (reverser, `lane/n66sa`, S2ae part 3):* the mask cells were raised after all (the two `lea`s carry no
store; [skills/0002 § 19](../findings/skills/0002-missiles.md#19-plan-0066-batch-s2ae-part-3-the-mask-uses-read-calldofunc-hit-27-and-unique-mod-29-emulated-2026-11-16-lanen66sa)); part 3's refinements are in
[`2026-11-16-reverser-spec-writer-plan-0066-s2ae-part-3-refinements`](archive/2026-11-16-reverser-spec-writer-plan-0066-s2ae-part-3-refinements.md).

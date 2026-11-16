---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/skills/0002-missiles.md
resolution: "Done (lane/n66sk, Phase 3 skills cluster part 1): missiles B1's unique-mod-29 hook (gates, seed, side point, first creation; the second [I]), the mask cells and G2's CallDoFunc written in. [plan log](../../plans/0066-simulation-inferred-claims-sweep.md#2026-11-16--phase-3-the-skills-cluster-re-tagged-part-1-spec-writer-lanen66sk-skillsreadme-missiles-and-catalogue-resume-note)"
---

Plan 0066 batch S2ae part 3 (`lane/n66sa`, run:2026-11-16-sweep2-s2ae3) raised skills/missiles G1's hit 27 (row 73),
the collide-type mask cells of D6 (rows 40–42, 45, 46, now whole with part 2), and in part B1's unique-mod-29 hook
(row 21) and G2's `CallDoFunc` (row 69), with these refinements for Phase 3 to carry when the skills cluster is
re-tagged (claims and anchors in
[skills/0002 § 19](../../findings/skills/0002-missiles.md#19-plan-0066-batch-s2ae-part-3-the-mask-uses-read-calldofunc-hit-27-and-unique-mod-29-emulated-2026-11-16-lanen66sa)):

1. **B1, the hook:** `UModEventRun` (slot 5) needs a non-zero first unique-mod byte and then calls every one of the
   nine, a later 0 not stopping it. Mod 29 acts only when bit 3 of the monster data's byte `+0x16` is set, the missile
   is type 3 with an owner, its class lies in the Missiles count, the row's `+5` bit 4 is clear, and the owner (a
   monster) is not already marked `+0x16` bit 0x80; it sets that bit for the creations.
2. **B1, the seed:** `Init(0x53454953)`, then its high word is overwritten with the owner's unit id; nothing reads it
   before the first creation (the spec's "makes a local seed" holds; no draw is made from it there).
3. **B1, "beside this one":** the two missiles are placed one sub-tile to each side of a point, perpendicular to the
   owner's direction: the point is the owner's (revalidated) path target, else the missile's path position;
   `(dx, dy)` are the signs of owner − point, zeroed for classes 0x3F–0x42; the first is
   `SkillMissileCreate(owner, skill, lvl, 0, 0, x0 − dy, y0 + dx, 0)` with the missile's skill and level. The second
   (`x0 + dy, y0 − dx`) is past an allocation and stays `[I]` (class b).
4. **G2:** `CallDoFunc` passes its `ECX` and `EDX` (game, the missile) through to the do function unchanged, with the
   stack `(skill, lvl)`; past the bound it returns `n`, at a null entry 0.

Not blocking. The mask cells need no text change, only the re-tag.

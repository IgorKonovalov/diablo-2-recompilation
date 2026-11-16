---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context: ["../plans/0066-simulation-inferred-claims-sweep.md", "../findings/skills/0002-missiles.md", "../specs/skills/dispatch.md", "../specs/skills/missiles.md"]
resolution: ""
---

Plan 0066 batch S2ae part 5 (`lane/n66sa`, run:2026-11-16-sweep2-s2ae5) raised skills/dispatch row 47
(`SKILLS_TargetCheck`, D2) whole with one **contradiction**, skills/missiles row 77 (callback `0x005CD110`) whole, and
rows 75 (callback `0x005D40F0`) and 82 in part. For Phase 3 to carry when the skills cluster is re-tagged (claims and
anchors in
[skills/0002 § 21](../findings/skills/0002-missiles.md#21-plan-0066-batch-s2ae-part-5-skills_targetcheck-and-two-re-seed-callbacks-emulated-2026-11-16-lanen66sa)):

1. **Contradiction, skills/dispatch D2 (`TargetCheck`'s target clear):** D2 says a dead target (`+0xC4` bit 1) is
   kept only by a `TargetCorpse` skill and otherwise cleared, other targets kept. The emulated map (0x0056CCF0–
   0x0056CD35; `split.txt`, 1 433 of 1 593 cases against D2's reading, the D2 reading as a control changes 1 564
   cases and matches none of them) is: `+0xC4` bit 1 **clear** → the target is cleared; bit set and the target a
   type-1 unit in mode 12 → kept by a `TargetCorpse` skill, cleared otherwise; bit set and any other target →
   **cleared** by a `TargetCorpse` skill, **kept** otherwise. Every branch past the `TargetableOnly` tests returns 1.
   "Cleared" is `UnitSetPathTargetUnit(unit, 0)`: the caster's path `+0x58` ← 0, and the fatal path for a caster not
   of type 0, 1 or 3. The code does not say what bit 1 means; the "dead" name should not survive unless another
   finding gives it. *(Tier A review, 2026-11-16: scope confirmed against 0x0056CCF0–0x0056CD43; the contradiction
   is D2's clear rule only, its first two clauses stand with items 2 and 3's refinements. No finding gives the name:
   skills/0003 § `TgtPlaceCheck`'s "dead" for `MonSkillTargetOk`, which requires the bit **set**, is marked there as
   a name, and the table doc's copy is routed to the archivist. The spec's other uses of `+0xC4` (items/tc's bit
   17) are not this bit.)*
2. **D2, the `TargetableOnly` tests:** three, in order: `UnitsHostile(game, unit, target)`, then `SkillPetTest`
   (the row's `+7` & 2, and the target a monster whose owner record names type 0 and the caster's guid), then
   `SkillAllyTest` (a player caster, the row's `+7` & 4, a player target or a monster owned by a player, and equal
   party ids); 0 when none passes. D2 names only the hostile and ally tests.
3. **D2, the target itself:** `UNIT_GetTargetUnit` re-finds the stored target by its type and guid and clears it when
   another unit (or none) is found, or when the unit found is an item in mode 1 or 2; the caster itself counts as no
   target. No target passes (1); a skill outside `[0, nSkills)` with a target fails (0).
4. **skills/missiles H, re-seed table, callback `0x005D40F0`:** `Init(argument)` (the argument alone), range capped
   at 77, type 10, `PathPlan(path, missile, 0)`: the same entry as `0x005C9290`'s, so "Draws after: none" leaves out
   the walk's steps (past the observed boundary, `[I]`, H1).
5. **H, callback `0x005CD110`:** `Init(path word +0x10 + argument)`, one inline step, then **only when** that step's
   low dword unsigned mod 100 is at least 20: type 10 and `PathPlan` (with the walk's steps after it, `[I]`); below 20
   the callback ends with the path unchanged.
6. **H1, "the other re-seed callbacks … reach the same walk":** `[C]` for these two callbacks up to `PathPlan`'s entry
   (type 10, `+0x90`/`+0x91` the capped range); the walk itself and the do functions stay open in plan 0066.

Not blocking. Row 77 needs only refinement 5 and the re-tag; D2 needs the contradiction carried before it can be
re-tagged.

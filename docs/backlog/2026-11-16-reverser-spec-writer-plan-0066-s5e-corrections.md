---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../findings/combat/0001-formulas.md
resolution: ""
---

Plan 0066 batch S5e (`lane/n66t`) found these against the combat specs at `b5999f5e`, from the emulation
run:2026-11-16-sweep2-s5e ([combat/0001 § 19](../findings/combat/0001-formulas.md#19-plan-0066-batch-s5e-part-1-emulated-reduction-and-to-hit-leaves-run2026-11-16-sweep2-s5e)).
For Phase 3 (re-tag); not blocking.

1. **Contradiction in part, reductions B2 (line 233) and the note at line 253.** `COMBAT_ResistFor`'s sanctuary test
   (row 0, attacker state 47, undead defender → 0) sits inside the `r ≥ 1` branch, after the cap (0x0057BEDE–0x0057BF02):
   a physical resistance of 0 or below is returned unchanged. B2's pseudocode puts the test after the floor for every
   `r`; 11 emulated cases separate the two readings. Line 253's "zeroes physical resistance against undead" holds for a
   positive resistance only.
2. **Refinement, to-hit C3 (lines 312 and 337).** `COMBAT_AvoidRoll`'s "moving" test for modes 2 and 15 applies to a
   defender of any type other than 0, not only a monster (type 1); 264 emulated cases of types 2 to 5 separate it.
   The weapon-block check is called from two sites, 0x0057DDAB for a player and 0x0057DEEA for the others.
3. **Refinement, reductions A2 (line 133).** A hireling against a boss returns 100 when the context's difficulty
   record pointer is 0 (0x0057C0FA–0x0057C0FC).
4. **Refinement, to-hit A7.** The stat-116 block runs only when the stat is above 0, so A7's clamp acts on a halved
   value only; a defender of type 2 to 5 is neither zeroed (stat 115) nor halved.
5. **To-hit A6 (line 161).** The state record `PreventHealHook` passes holds nine words: attacker, defender, 0, 1,
   120 000, 31, 0, 52, 0 (0x0057D869–0x0057D891); the 52 is the state id.

**2026-11-16, reverser (`lane/n66t`), S5e part 2 corrections** (evidence:
[combat/0001 § 20](../findings/combat/0001-formulas.md#20-plan-0066-batch-s5e-part-2-stat-events-life-tick-and-the-damage-builder-run2026-11-16-sweep2-s5e2),
run:2026-11-16-sweep2-s5e2). Phase 3's to apply:

6. **Damage A step 1 (lines 89–94).** The condition is "att is type 0, or `UnitAlignGet(att)` = 2" (every unit of
   type 2 or more; a type-1 unit through the stat 172 of its state-105 list), and def type 1, not "a player or a
   hireling". Stat 120 is **added**: `def's stat 31 ← max(0, stat 31 + stat(att, 120))`. Stats 121 and 122 are added
   only when positive (the undead sum `blunt + stat 122` likewise).
7. **Damage A step 5 (lines 106–112).** A player's or hireling's `lifeSteal` / `manaSteal` adds are skipped under the
   packet flags `0x04` / `0x08`, as the monster's drains are; units of type 2 or more take neither branch.
8. **Damage A step 6 (lines 113–118).** `COMBAT_RollRange` runs on every build with the poison field as its base and
   the result scaled **replaces** the field: `pkt.poison ← RollRange(57, 58, pct = stat 332 if stat 58 > 0 else 0,
   base pkt.poison) × srcdam ÷ 128`; at stat 58 ≤ 0 that is `max(pkt.poison, 0) × srcdam ÷ 128`.
9. **Delivery E1 (line 474 and the bullet at line 519).** At stat 36 ≥ 100 the blow is cancelled only while `cb` ≤
   0x100000; above it `MulDiv` divides first and the defender loses `cb mod 100`. A defender of type 2 or more gets
   `k` = 4 with no player-count term.
10. **Delivery E3 (lines 492–496).** `c ← (x·4 − dlvl + 10 + alvl [− 6])·5 [÷ 3]` with `x = max(stat 134 − 1, 0)`: the
    text's `(x − 1)·4` subtracts one twice. The draw is taken whenever stat 134 > 0, also at `c` = 0.

**2026-11-16, reverser (`lane/n66t`), S5e part 3.** Three more, from
[combat/0001 § 21](../findings/combat/0001-formulas.md#21-plan-0066-batch-s5e-part-3-the-defence-roll-with-a-shield-unit_getdefense-and-the-delivery-prologue-run2026-11-16-sweep2-s5e3)
(run:2026-11-16-sweep2-s5e3):

11. **To-hit B1 (lines 192–197).** For `d` ≤ 0 the percent term is subtracted: `d ← d − (d × p) ÷ 100` (the
    code multiplies by the negated magic at 0x006224DD), so a percent moves a non-positive defence toward 0. For
    `d` ≥ 1 the text holds. The Holy Shield term is gated by state 101's own stat list (base stats 350, 351 > 0), a
    Skills record and a shield through `InvItemQuery`, and is `SKILLS_EvalCalc(unit, record +0x138, 350, 351)`.
12. **To-hit C2 (lines 255–259).** `b ≥ 1` is tested before the `÷ 3`, not after: a moving player with a chance of
    1 or 2 still draws once (the block fails). The moving test reads `0x00621190`'s mode (`+0x40` when `+0x30` ≠ 0);
    the walking exception reads `+0x10`.
13. **Delivery B1 (line 297).** A defender with no room (`UnitGetRoom` 0) also clears `0x3` and returns, as the
    not-hostile case does.

**2026-11-16, architect (Tier B lane check of `lane/n66t`), additions for Phase 3.**

14. **Tags on the lines these corrections touch.** Three corrections reach lines the combat specs tag `[C]`; Phase 3
    re-tags each against § 20/§ 21, not against the old run. (a) delivery E3's tag on line 492 and its E3 bullet (line
    536: "each with its chance, draw and length as E3 gives them"): the old check
    (`workspace/logs/n66j/check-combat.txt`, `CASE freeze handler roll (melee): 81`, `freeze handler: freeze delivered
    (len 26..249): 81`) counted rolls and the length range only and did not compare the chance, so "as E3 gives
    them" is not what that run showed; the formula line stands `[C]` as § 20's `x·4` (run:2026-11-16-sweep2-s5e2),
    and the bullet's wording drops the chance. (b) damage A step 6 (line 113, `[C]` on run:2026-10-16-combat): the
    run's poison hits had a zero poison field at entry, where "add" and "replace" agree, so the `[C]` stands for that
    observed path only; the replace form is § 20's (correction 8). (c) to-hit B1: the `[C]` bullet at line 200 (the
    base term reproduced on logged, positive defences) stands; the `d ≤ 0` term (correction 11) goes in the `[I]`
    pseudocode line's replacement, tagged from § 21.
15. **Delivery row 46 is contradicted in part, not raised with a correction** (lane-check ruling): E1's
    "at 100 or more it cancels the blow … `cb` = 0 there" (line 519) is false above `cb` = 0x100000 (correction 9).

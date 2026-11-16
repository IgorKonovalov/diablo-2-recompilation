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

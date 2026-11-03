---
from: reverser
to: spec-writer
date: 2026-11-03
status: done
context: []
resolution: "Taken into the owning specs at the finding's tags: skills/catalogue J, K, M; skills/dispatch I4, L2; skills/missiles B2, E1; combat/to-hit A2, A6; combat/delivery B4, E1; combat/damage step 10; monsters/stats B8, G; items/tc MAX_DROP. Index: Q454-Q473 and Q254, the 'do not hold' section (rows 3, 12, 20, 25, 26, 28, 29), open questions (rows 9, 23, 30): [quirks § Community claims](../../specs/quirks/README.md#community-claims). lane/s68."
---

Plan 0057 Phase 3 and the owning specs: [quirks/0001](../../findings/quirks/0001-community-bugs.md) gives 30 verdicts. Not blocking.

**Rows with no owning statement** (the code reading is `[I]`; take them into the owning spec, or link the finding from the index until one does):

- skills/catalogue, do 42 and do 33: the knockback level difference is `slvl` (rows 1, 2). Do 74: `SKILLS_GetToHit` added to the missile's stat 19, the exception to row 18. Do 150: the forced hit bit, no flag `0x40`, the monster's mode 5 (rows 6, 7, 8).
- skills/dispatch I4: stat 137 twice with boots (row 4), and the weapon's damage stats disabled for the Assassin's kick build (row 3).
- skills/catalogue, do 65: Blessed Aim's `passivestate` is `penetrate`, so its apply removes Penetrate's list from the caster (row 19; the removal is already stated, the pair is not).
- combat/delivery B4 with monsters/stats § G: a `manahit` boss takes `256·v` mana (row 13). Each half is stated; the composed factor is not.
- combat/to-hit A2 with skills/missiles B2, E1: a monster's line missile counts stat 19 twice (row 17); and no to-hit for a player's skill missile (row 18).

**For the "does not hold" section:** rows 12, 20, 26, 28 (`contradicted`), each naming its statement in the finding; rows 3, 25, 29 (`not in 1.14d`). No reviewed statement changes because of them.

**Moved at the audit:** row 11 is `confirmed`, owned by combat/damage step 10, so it goes in the index and not in the "does not hold" section.

**Open questions:** rows 9, 23, 30, `[L]`, reasons in the finding.

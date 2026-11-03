---
from: reverser
to: spec-writer
date: 2026-11-03
status: open
context: []
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

Plan 0057 Phase 3 and the owning specs: [quirks/0001](../findings/quirks/0001-community-bugs.md) gives 30 verdicts. Not blocking.

**Rows with no owning statement** (the code reading is `[I]`; take them into the owning spec, or link the finding from the index until one does):

- skills/catalogue, do 42 and do 33: the knockback level difference is `slvl` (rows 1, 2). Do 150: the forced hit bit, no flag `0x40`, the monster's mode 5 (rows 6, 7, 8).
- skills/dispatch I4: stat 137 twice with boots (row 4), and the weapon's damage stats disabled for the Assassin's kick build (row 3).
- skills/catalogue: Blessed Aim's `passivestate` (row 19).
- combat/delivery B4 with monsters/stats § G: a `manahit` boss takes `256·v` mana (row 13). Each half is stated; the composed factor is not.
- combat/to-hit A2 with skills/missiles B2, E1: a monster's line missile counts stat 19 twice (row 17); and no to-hit for a player's skill missile (row 18).

**For the "does not hold" section:** rows 11, 12, 20, 26, 28 (`contradicted`), each naming its statement in the finding; rows 3, 25, 29 (`not in 1.14d`). No reviewed statement changes because of them.

**Open questions:** rows 9, 23, 30, `[L]`, reasons in the finding.

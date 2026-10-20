---
from: reverser
to: architect
date: 2026-10-20
status: open
context:
  - ../findings/skills/0010-necromancer.md
  - ../findings/skills/experiments.md
  - ../plans/0046-skills-function-catalogue.md
resolution: ""
---

Not blocking. Please review plan 0046 Phase 1 batch `nec` (`lane/p46m7`): the necromancer start functions 15–21 and
do functions 30–32 and 55–63, 19 entries (tier A: start 15, do 30, do 31)
([skills/0010](../findings/skills/0010-necromancer.md), run:2026-10-20-cat-emu-nec in
[experiments](../findings/skills/experiments.md)).

- **Run:** four families, 6 100 cases, 0 mismatches, 0 undeclared reads, 0 stopped; all 19 entries emulated; site
  control 1 891 of 1 891 (17 function/boundary/return-address triples); every negative control fails (three to seven
  per family, each family with one failing 76 or more). `workspace/logs/skills-cat-nec/manifest.sha256` `792c0cb4…`
  (28 files), `check.txt` `10fec33a…`, `static.txt` `c8bdc9e9…` (38 pins, the table entries, the read-only tables,
  the calc count's scan in every operand form, every call of each helper), `rows.txt` `2e561e99…`, tool `27b93f23…`;
  `repro.txt` `387455f3…`: the same tool revision regenerates 9a–9d's, `sor`'s and `ama`'s case, memory and
  expectation files and reproduces their `check.txt` and `static.txt` byte for byte. `EmuBoundary.java` unchanged.
- **Conventions:** `ama`'s, plus ruling 1's condition: at each boundary inside a helper (`0x005C2FF0`, `0x005C3300`,
  `0x005C31F0`, `0x005C5BC0`) the helper's return address into the batch function is compared at its absolute stack
  slot, and `static.txt` lists every call of each helper. Inputs set in the spec: `g_pDataTables`,
  `g_pDifficultyLevels`/`g_nDifficultyLevels` and `ITEMS_GetRecord`'s count and table (`0x0096CA58`/`0x0096CA5C`),
  all inputs on purpose (S1e ruling 3); no writer scan is cited for them.
- **Things to check:** (1) **do 57's fatal-path cases** end two helpers deep (start 20, then `0x00629CC0`); their
  return addresses are not compared, and the finding relies on one call of each on that path (§ 2): enough?;
  (2) **do 57's block word `+0x24`** is the frame slot `ebp−0x10`, which do 57 never writes before the call; the case
  writer puts a random word there and the block carries it (19 of 19), `[C]` as a value; (3) **the class-3 self-hit**
  (§ 5): `[C]` up to `COMBAT_ApplyDamage` with the packet by content; that class 3 is the paladin and that the packet
  is a hit of 1/8 life is `[I]`, the play consequence an Open question (harness); (4) **the weak controls**
  (`set33_skip`, `flag7`, `item_mode`, `hp4`, `pet_zero`, `flag1`, 4 to 13 failures) each with its deciding class
  named in § 2; (5) `0x0056E2F0` is declared a boundary (its `0x005DD480` not read), so start 21, do 58 and do 59 are
  `[C]` only up to their target tests.

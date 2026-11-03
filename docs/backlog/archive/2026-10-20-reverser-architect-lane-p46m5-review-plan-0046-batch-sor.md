---
from: reverser
to: architect
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0008-sorceress.md
  - ../../findings/skills/experiments.md
  - ../../plans/done/0046-skills-function-catalogue.md
resolution: "Reviewed 2026-10-20 (architect): accept with fixes (3: misread 1, overclaim 1, omission 1); rulings in plan 0046's log."
---

Not blocking. Please review plan 0046 Phase 1 batch `sor` (`lane/p46m5`): the sorceress start functions 11–14 and
do functions 17–29 and 144, 18 entries (tier A: do 18, 20, 22, 27, 28), with the Inferno helpers `0x005C8CA0` and
`0x005C8E30` ([skills/0008](../../findings/skills/0008-sorceress.md), run:2026-10-20-cat-emu-sor in
[experiments](../../findings/skills/experiments.md)).

- **Run:** six families, 8 500 cases, 0 mismatches, 0 undeclared reads, 0 stopped; 17 of the 18 entries emulated
  (do 27 Teleport read only, § 9); site control 2 977 of 2 977 (27 function/boundary/return-address triples); every
  negative control fails (two to six per family, each family with one failing 79 or more).
  `workspace/logs/skills-cat-sor/manifest.sha256` `83d7c0f9…` (35 files), `check.txt` `961ccef7…`, `static.txt`
  `91a6de74…` (35 pins, the table entries, the read-only tables, the writer scan of the `.data` inputs), `rows.txt`
  `148cf553…`, tool `7525830c…`; `repro.txt` `9a74392b…`: the same tool revision regenerates 9a–9d's case, memory and
  expectation files and reproduces their `check.txt` and `static.txt` byte for byte. `EmuBoundary.java` unchanged.
- **Conventions:** 9c/9d's, adapted to the skill functions: `(ECX game, EDX caster; id, lvl)`, the caster's and the
  target's seeds compared in every case, the blocks passed by pointer compared by content (`MissileCreate`,
  `STATE_ApplyTimed` at ECX, `SpawnOwnedMonster`, do 20's block, do 21's packet), the unit skill node's words and the
  second-argument slot compared as pre-call bytes; no model compares a callee-saved register that is not a boundary
  argument; meanings a callee gives (a state applied, a cell free, `StaticFieldMin`, a stun) are stated after the
  boundary (review-fixes 13).
- **Things to check:** (1) the one draw: do 21's `RNG_Range(caster seed, 100)` against `Param2` (control `tseed`
  fails 93, `stun_le` 23 on the cases at the edge); (2) `UnitsHostile`/`UnitsSameParty` run emulated (with the
  alignment rule `0x00650D70`/`0x006259B0`), which makes a player and a monster with no state-105 list "not hostile"
  (§ 4, an `[I]` consequence and an Open question): is that reading of the alignment rule worth a harness check
  before the spec states it?; (3) the `.data` inputs set in the spec (`0x0096C794`/`0x0096C79C` for `0x00663270`,
  `g_pDifficultyLevels`/`g_nDifficultyLevels`), justified as inputs of the claims with a writer scan (§ 2): enough
  under the S1e review's ruling 3?; (4) the weak controls (`nostate` 8, `town14` 6, `dist_ge` 9, `ign1c` 14,
  `charge_a` 17) beside a control of 79+ in each family, each deciding its claim deterministically.
- **Tags:** 34 `[C]`, 10 `[I]`, 4 `[L]` bullets.
- **Corrections** carried as a dated note into skills/0003 § 5 (do 18, 20, 22, 28 up to their boundaries; do 20's
  `+0x40` term is 0 outside an expansion game; do 22's velocity).
- **Symbols:** 25 rows (subsystem `skills/catalogue`, all `I`), no clash with `main` after the merge.
- Column readers filed to the archivist
  ([entry](2026-10-20-reverser-archivist-plan-0046-sor-skills-missiles-column-readers.md)).

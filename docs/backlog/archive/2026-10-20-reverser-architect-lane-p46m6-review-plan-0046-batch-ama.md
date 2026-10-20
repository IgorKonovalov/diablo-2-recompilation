---
from: reverser
to: architect
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0009-amazon.md
  - ../../findings/skills/experiments.md
  - ../../plans/0046-skills-function-catalogue.md
resolution: "Reviewed 2026-10-20 on lane/p46m6 at a6eaf75: accept with fixes (4: overclaim 3, stale cross-reference 1). Rulings: (1) frame words at a nested boundary admissible (ADR-0021 (c)); from the next batch the helper's return address is compared too or its single call site shown; (2) start 6/10's 0 is [C] as a value, AR meaning [I], combat/0001 note right; (3) the summons' +0x24 word [C] as a value; (4) srvmissileb [C] for word 0 only. Plan 0046 log. Next batch: nec."
---

Not blocking. Please review plan 0046 Phase 1 batch `ama` (`lane/p46m6`): the amazon start functions 4–10 and
do functions 6, 7, 8 and 10–16, 17 entries (tier A: start 4, start 5, do 7, do 8)
([skills/0009](../../findings/skills/0009-amazon.md), run:2026-10-20-cat-emu-ama in
[experiments](../../findings/skills/experiments.md)).

- **Run:** six families, 8 300 cases, 0 mismatches, 0 undeclared reads, 0 stopped; all 17 entries emulated; site
  control 4 190 of 4 190 (33 function/boundary/return-address triples); every negative control fails (two to four
  per family, each family with one failing 96 or more; the smallest, `nonorm`, 51).
  `workspace/logs/skills-cat-ama/manifest.sha256` `6a3181d8…` (37 files), `check.txt` `03a40fde…`, `static.txt`
  `b1b51e31…` (34 pins, the table entries, the read-only tables, the calc count's scan in every operand form),
  `rows.txt` `d441af4c…`, tool `69c01d13…`; `repro.txt` `9b03d065…`: the same tool revision regenerates 9a–9d's and
  `sor`'s case, memory and expectation files and reproduces their `check.txt` and `static.txt` byte for byte.
  `EmuBoundary.java` unchanged.
- **Conventions:** `sor`'s: both seeds compared in every case, blocks and packets passed by pointer compared by
  content, the unit's `+0xC4` and the second-argument slot as pre-call bytes, no callee-saved register that is not a
  boundary argument compared, callee meanings after the boundary (review-fixes 13). The writer scan cited (the skills
  calc function count) matches `PTR` and `moffs` stores, immediates and reads (ruling 3's condition): 0, 0, 7. The
  only `.data` input set is `g_pDataTables` (an input on purpose), plus the cookie as in 9a.
- **Things to check:** (1) **frame words at a nested boundary** (§ 2): where the boundary sits inside a helper the
  batch function called (`0x0063C9B0` inside `0x00623990`, `UnitGetWeapon` or `0x00622870`; the search inside
  `0x0056BC80`), the model compares the batch function's own frame words written before it (do 8's start point, step
  and `srvmissilea`; do 10's count, target and point) at their absolute stack address. They are bytes written before
  the call that the claim uses (ADR-0021 (c)), not registers; is that admissible as filed?; (2) start 6 and start 10
  pass 0 as `COMBAT_MeleeHitTest`'s second argument (`[C]` as a value), and the "AR percent" meaning, with what it
  implies for Power Strike's `ToHit`, is `[I]` after the boundary plus an Open question; a dated note says so in
  combat/0001; (3) do 15's and do 16's block word `+0x24` (the mode, the Skills record pointer: never stored by the
  function, the block spans those frame slots) is `[C]` as a value; its consequence is an Open question;
  (4) the `srvmissileb` choice of do 8 and 10 is `[C]` only for a caster with no inventory (weapon word 0); an armed
  caster ends at the inventory call, so the `≠ 1` test against 1 stays `[I]`.
- **Tags:** 31 `[C]`, 13 `[I]`, 4 `[L]` bullets.
- **Corrections** carried as dated notes into skills/0003 § 5 (start 4, start 5, do 7, do 8 up to their boundaries;
  do 8's step perpendicular, its start point, start 4's missing record test) and combat/0001 (skill melee hits: start
  6 and 10 pass 0).
- **Symbols:** 22 added (`I`, subsystem `skills/catalogue`); no address or name clashes with `main` at `9b5dfa8`.
- **Note:** the lane's first session was killed by the system's out-of-memory handler (six emulations at once); the
  resumed lane re-ran one family at a time and found the outputs byte-identical (experiments, Observed).

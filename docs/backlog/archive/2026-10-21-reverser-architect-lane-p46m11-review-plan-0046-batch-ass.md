---
from: reverser
to: architect
date: 2026-10-21
status: done
context:
  - ../../findings/skills/0014-assassin.md
  - ../../findings/skills/experiments.md
  - ../../plans/done/0046-skills-function-catalogue.md
resolution: "Reviewed 2026-10-21 (architect): accept with fixes (4: misread 1, stale cross-reference 1, wrong anchor 1, other 1); rulings in plan 0046's log; archivist and spec-writer entries released; the plan's Phase 1 carried-item text corrected to do 46."
---

Not blocking. Please review plan 0046 Phase 1 batch `ass` (`lane/p46m11`): the assassin start functions 22–28, do
functions 33–52 and 54, and the progressive entries 36–41 and 143, 29 entries (tier A: start 23, do 35, entries 38, 39,
143) ([skills/0014](../../findings/skills/0014-assassin.md), run:2026-10-21-cat-emu-ass in
[experiments](../../findings/skills/experiments.md)).

- **Run:** four families, 8 700 cases, 0 mismatches, 0 undeclared reads, 0 stopped; all 29 entries emulated; site
  control 3 020 of 3 020 (37 function/boundary/return-address triples); every negative control fails (five to seven
  per family, each family with one failing 165 or more). `workspace/logs/skills-cat-ass/manifest.sha256` `04f487b6…`
  (70 files, the two development runs under `dev/` with `dev/notes.txt`), `check.txt` `dd6ed294…`, `static.txt`
  `fcf4be4f…` (66 pins, the table entries, the read-only tables, the calc count's scan, every call of each nested
  helper and of `COMBAT_PrgFinisher`), `rows.txt` `3f8ff8a8…`, tool `b38bba31…`; `repro.txt` `43e65419…`: the same tool
  revision regenerates 9a–9d's, `sor`'s, `ama`'s, `nec`'s, `pal`'s, `bar`'s and `dru`'s case, memory and expectation
  files and reproduces their `check.txt` and `static.txt` byte for byte. `EmuBoundary.java` unchanged.
- **Conventions:** `dru`'s. `g_pDataTables` and the missile table and count `MissileSpeedAtLevel` reads (`0x0096C794`,
  `0x0096C79C`, as `sor`) are set in the spec, and the cookie. Nested boundaries (skills/0014 § 2), each compared at its
  absolute slot: do 33 → `0x0057E240`, do 35 → do 34, do 46 → `0x005D6200` (the two parities by the return address),
  entry 36 → `SkillNovaAtUnit`, 37/143 → their rings (and the ring's local seed), do 44/45 → `0x005D5E10`, do 54 →
  `0x005D7CE0`; the stack seeds of 39 and 41 at their frame addresses.
- **Things to check:** (1) **the draws before boundaries**: the inline step of the caster's seed at entry of 37, 39,
  41, 143 before the record test (a refused case returns stepped; `noseed` 1 200), and the stack-seed draws up to the
  first creation (39's `RNG_Range(local, 2r)` pairs, 41's two steps, the ring's one), each stack seed compared as
  frame words; (2) **four new observed boundaries** with their register reads (`COMBAT_PrgFinisher`, `UnitTeleport`;
  `InvGetBodyLocItem` and `0x006229F0` stack only), and the earlier ones newly given register arguments here
  (`SkillRollPhys`, `ApplyTimed`, `0x00553C70`, `MissileCreateAt`, `MissScatterAtTarget`), objdump cited in § 2;
  (3) **helpers run emulated** (start 22's test inside do 33, `0x0057E240`, `PrgCalcByCharge`, `MissileSpeedAtLevel`,
  `SkillNovaAtUnit` and the two rings up to their first creation, `0x005D5E10` with `MonsterOwner`, `0x005D6200`,
  `0x005D7CE0`, `LEVELS_GetRecord`, `STATS_GetUnitStat`): the claims cover only the paths reached (§ 2);
  (4) **the weak controls** (17 under 90), each with its deciding class recounted in § 2 (`prg_k1` 7 and `n18_le` 6 the
  thinnest); (5) **corrections** as dated notes in skills/0001 § 12 (the two finisher calls are do 46's, not start
  25's) and skills/0003 §§ 1, 5, 9 (the rings' `+0x28` is `SkillGetParam2(280) + 1`; tier-A start 23 and do 35);
  (6) the carried plan items: the five finisher calls (§§ 1, 4) and the `ItemEffect` 36 join (§ 1), and a spec-writer
  entry for combat/delivery A2/A3.
- **Surprises:** the rings never test their step count (0 is an endless loop, `[I]`); the rings' `MissileData+0x28` is
  Royal Strike's `Param2 + 1` for every row; the trap helper turns a bad `pettype` into 0 instead of refusing, and
  writes nine of the spawn block's ten words; do 35 returns 1 where do 34 refuses (and, by the reading, after its hit path) and sets bit 6 unconditionally
  for an inventory without two claws (`[I]`); Dragon Flight alternates kick and teleport by the frame parity and reads
  Levels `Teleport`; do 42 calls the finisher with a possibly null hit; do 33's knockback roll and do 42's last-kick
  `RNG_Range(100)` draw on the caster's seed after their boundaries (`[I]`); entry 40 and do 48 have no record test of
  their own.
- Tags: 39 `[C]`, 28 `[I]`, 4 `[L]` bullets; 27 symbols added (`I`, evidence 0014).

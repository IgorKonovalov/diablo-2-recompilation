---
from: reverser
to: architect
date: 2026-10-21
status: open
context:
  - ../findings/skills/0013-druid.md
  - ../findings/skills/experiments.md
  - ../plans/0046-skills-function-catalogue.md
resolution: ""
---

Not blocking. Please review plan 0046 Phase 1 batch `dru` (`lane/p46m10`): the druid start functions 56–58, do
functions 114–124 and do-table entries 145 and 146 (the States `srvactivefunc` of 144 `hurricane` and 145
`armageddon`), 16 entries (tier A: do 114, do 117) ([skills/0013](../findings/skills/0013-druid.md),
run:2026-10-21-cat-emu-dru in [experiments](../findings/skills/experiments.md)).

- **Run:** four families, 8 400 cases, 0 mismatches, 0 undeclared reads, 0 stopped; all 16 entries emulated; site
  control 3 967 of 3 967 (33 function/boundary/return-address triples); every negative control fails (four to six per
  family, each family with one failing 90 or more). `workspace/logs/skills-cat-dru/manifest.sha256` `d1a77e1f…` (69
  files, the two development runs under `dev/` with `dev/notes.txt`), `check.txt` `592baf51…`, `static.txt`
  `d2c98496…` (43 pins, the table entries, the read-only tables, the calc count's scan in every operand form, every call
  of each nested helper, the event-table words, the `0x005C7520` reference scan), `rows.txt` `fba56eef…`, tool
  `11b763dd…`; `repro.txt` `c6f4b37b…`: the same tool revision regenerates 9a–9d's, `sor`'s, `ama`'s, `nec`'s, `pal`'s
  and `bar`'s case, memory and expectation files and reproduces their `check.txt` and `static.txt` byte for byte.
  `EmuBoundary.java` unchanged.
- **Conventions:** `bar`'s. Only `g_pDataTables` (and the cookie) is set in the spec. Nested boundaries (skills/0013
  § 2), each compared at its absolute slot: start 58 and do 122 → `0x0056E680`, do 121 → `0x005C8980`, do 118 →
  `0x005C7040` (with its five pushed arguments), do 123 → `SkillTargetCellFree` and, for `RectTest`,
  `SkillTargetCellFree` → `COLL_WHTest`; call sites listed in `static.txt`.
- **Things to check:** (1) **`COLL_WHTest` run, not observed**: skills/0008 made it a boundary; here it runs with
  `COLL_CellTestNb` and `DUNGEON_GetCollMap` over one written collision word per case, so do 123's draw is reached
  (`RectTest` stays a boundary for `Size` ≥ 2); (2) **the two draws before boundaries** (do 124's `RNG_Range(0x10000)`
  kept at `ebp−0xC`, do 123's `RNG_Range(0x100)` low byte at `[ebp+0x8]`), each compared as a frame or argument-slot
  word with the caster's seed one step on (`seed_none` 202, `noseed` 72); (3) **entries 145 and 146**: their maps end
  at `UNIT_CancelEvents` (five early refusals share one exit), the town branch's `UNIT_UnlinkStatList`/`STATE_Set`, or
  the re-arm `CancelEvents`; entry 146's re-seed of the caster and its point draws are after the boundary, `[I]` (no
  callback boundary to emulate it alone: the code is inline after `UnitQueueEvent`); (4) **register arguments** of the
  new boundaries read before written (`STATE_GroupClear`, `UNIT_CancelEvents`, `SkillMissileCreate`,
  `COMBAT_BuildDamage`, `COLL_RectTest`, objdump cited in § 2); (5) **the weak controls** (`p4_noframe` 47,
  `nostate57` 47, `sd_first` 2, `mask7` 15), each with its deciding class in § 2; (6) **corrections** as dated notes in
  skills/0003 § 5 (the Firestorm row kept in step) and § 9 (the do 146 row), and a spec-writer entry for
  rng/seeds' open question on Armageddon's first period.
- **Surprises:** a `ResultFlags` bit-0 skill makes **no hit test** in start 58 and do 122 (`0x0056E680` returns the
  flags as the result; no stock row of either uses it); do 123 has **no upper test** on its class and reaches the fatal
  path in `SkillTargetCellFree`; do 119 puts the target point's x in the spawn block's `+0x24` and leaves the position
  words 0; do 120 evaluates the `aurastat` calcs at its stack count, not the skill level (`[I]`); do 124 draws at the
  cast and stores the value for Armageddon's first re-seed (`[I]` after the boundary); do 116 returns 0 when
  `STATE_GroupClear` clears a group; start 57 zeroes no packet before its hit test; `0x005C7520` has no reference in
  the image.
- Tags: 25 `[C]`, 25 `[I]`, 4 `[L]` bullets; 20 symbols added (`I`, evidence 0013).

---
from: reverser
to: architect
date: 2026-10-21
status: done
context:
  - ../../findings/skills/0016-monster-8a.md
  - ../../findings/skills/experiments.md
  - ../../plans/0046-skills-function-catalogue.md
resolution: "Accepted with fixes (5: misread 3, omission 2): PathDirection's 0xF fold on the x-major branch; the wrap bound 258 not 257; 0x005CC5C0 is do 95's no-point or failed-MissileCreate call; do 88's one refusal case named; do 110's MissileRec(m) test. Rulings: Ghidra-less start entries, first-time helpers, guarded allocator, start 48's Fatal, case-writer restrictions, thin do 88/do 97 coverage, the do 96 draw scope, unfollowed callers to 8b/8c, no spec-writer entry, all admitted. Archivist entry released. Reverser rule 15 promoted. Review in plan 0046's log."
---

Not blocking. Please review plan 0046 Phase 1 batch 8a (`lane/p46m13`): the monster skill functions of Skills rows
156–189, start 42–53, do 83–98, 110 and 111, 30 entries ([skills/0016](../../findings/skills/0016-monster-8a.md),
run:2026-10-21-cat-emu-8a in [experiments](../../findings/skills/experiments.md)).

- **Run:** five families (`hit_8a`, `move_8a`, `summon_8a`, `miss_8a`, `aura_8a`), 12 600 cases, 0 mismatches, 0
  undeclared reads, 0 stopped; all 30 entries emulated; site control 5 135 of 5 135 (31 function/boundary/return-address
  triples); every negative control fails (one to eight per family, each family with one failing 162 or more).
  `workspace/logs/skills-cat-8a/manifest.sha256` `10a8ce1f…` (106 files, three development runs under `dev/` with
  `dev/notes.txt`), `check.txt` `b06f25a1…` (nine `CLASS` lines, each equal to its control's failures), `static.txt`
  `f4ed00d9…` (52 pins, 30 table entries, 30 entry dwords in the file, the `.data` map scan, the helper call sites),
  `rows.txt` `d842e64a…` (34 Skills rows checked complete; the 52 MonStats `spawn` rows), tool `e2f67728…`; `repro.txt` `485fdbef…`:
  the same tool revision regenerates 9a–9d's, the seven class batches' and `item`'s case, memory and expectation files
  and reproduces their `check.txt` and `static.txt` byte for byte. `EmuBoundary.java` unchanged.
- **Conventions:** `item`'s, with two seeds compared in every case (caster, target) and every dumped byte written by
  the case. New observed boundaries with their register reads cited in skills/0016 § 2 (`SpawnNearUnitNoBox`,
  `UnitKilled`, `SpawnAtPos`, `COMBAT_ResolveAndQueue`, `SkillMissileCreateLob`, the allocator `0x0040B430` with `EDX`
  passed on unwritten; `0x00649F70`, `COLL_PatternMark`, `COLL_PatternUnmark` stack only). Nested: start 32 inside start
  42 (`0x7FEFFF70`), `0x005CC3B0` inside do 95 (`0x7FEFFF84`), `0x0056C210` inside do 111 (`0x7FEFFFD0`, its three
  stack words compared). The allocator is observed in one family only (`aura_8a`, do 111), guarded in the others.
- **Things to check:** (1) **the one draw**: do 96's `RNG_RangeB(caster, hi − lo)` before `UnitSetStat` on the target
  (`noseed` 94); (2) **emulated helpers new to the catalogue**: `PathDirection` and its `.rdata` table, the `.data` byte
  map `0x00745600` (declared read, scanned: no store, no immediate), `0x0063E7E0`'s offsets, `SkillSummonClass`'s
  MonStats path and its `0x0058F710` fallback, `MONSTATS_GetClassChainPos` (its `.data` table pointer set in the spec),
  `0x00645F00`; (3) **case-writer restrictions named with the reason** (§§ 4–6): `SkillSummonClass` faults for a
  non-monster with a refused Skills class and leaves its outs unwritten for a monster whose own class is out of range;
  do 111 has no id test and reads `[0x154]` for a bad id; `PathDirection`'s `(minor << 16) × 0x7F` wraps past 257
  subtiles and then reads outside its table, so do 87's and do 88's points stay within 250 (an `[L]` under *Open
  questions* whether play stays inside); (4) start 48's `Fatal` from `UNIT_GetTargetUnit` with no path is modelled as an
  outcome (16 cases), not avoided; (5) the dated note in skills/0003 § 4 (do 83's delivery now `[C]` up to its call);
  (6) the symbols: 38 added, all `I` (review-fixes rule 14's scope sentence).
- **Surprises:** do 110 writes stat 157's or 158's value over its level argument and casts missile 27 or 41 with it; do
  85 adds the caster's MonStats chain position to `srvmissilea`; do 93's `MissileCreate` target words are offsets, its
  position a sixth of the way to a point four steps out; do 88 sets no position or skill id, only the target point;
  start 49 marks a pattern in a room it never tests; do 98 falls back to the owner's room without testing the point
  against it; thirteen entries make no id test (start 43–46, 48, 50–52, do 83, 89, 94, 98, 111).
- Tags: 34 `[C]`, 6 `[I]`, 4 `[L]` bullets; 38 symbols added (`I`, evidence 0016).

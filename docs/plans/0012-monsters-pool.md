# 0012 — Monsters: the level's monster pool and monster level

> **Status:** approved (2026-10-11)
> **Created:** 2026-10-11
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only

## TL;DR

**Question:** when a level is created, which monster classes can it host, in which difficulty, and at what monster
level? `Levels` carries three pools (`mon1..10`, `nmon1..10`, `umon1..10`), a pool size (`NumMon`), critters, the
`rangedspawn` flag and the `MonLvl*` columns; `MonStats` carries per-class levels, group sizes and spawn flags. This plan
finds the code that turns those into the level's runtime pool, models it in `tools/monpool.py`, and checks the model
against pools logged at level creation. When it's done, `docs/findings/monsters/0001-level-pool.md` has the pool build
and the monster-level rule at `[C]` for the logged cases, and `docs/specs/monsters/pool.md` is drafted.
*Where* and *how many* monsters are placed (density, packs, minions) is `monsters/spawn`; champions and uniques are
`monsters/special`. Both are named here and left to their own plans.

## Context

- Research-map row `monsters/pool` (core), status `not started`. Its only dependency, `rng`, is **reviewed**; the
  level seed (`rng/seeds` step 4, level `+0x1C4`) is `[C]`. It does **not** need the DRLG room draws of plan 0008 unless
  Phase 1 finds the pool built after room creation; if so, the plan uses a boundary oracle (ADR-0004) for the room side.
- Data already in place: [Levels](../tables/Levels.md) layout `[C]` for every pool column (`mon*` `+0x036`, `nmon*`
  `+0x068`, `MonLvl*` `+0x010..+0x01A`, `MonDen*`, `MonUMin/Max*`, `NumMon` `+0x032`, `rangedspawn` `+0x031`), stored as
  the MonStats distinct-`Id` ordinal; [MonStats](../tables/MonStats.md) layout complete, semantics pending.
- Code already named, all `[I]` from [items/0001](../findings/items/0001-tc-resolution.md): `MONSTATS_GetRecord`
  `0x00451F80`, `sub_0061DCA0_LevelMonLvl` `0x0061DCA0` (picks `MonLvl[diff]` or `MonLvlEx[diff]` by game `+0x70`),
  `sub_006556E0_SuperUniqueGet`, `MONPRESET_GetActList` `0x00659B40`; data `g_pMonStats` `0x0096C6A8` `[C]`,
  `g_MonStatsLink` `0x0096C6AC`.
- Backlog this plan absorbs: spec-writer → reverser (a), the *Pandemonium 3* ordinal 723 question (is the second
  `cr_lancer8` reachable?) and how `g_MonStatsLink` is filled.
- Harness: ADR-0003 (wine on `:7`, gdb breakpoints logged), `tools/d2run.py`, `-seed N` runs; `tools/d2s.py setwp` and
  `progression` edits reach Nightmare and Hell (load test in plan 0004).
- Leads: none registered for monsters. Under ADR-0007, Phase 1b fetches one in-session (a community monster-spawning or
  `Levels.txt` column guide) and registers it in `docs/sources.md` before citing it.

## Phases

### Phase 0 — Monster tables the pool reads
- **Owner skill:** archivist
- **What:** document the tables and columns the pool and monster level read, with meaning columns where the data
  alone settles them.
- **Outputs:** `docs/tables/MonLvl.md` (new), `docs/tables/MonStats.md` (meaning for `enabled`, `Level`/`Level(N)`/
  `Level(H)`, `Rarity`, `isSpawn`, `MinGrp`/`MaxGrp`, `PartyMin`/`PartyMax`, `minion1/2`, `spawn`, `noRatio`/
  `killable`/`npc`/`boss`/`primeevil`-type flags), `docs/tables/Levels.md` (critter columns `cmon*`/`cpct*`/`camt*`,
  `umon*`, the `(N)`/`(H)` blanks, `mon9/10` always blank), `tools/excel_layouts.py` (monlvl).
- **Done when:** `excel_bin.py diff` reports 0 mismatches for `monlvl` and each newly mapped `MonStats` column; a
  survey in `Levels.md` lists, per difficulty, how many levels have an empty pool, a pool larger than `NumMon`, and
  pools naming a class whose `enabled` (or equivalent) is 0.

### Phase 1 — Read the pool build and the monster level
- **Owner skill:** reverser
- **What:** find and read the code that fills the level's runtime monster list, and the monster-level computation.
- **Outputs:** `docs/findings/monsters/0001-level-pool.md`, `re/symbols.csv` rows (subsystem `monsters/pool`), struct
  fields in `re/types/` for the level's pool.
- **Done when:** the finding states, with addresses and `[I]` or better:
  - where the pool is built (level creation, first activation, or per room), which seed it draws from, and its place
    relative to steps 4–6 of `rng/seeds`;
  - which column set is read per difficulty (`mon*` vs `nmon*`; whether classic and expansion differ), what `umon*`
    feeds, and how blanks and disabled classes are skipped;
  - the selection: how many entries are taken (`NumMon`, or another bound), the draw form (`RNG_RangeB` or other,
    range, order), whether duplicates are allowed, and any rarity weighting or `rangedspawn` rule;
  - the runtime pool layout (offset, count, element width) and who reads it (named, left to `monsters/spawn`);
  - monster level: `MonLvl` vs `MonLvlEx` vs `MonStats.Level*`, per difficulty and game type, and whether `MonLvl.txt`
    is read here or only for stats (the latter belongs to `monsters/stats`); champion/unique level bonuses named only;
  - critters: whether they come from the same pool or a separate draw;
  - the backlog (a) answer: whether ordinal 723 is used as a record position.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch and register at least one community source on level monster pools and monster level, then compare
  per `evidence-rules.md` § Community cross-checks (blind first; agreement never promotes a tag).
- **Outputs:** `docs/sources.md` entry, verdicts in the finding's *Leads used*, backlog entries for `contradicted`.
- **Done when:** the column set per difficulty, the pool size rule, the monster-level rule per difficulty and game
  type, and the critter rule each carry a verdict with a `src:` id (or `not covered`); every `contradicted` claim is a
  required case of Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser
- **What:** write `tools/monpool.py` (tables through `tools/excel_bin.py`, draws through `tools/rng.py`) that predicts
  a level's pool and monster level from the level seed, difficulty and game type, and check it against logged pools.
- **Logging:** a gdb script `tools/gdb/mon-pool.gdb` that logs, at the end of the pool build: level id, difficulty,
  game type, the seed before and after, and the pool entries; plus the monster level where it is computed.
- **Done when:** a run `run:YYYY-MM-DD-mon-pool` reproduces, with no oracle on the pool side:
  - at least 30 level creations over at least two `-seed` values, covering all three difficulties, every act, at
    least one level whose candidate list is longer than its pool size (so the draws matter), and one level with an
    empty pool;
  - every pool entry, the seed after the build, and the monster level of each logged level;
  - a classic-game creation, or the classic branch stays `[I]`;
  - *Pandemonium 3* in Hell (the ordinal 723 case), if reachable, else stays `[I]`;
  - the Phase 1b cases.
  In-scope claims are promoted to `[C]` citing the run; the backlog (a) entry is struck through.

### Phase 3 — Spec: monsters/pool
- **Owner skill:** spec-writer
- **What:** write `docs/specs/monsters/README.md` (the monster chain: pool → spawn → special → stats, with the rows
  not yet written marked so) and `docs/specs/monsters/pool.md`.
- **Done when:** the spec follows the template, every statement is tagged, it includes a worked example from the run
  (level seed in, draws, pool and monster level out), and the architect's review passes.

## Open questions

- If the pool is built per room or at activation, the plan's reproduction depends on the active-room seed and so on
  the k of plan 0008. Phase 1 decides; the fallback is an oracle on the room seed (ADR-0004).
- `MonDen`, `MonUMin/Max`, `MonWndr`, `MonSpcWalk` are read by spawning, not by the pool. Phase 1 names their readers
  only, for `monsters/spawn`.
- `MonStats.Level*` vs `MonLvl.txt` stats (HP, damage) belong to `monsters/stats`; this plan only settles the level.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-11 — Drafted (architect).** Next core row after the items chain; the Levels and MonStats layouts and the
  `LevelMonLvl` anchor from plan 0004 are its starting point.
- **2026-10-11 — Approved (human).** No changes to the draft.
- **2026-10-12 — Phase 0 landed (archivist).** New [MonLvl](../tables/MonLvl.md) doc and `monlvl` layout in
  `tools/excel_layouts.py` (120 B, thirty u32, `Level` = row index, not compiled): `excel_bin.py diff` 3 330 cells,
  0 mismatches; 6 offsets pinned by data, 24 by stride because each equals its classic/`L-` twin (only `AC(N)`,
  `AC(H)` and `HP(H)` differ between the classic and `L-` columns). [MonStats](../tables/MonStats.md#pool-and-level-columns-plan-0012-phase-0)
  gains *Pool and level columns* (every column was already laid out: 191 574 cells, 0 unexplained mismatches);
  meanings are `[L]` except `noRatio`/`boss` (`[I]`, items/0001 §4). [Levels](../tables/Levels.md#monster-pool-columns-plan-0012-phase-0)
  gains *Monster pool columns*: slot arrays, `mon9/10` and `umon9/10` always blank (`nmon9/10` used by 20 levels),
  the `(N)`/`(H)` blanks, critters, and the per-difficulty survey (normal `mon` / nightmare, hell `nmon`): 11 empty
  pools in every difficulty (exactly the `NumMon` 0 levels), pools over `NumMon` 85 / 104 / 104, pools naming a
  disabled class 0 / 0 / 0. New `tools/mon_survey.py` (`levels`, `monstats`) reproduces every count. Surprises:
  `nmon` equals `mon` in 117 levels (all 20 differences are Act 5); *Mountain Top* has a pool but `MonDen` 0.
  Phase 1 inputs in the backlog (archivist → reverser, 2026-10-12).
- **2026-10-12 — Phase 0 reviewed (architect): accept.** Checked: `excel_bin.py survey` monlvl 3 330 cells, monstats
  191 574, levels 13 152, all 0 unexplained; `mon_survey.py levels` reruns the survey (over `NumMon`: 85 / 104 / 104;
  empty: 11 per difficulty, exactly the `NumMon` 0 levels; disabled classes named: 0; ordinal 723 once). The
  difficulty → column-set mapping of the survey is an assumption and is stated `[L]`; the MonStats meanings are `[L]`
  except `noRatio`/`boss`. Both are Phase 1 questions, sent by the archivist to the reverser backlog. Next: Phase 1
  (reverser).
- **2026-10-12 — Phase 1 landed (reverser).** [monsters/0001](../findings/monsters/0001-level-pool.md). The pools are
  built **at game creation**, for every level id 1..136 at once, from the **first draw of the game seed**
  (`sub_00547D20_MonRegionsInit` → `sub_005479C0_MonRegionsBuild`, region seed `Init(low)`), not at level or room
  creation, so they need no map seed and no k (the plan's first open question). Normal reads `mon`, nightmare/hell
  `nmon` (selector `difficulty != 0`); picks `min(NumMon, 13, candidates)` by `Range` without replacement; first-pick
  `rangedspawn` redraw (≤ 20); `isSpawn` 0 dropped after the pick; then up to three appearance sets per entry
  (`sub_005BDB20_MonVariantRoll`, MonStats2) from the same seed. Region struct in `re/types/monregion.h`, array at
  `game+0xF0`. Monster level (`sub_00573CB0_MonStatsInit`): MonStats `Level*` except expansion nightmare/hell
  (`MonLvlEx`, not for `noRatio`/`boss`; hirelings use normal). `monlvl.bin` is stats only. `umon` = normal-difficulty
  champions/uniques; critters are a separate client draw. Ordinal 723 is a record position. 23 symbols (subsystem
  `monsters/pool`). Tooling: `re/ghidra_scripts/DecompileRange.java` + `tools/ghidra.sh decompile-range` (whole `.text`
  in about 3 min, for grepping).
- **2026-10-12 — Phase 1b landed (reverser).** Two leads fetched and registered after the finding was written:
  `src:rpgkdh-levels-guide` (Levels.txt column guide) and `src:pk-monstats-guide` (Phrozen Keep MonStats guide). Verdicts:
  column set **held**; `NumMon` **held with refinement**; `rangedspawn` **not covered**; `umon` **held**; `MonLvl*`
  **not covered**; monster level **held with refinement** (expansion only; `noRatio`, hirelings); `isSpawn`/`Rarity` **held
  with refinement**; critters **held with refinement**. No `contradicted` verdict, so no required case was added.
- **2026-10-12 — Phase 2 run (reverser), partial.** `tools/monpool.py` + `tools/gdb/mon-pool.gdb`,
  [run:2026-10-12-mon-pool](../findings/monsters/experiments.md#run2026-10-12-mon-pool): ten games, `-seed` 1–5, acts 1–5,
  no walking; 1360 regions, 47 monster levels, 130 critter rooms; `monpool: 1557/1557 match`; the game-seed draw index
  is asserted from N (no seed taken from the log). Rerun: `python3 -I tools/monpool.py check workspace/merged/data/global/excel workspace/logs/monpool-*.log`.
  Met: ≥ 30 creations over ≥ 2 seeds, every act, candidates > picks, empty pools, *Pandemonium 3* hell with class 723,
  every pool entry and seed after. **Not met:** nightmare and hell were reached by writing the difficulty byte before the
  build (the save swap to a nightmare/hell character was refused by the session's permission checks), and those games
  stop before monsters are created; so the monster-level rule and the classic branch stay `[I]`. To finish: a run with a
  character allowed into nightmare/hell (and a classic one) that logs MLV outside town (e.g. waypoint travel), needing
  the saves-directory swap. The architect decides whether the pool side counts as Phase 2 done.
- **2026-10-12 — Backlog (reverser).** Kill harness partly committed as `tools/d2hunt.py` (architect entry of 2026-10-11).
- **2026-10-12 — Review fixes F1–F2 applied (reverser).** monsters/0001 now states, in each `[C]` bullet that rests on
  the nightmare/hell logs, that the difficulty byte was forced at `0x00547D63` before the build's read (the pool reads
  difficulty only there), and the run record lists the forcing as an ADR-0003 intervention. The critter `[C]` is scoped
  to the slot/percent/count draws from a given room seed and to the pool not being used, with the room seed taken from
  the log as a boundary oracle (ADR-0004). **Required case added to the remaining Phase 2:** a natural nightmare and a
  natural hell game (a character allowed into them, no forcing), whose regions `tools/monpool.py check` reproduces, so
  the nightmare/hell pool claims do not rest on forcing alone; with the classic game and the out-of-town MLV it waits on
  the owner's decision on the saves-directory swap.
- **2026-10-12 — Phases 1, 1b and partial Phase 2 reviewed (architect): accept with fixes F1–F2, applied (c1173b1).**
  Checked: `tools/monpool.py check workspace/merged/data/global/excel workspace/logs/monpool-*.log` reruns 1557/1557;
  no resync (the MPS game seed is asserted to be Init(N) after one step, the regions are predicted from it); r2 at
  0x00547D20 (`+0xD0` step, `+0x6D` read at 0x00547D66, `+0xEC`, call 0x005479C0), 0x005475E0 (cap 13, `mon` `+0x36` /
  `nmon` `+0x68`) and the logged return 0x00530DCF after the call at 0x00530DCA; `game.h` offsets consistent after the
  merge with save/0001. F1: the Nightmare/Hell `[C]`s rest on `MONPOOL_FORCE_DIFF`, a write to `+0x6D` at 0x00547D63
  just before the pool's only read; accepted as an ADR-0003 intervention for the pool build, stated in each bullet, and
  a natural Nightmare and Hell game is a required case of the rest of Phase 2. F2: the critter `[C]` takes each room
  seed from the log (ADR-0004 boundary oracle) and checks to the first creation; scoped so. Verdicts: no
  `contradicted`. Remaining Phase 2 (natural NM/Hell, classic, monster level outside town) needs a saves-directory swap,
  which the session's permissions refused: an owner decision. Phase 3 (spec) may start on the pool build; the monster
  level stays `[I]` in it until then.
- **2026-10-12 — Phase 3 landed (spec-writer).** [specs/monsters/README.md](../specs/monsters/README.md) (draft,
  C 4 / I 7 / L 1: the chain pool → spawn → special → stats, rows after the pool marked not started) and
  [specs/monsters/pool.md](../specs/monsters/pool.md) (draft, C 68 / I 26 / L 5). The region seed, build, pool pick,
  appearance sets, region layout and critter draws are `[C]` from run:2026-10-12-mon-pool, scoped as in F1–F2: each
  nightmare/hell `[C]` says the difficulty byte was forced at `0x00547D63` (ADR-0003 intervention), and the critter
  `[C]` names the room-seed boundary oracle (ADR-0004). The monster level (step E) and the classic branch stay `[I]`.
  Worked example: `-seed 1` normal (the unforced game), levels 1–3 with every draw on `R` (level 3 has four candidates
  for three picks and a duplicate-set redraw), reproduced by `python3 -I tools/monpool.py pool workspace/merged/data/global/excel --seed 1 --diff 0 --level 1 --level 2 --level 3`;
  plus a model-only monster level for `cr_lancer1` in level 3 (hell: 68 expansion, 67 classic), `[I]`. Glossary:
  mlvl (refined), monster region, monster pool, appearance set, critter. Open questions (5, all `[L]`): natural
  nightmare/hell pools, the monster level outside town, classic games, the MonStats2 doc, the critter-create draws;
  each is already a plan 0012 Phase 2 case or an existing backlog entry, so no new backlog entry to the reverser.
  Not done here: the reverser → spec-writer entry on `rng/seeds`' game-seed consumer order (a reviewed spec, left for
  its own pass). Next: architect review.
- **2026-10-12 — Phase 3 review fixes F1–F4 applied (spec-writer).** F1: level-2 table separator fixed. F2: B2
  (missing difficulty record), "`enabled` not tested" (the survey fact that no pool names a disabled class stays
  `[C]`), the leading-slots rule of the candidate count (Inputs bullet and reimplementation note; the load-time
  counts stay `[C]`) and the `raritySum` wrap (the u8 width stays `[C]`) go to `[I]`. Checks over the ten logs of
  run:2026-10-12-mon-pool with the `tools/monpool.py` model: **C6 exhaustion is exercised**: of 200 ranged first
  picks, 76 took no redraw and 42 used all 20 redraws without a ranged class and kept the last draw, all
  reproduced, so C6 stays `[C]` whole and the spec now says so. **F4 no-draw is exercised**: all 12 critter rooms
  whose slot passed `cpct` have `MinGrp` = `MaxGrp` (`chicken`, `bug`) and match at the first creation with no
  count draw, so that clause stays `[C]` (the `MinGrp` < `MaxGrp` case was not reached, stated). F3: the
  forced-byte scoping added to the overview's first `[C]`, pool.md § A and the "per game" reimplementation note.
  F4: tags recounted: pool.md C 66 / I 31 / L 5, README C 4 / I 7 / L 1.
- **2026-10-12 — Phase 3 reviewed (architect): accept with fixes F1–F4, applied (7aa1fc4).** Checked: the worked
  example reruns (`monpool.py pool … --seed 1 --diff 0 --level 1..3`: seeds after `6ac6935f:0000029a`,
  `d52ffc3b:270b4ee5`, `679fafd2:63e02d41`, equal to MPR lines of `monpool-1-normal.log`); r2 at 0x0054790D (the
  ranged redraw loop, unrolled 5×, bound 20), 0x00573E20 (`game+0x70` read before E4), 0x0046C460; gate green. F1:
  a table separator. F2: `[C]`s on paths no run exercised or could distinguish downgraded to `[I]` (B2 fatal error,
  `enabled` not tested, the leading-non-negative count rule, the `raritySum` wrap); the C6 exhaustion fallback (42
  of 200 first picks) and the F4 equal-group no-draw (12 rooms, `MinGrp` = `MaxGrp`) were exercised and stay `[C]`,
  `MinGrp` < `MaxGrp` stated as not reached. F3: the forced-difficulty scoping carried into the overview and the
  "per game" note. F4: tag counts. The monster level, the classic branch and the natural nightmare/hell pools stay
  `[I]`/open until Phase 2 rest lands; the spec then gets a tag pass. Note for Phase 2 rest: the recorded check glob
  `monpool-*.log` now also matches the new `monpool-p2-*` logs.
- **2026-10-12 — Phase 2 rest (reverser).** [run:2026-10-12-mon-pool-p2](../findings/monsters/experiments.md#run2026-10-12-mon-pool-p2):
  seven natural games (no `MONPOOL_FORCE_DIFF`, no memory write), `-seed 1`, test characters built by the new
  `tools/monpool_saves.py` from the samples and swapped in only through `tools/saves.py`; waypoint travel out of the
  camp (steps `tools/gdb/monpool-*.steps`). Expansion normal / nightmare / hell, classic nightmare / hell, a mercenary
  (271) and a Clay Golem (289, `noRatio`). `monpool: 1483/1483 match`; rerun:
  `python3 -I tools/monpool.py check workspace/merged/data/global/excel workspace/logs/monpool-p2-*.log`. The natural
  seed-1 nightmare and hell regions are identical to the forced ones of run:2026-10-12-mon-pool, and classic regions equal
  expansion ones apart from the copied `MonLvl` fields. Monster levels outside town separate the two sources in 61
  creations (Jail Level 1 classes 384/57, Stony Field class 6, the mercenary, the golem), all as the rule says.
  [monsters/0001](../findings/monsters/0001-level-pool.md): the monster level (§5) goes to `[C]` for those cases and
  `sub_00573CB0_MonStatsInit` to `C`; classic nightmare/hell column set `[C]`; the F1 forced-difficulty scoping stays on
  the run:2026-10-12-mon-pool bullets, now next to the natural evidence. Still `[I]`: the `boss` exception, hirelings other
  than 271, classic normal. The old run's rerun glob `monpool-*.log` now also matches the -p2 logs; its record now uses
  `monpool-[1-5]-*.log` (1557/1557 unchanged); the plan entries above keep the old text. Also: `tools/ghidra.sh`
  `GHIDRA_PROJ_DIR` override (no Ghidra call was needed in this phase).
- **2026-10-12 — Phase 2 rest reviewed (architect): accept; Phase 2 done.** Checked: `monpool.py check … monpool-p2-*.log`
  reruns 1483/1483 and the narrowed glob `monpool-[1-5]-*.log` still gives 1557/1557; every `-p2` MPS line has
  `forced:null`, the game-seed draw asserted from N, and `exp` 0 in the two classic games, 1 elsewhere; the MLV check
  predicts the level and `d` from class, level id, difficulty and game type (no seed or level taken from the log);
  r2 at `0x0063EE90` (unit type 1, classes 359, 271, 338…), `0x00573E20`/`0x00573E28` (`game+0x70` gate, `d > 0`) and
  the join `0x00573E56` where MLV logs `d`; gate green. The `[C]` of §5 is scoped to the logged cases that tell the
  two sources apart; `boss`, the other four hirelings, classic normal and the no-record fallback stay `[I]`. The test
  characters are header edits on copies (ADR-0003 input, recorded); run 6 was finished by the lane driving `xdrive`
  interactively, every click recorded; no memory write, no oracle. The forced-difficulty scoping stays on the
  run:2026-10-12-mon-pool bullets, with the natural evidence beside it. Remaining for the plan: the spec tag pass
  (backlog, architect → spec-writer). A `boss` creation needs play and is left open, not a blocker.
- **2026-10-12 — Phase 3 tag pass after Phase 2 rest (spec-writer).** [specs/monsters/pool.md](../specs/monsters/pool.md)
  C 75 / I 28 / L 5 (was 66 / 31 / 5) and [specs/monsters/README.md](../specs/monsters/README.md) C 6 / I 5 / L 1
  (was 4 / 7 / 1), citing [run:2026-10-12-mon-pool-p2](../findings/monsters/experiments.md#run2026-10-12-mon-pool-p2).
  Raised to `[C]`: the `MonsterInit → MonStatsInit` entry rows (both files), step E's header, E2 (hireling 271 gets
  `d` = 0) and E4 (`expansion`, `d > 0`, `noRatio`), the bullet for expansion nightmare/hell `MonLvlEx` and the
  classic and normal MonStats levels (61 separating creations), the classic `MonLvl1..3` not being read, the
  hireling and `MonLvl1..3` reimplementation notes, C1 classic nightmare/hell column set, and B4's `monLvl` copy as
  written in both arms; the overview's monster-level bullet. The forced-difficulty caveats (A, C1, C8 723, the
  "per game" note, the overview) now state the natural seed-1 games beside the forced run. Kept `[I]`: `boss` (its
  own pseudocode line), hirelings 338/359/560/561, classic normal (pool and level), the no-record `1` fallback,
  `+0x2DC` unread. Worked example: a logged monster-level table for *Jail Level 1* classes 384/57 (41/71
  expansion, 40/70 classic, Stony Field class 6 for normal); the `cr_lancer1` table is marked model-only. Open
  questions (3, `[L]`): `boss` creation (needs play), the other unlogged step-E paths, more seeds/acts for the
  natural nightmare/hell regions. Glossary mlvl unchanged (already states the rule). Next: architect review.

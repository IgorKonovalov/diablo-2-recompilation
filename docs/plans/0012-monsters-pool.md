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

# 0014 — Monsters: random population of a room (density, class pick, packs, minions, placement)

> **Status:** in-progress (approved 2026-10-12; Phase 0 started 2026-10-12)
> **Created:** 2026-10-12
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only

## TL;DR

**Question:** when a server room becomes active, how does the game decide how many monster groups it gets, which
class each group is, whether a group is normal, champion or unique, how many monsters (and minions) it holds, and
where they stand? [monsters/pool](../specs/monsters/pool.md) (reviewed) gives the per-level region the population pass
picks from; this plan reads the pass itself (`sub_0054EC90_RoomPopulate` and its callees), models it in
`tools/monspawn.py` from the active-room seed, and checks the model against logged populations. When it's done,
`docs/findings/monsters/0002-room-population.md` has the pass at `[C]` for the logged cases and
`docs/specs/monsters/spawn.md` is drafted. Champion/unique **modifiers**, names and superuniques stay with
`monsters/special`; hit points and damage with `monsters/stats`.

## Context

- Research-map row `monsters/spawn` (core), `not started`. Dependencies: `rng` reviewed; `monsters/pool` reviewed (the
  region: `nPool`, `raritySum`, entries, `monDen`, `monUMin`/`monUMax`, `monWndr`); `drlg/overview` reviewed, which
  makes the active-room seed (`+0x6C`, `rng/seeds` step 6 with the k of plan 0008) reproducible from the map seed.
  `drlg/collision` is **not started**: where a monster may stand depends on the room's collision grid, so placement
  positions use a boundary oracle (ADR-0004) on the collision side unless Phase 1 finds the test simple enough to read
  in scope. Choosing the boundary is the Phase 1 decision recorded below.
- Code already named, all `[I]` from [monsters/0001 §6](../findings/monsters/0001-level-pool.md#6-who-reads-the-pool-named-for-monstersspawn):
  `sub_0054EC90_RoomPopulate` (steps the active-room seed once, `rng/seeds` step 6), `sub_0054EBC0_RoomPopulateGate`
  (`monDen` ≠ 0), `sub_005BDE80_MonRegionPickClass` (`RangeB(roomSeed, raritySum) + 1` over the entries, the
  `spawn`/`placespawn` substitution at `% 100 > 20`, `umon` for normal-difficulty uniques), `sub_005BE020_SpawnTypeRoll`
  (normal/champion/unique from `MonUMin`/`MonUMax` and region counters), `sub_00574250_MonsterInit`,
  `sub_00547BC0_MonRegionFindAdd`. `rng/seeds` lists the server population pass as an open `[L]` (no run reached it).
- Data: [Levels](../tables/Levels.md) (`MonDen`, `MonUMin/Max`, `MonWndr`, `MonSpcWalk`), [MonStats](../tables/MonStats.md)
  layout complete (`MinGrp`/`MaxGrp`, `PartyMin`/`PartyMax`, `minion1/2`, `spawn`/`spawnx`/`spawny`/`spawnmode`,
  `placespawn`, `SetBoss`…, meanings mostly `[L]`), [SuperUniques](../tables/SuperUniques.md). No doc yet for
  `monplace`, `monpreset`, `monumod` (special) or `MonStats2` (in progress on the archivist backlog).
- Harness: ADR-0003; `tools/monpool.py` + `tools/gdb/mon-pool.gdb` and the natural nightmare/hell and classic test
  characters of run:2026-10-12-mon-pool-p2 (`tools/monpool_saves.py`) are reusable; `tools/drlg.py` reproduces room
  seeds. Population happens only in rooms that become active near a player, so runs log the rooms around a waypoint
  arrival or a game start: no walking needed for the core cases.
- Leads: none registered for spawning. Phase 1b fetches one (ADR-0007).

## Phases

### Phase 0 — Spawn tables and columns
- **Owner skill:** archivist
- **What:** document the tables and columns the population pass reads, with meaning columns where the data alone
  settles them.
- **Outputs:** `docs/tables/MonPlace.md` and `docs/tables/MonPreset.md` (new, with layouts in `tools/excel_layouts.py`);
  [MonStats](../tables/MonStats.md) *Spawn columns* section (`MinGrp`/`MaxGrp`, `PartyMin`/`PartyMax`, `minion1/2`,
  `spawn`, `spawnx`, `spawny`, `spawnmode`, `placespawn`, `SetBoss`, `BossXfer`, `isMelee`, `npc`, `inTown`, `Align`
  and any group/AI-placement flag in the layout); [Levels](../tables/Levels.md) `MonDen`/`MonWndr`/`MonSpcWalk`
  survey per difficulty.
- **Done when:** `excel_bin.py diff` reports 0 mismatches for `monplace` and `monpreset`; a survey (extend
  `tools/mon_survey.py`) lists per difficulty: levels with `MonDen` 0, the `MinGrp`/`MaxGrp` and `PartyMin`/`PartyMax`
  ranges over pool classes, how many pool classes have `minion1`, `spawn` or `placespawn`, and the `MonUMin`/`MonUMax`
  pairs in use.

### Phase 1 — Read the population pass
- **Owner skill:** reverser
- **What:** read `sub_0054EC90_RoomPopulate` and its callees down to monster creation, and decide the collision boundary.
- **Outputs:** `docs/findings/monsters/0002-room-population.md`, `re/symbols.csv` rows (subsystem `monsters/spawn`),
  struct fields in `re/types/` (room population state, region counters).
- **Done when:** the finding states, with addresses and `[I]` or better:
  - when the pass runs (room activation, bit 0 of the room flags, server only), which seed each draw uses (active-room
    seed, unit seed, game seed) and its order relative to `rng/seeds` step 6;
  - density: how `monDen` (per difficulty) and the room's size or tile count become the number of groups or
    attempts, with integer widths and rounding;
  - the class pick (`MonRegionPickClass`) in full, the `spawn`/`placespawn` substitution, and how often it is
    called per group;
  - the type roll (`SpawnTypeRoll`): normal / champion / unique, the region counters it reads and writes, `MonUMin`/
    `MonUMax`, and where the champion/unique **count** per level comes from; the mod and name rolls named only for
    `monsters/special`;
  - group size: `MinGrp`/`MaxGrp`, `PartyMin`/`PartyMax`, player count if read, and minions (`minion1/2`, count,
    which class);
  - placement: how a position is chosen in the room (draws, tries, spacing between group members), what the
    collision test is called with and returns; **the boundary decision**: read the collision test in scope, or log
    its result and treat it as an ADR-0004 oracle in Phase 2 (stated either way);
  - wanderers (`MonWndr`) and `MonSpcWalk`: what reads them, named or read;
  - preset monsters from DS1 units and `monpreset`, and superunique placement: named only, with the boundary to
    `monsters/special` and `drlg/preset`;
  - classic vs expansion and difficulty branches anywhere in the pass.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch and register at least one community source on monster density, pack size, champion/unique counts
  and minions, then compare per `evidence-rules.md` § Community cross-checks (blind first; agreement never promotes).
- **Outputs:** `docs/sources.md` entry, verdicts in the finding's *Leads used*, backlog entries for `contradicted`.
- **Done when:** density, the class pick, the type roll (with the per-level unique count), group size and minions each
  carry a verdict with a `src:` id (or `not covered`); every `contradicted` claim is a required case of Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (a human may play, as in plan 0004)
- **What:** write `tools/monspawn.py` (tables through `tools/excel_bin.py`, regions through `tools/monpool.py`, room
  seeds through `tools/drlg.py`, draws through `tools/rng.py`) that predicts each populated room from its seed, and
  check it against logged populations.
- **Logging:** `tools/gdb/mon-spawn.gdb`: per populated room, the room id and level, the seed at entry and exit, every
  group (class, type, size, minions) and every monster created (class, position, unit id); the collision test's
  arguments and result if Phase 1 chose the oracle.
- **Done when:** a run `run:YYYY-MM-DD-mon-spawn` reproduces, with the room seed **predicted** from the map seed (not
  taken from the log) wherever `tools/drlg.py` covers the room, and any oracle stated:
  - at least 100 populated rooms over at least two `-seed` values and at least four levels in different acts;
  - normal and a natural nightmare or hell game (test characters of run:2026-10-12-mon-pool-p2);
  - every group's class, type and size, every minion, and the room seed at exit;
  - positions, under the boundary decision of Phase 1;
  - at least one champion group and one unique group, one `spawn`/`placespawn` substitution if a pool offers it, and
    a level whose `monDen` gate is closed;
  - the Phase 1b cases.
  In-scope claims are promoted to `[C]` citing the run; the `rng/seeds` population-pass `[L]` is answered through the
  backlog to the spec-writer.

### Phase 3 — Spec: monsters/spawn
- **Owner skill:** spec-writer
- **What:** write `docs/specs/monsters/spawn.md` and update the chain in `docs/specs/monsters/README.md`.
- **Done when:** the spec follows the template, every statement is tagged, it includes a worked example from the run
  (room seed in, draws, groups and positions out), any collision oracle is stated where it applies, and the
  architect's review passes.

## Open questions

- Placement depends on `drlg/collision`, which is not started. If Phase 1 finds the collision test small (a flag
  lookup in the room grid built from DT1 sub-tile flags), it can be read here; otherwise this plan uses an oracle and a
  `drlg/collision` plan follows. Phase 1 recommends which.
- Player count (`/players`, party size) may scale group size or the champion/unique count; single-player runs give
  one value. A multiplayer case waits on plan 0011's harness.
- Is the champion/unique count per level fixed at level creation (region counters) or rolled per room? Phase 1.
- Act bosses, quest monsters and superuniques are placed by other code (presets, quests); named only.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-12 — Drafted (architect).** Next row of the monster chain after `monsters/pool` was reviewed (plan 0012
  closed). The population-pass functions named in monsters/0001 §6 are its starting point.
- **2026-10-12 — Approved (human).** No changes to the draft.
- **2026-10-12 — Phase 0 landed (archivist).** [MonPlace](../tables/MonPlace.md) and [MonPreset](../tables/MonPreset.md)
  are new, with layouts in `tools/excel_layouts.py`: `excel_bin.py diff` reports 0 mismatches for `monplace` (37 cells)
  and `monpreset` (687 cells); the `excel_layout` gate baseline moved 28 → 30 tables. MonPreset `Place` compiles
  to a kind byte (0 MonPlace, 1 MonStats, 2 SuperUniques) and a row index, which matches the DS1 reader of
  drlg/0001 (`[I]` there; 2 672 of 2 676 DS1 `type` 1 ids fall inside their act's list). MonPlace is a list of
  names whose record is its own index, loaded only under `-txt`. [MonStats § Spawn columns](../tables/MonStats.md#spawn-columns-plan-0014-phase-0)
  and [Levels § Spawn survey](../tables/Levels.md#spawn-survey-per-difficulty-plan-0014-phase-0) cover the
  population-pass inputs; `python3 -I tools/mon_survey.py spawn <excel-dir>` prints them per difficulty. Key numbers
  (normal / nightmare / hell): `MonDen` 0 on 13 / 12 / 12 levels (*Siege 1* normal only); pool classes 240 / 342 /
  342 with `MinGrp` 1..7, `MaxGrp` 1..10, `PartyMin` 0..4, `PartyMax` 0..8; `minion1` 36 / 55 / 55, `spawn`
  12 / 15 / 15, `placespawn` 3 (`crownest1..3`); 6 / 11 / 18 distinct `MonUMin`/`MonUMax` pairs, never min > max.
  `MonWndr` is 1 on 113 levels, `MonSpcWalk` non-zero on 10 (values 1 and 5). Meanings stay `[L]` except
  where monsters/0001 anchors them (critter `MinGrp`/`MaxGrp` `[C]`, the `spawn`/`placespawn` substitution `[I]`).
  Surprises: in the pools `PartyMax` > 0 exactly when `minion1` is set; `minion1` is the class itself for 22 pool
  classes (fallen, fetish, scarab); three MonPlace keywords are named by no MonPreset row. `mon_survey` has no gate
  baseline (not registered), so none was changed.
- **2026-10-12 — Phase 0 reviewed (architect).** Verdict: **accept**. Checked: `excel_bin.py diff` rerun, `monplace`
  37 cells and `monpreset` 687 cells, 0 mismatches; `mon_survey.py spawn` rerun (`MonDen` 0 on 13/12/12 levels,
  240/342/342 pool classes); the table docs describe columns with short examples, no dumps; meanings the data can't
  settle stay `[L]`, and the DS1-reader meaning of `monpreset` is `[I]` from drlg/0001. Phase 1 (reverser) is next and
  inherits the archivist's backlog entries (group size and minion columns, `SetBoss`/`BossXfer`, `spawnx/y/mode`,
  `MonWndr`/`MonSpcWalk`, the (0,0) `MonUMin`/`MonUMax` pair, preset monsters per MonPreset range).

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
- **2026-10-13 — Phase 1 landed (reverser).** [monsters/0002](../findings/monsters/0002-room-population.md), all `[I]`
  from static reading (one `[C]` by data: the `umon` exit is never reached in stock data); 46 `monsters/spawn` rows in
  `re/symbols.csv`; `re/types/monspawn.h` (`SpawnBox`, `SpawnBoxes`, `MonSpawnReq`) and `monregion.h` `+0x2C4`/`+0x2C8`
  renamed. Answers per Done-when bullet: **when**: `sub_0052D160_NewRoomsUpdate` runs a wanderer tick (one room draw) on
  every room of a new-rooms walk, then, while room flag bit 0 is clear, presets → inactive units → objects →
  `RoomPopulate` → set bit 0; **seeds**: density and `sparsePopulate` from the game seed, class picks / type roll /
  positions from the active-room seed (after the tick, preset and object draws), group size, champion-or-unique and minion
  counts from unit seeds; **density**: per spawn box `(5h/3)·(5w/3)` attempts (i32, truncating), each passes iff
  `game draw mod 100000 ≤ min(monDen, 10000)`; **class pick**: `RangeB(raritySum)+1` walk, `placespawn` substitution
  `% 100 > 20` (0 for specials), `umon` for normal-difficulty specials, called once per attempt plus once more for a
  special; **type roll**: special iff (below `MonUMin` and `r < 100·visited/rooms`) or (below `MonUMax` and `r < 6`),
  else normal: its 1 is folded into 2, so the champion branch `0x0054EEE4` is dead; champion vs unique comes later from the
  boss's unit seed (`Range(100) <` MonUMod rec 0 `+0x1C`); the count is the live per-level special counter `+0x2C8`
  (low byte compared), not fixed at level creation; **group size**: `MinGrp..MaxGrp` (1/1 for fallen/scarab) from the
  leader's seed, members in rings 3–9; every normal-group member (leader included) gets `PartyMin..PartyMax` minions (`minion1`/`minion2`
  alternating); uniques 3..6 minions, champions 1..3 pack members; no player-count read found; **placement**:
  `MonSpawnTry` rings of 3·k with 3 room draws + one `RangeB` per ring, box/region/class-cell/collision tests;
  **boundary decision: oracle** (the test is read, its grid is `drlg/collision` and changes with every placed unit; logged
  as a value oracle, § 9 has the breakpoint list); **MonWndr**: wanderer tick `0x0054F060` (1/32768 · 3/100, cap 3,
  Act I class 270 only); **MonSpcWalk**: pathing helper `0x005B13E0` only; **presets/superuniques**: named
  (`0x005559A0`, `0x0054E600`, `0x005A49B0`); **classic/expansion**: no expansion branch in the pass, difficulty via the
  region values, `umon` and the special mods. Backlog: archivist's Phase 0 column entry struck, the MonPreset entry
  narrowed; new entries to the spec-writer (rng/seeds note 6 correction), the archivist (table links, MonUMod doc,
  `spawnCol` survey) and the architect (value-oracle reading of ADR-0004, `drlg/collision`). Phase 2 needs the
  owner's game: no runs were made.
- **2026-10-13 — Phase 1 reviewed (architect).** Verdict: **accept**. r2: 0x0054ED55 is the `/3` of the attempt count
  (`imul 0x55555556`), 0x0054EE0B folds type 1 into 2 (the champion branch at 0x0054EEE4 is dead), 0x005A0817 reads
  MonUMod record 0 `+0x1C`; the one `[C]` (every level with normal `MonDen` ≠ 0 has `umon1`) rechecked over
  levels.txt. **Boundary decision confirmed:** the collision test, the box-id, warp-distance and class-cell
  predicates and the room-seed consumers before the pass are ADR-0004 boundary oracles in Phase 2. For a callee that
  shares no seed the mandatory entry-state assertion becomes: log the active-room and game seeds on entry and exit of
  every oracle call and assert they are unchanged (a call that draws breaks the run), plus assert the arguments the
  model predicts. The record names each oracle, and `[C]` claims list the ones they depend on. `drlg/collision`
  gets its own plan after Phase 2, which re-runs these logs with the oracle replaced. Phase 1b (community
  cross-check) is next for the reverser, then Phase 2 runs. Note for 1b/2: no player-count read was found, so
  "/players" or party scaling of groups, which community sources may claim, needs a required case if contradicted.
- **2026-10-13 — Phase 1b landed (reverser).** Two sources fetched and read after the finding was written (blind first),
  registered in `docs/sources.md`: `src:d2dfg-blizzard` (re-fetched: § Levels.txt, § monstats.txt, § MonUMod.txt; no game
  version stated) and the new `src:arreat-summit-bonuses` (Blizzard's Arreat Summit "Monster Bonuses", LoD 1.13 or later).
  Neither page has code. Verdicts in [monsters/0002 § Leads used](../findings/monsters/0002-room-population.md#leads-used), per
  Done-when claim: **density** `MonDen` held with refinement (per attempt, not per room); **class pick** `Rarity` and `umon`
  held with refinement, the `spawn`/`placespawn` substitution not covered; **type roll** `MonUMin` held with refinement (not a
  guarantee), `MonUMax` **contradicted** (the page's "each room … 5/100" vs the code's per-attempt 6/100, `cmp ecx, 5; jle` at
  `0x005BE0DB` re-read, and a cap on the live special count rather than on successful rolls), champion 20 % held with
  refinement (MonUMod row 0 `constants` = 20, now `[C]` by data, 43/43 rows: `+0x1C` is that column); **group size**
  `MinGrp`/`MaxGrp` held with refinement, champion packs 2–4 held, `sparsePopulate` **contradicted** (the code spawns the group
  with probability `(v+1)/100` and puts nothing in its place, `0x0054EE8C` re-read); **minions** `PartyMin`/`PartyMax`, the
  unique 3–6 and the champion-minion classes held with refinement; **player count** not covered by either source. Also
  `MonWndr`'s `wanderingmon.txt` contradicted as a version difference (no such table in 1.14d; the class list is at
  `0x00731B2C`), settled by data and code. Both re-reads kept their `[I]` readings, so nothing was demoted. One complication:
  `evilhut`, the only class with `sparsePopulate`, is in no level pool and no `spawn` target (`[C]` by data), so stock data
  never reaches that roll and the Phase 2 case needs modified data, or the architect's ruling. Backlog: one entry with the
  Phase 2 required cases. Folded in the open reverser → reverser entry from plan 0016: the three `0x800000` writers (§ 2,
  with 22 flag sets on 22 distinct rooms and 16 `RoomPopLevelId` calls, 8 populated rooms × 2), the two-pass
  `RoomPresetUnits` walk (§ 7, `[C]`), and the logic-region renames with their citation sweep (`SpawnBox` → `LogicBox`,
  `SpawnBoxes` → `LogicRecord`, four `sub_` names; drlg/0004 and specs/drlg/preset changed in names only). The Ghidra
  project was not re-imported. The gate is green. Handing Phase 1b to the architect for review.
- **2026-10-13 — Phase 1b reviewed (architect).** Verdict: **accept with fixes**. Every Done-when claim (density, class
  pick, type roll with the per-level count, group size, minions, and player count) has a verdict and a `src:` id. Both
  sources were read blind-first and have no code. No tag was raised on agreement. Checked in r2: `0x005BE0DB` `cmp ecx, 5;
  jle` → `0x005BE097` (`xor eax, eax`, special), so the chance is 6/100. `0x0054EE81`–`0x0054EE8C` is a game-seed `mod 100`
  against the MonStats byte `+0x31`, and `jg` goes to `0x0054EEB2`, the attempt-loop decrement, so a failed roll creates
  neither a leader nor minions. `0x0054ECE2` is the `MonDen` clamp to 10000. `0x005A0817` reads MonUMod `+0x1C`, then
  `Range(100)` and `jge`. By data: MonUMod row 0 `constants` = 20, and `evilhut` is the only class with `sparsePopulate`
  (40), is in no `mon`/`nmon`/`umon` column and is no `spawn` target. The rename sweep leaves no live `SpawnBox*` name.
  Only historical log and backlog text keep the old names. The touch to specs/drlg/preset (one table cell, a renamed
  function, no content) is accepted as a names-only citation sweep. The gate is green.
  - **Fixes** (reverser; small, can land at the start of Phase 2 and be checked at its review):
    F1. § 2: the `[C]` bullet says "Three writers set `0x800000`" but proves two. Make it "two of the three writers",
    and leave the third to its `[I]` bullet.
    F2. § 5: scope the `[C]` to the data, meaning MonUMod `+0x1C` is the `constants` column, and row 0 holds 20 on 43/43
    rows. That the value *is* the champion chance (`Range(boss.seed, 100) < 20` at `0x005A0817`) stays `[I]` until
    Phase 2 logs a special's mod roll.
    F3. `sparsePopulate`, carried as an Open question (ruling below): edit the backlog entry and § 5 to match.
    F4. Take the two extra sources (ruling below).
    F5. Search statically for every reader of Levels `+0x2E` (`MonWndr`) and of the region's copy of it, then
    confirm or correct "read only by the wanderer gate" in § 7.
  - **Ruling, `sparsePopulate`:** this is **not a required case of Phase 2**. A run on modified data would not break
    ADR-0003, because the binary and process image stay unmodified and only the input changes. Plan 0005 accepted
    `-direct -txt` saves with edited tables on the same grounds. Still, the deliverable is stock 1.14d, and stock data
    never reaches this branch (`[C]` by data). The r2 re-read is one comparison with a clear sense, so it stays `[I]`.
    A re-read of the same code is not a second code path, so the contradiction is not settled. The spec states the
    branch `[I]` and states that stock data never reaches it (`[C]`), and it lists the community contradiction (the
    group spawns with `(v+1)/100`, nothing replaces it, and no minions are left) under *Open questions*, so a
    reimplementer for modded data knows the claim is untested. That satisfies the review rule. If the owner session
    has time, an opportunistic `-direct -txt` run with one Levels row edited to put `evilhut` in a pool can raise it
    to `[C]`. Its record must name the edit, and no stock-data claim may cite it.
  - **Ruling, the second session's sources:** take both, in the fix pass. Under ADR-0007 the fixing session
    **re-fetches and reads** each page itself. It can't cite the uncommitted session's reading. Update the two
    `docs/sources.md` rows ("re-fetched 2026-10-13, plan 0014 Phase 1b", sections used) and add these verdicts to
    *Leads used*: `src:pk-monstats-guide` `sparsePopulate`, where "overall chance something will spawn" is held with
    refinement and "a failure can leave only the minions" is contradicted and goes to the same Open question;
    `PartyMin`/`PartyMax` held; `minion1/2` for unique minions held with refinement (`minion1`, else the boss's
    class, and `minion2` unused on that path). From `src:rpgkdh-levels-guide`: `MonUMin`/`MonUMax` count champions
    and uniques, held with refinement; `MonDen` above 10000, held with refinement (clamped and written back at
    `0x0054ECE2`; stock maximum 2200). `MonWndr` "roam or stand put" stays **not covered / gap** until F5 decides
    between contradicted and held. It is a branch the docs describe that the finding may omit, and
    evidence-rules § Community cross-checks says to chase it. If d2dfg is quoted again, quote checks use the raw
    HTML, because fetch summaries drop sentences.
  - **Phase 2 required cases** are now `MonUMax` (asserting `≤ 5` on every logged type roll is enough if no roll
    lands on `r = 5`) and the `+0x2C8` count across a champion pack, plus F5's outcome if it finds a second reader.
    Everything else stays as the plan's Done-when.
  - **Next:** the reverser, with the owner (human) playing, runs **Phase 2**. F1–F5 come first in the same session.
    F5 is static and may add a logging point to `tools/gdb/mon-spawn.gdb`. The opportunistic `sparsePopulate` run is
    optional. The review of Phase 2 checks F1–F5.
- **2026-10-13 — Phase 2 landed (reverser, owner playing).** Fixes first: F1 (§ 2 "two of the three writers"), F2 (§ 5 data
  `[C]` split from its use), F3 (`sparsePopulate` under *Open questions*), F4 (`src:pk-monstats-guide` and
  `src:rpgkdh-levels-guide` re-fetched and read as raw HTML in this session; sources.md rows and seven verdicts), F5 (static:
  Levels `+0x2E` is read only by the region build `0x00547A99` and the wanderer tick `0x0054F0AA`; the region copy `+0x2BE`
  has no reader; rpgkdh's "roam or stand put" **contradicted**, then watched at run time). Tools: `tools/gdb/mon-spawn.gdb`
  (sources drlg-gen.py, drlg-roomk.py and the new `mon-spawn.py`), `tools/monspawn.py` (model and checker; runs `tools/drlg.py`
  gen and roomk and `tools/monpool.py` on the same log), two inert recording hooks in `tools/drlg.py`, the test-character
  recipe `tools/d2s_recipes/novasorc.json`. [run:2026-10-13-mon-spawn](../findings/monsters/experiments.md#run2026-10-13-mon-spawn):
  three owner-played games, **110 302 checks, 0 mismatches**: 516 rooms with the seed predicted from `-seed` (12345, 1),
  normal and hell, levels in Acts I–V, 169 populated rooms, 37 closed `MonDen` gates, 916 creations with their positions, 4
  champion packs and 20 unique groups, 19 crow-nest substitution rolls, 252 `MonUMax` draws (one special at `r = 5`), the
  special count `+0x2C8` checked across every pack member, the champion chance (MonUMod row 0, 20) on 24 rolls, `MonWndr`
  watched on five levels (region-build read only). Oracles named in monsters/0002 § 9. One correction found by the run:
  `ChampionMemberMark` calls `SpecialModsApply` on each pack member (§ 5). In-scope claims of §§ 1–7 promoted to `[C]`;
  22 `re/symbols.csv` rows to `C`. Not reached: `sparsePopulate`, spawnCol-1 placement, tentaclehead minions, the wanderer
  roll; no nightmare or classic game. Backlog: the fix and case entries closed; new entries to the architect (review), the
  spec-writer (`rng/seeds` population pass, Phase 3 inputs) and the archivist (Levels `+0x035`, MonUMod). Handing Phase 2
  to the architect for review.
- **2026-10-13 — Phase 2 reviewed (architect).** Verdict: **accept with fixes**. Rerun: `python3 -I tools/monspawn.py check`
  on the three logs prints **110 302 checks, 0 mismatches** with the counts of the run record. The sha256 of the three logs,
  `tools/gdb/mon-spawn.py` (`6ad436e8…a2438352`: the parallel session's overwrite is not what is committed), `mon-spawn.gdb`,
  `tools/monspawn.py` and `novasorc.json` match the record. The tree was clean. The `tools/drlg.py` hooks only append to
  lists the checker sets, and gen/roomk stay at 0 mismatches. Done-when: met. There are 169 populated rooms (≥ 100), seeds
  12345 and 1, 12 levels in all five acts, normal and hell (the plan asks for nightmare **or** hell), 4 champion packs and
  20 unique groups, 14 substitutions taken and 5 kept, 37 closed gates, positions under the Phase 1 oracle, and the
  Phase 1b cases (`MonUMax` at `r = 5`, `+0x2C8` across every pack member, the `MonWndr` watch). F1–F5 were checked, and
  all landed (backlog entry). In r2: `0x005BE0DB` `cmp ecx, 5; jle`; `0x005A0817` `+0x1C`, `Range(100)`, `jge`; the
  `ChampionMemberMark` body `0x005A48C0`–`0x005A4935`.
  - **ChampionMemberMark is adequately anchored.** The `call 0x005A2120` at `0x005A492C` is in the body (args `EAX`=`ECX`=`EDX`=0,
    `push 1`). The run shows the mod-handler window inside each of the 6 pack-member creations, with room and game seed
    unchanged. That gives two sources, code and run, and the checker change turned the window into a seed oracle; it fitted
    no number. Same for the `umon` count at Levels `+0x35`: it comes from data and the existing `mon`/`nmon` rule.
    The pseudocode needs one correction (F9).
  - **Oracle list accepted.** `SUnitCreate`: the game-seed step is predicted and the unit seed is taken. That is the
    boundary to `monsters/stats`, and the spec states the unit seed as an input, not as "Init + 2". The special mods
    after the champion roll and the mod handlers of bosses and pack members are `monsters/special` and are taken. The gate's
    DRLG parts and the logic-box list are DRLG state, taken. The game seed at pass entry is run-time state, taken. Every
    draw inside the pass is predicted. One scope correction, F7: the presets / inactive-restore / objects window is a
    seed oracle, so the room seed **at pass entry** is predicted end to end only where that window draws nothing. A
    scan of RW1 vs RW4 counts 176 of 516 rooms like that, and about 11 of the 169 populated rooms. The `[C]` claims
    stand, because every in-pass draw is predicted from the entry seed and the window is named. But "every room seed
    predicted from the `-seed` value" overstates what was predicted.
  - **Coverage limits accepted.** No nightmare game: difficulty enters only through region values, `umon` (normal) and the
    threshold-0 special pick, and hell takes the non-normal path. No classic game: § 8 finds no expansion branch, and it
    stays `[I]`. The unreached branches (`sparsePopulate`, spawnCol-1 tiles, tentaclehead minions, the evilhut object, the
    no-record exit, the wanderer roll and the tick's `0x0054F0AA` read) stay `[I]` and go to the spec as `[I]`. The test
    characters are tool-built and reproducible, and the aborted session-2 log is excluded and named.
  - **Fixes** (reverser). F6–F10 land before Phase 3. F11 lands before the plan closes.
    F6. § 5: the `[C]` bullet "That value is the champion chance" still says "no run has logged a special's mod roll yet".
    Replace that with the 24 logged rolls (champion iff `r < 20`).
    F7. Seed scope: have the checker count the rooms, and the populated rooms, whose pass-entry room seed is predicted end to
    end (no draw between RW1 and RW4). Print both, and state them in the Answer's reproduction bullet, the run record's
    *Observed* and *Oracles*, and the spec-writer backlog entry. Where those now say "every room seed predicted", say
    "predicted through the wanderer tick; at pass entry taken after the presets/objects window, end to end in N rooms".
    F8. Per-branch tags. The § 5 normal block and the § 6 `MonSpawnTry` block are tagged `[C]` as a whole but contain
    branches the run never reached: the `sparsePopulate` roll, the evilhut object 562, `SpawnPosOnTile` (spawnCol 1), the
    tentaclehead branch of `MinionsSpawn` (in a `[C]` bullet), and the `R.flags & 0x80` bypass and the `x = 0 or y = 0`
    exit unless the log shows them. Tag those lines `[I]` inline.
    F9. `ChampionMemberMark`: `0x005A4911 cmp eax, 9; jge 0x005A4931` skips **both** the mod append and the
    `SpecialModsApply` call. Write it as `if mods < 9: append mod; SpecialModsApply(…)`. The mod value is the caller's
    argument (`push 0x10` at `0x0054E246`), not a constant of the callee.
    F10. Unit seed: the spec-writer backlog entry calls the "+2 steps" MonsterInit. The run shows only that the steps
    happen inside `SUnitCreate`. Tag the attribution `[I]` or drop it. Name the two outlier creations (6 and 15 steps:
    class, level, log and line) in the run record, as a case for `monsters/stats`.
    F11. The finding's *Functions* table tags every row `I`, while 22 `re/symbols.csv` rows are now `C`. Sync the two
    (including `sub_0052D160_NewRoomsUpdate`, which § 1 tags `[C]`).
  - **Next: Phase 3 (spec-writer), after F6–F10.** `docs/specs/monsters/spawn.md` and the chain in
    `docs/specs/monsters/README.md`. Constraints for the draft:
    (a) An *Inputs and oracles* section that lists, as inputs, every oracle of monsters/0002 § 9: the room and game seed at
    pass entry, the logic boxes, the gate's DRLG parts, the four position predicates, the unit seed after `SUnitCreate`, and
    the special-mod and mod-handler windows. Each one names its owner (`drlg/collision`, `drlg/preset`, `objects`,
    `monsters/stats`, `monsters/special`).
    (b) The worked example is a populated room whose pass-entry seed is predicted end to end (one of F7's rooms), from
    `-seed` to positions, with the draw sequence.
    (c) The unreached branches are `[I]` per F8. `sparsePopulate` is `[I]` with "stock data never reaches it" `[C]`,
    and the three community contradictions (`sparsePopulate` sense and replacement, `MonUMax`, `MonWndr`) are stated, the
    unsettled one under *Open questions*.
    (d) The 1 → 2 fold and the dead champion branch are stated, so nobody implements a type-1 champion.
    (e) The `rng/seeds` population-pass `[L]` is answered in the same pass (backlog entry from the reverser).
    After Phase 3, the architect drafts the `drlg/collision` plan that replaces the position oracles (Phase 1 review).
- **2026-10-13 — Phase 2 review fixes F6–F11 applied (reverser).** No run; `tools/monspawn.py` gained counters only
  (sha256 `e6b6b56f…febbfb543`), and the rerun on the three logs still prints **110 302 checks, 0 mismatches**.
  - F6. § 5: the champion-chance bullet cites the 24 logged rolls (champion iff `r < 20`; `r` = 0, 9, 4, 15).
  - F7. The checker counts rooms whose pass-entry room seed is predicted end to end (predicted from `-seed` and RW1 rs =
    RW4 rs): **176 of 516 rooms, 11 of 169 populated** (s1: 1, s2: 0, s3: 10), the architect's scan confirmed. The Answer,
    § 9's oracle table, the run record (*Observed*, a table of the 11 rooms, *Oracles*) and the spec-writer `rng/seeds`
    entry now say "predicted through the wanderer tick; at pass entry taken after the presets/objects window, end to end
    in 176 rooms (11 populated)".
  - F8. Inline `[I]` on the unreached lines of the § 5 normal block (`sparsePopulate`, evilhut object 562), the § 6
    `MonSpawnTry` block (`SpawnPosOnTile`, the `R.flags & 0x80` bypass, the `x = 0 or y = 0` exit) and the tentaclehead
    sentence. The checker counts the bypass and the exit: 0 and 0. No request inside a pass carries `0x80` (the 122
    `MT0` lines with it, sessions 2 and 3, are outside the pass windows).
  - F9. Re-read in r2: `0x005A4911 cmp eax, 9; jge 0x005A4931` skips both the append (`mov byte [eax+edi], cl`, the byte at
    `[ebp+8]`) and `call 0x005A2120`; `ChampionPack` pushes `0x10` at `0x0054E246`; the `UnitGetRoom` result is discarded.
    The pseudocode is now `ChampionMemberMark(u, mod)` with `if mods < 9: append mod; SpecialModsApply(…)`.
  - F10. The "+2 steps (MonsterInit)" attribution is `[I]` in § 6 and dropped from the spec-writer entry. The outliers are
    named in the run record: 6 steps on a `goatman1` unique boss (s1 line 4101, level 4) and 15 on a `fallen1` minion of a
    `fallenshaman1` (s3 line 10222, level 3), a case for `monsters/stats`.
  - F11. The *Functions* table tags follow `re/symbols.csv` (23 `C`). `sub_0052D160_NewRoomsUpdate` is `C` in both now
    (CSV evidence moved to monsters/0002, which holds the run that confirms it).
  - **Next:** Phase 3 (spec-writer), backlog entry. The architect may spot-check the fixes first.
- **2026-10-14 — Phase 3 landed (spec-writer).** [monsters/spawn](../specs/monsters/spawn.md), `status: draft`, tags
  {C: 94, I: 41, L: 6}, 8 Mermaid diagrams, from monsters/0002 after F6–F11 (commit `c8c86b9`). Sections A–K: room driver
  and the room seed before the pass, gate, density, class pick, type roll, normal group, special group (boss, champion
  roll, unique minions, champion pack, `ChampionMemberMark` as F9), placement (`SpawnPosPick`, `MonSpawnTry` ring walk),
  MonStats minions, creation and the unit seed, wanderers, and a draw-order diagram across the three seeds. Constraints:
  (a) *Inputs and oracles* lists every oracle of monsters/0002 § 9 with its owner (`drlg/preset`, `objects`,
  `monsters/special`, `drlg/room-tiles`, `drlg/collision`, `drlg/warps`, `monsters/stats`); the unit seed after
  `SUnitCreate` is an input (+2 steps on 914 of 916, 6 and 15 on two), and no callee is named; (b) worked example
  `monspawn-s3-1-hell-a1.log` line 21181 (`-seed 1`, hell, Dark Wood, room `0x03021700`, one of the 11 end-to-end rooms):
  `levelSeedBase` → DRLG room `+0x04` → k = 122 → active-room seed → tick → pass, three groups (quillrat2 × 3, × 1;
  fallen2 + 2 minions), every draw re-derived with `tools/rng.py` and matched to the log, including a ring walk that
  reverses at a corner and a density roll at exactly `r = monDen`; (c) the unreached branches inline `[I]`
  (`sparsePopulate`, evil hut object, `SpawnPosOnTile`, the `0x80` bypass, the `x = 0 or y = 0` exit, tentaclehead
  minions, the no-record exit, the wanderer roll); `sparsePopulate` `[I]` with "stock data never reaches it" `[C]`; the
  `MonUMax` and `MonWndr` contradictions stated in *Reimplementation notes*, the `sparsePopulate` one under *Open
  questions*; (d) step note E2 and the first reimplementation note state the 1 → 2 fold and the dead `0x0054EEE4`
  branch; (e) [rng/seeds](../specs/rng/seeds.md) step note 6 corrected and the population-pass `[L]` struck, step note
  7a gains the unit-seed input ({C: 55, I: 18, L: 6} → {C: 58, I: 17, L: 5}). [monsters/README](../specs/monsters/README.md):
  spawn.md row (`draft`), data-flow diagram (type roll = normal or special; champion or unique on the boss seed), three
  rows and one bullet `[I]` → `[C]`, one new row ({C: 6, I: 5, L: 1} → {C: 11, I: 1, L: 1}). Both edited specs were
  `reviewed` and keep that status pending this review. Glossary: population pass, logic box, special, champion pack,
  minions. Open questions: 6 (`sparsePopulate`, the unreached branches, the unit-seed steps, nightmare/classic/multiplayer,
  room `+0x78` and `0x0061A4D0`, the DRLG inputs). Backlog: the three spec-writer entries struck; new entries to the
  reverser (`MonSpawnTry` early exits that the checker has and § 6 does not state; not blocking) and to the architect
  (review). The gate is green. Status change for the research map (architect's): `monsters/spawn` → `draft`.
- **2026-10-14 — Phase 3 reviewed (architect).** Verdict: **accept with fixes** (FS1, FS2: inline tags only, to the
  spec-writer). Checked: the gate is green. `python3 -I tools/monspawn.py check workspace/logs/monspawn-s3-1-hell-a1.log -v`
  prints **29 853 checks, 0 mismatches**, and line 21181 is listed as `[('normal', 64, 3), ('normal', 64, 1), ('normal', 20, 1)]`.
  - **Worked example, re-derived independently** with `tools/rng.py` (scratch script, not committed). Inputs were `-seed 1`,
    the cited DRLG room `+0x04` `8E44259B` and k = 122. Every value matched the spec and the log's `P0`/`PA`/`PC`/`PT`/`SPW0`
    lines: `levelSeedBase` `6AC6935F`, `0A8F2A48:218010C7` after k, active-room seed `4D241A2F:0000029A`, the tick
    (`0x18C5`, no roll), the pick (4 → class 64), the type draws 51 and 24, the position (15557, 5612), the probe and
    create seeds, the game seed `590F86A4:45E87BD0`, the leader seed as `Init(game.low)` + 2 steps `D496D6A5:212B878A`, and
    `k` = 2. Not giving a room index is accepted: the room is pinned by its address and its predicted `+0x04`, and the
    index adds nothing a reimplementer needs.
  - **r2 spot checks** (pinned `game.exe`, sha256 matches the inventory): `0x0054EE08`–`0x0054EE0D` `cmp eax, 1; jne;
    mov eax, 2` (the fold); `0x0054EE1E` `je 0x0054EEE4` and `0x0054EEE6` `call 0x005BDFF0` (the dead branch);
    `0x0054EDF9` `je 0x0054EEDD` → `ret`, past the `+0x08` increment at `0x0054EED9` (no-record exit, `[I]` correctly);
    `0x005BE031`/`0x005BE037` byte compare of `+0x2C8` with `+0x2BC`, `jae` (low byte, unsigned); `0x0054E040`–`0x0054E04A`
    u8 `max − min + 1` (the group size range). All match the spec.
  - **Constraints.** (a) met. *Inputs and oracles* lists all eight oracle rows of monsters/0002 § 9, each with its owner,
    and the unit seed is an input with no callee named. (b) met. The room is one of the 11 end-to-end rooms, and the
    example runs from `-seed` to positions and includes a reversing ring walk and an `r = monDen` pass. (c) met, apart
    from FS1/FS2 below. The F8 lines are inline `[I]`; `sparsePopulate` is `[I]` and "stock data never reaches it" is
    `[C]` by data; `MonUMax` and `MonWndr` are settled in *Reimplementation notes* (by the `r = 5` run case, and by the static
    reader search plus the run watch); `sparsePopulate` is under *Open questions*. (d) met (E2 and the first
    reimplementation note). (e) met (rng/seeds note 6, the struck `[L]`, and note 7a).
  - **The edits to the two reviewed specs are accepted, and both keep `status: reviewed`.** monsters/README: the four
    `[I]` → `[C]` (the population bullet and three entry-point rows) each restate a `[C]` of spawn.md with the same
    anchors plus the run. The new champion-or-unique row rests on the 24 logged rolls. The data-flow diagram matches the
    text. rng/seeds: note 6 now attributes `0x005BDFF0` to the dead type-1 branch, which the r2 read above confirms; the
    population-pass `[L]` is struck with a pointer; the note 7a unit-seed sentence matches the run (914 / 916). Tag counts
    are as stated, and the gate checks them.
  - **F6–F11 spot-checked in monsters/0002.** F6 at line 484 (24 rolls, `r` = 0, 9, 4, 15). F7: 176 / 11 in the Answer, § 9
    and the run record. F8: inline `[I]` on `sparsePopulate`, object 562, `SpawnPosOnTile`, the `0x80` bypass, the
    `x = 0 or y = 0` exit and tentaclehead. F9: `if mods(u) < 9: append; SpecialModsApply` with the `push 0x10` caller.
    F10: the outliers at s1 line 4101 and s3 line 10222. F11: the *Functions* tags match `re/symbols.csv`, with no mismatch
    by script. All hold.
  - **Ruling on the H2 early exits:** they may **not** stay `[C]`. A branch the checker implements but that no logged
    call takes is the model agreeing with itself, not corroboration. It is the same rule as F8. The code is there.
    I read it in r2: `0x005B2A16` and `0x005B2A2A` (class outside `[0, nMonStats)`), `0x005B2A43` (null MonStats record),
    `0x005B2A66` and `0x005B2A72` (`MonStatsEx` outside the MonStats2 range), `0x005B2A8B` (null MonStats2 record), all
    → `0x005B2EFB`, and `0x005B2E46` (`SUnitCreate` returned null → `0x005B2EF2`). So they are `[I]` with those anchors.
    I found no null-room test in the prologue up to the mask switch. That exit stays out of the spec until the reverser's
    § 6 entry settles it.
  - **Fixes** (spec-writer; tag-level, no new evidence needed):
    FS1. spawn.md H2: tag inline `[I]` on the first line (`not a valid class or has no MonStats2 record`), with
    the anchors 0x005B2A16, 0x005B2A43, 0x005B2A72, 0x005B2A8B. Tag inline `[I]` on `if unit = none: return none`, with
    the anchor 0x005B2E46. Update the front-matter tags.
    FS2. The same rule for every other guard exit inside a `[C]` pseudocode block of §§ A–J. If the run, through the checker's
    counters or the log, shows the exit taken, keep it `[C]`. Otherwise tag it `[I]` inline. Known candidates: F2
    `min = 0 or max = 0 or max < min` (stock `MinGrp` ≥ 1), D1 `region.nPool = 0`, C1 `if none: return` for a room with
    no logic box, and B1 `region = none`. Record the outcome of each check in the fix entry.
    With FS1–FS2 in, the spec-writer sets spawn.md to `status: reviewed`. The architect checks the fix commit at close.
  - **Bookkeeping.** The research-map row `monsters/spawn` now reads draft, P3 accepted with fixes. The review backlog
    entry is struck, and the fix entry goes to the spec-writer. The reverser entry on § 6 stays open and is not blocking.
    The `drlg/collision` follow-up is drafted as
    [plan 0017](0017-drlg-collision.md) (status draft, waiting for the owner's approval). It replaces the four position
    value oracles and keeps the presets/objects window, the unit seed and the special-mod windows with their owners.
  - **Next:** spec-writer FS1–FS2, then the architect closes plan 0014 (status `done`, moved to `done/`). The owner
    approves or amends plan 0017.
- **2026-10-14 — FS1–FS2 applied (spec-writer).** [monsters/spawn](../specs/monsters/spawn.md) is set to
  `status: reviewed`, tags {C: 94, I: 41, L: 6} → {C: 94, I: 64, L: 6}. No `[C]` statement was demoted: 17 guard lines
  gained an inline `[I]`, and six block headers (B1, C1, D1, G2, G6, H1) now read "[C] except the lines tagged [I]".
  `tools/monspawn.py` gained counters only (`guard …`, printed even at 0, no effect on any check). The rerun on the three
  logs prints the same 2548 + 77 901 + 29 853 = 110 302 checks with 0 mismatches. Totals over the three logs:
  - **FS1, H2:** class invalid or no MonStats2 record: 0, `[I]` (0x005B2A16, 0x005B2A43, 0x005B2A72, 0x005B2A8B).
    `unit = none`: 0, `[I]` (0x005B2E46). No null-room exit was added.
  - **B1:** `region = none` 0, `[I]`. `lvl = 0` taken 132 times (19 with `nRooms` still −1 at PX, plus 113 closures where
    `MonDen` and `nRooms` are non-zero on a level other than 108), stays `[C]`. `monDen = 0 or nRooms = 0` taken 5 times
    with `lvl ≠ 0` shown (`nRooms` read in that call), all on `MonDen` 0. The line stays `[C]`, with an inline `[I]` on the
    `nRooms = 0` half (never 0 in any logged region). 32 closures on `MonDen`-0 levels cannot be split between `lvl = 0`
    and `MonDen = 0`. The Chaos line was already `[I]`.
  - **C1:** no logic box 0, `[I]` (split onto its own line). `regionId = 0 or kind ≠ 0` skipped 147 boxes, `[C]`.
    `left = right = 0` 0, `[I]`. The no-record exit was already `[I]`.
  - **D1:** `c = 0` (umon) 0, `[I]`. `nPool = 0` 0, `[I]`.
  - **F2:** `min = 0 or max = 0 or max < min` 0, `[I]` (stock `MinGrp` ≥ 1). `SpawnPosPick` failed 60, `[C]`.
    `leader = none` 0, `[I]`.
  - **G1/G2:** `SpawnPosPick` failed 5, so G1 `boss = none` is taken, `[C]`. `boss = none` after the placement 0, `[I]`.
    **G5:** not a champion, return, 20, `[C]`. **G6:** the checker requires a special-count increment for every
    created pack member, so the first test never failed. It does not model the mod count, so `< 9` is not shown false.
    Both negative paths are `[I]` (fn:sub_005A48C0_ChampionMemberMark@0x005A48C0, 0x005A4911).
  - **H1:** 20 tries failed 65, `[C]`. NearWarpTest rejected 535 tries, `[C]`. LogicRegionIdAt rejected 0, `[I]` (0x0054DD49).
  - **H2, rest:** `smax < s` 0, `[I]` (radius 0 only). No cell found 1105, `[C]`. Ring cells skipped outside the
    rectangle 1121, by SpawnClassCellTest 5 and by CollisionTest 2706, all `[C]`. By LogicRegionIdAt 0, `[I]` (0x005B2D7F).
    `x = 0 or y = 0` was already `[I]`.
  - **I1:** `minion1` not a valid class, return, 596, `[C]`. `PartyMin ≥ PartyMax` (no draw) 0, `[I]`
    (fn:sub_004CC790_RandRangeIncl@0x004CC790). Tentaclehead was already `[I]`.
  - **No guard exit:** A1, E1 (`nRooms ≠ 0` is a condition that B1 already guarantees, not an exit) and J1.
  *Open questions* lists the new `[I]` exits under the unreached branches. *Evidence* names the counters. The gate is green.
  **Next:** the architect checks the commit and closes plan 0014.

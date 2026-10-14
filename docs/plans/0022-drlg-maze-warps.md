# 0022 — DRLG maze generator and warps: maze rooms, level links and warp placement

> **Status:** in-progress (approved 2026-10-14)
> **Created:** 2026-10-14
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only

## TL;DR

**Question:** how does a `DrlgType` 1 level go from one empty first room to its list of maze rooms, each with a
preset `Def` and a forced file index? And how does every level get its links to other levels: which neighbour
each `Vis` slot names, where the act's link builder puts the levels, which room of a maze level holds the stairs
to which neighbour, and which warp points (`level+0x1E0`) the level ends with? Today the maze generator is the
`MZ0`–`MZ1` ADR-0004 seed oracle of [drlg/overview](../specs/drlg/README.md) step 9. The act link callbacks are
named entry points only (rng/seeds 3d). The warp points are logged inputs to `NearWarpTest`
([drlg/collision](../specs/drlg/collision.md)). This plan reads all three and models them in `tools/drlg.py`. It
reruns the run:2026-10-12-drlg-gen logs with the maze oracle replaced, then logs a new run over the maze levels of
all five acts. When it is done:
- `docs/findings/drlg/0006-maze.md` and `0007-warps.md` hold the generator and the links at `[C]` for the logged
  cases;
- `docs/specs/drlg/maze.md` and `docs/specs/drlg/warps.md` are drafted;
- the drlg overview, collision and monsters/spawn specs point at them instead of at oracles or logged inputs.

The outdoor act generators (`OD0`–`OD1`) stay out of scope. Only the warp code they share is read here (see
*Open questions*).

## Context

- Research-map rows `drlg/maze` and `drlg/warps`, both `not started`. Dependencies:
  - [drlg/overview](../specs/drlg/README.md) is reviewed (dispatch, room-creation order, `MazeLevelCreate` with no
    draw, `MazeLevelBuild`'s first room, the maze-room → preset conversion with the 12 × 12 split, and the
    file rotation `MazePresetFile`, all `[C]`);
  - [drlg/room-tiles](../specs/drlg/room-tiles.md) is reviewed. The warp cell's bits 20–25 select a warp id
    (`sub_0066AF30_LevelWarpId`). `WarpTileAdd` and `HiddenWarpTilesAdd` are `[C]`/`[I]`;
  - [drlg/preset](../specs/drlg/preset.md) and [drlg/collision](../specs/drlg/collision.md) are reviewed;
  - [rng/seeds](../specs/rng/seeds.md) is reviewed. Step 3d says the link callbacks step a *copy* of the act seed,
    which is then discarded `[C]`.
- **Code already named:**
  - Maze, from [drlg/0003](../findings/drlg/0003-generator-dispatch.md):
    - `sub_00673B10_MazeLevelCreate`, `sub_00673B30_MazeLevelBuild`, `sub_00673A60_MazeLevelRooms` and
      `sub_006738C0_MazePresetFile` (`[C]`);
    - `sub_0061F490_LvlMazeByLevel`;
    - the oracle window's function chain: `0x00670F60`, `0x00671210`, `0x006714D0` … `0x00672550`, then
      `0x00642590`, `0x00673120` (level 28), `0x00673320` (level 107) and `0x006735F0`;
    - level-specific branches for levels 61, 92, 114, 116 and 119. Level 114 draws `RNG_Range(&L.seed, 2)`.
  - Links:
    - `sub_00678AD0_ActLinkInit`, `sub_00677750_ActLinkAct1` … `sub_00678A70_ActLinkAct5`,
      `sub_006772C0_LevelLinkBuild`, `sub_00642BB0_LevelEnsure`;
    - the level-6 draw that sets level 27's file index.
  - Warps:
    - `sub_0066AEC0_LevelWarpIds` (the act's `+0x90` override list, else leveldefs `+0x68`);
    - `LVLWARP_FindByIdDir`, `sub_0066E160_WarpRecFitDir`, `sub_0066E1C0_WarpUnitAdd`;
    - `sub_006423D0_LevelWarpPointsBuild` and `0x00642390`, which set room flags and a point list after every
      build. [drlg/0005 § 9](../findings/drlg/0005-collision.md#9-nearwarptestgame-room-x-y-and-the-warp-points)
      says they build `level+0x1E0` from room flags `0x30000`/`0x10..0x800`;
    - `sub_0066B2B0_LevelPointFind` (the type-11 waypoint point).
  - The rng call graph under the two dispatch roots puts **24 drawing functions inside the maze window**
    (drlg/0003 § RNG call graph).
- **Data:**
  - [LvlMaze](../tables/LvlMaze.md): layout `[C]`, every meaning `[L]`, owner `drlg/maze`; backlog 2026-10-11 (d)
    is still open.
  - [LvlWarp](../tables/LvlWarp.md): layout `[C]`, the select, exit-walk and offset meanings `[L]`.
  - [Levels](../tables/Levels.md): `Vis0..7` at leveldefs `+0x48` and `Warp0..7` at `+0x68`, layout `[C]`.
    `Warp` resolves into LvlWarp `[C]`; `Vis` has no meaning yet.
  - [LvlPrest](../tables/LvlPrest.md): the maze `Def` ranges per level type (`MAZE_DEF_BASE` in `tools/drlg.py`).
  - Stock data has **70 `DrlgType` 1 levels** across 20 level types (Levels `Act` is 0-based: Act I 18, Act II 26,
    Act III 9, Act IV 1, Act V 16). LvlMaze has 81 rows, so some rows may name non-maze levels. `Merge` takes the values
    500 (69 rows), 0, 1000 and 800. This is a planning count, which Phase 0 replaces with a survey.
- **Harness:**
  - `tools/gdb/drlg-gen.gdb`/`drlg-gen.py` already log the `MZ0`/`MZ1` window, the level seed around it and every
    preset instance the maze leaves;
  - `tools/drlg.py gen` replays them;
  - run:2026-10-12-drlg-gen covers the Den of Evil, Sewers Level 1 and Catacombs Levels 2–4 (owner-played), its
    first test set;
  - test characters reach any act through the `tools/d2s.py build` recipes, including `quests: all`.
- **Why now:** the DRLG plans so far (0008, 0016, 0017) each left the maze window and the warp points as named
  boundaries. Maze levels are most of the dungeon levels in the three priority subsystems: their room list feeds
  population, collision and object placement. `objects` (plan 0023) also needs the warp and waypoint points.
- **Leads:**
  - `src:pk-maze-ds1-mechanisms` (the Phrozen Keep thread on maze DS1s) and `src:pk-lvlprest-guide`, both
    already registered;
  - `src:d2dfg-blizzard` (the LvlMaze and LvlWarp columns, which it describes for D2R).

  Community coverage of the maze *algorithm* is thin (modding guides describe the tables, not the generator), so
  Phase 1b will mostly record `not covered`.

## Phases

### Phase 0 — Maze and link data
- **Owner skill:** archivist
- **What:** a survey of the maze levels and the level links in the data. The table docs exist, so this phase fills
  gaps only. It adds no new table doc.
- **Outputs:**
  - [LvlMaze](../tables/LvlMaze.md) § Survey: per row, its level, that level's `DrlgType` and `LevelType`, and the
    rows whose level is not a maze level (and the reverse);
  - [LvlPrest](../tables/LvlPrest.md) § Maze presets: per maze level type, the `Def` range, the count of rows and
    files, and the DS1 name pattern of the maze rooms;
  - [Levels](../tables/Levels.md) § Links survey:
    - `Vis` → level id resolution;
    - whether `Vis` is symmetric (A names B ⇔ B names A) and the exceptions;
    - `Warp` per `Vis` slot;
    - LvlWarp `Direction` per id;
  - a `tools/` survey command, registered as a gate survey with a baseline.
- **Done when:**
  - the survey prints the 70 (or corrected) maze levels with their LvlMaze values;
  - every maze `Def` range is listed with its file counts;
  - the `Vis`/`Warp` pairing table is printed, with symmetry exceptions and slots whose `Vis` is set but whose
    `Warp` is −1 (or the reverse);
  - every count is `[C]` by command. Meanings stay `[L]`.

### Phase 1 — Read the maze generator and the links
- **Owner skill:** reverser
- **What:** read the maze window end to end, the act link builder, and the warp and point builders. Then choose
  the boundary for Phase 2.
- **Outputs:**
  - `docs/findings/drlg/0006-maze.md` and `docs/findings/drlg/0007-warps.md`;
  - `re/symbols.csv` rows (subsystems `drlg/maze` and `drlg/warps`);
  - `re/types/` (the maze room record `M[+0x20]`, the link-builder struct).
- **Done when:** the findings state, with addresses and `[I]` or better:
  - **Maze rooms.** Which LvlMaze field is the room count per difficulty, with how it is read: the `Level` match or
    the row index (backlog 2026-10-11 (d)), and how the expansion or classic flag enters. Also `SizeX`/`SizeY`
    beyond the first room, and what `Merge` does.
  - **The generator as an algorithm.** Room placement (the growth step, the direction draws, the bounds and overlap
    tests against the level rectangle), the order rooms are created and removed in, and every draw with its seed
    (the level seed `+0x1C4` unless stated). This includes the per-type function chains (one entry per level type
    in the stock data) and the level-specific branches 28, 61, 92, 107, 114, 116 and 119.
  - **Each maze room's `Def` and forced index.** How each room gets its preset `Def` (connectivity, exit
    directions) and the forced file index `M.idx` that `MazePresetFile` takes (drlg/0003 open question).
  - **Special rooms.** The rooms that hold the warp to each `Vis` neighbour (stairs up and down, the entrance), quest
    and boss rooms (e.g. the Barracks forge room, the Tomb treasure room, River of Flame's Hellforge), the waypoint
    room, and the order of their draws relative to the room growth.
  - **Links.**
    - `ActLinkInit` and the five act callbacks: which level pairs are linked, the `LinkPick` callbacks and their
      draws on the act-seed copy, and the positions they write (`LevelEnsure`, the level rectangle);
    - how `Vis` slots and `Warp` slots pair;
    - what the act's `+0x90` override list is and who writes it.
  - **Warp placement in a maze level.** Which room gets the warp cell, how bits 20–25 are set, and the LvlWarp
    record the tile build then reads. Also the meanings of `OffsetX`/`OffsetY`, `ExitWalkX/Y` and
    `SelectX/Y/DX/DY`, or a statement that the server never reads them.
  - **Warp points.**
    - `0x00642390` and `LevelWarpPointsBuild` 0x006423D0 in full: the room flags `0x30000`/`0x10..0x800`, the point
      list `+0x1E0`/`+0x204`/`+0x228`, and the order of points;
    - the type-11 waypoint point (`LevelPointFind`) and the type-11 level-seed step of drlg/0005 § 9 (who owns that
      draw).
  - **The shared outdoor side.** Which of the above the outdoor generators call too (warp cells, points), named so
    that `drlg/outdoor` can cite it.
  - **The boundary decision** for Phase 2. Is the generator modelled end to end (room growth, `Def`s, indices,
    warps), or does any part stay a logged input? Recommend one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch the registered leads and look for others on the maze generator and on level links. Compare per
  `evidence-rules.md` § Community cross-checks, blind first. Coverage is expected to be thin.
- **Outputs:** `docs/sources.md` entries, or a "none found" note with the searches made; verdicts in each finding's
  *Leads used*.
- **Done when:**
  - every LvlMaze, LvlWarp and Levels `Vis`/`Warp` meaning, and every compared generator claim, carries a verdict
    with a `src:` id or `not covered`;
  - every `contradicted` claim is a required case of Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (agent-driven per
  [harness-play](../../.claude/skills/reverser/references/harness-play.md); a human may play)
- **What:** model the maze generator, the act links and the warp points in `tools/drlg.py`. Replace the `MZ0`–`MZ1`
  oracle in `drlg.py gen`, and the logged warp points in `tools/collision.py`/`tools/monspawn.py`.
- **Logging:** extend `tools/gdb/drlg-gen.gdb`:
  - every draw inside the maze window with its caller;
  - each maze room's create and remove with its rectangle, `Def` and index;
  - the link builder's callback draws and the level rectangles it writes;
  - the warp cells and the point list at the end of `LevelInit`.
- **Done when:** a run `run:YYYY-MM-DD-drlg-maze` shows, with 0 mismatches against the model:
  - the logs of run:2026-10-12-drlg-gen rerun with the maze window predicted. The level seed after the window, the
    room list, each room's `Def`/index and the preset instances match;
  - at least 25 maze levels built, over all five acts and every maze level type in stock data, on all three
    difficulties for at least five of them (the room counts are per difficulty), and on classic and expansion for
    at least three Act I–IV levels;
  - every level-specific branch (28, 61, 92, 107, 114, 116, 119) reached, or listed as unreached with its reason;
  - the act links of all five acts predicted (positions and the act-seed-copy draws), including level 27's file
    index from the level-6 draw (unexercised in run:2026-10-12-drlg-gen);
  - the warp cells and the `level+0x1E0` point list predicted for every logged level, maze and preset. Outdoor
    levels are predicted only where the shared code is the whole story;
  - the plan 0014 and run:2026-10-14-collision logs rerun with the warp points predicted instead of logged, 0
    mismatches;
  - the Phase 1b cases;
  - any remaining boundary named in the record.

  In-scope claims go to `[C]` citing the run. drlg/0003 and drlg/0005 § 9 note which oracle or logged input is now
  replaced.

### Phase 3 — Specs: drlg/maze and drlg/warps, and the overview updated
- **Owner skill:** spec-writer
- **What:** write `docs/specs/drlg/maze.md` and `docs/specs/drlg/warps.md`, and link both from the
  [drlg README](../specs/drlg/README.md). Replace the step 9 maze oracle and the act-seed consumer entry points
  there, the warp-point inputs in [drlg/collision](../specs/drlg/collision.md), and the warp-point row of
  [monsters/spawn](../specs/monsters/spawn.md) *Inputs and oracles*.
- **Done when:**
  - both specs follow the template and every statement is tagged;
  - `maze.md` has the RNG call sequence of one full maze level as a worked example (from the run; a small level such
    as the Den of Evil is the natural case), and a Mermaid diagram of the room growth;
  - `warps.md` has one act's link build and one level's warp points as worked examples;
  - the edited rows elsewhere cite the new run;
  - the architect's review passes.

## Open questions

- **Outdoor levels.** The outdoor act generators (`OD0`–`OD1`, `0x0067D050`, `0x00675080`) and `LvlSub` stay with
  `drlg/outdoor`. This plan reads the warp and point code they share, names their call sites, and stops there.
  Outdoor warp placement that lives inside the outdoor generators (e.g. which border cell holds a cave mouth) is
  deferred to that plan.
- **Preset levels.** Their warps come from DS1 presets (`drlg/preset`, reviewed). Only the point list built after
  them is in scope here.
- **Waypoints.** The waypoint *object* and its placement belong to `objects` (plan 0023). Here only the type-11
  level point and its level-seed side effect are read.
- **Arcane Sanctuary and Canyon of the Magi.** The `quests: all` recipe could not reach them by waypoint (backlog
  2026-10-14). Arcane Sanctuary (74) is a maze level (`DrlgType` 1; corrected 2026-10-14 from drlg/0006). If Phase 2 needs a link involving either, it takes that
  backlog entry first.
- **Client warps.** The client rebuilds levels from the same seeds; its warp drawing (`Select*`, the cut-away) is
  named only.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-14 — Drafted and approved (architect, on the owner's instruction "draft all three then approve").**
  Phase 0 (archivist) can start now. Phases 1 and 2 (reverser) wait for Ghidra and the harness after plan 0019
  Phase 2.
- **2026-10-14 — Phase 0 landed (archivist, branch `lane/a0022p0`).** New `tools/maze_survey.py <excel-dir> [--quiet]`,
  registered as gate survey `maze` (baseline `tools/gate/baselines/maze.txt`, generated by the survey). Docs:
  [LvlMaze § Survey](../tables/LvlMaze.md#survey-plan-0022-phase-0),
  [LvlPrest § Maze presets](../tables/LvlPrest.md#maze-presets-plan-0022-phase-0),
  [Levels § Links survey](../tables/Levels.md#links-survey-plan-0022-phase-0). Every count is `[C]` by command, and
  every meaning stays `[L]`.
  - **LvlMaze reconciliation:** the 70 maze levels / 20 types are confirmed (Act I 18, II 26, III 9, IV 1, V 16).
    Each has exactly one row. The 81 rows are 70 maze rows plus 11 others: `Null` (row 5, level 0) and 10 preset
    levels (13–16, 25, 37, 90, 91, 93, 132), all of maze level types. `Merge` 1000 is exactly the Harem, Basement and
    Arcane types.
  - **Maze presets:** 15 types have a rotation base. In 14 of them, record base + *m* carries exit mask *m*
    (N 8, S 4, E 2, W 1) in its `Name` and `File1`, and every file slot follows one DS1 pattern
    (`Act1/Caves/Cave{m}.ds1` …). **Surprise:** type 35 (Act 5 Lava) breaks this. Its range 1053–1067 is six
    non-mask-ordered Lava records followed by nine Baal records, and it overlaps type 34's range. The five types with
    no base (Harem, Basement, Arcane, Spider, Temple) have quadrant-named records. Arcane is the exception: 510–524
    are mask-ordered, and 11 of them have `Files` 0.
  - **Links:** all 236 `Vis` cells resolve. The links are symmetric except one, 133 → 17, which is also the only
    cross-act link. Of the slots, 228 hold `Vis` + `Warp`, 8 hold `Vis` without `Warp` (four symmetric pairs: 26↔27,
    27↔28, 32↔33, 107↔108), and 0 hold `Warp` without `Vis`. Level 0's eight `Warp` cells are explicit 0s, so
    Levels' earlier "236 warp cells" count included them (corrected: 228 on real levels). 5 LvlWarp `Id`s are
    `'l'`/`'r'` pairs, named by 20 cells, all in Act V.
  - Questions for Phase 1 are in the backlog (archivist → reverser, 2026-10-14). Review request: archivist →
    architect, 2026-10-14.
- **2026-10-14 — Phase 0 accepted (architect).** Survey `maze` reruns green under the gate (`--full=maze`); the LvlMaze
  reconciliation (70 maze rows + 1 null + 10 preset levels), the Vis/Warp pairing (one asymmetric link, 133 → 17) and the
  Levels.md correction (level 0's `Warp` cells are 0) are data facts at `[C]`; every meaning stays `[L]`. The type 35 (Act V
  Lava) range overlap, the five base-less types, the record choice after each range, the `Vis` reader and the non-maze
  LvlMaze rows are required Phase 1 questions (backlog archivist → reverser). Phase 1 (reverser) waits for Ghidra after
  plan 0021's reverser phases.
- **2026-10-14 — Phase 1 and 1b landed (reverser, branch `lane/r0022p1`).** Findings
  [drlg/0006](../findings/drlg/0006-maze.md) (the maze generator) and [drlg/0007](../findings/drlg/0007-warps.md) (links, warp
  slots, warp points). 75 `re/symbols.csv` rows (`drlg/maze`, `drlg/warps`), `re/types/maze.h`.
  - **Maze:**
    - each room is one `RoomCreate`, placed edge to edge with an overlap test against every room, and with no
      level-rectangle test until the final shift;
    - growth picks a room by `Range(level seed, count)`, then takes the direction from that room's own seed;
    - `Merge` is a per-mille draw on each edge-sharing neighbour's seed;
    - `Def = base + exit mask`, or a corner table for the quadrant and Act V lava types;
    - specials (Prev/Next/Down/Waypoint/quest rooms) replace dead ends from 16-byte tables under a rotating index;
    - themes give `Def + 15`, after 31 draws.

    One fixed chain per level type, and every level-specific branch, is in § 5 of drlg/0006.
  - **Reading check:** `tools/maze_replay.py` replays the 12 logged maze windows of run:2026-10-12-drlg-gen (levels 8,
    47, 34, 35, 36) with 0 mismatches (seed, list, `Def`, index, relative rects). Types 3/10/13 are `[C]`; the rest is
    `[I]`.
  - **Links:** the act link builder is a backtracking layout on an act-seed copy (tables `0x006F0750`–`0x006F0ED0`); level
    27's index is drawn on the act seed itself. `Vis`*k*/`Warp`*k* pair by slot index; the slot is the DS1 warp cell's
    bits 20–25; repeated destinations pair by rank, with no draw. `Warp` −1 is a walkable seam. Warp points: one per room
    with a valid warp bit or the waypoint flag (correction to drlg/0005 § 9: no carry).
  - **Boundary recommendation for Phase 2:** model the maze window end to end, and the act links of Acts I, II, IV and V.
    Keep Act III's jungle layout (`0x00677880`/`0x00678910`, not read) a logged input owned by plan 0026.
  - **Phase 1b:** `d2dfg-blizzard` is the only source (LvlMaze, LvlWarp and Levels `Vis`/`Warp`). There is no contradiction,
    so no required Phase 2 case from 1b. The generator itself is not covered.
  - **Answers:** the Phase 0 questions are answered and struck in the backlog. Plan 0026 (c) is answered: 769–795, 836 and
    852–856 are maze, and 857–862 are outdoor.
  - New backlog: reverser → architect (review), reverser → archivist (table meanings, a DS1 warp-slot survey).
- 2026-10-14 (architect): Phase 1 and 1b accepted. Spot checks: `sub_00670880_MazeRoomPlace`, `sub_006709B0_MazeRoomDefFromExits`, `sub_00670C70_MazeRoomMerge` and `sub_006735F0_MazeThemes` resolve; `tools/maze_replay.py` rerun by the architect: 12 windows, 0 mismatches. Rulings: (1) the boundary stands: Phase 2 models the maze window end to end (Arcane may stay a temporary oracle if it resists, named in the record) and the act links of Acts I, II, IV and V; Act III's jungle layout (0x00677880/0x00678910) stays a logged input for plan 0026. (2) Phase 2 must reach, beyond the plan's list, at least one level of each finisher read only `[I]` (Arcane, Tomb/Baal, Act V hell, Durance 100/101, 107) and the nightmare/hell room counts. (3) The shared-type answer (769–856 maze, 857–862 Act IV outdoor) is accepted for plan 0026. (4) The plan's Arcane sentence is corrected. The symbols-with-findings commit order is fine: the gate requires it.
- **2026-10-14 — Phase 1 table follow-ups landed (archivist, branch `lane/a-sweep5`, backlog reverser → archivist).**
  The LvlMaze, LvlWarp and Levels `Vis`/`Warp` meanings now cite drlg/0006 and drlg/0007. New warp-slot survey
  `python3 -I tools/ds1.py warps workspace/merged [--quiet]` (gate survey `ds1_warps`):
  [LvlPrest § Warp slots](../tables/LvlPrest.md#warp-slots-plan-0022-phase-2). Counts are `[C]`; the slot-to-neighbour
  readings are `[I]`.
  - Each record the maze code places carries one slot or none; no `base + mask` record carries one.
  - Prev 0 / Next 1 is the common case. The exceptions are the Dungeon (Next 0, Prev 1), the Act II sewer (dock 1,
    Next 2), the Tomb (Next 4) and the Cave (Down 4). The quadrant types (Harem, Basement) put one slot in each corner.
  - The Crypt Prev records carry slot 0, so level 133's Prev stairs lead to `Vis0` 17 (`Warp0` 8).
  - **Surprise:** the Durance Prev/Next records carry slot 2/3 and 0/1 by the side they face, so the slot a level
    uses depends on the finisher's rotation draw. Basement 3 (54) carries slots 2 and 3 with no `Vis`.

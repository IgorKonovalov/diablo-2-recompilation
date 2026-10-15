# 0026 — DRLG outdoor generator: act layouts, borders, paths and substitutions

> **Status:** in-progress (approved 2026-10-14)
> **Created:** 2026-10-14
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only

## TL;DR

**Question:** how does a `DrlgType` 3 (outdoor) level become its grid of outdoor rooms? The question covers:
- which act-specific generator runs;
- how it lays out borders, cliffs, rivers, paths and town or level edges;
- where it places the preset areas inside the wilderness (camps, the Tristram and Den entries, Act III's jungle chain,
  Act V's Bloody Foothills siege rows);
- what it draws from the level seed, and in which order.

Today the act layouts are the outdoor-layout ADR-0004 seed oracle of [drlg/overview](../specs/drlg/README.md) step 9 (log lines `OD0`–`OD1`, drlg/0003).
`sub_006750F0_OutdoorRoomsCreate` and the `LvlSub` roll that follow it are already read. This plan reads the
generators, models them in `tools/drlg.py`, and replaces the oracle. When it is done:
- `docs/findings/drlg/0008-outdoor.md` holds the layouts at `[C]` for the logged levels;
- `docs/specs/drlg/outdoor.md` is drafted;
- the overview, room-tiles and monsters/spawn specs point at it instead of at an oracle.

## Context

- Research-map row `drlg/outdoor`: `not started` (moved from `drlg/preset` on 2026-10-13). Its dependency
  [drlg/overview](../specs/drlg/README.md) is reviewed.
- Its neighbour [plan 0022](done/0022-drlg-maze-warps.md) (maze and warps) is in progress. 0022 owns the act link builder
  and the warp points, and reads only the warp code the outdoor generators share. This plan consumes those warp
  results: its Phase 1 starts after 0022 Phase 1 is accepted, so the two readings don't overlap.
- **Code already named:**
  - `sub_00675320_OutdoorLevelCreate` (no draw, `[I]`) and `sub_00675360_OutdoorLevelBuild` (`[C]`);
  - `sub_006750F0_OutdoorRoomsCreate` (`[C]`) and `sub_0067D540_OutRoomCreate`;
  - the LvlSub family: `LVLSUB_GetRecordByType`, `sub_006706A0_LvlSubRoll` (`[C]`), `sub_006707A0_LvlSubApply`,
    `sub_0066FF50_LvlSubApplyAll`, `sub_00670170_LvlSubApplyPick`, `sub_0066FCF0_LvlSubFits`,
    `sub_0066FE00_LvlSubMatches`, `sub_0066FAD0_LvlSubStamp` and `sub_006704E0_LvlSubLoadDs1` (mostly `[I]`);
  - the outdoor grid cell's bits 16–19, which choose the preset file index (drlg/0003);
  - the grid prepare `0x0067D2D0` (drlg/0002).
- Data:
  - [Levels](../tables/Levels.md) gives `DrlgType`, `SizeX/Y`, `OffsetX/Y`, `SubType`, `SubTheme`, `SubWaypoint`,
    `SubShrine`, `Vis*` and `Warp*`;
  - [LvlPrest](../tables/LvlPrest.md) gives the outdoor border and edge presets (`Outdoors` flag, the per-act DS1
    families);
  - [LvlSub](../tables/LvlSub.md) has a complete layout, with semantics partial;
  - [LvlTypes](../tables/LvlTypes.md).
- Harness: `tools/gdb/` DRLG logging (run:2026-10-12-drlg-gen and the collision run) already logs outdoor rooms and
  their seeds. The run:2026-10-12-drlg-gen logs can be rerun with the oracle replaced.
- Leads: little community documentation covers the outdoor generator. Phase 1b searches and records "none found" if so.

## Phases

### Phase 0 — Outdoor data survey
- **Owner skill:** archivist
- **What:** survey the data the outdoor generators read: the outdoor levels per act, their sizes and offsets, the
  `LvlPrest` rows of each act's border, edge and fill families, and the LvlSub semantics the data can show.
- **Outputs:**
  - `docs/tables/Levels.md` § Outdoor survey;
  - `docs/tables/LvlPrest.md` § Outdoor presets: the families by DS1 path prefix, their sizes and `Files` counts;
  - LvlSub.md semantics completed where the data shows them;
  - a `tools/outdoor_survey.py` command, gate survey `outdoor`, with a baseline.
- **Done when:** for each act, one command prints:
  - the outdoor levels with size and offset;
  - the preset families the act's generator can place, with DS1 sizes;
  - the LvlSub types each level rolls.

  Layouts are `[C]` by data; meanings stay `[L]`.

### Phase 1 — Read the act generators
- **Owner skill:** reverser
- **What:** read the outdoor generator of each act that `OutdoorLevelBuild` dispatches to, then choose the Phase 2
  boundary.
- **Outputs:**
  - `docs/findings/drlg/0008-outdoor.md`;
  - `re/symbols.csv` rows (subsystem `drlg/outdoor`);
  - `re/types/` additions (the outdoor grid and its cell bits).
- **Done when:** the finding states, with addresses and `[I]` or better:
  - **the dispatch:** which generator each outdoor level runs, by act and level id;
  - **per act:** the grid size, how borders and level edges are laid, how paths, rivers and cliffs are drawn (if
    drawn), and how preset areas are positioned. Every level-seed draw is listed in order, with its range;
  - **the cell bits:** how the grid cells encode the preset file index (bits 16–19), the warp id (20–25, shared with
    0022) and the other flags;
  - **the room split:** how the grid becomes `OutdoorRoomsCreate` rooms, as far as drlg/overview doesn't already say;
  - **the LvlSub step:** its remaining `[I]` functions, as they apply to the act grids;
  - **the boundary decision** for Phase 2. Recommend one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** search for and register community documents on outdoor map generation (wilderness layouts, the Act III
  jungle chain, the Act V siege rows). Compare blind. Downloads go to the scratchpad only.
- **Outputs:** `docs/sources.md` entries or a "none found" note listing the searches made; verdicts, if any, in the
  finding's *Leads used*.
- **Done when:** each layout claim carries a verdict or `not covered`.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (agent-driven per [harness-play](../../.claude/skills/reverser/references/harness-play.md);
  most of the work is a level walk with no fighting)
- **What:** extend `tools/drlg.py` with the outdoor generators, replace the outdoor-layout oracle, and rerun the
  run:2026-10-12-drlg-gen logs. Log a new run over the outdoor levels of all five acts.
- **Logging:** at each outdoor level build: the level, the seed, every generator draw, the final grid (cell values),
  the rooms created with their preset file indices, and the seed at exit.
- **Done when:** a run `run:YYYY-MM-DD-drlg-outdoor` shows, with 0 mismatches against the model:
  - every outdoor level of Acts I–V generated at least three times (different game seeds), in at least two
    difficulties, classic and expansion where the level exists in both;
  - the final grid matches cell for cell, and the room list and file indices match;
  - the level seed after the generator matches;
  - the Phase 1b cases, if any.

  In-scope claims go to `[C]`.

### Phase 3 — Spec: drlg/outdoor
- **Owner skill:** spec-writer
- **What:**
  - write `docs/specs/drlg/outdoor.md` and link it from the drlg README;
  - replace the outdoor-layout oracle rows in drlg/overview and the outdoor notes in room-tiles and monsters/spawn
    with links.
- **Done when:**
  - the spec follows the template, and every statement is tagged;
  - it gives each act's generator as an ordered draw sequence, with a Mermaid diagram of the grid layout per act;
  - it has worked examples from the run;
  - the architect's review passes.

## Open questions

- Town levels (DrlgType 2 presets) are drlg/preset. Only the wilderness that borders a town is in scope.
- Objects that the outdoor DS1s carry are drlg/preset and plan 0023. Only their placement inside the grid is in
  scope.

## Implementation log

- 2026-10-14 (architect): drafted and approved on the owner's request. Phase 0 (archivist) may start.
- **2026-10-14 — Phase 0 landed (archivist, branch `lane/a0026p0`).** New `tools/outdoor_survey.py <root> [--quiet] [--act N]`,
  registered as gate survey `outdoor` (baseline `tools/gate/baselines/outdoor.txt`, generated by the survey). For each
  act, `--act N` prints the outdoor levels with size and offset, the preset families the act's generator can place
  with their DS1 sizes, and the LvlSub records each level rolls. Docs:
  [Levels § Outdoor survey](../tables/Levels.md#outdoor-survey-plan-0026-phase-0),
  [LvlPrest § Outdoor presets](../tables/LvlPrest.md#outdoor-presets-plan-0026-phase-0),
  [LvlSub § Outdoor survey](../tables/LvlSub.md#outdoor-survey-plan-0026-phase-0). Every count is `[C]` by command.
  Meanings stay `[L]`.
  - **Levels:** 31 outdoor levels, 8 level types. Per generator act: I 8 (2–7, 17, 39), II 7 (41–46 and level 134 by
    the drlg/0003 override), III 8 (76–83), IV 4 (104–106, 108), V 4 (110–112, 117). Sizes are equal in all
    difficulties and are multiples of 8. **Surprise:** Barricade 1 and 2 (111, 112) have −1 in every size and offset cell.
  - **Presets:** the survey rule finds 450 records in 126 families (I 56/27, II 52/27, III 156/26, IV 50/13,
    V 136/33). No record fits two acts. Every DS1 size equals its record's size. Several level sizes are exact
    sums of family record sizes: Siege 1 = 15 × 16×48 strips, Jungle = 2 × 6 cells of 32 with 64×32 `Head`/`Tail`,
    Kurast 4 = the 48×16 `Bridge`, Travincal = 16+32+16 × 32+32, Diablo 1 = 5 × 5 of 24×24. Acts I, II and IV each
    have a 12-record 8×8 border family, and Act III's `Jungle` 530–544 is named in maze exit-mask order.
  - **Rule limits:** types 22 and 28 are shared with maze levels, so the `Mephisto` families (769–795) and the
    Act IV Lava records (836, 852–862) are listed although they may be maze records.
  - **LvlSub:** draws per out room are 6 (Act I wilderness), 7 (Act II deserts and 134), 3 (Barricade 1/2),
    2 (Barricade Snow) and 0 elsewhere (every Act III/IV level, Siege, Graveyard, Moo Moo Farm). **Surprise:**
    the five records with `BordType` ≠ −1 (`Type` 0–3, 12) are exactly the five `tag_type` 2 DS1s, the five with
    all-zero `Prob`/`Trials`/`Max`/`Dt1Mask`, and the five types no level names. `Expansion` 1 marks exactly the
    `Type` 10–12 records. `GridSize` 2 occurs only on `Barricade`.
  - Questions for Phase 1 are in the backlog (archivist → reverser).
- 2026-10-14 (architect): Phase 0 accepted. Rulings: (1) families grouped by record `Name` with variant tokens removed, as delivered, replace the plan's "by DS1 path prefix" (path stems would make every record its own family). (2) The data-only act-membership rule stands, with its blind spot flagged: records of the shared types 22 and 28 (`Mephisto *` 769–795, Act IV Lava 836, 852–862) may be maze records; Phase 1 settles it with 0022. (3) The four reverser questions (Barricade size, `tag_type` 2 LvlSub records, shared-type records, bits 16–19 beyond `Files`) are required items of Phase 1.
- **2026-10-14 — Phase 1 and 1b landed (reverser, branch `lane/r0026p1`).** [drlg/0008](../findings/drlg/0008-outdoor.md),
  125 new `re/symbols.csv` rows (`drlg/outdoor`) and 5 updated, `re/types/outdoor.h`, and two reading checks:
  `tools/outdoor_replay.py` (Acts I, II, IV, V, with the act link builder of drlg/0007 modelled for the rects, adjacency lists
  and outdoor flags) and `tools/jungle_replay.py` (Act III's jungle layout on the act seed, then the window). Every logged
  outdoor window replays with 0 mismatches: 370 windows (106 + 27 distinct builds) from 63 logs of five runs (record: the
  2026-10-14 addendum to run:2026-10-12-drlg-gen). Levels 2–7, 17, 41–45, 76–79, 104–106, 108 and 110–112 are `[C]`;
  39, 46, 80–83, 117, 134 and the unreached branches (§ 13) are `[I]`.
  - **Dispatch:** the act index (134 → Act II). No generator branches on difficulty, expansion or player count.
  - **Per act:** the common ring, seam mark and border pass (Acts I, II, IV), the placers and the per-`Def` file rotation
    (first use `RangeB(Files)`), waypoint and shrine marks; Act I cliffs, rivers, bridge, caves, roads and area lists; Act II
    cliff layouts, special areas and fill lists; Act III jungle cells, Kurast rings and fills, Travincal; Act IV Mesa fills and
    level 108's fixed grid; Act V Siege strips (no draw) and the Barricade ring, ravine, gates, caves, stamps, prisons and table.
  - **Questions:** (a) link-pick sizes; (b) the `tag_type` 2 records are border stamps (`BordType`, `GridSize` anchored);
    (c) 857–862 and 836 on level 108, 852–856 never outdoor; (d) the seam opening and explicit indices. Backlog entry struck.
  - **Boundary recommendation:** model the whole window in Phase 2 (the two scripts are the start); log the unreached levels.
  - **Phase 1b:** two sources registered (`maxroll-d2r-map-reading`, `fandom-d2-act-areas`); verdicts held / held with
    refinement / not covered, no contradiction; gap: Frigid Highlands' waypoint (backlog to the archivist).
- 2026-10-14 (architect): Phase 1 and 1b accepted. The architect reran both replays on the recorded log list: outdoor_replay 106 windows, jungle_replay 76 windows, 0 mismatches each. Rulings: (1) the boundary stands: Phase 2 models the whole outdoor window, starting from the two scripts, and logs the levels and branches no log reaches (39, 46, 134, Act II cliff layouts 1 and 4, 80–83, the jungle restart/path retry, 117, the prisons' fallback). (2) Overlap with plan 0022: the act link builder has one implementation. Plan 0022 Phase 2 owns it in `tools/drlg.py`, starting from `outdoor_replay.py`'s link code; plan 0026 Phase 2 imports it rather than keeping its own copy. Whichever Phase 2 runs first moves the code, and the other reuses it. (3) The answers to (a)–(d) are accepted; 852–856 stay `[I]` (no outdoor placer). (4) The Frigid Highlands waypoint lead (Def 880 `To Siege` lists waypt.dt1) goes to the archivist as filed.
- **2026-10-15 — Phase 2 landed (reverser, branch `lane/r0026p2`).** run:2026-10-15-drlg-outdoor
  ([experiments](../findings/drlg/experiments.md#run2026-10-15-drlg-outdoor)): 11 agent-driven sessions on harness slots 1
  and 2 (waypoint chains from the Act IV town; no fighting), 522 outdoor windows over 29 levels, 0 mismatches.
  - **Model:** the outdoor window of every act and Act III's jungle layout and Kurast stack live in `tools/drlg.py` (class
    `Outdoor`, `act_links_a3`), on the plan 0022 link builder (no second copy); `tools/outdoor_replay.py` and
    `tools/jungle_replay.py` are thin drivers. `drlg.py gen` has no outdoor oracle left: it predicts the seed after the
    window, every preset anchor with its `PIO` file index and `PRC` flags, every out room, each out room's `+0x28` (grid0 `|
    0x80000`) and Act III's `LevelLinks` list. With the new logger `tools/gdb/drlg-outdoor.gdb` it checks every level-seed step
    of the window (1443544) and the final def grid, grid0 and cell grid cell for cell.
  - **Done when:** every outdoor level of Acts I–V except 39 and 134 in 4–11 map seeds and all three difficulties, Acts I–IV
    in classic and expansion; grids, rooms, file indices and the seed after the window match. The run:2026-10-12-drlg-gen and
    run:2026-10-15-drlg-maze logs give 206937 checks, the 93 older logs with an `OD0` line 719282, both 0 mismatches;
    outdoor_replay (460 windows), jungle_replay (266), maze_replay (12), collision and monspawn stay at 0. The level 111
    waypoint case is met (the `To Siege` room's `0x30000`, from the DS1 scan). No Phase 1b case was raised.
  - **Boundaries:** level 39 (cow portal: `d2s.py build` cannot write a tome; backlog to the archivist) and level 134 (the
    Pandemonium transmute did nothing in single player). Unreached branches are listed in the record.
  - **Side results:** Canyon of the Magi opens by waypoint (backlog 2026-10-14 entry partly answered); the
    run:2026-10-15-drlg-maze `UniqClassic.d2s` is an expansion-status save (point (4) of the review request); the warp
    points of levels with out rooms are predicted, so `tools/collision.py` no longer takes levels 4 and 44 from the log.
  - [drlg/0008](../findings/drlg/0008-outdoor.md) § 15 and the tags it moves to `[C]` (46, 80–83, 117, the out-room bits, the
    Act III links); 10 `re/symbols.csv` rows to `C`.
  - Review request: backlog reverser → architect, 2026-10-15.
- 2026-10-15 (architect): Phase 2 accepted. `drlg.py gen` rerun on the 11 logs of run:2026-10-15-drlg-outdoor: 572 211 checks, 0 mismatches. Rulings: (1) levels 39 (Moo Moo Farm, blocked by the `tools/d2s.py build` `tbk` crash, backlog → archivist) and 134 (the Pandemonium key transmute refused in single-player hell; the refusal code unread) are named boundaries; the spec lists them under Open questions, and Phase 2 is done without them. (2) The maze run's session s4 was an expansion save (status `0x20`): the architect corrected run:2026-10-15-drlg-maze (a correction note, the coverage line and the case row), drlg/0006 (summary and Coverage bullet) and drlg/maze (the mode-flag claim), which now cite the four genuine classic sessions of this run (46 maze windows, levels 9, 56, 65, 84, 86, 92, 100, 107, 0 mismatches). drlg/maze stays `reviewed`. (3) Phase 3 (spec-writer, drlg/outdoor) can start.
- **2026-10-15 — Phase 3 landed (spec-writer, branch `lane/s0026p3`).** New [drlg/outdoor](../specs/drlg/outdoor.md) (draft,
  C 126 / I 24 / L 6): the window, the cell grid and its bits (with the out-room flags, grid0 `| 0x80000`), the level
  outline, the placement primitives and the file rotation, the seam mark and border pass, the waypoint and shrine marks,
  the border stamps, and each act's generator (§ H–L) with an ordered draw sequence and a Mermaid grid diagram per act;
  Act III's jungle layout on the act seed (§ J). Worked examples from run:2026-10-15-drlg-outdoor (map seed 3103: Burial
  Grounds' 9 draws one by one, Valley of Snakes' 19 with the overwritten W edge piece and the `PlaceRandom` shuffle, Chaos
  Sanctuary's 7 first uses, Spider Forest's 7) and a seed-in/seed-out/draw-count table for 14 levels of map seed 3101.
  Levels 39 and 134 are under *Open questions* as named boundaries (ruling of 2026-10-15). No statement takes a fact from
  `tools/*.py`; the table contents and the steps the finding gives only in outline are *Open questions* and a backlog
  entry to the reverser. Links: [drlg/overview](../specs/drlg/README.md) (purpose, step 7 and 8, step notes 7–8, the
  act-seed consumers, the sub-generator boundaries: the outdoor oracle row removed, open questions struck);
  [drlg/warps](../specs/drlg/warps.md) (Act III's links and the out rooms' warp bits now link § J and § B and cite the run;
  A1, its two bullets, D1, E1 and the Act I flag table to `[C]`; one `[L]` struck: C 86 / I 35 / L 6 → C 90 / I 31 / L 5);
  [drlg/room-tiles](../specs/drlg/room-tiles.md) (the OutRoom grids point at the room flags; their fill before the first
  `LvlSub` pass stays an input, new open question); [monsters/spawn](../specs/monsters/spawn.md) and
  [drlg/collision](../specs/drlg/collision.md) (the warp points of levels 4 and 44 are predicted; collision's `[L]` struck in
  part, counts unchanged). Four glossary terms. Review request: backlog spec-writer → architect, 2026-10-15.
- 2026-10-15 (architect): Phase 3 accepted with fixes; plan stays open. Spot checks: anchors resolve (sub_006817D0_A1PathSearch, DRLG_PresetMapScan, sub_006423D0_LevelWarpPointsBuild, sub_006424A0_LevelInit, sub_0066B6A0_LevelAdjLess), no `[L]` outside Open questions, `tools/drlg.py` named only as the reference model. Rulings: (1) drlg/outdoor stays `draft`: about 20 tables are named only by address and several sub-steps are only outlined, so a reimplementer cannot build the generators from the docs alone, which fails the review test (same standard as plan 0022). The spec-writer → reverser entry (a)–(d) is now blocking for `reviewed`; the reverser writes the table contents and the sub-steps into drlg/0008 with anchors, then the spec-writer fills them in. (2) The `[I]` → `[C]` moves in drlg/warps (A1, D1, E1, the Act I flag table) cite run:2026-10-15-drlg-outdoor and are accepted; warps stays `reviewed`. (3) The edit to drlg/collision (same outdoor warp-point note) is accepted. (4) Research map: drlg/outdoor at draft spec.

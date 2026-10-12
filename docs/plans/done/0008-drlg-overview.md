# 0008 — DRLG overview: generator dispatch, the room-seed chain and the room tile draws

> **Status:** done (closed 2026-10-12; all five phases accepted, fixes done)
> **Created:** 2026-10-11
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction

## TL;DR

**Question:** given a level's seed, how does the game turn it into DRLG rooms, and in what RNG call
order? `rng/seeds` already takes the seed tree down to the DRLG room (steps 1–6 `[C]`), but it leaves
one hole that every active-room seed, and so all population, depends on: the **k** room-seed draws of
step 6b, between the re-seed from room `+0x04` and the activation draw. This plan makes k a function of
the room's data, modelled bit-exact, and maps the layer above it: the dispatch on `Levels.DrlgType` into
the maze, preset and outdoor generators, the order in which each one creates rooms (and so takes level
draws), and how a preset room's `File1..6` is chosen. When it's done, `docs/specs/drlg/` holds an
overview spec and a room-tile spec, `tools/` has a model that predicts k (and so the active-room seed)
for every room it is given, and `rng/seeds` step 6b points at it instead of saying "k data-dependent,
not specified here". The generators' *internals* (maze layout, outdoor grid, substitutions, warps
placement) stay with their own research-map rows, behind boundary oracles.

## Context

Research-map row `drlg/overview` (core), status `not started`. The map gives it the k of
`rng/seeds` step 6 explicitly, and the plan 0003 close triage made "decoding k" a required *Done
when* ([backlog](../../backlog.md), reverser → architect entry, struck through at the 0003 close).

Dependencies and their confidence:

- `rng` **reviewed**: step, range and init `[C]` (run:2026-10-11-rng-emu).
- `rng/seeds` **reviewed** ([seeds.md](../../specs/rng/seeds.md)): game → act → level → DRLG room
  creation `[C]` (run:2026-10-11-seed-tree, 3102 room creations); the re-seed 6a, the existence of k
  and the activation draw 6c `[C]` (run:2026-10-11-seed-tree-p1: k = 50–376, never 0, over 157
  activations; server and client copies of one room get different k in 6 of 9 and 8 of 9 cases). k
  itself is `[L]` in its *Open questions*, owner `drlg/overview`. The dispatch on `DrlgType`
  (1 → `0x00673B10` maze, 2 → `0x00667430` preset, 3 → `0x00675320` outdoor) is `[I]`.
- Finding [drlg/0001](../../findings/drlg/0001-ds1-dt1-readers.md) **merged, `[I]`** (format gates
  `[C]`): the DS1 and DT1 readers; tile choice by a rarity-weighted draw on the **DRLG room seed
  `+0x14`** (`DRLG_PickTileByRarity` `0x0066D820`, a draw whenever the summed rarity is ≥ 1, even for
  one candidate); the room's DT1 list from `LvlTypes` `File 1..32` under the room mask `+0x50`
  (preset rooms: `LvlPrest.Dt1Mask`; outdoor rooms: a fixed per-level-type table; **maze rooms
  open**) plus three fixed files; the per-cell draw order (floor, wall plus the orientation-3/4
  partner, shadow) and the per-builder layer order. Its *Open questions* list the draw sites not yet
  modelled, which Phase 1 takes over whole.
- Formats: [ds1.md](../../formats/ds1.md), [dt1.md](../../formats/dt1.md) layout `[C]` (plan 0005 P1–2);
  `tools/ds1.py`, `tools/dt1.py` read every shipped file.
- Tables: [LvlPrest.md](../../tables/LvlPrest.md) layout `[C]`, every behavioural column `[L]`
  (`Files`, how one of `File1..6` is picked, `Dt1Mask` now `[I]` through drlg/0001);
  [Levels.md](../../tables/Levels.md) `DrlgType` (`+0x30`) and `LevelType` (`+0x34`) `[C]`.
  **No table doc yet** for `LvlTypes` (0x788-byte records, `File 1..32`) or `lvlmaze` (28 bytes):
  Phase 0 writes them.
- Method: the runtime harness (ADR-0003) reaches the Act I town, and `-act N` starts in any act's
  town; boundary oracles (ADR-0004) for out-of-scope callees that share a seed.
- Backlog entries this plan answers: architect ← archivist "LvlPrest semantics" (the `File1..6`
  pick, `Files`, `Dt1Mask`; the other columns go to `drlg/preset`), and the k-related part of the
  reverser → reverser "Plan: drlg/preset / drlg/collision" entry (draw sites, grid-prepare draws,
  maze-room mask, preset file-index draw).
- Leads: none behavioural. `src:siramy-ds1edit` covers DS1/DT1 layout only. The evidence rules note
  DRLG has little community coverage, so this plan has no cross-check phase; if a reverser finds
  and registers a DRLG source, the verdicts go in the finding's *Leads used*.
- Reaching maze levels: the harness starts in a town (ADR-0003 § Negative). Phase 0b gives it an
  edited save with waypoints set, so a run can travel to a maze level by waypoint. The same save
  **unblocks `monsters/spawn` runs**, which need the player outside town.
- Lane order: the reverser is on plan 0004 Phase 2; this plan's reverser phases start after it.
  Phases 0 and 0b run in the archivist lane, in parallel, at any time.

## Phases

### Phase 0 — Table docs for `LvlTypes` and `lvlmaze`
- **Owner skill:** archivist
- **What:** Document the two DRLG tables the code under this plan reads and that have no schema doc.
- **Outputs:** `docs/tables/LvlTypes.md`, `docs/tables/LvlMaze.md` (column → offset, layout tags),
  `docs/tables/README.md` links, and a `tools/` dump that prints a level type's `File 1..32` paths
  as the game prefixes them.
- **Done when:** both docs give every column's offset and width `[C]` against all records (36 and 81
  rows, record sizes 0x788 and 0x1C), the `File 1..32` stride (0x3C) agrees with
  `DRLG_LoadLvlTypes` as drlg/0001 reads it, and semantics beyond layout are `[L]` with the owner
  named (`drlg/maze` for `lvlmaze`).

### Phase 0b — Waypoint save for maze runs
- **Owner skill:** archivist
- **What:** Decode the D2S waypoint section (`WS`) and give `tools/d2s.py` a command that sets
  waypoints, so the harness can start a run that travels to a maze level by waypoint.
- **Outputs:** [d2s.md](../../formats/d2s.md) § Quests, waypoints, NPCs updated, a `tools/d2s.py`
  subcommand (e.g. `setwp <save> <difficulty> <waypoint…>`) that writes the bits and re-checksums, and
  `run:2026-10-11-d2s-waypoints` in `docs/formats/experiments.md` (format per evidence-rules
  § Experiments and ADR-0003).
- **Done when:** the `WS` layout (per-difficulty blocks, the bit field, bit → waypoint order) is `[C]`
  by data and the run, replacing the `[L]` lines in d2s.md; the command sets waypoints for one
  difficulty and leaves the checksum valid; and the run record shows an edited save loading, its
  waypoint menu listing exactly the waypoints set, and a travel to a maze level (e.g. the Catacombs in
  Act I) succeeding. The record names the save, the command line and the steps file, so Phase 2 and 3
  can reuse it.

### Phase 1 — The room-build draw sites and a static k model
- **Owner skill:** reverser
- **What:** Find every room-seed (`+0x14`) step between the re-seed (`sub_0066EE40_DrlgRoomReseed`)
  and the activation draw (`DRLG_RoomActivate`), for both room types and both act copies, and write k
  as an algorithm of the room's data.
- **Outputs:** `docs/findings/drlg/0002-room-build-draws.md`, `re/symbols.csv` rows (subsystem
  `drlg/overview`), the backlog entries it closes struck through.
- **Done when:** the finding states, each with an anchor and `[I]` or better:
  - **completeness**: the call graph under `0x0067D2D0`, `0x0067D710` (type 1) and `0x006667D0`,
    `0x00666AC0` (type 2) is enumerated by a recorded script, every function in it that contains the
    LCG multiplier (`0x6AC690C5`) or calls `RNG_Range`/an inlined step is listed with the seed it
    steps (room `+0x14`, level, act, other), and none is left unclassified;
  - every open draw site of drlg/0001 resolved: the bit-2 path `0x0066E940`, orientation 8/9
    `0x0066D9E0`, orientation 10/11 `0x0066E1C0`/`0x0066E360`/`0x0066E260`, the picks at `0x0066E073`,
    `0x0066E31B`, `0x0066E3FB`, `0x0066E6B2`, `0x0066E8F7`, the filler-floor test `0x0066B980`, the
    grid-prepare draws (`0x0066FF50`/`0x00670170` under type 1, `0x00667620` from
    `sub_00667890_PresetRoomLoadDs1`), each placed in the k window or outside it;
  - **k as pseudocode**: inputs (cell grids per layer, the room's DT1 list, the per-key rarity sums),
    loop order (builder layer order, rows then columns, per-cell order), and the draw condition at
    each site; any callee in the window that draws on `+0x14` and belongs to another row is named as a
    **boundary oracle** for Phase 2;
  - **server vs client**: why the two copies of one room can get different k (different DT1 list,
    grid, layer or path), with the branch that differs;
  - the maze-room mask (`+0x50` for rooms created by the maze generator) and the `RoomTile` fields
    `T[+0x18]`/`T[+0x20]` that gate the activation draw, from `rng/seeds` *Open questions*;
  - **overlap with Phase 3:** `0x00667620` steps room `+0x14` from `sub_00667890_PresetRoomLoadDs1`. If
    the preset file index turns out to be drawn on room `+0x14`, its draw moves into this phase (and
    into the k model), and Phase 3 only cross-refers to it.

### Phase 2 — Bit-exact k per room
- **Owner skill:** reverser
- **What:** Implement the Phase 1 model in `tools/` and check it against rooms activated under the
  harness, in the style of run:2026-10-11-seed-tree-p1.
- **Outputs:** `tools/drlg.py` (subcommand `roomk`; reads DT1s through `tools/dt1.py`, DS1s through
  `tools/ds1.py`, draws through `tools/rng.py`), `tools/gdb/drlg-roomk.gdb`,
  `docs/findings/drlg/experiments.md` with `run:YYYY-MM-DD-drlg-roomk`, tags raised in drlg/0002.
- **Logged:** Log at the re-seed `sub_0066EE40` (room seed, room id, copy); at each `sub_006707A0_LvlSubApply` entry and exit (seed, pass, grid dump at entry); at `sub_0066EE70` entry (grid dump, as a check); at activation (seed, and which neighbours have `+0x54 ≠ 0`) and at deactivation; and around the oracle `sub_0066D9E0_Orient89Unit` (seed in and out). LvlSub and the bit-2 path are modelled, not oracles. Split town, Blood Moor and maze cases into separate game entries to stay within ADR-0003's throughput limit. The required set includes a room whose `LvlSub` record has `Trials = −1`.
- **Done when:**
  - the model predicts k, and so the active-room seed, for **every** room activated in the run,
    server and client copies, with 0 mismatches; a missing line is a failure;
  - required cases: seeds 12345 and 777 (the p1 seeds, whose logged k the new run must repeat for the
    same rooms), the Act I town and the Blood Moor (type 1 and type 2 rooms in an outdoor level), and
    one `-act N` start in a preset town (Act II or IV), and **rooms of at least one maze level**,
    reached by waypoint with the Phase 0b save;
  - the k claims in drlg/0002 are `[C]` for outdoor, preset and maze rooms, with the run anchor and
    the oracles named;
  - **client copy:** `[C]` is required for the **server** copy, which gameplay uses. The client copy is
    checked too; if its k differs through a client-only path, that path stays `[I]` in drlg/0002 with
    an open question, and the server `[C]` stands;
  - the experiment record lets another session rerun it (command lines, steps and `.gdb` files,
    checker invocation).

### Phase 3 — Generator dispatch, room-creation order and the preset file choice
- **Owner skill:** reverser
- **What:** Map, for each `DrlgType`, how a level becomes rooms: what the generator entry draws from
  the level seed before, between and after its `DRLG_RoomCreate` calls, how a preset room's DS1 file is
  picked, and which act-seed consumers sit on the path.
- **Outputs:** `docs/findings/drlg/0003-generator-dispatch.md`, `re/symbols.csv` rows, a run in
  `docs/findings/drlg/experiments.md`, LvlPrest backlog entry answered.
- **Done when:**
  - the three entries (`0x00673B10`, `0x00667430`, `0x00675320`) and the room-creating functions
    under them (`sub_00667ED0_PresetRoomsCreate`, `sub_006750F0_OutdoorRoomsCreate`, the maze
    equivalent) are named `[I]`, each with: the room type it creates, the order of its room creations,
    and every other level-seed draw it makes, named as a **sub-generator entry point** (its internals
    belong to `drlg/maze`, `drlg/outdoor`, `drlg/preset`);
  - the preset file index (unless Phase 1 moved it there, because it draws on room `+0x14`; then
    this phase only cross-refers): the function that draws it, the seed it draws from, the range form and
    operand (`Files`, or the count of named files; the 81 disagreeing records explained), and the
    `Expansion` gate, `[I]`;
  - a run (Act I outdoor levels, a preset town by `-act N`, and at least one maze level reached by
    waypoint with the Phase 0b save) logs, per level created, the level seed after each draw and the chosen file index per
    preset room, with each sub-generator as a boundary oracle (entry/exit level seed); a checker
    reproduces the level-seed sequence and the file indices for every level the run creates, which
    raises those claims to `[C]` for all three generators;
  - warps and links only as far as `rng/seeds` step 3d already names them: the act-seed consumers
    (`sub_006772C0_LevelLinkBuild`, the nine `LinkPick` callbacks, the Act III code under
    `0x006789B0`) placed in the dispatch picture as entry points, nothing more;
  - nothing about the three generators' dispatch is left at `[I]` for want of a run.

### Phase 4 — Spec: `drlg/overview` and the room tile build
- **Owner skill:** spec-writer
- **What:** Turn drlg/0001–0003 into the DRLG overview and the room-tile spec, and close the k hole in
  `rng/seeds`.
- **Outputs:** `docs/specs/drlg/README.md` (act → level → room hierarchy, `DrlgType` dispatch, room
  creation order and the room-seed chain, entry points of the sub-generators and of later rows),
  `docs/specs/drlg/room-tiles.md` (DT1 list and mask, tile choice by rarity, the k algorithm, server
  vs client), an update to `docs/specs/rng/seeds.md` step 6b and its *Open questions*, glossary terms
  if new.
- **Done when:** `python3 -I tools/gate.py` passes; both specs carry `spec:` front matter with
  matching tag counts and no `[L]` outside *Open questions*; the k algorithm is pseudocode with RNG
  call order and integer widths, and a worked example reproduces one logged room from Phase 2;
  `seeds.md` 6b links the k algorithm instead of "not specified here"; and the architect's review
  passes, which moves `drlg/overview` to `reviewed` (or `draft spec` with listed fixes).

## Open questions

- ~~**Owner decision: how a run reaches a maze level.**~~ Decided 2026-10-11: an edited save with
  waypoints set (Phase 0b); maze rooms are in the Phase 2 and 3 required cases.
- **Split by generator, or by mechanism?** This plan takes the mechanisms common to all generators
  (dispatch, room creation order, tile build, k) and leaves each generator's own layout logic to
  `drlg/preset`, `drlg/maze` and `drlg/outdoor`, which already have map rows. If Phase 3 finds a
  generator whose room-creation order cannot be stated without its internals (likely the maze, whose
  layout probably decides the order), the oracle carries it and the later plan replaces the oracle.
  No ADR: the map already splits this way.
- **Preset file choice may sit inside the k window.** `0x00667620` steps room `+0x14` from the DS1
  loader; if the file index is a room-seed draw it belongs to Phase 1, and Phase 3 only cross-refers
  (instruction in both phases).
- ~~**Server vs client k.**~~ Decided 2026-10-11: server-copy `[C]` is enough (gameplay uses it,
  `rng/seeds` step note 6); a client-only path that changes k stays `[I]` with an open question
  (Phase 2 *Done when*).
- **Out of scope, explicitly:** population (objects, monsters, the pass `sub_0054EC90_RoomPopulate`
  and its active-room draw) → `monsters/spawn`, `objects`; collision bits → `drlg/collision`;
  substitution cells and groups, `LvlPrest` columns other than the file pick and `Dt1Mask` →
  `drlg/preset`; warp placement and `LvlWarp` → `drlg/warps`; the act `+0x094`/`+0x484` tomb pair and
  the Act III bit → the quest work.
- Later plans this one sets up: `drlg/preset`, `drlg/maze`, `drlg/outdoor` (each replaces its Phase 3
  oracle and re-runs the recorded logs), then `drlg/collision`.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-11 — Approved (human), with owner decisions.** (1) Maze runs: new archivist Phase 0b
  (waypoint save), maze rooms required in Phases 2 and 3. (2) Client copy: server `[C]` suffices; a
  client-only k path stays `[I]`. (3) Phase 0 kept. (4) The preset file pick moves from Phase 3 to
  Phase 1 if it draws on room `+0x14`. No phase started yet.
- **2026-10-11 — Phase 0 done (archivist), awaiting architect review.** [LvlTypes.md](../../tables/LvlTypes.md)
  (36 records × 0x788; 34 compiled columns: `File 1..32` `char[60]` at `+0x3C·(k−1)`, `Act` `+0x780`,
  `Expansion` `+0x784`; `Name`, `Id`, `Beta` not compiled) and [LvlMaze.md](../../tables/LvlMaze.md)
  (81 records × 0x1C; 7 compiled u32 columns `Level`, `Rooms`, `Rooms(N)`, `Rooms(H)`, `SizeX`, `SizeY`,
  `Merge`; `Name`, `Beta` not compiled). Layouts in `tools/excel_layouts.py`; `excel_bin.py diff` gives
  0 mismatches (1224 and 567 cells) and `unknown` finds no uncovered byte, so every offset and slot width
  is `[C]` by data. The `File 1..32` stride matches `DRLG_LoadLvlTypes` / `DRLG_LevelDt1ListBuild` as
  drlg/0001 reads them (`[C]`: code anchor plus data). `python3 -I tools/dt1.py lvltypes <root> <Id>`
  prints one type's slots with mask bit, offset and prefixed path. Column meanings stay `[L]`
  (owners `drlg/overview`, `drlg/maze`) except the mask-bit → `File i+1` mapping and the load-time
  path rewrite, which cite drlg/0001 `[I]`. Surprises: three level types have gaps in `File 1..32` (slot
  index = mask bit, not a count); `lvlmaze` has 11 rows for non-maze levels (10 `DrlgType` 2, one
  `Level` 0) and every `DrlgType` 1 level has a row; the `"%s\%s"` base string is not anchored (the dump
  tool's default is `[L]`). Leads: none fetched; derived from data. Backlog → reverser for the rest.
- **2026-10-11 — P0 reviewed (architect), accepted with fixes 1–4; applied.** (1) LvlPrest: integer
  columns are 4-byte slots, `u32`/`s32` is the slot decode only, signedness `[L]`. (2) LvlTypes and
  LvlMaze: the read-type sentence is `[L]`, the `u32` is the slot decode only. (3) Backlog → reverser
  item (e): drlg/0001 § Data touched and its two readings of the type source (`:222` vs `:231`).
  (4) `tools/dt1.py lvltypes` rejects an out-of-range Id (exit 2).
- **2026-10-11 — Phase 0b (archivist): decode and tool done, in-game run pending.** `WS` layout in
  [d2s.md § Waypoints](../../formats/d2s.md#waypoints-ws): header (`WS`, u32 1, u16 80) and three
  24-byte blocks at `0x281`/`0x299`/`0x2B1` (`02 01`, 5-byte bit field, 17 zero bytes) are `[C]` by
  byte accounting over the 21 full samples. **No sample varies**: every one is a fresh character with
  only bit 0 set in all three blocks, so bit → waypoint order (bit *n* = `levels.txt` `Waypoint` *n*;
  Catacombs Level 2 = bit 8), the field width (5 bytes) and the block → difficulty order stay `[L]`
  (`src:d2s-community-format`, WS section read this session). `tools/d2s.py setwp` added and checked on
  copies (`cmp -l`: only the field and checksum bytes change; checksum, survey, dump pass). The run is
  pre-written as [the pending record](../../formats/experiments.md#run2026-10-11-d2s-waypoints) (saves
  A `0,2,6,8` with a travel to Catacombs Level 2, B one or two bits per act); it needs the harness,
  held by 0004·P2. Done-when not met until it runs.
- **2026-10-11 — Phase 0b run done (archivist).** [run:2026-10-11-d2s-waypoints](../../formats/experiments.md#run2026-10-11-d2s-waypoints)
  executed as written. Save A (`setwp … normal 0,2,6,8`) loaded, and its waypoint menu (one tab, I) listed
  exactly Rogue Encampment, Stony Field, Jail Level 1 and Catacombs Level 2 as travelable, with the other
  five Act I rows greyed. A travel to **Catacombs Level 2** worked (the automap names it). Save B
  (`0,9,12,18,26,27,29,30,35,38`) showed only tab I, headed "No Other Waypoints Activated", and no tabs
  II–V (no quest progress). Both re-saved files keep the `WS` section byte for byte, bit 38 included.
  New steps file `tools/gdb/d2s-wp-open.steps` (after `enter-sp.steps`, `--seed 1`) replayed unchanged
  for B. Promoted to `[C]` in [d2s.md](../../formats/d2s.md#waypoints-ws): bits 0–8 → the Act I waypoints
  (LSB first across bytes `+0x02`/`+0x03`), and `0x281` = the normal block. Still `[L]`: bits 9–38, the
  5-byte width (only observed round-tripping), the nightmare/hell order, and bit 0 forcing (not tested).
  So the Done-when's "bit → waypoint order `[C]`" holds for Act I only; that is for the architect's
  review. Saves dir restored, sha256-identical; harness left clean. Two orphan `d2run.py` timers
  from finished plan 0004 runs (tc-run3/4, whose games had exited) were killed first: their delayed
  `wineserver -k` would have cut this run.
- **2026-10-11 — P0b reviewed (architect): accepted with fixes 1–2, Done-when narrowed.** What P2/P3 need is [C]: bits 2, 6, 8 (Stony Field, Jail 1, Catacombs 2), the LSB-first span, the normal block at 0x281, setwp, and tools/gdb/d2s-wp-open.steps with save smpsor-a. Bits 0, 1, 3, 4, 5, 7 and 9–38, the 5-byte width, the NM/Hell order and bit-0 forcing stay [L] in d2s.md Open questions; a save-C addendum run is pending (harness), and plan 0004 Phase 2's Cold Plains travel is expected to settle bit 1.
- **2026-10-11 — Phase 1 done (reverser), awaiting architect review.** [drlg/0002](../../findings/drlg/0002-room-build-draws.md)
  Symbols use
  subsystem `drlg/overview` (the research-map row; the orchestrator suggested `drlg/rooms`).
  Completeness: `re/ghidra_scripts/RngCallGraph.java` (`tools/ghidra.sh rngcallgraph`) over the four roots plus
  the grid-op table `0x00749BAC` gives 657 functions, 4 RNG-bearing, all room `+0x14`, 0 unclassified
  against `re/rngclass/drlg-room-build.txt`; 60 indirect calls in library code checked by hand. Findings:
  (1) type-1 rooms draw **`LvlSub` substitutions** in the grid prepare (`0x006707A0` → `0x0066FF50`/`0x00670170`),
  a k term the plan did not name; (2) every drlg/0001 site is in the window except `0x00667620`, which
  runs before the re-seed (draws discarded), and **the preset file index is not a room-seed draw**, so it
  stays with Phase 3; (3) server/client k differ through the neighbour-dependent bit-2 path; (4) RoomTile
  `T[+0x18]`/`+0x20` are the final wall/floor counts; (5) maze rooms take `LvlPrest.Dt1Mask` through
  `0x00673A60` → `sub_00667ED0_PresetRoomsCreate`. Oracles named for Phase 2: `0x006707A0`, `0x0066D9E0`,
  `0x0066E940`. Open: `0x006663C0` (client-only, pre-window), the unit/merge tables to dump, the `LvlSub`
  table doc (backlog → archivist).
- **2026-10-11 — P1 reviewed (architect): accepted with fixes 1–8.** k formula corrected (no draw on the (10,0,0) fallback; 40-candidate cap); LvlSub and the bit-2 path are modelled in P2, only Orient89Unit is an oracle; the preset file pick stays in P3; finding name 0002-room-build-draws.md kept.
- **2026-10-11 — Phase 2 done (reverser), awaiting architect review.** [run:2026-10-11-drlg-roomk](../../findings/drlg/experiments.md#run2026-10-11-drlg-roomk):
  `tools/drlg.py roomk` (model of drlg/0002, DT1s through `tools/dt1.py`, LvlSub DS1s through `tools/ds1.py`,
  draws through `tools/rng.py`) and `tools/gdb/drlg-roomk.gdb` (+ `drlg-roomk.py`, gdb Python) predict **all 520
  activations** of six game entries, server and client, with 0 mismatches over 8776 checks (seed at every LvlSub
  pass, type init, RACT, AROOM; modelled grids against the logged ones; neighbour seeds): seeds 12345 and 777 in
  the Act I town, the Blood Moor (type 1 and 2), Act II town by `-act 2`, and maze levels (Den of Evil; Catacombs
  Levels 2–4 by waypoint, 52 server / 43 client maze activations in one entry), k = 0..388. The p1 rooms repeat
  their k (45/45, 40/40). `Trials = −1` (records 6, 9) exercised. drlg/0002's k claims are `[C]`; oracle
  `sub_0066D9E0_Orient89Unit` only (526 calls, its `Range(3)` never reached). Corrections to drlg/0002: the merge
  re-pick `0x0066E8F7` draws on the **neighbour's** seed (not in this room's k); hidden-warp picks use
  orientation 0; every room border carries bit 2 (type 2 also bit 7, written into the cached DS1), so the bit-2
  path is the common case. Surprise: `Act1/Outdoors/Trees.ds1` (LvlSub rec 11) is read 12 bytes past its end;
  the last group held zeros in 26 of 27 loads and heap garbage once, so k can depend on uninitialized memory
  (open question for the spec). Inputs the model takes from the log as run-time state: grids (type 2 at type
  init, type 1 at the first LvlSub pass), DT1 list, neighbour list/state, warp nodes and warp ids, in-memory
  LvlSub groups. Maze runs were played by hand (owner and xdrive), not by a steps file. Also fixed the
  `d2run.py` driver bug (plan 0011 Phase 1 item; see that plan's log). Backlog → architect (review), → archivist
  (LvlWarp table doc, leveldefs warp ids).
- **2026-10-12 — P2 reviewed (architect): accepted with fixes F1–F3.** Rerun in the branch worktree:
  `roomk` over the six logs gives 520 activations, 8776 checks, 0 mismatches; `p1cmp` 45/45, 45/45, 40/40; log
  sha256 prefixes match the record; gate green. The checker never resyncs a seed: every room starts from
  `init(+0x04)`, LSUB/LSUBX/TINIT/RACT/AROOM and built neighbours' seeds are asserted, each O89 entry seed is
  asserted and unconsumed O89 lines fail. Anchors spot-checked with r2: `0x0066E8F2` loads ECX from `arg_ch` (the
  neighbour), `0x0066E3F7` zeroes EDX (orientation 0), `0x0067D4ED` passes `or 4`, and RACT `0x0064233A` sits
  behind the `T[+0x18] || T[+0x20]` test at `0x00642308`. Judgments:
  (a) **Inputs from the log.** These are inputs, not oracles. ADR-0004 governs callees that share the seed, and
  evidence rule 4 asks for identical outputs "for recorded inputs". So k is `[C]` *as a function of the inputs
  listed in drlg/0002 § k as pseudocode*, which the finding already states. That holds for the inputs made by
  code another row owns: the type-1 OutRoom grids (`drlg/outdoor`), the neighbour lists (`0x0066C370`,
  generators), the built state (activation order, which is gameplay), and the warp nodes and the act `+0x90`
  override (`drlg/warps`). It does **not** hold for the type-2 grid assembly. `0x006667D0` is one of this
  plan's four roots, and without it a reimplementer can't get a preset room's k from data, so it is F1 and
  must land before Phase 4. The DT1 list is cheap to compute and check, so it is F2.
  (b) **Hand-played maze entries** meet ADR-0003. The check is mechanical over the kept logs (sha256 in the
  record), the claim is "every activated room is predicted", and any walk that reaches Catacombs 2–4 tests the
  same claim, which the Deviations line says. ADR-0004 makes these logs the test set for `drlg/preset` and
  `drlg/maze`, so they must not be deleted. No ADR now. If plan 0011 Phase 2 (human play) needs the same
  allowance, write one ADR on played runs then.
  (c) **Corrections accepted.** The neighbour-seed re-pick is `[C]` (code, plus 354 re-picks checked through
  the neighbour's seed at a later TINIT). Phase 4 must say that a DRLG room's `+0x14` keeps moving after its
  own activation when later neighbours merge into it. The orientation-0 hidden-warp picks are `[C]`. The
  border bit is `[C]` for type 1 only. The type-2 `0x84` write is downgraded to `[I]` until F1.
  (d) **`Trees.ds1` overread.** It stays an open question for Phase 4. The spec states zero fill as the
  reimplementation's rule (`[C]` that zeros reproduce every observed draw), marks the original as reading
  uninitialised heap, and notes that the one garbage load made no group draw on it.
  (e) **Unexercised paths stay `[I]`**: the `Orient89Unit` `Range(3)`, the `(10,0,0)` fallback, ApplyAll and
  the RoomTile free. The checker counts a TINIT without RACT as a failure, so the "no tiles, no activation
  draw" case would show up as a mismatch rather than be predicted. Not a fix: no such room occurred.
  **Fixes:** F1 (reverser, before P4): model the type-2 prepare `0x006667D0` in `tools/drlg.py` (DS1 views
  through `tools/ds1.py` at the preset origin, the `0x84` border written into the cached DS1, and whether
  that write persists across rooms of one preset and across act copies; `0x006663C0` if it touches the grids).
  Check it against the logged TINIT grids of the six logs (no new run). Then the type-2 border line goes back
  to `[C]`. F2 (reverser, before P4): compute each room's DT1 list from `LvlTypes` `File i+1` under `+0x50` plus
  the three fixed files, and check it against the logged list. This raises the DT1-list rule and the maze-room
  mask (`LvlPrest.Dt1Mask`) to `[C]`. F3 (applied in this review): drlg/0002 tags. The type-2 border write is
  `[I]`, the RoomTile free is `[I]`, the `Orient89Unit` row is split into entry seed `[C]` and draw `[I]`, and
  the type-2 grid open question now has owner `drlg/overview`. Also accepted: the `d2run.py` driver fix (plan 0011
  P1 item). Phase 3 (reverser) can start now; F1 and F2 gate Phase 4 only.
- **2026-10-12 — P2 fixes F1 and F2 done (reverser), no new game run.** Addendum to
  [run:2026-10-11-drlg-roomk](../../findings/drlg/experiments.md#run2026-10-11-drlg-roomk): `roomk` over the six logs now
  gives 520 activations, **11208 checks, 0 mismatches** (was 8776). F1: `tools/drlg.py` models
  `sub_006667D0_PresetRoomGridPrepare` (grids are views of the DS1 layers at the room's offset in the preset, stride
  preset w + 1; `0x84` on the borders of wall 0, every floor and the shadow; `i << 18` on wall/floor layers i ≥ 1;
  orientation untouched) and reproduces the grids of all 464 type-2 rooms. Each write is necessary (mutation check).
  The cache question: `DS1_LoadCached` is one process-wide list, so the write persists and both act copies and all
  instances of a file share it `[I]`. It cannot be seen, though: persistent and fresh buffers give identical grids in
  every room `[C]`, because all writes are idempotent OR-s that each room repeats on its own borders.
  `0x006663C0` (client only) reads floor layer 0 and adds object preset units; it writes no grid `[I]`, and
  the client grids match the model `[C]`. The type-2 border line in drlg/0002 is back to `[C]`. F2: the DT1 list
  rule is `[C]` in all 520 rooms, and so is the maze (and every preset) room mask = `LvlPrest.Dt1Mask` (464 rooms,
  92 on `DrlgType` 1 levels). Surprise: an outdoor room's mask is the level-type value **OR the `Dt1Mask` of the
  SubType `LvlSub` records picked by `sub_006706A0_LvlSubRoll`**, a `% 100 < Prob` draw per record on the room seed
  at room creation (before the re-seed, so not in k; a room-creation draw for Phase 3). That corrects drlg/0001's
  mask table (`[C]` for level type 2, 56 rooms). The DS1 file index is not in the P2 logs; the checker identifies it
  by reproduction (457 unique, 7 with identical candidates), and Phase 3 logs it. Backlog: archivist (LvlTypes
  prefix `DATA\GLOBAL\TILES\`, LvlSub `Dt1Mask`/`Prob`, LvlPrest `Dt1Mask`).
- **2026-10-12 — Phase 3 (reverser): static work and scripted runs done; the waypoint maze run is pending (owner).**
  [drlg/0003](../../findings/drlg/0003-generator-dispatch.md), [run:2026-10-12-drlg-gen](../../findings/drlg/experiments.md#run2026-10-12-drlg-gen):
  `tools/gdb/drlg-gen.gdb` (+ `drlg-gen.py`) and `python3 -I tools/drlg.py gen` over five game entries (Act I town for
  seeds 12345 and 777, the Blood Moor walk, `-act 2`, `-act 4`) give **14545 checks, 0 mismatches**. That covers 149 level
  creations and 32 builds (maze 4, preset 12, outdoor 16), 1858 modelled room creations and 960 preset instances.
  Findings: (1) **two dispatches**: `DRLG_LevelCreate` → `0x00673B10`/`0x00667430`/`0x00675320`, then
  `sub_006424A0_LevelInit` **re-seeds** the level with the same `Init(base + id)` → `sub_00673B30_MazeLevelBuild` /
  `sub_00668100_PresetLevelBuild` / `sub_00675360_OutdoorLevelBuild`, and all room-creating draws come after it.
  (2) **Preset file index**: `sub_00666ED0_PresetInstanceCreate` draws `Range(level seed, Files)` on the level seed (not a
  room seed). It is replaced by the level's index (link value for levels 1 and 40, else the create-time `RangeB` on the same
  start value), by the outdoor cell (bits 16–19), or by the maze cell or a per-def rotation (`sub_006738C0_MazePresetFile`).
  `Files` is the operand, and the 81 disagreeing records are override cases. No `Expansion` gate. (3) **Order**: preset 8×8
  split rows-then-columns; outdoor cells rows-then-columns; maze conversion in room-list order (newest first) after the
  generator, which frees its own rooms. (4) `sub_00667620_PresetUnitDropRolls` also runs at build time, **on the level seed**
  (oracle, 52 calls, 2 drew). (5) `sub_006706A0_LvlSubRoll` reproduced 466 times. Oracles: the maze generator window, the
  outdoor act generators, `sub_00667620`. Call graph under both dispatch roots: 56 RNG functions, all classified
  (`re/rngclass/drlg-gen.txt`). Maze coverage is from Den of Evil and Sewers Level 1, both built on the way. The plan's
  waypoint run (Catacombs, Phase 0b save) failed at the main menu on its one scripted try, so it is **pending for the
  owner**; the command line and save are in the run record. Done-when: dispatch, order, other level-seed draws `[C]`
  for all three generators; file index `[C]`; act-seed consumers placed as entry points `[I]`; the waypoint maze case is open.
- **2026-10-12 — P2 fixes F1–F2 and Phase 3 reviewed (architect): accepted; the Catacombs confirmation run is
  pending.** Rerun on the branch: `roomk` gives 520 activations, 11208 checks, 0 mismatches (8776 before F1–F2);
  `gen` over the five logs gives 14545 checks, 0 mismatches; gate green. **F1:** the type-2 prepare is modelled
  and reproduces the logged grids of all 464 type-2 rooms. The model is discriminating: dropping any one write gives
  760–928 mismatches. Note: drlg-roomk.gdb doesn't log the file index, so `check_preset_grids` picks the DS1 among the
  record's at most 6 files by reproduction, and requires every room of one instance to agree (457 unique, 7 with 2–3
  identical candidates). Acceptable for `[C]` on the prepare. The Phase 4 worked example should use a room whose file
  the `gen` model predicts, so the two checks meet. Cache persistence: shared buffer `[I]`, no effect on any grid
  `[C]`. `0x006663C0` writes no grid `[I]`. **F2:** the DT1 list holds in all 520 rooms, preset and maze `+0x50` =
  `Dt1Mask` `[C]`. The drlg/0001 correction (outdoor mask ORs the `Dt1Mask` of the `LvlSubRoll` picks) is checked in
  56 rooms and accepted. So Phase 2 is fully closed. **Phase 3:** checked in r2: `0x00666F1C` reads `Files` at `LvlPrest +0x40`, then the
  inlined step and an unsigned `div` (mask for powers of two); `0x00673909` is the maze-def `switch`. The `gen` checker
  asserts the level seed into every oracle (`sub_00667620`, maze and outdoor windows) and fails if a build ends inside a
  window, so the ADR-0004 discipline holds. The double `Init(base+id)`, which makes the create-time draw irrelevant to
  the room sequence, and the three generators' room order are `[C]`. The file index is `[C]` (960 instances), with the 72
  unseen override records `[I]` as stated. **Maze case:** the Done-when asked for a maze level reached by waypoint, and
  the scripted try failed at the menu. The maze generator path itself is covered by two maze levels the runs built
  on the way (Den of Evil, Sewers Level 1: 16 first uses, 18 rotations of `MazePresetFile`), so the maze claims stand
  at `[C]`. The Catacombs run (run:2026-10-12-drlg-gen § Pending) stays a **confirmation run for the owner**. It
  doesn't block Phase 4. If it mismatches, the maze tags are demoted and Phase 4 is revisited. **Next:** Phase 4
  (spec-writer) can start.
- **2026-10-12 — Catacombs confirmation run done (owner); Phase 3 fully done.** Owner-played entry of
  [run:2026-10-12-drlg-gen](../../findings/drlg/experiments.md#run2026-10-12-drlg-gen) (save `smpsor-l50`, waypoint to
  Catacombs Level 2, down to Level 4): `drlg.py gen` gives 6608 checks, **0 mismatches**. Before that, a checker fix
  (`6f335bd`): the maze file-rotation counters now reset at every LevelInit build, because the game rebuilds an unloaded
  level and repeats the same draws. The maze tags in drlg/0003 stand. Two `[C]`/`[I]` lines were added: per-build counters, a
  list at level `+0x1CC` freed by `sub_00642010_LevelUnload`, and identical rebuilds.
- **2026-10-12 — Phase 4 written (spec-writer), awaiting architect review.** [drlg/overview](../../specs/drlg/README.md)
  (`status: draft`, C 53 / I 19 / L 0): both `DrlgType` dispatches and the `LevelInit` re-seed, the level-seed draws of the
  three generators in order, the preset file index (`Range(Files)`, overrides, maze rotation per build), the 8 × 8 split and the
  outdoor and maze room order, `LvlSubRoll`, the act-seed consumers and the three oracles as entry points.
  [drlg/room-tiles](../../specs/drlg/room-tiles.md) (`status: draft`, C 67 / I 32 / L 0): activation order and the k window, the
  DT1 list and mask, the pick and its draw rule, the type-1 `LvlSub` passes and the type-2 prepare, the builders, the per-cell
  decision, the bit-2 scan/new/merge, warps, `Orient89Unit` as oracle, the activation draw, and § k. `rng/seeds` step 6b links
  § k; step 4's dispatch is `[C]` (drlg/0003); step note 6 states k and the `RoomTile` counts; its k and `RoomTile` `[L]`s are
  closed (C 54 / I 17 / L 6). Glossary: seven terms. **Worked examples**: Den of Evil (level 8) for map seed 12345, from the
  re-seed through the maze oracle's exit to the preset conversion (defs 98 kept, 83 kept with `Range(2) = 1` →
  `CaveWPre2.ds1`, 58 rotated), ending at the room `+0x04 = 8E258975`; that room (client copy, roomk-12345-bloodmoor) has k = 15,
  all floor picks of key (0, 5, 0), with all 15 seeds listed, and the active-room seed `Init(2FE647C1)`. The two checks meet:
  `gen` predicts its file from a modelled draw, and the `roomk` reproduction finds that file and no other. Reproduce with
  `python3 -I tools/drlg.py roomk workspace/logs/roomk-12345-bloodmoor.log -v | grep 02d8f600` and
  `python3 -I tools/drlg.py gen workspace/logs/gen-12345-bloodmoor.log` (both 0 mismatches). The server/client contrast uses
  the `rng/seeds` example room (`F923BEE2`: server k = 64, client k = 55). Review caveats applied: `Trees.ds1` zero fill `[C]`,
  heap read `[I]`; the neighbour re-pick moves a built room's `+0x14`; rotation counters per `LevelInit` build, rebuilds
  identical; `Orient89Unit`'s `Range(3)`, the `(10,0,0)` fallback, `ApplyAll` and the RoomTile free `[I]`. **Found while
  writing:** in the six roomk logs no merge reached the orientation remap or the orientation-3 branch of
  `sub_0066E740_Bit2TileMerge` (every non-floor merge met flag `0x1`), and `g_Bit2OrientRow` reads 206–255 for eight
  orientations, so those branches are `[I]` in the spec though drlg/0002's row is `[C]`. Open questions: 6 in room-tiles, 6 in
  overview. Backlog → reverser (merge tables, `LvlSubRoll` with −1, outdoor cell position, RoomTile free), → architect (review).
- **2026-10-12 — Phase 4 reviewed (architect): accept; plan closed.** Checked: gate green; `drlg.py roomk` on
  roomk-12345-bloodmoor reruns 88 activations, 0 mismatches, and the worked example (Den of Evil, room 02d8f600, client
  copy) matches at TINIT `8E258975:0000029A`, RACT `6CC2E5DB:673E363A` with k 15 and AROOM `Init(2FE647C1)`; its DS1
  file comes from the modelled `Range(2)` of `gen` (3614 checks, 0 mismatches), not from roomk's candidate search. All
  60 `fn:` anchors of the two specs resolve in `re/symbols.csv`; r2 at 0x0066DD02 (PickTile, then the orientation-4
  partner), 0x0066E8F7 (the `+0x14` re-pick) and `DRLG_LevelCreate`. The five review caveats are in the specs with the
  asked tags. The spec-writer's own catch is upheld: the Bit2 merge orientation remap and orientation-3 branch were
  never reached in the six roomk logs, so the spec has them at `[I]`; drlg/0002's `[C]` on that row is over-tagged and
  goes back to the reverser with the merge-table layout question (backlog spec-writer → reverser, 2026-10-12, (a)).
  `drlg/overview` and `drlg/room-tiles` are `reviewed`; `rng/seeds` 6b links the k algorithm. Remaining open points
  (merge tables, `LvlSubRoll` with −1, outdoor cell position, re-activation after `RoomTileFree`, the three oracles)
  belong to the reverser backlog and the rows `drlg/preset`, `drlg/maze`, `drlg/outdoor`, `drlg/warps`, `objects`.

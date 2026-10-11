# 0008 — DRLG overview: generator dispatch, the room-seed chain and the room tile draws

> **Status:** draft (awaiting owner approval)
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
when* ([backlog](../backlog.md), reverser → architect entry, struck through at the 0003 close).

Dependencies and their confidence:

- `rng` **reviewed**: step, range and init `[C]` (run:2026-10-11-rng-emu).
- `rng/seeds` **reviewed** ([seeds.md](../specs/rng/seeds.md)): game → act → level → DRLG room
  creation `[C]` (run:2026-10-11-seed-tree, 3102 room creations); the re-seed 6a, the existence of k
  and the activation draw 6c `[C]` (run:2026-10-11-seed-tree-p1: k = 50–376, never 0, over 157
  activations; server and client copies of one room get different k in 6 of 9 and 8 of 9 cases). k
  itself is `[L]` in its *Open questions*, owner `drlg/overview`. The dispatch on `DrlgType`
  (1 → `0x00673B10` maze, 2 → `0x00667430` preset, 3 → `0x00675320` outdoor) is `[I]`.
- Finding [drlg/0001](../findings/drlg/0001-ds1-dt1-readers.md) **merged, `[I]`** (format gates
  `[C]`): the DS1 and DT1 readers; tile choice by a rarity-weighted draw on the **DRLG room seed
  `+0x14`** (`DRLG_PickTileByRarity` `0x0066D820`, a draw whenever the summed rarity is ≥ 1, even for
  one candidate); the room's DT1 list from `LvlTypes` `File 1..32` under the room mask `+0x50`
  (preset rooms: `LvlPrest.Dt1Mask`; outdoor rooms: a fixed per-level-type table; **maze rooms
  open**) plus three fixed files; the per-cell draw order (floor, wall plus the orientation-3/4
  partner, shadow) and the per-builder layer order. Its *Open questions* list the draw sites not yet
  modelled, which Phase 1 takes over whole.
- Formats: [ds1.md](../formats/ds1.md), [dt1.md](../formats/dt1.md) layout `[C]` (plan 0005 P1–2);
  `tools/ds1.py`, `tools/dt1.py` read every shipped file.
- Tables: [LvlPrest.md](../tables/LvlPrest.md) layout `[C]`, every behavioural column `[L]`
  (`Files`, how one of `File1..6` is picked, `Dt1Mask` now `[I]` through drlg/0001);
  [Levels.md](../tables/Levels.md) `DrlgType` (`+0x30`) and `LevelType` (`+0x34`) `[C]`.
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
- Lane order: the reverser is on plan 0004 Phase 2; this plan's reverser phases start after it.
  Phase 0 can run in the archivist lane at any time.

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

### Phase 1 — The room-build draw sites and a static k model
- **Owner skill:** reverser
- **What:** Find every room-seed (`+0x14`) step between the re-seed (`sub_0066EE40_DrlgRoomReseed`)
  and the activation draw (`DRLG_RoomActivate`), for both room types and both act copies, and write k
  as an algorithm of the room's data.
- **Outputs:** `docs/findings/drlg/0002-room-tile-draws.md`, `re/symbols.csv` rows (subsystem
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
    `T[+0x18]`/`T[+0x20]` that gate the activation draw, from `rng/seeds` *Open questions*.

### Phase 2 — Bit-exact k per room
- **Owner skill:** reverser
- **What:** Implement the Phase 1 model in `tools/` and check it against rooms activated under the
  harness, in the style of run:2026-10-11-seed-tree-p1.
- **Outputs:** `tools/drlg.py` (subcommand `roomk`; reads DT1s through `tools/dt1.py`, DS1s through
  `tools/ds1.py`, draws through `tools/rng.py`), `tools/gdb/drlg-roomk.gdb`,
  `docs/findings/drlg/experiments.md` with `run:YYYY-MM-DD-drlg-roomk`, tags raised in drlg/0002.
- **Logged per activation** (breakpoints at the re-seed and before the activation step, as in the p1
  run): room pointer, act copy (server/client), level id, room type `+0x48`, `+0x04`, mask `+0x50`,
  the DT1 list at `+0x68` (file names through the runtime name pointer, drlg/0001 § DT1 load), the
  room's cell grids as a memory dump (type 1) or its DS1 and origin within it (type 2), the seed at
  the activation step, and entry/exit seeds plus return value of every oracle Phase 1 named. No
  per-draw breakpoint: the throughput limit in ADR-0003 rules out a stop per tile pick.
- **Done when:**
  - the model predicts k, and so the active-room seed, for **every** room activated in the run,
    server and client copies, with 0 mismatches; a missing line is a failure;
  - required cases: seeds 12345 and 777 (the p1 seeds, whose logged k the new run must repeat for the
    same rooms), the Act I town and the Blood Moor (type 1 and type 2 rooms in an outdoor level), and
    one `-act N` start in a preset town (Act II or IV), at least one room where the two act copies
    differ;
  - the k claims in drlg/0002 are `[C]` for the cases covered, with the run anchor and the oracles
    named; room kinds no run reached (maze rooms unless the run gets there, see *Open questions*)
    stay `[I]` and are listed as such;
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
  - the preset file index: the function that draws it, the seed it draws from, the range form and
    operand (`Files`, or the count of named files; the 81 disagreeing records explained), and the
    `Expansion` gate, `[I]`;
  - a run logs, per level created, the level seed after each draw and the chosen file index per
    preset room, with each sub-generator as a boundary oracle (entry/exit level seed); a checker
    reproduces the level-seed sequence and the file indices for every level the run creates, which
    raises those claims to `[C]` for the generators covered;
  - warps and links only as far as `rng/seeds` step 3d already names them: the act-seed consumers
    (`sub_006772C0_LevelLinkBuild`, the nine `LinkPick` callbacks, the Act III code under
    `0x006789B0`) placed in the dispatch picture as entry points, nothing more;
  - generators no run reached stay `[I]`.

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

- **Owner decision: how a run reaches a maze level.** The harness starts in a town. Options:
  (a) a longer steps file that walks out and finds a maze entrance (seed-dependent, brittle);
  (b) an edited save with waypoints set, which needs the `WS` bit layout (`[L]` in
  [d2s.md](../formats/d2s.md)) checked and a `tools/d2s.py` setter (an archivist phase, and it also
  unblocks `monsters/spawn` runs, ADR-0003 § Negative); (c) accept maze rooms at `[I]` in this plan
  and let `drlg/maze` raise them. The draft assumes (c) with (b) as an optional archivist phase if the
  owner wants maze rooms `[C]` here.
- **Split by generator, or by mechanism?** This plan takes the mechanisms common to all generators
  (dispatch, room creation order, tile build, k) and leaves each generator's own layout logic to
  `drlg/preset`, `drlg/maze` and `drlg/outdoor`, which already have map rows. If Phase 3 finds a
  generator whose room-creation order cannot be stated without its internals (likely the maze, whose
  layout probably decides the order), the oracle carries it and the later plan replaces the oracle.
  No ADR: the map already splits this way.
- **Preset file choice may sit inside the k window.** `0x00667620` steps room `+0x14` from the DS1
  loader; if the file index is a room-seed draw it belongs to Phase 1, and Phase 3 only cross-refers.
- **Server vs client k.** Gameplay uses the server copy (`rng/seeds` step note 6). If the difference
  is a client-only path (rendering-side layers), the spec states it but a reimplementation needs only
  the server model; the owner may accept a server-only `[C]` with the client at `[I]`.
- **Out of scope, explicitly:** population (objects, monsters, the pass `sub_0054EC90_RoomPopulate`
  and its active-room draw) → `monsters/spawn`, `objects`; collision bits → `drlg/collision`;
  substitution cells and groups, `LvlPrest` columns other than the file pick and `Dt1Mask` →
  `drlg/preset`; warp placement and `LvlWarp` → `drlg/warps`; the act `+0x094`/`+0x484` tomb pair and
  the Act III bit → the quest work.
- Later plans this one sets up: `drlg/preset`, `drlg/maze`, `drlg/outdoor` (each replaces its Phase 3
  oracle and re-runs the recorded logs), then `drlg/collision`.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

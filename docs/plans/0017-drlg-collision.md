# 0017 — DRLG collision: the room collision grid, logic regions and the spawn position tests

> **Status:** in-progress (approved 2026-10-14)
> **Created:** 2026-10-14
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only

## TL;DR

**Question:** what does a room's u16 collision grid hold when the population pass reads it, and how do the four
position predicates of [monsters/spawn § H](../specs/monsters/spawn.md#h-placement-spawnpospick-and-monspawntry)
decide? Those predicates are `CollisionTest`, `LogicRegionIdAt`, `SpawnClassCellTest` and `NearWarpTest`. Plan 0014
took all four as ADR-0004 value oracles. This plan reads how the grid is built from DT1 sub-tile flags, how units
mark and unmark it, and the logic-region flood, then models them in `tools/collision.py`. It reruns the plan 0014
logs with the four oracles replaced by the model. When it is done, `docs/findings/drlg/0005-collision.md` has the
grid and the predicates at `[C]` for the logged cases, `docs/specs/drlg/collision.md` is drafted, and the
*Inputs and oracles* table of monsters/spawn lists those inputs as `drlg/collision` behaviour, not as oracles.
Movement, pathing and line of sight read the same grid but are only named here.

## Context

- Research-map row `drlg/collision`, `not started`. Dependencies: `drlg/overview` and `drlg/room-tiles` reviewed
  (which tile goes in which cell); `drlg/preset` reviewed (DS1 presets, their units, the `Logicals` builder
  selection); [fmt:dt1](../formats/dt1.md) documents the 25 sub-tile flag bytes. Their bit meanings are `[L]` until
  this plan anchors them.
- Code already named: `sub_0064C860_TileCollisionUpdate` and `COLL_ClearTile` 0x0064C580 (OR all 8 bits of each
  sub-tile byte into the u16 map, `[I]`, [drlg/0001 § Sub-tile flags](../findings/drlg/0001-ds1-dt1-readers.md#sub-tile-flags-into-the-collision-map));
  `sub_0064D9B0_CollisionTest` and its helpers 0x0064D450 and 0x0064D100 (`[I]`, monsters/0002 § 6); the logic-region
  builders `sub_0066CCB0_LogicBoxSingle` and `sub_0066D110_LogicRegionsFromDs1` (`[I]`, drlg/0004), with
  `sub_0066CA50_LogicBoxesFromGrid`; `sub_0061B130_LogicRegionIdAt`, `sub_005FD350_SpawnClassCellTest` and
  `sub_0054DB50_NearWarpTest` (`[I]`, monsters/0002 § 6). The active room keeps its collision map at `+0x20`
  (`{x0, y0, w, h, …, +0x20 cells}`), and a cell outside every room tests as `0x27`.
- Harness and logs: `tools/gdb/mon-spawn.gdb` already logs every predicate call with its arguments and result, and
  the room and game seeds around it. The three logs of run:2026-10-13-mon-spawn (916 creations) are the first
  test set. `tools/monspawn.py` holds the oracle hooks that this plan replaces.
- Why now: the plan 0014 Phase 1 review set this plan to follow Phase 3, and the Phase 3 review (2026-10-14)
  drafted it. Placement is the last oracle-bound part of monsters/spawn under DRLG ownership. `objects` placement
  (not started) also needs these predicates.
- Leads: none registered. DRLG has little community coverage. Phase 1b looks for a source on sub-tile flags
  (walk / LOS / block bits), registers what it finds or records "none found" (ADR-0007).

## Phases

### Phase 0 — Sub-tile flags and footprints in the data
- **Owner skill:** archivist
- **What:** survey the DT1 sub-tile flag bits, and the footprint columns of the units that mark the grid.
- **Outputs:** [fmt:dt1](../formats/dt1.md) § sub-tile flags survey (per bit: tiles and sub-tiles that set it, per
  LvlType and per tile orientation); [MonStats2](../tables/MonStats2.md) `SizeX`/`SizeY`/`spawnCol` and the
  object-collision columns with their value ranges over pool classes; the object table's size and collision columns
  if it has a doc, else a backlog entry; a `tools/` survey command.
- **Done when:** the survey prints per bit 0–7 the count of sub-tiles with it set over every DT1 in the inventory,
  and which bit combinations occur; `SizeX` and `spawnCol` value counts over the pool classes of plan 0014 Phase 0
  (and, as the backlog asks, which pool classes have `spawnCol` 1). Meanings stay `[L]`.

### Phase 1 — Read the grid and the predicates
- **Owner skill:** reverser
- **What:** read the collision grid's life cycle and the four position predicates. Then choose the boundary for
  Phase 2.
- **Outputs:** `docs/findings/drlg/0005-collision.md`, `re/symbols.csv` rows (subsystem `drlg/collision`),
  `re/types/` (the room collision map struct).
- **Done when:** the finding states, with addresses and `[I]` or better:
  - the grid build: allocation at active-room activation, its rectangle relative to the room (border cells, the
    neighbour rooms), the stamp from each tile's 25 sub-tile bytes (floor, wall, roof and special layers, which
    tiles are skipped), and how orientation and hidden tiles enter;
  - unit marks: which unit types mark the grid (monsters, objects, players, missiles, items if any), with which
    mask and footprint (`SizeX` per size 0–3, objects by their table columns), when a mark is added, moved and
    removed, and whether an object placed by `RoomObjectsPopulate` marks before the population pass;
  - every bit of the u16 word that a reader tests, named by its readers: the five spawn masks of monsters/spawn
    (`0x3C01`, `0x01C0`, `0x3F11`, 0, and `0x3C01`), the `0x27` out-of-room value and `0xFFFF` for an unknown
    size; movement, pathing and line-of-sight readers are only named;
  - `CollisionTest` in full (already `[I]`; re-anchor and extend to sizes 2 and 3);
  - the logic regions: `LogicBoxSingle`, the flood in `LogicRegionsFromDs1` and its helpers, and `LogicRegionIdAt`;
  - `SpawnClassCellTest` (the five `BaseId`s and their offset cells) and `NearWarpTest` (which warp and level points,
    and where they come from: `drlg/preset`, or `drlg/warps`, which is not started);
  - **the boundary decision** for Phase 2: is the grid at pass entry modelled end to end (tiles, then preset and object
    marks with logged positions), or is a grid snapshot at pass entry logged and only the in-pass marks modelled?
    Recommend one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch and register any community document on DT1 sub-tile flags or unit collision sizes, and compare
  per `evidence-rules.md` § Community cross-checks (blind first).
- **Outputs:** `docs/sources.md` entries or a "none found" note with the searches made; verdicts in the finding's
  *Leads used*.
- **Done when:** each sub-tile bit meaning and the footprint rule carry a verdict with a `src:` id or `not covered`.
  Every `contradicted` claim is a required case of Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (a human may play, as in plan 0014)
- **What:** write `tools/collision.py` (DT1 tiles through the existing parsers, rooms through `tools/drlg.py`) and
  plug it into `tools/monspawn.py` in place of the four value oracles.
- **Logging:** extend `tools/gdb/mon-spawn.gdb` or add `tools/gdb/collision.gdb`: per active room, a dump of the
  collision map at activation and at pass entry, and every mark and unmark inside the pass window.
- **Done when:** a run `run:YYYY-MM-DD-collision` shows:
  - the three plan 0014 logs rerun with `CollisionTest`, `LogicRegionIdAt`, `SpawnClassCellTest` and `NearWarpTest`
    predicted by the model: 0 mismatches over every call (the oracle assertions stay on as checks);
  - grid dumps compared cell for cell with the model at activation, on at least 50 rooms over at least four
    LvlTypes, including preset rooms, maze or outdoor rooms, and a room with a `Logicals` = 1 flood;
  - every bit the Phase 1 readers test exercised at least once, or listed as unreached;
  - the Phase 1b cases;
  - any remaining boundary (the snapshot, warp points from `drlg/warps`) named in the record.
  In-scope claims go to `[C]` citing the run. monsters/0002 § 9 notes which oracles are now replaced.

### Phase 3 — Spec: drlg/collision, and monsters/spawn updated
- **Owner skill:** spec-writer
- **What:** write `docs/specs/drlg/collision.md`. In [monsters/spawn](../specs/monsters/spawn.md) *Inputs and oracles*,
  point the four predicates and the logic boxes at it.
- **Done when:** the spec follows the template and every statement is tagged. It has a worked example: one room's
  grid from its tiles, plus a contested placement from the plan 0014 worked example. The cells (15559, 5615) with
  value 39 and (15558, 5615) with value 4096, which member 1 marks, are the natural case. The edited monsters/spawn
  rows cite the new run, and the architect's review passes.

## Open questions

- Objects mark the grid before the pass. If their footprints come from an object table that `objects` (not started)
  owns, Phase 1 may take object marks as logged inputs; the boundary decision says so.
- Warp points for `NearWarpTest` come from DS1 presets (`drlg/preset`, reviewed) and from the warp builder
  (`drlg/warps`, not started). Phase 1 decides whether the warp side is read here or stays an input.
- Movement, pathing and line of sight read the same bits. They are named, not specified, and wait on a later
  `monsters/ai` or `player/movement` row.
- The client has its own collision copy (the wall cut-away reads the logic regions, drlg/0004). Only the server grid
  that spawning reads is in scope.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-14 — Drafted (architect).** Follow-up named in the plan 0014 Phase 1 and Phase 2 reviews. It replaces the
  monsters/spawn position oracles. Drafted at the plan 0014 Phase 3 review. Waits for the owner's approval.
- **2026-10-14 — Approved (human).** No changes to the draft. Phase 0 (archivist) is next.
- **2026-10-14 — Phase 0 landed (archivist).** Two survey commands, both registered as gate surveys with baselines:
  `python3 -I tools/dt1.py subtiles workspace/merged` (`dt1_subtiles`) and
  `python3 -I tools/mon_survey.py collision workspace/merged/data/global/excel` (`mon_collision`).
  [fmt:dt1 § Sub-tile flags survey](../formats/dt1.md#sub-tile-flags-survey-plan-0017-phase-0) gives per bit 0–7
  the sub-tile and tile counts over all 257 version 7.6 files (16 456 tiles), the 14 byte values and 13 per-tile ORs,
  and tables per orientation, per byte position and per LvlType. Bits 3, 6 and 7 are never set. **Bit 4 is in one file
  only** (`act2/tomb/tombsteps.dt1`, 16 floor tiles, every sub-tile). Bit 5 is in 40 files and never on orientations 10,
  11, 13 or 15–19. [MonStats2 § Footprint and collision columns](../tables/MonStats2.md#footprint-and-collision-columns-plan-0017-phase-0)
  gives `SizeX`/`SizeY`/`spawnCol`/`objCol`/`deadCol` over the 362 pool classes of plan 0014 Phase 0. `SizeX` = `SizeY` in
  every row. The pool has `SizeX` 2 (238), 3 (123) and 0 (1, `baaltaunt`), `spawnCol` 1 on `frogdemon1..3`, 2 on
  `crownest1..3`, and `objCol` on none. **Surprise:** the classes `MonSpawnTry` excludes from the `spawnCol` 1 tile
  placement (153, 258–263) are exactly the other seven `spawnCol` 1 classes, so only the frog demons (levels 77,
  78, 93) reach `0x005B2700`. Phase 2 needs a log in those levels to exercise it. This answers backlog "plan 0014
  Phase 1 follow-ups" (c). `objects.txt` has no table doc, so there is a new backlog entry (archivist → architect) with its
  candidate columns. All counts are `[C]` by command. Every meaning stays `[L]`. Side fix: `dt1.py lvltypes` crashed
  on the `pad_781` layout entry (no `col`); the lookup now skips such entries.
- **2026-10-14 — Phase 0 accepted (architect).** Reran `tools/dt1.py subtiles workspace/merged` (257 files, 411 400 sub-tiles; bits 3, 6, 7 never set; bit 4 only in `tombsteps.dt1`) and `tools/mon_survey.py collision` (362 pool classes; `spawnCol` 1 on `frogdemon1..3` only, 2 on `crownest1..3`). Meanings stay `[L]` as the phase requires. For Phase 2: only the frog demons reach the `spawnCol` tile placement, so a log from level 77, 78 or 93 is a required case. The Objects table doc request is triaged separately (backlog). Phase 1 (reverser) is next.
- **2026-10-14 — Phase 1 landed (reverser).** [drlg/0005](../findings/drlg/0005-collision.md), static reading, every claim `[I]`. 88 new
  `re/symbols.csv` rows (subsystem `drlg/collision`: the `COLL_*` primitives, `DUNGEON_*` accessors, `UNIT_*`/`PATH_*` mark code, the
  `LOGIC_*` flood, the warp-point and level-point helpers, five data tables) and `re/types/collision.h` (`CollMap`, `DungeonRoom`,
  `RoomTileEntry`, `DungeonTileLists`, `DynPathColl`); `LogicRecord`'s padding in `re/types/monspawn.h` is now its two grids (`DrlgGrid`). No
  existing symbol renamed. Done-when, point by point: grid build (§ 1–2: `COLL_MapBuild` from `DUNGEON_RoomCreate`, the room's exact subtile
  rectangle, no border cells; floors, walls, shadows of the room **and its active near rooms** whose top-left subtile is inside; OR of the 25 bytes
  plus entry-flag bits `0x10`/`0x01`/`0x04`; nothing skipped for orientation or hidden; border tiles reach a neighbour only if it activates later;
  bit-2 merges re-stamp active neighbours); unit marks (§ 5: patterns by size, `0x80` players, `0x100` monsters, `0x1000`/`0x2000` centre bits,
  objects by `HasCollision[mode]` with masks from `IsDoor`/`BlocksVis`/`BlockMissile`/`SubClass`, items `0x200`, corpses `0x8000`, missiles nothing;
  all marked at creation, so preset and `RoomObjectsPopulate` objects are in the grid before the pass and each created monster marks before the next
  test); every bit with writers and readers (§ 6, the five spawn masks, `0x27`, `0xFFFF`, movement masks named); `CollisionTest` sizes 0–3 in full with the
  edge and out-of-room values (§ 3–4); logic regions (§ 7: `LogicBoxSingle` resets the level counter to 1, the flood with its rule tables, boxes,
  neighbour merge, `LogicRegionIdAt` returns 0 with no room); `SpawnClassCellTest` (§ 8) and `NearWarpTest` (§ 9: warp points are **per level**,
  built from DRLG room flags that `drlg/warps` sets; the waypoint lookup can init a level, activate a room and step the level seed). **Boundary:
  recommend B** (§ 12): log the grid snapshot at pass entry (room plus near rooms), model the in-pass marks and the four predicates, check the tile
  half end to end at activation with the cell-for-cell dumps, warp points as logged inputs. Reasons: the pre-pass grid holds runtime unit marks (players,
  wandering monsters, items, corpses) and object footprints from an undocumented table and an unread `objects` placement; the tile half depends on the
  activation history, which the activation dumps check directly. Surprises for review: spawn masks do not include the monster bit `0x100`, so earlier
  monsters block only through their `0x1000` cells (wraiths and size-0 monsters block nothing); `CollisionTest` size 2 returns the mask, not `0x27`, when
  the centre has no room; monsters/0002 § 6 corrected ("level's warp points"). Backlog: reverser → archivist (Objects offsets, link the bit meanings),
  reverser → architect (`NearWarpTest` side effects, `drlg/warps`). Phase 1b (community cross-check) is next, then the architect rules on the boundary.
- **2026-10-14 — Phase 1 accepted, boundary B ruled (architect).** drlg/0005 meets every *Done when* bullet at `[I]` (49 tags, all `[I]`, which is right for a static reading). Spot-checked `COLL_MapBuild` 0x0064C900, `DUNGEON_NearRoomsBuild` 0x00619800, `TileCollisionUpdate` 0x0064C860, `CollisionTest` 0x0064D9B0 and `NearWarpTest` 0x0054DB50 against `re/symbols.csv`. **Ruling: boundary B as recommended in § 12.** The grid snapshot at pass entry (the room and its near rooms) is an ADR-0004 value oracle. The tile half is modelled at activation and checked cell for cell. The in-pass marks and the four predicates are modelled. The warp and type-11 points are logged inputs (owner `drlg/warps`). Conditions for Phase 2, in addition to § 12's required cases:
  - **R1.** Around every `NearWarpTest` call, assert the level seed `+0x1C4` and the set of active rooms, not only the room and game seeds. A call in a `Position` level with population is a required case if the run reaches one; otherwise it is listed as unreached.
  - **R2.** Spawn masks leave out `0x100`. Required case: a placement accepted on a cell marked only `0x100` (an outer cell of a size-3 monster's 3×3, or next to a wraith), predicted by the model.
  - **R3.** The run record names the snapshot as an oracle. It reports the non-gating consistency check (snapshot minus the activation model, against the logged preset and object positions) with its numbers, so the size of the boundary is visible.
  - **R4.** The monsters/spawn wording "warp point of the room" → "of the level" goes to the spec-writer (backlog), at the latest in Phase 3.
  Phase 1b (reverser, community cross-check) is next, then Phase 2.
- **2026-10-14 — Phase 1b landed (reverser).** Community cross-check of [drlg/0005](../findings/drlg/0005-collision.md#phase-1b-community-cross-check-2026-10-14), written after the Phase 1 reading. Sources fetched and read in-session (ADR-0007), registered in [sources.md](../sources.md): `pk-walkable-thread`, `pk-dt1-advanced`, `pk-subtile-flags-thread` (new), `siramy-ds1edit` and `d2dfg-blizzard` (re-fetched). Rejected and not used: `siramy-dt1-doc` (the Siramy DT1 document and its PK copy, a=40: C decoder routines), `pk-pathfinding-thread` (reverse-engineered in-memory structs and code), `opendiablo2-dt1` (a reimplementation, not opened). **No admissible source numbers the DT1 sub-tile bits beyond bit 0.** Verdicts: bit 0 walk block **held with refinement**; the DS1 Unwalkable bit over a whole tile **held with refinement**; bits 1–7 **not covered**; the footprint rule (MonStats2 `SizeX`) **held with refinement** (a size class, not a square side); objects `SizeX`/`SizeY` held with refinement, `HasCollision` held, `IsDoor`/`BlocksVis`/`BlockMissile` held with refinement; `spawnCol` 0–3 held with refinement; `opendoors` held; `flying` held with refinement (no `flying` test seen in the spawn path; check in Phase 2); `objCol` not covered. **Two `contradicted`**, both the finding's errors, re-read with r2 and corrected in place at `[I]`: **(C1) `deadCol`**: only a `deadCol` 0 monster's corpse re-marks as a `0x8000` plus (tests 0x004B05DB, 0x004B09FB); a `deadCol` 1 corpse keeps `0x100`; player corpses are a 3×3 `0x8000` square. **(C2) Missiles `Collision`** (`+0x184`): such a missile marks `0x40` from creation (0x004CD11D, 0x0059FD64), so grid bit 6 is the missile bit that `spawnCol` 1 reads (33 of 684 missiles). **Required Phase 2 cases:** C1, a `deadCol` 1 class killed in a logged room with its corpse cells dumped (or listed as unreached); C2, a placement test in a room holding a `Collision` 1 missile (or listed as unreached). Backlog: reverser → architect. No symbol rows changed. Phase 1b goes to the architect for review; Phase 2 follows.
- **2026-10-14 — Phase 1b accepted (architect).** Every sub-tile bit and footprint claim in drlg/0005 *Leads used* has a verdict. Bit 0 (walk block) and the footprint rules are held with refinement. Bits 1–7 are not covered by any admissible source. The sources policy was applied conservatively: `siramy-dt1-doc` (it contains decoder source), `pk-pathfinding-thread` (reverse-engineered structs with code) and `opendiablo2-dt1` (a reimplementation) are registered as rejected. The few lines of `siramy-dt1-doc` seen before the rejection are recorded in its row, and no verdict rests on them, which is acceptable. The two `contradicted` claims were errors in the finding and are corrected at `[I]` (re-read with r2). Both join the Phase 2 required cases:
  - **C1:** a `deadCol` 1 corpse keeps its `0x100` mark, and only `deadCol` 0 corpses become a `0x8000` plus;
  - **C2:** a missile with Missiles `Collision` ≠ 0 marks `0x40`, the bit that `spawnCol` 1's mask `0x01C0` reads.

  Phase 2 is next. It needs the wine harness and a save that reaches Act III (levels 77, 78 or 93, for the frog demons), built with `tools/d2s.py build` `quests: all`.

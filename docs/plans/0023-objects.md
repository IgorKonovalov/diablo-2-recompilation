# 0023 — Objects: object groups, placement, preset objects, shrine and chest variants

> **Status:** in-progress (approved 2026-10-14)
> **Created:** 2026-10-14
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only

## TL;DR

**Question:** when a room activates on the server, which objects does it get, where do they stand, and what does each
object roll at creation? This covers the Levels object groups (`ObjGrp0..7` with `ObjPrb0..7`) that
`sub_00552610_RoomObjectsPopulate` draws, the ObjGroup member pick, the placement and its position test, the DS1 preset
objects that `sub_005557D0_PresetUnitDispatch` creates, and the per-object creation rolls: shrine type, chest and
container variants (locked, trapped, "sparkly" super chests), and the object's own seed. Today that whole stretch is the
**presets / inactive-restore / objects window**: a seed oracle in `tools/monspawn.py` (RW1 → RW4), in
[monsters/spawn](../specs/monsters/spawn.md) *Inputs and oracles*, in plan 0017 and again after plan 0018 (ruling (d)).
This plan reads that code and models it, so the window is predicted. When it is done:
- `docs/findings/objects/0001-object-population.md` has the population, placement and creation rolls at `[C]` for the
  logged cases;
- `docs/specs/objects/README.md` (and a `population.md` if the spec-writer splits it) is drafted;
- the *Inputs and oracles* table of monsters/spawn lists the objects window as `objects` behaviour, not as an oracle.

**Operation is out of scope except where it feeds item creation.** What a shrine *does* (its effect, duration,
regeneration) is game simulation, deferred by ADR-0002. A chest's or container's operate path is in scope only up to
the call into item creation: which draws it makes before `sub_00585B90_ObjectChestDrop`, how many drops it asks for, and
the TC it passes (the TC choice is already [items/tc](../specs/items/tc.md) `[I]`). Traps (the missile a trapped chest
fires) and the inactive-unit restore are named only.

## Context

- Research-map row `objects`, `not started`. Dependencies: `rng` and `rng/seeds` reviewed; `drlg/overview`,
  `drlg/preset` and `drlg/collision` reviewed (plans 0008, 0016, 0017; collision closed 2026-10-14); `monsters/spawn`
  reviewed (plan 0014). All are met.
- Code already named:
  - `sub_0052D160_NewRoomsUpdate` (`[C]`, monsters/0002 § 1) calls, per fresh room, the wanderer tick,
    `sub_005559A0_RoomPresetUnits`, `sub_00542B40_RoomInactiveUnitsRestore`, `sub_00552610_RoomObjectsPopulate` and
    `sub_0054EC90_RoomPopulate`, in that order. monsters/0002 § 1 item 4 (`[C]`, read only for the draw count): object
    population makes one room-seed draw per object-group slot (8), one more per group that passes its probability, plus
    the creators' draws. In 176 of 516 rooms of run:2026-10-13-mon-spawn the window drew nothing.
  - `sub_005559A0_RoomPresetUnits` walks non-monsters first, then monsters; `sub_005557D0_PresetUnitDispatch` sends
    type 2 with `id > 573` to `0x0054F490` (not read), type 2 `id = 573` to nothing, and every other non-monster to
    `sub_00555230_SUnitCreate` ([drlg/preset](../specs/drlg/preset.md) § 6, `[I]`). The DS1 keep/drop rolls for objects
    196, 261 and 581 and the act rewrites to objects are already `[C]`/`[I]` there.
  - `UNIT_GetCollMask` and `UNIT_CollMarkRect` (`[I]`, [drlg/collision](../specs/drlg/collision.md) § F): an object marks
    `SizeX`×`SizeY` when `HasCollision[mode]`, with mask `0x400` (plus `0x4` for `BlockMissile`, `0x8000` for the portal
    rows, `0x806`/`0x804` for doors). Run:2026-10-14-collision applied logged object marks; no object position test or
    object rejection was exercised.
  - `sub_00585B90_ObjectChestDrop`, `TC_GetChestTC`, `TC_BuildChestTable`, `g_ChestTCs` ([items/tc](../specs/items/tc.md),
    `[I]`): the `Act N Chest A/B/C` choice. Its callers (the object operate handlers) are not read.
- Data: `objects` (573 rows, `.bin` records of 448 B), `objgroup` (133 rows, 52 B) and `shrines` (23 rows, 184 B) have
  **no table doc** and no layout in `tools/excel_layouts.py`. The reverser → archivist entry of plan 0017 Phase 1 in
  [docs/backlog.md](../backlog.md) holds Objects offsets matched by `excel_bin.py probe` (`SizeX` `+0x0D0`, `SizeY`
  `+0x0D4`, `HasCollision0..7` `+0x120`, `IsDoor` `+0x13A`, `BlocksVis` `+0x13B`, `TotalPieces` `+0x161`,
  `Xspace`/`Yspace` `+0x162`/`+0x163`, `SubClass` `+0x167`, `NameOffset` `+0x168`, `CollisionSubst` `+0x19D`,
  `BlockMissile` `+0x1B6`, `DrawUnder` `+0x1B7`; Missiles `+0x18A` footprint), and the archivist → architect triage entry
  asks for the Objects doc. Both were held for this row; Phase 0 takes them. `ObjMode` (8 rows) has no doc either.
  [Levels](../tables/Levels.md) documents `ObjGrp0..7` (`+0x0E5`..) and `ObjPrb0..7` (`+0x0ED`..) at `[C]` layout.
- Harness and logs: `tools/gdb/mon-spawn.gdb`, `tools/gdb/collision.gdb` and `tools/gdb/mon-special.gdb` already log
  the window's entry and exit seeds (RW1/RW4) and the object marks (CM lines); the logs of run:2026-10-13-mon-spawn,
  run:2026-10-14-collision and run:2026-10-14-mon-special are the first test set for the window's seed accounting
  (draw counts only; they hold no per-object detail). `tools/monspawn.py` is the replay to extend.
- Why now: it is the last row of the core DRLG/population chain whose dependencies are all reviewed, and it retires
  the largest seed oracle left in the room driver. Chest drops are an item-creation path (ADR-0002) that items/tc can
  only name until this row exists.
- Leads: `src:d2dfg-blizzard` (registered; its Objects, ObjGroup and Shrines sections are not yet read),
  `src:siramy-ds1-any-units` (registered; DS1 object ids). Phase 1b fetches them again as ADR-0007 requires and
  searches for shrine and chest documentation.

## Phases

### Phase 0 — Objects, ObjGroup, Shrines and ObjMode tables
- **Owner skill:** archivist
- **What:** document the four object tables with `.bin` layouts, taking in the held Objects offsets.
- **Outputs:**
  - `docs/tables/Objects.md`: layout by `excel_bin.py diff`, every column, the `-1` marker row, and the columns the
    code is known to read (the held offsets above, cited to drlg/0005); the populate- and operate-related columns
    (`OperateFn`, `PopulateFn`, `InitFn`, `ClientFn`, `SubClass`, `Selectable0..7`, `IsDoor`, `HasCollision0..7`, `SizeX`/`SizeY`,
    `Xoffset`/`Yoffset`, `Mode0..7`, `Lit0..7`, `Trans`, `PreOperate`, `Parm0..7`, `AutoMap`) with value ranges;
  - `docs/tables/ObjGroup.md`: `GroupName`, `ID0..7`, `DENSITY0..7`, `PROB0..7`, `SHRINES`, `WELLS`, with a survey of
    which groups the Levels `ObjGrp*` columns use per difficulty and how many members each has;
  - `docs/tables/Shrines.md` (23 rows: `Code`, `Arg0`/`Arg1`, `Duration in frames`, `reset time in minutes`, `rarity`, `effectclass`,
    `LevelMin`, names) and `docs/tables/ObjMode.md`;
  - `tools/excel_layouts.py` entries, the regenerated `excel_layout` gate baseline, and survey commands;
  - the two held backlog entries (Objects offsets, Objects doc) closed; Missiles `+0x18A` left for a Missiles doc
    (not this plan).
- **Done when:** `excel_bin.py diff` passes on all four tables with 0 mismatches and no uncovered bytes, one survey
  command prints for every level its eight groups with probabilities and member lists, and every held offset resolves
  as a `tbl:Objects.txt:<col>` anchor. Meanings stay `[L]` except those already `[I]` in drlg/0005.

### Phase 1 — Read object population, placement and creation rolls
- **Owner skill:** reverser
- **What:** read the code from the start of the window (`0x0052D1D2`) to the population pass entry, plus the object
  creators it calls, and choose the boundary for Phase 2.
- **Outputs:** `docs/findings/objects/0001-object-population.md` (new subsystem directory), `re/symbols.csv` rows
  (subsystem `objects`, renaming the `sub_` ones it settles), `re/types/` additions (the object unit data, the ObjGroup
  record).
- **Done when:** the finding states, with addresses and `[I]` or better:
  - `RoomObjectsPopulate`: the eight Levels slots, the `ObjPrb` draw (seed, range, comparison), the ObjGroup member pick
    (`PROB0..7`, `DENSITY0..7`), the count per room, and which rooms are skipped (town, preset-filled, size);
  - placement: how a position in the room is chosen for an object, which collision mask and footprint the position test
    reads (drlg/collision § F/H), the retry count, and what happens when no spot is found;
  - preset objects: `PresetUnitDispatch` → `SUnitCreate` for objects and `0x0054F490` for `id > 573`, including any draw
    made per preset object;
  - the per-object creation rolls through the `InitFn`/`PopulateFn` handlers reachable at creation: the shrine type pick
    (Shrines `rarity`, `LevelMin`, difficulty), container variants (locked, trapped, super chest, exploding/poison
    barrels), the object's own unit seed and any game-seed draw. For each handler: **which draws it makes on which seed,
    in order**. Effects are only named;
  - the chest/container operate path up to `sub_00585B90_ObjectChestDrop`: the draws before the drop, the drop count,
    the TC passed, and whether a super chest or a locked chest changes them;
  - the inactive-unit restore `sub_00542B40` on a first activation: confirm it draws nothing, or name what it does;
  - **the boundary decision** for Phase 2: which handlers stay oracles (e.g. a quest object's state), and how the
    window's seed state is asserted. Recommend one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch `src:d2dfg-blizzard` (§ Objects, § ObjGroup, § Shrines) and `src:siramy-ds1-any-units` again, search
  for shrine-rarity and super-chest documentation, register what is found in `docs/sources.md`, and compare blind per
  `evidence-rules.md` § Community cross-checks.
- **Outputs:** `docs/sources.md` updates; verdicts in the finding's *Leads used*.
- **Done when:** each claim about group probability and density, shrine choice, chest variants and object drop counts
  carries a verdict with a `src:` id or `not covered`. Every `contradicted` claim reachable with stock data is a
  required case of Phase 2; an unreachable one stays `[I]` and goes under the spec's *Open questions* (precedent:
  `sparsePopulate`, plan 0014).

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (agent-driven per [harness-play](../../.claude/skills/reverser/references/harness-play.md);
  the owner may play, as in plan 0014)
- **What:** write `tools/objects.py` and plug it into `tools/monspawn.py` in place of the objects part of the RW1 → RW4
  seed oracle (and the preset-object part, if Phase 1 covers it); feed the object marks it predicts to the collision model
  instead of the logged CM lines. Then log a new run.
- **Logging:** a new `tools/gdb/objects.gdb` (or an extension of `mon-special.gdb`): per room, each slot's draw and
  verdict, each group member pick, every placement attempt with its position test, each object created (class, position,
  mode, seed), each creation handler's draws, and on operate the draws up to the TC call.
- **Done when:**
  - the logs of run:2026-10-13-mon-spawn, run:2026-10-14-collision and run:2026-10-14-mon-special rerun with the
    objects window's draw count predicted (they hold no per-object lines), 0 mismatches;
  - a run `run:YYYY-MM-DD-objects` covers Normal, Nightmare and Hell, classic and expansion, all five acts, and at least
    300 populated rooms with objects. It includes at least 30 shrines (with shrine type), 50 chests or containers
    with their variants, at least one super chest, a locked chest and a trapped one, a placement that needs retries, and
    at least 20 operated chests or containers whose draws up to the TC call reproduce. All of these reproduce with 0
    mismatches, with the room and game seed at the population pass entry predicted, not taken;
  - every ObjGroup used by a level visited is drawn at least once, or listed as unreached;
  - the Phase 1b cases are covered;
  - any boundary that remains is named in the record.

  In-scope claims go to `[C]` citing the run. monsters/0002 § 9 and drlg/0005 note which oracles are now replaced.

### Phase 3 — Spec: objects, and monsters/spawn and drlg/collision updated
- **Owner skill:** spec-writer
- **What:** write `docs/specs/objects/README.md` (object groups, placement, preset objects, creation rolls, the chest
  drop entry), point the window in [monsters/spawn](../specs/monsters/spawn.md) § A and its *Inputs and oracles* row at
  it, and update [drlg/collision](../specs/drlg/collision.md) where object marks stop being logged inputs.
- **Done when:**
  - the spec follows the template and every statement is tagged;
  - it gives the RNG call sequence of one room's object population as a worked example (taken from the run), and one
    shrine and one chest creation;
  - it has a table of per-handler draws at creation;
  - it links the chest drop into [items/tc](../specs/items/tc.md) (the TC choice stays there);
  - the architect's review passes.

## Open questions

- Shrine effects, well refills, door and lever behaviour, waypoint activation and trap missiles are game simulation
  (ADR-0002) and are named only. If a creation handler draws a value it stores for its effect, Phase 1 says whether the
  draw is specified here and the meaning deferred.
- Quest objects (Cain's stones, the Horadric orifice, the Hellforge, Anya's portal) may be created under quest state.
  Phase 1 names each; those tied to quest scripts can stay inputs, as in plan 0018.
- The inactive-unit restore on a revisited room may re-create objects with saved state. Only the first activation is
  in scope; a revisit is named.
- Object item drops beyond chests (weapon racks, armor stands, bodies, `Jar`s) use the same TC call; Phase 1 says
  whether any of them takes a different TC or count.
- Ordering: the reverser phases wait for Ghidra and display :7 after plan 0019 Phase 2. Whether they run before or after
  plan 0022's reverser phases is open; the architect sets the order in the plans index.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-14 — Drafted (architect).** Picked from the research-map rows whose dependencies are met: `drlg/collision`
  closed today, and the objects window is the largest seed oracle left in the room driver. It takes in the two held
  backlog entries (Objects offsets, Objects table doc).
- **2026-10-14 — Approved (human).** The owner asked to draft and approve plans 0021–0023 together. Phase 0 (archivist)
  can start now; it needs neither Ghidra nor the harness.
- **2026-10-14 — Phase 0 landed (archivist), branch `lane/a0023p0`.** Four table docs: [Objects](../tables/Objects.md),
  [ObjGroup](../tables/ObjGroup.md), [Shrines](../tables/Shrines.md), [ObjMode](../tables/ObjMode.md); four
  `tools/excel_layouts.py` entries; the `excel_layout` gate baseline regenerated by `excel_bin.py survey` (41 tables,
  653 155 cells, 0 unexplained); new `tools/obj_survey.py` (`levels`, `groups`, `objects`, `shrines`).
  - Layouts `[C]` by `excel_bin.py diff`, 0 mismatches each: objects 573 × 156 fields = 89 388 cells, objgroup
    133 × 26 = 3 458, shrines 23 × 10 = 230, objmode 8 × 2 = 16. `excel_bin.py unknown` leaves no byte uncovered: the
    bytes with no `.txt` column are layout `U` fields, zero in every record (objects `+0x040` 128 B, `+0x147`,
    `+0x16C`, `+0x16F`, `+0x176` 2 B, `+0x19E` 2 B; objgroup `+0x032` 2 B; shrines `+0x0B3`; objmode `+0x024` 16 B).
  - Not compiled: objects `Id`, `description - not loaded`, `Flicker` (0/1 on 44 rows, no offset under any encoding)
    and `ShrineFunction` (0 everywhere, could be either zero byte `+0x16C`/`+0x16F`; left unplaced); objgroup
    `GroupName`, `Offset`; shrines `Shrine Type`, `Shrine name`, `Effect`. Objects `Token` is a `char[3]` holding at
    most 2 characters (`NU0` → `NU`).
  - The held Objects offsets all landed where the reverser's probe put them, and each resolves as a
    `tbl:Objects.txt:<col>` anchor ([Objects § Columns the code is known to read](../tables/Objects.md#columns-the-code-is-known-to-read));
    meanings `[I]` where drlg/0005 has them, `[L]` otherwise. Missiles `+0x18A` left for a Missiles doc. Both held
    backlog entries are struck.
  - Survey command for every level's eight groups with probabilities and members:
    `python3 -I tools/obj_survey.py levels workspace/merged/data/global/excel` (`SURVEY obj_levels levels=137
    levels_with_groups=123 slots_used=476 slots_out_of_range=0`).
  - Surprises: (1) the objgroup separator row is spelled `EXPANSION` and is compiled as all-zero record 97, so group
    indices count it (noted in [excel-bin.md](../formats/excel-bin.md)); (2) objects `Id` differs from the record
    index on records 410–412 (Id 408, 409, 410 again); the docs take the record index as the class id `[L]`; (3) every
    member of the 24 `SHRINES` groups has `DENSITY` 0, while the expansion shrine groups have `SHRINES` 0 and
    `DENSITY` 30; (4) 13 level slots name the empty group 0 with a non-zero `ObjPrb`, and levels 41–46, 134 and 86–91
    name memberless groups 30 and 72; (5) Levels has no per-difficulty object columns. Questions for Phase 1 are in
    the backlog (archivist → reverser).
- **2026-10-14 — Phase 0 accepted (architect).** Four layouts diff clean with no uncovered bytes (objects 89 388 cells,
  objgroup 3 458, shrines 230, objmode 16); the held Objects offsets are `tbl:Objects.txt` anchors. Rulings: (1) the
  all-zero `EXPANSION` objgroup record 97 is a data fact `[C]` and group indices count it. (2) The record index as the object
  class id stays `[L]` until Phase 1 reads the class lookup (records 410–412 repeat ids 408–410, so it matters). (3) `Flicker`
  and `ShrineFunction` stay unplaced; Phase 1 says whether any code reads them. (4) Slots placed by stride keep their bytes
  `[C]` and their column names `[L]`. `obj_survey` stays outside the gate for now; register it when Phase 2 cites it.
  Phase 1 (reverser) waits for Ghidra after plans 0021 and 0022.

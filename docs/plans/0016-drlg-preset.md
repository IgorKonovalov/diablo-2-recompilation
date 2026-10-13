# 0016 — DRLG presets: the DS1 unit list, the preset-unit rolls and the LvlPrest columns

> **Status:** in-progress (approved 2026-10-13)
> **Created:** 2026-10-13
> **Owner skill(s):** archivist (P0), reverser (P1, P1b, P2), spec-writer (P3); a human may play in P2
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction

## TL;DR

What does a preset map put into the level, beyond the room grid and tiles that `drlg/overview` and
`drlg/room-tiles` already reproduce? This plan covers four things. First, the per-room list of preset units a DS1
contributes: objects, monsters, NPCs and their paths, after the act-specific rewrites. Second, the keep/drop rolls of
`sub_00667620_PresetUnitDropRolls`, the last preset oracle in `tools/drlg.py gen` and `roomk`. Third, the `LvlPrest`
columns still `[L]`. Fourth, the town and link-value file indices that no run has built yet (level 27). Once it is done,
`tools/drlg.py` replays the recorded logs with no preset oracle, a new run reproduces every preset room's unit list
across all five acts, and `docs/specs/drlg/preset.md` exists.

## Context

- **Research-map row:** `drlg/preset` (not started). Dependencies are met. `drlg/overview` is `reviewed`
  ([drlg/README](../specs/drlg/README.md), [room-tiles](../specs/drlg/room-tiles.md)). `rng/seeds` is `reviewed`.
  The `ds1` format is documented (plan 0005, accepted with fixes).
- **Already `[C]`, not redone here** ([drlg/0003](../findings/drlg/0003-generator-dispatch.md)):
  - the preset file index (`Range(level seed, Files)`, `File(idx+1)`, 960/960 instances);
  - the 8×8 room split, rows outer;
  - the create-time draw discarded by the re-seed;
  - the maze per-`Def` rotation;
  - `Dt1Mask` as the room's DT1 mask.

  The type-2 grid prepare is modelled in [drlg/0002](../findings/drlg/0002-room-build-draws.md) § Type 2 prepare.
  This plan treats all of that as input.
- **What is left for this row:**
  - `sub_00667620_PresetUnitDropRolls`: the README *Sub-generator boundaries* oracle (52 calls in
    run:2026-10-12-drlg-gen, only 2 drew, both in Act II). It has three callers. The map scan steps the level seed.
    `PresetRoomLoadDs1` steps room `+0x14` before the re-seed, so those draws are discarded. A third caller sits at
    `0x0061B210+0x133`.
  - The DS1 unit pipeline:
    - `DS1_Parse`'s object entries become preset units, with the act rewrites through `0x004E6C50` (not read);
    - `sub_00666710_PresetUnitsToRoom`, `sub_006664A0_PresetCentreMonster` and `sub_0066BF30_PresetUnitCreate`;
    - the client-only `sub_006663C0_PresetClientObjects`.
  - The `LvlPrest` columns still `[L]` ([LvlPrest § Open questions](../tables/LvlPrest.md#open-questions)):
    `Populate`, `Logicals`, `Outdoors`, `Animate`, `KillEdge`, `FillBlanks`, `AutoMap` (read in the
    `PresetLevelBuild` gate but untagged), `Pops`/`PopPad` beyond the scan gate, and the `+0x024` slot.
  - The shared-DS1-buffer `0x84` question from drlg/0002: does any shipped preset have a cell that is a border in one
    view and interior in another view of the same file?
  - Level 27's index from the level-6 act-seed draw (code-read only), and the town callback `act[+0x488]` for
    levels 40, 103 and 109.
- **Backlog inherited:**
  - reverser → reverser 2026-10-11 (drlg/0001), open parts in scope: DS1 (e) substitution cells and groups as far as a
    preset room consumes them, object `flags`, group `unk`, path `action`, and `0x004E6C50`. Not in scope: DS1 (c)
    bits 14–15/30 and entry flags, which are presentation; collision bits, which are `drlg/collision`.
  - archivist → reverser 2026-10-12 (MonPreset ranges): the DS1 unit list half. The spawn half is answered in
    [monsters/0002 § 7](../findings/monsters/0002-room-population.md).
- **Boundaries (decided here, Phase 1 may move them with a reason):**
  - **This row owns** which preset units a room ends up with: kind, id after rewrites, position, mode/flags, path,
    and the keep/drop result.
  - **Monster instantiation is out:** `sub_005559A0_RoomPresetUnits`, `sub_0054E600_PresetMonSpawn` and superuniques
    belong to `monsters/spawn` and `monsters/special`.
  - **Object instantiation and operation is out:** row `objects`, including `Orient89Unit`'s objects 91/92.
  - **Collision is out:** `drlg/collision`.
  - **Presentation is out:** roof pops and the animated-tile *rendering*. Where Phase 1 finds a column purely
    presentational, the spec names it and stops (ADR-0002 out of scope, ADR-0005).
- **Leads:** community DS1 and LvlPrest documentation exists (DS1 editor notes, LvlPrest column guides). None is
  registered yet; Phase 1b fetches and registers them (ADR-0007).

## Phases

### Phase 0 — Preset unit and column survey
- **Owner skill:** archivist
- **What:** extend `tools/ds1.py` with a `units` survey over every DS1 that `lvlprest.bin` names. The survey reports:
  - unit entries per act and type (monster, object, NPC, item), the id ranges hit;
  - monster ids per MonPreset range (class, superunique, MonPlace keyword);
  - paths per unit and the `action` values;
  - object `flags` values;
  - substitution groups per file (preset-level records vs LvlSub DS1s), group `unk` values.

  It also tabulates the `LvlPrest` columns against `Levels.DrlgType` (preset level, outdoor cell, maze room).
  It lists the files named by more than one `LvlPrest` record, or by records of different `SizeX`/`SizeY`, which are
  the candidates for the shared-buffer `0x84` case.
- **Outputs:** `tools/ds1.py units`; [ds1.md](../formats/ds1.md) and [LvlPrest](../tables/LvlPrest.md) survey sections
  (counts and short examples, no dumps); gate baseline if the subcommand is registered.
- **Done when:** the survey runs over all 2058 resolved `File1..6` references and exits 0. Every unit type and every
  MonPreset range has a count per act. Every `LvlPrest` column has its distribution per generator kind. The `0x84`
  candidate list exists, and may be empty. Meanings the data alone can't settle stay `[L]` with a question to the
  reverser in the backlog.

### Phase 1 — Read the preset unit pipeline
- **Owner skill:** reverser
- **What:** read, from the DS1 object entries to the room's preset-unit list:
  - `DS1_Parse`'s unit branches and the act rewrites (`0x004E6C50`);
  - `sub_00667620_PresetUnitDropRolls`: which units it rolls, the draw and the threshold, which seed per caller, and
    what it keeps;
  - `sub_00666710_PresetUnitsToRoom`, `sub_006664A0_PresetCentreMonster`, `sub_0066BF30_PresetUnitCreate`;
  - the readers of every `LvlPrest` column in the Context list;
  - whether type-2 rooms consume DS1 substitution groups;
  - the town callback `act[+0x488]` and the level-27 index write.
- **Outputs:** `docs/findings/drlg/0004-preset-units.md`; `re/symbols.csv` rows (subsystem `drlg/preset`), renames of
  the `sub_` rows read to the instruction; `re/types/` for the preset-instance (`0x58`) and preset-unit records.
- **Done when:**
  - `sub_00667620_PresetUnitDropRolls` is read to the instruction: units selected, draw function and operand,
    comparison, effect on the unit list, seed per caller (`[I]` or better), plus a scratch model that reproduces its
    52 logged calls of run:2026-10-12-drlg-gen (support only);
  - the unit pipeline is written as pseudocode with every rewrite. Each MonPreset range says what the room's unit
    record holds, and the record goes to `monsters/spawn` or `objects` at a named boundary function;
  - each `LvlPrest` column of the Context list has a meaning with an anchor, or "no reader in `Game.exe`" with the
    xref search that shows it, or "presentation only" with the reader named;
  - type-2 substitution groups: consumed (read the consumer) or not (show it);
  - the town callback and the level-27 write are read, with the draws they make on the act or level seed;
  - the Phase 2 logging points are named (addresses after a return where needed, as in plan 0010).

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch and register at least one community source on DS1 units and paths and one on `LvlPrest` columns,
  then compare per `evidence-rules.md` § Community cross-checks: blind first, and agreement never promotes.
- **Outputs:** `docs/sources.md` entries; verdicts in drlg/0004 *Leads used*; backlog entries for each `contradicted`.
- **Done when:** the drop rolls, the act rewrites, each `LvlPrest` column of the Context list and the path `action`
  each carry a verdict with a `src:` id (or `not covered`). Every `contradicted` claim is a required case of Phase 2.

### Phase 2 — Bit-exact reproduction, oracle removed
- **Owner skill:** reverser (a human may play, as in plan 0008's Catacombs entry)
- **What:**
  - model the drop rolls and the unit pipeline in `tools/drlg.py` (DS1 through `tools/ds1.py`);
  - give `gen` and `roomk` a switch that uses the model in place of the `0x00667620` oracle (ADR-0004: the oracle
    becomes a switch, the old logs are re-run);
  - add a `units` check that predicts each preset room's unit list.
- **Logging:** extend `tools/gdb/drlg-gen.gdb`:
  - per preset instance: `Def`, file index, file;
  - per room after `PresetUnitsToRoom`: the unit list (kind, id, x, y, mode/flags, path length);
  - the drop rolls' seed in and out and each draw.
- **Done when:**
  - run:2026-10-12-drlg-gen and run:2026-10-11-drlg-roomk replay with **no preset oracle**, every seed asserted as
    before;
  - a new run `run:YYYY-MM-DD-drlg-preset` reproduces the unit list of at least 200 preset rooms:
    - all five acts and every town, including a rebuilt level;
    - at least 20 drop-roll calls that draw, with both outcomes;
    - level 27 built (its index from the act-seed draw);
    - one preset level, one outdoor preset cell and one maze preset room per act where the act has them;
    - at least one non-normal difficulty game, which shows whether anything differs;
  - the Phase 1b cases are included;
  - in-scope claims are promoted to `[C]` citing the run, the `drlg/README` boundary row for `0x00667620` is answered
    through the backlog to the spec-writer, and `LvlPrest`'s `[L]` meanings go to the archivist through the backlog.

### Phase 3 — Spec: drlg/preset
- **Owner skill:** spec-writer
- **What:** write `docs/specs/drlg/preset.md`. Update `docs/specs/drlg/README.md`: remove the oracle row from
  *Sub-generator boundaries* and link the new spec.
- **Done when:**
  - the spec follows the template and every statement is tagged;
  - it includes a worked example from the run: DS1 in, drop-roll draws, unit list out;
  - the boundaries to `monsters/spawn`, `objects` and `drlg/collision` are stated;
  - the architect's review passes.

## Open questions

- **Are DS1 substitution groups a preset concern?** drlg/0002 runs the `LvlSub` passes for type-1 rooms only. If
  Phase 1 confirms that no type-2 room reads them, the research map moves `LvlSub` from this row's key tables to
  `drlg/outdoor`, and DS1 (e) goes with it.
- Monster preset units hand over at `sub_005559A0_RoomPresetUnits` (monsters/0002 § 7). If the keep/drop rolls turn
  out to run there and not in DRLG, the boundary moves and Phase 2 logs at the spawn side instead.
- `0x0061B210+0x133`, the third caller of the drop rolls: if it is client-only, it is named and not reproduced (the
  reference is the server's room).
- Room activation and preset NPC paths may interact with monster AI, which is out of scope (ADR-0002). The spec
  stops at the path data the unit carries.
- This plan does not cover the act link builder (`sub_006772C0_LevelLinkBuild`), only the file indices it writes.
  The link builder itself is `drlg/warps`.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-13 — Drafted (architect).** The first DRLG generator row after `drlg/overview` was reviewed (plan 0008
  closed). Chosen ahead of maze and outdoor because its inputs are fully documented (DS1, LvlPrest, the file-index
  draw `[C]`) and its last oracle is one function. Most of the work is static, so it runs alongside plan 0014's
  owner sessions.
- **2026-10-13 — Approved (human).** No changes to the draft. Phase 0 (archivist) is next.
- **2026-10-13 — Phase 0 landed (archivist).** `python3 -I tools/ds1.py units workspace/merged` runs over all 2058
  `File1..6` references (2043 files) and the LvlSub DS1s and exits 0 in about 1 s. It is registered in the gate
  as `ds1_units`, with a baseline. Results are in [ds1.md § Preset unit survey](../formats/ds1.md#preset-unit-survey)
  and [LvlPrest § Survey by generator kind](../tables/LvlPrest.md#survey-by-generator-kind-plan-0016-phase-0),
  as counts only.
  - 16 372 units: 2 102 monsters, 165 npc, 14 105 objects, no items.
  - Every MonPreset range has a count in every act, and no entry passes through raw.
  - Every object goes through the per-act table, and none maps to −1.
  - 117 paths, all owned. `flags` is set on one referenced unit only.
  - The `0x84` list has six shared files, none at two sizes, so the candidate list is effectively empty.
    `tri_town4` is the only file shared across levels (38, 136).
  - Generator kinds: 35 preset-level records (`[I]` by `LevelId`). 603 maze and 357 outdoor by a data-only DT1
    match (`[L]`), with the maze rotation ranges agreeing. 93 stay "maze or outdoor" (level types 22 and 28 serve
    both). 3 have no file.
  - Data for the open question on type-2 groups: LvlPrest files carry 429 groups, 93 of them in crypt maze rooms
    (the only `unk` 1 values) and 334 in outdoor cells.
  - Surprise: [MonPreset](../tables/MonPreset.md) said the two `siege_32x32?boss.ds1` files pass through raw. With
    the reader's act clamp they don't. Corrected.
  - Questions to the reverser are in the backlog (2026-10-13 archivist → reverser).
- **2026-10-13 — Phase 0 reviewed (architect): accept with fixes.** Anchors resolve, the totals reconcile, the
  survey reruns at exit 0 and matches its gate baseline. Fixes for the archivist, none blocking Phase 1:
  1. [LvlPrest § Survey by generator kind](../tables/LvlPrest.md#survey-by-generator-kind-plan-0016-phase-0):
     "a record inside a maze rotation range is taken as maze" is the classifier's rule, not an observation.
     Tag it `[L]` or leave it untagged as method.
  2. The act-3 rows of the units-per-act and MonPreset-range tables may be off by the two `0x004E6C50` rewrite
     ids. Mark them provisional until Phase 1 reads that function.
  3. `Beta` is missing from the per-kind table. Add one line: no `.bin` field, not surveyed.
  4. `tools/ds1.py units`: with no `game.exe`, the object table is `None` and the "no object maps to −1" check
     passes without running. Put the table's presence in the `SURVEY` line (e.g. `objtab=1`) so the baseline
     catches it.
  5. Nit: spell out the maze `SizeY` cell ("as `SizeX` but …").
- **2026-10-13 — Phase 0 review fixes applied (archivist).** All five fixes:
  1. The LvlPrest maze-rotation sorting rule is now `[L]` and described as the survey's rule.
  2. The act-3 rows in [ds1.md](../formats/ds1.md#units-per-act-and-type) and [MonPreset](../tables/MonPreset.md) are
     marked provisional until `0x004E6C50` is read.
  3. LvlPrest notes that `Beta` has no `.bin` field.
  4. `tools/ds1.py units` prints a `NOTE` and `objtab=0` when the pinned `game.exe` is absent. The gate baseline
     now carries `objtab=1`, so a run without the object table fails the gate.
  5. The maze `SizeY` cell is spelled out.
- **2026-10-13 — Phase 1 landed (reverser).** [drlg/0004](../findings/drlg/0004-preset-units.md), all `[I]` except the
  map-scan draw count. That count is `[C]`: a scratch model reproduces the exit seed of all 91 logged map-scan calls
  (the 52 of run:2026-10-12-drlg-gen plus 39 from the owner catacombs log). Only 2 calls draw, both on Lut Gholein's
  `act2vendor1/2`. 12 new `re/symbols.csv` rows (`drlg/preset`), 9 rows moved to `drlg/preset`, and
  `re/types/preset.h` (`PresetInstance` 0x58, `PresetUnit` 0x20, `PresetPath`).
  - **Drop rolls.** Ten ids draw once each:
    - MonStats 204/205/371/372 (kept 1/3);
    - `place_group25/50/75` (kept 3/4, 1/2, 1/4: inverse to the names);
    - objects 196/261 (1/2);
    - object 581 (3/4).

    Each instance rolls once: on the level seed in `PresetMapScan` when `Scan || Pops`, otherwise on the room seed
    of the instance's first-loaded room. The "third caller" is `RoomPrepareFiles`.
  - **Act-3 rewrites.** 297 → object 382, 366 → object 404. `0x004E6C50` is only a range check.
  - **`flags` bit 0** makes `sub_005559A0_RoomPresetUnits` skip the unit, so it never spawns on the server.
  - **Columns.** Every Context column has a reader or a stated search, and none draws:
    - `Logicals` selects the monster spawn boxes;
    - `+0x024` is the animation period;
    - `AutoMap` gates act callbacks that are null on the server and drive the automap on the client;
    - `PopPad` has no reader.
  - **Type-2 rooms never read DS1 groups.** No shipped DS1 is split two ways, so the `0x84` case does not occur.
  - **Level 27:** index `2 − (r&1)` for link value 1, or `(~r)&1` for 3, from one act-seed draw.
  - **Not done.** Renames of the `sub_` rows read to the instruction were held back. Each name is cited across
    drlg/0001–0003, the drlg specs and the plans, so a rename means a citation sweep. The architect can ask for it
    at close.
  - **Phase 2 logging points** are in drlg/0004. Backlog entries go to the archivist (column links, act-3 ids) and
    the architect (`LvlSub` to `drlg/outdoor`, an owner for `sub_0066D110_SpawnBoxesFromDs1`). Phase 1b
    (community cross-check) is next.
- **2026-10-13 — Phase 1b landed (reverser).** Community cross-check of [drlg/0004](../findings/drlg/0004-preset-units.md#leads-used):
  14 verdicts, after the finding was written blind. Agreement promoted nothing.
  - **Sources** fetched and read, then registered in [sources.md](../sources.md):
    - new: `pk-lvlprest-guide` (Phrozen Keep, 1.10–1.14), `d2dfg-blizzard` (Blizzard's Data File Guide, no version
      stated), `siramy-ds1-any-units` (1.10) and `pk-hardcoded-ds1`;
    - re-fetched: `siramy-ds1edit` (§ Path Editing).
    - Two pages were registered `rejected: contains decompiled code` and not used: `pk-maze-ds1-mechanisms`
      (disassembly) and `nefarius-metalstorm-log` (a game-code snippet).
  - **Keep/drop rolls and act rewrites: not covered.** No source found says a preset unit appears by chance, or
    names the act-index 2/4 rewrites. The `place_group25/50/75` keep probabilities (3/4, 1/2, 1/4) rest on the
    code alone.
  - **Contradicted (3), each a required Phase 2 case** (backlog 2026-10-13 reverser → reverser):
    - `Populate`: the sources say no monsters/units spawn. The finding stops only random population, and the shipped
      `Populate` 0 files carry type-1 units (Harrogath, act-3 treasure rooms).
    - `Logicals`: the sources say wall transparency, and the finding says spawn boxes.
    - `PopPad`: the sources say trigger-line offset, and the finding found no reader.
  - **Held:** `KillEdge`. **Held with refinement:** `Outdoors`, `Animate`, `FillBlanks`, `AutoMap`, `Scan`, `Pops`.
    **Not covered:** `+0x024`, path `action`. Siramy's "hardcoded animation and/or sound" lead for `action` goes
    under the finding's Open questions.
  - Not done, as agreed: the `sub_` renames and the open backlog items for the archivist and the architect. Phase 2
    is next.
- **2026-10-13 — Phase 2 landed (reverser).** [drlg/0004](../findings/drlg/0004-preset-units.md) corroborated by
  [run:2026-10-13-drlg-preset](../findings/drlg/experiments.md#run2026-10-13-drlg-preset). The run had 27 logs: 20
  scripted town entries over five acts and three difficulties, two scripted `PopPad`/`Logicals` walks, and one
  owner-played game per act.
  - **Oracle removed.** `tools/drlg.py gen` models `sub_00667620_PresetUnitDropRolls` (`--preset-oracle` keeps the
    old oracle). run:2026-10-12-drlg-gen replays with every seed asserted: 91 calls, 21 244 checks, 0 mismatches.
    run:2026-10-11-drlg-roomk never used the oracle (the roll precedes its window) and still gives 520 activations,
    0 mismatches.
  - **Done when, met:**
    - 2210 preset room unit lists reproduced (1088 with units), all five acts and towns, with rebuilt levels in Acts I
      and II;
    - 962 roll calls, 44 of them drawing, with both outcomes for MonStats 204/205, `place_group50` and object 581;
    - level 27 built with its link-draw index;
    - a preset level, outdoor cells and maze rooms (Acts I, II);
    - Nightmare and Hell (nothing differs);
    - 123 606 checks, 0 mismatches.
  - **Done when, not met:** no maze preset room in Acts III and V. Only Act I could use waypoints (the test save has
    no quest progress); the owner walked Acts II–V from town. Several drawing ids were never reached; they stay `[I]`
    (list in the run's Deviations).
  - **Phase 1b cases:**
    - `Populate` 0 rooms give pop level 0 and still spawn preset monsters. The sources are wrong for 1.14d.
    - `Logicals` builds DrlgLogic regions that the client's wall cut-away reads every frame, so the sources were
      right. `sub_0066D110_SpawnBoxesFromDs1` is renamed `sub_0066D110_LogicRegionsFromDs1`.
    - `PopPad` has a reader after all (`sub_006671E0_PresetPopsUpdate`, the trigger rectangle's width and height),
      and the model reproduces 6443 player positions.
  - **New in the finding:** two more writers of the no-population flag (next to a town, hidden warp tiles); the
    server walk's two passes and its level 133–136 filters; units other code prepends to room lists.
  - **Tools:** the logger is `tools/gdb/drlg-preset.gdb` (+ `-poppad`, `-logicals`) with `drlg-preset.py` and
    `drlg-preset-wp.py`. The test characters come from `tools/preset_saves.py`.
  - 6 new `re/symbols.csv` rows, 1 rename, 9 rows raised to `C`.
  - Backlog: the spec-writer (the boundary row is answered), the archivist (LvlPrest meanings, the act-index-2
    rewrites in `tools/ds1.py`), monsters/0002 (the flag writers, the walk order, the narrow "spawn box" names) and
    the architect (review).
  - Not done, as agreed: the held-back `sub_` renames, and the open archivist and architect items.
- **2026-10-13 — Phase 2 reviewed (architect): accept with fixes.** The checker reruns as recorded:
  `python3 -I tools/drlg.py gen workspace/logs/preset-*.log` gives 2210 preset rooms, 123 606 checks, 0 mismatches.
  Anchors resolve in `re/symbols.csv` (`0x00667620`, `0x00666710`, `0x006671E0`, `0x0066BD50`, `0x0066D110`). The
  three Phase 1b required cases are settled, and their backlog entries are struck. Decisions:
  - **Maze preset rooms in Acts III and V: waived for this plan.** The maze path is one call site
    (`PresetRoomsCreate` from the maze builder, `0x00673AAF`) and has no act-dependent branch. Acts I and II exercise
    it on six levels. The act-dependent code (the `DS1_Parse` rewrites) was reached in Acts III and V through the
    towns. The cases go to an opportunistic owner session (backlog). They don't gate Phase 3.
  - **Unreached branches stay `[I]`, and that is acceptable for Phase 3.** Each one is a single comparison on a draw
    whose position and seed are `[C]` through a sibling id. The spec states them `[I]` and names them. No `[L]` is
    involved.
  - **Input boundary.** The units at the head of the server walk are a legitimate input. They carry no seed, the
    modelled list is asserted as the exact tail, and the room-seed assertion would catch an interleaved draw. This
    is a row boundary, not an ADR-0004 oracle. The act seed before the level-27 draw is logged and not asserted, so
    the run corroborates the formula (one draw on the given state gives the index) but not the draw's position in
    the act-seed sequence. That position is `drlg/warps`' to establish. Fix 3 scopes the tag. A third input is not
    named anywhere (fix 2).
  - **Renames.** Held to the plan close, as agreed. Phase 3 cites the current `re/symbols.csv` names. The
    `SpawnBox*` sweep stays with monsters/0002's next pass (backlog 2026-10-13 reverser → reverser).
  - **Server read of the logic boxes** (`0x0054ED03`) is a `monsters/spawn` claim (monsters/0002 § 5, `[I]`), and
    it is not a blocker here. It is already in that backlog entry.
  - **Phase 1 architect items** (backlog 2026-10-13 reverser → architect, Phase 1):
    - `LvlSub` and DS1 (e) move from `drlg/preset` to `drlg/outdoor` on the research map.
    - The logic-region flood (`sub_0066D110_LogicRegionsFromDs1`, `sub_0066CA50_LogicBoxesFromGrid`,
      `sub_0066C9C0_LogicWallBoxes`) goes to `drlg/collision`, which owns the room's spatial structures that spawn
      and objects consume. `drlg/preset` states only which builder `Logicals` selects and the flag bit.

  Fixes (reverser; 1–3 before Phase 3, because they change tags the spec copies):
  1. **`Logicals` `[C]` reaches past the run.** The checker tests only `flags & 3` per `Logicals` (`tools/drlg.py`,
     `LGB`) and counts the watch reads. Region ids, the cross-room merge, the box runs and wall entry `+0x10` are not
     reproduced. Split the Answer bullet and the § LvlPrest columns row. The `[C]` part is the selection, the flag
     bit and the client reader. The flood is `[I]`. `0x0066D110` goes to `I` in the Functions table and
     `re/symbols.csv`.
  2. **Unnamed log input.** `PTR0` takes the room list that already exists before `PresetUnitsToRoom` from the log
     (108 rooms, coverage line "room list not empty before PresetUnitsToRoom"). Neither the experiment record nor
     drlg/0004 names it. Name it as an input next to the walk-head units, and attribute it (re-activation, warp or
     object placement) or put it under Open questions.
  3. **Level 27 tag scope.** drlg/0004 Answer and the experiment Checks: the `[C]` covers the index formula on the
     logged act seed. The draw's place in the act-seed sequence is `[I]` and is input from `drlg/warps`.
  4. **Count.** drlg/0004 says 22 rooms at `0x0066BD92`. The experiment says 16. The checker counts 22 flag sets,
     and 16 is presumably the `RoomPopLevelId` calls on those rooms. State both counts with their meanings in both
     places, and in the monsters/0002 backlog entry.
  5. Nit: the `[C]` bullet on the other `0x800000` writers holds an `[I]` claim (`0x0066E37E`) inline. Split it.
  6. From the Phase 1 entry: [findings/README](../findings/README.md) still has no rows for drlg/0001–0004.

  Phase 3 (spec-writer) may start once fixes 1–3 land. Fixes 4–6 can land any time before close.
- **2026-10-13 — Phase 2 review fixes 1–3 applied (reverser).**
  1. **`Logicals`.** The `[C]` now covers the builder selection (logic flag bit per `Logicals`) and the client
     cut-away reads. What the builders produce (regions, ids, the cross-room merge, boxes, wall `+0x10`) is a separate
     `[I]` bullet that names the owner `drlg/collision`. The § LvlPrest columns row is split the same way.
     `0x0066D110` is now `I` in the Functions table and in `re/symbols.csv`.
  2. **The re-prepared room list is now asserted, not just named.** All 108 non-empty lists before
     `PresetUnitsToRoom` belong to rooms prepared a second time. Each one holds the room's previous list. In 34 rooms
     other code had added 1 or 3 units at the head, and in 19 monster units the path pointer had become null in
     between (who detaches it is an Open question, owner `monsters/spawn`). No re-prepare moves a unit.
     - `tools/drlg.py gen` asserts the previous modelled list as the tail, allowing only the detached path:
       123 714 checks, 0 mismatches (108 more).
     - run:2026-10-12-drlg-gen is unchanged (21 244 checks, 0 mismatches).
     - The new `[C]` bullet is in drlg/0004. The experiment record has an *Inputs taken from the log* item and the
       re-check with the checker's hash.
  3. **Level 27.** The `[C]` is the formula and the single step on the logged act seed. The draw's place in the
     act-seed sequence is a separate `[I]` bullet that names `drlg/warps`. The experiment record says the same.

  Fixes 4–6 are still open (backlog). Phase 3 (spec-writer) can start.

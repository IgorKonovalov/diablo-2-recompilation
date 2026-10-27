# Objects (`data/global/excel/objects.txt` → `objects.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 573 (one `Expansion` marker row, not compiled)   **Record:** 448 B (`0x1C0`)
> **sha256:** `.txt` `9363c86bc6ce61549e162d176ad8398567aca1b433f076b729d4246bf478865c`, `.bin` `8a4c980e3f1a777d2c390d8a71dde4a76974ca5bf2ac8cd7b8766db1ea7f8639`
> **Doc status:** complete for layout (every byte placed or listed); semantics `[I]` for the columns the collision code
> reads ([drlg/0005](../findings/drlg/0005-collision.md)) and for the populate, init and operate readers of
> [objects/0001](../findings/objects/0001-object-population.md) (plan 0023 Phase 1, [§ Code semantics](#code-semantics-plan-0023-phase-1)),
> `[L]` for the rest; DS1 survey of the classes objects/0001 singles out

## Purpose

One row per object class: chests, caskets, urns, barrels, shrines, wells, doors, waypoints, portals, corpses, torches,
quest objects and many `Dummy` placeholders. A row gives the object's footprint and collision per mode, its animation
(frame counts and speeds per mode, lights, composite parts), and the numbers of the server handlers that set it up
(`InitFn`, `PopulateFn`), run when a player uses it (`OperateFn`) and draw it on the client (`ClientFn`), with
eight handler parameters `Parm0..7`. Readers known so far: the collision code (`UNIT_GetSizeX`/`Y`,
`UNIT_GetCollMask`, the mark), the DRLG map scan (waypoints), the waypoint lookup. Placement and creation are the
research-map row `objects` (plan [0023](../plans/done/0023-objects.md)). [ObjGroup](ObjGroup.md) `ID0..7` and the DS1
object entries ([ds1.md](../formats/ds1.md#objects-v--2)) name rows of this table. The mode index of the eight-column
runs (`Mode0..7`, `HasCollision0..7`, …) is the row of [ObjMode](ObjMode.md). Leads: no lead read; derived from data
(`src:d2dfg-blizzard` § Objects is for plan 0023 Phase 1b).

## Row identity

- `[C]` The `.bin` is a u32 record count (573) and 573 records of 448 bytes: one per `.txt` row in order, the
  `Expansion` marker row (after `.txt` row 409) left out ([excel-bin.md](../formats/excel-bin.md)). The loader call
  passes record size 448 (0x00640DDE, [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[C]` **`Id` is not compiled, and it is not the record index everywhere.** `Id` equals the record index for records
  0..409 and 413..572; records 410, 411, 412 (`Siege Control`, `ptox`, `pyox`) carry `Id` 408, 409, 410, so `Id` 408 and
  409 occur twice and 411, 412 never. No byte of the record holds `Id` (`probe`: no offset under any encoding).
- `[I]` The object class number used by the game (DS1 object entry, `ObjGroup` `ID*`, the unit's class) is the record
  index (`OBJECTS_GetRecord`, [§ Code semantics](#code-semantics-plan-0023-phase-1), fn:OBJECTS_GetRecord@0x00640E90). `[I]` The preset dispatch sends DS1 type-2 ids `> 573` to `0x0054F490` and does nothing for `573`, every other
  id to `SUnitCreate` ([drlg/preset § 6](../specs/drlg/preset.md)); with 573 records, 573 is the first id past the
  table (fn:sub_005557D0_PresetUnitDispatch@0x005557D0).
- `[C]` `Name` is not unique (198 distinct over 573 rows: `Dummy` 106, `Shrine` 49, `chest` 39, `Door` 19,
  `Waypoint` 16). `Token` (2 characters, 521 distinct; `ss` 26 times) is not a key either.

## Layout verification

`[C]` `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel objects`: 573 records × 156 mapped
fields = 89 388 cells, **0 mismatches**. `excel_bin.py unknown … objects` lists only the six `U` fields below, each
with one value (zero) in all 573 records; no other byte is uncovered. Layout in `tools/excel_layouts.py`
(`LAYOUTS["objects"]`); the gate baseline `tools/gate/baselines/excel_layout.txt` carries `objects_cells=89388`.

**Bytes with no `.txt` column** (zero in every record, `[C]` value; meaning `[L]`):

| Offset | Size | Name in layout | Note |
|---|---|---|---|
| `+0x040` | 128 | `unk_040` | after `Name` (`char[64]`); zero in the file. `[L]` a buffer filled at load (a wide-character name would fit 64 × 2 B) |
| `+0x147` | 1 | `pad_147` | after `Mode7`, before the s32 `Xoffset` |
| `+0x16C` | 1 | `unk_16C` | between `NameOffset` and `MonsterOK` |
| `+0x16F` | 1 | `unk_16F` | between `OperateRange` and `Act` |
| `+0x176` | 2 | `pad_176` | after `Sync`, before the s32 `Parm0` |
| `+0x19E` | 2 | `pad_19E` | after `CollisionSubst`, before the s32 `Left` |

**`.txt` columns with no field:** `description - not loaded` (comment; its header says so), `Id` (above),
`Flicker` (0/1, 44 rows set; `probe` finds no offset under any encoding), `ShrineFunction` (0 in every row: it could
sit in `+0x16C` or `+0x16F`, which are also 0 everywhere, so the data cannot place it; the layout leaves it out).

**Placed by stride, not by probe** (`[C]` bytes, `[L]` which column is which): where a run of columns is equal in every
row, `probe` finds the run but not the order, and where a column is constant it matches almost anywhere. The layout
continues the run's stride:

- `Selectable4..7` (equal in every row) → `+0x0C8..+0x0CB`; `CycleAnim4`/`5` and `6`/`7`; `Lit4`/`5` and `6`/`7`;
  `HasCollision4`/`5`; `OrderFlag3..7` (equal in every row);
- constant columns: `nTgtBX`, `nTgtBY` (0), `Start0`, `Start6`, `Start7` (0), `TR` (1), `LG`, `RA`, `LA`, `RH`, `LH`,
  `S5..S8` (0). `Damage` (100 everywhere) matches only `+0x19C`.
- widths: a column `probe` accepts as u8 to s32 at one offset takes the width up to the next placed field (e.g.
  `TrapProb` u32 at `+0x0CC`, `Width`/`Height` s32). Signed where the data has negative values (`Xoffset`,
  `Yoffset`, `NameOffset`, `Parm*`, `Left`, `Top`, `Xspace`).

## Columns

Value ranges are from the `.txt` over the 573 rows (equal to the decoded `.bin`, since the diff is clean); value
counts from `python3 -I tools/obj_survey.py objects workspace/merged/data/global/excel`. No column has a blank cell.
"Code reads" cites the reader where one is anchored; everything else is `[L]` by column name.

### Identity and spawn

| Column | Observed type / range | `.bin` field | Meaning (`[L]` unless stated) | References | Layout tag |
|---|---|---|---|---|---|
| `Name` | str ≤ 30 chars, 198 distinct | `+0x000` `char[64]` | editor / debug name | — | [C] |
| `description - not loaded` | str ≤ 60 chars | — | comment | — | [C] |
| `Id` | int 0..572, 408/409 twice | — | see *Row identity* | — | [C] |
| `Token` | str 2 chars (one row `NU0`) | `+0x0C0` `char[3]` | graphics token (the `objects/<token>/` art folder); `[C]` stored cut to 2 characters + NUL (`NU0` → `NU`) | — | [C] |
| `SpawnMax` | int {0: 350, 1: 196, 2: 27} | `+0x0C3` u8 | `[L]` how many of this class a populate pass may add per room (name); `[I]` no reader in the image (§ Code semantics) | — | [C] |
| `TrapProb` | int {0: 413, 15: 159, 20: 1} | `+0x0CC` u32 | `[L]` chance (%) that the object is created trapped (name); `[I]` not read by any record fetcher, the trap chance comes from `MonLvl1` (§ Code semantics) | — | [C] |
| `SubClass` | int, bits 0..7 | `+0x167` u8 | class flags, by bit: 0 (`0x01`) shrines, 92 rows; 1 (`0x02`) `Obelisk`, 2; 2 (`0x04`) `Portal` (ids 59, 60); 3 (`0x08`) chests, caskets, urns and other containers, 132; 4 (`0x10`) `portal` (298, 342); 5 (`0x20`) `Well`, 5; 6 (`0x40`) `Waypoint`, 16; 7 (`0x80`) beds and traps, 9. `[I]` bit 2 selects the collision mask `0x8000` (fn:UNIT_GetCollMask@0x006209D0, [drlg/0005 § 5](../findings/drlg/0005-collision.md#5-unit-marks)); `[I]` bit 6 marks the waypoint for the DRLG map scan and the waypoint lookup (fn:DRLG_PresetMapScan@0x00667970, fn:sub_0066B2B0_LevelPointFind@0x0066B2B0, [drlg/preset](../specs/drlg/preset.md)) | — | [C] |
| `Act` | int 0..16, bit set (1: 125, 16: 163, 4: 73, 2: 68, 15: 57, 8: 56) | `+0x170` u8 | `[L]` acts the object may appear in, one bit per act (1 = Act I … 16 = Act V) (name); `[I]` no reader in the image (§ Code semantics) | — | [C] |
| `Beta` | int {0: 340, 1: 233} | `+0x1B0` u8 | — | — | [C] |

### Size, footprint and collision

| Column | Observed type / range | `.bin` field | Meaning (`[L]` unless stated) | References | Layout tag |
|---|---|---|---|---|---|
| `SizeX`, `SizeY` | int 0..32 each; pairs 1×1: 190, 3×3: 95, 0×0: 49, 2×2: 47, 3×1: 24 | `+0x0D0`, `+0x0D4` u32 | `[I]` the footprint in sub-tiles that the object marks in the room collision grid, X × Y (fn:UNIT_GetSizeX@0x00620510, fn:UNIT_GetSizeY@0x006205A0, [drlg/0005 § 5](../findings/drlg/0005-collision.md#5-unit-marks)) | — | [C] |
| `HasCollision0..7` | int 0/1 (mode 0: 473 set, falling to 210 for mode 7) | `+0x120..+0x127` u8 | `[I]` the object marks its footprint when `HasCollision[mode]` is set (read at `+0x120 + mode`, fn:UNIT_CollMarkRect@0x00620A70, drlg/0005 § 5) | `objmode` row | [C] (4/5 by stride) |
| `IsDoor` | int {0: 548, 1: 25} | `+0x13A` u8 | `[I]` door: mask `0x806` with `BlocksVis`, `0x804` with `BlockMissile`, else `0x400` (fn:UNIT_GetCollMask@0x006209D0, drlg/0005 § 5) | — | [C] |
| `BlocksVis` | int {0: 552, 1: 21} | `+0x13B` u8 | `[I]` a door that also blocks sight (mask `0x806`, drlg/0005 § 5) | — | [C] |
| `BlockMissile` | int {0: 547, 1: 26} | `+0x1B6` u8 | `[I]` adds `0x4` to a non-door mask, `0x804` for a door (drlg/0005 § 5) | — | [C] |
| `CollisionSubst` | int {0: 561, 1: 12} | `+0x19D` u8 | — (`probe` match only; no reader read) | — | [C] |
| `Xspace`, `Yspace` | int −7..6 / 0..10; non-zero on 30 rows | `+0x162` s8, `+0x163` u8 | spacing kept free around the object (name) | — | [C] |
| `BlocksLight0..7` | int 0/1 | `+0x118..+0x11F` u8 | the object blocks light in mode k | `objmode` row | [C] |
| `IsAttackable0` | int {0: 543, 1: 30} | `+0x128` u8 | the object can be attacked (mode 0 only) | — | [C] |
| `EnvEffect` | int {0: 569, 1: 4} | `+0x139` u8 | — | — | [C] |

### Modes, animation and drawing

| Column | Observed type / range | `.bin` field | Meaning (`[L]` unless stated) | References | Layout tag |
|---|---|---|---|---|---|
| `Selectable0..7` | int 0/1 (mode 0: 380) | `+0x0C4..+0x0CB` u8 | the object can be clicked in mode k | `objmode` row | [C] (4..7 by stride) |
| `Mode0..7` | int 0/1 (mode 0: 562, 1: 422, 2: 441, 3: 97, 7: 1) | `+0x13F..+0x146` u8 | the object has mode k; `Mode1` `[C]` read by the chest operate ([§ Code semantics](#code-semantics-plan-0023-phase-1)) | `objmode` row | [C] |
| `Start0..7` | int; 0, 0/1, 0..28, 0..29, 0/1, 0/1, 0, 0 | `+0x129..+0x130` u8 | start frame of mode k | `objmode` row | [C] (0, 6, 7 by stride) |
| `FrameCnt0..7` | int 0..50 | `+0x0D8..+0x0F7` u32 ×8 | frames of mode k | `objmode` row | [C] |
| `FrameDelta0..7` | int 0..640 (mostly 0, 128, 256) | `+0x0F8..+0x107` u16 ×8 | animation speed of mode k (256 = one frame per tick, by the usual scale) | `objmode` row | [C] |
| `CycleAnim0..7` | int 0/1 | `+0x108..+0x10F` u8 | mode k loops | `objmode` row | [C] (4..7 by stride) |
| `Lit0..7` | int 0..25 | `+0x110..+0x117` u8 | light radius in mode k | `objmode` row | [C] (4..7 by stride) |
| `OrderFlag0..7` | int 0..2 | `+0x131..+0x138` u8 | draw order in mode k | `objmode` row | [C] (3..7 by stride) |
| `Orientation` | int {3: 429, 0: 60, 1: 58, 2: 26} | `+0x13C` u8 | — | — | [C] |
| `PreOperate` | int {0: 513, 1: 60} | `+0x13D` u8 | the object can be created already operated (name) | — | [C] |
| `Trans` | int {0: 563, 7: 9, 1: 1} | `+0x13E` u8 | palette transform | — | [C] |
| `Xoffset`, `Yoffset` | int −45..20 / −130..20 | `+0x148`, `+0x14C` s32 | sprite offset in pixels | — | [C] |
| `Draw` | int {1: 549, 0: 24} | `+0x150` u8 | — | — | [C] |
| `HD`, `TR`, `LG`, `RA`, `LA`, `RH`, `LH`, `SH`, `S1..S8` | int 0/1 (`TR` 1 everywhere; `LG`..`LH`, `S5..S8` 0) | `+0x151..+0x160` u8 | composite parts used | `compcode` order | [C] (constants by stride) |
| `TotalPieces` | int 1..4 | `+0x161` u8 | number of composite parts | — | [C] |
| `Red`, `Green`, `Blue` | int 100..255 / 55..255 / 0..255 | `+0x164..+0x166` u8 | light colour | — | [C] |
| `NameOffset` | int −250..0 | `+0x168` s32 | vertical pixel offset of the hover name | — | [C] |
| `Left`, `Top`, `Width`, `Height` | int −50..750 / −100..301 / 0..100 / 0..110 | `+0x1A0..+0x1AF` s32 ×4 | selection box; `[C]` `Left` = `Parm0` and `Top` = `Parm1` in 542 of 573 rows | — | [C] |
| `Overlay` | int {0: 562, 1: 11} | `+0x1B5` u8 | — | — | [C] |
| `DrawUnder` | int {0: 542, 1: 26, 2: 5} | `+0x1B7` u8 | — | — | [C] |
| `AutoMap` | int 0..1468, 20 distinct (310: 93) | `+0x1BC` u32 | automap cell (0 = none) | — | [C] |
| `Flicker` | int {0: 529, 1: 44} | — | — | — | [C] (no field) |
| `nTgtFX`, `nTgtFY`, `nTgtBX`, `nTgtBY` | int 0/3, 0/3, 0, 0 | `+0x198..+0x19B` u8 | — | — | [C] (BX/BY by stride) |

### Handlers and behaviour

| Column | Observed type / range | `.bin` field | Meaning (`[L]` unless stated) | References | Layout tag |
|---|---|---|---|---|---|
| `InitFn` | int 0..79, 78 distinct (0: 240, 1: 93, 3: 71, 2: 37, 16: 17, 17: 16) | `+0x1B1` u8 | index of the server init handler run at creation (0 = none) | — | [C] |
| `PopulateFn` | int 0..9 (0: 164, 3: 261, 2: 96, 1: 23, 8: 17) | `+0x1B2` u8 | index of the handler used when the object is placed by a populate pass (0 = none); by data: 1 urns, jars, caskets; 2 the 92 shrine rows plus 3 `Waypoint` and 1 `Obelisk`; 3 chests and most clickables; 4 `Barrel` (7); 5 `Crate` (46); 6 corpses (54–56, 154, 178); 7 `CorpseOnStick` (57, 58); 8 wells; 9 traps (250, 380, 381) | — | [C] |
| `OperateFn` | int 0..73, 73 distinct (0: 142, 2: 92, 4: 74, 14: 61) | `+0x1B3` u8 | index of the handler run when a player operates the object; 32 of the 39 `chest` rows use 4 | — | [C] |
| `ClientFn` | int 0..18 (0: 551) | `+0x1B4` u8 | client-side handler | — | [C] |
| `Parm0..7` | int −20..750, −80..344, 0..40, 0..40, 0..2, 0..6, 0..2, 0..255 | `+0x178..+0x197` s32 ×8 | handler parameters; by data: on shrine rows (`SubClass` bit 0) `Parm0` ∈ {1, 2, 3}, the rest of `Parm2..7` 0; on container rows (bit 3) `Parm0` 18 (78 rows), 0, 20, 1, 15 | — | [C] |
| `OperateRange` | int 0..50 (2: 495) | `+0x16E` u8 | distance from which a player can operate it | — | [C] |
| `Lockable` | int {0: 514, 1: 59} (56 containers) | `+0x171` u8 | the object can be created locked | — | [C] |
| `Gore` | int {0: 560, 1: 13} | `+0x172` u8 | — | — | [C] |
| `Restore` | int {1: 567, 0: 6} | `+0x173` u8 | the object is saved and restored when its room goes inactive | — | [C] |
| `RestoreVirgins` | int {0: 431, 1: 142} | `+0x174` u8 | restore also when never operated | — | [C] |
| `Sync` | int {1: 348, 0: 225} | `+0x175` u8 | — | — | [C] |
| `MonsterOK` | int {0: 402, 1: 171} | `+0x16D` u8 | monsters may operate it (doors) | — | [C] |
| `Damage` | int 100 in every row | `+0x19C` u8 | — | — | [C] |
| `OpenWarp` | int {0: 569, 1: 4} | `+0x1B8` u32 | the object opens a warp | — | [C] |
| `ShrineFunction` | int 0 in every row | — | — | — | [C] (no field) |

## Columns the code is known to read

The offsets the reverser matched by `probe` in plan 0017 Phase 1 (held in the backlog for this table), now all fields of
the layout above and verified by the diff (`[C]` layout). Meanings stay where drlg/0005 left them.

| Anchor | Offset | Reader | Meaning tag |
|---|---|---|---|
| tbl:Objects.txt:SizeX, tbl:Objects.txt:SizeY | `+0x0D0`, `+0x0D4` | fn:UNIT_GetSizeX@0x00620510, fn:UNIT_GetSizeY@0x006205A0 | [I] |
| tbl:Objects.txt:HasCollision0 (`..7`) | `+0x120 + mode` | fn:UNIT_CollMarkRect@0x00620A70 (via `SUnitCreate`, fn:sub_00555230_SUnitCreate@0x00555230) | [I] |
| tbl:Objects.txt:IsDoor | `+0x13A` | fn:UNIT_GetCollMask@0x006209D0 | [I] |
| tbl:Objects.txt:BlocksVis | `+0x13B` | fn:UNIT_GetCollMask@0x006209D0 | [I] |
| tbl:Objects.txt:SubClass | `+0x167` | fn:UNIT_GetCollMask@0x006209D0 (bit 2), fn:DRLG_PresetMapScan@0x00667970 (bit 6) | [I] |
| tbl:Objects.txt:BlockMissile | `+0x1B6` | fn:UNIT_GetCollMask@0x006209D0 | [I] |
| tbl:Objects.txt:TotalPieces | `+0x161` | — (probe only) | [L] |
| tbl:Objects.txt:Xspace, tbl:Objects.txt:Yspace | `+0x162`, `+0x163` | — (probe only) | [L] |
| tbl:Objects.txt:NameOffset | `+0x168` | — (probe only) | [L] |
| tbl:Objects.txt:CollisionSubst | `+0x19D` | — (probe only) | [L] |
| tbl:Objects.txt:DrawUnder | `+0x1B7` | — (probe only) | [L] |

`[C]` by data: the two rows with `SubClass` bit 2 are ids 59 and 60 (`Portal`), as drlg/0005 § 5 states, and the 25
`IsDoor` rows are ids 13–16, 23–25, 27, 47, 62–64, 75, 91, 92, 98, 99, 229, 230, 290–295. Missiles `+0x18A` (the missile
footprint, same backlog entry) belongs to a Missiles table doc, not this one.

## Code semantics (plan 0023 Phase 1)

From [objects/0001](../findings/objects/0001-object-population.md) (static reading, the replay of
run:2026-10-14-objects-window, and the plan 0023 Phase 2 bit-exact run). Phase 1 corroborated (`[C]`) only the slot
loop, the room-seed draws of the shrine, well and trap handlers, and the restore drawing nothing (architect's ruling,
plan 0023 log). Plan 0023 Phase 2's `tools/objects.py check` reproduces run:2026-10-15-objects with 0 mismatches in
142 540 checks (1265 windows, 3009 objects, 89 operated containers; Normal, Nightmare, Hell, classic and expansion,
Acts I–V; [objects/0001 § 12](../findings/objects/0001-object-population.md#12-phase-2-the-bit-exact-run)), which
moves the readers it exercised to `[C]` below. The branches it did not reach stay `[I]`.

- `[C]` **The class is the record index.** `OBJECTS_GetRecord(i)` is `objects.bin` record `i`; the DS1 object ids, the
  [ObjGroup](ObjGroup.md) `ID` columns and `SUnitCreate` all go through it, and `Id` is never read, so records 410–412
  are classes 410–412. In the run every `PopulateFn` handler is called with the member's class as the record index, and
  every object's size, handlers and draws follow from record `class`. (fn:OBJECTS_GetRecord@0x00640E90,
  fn:sub_00555230_SUnitCreate@0x00555230, data:g_ObjPopulateFns@0x00731D00, run:2026-10-15-objects)
- `[C]` **The three handler tables.** `InitFn` indexes `g_ObjInitFns` (run at creation by `OBJ_ServerInit` when
  `InitFn` < 80), `PopulateFn` indexes `g_ObjPopulateFns` (10 entries; ≥ 10 is fatal), `OperateFn` indexes
  `g_ObjOperateFns` (`OBJ_OperateDispatch`; classes 121, 122 and 22 excluded). The `PopulateFn` handlers are
  1 clusters, 2 shrine, 3 scatter, 4 barrels, 5 crates, 6 corpse (+ flies), 7 stick corpses, 8 well, 9 trap. Every
  handler but `PopulateFn` 5 (no stock level names a group with a `PopulateFn` 5 member) and `InitFn` 57/58 was met
  in the run; those stay `[I]`. (data:g_ObjInitFns@0x00731BC0, data:g_ObjPopulateFns@0x00731D00,
  data:g_ObjOperateFns@0x00732D18, fn:OBJ_ServerInit@0x0054F5D0, fn:OBJ_OperateDispatch@0x00584420,
  run:2026-10-15-objects)
- `[C]` **`Mode1` (`+0x140`) is read by the chest operate.** After the drops, `OBJOP_Chest` puts the chest in mode 1 and
  queues its next event when the row's `Mode1` byte is non-zero, else in mode 2; the mode change draws the unit seed.
  (fn:OBJOP_Chest@0x00585F60, tbl:Objects.txt:Mode1, run:2026-10-15-objects)
- `[C]` **Which seed.** The shrine (2), well (8) and trap (9) handlers draw the room seed (2: `1 + 2a` draws, 8: 0 or
  `1 + 2a`, 9: exactly once); handlers 1 and 3–7 draw nothing on it. (run:2026-10-14-objects-window)
  `[I]` Every other draw (handlers 1, 3–7, the trap placement, every `InitFn`, the `PreOperate` roll, the operate
  handlers) is on the game-wide object-region seed. (fn:OBJRGN_Create@0x00546C60)

Column readers (objects/0001 §§ 3–9 and § 12; a `C` tag is run:2026-10-15-objects, `I` the code only):

| Column | Reader | What it does | Tag |
|---|---|---|---|
| `Gore` | slot loop | a member with `Gore` > the limit byte (2, no writer) is skipped; stock 0/1, never excludes | I |
| `Xspace`, `Yspace` | `PopulateFn` 4 and 5 (barrels, crates) | follower step per direction, read as **u8**, so a negative cell is 249..255 (handler 4 uses record 7's) | C (handler 4), I (handler 5, not reached) |
| `Orientation` | `OBJ_PlaceByOrientation` (shrines) | 1: one subtile in from the top edge, `x` drawn in the middle half; 2: the axes swapped; else a plain random point | C (1), I (2) |
| `PreOperate` | `OBJ_ServerInit` | `RNG_Range(O, 14)` = 0 puts the object in mode 2 (opened), chance 1/14, unless unit flag `0x80` | C |
| `Lockable` | `InitFn` 3 (and 57, which runs 3) | locked with chance `(MonLvl1/2 + 8)` % | C (`InitFn` 3) |
| `Sync` | `UNIT_AnimInit` | 0: the animation start draws the object's own unit seed, `RangeB(FrameDelta[mode] >> 3)` | C |
| `Mode1` | `OBJOP_Chest` | non-zero: the opened chest goes to mode 1 and queues an event; else mode 2 | C |
| `Parm0` | `InitFn` 1 (shrines) | 1 → health class, 2 → mana class, other → class 1 with chance 1/10, else class 4 | C |
| `Parm1` | `OBJ_ShrineClassSubst` (forced shrine) | the class a forced non-health shrine becomes (1..572, else 84) | I (not reached) |
| `Parm0`, `Parm1`, `Parm3` | `OperateFn` 22 (wells, `0x005858A0`) | with charges left, a use adds `Parm1 · max >> 8` (`Parm1` in 1/256 of the maximum) to life when `Parm3` bit 1 is set, to mana when bit 0 is, and to stamina, each capped, and frees the `poison` and `freeze` lists; a use that changed something costs a charge and re-arms at `frame + 1 + Parm0`. `[C]` (data) all 14 `OperateFn` 22 rows have `Parm0` 750, `Parm1` 128 (half), `Parm3` 3 (life and mana) ([stats/0002 § 5](../findings/stats/0002-states.md#5-shrines-and-wells), tbl:Objects.txt:Parm0) | I |
| `SubClass` | forced-slot rule | read at the **group index** (a game bug the spec keeps, architect ruling (2)); bit 6 also marks the waypoint for the DRLG scan | I |
| `SpawnMax`, `TrapProb`, `Act` | none found | `SpawnMax` (`+0xC3`) and `Act` (`+0x170`) have no reader in the image (operand scan: no instruction addresses `+0xC3`, no byte read at `+0x170` but a stack array); `TrapProb` (`+0xCC`) none among the 89 functions that fetch an Objects record, [objects/0001 § Plan 0039 batch P1b](../findings/objects/0001-object-population.md#plan-0039-batch-p1b-2026-10-17); the trap chance is `(MonLvl1/8 + 5)` %, not `TrapProb` | I |

(fn:sub_00552610_RoomObjectsPopulate@0x00552610, fn:OBJPOP_Barrels@0x00551850, fn:OBJPOP_Crates@0x00551C00,
fn:OBJ_PlaceByOrientation@0x00550A30, fn:OBJINIT_Chest@0x0054FCB0, fn:OBJINIT_TrapByte@0x0054FBB0,
fn:UNIT_AnimInit@0x00624390, fn:OBJINIT_Shrine@0x0054F9D0, fn:OBJ_ShrineClassSubst@0x00552AC0,
tbl:Objects.txt:Xspace, tbl:Objects.txt:PreOperate, tbl:Objects.txt:Parm0, fn:OBJOP_Chest@0x00585F60,
tbl:Objects.txt:Mode1, run:2026-10-15-objects)

- `[I]` **Rows singled out by their `InitFn`** (objects/0001 § 7): 269 (`dummy`, `InitFn` 28) drops `1 + low mod 9` gold
  piles (1–9; the guide's 1–10 is a contradiction, a required Phase 2 case now that stock DS1s place it, § DS1 survey);
  397 (`sparklychest`) and 455 (`specialchest`) run `InitFn` 57 (chest, then the sparkle flag); class 397 also has its
  own operate table on `low mod 10000`. (fn:OBJINIT_SparklyChest@0x0054FD90, fn:OBJOP_Chest@0x00585F60)
- `[I]` **DS1 ids past the table.** `PresetUnitDispatch` sends ids < 573 to `SUnitCreate`, does nothing for 573, and
  sends 574..582 to `OBJ_PresetPseudoDispatch`: 574–579 fixed shrines (class 136 with a code range), 580 a super chest
  (a random chest with the sparkle flag), 581 a random chest by act, 582 a quest object.
  (fn:OBJ_PresetPseudoDispatch@0x0054F490, fn:OBJ_PresetSuperChest@0x0054F370, fn:OBJ_PresetRandomChest@0x0054F180,
  fn:OBJ_PresetFixedShrine@0x0054F0D0)

## DS1 survey: objects 269, 397, 455 and the pseudo-objects (plan 0023 Phase 1 follow-up)

`python3 -I tools/ds1.py objects workspace/merged [--quiet]` (gate survey `ds1_objects`) lists, for each class objects/0001
singles out, the LvlPrest records whose DS1s place it, after DS1_Parse's id mapping (ids < 150 through
`g_Ds1ObjectIds` from the pinned `game.exe`, ids ≥ 150 as `id − 150`; that mapping is `[I]`, drlg/0001). Counts are `[C]`
by that command; § 2 of its output lists DS1 files no record names (not loaded by the game).

| Class | Units | Files | Records | Where (examples) |
|---|---:|---:|---:|---|
| 269 gold pile dummy | 343 | 165 | 110 | Act I caves, Fallen camps, barracks; Act II sewers; Act III dungeons, clearings, Spider Forest; Act V ice caves, Barricade, temples |
| 397 sparkly chest | 58 | 58 | 37 | the treasure and chest rooms: Cave Treasure 103–107, Crypt Bonebreak/Chest 147–154, sewer and tomb chests 349–352, 472–475, 743–746, Spider chests 664, Dungeon Treasure 703, Ice Pool 1040–1041, Lava 1053–1056 |
| 455 special chest | 10 | 10 | 9 | Act V: Barricade Ruins 943, 947; Ice Theme 1030–1033; Temple Down 1046–1048 |
| 573 | 0 | 0 | 0 | — |
| 574–579 fixed shrines | 0 | 0 | 0 | none in stock data |
| 580 super chest | 54 | 29 | 30 | Cottages 47, Crypt themes, Countess 159, Lair 482–508 (Maggot Lair), Arcane 510–517, Kurast 618–651, Sewer 724, 747, Mephisto Complex 796, Lava 838, 846 |
| 581 random chest | 135 | 45 | 38 | Act III only: Kurast 615–651, Sewer Treasure 747, Temples 748–752, Durance 757–791 |
| 582 quest object | 24 | 4 | 4 | Arcane Summoner 525–528 (6 each) |

- `[C]` Every watched unit reaches its class through `g_Ds1ObjectIds` (route "table"); none uses a raw id ≥ 150. So the
  pseudo-objects come from the act tables, not from DS1 ids written as such. (data:g_Ds1ObjectIds@0x00748AD8)
- `[C]` **No stock DS1 places 573 or the fixed shrines 574–579**: `OBJ_PresetFixedShrine` is unreachable on stock data.
- `[C]` **Object 269 is placed by stock data** (110 records), so InitFn 28's `1 + low mod 9` against the guide's 1–10 is
  reachable: a required Phase 2 case by the architect's ruling (3) (plan 0023 log). The sparkly-chest case is reachable
  through 397 (37 records) and 580 (30 records, Maggot Lair 62–64 among them, where `P100(O) > 50` skips the sparkle).
- `[C]` Fifteen DS1 files that no record names also hold watched classes (Act I `cave?con`, `caveroom6`; Act II
  `magtreas`, `tombtreasure`; Act V ice-cave `dreh` rooms, `poolroom07/08`, `landmark1a/2a`).

## Waypoints and portals (plan 0042 Phase 0)

The rows the waypoint and portal code is expected to touch, from `python3 -I tools/travel_survey.py objects
<excel-dir>` (the `SURVEY travel` line is a gate baseline). Columns: `SubClass` `+0x167` u8, `InitFn` `+0x1B1`,
`OperateFn` `+0x1B3`, `PopulateFn` `+0x1B2`, `ClientFn` `+0x1B4` (u8), `Parm0` `+0x178` s32, `OpenWarp` `+0x1B8` u32,
`OperateRange` `+0x16E` u8, all `[C]` layout (§ Columns). The handler address is the u32 entry the index selects in
`data:g_ObjInitFns@0x00731BC0` or `data:g_ObjOperateFns@0x00732D18`, read from the pinned file by the survey (`[I]`:
a static read of the table, the same seven entries read again with r2 at the review; that the index selects that
entry is `[C]`, § Code semantics). The class is the record index ([§ Row identity](#row-identity)); it equals the
`.txt` `Id` on every row below but 410, whose `Id` is 408. The description is the `.txt`'s
`description - not loaded` cell, quoted as data only.

| Class (record index) | `Name` / description | `SubClass` | `InitFn` → handler | `OperateFn` → handler | `PopulateFn` | `Parm0` |
|---|---|---|---|---|---|---|
| 59 | `Portal` / Town portal | `0x04` (bit 2) | 11 → `OBJINIT_TownPortal` `0x00550140` | 15 → `OBJOP_Portal` `0x00584870` | 0 | 0 |
| 60 | `Portal` / Permanent town portal | `0x04` | 12 → `OBJINIT_Portal` `0x0054FE70` | 15 → `OBJOP_Portal` `0x00584870` | 0 | 0 |
| 298 | `portal` / arcane sanctuary portal | `0x10` (bit 4) | 29 → `0x0059BA40` | 34 → `OBJOP_ArcanePortal` `0x005846B0` | 3 | 0 |
| 342 | `portal` / hellgate | `0x10` | 44 → `0x005BCBF0` | 46 → `sub_00584750_DurancePortalOperate` | 0 | 18 |
| 410 | `Siege Control` | `0x08` | 0 | 46 → `sub_00584750_DurancePortalOperate` | 0 | 18 |
| 100 | `Duriel's Lair` / Portal to Duriel's Lair | 0 | 0 | 43 → `OBJOP_LevelPortal` `0x00584D00` | 0 | 0 |
| 377 | `Guild Portal` | 0 | 0 | 43 → `OBJOP_LevelPortal` `0x00584D00` | 0 | 0 |
| 119, 145, 156, 157, 237, 238, 288, 323, 324, 398, 402, 429, 494, 496, 511, 539 | `Waypoint` (16 rows) | `0x40` (bit 6) | 17 → `OBJINIT_Waypoint` `0x00547210` | 23 → `sub_00584E30_WaypointOperate` | 0, 2 or 3 | 0 |

- `[C]` **Waypoints by data.** The 16 rows with `SubClass` bit 6 are exactly the 16 rows with `OperateFn` 23, all with
  `InitFn` 17, `OperateRange` 2, `Restore` 1, `OpenWarp` 0, `ClientFn` 0 (`obj_subclass_bit6=16 obj_op_waypoint=16
  obj_bit6_op_waypoint=16`). Their descriptions name the act or the tileset (act 1 wilderness, act 2, act 2 sewer,
  "celler", act3 town, travincal, pandamonia fortress, valley, inner hell, ice cave, temple, baal's, expansion no snow,
  wilderness), so the class is the art; nothing in the row says which level it serves: the level's waypoint index
  comes from `Levels` `Waypoint` ([Levels § Travel](Levels.md#travel-plan-0042-phase-0)).
- `[C]` `OperateFn` 23 is `sub_00584E30_WaypointOperate`: in run:2026-10-15-objects every waypoint operate (23) went
  through it, 23 times (objects/0001 § 13). `[I]` It marks the level's waypoint and sends the record; travel is
  `sub_00584F60_WaypointTravel`, reached from it ([save/0002 § 4](../findings/save/0002-quest-words.md)).
  (fn:sub_00584E30_WaypointOperate@0x00584E30, fn:sub_00584F60_WaypointTravel@0x00584F60)
- `[I]` **Five waypoint rows draw at each mode change.** 429, 494, 496, 511 and 539 have `Sync` 0 (`[C]` data; the
  other eleven have `Sync` 1), so each of their mode changes draws their own unit seed,
  `RangeB(object seed, FrameDelta[mode] >> 3)` (`FrameDelta` 200 for mode 1, 100 for mode 2); `OBJINIT_Waypoint`
  (`InitFn` 17) puts a town's waypoint straight into mode 2. ([quests/0002 § 2](../findings/quests/0002-travel.md#2-waypoint-activation), fn:UNIT_AnimInit@0x00624390,
  fn:OBJINIT_Waypoint@0x00547210, tbl:Objects.txt:Sync)
- `[I]` **Bit 6** marks the waypoint for the DRLG map scan (`DRLG_PresetMapScan`, room flag `0x30000`) and the
  waypoint lookup `LevelWaypointRoom` (first type-2 preset object with the bit) (drlg/0007 § 1, drlg/0005 § 9).
  (fn:DRLG_PresetMapScan@0x00667970, fn:sub_0066AD80_LevelWaypointRoom@0x0066AD80)
- `[C]` **Town portals by data.** Bit 2 is on 59 and 60 only; they share `OperateFn` 15 and differ in `InitFn`
  (11 vs 12) and `Restore` (0 vs 1). `[I]` Class 60 is the portal `PortalObjectCreate` makes for the cow level
  (items/0008 § 5.1) and its `InitFn` 12 (`OBJINIT_Portal`) marks it at once (drlg/0005, objects/0001); it sets the
  destination from the level it stands on (1 ↔ 39, 4 ↔ 38, 46 ↔ 74, 109 ↔ 121, 111 ↔ 125, 112 ↔ 126, 117 ↔ 127, the
  true tomb ↔ 73). `[I]` A Town Portal scroll or book (`pSpell` 2, `ITEMUSE_TownPortal`) makes a class-59 pair: the
  field end at the player, the town end at the town's point type 11; `OBJINIT_TownPortal` (`InitFn` 11) sets the
  destination to the act's town. `OBJOP_Portal` (`OperateFn` 15) moves the user to the partner; someone else's
  class-59 portal is refused when the destination's `QuestFlag`/`QuestFlagEx` word lacks bit 0
  ([Levels § Travel](Levels.md#travel-plan-0042-phase-0)). ([quests/0002 § 6](../findings/quests/0002-travel.md#6-town-portals), fn:ITEMUSE_TownPortal@0x005BE290,
  fn:OBJINIT_TownPortal@0x00550140, fn:OBJOP_Portal@0x00584870) `[L]` What bit 2's collision mask `0x8000` does to
  the pair is not read.
  (fn:sub_0056D130_PortalObjectCreate@0x0056D130, fn:OBJINIT_Portal@0x0054FE70, fn:UNIT_GetCollMask@0x006209D0)
- `[C]` **Bit 4 by data** is on 298 (Arcane Sanctuary portal) and 342 (hellgate). `[I]` `OperateFn` 46 is
  `sub_00584750_DurancePortalOperate` (needs word 22 bit 13 or bit 0, then the Act IV travel, save/0002 § 2).
  **410 `Siege Control` shares `OperateFn` 46 and `Parm0` 18** with 342. `[I]` The handler does not read the class or
  `Parm0`: `0x00584750` takes the level of the operated unit's room (`sub_00620BB0_UnitGetRoom`,
  `sub_0061A1B0_RoomGetLevelId`), tests word 22 bits 13 and 0, and calls `sub_00546AC0_DuranceActTravel` with that
  level, which does the Act IV travel only on level 102 (`cmp …, 0x66`) and otherwise calls `0x005BCFD0` (not read);
  marking waypoint 103 and the move to level 103 are also gated on 102 (static read at the Phase 0 review, objdump;
  plan 0042 log). `[I]` On any level but 102, `0x005BCFD0` opens the Mephisto portal and bridge objects and moves no
  one, so 410 `Siege Control` would move no player; and no DS1 id, `objgroup` cell or creation call names 410, so it
  is never placed ([quests/0002 § Answer](../findings/quests/0002-travel.md#answer-summary), quests/0001 § 10).
  (fn:sub_00584750_DurancePortalOperate@0x00584750, fn:sub_00546AC0_DuranceActTravel@0x00546AC0)
- `[I]` `OperateFn` 43 is `OBJOP_LevelPortal`, shared by 100 (Portal to Duriel's Lair) and 377 (Guild Portal): class
  100 → level 73, class 377 → the level in its object byte, point type 0, no quest test. `OperateFn` 34 is
  `OBJOP_ArcanePortal`: from 74 to 54 at type 0, from 54 to 74 at type 11, then Act II quest code. Both set mode 1
  and queue event 1 when the object is in mode 0. ([quests/0002 § 6](../findings/quests/0002-travel.md#6-town-portals), fn:OBJOP_LevelPortal@0x00584D00,
  fn:OBJOP_ArcanePortal@0x005846B0)
- `[L]` `OpenWarp` 1 is on four rows that are not portals (74 trap door, 194/195 stairs, 386 `Dummy`); not named.

## Timing (plan 0050 Phase 0)

The animation columns, per mode *k* = [ObjMode](ObjMode.md) row (`NU`, `OP`, `ON`, `S1`..`S5`), with the
`animdata.d2` record of the same mode ([animdata](../formats/animdata.md); record name `<Token><ObjMode Token>HTH`,
the weapon class is `HTH` in every object COF name, [cof § Files](../formats/cof.md#files)). Offsets and widths are the
layout's ([§ Modes, animation and drawing](#modes-animation-and-drawing)); values from the `.bin`
(`python3 -I tools/anim_survey.py objects workspace/merged`; survey keys `obj_*`).

| Column | `.bin` field | Observed (573 rows) | Meaning | Tag |
|---|---|---|---|---|
| `Token` | `+0x0C0` char[3] | 573 set | the object's animation token | [C] layout |
| `Mode0..7` | `+0x13F + k` u8 | 0/1; set in 562, 422, 441, 97, 33, 27, 20, 1 rows | the object has mode *k* | [C] layout; meaning `[L]` (`Mode1` `[C]` read by the chest operate, [§ Code semantics](#code-semantics-plan-0023-phase-1)) |
| `FrameCnt0..7` | `+0x0D8 + 4k` u32 | 0..44, 0..50, 0..44, 0..30, 0..25, 0..20, 0..20, 0..10 | frames of mode *k* | [C] layout; `[I]` the animation length at a mode start (below) |
| `FrameDelta0..7` | `+0x0F8 + 2k` u16 | 0..256, 0..640, then 0..256; mostly 0, 128, 256 | animation speed of mode *k* | [C] layout; `[C]` its use at an animation start (below) |
| `CycleAnim0..7` | `+0x108 + k` u8 | 0/1; set in 249, 46, 67, 4, 4, 4, 3, 3 rows | mode *k* loops | [C] layout; `[L]` |
| `Start0..7` | `+0x129 + k` u8 | 0, 0..1, 0..28, 0..29, 0..1, 0..1, 0, 0 | start frame of mode *k* | [C] layout; `[I]` the start frame at a mode start (below) |
| `Sync` | `+0x175` u8 | 0/1; 1 in 348 rows | — | [C] layout; `[C]` (below) |

- `[C]` **`Sync` and `FrameDelta` at an animation start.** `UNIT_SetMode` → `UNIT_AnimInit` draws
  `Range(unit seed, FrameDelta[mode] >> 3)` on the object's own seed when `Sync` is 0, and nothing when the bound is
  below 1 ([objects § G2](../specs/objects/README.md), fn:UNIT_AnimInit@0x00624390, run:2026-10-15-objects). On the
  data: 225 rows have `Sync` 0; 216 of them have a flagged mode with `FrameDelta >> 3 ≥ 1`, 393 (row, mode) pairs in
  all (`obj_sync0_draw_rows`, `obj_sync0_draw_modes`).
- `[C]` **The tables and `animdata.d2` against each other.** Of 1 603 flagged (row, mode) pairs, 1 483 have a record.
  `FrameCnt<k>` equals the record's `frames` in 1 173, is smaller in 308 and larger in 2 (`obj_framecnt_gt`);
  `FrameDelta<k>` equals the record's `speed` in 609, and is 0 in 421 of the pairs (the record's `speed` is 256 in
  1 385 of the 1 483). So the two sources disagree for most modes: the table gives fewer frames (61 `NU`, 38 `ON`
  rows with `FrameCnt` 1 against a longer record) and often a delta of 0 where the record has 256. Per mode in
  [ObjMode § Timing](ObjMode.md#timing-plan-0050-phase-0).
- `[I]` **Which source the server uses** ([anim/0001 § 3](../findings/anim/0001-modes-frames.md#3-unit_setmode-unit_animinit-and-sunit_animinit)):
  the table's. `UNIT_AnimInit` sets an object's length `+0x48 = FrameCnt[mode]`, its frame `+0x44 = Start[mode] << 8`
  and its rate `+0x4C = FrameDelta[mode]` (`Sync` ≠ 0) or `FrameDelta − (FrameDelta >> 4) + RangeB(unit seed,
  FrameDelta >> 3)` clamped to `[0, 0x7FFF]` (`Sync` 0); a mode ≥ 8 is fatal. No server code advances an object's frame
  through these fields (`UNIT_AnimAdvance`'s callers are the monster mode functions and client code). (fn:UNIT_AnimInit@0x00624390, 0x00624500–0x0062456F,
  tbl:Objects.txt:FrameCnt0, tbl:Objects.txt:Start0, tbl:Objects.txt:FrameDelta0, tbl:Objects.txt:Sync)
- `[I]` **The record's token** is [ObjType](ObjType.md)'s, not this table's `Token` ([anim/0001 § 2](../findings/anim/0001-modes-frames.md#2-records-the-token-the-lookup-and-the-fallback),
  `0x0065B570(class, 0)`). `[C]` The two differ in 16 records; under the ObjType token 1 491 of the 1 603 flagged
  modes have a record, against the 1 483 above ([ObjType § Timing](ObjType.md#timing-plan-0050)).

## Interpretation notes

- **Mode-indexed runs.** `[L]` Eleven column groups end in `0..7`: `Selectable`, `FrameCnt`, `FrameDelta`, `CycleAnim`,
  `Lit`, `BlocksLight`, `HasCollision`, `Start`, `OrderFlag`, `Mode`, plus `IsAttackable0` alone. The index is the object
  mode, i.e. the row of [ObjMode](ObjMode.md) (0 `NU` neutral, 1 `OP` operating, 2 `ON` opened, 3..7 `S1`..`S5`
  special). `[I]` for `HasCollision`, read at `+0x120 + mode` (drlg/0005 § 5).
- **Handler numbers are indices into code tables.** `[I]` `InitFn`, `PopulateFn` and `OperateFn` index
  `g_ObjInitFns`, `g_ObjPopulateFns` and `g_ObjOperateFns` ([§ Code semantics](#code-semantics-plan-0023-phase-1),
  data:g_ObjPopulateFns@0x00731D00); `ClientFn` is not read by plan 0023.
- **Containers and traps.** `[C]` by data: of the 132 rows with `SubClass` bit 3, 106 have `TrapProb` 15, 1 has 20, 25
  have 0; 56 are `Lockable`. `TrapProb` is also set on 53 rows that are not containers (stashes, shrines, beds,
  `Dummy`). `[I]` `TrapProb` has no reader in objects/0001: the trap chance is `(MonLvl1/8 + 5)` % in `InitFn` 2;
  `Lockable` gates the lock draw of `InitFn` 3 (fn:OBJINIT_TrapByte@0x0054FBB0, fn:OBJINIT_Chest@0x0054FCB0).
- **Shrine rows.** `[C]` by data: all 92 rows with `SubClass` bit 0 have `PopulateFn` 2 and `InitFn` 1. `[I]` `InitFn` 1 picks the [Shrines](Shrines.md) row at creation from `Parm0` and the level id
  ([Shrines § Code semantics](Shrines.md#code-semantics-plan-0023-phase-1), fn:OBJINIT_Shrine@0x0054F9D0).

## Open questions

- `[L]` The meaning of the six zero byte ranges (`+0x040` 128 B, `+0x16C`, `+0x16F` and the three gaps before s32 fields), in
  particular whether `+0x040` is filled at load. Reverser: the loader `0x00640DDE` and its post-processing.
- `[L]` Which of `+0x16C` / `+0x16F`, if any, the code reads as `ShrineFunction`; why `Flicker` is not compiled.
- ~~The handler tables behind `InitFn`, `PopulateFn`, `OperateFn`~~ answered by objects/0001 (§ Code semantics).
  `[L]` `ClientFn`'s table is not read.
- ~~What the populate pass and the creation handlers read of `Xspace`/`Yspace`, `Lockable`, `PreOperate`, `Parm0`/`Parm1`~~
  answered (§ Code semantics). `SpawnMax` and `Act` have no reader in the image and `TrapProb` none among the record
  fetchers ([objects/0001 § Plan 0039 batch P1b](../findings/objects/0001-object-population.md#plan-0039-batch-p1b-2026-10-17), `[I]`). `[L]` Whether code reads `TrapProb` through a record pointer kept in an object's
  data, and `Parm2..7` outside the shrine, chest and well handlers, is open.

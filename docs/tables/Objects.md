# Objects (`data/global/excel/objects.txt` → `objects.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 573 (one `Expansion` marker row, not compiled)   **Record:** 448 B (`0x1C0`)
> **sha256:** `.txt` `9363c86bc6ce61549e162d176ad8398567aca1b433f076b729d4246bf478865c`, `.bin` `8a4c980e3f1a777d2c390d8a71dde4a76974ca5bf2ac8cd7b8766db1ea7f8639`
> **Doc status:** complete for layout (every byte placed or listed); semantics `[I]` for the columns the collision code
> reads ([drlg/0005](../findings/drlg/0005-collision.md)), `[L]` for the rest (plan 0023 Phase 1 reads the populate,
> init and operate handlers)

## Purpose

One row per object class: chests, caskets, urns, barrels, shrines, wells, doors, waypoints, portals, corpses, torches,
quest objects and many `Dummy` placeholders. A row gives the object's footprint and collision per mode, its animation
(frame counts and speeds per mode, lights, composite parts), and the numbers of the server handlers that set it up
(`InitFn`, `PopulateFn`), run when a player uses it (`OperateFn`) and draw it on the client (`ClientFn`), with
eight handler parameters `Parm0..7`. Readers known so far: the collision code (`UNIT_GetSizeX`/`Y`,
`UNIT_GetCollMask`, the mark), the DRLG map scan (waypoints), the waypoint lookup. Placement and creation are the
research-map row `objects` (plan [0023](../plans/0023-objects.md)). [ObjGroup](ObjGroup.md) `ID0..7` and the DS1
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
- `[L]` The object class number used by the game (DS1 object entry, `ObjGroup` `ID*`, the unit's class) is the record
  index. `[I]` The preset dispatch sends DS1 type-2 ids `> 573` to `0x0054F490` and does nothing for `573`, every other
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
| `SpawnMax` | int {0: 350, 1: 196, 2: 27} | `+0x0C3` u8 | how many of this class a populate pass may add per room (name) | — | [C] |
| `TrapProb` | int {0: 413, 15: 159, 20: 1} | `+0x0CC` u32 | chance (%) that the object is created trapped | — | [C] |
| `SubClass` | int, bits 0..7 | `+0x167` u8 | class flags, by bit: 0 (`0x01`) shrines, 92 rows; 1 (`0x02`) `Obelisk`, 2; 2 (`0x04`) `Portal` (ids 59, 60); 3 (`0x08`) chests, caskets, urns and other containers, 132; 4 (`0x10`) `portal` (298, 342); 5 (`0x20`) `Well`, 5; 6 (`0x40`) `Waypoint`, 16; 7 (`0x80`) beds and traps, 9. `[I]` bit 2 selects the collision mask `0x8000` (fn:UNIT_GetCollMask@0x006209D0, [drlg/0005 § 5](../findings/drlg/0005-collision.md#5-unit-marks)); `[I]` bit 6 marks the waypoint for the DRLG map scan and the waypoint lookup (fn:DRLG_PresetMapScan@0x00667970, fn:sub_0066B2B0_LevelPointFind@0x0066B2B0, [drlg/preset](../specs/drlg/preset.md)) | — | [C] |
| `Act` | int 0..16, bit set (1: 125, 16: 163, 4: 73, 2: 68, 15: 57, 8: 56) | `+0x170` u8 | acts the object may appear in, one bit per act (1 = Act I … 16 = Act V) | — | [C] |
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
| `Mode0..7` | int 0/1 (mode 0: 562, 1: 422, 2: 441, 3: 97, 7: 1) | `+0x13F..+0x146` u8 | the object has mode k | `objmode` row | [C] |
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

## Interpretation notes

- **Mode-indexed runs.** `[L]` Eleven column groups end in `0..7`: `Selectable`, `FrameCnt`, `FrameDelta`, `CycleAnim`,
  `Lit`, `BlocksLight`, `HasCollision`, `Start`, `OrderFlag`, `Mode`, plus `IsAttackable0` alone. The index is the object
  mode, i.e. the row of [ObjMode](ObjMode.md) (0 `NU` neutral, 1 `OP` operating, 2 `ON` opened, 3..7 `S1`..`S5`
  special). `[I]` for `HasCollision`, read at `+0x120 + mode` (drlg/0005 § 5).
- **Handler numbers are indices into code tables.** `[L]` `InitFn`, `PopulateFn`, `OperateFn` and `ClientFn` hold small
  integers with no other table behind them; plan 0023 Phase 1 reads which handler each runs.
- **Containers and traps.** `[C]` by data: of the 132 rows with `SubClass` bit 3, 106 have `TrapProb` 15, 1 has 20, 25
  have 0; 56 are `Lockable`. `TrapProb` is also set on 53 rows that are not containers (stashes, shrines, beds,
  `Dummy`). Whether `TrapProb` or `Lockable` take a draw is Phase 1's question.
- **Shrine rows.** `[C]` by data: all 92 rows with `SubClass` bit 0 have `PopulateFn` 2 and `InitFn` 1. `[L]` The [Shrines](Shrines.md) table gives the effect, picked at creation; how is Phase 1's question.

## Open questions

- `[L]` The meaning of the six zero byte ranges (`+0x040` 128 B, `+0x16C`, `+0x16F` and the three gaps before s32 fields), in
  particular whether `+0x040` is filled at load. Reverser: the loader `0x00640DDE` and its post-processing.
- `[L]` Which of `+0x16C` / `+0x16F`, if any, the code reads as `ShrineFunction`; why `Flicker` is not compiled.
- `[L]` The handler tables behind `InitFn`, `PopulateFn`, `OperateFn` (plan 0023 Phase 1) and `ClientFn`.
- `[L]` `SpawnMax`, `Xspace`/`Yspace`, `Act`, `TrapProb`, `Lockable`, `PreOperate`, `Parm0..7`: what the populate pass and
  the creation handlers read (plan 0023 Phase 1).

# Levels (`data/global/excel/levels.txt` → `levels.bin` + `leveldefs.bin`)

> **Source archive:** patch_d2 (`levels.txt`, `levels.bin`, `leveldefs.bin`)   **Rows:** 137 (138 data rows − 1 `Expansion` marker at row 109)
> **Record:** `levels.bin` 544 B, `leveldefs.bin` 156 B
> **sha256:** `.txt` `34add892965a7b38f08c7346ffe7a41ede6668b9d5b28277493ddf157e55da0b`, `levels.bin` `4af188176b8830afa78ee5f31558e6fd3b6c4a6c77fd9b4016490611a18e0cba`, `leveldefs.bin` `eeb6a9a485cdb217007c3aee1c20a7974466f2966f5b2a6ff210e5555e18e77c`
> **Doc status:** columns listed, both `.bin` layouts complete, semantics pending

## Purpose

One row per level (area): act, size per difficulty, DRLG generator type and level type, visibility
and warp links, monster levels and densities, the monster pools (`mon*`, `nmon*`, `umon*`, critters),
object groups, names and the entry file. Read by `drlg/*`, `monsters/*` and seeding
(`rng` finding 0002 cites `leveldefs +0x30`/`+0x34`).

## Row identity

- `[C]` `Id` equals the data row index after dropping the marker (0..136) in every row, and is
  compiled as `levels.bin +0x000` (u16). `Name` is not compiled.
- `[C]` `levels.bin` and `leveldefs.bin` both have one record per row in the same order. Each
  `Levels.txt` column is in exactly one of them (`excel_bin.py diff` refuses a column mapped in both).

## leveldefs `+0x30` / `+0x34`

- `[C]` **`leveldefs +0x30` is `DrlgType`** (u32; values 0..3 on 1/70/35/31 rows) and
  **`+0x34` is `LevelType`** (u32, 0..35). Both match all 137 records; no other offset fits either column.
  The meaning of the `DrlgType` values (generator 1/2/3) is the reverser's (finding `rng/0002`).
  `[C]` The game's own `leveldefs` field descriptor maps the same two columns; its full column→offset
  list is in [data/0001 § Data touched](../findings/data/0001-excel-loader.md#data-touched).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> levels` and `leveldefs` decodes every record and compares it with every mapped cell (blank cells and encoding rules as in [excel-bin.md](../formats/excel-bin.md#cell-encoding-rules)). A field is tagged `[C]` when the column's values pin its offset (a probe over every record finds no other offset that fits), `[I]` when the column is constant or identical to a sibling column, so its position comes from the neighbouring fields or the stride of its group. Widths are `[C]` with the same proviso; signedness is `[I]` (`s` where the column holds negative values). **Meaning:** no column semantics are claimed here; they come from reverser findings. The `.bin field` cell names the file.

| Column | Observed type / range | `.bin` field | References | Layout tag |
|---|---|---|---|---|
| `Name` | str, 137 distinct, len ≤ 27 | — (editor name; not in the record (rows are addressed by Id / row index)) | — | — |
| `Id` | int 0..136 (137 distinct) | `levels` `+0x000` u16 | — | [C] |
| `Pal` | int 0..4 (5 distinct) | `levels` `+0x002` u8 | — | [C] |
| `Act` | int 0..4 (5 distinct) | `levels` `+0x003` u8 | — | [C] |
| `QuestFlag` | int 11..39 (5 distinct), 113 blank | `leveldefs` `+0x000` u32 | — | [C] |
| `QuestFlagEx` | int 11..40 (5 distinct), 113 blank | `leveldefs` `+0x004` u32 | — | [C] |
| `Layer` | int 0..99 (100 distinct) | `leveldefs` `+0x008` u32 | — | [C] |
| `SizeX` | int -1..240 (25 distinct) | `leveldefs` `+0x00C` s32 | — | [I] |
| `SizeY` | int -1..200 (29 distinct) | `leveldefs` `+0x018` s32 | — | [I] |
| `SizeX(N)` | int -1..240 (25 distinct) | `leveldefs` `+0x010` s32 | — | [I] |
| `SizeY(N)` | int -1..200 (29 distinct) | `leveldefs` `+0x01C` s32 | — | [I] |
| `SizeX(H)` | int -1..240 (25 distinct) | `leveldefs` `+0x014` s32 | — | [I] |
| `SizeY(H)` | int -1..200 (29 distinct) | `leveldefs` `+0x020` s32 | — | [I] |
| `OffsetX` | int -4..5000 (13 distinct) | `leveldefs` `+0x024` s32 | — | [C] |
| `OffsetY` | int -40..3100 (45 distinct) | `leveldefs` `+0x028` s32 | — | [C] |
| `Depend` | int 0..32 (3 distinct) | `leveldefs` `+0x02C` u32 | — | [C] |
| `Teleport` | int 0..2 (3 distinct) | `levels` `+0x004` u8 | — | [C] |
| `Rain` | int 0..1 (2 distinct) | `levels` `+0x005` u8 | — | [C] |
| `Mud` | int 0..1 (2 distinct) | `levels` `+0x006` u8 | — | [C] |
| `NoPer` | int 0..1 (2 distinct) | `levels` `+0x007` u8 | — | [C] |
| `LOSDraw` | int 0..1 (2 distinct) | `leveldefs` `+0x098` u32 | — | [C] |
| `FloorFilter` | int 0..1 (2 distinct) | `levels` `+0x214` u32 | — | [C] |
| `BlankScreen` | int, always 1 | `levels` `+0x218` u32 | — | [I] |
| `DrawEdges` | int 0..1 (2 distinct) | `levels` `+0x009` u8 | — | [C] |
| `IsInside` | int 0..1 (2 distinct) | `levels` `+0x008` u8 | — | [C] |
| `DrlgType` | int 0..3 (4 distinct) | `leveldefs` `+0x030` u32 | — | [C] |
| `LevelType` | int 0..35 (36 distinct) | `leveldefs` `+0x034` u32 | — | [C] |
| `SubType` | int -1..11 (6 distinct) | `leveldefs` `+0x038` s32 | — | [C] |
| `SubTheme` | int -1..4 (6 distinct) | `leveldefs` `+0x03C` s32 | — | [C] |
| `SubWaypoint` | int -1..7 (4 distinct) | `leveldefs` `+0x040` s32 | — | [C] |
| `SubShrine` | int -1..8 (4 distinct) | `leveldefs` `+0x044` s32 | — | [C] |
| `Vis0` | int 0..131 (71 distinct) | `leveldefs` `+0x048` s32 | — | [C] |
| `Vis1` | int 0..132 (60 distinct) | `leveldefs` `+0x04C` s32 | — | [C] |
| `Vis2` | int 0..119 (25 distinct) | `leveldefs` `+0x050` s32 | — | [C] |
| `Vis3` | int 0..101 (21 distinct) | `leveldefs` `+0x054` s32 | — | [C] |
| `Vis4` | int 0..93 (18 distinct) | `leveldefs` `+0x058` s32 | — | [C] |
| `Vis5` | int 0..70 (7 distinct) | `leveldefs` `+0x05C` s32 | — | [C] |
| `Vis6` | int 0..71 (7 distinct) | `leveldefs` `+0x060` s32 | — | [C] |
| `Vis7` | int 0..72 (2 distinct) | `leveldefs` `+0x064` s32 | — | [C] |
| `Warp0` | int -1..81 (31 distinct) | `leveldefs` `+0x068` s32 | — | [C] |
| `Warp1` | int -1..82 (31 distinct) | `leveldefs` `+0x06C` s32 | — | [C] |
| `Warp2` | int -1..75 (15 distinct) | `leveldefs` `+0x070` s32 | — | [C] |
| `Warp3` | int -1..66 (10 distinct) | `leveldefs` `+0x074` s32 | — | [C] |
| `Warp4` | int -1..60 (9 distinct) | `leveldefs` `+0x078` s32 | — | [C] |
| `Warp5` | int -1..42 (4 distinct) | `leveldefs` `+0x07C` s32 | — | [C] |
| `Warp6` | int -1..43 (4 distinct) | `leveldefs` `+0x080` s32 | — | [C] |
| `Warp7` | int -1..44 (3 distinct) | `leveldefs` `+0x084` s32 | — | [C] |
| `Intensity` | int 0..140 (8 distinct) | `leveldefs` `+0x088` u8 | — | [C] |
| `Red` | int 0..255 (2 distinct) | `leveldefs` `+0x089` u8 | — | [I] |
| `Green` | int 0..255 (2 distinct) | `leveldefs` `+0x08A` u8 | — | [I] |
| `Blue` | int 0..255 (2 distinct) | `leveldefs` `+0x08B` u8 | — | [I] |
| `Portal` | int 0..1 (2 distinct) | `leveldefs` `+0x08C` u32 | — | [C] |
| `Position` | int 0..1 (2 distinct) | `leveldefs` `+0x090` u32 | — | [C] |
| `SaveMonsters` | int 0..1 (2 distinct) | `leveldefs` `+0x094` u32 | — | [C] |
| `Quest` | int 0..11 (3 distinct) | `levels` `+0x030` u8 | — | [C] |
| `WarpDist` | int 0..3900 (8 distinct) | `levels` `+0x00C` u32 | — | [C] |
| `MonLvl1` | int 0..50 (37 distinct) | `levels` `+0x010` u16 | — | [C] |
| `MonLvl2` | int 0..75 (38 distinct) | `levels` `+0x012` u16 | — | [C] |
| `MonLvl3` | int 0..93 (37 distinct) | `levels` `+0x014` u16 | — | [C] |
| `MonLvl1Ex` | int 1..50 (37 distinct), 8 blank | `levels` `+0x016` u16 | — | [C] |
| `MonLvl2Ex` | int 36..75 (33 distinct), 8 blank | `levels` `+0x018` u16 | — | [C] |
| `MonLvl3Ex` | int 67..87 (20 distinct), 8 blank | `levels` `+0x01A` u16 | — | [C] |
| `MonDen` | int 0..2200 (17 distinct) | `levels` `+0x01C` u32 | — | [C] |
| `MonDen(N)` | int 0..2200 (17 distinct) | `levels` `+0x020` u32 | — | [I] |
| `MonDen(H)` | int 0..2200 (17 distinct) | `levels` `+0x024` u32 | — | [I] |
| `MonUMin` | int 0..3 (4 distinct), 18 blank | `levels` `+0x028` u8 | — | [C] |
| `MonUMax` | int 0..3 (4 distinct), 18 blank | `levels` `+0x02B` u8 | — | [C] |
| `MonUMin(N)` | int 0..6 (7 distinct), 15 blank | `levels` `+0x029` u8 | — | [C] |
| `MonUMax(N)` | int 1..7 (7 distinct), 15 blank | `levels` `+0x02C` u8 | — | [C] |
| `MonUMin(H)` | int 0..10 (11 distinct), 15 blank | `levels` `+0x02A` u8 | — | [C] |
| `MonUMax(H)` | int 2..15 (11 distinct), 15 blank | `levels` `+0x02D` u8 | — | [C] |
| `MonWndr` | int 0..1 (2 distinct) | `levels` `+0x02E` u8 | — | [C] |
| `MonSpcWalk` | int 0..5 (3 distinct) | `levels` `+0x02F` u8 | — | [C] |
| `NumMon` | int 0..3 (3 distinct), 10 blank | `levels` `+0x032` u8 | — | [C] |
| `mon1` | str, 73 distinct, len ≤ 16, 11 blank | `levels` `+0x036` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon2` | str, 78 distinct, len ≤ 16, 11 blank | `levels` `+0x038` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon3` | str, 66 distinct, len ≤ 16, 26 blank | `levels` `+0x03A` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon4` | str, 42 distinct, len ≤ 13, 52 blank | `levels` `+0x03C` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon5` | str, 30 distinct, len ≤ 13, 86 blank | `levels` `+0x03E` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon6` | str, 10 distinct, len ≤ 11, 114 blank | `levels` `+0x040` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon7` | str, 4 distinct, len ≤ 12, 122 blank | `levels` `+0x042` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon8` | str, always 'bonefetish3', 134 blank | `levels` `+0x044` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon9` | always blank | `levels` `+0x046` u16 index (distinct-key ordinal) | `monstats:Id` | [I] |
| `mon10` | always blank | `levels` `+0x048` u16 index (distinct-key ordinal) | `monstats:Id` | [I] |
| `rangedspawn` | int, always 1, 117 blank | `levels` `+0x031` u8 | — | [C] |
| `nmon1` | str, 69 distinct, len ≤ 16, 11 blank | `levels` `+0x068` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon2` | str, 75 distinct, len ≤ 14, 11 blank | `levels` `+0x06A` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon3` | str, 74 distinct, len ≤ 16, 16 blank | `levels` `+0x06C` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon4` | str, 60 distinct, len ≤ 16, 33 blank | `levels` `+0x06E` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon5` | str, 48 distinct, len ≤ 14, 67 blank | `levels` `+0x070` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon6` | str, 29 distinct, len ≤ 14, 95 blank | `levels` `+0x072` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon7` | str, 19 distinct, len ≤ 12, 103 blank | `levels` `+0x074` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon8` | str, 20 distinct, len ≤ 13, 114 blank | `levels` `+0x076` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon9` | str, 18 distinct, len ≤ 16, 117 blank | `levels` `+0x078` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon10` | str, 19 distinct, len ≤ 14, 117 blank | `levels` `+0x07A` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon1` | str, 71 distinct, len ≤ 16, 12 blank | `levels` `+0x09A` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon2` | str, 71 distinct, len ≤ 14, 15 blank | `levels` `+0x09C` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon3` | str, 63 distinct, len ≤ 14, 30 blank | `levels` `+0x09E` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon4` | str, 41 distinct, len ≤ 13, 53 blank | `levels` `+0x0A0` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon5` | str, 29 distinct, len ≤ 13, 87 blank | `levels` `+0x0A2` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon6` | str, 10 distinct, len ≤ 11, 115 blank | `levels` `+0x0A4` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon7` | str, 4 distinct, len ≤ 12, 123 blank | `levels` `+0x0A6` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon8` | str, always 'bonefetish3', 134 blank | `levels` `+0x0A8` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon9` | always blank | `levels` `+0x0AA` u16 index (distinct-key ordinal) | `monstats:Id` | [I] |
| `umon10` | always blank | `levels` `+0x0AC` u16 index (distinct-key ordinal) | `monstats:Id` | [I] |
| `cmon1` | str, 8 distinct, len ≤ 10, 43 blank | `levels` `+0x0CC` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `cmon2` | str, 3 distinct, len ≤ 6, 73 blank | `levels` `+0x0CE` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `cmon3` | str, always 'scorpion', 110 blank | `levels` `+0x0D0` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `cmon4` | str, always 'larva', 136 blank | `levels` `+0x0D2` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `cpct1` | int 2..100 (5 distinct), 43 blank | `levels` `+0x0D4` u16 | — | [C] |
| `cpct2` | int 30..100 (2 distinct), 73 blank | `levels` `+0x0D6` u16 | — | [C] |
| `cpct3` | int, always 20, 110 blank | `levels` `+0x0D8` u16 | — | [C] |
| `cpct4` | int, always 100, 136 blank | `levels` `+0x0DA` u16 | — | [C] |
| `camt1` | always blank | `levels` `+0x0DC` u16 | — | [I] |
| `camt2` | always blank | `levels` `+0x0DE` u16 | — | [I] |
| `camt3` | always blank | `levels` `+0x0E0` u16 | — | [I] |
| `camt4` | always blank | `levels` `+0x0E2` u16 | — | [I] |
| `Themes` | int 0..60 (4 distinct) | `levels` `+0x210` u32 | — | [C] |
| `SoundEnv` | int 0..49 (48 distinct) | `levels` `+0x21C` u32 | — | [C] |
| `Waypoint` | int 0..255 (40 distinct) | `levels` `+0x0E4` u8 | — | [C] |
| `LevelName` | str, 127 distinct, len ≤ 27, 1 blank | `levels` `+0x0F5` char[40] | — | [C] |
| `LevelWarp` | str, 127 distinct, len ≤ 33, 1 blank | `levels` `+0x11D` char[40] | — | [C] |
| `EntryFile` | str, 129 distinct, len ≤ 5, 1 blank | `levels` `+0x145` char[40] | — | [C] |
| `ObjGrp0` | int 0..126 (30 distinct) | `levels` `+0x0E5` u8 | — | [C] |
| `ObjGrp1` | int 0..127 (27 distinct) | `levels` `+0x0E6` u8 | — | [C] |
| `ObjGrp2` | int 0..121 (20 distinct) | `levels` `+0x0E7` u8 | — | [C] |
| `ObjGrp3` | int 0..124 (18 distinct) | `levels` `+0x0E8` u8 | — | [C] |
| `ObjGrp4` | int 0..129 (10 distinct) | `levels` `+0x0E9` u8 | — | [C] |
| `ObjGrp5` | int 0..129 (7 distinct) | `levels` `+0x0EA` u8 | — | [C] |
| `ObjGrp6` | int 0..128 (3 distinct) | `levels` `+0x0EB` u8 | — | [C] |
| `ObjGrp7` | int 0..106 (2 distinct) | `levels` `+0x0EC` u8 | — | [C] |
| `ObjPrb0` | int 0..90 (24 distinct) | `levels` `+0x0ED` u8 | — | [C] |
| `ObjPrb1` | int 0..80 (23 distinct) | `levels` `+0x0EE` u8 | — | [C] |
| `ObjPrb2` | int 0..70 (22 distinct) | `levels` `+0x0EF` u8 | — | [C] |
| `ObjPrb3` | int 0..75 (17 distinct) | `levels` `+0x0F0` u8 | — | [C] |
| `ObjPrb4` | int 0..50 (9 distinct) | `levels` `+0x0F1` u8 | — | [C] |
| `ObjPrb5` | int 0..35 (4 distinct) | `levels` `+0x0F2` u8 | — | [C] |
| `ObjPrb6` | int 0..30 (3 distinct) | `levels` `+0x0F3` u8 | — | [C] |
| `ObjPrb7` | int 0..25 (2 distinct) | `levels` `+0x0F4` u8 | — | [C] |
| `Beta` | int 0..1 (2 distinct) | — (no field in levels.bin or leveldefs.bin matches it) | — | — |

Columns that equal their sibling in every row are ordered by header order `[I]`: `SizeX`/`SizeY` (all
three difficulties equal), `MonDen(N)`/`MonDen(H)`, and `Red`/`Green`/`Blue` (each row has all three 0
or all 255).
`mon9/10`, `umon9/10`, `camt1..4` are blank everywhere and placed by stride `[I]`.

### Fields with no `.txt` column

| file | offset | type | observed | tag |
|---|---|---|---|---|
| levels | `+0x00A` | u16 | 0 in every record | unknown |
| levels | `+0x033`, `+0x034` | u8, u16 | 0 | unknown |
| levels | `+0x04A`..`+0x067`, `+0x07C`..`+0x099`, `+0x0AE`..`+0x0CB` | u16 × 15 each | `0xFFFF` in every record | `[I]` slots 11..25 of the `mon`, `nmon`, `umon` arrays (25 × u16 each; only 10 have columns) |
| levels | `+0x16D`..`+0x20F` | 163 B | 0 | unknown |

## Record layouts

`levels.bin` (544 B): `+0x000` `Id` u16, `Pal`, `Act`, `Teleport`, `Rain`, `Mud`, `NoPer`, `IsInside`,
`DrawEdges` (u8) · `+0x00C` `WarpDist` u32 · `+0x010` `MonLvl1..3`, `MonLvl1Ex..3Ex` u16 · `+0x01C`
`MonDen` ×3 u32 · `+0x028` `MonUMin` ×3, `MonUMax` ×3, `MonWndr`, `MonSpcWalk`, `Quest`,
`rangedspawn`, `NumMon` (u8) · `+0x036` `mon[25]`, `+0x068` `nmon[25]`, `+0x09A` `umon[25]` (u16
monster ordinals) · `+0x0CC` `cmon1..4`, `cpct1..4`, `camt1..4` (u16) · `+0x0E4` `Waypoint`,
`ObjGrp0..7`, `ObjPrb0..7` (u8) · `+0x0F5` `LevelName`, `+0x11D` `LevelWarp`, `+0x145` `EntryFile`
(`char[40]`) · `+0x210` `Themes`, `FloorFilter`, `BlankScreen`, `SoundEnv` (u32).

### leveldefs.bin (156 B)

`+0x000` `QuestFlag`, `QuestFlagEx`, `Layer` · `+0x00C` `SizeX`, `SizeX(N)`, `SizeX(H)`, `SizeY` ×3 ·
`+0x024` `OffsetX`, `OffsetY`, `Depend` · `+0x030` `DrlgType` · `+0x034` `LevelType` · `+0x038`
`SubType`, `SubTheme`, `SubWaypoint`, `SubShrine` · `+0x048` `Vis0..7` · `+0x068` `Warp0..7` (all u32 /
s32) · `+0x088` `Intensity`, `Red`, `Green`, `Blue` (u8) · `+0x08C` `Portal`, `Position`,
`SaveMonsters`, `LOSDraw` (u32). No unknown bytes.

## Open questions

- Answered `[I]`: monster references (`mon*`/`nmon*`/`umon*`) are used as record positions, so after
  the duplicate `cr_lancer8` they point one record early
  ([data/0001 §8](../findings/data/0001-excel-loader.md#8-answers-to-the-archivists-phase-1-questions), [MonStats.md](MonStats.md#open-questions)).
- `[L]` `levels.bin +0x16D..+0x20F` (163 zero bytes): runtime-filled (localised names?) or padding
  (backlog → reverser).
- `[L]` `BlankScreen` is 1 in every row; `+0x218` is placed by elimination `[I]`.

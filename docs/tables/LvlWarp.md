# LvlWarp (`data/global/excel/LvlWarp.txt` → `lvlwarp.bin`)

> **Source archive:** d2exp (`LvlWarp.txt`, `lvlwarp.bin`)   **Rows:** 88 (89 data rows − 1 `Expansion` marker, the 72nd data row)
> **Record:** `lvlwarp.bin` 48 B (0x30)
> **sha256:** `.txt` `ee95bd2015140049ab497f44b6de5e7e4b43a8434524baf817776e735dbf4021`, `.bin` `89f88d0695a521c485a78195a2a93bd8cc195b8d11bcf05b76376c1a5076e7db`
> **Doc status:** columns listed, `.bin` layout complete, semantics from drlg/0002 and [drlg/0007](../findings/drlg/0007-warps.md) (all compiled columns)

## Purpose

One record per warp kind: the tile a level-to-level warp (cave mouth, stairs, Act 5 doorways) is
drawn with, its selection box, exit walk and offset. A level names the warps it can hold in
`Levels.txt` `Warp0..7` ([Levels § leveldefs `+0x68`](Levels.md#leveldefs-0x68-the-warp-ids)). Read by the
room build (`drlg/overview`, [research map](../specs/README.md)), which owns every column's meaning.
Written from the reverser's backlog request of 2026-10-11 (plan 0008). Leads: none; derived from data.
Column names are the `.txt` header row.

## Row identity

- `[C]` `Id` runs 0..82 (83 distinct over 88 records). It equals the record index for records 0..71;
  after that five `Id`s (71, 73, 74, 81, 82, all Act 5) have two records each, one with `Direction`
  `'l'` and one with `'r'`, in that order. Every other `Id` has one record, with `Direction` `'b'`.
- `[C]` `Levels.txt` `Warp0..7` hold −1 or an `Id`: all 236 non-−1 cells resolve, and every one of the
  83 `Id`s is named by at least one level ([Levels](Levels.md#leveldefs-0x68-the-warp-ids)).
- `[I]` Code finds a record by `Id` and `Direction`, not by index: `LVLWARP_FindByIdDir` (`0x0061F310`)
  returns the first record with that `Id` whose `Direction` is `'b'` or the one asked for, and is fatal
  if there is none. Records live at `g_pLvlWarp` (`0x0096CA00`, count at `0x0096CA04`)
  ([drlg/0002](../findings/drlg/0002-room-build-draws.md)).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel lvlwarp`
decodes all 88 records and matches every mapped cell (88 × 12 = 1056 cells, 0 mismatches), and
`excel_bin.py probe … lvlwarp` finds exactly one offset for each column. `excel_bin.py unknown … lvlwarp`
leaves only `+0x02D..+0x02F`, 0 in every record. `[L]` The integer type the game reads inside a
4-byte slot is not pinned by the data: `s32` in the `.bin field` column is the decode `excel_bin.py`
uses where a column holds negative values, not a claim about that type.

**Meaning tags** are `[I]` where drlg/0002 or [drlg/0007](../findings/drlg/0007-warps.md) reads the field in code
(`0x0061F310`, `0x0066E160`, `0x0066E260`; `0x0066E1C0`, `0x005550B0`, `0x0045B1E0`).

| Column | Observed type / range | `.bin` field | Meaning | References | Layout tag | Meaning tag |
|---|---|---|---|---|---|---|
| `Name` | str, 83 distinct, len ≤ 32 | — (editor name; not in the record) | — | — | — | — |
| `Id` | int 0..82 (83 distinct) | `+0x000` s32 | warp kind; the key `Levels.txt` `Warp0..7` name | `Levels.txt` `Warp0..7` | [C] | [I] |
| `SelectX` | int −130..20 (21 distinct) | `+0x004` s32 | the warp's selection box in screen pixels; read only by the client, which draws it (`0x0045B1E0`) | — | [C] | [I] |
| `SelectY` | int −210..−10 (22 distinct) | `+0x008` s32 | the warp's selection box in screen pixels; read only by the client, which draws it (`0x0045B1E0`) | — | [C] | [I] |
| `SelectDX` | int 0..210 (19 distinct) | `+0x00C` s32 | the warp's selection box in screen pixels; read only by the client, which draws it (`0x0045B1E0`) | — | [C] | [I] |
| `SelectDY` | int 0..240 (19 distinct) | `+0x010` s32 | the warp's selection box in screen pixels; read only by the client, which draws it (`0x0045B1E0`) | — | [C] | [I] |
| `ExitWalkX` | int −5..5 (6 distinct) | `+0x014` s32 | server exit: a unit that comes out of the paired warp is put at that warp unit's position plus this offset, in subtiles (`0x005550B0`) | — | [C] | [I] |
| `ExitWalkY` | int −5..5 (5 distinct) | `+0x018` s32 | server exit: a unit that comes out of the paired warp is put at that warp unit's position plus this offset, in subtiles (`0x005550B0`) | — | [C] | [I] |
| `OffsetX` | int −4..10 (13 distinct) | `+0x01C` s32 | offset of the warp unit (a type-5 preset unit whose class is `Id`) from its cell, in subtiles (`WarpUnitAdd`, `0x0066E1C0`) | — | [C] | [I] |
| `OffsetY` | int −6..6 (12 distinct) | `+0x020` s32 | offset of the warp unit (a type-5 preset unit whose class is `Id`) from its cell, in subtiles (`WarpUnitAdd`, `0x0066E1C0`) | — | [C] | [I] |
| `LitVersion` | int 0..1 (1 in 57 rows) | `+0x024` u32 | ≠ 0: a visible warp cell gets one extra tile pick | — | [C] | [I] |
| `Tiles` | int 2..4 (4 in 3 rows) | `+0x028` u32 | the extra pick's tile is `cell \| Tiles << 8` (the cell's sub-index bits) | — | [C] | [I] |
| `Direction` | char `b` (78), `l` (5), `r` (5) | `+0x02C` char, then 3 zero bytes | which side the record fits: `'b'` both, `'l'` orientation 10, `'r'` orientation 11 | — | [C] | [I] |
| `Beta` | int 0..1 (1 in 19 rows) | — (no field in `lvlwarp.bin` matches it) | — | — | — | — |

## Record layout

`+0x000` `Id` · `+0x004` `SelectX`, `SelectY`, `SelectDX`, `SelectDY` · `+0x014` `ExitWalkX`,
`ExitWalkY` · `+0x01C` `OffsetX`, `OffsetY` · `+0x024` `LitVersion` · `+0x028` `Tiles` (all 4-byte
slots) · `+0x02C` `Direction` (1 byte) · `+0x02D..+0x02F` 0 in the file. Every byte is covered, and the
record follows `.txt` column order. `[C]`

- `[C]` These offsets are the ones drlg/0002 § Data touched lists from the code's reads (`+0x00` Id,
  `+0x1C`/`+0x20` OffsetX/Y, `+0x24` LitVersion, `+0x28` Tiles, `+0x2C` Direction), now pinned by data.

## Interpretation notes

- `[I]` Use in the room build ([drlg/0002](../findings/drlg/0002-room-build-draws.md), warp-node bullet
  and `WarpTileAdd`): a wall cell of orientation 10 or 11 takes the level's warp id `Warp`*m*, m = cell
  bits 20–25 (`0x0066AF30`); the room's warp node with that `Id` is refitted to `Direction` `'l'` (o 10)
  or `'r'` (o 11) through `LVLWARP_FindByIdDir` when its own record is neither `'b'` nor that side
  (`0x0066E160`); and if `LitVersion` ≠ 0, one tile pick of `cell | Tiles << 8` follows
  (`0x0066E260`). Level 133 skips this.
- `[C]` Only the Act 5 pairs (`Id` 71, 73, 74, 81, 82) use `'l'`/`'r'`; every other record is `'b'`.
- `[I]` The positions ([drlg/0007](../findings/drlg/0007-warps.md) § Answer, LvlWarp columns): the warp unit
  sits at its cell plus `OffsetX/OffsetY`; a unit leaving through the paired warp lands at that unit plus
  `ExitWalkX/ExitWalkY` on the server; the client alone reads `Select*`. (fn:sub_0066E1C0_WarpUnitAdd@0x0066E1C0,
  fn:sub_005550B0_WarpExitPos@0x005550B0, fn:sub_0045B1E0_WarpSelectBoxDraw@0x0045B1E0)
- `[I]` **Units** ([drlg/0007 § P1a](../findings/drlg/0007-warps.md#plan-0039-batch-p1a-2026-10-16)):
  - `OffsetX/OffsetY` are subtiles relative to the room: `WarpUnitAdd` converts the cell's room-relative tile to
    subtiles (× 5) and adds `+0x1C`/`+0x20` before creating the type-5 preset unit (fn:sub_0066E1C0_WarpUnitAdd@0x0066E1C0,
    tbl:LvlWarp.txt:OffsetX).
  - `ExitWalkX/ExitWalkY` are subtiles: `WarpExitPos` adds `+0x14`/`+0x18` to the paired warp unit's subtile position
    (fn:sub_005550B0_WarpExitPos@0x005550B0, tbl:LvlWarp.txt:ExitWalkX).
  - `SelectX/SelectY/SelectDX/SelectDY` are screen pixels: the client converts the unit's subtile position with
    `SubtileToScreen` (`X = (x − y)·16`, `Y = (x + y)·8`), subtracts the view origin, adds `SelectX`/`SelectY` for the
    box corner and uses `SelectDX`/`SelectDY` as its width and height (fn:sub_0045B1E0_WarpSelectBoxDraw@0x0045B1E0,
    fn:sub_00643260_SubtileToScreen@0x00643260, tbl:LvlWarp.txt:SelectX).
- `[I]` Which warp a cell gets: the cell's slot *m* names `Warp`*m* (this table's `Id`) and `Vis`*m* (the
  destination) of its level ([Levels § Code semantics of the links](Levels.md#code-semantics-of-the-links-plan-0022-phase-1)).
  The slot each stock DS1 carries is surveyed in [LvlPrest § Warp slots](LvlPrest.md#warp-slots-plan-0022-phase-2).

## Open questions

- Answered `[I]` by drlg/0007 § P1a: `Offset*` and `ExitWalk*` are subtiles, `Select*` screen pixels (§ Interpretation
  notes, *Units*).
- `[L]` Whether `+0x02D..+0x02F` is anything but padding after the `Direction` char.

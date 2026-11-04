# Expanding-field table (`expfield.d2`)

Owned by `archivist`. One file of **65 536 direction bytes** in a 256 x 256 grid, with a 10-byte header. The server's
ground-drop cell search follows it from a cell toward the centre, one step per byte, and tests each cell it visits
([items/0014 § 1](../findings/items/0014-ground-items.md#1-the-search)). What the walk is for, its masks and the
search around it are that finding's; this page is the file's layout and the checks the parser makes.

Parser: `tools/expfield.py` (`check`, `walk`), tests `tools/test_expfield.py`. **Sources: no lead; derived from data and
the findings.** No external document was read for this format and nothing is registered in [sources.md](../sources.md)
(ADR-0007). The field names are ours.

## File

- `[C]` (data) **One copy in the archives** ([mpq](mpq.md)): `data\global\ExpField.D2` in `d2data.mpq`, 65 546 bytes,
  sha256 `0ff552c32f02b9d2eacd6a66e2622786b8885cb0fb9a47eda032d83c0346aba3`. The merged tree's `data/global/expfield.d2`
  is that copy (`merged-manifest.tsv`, archive `d2data`); no other archive of the 12 holds a file of the name.
  [inventory.md](../inventory.md) does not list archive members (its *MPQ contents* section), so the line the request
  asked for is the merged manifest's.
- `[C]` (data) The pinned `Game.exe` holds the string `%s\expfield.d2` at `0x006EED4C` (the one occurrence of `expfield` in the image, case-insensitive), and the loader that builds the
  path from it is `sub_0066A2B0_FieldLoad` (`0x0066A2B0`), with the matching free `sub_0066A420_FieldFree`
  (items/0014 § Functions, `I` in `re/symbols.csv`). Whether another function opens the file was not followed.
  (fn:sub_0066A2B0_FieldLoad@0x0066A2B0, fn:sub_0066A420_FieldFree@0x0066A420)

## Layout

All little-endian.

| Offset | Size | Type | Name | Meaning | Tag |
|---:|---:|---|---|---|---|
| `0x00` | 2 | u16 | `unk` | skipped by the loader as the findings read it; **266** (`0x010A`) in the shipped file | `[I]` the skip (items/0014 § 1); `[C]` (data) the value |
| `0x02` | 4 | u32 | `rows` | 256 | `[I]` as the loader's field, `[C]` (data) the value |
| `0x06` | 4 | u32 | `columns` | 256 | `[I]` as the loader's field, `[C]` (data) the value |
| `0x0A` | `rows` x `columns` | u8[] | `cells` | one direction byte per cell, row-major: cell `(x, y)` is at `0x0A + y * columns + x` | `[C]` (ADR-0015) the 256-wide row-major index (items/0014 § 1, family `line`) |

- `[C]` (data, `expfield.py check`) The file is exactly 10 + 256 x 256 bytes, so `rows x columns` fills it to the byte.
  Both counts are 256, so which of the two words is the row count cannot be told from this file (`[I]`: the order is the
  request's reading of the loader).
- `[C]` (data) **Byte values.** 0 to 7 and one 8; none above 8. Counts per value (`0`..`7`, `8`): 8 128, 8 192, 8 256,
  8 256, 8 256, 8 191, 8 128, 8 128, 1. The single 8 is at cell `(128, 128)`, the centre.
- `[C]` (ADR-0015) **Use.** Byte `d` in 0..7 steps by `(dx[d], dy[d])`; 8 is the centre, where a walk stops. The search's
  field cell for a candidate `(x, y)` about an origin `(ox, oy)` is row `128 + y - oy`, column `128 + x - ox`; the origin cell
  is tested only when the walk starts on it. This is items/0014 § 1's statement, whose family `line` is `[C]`; the
  search around it is `[I]` pending ADR-0029. (fn:sub_0066A5D0_FieldStep@0x0066A5D0, fn:sub_0066A670_FieldWalkBlocked@0x0066A670, run:2026-11-04-ground-emu)
- `[C]` (data) **Step tables**, image data read from the pinned `Game.exe` by `expfield.py check`:

  | `d` | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
  | `dx` at `0x00749780` | 0 | 1 | 1 | 1 | 0 | -1 | -1 | -1 | 0 |
  | `dy` at `0x007497A4` | -1 | -1 | 0 | 1 | 1 | 1 | 0 | -1 | 0 |

  Nine s32 each. Directions 0 to 7 are the eight neighbours, clockwise from north (`y` grows downward).
  (data:0x00749780, data:0x007497A4)

## Checks (`python3 -I tools/expfield.py check <file> <game.exe>`)

Output kept in `workspace/logs/a69/expfield-check.txt` (manifest `manifest.sha256` beside it).

- `[C]` (data) **Every cell walks to the centre.** Following the bytes from each of the 65 536 cells reaches the byte 8
  at `(128, 128)`: 0 walks leave the table, loop or meet a byte above 8. The longest is 128 steps (total 5 592 448), and
  every walk's length equals the Chebyshev distance `max(|x - 128|, |y - 128|)` of its start (0 exceptions), so no walk
  detours. This is the whole-table walk check `tools/item_emu3.py static` makes (items/0014 § 1, same numbers).
- `[C]` (data) The step tables read from the image equal the constants in `tools/expfield.py`.
- Tests: `python3 -I tools/test_expfield.py` (6 cases: parse, size mismatch, a walk to the centre, a walk that leaves the table or loops or meets a byte above 8, the step tables' shape, a synthetic check).

## Open questions

- `[L]` What the two bytes at `0x00` are for. The loader reads past them (items/0014 § Data touched: "a u16 of 266 by
  this copy"); no reader of the value was named.
- `[L]` Which function opens the file besides `0x0066A2B0` and whether the client reads it: not followed.

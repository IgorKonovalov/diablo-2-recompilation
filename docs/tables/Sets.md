# Sets (`data/global/excel/sets.txt` → `sets.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 32 (33 data rows − 1 `Expansion` marker)   **Record:** 296 B (`0x128`)
> **sha256:** `.txt` `e6694bc603f1f29efdfa981c3f747708e11bb0410786fa8bf5ab634f60f6b822`, `.bin` `abec75e33edd8ffaf1e28c04a4e79adc8e47198f5bf9a552fa057ba4cb220aa4`
> **Doc status:** identity and generation columns; `.bin` layout of the head (`+0x000..+0x00F`) and tail (`+0x110..+0x127`) complete, the bonus property block (`+0x010..+0x10F`) not mapped; semantics `[L]`

## Purpose

One row per item set: its name, its game version, its level, and the partial and full set bonuses.
The set items themselves are rows of [SetItems](SetItems.md), which name their set through `set`.
This doc covers the identity and generation columns (plan 0019 Phase 0, research-map row
`items/uniques-sets`). The bonus columns (`PCode2a..PMax5b`, `FCode1..FMax8`) are `items/properties`
and are only located here. Leads: no lead; derived from data.

## Row identity

- `[C]` The record index is the data row index once the `Expansion` marker is dropped (0..31): rows
  0..15 come before the marker, rows 16..31 after it. `python3 -I tools/excel_bin.py diff … sets`
  matches record *i* to data row *i* in every mapped column.
- `[C]` `index` is the row's key, unique in all 32 rows, and is stored as the row's own index (u16 at
  `+0x000`, 0..31). `name` equals `index` as text in all 32 rows and is stored as a string-table key.
- `[C]` `SetItems.set` names a row here by `index`: all 127 resolve, every one of the 32 sets is named,
  and `setitems.bin` stores the row index of this table ([SetItems](SetItems.md) layout, `+0x02C`).
  Members per set: 1 set with 2 items, 9 with 3, 14 with 4, 6 with 5, 2 with 6 (`127` in all).
- `[I]` The game loads `sets.bin` with a 296-byte record ([data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel sets`
decodes all 32 records and matches every mapped cell (32 × 3 = 96 cells, 0 mismatches), and
`excel_bin.py probe` finds `version` at `+0x004` only. The layout is **partial** on purpose: the 64
bonus columns are reported by `diff` as outside the layout and are not checked.
`[L]` The integer type the game reads inside a slot is not pinned (no code anchor).
**Meaning:** `[L]` throughout.

| Column | Observed type / range | `.bin` field | Meaning (`[L]`) | References | Layout tag |
|---|---|---|---|---|---|
| `index` | str, 32 distinct, len ≤ 22 | `+0x000` u16, the row's own index | set key | `setitems` `set` (all 127 resolve) | [C] |
| `name` | str, equal to `index` in all 32 rows | `+0x002` u16 string-table key | display name | `.tbl` key ([tbl.md](../formats/tbl.md)) | [C] |
| `version` | int {0: 16, 100: 16}, 0 blank | `+0x004` 4-byte slot (u32 decode) | 0 classic, 100 expansion | — | [C] |
| `level` | int 3..55 (29 distinct), 0 blank | — **no field**: `probe` finds it at no offset under any encoding | set level | equals the `lvl` of every member in `setitems` (127 of 127) | [C] (absence) |
| `PCode2a..PMax5b` | partial-set bonuses, 8 quads (code, param, min, max) | `+0x010..+0x08F`, 8 × 16 B (not mapped) | `items/properties` | `properties` `code` | — |
| `FCode1..FMax8` | full-set bonuses, 8 quads | `+0x090..+0x10F`, 8 × 16 B (not mapped) | `items/properties` | `properties` `code` | — |
| `*eol` | end-of-line marker column | — (not compiled) | — | — | — |

`[C]` `version` follows the marker: 0 in rows 0..15 and 100 in rows 16..31.

## Record layout

`+0x000` `index` (u16 row index) · `+0x002` `name` (u16 string key) · `+0x004` `version` (u32) ·
`+0x008`, `+0x00C` two u32, 0 in every record (`unk_008`, `unk_00C`; no `.txt` column) ·
`+0x010..+0x10F` sixteen 16-byte bonus quads in `.txt` order (`PCode2a` at `+0x010`, `FCode1` at
`+0x090`; position from `probe`, not diffed) · `+0x110..+0x127` six u32, 0 in every record
(`unk_110..unk_124`). `python3 -I tools/excel_bin.py unknown … sets` lists only the bonus block as
uncovered. `[C]` for the offsets of the mapped fields and for the zero ranges. `[L]` Whether the zero
ranges are slots the loader fills at run time (a member count, member pointers) is not known: no code
anchor.

## Interpretation notes

- `[C]` `level` is not compiled, but every set item carries the same value in its own `lvl`
  (`python3 -I tools/unique_survey.py … ` prints `SetItems lvl against its Sets level: 0 below, 127
  equal, 0 above`). A reader of the `.bin` that needs a set's level gets it from a member row.
- `[C]` The set items of the 16 classic sets are `setitems` rows 0..61 and those of the 16 expansion
  sets rows 62..126; the version changes once along `setitems` record order. `setitems.txt` has no
  `version` column, so the set's `version` is the only version a set item has in the data. Whether the
  set builder tests it, and where, is plan 0019 Phase 1 `[L]`.
- The bonus columns go to `items/properties`. Their `.bin` positions above come from `probe`
  (`PCode2a` `+0x010`, `PParam2a` `+0x014`, `PMin2a` `+0x018`, `PMax2a` `+0x01C`, …); several param
  columns hold skill names or parse to no single encoding, which is why the block is left unmapped.

## Open questions

- `[L]` What the game stores at `+0x008`, `+0x00C` and `+0x110..+0x127` once loaded (0 in the file).
  Backlog entry 2026-10-14 (archivist → reverser).
- `[L]` Whether `version` (here) and `lvl` (in `setitems`) gate the set builder: plan 0019 Phase 1.

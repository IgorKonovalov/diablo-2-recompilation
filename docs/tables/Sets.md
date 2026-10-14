# Sets (`data/global/excel/sets.txt` → `sets.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 32 (33 data rows − 1 `Expansion` marker)   **Record:** 296 B (`0x128`)
> **sha256:** `.txt` `e6694bc603f1f29efdfa981c3f747708e11bb0410786fa8bf5ab634f60f6b822`, `.bin` `abec75e33edd8ffaf1e28c04a4e79adc8e47198f5bf9a552fa057ba4cb220aa4`
> **Doc status:** identity and generation columns; `.bin` layout of the head (`+0x000..+0x00F`) and tail (`+0x110..+0x127`) complete, the bonus property block (`+0x010..+0x10F`) not mapped; semantics of `version` and the load-time slots from [items/0004](../findings/items/0004-uniques-sets.md) (plan 0019 Phase 1), `[L]` elsewhere

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
**Meaning:** `[L]` unless tagged in the cell; `version` and `level` are `[I]` from
[items/0004 § 7](../findings/items/0004-uniques-sets.md#7-load-time-slots-in-uniqueitems-setitems-and-sets-the-backlog-questions).

| Column | Observed type / range | `.bin` field | Meaning (`[L]`) | References | Layout tag |
|---|---|---|---|---|---|
| `index` | str, 32 distinct, len ≤ 22 | `+0x000` u16, the row's own index | set key | `setitems` `set` (all 127 resolve) | [C] |
| `name` | str, equal to `index` in all 32 rows | `+0x002` u16 string-table key | display name | `.tbl` key ([tbl.md](../formats/tbl.md)) | [C] |
| `version` | int {0: 16, 100: 16}, 0 blank | `+0x004` 4-byte slot (u32 decode) | 0 classic, 100 expansion; `[I]` copied at load into each member's `setitems` `+0x022`, where the set builder tests it (≥ 100 only in an expansion game) | `setitems` `+0x022` | [C] |
| `level` | int 3..55 (29 distinct), 0 blank | — **no field**: `probe` finds it at no offset under any encoding | `[I]` not compiled and not read: the loader has no `level` descriptor, and the only set level test reads `SetItems.lvl` | equals the `lvl` of every member in `setitems` (127 of 127) | [C] (absence) |
| `PCode2a..PMax5b` | partial-set bonuses, 8 quads (code, param, min, max) | `+0x010..+0x08F`, 8 × 16 B (not mapped) | `items/properties` | `properties` `code` | — |
| `FCode1..FMax8` | full-set bonuses, 8 quads | `+0x090..+0x10F`, 8 × 16 B (not mapped) | `items/properties` | `properties` `code` | — |
| `*eol` | end-of-line marker column | — (not compiled) | — | — | — |

`[C]` `version` follows the marker: 0 in rows 0..15 and 100 in rows 16..31.

## Record layout

`+0x000` `index` (u16 row index) · `+0x002` `name` (u16 string key) · `+0x004` `version` (u32) ·
`+0x008` u32, 0 in every record (`unk_008`; no `.txt` column) · `+0x00C` u32, 0 in every record
(`nMembers`, filled at load) · `+0x010..+0x10F` sixteen 16-byte bonus quads in `.txt` order (`PCode2a`
at `+0x010`, `FCode1` at `+0x090`; position from `probe`, not diffed) · `+0x110..+0x127` six u32, 0 in
every record (`member0..member5`, filled at load). `python3 -I tools/excel_bin.py unknown … sets` lists
only the bonus block as uncovered. `[C]` for the offsets of the mapped fields and for the zero ranges.

- `[C]` `+0x00C` is the member count and `+0x110..+0x127` six pointers to the member `setitems` records,
  both filled by the loader once `setitems` is loaded: for each `setitems` row in order whose `set` is
  valid and whose set has fewer than 6 members, the row's pointer goes to `members[nMembers]` and the
  count goes up by one. Corroborated by a second code path: the writer agrees with two readers,
  `sub_005C2740_ItemBuildSetV0` (walks `members[0 .. nMembers−1]`) and `sub_00660120_SetBonusApply`
  (reads `+0x0C` to choose partial or full bonuses). ([items/0004 § 7](../findings/items/0004-uniques-sets.md#7-load-time-slots-in-uniqueitems-setitems-and-sets-the-backlog-questions),
  fn:sub_00634DC0_LoadSetTables@0x00634DC0, fn:sub_005C2740_ItemBuildSetV0@0x005C2740,
  fn:sub_00660120_SetBonusApply@0x00660120, struct:SetsRec+0x0C)
- `[I]` `+0x008` is written neither by the column descriptors nor by the post-load loop, and no reader
  was found in the code read for items/0004 (not a full search). ([items/0004 § 7](../findings/items/0004-uniques-sets.md#7-load-time-slots-in-uniqueitems-setitems-and-sets-the-backlog-questions), 0x00634DC0)

## Interpretation notes

- `[C]` `level` is not compiled, but every set item carries the same value in its own `lvl`
  (`python3 -I tools/unique_survey.py … ` prints `SetItems lvl against its Sets level: 0 below, 127
  equal, 0 above`). A reader of the `.bin` that needs a set's level gets it from a member row.
- `[C]` The set items of the 16 classic sets are `setitems` rows 0..61 and those of the 16 expansion
  sets rows 62..126; the version changes once along `setitems` record order. `setitems.txt` has no
  `version` column, so the set's `version` is the only version a set item has in the data. `[I]` The
  loader copies it into each member row (`setitems` `+0x022`) and the set builder tests that copy: a
  member of a set with `version` ≥ 100 is a candidate only in an expansion game.
  ([items/0004 § 4](../findings/items/0004-uniques-sets.md#4-the-set-builder-items_buildsetitem-rec-0x005c2940), 0x005C2630, tbl:Sets.txt:version)
- `[I]` Set 29 (`Cow King's Leathers` in stock data) is the one set the builder treats apart: its members
  are candidates only when the drop's source is a `hellbovine`. ([items/0004 § 4](../findings/items/0004-uniques-sets.md#4-the-set-builder-items_buildsetitem-rec-0x005c2940), 0x005C264E–0x005C265F)
- The bonus columns go to `items/properties`. Their `.bin` positions above come from `probe`
  (`PCode2a` `+0x010`, `PParam2a` `+0x014`, `PMin2a` `+0x018`, `PMax2a` `+0x01C`, …); several param
  columns hold skill names or parse to no single encoding, which is why the block is left unmapped.

## Open questions

- Answered by [items/0004 § 7](../findings/items/0004-uniques-sets.md#7-load-time-slots-in-uniqueitems-setitems-and-sets-the-backlog-questions): `+0x00C` and `+0x110..+0x127` (`[C]`, § Record
  layout); whether `version` and `SetItems.lvl` gate the set builder (both do, `[I]`, Interpretation notes
  and [SetItems](SetItems.md)).
- `[L]` What `+0x008` is: no writer and no reader found; a full search of the `sets` readers would settle it.

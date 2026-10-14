# MonType (`data/global/excel/montype.txt` → `montype.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 59 (row 0 blank, no `Expansion` marker)   **Record:** 12 B (`0x0C`)
> **sha256:** `.txt` `755edd9bbe12e8427373d1725e0bcea62f31fca0a75871936057cca432960faa`, `.bin` `81c4732b29d441a64cdf2bcd0c157cd71fa872f29f1765b4ea01ec65a2d2ce6f`
> **Doc status:** complete for layout; `equiv1`–`equiv3` semantics `[I]` by the matrix builder
> ([monsters/0003 § 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible)); `strsing`/`strplur` `[L]`

## Purpose

One row per monster *type*, a category that several MonStats classes share (`skeleton`, `zombie`, `fallen`, `demon`,
`undead`, …). A class names its type in [MonStats](MonStats.md) `MonType`; [MonUMod](MonUMod.md) `exclude1`/`exclude2`
name a type a special-monster mod may not go on. A row lists up to three other types in `equiv1`–`equiv3`, which is how
the table expresses a hierarchy (`skeleton` → `lowundead` → `undead`). The code turns those links into a bit matrix
that the mod picks test ([monsters/0003 § 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible)).
Leads: no lead; derived from data.

## Row identity

- `[C]` The `.bin` is a u32 record count (59) and 59 records of 12 bytes (4 + 59 × 12 = 712 bytes), one per `.txt` row
  in order ([excel-bin.md](../formats/excel-bin.md)). The loader's record size 12 is confirmed in
  [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables) (`0x00658615`).
- `[C]` Row 0 has a blank `type`. Every reference to this table stores the row index, and a blank cell is stored as 0,
  so "blank" and "row 0" are the same value (MonStats `MonType`, MonUMod `exclude1`/`exclude2`, and `equiv1`–`equiv3`
  here). tbl:MonType.txt:type
- `[C]` `type` is unique over the 59 rows. The record's `+0x000` holds the row's own index (0..58), so the key string
  itself is not compiled. tbl:MonType.txt:type
- `[C]` Every `equiv` cell names an earlier row (no forward reference, no cycle in stock data). tbl:MonType.txt:equiv1
- `[I]` The loader keeps the row count at `DataTables+0xC40`, and the matrix built from it at `DataTables+0xC44`
  ([monsters/0003 § 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible),
  fn:sub_00658520_MonTypeLoad@0x00658520).

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel montype`: 59 records × 6 mapped
fields = 354 cells, **0 mismatches**; `excel_bin.py unknown … montype` lists no uncovered byte. The layout is
`LAYOUTS["montype"]` in [tools/excel_layouts.py](../../tools/excel_layouts.py). Value counts below are from the `.txt`
by script (`equiv*` resolved against `type`).

| Column | Observed type / range | `.bin` field | Meaning (`[L]` unless stated) | References | Layout tag |
|---|---|---|---|---|---|
| `type` | str, 58 distinct + blank row 0 | `+0x000` s16 = row index | the type's key name, referenced by row index | — | [C] |
| `equiv1` | str, 32 set (`demon` 16, `lowundead` 6, `insect` 4, `undead` 3, `highundead` 2, `construct` 1), 27 blank | `+0x002` s16 row index, blank 0 | `[I]` a type reachable from this one (see *equiv semantics*) | `montype:type` | [C] |
| `equiv2` | str, 1 set (`undeadfetish` → `demon`), 58 blank | `+0x004` s16 row index, blank 0 | `[I]` as `equiv1` | `montype:type` | [C] value; width s16 by the reader |
| `equiv3` | blank in all rows | `+0x006` s16 (0 everywhere) | `[I]` as `equiv1` | `montype:type` | [C] value; slot by the reader |
| `strsing` | str, 7 set (`Yeti` ×2, `Afflicted`, `Fallen`, `HellSwarm`, `Fetish`, `Undead Fetish`), 52 blank | `+0x008` u16 string-table index, blank 5382 | singular display name of the type; no reader read | — | [C] |
| `strplur` | str, equal to `strsing` in every row | `+0x00A` u16 string-table index, blank 5382 | plural display name; no reader read | — | [C] |
| `*eol` | always 0 | — | end-of-line marker | — | — |

- `[C]` `equiv2` and `equiv3` carry one value and none, so `probe` cannot place them alone. Their slots and the s16
  width are those of the reader, which takes `equiv1`..`equiv3` as s16 at `+0x02`/`+0x04`/`+0x06`
  (fn:sub_00658520_MonTypeLoad@0x00658520); the `diff` agrees cell for cell. tbl:MonType.txt:equiv2
- `[C]` The string keys resolve with [tools/tbl.py](../../tools/tbl.py) (`--key`): e.g. `Afflicted` 3020, `Fallen`
  3082, `Yeti` 2998. 5382 is the index a blank or unknown key compiles to ([formats/tbl.md](../formats/tbl.md)).
  tbl:MonType.txt:strsing
- `[C]` MonStats `MonType` resolves in every row (55 distinct types, 128 blank = row 0). `insect`, `lowundead` and
  `highundead` are named by no MonStats class; they exist only as `equiv` targets. tbl:MonStats.txt:MonType

Illustrative rows (`.txt` → `.bin` record):

| Row | `type` | `equiv1` | `equiv2` | `strsing` | record (hex) |
|---|---|---|---|---|---|
| 0 | *(blank)* | | | | `0000 0000 0000 0000 0615 0615` |
| 8 | `skeleton` | `lowundead` (6) | | | `0800 0600 0000 0000 0615 0615` |
| 12 | `fallen` | `demon` (2) | | `Fallen` | `0c00 0200 0000 0000 0a0c 0a0c` |
| 37 | `undeadfetish` | `lowundead` (6) | `demon` (2) | `Undead Fetish` | `2500 0600 0200 0000 5a0b 5a0b` |

## equiv semantics

The code side is [monsters/0003 § 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible);
this section only describes what the columns hold and what that finding derives from them.

- `[I]` `equiv1`–`equiv3` are edges of a directed graph over the rows: row `t` links to the types it lists. The loader
  sets bit `j` of matrix row `i` when `j` is reachable from `i` along those edges, `i` itself included (the walk's exact
  rules on 0 cells, row 0 and its depth limit are in the finding). The mod-pick test `MonTypeIsA(class, t)` asks whether the class's `MonType` is reachable from
  `t`, so a MonUMod `exclude` type `t` covers the classes of `t` and of every type `t` reaches, not the classes of the
  types that list `t` (fn:sub_00658460_MonTypeReachable@0x00658460, fn:sub_005A0070_MonTypeIsA@0x005A0070,
  [monsters/0003 § 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible)).
- `[C]` By data, the reachable sets are small: the longest is 4 types (`undeadfetish` → `lowundead`, `demon`,
  `undead`, itself); `skeleton` reaches `lowundead` and `undead`; `undead` reaches only itself. Twelve rows reach
  `undead`. tbl:MonType.txt:equiv1
- `[C]` The only stock `exclude` is MonUMod `lightning` → `sandleaper` (row 22), which lists no `equiv`, so the
  direction of the closure makes no difference with stock data (also stated in monsters/0003 § 3). tbl:MonUMod.txt:exclude1

## Open questions

- `[L]` Readers of `strsing`/`strplur` (probably a client-side name for the type); none read yet.
- `[L]` Whether other code than the MonUMod `exclude` test reads the MonType matrix or the raw `equiv` columns.

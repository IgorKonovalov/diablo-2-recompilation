# Runes (`data/global/excel/Runes.txt` → `runes.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 169 (no `Expansion` marker)   **Record:** 288 B (`0x120`)
> **sha256:** `.txt` `f8869655f58f5759919d088b3557e9e0615265f11ee70571a3c15334f95fc935`, `.bin` `7866bdb5aa0fa63670f346e82b532b8260e4f175728fdbdbc856f6806b2a6661`
> **Doc status:** layout complete (plan 0029 Phase 0); semantics from [items/0007](../findings/items/0007-sockets-runewords.md) (plan 0029 Phase 1)

## Purpose

One row per runeword: its string key and editor name, whether it is enabled (`complete`) and flagged `server`, the
item types it may go on (`itype1..6`, minus `etype1..3`), the runes in order (`Rune1..6`), and up to seven property
lines (`T1Code1..7` with `T1Param`, `T1Min`, `T1Max`). Reader: `items/sockets-runewords` (plan 0029), the save code
(the runeword field of an item, [save/0001 § 7](../findings/save/0001-d2s-io.md#7-one-item-items_serializebits--items_writefull--items_writecompact)).
Leads: no lead; derived from data.

## Row identity

- `[C]` The `.bin` is a u32 record count (169) and 169 records of 288 bytes, one per `.txt` row in order; the table
  has no `Expansion` marker ([excel-bin.md](../formats/excel-bin.md)). The loader allocates 288-byte records
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x00639C3F`).
- `[C]` `Name` is a string-table key, not unique: 168 distinct keys over 169 rows; `Runeword95` names both row 39
  (*Passion*, `complete` 1) and row 118 (*Patience*, not complete). 168 rows' keys resolve in `expansionstring.tbl`
  (indices 20000+), `Runeword22` (*Delirium*, row 29) only in `patchstring.tbl` (10910) (`tools/tbl.py lookup`).
  `Rune Name` (169 distinct) is the editor's name. The row order is not the key order (row 0 is `Runeword1`, row 1
  `Runeword6`, row 2 `Runeword44`).
- `[C]` **`+0x082` (u16, no column, 0 in every record of the file)** is the string index of the row's `Name`, which
  `RUNES_Load` writes at load with `STRTABLE_GetByKey(Name)`. A save stores the runeword of an item as this u16
  (`ITEMS_WriteFull` writes it, or `0xFFFF` when no row matches) ([save/0001 § 7](../findings/save/0001-d2s-io.md#7-one-item-items_serializebits--items_writefull--items_writecompact),
  [items/0007 § 5](../findings/items/0007-sockets-runewords.md#5-the-runeword-runeword_applyparent-child-0-0x006600a0), fn:RUNES_Load@0x006394A0, 0x00639C44–0x00639C7F). Corroboration: the one sample runeword, *Steel* in
  `qitbarb`, stores 20639 ([d2s.md](../formats/d2s.md)), the string index of row 18's `Name` key `Runeword134`
  (expansionstring entry 639). The duplicate `Runeword95` gives *Passion* and *Patience* the same value `[I]`.
- `[I]` **Rows are matched by scan**: `RUNEWORD_Match` walks the records from 0 and returns the first that qualifies
  (the columns below); no two `complete` stock rows share a rune sequence, so the order changes nothing on stock data
  ([items/0007 § 4](../findings/items/0007-sockets-runewords.md#4-the-match-runeword_match-0x0062bed0), fn:RUNEWORD_Match@0x0062BED0).

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel runes`: 169 records × 47 mapped
fields = 7943 cells, **0 mismatches**; `excel_bin.py unknown … runes` lists only `+0x082..+0x085`, 0 in every record.
Observed values are from the `.txt` cells.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Name` | str, 168 distinct (`Runeword1` … `Runeword170`) | `+0x000` char[64] | string key of the runeword's name | `expansionstring.tbl`, `patchstring.tbl` ([tbl](../formats/tbl.md)) | [C] |
| `Rune Name` | str, 169 distinct, max 20 chars | `+0x040` char[64] | editor name | — | [C] |
| `complete` | int {1} on 78 rows, 91 blank | `+0x080` u8 | 0 = the row never matches `[C]` ([items/0007 § 4](../findings/items/0007-sockets-runewords.md#4-the-match-runeword_match-0x0062bed0); the match of run:2026-10-15-sockets) | — | [C] |
| `server` | int {1} on 23 rows (all `complete`), 146 blank | `+0x081` u8 | the 23 are *Spirit*, *Oath*, *Obedience*, *Harmony*, *Fortitude*, *Faith*, *Brand*, *Death*, *Destruction*, *Dragon*, *Dream*, *Edge*, *Ice*, *Infinity*, *Insight*, *Last Wish*, *Lawbringer*, *Phoenix*, *Pride*, *Rift*, *Widowmaker*, *Winter*, *Wrath*. Non-zero = the runeword is applied only in a ladder game (`Game+0x74`); otherwise the insert still succeeds with no runeword. `RUNEWORD_Match` does not test it; `ITEMS_InsertSocket` does `[I]` ([items/0007 § 1](../findings/items/0007-sockets-runewords.md#1-the-insert-items_insertsocket-0x00562660), fn:ITEMS_InsertSocket@0x00562660) | — | [C] |
| — | — | `+0x082` u16 | no column; 0 in the file; `Name`'s string index, written at load (Row identity) | — | [C] |
| — | — | `+0x084` u16 | no column; 0 in every record; no reader found (`struct:RunesRec` `_pad084`) | — | [C] value 0; meaning `[L]` |
| `itype1` | str, 15 distinct, 83 blank | `+0x086` u16 row index, blank 0 | first allowed item type: the parent must be of one of `itype1..6` (`ITEMS_UnitIsType`, so `Equiv` counts); a 0 ends the list `[C]` ([items/0007 § 4](../findings/items/0007-sockets-runewords.md#4-the-match-runeword_match-0x0062bed0)) | [ItemTypes](ItemTypes.md) `Code` | [C] |
| `itype2` | str, 10 distinct, 144 blank | `+0x088` u16, blank 0 | — | [ItemTypes](ItemTypes.md) `Code` | [C] |
| `itype3` | str, 6 distinct, 160 blank | `+0x08A` u16, blank 0 | — | [ItemTypes](ItemTypes.md) `Code` | [C] |
| `itype4`, `itype5`, `itype6` | blank in every row | `+0x08C`, `+0x08E`, `+0x090` u16 | further allowed types | [ItemTypes](ItemTypes.md) `Code` | [C] value 0; slots `[I]` (the match reads `itype[6]` at `+0x86`, [items/0007 § 4](../findings/items/0007-sockets-runewords.md#4-the-match-runeword_match-0x0062bed0)) |
| `etype1`, `etype2`, `etype3` | blank in every row | `+0x092`, `+0x094`, `+0x096` u16 | excluded types: a parent of any of them never matches the row; tested before `itype`; a 0 ends the list `[I]` ([items/0007 § 4](../findings/items/0007-sockets-runewords.md#4-the-match-runeword_match-0x0062bed0); no stock row uses it) | [ItemTypes](ItemTypes.md) `Code` | [C] value 0; slots `[I]` (the match reads `etype[3]` at `+0x92`) |
| `*runes` | str, 51 distinct, 118 blank (rune letters joined, e.g. `TirEl`) | — (not compiled) | editor comment | — | [C] |
| `Rune1` … `Rune6` | item codes `r01` … `r33`; 83, 83, 69, 37, 12, 3 rows filled | `+0x098` + 4·(k−1) s32 item record index, blank −1 | the runes, equal to the children's base items in socket (insertion) order; a value < 1 ends the list; the row needs at least as many runes as the item has sockets, and every socket filled `[C]` ([items/0007 § 4](../findings/items/0007-sockets-runewords.md#4-the-match-runeword_match-0x0062bed0); the stale `kids[n]` read for a row one rune longer is in the finding) | weapons + armor + misc `code` ([Misc](Misc.md)) | [C] |
| `T1Code1` … `T1Code7` | property codes (33, 46, 47, 41, 45, 38, 30 distinct) | `+0x0B0` + 16·(k−1) s32 row index, blank −1 | property line *k*, applied in column order into a state-171 list on the parent; the first `code < 0` ends the list `[C]` ([items/0007 § 5](../findings/items/0007-sockets-runewords.md#5-the-runeword-runeword_applyparent-child-0-0x006600a0)) | [Properties](Properties.md) `code` | [C] |
| `T1Param1` … `T1Param7` | numbers or skill names (109 cells hold a skill name, e.g. `Holy Freeze`, `enchant`) | `+0x0B4` + 16·(k−1) s32: the number, or the named skill's row index (case-insensitive) | the line's parameter | [Skills](Skills.md) `skill` (named cells) | [C] |
| `T1Min1` … `T1Min7` | int −100..750 | `+0x0B8` + 16·(k−1) s32 | the line's minimum, rolled per items/0006 on the **inserted child's** item seed `[C]` ([items/0007 § 5](../findings/items/0007-sockets-runewords.md#5-the-runeword-runeword_applyparent-child-0-0x006600a0)) | — | [C] |
| `T1Max1` … `T1Max7` | int −100..775 | `+0x0BC` + 16·(k−1) s32 | the line's maximum (as `T1Min`) `[C]` ([items/0007 § 5](../findings/items/0007-sockets-runewords.md#5-the-runeword-runeword_applyparent-child-0-0x006600a0)) | — | [C] |
| `eol` | int {0} | — (not compiled) | end-of-line marker | — | [C] |

The `T1Param` rule is the one `tools/excel_bin.py` applies with the field option `names="skills:skill"`: a cell that is
not a number is stored as the row index of that skill name, matched case-insensitively (`enchant` → 52,
`fanaticism` → 122, `Delerium Change` → 350); all 109 such cells match. The SetItems `par` cells that hold a skill name
follow the same rule, through the same option ([SetItems](SetItems.md)).

## Survey of the stock rows

`python3 -I tools/socket_survey.py runes workspace/merged/data/global/excel` prints every row: record index, `Name`,
`Rune Name`, `complete`, `server`, the item types, the runes (letter and code), the rune count, the bases and the
property lines. `summary` gives the counts (gate survey `socket_survey`). Two rows as it prints them:

```
 18 Runeword134  Steel                  complete=1 server=0 runes=2
     itype axe mace swor
     runes Tir(r03) El(r01)
     bases 83: 2ax 2hs 72a 72h 7ax 7b7 7ba 7bs 7bt 7cm 7cr 7fb ...
     + swing2 25..25
     + dmg-min 3..3
     + dmg-max 3..3
     ...
103 Runeword62   Insight                complete=1 server=1 runes=4
     itype pole staf
     runes Ral(r08) Tir(r03) Tal(r07) Sol(r12)
     bases 24: 6bs 6cs 6ws 7h7 7pa 7s8 7vo 7wc 8bs 8cs 8ws 9h9 ...
     + dmg% 200..260
     + att% 180..250
     ...
```

| count | value | how |
|---|---:|---|
| rows | 169 | |
| `complete` | 78 | rows 0–43 all complete, then 34 more up to row 167 |
| `server` | 23 | all among the complete rows |
| complete rows by rune count | 2: 13, 3: 28, 4: 25, 5: 9, 6: 3 | `Rune1..6` filled |
| rows with runes but not `complete` | 5 | *Pattern* (119), *Plague* (127), *Vengeance* (153), *Voice* (155), *Wonder* (166) |
| property lines | 508 (494 on complete rows) | `T1Code1..7` filled |
| classic-legal rows | **0** | every rune (`r01`…`r33`) is a misc item of version 100, so no row can be built from classic items |
| complete rows with a base | 78 | some weapons/armor row reaches an `itype` through `Equiv1/2`, no `etype`, and `gemsockets` ≥ the rune count |

`complete` rows by `itype` value: `tors` 20, `swor` 12, `axe` 10, `shld` 8, `miss` 8, `weap` 8, `pole` 8, `hamm` 6,
`mele` 6, `mace` 5, `scep` 5, `helm` 5, `staf` 4, `club` 1, `wand` 1, `pala` 1, `h2h` 1. The "bases" definition is
data only. The game's own test is `RUNEWORD_Match`: parent quality not 4..9 (low, normal and superior qualify),
base `quest` 0, every socket filled, then the row tests above; it does not test `MaxSock*`, `server`, the item
version or the game type `[I]` ([items/0007 § 4](../findings/items/0007-sockets-runewords.md#4-the-match-runeword_match-0x0062bed0)).

## Interpretation notes

- **Ranges that run backwards.** Many lines have `T1Min` > `T1Max`: `charged` (e.g. *Black* `charged` 74, 12..4),
  `hit-skill`, `gethit-skill` and the like. For those property funcs the two columns are not a range (in the other
  item tables they read as charges and level, or chance and level). The runeword roll hands each line to the
  property funcs exactly as items/0006 § 3–4 does, with the inserted rune as "the item" `[C]`
  ([items/0007 § 5](../findings/items/0007-sockets-runewords.md#5-the-runeword-runeword_applyparent-child-0-0x006600a0); [Properties](Properties.md), [items/properties](../specs/items/properties.md)).
- **No `etype` and no `itype4..6` in the stock data.** The layout check cannot cover them; their slots are the
  `int16 itype[6]` at `+0x86` and `etype[3]` at `+0x92` that `RUNEWORD_Match` reads `[I]` ([items/0007 § 4](../findings/items/0007-sockets-runewords.md#4-the-match-runeword_match-0x0062bed0)).
- Recipes `tools/d2s_recipes/socketnova.json` (expansion) and `socketclassic.json` (classic) build Sorceresses with
  socketed bases and loose gems, runes and jewels for the insert runs; socketnova's runes make *Steel*, *Stealth*,
  *Lore*, *Rhyme* and *Malice* ([d2s.md § Building socketed items](../formats/d2s.md#building-socketed-items)).

## Open questions

- `[L]` What `+0x084` holds (no column, 0 everywhere, no reader found). Matching, `+0x082` and the `T1` rolls are
  settled by [items/0007](../findings/items/0007-sockets-runewords.md).

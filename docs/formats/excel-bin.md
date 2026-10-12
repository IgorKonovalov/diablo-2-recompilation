# Excel tables: `.txt` source and compiled `.bin`

Owned by `archivist`. Files live in `data/global/excel/` of `workspace/merged/` ([mpq.md](mpq.md)).
The inventory with counts is in [tables/README.md](../tables/README.md). Tools:
`tools/excel_survey.py` (shape survey), `tools/excel_bin.py` (layout-driven decoder and `.txt`↔`.bin`
cell diff; layouts in `tools/excel_layouts.py`), `tools/tbl.py` (string-table keys, [tbl.md](tbl.md)).

Per-table record layouts are in the table docs. Layouts done so far (plan 0002 Phase 1):
[TreasureClassEx](../tables/TreasureClassEx.md), [ItemRatio](../tables/ItemRatio.md),
[ItemTypes](../tables/ItemTypes.md), [Weapons](../tables/Weapons.md), [Armor](../tables/Armor.md),
[Misc](../tables/Misc.md), [MonStats](../tables/MonStats.md), [Levels](../tables/Levels.md) (with
`leveldefs.bin`), plus the affix and rare-affix layouts used for the mixed-archive check below.
Every layout in `tools/excel_layouts.py` (26 tables, [MonLvl](../tables/MonLvl.md) the latest) is re-diffed by
`python3 -I tools/excel_bin.py survey <excel-dir>`, registered in the docs gate as the `excel_layout` survey
(`python3 -I tools/gate.py --full`): its baseline holds each table's cell count and unexplained mismatches
(0 for every table), so a layout `[C]` tag that a change breaks turns the gate red.
Plan 0005 Phase 1 added [LvlPrest](../tables/LvlPrest.md) (the DS1 references, [ds1.md](ds1.md)).

## `.txt` (tab-separated source)

- `[C]` Tab-separated, one header row of column names, CRLF line endings on every line (also the
  last), no BOM. Checked over all 92 `.txt` files.
- `[C]` Encoding is a single-byte Windows code page. Only two non-ASCII bytes occur in the whole
  set: `0x85` (×2, `objects.txt`) and `0x92` (×1, `uniqueitems.txt`). In CP1252 they are `…` and
  `’`, which fit their context. Read as bytes or latin-1, and split rows on `\n` **only**:
  Python's `str.splitlines()` also breaks on `\x85` and miscounts `objects.txt`.
- `[C]` 30 tables contain an **`Expansion` marker row**: first field `Expansion`, the rest usually
  empty but sometimes with a stray value (`Expansion\t\t0` in `ObjType`, `Expansion\tExpansion…`
  in `misc`). In all 30, the compiled `.bin` has no record for it, so every record after the marker
  sits one index lower than its `.txt` data row. `tools/excel_bin.py diff` confirms the alignment
  cell by cell for the nine tables below.
- `[C]` A **tab-only line is a record**. `uniqueitems.txt` ends with a line of 69 tabs and nothing
  else, and `uniqueitems.bin` has a matching empty-name record at index 401 (its last). So a row
  counter must skip only zero-length lines. Likewise `treasureclassex.txt` ends with a row whose
  only non-empty cell is `Term = 0`; it is record 852, a TC with an empty name.
- `[C]` Row identity is not always "row index". `objects.txt` has rows with duplicate `Id` (408 and 409
  appear twice, once on each side of the marker) and no row for Ids 411–412. `monstats.txt` has the
  `Id` `cr_lancer8` twice (rows 617 and 723), see [index columns](#index-columns-names-and-codes-become-indices).

## `.bin` (compiled form)

| offset | size | type | name | meaning | tag |
|---|---|---|---|---|---|
| `0x00` | 4 | u32 LE | `count` | number of records | `[C]` |
| `0x04` | `count × recsize` | bytes | records | fixed-size records, layout per table | `[C]` |

- `[C]` For all 88 `.bin` files with this header (87 with a `.txt` twin, plus `leveldefs.bin`),
  `(size − 4)` is an exact multiple of `count`, and `count` equals the twin's `.txt` data rows
  (57 tables), or those rows minus the `Expansion` markers (30 tables). Data-behaviour
  corroboration over every file; no code anchor yet.
- `[C]` Records are packed: no padding is inserted for alignment. Fields sit at odd offsets
  (`levels.bin` `LevelName` at `+0x0F5`, `weapons.bin` `rarity` at `+0x0FC` followed by u8 runs), and
  the few gaps that exist are explicit zero bytes in every record.
- `[C]` Record sizes range from 2 bytes (`sounds`, `monai`, `uniqueprefix`…) to 1928 bytes
  (`LvlTypes`). Several 2- and 4-byte tables are single-column code lists (`bodylocs`, `colors`,
  `ElemTypes`…), so a record there is probably a code or a string-table index `[L]`.
- `[C]` **`leveldefs.bin` is the other half of `Levels.txt`.** It has 137 records of 156 bytes, one per
  `Levels.txt` row, and holds 42 of its columns (`QuestFlag`, `Layer`, `SizeX/Y` ×3, `OffsetX/Y`,
  `Depend`, `DrlgType`, `LevelType`, `Sub*`, `Vis0..7`, `Warp0..7`, light colour, `Portal`,
  `Position`, `SaveMonsters`, `LOSDraw`). `levels.bin` holds the other 96. No column is in both;
  `Name` and `Beta` are in neither. `leveldefs +0x30` is **`DrlgType`** (u32, values 0..3) and
  `+0x34` is **`LevelType`** (u32, 0..35), both matched over all 137 records. Layout:
  [Levels.md](../tables/Levels.md#leveldefsbin-156-b).
- `[C]` Four `.bin` files do **not** use the count header: `itemscode.bin` (158 B), `misscode.bin` (196 B),
  `skillscode.bin` (5891 B), `skilldesccode.bin` (4252 B). They are the bytecode pools that calc
  columns point into (see [calc columns](#calc-columns-formulas)). `compcode.bin` *does* have the
  count header (115 × 4 B).

## Cell encoding rules

Each rule below is **`[C]` by data behaviour**: `excel_bin.py diff` applies it to every cell of the
nine Phase 1 tables and finds no unexplained mismatch (one explained, see
[MonStats.md](../tables/MonStats.md)). The reverser has since located the converters for the
case-insensitive header match (unknown headers skipped), the unvalidated digit parsing with truncation
and the space-padded 4-character codes `[I]`
([data/0001 §8](../findings/data/0001-excel-loader.md#8-answers-to-the-archivists-phase-1-questions)); the
missing-column defaults, the key not-found value and the string-table key order have no code anchor yet.

### Columns are found by name

- `[C]` The compiler looks columns up **by header name, case-insensitively**. `weapons.txt`
  `alternateGfx` and `armor.txt`/`misc.txt` `alternategfx` fill the same field; `Nameable` and
  `nameable` likewise.
- `[C]` **A misspelled header is silently ignored.** `weapons.txt` and `armor.txt` spell the Hratli
  vendor column `HratliMagicLvl`; the field it should fill (`+0x190`, `HraltiMagicLvl` in `misc.txt`)
  is 0 in all 508 weapon and armor records, although the cells are 20/255 and 1/255.
- `[C]` **A column missing from a `.txt` leaves its field at a fixed default**: 0 for integer,
  string, code and string-index fields; −1 (all bits set) for index fields and calc offsets. The
  three item tables share one 424-byte layout and each lacks 31–37 of its columns; every such cell
  (22 253 of them) has that default. Same in `magicsuffix` (no `etype4/5` → `0xFFFF`) and `automagic`.
- `[C]` Header columns that feed no field: comment columns (`*eol`, `*name`), editor helpers
  (`TreasureClassEx` `SumItems`/`TotalProb`/`DropChance`), names that rows are not keyed by
  (`ItemType`, weapons/armor/misc `name`, `Levels` `Name`), and a few real-looking columns whose values
  appear nowhere in the record (`quivered`, affix `transform`, rare-affix `add`/`multiply`/`divide`,
  `Levels` `Beta`). Each table doc lists them. A duplicated header (`armor.txt` has `mindam`/`maxdam`
  twice) feeds the field from its **first** occurrence.

### Integers

- `[C]` A blank cell is 0, except in index fields (below).
- `[C]` Numbers are parsed digit by digit **without validation**: an optional leading `-`, then every
  character adds `(byte − 0x30)` to `value × 10`. A cell holding a single space therefore compiles to
  −16, stored as `0xF0` in a u8 (`misc.txt` `TMogMin`/`TMogMax` of the three Khalim parts).
- `[C]` The value is then **truncated to the field width** with no range check: `rarity = 999`
  (seven `misc.txt` rows) is stored as `999 & 0xFF = 231`; `spawnx = -2` (monstats `suckernest1..4`)
  as `0xFE`.
- `[C]` Field widths are 1, 2 or 4 bytes; a table's columns use different widths (TCEx `Picks` is 4 bytes,
  `group` 2). Offset and width are pinned by the data where values vary; **signedness is not**:
  the docs write `s` where the column holds negative values and `u` otherwise. `[I]` for signedness.
- `[C]` Boolean columns are either a whole byte (most tables) or **one bit of a packed flags word**
  (monstats `+0x0C..+0x0F`: 29 columns, one bit each; the bit order is not the header order).

### Strings

- `[C]` String cells (file names, TC names, `LevelName`) are copied into a fixed `char[N]` and
  NUL-terminated; the rest of the array is zero. No cell in the nine tables reaches its `N`, so
  overflow behaviour is untested. Blank is an empty string (all zero).
- `[C]` **4-character codes** (item `code`, `normcode`, `wclass`, monstats `Code`…) are stored as
  4 raw bytes, space-padded (`"hax "`); a blank code is four spaces (weapons `ubercode`/`ultracode`
  ×15, itemtypes `Code` ×5), and a column missing from the `.txt` gives four zero bytes (misc
  `normcode`). No code cell in these tables is longer than 4 characters, so cutting is untested
  for code fields (it is observed for item-type references, below).

### String-table keys

- `[C]` `namestr`, `spelldescstr`, monstats `NameStr`/`DescStr` are stored as a **u16 string index**,
  not as text: the key is looked up in `patchstring.tbl` (index 10000 + entry), then
  `expansionstring.tbl` (20000 + entry), then `string.tbl` (entry). A blank or unknown key stores
  **5382** (the entry of key `dummy` in `string.tbl`); a column missing from the `.txt` stores 0.
  Details and the one exception (`Lilith`) in [tbl.md](tbl.md).
- `[C]` The indices depend on the language's `.tbl` files (`deu`/`fra` `string.tbl` have 5322 keys,
  `eng` 5391), and the shipped `.bin` values are the English ones: the 147 unique-name rows match the
  `eng` lookup 147/147 and the `deu`/`fra` lookup 0/147 ([tbl.md § Unique monster name tables](tbl.md#unique-monster-name-tables)).

### Index columns: names and codes become indices

The compiler turns a reference to another table into that row's index. Observed rules:

- `[C]` **Lookup is "first row whose key equals the cell"**, and the cell is looked up **even when
  blank**. If the target table has a row with an empty key, a blank cell gets that row's index;
  otherwise it gets −1. So `itemtypes.txt` refs (`type`, `Equiv1`, `itype1`…) store **0** for a blank
  cell (row 0, `None`, has an empty code), as do `bodylocs`, `hitclass`, `elemtypes`, `montype`,
  `monsounds` and `sounds` refs; refs to `states`, `itemstatcost`, `properties`, `skills`, `missiles`,
  `monstats`, `monstats2`, `monprop`, `monai`, `playerclass`, `storepage`, `colors`, `monmode` store
  **−1** (`0xFF`/`0xFFFF`/`0xFFFFFFFF` by width). A non-blank key that matches nothing would also be −1;
  none occurs in the nine tables.
- `[C]` **Item-type codes are cut to 4 characters** before the lookup: `staff` in `magicprefix.txt`
  finds `staf`, `ring ` (trailing space) in `magicsuffix.txt` finds `ring`.
- `[C]` **Monster references use the ordinal of the `Id` among distinct `Id`s**, not the `.txt` row:
  `monstats.txt` repeats `cr_lancer8` (rows 617 and 723), so every later monster is one lower.
  `monstats.bin +0x000` holds that ordinal for each record (617 for both `cr_lancer8` rows, 723 for
  `overseer6` at record 724), and `levels.bin` `mon1`/`nmon1`/`umon1` of *Pandemonium 3* store
  `overseer6` as 723, the index of the **second `cr_lancer8` record**. `[I]` The game uses the stored
  value as a record position (nothing remaps it at load), so after the duplicate every monster
  reference points one record early
  ([data/0001 §8](../findings/data/0001-excel-loader.md#8-answers-to-the-archivists-phase-1-questions)).
- `[C]` **TC references in `monstats` store (TreasureClassEx row + 161)**; blank stores 0. All 4 362
  non-blank cells fit. The 161 slots below the first TCEx row are not in any excel table: `[C]` slot 0
  is an empty-named TC and slots 1–160 are the auto-built item-type TCs (5 itemtypes with
  `TreasureClass = 1` × 32 levels), created at load time before the TCEx rows
  ([data/0001 §7–8](../findings/data/0001-excel-loader.md#7-treasure-classes-at-load-time)).
- `[C]` **`TreasureClassEx` items are not indices.** `Item1..10` are stored as the cell text in
  `char[64]` arrays, so whether an entry names an item code, an item-type TC like `weap12`, or another
  TC is resolved when the game loads the table, not at compile time. `[C]` The resolving function is
  `TC_ParseItemCell` `0x00654440`; resolution order in
  [data/0001 §7](../findings/data/0001-excel-loader.md#7-treasure-classes-at-load-time).
- `[C]` `monstats` `SknMode` stores a `monmode` index (blank → 0, not −1), and a `seq_*` value stores 14
  (`xx`, sequence) plus the sequence's ordinal among distinct `monseq.txt` `sequence` values (blank
  row 0 included) in a second field (`+0x188 + 2k`, −1 when not a sequence).

### Calc columns (formulas)

- `[C]` Formula columns (`misc` `calc1..3`, `len`, `spelldesccalc`) are an **s32 offset into a
  header-less bytecode file** (`itemscode.bin` for the item tables); a blank cell is −1. Offsets are
  allocated in record order, and within a record in the order `len`, `calc1`, `calc2`, `calc3`,
  `spelldesccalc`.
- `[C]` An integer constant `n` compiles to `07 nn 00` when it fits a signed byte and `08 nn nn 00`
  (u16 LE) otherwise (`5` → `07 05 00`, `750` → `08 EE 02 00`); `00` ends the expression. All 45
  non-blank calc cells in `misc.txt` are such constants and decode back to the cell. Other opcodes
  belong to `data/calc` (not planned).

## Mixed-archive tables: `automagic`, `RarePrefix`, `RareSuffix`

patch_d2 ships a new `.bin` for these three and leaves the d2exp `.txt` (tables/README.md). Decoded
with their layouts and diffed cell by cell:

| table | records | cells compared | mismatches | what patch_d2 changed in the `.bin` |
|---|---:|---:|---:|---|
| `automagic` | 36 | 1 440 (+108 absent-column cells) | **0** | record 132 → 144 bytes (the 144-byte affix layout of `magicprefix`/`magicsuffix`) |
| `RarePrefix` | 46 | 552 | **0** | record 60 → 72 bytes; item-type indices widened u8 → u16 |
| `RareSuffix` | 155 | 1 860 | **0** | record 60 → 72 bytes; item-type indices widened u8 → u16 |

- `[C]` **No cell changed.** Every mapped column of the patch_d2 `.bin` equals the d2exp `.txt`, and
  probing the old d2exp `.bin` against the same `.txt` finds every varying column too. The patch
  re-compiled these tables into a new record format; for their content, `.txt` and `.bin` agree, so
  either side may be cited.
- `[C]` Not compared, because no field holds them: `automagic` `transform`; rare `version`, `add`,
  `multiply`, `divide` (the rare record's first 16 bytes are zero in every record). `RareSuffix.txt`
  has `add = multiply = divide = 1` on its belt rows, which the record does not carry.
- The two pairs that go the other way (`inventory`, `PlrMode`: new `.txt`, d2exp `.bin`) are outside
  plan 0002 Phase 1.

## Open questions

- Answered: the game loads the `.bin` `[C]`; the `.txt` is only compiled under `-txt`, and the result
  is only read with `-direct` as well `[I]`
  ([data/0001](../findings/data/0001-excel-loader.md#answer-summary),
  [data/0002](../findings/data/0002-mpq-precedence.md)).
- `[L]` Cell-encoding rules still without a code anchor: missing-column defaults, the key not-found
  value, the string-table key order (backlog → reverser). The others are anchored `[I]` in
  [data/0001 §8](../findings/data/0001-excel-loader.md#8-answers-to-the-archivists-phase-1-questions).
- `[L]` Bytecode format of the `*code.bin` files beyond integer constants (`data/calc`).
- Unknown fields (no `.txt` column, constant in every record) are listed per table and stay `unk_XXX`.

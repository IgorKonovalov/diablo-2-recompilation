# CubeMain (`data/global/excel/cubemain.txt` → `cubemain.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 151 (no `Expansion` marker)   **Record:** 328 B (`0x148`)
> **sha256:** `.txt` `ff5d7e9b6b6cff4ff5462684eb23358d764ce8c193beff0f1044af7fb0cb544a`, `.bin` `a907396dc4c5e20eb3a1f0848ec9a525eae71486402fd640949feebb7e540fdd`
> **Doc status:** layout complete, every input and output cell decoded (plan 0030 Phase 0); semantics from [items/0008](../findings/items/0008-cube.md) (plan 0030 Phase 1)

## Purpose

One row per Horadric Cube recipe: whether it is enabled, ladder-only, its minimum difficulty, game version, an
`op`/`param`/`value` condition and a class restriction, up to seven inputs, and up to three outputs (`output`,
`output b`, `output c`), each with its level columns and five property lines. Reader: `items/cube`
([plan 0030](../plans/done/0030-items-cube.md)). The loader is `0x00669130`, which allocates 328-byte records
(`0x0066A184`) and aborts with a fatal error if a `cubeserver.bin` or `cubeserver.txt` exists
([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300)).
Leads: no lead; derived from data and the compile probe. The compiled record is `struct:CubeMainRec` in
`re/types/cube.h` (0x148: inputs 8 bytes at `+0x14`, outputs 0x54 bytes at `+0x4C`, mods 12 bytes at output `+0x18`).

**`cubemod` and `cubetype` are not loaded.** `cubemod.txt`/`.bin` (12 rows: `ame`, `rub`, … `mag`, `rar`, `unq`,
`crf`) and `cubetype.txt`/`.bin` (15 rows: `hpt`, `mpt`, `itm`, `axe`, …) ship in d2exp, but `Game.exe` registers no
loader for them and their names do not occur in it `[C]`
([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)). Their codes
are not the ones the compiled cells use: the cube cell keywords are strings in `Game.exe` itself (`0x006EE7D8` …
`0x006EE898`: `nru`, `eli`, `exc`, `bas`, `upg`, `eth`, `noe`, `sock`, `nos`, `tmp`, `crf`, `uni`, `rar`, `mag`, `hiq`,
`nor`, `low`, `qty`, `any`, `rch`, `rep`, `reg`, `rem`, `uns`, `suf`, `pre`, `useitem`, `usetype`, the three portal
names, then `cubemain`). This table is the only cube data the game reads.

## Row identity

- `[C]` The `.bin` is a u32 record count (151) and 151 records of 328 bytes, one per `.txt` row in order; the table
  has no `Expansion` marker ([excel-bin.md](../formats/excel-bin.md)). Rows are addressed by record index; no
  column is a key, and `description` (151 distinct strings) is not compiled.
- `[C]` **The shipped `.bin` is the compiler's output of the shipped `.txt`.** Compiling `cubemain.txt` with the game
  (`-direct -txt`) gives a `cubemain.bin` byte-identical to the shipped one
  ([run:2026-10-15-cube-saves](../formats/experiments.md#run2026-10-15-cube-saves), step 1).
- `[I]` **The transmute is a first-fit scan in record order**: `CUBE_Transmute` tests the header fields below in
  table order (`enabled`, `version`, `ladder`, `min diff`, `class`, `numinputs` against the number of cube items,
  ops 1–14), then the seven inputs; the first row that passes is transmuted and the scan stops. A transmute that
  matches no row does nothing (no draw, no message, nothing moved) ([items/0008 § 1](../findings/items/0008-cube.md#1-the-row-filter-cube_transmute-0x005665f0), fn:CUBE_Transmute@0x005665F0).

## Record layout

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel cubemain`: 151 records × 164
mapped fields = 24 764 cells, **0 mismatches**; `excel_bin.py unknown … cubemain` finds no uncovered byte, and the
18 padding bytes (`U` fields: 3 in the header, 1 per mod line) are 0 in every record. The fields that every stock row leaves blank (`min diff`,
`param`, `value`, `class`, the `mod` chances, `output b`, `output c`) and every cell keyword the stock rows don't use
are placed by the **compile probe**: the game compiled a `cubemain.txt` with those cells filled, and the same diff
over that pair gives 232 records × 164 fields = 38 048 cells, 0 mismatches
([run:2026-10-15-cube-saves](../formats/experiments.md#run2026-10-15-cube-saves); § Compile probe). A third
pair, the plan 0005 sample table (`tools/d2s_samples.py`, compiled the same way on 2026-10-11), diffs with 0
mismatches over 158 records.

```mermaid
flowchart LR
  H["+0x000 header<br/>20 B"] --> I["+0x014 input 1..7<br/>7 × 8 B"]
  I --> A["+0x04C output<br/>84 B"]
  A --> B["+0x0A0 output b<br/>84 B"]
  B --> C["+0x0F4 output c<br/>84 B"]
```

### Header (`+0x000`, 20 bytes)

| Column | Observed (stock) | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `description` | str, 151 distinct | — (not compiled) | editor comment | — | [C] |
| `enabled` | {1} on 146 rows, blank on 5 (rows 142–146) | `+0x000` u8 | 0 = the row is skipped; the override `g_CubeAllRows` is never written, so the five blank rows are unreachable `[I]` ([items/0008 § 1](../findings/items/0008-cube.md#1-the-row-filter-cube_transmute-0x005665f0), data:g_CubeAllRows@0x0088CAC0) | — | [C] |
| `ladder` | {1} on 21 rows (104–122, 131, 132), else blank | `+0x001` u8 | non-zero: the row is skipped only when `Game+0x6A` = 0 **and** the game is not ladder (`Game+0x74` = 0); single player has `Game+0x6A` = 3, so the ladder rows are matchable offline `[I]` ([items/0008 § 1](../findings/items/0008-cube.md#1-the-row-filter-cube_transmute-0x005665f0)) | — | [C] |
| `min diff` | blank in every row | `+0x002` u8 (probe: 2 → 2, 300 → 44: truncated to a byte) | minimum difficulty: the row is skipped when it exceeds `Game+0x6D` (unsigned bytes) `[I]` ([items/0008 § 1](../findings/items/0008-cube.md#1-the-row-filter-cube_transmute-0x005665f0)) | — | [C] |
| `class` | blank in every row | `+0x003` u8 row index, blank −1 (`0xFF`) | `0xFF` any class, else the player's class id must equal it `[I]` ([items/0008 § 1](../findings/items/0008-cube.md#1-the-row-filter-cube_transmute-0x005665f0)) | `playerclass` `Code` (`Expansion` row dropped: `dru` → 5, `ass` → 6) | [C] |
| `op` | {28} on 5 rows (0, 1, 2, 148, 149), else blank | `+0x004` u8 (probe: 300 → 44, −2 → 254) | condition operator: 1–14 test the player in the row filter, 15–27 input 1's items, 28 the quest-item difficulty on every input (table below) `[I]` ([items/0008 § 1](../findings/items/0008-cube.md#1-the-row-filter-cube_transmute-0x005665f0), [items/0008 § 2.3](../findings/items/0008-cube.md#23-the-item-test-in-the-codes-order)) | — | [C] |
| — | — | `+0x005` 3 bytes | padding; 0 in every record | — | [C] |
| `param` | blank in every row | `+0x008` s32 (probe: 1 234 567, −1, 65 537) | condition parameter: a day for op 1, a stat id ([ItemStatCost](ItemStatCost.md) row) for ops 3–26 `[I]` ([items/0008 § 1](../findings/items/0008-cube.md#1-the-row-filter-cube_transmute-0x005665f0)) | — | [C] |
| `value` | blank in every row | `+0x00C` s32 (probe: −7, 70 000, −65 537) | condition value; for the stat ops compared as `value >> ItemStatCost[param].ValShift` (arithmetic) `[I]` ([items/0008 § 1](../findings/items/0008-cube.md#1-the-row-filter-cube_transmute-0x005665f0)) | — | [C] |
| `numinputs` | int 2..7 | `+0x010` u16 | equals the sum over the input cells of `qty` (1 when absent) in all 151 rows; the row filter requires it to equal the number of items in the cube (compared as a byte) `[I]` ([items/0008 § 1](../findings/items/0008-cube.md#1-the-row-filter-cube_transmute-0x005665f0)) | — | [C] |
| `version` | {0} on 55 rows, {100} on 96 | `+0x012` u16 | ≥ 100: the row is skipped in a classic game `[I]` ([items/0008 § 1](../findings/items/0008-cube.md#1-the-row-filter-cube_transmute-0x005665f0)) | — | [C] |

The five `op` 28 rows are the quest and portal recipes: Horadric Staff (0), Khalim's Flail (1), the cow portal (2),
the two Pandemonium portals (148, 149).

`[I]` The `op` values ([items/0008 § 1](../findings/items/0008-cube.md#1-the-row-filter-cube_transmute-0x005665f0), [items/0008 § 2.3](../findings/items/0008-cube.md#23-the-item-test-in-the-codes-order); `v` = `value >> ItemStatCost[param].ValShift`; for ops 3–27 the test
runs only when 0 ≤ `param` ≤ the stat count, otherwise the row passes; a missing ItemStatCost record refuses it):

| `op` | the row (or input) passes when |
|---|---|
| 1 | `param` ≤ day of month ≤ `value` (local time) |
| 2 | `value` = day of week + 1 (Sunday = 1) |
| 3 / 4 / 5 / 6 | player stat `param` ≥ v / ≤ v / ≠ v / = v |
| 7–10, 11–14 | the same on the player's base stat, and on `sub_00625560_UnitStatDelta` |
| 15–18, 19–22, 23–26 | the same on each item input 1 claims (stat, base stat, delta) |
| 27 | input 1's item's unique/set file index ≠ `value` |
| 28 | on every input: an item whose base has both `quest` and `questdiffcheck` needs stat 356 (`questitemdifficulty`) ≥ the game difficulty |
| 0, other | no test |

Op 28 binds Wirt's Leg, the Staff of Kings, the Viper Amulet, the Khalim Flail and Khalim's organs; the
Pandemonium keys and organs have `quest` blank and pass. In Nightmare and Hell a Wirt's Leg needs stat 356 ≥ 1 or 2
for the cow portal row to match ([items/0008 § 2.3](../findings/items/0008-cube.md#23-the-item-test-in-the-codes-order), tbl:Misc.txt:questdiffcheck).

### Input record (`input 1..7` at `+0x014 + 8·(k−1)`, 8 bytes)

| Offset | Size | Field | Filled from the cell | Tag |
|---|---|---|---|---|
| `+0` | u16 | `flags` | bits below | [C] |
| `+2` | u16 | `item` | flag `0x001`: item record index over weapons + armor + misc (`any`: `0xFFFF`); flag `0x002`: item type row index | [C] |
| `+4` | u16 | `id` | a unique or set item named by the cell: its `uniqueitems` / `setitems` record index **+ 1** (0 = none) | [C] |
| `+6` | u8 | `quality` | `low` 1, `nor` 2, `hiq` 3, `mag` 4, `set` 5, `rar` 6, `uni` 7, `crf` 8, `tmp` 9; 0 = any | [C] |
| `+7` | u8 | `qty` | `qty=N` (N truncated to a byte: probe `qty=300` → 44); 0 when absent | [C] |

| Bit | Value | Keyword | Stock cells | Tag |
|---|---|---|---|---|
| 0 | `0x001` | an item code, `any`, or a unique/set name | 319 item, 5 `any`, 2 names | [C] |
| 1 | `0x002` | an item type code | 63 | [C] |
| 2 | `0x004` | `nos` | 7 | [C] |
| 3 | `0x008` | `sock` (also `sock=N`; N is not stored) | 2 | [C] |
| 4 | `0x010` | `eth` | 0 (probe) | [C] |
| 5 | `0x020` | `noe` | 4 | [C] |
| 6 | `0x040` | a unique or set item name (with bit 0) | 2 (*The Stone of Jordan*) | [C] |
| 7 | `0x080` | `upg` | 24 | [C] |
| 8 | `0x100` | `bas` | 4 | [C] |
| 9 | `0x200` | `exc` | 4 | [C] |
| 10 | `0x400` | `eli` | 4 | [C] |
| 11 | `0x800` | `nru` | 0 (probe) | [C] |

`[I]` What each flag requires of a cube item, in the code's order ([items/0008 § 2.3](../findings/items/0008-cube.md#23-the-item-test-in-the-codes-order), fn:CUBE_MatchInput@0x00565010):
the base (`0x001` with `0xFFFF` any item; `0x001` the item's class = `item`; with `upg` the named base or a higher
tier of it, through `normcode`/`ubercode`/`ultracode`; `0x002` `ITEMS_UnitIsType`, so `Equiv` counts); `quality`
≠ 0 must equal the item's; `0x040` the item's unique/set file index = `id` − 1; `nos` stat 194 (`item_numsockets`)
= 0 and `sock` stat 194 ≠ 0 (the socket count, not the filled count); `noe` not ethereal, `eth` ethereal; `bas`,
else `exc`, else `eli`: the item's code is its `normcode` / `ubercode` / `ultracode`; `nru` no runeword flag; then
`op` 28 (above). For input 1 only, when `output` is `useitem`/`usetype` with `sock`, the item must have
`ItemMaxSockets` ≠ 0.

`[I]` **Counting** ([items/0008 § 2.2](../findings/items/0008-cube.md#22-one-input-against-the-cube)): each input, in column order, claims **every** unclaimed matching cube item and
passes when the count equals `qty` (1 when 0), or is at least `qty` once a claimed item has a stackable base. A
stack counts as one item. With `numinputs` = the sum of the `qty`s (every stock row), an extra or unmatched item
refuses the row.

`[I]` An unknown qualifier ends the input parse silently, keeping what the cell had so far ([items/0008 § 2.1](../findings/items/0008-cube.md#21-compiled-input-structcubeinput0x0-8-bytes-at-row-0x14--8k),
fn:sub_00668600_CubeParseInput@0x00668600).

### Output record (`output` at `+0x04C`, `output b` at `+0x0A0`, `output c` at `+0x0F4`, 84 bytes each)

The `b ` and `c ` columns (`b lvl`, `b mod 1`, …) fill the same fields of the second and third record.

| Offset | Size | Field | Filled from | Tag |
|---|---|---|---|---|
| `+0x00` | u16 | `flags` | bits below | [C] |
| `+0x02` | u16 | `item` | kind `0xFC`: item record index (weapons + armor + misc); kind `0xFD`: item type row index; 0 otherwise | [C] |
| `+0x04` | u16 | `id` | a named unique or set item: record index + 1 | [C] |
| `+0x06` | u8 | `quality` | the quality keyword (codes as in the input record); a unique name gives 7, a set item name 5 | [C] |
| `+0x07` | u8 | `qty` | `qty=N` **or** `sock=N`: one byte, the later keyword in the cell wins (probe: `rin,sock=2,qty=3` → 3, `rin,qty=3,sock=2` → 2), while `sock` keeps flag `0x002` once given. `[I]` The builder reads the byte as a socket count when flag `0x002` is set and as a stack quantity otherwise (`test byte [ebx], 2` at 0x0056632A; [items/0008 § 3.2](../findings/items/0008-cube.md#32-compiled-output-structcubeoutput0x00-0x54-bytes)) | [C] |
| `+0x08` | u8 | `kind` | `0xFC` item code or named unique/set, `0xFD` item type, `0xFE` `useitem`, `0xFF` `usetype`; 1 `Cow Portal`, 2 `Pandemonium Portal`, 3 `Pandemonium Finale Portal`; 0 for a cell the compiler can't read | [C] |
| `+0x09` | u8 | `lvl` | `lvl` / `b lvl` / `c lvl` (probe 300 → 44) | [C] |
| `+0x0A` | u8 | `plvl` | `plvl` / … (probe −1 → 255) | [C] |
| `+0x0B` | u8 | `ilvl` | `ilvl` / … (probe 256 → 0); the column is stored even when blank, so it overwrites the unique's or set item's `lvl` that the output parser puts in this byte for a named output (below) | [C] |
| `+0x0C` | 3 × u16 | `pre1..3` | the `pre=N` keywords in order | [C] |
| `+0x12` | 3 × u16 | `suf1..3` | the `suf=N` keywords in order; a fourth `pre=` lands in `suf1` (probe `pre=7,pre=8,pre=9,pre=10` → 7, 8, 9 / 10, 0, 0) | [C] |
| `+0x18` + 12·(m−1) | 12 B | `mod m` (m = 1..5) | `mod m`: s32 [Properties](Properties.md) row index (blank or unknown −1); `mod m param` u16; `mod m min` s16; `mod m max` s16; `mod m chance` u8; 1 byte padding | [C] |

| Bit | Value | Keyword | Stock outputs (all three columns) | Tag |
|---|---|---|---|---|
| 0 | `0x001` | `mod` | 8 | [C] |
| 1 | `0x002` | `sock=N` (N in `qty`) | 1 (row 63, `useitem,sock=1`) | [C] |
| 2 | `0x004` | `eth` | 0 (probe; the sample table's `buc,eth`) | [C] |
| 3 | `0x008` | a unique or set item name | 0 (probe; the sample table's *Angelic Halo*) | [C] |
| 4 | `0x010` | `uns` | 1 (row 141) | [C] |
| 5 | `0x020` | `rem` | 0 (probe) | [C] |
| 6 | `0x040` | `reg` (and `kind` becomes `0xFF`: probe `useitem,reg` → kind `0xFF`) | 0 (probe) | [C] |
| 7 | `0x080` | `exc` | 4 | [C] |
| 8 | `0x100` | `eli` | 4 | [C] |
| 9 | `0x200` | `rep` | 4 | [C] |
| 10 | `0x400` | `rch` | 2 | [C] |

`[I]` **The output ilvl** ([items/0008 § 3.1](../findings/items/0008-cube.md#31-the-ilvl-0x00565b660x00565d12)): `lvl` when non-zero; otherwise `trunc(player level × plvl / 100) +
trunc(input-1 ilvl × ilvl / 100)` (each term only when its column is non-zero), clamped to [1, the `experience`
`MaxLvl` row's class-0 value]. Only created items use it; `useitem` and `mod` outputs keep the input's ilvl.

`[I]` **The output kinds** ([items/0008 § 3.3](../findings/items/0008-cube.md#33-building-one-output), fn:sub_00565AB0_RecipeOutputCreate@0x00565AB0), outputs A, B, C in order:
`0xFC` (a fixed item, or a named unique or set item) and `usetype` (input 1's class, raised by `exc`/`eli` to its
`ubercode`/`ultracode` base) are new items from `ItemCreate` with the forced quality and `pre=`/`suf=`, no socket roll
unless `sock` without a count, no ethereal roll unless `eth`; `0xFD` first draws twice on the game seed to pick a
spawnable item of that type with `level` ≤ the output ilvl; `useitem` copies input 1; `mod` copies input 1 and changes
its class, then re-runs its base stats. **Input 1 feeds all three outputs**, computed from output A's kind and flags
([items/0008 § 2.4](../findings/items/0008-cube.md#24-what-input-1-hands-to-the-outputs)).

`[C]` **A named unique or set output keeps the `ilvl` column, not the item's `lvl`.** The output parser writes the
unique's or set item's `lvl` into byte `+0x0B` ([items/0008 § 3.2](../findings/items/0008-cube.md#32-compiled-output-structcubeoutput0x00-0x54-bytes), fn:CUBEMAIN_OutputTypeParse@0x00668A90), but the
compiled probe rows `The Stone of Jordan` (`lvl` 39), `Harlequin Crest` (69), `Angelic Halo` and `Tal Rasha's
Horadric Crest`, with the `ilvl` column blank, hold 0 there (probe records 219–222): the `ilvl` column, compiled
after the output cell, overwrites the byte. A `.bin` is loaded as compiled, so in the game the byte is the column's
value, a percentage of input 1's ilvl ([run:2026-10-15-cube-saves](../formats/experiments.md#run2026-10-15-cube-saves)).
This answers [items/0008](../findings/items/0008-cube.md)'s open question on the loader column order.

The mod widths are from the probe: `param` 70 000 → 4 464 (u16), `min` −3 → −3, `max` 65 537 → 1, `chance` 300 → 44.
A `param` cell holding a name is **not** looked up: `Holy Freeze` stores 9 013, the digit-by-digit value of
`excel-bin.md`'s integer rule (§ Cell encoding rules), unlike the `names=` columns of [Runes](Runes.md) and
[SetItems](SetItems.md). The stock `mod … param` cells are all numbers (`gethit-skill` 44).

`[I]` **After the item exists** ([items/0008 § 3.4](../findings/items/0008-cube.md#34-after-the-item-exists-in-this-order)), in this order: `uns`/`rem` strip a runeword (`rem` also keeps the
original's socketed children aside); the `mod 1..5` lines with `prop` ≥ 0, each, when `chance` is 1..99, gated by one
LCG step on the output's unit seed (skipped when `low % 100 > chance`, so it applies with probability
(chance + 1)/100), then applied through the property handlers on the item seed (blank `chance` on every stock row: no
chance draw); `rep` (quantity to `qty` for a stackable base, then repair); `rch` (charges refilled); `qty` without
`sock` (quantity); `sock=N` (only on an item with no sockets: `min(ItemMaxSockets, N)`, magic and quality 9 at most
3, set, rare, unique and crafted at most 1, then `ITEMS_SetSockets`' own clamps). If anything was produced, every
cube item is destroyed and the outputs are placed in the cube, identified; otherwise the cube is left as it was
([items/0008 § 3.5](../findings/items/0008-cube.md#35-finishing-the-transmute-0x005664000x00566563)).

## Cell grammar (input and output cells)

`tools/cubemain.py` holds the compiler model (`compile_input`, `compile_output`) that the layout check runs on
every cell, and the survey (`rows`, `summary`). The rules, each checked by the stock diff and the compile probe:

- `[C]` A cell is one comma list, quoted in the `.txt` when it has a comma. Its **first token** is the item; the rest
  are keywords, matched exactly.
- `[C]` **Input head:** an item **type** code is tried first, then an item code, then `any`, then a unique or set item
  name (`uniqueitems` / `setitems` `index`). `axe` and `key` are both a type and an item: as inputs they compile
  as the types (stock rows 11 and 81; the probe's `key`).
- `[C]` **Output head:** `useitem`, `usetype`, then an item **code**, then an item type, then a unique or set item
  name, then the three portal names (the whole cell). As outputs `axe` and `key` compile as the items (probe; the
  sample table's `key`), the opposite order to the inputs.
- `[C]` A named unique or set item stores its base item (`code` / `item` column) in `item`, its record index + 1 in
  `id`, and quality 7 or 5; the input sets flags `0x041`, the output flag `0x008` and kind `0xFC` (*The Stone of
  Jordan* → item 522 `rin`, id 123; *Tal Rasha's Horadric Crest* → item 358, id 81).
- `[C]` In an output, the input-only keywords `nos`, `noe`, `upg`, `bas`, `nru` and a second head `any` change no
  byte. A head the compiler doesn't know (`any` as an output) leaves the record zero, kind 0.
- `[C]` **`useitem,sock` with no `=N` stops the compile:** the game writes no `cubemain.bin` and the session goes no
  further (the probe found it by bisection, step 2 of the run). `sock` alone is fine in an input (`any,sock`).

## Survey of the stock rows

`python3 -I tools/cubemain.py rows workspace/merged/data/global/excel` prints every row with each cell's decoded
form; `summary` gives the counts (gate survey `cubemain`). Every one of the 389 input cells and 151 output cells
decodes with no token left over (`unexplained=0`). Two rows as `rows` prints them:

```
 63 3 perfect skull + 1 rare item + stone of jordan-> add 1 socket to rare  enabled=1 ladder=- version=0 op=- numinputs=5
    in1  "any,rar,nos"                      any/rar/nos flags=0x005 item=-1 id=0 q=rar qty=0
    in2  "skz,qty=3"                        item/qty flags=0x001 item=601 id=0 q=0 qty=3
    in3  The Stone of Jordan                uni name flags=0x041 item=522 id=123 q=uni qty=0
    out  "useitem,sock=1"                   useitem/sock kind=useitem flags=0x002 item=0 id=0 q=0 qty=1 lvl=- plvl=- ilvl=-
 64 magic full helm + jewel + rune 06 + perfect sapphire -> hitpower helm  enabled=1 ladder=- version=100 op=- numinputs=4
    in1  "fhl,mag,upg"                      item/mag/upg flags=0x081 item=309 id=0 q=mag qty=0
    in2  jew                                item flags=0x001 item=643 id=0 q=0 qty=0
    in3  r06                                item flags=0x001 item=615 id=0 q=0 qty=0
    in4  gpb                                item flags=0x001 item=571 id=0 q=0 qty=0
    out  "usetype,crf"                      usetype/crf kind=usetype flags=0x000 item=0 id=0 q=crf qty=0 lvl=- plvl=50 ilvl=50 mods gethit-skill(44)5..4 thorns()3..7 ac-miss()25..50
```

| count | value | rows |
|---|---:|---|
| rows | 151 | 0–150 |
| `enabled` 1 | 146 | not 142–146 (the five quality-9 `tmp` recipes) |
| `ladder` 1 | 21 | rune upgrades 104–122 (`r14` → `r15` and up), the elite upgrades 131–132 |
| `version` 0 / 100 | 55 / 96 | |
| `min diff`, `class`, `param`, `value`, any `mod` chance, `output b`, `output c` | 0 rows | blank everywhere |
| `op` 28 | 5 | 0, 1, 2, 148, 149 |
| input cells | 389 | 151 / 109 / 74 / 52 / 1 / 1 / 1 in `input 1..7`; `numinputs` sums to 532 |
| property lines | 133 | `mod 1..4` (`mod 5` blank) |

Rows by the kind and quality of `output`:

| `output` | rows | examples |
|---|---:|---|
| item code, no quality | 69 | quest items (0, 1), potions, gem / skull / rune upgrades, arrows ↔ bolts, Token of Absolution (150) |
| item code, `mag` / `nor` | 7 / 2 | prismatic amulet (6), the four `rin,mag,pre=…` rings (7–10), rings ↔ amulets (13, 14); throwing axes and javelins (11, 12) |
| item type, `mag` | 1 | `pole,mag,pre=191` (19) |
| `usetype,crf` | 36 | the crafted items, rows 64–99: Hit Power (`gpb`), Blood (`gpr`), Caster (`gpv`), Safety (`gpg`), nine each |
| `usetype,mag` | 6 | the magic rerolls and socket-weapon rows (15–18, 60, 147) |
| `usetype,rar` | 2 | the rare rerolls (61, 62) |
| `usetype,nor` | 2 | low-quality → normal (127, 128) |
| `usetype,tmp` / `useitem,tmp` | 2 / 2 | the disabled quality-9 recipes (142–145) |
| `useitem` | 19 | add sockets (63, 123–126), upgrade to exceptional / elite (129–136), repair and recharge (137–140), unsocket (141), 146 |
| portal | 3 | `Cow Portal` (2), `Pandemonium Portal` (148), `Pandemonium Finale Portal` (149) |

## Compile probe

The column semantics a stock row can't show were read off the compiler, by data only: `python3 -I tools/cubemain.py
probe-txt <excel-dir> <out-dir>` writes the stock rows followed by 81 probe rows (three header rows with every
header column filled, out-of-range values included; one row with `output`, `output b` and `output c` and all their
lvl and mod columns filled with distinct numbers; one row of over-wide mod values and a skill name in a `param`;
one row per input form and keyword; one row per output form and keyword). The game compiled it under
`-direct -txt`, and `excel_bin.py diff` matches all 232 records with the layout above
([run:2026-10-15-cube-saves](../formats/experiments.md#run2026-10-15-cube-saves)). The probe pair is kept as
`workspace/cmp/cubeprobe-excel/cubemain.{txt,bin}` (with links to the stock tables the references need).
These are compiler facts. They say how a cell is stored, not what the transmute does with it.

## Interpretation notes

- **Quantity counts.** `numinputs` is the number of items the recipe takes: the `qty` of each input, 1 when
  absent, summed (all 151 rows). The match counts a stack as one item `[I]` ([items/0008 § 2.2](../findings/items/0008-cube.md#22-one-input-against-the-cube)).
- **Ladder and disabled rows.** The 21 `ladder` rows are the high rune upgrades and the elite upgrades. They are
  **not** refused offline: the filter skips them only when `Game+0x6A` is 0 and the game is not ladder, and single
  player has `Game+0x6A` = 3 `[I]` ([items/0008 § 1](../findings/items/0008-cube.md#1-the-row-filter-cube_transmute-0x005665f0); no ladder transmute logged yet). The five disabled rows are
  unreachable.
- **No class or difficulty limits in the stock data.** The fields exist (and the sample recipes of plan 0005 used
  `class`), but no stock row sets them.
- **Item references.** Input and output `item` index the concatenated weapons + armor + misc rows ([Weapons](Weapons.md));
  types index [ItemTypes](ItemTypes.md) rows; `id` is a [UniqueItems](UniqueItems.md) or [SetItems](SetItems.md)
  record index plus one; `pre`/`suf` are [MagicPrefix](MagicPrefix.md) / [MagicSuffix](MagicSuffix.md) **record index
  + 1**, stored as written and handed to `ItemCreate` as the forced affix ids; the picker takes record `id − 1`.
  So `pre=331` is MagicPrefix record 330 (`Prismatic`, `.txt` data row 331 when the `Expansion` marker is counted),
  `suf=352` `of the Leech`. `[C]` ([items/0008 § 3.2](../findings/items/0008-cube.md#32-compiled-output-structcubeoutput0x00-0x54-bytes), [items/0008 § 3.3](../findings/items/0008-cube.md#33-building-one-output),
  0x00566062–0x00566090, 0x005C16FE–0x005C170A, run:2026-10-15-cube: 12 forced picks took exactly these rows)
- **Special outputs.** `Cow Portal` (kind 1, row 2) opens, through `CUBE_CowPortalOpen`, a permanent portal (object
  60) to level 39, once per game. It needs, in this order: the game's own quest word 4 bit 11 clear; in the player's
  quest record of the current difficulty, word 4 bit 10 clear (the Cow King's credit), and word 40 bit 0 set in an
  expansion game (word 26 bit 0 in classic; word 26 is not tested in expansion); the player in level 1 (the Act I
  town); a free spot near the player. On success it sets the game's word 4 bit 11; on failure the leg and the tome
  stay in the cube. The row's `op` 28 also needs the leg's stat 356 ≥ the difficulty, so in Normal any leg works
  `[I]` ([items/0008 § 5.1](../findings/items/0008-cube.md#51-cow-portal-cube_cowportalopen-ecx-game-edx-player), fn:CUBE_CowPortalOpen@0x00594140; quest words: [save/0002](../findings/save/0002-quest-words.md)).
  The two Pandemonium portals (kinds 2, 3, rows 148–149) are stubs that return 0: their transmute opens nothing and
  leaves the keys in the cube `[C]` ([items/0008 § 5.2](../findings/items/0008-cube.md#52-the-pandemonium-portals), run:2026-10-15-drlg-outdoor).
- **Recipe saves.** `tools/d2s_recipes/` has one recipe per recipe class, each with the inputs of the first
  transmute in the cube and those of several more in the inventory (and stash), including some that should match
  no row: `cuberunes` (rune and gem upgrades, two ladder rows), `cubereroll` (the 3-perfect-gem magic reroll, the
  6-perfect-skull rare reroll, the Stone of Jordan reroll), `cubecraft` (the four crafting families on rings,
  amulets and their gloves), `cubesock` (rows 123–126, 63, 141), `cubeportal` (Wirt's Leg and a Tome of Town
  Portal, the Pandemonium keys and organs, the Token of Absolution parts) and `cubeclassic` (classic rows, and row
  60 to be refused there). Each builds with `tools/d2s.py build` and loads in the game
  ([run:2026-10-15-cube-saves](../formats/experiments.md#run2026-10-15-cube-saves);
  [d2s.md § Cube recipe saves](../formats/d2s.md#cube-recipe-saves)).

## Open questions

- The transmute's use of these fields is read in [items/0008](../findings/items/0008-cube.md) (above; mostly `[I]`
  until plan 0030 Phase 2's run).
- `[L]` Why `useitem,sock` without a count stops the compile. (The head order is the parsers' try order: the input
  parser tries types before item codes, the output parser the reverse `[I]`, [items/0008 § 2.1](../findings/items/0008-cube.md#21-compiled-input-structcubeinput0x0-8-bytes-at-row-0x14--8k), [items/0008 § 3.2](../findings/items/0008-cube.md#32-compiled-output-structcubeoutput0x00-0x54-bytes).)

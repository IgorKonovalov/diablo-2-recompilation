# ItemStatCost (`data/global/excel/itemstatcost.txt` → `itemstatcost.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 359 (no `Expansion` marker)   **Record:** 324 B (`0x144`)
> **sha256:** `.txt` `ee7fa82b48e0c4f27a566334b2da13cf1c83f5c4c0439552084a231cb5938375`, `.bin` `969fa476c0d9c3c4cfa03f99a0abd12e6c15ffee8cb9f70a96e3b85d3600e544`
> **Doc status:** every column located; combat stats listed (plan 0037 Phase 0) and their readers `[I]` (combat/0001, plan 0039 A1); aggregation columns and every `op` row listed (plan 0041 Phase 0); `.bin` layout complete (`+0x05E..+0x13F` has no `.txt` column; its run-time contents `[I]`); semantics `[L]`
> except the save columns, which are `[I]` from [save/0001](../findings/save/0001-d2s-io.md) (plan 0024 Phase 0), and
> `ValShift` and `op` at creation, `[I]` from [items/0006 § 7](../findings/items/0006-properties.md#7-stat-storage-as-far-as-the-save-needs-it) (plan 0024 Phase 1)

## Purpose

One row per **stat**: a numbered value a unit can carry in its stat lists (strength, a resistance, an item
property such as `item_fastercastrate`). The row says how the stat is sent to the client, saved in a `.d2s`
(`Save Bits`, `Save Add`, `Save Param Bits`), derived from other stats (`op`…), and described in a tooltip
(`desc*`, `dgrp*`). The item property roll ([Properties](Properties.md)) writes stats by the row index of this
table. Readers: research-map rows `items/properties` (plan 0024) and `save/d2s`. Leads: no lead; derived from
data, with the save columns from [save/0001](../findings/save/0001-d2s-io.md).

## Row identity

- `[C]` The record index is the data row index (0..358); the `.txt` has no `Expansion` marker.
  `python3 -I tools/excel_bin.py diff … itemstatcost` matches record *i* to data row *i* in every mapped column.
- `[C]` `ID` equals the row index in all 359 rows and is stored at `+0x000` (u16). `Stat` is the row's key
  (359 distinct names) and is **not compiled**: no field holds it. Other tables name a stat by `Stat` and store
  its row index (u16, blank = `0xFFFF`): [Properties](Properties.md) `stat1..7`, this table's `maxstat`,
  `op base` and `op stat1..3`, and the `stat1..3` columns of [Misc](Misc.md)/[Weapons](Weapons.md).
- `[I]` The game addresses a record as `DataTables+0xBCC + 0x144 * id` with the count at `DataTables+0xBD4`;
  `ITEMSTATCOST_GetRecord` returns NULL for an id out of range.
  ([save/0001 § 7](../findings/save/0001-d2s-io.md), fn:ITEMSTATCOST_GetRecord@0x0045C4F0, struct:ItemStatCostRec)
- So the **stat id** that a save, a stat list or a property refers to is the row index here. `[C]` for the
  table side (`ID` = row index in every row, all `stat*` references resolve to row indices); that the game uses the
  same number is `[I]` (the record address above).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel itemstatcost`
decodes all 359 records and matches every mapped cell (359 × 51 = 18 309 cells, 0 mismatches); `excel_bin.py probe`
finds each column at the offset given (alone, or with the width the next field fixes). Observed values come from
`python3 -I tools/prop_survey.py columns … itemstatcost` (decoded `.bin`; *blank* counts the `.txt` cells).
**Meaning:** `[L]`, from the column name, unless the cell says otherwise. Signedness: the cells are ≥ 0 except
`Multiply` (two negative rows) and `Save Add`/`1.09-Save Add` (one `-1` each), so the data fixes the width of a
slot but the sign only for those three; the save columns' widths and signs are where the code reads them
([save/0001 § 7](../findings/save/0001-d2s-io.md)).

| Column | Observed (blank / values) | `.bin` field | Meaning (`[L]` unless tagged) | References | Layout tag |
|---|---|---|---|---|---|
| `Stat` | str, 359 distinct, 0 blank | — (not compiled) | the stat's name | key of every `stat` reference | [C] (absence) |
| `ID` | 0..358, = row index in every row | `+0x000` u16 | stat id | — | [C] |
| `Send Other` | 1 in 14, 345 blank | `+0x004` bit 0 | sent to other clients | — | [C] |
| `Signed` | 1 in 294, 65 blank | `+0x004` bit 1 | value is signed | — | [C] |
| `damagerelated` | 1 in 104, 255 blank | `+0x004` bit 2 | belongs to a damage stat list | — | [C] |
| `itemspecific` | 1 in 6, 353 blank | `+0x004` bit 3 | stat bound to the item | — | [C] |
| `direct` | 1 in 4, 355 blank | `+0x004` bit 4 | changed directly, capped by `maxstat` | — | [C] |
| `UpdateAnimRate` | 1 in 3, 356 blank | `+0x005` bit 1 | change refreshes the animation rate | — | [C] |
| `fMin` | 1 in 7, 352 blank | `+0x005` bit 2 | value floored at `MinAccr` | — | [C] |
| `fCallback` | 1 in 35, 324 blank | `+0x005` bit 3 | change runs a callback | — | [C] |
| `Saved` | 1 in 16, 343 blank | `+0x005` bit 4 | saved in the character stat section | — | [C] |
| `CSvSigned` | 0 or blank in every row (343 blank) | `+0x005` bit 5 (from code) | `[I]` character-stat value read signed (with `CSvBits` < 32) | — | [I] (slot from code) |
| `Send Bits` | 0..32, 21 distinct, 44 blank | `+0x008` u8 | width of the client update value | — | [C] |
| `Send Param Bits` | {0 ×337, 3 ×2, 6 ×1, 8 ×8, 9 ×2, 10 ×3, 16 ×6}, 337 blank | `+0x009` u8 | width of the client update param | — | [C] |
| `CSvBits` | {0 ×343, 7, 8, 10 ×5, 21 ×6, 25 ×2, 32}, 343 blank | `+0x00A` u8 | `[I]` width of the stat in the `.d2s` character-stat section; 0 = not saved there | [d2s § stats](../formats/d2s.md) | [C] |
| `CSvParam` | blank in every row | `+0x00B` u8 (from code) | `[I]` width of its param in that section | — | [I] (slot from code) |
| `Divide` | {0 ×7 (blank), 1024 ×352} | `+0x00C` s32 | cost divisor (vendor price) | — | [C] |
| `Multiply` | −34..4096, 67 distinct, 132 blank | `+0x010` s32 | cost multiplier | — | [C] |
| `Add` | 0..56452, 118 distinct, 174 blank | `+0x014` s32 | cost addend | — | [C] |
| `ValShift` | {0 ×351, 8 ×8}, 351 blank | `+0x018` u8 | `[I]` the stored value is shifted right by it before saving and left after loading (fixed point, `hitpoints`/`mana`/…); the property writer stores `value << ValShift` at creation (fn:PROP_WriteStat@0x0065EA50) | — | [C] |
| `1.09-Save Bits` | 0..30, 14 distinct, 87 blank | `+0x01A` u8 | `[I]` `Save Bits` for saves of version < 93 | — | [C] |
| `1.09-Save Add` | −1..128, 9 distinct, 89 blank | `+0x020` s32 | `[I]` `Save Add` for saves of version < 93 | — | [C] |
| `Save Bits` | 0..24, 15 distinct, 112 blank | `+0x019` u8 | `[I]` width of the value in an item property list; 0 = never written | [d2s § item properties](../formats/d2s.md) | [C] |
| `Save Add` | −1..128, 11 distinct, 120 blank | `+0x01C` s32 | `[I]` bias added before saving, subtracted after loading | — | [C] |
| `Save Param Bits` | {0 ×342, 3 ×2, 8, 9 ×3, 10 ×3, 16 ×8}, 342 blank | `+0x024` u32 | `[I]` width of the param in an item property list | — | [C] |
| `keepzero` | {0 ×357, 1 ×2}, 357 blank | `+0x050` u32 | keep the stat in its list when it reaches 0 | — | [C] |
| `MinAccr` | {0 ×354, 1 ×5}, 352 blank | `+0x02C` u32 | floor used with `fMin` | — | [C] |
| `Encode` | {0 ×304, 1 ×2, 2 ×6, 3 ×10, 4 ×37}, 304 blank | `+0x030` u16 | how value and param are packed (skill-on-event, charges, by-time) | — | [C] |
| `maxstat` | 4 named (`maxhp`, `maxmana`, `maxstamina`, `maxdurability`), 355 blank | `+0x032` u16 stat index, blank `0xFFFF` | stat that caps this one | `itemstatcost` `Stat` | [C] |
| `descpriority` | 0..180, 144 distinct, 152 blank | `+0x034` u16 | tooltip sort order | — | [C] |
| `descfunc` | 0..28, 24 distinct, 152 blank | `+0x036` u8 | tooltip formatter | — | [C] |
| `descval` | {0 ×179, 1 ×140, 2 ×40}, 162 blank | `+0x037` u8 | where the value goes in the tooltip | — | [C] |
| `descstrpos` | 130 distinct keys, 154 blank | `+0x038` u16 string-table key | tooltip text, positive value | `.tbl` key ([tbl.md](../formats/tbl.md)) | [C] |
| `descstrneg` | 130 distinct keys, 154 blank | `+0x03A` u16 string-table key | tooltip text, negative value | `.tbl` key | [C] |
| `descstr2` | 1 distinct key, 323 blank | `+0x03C` u16 string-table key | second tooltip text | `.tbl` key | [C] |
| `dgrp` | {0 ×351, 1 ×4, 2 ×4}, 351 blank | `+0x03E` u16 | tooltip group (all attributes, all resistances) | — | [C] |
| `dgrpfunc` | {0 ×351, 1 ×4, 19 ×4} | `+0x040` u8 | group formatter | — | [C] |
| `dgrpval` | {0 ×355, 1 ×4} | `+0x041` u8 | group value position | — | [C] |
| `dgrpstrpos` | 2 distinct keys, 351 blank | `+0x042` u16 string-table key | group text, positive | `.tbl` key | [C] |
| `dgrpstrneg` | 2 distinct keys, 351 blank | `+0x044` u16 string-table key | group text, negative | `.tbl` key | [C] |
| `dgrpstr2` | blank in every row | `+0x046` u16 string-table key (5382 = blank in every record) | second group text | `.tbl` key | [C] (slot by stride) |
| `itemevent1` | 6 named, 338 blank | `+0x048` u16 `events` row index, blank `0xFFFF` | event that triggers `itemeventfunc1` | `events` `event` | [C] |
| `itemevent2` | 3 named, 348 blank | `+0x04A` u16 `events` row index, blank `0xFFFF` | event that triggers `itemeventfunc2` | `events` `event` | [C] |
| `itemeventfunc1` | 0..31, 19 distinct, 338 blank | `+0x04C` u16 | event handler | — | [C] |
| `itemeventfunc2` | 0..21, 11 distinct, 348 blank | `+0x04E` u16 | event handler | — | [C] |
| `op` | {0 ×275, 1 ×2, 2 ×33, 4 ×2, 5 ×2, 6 ×34, 7 ×2, 8, 9, 11 ×2, 13 ×5} | `+0x054` u8 | how this stat modifies `op stat1..3` | — | [C] |
| `op param` | {0 ×322, 1 ×4, 3 ×33} | `+0x055` u8 | shift or divisor of the op | — | [C] |
| `op base` | `level` ×37, 322 blank | `+0x056` u16 stat index, blank `0xFFFF` | stat the op scales by (character level) | `itemstatcost` `Stat` | [C] |
| `op stat1` | 38 named, 275 blank | `+0x058` u16 stat index, blank `0xFFFF` | first stat the op writes | `itemstatcost` `Stat` | [C] |
| `op stat2` | 3 named, 352 blank | `+0x05A` u16 stat index | second | `itemstatcost` `Stat` | [C] |
| `op stat3` | 2 named, 353 blank | `+0x05C` u16 stat index | third | `itemstatcost` `Stat` | [C] |
| `stuff` | {0 ×358, 6 ×1} | `+0x140` u32 | — | — | [C] |
| `*eol` | end-of-line marker column | — | — | — | — |

`[C]` Every stat reference resolves: `maxstat`, `op base`, `op stat1..3` name rows of this table and `itemevent1/2`
name rows of `events.txt` (`diff` reports 0 mismatches, and a name that resolves nowhere would store `0xFFFF` against
a non-blank cell).

## Record layout

`+0x000` `ID` u16 · `+0x002` u16, 0 in every record · `+0x004` flag byte (bit 0 `Send Other`, 1 `Signed`,
2 `damagerelated`, 3 `itemspecific`, 4 `direct`; bits 5..7 clear in every record) · `+0x005` flag byte
(bit 1 `UpdateAnimRate`, 2 `fMin`, 3 `fCallback`, 4 `Saved`, 5 `CSvSigned`; bits 0, 6, 7 clear in every record) ·
`+0x006` u16, 0 · `+0x008` `Send Bits` · `+0x009` `Send Param Bits` · `+0x00A` `CSvBits` · `+0x00B` `CSvParam` ·
`+0x00C` `Divide` · `+0x010` `Multiply` · `+0x014` `Add` · `+0x018` `ValShift` · `+0x019` `Save Bits` ·
`+0x01A` `1.09-Save Bits` · `+0x01B` u8, 0 · `+0x01C` `Save Add` · `+0x020` `1.09-Save Add` · `+0x024`
`Save Param Bits` · `+0x028` u32, 0 · `+0x02C` `MinAccr` · `+0x030` `Encode` · `+0x032` `maxstat` ·
`+0x034` `descpriority` · `+0x036` `descfunc` · `+0x037` `descval` · `+0x038/3A/3C` `descstrpos/neg/2` ·
`+0x03E` `dgrp` · `+0x040` `dgrpfunc` · `+0x041` `dgrpval` · `+0x042/44/46` `dgrpstrpos/neg/2` ·
`+0x048/4A` `itemevent1/2` · `+0x04C/4E` `itemeventfunc1/2` · `+0x050` `keepzero` · `+0x054` `op` ·
`+0x055` `op param` · `+0x056` `op base` · `+0x058/5A/5C` `op stat1..3` · `+0x05E..+0x13F` (226 B) 0 in every
record, no `.txt` column, filled at run time (below) · `+0x140` `stuff` u32.

- `[C]` The offsets and the zero ranges: `diff` (0 mismatches) and `python3 -I tools/excel_bin.py unknown … itemstatcost`,
  which lists only `+0x002`, `+0x006`, `+0x01B`, `+0x028` and `+0x05E..+0x13F` as uncovered, each 0 in all 359 records.
- `[I]` **The record tail is filled at run time** (items/0006 § 4, read 2026-10-15 from the evaluation code: the reader only). The
  stat-list code reads these fields, which are 0 in every file record:

  | Offset | Type | What the reader does with it |
  |---|---|---|
  | `+0x051` | u8 | non-zero: walk this stat's `op stat1..3` and the list at `+0x05E`; meaning not settled |
  | `+0x052` | u8 | "has op inputs": `StatEvaluate` walks the `+0x0DE` table only when it is set |
  | `+0x05E` | u16[64] | the stats re-evaluated when this one changes (`sub_006266C0_StatRecompute`) |
  | `+0x0DE` | 16 × 6 B | the stats whose `op stat1..3` name this one, each `{u16 op base, u16 source stat, u8 op, u8 op param}`, ending at the first `op` 0 (`sub_00626200_StatEvaluate`) |

  `+0x0DE + 96` = `+0x13E`, so `+0x13E..+0x13F` are 2 bytes no reader was seen to touch. The `+0x0DE` table is the
  inverse of the `op stat1..3` columns: stat 73 `maxdurability` holds the entry for 75
  `item_maxdurability_percent` (`op` 13), which is how `dur%` reaches the evaluated maximum durability. `+0x051` and
  `+0x052` sit inside the u32 the `.bin` layout gives `keepzero` (`+0x050`, values 0 and 1 in the file, so bytes
  `+0x051..+0x053` are 0 in all 359 records); the reader treats them as their own bytes, so `keepzero` is in effect
  the byte `+0x050`. The loader that fills the tail is unread, so all of this is `[I]`.
  (fn:sub_00626200_StatEvaluate@0x00626200, fn:sub_006266C0_StatRecompute@0x006266C0, tbl:ItemStatCost.txt:op,
  [items/0006 § 4](../findings/items/0006-properties.md#4-the-handlers-per-func))
- `[C]` `CSvParam` (blank in every row) and `CSvSigned` (blank or 0) match any always-zero byte, so the data cannot
  place them. `[I]` Their slots are where the save code reads them: `CSvParam` `+0x00B`, `CSvSigned` `+0x005` bit 5
  ([save/0001 § 7](../findings/save/0001-d2s-io.md), 0x0056A4F0). `dgrpstr2` (blank in every row) takes the slot the
  stride of `dgrpstrpos`/`dgrpstrneg` leaves; `+0x046` holds the blank key 5382 in every record, as a blank string
  column does.

### Against `struct:ItemStatCostRec`

`re/types/save.h` `ItemStatCostRec` (from [save/0001](../findings/save/0001-d2s-io.md)) agrees with the layout above
on the record size (`0x144`) and on every save field: `+0x005` bit 5 `CSvSigned`, `+0x00A` `CSvBits`, `+0x00B`
`CSvParam`, `+0x010` `multiply`, `+0x018` `ValShift`, `+0x019` `Save Bits`, `+0x01A` `1.09-Save Bits`, `+0x01C`
`Save Add`, `+0x020` `1.09-Save Add`, `+0x024` `Save Param Bits`. `[C]` `+0x010` is `Multiply` (s32) in all 359
records (`diff`, two of them negative), and the struct now says so (struct:ItemStatCostRec+0x010; it was misnamed
`startSeed` until plan 0024 Phase 1).

## Combat stats (plan 0037 Phase 0)

The stats a combat formula is expected to read, chosen **by their `Stat` names** (`[L]`: which stats the attack code
really reads is plan 0037 Phase 1). For each: its id (the row index, § Row identity), where its record starts in
`itemstatcost.bin` (`4 + 0x144·id`), and the fields of that record that say how the value is stored. The values are
`python3 -I tools/combat_survey.py isc workspace/merged/data/global/excel` (gate survey `combat`), decoded from the
`.bin`; the field offsets are § Columns (`[C]`, `excel_bin.py diff`, 18 309 cells, 0 mismatches): `Signed`
`+0x004` bit 1, `damagerelated` `+0x004` bit 2, `ValShift` `+0x018` u8, `Save Bits` `+0x019` u8, `Save Add` `+0x01C`
s32, `Save Param Bits` `+0x024` u32, `op` `+0x054` u8. (tbl:ItemStatCost.txt:ValShift, tbl:ItemStatCost.txt:Signed)

| Group | id | `Stat` | record at | `ValShift` | `Signed` | `Save Bits` | `Save Add` | `Save Param Bits` | `damagerelated` | `op` |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| attacker | 12 | `level` | `0x00F34` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| attacker | 0 | `strength` | `0x00004` | 0 | 0 | 8 | 32 | 0 | 0 | 0 |
| attacker | 2 | `dexterity` | `0x0028C` | 0 | 0 | 7 | 32 | 0 | 0 | 0 |
| attack rating | 19 | `tohit` | `0x01810` | 0 | 1 | 10 | 0 | 0 | 1 | 0 |
| attack rating | 119 | `item_tohit_percent` | `0x096A0` | 0 | 1 | 9 | 20 | 0 | 1 | 0 |
| attack rating | 115 | `item_ignoretargetac` | `0x09190` | 0 | 1 | 1 | 0 | 0 | 1 | 0 |
| attack rating | 116 | `item_fractionaltargetac` | `0x092D4` | 0 | 1 | 7 | 0 | 0 | 1 | 0 |
| attack rating | 123 | `item_demon_tohit` | `0x09BB0` | 0 | 1 | 10 | 128 | 0 | 1 | 0 |
| attack rating | 124 | `item_undead_tohit` | `0x09CF4` | 0 | 1 | 10 | 128 | 0 | 1 | 0 |
| attack rating | 179 | `attack_vs_montype` | `0x0E290` | 0 | 0 | 9 | 0 | 10 | 1 | 0 |
| defence | 31 | `armorclass` | `0x02740` | 0 | 1 | 11 | 10 | 0 | 0 | 0 |
| defence | 32 | `armorclass_vs_missile` | `0x02884` | 0 | 1 | 9 | 0 | 0 | 0 | 0 |
| defence | 33 | `armorclass_vs_hth` | `0x029C8` | 0 | 1 | 8 | 0 | 0 | 0 | 0 |
| defence | 16 | `item_armor_percent` | `0x01444` | 0 | 1 | 9 | 0 | 0 | 0 | 13 |
| block | 20 | `toblock` | `0x01954` | 0 | 1 | 6 | 0 | 0 | 0 | 0 |
| damage | 21 | `mindamage` | `0x01A98` | 0 | 1 | 6 | 0 | 0 | 1 | 0 |
| damage | 22 | `maxdamage` | `0x01BDC` | 0 | 1 | 7 | 0 | 0 | 1 | 0 |
| damage | 23 | `secondary_mindamage` | `0x01D20` | 0 | 1 | 6 | 0 | 0 | 1 | 0 |
| damage | 24 | `secondary_maxdamage` | `0x01E64` | 0 | 1 | 7 | 0 | 0 | 1 | 0 |
| damage | 159 | `item_throw_mindamage` | `0x0C940` | 0 | 1 | 6 | 0 | 0 | 1 | 0 |
| damage | 160 | `item_throw_maxdamage` | `0x0CA84` | 0 | 1 | 7 | 0 | 0 | 1 | 0 |
| damage | 25 | `damagepercent` | `0x01FA8` | 0 | 1 | 8 | 0 | 0 | 1 | 0 |
| damage | 18 | `item_mindamage_percent` | `0x016CC` | 0 | 1 | 9 | 0 | 0 | 1 | 13 |
| damage | 17 | `item_maxdamage_percent` | `0x01588` | 0 | 1 | 9 | 0 | 0 | 1 | 13 |
| damage | 111 | `item_normaldamage` | `0x08C80` | 0 | 1 | 9 | 20 | 0 | 1 | 0 |
| damage | 121 | `item_demondamage_percent` | `0x09928` | 0 | 1 | 9 | 20 | 0 | 1 | 0 |
| damage | 122 | `item_undeaddamage_percent` | `0x09A6C` | 0 | 1 | 9 | 20 | 0 | 1 | 0 |
| damage | 180 | `damage_vs_montype` | `0x0E3D4` | 0 | 0 | 9 | 0 | 10 | 1 | 0 |
| damage | 137 | `item_kickdamage` | `0x0AD68` | 0 | 1 | 7 | 0 | 0 | 0 | 0 |
| fire | 48 | `firemindam` | `0x03CC4` | 0 | 1 | 8 | 0 | 0 | 1 | 0 |
| fire | 49 | `firemaxdam` | `0x03E08` | 0 | 1 | 9 | 0 | 0 | 1 | 0 |
| fire | 315 | `firelength` | `0x18EB0` | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| fire | 316 | `burningmin` | `0x18FF4` | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| fire | 317 | `burningmax` | `0x19138` | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| lightning | 50 | `lightmindam` | `0x03F4C` | 0 | 1 | 6 | 0 | 0 | 1 | 0 |
| lightning | 51 | `lightmaxdam` | `0x04090` | 0 | 1 | 10 | 0 | 0 | 1 | 0 |
| magic | 52 | `magicmindam` | `0x041D4` | 0 | 1 | 8 | 0 | 0 | 1 | 0 |
| magic | 53 | `magicmaxdam` | `0x04318` | 0 | 1 | 9 | 0 | 0 | 1 | 0 |
| cold | 54 | `coldmindam` | `0x0445C` | 0 | 1 | 8 | 0 | 0 | 1 | 0 |
| cold | 55 | `coldmaxdam` | `0x045A0` | 0 | 1 | 9 | 0 | 0 | 1 | 0 |
| cold | 56 | `coldlength` | `0x046E4` | 0 | 1 | 8 | 0 | 0 | 1 | 0 |
| poison | 57 | `poisonmindam` | `0x04828` | 0 | 1 | 10 | 0 | 0 | 1 | 0 |
| poison | 58 | `poisonmaxdam` | `0x0496C` | 0 | 1 | 10 | 0 | 0 | 1 | 0 |
| poison | 59 | `poisonlength` | `0x04AB0` | 0 | 1 | 9 | 0 | 0 | 1 | 0 |
| poison | 326 | `poison_count` | `0x19C9C` | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| leech | 60 | `lifedrainmindam` | `0x04BF4` | 0 | 1 | 7 | 0 | 0 | 1 | 0 |
| leech | 61 | `lifedrainmaxdam` | `0x04D38` | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| leech | 62 | `manadrainmindam` | `0x04E7C` | 0 | 1 | 7 | 0 | 0 | 1 | 0 |
| leech | 63 | `manadrainmaxdam` | `0x04FC0` | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| leech | 64 | `stamdrainmindam` | `0x05104` | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| leech | 65 | `stamdrainmaxdam` | `0x05248` | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| other on-hit | 66 | `stunlength` | `0x0538C` | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| other on-hit | 136 | `item_crushingblow` | `0x0AC24` | 0 | 1 | 7 | 0 | 0 | 1 | 0 |
| other on-hit | 141 | `item_deadlystrike` | `0x0B278` | 0 | 1 | 7 | 0 | 0 | 1 | 0 |
| other on-hit | 135 | `item_openwounds` | `0x0AAE0` | 0 | 1 | 7 | 0 | 0 | 1 | 0 |
| other on-hit | 134 | `item_freeze` | `0x0A99C` | 0 | 1 | 5 | 0 | 0 | 1 | 0 |
| other on-hit | 150 | `item_slow` | `0x0BDDC` | 0 | 1 | 7 | 0 | 0 | 1 | 0 |
| other on-hit | 117 | `item_preventheal` | `0x09418` | 0 | 1 | 7 | 0 | 0 | 1 | 0 |
| other on-hit | 156 | `item_pierce` | `0x0C574` | 0 | 1 | 7 | 0 | 0 | 1 | 0 |
| other on-hit | 81 | `item_knockback` | `0x06688` | 0 | 1 | 7 | 0 | 0 | 1 | 0 |
| other on-hit | 114 | `item_damagetomana` | `0x0904C` | 0 | 1 | 6 | 0 | 0 | 0 | 0 |
| other on-hit | 118 | `item_halffreezeduration` | `0x0955C` | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| other on-hit | 153 | `item_cannotbefrozen` | `0x0C1A8` | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| other on-hit | 110 | `item_poisonlengthresist` | `0x08B3C` | 0 | 1 | 8 | 20 | 0 | 0 | 0 |
| other on-hit | 337 | `passive_critical_strike` | `0x1AA88` | 0 | 1 | 8 | 0 | 0 | 0 | 0 |
| resistance | 36 | `damageresist` | `0x02D94` | 0 | 1 | 8 | 0 | 0 | 0 | 0 |
| resistance | 37 | `magicresist` | `0x02ED8` | 0 | 1 | 8 | 0 | 0 | 0 | 0 |
| resistance | 39 | `fireresist` | `0x03160` | 0 | 1 | 8 | 50 | 0 | 0 | 0 |
| resistance | 41 | `lightresist` | `0x033E8` | 0 | 1 | 8 | 50 | 0 | 0 | 0 |
| resistance | 43 | `coldresist` | `0x03670` | 0 | 1 | 8 | 50 | 0 | 0 | 0 |
| resistance | 45 | `poisonresist` | `0x038F8` | 0 | 1 | 8 | 50 | 0 | 0 | 0 |
| max resistance | 38 | `maxmagicresist` | `0x0301C` | 0 | 1 | 5 | 0 | 0 | 0 | 0 |
| max resistance | 40 | `maxfireresist` | `0x032A4` | 0 | 1 | 5 | 0 | 0 | 0 | 0 |
| max resistance | 42 | `maxlightresist` | `0x0352C` | 0 | 1 | 5 | 0 | 0 | 0 | 0 |
| max resistance | 44 | `maxcoldresist` | `0x037B4` | 0 | 1 | 5 | 0 | 0 | 0 | 0 |
| max resistance | 46 | `maxpoisonresist` | `0x03A3C` | 0 | 1 | 5 | 0 | 0 | 0 | 0 |
| damage reduction | 34 | `normal_damage_reduction` | `0x02B0C` | 0 | 1 | 6 | 0 | 0 | 0 | 0 |
| damage reduction | 35 | `magic_damage_reduction` | `0x02C50` | 0 | 1 | 6 | 0 | 0 | 0 | 0 |
| absorb | 142 | `item_absorbfire_percent` | `0x0B3BC` | 0 | 1 | 7 | 0 | 0 | 0 | 0 |
| absorb | 143 | `item_absorbfire` | `0x0B500` | 0 | 1 | 7 | 0 | 0 | 0 | 0 |
| absorb | 144 | `item_absorblight_percent` | `0x0B644` | 0 | 1 | 7 | 0 | 0 | 0 | 0 |
| absorb | 145 | `item_absorblight` | `0x0B788` | 0 | 1 | 7 | 0 | 0 | 0 | 0 |
| absorb | 146 | `item_absorbmagic_percent` | `0x0B8CC` | 0 | 1 | 7 | 0 | 0 | 0 | 0 |
| absorb | 147 | `item_absorbmagic` | `0x0BA10` | 0 | 1 | 7 | 0 | 0 | 0 | 0 |
| absorb | 148 | `item_absorbcold_percent` | `0x0BB54` | 0 | 1 | 7 | 0 | 0 | 0 | 0 |
| absorb | 149 | `item_absorbcold` | `0x0BC98` | 0 | 1 | 7 | 0 | 0 | 0 | 0 |
| enemy resistance | 305 | `item_pierce_cold` | `0x18208` | 0 | 1 | 8 | 50 | 0 | 0 | 0 |
| enemy resistance | 306 | `item_pierce_fire` | `0x1834C` | 0 | 1 | 8 | 50 | 0 | 0 | 0 |
| enemy resistance | 307 | `item_pierce_ltng` | `0x18490` | 0 | 1 | 8 | 50 | 0 | 0 | 0 |
| enemy resistance | 308 | `item_pierce_pois` | `0x185D4` | 0 | 1 | 8 | 50 | 0 | 0 | 0 |
| enemy resistance | 333 | `passive_fire_pierce` | `0x1A578` | 0 | 1 | 8 | 0 | 0 | 0 | 0 |
| enemy resistance | 334 | `passive_ltng_pierce` | `0x1A6BC` | 0 | 1 | 8 | 0 | 0 | 0 | 0 |
| enemy resistance | 335 | `passive_cold_pierce` | `0x1A800` | 0 | 1 | 8 | 0 | 0 | 0 | 0 |
| enemy resistance | 336 | `passive_pois_pierce` | `0x1A944` | 0 | 1 | 8 | 0 | 0 | 0 | 0 |
| enemy resistance | 358 | `passive_mag_pierce` | `0x1C51C` | 0 | 1 | 8 | 0 | 0 | 0 | 0 |
| life | 6 | `hitpoints` | `0x0079C` | 8 | 0 | 0 | 0 | 0 | 0 | 0 |
| life | 7 | `maxhp` | `0x008E0` | 8 | 0 | 9 | 32 | 0 | 0 | 0 |
| life | 8 | `mana` | `0x00A24` | 8 | 0 | 0 | 0 | 0 | 0 | 0 |
| life | 9 | `maxmana` | `0x00B68` | 8 | 0 | 8 | 32 | 0 | 0 | 0 |
| life | 10 | `stamina` | `0x00CAC` | 8 | 0 | 0 | 0 | 0 | 0 | 0 |
| life | 74 | `hpregen` | `0x05DAC` | 0 | 0 | 6 | 30 | 0 | 0 | 0 |
| avoidance | 338 | `passive_dodge` | `0x1ABCC` | 0 | 1 | 7 | 0 | 0 | 0 | 0 |
| avoidance | 339 | `passive_avoid` | `0x1AD10` | 0 | 1 | 7 | 0 | 0 | 0 | 0 |
| avoidance | 340 | `passive_evade` | `0x1AE54` | 0 | 1 | 7 | 0 | 0 | 0 | 0 |

- `[C]` 104 stats, all present: 92 have `Signed` 1, 5 have `ValShift` 8 (`hitpoints`, `maxhp`, `mana`, `maxmana`,
  `stamina`: the 1/256 fixed-point stats), 91 have `Save Bits` > 0 and 48 have `damagerelated` 1 (the attack-rating, damage
  and element-damage stats except `item_kickdamage`, `firelength`, `burningmin` and `burningmax`, the leech stats and
  the on-hit stats down to `item_knockback`; none of the defence, block, resistance, damage-reduction, absorb,
  enemy-resistance, life or avoidance stats). Only
  `attack_vs_montype` and `damage_vs_montype` carry a param (`Save Param Bits` 10). (tbl:ItemStatCost.txt:damagerelated)
- `[C]` `item_armor_percent`, `item_maxdamage_percent` and `item_mindamage_percent` have `op` 13; their `op stat1..3`
  name the stats they scale (§ Columns). (tbl:ItemStatCost.txt:op)
- `[C]` 13 have `Save Bits` 0: `level`, `hitpoints`, `mana`, `stamina`, `lifedrainmaxdam`, `manadrainmaxdam`,
  `stamdrainmindam`, `stamdrainmaxdam`, `firelength`, `burningmin`, `burningmax`, `poison_count` and `stunlength`, so
  no item property list in a save carries them. `[I]` A stat with `Save Bits` 0 is never written to a save
  ([§ Interpretation notes](#interpretation-notes), save/0001 § 7–8). (tbl:ItemStatCost.txt:Save Bits)
- `[L]` The group names are readings of the `Stat` names (`lifedrainmindam` is life leech in percent,
  `damageresist` is damage reduction in percent, `magicresist` magic resistance, `item_pierce` "piercing attack",
  `item_pierce_*` and `passive_*_pierce` the enemy-resistance reductions). `[I]` `ValShift` 8 means the stored value is
  the shown value `<< 8` (§ Columns, fn:PROP_WriteStat@0x0065EA50); that `hitpoints` is the life a hit lowers is
  [monsters/0004](../findings/monsters/0004-stats.md#2-monstatsinit-in-order) (stats 7 and 6 = `hp << 8`).

### Combat readers (plan 0037 Phase 1, plan 0039 A1)

From [combat/0001 § 12b (e)](../findings/combat/0001-formulas.md#12b-answers-to-the-archivists-phase-0-questions-backlog-2026-10-16-ae) and the
sections it points to (static reading). This replaces the "by their `Stat` names" choice above for the stats read;
the group names stay readings of the names.

- `[I]` **The stats the combat formulas read**, by id (reader in brackets): 0, 2, 12 (to-hit, build, open wounds);
  16, 31, 171, 182 (defence, `UNIT_GetDefense`); 17, 18, 21–25, 111 (physical roll); 19, 115, 116, 119, 123, 124, 179,
  325 (to-hit and its target modifiers); 20 (block); 32, 33 (defence against missile and melee); 34, 35 (flat DR and
  MDR); 36–46, 110, 333–336 (resistances, maxima, pierce); 48–59, 101, 326, 329–332, 357 (element damage, lengths,
  masteries); 60–66, 103, 104, 106 (steal, stun, the DR/MDR/absorb bypass flags); 74 (the poison and open-wounds
  bleed); 100 (crushing blow's `PlayerHpPct` input); 118, 153 (half freeze, cannot be frozen); 120, 121, 122, 180
  (build bonuses); 134, 135, 136, 141, 337 (on-hit chances); 142–149 (absorb); 315 (burn length); 327 (missile DR
  scaling); 338, 339, 340, 348 (dodge, avoid, evade, weapon block). Also, outside that list: 6–10 (life, mana and
  stamina at delivery and in the leech caps, § 8–9), 117 (`sub_0057D810_PreventHealHook` on a hit), and 316/317,
  which `MonAttackStats` writes for an `El<e>` `burn`. (fn:COMBAT_BuildDamage@0x0057B7D0, fn:COMBAT_ToHitRoll@0x0057D9B0,
  fn:COMBAT_DefenceRoll@0x0057DFB0, fn:COMBAT_ApplyReductions@0x0057C1E0, fn:COMBAT_ApplyDamage@0x0057C6C0,
  fn:UNIT_GetDefense@0x006223F0, fn:sub_0057D810_PreventHealHook@0x0057D810, tbl:ItemStatCost.txt:Stat)
- `[I]` **Pierce is 333–336**: `COMBAT_ResistFor` subtracts the attacker's `passive_fire_pierce`,
  `passive_ltng_pierce`, `passive_cold_pierce` and `passive_pois_pierce` (also for the cold and freeze lengths and
  for the poison length row). The magic row has no pierce stat, so `passive_mag_pierce` (358) is not read there, and
  `item_pierce_cold`/`fire`/`ltng`/`pois` (305–308) are not read by these formulas.
  ([combat/0001 § 7](../findings/combat/0001-formulas.md#7-reductions-combat_applyreductions), fn:COMBAT_ResistFor@0x0057BE00, data:g_DamageResistTable@0x00732980)
- Scope note, not a claim (architect review, plan 0039 Phase 0): of the 104 stats listed above, combat/0001 reads none of these: 81 `item_knockback`, 114
  `item_damagetomana`, 137 `item_kickdamage`, 150 `item_slow`, 156 `item_pierce`, 159/160 `item_throw_*damage`,
  305–308 and 358. The stat-event handlers other than 14–16 (knockback 7, damage to mana 13, slow 19, …) are outside
  combat/0001's scope, so this is "not read", not "no reader".
- `[I]` **`itemeventfunc` 14, 15, 16** are the handlers `STATEVENT_Freeze`, `STATEVENT_OpenWounds` and
  `STATEVENT_CrushingBlow` of `g_StatEventFuncs`, registered by stats 134 `item_freeze`, 135 `item_openwounds` and 136
  `item_crushingblow` on the events `domeleedamage` (5) and `domissiledamage` (6). The data agrees: these three rows
  are the only ones with funcs 14–16, each in both slots with `itemevent1` `domeleedamage` and `itemevent2`
  `domissiledamage`. (data:g_StatEventFuncs@0x007325B0, fn:sub_0056E740_AddStatEvent@0x0056E740,
  fn:STATEVENT_Freeze@0x005BFC60, fn:STATEVENT_OpenWounds@0x005BFE60, fn:STATEVENT_CrushingBlow@0x005BFFC0,
  tbl:ItemStatCost.txt:itemeventfunc1)
- `[C]` Crushing blow (136) and open wounds (135) through their handlers: one draw on the attacker's seed each,
  reproduced in run:2026-10-16-combat (combat/0001 § 15). (fn:STATEVENT_CrushingBlow@0x005BFFC0,
  fn:STATEVENT_OpenWounds@0x005BFE60, run:2026-10-16-combat)

## Aggregation (plan 0041 Phase 0)

The columns the stat-list code is expected to read when it sums a unit's lists and derives one stat from another
(plan 0041 Phase 1 reads that code). Offsets and widths are § Columns (`[C]`, `excel_bin.py diff`, 18 309 cells,
0 mismatches); the counts are `python3 -I tools/stats_survey.py isc workspace/merged/data/global/excel` (gate survey
`stats`), decoded from the `.bin`, `[C]` as data. **Meanings are `[L]`** (the column names), except where a line cites
the evaluation code of [items/0006 § 4](../findings/items/0006-properties.md#4-the-handlers-per-func).
(tbl:ItemStatCost.txt:op, tbl:ItemStatCost.txt:direct)

| Column | `.bin` field | Values (359 records) | Survey key | Meaning (`[L]`) |
|---|---|---|---|---|
| `op` | `+0x054` u8 | 0 ×275; 1 ×2, 2 ×33, 4 ×2, 5 ×2, 6 ×34, 7 ×2, 8 ×1, 9 ×1, 11 ×2, 13 ×5 (84 rows) | `op_rows`, `op1`…`op13` | how this stat changes its targets |
| `op param` | `+0x055` u8 | 0 ×322, 1 ×4, 3 ×33; non-zero only on rows with an `op` | `op_param_rows`, `op_param_without_op` = 0 | shift or divisor of the op |
| `op base` | `+0x056` u16 stat index, blank `0xFFFF` | `level` ×37, blank ×322; only on rows with an `op` | `op_base_rows`, `op_base_without_op` = 0 | stat the op multiplies by |
| `op stat1..3` | `+0x058`, `+0x05A`, `+0x05C` u16 stat index, blank `0xFFFF` | 84 / 7 / 6 rows set (38 / 3 / 2 distinct stats): 97 target cells, 42 distinct targets; every `op` row names at least one, no row without `op` names one | `op_target_cells`, `op_targets_distinct`, `op_rows_no_target` = 0, `op_target_without_op` = 0 | the stats the op writes |
| `direct` | `+0x004` bit 4 | 4 rows: 6 `hitpoints`, 8 `mana`, 10 `stamina`, 72 `durability` | `isc_direct` | a current value capped by `maxstat` |
| `maxstat` | `+0x032` u16 stat index, blank `0xFFFF` | 4 rows, the `direct` ones: 6 → 7 `maxhp`, 8 → 9 `maxmana`, 10 → 11 `maxstamina`, 72 → 73 `maxdurability` | `isc_maxstat`, `isc_maxstat_and_direct` = 4 | the cap of a `direct` stat |
| `itemspecific` | `+0x004` bit 3 | 6 rows: 70 `quantity`, 71 `value`, 72 `durability`, 73 `maxdurability`, 194 `item_numsockets`, 324 `item_extra_charges` | `isc_itemspecific` | kept on the item, not added to the owner |
| `damagerelated` | `+0x004` bit 2 | 104 rows: ids 17–19, 21–25, 48–66, 68, 70, 81, 93, 108, 111–113, 115–117, 119–124, 134–136, 140–141, 150, 154–156, 159–160, 179–180, 195–196, 198, 218–219, 224–229, 243–250, 256–261, 272–273, 278–283, 296–303, 309–312, 324, 326 | `isc_damagerelated` | belongs to the weapon's own damage list |
| `keepzero` | `+0x050` (u32 in the layout; the evaluation code reads the byte, § Record layout) | 2 rows: 8 `mana`, 10 `stamina` | `isc_keepzero` | the stat stays in its list at 0 |
| `fCallback` | `+0x005` bit 3 | 35 rows (below) | `isc_fcallback`; `isc_fcallback_with_event` = 21 | a change runs a callback |
| `fMin` | `+0x005` bit 2 | 7 rows: 0 `strength`, 1 `energy`, 2 `dexterity`, 3 `vitality`, 7 `maxhp`, 9 `maxmana`, 11 `maxstamina` | `isc_fmin` | the value is floored |
| `MinAccr` | `+0x02C` u32 | 1 on 5 rows (0–3, 7), all with `fMin`; 0 on 9 `maxmana` and 11 `maxstamina` | `isc_minaccr`, `isc_minaccr_without_fmin` = 0 | the floor `fMin` uses |
| `UpdateAnimRate` | `+0x005` bit 1 | 3 rows: 67 `velocitypercent`, 68 `attackrate`, 69 `other_animrate` | `isc_updateanimrate` | a change refreshes the unit's animation rate |

- `[C]` The `fCallback` rows: 7, 9, 11 (the maxima), 78, 81, 83, 86, 89, 90, 97, 98 `state`, 107, 108, 112–114, 126–128,
  134–136, 138, 139, 150, 151 `item_aura`, 155, 188, 195–199, 201, 204. 21 of them also name an `itemevent1`.
  (tbl:ItemStatCost.txt:fCallback)
- `[C]` `op param` and `op base` appear only together with an `op`, and the 37 `op base` rows are the `op` 2, 4 and 5
  rows (all `…_perlevel`); `op param` is 3 on 33 of them and 1 on the four to-hit rows (224, 225, 245, 246).
- `[I]` What the evaluation code is known to read (items/0006 § 4, the reader only, read for creation): the record
  tail `+0x0DE` holds, for a target stat, up to 16 entries `{op base, source stat, op, op param}`, the inverse of
  the `op stat1..3` columns, and `sub_00626200_StatEvaluate` walks it. By the data the inverse has 42 targets and at
  most **5** sources on one target (`op_fanin_max`; 11 `maxstamina`, 22 `maxdamage` and 31 `armorclass`), so no stock target
  overflows 16. (fn:sub_00626200_StatEvaluate@0x00626200, tbl:ItemStatCost.txt:op stat1)
- `[C]` Two targets carry an `op` of their own, so a derivation can chain: 1 `energy` (targets of 222 and 276, and
  itself `op` 8 → `maxmana`) and 3 `vitality` (targets of 223 and 277, itself `op` 9 → `maxhp`, `maxstamina`)
  (`op_target_has_op` = 2). No row names itself (`op_self_target` = 0).
- `[C]` **Rows whose targets do not follow their name** (as data; whether the code honours the cells is Phase 1):
  273 `item_maxdamage_percent_bytime` names `maxdamage`, `secondary_mindamage`, `item_throw_mindamage` (its
  per-level twin 219 names the three maxima); 237 `item_absorb_pois_perlevel` and 291 `item_absorb_pois_bytime` name
  `item_absorbmagic`.
- `[L]` The `op` numbers by the rows that use them: 1 (`skill_staminapercent`, `skill_passive_staminapercent` →
  `maxstamina`) and 11 (`item_maxhp_percent`, `item_maxmana_percent`) read as percentages of a target; 2, 4, 5 as
  per-level terms (`op base` `level`, `op param` a shift); 6 and 7 as by-time terms (the `Encode` 4 stats); 8 and 9
  as the attribute-to-maximum terms (`energy` → mana, `vitality` → life and stamina); 13 as a percentage of an
  item's own base (`item_armor_percent`, `item_maxdamage_percent`, `dur%`, `item_levelreqpct`). The arithmetic of
  each is plan 0041 Phase 1.

### Rows with an `op`

Every row with `op` ≠ 0 (`op_rows` = 84), from `stats_survey.py isc`. `[C]` as data (tbl:ItemStatCost.txt:op base).

| id | `Stat` | `op` | `op param` | `op base` | `op stat1..3` |
|---:|---|---:|---:|---|---|
| 1 | `energy` | 8 | 0 | — | `maxmana` |
| 3 | `vitality` | 9 | 0 | — | `maxhp`, `maxstamina` |
| 16 | `item_armor_percent` | 13 | 0 | — | `armorclass` |
| 17 | `item_maxdamage_percent` | 13 | 0 | — | `maxdamage`, `secondary_maxdamage`, `item_throw_maxdamage` |
| 18 | `item_mindamage_percent` | 13 | 0 | — | `mindamage`, `secondary_mindamage`, `item_throw_mindamage` |
| 75 | `item_maxdurability_percent` | 13 | 0 | — | `maxdurability` |
| 76 | `item_maxhp_percent` | 11 | 0 | — | `maxhp` |
| 77 | `item_maxmana_percent` | 11 | 0 | — | `maxmana` |
| 94 | `item_levelreqpct` | 13 | 0 | — | `item_levelreq` |
| 162 | `skill_staminapercent` | 1 | 0 | — | `maxstamina` |
| 163 | `skill_passive_staminapercent` | 1 | 0 | — | `maxstamina` |
| 214 | `item_armor_perlevel` | 4 | 3 | `level` | `armorclass` |
| 215 | `item_armorpercent_perlevel` | 5 | 3 | `level` | `armorclass` |
| 216 | `item_hp_perlevel` | 2 | 3 | `level` | `maxhp` |
| 217 | `item_mana_perlevel` | 2 | 3 | `level` | `maxmana` |
| 218 | `item_maxdamage_perlevel` | 4 | 3 | `level` | `maxdamage`, `secondary_maxdamage`, `item_throw_maxdamage` |
| 219 | `item_maxdamage_percent_perlevel` | 5 | 3 | `level` | `maxdamage`, `secondary_maxdamage`, `item_throw_maxdamage` |
| 220 | `item_strength_perlevel` | 2 | 3 | `level` | `strength` |
| 221 | `item_dexterity_perlevel` | 2 | 3 | `level` | `dexterity` |
| 222 | `item_energy_perlevel` | 2 | 3 | `level` | `energy` |
| 223 | `item_vitality_perlevel` | 2 | 3 | `level` | `vitality` |
| 224 | `item_tohit_perlevel` | 2 | 1 | `level` | `tohit` |
| 225 | `item_tohitpercent_perlevel` | 2 | 1 | `level` | `item_tohit_percent` |
| 226 | `item_cold_damagemax_perlevel` | 2 | 3 | `level` | `coldmaxdam` |
| 227 | `item_fire_damagemax_perlevel` | 2 | 3 | `level` | `firemaxdam` |
| 228 | `item_ltng_damagemax_perlevel` | 2 | 3 | `level` | `lightmaxdam` |
| 229 | `item_pois_damagemax_perlevel` | 2 | 3 | `level` | `poisonmaxdam` |
| 230 | `item_resist_cold_perlevel` | 2 | 3 | `level` | `coldresist` |
| 231 | `item_resist_fire_perlevel` | 2 | 3 | `level` | `fireresist` |
| 232 | `item_resist_ltng_perlevel` | 2 | 3 | `level` | `lightresist` |
| 233 | `item_resist_pois_perlevel` | 2 | 3 | `level` | `poisonresist` |
| 234 | `item_absorb_cold_perlevel` | 2 | 3 | `level` | `item_absorbcold` |
| 235 | `item_absorb_fire_perlevel` | 2 | 3 | `level` | `item_absorbfire` |
| 236 | `item_absorb_ltng_perlevel` | 2 | 3 | `level` | `item_absorblight` |
| 237 | `item_absorb_pois_perlevel` | 2 | 3 | `level` | `item_absorbmagic` |
| 238 | `item_thorns_perlevel` | 2 | 3 | `level` | `item_attackertakesdamage` |
| 239 | `item_find_gold_perlevel` | 2 | 3 | `level` | `item_goldbonus` |
| 240 | `item_find_magic_perlevel` | 2 | 3 | `level` | `item_magicbonus` |
| 241 | `item_regenstamina_perlevel` | 2 | 3 | `level` | `staminarecoverybonus` |
| 242 | `item_stamina_perlevel` | 2 | 3 | `level` | `maxstamina` |
| 243 | `item_damage_demon_perlevel` | 2 | 3 | `level` | `item_demondamage_percent` |
| 244 | `item_damage_undead_perlevel` | 2 | 3 | `level` | `item_undeaddamage_percent` |
| 245 | `item_tohit_demon_perlevel` | 2 | 1 | `level` | `item_demon_tohit` |
| 246 | `item_tohit_undead_perlevel` | 2 | 1 | `level` | `item_undead_tohit` |
| 247 | `item_crushingblow_perlevel` | 2 | 3 | `level` | `item_crushingblow` |
| 248 | `item_openwounds_perlevel` | 2 | 3 | `level` | `item_openwounds` |
| 249 | `item_kick_damage_perlevel` | 2 | 3 | `level` | `item_kickdamage` |
| 250 | `item_deadlystrike_perlevel` | 2 | 3 | `level` | `item_deadlystrike` |
| 268 | `item_armor_bytime` | 6 | 0 | — | `armorclass` |
| 269 | `item_armorpercent_bytime` | 7 | 0 | — | `armorclass` |
| 270 | `item_hp_bytime` | 6 | 0 | — | `maxhp` |
| 271 | `item_mana_bytime` | 6 | 0 | — | `maxmana` |
| 272 | `item_maxdamage_bytime` | 6 | 0 | — | `maxdamage`, `secondary_maxdamage`, `item_throw_maxdamage` |
| 273 | `item_maxdamage_percent_bytime` | 7 | 0 | — | `maxdamage`, `secondary_mindamage`, `item_throw_mindamage` |
| 274 | `item_strength_bytime` | 6 | 0 | — | `strength` |
| 275 | `item_dexterity_bytime` | 6 | 0 | — | `dexterity` |
| 276 | `item_energy_bytime` | 6 | 0 | — | `energy` |
| 277 | `item_vitality_bytime` | 6 | 0 | — | `vitality` |
| 278 | `item_tohit_bytime` | 6 | 0 | — | `tohit` |
| 279 | `item_tohitpercent_bytime` | 6 | 0 | — | `item_tohit_percent` |
| 280 | `item_cold_damagemax_bytime` | 6 | 0 | — | `coldmaxdam` |
| 281 | `item_fire_damagemax_bytime` | 6 | 0 | — | `firemaxdam` |
| 282 | `item_ltng_damagemax_bytime` | 6 | 0 | — | `lightmaxdam` |
| 283 | `item_pois_damagemax_bytime` | 6 | 0 | — | `poisonmaxdam` |
| 284 | `item_resist_cold_bytime` | 6 | 0 | — | `coldresist` |
| 285 | `item_resist_fire_bytime` | 6 | 0 | — | `fireresist` |
| 286 | `item_resist_ltng_bytime` | 6 | 0 | — | `lightresist` |
| 287 | `item_resist_pois_bytime` | 6 | 0 | — | `poisonresist` |
| 288 | `item_absorb_cold_bytime` | 6 | 0 | — | `item_absorbcold` |
| 289 | `item_absorb_fire_bytime` | 6 | 0 | — | `item_absorbfire` |
| 290 | `item_absorb_ltng_bytime` | 6 | 0 | — | `item_absorblight` |
| 291 | `item_absorb_pois_bytime` | 6 | 0 | — | `item_absorbmagic` |
| 292 | `item_find_gold_bytime` | 6 | 0 | — | `item_goldbonus` |
| 293 | `item_find_magic_bytime` | 6 | 0 | — | `item_magicbonus` |
| 294 | `item_regenstamina_bytime` | 6 | 0 | — | `staminarecoverybonus` |
| 295 | `item_stamina_bytime` | 6 | 0 | — | `maxstamina` |
| 296 | `item_damage_demon_bytime` | 6 | 0 | — | `item_demondamage_percent` |
| 297 | `item_damage_undead_bytime` | 6 | 0 | — | `item_undeaddamage_percent` |
| 298 | `item_tohit_demon_bytime` | 6 | 0 | — | `item_demon_tohit` |
| 299 | `item_tohit_undead_bytime` | 6 | 0 | — | `item_undead_tohit` |
| 300 | `item_crushingblow_bytime` | 6 | 0 | — | `item_crushingblow` |
| 301 | `item_openwounds_bytime` | 6 | 0 | — | `item_openwounds` |
| 302 | `item_kick_damage_bytime` | 6 | 0 | — | `item_kickdamage` |
| 303 | `item_deadlystrike_bytime` | 6 | 0 | — | `item_deadlystrike` |

## Price (plan 0043 Phase 0)

The three per-stat price columns. Offsets are [§ Columns](#columns) (`[C]`, `excel_bin.py diff`); the counts and the
row list come from `python3 -I tools/economy_survey.py stats workspace/merged/data/global/excel` (gate survey
`economy`), `[C]` as data. The price function (`sub_0062FDC0_ItemTradePrice`) is named only
([items/0009 § 9](../findings/items/0009-vendors.md#9-named-only-prices-and-repair)), so how a stat's value enters the
price is `[L]`; by the names, a stat adds `value · Multiply / Divide + Add` or similar, for Phase 1 to read.

| Column | Field | Values | Meaning |
|---|---|---|---|
| `Divide` | `+0x00C` s32 | 1024 on 352 rows; 0 (blank) on 7: 181 `fade`, 182 `armor_override_percent`, 183..187 `unused183`..`unused187` | price divisor `[L]` (a fixed point of 1024, as in [Npc](Npc.md), by the value) |
| `Multiply` | `+0x010` s32 | −34..4096, 67 distinct; non-zero on 187; negative on 2 (91 `item_req_percent` −34, 120 `item_damagetargetac` −20) | per-unit price `[L]` |
| `Add` | `+0x014` s32 | 0..56 452, 118 distinct; non-zero on 184 | fixed price per stat present `[L]` |

- `[C]` **190 rows are priced** (`Multiply` or `Add` ≠ 0); every one has `Divide` 1024, so no priced row divides by 0.
  6 have `Multiply` only: 59 `poisonlength` (4) and the five `passive_*_pierce` (333..336, 358; 1 984..2 812). 3 have
  `Add` only: 81 `item_knockback` (105), 90 `item_lightcolor` (155), 108 `item_restinpeace` (1 987).
- `[C]` The largest terms: `Add` 56 452 on 77 `item_maxmana_percent`, 49 523 on 83 `item_addclassskills`, 36 015 on 85
  `item_addexperience`, 32 093 on 76 `item_maxhp_percent`; `Multiply` 4 096 on 127 `item_allskills`, 2 048 on 153
  `item_cannotbefrozen` and 156 `item_pierce`. Illustrative: 0 `strength` 1024 / 55 / 125, 31 `armorclass`
  1024 / 10 / 17, 204 `item_charged_skill` 1024 / 256 / 401 (`Divide` / `Multiply` / `Add`).
- `[C]` **Stats the price may never see.** 70 `quantity`, 72 `durability`, 152 `item_indestructible` and the 37
  `*_bytime` stats have no price term; 73 `maxdurability` has one (4 / 9), and so do 252 `item_replenish_durability`
  and 253 `item_replenish_quantity` (256 / 106 each), 194 `item_numsockets` (170 / 38) and 254 `item_extra_stack`
  (10 / 99).
- `[C]` **Against the property roll** (`prop_survey.py stats`, [§ Interpretation notes](#interpretation-notes)): of the
  155 stats a used property code writes, 149 are priced; the 5 reachable on the drop path with no price are 27
  `manarecoverybonus`, 28 `staminarecoverybonus`, 151 `item_aura`, 155 `item_reanimate` and 268 `item_armor_bytime`.
  41 priced stats are written by no used code (the 205..213 `unused204`..`unused212` among them, priced as
  `item_charged_skill`).
- `[C]` 7 priced rows are also `Saved` (0 `strength`, 1 `energy`, 2 `dexterity`, 3 `vitality`, 7 `maxhp`, 9 `maxmana`,
  11 `maxstamina`); the last three have `ValShift` 8, so whether the price reads the raw or the shifted value matters
  `[L]`.

## Interpretation notes

- **Save columns.** [save/0001 § 7–8](../findings/save/0001-d2s-io.md) reads the item property writer and reader:
  `[I]` a stat is written only when `Save Bits` ≠ 0 and `value >> ValShift` ≠ 0; the value written is
  `(value >> ValShift) + Save Add`, clamped to `Save Bits`; the param is `Save Param Bits` wide. Stats 17, 48,
  50, 52, 54 and 57 are written with their followers (18; 49; 51; 53; 55, 56; 58, 59) and no id of their own for
  the followers. The [d2s format](../formats/d2s.md) decodes every sample with these columns `[C]`.
- **Encode.** `[L]` The 55 rows with `Encode` > 0 are the stats whose param packs more than a plain value:
  1 = `item_nonclassskill` and `item_singleskill` (param 9 bits); 2 = the six skill-on-event stats
  (`item_skillonattack`…, `Save Param Bits` 16); 3 = `item_charged_skill` (`Save Bits` 16) and nine `unused…` rows
  with `Save Bits` 0; 4 = 37 by-time stats (`item_*_bytime`…, 36 of them with `Save Bits` 22). On the drop path 10
  such stats are reachable (`prop_survey.py stats`).
- **op.** `[L]` 84 rows have an `op` (each listed in [§ Aggregation](#rows-with-an-op)). The 37 rows with `op base` `level` (`op` 2 ×33, 4 ×2, 5 ×2) are exactly the
  `…_perlevel` stats; their `op stat1..3` name the stats the per-level value adds to. `op` 6 (34 rows) has no
  `op base`. `[I]` `op`, `op param`, `op base` and `op stat1..3` are **not read at creation**: no property handler
  and not the writer reads them, so a created item's stat lists hold the raw values. What `op` adds is an
  evaluation-time view, which reaches creation only through func 13 (`dur%`) and the ethereal durability, both
  reading the evaluated stat 73 ([items/0006 § 7](../findings/items/0006-properties.md#7-stat-storage-as-far-as-the-save-needs-it),
  fn:PROP_WriteStat@0x0065EA50, fn:sub_00625E00_ItemMaxDurability@0x00625E00).
- **Which stats the property roll reaches.** `python3 -I tools/prop_survey.py stats …` lists every stat a used
  property code writes. 155 stats are written by some code a source table uses, 152 of them on the drop path; all
  152 have `Save Bits` > 0, 14 have `Save Param Bits` > 0, 10 have `Encode` > 0 and 34 have an `op`. See
  [Properties](Properties.md#survey-the-codes-the-item-tables-use).

## Open questions

- `[L]` Which loader fills the record tail (§ Record layout: `+0x051`, `+0x052`, `+0x05E`, `+0x0DE`, read by the
  evaluation code `[I]`), what `+0x051` means, and what reads `+0x002`, `+0x006`, `+0x028` (0 in every record).
- `[L]` The meaning of the non-save columns (flags, `op` at evaluation time, `Encode`, `desc*`) needs a code anchor;
  plan 0024 Phase 1 settled only that creation does not read `op` (§ Interpretation notes), and the tooltip columns
  are outside the item-generation scope.
- ~~The `startSeed` line of `struct:ItemStatCostRec`~~ fixed by the reverser (`multiply`, plan 0024 Phase 1).

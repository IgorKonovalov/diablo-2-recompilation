# AutoMagic (`data/global/excel/AutoMagic.txt` → `automagic.bin`)

> **Source archive:** mixed: the `.txt` is the d2exp copy and the `.bin` the patch_d2 one (see § The two forms)   **Rows:** 36 (no `Expansion` marker)   **Record:** 144 B
> **sha256:** `automagic.txt` `9c0ea5edcb02422fcfc6f7274a5667057d1a4a205102bb31cb2e102157aeb050`, `automagic.bin` `1838a9581ca8118690cd8b8b8b938c9fb87087a6192dd1a91e27411888d3385c`
> **Doc status:** columns listed, `.bin` layout complete (the [MagicPrefix](MagicPrefix.md) record), values surveyed (plan 0021 Phase 0); semantics `[L]` except the item-side links tagged below

## Purpose

One row per automagic affix: the extra affix an expansion class item (Amazon bows and javelins, Sorceress
orbs, Paladin shields, Druid pelts...) gets on top of its quality. A row has the columns of a magic affix
(three properties, level window, weight, `group`); the base item names the group it draws from in its
`auto prefix` column. Read by `items/affixes` (the automagic step after the quality switch, plan 0021).
Leads: no lead; derived from data.

## Row identity

- `[C]` The record index is the data row index (no `Expansion` marker): `excel_bin.py diff` matches record *i*
  to data row *i* in every mapped column. No row is blank and the 36 names are distinct. (tbl:AutoMagic.txt:Name)
- `[I]` The game loads it with a 144-byte record (call site `0x00633D9B`,
  [data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[I]` An item's automagic affix is kept in item data `+0x36` as an id of the merged affix array, whose `+0x10`
  is the first automagic entry; a save stores it as `class_affix` = id − that base
  ([d2s format](../formats/d2s.md), fn:ITEMS_SetAutoAffix@0x00627F50, data:g_MagicAffixInfo@0x0096CA7C).
  `[L]` Whether `class_affix` is the record index here or record + 1 is for the reverser (backlog).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel automagic`
decodes 36 records × 37 mapped fields = 1 440 cells, 0 mismatches, plus 108 cells of the three layout columns
the `.txt` lacks (`classspecific` holds `0xFF`, `etype4`/`etype5` hold `0xFFFF`, the missing-column defaults,
[data/0004](../findings/data/0004-cell-converters.md)). The record and offsets are those of
[MagicPrefix § Record layout](MagicPrefix.md#record-layout). Observed values from
`python3 -I tools/affix_survey.py columns workspace/merged/data/global/excel automagic`.
**Meaning** is `[L]` throughout, as in [MagicPrefix](MagicPrefix.md#columns).

| Column | Observed type / range | `.bin` field | Tag |
|---|---|---|---|
| `Name` | str, 36 distinct, len ≤ 15 | `+0x000` char[34] | [C] |
| `version` | 100 in every row | `+0x022` u16 | [C] |
| `spawnable` | 1 in every row | `+0x054` u16 | [C] |
| `rare` | 0 ×7, 1 ×29 | `+0x064` u8 | [C] |
| `level` | 1..75 (25 distinct) | `+0x058` u32 | [C] |
| `maxlevel` | blank in every row | `+0x060` u32 | [C] |
| `levelreq` | 2..67 (26 distinct) | `+0x065` u8 | [C] |
| `classspecific` | column absent from the `.txt`; `0xFF` in every record | `+0x066` u8 | [C] |
| `class`, `classlevelreq` | blank in every row | `+0x067` u8 (`0xFF`), `+0x068` u16 | [C] |
| `frequency` | 1..8: 1 ×7, 2 ×12, 3 ×8, 4 ×3, 5 ×2, 6 ×2, 7 ×1, 8 ×1 | `+0x082` u16 | [C] |
| `group` | 300..305: 300 ×3, 301 ×3, 302 ×3, 303 ×13, 304 ×10, 305 ×4 | `+0x05C` u32 | [C] |
| `mod1code`..`mod3code`, `param`, `min`, `max` | (`items/properties`) | `+0x024..+0x053` | [C] |
| `transform` | 1 on 5 rows | — (not compiled) | [C] |
| `transformcolor` | 2 colours on 5 rows | `+0x056` u8 index, blank `0xFF` | [C] |
| `itype1`, `itype2` | `armo` and `weap` in every row | `+0x06A`, `+0x06C` u16 | [C] |
| `itype3`..`itype7`, `etype1`..`etype3` | blank in every row | `+0x06E..`, `+0x078..` u16, 0 | [C] |
| `etype4`, `etype5` | column absent from the `.txt`; `0xFFFF` in every record | `+0x07E`, `+0x080` u16 | [C] |
| `divide`, `multiply`, `add` | 0 in every row | `+0x084`, `+0x088`, `+0x08C` u32 | [C] |

## Groups and the bases that name them

`[C]` by script (`tools/affix_survey.py`, and the `auto prefix` column of [Weapons](Weapons.md),
[Armor](Armor.md) and [Misc](Misc.md), `+0x0F8`). Each group is one or two ladders of rows whose `level` rises
while `frequency` does not; the last row of each ladder except `Sharp` .. `Knight's` has `rare` 0. (tbl:AutoMagic.txt:group, tbl:Weapons.txt:auto prefix)

| `group` | Records | First property | Bases with this `auto prefix` (their `type`) |
|---|---|---|---|
| 300 | 0..2 `Fletcher's`, `Bowyer's`, `Archer's` | `skilltab` | 6 (`abow`) |
| 301 | 3..5 `Acrobat's`, `Gymnast's`, `Athlete's` | `skilltab` | none |
| 302 | 6..8 `Harpoonist's`, `Spearmaiden's`, `Lancer's` | `skilltab` | 9 (`ajav`, `aspe`) |
| 303 | 9..14 `of the Jackal` .. `of the Colossus`; 15..21 `Lizard's` .. `Great Wyrm's` | `hp`; `mana` | 15 (`orb`) |
| 304 | 22..26 `Shimmering` .. `Chromatic`; 27..31 `Sharp` .. `Knight's` | `res-all`; `att` | 15 (`ashd`) |
| 305 | 32..35 `of Blight` .. `of Anthrax` | `pois-min` | 15 (`head`) |

- `[C]` 60 bases have a non-zero `auto prefix`, all with one of these five groups; 599 bases have 0. Group 301 is
  named by no base. (tbl:Weapons.txt:auto prefix, tbl:Armor.txt:auto prefix)
- `[C]` `rare` 0 rows: 2, 5, 8, 14, 21, 26, 35. (tbl:AutoMagic.txt:rare)
- `[C]` Since every row names `armo` and `weap` and no `etype`, any weapon or armour passes a type test against
  every row; the survey's `candidates` command therefore also prints the base's `auto prefix` and how many of
  the listed rows carry it. (tbl:AutoMagic.txt:itype1)
- `[I]` In an expansion game every quality except 5 (set) and 7 (unique) reaches the automagic step with the
  base's group (`+0xF8`) ([items/0004 § 8](../findings/items/0004-uniques-sets.md#8-after-the-switch-named-only-the-phase-2-boundary),
  0x005C1940, fn:ITEMS_SetAutoAffix@0x00627F50). How the row is picked within the group is plan 0021 Phase 1.

## The two forms (mixed-archive table)

The `.txt` is the expansion archive's (d2exp) and was not re-shipped; the patch (patch_d2) ships only a
re-compiled `.bin`, which the game reads ([README § Source and shape](README.md#source-and-shape)).

- `[C]` **No compiled cell differs**: decoded with the 144-byte layout, the `.bin` equals the `.txt` in every
  mapped column (1 440 cells, 0 mismatches, re-run for this doc). (tbl:AutoMagic.txt:Name)
- `[C]` **What differs is the record format and the column set.** The patch `.bin` uses the 144-byte
  `MagicPrefix` record (u16 type indices); the d2exp `.bin` (not loaded in a stock run) has a 132-byte record in
  which `excel_bin.py probe` places `itype1` as a u8 at `+0x069` and `frequency` at `+0x075`. The `.txt` lacks
  `classspecific`, `etype4` and `etype5` (the `.bin` holds their missing-column defaults) and has `transform`,
  which no field carries ([excel-bin § Mixed-archive tables](../formats/excel-bin.md#mixed-archive-tables-automagic-rareprefix-raresuffix)).

## Open questions

- `[L]` Whether the saved `class_affix` is the record index or record + 1 (backlog → reverser).
- `[L]` Every meaning above, in particular whether the pick filters by `group` only or also by type, level,
  `rare` and `frequency` (plan 0021 Phase 1).

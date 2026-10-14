# AutoMagic (`data/global/excel/AutoMagic.txt` → `automagic.bin`)

> **Source archive:** mixed: the `.txt` is the d2exp copy and the `.bin` the patch_d2 one (see § The two forms)   **Rows:** 36 (no `Expansion` marker)   **Record:** 144 B
> **sha256:** `automagic.txt` `9c0ea5edcb02422fcfc6f7274a5667057d1a4a205102bb31cb2e102157aeb050`, `automagic.bin` `1838a9581ca8118690cd8b8b8b938c9fb87087a6192dd1a91e27411888d3385c`
> **Doc status:** columns listed, `.bin` layout complete (the [MagicPrefix](MagicPrefix.md) record), values surveyed (plan 0021 Phase 0); the automagic pick `[I]` from [items/0005](../findings/items/0005-affixes.md)
> (plan 0021 Phase 1, § Code semantics below)

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
- `[I]` **Merged ids.** The automagic rows come last in the merged array (after `magicsuffix` and `magicprefix`), and
  an affix id is the merged index + 1: automagic record r is id `nSuffix + nPrefix + r + 1` (1417 + r with stock
  data). (fn:sub_00633730_LoadMagicAffixes@0x00633730, fn:MAGICAFFIX_GetRecord@0x00633EE0,
  [items/0005 § 1](../findings/items/0005-affixes.md#1-the-merged-affix-arrays-and-the-ids-0x00633730-0x00633f40))
- `[I]` Hence the saved `class_affix`, which is the id minus the automagic start of the merged array (`+0x10` of
  `g_MagicAffixInfo`, index `nSuffix + nPrefix`), is **record + 1**, 0 meaning none; the reader adds the start back
  ([save/0001 § 7](../findings/save/0001-d2s-io.md#7-one-item-items_serializebits--items_writefull--items_writecompact) with items/0005 § 1, data:g_MagicAffixInfo@0x0096CA7C).

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
  0x005C1940, fn:ITEMS_SetAutoAffix@0x00627F50).

## Code semantics (items/0005)

The Phase 0 questions of this doc are answered in
[items/0005 § Answers to the Phase 0 questions](../findings/items/0005-affixes.md#answers-to-the-phase-0-questions). Every statement here is `[I]`, from the code, not
yet reproduced (plan 0021 Phase 2).

- `[I]` **The pick filters by more than `group`.** It is the magic-affix pick
  ([MagicPrefix § Code semantics](MagicPrefix.md#code-semantics-items0005)) over the automagic block with the group
  set to the base's `auto prefix`: no `spawnable` test, but the level window on the item's alvl, the `rare` test (a
  rare item never gets one of the 7 `rare` 0 rows), the type test, `group` = `auto prefix`, `frequency` ≠ 0, the class
  test and group exclusion all apply; the weighted draw is by `frequency`. It always draws its first step (must roll)
  and, with candidates, the weighted draw; the properties are applied after `ITEMS_SetAutoAffix`.
  (fn:sub_005C1940_PickAutoAffixByVersion@0x005C1940, fn:ITEMS_PickMagicAffix@0x005C1560,
  [items/0005 § 7](../findings/items/0005-affixes.md#7-automagic-after-the-quality-switch-0x005579a80x00557a0c), [§ 3](../findings/items/0005-affixes.md#3-items_pickmagicaffixitem-needspawnable-mustroll-applyprops-isprefix-forcedid-autogroup-0x005c1560))
- `[I]` It runs after the quality builder, the ethereal roll and the socket roll, for an expansion item of any
  quality but 5 and 7. A base whose group has no eligible row gets no automagic and spends one step.
  ([items/0005 § 7](../findings/items/0005-affixes.md#7-automagic-after-the-quality-switch-0x005579a80x00557a0c))
- `[I]` Group 301 (named by no base) is never picked from a drop. ([items/0005 § 7](../findings/items/0005-affixes.md#7-automagic-after-the-quality-switch-0x005579a80x00557a0c))

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

- `[L]` Every `[I]` above until plan 0021 Phase 2 reproduces the automagic pick.

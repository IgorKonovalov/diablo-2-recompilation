# Gems (`data/global/excel/gems.txt` → `gems.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 68 (69 `.txt` data rows, one `Expansion` marker)   **Record:** 192 B (`0xC0`)
> **sha256:** `.txt` `157925b4d12502eed32139ca7a246b6f1f7bfca3ea2291239def4bbf8a222bf0`, `.bin` `6b25b05224c2695caa23aa22a52d2fde736edd595d5800e8065e456327ba8508`
> **Doc status:** layout complete (plan 0029 Phase 0); the socket path's use of the row from [items/0007](../findings/items/0007-sockets-runewords.md) (plan 0029 Phase 1)

## Purpose

One row per gem or rune: the item it describes, the rune letter, a colour, and three fixed mod groups of up to three
properties each, one group per kind of socketed item (`weaponMod*`, `helmMod*`, `shieldMod*`). Rows 0–34 are the 35
gems (seven kinds × five grades, the skulls included), rows 35–67 the 33 runes (`El` … `Zod`). Jewels have no row:
a jewel is a magic or rare item with its own rolled affixes. Reader: `items/sockets-runewords` (plan 0029); the loader
`GEMS_Load` links each row to its item ([data/0004 § 3](../findings/data/0004-cell-converters.md#3-runtime-fillers-of-no-column-fields)).
Leads: no lead; derived from data.

## Row identity

- `[C]` The `.bin` is a u32 record count (68) and 68 records of 192 bytes, one per `.txt` row in order, with the
  `Expansion` marker row (after the last skull) dropped; it takes no record ([excel-bin.md](../formats/excel-bin.md)).
  The loader allocates 192-byte records ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x006371AB`).
- `[I]` A row is reached from its item, not by name: `GEMS_Load` writes the row index into the item record's
  `gemoffset` (`+0x0F0`) of the item `code` names, and readers pass that value to `GEMS_GetRecord`
  ([data/0004 § 3](../findings/data/0004-cell-converters.md#3-runtime-fillers-of-no-column-fields), `0x00636B70`, `0x006372C0`).
- `[C]` The socket insert reads the row through the **child's** base record: `ITEMS_AttachToOwner` takes
  `GEMS_GetRecord(ITEMS_GetRecord(child)->gemoffset)` for the gem or rune being inserted; the parent's `gemoffset` is
  not read. So the community reading of `gemoffset` as "the starting index into `gems.txt` for the item" (a D2R guide)
  does not apply to 1.14d; every stock item cell is 0, so the two readings agree on stock data
  ([items/0007 § 3](../findings/items/0007-sockets-runewords.md#3-gems-and-runes-items_attachtoowner-0x0055c2c0), fn:ITEMS_AttachToOwner@0x0055C2C0; corroborated by the 337 transfers of run:2026-10-15-sockets).
- `[C]` `name` is unique (68 distinct); `code` is unique and names a misc item: the gems (`gcv` … `skz`, item version
  0) and the runes (`r01` … `r33`, item version 100).

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel gems`: 68 records × 41 mapped
fields = 2788 cells, **0 mismatches**; `excel_bin.py unknown … gems` lists only `+0x02C..+0x02D`, 0 in every record.
Observed values are from the `.txt` cells (68 rows, marker dropped). The three groups share one 16-byte mod shape
(`code` s32, `param` s32, `min` s32, `max` s32); a blank code stores −1, a blank number 0.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `name` | str, 68 distinct, max 17 chars | `+0x000` char[32] | editor name; not read by the socket path `[I]` ([items/0007 § 3](../findings/items/0007-sockets-runewords.md#3-gems-and-runes-items_attachtoowner-0x0055c2c0)) | — | [C] |
| `letter` | str, 33 distinct (`El` … `Zod`), 35 blank (the gems) | `+0x020` char[8] | rune letter (the runes' part of a runeword's `*runes` comment) `[L]` | — | [C] value; width `[L]` (see notes) |
| `code` | str, 68 distinct | `+0x028` s32 item record index | the gem's or rune's item | weapons + armor + misc `code` ([Misc](Misc.md)) | [C] |
| — | — | `+0x02C` u16 | no column; 0 in the file. `GEMS_Load` fills it at load with `STRTABLE_GetByKey` of a two-byte key built on its stack from the row's item index (68 keys `"-\x02"` … `"\x82\x02"`); no key is found on a stock install, so the stored value is 0 `[I]`; what the key was meant to name is not read ([data/0003 § Run](../findings/data/0003-string-tables.md#run), 0x00637217, 0x00637225; `struct:GemsRec+0x2C`) | — | [C] value 0 in the file |
| `nummods` | int {1, 3}: 3 on the 35 gems, 1 on the 33 runes | `+0x02E` u8 | not read by the socket path: the block loop stops at the first block with `code < 0` instead `[I]` ([items/0007 § 3](../findings/items/0007-sockets-runewords.md#3-gems-and-runes-items_attachtoowner-0x0055c2c0), 0x0065FEC0–0x0066007B) | — | [C] |
| `transform` | int 0..18 (14 distinct) | `+0x02F` u8 | colour of a socketed item `[L]`; every value is a [colors](colors.md) row: amethyst 18 `dpur` (perfect 17 `lpur`), sapphire 5 `dblu` (6 `cblu`), emerald 11 (12), ruby 8 (9), diamond 1 `lgry` (0 `whit`), topaz 14 (13), skull 2 `dgry` (perfect 3 `blac`), every rune 18 | [colors](colors.md) row index `[L]` | [C] |
| `weaponMod1Code` | str, 39 distinct, 0 blank | `+0x030` s32 row index | first property of the weapon group, applied when the parent's `gemapplytype` is 0 `[C]` ([items/0007 § 3](../findings/items/0007-sockets-runewords.md#3-gems-and-runes-items_attachtoowner-0x0055c2c0), fn:sub_0065C6D0_PropBlock3x3@0x0065C6D0) | [Properties](Properties.md) `code` | [C] |
| `weaponMod1Param` | int {0, 75, 125}, 31 blank | `+0x034` s32 | its parameter: 125 on `Tal` (`dmg-pois`), 75 on `Thul` (`dmg-cold`), presumably a length in frames `[L]` | — | [C] |
| `weaponMod1Min`, `weaponMod1Max` | int −20..154; equal on every row except `Ral`, `Ort`, `Thul` (elemental damage ranges, e.g. `Thul` `dmg-cold` 3..14) | `+0x038`, `+0x03C` s32 | its value or range | — | [C] |
| `weaponMod2Code` … `weaponMod2Max` | 8 codes, 40 blank | `+0x040` … `+0x04C` | second weapon property | [Properties](Properties.md) `code` | [C] |
| `weaponMod3Code` … `weaponMod3Max` | {`cold-len`, `pois-len`}, 58 blank | `+0x050` … `+0x05C` | third weapon property | [Properties](Properties.md) `code` | [C] |
| `helmMod1Code` … `helmMod1Max` | 36 codes, 0 blank; values −15..100 | `+0x060` … `+0x06C` | first property of the helm group, applied when the parent's `gemapplytype` is 1 `[C]` ([items/0007 § 3](../findings/items/0007-sockets-runewords.md#3-gems-and-runes-items_attachtoowner-0x0055c2c0)) | [Properties](Properties.md) `code` | [C] |
| `helmMod2Code` … `helmMod2Max` | {`ac`, `regen-mana`}, 62 blank | `+0x070` … `+0x07C` | second helm property | [Properties](Properties.md) `code` | [C] |
| `helmMod3Code` … `helmMod3Max` | blank in every row | `+0x080` … `+0x08C` | third helm property | — | [C] value; slot `[I]`: `PropBlock3x3` returns `row + {0x30, 0x60, 0x90}[group] + 16·i` for `i` < 3 ([items/0007 § 3](../findings/items/0007-sockets-runewords.md#3-gems-and-runes-items_attachtoowner-0x0055c2c0)) |
| `shieldMod1Code` … `shieldMod1Max` | 34 codes, 0 blank; values −15..50 | `+0x090` … `+0x09C` | first property of the shield group, applied when the parent's `gemapplytype` is 2 `[C]` ([items/0007 § 3](../findings/items/0007-sockets-runewords.md#3-gems-and-runes-items_attachtoowner-0x0055c2c0)) | [Properties](Properties.md) `code` | [C] |
| `shieldMod2Code` … `shieldMod2Max` | {`ac`}, 67 blank | `+0x0A0` … `+0x0AC` | second shield property | [Properties](Properties.md) `code` | [C] |
| `shieldMod3Code` … `shieldMod3Max` | blank in every row | `+0x0B0` … `+0x0BC` | third shield property | — | [C] value; slot `[I]` (as `helmMod3`) |

## Interpretation notes

- **Mod lines per group.** Weapon group: 1 line on 40 rows, 2 on 18, 3 on 10 (the sapphires, rubies and topazes:
  `cold-min`/`cold-max`/`cold-len` and the like; the emeralds' `dmg-pois` with `pois-len`). Helm group: 1 line on 62,
  2 on 6. Shield group: 1 on 67, 2 on 1. `nummods` does not follow this: 3 on every gem (also those with one line in
  each group), 1 on every rune (also `El`, which has 2 weapon lines). `[C]` for the counts
  (`python3 -I tools/socket_survey.py gems …`). The socket path does not read `nummods`; it applies a group's blocks
  up to the first `code < 0` `[I]` ([items/0007 § 3](../findings/items/0007-sockets-runewords.md#3-gems-and-runes-items_attachtoowner-0x0055c2c0)).
- **Which group applies.** The item tables carry `gemapplytype`: 0 on every weapon, 1 on the 58 helms and 45 body
  armours with sockets, 2 on the 54 shields (`shie`, `ashd`, `head`), 0 on belts, boots and gloves (no sockets). The
  insert applies group *g* = the **parent's** `gemapplytype` (0 → `weaponMod`, 1 → `helmMod`, 2 → `shieldMod`; a
  group ≥ 3 is fatal), so body armour takes the `helmMod` group `[C]` ([items/0007 § 3](../findings/items/0007-sockets-runewords.md#3-gems-and-runes-items_attachtoowner-0x0055c2c0), corroborated by the 178 gem
  transfers of run:2026-10-15-sockets, each gem into each group). On stock data the transfer makes no draw: every
  block has `min = max` or a func that does not draw `[C]` (data behaviour over all rows, same section)
  ([Weapons](Weapons.md), [Armor](Armor.md)).
- **Classic.** The 35 gem rows name items of version 0; the 33 runes are version 100 (expansion items). The server
  insert tests neither the item version nor the game type: a rune inserted in a classic game was accepted `[C]`
  ([items/0007 § 1](../findings/items/0007-sockets-runewords.md#1-the-insert-items_insertsocket-0x00562660),
  fn:ITEMS_InsertSocket@0x00562660, run:2026-10-15-sockets).
- **`letter` width.** The data fixes only that the field starts at `+0x020` and holds at least 4 characters and the
  NUL (`Cham`, `Shael` is 5: at least 6 bytes); `+0x026..+0x027` are 0 in every record and `code` follows at
  `+0x028`. Eight bytes is the space before `code`, not a read width. `[L]`
- Survey: `python3 -I tools/socket_survey.py gems workspace/merged/data/global/excel` prints each row's item, letter,
  `nummods`, `transform`, item version and its three groups.

## Open questions

- `[L]` What `transform` drives (the socketed item's colour, items/0003 § 3 names it only) and the `letter` read
  width. The group per base and `nummods` are settled above ([items/0007](../findings/items/0007-sockets-runewords.md)).
- `[L]` What the two-byte key `GEMS_Load` looks up for `+0x02C` was meant to name (no stock key resolves).

# CharTemplate (`data/global/excel/CharTemplate.txt` → `chartemplate.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 30 (no `Expansion` marker)   **Record:** 240 B (`0xF0`)
> **sha256:** `.txt` `64f58b7978093ec5a3013a35ea76dcb5e31861c37e84f20552813044c64a1a11`, `.bin` `6eb0b9240ddd7ec17d965a031b56b29212e03f0a1ade43c821d434a9ff2832ad`
> **Doc status:** layout complete (plan 0034 Phase 0); whether stock play reads it `[L]`

## Purpose

Thirty ready-made characters of the five classic classes, at level 3 or 9: attributes, life, mana, up to nine skills
with levels, and up to fifteen items. Every `Name` is `Unwritten`. Nothing in the plan's paths is known to read it.
Reader if any: `player/creation` (plan 0034 Phase 1 decides). Leads: none registered.

## Does the game read it?

- `[C]` It is loaded: data/0001 lists `chartemplate` with 240-byte records at `0x0066571A`, with no `-txt`-only marker
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[L]` Whether any stock path uses the records (the new-character path, a test or server mode, or nothing) is
  unknown; the data has no `Name` but `Unwritten`, no `Act`, and only the five classic classes, which looks like an
  unused or development feature. Question for the reverser, plan 0034 Phase 1 ([backlog](../backlog.md)).

## Row identity

- `[C]` The `.bin` is a u32 record count (30) and 30 records of 240 bytes, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). `Template` is not compiled: a record is found by its index or by
  (`Class`, `Level`). Records 0–14 are level 3, three per class in the order Amazon, Sorceress, Necromancer, Paladin,
  Barbarian; records 15–29 the same at level 9.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel chartemplate`: 30 records × 76
mapped fields = 2 280 cells, **0 mismatches**; `excel_bin.py unknown … chartemplate` lists only the no-column bytes
below, 0 in every record. Observed values are computed over the 30 `.txt` rows (`python3 -I tools/player_survey.py
templates …` prints each record from the `.bin`).

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Template` | str, 14 distinct (`Amazon Bow`, `Sorceress Fire`, `Necromancer`, …) | — (not compiled) | editor name | — | [C] |
| `Name` | str `Unwritten` (all) | `+0x000` char[30] | character name `[L]` | — | [C] |
| `Class` | str {`ama`, `sor`, `nec`, `pal`, `bar`}, 6 rows each | `+0x01E` u8 row index | class | `playerclass` `Code` (= [CharStats](CharStats.md) record) | [C] |
| `Level` | int {3, 9}, 15 rows each | `+0x01F` u8 | character level `[L]` | — | [C] |
| `Act` | blank (all) | `+0x020` u8, blank → 0 | `[L]` | — | [C] (value 0 only; the slot by `.txt` order) |
| `str`, `dex`, `int`, `vit` | int 10..40; 15..32; 10..40; 10..42 | `+0x021`..`+0x024` u8 | attributes `[L]` | — | [C] |
| `tot` | int 80..105 | — (not compiled) | editor sum | — | [C] |
| `LifePerLevel`, `ManaPerLevel`, `LifePerVitality`, `ManaPerMagic` | int {12, 18, 24}; 2..8; 4..8; {4, 5, 8} | — (not compiled: no byte holds them) | editor helpers | — | [C] |
| `Mana` | int 10..56 | `+0x025` u8 | mana `[L]` | — | [C] |
| `Hitpoints` | int 24..89 | `+0x026` u8 | life `[L]` | — | [C] |
| — | — | `+0x027` u8 | no column identified, 0 | — | [C] value |
| `Velocity`, `AttackRate`, `OtherRate` | int 100 (all) | `+0x028`, `+0x029`, `+0x02A` u8 | `[L]` | — | [C] bytes; which is which by `.txt` order `[L]` |
| `ManaRegenBonus`, `RightSkill` | int 0 (all) | not identified: `+0x027` or `+0x02B`..`+0x02F`, all zero | `[L]` | — | [C] that no non-zero byte holds them |
| — | — | `+0x02B` u8, `+0x02C` u32 | no column identified, 0 | — | [C] value |
| `Total Skills` | int {0, 3, 4} | — (not compiled) | editor helper | — | [C] |
| `SkillName` (×9) | str: skill names or `0` | — (not compiled) | editor label of the next `SkillN` | — | [C] |
| `Skill1..9` | int: `Skill1` 0 or a skill id (7, 10, 36, 38, 39, 67, 96, 97, 98); `Skill2` 0 or 37; 3–9 always 0 | `+0x030 + 4(k−1)` s32 | skills row index, written as a number in the `.txt` | [Skills](Skills.md) row | [C] for 1–2; 3–9 by the stride `[L]` |
| `SkillLevel1..9` | int {0, 3, 4}; {0, 1}; 3–9 always 0 | `+0x054 + 4(k−1)` s32 | the skill's level `[L]` | — | [C] for 1–2; 3–9 by the stride `[L]` |
| `baseWClass` | str `hth` (all) | — (not compiled: no field holds it) | `[L]` | — | [C] |
| `item1..15` | str: `item1` 12 weapon codes; `item2` `0`, `aqv`, `buc`; 3–15 `0` | `+0x078 + 8(k−1)` 4-byte code | item `[L]` | [Weapons](Weapons.md)/[Armor](Armor.md)/[Misc](Misc.md) `code` | [C] for 1–2; 3–15 by the stride `[L]` |
| `item1..15loc` | int: `item1loc` 4; `item2loc` 0 or 5; else 0 | `+0x07C + 8(k−1)` u8 | body location, a number (4 right arm, 5 left arm in `bodylocs` order) `[L]` | `bodylocs` row | [C] for 1–2; 3–15 by the stride `[L]` |
| `item1..15count` | int: 1; 0 or 1; else 0 | `+0x07D + 8(k−1)` u8 | count `[L]` | — | [C] for 1–2; 3–15 by the stride `[L]` |
| — | — | `+0x07E + 8(k−1)` u16 | padding of each slot, 0 | — | [C] value |

## Interpretation notes

- **Same item slot shape as CharStats** (code, location u8, count u8, two zero bytes), but the location is a plain
  number in the `.txt` here and a `bodylocs` code there; both compile to the same row index. `[C]`
- **Skills by number.** `Skill1..9` hold skills row indices directly, and `SkillName` is only a label for the editor:
  the `Sorceress Fire` row's label is `Firebolt`, its id 36 is `Fire Bolt`. `[C]`
- **The `Act` slot.** `Act` is blank in every row, and the only zero byte between `Level` and `str` is `+0x020`; the
  slot follows the `.txt` order `[L]`, the value 0 is `[C]`.
- **Levels 3 and 9 only.** The level 9 rows have no skills (`Skill1` 0); their attributes equal their class's
  CharStats attributes for the Amazon and the Necromancer and differ by 5 to 10 points for the other three. `[C]` for
  the values; whether the life and mana columns follow CharStats' arithmetic is for Phase 1 `[L]`.

## Open questions

- `[L]` Whether stock play reads the table at all (above); where `ManaRegenBonus` and `RightSkill` live (a `-txt`
  compile probe with non-zero cells settles it, and the order of `Velocity`/`AttackRate`/`OtherRate`).

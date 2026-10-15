# CharStats (`data/global/excel/charstats.txt` → `charstats.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 7 (8 `.txt` rows less the `Expansion` marker)   **Record:** 196 B (`0xC4`)
> **sha256:** `.txt` `bfd28714a573384da0575c6525b3733c82e3bf97f47d0f3e1b8552d137bff51f`, `.bin` `52e1903468b6ba50392545b1e61578b239b9b98a89d21e1ebf156988094541a6`
> **Doc status:** layout complete (plan 0034 Phase 0); semantics `[L]` (plan 0034 Phase 1)

## Purpose

One row per player class: the new character's attributes, stamina and life base, the per-level and per-attribute
growth, movement and combat factors, the class's string keys, and the starting item list and skills. Readers:
`player/creation` (plan 0034: the new character, the level-up) and the item and skill code that prints the class
strings. Leads: none registered; nothing here comes from one.

## Row identity

- `[C]` The `.bin` is a u32 record count (7) and 7 records of 196 bytes, the `.txt` rows in order with the
  `Expansion` marker row dropped ([excel-bin.md](../formats/excel-bin.md)): Amazon 0, Sorceress 1, Necromancer 2,
  Paladin 3, Barbarian 4, Druid 5, Assassin 6. The loader allocates 196-byte records
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x00613D07`).
- `[L]` The record index is the class id a save stores (header `0x028`, [d2s.md](../formats/d2s.md)): the order is the
  same as `d2s.py`'s class list and the [PlayerClass](README.md) codes `ama sor nec pal bar dru ass`, and each of the
  seven fresh saves' attributes equals its record's (notes). Which code indexes the table by it is for Phase 1.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel charstats`: 7 records × 71 mapped
fields = 497 cells, **0 mismatches**; `excel_bin.py unknown … charstats` lists only the no-column bytes below, 0 in
every record. Observed values are computed over the 7 `.txt` rows (`python3 -I tools/player_survey.py start …`
prints them per class from the `.bin`).

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| — | — | `+0x000` 32 bytes | no column, 0 in the file | — | [C] value |
| `class` | str, the 7 class names | `+0x020` char[16] | class name | — | [C] |
| `str`, `dex`, `int`, `vit` | int 10..30; {20, 25}; 10..35; 10..25 | `+0x030`, `+0x031`, `+0x032`, `+0x033` u8 | new character's strength, dexterity, energy, vitality `[L]` | — | [C] |
| `tot` | int {80, 85} | — (not compiled) | editor sum of the four | — | [C] |
| `stamina` | int 74..95 | `+0x034` u8 | new character's stamina `[L]` | — | [C] |
| `hpadd` | int 30 (all) | `+0x035` u8 | life added to vitality at creation `[L]` | — | [C] |
| `PercentStr`, `PercentInt`, `PercentDex`, `PercentVit` | int 20..35; 10..35; 15..35; 15..30 | `+0x036`, `+0x037`, `+0x038`, `+0x039` u8 | `[L]` (by name, an attribute split) | — | [C]; note `PercentInt` before `PercentDex` |
| `ManaRegen` | int 120 (all) | `+0x03A` u8 | mana regeneration factor `[L]` | — | [C] |
| — | — | `+0x03B` u8 | padding, 0 | — | [C] value |
| `ToHitFactor` | int −15..20 | `+0x03C` s32 | attack rating base `[L]` | — | [C] |
| `WalkVelocity`, `RunVelocity` | int 6; 9 (all) | `+0x040`, `+0x041` u8 | movement speeds `[L]` | — | [C] |
| `RunDrain` | int {15: Assassin, 20} | `+0x042` u8 | stamina drain while running `[L]` | — | [C] |
| `Comment` | str `The following are in fourths` (all) | — (not compiled) | editor note on the next six columns | — | [C] |
| `LifePerLevel`, `StaminaPerLevel`, `ManaPerLevel` | int {4, 6, 8}; {4, 5}; {4, 6, 8} | `+0x043`, `+0x044`, `+0x045` u8 | gain per character level, in fourths of a point by the comment `[L]` | — | [C] bytes; `+0x044` vs `+0x047` by `.txt` order (notes) |
| `LifePerVitality`, `StaminaPerVitality`, `ManaPerMagic` | int {8, 12, 16}; {4, 5}; 4..8 | `+0x046`, `+0x047`, `+0x048` u8 | gain per point of vitality / energy, in fourths `[L]` | — | [C] bytes; as above |
| `StatPerLevel` | int 5 (all) | `+0x050` u8 | attribute points per level `[L]` | — | [C] |
| `#walk`, `#run`, `#swing`, `#spell`, `#gethit`, `#bow` | int 4..22 | — (not compiled) | editor notes (frame counts by name) | — | [C] |
| `BlockFactor` | int {20, 25, 30} | `+0x049` u8 | block chance base `[L]` | — | [C] |
| — | — | `+0x04A` u16 | padding, 0 | — | [C] value |
| `baseWClass` | str `hth` (all) | `+0x04C` 4-byte code | unarmed weapon class `[L]` | WeaponClass codes | [C] |
| — | — | `+0x051` u8 | padding, 0 | — | [C] value |
| `StrAllSkills` | str, 7 keys (`ModStr3a` … `ModStre8b`) | `+0x052` u16 string index | "+n to <class> Skill Levels" text | string tables ([tbl.md](../formats/tbl.md)) | [C] |
| `StrSkillTab1`..`3` | str, 21 keys `StrSklTabItem1..21` | `+0x054`, `+0x056`, `+0x058` u16 string index | the three skill-tab texts | string tables | [C] |
| `StrClassOnly` | str `AmaOnly` … `AssOnly` | `+0x05A` u16 string index | "(<class> Only)" text | string tables | [C] |
| `item1..10` | str: `item1` the class weapon (7 codes), then `buc`, `hp1`, `tsc`, `isc`; `0` for an empty slot | `+0x05C + 8(k−1)` 4-byte code | starting item `[L]` | [Weapons](Weapons.md)/[Armor](Armor.md)/[Misc](Misc.md) `code` | [C] |
| `item1..10loc` | str: `item1loc` `rarm`; `item2loc` `larm` when `item2` is `buc`; else blank | `+0x060 + 8(k−1)` u8 row index, blank → 0 | body location the item starts in `[L]` | `bodylocs` `Code` (`rarm` 4, `larm` 5) | [C] |
| `item1..10count` | int 0..4 | `+0x061 + 8(k−1)` u8 | how many of the item `[L]` | — | [C] |
| — | — | `+0x062 + 8(k−1)` u16 | padding of each slot, 0 | — | [C] value |
| `StartSkill` | str, 5 blank, `fire bolt` (Sorceress), `raise skeleton` (Necromancer) | `+0x0AC` u16 row index, blank → `0xFFFF` | `[L]` (notes) | [Skills](Skills.md) `skill`, matched case-insensitively (or `skilldesc`, notes) | [C] |
| `Skill 1`..`Skill 10` | str: 1–6 `Throw`, `Kick`, `Scroll of Identify`, `Book of Identify`, `Scroll of Townportal`, `Book of Townportal`; 7–9 `Unsummon`, `Left Hand Throw`, `Left Hand Swing` or blank; 10 blank | `+0x0AE + 2(k−1)` u16 row index, blank → `0xFFFF` | skills every character has `[L]` | [Skills](Skills.md) `skill` | [C] |
| — | — | `+0x0C2` u16 | padding, 0 | — | [C] value |

The plan's column list also names `SkillsPerLevel` and `MinimumCastingDelay`: **this `charstats.txt` has neither**
`[C]`. Skill points per level are not in this table.

## Interpretation notes

- **The start block per class** (`python3 -I tools/player_survey.py start …`, `[C]` for the values): every class has
  4 × `hp1`, 1 × `tsc`, 1 × `isc` and its weapon in `rarm` (Amazon `jav`, Sorceress `sst`, Necromancer `wnd`,
  Paladin `ssd`, Barbarian `hax`, Druid `clb`, Assassin `ktr`); all but the Sorceress and Necromancer also a `buc` in
  `larm`. 33 item slots in all, at most 5 per class; every code resolves to an item.
- **The fresh saves agree.** The seven level-1 samples `workspace/samples/d2s/smp*.d2s`
  ([run:2026-10-11-d2s-samples](../formats/experiments.md#run2026-10-11-d2s-samples), made through the game's
  new-character screen) hold, for every class: strength, dexterity, vitality = `str`, `dex`, `vit`; energy (stat 1)
  = `int`; life = max life = `vit` + `hpadd`; mana = max mana = `int`; stamina = max stamina = `stamina`; the
  weapon in the right hand and the buckler in the left; four separate `hp1` in belt slots 0–3; `isc` at inventory
  (9, 2) and `tsc` at (9, 3). Each class skill byte is 0; the right mouse skill is 36 (Fire Bolt) for the Sorceress,
  70 (Raise Skeleton) for the Necromancer and 0 for the others. These are observations of 7 files: what the game
  computes, and whether `StartSkill` is a right-mouse default rather than a skill point, is `[L]` until Phase 1.
- **The "fourths".** The `Comment` column says the next columns are in fourths; at level 1 nothing shows it, since
  life is `vit + hpadd` in whole points. The unit of each per-level and per-attribute column is `[L]`.
- **Same cells, two columns.** `StaminaPerLevel` and `StaminaPerVitality` hold the same cell in every row, so the data
  cannot say which of `+0x044`/`+0x047` is which; the layout follows the `.txt` order. `[L]`
- **`StartSkill` resolves either way.** Its two cells are lower-case (`fire bolt`, `raise skeleton`), as in
  `skilldesc.txt`'s key; they resolve to the same index (36, 70) through `skills.txt` `skill` matched without case,
  and `skilldesc` rows 36 and 70 are those skills' descriptions. Which table the compiler reads is `[L]`.
- **`+0x000`..`+0x01F` are zero** in every record and have no column: filled at load, or unused, is `[L]`.

## Open questions

- `[L]` The new character's arithmetic (life, mana, stamina in 1/256 units, the "fourths"), what `StartSkill` sets,
  the item creation (quality, seed, placement), the per-level gains and `StatPerLevel`; reverser, plan 0034 Phase 1
  ([backlog](../backlog.md)).
- `[L]` `ToHitFactor`, `BlockFactor`, `ManaRegen`, the velocities, `RunDrain` and the `Percent*` columns: who reads them.
- `[L]` Which of `+0x044`/`+0x047` is `StaminaPerLevel` (a `-txt` compile probe with distinct cells settles it).

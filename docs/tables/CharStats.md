# CharStats (`data/global/excel/charstats.txt` → `charstats.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 7 (8 `.txt` rows less the `Expansion` marker)   **Record:** 196 B (`0xC4`)
> **sha256:** `.txt` `bfd28714a573384da0575c6525b3733c82e3bf97f47d0f3e1b8552d137bff51f`, `.bin` `52e1903468b6ba50392545b1e61578b239b9b98a89d21e1ebf156988094541a6`
> **Doc status:** layout complete (plan 0034 Phase 0); semantics from [player/0001](../findings/player/0001-creation.md) (plan 0034 Phase 1)

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
- `[I]` The record index is the class id a save stores (header `0x028`, [d2s.md](../formats/d2s.md)):
  `PLAYER_InitBaseStats` and `PLAYER_LevelUp` take record `unit->classId` (`classId < g_nCharStats`), and the order is
  the same as `d2s.py`'s class list and the [PlayerClass](README.md) codes `ama sor nec pal bar dru ass`; each of the
  seven fresh saves' attributes equals its record's (notes) ([player/0001 § 3](../findings/player/0001-creation.md#3-starting-attributes--player_initbasestats-0x005706d0),
  fn:PLAYER_InitBaseStats@0x005706D0).

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel charstats`: 7 records × 71 mapped
fields = 497 cells, **0 mismatches**; `excel_bin.py unknown … charstats` lists only the no-column bytes below, 0 in
every record. Observed values are computed over the 7 `.txt` rows (`python3 -I tools/player_survey.py start …`
prints them per class from the `.bin`).

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| — | — | `+0x000` 32 bytes | no column, 0 in the file; at load the class's display name, UTF-16, at most 16 units `[I]` ([player/0001 § 9](../findings/player/0001-creation.md#9-other-charstats-readers-for-the-archivists-table-doc)) | `class` key in the string tables | [C] value |
| `class` | str, the 7 class names | `+0x020` char[16] | class name | — | [C] |
| `str`, `dex`, `int`, `vit` | int 10..30; {20, 25}; 10..35; 10..25 | `+0x030`, `+0x031`, `+0x032`, `+0x033` u8 | new character's strength, dexterity, energy (stat 1), vitality, set as is `[I]` ([player/0001 § 3](../findings/player/0001-creation.md#3-starting-attributes--player_initbasestats-0x005706d0)) | — | [C] |
| `tot` | int {80, 85} | — (not compiled) | editor sum of the four; not compiled `[I]` ([§ 3](../findings/player/0001-creation.md#3-starting-attributes--player_initbasestats-0x005706d0)) | — | [C] |
| `stamina` | int 74..95 | `+0x034` u8 | new character's stamina and max stamina, `stamina << 8` `[I]` ([§ 3](../findings/player/0001-creation.md#3-starting-attributes--player_initbasestats-0x005706d0)) | — | [C] |
| `hpadd` | int 30 (all) | `+0x035` u8 | life = max life = `(vit + hpadd) << 8` at creation `[I]` ([§ 3](../findings/player/0001-creation.md#3-starting-attributes--player_initbasestats-0x005706d0)) | — | [C] |
| `PercentStr`, `PercentInt`, `PercentDex`, `PercentVit` | int 20..35; 10..35; 15..35; 15..30 | `+0x036`, `+0x037`, `+0x038`, `+0x039` u8 | compiled; no reader found among the 23 server code sites `[I]` ([§ 3](../findings/player/0001-creation.md#3-starting-attributes--player_initbasestats-0x005706d0)); client getter `0x004833E0` not followed | — | [C]; note `PercentInt` before `PercentDex` |
| `ManaRegen` | int 120 (all) | `+0x03A` u8 | mana regeneration factor, read as `ManaRegen × 25` `[I]` (0x00548640, [§ 9](../findings/player/0001-creation.md#9-other-charstats-readers-for-the-archivists-table-doc)) | — | [C] |
| — | — | `+0x03B` u8 | padding, 0 | — | [C] value |
| `ToHitFactor` | int −15..20 | `+0x03C` s32 | added to the base attack rating `(dex − 7) × 5 + stat 19 + ToHitFactor`, an attack-rating term only `[C]` (fn:sub_00622560_PlayerBaseToHit@0x00622560, [§ 9](../findings/player/0001-creation.md#9-other-charstats-readers-for-the-archivists-table-doc), run:2026-10-16-combat) | — | [C] |
| `WalkVelocity`, `RunVelocity` | int 6; 9 (all) | `+0x040`, `+0x041` u8 | walk speed `WalkVelocity << 8`; run as `velocitypercent = RunVelocity × 100 / WalkVelocity − 100` `[I]` (0x0056E5B0, [§ 9](../findings/player/0001-creation.md#9-other-charstats-readers-for-the-archivists-table-doc)); *plan 0046 readers:* `[C]` as a map: Charge (start 31) takes a player's `RunVelocity` byte `<< 8` (0x100 without a record) as `base` in `MulDiv(base, max(stat 67, 50) + Param1, 100)` (Skills `Param1`), passed to `sub_00648690_PathSetSpeed` (ADR-0021 boundary); `[I]` that this is the charge's speed, `run × (max(velocitypercent, 50) + 150) / 100` for Charge ([skills/0011 § 5](../findings/skills/0011-paladin.md#5-charge-and-the-missiles-start-31-do-67-73-80); fn:sub_005CF6B0_SkillSt31Charge@0x005CF6B0) | — | [C] |
| `RunDrain` | int {15: Assassin, 20} | `+0x042` u8 | per-step run drain `RunDrain × 2`, scaled by the equipped armour and stat 154 `[I]` (0x0057F240, [§ 9](../findings/player/0001-creation.md#9-other-charstats-readers-for-the-archivists-table-doc)) | — | [C] |
| `Comment` | str `The following are in fourths` (all) | — (not compiled) | editor note on the next six columns; not compiled `[I]` ([§ 3](../findings/player/0001-creation.md#3-starting-attributes--player_initbasestats-0x005706d0)) | — | [C] |
| `LifePerLevel`, `StaminaPerLevel`, `ManaPerLevel` | int {4, 6, 8}; {4, 5}; {4, 6, 8} | `+0x043`, `+0x044`, `+0x045` u8 | max life / stamina / mana gained per level, in quarter points (`× d × 64` in 1/256 units, `d` = levels gained) `[I]` ([§ 7](../findings/player/0001-creation.md#7-level-up--player_levelup-0x00570880)) | — | [C], `+0x044` `StaminaPerLevel` by the loader's descriptor ([§ 3](../findings/player/0001-creation.md#3-starting-attributes--player_initbasestats-0x005706d0)) |
| `LifePerVitality`, `StaminaPerVitality`, `ManaPerMagic` | int {8, 12, 16}; {4, 5}; 4..8 | `+0x046`, `+0x047`, `+0x048` u8 | max life and stamina per vitality point, max mana per energy point, in quarter points (`× n × 64`); not applied to the starting attributes `[I]` ([§ 3](../findings/player/0001-creation.md#3-starting-attributes--player_initbasestats-0x005706d0), [§ 7](../findings/player/0001-creation.md#7-level-up--player_levelup-0x00570880)) | — | [C], `+0x047` `StaminaPerVitality` by the descriptor |
| `StatPerLevel` | int 5 (all) | `+0x050` u8 | attribute points per level, read as a **signed** byte: `statpts += StatPerLevel × d` `[I]` ([§ 7](../findings/player/0001-creation.md#7-level-up--player_levelup-0x00570880)) | — | [C] |
| `#walk`, `#run`, `#swing`, `#spell`, `#gethit`, `#bow` | int 4..22 | — (not compiled) | editor notes (frame counts by name); not compiled `[I]` ([§ 3](../findings/player/0001-creation.md#3-starting-attributes--player_initbasestats-0x005706d0)) | — | [C] |
| `BlockFactor` | int {20, 25, 30} | `+0x049` u8 | block base: `block = toblock + BlockFactor`, dexterity form `((dex − 15) × block) / (2 × max(level, 1))`, capped at 75 `[I]` (fn:sub_00622720_UnitBlockChance@0x00622720, [§ 9](../findings/player/0001-creation.md#9-other-charstats-readers-for-the-archivists-table-doc)) | — | [C] |
| — | — | `+0x04A` u16 | padding, 0 | — | [C] value |
| `baseWClass` | str `hth` (all) | `+0x04C` 4-byte code | weapon class of a player in mode 0 or 0x11 or with no item of component 5/6 in either hand `[I]` (0x0064F166, [§ 5](../findings/player/0001-creation.md#5-starting-items--player_givestartitems-0x00534f10)) | WeaponClass codes | [C] |
| — | — | `+0x051` u8 | padding, 0 | — | [C] value |
| `StrAllSkills` | str, 7 keys (`ModStr3a` … `ModStre8b`) | `+0x052` u16 string index | "+n to <class> Skill Levels" text | string tables ([tbl.md](../formats/tbl.md)) | [C] |
| `StrSkillTab1`..`3` | str, 21 keys `StrSklTabItem1..21` | `+0x054`, `+0x056`, `+0x058` u16 string index | the three skill-tab texts | string tables | [C] |
| `StrClassOnly` | str `AmaOnly` … `AssOnly` | `+0x05A` u16 string index | "(<class> Only)" text | string tables | [C] |
| `item1..10` | str: `item1` the class weapon (7 codes), then `buc`, `hp1`, `tsc`, `isc`; `0` for an empty slot | `+0x05C + 8(k−1)` 4-byte code | starting item, created in slot order, quality 2 (normal), ilvl = the player's level, identified; `item1` also gets `item_singleskill(StartSkill) = 1` `[I]` ([§ 5](../findings/player/0001-creation.md#5-starting-items--player_givestartitems-0x00534f10)) | [Weapons](Weapons.md)/[Armor](Armor.md)/[Misc](Misc.md) `code` | [C] |
| `item1..10loc` | str: `item1loc` `rarm`; `item2loc` `larm` when `item2` is `buc`; else blank | `+0x060 + 8(k−1)` u8 row index, blank → 0 | body location: ≠ 0 → equipped there (inventory if that fails); beltable types go to the belt first `[I]` ([§ 5](../findings/player/0001-creation.md#5-starting-items--player_givestartitems-0x00534f10)) | `bodylocs` `Code` (`rarm` 4, `larm` 5) | [C] |
| `item1..10count` | int 0..4 | `+0x061 + 8(k−1)` u8 | copies of the item `[I]` ([§ 5](../findings/player/0001-creation.md#5-starting-items--player_givestartitems-0x00534f10)) | — | [C] |
| — | — | `+0x062 + 8(k−1)` u16 | padding of each slot, 0 | — | [C] value |
| `StartSkill` | str, 5 blank, `fire bolt` (Sorceress), `raise skeleton` (Necromancer) | `+0x0AC` u16 row index, blank → `0xFFFF` | the new character's **right** skill, if the unit has it after the items (via `item1`'s `item_singleskill`); blank = −1 `[I]` ([§ 4](../findings/player/0001-creation.md#4-starting-skills)) | [Skills](Skills.md) `skill`, matched case-insensitively (or `skilldesc`, notes) | [C] |
| `Skill 1`..`Skill 10` | str: 1–6 `Throw`, `Kick`, `Scroll of Identify`, `Book of Identify`, `Scroll of Townportal`, `Book of Townportal`; 7–9 `Unsummon`, `Left Hand Throw`, `Left Hand Swing` or blank; 10 blank | `+0x0AE + 2(k−1)` u16 row index, blank → `0xFFFF` | skills added at level 1 after Attack (skill 0), in column order, valid ids only; blank = −1 `[I]` ([§ 4](../findings/player/0001-creation.md#4-starting-skills)) | [Skills](Skills.md) `skill` | [C] |
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
  computes is in [player/0001 § 3](../findings/player/0001-creation.md#3-starting-attributes--player_initbasestats-0x005706d0) and [§ 4](../findings/player/0001-creation.md#4-starting-skills): `StartSkill` is the right-mouse default granted through
  `item1`'s `item_singleskill`, not a skill point `[I]`.
- **The "fourths".** The `Comment` column says the next columns are in fourths; at level 1 nothing shows it, since
  life is `vit + hpadd` in whole points. `[I]` The code multiplies each per-level and per-point column by 64 into the
  1/256 fixed point of life, mana and stamina, so the unit is a quarter point ([player/0001 § 7](../findings/player/0001-creation.md#7-level-up--player_levelup-0x00570880)).
- **Same cells, two columns.** `StaminaPerLevel` and `StaminaPerVitality` hold the same cell in every row, so the data
  cannot say which of `+0x044`/`+0x047` is which. `[C]` The loader's field descriptor puts `StaminaPerLevel` at
  `+0x044` and `StaminaPerVitality` at `+0x047`, the `.txt` order (fn:CHARSTATS_LoadTable@0x00613260,
  [player/0001 § 3](../findings/player/0001-creation.md#3-starting-attributes--player_initbasestats-0x005706d0)).
- **`StartSkill` resolves either way on the data.** Its two cells are lower-case (`fire bolt`, `raise skeleton`), as in
  `skilldesc.txt`'s key; they resolve to the same index (36, 70) through `skills.txt` `skill` matched without case,
  and `skilldesc` rows 36 and 70 are those skills' descriptions. `[I]` The compiler reads `skills`: `StartSkill` is a
  name-lookup descriptor entry (type `0x14`, stored as a word) on the `skills` name link, like `Skill 1..10`
  ([player/0001 § 9](../findings/player/0001-creation.md#9-other-charstats-readers-for-the-archivists-table-doc), fn:CHARSTATS_LoadTable@0x00613260, 0x006136E5–0x00613705).
- **`+0x000`..`+0x01F` are zero** in every record and have no column. `[I]` They are filled at load: right after
  the table load `CHARSTATS_LoadTable` calls `sub_00612600_RecWideNameFill`, which clears the field, looks the `class`
  text (`+0x020`) up in the string tables and copies the result as UTF-16 (at most 16 units), or a fallback built
  from the key when it is not found ([player/0001 § 9](../findings/player/0001-creation.md#9-other-charstats-readers-for-the-archivists-table-doc), fn:sub_00612600_RecWideNameFill@0x00612600, call at 0x00613D23).

## Open questions

- `[L]` `PercentStr..PercentVit`: no server reader found; the client getter `0x004833E0` was not followed
  ([player/0001 § Open questions](../findings/player/0001-creation.md#open-questions)).
- Answered `[C]` by run:2026-10-16-combat ([combat/0001 § 15](../findings/combat/0001-formulas.md#15-phase-2-per-event-reproduction-run2026-10-16-combat)):
  `ToHitFactor` is an attack-rating term only (`(dex − 7)·5 + stat 19 + ToHitFactor`, 1 974 player attacks,
  Sorceress −15, Barbarian +20), not an attacker-level bonus in the chance-to-hit code; the reading of
  src:arreat-summit-character-basics is contradicted (fn:sub_00622560_PlayerBaseToHit@0x00622560,
  fn:COMBAT_ToHitRoll@0x0057D9B0).
- Answered `[I]` by [player/0001 § 9](../findings/player/0001-creation.md#9-other-charstats-readers-for-the-archivists-table-doc): `StartSkill` compiles through `skills`, and `+0x000`..`+0x01F` hold the
  class's UTF-16 display name filled at load (Interpretation notes).

# Shrines (`data/global/excel/shrines.txt` → `shrines.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 23 (no `Expansion` marker)   **Record:** 184 B (`0xB8`)
> **sha256:** `.txt` `1dae6107c983c5e03079ac6916cf77a3d828df4b2a0517818504dcf20a68fb6d`, `.bin` `2a7e6f8f0cc8c8743f4d7971c31b80c3083cef846ff8100598944c71b0ab0678`
> **Doc status:** complete for layout (every byte placed); every effect row listed (plan 0041 Phase 0); semantics `[I]` for the pick ([§ Code semantics](#code-semantics-plan-0023-phase-1), objects/0001), `[I]` for the timed and recharge effects and row 20 (plan 0041 Phase 1, § Effects), `[L]` for the other magic effects

## Purpose

One row per shrine effect: `Refill`, `Health Boost`, `Armor Boost`, `Experience Boost`, `Gem Upgrade`, `Exploding
Shrine`, … (row 0 is `None`). A row gives the effect's two arguments, its duration, the time before the shrine can be
used again, a `rarity` and a minimum level. The shrine objects (Objects `SubClass` bit 0, [Objects](Objects.md)) are
created with one of these effects. How the effect is picked is in [§ Code semantics](#code-semantics-plan-0023-phase-1); what the effect does is game simulation (ADR-0002) and is only named. Leads:
no lead read (`src:d2dfg-blizzard` § Shrines is for Phase 1b).

## Row identity

- `[C]` The `.bin` is a u32 record count (23) and 23 records of 184 bytes, one per `.txt` row in order. The loader passes
  record size 184 (0x00641493, [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[C]` `Code` equals the row index in all 23 rows (`SURVEY obj_shrines … code_is_index=23`). `[L]` it is the effect
  number the shrine object stores.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel shrines`: 23 records × 10 mapped
fields = 230 cells, **0 mismatches**; `excel_bin.py unknown … shrines` lists only `+0x0B3` (1 B, zero in every record).
Values from `python3 -I tools/obj_survey.py shrines workspace/merged/data/global/excel`. No blank cell.

| Column | Observed type / range | `.bin` field | Meaning (`[L]` unless stated) | References | Layout tag |
|---|---|---|---|---|---|
| `Shrine Type` | str {Booster 10, Magic 7, Recharge 5, None 1} | — | editor grouping | — | [C] |
| `Shrine name` | str, 23 distinct | — | editor name | — | [C] |
| `Effect` | str, 23 distinct | — | editor description | — | [C] |
| `Code` | int 0..22 = row index | `+0x000` u32 | effect number | — | [C] |
| `Arg0` | int 0..400 (8 distinct) | `+0x004` s32 | first effect argument | — | [C] |
| `Arg1` | int 0..2000 (9 distinct) | `+0x008` s32 | second effect argument | — | [C] |
| `Duration in frames` | int {0: 13, 3600: 5, 2400: 4, 4800: 1} | `+0x00C` u32 | `[I]` duration of the timed state, in frames (§ Effects) | — | [C] |
| `reset time in minutes` | int {5: 11, 0: 10, 2: 2} | `+0x010` u8 | `[I]` the shrine re-arms `value × 1200 + 1` frames after use; 0 = never (§ Effects) | — | [C] |
| `rarity` | int {2: 12, 3: 9, 1: 2} | `+0x011` u8 | `[I]` not read by the shrine pick | — | [C] |
| `view name` | str `blah` in every row | `+0x012` `char[32]` | unused text | — | [C] (width by next field) |
| `niftyphrase` | str `blah` in every row | `+0x032` `char[128]` | unused text | — | [C] (width by next field) |
| `effectclass` | int {4: 11, 1: 7, 2: 2, 3: 2, 0: 1} | `+0x0B2` u8 | `[I]` the pick list the row is in (§ Code semantics); `[C]` by data it follows `Shrine Type`: Booster → 4, Magic → 1, None → 0, Recharge → 2 (Health Boost, Health Exchange), 3 (Mana Boost, Mana Exchange) or 4 (Refill) | — | [C] |
| — | — | `+0x0B3` u8 | zero in every record | — | [C] value |
| `LevelMin` | int 0..32 (1: 11) | `+0x0B4` u32 | `[I]` lowest Levels `Id` at which the effect can be picked | — | [C] |

`[C]` `view name` and `niftyphrase` hold the same value in every row, so `probe` places them only as a pair at
`+0x012`/`+0x032`; the order follows the `.txt`, and the widths follow from the next field. `effectclass` is placed as a
u8; a u16 at `+0x0B2` would decode the same values (`+0x0B3` is 0 everywhere).

## Effects (plan 0041 Phase 0)

Every row with the columns a shrine operate is expected to read: the code, the two arguments, the duration and the
class (all `[C]` layout, § Columns). From `python3 -I tools/stats_survey.py shrines workspace/merged/data/global/excel`
(gate survey `stats`; `tools/obj_survey.py shrines` prints the same values). Effect names are the `.txt` editor names.
What the timed and recharge effects do is read by plan 0041 Phase 1 (`[I]`, the bullets below the table, from
[stats/0002 § 5](../findings/stats/0002-states.md#5-shrines-and-wells)); the magic effects, which create missiles, objects or monsters, are not read, except the
function of row 20. (tbl:Shrines.txt:Arg0, tbl:Shrines.txt:Duration in frames)

| `Code` | Name | `Shrine Type` | `Arg0` | `Arg1` | Duration (frames) | reset | `rarity` | `effectclass` | `LevelMin` | [States](States.md) row (`[I]`, `g_ShrineEffects`) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | None | None | 100 | 100 | 0 | 2 | 1 | 0 | 0 | — |
| 1 | Refill | Recharge | 100 | 100 | 0 | 2 | 1 | 4 | 1 | — |
| 2 | Health Boost | Recharge | 200 | 400 | 0 | 5 | 2 | 2 | 1 | — |
| 3 | Mana Boost | Recharge | 200 | 400 | 0 | 5 | 2 | 3 | 1 | — |
| 4 | Health Exchange | Recharge | 50 | 500 | 0 | 0 | 3 | 2 | 2 | — |
| 5 | Mana Exchange | Recharge | 50 | 500 | 0 | 0 | 3 | 3 | 2 | — |
| 6 | Armor Boost | Booster | 100 | 1 | 2400 | 5 | 2 | 4 | 5 | 128 `shrine_armor` |
| 7 | Combat Boost | Booster | 200 | 200 | 2400 | 5 | 2 | 4 | 8 | 129 `shrine_combat` |
| 8 | Resist Fire Boost | Booster | 75 | 0 | 3600 | 5 | 2 | 4 | 5 | 131 `shrine_resist_fire` |
| 9 | Resist Cold Boost | Booster | 75 | 0 | 3600 | 5 | 2 | 4 | 26 | 132 `shrine_resist_cold` |
| 10 | Resist Lightning Boost | Booster | 75 | 0 | 3600 | 5 | 2 | 4 | 32 | 130 `shrine_resist_lightning` |
| 11 | Resist Poison Boost | Booster | 75 | 0 | 3600 | 5 | 2 | 4 | 21 | 133 `shrine_resist_poison` |
| 12 | Skill Boost | Booster | 2 | 0 | 2400 | 5 | 2 | 4 | 1 | 134 `shrine_skill` |
| 13 | Recharge Boost | Booster | 400 | 0 | 2400 | 5 | 2 | 4 | 1 | 135 `shrine_mana_regen` |
| 14 | Stamina Boost | Booster | 200 | 0 | 4800 | 5 | 3 | 4 | 1 | 136 `shrine_stamina` |
| 15 | Experience Boost | Booster | 50 | 50 | 3600 | 0 | 3 | 4 | 1 | 137 `shrine_experience` |
| 16 | Shrine of Enirhs | Magic | 0 | 0 | 0 | 0 | 3 | 1 | 1 | — |
| 17 | Portal to unknown | Magic | 0 | 0 | 0 | 0 | 2 | 1 | 3 | — |
| 18 | Gem Upgrade | Magic | 0 | 0 | 0 | 0 | 3 | 1 | 4 | — |
| 19 | Storm Shrine | Magic | 50 | 2000 | 0 | 0 | 2 | 1 | 1 | — |
| 20 | Warping Shrine | Magic | 0 | 0 | 0 | 0 | 3 | 1 | 3 | — |
| 21 | Exploding Shrine | Magic | 5 | 10 | 0 | 0 | 3 | 1 | 1 | — |
| 22 | Poison Shrine | Magic | 5 | 10 | 0 | 0 | 3 | 1 | 1 | — |

- `[C]` Ten rows have a duration, codes 6–15 (`shrine_timed`): 2400 frames on 6, 7, 12, 13, 3600 on 8–11 and 15, 4800 on 14. 19 rows have a non-zero `Arg0`, 12 a non-zero `Arg1`
  (`shrine_arg0_nonzero`, `shrine_arg1_nonzero`). (tbl:Shrines.txt:Duration in frames)
- `[C]` (data) The last column pairs a timed code with the States row of the same name (`shrine_pairs` = 10; the state
  is code + 122 for 7 of them; fire, cold and lightning are in another order: [States § Which data names a row](States.md#which-data-names-a-row)).
  `[I]` The code confirms the pairing for all ten: `OBJOP_Shrine` (OperateFn 2) runs `g_ShrineEffects[Code]`, a table
  of `{fn, stat, state}` rows: 6 → stat 171 `skill_armor_percent`, state 128; 7 → state 129; 8 → 39, 131; 9 → 43, 132;
  10 → 41, 130; 11 → 45, 133; 12 → state 134 (its stat is not read); 13 → 27, 135; 14 → 162, 136; 15 → 85, 137. The
  stat is not always the States row's `stat`: shrine 6 writes 171 although row 128 names `armorclass`.
  ([stats/0002 § 5](../findings/stats/0002-states.md#5-shrines-and-wells), fn:OBJOP_Shrine@0x00583C70, data:g_ShrineEffects@0x006E1850)
- `[I]` **`Arg0` is the stat value of codes 6, 8–11, 13 and 15** (armour 100, resists 75, mana regeneration 400,
  experience 50): `SHRINE_StatValue` returns `Arg0` itself for their stats. **`Arg1` is code 7's damage percent**
  (stat 25 `damagepercent` = 200), and code 7 adds a to-hit value worked out from the right skill. Code 14 sets
  stamina to its maximum and writes stat 162 = `stat 162 × Arg0 / 100`, stat 10 twice that and 28 = 1000; code 12
  writes no stat and refreshes the skills. Each timed state lasts `Duration in frames`. ([stats/0002 § 5](../findings/stats/0002-states.md#5-shrines-and-wells),
  fn:SHRINE_StatValue@0x00583840, fn:SHRINE_Combat@0x005839B0, fn:SHRINE_Stamina@0x00583A70, tbl:Shrines.txt:Arg0)
- `[I]` **Recharge codes 1–5:** 1 refills life and mana, 2 life, 3 mana; 4 takes `h = ⌊Arg0·⌊life/256⌋/100⌋` points of
  life and gives `⌊Arg1·h·256/100⌋` mana; 5 takes `m = ⌊Arg0·mana/100⌋` mana and gives `⌊Arg1·m/100⌋` life (unsigned).
  A code with no function falls back to `SHRINE_Refill`. ([stats/0002 § 5](../findings/stats/0002-states.md#5-shrines-and-wells), fn:SHRINE_HealthExchange@0x00582940,
  fn:SHRINE_ManaExchange@0x005829A0)
- `[I]` **`reset time in minutes` (`reset`) re-arms the shrine** `reset × 1200 + 1` frames after use (object event 5), when `reset` ≠ 0 (6000 + 1
  frames for `reset` 5); one unit of the column is 1200 frames whatever its header says. The `+ 1` is the event
  queue's next frame, as for the wells' `Parm0`. ([stats/0002 § 5](../findings/stats/0002-states.md#5-shrines-and-wells),
  fn:OBJOP_Shrine@0x00583C70, tbl:Shrines.txt:reset)
- `[I]` **Row 20 (Warping Shrine)** runs `sub_00583050_ShrineWarping` (`g_ShrineEffects` row at `0x006E1940`): it finds
  the operator's nearest unit through filter `0x00582750` and makes it a special monster (`MonMakeSpecial`); with no
  hit nothing happens. ([monsters/0003 § Plan 0039 batch P1c](../findings/monsters/0003-special-monsters.md#plan-0039-batch-p1c-2026-10-17), fn:sub_00583050_ShrineWarping@0x00583050)
- `[L]` By the names, codes 16–19, 21 and 22 are the magic class (portal, gem, storm, explosion, poison) that create
  objects, missiles or monsters; their functions are not read.
- `[C]` `rarity` sums to 53 over the 23 rows (1 on rows 0 and 1, 3 on rows 4, 5, 14–16, 18, 20–22, else 2).
- `[C]` `LevelMin` is above 8 only for the three resist boosts other than fire: cold 26, poison 21, lightning 32.

## Code semantics (plan 0023 Phase 1)

From [objects/0001 §§ 1, 7](../findings/objects/0001-object-population.md#7-the-initfn-draws) (static reading; `[I]`).

- `[I]` **`effectclass` selects the pick list.** `OBJRGN_Create` builds, once per game, eight lists of Shrines codes, one
  per `effectclass` (values below 8), each in record order. `InitFn` 1 (every shrine row) chooses the class from the
  object's Objects `Parm0`: 1 → class 2 (health), 2 → class 3 (mana), any other value → one object-region draw,
  `low mod 10 = 0` → class 1 (magic), else class 4 (boosters and `Refill`). Class 0, which holds row 0 (`None`), is never
  asked for, so `None` is never picked. (fn:OBJRGN_Create@0x00546C60, fn:OBJINIT_Shrine@0x0054F9D0, tbl:Shrines.txt:effectclass,
  tbl:Objects.txt:Parm0)
- `[I]` **The pick is uniform within the class**: up to 8 tries of `list[RangeB(O, n)]` until `LevelMin ≤` the room's
  level. **`rarity` is not read.** (fn:OBJ_ShrinePick@0x0054F770, tbl:Shrines.txt:rarity)
- `[I]` **`LevelMin` is compared with the Levels `Id`** of the room (`RoomGetLevelId`), not with a monster or character
  level. So Resist Cold (26), Resist Poison (21) and Resist Lightning (32) appear only in levels whose id reaches those
  values. (tbl:Shrines.txt:LevelMin)
- `[I]` **Rewrites after the pick:** codes 4 and 5 (Health Exchange, Mana Exchange) become 2 and 3, and 16 (Enirhs)
  becomes 18, so a populate pass never places those three. A forced health shrine (the level rule of
  [ObjGroup § Code semantics](ObjGroup.md#code-semantics-plan-0023-phase-1)) is set to code 2.
  (fn:OBJINIT_Shrine@0x0054F9D0, fn:OBJ_ShrineClassSubst@0x00552AC0)
- `[I]` The DS1 fixed shrines (pseudo-objects 574–579, class 136 with a code range) would bypass the pick, but no stock
  DS1 places them ([Objects § DS1 survey](Objects.md#ds1-survey-objects-269-397-455-and-the-pseudo-objects-plan-0023-phase-1-follow-up),
  fn:OBJ_PresetFixedShrine@0x0054F0D0).

## Interpretation notes

- The names suggested a pick weighted by `rarity`; the code picks uniformly within the `effectclass` list chosen by
  Objects `Parm0` and ignores `rarity` ([§ Code semantics](#code-semantics-plan-0023-phase-1)).

## Open questions

- ~~Which level `LevelMin` compares against, how `rarity` enters the pick, whether row 0 can be picked, and whether
  `effectclass` or Objects `Parm0` restricts the pick~~ answered by objects/0001 (§ Code semantics).
- `[L]` A shrine row with `Parm0` 0 (uniform pick over all codes, against the guide's health shrine): unreachable with
  stock data.

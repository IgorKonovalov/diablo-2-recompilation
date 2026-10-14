# ObjGroup (`data/global/excel/objgroup.txt` → `objgroup.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 133 (the `EXPANSION` separator row is compiled and counted)   **Record:** 52 B (`0x34`)
> **sha256:** `.txt` `6fd55a75ee1a36e00dbc25074d3cc5da2b8892fff00f8cda520da5330111e58f`, `.bin` `b967a78f273a5d10c2fb24e2a7bea7ed8d8671cb34af2452fbe810bba8f39566`
> **Doc status:** complete for layout (every byte placed); semantics `[L]` (plan 0023 Phase 1 reads `RoomObjectsPopulate`)

## Purpose

One row per object group: up to eight object classes (`ID0..7`, rows of [Objects](Objects.md)), each with a pick weight
(`PROB0..7`) and a density (`DENSITY0..7`), and two flags, `SHRINES` and `WELLS`. A level names up to eight groups in
its [Levels](Levels.md) `ObjGrp0..7` columns, each with a chance `ObjPrb0..7`. `[I]` The object population of a fresh room
makes one room-seed draw per Levels slot (eight) and one more per group that passes its chance, plus the creators' draws
([monsters/0002 § 1](../findings/monsters/0002-room-population.md), fn:sub_00552610_RoomObjectsPopulate@0x00552610).
What the draw is compared with, how a member is picked and how many are placed is plan [0023](../plans/0023-objects.md)
Phase 1. Leads: no lead read (`src:d2dfg-blizzard` § ObjGroup is for Phase 1b).

## Row identity

- `[C]` The `.bin` is a u32 record count (133) and 133 records of 52 bytes, one per `.txt` row in order. The loader
  passes record size 52 (0x006412E0, [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[C]` **The separator row is a record.** It is spelled `EXPANSION` (upper case), not `Expansion`, and the compiler
  keeps it: record 97 is all zero. ([excel-bin.md](../formats/excel-bin.md) drops only rows whose first field is
  exactly `Expansion`; `tools/excel_bin.py` follows the same rule and the diff is clean with record 97 present.)
- `[C]` `Offset` equals the row index on every row but the `EXPANSION` row, where it is blank; it is not compiled. `[I]`
  [Levels](Levels.md) `ObjGrp0..7` (u8, `+0x0E5`..) hold these row indices: the eight values per level are 0..129, all
  below 133, and no level names record 97 (`python3 -I tools/obj_survey.py levels`, below). `[L]` that the code indexes
  the table by them (Phase 1).
- `[C]` `GroupName` is not unique (102 distinct; `dummy` 21, `not used` 8) and not compiled.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel objgroup`: 133 records × 26 mapped
fields = 3 458 cells, **0 mismatches**; `excel_bin.py unknown … objgroup` lists only `+0x032` (2 B, zero in every
record). Ranges are from the `.txt`; the one blank cell per column is the `EXPANSION` row (stored 0).

| Column | Observed type / range | `.bin` field | Meaning (`[L]` unless stated) | References | Layout tag |
|---|---|---|---|---|---|
| `GroupName` | str ≤ 41 chars, 102 distinct | — | editor name | — | [C] |
| `Offset` | int 0..132 = row index | — | editor row number | — | [C] |
| `ID0..ID7` | int 0..556 | `+0x000 + 4k` u32 | object class of member k (an [Objects](Objects.md) record index) | `objects` row | [C] |
| `DENSITY0..DENSITY7` | int 0..125 (30: 217 member slots, 0: 99, 48, 64, 80, 120, 125, 16, 50) | `+0x020 + k` u8 | how densely member k is placed | — | [C] (6/7 by stride) |
| `PROB0..PROB7` | int 0..100 | `+0x028 + k` u8 | pick weight (%) of member k within the group | — | [C] |
| `SHRINES` | int {0: 108, 1: 24} | `+0x030` u8 | the group places shrines | — | [C] |
| `WELLS` | int {0: 124, 1: 8} | `+0x031` u8 | the group places wells | — | [C] |
| — | — | `+0x032` u16 | zero in every record (no `.txt` column) | — | [C] value |

`[C]` `DENSITY6` and `DENSITY7` are equal in every row (30 on one group, else 0), so `probe` places them only as a pair;
their slots follow the stride of `DENSITY0..5`.

## Survey: the groups the levels use

One command prints, for every level, its eight slots with group, chance and member list:

```
python3 -I tools/obj_survey.py levels workspace/merged/data/global/excel
python3 -I tools/obj_survey.py groups workspace/merged/data/global/excel
```

`levels` ends with `SURVEY obj_levels levels=137 levels_with_groups=123 slots_used=476 slots_out_of_range=0`,
`groups` with `SURVEY obj_groups groups=133 groups_used=93 groups_unused=40 shrines=24 wells=8 members_0=34 members_1=17
members_2=24 members_3=12 members_4=15 members_5=23 members_6=4 members_8=4 probsum_over_100=1`. A slot is "used" when
its `ObjGrp` or `ObjPrb` is non-zero; a member is used when its `ID` or `PROB` is non-zero.

Illustration (level 2, Blood Moor; the first four slots, the other four are 0/0):

| Slot | `ObjGrp` | `GroupName` | `ObjPrb` | Members (`ID` Objects name, `DENSITY`, `PROB`) |
|---|---|---|---|---|
| 0 | 4 | Rogues for act1 w/o staked rogues | 3 | 54 RogueCorpse 30 37 · 55 RogueCorpse 30 37 · 56 RogueCorpse 30 26 |
| 1 | 38 | outside forest object 3 | 17 | 155 hidden stash 30 34 · 174 loose rock 30 33 · 175 loose boulder 30 33 |
| 2 | 33 | outsideforestobj1 | 17 | 139 chest 30 25 · 140 chest 30 50 · 144 chest 30 25 |
| 3 | 34 | outsideforestobj2 | 17 | 141 chest 30 50 · 139 chest 30 50 |

Facts from the survey (`[C]` by data):

- **Per difficulty.** Levels has one `ObjGrp0..7`/`ObjPrb0..7` set per row and no `(N)`/`(H)` variant, so the table
  gives every difficulty the same groups and chances. `[L]` whether the code adjusts them by difficulty (Phase 1).
- **Slots per level.** 14 of 137 levels use no slot (level 0, the five towns, Burial Grounds 17, Forgotten Tower 20,
  Monastery Gate 26, Inner Cloister 32, Duriel's Lair 73, Rocky Summit 120, Nihlathak's Temple 121, Worldstone
  Chamber 132). The others use 1 (10 levels), 2 (22), 3 (12), 4 (40), 5 (17), 6 (16), 7 (3) or 8 (3) slots, always
  slots 0..n−1 with no gap. `ObjPrb` of a used slot is 0..90 (25 on 101 slots, 35 on 52, 30 on 38).
- **Odd slots.** 13 slots name group 0 (`Not Used`, all zero) with a non-zero `ObjPrb` (levels 38, 55–61, 84, 85, 92,
  93, 136); levels 86–91 name group 72 (`not used`, no member); levels 41–46 and 134 name group 30 (`Desert Wells`, no
  member, `WELLS` 1). Levels 38 and 136 (Tristram) name group 44 in slot 0 with `ObjPrb` 0.
- **Groups.** 93 of 133 groups are named by some level. The 40 others are the 21 `dummy` rows, the `EXPANSION` row,
  seven `not used` rows (20, 21, 39, 41, 54, 63, 71), and 11 named groups no level uses (11–13 `Forgotten Tower caskets/Shrines/Barrels`, 18, 22, 23
  `Desert … Shrines`, 25 `maggot lair shrines`, 27, 28 obelisks, 73 `act 2 Harum bed`, 98 `level1 fire`).
- **Members.** 34 groups have no member, the others 1 to 8 (four groups, 18, 50, 51 and 55, use all eight). Member slots are filled from
  slot 0 up except in group 69 (slot 0 empty, members in 1..4). Group 2 member 1 has `ID` 164 with `PROB` 0. 247
  distinct object classes are members, the largest id 556; none is past the 573 Objects records.
- **`PROB` sums.** Of the 93 groups in use, 66 sum to 100, 3 to 0 (no member), the rest to 20..99. Only group 23
  (unused) sums to more than 100 (102).
- **`SHRINES` and density.** All 83 member slots of the 24 groups with `SHRINES` 1 have `DENSITY` 0 (they hold shrine
  and well objects, Objects `SubClass` bits 0 and 5). The expansion shrine groups (99, 104, 108, 110, 112, 113, 116,
  119, 121, 124) have `SHRINES` 0 and `DENSITY` 30 on their shrine members. Besides 0 and 30, `DENSITY` is 48 (chests
  of groups 3 and 9), 64 (`Barrel`), 80 (caskets of group 16), 120 (`LargeUrn`), 125 (`Casket`, `HoleAnim`), 16
  (`skullpile`) and 50 (a `dummy`).

## Interpretation notes

- `[L]` The column names suggest: a level slot k passes with chance `ObjPrb<k>`; the group then picks a member by
  `PROB` and places it with a count or spacing taken from `DENSITY`; `SHRINES`/`WELLS` mark groups whose members are
  shrines or wells, maybe placed by a separate rule (their `DENSITY` is 0). None of this is read yet: plan 0023 Phase 1
  states the comparison, the pick, the count and the role of the flags.

## Open questions

- `[L]` The role of `DENSITY` (count per room, spacing, or a chance), and why it is 0 on every member of a `SHRINES`
  group. Reverser, plan 0023 Phase 1.
- `[L]` What `SHRINES` and `WELLS` change, and what the populate pass does with a group that has no member (group 0,
  30, 72 above) or a member with `PROB` 0.
- `[L]` Whether `PROB` is a weight over the members' sum or a percentage against 100 (sums below 100 occur in 24 used
  groups).

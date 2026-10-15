# ObjGroup (`data/global/excel/objgroup.txt` → `objgroup.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 133 (the `EXPANSION` separator row is compiled and counted)   **Record:** 52 B (`0x34`)
> **sha256:** `.txt` `6fd55a75ee1a36e00dbc25074d3cc5da2b8892fff00f8cda520da5330111e58f`, `.bin` `b967a78f273a5d10c2fb24e2a7bea7ed8d8671cb34af2452fbe810bba8f39566`
> **Doc status:** complete for layout (every byte placed); semantics from [objects/0001](../findings/objects/0001-object-population.md) (plan 0023 Phase 1): § Code semantics

## Purpose

One row per object group: up to eight object classes (`ID0..7`, rows of [Objects](Objects.md)), each with a pick weight
(`PROB0..7`) and a density (`DENSITY0..7`), and two flags, `SHRINES` and `WELLS`. A level names up to eight groups in
its [Levels](Levels.md) `ObjGrp0..7` columns, each with a chance `ObjPrb0..7`. `[I]` The object population of a fresh room
makes one room-seed draw per Levels slot (eight) and one more per group that passes its chance, plus the creators' draws
([monsters/0002 § 1](../findings/monsters/0002-room-population.md), fn:sub_00552610_RoomObjectsPopulate@0x00552610).
What the draw is compared with, how a member is picked and how many are placed is in
[§ Code semantics](#code-semantics-plan-0023-phase-1). Leads: no lead read (`src:d2dfg-blizzard` § ObjGroup is for Phase 1b).

## Row identity

- `[C]` The `.bin` is a u32 record count (133) and 133 records of 52 bytes, one per `.txt` row in order. The loader
  passes record size 52 (0x006412E0, [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[C]` **The separator row is a record.** It is spelled `EXPANSION` (upper case), not `Expansion`, and the compiler
  keeps it: record 97 is all zero. ([excel-bin.md](../formats/excel-bin.md) drops only rows whose first field is
  exactly `Expansion`; `tools/excel_bin.py` follows the same rule and the diff is clean with record 97 present.)
- `[C]` `Offset` equals the row index on every row but the `EXPANSION` row, where it is blank; it is not compiled. `[I]`
  [Levels](Levels.md) `ObjGrp0..7` (u8, `+0x0E5`..) hold these row indices: the eight values per level are 0..129, all
  below 133, and no level names record 97 (`python3 -I tools/obj_survey.py levels`, below). `[I]` The code indexes the
  table by them (`OBJGROUP_GetRecord(ObjGrp[k])`, fn:sub_00552610_RoomObjectsPopulate@0x00552610).
- `[C]` `GroupName` is not unique (102 distinct; `dummy` 21, `not used` 8) and not compiled.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel objgroup`: 133 records × 26 mapped
fields = 3 458 cells, **0 mismatches**; `excel_bin.py unknown … objgroup` lists only `+0x032` (2 B, zero in every
record). Ranges are from the `.txt`; the one blank cell per column is the `EXPANSION` row (stored 0).

| Column | Observed type / range | `.bin` field | Meaning (`[L]` unless stated) | References | Layout tag |
|---|---|---|---|---|---|
| `GroupName` | str ≤ 41 chars, 102 distinct | — | editor name | — | [C] |
| `Offset` | int 0..132 = row index | — | editor row number | — | [C] |
| `ID0..ID7` | int 0..556 | `+0x000 + 4k` u32 | `[I]` object class of member k (an [Objects](Objects.md) record index) | `objects` row | [C] |
| `DENSITY0..DENSITY7` | int 0..125 (30: 217 member slots, 0: 99, 48, 64, 80, 120, 125, 16, 50) | `+0x020 + k` u8 | `[I]` count factor of member k's scatter handlers; ≥ 128 fatal (§ Code semantics) | — | [C] (6/7 by stride) |
| `PROB0..PROB7` | int 0..100 | `+0x028 + k` u8 | `[C]` member k's share of a cumulative pick against 100 (§ Code semantics) | — | [C] |
| `SHRINES` | int {0: 108, 1: 24} | `+0x030` u8 | `[I]` not read by the populate pass | — | [C] |
| `WELLS` | int {0: 124, 1: 8} | `+0x031` u8 | `[I]` not read by the populate pass | — | [C] |
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
  gives every difficulty the same groups and chances; `[I]` the slot loop reads no difficulty (objects/0001 § 3).
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

## Code semantics (plan 0023 Phase 1)

From [objects/0001 § 3](../findings/objects/0001-object-population.md#3-the-slot-loop) and § 4. Per the architect's
ruling (plan 0023 log), the replay of run:2026-10-14-objects-window corroborates (`[C]`) only what it fixes exactly: the
slot loop, the room-seed draws of the shrine, well and trap handlers, and the restore drawing nothing. The plan 0023
Phase 2 run (run:2026-10-15-objects, 0 mismatches in 142 540 checks,
[objects/0001 § 12](../findings/objects/0001-object-population.md#12-phase-2-the-bit-exact-run)) confirms the readers
it exercised, marked `[C]` below; the rest stays `[I]`.

- `[C]` **Slot k** of a level: one room-seed draw `r = low mod 100` for every slot, group 0 included; the slot passes
  when `ObjGrp[k] ≠ 0` and `r ≤ ObjPrb[k]`. (fn:sub_00552610_RoomObjectsPopulate@0x00552610, tbl:Levels.txt:ObjPrb0,
  run:2026-10-14-objects-window)
- `[C]` **`PROB` is cumulative against 100**, not a weight over the members' sum: a passing slot makes a second draw
  `r2 = low mod 100`, walks `ID0..7` up to the first `ID` 0 summing `PROB`, and takes the first member with
  `r2 < sum`. When the sum is at most `r2` nothing is placed (259 of 2307 passing slots in the run), so the 24 used groups
  that sum below 100 place nothing with chance `(100 − sum)` %. A member with `PROB` 0 is never picked.
  (tbl:ObjGroup.txt:PROB0, run:2026-10-14-objects-window)
- `[C]` **`ID`** is the [Objects](Objects.md) record index (the class), and the member's `PopulateFn` handler is called
  with the member's `DENSITY`, its class and the probability 100 (the handler redraws it, so that draw always passes
  but is still made). (data:g_ObjPopulateFns@0x00731D00, run:2026-10-15-objects)
- `[I]` A member whose `Gore` exceeds the gore limit (2) is skipped; stock `Gore` is 0 or 1, so the test never
  excludes. (tbl:Objects.txt:Gore, data:g_ObjGoreLimit@0x00731BBC)
- `[C]` **`DENSITY` is a count factor** for the handlers that scatter: for a room of `w × h` subtiles the count is
  `((w·h >> 7) · DENSITY) >> 8` (signed shifts). The shrine, stick-corpse and well handlers ignore it, which is why
  every member of a `SHRINES` group has `DENSITY` 0. (fn:OBJPOP_Scatter@0x00551470, fn:OBJPOP_Clusters@0x00550C20,
  tbl:ObjGroup.txt:DENSITY0, run:2026-10-15-objects) `[I]` **`DENSITY` ≥ 128 (`0x80`) is fatal**, so the stock maximum
  125 is just under the limit of 127 (no stock row reaches it).
- `[I]` **`SHRINES` and `WELLS` are not read** by the populate pass: what makes a member a shrine or a well is its
  Objects `PopulateFn` (2, 8). (fn:sub_00552610_RoomObjectsPopulate@0x00552610, tbl:ObjGroup.txt:SHRINES)
- `[I]` Group 0 and the memberless groups 30 and 72 cost their draws and place nothing; group 69 starts with an empty
  member slot, so the walk ends at once and it never places.
- `[C]` **A game bug the spec keeps** (architect ruling (2), plan 0023 log): the forced-slot rule tests
  `Objects[group index].SubClass`, the Objects record whose index is the **group number**, not a member. The rule
  (`r` forced to 100 once 75 % of a level's rooms are gated and no code-2 shrine stands) was reached in plan 0023
  Phase 2: the counters matched at every slot and one slot was forced directly (Sewers level 2, slot 2, group 5). The
  slots it can suppress are those whose group index is 1–6, 50–53, 59, 60, 77, 109, 116, 119, 120, 123, 124 or 129.
  (0x005526CC, fn:OBJRGN_GetLevel@0x00546F90, run:2026-10-14-objects-window, run:2026-10-15-objects)
- `[C]` **Slot coverage of run:2026-10-15-objects.** The run drew 86 level slots with `ObjPrb` > 0 in the gated levels.
  Unreached (not contradicted): level 11 (groups 6, 4), 30 (51, 15, 3), 38 (45), 48 (26, 5), 62 (29), 92 (65), 110
  (100, 101, 106) and 125 (49); the run record lists them
  ([objects/experiments § run:2026-10-15-objects](../findings/objects/experiments.md#run2026-10-15-objects)).

## Interpretation notes

- The column names suggested a weight pick by `PROB` and a separate rule for `SHRINES`/`WELLS`; the code reads
  `PROB` cumulatively against 100 and ignores both flags ([§ Code semantics](#code-semantics-plan-0023-phase-1)).

## Open questions

- ~~The role of `DENSITY`; what `SHRINES` and `WELLS` change and what happens with a memberless group or a `PROB` 0
  member; whether `PROB` is a weight or a percentage~~ answered by objects/0001 (§ Code semantics).

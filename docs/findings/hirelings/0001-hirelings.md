# 0001 — Hirelings: the hire list, the hire, the mercenary's stats and its creation from a save

> **Subsystem:** hirelings
> **Question:** Which hirelings does a town's hire list offer (names, types, levels, prices), and how does a hired or loaded mercenary get its state from `Hireling.txt`, its seed and its experience?
> **Date:** 2026-10-15   **Plan:** 0033 (Phase 1, Phase 1b)   **Status:** open (Phase 1 read from the decompile and the disassembly, committed before any community source was read; Phase 1b cross-check added after, with a re-read of every contradicted claim)

Names of structs and fields are ours (`re/types/hireling.h`). Column names are those of the raw `hireling.txt` header:
plan 0033's Phase 0 (`docs/tables/Hireling.md`, `HireDesc.md`) had not landed, so this finding has no `tbl:` anchors
for those two tables. "Version flag" is `Game+0x70` (non-zero in an expansion game: rows with `Version` 100 are used,
else rows with `Version` 0); "difficulty" is `Game+0x6D` (0..2). "NPC seed" is the seed object at
`NpcControl+0x08` (`Game+0x1D24` → `+0x08`), a seed of its own, distinct from the game seed `Game+0xD0`
([rng/0002](../rng/0002-seed-tree.md)). "Step" and `Range` are the RNG primitives of [rng/0001](../rng/0001-rng-core.md)
(`RNG_Range` and `RNG_RangeB` compute the same thing). Names in `string.tbl` and friends are string indices
([data/strings](../../specs/data/strings.md)); the monster side (MonStatsInit, the level step E2) is
[monsters/pool](../../specs/monsters/pool.md) § E.

## Answer (summary)

- [C] **The `hireling` record is 0x118 bytes** with the field offsets of `struct:HirelingRec+0x000` (the loader's
  field descriptor, `Version` u16 at +0x00 … `NameLast` at +0xF3), plus two u16 string indices at +0x114/+0x116 that
  the loader fills from `NameFirst`/`NameLast` with `STRTABLE_GetByKey`. Corroborated by data: decoding the 120
  records of `hireling.bin` at these offsets reproduces every loaded cell of `hireling.txt` (8 280 fields, 0
  mismatches); +0x113 is 0 and +0x114/+0x116 are 0 in every record of the file. (fn:HIRELING_LoadTable@0x00655720,
  fn:STRTABLE_GetByKey@0x00524D30, data:g_pHirelingTxt@0x0096BDD0, data:g_nHirelingTxt@0x0096BDD4)
- [I] **One stock per hireling NPC per game.** The four sellers are Kashya (MonStats 150), Greiz (198), Asheara (252)
  and Qual-Kehk (515). An NPC's hire table is built the first time a player starts an interaction with it
  (`sub_00572C10_NpcInteractStart` → `HIRE_SendList`), and only rebuilt when no listed, unhired entry remains (after a
  hire or a free mercenary). It lives in the game's NPC record, so all players of a game share it.
  (fn:HIRE_SendList@0x00576770, fn:sub_00572C10_NpcInteractStart@0x00572C10, fn:HIRE_RebuildIfEmpty@0x00577010)
- [I] **The build draws `n + 10` times from the NPC seed**, where `n = NameLast − NameFirst + 1` of the seller's
  Normal row (Kashya 41, Greiz 21, Asheara 20, Qual-Kehk 67). First every name index, in order, gets the low word of
  one NPC-seed step as its seed; then 10 picks `Range(n)` each mark one entry listed, stepping +1 (wrapping) past
  entries already listed or hired. The list is 10 distinct names. (fn:HIRE_BuildStock@0x00576070,
  fn:HIRE_GetNameRange@0x00575FF0, fn:RNG_Range@0x0045C390)
- [I] **The NPC seed is `Init(low)` of one game-seed step taken at game creation**, right after the object-region
  step, so it is game-seed draw 3 under `-seed N`. Vendor code of the same NPCs draws from it too.
  (fn:sub_00536070_NpcRecordsInit@0x00536070, fn:sub_00536B40_NpcSeed@0x00536B40, fn:sub_00530BF0_GameCreate@0x00530BF0)
- [I] **An entry's seed decides its type and level; the player's level at the time decides the rest.**
  `HIRELING_RollEntry(seed, act, difficulty)` does `Init(seed)`, draw 1 `Range(k)` over the `k` rows of
  (version, act, difficulty) that share the first such row's `Level` (one row per type: Rogue fire/cold, the three
  Act II and Act III types, the two Barbarian ids), draw 2 a raw step: `level = max(2, playerLevel − 5 + low mod 5)`.
  Price, experience and the displayed stats are linear in `d = level − row.Level`. (fn:HIRELING_RollEntry@0x006637F0,
  fn:HIRELING_NextByActDiff@0x00656580)
- [I] **The hire stores `{seed, name index, Hireling Id}`** in the player's pet list (pet type 7); the save header
  copies it. The seed is the entry's seed from the stock build; the Id is draw 1 of `RollEntry`. Price is charged
  from inventory gold, then the stash. (fn:HIRE_Hire@0x005770E0, fn:MERC_Init@0x00573270, fn:PETS_Add@0x00575E90,
  fn:sub_00576D90_PayGold@0x00576D90, fn:D2S_WriteMercHeader@0x00568E60)
- [I] **In the world, every stat comes from the row whose `Level` band holds the mercenary's level**
  (`HIRELING_GetRecord(version, id, L)`, the matching row with the greatest `Level` ≤ L), with `d = L − row.Level` and
  signed integer arithmetic: strength, dexterity and damage add `Str/Lvl·d`, `Dex/Lvl·d`, `Dmg/Lvl·d` divided by 8
  (truncated), resistances `Resist/Lvl·d` divided by 4, life, defence and AR add the plain product; clamps 10, 10, 40
  life, 0/1 damage, 0. Skills `Skill1..6` at `Level_i + floor(LvlPerLvl_i·d / 32)`, capped at 32, if the player
  level requirement of the skill (`reqlevel`) is met. (fn:MERC_SetLevel@0x00572840, fn:HIRELING_GetRecord@0x006562F0)
- [C] **For `d ≥ 0` the per-level columns of strength, dexterity, life, defence and damage, and the skill level, are
  corroborated by a second code path.** `HIRELING_RollEntry` reads the same offsets with the same operation (eighths
  for `Str/Lvl`, `Dex/Lvl`, `Dmg/Lvl`; plain products for `HP/Lvl`, `Def/Lvl`) and the same clamps (10, 10, 40, 0, 1),
  and the client's `sub_004B1090_ClientMercInit` computes `min(32, Level_i + (LvlPerLvl_i·d >> 5))` from the same
  bytes. For `d < 0` the paths round differently (floor in `RollEntry`, truncation in `MERC_SetLevel`), and AR and
  resistances have no second path, so those stay `[I]` above. (fn:MERC_SetLevel@0x00572840,
  fn:HIRELING_RollEntry@0x006637F0, fn:sub_004B1090_ClientMercInit@0x004B1090)
- [C] **Experience gives the level through `ExpForLevel(L) = (L+1)·L²·Exp/Lvl`**: a loaded mercenary's level is the
  greatest L ≤ 99 whose `ExpForLevel(L)` (with the row of band L−1) is ≤ its experience. Two code paths compute the
  same threshold (the hire list's inline product and `HIRELING_ExpForLevel`), and the `exphellmerc` save of
  run:2026-10-12-mon-pool-p2 (Id 4, `Exp/Lvl` 120, experience 500 000) gives 15, the level its screen showed.
  (fn:HIRELING_ExpForLevel@0x00663790, fn:D2S_ReadMercHeader@0x0056AA50, run:2026-10-12-mon-pool-p2)
- [I] **The MonStats class is the row's `Class`**: 271, 338, 359 and 561. No `hireling.txt` row has 560
  (`act5hire1`), so no hire or save path creates it. All four take monsters/pool's E2 (`d` = 0, MonStats `Level`
  1), and `MERC_SetLevel` then overwrites the level stat and the stats above, in a fresh hire and in a load.
  (fn:MERC_Create@0x005774F0, fn:sub_0063EE90_HirelingType@0x0063EE90, fn:sub_00573CB0_MonStatsInit@0x00573CB0)
- [I] **A hireling's kill counts its owner's magic find**: `MERC_Init` sets the mercenary's owner to the hiring
  player (`sub_0058F030_MonSetOwner`), which is what `MonsterOwner` reads in `ITEMS_DropMagicFind`. This answers the
  items/quality `[L]` from the code; no kill was logged. (fn:sub_0058F030_MonSetOwner@0x0058F030,
  fn:sub_0058F0D0_MonsterOwner@0x0058F0D0, fn:ITEMS_DropMagicFind@0x005585D0)

## Leads used

No community source was read for Phase 1. Every claim above was derived from code (or, for the record layout, from
data checked against code). The Phase 1b cross-check (2026-10-15) compared it with three fetched documents, none of
which contains code. Agreement promotes nothing. The four `contradicted` verdicts were each re-read in the
disassembly (§ 4, § 6), none of the readings changed, and they are in the backlog entry
"from reverser → architect: plan 0033 Phase 1b contradictions" ([backlog](../../backlog.md)). Every one that stock data
can reach is a required case of Phase 2.

`src:d2dfg-blizzard` § hireling.txt describes a later build than 1.14d: it has four resistance columns,
`HiringMaxLevelDifference` and the `resurrectcost*` columns, none of which exist in the 1.14d `hireling.txt` header.
Its verdicts therefore often mean "1.14d differs", and the spec must say so.

- [L] src:d2dfg-blizzard: `Version` 0 = classic, 100 = expansion; `Act` 1..5; `Difficulty` 1..3; `Class` and `Seller`
  are MonStats `hcIdx`. **held**
  Detail: `GetRecord`, `NextByActDiff` (`Act = act + 1`, `Difficulty = diff + 1`) and the `Class` spawn (§ 1, § 5).
- [L] src:d2dfg-blizzard: `NameFirst`..`NameLast` is "a sequential range of string IDs … to randomly generate as
  hireling names". **held with refinement**
  Detail: the range is that of the seller's **Normal** row in every difficulty, and one stock takes 10 distinct names
  of it by `Range(n)` with a +1 probe (§ 3).
- [L] src:d2dfg-blizzard: hire cost `Gold · (100 + 15 · (level − Level)) / 100`. **held with refinement**
  Detail: signed, truncating, `Level` of the first band's row, and never below `Gold` (0x0066391F–0x0066394C).
- [L] src:d2dfg-blizzard: `Exp/Lvl` gives the experience for the next level as `L + L · (L + 1) · Exp/Lvl`.
  **contradicted**
  Detail: 1.14d computes `ExpForLevel(L) = (L + 1) · L · L · Exp/Lvl` (0x00663790–0x006637A4, re-read); the
  `exphellmerc` save (500 000 experience, `Exp/Lvl` 120) shows level 15, which only the 1.14d formula gives. Already
  settled by run:2026-10-12-mon-pool-p2; Phase 2 adds level checks across the range.
- [L] src:d2dfg-blizzard: `Str/Lvl`, `Dex/Lvl`, `Dmg/Lvl` are "calculated in 8ths". **held**
  Detail: `÷8` in both `MERC_SetLevel` (truncating) and `RollEntry` (floor); the two agree for `d ≥ 0` (§ 4, § 6).
- [L] src:d2dfg-blizzard: each `Resist…/Lvl` is "calculated in 4ths". **held with refinement**
  Detail: 1.14d has one `Resist` and one `Resist/Lvl` column, applied to fire, lightning, cold and poison alike
  (0x00572A77–0x00572ABD).
- [L] src:d2dfg-blizzard: skill level `FLOOR(Level + LvlPerLvl · d / 32)`. **held with refinement**
  Detail: capped at 32, added only when ≥ 1 and when the skill's `reqlevel` ≤ L, and the loop stops at the first empty
  `Skill_i` (0x00572B3A–0x00572B7E).
- [L] src:d2dfg-blizzard: `HiringMaxLevelDifference` makes a list entry's level a random value within that many
  levels above or below the player's. **contradicted**
  Detail: 1.14d has no such column; the level is `max(2, playerLevel − 5 + low mod 5)`, so 1 to 5 levels **below** the
  player, never above (0x00663874–0x006638BB, re-read). Phase 2 required case: list levels against the player level.
- [L] src:d2dfg-blizzard: `HireDesc` is a string key. **contradicted**
  Detail: in 1.14d it is a `hiredesc.txt` code (`farw`, `comb`, `def` …) stored as a u8 row of `hiredesc`
  (`+0xD2`, read by `RollEntry` into its output `+0x30`); the layout is `[C]` by the data check (§ 1). Settled by data;
  not a Phase 2 case.
- [L] src:d2dfg-blizzard: resurrect cost `L · L / divisor · multiplier`, capped by `resurrectcostmax`. **held with
  refinement**
  Detail: 1.14d hard-codes divisor 2, multiplier 15 and cap 50 000 (`MERC_ResurrectCost`, 0x006637B0–0x006637DE);
  named only.
- [L] src:d2dfg-blizzard: skill choice in combat from `DefaultChance` and `Chance_i + ChancePerLvl_i · d / 4`.
  **not covered**
  Detail: `MERCAI_PickSkill` is named only (ADR-0002).
- [L] src:rpgkdh-hireling-guide: `Resist/Lvl` is the "Amount (in 8ths) of additional All Resist given at lvl up".
  **contradicted**
  Detail: 1.14d divides by 4 (`cdq; and edx, 3; add; sar eax, 2` at 0x00572A7D–0x00572A83, re-read). Phase 2 required
  case: a mercenary whose `Resist/Lvl · d` differs under ÷4 and ÷8 (any Rogue past its first band start, e.g. Normal
  classic Fire, `Level` 3, `Resist/Lvl` 8, at L = 10: 14 against 7).
- [L] src:rpgkdh-hireling-guide: `Str/Lvl`, `Dex/Lvl`, `Dmg/Lvl` in 8ths; `Level` is the level that "upgrades"
  skills and stats; `Gold` "compounded by mlvl"; `NameFirst`/`NameLast` a range for random names. **held**
  Detail: as for the d2dfg verdicts above; `Level` is the band start of `GetRecord` (§ 1).
- [L] src:arreat-summit-hirelings: hirelings cannot level past the character level. **held**
  Detail: `MERC_AddExp` levels up only while the mercenary's level is below its owner's (§ 6).
- [L] src:arreat-summit-hirelings: Act V hirelings only after Qual-Kehk's quest; none in Act IV. **held**
  Detail: bit 0 of quest word 36 gates Qual-Kehk; the four sellers are in acts I, II, III and V (§ 5, § 2).
- [L] src:arreat-summit-hirelings: a one-time gold fee; revival never costs more than 50 000. **held**
  Detail: `HIRE_Hire` pays once; `MERC_ResurrectCost` caps at 50 000 (§ 5, § 10).
- [L] src:arreat-summit-hirelings: "The Aura the Hireling uses depends on the Difficulty level you were at". **held with
  refinement**
  Detail: the type draw is over the rows of the game's (version, act, difficulty), each with its own skills (§ 4).
- [L] src:arreat-summit-hirelings: a resurrected mercenary keeps its attributes, experience and equipment. **not
  covered**
  Detail: `MERC_Resurrect` is named only.
- [L] src:arreat-summit-hirelings, src:d2dfg-blizzard, src:rpgkdh-hireling-guide: list size (10), the rebuild trigger,
  the entry seeds, the NPC seed, the free mercenaries, the save's name and Id handling and the owner's magic find.
  **not covered**
  Detail: no fetched source states them.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00655720` | `HIRELING_LoadTable` | `"hireling"`, 0x118-byte records; name indices; first-row-by-Id index | C |
| `0x006562B0` | `HIRELING_FreeTable` | frees the table, resets the index | I |
| `0x006562F0` | `HIRELING_GetRecord` | `(version flag, id, level)` → row of that Id whose `Level` band holds `level` | I |
| `0x00656390` | `HIRELING_NextByName` | next row whose name range holds a string index | I |
| `0x00656440` | `HIRELING_NextByClass` | next row with a `Class` | I |
| `0x006564D0` | `HIRELING_NextBySeller` | next row with `Seller` and `Difficulty` | I |
| `0x00656580` | `HIRELING_NextByActDiff` | next row with `Act`, `Difficulty` and the previous row's `Level` | I |
| `0x00663750` | `HIRELING_GetAct` | act index (`Act` − 1) by class, else by name index | I |
| `0x00663790` | `HIRELING_ExpForLevel` | `(L+1)·L·L·expPerLvl` | C |
| `0x006637B0` | `MERC_ResurrectCost` | resurrection price (named only) | I |
| `0x006637F0` | `HIRELING_RollEntry` | seed → Id, level, price, experience and displayed stats | I |
| `0x00575FF0` | `HIRE_GetNameRange` | seller's Normal row: first, last name index, class | I |
| `0x00576070` | `HIRE_BuildStock` | the hire table and its 10 picks | I |
| `0x00576770` | `HIRE_SendList` | builds if needed; sends each listed, unhired entry | I |
| `0x00577010` | `HIRE_RebuildIfEmpty` | rebuild when nothing listed is left | I |
| `0x005770E0` | `HIRE_Hire` | the hire request | I |
| `0x00579180` | `HIRE_GiveFreeMerc` | quest gift (`a1q2.cpp` → Kashya, `a3q3.cpp` → Asheara) | I |
| `0x005774F0` | `MERC_Create` | creates the monster for a loaded mercenary | I |
| `0x00573270` | `MERC_Init` | replaces the old mercenary, pet info, owner; fresh hire: experience and level | I |
| `0x00572840` | `MERC_SetLevel` | level, experience floor, stats and skills from the band row | I |
| `0x005726C0` | `sub_005726C0_MercSendStats` | sends the mercenary's stats to the client | I |
| `0x0057E3F0` | `MERC_CapExpGain` | caps one gain at `(ExpForLevel(L+1) − ExpForLevel(L)) >> 6` | I |
| `0x0057E860` | `MERC_AddExp` | adds experience, levels up while below the owner's level | I |
| `0x00579C00` | `MERC_Resurrect` | resurrection at an NPC (named only) | I |
| `0x005E4D30` | `MERCAI_PickSkill` | combat skill choice from `DefaultChance`, `Chance`, `ChancePerLvl` (named only) | I |
| `0x00533C70` | `sub_00533C70_ReadMercOldSave` | the older save versions' mercenary reader | I |
| `0x00533BF0` | `sub_00533BF0_MercExpFromOldSave` | experience conversion for save versions below 90 | I |
| `0x00574BD0` | `PETS_GetInfo` | a pet's 12-byte info by unit | I |
| `0x00574EC0` | `PETS_GetUnitOfType` | first pet of a type (dead ones only when asked) | I |
| `0x005749B0` | `PETS_SetInfo` | overwrites a pet's info | I |
| `0x00575E90` | `PETS_Add` | adds a pet with its info | I |
| `0x005751A0` | `PETS_OnDeath` | marks a pet dead (a mercenary stays in the list) (named only) | I |
| `0x00535EA0` | `sub_00535EA0_NpcRecordFind` | NPC record by MonStats row | I |
| `0x00536070` | `sub_00536070_NpcRecordsInit` | NPC records and the NPC seed, at game creation | I |
| `0x00536B40` | `sub_00536B40_NpcSeed` | `&NpcControl.seed` | I |
| `0x00576890` | `sub_00576890_NpcLevelCap` | Normal only: `min(level, {12,20,28,36,45}[act])` | I |
| `0x00576D90` | `sub_00576D90_PayGold` | takes a price from gold, then the stash | I |
| `0x00572C10` | `sub_00572C10_NpcInteractStart` | an NPC starts interacting with a player | I |
| `0x00578B30` | `sub_00578B30_NpcTradeInit` | trade start: vendor stock, then hire table if not built | I |
| `0x00579D60` | `sub_00579D60_NpcMenuCommand` | NPC menu command; 3 = open the hire list | I |
| `0x0058F030` | `sub_0058F030_MonSetOwner` | sets a monster's owner unit | I |
| `0x004B1090` | `sub_004B1090_ClientMercInit` | client: mercenary skills and name | I |
| `0x004B5C60` | `sub_004B5C60_ClientHireListDraw` | client: the hire list window | I |

Data: `data:g_pHirelingTxt@0x0096BDD0` (records), `data:g_nHirelingTxt@0x0096BDD4` (count),
`data:g_HirelingFirstById@0x0096BDD8` (2 × 256 i32: first row index per Id, classic half then expansion half; −1 =
none).

## Walkthrough

### 1. The table and its lookups

The loader (fn:HIRELING_LoadTable@0x00655720) declares these fields; the offsets are those of
`struct:HirelingRec+0x000` and are `[C]` by the data check above. The `.txt` columns `Hireling`, `SubType`,
`WType1`, `WType2` are not loaded. [C]

| Offset | Column | Width |
|---|---|---|
| +0x00 | `Version` | u16 |
| +0x04, +0x08, +0x0C, +0x10, +0x14 | `Id`, `Class`, `Act`, `Difficulty`, `Seller` | i32 |
| +0x18, +0x1C, +0x20 | `Gold`, `Level`, `Exp/Lvl` | i32 |
| +0x24…+0x60 | `HP`, `HP/Lvl`, `Defense`, `Def/Lvl`, `Str`, `Str/Lvl`, `Dex`, `Dex/Lvl`, `AR`, `AR/Lvl`, `Share`, `Dmg-Min`, `Dmg-Max`, `Dmg/Lvl`, `Resist`, `Resist/Lvl` | i32 each, in that order |
| +0x64 | `DefaultChance` | i32 |
| +0x68…+0x74 | `Head`, `Torso`, `Weapon`, `Shield` | i32 |
| +0x78, +0x90, +0xA8 | `Skill1..6` (Skills row, −1 empty), `Chance1..6`, `ChancePerLvl1..6` | 6 × i32 each |
| +0xC0, +0xC6, +0xCC | `Mode1..6`, `Level1..6`, `LvlPerLvl1..6` | 6 × i8 each |
| +0xD2 | `HireDesc` (HireDesc row) | u8 |
| +0xD3, +0xF3 | `NameFirst`, `NameLast` (string keys) | char[32] |
| +0x114, +0x116 | string indices of `NameFirst`, `NameLast` (runtime) | u16 |

After the load, for each row: the two indices from `STRTABLE_GetByKey`; in an expansion install
(`sub_00408F20_HasExpansionMpq`) a fatal error if the first index is 0 (`0x816`), if last ≤ first (`0x817`), or if
`Id` > 255 (`0x818`); then `g_HirelingFirstById[(Version > 99)·256 + Id]` gets the first row index of that Id. [I]
(fn:HIRELING_LoadTable@0x00655720, fn:sub_00408F20_HasExpansionMpq@0x00408F20)

In the stock data the name ranges are: Rogue `merc01`..`merc41` = 3411..3451 (41 names), Act II `merca201`..`merca221`
= 1019..1039 (21), Act III `merca222`..`merca241` = 1040..1059 (20), Barbarian `MercX101`..`MercX167` = 10835..10901
(67), from `tools/tbl.py lookup` on the English tables. [I] (fn:STRTABLE_GetByKey@0x00524D30)

`HIRELING_GetRecord(version flag, id, level)` [I] (fn:HIRELING_GetRecord@0x006562F0):

```
GetRecord(vflag, id, L):
  if id > 255: return none
  i ← g_HirelingFirstById[(vflag ≠ 0)·256 + id];  if i < 0: return none
  prev ← none
  for each row r from i to the end:
    if r.Id = id and r.Version = (vflag ≠ 0 ? 100 : 0):
      if prev ≠ none and L < r.Level: return prev
      prev ← r
    else if id < r.Id: return prev
  return prev
```

So it returns the matching row with the greatest `Level` ≤ L, or the first row of the Id when L is below every band.
That relies on the rows of one Id being in `Level` order, which the stock file is. [I] (fn:HIRELING_GetRecord@0x006562F0)

`HIRELING_NextByActDiff(vflag, act, diff, prev)` returns the next row after `prev` with `Act = act + 1`,
`Difficulty = diff + 1`, the version, and, when `prev` is given, `Level = prev.Level`. Starting from none and chaining,
it lists the rows of the first `Level` band only: one row per type. [I] (fn:HIRELING_NextByActDiff@0x00656580)
`HIRELING_NextBySeller(vflag, seller, diff, prev)` matches `Seller` and `Difficulty = diff + 1`;
`HIRELING_NextByName` matches `+0x114 ≤ index ≤ +0x116`; `HIRELING_NextByClass` matches `Class`. `HIRELING_GetAct(vflag,
class, name)` is `Act − 1` of the first row by class, else by name, else 0. [I] (fn:HIRELING_NextBySeller@0x006564D0,
fn:HIRELING_NextByName@0x00656390, fn:HIRELING_NextByClass@0x00656440, fn:HIRELING_GetAct@0x00663750)

### 2. The NPC records and the NPC seed

At game creation, after `sub_00547D20_MonRegionsInit` (game draw 1) and `OBJRGN_Create` (draw 2),
`sub_00536070_NpcRecordsInit` allocates the NPC control block (`.\UNIT\sunitproxy.cpp`) and 64 records of 0x44 bytes,
one per MonStats row with the NPC flag. It does `InitOne(seed)`, one step of the game seed, `Init(seed, low)`. Its
static call graph holds no other RNG use (`tools/ghidra.sh rngcallgraph`). So the NPC seed is seeded from game draw 3.
[I] (fn:sub_00536070_NpcRecordsInit@0x00536070, 0x005360D2–0x005360FB, fn:sub_00530BF0_GameCreate@0x00530BF0)

A record's `act` (+0x22) and `trader` (+0x23) bytes come from a 43-entry table at `0x00731188` (8 bytes each: MonStats
row, then trader, act, and a third flag): Kashya 150 → trader 0, act 0; Greiz 198 → 0, 1; Asheara 252 → 1, 2;
Qual-Kehk 515 → 0, 4. [I] (fn:sub_00536070_NpcRecordsInit@0x00536070)

The NPC seed is also drawn by vendor code (`0x00576330`, `0x005786A0`, `0x00578790`, `0x00579030`, `0x00576980`
reach `sub_00536B40_NpcSeed`; plan 0031's subject). Its draws interleave with the hire builds in game order. [I]
(fn:sub_00536B40_NpcSeed@0x00536B40)

### 3. The stock build

```c
// fn:HIRE_BuildStock@0x00576070 (trimmed, renamed)
if (rec->hireBuilt == 0 && (rec->hireBuilt = 1, rec->pHireTable == NULL)) {
    t = alloc(0x450); memset(t, 0, 0x450);            // 69 entries of 16 bytes
    seed = NpcSeed(game);
    n = HIRE_GetNameRange(&first, &last, NULL);        // seller = rec's NPC, Normal row
    for (i = 0; i < n && first + i <= last; i++) {
        t[i].nameIdx = first + i;
        Step(seed); t[i].seed = seed->low;             // NPC draw i+1
        t[i].hired = 0; t[i].listed = 0;
    }
    for (k = 0; k < 10; k++) {
        u = Range(seed, n);                            // NPC draw n+k+1
        v = u;
        while (t[v].listed || t[v].hired) { v++; if (v >= n) v = 0; if (v == u) return; }
        t[v].listed = 1;
    }
}
```

- [I] `HIRE_GetNameRange` takes `HIRELING_NextBySeller(vflag, seller, 0, none)`: the first row of the seller with
  `Difficulty` 1. So the name range (and the class used for the hire) is the same in every difficulty; a range with
  `last − first + 1 = −1` is fatal. (fn:HIRE_GetNameRange@0x00575FF0)
- [I] Every name index gets a seed, whether it is picked or not, and the seeds are drawn before the picks.
  (fn:HIRE_BuildStock@0x00576070)
- [I] On a fresh table nothing is listed or hired, so the 10 picks give 10 distinct names (every `n` is ≥ 20). The
  probe never draws. (fn:HIRE_BuildStock@0x00576070)
- [I] **When.** `HIRE_SendList(npc)` returns at once unless the NPC is one of 150, 198, 515, 252; it then builds the
  table if `hireBuilt` is 0 and sends every entry with `listed ≠ 0` and `hired = 0`. It is called from
  `sub_00572C10_NpcInteractStart` (an NPC begins interacting with a player), from `sub_00579D60_NpcMenuCommand` command
  3 (the hire list) and after a hire. `sub_00578B30_NpcTradeInit` would also build it for an NPC whose `trader` byte
  is set (Asheara), after the vendor stock, but the interaction start comes first. So the build is at the first talk
  with each of the four NPCs in a game. (fn:HIRE_SendList@0x00576770, fn:sub_00572C10_NpcInteractStart@0x00572C10,
  fn:sub_00579D60_NpcMenuCommand@0x00579D60, fn:sub_00578B30_NpcTradeInit@0x00578B30)
- [I] **Rebuild.** `HIRE_RebuildIfEmpty` counts the entries with `listed ≠ 0` and `hired = 0`; at 0 it frees the
  table, clears `pHireTable` and `hireBuilt` and calls `HIRE_BuildStock` again (another `n + 10` NPC draws). It runs
  after each hire and after a free mercenary. Nothing else clears the table during a game. (fn:HIRE_RebuildIfEmpty@0x00577010)

### 4. An entry: type, level, price and the displayed stats

```c
// fn:HIRELING_RollEntry@0x006637F0 (ECX = version flag, EDX = player; trimmed)
Init(&s, seed);                                            // InitOne then Init
k = 0; for (r = NextByActDiff(vflag, act, diff, NULL); r; r = NextByActDiff(vflag, act, diff, r)) rows[k++] = r;
if (k == 0) return 0;
row = rows[RangeB(&s, k)];                                 // entry draw 1
out->id = row->id;
Step(&s);                                                  // entry draw 2, inline
L = playerLevel + (int)(s.low % 5) - 5;  if (L < 2) L = 2; // unsigned mod, signed compare
d = L - row->level;
out->level  = L;
out->hp     = max(40, row->hp + row->hpPerLvl * d);
out->str    = max(10, row->str + ((row->strPerLvl * d) >> 3));   // sar: floor
out->dex    = max(10, row->dex + ((row->dexPerLvl * d) >> 3));
out->price  = max(row->gold, ((15 * d + 100) * row->gold) / 100); // signed, truncating
out->exp    = max(0, (L + 1) * row->expPerLvl * L * L);
out->def    = max(0, row->defense + row->defPerLvl * d);
out->dmgMin = max(0, row->dmgMin + ((row->dmgPerLvl * d) >> 3));
out->dmgMax = max(1, row->dmgMax + ((row->dmgPerLvl * d) >> 3));
out->share  = max(0, row->share);  out->resist = max(0, row->resist);
out->hireDesc = row->hireDesc;  out->_34 = 1;  out->_38 = 0;
```

- [I] `act` is `HIRELING_GetAct(vflag, 0, name)`: the act of the row whose name range holds the entry's name, so a
  list shows its own act's types. `diff` is the game's difficulty. (fn:HIRE_Hire@0x005770E0, 0x0057725C–0x0057727A)
- [I] The seed only decides the type (draw 1) and the level offset `0..4` (draw 2). The level follows the player's
  **current** level each time the entry is rolled: the client rolls it to draw the list and the server rolls it again
  at the hire, so a level-up between the two changes the mercenary bought. (fn:HIRELING_RollEntry@0x006637F0,
  fn:sub_004B5C60_ClientHireListDraw@0x004B5C60, fn:HIRE_Hire@0x005770E0)
- [I] The displayed stats extrapolate from the **first band's row**, with floor division for the eighths, while the
  stats in the world (§ 6) use the row of the mercenary's own band and truncating division. They agree only while
  `L` is inside the first band and `d ≥ 0`. (fn:HIRELING_RollEntry@0x006637F0, fn:MERC_SetLevel@0x00572840)
- [I] The price is the `Gold` column raised 15 % per level above the band start, never below `Gold`.
  (0x0066391F–0x0066394C)
- [I] The client list window draws up to 10 entries. It shows name index 1057 (`Lharhad`) as 11021 (`Jarulf`), and
  so does the client's mercenary init. (fn:sub_004B5C60_ClientHireListDraw@0x004B5C60,
  fn:sub_004B1090_ClientMercInit@0x004B1090)

### 5. The hire

`HIRE_Hire(npc, nameIdx)` (EDX = the player) [I] (fn:HIRE_Hire@0x005770E0):

1. Qual-Kehk (515) refuses unless bit 0 of quest word 36 is set in the player's quest record for the game's difficulty;
   Kashya (150) refuses when `sub_00576890_NpcLevelCap(playerLevel) < 8` and bit 0 of quest word 2 is clear. The cap
   is `min(level, {12, 20, 28, 36, 45}[npc.act])` in Normal and the level itself otherwise, so for Kashya this is
   "player level below 8". (fn:QUESTRECORD_GetState@0x0065C310, fn:sub_00576890_NpcLevelCap@0x00576890)
2. The name must lie in the seller's range, the table entry at `nameIdx − first` must carry that name and have
   `hired = 0`. **`listed` is not checked.** (0x005771E8–0x00577258)
3. `HIRELING_RollEntry(entry.seed, act, difficulty)` gives the price; `sub_00576D90_PayGold` takes it from gold
   (stat 14), the remainder from the stash (stat 15), or refuses if the two together fall short.
4. The mercenary is spawned with `sub_005B23C0_SpawnNearUnitNoBox(class, 1, 4, 0)`, tried twice, where `class` is
   the `Class` of the seller's Normal row (271, 338, 359, 561). `entry.hired ← 1`.
5. `MERC_Init(merc, 0xFFFF, entry)`, then the list is resent, a hire message sent, `HIRE_RebuildIfEmpty`.

`MERC_Init(merc, id, {name, seed}, dead)` [I] (fn:MERC_Init@0x00573270):

- sets the unit flags `0x4020200`, alignment 2 (`sub_005543B0_MonAlignSet`); if the player already has a
  mercenary (pet type 7, dead or alive), it is released and removed;
- `RollEntry(seed, GetAct(vflag, 0, name), difficulty)` → `out`; `PETS_Add(merc, 7, {seed, name, out.id})`;
- `sub_0058F030_MonSetOwner(merc, player id, player type)` writes the owner into the monster's AI block
  (`monsterData+0x28` → `+0x2C` id, `+0x30` type, `+0x28` the game);
- **fresh hire only** (`id = 0xFFFF`): `row ← GetRecord(vflag, out.id, out.level)`; stat 13 ← `out.exp`;
  `MERC_SetLevel(merc, out.level)`; `sub_005726C0_MercSendStats`.

So the header the save writes (`D2S_WriteMercHeader`: seed, name − `+0x114`, Id, experience, dead flag) holds the
entry's seed, the name, the Id rolled from that seed, and the experience. [I] (fn:D2S_WriteMercHeader@0x00568E60,
fn:PETS_GetInfo@0x00574BD0)

**Free mercenary.** `HIRE_GiveFreeMerc(seller)` (called with 150 from `a1q2.cpp` code and 252 from `a3q3.cpp` code)
gives one when the player has none (expansion: no mercenary at all, dead or alive; classic: no living one) and the
seller's table exists: the first entry in name order with `listed = 1` and `hired ≠ 1` becomes hired and is spawned
(class from `NextBySeller(vflag, seller, difficulty)`; ranges 4, 6, 12) and initialised like a hire, with no payment
and no quest gate. [I] (fn:HIRE_GiveFreeMerc@0x00579180)

### 6. The stats per level (`MERC_SetLevel`)

`MERC_SetLevel(merc, L)` [I] (fn:MERC_SetLevel@0x00572840), with `row = GetRecord(vflag, info.id, L)` and
`d = L − row.Level` (all i32; "÷8" and "÷4" are `cdq; and; add; sar`, i.e. truncation toward zero):

| Stat | Value |
|---|---|
| 12 `level` | `L` |
| 30 `nextexp` | `ExpForLevel(L+1)` if `L < 98`, else 0 |
| 13 `experience` | `max(current, ExpForLevel(L))` |
| 0 `strength` | `max(10, Str + Str/Lvl·d ÷8)` |
| 2 `dexterity` | `max(10, Dex + Dex/Lvl·d ÷8)` |
| 7 `maxhp`, 6 `hitpoints` | `max(40·256, (HP + HP/Lvl·d)·256)` (in 1/256) |
| 31 `armorclass` | `max(0, Defense + Def/Lvl·d)` |
| 23 `secondary_mindamage` | `max(0, Dmg-Min + Dmg/Lvl·d ÷8)` |
| 24 `secondary_maxdamage` | `max(1, Dmg-Max + Dmg/Lvl·d ÷8)` |
| 19 `tohit` | `max(0, AR + AR/Lvl·d)` |
| 39, 41, 43, 45 (fire, lightning, cold, poison resist) | `max(0, Resist + Resist/Lvl·d ÷4)` |
| 74 `hpregen` | `max(0, maxhp_base ÷ 2000)`, maxhp in 1/256, signed truncating |

[C] for `d ≥ 0`, the strength, dexterity, life, defence and damage rows: `HIRELING_RollEntry` (§ 4) reads the same
offsets (`+0x34`/`+0x38`, `+0x3C`/`+0x40`, `+0x24`/`+0x28`, `+0x2C`/`+0x30`, `+0x50`/`+0x54`/`+0x58`) with the same
operation and clamp, and for `d ≥ 0` floor and truncation agree. The rest of the table (AR, resistances, the `d < 0`
rounding, experience floor, `hpregen`) is `[I]`. The resistance divisor 4 was re-read after the cross-check
(`cdq; and edx, 3; add eax, edx; sar eax, 2` at 0x00572A7D–0x00572A83). (fn:MERC_SetLevel@0x00572840,
fn:HIRELING_RollEntry@0x006637F0, 0x006638C0–0x006639E1)

Skills, for `i` = 1..6 in order, stopping at the first `Skill_i < 1` or ≥ the skill count, or `Mode_i > 15` (signed):
if `reqlevel` of the skill (Skills `+0x174`) ≤ L, `slvl = Level_i + (LvlPerLvl_i·d >> 5)` (a plain `sar`: floor),
`min(slvl, 32)`, and the skill is added when `slvl ≥ 1`. [I] (0x00572B3A–0x00572B7E, fn:SKILLS_GetRecord@0x0045C4B0,
fn:sub_0056DEB0_UnitSkillAdd@0x0056DEB0, tbl:Skills.txt:reqlevel)
The skill level itself, `min(32, Level_i + (LvlPerLvl_i·d >> 5))` for `d ≥ 0`, is [C]: the client's
`sub_004B1090_ClientMercInit` computes it from the same bytes (`movsx` of `+0xCC + i` and `+0xC6 + i`, `sar 5`, cap
0x20, 0x004B115A–0x004B1178), with `d` clamped at 0 and no `reqlevel` test. (fn:sub_004B1090_ClientMercInit@0x004B1090)

`ExpForLevel(L, e) = (L+1)·L·L·e` (i32 products). The 99 is `sub_00611830_ExpMaxLevel(0)` (`experience.txt`
`MaxLvl`, Amazon column). [C] for the formula (fn:HIRELING_ExpForLevel@0x00663790; second code path: the inline
product at 0x0066394F–0x00663968 in fn:HIRELING_RollEntry@0x006637F0; run:2026-10-12-mon-pool-p2)
(fn:sub_00611830_ExpMaxLevel@0x00611830)

**Levelling in play** (named, not specified): `MERC_AddExp` adds experience and calls `MERC_SetLevel` for each level
reached, only while the mercenary's level is below its owner's; `MERC_CapExpGain` caps one gain at
`(ExpForLevel(L+1) − ExpForLevel(L)) >> 6`. [I] (fn:MERC_AddExp@0x0057E860, fn:MERC_CapExpGain@0x0057E3F0)

### 7. The mercenary from a save

`D2S_ReadMercHeader(hdr + 0xAF)` [I] (fn:D2S_ReadMercHeader@0x0056AA50):

```
if seed = 0 and name = 0 and exp = 0: return none                ; hdr 0xB3, 0xB7 (u16), 0xBB
base ← GetRecord(vflag, id, 1)                                   ; id = hdr 0xB9 (u16)
name ← name + base.nameFirstIdx;  if name > base.nameLastIdx: name ← base.nameFirstIdx
dead ← flags & 0x10000                                           ; hdr 0xAF
merc ← MERC_Create(name, seed, id, base.Class, dead)
PETS_SetInfo(merc, {seed, name, id})                             ; the saved Id wins
stat 13 ← max(stat 13, exp)
L ← 1;  while L+1 ≤ 99 and ExpForLevel(L+1, GetRecord(vflag, id, L).Exp/Lvl) ≤ exp: L ← L+1
MERC_SetLevel(merc, L)
if dead: PETS_OnDeath(merc); merc.flags |= 0x10000; mode 12 …
if no inventory: create one
```

`MERC_Create` [I] (fn:MERC_Create@0x005774F0):

- **classic** (`vflag = 0`): the mercenary is created only if `GetAct(vflag, 0, name)` ≥ 0 equals the player's act
  (`Client+0x1AC`, or the unit's own byte when it has no client). An expansion game creates it anywhere.
- the row is `GetRecord(vflag, id, 1)` (or, for id `0xFFFF`, the first `NextByActDiff(vflag, act, difficulty)` row);
  the name is clamped into its range; if the seller's hire table exists and the name's entry is not listed, the entry
  is marked hired;
- `sub_00555230_SUnitCreate(type 1, class, …, mode = dead ? 12 : 1)`, then `MERC_Init(merc, id, {name, seed}, dead)`.

So for a loaded mercenary the **seed** is carried in the pet info and rolled once more inside `MERC_Init` (for an Id
that `PETS_SetInfo` then overwrites with the saved one); it does not reach the stats. The level and stats come from
the experience and the saved Id. The mercenary's items are read after the header, into the unit `MERC_Create`
returned ([save/0001](../save/0001-d2s-io.md), `D2S_ReadMercItems`). [I] (fn:D2S_ReadMercItems@0x0056AC10)

**The `exphellmerc` case** (run:2026-10-12-mon-pool-p2): Id 4 (`Fire - Hell`, expansion, one row at `Level` 67,
`Exp/Lvl` 120), experience 500 000. Every `GetRecord(…, L)` with L < 67 returns that row. `ExpForLevel(15) =
16·225·120 = 432 000 ≤ 500 000` and `ExpForLevel(16) = 17·256·120 = 522 240 > 500 000`, so L = 15, the level shown on
its screen; MonStatsInit had made it at level 1. [C] (fn:D2S_ReadMercHeader@0x0056AA50, run:2026-10-12-mon-pool-p2)
With L = 15 and `Level` 67, `d = −52`: strength `87 + (10·−52) ÷8 = 87 − 65 = 22`, life `max(40, 779 + 30·−52) = 40`.
[I] (fn:MERC_SetLevel@0x00572840)

The pre-1.07 save reader `sub_00533C70_ReadMercOldSave` does the same, after converting experience for versions below
90 (`sub_00533BF0_MercExpFromOldSave`); version 71 saves carry no Id and are created with id `0xFFFF`. [I]
(fn:sub_00533C70_ReadMercOldSave@0x00533C70)

### 8. MonStats class and the E2 level path

| Seller | `Class` | MonStats | `Level` / `Level(N)` / `Level(H)` | E2 effect |
|---|---|---|---|---|
| Kashya | 271 | `roguehire` | 1 / 34 / 67 | `d` ← 0: level 1 in every difficulty; `[C]` in hell (run:2026-10-12-mon-pool-p2) |
| Greiz | 338 | `act2hire` | 1 / 34 / 67 | same, `[I]` (fn:sub_0063EE90_HirelingType@0x0063EE90) |
| Asheara | 359 | `act3hire` | 1 / 34 / 67 | same, `[I]` (fn:sub_0063EE90_HirelingType@0x0063EE90) |
| Qual-Kehk | 561 | `act5hire2` | 1 / 1 / 1 | none observable: all three are 1 |
| (none) | 560 | `act5hire1` | — | no `hireling.txt` row has `Class` 560 |

- [I] Every hire and load path takes the class from a `hireling.txt` row (`HIRE_GetNameRange`, `NextBySeller`, or the
  saved Id's row), and the stock file's `Class` column holds only 271, 338, 359 and 561, in both versions.
  (fn:MERC_Create@0x005774F0, fn:HIRE_Hire@0x005770E0, fn:HIRE_GiveFreeMerc@0x00579180)
- [I] `sub_0063EE90_HirelingType` tests only the unit type and class, not the version flag, so a classic game takes
  the same E2 step. Classic uses the `Version` 0 rows: Act I base `Level` 3, Act II 9, Act III 15; the `Version` 0
  Barbarian rows exist but no classic act reaches them. (fn:sub_0063EE90_HirelingType@0x0063EE90)
- [I] Whatever the MonStatsInit level was, `MERC_SetLevel` overwrites stat 12 and the stats of § 6 right after the
  creation (`MERC_Init` for a hire, `D2S_ReadMercHeader` for a load). (fn:MERC_Init@0x00573270)

### 9. Magic find on a hireling's kill

- [I] `ITEMS_DropMagicFind(killer)` adds the stat 80 of `MonsterOwner(killer)`. `MonsterOwner` returns the unit whose
  id is at `monsterData+0x28 → +0x2C` when that block's `+0x28` is non-zero. `MERC_Init` writes exactly that block
  with the hiring player's id and type and the game pointer, so a mercenary's kill uses the mercenary's stat 80 plus
  the player's. (fn:sub_0058F030_MonSetOwner@0x0058F030, fn:sub_0058F0D0_MonsterOwner@0x0058F0D0,
  fn:ITEMS_DropMagicFind@0x005585D0, 0x005733A3–0x005733B2)

### 10. Named only

- [I] Resurrection: `MERC_Resurrect` at Kashya, Greiz, Asheara, Tyrael (`tyrael2`, 367) or Qual-Kehk, for a dead mercenary,
  price `MERC_ResurrectCost = min(50000, (L²/2)·15)` (unsigned compare), paid like a hire. (fn:MERC_Resurrect@0x00579C00,
  fn:MERC_ResurrectCost@0x006637B0)
- [I] Death: `PETS_OnDeath` sets the pet node's dead bit; a mercenary (pet type 7) stays in the list.
  (fn:PETS_OnDeath@0x005751A0)
- [I] Combat skill choice: `MERCAI_PickSkill` reads `DefaultChance`, `Chance_i`, `ChancePerLvl_i` and `Mode_i`. Out of
  scope (ADR-0002). (fn:MERCAI_PickSkill@0x005E4D30)

### 11. Phase 2 boundary (recommendation; the architect rules)

**Recommended: the hire list from the NPC seed on entry to each build, as a boundary oracle (ADR-0004).**
`tools/hirelings.py` models `HIRE_BuildStock`, `HIRELING_RollEntry`, `MERC_SetLevel` and the save's level loop. The
NPC seed is shared with vendor code (plan 0031), so the model takes the seed logged on entry to each
`HIRE_BuildStock` and asserts it; the vendor draws between two builds are an oracle, not modelled. Separately, one
check per game that the NPC seed starts at `Init(low of game draw 3)` (log `sub_00536070_NpcRecordsInit` exit).

What to log (`tools/gdb/hirelings.gdb`):

| Where | What |
|---|---|
| `sub_00536070_NpcRecordsInit` exit | game seed, NPC seed |
| `HIRE_BuildStock` entry / exit | NPC class, NPC seed in and out, the 69-entry table (name, seed, listed) |
| `HIRE_SendList` entry | NPC class, caller (interaction start, menu, hire) |
| `HIRELING_RollEntry` entry / exit | seed, act, difficulty, player level; the 15-dword output |
| `HIRE_Hire` entry, `MERC_Init` entry | name, entry seed, id argument |
| `MERC_SetLevel` entry / exit | L, row index, then stats 0, 2, 6, 7, 12, 13, 19, 23, 24, 30, 31, 39, 41, 43, 45, 74 and the skill list |
| `D2S_ReadMercHeader` | header bytes, the L the loop reaches |
| `ITEMS_DropMagicFind` | killer class, killer and owner stat 80 (a mercenary kill) |

Claims that only such a run can raise to C: the trigger (first interaction), the `n + 10` draw count, the probe,
the entry roll and its level rule, the stats table, the classic act test, game draw 3, the free mercenary, and the
mercenary's magic find.

## Data touched

- `hireling` records (`struct:HirelingRec+0x000`): every loaded column; `+0x114`/`+0x116` written at load.
- Skills `reqlevel` (tbl:Skills.txt:reqlevel, `+0x174`).
- `experience` row `MaxLvl`, Amazon column (through `sub_00611830_ExpMaxLevel`).
- NPC records (`struct:NpcRecord+0x10`, `+0x21`, `+0x22`), NPC seed (`struct:NpcControl+0x08`), hire table
  (`struct:HireEntry+0x0`), pet info (`struct:MercInfo+0x0`, `struct:PetNode+0x08`).
- Quest record words 2 and 36, bit 0 ([save/0002](../save/0002-quest-words.md)).

## Dead ends

- `HIRELING_NextByActDiff` looked like "every row of the act and difficulty"; the `+0x1C` test against the previous
  row restricts it to the first `Level` band, so the type draw is over 2 or 3 rows, not over all bands.
- The `Id` in a loaded mercenary's pet info is first the one `RollEntry` derives from the seed and the current
  difficulty; `PETS_SetInfo` right after replaces it with the saved Id. Reading `MERC_Init` alone suggests the Id
  follows the difficulty.

## Open questions

- Which MonStats-derived fields (velocity, mana, other stats that `MERC_SetLevel` does not set) survive from
  MonStatsInit's level-1 creation? Read `sub_00573CB0_MonStatsInit`'s stat writes against § 6, or log the stat list.
- The client's mercenary init rolls the entry again from the seed and the player's level and draws skills with
  `d` clamped at 0 (`sub_004B1090_ClientMercInit`); whether the client ever shows those instead of the server's values
  is a display question for Phase 2.
- The input of `MERC_AddExp` (the share of the owner's experience) and its doubling were not read.
- The third byte of the `0x00731188` NPC table (`NpcRecord+0x26`) is not used by hire code.
- Phase 1b contradictions to settle in Phase 2 (each re-read, readings unchanged): the resistance divisor 4 against
  `src:rpgkdh-hireling-guide`'s eighths (a merc at a level where ÷4 and ÷8 differ), and the entry level range
  `playerLevel − 5 .. playerLevel − 1` (min 2) against `src:d2dfg-blizzard`'s symmetric range (the logged lists). The
  experience formula contradiction is already settled by run:2026-10-12-mon-pool-p2 and the `HireDesc` one by data.

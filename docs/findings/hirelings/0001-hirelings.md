# 0001 — Hirelings: the hire list, the hire, the mercenary's stats and its creation from a save

> **Subsystem:** hirelings
> **Question:** Which hirelings does a town's hire list offer (names, types, levels, prices), and how does a hired or loaded mercenary get its state from `Hireling.txt`, its seed and its experience?
> **Date:** 2026-10-15   **Plan:** 0033 (Phase 1, Phase 1b, Phase 2)   **Status:** open (Phase 1 read from the decompile and the disassembly, committed before any community source was read; Phase 1b cross-check added after, with a re-read of every contradicted claim; Phase 2 run:2026-10-16-hirelings, § Phase 2); plan 0038 batch S3a, 2026-10-16: 0 raised, 3 in part, [§ Plan 0038 batch S3a](#plan-0038-batch-s3a-2026-10-16)

Names of structs and fields are ours (`re/types/hireling.h`). Column names are those of
[Hireling](../../tables/Hireling.md) and [HireDesc](../../tables/HireDesc.md) (the `hireling.txt` header); the
`tbl:Hireling.txt:…` anchors name those columns, and `struct:HirelingRec` the same bytes. "Version flag" is `Game+0x70` (non-zero in an expansion game: rows with `Version` 100 are used,
else rows with `Version` 0); "difficulty" is `Game+0x6D` (0..2). "NPC seed" is the seed object at
`NpcControl+0x08` (`Game+0x1D24` → `+0x08`), a seed of its own, distinct from the game seed `Game+0xD0`. It is the
same object as the **store seed** `S` of items/vendors § A1 and [items/0009 § 1](../items/0009-vendors.md#1-store-records-and-the-store-seed-game-creation) (`NPCSTORE_GetSeed` returns
it to both vendor and hire code), not a second seed: one game-seed draw (draw 3) seeds it once per game
([rng/0002](../rng/0002-seed-tree.md)). "Step" and `Range` are the RNG primitives of [rng/0001](../rng/0001-rng-core.md)
(`RNG_Range` and `RNG_RangeB` compute the same thing). Names in `string.tbl` and friends are string indices
([data/strings](../../specs/data/strings.md)); the monster side (MonStatsInit, the level step E2) is
[monsters/pool](../../specs/monsters/pool.md) § E.

## Answer (summary)

The tags below are those of the plan 0033 record. [§ Plan 0038 batch S3a](#plan-0038-batch-s3a-2026-10-16) raises
further statements; where it lists one, its tag and evidence take precedence over the bullet here.

- [C] **The `hireling` record is 0x118 bytes** with the field offsets of `struct:HirelingRec+0x000` (the loader's
  field descriptor, `Version` u16 at +0x00 … `NameLast` at +0xF3), plus two u16 string indices at +0x114/+0x116 that
  the loader fills from `NameFirst`/`NameLast` with `STRTABLE_GetByKey`. Corroborated by data: decoding the 120
  records of `hireling.bin` at these offsets reproduces every loaded cell of `hireling.txt` (8 280 fields, 0
  mismatches); +0x113 is 0 and +0x114/+0x116 are 0 in every record of the file. (fn:HIRELING_LoadTable@0x00655720,
  fn:STRTABLE_GetByKey@0x00524D30, data:g_pHirelingTxt@0x0096BDD0, data:g_nHirelingTxt@0x0096BDD4,
  tbl:Hireling.txt:Version, tbl:Hireling.txt:NameFirst, tbl:Hireling.txt:NameLast)
- [C] **One stock per hireling NPC per game.** The four sellers are Kashya (MonStats 150), Greiz (198), Asheara (252)
  and Qual-Kehk (515). An NPC's hire table is built the first time a player starts an interaction with it
  (`sub_00572C10_NpcInteractStart` → `HIRE_SendList`), and only rebuilt when no listed, unhired entry remains (after a
  hire or a free mercenary). In run:2026-10-16-hirelings all 52 first builds came from `HIRE_SendList` at the first
  interaction, and the one rebuild came after the hire that left no listed, unhired entry; the free mercenary's
  rebuild was not exercised. It lives in the game's NPC record, so all players of a game share it: that part stays
  `[I]` (single player only). (run:2026-10-16-hirelings, fn:HIRE_SendList@0x00576770, fn:sub_00572C10_NpcInteractStart@0x00572C10, fn:HIRE_RebuildIfEmpty@0x00577010,
  tbl:Hireling.txt:Seller)
- [C] **The build draws `n + 10` times from the NPC seed**, where `n = NameLast − NameFirst + 1` of the seller's
  Normal row (Kashya 41, Greiz 21, Asheara 20, Qual-Kehk 67). First every name index, in order, gets the low word of
  one NPC-seed step as its seed; then 10 picks `Range(n)` each mark one entry listed, stepping +1 (wrapping) past
  entries already listed or hired. The list is 10 distinct names. Reproduced table for table: 53 builds (all four
  sellers, the three difficulties), 2625 draws on the NPC seed, S chained from game creation through every build.
  (run:2026-10-16-hirelings, fn:HIRE_BuildStock@0x00576070,
  fn:HIRE_GetNameRange@0x00575FF0, fn:RNG_Range@0x0045C390, tbl:Hireling.txt:NameFirst, tbl:Hireling.txt:NameLast)
- [C] **The NPC seed is `Init(low)` of one game-seed step taken at game creation**, right after the object-region
  step, so it is game-seed draw 3 under `-seed N` (48 of 48 games). It is the store seed of items/vendors § A1 (one
  object, `NpcControl+0x08`, one seeding per game; run:2026-10-15-vendors observed the same draw in its own 7 games),
  and vendor code of the same NPCs draws from it too.
  (run:2026-10-16-hirelings, fn:NPCSTORE_CtlCreate@0x00536070, fn:NPCSTORE_GetSeed@0x00536B40, fn:sub_00530BF0_GameCreate@0x00530BF0)
- [C] **An entry's seed decides its type and level; the player's level at the time decides the rest.**
  `HIRELING_RollEntry(seed, act, difficulty)` does `Init(seed)`, draw 1 `Range(k)` over the `k` rows of
  (version, act, difficulty) that share the first such row's `Level` (one row per type: Rogue fire/cold, the three
  Act II and Act III types, the two Barbarian ids), draw 2 a raw step: `level = max(2, playerLevel − 5 + low mod 5)`.
  Price, experience and the displayed stats are linear in `d = level − row.Level`. 723 calls reproduced, output for
  output, from all four callers (the client's list window 530, `HIRE_Hire` 49, `MERC_Init` 72, the client's
  mercenary init 72), expansion and classic rows; every list entry lies at player level −5 .. −1.
  (run:2026-10-16-hirelings, fn:HIRELING_RollEntry@0x006637F0,
  fn:HIRELING_NextByActDiff@0x00656580, tbl:Hireling.txt:Act, tbl:Hireling.txt:Difficulty, tbl:Hireling.txt:Level)
- [C] **The hire stores `{seed, name index, Hireling Id}`** in the player's pet list (pet type 7). The seed is the
  entry's seed from the stock build; the Id is draw 1 of `RollEntry`; the price is `RollEntry`'s, taken from
  inventory gold (49 hires). [C] The save header copies it (`D2S_WriteMercHeader`; § Plan 0038 batch H1b,
  run:2026-10-27-sweep-d2s-play). [I] A price above the inventory gold takes the rest from the stash (never needed in the run). (run:2026-10-16-hirelings,
  fn:HIRE_Hire@0x005770E0, fn:MERC_Init@0x00573270, fn:PETS_Add@0x00575E90,
  fn:sub_00576D90_PayGold@0x00576D90, fn:D2S_WriteMercHeader@0x00568E60, tbl:Hireling.txt:Id, tbl:Hireling.txt:Gold)
- [C] **In the world, every stat comes from the row whose `Level` band holds the mercenary's level**
  (`HIRELING_GetRecord(version, id, L)`, the matching row with the greatest `Level` ≤ L), with `d = L − row.Level` and
  signed integer arithmetic: strength, dexterity and damage add `Str/Lvl·d`, `Dex/Lvl·d`, `Dmg/Lvl·d` divided by 8
  (truncated), resistances `Resist/Lvl·d` divided by 4, life, defence and AR add the plain product; clamps 10, 10, 40
  life, 0/1 damage, 0. Skills `Skill1..6` at `Level_i + floor(LvlPerLvl_i·d / 32)`, capped at 32, if the player
  level requirement of the skill (`reqlevel`) is met. Reproduced stat for stat in 72 `MERC_SetLevel` calls (49 hires,
  23 loads): rows of every band, `d` from −41 to 27, 17 levels where truncation and floor differ, 32 where `Resist/Lvl`
  ÷4 and ÷8 differ, clamps reached (life 40, AR and defence 0: a stat set to 0 has no entry in the list).
  (run:2026-10-16-hirelings, fn:MERC_SetLevel@0x00572840, fn:HIRELING_GetRecord@0x006562F0,
  tbl:Hireling.txt:Level, tbl:Hireling.txt:Str/Lvl, tbl:Hireling.txt:Resist/Lvl, tbl:Hireling.txt:LvlPerLvl1,
  tbl:Skills.txt:reqlevel)
- [C] **For a non-negative product `column·d` the per-level columns of strength, dexterity, life, defence and
  damage, and the skill level, are corroborated by a second code path.** That is `d ≥ 0` on stock data, where every
  per-level column is ≥ 0 (`HP/Lvl` 8..45, `Def/Lvl` 4..50, `Str/Lvl` 10..15, `Dex/Lvl` 8..16, `Dmg/Lvl` 2..8,
  `LvlPerLvl_i` 0..10). This covers the column arithmetic, not the choice of row: `RollEntry` always uses the
  first band's row, so the band lookup (`HIRELING_GetRecord`) stays inferred (the claim above). `HIRELING_RollEntry` reads the same offsets with the same operation (eighths
  for `Str/Lvl`, `Dex/Lvl`, `Dmg/Lvl`; plain products for `HP/Lvl`, `Def/Lvl`) and the same clamps (10, 10, 40, 0, 1),
  and the client's `sub_004B1090_ClientMercInit` computes `min(32, Level_i + (LvlPerLvl_i·d >> 5))` from the same
  bytes. For a negative product the paths round differently (floor in `RollEntry`, truncation in `MERC_SetLevel`), and AR and
  resistances have no second path; run:2026-10-16-hirelings settles those (the claim above). (fn:MERC_SetLevel@0x00572840,
  fn:HIRELING_RollEntry@0x006637F0, fn:sub_004B1090_ClientMercInit@0x004B1090, tbl:Hireling.txt:HP/Lvl,
  tbl:Hireling.txt:Def/Lvl, tbl:Hireling.txt:Str/Lvl, tbl:Hireling.txt:Dex/Lvl, tbl:Hireling.txt:Dmg/Lvl,
  tbl:Hireling.txt:Level1, tbl:Hireling.txt:LvlPerLvl1)
- [C] **Experience gives the level through `ExpForLevel(L) = (L+1)·L²·Exp/Lvl`**: a loaded mercenary's level is the
  greatest L ≤ 99 whose `ExpForLevel(L)` (with the row of band L−1) is ≤ its experience. Two code paths compute the
  same threshold (the hire list's inline product and `HIRELING_ExpForLevel`), and the `exphellmerc` save of
  run:2026-10-12-mon-pool-p2 (Id 4, `Exp/Lvl` 120, experience 500 000) gives 15, the level its screen showed;
  run:2026-10-16-hirelings adds 23 loads (every class and difficulty, L 3 to 80). (run:2026-10-16-hirelings,
  fn:HIRELING_ExpForLevel@0x00663790, fn:D2S_ReadMercHeader@0x0056AA50, run:2026-10-12-mon-pool-p2,
  tbl:Hireling.txt:Exp/Lvl)
- [C] **The MonStats class is the row's `Class`**: 271, 338, 359 and 561. All four take monsters/pool's E2 (`d` = 0,
  MonStats `Level` 1), and `MERC_SetLevel` then overwrites the level stat and the stats above, in a fresh hire and in
  a load: 49 hires and 23 loads, each class in the three difficulties (expansion; 271, 338, 359 also classic), every
  MonStatsInit level 1 with `d` 0 (`tools/monpool.py check`, 10 788 of 10 788). [I] No `hireling.txt` row has 560
  (`act5hire1`), so no hire or save path creates it (data). (run:2026-10-16-hirelings, fn:MERC_Create@0x005774F0, fn:sub_0063EE90_HirelingType@0x0063EE90, fn:sub_00573CB0_MonStatsInit@0x00573CB0,
  tbl:Hireling.txt:Class)
- [C] **A hireling's kill counts its owner's magic find**: `MERC_Init` sets the mercenary's owner to the hiring
  player (`sub_0058F030_MonSetOwner`), which is what `MonsterOwner` reads in `ITEMS_DropMagicFind`. This answers the
  items/quality lead from the code; run:2026-10-16-hirelings logged three kills by a mercenary: total 40, its own
  stat 80 (0) plus its owner's (40, the player's full stat list). (run:2026-10-16-hirelings,
  fn:sub_0058F030_MonSetOwner@0x0058F030,
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
  (tbl:Hireling.txt:Version, tbl:Hireling.txt:Act, tbl:Hireling.txt:Difficulty, tbl:Hireling.txt:Class,
  tbl:Hireling.txt:Seller)
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
  player, never above (0x00663874–0x006638BB, re-read). Phase 2 required case: list levels against the player level;
  settled by run:2026-10-16-hirelings (530 entries at −5 .. −1).
- [L] src:d2dfg-blizzard: `HireDesc` is a string key. **contradicted**
  Detail: in 1.14d it is a `hiredesc.txt` code (`farw`, `comb`, `def` …) stored as a u8 row of `hiredesc`
  (`+0xD2`, read by `RollEntry` into its output `+0x30`); the layout is `[C]` by the data check (§ 1). Settled by data;
  not a Phase 2 case. (tbl:Hireling.txt:HireDesc, tbl:HireDesc.txt:Code)
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
  classic Fire, `Level` 3, `Resist/Lvl` 8, at L = 10: 14 against 7); settled by run:2026-10-16-hirelings (32 levels
  where the two differ, all ÷4).
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
| `0x006562F0` | `HIRELING_GetRecord` | `(version flag, id, level)` → row of that Id whose `Level` band holds `level` | C |
| `0x00656390` | `HIRELING_NextByName` | next row whose name range holds a string index | I |
| `0x00656440` | `HIRELING_NextByClass` | next row with a `Class` | I |
| `0x006564D0` | `HIRELING_NextBySeller` | next row with `Seller` and `Difficulty` | I |
| `0x00656580` | `HIRELING_NextByActDiff` | next row with `Act`, `Difficulty` and the previous row's `Level` | C |
| `0x00663750` | `HIRELING_GetAct` | act index (`Act` − 1) by class, else by name index | C |
| `0x00663790` | `HIRELING_ExpForLevel` | `(L+1)·L·L·expPerLvl` | C |
| `0x006637B0` | `MERC_ResurrectCost` | resurrection price (named only) | I |
| `0x006637F0` | `HIRELING_RollEntry` | seed → Id, level, price, experience and displayed stats | C |
| `0x00575FF0` | `HIRE_GetNameRange` | seller's Normal row: first, last name index, class | C |
| `0x00576070` | `HIRE_BuildStock` | the hire table and its 10 picks | C |
| `0x00576770` | `HIRE_SendList` | builds if needed; sends each listed, unhired entry | C |
| `0x00577010` | `HIRE_RebuildIfEmpty` | rebuild when nothing listed is left | C |
| `0x005770E0` | `HIRE_Hire` | the hire request | C |
| `0x00579180` | `HIRE_GiveFreeMerc` | quest gift (`a1q2.cpp` → Kashya, `a3q3.cpp` → Asheara) | I |
| `0x005774F0` | `MERC_Create` | creates the monster for a loaded mercenary | C |
| `0x00573270` | `MERC_Init` | replaces the old mercenary, pet info, owner; fresh hire: experience and level | C |
| `0x00572840` | `MERC_SetLevel` | level, experience floor, stats and skills from the band row | C |
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
| `0x00535EA0` | `NPCSTORE_FindRec` | NPC record by MonStats row | I |
| `0x00536070` | `NPCSTORE_CtlCreate` | NPC records and the NPC seed, at game creation | C |
| `0x00536B40` | `NPCSTORE_GetSeed` | `&NpcControl.seed` | I |
| `0x00576890` | `VENDOR_StockLevel` | Normal only: `min(level, {12,20,28,36,45}[act])` | I |
| `0x00576D90` | `sub_00576D90_PayGold` | takes a price from gold, then the stash | I |
| `0x00572C10` | `sub_00572C10_NpcInteractStart` | an NPC starts interacting with a player | I |
| `0x00578B30` | `NPC_OpenStore` | trade start: vendor stock, then hire table if not built | I |
| `0x00579D60` | `NPC_MenuAction` | NPC menu command; 3 = open the hire list | I |
| `0x0058F030` | `sub_0058F030_MonSetOwner` | sets a monster's owner unit | I |
| `0x004B1090` | `sub_004B1090_ClientMercInit` | client: mercenary skills and name | I |
| `0x004B5C60` | `sub_004B5C60_ClientHireListDraw` | client: the hire list window | I |

Data: `data:g_pHirelingTxt@0x0096BDD0` (records), `data:g_nHirelingTxt@0x0096BDD4` (count),
`data:g_HirelingFirstById@0x0096BDD8` (2 × 256 i32: first row index per Id, classic half then expansion half; −1 =
none).

## Walkthrough

### 1. The table and its lookups

The loader (fn:HIRELING_LoadTable@0x00655720) declares these fields; the offsets are those of
`struct:HirelingRec+0x000` and are `[C]` by the data check above; the column-by-column layout is
[Hireling § Columns](../../tables/Hireling.md#columns). The `.txt` columns `Hireling`, `SubType`,
`WType1`, `WType2` are not loaded. [C] (tbl:Hireling.txt:Hireling, tbl:Hireling.txt:SubType, tbl:Hireling.txt:WType1)

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
(fn:HIRELING_LoadTable@0x00655720, fn:sub_00408F20_HasExpansionMpq@0x00408F20, tbl:Hireling.txt:Id,
tbl:Hireling.txt:Version)

In the stock data the name ranges are: Rogue `merc01`..`merc41` = 3411..3451 (41 names), Act II `merca201`..`merca221`
= 1019..1039 (21), Act III `merca222`..`merca241` = 1040..1059 (20), Barbarian `MercX101`..`MercX167` = 10835..10901
(67), from `tools/tbl.py lookup` on the English tables. [I] (fn:STRTABLE_GetByKey@0x00524D30,
tbl:Hireling.txt:NameFirst, tbl:Hireling.txt:NameLast)

`HIRELING_GetRecord(version flag, id, level)` [C] (run:2026-10-16-hirelings, fn:HIRELING_GetRecord@0x006562F0):

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
That relies on the rows of one Id being in `Level` order, which the stock file is. [I] (fn:HIRELING_GetRecord@0x006562F0,
tbl:Hireling.txt:Id, tbl:Hireling.txt:Level)

`HIRELING_NextByActDiff(vflag, act, diff, prev)` returns the next row after `prev` with `Act = act + 1`,
`Difficulty = diff + 1`, the version, and, when `prev` is given, `Level = prev.Level`. Starting from none and chaining,
it lists the rows of the first `Level` band only: one row per type. [C] (run:2026-10-16-hirelings, fn:HIRELING_NextByActDiff@0x00656580,
tbl:Hireling.txt:Act, tbl:Hireling.txt:Difficulty, tbl:Hireling.txt:Level)
`HIRELING_NextBySeller(vflag, seller, diff, prev)` matches `Seller` and `Difficulty = diff + 1`;
`HIRELING_NextByName` matches `+0x114 ≤ index ≤ +0x116`; `HIRELING_NextByClass` matches `Class`. `HIRELING_GetAct(vflag,
class, name)` is `Act − 1` of the first row by class, else by name, else 0. [I] (fn:HIRELING_NextBySeller@0x006564D0,
fn:HIRELING_NextByName@0x00656390, fn:HIRELING_NextByClass@0x00656440, fn:HIRELING_GetAct@0x00663750,
tbl:Hireling.txt:Seller, tbl:Hireling.txt:Class)

### 2. The NPC records and the NPC seed

At game creation, after `sub_00547D20_MonRegionsInit` (game draw 1) and `OBJRGN_Create` (draw 2),
`NPCSTORE_CtlCreate` allocates the NPC control block (`.\UNIT\sunitproxy.cpp`) and 64 records of 0x44 bytes,
one per MonStats row with the NPC flag. It does `InitOne(seed)`, one step of the game seed, `Init(seed, low)`. Its
static call graph holds no other RNG use (`tools/ghidra.sh rngcallgraph`). So the NPC seed is seeded from game draw 3.
[C] (run:2026-10-16-hirelings, fn:NPCSTORE_CtlCreate@0x00536070, 0x005360D2–0x005360FB, fn:sub_00530BF0_GameCreate@0x00530BF0)

A record's `act` (+0x22) and `trader` (+0x23) bytes come from a 43-entry table at `0x00731188` (8 bytes each: MonStats
row, then trader, act, and a third flag): Kashya 150 → trader 0, act 0; Greiz 198 → 0, 1; Asheara 252 → 1, 2;
Qual-Kehk 515 → 0, 4. [I] (fn:NPCSTORE_CtlCreate@0x00536070)

The NPC seed is also drawn by vendor code (`0x00576330`, `0x005786A0`, `0x00578790`, `0x00579030`, `0x00576980`
reach `NPCSTORE_GetSeed`; plan 0031's subject, where this seed is called the store seed). Its draws interleave with
the hire builds in game order: [C] by run:2026-10-15-vendors (the store seed at the entry of every logged stock,
gamble and `HIRE_BuildStock` call is the chain of the vendor model plus the logged hire builds). In
run:2026-10-16-hirelings no trade or gamble window was opened, so the chain there is hire builds only.
(fn:NPCSTORE_GetSeed@0x00536B40, run:2026-10-15-vendors, [items/0009 § 1](../items/0009-vendors.md#1-store-records-and-the-store-seed-game-creation))

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

- [C] `HIRE_GetNameRange` takes `HIRELING_NextBySeller(vflag, seller, 0, none)`: the first row of the seller with
  `Difficulty` 1. So the name range (and the class used for the hire) is the same in every difficulty; a range with
  `last − first + 1 = −1` is fatal. (run:2026-10-16-hirelings, fn:HIRE_GetNameRange@0x00575FF0, tbl:Hireling.txt:Seller,
  tbl:Hireling.txt:Difficulty, tbl:Hireling.txt:NameFirst, tbl:Hireling.txt:NameLast)
- [C] Every name index gets a seed, whether it is picked or not, and the seeds are drawn before the picks.
  (run:2026-10-16-hirelings, fn:HIRE_BuildStock@0x00576070)
- [C] On a fresh table nothing is listed or hired, so the 10 picks give 10 distinct names (every `n` is ≥ 20). The
  probe never draws. (run:2026-10-16-hirelings, fn:HIRE_BuildStock@0x00576070)
- [C] **When.** `HIRE_SendList(npc)` returns at once unless the NPC is one of 150, 198, 515, 252; it then builds the
  table if `hireBuilt` is 0 and sends every entry with `listed ≠ 0` and `hired = 0`. It is called from
  `sub_00572C10_NpcInteractStart` (an NPC begins interacting with a player), from `NPC_MenuAction` command
  3 (the hire list) and after a hire. `NPC_OpenStore` would also build it for an NPC whose `trader` byte
  is set (Asheara), after the vendor stock, but the interaction start comes first. So the build is at the first talk
  with each of the four NPCs in a game. (run:2026-10-16-hirelings, fn:HIRE_SendList@0x00576770, fn:sub_00572C10_NpcInteractStart@0x00572C10,
  fn:NPC_MenuAction@0x00579D60, fn:NPC_OpenStore@0x00578B30)
- [C] **Rebuild.** `HIRE_RebuildIfEmpty` counts the entries with `listed ≠ 0` and `hired = 0`; at 0 it frees the
  table, clears `pHireTable` and `hireBuilt` and calls `HIRE_BuildStock` again (another `n + 10` NPC draws). It runs
  after each hire and after a free mercenary. Nothing else clears the table during a game. (run:2026-10-16-hirelings, fn:HIRE_RebuildIfEmpty@0x00577010)

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

- [C] `act` is `HIRELING_GetAct(vflag, 0, name)`: the act of the row whose name range holds the entry's name, so a
  list shows its own act's types. `diff` is the game's difficulty. (run:2026-10-16-hirelings, fn:HIRE_Hire@0x005770E0, 0x0057725C–0x0057727A)
- [C] The seed only decides the type (draw 1) and the level offset `0..4` (draw 2). The level follows the player's
  **current** level each time the entry is rolled: the client rolls it to draw the list and the server rolls it again
  at the hire, so a level-up between the two changes the mercenary bought (a level-up between the two did not happen
  in the run: that consequence stays `[I]`). (run:2026-10-16-hirelings, fn:HIRELING_RollEntry@0x006637F0,
  fn:sub_004B5C60_ClientHireListDraw@0x004B5C60, fn:HIRE_Hire@0x005770E0)
- [C] The displayed stats extrapolate from the **first band's row**, with floor division for the eighths, while the
  stats in the world (§ 6) use the row of the mercenary's own band and truncating division. They agree only while
  `L` is inside the first band and `d ≥ 0`. (run:2026-10-16-hirelings, fn:HIRELING_RollEntry@0x006637F0, fn:MERC_SetLevel@0x00572840)
- [C] The price is the `Gold` column raised 15 % per level above the band start, never below `Gold`.
  (run:2026-10-16-hirelings, 0x0066391F–0x0066394C, tbl:Hireling.txt:Gold)
- [I] The client list window draws up to 10 entries. It shows name index 1057 (`Lharhad`) as 11021 (`Jarulf`), and
  so does the client's mercenary init. (fn:sub_004B5C60_ClientHireListDraw@0x004B5C60,
  fn:sub_004B1090_ClientMercInit@0x004B1090)

### 5. The hire

`HIRE_Hire(npc, nameIdx)` (EDX = the player) [I] (fn:HIRE_Hire@0x005770E0):

1. Qual-Kehk (515) refuses unless bit 0 of quest word 36 is set in the player's quest record for the game's difficulty;
   Kashya (150) refuses when `VENDOR_StockLevel(playerLevel) < 8` and bit 0 of quest word 2 is clear. The cap
   is `min(level, {12, 20, 28, 36, 45}[npc.act])` in Normal and the level itself otherwise, so for Kashya this is
   "player level below 8". (fn:QUESTRECORD_GetState@0x0065C310, fn:VENDOR_StockLevel@0x00576890)
2. The name must lie in the seller's range, the table entry at `nameIdx − first` must carry that name and have
   `hired = 0`. **`listed` is not checked.** (0x005771E8–0x00577258)
3. `HIRELING_RollEntry(entry.seed, act, difficulty)` gives the price; `sub_00576D90_PayGold` takes it from gold
   (stat 14), the remainder from the stash (stat 15), or refuses if the two together fall short.
4. The mercenary is spawned with `sub_005B23C0_SpawnNearUnitNoBox(class, 1, 4, 0)`, tried twice, where `class` is
   the `Class` of the seller's Normal row (271, 338, 359, 561; tbl:Hireling.txt:Class). `entry.hired ← 1`.
5. `MERC_Init(merc, 0xFFFF, entry)`, then the list is resent, a hire message sent, `HIRE_RebuildIfEmpty`.

`MERC_Init(merc, id, {name, seed}, dead)` [C] (run:2026-10-16-hirelings, fn:MERC_Init@0x00573270):

- sets the unit flags `0x4020200`, alignment 2 (`sub_005543B0_MonAlignSet`); if the player already has a
  mercenary (pet type 7, dead or alive), it is released and removed;
- `RollEntry(seed, GetAct(vflag, 0, name), difficulty)` → `out`; `PETS_Add(merc, 7, {seed, name, out.id})`;
- `sub_0058F030_MonSetOwner(merc, player id, player type)` writes the owner into the monster's AI block
  (`monsterData+0x28` → `+0x2C` id, `+0x30` type, `+0x28` the game);
- **fresh hire only** (`id = 0xFFFF`): `row ← GetRecord(vflag, out.id, out.level)`; stat 13 ← `out.exp`;
  `MERC_SetLevel(merc, out.level)`; `sub_005726C0_MercSendStats`.

So the header the save writes (`D2S_WriteMercHeader`: seed, name − `+0x114`, Id, experience, dead flag) holds the
entry's seed, the name, the Id rolled from that seed, and the experience. [C] (§ Plan 0038 batch H1b,
run:2026-10-27-sweep-d2s-play, fn:D2S_WriteMercHeader@0x00568E60,
fn:PETS_GetInfo@0x00574BD0)

**Free mercenary.** `HIRE_GiveFreeMerc(seller)` (called with 150 from `a1q2.cpp` code and 252 from `a3q3.cpp` code)
gives one when the player has none (expansion: no mercenary at all, dead or alive; classic: no living one) and the
seller's table exists: the first entry in name order with `listed = 1` and `hired ≠ 1` becomes hired and is spawned
(class from `NextBySeller(vflag, seller, difficulty)`; ranges 4, 6, 12) and initialised like a hire, with no payment
and no quest gate. [I] (fn:HIRE_GiveFreeMerc@0x00579180)

### 6. The stats per level (`MERC_SetLevel`)

`MERC_SetLevel(merc, L)` [C] (run:2026-10-16-hirelings, fn:MERC_SetLevel@0x00572840), with `row = GetRecord(vflag, info.id, L)` and
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

[C] for a non-negative product `column·d` (on stock data: `d ≥ 0`), the strength, dexterity, life, defence and
damage rows: `HIRELING_RollEntry` (§ 4) reads the same offsets (`+0x34`/`+0x38`, `+0x3C`/`+0x40`, `+0x24`/`+0x28`,
`+0x2C`/`+0x30`, `+0x50`/`+0x54`/`+0x58`) with the same operation and clamp, and for a non-negative product floor and
truncation agree. The choice of `row` is not covered (`RollEntry` uses the first band's row). [C] The whole table,
the row choice included, by run:2026-10-16-hirelings: 72 calls (49 hires, 23 loads) reproduced stat for stat, with
`d` from −41 to 27 (17 levels where a negative product's truncation and floor differ, 32 where `Resist/Lvl` ÷4 and ÷8
differ) and the clamps reached (life 40; AR and defence 0, which leave no entry in the stat list); `nextexp`,
the experience floor and `hpregen` included. The resistance divisor 4 was re-read after the cross-check
(`cdq; and edx, 3; add eax, edx; sar eax, 2` at 0x00572A7D–0x00572A83). (run:2026-10-16-hirelings,
fn:MERC_SetLevel@0x00572840,
fn:HIRELING_RollEntry@0x006637F0, 0x006638C0–0x006639E1, tbl:Hireling.txt:Str/Lvl, tbl:Hireling.txt:Dex/Lvl,
tbl:Hireling.txt:HP/Lvl, tbl:Hireling.txt:Def/Lvl, tbl:Hireling.txt:Dmg/Lvl, tbl:Hireling.txt:AR/Lvl,
tbl:Hireling.txt:Resist/Lvl)

Skills, for `i` = 1..6 in order, stopping at the first `Skill_i < 1` or ≥ the skill count, or `Mode_i > 15` (signed):
if `reqlevel` of the skill (Skills `+0x174`) ≤ L, `slvl = Level_i + (LvlPerLvl_i·d >> 5)` (a plain `sar`: floor),
`min(slvl, 32)`, and the skill is added when `slvl ≥ 1`. [C] (run:2026-10-16-hirelings, 0x00572B3A–0x00572B7E, fn:SKILLS_GetRecord@0x0045C4B0,
fn:sub_0056DEB0_UnitSkillAdd@0x0056DEB0, tbl:Skills.txt:reqlevel, tbl:Hireling.txt:Skill1, tbl:Hireling.txt:Mode1,
tbl:Hireling.txt:Level1, tbl:Hireling.txt:LvlPerLvl1)
The skill level itself, `min(32, Level_i + (LvlPerLvl_i·d >> 5))` for `d ≥ 0` (stock `LvlPerLvl_i` ≥ 0), is [C]: the client's
`sub_004B1090_ClientMercInit` computes it from the same bytes (`movsx` of `+0xCC + i` and `+0xC6 + i`, `sar 5`, cap
0x20, 0x004B115A–0x004B1178), with `d` clamped at 0 and no `reqlevel` test. (fn:sub_004B1090_ClientMercInit@0x004B1090)

`ExpForLevel(L, e) = (L+1)·L·L·e` (i32 products). The 99 is `sub_00611830_ExpMaxLevel(0)` (`experience.txt`
`MaxLvl`, Amazon column). [C] for the formula (fn:HIRELING_ExpForLevel@0x00663790; second code path: the inline
product at 0x0066394F–0x00663968 in fn:HIRELING_RollEntry@0x006637F0; run:2026-10-12-mon-pool-p2;
tbl:Hireling.txt:Exp/Lvl)
(fn:sub_00611830_ExpMaxLevel@0x00611830)

**Levelling in play** (named, not specified): `MERC_AddExp` adds experience and calls `MERC_SetLevel` for each level
reached, only while the mercenary's level is below its owner's; `MERC_CapExpGain` caps one gain at
`(ExpForLevel(L+1) − ExpForLevel(L)) >> 6`. [I] (fn:MERC_AddExp@0x0057E860, fn:MERC_CapExpGain@0x0057E3F0)

### 7. The mercenary from a save

`D2S_ReadMercHeader(hdr + 0xAF)` [C] (run:2026-10-16-hirelings, fn:D2S_ReadMercHeader@0x0056AA50; the dead flag, a
name past `NameLast` and the empty header not exercised: those lines stay [I]):

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

`MERC_Create` [C] (run:2026-10-16-hirelings, fn:MERC_Create@0x005774F0):

- **classic** (`vflag = 0`): the mercenary is created only if `GetAct(vflag, 0, name)` ≥ 0 equals the player's act
  (`Client+0x1AC`, or the unit's own byte when it has no client). An expansion game creates it anywhere. In the run:
  10 classic loads in Act IV were not created, the 9 in the mercenary's own act were, and the 14 expansion loads (all
  in Act IV) were.
- [I] (not exercised: no hire table existed at a load) if the seller's hire table exists and the name's entry is
  not listed, the entry is marked hired (fn:MERC_Create@0x005774F0);
- the row is `GetRecord(vflag, id, 1)` (or, for id `0xFFFF`, the first `NextByActDiff(vflag, act, difficulty)` row);
  the name is clamped into its range (id `0xFFFF` and a name past the range not exercised);
- `sub_00555230_SUnitCreate(type 1, class, …, mode = dead ? 12 : 1)`, then `MERC_Init(merc, id, {name, seed}, dead)`.

So for a loaded mercenary the **seed** is carried in the pet info and rolled once more inside `MERC_Init` (for an Id
that `PETS_SetInfo` then overwrites with the saved one); it does not reach the stats. The level and stats come from
the experience and the saved Id. The mercenary's items are read after the header, into the unit `MERC_Create`
returned ([save/0001](../save/0001-d2s-io.md), `D2S_ReadMercItems`). [I] (fn:D2S_ReadMercItems@0x0056AC10)

**The `exphellmerc` case** (run:2026-10-12-mon-pool-p2): Id 4 (`Fire - Hell`, expansion, one row at `Level` 67,
`Exp/Lvl` 120), experience 500 000. Every `GetRecord(…, L)` with L < 67 returns that row. `ExpForLevel(15) =
16·225·120 = 432 000 ≤ 500 000` and `ExpForLevel(16) = 17·256·120 = 522 240 > 500 000`, so L = 15, the level shown on
its screen; MonStatsInit had made it at level 1. [C] (fn:D2S_ReadMercHeader@0x0056AA50, run:2026-10-12-mon-pool-p2)
With L = 15 and `Level` 67, `d = −52`: strength `110 + (10·−52) ÷8 = 110 − 65 = 45`, life `max(40, 779 + 30·−52) = 40`.
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

- [C] Every hire and load path takes the class from a `hireling.txt` row (`HIRE_GetNameRange`, `NextBySeller`, or the
  saved Id's row), and the stock file's `Class` column holds only 271, 338, 359 and 561, in both versions.
  (run:2026-10-16-hirelings, fn:MERC_Create@0x005774F0, fn:HIRE_Hire@0x005770E0, fn:HIRE_GiveFreeMerc@0x00579180)
- [C] `sub_0063EE90_HirelingType` tests only the unit type and class, not the version flag, so a classic game takes
  the same E2 step. Classic uses the `Version` 0 rows: Act I base `Level` 3, Act II 9, Act III 15; the `Version` 0
  Barbarian rows exist but no classic act reaches them. (run:2026-10-16-hirelings, fn:sub_0063EE90_HirelingType@0x0063EE90)
- [C] Whatever the MonStatsInit level was, `MERC_SetLevel` overwrites stat 12 and the stats of § 6 right after the
  creation (`MERC_Init` for a hire, `D2S_ReadMercHeader` for a load). (run:2026-10-16-hirelings, fn:MERC_Init@0x00573270)

### 9. Magic find on a hireling's kill

- [C] `ITEMS_DropMagicFind(killer)` adds the stat 80 of `MonsterOwner(killer)`. `MonsterOwner` returns the unit whose
  id is at `monsterData+0x28 → +0x2C` when that block's `+0x28` is non-zero. `MERC_Init` writes exactly that block
  with the hiring player's id and type and the game pointer, so a mercenary's kill uses the mercenary's stat 80 plus
  the player's. (run:2026-10-16-hirelings, fn:sub_0058F030_MonSetOwner@0x0058F030, fn:sub_0058F0D0_MonsterOwner@0x0058F0D0,
  fn:ITEMS_DropMagicFind@0x005585D0, 0x005733A3–0x005733B2)

### 10. Named only

- [I] Resurrection: `MERC_Resurrect` at Kashya, Greiz, Asheara, Tyrael (`tyrael2`, 367) or Qual-Kehk, for a dead mercenary,
  price `MERC_ResurrectCost = min(50000, (L²/2)·15)` (unsigned compare), paid like a hire. (fn:MERC_Resurrect@0x00579C00,
  fn:MERC_ResurrectCost@0x006637B0)
- [I] Death: `PETS_OnDeath` sets the pet node's dead bit; a mercenary (pet type 7) stays in the list.
  (fn:PETS_OnDeath@0x005751A0)
- [I] Combat skill choice: `MERCAI_PickSkill` reads `DefaultChance`, `Chance_i`, `ChancePerLvl_i` and `Mode_i`. Out of
  scope (ADR-0002). (fn:MERCAI_PickSkill@0x005E4D30, tbl:Hireling.txt:DefaultChance, tbl:Hireling.txt:Chance1,
  tbl:Hireling.txt:ChancePerLvl1, tbl:Hireling.txt:Mode1)

### 11. Phase 2 boundary (recommendation; the architect rules)

**Recommended: the hire list from the NPC seed on entry to each build, as a boundary oracle (ADR-0004).**
`tools/hirelings.py` models `HIRE_BuildStock`, `HIRELING_RollEntry`, `MERC_SetLevel` and the save's level loop. The
NPC seed is shared with vendor code (plan 0031), so the model takes the seed logged on entry to each
`HIRE_BuildStock` and asserts it; the vendor draws between two builds are an oracle, not modelled. Separately, one
check per game that the NPC seed starts at `Init(low of game draw 3)` (log `NPCSTORE_CtlCreate` exit).

What to log (`tools/gdb/hirelings.gdb`):

| Where | What |
|---|---|
| `NPCSTORE_CtlCreate` exit | game seed, NPC seed |
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

## Phase 2: runtime results (run:2026-10-16-hirelings)

`tools/hirelings.py` models § 3–§ 8 as § 11 recommended and the review ruled: the NPC seed checked once per game
against `Init(low of game draw 3)`, then chained through every `HIRE_BuildStock` (no vendor build happened between,
so no oracle was needed), each table built from it; every `HIRELING_RollEntry` from its logged seed, act,
difficulty and player level; the hire (price, payment, `MERC_Init`'s pet info, the class); every `MERC_SetLevel` from
the mercenary's Id and level; the save's level loop and `MERC_Create`'s classic act test. Over 48 games on harness
slot 1 ([experiments](experiments.md#run2026-10-16-hirelings)): 53 hire tables (all four sellers in Normal,
Nightmare and Hell; one rebuild), 2625 draws on the NPC seed, 723 `RollEntry` calls from its four callers, 49 hires,
33 mercenary headers read (23 mercenaries created and levelled, 10 classic ones refused by the act test), 72
`MERC_SetLevel` stat blocks and 3 mercenary kills reproduce with 0 mismatches; `tools/monpool.py` reproduces every
creation's MonStatsInit level (10 788 of 10 788, the four hireling classes at level 1 in every difficulty). The tags
above are promoted where the run reaches them, with run:2026-10-16-hirelings among their anchors. Not reached, so
still `[I]`: the free mercenary, refused hires, the stash part of the payment, a hire of an unlisted entry, the build
through `NPC_OpenStore`, a level-up in play (`MERC_AddExp`), a dead or empty mercenary header, the written save
header, multiplayer sharing, classic hire lists. Class 560 is unreachable on stock data (no row). The Phase 1b
contradictions (a) and (b) are settled for 1.14d as read (§ Open questions).

## Data touched

- `hireling` records: every loaded column of [Hireling](../../tables/Hireling.md) (`tbl:Hireling.txt:Version` …
  `tbl:Hireling.txt:NameLast`, the same bytes as `struct:HirelingRec+0x000`); `+0x114`/`+0x116` (no column) written at
  load from `tbl:Hireling.txt:NameFirst`/`NameLast`.
- `tbl:Hireling.txt:HireDesc` (`+0xD2`), a row index of `tbl:HireDesc.txt:Code`; copied by `RollEntry`, its text not read.
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

## Plan 0038 batch S3a (2026-10-16)

Static batch S3a of [plan 0038](../../plans/0038-inferred-claims-sweep.md) took 3 inferred statements of
[hirelings](../../specs/hirelings/README.md), rows of [the inventory](../../plans/0038-inventory/hirelings-README.md) (spec lines
`Lnnn` at `main` `b349849`). No game ran. The check is `python3 -I tools/mon_sweep.py hire` over the 48 kept logs of
run:2026-10-16-hirelings (sha256 against `hire-run-manifest.txt`, itself `4559f158…`); `tools/hirelings.py check` still reports
0 mismatches on them. The addendum is under the run in [experiments.md](experiments.md#run2026-10-16-hirelings).

```
hire tables logged 53 (Asheara 14, Greiz 10, Kashya 13, Qual-Kehk 16): slot i holds name first + i in all 53,
  the slots past the seller's range zero in all 53; stock ranges 20, 21, 41, 67 (largest 67 of 69 slots)
hires 49: entry t[name - first] holds the name, is not hired, and its seed is MERC_Init's: 49
  cf: MERC_Init's seed equal to another listed entry's seed: 0 of 49
merc headers 48: all zero 15, MERC_Create entered 0; name 0 with seed and experience set 30, entered 30;
  name, seed and experience set 3, entered 3; dead bit 0
```

- **hirelings 4** (L106) **raised in part.** [C] The table is 16-byte slots, slot `i` the name `first + i`: `HIRE_BuildStock`
  writes it with stride 16 (`shl 4`, 0x00576177) and its two readers walk it with stride 16 at the same fields
  (`HIRE_SendList` 0x00576849–0x00576877: `+8` hired, `+0xC` listed, `+0` name, `+4` seed; `HIRE_RebuildIfEmpty`
  0x0057707F–0x00577095), and the 53 logged tables hold that layout with every slot past the range zero.
  (fn:HIRE_BuildStock@0x00576070, fn:HIRE_SendList@0x00576770, fn:HIRE_RebuildIfEmpty@0x00577010, run:2026-10-16-hirelings)
  **Remainder, d-none:** the 0x450-byte size (69 slots): no stock seller has more than 67 names, so the bound never binds.
- **hirelings 19** (L332) **raised in part.** [C] The hire reads `t[nameIdx − first]`: in all 49 hires that slot holds the
  hired name with `hired` 0, and its seed is the one `MERC_Init` receives; no other listed entry had that seed (`cf`).
  (fn:HIRE_Hire@0x005770E0, 0x005771E8–0x00577258, fn:MERC_Init@0x00573270, run:2026-10-16-hirelings) **Remainder `[I]`:** the
  refusals (a name outside the range, a slot holding another name or already hired), which no hire met.
- **hirelings 26** (L453) **raised in part.** [C] An empty header gives no mercenary: none of the 15 all-zero headers entered
  `MERC_Create` (no `MCA` line), while all 33 others did, 30 of them with a saved name of 0 and seed and experience set, so a
  zero name alone does not stop the read. (fn:D2S_ReadMercHeader@0x0056AA50, 0x0056AA5B–0x0056AA7A, run:2026-10-16-hirelings)
  **Remainder, d-none:** a header whose seed or experience alone is 0 (a hired mercenary has experience, and a seed of 0 is
  one value in 2³²).

## Plan 0038 batch H4b (run:2026-10-16-sweep-monsters-b)

Harness batch H4b of [plan 0038](../../plans/0038-inferred-claims-sweep.md) took one row of
[hirelings](../../specs/hirelings/README.md) ([inventory](../../plans/0038-inventory/hirelings-README.md), row 34).

- **hirelings 34** (L522) **raised.** [C] A hireling gets no player-count bonus: in session 5 of
  [run:2026-10-16-sweep-monsters-b](../monsters/experiments.md#run2026-10-16-sweep-monsters-b) `/players 8` was typed, the
  game left with *Save and Exit*, and a second game started in the same process with the setting still 8; the
  `roguehire` hireling (class 271, `Align` 1) was created with `MonPlayerBonus` record players 1, HP and XP percent 0,
  which `tools/monstats.py` reproduces. (0x0057396C, fn:sub_00573930_MonPlayerBonus@0x00573930, tbl:MonStats.txt:Align,
  run:2026-10-16-sweep-monsters-b) Its live stats then are the save's (level 30), not the creation's; the stats model does
  not cover that load.

## Plan 0038 batch S3b (2026-10-16)

Static batch S3b of [plan 0038](../../plans/0038-inferred-claims-sweep.md) took 2 inferred statements of
[hirelings](../../specs/hirelings/README.md), rows of [the inventory](../../plans/0038-inventory/hirelings-README.md) (spec lines
`Lnnn` at `main` `7df5039`). No game ran. The check is `python3 -I tools/sweep_s3b.py hire`: the Hireling table read with
`tools/hirelings.py`'s loader, objdump pins of the pinned image (the second tool, as ruled at the S4b review), and
`tools/hirelings.py check` re-run on the 48 logs of run:2026-10-16-hirelings (0 mismatches; addendum under the run in
[experiments.md](experiments.md#run2026-10-16-hirelings)).

```
S3B hire bands=120 firstbyid_refs=7 hirelings_check_rc=0 ids=60 pins=19 rows=120 stock_first_zero=0
         stock_id_ge_256=0 stock_last_le_first=0 walks=7326
  Version values {0: 60, 100: 60}; Ids 0..29
  instructions naming g_HirelingFirstById or its bounds: 0x00656175, 0x00656192, 0x0065624D, 0x00656254,
    0x006562C5, 0x006562DB, 0x00656322
  stock name ranges (first..last): [(1019, 1039), (1040, 1059), (3411, 3451), (10835, 10901)]
  tools/hirelings.py check on 48 logs of run:2026-10-16-hirelings: hirelings: 0 mismatches
```

- **hirelings 7** (L151) **raised.** [C] `GetRecord` returns the row of the Id with the greatest `Level` ≤ `L`, or the
  Id's first row when `L` is below every band. Data behaviour: in all 60 (version, Id) groups of the stock table (120 rows,
  `Version` only 0 and 100) the rows stand in strictly increasing `Level` order, and the walk of A3 as `tools/hirelings.py`
  models it gives exactly that row for all 7 326 inputs tried (both version flags, Ids 0–30, 255 and 256, `L` −5..105).
  The walk itself is the model that reproduces the 72 `MERC_SetLevel` calls and the 723 `RollEntry` calls of the run.
  (fn:HIRELING_GetRecord@0x006562F0, tbl:Hireling.txt:Level, run:2026-10-16-hirelings)
- **hirelings 8** (L154) **raised in part.** [C] The first-row index and the name indices, by writer and reader pairs read
  with objdump (fn:HIRELING_LoadTable@0x00655720, run:2026-10-16-hirelings; detail and anchors below):
  - `HIRELING_LoadTable` computes `(Version < 100 ? 0 : 1)·256 + Id` (`cmp word [rec], 0x64; sbb; add 1; shl 8` at
    0x0065623E–0x00656248), skips `Id` ≥ 256 (0x00656236), and stores the row index only while the slot is still negative
    (0x0065624D, 0x0065625D), after both halves were set to −1 (0x00656180). `HIRELING_GetRecord` reads the slot at
    `(vflag ≠ 0)·256 + id` (0x0065631A–0x00656322). Seven instructions in `.text` name the table or its bounds, all in
    the loader, its unloader (0x006562B0) and `GetRecord`; the run's `GetRecord` model starts from the first row of the
    (version, Id), and it reproduces every logged call.
  - The loader writes `+0x114` and `+0x116` from the two `STRTABLE_GetByKey` calls (0x006561CF–0x00656201), and
    `HIRE_GetNameRange` reads them (0x0057601F, 0x0057602C). The 53 logged hire tables of the run hold the names
    `first + i` with `first` the string index of `NameFirst` (§ Plan 0038 batch S3a above).
  (fn:HIRELING_LoadTable@0x00655720, fn:HIRELING_GetRecord@0x006562F0, data:g_HirelingFirstById@0x0096BDD8,
  fn:HIRE_GetNameRange@0x00575FF0, fn:STRTABLE_GetByKey@0x00524D30, run:2026-10-16-hirelings)
  **Remainder, d-edit (as routed):** the three fatal branches (`0x816` first index 0, `0x817` last ≤ first, `0x818`
  `Id` > 255; jumps pinned at 0x0065621C, 0x00656226, 0x00656230). No stock row takes one: every first index is non-zero,
  every last is above its first, every `Id` is below 30.
- Not a claim of the spec, recorded for the reader: the writer indexes by `Version > 99`, the reader compares `Version`
  with exactly 100 or 0. On stock data (only 0 and 100) the two agree.

## Plan 0039 batch P1c (2026-10-17)

Row Q28 of [plan 0039](../../plans/done/0039-backlog-sweep-4.md). Static: Ghidra on the lane's copy and objdump. It adds a
re-read of the 72 `MSX` lines in the manifest-pinned logs of run:2026-10-16-hirelings (scratch script, not kept). No
game run.

### The leftover stats and skill

- [C] **Stats 67, 68, 69, 100 and 352 are `MonStatsInit`'s constant writes.** A mercenary is a type-1 unit: `MERC_Create`
  calls `SUnitCreate(type 1, …)`, and `SUnitCreate` → `MonsterInit` → `MonStatsInit` runs for it as for any monster
  ([monsters/0004 § 2](../monsters/0004-stats.md#2-monstatsinit-in-order)). Step B5 writes `SetStat(68, 100)`,
  `SetStat(67, 75)`, `SetStat(69, 100)`, `SetStat(352, 128)` and `SetStat(100, max(1, players))`, with the `push 0x4B`,
  `push 0x43` pair at 0x00573F14. `MERC_SetLevel` writes none of these five. All 72 logged `MERC_SetLevel` blocks
  (hires, loads and the kill session) hold exactly 67 = 75, 68 = 100, 69 = 100, 100 = 1 and 352 = 128; every session
  was single player. (fn:MERC_Create@0x005774F0, fn:sub_00574250_MonsterInit@0x00574250,
  fn:sub_00573CB0_MonStatsInit@0x00573CB0, fn:MERC_SetLevel@0x00572840, run:2026-10-16-hirelings)
- [C] **The Rogues' skill 336 comes from `MonStatsInit` step B10**, from the `roguehire` MonStats row (`Skill1`
  `RogueMissile`, `Sk1mode` `A1`, `Sk1lvl` 1). Its level is `Sk1lvl` + DifficultyLevels `MonsterSkillBonus` of the
  game's difficulty (0, 3, 7). The hireling level rule (`d` = 0 for a hireling) does not apply to this bonus. In the
  logs every Rogue block has skill 336 at level 1 in Normal (22 blocks), 4 in Nightmare (6) and 8 in Hell (2: the
  `Merc271h` and `Merc271hca` loads). The finding said "level 1" before. Act II's `act2hire` row has `Skill1` `Jab` the
  same way; the Act III and Act V hireling rows have no MonStats skill. (0x005740E0–0x00574135,
  fn:sub_0056DEB0_UnitSkillAdd@0x0056DEB0, tbl:MonStats.txt:Sk1lvl, tbl:DifficultyLevels.txt:MonsterSkillBonus,
  run:2026-10-16-hirelings)

### `Share`, `Head`, `Torso`, `Weapon`, `Shield`

- [I] **No reader.** The record array `g_pHirelingTxt` is read only by the loader, `HIRELING_FreeTable` and the five
  getters (Ghidra xrefs). The getters' 19 callers are the only code that holds a record. They are listed in § Functions,
  plus `D2S_WriteMercHeader`, `D2S_ReadMercHeader`, `sub_00533C70_ReadMercOldSave`, `sub_00533BF0_MercExpFromOldSave`,
  `PLAYER_GrantLevel` and `MERCAI_PickSkill`. None of them reads `+0x4C` (`Share`) or `+0x68`…`+0x74` (`Head`,
  `Torso`, `Weapon`, `Shield`), and none passes a record to another function.
  (data:g_pHirelingTxt@0x0096BDD0, fn:HIRELING_GetRecord@0x006562F0, tbl:Hireling.txt:Share, tbl:Hireling.txt:Head)
- [I] `HIRELING_RollEntry` copies `max(0, Share)` into the entry at `+0x28` (0x006639C0–0x006639D1), `Resist` at
  `+0x2C` and `HireDesc` at `+0x30`. The entry is a stack record of the caller. Of its four callers, `MERC_Init` reads
  `+0x00`, `+0x04` and `+0x18`, `HIRE_Hire` reads `+0x14` (the price), `sub_004B1090_ClientMercInit` reads `+0x00` and
  `+0x04`, and `sub_004B5C60_ClientHireListDraw` reads `+0x04`, `+0x08`, `+0x14`, `+0x1C` and `+0x30`. None reads
  `+0x28`, so `Share` has no effect in 1.14d. (fn:HIRELING_RollEntry@0x006637F0, fn:MERC_Init@0x00573270,
  fn:HIRE_Hire@0x005770E0)

### The description text

- [I] **It comes from a hard-coded string table, indexed by the `HireDesc` row.** The client list window takes the
  entry's `+0x30` (`[ebp−0x8C]` → `[ebp−0x40]`, 0x004B5ECC–0x004B5ED2) and calls `HIRELING_DescString(ECX = index)`
  (0x004B6262–0x004B6267). For an index 0..8 with a non-zero word, that function returns
  `STRTABLE_GetByIndex(g_HireDescStrIdx[index])`, and NULL otherwise. The window then appends the text to the row's
  line through a format string. `hiredesc.txt` and `.bin` are not used for this.
  (fn:HIRELING_DescString@0x00663720, data:g_HireDescStrIdx@0x006EE410, fn:sub_004B5C60_ClientHireListDraw@0x004B5C60)
- [C] **The table matches every HireDesc row by data.** The nine u16 are 0, 3371, 3372, 11090, 11088, 11089, 3377, 3376
  and 3375. With the English tables (`tools/tbl.py index … spx`) these read: none, "Fire Arrow", "Cold Arrow",
  "Combat", "Defensive", "Offensive", "Fire", "Cold", "Lightning". Those are the rows `None`, `farw`, `carw`, `comb`,
  `def`, `off`, `fire`, `cold` and `ltng` in order, so a Barbarian (row 0) gets no description.
  (data:g_HireDescStrIdx@0x006EE410, tbl:HireDesc.txt:Code)

## Plan 0038 batch H1b (run:2026-10-27-sweep-d2s-play)

Harness batch H1b of [plan 0038](../../plans/0038-inferred-claims-sweep.md) took one row of
[hirelings](../../specs/hirelings/README.md) ([inventory](../../plans/0038-inventory/hirelings-README.md), row 24); the
save rows are in [save/0001](../save/0001-d2s-io.md#plan-0038-batch-h1b-run2026-10-27-sweep-d2s-play). § F and the
summary above had the saved header as inferred ("no save written in the run"); both now point here.

- **hirelings 24** (§ F, the saved mercenary header) **raised.** [C] A mercenary hired in play is written to the
  header from its pet entry and its unit: in the hire session (Kashya, Rogue Encampment, one hire through
  `tools/d2pilot.py npc kashya hire --buy 1`) *Save and Exit* wrote seed 2 573 073 805, name 0, Hireling Id 1 and
  experience 52 424 400 (header `000000008dfd5d9900000100d0ee1f03`), each equal to the `MHW` lines' sources (mercenary
  info `+0x00`, the name id minus record `+0x114`, info `+0x08`, stat 13), and the reload recreated the mercenary from
  those bytes (`0x005726C0` called once). The tool-built (12345 / 3 / 0; 54321 / 20 / 7 dead) and killed-in-play
  (hell-r3, merc mode 12, dead bit set) cases separate the fields and the flag. (fn:D2S_WriteMercHeader@0x00568E60,
  fn:D2S_ReadMercHeader@0x0056AA50, fn:HIRE_Hire@0x005770E0, run:2026-10-27-sweep-d2s-play)

## Plan 0038 batch H1a (run:2026-10-27-sweep-d2s-load)

Harness batch H1a of [plan 0038](../../plans/0038-inferred-claims-sweep.md) took four rows of
[hirelings](../../specs/hirelings/README.md) ([inventory](../../plans/0038-inventory/hirelings-README.md), rows 3, 30,
32, 33); the save rows are in [save/0001](../save/0001-d2s-io.md#plan-0038-batch-h1a-run2026-10-27-sweep-d2s-load),
with the counts of `workspace/logs/h1a/check/sweep-h1a-check.txt`.

- **hirelings 32** (§ H, the mercenary items read after the header) **raised.** [C] `MercMF` (`mercmf.json`, a
  mercenary with three items: `lea`, `cap`, `sbw`), loaded in Normal: `D2S_ReadMercHeader` returned the mercenary
  (`MRX`), the mercenary list's reader was called with the cursor at the file's `jf` (`RSEC` `merc_items` = the end of
  the corpse list, 970), and the load's `RITEM` lines were the file's 4 + 3 items in order (`tools/d2sio.py`: code,
  seed, quality, version, mode of each); the write held the same mercenary list. (fn:D2S_ReadMercItems@0x0056AC10,
  fn:D2S_ReadSaveV92@0x0056B180, 0x0056B32D, run:2026-10-27-sweep-d2s-load)
- **hirelings 3, 30, 33** (saves older than version 92: `ReadMercOldSave`, the Id `0xFFFF` of a version-71 save,
  `MercExpFromOldSave`) **shortfall.** No save in the version 71 or 87 layout was built (no builder, no format doc;
  archivist entry [2026-10-27-reverser-archivist-h1a-d2s-legacy-layouts-and-parser-gaps](../../backlog/archive/2026-10-27-reverser-archivist-h1a-d2s-legacy-layouts-and-parser-gaps.md)).
  The one legacy load, a version-96 body labelled 91, was refused by `sub_00534020_ReadSaveLegacy` (14) before any
  mercenary step.

## Open questions

- Which MonStats-derived fields (velocity, mana, other stats that `MERC_SetLevel` does not set) survive from
  MonStatsInit's level-1 creation? Partly answered by run:2026-10-16-hirelings (observed, not read): after
  `MERC_SetLevel` the base list also holds stats 67 `velocitypercent`, 68 `attackrate`, 69 `other_animrate`, 100
  `monster_playercount` and 352 `last_sent_hp_pct`, and the Rogues carry skill 336 (`RogueMissile`), none of them
  from `hireling.txt`. Which MonStatsInit write sets each is not read. Answered in
  [§ Plan 0039 batch P1c](#plan-0039-batch-p1c-2026-10-17): step B5's constants and step B10's MonStats skill (level
  1 + `MonsterSkillBonus`).
- The client's mercenary init rolls the entry again from the seed and the player's level and draws skills with
  `d` clamped at 0 (`sub_004B1090_ClientMercInit`); whether the client ever shows those instead of the server's values
  is a display question for Phase 2.
- The input of `MERC_AddExp` (the share of the owner's experience) and its doubling were not read.
- The third byte of the `0x00731188` NPC table (`NpcRecord+0x26`) is not used by hire code.
- ~~Phase 1b contradictions to settle in Phase 2~~ Settled by run:2026-10-16-hirelings: the resistance divisor is 4
  (32 mercenary levels where ÷4 and ÷8 differ, every one as ÷4) and the list levels lie at player level −5 .. −1
  (530 entries, none above the player). The experience formula was settled by run:2026-10-12-mon-pool-p2 and
  `HireDesc` by data.
- The client's list window draws name index 1057 as 11021 (§ 4): not checked (the run compares the window's
  `RollEntry` calls, not its text).

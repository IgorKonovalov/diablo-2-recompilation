---
spec: monsters/pool
status: draft
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [rng, rng/seeds, data/excel]
consumed_by: [monsters/spawn, monsters/special, monsters/stats, objects]
tags: {C: 66, I: 31, L: 5}
updated: 2026-10-12
---

# Level monster pools ("monster regions") and the monster level

## Purpose

At game creation the server builds one **monster region** for every level id, all from one region seed
that comes from the game seed's first draw. A region holds the level's **monster pool**: up to 13 classes
picked from the level's `mon` (normal) or `nmon` (nightmare, hell) candidates, each with a rarity weight
and up to three appearance sets. It also copies the level's density and unique-count columns. The
spawn code later picks classes from it. This spec also gives the **monster level** rule that runs when
any server monster is created, and the client **critter** draw, which does not use the pool.
Primitives (`Step`, `Range`, `RangeB`, `Init`, `InitOne`) are those of [rng](../rng/README.md). The game
seed is defined in [rng/seeds](../rng/seeds.md) step 1.

## Entry points

| When | Function | Tag |
|---|---|---|
| Game created (single player): calls the region init after `GAME_InitSeeds` and the set-up calls listed below | fn:sub_00530BF0_GameCreate@0x00530BF0 | [C] |
| Game created, other path (same order after `GAME_InitSeeds`, three middle calls absent) | fn:sub_00530930_GameCreateA@0x00530930 | [I] |
| Region seed: one game-seed draw | fn:sub_00547D20_MonRegionsInit@0x00547D20 | [C] |
| All regions built, level ids 1 … n−1 | fn:sub_005479C0_MonRegionsBuild@0x005479C0 | [C] |
| One level's pool | fn:sub_005475E0_MonRegionPool@0x005475E0 | [C] |
| One entry's appearance sets | fn:sub_005BDB20_MonVariantRoll@0x005BDB20 | [C] |
| Server monster created: the monster level | fn:sub_00574250_MonsterInit@0x00574250 → fn:sub_00573CB0_MonStatsInit@0x00573CB0 | [I] |
| Client room's critters | fn:sub_0046C460_ClientCritters@0x0046C460 | [C] |

- [C] Every logged region build returns to `0x00530DCF` inside `sub_00530BF0_GameCreate`, and the call order
  there is `GAME_InitSeeds`, `0x00541470`, `0x0053F4B0`, `0x005379A0`, `0x00539A30`, `0x0052B5E0`,
  (`0x00539000` only if `game+0x6A` = 1), `0x0053FF90`, then `sub_00547D20_MonRegionsInit`.
  (fn:sub_00530BF0_GameCreate@0x00530BF0, fn:GAME_InitSeeds@0x0052C280, run:2026-10-12-mon-pool;
  [monsters/0001 §1](../../findings/monsters/0001-level-pool.md#1-where-and-when-game-creation))

## Inputs

### Tables

All tables are the compiled `.bin` records, indexed by **record position** ([data/excel](../data/excel.md)).
A monster class is a MonStats record position (the stored distinct-Id ordinal, used as a position).

| Anchor | Used for |
|---|---|
| tbl:Levels.txt:mon1 | `mon` slots, 25 × i16 at `+0x036`: normal candidates |
| tbl:Levels.txt:nmon1 | `nmon` slots, 25 × i16 at `+0x068`: nightmare and hell candidates |
| tbl:Levels.txt:umon1 | `umon` slots, 25 × i16 at `+0x09A`: counted at load only; read at spawn time (`monsters/special`) |
| tbl:Levels.txt:NumMon | u8 at `+0x032`: the pick bound |
| tbl:Levels.txt:rangedspawn | u8 at `+0x031`: first-pick ranged rule |
| tbl:Levels.txt:Act | u8 at `+0x003`: copied into the region |
| tbl:Levels.txt:MonDen | i32 × 3 at `+0x01C`: copied, `[difficulty]` |
| tbl:Levels.txt:MonUMin, tbl:Levels.txt:MonUMax | u8 × 3 at `+0x028`, `+0x02B`: copied, `[difficulty]` |
| tbl:Levels.txt:MonWndr | u8 at `+0x02E`: copied |
| tbl:Levels.txt:Quest | u8 at `+0x030`: copied |
| tbl:Levels.txt:MonLvl1, tbl:Levels.txt:MonLvl1Ex | i16 × 3 at `+0x010` / `+0x016`: region copy (classic / expansion); `MonLvl*Ex` is the monster level in expansion nightmare and hell |
| tbl:Levels.txt:cmon1, tbl:Levels.txt:cpct1, tbl:Levels.txt:camt1 | 4 × i16 each at `+0x0CC`, `+0x0D4`, `+0x0DC`: critters |
| tbl:MonStats.txt:isSpawn | `+0x00C` bit 0: a picked class is kept only if set |
| tbl:MonStats.txt:noRatio, tbl:MonStats.txt:boss | `+0x00C` bits 2 and 6: keep the MonStats level |
| tbl:MonStats.txt:rangedtype | `+0x00F` bit 4: the ranged rule's test |
| tbl:MonStats.txt:Rarity | u8 at `+0x02E`: the entry's weight |
| tbl:MonStats.txt:MonStatsEx | i16 at `+0x018`: the class's `monstats2` record |
| tbl:MonStats.txt:Level | i16 × 3 at `+0x0AA` (`Level`, `Level(N)`, `Level(H)`): the monster level |
| tbl:MonStats.txt:MinGrp, tbl:MonStats.txt:MaxGrp | u8 at `+0x02F`, `+0x030`: critter count |
| `monstats2.bin` `+0x015..+0x024`, `+0x025` | 16 u8 component counts, and the set-cap exponent (no table doc yet) |

- [C] The candidate counts are computed at load, not at build: `DRLG_LoadLevels` stores one count each for
  `mon`, `nmon` and `umon` as u8 at `+0x033`, `+0x034`, `+0x035`, bytes that have no `.txt` column, and the
  pool reads them there; the run reproduces every pool from these counts. (fn:DRLG_LoadLevels@0x0061C540,
  run:2026-10-12-mon-pool, [monsters/0001 §3](../../findings/monsters/0001-level-pool.md#3-the-pool-sub_005475e0_monregionpool))
- [I] The count is the number of **leading** non-negative slots (of 25), up to the first negative one, not the
  number of set slots. Stock data has no blank before a set slot, so the two agree and the run cannot tell them
  apart; the rule rests on the code read. (fn:DRLG_LoadLevels@0x0061C540)
- [I] `enabled` (MonStats) is not tested by the pool code. (fn:sub_005475E0_MonRegionPool@0x005475E0)
- [C] No pool cell names a class with `enabled` 0 in stock data (table survey).
  (tbl:MonStats.txt:enabled, [Levels § Survey](../../tables/Levels.md#survey-per-difficulty))

### Runtime state

| State | Type | Source |
|---|---|---|
| game seed | `Seed` at game `+0xD0` | [rng/seeds](../rng/seeds.md) step 1; under `-seed N` it is `Init(N)` |
| region seed `R` | `Seed`, a local of `MonRegionsInit` | step A |
| `game.monRegionSeedLow` | u32 at game `+0xEC` | step A |
| difficulty | u8 at game `+0x06D`, 0 normal, 1 nightmare, 2 hell | game creation |
| expansion | u32 at game `+0x070`, non-zero in an expansion game | game creation |
| `regions[id]` | pointer array at game `+0xF0`, one `MonRegion` per level id, `[0]` unused | step B |
| level count | i32 at `g_pDataTables+0xC5C` (137 stock) | data/excel |
| client room seed | `Seed` at active room `+0x6C` (client copy) | [rng/seeds](../rng/seeds.md) step 6 |

### Constants

| Name | Value | Anchor | Tag |
|---|---|---|---|
| `POOL_MAX` | 13 entries per region | fn:sub_005475E0_MonRegionPool@0x005475E0 | [C] |
| `SLOTS` | 25 slots per `mon`/`nmon`/`umon` array | fn:DRLG_LoadLevels@0x0061C540 | [C] |
| `RANGED_REDRAWS` | 20 | fn:sub_005475E0_MonRegionPool@0x005475E0 (`0x0054790D`) | [C] |
| `SETS_MAX` | 3 appearance sets per entry | fn:sub_005BDB20_MonVariantRoll@0x005BDB20 | [C] |
| `DUP_TRIES` | 3 | fn:sub_005BDB20_MonVariantRoll@0x005BDB20 | [C] |
| `MONSTATS_REC` | `0x1A8` bytes | fn:sub_005475E0_MonRegionPool@0x005475E0 | [C] |
| `REGION_SIZE` | `0x2E4` bytes | fn:sub_005479C0_MonRegionsBuild@0x005479C0, struct:MonRegion | [C] |
| hireling classes | 271, 338, 359, 560, 561 (`roguehire`, `act2hire`, `act3hire`, `act5hire1`, `act5hire2`) | fn:sub_0063EE90_HirelingType@0x0063EE90 | [I] |

## Algorithm

```mermaid
flowchart TD
    gis["GAME_InitSeeds<br/>game.seed (rng/seeds step 1)"] --> A["A. MonRegionsInit<br/>Step(game.seed), R = Init(low)"]
    A --> B["B. MonRegionsBuild<br/>level ids 1 .. n-1 in order"]
    B --> C["C. MonRegionPool<br/>picks from mon / nmon"]
    C --> D["D. MonVariantRoll<br/>per kept entry"]
    D -->|"next level id, same R"| B
    B --> regs["regions at game+0xF0"]
    regs -.->|"spawn time"| spawn["monsters/spawn, monsters/special"]
    mi["server monster created"] --> E["E. MonStatsInit<br/>monster level"]
    cr["client room"] --> F["F. ClientCritters<br/>room seed, not the pool"]
```

### A. The region seed (`sub_00547D20_MonRegionsInit`)

```
A1. InitOne(R)                                                   [C] (fn:sub_00547D20_MonRegionsInit@0x00547D20, run:2026-10-12-mon-pool)
A2. Step(game.seed)                                              ; game-seed draw (the first after GAME_InitSeeds)
A3. Init(R, game.seed.low)                                       ; R = {low, 666}
A4. game.monRegionSeedLow ← game.seed.low                        ; +0xEC
A5. BuildRegions(R, game.difficulty, game.expansion)             ; step B
```

- [C] Under `-seed N` the game seed is `Init(N)` with no earlier draw, so A2 is its **first** draw and every
  pool is a function of N and the difficulty only (the nightmare and hell side on the forced difficulty byte,
  step note C1). No map seed, act, level or DRLG room is involved; the act,
  level and room seeds of [rng/seeds](../rng/seeds.md) steps 3–6 come later and do not feed it. All ten games
  of the run sit at draw index 1 of `Init(N)`. (fn:sub_00547D20_MonRegionsInit@0x00547D20, run:2026-10-12-mon-pool)
- [I] The game-creation calls after this one also step the game seed: object regions `0x00546C60`, unit
  proxies `0x00536070`, quests `0x00545D80`, in that order. They are not specified here.
  (fn:sub_00530BF0_GameCreate@0x00530BF0, [monsters/0001 §1](../../findings/monsters/0001-level-pool.md#1-where-and-when-game-creation))
- [C] `R` is a local of `MonRegionsInit`; nothing else draws from it, and it is not kept after the build.
  Only the game seed's single draw is visible to the rest of the game. (fn:sub_00547D20_MonRegionsInit@0x00547D20, run:2026-10-12-mon-pool)

### B. The region build (`sub_005479C0_MonRegionsBuild`)

```
B1. Init(R, game.seed.low)                                       [C] (fn:sub_005479C0_MonRegionsBuild@0x005479C0, run:2026-10-12-mon-pool)
                                                                 ; the same value again: no effect on the result
B2. if DifficultyRecord(difficulty) = none: fatal error          [I] (fn:sub_00611D30_DifficultyRec@0x00611D30) ; never exercised
B3. d: u8 ← difficulty
    for id: i32 in 1 ..< levelCount:                             [C] (fn:sub_005479C0_MonRegionsBuild@0x005479C0, run:2026-10-12-mon-pool)
B4.   L ← Levels[id]                                             ; LEVELS_GetRecord, record position
      reg ← new MonRegion, 0x2E4 bytes, all zero
      reg.act      ← L.Act                                       ; u8
      reg.levelId  ← id
      reg.monDen   ← L.MonDen[d]                                 ; i32
      reg.monUMin  ← L.MonUMin[d];  reg.monUMax ← L.MonUMax[d]   ; u8
      reg.monWndr  ← L.MonWndr;     reg.quest   ← L.Quest        ; u8
      reg.nRooms   ← −1;            reg.unk2D4  ← −1             ; +0x00C, +0x2D4
      reg.monLvl   ← reg.monLvl2 ← (expansion ≠ 0 ? L.MonLvlEx[d] : L.MonLvl[d])   ; i16 sign-extended to i32
B5.   BuildPool(R, L, reg, nightmareOrHell: d ≠ 0)               ; step C
B6.   for i in 0 ..< reg.nPool:
        RollVariants(R, reg.entries[i], n: 3)                    ; step D
B7.   regions[id] ← reg
```

Step notes:

- B3. [C] Level 0 (*Null*) gets no region. Levels are processed in id order, and each level's pool **and**
  its appearance sets are complete before the next level's first draw, so one level's data changes every
  later level's pool. (fn:sub_005479C0_MonRegionsBuild@0x005479C0, run:2026-10-12-mon-pool)
- B4. [I] `monLvl`/`monLvl2` (`+0x2DC`/`+0x2E0`) are written and never read anywhere in the binary; the
  monster level comes from step E. The values are `[C]` as written for expansion games (the run logs them),
  but no classic game was logged. (struct:MonRegion+0x2DC, fn:sub_005479C0_MonRegionsBuild@0x005479C0)

### C. The pool pick (`sub_005475E0_MonRegionPool`)

```
C1. count: i32 ← nightmareOrHell ? L[+0x034] : L[+0x033]         [C] (fn:sub_005475E0_MonRegionPool@0x005475E0, run:2026-10-12-mon-pool)
    cand: i16[] ← first `count` slots of (nightmareOrHell ? L.nmon : L.mon)
C2. bound: i32 ← min(L.NumMon, 13, count)
C3. for p: i32 in 0 ..< bound:
C4.   if count < 1: stop                                         ; never true in stock data (bound ≤ count)
C5.   i: u32 ← Range(R, count)                                   ; draw, guarded Range (inlined, pow2 mask)
      c: i16 ← cand[i]
C6.   if p = 0 and L.rangedspawn ≠ 0:                            [C] (0x0054790D, run:2026-10-12-mon-pool)
        for t in 0 ..< 20:
          if Valid(c) and MonStats[c].rangedtype: break
          i ← Range(R, count);  c ← cand[i]                      ; draw (redraw, same count)
C7.   remove cand[i], shifting the later slots down;  count ← count − 1
C8.   if Valid(c) and MonStats[c].isSpawn:                       [C] (fn:sub_005475E0_MonRegionPool@0x005475E0, run:2026-10-12-mon-pool)
        e ← reg.entries[reg.nPool]
        e.classId ← c;  e.rarity ← MonStats[c].Rarity
        reg.raritySum ← (u8) (reg.raritySum + e.rarity)
        reg.nPool ← reg.nPool + 1;  reg.nEntries ← reg.nEntries + 1

    Valid(c) = 0 ≤ c < nMonStats;  MonStats[c] = g_pMonStats + 0x1A8 × c   [C] (data:g_pMonStats@0x0096C6A8, run:2026-10-12-mon-pool)
```

Step notes:

- C1. [C] The selector is `difficulty ≠ 0` and nothing else: normal reads `mon`, nightmare and hell read
  `nmon`. The expansion flag is not read here. The nightmare and hell pools of the run were built with the
  difficulty byte **forced**: the logger wrote it at `0x00547D63`, just before the build's only read of it at
  `0x00547D66`, in otherwise normal games (an ADR-0003 intervention, listed in the run record). Their `[C]`
  rests on that forced byte; a natural nightmare and hell game is still to be run (plan 0012).
  (fn:sub_005475E0_MonRegionPool@0x005475E0, tbl:Levels.txt:nmon1, run:2026-10-12-mon-pool)
- C1. [I] Classic games use the same column sets as expansion games: the pool code reads no game-type
  flag, but every logged game was an expansion game. (fn:sub_005475E0_MonRegionPool@0x005475E0)
- C5. [C] `count` is the **remaining** candidate count, so the draw ranges shrink by one per pick. A slot
  is never taken twice, but a class named in two slots can be taken twice; every run has 6–10 regions holding
  one class twice. (fn:sub_005475E0_MonRegionPool@0x005475E0, run:2026-10-12-mon-pool)
- C6. [C] The ranged rule applies to the **first pick only**. The test comes before each redraw, so a first
  draw that is already ranged makes no redraw, and after 20 redraws the last class drawn is taken whatever it
  is. All 20 `rangedspawn` levels are built with it in every run. Both ends are exercised: of the 200 ranged
  first picks of the run (20 levels × 10 games), 76 needed no redraw and 42 used all 20 redraws without
  finding a ranged class and kept the last one drawn; every one of those regions and its seed after is
  reproduced. (fn:sub_005475E0_MonRegionPool@0x005475E0,
  tbl:Levels.txt:rangedspawn, tbl:MonStats.txt:rangedtype, run:2026-10-12-mon-pool)
- C8. [C] A picked class with `isSpawn` 0 is dropped **after** it was picked: the pick still counts against
  `bound` and its slot is still removed. *Mountain Top* (three `ancientbarb*`, all `isSpawn` 0) therefore builds
  an empty pool, as do the ten levels with `NumMon` 0. (fn:sub_005475E0_MonRegionPool@0x005475E0,
  tbl:MonStats.txt:isSpawn, run:2026-10-12-mon-pool)
- C8. [C] There is no weighting at pick time: `Rarity` is only copied into the entry and summed, for the
  weighted pick at spawn time. (fn:sub_005475E0_MonRegionPool@0x005475E0, tbl:MonStats.txt:Rarity, run:2026-10-12-mon-pool)
- C8. [C] Class 723 (*Pandemonium 3*'s first slot) is MonStats record 723, the second `cr_lancer8`, not
  `overseer6`: every run puts class 723 in level 135's region, and runtime record 723 is byte-identical to
  `monstats.bin` record 723. The hell builds of level 135 carry the same forced difficulty byte as C1.
  (fn:sub_005475E0_MonRegionPool@0x005475E0, data:g_pMonStats@0x0096C6A8, run:2026-10-12-mon-pool)

### D. Appearance sets (`sub_005BDB20_MonVariantRoll`)

Each kept entry gets up to three **appearance sets**: one byte per `monstats2` component (16 of them,
`HD` … `S8` by data), each the index of one of that component's variants.

```
RollVariants(R, e, n: i32 = 3):                                  [C] (fn:sub_005BDB20_MonVariantRoll@0x005BDB20, run:2026-10-12-mon-pool)
D1. m2 ← MonStats2 record of e.classId (MonStats +0x018)         ; fn:sub_00451FE0_MonStats2Rec
    if m2 = none: return
D2. comp: u8[16] ← m2[+0x015 .. +0x024]
    cap: i32 ← (1 << (m2[+0x025] & 31)) − e.nVariants
    n ← min(n, cap)
    if e.nVariants + n > 3: n ← 3 − e.nVariants
    if n ≤ 0: return
D3. if e.nVariants = 0:
      for c in 0 ..< 16:                                         ; in component order
        set0[c] ← comp[c] < 2 ? 0 : Range(R, comp[c])            ; draw only where comp[c] ≥ 2
      e.sets[0] ← set0;  e.nVariants ← 1;  n ← n − 1
D4. if n = 0: return
D5. K ← [c for c in 0 ..< 16 if comp[c] > 1]  (in order);  k ← |K|
    if k = 0: return
    if k = 1: a ← b ← K[0]
    else:
      u ← Range(R, k);  a ← K[u];  K[u] ← K[k − 1]               ; draw
      b ← K[Range(R, k − 1)]                                     ; draw; b ≠ a
D6. repeat n times:
      tries: i32 ← 3
      loop:
        new ← copy of e.sets[0]
        new[a] ← Range(R, comp[a])                               ; draw
        if a ≠ b: new[b] ← Range(R, comp[b])                     ; draw
        dup ← false
        for each s in e.sets[0 ..< e.nVariants]:
          if s = new: tries ← tries − 1;  dup ← true
        if not dup or tries = 0: exit loop
      e.sets[e.nVariants] ← new;  e.nVariants ← e.nVariants + 1  ; appended even if still a duplicate
```

- [C] These draws sit between one level's pool picks and the next level's, on the same `R`, so a
  reimplementation must make them even if it never draws monsters, or every later pool is wrong.
  (fn:sub_005BDB20_MonVariantRoll@0x005BDB20, run:2026-10-12-mon-pool)
- [C] Every new set differs from set 0 in at most the two components `a` and `b`, chosen once per entry.
  (fn:sub_005BDB20_MonVariantRoll@0x005BDB20, run:2026-10-12-mon-pool)
- [I] Stock `+0x025` values are 0, `0x10` and `0x31`: with 0 the cap allows one set (set 0 only); with 16 or
  more it never binds. What the byte means is open. (fn:sub_005BDB20_MonVariantRoll@0x005BDB20)

### E. The monster level (`sub_00573CB0_MonStatsInit`)

Not part of the region build: it runs at every server monster creation, from the monster's class and the
level of the room it is created in. The whole step is inferred from the code: the run logged only town NPCs in normal
expansion games.

```
MonsterLevel(game, class, levelId) → i32:                        [I] (fn:sub_00573CB0_MonStatsInit@0x00573CB0, 0x00573DC1..0x00573E70)
E1. d: u32 ← min(game.difficulty, 2)
E2. if HirelingType(class) ≠ 0: d ← 0                            [I] (fn:sub_0063EE90_HirelingType@0x0063EE90)
E3. level: i32 ← MonStats[class].Level[d]                        ; i16 at +0x0AA + 2d, sign-extended
E4. if game.expansion ≠ 0 and d > 0                              [I] (0x00573E20, fn:sub_0061DCA0_LevelMonLvl@0x0061DCA0)
       and not MonStats[class].noRatio and not MonStats[class].boss:
      level ← Levels[levelId].MonLvlEx[d]                        ; i16, sign-extended; 1 if levelId has no record
E5. SetStat(unit, 12 /* level */, level)
```

- [I] So in an **expansion** game, nightmare and hell monsters take the area level `MonLvl2Ex`/`MonLvl3Ex`,
  except `noRatio` classes (player summons and pets) and `boss` classes, which keep MonStats `Level(N)`/`Level(H)`.
  Normal-difficulty monsters always take MonStats `Level`. In a **classic** game every difficulty uses MonStats
  `Level*`. The classic `Levels.MonLvl1..3` columns are never read for a monster level.
  (fn:sub_00573CB0_MonStatsInit@0x00573CB0, fn:sub_0061DCA0_LevelMonLvl@0x0061DCA0, tbl:MonStats.txt:Level, tbl:Levels.txt:MonLvl1Ex)
- [I] The five hireling classes take normal's `Level` in every difficulty and every game type, because E2
  sets `d` to 0 before both E3 and E4. (fn:sub_0063EE90_HirelingType@0x0063EE90, fn:sub_00573CB0_MonStatsInit@0x00573CB0)
- [I] Town NPCs created in an expansion nightmare or hell game get their town's `MonLvl*Ex`, which is blank
  (stored 0). (fn:sub_00573CB0_MonStatsInit@0x00573CB0, [Levels § Per-difficulty columns](../../tables/Levels.md#per-difficulty-columns-and-their-blanks))
- [I] The 47 logged creations (town NPCs, normal, expansion, acts 1–5) all take MonStats `Level` as E3 says.
  They cannot tell `Level` from the towns' `MonLvl1Ex` (both 0), and the E4 branch was not reached.
  (fn:sub_00573CB0_MonStatsInit@0x00573CB0, run:2026-10-12-mon-pool)
- [I] `MonLvl.txt` is not read for the level. It is read right after, at row `min(level, nMonLvl − 1)`, for
  hit points, defence, to-hit, damage and experience (`monsters/stats`).
  (fn:sub_006538A0_MonLvlStats@0x006538A0, tbl:MonLvl.txt:HP)
- [I] Champion, unique and minion level bonuses are applied after this by the special-monster code
  (`monsters/special`), not here. (fn:sub_00573CB0_MonStatsInit@0x00573CB0)

### F. Critters (`sub_0046C460_ClientCritters`): not from the pool

```
Critters(room, levelId):                                         [C] (fn:sub_0046C460_ClientCritters@0x0046C460, run:2026-10-12-mon-pool)
F1. S ← room.seed                                                ; client active room +0x6C
F2. for k in 0 ..< 4:
      cls: i16 ← Levels[levelId].cmon[k];  if cls < 0: stop
F3.   Step(S)                                                    ; draw, inlined, no guard
      if S.low mod 100 < (u32)(i32) Levels[levelId].cpct[k]:     ; unsigned compare
F4.     n: u32 ← RangeB(S, MaxGrp − MinGrp) + MinGrp             ; MonStats[cls] +0x030, +0x02F; guarded: no draw if equal
F5.     if camt[k] ≠ 0: n ← n × camt[k]
F6.     repeat n times: ClientCritterCreate(room, cls)           ; draws more from S (monsters/spawn)
```

- [C] Critters are a separate, client-side draw per client room, from the room seed; nothing here reads
  the region or its pool. The `[C]` covers F2–F5 from a given room seed and the fact that the pool is not
  used: the run takes each room's entry seed from the log (`CR0`), a boundary oracle on the room seed
  (ADR-0004), and checks every room to its first creation (or to its exit seed when it has no critter).
  (fn:sub_0046C460_ClientCritters@0x0046C460, tbl:Levels.txt:cmon1, tbl:Levels.txt:cpct1, run:2026-10-12-mon-pool)
- [C] F4 is `RangeB(MaxGrp − MinGrp) + MinGrp`, so `MaxGrp` itself is never reached when the two differ,
  and when they are equal no draw is made. The no-draw case is exercised: in all 12 rooms of the run where a
  slot passed the `cpct` test, the class (`chicken` 149, `bug` 268) has `MinGrp` = `MaxGrp`, and the room seed at
  the first creation matches with no draw for the count. The `MinGrp` < `MaxGrp` case was not reached. (fn:sub_0046C460_ClientCritters@0x0046C460, tbl:MonStats.txt:MaxGrp, run:2026-10-12-mon-pool)
- [I] The draws inside `sub_0046C1A0_ClientCritterCreate` (placement, the client unit seed) are not read, so
  the slots after the first slot that creates critters are not predicted. (fn:sub_0046C1A0_ClientCritterCreate@0x0046C1A0)
- [C] `camt` is 0 in every stock row and `cpct` is 2..100 on every named slot, so F5 never fires and the
  sign of `cpct` never matters in stock data. (tbl:Levels.txt:camt1, [Levels § Critters](../../tables/Levels.md#critters-cmon14-cpct14-camt14))

### Draw order on `R`

- [C] All draws on `R` happen in one pass at game creation, in this order: for each level id 1 … n−1, the
  pool picks C5 (with the C6 redraws on the first pick), then for each kept entry in pool order its D3, D5
  and D6 draws. Nothing else draws on `R`, and `R` is gone when the build returns. The only other seed the
  build touches is one draw of the game seed (A2). (fn:sub_005479C0_MonRegionsBuild@0x005479C0, run:2026-10-12-mon-pool)

## Outputs

`regions[id]` for `id` in 1 … n−1, a `MonRegion` of `0x2E4` bytes (`re/types/monregion.h`). Fields set by the
build, all little-endian:

| Offset | Field | Type | Value | Anchor | Tag |
|---|---|---|---|---|---|
| `+0x000` | `act` | u8 | `Levels.Act` | struct:MonRegion+0x000 | [C] |
| `+0x00C` | `nRooms` | i32 | −1 | struct:MonRegion+0x00C | [C] |
| `+0x010` | `nPool` | u8 | kept pool entries (0 … 13); spawn picks range over these | struct:MonRegion+0x010 | [C] |
| `+0x011` | `raritySum` | u8 | sum of the entries' `rarity`, mod 256 | struct:MonRegion+0x011 | [C] |
| `+0x012` | `nEntries` | u8 | = `nPool` after the build; spawn time may append | struct:MonRegion+0x012 | [C] |
| `+0x014 + 0x34·i` | `entries[i].classId` | i16 | MonStats record position | struct:MonRegionEntry+0x00 | [C] |
| `+0x016 + 0x34·i` | `entries[i].rarity` | u8 | `MonStats.Rarity` | struct:MonRegionEntry+0x02 | [C] |
| `+0x017 + 0x34·i` | `entries[i].nVariants` | u8 | 0 … 3 | struct:MonRegionEntry+0x03 | [C] |
| `+0x018 + 0x34·i` | `entries[i].variant[3][16]` | u8 | appearance sets | struct:MonRegionEntry+0x04 | [C] |
| `+0x2B8` | `monDen` | i32 | `Levels.MonDen[d]` | struct:MonRegion+0x2B8 | [C] |
| `+0x2BC`, `+0x2BD` | `monUMin`, `monUMax` | u8 | `Levels.MonUMin[d]`, `MonUMax[d]` | struct:MonRegion+0x2BC | [C] |
| `+0x2BE` | `monWndr` | u8 | `Levels.MonWndr` | struct:MonRegion+0x2BE | [C] |
| `+0x2C0` | `levelId` | i32 | `id` | struct:MonRegion+0x2C0 | [C] |
| `+0x2D4` | `unk2D4` | i32 | −1 | struct:MonRegion+0x2D4 | [C] |
| `+0x2D8` | `quest` | u8 | `Levels.Quest` | struct:MonRegion+0x2D8 | [C] |
| `+0x2DC`, `+0x2E0` | `monLvl`, `monLvl2` | i32 | B4; never read | struct:MonRegion+0x2DC | [I] |

Every other byte is 0. The `[C]` rows are the fields the run logs for every region and `tools/monpool.py`
reproduces (struct:MonRegion, struct:MonRegionEntry, run:2026-10-12-mon-pool); the last row is `[C]` as
written in expansion games and `[I]` as unread (step note B4).

### Consumers (named only)

- [I] Random population (`sub_0054EC90_RoomPopulate`) runs only when the region's `monDen` ≠ 0
  (`sub_0054EBC0_RoomPopulateGate`), so *Mountain Top* and normal-difficulty *Siege 1* get no random
  population whatever their pool. (fn:sub_0054EC90_RoomPopulate@0x0054EC90, fn:sub_0054EBC0_RoomPopulateGate@0x0054EBC0, tbl:Levels.txt:MonDen)
- [I] The spawn-time class pick `sub_005BDE80_MonRegionPickClass` draws `RangeB(roomSeed, raritySum) + 1`
  and walks the entries subtracting `rarity`, so a `Rarity` 0 entry is never picked; with `nPool` = 0 nothing
  spawns. For champions and uniques in **normal** difficulty it picks from `umon` instead (`umon[Range(count)]`,
  count at Levels `+0x035`); in nightmare and hell they come from the region pool. Specified in
  `monsters/spawn` and `monsters/special`. (fn:sub_005BDE80_MonRegionPickClass@0x005BDE80, tbl:Levels.txt:umon1)
- [I] `sub_00547BC0_MonRegionFindAdd` (from `sub_00574250_MonsterInit`) appends a class not yet in its level's
  region (while `nEntries` < 13 and a MonStats2 `+0x0EC` test > 2 holds), rolling its sets from the **unit**
  seed, not from `R`. (fn:sub_00547BC0_MonRegionFindAdd@0x00547BC0, fn:sub_00574250_MonsterInit@0x00574250)
- [I] The object-region code reads the pool too (`sub_005474C0_RegionActClass`). (fn:sub_005474C0_RegionActClass@0x005474C0)

## Worked example

Source: run:2026-10-12-mon-pool, log `monpool-1-normal.log` (`-seed 1`, normal, expansion; the one game of
the run whose difficulty byte was not rewritten). `tools/monpool.py` reproduces the pools and the seed after
each level:

```
python3 -I tools/monpool.py pool workspace/merged/data/global/excel --seed 1 --diff 0 --level 1 --level 2 --level 3
game seed Init(1) after 1 step(s): 6ac6935f:00000000; region seed = Init(6ac6935f)
level   1 act 0 mlvl   0 pool [] seed after 6ac6935f:0000029a
level   2 act 0 mlvl   1 pool [5(r2,3v) 19(r2,3v) 63(r2,1v)] seed after d52ffc3b:270b4ee5
level   3 act 0 mlvl   2 pool [28(r1,1v) 58(r2,1v) 165(r1,3v)] seed after 679fafd2:63e02d41
```

`check` compares the same values with every logged region (1557/1557 for the run). The individual draws
below come from stepping the same model; each can be re-derived with [rng](../rng/README.md) step 1. Seeds are
`low:high` in hex.

**A.** Game seed `Init(1)` = `00000001:0000029a`. A2: `1 × 0x6AC690C5 + 0x29A = 0x6AC6935F`, so the game seed
becomes `6ac6935f:00000000` (logged `MPS gseed`), and `R = Init(0x6AC6935F)` = `6ac6935f:0000029a`.

**Level 1** (*Act 1 - Town*): `NumMon` 0, so `bound` = 0. No draw; `R` stays `6ac6935f:0000029a` (logged).

**Level 2** (*Act 1 - Wilderness 1*): `mon` = [5 `zombie1`, 19 `fallen1`, 63 `quillrat1`], `NumMon` 3, so
`bound` = 3 and every candidate is taken; the draws still happen.

| draw | call | `R` after | result | taken |
|---|---|---|---|---|
| 1 | `Range(R, 3)` | `2f2edab5:2c890afd` | 0 | 5 `zombie1` (rarity 2) |
| 2 | `Range(R, 2)` | `f09b2846:13adff7a` | 0 | 19 `fallen1` (rarity 2) |
| 3 | `Range(R, 1)` | `a3df5d58:645adebe` | 0 | 63 `quillrat1` (rarity 2) |

Appearance sets, in entry order:
- `zombie1`: `comp` = [3,3,3,3,3,0,0,0,3,3,3,0,0,0,0,0], cap exponent 16. D3: eight draws (components 0–4,
  8–10) give set 0 = `00 00 00 00 00 00 00 00 01 01 02 00 00 00 00 00`. D5: `K` = [0,1,2,3,4,8,9,10],
  `Range(R, 8)` = 2 → `a` = 2, `K[2]` ← 10, `Range(R, 7)` = 3 → `b` = `K[3]` = 3. D6: set 1 draws (a, b) = (1, 1),
  set 2 draws (2, 2); no duplicate. 14 draws.
- `fallen1`: `comp` = [0,1,0,0,0,3,0,4,2,1,0,0,0,0,0,1], exponent 6. D3: components 5, 7, 8 give (0, 1, 0).
  D5: `K` = [5,7,8], `Range(R, 3)` = 1 → `a` = 7, `K[1]` ← 8, `Range(R, 2)` = 1 → `b` = 8. D6: set 1 (a, b) = (0, 0),
  set 2 = (2, 1). 9 draws.
- `quillrat1`: exponent 0, so the cap is one set; no component has a count ≥ 2, so set 0 is all zero with no
  draw.

Region 2: `nPool` 3, `raritySum` 6, `monDen` 520, `monUMin`/`monUMax` 0/0, `monWndr` 1, `monLvl` 1 (`MonLvl1Ex`),
`R` after = `d52ffc3b:270b4ee5` (26 draws; logged).

**Level 3** (*Act 1 - Wilderness 2*): `mon` = [28 `brute1`, 43 `corruptrogue1`, 58 `fallenshaman1`,
165 `cr_lancer1`], `NumMon` 3: four candidates for three picks, so the draws decide the pool.

| draw | call | `R` after | result | taken | remaining |
|---|---|---|---|---|---|
| 1 | `Range(R, 4)` | `b67b984c:58eb3a1c` | 0 | 28 `brute1` (rarity 1) | [43, 58, 165] |
| 2 | `Range(R, 3)` | `8e7a2c98:4c1cb7d9` | 1 | 58 `fallenshaman1` (rarity 2) | [43, 165] |
| 3 | `Range(R, 2)` | `16c688d1:3b6d1988` | 1 | 165 `cr_lancer1` (rarity 1) | [43] |

`corruptrogue1` is left out. Appearance sets: `brute1` and `fallenshaman1` have exponent 0 and no component
count ≥ 2: one all-zero set each, no draw. `cr_lancer1` (`comp` = [3,3,3,3,3,3,0,0,3,3,3,0,0,0,0,0], exponent 18):
- D3: nine draws give set 0 = `00 01 00 01 01 02 00 00 00 02 02 00 00 00 00 00`.
- D5: `K` = [0,1,2,3,4,5,8,9,10], `Range(R, 9)` = 3 → `a` = 3, `K[3]` ← 10, `Range(R, 8)` = 2 → `b` = 2.
- D6, set 1: (a, b) = (1, 1): differs from set 0 at component 2, appended.
- D6, set 2: (1, 0) equals set 0 (a duplicate, `tries` 3 → 2), redrawn: (1, 2), appended.
- 17 draws in all (9 + 2 + 2 + 2 + 2).

Region 3: `nPool` 3, `raritySum` 4, `monUMin`/`monUMax` 1/1, `monLvl` 2, `R` after = `679fafd2:63e02d41` (logged).

**Monster level** (step E, inferred; not logged for these classes, the model's prediction only). A
`cr_lancer1` (class 165, MonStats `Level`/`Level(N)`/`Level(H)` = 2/36/67) created in level 3 (`MonLvl1Ex..3Ex` =
2/36/68):

| difficulty | expansion game | classic game |
|---|---|---|
| normal | 2 (MonStats `Level`) | 2 |
| nightmare | 36 (`MonLvl2Ex`) | 36 (MonStats `Level(N)`) |
| hell | **68** (`MonLvl3Ex`) | **67** (MonStats `Level(H)`) |

`python3 -I tools/monpool.py mlvl workspace/merged/data/global/excel --cls 165 --level 3 --diff 2 --exp 1`
prints `monster level 68 (difficulty index 2)`, and `--exp 0` prints 67.

## Reimplementation notes

- **Every pool depends on every earlier level.** One `R` runs through all levels in id order, including
  their appearance-set draws. Leaving out a level that draws, or the appearance sets of any entry, shifts
  every later pool. [C] (fn:sub_005479C0_MonRegionsBuild@0x005479C0, run:2026-10-12-mon-pool)
- **The pool is per game, not per level visit.** It is fixed at game creation and depends on the game seed
  and the difficulty only; the map seed and the order in which levels are entered do not affect it. The
  nightmare and hell side rests on the forced difficulty byte (ADR-0003 intervention, step note C1) until the
  natural nightmare/hell run lands. [C] (fn:sub_00547D20_MonRegionsInit@0x00547D20, run:2026-10-12-mon-pool)
- **The game seed is shared.** The region init's single draw (A2) is one step in the game seed's sequence;
  the object regions, unit proxies, quests and every server unit created later step the same seed after it
  ([rng/seeds](../rng/seeds.md) step 7a). [I] (fn:sub_00530BF0_GameCreate@0x00530BF0)
- **A dropped class still costs a pick.** `isSpawn` is tested after the pick and the slot removal (C8).
  [C] (fn:sub_005475E0_MonRegionPool@0x005475E0, run:2026-10-12-mon-pool)
- **Positions, not names.** A pool cell is a MonStats record position. Resolving it by `Id` name lands on
  the first `cr_lancer8` for 723 instead of the second. [C] (data:g_pMonStats@0x0096C6A8, run:2026-10-12-mon-pool)
- **Candidate count stops at the first blank.** The count is the number of leading non-negative slots (out of
  25), not the number of set slots; the two agree in stock data only. [I] (fn:DRLG_LoadLevels@0x0061C540)
- **`raritySum` is a u8.** The field is one byte. [C] (struct:MonRegion+0x011, run:2026-10-12-mon-pool) It cannot
  overflow in stock data (13 × 2 at most); with large `Rarity` values it would wrap mod 256, which no run
  exercised. [I] (fn:sub_005475E0_MonRegionPool@0x005475E0)
- **Duplicate check in D6 tests `tries = 0`, not `≤ 0`.** When two existing sets both equal the new one, one
  try costs two, so `tries` can pass from 1 to −1 and the loop then runs until a non-duplicate is drawn.
  [I] (fn:sub_005BDB20_MonVariantRoll@0x005BDB20)
- **Critter count excludes `MaxGrp`.** `RangeB(MaxGrp − MinGrp) + MinGrp` (F4). [C] (fn:sub_0046C460_ClientCritters@0x0046C460, run:2026-10-12-mon-pool)
- **Monster level ignores `Levels.MonLvl1..3`.** The classic area-level columns are copied into the region
  (B4, never read) but no monster level uses them. [I] (fn:sub_00573CB0_MonStatsInit@0x00573CB0)

## Evidence

- [findings/monsters/0001-level-pool.md](../../findings/monsters/0001-level-pool.md): the whole algorithm
  (sections 1–4 pool and sets, 5 monster level, 6 consumers, 7 critters, 8 ordinal 723).
- [findings/monsters/experiments.md § run:2026-10-12-mon-pool](../../findings/monsters/experiments.md#run2026-10-12-mon-pool):
  ten games, 1360 regions, 47 monster levels, 130 critter rooms, 1557/1557; the forced difficulty byte and the
  room-seed oracle are listed there.
- `tools/monpool.py` (`pool`, `check`, `mlvl`): the model behind the confirmed tags and the worked example.
- Tables: [Levels](../../tables/Levels.md#monster-pool-columns-plan-0012-phase-0),
  [MonStats](../../tables/MonStats.md#pool-and-level-columns-plan-0012-phase-0), [MonLvl](../../tables/MonLvl.md).
- Types: `re/types/monregion.h` (`MonRegion`, `MonRegionEntry`), `re/types/game.h` (`Game`).
- Upstream: [rng](../rng/README.md), [rng/seeds](../rng/seeds.md), [data/excel](../data/excel.md#h-monster-references).

## Open questions

- [L] The nightmare and hell pools rest on a forced difficulty byte. A natural nightmare and a natural hell game,
  reproduced by `tools/monpool.py check`, is a required case of the rest of plan 0012 Phase 2.
- [L] The monster level (step E) has no logged case outside normal-difficulty town NPCs: the `MonLvlEx` branch,
  the `noRatio`/`boss` exceptions and the hireling rule wait on the same plan 0012 Phase 2 run (monster levels
  logged outside town in nightmare and hell).
- [L] Classic games: the pool's column set (C1), the region's `monLvl` copy (B4) and the classic monster level
  (E4 not taken) are code-read only; a classic game is a case of the same run.
- [L] The meaning of `monstats2` `+0x025` (set-cap exponent) and `+0x0EC`, and the component names of
  `+0x015..+0x024`, need a MonStats2 table doc (backlog reverser → archivist, 2026-10-12, item d).
- [L] The draws of `sub_0046C1A0_ClientCritterCreate` belong to `monsters/spawn`.

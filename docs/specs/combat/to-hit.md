---
spec: combat/to-hit
status: reviewed
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [rng, combat/overview, player/creation, monsters/stats]
consumed_by: [combat/overview, combat/damage, combat/delivery]
tags: {C: 39, I: 30, L: 5}
updated: 2026-10-21
---

# Combat: the hit test, chance to hit and the defence rolls

## Purpose

At the hit frame of a melee attack the server decides whether the attack connects: a range check, the chance to
hit with one draw on the **attacker's** seed, then the defender's block and avoidance rolls on the **defender's**
seed. The result is the packet's result word, which decides whether the damage build of a monster runs and whether
any damage is applied ([combat/damage](damage.md), [combat/delivery](delivery.md)). Missiles reuse the chance to hit
and the defence roll with their own flags. The event that contains this test, its seeds and its chaining are in
[combat/overview](README.md). Primitives (`Step`, `Range`) are those of [rng](../rng/README.md); `RangeB` in our
symbol names is the second compile of `Range` and behaves the same.

```mermaid
flowchart TD
  start["COMBAT_MeleeHitTest"] --> host{"hostile, player or monster units?"}
  host -->|no| none["result 0"]
  host -->|yes| run{"defender a player in mode 3 (run)?"}
  run -->|yes| auto["hit, no to-hit draw"]
  run -->|no| rng{"in melee range?"}
  auto --> rng2{"in melee range?"}
  rng -->|no| none
  rng2 -->|no| none
  rng -->|yes| th["COMBAT_ToHitRoll: 1 draw, attacker seed"]
  rng2 -->|yes| hit
  th -->|r below c| hit["hit bit 0x1"]
  th -->|miss| miss["result 0"]
  hit --> dr["COMBAT_DefenceRoll: defender seed"]
  dr --> blk{"blocked, evaded, dodged or avoided?"}
  blk -->|yes| clr["bit set, hit bit cleared"]
  blk -->|no| gh["get-hit bit 0x4 unless state 54"]
```

## Entry points

| When | Function | Tag |
|---|---|---|
| A player's normal attack or a skill's melee hit, a monster's plain attack, at the hit frame | fn:COMBAT_MeleeHitTest@0x0057EC10 | [I] (0x0057EC16–0x0057EC28) |
| The chance to hit and its draw | fn:COMBAT_ToHitRoll@0x0057D9B0 | [C] (run:2026-10-16-combat) |
| The defender's block, then evade, weapon block, dodge or avoid | fn:COMBAT_DefenceRoll@0x0057DFB0 → fn:COMBAT_AvoidRoll@0x0057DD60 | [C] for the block (run:2026-10-16-combat); [C] for evade, weapon block, dodge and avoid on a player defender (run:2026-10-20-shortfalls) |
| A missile reaching a unit (phase (3); the to-hit and defence calls only) | fn:MISSILE_HitUnit@0x005ADF10, fn:MISSILE_ApplyDamage@0x005AD730 | [I] |

## Inputs

### Tables

| Anchor | Used for |
|---|---|
| tbl:CharStats.txt:ToHitFactor | added to a player's attack rating (A2) |
| tbl:CharStats.txt:BlockFactor | added to a player's block (C2) |
| tbl:MonStats.txt:NoShldBlock | a monster may block without a shield (C2) |
| tbl:MonStats.txt:MonType | the stat-179 attack-rating bonus by monster type (A2) |
| tbl:Skills.txt:ToHit, `LevToHit`, `ToHitCalc` | a skill's attack-rating percent through `SKILLS_GetToHit` ([data/calc § G](../data/calc.md#g-variables)) |

### Runtime state

| State | Type | Source |
|---|---|---|
| attacker and defender units | `Unit`, type 0 player, 1 monster, 3 missile | the attack event ([combat/overview](README.md)) |
| attacker seed, defender seed | `Seed` at `Unit+0x20` | [rng/seeds](../rng/seeds.md) |
| `arPct` | i32, the caller's attack-rating percent | 0 for a monster, stat 325 for the player's normal attack, `SKILLS_GetToHit` for a skill |
| unit stats | i32 values of the unit's stat lists | value inputs (ADR-0014); see the stat ids below |
| unit mode | the unit's animation mode | 2 walk, 3 run, 6 (player); 2, 15 (monster) |
| game type | `Game+0x70`, 0 classic, else expansion | game creation |

Stat ids read here: 0 strength is not read; 2 dexterity, 12 level, 16 and 171 defence percents, 19 attack rating,
20 block, 31 defence, 32 and 33 defence against missiles and melee, 115, 116, 119, 123, 124, 179, 182, 325, 338
dodge, 339 avoid, 340 evade, 348 weapon block. [I] ([combat/0001 § 12b (e)](../../findings/combat/0001-formulas.md#12b-answers-to-the-archivists-phase-0-questions-backlog-2026-10-16-ae), tbl:ItemStatCost.txt:Stat)

### Constants

| Name | Value | Anchor | Tag |
|---|---|---|---|
| to-hit clamp | 5 .. 95 | 0x0057DB22–0x0057DB30 | [C] (run:2026-10-16-combat) |
| block cap | 75 | fn:sub_00622720_UnitBlockChance@0x00622720 | [C] (run:2026-10-16-combat) |
| moving-player block divisor | 3 | 0x0057E011–0x0057E01F | [C] (run:2026-10-16-combat: 48 events, all on a running player, mode 3) |
| attacker-monster range bonus | 2 | fn:COMBAT_MeleeHitTest@0x0057EC10 | [I] |

## Algorithm

### A. The chance to hit (`COMBAT_ToHitRoll`)

```mermaid
flowchart LR
  ar["AR: player base or monster stat 19"] --> pct["AR += MulDiv(AR, pct, 100)"]
  def["DEF: UNIT_GetDefense + stat 32 or 33"] --> sw["negative swaps"]
  pct --> sw
  sw --> c1["c = 100 AR / (AR + DEF)"]
  c1 --> c2["c = c alvl 2 / (alvl + dlvl)"]
  c2 --> cl["clamp 5..95"]
  cl --> r["r = Range(att.seed, 100)"]
  r --> h{"r below c?"}
```

```
A1. ToHitRoll(att, def, arPct: i32, isMissile: bool) → bool:          [C] (fn:COMBAT_ToHitRoll@0x0057D9B0, run:2026-10-16-combat, all of A1–A6)
      dlvl: i32 ← stat(def, 12);  alvl: i32 ← stat(att, 12)
      DEF: i32 ← Defense(def) + stat(def, isMissile ? 32 : 33)        ; § B
A2.   if att is a player:
        AR: i32 ← (stat(att, 2) − 7) × 5 + stat(att, 19) + CharStats[att.class].ToHitFactor
        TargetMods(att, def, AR, DEF)                                 ; § A7, [I] (fn:COMBAT_ToHitTargetMods@0x0057D8A0)
        pct: i32 ← (not isMissile and att holds a weapon) ? masteryToHit(att, weapon) : 0
        pct ← pct + stat(att, 119) + arPct
        if def is a monster and MonStats[def.class].MonType > 0:
          for each (type, v) in att's stat-179 entries: if def's MonType matches type: pct ← pct + v
      else:
        AR ← stat(att, 19) + arPct + 5 × stat(att, 2)
        pct ← stat(att, 119)
A3.   AR ← AR + MulDiv(AR, pct, 100)
A4.   if DEF < 0: AR ← AR − DEF;  DEF ← 0
      if AR < 0:  DEF ← DEF − AR;  AR ← 0
      if DEF < 0: DEF ← 0
A5.   c: i32 ← (AR + DEF ≠ 0) ? (100 × AR) ÷ (AR + DEF) : 100
      c ← (c × alvl × 2) ÷ (alvl + dlvl)
      c ← (c ≤ 5) ? 5 : ((c ≥ 95) ? 95 : c)
A6.   r: u32 ← Range(att.seed, 100)                                   ; draw#1 (attacker), inlined LCG, low mod 100
      if r < c: PreventHealHook(att, def); return true
      return false
```

Step notes:

- A1–A6. Every division is signed 32-bit and truncates toward zero. `MulDiv(a, b, c)` is the overflow-guarded multiply-divide of
  [monsters/stats § A](../monsters/stats.md#a-muldiv-and-monlvlstats). The percent `100·AR/(AR+DEF)` is truncated
  **before** the level factor, which is then one multiply and one divide. [C] (0x0057DB01–0x0057DB30,
  run:2026-10-16-combat: 7 669 rolls in 7 822 melee events)
- A2. **`ToHitFactor` is an attack-rating term**, added before the percent; the level term uses plain stat 12 on both
  sides and has no class constant. Logged for the Sorceress (−15, 1 889 attacks) and the Barbarian (+20, 85). This
  contradicts src:arreat-summit-character-basics, which calls the class constants a level bonus; keep the code's
  form. [C] (fn:sub_00622560_PlayerBaseToHit@0x00622560, struct:CharStatsRec+0x3C, run:2026-10-16-combat)
- A2. The player's percent `pct` (the weapon mastery's to-hit, stat 119, the caller's `arPct`, the stat-179 entries)
  was a logged value oracle in the run, so its composition is [I]; the formula from `pct` on is [C].
  (fn:SKILLS_GetMasteryBonus@0x00645830, run:2026-10-16-combat)
- A2. The monster's attack rating `stat 19 + arPct + 5·dex` with `pct` = stat 119 is [C]; a monster's stat 19 at
  that moment is the value `MonAttackStats` wrote at its mode change ([monsters/stats § H](../monsters/stats.md#h-to-hit-and-damage-at-attack-time-reference-only)).
  [C] (fn:COMBAT_ToHitRoll@0x0057D9B0, run:2026-10-16-combat)
- A6. The draw is the inlined LCG on `att.seed` with the unsigned `low mod 100`, the same value as `Range(att.seed,
  100)`. Before the test the binary passes `c` and `r` to an empty debug stub. [C] (0x0057DB35–0x0057DB79,
  fn:DEBUG_ToHitRollStub@0x005347B0, run:2026-10-16-combat)
- A6. On a hit, `PreventHealHook` runs inside `COMBAT_ToHitRoll`'s success branch, after the draw: for a player
  attacker with stat 117 ≠ 0 and a monster defender whose class is outside 704–709, it applies state 52 (`STATE_ApplyTimed`)
  for 120 000 frames with stat 31 = 0. [I] (fn:sub_0057D810_PreventHealHook@0x0057D810, 0x0057DB80, 0x0057D869–0x0057D891,
  [skills/0003 § 3](../../findings/skills/0003-handlers.md#3-the-stat-event-handlers)) **It draws nothing**, so the state
  is applied between the to-hit draw and the defence rolls: 271 state-52 lines of the attacker between the two, each
  with both seeds asserted after it and no step between, beside the code reading of the hook (no RNG call). [C]
  (fn:sub_0057D810_PreventHealHook@0x0057D810, run:2026-10-20-shortfalls)

**A7. Target modifiers (players only).**

```
A7. TargetMods(att, def, AR, DEF):                                    [I] (fn:COMBAT_ToHitTargetMods@0x0057D8A0, all of A7)
      if stat(att, 115) ≠ 0 and def is a monster, not boss, unique, superunique (type flags 0x0A) nor a hireling:
        DEF ← 0
      p: i32 ← stat(att, 116)
      if def is a player, a boss, a superunique or a hireling: p ← p ÷ 2       ; signed
      p ← clamp(p, 0, 100);  DEF ← DEF − MulDiv(DEF, p, 100)
      if def is a demon:  AR ← AR + stat(att, 123)
      if def is undead:   AR ← AR + stat(att, 124)
```

- A7. Stat 115 is "ignore target defence", 116 the fractional target-defence reduction, 123 and 124 the
  attack-rating bonuses against demons and undead. No run reached these stats. [I] (0x0057D8BA, 0x0057D914,
  fn:MONSTATS_IsDemon@0x0063E940, fn:MONSTATS_IsUndead@0x0063E990)

**A8. Other attack-rating computations.** Two other functions compute an attack rating; neither is on an attack
path. `sub_00583740_AttackRatingCalc` adds `ToHitFactor` a second time and is reached only from a stat-by-id percent
helper; the client's character screen uses plain `÷ 100` instead of `MulDiv`. A reimplementation uses A2–A3. [I]
(fn:sub_00583740_AttackRatingCalc@0x00583740, fn:sub_004E9040_ClientAttackRating@0x004E9040, 0x00583890)

### B. Defence (`UNIT_GetDefense`)

```
B1. Defense(u) → i32:                                                 [I] (fn:UNIT_GetDefense@0x006223F0, all of B1)
      d: i32 ← stat(u, 31) + stat(u, 2) ÷ 4                          ; signed ÷ 4
      p: i32 ← stat(u, 171) + stat(u, 16)  (+ the Holy Shield calc when state 101 is on)
      d ← d + (d × p) ÷ 100
      if stat(u, 182) ≠ 0: d ← d + MulDiv(d, stat(u, 182), 100)
```

- B1. The base term `stat 31 + dex ÷ 4` plus stat 33 reproduced the defence of the player defenders (every monster
  attack on the player) and of the monster defenders in the run. [C] (fn:UNIT_GetDefense@0x006223F0,
  run:2026-10-16-combat) The percent terms (stats 171, 16, 182, the Holy Shield bonus through `SKILLS_EvalCalc`) were
  zero for every logged unit and stay [I]. (fn:UNIT_GetDefense@0x006223F0)

### C. The hit test and the defence rolls

```mermaid
sequenceDiagram
  participant A as attacker seed
  participant D as defender seed
  Note over A,D: COMBAT_MeleeHitTest
  A->>A: to-hit Range(100), unless the defender is a running player
  Note over D: only after a hit
  D->>D: shield block Range(100) if b > 0
  D->>D: evade Range(100) if moving and stat 340 > 0
  D->>D: else weapon block Range(100) if wb > 0
  D->>D: then dodge (melee) or avoid (missile) Range(100) if > 0
```

```
C1. MeleeHitTest(att, def, arPct: i32, rangeExtra: i32) → result: u16:            [I] (fn:COMBAT_MeleeHitTest@0x0057EC10, all of C1)
      if att and def are not hostile, or either is not a player or a monster: return 0
      auto: bool ← def is a player and def.mode = 3                                ; running; [C] (run:2026-10-16-combat, 47)
      reach ← (att is a monster ? 2 : 0) + 1 − (rangeExtra ≠ 0 ? weaponRange(att) + rangeExtra : 0)
      if not InMeleeRange(att, def, reach): return 0
      res: u16 ← auto ? 0x1 : (ToHitRoll(att, def, arPct, false) ? 0x1 : 0)       ; § A
      if res & 0x1:
        d ← DefenceRoll(def, isMissile: false, useBlock: true)                    ; § C2
        if d & 0x02: res |= 0x0100        ; avoided
        if d & 0x04: res |= 0x0080        ; dodged
        if d & 0x10: res |= 0x8000        ; weapon block
        if d & 0x01: res |= 0x0010        ; blocked
        if d ≠ 0: res &= ~0x1
      if res & 0x10: res &= ~0x1
      if (res & 0x1) and not HasState(def, 54): res |= 0x4                         ; get-hit
      return res
```

- C1. **A running player is hit without a to-hit roll**, and no draw happens on the attacker's seed; the block and
  avoidance rolls still run. Reproduced with 0 mismatches in 47 melee events on a player in mode 3: every one that
  reached a defence line had no to-hit draw logged, and none had one. [C]
  (0x0057EC71–0x0057EC77, run:2026-10-16-combat)
- C1. The result bits are: `0x1` hit, `0x2` killed, `0x4` get-hit, `0x8` knockback, `0x10` blocked, `0x80` dodged,
  `0x100` avoided, `0x200` evaded (missiles), `0x2000` doubled by a critical or deadly strike, `0x8000` weapon block.
  [I] (fn:COMBAT_MeleeHitTest@0x0057EC10, fn:MISSILE_ApplyDamage@0x005AD730, struct:DamagePacket+0x04) The melee
  hit test turns an evade (defence result `0x08`) into "not hit" without a bit of its own; the missile caller sets
  `0x200`. [I]
  (fn:MISSILE_ApplyDamage@0x005AD730)
- C1. The range test is `sub_00622C40_InMeleeRange` with the reach above; state 54 is `uninterruptable`. [I]
  (fn:sub_00622C40_InMeleeRange@0x00622C40, fn:UNIT_HasState@0x00639DF0)

**C2. Shield block.**

```
C2. DefenceRoll(def, isMissile: bool, useBlock: bool) → u32:                     [C] (fn:COMBAT_DefenceRoll@0x0057DFB0, run:2026-10-16-combat, all of C2)
      if useBlock:
        b: i32 ← BlockChance(def, game.expansion)
        if def is a player and IsMoving(def) and def.mode ≠ 2: b ← b ÷ 3            ; moving, not walking; [C] mode 3 (run:2026-10-16-combat, 48), [I] the mode-2 exception (0x0057E00B–0x0057E01F, run:2026-10-20-shortfalls, 6)
        if b > 0:
          r ← Range(def.seed, 100)                                                ; draw (defender)
          if r < b: return 0x01                                                   ; blocked
      return AvoidRoll(def, isMissile)                                            ; § C3

    BlockChance(u, expansion) → i32:                                              [C] (fn:sub_00622720_UnitBlockChance@0x00622720, run:2026-10-16-combat)
      if u is a player:
        if neither hand holds a usable shield: return 0                         ; the shield test: [I] for "usable" (fn:sub_0063C8F0_InvItemQuery@0x0063C8F0)
        b: i32 ← stat(u, 20) + CharStats[u.class].BlockFactor
        if expansion: b ← ((stat(u, 2) − 15) × b) ÷ (2 × max(stat(u, 12), 1))
      else:
        b ← (MonStats[u.class].NoShldBlock or u holds a shield) ? stat(u, 20) : 0
      return min(b, 75)
```

- C2. The player's chance was checked against its formula in 2 523 expansion and 395 classic events, and 2 243 blocks
  occurred. The shield test was a value oracle (`UnitBlockChance`'s shield check). [C]
  (fn:sub_00622720_UnitBlockChance@0x00622720, run:2026-10-16-combat) **A player holding no shield has chance 0.** In plan 0044's
  two-client run, 66 melee events between two players who held no shield (the saves' items, read with
  `tools/d2s.py dump`, are three inventory items each, nothing equipped) logged chance 0 where the formula with
  the shield would give more. [C] (fn:sub_00622720_UnitBlockChance@0x00622720, run:2026-10-20-two-clients) The `÷ 3` for a **running** player (mode 3)
  reproduced with 0 mismatches in 48 events (47 melee, 1 missile), with the moving test a value oracle
  (`sub_00622D00_UnitIsMoving`). [C] (fn:sub_00622D00_UnitIsMoving@0x00622D00, 0x0057E011–0x0057E01F,
  run:2026-10-16-combat) The exception for a walking player (mode 2), who keeps the full chance, is read from the code;
  run:2026-10-20-shortfalls met it 6 times in 48 events on a walking player, each chance undivided, under the floor of
  about 30. The one extra session the plan allowed was spent, so the count is final and the exception stays [I].
  (0x0057E00B–0x0057E01F, fn:COMBAT_DefenceRoll@0x0057DFB0, run:2026-10-20-shortfalls)
- C2. **The shield test.** `UnitBlockChance`'s player branch calls `sub_0063C8F0_InvItemQuery`, which takes each hand's
  item, tests it with `0x0062A4E0` (two item flags, `0x100` and `0x4000`, clear) and `ITEMS_UnitIsType(item, 51)`, and
  gives 0 otherwise; the chance is then 0. So a shield the player cannot use blocks nothing: two layouts logged
  chance 0 in every player block line, *Steelclash* above the level-5 player's level (a development log) and
  *Kerke's Sanctuary* beside a two-handed weapon. Which flag each layout sets is not read. [I]
  (fn:sub_00622720_UnitBlockChance@0x00622720, 0x00622797, fn:sub_0063C8F0_InvItemQuery@0x0063C8F0, 0x0062A4E0,
  fn:ITEMS_UnitIsType@0x00629BB0, run:2026-10-20-shortfalls)
- C2. The checker sees no hand's item, so the shield test stays a value oracle, and run:2026-10-20-shortfalls names
  the logs whose player holds no usable shield (`--no-shield-log`). The flag only sets the predicted chance to 0: a
  logged chance above 0 still fails, and a block roll the game made would break the seed chain. Without it the run
  list gives 88 mismatches, all a player block chance of 0 against the formula: 70 on the claw Assassins, whose
  recipes hold no shield, and 18 on `CombatDR`, whose 0 is taken from the logs, so those 18 check nothing about the
  refusal above. [C] (run:2026-10-20-shortfalls, [combat/0001 § 16](../../findings/combat/0001-formulas.md#16-plan-0047-phase-2-the-shortfalls-run2026-10-20-shortfalls))
- C2. **The dexterity form applies only in an expansion game**; classic uses `stat 20 + BlockFactor`. The divisor is
  `2·level` with level 0 and 1 both counting as 1. [C] (fn:sub_00622720_UnitBlockChance@0x00622720, tbl:CharStats.txt:BlockFactor,
  run:2026-10-16-combat)
- C2. The `÷ 3` comes after the 75 cap, so a moving player blocks at most 25 %: the logged chance of a running
  player was `b ÷ 3` taken after the cap in 45 expansion events (75 → 25) and 3 classic events (53 → 17). [C]
  (0x0057E011–0x0057E01F, run:2026-10-16-combat) Which modes `0x00621190` counts as moving (2, 3 and 6 by the reading) is a value oracle;
  see *Open questions*. [I] (0x0057DFD5)
- C2. The draw is inlined on `def.seed`, `low mod 100`, and reported to `DEBUG_DefenceRollStub` before the test. [C]
  (fn:DEBUG_DefenceRollStub@0x005347C0, run:2026-10-16-combat)

**C3. Evade, weapon block, dodge, avoid.**

```
C3. AvoidRoll(def, isMissile: bool) → u32:                                       [C] for a player defender (fn:COMBAT_AvoidRoll@0x0057DD60, run:2026-10-20-shortfalls, all of C3 except as tagged)
      moving ← (def is a player and def.mode ∈ {2, 3}) or (def is a monster and def.mode ∈ {2, 15})   ; [I] for the monster modes (0x0057DD60)
      if moving:
        e: i32 ← stat(def, 340)
        if e > 0:
          r ← Range(def.seed, 100)                                                ; draw (defender)
          if r < e: return 0x08                                                   ; evaded
        return 0
      wb: i32 ← WeaponBlockChance(def)                                            ; stat 348 by the held weapon's item type
      if wb > 0 and CurrentSkillCheck(def) = 13:                                   ; [I] what 13 stands for (0x0057DDAB–0x0057DDB4)
        if Range(def.seed, 100) < wb: return 0x10                                 ; draw (defender); weapon block
      ch: i32 ← isMissile ? stat(def, 339) : stat(def, 338)                       ; avoid : dodge
      if ch > 0:
        if Range(def.seed, 100) < ch: return isMissile ? 0x02 : 0x04              ; draw (defender)
      return 0
```

- C3. Each draw happens only when its chance is above 0, so a defender without these stats draws nothing here. That
  held for every logged event (the defence rolls were asserted by the defender's exit seed). [C] (run:2026-10-16-combat)
- C3. **The four rolls reproduced on player defenders**, each a `Range(100)` on the defender's seed with success when
  `r < chance`: evade 46 rolls (31 successes), weapon block 50 (30), dodge 172 (109), avoid 103 (68), every roll's
  value and exit seed asserted. The weapon block chance was a value oracle. [C] (fn:COMBAT_AvoidRoll@0x0057DD60,
  fn:sub_0057DCA0_WeaponBlockChance@0x0057DCA0, run:2026-10-20-shortfalls)
- C3. **A moving player rolls only evade.** A player in mode 2 or 3 rolled evade (46 rolls: 42 in mode 3, 4 in mode 2)
  and never weapon block, dodge or avoid, while the same characters rolled dodge, avoid and weapon block in modes 1,
  7, 9, 13 and 16; evade was rolled in no other mode. [C] (fn:COMBAT_AvoidRoll@0x0057DD60, run:2026-10-20-shortfalls)
  A monster defender with these stats was not logged, so its moving modes (2, 15) are [I]. (0x0057DD60)
- C3. **The weapon-block skill check** `0x0064F380` gave 13 in every logged check of the two-claw `CombatAss`, which
  rolled weapon block 50 times, and 12 in the one check of the one-claw `CombatAssO`, which rolled none. So 13 goes
  with two claws in the hands; what the value stands for is not read. [I] (0x0057DDAB–0x0057DDB4,
  run:2026-10-20-shortfalls)

**C4. Missiles.** When the missile's record byte `+0x18B` is set, `MISSILE_HitUnit` calls `ToHitRoll(missile's
stat 19 as arPct, isMissile = true)`, which reads stat 32 and skips the weapon mastery; `MISSILE_ApplyDamage` calls
`DefenceRoll(def, isMissile = true, useBlock = (physical ≠ 0))`, so a missile without physical damage cannot be
blocked. The missile path itself belongs to phase (3). [I] (fn:MISSILE_HitUnit@0x005ADF10, fn:MISSILE_ApplyDamage@0x005AD730)
The defence draws of 1 957 missiles on the player or the mercenary reproduced. [C] (run:2026-10-16-combat)

## Outputs

- The result word of the hit test (C1), carried in the packet at `+0x04`: a hit with or without get-hit, or one of
  blocked, dodged, avoided, evaded, weapon block, or 0. [I] (struct:DamagePacket+0x04)
- The attacker's seed advanced by 0 or 1 draw, the defender's by 0 to 3 draws (block, then evade, or weapon block
  and dodge or avoid). [I] (fn:COMBAT_DefenceRoll@0x0057DFB0, fn:COMBAT_AvoidRoll@0x0057DD60) The draws on each seed
  that the two runs' characters allowed reproduced: the block, and each of evade, weapon block, dodge and avoid. [C]
  (run:2026-10-16-combat, run:2026-10-20-shortfalls)

## Worked example

**Monster attacks blocked by the player, one per difficulty** (run:2026-10-16-combat). The defenders are the
tool-built `CombatSolo` Sorceress (dexterity 420, level 85 or 86, stat 20 = 33, `BlockFactor` 20), the `CombatBar`
Barbarian (dexterity 420, level 86, `BlockFactor` 25) and the classic `CombatCls` Sorceress (level 85). Seeds are
`low:high` hex. [C] (run:2026-10-16-combat)

| | Normal | Nightmare | Hell | classic Hell |
|---|---|---|---|---|
| session, frame | `bar-n-plains` 1306 | `solo-nm-p8` 448 | `solo-h-p3` 421 | `cls-h-plains` 419 |
| attacker (MonStats) | `fallen1`, level 1 | `corruptrogue1`, level 39 | `corruptrogue1`, level 68 | `fallen1`, level 54 |
| defender | Barbarian, **running** (mode 3) | Sorceress, mode 1 | Sorceress, mode 1 | Sorceress, mode 1 |
| AR, DEF | — (no roll) | 1479, 923 | 4038, 923 | 1263, 507 |
| `100·AR/(AR+DEF)` → `c` | — | 61 → `61·39·2/125` = 38 | 81 → `81·68·2/153` = 72 | 71 → `71·54·2/139` = 55 |
| attacker seed in → out | `aa2e63ff:678278de` unchanged | `31afbfe2:46bd8511` → `5bb74dfb:14b94f7b`, r = 7 | `eeeb6c86:43643019` → `f73e1337:63a6cc21`, r = 3 | `381d8151:0792795e` → `5daa8cb3:1767be19`, r = 27 |
| block chance `b` | `405·58/172` = 136 → 75 → `÷ 3` = 25 | `405·53/172` = 124 → 75 | `405·53/170` = 126 → 75 | classic: `33 + 20` = 53 |
| defender seed in → out | `d651eafd:4f86aa3d` → `d26cceee:596427db`, r = 22 | `14225c5d:18b8278b` → `dd0b8b1c:0865d834`, r = 44 | `ddecc595:116686fc` → `8afc62a5:5c902c70`, r = 33 | `c78b7d83:4aadff39` → `a0f14508:533a88b3`, r = 8 |
| result | blocked (`0x10`) | blocked | blocked | blocked |

DEF is `818 + 420 ÷ 4` = 923 for the expansion Sorceress and `407 + 400 ÷ 4` = 507 for the classic one. A monster
attack that is blocked runs no damage build, so the attacker's seed ends where the to-hit roll left it. The Normal
case shows the running defender: no to-hit draw, and a third of the capped block. [C] (run:2026-10-16-combat)

## Reimplementation notes

- **`ToHitFactor` is not a level bonus.** Add it to the attack rating (A2); 1.14d has no class term in `2·alvl/(alvl
  + dlvl)`. [C] (fn:sub_00622560_PlayerBaseToHit@0x00622560, run:2026-10-16-combat)
- **Truncate the percent first.** `c = 100·AR/(AR+DEF)` is an integer before the level factor; computing
  `100·AR·2·alvl / ((AR+DEF)·(alvl+dlvl))` in one step gives different values. [C] (0x0057DB01–0x0057DB30,
  run:2026-10-16-combat)
- **The clamp uses `≤ 5` and `≥ 95`**, so a hit is never certain and never impossible for a rolled attack. [C]
  (0x0057DB22–0x0057DB30, run:2026-10-16-combat)
- **The block draw is on the defender's seed**, the to-hit draw on the attacker's: a reimplementation that keeps one
  combat RNG gets every later draw wrong. [C] (fn:COMBAT_DefenceRoll@0x0057DFB0, run:2026-10-16-combat)
- **No difficulty branch** exists in the chance to hit or in the block chance; only the classic/expansion block form
  differs. [I] (fn:COMBAT_ToHitRoll@0x0057D9B0, fn:COMBAT_DefenceRoll@0x0057DFB0)
- **Defence comes before the block.** A miss draws no block; a running defender skips the to-hit draw but still draws
  the block. [I] (fn:COMBAT_MeleeHitTest@0x0057EC10)

## Evidence

- [combat/0001](../../findings/combat/0001-formulas.md) §§ 3 (to-hit, defence, target modifiers, 3.4 `ToHitFactor`),
  4 (hit test and defence rolls), 13 (*Leads used*: the `ToHitFactor` contradiction, the block formula held with
  refinement), 14 (the debug stubs), 15 (the confirmed raises), 16 (the shortfalls run: the four avoidance rolls,
  prevent-heal's no draw, the walking block, the shield test, `--no-shield-log`).
- [combat/experiments § run:2026-10-16-combat](../../findings/combat/experiments.md#run2026-10-16-combat): 7 669
  to-hit rolls, 2 243 blocks, the block formula in 2 523 expansion and 395 classic events.
- [combat/experiments § run:2026-10-20-shortfalls](../../findings/combat/experiments.md#run2026-10-20-shortfalls)
  (plan 0047 Phase 2, 31 logs, 18 737 events, 0 mismatches) and its review in the
  [plan 0047 log](../../plans/done/0047-simulation-shortfalls.md#implementation-log): the defence rolls by mode, the
  weapon-block skill values, the mode-2 events, the run without `--no-shield-log`.
- Tables: [CharStats](../../tables/CharStats.md), [MonStats](../../tables/MonStats.md),
  [ItemStatCost](../../tables/ItemStatCost.md), [Skills](../../tables/Skills.md).
- Upstream: [rng](../rng/README.md), [player/creation](../player/creation.md) (the class's base attributes),
  [monsters/stats § H](../monsters/stats.md#h-to-hit-and-damage-at-attack-time-reference-only) (a monster's stat 19 at
  attack time), [data/calc § G](../data/calc.md#g-variables) (`SKILLS_GetToHit`).

## Open questions

- ~~Evade, weapon block, dodge and avoid (C3): 0 events in run:2026-10-16-combat.~~ Reproduced on player defenders
  by run:2026-10-20-shortfalls (C3).
- [L] What the skill check `0x0064F380` returns: 13 with two claws, 12 with one (C3); the function is unread
  ([combat/0001 *Open questions*](../../findings/combat/0001-formulas.md#open-questions)).
- [L] Which item flag a shield the player cannot use sets for the shield test of C2 (`0x0062A4E0`).
- [L] The avoidance rolls of a monster defender (C3's monster modes): no logged monster had the stats.
- [L] Whether `0x00621190` (the "moving" test of C2) returns the player's mode or a separate state; the run took it
  as a value oracle.
- [L] The target modifiers of A7 and the defence percents of B1: no logged unit carried them.

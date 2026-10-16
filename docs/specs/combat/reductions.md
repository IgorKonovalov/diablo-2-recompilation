---
spec: combat/reductions
status: draft
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [combat/overview, combat/damage, monsters/stats]
consumed_by: [combat/delivery]
tags: {C: 35, I: 24, L: 5}
updated: 2026-10-16
---

# Combat: the defender's reductions

## Purpose

Between the damage build and the life change, the defender's side reduces each field of the packet: the
player-against-player and hireling percent, the absorb-damage stat events, the cold, freeze, poison and burn length
immunities, then per field the flat damage reduction (physical) or magic damage reduction (elements), the resistance
with its difficulty penalty, cap, pierce and immunity, the percent absorb and the flat absorb. The pass makes no
draw. Melee attacks run it inside the queue, before delivery; missiles run it at delivery
([combat/delivery](delivery.md)). The order is fixed by one 12-row table in the binary.

```mermaid
flowchart LR
  P["percent P"] --> E11["event 11 absorbdamage"] --> LI["length immunities"] --> R["per row: flat DR or MDR"] --> S["resistance %"] --> A1["absorb % ≤ 40"] --> A2["flat absorb"] --> T["total"]
```

## Entry points

| When | Function | Tag |
|---|---|---|
| A melee hit is queued (`doReductions` = 0 at delivery) | fn:COMBAT_ResolveAndQueue@0x0057DBF0 → fn:COMBAT_ApplyReductions@0x0057C1E0 | [C] (run:2026-10-16-combat) |
| A missile is delivered (`doReductions` = 1) | fn:COMBAT_ApplyDamage@0x0057C6C0 → fn:COMBAT_ApplyReductions@0x0057C1E0 | [C] (run:2026-10-16-combat) |
| One table row | fn:COMBAT_ReduceRow@0x0057BF80, fn:COMBAT_ResistFor@0x0057BE00, fn:COMBAT_Absorb@0x0057BF10 | [C] (run:2026-10-16-combat) |
| The percent P | fn:COMBAT_DamagePercent@0x0057C060 | [C] for 100 and the hireling-boss percent in Normal and Nightmare (run:2026-10-16-combat) |

## Inputs

### Tables

| Anchor | Used for |
|---|---|
| tbl:DifficultyLevels.txt:ResistPenalty | the expansion resistance penalty of players and hirelings (B2) |
| tbl:DifficultyLevels.txt:HireableBossDamagePercent | P when a hireling hits a boss (A2) |
| tbl:MonStats.txt:boss, `primeevil`, `lUndead`, `hUndead`, `demon` | P, the bypass flags, sanctuary |
| `g_DamageResistTable` (in the binary, not a `.txt`) | the rows of § B |

### Runtime state

| State | Type | Source |
|---|---|---|
| packet | `DamagePacket` after the build (or a skill's or missile's packet) | [combat/damage](damage.md) |
| difficulty record | `DifficultyLevels` record of the game's difficulty, kept in the context | `sub_00611D30_DifficultyRec` |
| game type | `Game+0x70`: 0 classic | game creation |
| `attIsMon`, `defIsMon` | bool: a monster that is not a hireling | `sub_0063EE90_HirelingType` |
| defender and attacker stats | i32 | value inputs (ADR-0014) |

Stat ids read: 34, 35 (DR, MDR), 36–46 (resistances and maxima), 110 (poison length reduction), 118 and 153 (half
freeze, cannot be frozen), 142–149 (absorb percent and flat), 327 (a missile's DR frame rate), 333–336 (pierce).
[I] (tbl:ItemStatCost.txt:Stat, [combat/0001 § 12b (e)](../../findings/combat/0001-formulas.md#12b-answers-to-the-archivists-phase-0-questions-backlog-2026-10-16-ae))

### Constants

| Name | Value | Anchor | Tag |
|---|---|---|---|
| player and hireling resistance cap | `min(75 + max-resist stat, 95)`; physical 50; rows without a max stat 75 | fn:COMBAT_ResistFor@0x0057BE00 | [C] (run:2026-10-16-combat) |
| resistance floor | −100 (below −99) | fn:COMBAT_ResistFor@0x0057BE00 | [I] |
| classic penalty | −20 Nightmare, −50 Hell | fn:COMBAT_ResistFor@0x0057BE00 | [C] (run:2026-10-16-combat) |
| absorb percent cap | 40 | 0x0057BF2A–0x0057BF6F | [C] (run:2026-10-16-combat) |
| PvP percent; hireling against hireling | 17; 25 | 0x0057C0B6, 0x0057C0D4 | [I] |
| prime evil against a bit-31 unit | 200 (hireling defender) or 400 | 0x0057C129–0x0057C132 | [I] |

## Algorithm

### A. `COMBAT_ApplyReductions`

```
A1. ApplyReductions(att, def, pkt):                                   [C] (fn:COMBAT_ApplyReductions@0x0057C1E0, run:2026-10-16-combat, all of A1)
      ctx.diff ← DifficultyRec(game.difficulty)
      ctx.attIsMon ← att is a monster and not a hireling;  ctx.defIsMon ← def is a monster and not a hireling
      DR: i32  ← stat(def, 34) << 8
      if DR > 0 and pkt.frameRate > 0:  DR  ← MulDiv(DR,  pkt.frameRate, 1024)
      MDR: i32 ← stat(def, 35) << 8
      if MDR > 0 and pkt.frameRate > 0: MDR ← MulDiv(MDR, pkt.frameRate, 1024)
      ctx.reduce ← [0, DR, MDR]
      P: i32 ← DamagePercent(ctx)                                     ; § A2
      if P ≠ 100:
        for row in Rows: if row.scaled and pkt[row.field] > 0: pkt[row.field] ← MulDiv(pkt[row.field], P, 100)
      DispatchEvent(11 absorbdamage, unit: def, other: att, pkt)       ; [I] (fn:UNIT_DispatchEvent@0x005C0C30): handlers not read
      LengthImmunities(ctx)                                           ; § A3
      bypass: bool ← def is a monster ? ((undead and pkt.flags & 0x100) or (demon and pkt.flags & 0x200)
                                          or (not undead and not demon and pkt.flags & 0x400))
                                      : (pkt.flags & 0x400) ≠ 0
      for row in Rows (in table order, § B):
        if row.monsterOnly and not ctx.attIsMon: break
        ReduceRow(ctx, row, bypass)                                   ; § B1
      pkt.total ← pkt.phys + pkt.fire + pkt.light + pkt.magic + pkt.cold + pkt.poison
                  + (ctx.attIsMon ? pkt.lifeSteal : 0)
```

- A1. `frameRate` is packet `+0x54`, which the missile path sets from the missile's stat 327. [I]
  (fn:MISSILE_ApplyDamage@0x005AD730) A melee packet has 0 there and takes DR and MDR whole. [C] (run:2026-10-16-combat)
- A1. Event 11's handlers (energy shield, bone and cyclone armour by the community's account) were not read; no
  logged unit had one. [I] (fn:UNIT_DispatchEvent@0x005C0C30)
- A1. The bypass flags are the attacker's "ignore resistances against undead / demons / beasts" bits that the build
  sets from stats 103, 104 and 106. [C] (fn:COMBAT_ApplyReductions@0x0057C1E0, run:2026-10-16-combat)
- A1. `total` includes the life drain only for a monster attacker: a monster's drain field is damage, a player's is a
  percent. [C] (fn:COMBAT_ApplyReductions@0x0057C1E0, run:2026-10-16-combat)

**A2. The percent P (`COMBAT_DamagePercent`).**

```mermaid
flowchart TD
  s{"same unit or none?"} -->|yes| p100["100"]
  s -->|no| dp{"defender a player?"}
  dp -->|yes| pv{"attacker a player, a hireling or bit 31?"}
  pv -->|yes| p17["17"]
  pv -->|no| p100
  dp -->|no| hh{"both hirelings?"}
  hh -->|yes| p25["25"]
  hh -->|no| hb{"attacker a hireling, defender a boss?"}
  hb -->|yes| phb["HireableBossDamagePercent"]
  hb -->|no| pe{"attacker a prime evil, defender bit 31?"}
  pe -->|yes| p400["200 if a hireling, else 400"]
  pe -->|no| p100
```

```
A2. DamagePercent(ctx) → i32:                                         [I] (fn:COMBAT_DamagePercent@0x0057C060, all of A2)
      if att = def or either is missing: return 100
      if def is a player:
        return (att is a player or a hireling or (att.flagsC4 & 0x80000000)) ? 17 : 100
      if att and def are both hirelings: return 25
      if att is a hireling and def is a boss: return ctx.diff.HireableBossDamagePercent
      if att is a prime evil and (def.flagsC4 & 0x80000000): return def is a hireling ? 200 : 400
      return 100
```

- A2. **P = 100** for every player and monster attack the run logged, and **`HireableBossDamagePercent`** for the
  mercenary hitting Andariel: 50 in Normal (2 events) and 35 in Nightmare (78), one read indexed by the difficulty.
  [C] (0x0057C0FE, tbl:DifficultyLevels.txt:HireableBossDamagePercent, run:2026-10-16-combat) Hell's 25 was not
  reached; it is the same read, and it is what tells this column from `MonsterCEDamagePercent` (20 in Hell). [I]
  (0x0057C0FE)
- A2. The prime-evil 200 occurred once (Andariel against the mercenary), under the floor. The 17 % of player against
  player and the 25 % of hireling against hireling were not reached. [I] (0x0057C129–0x0057C132, 0x0057C0B6,
  0x0057C0D4, run:2026-10-16-combat) `Unit+0xC4` bit 31's meaning is not named by the finding. [I] (0x0057C0B6)
- A2. "Boss" is MonStats `boss` (`+0x0C` bit 6), not a unique or superunique. [I] (fn:MONSTATS_IsBoss@0x0063E9F0)

**A3. Length immunities (`COMBAT_LengthImmunities`).**

```
A3. LengthImmunities(ctx):                                            [I] (fn:COMBAT_LengthImmunities@0x0057C140, all of A3)
      if pkt.coldLen > 0 or pkt.freezeLen > 0:
        if stat(def, 153) ≠ 0: pkt.coldLen ← 0; pkt.freezeLen ← 0        ; cannot be frozen
        else if stat(def, 118) ≠ 0: pkt.coldLen ← pkt.coldLen ÷ 2; pkt.freezeLen ← pkt.freezeLen ÷ 2   ; half freeze duration
      if HasState(def, 133): pkt.poisonLen ← 0
      if HasState(def, 131): pkt.burnLen ← 0
```

- A3. Stat 153 zeroing the cold length reproduced (the `CombatSolo` characters carry it). [C]
  (fn:COMBAT_LengthImmunities@0x0057C140, run:2026-10-16-combat) The stat-118 halving and states 131 and 133 were not
  met. [I] (fn:COMBAT_LengthImmunities@0x0057C140)

### B. The rows (`g_DamageResistTable`)

| Row | Field | Resist stat | Max stat | Pierce stat | Absorb % / flat | Reduce by | Scaled by P |
|---|---|---|---|---|---|---|---|
| 0 Dam | `phys` `+0x08` | 36 | — | — | — | DR | yes |
| 1 Fire | `fire` `+0x10` | 39 | 40 | 333 | 142 / 143 | MDR | yes |
| 2 Ligt | `light` `+0x1C` | 41 | 42 | 334 | 144 / 145 | MDR | yes |
| 3 Cold | `cold` `+0x24` | 43 | 44 | 335 | 148 / 149 | MDR | yes |
| 4 Magc | `magic` `+0x20` | 37 | 38 | — | 146 / 147 | MDR | yes |
| 5 CLen | `coldLen` `+0x30` | 43 | 44 | 335 | — | — | no |
| 6 FLen | `freezeLen` `+0x34` | 43 | 44 | 335 | — | — | no |
| 7 PLen | `poisonLen` `+0x2C` | 110 | — | 336 | — | — | no |
| 8 Pois | `poison` `+0x28` | 45 | 46 | 336 | — | — | yes |
| 9–11 Life, Mana, Stam | `+0x38`, `+0x3C`, `+0x40` (monster attackers only) | — | — | — | — | — | yes |

[C] The table is 12 rows of 11 dwords at `0x00732980` (field offset, resist, max, pierce, absorb percent, absorb
flat, reduce slot, monster-only, scaled, debug name), read from the pinned image by the checker and reproduced row by
row. (data:g_DamageResistTable@0x00732980, struct:ResistRow+0x1C, run:2026-10-16-combat) The lengths of cold and
freeze are reduced by **cold** resistance, and the poison length by stat 110, not by poison resistance. [C]
(data:g_DamageResistTable@0x00732980, run:2026-10-16-combat)

```
B1. ReduceRow(ctx, row, bypass: bool):                                [C] (fn:COMBAT_ReduceRow@0x0057BF80, run:2026-10-16-combat, all of B1)
      v: i32 ← pkt[row.field]
      if v ≤ 0: pkt[row.field] ← 0; return
      r: i32 ← ResistFor(ctx, row)                                    ; § B2
      if bypass: d: i32 ← v;  if r > 0: r ← 0
      else:      d ← v − ctx.reduce[row.slot]
      if d > 0 and r ≠ 0:
        r ← min(r, 100)
        d ← MulDiv(d, 100 − r, 100)
      if not bypass: d ← Absorb(ctx, row, d)                          ; § B3
      pkt[row.field] ← d                                              ; may be negative
```

- B1. **A field can end negative.** When DR or MDR exceeds the field, `d` is negative; the resistance is skipped
  (`d > 0` fails) and the negative value is stored and summed into `total`. [C] (0x0057BFB4–0x0057C04D,
  run:2026-10-16-combat) What the life change does with a negative total is in [combat/delivery § B](delivery.md#b-delivery-combat_applydamage).
- B1. A negative resistance raises the field: `100 − r` exceeds 100. [C] (fn:COMBAT_ReduceRow@0x0057BF80,
  run:2026-10-16-combat)
- B1. Monster immunity is `r ≥ 100`, capped here to 100, so the field becomes 0 (fire 268, cold 158, lightning 72,
  poison 73 immune applications). [C] (fn:COMBAT_ReduceRow@0x0057BF80, run:2026-10-16-combat) Magic immunity was not
  met. [I] (fn:COMBAT_ReduceRow@0x0057BF80)

**B2. The effective resistance (`COMBAT_ResistFor`).**

```
B2. ResistFor(ctx, row) → i32:                                        [C] (fn:COMBAT_ResistFor@0x0057BE00, run:2026-10-16-combat, all of B2)
      r: i32 ← row.resStat ≥ 0 ? stat(def, row.resStat) : 0
      if row.pierceStat ≥ 0 and (r < 100 or not ctx.defIsMon):       ; [I] for pierce (fn:COMBAT_ResistFor@0x0057BE00)
        r ← r − stat(att, row.pierceStat)
      if not ctx.defIsMon and row.resStat ∉ {36, 37}:                 ; players and hirelings; not physical, not magic
        if game is classic:
          if difficulty = Nightmare: r ← r − 20
          if difficulty = Hell:      r ← r − 50
        else:
          r ← r + ctx.diff.ResistPenalty                              ; 0, −40, −100
      if r < −99: r ← −100
      if r ≥ 1 and not ctx.defIsMon:
        cap: i32 ← row.maxStat ≥ 0 ? min(75 + stat(def, row.maxStat), 95) : (row is 0 ? 50 : 75)
        r ← min(r, cap)
      if row is 0 and HasState(att, 47) and def is undead: r ← 0      ; sanctuary, [I] (fn:COMBAT_ResistFor@0x0057BE00)
      return r
```

- B2. The penalty and the cap apply to **players and hirelings**; a monster's resistance is neither penalised nor
  capped. The classic penalty (−20 / −50) was logged on the player 138 and 208 times, the expansion `ResistPenalty`
  throughout. [C] (fn:COMBAT_ResistFor@0x0057BE00, tbl:DifficultyLevels.txt:ResistPenalty, run:2026-10-16-combat)
- B2. Physical (stat 36) and magic (stat 37) resistances take no difficulty penalty. [C] (fn:COMBAT_ResistFor@0x0057BE00,
  run:2026-10-16-combat)
- B2. The cap is one code path for every row; fire reached it 381 times. Cold (15), lightning (17) and poison (2)
  reached it fewer times than the plan's floor of about 30, and magic never. [C] for the formula
  (fn:COMBAT_ResistFor@0x0057BE00, run:2026-10-16-combat); the per-element counts are listed under *Open questions*.
- B2. Pierce (stats 333–336) applies unless the defender is a monster at 100 or more; no logged attacker had pierce.
  Sanctuary (state 47) zeroes physical resistance against undead; not met. [I] (fn:COMBAT_ResistFor@0x0057BE00)

**B3. Absorb (`COMBAT_Absorb`).**

```
B3. Absorb(ctx, row, d: i32) → i32:                                   [C] (fn:COMBAT_Absorb@0x0057BF10, run:2026-10-16-combat, all of B3)
      p: i32 ← min(stat(def, row.absorbPctStat), 40)
      if p > 0:
        a: i32 ← MulDiv(d, p, 100);  pkt.absorbHeal += a;  d ← d − a
      f: i32 ← stat(def, row.absorbFlatStat) << 8
      if f > 0:                                                        ; [I] for the flat branch (fn:COMBAT_Absorb@0x0057BF10)
        a ← min(f, d);  pkt.absorbHeal += a;  d ← d − a
      return d
```

- B3. **Both the percent and the flat absorbed amounts are healed** to the defender at delivery (`absorbHeal`,
  packet `+0x48`). 32 percent-absorb heals of the player reproduced; this contradicts src:purediablo-absorb, which
  heals from flat absorb only. [C] (0x0057BF2A–0x0057BF6F, run:2026-10-16-combat) No logged unit had flat absorb. [I]
  (fn:COMBAT_Absorb@0x0057BF10)
- B3. Absorb runs on whatever `d` is, also a negative one: the percent of a negative `d` is a negative absorbed
  amount, which delivery does not heal (4 events, under the floor). [I] (fn:COMBAT_Absorb@0x0057BF10,
  run:2026-10-16-combat)

## Outputs

The packet with every field reduced, `absorbHeal` set, and `total` = the sum of the six damage fields (plus the
life drain of a monster attacker). No seed changes. [C] (fn:COMBAT_ApplyReductions@0x0057C1E0, run:2026-10-16-combat)

## Worked example

**A monster hit resisted by the player, per difficulty** (run:2026-10-16-combat). The defender is the expansion
`CombatSolo`/`CombatSor` Sorceress (DR 8, MDR 12, physical resist 20, fire resist 115 with fire maximum + 10) or the
classic `CombatCls` Sorceress (MDR 1, fire resist 80, fire maximum + 10). Every attack has P = 100 and a zero frame
rate. Values in 1/256 life. [C] (run:2026-10-16-combat)

| | Normal | Nightmare | Hell | classic Hell |
|---|---|---|---|---|
| session, frame | `sor-n-highlands` 1114 | `sor-nm-andariel` 825 | `solo-h-p3` 2901 | `cls-h-plains` 449 |
| attack | `imp1`'s missile `impmiss21` | `fallenshaman4`'s `shafire4` | `fallen1`, melee | `fallenshaman1`'s `shafire1` |
| fire in | 3302 | 9696 | 5444 | 37386 |
| − MDR | 3302 − 3072 = 230 | 9696 − 3072 = 6624 | 5444 − 3072 = 2372 | 37386 − 256 = 37130 |
| fire resist | 115 + 0 = 115 → cap 85 | 115 − 40 = 75 | 115 − 100 = 15 | classic: 80 − 50 = 30 |
| fire out | `MulDiv(230, 15, 100)` = 34 | `MulDiv(6624, 25, 100)` = 1656 | `MulDiv(2372, 85, 100)` = 2016 | `MulDiv(37130, 70, 100)` = 25991 |
| physical | — | — | 16878 − 2048 = 14830; × 80 % = 11864 | — |
| total, life | 34: 1549056 → 1549022 | 1656: 1549056 → 1547400 | 13880: 1265909 → 1252029 | 25991: 1526429 → 1500438 |

Normal shows the cap (115 above the 85 cap), Nightmare and Hell the expansion `ResistPenalty` (−40, −100), classic
Hell the classic −50, and the Hell melee hit physical damage through DR and the uncapped physical resistance 20. [C]
(run:2026-10-16-combat)

**A field driven negative.** In `sor-n-plains` frame 3249 (Normal) a `fallenshaman1` fire bolt carries fire 1018:
`1018 − 3072 = −2054`, the resistance is skipped, and the packet's fire and total are −2054. [C] (run:2026-10-16-combat)

**A monster defender.** In [combat/overview § Example 1](README.md#example-1-a-melee-hit-in-hell-with-crushing-blow-and-leech)
the `fallen2` (physical 15, fire 110, cold 40) takes physical `MulDiv(92195, 85, 100)` = 78365, fire 0 (immune, 110
capped to 100), cold `MulDiv(10448, 60, 100)` = 6268, the cold length `MulDiv(100, 60, 100)` = 60; magic 22020 and
poison 153 pass unreduced. No penalty and no cap apply to the monster. [C] (run:2026-10-16-combat)

## Reimplementation notes

- **DR and MDR come before the resistance**, and a field they push negative skips the resistance and stays negative.
  [C] (0x0057BFB4–0x0057C04D, run:2026-10-16-combat)
- **Penalty, then floor, then cap**: a player's 115 % fire resist in Hell is 15 %, not `min(115, 85) − 100` = −15 %.
  [C] (fn:COMBAT_ResistFor@0x0057BE00, run:2026-10-16-combat)
- **Classic uses constants, not `ResistPenalty`.** Classic Nightmare −20 and Hell −50 differ from the expansion's −40
  and −100 in `DifficultyLevels`. [C] (fn:COMBAT_ResistFor@0x0057BE00, run:2026-10-16-combat)
- **Monsters are never capped**: a monster resistance above 100 is immunity, and pierce does not lower it. [C] for
  the immunity (run:2026-10-16-combat); [I] for pierce (fn:COMBAT_ResistFor@0x0057BE00)
- **Cold and freeze lengths use cold resistance**; the poison length uses stat 110. [C]
  (data:g_DamageResistTable@0x00732980, run:2026-10-16-combat)
- **The player-row loop stops at the first monster-only row**: for a player or hireling attacker rows 9–11 are never
  reached, so the steal percents are not scaled by P. [I] (fn:COMBAT_ApplyReductions@0x0057C1E0)
- **No minimum damage.** Nothing in this path keeps a hit above 0. [I] (fn:COMBAT_ApplyReductions@0x0057C1E0)

## Evidence

- [combat/0001](../../findings/combat/0001-formulas.md) § 7 (the reductions, the table, P, the length immunities),
  § 13 (*Leads used*: the absorb heal contradicted, the reduction order held with refinement), § 15 (the confirmed
  raises and the below-the-floor bullet).
- [combat/experiments § run:2026-10-16-combat](../../findings/combat/experiments.md#run2026-10-16-combat): resistance
  applications per element (fire 2 803, cold 1 386, lightning 930, poison 1 374, magic 1 340, physical 3 544); DR,
  MDR or absorb non-zero 1 747; the classic penalty 138 / 208.
- Tables: [DifficultyLevels](../../tables/DifficultyLevels.md), [MonStats](../../tables/MonStats.md),
  [ItemStatCost](../../tables/ItemStatCost.md).
- Types: `re/types/combat.h` (`DamagePacket`, `ReduceCtx`, `ResistRow`).

## Open questions

- [L] Hell's `HireableBossDamagePercent` (25): 0 events in run:2026-10-16-combat. A mercenary hitting Andariel in
  Hell (the resume lane, plan 0037 Phase 2) tells it from `MonsterCEDamagePercent` 20.
- [L] Branches reproduced under the plan's floor of about 30 events: the prime-evil 200 (1), the negative absorbed
  amount (4), the resistance cap reached for cold (15), lightning (17) and poison (2).
- [L] Not reached: magic at or above the cap and magic immunity, pierce, flat absorb, the stat-118 halving, states
  131 and 133, sanctuary, the PvP 17 % and the hireling-against-hireling 25 %. PvP needs two clients (ADR-0008).
- [L] The handlers of event 11 (`absorbdamage`): energy shield and the bone and cyclone armours by the community's
  account; their code is skills, phase (3).
- [L] The meaning of `Unit+0xC4` bit 31, which P tests for the PvP and prime-evil cases.

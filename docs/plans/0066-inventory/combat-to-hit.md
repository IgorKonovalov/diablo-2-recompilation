# Plan 0066 inventory: combat/to-hit

- **Spec:** [combat/to-hit](../../specs/combat/to-hit.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 33; the *Count* column sums to 33.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 47 | Entry points | A player's normal attack or a skill's melee hit, … | `0x0057EC16` | ? | ? | ? | 1 |
| 2 | 50 | Entry points | A missile reaching a unit (phase (3); the to-hit … | `fn:MISSILE_HitUnit@0x005ADF10` | ? | ? | ? | 1 |
| 3 | 70 | Runtime state | arPct — 0 for a monster's melee test, the missile's stat … | `0x005AE05F` | ? | ? | ? | 1 |
| 4 | 77 | Runtime state | (combat/0001 § 12b (e), ) | tbl:ItemStatCost.txt:Stat | ? | ? | ? | 1 |
| 5 | 86 | Constants | attacker-monster range bonus — 2 | `fn:COMBAT_MeleeHitTest@0x0057EC10` | ? | ? | ? | 1 |
| 6 | 110 | A. The chance to hit (COMBAT_ToHitRoll) | TargetMods(att, def, AR, DEF) ; § A7, | `fn:COMBAT_ToHitTargetMods@0x0057D8A0` | ? | ? | ? | 1 |
| 7 | 141 | A. The chance to hit (COMBAT_ToHitRoll) | ; the formula from pct on is . | – | ? | ? | ? | 1 |
| 8 | 151 | A. The chance to hit (COMBAT_ToHitRoll) | flag. | `fn:sub_0056ECB0_SkillMissileCreate@0x0056ECB0` | ? | ? | ? | 1 |
| 9 | 157 | A. The chance to hit (COMBAT_ToHitRoll) | … player attacker (unit = 0), so stat 117 on a mercenary's items applies no state. | – | ? | ? | ? | 1 |
| 10 | 161 | A. The chance to hit (COMBAT_ToHitRoll) | for 120 000 frames with stat 31 = 0. | `fn:sub_0057D810_PreventHealHook@0x0057D810` | ? | ? | ? | 1 |
| 11 | 170 | A. The chance to hit (COMBAT_ToHitRoll) | A7. TargetMods(att, def, AR, DEF): | `fn:COMBAT_ToHitTargetMods@0x0057D8A0` | ? | ? | ? | 1 |
| 12 | 181 | A. The chance to hit (COMBAT_ToHitRoll) | attack-rating bonuses against demons and undead. No run reached these stats. | `0x0057D8BA` | ? | ? | ? | 1 |
| 13 | 186 | A. The chance to hit (COMBAT_ToHitRoll) | … the client's character screen uses plain ÷ 100 instead of MulDiv. A reimplementation uses A2–A3. | – | ? | ? | ? | 1 |
| 14 | 192 | B. Defence (UNIT_GetDefense) | B1. Defense(u) → i32: | `fn:UNIT_GetDefense@0x006223F0` | ? | ? | ? | 1 |
| 15 | 202 | B. Defence (UNIT_GetDefense) | zero for every logged unit and stay | `fn:UNIT_GetDefense@0x006223F0` | ? | ? | ? | 1 |
| 16 | 220 | C. The hit test and the defence rolls | C1. MeleeHitTest(att, def, arPct: i32, rangeExtra: i32) → result: u16: | `fn:COMBAT_MeleeHitTest@0x0057EC10` | ? | ? | ? | 1 |
| 17 | 244 | C. The hit test and the defence rolls |  | `fn:COMBAT_MeleeHitTest@0x0057EC10` | ? | ? | ? | 1 |
| 18 | 246 | C. The hit test and the defence rolls | . | – | ? | ? | ? | 1 |
| 19 | 248 | C. The hit test and the defence rolls | C1. The range test is sub_00622C40_InMeleeRange with the reach above; state 54 is uninterruptable. | – | ? | ? | ? | 1 |
| 20 | 257 | C. The hit test and the defence rolls | … ≠ 2: b ← b ÷ 3 ; moving, not walking; mode 3 (, 48), | `0x0057E00B` | ? | ? | ? | 1 |
| 21 | 265 | C. The hit test and the defence rolls | if neither hand holds a usable shield: return 0 ; the shield test: | `fn:sub_0063C8F0_InvItemQuery@0x0063C8F0` | ? | ? | ? | 1 |
| 22 | 283 | C. The hit test and the defence rolls | … session the plan allowed was spent, so the count is final and the exception stays | – | ? | ? | ? | 1 |
| 23 | 289 | C. The hit test and the defence rolls | Kerke's Sanctuary beside a two-handed weapon. Which flag each layout sets is not read. | – | ? | ? | ? | 1 |
| 24 | 304 | C. The hit test and the defence rolls | see Open questions. | `0x0057DFD5` | ? | ? | ? | 1 |
| 25 | 312 | C. The hit test and the defence rolls | … def.mode ∈ {2, 3}) or (def is a monster and def.mode ∈ {2, 15}) ; | `0x0057DD60` | ? | ? | ? | 1 |
| 26 | 320 | C. The hit test and the defence rolls | if wb > 0 and CurrentSkillCheck(def) = 13: ; | `0x0057DDAB` | ? | ? | ? | 1 |
| 27 | 337 | C. The hit test and the defence rolls | … monster defender with these stats was not logged, so its moving modes (2, 15) are | `0x0057DD60` | ? | ? | ? | 1 |
| 28 | 340 | C. The hit test and the defence rolls | with two claws in the hands; what the value stands for is not read. | `0x0057DDAB` | ? | ? | ? | 1 |
| 29 | 346 | C. The hit test and the defence rolls | blocked. The missile path itself belongs to phase (3). | `fn:MISSILE_HitUnit@0x005ADF10` | ? | ? | ? | 1 |
| 30 | 352 | Outputs | blocked, dodged, avoided, evaded, weapon block, or 0. | `struct:DamagePacket+0x04` | ? | ? | ? | 1 |
| 31 | 354 | Outputs | and dodge or avoid). | `fn:COMBAT_DefenceRoll@0x0057DFB0` | ? | ? | ? | 1 |
| 32 | 393 | Reimplementation notes | differs. | `fn:COMBAT_ToHitRoll@0x0057D9B0` | ? | ? | ? | 1 |
| 33 | 395 | Reimplementation notes | the block. | `fn:COMBAT_MeleeHitTest@0x0057EC10` | ? | ? | ? | 1 |

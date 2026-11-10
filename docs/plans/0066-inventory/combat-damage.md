# Plan 0066 inventory: combat/damage

- **Spec:** [combat/damage](../../specs/combat/damage.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 35; the *Count* column sums to 35.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 44 | Entry points | A monster's to-hit and damage stats, at its attack … — for its draws, for its stats | run:2026-10-16-combat | ? | ? | ? | 1 |
| 2 | 71 | Runtime state | (combat/0001 § 12b (e), ) | tbl:ItemStatCost.txt:Stat | ? | ? | ? | 1 |
| 3 | 78 | Constants | unarmed min/max — 1 / 2 | `fn:COMBAT_RollPhysical@0x0057B420` | ? | ? | ? | 1 |
| 4 | 79 | Constants | burn constant — 316 | `0x0057BC2F` | ? | ? | ? | 1 |
| 5 | 80 | Constants | conversion minimum length — 50 frames | `0x0057BCB2` | ? | ? | ? | 1 |
| 6 | 87 | A. COMBAT_BuildDamage in order | BuildDamage(att, def, pkt, critFlag: i32, srcdam: i32): | `fn:COMBAT_BuildDamage@0x0057B7D0` | ? | ? | ? | 1 |
| 7 | 89 | A. COMBAT_BuildDamage in order | 1. link the weapon's stat lists to att; pkt.flags /= | `0x0057B82A` | ? | ? | ? | 1 |
| 8 | 107 | A. COMBAT_BuildDamage in order | … × srcdam ÷ 128 ; drain rolls, draws as § C; the base: note 5, | – | ? | ? | ? | 1 |
| 9 | 120 | A. COMBAT_BuildDamage in order | if pkt.stunLen = 0: pkt.stunLen += stat(att, 66) × srcdam ÷ 128 ; | `0x0057BB60` | ? | ? | ? | 1 |
| 10 | 124 | A. COMBAT_BuildDamage in order | 8. if att is a player or a hireling and not (pkt.result & ): | `0x0057BC8D` | ? | ? | ? | 1 |
| 11 | 126 | A. COMBAT_BuildDamage in order | 9. if pkt.convType ≠ 0: Convert(pkt) ; § D, | `0x0057BCB2` | ? | ? | ? | 1 |
| 12 | 136 | A. COMBAT_BuildDamage in order | oracle, so step 1's composition is | `fn:sub_0057B660_UndeadDmgBonus@0x0057B660` | ? | ? | ? | 2 |
| 13 | 145 | A. COMBAT_BuildDamage in order | unit had stat 337, so the chain order is | `fn:RNG_RangeOffset@0x00472280` | ? | ? | ? | 1 |
| 14 | 146 | A. COMBAT_BuildDamage in order | ); | `0x0057B8A9` | ? | ? | ? | 1 |
| 15 | 147 | A. COMBAT_BuildDamage in order | 3. The doubling applies to physical damage only, and only when step 2 ran. | `0x0057B8A9` | ? | ? | ? | 1 |
| 16 | 150 | A. COMBAT_BuildDamage in order | physical damage at the hit (overview § B, B4). | – | ? | ? | ? | 1 |
| 17 | 161 | A. COMBAT_BuildDamage in order | writers of these fields are unfollowed. | `0x0057BA71` | ? | ? | ? | 1 |
| 18 | 168 | A. COMBAT_BuildDamage in order | for the general formula, the constant 316 itself | `0x0057BC2F` | ? | ? | ? | 1 |
| 19 | 172 | A. COMBAT_BuildDamage in order |  | `fn:UNIT_DispatchEvent@0x005C0C30` | ? | ? | ? | 1 |
| 20 | 175 | A. COMBAT_BuildDamage in order | … overlay 54 on the defender is put only when the hit-class flag was already taken. | run:2026-10-16-combat | ? | ? | ? | 1 |
| 21 | 178 | A. COMBAT_BuildDamage in order | melee build's. | `0x005AD884` | ? | ? | ? | 1 |
| 22 | 186 | B. The physical roll (COMBAT_RollPhysical) | if att holds no weapon: mn ← max(mn, 1); mx ← max(mx, 2) ; | `fn:COMBAT_RollPhysical@0x0057B420` | ? | ? | ? | 1 |
| 23 | 226 | C. One element (COMBAT_RollElemStat, COMBAT_RollRange) | … v ← (v × srcdam) ÷ 128 ; signed, toward zero; on the no-draw path | – | ? | ? | ? | 1 |
| 24 | 234 | C. One element (COMBAT_RollElemStat, COMBAT_RollRange) |  | `0x0057B932` | ? | ? | ? | 1 |
| 25 | 238 | C. One element (COMBAT_RollElemStat, COMBAT_RollRange) |  | `0x0057A8F7` | ? | ? | ? | 1 |
| 26 | 243 | D. Conversion | D1. Convert(pkt): | `0x0057BCB2` | ? | ? | ? | 1 |
| 27 | 259 | D. Conversion | (skills/0003 § 12). | `fn:sub_005D7EA0_SkillSt32Hit@0x005D7EA0` | ? | ? | ? | 1 |
| 28 | 263 | D. Conversion | and no logged event converted, so § D is unexercised. | `struct:DamagePacket+0x65` | ? | ? | ? | 1 |
| 29 | 273 | E. A monster's attack stats (MonAttackStats) | ) The stats it writes were value inputs of the run, so their formulas stay | run:2026-10-16-combat | ? | ? | ? | 1 |
| 30 | 278 | E. A monster's attack stats (MonAttackStats) | only when its El<e>Mode equals the mode passed. | `fn:sub_005A7C20_MonSetMode@0x005A7C20` | ? | ? | ? | 1 |
| 31 | 283 | E. A monster's attack stats (MonAttackStats) | the call is not read. | `fn:sub_005A4F50_MonAttackStats@0x005A4F50` | ? | ? | ? | 1 |
| 32 | 286 | E. A monster's attack stats (MonAttackStats) |  | `0x00653BC2` | ? | ? | ? | 1 |
| 33 | 290 | E. A monster's attack stats (MonAttackStats) | 316/317 and 315; 12 frze sets nothing. | `0x005A5300` | ? | ? | ? | 1 |
| 34 | 334 | Reimplementation notes | for the player's physical-only doubling | `0x0057B8A9` | ? | ? | ? | 1 |

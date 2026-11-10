# Plan 0066 inventory: combat/README

- **Spec:** [combat/README](../../specs/combat/README.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 43; the *Count* column sums to 43.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 58 | Entry points | A monster skill's melee hit | `fn:sub_005D9C80_MonSkillAttackDo@0x005D9C80` | ? | ? | ? | 1 |
| 2 | 60 | Entry points | A missile that takes a weapon share is created … — → → → | `fn:sub_0059FA30_MissileCreate@0x0059FA30` | ? | ? | ? | 1 |
| 3 | 62 | Entry points | A player skill's melee hit (packet and SrcDam from … — and the other do-functions that call | `0x005C7690` | ? | ? | ? | 1 |
| 4 | 127 | The damage packet | The packet is bytes, zeroed by the caller on its stack and copied whole onto … | – | ? | ? | ? | 1 |
| 5 | 137 | The damage packet | Flags at +: physical already set (skip the roll), already built, // no | – | ? | ? | ? | 1 |
| 6 | 164 | The ADR-0014 boundary | finisher before delivery were dropped events by rule; none occurred. | `fn:COMBAT_PrgHooksBeforeBuild@0x005D3AC0` | ? | ? | ? | 1 |
| 7 | 180 | A. The attack events | if att wields a missile weapon: create a missile; return ; | `0x0056ECB0` | ? | ? | ? | 1 |
| 8 | 186 | A. The attack events | if att has the meleeonly state flag: AttackDeliverMeleeOnly(att, def) ; | `fn:sub_0056C2D0_AttackDeliverMeleeOnly@0x0056C2D0` | ? | ? | ? | 1 |
| 9 | 187 | A. The attack events | … delivery.md § A3: the finisher's own step peeks att.seed, its srvprgfunc entries draw (§ B5), | `fn:COMBAT_PrgFinisher@0x005D5220` | ? | ? | ? | 1 |
| 10 | 200 | A. The attack events | input. | `fn:SKILLS_GetToHit@0x006449F0` | ? | ? | ? | 1 |
| 11 | 202 | A. The attack events | attack frame relies on the call made at the mode change. | `fn:sub_005D9C80_MonSkillAttackDo@0x005D9C80` | ? | ? | ? | 1 |
| 12 | 205 | A. The attack events | player formula without the divisors, and no drain rolls in its build. | `fn:sub_0063EE90_HirelingType@0x0063EE90` | ? | ? | ? | 1 |
| 13 | 210 | A. The attack events | That path is phase (3); here its packet is an input. | `fn:MISSILE_HitUnit@0x005ADF10` | ? | ? | ? | 1 |
| 14 | 214 | A. The attack events | stats. The critical chain draws then, on the owner's seed (§ B4). | `fn:sub_0064B860_MissileDamageBlock@0x0064B860` | ? | ? | ? | 1 |
| 15 | 241 | B. Draw order per event |  | `fn:COMBAT_DurabilityLoss@0x0057D3D0` | ? | ? | ? | 1 |
| 16 | 243 | B. Draw order per event | … the other stat-event handlers draw on the seed of the unit that owns them (B6). | – | ? | ? | ? | 1 |
| 17 | 265 | B. Draw order per event | attacker's leech has no draw. | `fn:COMBAT_Leech@0x0057C420` | ? | ? | ? | 1 |
| 18 | 268 | B. Draw order per event | … (B3) and steps the monster's seed one to three times when it is created (B4). | `fn:sub_0064A850_MissileCritRoll@0x0064A850` | ? | ? | ? | 1 |
| 19 | 273 | B. Draw order per event | for the player's seed ( 1 957 events); | `fn:MISSILE_ApplyDamage@0x005AD730` | ? | ? | ? | 1 |
| 20 | 275 | B. Draw order per event | At the hit, for a missile whose row has ToHit, the owner's seed draws the … | – | ? | ? | ? | 1 |
| 21 | 300 | B. Draw order per event | B4. MissileCreate(params) → missile: | `fn:sub_0059FA30_MissileCreate@0x0059FA30` | ? | ? | ? | 1 |
| 22 | 316 | B. Draw order per event | CritChain(u, w) → bool: | `fn:sub_0064A850_MissileCritRoll@0x0064A850` | ? | ? | ? | 1 |
| 23 | 327 | B. Draw order per event | rng step 1 on Unit+, with the unsigned remainder compared signed. | – | ? | ? | ? | 1 |
| 24 | 332 | B. Draw order per event | (an arrow, a javelin, a throw, a SrcDam skill missile, a monster archer's arrow). | – | ? | ? | ? | 1 |
| 25 | 335 | B. Draw order per event | source unit's seed, a missile's own, with no weapon and so no mastery step. | `fn:sub_0064B860_MissileDamageBlock@0x0064B860` | ? | ? | ? | 1 |
| 26 | 338 | B. Draw order per event | drawn (rng/seeds, Reimplementation notes). | `fn:sub_0059F940_MissilePierceCount@0x0059F940` | ? | ? | ? | 1 |
| 27 | 366 | B. Draw order per event | to the current count). | `0x005D4E80` | ? | ? | ? | 1 |
| 28 | 372 | B. Draw order per event | block or avoid only, delivery § A3). | – | ? | ? | ? | 1 |
| 29 | 377 | B. Draw order per event | state. | `fn:sub_00571AA0_UnitMsgA3@0x00571AA0` | ? | ? | ? | 1 |
| 30 | 384 | B. Draw order per event | list and their draws are delivery § E5. | – | ? | ? | ? | 1 |
| 31 | 402 | C. Chaining events on one seed | The run had no finisher events (they were dropped by rule and none occurred), so … | – | ? | ? | ? | 1 |
| 32 | 407 | C. Chaining events on one seed | A weapon-share missile the player creates (a bow or crossbow attack, a javelin, a throw, … | – | ? | ? | ? | 1 |
| 33 | 414 | C. Chaining events on one seed | attack resynchronises. | `fn:sub_005A4F50_MonAttackStats@0x005A4F50` | ? | ? | ? | 1 |
| 34 | 417 | C. Chaining events on one seed |  | `fn:sub_005A4F50_MonAttackStats@0x005A4F50` | ? | ? | ? | 1 |
| 35 | 427 | D. Branches | classic against expansion — classic ×10/12 damage and ×10/15 to-hit in Nightmare and … | `fn:sub_005A4F50_MonAttackStats@0x005A4F50` | ? | ? | ? | 1 |
| 36 | 428 | D. Branches | difficulty — for the penalty and leech ; for the freeze … | `fn:COMBAT_ApplyFreeze@0x0057B230` | ? | ? | ? | 1 |
| 37 | 429 | D. Branches | difficulty — to-hit, block, crushing blow, open wounds | `fn:COMBAT_ToHitRoll@0x0057D9B0` | ? | ? | ? | 1 |
| 38 | 431 | D. Branches | player count — expansion, Nightmare and Hell: + b/128 with b = … | `fn:sub_005A4F20_PlayerDmgBonus@0x005A4F20` | ? | ? | ? | 1 |
| 39 | 432 | D. Branches | hireling — for P 50, 35 and 25 against a boss … | `fn:sub_0063EE90_HirelingType@0x0063EE90` | ? | ? | ? | 1 |
| 40 | 433 | D. Branches | player against player — named only; no two-client run yet (ADR-0008) | `fn:COMBAT_DamagePercent@0x0057C060` | ? | ? | ? | 1 |
| 41 | 496 | Reimplementation notes | the entries and not for the peek. | `0x005D5368` | ? | ? | ? | 1 |
| 42 | 501 | Reimplementation notes | a chance above 0. | `0x0064A864` | ? | ? | ? | 1 |
| 43 | 571 | Open questions | rate (0 mismatches over 131 logs); the short tiers stay | – | ? | ? | ? | 1 |

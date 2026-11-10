# Plan 0066 inventory: combat/README

- **Spec:** [combat/README](../../specs/combat/README.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 43; the *Count* column sums to 43.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 58 | Entry points | A monster skill's melee hit | `fn:sub_005D9C80_MonSkillAttackDo@0x005D9C80` | a-logs | the `EV0` return addresses of monster attacks in c37p2 and p47h: those inside `sub_005D9C80_MonSkillAttackDo`, a counter | S5a | 1 |
| 2 | 60 | Entry points | A missile that takes a weapon share is created … — → → → | `fn:sub_0059FA30_MissileCreate@0x0059FA30` | a-logs | run:2026-10-25-skills `MC.crit` lines (984 owner draws on weapon-share rows) place the chain inside the creation | S5a | 1 |
| 3 | 62 | Entry points | A player skill's melee hit (packet and SrcDam from … — and the other do-functions that call | `0x005C7690` | c | an xref scan with a second tool (r2 `axt`) of the do-functions that call `COMBAT_MeleeHitTest` | S5b | 1 |
| 4 | 127 | The damage packet | The packet is bytes, zeroed by the caller on its stack and copied whole onto … | – | a-logs | the whole-packet compares at `BD1`, `RD1` and `AD0` in every kept combat log, plus the `COMBAT_QueueHit` copy size read with r2 | S5a | 1 |
| 5 | 137 | The damage packet | Flags at +: physical already set (skip the roll), already built, // no | – | a-logs | the packet flag and result words in every kept combat log against each named bit, a counter per bit | S5a | 1 |
| 6 | 164 | The ADR-0014 boundary | finisher before delivery were dropped events by rule; none occurred. | `fn:COMBAT_PrgHooksBeforeBuild@0x005D3AC0` | b | as delivery row 6: a `CombatAss` charge-up session with the `PRG` events modelled | H5b | 1 |
| 7 | 180 | A. The attack events | if att wields a missile weapon: create a missile; return ; | `0x0056ECB0` | b | a `CombatAma` bow session under `combat.gdb` and `skills.gdb`: a normal attack makes an `MC` creation and no `EV0` | H5b | 1 |
| 8 | 186 | A. The attack events | if att has the meleeonly state flag: AttackDeliverMeleeOnly(att, def) ; | `fn:sub_0056C2D0_AttackDeliverMeleeOnly@0x0056C2D0` | c | States.txt `meleeonly` over every row, and the branch in `SKILL_AttackDo` read with a second tool | S5b | 1 |
| 9 | 187 | A. The attack events | … delivery.md § A3: the finisher's own step peeks att.seed, its srvprgfunc entries draw (§ B5), | `fn:COMBAT_PrgFinisher@0x005D5220` | c-emu | extend run:2026-10-21-cat-emu-ass `prg_ass` to the whole finisher (as delivery row 9) | S5fe | 1 |
| 10 | 200 | A. The attack events | input. | `fn:SKILLS_GetToHit@0x006449F0` | b | a `CombatBar` session attacking with Bash on the right button: `EV0` `arPct` against `SKILLS_GetToHit` | H5b | 1 |
| 11 | 202 | A. The attack events | attack frame relies on the call made at the mode change. | `fn:sub_005D9C80_MonSkillAttackDo@0x005D9C80` | a-logs | the monster skill attacks of c37p2 and p47h: `MAS0` inside events whose `EV0` return lies in `MonSkillAttackDo`, a counter | S5a | 1 |
| 12 | 205 | A. The attack events | player formula without the divisors, and no drain rolls in its build. | `fn:sub_0063EE90_HirelingType@0x0063EE90` | a-logs | the mercenary's 1 259 `ha` events and monster hits on it: P, leech without divisors, no drain roll, a counter per branch | S5a | 1 |
| 13 | 210 | A. The attack events | That path is phase (3); here its packet is an input. | `fn:MISSILE_HitUnit@0x005ADF10` | a-logs | run:2026-10-25-skills missile builds (`BD.seed`, 778) on the missile's seed, with c37p2 `md` for the defence | S5a | 1 |
| 14 | 214 | A. The attack events | stats. The critical chain draws then, on the owner's seed (§ B4). | `fn:sub_0064B860_MissileDamageBlock@0x0064B860` | a-logs | run:2026-10-25-skills `MC` creations: the critical result and damage stats fixed at creation, against the hit's `BD` lines | S5a | 1 |
| 15 | 241 | B. Draw order per event |  | `fn:COMBAT_DurabilityLoss@0x0057D3D0` | a-logs | as delivery row 57: a draw model of durability loss and the get-hit roll checked against kept `DU`/`GH` seeds | S5a | 1 |
| 16 | 243 | B. Draw order per event | … the other stat-event handlers draw on the seed of the unit that owns them (B6). | – | c-emu | extend `prg_ass` (the finisher's entry order with entry 38's delivery first); the handlers' part is row 30's logs | S5fe | 1 |
| 17 | 265 | B. Draw order per event | attacker's leech has no draw. | `fn:COMBAT_Leech@0x0057C420` | a-logs | c37p2 and p47h monster attacks with a leech: no seed step at `LE1` on the monster's seed, a counter | S5a | 1 |
| 18 | 268 | B. Draw order per event | … (B3) and steps the monster's seed one to three times when it is created (B4). | `fn:sub_0064A850_MissileCritRoll@0x0064A850` | a-logs | run:2026-10-30-skills-catalogue `MC` owner draws for monster archer creations, a per-owner-type count | S5a | 1 |
| 19 | 273 | B. Draw order per event | for the player's seed ( 1 957 events); | `fn:MISSILE_ApplyDamage@0x005AD730` | a-logs | as row 13 | S5a | 1 |
| 20 | 275 | B. Draw order per event | At the hit, for a missile whose row has ToHit, the owner's seed draws the … | – | a-logs | run:2026-10-25-skills `THR` (269) and `BD` lines of missile hits: the owner's to-hit first, then the build's `RangeB` order | S5a | 1 |
| 21 | 300 | B. Draw order per event | B4. MissileCreate(params) → missile: | `fn:sub_0059FA30_MissileCreate@0x0059FA30` | a-logs | run:2026-10-25-skills `MC` checks (31 391 creations, `MC.crit`, `MC.pierce`) cover B4, a re-tag after a review | S5a | 1 |
| 22 | 316 | B. Draw order per event | CritChain(u, w) → bool: | `fn:sub_0064A850_MissileCritRoll@0x0064A850` | c-emu | `sub_0064A850_MissileCritRoll` emulated with stats 337, 141 and a mastery crit (observed) above 0: two and three steps | S5fe | 1 |
| 23 | 327 | B. Draw order per event | rng step 1 on Unit+, with the unsigned remainder compared signed. | – | c-emu | as row 22 | S5fe | 1 |
| 24 | 332 | B. Draw order per event | (an arrow, a javelin, a throw, a SrcDam skill missile, a monster archer's arrow). | – | a-logs | run:2026-10-25-skills `MC.crit`: one draw per weapon-share creation at stat 337 = 0, against the melee chain | S5a | 1 |
| 25 | 335 | B. Draw order per event | source unit's seed, a missile's own, with no weapon and so no mastery step. | `fn:sub_0064B860_MissileDamageBlock@0x0064B860` | c-emu | `sub_0064B860_MissileDamageBlock` emulated with a `SrcMissDmg` row and a source missile | S5fe | 1 |
| 26 | 338 | B. Draw order per event | drawn (rng/seeds, Reimplementation notes). | `fn:sub_0059F940_MissilePierceCount@0x0059F940` | a-logs | run:2026-10-25-skills `MC.pierce` (856 pierce counts from the local seed) | S5a | 1 |
| 27 | 366 | B. Draw order per event | to the current count). | `0x005D4E80` | a-logs | run:2026-10-21-cat-emu-ass `prg_ass` already holds the entry steps; Skills.txt rows for Fists of Fire | S5a | 1 |
| 28 | 372 | B. Draw order per event | block or avoid only, delivery § A3). | – | c-emu | as row 9: entry 38 past `SkillRollPhys` | S5fe | 1 |
| 29 | 377 | B. Draw order per event | state. | `fn:sub_00571AA0_UnitMsgA3@0x00571AA0` | c-emu | extend `prg_ass`: entries 36 and 40 whole, and `sub_00571AA0_UnitMsgA3` with no game write | S5fe | 1 |
| 30 | 384 | B. Draw order per event | list and their draws are delivery § E5. | – | a-logs | the handler fires of run:2026-10-27-skills and run:2026-10-25-skills by handler and owner (as delivery row 49) | S5a | 1 |
| 31 | 402 | C. Chaining events on one seed | The run had no finisher events (they were dropped by rule and none occurred), so … | – | b | as row 6 | H5b | 1 |
| 32 | 407 | C. Chaining events on one seed | A weapon-share missile the player creates (a bow or crossbow attack, a javelin, a throw, … | – | a-logs | the 213 player-attack resynchronisations of c37p2 sorted by the lines between (as skills/0001 § 17 did) | S5a | 1 |
| 33 | 414 | C. Chaining events on one seed | attack resynchronises. | `fn:sub_005A4F50_MonAttackStats@0x005A4F50` | a-run | as damage row 31: Act II desert sessions (`sandraider2`) counting inner `MAS` calls | H5a | 1 |
| 34 | 417 | C. Chaining events on one seed |  | `fn:sub_005A4F50_MonAttackStats@0x005A4F50` | a-logs | as row 18 | S5a | 1 |
| 35 | 427 | D. Branches | classic against expansion — classic ×10/12 damage and ×10/15 to-hit in Nightmare and … | `fn:sub_005A4F50_MonAttackStats@0x005A4F50` | a-logs | the `MAS1` stats of `cls-nm-plains` and `cls-h-plains` under the damage row-1 model (×10/12, ×10/15) | S5a | 1 |
| 36 | 428 | D. Branches | difficulty — for the penalty and leech ; for the freeze … | `fn:COMBAT_ApplyFreeze@0x0057B230` | a-logs | as delivery row 33: the p47h freeze packets' state length by `MonsterFreezeDivisor` | S5a | 1 |
| 37 | 429 | D. Branches | difficulty — to-hit, block, crushing blow, open wounds | `fn:COMBAT_ToHitRoll@0x0057D9B0` | a-logs | to-hit, block, crushing blow and open wounds by difficulty in c37p2 and p47h under the models with no difficulty term | S5a | 1 |
| 38 | 431 | D. Branches | player count — expansion, Nightmare and Hell: + b/128 with b = … | `fn:sub_005A4F20_PlayerDmgBonus@0x005A4F20` | a-logs | the `MAS1` stats of the `/players` 2, 3 and 8 sessions of c37p2 under the damage row-1 model | S5a | 1 |
| 39 | 432 | D. Branches | hireling — for P 50, 35 and 25 against a boss … | `fn:sub_0063EE90_HirelingType@0x0063EE90` | a-logs | as row 12 | S5a | 1 |
| 40 | 433 | D. Branches | player against player — named only; no two-client run yet (ADR-0008) | `fn:COMBAT_DamagePercent@0x0057C060` | a-logs | run:2026-10-20-two-clients logs (multiplayer/0001 § 6): P = 17 and `D` = 100 on every logged field; the text predates the run | S5a | 1 |
| 41 | 496 | Reimplementation notes | the entries and not for the peek. | `0x005D5368` | c-emu | as row 9 | S5fe | 1 |
| 42 | 501 | Reimplementation notes | a chance above 0. | `0x0064A864` | c-emu | as row 22 | S5fe | 1 |
| 43 | 571 | Open questions | rate (0 mismatches over 131 logs); the short tiers stay | – | d-none | meta: a backticked tag in an open question, no claim of its own | – | 1 |

**Totals by class:** a-logs 26, a-run 1, b 4, c 2, c-emu 9, d-none 1 (sum 43).

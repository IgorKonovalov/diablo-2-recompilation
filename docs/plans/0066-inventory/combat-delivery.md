# Plan 0066 inventory: combat/delivery

- **Spec:** [combat/delivery](../../specs/combat/delivery.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 67; the *Count* column sums to 67.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 51 | Entry points | The kill — → | `fn:COMBAT_GetHit@0x0057CEE0` | ? | ? | ? | 1 |
| 2 | 86 | Constants | shatter chance — 20 | `0x0057B0FA` | ? | ? | ? | 1 |
| 3 | 87 | Constants | stun caps — hireling 13, others 250 frames | `0x0057AB17` | ? | ? | ? | 1 |
| 4 | 103 | A. Queue and delivery | A2. DeliverQueued(att, def): | `fn:COMBAT_DeliverQueued@0x0057D4F0` | ? | ? | ? | 1 |
| 5 | 122 | A. Queue and delivery | in the run, resynchronised); the attacker's AI may draw in between. | `fn:COMBAT_DeliverQueued@0x0057D4F0` | ? | ? | ? | 1 |
| 6 | 125 | A. Queue and delivery | state (wolf, bear) skips it. The run met no charged state. | `fn:COMBAT_PrgFinisher@0x005D5220` | ? | ? | ? | 1 |
| 7 | 142 | A. Queue and delivery | or one whose result lacks bit , so a null argument runs nothing. | `0x005D79D1` | ? | ? | ? | 1 |
| 8 | 149 | A. Queue and delivery | physical damage for a living caster. | `0x005D6386` | ? | ? | ? | 1 |
| 9 | 155 | A. Queue and delivery | A3. PrgFinisher(att, hit): | `fn:COMBAT_PrgFinisher@0x005D5220` | ? | ? | ? | 1 |
| 10 | 177 | A. Queue and delivery | ; | `0x005D4657` | ? | ? | ? | 1 |
| 11 | 188 | A. Queue and delivery | SkillRollPhys(att, pkt, skill, lvl) ; | `0x005D3ED5` | ? | ? | ? | 1 |
| 12 | 206 | A. Queue and delivery | after the first: the remaining tries | `0x005D40D6` | ? | ? | ? | 1 |
| 13 | 220 | A. Queue and delivery | ; | `0x005D51DA` | ? | ? | ? | 1 |
| 14 | 237 | A. Queue and delivery | message . | `fn:sub_00650E70_Copy64Out@0x00650E70` | ? | ? | ? | 1 |
| 15 | 250 | A. Queue and delivery | (combat/overview § B4). | `fn:sub_0056E170_SkillRollPhys@0x0056E170` | ? | ? | ? | 1 |
| 16 | 256 | A. Queue and delivery |  | `0x005D3E80` | ? | ? | ? | 1 |
| 17 | 259 | A. Queue and delivery | … 0 the index does not move and the loop never ends, a creation per pass. | – | ? | ? | ? | 1 |
| 18 | 263 | A. Queue and delivery | −2³¹ to a value ≥ , after about 2³¹ / /4n/ passes. Not run. | `0x005D4657` | ? | ? | ? | 1 |
| 19 | 268 | A. Queue and delivery | 143 only for a non-null missile of class 568 (royalstrikechainlightning). | `0x005D465E` | ? | ? | ? | 1 |
| 20 | 273 | A. Queue and delivery | stat without ItemTgtDo (E5); any other item cast of those rows runs their srvdofunc. | tbl:Skills.txt:ItemEffect | ? | ? | ? | 1 |
| 21 | 279 | A. Queue and delivery | times (38), and steps it once more (39). | `0x005D53E0` | ? | ? | ? | 1 |
| 22 | 297 | B. Delivery (COMBAT_ApplyDamage) | if not hostile(att, def) and not (pkt.flags & ): pkt.result &= ~; return ; | `0x0057C6D5` | ? | ? | ? | 1 |
| 23 | 302 | B. Delivery (COMBAT_ApplyDamage) | B3. if (pkt.result & ) and not (pkt.result & ): ; | `0x0057C7A5` | ? | ? | ? | 1 |
| 24 | 316 | B. Delivery (COMBAT_ApplyDamage) | stat(def, 8) ← stat(def, 8) − pkt.manaSteal, 0 when below 256 ; | `0x0057C879` | ? | ? | ? | 1 |
| 25 | 322 | B. Delivery (COMBAT_ApplyDamage) | DispatchEvent(10 killed, unit: def); DispatchEvent(9 kill, unit: att) ; | `0x0057C8DD` | ? | ? | ? | 1 |
| 26 | 329 | B. Delivery (COMBAT_ApplyDamage) | registration order. | `fn:UNIT_AddEvent@0x005C0AD0` | ? | ? | ? | 1 |
| 27 | 345 | B. Delivery (COMBAT_ApplyDamage) | … 6 and the divisor), so a monster defender with mana loses manaSteal·64/divisor in 1/256 units. | – | ? | ? | ? | 1 |
| 28 | 354 | B. Delivery (COMBAT_ApplyDamage) | code, and was not run. | `fn:sub_005A1F90_UModManaHit@0x005A1F90` | ? | ? | ? | 1 |
| 29 | 358 | B. Delivery (COMBAT_ApplyDamage) | (items/tc). | `fn:COMBAT_GetHit@0x0057CEE0` | ? | ? | ? | 1 |
| 30 | 392 | C. Leech (COMBAT_Leech) | C1. A hireling attacker uses the player formula without the divisors. | `fn:sub_0063EE90_HirelingType@0x0063EE90` | ? | ? | ? | 1 |
| 31 | 404 | C. Leech (COMBAT_Leech) | have no leech after it, or do not separate them. | `fn:COMBAT_ApplyDamage@0x0057C6C0` | ? | ? | ? | 1 |
| 32 | 410 | D. Stun, cold, freeze, poison, burn | D1. ApplyStun(att, def, len = pkt.stunLen): | `fn:COMBAT_ApplyStun@0x0057AAE0` | ? | ? | ? | 1 |
| 33 | 429 | D. Stun, cold, freeze, poison, burn | D3. ApplyFreeze(att, def, len = pkt.freezeLen): | `fn:COMBAT_ApplyFreeze@0x0057B230` | ? | ? | ? | 1 |
| 34 | 435 | D. Stun, cold, freeze, poison, burn | D4. ApplyPoison(att, def, dmg = pkt.poison, len = pkt.poisonLen): | `fn:COMBAT_ApplyPoison@0x0057AC50` | ? | ? | ? | 1 |
| 35 | 444 | D. Stun, cold, freeze, poison, burn | The chill strength and the shatter flag were not asserted. | `fn:COMBAT_ApplyCold@0x0057AF80` | ? | ? | ? | 1 |
| 36 | 446 | D. Stun, cold, freeze, poison, burn | MonsterColdDivisor (1, 2, 4) shortens a monster's chill only. | `fn:sub_0057AF30_MonColdEffect@0x0057AF30` | ? | ? | ? | 1 |
| 37 | 452 | D. Stun, cold, freeze, poison, burn | state, the divisor, the mode change) was not asserted. | `0x0057B2F1` | ? | ? | ? | 1 |
| 38 | 458 | E. The stat events: crushing blow, open wounds, freeze | … handler gets the attacker, the defender, the packet and stat id << 16 / layer. | – | ? | ? | ? | 1 |
| 39 | 467 | E. The stat events: crushing blow, open wounds, freeze | if def is a player or a hireling: k: i32 ← 10 ; | `0x005C0031` | ? | ? | ? | 1 |
| 40 | 472 | E. The stat events: crushing blow, open wounds, freeze | if event = 6: k ← k × 2 ; missile, | `0x005C0031` | ? | ? | ? | 1 |
| 41 | 474 | E. The stat events: crushing blow, open wounds, freeze | … 0: cb ← cb − MulDiv(cb, min(stat(def, 36), 100), 100) ; the cap at 100 | `0x005C00C5` | ? | ? | ? | 1 |
| 42 | 485 | E. The stat events: crushing blow, open wounds, freeze | … dmg ← dmg ÷ 4; if event = 6: dmg ← dmg ÷ 2 ; | `0x005BFEEC` | ? | ? | ? | 1 |
| 43 | 486 | E. The stat events: crushing blow, open wounds, freeze | for the champion bit alone | run:2026-10-16-combat | ? | ? | ? | 1 |
| 44 | 492 | E. The stat events: crushing blow, open wounds, freeze | … pkt, event): on a melee hit (, , all of E3 but the missile terms); | `fn:STATEVENT_Freeze@0x005BFC60` | ? | ? | ? | 1 |
| 45 | 513 | E. The stat events: crushing blow, open wounds, freeze | E1. There is no difficulty and no classic branch in crushing blow. | `fn:STATEVENT_CrushingBlow@0x005BFFC0` | ? | ? | ? | 1 |
| 46 | 519 | E. The stat events: crushing blow, open wounds, freeze | are the code reading. | `0x005C0031` | ? | ? | ? | 1 |
| 47 | 533 | E. The stat events: crushing blow, open wounds, freeze | defender. | `0x005BFEEC` | ? | ? | ? | 1 |
| 48 | 562 | E. The stat events: crushing blow, open wounds, freeze | open wounds never hit the player. | `fn:sub_00580610_LifeRegenTick@0x00580610` | ? | ? | ? | 1 |
| 49 | 582 | E. The stat events: crushing blow, open wounds, freeze | E5. As above. | `data:g_StatEventFuncs@0x007325B0` | ? | ? | ? | 1 |
| 50 | 586 | E. The stat events: crushing blow, open wounds, freeze | attacker's life, capped at its maximum, with no draw. | `fn:sub_005C01D0_StatEv28HealAfterKill@0x005C01D0` | ? | ? | ? | 1 |
| 51 | 625 | E. The stat events: crushing blow, open wounds, freeze | calls not followed). | `fn:sub_0056E390_CorpsePickNear@0x0056E390` | ? | ? | ? | 1 |
| 52 | 639 | E. The stat events: crushing blow, open wounds, freeze | path's dwords. | `0x005FD979` | ? | ? | ? | 1 |
| 53 | 645 | E. The stat events: crushing blow, open wounds, freeze | join composes the handler family's casts with the cast family's runs, so it stays inferred. | `0x005C0529` | ? | ? | ? | 1 |
| 54 | 653 | E. The stat events: crushing blow, open wounds, freeze | those rows runs their srvdofunc. | `0x005C054E` | ? | ? | ? | 1 |
| 55 | 663 | E. The stat events: crushing blow, open wounds, freeze | Chain Lightning starts at the target unit. | `0x005CA330` | ? | ? | ? | 1 |
| 56 | 666 | E. The stat events: crushing blow, open wounds, freeze | and 20 for stat 196), all inside COMBAT_ApplyDamage (B5). | `0x0057C8DD` | ? | ? | ? | 1 |
| 57 | 674 | F. The boundary at delivery | their exit seeds taken. | `fn:COMBAT_DurabilityLoss@0x0057D3D0` | ? | ? | ? | 1 |
| 58 | 684 | Outputs | life, leech, the open-wounds state ; | `fn:COMBAT_ApplyDamage@0x0057C6C0` | ? | ? | ? | 1 |
| 59 | 726 | Reimplementation notes | ; | `fn:COMBAT_Absorb@0x0057BF10` | ? | ? | ? | 1 |
| 60 | 728 | Reimplementation notes | so advancing the seed there shifts every later attacker draw (A3). | `fn:COMBAT_PrgFinisher@0x005D5220` | ? | ? | ? | 1 |
| 61 | 732 | Reimplementation notes | draws two or three times on it after delivering the queued hit. | `0x0056E1C4` | ? | ? | ? | 1 |
| 62 | 735 | Reimplementation notes | … of do 42, 46 (on its bad-id path) and 50 up to them (ADR-0021, ); | run:2026-10-21-cat-emu-ass | ? | ? | ? | 1 |
| 63 | 740 | Reimplementation notes | them happen. | `0x005D4657` | ? | ? | ? | 1 |
| 64 | 742 | Reimplementation notes | … unit's, knockback, howl, stupidity, skill on attack or hit, and reanimate on the attacker's (E5). | – | ? | ? | ? | 1 |
| 65 | 747 | Reimplementation notes | skills. for the 0 (ADR-0021, cost_item, ); | run:2026-10-21-cat-emu-item | ? | ? | ? | 1 |
| 66 | 751 | Reimplementation notes | item-use entries it runs the row's srvdofunc (E5). | `0x005C054E` | ? | ? | ? | 1 |
| 67 | 752 | Reimplementation notes | … applies from a plain attack: the builder leaves burn = 2 with burnLen = 0. | – | ? | ? | ? | 1 |

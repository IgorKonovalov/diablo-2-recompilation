# Plan 0066 inventory: skills/dispatch

- **Spec:** [skills/dispatch](../../specs/skills/dispatch.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 195; the *Count* column sums to 195.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 40 | Entry points | A player's skill request at a location (packets , … | `fn:PLRMSG_SkillAtXY@0x00549AD0` | ? | ? | ? | 1 |
| 2 | 41 | Entry points | A player's skill request at a unit (packets , … | `fn:PLRMSG_SkillAtUnit@0x00549BA0` | ? | ? | ? | 1 |
| 3 | 42 | Entry points | The request checks — for codes 0, 1, 6 and 8 and their … | `fn:SKILLS_CanUse@0x00647960` | ? | ? | ? | 1 |
| 4 | 43 | Entry points | A skill mode starts (player modes 7, 8, 10–16, … — for the caster's seed in the start events of … | `fn:SKILLS_StartUsedSkill@0x0056FAF0` | ? | ? | ? | 1 |
| 5 | 44 | Entry points | The mode's action frame — for the caster's seed in the do events of … | `fn:SKILLS_DoUsedSkill@0x0056FC50` | ? | ? | ? | 1 |
| 6 | 46 | Entry points | A periodic or aura skill runs again (unit events … | `fn:EVENT_SelectedAuraTick@0x0056FCB0` | ? | ? | ? | 1 |
| 7 | 47 | Entry points | An item's chance-to-cast fires | `fn:ITEMSKILL_Cast@0x005FDA80` | ? | ? | ? | 1 |
| 8 | 48 | Entry points | A player's normal attack under a charged progressive state | `fn:COMBAT_PrgFinisher@0x005D5220` | ? | ? | ? | 1 |
| 9 | 49 | Entry points | A stat event fires on a unit | `fn:UNIT_DispatchEvent@0x005C0C30` | ? | ? | ? | 1 |
| 10 | 50 | Entry points | A skill summons a monster | `fn:sub_0056D940_SpawnOwnedMonster@0x0056D940` | ? | ? | ? | 1 |
| 11 | 51 | Entry points | A monster's AI uses a skill | `fn:sub_005DEAD0_MonAiUseSkill@0x005DEAD0` | ? | ? | ? | 1 |
| 12 | 94 | Inputs and oracles | the frame of a mode that carries event code … — a logged input: animation timing is plan 0050's | `fn:sub_00580460_PlrModeSkillFrame@0x00580460` | ? | ? | ? | 1 |
| 13 | 95 | Inputs and oracles | the monster's choice of skill, mode and target — an input here: monsters/ai/machinery § T for the tier, … | `fn:sub_005DEAD0_MonAiUseSkill@0x005DEAD0` | ? | ? | ? | 1 |
| 14 | 96 | Inputs and oracles | the numbered start and do functions outside § O — value oracles of the checker; specified in the catalogue | `data:g_SkillDoFuncs@0x007322B0` | ? | ? | ? | 1 |
| 15 | 97 | Inputs and oracles | SKILLS_ForUnitsInRange's and SkillForUnitsNearTarget's unit order, SkillUnitFilter — logged as the list of units the callback ran … | `fn:SKILLS_ForUnitsInRange@0x0056B7E0` | ? | ? | ? | 1 |
| 16 | 98 | Inputs and oracles | the pet chosen for removal — a logged value | `fn:sub_00575850_PetLimit@0x00575850` | ? | ? | ? | 1 |
| 17 | 99 | Inputs and oracles | a calc's value — data/calc | `fn:SKILLS_EvalCalc@0x00646CA0` | ? | ? | ? | 1 |
| 18 | 105 | Constants | start table — g_SkillStartFuncs, bound | `data:g_SkillStartFuncs@0x00732140` | ? | ? | ? | 1 |
| 19 | 106 | Constants | do table — g_SkillDoFuncs, bound (shared by srvdofunc, srvprgfunc1..3, ItemEffect) | `data:g_SkillDoFuncs@0x007322B0` | ? | ? | ? | 1 |
| 20 | 107 | Constants | stat-event table — g_StatEventFuncs, 31 handlers (ids 1..31), bound | `data:g_StatEventFuncs@0x007325B0` | ? | ? | ? | 1 |
| 21 | 108 | Constants | delay state — 121 skilldelay | `fn:SKILLS_SetDelayState@0x0056EF90` | ? | ? | ? | 1 |
| 22 | 109 | Constants | blood mana state — 114 | `fn:SKILLS_PayCost@0x0056BFE0` | ? | ? | ? | 1 |
| 23 | 110 | Constants | periodic grid floor — perdelay 5 when the calc gives less than 6 | `fn:SKILLS_QueuePeriodic@0x0056CDA0` | ? | ? | ? | 1 |
| 24 | 111 | Constants | charge cap — 3 | `fn:SKILLS_AddProgressiveCharge@0x005D3320` | ? | ? | ? | 1 |
| 25 | 170 | B. The request | B1. PacketSkill(player, packet): | `data:g_SrvPacketTable@0x006E0D18` | ? | ? | ? | 1 |
| 26 | 177 | B. The request | B2. SkillAtXY(player, entry, x, y): | `fn:PLRMSG_SkillAtXY@0x00549AD0` | ? | ? | ? | 1 |
| 27 | 187 | B. The request | B3. SkillAtUnit(player, entry, type, guid, walk): | `fn:PLRMSG_SkillAtUnit@0x00549BA0` | ? | ? | ? | 1 |
| 28 | 196 | B. The request | the unit form needs the unit in the same act. | `fn:sub_005496F0_PktReadXY@0x005496F0` | ? | ? | ? | 1 |
| 29 | 200 | B. The request | the checks then decide. | `0x00549D50` | ? | ? | ? | 1 |
| 30 | 202 | B. The request | and 1 for a player in a meleeonly state. | `fn:SKILLS_GetRangeType@0x00645460` | ? | ? | ? | 1 |
| 31 | 205 | B. The request | sets + ← 0. So Attack and Left Hand Swing alternate, request by request. | – | ? | ? | ? | 1 |
| 32 | 237 | C. The request checks (SKILLS_CanUse) | C1. SKILLS_CanUse(unit, entry) → i32: | `fn:SKILLS_CanUse@0x00647960` | ? | ? | ? | 1 |
| 33 | 257 | C. The request checks (SKILLS_CanUse) | record. | `fn:SKILLS_CanUse@0x00647960` | ? | ? | ? | 1 |
| 34 | 260 | C. The request checks (SKILLS_CanUse) | … Hand Swing (5) dual wield and a weapon in the hand; any other skill passes. | – | ? | ? | ? | 1 |
| 35 | 263 | C. The request checks (SKILLS_CanUse) | … (for skills 4 and 5 with the primary weapon taken out of its hand first). | – | ? | ? | ? | 1 |
| 36 | 268 | C. The request checks (SKILLS_CanUse) | cost ≤ stat 8. | `fn:SKILLS_ManaOk@0x00647540` | ? | ? | ? | 1 |
| 37 | 273 | C. The request checks (SKILLS_CanUse) | level term rests on the payments of F1, not on these. | run:2026-10-27-skills | ? | ? | ? | 1 |
| 38 | 276 | C. The request checks (SKILLS_CanUse) | other value passes. | `fn:SKILLS_RestrictOk@0x00644060` | ? | ? | ? | 1 |
| 39 | 279 | C. The request checks (SKILLS_CanUse) | first frame needs startmana, later ones the per-use cost only. | `fn:SKILLS_StartManaOk@0x006440F0` | ? | ? | ? | 1 |
| 40 | 282 | C. The request checks (SKILLS_CanUse) | layer skill · 64 + (level & ); a missing item passes. | `fn:SKILLS_ItemChargesOk@0x00647840` | ? | ? | ? | 1 |
| 41 | 291 | C. The request checks (SKILLS_CanUse) | request, stated from the code reading. | `0x004D9FC5` | ? | ? | ? | 1 |
| 42 | 292 | C. The request checks (SKILLS_CanUse) | … monster does not pass through SKILLS_CanUse on its way to the mode start (§ M). | – | ? | ? | ? | 1 |
| 43 | 319 | D. The mode start | D1. PlayerModeCmd(entry, mode, x, y, force): | `fn:sub_005809D0_PlayerModeCmd@0x005809D0` | ? | ? | ? | 1 |
| 44 | 326 | D. The mode start | D2. SKILLS_StartUsedSkill(game, unit) → i32: | `fn:SKILLS_StartUsedSkill@0x0056FAF0` | ? | ? | ? | 1 |
| 45 | 338 | D. The mode start | D3. SKILLS_SrvStart(game, unit, id, lvl, noCost) → i32: | `fn:SKILLS_SrvStart@0x0056F640` | ? | ? | ? | 1 |
| 46 | 355 | D. The mode start |  | `0x0056FB49` | ? | ? | ? | 1 |
| 47 | 358 | D. The mode start | passes. | `fn:SKILLS_TargetCheck@0x0056CC60` | ? | ? | ? | 1 |
| 48 | 361 | D. The mode start | are where it matters. | `0x0056FBB2` | ? | ? | ? | 1 |
| 49 | 364 | D. The mode start | exception and no state-114 branch (unlike C4). | `fn:SKILLS_SrvManaCheck@0x0056C160` | ? | ? | ? | 1 |
| 50 | 366 | D. The mode start | usemanaondo rows (Plague Javelin, Blade Fury). noCost 1 comes from an item cast (§ H). | – | ? | ? | ? | 1 |
| 51 | 370 | D. The mode start | more there. | `fn:sub_005CAF30_SkillDo83DeliverRestart@0x005CAF30` | ? | ? | ? | 1 |
| 52 | 380 | E. The do frame and SKILLS_SrvDo | E1. PlayerSkillFrame(unit, event) → i32: | `fn:sub_00580460_PlrModeSkillFrame@0x00580460` | ? | ? | ? | 1 |
| 53 | 387 | E. The do frame and SKILLS_SrvDo | E2. MonsterAttackFrame(unit): | `fn:sub_005A7670_MonAttackFrame@0x005A7670` | ? | ? | ? | 1 |
| 54 | 393 | E. The do frame and SKILLS_SrvDo | E3. SKILLS_DoUsedSkill(unit): | `fn:SKILLS_DoUsedSkill@0x0056FC50` | ? | ? | ? | 1 |
| 55 | 397 | E. The do frame and SKILLS_SrvDo | E4. SKILLS_SrvDo(game, unit, id, lvl, pay, item, effect) → i32: | `fn:SKILLS_SrvDo@0x0056F7F0` | ? | ? | ? | 1 |
| 56 | 428 | E. The do frame and SKILLS_SrvDo | it. | `0x0057FED8` | ? | ? | ? | 1 |
| 57 | 430 | E. The do frame and SKILLS_SrvDo | … do not test the bit: the attack-frame handler, and the mode-14 Unit+ = 4 case. | – | ? | ? | ? | 1 |
| 58 | 435 | E. The do frame and SKILLS_SrvDo | srvmissilea..c and get no missile here. | `fn:SKILLS_SrvDo@0x0056F7F0` | ? | ? | ? | 1 |
| 59 | 438 | E. The do frame and SKILLS_SrvDo | distance; a lob keeps the caster as its start and aims at the doubled point. | `0x0056F9D0` | ? | ? | ? | 1 |
| 60 | 441 | E. The do frame and SKILLS_SrvDo | ITEMSKILL_Cast passes a non-zero effect flag. | `fn:SKILLS_SrvDo@0x0056F7F0` | ? | ? | ? | 1 |
| 61 | 448 | E. The do frame and SKILLS_SrvDo | events. | run:2026-10-25-skills | ? | ? | ? | 1 |
| 62 | 456 | F. Costs | F2. SKILLS_PayCost(unit, id, lvl) → i32: | `fn:SKILLS_PayCost@0x0056BFE0` | ? | ? | ? | 1 |
| 63 | 474 | F. Costs | entry. | `fn:SKILLS_PayCost@0x0056BFE0` | ? | ? | ? | 1 |
| 64 | 477 | F. Costs | the floor can bind. The run's payments never reached the floor. | tbl:Skills.txt:minmana | ? | ? | ? | 1 |
| 65 | 480 | F. Costs | … nothing is taken and the skill still runs. No such refusal occurred in the run. | – | ? | ? | ? | 1 |
| 66 | 484 | F. Costs | set to 256 and the payment fails. Not reached in the run. | `fn:sub_005D2B60_BloodManaPay@0x005D2B60` | ? | ? | ? | 1 |
| 67 | 487 | F. Costs | SKILLS_PayCost after each fragment do 48 makes. | `fn:sub_005D69D0_SkillSt26BladeFury@0x005D69D0` | ? | ? | ? | 1 |
| 68 | 492 | G. The delay state; periodic, aura and channelled skills | G1. SKILLS_SetDelayState(game, unit, d): | `fn:SKILLS_SetDelayState@0x0056EF90` | ? | ? | ? | 1 |
| 69 | 496 | G. The delay state; periodic, aura and channelled skills | G2. SKILLS_DelayOk(unit, entry) → bool: | `fn:SKILLS_DelayOk@0x006478F0` | ? | ? | ? | 1 |
| 70 | 499 | G. The delay state; periodic, aura and channelled skills | G3. SKILLS_QueuePeriodic(unit, id, lvl, selected): | `fn:SKILLS_QueuePeriodic@0x0056CDA0` | ? | ? | ? | 1 |
| 71 | 512 | G. The delay state; periodic, aura and channelled skills | server's there, which is not read. | run:2026-10-27-skills | ? | ? | ? | 1 |
| 72 | 517 | G. The delay state; periodic, aura and channelled skills | EvalCalc(delay) ≥ 1 of the row asked for. 23 stock rows have a delay. | `fn:SKILLS_DelayOk@0x006478F0` | ? | ? | ? | 1 |
| 73 | 521 | G. The delay state; periodic, aura and channelled skills | the delay is set on the sequence's first event (anim/timing § G, G5). | – | ? | ? | ? | 1 |
| 74 | 529 | G. The delay state; periodic, aura and channelled skills | channelled rows are the startmana rows (C6), not periodic. | `fn:SKILLS_QueuePeriodic@0x0056CDA0` | ? | ? | ? | 1 |
| 75 | 533 | G. The delay state; periodic, aura and channelled skills | SKILLS_SrvDo(id, lvl, 1, 0, 0) at once; then SKILLS_QueuePeriodic(id, lvl, 1). | – | ? | ? | ? | 1 |
| 76 | 535 | G. The delay state; periodic, aura and channelled skills | G5. repeat has no server reader; its three stock rows are the three startmana rows. | – | ? | ? | ? | 1 |
| 77 | 542 | H. Item-granted skills and item-event casts | charge. Not reached in the run. | `struct:SkillEntry+0x38` | ? | ? | ? | 1 |
| 78 | 544 | H. Item-granted skills and item-event casts | … item 1, 0); EVENT_ItemAuraTick repeats it while stat 151 at that layer is above 0. | – | ? | ? | ? | 1 |
| 79 | 548 | H. Item-granted skills and item-event casts | H3. ITEMSKILL_Cast(caster, id, lvl, target, x, y, effect) → bool: | `fn:ITEMSKILL_Cast@0x005FDA80` | ? | ? | ? | 1 |
| 80 | 560 | H. Item-granted skills and item-event casts | ItemEffect rows hold 1. | `fn:SKILLS_SrvDo@0x0056F7F0` | ? | ? | ? | 1 |
| 81 | 562 | H. Item-granted skills and item-event casts | runs its ItemEffect only on attack, kill or hit. | `0x005C054E` | ? | ? | ? | 1 |
| 82 | 565 | H. Item-granted skills and item-event casts |  | `fn:sub_005FDCA0_ItemCastAtUnit@0x005FDCA0` | ? | ? | ? | 1 |
| 83 | 569 | H. Item-granted skills and item-event casts | , ) The later tries, from the reading. | `fn:sub_005FD850_ItemTargetRandomPoint@0x005FD850` | ? | ? | ? | 1 |
| 84 | 571 | H. Item-granted skills and item-event casts | boundaries. | `fn:sub_005FD9C0_ItemTargetCorpse@0x005FD9C0` | ? | ? | ? | 1 |
| 85 | 581 | I. The skill packet | I1. SkillSt32Hit(game, unit, id, lvl) → i32: | `fn:sub_005D7EA0_SkillSt32Hit@0x005D7EA0` | ? | ? | ? | 1 |
| 86 | 597 | I. The skill packet | I2. SKILLS_RollElemDamage(unit, p, id, lvl): | `fn:SKILLS_RollElemDamage@0x0056E0C0` | ? | ? | ? | 1 |
| 87 | 610 | I. The skill packet | … flags & 2 is clear), which adds edPct to stat 25 and reads the conversion. | – | ? | ? | ? | 1 |
| 88 | 617 | I. The skill packet | Strike and others. | tbl:Skills.txt:EType | ? | ? | ? | 1 |
| 89 | 620 | I. The skill packet | no flags, no calc2/calc3, and SrcDam passed as stored (0 not replaced). | – | ? | ? | ? | 1 |
| 90 | 628 | I. The skill packet | the delivery's on the action frame. | `fn:SKILL_MeleeDeliverDo@0x0056F1F0` | ? | ? | ? | 1 |
| 91 | 643 | I. The skill packet | that call. | `0x00644C20` | ? | ? | ? | 1 |
| 92 | 648 | I. The skill packet | stops). | `0x00647C4D` | ? | ? | ? | 1 |
| 93 | 653 | I. The skill packet | neither GetPhysMin nor GetPhysMax, and does not read MaxDam. | `0x0056CB42` | ? | ? | ? | 1 |
| 94 | 672 | I. The skill packet | them. | `0x0056CB71` | ? | ? | ? | 1 |
| 95 | 680 | I. The skill packet | skill id from a variable, are unfollowed. | `0x00647BF0` | ? | ? | ? | 1 |
| 96 | 684 | I. The skill packet | … the kick's minimum and maximum take stat 137, then the boots' values plus stat 137. | `0x005D560F` | ? | ? | ? | 1 |
| 97 | 691 | I. The skill packet | items still reach that build. | `0x0057DC28` | ? | ? | ? | 1 |
| 98 | 697 | I. The skill packet | calcs (DmgSymPerCalc, EDmgSymPerCalc, the skill('…'.blvl) terms of calc1–calc4). | – | ? | ? | ? | 1 |
| 99 | 703 | J. Progressive charges and the finisher | J1. PrgChargeHitDo(unit, id, lvl): (srvdofunc 34: Tiger Strike, Cobra Strike, Royal Strike) | `fn:sub_005D3490_PrgChargeHitDo@0x005D3490` | ? | ? | ? | 1 |
| 100 | 710 | J. Progressive charges and the finisher | J2. AddProgressiveCharge(unit, id, lvl): | `fn:SKILLS_AddProgressiveCharge@0x005D3320` | ? | ? | ? | 1 |
| 101 | 717 | J. Progressive charges and the finisher | the parity of Unit+ >> 8, then runs 34. | `fn:sub_005D35D0_PrgChargeHitDualDo@0x005D35D0` | ? | ? | ? | 1 |
| 102 | 724 | J. Progressive charges and the finisher | … srvprgfunc n from the do table, and queues a client message carrying the peeked value. | – | ? | ? | ? | 1 |
| 103 | 727 | J. Progressive charges and the finisher | (1, 2, 3); for a row without progressive it is srvmissilea. | `fn:sub_005D3CF0_SkillSrvMissileByCharge@0x005D3CF0` | ? | ? | ? | 1 |
| 104 | 741 | J. Progressive charges and the finisher |  | `0x005D4E80` | ? | ? | ? | 1 |
| 105 | 748 | J. Progressive charges and the finisher | the current count's entry runs. | `0x005D53E0` | ? | ? | ? | 1 |
| 106 | 749 | J. Progressive charges and the finisher | J4. No finisher event was checked by (56 finisher calls logged as oracles). | run:2026-10-25-skills | ? | ? | ? | 1 |
| 107 | 755 | K. Stat-event handlers | K1. UNIT_DispatchEvent(unit, event, other, packet): | `fn:UNIT_DispatchEvent@0x005C0C30` | ? | ? | ? | 1 |
| 108 | 765 | K. Stat-event handlers | attacked…, damaged… and killed. | `data:g_StatEventFuncs@0x007325B0` | ? | ? | ? | 1 |
| 109 | 769 | K. Stat-event handlers | attacker's kill handlers (28, 31) run inside COMBAT_ApplyDamage. | `0x0057C8DD` | ? | ? | ? | 1 |
| 110 | 774 | K. Stat-event handlers | 1 — the skill's srvmissilea from the unit toward a hostile … | `fn:sub_005CAB40_StatEv01MissileAtSource@0x005CAB40` | ? | ? | ? | 1 |
| 111 | 775 | K. Stat-event handlers | 2 — a packet, result , + = calc1, on the … | `fn:sub_005CAC50_StatEv02CalcHitAttacker@0x005CAC50` | ? | ? | ? | 1 |
| 112 | 776 | K. Stat-event handlers | 3 — 1 (2 for EType 10) | `fn:sub_005CAD40_StatEv03ElemHitAttacker@0x005CAD40` | ? | ? | ? | 1 |
| 113 | 777 | K. Stat-event handlers | 4 — none while the cursed unit survives; one step when … | `fn:sub_005C5F50_StatEv04ReturnDamage@0x005C5F50` | ? | ? | ? | 1 |
| 114 | 778 | K. Stat-event handlers | 5 — draws ( 2 calls); effect | `fn:sub_005C61E0_StatEv05LifeTap@0x005C61E0` | ? | ? | ? | 1 |
| 115 | 779 | K. Stat-event handlers | 6 — draws ( 7 calls); effect | `fn:sub_005BF670_StatEv06ThornsPhys@0x005BF670` | ? | ? | ? | 1 |
| 116 | 780 | K. Stat-event handlers | 7 — draws ( 103 calls); effect | `fn:sub_005BF960_StatEv07Knockback@0x005BF960` | ? | ? | ? | 1 |
| 117 | 781 | K. Stat-event handlers | 8 — draws ( 103 calls); effect | `fn:sub_005BFA10_StatEv08Howl@0x005BFA10` | ? | ? | ? | 1 |
| 118 | 782 | K. Stat-event handlers | 9 — draws ( 65 calls); effect | `fn:sub_005BFAA0_StatEv09Stupidity@0x005BFAA0` | ? | ? | ? | 1 |
| 119 | 783 | K. Stat-event handlers | 10 — lightning stat << 8 to the attacker | `fn:sub_005BF720_StatEv10ThornsLightning@0x005BF720` | ? | ? | ? | 1 |
| 120 | 784 | K. Stat-event handlers | 11, 12 — fire, cold to the other unit | `fn:sub_005BF7D0_StatEv11ThornsFire@0x005BF7D0` | ? | ? | ? | 1 |
| 121 | 785 | K. Stat-event handlers | 13 — draws ( 9 calls); effect | `fn:sub_005BFBB0_StatEv13DamageToMana@0x005BFBB0` | ? | ? | ? | 1 |
| 122 | 786 | K. Stat-event handlers | 14–16 — draws for 15 and 16 ( 182, 138 calls), … | `fn:STATEVENT_OpenWounds@0x005BFE60` | ? | ? | ? | 1 |
| 123 | 787 | K. Stat-event handlers | 17 — draws ( 172 calls) and the cap (K2); the … | `fn:sub_005C0130_StatEv17ManaAfterKill@0x005C0130` | ? | ? | ? | 1 |
| 124 | 788 | K. Stat-event handlers | 18 — for a demon victim, life += stat · 256 | `fn:sub_005C0260_StatEv18HealAfterDemonKill@0x005C0260` | ? | ? | ? | 1 |
| 125 | 789 | K. Stat-event handlers | 19 — draws ( 103 calls); effect | `fn:sub_005C0310_StatEv19Slow@0x005C0310` | ? | ? | ? | 1 |
| 126 | 792 | K. Stat-event handlers | 22 — draws ( 2 calls); effect | `fn:sub_005C6370_StatEv22BoneArmorAbsorb@0x005C6370` | ? | ? | ? | 1 |
| 127 | 793 | K. Stat-event handlers | 23 — heals the golem and its owner | `fn:sub_005C6530_StatEv23BloodGolemHit@0x005C6530` | ? | ? | ? | 1 |
| 128 | 794 | K. Stat-event handlers | 24 — moves a share of each element to mana | `fn:sub_005CA6C0_StatEv24EnergyShield@0x005CA6C0` | ? | ? | ? | 1 |
| 129 | 795 | K. Stat-event handlers | 25 — absorbs fire, cold, lightning from aurastat1 | `fn:sub_005C87A0_StatEv25CycloneArmor@0x005C87A0` | ? | ? | ? | 1 |
| 130 | 796 | K. Stat-event handlers | 26 — the owner loses life with the golem, floor 256 | `fn:sub_005C6690_StatEv26BloodGolemDamaged@0x005C6690` | ? | ? | ? | 1 |
| 131 | 797 | K. Stat-event handlers | 27 — slow by its stat 150 | `fn:sub_005C6760_StatEv27ClayGolemSlow@0x005C6760` | ? | ? | ? | 1 |
| 132 | 799 | K. Stat-event handlers | 29 — draws ( 78 calls); effect | `fn:sub_005C0770_StatEv29RestInPeace@0x005C0770` | ? | ? | ? | 1 |
| 133 | 801 | K. Stat-event handlers | 31 — stat 155 | `fn:STATEVENT_Reanimate@0x005C09E0` | ? | ? | ? | 1 |
| 134 | 819 | K. Stat-event handlers | , and the handlers no session fired (1–4, 10–12, 14, | – | ? | ? | ? | 1 |
| 135 | 820 | K. Stat-event handlers | 18, 23–27, 30, 31). | `0x005BFA38` | ? | ? | ? | 1 |
| 136 | 826 | K. Stat-event handlers | came at full mana) and overlay 151 are the reading. | run:2026-10-27-skills | ? | ? | ? | 1 |
| 137 | 832 | K. Stat-event handlers | (combat/to-hit). | `fn:sub_0057D810_PreventHealHook@0x0057D810` | ? | ? | ? | 1 |
| 138 | 838 | K. Stat-event handlers | a monster defender outside 704–709, so the type and class tests are the reading. | run:2026-10-27-skills | ? | ? | ? | 1 |
| 139 | 843 | L. Summons | L1. SkillDo114Summon(unit, id, lvl) → i32: (Raven; the pattern of the summon do functions) | `fn:sub_005C6910_SkillDo114Summon@0x005C6910` | ? | ? | ? | 1 |
| 140 | 851 | L. Summons | L2. SummonSetLevel(owner, m, lvl, skillLvl): | `fn:sub_005C49E0_SummonSetLevel@0x005C49E0` | ? | ? | ? | 1 |
| 141 | 858 | L. Summons | L3. SpawnOwnedMonster(block) → unit: | `fn:sub_0056D940_SpawnOwnedMonster@0x0056D940` | ? | ? | ? | 1 |
| 142 | 872 | L. Summons | … summons share one input: the clamps, which do not bind at 84, are the reading. | run:2026-10-25-skills | ? | ? | ? | 1 |
| 143 | 874 | L. Summons | a summon gets them whole, whatever its class's noRatio bit. | `fn:sub_005C49E0_SummonSetLevel@0x005C49E0` | ? | ? | ? | 1 |
| 144 | 878 | L. Summons | (64-bit when large), sumskill1..5 with sumskcalc, sumumod, sumoverlay, and the equipment init. | – | ? | ? | ? | 1 |
| 145 | 881 | L. Summons | SpawnOwnedMonster adds no draw of its own. | `fn:sub_005B2F20_SpawnAtPos@0x005B2F20` | ? | ? | ? | 1 |
| 146 | 891 | L. Summons | noRatio (its MonLvl term), the golems and the other summons are the reading. | `fn:sub_005C4470_SummonInitStats@0x005C4470` | ? | ? | ? | 1 |
| 147 | 896 | L. Summons | later falls (a skill shrine wearing off), PetLimitRefresh recomputes each type's limit and runs PetLimit. | – | ? | ? | ? | 1 |
| 148 | 901 | L. Summons | L5. RaiseSkeletonDo(unit, id, lvl): (srvdofunc 31) | `fn:sub_005C4B00_SkillDo31RaiseSkeleton@0x005C4B00` | ? | ? | ? | 1 |
| 149 | 916 | L. Summons | … (no draw at skill level 2 or less) and the class-364 path are the reading. | – | ? | ? | ? | 1 |
| 150 | 923 | M. Monster skill use | frame SKILLS_DoUsedSkill (E2). The command is monsters/ai/machinery § B; the choice is an input here. | `fn:sub_005DEAD0_MonAiUseSkill@0x005DEAD0` | ? | ? | ? | 1 |
| 151 | 929 | M. Monster skill use | combat/damage § E's. | – | ? | ? | ? | 1 |
| 152 | 943 | M. Monster skill use | values in every call), the classic scaling, the expansion bonus, and type 10's redraw. | `0x005A4FB3` | ? | ? | ? | 1 |
| 153 | 950 | M. Monster skill use | the attack mode's min, max and to-hit, before the classic and player-count adjustments. | – | ? | ? | ? | 1 |
| 154 | 967 | M. Monster skill use | … and 428. SKILLS_GetPhysMin, GetPhysMax and GetToHit are checked only at this one row and level. | – | ? | ? | ? | 1 |
| 155 | 977 | N. Ammunition and weapon wear | gates are items/economy § H. | – | ? | ? | ? | 1 |
| 156 | 981 | N. Ammunition and weapon wear | N2. SkillWeaponWear(unit, chance, amount): (from start 7, Impale, after its hit: chance calc2, amount calc3) | `fn:sub_005DAA40_SkillWeaponWear@0x005DAA40` | ? | ? | ? | 1 |
| 157 | 993 | N. Ammunition and weapon wear | the weapon has durability. | `fn:sub_005DAB40_SkillSt07ImpaleHit@0x005DAB40` | ? | ? | ? | 1 |
| 158 | 1002 | O. Tier A: the start and do functions | 1 Kick — for 32 do events ; the build | `0x0056CAF0` | ? | ? | ? | 1 |
| 159 | 1003 | O. Tier A: the start and do functions | 2 Throw, 4 Left Hand Throw — for Left Hand Throw's 36 do events ; otherwise | `fn:sub_0056F460_SkillThrowDo@0x0056F460` | ? | ? | ? | 1 |
| 160 | 1004 | O. Tier A: the start and do functions | 25 Plague Javelin, 12 Multiple Shot — 8: calc1 missiles fanned perpendicular to the line to … | `fn:sub_005DB410_SkillDo08MultiShot@0x005DB410` | ? | ? | ? | 1 |
| 161 | 1005 | O. Tier A: the start and do functions | 10 Jab — to-hit, defence, build, 1–2 | `0x005DB2D0` | ? | ? | ? | 1 |
| 162 | 1007 | O. Tier A: the start and do functions | 259 Fists of Fire — J1, the finisher J3 | `fn:sub_005D35D0_PrgChargeHitDualDo@0x005D35D0` | ? | ? | ? | 1 |
| 163 | 1008 | O. Tier A: the start and do functions | 117 Holy Shield, 68 Bone Armor — bit 6, STATE_GroupClear(1), STATE_ApplyTimed(aurastate, auralencalc), the aura and passive … | `fn:sub_005C9480_SkillDo18TimedSelfState@0x005C9480` | ? | ? | ? | 1 |
| 164 | 1009 | O. Tier A: the start and do functions | 42 Static Field — ForUnitsInRange(aurarangecalc, aurafilter) with calc1, calc2, the elemental length, EType … | `fn:sub_005C9800_SorSkillStaticMin@0x005C9800` | ? | ? | ? | 1 |
| 165 | 1010 | O. Tier A: the start and do functions | 48 Nova, 44 Frost Nova, 130 Howl — bit 6; NovaAtUnit(unit, srvmissilea, id, lvl, vel + calc1) | `fn:sub_005C9B50_SkillDo22NovaAtSelf@0x005C9B50` | ? | ? | ? | 1 |
| 166 | 1011 | O. Tier A: the start and do functions | 54 Teleport — the target point, room checks, the move | `fn:sub_005CA360_SkillTeleportDo@0x005CA360` | ? | ? | ? | 1 |
| 167 | 1012 | O. Tier A: the start and do functions | 56 Meteor — bit 6; srvmissilea at the target point when the … | `0x005CA3E0` | ? | ? | ? | 1 |
| 168 | 1013 | O. Tier A: the start and do functions | 66 Amplify Damage — bit 6; auratargetstate, the stats and events on the … | `fn:sub_005C37C0_SkillDo30Curse@0x005C37C0` | ? | ? | ? | 1 |
| 169 | 1014 | O. Tier A: the start and do functions | 98 Might — the aura run (stats/states § F) | `fn:sub_005CF010_PalAuraDo@0x005CF010` | ? | ? | ? | 1 |
| 170 | 1015 | O. Tier A: the start and do functions | 102 Holy Fire — 1 per run | `fn:sub_005CF3A0_AuraHitDo@0x005CF3A0` | ? | ? | ? | 1 |
| 171 | 1016 | O. Tier A: the start and do functions | 221 Raven — — | `fn:sub_005C6910_SkillDo114Summon@0x005C6910` | ? | ? | ? | 1 |
| 172 | 1017 | O. Tier A: the start and do functions | 225 Firestorm — bit 6; with calc1 > 0 one SkillMissileCreate, then … | `fn:sub_005C7160_SkillDo117Firestorm@0x005C7160` | ? | ? | ? | 1 |
| 173 | 1018 | O. Tier A: the start and do functions | 36 Fire Bolt, 251 Fire Trauma — the srvmissile only (E4) | `fn:SKILLS_SrvDo@0x0056F7F0` | ? | ? | ? | 1 |
| 174 | 1033 | O. Tier A: the start and do functions | (L5). | run:2026-10-27-skills | ? | ? | ? | 1 |
| 175 | 1050 | P. Draws and seeds per event kind | request — none (stat 328 + 1) | `fn:SKILLS_CanUse@0x00647960` | ? | ? | ? | 1 |
| 176 | 1054 | P. Draws and seeds per event kind | periodic queue — SKILLS_QueuePeriodic | `fn:SKILLS_QueuePeriodic@0x0056CDA0` | ? | ? | ? | 1 |
| 177 | 1055 | P. Draws and seeds per event kind | finisher — attacker; area units; local | `fn:COMBAT_PrgFinisher@0x005D5220` | ? | ? | ? | 1 |
| 178 | 1056 | P. Draws and seeds per event kind | handler — for the handlers § K marks ( 1 303 … | `data:g_StatEventFuncs@0x007325B0` | ? | ? | ? | 1 |
| 179 | 1058 | P. Draws and seeds per event kind | item cast — none of its own; ItemTarget 2: 2 per try | `fn:ITEMSKILL_Cast@0x005FDA80` | ? | ? | ? | 1 |
| 180 | 1059 | P. Draws and seeds per event kind | summon — for 219 summons ; otherwise | `fn:sub_005B2F20_SpawnAtPos@0x005B2F20` | ? | ? | ? | 1 |
| 181 | 1061 | P. Draws and seeds per event kind | weapon wear — SkillWeaponWear | `fn:sub_005DAA40_SkillWeaponWear@0x005DAA40` | ? | ? | ? | 1 |
| 182 | 1062 | P. Draws and seeds per event kind | Armageddon period — re-seeds the caster's seed (P2) | `fn:sub_005C8520_SkillDo146Armageddon@0x005C8520` | ? | ? | ? | 1 |
| 183 | 1079 | P. Draws and seeds per event kind | … AI logged, 41 of 49 new gaps of this shape close (monsters/ai A4 and A5). | run:2026-10-25-skills | ? | ? | ? | 1 |
| 184 | 1090 | P. Draws and seeds per event kind | draw. | `fn:sub_005C8520_SkillDo146Armageddon@0x005C8520` | ? | ? | ? | 1 |
| 185 | 1094 | Outputs | The unit's mode and used skill; Unit+ bit 6 after the do. | `fn:SKILLS_SrvDo@0x0056F7F0` | ? | ? | ? | 1 |
| 186 | 1097 | Outputs | monsters/spawn and monsters/stats. | `fn:COMBAT_ResolveAndQueue@0x0057DBF0` | ? | ? | ? | 1 |
| 187 | 1098 | Outputs | … mana (or life, or a charge), the request counter stat 328, the delay state 121. | – | ? | ? | ? | 1 |
| 188 | 1108 | Worked example | ) The step's use, low mod 100 against Raise Skeleton's Param1 (5), was not logged. | run:2026-10-25-skills | ? | ? | ? | 1 |
| 189 | 1114 | Reimplementation notes | changes every later pierce count of the player's missiles. | `0x00549D50` | ? | ? | ? | 1 |
| 190 | 1116 | Reimplementation notes |  | `0x0056F7AA` | ? | ? | ? | 1 |
| 191 | 1119 | Reimplementation notes | events by frame accordingly. | `fn:sub_005D7EA0_SkillSt32Hit@0x005D7EA0` | ? | ? | ? | 1 |
| 192 | 1122 | Reimplementation notes | One delay state blocks all delayed skills, not only the one cast. | `fn:SKILLS_DelayOk@0x006478F0` | ? | ? | ? | 1 |
| 193 | 1124 | Reimplementation notes | Unit+ = 4 case. | `0x005DEB08` | ? | ? | ? | 1 |
| 194 | 1126 | Reimplementation notes | sets. | `0x005C054E` | ? | ? | ? | 1 |
| 195 | 1127 | Reimplementation notes | The ally test of StartUsedSkill is dead. Do not add a refusal there. | `0x0056FBB2` | ? | ? | ? | 1 |

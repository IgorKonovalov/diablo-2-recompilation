# Plan 0066 inventory: stats/states

- **Spec:** [stats/states](../../specs/stats/states.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 54; the *Count* column sums to 54.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 44 | Entry points | A shrine is operated (OperateFn 2) — (16 operates over , and ) | run:2026-10-17-stats | ? | ? | ? | 1 |
| 2 | 45 | Entry points | A well is used (OperateFn 22) — → | `0x005858A0` | ? | ? | ? | 1 |
| 3 | 46 | Entry points | A unit dies, or changes mode | `fn:sub_00627540_StatListsPurgeOnDeath@0x00627540` | ? | ? | ? | 1 |
| 4 | 82 | Inputs and oracles | the shrine to-hit and damage values (SHRINE_StatValue 19 and … — value oracles | `fn:SHRINE_StatValue@0x00583840` | ? | ? | ? | 1 |
| 5 | 93 | A. The state bit and its list | UNIT_HasState answers for players, monsters and objects; STATE_Set also keeps unit flag + bit 3 | – | ? | ? | ? | 1 |
| 6 | 121 | B. The timed apply | B1. STATE_ApplyTimed(req) → list or 0: (, , all of B1 but the lines marked | `fn:STATE_ApplyTimed@0x0056E970` | ? | ? | ? | 1 |
| 7 | 123 | B. The timed apply | if target is a monster refused by its MonStats/MonStats2 bits: return 0 | `0x0056E9A7` | ? | ? | ? | 1 |
| 8 | 127 | B. The timed apply | if r > 99: return 0 | `0x0056E9C9` | ? | ? | ? | 1 |
| 9 | 129 | B. The timed apply | MulDiv's rounding and r < 0 | run:2026-10-21-shortfalls2 | ? | ? | ? | 1 |
| 10 | 130 | B. The timed apply | if UNIT_HasState(target, 57 attract): return 0 on a monster target ; | `0x0056EA40` | ? | ? | ? | 1 |
| 11 | 162 | B. The timed apply | One curse at a time. A curse looks up any list with flag , so … | – | ? | ? | ? | 1 |
| 12 | 174 | B. The timed apply | The cut's rounding is MulDiv's, read from the code: len · 84 is a multiple … | – | ? | ? | ? | 1 |
| 13 | 178 | B. The timed apply | The duration is in frames and is not rounded. The monster gate refuses every timed … | – | ? | ? | ? | 1 |
| 14 | 181 | B. The timed apply | Callers. Open wounds (state 62, 200 frames), prevent-heal, the aura target callback (§ F), the … | – | ? | ? | ? | 1 |
| 15 | 190 | B. The timed apply | The hook's type and class tests (a monster defender outside 704–709) are not separated: every … | – | ? | ? | ? | 1 |
| 16 | 193 | B. The timed apply | Use kinds 6 and 9 only (sub_005BEDA0_ItemUseTimedState: yps, wms, vps, hrb) run the group clear | – | ? | ? | ? | 1 |
| 17 | 206 | C. Expiry and removal | C2. STATE_DefaultRemoveCB(unit, state): | `fn:STATE_DefaultRemoveCB@0x0056E900` | ? | ? | ? | 1 |
| 18 | 229 | C. Expiry and removal | The client copy calls the same function with frame 0, which counts + down by … | – | ? | ? | ? | 1 |
| 19 | 231 | C. Expiry and removal | Death and mode. Death frees every counting child that is not from an item (+ … | – | ? | ? | ? | 1 |
| 20 | 264 | D. The group clear | The call is re-entered: the nested call for 139 runs inside the outer call for … | – | ? | ? | ? | 1 |
| 21 | 293 | E. The regeneration tick | if hp < 256: hp ← 256 | `0x0058065B` | ? | ? | ? | 1 |
| 22 | 295 | E. The regeneration tick | E3. StaminaTick: (, , all of E3 but the line marked | `fn:PLAYER_StaminaRegenTick@0x00580500` | ? | ? | ? | 1 |
| 23 | 298 | E. The regeneration tick | … < 256; 3, 4 and any mode outside 1..6 with b ≥ 1000 → 8 | `0x0058054A` | ? | ? | ? | 1 |
| 24 | 321 | E. The regeneration tick | The floor at 256 (one life point): a poisoned or wounded player's tick never takes … | – | ? | ? | ? | 1 |
| 25 | 330 | E. The regeneration tick | Modes 2 and 6 (walking) and the b ≥ 1000 exception were not among the … | – | ? | ? | ? | 1 |
| 26 | 334 | E. The regeneration tick | A monster's tick is sub_005A6920_MonRegenEvent (combat/delivery § E4); | – | ? | ? | ? | 1 |
| 27 | 347 | F. Auras | F3. a paladin aura run (sub_005CF010_PalAuraDo): | `fn:sub_005CF010_PalAuraDo@0x005CF010` | ? | ? | ? | 1 |
| 28 | 356 | F. Auras | for each of the six values ≠ 0: | `0x005CEE0B` | ? | ? | ? | 1 |
| 29 | 382 | F. Auras | Range and filter. A unit counts when its squared distance to the caster (subtiles) is … | – | ? | ? | ? | 1 |
| 30 | 385 | F. Auras | The filter on a player target (sub_0056B3E0_SkillUnitFilter, called with the caster and the target): | – | ? | ? | ? | 1 |
| 31 | 397 | F. Auras | A run stops at the first blank aurastat, and a 0 value is never written, … | – | ? | ? | ? | 1 |
| 32 | 400 | F. Auras | ITEMAURA_Start (stat 151 gains a level for a skill with aura and an aurastate) cancels … | – | ? | ? | ? | 1 |
| 33 | 413 | G. Shrines and wells | G1. OBJOP_Shrine(object, player): | `fn:OBJOP_Shrine@0x00583C70` | ? | ? | ? | 1 |
| 34 | 418 | G. Shrines and wells | G2. the table g_ShrineEffects, {fn, stat, state} by Shrines Code: | `data:g_ShrineEffects@0x006E1850` | ? | ? | ? | 1 |
| 35 | 423 | G. Shrines and wells | G3. SHRINE_TimedStat: SHRINE_ApplyState(duration = Duration in frames, value, stat, state) | `fn:SHRINE_TimedStat@0x00583B30` | ? | ? | ? | 1 |
| 36 | 427 | G. Shrines and wells | G4. SHRINE_Combat: state 129 with 25 damagepercent = Arg1, then 19 tohit = SHRINE_StatValue(19) | `fn:SHRINE_Combat@0x005839B0` | ? | ? | ? | 1 |
| 37 | 429 | G. Shrines and wells | 28 staminarecoverybonus = 1000; its own remove callback | `fn:SHRINE_Stamina@0x00583A70` | ? | ? | ? | 1 |
| 38 | 430 | G. Shrines and wells | SHRINE_Skill: state 134 with stat 11 = 0, then a skill refresh | `fn:SHRINE_Skill@0x00583BF0` | ? | ? | ? | 1 |
| 39 | 431 | G. Shrines and wells | G5. recharge shrines (unsigned arithmetic): | `fn:SHRINE_Refill@0x005828E0` | ? | ? | ? | 1 |
| 40 | 435 | G. Shrines and wells | G6. a well (OperateFn 22, ), with charges left (object data +): | `0x00585747` | ? | ? | ? | 1 |
| 41 | 443 | G. Shrines and wells | Shrine states are curses. States 128–137 carry the curse bit, so a shrine's list has … | – | ? | ? | ? | 1 |
| 42 | 447 | G. Shrines and wells | The state is not always the States row's stat: shrine 6 writes 171 although row … | – | ? | ? | ? | 1 |
| 43 | 450 | G. Shrines and wells | The 4 recharge shrines of the run (codes 2 and 3) were all on a … | – | ? | ? | ? | 1 |
| 44 | 452 | G. Shrines and wells | The 5 wells matched G6: Parm1 · max >> 8 = 128/256 of each maximum, … | – | ? | ? | ? | 1 |
| 45 | 466 | H. Draws per event kind | aura run (F), units per run — one draw per run whatever the number of units … | `fn:sub_005CF3A0_AuraHitDo@0x005CF3A0` | ? | ? | ? | 1 |
| 46 | 467 | H. Draws per event kind | group clear (D), remove callback, death purge, mode drop — none found in the code | `fn:STATE_GroupClear@0x0056C740` | ? | ? | ? | 1 |
| 47 | 468 | H. Draws per event kind | shrine codes 0–15 (G1–G5), well (G6) — none found in the code; 16 and 5 events … | `fn:OBJOP_Shrine@0x00583C70` | ? | ? | ? | 1 |
| 48 | 481 | H. Draws per event kind | Once per run, not once per unit. Do 66 makes its one SKILLS_RollElemDamage call at … | `0x005CF5D5` | ? | ? | ? | 1 |
| 49 | 486 | H. Draws per event kind | Holy Freeze steps each unit's own seed. Do 81 makes the same one roll per … | – | ? | ? | ? | 1 |
| 50 | 491 | H. Draws per event kind | Shrine codes 18, 21 and 22 (missile and monster shrines, phase 3 and monsters/special) do … | – | ? | ? | ? | 1 |
| 51 | 532 | Reimplementation notes | mana potions (B3); stat 98; five skills) exclude a group. | `fn:STATE_GroupClear@0x0056C740` | ? | ? | ? | 1 |
| 52 | 534 | Reimplementation notes | shrine's state. | tbl:States.txt:curse | ? | ? | ? | 1 |
| 53 | 536 | Reimplementation notes |  | `fn:sub_00580610_LifeRegenTick@0x00580610` | ? | ? | ? | 1 |
| 54 | 540 | Reimplementation notes | run hits. | `fn:sub_005CF3A0_AuraHitDo@0x005CF3A0` | ? | ? | ? | 1 |

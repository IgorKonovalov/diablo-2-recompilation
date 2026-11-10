# Plan 0066 inventory: stats/states

- **Spec:** [stats/states](../../specs/stats/states.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 54; the *Count* column sums to 54.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 44 | Entry points | A shrine is operated (OperateFn 2) — (16 operates over , and ) | run:2026-10-17-stats | a-run | `stats.gdb` `objop` shrine sessions to pass 20 operates (16 kept) | H4e | 1 |
| 2 | 45 | Entry points | A well is used (OperateFn 22) — → | `0x005858A0` | a-run | `stats.gdb` `objop` well sessions to pass 20 uses (5 kept) | H4e | 1 |
| 3 | 46 | Entry points | A unit dies, or changes mode | `fn:sub_00627540_StatListsPurgeOnDeath@0x00627540` | b | a player death and a mode change with new lines at `StatListsPurgeOnDeath` and `StatListsDropOnMode` | H4e | 1 |
| 4 | 82 | Inputs and oracles | the shrine to-hit and damage values (SHRINE_StatValue 19 and … — value oracles | `fn:SHRINE_StatValue@0x00583840` | d-none | a boundary note: the two values are oracles by ADR-0004 | – | 1 |
| 5 | 93 | A. The state bit and its list | UNIT_HasState answers for players, monsters and objects; STATE_Set also keeps unit flag + bit 3 | – | c | full-table check of the States flag columns against the loader's 40 bit-sets, read with a second tool | S4d | 1 |
| 6 | 121 | B. The timed apply | B1. STATE_ApplyTimed(req) → list or 0: (, , all of B1 but the lines marked | `fn:STATE_ApplyTimed@0x0056E970` | d-none | a mention: "the lines marked" points at the other rows | – | 1 |
| 7 | 123 | B. The timed apply | if target is a monster refused by its MonStats/MonStats2 bits: return 0 | `0x0056E9A7` | a-run | `stats.gdb` rev 9 with `STATS_MONSTA`: applies on monsters of both MonStats gate bits (chosen from a table scan) | H4e | 1 |
| 8 | 127 | B. The timed apply | if r > 99: return 0 | `0x0056E9C9` | d-edit | no stock source gives curse resistance above 99 | – | 1 |
| 9 | 129 | B. The timed apply | MulDiv's rounding and r < 0 | run:2026-10-21-shortfalls2 | a-run | another curse-resistance value whose cut is not a multiple of 100 (r < 0: no stock source) | H4e | 1 |
| 10 | 130 | B. The timed apply | if UNIT_HasState(target, 57 attract): return 0 on a monster target ; | `0x0056EA40` | d-2c | attract on a player needs a second player's curse | – | 1 |
| 11 | 162 | B. The timed apply | One curse at a time. A curse looks up any list with flag , so … | – | a-run | as row 7 with two curses in turn on one monster | H4e | 1 |
| 12 | 174 | B. The timed apply | The cut's rounding is MulDiv's, read from the code: len · 84 is a multiple … | – | d-edit | the r ≥ 100 refusal and r < 0 need values no stock source gives (rounding: row 9) | – | 1 |
| 13 | 178 | B. The timed apply | The duration is in frames and is not rounded. The monster gate refuses every timed … | – | a-logs | STA1 durations and `+0x18` end frames of the s1017 and shortfalls logs: frames, not rounded | S4d | 1 |
| 14 | 181 | B. The timed apply | Callers. Open wounds (state 62, 200 frames), prevent-heal, the aura target callback (§ F), the … | – | c | exhaustive xref scan with a second tool on `STATE_ApplyTimed` and the four appliers | S4d | 1 |
| 15 | 190 | B. The timed apply | The hook's type and class tests (a monster defender outside 704–709) are not separated: every … | – | d-owner | defenders 704–709 are the uber bosses (owner play); a player defender needs a second client | – | 1 |
| 16 | 193 | B. The timed apply | Use kinds 6 and 9 only (sub_005BEDA0_ItemUseTimedState: yps, wms, vps, hrb) run the group clear | – | c | exhaustive xref scan with a second tool on `STATE_GroupClear` (nine call sites) | S4d | 1 |
| 17 | 206 | C. Expiry and removal | C2. STATE_DefaultRemoveCB(unit, state): | `fn:STATE_DefaultRemoveCB@0x0056E900` | a-logs | EXP lines and the state clears and PAS lines after them in the s1017 logs (2 749 expiry runs) | S4d | 1 |
| 18 | 229 | C. Expiry and removal | The client copy calls the same function with frame 0, which counts + down by … | – | d-none | the client copy is presentation | – | 1 |
| 19 | 231 | C. Expiry and removal | Death and mode. Death frees every counting child that is not from an item (+ … | – | b | as row 3 | H4e | 1 |
| 20 | 264 | D. The group clear | The call is re-entered: the nested call for 139 runs inside the outer call for … | – | b | a return-address field on the group-clear lines of the shortfalls2 recipe | H4e | 1 |
| 21 | 293 | E. The regeneration tick | if hp < 256: hp ← 256 | `0x0058065B` | b | as row 24 | H4e | 1 |
| 22 | 295 | E. The regeneration tick | E3. StaminaTick: (, , all of E3 but the line marked | `fn:PLAYER_StaminaRegenTick@0x00580500` | d-none | a mention: "the line marked" points at row 23 | – | 1 |
| 23 | 298 | E. The regeneration tick | … < 256; 3, 4 and any mode outside 1..6 with b ≥ 1000 → 8 | `0x0058054A` | a-logs | the TK lines (mode, states-on bits) under the stamina shrine's bonus in run:2026-10-20-shortfalls, counted by mode | S4d | 1 |
| 24 | 321 | E. The regeneration tick | The floor at 256 (one life point): a poisoned or wounded player's tick never takes … | – | b | a new recipe: a character with more life drained by poison alone, TK lines at the floor | H4e | 1 |
| 25 | 330 | E. The regeneration tick | Modes 2 and 6 (walking) and the b ≥ 1000 exception were not among the … | – | a-run | `stats.gdb` TK lines with a walking pilot (`explore --walk`) for modes 2 and 6 | H4e | 1 |
| 26 | 334 | E. The regeneration tick | A monster's tick is sub_005A6920_MonRegenEvent (combat/delivery § E4); | – | d-none | a cross-reference and a presentation note | – | 1 |
| 27 | 347 | F. Auras | F3. a paladin aura run (sub_005CF010_PalAuraDo): | `fn:sub_005CF010_PalAuraDo@0x005CF010` | a-run | `stats.gdb` AU lines with Paladin saves running the other auras | H4e | 1 |
| 28 | 356 | F. Auras | for each of the six values ≠ 0: | `0x005CEE0B` | a-run | as row 27: Cleansing, Holy Freeze, Prayer (the cold floor and the direct stat) | H4e | 1 |
| 29 | 382 | F. Auras | Range and filter. A unit counts when its squared distance to the caster (subtiles) is … | – | b | a new line in the target callback with each unit's distance and filter result | H4e | 1 |
| 30 | 385 | F. Auras | The filter on a player target (sub_0056B3E0_SkillUnitFilter, called with the caster and the target): | – | d-2c | the party and hostility bits need a second player | – | 1 |
| 31 | 397 | F. Auras | A run stops at the first blank aurastat, and a 0 value is never written, … | – | c | full-table check of Skills `aurastat` and `aurastatcalc` (rule 2) | S4d | 1 |
| 32 | 400 | F. Auras | ITEMAURA_Start (stat 151 gains a level for a skill with aura and an aurastate) cancels … | – | a-logs | the item-aura AU ticks after the Azurewrath equips in the s1017 logs: the first tick's frame | S4d | 1 |
| 33 | 413 | G. Shrines and wells | G1. OBJOP_Shrine(object, player): | `fn:OBJOP_Shrine@0x00583C70` | a-run | as row 1, with a re-armed shrine | H4e | 1 |
| 34 | 418 | G. Shrines and wells | G2. the table g_ShrineEffects, {fn, stat, state} by Shrines Code: | `data:g_ShrineEffects@0x006E1850` | c | `g_ShrineEffects` read with a second tool against the Shrines codes | S4d | 1 |
| 35 | 423 | G. Shrines and wells | G3. SHRINE_TimedStat: SHRINE_ApplyState(duration = Duration in frames, value, stat, state) | `fn:SHRINE_TimedStat@0x00583B30` | a-run | as row 1: timed shrines of each code | H4e | 1 |
| 36 | 427 | G. Shrines and wells | G4. SHRINE_Combat: state 129 with 25 damagepercent = Arg1, then 19 tohit = SHRINE_StatValue(19) | `fn:SHRINE_Combat@0x005839B0` | a-run | as row 1: the combat and skill shrines | H4e | 1 |
| 37 | 429 | G. Shrines and wells | 28 staminarecoverybonus = 1000; its own remove callback | `fn:SHRINE_Stamina@0x00583A70` | a-logs | the two stamina-shrine operates of run:2026-10-20-shortfalls: the state's stats | S4d | 1 |
| 38 | 430 | G. Shrines and wells | SHRINE_Skill: state 134 with stat 11 = 0, then a skill refresh | `fn:SHRINE_Skill@0x00583BF0` | a-run | as row 36 | H4e | 1 |
| 39 | 431 | G. Shrines and wells | G5. recharge shrines (unsigned arithmetic): | `fn:SHRINE_Refill@0x005828E0` | a-run | as row 1: recharge and exchange shrines on a player below the maxima | H4e | 1 |
| 40 | 435 | G. Shrines and wells | G6. a well (OperateFn 22, ), with charges left (object data +): | `0x00585747` | a-run | as row 2: wells on a poisoned or frozen player | H4e | 1 |
| 41 | 443 | G. Shrines and wells | Shrine states are curses. States 128–137 carry the curse bit, so a shrine's list has … | – | a-logs | the 3 timed shrines' STA1 flags 0x22 of the s1017 logs and the States `curse` column | S4d | 1 |
| 42 | 447 | G. Shrines and wells | The state is not always the States row's stat: shrine 6 writes 171 although row … | – | c | as row 34 | S4d | 1 |
| 43 | 450 | G. Shrines and wells | The 4 recharge shrines of the run (codes 2 and 3) were all on a … | – | a-run | as row 39 | H4e | 1 |
| 44 | 452 | G. Shrines and wells | The 5 wells matched G6: Parm1 · max >> 8 = 128/256 of each maximum, … | – | a-run | as row 40 | H4e | 1 |
| 45 | 466 | H. Draws per event kind | aura run (F), units per run — one draw per run whatever the number of units … | `fn:sub_005CF3A0_AuraHitDo@0x005CF3A0` | b | as stats/README row 3 | H4e | 1 |
| 46 | 467 | H. Draws per event kind | group clear (D), remove callback, death purge, mode drop — none found in the code | `fn:STATE_GroupClear@0x0056C740` | c | `rngcallgraph` rerun with an r2 LCG scan on the four functions | S4d | 1 |
| 47 | 468 | H. Draws per event kind | shrine codes 0–15 (G1–G5), well (G6) — none found in the code; 16 and 5 events … | `fn:OBJOP_Shrine@0x00583C70` | a-run | as rows 1 and 2 (seed pairs on each operate) | H4e | 1 |
| 48 | 481 | H. Draws per event kind | Once per run, not once per unit. Do 66 makes its one SKILLS_RollElemDamage call at … | `0x005CF5D5` | b | as row 45 | H4e | 1 |
| 49 | 486 | H. Draws per event kind | Holy Freeze steps each unit's own seed. Do 81 makes the same one roll per … | – | b | a Holy Freeze session with a new line at its target callback: each unit's seed and state 107 | H4e | 1 |
| 50 | 491 | H. Draws per event kind | Shrine codes 18, 21 and 22 (missile and monster shrines, phase 3 and monsters/special) do … | – | d-none | a scope note: those shrines are out of this spec | – | 1 |
| 51 | 532 | Reimplementation notes | mana potions (B3); stat 98; five skills) exclude a group. | `fn:STATE_GroupClear@0x0056C740` | c | as row 16 | S4d | 1 |
| 52 | 534 | Reimplementation notes | shrine's state. | tbl:States.txt:curse | b | a player cursed by monsters then taking a shrine, and cursed again, with STA lines (a new route) | H4e | 1 |
| 53 | 536 | Reimplementation notes |  | `fn:sub_00580610_LifeRegenTick@0x00580610` | b | as row 24 | H4e | 1 |
| 54 | 540 | Reimplementation notes | run hits. | `fn:sub_005CF3A0_AuraHitDo@0x005CF3A0` | b | as row 45 | H4e | 1 |

**Totals by class:** a-logs 6, a-run 17, b 12, c 8, d-2c 2, d-owner 1, d-edit 2, d-none 6 (sum 54).

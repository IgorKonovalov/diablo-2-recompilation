# Plan 0066 inventory: skills/README

- **Spec:** [skills/README](../../specs/skills/README.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 25; the *Count* column sums to 25.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 60 | Entry points | A player asks to use a skill | `fn:PLRMSG_SkillAtXY@0x00549AD0` | a-logs | as dispatch row 1: the `CU0` request-site lines of run:2026-10-27-skills paired with the following `SST` | S2a | 1 |
| 2 | 65 | Entry points | A missile hits or ends — for the end and the pierce use of a … | `fn:MISSILE_HitUnit@0x005ADF10` | a-logs | the `MH` lines of hit-function rows in run:2026-10-30-skills-catalogue against the catalogue's hit emulation models (end, pierce use) | S2a | 1 |
| 3 | 66 | Entry points | A stat event fires — for the draws of the handlers dispatch § K … | `fn:UNIT_DispatchEvent@0x005C0C30` | c-emu | as dispatch row 135: the unfired handlers to their boundaries | S2be | 1 |
| 4 | 67 | Entry points | A skill summons a monster — for the new unit's seed, life and defence ( … | `fn:sub_0056D940_SpawnOwnedMonster@0x0056D940` | b | as dispatch row 146: recipes with golems, Valkyrie, wolves; `SP`/`SL` lines | H2a | 1 |
| 5 | 92 | The ADR-0014 boundary | the frame on which a mode's do function runs … — a logged input until animation timing (plan 0050) | `fn:sub_00580460_PlrModeSkillFrame@0x00580460` | a-logs | as dispatch row 12: `SST`/`SDO` frames against the anim/timing event-frame model | S2a | 1 |
| 6 | 93 | The ADR-0014 boundary | a monster's choice of skill, mode and target — an input here: monsters/ai/machinery § T for the tier, … | `fn:sub_005DEAD0_MonAiUseSkill@0x005DEAD0` | d-none | a boundary declaration: the choice is monsters/ai/machinery's claim | – | 1 |
| 7 | 94 | The ADR-0014 boundary | the numbered functions outside tier A — value oracles, taking the logged exit seeds (plan 0046) | `data:g_SkillDoFuncs@0x007322B0` | d-none | a boundary declaration: the functions are the catalogue's | – | 1 |
| 8 | 96 | The ADR-0014 boundary | the live grid at a plan or a step, … — the count ; the step's cell list | `fn:sub_00648F40_PathStepCells@0x00648F40` | d-none | a boundary pointer: the cell list is path/README's claim, inventoried there | – | 1 |
| 9 | 97 | The ADR-0014 boundary | the unit order of the area helpers, the pet … — logged values | `fn:SKILLS_ForUnitsInRange@0x0056B7E0` | d-none | a boundary declaration: unit order and the removed pet are logged inputs | – | 1 |
| 10 | 98 | The ADR-0014 boundary | a unit's final stats — stats/aggregate | `fn:SKILLS_EvalCalc@0x00646CA0` | d-none | a boundary pointer: final stats are stats/aggregate's | – | 1 |
| 11 | 106 | A. The event kinds and their seeds | request — dispatch § B, § C | `fn:SKILLS_CanUse@0x00647960` | c-emu | as dispatch row 32: `SKILLS_CanUse` for the unreached codes | S2be | 1 |
| 12 | 110 | A. The event kinds and their seeds | finisher — the entries' on the attacker, area units, local seeds | `fn:COMBAT_PrgFinisher@0x005D5220` | a-logs | as dispatch row 102: the 56 kept finisher calls of run:2026-10-25-skills | S2a | 1 |
| 13 | 111 | A. The event kinds and their seeds | handler — for the handlers § K marks ; otherwise | `data:g_StatEventFuncs@0x007325B0` | c-emu | as dispatch row 135 | S2be | 1 |
| 14 | 127 | B. Chaining (ADR-0014) | defender); the monster gaps point at the AI (monsters/ai A4 and A5). | run:2026-10-27-skills | b | as dispatch row 183: a skills session with the ai.gdb lines and defender rolls out of span | H2a | 1 |
| 15 | 135 | B. Chaining (ADR-0014) | the reading. | `fn:COMBAT_PrgFinisher@0x005D5220` | a-logs | as dispatch row 102 | S2a | 1 |
| 16 | 141 | C. Branches | player against monster — for the payment and the request codes 0, 1, … | `fn:SKILLS_SetDelayState@0x0056EF90` | a-logs | the non-player `PAY` returns and the absence of monster `DLY` and `CU` lines over the kept skills logs | S2a | 1 |
| 17 | 142 | C. Branches | player against monster — SkillMissileCreate passes a to-hit only for a monster owner | `fn:sub_0056ECB0_SkillMissileCreate@0x0056ECB0` | c | the to-hit store of `SkillMissileCreate` read with r2 against `sub_0064B860_MissileDamageBlock`'s reader (second code path) | S2c | 1 |
| 18 | 143 | C. Branches | player against monster — a player's missile ends when the player is in … | `fn:sub_005ADBB0_MissileDoFrame@0x005ADBB0` | b | a pilot step casting then taking a waypoint to town while the missile flies; `MF` lines to the end | H2a | 1 |
| 19 | 144 | C. Branches | difficulty — the difficulty record's +, +; MonLvl by difficulty | `fn:sub_005C9800_SorSkillStaticMin@0x005C9800` | a-run | SkillsSor, SkillsNec, SkillsDru in Nightmare and Hell (existing recipes): Static Field, curse lengths, Raven MonLvl | H2b | 1 |
| 20 | 145 | C. Branches | difficulty, expansion, player count — none of their own; a monster skill hit's terms … | `fn:SKILLS_SrvDo@0x0056F7F0` | a-run | the tier-A recipes in a Hell expansion game at `/players 8` and in classic; `skills.py check` | H2b | 1 |
| 21 | 146 | C. Branches | two clients — party auras, player against player | `fn:AURA_ApplyToTarget@0x005CEDC0` | d-2c | party auras and player against player need two clients | – | 1 |
| 22 | 153 | Outputs | durability changes for items/economy. | `fn:SKILLS_SrvDo@0x0056F7F0` | a-logs | as dispatch row 186: the nested lines of the kept skills logs; durability in the economy logs | S2a | 1 |
| 23 | 163 | Reimplementation notes | Run the frame pass in order: missiles, players, monsters, objects, the fifth list. | – | a-logs | run:2026-11-03-frame-order's check over the corpus: the unit lists' order per frame | S2a | 1 |
| 24 | 167 | Reimplementation notes | ) That chain is not the melee build's. | `fn:sub_0064A850_MissileCritRoll@0x0064A850` | c | `COMBAT_BuildDamage`'s critical path against `sub_0064A850_MissileCritRoll` read with r2 (two code paths) | S2c | 1 |
| 25 | 169 | Reimplementation notes | Keep the request counter: stat 328 seeds every pierce count. | `0x00549D50` | a-logs | as dispatch row 25: stat 328 against the request count in run:2026-10-27-skills | S2a | 1 |

**Totals by class:** a-logs 9, a-run 2, b 3, c 2, c-emu 3, d-2c 1, d-none 5 (sum 25).

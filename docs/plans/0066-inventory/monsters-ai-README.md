# Plan 0066 inventory: monsters/ai/README

- **Spec:** [monsters/ai/README](../../specs/monsters/ai/README.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 56; the *Count* column sums to 56.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 46 | Entry points | A kind-2 event comes due in the monster slot … — from g_MonEventFuncs[2] | `fn:sub_005B1740_MonAiEvent@0x005B1740` | ? | ? | ? | 1 |
| 2 | 47 | Entry points | A mode ends, nine direct calls of the same … — (seven) | `fn:sub_005A8030_MonModeEndGeneric@0x005A8030` | ? | ? | ? | 1 |
| 3 | 48 | Entry points | A monster is created, or its AI state changes — first from | `fn:sub_005B0E00_MonAiInit@0x005B0E00` | ? | ? | ? | 1 |
| 4 | 82 | Constants | state rows — 18 of 16 bytes | `data:g_MonAiStateRows@0x0073D358` | ? | ? | ? | 1 |
| 5 | 83 | Constants | default aidel — 15 when the cell is 0 | `fn:sub_005A73E0_MonModeStartNeutral@0x005A73E0` | ? | ? | ? | 1 |
| 6 | 84 | Constants | stunned delay — 45 under state 21 | `0x005A7419` | ? | ? | ? | 1 |
| 7 | 111 | A. The event kinds and their seeds | a mode's frames — none of the animation's but an object's start | `fn:sub_005A7C20_MonSetMode@0x005A7C20` | ? | ? | ? | 1 |
| 8 | 120 | A. The event kinds and their seeds | Chaining short by name: Andariel has 8 drawing pairs of the 20 asked and BatDemon … | – | ? | ? | ? | 1 |
| 9 | 127 | A. The event kinds and their seeds | The rest of H1. The other 8 stop at an AD0 with the monster as … | – | ? | ? | ? | 1 |
| 10 | 154 | B. The tick | B1. the frame: | `fn:sub_0052D870_GameTick@0x0052D870` | ? | ? | ? | 1 |
| 11 | 157 | B. The tick | B2. the pass: | `fn:sub_005414D0_GameRunUnitEvents@0x005414D0` | ? | ? | ? | 1 |
| 12 | 162 | B. The tick | B3. MonEventDispatch(kind, a, b): | `fn:sub_005A7F80_MonEventDispatch@0x005A7F80` | ? | ? | ? | 1 |
| 13 | 165 | B. The tick | B4. MonAiEvent(game, unit): | `fn:sub_005B1740_MonAiEvent@0x005B1740` | ? | ? | ? | 1 |
| 14 | 176 | B. The tick | Every frame is run by ServerGamesFrame over its 1 024 game slots; GameTick's other caller … | – | ? | ? | ? | 1 |
| 15 | 180 | B. The tick | A frozen monster loses a due AI event, and COMBAT_ApplyFreeze queues a new one at … | – | ? | ? | ? | 1 |
| 16 | 182 | B. The tick | The nine direct calls are all mode ends: seven in MonModeEndGeneric | `0x005A80F5` | ? | ? | ? | 1 |
| 17 | 193 | C. When the next AI event comes | C1. MonModeStartNeutral (mode NU, and MonSetMode's refusal fallback): | `fn:sub_005A73E0_MonModeStartNeutral@0x005A73E0` | ? | ? | ? | 1 |
| 18 | 201 | C. When the next AI event comes | C2. MonAiIdle(n): | `fn:sub_005DE080_MonAiIdle@0x005DE080` | ? | ? | ? | 1 |
| 19 | 203 | C. When the next AI event comes | C3. MonAiDelay(n): | `fn:sub_005DE0F0_MonAiDelay@0x005DE0F0` | ? | ? | ? | 1 |
| 20 | 205 | C. When the next AI event comes | C4. MonAiDelayEarlier(n): | `fn:sub_005DE130_MonAiDelayEarlier@0x005DE130` | ? | ? | ? | 1 |
| 21 | 210 | C. When the next AI event comes | The other queueing sites, of 30 in all: MonAiTargetOrWait (T + 20); MonKnockbackEnd (T + … | – | ? | ? | ? | 1 |
| 22 | 217 | C. When the next AI event comes | What this means. A monster that commands a mode usually gets its next AI event … | – | ? | ? | ? | 1 |
| 23 | 221 | C. When the next AI event comes | What ends a mode, from the AI's side. The AI commands only from its event, … | – | ? | ? | ? | 1 |
| 24 | 243 | D. The AI table and its dispatch | D1. MonAiEntryGet(unit, state: u32) → row: | `fn:sub_005B15D0_MonAiEntryGet@0x005B15D0` | ? | ? | ? | 1 |
| 25 | 252 | D. The AI table and its dispatch | The gate for states 10–12 () is true for a class allowed by MonModeAllowed with … | `0x00623470` | ? | ? | ? | 1 |
| 26 | 255 | D. The AI table and its dispatch | A row is {+0 searchKind, +4 init, +8 think, +C alt}. It is dispatched in … | – | ? | ? | ? | 1 |
| 27 | 261 | D. The AI table and its dispatch | The row kind (MonAiTargetByKind, a switch on +0 of MonAiEntryGet(unit, AiCtl.state); ): | `fn:sub_005B1650_MonAiTargetByKind@0x005B1650` | ? | ? | ? | 1 |
| 28 | 274 | D. The AI table and its dispatch | No target, kind 1 (MonAiTargetOrIdle), each ring walk only if MonModeAllowed | `fn:sub_005DE890_MonAiTargetOrIdle@0x005DE890` | ? | ? | ? | 1 |
| 29 | 302 | E. The AI state on the unit | E1. MonAiInit(game, unit, ctl, state: i32): | `fn:sub_005B0E00_MonAiInit@0x005B0E00` | ? | ? | ? | 1 |
| 30 | 317 | E. The AI state on the unit | A unit with state 54 takes a fatal path at . The < 18 test … | `0x005B0E14` | ? | ? | ? | 1 |
| 31 | 320 | E. The AI state on the unit | The alt as a one-event bridge. A MonAiInit call while AiCtl.think is the current row's … | – | ? | ? | ? | 1 |
| 32 | 324 | E. The AI state on the unit | The blocks. MonsterInit allocates into MonsterData+/+/+ the AiCtl | – | ? | ? | ? | 1 |
| 33 | 328 | E. The AI state on the unit | E4. | `struct:AiCtl+0x08` | ? | ? | ? | 1 |
| 34 | 341 | E. The AI state on the unit | The state rows and who sets them. MonAiInit has 33 direct calls: 21 push an … | `fn:sub_005B0E00_MonAiInit@0x005B0E00` | ? | ? | ? | 1 |
| 35 | 373 | E. The AI state on the unit | "No setter" stays a reading. No immediate call passes 2, 3, 8, 9, 14 or … | – | ? | ? | ? | 1 |
| 36 | 377 | E. The AI state on the unit | Which curse sets which state. CurseSetAiState, CurseApplyCb's one callee, passes 10, 12 or 11 for … | – | ? | ? | ? | 1 |
| 37 | 380 | E. The AI state on the unit | The inactive save and restore keep, of all this, only the saved point of parameter … | – | ? | ? | ? | 1 |
| 38 | 385 | E. The AI state on the unit | Who has which row. A monster's row is its record's. Every Hireling row's class uses … | – | ? | ? | ? | 1 |
| 39 | 394 | F. The pre-checks and the walk check | F1. MonAiPreChecks: | `fn:sub_005B10E0_MonAiPreChecks@0x005B10E0` | ? | ? | ? | 1 |
| 40 | 398 | F. The pre-checks and the walk check | F2. MonAiOpenDoor: | `fn:sub_005B0F50_MonAiOpenDoor@0x005B0F50` | ? | ? | ? | 1 |
| 41 | 402 | F. The pre-checks and the walk check | F3. MonAiBossSightPause: | `fn:sub_005B1140_MonAiBossSightPause@0x005B1140` | ? | ? | ? | 1 |
| 42 | 406 | F. The pre-checks and the walk check | F4. MonSpcWalkCheck, only with a target: | `fn:sub_005B13E0_MonSpcWalkCheck@0x005B13E0` | ? | ? | ? | 1 |
| 43 | 449 | G. The first boundary | A hand map stays a reading. For rows 6, 13, 28, 29's think and 35, … | – | ? | ? | ? | 1 |
| 44 | 519 | H. Past the first boundary | Past the first boundary, a consistency check only: rows 6 Fallen, 61 Hireable and 67 … | – | ? | ? | ? | 1 |
| 45 | 527 | H. Past the first boundary | Not under the sentence for other reasons. Row 20 Scarab: 205 decisions fork-free, but one … | – | ? | ? | ? | 1 |
| 46 | 531 | H. Past the first boundary | Everything an entry of machinery § T states past its first boundary outside those | – | ? | ? | ? | 1 |
| 47 | 541 | Worked example | MonAiIdle(5) at frame 1 000 cancels any kind-2 record of the unit and queues one … | – | ? | ? | ? | 1 |
| 48 | 546 | Reimplementation notes | The AI has two entries, the queue and a mode end. At a mode end … | – | ? | ? | ? | 1 |
| 49 | 549 | Reimplementation notes | Idle queues; a think that queues nothing leaves no kind-2 record, so such a unit … | – | ? | ? | ? | 1 |
| 50 | 551 | Reimplementation notes | MonAiEntryGet is not bounded on the state branch. The bound is MonAiInit's, and it is … | – | ? | ? | ? | 1 |
| 51 | 553 | Reimplementation notes | The row kind follows the stored state, not the class: a unit in state 12 … | – | ? | ? | ? | 1 |
| 52 | 569 | Open questions | States 2, 3, 8, 9, 14 and 17. They stay E7's reading and are not … | run:2026-11-04-r72 | ? | ? | ? | 1 |
| 53 | 576 | Open questions | emulated or | run:2026-11-04-ai-resume | ? | ? | ? | 1 |
| 54 | 577 | Open questions | Row 23's mismatches. The 8 of the rev 4 logs have the logger's 600-call limit … | – | ? | ? | ? | 1 |
| 55 | 583 | Open questions | Its frequencies are arithmetic on that map with aip2..4 33, 50, 0: Smite 33 %, … | `fn:sub_005F67B0_AiDuriel@0x005F67B0` | ? | ? | ? | 1 |
| 56 | 587 | Open questions | The code's side of C40: the callback tests the unique flag only, so a champion … | `fn:sub_005F2A00_AiGreaterMummyCb@0x005F2A00` | ? | ? | ? | 1 |

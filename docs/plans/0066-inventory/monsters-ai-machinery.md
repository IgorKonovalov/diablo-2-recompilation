# Plan 0066 inventory: monsters/ai/machinery

- **Spec:** [monsters/ai/machinery](../../specs/monsters/ai/machinery.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 114; the *Count* column sums to 114.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 24 | Entry points | Row kinds 1, 2, 4, 5 of an event | `fn:sub_005DD7F0_MonAiFindTarget@0x005DD7F0` | ? | ? | ? | 1 |
| 2 | 25 | Entry points | A think asks for its own hostile | `fn:sub_005DDC30_MonAiFindHostile@0x005DDC30` | ? | ? | ? | 1 |
| 3 | 26 | Entry points | A think commands | `fn:sub_005DDF90_MonAiSetModeAtUnit@0x005DDF90` | ? | ? | ? | 1 |
| 4 | 27 | Entry points | A think overrides the next plan | `fn:sub_005DE190_MonAiPathOverride@0x005DE190` | ? | ? | ? | 1 |
| 5 | 57 | Constants | default range — 35 when aidist is 0 | `fn:sub_005DD7F0_MonAiFindTarget@0x005DD7F0` | ? | ? | ? | 1 |
| 6 | 58 | Constants | player list skip — 55 or more | `fn:sub_005DD7F0_MonAiFindTarget@0x005DD7F0` | ? | ? | ? | 1 |
| 7 | 59 | Constants | no-plan path byte — 100; 101 → type 13 | `struct:MonCmd+0x15` | ? | ? | ? | 1 |
| 8 | 60 | Constants | override parameter range — −126..126, fatal outside; the byte capped at 77 | `fn:sub_005DE190_MonAiPathOverride@0x005DE190` | ? | ? | ? | 1 |
| 9 | 64 | Notation | Every entry below uses these. | `fn:RNG_Step@0x0045C370` | ? | ? | ? | 1 |
| 10 | 103 | A. Target search | The lists. Lists 0–7 are one per player slot: TargetListAddPlayer, from SUnitCreate for a player … | – | ? | ? | ? | 1 |
| 11 | 112 | A. Target search | A2. MonAiFindTarget(game, unit, ctl, out dist, out melee): | `fn:sub_005DD7F0_MonAiFindTarget@0x005DD7F0` | ? | ? | ? | 1 |
| 12 | 145 | A. Target search | Distances here are AiDistToPoint from the unit's own point (A7). So, forced targets aside, a … | `fn:sub_00622AA0_UnitLineBlocked@0x00622AA0` | ? | ? | ? | 1 |
| 13 | 147 | A. Target search | The forced target (MonsterData+ kind, + guid; taunt, attract, confuse): kinds 1, 2 and 4 … | – | ? | ? | ? | 1 |
| 14 | 153 | A. Target search | MonAiFindHostile is the forced target, else search kind 6 and MonAiPreferDecoy between its nearest and … | – | ? | ? | ? | 1 |
| 15 | 155 | A. Target search | The unit search. AiUnitSearch(game, unit, out, param, kind) takes g_AiSearchKinds[kind] = {walker, callback} | – | ? | ? | ? | 1 |
| 16 | 164 | A. Target search | The hostility test with a draw. AiHostileCandidate (kinds 6, 7, 11) takes a living player … | – | ? | ? | ? | 1 |
| 17 | 168 | A. Target search | The AI distance. AiDistToPoint(unit, x, y): dx ← /ux − x/, dy ← /uy − … | – | ? | ? | ? | 1 |
| 18 | 176 | A. Target search | UnitDistSq(a, b) is dx² + dy² in 32-bit signed imul and add, compared signed by … | – | ? | ? | ? | 1 |
| 19 | 178 | A. Target search | No light radius term. The search's functions call no stat getter, and no code in … | – | ? | ? | ? | 1 |
| 20 | 183 | A. Target search | MonSkillTargetOk, which 13 calls in 10 AI functions use, reads TgtPlaceCheck; see row 13 and … | – | ? | ? | ? | 1 |
| 21 | 200 | B. The command | B1. MonCmdInit(unit, mode, cmd): | `fn:sub_005A7E60_MonCmdInit@0x005A7E60` | ? | ? | ? | 1 |
| 22 | 203 | B. The command | B2. MonSetMode(game, cmd, flag): | `fn:sub_005A7C20_MonSetMode@0x005A7C20` | ? | ? | ? | 1 |
| 23 | 209 | B. The command | B3. MonAiUseSkill(game, unit, mode, skill, target, x, y): | `fn:sub_005DEAD0_MonAiUseSkill@0x005DEAD0` | ? | ? | ? | 1 |
| 24 | 218 | B. The command | B4. MonAiUseSeqSkill(skill, target, x, y): | `fn:sub_005DE000_MonAiUseSeqSkill@0x005DE000` | ? | ? | ? | 1 |
| 25 | 220 | B. The command | B5. MonAiSetMode(mode, x, y), MonAiSetModeAtUnit(mode, target): | `fn:sub_005DDFC0_MonAiSetMode@0x005DDFC0` | ? | ? | ? | 1 |
| 26 | 223 | B. The command | B6. MonAiMove(game, unit, target, mode, x, y, stop, flags) → 0 or 1: | `fn:sub_005DEB60_MonAiMove@0x005DEB60` | ? | ? | ? | 1 |
| 27 | 236 | B. The command | The walkers around MonAiMove. MonAiWalkToUnit(t, flags) (Walk), MonAiWalkToUnitStop(t, n) (WalkStop), | – | ? | ? | ? | 1 |
| 28 | 247 | B. The command | B8. Ring(r) = MonAiWanderRing(r): | `fn:sub_005DE200_MonAiWanderRing@0x005DE200` | ? | ? | ? | 1 |
| 29 | 259 | B. The command | MonAiWanderRingDirect, MonAiWanderNearUnit and MonAiRunNearUnit do alike around another unit or with mode RN. | – | ? | ? | ? | 1 |
| 30 | 263 | B. The command | B9. StepAway(other, d, flag) = MonAiStepAway: | `fn:sub_005DEFE0_MonAiStepAway@0x005DEFE0` | ? | ? | ? | 1 |
| 31 | 267 | B. The command | B10. StepAwayXY(o, n, f) = MonAiStepAwayXY: | `fn:sub_005DF140_MonAiStepAwayXY@0x005DF140` | ? | ? | ? | 1 |
| 32 | 271 | B. The command | B11. T56(target, byte, flag) = MonAiWalkToUnitType56: | `fn:sub_005DF7D0_MonAiWalkToUnitType56@0x005DF7D0` | ? | ? | ? | 1 |
| 33 | 275 | B. The command | B12. Toward(t, max, ring) = MonAiWalkTowardUnit → MonAiMoveToUnitDist(t, 2, max, ring): | `fn:sub_005DE6D0_MonAiWalkTowardUnit@0x005DE6D0` | ? | ? | ? | 1 |
| 34 | 292 | C. Idle and delay | Idle(n), Delay(n) are README § C. | `fn:sub_005DE080_MonAiIdle@0x005DE080` | ? | ? | ? | 1 |
| 35 | 314 | D. The path request | Its parts. The command's target unit or point; the path type MonCmd+; the one-shot override … | – | ? | ? | ? | 1 |
| 36 | 319 | D. The path request | D2. MonAiPathOverride(unit, type, param, byte): | `fn:sub_005DE190_MonAiPathOverride@0x005DE190` | ? | ? | ? | 1 |
| 37 | 323 | D. The path request | AiPathOverrideSet(type, param, byte): | `fn:sub_005A6260_AiPathOverrideSet@0x005A6260` | ? | ? | ? | 1 |
| 38 | 326 | D. The path request | D3. MonMovePlan(type, param, byte): | `fn:sub_005A63F0_MonMovePlan@0x005A63F0` | ? | ? | ? | 1 |
| 39 | 334 | D. The path request | D4. MonPathPlanType(type): | `fn:sub_005A6290_MonPathPlanType@0x005A6290` | ? | ? | ? | 1 |
| 40 | 339 | D. The path request | The types the AI passes are 1, 2, 5, 6, 7, 13 and 15, plus … | – | ? | ? | ? | 1 |
| 41 | 348 | D. The path request | The planner call sites from AI code. MonPathPlanType | `0x005A62EF` | ? | ? | ? | 1 |
| 42 | 352 | D. The path request | The town. For a hostile searcher a player head in a town room is never … | – | ? | ? | ? | 1 |
| 43 | 370 | E. Following | MonAiKeepNear. When AiCtl+ ≠ −1 and MonModeAllowed, the unit (AiCtl+, AiCtl+) is looked up, and | – | ? | ? | ? | 1 |
| 44 | 374 | E. Following | Who sets the pair. AiCtlFollowSet writes it from UniqueMinions (minion → its boss), SkillReviveDo, | – | ? | ? | ? | 1 |
| 45 | 377 | E. Following | The owner and the group. MonsterOwner(U) reads the owner link; a leader is a unit … | – | ? | ? | ? | 1 |
| 46 | 380 | E. Following | The parameter list at AiCtl+/+: records of bytes {next, prev, kind, +, +, +, +} … | – | ? | ? | ? | 1 |
| 47 | 386 | E. Following | A leader's call. MonHelpBlock(unit, blk) pushes a copy of blk to each minion of the … | – | ? | ? | ? | 1 |
| 48 | 394 | F. Draws and seeds of the helpers | Ring, WanderRingDirect, WanderNearUnit, RunNearUnit — 4 steps, 3 when r = 0 | `fn:sub_005DE200_MonAiWanderRing@0x005DE200` | ? | ? | ? | 1 |
| 49 | 395 | F. Draws and seeds of the helpers | MonAiMove, refusal with flag 2 — 1 step, then 4 more on low mod 100 … | `fn:sub_005DEB60_MonAiMove@0x005DEB60` | ? | ? | ? | 1 |
| 50 | 396 | F. Draws and seeds of the helpers | T56 — acting unit | `fn:sub_005DF7D0_MonAiWalkToUnitType56@0x005DF7D0` | ? | ? | ? | 1 |
| 51 | 397 | F. Draws and seeds of the helpers | MonAiForcedTarget, confusion — acting unit | `fn:sub_005DD610_MonAiForcedTarget@0x005DD610` | ? | ? | ? | 1 |
| 52 | 398 | F. Draws and seeds of the helpers | AiHostileCandidate, a player with state 146 — 1 (Range 100) | `fn:sub_005DC970_AiHostileCandidate@0x005DC970` | ? | ? | ? | 1 |
| 53 | 399 | F. Draws and seeds of the helpers | state row 2's — 1 or 2 steps, then maybe a ring walk | `0x005B14E0` | ? | ? | ? | 1 |
| 54 | 400 | F. Draws and seeds of the helpers | UModTeleportTry — as drlg/lifecycle (SpawnPosPick) | `fn:sub_005B11F0_UModTeleportTry@0x005B11F0` | ? | ? | ? | 1 |
| 55 | 401 | F. Draws and seeds of the helpers | MonSetMode — anim/timing § N, skills/dispatch § P | `fn:sub_005A7C20_MonSetMode@0x005A7C20` | ? | ? | ? | 1 |
| 56 | 407 | T. The tier AIs | , and its first boundary is per README § G. "The map" in a line … | – | ? | ? | ? | 1 |
| 57 | 410 | T. The tier AIs | Only rows 29 and 61 have an alt. | `data:g_MonAiTable@0x0073CA18` | ? | ? | ? | 1 |
| 58 | 415 | T2. Row 2 Skeleton | if not melee: | `0x005EFCF0` | ? | ? | ? | 1 |
| 59 | 423 | T2. Row 2 Skeleton | One draw out of melee range, one or two in it. | `fn:sub_005EFCF0_AiSkeleton@0x005EFCF0` | ? | ? | ? | 1 |
| 60 | 430 | T6. Row 6 Fallen | 1. if U is null, or U.mode ∈ {0, 12}: return | `0x005F02C0` | ? | ? | ? | 1 |
| 61 | 468 | T6. Row 6 Fallen | Draws. The scan's mod-20 draw only after a successful step; then at most three Range(100) … | – | ? | ? | ? | 1 |
| 62 | 473 | T6. Row 6 Fallen | Past the first boundary this row is a consistency check only (README H3). | run:2026-11-04-ai-resume-flip | ? | ? | ? | 1 |
| 63 | 478 | T9. Row 9 Wraith | if not melee: | `0x005F0A20` | ? | ? | ? | 1 |
| 64 | 489 | T13. Row 13 FallenShaman | 1. if melee and chance(3): SetModeAtUnit(4, t); return ; draw#1 | `0x005F1440` | ? | ? | ? | 1 |
| 65 | 504 | T13. Row 13 FallenShaman | Which dead. AiDeadMinionCb takes a monster in mode 12 with Unit+ bit , no state … | – | ? | ? | ? | 1 |
| 66 | 509 | T13. Row 13 FallenShaman | Draw order: melee aip3; the aip1 call to the group; the aip1 resurrect draw (only … | – | ? | ? | ? | 1 |
| 67 | 518 | T20. Row 20 Scarab | 1. rec ← AiParamsHead(U) | `0x005F2540` | ? | ? | ? | 1 |
| 68 | 537 | T20. Row 20 Scarab | A head record of another kind is left in place and the plain decision runs. | `fn:sub_0058F0D0_MonsterOwner@0x0058F0D0` | ? | ? | ? | 1 |
| 69 | 540 | T20. Row 20 Scarab | Past the first boundary it stays a reading (README H4). | `0x005F283F` | ? | ? | ? | 1 |
| 70 | 545 | T21. Row 21 Mummy | 1. if AiMonState3or19(U) and not melee: Walk(t, 7); return | `0x005F2850` | ? | ? | ? | 1 |
| 71 | 555 | T21. Row 21 Mummy | aip1 is a range, not a chance. A failed aip3 draw (100 in every stock … | – | ? | ? | ? | 1 |
| 72 | 563 | T22. Row 22 GreaterMummy | 1. if melee and chance(1): SetModeAtUnit(4, t); return ; draw#1 | `0x005F2B10` | ? | ? | ? | 1 |
| 73 | 580 | T22. Row 22 GreaterMummy | AiGreaterMummyCb. A monster other than the searcher, on the same side (AlignSame02), alignment not 2, … | – | ? | ? | ? | 1 |
| 74 | 585 | T22. Row 22 GreaterMummy | Draw order: the two melee/near draws on aip1; then aip3 only with Skill2 ≥ 0 … | – | ? | ? | ? | 1 |
| 75 | 589 | T22. Row 22 GreaterMummy | Whether a champion corpse passes the skill's own test is unlogged: see Open questions. | `fn:sub_005FD470_MonSkillTargetOk@0x005FD470` | ? | ? | ? | 1 |
| 76 | 594 | T28. Row 28 Vampire | … b0, b1, b2 ← its bits 0, 1, 2 ; Pair, Skill2 (Firewall), Skill3 (Meteor) | `0x005F4A70` | ? | ? | ? | 1 |
| 77 | 647 | T28. Row 28 Vampire | The flee step's override. p is computed only when Velocity > 0, a signed 16-bit … | – | ? | ? | ? | 1 |
| 78 | 653 | T28. Row 28 Vampire | only: step 2's melee arm, all of step 4, Skills' two uses. Controls: T56's byte … | run:2026-11-04-ai-t28 | ? | ? | ? | 1 |
| 79 | 669 | T29. Row 29 BatDemon (, alt ) | life ← UnitLifePct(U) | `0x005F5040` | ? | ? | ? | 1 |
| 80 | 697 | T29. Row 29 BatDemon (, alt ) | The aip5 · r ÷ 8 is signed and truncating, (x + (x >> 31 … | `0x005F4FFC` | ? | ? | ? | 1 |
| 81 | 704 | T30. Row 30 Fetish | 1. rec ← AiParamsHead(U) | `0x005F53E0` | ? | ? | ? | 1 |
| 82 | 733 | T30. Row 30 Fetish | No writer of a kind-14 record with a unit was found in the batch. | `fn:sub_00621F20_UnitLifePct@0x00621F20` | ? | ? | ? | 1 |
| 83 | 740 | T34. Row 34 Andariel | if melee: | `0x005F5830` | ? | ? | ? | 1 |
| 84 | 753 | T34. Row 34 Andariel | The draws compare signed (jge); the skill tests are sign tests of the i16. Ovr(1, … | `fn:sub_005DE190_MonAiPathOverride@0x005DE190` | ? | ? | ? | 1 |
| 85 | 760 | T35. Row 35 CorruptArcher | 1. r ← dist; h ← FindHostile(&r, 0) | `0x005F5A20` | ? | ? | ? | 1 |
| 86 | 779 | T35. Row 35 CorruptArcher | After FindHostile every distance test reads r, the hostile's distance ( without one), not the … | – | ? | ? | ? | 1 |
| 87 | 787 | T37. Row 37 SkeletonBow | r ← dist | `0x005F6070` | ? | ? | ? | 1 |
| 88 | 798 | T37. Row 37 SkeletonBow | No skill column is read. | `fn:sub_005DE6D0_MonAiWalkTowardUnit@0x005DE6D0` | ? | ? | ? | 1 |
| 89 | 805 | T61. Row 61 Hireable and state 4 | 1. cls ← U ? U.class : −1; O ← MonsterOwner(U) | `0x005E52D0` | ? | ? | ? | 1 |
| 90 | 839 | T61. Row 61 Hireable and state 4 | HireFight(cls, O, t, seed, ctx): | `fn:sub_005E5050_AiHireFight@0x005E5050` | ? | ? | ? | 1 |
| 91 | 860 | T61. Row 61 Hireable and state 4 | MERCAI_PickSkill(cls, id, t, seed): | `fn:MERCAI_PickSkill@0x005E4D30` | ? | ? | ? | 1 |
| 92 | 887 | T61. Row 61 Hireable and state 4 | Follow(O, U, kind, run, speed, n) = AiHireFollow. Kind 0: from a start direction (UnitDirToPoint … | – | ? | ? | ? | 1 |
| 93 | 894 | T61. Row 61 Hireable and state 4 | The alt and states 5, 6. alt: if UNIT_HasState(U, 12): STATE_Set(U, 12, 0), then MonAiInit(ctl, … | – | ? | ? | ? | 1 |
| 94 | 898 | T61. Row 61 Hireable and state 4 | From the code's own writes v14 is a multiple of 10, so step 4's 17–19 … | – | ? | ? | ? | 1 |
| 95 | 901 | T61. Row 61 Hireable and state 4 | Past the first boundary a consistency check (README H3). | run:2026-11-04-ai-resume-flip | ? | ? | ? | 1 |
| 96 | 906 | T64. Row 64 SkeletonMage | … ← dist; h ← FindHostile(&e, 0) ; e is the frame word it may rewrite | `0x005F96C0` | ? | ? | ? | 1 |
| 97 | 921 | T64. Row 64 SkeletonMage | The walk-stop distance is the low byte of aip2; the compares use the full i16. … | `fn:sub_005DEF80_MonAiWalkToUnitStop@0x005DEF80` | ? | ? | ? | 1 |
| 98 | 928 | T67. Row 67 NecroPet and state 7 | UNIT_CancelEvents(G, U, 2, 0) | `fn:sub_005E4CF0_AiNecroPet@0x005E4CF0` | ? | ? | ? | 1 |
| 99 | 933 | T67. Row 67 NecroPet and state 7 | OwnerBlock: | `fn:sub_005E4830_AiNecroPetMelee@0x005E4830` | ? | ? | ? | 1 |
| 100 | 964 | T67. Row 67 NecroPet and state 7 | AiPetGuard(t, O, melee, ctx, flag, dist). dist ← dist + | `0x00574F40` | ? | ? | ? | 1 |
| 101 | 967 | T67. Row 67 NecroPet and state 7 | AiPetMove, returning 1 when it commanded: kind 0 walks to a point eight subtiles out … | – | ? | ? | ? | 1 |
| 102 | 970 | T67. Row 67 NecroPet and state 7 | Which code sets v14 for a necromancer's pet is not read. | `fn:sub_005E4CF0_AiNecroPet@0x005E4CF0` | ? | ? | ? | 1 |
| 103 | 972 | T67. Row 67 NecroPet and state 7 | Past the first boundary a consistency check (README H3). | run:2026-11-04-ai-resume-flip | ? | ? | ? | 1 |
| 104 | 977 | T89. Row 89 Megademon | n ← 1 | `0x005E0C80` | ? | ? | ? | 1 |
| 105 | 995 | T89. Row 89 Megademon | The skill's level is used as a distance, and aip6 is a cooldown in frames. … | `fn:sub_006439B0_SkillFindByOwner@0x006439B0` | ? | ? | ? | 1 |
| 106 | 1001 | T125. Row 125 BloodLord | if melee: | `0x005E36F0` | ? | ? | ? | 1 |
| 107 | 1014 | Outputs | … a helper of § C, or a return with nothing queued, as its block shows. | `fn:sub_005A7C20_MonSetMode@0x005A7C20` | ? | ? | ? | 1 |
| 108 | 1018 | Worked example | … 50 is false, so the branch is not taken and the seed has stepped once. | `fn:RNG_Step@0x0045C370` | ? | ? | ? | 1 |
| 109 | 1022 | Reimplementation notes | A draw in a failed and. chance(K) short-circuits as written: row 13's second chance(1) is … | `fn:sub_005F1440_AiFallenShaman@0x005F1440` | ? | ? | ? | 1 |
| 110 | 1023 | Reimplementation notes | Row 21's Idle does not return: the walk runs in the same event. | `0x005F29D7` | ? | ? | ? | 1 |
| 111 | 1024 | Reimplementation notes | Row 13's kind-9 bound compares an AI distance with a square. Row 22's bounds are … | `fn:sub_005DCDA0_AiDeadMinionCb@0x005DCDA0` | ? | ? | ? | 1 |
| 112 | 1025 | Reimplementation notes | Row 125 uses the constant mode 5 and no sign test on Skill1. | `0x005E3799` | ? | ? | ? | 1 |
| 113 | 1026 | Reimplementation notes | A leader's stack block carries four words the code does not write (E5), and row … | `0x005F04AA` | ? | ? | ? | 1 |
| 114 | 1027 | Reimplementation notes | Row 34's override type 1 plans type 7 (D2), so Ovr(1, …) is no type-1 … | `fn:sub_005DE190_MonAiPathOverride@0x005DE190` | ? | ? | ? | 1 |

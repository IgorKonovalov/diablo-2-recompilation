# Plan 0066 inventory: path/README

- **Spec:** [path/README](../../specs/path/README.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 80; the *Count* column sums to 80.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 36 | Entry points | Every plan: 68 direct calls in 58 functions, 34 … | `fn:sub_00649970_PathPlan@0x00649970` | ? | ? | ? | 1 |
| 2 | 38 | Entry points | A blocked path is planned again | `fn:sub_00650350_PathReplan@0x00650350` | ? | ? | ? | 1 |
| 3 | 39 | Entry points | The record is created — under | `fn:PATH_DynamicCreate@0x00649D00` | ? | ? | ? | 1 |
| 4 | 40 | Entry points | A mode reset restores the type — PathMoveReset | `0x00648DEC` | ? | ? | ? | 1 |
| 5 | 60 | Runtime state | … creation. Coordinates are subtiles; a point is x / y << 16 in a u32. | `0x00649D17` | ? | ? | ? | 1 |
| 6 | 87 | Runtime state | The context (, on PathPlan's stack, passed in ECX). + is never written. | `0x00649A0A` | ? | ? | ? | 1 |
| 7 | 102 | Constants | point slots — 78 | `0x00649D17` | ? | ? | ? | 1 |
| 8 | 111 | A. Two masks: what a move tests and what a unit writes | A record holds two masks, and they are not interchangeable. | `fn:sub_00648CE0_PathSetCollMask@0x00648CE0` | ? | ? | ? | 1 |
| 9 | 118 | A. Two masks: what a move tests and what a unit writes | player | `fn:PATH_DynamicCreate@0x00649D00` | ? | ? | ? | 1 |
| 10 | 119 | A. Two masks: what a move tests and what a unit writes | monster — PATH_MonTestMask: flying , opendoors , else ; wraith | `fn:PATH_MonTestMask@0x00648480` | ? | ? | ? | 1 |
| 11 | 120 | A. Two masks: what a move tests and what a unit writes | missile — the mark (drlg/collision § F, ); the test | `fn:sub_00648CE0_PathSetCollMask@0x00648CE0` | ? | ? | ? | 1 |
| 12 | 122 | A. Two masks: what a move tests and what a unit writes | Whirlwind, the flight — no zeroing found at the start; the end restores … | `0x005D90AE` | ? | ? | ? | 1 |
| 13 | 123 | A. Two masks: what a move tests and what a unit writes | Leap, the flight — set to 0 , set back at the landing | `fn:sub_005D9D50_SkillSt40Leap@0x005D9D50` | ? | ? | ? | 1 |
| 14 | 124 | A. Two masks: what a move tests and what a unit writes | Jump — no zeroing found at the start; the end restores … | `0x005CBA46` | ? | ? | ? | 1 |
| 15 | 125 | A. Two masks: what a move tests and what a unit writes | packet 's reach test — restored after | `fn:sub_0054CB10_PlrReachTest@0x0054CB10` | ? | ? | ? | 1 |
| 16 | 127 | A. Two masks: what a move tests and what a unit writes | Neither Whirlwind mask holds , or , so no live unit's mark refuses that plan … | `0x005D90B4` | ? | ? | ? | 1 |
| 17 | 128 | A. Two masks: what a move tests and what a unit writes | SizeY is unused by a monster's footprint: UNIT_GetSizeY reads it, no monster footprint uses it, … | `fn:UNIT_GetSizeY@0x006205A0` | ? | ? | ? | 1 |
| 18 | 133 | B. Creation, PathSetType and the setters | B1. PATH_DynamicCreate(…, room, x, y, unit, flag): | `fn:PATH_DynamicCreate@0x00649D00` | ? | ? | ? | 1 |
| 19 | 162 | B. Creation, PathSetType and the setters | PathMoveReset restores the speed from + under flag , then sets type 7 for a … | `0x00648DEC` | ? | ? | ? | 1 |
| 20 | 184 | C. PathPlan | 1. if path = 0: return 0 ; | `0x00649970` | ? | ? | ? | 1 |
| 21 | 185 | C. PathPlan | 2. if path.unit ≠ unit: fatal ; | `0x00649970` | ? | ? | ? | 1 |
| 22 | 202 | C. PathPlan | the call, ; IsBadCodePtr ≠ 0: fatal | `0x00649BAE` | ? | ? | ? | 1 |
| 23 | 203 | C. PathPlan | 19–26: past the import, the tail | `0x00649BA1` | ? | ? | ? | 1 |
| 24 | 215 | C. PathPlan | force is read once, at step 13: it lets a refused town target through and … | `0x005FBFB7` | ? | ? | ? | 1 |
| 25 | 216 | C. PathPlan | The window tests the request's target, before the free step: a target moved by C3 … | `0x00649AC5` | ? | ? | ? | 1 |
| 26 | 231 | C1. The target refresh | … return 1 when path + = 0 ; else PathTargetOffsetX87, an x87 offset not read: | `0x00649950` | ? | ? | ? | 1 |
| 27 | 290 | C4. The replan | unit + /= 1; PathAddByte94(p, −p.iPoint) ; | `0x00650384` | ? | ? | ? | 1 |
| 28 | 296 | C4. The replan | if n = 0: p.type ← 15; n ← PathPlan(p, unit, 0) ; | `0x006503D2` | ? | ? | ? | 1 |
| 29 | 299 | C4. The replan | return n ; | `0x006503E2` | ? | ? | ? | 1 |
| 30 | 302 | C4. The replan | PathReplan writes + without PathSetType, so a re-plan keeps the flags word of the type … | `0x006503AF` | ? | ? | ? | 1 |
| 31 | 303 | C4. The replan | … unchanged. The target revalidation is PathReplan's own code before the call and is not compared: | `0x006503CE` | ? | ? | ? | 1 |
| 32 | 332 | D. The 17 types: planner and draws | 3 — 0 | `0x00679E5A` | ? | ? | ? | 1 |
| 33 | 340 | D. The 17 types: planner and draws | 11 | `0x00679FE7` | ? | ? | ? | 1 |
| 34 | 341 | D. The 17 types: planner and draws | 12 — 0 | `0x00679E79` | ? | ? | ? | 1 |
| 35 | 347 | D. The 17 types: planner and draws | PathPlan and everything around it draw nothing: no and no call to the 19 RNG … | `fn:sub_00649970_PathPlan@0x00649970` | ? | ? | ? | 1 |
| 36 | 348 | D. The 17 types: planner and draws | Under the eight planners 58 functions hold one LCG step, , the random walk's; under … | `0x0067A315` | ? | ? | ? | 1 |
| 37 | 349 | D. The 17 types: planner and draws | SUnitPathCreate's callees after the path (PlrPlaceEventsInit, MonInitMode, the mode set) reach 118 RNG functions: those … | `fn:sub_00554850_SUnitPathCreate@0x00554850` | ? | ? | ? | 1 |
| 38 | 350 | D. The 17 types: planner and draws | Types 2 and 13 are the same plan: 13 differs in the flags word's , … | `0x006503AF` | ? | ? | ? | 1 |
| 39 | 369 | D. The 17 types: planner and draws | … are the same block write. That the write is the block's release or reuse is | `0x00681F4F` | ? | ? | ? | 1 |
| 40 | 370 | D. The 17 types: planner and draws | PATH_CHAIN for classes 225 and 195, short of the floor of 50 each: class 225, … | `0x00681F4F` | ? | ? | ? | 1 |
| 41 | 374 | E. Who asks: the request register | … a do function 14, a monster's last request type, a player's 7 after a reset. | `fn:sub_00649970_PathPlan@0x00649970` | ? | ? | ? | 1 |
| 42 | 389 | E. Who asks: the request register | The player's move: a walk, run or town walk start (PlrModeStartMove, modes 2, 3, 6) … | `fn:sub_0057F090_PlrModeStartMove@0x0057F090` | ? | ? | ? | 1 |
| 43 | 390 | E. Who asks: the request register | The AI's types are 1, 2, 5, 6, 7, 13 and 15; 5 and 6 … | `fn:sub_005A6290_MonPathPlanType@0x005A6290` | ? | ? | ? | 1 |
| 44 | 391 | E. Who asks: the request register | No Missiles column chooses a type: it is a constant in the do function or … | `fn:sub_005C9290_MissCbReseedPathXPlusArg@0x005C9290` | ? | ? | ? | 1 |
| 45 | 398 | F1. The planners take the live grid | The first run's other 842 plans also show 0 mismatches and back nothing here. They … | `0x00649BAE` | ? | ? | ? | 1 |
| 46 | 400 | F1. The planners take the live grid | What the model took from the game: the planner's address, the context and the record … | `0x00649BAE` | ? | ? | ? | 1 |
| 47 | 401 | F1. The planners take the live grid | The tail (the aim and the "every point at the position" refusal) agrees in all … | run:2026-11-04-path | ? | ? | ? | 1 |
| 48 | 411 | F3. The counted oracle | The candidates, chosen after the result, not tested on data they did not see: 8 … | `0x005CAF8E` | ? | ? | ? | 1 |
| 49 | 412 | F3. The counted oracle | What this does not establish: that the grid at a call is a function of … | `0x00649BAE` | ? | ? | ? | 1 |
| 50 | 414 | F3. The counted oracle | So the value-oracle rows of skills/README and skills/missiles retire for the planner and stay for … | `0x00649BAE` | ? | ? | ? | 1 |
| 51 | 422 | F4. Each grid rule at its tag | O1, objects — for the bits and : 0 cells differ over … | `0x00649611` | ? | ? | ? | 1 |
| 52 | 423 | F4. Each grid rule at its tag | T1, the plan's target — a targeted object of size 1 or more: with … | `0x00649B18` | ? | ? | ? | 1 |
| 53 | 425 | F4. Each grid rule at its tag | C2, deadCol 1 — classes 403 and 404, 18 distinct dead | `0x005A65CD` | ? | ? | ? | 1 |
| 54 | 426 | F4. Each grid rule at its tag | C3, re-created dead — 3 distinct units, as drlg/lifecycle § H5 | `0x005A73A6` | ? | ? | ? | 1 |
| 55 | 427 | F4. Each grid rule at its tag | The seventh caller — the call's effect, 35 lines | `0x005CAF8E` | ? | ? | ? | 1 |
| 56 | 428 | F4. Each grid rule at its tag | C4, no clear — The server's 3×3 has no paired clear: the cells … | `0x00649FD8` | ? | ? | ? | 1 |
| 57 | 429 | F4. Each grid rule at its tag | W1, the player after an act change — Unmarked: the first move unmarks and zeroes the room … | `0x0064EFA3` | ? | ? | ? | 1 |
| 58 | 430 | F4. Each grid rule at its tag | L1, a reserved landing — the calls at the three reached sites, 128, 237 … | `0x005CB902` | ? | ? | ? | 1 |
| 59 | 431 | F4. Each grid rule at its tag | The bit — no plan depends on them on these logs; no … | `0x00649BAE` | ? | ? | ? | 1 |
| 60 | 463 | G2. Type 1 | The seven sites that request it: AiPathOverrideSet(1) at AiHireFollow and AiPetMove , three in state … | `0x005E3BCC` | ? | ? | ? | 1 |
| 61 | 464 | G2. Type 1 | Two are a retry: AiHireFollow's and AiPetMove's are reached only when the request before returned … | `0x005E3BA1` | ? | ? | ? | 1 |
| 62 | 468 | G3. The other short types and stages | Type 0: named for a get-hit (ai/0001 § 8), planned where a "current" site holds … | `fn:sub_0067AD00_PathPlanSearch@0x0067AD00` | ? | ? | ? | 1 |
| 63 | 469 | G3. The other short types and stages | Types 3, 11, 12: no server code sets them: no store of an immediate 3, … | `0x0046525A` | ? | ? | ? | 1 |
| 64 | 470 | G3. The other short types and stages | . Of the 22 + store sites, 7 and 6 executed, none storing 3, or … | `0x00679FD0` | ? | ? | ? | 1 |
| 65 | 471 | G3. The other short types and stages | Type 16: planned only from two functions nothing references. | `fn:sub_00663E00_PathPlanType16A@0x00663E00` | ? | ? | ? | 1 |
| 66 | 472 | G3. The other short types and stages | Town-follow is short: attempted in the Rogue Encampment, 313 plans, no hostile monster in the … | `fn:sub_006483A0_PathTargetNotTown@0x006483A0` | ? | ? | ? | 1 |
| 67 | 473 | G3. The other short types and stages | Jump is short: no stock user. No MonStats skill column and no other excel table … | `0x005CB902` | ? | ? | ? | 1 |
| 68 | 478 | G4. Truncation | The earlier probe's 10 of 10 rest on a fraction a breakpoint wrote, so they … | `0x0067A1A1` | ? | ? | ? | 2 |
| 69 | 528 | H. The aim and the facing step | PathPlan's tail makes the same call (C's step 24, past the import). | `0x00649BA1` | ? | ? | ? | 1 |
| 70 | 529 | H. The aim and the facing step | The names are the reverser's, not an observed use: + the facing, + the direction … | `struct:PathRequestFields+0x64` | ? | ? | ? | 1 |
| 71 | 530 | H. The aim and the facing step | PathSetFacing(path, dir) writes dir & to both + and +; a null path writes nothing | `0x006488A6` | ? | ? | ? | 1 |
| 72 | 542 | Outputs | … the facing and step as PathAimNextPoint left them (§ H). Return: the count, or 0. | `0x00649BA1` | ? | ? | ? | 1 |
| 73 | 562 | Reimplementation notes | A planner's grid is the live one after PathPlan's unmarks: a unit doesn't block itself, … | `0x00649B07` | ? | ? | ? | 1 |
| 74 | 563 | Reimplementation notes | PathPlan's tail re-marks the unit even when the free step returned 0 (C's step 22); … | `0x00649BE0` | ? | ? | ? | 1 |
| 75 | 565 | Reimplementation notes | PathReplan changes the type without the flags (C4). | `0x006503AF` | ? | ? | ? | 1 |
| 76 | 567 | Reimplementation notes | is written but in no immediate move mask scanned (F4's C4): on what this spec … | `0x00649FD8` | ? | ? | ? | 1 |
| 77 | 568 | Reimplementation notes | unflatDead changes no grid mark and no move mask: its one direct reader is a … | `0x004648AB` | ? | ? | ? | 1 |
| 78 | 569 | Reimplementation notes | The plan of type 14 reads no grid. The hammer's end at a wall is … | `fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0` | ? | ? | ? | 1 |
| 79 | 580 | Open questions | , F4), and a mask built in a register or read from a table was … | src:d2mods-monstats-guide`'s | ? | ? | ? | 1 |

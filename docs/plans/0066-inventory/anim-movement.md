# Plan 0066 inventory: anim/movement

- **Spec:** [anim/movement](../../specs/anim/movement.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 44; the *Count* column sums to 44.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 38 | Entry points | A player starts running (or is knocked back) | `fn:sub_00620E80_RunVelocityStat@0x00620E80` | a-logs | all4 logs: MSET to 3 then SR with st 67 150 from the run's mode-scoped list | S6b | 1 |
| 2 | 41 | Entry points | A knockback path is planned | `fn:sub_0067A000_PathPlanKnockback@0x0067A000` | a-logs | all4 logs: monster knockback windows' PS0 points (one point, path type 8) | S6b | 1 |
| 3 | 73 | Inputs and oracles | The AI's mode command and its velocity block; the … — taken as given (plans 0052, 0046) | `fn:sub_005A6380_MonModeVelocity@0x005A6380` | a-logs | all4 logs: the 160 Charge steps' path speed against the MulDiv reading; monster SR st 67 after a velocity command | S6b | 1 |
| 4 | 80 | Constants | moving factor floor — 25 | `0x00624128` | c-emu | `UNIT_AnimSetRate`'s moving branch emulated with a factor below 25 (timing's rate-edges family) | S6e | 1 |
| 5 | 92 | A. Speeds | if the unit has no path: return; +0x4C kept, no speed set; no case | – | c-emu | `UNIT_AnimSetRate` emulated on a moving scratch unit with no path | S6e | 1 |
| 6 | 93 | A. Speeds | the floor 25: no case; B_FRW = 150 s / (150 + s), anim/timing J1 | – | c-emu | as row 4 | S6e | 1 |
| 7 | 99 | A. Speeds | A2. RunVelocityStat(class, unit), from UNIT_AnimInit for a player form in mode 3 or 19: | `fn:sub_00620E80_RunVelocityStat@0x00620E80` | a-logs | all4 logs: SR st 67 150 at run starts and 100 after the next mode change; the CharStats ratio | S6b | 1 |
| 8 | 111 | A. Speeds | The floor 25 is reached by no logged call (P1b-14; not played in Phase 2 … | – | c-emu | as row 4, with `PathSetSpeed`'s +0x38 write in the same emulation (the RN path base: a tally over all4) | S6e | 1 |
| 9 | 115 | A. Speeds | The animation base vbase: a player's in run, otherwise; a monster's MonStats + | – | a-logs | all4 logs: monster SR r in RN against +0x38, else +0x36; the player's 0x65 and 0xD5 | S6b | 1 |
| 10 | 118 | A. Speeds | The list is made at the run's start and dropped at the next UNIT_SetMode to | run:2026-10-27-anim | a-logs | all4 logs: SR st 67 across a run and the next mode; the wolf and bear runs (sp-dru-form) | S6b | 1 |
| 11 | 122 | A. Speeds | A monster's stat 67 starts at 75; the champion, possessed, fast and fanatic mods add … | – | a-logs | all4 logs: monster SR st 67 (75, the mods by mf, the 19 changed by a command) | S6b | 1 |
| 12 | 131 | A. Speeds | b ← MonStats[i].BaseId (out of range → i) ; | – | c | full-table check of the MonStats BaseId range (if none is out of range, a guard stock data never fails) | S6c | 1 |
| 13 | 132 | A. Speeds | the fallback record's 256 when no WL record | – | c-emu | emulate `MonStatsSpeeds` over the stock MonStats rows, compared with the tools/anim_rates.py model | S6e | 1 |
| 14 | 144 | A. Speeds | A class with no walk record (the classic 9A traps, compellingorb and the E9 rows) … | – | c-emu | as row 13 (the classes with no WL record and the row order) | S6e | 1 |
| 15 | 147 | A. Speeds | A Velocity-0 classic class in S1 (a classic monster's S1–S4 take the moving branch, anim/timing … | – | a-logs | all4 logs: monster SR in S1 of Velocity-0 classic classes (path speed 0, r 192 at X 75) | S6b | 1 |
| 16 | 151 | A. Speeds | Other writers of a unit's path speed: the knockback and moving branches, MonInitMode, and five | – | c | exhaustive xref scan with a second tool of `PathSetSpeed` callers and path +0x7C writers | S6c | 1 |
| 17 | 155 | A. Speeds | Charge's start sets MulDiv(RunVelocity << 8, max(stat 67, 50) + Param1, 100), Param1 150 | – | b | sp-pal-chg under a slow (stat 67 ≤ 50 by chill or Decrepify): a new pilot step; the ps-p-m18 lines | H6c | 1 |
| 18 | 182 | B. The per-frame step | if k ≤ 0: k ← 0x400; the server passes 0x400 | – | c | xref scan with a second tool of `PathStep`'s callers: one server caller, k 0x400 | S6c | 1 |
| 19 | 198 | B. The per-frame step | PathStep has one server caller, UnitMoveStep with k = , so the axis step is … | – | c | xref scan with a second tool of `PathStep` and `PathSetAccel` callers | S6c | 1 |
| 20 | 202 | B. The per-frame step | The direction (+, +) is a g_PathDirTable row, axes swapped and signed by octant, toward … | – | c | r2 dump of `g_PathDirTable`: every row's norm² within the stated bounds | S6c | 1 |
| 21 | 208 | B. The per-frame step | The snap (not for path type 4): with m = max(/stepX/, /stepY/) and the next … | – | a-logs | all4 logs: step-point windows: frames per point against ⌈65536 d / step⌉ | S6b | 1 |
| 22 | 212 | B. The per-frame step | The collision walk. When the step changes the subtile, PathStepCollide halves both axes together | – | c-emu | emulate `PathStepCollide` with 0x0064FF90 an observed boundary (+0x1D4, +0x90, the 10th crossing); tools/anim_moves.py model | S6e | 1 |
| 23 | 221 | B. The per-frame step | The end. With no point left, PathStop snaps to the subtile centre, clears flag , … | – | a-logs | all4 path ends (centre snap, flag); the target revalidation's replans in the path runs (run:2026-11-04-path) | S6b | 1 |
| 24 | 225 | B. The per-frame step | Wrap bound. d · s (s = 16 v) fits 32 bits up to v … | – | c-emu | `PathVelocityStep` emulated at v ≥ 32 768 (the wrap) | S6e | 1 |
| 25 | 231 | C. Who steps | UnitMoveStep has 11 call sites, each in a mode's every-frame function: the player's skill frame | – | c | xref scan with a second tool of `UnitMoveStep`'s 11 call sites | S6c | 1 |
| 26 | 237 | C. Who steps | Player walk and run, and monster WL and RN, end when UnitMoveStep returns 2; a … | – | a-logs | all4 logs: the last PS0 of a window then MSET to neutral (players, monster WL and RN) | S6b | 1 |
| 27 | 246 | D. The run drain | if the unit's room is a town: return 1 ; | – | a-logs | all4 logs: DR0 lines in town rooms (sessions start in town): return 1, stamina unchanged | S6b | 1 |
| 28 | 247 | D. The run drain | if the unit has no inventory: return 0 ; | – | d-none | a guard stock data never fails: a player always has an inventory | – | 1 |
| 29 | 259 | D. The run drain | The town and no-inventory returns are read from the code. | `0x0057F290` | a-logs | as row 27 (the no-inventory guard: row 28) | S6b | 1 |
| 30 | 260 | D. The run drain | The turn to a walk. On 0, PlrModeMoveFrame restarts the move (PlrModeStartMove), which turns a … | – | a-logs | op-run2–6 logs: pair each MSET 3 to 2 with its own EF by line order and phase, then the next PS0 | S6b | 1 |
| 31 | 269 | E. Knockback | E1. PathPlanKnockback (path type 8): | `fn:sub_0067A000_PathPlanKnockback@0x0067A000` | a-logs | all4 logs: monster knockback windows: the first PS0 point against E1 from the unit and attacker positions | S6b | 1 |
| 32 | 277 | E. Knockback | Start. A player: COMBAT_GetHit with result bit commands mode 19 at the attacker; | – | a-logs | all4 logs: GH result bit 0x8 on monsters against MSET to 13 or 3 by class | S6b | 1 |
| 33 | 284 | E. Knockback | A player's length: the path's, 3 frames for n 3 on an axis and 5 … | – | a-run | the op-br Hell hunt for Blood Raven (class 267): player mode-19 lengths, anim.gdb | H6c | 1 |
| 34 | 293 | E. Knockback | From + = 0 that is max(1, ⌈L / r⌉ − 1) calls of its … | – | a-logs | all4 logs: knockback windows: advances from +0x44 0 to KBE against the formula | S6b | 1 |
| 35 | 298 | F. The slowing states | Slowing reaches movement only through stat 67 and the FR/W bonus in X, floored at … | – | a-logs | all4 logs: slowed windows: a speed change mid-window taken at the next step | S6b | 1 |
| 36 | 305 | F. The slowing states | Slows Target sets stats 68 and 69 only (attack and default rate), capped at 50 … | – | a-logs | all4 logs: win-slow-p and monster slow windows: SR st 68 and 69 under the state, st 67 unchanged, the caps | S6b | 1 |
| 37 | 313 | G. Draws | None. The step, the snap, the collision walk, the speeds, the knockback planner and the … | – | c | the kept call-graph scan (`rngcallgraph` plus r2) from `PathStep` and `RunStaminaDrain` | S6c | 1 |
| 38 | 325 | Outputs | The mode end on arrival (2 from UnitMoveStep), which anim/timing § I turns | – | a-logs | as row 26 | S6b | 1 |
| 39 | 330 | Worked example | A player's walk (CharStats WalkVelocity 6, no FR/W, stat 67 100): pbase = 6 << … | – | a-logs | all4 logs: walk speed 1 536 and step 24 576 on axis rows; frames per 3 subtiles | S6b | 1 |
| 40 | 338 | Reimplementation notes | The run is a stat, not a base. A player's run speed comes from the … | – | a-logs | as rows 7 and 11 | S6b | 1 |
| 41 | 341 | Reimplementation notes | Two bases. The path speed (WalkVelocity or Velocity << 8) moves the unit; the animation … | – | a-logs | all4 logs: SR r and path speed share X at every moving call | S6b | 1 |
| 42 | 343 | Reimplementation notes | The snap is exact. A step that would pass the point lands on its subtile … | – | a-logs | as row 21 (steps landing on the centre) | S6b | 1 |
| 43 | 345 | Reimplementation notes | The tenth crossing is unchecked. A very fast step can pass a blocked subtile after … | – | c-emu | as row 22 | S6e | 1 |
| 44 | 374 | Open questions | The run's turn to a walk at 0 stamina (D2), reached in Phase 2 part … | – | a-logs | as row 30 | S6b | 1 |

**Totals by class:** a-logs 25, a-run 1, b 1, c 7, c-emu 9, d-none 1 (sum 44).

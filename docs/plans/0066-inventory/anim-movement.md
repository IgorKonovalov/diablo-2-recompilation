# Plan 0066 inventory: anim/movement

- **Spec:** [anim/movement](../../specs/anim/movement.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 44; the *Count* column sums to 44.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 38 | Entry points | A player starts running (or is knocked back) | `fn:sub_00620E80_RunVelocityStat@0x00620E80` | ? | ? | ? | 1 |
| 2 | 41 | Entry points | A knockback path is planned | `fn:sub_0067A000_PathPlanKnockback@0x0067A000` | ? | ? | ? | 1 |
| 3 | 73 | Inputs and oracles | The AI's mode command and its velocity block; the … — taken as given (plans 0052, 0046) | `fn:sub_005A6380_MonModeVelocity@0x005A6380` | ? | ? | ? | 1 |
| 4 | 80 | Constants | moving factor floor — 25 | `0x00624128` | ? | ? | ? | 1 |
| 5 | 92 | A. Speeds | if the unit has no path: return ; + kept, no speed set; | – | ? | ? | ? | 1 |
| 6 | 93 | A. Speeds | the floor 25: no case; B_FRW = 150 s / (150 + s), anim/timing J1 | – | ? | ? | ? | 1 |
| 7 | 99 | A. Speeds | A2. RunVelocityStat(class, unit), from UNIT_AnimInit for a player form in mode 3 or 19: | `fn:sub_00620E80_RunVelocityStat@0x00620E80` | ? | ? | ? | 1 |
| 8 | 111 | A. Speeds | The floor 25 is reached by no logged call (P1b-14; not played in Phase 2 … | – | ? | ? | ? | 1 |
| 9 | 115 | A. Speeds | The animation base vbase: a player's in run, otherwise; a monster's MonStats + | – | ? | ? | ? | 1 |
| 10 | 118 | A. Speeds | The list is made at the run's start and dropped at the next UNIT_SetMode to | run:2026-10-27-anim | ? | ? | ? | 1 |
| 11 | 122 | A. Speeds | A monster's stat 67 starts at 75; the champion, possessed, fast and fanatic mods add … | – | ? | ? | ? | 1 |
| 12 | 131 | A. Speeds | b ← MonStats[i].BaseId (out of range → i) ; | – | ? | ? | ? | 1 |
| 13 | 132 | A. Speeds | the fallback record's 256 when no WL record | – | ? | ? | ? | 1 |
| 14 | 144 | A. Speeds | A class with no walk record (the classic 9A traps, compellingorb and the E9 rows) … | – | ? | ? | ? | 1 |
| 15 | 147 | A. Speeds | A Velocity-0 classic class in S1 (a classic monster's S1–S4 take the moving branch, anim/timing … | – | ? | ? | ? | 1 |
| 16 | 151 | A. Speeds | Other writers of a unit's path speed: the knockback and moving branches, MonInitMode, and five | – | ? | ? | ? | 1 |
| 17 | 155 | A. Speeds | Charge's start sets MulDiv(RunVelocity << 8, max(stat 67, 50) + Param1, 100), Param1 150 | – | ? | ? | ? | 1 |
| 18 | 182 | B. The per-frame step | if k ≤ 0: k ← ; | – | ? | ? | ? | 1 |
| 19 | 198 | B. The per-frame step | PathStep has one server caller, UnitMoveStep with k = , so the axis step is … | – | ? | ? | ? | 1 |
| 20 | 202 | B. The per-frame step | The direction (+, +) is a g_PathDirTable row, axes swapped and signed by octant, toward … | – | ? | ? | ? | 1 |
| 21 | 208 | B. The per-frame step | The snap (not for path type 4): with m = max(/stepX/, /stepY/) and the next … | – | ? | ? | ? | 1 |
| 22 | 212 | B. The per-frame step | The collision walk. When the step changes the subtile, PathStepCollide halves both axes together | – | ? | ? | ? | 1 |
| 23 | 221 | B. The per-frame step | The end. With no point left, PathStop snaps to the subtile centre, clears flag , … | – | ? | ? | ? | 1 |
| 24 | 225 | B. The per-frame step | Wrap bound. d · s (s = 16 v) fits 32 bits up to v … | – | ? | ? | ? | 1 |
| 25 | 231 | C. Who steps | UnitMoveStep has 11 call sites, each in a mode's every-frame function: the player's skill frame | – | ? | ? | ? | 1 |
| 26 | 237 | C. Who steps | Player walk and run, and monster WL and RN, end when UnitMoveStep returns 2; a … | – | ? | ? | ? | 1 |
| 27 | 246 | D. The run drain | if the unit's room is a town: return 1 ; | – | ? | ? | ? | 1 |
| 28 | 247 | D. The run drain | if the unit has no inventory: return 0 ; | – | ? | ? | ? | 1 |
| 29 | 259 | D. The run drain | The town and no-inventory returns are read from the code. | `0x0057F290` | ? | ? | ? | 1 |
| 30 | 260 | D. The run drain | The turn to a walk. On 0, PlrModeMoveFrame restarts the move (PlrModeStartMove), which turns a … | – | ? | ? | ? | 1 |
| 31 | 269 | E. Knockback | E1. PathPlanKnockback (path type 8): | `fn:sub_0067A000_PathPlanKnockback@0x0067A000` | ? | ? | ? | 1 |
| 32 | 277 | E. Knockback | Start. A player: COMBAT_GetHit with result bit commands mode 19 at the attacker; | – | ? | ? | ? | 1 |
| 33 | 284 | E. Knockback | A player's length: the path's, 3 frames for n 3 on an axis and 5 … | – | ? | ? | ? | 1 |
| 34 | 293 | E. Knockback | From + = 0 that is max(1, ⌈L / r⌉ − 1) calls of its … | – | ? | ? | ? | 1 |
| 35 | 298 | F. The slowing states | Slowing reaches movement only through stat 67 and the FR/W bonus in X, floored at … | – | ? | ? | ? | 1 |
| 36 | 305 | F. The slowing states | Slows Target sets stats 68 and 69 only (attack and default rate), capped at 50 … | – | ? | ? | ? | 1 |
| 37 | 313 | G. Draws | None. The step, the snap, the collision walk, the speeds, the knockback planner and the … | – | ? | ? | ? | 1 |
| 38 | 325 | Outputs | The mode end on arrival (2 from UnitMoveStep), which anim/timing § I turns | – | ? | ? | ? | 1 |
| 39 | 330 | Worked example | A player's walk (CharStats WalkVelocity 6, no FR/W, stat 67 100): pbase = 6 << … | – | ? | ? | ? | 1 |
| 40 | 338 | Reimplementation notes | The run is a stat, not a base. A player's run speed comes from the … | – | ? | ? | ? | 1 |
| 41 | 341 | Reimplementation notes | Two bases. The path speed (WalkVelocity or Velocity << 8) moves the unit; the animation … | – | ? | ? | ? | 1 |
| 42 | 343 | Reimplementation notes | The snap is exact. A step that would pass the point lands on its subtile … | – | ? | ? | ? | 1 |
| 43 | 345 | Reimplementation notes | The tenth crossing is unchecked. A very fast step can pass a blocked subtile after … | – | ? | ? | ? | 1 |
| 44 | 374 | Open questions | The run's turn to a walk at 0 stamina (D2), reached in Phase 2 part … | – | ? | ? | ? | 1 |

# Plan 0066 inventory: path/search

- **Spec:** [path/search](../../specs/path/search.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 36; the *Count* column sums to 36.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 84 | Runtime state | … in the game the line's and the walk's inputs differ only in where they start. | `0x00679726` | c-emu | each planner emulated (tools/path_emu1.py..path_emu3.py): `+0x48` and `+0x50` unchanged on return | S7e | 1 |
| 2 | 97 | Constants | spiral — (the structure agrees under the emulator's rounding, control swap, … | run:2026-11-03-path-emu-3 | a-logs | path.gdb logs (run:2026-11-04-path, -path-2): every type-14 plan's points against the spiral's structure (step, angle, 77 points) | S7c | 1 |
| 3 | 130 | A2. Directions | g_DirOctant holds 0..7 only, so the assert of a third direction 255 cannot fire from … | `data:g_DirOctant@0x006F1518` | c | `g_DirOctant` read whole with a second tool: values 0..7 only | S7f | 1 |
| 4 | 175 | A5. The first line: PathFirstLine | pt.x = 0: assert ; pt.y = 0: assert ; | `0x00679AA5` | d-none | an assert stock callers never reach | – | 1 |
| 5 | 240 | B. The greedy planner: types 2 and 13 | Types 2 and 13 are one plan (overview D4). | `data:g_PathTypeFlags@0x006EB690` | c | as path/README row 38: the flags word's readers by a second tool | S7a | 1 |
| 6 | 268 | C. The + walk: types 5 and 6 | With + = 2 or −2 the three directions are the row's turned by 90°: … | `data:g_PathTypeParam98@0x006EB648` | c-emu | the 0x98 walk emulated with `+0x98` = 2 and −2 | S7e | 1 |
| 7 | 287 | D. Greedy-near: type 7 | 324 is 18 subtiles on an axis: (18, 0) passes, (18, 1) at 325 doesn't. … | `fn:sub_0057F090_PlrModeStartMove@0x0057F090` | a-logs | path.gdb logs (run:2026-11-04-path, -path-2): players' type-7 plans with targets 18 subtiles off and their fall to type 1 | S7c | 1 |
| 8 | 309 | E. The knockback planner: type 8 | A unit standing on its target has m = 0, and pt is the start: … | `0x0067A0B6` | c-emu | the greedy planner emulated with the unit on its target: `m` = 0, return 0 | S7e | 1 |
| 9 | 399 | G. Type 1: best-first over a pool of 200 | A node is expanded once and has 8 neighbours, so the code's silent drop of … | `0x0067B28E` | d-none | a ninth link no node of 8 neighbours reaches | – | 1 |
| 10 | 400 | G. Type 1: best-first over a pool of 200 | The model's propagation stack reached 3 on the first run's 270 plans and 23 on … | `0x0067B28E` | b | a new path.gdb field: the propagation stack's peak per plan | H7c | 1 |
| 11 | 421 | H. Type 15: a line with two wall followers | 1. unit neither player nor monster: assert ; | `0x0067C2D0` | d-none | an assert stock callers never reach | – | 1 |
| 12 | 452 | H. Type 15: a line with two wall followers | lim4 ≤ a.cnt: assert ; | `0x0067C07F` | d-none | an assert not reached under stock limits | – | 1 |
| 13 | 494 | H. Type 15: a line with two wall followers | A follower count of 0 reads as a point: last is then the stop word, … | `0x0067C0E2` | c-emu | the follower planner emulated with a follower count of 0 | S7e | 1 |
| 14 | 495 | H. Type 15: a line with two wall followers | lim above 80 is reached only with bytes no writer gives (lim50, 4 emulated cases). … | `0x0067C045` | c | a second-tool scan of the writers of `+0x90` and `+0x91` (creation's 14, the cap at 77) | S7a | 1 |
| 15 | 528 | I. The random walk: type 10 | A straight step has chance 10/32, each side 11/32. | `0x0067A258` | a-logs | path.gdb logs (run:2026-11-04-path, -path-2): the type-10 plans' steps tallied straight against side (10/32, 11/32) | S7c | 1 |
| 16 | 530 | I. The random walk: type 10 | At limit 77 the walk reaches 76 subtiles on an axis, so its u16 adds … | `0x0067A352` | c-emu | the random walk emulated near coordinate 0 and 65 535 | S7e | 1 |
| 17 | 535 | J. The spiral: type 14 | PathPlanSpiral(path) → 77: | `fn:sub_0067A140_PathPlanSpiral@0x0067A140` | a-logs | as row 2 | S7c | 1 |
| 18 | 551 | J. The spiral: type 14 | g_SineTable and R go on the x87 stack as f32, so the product has at … | `0x0067A196` | d-none | an x87 product and `FISTP` no run can separate from the exact one | – | 1 |
| 19 | 552 | J. The spiral: type 14 | No draw, no grid, neither + nor +. 94 iterations at the kept start, at … | `0x0067A21D` | a-logs | path.gdb logs (run:2026-11-04-path, -path-2): type-14 plans have no PLG and an unchanged seed; the iteration count at the kept start | S7c | 1 |
| 20 | 553 | J. The spiral: type 14 | The emulator's x87 can't test this: the p-code FISTP ignores the rounding field. So the … | `0x0067A1A1` | d-none | a note on the emulator's x87 limit | – | 1 |
| 21 | 554 | J. The spiral: type 14 | The hammer at a wall: this plan reads no grid; the end at a wall … | `fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0` | a-logs | as path/README row 78 | S7c | 1 |
| 22 | 561 | K. The straight planner and type 4 | type 10: PathPlanRandomWalk(path, &unit.seed); flag set; return + ; | `0x00649763` | c-emu | `PathPlanStraight` emulated with `PathPlanRandomWalk` as a boundary: flag 0x20 and the return | S7e | 1 |
| 23 | 562 | K. The straight planner and type 4 | type 14: PathPlanSpiral(path); flag set; return + ; | `0x00649763` | c-emu | as row 22 with `PathPlanSpiral` | S7e | 1 |
| 24 | 563 | K. The straight planner and type 4 | else: fatal ; | `0x006497C8` | d-none | a fatal default no stock type reaches | – | 1 |
| 25 | 616 | L1. The rectangle | Rooms on one row with equal rectangles get the margin only across, since r.w differs. … | `0x0067AD97` | c-emu | the search's room rectangles emulated with equal rooms on one row (tools/path_emu2.py) | S7e | 1 |
| 26 | 652 | L2. The run | Bounds: at most 51 passes (h0 ≥ 2, b1C ≤ 255), each at most 10 … | `0x0067ACB0` | c | the two loop bounds read with a second tool (objdump) | S7f | 1 |
| 27 | 714 | L3. The walk and the fan | The first try keeps the parent's direction in rows 0, 1, 2, 6 and 7: … | `data:g_PathSearchTurnRows@0x006F17D8` | c | `g_PathSearchTurnRows` read whole with a second tool | S7f | 1 |
| 28 | 729 | L4. Type 16's draws | Type 16's reach: two unreferenced functions. | `fn:sub_00663E00_PathPlanType16A@0x00663E00` | c | as path/README row 65: r2 `axt`, no reference | S7a | 1 |
| 29 | 734 | L5. The limits | The node store is out of reach under PathPlan's window: /dx/, /dy/ ≤ 100 gives … | `fn:sub_00649970_PathPlan@0x00649970` | d-none | a bound the window keeps out of reach | – | 1 |
| 30 | 736 | L5. The limits | No single stock room overruns: the largest is 60 × 60 subtiles, a same-room rectangle … | `0x0067AABC` | c | full-table check over every stock level's rooms (tools/room_extent.py, Levels) | S7f | 1 |
| 31 | 737 | L5. The limits | g and f are u16 read as i16; under the store g ≤ 2 697, … | `0x0067A88B` | d-none | a wrap the store's bound keeps out of reach | – | 1 |
| 32 | 753 | M. The client-only slots: types 3, 11, 12 | Type 12's total can be 2 × limit, past 78 from limit 40, though only … | `0x00679E8A` | c-emu | type 12 emulated at limit 40: the total past 78 (client only) | S7e | 1 |
| 33 | 763 | N. Points against the 78 slots | Type 15 — maxret 56; game 29 | `0x0067BFFD` | c-emu | the type-15 planner emulated at limit 77: at most 76 | S7e | 1 |
| 34 | 768 | N. Points against the 78 slots | Limit 77 is the most any writer gives: PathSetByte90 caps at 77, creation gives 73 … | `0x00648E7D` | c | exhaustive second-tool scan of the writers of `+0x90`: `PathSetByte90` caps at 77 | S7a | 1 |
| 35 | 769 | N. Points against the 78 slots | PathPlan has no test of a count above 78: a planner returning one would overrun … | `0x00649BA1` | c | a second-tool read of `PathPlan`'s tail: no count test; the planners' bounds as rows 33 and 34 | S7f | 1 |
| 36 | 773 | Outputs | … seed under types 10 and 16. PathPlan's tail then acts on them: overview § C. | `0x00649BA1` | a-logs | path.gdb logs (run:2026-11-04-path, -path-2): PLX lines' points, return and side writes against the output description | S7c | 1 |

**Totals by class:** a-logs 7, b 1, c 9, c-emu 10, d-none 9 (sum 36).

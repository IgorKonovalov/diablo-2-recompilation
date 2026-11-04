# 0006 — The hold-out of the grid rules: the kept batch of run:2026-11-04-path-2

> **Subsystem:** path/search
> **Question:** do the rules of [path/0005](0005-grid-rules.md) (O1, C1..C3, T1, W1, L1, fitted on run:2026-11-04-path's logs) predict the live grid on logs taken after they were frozen, and what do rev 5's new lines answer?
> **Date:** 2026-11-04   **Plan:** 0054 (Phase 2, the kept batch, `lane/p54c`)   **Status:** for review

Run record: [experiments.md](experiments.md#run2026-11-04-path-2). The rules and `tools/path.py` (sha256 `e2844c166519`, checked before and after the check and the grid run) were frozen before the first kept launch; nothing was fitted to this batch. Counts are `tools/path.py check` and `grid` on the 25 kept logs (`workspace/logs/path/2026-11-04-path-2-check.txt` `d93dad5e`, `2026-11-04-path-2-grid.txt` `56e8a1fb`, `manifest-path-2.sha256` there; tool hashes in `2026-11-04-path-2-tools.sha256`).

## Answer (summary)

- [C] **The hold-out does not hold.** `code+w1+l1` leaves **11 wrong plans of 15 663** (the plans with a built map), not 0: 2 of type 2, 3 of type 13, 6 of type 15, every one with the bit `0x1000` alone sufficient. The earlier passes on the same logs: frozen rules 472, O1+C1..C3+T1 72, with W1 62. The rules explain 461 of the 472 and leave 11; the prediction is wrong on the one bit the rules put on the player's own cell. No rule was changed. (`2026-11-04-path-2-grid.txt`, fn:sub_00649970_PathPlan@0x00649970)
- [C] **Boundary of "0 mismatches".** `RESULT OK: 0 mismatches over 20 671 reproduced plans` holds with the planners given the game's own live grids (`PLG`, taken at the planner call); that is a different claim from the 11 above, which compare the predicted grid (built map plus the unit list plus the rules) with the live one. A plan is compared on its return, the first point words and the exit seed ([path/0004](0004-per-event-reproduction.md) § 1). Types 0, 1, 3, 11, 12, 16 have no plan here either. (`2026-11-04-path-2-check.txt` `RESULT`, 0x00649970)
- [C] **`COR` holds the copy table:** 0 `UNLISTED CALLER`, 0 `AGAINST THE TABLE` over 4 981 lines: 0x005A65D9 `srv` arg 1 1 527, 0x005CAF8E `srv` arg 1 35, 0x004B05E3 `cli` arg 0 1 505, 0x004B0A05 `cli` arg 0 1 914. These are lines, not deaths. The other three callers of the seven (0x00461018, 0x004C8963, 0x0057F367) did not fire. (`COR`, 0x00649F70)
- [C] **C1 on the server, at the call:** all 1 527 lines at 0x005A65D9 hold the full 3×3 of `0x8000` in the 5×5 after the call, centre included (616 exactly that, 911 with further corpse cells of neighbours); none holds only the plus. The client's 3 419 lines at the two client sites all hold the plus (1 467 and 1 862 without a full 3×3, 38 and 52 with, by a neighbour). The shape after the call is the callee's, [C] at the observed return; that it is C1's reading of the call's effect rather than another writer's is [I]. (`COR` `after`, 0x005A65D9, 0x004B05E3, 0x004B0A05)
- [C] **Spiral rounding, answered: truncation.** 233 natural type-14 plans (no probe, no write), 43 804 stored products: all equal to truncation, 25 630 equal to rounding, **18 174 separate the two: 18 174 truncate, 0 round**. `HOLDS`. Scope: the integer the game stored after each `fistp` at 0x0067A1AF and 0x0067A1E0 on natural Blessed Hammer plans, read-only; the spiral model's rounding in [path/0004](0004-per-event-reproduction.md) § 6 becomes `[C]` for those inputs. (`SPX`, 0x0067A1AF, 0x0067A1E0, fn:sub_0067A240_PathPlanRandomWalk@0x0067A240)
- [I] **W1 holds on the hold-out where it was seen, thinly:** act changed: 7 of 7 unmarked at the first other unit's plan that sees the unmoved player (9 arrivals not seen by any plan); same act: 3 of 3 marked (6 not seen). The floors (10 each) are not met. (`W1`, `ARRIVAL` lines, 0x0064EFA3)
- [C] **L1: three of four mark sites reached, each as read.** 0x005D9123 (Whirlwind) 128 lines, 0x005D9EF8 (Leap) 237, 0x005DA5D5 (Leap Attack) 109, all unit type 0 and mask `0x80`; 474 `L1U` releases. Jump (0x005CB902): short, no stock user: no MonStats skill column and no other excel table holds `Jump` (it occurs in `skills.txt` only). The `code+w1+l1` pass is the 11 above. (`L1M`, `L1U`, tbl:Skills.txt)
- [I] **Seed watchpoints, short of the floor:** class 225: 216 type-10 plans, 22 watched, all block writes (0x00681F4F `rep stos` 20, 0x0057CAE6 `rep movs` 2) with the high dword unchanged; class 195: 32 plans, 3 watched, the same. 0 of 25 drew again. The floor was 50 watched each. (`SEEDW`, 0x00681F4F, 0x0057CAE6)
- [C] **Type-1 request sites: 0 of 7 reached** (`T1S`, all `srv 0 cli 0`: 0x005E3BCC, 0x005E4300, 0x005E5DD9, 0x005E5EE7, 0x005E5F40, 0x005CD484, 0x005CBC44); type 14: 233 stock plans (floor 30 met). (run:2026-11-04-path-2)

## Where the 11 are

All 11 differ in `0x1000` only, at the decisive cell: 6 are the player in mode 18 (mask 128) at its own cell with the model `0x1080`/`0x1180`/`0x9080` and the live `0x0080`/`0x0180`/`0x8000`: the model holds the player's `0x1000` where the game holds only the pattern. 2 are in the River of Flame at one cell (7793, 6124), model `0x1100`, live `0x0100`, the player at mode 18 mask 128 and 0 at the two plans. 3 are type 15 plans in the River with the player in mode 7 or 1, model `0x1100`, live `0x8000`. None is at the unit cap. In the earlier logs the 15 were the reverse (the live `0x1080` the model lacked), so the sign of the difference changed with the logger and the data: a finding, not a rule. Not fitted. (`REST` lines of `2026-11-04-path-2-grid.txt`)

Residuals of the code pass in cells (not plans): `0x0200` 92 597 (no plan depends: unchanged from the fitted logs), `0x8000` 26 034, `0x0100` 29 841, `0x1000` 854; the `0x0400` and `0x0800` cells are gone (the cap raised, O1 by the byte). C4 (the server's 3×3 outlasting the corpse) is the likely source of the `0x8000` cells and is not modelled: `[I]`. (0x00649FD8, run:2026-11-04-path-2)

## Floors

| Floor | Result |
|---|---|
| W1, 10 in-act arrivals and 10 act changes seen by another unit's plan | short: 3 of 9 and 7 of 16 seen; the waypoint-hop stages (12 act changes, 14 in-act) failed in development (below) |
| `COR` srv at 0x005A65D9 ≥ 50; cli at 0x004B05E3 and 0x004B0A05 ≥ 50 | met: 1 527; 1 505, 1 914 |
| `deadCol` 1 at ≥ 5 per side | server met: 18 distinct dead (403: 8, 404: 10), each with no `0x8000` cell and the live mark kept (C2); 273 not met; client: short, `deadCol` 1 skips the call so no line is the evidence, and the logger has no break on the client's tests 0x004B05DB, 0x004B09FB; no `COR` line for class 273, 403 or 404 beside 3 419 lines of other classes (a control) |
| re-created dead's shape | 3 distinct units with the 3×3, mask `0x8000`, pattern 5, as C3 and drlg/lifecycle § H5 |
| L1 four sites | 3 reached, Jump named (no stock user) |
| `SPX` `HOLDS` | met, truncation |
| `PATH_CHAIN` 50 each, 225 and 195 | short: 22 and 3 watched (216 and 32 plans) |
| type 14 at 30 | met: 233 |
| `T1S` per site | all 7 at 0; not reached by the necromancer's pets (`k5-necro`) or the sorceress's mercenary (`k5-sor-jail`) |
| type 1 stages: Countess state 13, Diablo's run, a far-behind mercenary | not staged |
| town-follow | attempted (`k5-town-a1`, Rogue Encampment, 313 plans): no hostile monster in the town room in these logs; short, the geometry stays [drlg/0009 § 11.2](../drlg/0009-room-lifecycle.md#112-the-town-follow-static-remainder-lanerbs4) |
| Phase 1b | not run: no community pathing source is registered in `docs/sources.md` with a claim these logs compare (the plan allows this) |

## Hop stages, development only

`wpchain` could not take a second waypoint in the Act IV logs: it read the waypoint from `OBJP` lines, which `path.gdb` does not log; `tools/d2pilot.py` now falls back to the type-2 entries of the newest `PLC` unit lists. In the River of Flame the nearest listed waypoint object lay at (7800, 5919), 32 and 23 subtiles from the player's logged position, off the window, so the list never opened; the cause (a player far from the arrival waypoint, or a wrong entry) was not read. The two hop cases stay development logs.

## Open questions

- `[L]` The 11: the player's `0x1000` at mode 18 and the River cell; the logger holds no marked-state field, so the model's player mark cannot be read from the game.
- `[L]` W1 beyond 7 and 3: waypoint hops need the waypoint position from the game.
- `[L]` Who creates class 195 (a stage that kills lightning-enchanted monsters) and the type-1 sites' stages.

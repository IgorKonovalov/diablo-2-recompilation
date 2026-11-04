# 0005 — The rules of the planner's grid: objects, corpses, the plan's target, reserved landings

> **Subsystem:** path/search
> **Question:** which code rules turn the built map plus the unit list into the live cells a planner reads, so that the 361 of 9 773 plans the tie's grid got wrong ([path/0004](0004-per-event-reproduction.md) § 7) are explained?
> **Date:** 2026-11-04   **Plan:** 0054 (Phase 2, steps 2 of the `lane/p54` review's order; `lane/p54b`)   **Status:** open: checkpoint, not yet for review (steps 1 and 3 remain, plan log)

No game in this lane. Static read of the pinned image; the counts are `tools/path.py grid` on the kept logs of run:2026-11-04-path (`workspace/logs/p54b/grid.txt`, manifest `manifest.sha256` there).
**Which is which.** Every rule below was read from the code. The counts on the kept logs are not its evidence: those logs suggested where to read, so they are fitted, and the next kept batch is each rule's hold-out. So all are `[I]`, except the corpse's disagreement with drlg/collision, where the code alone settles which copy a call serves, still `[I]` until the per-call lines of that batch.

## Answer (summary)

- [I] **O1, objects.** An object's rectangle is in the grid when `HasCollision[mode]` of its class is set: `SUnitPathCreate` and `UnitRelocate` test the byte before marking (0x0055494C, 0x00554BB5), `UNIT_CollUnmark` tests it through 0x006219C0 (0x00649611), and each operate handler that changes the state calls `UNIT_CollMarkRect` or `UNIT_CollUnmarkRect` itself; the mode change does not. The tie marked every object. Classes 374 and every waypoint (`SubClass` bit 6, e.g. 398) have `HasCollision` 0 in all modes, so bit 6 is not the cause: its only collision-related readers are the preset scan and 0x0066ADCE, and neither touches a mark. (fn:UNIT_CollMarkRect@0x00620A70, fn:sub_00554850_SUnitPathCreate@0x00554850, tbl:Objects.txt:HasCollision0, tbl:Objects.txt:SubClass)
- [I] **C1..C3, a dead monster on the server.** `MonDeathEvent` sets mode 0 and calls 0x005A6520, which tests `deadCol` (`edx` = 0x13, `+0x06` bit 3, at 0x005A65CD) and, when it is 0, calls `UnitCorpseColl(unit, 1)` at 0x005A65D9: the live mark off and a 3×3 of `0x8000` (0x00649FD8), mask and pattern untouched. C1: `deadCol` 0, the 3×3, from mode 0 on, not only at mode 12. C2: `deadCol` 1, the live mark stays. C3: a monster created dead or relocated dead is the plus, pattern 5, mask `0x8000` (0x00555492–0x005554D8, 0x00554B78–0x00554B8E). (fn:sub_005A6FF0_MonDeathEvent@0x005A6FF0, fn:sub_00649F70_UnitCorpseColl@0x00649F70, tbl:MonStats2.txt:deadCol)
- [I] **The plus of drlg/collision is the client's.** The tests 0x004B05DB and 0x004B09FB and their `UnitCorpseColl(unit, 0)` calls (0x004B05E3, 0x004B0A05) lie in client code, so the dumps of run:2026-10-14-collision (`DC`, 408 deaths, hooked there and not filtered to the server) hold for the client's units. The two rows are about different copies; neither reading is wrong for its copy. (0x004B05DB, 0x004B09FB, run:2026-10-14-collision)
- [I] **C4, the server's 3×3 has no clear.** `COLL_RectOrWH` at 0x00649FD8 has no paired clear of `0x8000`: `UNIT_CollUnmark` clears the record's pattern and mask (still `0x100`), and `UnitReviveColl` returns at once unless the mask is `0x8000` (0x00649FF0). So the cells outlast the corpse until the grid is rebuilt. Not modelled by the tie, whose list holds only the units present: 15 339 cells of `0x8000` differ, and `0x8000` is in no move mask read so far. (fn:sub_00649FF0_UnitReviveColl@0x00649FF0, 0x00649FD8)
- [I] **T1, the plan's target.** Under path flag `0x800` `PathPlan` unmarks the target whatever its type (0x00649B1A–0x00649B25); the tie excluded only players and monsters. A targeted object's `HasCollision` state decides through `UNIT_CollUnmark`. (fn:sub_00649970_PathPlan@0x00649970)
- [I] **L1, a reserved landing.** Four skill starts mark the landing point before the flight, with `COLL_PatternMark` and the unit's pattern: Whirlwind 0x005D9123 (`0x80` for a player, else `0x100`), Leap 0x005D9EF8 (`0x80`), Leap Attack 0x005DA5D5 (`0x80`), Jump 0x005CB902 (`0x100`). The flight sets the path mask to 0 (0x005D9F9C); landing unmarks the reserved cells (0x005DA1F3, 0x005DA269, 0x005D94E8, 0x005CBA3B) and sets the mask back. Leap's constant `0x80` holds for a monster too, whose landing unmarks `0x100`: read, not run. Not in the tie: the point is in the skill record `+0x18`/`+0x1C`, which rev 4 does not log. (fn:sub_005D9D50_SkillSt40Leap@0x005D9D50, fn:sub_005DA120_LeapAttackLand@0x005DA120, fn:sub_005D9460_WhirlwindEnd@0x005D9460)
- [L] **W1, a player unmarked after a waypoint arrival** (under *Open questions*): the logs show none of its cells until its first plan re-marks it; 0x00650910 not read.

## The 361 re-computed

`tools/path.py grid`, all 9 773 plans with a built map; the frozen lines reproduce the review's figures, so the attribution is the same computation. (`workspace/logs/p54b/grid.txt`, run:2026-11-04-path)

| Rules | Wrong plans | By type | Bit alone sufficient | Rooms exact | `0x400` cells |
|---|---:|---|---|---:|---:|
| frozen, own marks | 361 | 7: 260, 13: 71, 15: 23, 8: 7 | `0x400` 328, `0x1000` 18, `0x800` 8, both 7 | 67 080 | 81 325 |
| frozen, corpse reading | 361 | the same | the same | 72 557 | 81 325 |
| O1, C1..C3, T1 | **24** | 7: 6, 13: 10, 15: 8 | `0x1000` 24 | 82 470 | 2 205 |

- [I] **The 24 left, all one bit, the player's centre:** 15 with the player in mode 18, the shape L1 predicts and the tie does not yet model; 9 with the player just arrived and unmarked (`[L]` W1). None is at the unit cap. They name a candidate each, not a tested rule. (`REST` lines, 0x005D9D50)
- [I] **`0x400`, `0x800`, `0x2`, `0x4` left are mostly a logging truncation:** all 2 205 cells of `0x400` lie in the 221 plans at the 120-unit cap, where the list is cut before its objects (`units_in`, `out[:CAP_UNITS]`). That is rev 5's unit cap. (run:2026-11-04-path)
- [I] **`0x200`, 80 768 cells, no effect on a plan:** no type-4 entry is logged in any session, also under `PATH_ITEMS`, and the move masks read hold no `0x200`. (run:2026-11-04-path)

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005A6520` | `sub_005A6520_MonDeathCorpseMark` | server death: the `deadCol` test and `UnitCorpseColl(unit, 1)` | I |
| `0x006219C0` | `sub_006219C0_UnitCollActive` | an object's `HasCollision[mode]`; 1 for other types | I |
| `0x00649F70` | `sub_00649F70_UnitCorpseColl` | seven callers, table below | I |

## `UnitCorpseColl`'s seven callers

| Call | Argument | Function | Copy, by the code's module and neighbours | Tag |
|---|---:|---|---|---|
| 0x00461018 | 0 | client room change | client | I |
| 0x004B05E3 | 0 | client monster state, after the `deadCol` test | client | I |
| 0x004B0A05 | 0 | client monster state, after the `deadCol` test | client | I |
| 0x004C8963 | 0 | client, after the test at 0x00464820 | client | I |
| 0x0057F367 | 1 | server player death | server | I |
| 0x005A65D9 | 1 | server monster death, after the `deadCol` test | server | I |
| 0x005CAF8E | 1 | skill start 43 | server | I |

Order at a server monster's death: `SUNIT_SetMode(0)`, then 0x005A6520, then the drop (0x005A7019 onward). (fn:sub_005A6FF0_MonDeathEvent@0x005A6FF0)

## Data touched

`tbl:Objects.txt:HasCollision0`, `tbl:MonStats2.txt:deadCol`; `struct:DynPathColl+0x48`, `struct:DynPathColl+0x4C`.

## Open questions

- `[L]` W1: which code leaves a player unmarked after a waypoint arrival; read 0x00650910 (`PathTargetRoomXY`'s callee) and the caller of `UnitTeleport`.
- `[L]` Whether L1 accounts for the 15: rev 5's break line on the four mark sites gives the point; the kept logs do not hold it.
- `[L]` The kept batch's per-call lines at the seven callers are the hold-out of C1..C3 and of the copy table (corpse entry's part 2).

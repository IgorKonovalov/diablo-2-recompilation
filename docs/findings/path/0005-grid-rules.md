# 0005 — The rules of the planner's grid: objects, corpses, the plan's target, reserved landings

> **Subsystem:** path/search
> **Question:** which code rules turn the built map plus the unit list into the live cells a planner reads, so that the 361 of 9 773 plans the tie's grid got wrong ([path/0004](0004-per-event-reproduction.md) § 7) are explained?
> **Date:** 2026-11-04   **Plan:** 0054 (Phase 2, steps 2 of the `lane/p54` review's order; `lane/p54b`)   **Status:** for review (steps 1, 2, 3 of the review's order; the kept batch's steps 4 and 5 are the next lane's, plan log)

No game in this lane. Static read of the pinned image; the counts are `tools/path.py check` on the kept logs of run:2026-11-04-path (`workspace/logs/p54b/check-review.txt`, `48603989`, after the review's corrections of C3 and T1; manifest `manifest.sha256` there; `check.txt`, `d8211db0`, is the lane's before them, and `grid.txt` the checkpoint's, before W1).
**Which is which.** Every rule below was read from the code. The counts on the kept logs are not its evidence: those logs suggested where to read, so they are fitted, and the next kept batch is each rule's hold-out. So all are `[I]`, with one exception raised at the review: the copy the old corpse lines were read on is `[C]`, from a log that was not fitted to this question (below). The rule on the server's copy stays `[I]` until the per-call lines of that batch.

## Answer (summary)

- [C] **O1, objects** (raised 2026-11-04, `lane/p54c` review: the object bits, [path/0006](0006-holdout.md)). An object's rectangle is in the grid when `HasCollision[mode]` of its class is set: `SUnitPathCreate` and `UnitRelocate` test the byte before marking (0x0055494C, 0x00554BB5), `UNIT_CollUnmark` tests it through 0x006219C0 (0x00649611), and each operate handler that changes the state calls `UNIT_CollMarkRect` or `UNIT_CollUnmarkRect` itself; the mode change does not. The tie marked every object. Classes 374 and every waypoint (`SubClass` bit 6, e.g. 398) have `HasCollision` 0 in all modes, so bit 6 is not the cause: its only collision-related readers are the preset scan and 0x0066ADCE, and neither touches a mark. (fn:UNIT_CollMarkRect@0x00620A70, fn:sub_00554850_SUnitPathCreate@0x00554850, tbl:Objects.txt:HasCollision0, tbl:Objects.txt:SubClass)
- [C] **C1..C3, a dead monster on the server** (raised 2026-11-04, `lane/p54c` review, on the hold-out's `COR` lines: [path/0006](0006-holdout.md); C2 for classes 403 and 404). `MonDeathEvent` sets mode 0 and calls 0x005A6520, which tests `deadCol` (`edx` = 0x13, `+0x06` bit 3, at 0x005A65CD) and, when it is 0, calls `UnitCorpseColl(unit, 1)` at 0x005A65D9: the live mark off and a 3×3 of `0x8000` (0x00649FD8), mask and pattern untouched. C1: `deadCol` 0, the 3×3, from mode 0 on, not only at mode 12. C2: `deadCol` 1, the live mark stays. C3: a monster re-created dead takes the corpse call and then `SUnitCreate`'s re-mark, so its cells are the 3×3 and its record pattern 5, mask `0x8000`, the sequence [drlg/lifecycle § H5](../../specs/drlg/lifecycle.md#h5-the-grid-marks-of-a-re-created-monster) holds `[C]` on 134 line-for-line cases (run:2026-10-21-chain2). A monster relocated dead takes only the plus at the new place (0x00554B78–0x00554B8E), its old cells left. The re-mark at 0x0055546F–0x005554A3 is the monster's; 0x005554B3–0x005554D8 is the same for a player created in mode 0 or 17. 0x005A6520's second caller is 0x005A73A6, the start of mode 12, which calls it unless the unit is already in mode 0. (fn:sub_005A6FF0_MonDeathEvent@0x005A6FF0, fn:sub_00649F70_UnitCorpseColl@0x00649F70, tbl:MonStats2.txt:deadCol)
- [C] **The plus of drlg/collision is the client's; the reviewed row is a scope error, not a false observation.** The spec scopes itself to the server's grid (its L42), so the row read as written is wrong for an ordinary server death; what was observed was true of the client. The tests 0x004B05DB and 0x004B09FB and their `UnitCorpseColl(unit, 0)` calls (0x004B05E3, 0x004B0A05) lie in client code, and the logs agree: the game holds each room rectangle twice, 357 of the 559 (level, rectangle) pairs of run:2026-10-14-collision's seven logs having two DRLG rooms, of which exactly one ever has an `SN` line (the server's pass entry 0x0054EC90), and never both. All 408 `DC` lines sit on the copy with no `SN` whose other copy has one. Second source: that split, which the logs were not taken to show. It says which copy the lines were read on, not each call's side, which is `COR`'s. The 408 are lines of the two tests over 202 unit addresses, most dying once and hitting both, not 408 deaths. The server's reading of the same event is C1. (`tools/corpse_copy.py`, `workspace/logs/p54b/corpse-copy.txt`, 0x004B05DB, 0x004B09FB, run:2026-10-14-collision)
- [I] **C4, the server's 3×3 has no clear.** `COLL_RectOrWH` at 0x00649FD8 has no paired clear of `0x8000`: `UNIT_CollUnmark` clears the record's pattern and mask (still `0x100`), and `UnitReviveColl`, which acts only when the mask is `0x8000` (0x00649FF0), has only the client callers 0x004AEEDC and 0x004AFFA8. So the cells outlast the corpse until the grid is rebuilt. Not modelled by the tie, whose list holds only the units present: 13 342 cells of `0x8000` differ, and `0x8000` is in no move mask read so far. (fn:sub_00649FF0_UnitReviveColl@0x00649FF0, 0x00649FD8)
- [C] **T1, the plan's target** (raised 2026-11-04, `lane/p54c` review, a targeted object of size 1 or more: [path/0006](0006-holdout.md)). Under path flag `0x800` `PathPlan` unmarks a target whose `UNIT_GetSizeX` is not 0, whatever its type (0x00649B10–0x00649B25), and re-marks it at the tail (0x00649BD7) when the unmark returned non-zero; the tie excluded only players and monsters. Every target of the kept logs has a size of 1 or more, so the size test is read, not run. A targeted object's `HasCollision` state decides through `UNIT_CollUnmark`. (fn:sub_00649970_PathPlan@0x00649970)
- [I] **L1, a reserved landing.** Four skill starts mark the landing point before the flight, with `COLL_PatternMark` and the unit's pattern: Whirlwind 0x005D9123 (`0x80` for a player, else `0x100`), Leap 0x005D9EF8 (`0x80`), Leap Attack 0x005DA5D5 (`0x80`), Jump 0x005CB902 (`0x100`). Leap's flight sets the path mask to 0 (0x005D9F9C); no such call was found in the starts of Whirlwind or Jump, whose ends restore it (0x005D94F2, 0x005CBA46). Landing unmarks the reserved cells (0x005DA1F3, 0x005DA269, 0x005D94E8, 0x005CBA3B) and sets the mask back. Leap's constant `0x80` holds for a monster too, whose landing unmarks `0x100`: read, not run. Not in the tie: the point is in the skill record `+0x18`/`+0x1C`, which rev 4 does not log. (fn:sub_005D9D50_SkillSt40Leap@0x005D9D50, fn:sub_005DA120_LeapAttackLand@0x005DA120, fn:sub_005D9460_WhirlwindEnd@0x005D9460)
- [I] **W1, the player after an arrival in another act: no mark.** `PlayerChangeAct` moves the player twice through the wrapper `sub_00650BE0_PathTargetRoomXY`, whose one call is `sub_00650910_PathMoveWithMark`: to room 0 at (0, 0) (0x0053ADEA), then to the arrival (0x0053AE19). The first call unmarks at the old place (the `x, y = 0` branch, `COLL_PatternUnmark`, 0x006509E5) and its room word goes to 0 (flag 1 at 0x00650A18, `PathRoomUpdate` stores `+0x1C` at 0x0064FB6D). That store needs path flag `0x40000` clear: with it set, 0x0064FB9F returns before the room is touched and the second move would mark. No player's plan of the kept logs has it (0 of 1 486; 3 492 missiles do). The second reaches `sub_0064EFA0_COLL_PatternMoveAcross` with that old room, whose `test ecx, ecx` at 0x0064EFA3 returns before both the unmark and the `COLL_PatternMark` (0x0064EFCA). So the room and the position are set and the cells hold no mark. The player stays so until a later move through 0x00650910, whose old room is now set, or the tail of a plan that reached a planner (`UNIT_CollMark`, 0x00649BE0). Nothing else in `PlayerChangeAct` after the second move marks the player, by a walk of direct calls to depth 3 from its nine callees: the two paths found, both under 0x005754B0, are the pet's mask below and `MonSetMode` through `PetUnitRelease` (0x005A7CB1). Indirect calls are not followed. (`workspace/logs/p54b/reach.txt`, `tools/path_reach.py`) (fn:sub_0053ACC0_PlayerChangeAct@0x0053ACC0, fn:sub_00650910_PathMoveWithMark@0x00650910, fn:sub_0064EFA0_COLL_PatternMoveAcross@0x0064EFA0)
- [I] **A level change inside an act keeps the mark.** `PlayerChangeLevel` takes the act branch only when the acts differ (0x0053AF35); otherwise it calls `UnitTeleport` (0x0053AF97), whose single move (0x00554F5C, the same wrapper) has a non-zero old room: unmark there, mark here. Waypoints are not the rule's cause, the act change is. (fn:sub_0053AEC0_PlayerChangeLevel@0x0053AEC0, fn:sub_00554EA0_UnitTeleport@0x00554EA0)
- [I] **A pet's route** has the same two moves when its act differs (0x00574CF2, 0x00574D05, at `sub_00574CC0_PetMoveWithOwner`), then `PATH_SetMarkMask(path, 0x100)` at 0x00574D80, which marks, when 0x0063EA40 returns 0. That callee is unfollowed; the tie shows no pet's cell missing at these arrivals, which does not separate the branch. (fn:sub_00574CC0_PetMoveWithOwner@0x00574CC0, fn:PATH_SetMarkMask@0x00648C30)

## The 361 re-computed

`tools/path.py grid`, all 9 773 plans with a built map; the frozen lines reproduce the review's figures, so the attribution is the same computation. (`workspace/logs/p54b/check-review.txt`, run:2026-11-04-path) The rules were read and these counts then measured, W1 after its 9 were seen in the 24; the rows are fitted. C3 changed at the review, after the 15, from the code and drlg/lifecycle § H5: the rule for a record at pattern 5 went from the plus to the 3×3, which moved no wrong plan, took 1 997 cells of `0x8000` and 77 rooms out of the differences. T1's size test moved nothing.

| Rules | Wrong plans | By type | Bit alone sufficient | Rooms exact | `0x400` cells |
|---|---:|---|---|---:|---:|
| frozen, own marks | 361 | 7: 260, 13: 71, 15: 23, 8: 7 | `0x400` 328, `0x1000` 18, `0x800` 8, both 7 | 67 080 | 81 325 |
| frozen, corpse reading | 361 | the same | the same | 72 557 | 81 325 |
| O1, C1..C3, T1 | 24 | 7: 6, 13: 10, 15: 8 | `0x1000` 24 | 82 547 | 2 205 |
| the same and W1 | **15** | 13: 7, 15: 8 | `0x1000` 15 | 82 576 | 2 205 |

- [I] **W1 takes the 9 of the 24 whose player had just arrived,** by the rule above applied in `player_arrivals` (from a level change whose act differs, until the player moves or plans). (`code rules with W1`, 0x0064EFA3)
- [I] **W1 against the arrivals, fitted:** the player's 20 level changes in the 21 sessions; at the first other unit's plan that sees it unmoved, its centre lacks `0x1000` in **9 of 9** act changes and holds it in **2 of 2** arrivals inside an act (`k-sor-river`, `k-sor-river-2`, level 103 to 107); no plan saw the other 9. Two is a thin control, and the logs suggested the reading: the next batch is the hold-out. (`W1` and `ARRIVAL` lines, run:2026-11-04-path)
- [I] **The 15 left, all one bit, all in the two Barbarian sessions with the player in mode 18:** the decisive cell holds a `0x1080` the model lacks, a pattern's centre at `0x80`, up to 8 cells from the player's logged position, in 10 of them with the player's mask 0. That is the shape L1 predicts, which the tie does not model because rev 4 does not log the point. None is at the unit cap. A candidate, not a tested rule. (`REST` lines, 0x005D9D50)
- [I] **`0x400`, `0x800`, `0x2`, `0x4` left are mostly a logging truncation:** all 2 205 cells of `0x400` lie in the 221 plans at the 120-unit cap, where the list is cut before its objects (`units_in`, `out[:CAP_UNITS]`). That is rev 5's unit cap. (run:2026-11-04-path)
- [I] **`0x200`, 80 768 cells, no plan depends on them on these logs, and their source is not logged:** with every differing cell fed back, 9 758 of the 9 773 plans still match, and in the 15 others the attribution finds `0x1000`, not `0x200`, sufficient (`grid_report`). So the tie stays inexact here. No type-4 entry is logged in any session, also under `PATH_ITEMS`. The move masks read hold no `0x200`; the spawn mask `0x3F11` does, so this says nothing about a spawn test. (`check-review.txt`, run:2026-11-04-path)

## Tools

- [I] **The check holds the review's sections.** `tools/path.py check` now prints what `tools/path_review.py` printed, numbered as it was, and that tool is retired. The figures of this paragraph are the lane's `check.txt`; the review's rerun of the lane's tool gave it byte for byte, and `check-review.txt` differs from it only in the C3 cell counts. Sections 6 and 12 are `grid_report`. On the same logs the output before `UNMODELLED` differs from the kept check (`8f6951c3`) in the watchpoint's label and the two new `first plans per level` lines, and the review sections from `review.txt` (`93f9098e`) in sections 6 and 12, which moved, the wording of 9, 11 and 16 with their figures the same, and the added rev 5 sections, empty on these logs. `RESULT` is unchanged: 13 893 plans, 0 mismatches. `mix` and `tie` print the older part only. (`workspace/logs/p54b/check.txt`, run:2026-11-04-path)
- [I] **The block write is labelled.** A seed watchpoint's line that is not the LCG step now reads `block write rep stos 00681f4f` (or `rep movs` at 0x00682A1A, 0x0057CAE6) when its writer is listed and the high dword did not move, else `other writer <pc>`. The 6 control lines read `control: block write rep stos 00681f4f 6`, the 70 keep their label. (`CHAINED DRAWS`, 0x00681F4F)
- [I] **The tie's first plans per level:** 410 plans over the 21 sessions, beside the per-game 10. Own marks only: 3 576 rooms, 2 614 exact. (`TIE`, run:2026-11-04-path)

## Logger rev 5 (`tools/gdb/path.py`): read-only, not yet run

No game ran it. `tools/test_path.py`'s `Logger` class runs the file on a fake `gdb` whose memory fails the test on a write, and the source holds no `write_memory` (review-fixes rule 17, ADR-0003). `tools/test_path.py`: 30 tests. The read-only test covers this file: `path.gdb` also sources `tools/gdb/pilot.py`, which holds no `write_memory` either.

| What | How | Answers |
|---|---|---|
| `SPX` | breaks 0x0067A1AF and 0x0067A1E0, each right after `fistp qword [ebp-0x20]`; the low dword per iteration, joined to its plan by `k` | the rounding, read-only: `check` compares each with truncation and rounding from the image's table and says `HOLDS` only when all separating products truncate and none rounds |
| probe removed | `PATH_SPIRAL_PROBE`, `spiral_probe`, `spiral_sim`, the `probe` field; also from `tools/path_sessions.py`'s three stages | the review's ruling on the write |
| `BRK` counted | a count `c` per (function, side), printing the first 20 hits and each power of two, as `S3C`; no cap | a control now covers its window, within a factor of 2 of its last hit |
| object entries | `HasCollision[mode]` as `u[13]`, the byte `+0x120 + mode` (0x006219D3); `object_marked` reads it first | O1 from the game's own byte |
| unit cap | `PATH_CAP_UNITS` 400 for 120; objects listed first, `PLC` gains `ucut` and `ucap` | the 2 205 `0x400` cells of the 221 cut plans |
| `T1S` | the 7 type-1 request sites, counted: 0x005E3BCC, 0x005E4300, 0x005E5DD9, 0x005E5EE7, 0x005E5F40, 0x005CD484, 0x005CBC44 | site reached, or no plan |
| `L1M`, `L1U` | the 4 `COLL_PatternMark` calls of L1 and the 4 `COLL_PatternUnmark` calls at the landing, with their arguments, capped by `PATH_CAP_LINES` (300) per site | the reserved point, for the 15: `grid` adds a `code+w1+l1` pass on a log that holds them, already coded, so the batch is its hold-out |
| `COR` | `UnitCorpseColl` at entry and return: the call's address, unit, side, argument, the 5 × 5 after; capped per site | the copy table and C1..C3; a caller outside the table prints as `UNLISTED CALLER` |

- [I] **Marked state:** no field for it was read in the path record, so rev 5 logs none and the rule stands: the mark's presence is computed from O1, C1..C4, T1, L1, W1. (fn:UNIT_CollMark@0x00649400)
- [I] **The units at the seven sites:** `esi` at the five `AiPathOverrideSet` calls (from `[ebp+0x8]` at 0x005E3938, 0x005E3EA8; `[esi+0x14]` the monster data at the other three), `[esp]`'s `+0x30` at the two `PathSetType` calls. (0x005E3BCC, 0x005E5DC2, 0x005CD484)

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005A6520` | `sub_005A6520_MonDeathCorpseMark` | server death: the `deadCol` test and `UnitCorpseColl(unit, 1)` | C ([path/0006](0006-holdout.md)) |
| `0x006219C0` | `sub_006219C0_UnitCollActive` | an object's `HasCollision[mode]`; 1 for other types | I |
| `0x00649F70` | `sub_00649F70_UnitCorpseColl` | seven callers, table below | C ([path/0006](0006-holdout.md)) |
| `0x00650910` | `sub_00650910_PathMoveWithMark` | a path's move with its mark: `x, y` 0 unmarks; a missile by size; else across rooms | I |
| `0x0064EFA0` | `sub_0064EFA0_COLL_PatternMoveAcross` | unmark there, mark here; both skipped when the old room is 0 | I |
| `0x00574CC0` | `sub_00574CC0_PetMoveWithOwner` | a pet's move, the same two calls across an act | I |

## `UnitCorpseColl`'s seven callers

| Call | Argument | Function | Copy, by the code's module and neighbours | Tag |
|---|---:|---|---|---|
| 0x00461018 | 0 | client room change | client | I |
| 0x004B05E3 | 0 | client monster state, after the `deadCol` test | client | C |
| 0x004B0A05 | 0 | client monster state, after the `deadCol` test | client | C |
| 0x004C8963 | 0 | client, after the test at 0x00464820 | client | I |
| 0x0057F367 | 1 | server player death | server | I |
| 0x005A65D9 | 1 | server monster death, after the `deadCol` test | server | C |
| 0x005CAF8E | 1 | skill start 43 (MaggotEgg), class 194, the unit in mode 14 | server | C |

Order at a server monster's death: `SUNIT_SetMode(0)`, then 0x005A6520 (called at 0x005A7019), then the drop (`MonDeathDrop`, called at 0x005A7027; corrected 2026-11-04, `lane/scol` review, which read "0x005A7019 onward"). (fn:sub_005A6FF0_MonDeathEvent@0x005A6FF0, fn:sub_005A6830_MonDeathDrop@0x005A6830) The two client `C` rows are by `tools/corpse_copy.py`; the two server rows by run:2026-11-04-path-2's `COR` lines ([path/0006](0006-holdout.md)). 0x005A65D9 includes the callers 0x005A7019 and 0x005A73A6, the second met by run:2026-10-21-chain2's dead re-creations.

## Data touched

`tbl:Objects.txt:HasCollision0`, `tbl:MonStats2.txt:deadCol`; `struct:DynPathColl+0x48`, `struct:DynPathColl+0x4C`.

## Open questions

- `[L]` W1 beyond the hold-out's 7 and 3, short of its floors ([path/0006](0006-holdout.md)).
- `[L]` What sets the `0x200` cells: no logged unit does.

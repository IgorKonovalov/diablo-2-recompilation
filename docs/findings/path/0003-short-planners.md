# 0003 — The short planners: greedy, greedy-near, knockback, one point, type 1, type 15, random walk, spiral, the client-only slots, and missiles H1

> **Subsystem:** path/search
> **Question:** what do the planners other than the search compute from a `PathPlanCtx` (types 2, 5, 6, 13, 7, 8, 9, 1, 15, with 10 and 14 from the path itself), what do they read and write, how many points can each return against the record's 78 slots, which draws do they make, which of the missile callback's three path calls steps the seed and why 20 and 38, what do the client slots 3, 11, 12 do, and does any `+0x3C` store outside the path module set 3, 11 or 12?
> **Date:** 2026-11-03 (run), 2026-11-04 (filed)   **Plan:** 0054 (Phase 1, batches P1.3a and P1.3b)   **Status:** for review (`lane/r54c`)

Static reading of the pinned `Game.exe` with objdump (`p3-short-a.asm`, `p3-short-b.asm`, `p3-type1-15.asm`, `p3-648ad0.asm`, `p3-trig.asm`) and Ghidra decompiles as a reading
aid (project copy `workspace/ghidra-r54c`; `p3-dec15.c`), `RngCallGraph` (`p3-rngcg.txt`), the kept commands of `tools/path_emu3.py` (`bounds`, `stock`, `h1log`, `scan3c`) and emulation
under ADR-0015/ADR-0021 (§ 13, run:2026-11-03-path-emu-3, which started at 23:50 and ended at 00:00 the next day). Kept outputs are under `workspace/logs/r54c/` (`manifest.sha256`); the
emulation under `emu/` (its own manifest), the development runs under `emu/dev-1/`, `dev-2/`, `dev-3/` (their own manifests).

## Answer (summary)

| Type | Planner | Shape | Draws | Most points (78 slots) | Evidence |
|---:|---|---|---|---|---|
| 2, 13 | `PathPlanGreedy`, `+0x98` = 0 | one line from the position; else a walk of at most `ctx.limit` steps, the first free of 3 directions | none | `ctx.limit + 1`: **78 at limit 77**, every slot used | [C] `greedy`, `gbound`, run:2026-11-03-path-emu-3 |
| 5, 6 | the same, `+0x98` = 2, −2 | no line; the walk from the start with `+0x98` added to the 3 directions | none | `ctx.limit` | [C] `g98`, run:2026-11-03-path-emu-3 |
| 7 | `PathPlanGreedyNear` | greedy; `PathPlanType1` when it stops short and `dx² + dy² ≤ 324` | none | greedy's or type 1's | [C] `near`, run:2026-11-03-path-emu-3 |
| 8 | `PathPlanKnockback` | one point, `+0x90 / 2 + 1` away from the target unit, cut by a line | none | 1 | [C] `knock`, run:2026-11-03-path-emu-3 |
| 9 | `PathPlanOnePoint` | one point, the target cut by a line | none | 1 | [C] `onept`, run:2026-11-03-path-emu-3 |
| 1 | `PathPlanType1` | best-first over a 200-node pool; the node nearest the target when it stops | none | 77 kept; 78 returns 0 | [C] `t1real`, `t1syn`, `t1stair`, run:2026-11-03-path-emu-3 |
| 15 | `PathPlanType15` | a Bresenham line, two wall followers at each block | none | at most `lim − 1` = 76 ([I] bound), 56 reached | [C] `t15real`, `t15syn`, `t15stair`, run:2026-11-03-path-emu-3 |
| 10 | `PathPlanRandomWalk` | `+0x91 >> 1` steps of 2 subtiles from the position; no grid read | **`+0x91 >> 1` on the seed passed** | `(+0x91 >> 1) + 1` = 39 at 77 | [C] `rwalk`, `h1`, run:2026-11-03-path-emu-3; 654 game creations, § 10 |
| 14 | `PathPlanSpiral` | 77 points of a growing spiral; no grid read | none | 77, always | [I]: x87 (§ 9), 0x0067A140 |
| 3 | 0x00679E50 | `+0x24 = 0`, then greedy | none | as greedy | [C] `client`, run:2026-11-03-path-emu-3; no server code sets it, [I] (§ 12) |
| 11 | 0x00679FD0 | the target cut by the line in `+0x9C`; always 1 | none | 1 | [C] `client`, run:2026-11-03-path-emu-3; no server code sets it, [I] (§ 12) |
| 12 | 0x00679E60 | the walk at −4, appended at −2, or at +2 when −2 added nothing | none | `2 × limit`, **past 78 from limit 40** ([I]: cases ran to limit 38 only) | [C] the map, `client`, run:2026-11-03-path-emu-3; the bound [I]; no server code sets it, [I] (§ 12) |

(the planners: fn:sub_00679C80_PathPlanGreedy@0x00679C80, fn:sub_00679ED0_PathPlanGreedyNear@0x00679ED0, fn:sub_0067A000_PathPlanKnockback@0x0067A000, fn:sub_00679F70_PathPlanOnePoint@0x00679F70, fn:sub_0067B850_PathPlanType1@0x0067B850, fn:sub_0067C2D0_PathPlanType15@0x0067C2D0, fn:sub_0067A240_PathPlanRandomWalk@0x0067A240, fn:sub_0067A140_PathPlanSpiral@0x0067A140)

- [C] **Missiles H1, answered: `PathPlan` steps the seed, through the random walk, `+0x91 >> 1` times.** `PathSetType` and `PathSetByte90` step nothing: at `PathPlan`'s entry the seed is still the Init's (family `h1obs`, 100 cases, boundary 0x00649970). **20** is Missiles `Range` 40 (`firestormmaker`) `>> 1`. **38** is `Range` 98 (`lightunique`), capped at 77 by the callback, `>> 1`. The same holds in the game's own logs: **654 of 654 creations** of run:2026-10-25-skills, run:2026-10-27-skills and run:2026-10-30-skills-catalogue, with the exit seed predicted from the Init and the logged range: 442 class 458, 176 class 195, and 36 class 408 under `0x005AC040` (`Range` 20, the 10 steps of skills/0003 § 17). (`p3-h1log.txt`, `p3-stock.txt`, fn:sub_005C9290_MissCbReseedPathXPlusArg@0x005C9290, fn:sub_005AC040_MissCbReseedPathX@0x005AC040, tbl:Missiles.txt:Range)
- [C] **Draws:** in every family but `rwalk`, `h1` the unit's seed `+0x20` is undeclared and no traced access touches it, so these maps do not read it. (run:2026-11-03-path-emu-3)
- [I] **The graph agrees:** 58 functions under the eight planners with the fatal entries stopped, no indirect call, one LCG step, 0x0067A315. Slots 3, 11 and 12 have no Ghidra function, so they are not roots; their only calls are 0x00679C80, 0x00679B30 and 0x00679A60, which the graph holds. (`p3-rngcg.txt`, 0x00679E5A, 0x00679E79, 0x00679FE7)
- [I] **"No server code sets 3, 11 or 12" holds on the wider scan, with a named remainder** (§ 12): no store of an immediate 3, 0xB or 0xC to `[reg+0x3C]` anywhere in `.text`, by objdump and by a raw byte scan; the one register store with a base read from a unit's `+0x2C` is the client's 0x0046525A. 18 server register stores have a base the scan does not resolve. (`p3-scan3c.txt`, 0x0046525A)
- [I] **The spiral could not be emulated to a claim:** the p-code `FISTP` ignores the control word's rounding field. 47 cases written to separate them match rounding and none match truncation, while the code sets truncation (§ 9). Its 90 cases are in the run's 4 330 but count for nothing about the game (4 240 without them); only `spiralobs` (30) is `[C]`. (0x0067A1A1, 0x0067A1CA, run:2026-11-03-path-emu-3)

## Leads used

No community source was compared (Phase 1b's). Used to locate code only: [ai/0001 § 8](../ai/0001-machinery.md#8-the-path-request), [path/0001](0001-pathplan-register.md), [path/0002 § 1](0002-search.md#1-the-first-item-types-1-15-and-greedy-nears-switch), [skills/0003 § 9](../skills/0003-handlers.md) and [PathTypes](../../tables/PathTypes.md).

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00679C80` | `sub_00679C80_PathPlanGreedy` | types 2, 5, 6, 13 (§ 1) | I |
| `0x00679B30` | `sub_00679B30_PathWalkParam98` | (ECX ctx) the walk with `+0x98`, appended at `+0x28` | I |
| `0x00679A60` | `sub_00679A60_PathFirstLine` | (ESI path, EDI &pt) the aim, then the line from the position | I |
| `0x00679720` | `sub_00679720_PathLineFree` | (EAX path; s, &t) 1 when free to `t`, else 0 and the last free point | I |
| `0x006793E0` | `sub_006793E0_PathTry3Dirs` | (EAX ctx; s, &dirs, &out) the first free of three | I |
| `0x00679380` | `sub_00679380_PathDistNear` | the distance `ctx.refresh` is compared with | I |
| `0x00678D70` | `sub_00678D70_PathDirRow` | the three directions of `g_DirOctant`'s row | I |
| `0x00679ED0`, `0x00679F70`, `0x0067A000` | `sub_00679ED0_PathPlanGreedyNear`, `sub_00679F70_PathPlanOnePoint`, `sub_0067A000_PathPlanKnockback` | types 7, 9, 8 | I |
| `0x00679E50`, `0x00679FD0`, `0x00679E60` | `sub_00679E50_PathPlanType3`, `sub_00679FD0_PathPlanType11`, `sub_00679E60_PathPlanType12` | the client-only slots | I |
| `0x0067B850` | `sub_0067B850_PathPlanType1` | type 1 | I |
| `0x0067ADC0` | `sub_0067ADC0_PathOctile` | `2 max + min` | I |
| `0x0067AE00`, `0x0067AE50`, `0x0067AEA0` | `sub_0067AE00_T1FindOpen`, `sub_0067AE50_T1FindClosed`, `sub_0067AEA0_T1AddClosed` | the two hash tables | I |
| `0x0067AED0`, `0x0067AF40` | `sub_0067AED0_T1Insert`, `sub_0067AF40_T1Pop` | the list sorted by `f`; the head to the closed table | I |
| `0x0067AFE0` | `sub_0067AFE0_T1Propagate` | a closed node's better `g` down its links | I |
| `0x0067B1C0`, `0x0067B200`, `0x0067B440` | `sub_0067B1C0_T1Alloc`, `sub_0067B200_T1AddNeighbour`, `sub_0067B440_T1Neighbours` | the pool, one neighbour, the eight | I |
| `0x0067B690`, `0x0067B740` | `sub_0067B690_T1Reduce`, `sub_0067B740_T1TargetFree` | the point list; the entry test | I |
| `0x0067C2D0` | `sub_0067C2D0_PathPlanType15` | type 15 | I |
| `0x0067B9F0`, `0x0067BBF0`, `0x0067BD80`, `0x0067BDF0`, `0x0067C1E0` | `sub_0067B9F0_T15Line`, `sub_0067BBF0_T15WalkStep`, `sub_0067BD80_T15Splice`, `sub_0067BDF0_T15Follow`, `sub_0067C1E0_T15Reduce` | the line, a follower's step, the splice, the two followers, the point list | I |
| `0x0067A240` | `sub_0067A240_PathPlanRandomWalk` | type 10; its draws checked in 654 game creations (the points by emulation) | C |
| `0x0067A140` | `sub_0067A140_PathPlanSpiral` | type 14 | I |
| `0x0040B330`, `0x0040B350` | `sub_0040B330_TableCos`, `sub_0040B350_TableSin` | `table[(a + 0x80) & 0x1FF]`, `table[a & 0x1FF]` | I |
| `0x00707800` | `g_SineTable` | 512 float32, within 1.8e-07 of `sin(2πk/512)` (`p3-bounds.txt`) | I |
| `0x006F1698` | `g_PathDistNear` | 64 dwords, `dx + 8 dy` | I |
| `0x006F1798` | `g_PathStep8Long` | 8 × (dx, dy) dwords, the same steps as `g_PathSearchStep8` | I |
| `0x006F1D98` | `g_T15Step` | 16 × (dx, dy) dwords: (0,−1), (1,−1), … twice | I |
| `0x006F1E28` | `g_T15DirFromStep` | centred: index `3 dy + dx` | I |
| `0x006F1E40`, `0x006F1E80`, `0x006F1EC0`, `0x006F1F00` | `g_T15TurnB`, `g_T15NextB`, `g_T15TurnA`, `g_T15NextA` | 16 dwords each: the followers' turns | I |

`re/types/path.h`: `T1Node`, `T1Store`, `T15Walker`.

## Walkthrough

### 1. `PathPlanGreedy`

```c
// fn:sub_00679C80_PathPlanGreedy@0x00679C80 (ECX ctx), trimmed; our names
path->iPoint = path->nPoints = 0;                      // +0x24, +0x28
if (path->b98) return PathWalkParam98(ctx);            // types 5, 6: § 2
pt = ctx->target;  path->points[0] = pt;
if (PathFirstLine(path, &pt)) { points[0] = pt; n = 1; return n; }            // reached
if (PathDistNear(pt, ctx->target) <= ctx->refresh) { points[0] = pt; n = 1; return n; }
cur = ctx->start;  n = 0;
if (pt != ctx->start) { points[n++] = pt; cur = pt; }
prev = 0xFF; turned = 0;
for (i = 0; i < ctx->limit; ) {                        // (s32) ctx +0x18
    if (cur == ctx->target) { if (turned) goto done; break; }
    dirs = PathDirRow(cur, ctx->target);  turned = 0;
    if (!PathTry3Dirs(ctx, cur, dirs, &d) || ((d - 4) & 7) == prev) break;
    next = cur + g_PathStep8Long[d];                   // u16 adds
    if (d != prev) { if (cur != ctx->start) points[n++] = cur; turned = 1; }
    cur = next;  prev = d;  i++;
    if (i >= ctx->limit && turned) goto done;
}
if (i) points[n++] = cur;
done: path->nPoints = n; return n;
```

- [C] As above, the whole record compared byte by byte (families `greedy` 600, `gbound` 30). The controls fail what they separate and pass none (`check.txt`): `order` (the three directions reversed) 114, `noflag` (the last point always written) 57 of `greedy` and all 30 of `gbound`, `limit` (one more step) 67 and 30, `ctxroom` 25, `dist` (`g_PathDistNear` ignored) 7, `rev` (no reversal test) 2, `refresh` (0 for `ctx.refresh`) 2. (run:2026-11-03-path-emu-3)
- [C] **A walk whose last step turned ends one step short:** when the step that reaches the target or the limit changed direction, only the corner is written, not the point after it. (0x00679E1D–0x00679E2E, run:2026-11-03-path-emu-3, control `noflag`)
- [C] **The first point is written twice when the walk turns at once**, since `cur` equals the first point and is not the start. (0x00679DDA–0x00679DF4, run:2026-11-03-path-emu-3)
- [C] **A reversal ends the walk**, with the point reached written. (0x00679DB7–0x00679DBC, run:2026-11-03-path-emu-3, control `rev`, 2 cases)
- [C] `PathFirstLine` (0x00679A60): the assert below; with `+0x7C` = 0, `pt` becomes the position's subtile and it returns 0; otherwise `PathAimNextPoint(path, 1; 1)` runs over the record, with `points[0]` the target and `+0x28` = 0, which writes the vector, the step and the facing; when that zeroes `+0x7C` (the target is the position) the same; else the line from the position. So **the planner aims the path before its own points exist**, and the speed gates the line. (0x00679AC0–0x00679B1B, fn:sub_0064FE40_PathAimNextPoint@0x0064FE40, run:2026-11-03-path-emu-3)
- [C] **The line's inputs are the path's, the walk's the context's:** `PathLineFree` tests under path `+0x1C`, `+0x48`, `+0x50` from the position; `PathTry3Dirs` under `ctx.room`, `+0x28`, `+0x2C` from `ctx.start`. The cases set them apart on purpose; `PathPlan` writes both from the same fields (path/0001 § 1), and `+0x48`, `+0x50` are not changed by a planner. (0x00679726–0x0067972C, 0x00679417–0x00679423, run:2026-11-03-path-emu-3)
- [C] **`PathLineFree`** (s, t): with `ax = |dx| + 1`, `ay = |dy| + 1`, along the major axis, with an error that starts at the minor count, adds it per step, and on reaching the major count moves the minor axis, tests the moved cell only when the remainder is above 0; on a diagonal both axes per step. A cell blocked returns 0 and the last point that was wholly free. It ends when the major coordinate reaches `t`'s. (0x00679720–0x00679A58, run:2026-11-03-path-emu-3)
- [I] The branches at 0x00679794 and 0x006798C9 (the major difference 0) cannot be taken: `ax > ay` needs `|dx| > 0`, `ax < ay` needs `|dy| > 0`. (0x00679790, 0x006798C5)
- [C] `PathDistNear(a, b)`: with `dx`, `dy` absolute; below 8 on both axes `g_PathDistNear[dx + 8 dy]`, a negative entry giving 0 and another `entry + 1`; otherwise `2 max + min` (`dx > dy` strictly picks the first form, which is the same value at equality). (0x00679380–0x006793D7, data:g_PathDistNear@0x006F1698, run:2026-11-03-path-emu-3)
- [C] `PathTry3Dirs`: the row's three directions in order, each tested at `cur + step`; the first free one. (0x006793E0–0x0067951E, run:2026-11-03-path-emu-3, control `order`)
- [I] Its assert 0x4C (a third direction of 255) cannot fire from these callers: `g_DirOctant` holds 0..7 only, and the `+0x98` walk masks with 7. (`p3-bounds.txt` `BOUND dirs`, 0x006794BC, data:g_DirOctant@0x006F1518)
- [C] **Asserts at the first line:** a unit that is neither player nor monster (line 0x144, 43 cases) and a path of type 4 (0x145, 25 cases), both at their return site 0x00679A83, in `onept`; what `0x00408090` then does is outside the case. (0x00679A79–0x00679A9E, run:2026-11-03-path-emu-3)
- [I] 0x146, 0x147 (a target coordinate 0) are read, not run: `PathPlan` refuses a target of (0, 0), but not one with a single 0 coordinate, except under a target unit (path/0001 § 1). (0x00679AA5–0x00679AB9)
- [C] **Fields:** none of `ctx +0x0C`, `+0x10`, `+0x1C`, `+0x20`, `+0x24` is read (undeclared, `traced=0`), in any family here. (run:2026-11-03-path-emu-3)
- [I] **Type 13** differs from type 2 only in the flags word's `0x100`, which no planner here tests; the only flag read is `0x200`, in `PathAimNextPoint`. So 2 and 13 are the same plan, and the difference is `PathReplan`'s (path/0001 § 9). (0x006503AF, data:g_PathTypeFlags@0x006EB690)

### 2. The `+0x98` walk: types 5, 6 (and 12)

- [C] As the walk of § 1 with these differences: no line first and no refresh test; it starts at `ctx.start`; each direction is `(row + b98) & 7`; **a turn always writes `cur`, so the first point is the start itself**; it appends from `+0x28`; a `turned` flag at the target skips the last point, and the limit behaves as in § 1. (family `g98`, 300 cases, values 2, −2, −4 and 1; controls `param0` 164, `order` 158) (0x00679B30–0x00679C78, run:2026-11-03-path-emu-3)
- [I] With `+0x98` = 2 or −2 the three directions are the row's turned by 90°: the walk goes sideways to the target line rather than to the target. A stock read of `g_PathTypeParam98` gives 2 and −2 to types 5 and 6, and −4 to type 12. (data:g_PathTypeParam98@0x006EB648)

### 3. `PathPlanGreedyNear` (type 7)

```c
// fn:sub_00679ED0_PathPlanGreedyNear@0x00679ED0 (ESI ctx); our names
path->iPoint = path->nPoints = 0;
n = PathPlanGreedy(ctx);
if (n && PathDistNear(points[n - 1], ctx->target) <= ctx->refresh && points[n - 1] != ctx->start) return n;
if (dx*dx + dy*dy > 324) return n;                     // start to target; 0x00679F43
r = PathPlanType1(ctx);
if (r) return r;
return n ? PathPlanGreedy(ctx) : 0;
```

- [C] As above (family `near`, 480 cases: 244 greedy with points, 71 with none, 52 by type 1, 113 type 1 with none). The bound is `≤ 324` (control `le325` 18 cases, the 80 written at 324 and 325 among them); `noretry` 18. (0x00679F43–0x00679F61, run:2026-11-03-path-emu-3)
- [I] **`324` is 18 subtiles on an axis:** (18, 0) passes, (18, 1) at 325 does not; the player plans this type (path/0001 § 11), so a player's walk within 18 subtiles falls to type 1 when the greedy route stops short. (`p3-bounds.txt`, fn:sub_0057F090_PlrModeStartMove@0x0057F090)
- [C] After a type 1 that returned 0 the list is left as it was and greedy runs again from the record, since greedy clears `+0x24`, `+0x28` and rewrites. The second greedy repeats the first's aim. (0x00679F5C, run:2026-11-03-path-emu-3)

### 4. `PathPlanKnockback` (type 8)

```c
// fn:sub_0067A000_PathPlanKnockback@0x0067A000 (EBX ctx); our names
k = (path->b90 >> 1) + 1;
if (t = path->target) {                                 // +0x58
    // (tx, ty): types 2, 4, 5 the static path's +0x0C, +0x10; others the words +0x02, +0x06, 0 without a path
    dx = sx - tx;  dy = sy - ty;  m = max(|dx|, |dy|);
    if (m) { dx = k * dx / m;  dy = k * dy / m; }       // signed idiv, toward zero
    pt = (sx + dx, sy + dy);                            // u16 adds
} else pt = ctx->target;
points[0] = pt;
PathLineFree(path, ctx->start, &pt);                    // from ctx.start here, not the position
PathSetTargetPoint(path, pt.x, pt.y);                   // +0x10, +0x12; +0x58 = 0: 0x00648AD0
if (pt == ctx->start) return 0;
points[0] = pt;  path->nPoints = 1;  return 1;
```

- [C] As above (family `knock`, 300 cases, 158 one point, 142 refused; target types 0–6; controls `k` 124, `floor` 41, `ctxroom` 19). (0x0067A00D–0x0067A13C, run:2026-11-03-path-emu-3)
- [C] **The plan clears the path's target unit** and leaves the point as its target, on either outcome. It does not write `+0x24`; `PathPlan` has set it. (0x00648AE2–0x00648AEA, run:2026-11-03-path-emu-3)
- [I] A unit standing on its target has `m` = 0, and `pt` is the start: a return of 0. (0x0067A0B6)
- [I] `PathPlan`'s window applies to the request's target (path/0001 § 1); `k` ≤ 128 and the pushed point are not tested here beyond the line. (0x0067A016)

### 5. `PathPlanOnePoint` (type 9) and `PathPlanType3`, `Type11`, `Type12`

- [C] Type 9: `+0x24 = 0`; `points[0] = ctx.target`; `PathFirstLine`; when the point it leaves equals `ctx.start` return 0 with `+0x28` untouched, else `points[0] = pt`, `+0x28 = 1`, 1. (family `onept`, 200 cases: 62 one point, 70 refused, 68 at the asserts; `ctxroom` 7) (0x00679F7B–0x00679FBE, run:2026-11-03-path-emu-3)
- [C] Type 3: `+0x24 = 0`, a jump into greedy. Type 11: `+0x24 = 0`, `points[0] = target`, `PathFirstLine` on the slot itself, return 1, `+0x28` never written, **even when the point equals the start**. Type 12: `+0x24 = 0`, `+0x98 = −4`, the walk; 0 returns 0, leaving `+0x98` at −4; else `+0x28 = n`, `+0x98 = −2`, the walk appended; when that added nothing `+0x98 = 2` and the walk again; then `+0x98 = −4`; the total. (family `client`, 60 cases each: 43 zero, 84 one point, 53 more; control `order` 49) (0x00679E50–0x00679EC2, 0x00679FD0–0x00679FF3, run:2026-11-03-path-emu-3)
- [I] **None draws:** their only calls are in the graph of the summary. (0x00679E5A, 0x00679E79, 0x00679FE7)
- [I] **Their reach:** no server code sets 3, 11 or 12 (§ 12); that they run in the client at all is out of scope (owner decision 5) and unfollowed past path/0001's three type-11 sites. (0x004614A6, 0x004B04BF, 0x004C8870)

### 6. `PathPlanType1`

```c
// fn:sub_0067B850_PathPlanType1@0x0067B850 (ECX ctx), frame 0x32F4 (struct:T1Store); our names
if (path->target && all of (tx±2, ty±2), (tx-2, ty), (tx, ty-2), (tx+2, ty), (tx, ty+2) are blocked) return 0;   // 0x0067B740
root: g = 0; h = f = octile(start, target); pt = start;  insert(root);
best = 0;
for (n = pop(); n; n = pop()) {
    if (!best || n->h < best->h || (n->h == best->h && n->g > best->g + 5)) best = n;
    if (n->h == 0) break;
    if (!neighbours(n)) break;                          // the pool is spent
}
return reduce(best);
```

- [C] As above, by families `t1real` 400, `t1syn` 240 and `t1stair` 40. `h`, `f`, `g` as words: `f = g + h`, `h = 2 max + min`, straight 2, diagonal 3. Controls: `h` 198 and 238, `cost` 176 and 235, `list` 173 and 231, `offs` 173 and 233, `gt0` (the 5 dropped) 4 and 4, `resort` 19 and 103, `pool` (201) 1 and 9, `nostart` 18 of `t1real`, `max77` 15, `min2` 5. (0x0067B850–0x0067B9B0, run:2026-11-03-path-emu-3)
- [C] **The target's surroundings:** the test applies only with a target unit (`+0x58`), in the order given, on 8 cells two away from the target; all blocked returns 0 with nothing else written. (0x0067B740–0x0067B846, run:2026-11-03-path-emu-3, control `nostart`)
- [C] **The neighbour order:** (−1,−1), (−1,+1), (+1,−1), (+1,+1), (−1,0), (0,−1), (+1,0), (0,+1), each tested with `COLL_PatternTestBool` under the context's room, pattern and mask, the room as hint for all. **The diagonals come first and no corner test applies:** a diagonal between two blocked cells is taken. (0x0067B458–0x0067B677, run:2026-11-03-path-emu-3, control `offs`)
- [C] **The open list:** sorted by `f` as s16; a new node goes before the first with `f` not less than its own, so among equals the newest comes first. **An open node given a better `g` is not moved** in the list; its `f` is rewritten where it lies (control `resort`). (0x0067AED0–0x0067AF35, 0x0067B2A4–0x0067B2B3, run:2026-11-03-path-emu-3)
- [C] **A closed node given a better `g`** takes the new parent and `f`, then `T1Propagate` carries it down its child links, on a stack at `+0x2FC8`: a child takes it when strictly better. Each node holds 8 links (`+0x10..+0x2C`), filled in neighbour order; a node is expanded once and has 8 neighbours, so the code's silent drop of a ninth is not reached ([I], 0x0067B28E). (0x0067AFE0–0x0067B1B7, 0x0067B2C1–0x0067B34E, run:2026-11-03-path-emu-3)
- [C] **The pool:** 200 nodes of 0x38 bytes. The 201st request ends the search at once with the nodes so far, **`best` included even when no route reached the target**. So a plan past the pool gives a list ending short: 60 of `t1real` end at the pool (2 of them returning 0) and 108 of `t1syn`. (0x0067B1C0–0x0067B1CF, 0x0067B981, run:2026-11-03-path-emu-3)
- [C] **`best` is the node with the least `h`**, and on equal `h` a later node with `g` more than 5 above replaces it, an odd preference for a longer route. Control `gt0` separates only 4 cases of each family. (0x0067B946–0x0067B964, run:2026-11-03-path-emu-3)
- [C] **The reduction** (0x0067B690): walks back from `best`, keeps a node whose step from its parent differs from the kept step before it, stops at 78 kept; 1..77 are copied in order to the list, and otherwise it returns 0 with the list untouched. **The start is never kept; a single-segment route gives one point**, unlike the search (path/0002 § 6). It writes neither `+0x24` nor `+0x28`. (0x0067B6C0–0x0067B72B, run:2026-11-03-path-emu-3, controls `max77`, `min2`)
- [C] **Not read:** `ctx.limit`, `ctx.refresh`, `+0x91`. The refresh's near stop is the caller's, and a type-1 route has no length limit but its pool. The hash tables (`0x006F1998`, `0x006F1B98`) only place nodes in buckets: the model holds no hash and matches, 2 028 240 table reads accounted over the three families and `near`'s. (run:2026-11-03-path-emu-3)

### 7. `PathPlanType15`

```c
// fn:sub_0067C2D0_PathPlanType15@0x0067C2D0 (ECX ctx), frame 0x160; our names
assert unit type 0 or 1;                                 // line 0x2AD
lim = path->b91;                                         // the byte, not ctx.limit
if (path->target && lim < 40) lim = 40;
n = T15Line(start, target, lim, L, &axis);               // cells after start; 0 when the major difference > lim - 1
if (n <= 2) return 0;
cur = start;
for (i = 0; ; ) {
    if (blocked(L[i])) {
        r = T15Follow(ctx, L, cur, &i, &n, lim - i, axis);
        if (r == 0) return T15Reduce(points, start, L, i);
    }
    cur = L[i];  i++;
    if (i >= n) break;
}
return n ? T15Reduce(points, start, L, n) : 0;
```

- [C] As above (families `t15real` 400, `t15syn` 300, `t15stair` 40; outcomes by `OUTCOMES`: clear line, refused at 2 points or fewer, follow, follow with splice, truncation, loop). Controls: `lim40` 32 and 7, `lim18` (`ctx.limit` for the byte) 120 and 150, `min2` 4 and 1, `reduce` 171, 230, 34, `wswap` 29, 99, 2, `noswap` 28, 66, 18, `lim50` 4. (0x0067C2D0–0x0067C416, run:2026-11-03-path-emu-3)
- [C] **`T15Line`:** a Bresenham from `start` with the error from 0: major step, error plus the minor difference, and at the major difference the minor step. An equal `dx`, `dy` takes `x` as major. `axis`: 2 for `y` increasing as major, 0 decreasing, 1 for `x` increasing, 3 decreasing. (0x0067B9F0–0x0067BBA8, run:2026-11-03-path-emu-3)
- [C] **`T15Follow`:** two followers from `cur`, with directions from `g_T15DirFromStep[3 dy + dx] + 1` and `+ 7` of the step to the block (not masked: an index up to 14, and the tables have 16 entries). A follower's step tries its direction, then up to three turns of its `Turn` table; a free one is its next cell, and on success its direction becomes `Next[d]`. **They alternate**, except while one has its mark set (`+0x1C`: it met the other's position; it then keeps the move). (0x0067BBF0–0x0067BD6E, 0x0067BEBA–0x0067C045, run:2026-11-03-path-emu-3, data:g_T15DirFromStep@0x006F1E28)
- [C] **How a follow ends** (0x0067BF38, run:2026-11-03-path-emu-3):
  - a follower with at least one cell, ahead along `axis` by `v > 0`, on `L[i + v − 1]`, within `n`: the walked cells replace the line up to there (`T15Splice`, assert 0x1BB read, not reached); the count returned;
  - marked and back at the other's cell: `n = i`, return 0, so the plan is the line before the block;
  - a follower's count reaching `lim4 − n − 1`, or all four tries blocked, stops both. Then, with `lim4 > 80`, `n = i`, return 0; otherwise, of the two last cells take the follower nearer the target (`d0 < d1`, else the second), and when `ctx.start` is nearer than that cell return 0 with nothing changed; else its cells are copied at `L[i]` and `n = i + count`.
  (0x0067BF38–0x0067C1D0, run:2026-11-03-path-emu-3, controls `wswap`, `noswap`, `lim50`)
- [I] **A count of 0 for a follower reads as a point:** `last` is then the follower's stop word (1 or 0), as a point of (1, 0) or (0, 0), since the index is `+0x20 + 4 × count`. The model carries it; no control separates it. (0x0067C0E2–0x0067C13A)
- [C] **`T15Reduce`:** the last point is always kept. A point is dropped when its step equals the last, or as one kink, with nothing dropped since (`run < 1`) and both coordinates of the step differing, when `lx` becomes −2. So a line like E, SE, E, SE loses every other corner. (0x0067C1E0–0x0067C2C8, run:2026-11-03-path-emu-3, control `reduce`)
- [C] **A read past the written list, without effect:** with `i = n` after a follow, 0x0067C3D6 reads `L[n]`, where a truncation has written only the `x` word and a splice nothing; the value goes to `cur`, and the loop then ends. These are the 16 `term` lines of `check.txt` (11 + 5), each accounted only in a case whose model made that read. (0x0067C3D6–0x0067C3E8, run:2026-11-03-path-emu-3)
- [I] `+0x58` set with `+0x91` below 40 is a monster with its creation's 14 (path/0001 § 8) following a unit, so its line reaches 39 subtiles where its other plans have 14. `PlrReachTest` plans with limit 77, restored. (0x0067C312, fn:sub_0054CB10_PlrReachTest@0x0054CB10)

### 8. `PathPlanRandomWalk` (type 10)

```c
// fn:sub_0067A240_PathPlanRandomWalk@0x0067A240 (ECX path, EDX &seed); our names
add[32] = { -1, 0, 1 } ten times, then -1, 1;            // built on the stack
n = path->b91 >> 1;
cur = (path->x word, path->y word);                      // +0x02, +0x06
d = PathDirRow(cur, path->tx_ty)[0];                     // the row's first direction, once, from the start
for (k = 0; k < n; k++) {
    seed = 0x6AC690C5 * lo + hi;                         // the LCG, inline, 0x0067A31A
    dir = (d + add[lo & 31]) & 7;
    points[k] = cur;
    cur += 2 * g_PathStep8Long[dir];                     // u16 adds
}
points[n] = cur;  path->nPoints = n + 1;  return n + 1;
```

- [C] As above (family `rwalk`, 300 cases, 5 092 draws, 23 distinct draw counts, all 300 point lists distinct; controls `shr` 279, `n1` 300, `step1` 258, `accum` 204, `noadd` 238). The seed is compared in every case. (0x0067A240–0x0067A385, run:2026-11-03-path-emu-3)
- [C] **It is not a walk of accumulating turns:** every step is the first direction ±1 or straight (`accum`). The **first point is the position itself**. No grid is read and no room: the missile's collision is its own. (0x0067A32E, run:2026-11-03-path-emu-3)
- [I] The chance of a straight step is 10/32, of each side 11/32. (`add`, 0x0067A258–0x0067A2F3)
- [C] **A path with `+0x91` of 0 or 1 draws nothing and has one point.** (family `rwalk`, `draws:0` 42) (0x0067A2FE, run:2026-11-03-path-emu-3)

### 9. `PathPlanSpiral` (type 14), and why it stays a reading

- [I] **The reading:** from the 16.16 position `(fx, fy)`, with `r = 0`, `a = 0`, `k = 0`: `r += 0x2580`, `a += 16`, `x = trunc(cos(a) · r) + fx`, `y = trunc(sin(a) · r) + fy` from `g_SineTable`; when `x >> 16` or `y >> 16` differs from the last kept cell, `points[k++]`, until `k = 77`. `+0x28 = 77`, return 77. No draw, no grid, neither `+0x90` nor `+0x91`. The radius passes through a float32 (`fstp`), exact for these values, and the control word is `or 0xC00` around each `fistp`: rounding toward zero. (0x0067A180–0x0067A233, data:g_SineTable@0x00707800, fn:sub_0040B330_TableCos@0x0040B330)
- **Why it cannot be `[C]` here:** ADR-0015 leaves x87 results uncovered, and this batch shows the reason in the planner. The kept family `spiral` compares the emulator with the model **rounding** and matches 90 of 90; the control `trunc` (the reading above) separates 47 and passes 0, the 60 `tight` cases being written so a rounded product crosses a subtile. So the p-code `FISTP` ignores the rounding field. It is the emulator's behaviour, not the game's. (run:2026-11-03-path-emu-3, 0x0067A1A1)
- [C] The first table read has argument 16 and return site 0x0067A196, in all 30 cases of `spiralobs` (boundary 0x0040B330; nothing after it is covered). (0x0067A18D–0x0067A191, run:2026-11-03-path-emu-3)
- [I] The structure agrees (`swap` separates 90, passes 0): the count, the order of the axes and the skip of a repeated cell hold under the emulator's rounding. Truncation stays the reading until Phase 2's type-14 plans compare it (floor 30, § Phase 2). (0x0067A1E6, run:2026-11-03-path-emu-3)

### 10. Missiles H1, and the other callback

- [C] **`0x005C9290` (ECX missile, EDX arg)** run whole, to its return (family `h1`, 198 of the 300 cases; `0x005AC040` the other 102): `r = data +0x0E`; `r ≥ 78` gives `r = 77`, written back to `+0x0E` and `+0x10` through their clamping setters; `Init(path word +0x10 + arg, 0x29A)`; `PathSetType(path, 10)`; `PathSetByte90(path, r)`; `PathPlan(path, missile, 0)`, which takes its flag `0x40000` branch to the random walk; flag `0x20` set. (`nocap` 92, `noarg` 195, `shr` 293, `n1` 300.) (fn:sub_005C9290_MissCbReseedPathXPlusArg@0x005C9290, 0x005C92A8–0x005C92E9, run:2026-11-03-path-emu-3)
- [C] **`0x005AC040`:** the same without the argument; `r > 255` gives 255, not written back; `PathSetByte90` then caps it. (0x005AC04F–0x005AC08B, run:2026-11-03-path-emu-3)
- [C] **Which call steps:** at `PathPlan`'s entry, with `(path, missile, 0)` and return site 0x005C92EE or 0x005AC090, the seed is the Init itself and the record has type 10, in all 100 of `h1obs`. So neither earlier call steps it. (0x00649970, run:2026-11-03-path-emu-3)
- [C] **Why 20, 38 and 10, from the game's own logs** (`p3-h1log.txt`; the seed at the exit predicted from the Init and the logged range, 45 logs of three runs; fn:sub_0067A240_PathPlanRandomWalk@0x0067A240):

| callback | class | Missiles row | `Range` | after the cap | draws | creations | match |
|---|---:|---|---:|---:|---:|---:|---:|
| `0x005C9290` | 458 | `firestormmaker` | 40 | 40 | 20 | 442 | 442 |
| `0x005C9290` | 195 | `lightunique` | 98 | 77 | 38 | 176 | 176 |
| `0x005AC040` | 408 | `catapultchargedballbolt` | 20 | 20 | 10 | 36 | 36 |

  (tbl:Missiles.txt:Range, run:2026-10-25-skills, run:2026-10-27-skills, run:2026-10-30-skills-catalogue)
- [C] **The ranges the skills check took as oracles are this cap:** across the 45 logs `MCB1` gives range and frames left (77, 77) for all 176 of class 195 and (40, 40) for all 442 of class 458, and `h1log` compares `md.rng` with the model's `r`. The 450 of run:2026-10-25-skills (skills/0003 § 15) are 442 of class 458 and 8 of class 195, a part of these 618 (the third class, 408, takes the other callback); the 168 more class-195 creations come from the later runs. (`p3-h1log.txt`, 0x005C92AD–0x005C92BB, run:2026-10-25-skills, run:2026-10-27-skills)
- [I] The range logged before the callback is the row's `Range` in all 654, and all three classes have a blank `LevRange`; a missile with a `LevRange` draws by its own level (skills/missiles B1). (`p3-stock.txt`, fn:sub_0059FA30_MissileCreate@0x0059FA30)
- [I] The four reseed callbacks and do functions other than these two reach the same walk when they set type 10 (path/0001 § 11); they are not rerun here. (fn:sub_00649760_PathPlanStraight@0x00649760)

### 11. Points against the 78 slots

From `p3-bounds.txt` (`tools/path_emu3.py bounds`), with the emulated counts of `check.txt`. The slots are `+0x9C`..`+0x1D3`; index 78 is `+0x1D4` (anim/0003's crossed-subtile count); the record's last index is 88.

- [C] **Greedy, `+0x98` = 0: at most `ctx.limit + 1`.** One first point, then at most `limit` from the loop, since a final point needs a loop that did not turn on its last step. `gbound` reaches **78 at limit 77** (`maxret=78`): `points[77]`, the last slot, no write past it. (0x00679E2E, run:2026-11-03-path-emu-3)
- [I] Limit 77 is the most any writer gives: `PathSetByte90` caps at 77, creation gives 73 or 14 (path/0001 § 2). Limit 78 would write `+0x1D4`; no code path sets it on the server (the quest byte stores are not paths, path/0002 § 10). (0x00648E7D)
- [C] **The `+0x98` walk: at most `ctx.limit`** from an empty list (`g98` reaches 76). (`p3-bounds.txt`, 0x00679E8A, run:2026-11-03-path-emu-3)
- [I] **Type 12's total can be `2 × limit`**: 78 fits to limit 39, limit 40 writes `+0x1D4`, limit 44 still stays in the record (88 points), limit 45 passes its end. This is the sum of two walks each bounded by `limit`; only cases of limit 38 or less ran (`client` maxret=14), so the overflow past 78 is a reading, not an observation. Client-only. (`p3-bounds.txt`, 0x00679E8A, run:2026-11-03-path-emu-3)
- [C] **Knockback and one point: 1.** Type 11: 1. (run:2026-11-03-path-emu-3, 0x0067A134, 0x00679FBE)
- [C] **Type 1: 1..77; a raw 78 returns 0** (`t1stair`: 15 cases return 0 past 77, 5 of one point; `maxret=77`). The buffer stops at 78. 78 corners fit in the pool: about 117 cells of the corridor. (0x0067B6C0, 0x0067B70B, run:2026-11-03-path-emu-3)
- [I] **Type 1's propagation stack** has 200 slots (`+0x2FC8`..`+0x32E7`), and the 201st push would overwrite its own count at `+0x32E8`. The largest depth in 720 cases is 23 (`maxstack`); no bound is proved. A strict improvement is required for each push. (0x0067AFEA, 0x0067B16F)
- [I] **Type 15: at most `lim − 1` = 76 in `L`, and the kept points at most that.** The line has `lim − 1`; L is 77 dwords, so its terminator fits at index 76, and `lim` 78 would reach `EBP − 0x2C`. A follower stops at `lim − i − n − 1`, so a splice leaves `n ≤ lim − i − 2` and a truncation `n ≤` the old `n`. Reached: `maxline=73`, `maxn=72`, `maxret=56`. (0x0067BFFD–0x0067C00F, 0x0067C3E0, run:2026-11-03-path-emu-3)
- [I] A `lim` above 80 reaches the truncation's refusal only with bytes no writer gives (`lim50`, 4 cases of `t15syn` at 85 and 90, short lines). (0x0067C045)
- [C] **Random walk: `(+0x91 >> 1) + 1`** (`maxret=39` at 77). (`rwalk`, run:2026-11-03-path-emu-3, 0x0067A37C)
- [I] 78 points is `+0x91` = 154 or 155; 156 gives 79; 255 gives 128. No writer passes 77. At 77 the walk reaches 76 subtiles on an axis, so its u16 adds wrap only on a position within 76 subtiles of 0 or 65 535. (`p3-bounds.txt`, 0x0067A352)
- [I] **Spiral: 77, always**, in 94 iterations at the kept start and at most 95 in the emulator's cases. Its `r` adds would wrap at iteration 223 697. (`p3-bounds.txt`, 0x0067A21D)

### 12. The `+0x3C` scan (P1.3b)

From `p3-scan3c.txt` (`tools/path_emu3.py scan3c`, objdump over all of `.text`; a raw scan of `C7 /0` with disp8 and disp32 for the three values; a backward walk to each register store's definition and base):

- [I] **No immediate:** 174 dword stores to `[reg+0x3C]`, 21 with `mov` of an immediate, with the values 0 (9), 1 (6), 2 (2), 0xD, 0xF, 0x100, −1; none is 3, 0xB or 0xC. The raw scan finds 0 hits. (`p3-scan3c.txt`, 0x006503AF)
- [I] **Read-modify-write with an immediate:** four, not covered by the "no immediate" line (`by_op` add/imm 3, or/imm 1): `add [reg+0x3C], 1` at 0x005BB82C, 0x0063D4CF; `add [reg+0x3C], -1` at 0x0063D54C; `or [reg+0x3C], -1` at 0x0068CDCF. Counters or a fill, bases unfollowed; a `+1` on a type of 2 or 10 would make a 3 or 11, so they join the unresolved remainder. (`p3-scan3c.txt` `by_op`, objdump of `.text`)
- [I] **Register stores:** 138, with definitions: memory 67, zero 29, other arithmetic 26, a call's return 14, a literal 2 (0xFF at 0x00559002, 0x80000 at 0x00409FB9). By base: the one read from a unit's `+0x2C` is 0x0046525A, the client copy of path/0001 § 2, copying `+0x3C` from another path; `PathSetType`'s own 0x00648D70; 0x0064BE75, a rectangle's store in the same range, not a path's. Other 82 server bases are resolved to something other than a unit's path; **18 server bases are unresolved** by the walk: 0x00529481, 0x0052981A, 0x00529BD7, 0x00529F12, 0x00559002, 0x0057C628, 0x005B5389, 0x005BBC61, 0x005FFF92, 0x00600225, 0x00600230, 0x006003B2, 0x006242FF, 0x00626E9D, 0x00670869, 0x0068CFFB, 0x006C3CF6, 0x006C3DE9 (the 19 `server … base=?` lines of `p3-scan3c.txt` less 0x0064BE75, read by hand above). (`p3-scan3c.txt`, 0x0046525A, 0x00648D70)
- [I] **So a 3, 11 or 12 can enter a server path's type only by:** a `PathSetType` argument (path/0001 § 11's list, ruling 4: no 3, 11, 12), or a store of one of those 18, or a whole-record copy, which only carries a value already there. The rule that the "not set" reading rests on is thus the listed calls and these 18. Phase 2's break lines observe the rest (§ Phase 2). (fn:sub_00648CF0_PathSetType@0x00648CF0)

### 13. The emulation (run:2026-11-03-path-emu-3)

- **Entry and images (P1.1 review ruling 2).** As path/0002 § 11: entry at the planner with a declared context in `ECX` for § 1–7; `ECX` the path and `EDX` the seed pointer for the walk and the spiral; the callbacks whole. The same 236 real room records (four blocks, each with and without seeded marks; the blocks regenerated, 362, 44, 215 model checks, 0 failures), plus synthetic rooms. The start's own marks stay off; targets fall where they fall. The record is 512 random bytes under its declared fields, compared whole.
- **Scratch.** `EmuScratch.java` with the P1.2 check's changes: a `UX <n>` line when `U` lines pass the 200-key cap; `U_OK` keyed on pc, size and unwritten count. Accounted: `_chkstk`'s probes (`chkstk`) and § 7's read (`term`).
- **The negative probe, kept as family `probe`** (`check.txt`, the first three lines): **(read)** a planner entered with `ECX` on stack bytes no case wrote gives 2 `U` lines, both unaccounted, and the check fails the case; **(overflow)** `memcpy` over 0x800 unwritten bytes gives 200 `U` lines and `UX 312`, and the check fails it; **(tightened)** the accounted pc under another size or count is not accounted. The check's `result` line requires all three.
- **Totals:** 18 compared families, **4 330 cases (and the 2 probes), 4 330 matching, 0 stopped, 0 unaccounted traced accesses**; every control passes 0 and separates at least one. **The `spiral` family's 90 are inside the 4 330 and are no evidence about the game**: they match a model chosen to agree with the emulator's `FISTP` (§ 9). Without them, **4 240 cases** test the game's code against a reading; only `spiralobs` (30 cases, the first table read) is `[C]` for type 14. The tool's `total` line is the raw 4 330. The kept `probe` has three parts and the check's result requires all three; the third is a lookup that the accounted key does not cover another size or count, not a run (the check's return omitted it until the Tier B check of this lane). Distinct outcomes are the `OUTCOMES` and `distinct=` of each family.
- **Accounted reads** are the image tables and switch tables named in `TABLES` of the tool.
- **Not covered:** `PathPlan`'s tail after the planner (path/0001 § 6); what the game stores in a context; x87 (§ 9); what `0x00408090` does; the asserts 0x4C, 0x122, 0x146, 0x147, 0x1BB, 0x2AD (not reached). No symbol is raised by the emulation (rule 14); `PathPlanRandomWalk`'s row rests on `h1log`'s game logs.

## Data touched

- `struct:PathPlanCtx` (`+0x00`, `+0x04`, `+0x08`, `+0x14`, `+0x18`, `+0x28`, `+0x2C`, `+0x30`), `struct:PathRequestFields`, `struct:PathMove`, `struct:DungeonRoom`, `struct:CollMap`; new `struct:T1Node`, `struct:T1Store`, `struct:T15Walker`.
- Image tables: `data:g_DirOctant@0x006F1518`, `data:g_PathDistNear@0x006F1698`, `data:g_PathStep8Long@0x006F1798`, `data:g_T15Step@0x006F1D98`, `data:g_T15DirFromStep@0x006F1E28`, `data:g_SineTable@0x00707800`, and the turn tables of *Functions*.
- `tbl:Missiles.txt:Range`, `tbl:Missiles.txt:LevRange` (§ 10).

## Dead ends

- A first control `round` for the spiral separated nothing in 30 cases (the subtile hides the fraction). Written tight, it **passed** all 47: that is § 9's finding, seen first in `emu/dev-3/`. The model's default was then set to the emulator's rounding and the control to `trunc`.
- A stair of E, E, S, S for type 1's point bound is a straight diagonal under its diagonals (`maxret=3` in `emu/dev-2/`); E, E, E, S, S, S gives corners. Moved in `emu/dev-3/`.
- The `U` lines at 0x0067C3D6 failed `t15*` in `emu/dev-2/`, and those with 4 unwritten bytes in `dev-3/`; both read as § 7 and accounted by the model's `overread`.
- The development runs' tool revisions were not copied; no claim cites them. `emu/dev-3/` holds `dev-2/`'s outputs for the families whose cases did not change. The kept directory's case files equal `dev-3/`'s.

## Open questions

- `[L]` Whether type 1's stack can reach 200 entries (§ 11): measured 23.
- `[L]` Truncation in the spiral (§ 9): Phase 2's type-14 plans.
- `[L]` The 18 unresolved server bases of § 12: Phase 2's break lines on the slots of 3, 11, 12.
- `[L]` The reasons behind `best`'s "more than 5" and the walk's one-step-short end: only the behaviour is read.

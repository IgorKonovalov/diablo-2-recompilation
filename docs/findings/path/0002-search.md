# 0002 — The search: `PathPlanSearch` and `PathSearchRun` (types 0 and 16), and which other planners use it

> **Subsystem:** path/search
> **Question:** what do `sub_0067AD00_PathPlanSearch` and `sub_0067AAA0_PathSearchRun` compute from a `PathPlanCtx`: the node
> store, the cost and heuristic, the neighbour order and tie-break, the limits, the reduction to the path's points, the draws
> under type 16; do `PathPlanType1`, `PathPlanType15` and greedy-near's switch call it; what are the 14 byte stores at the
> request offsets; and how many points can the search return against the record's 78 slots?
> **Date:** 2026-11-03   **Plan:** 0054 (Phase 1, batch P1.2)   **Status:** for review (`lane/r54b`)

Static reading of the pinned `Game.exe` with objdump (`p2-search.asm`: `0x00679C80`–`0x0067C480`) and Ghidra decompiles as a
reading aid (project copy `workspace/ghidra-r54b`, symbols replayed from `re/symbols.csv`; `p2-dec.c`), the scans of
`tools/path_scan.py` (`sites`, `writers`) and `tools/path_emu2.py` (`stores`, `bounds`), `RngCallGraph` (`p2-rngcg-search.txt`),
`FindPointer` (`p2-findptr.txt`), and emulation under ADR-0015/ADR-0021 entering at the planner (§ 11,
run:2026-11-03-path-emu-2). Kept outputs are under `workspace/logs/r54b/` (manifest `manifest.sha256`, one path base: that
directory); the emulation under `emu/` (its own manifest), the development run under `emu/dev-1/` (its own manifest and
tool copy).

## Answer (summary)

- [I] **First item: neither `PathPlanType1` nor `PathPlanType15` calls the search, and greedy-near's switch calls
  `PathPlanType1`, so all three go to P1.3a.** `PathSearchRun` has one call, 0x0067ADB4 in `PathPlanSearch`, and
  `PathPlanSearch` none: slots 0 and 16 of `g_PathPlanFuncs` are its only references (`p2-sites.txt`; `workspace/logs/r54a/p1-tables.txt`).
  Type 1 is its own best-first search, type 15 a line with wall following (§ 1). (fn:sub_0067B850_PathPlanType1@0x0067B850,
  fn:sub_0067C2D0_PathPlanType15@0x0067C2D0, fn:sub_00679ED0_PathPlanGreedyNear@0x00679ED0)
- [C] **The search is an iterative-deepening depth-first walk, not a best-first one**, by emulation to its return
  (run:2026-11-03-path-emu-2, 2 116 cases of families `real0`, `real16`, `stair`, `corr`, `open`, `rect`, 0 mismatches; the
  point list, the return, `ctx +0x14`, the start and target fields and, under type 16, the seed compared; the frame compared as
  scratch). There is no open list and no priority: at each node it takes the first direction of a fixed fan that passes
  the tests, so the fan's order is the tie-break. (fn:sub_0067A740_PathSearchWalk@0x0067A740)
- [C] **Cost and heuristic:** a straight step costs 2, a diagonal 3; `h = 2 max(|dx|, |dy|) + min(|dx|, |dy|)`, `f = g + h`; a
  step with `f > bound` is refused after its cell has taken `g`. (0x0067A875–0x0067A8E0)
- [C] **The bounds:** the first pass runs at `h0`, the start's `h` (type 16: `h0 + h0 / 2`); the bound rises by 5 and the walk restarts
  while the bound is below `max(first, ctx.b1C)`. `ctx.b1C` is path `+0x92`. With `b1C` at or below `h0` type 0 has **one
  pass at exactly `h0`**: only a route of the unblocked octile length is found. The cell grid is kept across passes.
  (0x0067AC3E–0x0067ACD4)
- [C] **The neighbour order** (§ 5): the root tries 8 directions from `want`, the octant to the target: `d, d+1, d−1, d+2, d−2,
  d+3, d−3, d+4`. A child tries 5, from a row of `g_PathSearchTurnRows` chosen by `(want − parent's direction) & 7`.
  (data:g_PathSearchTurnRows@0x006F17D8, fn:sub_0067A690_PathSearchAdvance@0x0067A690)
- [C] **How a walk ends:** at the target; at a node outside the rectangle, or with `h < 2 × ctx.refresh` (both are returned as
  found); or with nothing: the root spent, more than 10 000 passes of the loop, or the 900-node store full (the last ends the
  whole search, the others go on to the next bound). (0x0067A760–0x0067A786, 0x0067A8EC, 0x0067A9D7)
- [C] **The rectangle is the unit's room, or the rule of § 2 over the two rooms**, not their true union: a start can lie outside it, and the
  search then returns 0. (fn:sub_0067AD00_PathPlanSearch@0x0067AD00)
- [C] **The points:** walking back from the found node, a node is kept when its step differs from the step after it; the start is
  never kept. **A count outside 2..77 returns 0 with the list untouched**, so a route of one straight or diagonal segment
  fails, and 78 corners fail. `ctx.limit` is never read. (fn:sub_0067A9F0_PathSearchReduce@0x0067A9F0)
- [C] **Draws:** type 0 none. Type 16 steps the unit's seed (`unit +0x20`) once at each child and once at each turn, adding
  `g_PathSearchDrawAdd[low & 31]` to the direction (§ 7). (0x0067A641, 0x0067A6E1, 0x0067A983)
- [C] **At and past the 50 000 assert** (families `grid`, `over`, 120 boundary cases): `w h > 50 000` asserts (line 0x171);
  50 000 passes. But the clear covers `(w + 6)(h + 6)` cells, and the frame holds 50 010 before the saved `EBP`: a rectangle can pass
  the assert and overrun the frame (§ 9). Whether a stock room is that large is open. (0x0067AABC, 0x0067AAFB)
- [I] **The 14 byte stores are not path writes:** each stores into a quest's private data (§ 10). The object record of the target refresh
  is the `objects.bin` record (§ 10), closing the entry on `+0x13A` / `+0x13C`. (0x0058A98F, 0x005553E2)

## Leads used

No community source was compared (Phase 1b's). Used to locate code only: [ai/0001 § 8](../ai/0001-machinery.md#8-the-path-request) (the
slots and the type-16 gate), [path/0001](0001-pathplan-register.md) (the context, the record, the image).

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x0067AD00` | `sub_0067AD00_PathPlanSearch` | (ECX ctx) doubles `+0x14`, builds the rectangle, calls the run | I |
| `0x0067AAA0` | `sub_0067AAA0_PathSearchRun` | (ECX rect; ctx) the store on its frame, the bounds, the reduction | I |
| `0x0067A740` | `sub_0067A740_PathSearchWalk` | (EDI store; bound, ctx) one pass; the node it ends on, or 0 | I |
| `0x0067A690` | `sub_0067A690_PathSearchAdvance` | (EAX node; store) the node's next try; past its last, the parent's | I |
| `0x0067A630` | `sub_0067A630_PathSearchDirDraw` | (ESI node, EAX store) the try's direction, with the draw under type 16 | I |
| `0x0067A9F0` | `sub_0067A9F0_PathSearchReduce` | (EAX node, ECX ctx) the kept steps into the point list; the count or 0 | I |
| `0x00678D10` | `sub_00678D10_PathDirOctant` | `g_DirOctant[PathDirCell(a, b)]`: the first of the cell's three values | I |
| `0x006F17D8` | `g_PathSearchTurnRows` | 8 rows of 8 dwords: the turn before each try | I |
| `0x006F18D8` | `g_PathSearchDrawAdd` | 32 dwords: −2..2 six times, then −1, 1 | I |
| `0x006F1958` | `g_PathSearchStep8` | 8 × (dx, dy) dwords, read as words | I |

`re/types/path.h`: `PathSearchNode`, `PathSearchStore`.

## Walkthrough

### 1. The first item: types 1, 15 and greedy-near's switch

- [I] **`PathPlanType1`** (0x0067B850, frame 0x32F4): a test of the start's surroundings first (0x0067B740, return 0 when it
  fails), then a best-first search of its own: nodes of 0x38 bytes from a pool of 200 (0x0067B1C0), two 128-bucket hash tables and a list
  sorted by `f` (0x0067AED0, 0x0067AF40), eight neighbours (0x0067B440), the same `h` (0x0067ADC0), the reduction 0x0067B690 (a count of 1..77
  kept, unlike the search's 2..77). No call into `PathSearchRun`.
- [I] **`PathPlanType15`** (0x0067C2D0, frame 0x160): a Bresenham line (0x0067B9F0) of at most `max(limit, 40)` points when
  path `+0x58` is set, else `limit`; refused at 2 points or fewer; each blocked point sent to a wall follow with two
  walkers (0x0067BDF0, 0x0067BBF0, the tables 0x006F1E40–0x006F1F00); then 0x0067C1E0. No call into `PathSearchRun`.
- [I] **Greedy-near's switch** (0x00679F1A–0x00679F61): after `PathPlanGreedy`, a last point within `ctx.refresh` of the target and
  not the start returns the count; otherwise, when `dx² + dy² ≤ 324` from the start to the target (the plan's `< 325`), `PathPlanType1`
  (0x00679F4D), its non-zero count returned; on 0 with a greedy count, the greedy planner is run again and its count returned.
- [I] No RNG under types 1 or 15: `p2-rngcg-search.txt`, roots 0x0067AD00, 0x0067B850, 0x0067C2D0, fatal entries stopped: 46
  functions, no indirect call, the only LCG steps the three of § 7. All three planners **go to P1.3a**, which has them in its list.

### 2. `PathPlanSearch`: the radius and the rectangle

```c
// fn:sub_0067AD00_PathPlanSearch@0x0067AD00 (ECX ctx), trimmed, our names
ctx->refresh *= 2;                                      // u8 add, 0x0067AD15: 0, 1, 2 -> 0, 2, 4
own = RoomRectGet(ctx->pRoom);                          // x, y, w, h: DungeonRoom +0x4C
r = own;
if (ctx->pTargetRoom && ctx->pTargetRoom != ctx->pRoom) {
    o = RoomRectGet(ctx->pTargetRoom);
    if (o.x < own.x) { r.x = o.x;   r.w = own.w - o.x + own.x; }   // own's right end
    else             { r.x = own.x; r.w = o.w - own.x + o.x;   }   // o's right end, even when own's lies further
    if (o.y < own.y) { r.y = o.y;   r.h = own.h - o.y + own.y; }
    else             { r.y = own.y; r.h = o.h - own.y + o.y;   }
    if (r.w == own.w) { r.x -= 10; r.w += 20; }
} else { r.x -= 10; r.w += 20; }
if (r.h == own.h) { r.y -= 10; r.h += 20; }
return PathSearchRun(&r, ctx);
```

- [C] As above (families `real0`, `real16`, `rect`; control `union`, the true union, separates 11 cases of `rect` and passes none;
  `margin`, 9 for 10, separates 10 of `real0`, 37 of `real16`). (run:2026-11-03-path-emu-2)
- [C] So a target room right of or below the unit's, with the same left or top edge or one inside, and a smaller far end **shrinks** the rectangle
  below the unit's room, and a start beyond it ends the walk at the root: count 0, return 0. (run:2026-11-03-path-emu-2, family `rect`:
  `startout=24`, all with count 0; the other families' are 0)
- [I] Rooms on one row with equal rectangles get the 10-subtile margin only across (`r.h == own.h`), since `r.w` differs. A
  rectangle's `x1 = x + w` and `y1 = y + h` are **both inside** (§ 4), one column and row past the room's own end. (0x0067AD97, 0x0067ADA6, 0x0067A78F)

### 3. The store

- [I] `PathSearchRun`'s frame is `struct:PathSearchStore`: the root pointer, 900 nodes of 0x1C bytes, the node count, the rectangle as
  u16 words, stride `w + 6`, offsets `3 − x0` and `3 − y0`, 50 000 cells of 4 bytes at `+0x6290`, the draw flag and seed pointer at `+0x36FD0`
  and `+0x36FD4`, the root's initial image at `+0x36FD8`, the last bound at `+0x36FF4` (`EBP − 4`). (0x0067AAA3–0x0067AC52)
- [C] Cell `(x, y)` is `cells[(y + 3 − y0) × (w + 6) + 3 − x0 + x]`. It holds 0 (unseen), 1 (blocked) or the least `g` written (a later equal
  `g` is written again). The clear happens once per search; every pass reuses the cells (control `regrid`, cleared between passes,
  separates 1 of `real0`, 2 of `real16`, 10 of `open`, passes none). (0x0067A7EB–0x0067A80D, 0x0067AAFB)
- [C] A node has one child slot, kept across a backtrack (`+0x18`, 0x0067A8E6–0x0067A938), so the count of allocated nodes is the deepest
  chain of the pass + 1; the root and count are re-initialised before each pass (0x0067ACA2, 0x0067ACC5). (run:2026-11-03-path-emu-2, family `corr`)

### 4. The walk

```c
// fn:sub_0067A740_PathSearchWalk@0x0067A740 (EDI store; bound, ctx), one pass; our names
node = store->root; passes = 0;
for (;;) {
    if (node->pt == ctx->target) return node;
    if (++passes > 10000) return 0;
    if (node outside x0..x1, y0..y1) return node;                     // u16 compares, both ends inside
    n = node->pt + g_PathSearchStep8[node->dir];                      // u16 adds
    c = &cells[index(n)];
    if (*c == 0 && COLL_PatternTestBool(ctx->pRoom, n.x, n.y, ctx->pattern, ctx->testMask)) {
        *c = 1;  goto next;
    }
    g = node->g + (n.x != x && n.y != y ? 3 : 2);                     // u16
    if (*c != 0 && *c < (u32)(s16)g) goto next;                       // 1 (blocked) is below every g
    *c = (s16)g;                                                      // written before the bound test
    h = 2 max(|dx|, |dy|) + min(|dx|, |dy|);  f = (u16)(g + h);       // n to the target
    if ((s16)f > bound) goto next;
    child = node->child;
    if (!child) {
        if (store->nNodes == 900) return 0;
        child = zeroed nodes[store->nNodes++];  child->parent = node;  node->child = child;
    }
    child->h = h; child->g = g; child->f = f; child->tries = 0;
    want = PathDirOctant(n, ctx->target);
    child->turn = &g_PathSearchTurnRows[(want - node->dir) & 7][0];
    child->dir = (node->dir + child->turn[0] [+ draw under type 16]) & 7;
    child->pt = n;
    node = child;
    if ((s16)node->h < ctx->refresh) return node;                     // ctx->refresh already doubled
    continue;
next:
    node = PathSearchAdvance(node);
    if (!node) return 0;
}
```

- [C] As above: each statement is held by the families' 0 mismatches, with these controls failing what they separate
  (`check.txt`): `h` (max + 2 min) 234 of `real0`; `cost` (diagonal 2) 133; `fgt` (`f ≥ bound`) 216; `cellle` (an equal `g` refused) 3 of `real0`,
  217 of `real16`, 7 type-0 cases of `open`; `rectend` (the rectangle ignored) 10 of `real0`, 40 of `real16`; `radius` (no doubling) 46 of
  `real0`; `passes` (20 000) 26 of `open`, 2 of them type 0; `nodes` (901) 16 of `corr`, 1 type 0. (run:2026-11-03-path-emu-2)
- [C] A try that a test refuses and a try that passes both count one pass of the loop, so the 10 000 counts tries, not nodes. Outcomes of the 2 116 cases are
  listed in `check.txt` (`none:passes` 72 of `real0`, 81 of `real16`, 43 of `open`, 64 of `rect`). (run:2026-11-03-path-emu-2)
- [C] A cell's blocked mark uses the unit's room as the hint for every step, so a cell in a room outside that room's near list is
  "no room" and blocked, however large the rectangle. The tests run inside each case, edge branches included.
  (fn:COLL_PatternTestBool@0x0064D910, fn:COLL_PlusTestBool@0x0064D4E0, fn:COLL_RectTestBool@0x0064CF50, run:2026-11-03-path-emu-2)
- [I] Reaching a node outside the rectangle returns it as found: the route ends one step outside the rectangle, short of the target.
  What the caller then does with a shorter route is `PathPlan`'s tail (path/0001 § 6). (0x0067A796–0x0067A7C0)

### 5. The neighbour order

- [C] `g_PathSearchStep8` is `(1,0), (1,1), (0,1), (−1,1), (−1,0), (−1,−1), (0,−1), (1,−1)` (x, y; index = direction). The root's
  `dir` is `want & 7` (0x0067ABF5), its row 0, `tries` −3. `PathSearchAdvance` before each next try adds the next entry of the node's row to its `dir`. A
  node is spent when `tries` reaches 5: the root tries 8 directions, a child 5. (data:g_PathSearchStep8@0x006F1958, run:2026-11-03-path-emu-2)
- [C] The rows give these tries, as offsets from `d`, the parent's direction when the child was made (the root: from `want`).
  Row index is `(want − d) & 7`, `want` the child's own octant to the target (control `row`, the difference negated, separates 246 of
  `real16`, 40 of `open`, 85 of `rect`, 5 type-0 cases each of `open` and `rect`, passes none; `tries`, 8 for a child, 231, 39). Under a tight bound the fan's
  order does not show: `row` and `tries` separate no `real0` case, so type 0 rests on `open` and `rect` here. (data:g_PathSearchTurnRows@0x006F17D8, run:2026-11-03-path-emu-2)

| row | turn entries used | tries, from `d` |
|---:|---|---|
| root (0) | 0, 1, 6, 3, 4, 5, 2, 7 | `0, +1, −1, +2, −2, +3, −3, +4` |
| 0 | 0, 1, 6, 3, 4 | `0, +1, −1, +2, −2` |
| 1 | 0, 1, 6, 3, 1 | `0, +1, −1, +2, +3` |
| 2 | 0, 1, 1, 1, 1 | `0, +1, +2, +3, +4` |
| 3 | 1, 1, 1, 1, 1 | `+1, +2, +3, +4, +5` |
| 4 | 6, 4, 3, 6, 1 | `−2, +2, −3, +3, +4` |
| 5 | 7, 7, 7, 7, 7 | `−1, −2, −3, −4, −5` |
| 6 | 0, 7, 7, 7, 7 | `0, −1, −2, −3, −4` |
| 7 | 0, 7, 2, 5, 7 | `0, −1, +1, −2, −3` |

- [I] The first try keeps the parent's direction in rows 0, 1, 2, 6 and 7: the walk runs straight until the bound or a wall turns it. (data:g_PathSearchTurnRows@0x006F17D8)
- [C] **Backtrack:** past a node's fifth try the walk goes to the parent, which turns once and counts its try, repeating while a parent is spent too; at
  the root spent it returns 0. (fn:sub_0067A690_PathSearchAdvance@0x0067A690, run:2026-11-03-path-emu-2)

### 6. The bounds and the reduction

```c
// fn:sub_0067AAA0_PathSearchRun@0x0067AAA0, after the store is set; our names
first = (s16)h0;
if (type == 0)       last = max(first, b1C);
else if (type == 16) { first = (s16)(h0 + h0 / 2); last = max(first, b1C); }   // the only two types with this planner
else                 last = first;
do {
    root = rootInit;  node = Walk(first, ctx);  first += 5;
    if (!node && nNodes == 900) break;
    nNodes = 1;
} while (!node && first < last);
n = node ? PathSearchReduce(node, ctx) : 0;
return n >= 78 ? 0 : n;
```

```c
// fn:sub_0067A9F0_PathSearchReduce@0x0067A9F0; our names
n = 0;  prev = (-2, -2);
for (; node && n < 78; node = node->parent)
    if (node->parent && (step = node->pt - node->parent->pt) != prev) { buf[n++] = node->pt; prev = step; }
if (n < 2 || n > 77) return 0;
memcpy(path->points, reversed(buf), n * 4);                       // +0x9C
return n;
```

- [C] As above: `step` (4 for 5) separates 2 of `real0`, 17 of `open`; `half` (`2 h0`) 253 of `real16`, 38 of `open`; `min2` (one point accepted) 81 of `real0`,
  4 of `real16`, 3 of `stair`; `max77` (78 accepted) 42 of `stair`. The list keeps the poison the case wrote when the return is 0. The list ends at the node the walk
  ended on; the start is not in it. `+0x28` and the other tail fields are `PathPlan`'s (path/0001 § 6). (run:2026-11-03-path-emu-2)
- [C] A route of one segment returns 0: `points<2:target` 9 of `real0`, 1 of `real16`, 3 of `stair` (route length 1). A straight or exactly diagonal free line between two points
  is therefore refused by this planner. (0x0067AA6B–0x0067AA72, run:2026-11-03-path-emu-2)
- [C] Neither planner reads `ctx.limit` (`+0x18`), `ctx.size` (`+0x24`) or `+0x10`, and neither reads the path except `+0x30` under type 16: they stay undeclared in every
  case with no traced read over 2 116 cases (`traced=0`). (run:2026-11-03-path-emu-2)

### 7. Type 16's draws

- [C] `PathSearchRun` sets the flag and the seed pointer `path->unit + 0x20` for type 16 only (0x0067AB74–0x0067ABA4). The step is the game's LCG, `v = 0x6AC690C5 · lo + hi`, `lo = low 32`, `hi = high
  32` (rng/0001), inlined at three sites: at a child, before its first try (0x0067A983); in `PathSearchAdvance` for the parent's turn on a backtrack (0x0067A6E1); in `PathSearchDirDraw` for a node's own next try
  (0x0067A641, which a node's fifth try skips: `tries < 4` only). `dir = (dir + turn entry + g_PathSearchDrawAdd[lo & 31]) & 7`. The control `draw` separates all 400 of `real16`; the exit seed is compared in every
  type-16 case (`check.txt` `draws=`: 994 022 in `real16`). (run:2026-11-03-path-emu-2, data:g_PathSearchDrawAdd@0x006F18D8)
- [I] Type 16's reach is unchanged: no server code plans it but two unreferenced functions (path/0001 § 11); Phase 2 watches it with a break line. (fn:sub_00663E00_PathPlanType16A@0x00663E00)

### 8. Other functions in the range

- [I] 0x0067A4A0, 0x0067A550, 0x0067A590, 0x0067A5D0 and 0x0067A5F0 have no reference of any kind (`p2-findptr.txt`, counts 0; `p2-sites-helpers.txt`): the last four are uninlined copies of the
  octile, the node allocation, the row pointer and the rectangle test, the first a segment check over a path's points with 0x0067A420. Not reached by this planner.

### 9. The limits, against integer widths and slots

From `p2-bounds.txt` (`tools/path_emu2.py bounds`), each with its emulation where a case can reach it:

- [C] **Points: at most 77, against 78 slots.** The reduction stops at 78 stored into a 78-slot local (0x148 − 0x10 = 312 bytes), keeps 2..77, returns 0 at 78, and `PathSearchRun` tests `< 78` again
  (0x0067ACE9). 77 × 4 = 308 bytes into the record's 312. `stair`: 77 returned (`maxpoints=77`), 78 refused (`points78:target` 42). A route of 78 corners fits inside `PathPlan`'s window: a staircase of `dx` 78, `dy` 39 has `g = h0 = 195`. (run:2026-11-03-path-emu-2)
- [C] **The node store is out of reach under `PathPlan`'s window.** `|dx|, |dy| ≤ 100` gives `h0 ≤ 300`; the last bound is at most `max(300, 254) = 300` (type 0) or `max(450, 254) = 450` (type 16); `g ≤ bound` and each step costs at least 2, so
  the depth is at most 150 or 225 and the nodes 151 or 226, below 900. Past the window, `corr` reaches it: 899 steps fit, the 900th step's child returns 0 and ends the search (`none:nodes` 22, `maxnodes=900`). The largest counts
  elsewhere: `real16` 103 and `rect` 130, inside the window; `open` 150, whose targets lie up to 126 off. (run:2026-11-03-path-emu-2, fn:sub_00649970_PathPlan@0x00649970)
- [C] **The assert and the frame.** `w h` is a signed product against 50 000 (0x0067AAB9–0x0067AAC3): 50 000 passes, 50 001 asserts with line 0x171 (35 assert cases in `grid`, 73 at the clear with length `4 (w + 6)(h + 6)`). The grid has 50 000 cells to the flag, and `EBP` lies 50 010 cells from its start: **a clear of 50 011 cells zeroes the saved `EBP`,
  50 012 the return address, 50 013 the context argument** (`over`, 12 cases, the three words dumped after the clear). [I] The next read of the argument, 0x0067AB67, then loads 0 and faults at 0x0067AB74. Square rectangles: 217 × 217 fits (49 729 cells), 218 × 218 passes the assert (47 524) and overruns (50 176); 223 × 223 passes (49 729), 224 × 224 asserts. The smallest passing product that overruns is 1 × 7 139. For a same-room rectangle (room + 20), a room of 197 × 197 fits and 198 × 198 overruns. (run:2026-11-03-path-emu-2)
- [C] **The signed product wraps** from 46 341² (2 147 488 281 → −2 147 479 015), which passes the assert; 46 340² (2 147 395 600) still fits. Cases `(46340, 46340)`, `(46341, 46341)`, `(65536, 65536)`, `(65536, 32768)` in `grid` show it at the boundary. No such room is known: it needs a rectangle of 46 341 subtiles. (run:2026-11-03-path-emu-2)
- [I] **`g` and `f` are u16 read as i16.** Under the store `g ≤ 899 × 3 = 2 697`; `f` stays below 32 768 while `h` does, which holds in any rectangle under 10 000 subtiles a side. No wrap is reached by a case. (0x0067A88B–0x0067A8DD)
- [I] **The bounds of a search:** at most 51 passes (`h0` ≥ 2, `b1C` ≤ 255), each at most 10 000 tries. `real0` reached 14 passes and 19 046 tries in a case, `open` 38 and 57 797 (case writers resample above 25 000 and 60 000 tries, a run-time limit of the emulator, not of the game). (0x0067ACB0, 0x0067A77E)

### 10. The byte stores and the object record

- [I] **The 14 byte stores** (`p2-stores.txt`, recounted from `p2-writers-9x.txt`; the range is 0x0058929F–0x00594647, one store below the 0x0058AB9C that path/0001 and the plan named) are all in quest functions: 0x90: 0x0058AB9C, 0x0058E3B6, 0x0058E4B0, 0x00594647; 0x91: 0x0058929F, 0x005894A1, 0x0058EB4B, 0x00594513; 0x92: 0x0058A71F, 0x0059430C, 0x00594601; 0x93: 0x0058951A, 0x0058A679, 0x00592243. Thirteen load the base from `[x + 0x18]` in the same function, `pPrivate` of the quest record `QUESTS_FindById` returns (`re/types/quests.h`); 0x0058929F's `EDI` is a register argument of the fragment at 0x005891D0, loaded the same way at its caller 0x0058A98F (`p2-sites-5891d0.txt`, the other caller 0x005897C6 passes `EBX`, whose stores at `+0xAD` and `+0x84` match those at 0x0058A993 and 0x0058A99A). None is a path record. (fn:QUESTS_FindById@0x00543640)
- [I] **The object record of the target refresh is the `objects.bin` record.** The readers 0x00621A70 and 0x00621AC0 read `unit +0x14 → +0x00 → +0x13A / +0x13C` for a unit of type 2; `SUnitCreate` allocates the 0x38-byte data at `unit +0x14` and stores `OBJECTS_GetRecord(class)` at its `+0x00` (0x005553C8–0x005553E2), and `OBJECTS_GetRecord` is `0x0096D470 + class × 0x1C0` (0x00640EC8), the table's 448-byte record ([Objects](../../tables/Objects.md)). So `+0x13A` is `IsDoor`, `+0x13C` `Orientation`. (fn:OBJECTS_GetRecord@0x00640E90, fn:sub_00555230_SUnitCreate@0x00555230, tbl:Objects.txt:IsDoor, tbl:Objects.txt:Orientation)

### 11. The emulation

- **Entry and images (P1.1 review ruling 2).** Every case enters `PathPlanSearch` with a declared context in `ECX`. Real blocks: `tools/collision.py`'s predicted cells of 36 rooms of level 75, 36 of 76, 10 of 29 and 36 of 106 from three kept run:2026-10-14-collision logs (`grids.txt`; 362, 44 and 215 model checks, 0 failures), each once as predicted and once with 60 seeded unit marks per room; the case writer keeps the start clear of marks (the unit's own marks absent); targets fall where they fall, so those off every mark stand for a path with flag `0x800`, those on one for a path without it (the context does not carry the flag). Near lists are every touching room (declared); a cell outside them is no room. Synthetic rooms for the branches stock cells seldom reach. The edge branches run: the "one subtile inside a room" domain is gone.
- **The frame** stays on the declared stack as scratch through `re/ghidra_scripts/EmuScratch.java` (`EmuBoundary.java` plus the check): a read of a stack byte before the case wrote it prints a `U` line, and the top 256 KiB of the stack is filled per case with a different byte. Accounted: `_chkstk`'s page probes (0x006831D7) and 0x0067AB46, a dword read covering 2 bytes (the stride, not yet written) of which the store at 0x0067AB78 keeps the low word's sum only; every other `U` line would fail its case, and there are none (`scratch=` in `check.txt`).
- **Controls and outcomes** are §§ 2–7's; the site control passes 0 of the 120 boundary cases. No symbol raise (ADR-0015 scope, review-fixes rule 14).
- **Not covered:** `PathPlan`'s tail after the planner (path/0001 § 6), what the game stores in a real context, a target `+0x13A` step, and every other planner. A family that could not be emulated: none in this batch.

## Data touched

- `struct:PathPlanCtx` (`+0x00`, `+0x04`, `+0x08`, `+0x0C`, `+0x14`, `+0x1C`, `+0x20`, `+0x28`, `+0x2C`, `+0x30`), `struct:PathRequestFields` (`+0x9C`), `struct:DynPathColl` (`+0x30`), `struct:DungeonRoom` (`+0x00`, `+0x20`, `+0x24`, `+0x4C`), `struct:CollMap`, `struct:PathSearchStore`, `struct:PathSearchNode`.
- Image tables: `data:g_PathSearchTurnRows@0x006F17D8`, `data:g_PathSearchDrawAdd@0x006F18D8`, `data:g_PathSearchStep8@0x006F1958`, `data:g_DirOctant@0x006F1518`.
- `tbl:Objects.txt:IsDoor`, `tbl:Objects.txt:Orientation` (§ 10).

## Dead ends

- Filtering the `grid` and `over` memory specs by hand to drop empty `const bytes` lines of the development run also dropped the `observe` lines: 88 + 8 cases ran on past the clear and stopped. The tool was fixed and the two families re-run under the same names in `emu/dev-1/`, so those first outputs are not kept. `emu/dev-1/path_emu2.py.rev` is the revision of that re-run; the kept revision differs only in the controls' `_type0` print, `bounds` and `startout`.
- Expecting `row` and `tries` to separate `real0`: under a bound of exactly `h0` the refused tries are the same ones in any order (§ 5). Moved to the type-0 counts of `open` and `rect`, printed as `*_type0=`.

## Open questions

- `[L]` Whether any stock room or pair of rooms makes a rectangle whose `(w + 6)(h + 6)` passes 50 010: the observed rooms are 40 and 60 subtiles on a side. A scan of the largest active room rectangle (DS1 sizes against `DUNGEON_RoomCreate`) would settle it; 198 × 198 subtiles is the same-room threshold.
- `[L]` What a get-hit request's `ctx.b1C` is on the server: `+0x92` is written in the path module only at creation (70 a player) and by `PathSetByte92`, so a monster's would be 0 and type 0 one pass at `h0`; Phase 2's `PLC` line logs it.
- `[L]` `PathPlanType1`, `PathPlanType15`, greedy-near in full (P1.3a).

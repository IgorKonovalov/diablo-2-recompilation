"""Animate three planners of the path spec on one toy grid (docs/specs/path/search.md sections A, I, J and L):
the search of types 0 and 16 (an iterative-deepening depth-first walk), the random walk (type 10) and the spiral (type 14).
Schematic only (ADR-0036): boxes, text and lines in our own palette; the grid is a hand-drawn toy of our own.

Usage:
  python3 -I tools/path_anim.py <root> [--mode search|walk|spiral] [--b1c N] [--limit N] [--seed S]
        [--theme dark|light] [--out DIR] [--schematic]

<root> is the data tree every illustration tool takes first (workspace/merged); this tool reads no game file and ignores
it. --mode search (default): one room, 16 by 9 subtiles, a wall with a gap, a start and a target; the search of type 0
with the caller's last bound --b1c N (default 33; the passes run at h0, h0 + 5, ... while below it). --mode walk: the
random walk of type 10 from the toy start with the path's limit --limit N (the byte +0x91, default 12; the walk takes
N / 2 steps) on the seed --seed S (decimal or 0x hex, default 0xC0FFEE; an illustrative input, never a game seed).
--mode spiral: the 77-point spiral of type 14 around the start (default; --limit does not apply). The walk and the
spiral read no grid, so they cross the wall. --theme: dark or light palette values. --schematic is accepted for the
export builder and changes nothing. DIR defaults to workspace/render/anim/path-<mode>-schematic/ and must stay under
workspace/. Outputs: frame-NNN.png, path.gif, index.html, steps.json, schematic.json (ADR-0036).

The search mode follows search L1 to L3 for type 0 with the toy's numbers (the ctx's near-target stop is off: refresh 0;
the unit's room is the target's room); the walk is tools/rng.py's step with search I's add table; the spiral is search
J with the sine table computed here from sin (the table is within 1.8e-07 of it; the toy shows the cells, not the table).
tools/test_schematic_kit.py compares the search with the emulation model of tools/path_emu2.py (its Search class, run on
the same toy room with the tables of the spec) and the walk with the formula of search I. Times are frames, none is shown.
Not shown: type 16's draws, the rectangle's rule for two rooms, a real room's collision masks, the list's later use by the
unit. Stdlib only.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import rng  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 500
CAP_Y = 420
GW, GH, CS = 16, 9, 30                 # the toy room: 16 by 9 subtiles, drawn at 30 pixels a cell
GX, GY = 20, 56
WALL = {(7, y) for y in range(1, 9)}   # a wall at x = 7 with a gap at y = 0
START, TARGET = (2, 4), (13, 4)
HELP = """<li>The grid is a toy room of 16 by 9 subtiles drawn for this page. Dark cells are walls; the cells outside the room count as walls too.</li>
<li>Search: the walk runs depth first under a bound on the cost; if it finds no route the bound grows by 5 and it runs again over the same cell store.</li>
<li>Random walk and spiral: both ignore the grid. The walk keeps its first direction plus or minus one or straight; the spiral grows around the start.</li>
<li>Every value is computed by our model for the toy numbers given, not observed in the game.</li>"""

# search A2, A3, L3 (the stock tables as the spec and docs/tables/PathDirTables state them; ADR-0031)
STEP8 = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
TURN_ROWS = ((0, 1, 6, 3, 4, 5, 2, 7), (0, 1, 6, 3, 1, 3, 6, 1), (0, 1, 1, 1, 1, 1, 2, 7), (1, 1, 1, 1, 1, 3, 6, 1),
             (6, 4, 3, 6, 1, 3, 2, 7), (7, 7, 7, 7, 7, 5, 2, 7), (0, 7, 7, 7, 7, 5, 2, 7), (0, 7, 2, 5, 7, 5, 2, 7))
DIR_OCTANT = (5, 4, 4, 4, 3, 6, 5, 4, 3, 2, 6, 6, 6, 2, 2, 6, 7, 0, 1, 2, 7, 0, 0, 0, 1)   # column 0, by PathDirCell
ADD_WALK = [-1, 0, 1] * 10 + [-1, 1]                                                   # search I step 1
DIR_NAME = ("RIGHT", "DOWN RIGHT", "DOWN", "DOWN LEFT", "LEFT", "UP LEFT", "UP", "UP RIGHT")


# ---------------------------------------------------------------- the model
def dir_cell(a, b):
    """search A2 PathDirCell."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    if abs(dx) >= 2 * abs(dy):
        dy = -1 if dy < 0 else dy & 1
    elif abs(dy) >= 2 * abs(dx):
        dx = -1 if dx < 0 else dx & 1
    dx, dy = max(-2, min(2, dx)), max(-2, min(2, dy))
    return 5 * dx + dy + 12


def octile(a, b):
    """search A3 PathOctile."""
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return 2 * max(dx, dy) + min(dx, dy)


def blocked(p, walls=WALL):
    """search A1, pattern 0 on the toy room: a wall cell, or a cell outside the room (no room: blocked)."""
    return not (0 <= p[0] < GW and 0 <= p[1] < GH) or p in walls


class Node:
    __slots__ = ("pt", "g", "h", "f", "d", "ptr", "n", "parent", "child")

    def __init__(self):
        self.child = self.parent = None


def reduce_route(node):
    """search L2 Reduce: from the end back, a node is kept when its step differs from the kept step after it."""
    buf, prev = [], (-2, -2)
    while node and len(buf) < 78:
        if node.parent:
            step = (node.pt[0] - node.parent.pt[0], node.pt[1] - node.parent.pt[1])
            if step != prev:
                buf.append(node.pt)
                prev = step
        node = node.parent
    if len(buf) < 2 or len(buf) > 77:
        return []
    return buf[::-1]


def search(s=START, t=TARGET, b1c=33, walls=WALL):
    """search L2 and L3 for type 0 on the toy room. -> dict: h0, passes (one record each: bound, tries, nodes, result chain
    or None, the cell store after it, the first descent), route (the corner list), points."""
    store = {}                                   # 0 unseen (absent), 1 blocked, else the least g written; kept across passes
    h0 = octile(s, t)
    first, last = h0, max(h0, b1c)
    passes = []
    d0 = DIR_OCTANT[dir_cell(s, t)] & 7
    nn = 1
    while True:
        root = Node()
        root.pt, root.g, root.h, root.f, root.d, root.ptr, root.n = s, 0, h0, h0, d0, 0, -3
        rec = dict(bound=first, tries=0, chain=None, first_descent=None, end=None)
        node = root
        count = 1
        tries = 0
        desc_done = False
        result = None
        ended = False
        while not ended:
            if node.pt == t:
                rec["end"], result = "target", node
                break
            tries += 1
            if tries > 10000:
                rec["end"] = "tries"
                break
            sx, sy = STEP8[node.d]
            n = (node.pt[0] + sx, node.pt[1] + sy)
            c = store.get(n, 0)
            adv = False
            if c == 0 and blocked(n, walls):
                store[n] = 1
                adv = True
            else:
                g = node.g + (3 if n[0] != node.pt[0] and n[1] != node.pt[1] else 2)
                if c != 0 and c < g:
                    adv = True
                else:
                    store[n] = g
                    h = octile(n, t)
                    f = g + h
                    if f > first:
                        adv = True
                    else:
                        child = node.child
                        if child is None:
                            if count == 900:
                                rec["end"] = "nodes"
                                ended = True
                                break
                            count += 1
                            child = Node()
                            child.parent = node
                            node.child = child
                        child.h, child.g, child.f, child.n = h, g, f, 0
                        want = DIR_OCTANT[dir_cell(n, t)]
                        row = (want - node.d) & 7
                        child.ptr = row * 8
                        child.d = (node.d + TURN_ROWS[row][0]) & 7
                        child.pt = n
                        node = child
                        continue
            if adv:
                if not desc_done:
                    desc_done = True
                    ch, q = [], node
                    while q:
                        ch.append(q.pt)
                        q = q.parent
                    rec["first_descent"] = ch[::-1]
                # Advance (search L3)
                while True:
                    if node.n < 4:
                        node.ptr += 1
                        node.d = (node.d + TURN_ROWS[node.ptr // 8][node.ptr % 8]) & 7
                    node.n += 1
                    if node.n != 5:
                        break
                    done = False
                    while True:
                        if node.parent is None:
                            done = True
                            break
                        node = node.parent
                        node.ptr += 1
                        node.d = (node.d + TURN_ROWS[node.ptr // 8][node.ptr % 8]) & 7
                        node.n += 1
                        if node.n != 5:
                            break
                    if done:
                        node = None
                    break
                if node is None:
                    rec["end"] = "exhausted"
                    break
        rec["tries"], rec["nodes"] = tries, count
        rec["store"] = dict(store)
        if result is not None:
            ch, q = [], result
            while q:
                ch.append(q.pt)
                q = q.parent
            rec["chain"] = ch[::-1]
        passes.append(rec)
        first += 5
        if result is not None or (rec["end"] == "nodes"):
            break
        if not first < last:
            break
    route = []
    if passes[-1]["chain"]:
        q = result
        route = reduce_route(q)
    return dict(h0=h0, passes=passes, points=route, found=bool(passes[-1]["chain"]), b1c=b1c, first=h0, last=last)


def walk_points(limit, seed, start=START):
    """search I for the toy: -> (d, [(k, low word, high word, add, dir, point)], points); the position's subtile is the start."""
    n = limit >> 1
    cur = start
    lo, hi = seed & 0xFFFFFFFF, 666
    d = DIR_OCTANT[dir_cell(start, TARGET)]      # search I step 4: the first of PathDirRow toward the path's target, once
    pts, log = [], []
    for k in range(n):
        v = rng.MULT * lo + hi
        lo, hi = v & 0xFFFFFFFF, v >> 32
        add = ADD_WALK[lo & 31]
        dr = (d + add) & 7
        pts.append(cur)
        log.append((k, lo, hi, add, dr, cur))
        cur = (cur[0] + 2 * STEP8[dr][0], cur[1] + 2 * STEP8[dr][1])
    pts.append(cur)
    return d, log, pts


def sine(i):
    return math.sin(2 * math.pi * (i & 0x1FF) / 512)


def spiral_points(start=START, count=77):
    """search J: the 77 points, each the cell the position reaches when its whole part changes (start fraction 0x8000)."""
    fx, fy = (start[0] << 16) + 0x8000, (start[1] << 16) + 0x8000
    lx, ly = fx, fy
    r = a = 0
    pts, it = [], []
    while True:
        r += 0x2580
        a += 16
        X = int(sine(a + 0x80) * float(r))
        Y = int(sine(a) * float(r))
        x, y = fx + X, fy + Y
        if x >> 16 != lx >> 16 or y >> 16 != ly >> 16:
            pts.append((x >> 16, y >> 16))
            it.append((len(it) + 1, r, a, X, Y))
            lx, ly = x, y
        if len(pts) >= count:
            break
    return pts, a >> 4


# ---------------------------------------------------------------- the frames
def build(mode, b1c, limit, seed, theme):
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    PX = 520                                     # the right-hand panel

    def header(s):
        k.text(20, 12, s, "acc", 2, True)

    def cxy(p):
        return GX + p[0] * CS, GY + p[1] * CS

    def grid(fills=None, labels=None, marks=True):
        """The toy room: free cells, walls, S and T; fills {cell: (fill, edge)}, labels {cell: (text, colour)}."""
        fills, labels = fills or {}, labels or {}
        for y in range(GH):
            for x in range(GW):
                p = (x, y)
                if p in WALL:
                    fl, ed = "dim", "grey"
                else:
                    fl, ed = fills.get(p, ("panel", "grey"))
                if p in fills and p in WALL:
                    fl, ed = fills[p]
                k.rect(GX + x * CS, GY + y * CS, CS + 1, CS + 1, fl)
                k.outline(GX + x * CS, GY + y * CS, CS + 1, CS + 1, ed)
        if marks:
            for p, lab, col in ((START, "S", "acc"), (TARGET, "T", "blue")):
                x, y = cxy(p)
                k.outline(x, y, CS + 1, CS + 1, col, 3)
                k.text_c(x + CS // 2 + 1, y + (CS - 14) // 2 + 1, lab, col, 2, True)
        for p, (lab, col) in labels.items():
            x, y = cxy(p)
            if p in (START, TARGET):                 # beside the S or T letter, at the cell's lower right
                k.text(x + CS - 2 - K.text_w(lab, 1), y + CS - 9, lab, col, 1)
            else:
                k.text_c(x + CS // 2 + 1, y + (CS - 7) // 2 + 1, lab, col, 1)

    def panel(rows, y0=56, dy=28):
        for i, r in enumerate(rows):
            s, col, bold = (r + (False,))[:3] if isinstance(r, tuple) else (r, "txt", False)
            k.text(PX, y0 + i * dy, s, col, 2, bold)

    def under(rows):
        for i, r in enumerate(rows):
            s, col = r if isinstance(r, tuple) else (r, "dim")
            k.text(20, 332 + i * 24, s, col, 2)

    def put(cap, text, calc):
        k.caption(cap, CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(text=text, calc=calc))

    if mode == "search":
        res = search(b1c=b1c)
        ps = res["passes"]
        h0 = res["h0"]
        bounds = [p["bound"] for p in ps]
        allb = [h0 + 5 * i for i in range(10) if h0 + 5 * i < max(h0 + 1, res["last"])] or [h0]
        # ---- the toy
        header("SEARCH OF TYPE 0 ON A TOY ROOM, 16 BY 9 SUBTILES")
        grid()
        panel([("START S (%d,%d)" % START, "acc", True), ("TARGET T (%d,%d)" % TARGET, "blue", True),
               ("H0 = 2 * %d + %d = %d" % (11, 0, h0), "txt", True), "THE OCTILE LENGTH IF NOTHING BLOCKS",
               "BOUNDS: " + ", ".join(str(b) for b in allb[:4]) + (", ..." if len(allb) > 4 else ""),
               "THE LAST BOUND ASKED FOR: %d" % res["last"]])
        under(["THE WALK IS DEPTH FIRST UNDER A BOUND ON G + H; NO OPEN LIST.", "STRAIGHT STEP COSTS 2, DIAGONAL 3.",
               "CELLS OUTSIDE THE ROOM COUNT AS WALLS."])
        put("A toy room 16 by 9 subtiles with a wall, a start S and a target T. The octile length h0 is %d, so the first "
            "bound is %d; the walk runs again at +5 while the bound is below %d (search L1 to L3)." % (h0, h0, res["last"]),
            "The toy room: start, target, the octile length %d and the bounds the passes will use." % h0,
            ["search A3: PathOctile = 2 max(dx, dy) + min(dx, dy) = 2 * 11 + 0 = %d." % h0,
             "search L2: first = h0 = %d, last = max(first, b1C) = %d; each pass adds 5 to the bound." % (h0, res["last"])])
        # ---- the first descent of pass 1
        fd = ps[0]["first_descent"]
        fills = {p: ("room", "edge") for p in fd[1:]}
        bl = None
        # the first blocked cell the first descent tried: the cell after its last point along that node's direction
        header("PASS 1, BOUND %d: THE FIRST DESCENT" % ps[0]["bound"])
        grid(fills)
        panel([("THE FIRST DIRECTION: RIGHT,", "txt", True), ("TOWARD THE TARGET", "txt", True),
               "THE ROOT TRIES 8 DIRECTIONS", "A CHILD TRIES 5", "",
               ("%d STEPS RIGHT, THEN A WALL" % (len(fd) - 1), "bad", True)])
        under(["EACH CHILD TRIES THE PARENT'S DIRECTION FIRST, SO THE WALK RUNS STRAIGHT", "UNTIL THE BOUND OR A WALL TURNS IT.",
               "A WALL CELL IS MARKED BLOCKED IN THE CELL STORE."])
        put("Pass 1, bound %d: each node tries its parent's direction first, so the walk runs straight right from S to the "
            "wall at x = 7 (search L3)." % ps[0]["bound"],
            "Pass 1: the walk runs straight toward the target until the wall.",
            ["search L3: step 6 takes n = point + step[dir]; step 8 marks a blocked unseen cell 1 and tries the next direction.",
             "search L3: the first try keeps the parent's direction in rows 0, 1, 2, 6 and 7."])
        # ---- the end of each pass
        for i, p in enumerate(ps):
            st = p["store"]
            fills = {}
            labels = {}
            for c, v in st.items():
                if v == 1:
                    fills[c] = ("qd_rare", "bad")
                elif c not in (START,):
                    fills[c] = ("room", "edge")
                    labels[c] = (str(v), "txt")
            found = p["chain"] is not None
            if found:
                for c in p["chain"][1:]:
                    fills[c] = ("qd_set", "good")
            header("PASS %d, BOUND %d: %s" % (i + 1, p["bound"], "THE TARGET IS REACHED" if found else "NO ROUTE UNDER THE BOUND"))
            grid(fills, labels)
            seen = sum(1 for v in st.values() if v != 1)
            blk = sum(1 for v in st.values() if v == 1)
            panel([("BOUND %d" % p["bound"], "acc", True), "TRIES IN THIS PASS: %d" % p["tries"],
                   "NODES USED: %d OF 900" % p["nodes"], "CELLS WITH A G: %d" % seen, "CELLS MARKED BLOCKED: %d" % blk, "",
                   (("TARGET REACHED" if found else "EVERY TRY EXHAUSTED"), "good" if found else "bad", True)])
            if found:
                under(["NUMBERS: THE LEAST G WRITTEN IN EACH CELL. GREEN CELLS: THE ROUTE.",
                       "THE STORE IS KEPT BETWEEN PASSES; A LOWER G IN A CELL BLOCKS ENTRY."])
            else:
                under(["THE NUMBERS ARE THE LEAST G WRITTEN IN EACH CELL.",
                       "THE NEXT PASS RAISES THE BOUND BY 5 AND KEEPS THESE CELLS."])
            cap = ("Pass %d, bound %d: %d tries and %d nodes, %s." % (
                i + 1, p["bound"], p["tries"], p["nodes"], "the target is reached" if found else
                "no route within the bound; the next pass raises it by 5"))
            put(cap, "Pass %d at bound %d: %s." % (i + 1, p["bound"], "the target is reached" if found else "no route"),
                ["search L3: tries = %d (a refused try and a passing one both count), nodes = %d." % (p["tries"], p["nodes"]),
                 "search L2: first = first + 5 = %d for the next pass." % (p["bound"] + 5)] if not found else
                ["search L3: node.pt = target ends the walk; tries = %d, nodes = %d." % (p["tries"], p["nodes"])])
        # ---- the reduced route
        pts = res["points"]
        header("THE ROUTE REDUCED TO ITS CORNERS")
        fills = {c: ("qd_set", "good") for c in ps[-1]["chain"][1:]}
        labels = {c: (str(i + 1), "txt") for i, c in enumerate(pts)}
        grid(fills, labels)
        panel([("%d POINTS, IN ORDER:" % len(pts), "acc", True)] + ["%d: (%d,%d)" % (i + 1, a, b) for i, (a, b) in enumerate(pts)] +
              [("THE START IS NOT IN THE LIST", "dim")], dy=26)
        under(["KEPT: A NODE WHOSE STEP DIFFERS FROM THE LAST KEPT STEP (FROM THE END BACK).",
               "A ROUTE OF ONE SEGMENT GIVES 0: THIS PLANNER REFUSES A STRAIGHT FREE LINE."])
        put("The route reduced to %d corner points, in order from the start; the start itself is not in the list "
            "(search L2)." % len(pts), "The route reduced to its corners.",
            ["search L2 Reduce: points = %s." % ", ".join("(%d, %d)" % p for p in pts),
             "search L2: fewer than 2 points returns 0; more than 77 returns 0."])
        return frames, caps, k.pal, res

    if mode == "walk":
        d0, log, pts = walk_points(limit, seed)
        n = limit >> 1
        fills = {}
        header("RANDOM WALK OF TYPE 10: %d STEPS" % n)
        grid()
        panel([("LIMIT %d, SO %d STEPS" % (limit, n), "acc", True), "FIRST DIRECTION: %s" % DIR_NAME[d0],
               "(TOWARD THE TARGET, ONCE)", "SEED %08X:%08X" % (seed & 0xFFFFFFFF, 666), "",
               "THE GRID IS NOT READ"])
        under(["ONE DRAW A STEP: DIRECTION = FIRST DIRECTION + ADD, ADD FROM THE LOW 5 BITS.",
               "THE POINT MOVES 2 SUBTILES A STEP. THE FIRST POINT IS THE POSITION."])
        put("The random walk of type 10 on the toy room: it keeps the first direction, toward the target, and each of its %d "
            "steps adds -1, 0 or +1 to it from one draw (search I). It reads no grid." % n,
            "Random walk: the first direction is %s and the walk takes %d steps from the start." % (DIR_NAME[d0].lower(), n),
            ["search I: n = limit >> 1 = %d; d = the first direction of PathDirRow toward the target, once = %d." % (n, d0),
             "search I: seed = {%08x:%08x} (low:high), the toy's illustrative input." % (seed & 0xFFFFFFFF, 666)])
        for i, (kk, lo, hi, add, dr, cur) in enumerate(log):
            pre = pts[:kk + 1]
            for j, c in enumerate(pre):
                fills[c] = ("qd_set", "good")
            header("STEP %d OF %d" % (kk + 1, n))
            grid(fills, {c: (str(j), "txt") for j, c in enumerate(pre)})
            nxt = pts[kk + 1]
            panel([("DRAW %d: LOW %08X" % (kk + 1, lo), "txt", True), "HIGH %08X" % hi,
                   "LOW AND 31 = %d, ADD = %d" % (lo & 31, add),
                   "DIR = (%d + %d) AND 7 = %d" % (d0, add, dr), "    %s" % DIR_NAME[dr],
                   ("POINT %d = (%d,%d)" % (kk, cur[0], cur[1]), "acc", True),
                   "NEXT: (%d,%d) + 2 STEPS = (%d,%d)" % (cur[0], cur[1], nxt[0], nxt[1])], dy=26)
            under(["THE POINT BEFORE THE STEP IS KEPT; THE POSITION THEN MOVES 2 SUBTILES IN DIR.",
                   "NO WALL IS TESTED: A POINT MAY LIE IN OR PAST THE WALL."])
            put("Step %d of %d: the draw gives low word %d, which AND 31 is %d, so add is %d and the direction is %s."
                % (kk + 1, n, lo, lo & 31, add, DIR_NAME[dr].lower()),
                "Step %d: add %d, direction %s, point %d is (%d, %d)." % (kk + 1, add, DIR_NAME[dr].lower(), kk, cur[0], cur[1]),
                ["search I: v = %d * %d + %d; new low = %d, new high = %d." % (rng.MULT, lo if kk == 0 else log[kk - 1][1],
                                                                                666 if kk == 0 else log[kk - 1][2], lo, hi)
                 if False else "search I: draw %d on the seed gives low word %d (seed {%08x:%08x})." % (kk + 1, lo, lo, hi),
                 "search I: add[%d] = %d; dir = (%d + %d) & 7 = %d." % (lo & 31, add, d0, add, dr),
                 "search I: points[%d] = (%d, %d); cur = cur + 2 * step[%d] = (%d, %d)." % (kk, cur[0], cur[1], dr, nxt[0], nxt[1])])
        header("THE WALK ENDED: %d POINTS" % (n + 1))
        fills = {c: ("qd_set", "good") for c in pts}
        grid(fills, {c: (str(j), "txt") for j, c in enumerate(pts)})
        panel([("%d POINTS" % (n + 1), "acc", True), "THE LAST ONE IS THE", "POSITION AFTER THE", "LAST STEP", "",
               "RETURN VALUE: %d" % (n + 1), "THE WALL WAS NEVER TESTED"], dy=26)
        under(["A STRAIGHT STEP HAS CHANCE 10 IN 32, EACH SIDE 11 IN 32: ADD IS -1, 0 OR 1.",
               "IT IS NOT A WALK OF ACCUMULATING TURNS."])
        put("The walk ends with %d points, the last one the position after the final step. It tested no wall: a straight "
            "step has chance 10 in 32 and each side 11 in 32 (search I)." % (n + 1),
            "The walk ends with %d points and returns %d." % (n + 1, n + 1),
            ["search I: points[n] = cur; +0x28 = n + 1 = %d; return n + 1." % (n + 1),
             "search I: the first point is the position itself; no grid and no room are read."])
        return frames, caps, k.pal, (d0, log, pts)

    # ---- the spiral
    O = (8, 4)
    pts, iters = spiral_points(O)
    on = [p for p in pts if 0 <= p[0] < GW and 0 <= p[1] < GH]
    header("SPIRAL OF TYPE 14: 77 POINTS AROUND THE POSITION")
    fills = {}
    grid(fills, marks=False)
    x, y = cxy(O)
    k.outline(x, y, CS + 1, CS + 1, "acc", 3)
    k.text_c(x + CS // 2 + 1, y + (CS - 14) // 2 + 1, "P", "acc", 2, True)
    panel([("THE POSITION P (%d,%d)" % O, "acc", True), "R GROWS BY 9600 A TURN STEP,", "THE ANGLE BY 16 OF 512",
           "A POINT IS KEPT WHEN THE CELL", "CHANGES", "", "NO DRAW, NO GRID READ"])
    under(["EACH ITERATION: R = R + 9600 AND ANGLE = ANGLE + 16.",
           "X = SIN(ANGLE + 128) * R AND Y = SIN(ANGLE) * R, TRUNCATED TOWARD ZERO,",
           "ARE ADDED TO THE POSITION, IN 1/65536 OF A SUBTILE."])
    put("The spiral of type 14 around the position P: no draw and no grid. Each iteration grows the radius by 9600 (in 1/65536 "
        "subtile) and the angle by 16 of 512 (search J).",
        "The spiral: the radius and the angle grow by a fixed amount each iteration.",
        ["search J step 3: r = r + 0x2580, a = a + 16.",
         "search J steps 5 and 6: X = trunc(SIN[(a + 0x80) & 0x1FF] * R), Y = trunc(SIN[a & 0x1FF] * R).",
         "The sine table is within 1.8e-07 of sin(2 pi k / 512) (search inputs)."])
    # one iteration's arithmetic: the first, and the first one that keeps a point
    fx, fy = (O[0] << 16) + 0x8000, (O[1] << 16) + 0x8000
    kept_at = []
    r = a = 0
    lx, ly = fx, fy
    for it in range(1, iters + 1):
        r += 0x2580
        a += 16
        x, y = fx + int(sine(a + 0x80) * r), fy + int(sine(a) * r)
        if x >> 16 != lx >> 16 or y >> 16 != ly >> 16:
            kept_at.append(it)
            lx, ly = x, y

    def one_iteration(it, nkept):
        r_, a_ = it * 0x2580, it * 16
        X, Y = int(sine(a_ + 0x80) * r_), int(sine(a_) * r_)
        cell = ((fx + X) >> 16, (fy + Y) >> 16)
        last = pts[nkept - 1] if nkept else O
        keep = cell != last
        header("ITERATION %d" % it)
        shown = pts[:nkept + (1 if keep else 0)]
        grid({c: ("qd_set", "good") for c in shown if 0 <= c[0] < GW and 0 <= c[1] < GH}, marks=False)
        x, y = cxy(O)
        k.outline(x, y, CS + 1, CS + 1, "acc", 3)
        k.text_c(x + CS // 2 + 1, y + (CS - 14) // 2 + 1, "P", "acc", 2, True)
        panel([("R = %d * 9600 = %d" % (it, r_), "txt", True), "ANGLE = %d * 16 = %d" % (it, a_),
               "X = SIN(%d) * R = %d" % ((a_ + 0x80) & 0x1FF, X), "Y = SIN(%d) * R = %d" % (a_ & 0x1FF, Y),
               "CELL (%d,%d); LAST KEPT (%d,%d)" % (cell[0], cell[1], last[0], last[1]),
               ("KEPT AS POINT %d" % (nkept + 1) if keep else "THE SAME CELL: NOT KEPT", "good" if keep else "dim", True)],
              dy=26)
        under(["THE OFFSET IS ADDED TO THE 16.16 POSITION; THE POINT IS THE WHOLE PARTS.",
               "THE ANGLE GOES ROUND ONCE EVERY 32 ITERATIONS: 512 / 16."])
        put("Iteration %d: radius %d, angle %d; the offset is (%d, %d), which is cell (%d, %d)%s (search J)." % (
            it, r_, a_, X, Y, cell[0], cell[1],
            ", a new cell, so the point is kept" if keep else ", the last kept cell, so nothing is kept"),
            "Iteration %d: the offset (%d, %d) reaches cell (%d, %d)%s." % (it, X, Y, cell[0], cell[1],
                                                                          ", which is kept" if keep else ", not kept"),
            ["search J: R = %d, a = %d, X = trunc(sin(%d) * %d) = %d, Y = trunc(sin(%d) * %d) = %d." % (
                r_, a_, a_ + 0x80, r_, X, a_, r_, Y),
             "search J step 8: x >> 16 or y >> 16 %s the last kept cell." % ("differs from" if keep else "equals")])

    one_iteration(1, 0)
    one_iteration(kept_at[0], 0)
    # progress frames: the kept points by iteration
    for upto in (32, 64, iters):
        n = sum(1 for v in kept_at if v <= upto)
        shown = pts[:n]
        header("AFTER ITERATION %d: %d POINTS" % (upto, n))
        fills = {c: ("qd_set", "good") for c in shown if 0 <= c[0] < GW and 0 <= c[1] < GH}
        grid(fills, marks=False)
        x, y = cxy(O)
        k.outline(x, y, CS + 1, CS + 1, "acc", 3)
        k.text_c(x + CS // 2 + 1, y + (CS - 14) // 2 + 1, "P", "acc", 2, True)
        offg = sum(1 for c in shown if not (0 <= c[0] < GW and 0 <= c[1] < GH))
        panel([("ITERATION %d" % upto, "acc", True), "R = %d * 9600" % upto, "  = %d.%02d SUBTILES" % (
            upto * 9600 // 65536, upto * 9600 % 65536 * 100 // 65536), "ANGLE = %d OF 512" % ((upto * 16) % 512),
            "POINTS KEPT: %d OF 77" % n, "OFF THE TOY ROOM: %d" % offg], dy=26)
        under(["THE SPIRAL ENDS WHEN 77 POINTS ARE KEPT: %d ITERATIONS HERE." % iters,
               "POINTS PAST THE ROOM'S EDGE ARE NOT DRAWN; THE PLAN DOES NOT READ THE ROOM."])
        put("After iteration %d the spiral has kept %d points, %d of them inside the toy room; it reads no grid, so the wall "
            "does not matter (search J)." % (upto, n, n - offg),
            "After iteration %d: %d points kept." % (upto, n),
            ["search J step 9: the loop ends when k >= 77; here that is iteration %d." % iters,
             "search J: no grid, no draw and neither +0x90 nor +0x91 are used."])
    return frames, caps, k.pal, (pts, iters)


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--mode": "search", "--b1c": "33", "--limit": "12", "--seed": "0xC0FFEE", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            if i + 1 >= len(argv):
                print(__doc__.strip(), file=sys.stderr)
                return 2
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 1 or opts["--mode"] not in ("search", "walk", "spiral") or opts["--theme"] not in K.THEMES:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        b1c, limit, seed = int(opts["--b1c"]), int(opts["--limit"]), int(opts["--seed"], 0)
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not (0 <= b1c <= 255 and 2 <= limit <= 40 and 0 <= seed < 1 << 32):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "path-%s-schematic" % opts["--mode"])
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal, _i = build(opts["--mode"], b1c, limit, seed, opts["--theme"])
    K.write_illustration(out, "path", frames, caps, W, H, K.palette(opts["--theme"])[1],
                         "path planners animation", HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Plan 0054 Phase 1.2 (`lane/r54b`): PathPlanSearch (types 0 and 16) run under Ghidra's p-code emulator (ADR-0015,
ADR-0021) with re/ghidra_scripts/EmuScratch.java over declared images, and compared with the model below. No game run,
no slot. docs/findings/path/0002-search.md.

    python3 -I tools/path_emu2.py grids  [--dir D]     predict the room blocks (tools/collision.py's activation model on
                                                       three kept run:2026-10-14-collision logs) into D/block-*.bin
    python3 -I tools/path_emu2.py cases  [--dir D]     write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuscratch D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/path_emu2.py check  [--dir D]     compare every D/<family>.out with the model, account for every
                                                       traced access and scratch read, run the controls
    python3 -I tools/path_emu2.py bounds               the kept integer computations (grid size, node depth, points)
    python3 -I tools/path_emu2.py stores <writers file> <game.exe>   the base of the 14 byte stores
    python3 -I tools/path_emu2.py manifest [--dir D] [--write]

Default D: workspace/logs/r54b/emu. Every case draw comes from random.Random("r54b-<family>"); `cases` reads the blocks
`grids` wrote, so both regenerate identical files.

The entry (ruling 2 of the P1.1 review). Every case enters sub_0067AD00_PathPlanSearch with ECX a declared PathPlanCtx: the
IsBadCodePtr import blocks a run through PathPlan. The context's +0x10, +0x18 (limit) and +0x24 (size) and the path's every
field but the point list (and +0x30 under type 16) are left undeclared, so a read of them is a traced access and fails the
family. The 0x36FF8-byte frame stays on the declared stack as scratch: EmuScratch reports a read of a stack byte before
the case's write of it (a U line); only _chkstk's page probes (0x006831D7) and the 2 stray bytes of 0x0067AB46 are accounted.

The images. Real blocks (families real0, real16): DungeonRoom records over cells predicted by tools/collision.py for one game
of each log, as many rooms of a 6 x 6 (40-subtile rooms) or 4 x 4 (60-subtile rooms) window as the log activated, each
block once as predicted and once with seeded unit marks; a start's own marks and, under flag 0x800, the target's are
absent, as PathPlan leaves them (the case writer picks such points; a target with no 0x800 keeps what is there).
The near list of a room is every block room touching it, self included (a declared reading of the DRLG near list);
a cell outside every near room is "no room". Synthetic rooms (families stair, corr, open, rect, grid, over): seeded cells,
for the branches stock cells seldom reach; declared, they claim the map only. The collision tests run inside each case,
edge branches included, and the model below carries them (drlg/0005 § 3 and § 4).

Families: real0, real16 (types 0 and 16 on the real blocks); stair (a one-cell staircase corridor, route lengths 1 to 90: the
point bound); corr (a long corridor past PathPlan's +-100 window: the 900-node store); open (noise, walled targets, a
high b1C: the 10 000-pass limit, the iterations); rect (two rooms of unequal rectangles: the rectangle's rule and the start
outside it); grid (rectangles at and past the 50 000 assert, boundary: the assert entry 0x00408090 or the clear's memset
0x00681EF0); over (rectangles at the frame's end, boundary: the instruction after the memset, 0x0067AB00, with the saved EBP,
the return address and the context argument dumped).

Controls (each must fail every case it separates): h (the heuristic as max + 2 min), cost (diagonal 2), tries (a child
tries 8 directions), row (the row index as parent - wanted), fgt (f >= bound prunes), cellle (a cell equal to g prunes),
step (bound step 4), regrid (the grid cleared between iterations), min2 (one point accepted), rectend (leaving the rectangle
does not end the search), radius (no doubling of ctx +0x14), union (the true union of the rooms), margin (margin 9), draw
(type 16 draws nothing), half (type 16 bound 2 h), max77 (78 points accepted), nodes (901 nodes), passes (20 000 passes),
and the site control (every call site one byte later) for every boundary case.

Not covered (ADR-0021): PathPlan's tail after the planner, and the planners of the other types. Stdlib only.
"""
import argparse
import hashlib
import json
import os
import random
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import path_scan                                            # noqa: E402

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r54b", "emu")
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
PINNED = "631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf"
LOGS = os.path.join(ROOT, "workspace", "logs")
BLOCKS = (   # name, log, level ids, room side, window side in rooms
    ("T", "collision-s3-2026-normal-a3.log", (75,), 40, 6),
    ("U", "collision-s3-2026-normal-a3.log", (76,), 40, 6),
    ("J", "collision-s6-2026-normal-a1.log", (29,), 60, 4),
    ("K", "collision-s1-2026-normal.log", (106,), 40, 6),
)
PLANNER = 0x0067AD00
CTX, UPATH, UNIT = 0x12700000, 0x12200000, 0x12100000
ROOM0, MAP0 = 0x13000000, 0x14000000                       # DungeonRoom i at ROOM0 + 0x1000 i; maps packed from MAP0
ESP0 = 0x7FF00000
EBP_PLAN = ESP0 - 4
EBP_RUN = EBP_PLAN - 0x78                                  # PathSearchRun's frame pointer on this entry
GRID_AT = EBP_RUN - 0x30D68
ASSERT, MEMSET, AFTER_MEMSET = 0x00408090, 0x00681EF0, 0x0067AB00
SITE_ASSERT, SITE_MEMSET = 0x0067AACF, 0x0067AB00
FATAL = (0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)
A = 0x6AC690C5
POINTS_DUMP = 0x138
# scratch reads accounted (U lines): _chkstk's page probes, and the dword read whose high half (the stride, unwritten yet) the
# low-word store at 0x0067AB78 drops
U_OK = {0x006831D7: "chkstk", 0x0067AB46: "stray2"}
TABLES = {
    "rows": (0x006F17D8, 8 * 32 + 4), "drawadd": (0x006F18D8, 128), "steps": (0x006F1958, 64), "dirs": (0x006F1518, 300),
    "jt_ptb": (0x0064D994, 24), "jt_plus": (0x0064D784, 52), "sse": (0x00994C88, 4), "jt_memcpy": (0x00682AD0, 0x68),
}
MASKS = (0x1C09, 0x3C01, 0x3401, 0x1C01, 0x0804, 0x0409, 0x0001, 0x0000, 0xFFFF, 0x0100, 0x0080, 0x0004)


def u32(v):
    return v & 0xFFFFFFFF


def s32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


def s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


class Image:
    def __init__(self):
        data = open(EXE, "rb").read()
        if hashlib.sha256(data).hexdigest() != PINNED:
            raise SystemExit("path_emu2: not the pinned Game.exe")
        self.rows = struct.unpack("<65i", path_scan.va_bytes(data, 0x006F17D8, 260))
        self.add = struct.unpack("<32i", path_scan.va_bytes(data, 0x006F18D8, 128))
        raw = path_scan.va_bytes(data, 0x006F1958, 64)
        self.steps = [(struct.unpack_from("<h", raw, 8 * d)[0], struct.unpack_from("<h", raw, 8 * d + 4)[0]) for d in range(8)]
        self.dirs = [struct.unpack_from("<i", path_scan.va_bytes(data, 0x006F1518, 300), 12 * q)[0] for q in range(25)]


IMG = None


def img():
    global IMG
    if IMG is None:
        IMG = Image()
    return IMG


# ------------------------------------------------------------------------------------------------------ the rooms
class Room:
    def __init__(self, i, rect, cells, tag=""):
        self.i, self.tag = i, tag
        self.x0, self.y0, self.w, self.h = rect
        self.c = cells
        self.addr = ROOM0 + 0x1000 * i
        self.near = []
        self.map = 0

    def has(self, x, y):
        return self.x0 <= x < self.x0 + self.w and self.y0 <= y < self.y0 + self.h

    def cell(self, x, y):
        return self.c[(y - self.y0) * self.w + (x - self.x0)]


def link(rooms):
    """Near lists: every room touching it (corners too), self included. Maps packed."""
    at = MAP0
    for r in rooms:
        r.near = [n for n in rooms if n.x0 <= r.x0 + r.w and r.x0 <= n.x0 + n.w and n.y0 <= r.y0 + r.h and r.y0 <= n.y0 + n.h
                  and n.tag == r.tag]
        r.map = at
        if r.c:
            at += (0x24 + 2 * r.w * r.h + 0xFFF) & ~0xFFF


def room_spec(rooms):
    out = []
    for r in rooms:
        a = r.addr
        out.append("const bytes %08x %s" % (a, struct.pack("<I", a + 0x100).hex()))
        out.append("const bytes %08x %s" % (a + 0x20, struct.pack("<II", r.map, len(r.near)).hex()))
        out.append("const bytes %08x %s" % (a + 0x4C, struct.pack("<8i", r.x0, r.y0, r.w, r.h, r.x0 // 5, r.y0 // 5, r.w // 5,
                                                                  r.h // 5).hex()))
        if r.near:
            out.append("const bytes %08x %s" % (a + 0x100, b"".join(struct.pack("<I", n.addr) for n in r.near).hex()))
        if not r.c:                                               # a header only (families grid, over)
            continue
        out.append("const bytes %08x %s" % (r.map, struct.pack("<9I", r.x0, r.y0, r.w, r.h, r.x0 // 5, r.y0 // 5, r.w // 5,
                                                               r.h // 5, r.map + 0x24).hex()))
        out.append("const bytes %08x %s" % (r.map + 0x24, struct.pack("<%dH" % len(r.c), *r.c).hex()))
    return out


def cmd_grids(d):
    """Predicted blocks: per block the rooms of the window of `BLOCKS` holding the most activated rooms of the level ids."""
    import collision
    os.makedirs(d, exist_ok=True)
    meta = {"blocks": []}
    for name, logname, lids, side, win in BLOCKS:
        path = os.path.join(LOGS, logname)
        W = collision.World(os.path.join(ROOT, "workspace", "merged"), None)
        game = 0
        found = {}
        for ln, line in enumerate(open(path, errors="replace"), 1):
            tag, _, rest = line.rstrip("\n").partition(" ")
            if tag == "GP":
                game += 1
                continue
            if tag not in ("TL", "CB", "RRESEED") or not rest.startswith("{"):
                continue
            dd = json.loads(rest)
            W.event(tag, dd, ln, path)
            if tag == "CB":
                m = W.model[dd["room"]]
                found[(game, dd["lid"], m.x0, m.y0, m.w, m.h)] = (list(m.c), ln)
        if W.fail:
            raise SystemExit("path_emu2 grids: the activation model differs from %s" % logname)
        best = None
        for (g, lid, x0, y0, w, h) in sorted(found):
            if lid not in lids or (w, h) != (side, side):
                continue
            for ox in range(win):
                for oy in range(win):
                    ax, ay = x0 - ox * side, y0 - oy * side
                    have = [k for k in sorted(found) if k[0] == g and k[1] in lids and k[4:] == (side, side)
                            and ax <= k[2] < ax + win * side and ay <= k[3] < ay + win * side]
                    if best is None or len(have) > len(best):
                        best = have
        rooms = []
        for k, key in enumerate(best):
            cells, ln = found[key]
            fn = "block-%s%02d.bin" % (name, k)
            with open(os.path.join(d, fn), "wb") as f:
                f.write(struct.pack("<%dH" % len(cells), *cells))
            rooms.append({"file": fn, "lid": key[1], "rect": list(key[2:]), "log_line": ln,
                          "nonzero": sum(1 for c in cells if c)})
        meta["blocks"].append({"name": name, "log": logname, "game": best[0][0], "rooms": rooms, "checks": W.checks,
                               "fail": W.fail})
        print("GRIDS %s %s game=%d rooms=%d lids=%s checks=%d fail=%d" % (
            name, logname, best[0][0], len(rooms), sorted(set(r["lid"] for r in rooms)), W.checks, W.fail))
    with open(os.path.join(d, "grids.json"), "w") as f:
        json.dump(meta, f, indent=1, sort_keys=True)


def load_real(d):
    meta = json.load(open(os.path.join(d, "grids.json")))
    rooms = []
    for b in meta["blocks"]:
        base = []
        for r in b["rooms"]:
            raw = open(os.path.join(d, r["file"]), "rb").read()
            base.append((r["rect"], list(struct.unpack("<%dH" % (len(raw) // 2), raw))))
        for variant in (0, 1):
            rnd = random.Random("r54b-marks-%s" % b["name"])
            for rect, cells in base:
                c = list(cells)
                if variant:
                    x0, y0, w, h = rect
                    for _ in range(60):
                        cx, cy = rnd.randrange(1, w - 1), rnd.randrange(1, h - 1)
                        v = rnd.choice((0x80, 0x100))
                        foot = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)) if rnd.random() < 0.5 else \
                            tuple((a, bb) for a in (-1, 0, 1) for bb in (-1, 0, 1))
                        for a, bb in foot:
                            c[(cy + bb) * w + cx + a] |= v
                rooms.append(Room(len(rooms), rect, c, "%s%d" % (b["name"], variant)))
    link(rooms)
    return rooms


# ------------------------------------------------------------------------------------------ the collision model
def room_at(R, hint, x, y):
    """sub_00463740_RoomAtSubtile: the hint, else the first of its near list that holds the point."""
    h = R[hint]
    if h.has(x, y):
        return h
    for n in h.near:
        if n.has(x, y):
            return n
    return None


def rect_test(R, hint, left, top, right, bottom, mask):
    """COLL_RectTestBool 0x0064CF50 with COLL_RectSplit 0x0064CDF0."""
    r = room_at(R, hint, left, top)
    if r is None or top > bottom or left > right:
        return 1
    p0r, p0b = right, bottom
    more = []
    if right >= r.x0 + r.w:
        p0r = r.x0 + r.w - 1
        more.append((r.x0 + r.w, top, right, bottom))
    if bottom >= r.y0 + r.h:
        p0b = r.y0 + r.h - 1
        more.append((left, r.y0 + r.h, p0r, bottom))
    for y in range(top, p0b + 1):
        for x in range(left, p0r + 1):
            if r.cell(x, y) & mask:
                return 1
    for p in more:
        if rect_test(R, r.addr, p[0], p[1], p[2], p[3], mask):
            return 1
    return 0


def ptb(R, hint, x, y, pattern, mask):
    """COLL_PatternTestBool 0x0064D910: 0 cell, 1 / 3 / 5 plus, 2 / 4 3 x 3, other 1. Non-zero = blocked."""
    mask &= 0xFFFF
    if pattern == 0:
        r = room_at(R, hint, x, y)
        return 0x27 if r is None else r.cell(x, y) & mask
    if pattern in (1, 3, 5):                                       # COLL_PlusTestBool 0x0064D4E0
        r = room_at(R, hint, x, y)
        if r is None:
            return 1
        e = (x <= r.x0) | (y <= r.y0) << 1 | (r.x0 + r.w <= x + 1) << 2 | (r.y0 + r.h <= y + 1) << 3
        if e in (5, 7, 10, 11, 13, 14, 15):                        # a room one cell wide or high
            return 1
        for a, b in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            if r.has(x + a, y + b):
                if r.cell(x + a, y + b) & mask:
                    return 1
            else:                                                  # COLL_CellTestNb 0x0064CA50 with the centre's room as hint
                n = room_at(R, r.addr, x + a, y + b)
                if n is None or n.cell(x + a, y + b) & mask:
                    return 1
        return 0
    if pattern in (2, 4):                                          # COLL_Square3TestBool 0x0064D7C0
        return rect_test(R, hint, x - 1, y - 1, x + 1, y + 1, mask)
    return 1


# ---------------------------------------------------------------------------------------------------- the search
def dir_index(a, b):
    """0x00678C10 PathDirCell (path/0001 § 5)."""
    dx = (b & 0xFFFF) - (a & 0xFFFF)
    dy = (b >> 16) - (a >> 16)
    adx, ady = abs(dx), abs(dy)
    mn = lambda v: -1 if v < 0 else v & 1
    if adx >= 2 * ady:
        dy = mn(dy)
    elif ady >= 2 * adx:
        dx = mn(dx)
    dx = max(-2, min(2, dx))
    dy = max(-2, min(2, dy))
    return 5 * dx + dy + 12


def oct_h(a, b, neg=None):
    dx = abs((a & 0xFFFF) - (b & 0xFFFF))
    dy = abs((a >> 16) - (b >> 16))
    lo, hi = min(dx, dy), max(dx, dy)
    return hi + 2 * lo if neg == "h" else lo + 2 * hi


class Node:
    __slots__ = ("f", "h", "g", "n", "pt", "ptr", "d", "parent", "child")


class Fail(Exception):
    pass


class Search:
    def __init__(self, c, R, memo, neg=None):
        self.c, self.R, self.memo, self.neg = c, R, memo, neg
        self.visits = self.iters = self.nodes = self.maxvisits = 0
        self.tag = None
        self.seed = c.get("seed")
        self.I = img()
        self.draws = 0

    def rect(self):
        c, R, neg = self.c, self.R, self.neg
        own = R[c["room"]]
        x, y, w, h = own.x0, own.y0, own.w, own.h
        m = 9 if neg == "margin" else 10
        o = R.get(c["troom"]) if c["troom"] != c["room"] else None
        if o is None:
            return x - m, y - m, w + 2 * m, h + 2 * m
        if neg == "union":
            nx, ny = min(own.x0, o.x0), min(own.y0, o.y0)
            nw, nh = max(own.x0 + own.w, o.x0 + o.w) - nx, max(own.y0 + own.h, o.y0 + o.h) - ny
        else:
            nx, nw = (o.x0, own.w - o.x0 + own.x0) if o.x0 < own.x0 else (own.x0, o.w - own.x0 + o.x0)
            ny, nh = (o.y0, own.h - o.y0 + own.y0) if o.y0 < own.y0 else (own.y0, o.h - own.y0 + o.y0)
        if nw == own.w:
            nx, nw = nx - m, nw + 2 * m
        if nh == own.h:
            ny, nh = ny - m, nh + 2 * m
        return nx, ny, nw, nh

    def rng(self):
        lo, hi = self.seed
        v = A * lo + hi
        self.seed = (v & 0xFFFFFFFF, v >> 32)
        self.draws += 1
        return self.seed[0]

    def turn(self, node):
        """0x0067A630 PathSearchDirDraw: the next try's direction."""
        k = self.I.rows[node.ptr] if node.ptr < 65 else 0
        if self.flag and self.neg != "draw":
            node.d = (self.I.add[self.rng() & 0x1F] + k + node.d) & 7
        else:
            node.d = (k + node.d) & 7

    def advance(self, node):
        """0x0067A690: the node's next try; past its last, its parent's next."""
        if node.n < 4:
            node.ptr += 1
            self.turn(node)
        node.n += 1
        if node.n != 5:
            return node
        while True:
            if node is self.root:
                return None
            node = node.parent
            node.ptr += 1
            self.turn(node)
            node.n += 1
            if node.n != 5:
                return node

    def blocked(self, x, y):
        c = self.c
        k = (c["room"], x, y, c["pattern"], c["mask"])
        v = self.memo.get(k)
        if v is None:
            v = self.memo[k] = ptb(self.R, c["room"], x, y, c["pattern"], c["mask"])
        return v

    def walk(self, bound):
        """0x0067A740: one depth-first pass under `bound`; the node it ends on, or None."""
        I, neg, c = self.I, self.neg, self.c
        node = self.root
        t = self.t
        passes = 0
        limit = 20000 if neg == "passes" else 10000
        cap = 901 if neg == "nodes" else 900
        x0, y0, x1, y1, stride, ox, oy = self.box
        grid = self.grid
        radius = self.radius
        rowbase = I.rows
        while True:
            if node.pt == t:
                self.end = "target"
                return node
            passes += 1
            self.visits += 1
            if passes > limit:
                self.end = "passes"
                self.maxvisits = max(self.maxvisits, passes)
                return None
            px, py = node.pt & 0xFFFF, node.pt >> 16
            if neg != "rectend" and not (x0 <= px <= x1 and y0 <= py <= y1):
                self.end = "rect"
                return node
            sx, sy = I.steps[node.d]
            nx, ny = (px + sx) & 0xFFFF, (py + sy) & 0xFFFF
            idx = (ny + oy) * stride + ox + nx
            cell = grid.get(idx, 0)
            if cell == 0 and self.blocked(nx, ny):
                grid[idx] = 1
                node = self.advance(node)
                if node is None:
                    self.end = "exhausted"
                    return None
                continue
            diag = px != nx and py != ny
            g = (node.g + (2 if neg == "cost" else 3 if diag else 2)) & 0xFFFF
            sg = s16(g)
            if cell and (u32(cell) <= u32(sg) if neg == "cellle" else u32(cell) < u32(sg)):
                node = self.advance(node)
                if node is None:
                    self.end = "exhausted"
                    return None
                continue
            grid[idx] = sg
            np_ = nx | ny << 16
            h = oct_h(np_, t, neg) & 0xFFFF
            f = (h + g) & 0xFFFF
            if (s16(f) >= bound) if neg == "fgt" else (s16(f) > bound):
                node = self.advance(node)
                if node is None:
                    self.end = "exhausted"
                    return None
                continue
            child = node.child
            if child is None:
                if self.count == cap:
                    self.end = "nodes"
                    return None
                self.count += 1
                self.nodes = max(self.nodes, self.count)
                child = Node()
                child.child = None
                child.parent = node
                node.child = child
            child.h, child.g, child.f = h, g, f
            child.n = 0
            want = I.dirs[dir_index(np_, t)]
            row = (node.d - want) & 7 if neg == "row" else (want - node.d) & 7
            child.ptr = row * 8
            k = rowbase[child.ptr]
            if self.flag and neg != "draw":
                child.d = (I.add[self.rng() & 0x1F] + node.d + k) & 7
            else:
                child.d = (node.d + k) & 7
            child.pt = np_
            if neg == "tries":
                child.n = -3
            node = child
            if s16(child.h) < radius:
                self.end = "radius"
                return node

    def reduce(self, node):
        """0x0067A9F0: from the end back, a node is kept when its step differs from the kept step after it."""
        buf = []
        px, py = -2, -2
        while True:
            if len(buf) >= 78:
                break
            p = node.parent
            if p is not None:
                dx = (node.pt & 0xFFFF) - (p.pt & 0xFFFF)
                dy = (node.pt >> 16) - (p.pt >> 16)
                if dx != px or dy != py:
                    buf.append(node.pt)
                    px, py = dx, dy
            node = p
            if node is None:
                break
        n = len(buf)
        lo = 1 if self.neg == "min2" else 2
        hi = 78 if self.neg == "max77" else 77
        if not lo <= n <= hi:
            self.tag = "points<2" if n < 2 else "points78"
            return 0, None, n
        return n, buf[::-1], n

    def run(self):
        c, neg = self.c, self.neg
        self.radius = (c["refresh"] if neg == "radius" else c["refresh"] * 2) & 0xFF
        x, y, w, h = self.rect()
        area = s32(w * h)
        if area > 50000:
            return {"assert": True}
        s, t = c["s"], c["t"]
        self.t = t
        self.flag = c["type"] == 16
        x0, y0 = x & 0xFFFF, y & 0xFFFF
        x1, y1 = (x + w) & 0xFFFF, (y + h) & 0xFFFF
        self.box = (x0, y0, x1, y1, (w & 0xFFFF) + 6, 3 - x0, 3 - y0)
        self.grid = {}
        h0 = oct_h(s, t, neg) & 0xFFFF
        b = s16(h0)
        end = b
        if c["type"] == 0:
            end = max(b, c["b1C"])
        elif c["type"] == 16:
            b = s16(h0 + (2 * b - b if neg == "half" else int(b / 2)))
            end = max(b, c["b1C"])
        d0 = self.I.dirs[dir_index(s, t)] & 7
        result = None
        step = 4 if neg == "step" else 5
        self.count = 1
        self.end = None
        while True:
            root = Node()
            root.f, root.h, root.g, root.n, root.pt, root.ptr, root.d = h0, h0, 0, -3, s, 0, d0
            root.parent = root.child = None
            self.root = root
            self.iters += 1
            if neg == "regrid":
                self.grid = {}
            result = self.walk(b)
            b += step
            if result is None and self.count == (901 if neg == "nodes" else 900):
                break
            self.count = 1
            if result is not None or b >= end:
                break
        sx0, sy0 = s & 0xFFFF, s >> 16
        out = {"assert": False, "startout": not (x0 <= sx0 <= x1 and y0 <= sy0 <= y1), "rect": (x, y, w, h), "h0": h0, "iters": self.iters, "visits": self.visits, "end": self.end,
               "nodes": self.nodes, "seed": self.seed, "draws": self.draws, "stored": None}
        if result is None:
            out.update(eax=0, points=None, tag="none:" + self.end)
            return out
        n, pts, st = self.reduce(result)
        out.update(eax=n, points=pts, tag=(self.tag or "route") + ":" + self.end, stored=st)
        return out


# ------------------------------------------------------------------------------------------------------ the cases
def case_lines(c, poison):
    L = []
    ctx = struct.pack("<HHHHII", c["s"] & 0xFFFF, c["s"] >> 16, c["t"] & 0xFFFF, c["t"] >> 16, c["room"], c["troom"])
    L.append("w %08x %s" % (CTX, ctx.hex()))
    L.append("w %08x %02x" % (CTX + 0x14, c["refresh"]))
    L.append("w %08x %02x" % (CTX + 0x1C, c["b1C"]))
    L.append("w %08x %s" % (CTX + 0x20, struct.pack("<I", c["type"]).hex()))
    L.append("w %08x %s" % (CTX + 0x28, struct.pack("<III", c["pattern"], c["mask"], UPATH).hex()))
    L.append("w %08x %s" % (UPATH + 0x9C, poison.hex()))
    if c["type"] == 16:
        L.append("w %08x %s" % (UPATH + 0x30, struct.pack("<I", UNIT).hex()))
        L.append("w %08x %s" % (UNIT + 0x20, struct.pack("<II", *c["seed"]).hex()))
        L.append("d %08x 8" % (UNIT + 0x20))
    L.append("d %08x 1" % (CTX + 0x14))
    L.append("d %08x 16" % CTX)
    L.append("d %08x %d" % (UPATH + 0x9C, POINTS_DUMP))
    L.append("call %08x %08x 00000000" % (PLANNER, CTX))
    return L


def base_spec(rooms, observe=()):
    out = room_spec(rooms)
    for a in FATAL + ALLOC:
        out.append("guard %08x" % a)
    if ASSERT in observe:
        out.append("observe %08x" % ASSERT)
    else:
        out.append("guard %08x" % ASSERT)
    for a in observe:
        if a != ASSERT:
            out.append("observe %08x" % a)
    return out


def free_of_marks(r, x, y):
    for a in (-1, 0, 1):
        for b in (-1, 0, 1):
            if r.has(x + a, y + b) and r.cell(x + a, y + b) & 0x180:
                return False
    return True


def params(rnd, typ):
    c = {"type": typ, "refresh": rnd.choice((0, 1, 1, 2)), "pattern": rnd.choice((0, 1, 1, 1, 2, 2, 3, 4, 5, 5)),
         "mask": rnd.choice(MASKS), "b1C": rnd.choice((0, 0, 0, 0, 14, 30, 70, 70))}
    if typ == 16:
        c["seed"] = (rnd.getrandbits(32), rnd.randrange(1, 0x7FFFFFFF))
    return c


def budgeted(c, R, memo, limit):
    S = Search(c, R, memo)
    o = S.run()
    return not o.get("assert") and o["visits"] <= limit


def gen_real(rnd, rooms, typ, n, limit=25000):
    R = {r.addr: r for r in rooms}
    memo = {}
    cases = []
    while len(cases) < n:
        r = rnd.choice(rooms)
        sx, sy = r.x0 + rnd.randrange(r.w), r.y0 + rnd.randrange(r.h)
        if not free_of_marks(r, sx, sy):
            continue
        mode = rnd.random()
        if mode < 0.2:                                                            # near, a few subtiles off
            tx, ty = sx + rnd.randint(-8, 8), sy + rnd.randint(-8, 8)
        elif mode < 0.7:                                                          # up to the window's end
            tx, ty = sx + rnd.randint(-40, 40), sy + rnd.randint(-40, 40)
        else:
            tx, ty = sx + rnd.randint(-100, 100), sy + rnd.randint(-100, 100)
        if (tx, ty) == (sx, sy) or tx <= 0 or ty <= 0:
            continue
        tr = room_at(R, r.addr, tx, ty)
        c = params(rnd, typ)
        c.update(room=r.addr, troom=tr.addr if tr else 0, s=sx | sy << 16, t=tx | ty << 16)
        if budgeted(c, R, memo, limit):
            cases.append(c)
    return cases


def noise_room(rnd, i, rect, density, tag):
    x0, y0, w, h = rect
    return Room(i, rect, [1 if rnd.random() < density else 0 for _ in range(w * h)], tag)


def gen_stair(rnd):
    """One-cell staircase corridors: E, SE, E, SE ...; every step a corner."""
    w, h = 190, 190
    x0, y0 = 500, 500
    cells = [1] * (w * h)
    path = [(5, 5)]
    x, y = 5, 5
    for k in range(120):
        if k % 2 == 0:
            x += 1
        else:
            x += 1
            y += 1
        path.append((x, y))
    for (a, b) in path:
        cells[b * w + a] = 0
    room = Room(0, (x0, y0, w, h), cells, "S")
    rooms = [room]
    link(rooms)
    cases = []
    for k in list(range(1, 91)) + [76, 77, 78, 79] * 4:
        for typ, b1c in ((0, 0), (16, 0), (0, 255)):
            c = {"type": typ, "refresh": 0, "pattern": 0, "mask": 1, "b1C": b1c}
            if typ == 16:
                c["seed"] = (rnd.getrandbits(32), rnd.randrange(1, 0x7FFFFFFF))
            sx, sy = path[0]
            tx, ty = path[k]
            c.update(room=room.addr, troom=room.addr, s=(x0 + sx) | (y0 + sy) << 16, t=(x0 + tx) | (y0 + ty) << 16)
            cases.append(c)
    return rooms, cases


def gen_corr(rnd):
    """A long corridor with one bend at its end; past PathPlan's +-100: the node store."""
    w, h = 1000, 20
    x0, y0 = 100, 2000
    cells = [1] * (w * h)
    for a in range(w):
        cells[10 * w + a] = 0
    cases = []
    rooms = []
    room = Room(0, (x0, y0, w, h), cells, "C")
    for a in range(w):
        cells[11 * w + a] = 0
    rooms = [room]
    link(rooms)
    for d in list(range(893, 906)) + [100, 300, 500, 700, 850, 950]:
        for typ in (0, 16):
            c = {"type": typ, "refresh": 0, "pattern": 0, "mask": 1, "b1C": 0}
            if typ == 16:
                c["seed"] = (rnd.getrandbits(32), rnd.randrange(1, 0x7FFFFFFF))
            c.update(room=room.addr, troom=room.addr, s=(x0 + 2) | (y0 + 10) << 16, t=(x0 + 2 + d) | (y0 + 11) << 16)
            cases.append(c)
    return rooms, cases


def gen_open(rnd, n=160):
    rooms = []
    for i, dens in enumerate((0.0, 0.05, 0.12, 0.2, 0.3, 0.4)):
        rooms.append(noise_room(rnd, i, (1000 + 400 * i, 3000, 130, 130), dens, "O%d" % i))
    for r in rooms:                                                                 # a walled pocket in the middle
        for a in range(-3, 4):
            for b in range(-3, 4):
                if max(abs(a), abs(b)) == 3:
                    r.c[(65 + b) * r.w + 65 + a] = 1
                elif max(abs(a), abs(b)) < 3:
                    r.c[(65 + b) * r.w + 65 + a] = 0
    link(rooms)
    R = {r.addr: r for r in rooms}
    memo = {}
    cases = []
    want = 0
    while len(cases) < n:
        r = rnd.choice(rooms)
        sx, sy = rnd.randrange(5, 125), rnd.randrange(5, 125)
        if max(abs(sx - 65), abs(sy - 65)) <= 3:
            continue
        walled = rnd.random() < 0.5
        tx, ty = (65, 65) if walled else (rnd.randrange(2, 128), rnd.randrange(2, 128))
        if (tx, ty) == (sx, sy):
            continue
        typ = rnd.choice((0, 0, 16))
        c = {"type": typ, "refresh": rnd.choice((0, 1)), "pattern": rnd.choice((0, 0, 1, 2)), "mask": 1,
             "b1C": rnd.choice((0, 70, 120, 180, 255))}
        if typ == 16:
            c["seed"] = (rnd.getrandbits(32), rnd.randrange(1, 0x7FFFFFFF))
        c.update(room=r.addr, troom=r.addr, s=(r.x0 + sx) | (r.y0 + sy) << 16, t=(r.x0 + tx) | (r.y0 + ty) << 16)
        S = Search(c, R, memo)
        o = S.run()
        if o["visits"] > 60000:
            continue
        cases.append(c)
    return rooms, cases


def gen_rect(rnd, n=400):
    """Pairs of rooms: right of, left of, below, above each other, equal or unequal on the other axis."""
    rooms = []
    pairs = []
    i = 0
    base = 7000
    for k in range(24):
        w1, h1 = rnd.choice((20, 30, 40, 60)), rnd.choice((20, 30, 40, 60))
        w2 = rnd.choice((w1, w1, 20, 30, 40, 60, 70))
        h2 = rnd.choice((h1, h1, 20, 30, 40, 60, 70))
        x1, y1 = base + 300 * k, 7000
        side = k % 4
        off = rnd.choice((0, 0, -10, 10, 20))
        if side == 0:
            x2, y2 = x1 + w1, y1 + off
        elif side == 1:
            x2, y2 = x1 - w2, y1 + off
        elif side == 2:
            x2, y2 = x1 + off, y1 + h1
        else:
            x2, y2 = x1 + off, y1 - h2
        tag = "R%d" % k
        dens = rnd.choice((0.0, 0.05, 0.15, 0.3))
        a = noise_room(rnd, i, (x1, y1, w1, h1), dens, tag)
        b = noise_room(rnd, i + 1, (x2, y2, w2, h2), dens, tag)
        rooms += [a, b]
        pairs.append((a, b))
        i += 2
    link(rooms)
    R = {r.addr: r for r in rooms}
    memo = {}
    cases = []
    while len(cases) < n:
        a, b = rnd.choice(pairs)
        if rnd.random() < 0.5:
            a, b = b, a
        sx, sy = a.x0 + rnd.randrange(a.w), a.y0 + rnd.randrange(a.h)
        same = rnd.random() < 0.1
        o = a if same else b
        tx, ty = o.x0 + rnd.randrange(o.w), o.y0 + rnd.randrange(o.h)
        if (tx, ty) == (sx, sy) or abs(tx - sx) > 100 or abs(ty - sy) > 100:
            continue
        typ = rnd.choice((0, 0, 0, 16))
        c = params(rnd, typ)
        c["mask"] = rnd.choice((1, 1, 1, 0))
        c.update(room=a.addr, troom=o.addr, s=sx | sy << 16, t=tx | ty << 16)
        if budgeted(c, R, memo, 25000):
            cases.append(c)
    return rooms, cases


def factor_rect(cells):
    """(w, h) with (w + 6)(h + 6) == cells, w + 6 >= 2 the largest such factor; w may be <= 0 in a declared header (the case
    ends after the clear)."""
    best = None
    for a in range(2, int(cells ** 0.5) + 1):
        if cells % a == 0:
            best = (a - 6, cells // a - 6)
    if best:
        return best
    return None


def gen_grid(rnd):
    """The rooms are headers only: the cases end at the assert or the memset, before any cell is read. Rectangles of the
    same-room branch: the room's w, h + 20."""
    dims = []
    for wr, hr in ((250, 200), (200, 250), (500, 100), (100, 500), (125, 400), (1000, 50), (2500, 20), (5000, 10)):
        for dh in (-1, 0, 1):                                                          # w * h around 50 000
            dims.append((wr, hr + dh))
    for k in range(60):
        w = rnd.randrange(1, 400)
        h = 50000 // w + rnd.randint(-3, 3)
        if h >= 1:
            dims.append((w, h))
    for k in range(20):
        dims.append((rnd.randrange(1, 300), rnd.randrange(1, 150)))
    dims += [(46340, 46340), (46341, 46341), (65536, 65536), (65536, 32768)]              # w * h past 2^31: wraps
    rooms = []
    cases = []
    for i, (w, h) in enumerate(dims):
        rw, rh = w - 20, h - 20
        r = Room(i, (3000, 3000, rw, rh), [], "G%d" % i)
        rooms.append(r)
        cases.append({"type": 0, "refresh": 0, "pattern": 0, "mask": 1, "b1C": 0, "room": r.addr, "troom": r.addr,
                      "s": 3005 | 3005 << 16, "t": 3006 | 3005 << 16, "w": w, "h": h})
    link(rooms)
    return rooms, cases


def gen_over():
    rooms = []
    cases = []
    for i, cells in enumerate((49000, 50000, 50009, 50010, 50011, 50012, 50013, 50014, 50015, 50020, 50024, 50040)):
        wh = factor_rect(cells)
        if wh is None:
            raise SystemExit("no factors of %d" % cells)
        w, h = wh
        r = Room(i, (3000, 3000, w - 20, h - 20), [], "V%d" % i)
        rooms.append(r)
        cases.append({"type": 0, "refresh": 0, "pattern": 0, "mask": 1, "b1C": 0, "room": r.addr, "troom": r.addr,
                      "s": 3005 | 3005 << 16, "t": 3006 | 3005 << 16, "w": w, "h": h, "cells": cells})
    link(rooms)
    return rooms, cases


FAMILIES = ("real0", "real16", "stair", "corr", "open", "rect", "grid", "over")
COMMON = ("h", "cost", "fgt", "cellle", "regrid", "min2", "rectend", "radius", "margin")
CONTROLS = {
    "real0": COMMON + ("step",), "real16": COMMON + ("tries", "row", "draw", "half"), "stair": ("max77", "min2", "draw"),
    "corr": ("nodes",), "open": ("h", "cost", "tries", "row", "fgt", "cellle", "step", "regrid", "passes", "draw", "half"),
    "rect": ("union", "rectend", "h", "row"),
}
_CACHE = {}


def family(fam, d):
    if fam in _CACHE:
        return _CACHE[fam]
    rnd = random.Random("r54b-" + fam)
    if fam in ("real0", "real16"):
        rooms = load_real(d)
        cases = gen_real(rnd, rooms, 0 if fam == "real0" else 16, 800 if fam == "real0" else 400)
    elif fam == "stair":
        rooms, cases = gen_stair(rnd)
    elif fam == "corr":
        rooms, cases = gen_corr(rnd)
    elif fam == "open":
        rooms, cases = gen_open(rnd)
    elif fam == "rect":
        rooms, cases = gen_rect(rnd)
    elif fam == "grid":
        rooms, cases = gen_grid(rnd)
    else:
        rooms, cases = gen_over()
    pr = random.Random("r54b-poison-" + fam)
    for c in cases:
        c["poison"] = bytes(pr.getrandbits(8) for _ in range(POINTS_DUMP))
    _CACHE[fam] = (rooms, cases)
    return rooms, cases


def cmd_cases(d):
    for fam in FAMILIES:
        rooms, cases = family(fam, d)
        obs = {"grid": (ASSERT, MEMSET), "over": (AFTER_MEMSET, ASSERT)}.get(fam, ())
        with open(os.path.join(d, fam + ".mem"), "w") as f:
            f.write("\n".join(base_spec(rooms, obs)) + "\n")
        with open(os.path.join(d, fam + ".cases"), "w") as f:
            for c in cases:
                L = case_lines(c, c["poison"])
                if fam == "over":
                    L.insert(-1, "d %08x 12" % EBP_RUN)
                f.write("\n".join(L) + "\n")
        print("CASES %s %d rooms=%d" % (fam, len(cases), len(rooms)))


# -------------------------------------------------------------------------------------------------------- the check
def read_out(path):
    calls, traced = [], []
    for ln in open(path):
        p = ln.split()
        if not p:
            continue
        if p[0] == "C":
            c = {"n": int(p[1]), "dumps": {}, "u": []}
            if p[3] == "STOP":
                c["stop"] = " ".join(p[4:])
            elif p[3] == "OBS":
                c["obs"] = int(p[4], 16)
                kv = dict(x.split("=") for x in p[5:])
                c["regs"] = {k: int(v, 16) for k, v in kv.items()}
            else:
                kv = dict(x.split("=") for x in p[3:])
                c["eax"] = int(kv["eax"], 16)
                c["pop"] = int(kv["pop"])
                c["steps"] = int(kv["steps"])
            calls.append(c)
        elif p[0] == "A":
            calls[-1]["args"] = bytes.fromhex(p[1])
        elif p[0] == "U":
            calls[-1]["u"].append((int(p[1], 16), int(p[2], 16), int(p[3]), int(p[4])))
        elif p[0] == "D":
            calls[-1]["dumps"][int(p[1], 16)] = bytes.fromhex(p[2]) if len(p) > 2 else b""
        elif p[0] in ("R", "W"):
            traced.append(ln.strip())
    return calls, traced


def table_of(a):
    for k, (lo, n) in TABLES.items():
        if lo <= a < lo + n:
            return k
    return None


def same(c, case, want):
    """The emulator's return and dumps against the model's outcome."""
    if "eax" not in c or c.get("pop") != 0:
        return False
    if c["eax"] != want["eax"]:
        return False
    pts = bytearray(case["poison"])
    if want["points"] is not None:
        for i, p in enumerate(want["points"]):
            struct.pack_into("<I", pts, 4 * i, p)
    if c["dumps"].get(UPATH + 0x9C) != bytes(pts):
        return False
    if c["dumps"].get(CTX + 0x14) != bytes([case["refresh"] * 2 & 0xFF]):
        return False
    ctx = struct.pack("<HHHHII", case["s"] & 0xFFFF, case["s"] >> 16, case["t"] & 0xFFFF, case["t"] >> 16, case["room"],
                      case["troom"])
    if c["dumps"].get(CTX) != ctx:
        return False
    if case["type"] == 16 and c["dumps"].get(UNIT + 0x20) != struct.pack("<II", *want["seed"]):
        return False
    return True


def outcome_key(o):
    return (o["eax"], tuple(o["points"]) if o["points"] else None, o.get("seed"))


def boundary_want(case, fam):
    w, h = case["w"], case["h"]
    if s32(w * h) > 50000:
        return ("assert", SITE_ASSERT, 0x171)
    if fam == "grid":
        return ("memset", SITE_MEMSET, GRID_AT, 0, u32((w + 6) * (h + 6) * 4))
    return ("after",)


def check_boundary(fam, c, case, shift=0):
    want = boundary_want(case, fam)
    if want[0] == "after":
        if c.get("obs") != AFTER_MEMSET + shift:
            return False
        n = (case["cells"]) * 4                                       # the clear's bytes from the grid's start
        # the saved EBP, return address and argument, each zero where the clear reached it
        got = c["dumps"].get(EBP_RUN)
        words = struct.unpack("<III", got)
        ok = True
        for k, keep in zip(range(3), (EBP_PLAN, 0x0067ADB9, CTX)):
            off = 0x30D68 + 4 * k
            ok &= words[k] == (0 if n >= off + 4 else keep)
        return ok
    if want[0] == "assert":
        if c.get("obs") != ASSERT + shift or "args" not in c:
            return False
        ret, a1 = struct.unpack_from("<II", c["args"], 0)
        return ret == want[1] and a1 == want[2]
    if c.get("obs") != MEMSET + shift or "args" not in c:
        return False
    ret, p, v, n = struct.unpack_from("<IIII", c["args"], 0)
    return (ret, p, v, n) == want[1:]


def check_family(fam, d):
    rooms, cases = family(fam, d)
    R = {r.addr: r for r in rooms}
    calls, traced = read_out(os.path.join(d, fam + ".out"))
    bad, match, stops = [], 0, 0
    tags, accu, sites = {}, {}, {}
    ctl = {n: [0, 0, 0] for n in CONTROLS.get(fam, ())}                  # separating, passed, separating at type 0
    site = 0
    steps = 0
    if len(calls) != len(cases):
        bad.append("case count %d != %d" % (len(calls), len(cases)))
    memo = {}
    stat = {"maxvisits": 0, "maxiters": 0, "maxnodes": 0, "maxpoints": 0, "draws": 0, "startout": 0}
    for c, case in zip(calls, cases):
        for pc, addr, size, un in c["u"]:
            k = U_OK.get(pc)
            if k is None:
                bad.append("case %d scratch read pc=%08x addr=%08x size=%d unwritten=%d" % (c["n"], pc, addr, size, un))
            else:
                accu[k] = accu.get(k, 0) + 1
        if "stop" in c:
            stops += 1
            bad.append("case %d STOP %s" % (c["n"], c["stop"]))
            continue
        if fam in ("grid", "over"):
            ok = check_boundary(fam, c, case)
            match += ok
            kind = boundary_want(case, fam)[0]
            tags[kind] = tags.get(kind, 0) + 1
            sites[kind] = sites.get(kind, 0) + 1
            site += check_boundary(fam, c, case, 1)
            if not ok:
                bad.append("case %d boundary %s obs=%s args=%s" % (c["n"], boundary_want(case, fam), hex(c.get("obs", 0)),
                                                                  c.get("args", b"")[:16].hex()))
            continue
        S = Search(case, R, memo)
        want = S.run()
        steps += c.get("steps", 0)
        ok = same(c, case, want)
        match += ok
        tags[want["tag"]] = tags.get(want["tag"], 0) + 1
        stat["maxvisits"] = max(stat["maxvisits"], want["visits"])
        stat["maxiters"] = max(stat["maxiters"], want["iters"])
        stat["maxnodes"] = max(stat["maxnodes"], want["nodes"])
        stat["maxpoints"] = max(stat["maxpoints"], want["eax"])
        stat["draws"] += want["draws"]
        stat["startout"] += want["startout"]
        if not ok:
            bad.append("case %d mismatch s=%x t=%x type=%d want eax=%d %s got eax=%s" % (
                c["n"], case["s"], case["t"], case["type"], want["eax"], want["tag"], c.get("eax")))
        for n in ctl:
            if n in ("draw", "half") and case["type"] != 16:
                continue
            nw = Search(case, R, memo, neg=n).run()
            if nw.get("assert"):
                ctl[n][0] += 1
                ctl[n][2] += case["type"] == 0
                continue
            if outcome_key(nw) != outcome_key(want):
                ctl[n][0] += 1
                ctl[n][2] += case["type"] == 0
                ctl[n][1] += same(c, case, nw)
    acc, rest = {}, []
    for t in traced:
        p = t.split()
        k = table_of(int(p[2], 16)) if p[0] == "R" else None
        if k:
            acc[k] = acc.get(k, 0) + int(p[4])
        else:
            rest.append(t)
    line = "PATH54 %s cases=%d match=%d bad=%d stopped=%d traced=%d accounted=%s scratch=%s steps=%d %s %s" % (
        fam, len(cases), match, len(bad), stops, len(rest), ",".join("%s:%d" % kv for kv in sorted(acc.items())) or "-",
        ",".join("%s:%d" % kv for kv in sorted(accu.items())) or "-", steps,
        " ".join("%s=%d" % kv for kv in stat.items()) if fam not in ("grid", "over") else "site_control_passed=%d" % site,
        " ".join("%s_separating=%d %s_type0=%d %s_passed=%d" % (n, ctl[n][0], n, ctl[n][2], n, ctl[n][1]) for n in ctl))
    return line, bad[:25], rest[:25], tags, ctl, site


def cmd_check(d):
    allok = True
    tot = [0, 0]
    for fam in FAMILIES:
        line, bad, traced, tags, ctl, site = check_family(fam, d)
        print(line)
        print("  OUTCOMES " + " ".join("%s:%d" % kv for kv in sorted(tags.items())))
        for b in bad:
            print("  BAD", b)
        for t in traced:
            print("  TRACED", t)
        if bad or traced or site or any(ctl[n][1] for n in ctl) or any(ctl[n][0] == 0 for n in ctl):
            allok = False
        tot[0] += int(line.split("cases=")[1].split()[0])
        tot[1] += int(line.split("match=")[1].split()[0])
    print("PATH54 total cases=%d match=%d" % tuple(tot))
    print("PATH54 result=%s" % ("ok" if allok else "FAIL"))


# ---------------------------------------------------------------------------------------------- bounds, stores, manifest
def cmd_bounds():
    print("BOUND frame: grid at frame+0x6290, flag at frame+0x36FD0: %d bytes = %d cells to the flag; EBP - grid = 0x30D68 = %d bytes"
          % (0x30D40, 0x30D40 // 4, 0x30D68))
    print("BOUND cells=(w+6)(h+6): the clear reaches: flag fields past 50000 (reset after the clear), saved EBP at 50011, return at 50012, ctx argument at 50013")
    print("BOUND square rect: w=h=%d: cells=%d (fits, <= 50010); w=h=%d: cells=%d, w*h=%d (passes the assert, overruns)" % (
        217, 223 * 223, 218, 224 * 224, 218 * 218))
    print("BOUND square rect: w=h=223: w*h=%d passes; w=h=224: w*h=%d asserts" % (223 * 223, 224 * 224))
    best = None
    for w in range(1, 8000):
        h = 50010 // (w + 6) - 6 + 1
        if h >= 1 and w * h <= 50000 and (w + 6) * (h + 6) > 50010 and (best is None or w * h < best[2]):
            best = (w, h, w * h)
    print("BOUND smallest w*h whose cells pass 50010: w=%d h=%d w*h=%d" % best)
    print("BOUND same-room rect is room + 20: a room of %dx%d fits (cells %d), %dx%d overruns (cells %d)" % (
        197, 197, 223 * 223, 198, 198, 224 * 224))
    print("BOUND imul w*h i32: 46340^2=%d fits, 46341^2=%d wraps to %d (the assert passes)" % (
        46340 ** 2, 46341 ** 2, s32(46341 ** 2)))
    print("BOUND h under PathPlan's window: |dx|,|dy|<=100: h0 <= 2*100+100 = 300; type 16 first bound h0 + h0/2 <= 450")
    print("BOUND g <= f <= bound; every step costs >= 2: depth <= bound/2")
    print("BOUND type 0: bounds h0, h0+5, ... while < max(h0, b1C): the last is h0 or < b1C <= 255: last <= max(300, 254) = 300; depth <= 150; nodes <= 151")
    print("BOUND type 16: first bound h0 + h0/2 <= 450, then < max(first, b1C): last <= max(450, 254) = 450; depth <= 225; nodes <= 226 < 900")
    print("BOUND passes: at most 1 + (255 - 0 - 1) // 5 = %d bounds a search (h0 >= 2); 10 000 passes each" % (1 + 254 // 5))
    print("BOUND points: kept steps stop at 78 stored; n in 2..77 is copied; 78 returns 0; 77*4 = %d bytes <= the record's 78*4 = %d" % (
        77 * 4, 78 * 4))
    print("BOUND local point buffer 0x148 - 0x10 = %d bytes = %d slots" % (0x148 - 0x10, (0x148 - 0x10) // 4))
    print("BOUND a route of 78 corners inside the window: staircase dx=78, dy=39, g = h0 = %d <= 300" % (2 * 78 + 39))
    print("BOUND g, f are u16 read as i16: g <= 899 * 3 = %d at the store's end; f = g + h stays below 32768 while h does (|dx|, |dy| <= 10000: h <= 30000 with g <= 2697)" % (899 * 3))


def cmd_stores(writers, exe):
    rows = [ln.split() for ln in open(writers) if ln.startswith("W ")]
    syms = []
    import csv
    for r in list(csv.reader(open(os.path.join(ROOT, "re", "symbols.csv"))))[1:]:
        if r[1] == "func":
            syms.append((int(r[0], 16), r[2], r[5]))
    syms.sort()
    n = 0
    for r in rows:
        a = int(r[1], 16)
        if not 0x00589000 <= a <= 0x00594647:
            continue
        n += 1
        f = [s for s in syms if s[0] <= a][-1]
        base = re.search(r"\[(e[a-z]{2})\+", " ".join(r[2:])).group(1)
        o = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=%#x" % f[0],
                            "--stop-address=%#x" % (a + 8), exe], capture_output=True, text=True).stdout.splitlines()
        loads = [ln.strip() for ln in o if re.search(r"mov\s+%s,|lea\s+%s," % (base, base), ln)
                 or re.search(r"call\s+0x543640", ln)]
        print("STORE %08x %s fn=%08x %s sub=%s" % (a, " ".join(r[2:]), f[0], f[1], f[2]))
        for ln in loads[-4:]:
            print("   ", re.sub(r"\s+", " ", ln))
    print("SCAN path stores n=%d" % n)


def cmd_manifest(d, write):
    rows = []
    for fn in sorted(os.listdir(d)):
        p = os.path.join(d, fn)
        if os.path.isfile(p) and fn != "manifest.sha256":
            rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), fn))
    text = "\n".join(rows) + "\n"
    if write:
        with open(os.path.join(d, "manifest.sha256"), "w") as f:
            f.write(text)
    sys.stdout.write(text)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["grids", "cases", "check", "bounds", "stores", "manifest"])
    ap.add_argument("rest", nargs="*")
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "grids":
        cmd_grids(a.dir)
    elif a.cmd == "cases":
        cmd_cases(a.dir)
    elif a.cmd == "check":
        cmd_check(a.dir)
    elif a.cmd == "bounds":
        cmd_bounds()
    elif a.cmd == "stores":
        cmd_stores(a.rest[0], a.rest[1])
    else:
        cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    main(sys.argv[1:])

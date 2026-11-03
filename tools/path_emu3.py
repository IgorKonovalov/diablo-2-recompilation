#!/usr/bin/env python3
"""Plan 0054 Phase 1.3 (`lane/r54c`): the short planners run under Ghidra's p-code emulator (ADR-0015, ADR-0021) with
re/ghidra_scripts/EmuScratch.java over declared images, and compared with the models below. No game run, no slot.
docs/findings/path/0003-short-planners.md.

    python3 -I tools/path_emu3.py grids  [--dir D]     predict the room blocks (path_emu2's kept command) into D
    python3 -I tools/path_emu3.py cases  [--dir D]     write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuscratch D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/path_emu3.py check  [--dir D]     compare every D/<family>.out with the model, account for every
                                                       traced access and scratch read, run the controls and the probes
    python3 -I tools/path_emu3.py bounds               the kept integer computations (point counts against 78 slots)
    python3 -I tools/path_emu3.py stock                Missiles rows of the H1 classes: Range, cap, draws per seed
    python3 -I tools/path_emu3.py scan3c <game.exe>    the kept scan of +0x3C stores (P1.3b) over the whole of .text
    python3 -I tools/path_emu3.py h1log <log>...       every logged callback creation (MCB0/MCB1, MC0/MC1) of the kept skills logs against the model:
                                                       draws = min(range, 77) >> 1 from the Init, the range after the callback
    python3 -I tools/path_emu3.py manifest [--dir D] [--write]

Default D: workspace/logs/r54c/emu. Every case draw comes from random.Random("r54c-<family>"); `cases` reads the blocks `grids`
wrote, so both regenerate identical files.

The entry (ruling 2 of the P1.1 review). Every case enters the planner with ECX a declared PathPlanCtx (the IsBadCodePtr import
blocks a run through PathPlan), except PathPlanRandomWalk and PathPlanSpiral (ECX the path, EDX the seed pointer, as
PathPlanStraight calls them, which PathPlan reaches before the import) and the callbacks (family h1: the whole of
0x005C9290 / 0x005AC040, through PathSetType, PathSetByte90 and PathPlan's flag 0x40000 branch). The context's +0x0C, +0x10, +0x1C,
+0x20 and +0x24 stay undeclared, so a read of one is a traced access and fails the family. The path record is written whole,
512 seeded random bytes under the declared fields and compared whole, so a read of a field the model does not use shows as a
mismatch by chance only; ctx.limit (+0x18) and path +0x91 differ on purpose, as do ctx.start and the position, and ctx.room and
path +0x1C in a share of the cases. The frames stay on the declared stack as scratch: a U line outside U_OK fails its case.

The images: path_emu2's (real blocks: tools/collision.py's predicted cells of four kept run:2026-10-14-collision logs, each once as
predicted and once with seeded unit marks; near lists declared; synthetic rooms for the branches stock cells seldom reach). The
collision tests run inside each case, edge branches included. A start's own marks are kept off, as PathPlan leaves them.

Families: probe (kept negative checks of EmuScratch and this check: they must FAIL); greedy (types 2, 13 on real blocks), g98 (types 5, 6:
the +0x98 walk), gbound (a carved corridor that turns at every step: the point bound), near (type 7 with the type-1 switch), knock
(type 8), onept (type 9), t1real, t1syn, t1stair (type 1), t15real, t15syn, t15stair (type 15), rwalk (type 10), spiral and spiralobs (type
14: x87, see ADR-0015; spiralobs the integer arguments at the first table read), h1 and h1obs (the callbacks to their return, and to PathPlan's entry), client (types 3, 11, 12).

Each family's controls must fail every case they separate, and pass none. Not covered (ADR-0021): PathPlan's tail after the planner. Stdlib only.
"""
import argparse
import csv
import hashlib
import math
import os
import random
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import path_emu1 as P1                                     # noqa: E402
import path_emu2 as P2                                     # noqa: E402
import path_scan                                           # noqa: E402

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r54c", "emu")
CTX, UPATH, UNIT = 0x12700000, 0x12200000, 0x12100000
TARGET, TPATH, MDATA = 0x12400000, 0x12B00000, 0x12C00000
ASSERT = 0x00408090
A = 0x6AC690C5
GREEDY, NEAR, ONEPT, KNOCK, SPIRAL, RWALK, TYPE1, TYPE15 = (0x00679C80, 0x00679ED0, 0x00679F70, 0x0067A000, 0x0067A140, 0x0067A240,
                                                            0x0067B850, 0x0067C2D0)
T3, T11, T12 = 0x00679E50, 0x00679FD0, 0x00679E60
CB_PLUS, CB_X = 0x005C9290, 0x005AC040
PATHPLAN = 0x00649970
SINCOS = 0x0040B330
SITES = {0x34: 0x00679402, 0x4C: 0x00679402, 0x144: 0x00679A83, 0x145: 0x00679A83, 0x146: 0x00679A83, 0x147: 0x00679A83,
         0x122: None, 0x1BB: 0x0067C07F, 0x2AD: None}
# scratch reads accounted, by pc, size and unwritten bytes (P1.2 check): _chkstk's page probes only, unless a family's list adds one
U_OK = {(0x006831D7, 4, 4): "chkstk"}
# the dword read at 0x0067C3D6 with i = nv after follow (a truncation writes L[i]'s x word only, a splice neither): stored as `cur` and never
# used, since the loop then ends (i + 1 > nv); accounted only in a case whose model made that read (check_family)
U_T15 = ((0x0067C3D6, 4, 2), (0x0067C3D6, 4, 4))
TABLES = {
    "dirs": (0x006F1518, 300), "dist": (0x006F1698, 256), "step8": (0x006F1798, 64), "hash": (0x006F1998, 0x400),
    "drawadd": (0x006F18D8, 128), "walk": (0x006F1D98, 0x1A8), "jt_follow": (0x0067C1D0, 16), "sine": (0x00707800, 512 * 4 + 0x200),
    "jt_ptb": (0x0064D994, 24), "jt_plus": (0x0064D784, 52), "sse": (0x00994C88, 4), "jt_memcpy": (0x00682AC0, 0x78),
    "jt_memmove": (0x00683940, 0x240), "t1648": (0x006F1648, 75), "t98": (0x006EB648, 68), "flags": (0x006EB690, 68),
    "dirtab": (0x006EB7E0, 128 * 12), "d4d8": (0x006EB7D4, 8), "t548": (0x006EB548, 256),
}


class Assert(Exception):
    def __init__(self, line):
        Exception.__init__(self, "assert %x" % line)
        self.line = line


class Image:
    def __init__(self):
        self.data = open(P2.EXE, "rb").read()
        if hashlib.sha256(self.data).hexdigest() != P2.PINNED:
            raise SystemExit("path_emu3: not the pinned Game.exe")
        self.dirs = struct.unpack("<75i", path_scan.va_bytes(self.data, 0x006F1518, 300))
        self.step = [struct.unpack_from("<ii", path_scan.va_bytes(self.data, 0x006F1798, 64), 8 * d) for d in range(8)]
        self.dist = struct.unpack("<64i", path_scan.va_bytes(self.data, 0x006F1698, 256))
        self.sine = struct.unpack("<512f", path_scan.va_bytes(self.data, 0x00707800, 2048))

    def d32(self, a):
        return struct.unpack("<i", path_scan.va_bytes(self.data, a, 4))[0]


IMG = None


def img():
    global IMG
    if IMG is None:
        IMG = Image()
    return IMG


def mk(x, y):
    return (x & 0xFFFF) | (y & 0xFFFF) << 16


def X(p):
    return p & 0xFFFF


def Y(p):
    return p >> 16 & 0xFFFF


class C:
    """A case's context as the planner reads it."""

    def __init__(self, c, R, M, neg=None):
        self.s, self.t, self.room, self.refresh, self.limit = c["s"], c["t"], c["room"], c["refresh"], c["limit"]
        self.pattern, self.mask = c["pattern"], c["mask"]
        self.R, self.M, self.neg = R, M, neg
        self.stat = {"tests": 0, "maxstack": 0, "nodes": 0, "walk": 0, "ovl": 0}

    def path(self, off, n=4):
        return {1: self.M.r8, 2: self.M.r16, 4: self.M.r32}[n](UPATH + off)

    def setp(self, off, v):
        self.M.w32(UPATH + off, v, False)

    def test(self, x, y):
        self.stat["tests"] += 1
        return P2.ptb(self.R, self.room, x & 0xFFFF, y & 0xFFFF, self.pattern, self.mask)

    def setpt(self, i, p):
        if i >= 0x59:
            self.stat["ovl"] += 1
        self.M.w32(UPATH + 0x9C + 4 * i, p, False)

    def unit_ok(self, line):
        u = self.M.r32(UPATH + 0x30)
        if not u or self.M.r32(u) not in (0, 1):
            raise Assert(line)


def line_of_sight(c, s, t):
    """0x00679720 (EAX path; s, &t): the path's room, pattern and mask. 1 when every cell to t is free, else 0 and the last free point."""
    hint, pat, mask = c.path(0x1C), c.path(0x48), c.path(0x50)
    if c.neg == "ctxroom":
        hint = c.room

    def blocked(x, y):
        c.stat["tests"] += 1
        return P2.ptb(c.R, hint, x & 0xFFFF, y & 0xFFFF, pat, mask)
    sx, sy, tx, ty = X(s), Y(s), X(t), Y(t)
    dx, dy = tx - sx, ty - sy
    ax, ay = abs(dx) + 1, abs(dy) + 1
    px = 1 if dx >= 0 else -1
    py = 1 if dy >= 0 else -1
    x, y = sx, sy
    last = s
    if ax > ay:
        err = ay
        while True:
            x = (x + px) & 0xFFFF
            if blocked(x, y):
                return 0, last
            err += ay
            if err >= ax:
                y = (y + py) & 0xFFFF
                err -= ax
                if err > 0 and blocked(x, y):
                    return 0, last
            last = mk(x, y)
            if x == tx:
                return 1, t
    if ax < ay:
        err = ax
        while True:
            y = (y + py) & 0xFFFF
            if blocked(x, y):
                return 0, last
            err += ax
            if err >= ay:
                x = (x + px) & 0xFFFF
                err -= ay
                if err > 0 and blocked(x, y):
                    return 0, last
            last = mk(x, y)
            if y == ty:
                return 1, t
    if sx == tx:
        return 1, t
    while True:
        x, y = (x + px) & 0xFFFF, (y + py) & 0xFFFF
        if blocked(x, y):
            return 0, last
        last = mk(x, y)
        if x == tx:
            return 1, t


def pos_pt(c):
    return mk(c.path(2, 2), c.path(6, 2))


def step_first(c, pt):
    """0x00679A60 (ESI path, EDI &pt): the aim, then the line from the position. Returns (reached, pt)."""
    c.unit_ok(0x144)
    if c.path(0x3C) == 4:
        raise Assert(0x145)
    if X(pt) == 0:
        raise Assert(0x146)
    if Y(pt) == 0:
        raise Assert(0x147)
    if c.path(0x7C) == 0:
        return 0, pos_pt(c)
    P1.aim(c.M, UPATH, 1, 1)
    if c.path(0x7C) == 0:
        return 0, pos_pt(c)
    return line_of_sight(c, pos_pt(c), pt)


def dist8(a, b, neg=None):
    """0x00679380."""
    dx, dy = abs(X(a) - X(b)), abs(Y(a) - Y(b))
    if dx < 8 and dy < 8 and neg != "dist":
        v = img().dist[dx + 8 * dy]
        return 0 if v < 0 else v + 1
    return dy + 2 * dx if dx > dy else dx + 2 * dy


def triple(a, b):
    q = P2.dir_index(a, b)
    I = img()
    return [I.dirs[3 * q], I.dirs[3 * q + 1], I.dirs[3 * q + 2]]


def try3(c, s, tr):
    """0x006793E0 (EAX ctx; s, &triple, &out): the first free of the three."""
    c.unit_ok(0x34)
    I = img()
    order = tr[::-1] if c.neg == "order" else tr
    for k, d in enumerate(order):
        if k == 2 and d == 0xFF:
            raise Assert(0x4C)
        dx, dy = I.step[d]
        if not c.test(X(s) + dx, Y(s) + dy):
            return d
    return None


def greedy(c):
    """sub_00679C80_PathPlanGreedy."""
    I = img()
    c.setp(0x24, 0)
    c.setp(0x28, 0)
    if c.path(0x98) != 0:
        return walk98(c)
    pt = c.t
    c.setp(0x9C, c.t)
    r, pt = step_first(c, pt)
    if r:
        c.setpt(0, pt)
        c.setp(0x28, 1)
        return 1
    if dist8(pt, c.t, c.neg) <= (0 if c.neg == "refresh" else c.refresh):
        c.setpt(0, pt)
        c.setp(0x28, 1)
        return 1
    cur = c.s
    cnt = 0
    if c.s != pt:
        c.setpt(0, pt)
        cnt = 1
        cur = pt
    c.setp(0x28, cnt)
    limit = P2.s32(c.limit)
    if c.neg == "limit":
        limit += 1
    prev, flag, i = 0xFF, 0, 0
    if limit > 0:
        while True:
            if cur == c.t:
                if flag == 0 or c.neg == "noflag":
                    if i:
                        c.setpt(cnt, cur)
                        cnt += 1
                break
            tr = triple(cur, c.t)
            flag = 0
            d = try3(c, cur, tr)
            if d is None or ((d - 4) & 7 == prev and c.neg != "rev"):
                if i:
                    c.setpt(cnt, cur)
                    cnt += 1
                break
            dx, dy = I.step[d]
            new = mk(X(cur) + dx, Y(cur) + dy)
            if d != prev:
                if cur != c.s:
                    c.setpt(cnt, cur)
                    cnt += 1
                flag = 1
            cur, prev = new, d
            i += 1
            if i >= limit:
                if flag == 0 or c.neg == "noflag":
                    c.setpt(cnt, cur)
                    cnt += 1
                break
    c.setp(0x28, cnt)
    c.stat["cnt"] = cnt
    return cnt


def walk98(c):
    """0x00679B30: the walk with +0x98 added to the triple, from the start, appended at +0x28."""
    I = img()
    cnt = c.path(0x28)
    param = 0 if c.neg == "param0" else P2.s32(c.path(0x98))
    limit = P2.s32(c.limit)
    cur = c.s
    prev, flag, i = 0xFF, 0, 0
    if limit > 0:
        while True:
            if cur == c.t:
                if flag == 0 and i:
                    c.setpt(cnt, cur)
                    cnt += 1
                break
            tr = [(v + param) & 7 for v in triple(cur, c.t)]
            flag = 0
            d = try3(c, cur, tr)
            if d is None or (d - 4) & 7 == prev:
                if i:
                    c.setpt(cnt, cur)
                    cnt += 1
                break
            dx, dy = I.step[d]
            new = mk(X(cur) + dx, Y(cur) + dy)
            if d != prev:
                c.setpt(cnt, cur)
                cnt += 1
                flag = 1
            cur, prev = new, d
            i += 1
            if i >= limit:
                if flag == 0:
                    c.setpt(cnt, cur)
                    cnt += 1
                break
    c.setp(0x28, cnt)
    c.stat["cnt"] = cnt
    return cnt


def near(c):
    """sub_00679ED0_PathPlanGreedyNear."""
    c.setp(0x24, 0)
    c.setp(0x28, 0)
    n = greedy(c)
    if n:
        p = c.path(0x98 + 4 * n)
        if dist8(p, c.t) <= c.refresh and p != c.s:
            return n
    d2 = (X(c.s) - X(c.t)) ** 2 + (Y(c.s) - Y(c.t)) ** 2
    if d2 > (325 if c.neg == "le325" else 324):
        return n
    c.stat["t1"] = 1
    r = type1(c)
    if r:
        return r
    if n == 0:
        return 0
    return 0 if c.neg == "noretry" else greedy(c)


def onept(c):
    """sub_00679F70_PathPlanOnePoint."""
    c.setp(0x24, 0)
    pt = c.t
    c.setp(0x9C, pt)
    _, pt = step_first(c, pt)
    if pt == c.s:
        return 0
    c.setp(0x9C, pt)
    c.setp(0x28, 1)
    return 1


def type11(c):
    """0x00679FD0: as the one point, the point kept in place, always 1."""
    c.setp(0x24, 0)
    c.setp(0x9C, c.t)
    _, pt = step_first(c, c.t)
    c.setp(0x9C, pt)
    return 1


def type3(c):
    """0x00679E50: +0x24 cleared, then the greedy planner."""
    c.setp(0x24, 0)
    return greedy(c)


def type12(c):
    """0x00679E60: the +0x98 walk at -4, then appended at -2, or at +2 when -2 added nothing."""
    c.setp(0x24, 0)
    c.setp(0x98, 0xFFFFFFFC)
    n = walk98(c)
    if not n:
        return 0
    c.setp(0x28, n)
    c.setp(0x98, 0xFFFFFFFE)
    v = walk98(c)
    if v == n:
        c.setp(0x98, 2)
        v = walk98(c)
    c.setp(0x98, 0xFFFFFFFC)
    return v


def knock(c):
    """sub_0067A000_PathPlanKnockback."""
    M = c.M
    k = (c.path(0x90, 1) >> 1) + (0 if c.neg == "k" else 1)
    u = c.path(0x58)
    if u:
        pt = c.s
        t = M.r32(u)
        p = M.r32(u + 0x2C)
        if t == 2 or 4 <= t <= 5:
            tx, ty = M.r32(p + 0xC), M.r32(p + 0x10)
        elif p:
            tx, ty = M.r16(p + 2), M.r16(p + 6)
        else:
            tx, ty = 0, 0
        dx, dy = P2.s32(X(c.s) - tx), P2.s32(Y(c.s) - ty)
        m = abs(dx) if abs(dx) > abs(dy) else abs(dy)
        if m:
            if c.neg == "floor":
                dx, dy = k * dx // m, k * dy // m
            else:
                dx, dy = int(math.copysign(abs(k * dx) // m, dx)), int(math.copysign(abs(k * dy) // m, dy))
        pt = mk(X(pt) + dx, Y(pt) + dy)
    else:
        pt = c.t
    c.setp(0x9C, pt)
    r, q = line_of_sight(c, c.s, pt)
    if not r:
        pt = q
    M.w16(UPATH + 0x10, X(pt), False)
    M.w16(UPATH + 0x12, Y(pt), False)
    c.setp(0x58, 0)
    if pt == c.s:
        return 0
    c.setp(0x9C, pt)
    c.setp(0x28, 1)
    return 1


# ------------------------------------------------------------------------------------------------------ type 1
class N:
    __slots__ = ("pt", "f", "h", "g", "parent", "kids")

    def __init__(self):
        self.pt = self.f = self.h = self.g = 0
        self.parent = None
        self.kids = []


def oct16(a, b, neg=None):
    dx, dy = abs(X(a) - X(b)), abs(Y(a) - Y(b))
    if neg == "h":
        return max(dx, dy) + 2 * min(dx, dy)
    return dy + 2 * dx if dx >= dy else dx + 2 * dy


def t1_cost(a, b, neg=None):
    if X(a) == X(b):
        return 2
    if Y(a) == Y(b):
        return 2
    return 2 if neg == "cost" else 3


def type1(c):
    """sub_0067B850_PathPlanType1: best-first over a 200-node pool."""
    neg = c.neg
    if c.path(0x58) and neg != "nostart":                         # 0x0067B740
        x, y = X(c.t), Y(c.t)
        for a, b in ((-2, -2), (-2, 2), (2, -2), (2, 2), (-2, 0), (0, -2), (2, 0), (0, 2)):
            if not c.test(x + a, y + b):
                break
        else:
            return 0
    pool = 201 if neg == "pool" else 200
    opened, closed, lst = {}, {}, []
    count = 1
    root = N()
    root.pt, root.h, root.f = c.s, oct16(c.s, c.t, neg), oct16(c.s, c.t, neg)

    def insert(n):
        k = 0
        while k < len(lst) and P2.s16(lst[k].f) < P2.s16(n.f) + (1 if neg == "list" else 0):
            k += 1
        lst.insert(k, n)
    opened[root.pt] = root
    insert(root)
    best = None
    offs = ((-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (0, -1), (1, 0), (0, 1))
    if neg == "offs":
        offs = offs[4:] + offs[:4]
    while lst:
        n = lst.pop(0)
        del opened[n.pt]
        closed[n.pt] = n
        if best is None or P2.s16(n.h) < P2.s16(best.h) or (
                n.h == best.h and P2.s16(n.g) > P2.s16(best.g) + (0 if neg == "gt0" else 5)):
            best = n
        if n.h == 0:
            break
        full = False
        for a, b in offs:
            p = mk(X(n.pt) + a, Y(n.pt) + b)
            if c.test(X(p), Y(p)):
                continue
            g = (n.g + t1_cost(n.pt, p, neg)) & 0xFFFF
            o = opened.get(p)
            if o is None:
                o = closed.get(p)
                if o is not None:
                    if len(n.kids) < 8:
                        n.kids.append(o)
                    if P2.s16(g) < P2.s16(o.g):
                        o.parent, o.g, o.f = n, g, (g + o.h) & 0xFFFF
                        st = [o]
                        while st:
                            c.stat["maxstack"] = max(c.stat["maxstack"], len(st))
                            cu = st.pop()
                            for ki in cu.kids:
                                gg = (cu.g + t1_cost(cu.pt, ki.pt, neg)) & 0xFFFF
                                if P2.s16(gg) < P2.s16(ki.g):
                                    ki.parent, ki.g, ki.f = cu, gg, (gg + ki.h) & 0xFFFF
                                    st.append(ki)
                    continue
                if count >= pool:
                    full = True
                    break
                count += 1
                o = N()
                o.parent, o.g, o.pt = n, g, p
                o.h = oct16(p, c.t, neg)
                o.f = (g + o.h) & 0xFFFF
                opened[p] = o
                insert(o)
                n.kids.append(o)
                continue
            if len(n.kids) < 8:
                n.kids.append(o)
            if P2.s16(g) < P2.s16(o.g):
                o.parent, o.g, o.f = n, g, (g + o.h) & 0xFFFF
                if neg == "resort":
                    lst.remove(o)
                    insert(o)
        if full:
            c.stat["full"] = 1
            break
    c.stat["nodes"] = count
    c.stat["found"] = int(best is not None and best.h == 0)
    # the reduction 0x0067B690
    buf = []
    prev = (-2, -2)
    n = best
    while n is not None and len(buf) < 78:
        p = n.parent
        if p is not None:
            d = (X(n.pt) - X(p.pt), Y(n.pt) - Y(p.pt))
            if d != prev:
                buf.append(n.pt)
                prev = d
        n = p
    k = len(buf)
    c.stat["raw"] = k
    lo, hi = (2 if neg == "min2" else 1), (78 if neg == "max77" else 77)
    if not lo <= k <= hi:
        return 0
    for i, p in enumerate(reversed(buf)):
        c.setpt(i, p)
    return k


# ----------------------------------------------------------------------------------------------------- type 15
def line15(a, b, limit):
    """0x0067B9F0: the Bresenham cells after a to b; none when the major axis exceeds limit - 1."""
    ax, ay, bx, by = X(a), Y(a), X(b), Y(b)
    dx, dy = bx - ax, by - ay
    px = 1 if dx >= 0 else -1
    py = 1 if dy >= 0 else -1
    dx, dy = abs(dx), abs(dy)
    lim = limit - 1
    out = []
    if dx == 0:
        if dy < 1:
            return out, 0
        dc = 2 if py > 0 else 0
        if dy > lim:
            return out, dc
        y = ay
        for _ in range(dy):
            y += py
            out.append(mk(ax, y))
        return out, dc
    if dy == 0:
        dc = 3 if px <= 0 else 1
        if dx > lim:
            return out, dc
        x = ax
        for _ in range(dx):
            x += px
            out.append(mk(x, ay))
        return out, dc
    x, y, err = ax, ay, 0
    if dx < dy:
        dc = 2 if py > 0 else 0
        if dy > lim:
            return out, dc
        for _ in range(dy):
            y += py
            err += dx
            if dy <= err:
                err -= dy
                x += px
            out.append(mk(x, y))
        return out, dc
    dc = 3 if px <= 0 else 1
    if dx > lim:
        return out, dc
    for _ in range(dx):
        x += px
        err += dy
        if dx <= err:
            err -= dx
            y += py
        out.append(mk(x, y))
    return out, dc


class W:
    __slots__ = ("dir", "cnt", "pos", "next", "hard", "t5", "t6", "mark", "stop", "list")


def walker(d, pos, t5, t6):
    w = W()
    w.dir, w.cnt, w.pos, w.next, w.hard, w.t5, w.t6, w.mark, w.stop = d, 0, pos, 0, 0, t5, t6, 0, 0
    w.list = []
    return w


def wstep(c, w):
    """0x0067BBF0 (EAX ctx, ESI walker): the next free of four turns."""
    c.unit_ok(0x122)
    I = img()
    w.hard = 0

    def at():
        dx, dy = I.d32(0x006F1D98 + w.dir * 8), I.d32(0x006F1D9C + w.dir * 8)
        w.next = mk(X(w.pos) + dx, Y(w.pos) + dy)
        return c.test(X(w.next), Y(w.next))
    if not at():
        return 1
    w.dir = I.d32(w.t6 + w.dir * 4)
    if not at():
        return 1
    w.dir = I.d32(w.t6 + w.dir * 4)
    if not at():
        return 1
    w.hard = 1
    w.dir = I.d32(w.t6 + w.dir * 4)
    return 0 if at() else 1


def follow(c, L, cur, st, lim4, dc):
    """0x0067BDF0: two walkers round the block at L[i]. st = [i, nv]."""
    I = img()
    p = L[st[0]]
    q = I.d32(0x006F1E28 + ((Y(p) - Y(cur)) * 3 - X(cur) + X(p)) * 4)
    w0 = walker(q + 1, cur, 0x006F1F00, 0x006F1EC0)
    w1 = walker(q + 7, cur, 0x006F1E80, 0x006F1E40)
    if c.neg == "wswap":
        w0.dir, w1.dir = w1.dir, w0.dir
    a, b = w0, w1
    while True:
        c.stat["walk"] += 1
        skip = a.stop != 0
        if not skip and not wstep(c, a):
            a.stop = 1
            skip = True
        if not skip:
            v = None
            if a.cnt >= 1:
                if dc == 0:
                    v = Y(cur) - Y(a.next)
                elif dc == 1:
                    v = X(a.next) - X(cur)
                elif dc == 2:
                    v = Y(a.next) - Y(cur)
                elif dc == 3:
                    v = X(cur) - X(a.next)
            if v is not None and v > 0:
                idx = v - 1 + st[0]
                if idx < st[1] and L[idx] == a.next:
                    if lim4 <= a.cnt:
                        raise Assert(0x1BB)
                    a.list.append(a.next)
                    a.cnt += 1
                    i, nv = st
                    d = i - idx - 1 + a.cnt
                    new = d + idx
                    moved = L[idx + 1:nv]
                    L[new + 1:new + 1 + len(moved)] = moved
                    L[i:i + a.cnt] = a.list[:a.cnt]
                    st[1] = nv + d
                    st[0] = new + 1
                    c.stat["spliced"] = c.stat.get("spliced", 0) + 1
                    return a.cnt
            if b.cnt > 1:
                if a.mark:
                    if a.next == b.list[a.mark - 2]:
                        st[1] = st[0]
                        L[st[0]] &= 0xFFFF0000
                        c.stat["looped"] = 1
                        return 0
                    a.mark = 0
                if a.next == b.pos:
                    a.mark = b.cnt
            a.list.append(a.next)
            a.cnt += 1
            a.pos = a.next
            a.dir = I.d32(a.t5 + a.dir * 4)
            if (lim4 - st[1]) - 1 <= a.cnt:
                a.stop = 1
        if a.mark == 0 and c.neg != "noswap":
            a, b = b, a
        if w0.stop or w1.stop:
            break
    if lim4 > (0x7FFF if c.neg == "lim50" else 0x50):
        L[st[0]] &= 0xFFFF0000
        st[1] = st[0]
        return 0

    def d2(p, q):
        return (X(p) - X(q)) ** 2 + (Y(p) - Y(q)) ** 2

    def last(w):
        return w.list[w.cnt - 1] if w.cnt else w.stop
    d0, d1, dq = d2(last(w0), c.t), d2(last(w1), c.t), d2(c.s, c.t)
    if d0 < d1:
        if dq < d0:
            return 0
        w = w0
    else:
        if dq < d1:
            return 0
        w = w1
    i = st[0]
    L[i:i + w.cnt] = w.list[:w.cnt]
    st[0] = i + w.cnt
    st[1] = st[0]
    if len(L) > st[0]:
        L[st[0]] &= 0xFFFF0000
    c.stat["trunc"] = c.stat.get("trunc", 0) + 1
    return a.cnt


def reduce15(c, start, L, n):
    """0x0067C1E0: drops a point that continues the last step, and every other point of a one-off kink."""
    if n > 1:
        lx, ly = X(L[0]) - X(start), Y(L[0]) - Y(start)
        o, run = 0, 0
        for j in range(n - 1):
            dx, dy = X(L[j + 1]) - X(L[j]), Y(L[j + 1]) - Y(L[j])
            if c.neg == "reduce":
                c.setpt(o, L[j])
                o += 1
            elif dx == lx and dy == ly:
                run += 1
                lx = dx
            elif run < 1 and lx != dx and ly != dy:
                run = 1
                lx = -2
            else:
                c.setpt(o, L[j])
                o += 1
                run = 0
                lx = dx
            ly = dy
        c.setpt(o, L[n - 1])
        return o + 1
    if n != 1:
        return 0
    c.setpt(0, L[0])
    return 1


def type15(c):
    """sub_0067C2D0_PathPlanType15."""
    c.unit_ok(0x2AD)
    lim = c.path(0x91, 1)
    if c.path(0x58) and lim < 0x28 and c.neg != "lim40":
        lim = 0x28
    if c.neg == "lim18":
        lim = c.limit & 0xFF
    start = cur = c.s
    L, dc = line15(start, c.t, lim)
    n = len(L)
    c.stat["line"] = n
    if n <= (1 if c.neg == "min2" else 2):
        return 0
    L = L + [0] * 400
    L[n] = 0
    st = [0, n]
    while True:
        i = st[0]
        if c.test(X(L[i]), Y(L[i])):
            c.stat["follows"] = c.stat.get("follows", 0) + 1
            r = follow(c, L, cur, st, lim - i, dc)
            if r == 0:
                c.stat["maxn"] = st[0]
                return reduce15(c, start, L, st[0])
        i = st[0]
        if i >= st[1]:
            c.stat["overread"] = 1
        cur = L[i]
        st[0] = i + 1
        if st[0] >= st[1]:
            break
    n = st[1]
    c.stat["maxn"] = n
    if n == 0:
        return 0
    return reduce15(c, start, L, n)


# ------------------------------------------------------------------------------------------- types 10 and 14, H1
def rwalk(M, seed_at, neg=None, stat=None):
    """sub_0067A240_PathPlanRandomWalk (ECX path, EDX &seed)."""
    I = img()
    n = M.r8(UPATH + 0x91)
    n = n if neg == "shr" else n >> 1
    if neg == "n1":
        n += 1
    cur = mk(M.r16(UPATH + 2), M.r16(UPATH + 6))
    base = triple(cur, M.r32(UPATH + 0x10))[0]
    lo, hi = M.r32(seed_at), M.r32(seed_at + 4)
    k = 0
    for k in range(n):
        v = lo * A + hi
        lo, hi = v & 0xFFFFFFFF, v >> 32 & 0xFFFFFFFF
        add = (-1, 0, 1)[(lo & 31) % 3] if (lo & 31) < 30 else (-1, 1)[(lo & 31) - 30]
        d = ((add if neg != "noadd" else 0) + base) & 7
        if neg == "accum":
            base = d
        M.w32(UPATH + 0x9C + 4 * k, cur, False)
        dx, dy = I.step[d]
        m = 1 if neg == "step1" else 2
        cur = mk(X(cur) + m * dx, Y(cur) + m * dy)
    M.w32(seed_at, lo, False)
    M.w32(seed_at + 4, hi, False)
    M.w32(UPATH + 0x9C + 4 * n, cur, False)
    M.w32(UPATH + 0x28, n + 1, False)
    if stat is not None:
        stat["draws"] = n
    return n + 1


def spiral(M, neg=None, stat=None):
    """sub_0067A140_PathPlanSpiral: x87, table 0x00707800 (512 float32). The code sets the control word's RC to 11 around each FISTP (or 0xC00), so
    the game's product truncates; `neg` "emu" rounds, which is what the p-code FISTP does: it ignores RC. The family compares "emu" with the
    emulator and keeps "trunc" as the reading (ADR-0015 leaves x87 results uncovered; see the family's note)."""
    I = img()
    fx, fy = M.r32(UPATH), M.r32(UPATH + 4)
    lx, ly = fx, fy
    r, ang, k, it = 0, 0, 0, 0
    while True:
        it += 1
        r += 0x2580
        ang += 16
        f = struct.unpack("<f", struct.pack("<f", float(r)))[0]
        cs = I.sine[(ang + 0x80) & 0x1FF]
        sn = I.sine[ang & 0x1FF]
        if neg == "swap":
            cs, sn = sn, cs
        if neg == "emu" or (neg == "swap"):
            a, b = int(round(cs * f)), int(round(sn * f))
        else:
            a, b = int(cs * f), int(sn * f)
        x = (a + fx) & 0xFFFFFFFF
        y = (b + fy) & 0xFFFFFFFF
        if (x >> 16) != (lx >> 16) or (y >> 16) != (ly >> 16):
            M.w16(UPATH + 0x9C + 4 * k, x >> 16, False)
            M.w16(UPATH + 0x9E + 4 * k, y >> 16, False)
            k += 1
            lx, ly = x, y
        if k >= 77:
            break
    M.w32(UPATH + 0x28, k, False)
    if stat is not None:
        stat["iters"] = it
    return k


def h1_model(M, fn, arg, neg=None, stat=None, stop_at_plan=False):
    """The callbacks 0x005C9290 (arg added, range capped at 77 and written back) and 0x005AC040 (range capped at 255, no arg)."""
    I = P1.img()
    r = P2.s16(M.r16(MDATA + 0xE))
    if fn == CB_PLUS:
        if r >= 0x4E and neg != "nocap":
            r = 0x4D
            M.w16(MDATA + 0xE, r, False)
            M.w16(MDATA + 0x10, r, False)
        low = (M.r16(UPATH + 0x10) + (0 if neg == "noarg" else arg)) & 0xFFFFFFFF
    else:
        if r > 0xFF:
            r = 0xFF
        low = M.r16(UPATH + 0x10)
    M.w32(UNIT + 0x20, low, False)
    M.w32(UNIT + 0x24, 0x29A, False)
    R = P1.m_settype(M, UPATH, 10)
    if R[0] != P1.RET:
        raise Assert(R[3][0])
    P1.m_setter(M, 0x00648E70, UPATH, r)
    if stop_at_plan:
        return None
    n = rwalk(M, UNIT + 0x20, neg, stat)
    M.w32(UPATH + 0x34, M.r32(UPATH + 0x34) | 0x20, False)
    return n


PLANNERS = {GREEDY: greedy, NEAR: near, ONEPT: onept, KNOCK: knock, TYPE1: type1, TYPE15: type15, T3: type3, T11: type11, T12: type12}


# -------------------------------------------------------------------------------------------------- the cases
def path_bytes(rnd, f):
    buf = bytearray(rnd.getrandbits(8) for _ in range(0x200))
    for off, (sz, v) in f.items():
        struct.pack_into({1: "<B", 2: "<H", 4: "<I"}[sz], buf, off, v & ((1 << (8 * sz)) - 1))
    return bytes(buf)


def ctx_case(rnd, fn, sx, sy, tx, ty, room, proom, pattern, mask, refresh, limit, b91, speed=0x800, utype=None, param=0, b90=None,
             target=None, ptype=2, posoff=None):
    """One planner case: the context, the path record (random, declared fields set) and the unit."""
    M = P1.Mem()
    px, py = (sx, sy) if posoff is None else (sx + posoff[0], sy + posoff[1])
    fx, fy = rnd.choice((0x8000, 0x8000, rnd.randrange(0x10000))), rnd.choice((0x8000, 0x8000, rnd.randrange(0x10000)))
    f = {0: (4, px << 16 | fx), 4: (4, py << 16 | fy), 0x1C: (4, proom), 0x24: (4, rnd.getrandbits(16)), 0x28: (4, 0), 0x30: (4, UNIT),
         0x34: (4, rnd.choice((0, 0x20, 0x200, 0x800, 0x1900))), 0x3C: (4, ptype), 0x48: (4, pattern), 0x50: (4, mask),
         0x58: (4, target or 0), 0x7C: (4, speed), 0x90: (1, b91 if b90 is None else b90), 0x91: (1, b91), 0x98: (4, param),
         0x65: (1, rnd.randrange(64)), 0x64: (1, rnd.randrange(64))}
    M.w(UPATH, path_bytes(rnd, f))
    M.w32(UNIT, rnd.choice((0, 1)) if utype is None else utype)
    if target:
        pass
    ctx = struct.pack("<HHHHI", sx, sy, tx, ty, room)
    M.w(CTX, ctx)
    M.w8(CTX + 0x14, refresh)
    M.w32(CTX + 0x18, limit)
    M.w(CTX + 0x28, struct.pack("<III", pattern, mask, UPATH))
    return {"fn": fn, "lines": M.lines, "b": M.b, "s": mk(sx, sy), "t": mk(tx, ty), "room": room, "refresh": refresh, "limit": limit,
            "pattern": pattern, "mask": mask}


def add_target(c, rnd, t, x, y, tmode=None):
    """A target unit at (x, y), type t; tmode 'nopath' for a dynamic unit with no path."""
    M = P1.Mem()
    M.b = c["b"]
    M.lines = c["lines"]
    M.w32(TARGET, t)
    if tmode == "nopath":
        M.w32(TARGET + 0x2C, 0)
    else:
        M.w32(TARGET + 0x2C, TPATH)
        if t == 2 or 4 <= t <= 5:
            M.w32(TPATH + 0xC, x)
            M.w32(TPATH + 0x10, y)
        else:
            M.w16(TPATH + 2, x)
            M.w16(TPATH + 6, y)


def real_point(rnd, rooms):
    while True:
        r = rnd.choice(rooms)
        sx, sy = r.x0 + rnd.randrange(r.w), r.y0 + rnd.randrange(r.h)
        if P2.free_of_marks(r, sx, sy):
            return r, sx, sy


def real_target(rnd, sx, sy, spread=(8, 40, 100)):
    while True:
        m = rnd.random()
        d = spread[0] if m < 0.3 else (spread[1] if m < 0.8 else spread[2])
        tx, ty = sx + rnd.randint(-d, d), sy + rnd.randint(-d, d)
        if (tx, ty) != (sx, sy) and tx > 0 and ty > 0:
            return tx, ty


def real_params(rnd):
    return dict(pattern=rnd.choice((0, 1, 1, 1, 2, 2, 3, 4, 5, 5)), mask=rnd.choice(P2.MASKS), refresh=rnd.choice((0, 0, 1, 1, 2, 3)),
                limit=rnd.choice((14, 14, 14, 73, 77, 40, 5, 1, 2, 20)), b91=rnd.choice((14, 14, 73, 77, 40, 5, 39, 20)))


def proom_of(rnd, r, sx, sy, rooms):
    m = rnd.random()
    if m < 0.1 and len(r.near) > 1:
        return rnd.choice(r.near).addr
    if m < 0.2:                                                    # a room whose near list does not hold the start
        return rnd.choice(rooms).addr
    return r.addr


def gen_planner(rnd, rooms, fn, n, params=None, spread=(8, 40, 100), mode=None):
    out = []
    while len(out) < n:
        r, sx, sy = real_point(rnd, rooms)
        tx, ty = real_target(rnd, sx, sy, spread)
        p = real_params(rnd)
        if params:
            p.update(params(rnd))
        speed = rnd.choice((0x800, 0x800, 0x800, 0x400, 0x1000, 0))
        posoff = None if rnd.random() < 0.9 else (rnd.randint(-2, 2), rnd.randint(-2, 2))
        target = TARGET if mode == "target" and rnd.random() < 0.5 else None
        c = ctx_case(rnd, fn, sx, sy, tx, ty, r.addr, proom_of(rnd, r, sx, sy, rooms), p["pattern"], p["mask"], p["refresh"], p["limit"], p["b91"],
                     speed=speed, param=p.get("param", 0), target=target, utype=p.get("utype"), ptype=p.get("ptype", 2))
        if target:
            add_target(c, rnd, rnd.choice((0, 1, 2, 3, 4, 5, 6)), tx, ty)
        out.append(c)
    return out


def carve_room(i, rect, free, tag, fill=1):
    x0, y0, w, h = rect
    cells = [fill] * (w * h)
    for (x, y) in free:
        cells[(y - y0) * w + x - x0] = 0
    return P2.Room(i, rect, cells, tag)


def gen_gbound(rnd, n=30):
    """A corridor carved so that greedy's walk turns at every step; 78 points at limit 77."""
    I = img()
    rooms, cases = [], []
    while len(cases) < n:
        limit = rnd.choice((77, 77, 77, 73, 14, 40))
        s = (200 + rnd.randrange(5), 200 + rnd.randrange(5))
        t = (s[0] + rnd.randint(85, 100), s[1] + rnd.randint(30, 60))
        first = (s[0] + 1, s[1])
        free = {s, first}
        cur = mk(*first)
        prev = 0xFF
        path = []
        ok = True

        def dfs(cur, prev, depth):
            if depth == limit:
                return True
            tr = triple(cur, mk(*t))
            for k in range(3):
                d = tr[k]
                if d == prev or (d - 4) & 7 == prev:
                    continue
                dx, dy = I.step[d]
                nx = (X(cur) + dx, Y(cur) + dy)
                if nx in free:
                    continue
                if any((X(cur) + I.step[tr[j]][0], Y(cur) + I.step[tr[j]][1]) in free for j in range(k)):
                    continue
                free.add(nx)
                if dfs(mk(*nx), d, depth + 1):
                    return True
                free.discard(nx)
            return False
        if not dfs(cur, prev, 0):
            continue
        tag = "G%d" % len(cases)
        r = carve_room(len(rooms), (180, 180, 140, 120), free, tag)
        rooms.append(r)
        P2.link(rooms)
        c = ctx_case(rnd, GREEDY, s[0], s[1], t[0], t[1], r.addr, r.addr, 0, 1, 0, limit, limit)
        M = P1.Mem()
        M.b = c["b"]
        M.lines = c["lines"]
        cases.append(c)
    P2.link(rooms)
    return rooms, cases


def gen_noise(rnd, fn, n, tagp, params=None, dens=(0.05, 0.15, 0.3, 0.42), mode=None, rect=(100, 100, 80, 80)):
    rooms, cases = [], []
    per = 8
    while len(cases) < n:
        if len(cases) % per == 0:
            x0, y0, w, h = rect
            if rnd.random() < 0.5:                     # walls: rectangles a walker goes round
                cells = [0] * (w * h)
                for _ in range(rnd.randint(4, 16)):
                    a, b = rnd.randrange(w), rnd.randrange(h)
                    ww, hh = rnd.choice(((1, rnd.randint(3, 30)), (rnd.randint(3, 30), 1), (rnd.randint(2, 12), rnd.randint(2, 12))))
                    for yy in range(b, min(h, b + hh)):
                        for xx in range(a, min(w, a + ww)):
                            cells[yy * w + xx] = 1
                r = P2.Room(len(rooms), rect, cells, "%s%d" % (tagp, len(rooms)))
            else:
                r = P2.noise_room(rnd, len(rooms), rect, rnd.choice(dens), "%s%d" % (tagp, len(rooms)))
            rooms.append(r)
        r = rooms[-1]
        x0, y0, w, h = rect
        while True:
            sx, sy = x0 + rnd.randrange(2, w - 2), y0 + rnd.randrange(2, h - 2)
            tx, ty = x0 + rnd.randrange(2, w - 2), y0 + rnd.randrange(2, h - 2)
            if (sx, sy) != (tx, ty) and not r.cell(sx, sy):
                break
        p = dict(pattern=0, mask=1, refresh=rnd.choice((0, 1, 2)), limit=rnd.choice((14, 40, 77)), b91=rnd.choice((14, 40, 73, 77, 20, 30)))
        if params:
            p.update(params(rnd))
        target = TARGET if mode == "target" and rnd.random() < 0.3 else None
        c = ctx_case(rnd, fn, sx, sy, tx, ty, r.addr, r.addr, p["pattern"], p["mask"], p["refresh"], p["limit"], p["b91"], target=target)
        if target:
            add_target(c, rnd, 1, tx, ty)
        cases.append(c)
    P2.link(rooms)
    return rooms, cases


def stair_cells(s, steps):
    """E, E, E, S, S, S repeated: the best route is E, diagonal, S, diagonal, ..., so it keeps about two points in three cells.
    `straight`: E only, one kept point."""
    x, y = s
    cells = [(x, y)]
    seq = (0, 0, 0, 1, 1, 1)
    for k in range(steps):
        if seq[k % 6] == 0:
            x += 1
        else:
            y += 1
        cells.append((x, y))
    return cells


def gen_t1stair(rnd):
    rooms, cases = [], []
    plain = [("s", n) for n in list(range(104, 126)) + [4, 8, 20, 40, 60, 80, 150, 198, 199, 200, 201, 260, 300]]
    for kind, steps in plain + [("e", 1), ("e", 2), ("e", 3), ("e", 10), ("e", 50)]:
        s = (150, 150)
        cells = stair_cells(s, steps) if kind == "s" else [(s[0] + k, s[1]) for k in range(steps + 1)]
        tag = "S%s%d" % (kind, steps)
        r = carve_room(len(rooms), (140, 140, 200, 200), cells, tag)
        rooms.append(r)
        t = cells[-1]
        cases.append(ctx_case(rnd, TYPE1, s[0], s[1], t[0], t[1], r.addr, r.addr, 0, 1, 0, 77, 77))
    P2.link(rooms)
    return rooms, cases


def gen_t15stair(rnd):
    """A wall a walker follows, past each limit: the largest point count."""
    rooms, cases = [], []
    for k in range(40):
        s = (150, 150)
        rect = (120, 120, 90, 90)
        x0, y0, w, h = rect
        cells = [0] * (w * h)
        # a comb across the line: teeth the walker goes round
        tx, ty = s[0] + rnd.randint(30, 60), s[1] + rnd.randint(-3, 3)
        nteeth = rnd.randint(1, 8)
        for q in range(nteeth):
            xx = s[0] + 3 + q * rnd.randint(2, 5)
            a, b = rnd.randint(1, 12), rnd.randint(1, 12)
            for yy in range(s[1] - a, s[1] + b):
                if x0 <= xx < x0 + w and y0 <= yy < y0 + h and (xx, yy) != (tx, ty):
                    cells[(yy - y0) * w + xx - x0] = 1
        r = P2.Room(len(rooms), rect, cells, "W%d" % k)
        rooms.append(r)
        b91 = rnd.choice((77, 77, 77, 73, 40, 60))
        cases.append(ctx_case(rnd, TYPE15, s[0], s[1], tx, ty, r.addr, r.addr, 0, 1, 0, 14, b91))
    P2.link(rooms)
    return rooms, cases


def gen_rwalk(rnd, n=300):
    out = []
    while len(out) < n:
        sx, sy = rnd.randrange(1000, 20000), rnd.randrange(1000, 20000)
        tx, ty = sx + rnd.randint(-100, 100), sy + rnd.randint(-100, 100)
        b91 = rnd.choice((0, 1, 2, 3, 14, 40, 41, 73, 76, 77, rnd.randrange(78)))
        f = {0: (4, sx << 16 | 0x8000), 4: (4, sy << 16 | 0x8000), 0x10: (2, tx), 0x12: (2, ty), 0x91: (1, b91)}
        M = P1.Mem()
        M.w(UPATH, path_bytes(rnd, f))
        M.w32(UNIT + 0x20, rnd.getrandbits(32))
        M.w32(UNIT + 0x24, rnd.randrange(1, 0x7FFFFFFF))
        out.append({"fn": RWALK, "lines": M.lines, "b": M.b, "edx": UNIT + 0x20})
    return out


def gen_spiral(rnd, fn=SPIRAL, n=30, tight=0):
    """`tight` cases: fx so that a product with a fraction of at least one half ends at 0xFFFF, where a rounded product would cross."""
    I = img()
    out = []
    while len(out) < n + tight:
        sx, sy = rnd.randrange(1000, 20000), rnd.randrange(1000, 20000)
        fx, fy = rnd.choice((0x8000, rnd.randrange(0x10000))), rnd.choice((0x8000, rnd.randrange(0x10000)))
        if len(out) >= n:
            it = rnd.randrange(1, 40)
            v = I.sine[(16 * it + 0x80) & 0x1FF] * float(it * 0x2580)
            if v <= 0 or v - int(v) < 0.5:
                continue
            fx = (0xFFFF - int(v)) & 0xFFFF
        f = {0: (4, sx << 16 | fx), 4: (4, sy << 16 | fy), 0x10: (2, sx), 0x12: (2, sy), 0x91: (1, rnd.randrange(78))}
        M = P1.Mem()
        M.w(UPATH, path_bytes(rnd, f))
        out.append({"fn": fn, "lines": M.lines, "b": M.b, "edx": UNIT + 0x20})
    return out


def stock_ranges():
    rows = list(csv.reader(open(os.path.join(ROOT, "workspace", "merged", "data", "global", "excel", "missiles.txt"), errors="replace"),
                           delimiter="\t"))
    h = rows[0]
    r, m = h.index("Range"), h.index("Missile")
    out = {}
    for row in rows[1:]:
        if row and row[m] and row[m] != "Expansion" and row[r].strip():
            try:
                out[row[m]] = int(row[r])
            except ValueError:
                pass
    return out


def gen_h1(rnd, n=300, plan=False):
    st = stock_ranges()
    out = []
    while len(out) < n:
        fn = CB_PLUS if rnd.random() < 0.7 else CB_X
        m = rnd.random()
        if m < 0.3:
            rng = st["firestormmaker"]
        elif m < 0.5:
            rng = st["lightunique"]
        elif m < 0.8:
            rng = rnd.choice((0, 1, 2, 19, 20, 21, 40, 41, 76, 77, 78, 79, 98, 255, 256, 300))
        else:
            rng = rnd.randrange(0, 400)
        arg = rnd.randrange(0, 30)
        sx, sy = rnd.randrange(1000, 20000), rnd.randrange(1000, 20000)
        tx, ty = sx + rnd.randint(-100, 100), sy + rnd.randint(-100, 100)
        f = {0: (4, sx << 16 | 0x8000), 4: (4, sy << 16 | 0x8000), 0x10: (2, tx), 0x12: (2, ty), 0x30: (4, UNIT),
             0x34: (4, rnd.choice((0, 0x20, 0x60000, 0x100))), 0x3C: (4, rnd.choice((4, 2))), 0x40: (4, 4), 0x7C: (4, 0x800),
             0x54: (2, 0), 0x91: (1, rnd.randrange(78)), 0x90: (1, rnd.randrange(78))}
        M = P1.Mem()
        M.w(UPATH, path_bytes(rnd, f))
        M.w32(UNIT, 3)
        M.w32(UNIT + 0x14, MDATA)
        M.w32(UNIT + 0x2C, UPATH)
        seed0 = (rnd.getrandbits(32), rnd.randrange(1, 0x7FFFFFFF))
        M.w32(UNIT + 0x20, seed0[0])
        M.w32(UNIT + 0x24, seed0[1])
        M.w16(MDATA + 0xE, rng)
        M.w16(MDATA + 0x10, rnd.randrange(0, 400))
        out.append({"fn": fn, "lines": M.lines, "b": M.b, "arg": arg, "range": rng, "plan": plan})
    return out


FAMILIES = ("probe", "greedy", "g98", "gbound", "near", "knock", "onept", "t1real", "t1syn", "t1stair", "t15real", "t15syn", "t15stair",
            "rwalk", "spiral", "spiralobs", "h1", "h1obs", "client")
CONTROLS = {
    "greedy": ("ctxroom", "order", "noflag", "rev", "dist", "refresh", "limit"),
    "g98": ("param0", "order"),
    "gbound": ("noflag", "limit"),
    "near": ("le325", "noretry", "order", "noflag"),
    "knock": ("k", "floor", "ctxroom"),
    "onept": ("ctxroom",),
    "t1real": ("h", "cost", "list", "offs", "gt0", "nostart", "resort", "pool"),
    "t1syn": ("h", "cost", "list", "offs", "gt0", "pool", "resort"),
    "t1stair": ("max77", "min2"),
    "t15real": ("lim40", "lim18", "min2", "reduce", "wswap", "noswap"),
    "t15syn": ("lim40", "lim18", "min2", "reduce", "wswap", "noswap", "lim50"),
    "t15stair": ("reduce", "wswap", "noswap"),
    "rwalk": ("shr", "n1", "step1", "accum", "noadd"),
    "spiral": ("swap", "trunc"),
    "h1": ("nocap", "noarg", "shr", "n1"),
    "client": ("order",),
}
_CACHE = {}


def family(fam, d):
    if fam in _CACHE:
        return _CACHE[fam]
    rnd = random.Random("r54c-" + fam)
    def real():
        return P2.load_real(d)
    if fam == "probe":
        rooms, cases = [], [{"fn": ONEPT, "lines": [], "b": {}, "ecx": P2.ESP0 - 0x8000, "probe": "read"},
                            {"fn": 0x006829C0, "lines": [], "b": {}, "ecx": 0, "args": (0x12600000, P2.ESP0 - 0x4000, 0x800), "probe": "over"}]
    elif fam == "greedy":
        rooms = real()
        cases = gen_planner(rnd, rooms, GREEDY, 600, params=lambda r: dict(ptype=r.choice((2, 2, 13, 5))))
    elif fam == "g98":
        rooms = real()
        cases = gen_planner(rnd, rooms, GREEDY, 300, params=lambda r: dict(param=r.choice((2, 0xFFFFFFFE, 2, 0xFFFFFFFE, 0xFFFFFFFC, 1)), ptype=r.choice((5, 6))))
    elif fam == "gbound":
        rooms, cases = gen_gbound(rnd)
    elif fam == "near":
        rooms = real()
        cases = gen_planner(rnd, rooms, NEAR, 400, spread=(8, 18, 40), params=lambda r: dict(ptype=7, limit=r.choice((73, 14, 5, 20))), mode="target")
        k = 0
        while k < 80:                                                 # at the switch: dx^2 + dy^2 of 324 and of 325
            r, sx, sy = real_point(rnd, rooms)
            a, b = rnd.choice(((18, 0), (0, 18), (18, 1), (1, 18), (17, 6), (6, 17), (15, 10), (10, 15)))
            tx, ty = sx + rnd.choice((-1, 1)) * a, sy + rnd.choice((-1, 1)) * b
            if tx <= 0 or ty <= 0:
                continue
            cases.append(ctx_case(rnd, NEAR, sx, sy, tx, ty, r.addr, r.addr, r.near and rnd.choice((1, 2, 5)), rnd.choice(P2.MASKS), rnd.choice((0, 1)), 2, 73, ptype=7))
            k += 1
    elif fam == "knock":
        rooms = real()
        cases = gen_planner(rnd, rooms, KNOCK, 300, spread=(8, 12, 40), params=lambda r: dict(ptype=8), mode="target")
        for c in cases:
            pass
    elif fam == "onept":
        rooms = real()
        cases = gen_planner(rnd, rooms, ONEPT, 200, params=lambda r: dict(ptype=r.choice((9, 9, 9, 9, 9, 4)), utype=r.choice((0, 1, 1, 1, 3))))
    elif fam == "t1real":
        rooms = real()
        cases = gen_planner(rnd, rooms, TYPE1, 400, spread=(8, 18, 40), mode="target")
    elif fam == "t1syn":
        rooms, cases = gen_noise(rnd, TYPE1, 240, "N", mode="target")
    elif fam == "t1stair":
        rooms, cases = gen_t1stair(rnd)
    elif fam == "t15real":
        rooms = real()
        cases = gen_planner(rnd, rooms, TYPE15, 400, spread=(8, 30, 70), mode="target")
    elif fam == "t15syn":
        rooms, cases = gen_noise(rnd, TYPE15, 300, "W", mode="target", params=lambda r: dict(b91=r.choice((14, 40, 73, 77, 77, 30, 85, 90))))
    elif fam == "t15stair":
        rooms, cases = gen_t15stair(rnd)
    elif fam == "rwalk":
        rooms, cases = [], gen_rwalk(rnd)
    elif fam == "spiral":
        rooms, cases = [], gen_spiral(rnd, tight=60)
    elif fam == "spiralobs":
        rooms, cases = [], gen_spiral(rnd)
    elif fam == "h1":
        rooms, cases = [], gen_h1(rnd)
    elif fam == "h1obs":
        rooms, cases = [], gen_h1(rnd, n=100, plan=True)
    else:
        rooms = real()
        cases = []
        for fn, n in ((T3, 60), (T11, 60), (T12, 60)):
            cases += gen_planner(rnd, rooms, fn, n, params=lambda r: dict(limit=r.choice((14, 5, 20, 38)), ptype={T3: 3, T11: 11, T12: 12}[fn]))
    _CACHE[fam] = (rooms, cases)
    return rooms, cases


def case_lines(c):
    L = list(c["lines"])
    if c.get("probe") == "read":
        L.append("d %08x 4" % UPATH)
        L.append("call %08x %08x 00000000" % (c["fn"], c["ecx"]))
        return L
    if c.get("probe") == "over":
        L.append("s 12600000 %d" % c["args"][2])
        L.append("d %08x 4" % 0x12600000)
        L.append("call %08x 00000000 00000000 %08x %08x %08x" % (c["fn"], c["args"][0], c["args"][1], c["args"][2]))
        return L
    L.append("d %08x %d" % (UPATH, 0x200))
    fn = c["fn"]
    if fn in (RWALK, SPIRAL):
        L.append("d %08x 8" % (UNIT + 0x20))
        L.append("call %08x %08x %08x" % (fn, UPATH, c["edx"]))
    elif fn in (CB_PLUS, CB_X):
        L.append("d %08x 8" % (UNIT + 0x20))
        L.append("d %08x 4" % (MDATA + 0xE))
        L.append("call %08x %08x %08x" % (fn, UNIT, c["arg"]))
    else:
        L.append("d %08x 8" % CTX)
        L.append("call %08x %08x 00000000" % (fn, CTX))
    return L


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        rooms, cases = family(fam, d)
        obs = [ASSERT]
        if fam == "spiralobs":
            obs.append(SINCOS)
        if fam == "h1obs":
            obs.append(PATHPLAN)
        with open(os.path.join(d, fam + ".mem"), "w") as f:
            f.write("\n".join(P2.base_spec(rooms, tuple(obs))) + "\n")
        with open(os.path.join(d, fam + ".cases"), "w") as f:
            for c in cases:
                f.write("\n".join(case_lines(c)) + "\n")
        print("CASES %s %d rooms=%d" % (fam, len(cases), len(rooms)))


# -------------------------------------------------------------------------------------------------------- the check
def read_out(path):
    calls, traced = [], []
    for ln in open(path):
        p = ln.split()
        if not p:
            continue
        if p[0] == "C":
            c = {"n": int(p[1]), "dumps": {}, "u": [], "ux": 0}
            if p[3] == "STOP":
                c["stop"] = " ".join(p[4:])
            elif p[3] == "OBS":
                c["obs"] = int(p[4], 16)
                c["regs"] = {k: int(v, 16) for k, v in (x.split("=") for x in p[5:])}
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
        elif p[0] == "UX":
            calls[-1]["ux"] = int(p[1])
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


def fresh(case):
    M = P1.Mem()
    M.b = dict(case["b"])
    return M


def predict(case, R, neg=None):
    """(kind, value, M, stat). kind 'ret' with eax, or 'assert' with the line."""
    M = fresh(case)
    fn = case["fn"]
    stat = {}
    try:
        if fn == RWALK:
            return "ret", rwalk(M, case["edx"], neg, stat), M, stat
        if fn == SPIRAL:
            return "ret", spiral(M, neg or "emu", stat), M, stat
        if fn in (CB_PLUS, CB_X):
            if case.get("plan"):
                h1_model(M, fn, case["arg"], neg, stat, True)
                return "plan", None, M, stat
            return "ret", h1_model(M, fn, case["arg"], neg, stat), M, stat
        c = C(case, R, M, neg)
        v = PLANNERS[fn](c)
        c.stat["ret"] = v
        return "ret", v, M, c.stat
    except Assert as e:
        return "assert", e.line, M, stat


def compare(c, case, kind, val, M):
    if kind == "assert":
        if c.get("obs") != ASSERT or "args" not in c:
            return False
        ret, a1 = struct.unpack_from("<II", c["args"], 0)
        site = SITES.get(val)
        return a1 == val and (site is None or ret == site)
    if "eax" not in c or c.get("pop") != 0:
        return False
    if kind == "ret":
        if case["fn"] in (CB_PLUS, CB_X):
            pass
        elif c["eax"] != val:
            return False
    if c["dumps"].get(UPATH) != M.snap(UPATH, 0x200):
        return False
    if case["fn"] in (RWALK, SPIRAL, CB_PLUS, CB_X):
        if case["fn"] != SPIRAL and c["dumps"].get(UNIT + 0x20) != M.snap(UNIT + 0x20, 8):
            return False
        if case["fn"] in (CB_PLUS, CB_X) and c["dumps"].get(MDATA + 0xE) != M.snap(MDATA + 0xE, 4):
            return False
    elif c["dumps"].get(CTX) != struct.pack("<HHHH", X(case["s"]), Y(case["s"]), X(case["t"]), Y(case["t"])):
        return False
    return True


def outcome(fam, case, kind, val, st):
    if kind == "assert":
        return "assert:%x" % val
    if fam in ("rwalk", "h1"):
        return "draws:%d" % st.get("draws", 0)
    if fam == "spiral":
        return "points:%d" % val
    if fam in ("t1real", "t1syn", "t1stair"):
        return "%s%s%s" % ("found" if st.get("found") else "best", ":full" if st.get("full") else "", ":0" if not val else "")
    if fam in ("t15real", "t15syn", "t15stair"):
        k = "refused" if st.get("line", 0) <= 2 else ("follow" if st.get("follows") else "clear")
        if st.get("spliced"):
            k += ":splice"
        if st.get("trunc"):
            k += ":trunc"
        if st.get("looped"):
            k += ":loop"
        return k + (":0" if not val else "")
    if fam == "near":
        return ("t1:" if st.get("t1") else "greedy:") + ("0" if not val else "n")
    return "0" if not val else ("1" if val == 1 else "n")


def check_probe(d):
    """The kept negative checks: an injected unaccounted read must fail its case, and more U lines than the cap must show."""
    calls, traced = read_out(os.path.join(d, "probe.out"))
    res = []
    r = calls[0]
    bad_u = [u for u in r["u"] if (u[0], u[2], u[3]) not in U_OK]
    res.append("PROBE read: a planner entered with ECX below the stack's written bytes: U lines=%d unaccounted=%d first=%s case_fails=%s" % (
        len(r["u"]), len(bad_u), ("pc=%08x size=%d unwritten=%d" % (bad_u[0][0], bad_u[0][2], bad_u[0][3])) if bad_u else "-", "yes" if bad_u else "NO"))
    o = calls[1]
    bad_u2 = [u for u in o["u"] if (u[0], u[2], u[3]) not in U_OK]
    res.append("PROBE overflow: memcpy over unwritten stack: U lines=%d overflow marker UX=%d case_fails=%s" % (
        len(o["u"]), o["ux"], "yes" if (o["ux"] and bad_u2) else "NO"))
    tight = (0x006831D7, 4, 3) not in U_OK and (0x006831D7, 2, 2) not in U_OK
    res.append("PROBE tightened: the same pc with another size or count is not accounted: %s" % ("yes" if tight else "NO"))
    return res, bool(bad_u and o["ux"] and bad_u2 and tight)


def check_family(fam, d):
    rooms, cases = family(fam, d)
    R = {r.addr: r for r in rooms}
    calls, traced = read_out(os.path.join(d, fam + ".out"))
    bad, match, stops = [], 0, 0
    tags, accu = {}, {}
    ctl = {n: [0, 0] for n in CONTROLS.get(fam, ())}
    stat = {"maxret": 0, "steps": 0, "maxnodes": 0, "maxstack": 0, "maxwalk": 0, "maxn": 0, "maxline": 0, "ovl": 0, "draws": 0, "maxiters": 0, "dirhi": 0}
    if len(calls) != len(cases):
        bad.append("case count %d != %d" % (len(calls), len(cases)))
    distinct = set()
    for c, case in zip(calls, cases):
        for pc, addr, size, un in c["u"]:
            k = U_OK.get((pc, size, un))
            if k is None and (pc, size, un) in U_T15 and predict(case, R)[3].get("overread"):
                k = "term"
            if k is None:
                bad.append("case %d scratch read pc=%08x addr=%08x size=%d unwritten=%d" % (c["n"], pc, addr, size, un))
            else:
                accu[k] = accu.get(k, 0) + 1
        if c["ux"]:
            bad.append("case %d more U lines than the cap: %d" % (c["n"], c["ux"]))
        if "stop" in c:
            stops += 1
            bad.append("case %d STOP %s" % (c["n"], c["stop"]))
            continue
        if fam == "spiralobs":
            ok = c.get("obs") == SINCOS and struct.unpack_from("<II", c["args"], 0) == (0x0067A196, 16)
            match += ok
            tags["sincos"] = tags.get("sincos", 0) + 1
            if not ok:
                bad.append("case %d spiralobs %s" % (c["n"], c.get("args", b"")[:8].hex()))
            continue
        kind, val, M, st = predict(case, R)
        if fam == "h1obs":
            ok = c.get("obs") == PATHPLAN and c["dumps"].get(UNIT + 0x20) == M.snap(UNIT + 0x20, 8) and c["dumps"].get(UPATH) == M.snap(UPATH, 0x200)
            if ok:
                ret, a1, a2, a3 = struct.unpack_from("<IIII", c["args"], 0)
                ok = (a1, a2, a3) == (UPATH, UNIT, 0) and ret == (0x005C92EE if case["fn"] == CB_PLUS else 0x005AC090)
            match += ok
            tags["plan"] = tags.get("plan", 0) + 1
            if not ok:
                bad.append("case %d h1obs obs=%s" % (c["n"], hex(c.get("obs", 0))))
            continue
        ok = compare(c, case, kind, val, M)
        match += ok
        stat["steps"] += c.get("steps", 0)
        o = outcome(fam, case, kind, val, st)
        tags[o] = tags.get(o, 0) + 1
        distinct.add((kind, val, M.snap(UPATH + 0x9C, 4 * min(val or 0, 90)) if kind == "ret" and val else b""))
        if kind == "ret" and val:
            stat["maxret"] = max(stat["maxret"], val)
        for k, s in (("maxnodes", "nodes"), ("maxstack", "maxstack"), ("maxwalk", "walk"), ("maxn", "maxn"), ("maxline", "line"), ("maxiters", "iters")):
            stat[k] = max(stat[k], st.get(s, 0))
        stat["ovl"] += st.get("ovl", 0)
        stat["draws"] += st.get("draws", 0)
        if not ok:
            bad.append("case %d mismatch fn=%x want %s %s got eax=%s obs=%s stop=%s" % (
                c["n"], case["fn"], kind, val, c.get("eax"), hex(c.get("obs", 0)), c.get("stop")))
        for n in ctl:
            try:
                k2, v2, M2, s2 = predict(case, R, n)
            except Exception as e:                                    # a control that runs off its own model separates
                ctl[n][0] += 1
                continue
            same = (k2, v2) == (kind, val) and M2.snap(UPATH, 0x200) == M.snap(UPATH, 0x200) and M2.snap(UNIT + 0x20, 8) == M.snap(UNIT + 0x20, 8) \
                and M2.snap(MDATA + 0xE, 4) == M.snap(MDATA + 0xE, 4)
            if not same:
                ctl[n][0] += 1
                ctl[n][1] += compare(c, case, k2, v2, M2)
    acc, rest = {}, []
    for t in traced:
        p = t.split()
        k = table_of(int(p[2], 16)) if p[0] == "R" else None
        if k:
            acc[k] = acc.get(k, 0) + int(p[4])
        else:
            rest.append(t)
    line = "PATH54C %s cases=%d match=%d bad=%d stopped=%d traced=%d distinct=%d accounted=%s scratch=%s %s %s" % (
        fam, len(cases), match, len(bad), stops, len(rest), len(distinct), ",".join("%s:%d" % kv for kv in sorted(acc.items())) or "-",
        ",".join("%s:%d" % kv for kv in sorted(accu.items())) or "-", " ".join("%s=%d" % kv for kv in stat.items()),
        " ".join("%s_separating=%d %s_passed=%d" % (n, ctl[n][0], n, ctl[n][1]) for n in ctl))
    return line, bad[:25], rest[:25], tags, ctl


def cmd_check(d, only=None):
    allok = True
    tot = [0, 0]
    res, ok = check_probe(d)
    for r in res:
        print(r)
    allok &= ok
    for fam in FAMILIES:
        if fam == "probe" or (only and fam not in only):
            continue
        if not os.path.exists(os.path.join(d, fam + ".out")):
            print("PATH54C %s MISSING" % fam)
            allok = False
            continue
        line, bad, traced, tags, ctl = check_family(fam, d)
        print(line)
        print("  OUTCOMES " + " ".join("%s:%d" % kv for kv in sorted(tags.items())))
        for b in bad:
            print("  BAD", b)
        for t in traced:
            print("  TRACED", t)
        if bad or traced or any(ctl[n][1] for n in ctl) or any(ctl[n][0] == 0 for n in ctl):
            allok = False
        tot[0] += int(line.split("cases=")[1].split()[0])
        tot[1] += int(line.split("match=")[1].split()[0])
    print("PATH54C total cases=%d match=%d" % tuple(tot))
    print("PATH54C result=%s" % ("ok" if allok else "FAIL"))


def cmd_stock():
    st = stock_ranges()
    print("# Range, the callback 0x005C9290's cap at 77, PathSetByte90's cap at 77, the random walk's +0x91 >> 1")
    for name in ("firestormmaker", "firestorm", "lightunique"):
        r = st.get(name)
        print("STOCK %s Range=%s cap=%d draws=%d points=%d" % (name, r, min(r, 77), min(r, 77) >> 1, (min(r, 77) >> 1) + 1))
    rows = list(csv.reader(open(os.path.join(ROOT, "workspace", "merged", "data", "global", "excel", "missiles.txt"), errors="replace"), delimiter="\t"))
    h = rows[0]
    idc, r_, m_, lr = h.index("*ID") if "*ID" in h else h.index("Id"), h.index("Range"), h.index("Missile"), h.index("LevRange")
    for row in rows[1:]:
        if len(row) > r_ and row[idc] == "408":
            print("STOCK class-408 %s Range=%s LevRange=%s draws_at_level0=%d" % (row[m_], row[r_], row[lr], min(int(row[r_]), 77) >> 1))
        if len(row) > r_ and row[idc] in ("195", "458"):
            print("STOCK class-%s %s Range=%s LevRange=%s" % (row[idc], row[m_], row[r_], row[lr]))


def lcg(s, n):
    lo, hi = s
    for _ in range(n):
        v = lo * A + hi
        lo, hi = v & 0xFFFFFFFF, v >> 32 & 0xFFFFFFFF
    return lo, hi


def cmd_h1log(paths):
    """Game logs, not the emulator: at MCB0 the seed is the Init's and md.rng the row's range; at MCB1 the seed and md.rng are the callback's exit.
    The 0x005AC040 creations have no logger line: from the parameter block's +0x54, the seed at MC1 against Init(path x10)."""
    import json
    tally = {}
    bad = 0
    n = 0
    for path in paths:
        cb0 = None
        mc0 = {}
        cls = {}
        for ln in open(path, errors="replace"):
            t, _, rest = ln.partition(" ")
            if t == "MC0":
                d = json.loads(rest)
                mc0[d.get("n")] = d.get("p")
            elif t == "SU0":
                cls[json.loads(rest)["u"]] = json.loads(rest).get("c")
            elif t == "MCB0":
                cb0 = json.loads(rest)
            elif t == "MCB1" and cb0 is not None:
                d = json.loads(rest)
                n += 1
                lo, hi = (cb0["x10"] + cb0["arg"]) & 0xFFFFFFFF, 0x29A   # the Init at 0x005C92D1 (the s of MCB0 is the entry's)
                rng = cb0["md"]["rng"]
                r2 = 77 if rng >= 78 else rng
                k = (r2 & 0xFF if (r2 & 0xFF) < 77 else 77) >> 1
                want = "%08x:%08x" % lcg((lo, hi), k)
                ok = want == d["s"] and d["md"]["rng"] == r2 and d["md"]["rem"] == (77 if rng >= 78 else cb0["md"]["rem"]) and hi == 0x29A
                ok = ok and lo == (cb0["x10"] + cb0["arg"]) & 0xFFFFFFFF
                key = ("0x005C9290", cls.get(cb0["m"]), rng, r2, k)
                tally.setdefault(key, [0, 0])
                tally[key][0] += 1
                tally[key][1] += ok
                bad += not ok
                cb0 = None
            elif t == "MC1":
                d = json.loads(rest)
                p = mc0.get(d.get("k"))
                if p and struct.unpack_from("<I", bytes.fromhex(p), 0x54)[0] == CB_X:
                    m = d["m"]
                    if "path" not in m or m["path"].get("x10") is None:
                        continue
                    n += 1
                    rng = m["md"]["rng"]
                    r = min(rng, 255)
                    k = (r if r < 77 else 77) >> 1
                    want = "%08x:%08x" % lcg((m["path"]["x10"], 0x29A), k)
                    ok = want == m["s"]
                    key = ("0x005AC040", m.get("c"), rng, r, k)
                    tally.setdefault(key, [0, 0])
                    tally[key][0] += 1
                    tally[key][1] += ok
                    bad += not ok
    for key in sorted(tally, key=str):
        print("H1LOG cb=%s class=%s range=%s after_cap=%s draws=%s creations=%d match=%d" % (key + tuple(tally[key])))
    print("H1LOG logs=%d creations=%d mismatches=%d" % (len(paths), n, bad))


def cmd_bounds():
    I = img()
    print("# Point counts against the record's 78 slots (+0x9C .. +0x1D3); the record ends at +0x1FF (last index 88)")
    print("BOUND slots=78 index_of_+0x1D4=%d index_past_record=%d" % ((0x1D4 - 0x9C) // 4, (0x200 - 0x9C) // 4))
    for lim in (14, 73, 77, 78, 255):
        print("BOUND greedy limit=%d most_points=limit+1=%d fits=%s" % (lim, lim + 1, lim + 1 <= 78))
    for lim in (14, 77, 78):
        print("BOUND walk98 limit=%d most_points=limit=%d fits=%s" % (lim, lim, lim <= 78))
    for lim in (38, 39, 40, 44, 45, 77):
        print("BOUND type12 limit=%d most_points=2*limit=%d fits78=%s inrecord=%s" % (lim, 2 * lim, 2 * lim <= 78, 2 * lim <= 89))
    for b in (14, 73, 77, 78, 154, 155, 156, 157, 255):
        print("BOUND rwalk +0x91=%d draws=%d points=%d fits=%s" % (b, b >> 1, (b >> 1) + 1, (b >> 1) + 1 <= 78))
    M = P1.Mem()
    M.w(UPATH, bytes(0x200))
    M.w32(UPATH, 5000 << 16 | 0x8000)
    M.w32(UPATH + 4, 5000 << 16 | 0x8000)
    st = {}
    n = spiral(M, None, st)
    print("BOUND spiral points=%d iterations=%d radius_last=%d radius_wraps_at_iter=%d" % (n, st["iters"], st["iters"] * 0x2580, (1 << 31) // 0x2580 + 1))
    print("BOUND type1 pool=200 stored_at_most=78 kept=1..77 stack_slots=%d" % ((0x32E8 - 0x2FC8) // 4))
    print("BOUND type15 line_slots=%d line_points_at_lim77=76 terminator_index=76 first_lim_past_the_array=78 walker_list_dwords=%d" % ((0x160 - 0x2C) // 4, (0x322 + 2) // 4))
    print("BOUND near greedy_u16 window: |dx|,|dy|<=18 for dsq<=324; 18*18=324 dx=18,dy=0; (18,1)=325 refused")
    print("BOUND dirs g_DirOctant values=%d distinct=%s" % (len(I.dirs), sorted(set(I.dirs))))
    print("BOUND sine table entries=512 max|err|=%.3e" % max(abs(I.sine[k] - math.sin(2 * math.pi * k / 512)) for k in range(512)))


def text_range(data):
    return path_scan.text_range(data) if hasattr(path_scan, "text_range") else None


def cmd_scan3c(exe):
    """Every instruction of .text that stores to [reg+0x3C], immediate or register, from objdump's linear sweep, and a raw scan of the
    C7 /0 encodings for 3, 0xB, 0xC; a store's owner is the nearest int3-padded start. The path module is 0x00647000..0x00680000."""
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x401000", "--stop-address=0x6cb5a1", exe],
                         capture_output=True, text=True).stdout
    import re
    pat = re.compile(r"^\s*([0-9a-f]+):\s+(mov|add|or|and|sub|xor|inc|dec)\s+(DWORD PTR )?\[([a-z]{3})\+0x3c\],(\S+)")
    imm, regs, n = {}, [], 0
    rows = []
    for ln in out.splitlines():
        m = pat.match(ln)
        if not m:
            continue
        n += 1
        a = int(m.group(1), 16)
        v = m.group(5)
        rows.append((a, m.group(2), m.group(4), v))
    data = open(exe, "rb").read()
    print("SCAN3C stores=%d (mov/add/or/and/sub/xor to [reg+0x3c] with a dword or register source, objdump linear sweep of .text)" % n)
    ops = {}
    for a, op, base, v in rows:
        k = "imm" if v.startswith("0x") or v.isdigit() else "reg"
        ops[(op, k)] = ops.get((op, k), 0) + 1
    print("SCAN3C by_op " + " ".join("%s/%s:%d" % (o, k, c) for (o, k), c in sorted(ops.items())))
    vals = {}
    for a, op, base, v in rows:
        if op == "mov" and (v.startswith("0x") or v.isdigit()):
            vv = int(v, 16)
            vals[vv] = vals.get(vv, 0) + 1
    print("SCAN3C mov_imm_values " + " ".join("%#x:%d" % kv for kv in sorted(vals.items())))
    hits = [(a, op, base, v) for a, op, base, v in rows if op == "mov" and (v.startswith("0x") or v.isdigit()) and int(v, 16) in (3, 0xB, 0xC)]
    for h in hits:
        print("SCAN3C IMM3BC %08x mov [%s+0x3c],%s" % (h[0], h[2], h[3]))
    # raw: mov dword [r+0x3c], imm32 (C7 4x 3C imm32, mod 01, r/m != 4) and the SIB form C7 44 24 3C (esp); disp32 too
    tb = path_scan.va_bytes(data, 0x401000, 0x2CA5A1)
    raw = []
    for v in (3, 0xB, 0xC):
        for modrm in range(0x40, 0x48):
            if modrm == 0x44:
                continue
            pat8 = bytes([0xC7, modrm, 0x3C]) + struct.pack("<I", v)
            at = tb.find(pat8)
            while at >= 0:
                raw.append((0x401000 + at, v, "disp8"))
                at = tb.find(pat8, at + 1)
        for modrm in range(0x80, 0x88):
            if modrm == 0x84:
                continue
            pat32 = bytes([0xC7, modrm, 0x3C, 0, 0, 0]) + struct.pack("<I", v)
            at = tb.find(pat32)
            while at >= 0:
                raw.append((0x401000 + at, v, "disp32"))
                at = tb.find(pat32, at + 1)
    print("SCAN3C raw_c7 hits=%d" % len(raw))
    for r in sorted(raw):
        print("SCAN3C RAW %08x imm=%#x %s" % r)
    # byte and word stores, for the width's sake
    small = re.findall(r"^\s*([0-9a-f]+):\s+mov\s+(?:BYTE|WORD) PTR \[[a-z]{3}\+0x3c\],\S+", out, re.M)
    print("SCAN3C byte_or_word_stores=%d (a dword type is not set by one)" % len(small))
    # each register store: the register's last definition and the base's, walking back to the function start (int3 or ret)
    ins = []
    for ln in out.splitlines():
        m = re.match(r"^\s*([0-9a-f]+):\s+(.*)$", ln)
        if m:
            ins.append((int(m.group(1), 16), re.sub(r"\s+", " ", m.group(2)).strip()))
    at = {a: i for i, (a, _) in enumerate(ins)}
    alias = {"eax": "(eax|ax|al)", "ebx": "(ebx|bx|bl)", "ecx": "(ecx|cx|cl)", "edx": "(edx|dx|dl)", "esi": "(esi|si)", "edi": "(edi|di)", "ebp": "(ebp|bp)", "esp": "esp"}

    def last_def(i, r):
        pat = re.compile(r"^(mov|movzx|movsx|lea|xor|add|sub|imul|or|and|pop|shr|shl|sar|neg|inc|dec|sbb|cdq|mul|idiv|setg|setl|sete|setne)\b ?%s\b(,|$)" % alias.get(r, r))
        j = i - 1
        while j >= 0 and i - j < 200:
            t = ins[j][1]
            if t.startswith("int3") or t.startswith("ret"):
                return None
            if t.startswith("call") and r in ("eax", "ecx", "edx"):
                return ins[j]
            if pat.match(t):
                return ins[j]
            j -= 1
        return None
    kinds = {}
    bases = {}
    pathish, immdefs = [], []
    lines = []
    for a, op, base, v in rows:
        if op != "mov" or v.startswith("0x") or v.isdigit():
            continue
        i = at[a]
        d = last_def(i, v)
        b = last_def(i, base)
        dt = d[1] if d else "?"
        bt = b[1] if b else "?"
        kind = "call" if dt.startswith("call") else ("imm" if re.match(r"^mov \w+,0x[0-9a-f]+$", dt) else ("zero" if dt.startswith("xor") else ("mem" if "[" in dt and dt.startswith("mov") else "other")))
        kinds[kind] = kinds.get(kind, 0) + 1
        if kind == "imm":
            immdefs.append(int(dt.split(",")[1], 16))
        inpath = 0x00647F00 <= a < 0x00651000 or 0x00678B80 <= a < 0x0067C480
        isp = "+0x2c]" in bt or inpath
        side = "server" if a >= 0x00500000 else "client"
        bk = "unit_path" if "+0x2c]" in bt else ("path_module" if inpath else ("unresolved" if bt == "?" else "other"))
        bases[(side, bk)] = bases.get((side, bk), 0) + 1
        lines.append("SCAN3C REG %08x %s [%s+0x3c],%s def=%s base=%s%s" % (a, side, base, v, dt, bt, " PATHISH" if isp else ""))
        if isp:
            pathish.append(a)
    print("SCAN3C reg_store_def_kinds " + " ".join("%s:%d" % kv for kv in sorted(kinds.items())))
    print("SCAN3C reg_store_imm_values " + " ".join("%#x" % v for v in sorted(immdefs)))
    print("SCAN3C reg_store_base_from_unit_path_or_in_path_module=%d" % len(pathish))
    print("SCAN3C reg_store_bases " + " ".join("%s/%s:%d" % (k[0], k[1], c) for k, c in sorted(bases.items())))
    print("\n".join(lines))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["grids", "cases", "check", "bounds", "stock", "scan3c", "h1log", "manifest"])
    ap.add_argument("rest", nargs="*")
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "grids":
        os.makedirs(a.dir, exist_ok=True)
        P2.cmd_grids(a.dir)
    elif a.cmd == "cases":
        cmd_cases(a.dir)
    elif a.cmd == "check":
        cmd_check(a.dir, a.rest or None)
    elif a.cmd == "bounds":
        cmd_bounds()
    elif a.cmd == "stock":
        cmd_stock()
    elif a.cmd == "h1log":
        cmd_h1log(a.rest)
    elif a.cmd == "scan3c":
        cmd_scan3c(a.rest[0])
    else:
        P2.cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    main(sys.argv[1:])

#!/usr/bin/env python3
"""The figures of the lane/s54 review (plan 0054 Phase 3) on the kept logs of run:2026-11-04-path and run:2026-11-04-path-2. Reads; changes nothing.

    python3 -I tools/path_spec_review.py logs LOGDIR > logs.txt        the worked example, draw by draw, against its log lines; every watched break function by
                                                                       side, zeros printed; plans outside the register; the probe's plans by type; type 15's zeros
    python3 -I tools/path_spec_review.py literal > literal.txt         docs/specs/path/search.md's T15* and type 1 pseudocode, run as written, against
                                                                       tools/path_emu3.py on random grids, with the outcome mix and controls that must differ

No rule and no tag comes from `literal`: it tests the spec's text against the kept model. The model's own evidence is run:2026-11-03-path-emu-3.
"""
import base64
import collections
import glob
import json
import os
import random
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import path_emu3 as E3  # noqa: E402

A = 0x6AC690C5
EXAMPLE = ("2026-11-04-path-2-s1-6004-k5-sor-oasis.log", 1633)
WATCHED = {0x00679E50: "type 3", 0x00679FD0: "type 11", 0x00679E60: "type 12", 0x00663E00: "type-16 A", 0x00663ED0: "type-16 B", 0x00679C80: "control: greedy"}
RUN1, RUN2 = "2026-11-04-path-s1-*.log", "2026-11-04-path-2-s1-*.log"


def lines_of(path):
    with open(path, errors="replace") as f:
        for n, line in enumerate(f, 1):
            tag, _, rest = line.partition(" ")
            if tag in ("PLN", "PLX", "BRK", "PLC") and rest.startswith("{"):
                try:
                    yield n, tag, json.loads(rest)
                except ValueError:
                    pass


def worked_example(d):
    log, at = EXAMPLE
    rows = {n: (tag, o) for n, tag, o in lines_of(os.path.join(d, log)) if n in (at, at + 1)}
    pln, plx = rows[at][1], rows[at + 1][1]
    rec = zlib.decompress(base64.b64decode(pln["rec"]))
    u = pln["u"]
    lim = rec[0x91]
    x, y = u[4], u[5]
    tx, ty = plx["t"]
    lo, hi = (int(v, 16) for v in pln["s0"].split(":"))
    print("WORKED EXAMPLE %s lines %d, %d" % (log, at, at + 1))
    print("  entry: unit type %d class %d, position (%d, %d), target (%d, %d), +0x91 %d, flags 0x%X, seed %08x:%08x" % (u[0], u[1], x, y, tx, ty, lim, pln["fl"], lo, hi))
    I = E3.img()
    d0 = E3.triple(E3.mk(x, y), E3.mk(tx, ty))[0]
    add = [-1, 0, 1] * 10 + [-1, 1]
    n = lim >> 1
    print("  draws %d, first direction %d" % (n, d0))
    pts = []
    for k in range(n):
        v = A * lo + hi
        lo, hi = v & 0xFFFFFFFF, v >> 32
        dr = (d0 + add[lo & 31]) & 7
        pts.append(E3.mk(x, y))
        if k < 5:
            print("  draw %d low %08x low&31 %d add %+d direction %d point written (%d, %d)" % (k + 1, lo, lo & 31, add[lo & 31], dr, x, y))
        dx, dy = I.step[dr]
        x, y = (x + 2 * dx) & 0xFFFF, (y + 2 * dy) & 0xFFFF
    pts.append(E3.mk(x, y))
    print("  computed: return %d, last point (%d, %d), seed %08x:%08x" % (n + 1, x, y, lo, hi))
    print("  logged:   return %d, last point (%d, %d), seed %s" % (plx["eax"], plx["pts"][-1] & 0xFFFF, plx["pts"][-1] >> 16, plx["s"]))
    print("  all points equal: %s; seed equal: %s" % (pts == plx["pts"], "%08x:%08x" % (lo, hi) == plx["s"]))


def watched(d):
    print("WATCHED BREAK FUNCTIONS (BRK lines and the last counter `c`, by side; zeros printed; path.py's report prints only functions with a hit)")
    for name, pat in (("run:2026-11-04-path", RUN1), ("run:2026-11-04-path-2", RUN2)):
        logs = sorted(glob.glob(os.path.join(d, pat)))
        count, top, armed = collections.Counter(), collections.Counter(), 0
        for p in logs:
            last = {}
            with open(p, errors="replace") as f:
                text = f.read()
            armed += "PATH logger armed" in text
            for line in text.splitlines():
                if line.startswith("BRK {"):
                    o = json.loads(line[4:])
                    key = (o["fn"], o["side"])
                    count[key] += 1
                    last[key] = max(last.get(key, 0), o.get("c", 0))
            for k, v in last.items():
                top[k] += v
        print("  %s: %d logs, armed line in %d" % (name, len(logs), armed))
        for fn, label in sorted(WATCHED.items()):
            sides = sorted(s for (f, s) in count if f == fn)
            if not sides:
                print("    %08x %-16s no BRK line on any side" % (fn, label))
            for s in sides:
                print("    %08x %-16s side=%s lines=%d hits=%d" % (fn, label, s, count[(fn, s)], top[(fn, s)]))


def plans(d):
    import path as P
    reg = P.load_register()
    print("REGISTER, THE PROBE'S PLANS, TYPE 15's ZEROS")
    allg = {}
    for name, pat in (("run:2026-11-04-path", RUN1), ("run:2026-11-04-path-2", RUN2)):
        logs = sorted(glob.glob(os.path.join(d, pat)))
        games = []
        for p in logs:
            games += P.parse(p)
        allg[name] = games
        pl = [x for g in games for x in g.plans]
        no = sum(1 for x in pl if x.pln["ra"] not in reg)
        print("  %s: plans %d, return address outside the register's sites %d" % (name, len(pl), no))
        reached = [x for x in pl if x.ty == 15 and x.plc is not None]
        zero = sum(1 for x in reached if x.plx and x.plx["eax"] == 0)
        allz = sum(1 for x in pl if x.ty == 15 and x.plx and x.plx["eax"] == 0)
        print("    type 15: plans %d, reached the planner %d, return 0 among those %d; return 0 over all plans %d" % (
            sum(1 for x in pl if x.ty == 15), len(reached), zero, allz))
        after = collections.Counter()
        seen = {}
        for g in games:
            s = os.path.basename(g.log)
            for x in g.plans:
                if x.pln.get("probe") and s not in seen:
                    seen[s] = x.k
                if s in seen:
                    after[x.ty] += 1
        print("    plans from a probe's first write on: %d, by session %s, by type %s" % (sum(after.values()), sorted(seen), sorted(after.items())))
        print("    stock plans: %d" % (len(pl) - sum(after.values())))
        replans, stock = 0, 0
        for g in games:
            first = seen.get(os.path.basename(g.log))
            for x in g.plans:
                if x.pln["ra"] in (0x006503CE, 0x006503E2):
                    replans += 1
                    stock += first is None or x.k < first
        print("    replans (return address 0x006503CE or 0x006503E2): %d, stock %d" % (replans, stock))


# ---------------------------------------------------------------------------------- search.md § H and § G, as written
def lit_line(a, b, lim):
    ax, ay, bx, by = E3.X(a), E3.Y(a), E3.X(b), E3.Y(b)
    dx, dy = bx - ax, by - ay
    px, py = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    dx, dy = abs(dx), abs(dy)
    xmajor = dy == 0 or (dx != 0 and dx >= dy)
    axis = (1 if px > 0 else 3) if xmajor else (2 if py > 0 else 0)
    major = dx if xmajor else dy
    minor = dy if xmajor else dx
    out = []
    if major == 0 or major > lim - 1:
        return out, axis
    x, y, err = ax, ay, 0
    for _ in range(major):
        if xmajor:
            x += px
        else:
            y += py
        err += minor
        if err >= major:
            err -= major
            if xmajor:
                y += py
            else:
                x += px
        out.append(E3.mk(x, y))
    return out, axis


class Wk:
    pass


def lit_walker(d, cur, turn, nxt):
    w = Wk()
    w.dir, w.Turn, w.Next, w.pos, w.cnt, w.list, w.mark, w.stop, w.next = d, turn, nxt, cur, 0, [], 0, 0, 0
    return w


def lit_wstep(w, blocked):
    I = E3.img()
    for t in range(4):
        if t:
            w.dir = I.d32(w.Turn + 4 * w.dir)
        dx, dy = I.d32(0x006F1D98 + 8 * w.dir), I.d32(0x006F1D9C + 8 * w.dir)
        w.next = E3.mk(E3.X(w.pos) + dx, E3.Y(w.pos) + dy)
        if not blocked(E3.X(w.next), E3.Y(w.next)):
            return 1
    return 0


def lit_follow(ctx, L, cur, st, lim4, axis, blocked):
    X, Y = E3.X, E3.Y
    I = E3.img()
    p = L[st[0]]
    q = I.d32(0x006F1E28 + 4 * (3 * (Y(p) - Y(cur)) + (X(p) - X(cur))))
    w0 = lit_walker(q + 1, cur, 0x006F1EC0, 0x006F1F00)
    w1 = lit_walker(q + 7, cur, 0x006F1E40, 0x006F1E80)
    a, b = w0, w1
    while True:
        if a.stop == 0 and not lit_wstep(a, blocked):
            a.stop = 1
        if a.stop == 0:
            v = None
            if a.cnt >= 1:
                v = {0: Y(cur) - Y(a.next), 1: X(a.next) - X(cur), 2: Y(a.next) - Y(cur), 3: X(cur) - X(a.next)}[axis]
            if v is not None and v > 0 and st[0] + v - 1 < st[1] and L[st[0] + v - 1] == a.next:
                a.list.append(a.next)
                a.cnt += 1
                i, n = st
                idx = i + v - 1
                d = i - idx - 1 + a.cnt
                new = idx + d
                moved = L[idx + 1:n]
                L[new + 1:new + 1 + len(moved)] = moved
                L[i:i + a.cnt] = a.list
                st[1] = n + d
                st[0] = new + 1
                ctx["mix"]["splice"] += 1
                return a.cnt
            if b.cnt > 1:
                if a.mark != 0:
                    if a.next == b.list[a.mark - 2]:
                        st[1] = st[0]
                        ctx["mix"]["loop"] += 1
                        return 0
                    a.mark = 0
                if a.next == b.pos:
                    a.mark = b.cnt
            a.list.append(a.next)
            a.cnt += 1
            a.pos = a.next
            a.dir = I.d32(a.Next + 4 * a.dir)
            if (lim4 - st[1]) - 1 <= a.cnt:
                a.stop = 1
        if a.mark == 0:
            a, b = b, a
        if w0.stop or w1.stop:
            break
    if lim4 > 80:
        st[1] = st[0]
        return 0

    def d2(p, q):
        return (X(p) - X(q)) ** 2 + (Y(p) - Y(q)) ** 2

    def last(w):
        return w.list[w.cnt - 1] if w.cnt else w.stop
    d0, d1, dq = d2(last(w0), ctx["t"]), d2(last(w1), ctx["t"]), d2(ctx["s"], ctx["t"])
    w, chosen = (w0, d0) if d0 < d1 else (w1, d1)
    if dq < chosen:
        return 0
    L[st[0]:st[0] + w.cnt] = w.list
    st[0] += w.cnt
    st[1] = st[0]
    ctx["mix"]["truncate"] += 1
    return a.cnt


def lit_reduce(start, L, n, neg=None):
    X, Y = E3.X, E3.Y
    if n == 0:
        return []
    if n == 1:
        return [L[0]]
    lx, ly = X(L[0]) - X(start), Y(L[0]) - Y(start)
    out, run = [], 0
    for j in range(n - 1):
        dx, dy = X(L[j + 1]) - X(L[j]), Y(L[j + 1]) - Y(L[j])
        kink = (lx != dx or ly != dy) if neg == "or" else (lx != dx and ly != dy)
        if dx == lx and dy == ly:
            run += 1
            lx = dx
        elif run < 1 and kink:
            run = 1
            lx = -2
        else:
            out.append(L[j])
            run = 0
            lx = dx
        ly = dy
    out.append(L[n - 1])
    return out


def lit_type15(ctx, blocked, neg=None):
    lim = ctx["b91"]
    if ctx["u58"] and lim < 40:
        lim = 40
    L, axis = lit_line(ctx["s"], ctx["t"], lim)
    n = len(L)
    if n <= 2:
        ctx["mix"]["refused at 2"] += 1
        return []
    L = L + [0] * 400
    st = [0, n]
    cur = ctx["s"]
    while True:
        i = st[0]
        if blocked(E3.X(L[i]), E3.Y(L[i])):
            ctx["mix"]["follow"] += 1
            r = lit_follow(ctx, L, cur, st, lim - i, axis, blocked)
            if r == 0:
                return lit_reduce(ctx["s"], L, st[0], neg)
        i = st[0]
        cur = L[i]
        st[0] = i + 1
        if st[0] >= st[1]:
            break
    return lit_reduce(ctx["s"], L, st[1], neg) if st[1] else []


class T1N:
    __slots__ = ("pt", "g", "h", "f", "parent", "links")

    def __init__(self, pt, g, h, parent):
        self.pt, self.g, self.h, self.f, self.parent, self.links = pt, g, h, (g + h) & 0xFFFF, parent, []


def s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def lit_octile(a, b):
    dx, dy = abs(E3.X(a) - E3.X(b)), abs(E3.Y(a) - E3.Y(b))
    return 2 * max(dx, dy) + min(dx, dy)


def lit_cost(a, b):
    return 2 if E3.X(a) == E3.X(b) or E3.Y(a) == E3.Y(b) else 3


def lit_type1(ctx, blocked, neg=None):
    X, Y = E3.X, E3.Y
    s, t = ctx["s"], ctx["t"]
    if ctx["u58"]:
        if all(blocked(X(t) + a, Y(t) + b) for a, b in ((-2, -2), (-2, 2), (2, -2), (2, 2), (-2, 0), (0, -2), (2, 0), (0, 2))):
            ctx["mix"]["no start"] += 1
            return []
    root = T1N(s, 0, lit_octile(s, t), None)
    count, opn, closed, best = 1, [root], {}, None
    done = False
    while opn and not done:
        n = opn.pop(0)
        closed[n.pt] = n
        if best is None or s16(n.h) < s16(best.h) or (n.h == best.h and s16(n.g) > s16(best.g) + 5):
            best = n
        if n.h == 0:
            ctx["mix"]["reached"] += 1
            break
        for a, b in ((-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (0, -1), (1, 0), (0, 1)):
            p = E3.mk(X(n.pt) + a, Y(n.pt) + b)
            if blocked(X(p), Y(p)):
                continue
            g = (n.g + lit_cost(n.pt, p)) & 0xFFFF
            o = next((q for q in opn if q.pt == p), None)
            if o is not None:
                if len(n.links) < 8:
                    n.links.append(o)
                if s16(g) < s16(o.g):
                    o.parent, o.g, o.f = n, g, (g + o.h) & 0xFFFF
                continue
            o = closed.get(p)
            if o is not None:
                if len(n.links) < 8:
                    n.links.append(o)
                if s16(g) < s16(o.g):
                    o.parent, o.g, o.f = n, g, (g + o.h) & 0xFFFF
                    stack = [o]
                    while stack:
                        u = stack.pop()
                        for v in u.links:
                            gg = (u.g + lit_cost(u.pt, v.pt)) & 0xFFFF
                            if s16(gg) < s16(v.g):
                                v.parent, v.g, v.f = u, gg, (gg + v.h) & 0xFFFF
                                stack.append(v)
                continue
            if count >= 200:
                ctx["mix"]["pool"] += 1
                done = True
                break
            count += 1
            o = T1N(p, g, lit_octile(p, t), n)
            k = 0
            older = neg == "older"
            while k < len(opn) and (s16(opn[k].f) <= s16(o.f) if older else s16(opn[k].f) < s16(o.f)):
                k += 1
            opn.insert(k, o)
            n.links.append(o)
    buf, prev, m = [], (-2, -2), best
    while m is not None and len(buf) < 78:
        if m.parent is not None:
            step = (X(m.pt) - X(m.parent.pt), Y(m.pt) - Y(m.parent.pt))
            if step != prev:
                buf.append(m.pt)
                prev = step
        m = m.parent
    if not 1 <= len(buf) <= 77:
        return []
    return buf[::-1]


class Fake(E3.C):
    def __init__(self, s, t, blocked, b91, u58):
        self.s, self.t, self.room, self.refresh, self.limit, self.pattern, self.mask = s, t, 1, 0, 77, 0, 1
        self.neg, self.b, self.pts = None, blocked, {}
        self.vals = {0x91: b91, 0x58: u58, 0x30: 1}
        self.stat = collections.defaultdict(int)

    def path(self, off, n=4):
        return self.vals.get(off, 0)

    def test(self, x, y):
        return self.b(x & 0xFFFF, y & 0xFFFF)

    def setpt(self, i, p):
        self.pts[i] = p

    def unit_ok(self, line):
        pass


def literal():
    rnd = random.Random("lane/s54 review")
    print("LITERAL: search.md §§ G and H run as written, against tools/path_emu3.py type1 and type15, on random grids (cell blocked at a density; outside a 120 x 120 room blocked)")
    for name, model, lit, controls in (("type 15", E3.type15, lit_type15, ("or",)), ("type 1", E3.type1, lit_type1, ("older",))):
        total, bad, ctl_diff = 0, 0, collections.Counter()
        mix, rets = collections.Counter(), collections.Counter()
        for case in range(6000):
            dens = rnd.choice((0.02, 0.08, 0.15, 0.25, 0.35, 0.45))
            cells = {}

            def blocked(x, y, cells=cells, dens=dens, seed=case):
                if not (1000 <= x < 1120 and 1000 <= y < 1120):
                    return 1
                k = (x, y)
                if k not in cells:
                    cells[k] = rnd.random() < dens
                return cells[k]
            s = E3.mk(rnd.randrange(1030, 1090), rnd.randrange(1030, 1090))
            reach = rnd.choice((3, 8, 18, 35, 70))
            t = E3.mk(min(1119, max(1000, E3.X(s) + rnd.randint(-reach, reach))), min(1119, max(1000, E3.Y(s) + rnd.randint(-reach, reach))))
            b91, u58 = rnd.choice((14, 40, 73, 77)), rnd.choice((0, 1))
            f = Fake(s, t, blocked, b91, u58)
            n = model(f)
            want = [f.pts[i] for i in range(n)]
            ctx = {"s": s, "t": t, "b91": b91, "u58": u58, "mix": mix}
            got = lit(ctx, blocked)
            total += 1
            rets["0" if not n else "1" if n == 1 else "2-5" if n < 6 else "6-20" if n < 21 else "21+"] += 1
            if got != want:
                bad += 1
            for c in controls:
                if lit(dict(ctx, mix=collections.Counter()), blocked, c) != want:
                    ctl_diff[c] += 1
        print("  %s: cases %d, differ from the model %d; returns %s; literal's outcomes %s; controls that must differ: %s" % (
            name, total, bad, sorted(rets.items()), sorted(mix.items()), sorted(ctl_diff.items())))
    print("  T15Reduce on a list from the start (0, 0):")
    for label, steps in (("E, SE, E, SE, E", [(1, 0), (1, 1), (1, 0), (1, 1), (1, 0)]), ("E, S, E, S, E", [(1, 0), (0, 1), (1, 0), (0, 1), (1, 0)])):
        x, y, L = 100, 100, []
        for dx, dy in steps:
            x, y = x + dx, y + dy
            L.append(E3.mk(x, y))
        out = lit_reduce(E3.mk(100, 100), L, len(L))
        print("    %-16s %d points in, %d out: %s" % (label, len(L), len(out), [(E3.X(p) - 100, E3.Y(p) - 100) for p in out]))


def main(argv):
    if argv[:1] == ["logs"] and len(argv) == 2:
        worked_example(argv[1])
        watched(argv[1])
        plans(argv[1])
    elif argv[:1] == ["literal"]:
        literal()
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

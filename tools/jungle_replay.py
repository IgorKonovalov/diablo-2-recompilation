"""Plan 0026 Phase 1 reading check (Act III): replay the jungle link layout 0x00677880 / 0x00678910 on the
act seed, then the Act III outdoor window OD0 -> OD1 (0x0067F450) for the logged levels 76-83, and compare:
the level rectangle, the OD1 seed, and the preset placement list (def, rect, file index) that OutdoorRoomsCreate
logs (PIC / PIO) after OD1.

Usage: python3 -I tools/jungle_replay.py <excel-dir> <exe> <log>... [--seed N]

Evidence: docs/findings/drlg/0008-outdoor.md § 13. Acts I, II, IV and V: tools/outdoor_replay.py.
"""
import csv, json, struct, sys

M32 = 0xFFFFFFFF
from collections import Counter
COV = Counter()


def exe_read(path, va, n):
    data = open(path, "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    base = struct.unpack_from("<I", data, pe + 24 + 28)[0]
    sec = pe + 24 + opt
    rva = va - base
    for i in range(nsec):
        vsize, vaddr, rawsize, raw = struct.unpack_from("<IIII", data, sec + 40 * i + 8)
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            return data[raw + rva - vaddr: raw + rva - vaddr + n]
    raise ValueError(hex(va))


class Seed:
    def __init__(s, lo, hi=666):
        s.lo, s.hi = lo & M32, hi & M32
        s.n = 0

    def step(s):
        v = s.lo * 0x6AC690C5 + s.hi
        s.lo, s.hi = v & M32, (v >> 32) & M32
        s.n += 1
        return s.lo

    def range(s, n):  # RNG_Range / RangeB and the inline copies: n < 1 -> 0, no draw
        if n < 1:
            return 0
        lo = s.step()
        return lo & (n - 1) if n & (n - 1) == 0 else lo % n


def tdiv(a, b):  # C signed division
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def tsv(path):
    rows = list(csv.reader(open(path, encoding="latin1"), delimiter="\t"))
    return rows[0], rows[1:]


EXCEL, EXE = sys.argv[1].rstrip("/") + "/", sys.argv[2]
h, rows = tsv(EXCEL + "levels.txt")
LV = {}
for r in rows:
    if len(r) > 5 and r[h.index("Id")].strip().isdigit():
        g = lambda c: int(r[h.index(c)])
        LV[g("Id")] = dict(sx=[g("SizeX"), g("SizeX(N)"), g("SizeX(H)")], sy=[g("SizeY"), g("SizeY(N)"), g("SizeY(H)")],
                         ox=g("OffsetX"), oy=g("OffsetY"))
h, rows = tsv(EXCEL + "lvlprest.txt")
PREST = {}
for r in rows:
    if len(r) > 10 and r[h.index("Def")].strip().isdigit():
        PREST[int(r[h.index("Def")])] = dict(files=int(r[h.index("Files")]), sx=int(r[h.index("SizeX")]),
                                             sy=int(r[h.index("SizeY")]))


def ints(va, n):
    return list(struct.unpack("<%di" % n, exe_read(EXE, va, 4 * n)))


T_CLR = ints(0x006F13BC, 16)           # clearing cell (exit mask >> 4) -> Def
T_SIDE = ints(0x006F13F0, 4 * 16)      # [def or mask][side 0x10,0x20,0x40,0x80] -> Def
PERM = ints(0x006F2328, 18)            # clearing file indices, 6 rows of 3
CLR_OFF = ints(0x006F2240, 0x54)       # per level id: clearing family offset


def side_lookup(v, side):
    if 0 <= v < 16:
        return T_SIDE[4 * v + side]
    raise RuntimeError("side lookup with Def %d (outside the 16-row table)" % v)


# ---------------------------------------------------------------- 0x006777D0
def rel_rect(P, w, h, d):
    dx = dy = 0
    if d == 0:
        dy = -h
    elif d in (1, 2):
        dy = tdiv(-h, 3)  # (hi(h*0x55555555) - h) >> 1, sign-corrected
        dx = -w if d == 1 else w
    elif d in (3, 4):
        dy = tdiv(-2 * h, 3)
        dx = -w if d == 3 else w
    return dict(x=P["x"] + dx, y=P["y"] + dy, w=w, h=h, dir=d, kids=[], parent=P)


def gap_overlap(A, B):  # RectGapTest(A, B, 0) == 0
    gx = (B["x"] - A["w"] - A["x"]) if A["x"] < B["x"] else (A["x"] - B["w"] - B["x"])
    gy = (B["y"] - A["h"] - A["y"]) if A["y"] < B["y"] else (A["y"] - B["h"] - B["y"])
    return gx < 0 and gy < 0


# ---------------------------------------------------------------- 0x00677880
def jungle_layout(act, diff=0):
    town = dict(x=LV[75]["ox"], y=LV[75]["oy"])
    W, H = LV[76]["sx"][diff], LV[76]["sy"][diff]
    nx, ny = tdiv(W, 32), tdiv(H, 32)
    recs = [dict(x=town["x"], y=town["y"] - H, w=W, h=H, dir=0, kids=[], parent=None)]
    minx, miny, maxx, maxy = town["x"], town["y"] - H, town["x"] + W, town["y"]
    while len(recs) < 3:
        k = act.range(len(recs))
        d = act.step() % 5
        R = rel_rect(recs[k], W, H, d)
        if any(gap_overlap(A, R) for A in recs):
            continue
        recs[k]["kids"].append(R)
        if len(recs[k]["kids"]) > 3:
            raise RuntimeError("fatal 0x63e")
        minx, miny, maxx = min(minx, R["x"]), min(miny, R["y"]), max(maxx, R["x"] + R["w"])
        recs.append(R)
    if (maxx - minx) % 32 or (maxy - miny) % 32:
        raise RuntimeError("fatal 0x64d/0x64e")
    gh, gw = tdiv(maxy - miny, 32) + 2, tdiv(maxx - minx, 32) + 2
    restarts = 0
    while True:  # LAB_00677b80
        owner = [0] * (gw * gh); order = [0] * (gw * gh); marks = [0] * (gw * gh); res = [0] * (gw * gh)
        for k, R in enumerate(recs):
            cx0, cy0 = tdiv(R["x"] - minx, 32) + 1, tdiv(R["y"] - miny, 32) + 1
            R["cx0"], R["cy0"] = cx0, cy0
            s = act.step() & 1 if k == 0 else (1 if R["dir"] % 2 == 1 else 0)
            bottom = cy0 + ny - 1
            while True:
                for j in range(ny):
                    for i in range(nx):
                        c = (cy0 + j) * gw + cx0 + i
                        owner[c] = k + 1; order[c] = 0; marks[c] = 0; res[c] = 0
                col = s + cx0
                if k != 0:
                    marks[gw * bottom + col] = 1
                    marks[gw * bottom + col + (1 if s == 0 else -1)] = 2
                for K in R["kids"]:
                    cd = K["dir"]
                    if cd == 0: marks[cy0 * gw + cx0] = 1
                    elif cd == 1: marks[(cy0 + 3) * gw + cx0] = 1
                    elif cd == 2: marks[(cy0 + 3) * gw + cx0 + 1] = 1
                    elif cd == 3: marks[(cy0 + 1) * gw + cx0] = 1
                    elif cd == 4: marks[(cy0 + 1) * gw + cx0 + 1] = 1
                cnt2 = 1 if k != 0 else 0
                run = 0
                row = bottom
                num = (k + 1) * 100
                while cy0 <= row:
                    order[row * gw + col] = num; num += 1
                    up = True
                    if not (run == 0 or row == cy0):
                        r = act.step() % 3
                        if r == 0:
                            up = False
                            run = 0
                            if s == 0: col += 1; s = 1
                            else: col -= 1; s = 0
                    if up:
                        run += 1
                        o = row * gw + col + (1 if s == 0 else -1)
                        if run > 1 and row > 1 and marks[o] == 0:
                            cnt2 += 1; marks[o] = 2
                        row -= 1
                if cnt2 >= 2:
                    break
                COV["path retry"] += 1
            while cnt2 > 3:
                j2 = act.range(cnt2); COV["mark2 trim"] += 1
                n2 = 0; done = False
                for j in range(ny):
                    if done: break
                    for i in range(nx):
                        if done: break
                        c = (cy0 + j) * gw + cx0 + i
                        if marks[c] == 2:
                            if n2 == j2:
                                marks[c] = 0; done = True; cnt2 -= 1
                            n2 += 1
        # phase 3: exit masks
        for row in range(gh):
            for col in range(gw):
                c = row * gw + col
                ow = owner[c]; m = 0; best = 0x7FFFFFFF
                if marks[c] == 1:
                    U, D, Rr, Lf = c - gw, c + gw, c + 1, c - 1
                    if order[U] and order[U] < best and owner[U] == ow: m = 8; best = order[U]
                    if order[D] and order[D] < best and owner[D] == ow: m = 4; best = order[D]
                    if order[Rr] and order[Rr] < best and owner[Rr] == ow: m = 2; best = order[Rr]
                    if order[Lf] and order[Lf] < best and owner[Lf] == ow: m = 1
                    if m & 8: res[U] |= 4
                    if m & 4: res[D] |= 8
                    if m & 2: res[Rr] |= 1
                    if m & 1: res[Lf] |= 2
                    if marks[U] == 1 and owner[U] != ow: m |= 8
                    if marks[D] == 1 and owner[D] != ow: m |= 4
                    if marks[Rr] == 1 and owner[Rr] != ow: m |= 2
                    if marks[Lf] == 1 and owner[Lf] != ow: m |= 1
                o = order[c]
                if o:
                    if abs(o - order[c - gw]) == 1: m |= 8
                    if abs(o - order[c + gw]) == 1: m |= 4
                    if abs(o - order[c + 1]) == 1: m |= 2
                    if abs(o - order[c - 1]) == 1: m |= 1
                res[c] |= m
        # phase 4: clearings
        restart = False
        for row in range(gh):
            if restart: break
            for col in range(gw):
                c = row * gw + col
                v = res[c]; ow = owner[c]
                r = act.step() & 3
                zero = v == 0
                if marks[c] == 2:
                    nb = [c - gw, c + gw, c + 1, c - 1]; bit = [0x80, 0x40, 0x20, 0x10]
                    for i in range(4):
                        q = (i + r) & 3; n = nb[q]
                        if owner[n] == ow and res[n] != 0 and res[n] < 15:
                            v |= bit[q]; break
                    if v == 0:
                        restart = True; break
                    if zero:
                        found = False
                        for i in range(4):
                            q = (i + r) & 3; n = nb[q]
                            if owner[n] != ow and marks[n] == 2:
                                v |= bit[q]; found = True; COV["clearing 2nd loop link"] += 1; break
                        third = (act.step() & 1) and not found
                        r = act.step() & 3
                        COV["clearing zero-v cells"] += 1
                        if third:
                            COV["clearing 3rd loop"] += 1
                            for i in range(4):
                                q = (i + r) & 3; n = nb[q]
                                if res[n] != 0 and res[n] < 15 and not (v & bit[q]):
                                    v |= bit[q]; break
                    if v & 0x80: res[c - gw] |= 0x40
                    if v & 0x40: res[c + gw] |= 0x80
                    if v & 0x20: res[c + 1] |= 0x10
                    if v & 0x10: res[c - 1] |= 0x20
                    marks[c] = 0
                res[c] |= v
        if restart:
            COV["restart"] += 1
            restarts += 1
            continue
        break
    # phase 5: Defs
    for c in range(gw * gh):
        v = res[c]; low = v & 15
        if low == 0:
            d = T_CLR[v >> 4] if v >= 16 else 0
            if v >= 16 and d == 0: raise RuntimeError("fatal 0x799")
        elif v < 16:
            d = low + 0x211
        else:
            d = low
            for b, side in ((0x10, 0), (0x20, 1), (0x40, 2), (0x80, 3)):
                if v & b: d = side_lookup(d, side); COV["side bits"] += 1
            if d == 0: raise RuntimeError("fatal 0x78c")
        res[c] = d
    for R in recs:
        R["defs"] = [res[(R["cy0"] + j) * gw + i + R["cx0"]] for j in range(ny) for i in range(nx)]
        R["clr"] = sum(1 for d in R["defs"] if d > 0x23E)
    recs.sort(key=lambda R: -R["y"])  # bubble sort, descending y, stable
    out = {}
    for i, R in enumerate(recs):
        out[76 + i] = R
    # 0x00678910: 79..83 stacked north of 78
    P = out[78]; acc = 0
    for lid in range(79, 84):
        w, hh = LV[lid]["sx"][diff], LV[lid]["sy"][diff]
        acc -= hh
        out[lid] = dict(x=tdiv(P["w"], 2) - tdiv(w, 2) + P["x"], y=P["y"] + acc, w=w, h=hh)
    return out, restarts


# ---------------------------------------------------------------- the outdoor window, Act III
class Out:
    def __init__(o, lid, rect, seed, bit474, jung=None):
        o.lid, o.rect, o.seed, o.bit = lid, rect, seed, bit474
        o.cw, o.ch = tdiv(rect["w"], 8), tdiv(rect["h"], 8)
        o.cell = [[0] * o.cw for _ in range(o.ch)]
        o.defg = [[0] * o.cw for _ in range(o.ch)]
        o.rot = {}
        o.jung = jung

    def rotation(o, d):
        if d not in o.rot:
            n = PREST[d]["files"]
            o.rot[d] = [n, o.seed.range(n)]
        r = o.rot[d]
        r[1] = (r[1] + 1) % r[0]   # signed idiv in the binary; values are non-negative here
        return r[1]

    def place(o, x, y, d, idx):   # 0x006743C0 (flag 0)
        if idx == -1:
            idx = o.rotation(d)
        P = PREST[d]
        for yy in range(y, y + tdiv(P["sy"], 8)):
            for xx in range(x, x + tdiv(P["sx"], 8)):
                o.cell[yy][xx] = (o.cell[yy][xx] & ~0xF0000) | (idx << 16) | 0x200
                o.defg[yy][xx] = 0
        o.defg[y][x] = d

    def fits(o, x, y, d):  # 0x00674230, pad 0
        P = PREST[d]
        for yy in range(y, y + tdiv(P["sy"], 8)):
            for xx in range(x, x + tdiv(P["sx"], 8)):
                if not (0 <= xx < o.cw and 0 <= yy < o.ch): return False
                if o.cell[yy][xx] & 0x1B81: return False
        return True

    def shuffle(o, w, h):
        n = w * h
        a = [(i % w, i // w) for i in range(n)]
        for _ in range(n):
            u = o.seed.range(n); v = o.seed.range(n)
            a[u], a[v] = a[v], a[u]
        return a

    def place_random(o, d, idx):  # 0x00674730, pad 0, flags 15 (interior cells)
        a = o.shuffle(o.cw - 2, o.ch - 2)
        for (x, y) in a:
            if o.fits(x + 1, y + 1, d):
                o.place(x + 1, y + 1, d, idx); return 1
        return 0

    def fill(o, lo, hi, maxn):  # 0x0067EED0
        a = o.shuffle(o.cw, o.ch)
        n = 0
        for (x, y) in a:
            d = lo + o.seed.range(hi - lo + 1)
            if o.fits(x, y, d):
                o.place(x, y, d, -1); n += 1
                if maxn > 0 and n >= maxn: return

    def run(o):
        lid = o.lid
        if 76 <= lid <= 78:   # 0x0067E910
            J = o.jung; defs = J["defs"]; nx = tdiv(LV[76]["sx"][0], 32); ny = tdiv(LV[76]["sy"][0], 32)
            r = o.seed.range(6 if J["clr"] == 3 else 2)
            e = 0; kk = 0
            for j in range(ny):
                if lid == 76 and j == ny - 1:
                    o.place(0, j * 4, 0x23D, 1 if defs[ny * nx - 1] == 0 else 0, ); e += 2
                elif lid == 78 and j == 0:
                    o.place(0, 0, 0x23E, 1 if defs[1] == 0 else 0); e += 2
                else:
                    for i in range(nx):
                        d = defs[e]; e += 1; idx = -1
                        if d > 0x23E:
                            if kk > 2: raise RuntimeError("fatal 0x47")
                            d += CLR_OFF[lid]; idx = PERM[kk + r * 3]; kk += 1
                        if d:
                            o.place(i * 4, j * 4, d, idx)
        cw, ch = o.cw, o.ch
        if lid in (79, 80, 81):
            S, N_, E_, W_, NE, NW, SE, SW = {79: (606, 605, 607, 608, 609, 610, 611, 612),
                                             80: (620, 619, 621, 622, 623, 624, 625, 626),
                                             81: (637, 636, 638, 639, 640, 641, 642, 643)}[lid]
            mid = tdiv(cw - 1, 2)
            if lid == 79:
                gate = 1 if o.bit else cw - 2
                for x in range(1, cw - 1): o.place(x, 0, N_ + 8 * (x == gate), -1)
                x = 1
                while x < cw - 1:
                    o.place(x, ch - 1, S + 8 * (x == mid), -1); x += 1 + (x == mid)
            elif lid == 80:
                sg, ng = (1, cw - 2) if o.bit else (cw - 2, 1)
                for x in range(1, cw - 1):
                    o.place(x, 0, N_ + 8 * (x == ng), -1)
                    o.place(x, ch - 1, S + 8 * (x == sg), -1)
            else:
                sg = cw - 2 if o.bit else 1
                x = 1
                while x < cw - 1:
                    o.place(x, 0, N_ + 8 * (x == mid), -1); x += 1 + (x == mid)
                for x in range(1, cw - 1): o.place(x, ch - 1, S + 8 * (x == sg), -1)
            for y in range(1, ch - 1):
                o.place(cw - 1, y, E_, -1); o.place(0, y, W_, -1)
            o.place(0, 0, NW, -1); o.place(cw - 1, 0, NE, -1); o.place(0, ch - 1, SW, -1); o.place(cw - 1, ch - 1, SE, -1)
            if lid == 79:
                o.place_random(0x277, 0)
                o.fill(0x26A, 0x26A, 4); o.fill(0x268, 0x269, 0); o.fill(0x267, 0x267, 0)
            elif lid == 80:
                o.place(3, 3, 0x275, 0); o.place(cw - 4, 3, 0x275, 1)
                o.place_random(0x276, 0); o.place_random(0x276, 1); o.place_random(0x277, 0)
                o.fill(0x27B, 0x27B, 4); o.fill(0x279, 0x27A, 0); o.fill(0x278, 0x278, 0)
            else:
                o.place(3, ch - 4, 0x286, 0); o.place(cw - 4, ch - 4, 0x286, 1)
                o.place_random(0x287, 0); o.place_random(0x287, 1); o.place_random(0x277, 0)
                o.fill(0x28B, 0x28B, 4); o.fill(0x289, 0x28A, 0); o.fill(0x288, 0x288, 0)
        elif lid == 82:
            o.place(0, 0, 0x28C, 0)
        elif lid == 83:
            for (x, y, d) in ((0, 0, 0x28D), (2, 0, 0x28E), (6, 0, 0x28F), (0, 4, 0x290), (2, 4, 0x291), (6, 4, 0x292)):
                o.place(x, y, d, -1)

    def anchors(o):
        out = []
        for cy in range(o.ch):
            for cx in range(o.cw):
                c = o.cell[cy][cx]
                if c & 0x200 and o.defg[cy][cx]:
                    out.append((o.defg[cy][cx], o.rect["x"] + 8 * cx, o.rect["y"] + 8 * cy, (c >> 16) & 0xF))
        return out


def parse_seed(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def main():
    logs = [a for a in sys.argv[3:] if not a.startswith("--")]
    extra = [int(a.split("=")[1]) for a in sys.argv[3:] if a.startswith("--seed=")]
    for ms in extra:
        act = Seed(ms); act.step(); act.step()
        n0 = act.n
        J, rs = jungle_layout(act)
        print("seed %d: jungle layout act-seed steps %d (restarts %d)" % (ms, act.n - n0, rs))
    bad = tot = 0
    for path in logs:
        head = open(path).readline()
        ms = int(head.split("seed=")[1].split()[0])
        act = Seed(ms); base = act.step(); act.step(); bit = act.lo & 1
        n0 = act.n
        J, rs = jungle_layout(act)
        print("%s: map seed %d, act base %d, bit474 %d, jungle steps %d, restarts %d" % (path.split('/')[-1], ms, base, bit, act.n - n0, rs))
        ev = [(l.split(" ", 1)[0], json.loads(l.split(" ", 1)[1])) for l in open(path) if l[:4] in ("LC0 ", "OD0 ", "OD1 ", "PIC ", "PIO ", "LI1 ")]
        for i, (t, d) in enumerate(ev):
            if t == "LC0" and d["id"] == 75 and d["base"] != base:
                print("  act base mismatch", d["base"]); bad += 1
            if t != "OD0" or not (76 <= d["id"] <= 83): continue
            lid, lvp = d["id"], d["level"]
            o = Out(lid, J[lid], Seed(*parse_seed(d["seed"])), bit, J.get(lid))
            o.run()
            od1 = [e for e in ev[i:] if e[0] == "OD1" and e[1]["level"] == lvp][0][1]
            got = "%08x:%08x" % (o.seed.lo, o.seed.hi)
            # logged placements: PIC/PIO pairs after OD1 until LI1 of this level
            pl = []; j = [k for k in range(i, len(ev)) if ev[k][0] == "OD1" and ev[k][1]["level"] == lvp][0] + 1
            cur = None
            while j < len(ev) and not (ev[j][0] == "LI1" and ev[j][1]["level"] == lvp):
                t2, d2 = ev[j]
                if t2 == "PIC" and d2["level"] == lvp: cur = [d2["def"], d2["rect"][0], d2["rect"][1]]
                elif t2 == "PIO" and cur is not None: pl.append(tuple(cur + [d2["idx"]])); cur = None
                j += 1
            exp = o.anchors()
            ok = got == od1["seed"] and exp == pl
            tot += 1; bad += not ok
            print("  level %d rect %s: OD1 %s %s, presets %d/%d %s" % (lid, (J[lid]["x"], J[lid]["y"]), got, "ok" if got == od1["seed"] else "!= " + od1["seed"],
                                                               len(exp), len(pl), "ok" if exp == pl else "MISMATCH"))
            if exp != pl:
                for a, b in zip(exp, pl):
                    print("    ", a, b, "" if a == b else "<--")
    print("windows %d, mismatches %d" % (tot, bad)); print(dict(COV))


main()

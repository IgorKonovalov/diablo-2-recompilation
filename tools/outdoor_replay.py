"""Plan 0026 Phase 1 reading check : replay the outdoor window OD0 -> OD1 (sub_00675360_OutdoorLevelBuild's
act generator, up to sub_006750F0_OutdoorRoomsCreate) for the logged Act I, II, IV and V levels, with the act link
builder (sub_006772C0_LevelLinkBuild on the act-seed copy) modelled for the level rectangles, the level links, the
border-adjacency lists and the outdoor flags the window reads. Compares the seed at OD1, and the full list of what
OutdoorRoomsCreate makes after OD1 (preset anchors: def, rect, file index, grid0 flags; out rooms: rect).

Usage: python3 -I tools/outdoor_replay.py <merged-root> <exe> <log>... [-v]
Act III is replayed by tools/jungle_replay.py. Evidence: docs/findings/drlg/0008-outdoor.md § 13.
"""
import collections, csv, json, os, struct, sys

M32 = 0xFFFFFFFF
VERBOSE = "-v" in sys.argv
ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
ROOT, EXE = ARGS[0].rstrip("/"), ARGS[1]
EXCEL = os.path.join(ROOT, "data", "global", "excel") + "/"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds1 as ds1mod   # noqa: E402 (read-only import of the worktree parser)
import drlg            # noqa: E402 the act link builder has one implementation, in tools/drlg.py (plan 0022 Phase 2)

drlg.load_links(EXCEL, EXE)
from drlg import (COV, LV, Act, Fatal, Seed, act_links, adj_insert, adj_less, border_adj, rect_adj_dir,  # noqa: E402,F401
                  seams_by_touch, tdiv, touch)

EXEDATA = open(EXE, "rb").read()


def exe_read(va, n):
    data = EXEDATA
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


def ints(va, n):
    return list(struct.unpack("<%di" % n, exe_read(va, 4 * n)))


def tmod(a, b):
    return a - tdiv(a, b) * b


def tsv(path):
    rows = list(csv.reader(open(path, encoding="latin1"), delimiter="\t"))
    return rows[0], rows[1:]


h, rows = tsv(EXCEL + "lvlprest.txt")
PREST = {}
for r in rows:
    if len(r) > 10 and r[h.index("Def")].strip().isdigit():
        PREST[int(r[h.index("Def")])] = dict(files=int(r[h.index("Files")]), sx=int(r[h.index("SizeX")]),
                                             sy=int(r[h.index("SizeY")]))

# LvlSub records (lvlsub.bin, 0x15C each): Type +0, File +4, BordType +0x44, GridSize +0x4C
_b = open(EXCEL + "lvlsub.bin", "rb").read()
_n = struct.unpack_from("<I", _b)[0]
LVLSUB = []
for i in range(_n):
    rec = _b[4 + i * 0x15C: 4 + (i + 1) * 0x15C]
    LVLSUB.append(dict(type=struct.unpack_from("<i", rec, 0)[0], file=rec[4:0x40].split(b"\0")[0].decode("latin-1"),
                       bord=struct.unpack_from("<i", rec, 0x44)[0], gs=struct.unpack_from("<i", rec, 0x4C)[0]))
_SUBDS1 = {}


def sub_ds1(i):
    if i not in _SUBDS1:
        s = LVLSUB[i]
        path = os.path.join(ROOT, "data", "global", "tiles", s["file"].replace("\\", "/").lower())
        f = ds1mod.parse(open(path, "rb").read())
        L = f["layers"]
        _SUBDS1[i] = dict(cols=f["cols"], wall=list(L["wall0"]) if f["wall_layers"] else None,
                          floor=list(L["floor0"]) if f["floor_layers"] else None,
                          groups=[(g["x"], g["y"], g["w"], g["h"], g["unk"] or 0) for g in f["groups"]])
    return _SUBDS1[i]


# ================================================================ logs
def log_windows(path):
    """Per OD0: level ptr, id, seed0, seed1, and the OutdoorRoomsCreate output up to LI1 (anchors and out rooms)."""
    ev = []
    for l in open(path, errors="replace"):
        t, _, js = l.partition(" ")
        if t in ("OD0", "OD1", "PRC", "RL", "LI1", "LC0"):
            try:
                ev.append((t, json.loads(js)))
            except ValueError:
                pass
    out = []
    for i, (t, d) in enumerate(ev):
        if t != "OD0":
            continue
        lv = d["level"]; w = dict(id=d["id"], seed0=d["seed"], seed1=None, items=[], level=lv)
        for t2, d2 in ev[i + 1:]:
            if d2.get("level") != lv:
                continue
            if t2 == "OD1": w["seed1"] = d2["seed"]
            elif t2 == "PRC": w["items"].append(("P", d2["def"], d2["prect"][0], d2["prect"][1], d2["idx"], d2["flags"]))
            elif t2 == "RL" and d2["type"] == 1: w["items"].append(("R", d2["rect"][0], d2["rect"][1], d2["f28"]))
            # (RL logs room +0x28 at LevelRoomLink, before OutRoomCreate's grid0 is applied: compared as rect only)
            elif t2 == "LI1": break
        rs = [it for it in w["items"] if it[0] == "R"]
        w["client"] = bool(rs) and all(it[3] & 0x40000 for it in rs)
        COV["out room f28 at link (non-client) != 0"] += sum(1 for it in rs if it[3] & ~0x40000)
        # the client copy's out rooms carry room +0x28 bit 0x40000 (set by OutRoomCreate for the client; not a grid0 bit)
        if w["client"]:
            its = []
            for it in w["items"]:
                if it[0] == "R":
                    COV["client out room with 0x40000" if it[3] & 0x40000 else "client out room without 0x40000"] += 1
                its.append(it)
            w["items"] = its
        w["items"] = [it[:3] if it[0] == "R" else it for it in w["items"]]
        out.append(w)
    return out, ev


def log_meta(path):
    head = open(path).readline()
    ms = int(head.split("seed=")[1].split()[0])
    n = os.path.basename(path)
    diff = 2 if "hell" in n else 1 if "nightmare" in n else 0
    return ms, diff


ACT_OF = {}
for l, v in LV.items():
    ACT_OF[l] = v["act"]
ACT_OF[134] = 4


def main():
    logs = ARGS[2:]
    tot = bad = 0
    per = collections.Counter(); perbad = collections.Counter()
    seen = set()
    for path in logs:
        ms, diff = log_meta(path)
        wins, ev = log_windows(path)
        acts = {}
        for w in wins:
            lid = w["id"]
            a = ACT_OF[lid]
            if a == 2 and not os.environ.get("WITH_A3"):
                continue
            key = (ms, diff, lid, w["seed0"])
            dup = key in seen
            seen.add(key)
            if a not in acts:
                A = Act(a, ms, diff)
                act_links(A)
                acts[a] = A
            A = acts[a]
            ok, msg = run_window(A, lid, w)
            if dup and ok and not VERBOSE:
                continue
            tot += 1; bad += not ok
            per[lid] += 1; perbad[lid] += not ok
            print("%s level %d seed %s: %s" % (os.path.basename(path), lid, w["seed0"], "ok" if ok else "MISMATCH " + msg))
    print("windows %d, mismatches %d" % (tot, bad))
    print("per level:", {k: (per[k], perbad[k]) for k in sorted(per)})
    print(dict(COV))


def run_window(A, lid, w):
    r = A.rect.get(lid)
    xs = [it[2] if it[0] == "P" else it[1] for it in w["items"]]
    ys = [it[3] if it[0] == "P" else it[2] for it in w["items"]]
    lr = (min(xs), min(ys)) if xs else None
    if r is None:
        return False, "no rect"
    if lr and (lr[0] < r[0] or lr[1] < r[1] or lr[0] >= r[0] + r[2] or lr[1] >= r[1] + r[3]):
        return False, "rect %s, logged rooms start %s" % (r, lr)
    try:
        O = Outdoor(A, lid, Seed(*[int(x, 16) for x in w["seed0"].split(":")]))
        O.run()
    except NotImplementedError as e:
        return False, "not modelled: %s" % e
    except Fatal as e:
        return False, "fatal %s" % e
    got = O.seed.fmt()
    exp = O.items()
    if got != w["seed1"]:
        msg = "OD1 %s, model %s; " % (w["seed1"], got)
    else:
        msg = ""
    if exp != w["items"]:
        n = next((k for k in range(min(len(exp), len(w["items"]))) if exp[k] != w["items"][k]), min(len(exp), len(w["items"])))
        msg += "items %d/%d, first diff at %d: model %s log %s" % (len(exp), len(w["items"]), n,
                                                                  exp[n] if n < len(exp) else None, w["items"][n] if n < len(w["items"]) else None)
    return msg == "", msg


# ================================================================ the outdoor window
PROBE = ints(0x6F05D8, 8)
BDEFS = ints(0x6F0620, 13 * 4)        # g_BorderDefs rows 0..12 x 4 styles (row 0 is another table's tail)
BDEFS5 = ints(0x6F06F0, 12 * 2)       # Act V families
DIRIDX = {(-1, 0): ints(0x6F0FD0 - 4, 1)[0], (0, -1): ints(0x6F0FD0 - 12, 1)[0], (1, 0): ints(0x6F0FD0 + 4, 1)[0],
          (0, 1): ints(0x6F0FD0 + 12, 1)[0], (0, 0): ints(0x6F0FD0, 1)[0]}
CORNER = ints(0x6F1088 - 40 * 4, 81)  # centre-based
PAIR = ints(0x6F112C, 10)
NBR_DY = list(struct.unpack("<8b", exe_read(0x6F060C, 8)))
NBR_DX = list(struct.unpack("<8b", exe_read(0x6F0614, 8)))
SHRINE_FLAG = ints(0x6F061C, 4)
A5MAP = ints(0x6F2038, 50)
RIVER_T = ints(0x6F2680, 32)
HUB_DX = ints(0x6F2810, 4)
HUB_DY = ints(0x6F2800, 4)
T2840 = list(exe_read(0x6F2840, 16))
DY4 = list(struct.unpack("<4b", exe_read(0x6F2850, 4)))
DX4 = list(struct.unpack("<4b", exe_read(0x6F2854, 4)))
T8 = ints(0x6F1518, 75)


def dir4(x, y, tx, ty):   # 0x00678CF0 / 0x00678B80, then /2
    dx, dy = tx - x, ty - y
    ax, ay = abs(dx), abs(dy)
    if ax >= 2 * ay:
        dy = -1 if dy < 0 else dy & 1
    elif ay >= 2 * ax:
        dx = -1 if dx < 0 else dx & 1
    dx = max(-2, min(2, dx)); dy = max(-2, min(2, dy))
    return tdiv(T8[3 * (5 * dx + dy + 12)], 2)
A5STEP = ints(0x6F1FD8, 24)
A5CAVE = ints(0x6F1F9C, 15)
A5TABLE = ints(0x6F2100, 105)


class V:
    __slots__ = ("x", "y", "type", "flags", "next")

    def __init__(s, x, y, t=0):
        s.x, s.y, s.type, s.flags, s.next = x, y, t, 0, None


def sgn(z):
    return -1 if z < 0 else 1 if z > 0 else 0


def e2(z):
    return z - 2 if z < 0 else z + 2 if z > 0 else 0


class Outdoor:
    def __init__(O, A, lid, seed):
        O.A, O.lid, O.seed = A, lid, seed
        O.rect = list(A.rect[lid])
        O.cw, O.ch = tdiv(O.rect[2], 8), tdiv(O.rect[3], 8)
        O.cell = [[0] * O.cw for _ in range(O.ch)]
        O.defg = [[0] * O.cw for _ in range(O.ch)]
        O.g0 = [[0] * O.cw for _ in range(O.ch)]
        O.rot = {}
        O.flags = A.oflags[lid]
        O.adj = A.adj.get(lid, [])
        O.act = ACT_OF[lid]
        O.ltype = LV[lid]["ltype"]

    # ---- grids
    def inb(O, x, y):
        return 0 <= x < O.cw and 0 <= y < O.ch

    def rotation(O, d):
        if d not in O.rot:
            n = PREST[d]["files"]
            O.rot[d] = [n, O.seed.range(n)]
            COV["rotation first use"] += 1
        r = O.rot[d]
        if r[0] == 0:
            raise Fatal("rotation of def %d with Files 0 (idiv by zero)" % d)
        r[1] = tmod(r[1] + 1, r[0])
        return r[1]

    def place(O, x, y, d, idx, flag=0):   # 0x006743C0
        P = PREST[d]
        w, h = tdiv(P["sx"], 8), tdiv(P["sy"], 8)
        if idx == -1:
            idx = O.rotation(d)
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                c = (O.cell[yy][xx] & ~0xF0000) | ((idx << 16) & M32) | 0x200
                if flag and (4 <= d <= 15 or 364 <= d <= 375):
                    c |= 1
                O.cell[yy][xx] = c
                O.defg[yy][xx] = 0
        O.defg[y][x] = d

    def fits(O, x, y, d, pad=0, sides=0):   # 0x00674230
        if d == 0:
            w = h = 1
        else:
            P = PREST[d]; w, h = tdiv(P["sx"], 8), tdiv(P["sy"], 8)
        if pad:
            if sides & 1: y -= pad; h += pad
            if sides & 2: w += pad
            if sides & 4: h += pad
            if sides & 8: x -= pad; w += pad
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if not O.inb(xx, yy) or O.cell[yy][xx] & 0x1B81:
                    return False
        return True

    def shuffle(O, w, h):
        n = w * h
        a = [(i % w, i // w) for i in range(n)]
        for _ in range(n):
            u = O.seed.range(n); v = O.seed.range(n)
            a[u], a[v] = a[v], a[u]
        return a

    def place_random(O, d, idx=-1, pad=0, sides=0xF):   # 0x00674730
        N = (O.cw - 2) * (O.ch - 2)
        if N <= 0:
            return 0
        for (x, y) in O.shuffle(O.cw - 2, O.ch - 2):
            if O.fits(x + 1, y + 1, d, pad, sides):
                O.place(x + 1, y + 1, d, idx, 0)
                COV["PlaceRandom placed"] += 1
                return 1
        COV["PlaceRandom failed"] += 1
        return 0

    def place_near(O, d, idx=-1):   # 0x00674920
        N = (O.cw - 2) * (O.ch - 2)
        if N <= 0:
            return 0
        for (x, y) in O.shuffle(O.cw - 2, O.ch - 2):
            if O.cell[y + 1][x + 1] & 0x80:
                for k in range(8):
                    X, Y = x + 1 + NBR_DX[k], y + 1 + NBR_DY[k]
                    if O.fits(X, Y, d, 0, 0xF):
                        O.place(X, Y, d, idx, 0)
                        COV["PlaceNear placed"] += 1
                        return 1
        COV["PlaceNear fallback"] += 1
        return O.place_random(d, idx, 0, 0xF)

    def place_far(O, rect, d, idx, pad, sides):   # 0x006744F0
        W, H = O.cw - 2, O.ch - 2
        ox = O.seed.range(W); oy = O.seed.range(H)
        tx = rect[0] + tdiv(rect[2], 2); ty = rect[1] + tdiv(rect[3], 2)
        best = 0; bx = by = -1
        for r in range(H + 1):
            y = tmod(r + oy, H) + 1
            for c in range(W + 1):
                x = tmod(c + ox, W) + 1
                if O.fits(x, y, d, pad, sides):
                    a = abs(8 * x + O.rect[0] + 4 - tx); b = abs(8 * y + O.rect[1] + 4 - ty)
                    dd = tdiv(b + 2 * a if a > b else a + 2 * b, 2)
                    if dd > best:
                        best, bx, by = dd, x, y
        if bx != -1 and by != -1:
            O.place(bx, by, d, idx, 0)
            return 1
        return 0

    # ---- vertex ring
    def ring_build(O):
        R = O.rect
        x, y, w, h = R[0], R[1], R[2] - 1, R[3] - 1
        v0, v1, v2, v3 = V(x, y + h), V(x, y), V(x + w, y), V(x + w, y + h)
        v0.next, v1.next, v2.next, v3.next = v1, v2, v3, v0
        for n in O.adj:   # 0x0067CE20, node list order
            r = list(n["rect"]); r[2] -= 1; r[3] -= 1
            side = n["side"]
            if side == 0: p, vert, c, a, b, s, e = v0, True, -1, r[1] + r[3], r[1], v0.y, v1.y
            elif side == 1: p, vert, c, a, b, s, e = v1, False, 1, r[0], r[0] + r[2], v1.x, v2.x
            elif side == 2: p, vert, c, a, b, s, e = v2, True, 1, r[1], r[1] + r[3], v2.y, v3.y
            elif side == 3: p, vert, c, a, b, s, e = v3, False, -1, r[0] + r[2], r[0], v3.x, v0.x
            else:
                raise Fatal("adjacency side %d" % side)

            def ins(p, coord):
                q = V(p.x if vert else coord, coord if vert else p.y)
                q.next = p.next; p.next = q
                return q
            if a * c <= s * c:
                if s * c > b * c:
                    continue
            else:
                if a * c > e * c:
                    continue
                p = ins(p, a)
            p.flags |= 1
            if n["preset"]:
                p.flags |= 2
            if b * c < e * c:
                ins(p, b)
            COV["ring seam side %d" % side] += 1
        v = v0
        while True:
            v.x -= O.rect[0]; v.y -= O.rect[1]
            v = v.next
            if v is v0:
                break
        # 0x00675080: to cells, merge equal consecutive vertices
        head = v0
        v = head
        while True:
            v.x, v.y = tdiv(v.x, 8), tdiv(v.y, 8)
            v = v.next
            if v is head:
                break
        v = head
        while True:
            n = v.next
            if v.x == n.x and v.y == n.y:
                if n is head:
                    head = v
                v.next = n.next; v.flags |= n.flags; v.type = n.type
                COV["ring merge"] += 1
            v = v.next
            if v is head:
                break
        O.ring = head

    def ring_list(O):
        out = []; v = O.ring
        while True:
            out.append(v); v = v.next
            if v is O.ring:
                return out

    def seam_warp_flag(O, v):   # 0x00674040
        x, y, cw, ch = v.x, v.y, O.cw, O.ch
        if x == 0:
            side = 1 if y == 0 else 0
        elif y == 0:
            side = (x == cw - 1) + 1
        elif x == cw - 1:
            side = (y == ch - 1) + 2
        elif y == ch - 1:
            side = 3
        else:
            return 0
        px = PROBE[2 * side] + 8 * x + O.rect[0]; py = PROBE[2 * side + 1] + 8 * y + O.rect[1]
        for n in O.adj:
            r = n["rect"]
            if n["side"] == side and r[0] <= px < r[0] + r[2] and r[1] <= py < r[1] + r[3]:
                vis = O.A.vis(O.lid)
                for k in range(8):
                    if vis[k] == n["nbr"]:
                        return 0x10 << k
                return 0
        return 0

    def seg_cells(O, v):
        n = v.next
        if v.x == n.x:
            if v.y == n.y:
                return [(v.x, v.y)]
            a, b = sorted((v.y, n.y))
            return [(v.x, y) for y in range(a, b + 1)]
        a, b = sorted((v.x, n.x))
        return [(x, v.y) for x in range(a, b + 1)]

    def seam_mark(O):   # 0x00675770
        for v in O.ring_list():
            if v.flags & 1:
                f = O.seam_warp_flag(v)
                cv = 3 if v.type else 1
                for (x, y) in O.seg_cells(v):
                    if O.inb(x, y):
                        O.g0[y][x] |= f
                        O.cell[y][x] |= cv
                    else:
                        raise Fatal("seam cell out of grid")

    def style(O, t):
        lt = O.ltype
        if lt == 2: return 1 if t == 0 else 0
        if lt == 16: return 2
        if lt == 27: return 3
        if lt == 31: return 4 + (O.lid == 117)
        return -1

    def border_build(O):   # 0x00675850
        for v in O.ring_list():
            n = v.next
            dx, dy = sgn(n.x - v.x), sgn(n.y - v.y)
            dx2, dy2 = sgn(n.next.x - n.x), sgn(n.next.y - n.y)
            ax, ay = abs(dx), abs(dy)
            ln = abs(v.x - n.x) if ax else abs(v.y - n.y)
            cv = 3 if v.type else 1
            s = O.style(v.type)
            di = DIRIDX[(dx, dy)]
            d = BDEFS[4 * (1 + di) + s] if s < 4 else BDEFS5[(s - 4) + 2 * di]
            if not (v.flags & 2):
                x, y = v.x, v.y
                while (x, y) != (n.x, n.y):
                    y += dy; x += dx
                    O.place(x, y, d, -1, 0)
                    O.cell[y][x] |= cv
            if (v.flags & 1) and not (v.flags & 2):
                mx = min(v.x, n.x) + tdiv(ln * ax, 2); my = min(v.y, n.y) + tdiv(ln * ay, 2)
                if O.act in (0, 4, 3):
                    val = 0x40400 if (O.lid == 17 and O.act in (0, 4)) else 0x30400
                    O.cell[my][mx] = (O.cell[my][mx] & ~0xF0000) | val
                    COV["seam opening"] += 1
                elif O.act == 1:
                    k = dx + 2 * dy + 2
                    O.place(mx, my, PAIR[2 * k], -1, 0)
                    O.place(mx + ax, my + ay, PAIR[2 * k + 1], -1, 0)
                    COV["seam opening (Act II pair)"] += 1
            t = v.type if v.type else n.type
            if t:
                cv |= 2
            s = O.style(t)
            a = e2(dx) if v.flags & 2 else e2(2 * dx)
            b = (e2(dx2) + dy2) if n.flags & 2 else (e2(2 * dx2) + 2 * dy2)
            c = dy if v.flags & 2 else 2 * dy
            k = CORNER[40 + a + 9 * b + c]
            if k == -1:
                continue
            cd = BDEFS[s + 4 * k] if s < 4 else BDEFS5[(s - 6) + 2 * k]
            if cd == 0x13:
                cd = (0x13 + (n.type != 1)) if v.type == 1 else 0x15
            elif cd == 0:
                continue
            O.place(n.x, n.y, cd, -1, 0)
            O.cell[n.y][n.x] |= cv
        O.corner_flood()

    def corner_flood(O):   # 0x00675670
        for (xf, yf, dx, dy) in ((0, 0, 1, 1), (1, 0, -1, 1), (0, 1, 1, -1), (1, 1, -1, -1)):
            x0 = O.cw - 1 if xf else 0
            y = O.ch - 1 if yf else 0
            while not (O.cell[y][x0] & 1):
                x = x0
                while not (O.cell[y][x] & 1):
                    O.cell[y][x] |= 0x100
                    x += dx
                y += dy

    # ---- tag-2 LvlSub border substitutions (0x006752A0 -> 0x00670750 -> 0x0066F990 -> 0x0066F690)
    def border_sub(O, typ, base, act5=False):
        ctx = dict(type=typ, base=base, wild=-1, act5=act5)
        i = next(k for k, s in enumerate(LVLSUB) if s["type"] == typ)
        while i < len(LVLSUB) and LVLSUB[i]["type"] == typ:
            O.bsub_record(i, ctx)
            i += 1

    def bsub_record(O, ri, ctx):
        rec = LVLSUB[ri]; S = sub_ds1(ri); G = S["groups"]
        if not G:
            return
        if ctx["wild"] == -1:
            ctx["wild"] = 62
        s = O.seed.range(len(G)) if rec["bord"] == 0 else 0
        for i in range(len(G)):
            ok = O.bsub_group(ctx, rec, S, G[(s + i) % len(G)])
            if ok and rec["bord"] == 0:
                return

    def bsub_group(O, ctx, rec, S, g):
        GS = rec["gs"]
        off = -1 if (ctx["type"] == 1 and (O.flags & 0xC)) else 1
        nx = O.cw - g[2] * GS + off; ny = O.ch - g[3] * GS + 1
        N = nx * ny
        if N == 0:
            return 0
        if N < 0:
            COV["border sub N < 0"] += 1
            return 0
        skip22 = ctx["type"] == 1 and 2 <= O.lid <= 7 and nx < 6 and ny < 6
        lst = [(i % nx, i // nx) for i in range(N)]
        for _ in range(N):
            a = O.seed.range(N); b = O.seed.range(N)
            lst[a], lst[b] = lst[b], lst[a]
        ret = 0
        for (px, py) in lst:
            if skip22 and px == 2 and py == 2:
                continue
            if O.bsub_fits(ctx, S, g, GS, px, py):
                v = O.seed.range(g[4])
                O.bsub_stamp(ctx, S, g, GS, px, py, (g[2] + 1) * (v + 1))
                COV["border sub stamp (type %d)" % ctx["type"]] += 1
                ret = 1
                if rec["bord"] in (0, 1):
                    return 1
        return ret

    def bsub_cells(O, S, g, GS, px, py, srcx):
        px -= tmod(px, GS); py -= tmod(py, GS)
        cols = S["cols"]
        for gy in range(g[3]):
            for gx in range(g[2]):
                si = (g[1] + gy) * cols + g[0] + gx + srcx
                W = S["wall"][si] if S["wall"] else 0
                F = S["floor"][si] if S["floor"] else 0
                yield px + GS * gx, py + GS * gy, W, F

    def bsub_fits(O, ctx, S, g, GS, px, py):
        for X, Y, W, F in O.bsub_cells(S, g, GS, px, py, 0):
            if not O.inb(X, Y):
                raise NotImplementedError("border sub cell outside the grid")
            D = O.defg[Y][X]
            if ctx["act5"]:
                if not O.a5_match(X, Y, D, F, W):
                    return False
            elif W & 1:
                o = ((W >> 8) & 0xFF) - 1
                if o != ctx["wild"] and ctx["base"] + o != D:
                    return False
                if O.cell[Y][X] & 0x400:
                    return False
            elif F & 2:
                if not O.fits(X, Y, 0, 0, 0):
                    return False
        return True

    def bsub_stamp(O, ctx, S, g, GS, px, py, srcx):
        for X, Y, W, F in O.bsub_cells(S, g, GS, px, py, srcx):
            if W & 1:
                o = ((W >> 8) & 0xFF) - 1
                d = O.a5_map((W >> 20) & 0x3F, (W >> 8) & 0xFF) if ctx["act5"] else ctx["base"] + o
                if d != -5 and o != ctx["wild"]:
                    O.place(X, Y, d, 0, 1)
            elif F & 2:
                O.defg[Y][X] = 0; O.cell[Y][X] = 0
            else:
                O.defg[Y][X] = 0; O.cell[Y][X] = 0x100

    # ---- output: what OutdoorRoomsCreate makes
    def items(O):
        out = []
        for cy in range(O.ch):
            for cx in range(O.cw):
                c = O.cell[cy][cx]
                x, y = O.rect[0] + 8 * cx, O.rect[1] + 8 * cy
                if c & 0x200:
                    if O.defg[cy][cx]:
                        out.append(("P", O.defg[cy][cx], x, y, (c >> 16) & 0xF, O.g0[cy][cx]))
                elif not (c & 0x100):
                    out.append(("R", x, y))
        return out

    def run(O):
        O.ring_build()
        a = O.act
        if O.lid == 134:
            a = 1
        getattr(O, "act%d" % (a + 1))()

    # ---- Act I (sub_006807F0_OutdoorAct1)
    def a1_cliff_mark(O):   # 0x00680070
        head = O.ring
        p = head
        while p.next is not head:
            p = p.next
        v = head; first = head; done = False
        while True:
            w = v
            n0 = v.next
            if ((v.x < n0.x and v.y < p.y and not v.flags & 1 and not p.flags & 1) or
                    (n0.y < v.y and v.x < p.x and not v.flags & 1 and not p.flags & 1)):
                last = None
                while True:
                    if w is first:
                        done = True
                    n = w.next
                    if w.y < n.y or n.x < w.x or w.flags & 1 or n.flags & 1:
                        break
                    if (w.x < n.x and n.y < n.next.y and not n.flags & 1) or (n.y < w.y and n.x < n.next.x and not n.flags & 1):
                        last = w
                    w = n
                    if n is v:
                        break
                if last is not None:
                    q = v
                    while q is not last:
                        q.type = 1; q = q.next
                    q.type = 1
                    O.flags |= 0x20
                    COV["A1 cliff run"] += 1
            v = w.next
            if done:
                return
            p = w; first = O.ring
            if v is O.ring:
                return

    def a1_river_clear(O, x):   # 0x0067FC70
        for y in range(O.ch):
            if O.cell[y][x] & 2 or O.cell[y][x + 1] & 2:
                return False
        return True

    def a1_river(O, x):   # 0x0067FE90
        for y in range(O.ch):
            for col, d, k in ((x, 26, 0), (x + 1, 27, 1)):
                c = O.cell[y][col]; pd = O.defg[y][col]
                if pd == 0:
                    idx = 0 if c & 0x100 else 3
                elif pd == 7 and (c & 0xF0000) == 0x30000:
                    idx = 3
                else:
                    idx = RIVER_T[2 * pd + k]
                O.place(col, y, d, idx)
        COV["A1 river"] += 1
        if O.flags & 0x14:
            O.a1_bridge(x)

    def free(O, x, y):   # 0x00674200
        return not (O.cell[y][x] & 0x1B81)

    def a1_bridge(O, x):   # 0x0067FD20
        n = O.ch - 2
        s0 = O.seed.range(n)
        for k in range(max(n, 0)):
            y = tmod(k + s0, n) + 1
            if not (O.flags & 4) and not O.free(x - 1, y):
                continue
            if not O.free(x + 2, y) if not (O.flags & 4) else not O.free(x - 1, y):
                continue
            if (O.cell[y][x] & 0xF0000) != 0x30000 or (O.cell[y][x + 1] & 0xF0000) != 0x30000:
                continue
            O.place(x, y, 28, 1); O.place(x + 1, y, 28, 2 + ((O.flags & 4) != 0))
            COV["A1 bridge"] += 1
            return

    def a1_cave_try(O, x, y):   # 0x006801A0
        d = O.defg[y][x]
        if d == 16: O.place(x, y, 25, -1)
        elif d == 17: O.place(x, y, 24, -1)
        else: return 0
        O.flags |= 0x40
        return 1

    def a1_river_east_cave(O):   # 0x00680200
        if O.flags & 0xC and O.a1_river_clear(O.cw - 2):
            O.a1_river(O.cw - 2)
        if O.flags & 0x20 and not O.flags & 0x40:
            r = O.seed.step()
            hit = 0
            if r & 1 == 0:
                for y in range(O.ch):
                    for x in range(O.cw):
                        hit = O.a1_cave_try(x, y)
                        if hit: break
                    if hit: break
            else:
                for x in range(O.ch):
                    for y in range(O.cw):
                        hit = O.a1_cave_try(x, y)
                        if hit: break
                    if hit: break
            if not hit:
                raise Fatal("cliff cave not placed")
            COV["A1 cliff cave"] += 1
        if O.flags & 0x1C and not O.flags & 0x40:
            x0 = O.cw - (4 if O.flags & 0x10 else 5)
            r = O.seed.step() & 3
            x = 3 if r & 1 else x0
            y = 3 if r >> 1 else O.ch - 4
            O.place(x, y, 51 + (O.lid == 2), -1)
            O.flags |= 0x40
            COV["A1 corner cave"] += 1

    def a1_mid_trans_cave(O):   # 0x006803D0
        if O.flags & 0x10 and O.a1_river_clear(tdiv(O.cw, 2) - 1):
            O.a1_river(tdiv(O.cw, 2) - 1)
        if O.flags & 0x80: O.place(0, 0, 3, 1)
        if O.flags & 0x100: O.place(O.cw - 7, 0, 3, 2)
        if O.flags & 0x200: O.place(0, 1, 2, 1)
        if O.flags & 0x400: O.place(0, O.ch - 6, 2, 1)
        if not O.flags & 0x40:
            if O.lid == 2:
                ok = O.place_far(O.A.rect[1], 52, -1, 1, 0xF)
            else:
                ok = O.place_random(51, -1, 1, 0xF)
            if not ok:
                raise Fatal("cave not placed")
            O.flags |= 0x40

    # roads (0x00681420)
    def snap(O, pt):   # 0x00680CC0
        x, y, d = pt
        x -= O.rect[0]; y -= O.rect[1]
        if d == 0: x = tdiv(x, 8) * 8 + 11
        elif d == 1: y = tdiv(y, 8) * 8 + 11
        elif d == 2: x = tdiv(x, 8) * 8 - 5
        elif d == 3: y = tdiv(y, 8) * 8 - 5
        return [x + O.rect[0], y + O.rect[1], d]

    def a1_paths(O):
        Lx, Ly = O.rect[0], O.rect[1]
        A = []
        for n in O.adj:   # 0x00680D70
            if n["nbr"] == 1:
                r = n["rect"]; off = {0: (59, 19), 1: (29, 35), 2: (4, 22), 3: (29, 3)}.get(n["side"])
                if off is None:
                    raise NotImplementedError("town node side %d" % n["side"])
                A.append([r[0] + off[0], r[1] + off[1], n["side"]])
            elif n["nbr"] == 26:
                r = n["rect"]; A.append([r[0] + 27, r[1] + 13, 1])
        for x in range(O.cw):
            for y in range(O.ch):
                d = O.defg[y][x]; idx = (O.cell[y][x] >> 16) & 0xF
                dr = 4
                if d == 4 and idx == 3: dr = 3
                elif d == 5 and idx == 3: dr = 0
                elif d == 6 and idx == 3: dr = 1
                elif d == 7 and idx == 3: dr = 2
                elif d == 24: dr = 1
                elif d == 25: dr = 0
                elif d == 28 and idx == 1 and x == O.cw - 2: dr = 2
                elif d in (51, 52): dr = 1 if idx != 0 else 0
                if dr != 4:
                    A.append([Lx + 3 + 8 * x, Ly + 3 + 8 * y, dr])
        if len(A) > 6:
            raise NotImplementedError("more than 6 road endpoints")
        Bp = [O.snap(a) for a in A]
        cnt = len(A)
        COV["A1 road endpoints %d" % cnt] += 1
        # 0x00681000 hubs
        D = []
        bx = by = -1
        if O.flags & 0x10:
            xc = tdiv(O.cw, 2) - 1
            for yy in range(1, O.cw - 1):   # row bound cw-1 as in the code
                if yy >= O.ch:
                    raise NotImplementedError("BridgeFind reads past the grid")
                if O.defg[yy][xc] == 28 and ((O.cell[yy][xc] >> 16) & 0xF) == 1:
                    bx, by = xc, yy; break
        if bx != -1:
            X = Lx + 3 + bx * 8
            for a in A:
                D.append([X + 8, Ly + 3 + by * 8, 0] if X < a[0] else [X, Ly + 3 + by * 8, 2])
            COV["A1 road hub at the bridge"] += 1
        elif cnt > 0:
            if cnt == 1:
                cx, cy = tdiv(O.cw, 2), tdiv(O.ch, 2)
            else:
                cx = tdiv(sum(a[0] - Lx for a in A), cnt * 8); cy = tdiv(sum(a[1] - Ly for a in A), cnt * 8)
            found = False
            for r in range(8):
                for j in range(4):
                    hx = HUB_DX[j] * r + cx; hy = HUB_DY[j] * r + cy
                    if 0 <= hx < O.cw and 0 <= hy < O.ch and O.free(hx, hy):
                        found = True; break
                if found: break
            hub = [Lx + 3 + hx * 8, Ly + 3 + hy * 8, 4]
            D = [list(hub) for _ in A]
        C = [O.snap(dd) for dd in D]
        for i in range(cnt):
            path = O.a1_search(Bp[i], C[i])
            if path is not None:
                for (x, y) in path:
                    if O.inb(x, y):
                        O.cell[y][x] |= 0x80
                O.seed.step()   # 0x00681240: r = step & 3
                nint = len(path) - 2
                for _ in range(max(nint, 0)):
                    O.seed.step(); O.seed.step()
                COV["A1 road path found"] += 1
            else:
                COV["A1 road path not found"] += 1

    def a1_search(O, Bw, Cw):   # 0x006817D0
        sx, sy = tdiv(Bw[0] - O.rect[0], 8), tdiv(Bw[1] - O.rect[1], 8)
        tx, ty = tdiv(Cw[0] - O.rect[0], 8), tdiv(Cw[1] - O.rect[1], 8)
        if abs(sx - tx) + abs(sy - ty) <= 1:
            return [(sx, sy), (tx, ty)]
        def h(x, y):
            a, b = abs(x - tx), abs(y - ty)
            return min(a, b) + 2 * max(a, b)
        h0 = h(sx, sy)
        d0 = dir4(sx, sy, tx, ty)
        bound = h0 + tdiv(h0, 2); top = bound + 35
        while True:
            res, cnt = O.a1_ida(sx, sy, tx, ty, d0, h0, bound)
            bound += 5
            if cnt > 899:
                COV["A1 road search pool exhausted"] += 1
                return None
            if res is not None:
                return res
            if not bound < top:
                return None

    def a1_ida(O, sx, sy, tx, ty, d0, h0, bound):   # 0x00681630 on a fresh pool
        class N:
            __slots__ = ("f", "h", "g", "x", "y", "tried", "row", "ptr", "dir", "parent", "child")
        root = N(); root.f = root.h = h0; root.g = 0; root.x, root.y = sx, sy; root.tried = -1; root.row = 0; root.ptr = 0
        root.dir = d0 & 3; root.parent = None; root.child = None
        cnt = [1]
        node = root
        while True:
            if node.x == tx and node.y == ty:
                path = []; q = node
                while q is not None:
                    path.append((q.x, q.y)); q = q.parent
                return path, cnt[0]
            nx = node.x + DX4[node.dir]; ny = node.y + DY4[node.dir]
            ok = False
            if nx == tx and ny == ty:
                ok = True
            elif 0 <= nx < O.cw and 0 <= ny < O.ch and not O.cell[ny][nx] & 0x200:
                ok = True; q = node
                while q is not None:
                    if q.x == nx and q.y == ny:
                        ok = False; break
                    q = q.parent
            if ok:
                cost = 2 if (node.x == nx or node.y == ny) else 3
                a, b = abs(nx - tx), abs(ny - ty)
                hh = min(a, b) + 2 * max(a, b)
                f = hh + node.g + cost
                if f <= bound:
                    if node.child is None:
                        if cnt[0] == 900:
                            return None, cnt[0]
                        cnt[0] += 1
                        c = N(); c.child = None; c.parent = node; node.child = c
                    c = node.child
                    c.h = hh; c.f = f; c.g = node.g + cost; c.tried = 0
                    td = dir4(nx, ny, tx, ty)
                    row = (node.dir - td) & 3
                    c.row = row; c.ptr = 0
                    c.dir = (T2840[4 * row] + td) & 3
                    c.x, c.y = nx, ny
                    node = c
                    continue
            # 0x00681560 backtrack
            n = node
            if n.tried < 4:
                n.ptr += 1; n.dir = (T2840[(4 * n.row + n.ptr) % 16] + n.dir) & 3
            n.tried += 1
            if n.tried == 3:
                while True:
                    if n is root:
                        return None, cnt[0]
                    n = n.parent
                    n.ptr += 1; n.dir = (T2840[(4 * n.row + n.ptr) % 16] + n.dir) & 3
                    n.tried += 1
                    if n.tried != 3:
                        break
            node = n

    def act1(O):
        lid = O.lid
        if lid not in (2, 3, 17):
            O.a1_cliff_mark()
        O.seam_mark()
        O.border_build()
        if 2 <= lid <= 7:
            O.border_sub(0, 4)
            O.a1_river_east_cave()
            O.border_sub(1, 4); O.border_sub(2, 4)
            O.a1_mid_trans_cave()
            O.border_sub(3, 4)
            O.a1_paths()
        if lid == 39:
            for t in range(4):
                O.border_sub(t, 4)
        if 3 <= lid <= 6:
            O.waypoint()
        if 2 <= lid <= 7:
            O.shrines()
        Near, Rand = O.place_near, (lambda d: O.place_random(d, -1, 0, 0xF))
        def one_or_two(d, s):
            r = O.seed.step()
            if r & 3 == 0:
                Near(d); Near(d)
            else:
                Near(d)
                if s and O.seed.step() & 1:
                    Near(49)
        if lid == 2: Near(46); one_or_two(47, 0); Rand(29); Rand(30)
        elif lid == 3: one_or_two(48, 1); Rand(44); Rand(29); Rand(30)
        elif lid == 4: Near(160); Near(45); Rand(162); one_or_two(47, 1); one_or_two(42, 0); Rand(31)
        elif lid == 5: Rand(161); Rand(41); Rand(40); one_or_two(48, 1); one_or_two(43, 0); Rand(29); Rand(30)
        elif lid == 6: Rand(163); Rand(38); Rand(39); one_or_two(47, 1); one_or_two(42, 0); Rand(29); Rand(30)
        elif lid == 7: one_or_two(48, 1); one_or_two(43, 0); Rand(31)
        elif lid == 17: O.place(1, 1, 108, -1)
        elif lid == 39:
            for d in (50, 46, 31, 38, 39, 29, 30): Rand(d)

    def waypoint(O):   # 0x00674B70
        if O.lid == 3:
            vis = O.A.vis(3)
            k = next((k for k in range(8) if vis[k] == 2), 8)
            f = 0x10 << k
            for y in range(O.ch):
                for x in range(O.cw):
                    if (O.g0[y][x] & f) and (O.cell[y][x] & 0x400):
                        x = 1 if x == 0 else x; y = 1 if y == 0 else y
                        if x == O.cw - 1: x -= 1
                        if y == O.ch - 1: y -= 1
                        O.g0[y][x] |= 0x20000; O.cell[y][x] |= 0x800
                        COV["waypoint by the Blood Moor seam"] += 1
                        return
        N = (O.cw - 2) * (O.ch - 2)
        if N <= 0:
            return
        for (x, y) in O.shuffle(O.cw - 2, O.ch - 2):
            if not O.cell[y + 1][x + 1] & 0x1B81:
                O.g0[y + 1][x + 1] |= 0x10000; O.cell[y + 1][x + 1] |= 0x800
                COV["waypoint placed"] += 1
                return
        COV["waypoint not placed"] += 1

    def shrines(O, count=5):   # 0x00674E40
        r = O.seed.step() & 3
        N = (O.cw - 2) * (O.ch - 2)
        if N <= 0:
            return
        for (x, y) in O.shuffle(O.cw - 2, O.ch - 2):
            if count <= 0:
                break
            if not O.cell[y + 1][x + 1] & 0x1B81:
                O.g0[y + 1][x + 1] |= SHRINE_FLAG[r]; O.cell[y + 1][x + 1] |= 0x1000
                r = (r + 1) & 3; count -= 1
                COV["shrine placed"] += 1

    def place_list(O, defs, perfile):   # 0x0067F470
        n = len(defs)
        k = O.seed.range(n)
        for _ in range(n):
            if not perfile:
                O.place_random(defs[k], -1, 0, 0xF)
            else:
                for i in range(PREST[defs[k]]["files"]):
                    O.place_random(defs[k], i, 0, 0xF)
            k = tmod(k + 1, n)

    def a2_subs(O):   # 0x0067F630
        for t in (2, 1, 3):
            O.border_sub(t, 364)

    def a2_special(O):   # 0x0067F670
        d = {41: 388, 42: 388, 43: 390, 44: 412, 45: 389}.get(O.lid)
        if d is None or not O.place_random(d, -1, 0, 0xF):
            raise Fatal("Act II special area")

    def a2_cliff(O):   # 0x0067F5C0
        k = O.seed.step() & 7
        COV["Act II cliff layout %d" % k] += 1
        e = ints(0x6F2390 + 0x50 * k, 20)
        for j in range(5):
            d, idx, x, y = e[4 * j: 4 * j + 4]
            O.place(x, y, d, idx)

    def act2(O):   # sub_0067F980_OutdoorAct2
        O.seam_mark()
        O.border_build()
        lid = O.lid
        if lid == 41:
            node = next((n for n in O.adj if n["nbr"] == 40), None)
            if node is not None:
                if node["side"] == 3: O.place(0, O.ch - 1, 363, -1)
                else: O.place(O.cw - 1, 0, 362, -1)
            O.a2_subs(); O.a2_special(); O.shrines()
            O.place_list([395, 411, 401, 402, 399, 398, 403], 0)
        elif lid in (42, 43, 44):
            O.a2_cliff(); O.a2_subs(); O.a2_special()
            if lid == 42:
                O.waypoint(); O.shrines()
                O.place_list([395, 411, 400, 398], 0); O.place_list([404, 405, 406, 407], 1)
            elif lid == 43:
                O.place_list([396, 397], 0); O.waypoint(); O.shrines()
                O.place_list([411, 399, 398, 403], 0); O.place_list([395], 1); O.place_list([395], 1)
            else:
                O.place_list([413, 408, 409, 410], 0); O.waypoint(); O.shrines()
                O.place_list([395, 400, 398, 404, 405], 0); O.place_list([411], 1); O.place_list([411], 1)
        elif lid == 45:
            O.a2_special()
        elif lid == 46:
            e = ints(0x6F2610, 36)
            for j in range(9):
                d, idx, x, y = e[4 * j: 4 * j + 4]
                O.place(x, y, d, idx)
            O.place(4, 4, 394, -1)
            O.a2_subs(); O.shrines()
            O.place_list([401, 402, 406, 407, 403], 0); O.place_list([392, 393], 1)
        elif lid == 134:
            O.place(4, 4, 394, -1)
            O.a2_subs()
            O.place_list([401, 402, 406, 407, 403], 0); O.place_list([392, 393], 1)
            O.shrines()

    def act3(O):
        raise NotImplementedError("Act III (see act3_replay.py)")

    def act4(O):   # sub_0067E890_OutdoorAct4
        if O.lid == 108:
            O.seam_mark()
            T = ints(0x6F22C0, 25)
            for i in range(25):
                O.place((i % 5) * 3, (i // 5) * 3, T[i], -1)
            return
        O.seam_mark()
        O.border_build()
        if O.lid in (104, 105, 106):
            if O.flags & 0x400000: O.place(0, 1, 798, -1)
            if O.flags & 0x800000: O.place(0, 4, 798, -1)
            for t in (1, 2, 3):
                O.border_sub(t, 799)
            if O.lid == 106:
                O.place_random(811)
            aa = {104: 812, 105: 817, 106: 823}[O.lid]; p = {104: 828, 105: 832, 106: 832}[O.lid]
            for d, k in ((aa, 1), (aa + 1, 2), (aa + 2, 2), (aa + 3, 2)):
                for _ in range(k): O.place_random(d)
            if O.lid == 105:
                O.place_random(822)
            for _ in range(4): O.place_random(aa + 4)
            for d, k in ((p, 1), (p + 1, 2), (p + 2, 2), (p + 3, 4)):
                for _ in range(k): O.place_random(d)

    # ---- Act V (sub_0067E600_OutdoorAct5)
    def a5_map(O, main, sub):   # 0x0067E000
        if main in (0x30, 0x31):
            for r in range(10):
                e = A5MAP[5 * r: 5 * r + 5]
                if main == e[0] and e[1] <= sub <= e[2]:
                    return (e[4] if O.lid == 117 else e[3]) - e[1] + sub
        raise Fatal("BarricadeSubDefMap main %d sub %d" % (main, sub))

    def a5_match(O, X, Y, D, F, W):   # 0x0067E080
        m = O.a5_map((W >> 20) & 0x3F, (W >> 8) & 0xFF)
        if m == -5:
            return True
        if m != D:
            return False
        return not (O.cell[Y][X] & 0x400)

    def defat(O, x, y):   # 0x00674120
        return O.defg[y][x] if O.cell[y][x] & 0x200 else 0

    def act5(O):
        cw, ch, lid = O.cw, O.ch, O.lid
        if lid == 110:   # 0x0067E560
            sw = tdiv(PREST[865]["sx"], 8); x = cw - sw; k = 0
            while x >= 0:
                O.place(x, 0, 865 + k, 0); k += 1; x -= sw
                if k > 14:
                    return
            raise Fatal("siege strips do not fit")
        O.seam_mark()
        fam = 4 + (lid == 117)
        # 0x0067DCF0 border ring
        for v in O.ring_list():
            n = v.next
            dx, dy = sgn(n.x - v.x), sgn(n.y - v.y)
            dx2, dy2 = sgn(n.next.x - n.x), sgn(n.next.y - n.y)
            ax, ay = abs(dx), abs(dy)
            tx, ty = n.x & ~1, n.y & ~1
            x, y = v.x & ~1, v.y & ~1
            side = BDEFS5[(fam - 4) + 2 * DIRIDX[(dx, dy)]]
            if not (v.flags & 2):
                while (x, y) != (tx, ty):
                    y += 2 * dy; x += 2 * dx
                    O.place(x, y, side, -1); O.cell[y][x] |= 1
            if v.flags & 1:
                gx = (max(v.x, n.x) - 4 * ax) & ~1; gy = (max(v.y, n.y) - 4 * ay) & ~1
                O.cell[gy][gx] |= 0x400; O.cell[gy + 2 * ay][gx + 2 * ax] |= 0x400
                COV["A5 seam gate marks"] += 1
            k = CORNER[40 + e2(2 * dx) + 9 * (e2(2 * dx2) + 2 * dy2) + 2 * dy]
            if k != -1:
                cd = BDEFS5[(fam - 6) + 2 * k]
                if cd:
                    O.place(tx, ty, cd, -1); O.cell[ty][tx] |= 1
        if lid == 111:
            O.cell[ch - 4][cw - 2] |= 0x400; O.cell[ch - 3][cw - 2] |= 0x400
        # 0x0067DEF0 ravine
        snow = 76 if lid == 117 else 0
        x, y = cw - 2, 0
        while x != 0 or y != ch - 2:
            k = O.defg[y][x] - (881 + snow)
            if not 0 <= k < 12:
                raise Fatal("ravine walk on def %d" % O.defg[y][x])
            O.place(x, y, 893 + snow + k, -1)
            x += 2 * A5STEP[2 * k]; y += 2 * A5STEP[2 * k + 1]
        O.place(cw - 2, 0, 906 + snow, -1)
        O.place(0, ch - 2, 905 + snow, -1)
        # 0x0067DB50 gates
        for x in range(cw):
            if O.cell[0][x] & 0x400: O.place(x, 0, 909, -1); COV["A5 gate 909"] += 1; break
        for x in range(cw):
            if O.cell[ch - 2][x] & 0x400: O.place(x, ch - 2, 908, -1); COV["A5 gate 908"] += 1; break
        for y in range(ch):
            if O.cell[y][0] & 0x400: O.place(0, y, 910, -1); COV["A5 gate 910"] += 1; break
        for y in range(ch):
            if O.cell[y][cw - 2] & 0x400: O.place(cw - 2, y, 907, -1); COV["A5 gate 907"] += 1; break
        # 0x0067DA70 cave entries
        for r in range(3):
            e = A5CAVE[5 * r: 5 * r + 5]
            if e[0] == lid:
                if O.rect[3] < O.rect[2]:
                    O.place(cw - 2 if e[2] else 0, 2, e[4], e[1])
                else:
                    O.place(2, ch - 2 if e[2] else 0, e[3], e[1])
        if lid == 111:   # 0x0067E4B0
            y = ch - tdiv(PREST[880]["sy"], 8)
            O.place(cw - 2, y, 880, -1); O.place(cw - 2, y - 2, 896, -1)
        O.border_sub(12, 0, act5=True)   # 0x0067E0E0
        if lid == 111:   # 0x0067E240 prisons
            n = 0
            for a in range(90):
                if n > 2:
                    break
                x = 2 * O.seed.range(tdiv(cw, 2)); y = 2 * O.seed.range(tdiv(ch, 2))
                d = O.defat(x, y)
                if 915 <= d <= 922:
                    O.place(x, y, d + 16, -1); n += 1
            ox = O.seed.range(tdiv(cw, 2)); oy = O.seed.range(tdiv(ch, 2))
            for r in range(ch):
                if n > 2: break
                for c in range(cw):
                    if n > 2: break
                    y = tmod(r + 2 * oy, ch); x = tmod(c + 2 * ox, cw)
                    d = O.defat(x, y)
                    if 915 <= d <= 922:
                        O.place(x, y, d + 16, -1); n += 1; COV["A5 prison by scan"] += 1
            if n < 3:
                raise Fatal("fewer than 3 prisons")
        for r in range(15):   # 0x0067E160
            e = A5TABLE[7 * r: 7 * r + 7]
            if e[0] != lid:
                continue
            d = e[1] if O.rect[2] < O.rect[3] else e[2]
            res = 0
            for _ in range(e[5]):
                res = O.place_random(d, e[3], 0, 0xF)
            if (e[5] <= 0 or not res) and e[6]:
                raise Fatal("required table row failed")


main()

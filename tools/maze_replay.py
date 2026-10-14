"""Plan 0022 Phase 1 check of the maze reading (docs/findings/drlg/0006-maze.md): replay the maze window
MZ0 -> MZ1 that tools/gdb/drlg-gen.gdb logs, for the level types the logs reach (3 caves, 10 catacombs,
13 Act II sewers), and compare the level seed after the window, the room list order, each room's Def and
forced index, and the room rectangles relative to the bounding box (the window ends after the placement
shift sub_00642590, whose level rectangle the log does not carry).

This is a reading check, not the Phase 2 model: Phase 2 folds it into tools/drlg.py and replaces the oracle.

Usage: python3 -I tools/maze_replay.py <excel-dir> <drlg-gen log>...
"""
import json, os, sys, struct, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drlg import exe_read

EXE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'workspace', 'install', 'app', 'game.exe')
EXCEL = sys.argv[1].rstrip('/') + '/' if len(sys.argv) > 1 else ''
M32 = 0xFFFFFFFF

def tsv(name):
    rows = list(csv.reader(open(EXCEL + name, encoding='latin1'), delimiter='\t'))
    return rows[0], rows[1:]

h, rows = tsv('lvlmaze.txt')
MAZE = {}
for r in rows:
    if len(r) > 7 and r[h.index('Level')].strip().isdigit():
        g = lambda c: int(r[h.index(c)])
        MAZE[g('Level')] = dict(rooms=[g('Rooms'), g('Rooms(N)'), g('Rooms(H)')], sx=g('SizeX'), sy=g('SizeY'), merge=g('Merge'))
h, rows = tsv('levels.txt')
LTYPE = {int(r[h.index('Id')]): int(r[h.index('LevelType')]) for r in rows if len(r) > 5 and r[h.index('Id')].strip().isdigit()}

def tbl(va, n):
    b = exe_read(EXE, va, 16 * n)
    return [struct.unpack_from('<iiii', b, 16 * i) for i in range(n)]

BASE = {3: 0x34, 4: 0x6C, 7: 0xA7, 8: 0xCD, 10: 0x101, 13: 0x12D, 17: 0x19D, 18: 0x1E1, 19: 0x1FD, 22: 0x2F1,
        24: 0x298, 25: 0x2C0, 28: 0x344, 34: 0x422}
THEME_BASE = {3: 0x34, 4: 0x6C, 7: 0xA7, 8: 0xCD, 10: 0x101, 13: 0x12D, 17: 0x19D, 22: 0x2F1, 24: 0x298, 25: 0x2C0}

class Seed:
    def __init__(s, lo, hi): s.lo, s.hi = lo, hi
    def step(s):
        v = s.lo * 0x6AC690C5 + s.hi
        s.lo, s.hi = v & M32, (v >> 32) & M32
        return s.lo

class Room:
    n = 0
    def __init__(R, L):
        R.L = L
        lo = L.seed.step()
        R.seed = Seed(lo, 666); R.seed.step()
        R.x = R.y = 0; R.w = MAZE[L.id]['sx']; R.h = MAZE[L.id]['sy']
        R.d = 0; R.idx = -1; R.lock = False; R.adj = []
        Room.n += 1; R.k = Room.n

class Level:
    def __init__(L, lid, seed, diff=0):
        L.id = lid; L.lt = LTYPE[lid]; L.seed = seed; L.rooms = []; L.diff = diff; L.draws = []

def gap(A, B):
    gx = B.x - A.w - A.x if A.x < B.x else A.x - B.w - B.x
    gy = B.y - A.h - A.y if A.y < B.y else A.y - B.h - B.y
    return gx, gy

def place(L, R, cur, d):
    if d == 0: R.x, R.y = cur.x - cur.w, cur.y
    elif d == 1: R.x, R.y = cur.x, cur.y - cur.h
    elif d == 2: R.x, R.y = cur.x + cur.w, cur.y
    elif d == 3: R.x, R.y = cur.x, cur.y + cur.h
    for (o, _) in cur.adj:
        gx, gy = gap(R, o)
        if gx < 0 and gy < 0: return False
    for P in L.rooms:
        if P is R or P is cur: continue
        gx, gy = gap(R, P)
        if gx < 0 and gy < 0: return False
    return True

def addadj(A, B, d):
    if any(o is B for (o, _) in A.adj): return
    A.adj.insert(0, (B, d))

def connect(A, B, d):
    addadj(A, B, d); addadj(B, A, (d - 2) & 3)

def adjdir(A, B):
    if B.x < A.x:
        if A.x == B.x + B.w: return 0
    elif B.x == A.x + A.w: return 2
    if B.y < A.y:
        if A.y == B.y + B.h: return 1
    elif B.y == A.y + A.h: return 3
    return -1

def defcalc(L, R):
    m = 0
    for (_, d) in R.adj:
        m |= {0: 1, 1: 8, 2: 2, 3: 4}.get(d, 0)
    if L.lt in BASE: v = BASE[L.lt] + m if m else 0
    else: raise NotImplementedError(L.lt)
    if v:
        R.d = v; R.idx = -1; R.lock = False

def merge(L, R):
    if R.lock: return
    mg = MAZE[L.id]['merge']
    for P in list(L.rooms):
        if P is R or P.lock: continue
        gx, gy = gap(R, P)
        if gx < 1 and gy < 1 and gx != gy:
            if any(o is P for (o, _) in R.adj): continue
            lo = P.seed.step()
            if lo % 1000 < mg:
                d = adjdir(P, R)
                if d != -1:
                    connect(P, R, d); defcalc(L, P)

def free(L, R):
    for (o, _) in R.adj:
        o.adj = [(x, d) for (x, d) in o.adj if x is not R]
    if R in L.rooms: L.rooms.remove(R)

def grow(L, cur, d, do_merge=True):
    R = Room(L)
    if not place(L, R, cur, d): return None
    connect(cur, R, d)
    if do_merge: merge(L, R)
    L.rooms.insert(0, R)
    defcalc(L, cur); defcalc(L, R)
    return R

def attach_locked(L, cur, d, dfn, idx, recalc):   # 0x00670DE0
    R = Room(L)
    if not place(L, R, cur, d): return None
    connect(cur, R, d); L.rooms.insert(0, R)
    if recalc: defcalc(L, cur)
    R.lock = True; R.d = dfn; R.idx = idx
    return R

def rng_range(s, n):
    if n < 1: return 0
    lo = s.step()
    return lo & (n - 1) if n & (n - 1) == 0 else lo % n

def growth(L):                                     # 0x00671210
    tgt = MAZE[L.id]['rooms'][L.diff]
    while len(L.rooms) < tgt:
        k = rng_range(L.seed, len(L.rooms))
        P = L.rooms[k]
        d = P.seed.step() & 3
        if not P.lock: grow(L, P, d)

def special(L, rec, rot=None):                     # 0x006724E0
    match, nd, ni, d = rec
    for R in L.rooms:
        if not R.lock and R.d == match:
            R.lock = True; R.d = nd; R.idx = ni; break
    else:
        for P in L.rooms:                          # 0x00670EB0
            if P.lock: continue
            R = Room(L)
            if place(L, R, P, d):
                connect(P, R, d); L.rooms.insert(0, R); defcalc(L, P)
                R.lock = True; R.d = nd; R.idx = ni
                break
    if rot is not None: rot[0] = (rot[0] + 1) & 3

def T(va, rot): return tbl(va + 16 * rot[0], 1)[0]

def ring(L, n):                                    # 0x00670F60
    cur = L.rooms[-1]; first = cur
    for d, cnt in ((1, n - 1), (0, n - 1), (3, n - 1), (2, n - 2)):
        for _ in range(cnt): cur = grow(L, cur, d)
    connect(cur, first, 2); defcalc(L, cur); defcalc(L, first)

def probe(L, R, d):                                # 0x00672340
    if R.lock or any(dd == d for (_, dd) in R.adj): return False
    T_ = Room(L)
    if not place(L, T_, R, d): return False
    connect(R, T_, d); L.rooms.insert(0, T_); defcalc(L, T_)
    free(L, T_)
    return True

def finder(L, d, key, better):
    best = None
    for R in list(L.rooms):
        if best is None or better(key(R), key(best)):
            if probe(L, R, d): best = R
    return best

def themes(L):                                     # 0x006735F0
    if L.lt not in THEME_BASE or L.id == 8: return
    base = THEME_BASE[L.lt]
    perm = list(range(15))
    s = L.seed.step() % 15
    want = max(2, len(L.rooms) // 5 + 1)
    tries = len(L.rooms) * 2
    for _ in range(15):
        a = L.seed.step() % 15; b = L.seed.step() % 15
        perm[a], perm[b] = perm[b], perm[a]
    while want and tries:
        dv = base + perm[s]
        for R in L.rooms:
            if not R.lock and R.d == dv:
                R.lock = True; want -= 1; R.d = dv + 15; R.idx = -1; break
        tries -= 1; s = (s + 1) % 15

def build(L):
    R0 = Room.__new__(Room)                        # the first room exists before MZ0
    R0.L = L; R0.seed = Seed(0, 0); R0.x = R0.y = 0; R0.w = MAZE[L.id]['sx']; R0.h = MAZE[L.id]['sy']
    R0.d = 0; R0.idx = -1; R0.lock = False; R0.adj = []; R0.k = 0
    L.rooms.insert(0, R0)
    return R0

def run(L, first_seed):
    R0 = build(L); R0.seed = first_seed
    lt, lid = L.lt, L.id
    if lt == 3:
        growth(L)
        rot = [L.seed.step() & 3]
        special(L, T(0x6ef8a8, rot), rot)
        special(L, T(0x6ef8e8 if lid == 8 else 0x6ef928, rot), rot)
        if lid == 9: special(L, T(0x6ef968, rot), rot)
        if lid == 10: special(L, T(0x6ef9a8, rot), rot)
    elif lt == 10:
        if lid == 34:
            for d in (1, 2, 3, 0): grow(L, R0, d)
            R0.d, R0.lock, R0.idx = 0x122, True, -1
        else:
            b = L.seed.step() & 1
            if b == 0:
                grow(L, R0, 1); grow(L, R0, 3); R0.d = 0x121
            else:
                grow(L, R0, 0); grow(L, R0, 2); R0.d = 0x120
            R0.lock = True; R0.idx = -1
        growth(L)
        rot = [L.seed.step() & 3]
        special(L, T(0x6efc68, rot), rot)
        if lid == 35: special(L, T(0x6efca8, rot), rot)
    elif lt == 13:
        ring(L, 2); growth(L)
        a = (L.seed.step() & 1) * 2 | 1
        rot = [L.seed.step() & 3]
        if lid == 47:
            P = finder(L, 1, lambda R: R.y, lambda a_, b_: a_ < b_)
            R1 = grow(L, P, 1); R2 = grow(L, R1, 1)
            attach_locked(L, R2, 0, 0x14d, 0, True)
            P = finder(L, 2, lambda R: R.x, lambda a_, b_: a_ > b_)
            R1 = grow(L, P, 2); R2 = grow(L, R1, 2)
            dock = attach_locked(L, R2, a, 0x150, 0, True)
            R = Room(L)
            if place(L, R, dock, a):
                connect(dock, R, a); L.rooms.insert(0, R); defcalc(L, R)
            special(L, T(0x6efd28, rot), rot)
        elif lid == 48:
            for t in (0x6efce8, 0x6efd68, 0x6efd28): special(L, T(t, rot), rot)
        elif lid == 49:
            for t in (0x6efce8, 0x6efda8): special(L, T(t, rot), rot)
        elif lid == 65:
            for t in (0x6efce8, 0x6efde8): special(L, T(t, rot), rot)
    else:
        raise NotImplementedError(lt)
    themes(L)

def parse(path):
    out = []
    cur = None
    for line in open(path, errors='replace'):
        if line.startswith('MZ0 '):
            cur = json.loads(line[4:])
        elif line.startswith('MZ1 ') and cur:
            out.append((cur, json.loads(line[4:]))); cur = None
    return out

def first_room_seed(path, mz0):
    """The first room's seed: the RL/RC just before MZ0 gives the level seed before its draw."""
    prev = None
    for line in open(path, errors='replace'):
        if line.startswith('RC '):
            prev = json.loads(line[3:])
        if line.startswith('MZ0 ') and json.loads(line[4:]) == mz0:
            break
    lo, hi = (int(x, 16) for x in prev['seed'].split(':'))
    s = Seed(lo, hi); v = s.step()
    r = Seed(v, 666); r.step()
    return r

def main(paths):
    tot = bad = 0
    for p in paths:
        for mz0, mz1 in parse(p):
            lid = mz0['id']
            lo, hi = (int(x, 16) for x in mz0['seed'].split(':'))
            L = Level(lid, Seed(lo, hi))
            try:
                run(L, first_room_seed(p, mz0))
            except NotImplementedError as e:
                print(p.split('/')[-1], lid, 'skip type', e); continue
            got = [(R.x, R.y, R.w, R.h, R.d, R.idx) for R in L.rooms]
            exp = [tuple(r[2:8]) for r in mz1['rooms']]
            # relative positions: shift so the bounding boxes' minima coincide (0x00642590)
            def norm(lst):
                mx = min(t[0] for t in lst); my = min(t[1] for t in lst)
                return [(t[0] - mx, t[1] - my) + tuple(t[2:]) for t in lst]
            seed_ok = '%08x:%08x' % (L.seed.lo, L.seed.hi) == mz1['seed']
            ok = seed_ok and norm(got) == norm(exp)
            tot += 1; bad += not ok
            print(p.split('/')[-1], 'level', lid, 'rooms', len(exp), 'seed', 'ok' if seed_ok else 'MISMATCH', 'list', 'ok' if norm(got) == norm(exp) else 'MISMATCH')
            if not ok:
                print('  got', norm(got)); print('  exp', norm(exp))
    print('windows', tot, 'mismatches', bad)

if __name__ == '__main__':
    main(sys.argv[2:])

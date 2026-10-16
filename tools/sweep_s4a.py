"""Plan 0038 batch S4a: second sources over the kept DRLG and objects logs (static, no game run).

Usage:
  python3 -I tools/sweep_s4a.py <check> [--logs DIR] [-v]
  python3 -I tools/sweep_s4a.py all

Checks (the inventory rows each serves are in its docstring): adj barrier bits dispatch expansion flood kill l27 lc1
lnks logic lsr ltype maze nww objects odg orpath outroom pcopies pflags pick placefar punits r0 roomk tl warpunit wgen.
Unit tests of the pure helpers: python3 -I tools/test_sweep_s4a.py.

Each check re-reads logs that an earlier run already recorded (the run ids are in the check's docstring) and prints
one `S4A <check> key=value ...` line of counts, plus a few detail lines. A check exits 1 when an observation
contradicts the claim it tests (a `bad=` count above 0); a claim with no stock case shows up as a zero count, never as a
failure. The checks import the existing models (tools/drlg.py, tools/collision.py, tools/objects.py) and only add
counters around them: no existing checker is changed, and each still runs its own checks (0 mismatches required).
The batch record is the "Plan 0038 batch S4a" section of each finding (docs/findings/drlg/*, objects/0001) and the
dated addenda in docs/findings/drlg/experiments.md and docs/findings/objects/experiments.md.

Stdlib only. Read-only.
"""
import base64
import collections
import contextlib
import glob
import io
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
LOGS = os.path.join(ROOT, "workspace", "logs")
DATA = os.path.join(ROOT, "workspace", "merged")
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
EXCEL = os.path.join(DATA, "data", "global", "excel")


# ----------------------------------------------------------------------------------------------------------------- logs
def log_set(name, logs=None):
    """The log lists of the runs this batch re-reads (paths as the run records name them)."""
    L = logs or LOGS
    g = lambda pat: sorted(glob.glob(os.path.join(L, pat)))     # noqa: E731
    sets = {
        "roomk": [os.path.join(L, "roomk-%s.log" % s) for s in
                  ("12345-town", "777-town", "12345-bloodmoor", "12345-act2", "1-catacombs", "1-catacombs-b")],
        "gen": [os.path.join(L, "gen-%s.log" % s) for s in
                ("12345-town", "777-town", "12345-bloodmoor", "12345-act2", "12345-act4", "1-catacombs-owner")],
        "preset": [p for p in g("preset-*.log") if "test" not in p],
        "collision": g("collision-s[1-7]-*.log"),
        "maze": g("maze/maze-s*.log"),
        "outdoor": g("outdoor/od-s*.log") + g("outdoor/od-k1-*.log"),
        "acts35": g("acts35/a35-s*.log"),
        "objects": [p for p in g("objects-s[0-9]*.log") if not os.path.basename(p).startswith("objects-s1-")],
        "quests": g("quests-s*.log"),
    }
    sets["cow"] = g("cow-3301-normal.log")
    if name == "cluster":
        # the logs of the drlg and objects run records this batch writes addenda to (dev and smoke logs excluded)
        out = []
        for k in ("roomk", "gen", "preset", "collision", "maze", "outdoor", "acts35", "cow", "objects"):
            out += sets[k]
        return out
    return sets[name]


def events(path, tags):
    """(tag, dict, line) for the JSON lines of the given tags."""
    for ln, line in enumerate(open(path, errors="replace"), 1):
        tag, _, rest = line.partition(" ")
        if tag in tags:
            try:
                yield tag, json.loads(rest), ln
            except ValueError:
                continue


def tagged(paths, tag):
    """The logs among paths that hold at least one line starting with tag."""
    out = []
    pre = tag + " "
    for p in paths:
        with open(p, errors="replace") as f:
            if any(line.startswith(pre) for line in f):
                out.append(p)
    return out


def unz(s):
    return json.loads(zlib.decompress(base64.b64decode(s)))


def seed_t(s):
    a, b = s.split(":")
    return int(a, 16), int(b, 16)


@contextlib.contextmanager
def quiet():
    """Run an existing checker with its own report captured (its mismatch count is returned by the caller)."""
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        yield buf
    finally:
        sys.stdout = old


class Report:
    def __init__(self, name):
        self.name = name
        self.c = collections.Counter()
        self.notes = []

    def __getitem__(self, k):
        return self.c[k]

    def add(self, k, n=1):
        self.c[k] += n

    def note(self, s):
        self.notes.append(s)

    def done(self):
        keys = " ".join("%s=%d" % (k, self.c[k]) for k in sorted(self.c))
        print("S4A %s %s" % (self.name, keys))
        for s in self.notes:
            print("  " + s)
        return 1 if self.c["bad"] else 0


def excel_rows(name):
    d = open(os.path.join(EXCEL, name + ".bin"), "rb").read()
    n = struct.unpack_from("<I", d)[0]
    size = (len(d) - 4) // n
    return [d[4 + i * size: 4 + (i + 1) * size] for i in range(n)]


def levels_txt():
    import drlg
    drlg.load_links(EXCEL, EXE)
    return drlg.LV


# ------------------------------------------------------------------------------------------------- simple log scans
def chk_ltype(a):
    """README row 9 (spec L317), room-tiles row 18 (L586): LevelCreate copies Levels.LevelType to level +0x1C0 and
    nothing else writes it. Every LC0 (DRLG_LevelCreate, run:2026-10-12-drlg-gen and later gen-family loggers) and every
    RRESEED (DrlgRoomReseed, run:2026-10-11-drlg-roomk family) logs the level's +0x1C0; compare with Levels.LevelType."""
    R = Report("ltype")
    LV = levels_txt()
    paths = log_set("cluster", a.logs)
    seen_lv = set()
    for p in paths:
        for tag, d, ln in events(p, ("LC0", "LI0", "RRESEED")):
            if tag in ("LC0", "LI0"):
                lid, lt = d["id"], d["ltype"]
            else:
                lid, lt = d["level"], d.get("ltype")
                if lt is None:
                    R.add("RRESEED without the level type (early logger)")
                    continue
            if lid not in LV:
                R.add("unknown level")
                continue
            R.add(tag)
            seen_lv.add(lid)
            if LV[lid]["ltype"] != lt:
                R.add("bad")
                R.note("%s:%d %s level %d +0x1C0 %d, Levels.LevelType %d" % (os.path.basename(p), ln, tag, lid, lt,
                                                                             LV[lid]["ltype"]))
    R.add("levels", len(seen_lv))
    R.add("logs", len(paths))
    return R.done()


def chk_lsr(a):
    """README rows 7, 14 (spec L279, L379): LvlSubRoll returns 0 with no draw when SubType or SubTheme is -1. Every
    LSR/LSRX pair (sub_006706A0_LvlSubRoll entry and exit, drlg-gen.py; run:2026-10-12-drlg-gen family): with -1 in
    either input, the room seed is unchanged and the mask 0; otherwise one draw per record of the type (the gen checker
    models those). Also the two halves with no stock case: a SubType with no LvlSub record, and a SubTheme past the
    five Prob columns, counted over levels.txt."""
    R = Report("lsr")
    LV = levels_txt()
    paths = tagged(log_set("cluster", a.logs), "LSR")
    for p in paths:
        pend = {}
        for tag, d, ln in events(p, ("LSR", "LSRX")):
            if tag == "LSR":
                pend[d["room"]] = d
                continue
            d0 = pend.pop(d["room"], None)
            if d0 is None:
                continue
            neg = d0["stype"] == -1 or d0["theme"] == -1
            same = d0["seed"] == d["seed"]
            if neg:
                R.add("calls with -1 (%s)" % ("both" if d0["stype"] == d0["theme"] == -1 else
                                             "stype" if d0["stype"] == -1 else "theme"))
                if not same or d["mask"] != 0:
                    R.add("bad")
                    R.note("%s:%d LSR with -1 drew or set a mask" % (os.path.basename(p), ln))
            else:
                R.add("calls with a type and a theme")
                R.add("draws on those calls" if not same else "no draw on a typed call")
    R.add("logs", len(paths))
    # the data halves: SubType values with no record, SubTheme values above 4
    sub_types = {struct.unpack_from("<i", r, 0)[0] for r in excel_rows("lvlsub")}
    h, rows = _tsv("levels.txt")
    st = [int(r[h.index("SubType")]) for r in rows if r[h.index("Id")].strip().isdigit() and r[h.index("SubType")].strip()]
    th = [int(r[h.index("SubTheme")]) for r in rows if r[h.index("Id")].strip().isdigit() and r[h.index("SubTheme")].strip()]
    R.add("levels with a SubType and no LvlSub record", sum(1 for t in st if t >= 0 and t not in sub_types))
    R.add("levels with SubTheme above 4", sum(1 for t in th if t > 4))
    R.add("levels with SubTheme below -1", sum(1 for t in th if t < -1))
    return R.done()


def _tsv(name):
    import csv
    rows = list(csv.reader(open(os.path.join(EXCEL, name), encoding="latin1"), delimiter="\t"))
    return rows[0], rows[1:]


def chk_expansion(a):
    """README row 12 (spec L341): neither LvlPrest lookup tests Expansion. In the classic sessions of
    run:2026-10-15-drlg-outdoor (od-s3, s5, s8, s10: status byte 0), count the PresetInstanceCreate (PIC) and
    PresetRoomsCreate (PRC) calls on records whose Expansion (+0x20) is 1."""
    R = Report("expansion")
    exp = [struct.unpack_from("<i", r, 0x20)[0] for r in excel_rows("lvlprest")]
    lvl = [struct.unpack_from("<i", r, 0x04)[0] for r in excel_rows("lvlprest")]
    paths = [p for p in log_set("outdoor", a.logs) if "classic" in os.path.basename(p)]
    defs = collections.Counter()
    for p in paths:
        for tag, d, ln in events(p, ("PIC", "PRC")):
            R.add("%s calls" % tag)
            if exp[d["def"]] == 1:
                R.add("%s on an Expansion-1 record" % tag)
                defs[(d["def"], lvl[d["def"]])] += 1
    R.add("classic logs", len(paths))
    R.add("Expansion-1 records in lvlprest", sum(exp))
    R.add("Expansion-1 records hit (distinct Def)", len(defs))
    if defs:
        R.note("Def (LevelId): count  " + ", ".join("%d (%d): %d" % (k[0], k[1], v) for k, v in sorted(defs.items())[:24]))
    return R.done()


def chk_lnks(a):
    """maze row 16 (spec L563): the Vis pairs 27<->28 and 107<->108 have Warp -1, so no warp pairs them; the maze
    placement of 28 and 107 joins them through a level-adjacency node (the MZA inputs). LNKS lines (the act's
    LevelLinks list after ActLinkInit, run:2026-10-15-drlg-maze and run:2026-10-15-drlg-outdoor loggers) and the WPR
    pairings of the same logs."""
    R = Report("lnks")
    paths = tagged(log_set("maze", a.logs) + log_set("outdoor", a.logs) + log_set("acts35", a.logs), "LNKS")
    pairs = {(27, 28), (28, 27), (107, 108), (108, 107)}
    for p in paths:
        for tag, d, ln in events(p, ("LNKS", "WPR", "MZA")):
            if tag == "LNKS":
                links = {lv: (vis, warp) for lv, vis, warp in d["links"]}
                for s, t in pairs:
                    if s not in links:
                        continue
                    vis, warp = links[s]
                    if t not in vis:
                        R.add("bad")
                        R.note("%s:%d level %d: Vis has no %d" % (os.path.basename(p), ln, s, t))
                        continue
                    k = vis.index(t)
                    R.add("LevelLinks %d -> %d seen" % (s, t))
                    if warp[k] != -1:
                        R.add("bad")
                        R.note("%s:%d level %d slot %d -> %d Warp %d" % (os.path.basename(p), ln, s, k, t, warp[k]))
            elif tag == "WPR":
                R.add("WPR pairings")
                if (d["slv"], d["dlv"]) in pairs:
                    R.add("bad")
                    R.note("%s:%d warp pairing %d -> %d" % (os.path.basename(p), ln, d["slv"], d["dlv"]))
            elif tag == "MZA" and d["id"] in (28, 107):
                R.add("maze windows placed against the neighbour level (%d)" % d["id"])
    R.add("logs", len(paths))
    LV = levels_txt()
    for s, t in sorted(pairs):
        k = LV[s]["vis"].index(t) if t in LV[s]["vis"] else None
        if k is None or LV[s]["warp"][k] != -1:
            R.add("bad")
            R.note("levels.txt %d -> %d: slot %s warp %s" % (s, t, k, k is not None and LV[s]["warp"][k]))
        else:
            R.add("levels.txt Vis pairs with Warp -1")
    return R.done()


def chk_tl(a):
    """collision row 47 (spec L700): TILE_GetFlags16 reads the tile record's +0x06 as a u16. The TL lines
    (tools/gdb/collision.py, run:2026-10-14-collision and run:2026-10-15-objects) log the in-memory record's u16 at +0x06;
    the DT1 file's tile header holds sound (+0x06) and animated (+0x07). Every TL record, every log."""
    R = Report("tl")
    import dt1 as dt1mod
    files = {}
    paths = tagged(log_set("cluster", a.logs), "TL")
    seen = set()
    for p in paths:
        for tag, d, ln in events(p, ("TL",)):
            fp = os.path.join(DATA, d["f"].replace("\\", "/").lower())
            if fp not in files:
                files[fp] = dt1mod.parse(open(fp, "rb").read())["tiles"]
            t = files[fp]
            i = d["i"]
            if i is None or not 0 <= i < len(t):
                R.add("records without a file index (not compared)")
                continue
            R.add("records")
            seen.add((d["f"].lower(), i))
            w = t[i]["sound"] | t[i]["animated"] << 8
            if w != d["w6"]:
                R.add("bad")
                R.note("%s:%d %s #%d: memory +0x06 %#x, file %#x" % (os.path.basename(p), ln, d["f"], i, d["w6"], w))
            if d["w6"] & 2:
                R.add("records with flags16 bit 1 (the SpawnPosOnTile bit)")
            if d["w6"] & 0x100:
                R.add("records with flags16 0x100 (animated)")
    R.add("distinct tiles", len(seen))
    R.add("DT1 files", len(files))
    R.add("logs", len(paths))
    return R.done()


# ------------------------------------------------------------------------------------------- tools/drlg.py gen runs
GEN_SETS = ("gen", "maze", "outdoor", "acts35")


def gen_logs(a, sets=GEN_SETS):
    out = []
    for s in sets:
        out += log_set(s, a.logs)
    return out


def run_gen(paths):
    """tools/drlg.py gen on paths, as cmd_gen runs it (GenModel, then the roomk passes in logs with OD0 and LSUB lines);
    returns (GenModel, Model, mismatches). The checker's own report is captured."""
    import drlg
    with quiet():
        m = drlg.GenModel(drlg.Data(DATA, EXE), False, False, drlg.PresetUnitData(DATA, EXE))
        rk = drlg.Model(drlg.Data(DATA, EXE), False)
        for p in paths:
            m.run(p)
            if m.prep_pred:
                drlg.run_log(rk, p, m.prep_pred)
    return m, rk, m.fail + rk.fail


@contextlib.contextmanager
def patched(obj, name, fn):
    old = getattr(obj, name)
    setattr(obj, name, fn)
    try:
        yield old
    finally:
        setattr(obj, name, old)


def chk_lc1(a):
    """maze row 1 (spec L30), outdoor row 1 (L32): MazeLevelCreate and OutdoorLevelCreate make no draw. LC0 logs the seed
    after DRLG_LevelCreate's Init(base + id) and LC1 the seed after the create dispatch (run:2026-10-12-drlg-gen and every
    later gen-family logger); for DrlgType 1 and 3 they must be equal. DrlgType 2 (PresetLevelCreate's file draw) is the
    control."""
    R = Report("lc1")
    import drlg
    drlg.load_links(EXCEL, EXE)
    paths = tagged(log_set("cluster", a.logs), "LC1")
    for p in paths:
        pend = {}
        for tag, d, ln in events(p, ("LC0", "LC1")):
            if tag == "LC0":
                pend[d["level"]] = d
                lo, hi = seed_t(d["seed"])
                if lo != (d["base"] + d["id"]) & 0xFFFFFFFF or hi != 666:
                    R.add("bad")
                    R.note("%s:%d LC0 seed is not Init(base + id)" % (os.path.basename(p), ln))
                continue
            d0 = pend.pop(d["level"], None)
            if d0 is None:
                continue
            t = d0["drlg"]
            same = d0["seed"] == d["seed"]
            R.add("creations DrlgType %d (%s)" % (t, "no draw" if same else "draw"))
            if t in (1, 3) and not same:
                R.add("bad")
                R.note("%s:%d level %d DrlgType %d: create drew" % (os.path.basename(p), ln, d["id"], t))
            if t == 1 and d["id"] not in drlg.LVLMAZE:
                R.add("bad")
                R.note("maze level %d has no LvlMaze row" % d["id"])
    R.add("logs", len(paths))
    return R.done()


def chk_odg(a):
    """outdoor row 6 (spec L240): no outdoor generator writes cell bits 20-25. The ODG line (tools/gdb/drlg-outdoor.py at
    OutdoorRoomsCreate, run:2026-10-15-drlg-outdoor) dumps the final cell grid (+0x2C) of every window."""
    R = Report("odg")
    paths = tagged(log_set("cluster", a.logs), "ODG")
    lv = set()
    for p in paths:
        for tag, d, ln in events(p, ("ODG",)):
            R.add("windows")
            lv.add(d["id"])
            cells = [c for row in d["cells"] for c in row] if d["cells"] and isinstance(d["cells"][0], list) else d["cells"]
            R.add("cells", len(cells))
            n = sum(1 for c in cells if c & 0x03F00000)
            if n:
                R.add("bad")
                R.note("%s:%d level %d: %d cells with bits 20-25" % (os.path.basename(p), ln, d["id"], n))
            g0 = [c for row in d["grid0"] for c in row] if d["grid0"] and isinstance(d["grid0"][0], list) else d["grid0"]
            R.add("grid0 cells with a warp-slot bit 0x10 << k", sum(1 for c in g0 if c & 0xFF0))
    R.add("levels", len(lv))
    R.add("logs", len(paths))
    return R.done()


def chk_maze(a):
    """maze rows 7, 8 (spec L299, L314): MazeSpecialAttach spends one RoomCreate level draw per candidate tried, and a
    candidate whose placement fails is freed and the walk goes on. tools/drlg.py gen over the maze windows of
    run:2026-10-15-drlg-maze (MZD: every level-seed step of the window, one by one), run:2026-10-12-drlg-gen,
    run:2026-10-15-drlg-outdoor and run:2026-10-15-acts-3-5, counting the attaches by failed candidates before the one that
    took the special, and the attaches no room took."""
    R = Report("maze")
    import drlg
    st = collections.Counter()

    def special(M, va, rot=None):
        match, nd, ni, d = drlg.mz_special(va)
        for Rr in M.L.rooms:
            if not Rr.lock and Rr.d == match:
                Rr.lock, Rr.d, Rr.idx = True, nd, ni
                st["specials by match (no draw)"] += 1
                break
        else:
            fails = 0
            for P in list(M.L.rooms):
                if P.lock:
                    continue
                Rn = drlg.MRoom(M)
                if M.place(Rn, P, d):
                    M.connect(P, Rn, d)
                    M.link(Rn)
                    M.defcalc(P)
                    Rn.lock, Rn.d, Rn.idx = True, nd, ni
                    st["attaches placed"] += 1
                    if fails:
                        st["attaches whose first candidate(s) failed"] += 1
                        st["failed candidates (one level draw each)"] += fails
                    break
                fails += 1
            else:
                drlg.COV["maze special: no room took it"] += 1
                st["attaches no room took"] += 1
        if rot is not None:
            rot[0] = (rot[0] + 1) & 3

    with patched(drlg.Maze, "special", special):
        m, rk, bad = run_gen(gen_logs(a))
    for k, v in st.items():
        R.add(k, v)
    R.add("MZD draws checked", m.cov.get("maze window level-seed draws checked one by one (MZD)", 0))
    R.add("maze windows", sum(v for k, v in m.cov.items() if k.startswith("maze windows modelled: difficulty")))
    R.add("checks", m.checks + rk.checks)
    R.add("bad", bad)
    return R.done()


def chk_r0(a):
    """maze row 3 (spec L135): R0's centred position cancels out. The maze model is run with R0 moved by an offset
    (several offsets); every window must still give the same absolute room rects, seeds and MZD draws. Negative
    control: moving the second room instead must break the checks."""
    R = Report("r0")
    import drlg
    paths = gen_logs(a, ("gen", "maze"))
    orig = drlg.Maze.link
    for dx, dy in ((0, 0), (37, -53), (-1000, 999), (4096, 4096)):
        def link(M, Rr, dx=dx, dy=dy):
            n = getattr(M, "_s4a_n", 0)
            M._s4a_n = n + 1
            if n == 0:
                Rr.x += dx
                Rr.y += dy
            return orig(M, Rr)
        with patched(drlg.Maze, "link", link):
            m, rk, bad = run_gen(paths)
        R.add("windows run with R0 moved by (%d, %d)" % (dx, dy),
              sum(v for k, v in m.cov.items() if k.startswith("maze windows modelled: difficulty")))
        R.add("bad", bad)

    def link2(M, Rr):
        n = getattr(M, "_s4a_n", 0)
        M._s4a_n = n + 1
        if n == 1:
            Rr.x += 1
        return orig(M, Rr)
    with patched(drlg.Maze, "link", link2):
        m, rk, bad = run_gen(paths)
    R.add("negative control: second room moved by one tile, mismatches", bad)
    if not bad:
        R.add("bad")
        R.note("the negative control did not fail")
    return R.done()


def chk_wgen(a):
    """warps row 13 (spec L367): the DS1 scan's warp-slot and waypoint bits hold for presets placed by every generator.
    The preset room flags at LevelWarpPointsBuild (LWP, run:2026-10-15-drlg-maze loggers) that tools/drlg.py gen predicts
    from the DS1 scan, split by the generator that placed the preset (the level's DrlgType)."""
    R = Report("wgen")
    import drlg
    orig = drlg.GenModel.points_for

    def points_for(self, path, lid, rooms, diff, check, g0=None):
        if check:
            for r in rooms:
                ptr, typ, x, y, w, h, lf = r
                if typ == 2 and self.room_inst.get(ptr) is not None:
                    t = drlg.LV[lid]["drlg"]
                    gen = {1: "maze rooms", 2: "preset levels", 3: "outdoor embedded presets"}[t]
                    pf = self.room_flags(path, lid, r)
                    R.add("%s: preset rooms predicted" % gen)
                    prc, single = self.room_inst[ptr]
                    g = self.warp_grid(prc, single).get((0, 0) if single else ((x - prc["prect"][0]) // 8,
                                                                               (y - prc["prect"][1]) // 8), 0)
                    if g & 0xFF0:
                        R.add("%s: rooms with a warp-slot bit from the DS1 scan" % gen)
                    if g & 0x30000:
                        R.add("%s: rooms with the waypoint bits from the DS1 scan" % gen)
                    if pf != lf & 0x30FF0:
                        R.add("flags differ (the checker reports them)")
        return orig(self, path, lid, rooms, diff, check, g0)

    with patched(drlg.GenModel, "points_for", points_for):
        m, rk, bad = run_gen(gen_logs(a))
    R.add("bad", bad)
    return R.done()


def chk_adj(a):
    """outdoor row 8 (spec L286): LevelAdjInsert compares a new node with the head only while the list holds one node.
    Counts the inserts into lists of two or more nodes where the new node sorts before the head (the quirk decides the
    order), in the act link model of tools/drlg.py gen over the outdoor-window logs; then the negative control: the
    same run with a full compare."""
    R = Report("adj")
    import drlg
    orig = drlg.adj_insert

    def quirk(lst, n):
        if len(lst) >= 2 and drlg.adj_less(n, lst[0]):
            R.add("inserts where the head is skipped and the new node sorts before it")
            if n["side"] == lst[0]["side"]:
                R.add("... of those, on the head's side (where the order is read)")
        if len(lst) >= 2:
            R.add("inserts into a list of two or more")
        elif len(lst) == 1:
            R.add("inserts into a list of one")
        return orig(lst, n)

    def full(lst, n):
        for k in range(len(lst)):
            if drlg.adj_less(n, lst[k]):
                lst.insert(k, n)
                return
        lst.append(n)

    paths = gen_logs(a, ("outdoor",))
    with patched(drlg, "adj_insert", quirk):
        m, rk, bad = run_gen(paths)
    R.add("outdoor windows", sum(v for k, v in m.cov.items() if k.startswith("outdoor windows modelled: act")))
    R.add("bad", bad)
    with patched(drlg, "adj_insert", full):
        m, rk, bad2 = run_gen(paths)
    R.add("negative control (full compare): mismatches", bad2)
    return R.done()


def chk_placefar(a):
    """outdoor row 10 (spec L359): PlaceFar's inclusive bounds visit row oy and column ox twice. The level-2 cave
    placement (the only caller) in tools/drlg.py gen over run:2026-10-15-drlg-outdoor, with the bounds made exclusive:
    whether any window changes, and how many PlaceFar calls had a tie for the best distance."""
    R = Report("placefar")
    import drlg

    def place_far(O, rect, d, idx, pad, sides, excl=False):
        W, H = O.cw - 2, O.ch - 2
        ox = O.seed.range(W)
        oy = O.seed.range(H)
        tx = rect[0] + drlg.tdiv(rect[2], 2)
        ty = rect[1] + drlg.tdiv(rect[3], 2)
        best, bx, by, ties, seen = 0, -1, -1, 0, collections.Counter()
        for r in range(H if excl else H + 1):
            y = drlg.tmod(r + oy, H) + 1
            for c in range(W if excl else W + 1):
                x = drlg.tmod(c + ox, W) + 1
                if O.fits(x, y, d, pad, sides):
                    a_ = abs(8 * x + O.rect[0] + 4 - tx)
                    b_ = abs(8 * y + O.rect[1] + 4 - ty)
                    dd = drlg.tdiv(b_ + 2 * a_ if a_ > b_ else a_ + 2 * b_, 2)
                    seen[dd] += 1
                    if dd > best:
                        best, bx, by = dd, x, y
        R.add("PlaceFar calls")
        if seen and seen[max(seen)] > (2 if not excl else 1):
            R.add("calls with a tie for the best distance")
        if bx != -1 and by != -1:
            O.place(bx, by, d, idx, 0)
            return 1
        return 0

    paths = gen_logs(a, ("outdoor",))
    with patched(drlg.Outdoor, "place_far", place_far):
        m, rk, bad = run_gen(paths)
    R.add("bad", bad)
    with patched(drlg.Outdoor, "place_far", lambda O, *x: place_far(O, *x, excl=True)):
        m, rk, bad2 = run_gen(paths)
    R.add("exclusive bounds: mismatches", bad2)
    return R.done()

# ----------------------------------------------------------------------------------------------- logic regions (drlg/0005 § 7)
def rect_gap_test(A, B, t):
    """sub_0066B860_RectGapTest(A, B, t): 0 iff both gaps are below t (sub_0066B800_RectGap)."""
    gx = (B[0] - A[2] - A[0]) if A[0] < B[0] else (A[0] - B[2] - B[0])
    gy = (B[1] - A[3] - A[1]) if A[1] < B[1] else (A[1] - B[3] - B[1])
    return 0 if (gx < t and gy < t) else 1


def contains_incl(rc, x, y):
    """sub_0066B9D0_RectContainsIncl: x0 <= x <= x0 + w, y0 <= y <= y0 + h."""
    return rc[0] <= x <= rc[0] + rc[2] and rc[1] <= y <= rc[1] + rc[3]


class LogicRoom:
    """A DRLG room's logic record as the model keeps it: single (LogicBoxSingle: one box, id 1) or the box list of the
    flood (LG1), each box {id, kind, r0}."""

    def __init__(self, rect, level, nb, single, boxes=None):
        self.rect, self.level, self.nb, self.single = rect, level, nb, single
        self.boxes = boxes or []

    def box_at(self, x, y):
        if self.single:
            return self.boxes[0]
        for b in self.boxes:
            r0 = b["r0"]
            if r0[0] <= x < r0[2] and r0[1] <= y < r0[3]:
                return b
        return None


def relabel(rooms, r, old, new, depth=0):
    """LOGIC_RegionRelabel(room r, old id, new id): rename r's boxes with id old (a single-box record is skipped); when
    any was renamed, recurse into every same-level room of r's near list other than r."""
    L = rooms.get(r)
    if L is None or L.single:
        return 0
    hit = 0
    for b in L.boxes:
        if b["id"] == old:
            b["id"] = new
            hit += 1
    if hit:
        for q in L.nb:
            Q = rooms.get(q)
            if q != r and Q is not None and Q.level == L.level:
                hit += relabel(rooms, q, old, new, depth + 1)
    return hit


def edge_merge(rooms, r, n, x, y, st):
    """LOGIC_EdgeMerge(x, y, R = r, N = n), from the disassembly of 0x0066CF60."""
    R, N = rooms[r], rooms[n]
    if not contains_incl(N.rect, x, y):
        return
    bn = N.box_at(x, y)
    br = R.box_at(x, y)
    if bn is None or br is None:
        st["edge points with no box (model)"] += 1
        return
    if not bn["id"] or not br["id"] or N.level != R.level or bn["id"] == br["id"] or bn["kind"] != br["kind"]:
        return
    st["relabel calls"] += 1
    relabel(rooms, r, br["id"], bn["id"])


def neighbour_merge(rooms, r, st):
    """LOGIC_NeighbourMerge (0x0066D040): for each near room (list order) with a logic record and RectGapTest(R, N, 1)
    = 0: EdgeMerge at (x, R.y) and (x, R.y + R.h) for x = R.x .. R.x + R.w, then at (R.x, y) and (R.x + R.w, y) for
    y = R.y .. R.y + R.h."""
    R = rooms[r]
    x0, y0, w, h = R.rect
    for n in R.nb:
        if n == r or n not in rooms:
            continue
        if rect_gap_test(R.rect, rooms[n].rect, 1):
            continue
        st["neighbours merged against"] += 1
        for x in range(x0, x0 + w + 1):
            edge_merge(rooms, r, n, x, y0, st)
            edge_merge(rooms, r, n, x, y0 + h, st)
        for y in range(y0, y0 + h + 1):
            edge_merge(rooms, r, n, x0, y, st)
            edge_merge(rooms, r, n, x0 + w, y, st)


def _logic(a, R, release=True):
    """collision rows 41, 42, 44, 49 (spec L511, L562, L583, L863), drlg/0005 § 7: LogicBoxSingle sets the level's region
    counter +0x1DC to 1 and makes one box with id 1; a later flood room of the level therefore starts from 1; and the
    neighbour merge (LOGIC_NeighbourMerge / EdgeMerge / RegionRelabel, read from the disassembly) relabels boxes across
    same-level near rooms. Over the logs with LG0 lines (run:2026-10-14-collision; run:2026-10-15-objects and the other
    collision-family loggers):
      * counter: per level object (level id, act copy), the logic builds in tile-build order (TINIT; a type-1 room or a
        Logicals-0 preset is LogicBoxSingle, a Logicals-1 preset logs LG0/LG1); predicted LG0 base = 1 after a single
        box or at the first build, else the previous flood's LG1 counter;
      * the single box: every SN snapshot room with logic flag bit 0 has first box id 1;
      * merge: the boxes after the flood (LG1) and the model state of the near rooms, merged, against LG2's box ids;
        and every SN snapshot room's box grid against the model state at that time (relabels by later rooms included)."""
    logicals = [struct.unpack_from("<i", r, 0x0C)[0] for r in excel_rows("lvlprest")]
    paths = tagged(log_set("cluster", a.logs), "LG0")
    for p in paths:
        rooms = {}           # DRLG room -> LogicRoom
        info = {}            # DRLG room -> RRESEED
        ctr = {}             # (level id, act copy) -> +0x1DC as modelled
        last_single = {}     # (level id, act copy) -> True when the last logic build was a single box
        st = collections.Counter()
        lg0 = {}
        ev = list(events(p, ("RRESEED", "TINIT", "LG0", "LG1", "LG2", "SN", "RTFREE", "AROOM")))
        copy = {}            # RRESEED line -> 4 (client) or 0 (server), from the room's next AROOM flags
        open_ = {}
        for tag, d, ln in ev:
            if tag == "RRESEED":
                open_[d["room"]] = ln
            elif tag == "AROOM" and d["room"] in open_:
                copy[open_.pop(d["room"])] = d["flags"] & 4
        for tag, d, ln in ev:
            if tag == "RRESEED":
                d["actflag"] = copy.get(ln, -1)
                info[d["room"]] = d
            elif tag == "TINIT":
                I = info.get(d["room"])
                if I is None:
                    continue
                key = (I["level"], I.get("actflag", 0))
                single = I["type"] == 1 or (I["type"] == 2 and logicals[(I.get("preset") or {}).get("def", 0)] == 0)
                if single:
                    if ctr.get(key, 0) > 1:
                        R.add("single-box builds after a flood on the level (the reset is visible)")
                    ctr[key] = 1
                    last_single[key] = True
                    rooms[d["room"]] = LogicRoom(I["rect"], I["level"], I["nb"], True,
                                                 [{"id": 1, "kind": 0, "r0": None}])
            elif tag == "LG0":
                I = info.get(d["dr"])
                if I is None:
                    R.add("LG0 without RRESEED (not compared)")
                    continue
                key = (I["level"], I.get("actflag", 0))
                want = ctr.get(key, 0) or 1
                R.add("LG0 base checked")
                if last_single.get(key) and ctr.get(key) == 1:
                    R.add("LG0 after a single-box build on the level")
                if d["base"] != want:
                    R.add("bad")
                    R.note("%s:%d LG0 level %d base %d, model %d" % (os.path.basename(p), ln, I["level"], d["base"], want))
                lg0[d["dr"]] = (I, key)
            elif tag == "LG1":
                got = lg0.pop(d["dr"], None)
                if got is None:
                    continue
                I, key = got
                ctr[key] = d["ctr"]
                last_single[key] = False
                boxes = [dict(id=b["id"], kind=b["kind"], r0=b["r0"], b=b["b"]) for b in unz(d["z"])["boxes"]]
                rooms[d["dr"]] = LogicRoom(I["rect"], I["level"], I["nb"], False, boxes)
                st["lg1"] += 1
            elif tag == "LG2":
                if d["dr"] not in rooms:
                    continue
                L = rooms[d["dr"]]
                before = [b["id"] for b in L.boxes]
                neighbour_merge(rooms, d["dr"], st)
                got = {b["b"]: b["id"] for b in unz(d["z"])["boxes"]}
                mine = {b["b"]: b["id"] for b in L.boxes}
                R.add("LG2 merges compared")
                if before != [b["id"] for b in L.boxes]:
                    R.add("LG2 merges that relabelled the room's boxes (model)")
                if got != mine:
                    R.add("bad")
                    R.note("%s:%d LG2 room %08x: logged %s, model %s" % (os.path.basename(p), ln, d["dr"],
                                                                         sorted(got.items())[:6], sorted(mine.items())[:6]))
                    for b in L.boxes:                      # continue from the logged state
                        b["id"] = got.get(b["b"], b["id"])
            elif tag == "RTFREE":
                # sub_0066F1A0_RoomTilesRelease calls sub_0066C6E0_LogicRecordFree (frees +0x64, zeroes it) just before
                # RoomTileFree (the RTFREE line): a released room has no logic record until its next tile build
                st["logic records released (RTFREE)"] += 1
                if release:
                    rooms.pop(d["room"], None)
            elif tag == "SN":
                z = unz(d["z"])
                for rr in z["rooms"]:
                    lg, dr = rr["lg"], rr.get("dr")
                    if lg is None or dr not in rooms:
                        continue
                    L = rooms[dr]
                    if lg["fl"] & 1:
                        R.add("SN single-box records")
                        if lg["first"] != 1 or not L.single:
                            R.add("bad")
                            R.note("%s:%d SN room %08x single box first %s (model single %s)" % (os.path.basename(p), ln,
                                                                                                  dr, lg["first"], L.single))
                        continue
                    g = lg.get("grid")
                    if g is None or L.single:
                        continue
                    if isinstance(g, str):
                        g = json.loads(g)
                    tx, ty = lg["t"]
                    bad = 0
                    for yy, row in enumerate(g[2]):
                        for xx, v in enumerate(row):
                            b = L.box_at(tx + xx, ty + yy)
                            if (b["id"] if b else None) != v:
                                bad += 1
                    R.add("SN flood-room box grids compared")
                    if bad:
                        R.add("bad")
                        R.note("%s:%d SN room %08x: %d cells differ from the model's box ids" % (os.path.basename(p), ln,
                                                                                                dr, bad))
        for k, v in st.items():
            R.add(k, v)
    R.add("logs", len(paths))



def chk_logic(a):
    """See _logic. The run is made twice: as read (the logic record freed at RoomTilesRelease), and as a control with the
    record kept, whose mismatches are reported as the control's (not as failures)."""
    R = Report("logic")
    _logic(a, R, True)
    C = Report("logic-control")
    _logic(a, C, False)
    R.add("control (record kept at release): mismatches", C["bad"])
    return R.done()

def chk_barrier(a):
    """collision row 43 (spec L572): LOGIC_BarrierGridBuild (0x0066C870). A tile is a barrier when one of the room's own
    wall entries there (RoomTile +0x14 array) has layer bits (flags & 0x1C000) = 0x4000, orientation != 15 and no flag
    0x800, or when an entry of a near room's kind-0 node list (walls and shadows of its bit-2 nodes) does, inside this
    room's tile rectangle (inclusive). The entries are tools/drlg.py's room-tiles model (Model, run_log: every entry's
    position, orientation and flags are compared with the activation dumps in logs with CB lines). An entry's 0x800 can
    also come from its tile's flags16 bit 2 (entry_flags), so each entry takes its tile from the CB dump that lists it
    (index-aligned with the model's array, as Model.cb_entries compares them) and the TL record of that tile. The flags
    are the model's at the room's tile build; the barrier grid the flood read is LG0's. Every log with LG0 and roomk
    lines."""
    R = Report("barrier")
    import drlg
    paths = [p for p in tagged(log_set("cluster", a.logs), "LG0") if tagged([p], "RRESEED")]

    def cond(fl, o):
        return (fl & 0x1C000) == 0x4000 and o != 15 and not fl & 0x800

    class BModel(drlg.Model):
        def cb_entries(self, path, d, rooms):
            z = unz(d["z"])
            for n, dr, _t, Wl, Fl, Sl in z["near"]:
                Rr = rooms.get(dr)
                if Rr is None or Rr.nodes is None or not Rr.built:
                    continue
                for kind, got in (("W", Wl), ("F", Fl), ("S", Sl)):
                    mine = Rr.arr[kind]
                    for i, g in enumerate(got[:len(mine)]):
                        w6 = self.tl.get(g[3])
                        if w6 is not None:
                            W6[id(mine[i])] = w6
            return super().cb_entries(path, d, rooms)

        def tiles_build(self, Rm, d):
            super().tiles_build(Rm, d)
            q = self.lg0.get(Rm.ptr)
            if not q:
                return
            want = q.pop(0)
            own = [(e, e.flags) for e in Rm.arr["W"]]
            nbr = []
            for qq in Rm.nb:
                N = self.rooms.get(qq)
                if qq == Rm.ptr or N is None or N.nodes is None:
                    continue
                for nd in N.nodes:
                    if nd[0] == 0:
                        nbr += [(e, e.flags, N.x, N.y) for e in nd[1]]
            self.pend.append((Rm.ptr, Rm.level, (Rm.x, Rm.y, Rm.w, Rm.h), want, own, nbr))

    W6 = {}                      # id(model entry) -> flags16 of its tile (Entry has __slots__)

    def flags_of(e, fl):
        w6 = W6.get(id(e))
        if w6 is None:
            return None
        if e.tbits:
            if w6 & 1:
                fl |= 4
            if w6 & 4:
                fl |= 0x800
        return fl

    for p in paths:
        m = BModel(drlg.Data(DATA, EXE), False)
        m.lg0, m.pend = {}, []
        W6.clear()
        for tag, d, ln in events(p, ("LG0",)):
            m.lg0.setdefault(d["dr"], []).append(unz(d["z"])["barrier"])
        with quiet():
            drlg.run_log(m, p)
        R.add("roomk model mismatches", m.fail)
        R.add("LG0 not reached by the model", sum(len(v) for v in m.lg0.values()))
        for ptr, lv, (x0, y0, w, h), want, own, nbr in m.pend:
            W, H = w + 1, h + 1
            grid = [[0] * W for _ in range(H)]
            unk = [[False] * W for _ in range(H)]
            tile_800 = 0
            for e, fl in own:
                f = flags_of(e, fl)
                if not (0 <= e.x < W and 0 <= e.y < H):
                    continue
                if f is None:
                    if cond(fl, e.o):
                        unk[e.y][e.x] = True
                    continue
                if cond(f, e.o):
                    grid[e.y][e.x] = 1
                elif cond(fl, e.o):
                    tile_800 += 1
            from_nb = 0
            for e, fl, nx, ny in nbr:
                X, Y = e.x + nx, e.y + ny
                if not (x0 <= X <= x0 + w and y0 <= Y <= y0 + h):
                    continue
                f = flags_of(e, fl)
                if f is None:
                    if cond(fl, e.o):
                        unk[Y - y0][X - x0] = True
                    continue
                if cond(f, e.o):
                    if not grid[Y - y0][X - x0]:
                        from_nb += 1
                    grid[Y - y0][X - x0] = 1
            got = want[2]
            diff = [(x, y) for y in range(H) for x in range(W) if got[y][x] != grid[y][x]]
            und = [(x, y) for x, y in diff if unk[y][x]]
            R.add("barrier grids compared")
            R.add("barrier tiles", sum(map(sum, grid)))
            if from_nb:
                R.add("rooms with barrier tiles only from a near room's bit-2 node")
                R.add("barrier tiles only from a near room's bit-2 node", from_nb)
            if tile_800:
                R.add("wall entries excluded only by their tile's flags16 bit 2 (0x800)", tile_800)
            if diff and len(und) == len(diff):
                R.add("grids whose only differences are entries never dumped (tile unknown)")
            elif diff:
                R.add("bad")
                R.note("%s room %08x level %d: %d tiles differ %s" % (os.path.basename(p), ptr, lv, len(diff), diff[:6]))
    R.add("logs", len(paths))
    if R["roomk model mismatches"]:
        R.add("bad")
    return R.done()


def chk_flood(a):
    """collision rows 6, 42 (spec L90-L91, the G3 ROW/RULES note): the flood tables g_LogicFloodDirs, g_LogicFloodOrientRow
    and g_LogicFloodRules, as tools/collision.py reads them from the pinned game.exe, drive the reproduction of every
    flood (LG0 -> LG1). Here: which (row, d) entries and orientations the floods read, and for each entry read, whether
    changing it breaks a flood (the reproduction depends on that value)."""
    R = Report("flood")
    import collision
    W = collision.World(DATA, None)
    floods = []
    for p in tagged(log_set("cluster", a.logs), "LG0"):
        pend = {}
        for tag, d, ln in events(p, ("LG0", "LG1")):
            if tag == "LG0":
                pend[d["dr"]] = (d, unz(d["z"]))
            elif d["dr"] in pend:
                d0, z0 = pend.pop(d["dr"])
                z1 = unz(d["z"])
                floods.append((d0, z0, z1["ids"][2] if z1["ids"] else None, d["n"], d["ctr"]))
    R.add("floods", len(floods))

    class Rec(dict):
        def __init__(self, base):
            super().__init__(base)
            self.used = collections.Counter()

        def __getitem__(self, k):
            self.used[k] += 1
            return dict.__getitem__(self, k)

    rules0 = dict(W.flood_rules)
    rec = Rec(rules0)
    W.flood_rules = rec
    orients = collections.Counter()
    for d0, z0, ids, n, ctr in floods:
        got = W.flood(d0, z0)
        if got[0] != ids or got[2] != n or got[3] != ctr:
            R.add("bad")
        o = z0["orient"]
        bar = z0["barrier"]
        if bar and bar[2]:
            for y, row in enumerate(bar[2]):
                for x, v in enumerate(row):
                    if v:
                        orients[o[2][y][x] if o and o[2] else 0] += 1
    R.add("(row, d) rule entries read", len(rec.used))
    R.add("orientations at barrier tiles", len(orients))
    R.note("orientations at barrier tiles (count): " + ", ".join("%d: %d" % kv for kv in sorted(orients.items())))
    R.note("rule entries read (row, d): " + ", ".join("%s" % (k,) for k in sorted(rec.used)))
    # sensitivity: each entry read, flipped one bit at a time; a flood that changes is a dependence
    sens = 0
    for k in sorted(rec.used):
        hit = False
        for bit in (1, 2, 4, 8, 0x10, 0x20):
            W.flood_rules = dict(rules0)
            W.flood_rules[k] = rules0[k] ^ bit
            for d0, z0, ids, n, ctr in floods:
                g = W.flood(d0, z0)
                if g[0] != ids or g[2] != n:
                    hit = True
                    break
            if hit:
                break
        sens += hit
        if not hit:
            R.note("entry %s: no flood changes when one of bits 0-5 is flipped" % (k,))
    R.add("entries read whose change breaks a flood", sens)
    # the orientation -> row table: each orientation met at a barrier tile, its row replaced by every other row
    row0 = list(W.flood_row)
    W.flood_rules = dict(rules0)
    rsens = 0
    for o in sorted(orients):
        hit = False
        for alt in (-1, 0, 1, 2, 3, 4):
            if alt == row0[o] if o < len(row0) else alt == 0:
                continue
            W.flood_row = list(row0)
            if o < len(W.flood_row):
                W.flood_row[o] = alt
            for d0, z0, ids, n, ctr in floods:
                g = W.flood(d0, z0)
                if g[0] != ids or g[2] != n:
                    hit = True
                    break
            if hit:
                break
        rsens += hit
        if not hit:
            R.note("orientation %d: no flood changes with any other row" % o)
    W.flood_row = row0
    R.add("orientations met whose row change breaks a flood", rsens)
    R.note("g_LogicFloodOrientRow (first 20): %s" % (row0[:20],))
    # the direction table
    import drlg
    dirs = struct.unpack("<8i", drlg.exe_read(EXE, 0x006EEE14, 32))
    R.add("g_LogicFloodDirs matches the model's DX/DY", int(list(zip(dirs[0::2], dirs[1::2])) == collision.FLOOD_DIRS
                                                           or (list(dirs[:4]), list(dirs[4:])) ==
                                                           ([x for x, _ in collision.FLOOD_DIRS], [y for _, y in collision.FLOOD_DIRS])))
    R.note("g_LogicFloodDirs dwords: %s" % (dirs,))
    W.flood_rules = rules0
    return R.done()


def u16cells(hx):
    b = bytes.fromhex(hx)
    return list(struct.unpack("<%dH" % (len(b) // 2), b))


def chk_bits(a):
    """collision rows 12, 13, 15, 16, 17, 18, 20, 29, 31, 32, 33 (spec § D, § F): the writers of grid bits 1, 2, 4, 5, 6,
    7 and 11 and the unit footprints, counted on what the earlier runs already compared:
      * activation dumps (CB, run:2026-10-14-collision and run:2026-10-15-objects; each dump equals the activation model
        cell for cell, the stamp of the DT1 sub-tile bytes and the entry flags): cells holding bits 1, 2, 4, 5, and the
        DT1 files whose sub-tile bytes carry bit 4 (TL records);
      * unit marks logged in the windows (CM, each compared with the model's mark by tools/monspawn.py and
        tools/objects.py): masks with bits 1, 2, 11 (doors 0x806, BlockMissile objects 0x404), monster patterns by size,
        object rectangles, the ground items' 0x200;
      * missile mask changes (MS/MSX, PATH_SetMarkMask 0x40): replayed here as SizeMark(size, 0x40) on the 5 x 5 cells,
        size against Missiles +0x18A and Collision +0x184;
      * pass-entry snapshots (SN): every cell carrying the player bit 0x80, grouped by footprint."""
    R = Report("bits")
    mis = excel_rows("missiles")
    files_b4 = collections.Counter()
    # the logs whose activation dumps and marks a checker compared (tools/gdb/collision.py; tools/gdb/pilot.py also
    # writes CB lines, which no checker compared)
    paths = tagged(log_set("collision", a.logs) + log_set("objects", a.logs), "CB")
    for p in paths:
        for tag, d, ln in events(p, ("CB", "TL", "CM", "MS", "MSX", "SN")):
            if tag == "TL":
                b = bytes.fromhex(d["b"])
                if any(x & 0x10 for x in b):
                    files_b4[d["f"].split("\\")[-1].lower()] += 1
            elif tag == "CB":
                z = unz(d["z"])
                if z["cells"][4] is None:
                    continue
                c = u16cells(z["cells"][4])
                R.add("activation dumps")
                for bit in (1, 2, 4, 5):
                    R.add("activation cells with bit %d" % bit, sum(1 for v in c if v & (1 << bit)))
                R.add("activation cells with a unit bit (0x40..0x8000; must be 0)", sum(1 for v in c if v & 0xFFC0))
                if any(v & 0xFFC0 for v in c):
                    R.add("bad")
            elif tag == "CM":
                f, m_ = d["f"], d.get("m", d.get("b"))
                if f == "RO":
                    R.add("CM RectOrWH mask %#x" % d["m"])
                elif f == "PM":
                    R.add("CM PatternMark pattern %d mask %#x" % (d["a"], d["b"]))
            elif tag == "MS":
                pend = d
            elif tag == "MSX":
                d0 = pend
                cls, size = d0["cls"], d0["size"]
                rec = mis[cls]
                R.add("missile 0x40 marks, class %d size %d" % (cls, size))
                if rec[0x184] == 0:
                    R.add("bad")
                if struct.unpack_from("<B", rec, 0x18A)[0] != size:
                    R.add("bad")
                    R.note("%s:%d missile class %d size %d, Missiles +0x18A %d" % (os.path.basename(p), ln, cls, size,
                                                                                 rec[0x18A]))
                exp = [row[:] for row in d0["cells"]]
                fp = {1: [(0, 0)], 2: [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)],
                      3: [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]}.get(size, [])
                for dx, dy in fp:
                    if exp[2 + dy][2 + dx] is not None:
                        exp[2 + dy][2 + dx] |= 0x40
                if exp != d["cells"]:
                    R.add("bad")
                    R.note("%s:%d missile class %d size %d: cells differ from SizeMark" % (os.path.basename(p), ln, cls,
                                                                                         size))
                if size == 2:
                    sq = [row[:] for row in d0["cells"]]
                    for dy in (-1, 0):
                        for dx in (-1, 0):
                            if sq[2 + dy][2 + dx] is not None:
                                sq[2 + dy][2 + dx] |= 0x40
                    if sq != d["cells"]:
                        R.add("size-2 marks a 2 x 2 RectOrWH would not give")
            elif tag == "SN":
                z = unz(d["z"])
                for rr in z["rooms"]:
                    if not rr["cells"] or not rr["cells"][4]:
                        continue
                    x0, y0, w, h = rr["rect"]
                    c = u16cells(rr["cells"][4])
                    pts = {(i % w, i // w) for i, v in enumerate(c) if v & 0x80}
                    while pts:
                        st, comp = [pts.pop()], set()
                        while st:
                            q = st.pop()
                            comp.add(q)
                            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                                n = (q[0] + dx, q[1] + dy)
                                if n in pts:
                                    pts.discard(n)
                                    st.append(n)
                        cx = sorted(comp)
                        plus = None
                        for (x, y) in comp:
                            if {(x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)} == comp:
                                plus = (x, y)
                        if plus:
                            R.add("SN player footprints: a full plus")
                            v = c[plus[1] * w + plus[0]]
                            R.add("... with 0x1000 at the centre" if v & 0x1000 else "... without 0x1000 at the centre")
                        elif any(x in (0, w - 1) or y in (0, h - 1) for x, y in comp):
                            R.add("SN player footprints cut by the room edge")
                        else:
                            R.add("SN player footprints of another shape")
                            R.note("%s:%d %s" % (os.path.basename(p), ln, cx[:9]))
    R.add("logs", len(paths))
    R.note("TL records whose sub-tile bytes carry bit 4, by file: %s" % dict(files_b4))
    return R.done()


def chk_pflags(a):
    """preset rows 9, 16, 28, 40 (spec L195, L360, L479, L548): room flags 0x80000 (Outdoors, at PresetRoomsCreate),
    0x2000000 (set by PresetRoomLoadDs1 on every call) and 0x8000000 (the Animate tile build).
      * RL (LevelRoomLink, every gen-family log): a type-2 room's +0x28 at creation; 0x80000 iff its LvlPrest Outdoors
        (+0x10) is 1, and never 0x2000000;
      * PLDX (the return of PresetRoomLoadDs1 to its two callers, run:2026-10-13-drlg-preset, run:2026-10-15-acts-3-5):
        +0x28 after every call holds 0x2000000;
      * RTFREE (RoomTileFree, roomk-family logs): +0x28 of a released type-2 room whose tiles were built (rt != 0):
        0x8000000 iff the preset's Animate (RRESEED preset record) is 1."""
    R = Report("pflags")
    outd = [struct.unpack_from("<i", r, 0x10)[0] for r in excel_rows("lvlprest")]
    for p in log_set("cluster", a.logs):
        info = {}
        for tag, d, ln in events(p, ("RL", "PLDX", "RRESEED", "RTFREE")):
            if tag == "RL" and d["type"] == 2 and d.get("pdef") is not None:
                R.add("RL type-2 rooms")
                o = outd[d["pdef"]]
                if bool(d["f28"] & 0x80000) != bool(o):
                    R.add("bad")
                    R.note("%s:%d RL Def %d Outdoors %d flags %#x" % (os.path.basename(p), ln, d["pdef"], o, d["f28"]))
                R.add("RL type-2 rooms with Outdoors 1 (0x80000 set)" if o else "RL type-2 rooms with Outdoors 0")
                if d["f28"] & 0x2000000:
                    R.add("bad")
                    R.note("%s:%d RL room already has 0x2000000" % (os.path.basename(p), ln))
            elif tag == "PLDX":
                R.add("PresetRoomLoadDs1 calls (PLDX)")
                if not d["f28"] & 0x2000000:
                    R.add("bad")
                    R.note("%s:%d PLDX flags %#x" % (os.path.basename(p), ln, d["f28"]))
            elif tag == "RRESEED":
                info[d["room"]] = d
            elif tag == "RTFREE" and d["rt"]:
                I = info.get(d["room"])
                if I is None or I["type"] != 2 or not I.get("preset"):
                    continue
                an = I["preset"].get("animate")
                if an is None:
                    continue
                R.add("released preset rooms, Animate %d" % an)
                if bool(d["f28"] & 0x8000000) != bool(an):
                    R.add("bad")
                    R.note("%s:%d RTFREE room %08x Def %d Animate %d flags %#x" % (os.path.basename(p), ln, d["room"],
                                                                                  I["preset"]["def"], an, d["f28"]))
    return R.done()


def chk_dispatch(a):
    """preset row 18 (spec L415): sub_005557D0_PresetUnitDispatch sends type 1 to the monster spawner, a type-2 id above
    573 to 0x0054F490, 573 to nothing and every other unit to SUnitCreate. PSP (sub_00555910_PresetUnitSpawn after the
    dispatch: the unit made, its type and class; run:2026-10-13-drlg-preset, run:2026-10-15-acts-3-5) per branch; and,
    in the objects windows (run:2026-10-15-objects), the CM mark calls between a type-5 unit's OPU0 and OPUX (collision
    row 38: a type-5 unit marks nothing)."""
    R = Report("dispatch")
    for p in log_set("preset", a.logs) + log_set("acts35", a.logs):
        for tag, d, ln in events(p, ("PSP",)):
            t, i = d["type"], d["id"]
            u = d["unit"]
            if t == 1:
                R.add("type 1: monster made" if u and d["utype"] == 1 else "type 1: no unit" if not u else "bad")
            elif t == 2 and i < 573:
                R.add("type 2 below 573: SUnitCreate, class = id" if u and d["utype"] == 2 and d["cls"] == i else "bad")
            elif t == 2 and i == 573:
                R.add("type 2 id 573: nothing" if not u else "bad")
            elif t == 2:
                R.add("type 2 above 573: an object of another class" if u and d["utype"] == 2 and d["cls"] != i
                      else "bad")
            else:
                R.add("type %d: SUnitCreate, type and class kept" % t if u and d["utype"] == t and d["cls"] == i
                      else "bad")
    for p in log_set("objects", a.logs):
        cur, marks = None, 0
        for tag, d, ln in events(p, ("OPU0", "OPUX", "CM")):
            if tag == "OPU0":
                cur, marks = d, 0
            elif tag == "CM" and cur is not None:
                marks += 1
            elif tag == "OPUX" and cur is not None:
                if cur["type"] == 5:
                    R.add("type-5 units created in a logged window")
                    if marks:
                        R.add("bad")
                        R.note("%s:%d type-5 unit with %d mark calls" % (os.path.basename(p), ln, marks))
                cur = None
    return R.done()


def chk_punits(a):
    """preset rows 5, 7, 20 (spec L120, L153, L430): DS1_Parse's unit list (the skip rule, the path attach, MapId by type
    and version), the unit mode, and the 0x20-byte PresetUnit record. tools/drlg.py gen (PresetUnitData) reproduces
    every instance list and room list of run:2026-10-13-drlg-preset and run:2026-10-15-acts-3-5 (the lists are logged
    as [ptr, type, id, mode, x, y, flags, path] read from the PresetUnit record); this run counts, over the DS1 files the
    model parsed for those logs, each branch the parse took, and over the logged lists the (type, mode) pairs."""
    R = Report("punits")
    import drlg
    import ds1 as ds1mod
    orig = drlg.PresetUnitData.ds1
    seen = set()

    def ds1(self, cell):
        if cell not in seen:
            seen.add(cell)
            path = os.path.join(self.root, "data", "global", "tiles", cell.replace("\\", "/").lower())
            f = ds1mod.parse(open(path, "rb").read())
            v = f["version"]
            act = min(f["act"] or 0, 4) if v >= 8 else 0
            R.add("DS1 files parsed")
            units = []
            for o in f["objects"]:
                typ, uid = o["type"], o["id"]
                if typ == 1:
                    if v <= 4:
                        R.add("type 1 in a DS1 below version 5: skipped")
                        continue
                    lst = self.monpreset.get(act, [])
                    if uid >= len(lst):
                        R.add("type 1 past the act's MonPreset list (id kept)")
                    else:
                        kind = lst[uid][0]
                        R.add("type 1 MonPreset kind %d (%s)" % (kind, {0: "MonPlace: nMonStats + nSuperUniques + row",
                                                                        1: "MonStats class", 2: "SuperUnique: nMonStats + row"}
                                                                 .get(kind, "other: -1, skipped")))
                elif typ == 2:
                    if v < 6:
                        R.add("type 2, version below 6: id kept" if uid != 0x23D else "type 2, version below 6: 0x23D, skipped")
                    elif uid < 150:
                        R.add("type 2, version 6+, id below 150: g_Ds1ObjectIds[act][id]%s"
                              % (", -1 skipped" if self.objtab[act][uid] < 0 else ""))
                    else:
                        R.add("type 2, version 6+, id 150+: id - 150")
                else:
                    R.add("type %d entries" % typ)
                units.append((o["x"], o["y"]))
            pos = collections.Counter(units)
            for pth in f["paths"]:
                if not pth["points"]:
                    R.add("paths without points")
                    continue
                n = pos.get((pth["x"], pth["y"]), 0)
                R.add("paths attached" if n else "paths dropped (no unit at their position)")
                if n > 1:
                    R.add("paths whose position holds two or more units (the last in the file takes it)")
                if v < 15:
                    R.add("paths in a DS1 below version 15 (action 1)")
        return orig(self, cell)

    if os.environ.get("S4A_PUNITS_SURVEY"):
        # every File cell of lvlprest, outside any log (data behaviour over the whole table): the same counters
        pu = drlg.PresetUnitData(DATA, EXE)
        for rec in excel_rows("lvlprest"):
            for f in drlg.LvlPrest(rec).files:
                if f not in ("", "0"):
                    try:
                        ds1(pu, f)
                    except drlg.ModelError as e:
                        R.add("DS1 files the model refuses (%s)" % str(e).split(":")[-1].strip())
        return R.done()
    with patched(drlg.PresetUnitData, "ds1", ds1):
        m, rk, bad = run_gen(log_set("preset", a.logs) + log_set("acts35", a.logs))
    R.add("gen mismatches", bad)
    if bad:
        R.add("bad")
    R.add("preset rooms reproduced", len(m.prooms))
    modes = collections.Counter()
    for p in log_set("preset", a.logs) + log_set("acts35", a.logs):
        for tag, d, ln in events(p, ("PLDX", "PRRX", "PSL")):
            for u in d.get("units") or []:
                modes[(u[1], u[3])] += 1
    for (t, mo), n in sorted(modes.items()):
        R.add("logged units type %d mode %d" % (t, mo), n)
        if (t, mo) not in ((1, 1), (2, 0)):
            R.add("bad")
    return R.done()


def chk_kill(a):
    """preset row 30 (spec L481): KillEdge and FillBlanks feed the tile build. tools/drlg.py roomk's model (Model,
    run_log) over the roomk-family logs, as recorded (0 mismatches), then with KillEdge ignored and with FillBlanks
    ignored: the rooms whose preset sets each column, and the mismatches each change makes."""
    R = Report("kill")
    import drlg
    paths = [p for p in log_set("cluster", a.logs) if tagged([p], "TINIT")]
    orig = drlg.Model.tiles_build
    for mode in ("stock", "killedge", "fillblanks"):
        def tiles_build(self, Rm, d, mode=mode):
            if Rm.type == 2:
                P = Rm.preset
                if mode == "stock":
                    R.add("type-2 rooms built with KillEdge 1" if P["killedge"] else "type-2 rooms built with KillEdge 0")
                    R.add("type-2 rooms built with FillBlanks 1" if P["fillblanks"] else "type-2 rooms built with FillBlanks 0")
                saved = dict(P)
                if mode == "killedge":
                    P["killedge"] = 0
                elif mode == "fillblanks":
                    P["fillblanks"] = 0
                try:
                    return orig(self, Rm, d)
                finally:
                    P.update(saved)
            return orig(self, Rm, d)
        fail = 0
        with patched(drlg.Model, "tiles_build", tiles_build):
            for p in paths:
                m = drlg.Model(drlg.Data(DATA, EXE), False)
                with quiet():
                    drlg.run_log(m, p)
                fail += m.fail
        R.add("mismatches, %s" % mode, fail)
    if R["mismatches, stock"] or not R["mismatches, killedge"] or not R["mismatches, fillblanks"]:
        R.add("bad")
    R.add("logs", len(paths))
    return R.done()


def chk_l27(a):
    """preset rows 23, 24, 25, 38 (spec L449, L455, L463, L528): level 27's file index is drawn on the act seed while
    LevelLinkBuild handles level 6, from level 6's link value v (1 or 3; any other v: no draw, no write). The link
    builder of tools/drlg.py gen predicts the act seed from the map seed (Act; LNK0's seed in, LNK1's seed out, LK27's
    index and seed, run:2026-10-15-drlg-maze and run:2026-10-15-drlg-outdoor loggers). Counts the Act I builds by
    level 6's link value, the ones that drew, and checks levels.txt names levels 6 and 27."""
    R = Report("l27")
    import drlg
    orig = drlg.link_build

    def link_build(A, va, check=None, after=None):
        idx0 = getattr(A, "idx27", None)
        n0 = A.seed.n if hasattr(A.seed, "n") else None
        lo0 = A.seed.copy()
        B = orig(A, va, check, after)
        for i, (pk, lv, x, y) in enumerate(drlg.TABLE[va]):
            if lv == 6:
                d = B.dir[i]
                R.add("link builds handling level 6, link value %d" % d)
        return B

    with patched(drlg, "link_build", link_build):
        m, rk, bad = run_gen(gen_logs(a, ("gen", "maze", "outdoor", "acts35")))
    for k in ("link builder: level-27 index draw on the act seed predicted",):
        R.add("LK27 lines checked (index and act seed after the draw)", m.cov.get(k, 0))
    R.add("LevelLinkBuild calls checked (seed in, seed out, rects)",
          sum(v for k, v in m.cov.items() if k.startswith("link builder: calls predicted")))
    R.add("gen mismatches", bad)
    if bad:
        R.add("bad")
    h, rows = _tsv("levels.txt")
    names = {r[h.index("Id")]: r[h.index("Name")] for r in rows if r[h.index("Id")].strip().isdigit()}
    R.note("levels.txt: 6 = %s, 27 = %s" % (names.get("6"), names.get("27")))
    return R.done()


def chk_pcopies(a):
    """preset row 10 (spec L215): with the room-seed caller (PresetRoomLoadDs1 at 0x006678E2), each copy rolls on the
    seed of whichever of its rooms loads first, so the server and client copies of an instance agree only when the same
    room loads first in both. PRR lines (seed in, the loading room, the instance's Def and rect, the level; run:2026-10-13-
    drlg-preset, run:2026-10-15-acts-3-5) paired across copies (level id, Def, preset rect); the copy is the room's flag
    0x40000 (client). Counts pairs with the same first room (seeds must be equal) and with different first rooms
    (seeds, and the kept lists of PRRX)."""
    R = Report("pcopies")
    for p in log_set("preset", a.logs) + log_set("acts35", a.logs):
        client = {}
        rooms = {}
        firsts = {}
        pend = {}
        for tag, d, ln in events(p, ("LC0", "RL", "PRR", "PRRX")):
            if tag == "LC0":
                client[d["level"]] = d["client"]
            elif tag == "RL":
                rooms[d["room"]] = tuple(d["rect"])
            elif tag == "PRR":
                c = 1 if d["f28"] & 0x40000 else 0          # room +0x28 bit 0x40000: the client copy (drlg.py)
                key = (d["lid"], d["def"], tuple(d["prect"]))
                pend[d["room"]] = (key, c)
                firsts.setdefault(key, {}).setdefault(c, [rooms.get(d["room"]), d["seed"], None])
            elif tag == "PRRX" and d["room"] in pend:
                key, c = pend.pop(d["room"])
                f = firsts[key][c]
                if f[2] is None:
                    f[2] = [(u[1], u[2], u[4], u[5]) for u in d["units"]]
                    f.append(d["seed"] != f[1])                 # the roll drew
        for key, by in firsts.items():
            if 0 not in by or 1 not in by:
                continue
            s_, c_ = by[0], by[1]
            same_room = s_[0] == c_[0]
            same_seed = s_[1].split(":")[0] == c_[1].split(":")[0]
            same_list = s_[2] == c_[2]
            if same_room:
                R.add("instances whose copies loaded the same room first")
                if not same_seed or not same_list:
                    R.add("bad")
                    R.note("%s Def %d: same first room, seeds %s %s" % (os.path.basename(p), key[1], s_[1], c_[1]))
            else:
                R.add("instances whose copies loaded different rooms first")
                R.add("... with different roll seeds" if not same_seed else "... with the same roll seed")
                R.add("... whose kept lists differ" if not same_list else "... whose kept lists agree")
                R.add("... where neither roll drew" if not (s_[3:] and s_[3]) and not (c_[3:] and c_[3])
                      else "... where a roll drew")
    return R.done()



def b4(p, T, R):
    """objects row 7 (B4): from the lines alone. A creation is SUnitCreate (OU0 .. OUX: class, position, mode, sparkle);
    it is a re-creation when it comes through PresetUnitDispatch (OPU0) and an object of the same level, class and
    position was created before (RoomInactiveUnitsRestore dispatches every saved record; the populate pass does not use
    the dispatch). A restore is a run of re-creations in one room. Every object created earlier inside that room's
    rectangle (CB) is checked against SaveTest at its last known state (OUX, then each operate's OOX): Restore set,
    sparkle bit 0x02 clear, RestoreVirgins 0 or mode 0. The preset flag is "created through the dispatch"; for the
    other objects the level flag (+0x94) is the remaining input, so they are counted per level. Also the order inside
    a restore (B5, the records oldest first)."""
    units, ident, cb, groups, allst = {}, set(), {}, [], []
    lid = pend = grp = opu = None
    for tag, d, ln in events(p, ("RW1", "OPU0", "OPUX", "OU0", "OUX", "OOX", "CB")):
        if tag in ("RW1", "OPU0"):
            lid = d.get("lid", lid)
        if tag == "OPU0":
            opu = d
        elif tag == "OPUX":
            opu = None
        elif tag == "CB":
            cb.setdefault(d["room"], []).append((ln, d["rect"]))
        elif tag == "OU0" and d["type"] == 2:
            pend = dict(cls=d["cls"], x=d["x"], y=d["y"], room=d["room"], lid=lid, pre=opu is not None and opu["type"] == 2)
        elif tag == "OUX" and pend:
            o = d["o"]
            if o and o.get("u"):
                u = dict(pend, mode=o["mode"], sp=o["sp"], seq=ln)
                k = (u["lid"], u["cls"], u["x"], u["y"])
                if k in ident and u["pre"]:
                    if grp is None or grp["room"] != u["room"]:
                        grp = dict(room=u["room"], lid=u["lid"], ln=ln, units=[])
                        groups.append(grp)
                    grp["units"].append(u)
                else:
                    grp = None
                ident.add(k)
                units[o["u"]] = u
                allst.append(u)
            pend = None
        elif tag == "OOX" and d.get("u") in units:
            units[d["u"]].update(mode=d["mode"], sp=d["sp"])
    for G in groups:
        rects = [r for r in cb.get(G["room"], []) if r[0] < G["ln"]]
        if not rects:
            R.add("B4: restores whose room rectangle is not logged")
            continue
        x0, y0, w, h = rects[-1][1]
        first = min(u["seq"] for u in G["units"])
        back = [(u["cls"], u["x"], u["y"]) for u in G["units"]]
        lat = {}
        for u in allst:
            if u["seq"] < first and u["lid"] == G["lid"] and x0 <= u["x"] < x0 + w and y0 <= u["y"] < y0 + h:
                lat[(u["cls"], u["x"], u["y"])] = u
        R.add("B4: restores checked")
        for k, u in lat.items():
            o = T.objs[u["cls"]]
            save = bool(o["Restore"]) and not (u["sp"] & 2) and (not o["RestoreVirgins"] or u["mode"] == 0)
            if u["pre"]:
                R.add("B4: preset objects, SaveTest %s, %s" % (save, "re-created" if k in back else "not re-created"))
            else:
                R.add("B4: populated objects, SaveTest without the level flag %s, %s"
                      % (save, "re-created" if k in back else "not re-created"))
                if k in back:
                    R.levels_back = getattr(R, "levels_back", set()) | {G["lid"]}
            if save != (k in back):
                R.add("bad")
                R.note("%s:%d restore: class %d at (%d, %d) mode %d sp %d, SaveTest %s, re-created %s"
                       % (os.path.basename(p), G["ln"], u["cls"], u["x"], u["y"], u["mode"], u["sp"], save, k in back))
        seqs = [lat[k]["seq"] for k in back if k in lat]
        for x, y in zip(seqs, seqs[1:]):
            R.add("B5: consecutive re-creations in the earlier creation order" if y > x else "bad")


def chk_objects(a):
    """objects rows 7, 9, 11, 14, 28, 37 (spec L224, L262, L346, L428, L617, L699) over the 29 logs of
    run:2026-10-15-objects, with tools/objects.py check run as recorded (its mismatch count is reported):
      * C1 gate: each OG line's inputs as the gate evaluated them (f: the room-flag test, pop, pre, town; a key is logged
        only when its test ran) give the short-circuit order and the result; f against the DRLG room's flags & 0x30000
        (RRESEED/TINIT f28 of the room's DRLG room, CB);
      * D3: the slots that drew group 0 (no member pick), groups 30 and 72 (no member) and 69 (empty first slot); no
        PROB-0 member ever handled; Objects Gore over every row and the limit byte g_ObjGoreLimit;
      * E2: HealthShrineDue as the model evaluates it in every shrine handler call, and the OS counters it feeds;
      * H: the InitFns that ran with no draw (the seeds and the unit seed asserted at OIX);
      * I1: the DS1 580 super chests (the closing SetMode(0) made no draw);
      * B4: at every revisit restore (objects re-created by RoomInactiveUnitsRestore, tools/objects.py's lone_preset),
        the objects of that room before the revisit against SaveTest: Restore, sparkle bit 0x02 clear, RestoreVirgins 0
        or mode 0, and the preset flag (the level flag +0x94 is not modelled: the populated objects are counted apart)."""
    R = Report("objects")
    import objects as om
    paths = log_set("objects", a.logs)
    T = om.Tables(EXCEL)
    st = R.c

    class C(om.Checker):
        def pop_2(self, cls, den):
            L = self.L_
            forced = L["cnt"] > 0 and om.idiv(L["vis"] << 7, L["cnt"]) > 96 and L["hs"] == 0
            st["shrine handler calls, HealthShrineDue %s" % ("true (30 tries)" if forced else "false")] += 1
            return om.Checker.pop_2(self, cls, den)

    c = C(EXCEL, DATA, False)
    for p in paths:
        with quiet():
            c.run(p)
        b4(p, T, R)
    R.note("B4: levels whose populated objects came back (the level flag +0x94 held): %s"
           % sorted(getattr(R, "levels_back", set())))
    R.add("objects.py mismatches", c.fail)
    if c.fail:
        R.add("bad")
    for k, v in c.stats.items():
        if k.startswith("InitFns without draws"):
            R.add(k, v)
    R.add("forced slots (r = 100; the inlined HealthShrineDue test held)", len(c.cov.get("forced slots (r = 100)", [])))
    R.add("DS1 580 super chests created", len(c.cov.get("super chests (DS1 580)", [])))
    R.add("windows predicted RW1 -> RW4", c.stats.get("windows predicted RW1 -> RW4 (room, object-region and game seed)", 0))
    # C1 and D3 from the lines themselves
    groups = T.groups
    prob0 = {(g, i) for g, gr in enumerate(groups) for i in range(8) if gr["ID%d" % i] and not gr["PROB%d" % i]}
    for p in paths:
        dflags, room_dr = {}, {}
        slot = None
        for tag, d, ln in events(p, ("RRESEED", "TINIT", "CB", "OG", "OS", "OK", "OH0")):
            if tag in ("RRESEED", "TINIT"):
                dflags[d["room"]] = d["f28"]
            elif tag == "CB":
                room_dr[d["room"]] = d["dr"]
            elif tag == "OG":
                keys = [k for k in ("f", "pop", "pre", "town") if k in d]
                path = "f" if d.get("f") else "pop 0" if "pop" in d and not d["pop"] else \
                    "pre" if d.get("pre") else "town" if d.get("town") else "open" if "town" in d else "?"
                R.add("gate: closed by %s" % path if path != "open" else "gate: open")
                want = {"f": ["f"], "pop 0": ["f", "pop"], "pre": ["f", "pop", "pre"],
                        "town": ["f", "pop", "pre", "town"], "open": ["f", "pop", "pre", "town"]}.get(path)
                if keys != want:
                    R.add("bad")
                    R.note("%s:%d gate keys %s for path %s" % (os.path.basename(p), ln, keys, path))
                if path != "open" and d["res"]:
                    R.add("bad")
                dr = room_dr.get(d["room"])
                if dr in dflags:
                    R.add("gate f against the DRLG room flags & 0x30000")
                    if bool(d.get("f")) != bool(dflags[dr] & 0x30000):
                        R.add("bad")
                        R.note("%s:%d gate f %s, DRLG flags %#x" % (os.path.basename(p), ln, d.get("f"), dflags[dr]))
                    elif d.get("f"):
                        R.add("gate f set on a waypoint room (flags & 0x30000)")
            elif tag == "OS":
                slot = d
                if d["g"] == 0:
                    R.add("slots that drew group 0")
                elif d["g"] in (30, 72):
                    R.add("slots that drew group %d" % d["g"])
                elif d["g"] == 69:
                    R.add("slots that drew group 69")
            elif tag == "OK" and slot is not None:
                if slot["g"] == 0:
                    R.add("bad")
                    R.note("%s:%d member pick after group 0" % (os.path.basename(p), ln))
                if slot["g"] in (30, 72, 69):
                    R.add("member picks in group %d (none can place)" % slot["g"])
            elif tag == "OH0" and slot is not None:
                if slot["g"] in (0, 30, 72, 69):
                    R.add("bad")
                    R.note("%s:%d handler after group %d" % (os.path.basename(p), ln, slot["g"]))
                gr = groups[slot["g"]]
                idx = [i for i in range(8) if gr["ID%d" % i] == d["cls"]]
                if idx and all((slot["g"], i) in prob0 for i in idx):
                    R.add("bad")
                    R.note("%s:%d PROB-0 member %d handled" % (os.path.basename(p), ln, d["cls"]))
    import drlg
    lim = drlg.exe_read(EXE, 0x00731BBC, 4)
    R.add("Gore values above 1 in objects.bin", sum(1 for o in T.objs if o["Gore"] > 1))
    R.add("g_ObjGoreLimit", lim[0])
    R.add("PROB-0 members with an id in objgroup", len(prob0))
    R.add("groups with no member", sum(1 for gr in groups if not gr["ID0"] and not any(gr["ID%d" % i] for i in range(8))))
    return R.done()


def choose(cands, total, r):
    """DRLG_PickTileByRarity's choice (3d): c = r + 1; while n > 1 and c > 0: c -= rarity(buf[i]); i += 1;
    the result is buf[i - 1], or buf[0] when i = 0. cands: [(tile id, rarity)] in candidate order."""
    i, c = 0, r + 1
    if total != 0:
        while len(cands) > 1 and c > 0:
            c -= cands[i][1]
            i += 1
    return cands[i - 1 if i else 0][0]


def chk_pick(a):
    """room-tiles rows 8, 10, 21 (spec L333, L344, L601): the candidate list (files in the room's DT1 list slot order,
    within a file newest-indexed first, at most 40) and the choice walk (3d) of DRLG_PickTileByRarity. The room-tiles
    model (tools/drlg.py Model, run_log) already predicts every pick's key and draw; here each pick also chooses its
    tile, and every entry of every activation dump (CB: the entry's tile record pointer, whose TL line names the DT1 file
    and tile index) is compared with the model's choice. Also the same with the candidates in file order (control)."""
    R = Report("pick")
    import drlg
    import dt1 as dt1mod
    paths = [p for p in log_set("cluster", a.logs) if tagged([p], "TL") and tagged([p], "TINIT")]
    files = {}

    def tiles_of(name):
        if name not in files:
            fp = os.path.join(DATA, name.replace("\\", "/").lower())
            keys = {}
            for i, t in enumerate(dt1mod.parse(open(fp, "rb").read())["tiles"]):
                keys.setdefault((t["orientation"], t["main_index"], t["sub_index"]), []).append((i, t["rarity"]))
            files[name] = keys
        return files[name]

    tidx = {}

    def tiles_of_idx(fi):
        name, i = fi
        if name not in tidx:
            fp = os.path.join(DATA, name.replace("\\", "/").lower())
            tidx[name] = dt1mod.parse(open(fp, "rb").read())["tiles"]
        t = tidx[name]
        return t[i] if i is not None and 0 <= i < len(t) else None

    for order in ("newest first", "file order"):
        bad = cmp = 0
        st = collections.Counter()
        for p in paths:
            TLm = {}
            for tag, d, ln in events(p, ("TL",)):
                TLm.setdefault(d["p"], set()).add((d["f"].lower(), d["i"]))
            TILE = {}
            LAST = [None]
            CAND = [None]
            CINFO = {}

            class PModel(drlg.Model):
                def pick(self, Rm, o, cell):
                    main, sub = (cell >> 20) & 0x3F, (cell >> 8) & 0xFF
                    s0 = Rm.seed
                    ms = drlg.Model.pick(self, Rm, o, cell)
                    cands = []
                    for name in Rm.dt1:
                        lst = tiles_of(name).get((o, main, sub), [])
                        if order == "newest first":
                            lst = lst[::-1]
                        for i, rr in lst:
                            if len(cands) < 40:
                                cands.append(((name.lower(), i), rr))
                    if not cands:
                        LAST[0] = None
                        st["picks with no candidate (the (10, 0, 0) fallback)"] += 1
                        return ms
                    total = 0
                    for _, rr in cands:
                        total = (total + rr) & 0xFFFFFFFF
                    tot = total - (1 << 32) if total & 0x80000000 else total
                    r = 0
                    if tot > 0:
                        lo = Rm.seed[0]                      # the model stepped Rm.seed for this draw
                        r = lo & (tot - 1) if tot & (tot - 1) == 0 else lo % tot
                        st["picks with a draw"] += 1
                    else:
                        st["picks with no draw (rarity sum 0)"] += 1
                    if len(cands) > 1:
                        st["picks with two or more candidates"] += 1
                    LAST[0] = choose(cands, tot, r)
                    CAND[0] = (cands, tot, r)
                    return ms

                def merge(self, Rm, N, E, o, cell, x, y):
                    before = (E.o, E.main, E.sub)
                    LAST[0] = "none"
                    drlg.Model.merge(self, Rm, N, E, o, cell, x, y)
                    if LAST[0] != "none" and (E.o, E.main, E.sub) != before or (LAST[0] != "none" and E.o == 0
                                                                                and before == (0, 30, 0)):
                        TILE[id(E)] = LAST[0]

                def cb_entries(self, path, d, rooms):
                    z = unz(d["z"])
                    for n, dr, _t, Wl, Fl, Sl in z["near"]:
                        Rr = rooms.get(dr)
                        if Rr is None or Rr.nodes is None or not Rr.built:
                            continue
                        for kind, got in (("W", Wl), ("F", Fl), ("S", Sl)):
                            mine = Rr.arr[kind]
                            for i, g in enumerate(got[:len(mine)]):
                                want = TILE.get(id(mine[i]))
                                logged = TLm.get(g[3])
                                if want is None or logged is None or len(logged) != 1:
                                    st["entries not compared (no model choice or tile record)"] += 1
                                    continue
                                lg = next(iter(logged))
                                lt = tiles_of_idx(lg)
                                if lt is not None and lt["animated"] and Rr.type == 2 and (Rr.preset or {}).get("animate"):
                                    # AnimTilesBuild (sub_0066D440) gives an animated entry the tile of its rarity-0
                                    # frame after the pick: compared with that rule instead
                                    st["animated entries of Animate rooms: the tile is a rarity-0 frame"
                                       if lt["rarity"] == 0 else "animated entries of Animate rooms: rarity not 0"] += 1
                                    continue
                                st["entries compared"] += 1
                                if want != lg:
                                    st["entries whose tile differs"] += 1
                                    if a.verbose and order == "newest first":
                                        ci = CINFO.get(id(mine[i]))
                                        lg = next(iter(logged))
                                        pos = [c[0] for c in ci[0]].index(lg) if ci and lg in [c[0] for c in ci[0]] else None
                                        st["diff kind %s o %d merged %d ncand %s pos %s main %d sub %d tot %s r %s mypos %s file %s" % (kind, mine[i].o,
                                           bool(mine[i].merged), len(ci[0]) if ci else None, pos, mine[i].main, mine[i].sub,
                                           ci[1] if ci else None, ci[2] if ci else None,
                                           [c[0] for c in ci[0]].index(want) if ci else None, lg[0].split("\\")[-1])] += 1
                    return drlg.Model.cb_entries(self, path, d, rooms)

            orig_init = drlg.Entry.__init__

            def entry_init(self, *args, orig_init=orig_init):
                orig_init(self, *args)
                TILE[id(self)] = LAST[0]
                CINFO[id(self)] = CAND[0]

            m = PModel(drlg.Data(DATA, EXE), False)
            with patched(drlg.Entry, "__init__", entry_init):
                with quiet():
                    drlg.run_log(m, p)
            st["roomk model mismatches"] += m.fail
            st["model: (10, 0, 0) fallbacks"] += m.cov.get("pick: (10,0,0) fallback", 0)
        for k, v in st.items():
            R.add("%s: %s" % (order, k), v)
        if order == "newest first" and (st["entries whose tile differs"] or st["roomk model mismatches"]
                                        or st["animated entries of Animate rooms: rarity not 0"]):
            R.add("bad")
    R.add("logs", len(paths))
    return R.done()


def chk_roomk(a):
    """room-tiles rows 4, 5, 12, 13, 14, 16, 26, 28, 37 (spec L77, L306, L427-L428, L493, L578, L626, L645, L884), with the
    room-tiles model (tools/drlg.py Model, run_log) over every log with roomk lines (run:2026-10-11-drlg-roomk,
    run:2026-10-14-collision, run:2026-10-15-objects; each room's seed checked at RACT, so k):
      * the bit-2 merge branches the model took (the row table g_Bit2OrientRow and the orientation table
        g_Bit2OrientMerge read from the pinned game.exe; the 8/9 edge rule; row -1 and row -2; E.o above 7);
      * rooms of preset Defs 1 and 108 (the extra zero-filled grid) and Animate rooms whose k was checked;
      * ActivateRoom's order: PLDX (+0x28 after PresetRoomLoadDs1) holds 0x1000000 (the DT1 list is built first) and
        every TINIT of a type-2 room holds 0x1000000 and 0x2000000 with its neighbour states;
      * the DS1 is File(idx + 1): every PRC line's file against LvlPrest.File[idx] (no draw chooses it: drlg/0003)."""
    R = Report("roomk")
    import drlg
    paths = [p for p in log_set("cluster", a.logs) if tagged([p], "TINIT")]
    cov = collections.Counter()
    rooms = collections.Counter()
    fail = 0

    class KModel(drlg.Model):
        def tiles_build(self, Rm, d):
            if Rm.type == 2 and Rm.preset:
                if Rm.preset.get("def") in (1, 108):
                    rooms["type-2 rooms of Def %d built (k checked at RACT)" % Rm.preset["def"]] += 1
                if Rm.preset.get("animate"):
                    rooms["type-2 rooms with Animate 1 built (k checked at RACT)"] += 1
            return drlg.Model.tiles_build(self, Rm, d)

    for p in paths:
        m = KModel(drlg.Data(DATA, EXE), False)
        with quiet():
            drlg.run_log(m, p)
        fail += m.fail
        for k, v in m.cov.items():
            if k.startswith("bit-2 merge"):
                cov[k] += v
    for k, v in sorted(cov.items()):
        R.add(k, v)
    for k, v in rooms.items():
        R.add(k, v)
    R.add("roomk model mismatches", fail)
    if fail:
        R.add("bad")
    for p in log_set("cluster", a.logs):
        for tag, d, ln in events(p, ("PLDX", "TINIT")):
            if tag == "PLDX":
                R.add("PLDX with the DT1-list flag 0x1000000" if d["f28"] & 0x1000000 else "bad")
            elif d["type"] == 2:
                ok = d["f28"] & 0x3000000 == 0x3000000
                R.add("type-2 TINIT with 0x1000000 and 0x2000000" if ok else "bad")
                if d.get("nbstate"):
                    R.add("TINIT with the neighbour list in place")
    files = [drlg.LvlPrest(r).files for r in excel_rows("lvlprest")]
    for p in log_set("cluster", a.logs):
        for tag, d, ln in events(p, ("PRC",)):
            want = files[d["def"]][d["idx"]] if 0 <= d["idx"] < 6 else None
            got = d["file"].replace("\\", "/").lower()
            ok = want is not None and got == "data/global/tiles/" + want.replace("\\", "/").lower()
            R.add("PRC file = LvlPrest File(idx + 1)" if ok else "bad")
            if not ok:
                R.note("%s:%d PRC Def %d idx %d file %s, table %s" % (os.path.basename(p), ln, d["def"], d["idx"],
                                                                     d["file"], want))
    return R.done()


def chk_outroom(a):
    """README rows 6, 8, 15, 16 and outdoor row 16 (spec L263, L299, L382, L396; outdoor L983), counted from tools/drlg.py
    gen over the gen-family logs (run:2026-10-12-drlg-gen, run:2026-10-15-drlg-maze, run:2026-10-15-drlg-outdoor,
    run:2026-10-15-acts-3-5):
      * every out room's rect (x = L.x + 8 cx, y = L.y + 8 cy) and creation order, and the seed after every window and
        build (the position passes no draw);
      * the maze builds (LI1: the level seed at the end of each build) whose rooms carry room-adjacency nodes (+0x0C = 1,
        RoomAdjAdd) that MazeLevelRooms passes to 0x0066B5E0;
      * the maze rotation counters: first uses and rotations, in rebuilt levels too;
      * the outdoor windows of levels 41, 45 and 46 checked draw by draw (ODD), with no waypoint pass in the model."""
    R = Report("outroom")
    import drlg
    m, rk, bad = run_gen(gen_logs(a))
    for k in ("out rooms predicted (rect, creation order)", "maze preset rotation: first use, RangeB(level seed, Files)",
              "maze preset rotation: (counter + 1) % Files", "LevelInit (DrlgType 1)", "LevelInit (DrlgType 3)",
              "maze windows modelled: difficulty 0", "maze windows modelled: difficulty 1", "maze windows modelled: difficulty 2"):
        R.add(k, m.cov.get(k, 0))
    for lv in (41, 45, 46):
        R.add("outdoor windows of level %d" % lv, m.cov.get("outdoor windows modelled: level %d" % lv, 0))
    n = 0
    for p in gen_logs(a):
        for tag, d, ln in events(p, ("ODD",)):
            if d["id"] in (41, 45, 46):
                n += 1
    R.add("ODD lines (every level-seed step) of levels 41, 45, 46", n)
    R.add("gen mismatches", bad)
    if bad:
        R.add("bad")
    return R.done()


def chk_nww(a):
    """warps row 14 (spec L374): the type-11 point NearWarpTest takes from ActLevelPointFind / LevelPointFind (NWW, the
    point in tiles; run:2026-10-14-collision, run:2026-10-15-objects). Read again for this batch (0x0066B2B0): with the
    level's Position (leveldefs +0x90) set, LevelPointPick takes the point from the level's point list, whose type-11
    entries DRLG_PresetMapScan makes from slot-33 cells (orientation 10/11, main index 33) of a preset; with Position 0,
    LevelWaypointRoom (0x0066AD80) takes the first waypoint-flagged room and the tile of the first waypoint object
    (type 2, id < 0x23D, Objects SubClass bit 0x40) of its preset unit list, unit / 5 + the room's tile origin. Each
    distinct NWW point is looked up among the slot-33 cells and the waypoint objects of the preset instances (PRC) of
    the same log, and split by the Position of the level whose instance holds it."""
    R = Report("nww")
    import drlg
    data = drlg.Data(DATA, EXE)
    pu = drlg.PresetUnitData(DATA, EXE)
    sub = [struct.unpack_from("<B", r, 0x167)[0] for r in excel_rows("objects")]
    h, rows = _tsv("levels.txt")
    pos = {int(r[h.index("Id")]): int(r[h.index("Position")] or 0) for r in rows if r[h.index("Id")].strip().isdigit()}
    paths = tagged(log_set("collision", a.logs) + log_set("objects", a.logs), "NWW")
    for p in paths:
        pts = set()
        inst = set()
        lid = {}
        cur, rl, opu = None, {}, {}
        for tag, d, ln in events(p, ("NWW", "PRC", "LC0", "CB", "SN", "OPU0")):
            if tag == "NWW":
                if d["x"] > 0 and d["y"] > 0:
                    pts.add((d["x"], d["y"], cur))
            elif tag == "CB":
                rl[d["room"]] = d["lid"]
            elif tag == "SN":
                cur = rl.get(d["room"])
            elif tag == "OPU0":
                if d["type"] == 2 and 0 <= d["id"] < 0x23D and sub[d["id"]] & 0x40:
                    opu[(d["x"] // 5, d["y"] // 5)] = d.get("lid")
            elif tag == "LC0":
                lid[d["level"]] = d["id"]
            else:
                inst.add((d["def"], d["idx"], tuple(d["prect"]), lid.get(d["level"])))
        s33, wpo = {}, {}
        for dfn, idx, pr, lv in inst:
            f = data.lvlprest[dfn].files[idx] if 0 <= idx < 6 else "0"
            if f in ("", "0"):
                continue
            P = data.preset_pristine(f)
            cols = P["cols"]
            sx, sy = P["size"]
            for walls, orients in zip(P["walls"], P["orients"]):
                for y in range(sy):
                    for x in range(sx):
                        k = y * cols + x
                        if orients[k] in (10, 11) and (walls[k] >> 20) & 0x3F == 33:
                            s33[(pr[0] + x, pr[1] + y)] = lv
            for u in pu.ds1(f)["units"]:
                if u[0] == 2 and 0 <= u[1] < 0x23D and sub[u[1]] & 0x40:
                    wpo.setdefault((pr[0] + u[3] // 5, pr[1] + u[4] // 5), lv)
        wpo.update(opu)
        for x, y, lv in pts:
            pt = (x, y)
            kind = "slot-33 cell" if pt in s33 else "waypoint object tile" if pt in wpo else None
            ps = pos.get(lv)
            if kind is None:
                R.add("points on neither, level Position %s" % ("set" if ps else "0"))
                R.note("%s: level %s Position %s: NWW point %s on neither (no PRC/OPU0 source in this log)"
                       % (os.path.basename(p), lv, ps, pt))
                continue
            R.add("distinct NWW points, level Position %s: %s" % ("set" if ps else "0", kind))
            if (ps and kind != "slot-33 cell") or (not ps and kind != "waypoint object tile"):
                R.add("bad")
                R.note("%s: level %s Position %s, point %s is a %s" % (os.path.basename(p), lv, ps, pt, kind))
            else:
                R.levels = getattr(R, "levels", set()) | {(lv, ps)}
    R.add("logs", len(paths))
    R.note("levels (id, Position): %s" % sorted(getattr(R, "levels", set()), key=str))
    return R.done()


def chk_warpunit(a):
    """warps row 18 (spec L460): sub_0066E1C0_WarpUnitAdd makes a preset unit of type 5 whose class is the LvlWarp Id, at
    the warp cell's subtile (room-relative tile x 5) plus OffsetX/OffsetY (+0x1C/+0x20). Every type-5 unit of the server
    walks (RPU, run:2026-10-13-drlg-preset, run:2026-10-15-acts-3-5) is matched to a warp cell of the room's preset
    instance (PRC: Def, file index, rect; the DS1's wall cells of orientation 10/11 with a main index below 8): the unit
    must sit at that cell's subtile plus the offsets of a LvlWarp row with its id, of the cell's direction ('l' for 10,
    'r' for 11, or 'b')."""
    R = Report("warpunit")
    import drlg
    data = drlg.Data(DATA, EXE)
    lw = [(struct.unpack_from("<i", r, 0)[0], struct.unpack_from("<i", r, 0x1C)[0], struct.unpack_from("<i", r, 0x20)[0],
           r[0x2C:0x2D].decode("latin-1")) for r in excel_rows("lvlwarp")]
    for p in log_set("preset", a.logs) + log_set("acts35", a.logs):
        rect = {}
        warp = {}
        for tag, d, ln in events(p, ("RL", "PRC", "RPU")):
            if tag == "RL":
                rect[d["room"]] = d["rect"]
            elif tag == "PRC":
                f = data.lvlprest[d["def"]].files[d["idx"]] if 0 <= d["idx"] < 6 else "0"
                if f in ("", "0"):
                    continue
                P = data.preset_pristine(f)
                cols, (sx, sy) = P["cols"], P["size"]
                for walls, orients in zip(P["walls"], P["orients"]):
                    for y in range(sy + 1):
                        for x in range(sx + 1):
                            k = y * cols + x
                            if k < len(orients) and orients[k] in (10, 11) and (walls[k] >> 20) & 0x3F < 8:
                                warp[(d["prect"][0] + x, d["prect"][1] + y)] = orients[k]
            else:
                rc = rect.get(d["room"])
                for u in d["rlist"]:
                    if u[1] != 5:
                        continue
                    R.add("type-5 units in the walks")
                    if rc is None:
                        R.add("type-5 units in a room with no RL line (not compared)")
                        continue
                    ok = False
                    for wid, ox, oy, dr in lw:
                        if wid != u[2] or (u[4] - ox) % 5 or (u[5] - oy) % 5:
                            continue
                        t = (rc[0] + (u[4] - ox) // 5, rc[1] + (u[5] - oy) // 5)
                        o = warp.get(t)
                        if o is not None and (dr == "b" or dr == ("l" if o == 10 else "r")):
                            ok = True
                            break
                    R.add("type-5 units at a warp cell's subtile + the LvlWarp row's offsets (class = its Id)" if ok
                          else "bad")
                    if not ok:
                        R.note("%s:%d room %08x unit id %d at (%d, %d)" % (os.path.basename(p), ln, d["room"], u[2], u[4],
                                                                          u[5]))
    return R.done()


def chk_orpath(a):
    """collision row 7 (spec L186): COLL_MapBuild always stamps with the OR form (COLL_StampTile), never the overwrite
    form COLL_SetTile. Every activation dump (CB) of run:2026-10-14-collision and run:2026-10-15-objects is rebuilt twice
    from its tile entries (DT1 sub-tile bytes from the TL records' files, in the entries' order): with OR, as the
    checker does, and with each stamp overwriting its 25 cells; the logged cells must equal the OR build, and the count
    of dumps where the overwrite build would differ shows that the logs can tell them apart."""
    R = Report("orpath")
    import collision
    paths = tagged(log_set("collision", a.logs) + log_set("objects", a.logs), "CB")
    for p in paths:
        tiles = collision.TileDB(DATA)
        for tag, d, ln in events(p, ("TL", "CB")):
            if tag == "TL":
                tiles.add(d)
                continue
            z = unz(d["z"])
            if z["cells"][4] is None:
                continue
            x0, y0, w, h = d["rect"]
            c_or, c_set = [0] * (w * h), [0] * (w * h)
            flags = []
            try:
                for n, _dr, trect, Wl, Fl, Sl in z["near"]:
                    tx, ty = trect[0], trect[1]
                    for lst in (Fl, Wl, Sl):
                        for x, y, fl, tp, _o in lst:
                            sx, sy = (x + tx) * 5, (y + ty) * 5
                            if not (x0 <= sx < x0 + w and y0 <= sy < y0 + h) or not tp:
                                continue
                            row, col = sy - y0, sx - x0
                            b = tiles.bytes_of(tp)
                            collision.stamp(c_or, w, row, col, b)
                            for r_ in range(5):
                                for cc in range(5):
                                    i = (row + r_) * w + col + cc
                                    if 0 <= i < len(c_set):
                                        c_set[i] = b[(4 - r_) * 5 + cc]
                            v = (0x10 if fl & 0x02 else 0) | (0x01 if fl & 0x40 else 0) | (0x04 if fl & 0x80 else 0)
                            if v:
                                flags.append((row, col, v))
            except collision.CollMismatch:
                R.add("dumps with a tile not logged (not compared)")
                continue
            for row, col, v in flags:
                collision.or_block(c_or, w, row, col, v)
                collision.or_block(c_set, w, row, col, v)
            logged = u16cells(z["cells"][4])
            R.add("activation dumps")
            if logged != c_or:
                R.add("bad")
            if c_set != c_or:
                R.add("dumps where the overwrite form would differ")
                R.add("cells where the overwrite form would differ", sum(1 for q, r_ in zip(c_set, c_or) if q != r_))
    R.add("logs", len(paths))
    return R.done()


CHECKS = {}


def register(*fns):
    for f in fns:
        CHECKS[f.__name__[4:]] = f


register(chk_ltype, chk_lsr, chk_expansion, chk_lnks, chk_tl, chk_lc1, chk_odg, chk_maze, chk_r0, chk_wgen, chk_adj,
         chk_placefar, chk_logic, chk_barrier, chk_flood, chk_bits, chk_pflags, chk_dispatch, chk_punits, chk_kill, chk_l27, chk_pcopies, chk_objects, chk_pick, chk_roomk, chk_outroom, chk_nww, chk_warpunit, chk_orpath)


class Args:
    def __init__(self, argv):
        self.logs, self.verbose = None, False
        it = iter(argv)
        self.rest = []
        for x in it:
            if x == "--logs":
                self.logs = next(it)
            elif x == "-v":
                self.verbose = True
            else:
                self.rest.append(x)


def main(argv):
    if len(argv) < 2 or (argv[1] not in CHECKS and argv[1] != "all"):
        print(__doc__)
        print("checks: " + " ".join(sorted(CHECKS)))
        return 2
    a = Args(argv[2:])
    names = sorted(CHECKS) if argv[1] == "all" else [argv[1]]
    rc = 0
    for n in names:
        rc |= CHECKS[n](a)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""Object population, placement, creation rolls and the chest operate path, checked against runtime logs (plan 0023).

Usage:
  python3 -I tools/objects.py window <run.log> [...] [--excel DIR] [-v]                 # Phase 1 room-seed accounting
  python3 -I tools/objects.py check  <run.log> [...] [--excel DIR] [--root DIR] [-v]    # Phase 2 bit-exact model

`window` reads any log written by tools/d2run.py with tools/gdb/mon-spawn.gdb, collision.gdb, mon-special.gdb or
objects.gdb: they log the room seed (rs, low:high) and game seed (gs) after each out-of-scope call of the room driver,
RW1 (wanderer tick) .. RW4 (object population). It enumerates the unknowns of the objects window (gate, forced flag,
placement attempts, caps, InitFn 46's draws) and requires the logged RW4 room seed to be reached; "exact" rooms needed
no unknown besides the gate.

`check` reads logs written with tools/gdb/objects.gdb (the tags of tools/gdb/objects.py on top of mon-special.gdb's) and
runs the model of docs/findings/objects/0001-object-population.md, written from the code, on three seeds: the
active-room seed (room +0x6C), the object-region seed (*(game +0x10F0), built at game creation from game-seed draw 2)
and the game seed (+0xD0), plus each object's unit seed (+0x20). Tables are the .bin files the game loads (levels,
objgroup, objects, shrines), decoded with tools/excel_layouts.py, from --excel.

  * The object-region seed is predicted from OGC (Init(low of the game-seed step)) and carried across every presets
    window, every objects window and every operate, in log order. Every draw on it is a watchpoint line (OD: pc and
    the new low word); the model consumes one OD per draw and compares the low word, so a draw the model does not make,
    or makes and the game does not, is a mismatch at the draw where it happens. An OD line outside a modelled scope is
    a mismatch ("stray object-region draw").
  * The presets window (RW1 -> RW2, PresetUnitDispatch OPU0 .. OPUX): an object (type 2, id < 573) is SUnitCreate
    (one game-seed step for the unit seed; OBJ_ServerInit: the InitFn, the PreOperate Range(O, 14)), ids 580 / 581 /
    582 the pseudo-objects (582's class is quest state, taken from the log); any other preset unit (monsters) is a seed
    oracle: the room, object-region and game seeds are asserted at its OPU0 and taken at its OPUX.
  * RW2 -> RW3 (the inactive-unit restore) draws nothing.
  * RW3 -> RW4, sub_00552610_RoomObjectsPopulate: the gate (the room-flag test, RoomPopLevelId, the preset test and the
    town test are DRLG inputs taken from the OG line; a town must close it; roomsVisited and roomCount are tracked per
    population level, roomCount taken when first read and checked after), the theme roll on the object-region seed, the
    eight slots and the forced-shrine rule from the tracked counters (checked against the OS lines), the member pick
    (OK), and the ten PopulateFn handlers with their placement helpers: every COLL_WHTest call (site, position, box,
    mask) is predicted and compared with its OT line, and its result is taken from the line (a value oracle, counted).
  * Creation: SUnitCreate class, position, flags and mode (OU0) and the unit's seed, mode, interact byte and sparkle
    flag at OIX / OUX; the InitFn draws (1 shrine, 2 trap byte, 3 chest lock and re-seed, 57 sparkly chest, 27, 28 gold
    piles with the gold drop as a seed oracle, 34, 58); the monster-spawning and quest InitFns (46, 47, 54, 55, 62, 66,
    68, 69, 79) are seed oracles (seeds asserted at OI0 and taken at OIX). A mode change draws RangeB(unit seed,
    FrameDelta[mode] >> 3) when Sync is 0 (UNIT_AnimInit).
  * Operate (OO0 .. OOX): OperateFn 1 (casket), 3 (urn), 4 (chest: the sparkle quality, the 25 % empty chest, locked
    chests, the class-397 table) and 5 (barrel) on the object-region seed up to each ObjectChestDrop: the forced quality
    and the object's unit seed are checked at OC0 and OCT, the TC is recorded (and must be an act chest TC),
    TC_ResolveDrops is a seed oracle (unit and game seeds taken at OCX; the object-region seed must not move). The
    monster spawns of caskets and barrels are seed oracles. Other OperateFns must leave the object-region seed alone.

The last lines are counters, oracles and the coverage the plan asks for. Exit 0 only if every check holds. Stdlib only.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from obj_survey import decode, txt_col  # noqa: E402

M = 0x6AC690C5
INIT_HIGH = 666
TOWNS = {1, 40, 75, 103, 109}
ORACLE_INITFNS = {46, 47, 54, 55, 62, 66, 68, 69, 79}
MODELLED_INITFNS = {1, 2, 3, 27, 28, 34, 57, 58}
INIT_TABLE = (set(range(1, 80)) - {35, 36, 40})       # g_ObjInitFns 0x00731BC0: the non-null entries
CLUSTER = {3: ([3, 28], 18, 5, 5, False), 1: ([79, 53, 1], 12, 5, 5, False), 79: ([79, 53, 1], 12, 5, 5, False),
           4: ([4, 9, 52, 94, 95], 12, 0, 1, True), 89: ([89, 284], 12, 5, 5, False),
           208: ([208, 209], 12, 0, 1, True), 209: ([208, 209], 12, 0, 1, True)}   # g_ObjClusterLists 0x00731D50
CRATE_LIST = [4, 9, 52, 94, 95]
DX = [-1, 0, 1, -1, 1, -1, 0, 1]          # g_ObjDir8X 0x00731B7C
DY = [-1, -1, -1, 0, 0, 1, 1, 1]          # g_ObjDir8Y 0x00731B9C
STICK = [[(-4, 0), (0, 0), (4, 0), (8, 0), (0, 4), (0, -4)], [(-8, 0), (-4, 0), (0, 0), (4, 0), (8, 0)],
         [(0, -8), (0, -4), (0, 0), (0, 4), (0, 8)], [(-7, -5), (-5, -3), (-3, -1), (0, 0), (3, -1), (5, -3), (7, -5)]]
CHEST581 = [5, 6, 139, 140, 141, 144, 176, 177, 198, 240, 241, 242, 243]
SITE_GOLD, SITE_PAD1, SITE_PAD2, SITE_TIGHT, SITE_PLACE, SITE_PLACERS, SITE_ORIENT = (
    0x0054F99D, 0x0055029E, 0x005502BA, 0x00550355, 0x005504B3, 0x0055062D, 0x00550B89)


def step(s):
    v = s[0] * M + s[1]
    return (v & 0xFFFFFFFF, v >> 32)


def parse_seed(t):
    a, b = t.split(":")
    return (int(a, 16), int(b, 16))


def fmt(s):
    return "%08x:%08x" % s if s else "None"


def s32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


def idiv(a, b):
    """C signed division (truncation towards zero)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def solve(s0, s1, lv, groups, objs, forced, forced_due=True):
    """All ways the slot loop can turn s0 into s1; each is (branched, trace). With forced_due False the shrine handler
    is bounded by the Phase 2 model (3 tries of OBJ_PlaceByOrientation, 5 attempts each, 2 room draws per attempt)."""
    sols = []

    def run(s, k, branched, trace):
        if k == 8:
            if s == s1:
                sols.append((branched, trace))
            return
        s = step(s)
        r = s[0] % 100
        g, p = lv["ObjGrp%d" % k], lv["ObjPrb%d" % k]
        if forced and objs[g]["SubClass"] != 0:
            r = 100
        if g == 0 or r > p:
            return run(s, k + 1, branched, trace)
        s = step(s)
        r2 = s[0] % 100
        gr = groups[g]
        cum, oid, fn = 0, None, None
        for i in range(8):
            o = gr["ID%d" % i]
            if o == 0:
                break
            cum += gr["PROB%d" % i]
            if r2 < cum and objs[o]["Gore"] <= 2:
                oid, fn = o, objs[o]["PopulateFn"]
                break
        tr = trace + [(k, g, oid, fn)]
        if oid is not None and objs[oid]["InitFn"] == 46:
            t = s
            for e in range(800):
                run(t, k + 1, True, tr + [("init46", e)])
                t = step(t)
            return
        if fn == 2:
            t = step(s)
            for a in range(151 if forced_due else 16):     # 3 tries x 5 attempts, 30 x 5 when the health shrine is due
                run(t, k + 1, True, tr + [("shrine", a)])
                t = step(step(t))
            return
        if fn == 8:
            run(s, k + 1, True, tr + [("wellcap",)])
            t = step(s)
            for a in range(6):
                run(t, k + 1, True, tr + [("well", a)])
                t = step(step(t))
            return
        if fn == 9:
            s = step(s)
        return run(s, k + 1, branched, tr)

    run(s0, 0, False, [])
    return sols


def cmd_window(argv):
    excel, verbose, logs = "workspace/merged/data/global/excel", False, []
    it = iter(argv)
    for a in it:
        if a == "--excel":
            excel = next(it)
        elif a == "-v":
            verbose = True
        else:
            logs.append(a)
    levels, groups, objs = decode(excel, "levels"), decode(excel, "objgroup"), decode(excel, "objects")
    st = dict(logs=len(logs), rooms=0, restore_checked=0, restore_moved=0, closed=0, closed_town=0, exact=0,
              branched=0, forced=0, fail=0, slot_passes=0, member_none=0, shrine=0, well=0, trap=0, init46=0,
              other_handlers=0, shrine_due=0)
    for path in logs:
        rw = {}
        for line in open(path, errors="replace"):
            if not line.startswith("RW"):
                continue
            tag, js = line.split(" ", 1)
            try:
                d = json.loads(js)
            except ValueError:
                continue
            rw[tag] = d
            if tag == "RW3" and "RW2" in rw and rw["RW2"]["room"] == d["room"]:
                st["restore_checked"] += 1
                if (rw["RW2"]["rs"], rw["RW2"]["gs"]) != (d["rs"], d["gs"]):
                    st["restore_moved"] += 1
                    print("RESTORE-MOVED", os.path.basename(path), d["room"])
            if tag != "RW4" or "RW3" not in rw or rw["RW3"]["room"] != d["room"]:
                continue
            st["rooms"] += 1
            s0, s1, lid = parse_seed(rw["RW3"]["rs"]), parse_seed(d["rs"]), d["lid"]
            if s0 == s1:
                st["closed"] += 1
                st["closed_town"] += lid in TOWNS
                continue
            if lid in TOWNS:
                st["fail"] += 1
                print("FAIL town window drew", os.path.basename(path), d["room"], lid)
                continue
            sols = solve(s0, s1, levels[lid], groups, objs, False, False)
            if not sols:
                sols = solve(s0, s1, levels[lid], groups, objs, False, True)
                if sols:
                    st["shrine_due"] += 1
            if not sols:
                sols = solve(s0, s1, levels[lid], groups, objs, True)
                if sols:
                    st["forced"] += 1
                    if verbose:
                        print("FORCED", os.path.basename(path), d["room"], lid)
            if not sols:
                st["fail"] += 1
                print("FAIL", os.path.basename(path), d["room"], "lid", lid, rw["RW3"]["rs"], d["rs"])
                continue
            branched, trace = sols[0]
            st["branched" if branched else "exact"] += 1
            for t in trace:
                if len(t) == 4:
                    st["slot_passes"] += 1
                    if t[2] is None:
                        st["member_none"] += 1
                    elif objs[t[2]]["InitFn"] == 46:
                        st["init46"] += 1
                    elif t[3] == 2:
                        st["shrine"] += 1
                    elif t[3] == 8:
                        st["well"] += 1
                    elif t[3] == 9:
                        st["trap"] += 1
                    else:
                        st["other_handlers"] += 1
            if verbose:
                print("ROOM", os.path.basename(path), d["room"], lid, "exact" if not branched else "branched", trace)
    print("objects-window: " + " ".join("%s=%d" % kv for kv in st.items()))
    return 1 if st["fail"] or st["restore_moved"] else 0


# ======================================================================================================================
# Phase 2 model
# ======================================================================================================================

class Mismatch(Exception):
    pass


OBJ_TAGS = {"OGC", "OD", "OG", "OS", "OK", "OH0", "OHX", "OT", "OPU0", "OPUX", "OU0", "OUX", "OI0", "OIX", "OGP0",
            "OGPX", "OO0", "OOX", "OC0", "OCT", "OCX", "RW0", "RW1", "RW2", "RW3", "RW4", "P0"}
PASS_TAGS = ("HDR", "GAME", "RW0", "P0")


class Tables:
    def __init__(self, excel):
        self.levels = decode(excel, "levels")
        self.groups = decode(excel, "objgroup")
        self.objs = decode(excel, "objects")
        self.shrines = decode(excel, "shrines")
        for o in self.objs:
            o["Xspace"] &= 0xFF
            o["Yspace"] &= 0xFF
        self.shrine_lists = {c: [i for i, r in enumerate(self.shrines) if r["effectclass"] == c] for c in range(8)}
        try:
            self.tc_names = txt_col(excel, "treasureclassex", "Treasure Class")
        except Exception:
            self.tc_names = []


class Seed:
    """A predicted seed; `od` is the checker's OD consumer for the object-region seed (None for the others)."""

    def __init__(self, s, name, od=None):
        self.s, self.name, self.od = s, name, od

    def draw(self):
        self.s = step(self.s)
        if self.od is not None:
            self.od(self.s)
        return self.s[0]

    def rng(self, n):
        """RNG_Range / RNG_RangeB: 0 without a draw when n < 1, else low mod n (low & (n-1) for a power of two)."""
        n = s32(n)
        if n < 1:
            return 0
        return self.draw() % n

    def p100(self):
        return self.draw() % 100

    def lohi(self, lo, hi):
        """RNG_RandLoHi 0x004BC500."""
        if hi <= lo:
            return lo
        return lo + self.draw() % (hi - lo)


class Checker:
    def __init__(self, excel, root, verbose):
        self.t = Tables(excel)
        self.root, self.verbose = root, verbose
        self.checks = self.fail = 0
        self.stats = {}
        self.oracles = {}
        self.cov = {}
        self.msgs = []
        self.pred_rw4 = set()     # (log, line) of every RW4 the model reached with all three seeds predicted

    # --- bookkeeping --------------------------------------------------------------------------------------------
    def hit(self, k, n=1):
        self.stats[k] = self.stats.get(k, 0) + n

    def oracle(self, k):
        self.oracles[k] = self.oracles.get(k, 0) + 1

    def ok(self, cond, msg):
        self.checks += 1
        if not cond:
            raise Mismatch(msg)

    def covk(self, k, item):
        self.cov.setdefault(k, []).append(item)

    # --- the line stream ----------------------------------------------------------------------------------------
    def load(self, path):
        lines = []
        for ln, line in enumerate(open(path, errors="replace"), 1):
            tag, _, rest = line.partition(" ")
            if tag == "LOGERR":
                lines.append(("LOGERR", {"text": rest.strip()}, ln))
            elif line.startswith("# d2run seed="):
                lines.append(("HDR", {"text": line.strip()}, ln))
            elif tag == "GAME":
                lines.append(("GAME", {"text": rest.strip()}, ln))
            elif tag in OBJ_TAGS:
                try:
                    lines.append((tag, json.loads(rest), ln))
                except ValueError:
                    pass
        return lines

    def peek_tag(self):
        j = self.i
        while j < len(self.L) and self.L[j][0] in PASS_TAGS:
            j += 1
        return self.L[j][0] if j < len(self.L) else None

    def next_obj(self, want):
        """The next object line; it must carry the tag `want` (a string or a set)."""
        wants = want if isinstance(want, (set, frozenset)) else {want}
        while self.i < len(self.L):
            tag, d, ln = self.L[self.i]
            if tag in PASS_TAGS:
                if tag == "P0":
                    self.room_lid[d["room"]] = d["lid"]
                    self.de = (d["diff"], d["exp"])
                self.i += 1
                continue
            if tag == "LOGERR":
                self.i += 1
                raise Mismatch("logger error at line %d: %s" % (ln, d["text"]))
            if tag not in wants:
                raise Mismatch("line %d: expected %s, got %s %s" % (ln, "/".join(sorted(wants)), tag, json.dumps(d)[:160]))
            self.i += 1
            self.ln = ln
            return tag, d
        raise Mismatch("log ended while expecting %s" % "/".join(sorted(wants)))

    def od(self, s):
        """One object-region draw: the next object line must be its OD."""
        if not self.watch:
            return
        tag, d = self.next_obj("OD")
        self.n_od += 1
        self.ok(int(d["lo"], 16) == s[0], "line %d: object-region draw low %s, model %08x (pc %08x)"
                % (self.ln, d["lo"], s[0], d["pc"]))
        self.pcs[d["pc"]] = self.pcs.get(d["pc"], 0) + 1

    def seeds_eq(self, d, what, rs=True, os_=True, gs=True):
        if rs and self.rs is not None and d.get("rs") is not None:
            self.ok(parse_seed(d["rs"]) == self.rs.s, "line %d: %s room seed %s, model %s" % (self.ln, what, d["rs"], fmt(self.rs.s)))
        if os_ and d.get("os") is not None:
            self.ok(parse_seed(d["os"]) == self.O.s, "line %d: %s object-region seed %s, model %s" % (self.ln, what, d["os"], fmt(self.O.s)))
        if gs and self.G is not None and d.get("gs") is not None:
            self.ok(parse_seed(d["gs"]) == self.G.s, "line %d: %s game seed %s, model %s" % (self.ln, what, d["gs"], fmt(self.G.s)))

    def take(self, d, rs=True, gs=True, os_=True):
        if rs and d.get("rs") is not None and self.rs is not None:
            self.rs.s = parse_seed(d["rs"])
        if gs and d.get("gs") is not None:
            self.G = Seed(parse_seed(d["gs"]), "game")
        if os_ and d.get("os") is not None:
            self.O.s = parse_seed(d["os"])

    def skip_until(self, tag, oracle_name):
        """A seed oracle: skip every line up to `tag` (OD lines included)."""
        n = 0
        while self.i < len(self.L):
            tg, d, ln = self.L[self.i]
            self.i += 1
            if tg == tag:
                self.ln = ln
                self.oracle(oracle_name)
                if n:
                    self.hit("object-region draws inside oracle '%s'" % oracle_name, n)
                return d
            if tg == "OD":
                n += 1
        raise Mismatch("log ended inside oracle %s" % oracle_name)

    # --- run one log --------------------------------------------------------------------------------------------
    def run(self, path):
        self.path = path
        self.L = self.load(path)
        self.i = self.ln = 0
        self.O = self.G = self.rs = None
        self.watch = False
        self.n_od = 0
        self.pcs = {}
        self.units = {}           # unit pointer -> model unit
        self.room_lid = {}
        self.de = None
        self.lvl = {}             # population level -> counters
        chk0, fail0 = self.checks, self.fail
        while self.i < len(self.L):
            tag, d, ln = self.L[self.i]
            self.ln = ln
            self.i += 1
            try:
                if tag == "OGC":
                    self.ev_ogc(d)
                elif tag == "RW1":
                    self.window(d)
                elif tag == "OO0":
                    self.operate(d)
                elif tag == "OPU0":
                    self.lone_preset(d)
                elif tag == "P0":
                    self.room_lid[d["room"]] = d["lid"]
                    self.de = (d["diff"], d["exp"])
                elif tag == "OD":
                    self.stray(d, ln)
                elif tag == "LOGERR":
                    raise Mismatch("logger error at line %d: %s" % (ln, d["text"]))
            except Mismatch as e:
                self.fail += 1
                self.msgs.append("%s: %s" % (os.path.basename(path), e))
                print("MISMATCH %s: %s" % (os.path.basename(path), e))
                self.resync()
        print("%s: %d checks, %d mismatches, %d object-region draws matched" % (
            os.path.basename(path), self.checks - chk0, self.fail - fail0, self.n_od))
        if self.verbose:
            print("  draw sites %s" % {"%08x" % k: v for k, v in sorted(self.pcs.items())})

    def stray(self, d, ln):
        """An object-region draw outside the populate and operate scopes. The object timer events (the twelve callbacks of
        the table at 0x006E19B0, 0x00581250 .. 0x00581AFF and 0x00585CE0 / 0x00586850) draw it while the game runs;
        they are game simulation (ADR-0002): the draw is stepped and compared, its occurrence comes from the log."""
        pc = d["pc"]
        if self.O is None:
            raise Mismatch("line %d: object-region draw before OGC" % ln)
        self.O.s = step(self.O.s)
        self.ok(int(d["lo"], 16) == self.O.s[0], "line %d: object-region draw low %s, model %08x (pc %08x)" % (ln, d["lo"], self.O.s[0], pc))
        if 0x00581250 <= pc < 0x00581B00 or 0x00585CE0 <= pc < 0x00585D80 or 0x00586850 <= pc < 0x005868A0:
            self.oracle("object timer event draws (simulation; occurrence from the log)")
            self.pcs[pc] = self.pcs.get(pc, 0) + 1
            return
        raise Mismatch("line %d: stray object-region draw outside a modelled scope (pc %08x)" % (ln, pc))

    def resync(self):
        """After a mismatch: skip to the next RW1, OO0 or OGC and take the object-region seed there."""
        while self.i < len(self.L) and self.L[self.i][0] not in ("RW1", "OO0", "OGC"):
            self.i += 1
        if self.i < len(self.L) and self.O is not None:
            d = self.L[self.i][1]
            if d.get("os"):
                self.O.s = parse_seed(d["os"])
        self.hit("resyncs after a mismatch")

    # --- game creation ------------------------------------------------------------------------------------------
    def ev_ogc(self, d):
        gs = parse_seed(d["gs"])
        osd = parse_seed(d["os"])
        self.ok(osd == (gs[0], INIT_HIGH), "line %d: object-region seed %s is not Init(low of the game seed %s)"
                % (self.ln, d["os"], d["gs"]))
        g = [x for x in self.L[:self.i] if x[0] == "GAME"]
        if g:
            sd = parse_seed(g[-1][1]["text"].split("seed=")[1].split()[0])
            want = step(step(sd))
            self.ok(want == gs, "line %d: OBJRGN_Create game seed %s, model step^2(GAME %s) %s" % (self.ln, d["gs"], fmt(sd), fmt(want)))
            self.hit("object-region seed = Init(low of game-seed draw 2), checked against GAME")
        self.O = Seed(osd, "objrgn", self.od)
        self.watch = bool(d.get("watch"))
        self.units = {}
        self.lvl = {}
        self.hit("games (OGC)")

    # --- the room driver window ---------------------------------------------------------------------------------
    def window(self, d1):
        if self.O is None:
            raise Mismatch("line %d: window before any OGC line" % self.ln)
        self.room = d1["room"]
        self.lid = d1["lid"]
        self.room_lid[self.room] = self.lid
        self.rs = Seed(parse_seed(d1["rs"]), "room")
        self.G = Seed(parse_seed(d1["gs"]), "game")
        self.seeds_eq(d1, "RW1", rs=False, gs=False)
        self._np0 = self.stats.get("objects created (populate)", 0)
        while True:
            tag, d = self.next_obj({"OPU0", "RW2"})
            if tag == "RW2":
                break
            self.preset_unit(d)
        self.seeds_eq(d, "RW2")
        tag, d = self.next_obj("RW3")
        self.seeds_eq(d, "RW3")
        self.hit("restore windows: no draw")
        self.populate()
        tag, d = self.next_obj("RW4")
        self.seeds_eq(d, "RW4")
        self.pred_rw4.add((self.path, self.ln))
        self.hit("windows predicted RW1 -> RW4 (room, object-region and game seed)")
        self.covk("windows by level", (self.lid, self.de))
        if self.stats.get("objects created (populate)", 0) > self._np0:
            self.covk("populated rooms by difficulty / expansion / act",
                      ("nmh"[self.de[0]] if self.de else "?", self.de[1] if self.de else "?", self.t.levels[self.lid]["Act"] + 1))
        self.rs = None

    def lone_preset(self, d):
        """A preset unit created outside a logged window (a room whose driver flag bit 0 is set gets no RW lines):
        the room and game seeds are taken from its OPU0, the object-region seed is predicted."""
        if self.O is None:
            raise Mismatch("line %d: preset unit before any OGC line" % self.ln)
        self.room = d["room"]
        lid = d.get("lid")
        if lid is None:
            lid = self.room_lid.get(d["room"])
        if lid is None:
            raise Mismatch("line %d: preset unit in a room of unknown level" % self.ln)
        self.lid = lid
        self.rs = Seed(parse_seed(d["rs"]), "room")
        self.G = Seed(parse_seed(d["gs"]), "game")
        n0 = len(self.units)
        u = self.preset_unit(d)
        self.hit("preset units outside a logged window (room and game seed taken)")
        if u is not None and any(v is not u and (v["cls"], v["x"], v["y"]) == (u["cls"], u["x"], u["y"]) for v in self.units.values()):
            # a revisit: RoomInactiveUnitsRestore re-creates the saved object through PresetUnitDispatch (the creation
            # draws are modelled above), then restores its saved interact byte, mode and sparkle flag
            u["restored"] = True
            self.hit("objects re-created by the inactive-unit restore (revisit)")
        self.rs = None

    def preset_unit(self, d):
        self.seeds_eq(d, "OPU0")
        typ, uid = d["type"], d["id"]
        if typ == 2 and uid < 573:
            u = self.create(uid, d["x"], d["y"], 1, d["mode"], preset=True)
        elif typ == 2 and uid == 573:
            u = None
        elif typ == 2:
            u = self.pseudo(uid, d)
        else:
            dx = self.skip_until("OPUX", "preset unit of type %d (monsters: tools/monspawn.py)" % typ)
            self.take(dx)
            return
        tag, dx = self.next_obj("OPUX")
        self.seeds_eq(dx, "OPUX")
        if u is not None and dx.get("o"):
            self.check_unit(dx["o"], u, "OPUX")
        return u

    def pseudo(self, uid, d):
        lid = self.lid
        act = self.t.levels[lid]["Act"]
        if uid in (580, 581):
            v = self.O.draw()
            if act == 1:
                c = [387, 389, 390, 391][v & 3] if lid == 74 else [87, 88][v & 1]
            elif act == 2:
                c = [329, 330, 331, 332][v & 3] if lid == 83 else [181, 183][v & 1]
            else:
                c = CHEST581[v % 13]
            if uid == 580 and lid == 25:
                c = 371
            u = self.create(c, d["x"], d["y"], 1, 0, preset=True)
            self.covk("pseudo-object %d" % uid, (lid, c))
            if uid == 580:
                spark = True
                if 62 <= lid <= 64 and self.O.p100() > 50:
                    spark = False
                if spark:
                    u["sp"] = 1
                    if lid == 25:
                        u["it"] = 3
                self.covk("super chests (DS1 580)", (lid, c, spark))
            return u
        if uid == 582:
            j = self.i
            while j < len(self.L) and self.L[j][0] != "OU0":
                j += 1
            self.oracle("quest object 582 class (quest state)")
            return self.create(self.L[j][1]["cls"], d["x"], d["y"], 1, 0, preset=True)
        raise Mismatch("line %d: pseudo-object %d not modelled (no stock DS1 places it)" % (self.ln, uid))

    # --- creation -----------------------------------------------------------------------------------------------
    def create(self, cls, x, y, fl, mode, preset=False):
        tag, d = self.next_obj("OU0")
        self.ok((d["type"], d["cls"], d["x"], d["y"], d["fl"], d["mode"]) == (2, cls, x, y, fl, mode),
                "line %d: SUnitCreate %s, model type 2 class %d at (%d, %d) flags %d mode %d"
                % (self.ln, json.dumps(d)[:140], cls, x, y, fl, mode))
        self.seeds_eq(d, "OU0")
        o = self.t.objs[cls]
        lo = self.G.draw()
        u = {"cls": cls, "us": Seed((lo, INIT_HIGH), "unit"), "mode": mode, "it": 0, "sp": 0, "x": x, "y": y,
             "lid": self.lid, "room": self.room}
        fn = o["InitFn"]
        if fn in INIT_TABLE:
            tag, di = self.next_obj("OI0")
            self.ok(di["fn"] == fn and di["cls"] == cls, "line %d: InitFn %s class %s, model %d class %d"
                    % (self.ln, di["fn"], di["cls"], fn, cls))
            self.seeds_eq(di, "OI0")
            self.ok(parse_seed(di["us"]) == u["us"].s, "line %d: unit seed at InitFn %s, model %s" % (self.ln, di["us"], fmt(u["us"].s)))
            if fn in ORACLE_INITFNS:
                dx = self.skip_until("OIX", "InitFn %d (monster spawns / quest state)" % fn)
                self.take(dx)
                u["us"].s = parse_seed(dx["o"]["us"])
                u["it"], u["mode"], u["sp"] = dx["o"]["it"], dx["o"]["mode"], dx["o"]["sp"]
                self.covk("InitFn oracles", (self.lid, cls, fn))
            else:
                if fn in MODELLED_INITFNS:
                    getattr(self, "init_%d" % fn)(u, o)
                    self.hit("InitFn %d runs" % fn)
                else:
                    self.hit("InitFns without draws: %d" % fn)
                    if self.peek_tag() == "OIX":
                        ox = self.L[self.i][1]["o"]
                        if ox["mode"] != u["mode"]:
                            self.set_mode(u, ox["mode"])
                            self.oracle("object mode set by a state InitFn (%d)" % fn)
                        if ox["it"] != u["it"]:
                            u["it"] = ox["it"]
                            self.oracle("interact byte set by a state InitFn (%d)" % fn)
                tag, dx = self.next_obj("OIX")
                self.seeds_eq(dx, "OIX")
                self.check_unit(dx["o"], u, "OIX")
        if o["PreOperate"]:
            r = self.O.rng(14)
            self.hit("PreOperate rolls")
            if r == 0:
                self.set_mode(u, 2)
                self.covk("PreOperate opened", (self.lid, cls))
        tag, dx = self.next_obj("OUX")
        self.seeds_eq(dx, "OUX")
        self.check_unit(dx["o"], u, "OUX")
        self.units[dx["o"]["u"]] = u
        self.hit("objects created (%s)" % ("preset" if preset else "populate"))
        self.covk("class", cls)
        if fn in (2, 3, 57):
            self.covk("containers", (self.lid, cls, u["it"] & 0x7F, bool(u["it"] & 0x80), u["sp"]))
        return u

    def check_unit(self, o, u, what):
        if not o or not o.get("u"):
            raise Mismatch("line %d: %s no unit, model created class %d" % (self.ln, what, u["cls"]))
        self.ok(o["cls"] == u["cls"], "line %d: %s class %d, model %d" % (self.ln, what, o["cls"], u["cls"]))
        self.ok(parse_seed(o["us"]) == u["us"].s, "line %d: %s unit seed %s, model %s (class %d)"
                % (self.ln, what, o["us"], fmt(u["us"].s), u["cls"]))
        self.ok(o["mode"] == u["mode"], "line %d: %s mode %d, model %d (class %d)" % (self.ln, what, o["mode"], u["mode"], u["cls"]))
        if o.get("it") is not None:
            self.ok(o["it"] == u["it"], "line %d: %s interact %d, model %d (class %d)" % (self.ln, what, o["it"], u["it"], u["cls"]))
        if o.get("sp") is not None:
            self.ok(o["sp"] == u["sp"], "line %d: %s sparkle %d, model %d (class %d)" % (self.ln, what, o["sp"], u["sp"], u["cls"]))

    def set_mode(self, u, mode):
        """UNIT_SetMode -> UNIT_AnimInit (object branch): RangeB(unit seed, FrameDelta[mode] >> 3) when Sync is 0."""
        if u["mode"] == mode:
            return
        u["mode"] = mode
        o = self.t.objs[u["cls"]]
        if mode < 8 and not o["Sync"]:
            fd = o["FrameDelta%d" % mode] & 0xFFFF
            fd = fd - 0x10000 if fd & 0x8000 else fd
            u["us"].rng(fd >> 3)

    # --- InitFns ------------------------------------------------------------------------------------------------
    def init_1(self, u, o):
        lid = self.lid
        p0 = s32(o["Parm0"])
        if p0 == 0:
            n = len(self.t.shrines)
            for _ in range(8):
                code = 1 + self.O.rng(n - 1)
                if self.t.shrines[code]["LevelMin"] <= lid:
                    break
        else:
            if p0 == 1:
                ec = 2
            elif p0 == 2:
                ec = 3
            else:
                ec = 1 if self.O.draw() % 10 == 0 else 4
            code = self.shrine_pick(ec, lid)
        code = {5: 3, 4: 2, 16: 18}.get(code, code)
        u["it"] = code
        self.covk("shrines", (lid, u["cls"], code))

    def shrine_pick(self, ec, lid):
        if ec == 0 or ec > 4:
            ec = 2
        lst = self.t.shrine_lists[ec]
        code = None
        for _ in range(8):
            code = lst[self.O.rng(len(lst))]
            if code == 0:
                code = 1
            if self.t.shrines[code]["LevelMin"] <= lid:
                break
        return code

    def init_2(self, u, o):
        ml = s32(self.t.levels[self.lid]["MonLvl1"])
        thr = (idiv(ml, 8) + 5) & 0xFFFF
        r = self.O.p100()
        u["it"] = self.O.lohi(1, 9) if r < thr else 0

    def init_3(self, u, o):
        self.init_2(u, o)
        it = u["it"]
        ml = s32(self.t.levels[self.lid]["MonLvl1"])
        if o["Lockable"] and self.O.p100() < idiv(ml, 2) + 8:
            it |= 0x80
        else:
            it &= 0x7F
        v = self.O.draw()
        u["us"].s = (v % 0xFFFE + 1, INIT_HIGH)
        u["it"] = it

    def init_57(self, u, o):
        self.init_3(u, o)
        u["sp"] = 1

    def init_27(self, u, o):
        u["it"] = 0 if self.O.draw() % 1000 > 332 else 3

    def init_28(self, u, o):
        self.set_mode(u, 2)
        n = self.O.draw() % 9 + 1
        x, y = u["x"], u["y"]           # the 1x1 test is always at the object's cell + (dx, dy); RoomAtSubtile is asked
        piles = 0                       # at a running position (the last tested cell, as the gold drop left it)
        for _ in range(n):
            dx = self.O.draw() & 3
            dy = self.O.draw() & 3
            # RoomAtSubtile(x + dx, y + dy) must be the object's room; only then is the 1x1 test made
            if self.peek_tag() == "OT":
                tag, dt = self.next_obj("OT")
                self.ok((dt["site"], dt["x"], dt["y"], dt["w"], dt["h"], dt["m"]) == (SITE_GOLD, x + dx, y + dy, 1, 1, 0x3F11),
                        "line %d: gold-pile test %s, model (%d, %d)" % (self.ln, json.dumps(dt), x + dx, y + dy))
                self.oracle("position test result (COLL_WHTest)")
                if dt["res"] == 0:
                    tag, dg = self.next_obj("OGP0")
                    self.ok((dg["x"], dg["y"]) == (x + dx, y + dy), "line %d: gold pile at (%d, %d), model (%d, %d)"
                            % (self.ln, dg["x"], dg["y"], x + dx, y + dy))
                    self.seeds_eq(dg, "OGP0", rs=False)
                    self.ok(parse_seed(dg["us"]) == u["us"].s, "line %d: gold-pile unit seed" % self.ln)
                    dx_ = self.skip_until("OGPX", "gold drop (item creation)")
                    self.take(dx_, rs=False)
                    u["us"].s = parse_seed(dx_["us"])
                    piles += 1
            else:
                self.oracle("gold-pile cell outside the object's room (RoomAtSubtile, no test)")
        self.covk("gold piles (InitFn 28)", (self.lid, n, piles))

    def init_34(self, u, o):
        if self.O.draw() & 1:
            self.set_mode(u, 1)

    def init_58(self, u, o):
        self.O.draw()

    # --- placement ----------------------------------------------------------------------------------------------
    def whtest(self, site, x, y, w, h, m):
        tag, d = self.next_obj("OT")
        self.ok((d["site"], d["x"], d["y"], d["w"], d["h"], d["m"]) == (site, s32(x), s32(y), w, h, m),
                "line %d: position test %s, model site %08x (%d, %d) %dx%d mask %04x"
                % (self.ln, json.dumps(d), site, x, y, w, h, m))
        self.oracle("position test result (COLL_WHTest)")
        self.hit("position tests")
        return d["res"]

    def pos_padded(self, x, y, sx, sy):
        rx, ry, w, h = self.rect
        if w < sx + 2 or h < sy + 2:
            return False
        if not (x & 0xFFFF) > rx + 1 or not (y & 0xFFFF) > ry + 1:
            return False
        if (x & 0xFFFF) >= rx - sx + w - 2 or (y & 0xFFFF) >= ry - sy + h - 2:
            return False
        if self.whtest(SITE_PAD1, x, y, sx + 7, sy + 7, 0xC01):
            return False
        if self.whtest(SITE_PAD2, x, y, sx, sy, 0x3F11):
            return False
        return True

    def pos_tight(self, x, y, sx, sy):
        rx, ry, w, h = self.rect
        if w < 2 or h < 2:
            return False
        if not (x & 0xFFFF) > rx + 2 or not (y & 0xFFFF) > ry + 2:
            return False
        if (x & 0xFFFF) >= rx - sx + w or (y & 0xFFFF) >= ry - sy + h:
            return False
        return not self.whtest(SITE_TIGHT, x, y, sx + 2, sy + 2, 0x3F11)

    def in_bounds(self, x, y):
        rx, ry, w, h = self.rect
        return (x != 0 and y != 0 and rx + 1 <= (x & 0xFFFF) and ry + 1 <= (y & 0xFFFF)
                and (x & 0xFFFF) < rx + w - 1 and (y & 0xFFFF) < ry + h - 1)

    def placed_after(self, a):
        self.hit("placements accepted at attempt %d" % (a + 1))
        if a:
            self.covk("placements that needed retries", (self.lid, a + 1))

    def place_random(self, cls, sx, sy):
        """OBJ_PlaceRandom 0x00550380 on the object-region seed."""
        rx, ry, w, h = self.rect
        if w < 2 or h < 2:
            return None
        for a in range(5):
            x = rx + self.O.rng(w - sx - 1)
            y = ry + self.O.rng(h - sy - 1)
            if self.in_bounds(x, y) and not self.whtest(SITE_PLACE, x, y, sx + 6, sy + 6, 0x3F11):
                self.placed_after(a)
                return self.create(cls, x, y, 1, 0)
        self.hit("placements with no spot after 5 attempts")
        return None

    def place_roomseed(self, cls, sx, sy, dist):
        """OBJ_PlaceRandomRoomSeed 0x00550540 on the room seed, with a spacing test."""
        rx, ry, w, h = self.rect
        if w < 2 or h < 2 or w <= sx or h <= sy:
            return None
        for a in range(5):
            x = rx + self.rs.rng(w - sx - 1)
            y = ry + self.rs.rng(h - sy - 1)
            if self.in_bounds(x, y) and not self.whtest(SITE_PLACERS, x, y, sx + 6, sy + 6, 0x3F11) and dist(x, y):
                self.placed_after(a)
                return self.create(cls, x, y, 1, 0)
        self.hit("placements with no spot after 5 attempts")
        return None

    def place_orient(self, cls, sx, sy, orient, dist):
        """OBJ_PlaceByOrientation 0x00550A30 on the room seed."""
        rx, ry, w, h = self.rect
        if not (sx + 2 <= w and sy + 2 <= h):
            return None
        for a in range(5):
            if orient == 1:
                x = self.rs.rng(idiv(w, 2)) + idiv(w, 4) + rx
                y = self.rs.lohi(1, 2) + ry
            elif orient == 2:
                x = self.rs.lohi(1, 2) + rx
                y = self.rs.rng(idiv(h, 2)) + idiv(h, 4) + ry
            else:
                x = self.rs.rng(w - sx - 1) + rx
                y = self.rs.rng(h - sy - 1) + ry
            if self.in_bounds(x, y) and not self.whtest(SITE_ORIENT, x, y, sx + 6, sy + 6, 0x3F11) and dist(x, y):
                self.placed_after(a)
                return self.create(cls, x, y, 1, 0)
        self.hit("placements with no spot after 5 attempts")
        return None

    # --- the populate pass --------------------------------------------------------------------------------------
    def populate(self):
        tag, d = self.next_obj("OG")
        self.seeds_eq(d, "OG")
        self.rect = tuple(d["rect"])
        lid = d["lid"]
        lv = self.t.levels[lid]
        closed = bool(d.get("f")) or not d.get("pop") or bool(d.get("pre")) or bool(d.get("town"))
        self.oracle("gate inputs (DRLG: room flags 0x30000, population level, preset test, town)")
        if lid in TOWNS:
            self.ok(closed, "line %d: a town window was not closed" % self.ln)
        if closed:
            self.ok(d["res"] == 0, "line %d: gate inputs %s close it, result %d" % (self.ln, json.dumps(d)[:120], d["res"]))
            self.hit("windows closed at the gate")
            return
        pop = d["pop"]
        L = self.lvl.setdefault(pop, {"vis": 0, "cnt": 0x7FFFFFFF, "hs": 0, "nsh": 0, "nwl": 0, "shp": [], "wlp": []})
        if L["cnt"] == 0x7FFFFFFF:
            if "cnt" in d:
                L["cnt"] = d["cnt"]
                self.oracle("LevelRoomCount (DRLG)")
            else:
                # the level's first gated room was not followed (a resync): take its counters from the gate line
                g = d.get("L") or {}
                self.ok("cnt" in g and g["vis"] > 1, "line %d: roomCount not logged at the first gated room" % self.ln)
                L.update(vis=g["vis"] - 1, cnt=g["cnt"], hs=g["hs"], nsh=g["nsh"], nwl=g["nwl"])
                L["lost"] = True
                self.oracle("level counters taken after a resync")
        L["vis"] += 1
        res = self.theme_roll(L, lv["Themes"]) if lv["Themes"] else 1
        self.ok(d["res"] == res, "line %d: gate result %d, model %d" % (self.ln, d["res"], res))
        if d.get("L"):
            g = d["L"]
            mine = {k: L[k] for k in ("vis", "cnt", "hs", "nsh", "nwl")}
            if (g["vis"], g["cnt"], g["hs"], g["nsh"], g["nwl"]) != (L["vis"], L["cnt"], L["hs"], L["nsh"], L["nwl"]):
                L.update(vis=g["vis"], cnt=g["cnt"], hs=g["hs"], nsh=g["nsh"], nwl=g["nwl"])   # one mismatch, then go on
            self.ok(mine == {k: L[k] for k in mine}, "line %d: level %d counters %s, model %s" % (self.ln, pop, g, mine))
        if not res:
            return
        self.hit("windows past the gate")
        self.pop, self.L_ = pop, L
        nobj0 = self.stats.get("objects created (populate)", 0)
        for k in range(8):
            g = lv["ObjGrp%d" % k]
            r = self.rs.p100()
            forced = (L["cnt"] > 0 and idiv(L["vis"] << 7, L["cnt"]) > 96 and L["hs"] == 0
                      and self.t.objs[g]["SubClass"] != 0)
            if forced:
                r = 100
            tag, ds = self.next_obj("OS")
            self.ok((ds["k"], ds["g"], ds["r"]) == (k, g, r), "line %d: slot %s, model k %d group %d r %d"
                    % (self.ln, json.dumps(ds), k, g, r))
            if ds.get("L"):
                q = ds["L"]
                self.ok((q["vis"], q["cnt"], q["hs"]) == (L["vis"], L["cnt"], L["hs"]),
                        "line %d: forced-rule counters %s, model %s" % (self.ln, q, L))
            self.hit("slots")
            if forced:
                self.covk("forced slots (r = 100)", (lid, k, g))
            if g == 0 or r > lv["ObjPrb%d" % k]:
                continue
            gr = self.t.groups[g]
            r2 = self.rs.p100()
            tag, dk = self.next_obj("OK")
            self.ok(dk["r2"] == r2, "line %d: member pick %d, model %d" % (self.ln, dk["r2"], r2))
            self.hit("slots passed")
            self.covk("groups drawn", (lid, g))
            cum, member = 0, None
            for i in range(8):
                oid = gr["ID%d" % i]
                if oid == 0:
                    break
                cum += gr["PROB%d" % i]
                if r2 < cum and self.t.objs[oid]["Gore"] <= 2:
                    member = (oid, gr["DENSITY%d" % i])
                    break
            if member is None:
                self.hit("slots with no member (pick at or past the PROB sum)")
                continue
            oid, den = member
            fn = self.t.objs[oid]["PopulateFn"]
            if not fn:
                continue
            tag, dh = self.next_obj("OH0")
            self.ok((dh["fn"], dh["cls"], dh["den"], dh["k"]) == (fn, oid, den, k),
                    "line %d: handler %s, model fn %d class %d density %d" % (self.ln, json.dumps(dh)[:120], fn, oid, den))
            self.seeds_eq(dh, "OH0")
            getattr(self, "pop_%d" % fn)(oid, den)
            tag, dx = self.next_obj("OHX")
            self.seeds_eq(dx, "OHX")
            self.hit("PopulateFn %d calls" % fn)
            self.covk("PopulateFn", fn)
        if self.stats.get("objects created (populate)", 0) > nobj0:
            self.hit("rooms populated with objects")

    def theme_roll(self, L, themes):
        """OBJ_RoomThemeRoll 0x00552400 (ObjRgnLevel +0x0C has no writer: 0, so the first test never returns)."""
        if L["cnt"] < 0:
            return 1
        r = self.O.p100()
        thr = 12 + (5 if idiv(L["cnt"], 2) < L["vis"] else 0) + (5 if L["cnt"] - idiv(L["cnt"], 4) < L["vis"] else 0)
        self.hit("theme rolls")
        if r < thr:
            lst = [t for t in range(1, 8) if themes & (1 << (t - 1))]
            i = self.O.rng(len(lst))
            if i < len(lst) and lst[i] < len(lst):
                raise Mismatch("line %d: theme %d would run (not modelled)" % (self.ln, lst[i]))
            self.hit("theme rolls that drew a theme (none runs on stock data)")
        return 1

    def cnt_of(self, den):
        return ((self.rect[3] * self.rect[2]) >> 7) * den >> 8

    def pop_1(self, cls, den):
        o = self.t.objs[cls]
        sx, sy = o["SizeX"], o["SizeY"]
        if self.O.p100() > 100:
            return
        if cls not in CLUSTER:
            return
        lst, tries, stp, base, tight = CLUSTER[cls]
        cnt = self.cnt_of(den)
        if cnt < 1:
            return
        rx, ry, w, h = self.rect
        while tries >= 1:
            c = lst[self.O.rng(len(lst))]
            x = rx + self.O.rng(w - sx - 1)
            y = ry + self.O.rng(h - sy - 1)
            if self.pos_padded(x, y, sx, sy):
                self.create(c, x, y, 1, 0)
                k, ok = 1, True
                while True:
                    m = k >> 1
                    if m > 0 and self.O.rng(m) != 0:
                        break
                    if not ok:
                        break
                    ok, i, lim = False, 0, 3 * max(cnt, 4)
                    while i < lim:
                        dd = self.O.draw() & 7
                        x = x + (self.O.rng(stp) + base) * DX[dd] * 2
                        y = y + (self.O.rng(stp) + base) * DY[dd] * 2
                        ok = self.pos_tight(x, y, sx, sy) if tight else self.pos_padded(x, y, sx, sy)
                        i += 1
                        if ok:
                            break
                    if not ok:
                        continue
                    c = lst[self.O.rng(len(lst))]
                    self.create(c, x, y, 1, 0)
                    k += 1
                cnt -= 1
            tries -= 1
            if cnt < 1:
                return

    def pop_2(self, cls, den):
        o = self.t.objs[cls]
        L = self.L_
        r = self.rs.p100()
        forced = L["cnt"] > 0 and idiv(L["vis"] << 7, L["cnt"]) > 96 and L["hs"] == 0
        tries = 30 if forced else 3
        if not forced and r > 100:
            return
        if L["nsh"] == 10 or L["nsh"] > idiv(L["cnt"], 8):
            self.hit("shrine handler at its cap")
            return

        def dist(x, y):
            ok = all(abs(x - px) >= 50 and abs(y - py) >= 50 for px, py in L["shp"])
            if L["shp"]:
                self.hit("shrine spacing tests against earlier shrines (%s)" % ("pass" if ok else "reject"))
            return ok

        for _ in range(tries):
            u = self.place_orient(cls, o["SizeX"], o["SizeY"], o["Orientation"], dist)
            if u is None:
                continue
            if u["it"] != 2:
                if not forced:
                    L["shp"].append((u["x"], u["y"]))
                    L["nsh"] += 1
                    return
                p1 = s32(self.t.objs[u["cls"]]["Parm1"])
                u["cls"] = p1 if 0 < p1 < 573 else 84
                self.shrine_pick(2, 1)
                u["it"] = 2
                self.covk("forced health shrines", (self.lid, u["cls"]))
            L["hs"] += 1
            L["shp"].append((u["x"], u["y"]))
            L["nsh"] += 1
            return

    def pop_3(self, cls, den):
        o = self.t.objs[cls]
        if self.O.p100() > 100:
            return None
        last = None
        for _ in range(self.cnt_of(den)):
            last = self.place_random(cls, o["SizeX"], o["SizeY"])
        return last

    def pop_4(self, cls, den):
        o = self.t.objs[7]
        sx, sy = o["SizeX"], o["SizeY"]
        if self.O.p100() > 100:
            return
        rx, ry, w, h = self.rect
        cnt = self.cnt_of(den)
        tries = cnt * 2
        total = 0
        while cnt > 0 and tries > 0:
            c = 11 if self.O.draw() % 3 == 0 else 7
            x = rx + self.O.rng(w)
            y = ry + self.O.rng(h)
            if not self.pos_tight(x, y, sx, sy):
                tries -= 1
                continue
            self.create(c, x, y, 1, 0)
            self.covk("barrels", c)
            total += 1
            if total >= 8:
                return
            k, ok = 1, True
            while True:
                m = k >> 1
                if m > 0 and self.O.rng(m) != 0:
                    break
                if not ok:
                    break
                ok, i = False, 0
                while i <= 14:
                    dd = self.O.draw() & 7
                    x += o["Xspace"] * DX[dd]
                    y += o["Yspace"] * DY[dd]
                    ok = self.pos_tight(x, y, sx, sy)
                    i += 1
                    if ok:
                        break
                if not ok:
                    continue
                c = 11 if self.O.draw() & 3 == 0 else 7
                self.create(c, x, y, 1, 0)
                self.covk("barrels", c)
                k += 1
                total += 1
                if total > 7:
                    return
            cnt -= 1
            tries -= 1

    def pop_5(self, cls, den):
        o = self.t.objs[cls]
        sx, sy = o["SizeX"], o["SizeY"]
        if self.O.p100() > 100:
            return
        rx, ry, w, h = self.rect
        cnt = self.cnt_of(den)
        tries = cnt * 2
        if cnt < 1:
            return
        ring = cnt * 4
        followers = 0
        while tries >= 1:
            c = cls
            if cls != 46:
                c = CRATE_LIST[self.O.rng(5)]
            x = rx + self.O.rng(w)
            y = ry + self.O.rng(h)
            if self.pos_tight(x, y, sx, sy):
                if cls != 46:
                    c = CRATE_LIST[self.O.rng(5)]
                self.create(c, x, y, 1, 0)
                k, ok = 1, True
                while True:
                    m = k >> 1
                    if m > 0 and self.O.rng(m) != 0:
                        break
                    if not ok:
                        break
                    ok, i, lim = False, 0, max(4, ring)
                    while i < lim:
                        dd = self.O.draw() & 7
                        x += o["Xspace"] * DX[dd]
                        y += o["Yspace"] * DY[dd]
                        ok = self.pos_tight(x, y, sx, sy)
                        i += 1
                        if ok:
                            break
                    if not ok:
                        continue
                    if self.create(c, x, y, 1, 0) is not None:
                        followers += 1
                        if followers > 7:
                            return
                    k += 1
                cnt -= 1
                ring -= 4
            tries -= 1
            if cnt < 1:
                return

    def pop_6(self, cls, den):
        u = self.pop_3(cls, den)
        if u is not None:
            self.flies(u)

    def flies(self, u):
        if self.O.p100() > 70:
            self.create(103, u["x"], u["y"], 1, 0)
            self.hit("flies")

    def pop_7(self, cls, den):
        o = self.t.objs[cls]
        sx, sy = o["SizeX"], o["SizeY"]
        if self.O.p100() > 100:
            return
        p = self.O.rng(4)
        rx, ry, w, h = self.rect
        for _ in range(8):
            ax = rx + self.O.rng(w - sx - 1)
            ay = ry + self.O.rng(h - sy - 1)
            if self.pos_padded(ax, ay, 5, 5):
                for ox, oy in STICK[p]:
                    x, y = ax + ox, ay + oy
                    if self.pos_padded(x, y, sx, sy):
                        c = 57 + (self.O.draw() & 1)
                        u = self.create(c, x, y, 1, 0)
                        if u is not None:
                            self.flies(u)
                self.covk("stick-corpse patterns", (self.lid, p))
                return

    def pop_8(self, cls, den):
        o = self.t.objs[cls]
        L = self.L_
        if L["nwl"] == 4 or L["nwl"] > idiv(L["cnt"], 8):
            self.hit("well handler at its cap")
            return
        if self.rs.p100() > 100:
            return

        def dist(x, y):
            ok = all(abs(x - px) >= 100 and abs(y - py) >= 100 for px, py in L["wlp"])
            if L["wlp"]:
                self.hit("well spacing tests against earlier wells (%s)" % ("pass" if ok else "reject"))
            return ok

        u = self.place_roomseed(cls, 2 * o["SizeX"] + 1, 2 * o["SizeY"] + 1, dist)
        if u is not None:
            if L["nwl"] < 4:
                L["wlp"].append((u["x"], u["y"]))
                L["nwl"] += 1
            self.covk("wells", (self.lid, cls))

    def pop_9(self, cls, den):
        o = self.t.objs[cls]
        if self.rs.p100() > 100:
            return
        for _ in range(self.cnt_of(den)):
            if self.place_random(cls, o["SizeX"], o["SizeY"]) is not None:
                self.covk("traps (PopulateFn 9)", (self.lid, cls))
                return

    # --- operate ------------------------------------------------------------------------------------------------
    def operate(self, d):
        u = self.units.get(d["u"])
        fn = d["fn"]
        self.seeds_eq(d, "OO0", rs=False, gs=False)
        self.G = Seed(parse_seed(d["gs"]), "game")
        self.rs = None
        if u is None or u["cls"] != d["cls"]:
            self.hit("operates of objects the model did not create (seeds taken)")
            dx = self.skip_until("OOX", "operate of an object created outside the logged windows")
            self.ok(parse_seed(dx["os"]) == self.O.s, "line %d: OperateFn %d moved the object-region seed" % (self.ln, fn))
            return
        self.ok(parse_seed(d["us"]) == u["us"].s, "line %d: unit seed at operate %s, model %s (class %d)"
                % (self.ln, d["us"], fmt(u["us"].s), u["cls"]))
        if u.get("restored") and (d["mode"], d["it"], d["sp"]) != (u["mode"], u["it"], u["sp"]):
            u["mode"], u["it"], u["sp"] = d["mode"], d["it"], d["sp"]
            self.oracle("object state restored on a revisit (saved interact, mode, sparkle)")
        self.ok((d["mode"], d["it"], d["sp"]) == (u["mode"], u["it"], u["sp"]),
                "line %d: operate mode/interact/sparkle %s, model %s" % (self.ln, (d["mode"], d["it"], d["sp"]), (u["mode"], u["it"], u["sp"])))
        self.lid = u["lid"]
        rec = {"lid": u["lid"], "cls": u["cls"], "fn": fn, "it": u["it"], "sp": u["sp"], "mode": u["mode"], "drops": []}
        if fn in (1, 3, 4, 5):
            getattr(self, "op_%d" % fn)(u, rec)
        else:
            dx = self.skip_until("OOX", "OperateFn %d (not a container)" % fn)
            self.ok(parse_seed(dx["os"]) == self.O.s, "line %d: OperateFn %d moved the object-region seed" % (self.ln, fn))
            u["mode"] = dx["mode"]
            u["us"].s = parse_seed(dx["us"])
            return
        tag, dx = self.next_obj("OOX")
        self.seeds_eq(dx, "OOX", rs=False, gs=False)
        self.ok(parse_seed(dx["us"]) == u["us"].s, "line %d: unit seed after operate %s, model %s" % (self.ln, dx["us"], fmt(u["us"].s)))
        self.ok(dx["mode"] == u["mode"], "line %d: mode after operate %d, model %d" % (self.ln, dx["mode"], u["mode"]))
        self.hit("operates predicted (OperateFn %d)" % fn)
        self.covk("operates", rec)

    def drop(self, u, q, rec):
        tag, d = self.next_obj("OC0")
        self.ok(d["q"] == q, "line %d: forced quality %d, model %d" % (self.ln, d["q"], q))
        self.seeds_eq(d, "OC0", rs=False, gs=False)
        self.ok(parse_seed(d["us"]) == u["us"].s, "line %d: unit seed at the drop %s, model %s" % (self.ln, d["us"], fmt(u["us"].s)))
        tag, dt = self.next_obj({"OCT", "OCX"})
        if tag == "OCX":
            rec["drops"].append({"q": q, "tc": None})
            return None
        self.ok(dt["q"] == q, "line %d: TC_ResolveDrops quality %d, model %d" % (self.ln, dt["q"], q))
        self.seeds_eq(dt, "OCT", rs=False, gs=False)
        k = (dt["tc"] or 0) - 161
        name = self.t.tc_names[k] if 0 <= k < len(self.t.tc_names) else None
        self.ok(name is not None and "Chest" in name, "line %d: chest drop TC %s (%s) is not an act chest TC" % (self.ln, dt["tc"], name))
        dx = self.skip_until("OCX", "TC_ResolveDrops (items/tc)")
        self.ok(parse_seed(dx["os"]) == self.O.s, "line %d: the resolver moved the object-region seed" % self.ln)
        u["us"].s = parse_seed(dx["us"])
        self.G = Seed(parse_seed(dx["gs"]), "game")
        rec["drops"].append({"q": q, "tc": name, "item_q": dx["q"] if dx["item"] else None})
        return dx["q"] if dx["item"] else None

    @staticmethod
    def magic(qr):
        return qr is not None and 4 <= qr <= 9

    def op_4(self, u, rec):
        if u["mode"] != 0:
            return
        locked = u["it"] & 0x80
        drops = 1
        if locked:
            if self.peek_tag() == "OOX":
                self.hit("locked chests not opened (no key)")
                return
            drops = 2
            rec["locked_opened"] = True
        q = 0
        if u["sp"]:
            q = 6 if self.O.p100() < 5 else 4
        rec["q"] = q
        if u["cls"] != 397:
            r = self.O.p100()
            rec["r"] = r
            if r > 24 or u["sp"] or locked:
                nm = 0
                for _ in range(drops):
                    if self.magic(self.drop(u, q, rec)):
                        nm += 1
                if u["sp"] and nm == 0:
                    for _ in range(10):
                        if self.magic(self.drop(u, q, rec)):
                            break
            else:
                rec["empty"] = True
        else:
            self.op_397(u, rec)
        self.set_mode(u, 1 if self.t.objs[u["cls"]]["Mode1"] else 2)

    def op_397(self, u, rec):
        r = self.O.draw() % 10000
        rec["r397"] = r
        if r < 1200:
            q = 7 if r < 200 else 5 if r < 600 else 6
            for _ in range(2):
                v = self.drop(u, q, rec)
                if v is None or self.magic(v):
                    if v is not None:
                        return
                    break
            self.op_397_f(u, rec, 0)
            return
        if r < 3200:
            nm = n = 0
            for _ in range(10):
                v = self.drop(u, 4, rec)
                if v is not None:
                    if self.magic(v):
                        nm += 1
                    n += 1
                if nm >= 3:
                    break
            if n:
                return
            self.op_397_f(u, rec, n)
            return
        if r < 6200:
            plain = mg = 0
            for _ in range(10):
                v = self.drop(u, 4, rec)
                if v is not None:
                    if self.magic(v):
                        mg += 1
                    else:
                        plain += 1
                if mg >= 2:
                    break
            if plain == 0:
                if self.drop(u, 0, rec) is not None:
                    plain = 1
            elif plain > 6:
                return
            self.gold_like(rec, 7 - plain)
            return
        self.op_397_f(u, rec, 0)

    def op_397_f(self, u, rec, n0):
        n = n0
        for _ in range(10):
            v = self.drop(u, 4, rec)
            if v is not None:
                if self.magic(v):
                    break
                n += 1
        if n < 4:
            for _ in range(4 - n):
                self.drop(u, 0, rec)
        self.gold_like(rec, 9)

    def gold_like(self, rec, n):
        """sub_00585970 drops of fixed codes (gold, potions): item creation, seeds not followed (no OC lines)."""
        rec["fixed_drops"] = rec.get("fixed_drops", 0) + n

    def op_1(self, u, rec):
        if u["mode"] != 0:
            return
        v = self.drop(u, 0, rec)
        if v is None:
            return
        self.set_mode(u, 1)
        r = self.O.draw() % 10000
        rec["r10000"] = r
        if r & 0xFFFFE000:
            rec["monster"] = True
            self.monster_oracle(u)

    def monster_oracle(self, u):
        """The casket / barrel monster spawn (0x00582280): monster creation, seeds taken at OOX (object-region seed kept)."""
        j = self.i
        while j < len(self.L) and self.L[j][0] != "OOX":
            if self.L[j][0] == "OD":
                raise Mismatch("line %d: object-region draw inside the operate monster spawn" % self.L[j][2])
            j += 1
        self.oracle("operate monster spawn (0x00582280)")
        if j < len(self.L):
            u["us"].s = parse_seed(self.L[j][1]["us"])

    def op_3(self, u, rec):
        if u["mode"] != 0:
            return
        self.set_mode(u, 1)
        r = self.O.p100()
        rec["r"] = r
        if r < 21:
            self.drop(u, 0, rec)

    def op_5(self, u, rec):
        if u["mode"] != 0:
            return
        self.set_mode(u, 1)
        r = self.O.draw() % 10000
        rec["r10000"] = r
        if r & 0xFFFFE000:
            rec["monster"] = True
        r = self.O.p100()
        rec["r"] = r
        if r < 21:
            self.drop(u, 0, rec)
        if rec.get("monster"):
            self.monster_oracle(u)


def summary(c):
    """The plan 0023 Phase 2 counts the run record quotes."""
    ops = c.cov.get("operates", [])
    urns = [o for o in ops if o["fn"] == 3]
    chests = [o for o in ops if o["fn"] == 4]
    print("summary: populated rooms %d %s" % (len(c.cov.get("populated rooms by difficulty / expansion / act", [])),
                                             sorted(set(c.cov.get("populated rooms by difficulty / expansion / act", [])))))
    print("summary: shrines %d (codes %s)" % (len(c.cov.get("shrines", [])), sorted({x[2] for x in c.cov.get("shrines", [])})))
    cont = c.cov.get("containers", [])
    print("summary: containers created %d: trapped %d, locked %d, sparkle %d" % (
        len(cont), sum(1 for x in cont if x[2]), sum(1 for x in cont if x[3]), sum(1 for x in cont if x[4])))
    print("summary: operated containers %d (casket %d, urn %d, chest %d, barrel %d)" % (
        len(ops), sum(1 for o in ops if o["fn"] == 1), len(urns), len(chests), sum(1 for o in ops if o["fn"] == 5)))
    print("summary: urns: draw r < 21 (drop) %d of %d; drops made %d" % (
        sum(1 for o in urns if o["r"] < 21), len(urns), sum(len(o["drops"]) for o in urns)))
    print("summary: chests: empty (r <= 24) %d, locked opened %d, sparkle %d (qualities %s), TCs %s" % (
        sum(1 for o in chests if o.get("empty")), sum(1 for o in chests if o.get("locked_opened")),
        sum(1 for o in chests if o["sp"]), sorted({o.get("q") for o in chests if o["sp"]}),
        sorted({d["tc"] for o in ops for d in o["drops"] if d.get("tc")})))
    print("summary: placements that needed retries %d; gold piles %s" % (
        len(c.cov.get("placements that needed retries", [])), c.cov.get("gold piles (InitFn 28)", [])))


def report(c):
    for k in sorted(c.stats):
        print("  %-74s %d" % (k, c.stats[k]))
    for k in sorted(c.oracles):
        print("  oracle %-67s %d" % (k, c.oracles[k]))
    for k in sorted(c.cov):
        v = c.cov[k]
        cnt = {}
        for x in v:
            key = json.dumps(x) if isinstance(x, dict) else x
            cnt[key] = cnt.get(key, 0) + 1
        if k in ("class", "PopulateFn", "barrels"):
            print("  cov %-40s %d %s" % (k, len(v), dict(sorted(cnt.items()))))
        elif c.verbose or len(v) <= 12:
            print("  cov %-40s %d %s" % (k, len(v), v[:60]))
        else:
            print("  cov %-40s %d" % (k, len(v)))


def cmd_check(argv):
    excel, root, verbose, paths = "workspace/merged/data/global/excel", "workspace/merged", False, []
    it = iter(argv)
    for a in it:
        if a == "--excel":
            excel = next(it)
        elif a == "--root":
            root = next(it)
        elif a == "-v":
            verbose = True
        else:
            paths.append(a)
    if not paths:
        print(__doc__)
        return 2
    c = Checker(excel, root, verbose)
    for p in paths:
        c.run(p)
    report(c)
    summary(c)
    print("objects: %d checks, %d mismatches" % (c.checks, c.fail))
    return 1 if c.fail else 0


def main(argv):
    if len(argv) < 3 or argv[1] not in ("window", "check"):
        print(__doc__)
        return 2
    return cmd_window(argv[2:]) if argv[1] == "window" else cmd_check(argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""Per-event model of the server's stat lists (plan 0041 Phase 2), checked against runtime logs, from
docs/findings/stats/0001-aggregate.md and 0002-states.md.

Usage:
  python3 -I tools/stats.py check <log> [...] [--excel DIR] [-v] [--json OUT]
  python3 -I tools/stats.py manifest <log> [...]          # sha256, size and line count of each log
  python3 -I tools/stats.py isc [--excel DIR]             # the op graph ITEMSTATCOST_Load builds, from the table

<log> is written by tools/d2run.py with tools/gdb/stats.gdb (the tags of tools/gdb/stats.py). The model mirrors the
player's stat-list tree (the unit list and every list under it) and replays the logged events on it:

  * ISC: the loaded op graph (targets +0x58, dependents +0x5E, opIn +0x0DE, the +0x51/+0x52/+0x53 flags) is predicted
    from ItemStatCost (the loader's rules, stats/0001 § 4) and compared field by field with the dump; ValShift,
    MinAccr, keepzero and the damagerelated / fMin / fCallback bits likewise;
  * a list event (LNK STATLIST_LinkToUnit, ULK STATLIST_Unlink, PRP STATLIST_Propagate) is emulated: the structure
    change, then every write it makes, in order (§ 2, § 3): which Propagate calls a link or unlink makes (key, delta),
    and for each Propagate the CacheAdd or the StatRecompute writes (the evaluation of § 4 with the op terms, the
    take test, the targets and dependents); each logged CA/CW line is compared with the next predicted write (list,
    key, delta or value) and the old value it found with the mirror;
  * SCB (the player's stat callback): predicted from the write before it (key, old, new); for keys 7, 9, 11 the
    rescale of the current value (§ 5) is predicted and checked against the own write of 6, 8, 10 that follows;
  * TREE: after every top-level event the mirror is compared with the logged tree (own entries, caches, flags,
    chains): a difference is a drift mismatch; the mirror is then resynchronised;
  * RD (reads in the 50-frame windows): predicted from the mirror's cache with the fMin floor (§ 1);
  * RQ0..RQX (sub_0062EAF0_ItemReqCheck): the strength, dexterity and level tests predicted from the item's base
    record (Weapons/Armor/Misc reqstr, reqdex), stat 91, the ethereal flag and the mirror's unit stats, with the
    logged required level (RQL) and self contribution (RQS, RQD) as value oracles;
  * UOE/MSK/TIP/TGL (sets): the worn mask from the inventory listing (page 3, quality 5, not 0x4000 or 0x100, same
    set id, bit = member index), and the toggle sequence of the item's aprop lists by add func (§ 7);
  * SBX: the wearer's set list predicted from the Sets blocks for n = popcount(mask) (partial pairs and full);
  * seeds: the game seed and the player's seed at the entry and exit of every top-level event (LNK, ULK, TGL, PRP,
    TK) must be equal (stats/0002 § 7, the P1 review's draw-freedom amendment).
Exit 0 only if every check holds. Stdlib only. Read-only.
"""
import base64
import collections
import hashlib
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from monstats import muldiv, s32  # noqa: E402

DEFAULT_EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
EXT, OFF, NODMG, OPSRC = 0x80000000, 0x2000, 0x40000000, 0x20000000
WRITERS = {0x627091, 0x62712F, 0x6271F1, 0x6273D3}          # AddStat, SetStatEx, 0x00627170, STATLIST_Clear
LINK_RA = {0x626FB2, 0x627015}
UNLINK_RA = {0x626BAA, 0x626BCB}
DMG_RA = {0x6278FB: +1, 0x627ADD: -1}                         # Enable / DisableDamageStats
TAKE_CLASS = [0, 5, 1, 1, 2, 2, 3, 3, 0, 0, 0, 0, 5, 4]      # 0x0062690C by op


def lcg_step(lo, hi):
    """RNG_Step (rng/0001): (lo, hi) <- (lo * 0x6AC690C5 + hi) as 64 bits."""
    v = lo * 0x6AC690C5 + hi
    return v & 0xFFFFFFFF, (v >> 32) & 0xFFFFFFFF


def lcg_distance(a, b, limit):
    """The number of LCG steps from seed a to seed b ("lo:hi" hex), None beyond limit."""
    lo, hi = (int(x, 16) for x in a.split(":"))
    t = tuple(int(x, 16) for x in b.split(":"))
    for k in range(limit + 1):
        if (lo, hi) == t:
            return k
        lo, hi = lcg_step(lo, hi)
    return None


def unz(s):
    return json.loads(zlib.decompress(base64.b64decode(s)))


def sar(v, n):
    return s32(v) >> n


def load_txt(excel, name):
    rows = open(os.path.join(excel, name), encoding="latin1").read().split("\n")
    hdr = rows[0].rstrip("\r").split("\t")
    out = []
    for r in rows[1:]:
        r = r.rstrip("\r")
        if not r:
            continue
        out.append(dict(zip(hdr, r.split("\t"))))
    return out


class Tables:
    def __init__(self, excel):
        self.excel = excel
        self.isc = load_txt(excel, "itemstatcost.txt")
        self.stat_id = {r["Stat"]: int(r["ID"]) for r in self.isc}
        self.charstats = [r for r in load_txt(excel, "charstats.txt") if r["class"] != "Expansion"]
        self.base = []                       # item class index -> row: weapons, armor, misc in file order
        for t in ("weapons.txt", "armor.txt", "misc.txt"):
            for r in load_txt(excel, t):
                if r.get("code"):
                    self.base.append(r)
        self.setitems = [r for r in load_txt(excel, "setitems.txt") if r["index"] != "Expansion"]
        self.sets = [r for r in load_txt(excel, "sets.txt") if r["index"] != "Expansion"]
        self.set_id = {r["index"]: i for i, r in enumerate(self.sets)}
        self.props = {}
        for r in load_txt(excel, "properties.txt"):
            slots = []
            for k in range(1, 8):
                if r.get("func%d" % k):
                    slots.append((int(r["func%d" % k]), r.get("stat%d" % k, ""), r.get("val%d" % k, "")))
            self.props[r["code"]] = slots
        self.skills = load_txt(excel, "skills.txt")
        self.skill_id = {r["skill"]: int(r["Id"]) for r in self.skills}
        self.skill_by_id = {int(r["Id"]): r for r in self.skills}
        self.states_rows = load_txt(excel, "states.txt")
        self.states = [r["state"] for r in self.states_rows]
        self.shrines = load_txt(excel, "shrines.txt")
        self.itypes = [r["Code"] for r in load_txt(excel, "itemtypes.txt")]

    def isc_graph(self):
        """What ITEMSTATCOST_Load builds (stats/0001 § 4): per stat [targets(3), dependents, opIn, b51, b52, b53]."""
        n = len(self.isc)
        tg = [[0xFFFF] * 3 for _ in range(n)]
        deps = [[] for _ in range(n)]
        opin = [[] for _ in range(n)]
        b51, b52, b53 = [0] * n, [0] * n, [0] * n
        for i, r in enumerate(self.isc):
            op = int(r["op"] or 0)
            if not 1 <= op <= 13:
                continue
            ob = self.stat_id.get(r["op base"], 0xFFFF) if r["op base"] else 0xFFFF
            opp = int(r["op param"] or 0)
            k = 0
            for c in ("op stat1", "op stat2", "op stat3"):
                if r[c]:
                    t = self.stat_id[r[c]]
                    tg[i][k] = t
                    k += 1
                    opin[t].append([ob, i, op, opp])
                    b52[t] = 1
                    b51[i] = 1
            if ob != 0xFFFF:
                b51[ob] = 1
                deps[ob].append(i)
            if op in (4, 5):
                b53[i] = 1
        return tg, deps, opin, b51, b52, b53


class ISC:
    def __init__(self, line):
        rows = unz(line["z"])
        self.n = line["n"]
        self.m270, self.m274 = line["m270"], line["m274"]
        self.f4 = [r[0] for r in rows]
        self.f5 = [r[1] for r in rows]
        self.vs = [r[2] for r in rows]
        self.minaccr = [r[3] for r in rows]
        self.keepzero = [r[4] for r in rows]
        self.b51 = [r[5] for r in rows]
        self.b52 = [r[6] for r in rows]
        self.b53 = [r[7] for r in rows]
        self.op = [r[8] for r in rows]
        self.tg = [r[9] for r in rows]
        self.deps = [r[10] for r in rows]
        self.opin = [r[11] for r in rows]
        self.tw = [r[12] if len(r) > 12 else None for r in rows]      # logger rev 1 did not dump it

    def ok(self, t):
        return 0 <= t < self.n

    def dmgrel(self, t):
        return bool(self.f4[t] & self.m270)

    def fmin(self, t):
        return bool(self.f5[t] & self.m270)

    def fcb(self, t):
        return bool(self.f5[t] & self.m274)


class Lst:
    __slots__ = ("p", "f", "s", "u", "ct", "own", "cache", "ow", "ch", "off", "parent", "x", "sk", "sl")

    def __init__(self, d):
        self.p, self.f, self.s, self.u, self.ct = d["p"], d["f"], d["s"], d["u"], d["ct"]
        self.x, self.sk, self.sl = d.get("x", 0), d.get("sk", 0), d.get("sl", 0)
        self.own = {k: v for k, v in d["own"]}
        self.cache = {k: v for k, v in d["cache"]} if "cache" in d else None
        self.ow = d.get("ow")
        self.ch, self.off, self.parent = [], [], 0

    def active(self):
        return self.cache if self.f & EXT else self.own


class Mismatch(Exception):
    pass


class Model:
    """The mirror of the player's tree and the emulation of the stat-list code."""

    def __init__(self, isc, tables, report):
        self.isc, self.t, self.rep = isc, tables, report
        self.L = {}                  # list pointer -> Lst
        self.unit_list = {}          # unit pointer -> its unit list pointer (owner +0x44 of an extended list)
        self.unit_type = {}          # unit pointer -> type
        self.unit_class = {}
        self.plr = self.plist = 0
        self.counting = False
        self.opcount = collections.Counter()      # op -> terms that added a non-zero value in a predicted write
        self.takes = collections.Counter()        # (source op, taken) of the predicted take tests
        self.paths = collections.Counter()        # StatRecompute paths predicted

    def term(self, op, v):
        if self.counting and v:
            self.opcount[op] += 1
        return v

    # ---- structure
    def add_tree(self, d, parent=0, chain="ch"):
        x = Lst(d)
        x.parent = parent
        self.L[x.p] = x
        if x.ow:
            self.unit_list[x.ow["u"]] = x.p
            self.unit_type[x.ow["u"]] = x.ow["t"]
            self.unit_class[x.ow["u"]] = x.ow["c"]
        for c in d.get("ch", []):
            x.ch.append(self.add_tree(c, x.p, "ch").p)
        for c in d.get("off", []):
            x.off.append(self.add_tree(c, x.p, "off").p)
        return x

    def drop_subtree(self, p):
        x = self.L.pop(p, None)
        if not x:
            return
        for c in x.ch + x.off:
            self.drop_subtree(c)

    def reset(self, tree, plr):
        self.L, self.unit_list = {}, {}
        root = self.add_tree(tree)
        self.plist, self.plr = root.p, plr
        self.unit_type[plr] = 0

    def utype(self, u):
        if u in self.unit_type:
            return self.unit_type[u]
        return None

    # ---- reads
    def active_get(self, x, key):
        return x.active().get(key, 0)

    def floor(self, x, key, v, rec=True):
        t = key >> 16
        if rec and x.f & EXT and x.ow and x.ow["t"] in (0, 1) and self.isc.ok(t) and self.isc.fmin(t):
            if v < self.isc.minaccr[t]:
                v = s32(self.isc.minaccr[t] << self.isc.vs[t])
        return v

    def unit_stat(self, u, t):
        """STATS_GetUnitStat (0x00625480): the unit list's active value with the fMin floor."""
        lp = self.unit_list.get(u)
        x = self.L.get(lp) if lp else None
        if not x:
            raise Mismatch("unit 0x%x has no mirrored list" % u)
        return self.floor(x, t << 16, self.active_get(x, t << 16))

    def base_stat(self, u, t):
        lp = self.unit_list.get(u)
        x = self.L.get(lp) if lp else None
        if not x:
            raise Mismatch("unit 0x%x has no mirrored list" % u)
        return self.floor(x, t << 16, x.own.get(t << 16, 0))

    def sum_own_children(self, x, key):
        t = key >> 16
        v = x.own.get(key, 0)
        if x.f & EXT:
            dmg = self.isc.dmgrel(t)
            for cp in x.ch:
                c = self.L[cp]
                if dmg and c.f & NODMG:
                    continue
                v += c.active().get(key, 0)
        return s32(v)

    def cstats(self, cls):
        return self.t.charstats[cls]

    def evaluate(self, x, key, depth=0):
        """sub_00626200_StatEvaluate (stats/0001 § 4)."""
        I = self.isc
        t = key >> 16
        if not I.ok(t):
            return 0
        v = self.sum_own_children(x, key)
        if not I.b52[t]:
            return v
        b0 = acc = v
        ow = x.ow
        for ob, src, op, opp in I.opin[t]:
            sk = src << 16
            if op == 1:
                if not ow:
                    continue
                if ow["t"] == 4:
                    b0 = self.base_stat(ow["u"], t)
                if b0:
                    p = self.evaluate(x, sk, depth + 1)
                    if p:
                        acc = s32(acc + self.term(1, muldiv(b0, p, 100)))
            elif op in (2, 3):
                if x.ct not in (0, 1) or ob == 0xFFFF or not I.ok(ob):
                    continue
                b = sar(x.active().get(ob << 16, 0), I.vs[ob])
                if b <= 0:
                    continue
                p = self.evaluate(x, sk, depth + 1)
                if not p:
                    continue
                term = sar(s32(p * b), opp)
                acc = s32(acc + self.term(op, term if op == 2 else muldiv(b0, term, 100)))
            elif op in (4, 5):
                pu = x.u
                if not pu or self.utype(pu) not in (0, 1) or ob == 0xFFFF or not I.ok(ob):
                    continue
                b = sar(self.unit_stat(pu, ob), I.vs[ob])
                if b <= 0:
                    continue
                p = self.evaluate(x, sk, depth + 1)
                if not p:
                    continue
                term = sar(s32(p * b), opp)
                acc = s32(acc + self.term(op, term if op == 4 else muldiv(b0, term, 100)))
            elif op in (6, 7):
                if ow and self.evaluate(x, sk, depth + 1):
                    raise Mismatch("op %d (by time) reached: stat %d from %d" % (op, t, src))
            elif op in (8, 9):
                if not ow or ow["t"] != 0:
                    continue
                cs = self.cstats(ow["c"])
                d = s32(self.evaluate(x, sk, depth + 1) - x.own.get(sk, 0))
                if not d:
                    continue
                f = int(cs["ManaPerMagic"] if op == 8 else cs["StaminaPerVitality"] if t == 11 else cs["LifePerVitality"])
                acc = s32(acc + self.term(op, s32(s32(f * d) << 6)))
            elif op == 11:
                if not b0 or not ow or ow["t"] not in (0, 1):
                    continue
                p = self.evaluate(x, sk, depth + 1)
                if p:
                    acc = s32(acc + self.term(11, muldiv(b0, p, 100)))
            elif op == 13:
                if not ow or ow["t"] != 4:
                    continue
                b0 = self.base_stat(ow["u"], t)
                if not b0:
                    continue
                p = self.evaluate(x, sk, depth + 1)
                if p:
                    acc = s32(acc + self.term(13, muldiv(b0, p, 100)))
        return acc

    # ---- writes (generators of the expected lines; each yields a tuple and receives the logged line)
    def take(self, x, t, k):
        r = self._take(x, t, k)
        self.takes[(self.isc.op[t], bool(r))] += 1
        return r

    def _take(self, x, t, k):
        I = self.isc
        cls = TAKE_CLASS[I.op[t]] if I.op[t] < len(TAKE_CLASS) else 0
        if cls == 5:
            return True
        if cls == 1:
            if x.ct not in (0, 1):
                return False
            w = I.tw[t][k]
            return w != 0xFFFF and x.active().get(w << 16, 0) > 0
        if cls == 2:
            pu = x.u
            if not pu or self.utype(pu) not in (0, 1):
                return False
            w = I.tw[t][k]
            return w != 0xFFFF and I.ok(w) and self.unit_stat(pu, w) > 0
        if cls == 3:
            return x.ct in (0, 1)
        if cls == 4:
            return x.ct == 4
        return False

    def recompute(self, x, key):
        I = self.isc
        t = key >> 16
        self.counting = True
        try:
            v = self.evaluate(x, key)
        finally:
            self.counting = False
        if not I.b51[t]:
            yield ("CW", x.p, key, v)
            return v
        if v == 0:
            self.paths["source evaluates to 0: early write, no dependent walk"] += 1
            yield ("CW", x.p, key, 0)
        taken = False
        for k in range(3):
            tt = I.tg[t][k]
            if tt == 0xFFFF:
                break
            tv = yield from self.recompute(x, tt << 16)
            yield ("CW", x.p, tt << 16, tv)
            if tv != 0 and self.take(x, t, k):
                taken = True
        if taken:
            self.paths["a target took: the source keeps its old cache"] += 1
        if not taken and v != 0:
            if I.deps[t]:
                self.paths["source written, dependents walked"] += 1
            yield ("CW", x.p, key, v)
            for d in I.deps[t][:64]:
                dv = yield from self.recompute(x, d << 16)
                yield ("CW", x.p, d << 16, dv)
        return v

    def propagate(self, x, key, delta):
        I = self.isc
        t = key >> 16
        if delta == 0 or not I.ok(t) or x.f & OFF:
            return
        dmg = I.dmgrel(t)
        y = x if x.f & EXT else self.L.get(x.parent)
        while y:
            if not I.b51[t] and not I.b52[t]:
                yield ("CA", y.p, key, delta)
            else:
                yield from self.recompute(y, key)
            fl, nxt = y.f, y.parent
            if fl & OFF or (dmg and fl & NODMG):
                break
            y = self.L.get(nxt)

    def link_gen(self, ul, x, dmg):
        I = self.isc
        if x.f & OFF:
            return
        if x.f & EXT and x.f & OPSRC:
            keys = [k for k in sorted(x.cache) if I.ok(k >> 16) and I.b53[k >> 16]][:16]
            for k in keys:
                yield from self.recompute(x, k)
        for k, v in sorted(x.active().items()):
            if not dmg and I.ok(k >> 16) and I.dmgrel(k >> 16):
                continue
            yield ("PRP", ul.p, k, v)

    def unlink_gen(self, x, parent):
        I = self.isc
        if x.f & OFF:
            return
        if x.f & EXT and x.f & OPSRC:
            keys = [k for k in sorted(x.cache) if I.ok(k >> 16) and I.b53[k >> 16]][:16]
            for k in keys:
                yield from self.recompute(x, k)
        if not parent:
            return
        for k, v in sorted(x.active().items()):
            if x.f & NODMG and I.ok(k >> 16) and I.dmgrel(k >> 16):
                continue
            yield ("PRP", parent.p, k, -v)

    # ---- applying a logged write
    def cache_add(self, x, key, d):
        old = x.cache.get(key)
        new = s32((old or 0) + d)
        if new == 0 and not self.isc.keepzero[key >> 16]:
            x.cache.pop(key, None)
        else:
            x.cache[key] = new
            if new > 0 and self.isc.b53[key >> 16]:
                x.f |= OPSRC
        return old or 0, new

    def cache_write(self, x, key, v):
        old = x.cache.get(key)
        if old is None and v == 0:
            return None, None
        if v == 0 and not self.isc.keepzero[key >> 16]:
            x.cache.pop(key, None)
        else:
            x.cache[key] = v
            if self.isc.b53[key >> 16]:
                x.f |= OPSRC
        return old or 0, v


class Checker:
    def __init__(self, tables, verbose=False):
        self.t = tables
        self.v = verbose
        self.n = collections.Counter()
        self.bad = collections.Counter()
        self.examples = collections.defaultdict(list)
        self.seeds = collections.defaultdict(lambda: [0, 0])     # kind -> [equal, moved]
        self.reads_by_stat = collections.Counter()
        self.opcount = collections.Counter()
        self.apply_cases = collections.Counter()
        self.takes = collections.Counter()
        self.paths = collections.Counter()
        self.apply_sources = collections.Counter()
        self.exp_late = collections.Counter()
        self.tick_cases = collections.Counter()
        self.au = {}
        self.au_sites = collections.Counter()
        self.aura_durations = collections.Counter()
        self.wells = []
        self.notes = collections.Counter()

    def fail(self, kind, msg):
        self.bad[kind] += 1
        if len(self.examples[kind]) < 12:
            self.examples[kind].append("%s:%d %s" % (self.cur_log, self.cur_line, msg))

    # ------------------------------------------------------------------ the ISC graph
    def check_isc(self, I):
        tg, deps, opin, b51, b52, b53 = self.t.isc_graph()
        n = len(self.t.isc)
        if I.n != n:
            self.fail("isc", "rows %d, table %d" % (I.n, n))
        for i in range(min(n, I.n)):
            r = self.t.isc[i]
            want = {"tg": tg[i], "deps": deps[i], "opin": opin[i], "b51": b51[i], "b52": b52[i], "b53": b53[i],
                    "vs": int(r["ValShift"] or 0), "minaccr": int(r["MinAccr"] or 0),
                    "keepzero": int(r["keepzero"] or 0), "dmg": int(r["damagerelated"] or 0),
                    "fmin": int(r["fMin"] or 0), "fcb": int(r["fCallback"] or 0),
                    "op": int(r["op"] or 0) if 1 <= int(r["op"] or 0) <= 13 else 0}
            got = {"tg": I.tg[i], "deps": I.deps[i], "opin": I.opin[i], "b51": I.b51[i], "b52": I.b52[i],
                   "b53": I.b53[i], "vs": I.vs[i], "minaccr": I.minaccr[i], "keepzero": I.keepzero[i],
                   "dmg": int(I.dmgrel(i)), "fmin": int(I.fmin(i)), "fcb": int(I.fcb(i)), "op": I.op[i]}
            for k in want:
                self.n["isc_field"] += 1
                if want[k] != got[k]:
                    self.fail("isc", "stat %d %s: table %r, memory %r" % (i, k, want[k], got[k]))
            # the take test's word: opIn[k].opBase of the row itself, 0 where the row has no opIn entry k
            for k in range(3):
                w = opin[i][k][0] if k < len(opin[i]) else 0
                if I.tw[i] is None:
                    I.tw[i] = [opin[i][j][0] if j < len(opin[i]) else 0 for j in range(3)]
                    self.notes["take words predicted (logger rev 1)"] += 1
                    break
                self.n["isc_field"] += 1
                if I.tw[i][k] != w:
                    self.fail("isc", "stat %d take word %d: predicted %d, memory %d" % (i, k, w, I.tw[i][k]))

    # ------------------------------------------------------------------ the replay
    def run_log(self, path):
        self.cur_log = os.path.basename(path)
        self.cur_line = 0
        M = None
        isc = None
        stack = []                 # frames: dict(tag, gen, pend (expected tuple or None), top, seeds)
        last_write = None          # (list, key, old, new) of the last CA/CW applied
        pend_rescale = None
        uoe = None
        rq = None
        sba_mask = {}
        with open(path, errors="replace") as fh:
            for line in fh:
                self.cur_line += 1
                tag, _, rest = line.partition(" ")
                if tag not in TAGS:
                    if tag == "LOGERR":
                        self.fail("logerr", line.strip()[:200])
                    continue
                try:
                    d = json.loads(rest)
                except ValueError:
                    self.fail("parse", line[:80])
                    continue
                if tag == "ISC":
                    isc = ISC(d)
                    self.check_isc(isc)
                    continue
                if isc is None:
                    continue
                if tag == "TREE0":
                    z = unz(d["z"])
                    M = Model(isc, self.t, self)
                    M.reset(z["t"], d["plr"])
                    stack = []
                    continue
                if M is None:
                    continue
                try:
                    r = self.step(M, tag, d, stack)
                except Mismatch as e:
                    self.fail("model", "%s: %s" % (tag, e))
                    r = None
        if stack:
            self.notes["frames open at end of log"] += len(stack)
        if M is not None:
            self.opcount.update(M.opcount)
            self.takes.update(M.takes)
            self.paths.update(M.paths)

    def next_expected(self, stack):
        """The innermost frame's next predicted line (advancing its generator), or None."""
        for fr in reversed(stack):
            if fr.get("pend") is not None:
                return fr
            gen = fr.get("gen")
            if gen is None:
                continue
            try:
                fr["pend"] = next(gen)
                return fr
            except StopIteration:
                fr["gen"] = None
                continue
            break
        return None

    def take_expected(self, stack, kind):
        """Pop the next expected line of the innermost frame with a generator."""
        for fr in reversed(stack):
            if fr.get("gen") is None and fr.get("pend") is None:
                if fr["tag"] in ("PRP", "LNK", "ULK"):
                    return fr, None          # this frame is exhausted: nothing expected
                continue
            if fr.get("pend") is None:
                try:
                    fr["pend"] = next(fr["gen"])
                except StopIteration:
                    fr["gen"] = None
                    return fr, None
            e = fr["pend"]
            fr["pend"] = None
            return fr, e
        return None, None

    def step(self, M, tag, d, stack):
        I = M.isc
        if tag in ("CA", "CW"):
            x = M.L.get(d["l"])
            if not x or x.cache is None:
                self.fail("structure", "%s on an unmirrored list 0x%x" % (tag, d["l"]))
                return
            fr, e = self.take_expected(stack, tag)
            key = d["k"]
            old_m = x.cache.get(key)
            if old_m != d["o"]:
                self.fail("old", "%s list 0x%x key %d/%d: log old %r, mirror %r" % (tag, x.p, key >> 16, key & 0xFFFF,
                                                                                 d["o"], old_m))
            if fr is None:
                self.notes["unframed " + tag] += 1
            elif e is None:
                self.fail("extra", "%s list 0x%x key %d: no write predicted" % (tag, x.p, key >> 16))
            else:
                self.n[tag] += 1
                val = d["d"] if tag == "CA" else d["v"]
                if e[0] != tag or e[1] != d["l"] or e[2] != key or e[3] != val:
                    self.fail("write", "%s 0x%x %d/%d %d, predicted %s 0x%x %d/%d %d" % (
                        tag, d["l"], key >> 16, key & 0xFFFF, val, e[0], e[1], e[2] >> 16, e[2] & 0xFFFF, e[3]))
                    # resync the generator: drop the frame's remaining prediction
                    fr["gen"], fr["pend"] = None, None
            if tag == "CA":
                old, new = M.cache_add(x, key, d["d"])
            else:
                old, new = M.cache_write(x, key, d["v"])
            if x.p == M.plist and old is not None and old != new and I.fcb(key >> 16):
                self.pending_cb = (key, old, new)
            else:
                self.pending_cb = None
            return
        if tag == "SCB":
            p = getattr(self, "pending_cb", None)
            self.n["CB"] += 1
            if not p or p != (d["k"], d["o"], d["n"]):
                self.fail("callback", "CB key %d %d->%d, predicted %r" % (d["k"] >> 16, d["o"], d["n"], p))
            self.pending_cb = None
            k = d["k"] >> 16
            if k in (7, 9, 11) and d["n"] != d["o"] and d["o"] > 0:
                cur_stat = k - 1
                cur = M.unit_stat(M.plr, cur_stat)
                if cur > 0:
                    old = max(d["o"], 256)
                    q = struct.unpack("<f", struct.pack("<f", d["n"] / old * cur))[0]
                    r = int(q)
                    r = max(r, 1)
                    res = r if r < d["n"] else d["n"]
                    own = M.L[M.plist].own.get(cur_stat << 16, 0)
                    self.rescale = (cur_stat << 16, res, own)
                    self.n["rescale"] += 1
                    self.rescale_cases = getattr(self, "rescale_cases", collections.Counter())
                    self.rescale_cases["stat %d %s%s%s%s" % (
                        k, "rises" if d["n"] > d["o"] else "falls", " old<=256" if d["o"] <= 256 else "",
                        " r<=1" if int(q) <= 1 else "", " capped" if res == d["n"] else "")] += 1
                    if res == own:
                        self.rescale = None
                        self.n["rescale_nochange"] += 1
            return
        if tag == "PRP":
            x = M.L.get(d["l"])
            if not x:
                self.fail("structure", "PRP on an unmirrored list 0x%x" % d["l"])
                stack.append({"tag": "PRP", "gen": None, "pend": None, "top": d["top"], "d": d})
                return
            ra = d["ra"]
            if ra in WRITERS:
                # an own write: the entry has changed by delta before the call
                old = x.own.get(d["k"], 0)
                new = s32(old + d["d"])
                got = d["own"] if d["own"] is not None else 0
                self.n["own_write"] += 1
                if new != got:
                    self.fail("own", "own write list 0x%x key %d: mirror %d + %d = %d, log %d" % (
                        x.p, d["k"] >> 16, old, d["d"], new, got))
                if new:
                    x.own[d["k"]] = new
                else:
                    x.own.pop(d["k"], None)
                rs = getattr(self, "rescale", None)
                if rs and x.p == M.plist and d["k"] == rs[0]:
                    self.n["rescale_checked"] += 1
                    if got != rs[1]:
                        self.fail("rescale", "stat %d rescaled to %d, predicted %d" % (rs[0] >> 16, got, rs[1]))
                    self.rescale = None
            elif ra in LINK_RA or ra in UNLINK_RA:
                fr, e = self.take_expected(stack, "PRP")
                self.n["PRP_link"] += 1
                if e is None or e[0] != "PRP" or e[1] != d["l"] or e[2] != d["k"] or e[3] != d["d"]:
                    self.fail("link_prp", "PRP 0x%x %d/%d %d, predicted %r" % (d["l"], d["k"] >> 16, d["k"] & 0xFFFF,
                                                                            d["d"], e))
            elif ra in DMG_RA:
                self.n["PRP_dmg"] += 1
            else:
                self.notes["PRP from 0x%x" % ra] += 1
            if d["top"]:
                self.seed_open(stack, "own_write" if ra in WRITERS else "propagate", d)
            stack.append({"tag": "PRP", "gen": M.propagate(x, d["k"], d["d"]), "pend": None, "top": d["top"], "d": d})
            return
        if tag == "PRX":
            self.close(stack, "PRP", d)
            return
        if tag == "LNK":
            sub = unz(d["sub"])
            ul = M.L.get(d["ul"])
            if not ul:
                self.fail("structure", "LNK to an unmirrored unit list 0x%x" % d["ul"])
                stack.append({"tag": "LNK", "gen": None, "pend": None, "top": d["top"], "d": d})
                return
            old = M.L.get(sub["p"])
            if old is not None and old.parent:
                self.notes["LNK of a linked list"] += 1
            M.drop_subtree(sub["p"])
            x = M.add_tree(sub)
            if x.f & 4:
                ul.f |= 2
            x.parent, x.u = ul.p, d["u"]
            (ul.off if x.f & OFF else ul.ch).insert(0, x.p)
            if not x.f & OFF:
                if d["dmg"]:
                    x.f &= ~NODMG
                else:
                    x.f |= NODMG
            self.n["LNK"] += 1
            if not d["dmg"]:
                self.n["LNK_nodmg"] += 1
            if d["top"]:
                self.seed_open(stack, "link", d)
            stack.append({"tag": "LNK", "gen": M.link_gen(ul, x, d["dmg"]), "pend": None, "top": d["top"], "d": d})
            return
        if tag == "LNX":
            self.close(stack, "LNK", d)
            return
        if tag == "ULK":
            x = M.L.get(d["l"])
            if not x:
                self.fail("structure", "ULK of an unmirrored list 0x%x" % d["l"])
                stack.append({"tag": "ULK", "gen": None, "pend": None, "top": d["top"], "d": d})
                return
            par = M.L.get(x.parent)
            if par:
                if x.p in par.ch:
                    par.ch.remove(x.p)
                if x.p in par.off:
                    par.off.remove(x.p)
            x.parent, x.u = 0, 0
            self.n["ULK"] += 1
            e = getattr(self, "exp", None)
            if e is not None:
                e["freed"].add(x.p)
            if d["top"]:
                self.seed_open(stack, "unlink", d)
            stack.append({"tag": "ULK", "gen": M.unlink_gen(x, par), "pend": None, "top": d["top"], "d": d})
            return
        if tag == "ULX":
            self.close(stack, "ULK", d)
            return
        if tag == "TGL":
            self.n["TGL"] += 1
            tip = getattr(self, "tip", None)
            if tip is not None and d["u"] == tip["it"]:
                self.n["TGL_aprop"] += 1
                if not tip["want"]:
                    self.fail("set_toggle", "toggle state %d off %d of item 0x%x: none predicted" % (d["st"], d["off"],
                                                                                                    d["u"]))
                else:
                    w = tip["want"].pop(0)
                    if w != (d["st"], d["off"]):
                        self.fail("set_toggle", "toggle (state, off) %r, predicted %r" % ((d["st"], d["off"]), w))
            if d["top"]:
                self.seed_open(stack, "toggle", d)
            stack.append({"tag": "TGL", "gen": None, "pend": None, "top": d["top"], "d": d})
            return
        if tag == "TGX":
            self.close(stack, "TGL", d)
            return
        if tag == "TREE":
            if stack:
                self.notes["TREE inside a frame"] += 1
            self.compare_tree(M, unz(d["z"]), d)
            return
        if tag == "RD":
            x = M.L.get(M.plist)
            key = d["k"]
            want = M.floor(x, key, x.active().get(key, 0), d["r"])
            self.n["RD"] += 1
            self.reads_by_stat[key >> 16] += 1
            if want != d["v"]:
                self.fail("read", "read %d/%d = %d, predicted %d" % (key >> 16, key & 0xFFFF, d["v"], want))
            return
        if tag in ("TK0", "TK1"):
            if tag == "TK0":
                self.tk = d
                self.tk_pred = self.predict_tick(M, d)
            else:
                a = getattr(self, "tk", None)
                if a:
                    self.seed_pair("tick", a, d)
                    p = getattr(self, "tk_pred", None)
                    if p is not None and "v" in d and len(d["v"]) >= 6:
                        got = {6: d["v"][0], 10: d["v"][4], 8: d["v"][2]}
                        self.n["tick"] += 1
                        for k, (v, why) in p.items():
                            self.tick_cases[why] += 1
                            if got[k] != v:
                                self.fail("tick", "stat %d after the tick %r, predicted %d (%s; in %r mode %d)" % (
                                    k, got[k], v, why, a["v"], a["m"]))
                self.tk = None
            return
        if tag in ("UOE", "MSK", "TIP", "UOB", "SBA", "SBX", "UOX"):
            self.sets_step(M, tag, d, stack)
            return
        if tag in ("RQ0", "RQ91", "RQS", "RQD", "RQL", "RQF", "RQX"):
            self.req_step(M, tag, d)
            return
        if tag == "DMG":
            self.n["DMG_" + d["k"]] += 1
            it = d["it"]
            lp = M.unit_list.get(it)
            x = M.L.get(lp) if lp else None
            if x and x.u == M.plr:
                if d["k"] == "off":
                    x.f |= NODMG
                else:
                    x.f &= ~NODMG
            return
        if tag == "PAS":
            self.pas = d["sk"]
            self.n["PAS"] += 1
            return
        if tag == "PAX":
            self.passive_check(M, getattr(self, "pas", None))
            self.pas = None
            return
        if tag in ("EQR", "EQX"):
            self.n[tag] += 1
            return
        if tag in ("STA0", "STA1", "EXP0", "EXP1", "AU0", "AU1", "GRP", "GRX", "SHR0", "SHR1", "WEL0", "WEL1", "RNGA"):
            self.states_step(M, tag, d, stack)
            return

    # ------------------------------------------------------------------ states (stats/0002 § 2-5)
    def sflag(self, state, col):
        r = self.t.states_rows[state] if 0 <= state < len(self.t.states_rows) else {}
        return r.get(col, "") == "1"

    def states_step(self, M, tag, d, stack):
        if tag == "STA0":
            self.n["apply_%s" % d["w"]] += 1
            r = self.t.skill_by_id.get(d["sk"])
            if r is not None and r.get("aura") == "1" and d.get("src") and d["len"]:
                # an aura's target state lasts to one frame past the next run on the perdelay grid
                # (SKILLS_NextPeriodicFrame: ((f - 1 + p) / p) p + 1, p = perdelay, 5 below 6)
                pd = int(r.get("perdelay") or 0)
                pd = pd if pd >= 6 else 5
                fr = d["fr"]
                want = ((fr - 1 + pd) // pd) * pd + 1 + 1 - fr
                self.n["aura_duration"] += 1
                self.aura_durations[(d["sk"], d["len"])] += 1
                if d["len"] != want:
                    self.fail("aura_len", "skill %d at frame %d: duration %d, predicted %d (perdelay %d)" % (
                        d["sk"], fr, d["len"], want, pd))
            self.sta = d
            self.sta_pred = self.predict_apply(M, d) if d["w"] == "p" else None
            if d["w"] == "p":
                self.apply_sources[(d["state"], d["sk"], d.get("srct"))] += 1
            return
        if tag == "STA1":
            a = getattr(self, "sta", None)
            self.sta = None
            if not a:
                return
            self.seed_pair("apply", {"gs": a["gs"], "us": a["us"]}, d)
            p = getattr(self, "sta_pred", None)
            if p is None:
                return
            self.n["apply_checked"] += 1
            kind = p[0]
            self.apply_cases[(kind, a["state"])] += 1
            if kind == "refuse":
                if d["r"] != 0:
                    self.fail("apply", "state %d: refusal predicted (%s), got list 0x%x" % (a["state"], p[1], d["r"]))
                return
            if d["r"] == 0:
                self.fail("apply", "state %d: %s predicted, refused" % (a["state"], kind))
                return
            if kind == "refresh":
                if d["r"] != p[1].p:
                    self.fail("apply", "state %d: refresh of 0x%x predicted, got 0x%x" % (a["state"], p[1].p, d["r"]))
                if p[2] is not None and d["x"] != p[2]:
                    self.fail("apply", "state %d refresh: expiry %d, predicted %d" % (a["state"], d["x"], p[2]))
                x = M.L.get(d["r"])
                if x is not None and p[2] is not None:
                    x.x = d["x"]
                    x.f |= 2
                return
            # new (or replace): the list made
            want = p[1]
            got = {"f": d["f"] & 0x82A, "s": d["s"], "x": d["x"], "sk": d["sk"], "sl": d["sl"],
                   "own": {k: v for k, v in d["own"]}, "pa": d["pa"]}
            for k in want:
                if got[k] != want[k]:
                    self.fail("apply", "state %d %s: %s %r, predicted %r" % (a["state"], kind, k, got[k], want[k]))
            if kind == "replace" and p[2] in M.L and M.L[p[2]].parent:
                self.fail("apply", "state %d replace: the old list 0x%x is still linked" % (a["state"], p[2]))
            x = M.L.get(d["r"])
            if x is not None:
                x.x, x.sk, x.sl = d["x"], d["sk"], d["sl"]
            return
        if tag == "EXP0":
            fr = d["fr"]
            want = {c for c, f, st, x in d["x"] if f & 2 and not f & EXT and x <= fr}
            self.exp = {"d": d, "want": want, "freed": set()}
            for c, f, st, x in d["x"]:
                if f & 2 and x <= fr:
                    self.exp_late[fr - x] += 1
            return
        if tag == "EXP1":
            e = getattr(self, "exp", None)
            self.exp = None
            if not e:
                return
            self.seed_pair("expire", e["d"], d)
            self.n["expire_runs"] += 1
            if e["want"] != e["freed"]:
                self.fail("expire", "freed %r, predicted %r" % (sorted(e["freed"]), sorted(e["want"])))
            self.n["expired_lists"] += len(e["freed"])
            if not e["freed"]:
                self.n["expire_runs_freeing_nothing"] += 1
            return
        if tag == "AU0":
            self.au.setdefault((d["w"], d["k"]), []).append(d["fr"])
            self.au_open = d
            self.au_rng = []
            return
        if tag == "RNGA":
            if getattr(self, "au_open", None) is not None:
                self.au_rng.append(d)
            return
        if tag == "AU1":
            a = getattr(self, "au_open", None)
            self.au_open = None
            if not a:
                return
            if a["gs"] == d["gs"] and a["us"] == d["us"]:
                self.seeds["aura"][0] += 1
                if self.au_rng:
                    self.fail("aura_rng", "%d LCG step(s) in an aura run that left both seeds unchanged" %
                              len(self.au_rng))
                return
            # the run drew: chain it (ADR-0014). Each RNGA line is one LCG step; the caster's seed must have moved
            # by exactly that many steps and the game seed not at all
            self.seeds["aura"][1] += 1
            k = lcg_distance(a["us"], d["us"], 256)
            sites = collections.Counter((r["pc"], r.get("ra2")) for r in self.au_rng)
            for site in sites:
                self.au_sites[(hex(site[0]), hex(site[1] or 0), a["w"], a["k"])] += sites[site]
            self.n["aura_chained"] += 1
            if a["gs"] != d["gs"] or k is None or k != len(self.au_rng):
                self.fail("aura_rng", "aura run %s/%s: unit seed %s -> %s is %r step(s), %d LCG line(s); game seed %s"
                          % (a["w"], a["k"], a["us"], d["us"], k, len(self.au_rng),
                             "same" if a["gs"] == d["gs"] else "moved"))
            else:
                self.n["aura_chained_steps"] += k
            return
        if tag == "GRP":
            grp = self.t.states_rows[d["st"]].get("group", "") if 0 <= d["st"] < len(self.t.states_rows) else ""
            want = set(d["sb"])
            if grp not in ("", "0"):
                for sbit in d["sb"]:
                    if self.t.states_rows[sbit].get("group", "") == grp and (sbit != d["st"] or d["self"]):
                        want.discard(sbit)
            self.grp = (d, want)
            return
        if tag == "GRX":
            g = getattr(self, "grp", None)
            self.grp = None
            if not g:
                return
            self.n["group_clear"] += 1
            cleared = set(g[0]["sb"]) - set(d["sb"])
            if cleared:
                self.n["group_clear_effective"] += 1
            if set(d["sb"]) != g[1]:
                self.fail("group", "group clear of state %d: bits %r, predicted %r" % (
                    g[0]["st"], sorted(set(d["sb"]) ^ set(g[0]["sb"])), sorted(set(g[0]["sb"]) - g[1])))
            return
        if tag == "SHR0":
            self.shr = d
            return
        if tag == "SHR1":
            a = getattr(self, "shr", None)
            self.shr = None
            if a:
                self.seed_pair("shrine", a, d)
                self.n["shrine"] += 1
            return
        if tag == "WEL0":
            self.wel = d
            return
        if tag == "WEL1":
            a = getattr(self, "wel", None)
            self.wel = None
            if a:
                self.seed_pair("well", a, d)
                self.n["well"] += 1
                self.wells.append((a, d))
            return

    def predict_apply(self, M, d):
        """STATE_ApplyTimed (stats/0002 § 2, 0x0056E970-0x0056EBDD) on the player: refuse, refresh, replace or new,
        with the list it makes."""
        state, dur = d["state"], d["len"]
        curse = self.sflag(state, "curse")
        if curse:
            r = M.unit_stat(M.plr, 109)
            if r >= 100:
                return ("refuse", "curse resistance %d" % r)
            if r:
                dur = s32(dur - muldiv(dur, r, 100))
            if 57 in d["sb"]:
                return ("refuse", "attract")
        root = M.L[M.plist]
        if curse:
            old = next((M.L[c] for c in root.ch if M.L[c].f & 0x20), None)
        else:
            old = next((M.L[c] for c in root.ch if M.L[c].s == state), None)
        kind = "new"
        if old is not None:
            if old.s == state and old.sk == d["sk"]:
                if old.sl == d["sl"]:
                    return ("refresh", old, d["fr"] + dur if dur else None)
                if d["sl"] < old.sl:
                    return ("refuse", "lower level")
            kind = "replace"
        flags = (0x20 if curse else 0) | (2 if dur else 0) | (0x800 if self.sflag(state, "exp") else 0) | \
            (8 if self.sflag(state, "aura") else 0)
        own = {d["stat"] << 16: d["val"]} if d["stat"] != -1 and d["val"] else {}
        want = {"f": flags, "s": state, "x": d["fr"] + dur if dur else 0, "sk": d["sk"], "sl": d["sl"],
                "own": own, "pa": M.plist}
        return (kind, want, old.p if old is not None else None)

    # ------------------------------------------------------------------ the regeneration tick (stats/0002 § 6)
    def predict_tick(self, M, d):
        v = d.get("v")
        if not v or len(v) < 10 or "m" not in d:
            return None
        if not hasattr(self, "tick_cases"):
            self.tick_cases = collections.Counter()
        st = lambda k: M.unit_stat(M.plr, k)
        out = {}
        # life, sub_00580610_LifeRegenTick (0x0058061B-0x0058066E)
        r = st(74)
        hp = st(6)
        if r:
            n = s32(hp + r)
            mx = st(7)
            why = "life +74"
            if n > mx:
                n, why = mx, "life capped"
            if n < 256:
                n, why = 256, "life floored at 256"
            out[6] = (n, why)
        else:
            out[6] = (hp, "life no 74")
        # stamina, PLAYER_StaminaRegenTick (jump table 0x005805B8 by mode)
        s, b, m = st(10), st(28), d["m"]
        shift, go = 8, True
        if m in (1, 5):
            shift = 8
        elif m == 6:
            shift = 9
        elif m == 2:
            shift = 9
            if s < 256:
                go = False
        else:
            go = b >= 1000
        why = "stamina mode %d" % m
        if go:
            mx = st(11)
            if s < mx:
                dd = mx >> shift
                if b:
                    t = dd * b
                    dd += abs(t) // 100 * (1 if t >= 0 else -1)
                s = min(s + dd, mx)
                why += " +%d" % dd
            else:
                why += " full"
        else:
            why += " none"
        out[10] = (s, why)
        # mana, PLAYER_ManaRegenTick (0x005806F0-0x005807EB)
        cur, mx = st(8), st(9)
        dm = 0
        if 85 not in d.get("sb", []):
            k = int(self.t.charstats[M.unit_class.get(M.plr, 0)]["ManaRegen"] or 0) * 25 or 7500
            dm = int(mx / k) if mx >= 0 else -int(-mx / k)
            if dm < 1:
                dm = 1
            dm = muldiv(dm, st(27) + 100, 100)
            why = "mana regen"
        else:
            why = "mana state 85"
        dm += st(26)
        dm = min(dm, mx - cur)
        dm = max(dm, -cur)
        out[8] = (cur + dm, why)
        return out

    def seed_open(self, stack, kind, d):
        self.open_seed = (kind, d)

    def seed_pair(self, kind, a, b):
        same = a.get("gs") == b.get("gs") and a.get("us") == b.get("us")
        self.seeds[kind][0 if same else 1] += 1
        if not same:
            self.fail("seed", "%s moved a seed: %s/%s -> %s/%s" % (kind, a.get("gs"), a.get("us"), b.get("gs"),
                                                                  b.get("us")))

    def close(self, stack, tag, d):
        if not stack or stack[-1]["tag"] != tag:
            self.fail("nesting", "%s exit without its entry" % tag)
            # drop to the matching frame
            while stack and stack[-1]["tag"] != tag:
                stack.pop()
            if not stack:
                return
        fr = stack.pop()
        rest = []
        if fr.get("pend") is not None:
            rest.append(fr["pend"])
        if fr.get("gen") is not None:
            for e in fr["gen"]:
                rest.append(e)
                if len(rest) > 5:
                    break
        if rest:
            self.fail("missing", "%s ended with %d predicted line(s) not seen: %r" % (tag, len(rest), rest[:3]))
        else:
            self.n[tag + "_frames"] += 1
        if fr["top"]:
            kind = {"PRP": "own_write" if fr["d"]["ra"] in WRITERS else "propagate", "LNK": "link", "ULK": "unlink",
                    "TGL": "toggle"}[tag]
            self.seed_pair(kind, fr["d"], d)

    # ------------------------------------------------------------------ the tree
    def compare_tree(self, M, z, d):
        self.n["TREE"] += 1
        seen = set()

        def walk(n, parent, chain):
            x = M.L.get(n["p"])
            seen.add(n["p"])
            if x is None:
                self.fail("drift", "list 0x%x (state %d) not mirrored" % (n["p"], n["s"]))
            else:
                own = {k: v for k, v in n["own"]}
                if own != x.own:
                    diff = sorted(set(own.items()) ^ set(x.own.items()))[:4]
                    self.fail("drift", "list 0x%x own differs: %r" % (n["p"], diff))
                if "cache" in n:
                    cache = {k: v for k, v in n["cache"]}
                    if x.cache != cache:
                        diff = sorted(set(cache.items()) ^ set((x.cache or {}).items()))[:4]
                        self.fail("drift", "list 0x%x cache differs: %r" % (n["p"], diff))
                # bit 1 of an extended unit list ("holds a mode-drop list", set by STATLIST_LinkToUnit) is cleared by
                # the mode-change drop, which is not mirrored: compared on plain lists only
                mask = EXT | OFF | NODMG | OPSRC | 0x4 | 0x20 | 0x40 | 0x800 | 0x8 | (0 if n["f"] & EXT else 0x2)
                if (x.f ^ n["f"]) & mask:
                    self.fail("drift", "list 0x%x flags 0x%x, mirror 0x%x" % (n["p"], n["f"], x.f))
                if x.parent != parent:
                    self.fail("drift", "list 0x%x parent 0x%x, mirror 0x%x" % (n["p"], parent, x.parent))
                # the full evaluation of every cached key (the invariant the propagation keeps), except op sources
                # whose target took (they keep an old value, stats/0001 § 3)
            for c in n.get("ch", []):
                walk(c, n["p"], "ch")
            for c in n.get("off", []):
                walk(c, n["p"], "off")
        walk(z["t"], 0, "ch")
        reach, todo = set(), [M.plist]
        while todo:
            q = todo.pop()
            if q in reach or q not in M.L:
                continue
            reach.add(q)
            todo.extend(M.L[q].ch + M.L[q].off)
        extra = [p for p in reach if p not in seen]
        if extra:
            self.fail("drift", "%d mirrored list(s) not in the tree" % len(extra))
        M.reset(z["t"], d["plr"])
        self.check_invariant(M)

    def check_invariant(self, M):
        """Every cache entry of every extended list equals its evaluation, except the stale op sources."""
        I = M.isc
        for x in list(M.L.values()):
            if not x.f & EXT:
                continue
            keys = set(x.cache)
            for k in x.own:
                keys.add(k)
            for cp in x.ch:
                keys.update(M.L[cp].active().keys())
            for key in sorted(keys):
                t = key >> 16
                if not I.ok(t):
                    continue
                try:
                    v = M.evaluate(x, key)
                except Mismatch as e:
                    self.fail("model", str(e))
                    continue
                c = x.cache.get(key, 0)
                stale_ok = I.b51[t] and any(I.tg[t][k] != 0xFFFF for k in range(3))
                self.n["eval"] += 1
                if v != c:
                    if stale_ok:
                        self.n["eval_stale_source"] += 1
                        continue
                    if x.ow and x.ow["t"] == 4 and any(op in (4, 5) and self.src_nonzero(M, x, src)
                                                       for ob, src, op, opp in I.opin[t]):
                        # an op-4/5 term reads the wearer's level, which no propagation reaches: the item keeps
                        # the value of its last link or recompute (seen after a level-up)
                        self.n["eval_stale_op45_item"] += 1
                        continue
                    self.fail("eval", "list 0x%x (owner %s) stat %d/%d cache %d, evaluated %d" % (
                        x.p, (x.ow or {}).get("c"), t, key & 0xFFFF, c, v))
                elif I.b52[t]:
                    self.n["eval_op_target"] += 1

    def src_nonzero(self, M, x, src):
        try:
            return M.evaluate(x, src << 16) != 0
        except Mismatch:
            return False

    # ------------------------------------------------------------------ sets
    def sets_step(self, M, tag, d, stack):
        if tag == "UOE":
            inv = unz(d["inv"])
            it = d["it"]
            self.uoe = {"it": it, "mode": d["mode"], "x": d["x"], "inv": inv, "mask": None, "tgl": []}
            self.n["UOE"] += 1
            return
        u = getattr(self, "uoe", None)
        if tag == "MSK":
            if not u:
                return
            it = u["it"]
            si = self.t.setitems[it["fi"]]
            sid = self.t.set_id[si["set"]]
            want = 0
            for e in u["inv"]:
                if e.get("t") != 4 or e.get("pg") != 3 or e.get("q") != 5:
                    continue
                if e["fl"] & 0x4000 or e["fl"] & 0x100:
                    continue
                r = self.t.setitems[e["fi"]]
                if self.t.set_id[r["set"]] != sid:
                    continue
                members = [i for i, s in enumerate(self.t.setitems) if s["set"] == r["set"]]
                want |= 1 << members.index(e["fi"])
            # the item itself is in page 3 only when equipped; its own flags are those of the listing
            self.n["mask"] += 1
            if want != d["m"]:
                self.fail("set_mask", "set %s item %d mode %d: mask %d, predicted %d" % (si["set"], it["fi"], u["mode"],
                                                                                       d["m"], want))
            u["mask"] = d["m"]
            self.last_mask = (sid, d["m"])
            return
        if tag == "SBX":
            mask = getattr(self, "last_mask", None)
            if not mask:
                return
            sid, m = mask
            n = bin(m).count("1")
            want = self.set_list(sid, n)
            lists = [l for l in d["lists"] if any(k == 71 << 16 and v == sid for k, v in l[2])] or \
                [l for l in d["lists"] if sid == 0]
            if len(lists) != 1:
                self.fail("set_list", "set %d: %d lists of state %d hold stat 71 = %d" % (sid, len(lists), d["st"],
                                                                                         sid))
                return
            got = {(k >> 16, k & 0xFFFF): v for k, v in lists[0][2]}
            self.n["set_list"] += 1
            self.set_counts = getattr(self, "set_counts", collections.Counter())
            self.set_counts[(self.t.sets[sid]["index"], n)] += 1
            if want is None:
                self.notes["set list not predicted (property func)"] += 1
            elif got != want:
                diff = sorted(set(got.items()) ^ set(want.items()))[:6]
                self.fail("set_list", "set %s n=%d: list differs %r" % (self.t.sets[sid]["index"], n, diff))
            return
        if tag == "TIP":
            if not u:
                return
            r = self.t.setitems[u["it"]["fi"]]
            func = int(r.get("add func") or 0)
            m = d["m"]
            want = []
            if func == 2:
                c = (bin(m).count("1") if m < 64 else 0) - 1           # g_PopCount6B 0x006EE440
                for k in range(max(c, 0)):
                    want.append((165 + k, 0))
                for k in range(max(c, 0), 5):
                    want.append((165 + k, 1))
            elif func == 1:
                members = [i for i, s in enumerate(self.t.setitems) if s["set"] == r["set"]]
                own = members.index(u["it"]["fi"])
                for k in range(6):
                    if k == own:
                        continue
                    slot = k if k < own else k - 1
                    want.append((165 + slot, 0 if m >> k & 1 else 1))
            self.tip = {"it": d["it"], "want": want, "func": func}
            self.n["TIP_func%d" % func] += 1
            return
        if tag in ("UOB", "UOX"):
            tip = getattr(self, "tip", None)
            if tip is not None:
                if tip["want"]:
                    self.fail("set_toggle", "%d predicted toggle(s) not seen: %r" % (len(tip["want"]), tip["want"][:3]))
                else:
                    self.n["TIP_checked"] += 1
                self.tip = None
            if tag == "UOX":
                self.uoe = None
            return

    def set_list(self, sid, n):
        """The wearer's set list for n worn members: stat 71 = set id, partial blocks 0 .. 2 min(n, m-1) - 3 (pairs
        PCode2a/2b, 3a/3b, ...), and the full blocks FCode1..8 when n >= m (stats/0001 § 7)."""
        s = self.t.sets[sid]
        m = sum(1 for r in self.t.setitems if r["set"] == s["index"])
        out = collections.Counter()
        out[(71, 0)] += sid
        blocks = []
        k = 2
        names = []
        for j in range(2, 6):
            for ab in "ab":
                names.append(("PCode%d%s" % (j, ab), "PParam%d%s" % (j, ab), "PMin%d%s" % (j, ab), "PMax%d%s" % (j, ab)))
        last = 2 * min(n, m - 1) - 3
        for i, nm in enumerate(names):
            if i > last:
                break
            if s.get(nm[0]):
                blocks.append(nm)
        if n >= m:
            for j in range(1, 9):
                nm = ("FCode%d" % j, "FParam%d" % j, "FMin%d" % j, "FMax%d" % j)
                if not s.get(nm[0]):
                    break
                blocks.append(nm)
        for c, p, lo, hi in blocks:
            r = self.prop_stats(s[c], s.get(p, ""), s.get(lo, ""), s.get(hi, ""))
            if r is None:
                return None
            for k, v in r.items():
                out[k] += v
        return {k: v for k, v in out.items() if v}

    def prop_stats(self, code, par, lo, hi):
        slots = self.t.props.get(code)
        if not slots:
            return None
        lo = int(lo) if lo not in ("", None) else 0
        hi = int(hi) if hi not in ("", None) else lo
        if lo != hi:
            return None
        v = lo
        out = collections.Counter()
        for fn, stat, val in slots:
            sid = self.t.stat_id.get(stat) if stat else None
            if fn in (1, 2, 3, 8) and sid is not None:
                out[(sid, 0)] += v
            elif fn == 17 and sid is not None:
                out[(sid, 0)] += int(par)
            elif fn == 21 and sid is not None:
                out[(sid, int(val))] += v
            elif fn == 22 and sid is not None:
                out[(sid, self.t.skill_id.get(par, int(par) if par.isdigit() else 0))] += v
            elif fn == 10 and sid is not None:
                pv = int(par)
                out[(sid, pv % 3 + (pv // 3) * 8)] += v
            elif fn == 7 and sid is None:
                out[(17, 0)] += v
                out[(18, 0)] += v
            else:
                return None
        return out

    # ------------------------------------------------------------------ requirements
    def req_step(self, M, tag, d):
        if tag == "RQ0":
            self.rq = {"it": d["it"], "self": d["self"]}
            return
        q = getattr(self, "rq", None)
        if q is None:
            return
        if tag == "RQ91":
            q["s91"] = d["v"]
        elif tag == "RQS":
            q["ss"] = d["v"]
        elif tag == "RQD":
            q["sd"] = d["v"]
        elif tag == "RQL":
            q["lvl"] = d["v"]
        elif tag == "RQF":
            q["flags"] = (d["so"], d["do"], d["lo"])
        elif tag == "RQX":
            self.rq = None
            it = q["it"]
            b = self.t.base[it["c"]]
            rs = int(b.get("reqstr") or 0)
            rd = int(b.get("reqdex") or 0)
            s91 = q.get("s91", 0) or 0
            xs = muldiv(rs, s91, 100) if s91 else 0
            xd = muldiv(rd, s91, 100) if s91 else 0
            eth = bool(it["fl"] & 0x400000)
            if eth:
                xs, xd = xs - 10, xd - 10
            strv = M.unit_stat(M.plr, 0)
            dexv = M.unit_stat(M.plr, 2)
            # sub_0062EAF0_ItemReqCheck (0x0062EBC2-0x0062EC75): > 0 and >= the requirement, then again without the
            # item's own contribution when asked (self) and the item is worn (RQS / RQD logged only then)
            so = int(strv > 0 and strv >= rs + xs)
            if so and "ss" in q:
                v = strv - q["ss"]
                so = int(v > 0 and v >= rs + xs)
            do = int(dexv > 0 and dexv >= rd + xd)
            if do and "sd" in q:
                v = dexv - q["sd"]
                do = int(v > 0 and v >= rd + xd)
            lvl = q.get("lvl", -1)
            lo = int(lvl == -1 or M.unit_stat(M.plr, 12) >= lvl)
            ident = int(bool(it["fl"] & 0x10))
            want = int(so and do and lo and ident)            # the class test passes for every logged item [I]
            self.n["req"] += 1
            self.req_cases = getattr(self, "req_cases", collections.Counter())
            self.req_cases[(want, "eth" if eth else "", "s91" if s91 else "", "unid" if not ident else "",
                            "self" if "ss" in q else "", "strfail" if not so else "", "lvlfail" if not lo else "")] += 1
            fl = q.get("flags")
            if fl is not None:
                self.n["req_flags"] += 1
            if d["r"] != want or (fl is not None and fl != (so, do, lo)):
                self.fail("req", "item class %d fl 0x%x: r %d flags %r, predicted r %d flags %r "
                                 "(unit str %d dex %d, req %d/%d, s91 %d, self %r/%r, lvl %r)" % (
                                     it["c"], it["fl"], d["r"], fl, want, (so, do, lo), strv, dexv, rs, rd,
                                     s91, q.get("ss"), q.get("sd"), lvl))

    def passive_check(self, M, sk):
        """SKILLS_RefreshPassive (stats/0002 § 4): the passivestate list holds passivestat1..5 = passivecalc at the
        level the list records in 351 (an input: the skill level with its bonuses), param = passiveitype, and
        350 = the skill. The stock passive calcs are ln12, ln34, dm12, dm56 (data/calc)."""
        r = self.t.skill_by_id.get(sk)
        if r is None or not r.get("passivestate"):
            return
        st = self.t.states.index(r["passivestate"])
        lists = [x for x in M.L.values() if x.s == st and x.parent == M.plist]
        if not lists:
            self.n["passive_absent"] += 1
            return
        if len(lists) > 1:
            self.fail("passive", "skill %d: %d lists of state %d" % (sk, len(lists), st))
            return
        x = lists[0]
        lvl = x.own.get(351 << 16, 0)
        par = r.get("passiveitype", "")
        pv = self.t.itypes.index(par) if par else 0
        want = {350 << 16: sk, 351 << 16: lvl}
        for k in range(1, 6):
            stat, calc = r.get("passivestat%d" % k, ""), r.get("passivecalc%d" % k, "")
            if not stat:
                continue
            v = self.calc(calc, r, lvl)
            if v is None:
                self.notes["passive calc not modelled: %s" % calc] += 1
                return
            if v:
                key = self.t.stat_id[stat] << 16 | pv
                want[key] = want.get(key, 0) + v
        self.n["passive_checked"] += 1
        self.passive_levels = getattr(self, "passive_levels", collections.Counter())
        self.passive_levels[(sk, lvl)] += 1
        if x.own != want:
            self.fail("passive", "skill %d level %d: list %r, predicted %r" % (sk, lvl, sorted(x.own.items()),
                                                                               sorted(want.items())))

    def calc(self, text, r, lvl):
        from calc import _dimret
        if len(text) == 4 and text[:2] in ("ln", "dm") and text[2:].isdigit():
            a = int(r.get("Param%s" % text[2]) or 0)
            b = int(r.get("Param%s" % text[3]) or 0)
            return s32(a + (lvl - 1) * b) if text[:2] == "ln" else _dimret(lvl, a, b)
        return None

    def aura_grid(self):
        """Per (who, event): the run frames modulo the period seen (the perdelay grid ((f - 1 + p) / p) p + 1)."""
        out = {}
        for k, frs in self.au.items():
            gaps = collections.Counter(b - a for a, b in zip(frs, frs[1:]))
            res = collections.Counter(f % 50 for f in frs)
            out["%s/%s" % k] = {"runs": len(frs), "gaps": dict(gaps.most_common(5)), "mod50": dict(res.most_common(3))}
        return out

    def report(self, out=None):
        res = {"counts": dict(self.n), "mismatches": dict(self.bad), "examples": dict(self.examples),
               "seeds": {k: {"unchanged": v[0], "moved": v[1]} for k, v in self.seeds.items()},
               "reads_by_stat": {str(k): v for k, v in sorted(self.reads_by_stat.items())},
               "ops_in_predicted_writes": {str(k): v for k, v in sorted(self.opcount.items())},
               "notes": dict(self.notes),
               "set_counts": {"%s n=%d" % k: v for k, v in sorted(getattr(self, "set_counts", {}).items())},
               "req_cases": {repr(k): v for k, v in sorted(getattr(self, "req_cases", {}).items())},
               "passive_levels": {"%d@%d" % k: v for k, v in sorted(getattr(self, "passive_levels", {}).items())},
               "apply_cases": {"%s state %d" % k: v for k, v in sorted(self.apply_cases.items())},
               "apply_sources": {"state %d skill %d source type %r" % k: v for k, v in sorted(
                   self.apply_sources.items(), key=lambda kv: repr(kv[0]))},
               "expire_lateness": {str(k): v for k, v in sorted(self.exp_late.items())},
               "tick_cases": dict(self.tick_cases), "aura_grid": self.aura_grid(),
               "take_tests": {"op %d %s" % (k[0], "taken" if k[1] else "not taken"): v
                              for k, v in sorted(self.takes.items())},
               "recompute_paths": dict(self.paths),
               "rescale_cases": dict(getattr(self, "rescale_cases", {})),
               "aura_durations": {"skill %d len %d" % k: v for k, v in sorted(self.aura_durations.items())},
               "aura_draw_sites": {"%s from %s (%s/%s)" % k: v for k, v in self.au_sites.items()},
               "wells": [[a["p"], a["v"], b["v"]] for a, b in self.wells[:20]]}
        print(json.dumps(res, indent=1, sort_keys=True))
        if out:
            with open(out, "w") as fh:
                json.dump(res, fh, indent=1, sort_keys=True)
        return 0 if not self.bad else 1


TAGS = {"ISC", "TREE0", "TREE", "LNK", "LNX", "ULK", "ULX", "TGL", "TGX", "PRP", "PRX", "CA", "CW", "SCB", "RD",
        "RQ0", "RQ91", "RQS", "RQD", "RQL", "RQF", "RQX", "EQR", "EQX", "UOE", "UOX", "MSK", "TIP", "UOB", "SBA", "SBX",
        "DMG", "PAS", "PAX", "TK0", "TK1", "STA0", "STA1", "EXP0", "EXP1", "AU0", "AU1", "GRP", "GRX", "SHR0", "SHR1",
        "WEL0", "WEL1", "RNGA"}


def manifest(paths):
    for p in paths:
        h = hashlib.sha256()
        n = 0
        with open(p, "rb") as fh:
            for line in fh:
                h.update(line)
                n += 1
        print("%s %d %d %s" % (h.hexdigest(), os.path.getsize(p), n, p))
    return 0


def main(argv):
    if not argv or argv[0] not in ("check", "manifest", "isc"):
        print(__doc__)
        return 2
    excel, verbose, out, paths = DEFAULT_EXCEL, False, None, []
    rest = argv[1:]
    k = 0
    while k < len(rest):
        a = rest[k]
        if a == "--excel":
            excel, k = rest[k + 1], k + 2
        elif a == "--json":
            out, k = rest[k + 1], k + 2
        elif a == "-v":
            verbose, k = True, k + 1
        else:
            paths.append(a)
            k += 1
    if argv[0] == "manifest":
        return manifest(paths)
    T = Tables(excel)
    if argv[0] == "isc":
        tg, deps, opin, b51, b52, b53 = T.isc_graph()
        for i, r in enumerate(T.isc):
            if opin[i] or b51[i]:
                print(i, r["Stat"], "targets", [t for t in tg[i] if t != 0xFFFF], "deps", deps[i], "opIn", opin[i])
        return 0
    C = Checker(T, verbose)
    for p in paths:
        C.run_log(p)
    return C.report(out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

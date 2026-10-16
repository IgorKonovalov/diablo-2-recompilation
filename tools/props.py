#!/usr/bin/env python3
"""Base stats, property roll, ethereal and socket model (plan 0024 Phase 2), checked against tools/gdb/props.gdb logs.

    python3 -I tools/props.py check <log> [<log> ...] [--excel DIR] [-v]
    python3 -I tools/props.py rerun <log> [<log> ...] [--excel DIR]     # plan 0019 logs (tools/gdb/uniques.gdb)

Model of docs/findings/items/0006-properties.md:
  - sub_00557AB0_ItemInitStats (section 1): the base-stat draws on the unit seed (Unit+0x20), in category order
    (gold; quiver types; armour: durability then defense; weapon: quantity when stackable, then durability; misc:
    quantity when stackable), then the picture draw; the stats it writes. Checked at IIS1 (unit seed after, the
    picture, the unit's base stat entries).
  - sub_0065FEC0_ItemApplyProps (sections 2-4): the block walk per mode (0 and 2/5: 3 blocks, 1: 2, 3: 12 unique
    blocks, 4: 9 set blocks then the 10 aprop blocks with their lists), PROP_ApplyBlock's slot walk (func 0 ends it;
    prev = slot 1's return), every drop-path handler (funcs 1-8, 10-17, 19-24, 36), PROP_RollValue (no draw when
    min == max), PROP_WriteStat (ValShift, add or set, 58 -> 326, value 0 writes nothing), the base resets
    (sub_0065CCC0_PropBaseReset) and the stat lists ((state, flags) found or created). Checked per call between APE
    and APX: every SLOT (func, properties row, set, stat, val, prev, block, state, flags, item seed), ROLL and ROLLR
    (min, max, value, item seed), WR (stat, param, value, set, state, flags), SLOTR (return value, item seed), the
    item seed at APX, and the stat lists at APX (the unit's base entries and every attached list) against the APE
    lists with the model's writes applied.
  - sub_00556CA0_ItemRollEthereal and sub_00556B60_ItemRollSockets with ITEMS_SetSockets (section 6): eligibility,
    the one RNG_Range(100) draw each, the < 5 and < 33 tests, ITEMS_MakeEthereal, the count startSeed % cap + 1 with
    the difficulty cap and the clamps; checked at ETH0/ETHR/ETHX and SOK0/SOKM/SOKR/SSET/SOKX, and the final lists at
    LX (when the item's last stat change before LX is one the model makes).
  - Chained after tools/uniques.py: every ItemCreateByQuality call is first checked by uniques.check_block, with its
    ItemApplyProps seed oracle (PROPS -> BRET) replaced by this model's seed. The rare, magic, superior, low and
    normal builders' picks and the automagic pick stay plan 0019 / 0021 seed oracles (their ItemApplyProps calls are
    checked here). The item seed is followed from ICJ through ethereal and sockets to ICX (or to the automagic call).
Value inputs read from the log (architect ruling, plan 0024 Phase 1): the evaluated max durability (EVD) that func 13
and the ethereal roll read; DataTables+0xC6C/+0xC70 (PDT) for the func 19 param; the skills rows (reqlevel, maxlvl)
are read from skills.bin and compared with the SLOT line's values.

apply_seed: the seed-only walk of one affix (mode 0) or QualityItems (mode 1) row, which tools/items_chain.py hands
to tools/affixes.py in place of its ItemApplyProps oracle; items_chain.py also runs affixes.py's pick model on these
logs, so the builders' picks are predicted there.

rerun: the plan 0019 logs have no APE lines; uniques.check_block runs with the PROPS oracle replaced by this model's
seed prediction (the walk and its draws from the tables, ilvl and the base), compared with the BRET seed.

Exit 0 only when every checked item reproduces. Stdlib only. Read-only.
"""
import argparse
import collections
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin  # noqa: E402
import rng  # noqa: E402
import uniques  # noqa: E402

EXCEL = uniques.EXCEL
M32 = 0xFFFFFFFF
WEAP, ARMO, TORS, GOLD = 45, 50, 3, 4
QN = uniques.QN


def recs(excel, table):
    r, _ = excel_bin.read_bin(excel_bin.find_file(excel, table, ".bin"))
    return r


def s16(b, o):
    return struct.unpack_from("<h", b, o)[0]


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def s32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def blocks(r, off, n):
    return [list(struct.unpack_from("<iiii", r, off + 16 * i)) for i in range(n)]


# Plan 0038 batch S2b counterfactual (tools/items_sweep.py cf): True makes every division of the model floor instead
# of truncating toward zero. It must FAIL on logs where a negative operand decides; it is never on by default.
FLOOR_CF = False


def trunc_div(a, b):
    if FLOOR_CF:
        return a // b
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


class Mismatch(Exception):
    pass


def eq(what, model, logged):
    if model != logged:
        raise Mismatch("%s: model %r, log %r" % (what, model, logged))


# ---------------------------------------------------------------- tables

class Tables:
    def __init__(self, excel):
        self.items = []
        for t in ("weapons", "armor", "misc"):
            self.items.extend(recs(excel, t))
        self.itypes = recs(excel, "itemtypes")
        self.props = []
        for r in recs(excel, "properties"):
            self.props.append(dict(set=list(r[2:9]), val=[s16(r, 0xA + 2 * k) for k in range(7)],
                                   func=list(r[0x18:0x1F]), stat=[u16(r, 0x20 + 2 * k) for k in range(7)]))
        isc = recs(excel, "itemstatcost")
        self.valshift = [r[0x18] for r in isc]
        self.nstats = len(isc)
        self.uniq = recs(excel, "uniqueitems")
        self.setit = recs(excel, "setitems")
        self.affix = recs(excel, "magicsuffix") + recs(excel, "magicprefix") + recs(excel, "automagic")
        self.qitems = recs(excel, "qualityitems")
        self.skills = [(s16(r, 0x174), s16(r, 0x12C)) for r in recs(excel, "skills")]
        self.uq = uniques.Tables(excel)

    def base(self, cls):
        r = self.items[cls]
        return dict(code=r[0x80:0x84].decode("latin1").strip(), minac=s32(r, 0xCC), maxac=s32(r, 0xD0),
                    speed=s32(r, 0xD8), minstack=s32(r, 0xE4), maxstack=s32(r, 0xE8), spawnstack=s32(r, 0xEC),
                    mindam=r[0xFE], maxdam=r[0xFF], minmis=r[0x100], maxmis=r[0x101], min2=r[0x102], max2=r[0x103],
                    invw=r[0x10F], invh=r[0x110], block=r[0x111], dur=r[0x112], nodur=r[0x113],
                    type=s16(r, 0x11E), type2=s16(r, 0x120), quest=r[0x12A], stackable=r[0x132], hasinv=r[0x137],
                    gemsockets=r[0x138])

    def is_type(self, cls, t):
        """ITEMS_IsType (0x00629BB0): type or type2 is t or has t among its Equiv ancestors."""
        b = self.base(cls)

        def up(x, seen):
            if x <= 0 or x in seen or x >= len(self.itypes):
                return False
            if x == t:
                return True
            seen.add(x)
            return up(u16(self.itypes[x], 4), seen) or up(u16(self.itypes[x], 6), seen)
        return up(b["type"], set()) or up(b["type2"], set())

    def tfield(self, cls, off, kind="u8"):
        t = self.base(cls)["type"]
        if t < 0 or t >= len(self.itypes):
            return 0
        r = self.itypes[t]
        return r[off] if kind == "u8" else s16(r, off)

    def throwable(self, cls):
        return self.tfield(cls, 0x10)          # 0x0062BA80: the type's Throwable byte

    def max_sockets(self, cls, ilvl):
        """sub_0062BC20_ItemMaxSockets: min(gemsockets, MaxSock1/25/40 of the first type by ilvl)."""
        lv = max(ilvl, 1)
        off = 0x1A if lv <= 25 else 0x1B if lv <= 40 else 0x1C
        return min(self.base(cls)["gemsockets"], self.tfield(cls, off))


class Seed:
    def __init__(self, s):
        if isinstance(s, str):
            a, b = s.split(":")
            s = (int(a, 16), int(b, 16))
        self.lo, self.hi = s

    def range(self, n):
        """RNG_Range / RNG_RangeB: no step when (int)n < 1."""
        n &= M32
        if n == 0 or n & 0x80000000:
            return 0
        self.lo, self.hi = rng.step(self.lo, self.hi)
        return self.lo % n

    def offset(self, b, n):
        return b + self.range(n) if not (n & 0x80000000 or n == 0) else b

    def __str__(self):
        return "%08x:%08x" % (self.lo, self.hi)


# ---------------------------------------------------------------- ItemInitStats

def init_stats(T, cls, useed, rilvl, rqty, has_rec=True):
    """sub_00557AB0_ItemInitStats on a drop (item quality 0). Returns ({(stat, 0): value}, picture or None, kind)."""
    b = T.base(cls)
    s = Seed(useed)
    st = {}

    def put(stat, v):
        if v:
            st[(stat, 0)] = v
        else:
            st.pop((stat, 0), None)

    if b["type"] == GOLD:
        kind = "gold"
        if has_rec:
            n = rilvl + s.range(rilvl * 5)
            if n < 1:
                n = 1
            if rqty > 0:
                n = rqty
        else:
            n = 1
        put(14, max(n, 0))
    elif T.tfield(cls, 0x0E, "s16"):
        kind = "quiver"
        lo, hi = b["minstack"], min(b["maxstack"], 511)
        q = lo + s.range(hi - lo)
        if q < 1:
            q = 1
        if rqty > 0:
            q = rqty
        put(70, q)
    elif T.is_type(cls, ARMO):
        kind = "armor"
        put(20, b["block"])
        put(67, -b["speed"])
        d = b["dur"]
        cur = s.range(d >> 1) + (d >> 1)
        put(72, min(cur, 255))
        put(73, min(d, 255))
        put(31, s.offset(b["minac"], b["maxac"] - b["minac"] + 1))
    elif T.is_type(cls, WEAP):
        kind = "weapon"
        if b["stackable"]:
            lo, hi = b["minstack"], min(b["maxstack"], 511)
            q = lo + s.range(hi - lo)
            if rqty > 0:
                q = rqty
            if q & M32 == 0:
                q = 1
            put(70, q)
        d = b["dur"]
        cur = s.range(d >> 1) + (d >> 1)
        put(72, min(cur, 255))
        put(73, min(d, 255))
        for stat, k in ((22, "maxdam"), (21, "mindam"), (23, "min2"), (24, "max2")):
            if b[k]:
                put(stat, b[k])
        if b["maxmis"]:
            put(159, b["minmis"])
            put(160, b["maxmis"])
        put(68, -b["speed"])
    else:
        kind = "misc"
        if b["stackable"]:
            lo, hi, sp = b["minstack"], min(b["maxstack"], 511), b["spawnstack"]
            top = sp if (sp >= lo and sp != 0) else (lo if lo > hi else hi)
            q = lo + s.range(top - lo)
            if rqty > 0:
                q = rqty
            if q & M32 == 0:
                q = 1
            put(70, q)
    n = T.tfield(cls, 0x23)
    gfx = (s.offset(0, n) & 0xFF) if n else None
    return st, gfx, kind, s


# ---------------------------------------------------------------- the property roll

EVD_CHECKED = collections.Counter()      # logged EVD values compared with Item.eval_maxdur


class Item:
    """The state the handlers read and write: the unit's base entries and its attached lists."""

    def __init__(self, T, cls, q, ilvl, ver, flags, base, subs, seed):
        self.T, self.cls, self.q, self.ilvl, self.ver, self.flags = T, cls, q, ilvl, ver, flags
        self.b = T.base(cls)
        self.base = dict(base)                  # {(stat, param): value}
        self.subs = [[st, fl, dict(e)] for st, fl, e in subs]
        self.seed = Seed(seed)

    @classmethod
    def from_dump(cls_, T, cls, q, ilvl, ver, flags, dump, seed):
        base = {(s, p): v for s, p, v in (dump.get("b") or [])}
        subs = [[st, fl, {(s, p): v for s, p, v in ent}] for st, fl, ent in dump.get("sub", [])]
        return cls_(T, cls, q, ilvl, ver, flags, base, subs, seed)

    def weapon(self):
        return self.T.is_type(self.cls, WEAP)

    def armor(self):
        return self.T.is_type(self.cls, ARMO)

    def set_base(self, stat, v):
        if v:
            self.base[(stat, 0)] = v
        else:
            self.base.pop((stat, 0), None)

    def get_base(self, stat):
        return self.base.get((stat, 0), 0)

    def eval_stat(self, stat):
        v = self.base.get((stat, 0), 0)
        for st, fl, e in self.subs:
            if not fl & 0x2000:
                v += e.get((stat, 0), 0)
        return v

    def eval_maxdur(self):
        """The evaluated stat 73 (sub_00625E00_ItemMaxDurability -> the stat list's cached full value): the list's own
        value plus, for each stat whose op 13 targets 73 (ItemStatCost: only 75, item_maxdurability_percent), MulDiv(the
        item's base stat 73, the evaluated stat 75, 100) (sub_00626200_StatEvaluate, case 13 at 0x00626626-0x00626662;
        MulDiv truncates toward zero). Compared with the logged EVD; the logged value is still what the model uses."""
        b73 = self.get_base(73)
        p75 = self.eval_stat(75)
        add = trunc_div(b73 * p75, 100) if b73 and p75 else 0
        return self.eval_stat(73) + add

    def target(self, state, flags):
        """sub_0065CBF0_PropTargetList: the list of that state (state != 0) or with those flag bits, else a new one."""
        chain2000 = bool(flags & 0x2000)
        want = flags & ~0x2000
        for L in self.subs:
            if state:
                if L[0] == state:
                    return L
            elif bool(L[1] & 0x2000) == chain2000 and L[1] & want:
                return L
        L = [state, flags, {}]
        self.subs.insert(0, L)
        return L

    def has_dur(self, evd=None):
        """sub_00629930_ItemHasDurability: nodurability 0, durability > 0, evaluated max durability != 0,
        evaluated stat 152 <= 0."""
        if self.b["nodur"] or not self.b["dur"]:
            return False
        if (evd if evd is not None else self.eval_stat(73)) == 0:
            return False
        return self.eval_stat(152) <= 0

    def dumps(self):
        return ({k: v for k, v in self.base.items()},
                sorted([(st, fl, tuple(sorted(e.items()))) for st, fl, e in self.subs]))


class Roller:
    """One ItemApplyProps call. ev: the model's event list (compared with the log)."""

    def __init__(self, T, it, mode, evd, pdt):
        self.T, self.it, self.mode, self.evd, self.pdt = T, it, mode, evd, pdt
        self.check_evd = True                   # off in the seed-only rerun, which feeds dummy EVD values
        self.ev = []

    def roll(self, lo, hi):
        self.ev.append(("ROLL", dict(min=lo, max=hi, seed=str(self.it.seed))))
        if lo == hi:
            v = lo
        else:
            a, b = (lo, hi) if hi >= lo else (hi, lo)
            v = a + self.it.seed.range(b - a + 1)
        self.ev.append(("ROLLR", dict(v=v, seed=str(self.it.seed))))
        return v

    def write(self, stat, param, v, sset, state, flags):
        self.ev.append(("WR", dict(stat=stat, param=param, v=v, set=sset, st=state, fl=flags)))
        if v == 0 or stat < 0 or stat >= self.T.nstats:
            return 0
        L = self.it.target(state, flags)[2]
        key = (stat, param & 0xFFFF)
        sv = (v << self.T.valshift[stat]) & M32
        sv = sv - (1 << 32) if sv & 0x80000000 else sv
        if sset:
            L[key] = sv
        else:
            L[key] = L.get(key, 0) + sv
            if L[key] == 0:
                del L[key]
        if stat == 58:
            k2 = (326, 0)
            if sset:
                if not L.get(k2):
                    L[k2] = 1
            else:
                L[k2] = L.get(k2, 0) + 1
                if L[k2] == 0:
                    del L[k2]
        return v

    def reset(self, stat):
        """sub_0065CCC0_PropBaseReset: 16, 31 defense; 17, 22 max damage; 18, 21 min damage."""
        it, b = self.it, self.it.b
        if stat in (16, 31):
            if it.armor() and b["maxac"] != 0:
                cur = it.get_base(31) + 1
                it.set_base(31, cur if cur > b["maxac"] else b["maxac"] + 1)
        elif stat in (17, 22):
            if it.weapon():
                if b["maxdam"]:
                    it.set_base(22, b["maxdam"])
                if b["max2"]:
                    it.set_base(24, b["max2"])
                if self.T.throwable(it.cls) and b["maxmis"]:
                    it.set_base(160, b["maxmis"])
        elif stat in (18, 21):
            if it.weapon():
                if b["mindam"]:
                    it.set_base(21, b["mindam"])
                if b["min2"]:
                    it.set_base(23, b["min2"])
                if self.T.throwable(it.cls) and b["minmis"]:
                    it.set_base(159, b["minmis"])

    def skill_level(self, skill, mx):
        req, maxlvl = self.T.skills[skill]
        ilvl = max(self.it.ilvl, 1)
        if mx > 0:
            return mx
        if mx == 0:
            t = trunc_div(ilvl - req, 4) + 1
            cap = maxlvl if maxlvl >= 1 else 20
            return cap if max(t, 1) >= cap else max(t, 1)
        step = -trunc_div(max(99 - req, 1), mx)
        if step < 1:
            step = 1
        L = trunc_div(ilvl - req, step)
        return L if L > 0 else 1

    def dmg(self, which, v, sset, state, flags):
        """Funcs 5 (which 'min') and 6 ('max'): the three damage stats by base column, each clamped."""
        it, b = self.it, self.it.b
        if which == "min":
            cols = ((21, "mindam", "min2"), (23, "min2", "mindam"), (159, "minmis", None))
        else:
            cols = ((22, "maxdam", "max2"), (24, "max2", "maxdam"), (160, "maxmis", None))
        w = it.weapon()
        for stat, own, other in cols:
            if other is not None:
                if w and b[own] == 0 and b[other] != 0:
                    continue
            elif w and not self.T.throwable(it.cls):
                continue
            bb = b[own]
            x = v
            if bb > 0 and bb + v <= 0:
                x = 1 - bb if which == "min" else -bb
            if x:
                self.write(stat, 0, x, sset, state, flags)

    def handler(self, func, blk, sset, stat, val, prev, state, flags):
        code, par, mn, mx = blk
        it = self.it
        if func in (1, 2, 3, 4):
            if func in (2, 4) or self.mode == 1:
                self.reset(stat)
            v = prev if (func in (3, 4) and prev) else self.roll(mn, mx)
            return self.write(stat, 0, v, sset, state, flags)
        if func in (5, 6):
            v = prev if prev else self.roll(mn, mx)
            self.dmg("min" if func == 5 else "max", v, sset, state, flags)
            return v
        if func == 7:
            v = prev if prev else self.roll(mn, mx)
            b = it.b
            if it.weapon():
                for s_, k in ((21, "mindam"), (23, "min2")):
                    if b[k]:
                        it.set_base(s_, b[k])
                if self.T.throwable(it.cls) and b["minmis"]:
                    it.set_base(159, b["minmis"])
                for s_, k in ((22, "maxdam"), (24, "max2")):
                    if b[k]:
                        it.set_base(s_, b[k])
                if self.T.throwable(it.cls) and b["maxmis"]:
                    it.set_base(160, b["maxmis"])
                m = max(b["max2"], b["maxdam"])
                if trunc_div(m * v, 100) <= 0:
                    self.dmg("max", 1, sset, state, flags)
                    return 1
            self.write(18, 0, v, sset, state, flags)
            self.write(17, 0, v, sset, state, flags)
            return v
        if func == 8:
            v = prev if prev else self.roll(mn, mx)
            return self.write(stat, 0, v, sset, state, flags)
        if func == 10:
            v = prev if prev else self.roll(mn, mx)
            if v == 0:
                return 0
            return self.write(stat, par % 3 + trunc_div(par, 3) * 8 if par >= 0 else
                              -((-par) % 3) + trunc_div(par, 3) * 8, v, sset, state, flags)
        if func == 11:
            if par < 0 or par >= len(self.T.skills):
                return 0
            chance = mn if mn > 0 else 5
            L = self.skill_level(par, mx)
            return self.write(stat, (par << 6) + (L & 0x3F), chance, sset, state, flags)
        if func == 12:
            v = self.roll(mn, mx)
            return self.write(stat, v, par, sset, state, flags)
        if func == 13:
            if self.mode == 1:
                self.reset(stat)
            v = self.roll(mn, mx)
            r = self.write(stat, 0, v, sset, state, flags)
            if r:
                e = self.evd.pop(0) if self.evd else None
                if e is None:
                    raise Mismatch("func 13 wrote but no EVD value is logged")
                if self.check_evd:
                    if e != it.eval_maxdur():
                        raise Mismatch("func 13 EVD: model %d, logged %d" % (it.eval_maxdur(), e))
                    EVD_CHECKED["func 13"] += 1
                self.ev.append(("EVD", dict(at="f13", v=e)))
                if e > 0:
                    it.set_base(72, e)
            return r
        if func == 14:
            b = it.b
            sz = b["invw"] * b["invh"]
            if sz > 6:
                cap = 6
            elif sz > 0:
                cap = sz
            else:
                return 0
            cap = min(cap, self.T.max_sockets(it.cls, it.ilvl))
            n = prev if prev > 0 else self.roll(mn, mx)
            if n <= 0:
                n = par
            if max(n, 1) >= cap:
                n = cap
                if n <= 0:
                    return 0
            elif n <= 1:
                n = 1
            it.flags |= 0x800
            it.set_base(194, n)
            return n
        if func == 15:
            v = mn
            if stat == 21:
                self.handler(5, blk, sset, 21, 0, v, state, flags)
            else:
                self.write(stat, 0, v, sset, state, flags)
            return v
        if func == 16:
            v = mx
            if stat == 22:
                self.handler(6, blk, sset, 22, 0, v, state, flags)
            else:
                self.write(stat, 0, v, sset, state, flags)
            return v
        if func == 17:
            v = par
            if v == 0:
                v = self.roll(mn, mx)
                if v == 0:
                    return 0
            if stat == 22:
                self.handler(6, blk, sset, 22, 0, v, state, flags)
            else:
                self.write(stat, 0, v, sset, state, flags)
            return v
        if func == 19:
            if par < 0 or par >= len(self.T.skills):
                return 0
            L = self.skill_level(par, mx)
            c = mn
            if c == 0:
                c = 5
            else:
                if c < 0:
                    c = -c + trunc_div(-c * L, 8)
                c = 1 if c <= 1 else 255 if c >= 255 else c
            r = it.seed.range(c - trunc_div(c, 8))
            value = ((r + trunc_div(c, 8) + 1) & 0xFF) + (c << 8)
            sh, mask = self.pdt
            p = (par << sh) & M32
            param = (p & 0xFFFF0000) | ((p + (L & mask & 0xFFFF)) & 0xFFFF)
            L_ = it.target(state, flags)[2]
            L_[(stat, param & 0xFFFF)] = value
            self.ev.append(("F19", dict(r=r, c=c, L=L)))
            return c
        if func == 20:
            L_ = it.target(state, flags)[2]
            L_[(152, 0)] = L_.get((152, 0), 0) + 1
            return 1
        if func == 21:
            v = self.roll(mn, mx)
            return self.write(stat, val, v, sset, state, flags)
        if func == 22:
            v = self.roll(mn, mx)
            return self.write(stat, par & 0xFFFF, v, sset, state, flags)
        if func == 23:
            if not it.flags & 0x400000 and it.has_dur():
                make_ethereal(it)
                return 1
            return 0
        if func == 24:
            v = prev if prev else self.roll(mn, mx)
            return self.write(stat, par, v, sset, state, flags)
        if func == 36:
            v = self.roll(mn, mx)
            return self.write(stat, v, val, sset, state, flags)
        raise Mismatch("func %d not modelled" % func)

    def apply_block(self, blk, state, flags):
        """PROP_ApplyBlock: the slots of the block's properties row, prev = slot 1's return."""
        code = blk[0]
        if code < 0 or code >= len(self.T.props):
            return
        p = self.T.props[code]
        prev = 0
        for k in range(7):
            f = p["func"][k]
            if f >= 37 or f in (0,) or 25 <= f <= 35:
                return
            stat = p["stat"][k]
            self.ev.append(("SLOT", dict(k=k, prop=code, func=f, set=p["set"][k], stat=stat, val=p["val"][k],
                                         prev=prev, blk=list(blk), st=state, fl=flags, seed=str(self.it.seed))))
            r = self.handler(f, blk, p["set"][k], stat if stat != 0xFFFF else -1, p["val"][k], prev, state, flags)
            self.ev.append(("SLOTR", dict(r=r, seed=str(self.it.seed))))
            if k == 0:
                prev = r

    def run(self, rowblocks):
        """rowblocks: [(block, state, flags, skip_negative)] in walk order."""
        for blk, state, flags, skip in rowblocks:
            if blk[0] < 0:
                if skip:
                    continue
                return
            self.apply_block(blk, state, flags)


def make_ethereal(it):
    """ITEMS_MakeEthereal: flag 0x400000; a weapon's base 21-24, 159, 160 (else base 31) become (3x)/2."""
    it.flags |= 0x400000
    for s_ in ((21, 22, 23, 24, 159, 160) if it.weapon() else (31,)):
        it.set_base(s_, trunc_div(3 * it.get_base(s_), 2))


def row_blocks(T, mode, fi, ver, logged_blk=None, aid=None):
    """The (block, state, flags, skip) walk of ItemApplyProps for a mode; the row from the tables."""
    if mode == 3:
        if fi < 0 or fi >= len(T.uniq):
            return [], "unique -"
        return [(b, 0, 0x40, True) for b in blocks(T.uniq[fi], 0x8C, 12)], "unique %d" % fi
    if mode == 4:
        if fi < 0 or fi >= len(T.setit):
            return [], "set -"
        r = T.setit[fi]
        if ver == 0:
            return [(b, 0, 0x40, True) for b in blocks(r, 0x88, 2)], "set %d (v0)" % fi
        out = [(b, 0, 0x40, True) for b in blocks(r, 0x88, 9)]
        addf = r[0x87]
        for k, b in enumerate(blocks(r, 0x118, 10)):
            j = (k >> 1) + 2
            out.append((b, (0xA3 + j) if addf else 0, 0x2040 if addf else 0x40, True))
        return out, "set %d" % fi
    if mode == 0:
        if aid is None or not 1 <= aid <= len(T.affix):
            raise Mismatch("affix id %r out of range" % aid)
        bl = blocks(T.affix[aid - 1], 0x24, 3)
        if logged_blk is not None:
            eq("affix %d blocks (table vs memory)" % aid, bl, logged_blk)
        return [(b, 0, 0x40, False) for b in bl], "affix %d" % aid
    if mode == 1:
        rows = [i for i, r in enumerate(T.qitems) if blocks(r, 0x0C, 2) == logged_blk]
        if not rows:
            raise Mismatch("qualityitems blocks %r match no row" % logged_blk)
        return [(b, 0, 0x40, False) for b in logged_blk], "qualityitems %s" % rows
    raise Mismatch("mode %d not on the drop path" % mode)


SETSTATES = {0xA5, 0xA6, 0xA7, 0xA8, 0xA9}


# ---------------------------------------------------------------- the seed-only model (rerun of plan 0019 logs)

def props_seed(T, mode, fi, seed, ic):
    """Item seed after ItemApplyProps (modes 3 and 4) for a fresh item: the walk with an empty stat state."""
    it = Item(T, ic["cls"], 7 if mode == 3 else 5, ic["ilvl"], ic["ver"], 0, {}, [], uniques.fmt(seed))
    bl, _ = row_blocks(T, mode, fi, ic["ver"])
    R = Roller(T, it, mode, [1] * 64, (0, 0))
    R.check_evd = False
    R.run(bl)
    return it.seed.lo, it.seed.hi


def apply_seed(T, mode, rec, seed, cls, ilvl, ver, q):
    """Item seed (lo, hi) after one ItemApplyProps call of the affix and quality builders, from the tables: mode 0
    with rec = the MagicPrefix/MagicSuffix/automagic id (1-based, the affix block), mode 1 with rec = the QualityItems
    row. The walk runs on an empty stat state (as props_seed): on the drop path no handler's draws depend on it.
    Used by tools/items_chain.py in place of tools/affixes.py's APR0/APR1 seed oracle."""
    it = Item(T, cls, q, ilvl, ver, 0, {}, [], uniques.fmt(seed))
    if mode == 0:
        bl, _ = row_blocks(T, 0, 0, ver, aid=rec)
    elif mode == 1:
        if rec is None or not 0 <= rec < len(T.qitems):
            raise Mismatch("qualityitems row %r out of range" % rec)
        bl = [(b, 0, 0x40, False) for b in blocks(T.qitems[rec], 0x0C, 2)]
    else:
        raise Mismatch("mode %d is not an affix or quality builder call" % mode)
    R = Roller(T, it, mode, [1] * 64, (0, 0))
    R.check_evd = False
    R.run(bl)
    return it.seed.lo, it.seed.hi


# ---------------------------------------------------------------- log reading

UTAGS = set(uniques.TAGS)
PTAGS = {"APE", "SLOT", "SLOTR", "ROLL", "ROLLR", "WR", "EVD", "APX", "ETH0", "ETHR", "ETHX", "SOK0", "SOKM", "SOKR",
         "SSET", "SOKX", "LX"}


def read_log(path):
    """Yield ("GAME", None), ("PDT", d), ("IIS", (iis0, iis1)) and ("IC", (events, cpre)) in log order."""
    open_ = {}
    iis0 = {}
    iis1 = {}
    cpre = None
    last = None
    for line in open(path, errors="replace"):
        line = line.rstrip("\n")
        tag, _, rest = line.partition(" ")
        if tag == "GAME":
            yield "GAME", None
            continue
        if tag == "CPRE":
            cpre = dict(x.split("=", 1) for x in rest.split() if "=" in x)
            continue
        if tag == "CPOST":
            cpre = None
            continue
        if not rest.startswith("{") or tag not in UTAGS | PTAGS | {"IIS0", "IIS1", "PDT"}:
            continue
        try:
            d = json.loads(rest)
        except ValueError:
            continue
        th = d.get("th", 0)
        if tag == "PDT":
            yield "PDT", d
            continue
        if tag == "IIS0":
            iis0[th] = d
            continue
        if tag == "IIS1":
            if th in iis0:
                yield "IIS", (iis0.pop(th), d)
                iis1[d["it"]] = d
            continue
        if tag == "IC0":
            open_[th] = [[("IC0", d)], cpre, False, iis1.pop(d.get("it"), None)]
            last = th
            continue
        if tag in UTAGS:          # the plan 0019 lines carry no thread except IC0
            th = last
        if th not in open_:
            continue
        blk = open_[th]
        blk[0].append((tag, d))
        if tag == "ICX":
            blk[2] = True
            if not any(t == "LX" for t, _ in blk[0]) and not has_lx(path):
                yield "IC", (blk[0], blk[1], blk[3])
                del open_[th]
        elif tag == "LX":
            yield "IC", (blk[0], blk[1], blk[3])
            del open_[th]
    for th, blk in open_.items():
        if blk[2]:
            yield "IC", (blk[0], blk[1], blk[3])


_LX = {}


def has_lx(path):
    if path not in _LX:
        with open(path, errors="replace") as f:
            _LX[path] = any(ln.startswith("LX ") for ln in f)
    return _LX[path]


# ---------------------------------------------------------------- checks

def check_iis(T, a, b, stats):
    cls = a["cls"]
    st, gfx, kind, s = init_stats(T, cls, a["useed"], a["rilvl"] or 0, a["rqty"] or 0, a["rec"] != 0)
    logged = {(x[0], x[1]): x[2] for x in (b["b"] or [])}
    eq("IIS unit seed after the base stats", str(s), b["useed"])
    eq("IIS base stats", sorted(st.items()), sorted(logged.items()))
    if gfx is not None:
        eq("IIS picture", gfx, b["gfx"])
    t = T.base(cls)["type"]
    if t != 11:
        eq("IIS item seed unchanged (no type-11 setup)", a["iseed"], b["iseed"])
    return kind, st


def lists_of(d):
    base = {(s, p): v for s, p, v in (d.get("b") or [])}
    subs = sorted((st, fl, tuple(sorted(((s, p), v) for s, p, v in ent))) for st, fl, ent in d.get("sub", []))
    return base, subs


def norm_subs(it):
    return sorted((st, fl, tuple(sorted(e.items()))) for st, fl, e in it.subs)


class Seg:
    """The events of one ItemApplyProps call in the log."""

    def __init__(self, ape):
        self.ape, self.ev, self.apx = ape, [], None


def compare_events(model, logged, where):
    m = [(t, d) for t, d in model if t != "F19"]
    lg = [(t, d) for t, d in logged]
    for i, (a, b) in enumerate(zip(m, lg)):
        ta, da = a
        tb, db = b
        if ta != tb:
            raise Mismatch("%s event %d: model %s %s, log %s %s" % (where, i, ta, da, tb, db))
        for k, v in da.items():
            if db.get(k) != v:
                if tb == "SLOT" and k == "stat" and v == -1 and db.get(k) == 0xFFFF:
                    continue
                raise Mismatch("%s event %d %s.%s: model %r, log %r (model %s, log %s)" % (where, i, ta, k, v,
                                                                                             db.get(k), da, db))
    if len(m) != len(lg):
        raise Mismatch("%s: model has %d events, log %d (next model %s, next log %s)" % (
            where, len(m), len(lg), m[len(lg)] if len(m) > len(lg) else None, lg[len(m)] if len(lg) > len(m) else None))


def staff_mods_oracle(T, cls, st, dump, S, res):
    """ITEMS_RollStaffMods (items/0005 boundary, a seed oracle) runs inside the normal, superior, magic and rare
    builders after their last ItemApplyProps call, on a type whose ItemTypes StaffMods (+0x1F) is not 7, and adds
    item_singleskill (107) entries to the main list. Those entries are taken from the logged list (the oracle's
    output); every other entry must equal the model's. Returns the logged lists for comparison."""
    lb, ls = lists_of(dump)
    if T.tfield(cls, 0x1F) == 7:
        return ls
    model = {(stf, fl): dict(e) for stf, fl, e in norm_subs(st)}
    out = []
    added = 0
    for stf, fl, ent in ls:
        m = model.get((stf, fl), {})
        keep = []
        for k, v in ent:
            if k[0] == 107 and stf == 0 and m.get(k) != v:
                if k in m:
                    raise Mismatch("staff mods changed an existing 107 entry %r: model %r, log %r" % (k, m[k], v))
                added += 1
                continue
            keep.append((k, v))
        if keep or (stf, fl) in model:
            out.append((stf, fl, tuple(keep)))
    if added:
        S["staff-mod 107 entries (oracle)"] += added
        res["staffmods"] = added
    return sorted(out)


AUTOMAGIC_RET = 0x00557A11      # return address of the automagic ItemApplyProps call in ItemCreateByQuality


def check_ic(T, ev, made, ustats, cpre, pdt, S, verbose=False, rerun=False, iis1=None):
    """One ItemCreateByQuality call: uniques.check_block (seed oracle replaced), then every ItemApplyProps call,
    ethereal, sockets and the final lists."""
    u_ev = [(t, d) for t, d in ev if t in UTAGS]
    uniques.PROPS_MODEL = lambda mode, fi, seed, ic: props_seed(T, mode, fi, seed, ic)
    res = uniques.check_block(T.uq, u_ev, made, ustats, cpre)
    if res.get("props_model"):
        S["props seed model (PROPS -> BRET)"] += 1
    if "skip" in res or rerun:
        return res
    ic = ev[0][1]
    cls = ic["cls"]
    # split the ItemApplyProps calls
    segs, cur = [], None
    others = []
    for t, d in ev:
        if t == "APE":
            cur = Seg(d)
            segs.append(cur)
        elif t == "APX":
            if cur is None:
                raise Mismatch("APX without APE")
            cur.apx = d
            cur = None
        elif cur is not None and t in ("SLOT", "SLOTR", "ROLL", "ROLLR", "WR", "EVD"):
            cur.ev.append((t, d))
        elif t in PTAGS or t in UTAGS:
            others.append((t, d))
    res["segs"] = []
    for sg in segs:
        a = sg.ape
        if sg.apx is None:
            raise Mismatch("APE without APX")
        if not a["same"] or a["a2"]:
            raise Mismatch("ItemApplyProps on another unit (a2 %s)" % a["a2"])
        it = Item.from_dump(T, cls, a["q"], a["ilvl"], a["ver"], a["fl"], a, a["seed"])
        bl, rowname = row_blocks(T, a["mode"], a["fi"], a["ver"], a.get("blk"), a.get("aid"))
        evd = [d["v"] for t, d in sg.ev if t == "EVD"]
        R = Roller(T, it, a["mode"], list(evd), pdt)
        R.run(bl)
        compare_events(R.ev, sg.ev, "ItemApplyProps mode %d %s" % (a["mode"], rowname))
        eq("item seed at APX (%s)" % rowname, str(it.seed), sg.apx["seed"])
        mb, ms = it.base, norm_subs(it)
        lb, ls = lists_of(sg.apx)
        eq("base entries at APX (%s)" % rowname, sorted(mb.items()), sorted(lb.items()))
        eq("attached lists at APX (%s)" % rowname, ms, ls)
        funcs = [d["func"] for t, d in sg.ev if t == "SLOT"]
        res["segs"].append(dict(mode=a["mode"], row=rowname, funcs=funcs, ev=sg.ev, model=R.ev, ret=a["ret"],
                                state=it, ape=a, apx=sg.apx))
        S["slots"] += len(funcs)
    # ethereal, sockets, the item seed after the join
    get = collections.defaultdict(list)
    for t, d in others:
        get[t].append(d)
    icj = get["ICJ"][-1]
    icx = get["ICX"][-1]
    q = icj["q"]
    ver = ic["ver"]
    seed = Seed(icj["seed"])
    b = T.base(cls)
    pre = [r_ for r_ in res["segs"] if r_["ret"] != AUTOMAGIC_RET]
    auto = [r_ for r_ in res["segs"] if r_["ret"] == AUTOMAGIC_RET]
    # the item state at the join: the last ItemApplyProps call of the builder, else the ItemInitStats dump when no
    # builder step between them changes stats (normal, superior without a block, or no fallback durability step)
    if pre:
        st, tracked = pre[-1]["state"], True
    else:
        base0 = {(x[0], x[1]): x[2] for x in ((iis1 or {}).get("b") or [])}
        st = Item(T, cls, q, ic["ilvl"], ver, ic["fl"], base0, [], str(seed))
        tracked = iis1 is not None and q in (2, 3) and not res["steps"] and "dur" not in res
    eth_called = 1 <= q <= 9 and ver >= 100
    eq("ItemRollEthereal called (quality 1..9, version >= 100)", eth_called, bool(get["ETH0"]))
    res["eth"] = None
    evd_eth = [d["v"] for d in get["EVD"] if d["at"] == "eth"]
    if eth_called:
        e0 = get["ETH0"][0]
        eq("item seed at ItemRollEthereal", str(seed), e0["seed"])
        elig = (not e0["rfl"] & 2 and (T.is_type(cls, WEAP) or T.is_type(cls, ARMO)) and st.has_dur(1)
                and q not in (1, 5) and not b["quest"])
        eq("ethereal draw made", elig, bool(get["ETHR"]))
        if elig:
            r = seed.range(100)
            eq("ethereal r", r, get["ETHR"][0]["r"])
            eq("item seed after the ethereal draw", str(seed), get["ETHR"][0]["seed"])
            eth = bool(e0["rfl"] & 4 or e0["r44"] & 0x400000 or r < 5)
            res["eth"] = (r, eth)
            S["eth_yes" if eth else "eth_no"] += 1
            if eth:
                make_ethereal(st)
                if st.has_dur(1):
                    st.set_base(73, trunc_div(st.get_base(73), 2) + 1)
                    eq("EVD logged by the ethereal durability", 1, len(evd_eth))
                    eq("EVD after the ethereal halving (model)", st.eval_maxdur(), evd_eth[0])
                    S["EVD model checked (ethereal)"] += 1
                    if st.eval_stat(75):
                        S["EVD model checked (ethereal with dur%)"] += 1
                    st.set_base(72, evd_eth[0])
                    res["eth_dur"] = (st.get_base(73), evd_eth[0])
        eq("ethereal flag at ETHX", bool(res["eth"] and res["eth"][1]) or bool(ic["fl"] & 0x400000) or
           bool(st.flags & 0x400000), bool(get["ETHX"][0]["fl"] & 0x400000))
        eq("item seed after ItemRollEthereal", str(seed), get["ETHX"][0]["seed"])
    sok_called = 1 <= q <= 3
    eq("ItemRollSockets called (quality 1..3)", sok_called, bool(get["SOK0"]))
    res["sock"] = None
    if sok_called:
        s0 = get["SOK0"][0]
        eq("item seed at ItemRollSockets", str(seed), s0["seed"])
        ms = T.max_sockets(cls, ic["ilvl"])
        go = q >= 2 and b["hasinv"] and not b["stackable"] and ms > 0
        eq("ItemMaxSockets reached", go, bool(get["SOKM"]))
        if go:
            eq("ItemMaxSockets", ms, get["SOKM"][0]["ms"])
            cap = min(ms, (3, 4, 6)[ic["diff"]])
            draw = ver >= 100 or not T.is_type(cls, TORS)
            eq("socket draw made", draw, bool(get["SOKR"]))
            if draw:
                r = seed.range(100)
                eq("socket r", r, get["SOKR"][0]["r"])
                eq("item seed after the socket draw", str(seed), get["SOKR"][0]["seed"])
                rr = 0 if s0["rfl"] & 0x10 else r
                sock = not s0["rfl"] & 8 and bool(s0["r44"] & 0x800 or rr < 33)
                eq("ITEMS_SetSockets called", sock, bool(get["SSET"]))
                if sock:
                    n = ic["start"] % cap + 1
                    eq("socket count requested (startSeed % cap + 1)", n, get["SSET"][0]["n"])
                    sz = b["invw"] * b["invh"]
                    c2 = min(6 if sz > 6 else sz, ms)
                    final = c2 if max(n, 1) >= c2 else max(n, 1)
                    res["sock"] = (r, n, final, cap, ms, sz)
                    S["sock_yes"] += 1
                    if final > 0:
                        st.flags |= 0x800
                        st.set_base(194, final)
                else:
                    res["sock"] = (r, 0, 0, cap, ms, 0)
                    S["sock_no"] += 1
        eq("item seed after ItemRollSockets", str(seed), get["SOKX"][0]["seed"])
    if auto:
        # the automagic pick draws (an affix-pick oracle) come between; its ItemApplyProps call was checked above
        a0 = auto[0]["ape"]
        if tracked:
            lb, ls = lists_of(a0)
            eq("base entries at the automagic APE (state after ethereal and sockets)", sorted(st.base.items()),
               sorted(lb.items()))
            eq("attached lists at the automagic APE", norm_subs(st), staff_mods_oracle(T, cls, st, a0, S, res))
            S["state checked at the automagic call"] += 1
        st, tracked = auto[-1]["state"], True
        eq("item seed at ICX (after the automagic ItemApplyProps)", auto[-1]["apx"]["seed"], icx["seed"])
    else:
        eq("item seed at ICX (after ethereal and sockets)", str(seed), icx["seed"])
    res["lx"] = get["LX"][0] if get["LX"] else None
    if res["lx"] and tracked:
        lb, ls = lists_of(res["lx"])
        eq("base entries at LX", sorted(st.base.items()), sorted(lb.items()))
        eq("attached lists at LX", norm_subs(st), ls if auto else staff_mods_oracle(T, cls, st, res["lx"], S, res))
        S["lx_checked"] += 1
    res["state"] = st if tracked else None
    return res


def cmd_check(ns, rerun=False):
    T = Tables(ns.excel)
    ok = bad = 0
    S = collections.Counter()
    ustats = collections.Counter()
    table = collections.Counter()
    funcs = collections.Counter()
    iis_n = collections.Counter()
    notes = collections.defaultdict(list)
    for path in ns.logs:
        made = set()
        game = 0
        pdt = None
        for kind, x in read_log(path):
            if kind == "GAME":
                made = set()
                game += 1
                continue
            if kind == "PDT":
                pdt = (x["c6c"], x["c70"])
                continue
            if kind == "IIS":
                try:
                    k, st = check_iis(T, x[0], x[1], S)
                    S["iis_ok"] += 1
                    iis_n[(k, "exp" if x[0]["ver"] >= 100 else "classic")] += 1
                except (Mismatch, KeyError, IndexError) as e:
                    S["iis_bad"] += 1
                    bad += 1
                    print("FAIL %s game %d IIS cls %s: %s" % (os.path.basename(path), game, x[0]["cls"], e))
                continue
            blk, cpre, iis1 = x
            try:
                r = check_ic(T, blk, made, ustats, cpre, pdt or (0, 0), S, ns.verbose, rerun, iis1)
            except (Mismatch, KeyError, IndexError, TypeError) as e:
                bad += 1
                print("FAIL %s game %d IC0 %s: %s" % (os.path.basename(path), game, json.dumps(blk[0][1])[:200], e))
                continue
            ok += 1
            if "skip" in r:
                continue
            mode = "exp" if r["ver"] >= 100 else "classic"
            dn = ("normal", "nightmare", "hell")[r["diff"]] if r["diff"] is not None else "?"
            table[(QN.get(r.get("final", r["q"]), r["q"]), mode, dn)] += 1
            if r.get("props_model"):
                table[("+" + QN[r["q"]] + " row (props seed)", mode, dn)] += 1
            for sg in r.get("segs", []):
                S["segs mode %d" % sg["mode"]] += 1
                for t, d in sg["ev"]:
                    if t == "SLOT":
                        funcs[d["func"]] += 1
                notes_case(T, r, sg, notes)
            if r.get("sock"):
                notes["sock"].append("%s %s %s q%d ilvl %d: r %d, n %d -> %d (cap %d, maxsock %d)" % (
                    mode, dn, T.base(r["cls"])["code"], r.get("final", 0), r["ilvl"], *r["sock"][:5]))
            if r.get("eth"):
                notes["eth"].append("%s %s %s q%d: r %d -> %s" % (mode, dn, T.base(r["cls"])["code"],
                                                                 r.get("final", 0), *r["eth"]))
    print("%d creations reproduced, %d failed (base-stat blocks: %d ok, %d failed)" % (ok, bad - S["iis_bad"],
                                                                                      S["iis_ok"], S["iis_bad"]))
    print("base stats (ItemInitStats) by category and mode:")
    for k, v in sorted(iis_n.items()):
        print("  %-7s %-8s %d" % (k[0], k[1], v))
    print("items by final quality, mode, difficulty:")
    for k, v in sorted(table.items()):
        print("  %-9s %-8s %-10s %d" % (k[0], k[1], k[2], v))
    print("ItemApplyProps calls: %s" % ", ".join("%s %d" % (k, v) for k, v in sorted(S.items()) if k.startswith("segs")))
    print("slots per func: %s" % ", ".join("%d:%d" % kv for kv in sorted(funcs.items())))
    print("unique/set ItemApplyProps calls checked on the seed (PROPS -> BRET): %d" % S["props seed model (PROPS -> BRET)"])
    print("ethereal draws: %d ethereal, %d not; socket draws: %d socketed, %d not; final lists checked at LX: %d" % (
        S["eth_yes"], S["eth_no"], S["sock_yes"], S["sock_no"], S["lx_checked"]))
    print("evaluated max durability (EVD) model vs log: func 13 %d, ethereal %d (of them with dur%% %d)" % (
        EVD_CHECKED["func 13"], S["EVD model checked (ethereal)"], S["EVD model checked (ethereal with dur%)"]))
    for k in sorted(notes):
        print("-- %s (%d)" % (k, len(notes[k])))
        for n in notes[k][: (None if ns.verbose else 25)]:
            print("   " + n)
    return 0 if bad == 0 else 1


def notes_case(T, r, sg, notes):
    """The Phase 1b and Phase 1 required cases, as they occur."""
    q = r.get("final", r["q"])
    code = T.base(r["cls"])["code"]
    slots = [d for t, d in sg["ev"] if t == "SLOT"]
    wrs = [d for t, d in sg["ev"] if t == "WR"]
    if sg["mode"] == 1:
        for d in slots:
            if d["func"] == 1 and d["stat"] == 19:
                notes["func1 superior att (19)"].append("%s %s -> %s" % (code, d["blk"][2:], [w["v"] for w in wrs
                                                                                       if w["stat"] == 19]))
            if d["func"] == 13:
                notes["func13 superior dur% (75)"].append("%s %s -> %s" % (code, d["blk"][2:], [w["v"] for w in wrs
                                                                                         if w["stat"] == 75]))
            if d["func"] == 2:
                notes["func2 superior ac% (16)"].append("%s %s -> %s" % (code, d["blk"][2:], [w["v"] for w in wrs
                                                                                        if w["stat"] == 16]))
            if d["func"] == 7:
                notes["func7 superior dmg%"].append("%s %s -> %s" % (code, d["blk"][2:], [(w["stat"], w["v"])
                                                                                        for w in wrs]))
    else:
        for d in slots:
            if d["func"] == 2:
                notes["func2 ac%% mode %d" % sg["mode"]].append("%s %s %s -> %s" % (
                    code, sg["row"], d["blk"][2:], [w["v"] for w in wrs if w["stat"] == 16]))
            if d["func"] == 19:
                notes["func19 charged"].append("%s %s blk %s req %s maxlvl %s" % (code, sg["row"], d["blk"],
                                                                                 d.get("req"), d.get("maxlvl")))
            if d["func"] == 6 and d["blk"][2] < 0:
                notes["func6 negative dmg-max"].append("%s %s %s" % (code, sg["row"], d["blk"]))
            if d["func"] == 14:
                notes["func14 sock"].append("%s %s %s" % (code, sg["row"], d["blk"]))
            if d["func"] in (11, 12, 23, 36, 20, 24):
                notes["func%d" % d["func"]].append("%s %s %s" % (code, sg["row"], d["blk"]))
    if sg["mode"] == 4:
        for d in slots:
            if d["st"] in SETSTATES:
                notes["set aprop lists (state 165..169)"].append("%s %s state %d" % (code, sg["row"], d["st"]))
                break
        fi = int(sg["row"].split()[1])
        if T.setit[fi][0x87] == 0 and any(b[0] >= 0 for b in blocks(T.setit[fi], 0x118, 10)):
            notes["set aprop on the main list (add func 0)"].append("%s %s" % (code, sg["row"]))


def cmd_saved(ns):
    """Compare the saved items of a .d2s written in the logged session with the stat lists logged at LX. A saved
    item's `seed` is Unit+0x28 (save/0001 section 6), the value the unit seed was initialised from, which is the low
    word of the unit seed at ItemInitStats entry (IIS0)."""
    import d2s
    T = Tables(ns.excel)
    isc = d2s.load_isc(ns.excel)
    kinds = d2s.load_kinds(ns.excel)
    final = {}
    for path in ns.logs:
        useed = {}                 # item unit -> the low word its unit seed was initialised from (Unit+0x28)
        for kind, x in read_log(path):
            if kind == "IIS":
                useed[x[0]["it"]] = int(x[0]["useed"].split(":")[0], 16)
            elif kind == "IC":
                blk = x[0]
                lx = [d for t, d in blk if t == "LX"]
                it = blk[0][1].get("it")
                if lx and it in useed:
                    final[useed.pop(it)] = (blk[0][1], lx[0])
    data = open(ns.save, "rb").read()
    parsed = d2s.parse(data, isc, kinds)
    items = [it for it in d2s.all_items(parsed) if not it.get("simple") and not it.get("ear")]
    ok = bad = 0
    for it in items:
        if it["seed"] not in final:
            continue
        ic, lx = final[it["seed"]]
        try:
            check_saved(T, isc, it, ic, lx)
            ok += 1
            print("ok   %s q%d seed %08x: %d main stats%s" % (it["code"].strip(), it["quality"], it["seed"],
                                                           len(it["props"]), ", set lists %d" % len(
                                                               it.get("set_props", [])) if it["quality"] == 5 else ""))
        except Mismatch as e:
            bad += 1
            print("FAIL %s seed %08x: %s" % (it["code"].strip(), it["seed"], e))
    print("%d saved items matched to logged creations: %d reproduced, %d failed (%d extended items in the save)" % (
        ok + bad, ok, bad, len(items)))
    return 0 if bad == 0 and ok > 0 else 1


def saved_list(T, isc, entries):
    """What D2S writes for one stat list: (stat, param) -> value >> ValShift, for stats with Save Bits."""
    out = {}
    for (stat, param), v in entries.items():
        e = isc.get(stat)
        if not e or not e["save_bits"]:
            continue
        x = v >> T.valshift[stat]
        if x:
            out[(stat, param if e["param_bits"] else None)] = x
    return out


def file_list(props):
    out = {}
    for sid, param, vals in props:
        for k, v in enumerate(vals):
            if v:
                out[(sid + k, param if k == 0 else None)] = v
    return out


def check_saved(T, isc, it, ic, lx):
    base, subs = lists_of(lx)
    eq("quality", it["quality"], lx["q"])
    eq("ethereal flag", it["ethereal"], 1 if lx["fl"] & 0x400000 else 0)
    eq("socketed flag", it["socketed"], 1 if lx["fl"] & 0x800 else 0)
    if it.get("sockets") is not None:
        eq("sockets (194)", it["sockets"], base.get((194, 0), 0))
    if "defense" in it:
        eq("defense (base 31)", it["defense"], base.get((31, 0), 0))
    if "maxdur" in it:
        eq("max durability (base 73)", it["maxdur"], base.get((73, 0), 0))
        if it["maxdur"]:
            eq("durability (base 72)", it["dur"], base.get((72, 0), 0))
    if "quantity" in it:
        eq("quantity (base 70)", it["quantity"], base.get((70, 0), 0))
    if it["has_gfx"]:
        eq("picture", it["gfx"], lx["gfx"])
    main = {}
    sets = {}
    for st, fl, ent in subs:
        d = dict(ent)
        if st == 0 and fl & 0x40 and not fl & 0x2000:
            main = d
        elif st in SETSTATES:
            sets[st] = d
    want = {k: v for k, v in saved_list(T, isc, main).items()}
    got = file_list(it["props"])
    # a group follower is written with its head: compare on the union, absent = 0
    diff = [(k, want.get(k, 0), got.get(k, 0)) for k in sorted(set(want) | set(got), key=str)
            if want.get(k, 0) != got.get(k, 0)]
    eq("main property list ((stat, param), logged >> ValShift, saved)", [], diff)
    if it["quality"] == 5:
        bits = sum(1 << (st - 0xA5) for st, d in sets.items() if d)
        eq("set list bits", it["set_lists"], bits)
        for (st, d), props in zip(sorted((st, d) for st, d in sets.items() if d), it.get("set_props", [])):
            w, g = saved_list(T, isc, d), file_list(props)
            diff = [(k, w.get(k, 0), g.get(k, 0)) for k in sorted(set(w) | set(g), key=str) if w.get(k, 0) != g.get(k, 0)]
            eq("set list %d ((stat, param), logged, saved)" % st, [], diff)


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("saved")
    c.add_argument("save")
    c.add_argument("logs", nargs="+")
    c.add_argument("--excel", default=EXCEL)
    for name in ("check", "rerun"):
        c = sub.add_parser(name)
        c.add_argument("logs", nargs="+")
        c.add_argument("--excel", default=EXCEL)
        c.add_argument("-v", "--verbose", action="store_true")
    ns = ap.parse_args(argv)
    if ns.cmd == "saved":
        return cmd_saved(ns)
    return cmd_check(ns, ns.cmd == "rerun")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

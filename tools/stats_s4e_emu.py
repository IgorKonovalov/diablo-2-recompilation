#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S4e part 1 (`lane/n66z`): the stats family. The stat-list readers, the three maxima
getters, StatEvaluate's ops 2, 3, 10 and 12, and StatRecompute's take test, run on the pinned Game.exe under Ghidra's
p-code emulator (ADR-0015) with re/ghidra_scripts/EmuBoundary.java, compared with the models below.

    python3 -I tools/stats_s4e_emu.py cases [--dir D]      write D/<family>.cases, .mem, .json for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/stats_s4e_emu.py check [--dir D]      compare, account every traced access, run the controls
    python3 -I tools/stats_s4e_emu.py static               objdump pins and the image bytes the record cites
    python3 -I tools/stats_s4e_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66z/s4e/run. Every draw comes from random.Random("n66z-s4e-<family>").

Every callee runs whole on the declared image (ruling R2: no declared return, no observed boundary in this part). The
allocator entries and the assert path are guards: a case that reaches one stops and fails (the generator rejects a
case whose model would reach the allocator, so none is expected).

Families (function, convention; inventory rows of stats/aggregate):
  read  sub_00624F60_StatListGetValue (EBX list, EDI key; stack rec), sub_00624ED0_StatListGetBaseValue (same), and
        STATS_GetUnitStat 0x00625480 (unit, stat, param; stdcall), on synthetic lists, owners and records.   row 20
  max   sub_00625D10_UnitGetMaxHp, UNIT_GetMaxMana 0x00625D60, UNIT_GetMaxStamina 0x00625DB0 (unit; stdcall), with
        StatListGetValue as callee; the DataTables count varied around 7, 9 and 11.                    rows 1, 21
  ops   sub_00626200_StatEvaluate (ECX list, EDX key) on a target whose op table holds ops 2, 3, 10, 12 and above 13,
        sources plain or with their own op 2/3 table; MulDiv 0x00483360 and StatListGetValue as callees.   row 15
  take  sub_006266C0_StatRecompute (ECX list, EDX key; stack rec, arg) on a source with one to three targets and up to
        three dependents; StatEvaluate, STATLIST_CacheWrite 0x00625150 (insert 0x00624C80, remove 0x00624D10, the
        CRT memmove 0x00683840), StatListGetValue and STATS_GetUnitStat as callees. The take test at 0x006267AD by
        the source row's op class (0x0062690C, jump table 0x006268F4).                                    row 14

Controls: each named test reversed or replaced alone, and the spec's own readings (`spec_*`); `sep` counts the cases
a control's prediction differs from the model's, `passed` those where the emulator still equals the control (must be 0
when sep > 0). Stdlib only, plus objdump for `static`.
"""
import argparse
import collections
import hashlib
import json
import os
import random
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sweep_s1e as E  # noqa: E402
import sweep_s1f as F  # noqa: E402
import sweep_s4b as S4  # noqa: E402
from sweep_s1e import M32, s32  # noqa: E402

DEFDIR = os.path.join(ROOT, "workspace", "logs", "n66z", "s4e", "run")
FAMILIES = ("read", "max", "ops", "take")
NCASES = {"read": 4000, "max": 1500, "ops": 2500, "take": 3000}

FN = {"GetValue": 0x00624F60, "GetBaseValue": 0x00624ED0, "GetUnitStat": 0x00625480,
      "MaxHp": 0x00625D10, "MaxMana": 0x00625D60, "MaxStamina": 0x00625DB0,
      "StatEvaluate": 0x00626200, "StatRecompute": 0x006266C0}
MAXSTAT = {"MaxHp": 7, "MaxMana": 9, "MaxStamina": 11}
POP = {"GetValue": 4, "GetBaseValue": 4, "GetUnitStat": 12, "MaxHp": 4, "MaxMana": 4, "MaxStamina": 4,
       "StatEvaluate": 0, "StatRecompute": 8}

G_PDATATABLES = 0x00744304
MASK4 = 0x006CE270              # u32 4 (.rdata): fMin (+0x05) and damagerelated (+0x04) bit
MASK_CB = 0x006CE274            # u32 (.rdata): fCallback bit of +0x05, read only when the list has a callback
TAKE_CLASS = bytes.fromhex("0005010102020303000000000504")   # 0x0062690C, op 0..13
TAKE_JT = 0x006268F4

# scratch memory (outside the image and the emulator stack 0x7FE00000..0x7FF01000)
DTS = 0x13100000
ISC = 0x13200000                # records 0x144 bytes each
NISC = 0x200
REC = 0x13300000                # a free-standing record for the readers' rec argument
LIST, OWN, CACHE, OWNER = 0x13400000, 0x13401000, 0x13402000, 0x13403000
LIST2, OWN2, CACHE2, OWNER2 = 0x13404000, 0x13405000, 0x13406000, 0x13407000
UNIT, UNIT2 = 0x13408000, 0x13409000

RS_MASK4 = (MASK4, MASK4 + 4, "r", "mask 0x006CE270 (.rdata, u32 4)")
RS_TJT = (0x0062690C, 0x0062690C + 14, "r", "take class table 0x0062690C (.text)")
RS_TJT2 = (TAKE_JT, TAKE_JT + 24, "r", "take jump table 0x006268F4 (.text)")
RS_SEJT = (0x00626688, 0x00626688 + 52, "r", "StatEvaluate jump table 0x00626688 (.text)")
RS_MEMMOVE = (0x00683840, 0x00683C00, "r", "the CRT memmove 0x00683840's own jump tables (.text)")


class Report(E.Report):
    def line(self):
        keys = ["cases", "match", "bad", "neg", "traced", "undeclared", "stopped"]
        rest = sorted(k for k in self.c if k not in keys)
        return "S4E %s " % self.fam + " ".join("%s=%d" % (k, self.c[k]) for k in keys + rest)


def le32(v):
    return struct.pack("<I", v & M32)


def w(addr, data):
    return "w %08x %s" % (addr, bytes(data).hex())


def skey(k):
    return s32(k)


def sar(v, n):
    return s32(v) >> (n & 31)


# ----------------------------------------------------------------------------------------------- the world
class Lst:
    """A stat list: flags (+0x10), owner type field (+0x08), linked unit (+0x04), owner (+0x44), own and cache."""

    def __init__(self, base, own_at, cache_at, owner_at):
        self.base, self.own_at, self.cache_at, self.owner_at = base, own_at, cache_at, owner_at
        self.ext = False
        self.own = {}
        self.cache = {}
        self.cap = 0
        self.flags = 0
        self.ct = 0                  # +0x08
        self.linked = 0              # +0x04
        self.owner = 0               # +0x44 pointer (owner_at or 0)
        self.otype = 0               # the owner's type dword

    def active(self):
        return self.cache if self.ext else self.own

    @staticmethod
    def arr(d):
        return b"".join(struct.pack("<Ii", k & M32, s32(v)) for k, v in sorted(d.items(), key=lambda kv: skey(kv[0])))

    def lines(self, fields):
        out = []
        if "flags" in fields:
            out.append(w(self.base + 0x10, le32(self.flags | (0x80000000 if self.ext else 0))))
        if "own" in fields:
            out.append(w(self.own_at, self.arr(self.own) or b"\0"))
            out.append(w(self.base + 0x24, le32(self.own_at) + struct.pack("<hH", len(self.own), len(self.own))))
        if "cache" in fields:
            body = self.arr(self.cache)
            out.append(w(self.cache_at, body + b"\0" * (8 * (self.cap - len(self.cache)))) if self.cap else
                       w(self.cache_at, b"\0"))
            out.append(w(self.base + 0x48, le32(self.cache_at) + struct.pack("<hH", len(self.cache), self.cap)))
        if "owner" in fields:
            out.append(w(self.base + 0x44, le32(self.owner)))
            if self.owner:
                out.append(w(self.owner_at, le32(self.otype)))
        if "ct" in fields:
            out.append(w(self.base + 0x08, le32(self.ct)))
        if "linked" in fields:
            out.append(w(self.base + 0x04, le32(self.linked)))
        if "child" in fields and self.ext:
            out.append(w(self.base + 0x3C, le32(0)))
        if "cb" in fields:
            out.append(w(self.base + 0x5C, le32(0)))
        return out


class Rec:
    def __init__(self):
        self.b4 = 0
        self.b5 = 0
        self.vs = 0
        self.minaccr = 0
        self.keepzero = 0
        self.b51 = self.b52 = self.b53 = 0
        self.op = 0
        self.tg = [0xFFFF, 0xFFFF, 0xFFFF]
        self.ent = []                # [(ob, src, op, param)]
        self.deps = []


def rec_lines(addr, r, fields):
    out = []
    if "b4" in fields:
        out.append(w(addr + 0x04, bytes([r.b4])))
    if "b5" in fields:
        out.append(w(addr + 0x05, bytes([r.b5])))
    if "vs" in fields:
        out.append(w(addr + 0x18, bytes([r.vs])))
    if "minaccr" in fields:
        out.append(w(addr + 0x2C, le32(r.minaccr)))
    if "kz" in fields:
        out.append(w(addr + 0x50, bytes([r.keepzero, r.b51, r.b52, r.b53, r.op])))
    elif "b52" in fields:
        out.append(w(addr + 0x52, bytes([r.b52])))
    if "tg" in fields:
        out.append(w(addr + 0x58, struct.pack("<3H", *r.tg)))
        out.append(w(addr + 0x5E, struct.pack("<%dH" % (len(r.deps) + 1), *(r.deps + [0xFFFF]))))
    if "ent" in fields:
        body = b"".join(struct.pack("<HHBB", ob, src, op, par) for ob, src, op, par in r.ent)
        if len(r.ent) < 16:
            body += struct.pack("<HHBB", 0xFFFF, 0, 0, 0)
        out.append(w(addr + 0xDE, body))
    return out


def getvalue(lst, key, rec, base=False, ctl=None):
    """StatListGetValue (base=False: the cache when extended) / StatListGetBaseValue (base=True: own)."""
    arr = lst.own if (base or not lst.ext or ctl == "own") else lst.cache
    if key not in arr:
        if ctl == "absent_floor" and rec is not None:
            arr = {key: 0}
        else:
            return 0
    v = s32(arr[key])
    if rec is None or not rec.b5 & 4:
        return v & M32
    if not lst.ext and ctl != "noext":
        return v & M32
    if not lst.owner:
        return v & M32
    if lst.otype not in (0, 1) and ctl != "notype":
        return v & M32
    m = s32(rec.minaccr)
    if ctl == "spec_shifted":
        lim = s32((rec.minaccr << (rec.vs & 31)) & M32)
        below = v < lim
    elif ctl == "unsigned":
        below = (v & M32) < (rec.minaccr & M32)
    elif ctl == "le":
        below = v <= m
    else:
        below = v < m
    if below:
        sh = rec.vs if ctl == "nomask" else rec.vs & 31
        return (rec.minaccr << sh) & M32
    return v & M32


def rand_value(rnd, m=None, vs=0):
    r = rnd.random()
    if m is not None and r < 0.45:
        lim = s32((m << (vs & 31)) & M32)
        return s32(rnd.choice([m - 1, m, m + 1, m - 2, (m + lim) // 2 if lim > m else m + 3, lim, lim - 1, lim + 1,
                               0, -1, -rnd.randrange(1, 1000)]))
    if r < 0.7:
        return rnd.randrange(-300, 3000)
    if r < 0.8:
        return rnd.choice([0x7FFFFFFF, -0x80000000, 0x100000, -0x100001, 0x40000000, 0])
    return s32(rnd.getrandbits(32))


def rand_rec_floor(rnd, r):
    r.b5 = (rnd.getrandbits(8) & ~4) | (4 if rnd.random() < 0.75 else 0)
    r.vs = rnd.choice([0, 0, 8, 8, 8, rnd.randrange(32), rnd.randrange(32, 256)])
    r.minaccr = s32(rnd.choice([0, 1, 1, 1, 2, rnd.randrange(3, 300), -rnd.randrange(1, 300), rnd.getrandbits(32)]))


def rand_keys(rnd, n, extra=()):
    ks = set(extra)
    while len(ks) < n + len(extra):
        st = rnd.choice([rnd.randrange(0, NISC), rnd.randrange(0, 0x10000)])
        ks.add((st << 16) | rnd.choice([0, 0, rnd.getrandbits(16)]))
    return list(ks)


def make_list(rnd, base, own_at, cache_at, owner_at, key=None, m=None, vs=0, present=0.8):
    L = Lst(base, own_at, cache_at, owner_at)
    L.ext = rnd.random() < 0.7
    L.flags = rnd.getrandbits(31) & ~0x20000000 if rnd.random() < 0.5 else 0
    L.owner = owner_at if rnd.random() < 0.9 else 0
    L.otype = rnd.choice([0, 1, 0, 1, 2, 3, 4, 5, rnd.getrandbits(32)])
    for d in (L.own, L.cache):
        for k in rand_keys(rnd, rnd.randrange(0, 9)):
            d[k] = rand_value(rnd)
        if key is not None and rnd.random() < present:
            d[key] = rand_value(rnd, m, vs)
    L.cap = len(L.cache)
    return L


# ----------------------------------------------------------------------------------------------- read
def gen_read(rnd):
    fn = rnd.choice(["GetValue", "GetValue", "GetBaseValue", "GetUnitStat", "GetUnitStat"])
    rec = Rec()
    rand_rec_floor(rnd, rec)
    a = {"fn": fn}
    if fn == "GetUnitStat":
        stat = rnd.choice([rnd.randrange(NISC), rnd.randrange(NISC), -rnd.randrange(1, 5), NISC + rnd.randrange(3),
                           NISC - 1, 0, rnd.getrandbits(32)])
        stat = s32(stat)
        param = rnd.choice([0, 0, rnd.getrandbits(16), rnd.getrandbits(32)])
        key = ((stat << 16) + (param & 0xFFFF)) & M32
        L = make_list(rnd, LIST, OWN, CACHE, OWNER, key, rec.minaccr, rec.vs)
        unit = UNIT if rnd.random() < 0.95 else 0
        ulist = LIST if rnd.random() < 0.95 else 0
        lines = [w(DTS + 0xBCC, le32(ISC)), w(DTS + 0xBD4, le32(NISC)), w(G_PDATATABLES, le32(DTS))]
        if unit:
            lines.append(w(UNIT + 0x5C, le32(ulist)))
        inb = 0 <= stat < NISC
        if unit and ulist and inb:
            lines += L.lines(("flags", "own", "cache", "owner"))
            lines += rec_lines(ISC + stat * 0x144, rec, ("b5", "vs", "minaccr"))
        lines.append("call %08x %08x %08x %08x %08x %08x" % (FN[fn], rnd.getrandbits(32), rnd.getrandbits(32), unit,
                                                             stat & M32, param & M32))
        if not unit or not ulist or not inb:
            want = 0
        else:
            want = getvalue(L, key, rec)
        a.update(key=key, stat=stat, param=param & M32, unit=unit, ulist=ulist, want=want)
        a["ctl"] = {c: (0 if (not unit or not ulist or not inb) else getvalue(L, key, rec, ctl=c))
                    for c in ("spec_shifted", "noext", "notype", "unsigned", "le", "nomask", "absent_floor", "own")}
        a["br"] = br_read(L, key, rec, unit and ulist and inb, stat)
        return lines, a
    key = rnd.choice(rand_keys(rnd, 1)) if rnd.random() < 0.9 else rnd.getrandbits(32)
    L = make_list(rnd, LIST, OWN, CACHE, OWNER, key, rec.minaccr, rec.vs)
    recp = REC if rnd.random() < 0.9 else 0
    lines = L.lines(("flags", "own", "owner") + (("cache",) if fn == "GetValue" else ()))
    if recp:
        lines += rec_lines(REC, rec, ("b5", "vs", "minaccr"))
    lines += ["r ebx %08x" % LIST, "r edi %08x" % key,
              "call %08x %08x %08x %08x" % (FN[fn], rnd.getrandbits(32), rnd.getrandbits(32), recp)]
    r = rec if recp else None
    base = fn == "GetBaseValue"
    a.update(key=key, want=getvalue(L, key, r, base))
    a["ctl"] = {c: getvalue(L, key, r, base, ctl=c)
                for c in ("spec_shifted", "noext", "notype", "unsigned", "le", "nomask", "absent_floor")}
    a["ctl"]["own"] = getvalue(L, key, r, base, ctl="own") if not base else getvalue(L, key, r, False)
    a["br"] = br_read(L, key, r, True, None, base)
    return lines, a


def br_read(L, key, rec, reached, stat, base=False):
    b = collections.Counter()
    if not reached:
        b["unit_or_list_null_or_stat_out"] += 1
        if stat is not None and not (0 <= stat < NISC):
            b["stat_out_of_range"] += 1
        return b
    arr = L.own if (base or not L.ext) else L.cache
    if key not in arr:
        b["absent"] += 1
        return b
    b["present"] += 1
    if rec is None:
        b["rec_null"] += 1
    elif not rec.b5 & 4:
        b["fmin_off"] += 1
    elif not L.ext:
        b["not_extended"] += 1
    elif not L.owner:
        b["owner_null"] += 1
    elif L.otype not in (0, 1):
        b["owner_type_other"] += 1
    else:
        v = s32(arr[key])
        b["floor_tested"] += 1
        if v < s32(rec.minaccr):
            b["floored"] += 1
            b["floored_vs_ge32"] += rec.vs >= 32
            lim = s32((rec.minaccr << (rec.vs & 31)) & M32)
        else:
            lim = s32((rec.minaccr << (rec.vs & 31)) & M32)
            b["kept_between_minaccr_and_shifted"] += v < lim
        b["minaccr_negative"] += s32(rec.minaccr) < 0
    return b


# ----------------------------------------------------------------------------------------------- max
def gen_max(rnd):
    fn = rnd.choice(["MaxHp", "MaxMana", "MaxStamina"])
    st = MAXSTAT[fn]
    rec = Rec()
    rand_rec_floor(rnd, rec)
    key = st << 16
    L = make_list(rnd, LIST, OWN, CACHE, OWNER, key, rec.minaccr, rec.vs, present=0.85)
    for d in (L.own, L.cache):             # neighbours that a wrong stat would read
        for k in (key - 0x10000, key + 0x10000):
            if rnd.random() < 0.7:
                d[k] = rand_value(rnd, rec.minaccr, rec.vs)
    L.cap = len(L.cache)
    unit = UNIT if rnd.random() < 0.95 else 0
    ulist = LIST if rnd.random() < 0.95 else 0
    cnt = rnd.choice([NISC, NISC, NISC, st, st + 1, st - 1, 0, -1, rnd.getrandbits(32)])
    base = ISC if rnd.random() < 0.95 else (-(st * 0x144)) & M32
    lines = [w(G_PDATATABLES, le32(DTS))]
    if unit:
        lines.append(w(UNIT + 0x5C, le32(ulist)))
    if unit and ulist:
        lines.append(w(DTS + 0xBD4, le32(cnt)))
        if s32(cnt) > st:
            lines.append(w(DTS + 0xBCC, le32(base)))
    ok = unit and ulist and s32(cnt) > st and base == ISC
    if ok:
        lines += L.lines(("flags", "own", "cache", "owner"))
        lines += rec_lines(ISC + st * 0x144, rec, ("b5", "vs", "minaccr"))
    lines.append("call %08x %08x %08x %08x" % (FN[fn], rnd.getrandbits(32), rnd.getrandbits(32), unit))
    want = getvalue(L, key, rec) if ok else 0
    ctl = {}
    ctl["stat_minus1"] = getvalue(L, key - 0x10000, rec) if ok else 0
    ctl["base_value"] = getvalue(L, key, rec, base=True) if ok else 0
    ctl["nofloor"] = getvalue(L, key, None) if ok else 0
    ctl["count_ge"] = getvalue(L, key, rec) if (unit and ulist and s32(cnt) >= st and base == ISC) else 0
    ctl["spec_shifted"] = getvalue(L, key, rec, ctl="spec_shifted") if ok else 0
    b = collections.Counter()
    b[fn] += 1
    b["unit_null"] += not unit
    b["list_null"] += bool(unit and not ulist)
    b["count_le_stat"] += bool(unit and ulist and s32(cnt) <= st)
    b["rec_zero"] += bool(unit and ulist and s32(cnt) > st and base != ISC)
    if ok:
        b.update(br_read(L, key, rec, True, None))
    return lines, {"fn": fn, "want": want, "ctl": ctl, "br": b}


# ----------------------------------------------------------------------------------------------- ops
class OpsWorld:
    def __init__(self, rnd):
        self.rnd = rnd
        self.recs = {}
        ids = rnd.sample(range(1, NISC), 14)
        self.t, srcs, bases, leaf = ids[0], ids[1:5], ids[5:9], ids[9:14]
        self.L = make_list(rnd, LIST, OWN, CACHE, OWNER)
        self.L.ext = rnd.random() < 0.6
        self.L.ct = rnd.choice([0, 1, 0, 1, 2, 3, 4, rnd.getrandbits(32)])
        tr = Rec()
        tr.b4, tr.b52 = rnd.getrandbits(8), rnd.choice([1, 1, 0x40])
        n = rnd.choice([1, 2, 3, 4, 6, 16])
        for _ in range(n):
            r = rnd.random()
            op = 2 if r < 0.3 else 3 if r < 0.75 else rnd.choice([10, 12, 14, 0x80, 0xFF])
            ob = rnd.choice(bases) if rnd.random() < 0.9 else rnd.choice([0xFFFF, NISC, rnd.randrange(NISC, 0xFFFF)])
            tr.ent.append((ob, rnd.choice(srcs), op, rnd.choice([0, 0, 1, 2, 4, 8, rnd.randrange(32),
                                                                rnd.getrandbits(8)])))
        self.recs[self.t] = tr
        for s in srcs:
            r = Rec()
            r.b4 = rnd.getrandbits(8)
            if rnd.random() < 0.25:
                r.b52 = 1
                r.ent = [(rnd.choice(bases), rnd.choice(leaf), rnd.choice([2, 3]), rnd.randrange(8))
                         for _ in range(rnd.randrange(1, 3))]
            self.recs[s] = r
        for s in leaf:
            r = Rec()
            r.b4 = rnd.getrandbits(8)
            self.recs[s] = r
        for b in bases:
            r = self.recs.get(b) or Rec()
            r.vs = rnd.choice([0, 0, 8, rnd.randrange(32), rnd.randrange(32, 256)])
            self.recs[b] = r
        self.param = rnd.choice([0, 0, rnd.getrandbits(16)])
        self.key = (self.t << 16) | self.param
        for d in (self.L.own, self.L.cache):
            if rnd.random() < 0.9:
                d[self.key] = rand_value(rnd)
            for s in srcs + leaf:
                if rnd.random() < 0.85:
                    d[s << 16] = rand_value(rnd) if rnd.random() < 0.9 else 0
            for b in bases:
                if rnd.random() < 0.85:
                    v = rand_value(rnd)
                    d[b << 16] = v if rnd.random() < 0.6 else abs(v) << rnd.choice([0, 8])
        self.L.cap = len(self.L.cache)

    def lines(self):
        out = [w(DTS + 0xBCC, le32(ISC)), w(DTS + 0xBD4, le32(NISC)), w(G_PDATATABLES, le32(DTS))]
        out += self.L.lines(("flags", "own", "cache", "ct", "child"))
        for rid, r in self.recs.items():
            fl = ["b4", "b52"]
            if r.b52:
                fl.append("ent")
            if r.vs or any(rid == e[0] for rr in self.recs.values() for e in rr.ent):
                fl.append("vs")
            out += rec_lines(ISC + rid * 0x144, r, fl)
        out.append("call %08x %08x %08x" % (FN["StatEvaluate"], LIST, self.key))
        return out

    def ev(self, key, br, ctl=None, depth=0):
        t = (key >> 16) & 0xFFFF
        if t >= NISC:
            return 0
        r = self.recs.get(t)
        v = s32(self.L.own.get(key, 0))
        if r is None or not r.b52:
            return v
        b0 = acc = v
        for k in range(16):
            if k >= len(r.ent):
                break
            ob, src, op, par = r.ent[k]
            if op in (2, 3) or (ctl == "op10_as_op2" and op == 10):
                if self.L.ct not in (0, 1) and ctl != "noct":
                    br["op%d_ct_other" % op] += 1
                    continue
                if ob == 0xFFFF or ob >= NISC:
                    br["op%d_ob_none" % op] += 1
                    continue
                act = self.L.active()
                bv = s32(act.get(ob << 16, 0))
                b = bv >> (self.recs[ob].vs & 31) if ctl != "logical" else (bv & M32) >> (self.recs[ob].vs & 31)
                b = s32(b)
                if b <= 0:
                    br["op%d_b_le0" % op] += 1
                    continue
                p = self.ev(src << 16, br, ctl, depth + 1)
                if p == 0:
                    br["op%d_p0" % op] += 1
                    continue
                prod = s32(p * b)
                term = prod >> (par & 31) if ctl != "logical" else s32((prod & M32) >> (par & 31))
                br["op%d_term" % op] += 1
                br["op%d_par_ge32" % op] += par >= 32
                br["op%d_prod_wraps" % op] += prod != p * b
                br["depth%d" % depth] += 1
                if op == 2 or ctl == "op3_as_op2" or (ctl == "op10_as_op2" and op == 10):
                    acc = s32(acc + term)
                else:
                    base = acc if ctl == "op3_acc" else b0
                    acc = s32(acc + s32(F.muldiv_model(base, term, 100, br=br if ctl is None else None)[0]))
                continue
            br["op_%s_skipped" % ("10" if op == 10 else "12" if op == 12 else "gt13")] += 1
        return acc


def gen_ops(rnd):
    wd = OpsWorld(rnd)
    br = collections.Counter()
    want = wd.ev(wd.key, br) & M32
    ctl = {c: wd.ev(wd.key, collections.Counter(), ctl=c) & M32
           for c in ("op3_as_op2", "op3_acc", "noct", "logical", "op10_as_op2")}
    br["ext"] += wd.L.ext
    return wd.lines(), {"want": want, "ctl": ctl, "br": br}


# ----------------------------------------------------------------------------------------------- take
class Alloc(Exception):
    pass


class TakeWorld:
    def __init__(self, rnd):
        self.rnd = rnd
        self.recs = {}
        ids = rnd.sample(range(1, NISC), 12)
        self.s, tgs, deps, ws = ids[0], ids[1:4], ids[4:7], ids[7:12]
        self.L = make_list(rnd, LIST, OWN, CACHE, OWNER)
        self.L.ext = rnd.random() < 0.6
        self.L.ct = rnd.choice([0, 1, 0, 1, 4, 4, 2, 3, rnd.getrandbits(32)])
        self.L.linked = UNIT if rnd.random() < 0.85 else 0
        self.utype = rnd.choice([0, 1, 0, 1, 2, 4, rnd.getrandbits(32)])
        self.ulist_same = rnd.random() < 0.3
        self.U = make_list(rnd, LIST2, OWN2, CACHE2, OWNER2)
        self.unit_has_list = rnd.random() < 0.93
        sr = Rec()
        sr.b4 = rnd.getrandbits(8)
        sr.b51 = rnd.choice([1, 1, 1, 1, 0, 0x20])
        sr.op = rnd.choice(list(range(14)) + [1, 2, 3, 4, 5, 6, 7, 13, 2, 3, 4, 5, rnd.randrange(14, 256)])
        sr.keepzero = rnd.choice([0, 0, 0, 1])
        sr.b53 = rnd.choice([0, 0, 1])
        nt = rnd.choice([1, 2, 3, 3])
        sr.tg = tgs[:nt] + [0xFFFF] * (3 - nt)
        sr.deps = deps[:rnd.choice([0, 0, 1, 2, 3])]
        # the opIn words the take test reads (+0x0DE + 6k of the SOURCE row)
        sr.ent = [(rnd.choice(ws + [0xFFFF]) if rnd.random() < 0.95 else rnd.randrange(NISC, 0xFFFF), 0,
                   rnd.choice([0, 1]), 0)
                  for _ in range(3)]
        self.recs[self.s] = sr
        for t in tgs + deps:
            r = Rec()
            r.b4 = rnd.getrandbits(8)
            r.keepzero = rnd.choice([0, 0, 1])
            r.b53 = rnd.choice([0, 0, 1])
            self.recs[t] = r
        for x in ws:
            r = Rec()
            rand_rec_floor(rnd, r)
            self.recs[x] = r
        self.param = rnd.choice([0, 0, rnd.getrandbits(16)])
        self.key = (self.s << 16) | self.param
        for d in (self.L.own, self.L.cache):
            if rnd.random() < 0.8:
                d[self.key] = rand_value(rnd) if rnd.random() < 0.8 else 0
            for t in tgs + deps:
                if rnd.random() < 0.75:
                    d[t << 16] = rand_value(rnd) if rnd.random() < 0.8 else 0
            for x in ws:
                if rnd.random() < 0.7:
                    d[x << 16] = rnd.choice([0, 1, -1, rnd.randrange(-50, 50), rand_value(rnd)])
        for d in (self.U.own, self.U.cache):
            for x in ws:
                if rnd.random() < 0.7:
                    d[x << 16] = rnd.choice([0, 1, -1, rnd.randrange(-50, 50), rand_value(rnd)])
        self.L.cache = {k: v for k, v in self.L.cache.items() if v != 0 or self.recs.get(k >> 16, Rec()).keepzero}
        self.L.cap = len(self.L.cache) + rnd.randrange(1, 9)
        self.U.cap = len(self.U.cache)
        self.cbflag = rnd.random() < 0.5

    # -------- model
    def ul(self):
        return self.L if self.ulist_same else self.U

    def ev(self, key):
        return s32(self.L.own.get(key, 0))            # every row here has +0x52 = 0: the own value (no children)

    def cw(self, key, v, rec, trace):
        L = self.L
        v = s32(v)
        if key not in L.cache:
            if v == 0:
                trace.append(("cw_skip", key))
                return
            if len(L.cache) >= L.cap:
                raise Alloc("grow")
            L.cache[key] = 0
            trace.append(("ins", key))
        if v == 0 and not rec.keepzero:
            del L.cache[key]
            if L.cap - len(L.cache) > 8:
                raise Alloc("shrink")
            trace.append(("rem", key))
            return
        L.cache[key] = v
        if rec.b53:
            L.flags |= 0x20000000
        trace.append(("set", key, v))

    def takes(self, k, ctl, br):
        sr = self.recs[self.s]
        op = sr.op
        if ctl == "gt13_false" and op > 13:
            return False
        if op > 13:
            br["op_gt13_taken"] += 1
            return True
        cls = TAKE_CLASS[op]
        r = self._takes(k, ctl, br, sr, cls)
        br["class%d_%s" % (cls, "taken" if r else "not")] += 1
        return r

    def _takes(self, k, ctl, br, sr, cls):
        if ctl == "op67_false" and cls == 3:
            return False
        if ctl == "class0_true" and cls == 0:
            return True
        if ctl == "class5_false" and cls == 5:
            return False
        if ctl == "class4_false" and cls == 4:
            return False
        if ctl == "class3_any_ct" and cls == 3:
            return True
        if ctl == "class4_ct01" and cls == 4:
            return self.L.ct in (0, 1)
        wd = sr.ent[k][0] if ctl != "w_from_target" else (self.recs[sr.tg[k]].ent[0][0]
                                                           if self.recs[sr.tg[k]].ent else 0xFFFF)
        br["class%d" % cls] += 1
        if cls == 5:
            return True
        if cls == 1:
            if self.L.ct not in (0, 1):
                br["c1_ct_other"] += 1
                return False
            if wd == 0xFFFF:
                br["c1_w_none"] += 1
                return False
            if ctl == "c1_floor" and wd < NISC:
                v = s32(getvalue(self.L, wd << 16, self.recs.get(wd)))
            else:
                v = s32(getvalue(self.L, wd << 16, None))
            br["c1_pos"] += v > 0
            return v > 0
        if cls == 2:
            if not self.L.linked:
                br["c2_unlinked"] += 1
                return False
            if self.utype not in (0, 1):
                br["c2_utype_other"] += 1
                return False
            if wd == 0xFFFF:
                br["c2_w_none"] += 1
                return False
            if not self.unit_has_list:
                br["c2_no_list"] += 1
                return False
            if wd >= NISC:
                br["c2_w_out"] += 1
                return False
            r = self.recs.get(wd) if ctl != "c2_nofloor" else None
            v = s32(getvalue(self.ul(), wd << 16, r))
            br["c2_pos"] += v > 0
            return v > 0
        if cls == 3:
            return self.L.ct in (0, 1)
        if cls == 4:
            return self.L.ct == 4
        return False

    def recompute(self, key, rec, trace, ctl, br, depth=0):
        v = self.ev(key)
        if not rec.b51:
            self.cw(key, v, rec, trace)
            return v
        if v == 0:
            self.cw(key, 0, rec, trace)
            br["src_v0"] += 1
        flag = True
        for k in range(3):
            t = rec.tg[k]
            if t == 0xFFFF:
                break
            trec = self.recs[t]
            tv = self.recompute(t << 16, trec, trace, ctl, br, depth + 1)
            self.cw(t << 16, tv, trec, trace)
            if tv != 0 or ctl == "always_test":
                if ctl == "no_take":
                    continue
                if self.takes(k, ctl, br):
                    flag = False
            else:
                br["tv0_no_test"] += 1
        if flag and v != 0:
            br["src_written_deps"] += 1
            self.cw(key, v, rec, trace)
            for d in rec.deps[:64]:
                drec = self.recs[d]
                dv = self.recompute(d << 16, drec, trace, ctl, br, depth + 1)
                self.cw(d << 16, dv, drec, trace)
        elif not flag:
            br["taken"] += 1
        return v

    def run(self, ctl=None, br=None):
        import copy
        save = (copy.deepcopy(self.L.cache), self.L.flags)
        trace = []
        br = br if br is not None else collections.Counter()
        try:
            v = self.recompute(self.key, self.recs[self.s], trace, ctl, br)
            out = (v & M32, dict(self.L.cache), self.L.flags)
        finally:
            self.L.cache, self.L.flags = save
        return out, trace

    def lines(self):
        out = [w(DTS + 0xBCC, le32(ISC)), w(DTS + 0xBD4, le32(NISC)), w(G_PDATATABLES, le32(DTS))]
        out += self.L.lines(("flags", "own", "cache", "ct", "linked", "owner", "child", "cb"))
        if self.L.linked:
            out.append(w(UNIT, le32(self.utype)))
            out.append(w(UNIT + 0x5C, le32((LIST if self.ulist_same else LIST2) if self.unit_has_list else 0)))
        if not self.ulist_same:
            out += self.U.lines(("flags", "own", "cache", "owner"))
        for rid, r in self.recs.items():
            fl = ["b4", "kz"]
            if rid == self.s:
                fl += ["tg", "ent"]
            else:
                fl += ["b5", "vs", "minaccr"]
            out += rec_lines(ISC + rid * 0x144, r, fl)
        out.append(w(LIST, le32(0x13F00000)))      # list +0x00: the pool handed to insert/remove (used only to grow)
        out.append("d %08x %d" % (LIST + 0x10, 4))
        out.append("d %08x %d" % (LIST + 0x48, 8))
        out.append("d %08x %d" % (CACHE, 8 * self.L.cap))
        out.append("call %08x %08x %08x %08x %08x" % (FN["StatRecompute"], LIST, self.key,
                                                      ISC + self.s * 0x144, self.rnd.getrandbits(32)))
        return out


def gen_take(rnd):
    while True:
        wd = TakeWorld(rnd)
        br = collections.Counter()
        try:
            (v, cache, flags), trace = wd.run(None, br)
        except Alloc:
            continue
        ctl = {}
        for c in ("w_from_target", "always_test", "no_take", "op67_false", "gt13_false", "c1_floor", "c2_nofloor",
                  "class0_true", "class5_false", "class4_false", "class3_any_ct", "class4_ct01"):
            try:
                ctl[c] = list(enc_take(wd.run(c)[0], wd.L.cap))
            except Alloc:
                ctl[c] = "alloc"
        br["op%d" % wd.recs[wd.s].op if wd.recs[wd.s].op <= 13 else "op_gt13"] += 1
        br["b51_0"] += not wd.recs[wd.s].b51
        br["ext"] += wd.L.ext
        br["ins"] += sum(1 for t in trace if t[0] == "ins")
        br["rem"] += sum(1 for t in trace if t[0] == "rem")
        br["flag_0x20000000_set"] += bool(flags & 0x20000000)
        return wd.lines(), {"want": list(enc_take((v, cache, flags), wd.L.cap)), "ctl": ctl, "br": br,
                            "cap": wd.L.cap}


def enc_take(res, cap):
    v, cache, flags = res
    ext = 0x80000000                    # the list's own ext bit is written by the case; compare the rest of +0x10
    body = Lst.arr(cache)
    return v, flags & ~ext & M32, len(cache), body.hex()


# ----------------------------------------------------------------------------------------------- driver
GEN = {"read": gen_read, "max": gen_max, "ops": gen_ops, "take": gen_take}


def cmd_cases(d, limit=None):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        rnd = random.Random("n66z-s4e-%s" % fam)
        cases, meta = [], []
        n = limit or NCASES[fam]
        for _ in range(n):
            lines, a = GEN[fam](rnd)
            cases.extend(lines)
            a["br"] = dict(a["br"])
            meta.append(a)
        mem = ["guard %08x" % x for x in F.FATAL + F.ALLOC]
        E.write_family(d, fam, cases, mem, {"cases": meta})
        print("%s: %d cases, %d lines" % (fam, n, len(cases)))


def got_of(fam, c):
    if fam != "take":
        return c["eax"]
    dumps = dict(c["dumps"])
    fl = struct.unpack("<I", dumps[LIST + 0x10])[0] & ~0x80000000
    cnt = struct.unpack("<h", dumps[LIST + 0x48][4:6])[0]
    body = dumps[CACHE][:8 * max(cnt, 0)]
    return [c["eax"], fl, cnt, body.hex()]


def cmd_check(d):
    rc = 0
    for fam in FAMILIES:
        calls, reads, writes = E.read_out(os.path.join(d, fam + ".out"))
        meta = json.load(open(os.path.join(d, fam + ".json")))["cases"]
        rep = Report(fam)
        sep, passed = collections.Counter(), collections.Counter()
        if len(calls) != len(meta):
            rep.bad("%d calls for %d cases" % (len(calls), len(meta)))
        for c, a in zip(calls, meta):
            rep.c["cases"] += 1
            if F.stopped(rep, c):
                continue
            fn = a.get("fn", "StatEvaluate" if fam == "ops" else "StatRecompute")
            got = got_of(fam, c)
            ok = got == a["want"] and c["pop"] == POP[fn]
            rep.c["match"] += ok
            if not ok:
                rep.bad("case %d %s: got %s pop=%d want %s" % (c["n"], fn, got, c["pop"], a["want"]))
                continue
            rep.branches.update(a["br"])
            for k, v in a["ctl"].items():
                if v != a["want"]:
                    sep[k] += 1
                    passed[k] += v == got
        declared = [RS_MASK4, RS_TJT, RS_TJT2, RS_SEJT, RS_MEMMOVE]
        E.account(rep, reads, writes, declared)
        for k in sorted(set(sep) | set(a["ctl"])):
            rep.notes.append("  control %s: sep=%d passed=%d" % (k, sep[k], passed[k]))
            if passed[k]:
                rep.bad("control %s passed %d" % (k, passed[k]))
        neg = sum(sep.values())
        rc |= E.finish(rep, neg)
    return rc


PINS = [  # (va, mnemonic, operand substring): the instructions the record cites (ADR-0015 (5))
    (0x00624FC8, "cmp", "eax,edx"), (0x00624FCA, "jge", ""), (0x00624FCF, "shl", "edx,cl"),
    (0x00624F28, "cmp", "eax,edx"), (0x00624F2F, "shl", "edx,cl"), (0x00624F07, "test", "0x80000000"),
    (0x00624F9F, "mov", "0x6ce270"), (0x006254D0, "shl", "edi,0x10"), (0x006254D3, "add", "edi,eax"),
    (0x00625D2B, "cmp", "0x7"), (0x00625D32, "jle", ""), (0x00625D3A, "add", "0x8dc"),
    (0x00625D7B, "cmp", "0x9"), (0x00625D8A, "add", "0xb64"), (0x00625DCB, "cmp", "0xb"), (0x00625DDA, "add", "0xdec"),
    (0x00626301, "sar", "edi,cl"), (0x00626323, "imul", "eax,edi"), (0x00626326, "sar", "eax,cl"),
    (0x00626372, "sar", "edi,cl"), (0x00626396, "imul", "edx,edi"), (0x00626399, "sar", "edx,cl"),
    (0x0062639B, "jmp", "0x626658"), (0x0062665D, "call", "0x483360"),
    (0x00626790, "je", "0x62682a"), (0x0062679D, "cmp", "eax,0xd"), (0x006267A0, "ja", "0x626827"),
    (0x006267A6, "movzx", "0x62690c"), (0x006267AD, "jmp", "0x6268f4"),
]


def cmd_static():
    rep = Report("static")
    exe = S4.EXE
    for va, mn, sub in PINS:
        out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % va,
                              "--stop-address=0x%x" % (va + 16), exe], capture_output=True, text=True).stdout
        line = [ln for ln in out.splitlines() if ln.strip().startswith("%x:" % va)]
        rep.c["pins"] += 1
        txt = line[0].split(":", 1)[1].strip() if line else ""
        if not txt.startswith(mn) or sub not in txt:
            rep.bad("pin 0x%08X: %r, want %s %s" % (va, txt, mn, sub))
        else:
            rep.c["pins_ok"] += 1
            rep.notes.append("  0x%08X %s" % (va, txt))
    cls = E.img_bytes(0x0062690C, 14)
    jt = struct.unpack("<6I", E.img_bytes(TAKE_JT, 24))
    sej = struct.unpack("<13I", E.img_bytes(0x00626688, 52))
    rep.notes.append("  take class table 0x0062690C (op 0..13): " + cls.hex())
    rep.notes.append("  take jump table 0x006268F4: " + " ".join("%d:%08X" % kv for kv in enumerate(jt)))
    rep.notes.append("  StatEvaluate jump table 0x00626688 (op 1..13): " +
                     " ".join("%d:%08X" % (i + 1, t) for i, t in enumerate(sej)))
    if cls != TAKE_CLASS:
        rep.bad("class table")
    for lo, n, name in ((0x0062690C, 14, "class table"), (TAKE_JT, 24, "take jump table"),
                        (0x00626688, 52, "StatEvaluate jump table"), (MASK4, 8, "masks 0x006CE270/4"),
                        (0x00683840, 0x3C0, "memmove 0x00683840..0x00683C00")):
        sec = S4.section_of(lo)
        fl = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.c["ro"] += not fl & 0x80000000
        rep.notes.append("  %s 0x%08X in %s (writable %s)" % (name, lo, sec, bool(fl & 0x80000000)))
        if fl & 0x80000000:
            rep.bad("%s writable" % name)
    rep.notes.append("  mask 0x006CE270 = %d, 0x006CE274 = %d" % (S4.dword(MASK4), S4.dword(MASK_CB)))
    import stats as ST                       # the stock table (rule 2 for the data half of D1's "no row")
    rows = ST.load_txt(os.path.join(ROOT, "workspace", "merged", "data", "global", "excel"), "itemstatcost.txt")
    ops = collections.Counter(r.get("op", "") for r in rows if r.get("Stat") != "Expansion")
    rep.notes.append("  ItemStatCost.txt rows %d, op cells: %s" % (len(rows), " ".join(
        "%s:%d" % (k or "blank", v) for k, v in sorted(ops.items(), key=lambda kv: (len(kv[0]), kv[0])))))
    for op in ("3", "10", "12"):
        rep.c["isc_op%s_rows" % op] = ops.get(op, 0)
    rep.notes.append("  op 6/7 rows: " + " ".join("%s(%s)" % (r["Stat"], r["op"]) for r in rows
                                                 if r.get("op") in ("6", "7")))
    rep.c["neg"] = 1
    print(rep.line())
    for n in rep.notes:
        print("  " + n)
    return 1 if rep.c["bad"] else 0


def cmd_manifest(d, write):
    lines = []
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if os.path.isfile(p) and not name.startswith("manifest"):
            lines.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), name))
    txt = "\n".join(lines) + "\n"
    if write:
        open(os.path.join(d, "manifest.sha256"), "w").write(txt)
    sys.stdout.write(txt)
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["cases", "check", "static", "manifest"])
    ap.add_argument("--dir", default=DEFDIR)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "cases":
        cmd_cases(a.dir, a.limit)
        return 0
    if a.cmd == "check":
        return cmd_check(a.dir)
    if a.cmd == "static":
        return cmd_static()
    return cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

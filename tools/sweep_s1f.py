#!/usr/bin/env python3
"""Plan 0038 batch S1f: eight more functions of the pinned image run under Ghidra's p-code emulator (ADR-0015) with
re/ghidra_scripts/EmuTrace.java and compared bit for bit with the models below (no game run, no slot). The S1e
tooling is reused: tools/sweep_s1e.py's report, read-set accounting, CALC models and parsetxt world.

    python3 -I tools/sweep_s1f.py cases [FAMILY ...] [--dir D]   write D/<family>.cases, .mem, .json (expected inputs)
    tools/ghidra.sh emutrace D/<family>.cases D/<family>.mem > D/<family>.out        (or any EmuTrace runner)
    python3 -I tools/sweep_s1f.py check [FAMILY ...] [--dir D]   compare D/<family>.out with the models; account for
                                                                every traced access; run the negative controls
    python3 -I tools/sweep_s1f.py static                         objdump pins (ADR-0015 (5)), the call closures of
                                                                every family, the writer scan of declared .data reads
    python3 -I tools/sweep_s1f.py manifest [--write]             sha256 of every file under D
    python3 -I tools/sweep_s1f.py all [--dir D]                  check of every family, static, manifest

Families (the function each calls; the inventory rows it serves):
  validid    MONSTATS_ValidId 0x004E6C50                                    drlg-preset 6 (second statement)
  muldiv     sub_00483360_MulDiv (and the CRT 64-bit divide 0x00684240)     monsters-stats 9, 11
  candadd    sub_005C0D00_AffixCandAdd                                       items-affixes 6
  pickaffix  ITEMS_PickMagicAffix 0x005C1560 on synthetic affix blocks of 100-700 rows (applyProps 0)
                                                                             items-affixes 12 (and 6)
  calcvar2   SKILLS_CalcVar 0x00646460 codes 43-48 (MISS_GetElemMin/Max, MISS_EvalCalc, CALC_Eval, MulDiv)
                                                                             data-calc 33
  parsetxt2  EXCEL_ParseTxt 0x006BD780 with absent descriptor entries of every type and the item calc cell callback
             0x00631530 on calc columns (types 0x17, 0x18, 0x19)            data-calc 8; data-excel 65, 69
  varroll    sub_005BDB20_MonVariantRoll                                     monsters-pool 27
  setpick    ITEMS_BuildSetPick 0x005C25C0 (its success path runs ItemApplyProps mode 4 on property-less records)
                                                                             items-uniques-sets 44

Each check prints one `S1F <family> key=value ...` line: cases, matches, mismatches (`bad`), the negative control's
mismatch count (`neg`, must be above 0), the traced accesses outside the stack and the memory spec, each of which must
fall in the family's declared read set (`undeclared`, must be 0), `stopped` (cases that did not return: must be 0),
then the branches reached. The batch record is run:2026-10-17-sweep-emu2 in docs/findings/data/experiments.md and
the "Plan 0038 batch S1f" sections of the findings.

Stdlib only, plus objdump for `static`. Writes only under D (default workspace/logs/sweep-s1f/).
"""
import argparse
import collections
import hashlib
import json
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rng as RNG  # noqa: E402
import sweep_s1e as E  # noqa: E402
import sweep_s4b as S4  # noqa: E402

from sweep_s1e import M32, s32, s16, cdiv, le32, hx  # noqa: E402

ROOT = os.path.dirname(HERE)
DEFDIR = os.path.join(ROOT, "workspace", "logs", "sweep-s1f")

FN = {
    "MONSTATS_ValidId": 0x004E6C50, "MulDiv": 0x00483360, "alldiv": 0x00684240, "AffixCandAdd": 0x005C0D00,
    "ITEMS_PickMagicAffix": 0x005C1560, "SKILLS_CalcVar": 0x00646460, "MISS_GetElemMin": 0x0064B100,
    "MISS_GetElemMax": 0x0064B1D0, "EXCEL_ParseTxt": 0x006BD780, "ItemCalcCell": 0x00631530,
    "MonVariantRoll": 0x005BDB20, "ITEMS_BuildSetPick": 0x005C25C0,
}
G_PDATATABLES = E.G_PDATATABLES          # 0x00744304
GDT = E.G_DATATABLES                     # 0x0096BC30, g_DataTables (.data, no file bytes)
COOKIE = E.COOKIE
RS_COOKIE = E.RS_COOKIE
MASKS = 0x006CE268                       # u32 masks 1 << i, i = 0..31 (.rdata)

# scratch memory (outside the image)
DTS = 0x11000000         # a scratch DataTables (validid, calcvar2, varroll)
ARR = 0x11100100         # AffixCandAdd's array
SEEDP = 0x11200000       # a seed pair
ENTRY = 0x11200100       # a MonRegion entry
MS = 0x11300000          # monstats records (0x1A8)
M2 = 0x11380000          # monstats2 records (0x134)
UNIT = 0x11400000        # an item unit
IDATA = 0x11400100       # its item data
PARAMS = 0x11400400      # BuildSetPick's create parameters
ITREC = 0x11410000       # items records (0x1A8)
ITYP = 0x11420000        # itemtypes records (0xE4)
EQUIV = 0x11430000       # itemtypes equivalence bits
AFX = 0x11500000         # affix rows (0x90)
SETS = 0x11600000        # sets records (0x1B8)


def calls_of(d, fam, suffix=""):
    calls, reads, writes = E.read_out(os.path.join(d, fam + suffix + ".out"))
    meta = json.load(open(os.path.join(d, fam + ".json")))
    return calls, reads, writes, meta


class Report(E.Report):
    def line(self):
        keys = ["cases", "match", "bad", "neg", "traced", "undeclared", "stopped"]
        rest = sorted(k for k in self.c if k not in keys)
        return "S1F %s " % self.fam + " ".join("%s=%d" % (k, self.c[k]) for k in keys + rest)


def stopped(rep, c):
    if "stop" in c:
        rep.c["stopped"] += 1
        rep.bad("case %d stopped: %s" % (c["n"], c["stop"]))
        return True
    return False


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def fields(base, pairs):
    """One `dword` spec line per DataTables field the code reads, so a read of any other field is traced."""
    return ["dword %08x %08x" % (base + off, v & M32) for off, v in pairs]


FATAL = (0x00408090, 0x00408A60, 0x00681E09)      # the assert path: caller address, report, exit
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)      # the pool allocator's entries (each reads 0x00708000 first)
GUARDS = ["guard %08x" % a for a in FATAL + ALLOC]   # EmuTrace stops a case that reaches one (review condition (a))


# =============================================================================================== validid
def validid_model(i, n, neg=False):
    i, n = s32(i), s32(n)
    if neg:
        return i if 0 <= i <= n else -1
    return i if 0 <= i < n else -1


def validid_cases(rnd):
    cases, exp = [], []
    ns = [0, 1, 2, 733, 734, 0x7FFFFFFF, -1, -0x80000000]
    while len(exp) < 2000:
        n = rnd.choice(ns + [rnd.randrange(0, 2000)] * 4 + [rnd.getrandbits(32)])
        n = s32(n)
        i = rnd.choice([-1, 0, 1, n - 1, n, n + 1, -0x80000000, 0x7FFFFFFF, rnd.randrange(-5, 2000),
                        rnd.getrandbits(32), rnd.randrange(0, max(n, 1))])
        i = s32(i)
        cases += ["w %08x %s" % (DTS + 0xA80, hx(le32(n))), "call %08x %08x 0" % (FN["MONSTATS_ValidId"], i & M32)]
        exp.append([i, n])
    return cases, ["dword %08x %08x" % (G_PDATATABLES, DTS)], {"cases": exp}


def validid_check(d):
    calls, reads, writes, meta = calls_of(d, "validid")
    rep = Report("validid")
    neg = 0
    for c, (i, n) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        if stopped(rep, c):
            continue
        want = validid_model(i, n) & M32
        ok = c["eax"] == want and c["pop"] == 0
        rep.c["match"] += ok
        if not ok:
            rep.bad("case %d id=%d n=%d: got %08x want %08x" % (c["n"], i, n, c["eax"], want))
            continue
        neg += c["eax"] != validid_model(i, n, neg=True) & M32
        rep.branches["neg_id" if i < 0 else "in_range" if i < n else "id_ge_n"] += 1
        rep.branches["n_le0"] += n <= 0
    E.account(rep, reads, writes, [])
    return E.finish(rep, neg)


# =============================================================================================== muldiv
class Fault(Exception):
    pass


def muldiv_model(a, b, c, neg=False, br=None):
    """sub_00483360_MulDiv(a: ECX, b: EDX, c: stack) -> (eax, edx or None)."""
    a, b, c = s32(a), s32(b), s32(c)

    def tag(t):
        if br is not None:
            br[t] += 1
    if neg:                                    # the exact quotient everywhere: no truncation before multiplying
        if c == 0:
            return 0, None
        return cdiv(a * b, c) & M32, None
    if c == 0:
        tag("c0")
        return 0, None
    if a > 0x100000:
        if c <= a >> 4:
            tag("a_big_div_first")
            return s32(cdiv(a, c) * b) & M32, None
        tag("a_big_64")
        q = cdiv(a * b, c)
        tag("a_big_64_q_wide" if s32(q) != q else "a_big_64_q_fits")
        return q & M32, (q >> 32) & M32
    if b > 0x10000:
        if c <= b >> 4:
            tag("b_big_div_first")
            return s32(cdiv(b, c) * a) & M32, None
        tag("b_big_64")
        q = cdiv(a * b, c)
        tag("b_big_64_q_wide" if s32(q) != q else "b_big_64_q_fits")
        return q & M32, (q >> 32) & M32
    p = s32(a * b)
    if p == -0x80000000 and c == -1:
        raise Fault("idiv INT32_MIN / -1")
    tag("32bit_wrapped" if p != a * b else "32bit")
    return cdiv(p, c) & M32, None


def muldiv_cases(rnd):
    cases, exp = [], []
    edges = [0, 1, -1, 2, 100, 0x10000, 0x10001, 0x100000, 0x100001, 0x7FFFFFFF, -0x80000000, 0xFFFFF, 0x1FFFFF]
    while len(exp) < 4000:
        k = rnd.random()
        if k < 0.25:
            a = rnd.choice(edges + [rnd.randrange(0x100001, 0x7FFFFFFF)])
            b = rnd.choice(edges + [rnd.randrange(-0x10000, 0x10000), rnd.getrandbits(32)])
            c = rnd.choice([100, rnd.randrange(1, 0x100), (s32(a) >> 4), (s32(a) >> 4) + 1, rnd.getrandbits(32)])
        elif k < 0.5:
            a = rnd.choice(edges + [rnd.randrange(-0x100000, 0x100001)])
            b = rnd.choice([rnd.randrange(0x10001, 0x7FFFFFFF), 0x10001, 0x7FFFFFFF])
            c = rnd.choice([100, rnd.randrange(1, 0x100), (s32(b) >> 4), (s32(b) >> 4) + 1, -1, -100,
                            rnd.getrandbits(32)])
        elif k < 0.75:
            a = rnd.randrange(-0x80000000, 0x100001)
            b = rnd.randrange(-0x80000000, 0x10001)
            c = rnd.choice([100, 1, -1, 3, rnd.getrandbits(32), rnd.randrange(-1000, 1000)])
        else:
            a, b, c = rnd.getrandbits(32), rnd.getrandbits(32), rnd.choice([rnd.getrandbits(32), 0, 100])
        a, b, c = s32(a), s32(b), s32(c)
        try:
            muldiv_model(a, b, c)
        except Fault:
            continue
        cases.append("call %08x %08x %08x %08x" % (FN["MulDiv"], a & M32, b & M32, c & M32))
        exp.append([a, b, c])
    return cases, [], {"cases": exp}


def muldiv_check(d):
    calls, reads, writes, meta = calls_of(d, "muldiv")
    rep = Report("muldiv")
    neg = 0
    for c, (a, b, cc) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        if stopped(rep, c):
            continue
        br = collections.Counter()
        eax, edx = muldiv_model(a, b, cc, br=br)
        ok = c["eax"] == eax and c["pop"] == 4 and (edx is None or c["edx"] == edx)
        rep.c["match"] += ok
        if not ok:
            rep.bad("case %d a=%d b=%d c=%d: got %08x:%08x want %08x:%r" % (c["n"], a, b, cc, c["edx"], c["eax"],
                                                                          eax, edx))
            continue
        rep.branches.update(br)
        rep.branches["neg_c"] += cc < 0
        neg += c["eax"] != muldiv_model(a, b, cc, neg=True)[0]
    E.account(rep, reads, writes, [])
    return E.finish(rep, neg)


# =============================================================================================== candadd
CAND_CAP = 0x1FF


def candadd_model(win, base, n, rec, cid, neg=False):
    """win: bytes at `base`; returns (new n, new window)."""
    n = s32(n)
    out = bytearray(win)
    cap = 0x200 if neg else CAND_CAP
    if n >= cap:
        return n, bytes(out)
    a = (ARR + 8 * n) & M32
    for o, v in ((4, rec), (0, cid)):
        p = a + o - base
        if 0 <= p and p + 4 <= len(out):
            out[p:p + 4] = le32(v)
    return n + 1, bytes(out)


def candadd_cases(rnd):
    cases, exp = [], []
    ns = list(range(0x1F0, 0x210)) + [0, 1, -1, -4, 0x7FFFFFFF, -0x80000000, 0x60000000, 0x1000]
    while len(exp) < 3000:
        n = rnd.choice(ns + [rnd.randrange(0, 0x260)] * 6)
        rec, cid = rnd.getrandbits(32), rnd.getrandbits(32)
        a = (ARR + 8 * s32(n)) & M32
        base = (a - 16) & M32
        if not (ARR - 0x100 <= base and base + 48 <= ARR + 0x1100):
            base = ARR
        win = bytes(rnd.getrandbits(8) for _ in range(48))
        cases += ["s %08x %d" % (ARR - 0x100, 0x1200), "w %08x %s" % (base, hx(win)), "d %08x 48" % base,
                  "r EAX %08x" % (n & M32), "call %08x %08x %08x %08x" % (FN["AffixCandAdd"], ARR, rec, cid)]
        exp.append([n, rec, cid, base, win.hex()])
    return cases, [], {"cases": exp}


def candadd_check(d):
    calls, reads, writes, meta = calls_of(d, "candadd")
    rep = Report("candadd")
    neg = 0
    for c, (n, rec, cid, base, win) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        if stopped(rep, c):
            continue
        win = bytes.fromhex(win)
        nn, w2 = candadd_model(win, base, n, rec, cid)
        got = c["dumps"][0][1]
        ok = c["eax"] == nn & M32 and got == w2 and c["pop"] == 4
        rep.c["match"] += ok
        if not ok:
            rep.bad("case %d n=%d: got eax=%08x %s want %08x %s" % (c["n"], n, c["eax"], got.hex(), nn & M32,
                                                                   w2.hex()))
            continue
        nn2, w3 = candadd_model(win, base, n, rec, cid, neg=True)
        neg += (nn2 & M32) != c["eax"] or w3 != got
        rep.branches["stored" if s32(n) < CAND_CAP else "at_or_past_cap"] += 1
        rep.branches["n_eq_510"] += s32(n) == 0x1FE
        rep.branches["n_eq_511"] += s32(n) == 0x1FF
        rep.branches["n_negative"] += s32(n) < 0
    E.account(rep, reads, writes, [])
    return E.finish(rep, neg)


# =============================================================================================== pickaffix
AFF_STRUCT = GDT + 0xE4C       # 0x0096CA7C: {n, base, suffix start, prefix start, automagic start} (0x00633ED0)
ITEMS_N = GDT + 0xE28          # 0x0096CA58: items count, +4 the records (ITEMS_GetRecord 0x006335F0)


class AffixWorld:
    NT = 6                     # item types; every type is also type 1 (the equivalence bits), as "any" in stock data
    S, P, A = 1000, 1100, 120   # suffix, prefix, automagic rows: a block can hold more eligible rows than the cap

    def __init__(self, rnd=None):
        if rnd is None:
            return
        n = self.S + self.P + self.A
        self.rows = []
        groups = list(range(1, 40))
        for i in range(n):
            r = bytearray(rnd.getrandbits(8) for _ in range(0x90))
            struct.pack_into("<H", r, 0x22, rnd.choice([0, 1, 100, 101, 0x8000]))
            struct.pack_into("<i", r, 0x24, -1)
            r[0x54] = rnd.choice([0, 1, 1, 1, 1, 1])
            lv = rnd.choice([rnd.randrange(1, 100)] * 12 + [0, -3, 120])
            if rnd.random() < 0.002:
                lv = rnd.randrange(-0x80000000, 0x80000000)
            struct.pack_into("<i", r, 0x58, lv)
            struct.pack_into("<i", r, 0x5C, rnd.choice(groups))
            struct.pack_into("<i", r, 0x60, rnd.choice([0] * 12 + [rnd.randrange(1, 100), -1]))
            r[0x64] = rnd.choice([0, 1, 1, 1])
            r[0x66] = rnd.choice([0xFF] * 12 + [rnd.randrange(0, 9)])
            types = [rnd.choice([1] * 60 + [2, 3, 4, 5, 0, -1, 6, 0x7FFF])]
            types += [rnd.choice([0, 0, 1, 2, 3, 4, 5]) for _ in range(6)]
            for k, t in enumerate(types):
                struct.pack_into("<h", r, 0x6A + 2 * k, t if k == 0 or rnd.random() < 0.3 else 0)
            for k in range(5):
                struct.pack_into("<h", r, 0x78 + 2 * k, rnd.choice([0] * 30 + [2, 3, -1]) if k == 0 or
                                 rnd.random() < 0.2 else 0)
            r[0x82] = rnd.choice([0] + [rnd.randrange(1, 256)] * 20)
            self.rows.append(bytes(r))
        self.types = [bytearray(rnd.getrandbits(8) for _ in range(0xE4)) for _ in range(self.NT)]
        for t in self.types:
            t[0x21] = rnd.randrange(0, 10)
        self.equiv = [(1 << t) | 2 | rnd.getrandbits(self.NT) for t in range(self.NT)]
        self.types = [bytes(t) for t in self.types]

    def meta(self):
        return {"rows": [r.hex() for r in self.rows], "types": [t.hex() for t in self.types], "equiv": self.equiv}

    @classmethod
    def from_meta(cls, m):
        w = cls()
        w.rows = [bytes.fromhex(x) for x in m["rows"]]
        w.types = [bytes.fromhex(x) for x in m["types"]]
        w.equiv = m["equiv"]
        return w

    def blocks(self):
        sfx = AFX
        pfx = AFX + 0x90 * self.S
        aut = pfx + 0x90 * self.P
        return [len(self.rows), AFX, sfx, pfx, aut]

    def mem(self):
        dt = fields(GDT, [(0xBF8, ITYP), (0xBFC, self.NT), (0xC00, 1), (0xC04, EQUIV), (0xE28, 1), (0xE2C, ITREC)] +
                    [(0xE4C + 4 * k, v) for k, v in enumerate(self.blocks())])
        return ["dword %08x %08x" % (G_PDATATABLES, GDT)] + dt + [
                "bytes %08x %s" % (ITYP, hx(b"".join(self.types))),
                "bytes %08x %s" % (EQUIV, hx(b"".join(le32(v) for v in self.equiv))),
                "const bytes %08x %s" % (AFX, hx(b"".join(self.rows)))]

    # ------------------------------------------------------------------ the item helpers
    def is_type(self, it, t):
        t = s16(t)
        if t < 0 or t >= self.NT:
            return False
        T = s16(u32(it["rec"], 0x11E))
        if self.equiv[T] & (1 << (t & 31)):
            return True
        T2 = s16(u32(it["rec"], 0x120))
        if T2 <= 0 or T2 >= self.NT:
            return False
        return bool(self.equiv[T2] & (1 << (t & 31)))

    def type_ok(self, it, r):
        for k in range(5):
            e = s16(struct.unpack_from("<H", r, 0x78 + 2 * k)[0])
            if e <= 0:
                break
            if self.is_type(it, e):
                return False
        for k in range(7):
            t = s16(struct.unpack_from("<H", r, 0x6A + 2 * k)[0])
            if t <= 0:
                return False
            if self.is_type(it, t):
                return True
        return False

    def type_class(self, it):
        T = s16(u32(it["rec"], 0x11E))
        if T < 0 or T >= self.NT:
            return 7
        c = self.types[T][0x21]
        return c if c < 7 else 7

    def by_id(self, i):
        if i > len(self.rows) or i <= 0:
            return None
        return self.rows[i - 1]

    def group_taken(self, it, g):
        for lst in (it["pfx"], it["sfx"]):
            for i in lst:
                a = self.by_id(i)
                if a is None:
                    break
                if u32(a, 0x5C) == g & M32:
                    return True
        return False

    def pick(self, it, a, neg=False, br=None):
        """ITEMS_PickMagicAffix(item, needSpawnable, mustRoll, applyProps 0, isPrefix, forced 0, autoGroup) ->
        (ax, seed lo, seed hi, item data after)."""
        def tag(t):
            if br is not None:
                br[t] += 1
        n_all, base, sfx, pfx, aut = self.blocks()
        lo, hi = it["seed"]
        if a["auto"]:
            start, end = aut, (base + 0x90 * n_all) & M32
        elif a["prefix"]:
            start, end = pfx, aut
        else:
            start, end = sfx, pfx
        count = cdiv(s32(end - start), 0x90)
        data = it
        if start == 0:
            return 0, lo, hi, data["ilvl"]
        block0 = cdiv(s32(start - base), 0x90)
        lo, hi = RNG.step(lo, hi)
        qlvl = it["rec"][0xFD]
        if not (lo & 1) and not a["must"]:
            tag("no_roll")
            return 0, lo, hi, data["ilvl"]
        ilvl = s32(data["ilvl"])
        ilvl_after = ilvl if ilvl >= 1 else 1
        ilvl = ilvl_after
        if ilvl <= qlvl:
            ilvl = qlvl
        m = it["rec"][0x140]
        if m:
            alvl = ilvl + m
        else:
            h = cdiv(qlvl, 2)
            alvl = ilvl - h if ilvl < 99 - h else 2 * ilvl - h - (99 - h)
        if alvl <= 1:
            alvl = 1
        elif alvl >= 99:
            alvl = 99
        if count <= 0:
            return 0, lo, hi, ilvl_after
        cands, W, n, eligible = [], 0, 0, 0
        for row in range(count):
            r = self.rows[block0 + row]
            if a["spawn"] and r[0x54] == 0:
                continue
            if struct.unpack_from("<H", r, 0x22)[0] >= 100 and it["ver"] < 100:
                continue
            if s32(u32(r, 0x58)) > alvl:
                continue
            mx = s32(u32(r, 0x60))
            if mx != 0 and mx < alvl:
                continue
            if r[0x64] == 0:
                q = it["quality"]
                if q == 6 or ((q - 8) & M32) <= 1:
                    continue
            if not self.type_ok(it, r):
                continue
            if a["auto"] and (a["auto"] & M32) != u32(r, 0x5C):
                continue
            if r[0x82] == 0:
                continue
            if r[0x66] != 0xFF:
                tc = self.type_class(it)
                if tc != 7 and r[0x66] != tc:
                    continue
            if self.group_taken(it, u32(r, 0x5C)):
                continue
            w = s32(r[0x82] * s32(u32(r, 0x58))) if m else r[0x82]
            eligible += 1
            if n < CAND_CAP:
                cands.append((block0 + row, w))
                n += 1
                W = s32(W + w)
            elif not neg:
                W = s32(W + w)
        tag("eligible_gt_511" if eligible > CAND_CAP else "eligible_le_511")
        if n <= 0:
            tag("no_candidate")
            return 0, lo, hi, ilvl_after
        if s32(W + 1) <= 0:
            x = 0
            tag("range_nodraw")
        else:
            lo, hi = RNG.step(lo, hi)
            x = lo % s32(W + 1)
        stored = sum(w for _, w in cands)
        if eligible > CAND_CAP:
            tag("x_beyond_stored" if x >= stored else "x_within_stored")
        for k, (i, w) in enumerate(cands):
            x = s32(x - w)
            if x < 0:
                tag("picked_last" if k == n - 1 else "picked")
                return (i + 1) & 0xFFFF, lo, hi, ilvl_after
        tag("fell_through_last")
        return (cands[-1][0] + 1) & 0xFFFF, lo, hi, ilvl_after


def pick_item(rnd, w):
    rec = bytearray(rnd.getrandbits(8) for _ in range(0x1A8))
    rec[0xFD] = rnd.choice([0, 1, 5, 30, 60, 85, 99, rnd.randrange(0, 256)])
    struct.pack_into("<h", rec, 0x11E, rnd.randrange(0, w.NT))
    struct.pack_into("<h", rec, 0x120, rnd.choice([0, 0, 0, rnd.randrange(1, w.NT), -1, 0x7FFF]))
    rec[0x137] = 0
    rec[0x140] = rnd.choice([0, 0, 0, rnd.randrange(1, 30), rnd.randrange(0, 256)])
    pfx = [rnd.choice([0] * 4 + [rnd.randrange(1, len(w.rows) + 3)]) for _ in range(3)]
    sfx = [rnd.choice([0] * 4 + [rnd.randrange(1, len(w.rows) + 3)]) for _ in range(3)]
    return {"rec": rec.hex(), "ilvl": rnd.choice([rnd.randrange(1, 100)] * 4 + [rnd.randrange(80, 100)] * 4 +
                                                 [0, -5, 99, 120]),
            "quality": rnd.choice([4, 4, 4, 4, 4, 6, 8, 9, 2, 5, 7]), "ver": 101, "pfx": pfx, "sfx": sfx,
            "seed": [rnd.getrandbits(32), rnd.getrandbits(32)]}


def item_bytes(it):
    unit = le32(4) + le32(0) + le32(0) + le32(0) + le32(0) + le32(IDATA) + bytes(0x18)
    data = bytearray(0x50)
    struct.pack_into("<III", data, 0, it["quality"] & M32, it["seed"][0], it["seed"][1])
    struct.pack_into("<i", data, 0x2C, it["ilvl"])
    struct.pack_into("<H", data, 0x30, it["ver"])
    struct.pack_into("<3H", data, 0x38, *it["pfx"])
    struct.pack_into("<3H", data, 0x3E, *it["sfx"])
    return unit, bytes(data)


def pickaffix_cases(rnd):
    w = AffixWorld(rnd)
    cases, exp = [], []
    while len(exp) < 500:
        it = pick_item(rnd, w)
        a = {"spawn": rnd.choice([0, 0, 1]), "must": rnd.choice([1, 1, 1, 0]), "prefix": rnd.choice([0, 1]),
             "auto": rnd.choice([0] * 6 + [rnd.randrange(1, 40)])}
        unit, data = item_bytes(it)
        cases += ["w %08x %s" % (UNIT, hx(unit)), "w %08x %s" % (IDATA, hx(data)),
                  "w %08x %s" % (ITREC, it["rec"]), "d %08x %d" % (IDATA, 0x50),
                  "call %08x 0 0 %08x %x %x 0 %x 0 %x" % (FN["ITEMS_PickMagicAffix"], UNIT, a["spawn"], a["must"],
                                                         a["prefix"], a["auto"])]
        exp.append([it, a])
    return cases, w.mem(), {"cases": exp, "world": w.meta()}


def pickaffix_check(d):
    calls, reads, writes, meta = calls_of(d, "pickaffix")
    rep = Report("pickaffix")
    w = AffixWorld.from_meta(meta["world"])
    neg = 0
    for c, (it, a) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        if stopped(rep, c):
            continue
        it = dict(it)
        it["rec"] = bytes.fromhex(it["rec"])
        br = collections.Counter()
        ax, lo, hi, ilvl = w.pick(it, a, br=br)
        data = c["dumps"][0][1]
        got = (c["eax"] & 0xFFFF, u32(data, 4), u32(data, 8), s32(u32(data, 0x2C)))
        ok = got == (ax, lo, hi, ilvl) and c["pop"] == 28
        rep.c["match"] += ok
        if not ok:
            rep.bad("case %d: got %r want %r" % (c["n"], got, (ax, lo, hi, ilvl)))
            continue
        rep.branches.update(br)
        if a["auto"]:
            rep.branches["autogroup"] += 1
        if it["rec"][0x140]:
            rep.branches["weight_freq_x_level"] += 1
        neg += w.pick(it, a, neg=True)[0] != ax
    declared = [(MASKS, MASKS + 0x80, "r", "bit masks 0x006CE268 (.rdata)")]
    E.account(rep, reads, writes, declared)
    return E.finish(rep, neg)


# =============================================================================================== calcvar2
MISSPOOL = 0x11280000


class ElemWorld(E.CalcVarWorld):
    """CalcVarWorld (skills, skilldesc, missiles records) with the missile fields MISS_GetElemMin/Max read set by
    hand, and a misscode pool of constant-only formulas (CALC_Eval never calls a function or the variable reader)."""

    def __init__(self, rnd=None):
        super().__init__(rnd)
        if rnd is None:
            return
        progs, pool = [], bytearray()
        for _ in range(40):
            progs.append(len(pool))
            out = bytearray()
            for i in range(rnd.randrange(1, 4)):
                if rnd.random() < 0.6:
                    out += bytes([7, rnd.getrandbits(8)])
                else:
                    out += bytes([9]) + le32(rnd.choice([rnd.randrange(-300, 300), rnd.getrandbits(32), 100, 0]))
                if i:
                    out.append(rnd.choice([0x10, 0x11, 0x12]))
            out.append(0)
            pool += out
        self.mpool = bytes(pool)
        for r in self.mi:
            for o in (0xE8, 0xEC):
                struct.pack_into("<i", r, o, rnd.choice([rnd.randrange(-50, 400), rnd.randrange(-0x80000000,
                                                                                               0x80000000)]))
            for o in range(0xF0, 0x118, 4):
                struct.pack_into("<I", r, o, rnd.choice([rnd.randrange(-20, 60)] * 4 + [rnd.getrandbits(32)]) & M32)
            struct.pack_into("<I", r, 0x118, rnd.choice([M32] * 3 + [rnd.choice(progs)] * 4 +
                                                       [len(self.mpool), 0x80000000]))
            r[0x196] = rnd.choice([0, 0, 8, 3, 31, 32, 40, rnd.getrandbits(8)])
        struct.pack_into("<I", self.mi[0], 0x118, len(self.mpool))          # offset = size: no evaluation
        struct.pack_into("<I", self.mi[1], 0x118, 0x80000000)              # unsigned compare
        # distinct description missiles, so each index reads a different record
        for r in self.sd:
            ms = rnd.sample(range(self.NMI), 3)
            for k in range(3):
                struct.pack_into("<h", r, 0x3C + 2 * k, rnd.choice([ms[k]] * 8 + [-1, self.NMI]))

    def meta(self):
        m = super().meta()
        m["mpool"] = self.mpool.hex()
        return m

    @classmethod
    def from_meta(cls, m):
        w = cls()
        w.sk = [bytes.fromhex(x) for x in m["sk"]]
        w.sd = [bytes.fromhex(x) for x in m["sd"]]
        w.mi = [bytes.fromhex(x) for x in m["mi"]]
        w.pool = bytes.fromhex(m["pool"])
        w.mpool = bytes.fromhex(m["mpool"])
        return w

    def mem(self):
        out = super().mem()
        dt = fields(E.DT, [(0x60, MISSPOOL), (0x64, len(self.mpool)), (0xB98, E.SKREC), (0xBA0, self.NSK),
                           (0xB8C, E.SDREC), (0xB94, self.NSD), (0xB64, E.MIREC), (0xB6C, self.NMI)])
        return [out[0]] + dt + out[2:5] + ["bytes %08x %s" % (MISSPOOL, hx(self.mpool))]

    @staticmethod
    def bands(lvl, b):
        if lvl <= 1:
            return 0
        if lvl <= 8:
            return s32((lvl - 1) * b[0])
        if lvl <= 16:
            return s32((lvl - 8) * b[1] + 7 * b[0])
        if lvl <= 22:
            return s32((lvl - 16) * b[2] + 8 * b[1] + 7 * b[0])
        if lvl <= 28:
            return s32((lvl - 22) * b[3] + 6 * b[2] + 8 * b[1] + 7 * b[0])
        return s32((lvl - 28) * b[4] + 6 * (b[3] + b[2]) + 8 * b[1] + 7 * b[0])

    def elem(self, m, lvl, mx, br=None):
        """MISS_GetElemMin/Max(NULL, unit, m, lvl) for lvl >= 1."""
        r = self.mi[m]
        b = [s32(u32(r, (0x104 if mx else 0xF0) + 4 * k)) for k in range(5)]
        x = s32(self.bands(lvl, b) + s32(u32(r, 0xEC if mx else 0xE8)))
        off = u32(r, 0x118)
        if off != M32:
            if off < len(self.mpool):
                env = E.EvalEnv(None, [], 0, 0)
                v = E.eval_model(self.mpool[off:] + bytes(8), len(self.mpool) - off, env)
                if br is not None:
                    br["calc_eval"] += 1
            else:
                v = 0
                if br is not None:
                    br["calc_off_ge_size"] += 1
            if v:
                x = s32(x + s32(muldiv_model(x, v, 100, br=br)[0]))
        else:
            if br is not None:
                br["calc_none"] += 1
        return s32(x << (r[0x196] & 31))

    def calcvar43(self, code, skill, lvl, neg=False, br=None):
        skill, lvl = s32(skill), s32(lvl)
        if skill < 0 or skill >= self.NSK:
            return 0
        if lvl <= 0:
            if br is not None:
                br["lvl_le0"] += 1
            return 0
        mx = code in (44, 46, 48)
        idx = cdiv(code - (44 if mx else 43), 3) if not neg else cdiv(code - 43, 3)
        sdi = s16(struct.unpack_from("<H", self.sk[skill], 0x194)[0])
        if not (0 <= sdi < self.NSD):
            if br is not None:
                br["no_skilldesc"] += 1
            return 0
        m = s16(struct.unpack_from("<H", self.sd[sdi], 0x3C + 2 * idx)[0])
        if not (0 <= m < self.NMI):
            if br is not None:
                br["no_missile"] += 1
            return 0
        if br is not None:
            br["code%d_missile%d" % (code, idx)] += 1
        return self.elem(m, lvl, mx, br)


def calcvar2_cases(rnd):
    w = ElemWorld(random.Random(1743))
    cases, exp = [], []
    lvls = [0, 1, 2, 8, 9, 16, 17, 22, 23, 28, 29, 40, 99, -1, 0x7FFFFFFF, 1000]
    while len(exp) < 3000:
        code = rnd.randrange(43, 49)
        skill = rnd.choice([rnd.randrange(0, w.NSK)] * 10 + [-1, w.NSK])
        lvl = rnd.choice(lvls + [rnd.randrange(1, 60)] * 6)
        try:
            w.calcvar43(code, skill, lvl)
        except (E.PowLimit, Fault):
            continue
        hi = rnd.choice([0, 0, rnd.getrandbits(24) << 8])
        cases.append("call %08x 0 0 0 %08x %08x %08x" % (FN["SKILLS_CalcVar"], (code | hi) & M32, skill & M32,
                                                         lvl & M32))
        exp.append([code, skill, lvl])
    return cases, w.mem(), {"cases": exp, "w": w.meta()}


def calcvar2_check(d):
    calls, reads, writes, meta = calls_of(d, "calcvar2")
    rep = Report("calcvar2")
    w = ElemWorld.from_meta(meta["w"])
    neg = 0
    for c, (code, skill, lvl) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        if stopped(rep, c):
            continue
        br = collections.Counter()
        want = w.calcvar43(code, skill, lvl, br=br) & M32
        ok = c["eax"] == want and c["pop"] == 16
        rep.c["match"] += ok
        if not ok:
            rep.bad("case %d code=%d skill=%d lvl=%d: got %08x want %08x" % (c["n"], code, skill, lvl, c["eax"], want))
            continue
        rep.branches.update(br)
        neg += (w.calcvar43(code, skill, lvl, neg=True) & M32) != c["eax"]
    declared = [E.RS_CALC_JT, (E.T_MISS, E.T_MISS + 0x20, "r", "g_MissCalcFuncs 0x00745828"),
                (E.N_MISS, E.N_MISS + 4, "r", "g_nMissCalcFuncs 0x00745848"),
                (0x00646ABC, 0x00646ABC + 4 * 0x49, "r", "SKILLS_CalcVar jump table 0x00646ABC (.text)"), RS_COOKIE]
    E.account(rep, reads, writes, declared)
    return E.finish(rep, neg)


# =============================================================================================== parsetxt2
# descriptor: (name, type, len, offset, link kind); link kinds: None, "code", "name", "calc"
CALC_CB = FN["ItemCalcCell"]
PT2_RECSIZE = 0xA0
PT2_PRESENT = [  # entries that may have a .txt column
    (b"IntD", 2, 4, 0x00), (b"IntW", 3, 2, 0x04), (b"IntB", 4, 1, 0x06), (b"IntB5", 5, 1, 0x07),
    (b"IntD8", 8, 4, 0x08), (b"Flag", 0x1A, 3, 0x0C), (b"CodeD", 0x0B, 4, 0x10), (b"CodeB", 0x0D, 1, 0x14),
    (b"CodeW", 0x0F, 2, 0x16), (b"NameD", 0x13, 4, 0x18), (b"NameW", 0x14, 2, 0x1C), (b"NameB", 0x15, 1, 0x1E),
    (b"calc1", 0x19, 0, 0x20), (b"calc2", 0x19, 0, 0x24), (b"calc3", 0x19, 0, 0x28), (b"cb17", 0x17, 0, 0x2C),
    (b"cb18", 0x18, 0, 0x30),
]
PT2_ABSENT_ONLY = [  # types the parse pass would register or convert through links the run does not build
    (b"Str1", 1, 7, 0x34), (b"Str7", 7, 5, 0x3C), (b"Code9", 9, 4, 0x44), (b"RegA", 0x0A, 0, 0x48),
    (b"RegC", 0x0C, 0, 0x4C), (b"RegE", 0x0E, 0, 0x4E), (b"Reg10", 0x10, 0, 0x50), (b"Reg11", 0x11, 0, 0x52),
    (b"Reg12", 0x12, 0, 0x54), (b"Key16", 0x16, 0, 0x58), (b"Flag2", 0x1A, 13, 0x0C),
    # overlapping groups: the last writer wins, so the record shows which ran last
    (b"OvA_int", 2, 4, 0x60), (b"OvA_dw13", 0x13, 4, 0x60), (b"OvA_calc", 0x19, 0, 0x60),
    (b"OvB_calc", 0x19, 0, 0x64), (b"OvB_int", 2, 4, 0x64),
    (b"OvC_b15", 0x15, 1, 0x68), (b"OvC_b5", 5, 1, 0x68), (b"OvC_cb17", 0x17, 0, 0x68),
    (b"OvD_w14", 0x14, 2, 0x6C), (b"OvD_w3", 3, 2, 0x6C), (b"OvD_dw0B", 0x0B, 4, 0x6C),
]
# a present column and an absent entry on the same field: the absent default must land after the cell
PT2_OVER_PRESENT = [(b"OvP_int", 2, 4, 0x70), (b"OvP_calcabs", 0x19, 0, 0x70), (b"OvQ_calc", 0x19, 0, 0x74),
                    (b"OvQ_dw13abs", 0x13, 4, 0x74), (b"OvR_calc", 0x19, 0, 0x78), (b"OvR_intabs", 2, 4, 0x78)]
PT2_UNKNOWN = [b"Unknown1", b"HratliMagicLvl"]
TEXTS_OK = ["1", "lvl", "lvl*3+1", "min(lvl,5)", "stat('strength'.base)", "rand(1,5)", "2^3", "(lvl+2)*7",
            "max(1,2)", "lvl ? 2 : 3", "-37", "100*lvl/3"]
TEXTS_BAD = ["", " ", "(1+2", "nosuch(1,2)", "1+", "?"]


def pt2_desc_list():
    return PT2_PRESENT + PT2_ABSENT_ONLY + PT2_OVER_PRESENT


def pt2_default(rec, typ, ln, off, calls):
    """The defaults pass for one absent entry (jump table 0x006BE128)."""
    if typ in (1, 4, 5, 6, 7, 0x0C, 0x10):
        rec[off] = 0
    elif typ in (2, 8, 9, 0x0A, 0x12):
        rec[off:off + 4] = bytes(4)
    elif typ in (3, 0x0E, 0x11, 0x16):
        rec[off:off + 2] = bytes(2)
    elif typ in (0x0B, 0x13):
        rec[off:off + 4] = b"\xff" * 4
    elif typ in (0x0D, 0x15):
        rec[off] = 0xFF
    elif typ in (0x0F, 0x14):
        rec[off:off + 2] = b"\xff\xff"
    elif typ in (0x17, 0x18, 0x19):
        rec[off:off + 4] = le32(M32)          # the item calc cell callback with ECX = NULL
        calls.append(("absent", off))


def pt2_model(cols, rows, pre, pool0, neg=False):
    """-> (records, pool). cols: descriptor indices in .txt order (-1, -2: unknown headers). neg: True runs the
    absent entries first, "desc" walks the present cells in descriptor order (the two orders data-calc 8 and
    data-excel 69 rule out)."""
    desc = pt2_desc_list()
    arr, nodes, root = E.pt_world()
    recs = bytearray(pre)
    pool = bytearray(pool0)
    present = set(c for c in cols if c >= 0)
    absent = [i for i in range(len(desc)) if i not in present]
    for r, row in enumerate(rows):
        rec = recs[PT2_RECSIZE * r:PT2_RECSIZE * (r + 1)]
        calls = []

        def run_absent():
            for i in absent:
                nm, typ, ln, off = desc[i]
                pt2_default(rec, typ, ln, off, calls)
        if neg is True:
            run_absent()
        order = list(zip(cols, row))
        if neg == "desc":
            order.sort(key=lambda x: x[0])
        for ci, cell in order:
            if ci < 0:
                continue
            nm, typ, ln, off = desc[ci]
            cell = bytes.fromhex(cell)
            if typ in (0x17, 0x18, 0x19):
                t = cell[:256].decode("latin-1")
                want = E.compile_model(t)
                if not want:
                    rec[off:off + 4] = le32(M32)
                else:
                    rec[off:off + 4] = le32(len(pool))
                    pool += want
                calls.append(("cell", off))
            else:
                E.pt_cell_model(rec, (nm, typ, ln, off), cell, arr, nodes, root)
        if neg is not True:
            run_absent()
        recs[PT2_RECSIZE * r:PT2_RECSIZE * (r + 1)] = rec
    return bytes(recs), bytes(pool)


PT2_LINK = 0x10760000     # LINKPTRS of sweep_s1e: {code link, name link}


def parsetxt2_cases(rnd):
    desc = pt2_desc_list()
    arr, nodes, root = E.pt_world()
    names_raw = bytearray()
    name_ptr = []
    for nm, *_ in desc:
        name_ptr.append(E.DESCNAMES + len(names_raw))
        names_raw += nm + b"\0"
    d = bytearray()
    for (nm, typ, ln, off), np_ in zip(desc, name_ptr):
        link = 0
        if typ in (0x0B, 0x0D, 0x0F):
            link = E.LINKPTRS
        elif typ in (0x13, 0x14, 0x15):
            link = E.LINKPTRS + 4
        elif typ in (0x17, 0x18, 0x19):
            link = CALC_CB
        d += le32(np_) + le32(typ) + le32(ln) + le32(off) + le32(link)
    d += bytes(20)
    nraw = bytearray(0x30 * len(E.PT_NAMES))
    for i, nd in nodes.items():
        nb = bytearray(0x30)
        nb[:len(nd["name"])] = nd["name"]
        struct.pack_into("<III", nb, 0x20, nd["index"], 0 if nd["left"] is None else E.NLINKNODES + 0x30 * nd["left"],
                         0 if nd["right"] is None else E.NLINKNODES + 0x30 * nd["right"])
        nraw[0x30 * i:0x30 * i + 0x30] = nb
    mem = ["dword %08x %08x" % (COOKIE, 0x51F0C0DE), "dword %08x 0" % E.LOCALE_CHANGED,
           "bytes %08x %s" % (E.DESCNAMES, hx(names_raw)), "bytes %08x %s" % (E.DESC, hx(d)),
           "bytes %08x %s" % (E.CLINK, hx(le32(len(arr)) + le32(len(arr)) + le32(E.CLINKARR) + le32(0))),
           "bytes %08x %s" % (E.CLINKARR, hx(b"".join(le32(c) + le32(i) for c, i in arr))),
           "bytes %08x %s" % (E.NLINK, hx(le32(len(E.PT_NAMES)) + le32(0) + le32(0) +
                                          le32(E.NLINKNODES + 0x30 * root))),
           "bytes %08x %s" % (E.NLINKNODES, hx(nraw)),
           "bytes %08x %s" % (E.LINKPTRS, hx(le32(E.CLINK) + le32(E.NLINK)))] + E.stat_tree_mem()
    cases, exp = [], []
    npres = len(PT2_PRESENT)
    over = len(PT2_PRESENT) + len(PT2_ABSENT_ONLY)
    for k in range(300):
        cols = [i for i in range(npres) if rnd.random() < 0.6]
        # the overlap rows: the present half of each pair is always a column
        cols += [over, over + 2, over + 4]
        cols += [-1 - j for j in range(len(PT2_UNKNOWN)) if rnd.random() < 0.5]
        rnd.shuffle(cols)
        nrows = rnd.randrange(1, 4)
        rows = []
        for _ in range(nrows):
            row = []
            for ci in cols:
                typ = desc[ci][1] if ci >= 0 else 2
                if typ in (0x17, 0x18, 0x19):
                    t = rnd.choice(TEXTS_OK * 3 + TEXTS_BAD + [E.rand_expr(rnd)[:150]])
                    row.append(t.encode("latin-1"))
                else:
                    row.append(E.pt_rand_cell(rnd, typ))
            rows.append(row)
        hdr = b"".join((desc[c][0] if c >= 0 else PT2_UNKNOWN[-1 - c]) + b"\0" for c in cols)
        cells = b"".join(b"".join(cell + b"\0" for cell in row) + b"\n" for row in rows)
        pre = bytes(rnd.getrandbits(8) for _ in range(PT2_RECSIZE * nrows))
        pool0 = bytes(rnd.getrandbits(8) for _ in range(rnd.randrange(0, 40)))
        cases += ["w %08x %s" % (E.TXT, hx(le32(E.TXTHDR) + le32(E.TXTCELLS) + le32(nrows) + le32(len(cols)))),
                  "w %08x %s" % (E.TXTHDR, hx(hdr)), "w %08x %s" % (E.TXTCELLS, hx(cells)),
                  "s %08x %d" % (E.TXTCELLS, len(cells) + 8),
                  "w %08x %s" % (E.G_DATATABLES + 0x98, hx(le32(E.ITEMPOOL) + le32(len(pool0)) + le32(0x10000))),
                  "s %08x %d" % (E.ITEMPOOL, 0x10000)] + (["w %08x %s" % (E.ITEMPOOL, hx(pool0))] if pool0 else []) + [
                  "w %08x %s" % (E.RECS, hx(pre)), "d %08x %d" % (E.RECS, PT2_RECSIZE * nrows),
                  "d %08x 12" % (E.G_DATATABLES + 0x98), "d %08x %d" % (E.ITEMPOOL, len(pool0) + 0x2000),
                  "call %08x 0 0 %08x %08x %08x %08x %08x" % (FN["EXCEL_ParseTxt"], E.TXT, E.DESC, E.RECS, 1,
                                                              PT2_RECSIZE)]
        exp.append([cols, [[c.hex() for c in row] for row in rows], pre.hex(), pool0.hex()])
    return cases, mem, {"cases": exp}


def parsetxt2_check(d, suffix=""):
    calls, reads, writes, meta = calls_of(d, "parsetxt2", suffix)
    rep = Report("parsetxt2" + suffix)
    desc = pt2_desc_list()
    neg = 0
    for c, (cols, rows, pre, pool0) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        if stopped(rep, c):
            continue
        pre, pool0 = bytes.fromhex(pre), bytes.fromhex(pool0)
        recs, pool = pt2_model(cols, rows, pre, pool0)
        got_recs, hdr, got_pool = (x[1] for x in c["dumps"])
        ok = (got_recs == recs and struct.unpack("<III", hdr) == (E.ITEMPOOL, len(pool), 0x10000) and
              got_pool[:len(pool)] == pool and c["pop"] == 20)
        rep.c["match"] += ok
        if not ok:
            rep.bad("case %d: recs %s / %s; hdr %s; pool %s / %s" % (c["n"], got_recs.hex(), recs.hex(), hdr.hex(),
                                                                     got_pool[:len(pool)].hex(), pool.hex()))
            continue
        nrecs, npool = pt2_model(cols, rows, pre, pool0, neg=True)
        neg += nrecs != got_recs or npool != got_pool[:len(npool)]
        drecs, dpool = pt2_model(cols, rows, pre, pool0, neg="desc")
        rep.c["neg_desc_order"] += drecs != got_recs or dpool != got_pool[:len(dpool)]
        present = set(x for x in cols if x >= 0)
        for i, (nm, typ, ln, off) in enumerate(desc):
            if i not in present:
                rep.branches["absent_type_%02X" % typ] += 1
        ncalc = sum(1 for x in cols if x >= 0 and desc[x][1] in (0x17, 0x18, 0x19))
        appended = len(pool) - len(pool0)
        rep.branches["rows"] += len(rows)
        rep.branches["calc_columns_present"] += ncalc * len(rows)
        if appended:
            rep.branches["pool_appends_rows"] += 1
        if sum(1 for x in cols if x >= 0 and desc[x][1] in (0x17, 0x18, 0x19)) >= 2:
            rep.branches["two_or_more_calc_columns"] += 1
        rep.branches["unknown_header"] += any(x < 0 for x in cols)
    declared = [RS_COOKIE, E.RS_CALC_JT,
                (0x006BE080, 0x006BE140, "r", "EXCEL_ParseTxt jump tables and index bytes 0x006BE088..0x006BE13F (.text)"),
                (0x006CE270, 0x006CE300, "r", "BITFIELD_Set/Clear bit-mask tables 0x006CE274..0x006CE2FF (.rdata)"),
                (0x006CEE30, 0x006CEE30 + 0x40, "r", "the name-hash table 0x006CEE30 (.rdata)"),
                (E.LOWER - 128, E.LOWER + 128, "r", "STR_ToLowerN table (.rdata)"),
                (0x0074AB98, 0x0074AB9C, "r", "_pctype pointer 0x0074AB98 (.data)"),
                (0x006F9280, 0x006F9280 + 0x200, "r", "the ctype table (.rdata)"),
                (0x006C1754, 0x006C1754 + 4 * 0x40, "r", "CALC_NextToken operator jump table (.text)"),
                (0x006C186C, 0x006C186C + 4 * 0x16, "r", "CALC_OpArity jump table (.text)"),
                (0x006C1F0C, 0x006C1F0C + 4 * 0x13, "r", "CALC_Compile token jump table (.text)"),
                (0x006FC874, 0x006FC874 + 23, "r", "g_CalcPrecedence (.rdata)"),
                (0x006E6390, 0x006E63D0, "r", "the item callbacks' name strings (.rdata)"),
                (0x00683900, 0x00683C00, "r", "memcpy/memmove jump tables (.text)"),
                (0x00682A40, 0x00682B50, "r", "memcpy's jump tables 0x00682A50..0x00682B43 (.text)"),
                (0x007788D8, 0x007788DC, "w", "strncpy 0x004135D0's store to 0x007788D8 (written only)")]
    E.account(rep, reads, writes, declared)
    return E.finish(rep, neg)


# =============================================================================================== varroll
class RollWorld:
    NMS = 12

    def __init__(self, rnd=None):
        if rnd is None:
            return
        self.ms = []
        for i in range(self.NMS):
            r = bytearray(rnd.getrandbits(8) for _ in range(0x1A8))
            struct.pack_into("<h", r, 0x18, i if i < 3 else rnd.choice([i] * 8 + [-1, self.NMS]))
            self.ms.append(bytes(r))
        self.m2 = []
        for i in range(self.NMS):
            r = bytearray(rnd.getrandbits(8) for _ in range(0x134))
            kind = rnd.random()
            for c in range(16):
                if kind < 0.3:          # one component with two or three variants: duplicates are likely
                    r[0x15 + c] = 0
                elif kind < 0.6:
                    r[0x15 + c] = rnd.choice([0, 0, 1, 2, 2, 3])
                else:
                    r[0x15 + c] = rnd.choice([0, 1, 2, 3, 4, 7, 8, 16, 255, rnd.getrandbits(8)])
            if kind < 0.3:
                r[0x15 + rnd.randrange(16)] = rnd.choice([2, 2, 3])
            r[0x25] = rnd.choice([0, 1, 2, 3, 4, 16, 31, 32, 33, 0x31, rnd.getrandbits(8)])
            if i < 3:               # the duplicate test's subject: one component of 2 (or 3) variants, room for 3 sets
                r[0x15:0x25] = bytes(16)
                r[0x15 + rnd.randrange(16)] = 2 if i < 2 else 3
                r[0x25] = 2
            self.m2.append(bytes(r))

    def meta(self):
        return {"ms": [r.hex() for r in self.ms], "m2": [r.hex() for r in self.m2]}

    @classmethod
    def from_meta(cls, m):
        w = cls()
        w.ms = [bytes.fromhex(x) for x in m["ms"]]
        w.m2 = [bytes.fromhex(x) for x in m["m2"]]
        return w

    def mem(self):
        dt = fields(DTS, [(0xA78, MS), (0xA80, self.NMS), (0xA90, M2), (0xA98, self.NMS)])
        return ["dword %08x %08x" % (G_PDATATABLES, DTS)] + dt + [
                "bytes %08x %s" % (MS, hx(b"".join(self.ms))), "bytes %08x %s" % (M2, hx(b"".join(self.m2))),
                "dword %08x %08x" % (COOKIE, 0x6B3A11F5)]

    def m2rec(self, cls_id):
        if cls_id < 0 or cls_id >= self.NMS:
            return None
        j = s16(struct.unpack_from("<H", self.ms[cls_id], 0x18)[0])
        if j < 0 or j >= self.NMS:
            return None
        return self.m2[j]

    def roll(self, lo, hi, entry, n, neg=False, br=None):
        """sub_005BDB20_MonVariantRoll(seed, entry, n) -> (lo, hi, entry bytes)."""
        def tag(t):
            if br is not None:
                br[t] += 1
        e = bytearray(entry)
        m2 = self.m2rec(s16(struct.unpack_from("<H", e, 0)[0]))
        if m2 is None:
            tag("no_monstats2")
            return lo, hi, bytes(e)
        comp = m2[0x15:0x25]
        nv = e[3]
        cap = s32((1 << (m2[0x25] & 31)) - nv)
        n = s32(n)
        if n > cap:
            n = cap
            tag("cap_binds")
        if n <= 0:
            tag("n_le0")
            return lo, hi, bytes(e)
        if nv + n > 3:
            n = 3 - nv
        if n <= 0:
            tag("full")
            return lo, hi, bytes(e)
        slot = 4 + 16 * nv

        def rng(k):
            nonlocal lo, hi
            v, lo, hi = RNG.rng_range(lo, hi, k)
            return v
        if nv == 0:
            tag("set0")
            for c in range(16):
                e[4 + c] = 0 if comp[c] <= 1 else rng(comp[c]) & 0xFF
            e[3] = (e[3] + 1) & 0xFF
            n -= 1
            slot += 16
        if n == 0:
            return lo, hi, bytes(e)
        K = [c for c in range(16) if comp[c] > 1]
        k = len(K)
        if k == 0:
            tag("no_component")
            return lo, hi, bytes(e)
        if k == 1:
            a = b = K[0]
            tag("k1")
        else:
            u = rng(k)
            a = K[u]
            K[u] = K[k - 1]
            b = K[rng(k - 1)]
            tag("k_ge2")
        for _ in range(n):
            e[slot:slot + 16] = e[4:20]
            tries = 3
            went_neg = False
            for _guard in range(100000):
                e[slot + a] = rng(comp[a]) & 0xFF if comp[a] > 0 else 0
                if b != a:
                    e[slot + b] = rng(comp[b]) & 0xFF if comp[b] > 0 else 0
                dup = False
                for s in range(e[3]):
                    if e[slot:slot + 16] == e[4 + 16 * s:20 + 16 * s]:
                        tries -= 1
                        dup = True
                if tries < 0:
                    went_neg = True
                if not dup:
                    tag("nodup_tries%d" % tries)
                    break
                if (tries <= 0) if neg else (tries == 0):
                    tag("stopped_at_zero_appended_dup")
                    break
            else:
                raise RuntimeError("variant loop did not end")
            if went_neg:
                tag("tries_went_negative")
            e[3] = (e[3] + 1) & 0xFF
            slot += 16
        return lo, hi, bytes(e)


def varroll_cases(rnd):
    w = RollWorld(random.Random(2743))
    cases, exp = [], []
    while len(exp) < 3000:
        e = bytearray(rnd.getrandbits(8) for _ in range(0x34))
        dupcase = rnd.random() < 0.3
        cls_id = rnd.randrange(0, 3) if dupcase else rnd.choice([rnd.randrange(0, w.NMS)] * 10 + [-1, w.NMS])
        struct.pack_into("<h", e, 0, cls_id)
        nv = 2 if dupcase else rnd.choice([0, 0, 1, 2, 2, 2, 3, rnd.getrandbits(8)])
        e[3] = nv
        m2 = w.m2rec(cls_id)
        if m2 is not None and 1 <= nv <= 3:
            comp = m2[0x15:0x25]
            s0 = bytes(rnd.randrange(comp[c]) if comp[c] > 1 else 0 for c in range(16))
            e[4:20] = s0
            for s in range(1, min(nv, 3)):
                if dupcase or rnd.random() < 0.6:
                    e[4 + 16 * s:20 + 16 * s] = s0          # an equal set: a new draw may match two at once
                else:
                    e[4 + 16 * s:20 + 16 * s] = bytes(rnd.randrange(comp[c]) if comp[c] > 1 else 0 for c in range(16))
        n = rnd.choice([1, 3]) if dupcase else rnd.choice([3, 3, 1, 2, 0, -1, 5, 0x7FFFFFFF])
        lo, hi = rnd.getrandbits(32), rnd.getrandbits(32)
        cases += ["w %08x %s" % (SEEDP, hx(le32(lo) + le32(hi))), "w %08x %s" % (ENTRY, hx(e)),
                  "d %08x 8" % SEEDP, "d %08x %d" % (ENTRY, 0x34),
                  "call %08x 0 0 %08x %08x %08x" % (FN["MonVariantRoll"], SEEDP, ENTRY, n & M32)]
        exp.append([lo, hi, e.hex(), n])
    return cases, w.mem(), {"cases": exp, "w": w.meta()}


def varroll_check(d):
    calls, reads, writes, meta = calls_of(d, "varroll")
    rep = Report("varroll")
    w = RollWorld.from_meta(meta["w"])
    neg = 0
    for c, (lo, hi, e, n) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        if stopped(rep, c):
            continue
        e = bytes.fromhex(e)
        br = collections.Counter()
        lo2, hi2, e2 = w.roll(lo, hi, e, n, br=br)
        seed, ent = c["dumps"][0][1], c["dumps"][1][1]
        ok = seed == le32(lo2) + le32(hi2) and ent == e2 and c["pop"] == 12
        rep.c["match"] += ok
        if not ok:
            rep.bad("case %d: got %s %s want %s %s" % (c["n"], seed.hex(), ent.hex(), (le32(lo2) + le32(hi2)).hex(),
                                                       e2.hex()))
            continue
        rep.branches.update(br)
        lo3, hi3, e3 = w.roll(lo, hi, e, n, neg=True)
        neg += (le32(lo3) + le32(hi3) != seed) or e3 != ent
    E.account(rep, reads, writes, [RS_COOKIE])
    return E.finish(rep, neg)


# =============================================================================================== setpick
class SetWorld:
    NTAB = 40

    def __init__(self, rnd=None):
        if rnd is None:
            return
        self.codes = [rnd.getrandbits(32) for _ in range(3)]
        self.tables = [self.rand_sets(rnd, k) for k in range(self.NTAB)]

    def meta(self):
        return {"codes": self.codes, "tables": [[r.hex() for r in t] for t in self.tables]}

    @classmethod
    def from_meta(cls, m):
        w = cls()
        w.codes = m["codes"]
        w.tables = [[bytes.fromhex(r) for r in t] for t in m["tables"]]
        return w

    def rand_sets(self, rnd, k):
        n = [0, 1, 2, 5, 20, 60, 127, 200][k % 8] if k >= 8 else rnd.choice([1, 2, 3, 4, 6])
        out = []
        for _ in range(n):
            r = bytearray(rnd.getrandbits(8) for _ in range(0x1B8))
            struct.pack_into("<H", r, 0x22, rnd.choice([0, 1, 99, 100, 101, 0xFFFF]))
            struct.pack_into("<I", r, 0x28, rnd.choice(self.codes * 3 + [rnd.getrandbits(32)]))
            struct.pack_into("<H", r, 0x2C, rnd.choice([0, 1, 0x1D, 0x1D, rnd.getrandbits(16)]))
            struct.pack_into("<h", r, 0x30, rnd.choice([rnd.randrange(0, 100)] * 6 + [-1, 0x7FFF, -0x8000]))
            wt = rnd.choice([1, 3, 7, 0, 0, -1, -3, rnd.randrange(-10, 10), rnd.getrandbits(32), 0x7FFFFFFF])
            struct.pack_into("<i", r, 0x34, s32(wt))
            r[0x87] = 0
            for o in range(0x88, 0x1B8, 0x10):
                struct.pack_into("<i", r, o, -1)
            out.append(bytes(r))
        return out

    def table_va(self, k):
        return SETS + 0x20000 * k

    def mem(self):
        return ["const bytes %08x %s" % (self.table_va(k), hx(b"".join(t))) for k, t in enumerate(self.tables) if t]

    def pick(self, sets, it, params, neg=False, br=None):
        """ITEMS_BuildSetPick(item, params) -> (eax, lo, hi, file index, flags, ilvl after)."""
        def tag(t):
            if br is not None:
                br[t] += 1
        lo, hi = it["seed"]
        fi, flags = it["fi"], it["flags"]
        ver = it["ver"]
        code = it["code"]
        ilvl = it["ilvl"] if it["ilvl"] >= 1 else 1
        forced, W, cands = -1, 0, []
        f40 = params["f40"] & M32
        for i, r in enumerate(sets):
            if struct.unpack_from("<H", r, 0x22)[0] >= 100 and ver < 100:
                continue
            if s16(struct.unpack_from("<H", r, 0x30)[0]) > ilvl:
                continue
            if code != u32(r, 0x28):
                continue
            if struct.unpack_from("<H", r, 0x2C)[0] == 0x1D and not (params["f80"] & 1):
                continue
            if f40 > 0 and f40 - 1 == i:
                forced = i
            w = s32(u32(r, 0x34))
            if w == 0 and not neg:
                w = 1
                tag("weight0_as_1")
            if w < 0:
                tag("weight_negative")
            cands.append((i, w))
            W = s32(W + w)
        ret_fail = (0, lo, hi, fi, flags, ilvl)
        if forced >= 0:
            tag("forced")
            pick = forced
        else:
            if W == 0:
                tag("total0_return")
                return ret_fail
            if W < 0:
                tag("total_negative_nodraw")
                x = 0
            else:
                lo, hi = RNG.step(lo, hi)
                x = lo % W
            pick = None
            for i, w in cands:
                if x < w:
                    pick = i
                    break
                x = s32(x - w)
            if pick is None:
                tag("walk_fails")
                return (0, lo, hi, fi, flags, ilvl)
            tag("picked")
            if s32(u32(sets[pick], 0x34)) == 0:
                tag("picked_weight0")
        return (1, lo, hi, pick, flags & ~0x10 & M32, ilvl)


def setpick_cases(rnd):
    w = SetWorld(rnd)
    cases, exp = [], []
    itrec = bytearray(rnd.getrandbits(8) for _ in range(0x1A8))
    mem = ["dword %08x %08x" % (G_PDATATABLES, GDT)] + fields(GDT, [(0xE28, 1), (0xE2C, ITREC)]) + w.mem()
    while len(exp) < 3000:
        k = rnd.randrange(w.NTAB)
        sets = w.tables[k]
        code = rnd.choice(w.codes + [rnd.getrandbits(32)])
        struct.pack_into("<I", itrec, 0x80, code)
        it = {"seed": [rnd.getrandbits(32), rnd.getrandbits(32)], "fi": rnd.getrandbits(32),
              "flags": rnd.getrandbits(32), "ver": rnd.choice([0, 1, 99, 100, 101]), "code": code,
              "ilvl": rnd.choice([rnd.randrange(1, 100)] * 6 + [0, -7, 0x7FFF])}
        params = {"f40": rnd.choice([0] * 12 + [rnd.randrange(1, len(sets) + 2)]),
                  "f80": rnd.choice([0, 1, rnd.getrandbits(8)])}
        unit = le32(4) + le32(0) + bytes(12) + le32(IDATA) + bytes(0x18)
        data = bytearray(0x50)
        struct.pack_into("<II", data, 4, *it["seed"])
        struct.pack_into("<I", data, 0x18, it["flags"])
        struct.pack_into("<I", data, 0x28, it["fi"])
        struct.pack_into("<i", data, 0x2C, it["ilvl"])
        struct.pack_into("<H", data, 0x30, it["ver"])
        prm = bytearray(0x90)
        struct.pack_into("<I", prm, 0x40, params["f40"])
        prm[0x80] = params["f80"]
        cases += ["w %08x %s" % (GDT + 0xC18, hx(le32(w.table_va(k)) + le32(len(sets)))),
                  "w %08x %s" % (UNIT, hx(unit)), "w %08x %s" % (IDATA, hx(data)), "w %08x %s" % (ITREC, hx(itrec)),
                  "w %08x %s" % (PARAMS, hx(prm)), "d %08x %d" % (IDATA, 0x50), "r EBX %08x" % UNIT,
                  "call %08x 0 0 %08x" % (FN["ITEMS_BuildSetPick"], PARAMS)]
        exp.append([k, it, params])
    return cases, mem, {"cases": exp, "w": w.meta()}


def setpick_check(d):
    calls, reads, writes, meta = calls_of(d, "setpick")
    rep = Report("setpick")
    w = SetWorld.from_meta(meta["w"])
    neg = 0
    for c, (k, it, params) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        if stopped(rep, c):
            continue
        sets = w.tables[k]
        br = collections.Counter()
        want = w.pick(sets, it, params, br=br)
        data = c["dumps"][0][1]
        got = (c["eax"], u32(data, 4), u32(data, 8), u32(data, 0x28), u32(data, 0x18), s32(u32(data, 0x2C)))
        ok = got == want and c["pop"] == 4
        rep.c["match"] += ok
        if not ok:
            rep.bad("case %d: got %r want %r" % (c["n"], got, want))
            continue
        rep.branches.update(br)
        neg += w.pick(sets, it, params, neg=True) != got
    declared = [(0x00660084, 0x00660084 + 4 * 6, "r", "ItemApplyProps mode jump table 0x00660084 (.text)")]
    E.account(rep, reads, writes, declared)
    return E.finish(rep, neg)


# =============================================================================================== guardctl
def guardctl_cases(rnd):
    """Two calls that must stop at a guard: MonVariantRoll with a NULL seed (the assert path) and the item calc cell
    callback appending to a pool at capacity (CalcPoolAppend's growth calls the allocator)."""
    cases = ["call %08x 0 0 0 %08x 1" % (FN["MonVariantRoll"], ENTRY),
             "w %08x %s" % (E.G_DATATABLES + 0x98, hx(le32(E.ITEMPOOL) + le32(0x10) + le32(0x10))),
             "w %08x %s" % (E.TEXTBUF, hx(b"1+2\0")), "s %08x 16" % E.TEXTBUF, "w %08x %s" % (E.RECBUF, "00" * 16),
             "call %08x %08x 4 %08x 4 0 0" % (FN["ItemCalcCell"], E.TEXTBUF, E.RECBUF)]
    mem = ["dword %08x %08x" % (COOKIE, 0x0BADC0DE), "dword %08x 0" % E.LOCALE_CHANGED,
           "dword %08x 0" % E.SSE_FLAG] + E.stat_tree_mem()
    return cases, mem, {"cases": [["fatal", 0x00408090], ["alloc", 0x0040B4B0]]}


def guardctl_check(d):
    calls, reads, writes, meta = calls_of(d, "guardctl")
    rep = Report("guardctl")
    for c, (kind, addr) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        stop = c.get("stop", "")
        ok = ("%08x" % addr) in stop.split(" ")[0] and "guard address reached" in stop
        rep.c["match"] += ok
        if not ok:
            rep.bad("case %d (%s): %r" % (c["n"], kind, c.get("stop")))
        else:
            rep.branches["guard_" + kind] += 1
    rep.c["traced"] = len(reads) + len(writes)
    print(rep.line())
    for n in rep.notes:
        print("  " + n)
    print("  branches: " + " ".join("%s=%d" % kv for kv in sorted(rep.branches.items())))
    return 1 if rep.c["bad"] else 0


# =============================================================================================== static
PINS = [  # (va, mnemonic, operand substring): the instructions the ledgers cite (ADR-0015 condition 5)
    # MONSTATS_ValidId
    (0x004E6C52, "test", "eax,eax"), (0x004E6C54, "jl", "0x4e6c64"), (0x004E6C5C, "cmp", "eax,DWORD PTR [ecx+0xa80]"),
    (0x004E6C62, "jl", "0x4e6c67"), (0x004E6C64, "or", "eax,0xffffffff"),
    # MulDiv
    (0x00483367, "test", "esi,esi"), (0x00483376, "cmp", "ecx,0x100000"), (0x0048337C, "jle", "0x483395"),
    (0x00483380, "sar", "eax,0x4"), (0x00483387, "jg", "0x4833a6"), (0x00483389, "cdq", ""),
    (0x0048338A, "idiv", "esi"), (0x0048338C, "imul", "eax,edi"), (0x00483395, "cmp", "edi,0x10000"),
    (0x0048339D, "sar", "edx,0x4"), (0x004833A2, "jle", "0x4833be"), (0x004833A6, "imul", "edi"),
    (0x004833B3, "call", "0x684240"), (0x004833C1, "idiv", "esi"), (0x004833C5, "imul", "eax,ecx"),
    (0x004833CE, "imul", "eax,edi"), (0x004833D1, "cdq", ""), (0x004833D3, "idiv", "esi"),
    (0x00684252, "neg", "eax"), (0x00684254, "neg", "edx"), (0x00684256, "sbb", "eax,0x0"),
    # AffixCandAdd and its caller
    (0x005C0D03, "cmp", "eax,0x1ff"), (0x005C0D08, "jge", "0x5c0d17"), (0x005C0D0A, "mov", "DWORD PTR [ecx+eax*8+0x4],edx"),
    (0x005C17C9, "call", "0x5c0d00"), (0x005C17D2, "mov", "DWORD PTR [ebp-0x4],eax"),
    (0x005C17E1, "add", "DWORD PTR [ebp-0x8],ecx"), (0x005C17EA, "add", "DWORD PTR [ebp-0x8],edx"),
    (0x005C1828, "mov", "edx,DWORD PTR [ebp-0x8]"), (0x005C182B, "add", "edx,0x1"),
    (0x005C15AE, "mov", "eax,0x38e38e39"),
    # SKILLS_CalcVar codes 43-48
    (0x006468BE, "lea", "edx,[esi-0x2b]"), (0x006468C1, "mov", "eax,0x55555556"), (0x006468C6, "imul", "edx"),
    (0x006468CA, "shr", "esi,0x1f"), (0x00646910, "lea", "edx,[esi-0x2c]"), (0x0064691C, "shr", "esi,0x1f"),
    (0x0064B1BF, "shl", "eax,cl"), (0x0064B28F, "shl", "eax,cl"),
    # EXCEL_ParseTxt: the first-pass gate counts .txt columns only; the defaults pass
    (0x006BD7FE, "mov", "eax,DWORD PTR [ebx+0xc]"), (0x006BD847, "cmp", "edx,eax"),
    (0x006BDFBE, "jmp", "DWORD PTR [ebx*4+0x6be128]"), (0x006BE016, "mov", "edx,edi"), (0x006BE018, "xor", "ecx,ecx"),
    (0x006BCFB0, "cmp", "DWORD PTR [ebx-0x4],0x0"),
    # MonVariantRoll
    (0x005BDB87, "shl", "esi,cl"), (0x005BDCC0, "mov", "DWORD PTR [ebp-0x20],0x3"),
    (0x005BDE28, "sub", "DWORD PTR [ebp-0x20],eax"), (0x005BDE46, "cmp", "DWORD PTR [ebp-0x20],0x0"),
    (0x005BDE4A, "jne", "0x5bdcd0"),
    # ITEMS_BuildSetPick
    (0x005C2678, "test", "ecx,ecx"), (0x005C268A, "mov", "DWORD PTR [ebp+edi*8-0x810],0x1"),
    (0x005C26B9, "test", "esi,esi"), (0x005C26BB, "je", "0x5c25e9"), (0x005C26CB, "call", "0x45c3e0"),
    (0x005C26E7, "cmp", "eax,edx"), (0x005C26E9, "jl", "0x5c26fe"), (0x005C25C3, "sub", "esp,0x814"),
    (0x0045C3E3, "test", "esi,esi"), (0x0045C3E5, "jg", "0x45c3eb"),
]

ROOTS = {  # family -> (entry, functions a case may reach, by reading the code)
    "validid": [0x004E6C50], "muldiv": [0x00483360], "candadd": [0x005C0D00], "pickaffix": [0x005C1560],
    "calcvar2": [0x00646460], "parsetxt2": [0x006BD780, 0x00631530], "varroll": [0x005BDB20],
    "setpick": [0x005C25C0],
}


def cmd_static(a):
    rep = Report("static")
    A = S4.asm()
    for va, mn, sub in PINS:
        ins = A.at(va)
        rep.c["pins"] += 1
        if ins is None or ins[0] != mn or sub not in ins[1]:
            rep.bad("pin 0x%08X: %r, want %s %s" % (va, ins, mn, sub))
        else:
            rep.c["pins_ok"] += 1
    # the masks the item-type test reads are 1 << i
    m = S4.dwords(MASKS, 32)
    rep.c["masks_ok"] = int(m == [1 << i for i in range(32)])
    if not rep.c["masks_ok"]:
        rep.bad("mask table 0x%08X: %r" % (MASKS, m))
    # static call closures: which allocator, fatal and indirect sites each family's code can reach
    for fam, roots in ROOTS.items():
        G = S4.graph(roots, stop=FATAL + ALLOC)
        fatal = sorted(set(e for e, v in G.items() for _, t in v[3] if t in FATAL))
        alloc = sorted(set(e for e, v in G.items() for _, t in v[3] if t in ALLOC))
        ind = sorted(set(e for e, v in G.items() if v[4]))
        rep.notes.append("  %-9s %3d functions; fatal call in %d, allocator call in %d (%s), indirect site in %d (%s)"
                         % (fam, len(G), len(fatal), len(alloc), " ".join("%08X" % x for x in alloc[:6]), len(ind),
                            " ".join("%08X" % x for x in ind[:8])))
    # the declared .data reads (g_MissCalcFuncs): no store in .text (as S1e's scan)
    for lo, hi, name in [(0x00745828, 0x0074584C, "g_MissCalcFuncs + g_nMissCalcFuncs")]:
        stores = []
        for va, (mn, ops) in A.ins.items():
            for t in E.mem_targets(ops):
                if lo - 3 <= t < hi and E.STORE.match(mn) and "PTR" in ops.split(",")[0] and mn != "push":
                    stores.append((va, mn, ops))
        rep.c["data_stores"] += len(stores)
        rep.notes.append("  %s 0x%08X..0x%08X: %d stores" % (name, lo, hi - 1, len(stores)))
        for s in stores:
            rep.bad("store into %s: %r" % (name, s))
    # every other declared image read lies in a section without write permission
    for lo, name in ((MASKS, "bit masks"), (0x00660084, "ItemApplyProps jump table"), (0x00646ABC, "CalcVar jump table"),
                     (0x006C1164, "CALC_Eval jump table"), (0x006BE0D7, "ParseTxt class bytes"),
                     (0x006CEE30, "name hash table"), (0x006F9280, "ctype table"), (0x006FC874, "g_CalcPrecedence")):
        sec = S4.section_of(lo)
        flags = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.c["ro_reads"] += 1
        if flags & 0x80000000:
            rep.bad("%s 0x%08X in writable %s" % (name, lo, sec))
    print(rep.line())
    for n in rep.notes:
        print(n)
    return 1 if rep.c["bad"] else 0


def cmd_manifest(a):
    lines = []
    for root, _, files in sorted(os.walk(a.dir)):
        for f in sorted(files):
            if f == "manifest.txt":
                continue
            p = os.path.join(root, f)
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            lines.append("%s  %s" % (h, os.path.relpath(p, a.dir)))
    text = "\n".join(lines) + "\n"
    if a.write:
        open(os.path.join(a.dir, "manifest.txt"), "w").write(text)
    print("S1F manifest files=%d sha256=%s" % (len(lines), hashlib.sha256(text.encode()).hexdigest()))
    return 0


FAMILIES = {
    "validid": (validid_cases, validid_check),
    "muldiv": (muldiv_cases, muldiv_check),
    "candadd": (candadd_cases, candadd_check),
    "pickaffix": (pickaffix_cases, pickaffix_check),
    "calcvar2": (calcvar2_cases, calcvar2_check),
    "parsetxt2": (parsetxt2_cases, parsetxt2_check),
    "varroll": (varroll_cases, varroll_check),
    "setpick": (setpick_cases, setpick_check),
    "guardctl": (guardctl_cases, guardctl_check),
}
SSE_FAMILIES = ("parsetxt2",)


def cmd_cases(a):
    for fam in a.family or list(FAMILIES):
        rnd = random.Random("s1f-" + fam)
        cases, mem, meta = FAMILIES[fam][0](rnd)
        mem = mem + GUARDS
        if fam in SSE_FAMILIES:
            mem = mem + ["dword %08x 0" % E.SSE_FLAG]
        E.write_family(a.dir, fam, cases, mem, meta)
        if fam in SSE_FAMILIES:
            with open(os.path.join(a.dir, fam + "-sse.mem"), "w") as f:
                f.write("\n".join(mem[:-1] + ["dword %08x 1" % E.SSE_FLAG]) + "\n")
        print("S1F cases %s calls=%d mem_lines=%d" % (fam, sum(1 for c in cases if c.startswith("call")), len(mem)))
    return 0


def cmd_check(a):
    rc = 0
    for fam in a.family or list(FAMILIES):
        rc |= FAMILIES[fam][1](a.dir)
        if fam in SSE_FAMILIES:
            rc |= parsetxt2_check(a.dir, "-sse")
    return rc


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["cases", "check", "static", "manifest", "all"])
    ap.add_argument("family", nargs="*")
    ap.add_argument("--dir", default=DEFDIR)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "cases":
        return cmd_cases(a)
    if a.cmd == "check":
        return cmd_check(a)
    if a.cmd == "static":
        return cmd_static(a)
    if a.cmd == "manifest":
        return cmd_manifest(a)
    rc = cmd_check(a)
    rc |= cmd_static(a)
    cmd_manifest(a)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

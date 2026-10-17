#!/usr/bin/env python3
"""Plan 0038 batch S1e: the binary's own functions run under Ghidra's p-code emulator (ADR-0015) and compared bit for
bit with the models below (no game run, no slot).

    python3 -I tools/sweep_s1e.py cases [FAMILY ...] [--dir D]   write D/<family>.cases, .mem, .json (expected values)
    tools/ghidra.sh emutrace D/<family>.cases D/<family>.mem > D/<family>.out        (re/ghidra_scripts/EmuTrace.java)
    python3 -I tools/sweep_s1e.py check [FAMILY ...] [--dir D]   compare D/<family>.out with the models; account for
                                                                every traced access; run the negative controls
    python3 -I tools/sweep_s1e.py static                         objdump pins (subtle instructions, ADR-0015 (5)) and
                                                                the writer scan of every declared image read
    python3 -I tools/sweep_s1e.py manifest [--write]             sha256 of every file under D
    python3 -I tools/sweep_s1e.py all [--dir D]                  check of every family, static, manifest

Families (the functions each calls, the inventory rows it serves):
  rng      RNG_RangePow2Plus 0x00472240                                   rng 3, 5
  bitbuf   BITBUF_WriteClamped 0x0062AF50 (and BITBUF_Write under it)    save/d2s 82, 122, 129, 133
  eval     CALC_Eval 0x006C0BC0 on synthetic code, with an identity variable reader (0x0040F590), the stock skills,
           missiles and items function tables and a scratch table of the stock min/max/rand/sklvl entries under
           every argc                                                     data-calc 4, 10, 13, 14, 15, 20, 38, 39
  entry    SKILLS_EvalCalc, SKILLS_EvalDescCalc, ITEMS_EvalCalc, MISS_EvalCalc: the offset test   data-calc 9, 16, 37
  calcvar  SKILLS_CalcVar 0x00646460 on synthetic skills/skilldesc/missiles records and a synthetic pool
                                                                          data-calc 31 (6 of 7), 40
  compile  CALC_Compile 0x006C1AE0 with the item callbacks; the item variable reader 0x00627B40
                                                                          data-calc 5, 11, 12, 36
  excel    EXCEL_FindCode, EXCEL_AddCode, EXCEL_FindName                 data-excel 16, 36, 37, 40
  tccell   TC_ParseItemCell 0x00654440 on a synthetic item code link, TC/unique/set name trees and a TC builder
                                                                          data-excel 43, 44
  lang     LNG_GetLanguageCode 0x00525260                                 data-excel 51
  strings  STRTABLE_GetByIndex, STRTABLE_GetByKey, STRTABLE_KeyToIndex, UNICODE_CharCount on stock and synthetic
           string tables                                                  data-excel 52, 53, 56; data-strings 4, 5,
                                                                          10, 12, 14, 16, 17, 20, 24, 25, 32, 35
  parsetxt EXCEL_ParseTxt 0x006BD780 on a synthetic parsed .txt and descriptor; the item calc cell callback
           0x00631530                                                     data-excel 60, 64, 66

Each check prints one `S1E <family> key=value ...` line: cases, matches, mismatches (`bad`), the branches reached,
the negative control's mismatch count (`neg`, must be above 0), and the traced accesses outside the stack and the
memory spec, each of which must fall in the family's declared read set (`undeclared`, must be 0). The batch record is
run:2026-10-17-sweep-emu in docs/findings/data/experiments.md and the "Plan 0038 batch S1e" sections of the findings.

Stdlib only, plus objdump for `static`. Writes only under D (default workspace/logs/sweep-s1e/).
"""
import argparse
import collections
import functools
import hashlib
import json
import os
import random
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import calc as CALC  # noqa: E402
import rng as RNG  # noqa: E402
import sweep_s4b as S4  # noqa: E402

ROOT = os.path.dirname(HERE)
WS = os.path.join(ROOT, "workspace")
DEFDIR = os.path.join(WS, "logs", "sweep-s1e")
MERGED = os.path.join(WS, "merged")
ENG = os.path.join(MERGED, "data", "local", "lng", "eng")
M32 = 0xFFFFFFFF


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def cdiv(x, y):
    q = abs(x) // abs(y)
    return q if (x < 0) == (y < 0) else -q


def le32(v):
    return struct.pack("<I", v & M32)


def hx(b):
    return bytes(b).hex()


@functools.lru_cache(maxsize=None)
def img_bytes(va, n):
    """n bytes of the pinned image at va (zeros past a section's file bytes)."""
    out = bytearray()
    for k in range(n):
        off = S4.va_off(va + k)
        out.append(0 if off is None else S4.image()[0][off])
    return bytes(out)


# ----------------------------------------------------------------------------------------------- addresses (pinned)
FN = {
    "RNG_RangePow2Plus": 0x00472240, "BITBUF_WriteClamped": 0x0062AF50, "BITBUF_Write": 0x00410EB0,
    "CALC_Eval": 0x006C0BC0, "CALC_Compile": 0x006C1AE0, "IDENT": 0x0040F590,
    "SKILLS_EvalCalc": 0x00646CA0, "SKILLS_EvalDescCalc": 0x00646D00, "ITEMS_EvalCalc": 0x00627C20,
    "MISS_EvalCalc": 0x0064B7C0, "SKILLS_CalcVar": 0x00646460, "SkillsCalcVar": 0x00646BE0,
    "ItemCalcVar": 0x00627B40, "ItemCalcFnLookup": 0x00631430, "ItemCalcFnArity": 0x00631490,
    "ItemCalcIdent": 0x006314A0, "ItemCalcCell": 0x00631530,
    "EXCEL_FindCode": 0x006BD130, "EXCEL_AddCode": 0x006BD230, "EXCEL_FindName": 0x006BD3C0,
    "TC_ParseItemCell": 0x00654440, "LNG_GetLanguageCode": 0x00525260,
    "STRTABLE_GetByIndex": 0x00524A30, "STRTABLE_GetByKey": 0x00524D30, "STRTABLE_KeyToIndex": 0x006117B0,
    "UNICODE_CharCount": 0x00527D50, "EXCEL_ParseTxt": 0x006BD780,
}
SK_MIN, SK_MAX, SK_RAND, SK_SKILL, SK_MISS, SK_STAT, SK_SKLVL = (0x006436E0, 0x006436F0, 0x00643700, 0x00646C00,
                                                                0x00643740, 0x00643770, 0x00646C60)
IT_MIN, IT_MAX, IT_RAND, IT_STAT = 0x00627B50, 0x00627B60, 0x00627B70, 0x00627BB0
MI_MIN, MI_MAX, MI_RAND, MI_SKILL = 0x0064B700, 0x0064B710, 0x0064B720, 0x0064B760
FNKIND = {SK_MIN: "min", IT_MIN: "min", MI_MIN: "min", SK_MAX: "max", IT_MAX: "max", MI_MAX: "max",
          SK_RAND: "rand", IT_RAND: "rand", MI_RAND: "mrand", SK_SKLVL: "sklvl"}
T_SKILLS, N_SKILLS = 0x00745774, 0x007457AC
T_MISS, N_MISS = 0x00745828, 0x00745848
T_ITEMS, N_ITEMS = 0x0074463C, 0x0074465C
G_PDATATABLES = 0x00744304
G_DATATABLES = 0x0096BC30
COOKIE = 0x00749DE0

# scratch memory (outside the image)
DT = 0x10000000          # a DataTables image (0x1000 bytes)
CODE = 0x10020000        # CALC_Eval code buffer
FTAB = 0x10030000        # a scratch function table
CTX = 0x10040000         # a scratch evaluation context
UNIT = 0x10041000        # a scratch unit (seed at +0x20)
BB = 0x10050000          # a bit-buffer context, its bytes at BBUF
BBUF = 0x10051000
SEED = 0x10060000
SKREC = 0x10100000       # skills records (0x23C)
SDREC = 0x10180000       # skilldesc records (0x120)
MIREC = 0x101C0000       # missiles records (0x1A4)
POOL = 0x10200000        # a formula pool


# ------------------------------------------------------------------------------------------------- file handling
def write_family(d, fam, cases, mem, meta):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, fam + ".cases"), "w") as f:
        f.write("\n".join(cases) + "\n")
    with open(os.path.join(d, fam + ".mem"), "w") as f:
        f.write("\n".join(mem) + "\n")
    with open(os.path.join(d, fam + ".json"), "w") as f:
        json.dump(meta, f)


def read_out(path):
    """-> (calls [dict], reads [(pc, addr, size, count)], writes [...])"""
    calls, reads, writes = [], [], []
    for ln in open(path):
        p = ln.split()
        if not p:
            continue
        if p[0] == "C":
            c = {"n": int(p[1]), "fn": int(p[2], 16), "dumps": []}
            if p[3] == "STOP":
                c["stop"] = " ".join(p[4:])
            else:
                kv = dict(x.split("=") for x in p[3:])
                c.update(eax=int(kv["eax"], 16), edx=int(kv["edx"], 16), pop=int(kv["pop"]), steps=int(kv["steps"]))
            calls.append(c)
        elif p[0] == "D":
            calls[-1]["dumps"].append((int(p[1], 16), bytes.fromhex(p[2]) if len(p) > 2 else b""))
        elif p[0] in ("R", "W"):
            (reads if p[0] == "R" else writes).append((int(p[1], 16), int(p[2], 16), int(p[3]), int(p[4])))
    return calls, reads, writes


class Report:
    def __init__(self, fam):
        self.fam = fam + OUT_SUFFIX
        self.c = collections.Counter()
        self.notes = []
        self.branches = collections.Counter()

    def bad(self, why):
        self.c["bad"] += 1
        if self.c["bad"] <= 25:
            self.notes.append("BAD " + why)

    def line(self):
        keys = ["cases", "match", "bad", "neg", "traced", "undeclared"]
        rest = sorted(k for k in self.c if k not in keys)
        s = "S1E %s " % self.fam + " ".join("%s=%d" % (k, self.c[k]) for k in keys + rest)
        return s


def account(rep, reads, writes, declared):
    """Every traced access must lie in a declared range: declared = [(lo, hi, kind, why)]; kind 'r' or 'rw'."""
    seen = collections.Counter()
    for kind, rows in (("R", reads), ("W", writes)):
        for pc, a, n, cnt in rows:
            rep.c["traced"] += 1
            hit = None
            for lo, hi, k, why in declared:
                if lo <= a and a + n <= hi and (kind == "R" or "w" in k):
                    hit = why
                    break
            if hit is None:
                rep.c["undeclared"] += 1
                rep.bad("undeclared %s pc=0x%08X addr=0x%08X size=%d count=%d" % (kind, pc, a, n, cnt))
            else:
                seen[hit] += cnt
    for why, cnt in sorted(seen.items()):
        rep.notes.append("  read-set %s: %d accesses" % (why, cnt))


def finish(rep, neg_fail):
    rep.c["neg"] = neg_fail
    if neg_fail == 0:
        rep.bad("negative control did not fail")
    print(rep.line())
    for n in rep.notes:
        print("  " + n)
    if rep.branches:
        print("  branches: " + " ".join("%s=%d" % kv for kv in sorted(rep.branches.items())))
    return 1 if rep.c["bad"] else 0


OUT_SUFFIX = ""        # "-sse": the run with the CRT's SSE2 flag set (memcpy/memset's other path)
SSE_FLAG = 0x00994C88  # written once by the CRT start-up (0x0069A8C5); memcpy/memmove/memset pick a path by it
SSE_FAMILIES = ("compile", "parsetxt")


def calls_by_case(d, fam):
    calls, reads, writes = read_out(os.path.join(d, fam + OUT_SUFFIX + ".out"))
    meta = json.load(open(os.path.join(d, fam + ".json")))
    return calls, reads, writes, meta


# declared image reads shared by several families (ADR-0015 condition 2; `static` runs the writer scan)
RS_COOKIE = (COOKIE, COOKIE + 4, "r", "security cookie 0x00749DE0 (xor in, xor out: no output depends on it)")
RS_CALC_JT = (0x006C1164, 0x006C1164 + 4 * 22, "r", "CALC_Eval jump table 0x006C1164, opcodes 01-16 (.text)")


# =============================================================================================== family: rng
def rng_cases(rnd):
    cases, exp = [], []
    seeds = [(0, 0), (1, 666), (M32, M32), (0x12345678, 666), (0x80000000, 0x7FFFFFFF)]
    ns = [0, 1, 2, 3, 4, 7, 8, 0x10, 0x100, 0x7FFFFFFF, 0x80000000, 0x80000001, M32, 0xFFFFFFFE, 0x40000000]
    bases = [0, 1, M32, 0x7FFFFFFF, 0x80000000, 5, 0xFFFFFF9C]
    todo = [(s, b, n) for s in seeds for b in bases[:3] for n in ns]
    while len(todo) < 3000:
        todo.append(((rnd.getrandbits(32), rnd.getrandbits(32)), rnd.choice(bases + [rnd.getrandbits(32)]),
                     rnd.choice(ns + [rnd.getrandbits(32), 1 << rnd.randrange(32), rnd.randrange(1, 1000)])))
    for (lo, hi), base, n in todo:
        cases += ["w %08x %s" % (SEED, hx(le32(lo) + le32(hi))), "d %08x 8" % SEED,
                  "call %08x %08x %08x %08x" % (FN["RNG_RangePow2Plus"], SEED, base, n)]
        exp.append([lo, hi, base, n])
    return cases, [], {"cases": exp}


def rng_model(lo, hi, base, n, neg=False):
    lo2, hi2 = RNG.step(lo, hi)
    if neg:     # the sibling RNG_RangePow2's map (no base), or a mask of n instead of n - 1
        return (lo2 & n) + base & M32, lo2, hi2
    return ((lo2 & ((n - 1) & M32)) + base) & M32, lo2, hi2


def rng_check(d):
    calls, reads, writes, meta = calls_by_case(d, "rng")
    rep = Report("rng")
    neg = 0
    for c, (lo, hi, base, n) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        eax, lo2, hi2 = rng_model(lo, hi, base, n)
        got = c.get("eax"), struct.unpack("<II", c["dumps"][0][1]) if "eax" in c else None, c.get("pop")
        if "stop" in c or (got[0], got[1], got[2]) != (eax, (lo2, hi2), 4):
            rep.bad("case %d: %r != %r" % (c["n"], got, (eax, (lo2, hi2), 4)))
        else:
            rep.c["match"] += 1
        if rng_model(lo, hi, base, n, neg=True)[0] != c.get("eax"):
            neg += 1
        rep.branches["n_pow2" if n and not n & (n - 1) else "n_other"] += 1
        rep.branches["base_nonzero"] += base != 0
    account(rep, reads, writes, [])
    return finish(rep, neg)


# =============================================================================================== family: bitbuf
MASKTAB = 0x006CE368


def bb_write(buf, st, value, nbits):
    """fn:BITBUF_Write@0x00410EB0. st = [cur, cap, byteidx, bitpos, overflow]; buf: bytearray at BBUF."""
    mask = [S4.dword(MASKTAB + 4 * k) & 0xFF for k in range(9)]     # u32[9] at 0x006CE368, low byte used
    cur, cap, bi, bp, ov = st
    cap = s32(cap)
    if cap < s32(bp + bi * 8 + nbits):
        st[4] = 1
        st[2] = (cap + ((cap >> 31) & 7)) >> 3
        st[3] = 0
        return
    if bp == 0:
        buf[cur - BBUF] = 0
    value = s32(value)
    while nbits >= 1:
        k = 8 - bp
        if nbits < k:
            k = nbits
        buf[cur - BBUF] |= ((mask[k] & value & 0xFF) << bp) & 0xFF
        bp += k
        if bp != 8:
            break
        bi += 1
        cur += 1
        bp = 0
        if bi * 8 < cap:
            buf[cur - BBUF] = 0
        value >>= k
        nbits -= k
    st[0], st[2], st[3] = cur, bi, bp


def clampu(v, n, neg=False):
    if n == 32:
        return v & M32
    m = ((1 << (n & 31)) - 1) & M32
    if neg:     # a signed clamp: negative to 0
        return 0 if s32(v) < 0 else min(v, m)
    return min(v & M32, m)


def bitbuf_cases(rnd):
    cases, exp = [], []
    vals = [0, 1, 2, 0x7F, 0x80, 0xFF, 0x100, 0x1FF, 0x7FFFFFFF, 0x80000000, M32, 0xFFFFFFFE, 0xFFFFFF00, 0xFFFF]
    todo = [(n, v) for n in range(0, 33) for v in vals]
    while len(todo) < 2500:
        n = rnd.randrange(0, 33)
        v = rnd.choice([rnd.getrandbits(32), (-rnd.randrange(1, 1 << 20)) & M32, rnd.randrange(0, 1 << max(n, 1) + 1)])
        todo.append((n, v))
    for n, v in todo:
        bi = rnd.randrange(0, 8)
        bp = rnd.randrange(0, 8)
        cap = rnd.choice([512, 512, 512, bi * 8 + bp + n, bi * 8 + bp + n - 1, bi * 8 + bp + n + 1])
        pre = bytes(rnd.getrandbits(8) for _ in range(24))
        st = [BBUF + bi, cap, bi, bp, 0]
        cases += ["w %08x %s" % (BBUF, hx(pre)),
                  "w %08x %s" % (BB, hx(b"".join(le32(x) for x in st))),
                  "d %08x 20" % BB, "d %08x 24" % BBUF,
                  "call %08x %08x %08x %08x" % (FN["BITBUF_WriteClamped"], n, v, BB)]
        exp.append([n, v, st, pre.hex()])
    return cases, [], {"cases": exp}


def bitbuf_check(d):
    calls, reads, writes, meta = calls_by_case(d, "bitbuf")
    rep = Report("bitbuf")
    neg = 0
    for c, (n, v, st, pre) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        outs = []
        for negm in (False, True):
            buf = bytearray(bytes.fromhex(pre))
            s = list(st)
            bb_write(buf, s, clampu(v, n, negm), n)
            outs.append((b"".join(le32(x) for x in s), bytes(buf)))
        got = (c["dumps"][0][1], c["dumps"][1][1]) if "eax" in c else None
        if got != outs[0] or c.get("pop") != 4:
            rep.bad("case %d n=%d v=%08x: %r != %r" % (c["n"], n, v, got, outs[0]))
        else:
            rep.c["match"] += 1
        neg += got != outs[1]
        if n != 32 and (v & M32) > (((1 << n) - 1) & M32):
            rep.branches["clamped_neg" if v & 0x80000000 else "clamped_pos"] += 1
        rep.branches["n32"] += n == 32
        rep.branches["overflow"] += outs[0][0][16:20] != b"\0\0\0\0"
    account(rep, reads, writes, [(MASKTAB, MASKTAB + 36, "r", "BITBUF_Write mask table u32[9] 0x006CE368 (.rdata)")])
    return finish(rep, neg)


# =============================================================================================== family: eval
# A model of fn:CALC_Eval@0x006C0BC0 with explicit variable reader and function table.
class EvalEnv:
    """var: None (varFn NULL), 'ident' (0x0040F590: returns ECX) or 'skills' (sub_00646BE0 over a CalcVar model).
    funcs: [(kind, argc)] as the table holds them; nfuncs: the signed count passed; mem: {'seed': (lo, hi)}."""

    def __init__(self, var, funcs, nfuncs, ctx, unit_seed=None, ctx_words=None, calcvar=None):
        self.var, self.funcs, self.nfuncs, self.ctx = var, funcs, s32(nfuncs), ctx
        self.seed = unit_seed           # seed at unit + 0x20 (skills/items rand)
        self.ctxseed = None             # seed at ctx + 0x20 (missile rand)
        self.ctx_words = ctx_words or [0, 0, 0]
        self.calcvar = calcvar
        self.events = collections.Counter()

    def var_value(self, op, idx):
        if self.var == "ident":
            return idx
        if self.var == "skills":
            if not self.ctx:
                return 0
            unit, skill, lvl = self.ctx_words
            return self.calcvar(unit, idx & 0xFF, skill, lvl)
        raise ValueError(self.var)

    def call(self, f, a, b, c):
        kind = self.funcs[f][0]
        a, b, c = s32(a), s32(b), s32(c)
        if kind == "min":
            return a if a < b else b
        if kind == "max":
            return a if a > b else b
        if kind in ("rand", "mrand"):
            if not self.ctx:
                return 0
            if a >= b:
                return a
            n = (b - a + 1) & M32
            lo, hi = self.seed if kind == "rand" else self.ctxseed
            r, lo, hi = RNG.rng_range(lo, hi, n)
            if kind == "rand":
                self.seed = (lo, hi)
            else:
                self.ctxseed = (lo, hi)
            self.events["rand_draw" if not (n & 0x80000000 or n == 0) else "rand_nodraw"] += 1
            return s32(a + r)
        if kind == "sklvl":
            if not self.ctx:
                return 0
            unit, skill, lvl = self.ctx_words
            lv = self.calcvar(unit, b & 0xFF, skill, lvl)
            return self.calcvar(unit, c & 0xFF, a, lv)
        raise ValueError(kind)


class PowLimit(Exception):
    pass


def eval_model(code, length, env, trace=None, divfix=True, stack=64):
    """Value of CALC_Eval(code, length, ...). code: the whole buffer (operands may be read past length, as the binary
    reads the 01 operand). Raises PowLimit for an exponent the emulator should not be asked to loop over."""
    length = s32(length)
    if length <= 0:
        if trace is not None:
            trace["len_le0"] += 1
        return 0
    st = []

    def pop():
        return st.pop() if st else 0

    def push(v):
        if len(st) < stack:
            st.append(s32(v))

    def tr(k):
        if trace is not None:
            trace[k] += 1

    p = 0
    while p < length:
        op = code[p]
        p += 1
        tr("op%02X" % min(op, 0x17))
        if op in (4, 5, 6):
            if env.var is None:
                tr("var_null")
                return 0
            if p >= length:
                tr("operand_past_len")
                return 0
            n = {4: 1, 5: 2, 6: 4}[op]
            raw = code[p:p + n]
            idx = raw[0] if op == 4 else struct.unpack("<h" if op == 5 else "<i", raw)[0]
            push(env.var_value(op, idx & M32 if op == 6 else idx))
            p += n
        elif op in (7, 8, 9):
            if p >= length:
                tr("operand_past_len")
                return 0
            n = {7: 1, 8: 2, 9: 4}[op]
            push(struct.unpack({7: "<b", 8: "<h", 9: "<i"}[op], code[p:p + n])[0])
            p += n
        elif op == 1:
            f = code[p]
            p += 1
            if f >= env.nfuncs:
                tr("f_out_of_range")
                push(0)
                continue
            argc = s32(env.funcs[f][1])
            if argc == 3:
                c = pop(); b = pop(); a = pop()
            elif argc == 2:
                b = pop(); a = pop(); c = 0
            elif argc == 1:
                a = pop(); b = c = 0
            elif argc == 0:
                a = b = c = 0
            else:
                tr("argc_other")
                push(0)
                continue
            tr("argc%d" % argc)
            push(env.call(f, a, b, c))
        elif 0x0A <= op <= 0x14:
            r = pop()
            l = pop()
            if op == 0x0A:
                v = int(l < r)
            elif op == 0x0B:
                v = int(l > r)
            elif op == 0x0C:
                v = int(l <= r)
            elif op == 0x0D:
                v = int(l >= r)
            elif op == 0x0E:
                v = int(l == r)
            elif op == 0x0F:
                v = int(l != r)
            elif op == 0x10:
                v = l + r
            elif op == 0x11:
                v = l - r
            elif op == 0x12:
                v = l * r
            elif op == 0x13:
                if r == 0 and divfix:
                    tr("div_zero")
                    v = 0
                elif r == 0:
                    v = l
                else:
                    if l == -0x80000000 and r == -1:
                        raise PowLimit("INT32_MIN / -1")
                    v = cdiv(l, r)
            else:
                tr("pow_e_le0" if r <= 0 else "pow")
                if r <= 0:
                    v = 1
                else:
                    if r > 64:
                        raise PowLimit("exponent %d" % r)
                    v = l
                    for _ in range(r - 1):
                        v = s32(v * l)
            if op <= 0x0F:
                tr("cmp%02X_%d" % (op, v))
            elif s32(v) != v:
                tr("wrap%02X" % op)
            push(v)
        elif op == 0x15:
            push(-pop())
        elif op == 0x16:
            e = pop()
            t = pop()
            if not st:
                tr("ternary_short")
                push(e)
            else:
                cond = pop()
                tr("ternary_%s" % ("then" if cond else "else"))
                push(t if cond else e)
        else:
            tr("end_empty" if not st else "end_value")
            return st.pop() if st else 0
        if len(st) >= stack:
            tr("stack_full")
    tr("ran_past_len")
    return 0


SKILLS_TABLE = [("min", 2), ("max", 2), ("rand", 2), ("skill", 2), ("miss", 2), ("stat", 2), ("sklvl", 3)]


def stock_table(tab, cnt):
    n = S4.dword(cnt)
    ent = []
    for k in range(n):
        fn, argc = S4.dword(tab + 8 * k), S4.dword(tab + 8 * k + 4)
        ent.append((FNKIND.get(fn, "fn%08X" % fn), argc))
    return ent, n


def rand_program(rnd, nfuncs_ok, allow_var, maxlen, var_codes=None):
    """Random bytes biased to valid opcodes; function indices from nfuncs_ok; variable indices (low byte) from
    var_codes when given."""
    out = bytearray()
    depth = 0
    while len(out) < maxlen:
        r = rnd.random()
        if r < 0.32 or depth < 1:
            op = rnd.choice([7, 7, 8, 9] + ([4, 5, 6] if allow_var else []))
            out.append(op)
            if op in (4, 5, 6) and var_codes is not None:
                low = rnd.choice(var_codes)
                hi = {4: 0, 5: rnd.getrandbits(8), 6: rnd.getrandbits(24)}[op]
                out += struct.pack("<I", (hi << 8) | low)[:{4: 1, 5: 2, 6: 4}[op]]
            elif op in (7, 4):
                out += bytes([rnd.choice([rnd.getrandbits(8), 0, 1, 2, 0xFF, 0x80, 0x7F, 3, 5])])
            elif op in (8, 5):
                out += struct.pack("<h", rnd.choice([rnd.randrange(-0x8000, 0x8000), 300, -300, 0x7FFF, -0x8000]))
            else:
                out += struct.pack("<i", rnd.choice([rnd.randrange(-2 ** 31, 2 ** 31), 2 ** 31 - 1, -2 ** 31,
                                                     100000, -100000, 65536]))
            depth += 1
        elif r < 0.80:
            op = rnd.choice(list(range(0x0A, 0x15)) + [0x15, 0x16, 0x14, 0x13, 0x13])
            out.append(op)
            depth = max(depth - (2 if op <= 0x14 else 0 if op == 0x15 else 2), 0)
        elif r < 0.92:
            out += bytes([1, rnd.choice(nfuncs_ok)])
        elif r < 0.97:
            out.append(rnd.choice([0, 2, 3, 0x17, 0x18, 0x40, 0xFF, rnd.randrange(0x17, 0x100)]))
            if rnd.random() < 0.7:
                break
        else:
            for _ in range(rnd.randrange(1, 80)):          # a run of pushes (stack limit)
                out += bytes([7, rnd.getrandbits(8)])
            depth += 1
    out.append(0)
    return bytes(out)


EVAL_UNITSEED = (0x5EED1234, 0x29A)


def eval_setup_tables():
    """The scratch function table: stock skills entries under every argc; returns (entries, bytes)."""
    ent = [(SK_MIN, 2), (SK_MAX, 2), (SK_RAND, 2), (SK_MIN, 0), (SK_MAX, 1), (SK_MIN, 3), (SK_MAX, 4),
           (SK_MIN, M32), (SK_SKLVL, 3), (SK_RAND, 3), (SK_MAX, 0x80000002), (SK_MAX, 1)]
    raw = b"".join(le32(f) + le32(a) for f, a in ent)
    return [(FNKIND[f], a) for f, a in ent], raw


def eval_cases(rnd):
    """Configurations: varFn NULL / identity / skills reader; tables: none, stock skills (n 7), stock missiles (4),
    stock items (4), scratch (12 entries, every argc)."""
    cases, exp = [], []
    scr_ent, scr_raw = eval_setup_tables()
    sk_ent, sk_n = stock_table(T_SKILLS, N_SKILLS)
    mi_ent, mi_n = stock_table(T_MISS, N_MISS)
    it_ent, it_n = stock_table(T_ITEMS, N_ITEMS)
    cv = CalcVarWorld(random.Random(7))
    mem = ["bytes %08x %s" % (FTAB, hx(scr_raw))] + cv.mem()

    configs = [
        ("none", 0, [], 0, None), ("ident", FN["IDENT"], [], 0, None),
        ("skills_tab", FN["IDENT"], sk_ent, sk_n, T_SKILLS), ("miss_tab", FN["IDENT"], mi_ent, mi_n, T_MISS),
        ("items_tab", FN["IDENT"], it_ent, it_n, T_ITEMS), ("scratch", FN["IDENT"], scr_ent, None, FTAB),
        ("skillsvar", FN["SkillsCalcVar"], scr_ent, None, FTAB),
    ]
    fixed = eval_fixed_programs()
    cfgs = {c[0]: c for c in configs}
    k = 0
    while len(exp) < 6000:
        tag = None
        if fixed:
            prog, cname, tag = fixed.pop(0)
            name, varfn, ent, n, tab = cfgs[cname]
            if n is None:
                n = len(ent)
        else:
            name, varfn, ent, n, tab = configs[k % len(configs)]
            k += 1
            prog = None
        if prog is None and name in ("scratch", "skillsvar"):
            n = rnd.choice([len(ent), len(ent), 0, 5, 9, 3, M32, 0x80000000, 100])
        okf = [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 200]        # sklvl (8) only in the fixed programs
        if name == "skills_tab":
            okf = [0, 1, 2, 7, 8, 9, 200]
        elif name in ("miss_tab", "items_tab"):
            okf = [0, 1, 2, 4, 5, 200]
        okf = [f for f in okf if f < len(ent) or f >= s32(n)]      # never an entry past the table's bytes
        if name == "skillsvar":
            okf = [f for f in okf if f not in (2, 9)]                 # ctx.unit is NULL here: no rand
        if prog is None:
            prog = rand_program(rnd, okf, True, rnd.choice([4, 12, 30, 60, 160, 300]),
                                CALCVAR_CODES if name == "skillsvar" else None)
        length = len(prog)
        r = rnd.random() if tag is None else 1.0
        if r < 0.15:
            length = rnd.randrange(0, len(prog) + 1)
        elif r < 0.18:
            length = rnd.choice([0, M32, 0x80000000, 0xFFFFFFF0])
        elif r < 0.22:
            length = len(prog) - 1
        ctx = rnd.choice([CTX, CTX, CTX, 0]) if name != "skillsvar" and tag is None else CTX
        words = [UNIT, cv.rnd_skill(), rnd.choice([0, 1, 5, 20, -3, 33])] if name == "skillsvar" or ctx else [UNIT, 0, 0]
        if name == "skillsvar":
            words[0] = 0            # the CalcVar model reads no unit; NULL keeps a unit read visible in the trace
        useed = (rnd.getrandbits(32), rnd.getrandbits(32))
        cseed = (rnd.getrandbits(32), rnd.getrandbits(32))
        env = EvalEnv({0: None, FN["IDENT"]: "ident", FN["SkillsCalcVar"]: "skills"}[varfn], ent, n, ctx,
                      useed, words, cv.calcvar)
        env.ctxseed = cseed
        try:
            eval_model(prog + bytes(8), length, env, collections.Counter())
        except (PowLimit, ZeroDivisionError, RecursionError):
            continue
        pad = prog + bytes(8)
        cases += ["w %08x %s" % (CODE, hx(pad)),
                  "w %08x %s" % (CTX, hx(le32(words[0]) + le32(words[1]) + le32(words[2]) + bytes(20) +
                                         le32(cseed[0]) + le32(cseed[1]))),
                  "w %08x %s" % (UNIT, hx(bytes(0x20) + le32(useed[0]) + le32(useed[1]))),
                  "d %08x 8" % (UNIT + 0x20), "d %08x 8" % (CTX + 0x20),
                  "call %08x 0 0 %08x %08x %08x %08x %08x %08x" % (FN["CALC_Eval"], CODE, length & M32, varfn,
                                                                  tab or 0, n & M32, ctx)]
        exp.append({"cfg": name, "prog": pad.hex(), "len": length & M32, "varfn": varfn, "n": n & M32,
                    "ctx": ctx, "words": words, "useed": useed, "cseed": cseed, "tag": tag})
    return cases, mem, {"cases": exp, "cv": cv.meta()}


def eval_fixed_programs():
    """Hand-made programs for the rarer statements: (bytes, configuration, tag)."""
    P = []
    # 65 pushes then sums: the 65th push is dropped (data-calc 4)
    P.append((bytes(sum(([7, (i % 120) + 1] for i in range(65)), [])) + bytes([0x10] * 70) + b"\0", "ident",
              "push65_sum"))
    P.append((bytes(sum(([7, 1] for i in range(64)), [])) + bytes([7, 99, 0]), "ident", "push65_top"))
    # rand in the unused branch of a ternary (data-calc 38): cond 0 ? rand(1,1000) : 7, and cond 1 ? 5 : rand
    P.append((bytes([7, 0, 7, 1, 9]) + struct.pack("<i", 1000) + bytes([1, 2, 7, 7, 0x16, 0]), "scratch",
              "rand_in_unused_then"))
    P.append((bytes([7, 1, 7, 5, 7, 1, 9]) + struct.pack("<i", 1000) + bytes([1, 2, 0x16, 0]), "scratch",
              "rand_in_unused_else"))
    P.append((bytes([7, 0, 7, 1, 9]) + struct.pack("<i", 1000) + bytes([1, 2, 7, 7, 0x16, 0]), "skills_tab",
              "rand_in_unused_then_stock"))
    # zero divisor (data-calc 39), ternary short (15)
    P.append((bytes([7, 9, 7, 0, 0x13, 0]), "ident", "div_zero"))
    P.append((bytes([9]) + struct.pack("<i", -2 ** 31) + bytes([7, 0, 0x13, 0]), "ident", "div_zero_min"))
    P.append((bytes([7, 3, 7, 4, 0x16, 0]), "ident", "ternary_two"))
    P.append((bytes([7, 3, 0x16, 0]), "ident", "ternary_one"))
    P.append((bytes([0x16, 0]), "ident", "ternary_none"))
    # missiles/items table: index 4 pushes 0 (data-calc 20); 0, 1, 2 are min, max, rand
    for t in ("miss_tab", "items_tab"):
        P.append((bytes([7, 3, 7, 9, 1, 4, 0]), t, t + "_idx4"))
        P.append((bytes([7, 3, 7, 9, 1, 4, 0x10, 0x10, 0]), t, t + "_idx4_args_stay"))
        P.append((bytes([7, 3, 7, 9, 1, 0, 7, 3, 7, 9, 1, 1, 0x10, 0]), t, t + "_min_max"))
        P.append((bytes([7, 3, 9]) + struct.pack("<i", 99999) + bytes([1, 2, 0]), t, t + "_rand"))
    # sklvl with par/lvl codes (argc 3)
    for sk in range(3):
        for v, w in ((16, 16), (8, 16), (16, 9), (15, 8), (0, 1)):
            P.append((bytes([7, sk, 7, v, 7, w, 1, 8, 0]), "scratch", "sklvl"))
    # every opcode as a lone byte, and each binary operator on wide operands
    for op in range(0x100):
        P.append((bytes([7, 5, op, 7, 6, 0]), "ident", "lone_op"))
    for op in range(0x0A, 0x15):
        P.append((bytes([9]) + struct.pack("<i", -5) + bytes([9]) + struct.pack("<i", 2 ** 31 - 1) + bytes([op, 0]),
                  "ident", "wide_%02X" % op))
        P.append((bytes([9]) + struct.pack("<i", 2 ** 31 - 1) + bytes([9]) + struct.pack("<i", -5) + bytes([op, 0]),
                  "ident", "wide_%02X" % op))
    for e in (-3, 0, 1, 2, 31, 32, 33):
        P.append((bytes([7, 3, 9]) + struct.pack("<i", e) + bytes([0x14, 0]), "ident", "pow_e%d" % e))
    # variables of every width through the identity reader, and a NULL reader
    P.append((bytes([4, 0xFF, 5]) + struct.pack("<h", -2) + bytes([6]) + struct.pack("<i", -7) + bytes([0x10, 0x10, 0]),
              "ident", "var_widths"))
    P.append((bytes([7, 3, 4, 0x80, 0x10, 0]), "none", "var_null"))
    return P


def eval_check(d):
    calls, reads, writes, meta = calls_by_case(d, "eval")
    rep = Report("eval")
    cv = CalcVarWorld.from_meta(meta["cv"])
    neg = 0
    for c, e in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        ent = {"none": [], "ident": []}.get(e["cfg"])
        if ent is None:
            if e["cfg"] in ("scratch", "skillsvar"):
                ent = eval_setup_tables()[0]
            else:
                ent = stock_table(*{"skills_tab": (T_SKILLS, N_SKILLS), "miss_tab": (T_MISS, N_MISS),
                                    "items_tab": (T_ITEMS, N_ITEMS)}[e["cfg"]])[0]
        res = []
        for variant in ("model", "neg"):
            env = EvalEnv({0: None, FN["IDENT"]: "ident", FN["SkillsCalcVar"]: "skills"}[e["varfn"]], ent, e["n"],
                          e["ctx"], tuple(e["useed"]), e["words"], cv.calcvar)
            env.ctxseed = tuple(e["cseed"])
            tr = collections.Counter()
            try:
                v = eval_model(bytes.fromhex(e["prog"]), e["len"], env, tr if variant == "model" else None,
                               divfix=(variant == "model"), stack=64 if variant == "model" else 65)
            except PowLimit:
                v = None
            res.append(((v if v is None else v & M32), env.seed, env.ctxseed, tr))
        got = None
        if "eax" in c:
            got = (c["eax"], struct.unpack("<II", c["dumps"][0][1]), struct.unpack("<II", c["dumps"][1][1]))
        want = (res[0][0], tuple(res[0][1]), tuple(res[0][2]))
        if got != want or c.get("pop") != 24:
            rep.bad("case %d cfg=%s: got %r want %r pop=%r" % (c["n"], e["cfg"], got, want, c.get("pop")))
        else:
            rep.c["match"] += 1
            rep.branches.update(res[0][3])
            if e.get("tag"):
                rep.branches["fixed_" + e["tag"]] += 1
                if e["tag"].startswith("rand_in_unused") and got[1] != tuple(e["useed"]):
                    rep.branches["fixed_rand_in_unused_drew"] += 1
        if got != (res[1][0], tuple(res[1][1]), tuple(res[1][2])):
            neg += 1
    declared = [RS_CALC_JT,
                (T_SKILLS, T_SKILLS + 56, "r", "g_SkillsCalcFuncs 0x00745774"),
                (N_SKILLS, N_SKILLS + 4, "r", "g_nSkillsCalcFuncs 0x007457AC"),
                (T_MISS, T_MISS + 32, "r", "g_MissCalcFuncs 0x00745828"),
                (T_ITEMS, T_ITEMS + 32, "r", "g_ItemCalcFuncs 0x0074463C"),
                (0x00646ABC, 0x00646ABC + 4 * 0x49, "r", "SKILLS_CalcVar jump table 0x00646ABC, codes 0-72 (.text)")]
    account(rep, reads, writes, declared)
    return finish(rep, neg)


# =============================================================================================== family: calcvar
class CalcVarWorld:
    """A scratch DataTables (g_pDataTables -> DT) with skills, skilldesc and missiles records and a skillscode pool,
    and a model of fn:SKILLS_CalcVar@0x00646460 for the codes that read only the records (and, through the formula
    codes, CALC_Eval with the skills reader and the stock skills function table)."""
    NSK, NSD, NMI = 24, 10, 12
    FORMULA = {54: 0x60, 55: 0x138, 56: 0x13C, 57: 0x140, 58: 0x144, 59: 0x64, 60: 0x68, 61: 0x6C, 62: 0x70,
               63: 0x74, 64: 0x78, 65: 0x7C, 66: 0xA4, 67: 0xA8, 68: 0xAC, 69: 0xB0, 70: 0xB4, 71: 0xC0, 72: 0x170}
    SAFE_VARS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 21, 22, 35, 36, 37, 42]

    def __init__(self, rnd=None):
        if rnd is None:
            return
        self.sk = [bytearray(rnd.getrandbits(8) for _ in range(0x23C)) for _ in range(self.NSK)]
        self.sd = [bytearray(rnd.getrandbits(8) for _ in range(0x120)) for _ in range(self.NSD)]
        self.mi = [bytearray(rnd.getrandbits(8) for _ in range(0x1A4)) for _ in range(self.NMI)]
        progs = []
        pool = bytearray()
        for _ in range(60):
            progs.append(len(pool))
            pool += self._formula(rnd)
        self.pool = bytes(pool)
        for i, r in enumerate(self.sk):
            # parameters: mostly small, some wide
            for k in range(8):
                v = rnd.choice([rnd.randrange(-50, 300), rnd.getrandbits(32), 0, 1])
                struct.pack_into("<I", r, 0x148 + 4 * k, v & M32)
            r[0x188] = rnd.choice([0, 1, 4, 8, 0x1F, 0x20, 0x27, rnd.getrandbits(8)])
            struct.pack_into("<h", r, 0x18A, rnd.choice([rnd.randrange(-200, 200), rnd.randrange(-0x8000, 0x8000)]))
            struct.pack_into("<h", r, 0x18C, rnd.choice([rnd.randrange(-50, 50), rnd.randrange(-0x8000, 0x8000)]))
            struct.pack_into("<h", r, 0x194, rnd.choice([rnd.randrange(0, self.NSD)] * 4 + [-1, self.NSD, 0x7FFF]))
            for code, off in self.FORMULA.items():
                v = rnd.choice([rnd.choice(progs)] * 6 + [M32, len(self.pool), len(self.pool) - 1, 0x80000000])
                struct.pack_into("<I", r, off, v & M32)
        for r in self.sd:
            for k in range(3):
                struct.pack_into("<h", r, 0x3C + 2 * k, rnd.choice([rnd.randrange(0, self.NMI)] * 4 + [-1, self.NMI]))
        for r in self.mi:
            struct.pack_into("<h", r, 0x96, rnd.randrange(-0x8000, 0x8000))
            struct.pack_into("<h", r, 0x98, rnd.choice([rnd.randrange(-20, 20), rnd.randrange(-0x8000, 0x8000)]))

    def _formula(self, rnd):
        out = bytearray()
        n = rnd.randrange(1, 5)
        for i in range(n):
            if rnd.random() < 0.6:
                out += bytes([4, rnd.choice(self.SAFE_VARS)])
            else:
                out += bytes([7, rnd.getrandbits(8)])
            if i:
                out.append(rnd.choice([0x10, 0x11, 0x12, 0x10]))
        if rnd.random() < 0.3:
            out += bytes([4, 16, 1, rnd.choice([0, 1])])        # min/max(x, lvl)
        out.append(0)
        return bytes(out)

    def meta(self):
        return {"sk": [r.hex() for r in self.sk], "sd": [r.hex() for r in self.sd], "mi": [r.hex() for r in self.mi],
                "pool": self.pool.hex()}

    @classmethod
    def from_meta(cls, m):
        w = cls()
        w.sk = [bytes.fromhex(x) for x in m["sk"]]
        w.sd = [bytes.fromhex(x) for x in m["sd"]]
        w.mi = [bytes.fromhex(x) for x in m["mi"]]
        w.pool = bytes.fromhex(m["pool"])
        return w

    def rnd_skill(self, rnd=random):
        return rnd.randrange(0, self.NSK)

    def mem(self):
        dt = bytearray(0x1000)
        struct.pack_into("<III", dt, 0x40, POOL, len(self.pool), len(self.pool))
        struct.pack_into("<I", dt, 0xB98, SKREC)
        struct.pack_into("<I", dt, 0xBA0, self.NSK)
        struct.pack_into("<I", dt, 0xB8C, SDREC)
        struct.pack_into("<I", dt, 0xB94, self.NSD)
        struct.pack_into("<I", dt, 0xB64, MIREC)
        struct.pack_into("<I", dt, 0xB6C, self.NMI)
        return ["dword %08x %08x" % (G_PDATATABLES, DT), "bytes %08x %s" % (DT, hx(dt)),
                "bytes %08x %s" % (SKREC, hx(b"".join(self.sk))), "bytes %08x %s" % (SDREC, hx(b"".join(self.sd))),
                "bytes %08x %s" % (MIREC, hx(b"".join(self.mi))), "bytes %08x %s" % (POOL, hx(self.pool))]

    def calcvar(self, unit, code, skill, lvl, depth=0, neg=False):
        skill, lvl = s32(skill), s32(lvl)
        code &= 0xFF
        if skill < 0 or skill >= self.NSK:
            return 0
        r = self.sk[skill]
        P = lambda n: s32(struct.unpack_from("<I", r, 0x148 + 4 * (n - 1))[0])  # noqa: E731
        if code in (0, 2, 4, 6):
            a = code + 1
            return 0 if lvl < 1 else s32(P(a) + s32((lvl - 1) * P(a + 1)))
        if code in (1, 3, 5):
            a = code
            return 0 if lvl < 1 else dimret(lvl, P(a), P(a + 1))
        if code == 7:
            if neg and lvl < 1:
                return 0
            return dimret(lvl, P(7), P(8))
        if 8 <= code <= 15:
            return P(code - 7)
        if code == 16:
            return lvl
        if code in (21, 22, 42):
            if lvl < 1:
                return 0
            x = s32(s16(struct.unpack_from("<H", r, 0x18C)[0]) * (lvl - 1) + s16(struct.unpack_from("<H", r, 0x18A)[0]))
            sh = r[0x188] & 0x1F
            if code == 21:
                return s32(x << sh) >> 8
            if code == 42:
                return s32(x << sh)
            return s32(cdiv(s32(x * 0x19), 2) << sh) >> 8
        if code in (35, 36, 37):
            sdi = s16(struct.unpack_from("<H", r, 0x194)[0])
            if not (0 <= sdi < self.NSD):
                return 0
            m = s16(struct.unpack_from("<H", self.sd[sdi], 0x3C + 2 * (code - 35))[0])
            if not (0 <= m < self.NMI):
                return 0
            mr = self.mi[m]
            return s32(s16(struct.unpack_from("<H", mr, 0x98)[0]) * lvl + s16(struct.unpack_from("<H", mr, 0x96)[0]))
        if code in self.FORMULA:
            off = struct.unpack_from("<I", r, self.FORMULA[code])[0]
            if off >= len(self.pool):
                return 0
            if depth > 6:
                raise RecursionError
            env = EvalEnv("skills", SKILLS_TABLE, 7, 1, None, [unit, skill, lvl],
                          lambda u, c, s, l: self.calcvar(u, c, s, l, depth + 1, neg))
            return eval_model(self.pool[off:] + bytes(8), len(self.pool) - off, env)
        if code > 72:
            return 0
        raise ValueError("code %d not modelled" % code)


def dimret(lvl, a, b):
    """fn:SKILLS_DimReturns@0x00645B20 (each step wraps at 32 bits)."""
    if s32(lvl + 6) == 0:
        raise ZeroDivisionError
    q = cdiv(s32(lvl * 110), s32(lvl + 6))
    r = s32(cdiv(s32(q * s32(b - a)), 100) + a)
    return b if r > b else r


CALCVAR_CODES = CalcVarWorld.SAFE_VARS + list(CalcVarWorld.FORMULA) + [73, 100, 0xFF]


def calcvar_cases(rnd):
    cv = CalcVarWorld(random.Random(11))
    cases, exp = [], []
    lvls = [0, 1, 2, 5, 20, 21, 40, 99, -1, -5, 0x7FFFFFFF, -0x80000000, 1000]
    while len(exp) < 5000:
        code = rnd.choice(CALCVAR_CODES)
        skill = rnd.choice([rnd.randrange(0, cv.NSK)] * 8 + [-1, cv.NSK, 0x7FFFFFFF])
        lvl = rnd.choice(lvls + [rnd.randrange(-10, 120)] * 3)
        if s32(lvl + 6) == 0:
            continue
        hi = rnd.choice([0, 0, rnd.getrandbits(24) << 8])     # garbage above the code byte
        try:
            cv.calcvar(0, code, skill, lvl)
        except (ZeroDivisionError, RecursionError, PowLimit):
            continue
        cases.append("call %08x 0 0 0 %08x %08x %08x" % (FN["SKILLS_CalcVar"], (code | hi) & M32, skill & M32,
                                                           lvl & M32))
        exp.append([code, skill, lvl])
    return cases, cv.mem(), {"cases": exp, "cv": cv.meta()}


def calcvar_check(d):
    calls, reads, writes, meta = calls_by_case(d, "calcvar")
    rep = Report("calcvar")
    cv = CalcVarWorld.from_meta(meta["cv"])
    neg = 0
    for c, (code, skill, lvl) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        want = cv.calcvar(0, code, skill, lvl) & M32
        if "eax" not in c or c["eax"] != want or c["pop"] != 16:
            rep.bad("case %d code=%d skill=%d lvl=%d: got %r want %08x" % (c["n"], code, s32(skill), s32(lvl),
                                                                         c.get("eax"), want))
        else:
            rep.c["match"] += 1
            tag = "code%d" % code if code <= 72 else "code_gt72"
            if not (0 <= s32(skill) < cv.NSK):
                tag = "skill_out_of_range"
            elif s32(lvl) < 1:
                tag += "_lvl_lt1"
            rep.branches[tag] += 1
        if (cv.calcvar(0, code, skill, lvl, neg=True) & M32) != c.get("eax"):
            neg += 1
    declared = [RS_CALC_JT, (T_SKILLS, T_SKILLS + 56, "r", "g_SkillsCalcFuncs 0x00745774"),
                (N_SKILLS, N_SKILLS + 4, "r", "g_nSkillsCalcFuncs 0x007457AC"),
                (0x00646ABC, 0x00646ABC + 4 * 0x49, "r", "SKILLS_CalcVar jump table 0x00646ABC, codes 0-72 (.text)")]
    account(rep, reads, writes, declared)
    return finish(rep, neg)


# =============================================================================================== family: entry
ENTRY = [("SKILLS_EvalCalc", 0x40), ("SKILLS_EvalDescCalc", 0x4C), ("ITEMS_EvalCalc", 0x98), ("MISS_EvalCalc", 0x60)]


def entry_cases(rnd):
    cases, exp = [], []
    progs = bytearray()
    starts = []
    for _ in range(40):
        starts.append(len(progs))
        progs += rand_program(rnd, [200], False, rnd.choice([4, 10, 30]))
    pool = bytes(progs)
    for k in range(1600):
        fn, poolfield = ENTRY[k % 4]
        nul = rnd.random() < 0.08
        size = len(pool)
        off = rnd.choice([rnd.choice(starts)] * 5 + [0, size - 1, size, size + 1, M32, 0x80000000, 0x7FFFFFFF,
                                                    rnd.getrandbits(32)])
        dt = bytearray(0x100)
        struct.pack_into("<II", dt, poolfield, 0 if nul else POOL, size)
        if fn == "MISS_EvalCalc":
            args = [0, 0, off, rnd.randrange(0, 5), rnd.randrange(0, 30)]
        elif fn == "ITEMS_EvalCalc":
            args = [0, 0, off]
        else:
            args = [0, off, 0, rnd.randrange(0, 30)]
        try:
            v = entry_model(pool, 0 if nul else POOL, size, off)
        except PowLimit:
            continue
        cases += ["w %08x %s" % (DT, hx(dt)),
                  "call %08x 0 0 %s" % (FN[fn], " ".join("%08x" % (a & M32) for a in args))]
        exp.append([fn, nul, off, v & M32, 4 * len(args)])
    return cases, ["dword %08x %08x" % (G_PDATATABLES, DT), "bytes %08x %s" % (POOL, hx(pool))], \
        {"cases": exp, "pool": pool.hex()}


def entry_model(pool, buf, size, off):
    if not buf or off >= size:      # unsigned: -1 is past the end
        return 0
    env = EvalEnv(None, [], 0, 0)
    return eval_model(pool[off:] + bytes(8), size - off, env)


def entry_check(d):
    calls, reads, writes, meta = calls_by_case(d, "entry")
    rep = Report("entry")
    pool = bytes.fromhex(meta["pool"])
    neg = 0
    for c, (fn, nul, off, v, pop) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        if "eax" not in c or c["eax"] != v or c["pop"] != pop:
            rep.bad("case %d %s off=%08x: got %r want %08x" % (c["n"], fn, off, c.get("eax"), v))
        else:
            rep.c["match"] += 1
            rep.branches["%s_%s" % (fn, "null_pool" if nul else "off_ge_size" if off >= len(pool) else "eval")] += 1
        try:        # negative control: no pool test, offset taken modulo the size
            alt = eval_model(pool[off % len(pool):] + bytes(8), len(pool) - off % len(pool), EvalEnv(None, [], 0, 0))
        except (PowLimit, KeyError, ValueError):
            alt = None
        neg += alt is None or (alt & M32) != c.get("eax")
    declared = [RS_CALC_JT]
    for t, n in ((T_SKILLS, N_SKILLS), (T_MISS, N_MISS), (T_ITEMS, N_ITEMS)):
        declared += [(t, t + 56, "r", "function table 0x%08X" % t), (n, n + 4, "r", "function count 0x%08X" % n)]
    account(rep, reads, writes, declared)
    return finish(rep, neg)


# =============================================================================================== family: excel
LINK = 0x10300000       # an excel link {count, capacity, array, root}
LARR = 0x10301000       # its {u32 code, s32 index} array
NODES = 0x10310000      # name-tree nodes, 0x30 apart: char name[32] +0x00, index +0x20, left +0x24, right +0x28
NAMEBUF = 0x10320000
LOWER = 0x006CEB98      # STR_ToLowerN's table, indexed by a signed char


def findcode_model(arr, code, neg=False):
    lo, hi = 0, len(arr)
    if hi <= 0:
        return -1
    while True:
        mid = (hi - lo) // 2 + lo
        c = arr[mid][0]
        if (s32(c) < s32(code)) if neg else (c < code):
            lo = mid + 1
            mid = hi
        elif c == code:
            return arr[mid][1]
        hi = mid
        if not lo < mid:
            return -1


def addcode_model(arr, code, neg=False):
    """-> (returned index, new array). arr: list of [code, index]; count = len(arr)."""
    arr = [list(x) for x in arr]
    while True:
        lo, hi = 0, len(arr)
        found = False
        while True:
            if hi <= lo:
                break
            mid = (hi - lo) // 2 + lo
            u = arr[mid][0]
            if code <= u:
                hi = mid
                if not code < u:
                    found = True
                    break
                continue
            lo = mid + 1
        if not found:
            arr.insert(lo, [code, len(arr)])
            return arr[lo][1], arr
        if neg:
            return arr[mid][1], arr       # a FindCode-like reuse of the duplicate instead of code + 1
        code = (code + 1) & M32


def lower_key(name):
    """FindName's key: the first 31 bytes (strncpy to char[32], NUL at [31]), through the signed-char table."""
    tab = img_bytes(LOWER - 128, 256)
    k = bytearray()
    for b in name[:31]:
        if b == 0:
            break
        k.append(tab[(b - 256 if b >= 128 else b) + 128])
    return bytes(k)


def cstrcmp(a, b):
    """strcmp on byte strings that end at their first NUL: -1, 0, 1."""
    a = a.split(b"\0")[0]
    b = b.split(b"\0")[0]
    return (a > b) - (a < b)


def findname_model(nodes, root, name, cut=31):
    key = lower_key(name) if cut == 31 else lower_key(name[:cut])
    n = root
    while n is not None:
        r = cstrcmp(key, nodes[n]["name"])
        if r == 0:
            return nodes[n]["index"]
        n = nodes[n]["left"] if r < 0 else nodes[n]["right"]
    return -1


def rand_code(rnd):
    r = rnd.random()
    if r < 0.4:
        return struct.unpack("<I", bytes(rnd.choice(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJ0123456789 ")
                                         for _ in range(4)))[0]
    if r < 0.6:
        return rnd.getrandbits(32) | 0x80000000
    return rnd.getrandbits(32)


def excel_cases(rnd):
    cases, exp = [], []
    # FindCode: sorted and unsorted arrays, codes >= 2^31, case variants
    for k in range(2500):
        n = rnd.choice([0, 1, 2, 3, 7, 16, 50, 200, rnd.randrange(1, 300)])
        codes = [rand_code(rnd) for _ in range(n)]
        if rnd.random() < 0.8:
            codes.sort()
        arr = [[c, rnd.choice([i, rnd.getrandbits(32)])] for i, c in enumerate(codes)]
        r = rnd.random()
        variant = False
        if arr and r < 0.5:
            probe = rnd.choice(arr)[0]
        elif arr and r < 0.7:          # the same letters in another case
            b = struct.pack("<I", rnd.choice(arr)[0])
            b = bytes(x ^ 0x20 if chr(x).isascii() and chr(x).isalpha() else x for x in b)
            probe = struct.unpack("<I", b)[0]
            variant = probe not in codes
        else:
            probe = rand_code(rnd)
        cnt = n if rnd.random() < 0.95 else rnd.choice([-1, -5])
        raw = b"".join(le32(c) + le32(i) for c, i in arr)
        cases += ["w %08x %s" % (LINK, hx(le32(cnt) + le32(n + 4) + le32(LARR) + le32(0))),
                  ("w %08x %s" % (LARR, hx(raw))) if raw else "s %08x 0" % LARR,
                  "call %08x 0 0 %08x %08x %08x" % (FN["EXCEL_FindCode"], LINK, probe, rnd.getrandbits(32))]
        exp.append(["find", arr if cnt >= 0 else [], probe, cnt, variant])
    # AddCode: insert into sorted arrays, duplicates bump to code + 1 (chains, wrap at 2^32)
    for k in range(1500):
        n = rnd.choice([0, 1, 2, 5, 20, 60, rnd.randrange(0, 120)])
        codes = sorted(set(rand_code(rnd) for _ in range(n)))
        r = rnd.random()
        if codes and r < 0.4:
            probe = rnd.choice(codes)
            for j in range(rnd.randrange(0, 4)):          # a chain of taken successors
                if (probe + j + 1) & M32 not in codes:
                    codes.append((probe + j + 1) & M32)
            codes.sort()
        elif r < 0.5:
            probe = M32
            codes = sorted(set(codes + [M32, 0]))
        else:
            probe = rand_code(rnd)
        if rnd.random() < 0.15:
            rnd.shuffle(codes)                             # unsorted: the probe path is exact
        arr = [[c, i] for i, c in enumerate(codes)]
        n = len(arr)
        raw = b"".join(le32(c) + le32(i) for c, i in arr) + bytes(16)
        cases += ["w %08x %s" % (LINK, hx(le32(n) + le32(n + 8) + le32(LARR) + le32(0))),
                  "w %08x %s" % (LARR, hx(raw)), "d %08x 16" % LINK, "d %08x %d" % (LARR, 8 * (n + 2)),
                  "call %08x 0 0 %08x %08x" % (FN["EXCEL_AddCode"], LINK, probe)]
        exp.append(["add", arr, probe, n])
    # FindName: random trees; names past 31 bytes, upper case, bytes >= 0x80
    alpha = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-'\xe9\xc0\x80\xff"
    for k in range(1500):
        nn = rnd.choice([1, 2, 5, 15, 40])
        names = []
        for _ in range(nn):
            ln = rnd.choice([rnd.randrange(0, 12), 31, 30, 32, rnd.randrange(0, 32)])
            names.append(lower_key(bytes(rnd.choice(alpha) for _ in range(ln))))
        nodes = []
        root = None
        for i, nm in enumerate(names):          # BST insert by the same compare (duplicates go right)
            nodes.append({"name": nm, "index": rnd.choice([i, rnd.getrandbits(32)]), "left": None, "right": None})
            if root is None:
                root = 0
                continue
            cur = root
            while True:
                side = "left" if cstrcmp(nm, nodes[cur]["name"]) < 0 else "right"
                if nodes[cur][side] is None:
                    nodes[cur][side] = i
                    break
                cur = nodes[cur][side]
        r = rnd.random()
        base = rnd.choice(names)
        if r < 0.35:
            q = bytes(base)
        elif r < 0.55:          # the stored name in mixed case
            q = bytes(x ^ 0x20 if 0x61 <= x <= 0x7A and rnd.random() < 0.5 else x for x in base)
        elif r < 0.8:           # a longer key whose first 31 bytes are a stored 31-byte name, or one past 31
            q = (base + bytes(rnd.choice(alpha) for _ in range(31)))[:31] + bytes(rnd.choice(alpha)
                                                                               for _ in range(rnd.randrange(1, 20)))
            q = q.replace(b"\0", b"a")
        else:
            q = bytes(rnd.choice(alpha) for _ in range(rnd.randrange(0, 40)))
        raw = bytearray()
        for nd in nodes:
            nb = bytearray(0x30)
            nb[:len(nd["name"])] = nd["name"]
            struct.pack_into("<III", nb, 0x20, nd["index"] & M32,
                             0 if nd["left"] is None else NODES + 0x30 * nd["left"],
                             0 if nd["right"] is None else NODES + 0x30 * nd["right"])
            raw += nb
        empty = rnd.random() < 0.05
        cases += ["w %08x %s" % (LINK, hx(le32(0 if empty else nn) + le32(0) + le32(0) +
                                          le32(0 if empty else NODES))),
                  "w %08x %s" % (NODES, hx(raw)), "w %08x %s" % (NAMEBUF, hx(q + b"\0")), "s %08x 96" % NAMEBUF,
                  "call %08x 0 0 %08x %08x %08x" % (FN["EXCEL_FindName"], LINK, NAMEBUF, rnd.getrandbits(32))]
        exp.append(["name", [{"name": nd["name"].hex(), "index": nd["index"], "left": nd["left"],
                              "right": nd["right"]} for nd in nodes], None if empty else 0, q.hex()])
    return cases, ["dword %08x %08x" % (COOKIE, 0xBB40E64E)], {"cases": exp}


def excel_check(d):
    calls, reads, writes, meta = calls_by_case(d, "excel")
    rep = Report("excel")
    neg = 0
    for c, e in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        kind = e[0]
        if kind == "find":
            arr, probe, cnt = e[1], e[2], e[3]
            want = findcode_model(arr, probe) & M32
            ok = "eax" in c and c["eax"] == want and c["pop"] == 12
            neg += findcode_model(arr, probe, neg=True) & M32 != c.get("eax")
            if ok:
                rep.branches["find_hit" if s32(want) >= 0 else "find_miss"] += 1
                rep.branches["find_probe_ge_2^31"] += probe >= 0x80000000
                rep.branches["find_unsorted"] += [x[0] for x in arr] != sorted(x[0] for x in arr)
                rep.branches["find_case_variant_miss"] += e[4] and s32(want) == -1
                rep.branches["find_negative_count"] += e[3] < 0
        elif kind == "add":
            arr, probe, n = e[1], e[2], e[3]
            ret, new = addcode_model(arr, probe)
            wl = le32(n + 1) + le32(n + 8) + le32(LARR) + le32(0)
            wa = b"".join(le32(x) + le32(y) for x, y in new) + bytes(8 * (n + 2) - 8 * len(new))
            got = (c.get("eax"), c["dumps"][0][1], c["dumps"][1][1][:len(wa)]) if "eax" in c else None
            ok = got == (ret & M32, wl, wa) and c["pop"] == 8
            r2, new2 = addcode_model(arr, probe, neg=True)
            neg += (r2 & M32, b"".join(le32(x) + le32(y) for x, y in new2)) != (c.get("eax"), got and got[2][:8 * len(new2)])
            if ok:
                bumped = [x[0] for x in new if x[1] == n][0] != probe
                rep.branches["add_bumped" if bumped else "add_plain"] += 1
                rep.branches["add_wrapped"] += bumped and [x[0] for x in new if x[1] == n][0] < probe
                rep.branches["add_unsorted"] += [x[0] for x in arr] != sorted(x[0] for x in arr)
        else:
            nodes = [dict(x, name=bytes.fromhex(x["name"])) for x in e[1]]
            q = bytes.fromhex(e[3])
            want = findname_model(nodes, e[2], q) & M32
            ok = "eax" in c and c["eax"] == want and c["pop"] == 12
            neg += findname_model(nodes, e[2], q.lower() if False else q, cut=32) & M32 != c.get("eax")
            if ok:
                rep.branches["name_hit" if s32(want) != -1 or any(nd["index"] == M32 for nd in nodes)
                             else "name_miss"] += 1
                rep.branches["name_key_over_31"] += len(q.split(b"\0")[0]) > 31
                rep.branches["name_key_over_31_hit"] += len(q.split(b"\0")[0]) > 31 and s32(want) != -1
                rep.branches["name_mixed_case"] += q != q.lower()
                rep.branches["name_empty_link"] += e[2] is None
        if ok:
            rep.c["match"] += 1
        else:
            rep.bad("case %d %s: got %r" % (c["n"], kind, {k: v for k, v in c.items() if k != "dumps"}))
    account(rep, reads, writes, excel_readset())
    return finish(rep, neg)


def excel_readset():
    return [(LOWER - 128, LOWER + 128, "r", "STR_ToLowerN table 0x006CEB18..0x006CEC17 (.rdata, signed-char index)"),
            (0x00683900, 0x00683C00, "r", "memmove's jump tables 0x00683950..0x00683B5F (.text)"),
            (0x007788D8, 0x007788DC, "w", "strncpy 0x004135D0's store to 0x007788D8 (written only)")]

# =============================================================================================== family: lang
LANGTAB = 0x007303DC    # g_LanguageTable: 13 entries of 0x18 bytes {code, +4, +8 strings; +0xC fourcc; +0x10 id}
LANG_FLAG, LANG_IDX = 0x008829F0, 0x008829EC
OUT = 0x10330000


def cstr_at(va):
    off = S4.va_off(va)
    d = S4.image()[0]
    return d[off:d.index(b"\0", off)] + b"\0"


def lang_model(idx, mode, neg=False):
    """-> (entry, the bytes written to the buffer, or None when the source pointer is outside the image)."""
    idx = s32(idx)
    e = 0
    if idx < 14:
        e = 0
        while e < 13 and s32(S4.dword(LANGTAB + 0x18 * e + 0x10)) != idx:
            e += 1
        if e >= 14 or (neg and e == 13):
            e = 0
    base = LANGTAB + 0x18 * e
    field = {1: 4, 2: 8, 3: 0xC}.get(s32(mode), 0)
    if field == 0xC:
        return e, le32(S4.dword(base + 0xC))
    ptr = S4.dword(base + field)
    if S4.section_of(ptr) is None:
        return e, None
    return e, cstr_at(ptr)


def lang_cases(rnd):
    cases, exp = [], []
    idxs = list(range(-2, 20)) + [0x7FFFFFFF, 0x80000000, 255, 100]
    for idx in idxs:
        for mode in (0, 1, 2, 3, 4, -1, 7):
            pre = bytes(rnd.getrandbits(8) for _ in range(16))
            cases += ["w %08x %s" % (OUT, hx(pre)), "w %08x %s" % (LANG_IDX, hx(le32(idx))), "d %08x 16" % OUT,
                      "call %08x 0 0 %08x %08x" % (FN["LNG_GetLanguageCode"], OUT, mode & M32)]
            exp.append([idx & M32, mode & M32, pre.hex()])
    return cases, ["bytes %08x 01" % LANG_FLAG], {"cases": exp}


def lang_check(d):
    calls, reads, writes, meta = calls_by_case(d, "lang")
    rep = Report("lang")
    neg = 0
    for c, (idx, mode, pre) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        e, w = lang_model(idx, mode)
        got = c["dumps"][0][1] if "eax" in c else None
        if w is None:       # entry 13: a pointer made of string bytes; the game faults on the copy
            ok = got is not None and c["pop"] == 8
            rep.branches["entry13_wild_pointer"] += ok
        else:
            ok = got is not None and got[:len(w)] == w and got[len(w):] == bytes.fromhex(pre)[len(w):] and \
                c["pop"] == 8
            rep.branches["entry%d" % e] += ok
        rep.c["match"] += ok
        if not ok:
            rep.bad("case %d idx=%d mode=%d: got %r want %r" % (c["n"], s32(idx), s32(mode), got, w))
        e2, w2 = lang_model(idx, mode, neg=True)
        neg += (w2 is None) != (w is None) or (w2 is not None and got[:len(w2)] != w2)
    declared = [(LANGTAB, LANGTAB + 13 * 0x18, "r", "g_LanguageTable 0x007303DC, 13 entries (.data)"),
                (LANGTAB + 13 * 0x18, LANGTAB + 14 * 0x18, "r",
                 "entry 13 = the 0x18 bytes after the table, 0x00730514 (dwords 'M' 'B' 'T', then g_szNotXlatedSuffix)"),
                (0x006CC000, 0x00704A10, "r", "the language strings (.rdata)"),
                (0x40, 0x60, "r", "entry 13's string pointers 0x4D, 0x42, 0x54 (NULL page: the game faults)")]
    account(rep, reads, writes, declared)
    return finish(rep, neg)

# =============================================================================================== family: strings
G_STR, G_STRTXT, G_PATTXT, G_EXPTXT, G_PAT, G_EXP = 0x008829B4, 0x008829B8, 0x008829BC, 0x008829C0, 0x008829D0, \
    0x008829D4
G_EMPTY, G_NXLIST, G_FONTMAP = 0x008829E8, 0x008829B0, 0x00882B2C
TBLBASE, TXABASE, TXTBASE = 0x12000000, 0x10400000, 0x11000000
NXNODES, KEYBUF = 0x10500000, 0x10510000
STRTABLES = ["string", "patchstring", "expansionstring", "syn-patch600", "syn-string520", "syn-exp700"]
WORLDS = {"stock": (0, 1, 2), "noexp": (0, 1, None), "stringonly": (0, None, None),
          "smallpatch_noexp": (0, 3, None), "small_all": (4, 3, 5), "small_string_noexp": (4, 1, None)}


def build_tbl(pairs):
    """A .tbl image (fmt:tbl) of (key, value) byte pairs: hash_size = count + 2, signed ELF home slot, linear probing."""
    import tbl as TBL
    n = len(pairs)
    hs = n + 2
    slots = [None] * hs
    longest = 0
    for e, (k, v) in enumerate(pairs):
        s, probes = TBL.elf_hash_signed(k) % hs, 1
        while slots[s] is not None:
            s, probes = (s + 1) % hs, probes + 1
        slots[s] = e
        longest = max(longest, probes)
    start = 0x15 + 2 * n + 17 * hs
    area = bytearray()
    node_of = {e: s for s, e in enumerate(slots) if e is not None}
    offs = {}
    for e, (k, v) in enumerate(pairs):
        ko = start + len(area)
        area += k + b"\0"
        so = start + len(area)
        area += v + b"\0"
        offs[e] = (ko, so, len(v) + 1)
    out = bytearray(struct.pack("<HHIBIII", 0, n, hs, 1, start, longest, start + len(area)))
    out += b"".join(struct.pack("<H", node_of[e]) for e in range(n))
    for s in range(hs):
        e = slots[s]
        if e is None:
            out += bytes(17)
        else:
            ko, so, sl = offs[e]
            out += struct.pack("<BHIIIH", 1, e, TBL.elf_hash_signed(pairs[e][0]) % hs, ko, so, sl)
    return bytes(out + area)


class StrWorld:
    def __init__(self, d):
        import tbl as TBL
        self.paths, self.t = [], []
        for k, name in enumerate(STRTABLES):
            if name.startswith("syn-"):
                cnt = int(re.sub(r"\D", "", name))
                pairs = [(b"syn%d_%04d" % (k, i), b"v%d" % i) for i in range(cnt)]
                path = os.path.join(d, name + ".tbl")
                if not os.path.exists(path) or open(path, "rb").read() != build_tbl(pairs):
                    os.makedirs(d, exist_ok=True)
                    open(path, "wb").write(build_tbl(pairs))
            else:
                path = os.path.join(ENG, name + ".tbl")
            self.paths.append(path)
            self.t.append(TBL.Tbl(path))

    def text(self, k, node):
        return TXTBASE + 0x100000 * k + 2 * node + 2

    def txa(self, k):
        t = self.t[k]
        used = {nd for nd, _, _ in t.entries}
        return b"".join(le32(self.text(k, n) if n in used else 0) for n in range(t.hash_size))

    def mem(self, d):
        out = []
        for k, path in enumerate(self.paths):
            out.append("const load %08x %s" % (TBLBASE + 0x1000000 * k, os.path.abspath(path)))
            tp = os.path.join(d, "txa%d.bin" % k)
            open(tp, "wb").write(self.txa(k))
            out.append("const load %08x %s" % (TXABASE + 0x40000 * k, os.path.abspath(tp)))
        return out

    def entry(self, k, e, neg=False):
        t = self.t[k]
        e &= 0xFFFF
        if e >= t.count:
            if neg:
                return ("fatal",)
            e = 500
        node = t.index[e] if e < t.count else struct.unpack_from("<H", t.data, 0x15 + 2 * e)[0]
        return ("text", k, node)

    def by_index(self, world, idx, neg=False):
        s, p, x = WORLDS[world]
        idx &= 0xFFFF
        if idx >= 20000:
            if x is not None:
                return self.entry(x, idx - 20000, neg)
            idx = 11078 if not neg else idx
        if p is not None and idx >= 10000:
            return self.entry(p, idx - 10000, neg)
        return self.entry(s, idx, neg)

    def find(self, k, key):
        import tbl as TBL
        t = self.t[k]
        slot = TBL.elf_hash_signed(key) % t.hash_size
        for _ in range(t.max_probes):
            used, entry, h, ko, so, sl = t.nodes[slot]
            if used == 1 and t.data[ko:t.data.index(b"\0", ko)] == key:
                return entry, self.text(k, slot)
            slot = (slot + 1) % t.hash_size
        return None, None

    def by_key(self, world, key, nx):
        s, p, x = WORLDS[world]
        if key == b"":
            return 0, G_EMPTY
        e, txt = self.find(p, key)
        if e is not None:
            return (10000 + e) & 0xFFFF, txt
        if x is not None:
            e, txt = self.find(x, key)
            if e is not None:
                return (20000 + e) & 0xFFFF, txt
        e, txt = self.find(s, key)
        if e is not None:
            return e, txt
        return 0, nx[key]


def strings_world_writes(world):
    s, p, x = WORLDS[world]
    w = []
    for g, gt, k in ((G_STR, G_STRTXT, s), (G_PAT, G_PATTXT, p), (G_EXP, G_EXPTXT, x)):
        w.append("w %08x %s" % (g, hx(le32(0 if k is None else TBLBASE + 0x1000000 * k))))
        w.append("w %08x %s" % (gt, hx(le32(0 if k is None else TXABASE + 0x40000 * k))))
    return w


def strings_cases(rnd, d=None):
    d = d or DEFDIR
    sw = StrWorld(d)
    cases, exp = [], []
    # the not-xlated cache: keys found in no table, each with its text, chained from G_NXLIST
    nxkeys = [b"S1eUnknownKey%d" % i for i in range(6)] + [b"funeralpire", b"zz\xe9z"]
    nx = {}
    raw = bytearray()
    keyarea = NXNODES + 0x100
    keys_raw = bytearray()
    for i, k in enumerate(nxkeys):
        kp = keyarea + len(keys_raw)
        keys_raw += k + b"\0"
        nx[k] = 0x13000000 + 0x10 * i
        nxt = 0 if i == len(nxkeys) - 1 else NXNODES + 12 * (i + 1)
        raw += le32(nx[k]) + le32(kp) + le32(nxt)
    mem = sw.mem(d) + ["dword %08x %08x" % (G_NXLIST, NXNODES), "bytes %08x %s" % (NXNODES, hx(raw)),
                       "bytes %08x %s" % (keyarea, hx(keys_raw)), "dword %08x 0" % G_FONTMAP,
                       "dword %08x %08x" % (COOKIE, 0x4E1C2B7A)]
    cnt = [t.count for t in sw.t]
    # GetByIndex
    for world in WORLDS:
        s, p, x = WORLDS[world]
        idxs = [0, 1, 499, 500, 501, cnt[s] - 1, cnt[s], cnt[s] + 1, 9999, 10000, 10001, 11078, 19999, 20000, 20001,
                21078, 65535, 0x4E1F, 0x4E20]
        if p is not None:
            idxs += [10000 + cnt[p] - 1, 10000 + cnt[p], 10000 + 1078]
        if x is not None:
            idxs += [20000 + cnt[x] - 1, 20000 + cnt[x]]
        idxs += [rnd.randrange(0, 65536) for _ in range(40)]
        for idx in idxs:
            hi = rnd.choice([0, 0, rnd.getrandbits(16) << 16])
            cases += strings_world_writes(world) + ["call %08x %08x 0" % (FN["STRTABLE_GetByIndex"], idx | hi)]
            exp.append(["idx", world, idx])
    # GetByKey and KeyToIndex
    stock_keys = []
    for k in (0, 1, 2):
        ents = sw.t[k].entries
        stock_keys += [ents[0][1], ents[-1][1]] + [ents[rnd.randrange(len(ents))][1] for _ in range(10)]
    for world in ("stock", "noexp", "small_string_noexp"):
        keys = stock_keys + nxkeys + [b"", b"WarrivAct1IntroGossip1"]
        if world == "small_string_noexp":       # the synthetic string table's entry 0, and its last key
            keys += [sw.t[4].entries[0][1], sw.t[4].entries[-1][1]]
        loaded = [t for t in WORLDS[world] if t is not None]     # a key found nowhere and not cached would allocate
        keys = [k for k in keys if k == b"" or k in nx or any(sw.find(t, k)[0] is not None for t in loaded)]
        for key in keys:
            for fn in ("STRTABLE_GetByKey", "STRTABLE_KeyToIndex"):
                pre = strings_world_writes(world) + ["w %08x %s" % (KEYBUF, hx(key + b"\0")), "s %08x 64" % KEYBUF]
                if fn == "STRTABLE_GetByKey":
                    cases += pre + ["w %08x %s" % (OUT, hx(le32(0xCCCCCCCC))), "d %08x 4" % OUT,
                                    "call %08x 0 0 %08x %08x" % (FN[fn], KEYBUF, OUT)]
                else:
                    cases += pre + ["call %08x %08x 0" % (FN[fn], KEYBUF)]
                exp.append([fn, world, key.hex()])
    # CharCount with no font map: strlen, whatever the limit
    for _ in range(300):
        st = bytes(rnd.randrange(1, 256) for _ in range(rnd.randrange(0, 60)))
        lim = rnd.choice([0, 1, len(st), len(st) + 5, rnd.getrandbits(32), 0x80000000])
        cases += ["w %08x %s" % (KEYBUF, hx(st + b"\0")), "s %08x 96" % KEYBUF,
                  "call %08x %08x %08x" % (FN["UNICODE_CharCount"], KEYBUF, lim)]
        exp.append(["count", st.hex(), lim])
    return cases, mem, {"cases": exp, "nx": {k.hex(): v for k, v in nx.items()}}


def strings_check(d):
    calls, reads, writes, meta = calls_by_case(d, "strings")
    rep = Report("strings")
    sw = StrWorld(d)
    nx = {bytes.fromhex(k): v for k, v in meta["nx"].items()}
    neg = 0
    for c, e in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        kind = e[0]
        if kind == "idx":
            world, idx = e[1], e[2]
            want = sw.by_index(world, idx)
            wv = sw.text(want[1], want[2])
            ok = "eax" in c and c["eax"] == wv and c["pop"] == 0
            alt = sw.by_index(world, idx, neg=True)
            neg += alt[0] == "fatal" or sw.text(alt[1], alt[2]) != c.get("eax")
            if ok:
                s, p, x = WORLDS[world]
                tag = "idx_%s_%s" % (world, STRTABLES[want[1]])
                if idx >= 20000 and x is None:
                    tag += "_via11078"
                k0 = want[1]
                ent = sw.t[k0].index.index(want[2]) if want[2] in sw.t[k0].index else None
                if ent == 500:
                    tag += "_entry500"
                rep.branches[tag] += 1
        elif kind == "count":
            st = bytes.fromhex(e[1])
            ok = "eax" in c and c["eax"] == len(st)
            neg += c.get("eax") != min(len(st), e[2])
            rep.branches["charcount_nofontmap"] += ok
        else:
            fn, world, key = kind, e[1], bytes.fromhex(e[2])
            idx, txt = sw.by_key(world, key, nx)
            if fn == "STRTABLE_GetByKey":
                ok = "eax" in c and c["eax"] & 0xFFFF == idx and c["dumps"][0][1] == le32(txt) and c["pop"] == 8
                neg += (c.get("eax", 0) & 0xFFFF) != (idx if idx else 0xFFFF)
            else:
                want = idx if idx else 5382
                ok = "eax" in c and c["eax"] & 0xFFFF == want and c["pop"] == 0
            if ok:
                where = "empty" if key == b"" else "notfound" if key in nx else "found%s" % (
                    "_entry0" if idx == 0 else "")
                rep.branches["%s_%s_%s" % (fn.split("_")[1], world, where)] += 1
        rep.c["match"] += bool(ok)
        if not ok:
            rep.bad("case %d %r: got %r" % (c["n"], e[:3], {k: v for k, v in c.items()}))
    declared = [RS_COOKIE,
                (G_STR, G_STR + 4, "r", "g_pStringTbl"), (G_STRTXT, G_STRTXT + 12, "r", "g_*TblText")]
    account(rep, reads, writes, declared)
    return finish(rep, neg)

# =============================================================================================== family: compile
TEXTBUF, OUTBUF = 0x10600000, 0x10610000
STATLINK = 0x0096C800           # g_DataTables + 0xBD0: the itemstatcost name link the item ident callback reads
STATNODES = 0x10620000
ITEMPOOL = 0x10630000           # itemscode pool for the item cell callback (g_DataTables + 0x98/+0x9C/+0xA0)
RECBUF = 0x10640000
LOCALE_CHANGED = 0x0096DFE4     # __locale_changed (.bss); its one writer 0x006926F7 is in setlocale, never called
STAT_NAMES = [b"strength", b"dexterity", b"vitality", b"energy", b"item_armor_percent", b"hpregen", b"maxhp"]


class StatNames:
    """calc.py's Names, for the items context: the scratch itemstatcost name tree (FindName rules)."""

    def find_name(self, table, col, name):
        key = lower_key(name.encode("latin-1"))
        for i, n in enumerate(STAT_NAMES):
            if n == key:
                return i + 3
        return -1


def stat_tree_mem():
    nodes = sorted(range(len(STAT_NAMES)), key=lambda i: STAT_NAMES[i])

    def build(lo, hi):
        if lo >= hi:
            return None
        mid = (lo + hi) // 2
        return (nodes[mid], build(lo, mid), build(mid + 1, hi))
    tree = build(0, len(nodes))
    raw = bytearray(0x30 * len(STAT_NAMES))

    def emit(t):
        if t is None:
            return 0
        i, l, r = t
        nb = bytearray(0x30)
        nb[:len(STAT_NAMES[i])] = STAT_NAMES[i]
        struct.pack_into("<III", nb, 0x20, i + 3, emit(l), emit(r))
        raw[0x30 * i:0x30 * i + 0x30] = nb
        return STATNODES + 0x30 * i
    root = emit(tree)
    return ["dword %08x %08x" % (STATLINK, LINK), "bytes %08x %s" % (LINK, hx(le32(len(STAT_NAMES)) + le32(0) +
                                                                          le32(0) + le32(root))),
            "bytes %08x %s" % (STATNODES, hx(raw))]


def rand_expr(rnd, depth=0):
    r = rnd.random()
    if depth > 6 or r < 0.3:
        return rnd.choice([str(rnd.randrange(0, 200)), str(rnd.randrange(0, 2 ** 31)), "lvl", "par1", "x",
                           str(rnd.choice([2147483648, 4294967295, 99999999999])), "'quoted name'", ".dot",
                           "stat('strength'.base)", "stat('DexTerity'.mod)", "stat('nosuch'.accr)", "rand(1,5)"])
    if r < 0.45:
        return rnd.choice(["-", "- ", "--", "(-"]) + rand_expr(rnd, depth + 1) + (")" if False else "")
    if r < 0.6:
        return "(" + rand_expr(rnd, depth + 1) + ")" + ("" if rnd.random() < 0.95 else ")")
    if r < 0.75:
        f = rnd.choice(["min", "max", "rand", "stat", "MIN", "Max", "nosuch"])
        return "%s(%s,%s)" % (f, rand_expr(rnd, depth + 1), rand_expr(rnd, depth + 1))
    if r < 0.85:
        return "%s ? %s : %s" % (rand_expr(rnd, depth + 1), rand_expr(rnd, depth + 1), rand_expr(rnd, depth + 1))
    op = rnd.choice(["+", "-", "*", "/", "^", "<", ">", "<=", ">=", "==", "!=", "=", "!", "@"])
    return rand_expr(rnd, depth + 1) + rnd.choice(["", " "]) + op + rnd.choice(["", " "]) + rand_expr(rnd, depth + 1)


def compile_fixed():
    T = ["lvl < 4 ? 1 : 2", "(lvl < 4) ? 1 : 2", "lvl ? 1+lvl : 3", "lvl ? 2 : 3+lvl", "min(-1,lvl)", "a ? -1 : 2",
         "-100", "-37", "- -5", "-(-5)", "2^3^2", "1-2-3", "8/2/2", " ", "", "(1+2", "min(1,2", "1+2)", "\"min(24,ln12)\"",
         "lvl", "par3", "anything", "stat('strength'.base)", "stat('strength'.mod)", "stat('strength'.accr)",
         "stat('STRENGTH'.base)", "stat(strength,base)", "stat(nosuch,base)", "rand(lvl,lvl+5)", "1 == 1", "3 != 3",
         "2 <= 3", "2 >= 3", "(lvl)", "'lvl'", ".lvl", "min ( 1 , 2 )", "max(1)", "max(1,2,3)", "1?2", "1:2", "?",
         "1 & 2", "12345678901", "2147483647+1", "65535*65537"]
    T.append("(" * 64 + "1" + ")" * 64)
    T.append("(" * 65 + "1" + ")" * 65)
    T.append("(" * 63 + "1" + ")" * 63)
    T.append("1" + "+(1" * 63 + ")" * 63)
    T.append("1" + "+(1" * 64 + ")" * 64)
    T.append("-" * 64 + "1")
    T.append("min(" * 64 + "1" + ",1)" * 64)
    T.append("min(" * 65 + "1" + ",1)" * 65)
    for n in range(330, 350):           # outputs around the 1 024-byte buffer
        T.append("+".join(["lvl*1000"] * n))
        T.append("+".join(["lvl"] * (n + 2)) + "+70000")
    return T


def compile_cases(rnd):
    cases, exp = [], []
    texts = compile_fixed()
    while len(texts) < 3000:
        t = rand_expr(rnd)
        if "^" in t and any(int(x) > 64 for x in re.findall(r"\d+", t)):
            continue        # a folded power with a large exponent loops that many times
        texts.append(t)
    cookie_mem = ["dword %08x %08x" % (COOKIE, 0x7A3F19C2), "dword %08x 0" % LOCALE_CHANGED]
    for t in texts:
        b = t.encode("latin-1")
        mx = 0x400
        cases += ["w %08x %s" % (TEXTBUF, hx(b + b"\0")), "s %08x %d" % (TEXTBUF, len(b) + 8),
                  "w %08x %s" % (OUTBUF, "cc" * 0x410), "d %08x %d" % (OUTBUF, 0x410),
                  "call %08x 0 0 %08x %08x %08x %08x %08x %08x" % (FN["CALC_Compile"], TEXTBUF, OUTBUF, mx,
                                                                  FN["ItemCalcFnLookup"], FN["ItemCalcFnArity"],
                                                                  FN["ItemCalcIdent"])]
        exp.append(["compile", t])
    # the item variable reader: 0 for every index
    for _ in range(200):
        cases.append("call %08x %08x %08x" % (FN["ItemCalcVar"], rnd.getrandbits(32), rnd.getrandbits(32)))
        exp.append(["itemvar"])
    # the item cell callback (0x00631530): ECX = text or NULL, EDX = field offset, stack = record
    pool0 = bytes(rnd.getrandbits(8) for _ in range(rnd.randrange(0, 40)))
    for t in texts[:400] + [None] * 20:
        off = rnd.choice([0x10, 0xA4, 0xB0, 0])
        cases += ["w %08x %s" % (G_DATATABLES + 0x98, hx(le32(ITEMPOOL) + le32(len(pool0)) + le32(0x10000))),
                  "w %08x %s" % (ITEMPOOL, hx(pool0)), "s %08x %d" % (ITEMPOOL, 0x2000),
                  "w %08x %s" % (RECBUF, "dd" * 0x100), "d %08x 256" % RECBUF, "d %08x 12" % (G_DATATABLES + 0x98),
                  "d %08x %d" % (ITEMPOOL, len(pool0) + 0x410)]
        if t is not None:
            b = t.encode("latin-1")
            cases += ["w %08x %s" % (TEXTBUF, hx(b + b"\0")), "s %08x %d" % (TEXTBUF, len(b) + 8)]
        cases.append("call %08x %08x %08x %08x %08x %08x %08x" % (FN["ItemCalcCell"], 0 if t is None else TEXTBUF, off,
                                                                RECBUF, 4, rnd.randrange(100), rnd.randrange(100)))
        exp.append(["cell", t, off, pool0.hex()])
    return cases, cookie_mem + stat_tree_mem(), {"cases": exp}


def compile_model(text):
    ctx = CALC.ItemsContext(StatNames())
    return CALC.compile_expr(text, ctx)


def compile_check(d):
    calls, reads, writes, meta = calls_by_case(d, "compile")
    rep = Report("compile")
    neg = 0
    for c, e in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        kind = e[0]
        if kind == "compile":
            want = compile_model(e[1])
            out = c["dumps"][0][1] if "eax" in c else None
            if want is None:
                ok = out is not None and c["eax"] == 0 and out[0] == 0 and out[0x400:] == b"\xcc" * 0x10
            else:
                ok = out is not None and c["eax"] == len(want) and out[:len(want)] == want and \
                    out[0x400:] == b"\xcc" * 0x10
            ok = ok and c.get("pop") == 24
            # negative control: calc.py with the incoming operator's precedence pushed against a 65-deep stack
            CALC.STACK = 65
            try:
                alt = compile_model(e[1])
            finally:
                CALC.STACK = 0x40
            neg += alt != want
            if ok:
                rep.branches["compile_fail" if want is None else "compile_ok"] += 1
                if want is not None and want[0] in (4, 5, 6) and len(want) == 3:
                    rep.branches["bare_ident_var0"] += want == b"\x04\x00\x00"
        elif kind == "itemvar":
            ok = c.get("eax") == 0 and c.get("pop") == 0
            rep.branches["itemvar_zero"] += ok
        else:
            t, off, pool0 = e[1], e[2], bytes.fromhex(e[3])
            want = None if t is None else compile_model(t)
            rec, hdr, pool = (c["dumps"][0][1], c["dumps"][1][1], c["dumps"][2][1]) if "eax" in c else (None,) * 3
            exp_rec = bytearray(b"\xdd" * 0x100)
            if off:
                exp_rec[off:off + 4] = le32(M32 if want is None else len(pool0))
            exp_size = len(pool0) + (0 if want is None or not off else len(want))
            ok = rec == bytes(exp_rec) and hdr is not None and struct.unpack("<III", hdr) == (
                ITEMPOOL, exp_size, 0x10000) and pool[:exp_size] == pool0 + (b"" if want is None or not off else want)
            ok = ok and c.get("pop") == 16
            # negative control: a callback that stores 0 (not -1) for a failed or blank cell
            neg += bool(rec is not None and off and want is None and rec[off:off + 4] != le32(0))
            if ok:
                rep.branches["cell_%s" % ("noop_off0" if not off else "null" if t is None else
                                          "fail" if want is None else "append")] += 1
        rep.c["match"] += bool(ok)
        if not ok:
            rep.bad("case %d %r: got %r" % (c["n"], e[:2], {k: (v if k != "dumps" else [x[1][:24].hex() for x in v])
                                                             for k, v in c.items()}))
    declared = [RS_CALC_JT, (0x006C1754, 0x006C1754 + 4 * 0x40, "r", "CALC_NextToken operator jump table (.text)"),
                (0x006C186C, 0x006C186C + 4 * 0x16, "r", "CALC_OpArity jump table (.text)"),
                (0x006C1F0C, 0x006C1F0C + 4 * 0x13, "r", "CALC_Compile token jump table (.text)"),
                (0x006FC874, 0x006FC874 + 23, "r", "g_CalcPrecedence (.rdata)"),
                (0x0074AB98, 0x0074AB9C, "r", "_pctype pointer 0x0074AB98 (.data)"),
                (0x006F9280, 0x006F9280 + 0x200, "r", "the ctype table it points to (.rdata)"),
                (0x006E6390, 0x006E63D0, "r", "the item callbacks' name strings (.rdata)"),
                (LOWER - 128, LOWER + 128, "r", "STR_ToLowerN table (.rdata)"),
                (0x00683900, 0x00683C00, "r", "memcpy/memmove jump tables (.text)"),
                (0x00682A40, 0x00682B50, "r", "memcpy's jump tables 0x00682A50..0x00682B43 (.text)"),
                (0x007788D8, 0x007788DC, "w", "strncpy 0x004135D0's store to 0x007788D8 (written only)")]
    account(rep, reads, writes, declared)
    return finish(rep, neg)

# =============================================================================================== family: parsetxt
TXT, TXTHDR, TXTCELLS = 0x10700000, 0x10701000, 0x10710000
DESC, DESCNAMES, RECS = 0x10720000, 0x10721000, 0x10730000
CLINK, CLINKARR, NLINK, NLINKNODES, LINKPTRS = 0x10740000, 0x10741000, 0x10750000, 0x10751000, 0x10760000
PT_COLS = [  # (name, type, len, offset)
    (b"IntD", 2, 4, 0), (b"IntW", 3, 2, 4), (b"IntB", 4, 1, 6), (b"IntB5", 5, 1, 7), (b"IntD8", 8, 4, 8),
    (b"Flag", 0x1A, 3, 12), (b"Flag2", 0x1A, 13, 12), (b"CodeD", 0x0B, 4, 16), (b"CodeB", 0x0D, 1, 20),
    (b"CodeW", 0x0F, 2, 22), (b"NameD", 0x13, 4, 24), (b"NameW", 0x14, 2, 28), (b"NameB", 0x15, 1, 30)]
PT_RECSIZE = 32
PT_CODES = [b"abc ", b"ab  ", b"a   ", b"    ", b"wxyz", b"WXYZ", b"\xe9t\xe9 ", b"7wa ", b"ring"]
PT_NAMES = [b"", b"fire bolt", b"x" * 31, b"y" * 30 + b"z", b"monstre \xe9lite", b"cr_lancer8"]


def pt_world():
    codes = sorted(set(struct.unpack("<I", c)[0] for c in PT_CODES))
    arr = [[c, i * 3 + 1] for i, c in enumerate(codes)]
    names = [lower_key(n) for n in PT_NAMES]
    # a balanced BST of the names (index = 10 + position in PT_NAMES)
    order = sorted(range(len(names)), key=lambda i: names[i])

    def build(lo, hi):
        if lo >= hi:
            return None
        m = (lo + hi) // 2
        return (order[m], build(lo, m), build(m + 1, hi))
    nodes = {}

    def emit(t):
        if t is None:
            return None
        i, l, r = t
        nodes[i] = {"name": names[i], "index": 10 + i, "left": emit(l), "right": emit(r)}
        return i
    root = emit(build(0, len(order)))
    return arr, nodes, root


def pt_cell_model(rec, col, cell, arr, nodes, root, neg=False):
    name, typ, ln, off = col
    if typ in (2, 3, 4, 5, 8, 0x1A):
        p = 1 if cell[:1] == b"-" else 0
        v = 0
        for b in cell[p:]:
            sb = b - 256 if (b >= 128 and not neg) else b
            v = s32(v * 10 + sb - 0x30)
        if cell[:1] == b"-":
            v = s32(-v)
        if typ in (2, 8):
            rec[off:off + 4] = le32(v)
        elif typ == 3:
            rec[off:off + 2] = struct.pack("<H", v & 0xFFFF)
        elif typ == 4 or (typ == 5 and cell != b""):
            rec[off] = v & 0xFF
        elif typ == 0x1A:
            if v:
                rec[off + (ln >> 3)] |= 1 << (ln & 7)
            else:
                rec[off + (ln >> 3)] &= ~(1 << (ln & 7)) & 0xFF
        return
    if typ in (0x0B, 0x0D, 0x0F):
        k = (cell[:4] + b"    ")[:4]
        r = findcode_model(arr, struct.unpack("<I", k)[0])
        if neg and r < 0:
            r = 0
    else:
        r = findname_model(nodes, root, cell)
        if neg and r < 0:
            r = 0
    w = {0x0B: 4, 0x13: 4, 0x0F: 2, 0x14: 2, 0x0D: 1, 0x15: 1}[typ]
    rec[off:off + w] = le32(r)[:w]


def pt_rand_cell(rnd, typ):
    if typ in (2, 3, 4, 5, 8, 0x1A):
        r = rnd.random()
        if r < 0.25:
            return str(rnd.randrange(-100000, 100000)).encode()
        if r < 0.45:          # bytes >= 0x80 among digits
            return bytes(rnd.choice(b"0123456789\x80\x9c\xc8\xe9\xff") for _ in range(rnd.randrange(1, 6)))
        if r < 0.55:
            return rnd.choice([b"", b"-", b" ", b"--5", b"-\xff", b"99999999999", b"1e5", b"0x10"])
        return bytes(rnd.choice(b"0123456789- abz\x7f\x80\xf0") for _ in range(rnd.randrange(0, 8)))
    if typ in (0x0B, 0x0D, 0x0F):
        r = rnd.random()
        if r < 0.4:
            c = rnd.choice(PT_CODES)
            return (c.rstrip(b" ") if rnd.random() < 0.6 else c) + (b"suffix"[:rnd.randrange(0, 4)] if rnd.random() < 0.3 else b"")
        return bytes(rnd.choice(b"abcwxyzABC 7\xe9") for _ in range(rnd.randrange(0, 7)))
    r = rnd.random()
    if r < 0.4:
        n = rnd.choice(PT_NAMES)
        return bytes(x ^ 0x20 if 0x61 <= x <= 0x7A and rnd.random() < 0.3 else x for x in n)
    if r < 0.6:
        return rnd.choice(PT_NAMES[2:4]) + bytes(rnd.choice(b"abc") for _ in range(rnd.randrange(1, 9)))
    return bytes(rnd.choice(b"abcdefxyz \xe9") for _ in range(rnd.randrange(0, 40)))


def parsetxt_cases(rnd):
    arr, nodes, root = pt_world()
    cases, exp = [], []
    names_raw = bytearray()
    name_ptr = []
    for nm, *_ in PT_COLS:
        name_ptr.append(DESCNAMES + len(names_raw))
        names_raw += nm + b"\0"
    desc = bytearray()
    for (nm, typ, ln, off), np_ in zip(PT_COLS, name_ptr):
        link = 0
        if typ in (0x0B, 0x0D, 0x0F):
            link = LINKPTRS
        elif typ in (0x13, 0x14, 0x15):
            link = LINKPTRS + 4
        desc += le32(np_) + le32(typ) + le32(ln) + le32(off) + le32(link)
    desc += bytes(20)
    nraw = bytearray(0x30 * len(PT_NAMES))
    for i, nd in nodes.items():
        nb = bytearray(0x30)
        nb[:len(nd["name"])] = nd["name"]
        struct.pack_into("<III", nb, 0x20, nd["index"], 0 if nd["left"] is None else NLINKNODES + 0x30 * nd["left"],
                         0 if nd["right"] is None else NLINKNODES + 0x30 * nd["right"])
        nraw[0x30 * i:0x30 * i + 0x30] = nb
    mem = ["dword %08x %08x" % (COOKIE, 0x5A17C0DE), "bytes %08x %s" % (DESCNAMES, hx(names_raw)),
           "bytes %08x %s" % (DESC, hx(desc)),
           "bytes %08x %s" % (CLINK, hx(le32(len(arr)) + le32(len(arr)) + le32(CLINKARR) + le32(0))),
           "bytes %08x %s" % (CLINKARR, hx(b"".join(le32(c) + le32(i) for c, i in arr))),
           "bytes %08x %s" % (NLINK, hx(le32(len(PT_NAMES)) + le32(0) + le32(0) + le32(NLINKNODES + 0x30 * root))),
           "bytes %08x %s" % (NLINKNODES, hx(nraw)),
           "bytes %08x %s" % (LINKPTRS, hx(le32(CLINK) + le32(NLINK)))]
    for _ in range(400):
        cols = list(range(len(PT_COLS)))
        rnd.shuffle(cols)               # the .txt column order differs from the descriptor's
        nrows = rnd.randrange(1, 6)
        rows = [[pt_rand_cell(rnd, PT_COLS[c][1]) for c in cols] for _ in range(nrows)]
        hdr = b"".join(PT_COLS[c][0] + b"\0" for c in cols)
        cells = b"".join(b"".join(cell + b"\0" for cell in row) + b"\n" for row in rows)
        pre = bytes(rnd.getrandbits(8) for _ in range(PT_RECSIZE * nrows))
        cases += ["w %08x %s" % (TXT, hx(le32(TXTHDR) + le32(TXTCELLS) + le32(nrows) + le32(len(cols)))),
                  "w %08x %s" % (TXTHDR, hx(hdr)), "w %08x %s" % (TXTCELLS, hx(cells)), "s %08x %d" % (TXTCELLS, len(cells) + 8),
                  "w %08x %s" % (RECS, hx(pre)), "d %08x %d" % (RECS, PT_RECSIZE * nrows),
                  "call %08x 0 0 %08x %08x %08x %08x %08x" % (FN["EXCEL_ParseTxt"], TXT, DESC, RECS, 1, PT_RECSIZE)]
        exp.append([cols, [[c.hex() for c in row] for row in rows], pre.hex()])
    return cases, mem, {"cases": exp}


def parsetxt_check(d):
    calls, reads, writes, meta = calls_by_case(d, "parsetxt")
    rep = Report("parsetxt")
    arr, nodes, root = pt_world()
    neg = 0
    for c, (cols, rows, pre) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        outs = []
        for negm in (False, True):
            recs = bytearray(bytes.fromhex(pre))
            for r, row in enumerate(rows):
                rec = recs[PT_RECSIZE * r:PT_RECSIZE * (r + 1)]
                for ci, cell in zip(cols, row):
                    pt_cell_model(rec, PT_COLS[ci], bytes.fromhex(cell), arr, nodes, root, negm)
                recs[PT_RECSIZE * r:PT_RECSIZE * (r + 1)] = rec
            outs.append(bytes(recs))
        got = c["dumps"][0][1] if "eax" in c else None
        ok = got == outs[0] and c.get("pop") == 20
        neg += got != outs[1]
        rep.c["match"] += ok
        if not ok:
            rep.bad("case %d: got %s want %s" % (c["n"], got and got.hex(), outs[0].hex()))
            continue
        for row in rows:
            for ci, cell in zip(cols, row):
                cb = bytes.fromhex(cell)
                typ = PT_COLS[ci][1]
                if typ in (2, 3, 4, 5, 8, 0x1A):
                    rep.branches["int_byte_ge_0x80"] += any(b >= 0x80 for b in cb[1 if cb[:1] == b"-" else 0:])
                    rep.branches["int_type5_empty"] += typ == 5 and cb == b""
                elif typ in (0x0B, 0x0D, 0x0F):
                    miss = findcode_model(arr, struct.unpack("<I", (cb[:4] + b"    ")[:4])[0]) < 0
                    rep.branches["code_%02X_%s%s" % (typ, "miss" if miss else "hit", "_blank" if cb == b"" else
                                                     "")] += 1
                else:
                    miss = findname_model(nodes, root, cb) < 0
                    rep.branches["name_%02X_%s%s" % (typ, "miss" if miss else "hit",
                                                     "_over31" if len(cb) > 31 else "")] += 1
    declared = [(0x006BE0D7, 0x006BE0D7 + 0x1C, "r", "EXCEL_ParseTxt type -> class bytes 0x006BE0D7 (.text)"),
                (0x006BE080, 0x006BE140, "r", "EXCEL_ParseTxt jump tables and index bytes 0x006BE08C..0x006BE13F (.text)"),
                (0x006CE270, 0x006CE300, "r", "BITFIELD_Set/Clear bit-mask tables 0x006CE274..0x006CE2FF (.rdata)"),
                (0x006CEE30, 0x006CEE30 + 0x40, "r", "the name-hash table 0x006CEE30 (.rdata)"),
                (LOWER - 128, LOWER + 128, "r", "STR_ToLowerN table (.rdata)"),
                (0x0074AB98, 0x0074AB9C, "r", "_pctype pointer 0x0074AB98 (.data)"),
                (0x006F9280, 0x006F9280 + 0x200, "r", "the ctype table (.rdata)"),
                (0x007788D8, 0x007788DC, "w", "strncpy 0x004135D0's store to 0x007788D8 (written only)")]
    account(rep, reads, writes, declared)
    return finish(rep, neg)

# =============================================================================================== static
DATA_READS = [  # declared .data reads: (lo, hi, name) -> the writer scan must find no store
    (0x00745774, 0x007457B0, "g_SkillsCalcFuncs + g_nSkillsCalcFuncs"),
    (0x00745828, 0x0074584C, "g_MissCalcFuncs + g_nMissCalcFuncs"),
    (0x0074463C, 0x00744660, "g_ItemCalcFuncs + g_nItemCalcFuncs"),
    (0x007303DC, 0x00730514, "g_LanguageTable (13 entries)"),
    (0x00730514, 0x0073052C, "entry 13 = the 0x18 bytes after the table"),
    (0x0074AB98, 0x0074AB9C, "_pctype pointer"),
]
STORE = re.compile(r"^(mov|add|sub|or|and|xor|inc|dec|adc|sbb|neg|not|shl|shr|sar|rol|ror|xchg|movs[bwd]|stos[bwd]|"
                   r"set\w+|cmpxchg|pop)$")
MEMOP = re.compile(r"(?:BYTE|WORD|DWORD|QWORD) PTR (?:ds:)?(?:\[([^\]]*)\]|0x([0-9a-f]+))")

PINS = [  # (va, mnemonic, operand substring): the instructions the ledger cites (ADR-0015 condition 5)
    (0x0062AF53, "cmp", "ecx,0x20"), (0x0062AF56, "je", "0x62af70"), (0x0062AF58, "xor", "eax,eax"),
    (0x0062AF5A, "cmp", "eax,edx"), (0x0062AF5C, "sbb", "eax,eax"), (0x0062AF5E, "and", "eax,edx"),
    (0x0062AF60, "mov", "edx,0x1"), (0x0062AF65, "shl", "edx,cl"), (0x0062AF67, "add", "edx,0xffffffff"),
    (0x0062AF6A, "cmp", "eax,edx"), (0x0062AF6C, "jae", "0x62af70"), (0x0062AF6E, "mov", "edx,eax"),
    (0x00630F33, "cmp", "ecx,0x20"), (0x00630F36, "je", "0x630f50"), (0x00630F38, "xor", "edx,edx"),
    (0x00630F3A, "cmp", "edx,esi"), (0x00630F3C, "sbb", "eax,eax"), (0x00630F3E, "and", "eax,esi"),
    (0x00630F40, "mov", "esi,0x1"), (0x00630F45, "shl", "esi,cl"), (0x00630F47, "add", "esi,0xffffffff"),
    (0x00630F4A, "cmp", "eax,esi"), (0x00630F4C, "jae", "0x630f50"), (0x00630F4E, "mov", "esi,eax"),
    (0x00630F56, "call", "0x410eb0"),
    (0x006C0BC0, "push", "ebp"), (0x006C0BC1, "mov", "ebp,esp"), (0x006C0BC3, "sub", "esp,0x104"),
    (0x006C0BFE, "cmp", "eax,0x15"), (0x006C0C07, "jmp", "0x6c1164"),
    (0x006C0EC6, "test", "esi,esi"), (0x006C0ECE, "cdq", ""), (0x006C0ECF, "idiv", "esi"),
    (0x00525292, "cmp", "eax,0xe"), (0x005252AA, "cmp", "edx,0x730524"), (0x005252B2, "cmp", "ecx,0xe"),
    (0x005252B5, "jl", "0x5252b9"), (0x005252B7, "xor", "ecx,ecx"),
    (0x005251A1, "cmp", "eax,0xe"), (0x00525157, "jne", "0x5251ae"), (0x005251AE, "mov", "eax,ds:0x8829ec"),
    (0x00524A33, "cmp", "si,0x4e20"), (0x00524A44, "mov", "esi,0x2b46"), (0x00524A6B, "cmp", "si,0x2710"),
    (0x00524943, "cmp", "si,ax"), (0x00524948, "mov", "esi,0x1f4"),
    (0x00527D54, "cmp", "ds:0x882b2c,0x0"),
    (0x006117B0, "push", "ebp"),
    (0x006BDE20, "movsx", "ecx,cl"), (0x006BDE29, "lea", "eax,[ecx+eax*2-0x30]"),
    (0x00686F0F, "cmp", "ds:0x96dfe4,0x0"), (0x00686F1C, "mov", "ecx,DWORD PTR ds:0x74ab98"),
    (0x006926F7, "mov", "ds:0x96dfe4,0x1"),
]


def mem_targets(ops):
    out = []
    for m in MEMOP.finditer(ops):
        if m.group(2):
            out.append(int(m.group(2), 16))
        else:
            for h in re.findall(r"0x([0-9a-f]+)", m.group(1)):
                out.append(int(h, 16))
    return out


def cmd_static(a):
    rep = Report("static")
    A = S4.asm()
    for va, mn, sub in PINS:
        if not va:
            continue
        ins = A.at(va)
        rep.c["pins"] += 1
        if ins is None or ins[0] != mn or sub not in ins[1]:
            rep.bad("pin 0x%08X: %r, want %s %s" % (va, ins, mn, sub))
        else:
            rep.c["pins_ok"] += 1
    # the inlined clamp at 0x00630F38 is the function's sequence, register for register renamed
    f = [A.at(v)[0] for v, _ in A.range(0x0062AF53, 0x0062AF70)]
    g = [A.at(v)[0] for v, _ in A.range(0x00630F33, 0x00630F50)]
    rep.c["clamp_sequence_equal"] = int(f == g)
    if f != g:
        rep.bad("clamp sequences differ: %r %r" % (f, g))
    # writer scan of the declared .data reads
    for lo, hi, name in DATA_READS:
        refs, stores = [], []
        for va, (mn, ops) in A.ins.items():
            for t in mem_targets(ops):
                if lo - 3 <= t < hi:
                    first = ops.split(",")[0]
                    is_store = bool(STORE.match(mn)) and ("PTR" in first) and mn != "push"
                    (stores if is_store else refs).append((va, mn, ops))
            if mn in ("push", "mov", "lea") and re.search(r",0x([0-9a-f]+)$|^0x([0-9a-f]+)$", ops):
                for h in re.findall(r"0x([0-9a-f]+)", ops):
                    v = int(h, 16)
                    if lo <= v < hi and not mem_targets(ops):
                        refs.append((va, mn, ops))
        raw = sorted(set(sum((S4.raw_abs(x) for x in range(lo, hi, 4)), [])))
        rep.notes.append("  %s 0x%08X..0x%08X (%s): %d instruction references, %d stores, %d raw 4-byte occurrences"
                         % (name, lo, hi - 1, S4.section_of(lo), len(refs), len(stores), len(raw)))
        for va, mn, ops in refs[:12]:
            rep.notes.append("    ref 0x%08X %s %s" % (va, mn, ops))
        rep.c["data_reads"] += 1
        rep.c["data_stores"] += len(stores)
        for va, mn, ops in stores:
            if lo == 0x00730514 or "0x730510" in ops:
                # expected: word stores of small characters into entry 13, and into entry 12's +0x14, a field
                # LNG_GetLanguageCode does not read (it reads +0x00..+0x10)
                rep.notes.append("    store 0x%08X %s %s" % (va, mn, ops))
                continue
            rep.bad("store into %s at 0x%08X: %s %s" % (name, va, mn, ops))
    # __locale_changed: one writer, inside setlocale 0x0069263E, which nothing calls or points to
    w = [va for va, (mn, ops) in A.ins.items() if mn == "mov" and "ds:0x96dfe4," in ops]
    callers = S4.raw_callers(0x0069263E) + S4.raw_abs(0x0069263E)
    rep.c["locale_changed_writers"] = len(w)
    rep.c["setlocale_refs"] = len(callers)
    if w != [0x006926F7] or callers:
        rep.bad("__locale_changed writers %r, setlocale references %r" % (w, callers))
    # every declared .rdata/.text read lies in a section with no write permission
    for lo, name in ((0x006F9280, "ctype table"), (0x006FC874, "g_CalcPrecedence"), (MASKTAB, "BITBUF mask"),
                     (LOWER - 128, "lower table"), (0x006CEE30, "name hash table"), (0x006E6390, "item fn names"),
                     (0x006C1164, "CALC_Eval jump table"), (0x00646ABC, "CalcVar jump table"),
                     (0x006BE0D7, "ParseTxt class bytes")):
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
    print("S1E manifest files=%d sha256=%s" % (len(lines), hashlib.sha256(text.encode()).hexdigest()))
    return 0


FAMILIES = {
    "rng": (rng_cases, rng_check),
    "bitbuf": (bitbuf_cases, bitbuf_check),
    "eval": (eval_cases, eval_check),
    "calcvar": (calcvar_cases, calcvar_check),
    "entry": (entry_cases, entry_check),
    "excel": (excel_cases, excel_check),
    "lang": (lang_cases, lang_check),
    "strings": (strings_cases, strings_check),
    "compile": (compile_cases, compile_check),
    "parsetxt": (parsetxt_cases, parsetxt_check),
}


def cmd_cases(a):
    for fam in a.family or list(FAMILIES):
        rnd = random.Random("s1e-" + fam)
        cases, mem, meta = FAMILIES[fam][0](rnd, a.dir) if fam in ("strings",) else FAMILIES[fam][0](rnd)
        if fam in SSE_FAMILIES:
            mem = mem + ["dword %08x 0" % SSE_FLAG, "dword %08x 0" % LOCALE_CHANGED]
        write_family(a.dir, fam, cases, mem, meta)
        if fam in SSE_FAMILIES:
            with open(os.path.join(a.dir, fam + "-sse.mem"), "w") as f:
                f.write("\n".join(mem[:-2] + ["dword %08x 1" % SSE_FLAG, "dword %08x 0" % LOCALE_CHANGED]) + "\n")
        print("S1E cases %s calls=%d mem_lines=%d" % (fam, sum(1 for c in cases if c.startswith("call")), len(mem)))
    return 0


def cmd_check(a):
    global OUT_SUFFIX
    rc = 0
    for fam in a.family or list(FAMILIES):
        rc |= FAMILIES[fam][1](a.dir)
        if fam in SSE_FAMILIES:
            OUT_SUFFIX = "-sse"
            try:
                rc |= FAMILIES[fam][1](a.dir)
            finally:
                OUT_SUFFIX = ""
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

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
        self.fam = fam
        self.c = collections.Counter()
        self.notes = []
        self.branches = collections.Counter()

    def bad(self, why):
        self.c["bad"] += 1
        if len(self.notes) < 25:
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


def calls_by_case(d, fam):
    calls, reads, writes = read_out(os.path.join(d, fam + ".out"))
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


FAMILIES = {
    "rng": (rng_cases, rng_check),
    "bitbuf": (bitbuf_cases, bitbuf_check),
    "eval": (eval_cases, eval_check),
    "calcvar": (calcvar_cases, calcvar_check),
    "entry": (entry_cases, entry_check),
}


def cmd_cases(a):
    for fam in a.family or list(FAMILIES):
        rnd = random.Random("s1e-" + fam)
        cases, mem, meta = FAMILIES[fam][0](rnd)
        write_family(a.dir, fam, cases, mem, meta)
        print("S1E cases %s calls=%d mem_lines=%d" % (fam, sum(1 for c in cases if c.startswith("call")), len(mem)))
    return 0


def cmd_check(a):
    rc = 0
    for fam in a.family or list(FAMILIES):
        rc |= FAMILIES[fam][1](a.dir)
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
    raise SystemExit("not yet")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Plan 0051 Phase 1b (`lane/p51s`): the two optional emulations of the backlog sweep, run on the pinned Game.exe under
Ghidra's p-code emulator with re/ghidra_scripts/EmuTrace.java (ADR-0015). No game, no slot.

    python3 -I tools/sweep_p51s.py cases [FAMILY ...] [--dir D]   write D/<family>.cases, .mem, .json
    tools/ghidra.sh emutrace D/<family>.cases D/<family>.mem > D/<family>.out
    python3 -I tools/sweep_p51s.py check [FAMILY ...] [--dir D]   compare with the models, account every traced access,
                                                                 run the negative controls
    python3 -I tools/sweep_p51s.py calcemu-cases [--dir D]        D/calcemu/: the kept run:2026-10-16-calc-emu cases and
                                                                 memory specs rewritten as EmuTrace files (11 runs)
    python3 -I tools/sweep_p51s.py calcemu-check [--dir D]        D/calcemu/<run>.out back into the old output formats:
                                                                 byte compare with the kept outputs, the kept checkers
                                                                 (tools/calc_funcs.py), and the traced read set
    python3 -I tools/sweep_p51s.py static                         objdump pins (ADR-0015 (5)); section of the image reads
    python3 -I tools/sweep_p51s.py manifest [--write] [--dir D]   sha256 of every file under D

Families (backlog 2026-10-17 op 6/7 emulation entry; stats/0001 § 4):
  bytime   STAT_ByTimeValue 0x0065CA30 called directly: value word, unused arg, phase x, three out pointers
  op67     sub_00626200_StatEvaluate 0x00626200 on a scratch stat list whose target stat's op table holds op 6 and 7
           entries (with 10, 12 and out-of-range ops between), reaching STATLIST_SumOwnAndChildren, ActTimeOfDay
           0x0061C100 (and 0x0061AA60), STAT_ByTimeValue and MulDiv as callees; nested sources with their own op 6/7

Each check prints one `P51S <family> key=value ...` line: cases, match, bad, neg (the negative control's mismatches, must
be > 0), traced, undeclared (must be 0), stopped (must be 0), then the branches reached.

calcemu (backlog 2026-10-17 S1e review follow-ups (b)): the nine calc functions (EmuCalcFunc's convention: ECX a, EDX b,
stack c, ctx; the ctx block's dword 0 -> a scratch unit; the seed at unit+0x20 and ctx+0x20), MISS_CalcVar and
MISS_EvalCalc (EmuCall's lines: ecx edx args, the kept memory specs) are re-run unchanged under EmuTrace, so the read
set is enumerated by the tool.

Stdlib only, plus objdump for `static`. Writes only under D (default workspace/logs/p51s/emu).
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
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sweep_s1e as E  # noqa: E402
import sweep_s1f as F  # noqa: E402
import sweep_s4b as S4  # noqa: E402

from sweep_s1e import M32, s32, cdiv  # noqa: E402

ROOT = os.path.dirname(HERE)
DEFDIR = os.path.join(ROOT, "workspace", "logs", "p51s", "emu")
CALCEMU = os.path.join(ROOT, "workspace", "logs", "calc-emu")
EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")

FN = {"STAT_ByTimeValue": 0x0065CA30, "StatEvaluate": 0x00626200, "ActTimeOfDay": 0x0061C100,
      "MulDiv": 0x00483360}
G_PDATATABLES = 0x00744304
MASK_DMG = 0x006CE270            # u32 4 (.rdata): the "damagerelated" bit of an ItemStatCost record's byte +0x04

# scratch memory (outside the image and the emulator stack 0x7FE00000..0x7FF01000)
OUTS = 0x13000000                # bytime: the three out words
DTS = 0x13100000                 # a scratch DataTables: +0xBCC ItemStatCost records, +0xBD4 their count
ISC = 0x13200000                 # ItemStatCost records, 0x144 bytes each
NISC = 0x200
LIST = 0x13400000                # a stat list
ARR = 0x13401000                 # its own (+0x24) array of {key, value}
UNIT = 0x13402000                # the list's owner unit (+0x44)
ACT = 0x13403000                 # owner +0x1C
ENV = 0x13404000                 # act +0x04

RS_MASK = (MASK_DMG, MASK_DMG + 4, "r", "mask 0x006CE270 (.rdata, u32 4): STATLIST_SumOwnAndChildren's damage-bit test")
RS_JT = (0x00626688, 0x00626688 + 4 * 13, "r", "StatEvaluate jump table 0x00626688, ops 1-13 (.text)")


class Report(E.Report):
    def line(self):
        keys = ["cases", "match", "bad", "neg", "traced", "undeclared", "stopped"]
        rest = sorted(k for k in self.c if k not in keys)
        return "P51S %s " % self.fam + " ".join("%s=%d" % (k, self.c[k]) for k in keys + rest)


def calls_of(d, fam):
    calls, reads, writes = E.read_out(os.path.join(d, fam + ".out"))
    meta = json.load(open(os.path.join(d, fam + ".json")))
    return calls, reads, writes, meta


def w(addr, data):
    return "w %08x %s" % (addr, data.hex())


def le32(v):
    return struct.pack("<I", v & M32)


# =============================================================================================== STAT_ByTimeValue
def bytime_model(v, x, neg=None):
    """STAT_ByTimeValue(v, unused, x, pq, plo, phi) -> (eax, q, lo, hi). Signed 32-bit throughout, as the code."""
    v &= M32
    q = v & 3
    lo = ((v >> 2) & 0x3FF) - 0x100
    hi = ((v >> 12) & 0x3FF) - 0x100
    a = s32(x - q * 0x5A)
    if a < 0:
        a = s32(-a)                            # neg: INT32_MIN stays INT32_MIN
    a = s32(cdiv(s32(a + 7), 15) * 15)         # imul 0x88888889 / sar 3: signed division truncated toward zero
    if a <= 0:
        a = 0
    if neg == "no359":
        if a > 180:
            a = 360 - a
    elif a >= 0x167:
        a = 360 - 0x167
    elif a > 0xB4:
        a = 360 - a
    if neg == "floor":
        r = hi - ((hi - lo) * a) // 180
    else:
        r = hi - cdiv(s32((hi - lo) * a), 180)
    return s32(r) & M32, q, lo & M32, hi & M32


def bytime_cases(rnd):
    cases, exp = [], []
    xedges = [0, 1, -1, 7, 8, 22, 23, 90, 180, 181, 270, 352, 353, 359, 360, 450, 539, 540, 1000, -1000,
              0x7FFFFFF0, 0x7FFFFFFF, -0x80000000, -0x7FFFFFF0]
    while len(exp) < 6000:
        k = rnd.random()
        v = rnd.getrandbits(32) if k < 0.6 else (rnd.randrange(4) | rnd.randrange(0x400) << 2 |
                                                 rnd.randrange(0x400) << 12 | rnd.getrandbits(10) << 22)
        if k < 0.3:
            x = rnd.choice(xedges) + rnd.randrange(-2, 3)
        elif k < 0.7:
            x = rnd.randrange(-400, 760)
        else:
            x = s32(rnd.getrandbits(32))
        x = s32(x)
        unused = rnd.getrandbits(32)
        ptrs = [OUTS + 4 * i if rnd.random() < 0.7 else 0 for i in range(3)]
        lines = ["w %08x %s" % (OUTS, "ee" * 12), "d %08x 12" % OUTS]
        lines.append("call %08x %08x %08x %08x %08x %08x %08x %08x %08x" % (
            FN["STAT_ByTimeValue"], rnd.getrandbits(32), rnd.getrandbits(32), v, unused, x & M32,
            ptrs[0], ptrs[1], ptrs[2]))
        cases.extend(lines)
        exp.append([v, x, ptrs])
    return cases, [], {"cases": exp}


def bytime_check(d):
    calls, reads, writes, meta = calls_of(d, "bytime")
    rep = Report("bytime")
    neg = negf = 0
    for c, (v, x, ptrs) in zip(calls, meta["cases"]):
        rep.c["cases"] += 1
        if F.stopped(rep, c):
            continue
        eax, q, lo, hi = bytime_model(v, x)
        outs = c["dumps"][0][1]
        want = bytearray(b"\xee" * 12)
        for i, val in enumerate((q, lo, hi)):
            if ptrs[i]:
                want[4 * i:4 * i + 4] = le32(val)
        ok = c["eax"] == eax and c["pop"] == 0x18 and outs == bytes(want)
        rep.c["match"] += ok
        if not ok:
            rep.bad("case %d v=%08x x=%d: got %08x pop=%d outs=%s want %08x %s" % (
                c["n"], v, x, c["eax"], c["pop"], outs.hex(), eax, bytes(want).hex()))
            continue
        dd = s32(x - (v & 3) * 90)
        ad = s32(-dd) if dd < 0 else dd
        aa = s32(cdiv(s32(ad + 7), 15) * 15)
        rep.branches["x_neg_after_q"] += dd < 0
        rep.branches["a_le0"] += aa <= 0
        rep.branches["a_le180"] += 0 < aa <= 180
        rep.branches["a_181_358"] += 180 < aa < 359
        rep.branches["a_ge359"] += aa >= 359
        rep.branches["abs_int_min"] += dd == -0x80000000
        rep.branches["lo_gt_hi"] += s32(lo) > s32(hi)
        rep.branches["null_out"] += sum(1 for p in ptrs if not p)
        rep.branches["q%d" % (v & 3)] += 1
        neg += c["eax"] != bytime_model(v, x, neg="no359")[0]
        negf += c["eax"] != bytime_model(v, x, neg="floor")[0]
    rep.c["neg_floor"] = negf
    E.account(rep, reads, writes, [])
    return E.finish(rep, neg)


# =============================================================================================== StatEvaluate op 6/7
class World:
    """One case: a stat list, its owner, an act and environment, and the ItemStatCost records the evaluation reads."""

    def __init__(self, rnd):
        self.rnd = rnd
        self.recs = {}           # id -> {"b4": byte, "has": byte, "ent": [(src, op, param)]}
        self.vals = {}           # key -> value (the own array)
        ids = rnd.sample(range(1, NISC), 12)
        self.t = ids[0]
        srcs = ids[1:6]
        nested_srcs = ids[6:12]
        nent = rnd.choice([1, 1, 2, 3, 4, 6, 16])
        ops = []
        for _ in range(nent):
            r = rnd.random()
            ops.append(6 if r < 0.42 else 7 if r < 0.84 else rnd.choice([10, 12, 14, 200]))
        ent = [(rnd.choice(srcs), op, rnd.getrandbits(8)) for op in ops]
        self.recs[self.t] = {"b4": rnd.getrandbits(8), "has": rnd.choice([1, 1, 1, 0x80]), "ent": ent}
        for s in srcs:
            nested = rnd.random() < 0.25
            if nested:
                ne = [(rnd.choice(nested_srcs), rnd.choice([6, 7]), rnd.getrandbits(8)) for _ in range(rnd.randrange(1, 3))]
                self.recs[s] = {"b4": rnd.getrandbits(8), "has": 1, "ent": ne}
            else:
                self.recs[s] = {"b4": rnd.getrandbits(8), "has": 0, "ent": []}
        for s in nested_srcs:
            self.recs[s] = {"b4": rnd.getrandbits(8), "has": 0, "ent": []}
        self.param = rnd.choice([0, 0, rnd.getrandbits(16)])
        self.key = (self.t << 16) | self.param
        # the own array: the target key, most sources (some 0 or absent), decoys
        self.vals[self.key] = self.value()
        for s in srcs + nested_srcs:
            if rnd.random() < 0.85:
                self.vals[s << 16] = self.value() if rnd.random() < 0.85 else 0
        for _ in range(rnd.randrange(0, 6)):
            k = (rnd.randrange(1, NISC) << 16) | rnd.getrandbits(16)
            self.vals.setdefault(k, self.value())
        self.ext = rnd.random() < 0.3                     # list +0x10 bit 31 with no children
        self.owner = rnd.random() < 0.92
        self.act = rnd.random() < 0.92
        self.env = rnd.random() < 0.9
        self.env4 = rnd.getrandbits(32)
        while True:
            r = rnd.random()
            if r < 0.5:
                num, den = rnd.randrange(-50, 800), rnd.choice([1, 1, 2, 3, 25, 100, 0])
            elif r < 0.85:
                num, den = s32(rnd.getrandbits(32)), s32(rnd.getrandbits(32)) >> rnd.randrange(0, 31)
            else:
                num, den = s32(rnd.getrandbits(32)), rnd.choice([0, 1, -1, 7])
            if not (num == -0x80000000 and den == -1):    # the one idiv fault input (SLEIGH returns 0; not admitted)
                break
        self.num, self.den = s32(num), s32(den)

    def value(self):
        r = self.rnd.random()
        if r < 0.4:
            return self.rnd.randrange(-300, 300)
        if r < 0.55:
            return self.rnd.choice([0x7FFFFFFF, -0x80000000, 0x100000, 0x100001, -0x100001, 0x40000000])
        if r < 0.75:
            v = self.rnd.randrange(4) | self.rnd.randrange(0x400) << 2 | self.rnd.randrange(0x400) << 12
            return s32(v | self.rnd.getrandbits(10) << 22) if self.rnd.random() < 0.3 else v
        return s32(self.rnd.getrandbits(32))

    # ------------------------------------------------------------------------------------------ memory
    def lines(self):
        out = []
        for i, (rid, r) in enumerate(sorted(self.recs.items())):
            base = ISC + rid * 0x144
            out.append(w(base + 0x04, bytes([r["b4"]])))
            out.append(w(base + 0x52, bytes([r["has"]])))
            if r["has"]:
                for k, (src, op, par) in enumerate(r["ent"]):
                    out.append(w(base + 0xE0 + 6 * k, struct.pack("<HBB", src, op, par)))
                if len(r["ent"]) < 16:
                    out.append(w(base + 0xE2 + 6 * len(r["ent"]), b"\0"))
        keys = sorted(self.vals, key=s32)
        arr = b"".join(struct.pack("<Ii", k, v) for k, v in ((k, s32(self.vals[k])) for k in keys))
        out.append(w(ARR, arr))
        out.append(w(LIST + 0x10, le32(0x80000000 if self.ext else 0)))
        out.append(w(LIST + 0x24, le32(ARR)))
        out.append(w(LIST + 0x28, struct.pack("<H", len(keys))))
        if self.ext:
            out.append(w(LIST + 0x3C, le32(0)))
        out.append(w(LIST + 0x44, le32(UNIT if self.owner else 0)))
        if self.owner:
            out.append(w(UNIT + 0x1C, le32(ACT if self.act else 0)))
            if self.act:
                out.append(w(ACT + 0x04, le32(ENV if self.env else 0)))
                if self.env:
                    out.append(w(ENV + 0x04, le32(self.env4)))
                    out.append(w(ENV + 0x08, le32(self.num)))
                    out.append(w(ENV + 0x28, le32(self.den)))
        out.append("call %08x %08x %08x" % (FN["StatEvaluate"], LIST, self.key))
        return out

    # ------------------------------------------------------------------------------------------ model
    def phase(self):
        if not self.env:
            return 0
        return 0 if self.den == 0 else s32(cdiv(self.num, self.den))

    def ev(self, key, br, neg=None, depth=0):
        t = (key >> 16) & 0xFFFF
        if t >= NISC:
            return 0
        r = self.recs[t]
        v = s32(self.vals.get(key, 0))
        acc = v
        if not r["has"]:
            return v
        br["depth%d" % depth] += 1
        for k in range(16):
            if k >= len(r["ent"]):
                break
            src, op, _ = r["ent"][k]
            if op in (10, 12):
                br["op%d" % op] += 1
                continue
            if op > 13:
                br["op_gt13"] += 1
                continue
            if not self.owner:
                br["op%d_no_owner" % op] += 1
                continue
            if not self.act:
                br["op%d_no_act" % op] += 1
                continue
            p = self.ev(src << 16, br, neg, depth + 1)
            if p == 0:
                br["op%d_p0" % op] += 1
                continue
            x = self.phase()
            tv = s32(bytime_model(p, x)[0])
            br["op%d_term" % op] += 1
            br["op%d_env0" % op] += not self.env
            if neg == "noop67":
                continue
            if op == 6:
                acc = s32(acc + tv)
            else:
                base = v if neg == "b0" else acc
                m = s32(F.muldiv_model(base, tv, 100, br=br if neg is None else None)[0])
                acc = s32(acc + m)
        return acc


def op67_cases(rnd):
    mem = ["dword %08x %08x" % (G_PDATATABLES, DTS), "dword %08x %08x" % (DTS + 0xBCC, ISC),
           "dword %08x %08x" % (DTS + 0xBD4, NISC)]
    cases, seeds = [], []
    for i in range(3000):
        seed = rnd.getrandbits(64)
        cases.extend(World(random.Random(seed)).lines())
        seeds.append(seed)
    return cases, mem, {"seeds": seeds}


def op67_check(d):
    calls, reads, writes, meta = calls_of(d, "op67")
    rep = Report("op67")
    neg = negb = 0
    for c, seed in zip(calls, meta["seeds"]):
        rep.c["cases"] += 1
        if F.stopped(rep, c):
            continue
        wd = World(random.Random(seed))
        br = collections.Counter()
        want = wd.ev(wd.key, br) & M32
        ok = c["eax"] == want and c["pop"] == 0
        rep.c["match"] += ok
        if not ok:
            rep.bad("case %d seed=%d: got %08x pop=%d want %08x" % (c["n"], seed, c["eax"], c["pop"], want))
            continue
        rep.branches.update(br)
        rep.branches["ext_list"] += wd.ext
        rep.branches["phase_den0"] += wd.env and wd.den == 0
        rep.branches["has_0x80"] += wd.recs[wd.t]["has"] == 0x80
        rep.branches["entries16"] += len(wd.recs[wd.t]["ent"]) == 16
        rep.branches["param_nonzero"] += wd.param != 0
        neg += c["eax"] != wd.ev(wd.key, collections.Counter(), neg="noop67") & M32
        negb += c["eax"] != wd.ev(wd.key, collections.Counter(), neg="b0") & M32
    rep.c["neg_b0"] = negb
    E.account(rep, reads, writes, [RS_MASK, RS_JT])
    return E.finish(rep, neg)


# =============================================================================================== calc-emu re-run
CALCFNS = ["skills_min", "skills_max", "skills_rand", "items_min", "items_max", "items_rand", "miss_min", "miss_max",
           "miss_rand"]
CE_CTX, CE_UNIT = 0x7F100000, 0x7F200000             # EmuCalcFunc's scratch context and unit
RS_MISSFUNCS = (0x00745828, 0x0074584C, "r", "g_MissCalcFuncs 0x00745828 + g_nMissCalcFuncs 0x00745848 (.data)")
# found by this re-run (not in the 2026-10-16 record's list): the two switch tables, both in .text (READONLY)
RS_MISSCV_JT = (0x0064B62C, 0x0064B62C + 4 * 43, "r", "MISS_CalcVar jump table 0x0064B62C, codes 0-42 (.text)")
CALCEMU_DECLARED = [RS_MISSFUNCS, RS_MISSCV_JT, E.RS_CALC_JT]


def calcemu_runs():
    import calc_funcs as CF
    runs = [(f, CF.FNS[f][0]) for f in CALCFNS]
    return runs + [("miss", 0x0064B340), ("eval", 0x0064B7C0)]


def cmd_calcemu_cases(a):
    d = os.path.join(a.dir, "calcemu")
    os.makedirs(d, exist_ok=True)
    guards = F.GUARDS
    src = [ln.split() for ln in open(os.path.join(CALCEMU, "calcfn-cases.txt")) if ln.strip()]
    for f, addr in calcemu_runs():
        out = []
        if f in CALCFNS:
            for aa, b, c, ctx, lo, hi in src:
                seed = le32(int(lo, 16)) + le32(int(hi, 16))
                out += [w(CE_CTX, le32(CE_UNIT)), w(CE_UNIT + 0x20, seed), w(CE_CTX + 0x20, seed),
                        "d %08x 8" % (CE_UNIT + 0x20), "d %08x 8" % (CE_CTX + 0x20),
                        "call %08x %s %s %s %08x" % (addr, aa, b, c, 0 if int(ctx, 16) == 0 else CE_CTX)]
            mem = list(guards)
        else:
            sub = os.path.join(CALCEMU, f)
            for ln in open(os.path.join(sub, f + "-cases.txt")):
                p = ln.split()
                if p:
                    out.append("call %08x %s" % (addr, " ".join(p)))
            mem = [ln.rstrip("\n") for ln in open(os.path.join(sub, f + "-mem.txt"))] + guards
        with open(os.path.join(d, f + ".cases"), "w") as fh:
            fh.write("\n".join(out) + "\n")
        with open(os.path.join(d, f + ".mem"), "w") as fh:
            fh.write("\n".join(mem) + "\n")
        print("P51S calcemu-cases %s calls=%d mem_lines=%d" % (f, sum(1 for x in out if x.startswith("call")), len(mem)))
    return 0


def cmd_calcemu_check(a):
    d = os.path.join(a.dir, "calcemu")
    rc = 0
    for f, addr in calcemu_runs():
        calls, reads, writes = E.read_out(os.path.join(d, f + ".out"))
        rep = Report("calcemu-" + f)
        lines = []
        for c in calls:
            rep.c["cases"] += 1
            if F.stopped(rep, c):
                lines.append("STOP")
                continue
            if f in CALCFNS:
                u, cs = c["dumps"][0][1], c["dumps"][1][1]
                lines.append("%08x %08x %08x %08x %08x" % (c["eax"], F.u32(u, 0), F.u32(u, 4), F.u32(cs, 0),
                                                           F.u32(cs, 4)))
                rep.c["pop_ok"] += c["pop"] == 8
            else:
                lines.append("%08x %d" % (c["eax"], c["pop"]))
        text = "\n".join(lines) + "\n"
        old = os.path.join(CALCEMU, "calcfn-%s.out" % f if f in CALCFNS else os.path.join(f, f + ".out"))
        oldt = open(old).read()
        same = text == oldt
        rep.c["same_as_kept"] = int(same)
        rep.c["match"] = sum(1 for x, y in zip(text.splitlines(), oldt.splitlines()) if x == y)
        if not same:
            rep.bad("output differs from the kept %s" % os.path.relpath(old, ROOT))
        conv = os.path.join(d, f + ".old-format.out")
        with open(conv, "w") as fh:
            fh.write(text)
        if f in CALCFNS:
            cmd = ["check", f, os.path.join(CALCEMU, "calcfn-cases.txt"), conv]
        elif f == "miss":
            cmd = ["misscheck", os.path.join(CALCEMU, "miss"), conv]
        else:
            cmd = ["evalcheck", EXCEL, os.path.join(CALCEMU, "eval"), conv]
        r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "calc_funcs.py")] + cmd, capture_output=True,
                           text=True)
        rep.c["model_check_rc"] = r.returncode
        if r.returncode:
            rep.bad("calc_funcs.py %s: rc %d" % (cmd[0], r.returncode))
        rep.notes.append("  calc_funcs.py %s: %s" % (cmd[0], r.stdout.strip().splitlines()[-1] if r.stdout.strip()
                                                     else r.stderr.strip()[-200:]))
        E.account(rep, reads, writes, CALCEMU_DECLARED)
        # negative control: the same checker on this output with every EAX + 1 must fail (rc != 0); for the nine
        # calc functions also the count of lines that differ from a sibling's kept output
        pert = os.path.join(d, f + ".neg.out")
        with open(pert, "w") as fh:
            for ln in text.splitlines():
                p = ln.split()
                fh.write(" ".join(["%08x" % ((int(p[0], 16) + 1) & M32)] + p[1:]) + "\n")
        r2 = subprocess.run([sys.executable, "-I", os.path.join(HERE, "calc_funcs.py")] + cmd[:-1] + [pert],
                            capture_output=True, text=True)
        rep.c["neg"] = int(r2.returncode != 0)
        if not rep.c["neg"]:
            rep.bad("negative control did not fail")
        if f in CALCFNS:
            tab, kind = f.split("_")
            sibf = "%s_%s" % (tab, {"min": "max", "max": "min"}[kind]) if kind != "rand" else \
                ("skills_rand" if tab == "miss" else "miss_rand")
            st = open(os.path.join(CALCEMU, "calcfn-%s.out" % sibf)).read().splitlines()
            rep.c["neg_vs_" + sibf] = sum(1 for x, y in zip(text.splitlines(), st) if x != y)
        print(rep.line())
        for n in rep.notes:
            print("  " + n)
        for pc, addr2, n, cnt in reads:
            print("    R pc=%08x addr=%08x size=%d count=%d" % (pc, addr2, n, cnt))
        for pc, addr2, n, cnt in writes:
            print("    W pc=%08x addr=%08x size=%d count=%d" % (pc, addr2, n, cnt))
        rc |= 1 if rep.c["bad"] else 0
    return rc


# =============================================================================================== static
PINS = [  # (va, mnemonic, operand substring): the instructions the finding cites (ADR-0015 condition 5)
    # STAT_ByTimeValue
    (0x0065CA33, "mov", "eax,DWORD PTR [ebp+0x8]"), (0x0065CA3B, "sar", "eax,0xc"), (0x0065CA43, "sar", "esi,0x2"),
    (0x0065CA78, "mov", "eax,DWORD PTR [ebp+0x10]"), (0x0065CA7B, "imul", "ecx,ecx,0x5a"), (0x0065CA80, "jns", ""),
    (0x0065CA82, "neg", "eax"), (0x0065CA84, "lea", "ecx,[eax+0x7]"), (0x0065CA87, "mov", "eax,0x88888889"),
    (0x0065CA90, "sar", "edx,0x3"), (0x0065CAA5, "setle", "al"), (0x0065CAAD, "cmp", "eax,0x167"),
    (0x0065CAB2, "jl", ""), (0x0065CABB, "cmp", "eax,0xb4"), (0x0065CAC0, "jle", ""), (0x0065CAC2, "mov", "ecx,0x168"),
    (0x0065CACF, "imul", "ecx,eax"), (0x0065CAD2, "mov", "eax,0xb60b60b7"), (0x0065CADB, "sar", "edx,0x7"),
    (0x0065CAE0, "shr", "eax,0x1f"), (0x0065CAEA, "sub", "eax,ecx"),
    # StatEvaluate cases 6 and 7
    (0x0062628D, "jmp", "DWORD PTR [eax*4+0x626688]"), (0x00626455, "mov", "eax,DWORD PTR [eax+0x1c]"),
    (0x00626489, "call", "0x61c100"), (0x0062649A, "call", "0x65ca30"), (0x0062649F, "jmp", "0x626662"),
    (0x006264EB, "push", "0x64"), (0x006264F6, "call", "0x65ca30"), (0x006264FB, "mov", "edi,DWORD PTR [ebp-0x4]"),
    (0x00626502, "call", "0x483360"), (0x00626662, "add", "DWORD PTR [ebp-0x4],eax"),
    # ActTimeOfDay
    (0x0061C107, "call", "0x61aa60"), (0x0061C12A, "mov", "ecx,DWORD PTR [esi+0x28]"), (0x0061C134, "cdq", ""),
    (0x0061C135, "idiv", "ecx"), (0x0061C139, "mov", "eax,DWORD PTR [esi+0x4]"), (0x0061AA83, "mov", "eax,DWORD PTR [ecx+0x4]"),
    # calc-emu re-run: the two switches whose tables the trace reads
    (0x0064B38B, "cmp", "esi,0x2a"), (0x0064B38E, "ja", ""), (0x0064B394, "jmp", "DWORD PTR [esi*4+0x64b62c]"),
    (0x006C0BFE, "cmp", "eax,0x15"), (0x006C0C01, "ja", ""), (0x006C0C07, "jmp", "DWORD PTR [eax*4+0x6c1164]"),
]


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
    jt = [S4.dword(0x00626688 + 4 * i) for i in range(13)]
    rep.notes.append("  StatEvaluate jump table 0x00626688 (op 1..13): " + " ".join("%d:%08X" % (i + 1, t)
                                                                                 for i, t in enumerate(jt)))
    rep.c["jt_ok"] = int(jt[5] == 0x0062644A and jt[6] == 0x006264A4 and jt[9] == jt[11] == 0x00626665)
    if not rep.c["jt_ok"]:
        rep.bad("jump table entries 6/7/10/12")
    m = S4.dword(MASK_DMG)
    sec = S4.section_of(MASK_DMG)
    flags = [x[5] for x in S4.image()[2] if x[4] == sec][0]
    rep.c["mask_ro"] = int(m == 4 and not flags & 0x80000000)
    rep.notes.append("  mask 0x%08X = %d in %s (writable %s)" % (MASK_DMG, m, sec, bool(flags & 0x80000000)))
    if not rep.c["mask_ro"]:
        rep.bad("mask 0x006CE270")
    for lo, name in ((0x00626688, "StatEvaluate jump table"), (0x0064B62C, "MISS_CalcVar jump table"),
                     (0x006C1164, "CALC_Eval jump table")):
        sec = S4.section_of(lo)
        fl = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.c["ro_tables"] += not fl & 0x80000000
        rep.notes.append("  %s 0x%08X in %s (writable %s)" % (name, lo, sec, bool(fl & 0x80000000)))
        if fl & 0x80000000:
            rep.bad("%s writable" % name)
    for t in (0x0065CA30, 0x0061C100, 0x00626200):
        n = len(S4.raw_callers(t))
        rep.c["callers_%08X" % t] = n
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
            lines.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.relpath(p, a.dir)))
    text = "\n".join(lines) + "\n"
    if a.write:
        open(os.path.join(a.dir, "manifest.txt"), "w").write(text)
    print("P51S manifest files=%d sha256=%s" % (len(lines), hashlib.sha256(text.encode()).hexdigest()))
    return 0


FAMILIES = {"bytime": (bytime_cases, bytime_check), "op67": (op67_cases, op67_check)}


def cmd_cases(a):
    for fam in a.family or list(FAMILIES):
        rnd = random.Random("p51s-" + fam)
        cases, mem, meta = FAMILIES[fam][0](rnd)
        E.write_family(a.dir, fam, cases, mem + F.GUARDS, meta)
        print("P51S cases %s calls=%d mem_lines=%d" % (fam, sum(1 for c in cases if c.startswith("call")),
                                                       len(mem) + len(F.GUARDS)))
    return 0


def cmd_check(a):
    rc = 0
    for fam in a.family or list(FAMILIES):
        rc |= FAMILIES[fam][1](a.dir)
    return rc


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["cases", "check", "calcemu-cases", "calcemu-check", "static", "manifest"])
    ap.add_argument("family", nargs="*")
    ap.add_argument("--dir", default=DEFDIR)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    return {"cases": cmd_cases, "check": cmd_check, "calcemu-cases": cmd_calcemu_cases,
            "calcemu-check": cmd_calcemu_check, "static": cmd_static, "manifest": cmd_manifest}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

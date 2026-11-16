#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S6e part 2 (`lane/n66l`): three more anim functions run whole under Ghidra's p-code
emulator (ADR-0015, ADR-0021, ADR-0029) with re/ghidra_scripts/EmuBoundary.java, compared with the models below.
Part 1's tool, tools/anim_s6e_emu.py, and its families and seeds stay unchanged; this file imports its helpers only.
As there, no callee is an observed boundary and no callee return is declared (ruling R2): every callee runs.

    python3 -I tools/anim_s6e2_emu.py cases [--dir D]     write D/s6e2.cases, D/s6e2.mem and the region images
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s6e2.cases D/s6e2.mem > D/s6e2.out
    python3 -I tools/anim_s6e2_emu.py check [--dir D]     compare, account for every traced read and write, controls
    python3 -I tools/anim_s6e2_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66l/s6e/run2. Every draw comes from random.Random("n66l-s6e2-<family>").

Declared image (re-applied before every case, then the case's `w` lines): the DataTables pointer 0x00744304 -> DT
(+0xA78/+0xA80 MonStats base and count, +0xA90/+0xA98 MonStats2 base and count, +0xBC/+0xC4 States base and count,
+0x17C/+0x180 the transform-state list and its i16 count; all other bytes 0); the stock monstats.bin and monstats2.bin
records (game data, read from workspace/merged/data/global/excel/, loaded `const` without their u32 count header: no
code under test writes them); a scratch States region (64 records of 0x3C, zero but for the case's writes), a scratch
list, a unit, a stat list with its state bit field, a path, three out dwords.
Image constants read (.rdata, no code writes them): g_BitMask32 0x006CE268 (32 dwords), g_PlrToMonMode 0x006EB348
(20), g_MonToPlrMode 0x006EB308 (16), PlrToMonMode's jump table 0x00645248 and its byte index 0x00645260.

Families (function, inventory rows):
  pvs    0x006502D0 sub_006502D0_PathVelocityStep, EAX the path, ECX k (movement 24; movement 19's remainder: the
         step arithmetic and the fifth-call acceleration)
  p2m    0x00645190 sub_00645190_PlrToMonMode(mode, class) over every player mode and every stock MonStats class,
         and the class and MonStats2 bounds (timing 20; timing 130's remainder: the fallback chain)
  xform  0x00645270 UNIT_AnimTransform(unit, &type, &class, &mode, file, line) with UNIT_HasState 0x00639DF0,
         UNIT_TestStateBit 0x00625B70 and PlrToMonMode run whole: gfxtype 1 and 2, players and monsters, the list
         order, the state bounds (timing 20's gfxtype 2 half; timing 130's remainder)

Controls as part 1: every named test reversed alone and every ordered compare's strictness switched alone; `sep`
counts the cases a control changes, `passed` those the emulator still matches (must be 0). Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from anim_s6e_emu import E, Img, Fatal, Runaway, s16, s32, u32, le32, read_out  # noqa: E402

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66l", "s6e", "run2")
XL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
MSBIN, MS2BIN = os.path.join(XL, "monstats.bin"), os.path.join(XL, "monstats2.bin")

G_DT = 0x00744304
DT, DT_LEN = 0x21000000, 0x1000
MS, MS_SZ = 0x21100000, 0x1A8
MS2, MS2_SZ = 0x21200000, 0x134
ST, ST_N, ST_SZ = 0x21300000, 64, 0x3C
LIST = 0x21310000
U, SL, BITS, OUT, PATH = 0x20000000, 0x20001000, 0x20002000, 0x20003000, 0x20004000
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)
BM, P2M, M2P = 0x006CE268, 0x006EB348, 0x006EB308
CONST_READS = ((BM, 128, "g_BitMask32"), (P2M, 80, "g_PlrToMonMode"), (M2P, 64, "g_MonToPlrMode"),
               (0x00645248, 0x18, "PlrToMonMode's jump table"), (0x00645260, 15, "PlrToMonMode's case index"))
FNS = {"pvs": 0x006502D0, "p2m": 0x00645190, "xform": 0x00645270}
POP = {"pvs": 0, "p2m": 8, "xform": 24}
FAMILIES = ("pvs", "p2m", "xform")
STEP = {5: 4, 7: 4, 6: 3, 9: 8, 10: 8, 11: 8, 15: 2}     # anim/timing B3's fallback steps; every other mode -> 1


class Tables:
    def __init__(self):
        d = open(MSBIN, "rb").read()
        self.msn = struct.unpack_from("<I", d)[0]
        self.ms = d[4:]
        d = open(MS2BIN, "rb").read()
        self.ms2n = struct.unpack_from("<I", d)[0]
        self.ms2 = d[4:]

    def idx2(self, cls):
        if not 0 <= cls < self.msn:                             # only a reversed bound test reads here: the bytes
            raise Runaway()                                     # past the table are not modelled, so no case matches
        return s16(struct.unpack_from("<H", self.ms, MS_SZ * cls + 0x18)[0])

    def modebits(self, i2):
        if not 0 <= i2 < self.ms2n:
            raise Runaway()
        return self.ms2[MS2_SZ * i2 + 0xF0:MS2_SZ * i2 + 0xF0 + 4]


# ------------------------------------------------------------------------------------------------ pvs
def m_pvs(e, a):
    """PathVelocityStep: -> the path's (+0x72, +0x76, +0x7C, +0x88, +0x8C) after the call."""
    k = s32(a["k"])
    if not e.c("kpos", k, ">", 0):
        k = 0x400
    v, acc, cnt, vmax = s32(a["v"]), s32(a["acc"]), s32(a["cnt"]), s32(a["vmax"])
    if e.t("acc", acc != 0):
        cnt = s32(cnt + 1)
        if e.c("c5", cnt, ">=", 5):
            v = s32(v + acc)
            if e.c("vmax", v, ">", vmax):
                v, acc = vmax, 0
            elif e.c("vneg", v, "<", 0):
                v = 0
            cnt = 0
    w32 = (lambda x: s32(x)) if e.t("wrap", True) else (lambda x: x)
    s = w32(v * k) >> 6 if e.t("sar6", True) else (u32(v * k) >> 6)
    dx = w32(s32(a["dx"]) * s) >> 12 if e.t("sar12", True) else u32(s32(a["dx"]) * s) >> 12
    dy = w32(s32(a["dy"]) * s) >> 12 if e.t("sar12", True) else u32(s32(a["dy"]) * s) >> 12
    return tuple(u32(x) for x in (dx, dy, v, acc, cnt))


def gen_pvs(rnd):
    out = []
    for v in range(32760, 32776):                               # the wrap sweep at k = 0x400 (movement 24)
        for d in (4096, -4096, 2896, -2896):
            out.append(dict(k=0x400, v=v, acc=0, cnt=0, vmax=0, dx=d, dy=-d, sweep=1))
    for _ in range(3000):
        k = rnd.choice([0x400, 0x400, 0, 1, 0xFFFFFFFF, 0x80000000, rnd.randrange(1, 0x2000), rnd.getrandbits(32)])
        v = rnd.choice([rnd.randrange(0, 0x400), rnd.randrange(0, 0x10000), rnd.randrange(32700, 32800),
                        u32(-rnd.randrange(1, 0x400)), rnd.getrandbits(32), 0])
        acc = rnd.choice([0, 0, rnd.randrange(1, 0x100), u32(-rnd.randrange(1, 0x100)), rnd.getrandbits(32)])
        cnt = rnd.choice([0, 1, 3, 4, 4, 5, 6, u32(-1), rnd.randrange(0, 10)])
        vmax = rnd.choice([u32(s32(v) + s32(acc)), u32(s32(v) + s32(acc) - 1), u32(s32(v) + s32(acc) + 1),
                           rnd.randrange(0, 0x1000), rnd.getrandbits(32), 0])
        dx, dy = rnd.choice([(4096, 0), (0, 4096), (-4096, 0), (2896, 2896), (-2896, 2896)] +
                            [(rnd.randrange(-4096, 4097), rnd.randrange(-4096, 4097))])
        out.append(dict(k=k, v=v, acc=acc, cnt=cnt, vmax=vmax, dx=dx, dy=dy, sweep=0))
    return out


def case_pvs(a):
    b = bytearray(0x26)                                         # path +0x6A .. +0x8F
    struct.pack_into("<ii", b, 0x00, a["dx"], a["dy"])          # +0x6A, +0x6E the direction
    struct.pack_into("<II", b, 0x08, 0xA5A5A5A5, 0xA5A5A5A5)    # +0x72, +0x76 the step (written)
    struct.pack_into("<I", b, 0x12, u32(a["v"]))                # +0x7C the speed
    struct.pack_into("<I", b, 0x1A, u32(a["vmax"]))             # +0x84 the speed cap
    struct.pack_into("<I", b, 0x1E, u32(a["acc"]))              # +0x88 the acceleration
    struct.pack_into("<I", b, 0x22, u32(a["cnt"]))              # +0x8C the call count
    return ["w %08x %s" % (PATH + 0x6A, bytes(b).hex()), "d %08x 38" % (PATH + 0x6A),
            "r EAX %08x" % PATH, "call %08x %08x 00000000" % (FNS["pvs"], u32(a["k"]))]


def obs_pvs(c):
    b = c["dumps"][PATH + 0x6A]
    dx, dy = struct.unpack_from("<II", b, 0x08)
    v, = struct.unpack_from("<I", b, 0x12)
    acc, cnt = struct.unpack_from("<II", b, 0x1E)
    return (dx, dy, v, acc, cnt)


# ------------------------------------------------------------------------------------------------ p2m
def p2m(e, tb, mode, cls, msn, ms2n):
    m = Img.dw(P2M + 4 * mode)
    for _ in range(64):
        if e.c("cneg", s32(cls), ">=", 0) and e.c("ccnt", s32(cls), "<", s32(msn)):
            i2 = tb.idx2(cls)
            if e.c("ineg", i2, ">=", 0) and e.c("icnt", i2, "<", s32(ms2n)):
                bits = tb.modebits(i2)
                if e.t("bit", bits[m >> 3] & Img.dw(BM + 4 * (m & 7))):
                    return m
        if e.t("ret1", m == 1):
            return m
        if e.t("s%d" % m, m in STEP) if m in STEP else False:
            m = STEP[m]
        else:
            m = 1
    raise Runaway()


def m_p2m(e, a, tb):
    return p2m(e, tb, a["mode"], a["cls"], a["msn"], a["ms2n"])


def gen_p2m(rnd, tb):
    out = []
    for cls in range(tb.msn):                                   # every player mode on every stock class
        for mode in range(20):
            out.append(dict(mode=mode, cls=cls, msn=tb.msn, ms2n=tb.ms2n))
    for _ in range(400):                                        # the bounds: classes and MonStats2 counts at the edges
        mode = rnd.randrange(20)
        cls = rnd.choice([u32(-1), 0x80000000, tb.msn, tb.msn + 1, rnd.randrange(tb.msn)])
        msn = tb.msn
        ms2n = tb.ms2n
        r = rnd.random()
        if r < 0.3 and cls < tb.msn:
            msn = rnd.choice([cls, cls + 1])                    # the class count at the class
        elif r < 0.6 and cls < tb.msn and tb.idx2(cls) >= 0:
            ms2n = rnd.choice([tb.idx2(cls), tb.idx2(cls) + 1])  # the MonStats2 count at the class's index
        out.append(dict(mode=mode, cls=cls, msn=msn, ms2n=ms2n))
    return out


def case_p2m(a):
    return ["w %08x %s" % (DT + 0xA80, le32(a["msn"]).hex()), "w %08x %s" % (DT + 0xA98, le32(a["ms2n"]).hex()),
            "call %08x 00000000 00000000 %08x %08x" % (FNS["p2m"], a["mode"], u32(a["cls"]))]


# ------------------------------------------------------------------------------------------------ xform
def m_xform(e, a, tb):
    """-> (type, class, mode) out dwords after UNIT_AnimTransform."""
    t, c, m = a["otype"], a["ocls"], a["omode"]
    if not e.t("unit", a["unit"] != 0) or not e.t("c8", a["c8"] & 8):
        return (t, c, m)
    ut = s32(a["utype"])
    for i in range(s16(a["listn"])):
        st = s16(a["list"][i])
        has = (e.c("utneg", ut, ">=", 0) and (e.c("ut1", ut, "<=", 1) or e.t("ut3", ut == 3))
               and e.c("sneg", st, ">=", 0) and e.c("scnt", st, "<", a["stn"])
               and e.t("sl", a["sl"] != 0) and e.t("sl31", a["slflags"] & 0x80000000)
               and e.t("bitset", st in a["on"]))
        if not e.t("has", has):
            continue
        if not (e.c("sneg2", st, ">=", 0) and e.c("scnt2", st, "<", a["stn"])):
            continue
        g, gc = a["gfx"][st]
        if e.t("g1", g == 1):
            t, c = 1, u32(gc)
            if e.t("pl", ut == 0):
                m = p2m(e, tb, m, gc, tb.msn, tb.ms2n)
            return (t, c, m)
        if e.t("g2", g == 2):
            t, c = 0, u32(gc)
            if e.t("mon", ut == 1):
                if e.t("as6", gc == 6) and e.t("kk4", m == 4):
                    m = 12
                else:
                    m = Img.dw(M2P + 4 * m)
            return (t, c, m)
    return (t, c, m)


def gen_xform(rnd, tb):
    out = []
    for k in range(3000):
        listn = rnd.choice([0, 1, 2, 3, 4, 6])
        stn = rnd.choice([ST_N, ST_N, 40, 0])
        lst = [rnd.choice([rnd.randrange(ST_N), rnd.randrange(ST_N), u32(-1) & 0xFFFF, ST_N, stn if stn else 1])
               for _ in range(listn)]
        gfx = {}
        for s in range(ST_N):
            g = rnd.choice([0, 1, 1, 2, 2, 3, 0xFF])
            gc = rnd.choice([6, 6, 0, 1, 4, rnd.randrange(tb.msn), 430, 431, rnd.randrange(7)])
            gfx[s] = (g, gc)
        on = {s for s in range(ST_N) if rnd.random() < 0.5}
        utype = rnd.choice([0, 0, 1, 1, 2, 3, 4, 5, u32(-1)])
        omode = rnd.randrange(20) if utype == 0 else rnd.randrange(16)
        if utype == 1 and rnd.random() < 0.3:
            omode = 4
        ocls = rnd.choice([rnd.randrange(7), rnd.randrange(tb.msn)])
        out.append(dict(unit=0 if k < 6 else U, c8=rnd.choice([8, 8, 8, 0xFFFFFFFF, 0, 0xFFFFFFF7]), utype=utype,
                        otype=utype, ocls=ocls, omode=omode, listn=listn, list=lst, stn=stn, gfx=gfx, on=on,
                        sl=0 if rnd.random() < 0.05 else SL,
                        slflags=0x80000000 if rnd.random() < 0.93 else rnd.choice([0, 0x7FFFFFFF])))
    return out


def case_xform(a):
    lines = ["w %08x %s" % (DT + 0xC4, le32(a["stn"]).hex()),
             "w %08x %s" % (DT + 0x180, struct.pack("<H", a["listn"]).hex())]
    if a["listn"]:
        lines.append("w %08x %s" % (LIST, b"".join(struct.pack("<H", x & 0xFFFF) for x in a["list"]).hex()))
    recs = bytearray(ST_N * ST_SZ)
    for s, (g, gc) in a["gfx"].items():
        recs[ST_SZ * s + 0x2D] = g
        struct.pack_into("<H", recs, ST_SZ * s + 0x2E, gc & 0xFFFF)
    lines.append("w %08x %s" % (ST, bytes(recs).hex()))
    bits = bytearray(8)
    for s in a["on"]:
        bits[s >> 3] |= 1 << (s & 7)
    lines += ["w %08x %s" % (BITS, bytes(bits).hex()),
              "w %08x %s" % (SL + 0x10, le32(a["slflags"]).hex()), "w %08x %s" % (SL + 0x58, le32(BITS).hex()),
              "w %08x %s" % (U, le32(a["utype"]).hex()), "w %08x %s" % (U + 0x5C, le32(a["sl"]).hex()),
              "w %08x %s" % (U + 0xC8, le32(a["c8"]).hex()),
              "w %08x %s" % (OUT, (le32(a["otype"]) + le32(a["ocls"]) + le32(a["omode"])).hex()),
              "d %08x 12" % OUT,
              "call %08x 00000000 00000000 %08x %08x %08x %08x 006cc837 00001234" % (FNS["xform"], a["unit"], OUT,
                                                                                   OUT + 4, OUT + 8)]
    return lines


# ------------------------------------------------------------------------------------------------ build, check
def build(tb):
    allc = []
    for fam in FAMILIES:
        rnd = random.Random("n66l-s6e2-" + fam)
        if fam == "pvs":
            allc += [("pvs", a) for a in gen_pvs(rnd)]
        elif fam == "p2m":
            allc += [("p2m", a) for a in gen_p2m(rnd, tb)]
        else:
            allc += [("xform", a) for a in gen_xform(rnd, tb)]
    return allc


def predict(fam, a, tb, flip=None):
    e = E(flip)
    try:
        if fam == "pvs":
            out = ("pvs",) + m_pvs(e, a)
        elif fam == "p2m":
            out = ("ret", u32(m_p2m(e, a, tb)))
        else:
            out = ("xform",) + tuple(u32(x) for x in m_xform(e, a, tb))
    except Fatal:
        out = ("fatal",)
    except Runaway:
        out = ("runaway",)
    return out, e.names


def observed(fam, c):
    if "stop" in c:
        return ("fatal",) if c["stop"] == FATAL[0] else ("stop", c["stop"], c["msg"])
    if fam == "pvs":
        return ("pvs",) + obs_pvs(c)
    if fam == "xform":
        return ("xform",) + struct.unpack("<III", c["dumps"][OUT])
    return ("ret", c["eax"])


def write_spec(d):
    with open(os.path.join(d, "s6e2-dt.bin"), "wb") as f:
        b = bytearray(DT_LEN)
        tb = Tables()
        struct.pack_into("<I", b, 0xA78, MS)
        struct.pack_into("<I", b, 0xA80, tb.msn)
        struct.pack_into("<I", b, 0xA90, MS2)
        struct.pack_into("<I", b, 0xA98, tb.ms2n)
        struct.pack_into("<I", b, 0xBC, ST)
        struct.pack_into("<I", b, 0xC4, ST_N)
        struct.pack_into("<I", b, 0x17C, LIST)
        f.write(b)
    mem = ["# plan 0066 S6e part 2 declared image (tools/anim_s6e2_emu.py)",
           "dword %08x %08x" % (G_DT, DT), "load %08x %s" % (DT, os.path.join(d, "s6e2-dt.bin")),
           "const load %08x %s" % (MS - 4, MSBIN), "const load %08x %s" % (MS2 - 4, MS2BIN),
           "bytes %08x %s" % (ST, "00" * (ST_N * ST_SZ)), "bytes %08x %s" % (LIST, "00" * 0x40),
           "bytes %08x %s" % (U, "00" * 0x100), "bytes %08x %s" % (SL, "00" * 0x60),
           "bytes %08x %s" % (BITS, "00" * 0x10), "bytes %08x %s" % (OUT, "00" * 0x10),
           "bytes %08x %s" % (PATH, "00" * 0xA0)]
    mem += ["guard %08x" % x for x in FATAL + ALLOC]
    with open(os.path.join(d, "s6e2.mem"), "w") as f:
        f.write("\n".join(mem) + "\n")


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    write_spec(d)
    tb = Tables()
    allc = build(tb)
    lines = []
    for fam, a in allc:
        lines += {"pvs": case_pvs, "p2m": case_p2m, "xform": case_xform}[fam](a)
    with open(os.path.join(d, "s6e2.cases"), "w") as f:
        f.write("\n".join(lines) + "\n")
    n = {}
    for fam, _ in allc:
        n[fam] = n.get(fam, 0) + 1
    print("CASES total=%d %s" % (len(allc), " ".join("%s=%d" % kv for kv in sorted(n.items()))))


def cmd_check(d):
    tb = Tables()
    allc = build(tb)
    calls, reads, writes = read_out(os.path.join(d, "s6e2.out"))
    print("CHECK cases=%d out=%d monstats=%d monstats2=%d" % (len(allc), len(calls), tb.msn, tb.ms2n))
    if len(calls) != len(allc):
        print("BAD count")
        return 1
    bad = stops = 0
    fams, names, preds, basep, tags = {}, {}, [], {}, {}
    for (fam, a), c in zip(allc, calls):
        want, nm = predict(fam, a, tb)
        basep[id(a)] = want
        got = observed(fam, c)
        preds.append(got)
        names.setdefault(fam, set()).update(nm)
        st = fams.setdefault(fam, [0, 0])
        st[0] += 1
        if want == got and ("stop" in c or c["pop"] == POP[fam]):
            st[1] += 1
        else:
            bad += 1
            if bad <= 30:
                print("BAD %s case=%d args=%s want=%s got=%s" % (fam, c["n"], {k: v for k, v in a.items()
                      if k not in ("gfx", "on")}, want, got))
        stops += got[0] == "stop"
        if fam == "p2m":
            m0 = Img.dw(P2M + 4 * a["mode"])
            k = "p2m:%s" % ("direct" if want[1] == m0 else "fallback->%d" % want[1])
        elif fam == "xform":
            k = "xform:%s" % ("unchanged" if want[1:] == (a["otype"], a["ocls"], a["omode"]) else
                              "g1" if want[1] == 1 else "g2")
            if k == "xform:g2" and a["utype"] == 1 and a["omode"] == 4 and want[3] == 12:
                k += ":kk12"
        else:
            k = "pvs:%s" % ("sweep" if a["sweep"] else "accel" if s32(a["acc"]) and s32(a["cnt"]) + 1 >= 5
                            else "plain")
        tags[k] = tags.get(k, 0) + 1
    for k in sorted(fams):
        print("FAMILY %s cases=%d match=%d" % ((k,) + tuple(fams[k])))
    for k in sorted(tags):
        print("TAG %s %d" % (k, tags[k]))
    # the wrap sweep (movement 24): the first v whose emulated axis step turns negative at d = +4096, k = 0x400
    for d in (4096, -4096, 2896, -2896):
        row = [(a["v"], s32(g[1])) for (f, a), g in zip(allc, preds) if f == "pvs" and a["sweep"] and a["dx"] == d]
        neg = [v for v, x in row if (x < 0) != (d < 0)]
        print("WRAP d=%d v=%d..%d steps=%s first_sign_flip=%s" % (d, row[0][0], row[-1][0],
              ",".join(str(x) for _, x in row[6:10]), neg[0] if neg else "none"))
    # the stock fallback chains (timing 20, 130's remainder): per display class used as a form, every player mode
    for cls in (430, 431):
        print("P2M class=%d %s" % (cls, " ".join("%d>%d" % (a["mode"], preds[i][1]) for i, (f, a) in
                                                 enumerate(allc) if f == "p2m" and a["cls"] == cls
                                                 and a["msn"] == tb.msn and a["ms2n"] == tb.ms2n)))
    # MonStats2's mode bit field: bit m of the u16 at +0xF0 against the .txt mode columns, every row (timing 20's
    # column names; the .bin is the record array the game reads, the .txt the table it is built from)
    cols = ("mDT", "mNU", "mWL", "mGH", "mA1", "mA2", "mBL", "mSC", "mS1", "mS2", "mS3", "mS4", "mDD", "mKB", "mSQ",
            "mRN")
    txt = open(os.path.join(XL, "monstats2.txt"), encoding="latin-1").read().splitlines()
    hd = txt[0].split("\t")
    rows = [r.split("\t") for r in txt[1:] if r.strip() and r.split("\t")[0] != "Expansion"]
    cbad = sum(1 for i, r in enumerate(rows[:tb.ms2n]) if struct.unpack_from("<H", tb.ms2, MS2_SZ * i + 0xF0)[0] !=
               sum(1 << m for m, c in enumerate(cols) if r[hd.index(c)].strip() not in ("", "0")))
    print("MS2COLS txt_rows=%d bin_rows=%d differing=%d" % (len(rows), tb.ms2n, cbad))
    bad += cbad + (len(rows) != tb.ms2n)
    nctl = unsep = 0
    for fam in sorted(names):
        for nm in sorted(names[fam]):
            sep = passed = 0
            for (f, a), got in zip(allc, preds):
                if f != fam:
                    continue
                alt, _ = predict(f, a, tb, nm)
                if alt != basep[id(a)]:
                    sep += 1
                    passed += alt == got
            nctl += 1
            unsep += sep == 0
            print("CONTROL %s %s sep=%d passed=%d%s" % (fam, nm, sep, passed, "" if sep else " UNSEPARATED"),
                  flush=True)
            bad += passed
    extra = 0
    for pc, addr, sz, cnt in reads:
        why = next((nm for lo, n, nm in CONST_READS if lo <= addr and addr + sz <= lo + n), None)
        print("READ pc=%08x addr=%08x size=%d count=%d %s" % (pc, addr, sz, cnt, why or "UNACCOUNTED"))
        extra += why is None
    for pc, addr, sz, cnt in writes:
        print("WRITE pc=%08x addr=%08x size=%d count=%d UNACCOUNTED" % (pc, addr, sz, cnt))
        extra += 1
    print("S6E2 total cases=%d bad=%d stops=%d controls=%d unseparated=%d unaccounted=%d" %
          (len(allc), bad, stops, nctl, unsep, extra))
    return 0 if bad == 0 and stops == 0 and extra == 0 else 1


def cmd_manifest(d, write):
    names = sorted(x for x in os.listdir(d) if os.path.isfile(os.path.join(d, x)) and x != "manifest.sha256")
    out = []
    for n in names:
        with open(os.path.join(d, n), "rb") as f:
            out.append("%s  %s" % (hashlib.sha256(f.read()).hexdigest(), n))
    text = "\n".join(out) + "\n"
    if write:
        with open(os.path.join(d, "manifest.sha256"), "w") as f:
            f.write(text)
    print(text, end="")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("cases", "check", "manifest"))
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    o = ap.parse_args(argv)
    if o.cmd == "cases":
        cmd_cases(o.dir)
        return 0
    if o.cmd == "check":
        return cmd_check(o.dir)
    cmd_manifest(o.dir, o.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S6e (`lane/n66l`): anim/timing functions run whole under Ghidra's p-code emulator
(ADR-0015, ADR-0021, ADR-0029) with re/ghidra_scripts/EmuBoundary.java, compared with the models below. No game, no
slot. As in S1e (tools/ai_s1e_emu.py), no callee is an observed boundary and no callee return is declared (ruling R2
of the plan 0066 inventory): every callee runs emulated on the declared image, so each case's claim is the function's
whole map, from the declared image to its return value and the bytes it writes.

    python3 -I tools/anim_s6e_emu.py cases [--dir D]     write D/s6e.cases, D/s6e.mem and the region images
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s6e.cases D/s6e.mem > D/s6e.out
    python3 -I tools/anim_s6e_emu.py check [--dir D]     compare D/s6e.out with the models, account for every traced
                                                          read and write, run the per-test controls
    python3 -I tools/anim_s6e_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66l/s6e/run. Every case draw comes from random.Random("n66l-s6e-<family>"), so `cases`
regenerates identical files. The animdata file is read from workspace/merged/data/global/animdata.d2 (game data: it
stays in the workspace; the memory spec names its path).

The declared image (memory spec, re-applied before every case, then the case's own `w` lines):
  the DataTables pointer 0x00744304 -> DT (+0xA78/+0xA80 MonStats base and count, records 0x1A8; +0xB98/+0xBA0
  Skills base and count, records 0x23C; all other bytes 0; MonStats and Skills zero but for the case's writes);
  the animdata pointer 0x0096C8A4 -> CONT (the loader's container: +0 the file buffer, +4 + 4 b the pointer to block
  b found by walking the file as ANIMDATA_Load 0x0066A7E1-0x0066A804 does, +0x404 the fallback record with
  +0x40C 0x800 and +0x410 0x100, as 0x0066A80A-0x0066A814 store; the container and the file are `const`, written
  once: no code under test writes them); the game (+0xA8 the frame, +0xB8 -> POOL); the event pool (+0xA1C -> BLOCK,
  the rest 0: the bucket heads); the event block (+0x7080 the free-node head, +0x7084 0; nodes of 0x30 bytes chained
  in order by +0x1C); units and records in case memory.
Image constants read (no code writes them, .rdata): g_BitMask32 words 0 and 3 (0x006CE268, 0x006CE274), the mode-class
tables 0x006E8A00 (player, 20 x 5 dwords), 0x006E8B90 and 0x006E8CD0 (monster, 16 x 5), the event type table
0x006E0B9C (6 dwords). Guards: the fatal path (0x00408090, 0x00408A60, 0x00681E09) and the allocators (0x0040B4B0,
0x0040B430, 0x0040B480). A case the model sends to the fatal path must stop at 0x00408090.

Families (function, inventory rows of anim-timing.md):
  atend  0x006217C0 UNIT_AnimAtEnd (41)
  find   0x0066A8F0 ANIMDATA_Find, EBX the name: every stock name (17, 19), case variants, absent names (9, 16),
         long names, bytes after the NUL
  sched  0x005539B0 SUNIT_ScheduleModeEvents with sub_005416B0_EventQueueAt and the event pool run whole (10, 32, 33,
         34; remainders of 21, 36, 96); start frame 0 (a monster, or a player outside modes 7, 8, 15, 16, with
         Unit+0xC8 bit 3 clear); no sequence
  pred   0x006214A0 AnimRateIsMove, 0x00621580 AnimRateIsAttack, 0x00621630 AnimRateIsFixed, 0x006216E0
         AnimRateIsCast, and the two small mode tests 0x00621680 (get-hit) and 0x006216B0 (block) (89)

Controls. Every named test of a model is reversed alone, and every ordered compare has its strictness switched alone
(`<` and `<=`, `>` and `>=`; name + "~"). For each control the check counts the cases whose predicted outputs it
changes (`sep`) and how many of those the emulator output still matches (`passed`, must be 0). A control with sep 0
is listed as unseparated: no case of the run tells that test from its reversal, and the claim on it stays `[I]`.
Stdlib only.
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

import anim_scan as AS  # noqa: E402
import animdata as AD   # noqa: E402

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66l", "s6e", "run")
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
ANIMDATA = os.path.join(ROOT, "workspace", "merged", "data", "global", "animdata.d2")
M32 = 0xFFFFFFFF

G_DT, G_AD = 0x00744304, 0x0096C8A4
DT, DT_LEN = 0x21000000, 0x1000
MS, MS_N, MS_SZ = 0x21100000, 0x1A0, 0x1A8
SK, SK_N, SK_SZ = 0x21200000, 0x100, 0x23C
CONT, FILE = 0x23000000, 0x23100000
GAME, POOL, BLOCK = 0x22000000, 0x22100000, 0x22200000
NODES, NODE = 200, 0x30
U, U2, U3, U4 = 0x20000000, 0x20001000, 0x20002000, 0x20003000
REC = 0x20004000
NAMEBUF = 0x20006000
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)
BM0, BM3 = 0x006CE268, 0x006CE274
TP, TM, TX = 0x006E8A00, 0x006E8B90, 0x006E8CD0
EVTYPE = 0x006E0B9C
CONST_READS = ((BM0, 4, "g_BitMask32[0]"), (BM3, 4, "g_BitMask32[3]"), (TP, 400, "g_PlrModeRateClass"),
               (TM, 320, "monster mode-class table < 410"), (TX, 320, "monster mode-class table >= 410"),
               (EVTYPE, 24, "event type index table"),
               (0x00553AFC, 16, "SUNIT_ScheduleModeEvents' event-code jump table"),
               (0x00623C04, 0x16, "UNIT_AnimStartFrame's mode jump tables"))
FNS = {"atend": 0x006217C0, "find": 0x0066A8F0, "sched": 0x005539B0,
       "move": 0x006214A0, "attack": 0x00621580, "fixed": 0x00621630, "cast": 0x006216E0,
       "gethit": 0x00621680, "block": 0x006216B0}
FAMILIES = ("atend", "find", "sched", "pred")


def u32(v):
    return v & M32


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def s8(v):
    v &= 0xFF
    return v - 0x100 if v & 0x80 else v


def le32(v):
    return struct.pack("<I", u32(v))


class Fatal(Exception):
    pass


class Runaway(Exception):
    """A reversed test that would loop past any base case's bound: an outcome no emulated case can match."""


class E:
    """One model run: the named tests and the reversal or strictness control."""

    def __init__(self, flip=None):
        self.flip = flip
        self.names = set()

    def t(self, name, cond):
        self.names.add(name)
        return (not cond) if self.flip == name else bool(cond)

    def c(self, name, a, op, b):
        self.names.add(name)
        self.names.add(name + "~")
        if self.flip == name + "~":
            op = {"<": "<=", "<=": "<", ">": ">=", ">=": ">"}[op]
        r = {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]
        return (not r) if self.flip == name else r


class Img:
    """The pinned image's .rdata, for the constants the models read (the same bytes the emulator reads)."""
    pe = None

    @classmethod
    def dw(cls, a):
        if cls.pe is None:
            cls.pe = AS.PE(EXE)
        return cls.pe.dw(a)


# ------------------------------------------------------------------------------------------------ atend
def m_atend(e, a):
    """UNIT_AnimAtEnd(unit) -> bool. a: dict(unit, seq, L, pos, rate) or unit 0."""
    if not e.t("null", a["unit"] != 0):
        raise Fatal()
    if e.t("seq", a["seq"] != 0):
        return int(e.c("seqle", s32(a["L"]), "<=", 0))
    r = s16(a["rate"]) if e.t("signext", True) else a["rate"] & 0xFFFF
    v = s32(r + a["pos"]) if e.t("wrap32", True) else r + s32(a["pos"])
    return int(e.c("ge", v, ">=", s32(a["L"])))


def gen_atend(rnd):
    out = []
    edges = [0, 1, 0xFF, 0x100, 0x101, 0x7FFF, 0x8000, 0xFFFF, 0x80, 0xFF00]
    for k in range(600):
        if k < 2:
            out.append(dict(unit=0, seq=0, L=0, pos=0, rate=0))
            continue
        seq = rnd.choice([0, 0, 0, U4, rnd.getrandbits(32) | 1])
        L = rnd.choice([0, 1, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF, rnd.randrange(1, 0x3000), rnd.getrandbits(32),
                        0x100 * rnd.randrange(1, 40)])
        rate = rnd.choice(edges + [rnd.getrandbits(16)])
        mode = rnd.randrange(4)
        if mode == 0:
            pos = u32(L - s16(rate) + rnd.choice([-1, 0, 1]))      # at the boundary
        elif mode == 1:
            pos = u32(0x7FFFFFFF - rnd.randrange(0, 0x100))         # the add wraps
        else:
            pos = rnd.choice([0, rnd.randrange(0, 0x3000), rnd.getrandbits(32)])
        out.append(dict(unit=U, seq=seq, L=L, pos=pos, rate=rate))
    return out


def case_atend(a):
    if a["unit"] == 0:
        return ["call %08x 00000000 00000000 00000000" % FNS["atend"]]
    u = a["unit"]
    return ["w %08x %s" % (u + 0x30, le32(a["seq"]).hex()),
            "w %08x %s" % (u + 0x44, (le32(a["pos"]) + le32(a["L"]) + struct.pack("<H", a["rate"])).hex()),
            "call %08x 00000000 00000000 %08x" % (FNS["atend"], u)]


# ------------------------------------------------------------------------------------------------ find
class AnimFile:
    def __init__(self, path):
        self.data = open(path, "rb").read()
        self.recs = AD.parse(self.data)
        self.blocks = []                    # (file offset of the block, count)
        off = 0
        for _b in range(256):               # the loader's walk, 0x0066A7F0-0x0066A804: next = this + 4 + 160 n
            n = struct.unpack_from("<I", self.data, off)[0]
            self.blocks.append((off, n))
            off += 4 + 160 * n

    def cont(self):
        b = bytearray(0x4A4)
        b[0:4] = le32(FILE)
        for i, (off, _n) in enumerate(self.blocks):
            b[4 + 4 * i:8 + 4 * i] = le32(FILE + off)
        b[0x40C:0x410] = le32(0x800)
        b[0x410:0x414] = le32(0x100)
        return bytes(b)


def cstrlen(buf, i=0):
    n = 0
    while i + n < len(buf) and buf[i + n] != 0:
        n += 1
    return n


def m_find(e, a, af):
    """ANIMDATA_Find(EBX = name) -> (record VA or 0, the name buffer after)."""
    buf = bytearray(a["buf"])
    i = 0
    while buf[i] != 0:
        c = buf[i]
        if e.c("lo", s8(c), ">=", 0x61) and e.c("hi", s8(c), "<=", 0x7A):
            buf[i] = (c - 0x20) & 0xFF
        i += 1
    h = sum(buf[:cstrlen(buf)])
    h = h & 0xFF if e.t("mask8", True) else h & 0x7F
    off, n = af.blocks[h]
    p = off + 4
    found = 0
    n = s32(n)
    guard = 0
    while e.c("cnt", n, ">", 0):
        guard += 1
        if guard > 4096:                                        # only the reversed count test runs this far
            raise Runaway()
        if e.c("namelen", cstrlen(buf), ">", 8):
            raise Fatal()
        if e.c("reclen", cstrlen(af.data, p), ">", 8):
            raise Fatal()
        d0 = buf[0:4] == af.data[p:p + 4]
        d1 = buf[4:8] == af.data[p + 4:p + 8]
        if d0 and (d1 or not e.t("dw2", True)):
            if e.t("first", True):
                return FILE + p, bytes(buf)
            found = FILE + p
        n -= 1
        p += 160
    return found, bytes(buf)


def gen_find(rnd, af):
    out = []
    names = []
    for r in af.recs:
        if r.name not in names:
            names.append(r.name)
    dups = sorted({r.name for r in af.recs if sum(1 for x in af.recs if x.name == r.name) > 1})
    empty = [b for b in range(256) if af.blocks[b][1] == 0]

    def buf_of(s, tail=b""):
        b = bytearray(16)
        b[:len(s)] = s
        b[len(s) + 1:len(s) + 1 + len(tail)] = tail
        return bytes(b)

    def mixcase(s):
        return bytes(c + 0x20 if 0x41 <= c <= 0x5A and rnd.random() < 0.5 else c for c in s)
    for nm in names:                                            # every stock name, upper case as stored
        out.append(dict(buf=buf_of(nm.encode()), kind="stock"))
    for nm in names:                                            # every stock name again, mixed case
        out.append(dict(buf=buf_of(mixcase(nm.encode())), kind="mixed"))
    for nm in dups * 3:                                         # the duplicates, upper and mixed
        out.append(dict(buf=buf_of(mixcase(nm.encode())), kind="dup"))
    for _ in range(300):                                        # absent names (random tokens)
        s = bytes(rnd.choice(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz") for _ in
                  range(rnd.randrange(1, 8)))
        out.append(dict(buf=buf_of(s), kind="absent"))
    for _ in range(120):                                        # a stock name with bytes after the NUL
        nm = rnd.choice(names).encode()
        tail = bytes(rnd.randrange(1, 256) for _ in range(rnd.randrange(1, 4)))
        out.append(dict(buf=buf_of(nm, tail[:7 - len(nm)] if len(nm) < 7 else b""), kind="tail"))
    for _ in range(80):                                         # bytes outside 'a'..'z', high bytes among them
        nm = bytearray(rnd.choice(names).encode())
        j = rnd.randrange(len(nm))
        nm[j] = rnd.choice([0x60, 0x7B, 0x40, 0x5B, 0xE1, 0xFA, 0x80, 0xFF, 0x61, 0x7A])
        out.append(dict(buf=buf_of(bytes(nm)), kind="odd"))
    for k in range(60):                                         # long names: 8 (fits), 9-12 (fatal in a used block)
        ln = 8 if k % 3 == 0 else rnd.randrange(9, 13)
        s = bytearray(rnd.choice(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(ln))
        if k % 2 == 0 and empty:                                # steer half of them into an empty block
            want = rnd.choice(empty)
            d = (want - sum(s)) & 0xFF
            for j in range(len(s)):
                take = min(d, 0x5A - s[j])
                s[j] += take
                d -= take
        out.append(dict(buf=buf_of(bytes(s)), kind="long"))
    return out


def case_find(a):
    return ["w %08x %s" % (NAMEBUF, a["buf"].hex()), "r EBX %08x" % NAMEBUF, "d %08x 16" % NAMEBUF,
            "call %08x 00000000 00000000" % FNS["find"]]


# ------------------------------------------------------------------------------------------------ sched
def m_sched(e, a):
    """SUNIT_ScheduleModeEvents(game, unit), start frame 0, no sequence. -> (queued [(kind, frame, a, b)], +0x44)."""
    T = s32(a["T"])
    q = []

    def queue(kind, frame, x, y):                               # sub_005416B0_EventQueueAt: frame <= T -> T + 1
        frame = s32(frame)
        if not e.c("qfr", frame, ">", T):
            frame = s32(T + 1)
        q.append((kind, frame, x, y))
    r = s16(a["rate"]) if e.t("signext", True) else a["rate"] & 0xFFFF
    L = s32(a["L"])
    if e.t("r0", r == 0):
        queue(1, T + 1, 0, 0)
        return q, None
    t, f, n = T, 0, 0
    if e.flip is None:
        a["_steps"] = 0
    acc = s32(0 + r)
    ev = a["ev"]
    steps = 0
    while e.c("accL", acc, "<", L):
        steps += 1
        if steps > a.get("_cap", 300000):                       # only a reversed test runs this far: past twice
            raise Runaway()                                     # the base case's own step count
        hi = acc >> 8
        if e.flip is None:
            a["_steps"] += 1
        t = s32(t + 1)
        while e.c("fhi", f, "<=", hi) and (not e.t("bound", True) or e.c("b90", f, "<", 0x90)):
            if f > 0x100000:
                raise Runaway()
            x = ev[f] if f < len(ev) else 0
            if 1 <= x <= 4:
                if e.t("e3", x == 3):
                    queue(0, t, x, 0)
                else:
                    queue(0, t, x, n)
                    n += 1
            f += 1
        acc = s32(acc + r)
    if e.t("tT", t == T):
        t += 1
    queue(1, t + 1, 0, 0)
    return q, u32(T << 8)


def gen_sched(rnd):
    out = []
    for k in range(1300):
        F = rnd.choice([1, 2, 3, 4, 6, 8, 10, 12, 13, 15, 16, 17, 18, 20, 24, 0x8E, 0x8F, 0x90, 0x91, 0x92, 0xA0, 0xA8])
        L = F << 8
        if rnd.random() < 0.1:
            L += rnd.randrange(1, 256)                          # a length that is not a whole frame count
        ev = [0] * 0xB0
        for _ in range(rnd.choice([0, 1, 2, 3, 6, 20])):
            j = rnd.randrange(min(0xB0, F + 4))
            ev[j] = rnd.choice([1, 2, 3, 4, 5, 0xFF, 1, 2, 4])
        if F > 0x90 and rnd.random() < 0.7:                     # events past the 0x90 bound
            for j in range(0x90, min(F, 0xB0)):
                if rnd.random() < 0.5:
                    ev[j] = rnd.choice([1, 2, 3, 4])
        cls = rnd.random()
        if k < 40:
            rate = 0                                            # r = 0
        elif cls < 0.15:
            rate = rnd.choice([L, L + 1, L - 1, 2 * L, 0x7FFF, max(1, L - rnd.randrange(1, 0x80))]) & 0x7FFF
        elif cls < 0.18:
            rate = rnd.choice([0x8000, 0xC000, 0x8001])             # negative rates: the add wraps at last
        else:
            rate = rnd.choice([1, 0x40, 0x80, 0xFF, 0x100, 0x101, 0x180, 0x200, rnd.randrange(1, 0x400),
                               rnd.randrange(1, 0x8000)])
        if rate >= 0x8000 and L > 0x1000:
            L = 0x1000
            F = 0x10
        T = rnd.choice([rnd.randrange(0, 1 << 20), rnd.randrange(0, 1 << 30), 0, 1])
        typ = rnd.choice([0, 1, 1])
        mode = rnd.choice([0, 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 17, 18, 19]) if typ == 0 else rnd.randrange(16)
        if rate in (1,) and L > 0x2000:
            L, F = 0x2000, 0x20
        out.append(dict(T=T, L=L, rate=rate, ev=ev, typ=typ, mode=mode, cls=rnd.randrange(0, 700)))
    return out


def case_sched(a, nq):
    u = U
    lines = ["w %08x %s" % (GAME + 0xA8, le32(a["T"]).hex()),
             "w %08x %s" % (u + 0x00, (le32(a["typ"]) + le32(a["cls"])).hex()),
             "w %08x %s" % (u + 0x0C, (le32(0x1234 + a["cls"]) + le32(a["mode"])).hex()),
             "w %08x %s" % (u + 0x30, le32(0).hex()),
             "w %08x %s" % (u + 0x44, (le32(0xA5A5A5A5) + le32(a["L"]) + struct.pack("<H", a["rate"])).hex()),
             "w %08x %s" % (u + 0x50, le32(REC).hex()),
             "w %08x %s" % (u + 0xC8, le32(0).hex()),
             "w %08x %s" % (u + 0xDC, le32(0).hex()),
             "w %08x %s" % (REC + 0x10, bytes(a["ev"]).hex()),
             "d %08x 4" % (u + 0x44), "d %08x 4" % (u + 0xDC),
             "d %08x %d" % (BLOCK, NODE * min(NODES, nq + 3)),
             "call %08x %08x %08x" % (FNS["sched"], GAME, u)]
    return lines


# ------------------------------------------------------------------------------------------------ pred
def usedskill(e, a):
    if not e.t("unitnull", a["unit"] != 0):
        raise Fatal()
    return a["skill"] if a["slist"] else 0


def skillrec(a, sid):
    return sid if 0 <= sid < a["skn"] else None


def m_pred(e, a):
    fn, typ, mode, cls = a["fn"], a["typ"], a["mode"], s32(a["cls"])

    def table(c):
        return TM if e.c("c410", c, "<", 0x19A) else TX
    if fn == "move":
        if typ == 0:
            row = TP + 20 * mode
        elif typ == 1:
            if e.c("cneg", cls, ">=", 0) and e.c("ccnt", cls, "<", a["msn"]) and e.t("npc", a["npc"] & Img.dw(BM0)):
                return int(e.t("npcmode", mode in (2, 15)))
            row = table(cls) + 20 * mode
        else:
            raise Fatal()
        if e.t("mv", Img.dw(row + 4) != 0):
            return 1
        if not e.t("smv", Img.dw(row) != 0):
            return 0
        sk = usedskill(e, a)
        if not e.t("sk", sk != 0):
            return 0
        fl = a["flags"]
        return int(e.t("fl1", fl & 1) and not e.t("fl1000", fl & 0x1000))
    if fn == "attack":
        if typ == 0:
            row = TP + 20 * mode
        elif typ == 1:
            row = table(cls) + 20 * mode
        else:
            raise Fatal()
        if e.t("at", Img.dw(row + 12) != 0):
            return 1
        if not e.t("sat", Img.dw(row + 8) != 0):
            return 0
        sk = usedskill(e, a)
        if not e.t("sk", sk != 0):
            return 0
        return a["rec6"] & Img.dw(BM3) if e.t("uar", True) else a["rec6"] & 0xFF
    if fn == "fixed":
        if typ == 0:
            return Img.dw(TP + 20 * mode + 16)
        if typ == 1:
            return Img.dw(table(cls) + 20 * mode + 16)
        return 0
    if fn == "cast":
        if typ == 1:
            return int(e.t("m7", mode == 7))
        if typ != 0:
            return 0
        if e.t("p10", mode == 10):
            return 1
        if not e.t("p18", mode == 18) or not e.t("cu", a["unit"] != 0):
            return 0
        sk = a["skill"] if a["slist"] else 0
        if not e.t("sk", sk != 0):
            return 0
        if skillrec(a, s16(a["recid"])) is None:
            return 0
        return int(e.t("sq10", a["rec12"] == 10))
    if fn == "gethit":
        return int(e.t("gh", (typ == 0 and mode == 4) or (typ == 1 and mode == 3)))
    if fn == "block":
        return int(e.t("bl", (typ == 0 and mode == 9) or (typ == 1 and mode == 6)))
    raise ValueError(fn)


def gen_pred(rnd):
    out = []
    for fn in ("move", "attack", "fixed", "cast", "gethit", "block"):
        combos = []
        for typ in (0, 1, 2, 3, 4, 5):
            for mode in range(20 if typ == 0 else 16):
                combos.append((typ, mode))
        for rep in range(4):
            for typ, mode in combos:
                if fn in ("move", "attack") and typ >= 2 and rnd.random() < 0.8:
                    continue                                    # the fatal path: a few cases only
                a = dict(fn=fn, typ=typ, mode=mode)
                a["cls"] = rnd.choice([rnd.randrange(0, 0x19A), rnd.randrange(0x19A, 0x1A0), 0x199, 0x19A,
                                       rnd.randrange(0, 0x1A0), 0xFFFFFFFF, 0x80000000, 0x1A0, 0x1A5])
                a["msn"] = rnd.choice([MS_N, MS_N, 0x19B, 0x100])
                a["npc"] = rnd.choice([0, 0, 1, 0xFF, 0xFE])
                a["unit"] = 0 if rnd.random() < 0.05 else U
                a["slist"] = 0 if rnd.random() < 0.15 else U2
                a["skill"] = 0 if rnd.random() < 0.15 else U3
                a["flags"] = rnd.choice([0, 1, 0x1001, 0x1000, 0xFFFFFFFF, rnd.getrandbits(32)])
                a["skn"] = SK_N
                a["recid"] = rnd.randrange(0, SK_N)
                a["rec6"] = rnd.choice([0, 8, 0xFF, 0xF7, rnd.getrandbits(8)])
                a["rec12"] = rnd.choice([10, 10, 0, 9, 11, 0x8A, rnd.getrandbits(8)])
                if fn == "cast" and rnd.random() < 0.5:
                    a["mode"] = rnd.choice([10, 18, 7])
                out.append(a)
        if fn == "move":                                        # the class bounds of the npc test, exactly
            for cls, msn in ((0, MS_N), (0x19B, 0x19B), (0x19A, 0x19B), (1, MS_N)):
                for mode in (2, 3, 8, 15):
                    out.append(dict(fn=fn, typ=1, mode=mode, cls=cls, msn=msn, npc=1, unit=U, slist=U2, skill=U3,
                                    flags=1, skn=SK_N, recid=5, rec6=8, rec12=10))
    return out


def case_pred(a):
    fn, lines = a["fn"], []
    lines.append("w %08x %s" % (DT + 0xA80, le32(a["msn"]).hex()))
    cls = s32(a["cls"])
    if 0 <= cls < MS_N:
        lines.append("w %08x %02x" % (MS + MS_SZ * cls + 0x0D, a["npc"] & 0xFF))
    if a["unit"]:
        lines.append("w %08x %s" % (U + 0xA8, le32(a["slist"]).hex()))
        if a["slist"]:
            lines.append("w %08x %s" % (U2 + 0x10, le32(a["skill"]).hex()))
        if a["skill"]:
            rec = SK + SK_SZ * a["recid"]
            lines.append("w %08x %s" % (U3 + 0x00, le32(rec).hex()))
            lines.append("w %08x %s" % (U3 + 0x0C, le32(a["flags"]).hex()))
            lines.append("w %08x %s" % (rec, struct.pack("<H", a["recid"]).hex()))
            lines.append("w %08x %02x" % (rec + 6, a["rec6"]))
            lines.append("w %08x %02x" % (rec + 0x12, a["rec12"]))
    f = FNS[fn]
    t, m, c, u = a["typ"], a["mode"], u32(a["cls"]), a["unit"]
    if fn == "move":
        lines += ["r ESI %08x" % c, "call %08x %08x %08x %08x" % (f, t, m, u)]
    elif fn == "attack":
        lines.append("call %08x %08x %08x %08x %08x" % (f, m, t, u, c))
    elif fn == "fixed":
        lines += ["r EAX %08x" % t, "call %08x %08x 00000000 %08x" % (f, m, c)]
    elif fn == "cast":
        lines += ["r EAX %08x" % t, "call %08x %08x %08x" % (f, u, m)]
    else:
        lines += ["r EAX %08x" % t, "call %08x %08x 00000000" % (f, m)]
    return lines


POP = {"atend": 4, "find": 0, "sched": 0, "move": 4, "attack": 8, "fixed": 4, "cast": 0, "gethit": 0, "block": 0}


# ------------------------------------------------------------------------------------------------ cases, check
def build(af):
    """-> list of (family, args), in file order, and the per-case expected node count for sched."""
    allc = []
    for fam in FAMILIES:
        rnd = random.Random("n66l-s6e-" + fam)
        if fam == "atend":
            allc += [("atend", a) for a in gen_atend(rnd)]
        elif fam == "find":
            allc += [("find", a) for a in gen_find(rnd, af)]
        elif fam == "sched":
            allc += [("sched", a) for a in gen_sched(rnd)]
        else:
            allc += [(a["fn"], a) for a in gen_pred(rnd)]
    return allc


def predict(fam, a, af, flip=None):
    e = E(flip)
    try:
        if fam == "atend":
            out = ("ret", m_atend(e, a))
        elif fam == "find":
            out = ("find",) + m_find(e, a, af)
        elif fam == "sched":
            out = ("sched",) + (lambda q: (tuple(q[0]), q[1]))(m_sched(e, a))
        else:
            out = ("ret", u32(m_pred(e, a)))
    except Fatal:
        out = ("fatal",)
    except Runaway:
        out = ("runaway",)
    return out, e.names


def write_spec(d, af):
    with open(os.path.join(d, "s6e-dt.bin"), "wb") as f:
        b = bytearray(DT_LEN)
        b[0xA78:0xA7C] = le32(MS)
        b[0xA80:0xA84] = le32(MS_N)
        b[0xB98:0xB9C] = le32(SK)
        b[0xBA0:0xBA4] = le32(SK_N)
        f.write(b)
    with open(os.path.join(d, "s6e-ms.bin"), "wb") as f:
        f.write(bytes(MS_N * MS_SZ))
    with open(os.path.join(d, "s6e-sk.bin"), "wb") as f:
        f.write(bytes(SK_N * SK_SZ))
    with open(os.path.join(d, "s6e-cont.bin"), "wb") as f:
        f.write(af.cont())
    with open(os.path.join(d, "s6e-game.bin"), "wb") as f:
        b = bytearray(0x200)
        b[0xB8:0xBC] = le32(POOL)
        f.write(b)
    with open(os.path.join(d, "s6e-pool.bin"), "wb") as f:
        b = bytearray(0x1000)
        b[0xA1C:0xA20] = le32(BLOCK)
        f.write(b)
    with open(os.path.join(d, "s6e-block.bin"), "wb") as f:
        b = bytearray(0x7088)
        for i in range(NODES):
            nxt = BLOCK + NODE * (i + 1) if i + 1 < NODES else 0
            b[NODE * i + 0x1C:NODE * i + 0x20] = le32(nxt)
        b[0x7080:0x7084] = le32(BLOCK)
        f.write(b)
    mem = ["# plan 0066 S6e declared image (tools/anim_s6e_emu.py)",
           "dword %08x %08x" % (G_DT, DT), "load %08x %s" % (DT, os.path.join(d, "s6e-dt.bin")),
           "load %08x %s" % (MS, os.path.join(d, "s6e-ms.bin")), "load %08x %s" % (SK, os.path.join(d, "s6e-sk.bin")),
           "dword %08x %08x" % (G_AD, CONT),
           "const load %08x %s" % (CONT, os.path.join(d, "s6e-cont.bin")),
           "const load %08x %s" % (FILE, ANIMDATA),
           "load %08x %s" % (GAME, os.path.join(d, "s6e-game.bin")),
           "load %08x %s" % (POOL, os.path.join(d, "s6e-pool.bin")),
           "load %08x %s" % (BLOCK, os.path.join(d, "s6e-block.bin")),
           "bytes %08x %s" % (U, "00" * 0x100), "bytes %08x %s" % (U2, "00" * 0x20),
           "bytes %08x %s" % (U3, "00" * 0x20), "bytes %08x %s" % (REC, "00" * 0xC0)]
    mem += ["guard %08x" % x for x in FATAL + ALLOC]
    with open(os.path.join(d, "s6e.mem"), "w") as f:
        f.write("\n".join(mem) + "\n")


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    af = AnimFile(ANIMDATA)
    write_spec(d, af)
    allc = build(af)
    lines = []
    for fam, a in allc:
        if fam == "atend":
            lines += case_atend(a)
        elif fam == "find":
            lines += case_find(a)
        elif fam == "sched":
            p, _ = predict(fam, a, af)
            lines += case_sched(a, len(p[1]))
        else:
            lines += case_pred(a)
    with open(os.path.join(d, "s6e.cases"), "w") as f:
        f.write("\n".join(lines) + "\n")
    n = {}
    for fam, _ in allc:
        n[fam] = n.get(fam, 0) + 1
    print("CASES total=%d %s" % (len(allc), " ".join("%s=%d" % kv for kv in sorted(n.items()))))


def read_out(path):
    calls, reads, writes = [], [], []
    for ln in open(path):
        p = ln.split()
        if not p:
            continue
        if p[0] == "C":
            c = {"n": int(p[1]), "fn": int(p[2], 16), "dumps": {}}
            if p[3] == "STOP":
                c["stop"] = int(p[4], 16)
                c["msg"] = " ".join(p[5:])
            elif p[3] == "OBS":
                c["stop"] = -1
                c["msg"] = "observe"
            else:
                kv = dict(x.split("=") for x in p[3:])
                c.update(eax=int(kv["eax"], 16), pop=int(kv["pop"]))
            calls.append(c)
        elif p[0] == "D":
            calls[-1]["dumps"][int(p[1], 16)] = bytes.fromhex(p[2]) if len(p) > 2 else b""
        elif p[0] in ("R", "W"):
            (reads if p[0] == "R" else writes).append((int(p[1], 16), int(p[2], 16), int(p[3]), int(p[4])))
    return calls, reads, writes


def observed(fam, c):
    """-> the emulator's outcome in predict()'s shape."""
    if "stop" in c:
        return ("fatal",) if c["stop"] == FATAL[0] else ("stop", c["stop"], c["msg"])
    if fam == "find":
        return ("find", c["eax"], c["dumps"][NAMEBUF])
    if fam == "sched":
        head = struct.unpack("<I", c["dumps"][U + 0xDC])[0]
        blk = c["dumps"][BLOCK]
        nodes = []
        seen = 0
        while head:
            off = head - BLOCK
            if off < 0 or off + NODE > len(blk) or seen > NODES:
                return ("sched-bad-list", head)
            kind, fr = blk[off], s32(struct.unpack_from("<I", blk, off + 4)[0])
            x, y = struct.unpack_from("<II", blk, off + 0x14)
            nodes.append((kind, fr, x, y))
            head = struct.unpack_from("<I", blk, off + 0x24)[0]
            seen += 1
        pos = struct.unpack("<I", c["dumps"][U + 0x44])[0]
        return ("sched", tuple(reversed(nodes)), pos)
    return ("ret", c["eax"])


def same(fam, want, got, a):
    if want[0] == "sched" and got[0] == "sched":
        return want[1] == got[1] and (want[2] is None and got[2] == 0xA5A5A5A5 or want[2] == got[2])
    return want == got


def cmd_check(d):
    af = AnimFile(ANIMDATA)
    allc = build(af)
    calls, reads, writes = read_out(os.path.join(d, "s6e.out"))
    print("CHECK cases=%d out=%d" % (len(allc), len(calls)))
    if len(calls) != len(allc):
        print("BAD count")
        return 1
    fams = {}
    bad = stops = 0
    names = {}
    preds = []
    basep = {}
    tags = {}
    for (fam, a), c in zip(allc, calls):
        famk = fam if fam in ("atend", "find", "sched") else "pred:" + fam
        want, nm = predict(fam, a, af)
        basep[id(a)] = want
        if fam == "sched":
            a["_cap"] = 2 * a.get("_steps", 0) + 1000
        got = observed(fam, c)
        preds.append((fam, a, got))
        names.setdefault(famk, set()).update(nm)
        st = fams.setdefault(famk, [0, 0, 0])
        st[0] += 1
        ok = same(fam, want, got, a) and ("stop" in c or c["pop"] == POP[fam])
        if want == ("fatal",):
            st[2] += 1
        if ok:
            st[1] += 1
        else:
            bad += 1
            if bad <= 30:
                print("BAD %s case=%d args=%s want=%s got=%s" % (famk, c["n"], {k: v for k, v in a.items()
                      if k not in ("ev", "buf")}, str(want)[:200], str(got)[:200]))
        if got[0] == "stop":
            stops += 1
        k = None
        if fam == "find":
            k = "find:%s:%s" % (a["kind"], "hit" if got[0] == "find" and got[1] else ("fatal" if got[0] == "fatal"
                                                                                       else "none"))
        elif fam == "sched":
            k = "sched:%s" % ("r0" if a["rate"] == 0 else "neg" if a["rate"] >= 0x8000 else
                              "nostep" if (a["rate"] >= a["L"]) else "steps")
            if got[0] == "sched" and any(fr for kd, fr, x, y in got[1] if kd == 0) and a["L"] > 0x9000:
                k += ":past90"
        elif fam == "atend":
            k = "atend:%s" % ("null" if not a["unit"] else "seq" if a["seq"] else "plain")
        if k:
            tags[k] = tags.get(k, 0) + 1
    for k in sorted(fams):
        print("FAMILY %s cases=%d match=%d fatal_expected=%d" % ((k,) + tuple(fams[k])))
    for k in sorted(tags):
        print("TAG %s %d" % (k, tags[k]))
    # duplicates: the earlier record of a name wins
    first = {}
    for r in af.recs:
        first.setdefault(r.name, r)
    dn = 0
    for (fam, a), (_f, _a, got) in zip(allc, preds):
        if fam == "find" and a["kind"] == "dup" and got[0] == "find":
            nm = a["buf"].split(b"\0")[0].upper().decode()
            fr = first[nm]
            off = got[1] - FILE
            if af.blocks[fr.block][0] + 4 + 160 * fr.slot == off:
                dn += 1
    print("DUP earlier-record-wins %d of %d dup cases" % (dn, sum(1 for f, a in allc if f == "find" and
                                                                    a["kind"] == "dup")))
    # E2's closed form (anim/timing E2, K1) against the emulated lists: L = 256 F, start 0, 0 < r < 0x8000
    e2 = e2bad = drop = nostep = 0
    for (fam, a), (_f, _a, got) in zip(allc, preds):
        if fam != "sched" or got[0] != "sched" or a["L"] % 256 or not 0 < a["rate"] < 0x8000:
            continue
        F, r, T = a["L"] >> 8, a["rate"], a["T"]
        K = -(-256 * F // r)
        N = K - 1
        evs, n, dropped = [], 0, 0
        for f in range(min(F, 0x90)):
            x = a["ev"][f]
            if 1 <= x <= 4:
                k = max(1, -(-256 * f // r))
                if k <= N:
                    evs.append((0, T + k, x, 0 if x == 3 else n))
                    n += x != 3
                else:
                    dropped += 1
        want = tuple(evs) + ((1, T + max(2, N + 1), 0, 0),)
        e2 += 1
        drop += dropped > 0
        nostep += N == 0 and any(1 <= x <= 4 for x in a["ev"][:min(F, 0x90)])
        if want != got[1]:
            e2bad += 1
            if e2bad <= 5:
                print("BAD e2 F=%d r=%d want=%s got=%s" % (F, r, want[:4], got[1][:4]))
    print("E2 closed-form cases=%d bad=%d with_dropped_event=%d no_step_with_event=%d" % (e2, e2bad, drop, nostep))
    bad += e2bad
    # J3: the mode-class tables as the spec lists them
    j3 = {"P": (TP, 20, {"move": {2, 3, 6}, "attack": {7, 8, 11, 12}, "skillmove": {13, 14, 15, 16, 18},
                         "skillattack": {13, 14, 15, 16, 18}, "fixed": {0, 17}}),
          "M<410": (TM, 16, {"move": {2, 15, 8, 9, 10, 11}, "attack": {4, 5}, "skillmove": {8, 9, 10, 11, 14},
                             "skillattack": {8, 9, 10, 11, 14}, "fixed": {0, 12}}),
          "M>=410": (TX, 16, {"move": {2, 15}, "attack": {4, 5}, "skillmove": {8, 9, 10, 11, 14},
                              "skillattack": {8, 9, 10, 11, 14}, "fixed": {0, 12}})}
    print("J3 note: expected sets are J3's outcomes plus two table facts J3 does not state: below 410 S1-S4 also "
          "carry the skill flags (moot: IsMove tests +4 first), and monster SQ (14) is skill-dependent in both tables")
    j3bad = 0
    for tn, (base, cnt, want) in sorted(j3.items()):
        for col, off in (("skillmove", 0), ("move", 4), ("skillattack", 8), ("attack", 12), ("fixed", 16)):
            got = {m for m in range(cnt) if Img.dw(base + 20 * m + off)}
            ok = got == want[col]
            j3bad += not ok
            print("J3 %s %s modes=%s%s" % (tn, col, ",".join(map(str, sorted(got))), "" if ok else
                                          " DIFFERS spec=%s" % ",".join(map(str, sorted(want[col])))))
    print("J3 tables bad=%d" % j3bad)
    # the stock records the 0x90 bound can touch
    over = [r for r in af.recs if r.frames > 0x90]
    print("ANIMDATA records=%d frames_over_0x90=%d (max frames %d)" % (len(af.recs), len(over),
                                                                     max(r.frames for r in af.recs)))
    for r in over:                                              # what an unbounded scan would read past 0x90
        p = af.blocks[r.block][0] + 4 + 160 * r.slot
        past = af.data[p + 0x10 + 0x90:p + 0x10 + r.frames]
        print("ANIMDATA over0x90 %s frames=%d event_bytes=%d bytes_1to4_past_0x90=%d of %d" %
              (r.name, r.frames, sum(1 for x in r.events if 1 <= x <= 4), sum(1 for x in past if 1 <= x <= 4),
               len(past)))
    # controls
    nctl = unsep = 0
    for famk in sorted(names):
        for nm in sorted(names[famk]):
            sep = passed = 0
            for (fam, a), (_f, _a, got) in zip(allc, preds):
                fk = fam if fam in ("atend", "find", "sched") else "pred:" + fam
                if fk != famk:
                    continue
                base = basep[id(a)]
                alt, _ = predict(fam, a, af, nm)
                if alt != base:
                    sep += 1
                    if same(fam, alt, got, a):
                        passed += 1
            nctl += 1
            if sep == 0:
                unsep += 1
            print("CONTROL %s %s sep=%d passed=%d%s" % (famk, nm, sep, passed, "" if sep else " UNSEPARATED"),
                  flush=True)
            bad += passed
    # read and write accounting
    extra = 0
    for pc, addr, sz, cnt in reads:
        why = next((nm for lo, n, nm in CONST_READS if lo <= addr and addr + sz <= lo + n), None)
        print("READ pc=%08x addr=%08x size=%d count=%d %s" % (pc, addr, sz, cnt, why or "UNACCOUNTED"))
        extra += why is None
    for pc, addr, sz, cnt in writes:
        print("WRITE pc=%08x addr=%08x size=%d count=%d UNACCOUNTED" % (pc, addr, sz, cnt))
        extra += 1
    print("S6E total cases=%d bad=%d stops=%d controls=%d unseparated=%d unaccounted=%d" %
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

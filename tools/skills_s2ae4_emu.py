#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S2ae part 4 (`lane/n66sa`): the zig-zag re-seed callback and MissileCreate up to its
SUnitCreate call under Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java, and the
route reads (per call site: allocator and import reach) of the part's rows.

    python3 -I tools/skills_s2ae4_emu.py cases [--dir D] [--limit N]   write D/s2ae.cases, D/s2ae.mem and the tables
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s2ae.cases D/s2ae.mem > D/s2ae.out
    python3 -I tools/skills_s2ae4_emu.py check [--dir D] [--limit N]   compare, account for traced reads, controls
    python3 -I tools/skills_s2ae4_emu.py reach [--limit N]             model outcomes and branch reach per family
    python3 -I tools/skills_s2ae4_emu.py static                        objdump of the functions run; the .data
                                                                        values read and their reference scans
    python3 -I tools/skills_s2ae4_emu.py sites                         per root: each direct call site and whether
                                                                        its callee reaches the pool allocator or an
                                                                        import (tools/skills_s2ae3_emu.py's walk)
    python3 -I tools/skills_s2ae4_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66sa/s2ae/run4. Parts 1-3 (tools/skills_s2ae_emu.py, skills_s2ae2_emu.py,
skills_s2ae3_emu.py) and their run/, run2/, run3/ are unchanged; this tool reuses part 1's check machinery (build,
predict, cmd_check) and PathDirection model (m_pdir), and part 3's Mem view, objdump, reference scan and site walk,
in its module state only. Every draw comes from random.Random("n66sa-s2ae4-<family>"); the declared Missiles rows
from random.Random("n66sa-s2ae4-tables").

The models read each case's own memory (an unwritten read is a model error) and the image (.rdata tables, and the
.data words 0x00741B0C, 0x00741B10 and the 64 bytes at 0x00745600, read from the pinned file: `static` lists every
.text reference to them). Every callee runs whole on the declared image unless named as an observed boundary
(ADR-0021): the case ends at that call and its claim ends there. The allocator entries and the fatal path are guards.

Families (function, registers; inventory rows, m = skills/missiles):
  zz   0x005D4680 sub_005D4680_MissCbReseedZigzag (ECX unit, EDX the argument), whole, with MISSDATA_GetRange
       0x0064A300, the range setters 0x0064A2B0/0x0064A330, RNG_SeedInit, sub_00648CF0_PathSetType (type 10),
       sub_00648E70_PathSetByte90, 0x006487D0 (the point list), the path getters, sub_00621DC0_UnitDirToPoint with
       0x0064FDC0 and sub_0064FC60_PathDirection (part 1's model), 0x0063E7A0 (the 64-to-8 direction byte at
       0x00745600) and 0x00648790 (the point count).                                             m76
  mcr  0x0059FA30 sub_0059FA30_MissileCreate (ECX game, EDX the parameter block), to its first allocation: observed
       boundary sub_00555230_SUnitCreate from 0x0059FC75 (ruling R2: the pool allocation lies past it). Whole
       before it: sub_0046ACE0_MissileRec, UnitGetSubX/Y, sub_00620BB0_UnitGetRoom, sub_00648A80_PathGetRoom,
       sub_00463740_RoomAtSubtile with 0x00619790 (the neighbour list), UNIT_HasState (0x00625B70),
       UNIT_FindStatListByState (0x00625650), sub_00625D00 -> 0x00625350 -> 0x00624ED0 / 0x00624B90 (the state
       list's base stat 161, ItemStatCost declared as zero records). At the boundary the frame's locals (target,
       x, y, velocity, tx, ty, row) are dumped from the stack.                                   m14, m16-19

Controls as parts 1-3: every named test reversed alone, every ordered compare's strictness switched alone; `sep`
counts the cases a control changes, `passed` those the emulator still matches (must be 0); `spec_*` controls are
the alternatives the spec names or rules out. Stdlib only, plus objdump for `static` and `sites`.
"""
import argparse
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import combat_s5e_emu as p1  # noqa: E402
import skills_s2ae_emu as B  # noqa: E402
import skills_s2ae3_emu as P3  # noqa: E402
from combat_s5e_emu import u32, s32, le32, tdiv, G_DT, DT, FATAL, ALLOC, BITMASK  # noqa: E402

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66sa", "s2ae", "run4")
FNS = {"zz": 0x005D4680, "mcr": 0x0059FA30}
FAMILIES = ("zz", "mcr")
NCASES = {"zz": 2500, "mcr": 4000}
POP = {"zz": 0, "mcr": 0}
p1.FNS.update(FNS)

SUNIT = 0x00555230
MCR_SITE = 0x0059FC7A                  # the return address of the call at 0x0059FC75
FATAL_PC = 0x00408090                  # the first guard of the fatal path
PDT, PDT_N = 0x006EB7E0, 128
PT_FLAGS, PT_W98 = 0x006EB690, 0x006EB648      # PathSetType's two per-type .rdata tables (type 10 read)
DIRX, DIRY = 0x006E32AC, 0x006E328C            # 8 dwords each (.rdata)
DIR64 = 0x00745600                             # 64 bytes read (.data)
ZZ_PERIOD, ZZ_BASE = 0x00741B0C, 0x00741B10    # .data words
NSTATES = 0xC0
ISC, ISC_N, ISC_SZ = 0x21100000, 0x200, 0x144
MIS, MIS_N, MIS_SZ = 0x21600000, 0x50, 0x1A4
FRAME = 0x7FEFFFE0                             # EBP - 0x1C of MissileCreate's frame (EBP = 0x7FEFFFFC)

ZU = 0x20020000                                # zz: the unit, its missile data, its path
ZD, ZP = ZU + 0x200, ZU + 0x400
ZP_N = 0x1D0                                   # the path through its point list (+0x9C, 77 points of 4 bytes)
PRM = 0x20030000                               # mcr: the parameter block
UNITS = (0x20040000, 0x20041000, 0x20042000)   # owner, source, target; path at +0x400, stat list at +0x600
ROOM, NB, NBL = 0x20070000, 0x20070100, 0x20070800
SL2, ARR2 = 0x20050000, 0x20050100

TABLES = None
IMGC = {}


def tables():
    global TABLES
    if TABLES is None:
        r = random.Random("n66sa-s2ae4-tables")
        TABLES = bytearray(r.getrandbits(8) for _ in range(MIS_N * MIS_SZ))
        for i in range(MIS_N):
            rec = i * MIS_SZ
            if r.random() < 0.5:                      # CanSlow (+4 bit 3) set in about half the rows
                TABLES[rec + 4] |= 0x08
            else:
                TABLES[rec + 4] &= ~0x08
            if r.random() < 0.3:                      # small Vel / VelLev in some rows
                TABLES[rec + 0x9A] = r.randrange(40)
                TABLES[rec + 0x9B] = r.randrange(16)
            if r.random() < 0.15:
                TABLES[rec + 0x9A] = 0
                TABLES[rec + 0x9B] = 0
    return TABLES


def mrow(cls, off):
    return tables()[cls * MIS_SZ + off]


def img32(va):
    if va not in IMGC:
        IMGC[va] = struct.unpack("<I", B.img_bytes(va, 4))[0]
    return IMGC[va]


def imgs32(va):
    return s32(img32(va))


def img8(va):
    return B.img_bytes(va, 1)[0]


class Case(p1.Case):
    pass


Mem = P3.Mem


def rbytes(rnd, n):
    return bytes(rnd.getrandbits(8) for _ in range(n))


def lcg2(lo, hi):
    v = lo * 0x6AC690C5 + hi
    return v & 0xFFFFFFFF, (v >> 32) & 0xFFFFFFFF


def dumped(M, dumps):
    return tuple(bytes(M.b(va + i) for i in range(n)) for va, n in dumps)


# ----------------------------------------------------------------------------------------------- zz
def gen_zz(rnd):
    c = Case("zz")
    typ = rnd.choice([3] * 10 + [0, 1, 2, 4, 5])
    c.put(ZU, rbytes(rnd, 0x100))
    c.put(ZU, le32(typ))
    data = ZD if (typ != 3 or rnd.random() < 0.96) else 0
    c.put(ZU + 0x14, le32(data))
    c.put(ZD, rbytes(rnd, 0x20))
    rng = rnd.choice([rnd.randint(1, 40), rnd.randint(1, 40), rnd.randint(1, 76), 0x4C, 0x4D, 0x4E, 0x4F,
                      rnd.randint(0x4E, 0x7FFF), 0, rnd.randint(-0x8000, -1), rnd.choice([-1, -0xB3, -0x100])])
    c.put(ZD + 0xE, struct.pack("<h", rng))
    c.put(ZU + 0x2C, le32(ZP))
    c.put(ZP, rbytes(rnd, ZP_N))
    c.put(ZP + 0x30, le32(rnd.choice([0, 0, ZU])))
    f40 = rnd.choice([rnd.getrandbits(32)] * 12 + [rnd.randrange(16)] * 4 + [8, 0xB])
    c.put(ZP + 0x40, le32(f40))
    # the domain: the unit's sub-tile and its target differ by at most 250 in x and in y (PathDirection's
    # (minor << 16) * 0x7F fits an i32 to 258; past it the index leaves g_PathDirTable)
    span = rnd.choice([0, 1, 3, 30, 120, 250])
    lx, ly = rnd.randrange(0x400, 0x7000), rnd.randrange(0x400, 0x7000)
    d = lambda: rnd.randint(-span, span)  # noqa: E731
    if typ in (2, 4, 5):
        ly = lx + d()                      # a static unit's y dword is also the target words +0x10/+0x12:
        c.put(ZP + 0xC, le32((rnd.getrandbits(16) << 16) | lx))   # tx = its low word (y), ty = its high word
        c.put(ZP + 0x10, struct.pack("<HH", ly, ly + d()))
    else:
        c.put(ZP + 2, struct.pack("<H", lx))
        c.put(ZP + 6, struct.pack("<H", ly))
        c.put(ZP + 0x10, struct.pack("<HH", lx + d(), ly + d()))
    c.ecx = 0 if rnd.random() < 0.02 else ZU
    c.edx = rnd.getrandbits(32)
    c.dumps = [(ZU + 0x20, 8), (ZD + 0xC, 8), (ZP, ZP_N)]
    c.a = dict(w=dict(c.w), ecx=c.ecx, edx=c.edx, dumps=list(c.dumps))
    return c


def unit_xy(M, u):
    """UnitGetSubX/Y (and the inlined copies): a static type's path dwords +0x0C/+0x10, else the path words +2/+6."""
    t = s32(M.d(u))
    p = M.d(u + 0x2C)
    if t == 2 or 3 < t <= 5:
        return M.d(p + 0xC), M.d(p + 0x10)
    if p == 0:
        return 0, 0
    return M.h(p + 2), M.h(p + 6)


def zz_dir(e, M, u):
    """sub_00621DC0_UnitDirToPoint(u, tx, ty) -> 0x0064FDC0 -> PathDirection: the direction index's low byte."""
    p = M.d(u + 0x2C)
    tx, ty = M.h(p + 0x10), M.h(p + 0x12)
    x, y = unit_xy(M, u)
    w = B.m_pdir(e, dict(x1=u32((x << 16) + 0x8000), y1=u32((y << 16) + 0x8000),
                         x2=u32((tx << 16) + 0x8000), y2=u32((ty << 16) + 0x8000)))
    if w[0] != "ret":
        raise IndexError("pdir")
    return w[2] & 0xFF


def m_zz(e, a):
    M = Mem(a["w"])
    u = a["ecx"]
    if not e.t("unit_nz", u != 0):
        return ("ret", dumped(M, a["dumps"]))
    d = M.d(u + 0x14)
    n = 0
    if e.t("type3", s32(M.d(u)) == 3) and e.t("data_nz", d != 0):
        n = P3.sx16(M.h(d + 0xE))
    if e.c("n_ge_4e", n, ">=", 0x4E):
        n = 0x4D
        M.put(d + 0xE, 0x4D, 2)                      # both setters: type 3 with data, as the getter just read
        M.put(d + 0x10, 0x4D, 2)
    p = M.d(u + 0x2C)
    seed = u + 0x20
    M.put(seed, a["edx"])
    M.put(seed + 4, 0x29A)
    # PathSetType(p, 10): the type's flags (0x60000) have neither 0x2000 nor 0x8000
    c30 = M.d(p + 0x30)
    if c30:
        M.d(c30)                                     # read by the type-2 test; 10 is not 2
    M.put(p + 0x34, (M.d(p + 0x34) & 0xFFF800FF) | img32(PT_FLAGS + 4 * 10))
    M.put(p + 0x3C, 10)
    M.put(p + 0x98, img32(PT_W98 + 4 * 10))
    f40 = M.d(p + 0x40)
    if e.t("f40_b", f40 == 0xB) or e.t("f40_8", f40 == 8):
        return ("stop", FATAL_PC, None)
    b = n & 0xFF
    if not e.c("b_lt_4d", b, "<", 0x4D):            # unsigned byte compare
        b = 0x4D
    M.put(p + 0x91, b, 1)
    M.put(p + 0x90, b, 1)
    lst = p + 0x9C
    if e.t("static", s32(M.d(u)) in (2, 4, 5)):
        x, y = M.d(p + 0xC), M.d(p + 0x10)
    else:
        x, y = M.h(p + 2), M.h(p + 6)
    dr = zz_dir(e, M, u)
    lo1, hi1 = lcg2(M.d(seed), M.d(seed + 4))
    sgn = 1 if e.t("odd", lo1 & 1) else -1
    lo, hi = lcg2(lo1, hi1)
    M.put(seed, lo)
    M.put(seed + 4, hi)
    per, base = imgs32(ZZ_PERIOD), imgs32(ZZ_BASE)
    amp = s32(lo % 3 + base)
    e.names.add("spec_no_flip")
    i = 0
    while e.c("i_lt_n", i, "<", n):
        dr = s32(dr + s32(amp * sgn))
        d8 = img8(DIR64 + (dr & 0x3F))
        x = s32(x + imgs32(DIRX + 4 * d8))
        y = s32(y + imgs32(DIRY + 4 * d8))
        M.put(lst + 4 * i, x & 0xFFFF, 2)
        M.put(lst + 4 * i + 2, y & 0xFFFF, 2)
        if e.t("i_mod_per", i % per == 0):
            if e.flip != "spec_no_flip":
                sgn = -sgn
            lo, hi = lcg2(lo, hi)
            M.put(seed, lo)
            M.put(seed + 4, hi)
            amp = s32(lo % 3 + base)
        i += 1
        if i > 0x100:
            raise IndexError("loop")
    M.put(p + 0x28, u32(n if n <= 0x4D else 0x4D))
    return ("ret", dumped(M, a["dumps"]))


# ----------------------------------------------------------------------------------------------- mcr
def put_path(c, rnd, u, typ, xy, room):
    p = u + 0x400
    c.put(u + 0x2C, le32(p))
    c.put(p, rbytes(rnd, 0x20))
    x, y = xy
    if typ in (2, 4, 5):
        c.put(p + 0xC, le32(x) + le32(y))
    else:
        c.put(p + 2, struct.pack("<H", x & 0xFFFF))
        c.put(p + 6, struct.pack("<H", y & 0xFFFF))
        c.put(p + 0x1C, le32(room))


def put_states(c, rnd, u, st87, node_kind, s161):
    """The unit's stat list at +0x600 (flag, the state bits with 87 set or clear), its state-list chain (one node at
    SL2 under head +0x3C or +0x40, or none) and the node's base-stat array (stat 161 at layer 0, or absent)."""
    sl = u + 0x600
    c.put(u + 0x5C, le32(sl))
    c.put(sl, rbytes(rnd, 0x60))
    flag = rnd.random() < 0.9
    c.put(sl + 0x10, le32((0x80000000 if flag else 0) | rnd.getrandbits(31)))
    bits = sl + 0x80
    words = [rnd.getrandbits(32) for _ in range(NSTATES // 32)]
    w = 87 >> 5
    words[w] = (words[w] | (1 << (87 & 31))) if st87 else (words[w] & ~(1 << (87 & 31)))
    c.put(sl + 0x58, le32(bits))
    for i, x in enumerate(words):
        c.put(bits + 4 * i, le32(x))
    h3c = h40 = 0
    if node_kind:
        nst = rnd.choice([87, 87, 87, rnd.randrange(1, NSTATES)])
        c.put(SL2, rbytes(rnd, 0x60))
        c.put(SL2 + 0x14, le32(nst))
        c.put(SL2 + 0x2C, le32(0))
        keys = {(200 << 16): rnd.getrandbits(32), (161 << 16) | 1: rnd.getrandbits(32)}
        if s161 is not None:
            keys[161 << 16] = u32(s161)
        if rnd.random() < 0.5:
            keys[rnd.randrange(1, 160) << 16] = rnd.getrandbits(32)
        ks = sorted(keys, key=s32)
        for i, k in enumerate(ks):
            c.put(ARR2 + 8 * i, le32(k) + le32(keys[k]))
        c.put(SL2 + 0x24, le32(ARR2) + struct.pack("<H", len(ks)) + bytes(2))
        if node_kind == 1:
            h3c = SL2
        else:
            h40 = SL2
    c.put(sl + 0x3C, le32(h3c))
    c.put(sl + 0x40, le32(h40))


def put_unit(c, rnd, k, typ, xy, room=ROOM):
    u = UNITS[k]
    c.put(u, rbytes(rnd, 0x100))
    c.put(u, le32(typ))
    put_path(c, rnd, u, typ, xy, room)
    return u


def gen_mcr(rnd):
    c = Case("mcr")
    rx, ry = rnd.randrange(0, 0x4000), rnd.randrange(0, 0x4000)
    rw, rh = rnd.choice([8, 16, 40, rnd.randrange(1, 80)]), rnd.choice([8, 16, 40, rnd.randrange(1, 80)])
    c.put(ROOM, rbytes(rnd, 0x60))
    c.put(ROOM + 0x4C, le32(rx) + le32(ry) + le32(rw) + le32(rh))
    nnb = rnd.choice([0, 1, 2, 3, 4])
    c.put(ROOM, le32(NBL))
    c.put(ROOM + 0x24, le32(nnb))
    nbs = []
    for j in range(nnb):
        if rnd.random() < 0.1:
            c.put(NBL + 4 * j, le32(0))
            continue
        nb = NB + 0x100 * j
        nx = rx + rnd.choice([-rw, rw, 0]) + rnd.randint(-3, 3)
        ny = ry + rnd.choice([-rh, rh, 0]) + rnd.randint(-3, 3)
        nw, nh = rnd.choice([rw, 8, 16]), rnd.choice([rh, 8, 16])
        c.put(nb + 0x4C, le32(nx) + le32(ny) + le32(nw) + le32(nh))
        c.put(NBL + 4 * j, le32(nb))
        nbs.append((nx, ny, nw, nh))

    def pt(near=True):
        if near and rnd.random() < 0.8:
            return rx + rnd.randrange(rw), ry + rnd.randrange(rh)
        if nbs and rnd.random() < 0.6:
            nx, ny, nw, nh = rnd.choice(nbs)
            return nx + rnd.randrange(nw), ny + rnd.randrange(nh)
        return rx + rnd.randint(-100, rw + 100), ry + rnd.randint(-100, rh + 100)

    otyp = rnd.choice([0, 0, 1, 1, 1] * 5 + [2, 3, 4, -1])
    oxy = pt()
    owner = put_unit(c, rnd, 0, otyp, oxy, room=rnd.choice([ROOM] * 30 + [0]))
    st87 = rnd.random() < 0.6
    node_kind = rnd.choice([1, 1, 1, 2, 0]) if st87 or rnd.random() < 0.2 else 0
    s161 = rnd.choice([rnd.randint(1, 100), rnd.randint(1, 100), 0, rnd.randint(-100, -1), rnd.getrandbits(32), None,
                       50, 100, 25])
    put_states(c, rnd, owner, st87, node_kind, s161)
    source = put_unit(c, rnd, 1, rnd.choice([0, 1, 1, 2, 3, 4, 5]), pt())
    tr = rnd.random()
    if tr < 0.35:
        target = 0
    elif tr < 0.45:
        target = owner
    else:
        ttyp = rnd.choice([0, 1, 1, 2, 3, 4, 5])
        if rnd.random() < 0.15:
            txy = oxy                              # on the owner's sub-tile
        elif rnd.random() < 0.35:
            txy = (oxy[0] + rnd.choice([-1, 1]) * rnd.choice([99, 100, 101, rnd.randint(50, 300)]),
                   oxy[1] + rnd.choice([0, rnd.randint(-120, 120)]))
            if rnd.random() < 0.5:
                txy = (oxy[0] + txy[1] - oxy[1], oxy[1] + txy[0] - oxy[0])
        else:
            txy = pt()
        target = put_unit(c, rnd, 2, ttyp, txy)
    flags = rnd.getrandbits(32) & ~0x3F
    for bit, pr in ((1, 0.4), (2, 0.25), (0x20, 0.25), (4, 0.25), (0x10, 0.5)):
        if rnd.random() < pr:
            flags |= bit
    cls = rnd.choice([rnd.randrange(MIS_N)] * 12 + [-1, MIS_N, MIS_N + 7, rnd.getrandbits(32)])
    x, y = pt() if rnd.random() < 0.9 else (rnd.getrandbits(32), rnd.getrandbits(32))
    if flags & 0x20 and rnd.random() < 0.08:
        tx, ty = u32(x + 0x80000000), u32(y + rnd.choice([0, 0x80000000, 50]))
    elif flags & 0x20:
        tx = x + rnd.choice([0, 0, rnd.randint(-120, 120), 99, 100, -99, -100])
        ty = y + rnd.choice([0, 0, rnd.randint(-120, 120), 99, 100, -100])
    else:
        tx = rnd.choice([0, 0, rnd.randint(-120, 120), 99, 100, -100, rnd.getrandbits(32)])
        ty = rnd.choice([0, 0, rnd.randint(-120, 120), 99, 100, -99, rnd.getrandbits(32)])
    vel = rnd.choice([0, 0, rnd.randint(1, 40), rnd.randint(1, 0x4000), rnd.getrandbits(32), rnd.randint(-40, -1)])
    lvl = rnd.choice([1, 1, rnd.randint(1, 30), rnd.randint(1, 99), 0, rnd.randint(-20, -1), rnd.getrandbits(32),
                      8, 7, 9, 16, 0x7FFFFFFF])
    c.put(PRM, rbytes(rnd, 0x40))
    ow = owner if rnd.random() < 0.97 else 0
    sw = source if rnd.random() < 0.9 else 0
    for off, v in ((0, flags), (4, ow), (8, sw), (0xC, target), (0x10, u32(cls)), (0x14, u32(x)), (0x18, u32(y)),
                   (0x1C, u32(tx)), (0x20, u32(ty)), (0x28, u32(vel)), (0x30, u32(lvl))):
        c.put(PRM + off, le32(v))
    c.ecx, c.edx = 0x20090000 + rnd.randrange(0x1000) * 4, PRM
    c.dumps = [(FRAME, 0x1C)]
    c.a = dict(w=dict(c.w), game=c.ecx)
    return c


def room_at(e, M, room, x, y):
    """sub_00463740_RoomAtSubtile(room, x, y): the room itself when (x, y) lies inside, else the first entry of its
    neighbour list (0x00619790: [room], count [room + 0x24], unsigned) that holds it; signed bounds."""
    if room == 0:
        return 0

    def inside(r, tag):
        x0, y0 = s32(M.d(r + 0x4C)), s32(M.d(r + 0x50))
        return (e.c(tag + "x0", x, ">=", x0) and e.c(tag + "x1", x, "<", s32(x0 + s32(M.d(r + 0x54))))
                and e.c(tag + "y0", y, ">=", y0) and e.c(tag + "y1", y, "<", s32(y0 + s32(M.d(r + 0x58)))))
    if inside(room, "r_"):
        return room
    lst, n = M.d(room), M.d(room + 0x24)
    for i in range(n):
        if i > 16:
            raise IndexError("neighbours")
        r = M.d(lst + 4 * i)
        if e.t("nb_nz", r != 0) and inside(r, "nb_"):
            return r
    return 0


def has_state(M, u, st):
    t = s32(M.d(u))
    if not (0 <= t <= 1 or t == 3) or not 0 <= st < NSTATES:
        return False
    sl = M.d(u + 0x5C)
    if sl == 0 or not M.d(sl + 0x10) & 0x80000000:
        return False
    return bool(M.d(M.d(sl + 0x58) + 4 * (st >> 5)) & (1 << (st & 31)))


def find_state_list(M, u, st):
    sl = M.d(u + 0x5C)
    if sl == 0 or not M.d(sl + 0x10) & 0x80000000:
        return 0
    for head in (M.d(sl + 0x3C), M.d(sl + 0x40)):
        q = head
        for _ in range(8):
            if q == 0:
                break
            if M.d(q + 0x14) == st:
                return q
            q = M.d(q + 0x2C)
    return 0


def base_stat(M, sl, stat, layer=0):
    """0x00625350 -> 0x00624ED0 / 0x00624B90: the signed binary search of the list's +0x24 array (the ItemStatCost
    records are declared zero, so no flag adjusts the value)."""
    if sl == 0 or not 0 <= stat < ISC_N:
        return 0
    key = s32((stat << 16) + layer)
    arr, n = M.d(sl + 0x24), P3.sx16(M.h(sl + 0x28))
    lo, hi = 0, n
    while lo < hi:
        mid = lo + tdiv(hi - lo, 2)
        k = s32(M.d(arr + 8 * mid))
        if key > k:
            lo = mid + 1
        elif key < k:
            hi = mid
        else:
            return s32(M.d(arr + 8 * mid + 4))
    return 0


def m_mcr(e, a):
    M = Mem(a["w"])
    p = PRM
    REF = ("ret", 0)
    owner = M.d(p + 4)
    if not e.t("owner_nz", owner != 0):
        return REF
    cls = s32(M.d(p + 0x10))
    if not e.c("cls_ge0", cls, ">=", 0) or not e.c("cls_lt_n", cls, "<", MIS_N):
        return REF
    ot = M.d(owner)
    if not (e.t("owner_t0", ot == 0) or e.t("owner_t1", ot == 1)):
        return REF
    row = MIS + cls * MIS_SZ
    flags = M.d(p)
    if e.t("f1", flags & 1):
        x, y = M.d(p + 0x14), M.d(p + 0x18)
    else:
        src = M.d(p + 8)
        if not e.t("src_nz", src != 0):
            return REF
        x, y = unit_xy(M, src)
    po = M.d(owner + 0x2C)
    room = room_at(e, M, M.d(po + 0x1C) if po else 0, s32(x), s32(y))
    if not e.t("room_nz", room != 0):
        return REF
    if e.t("f2", flags & 2):
        tx, ty = u32(M.d(p + 0x1C) + x), u32(M.d(p + 0x20) + y)
    elif e.t("f20", flags & 0x20):
        tx, ty = M.d(p + 0x1C), M.d(p + 0x20)
    else:
        tx, ty = x, y
    lvl = s32(M.d(p + 0x30))
    e.names.add("spec_lvl_m1")
    e.names.add("spec_floor8")
    e.names.add("spec_udiv8")
    e.names.add("spec_floor100_slow")
    e.names.add("spec_floor100_75")

    def div100(z, which):
        return z // 100 if e.flip == "spec_floor100_" + which else tdiv(z, 100)
    if e.t("f4", flags & 4):
        v = M.d(p + 0x28) if e.t("f10", flags & 0x10) else u32(M.d(p + 0x28) << 8)
    else:
        prod = s32(mrow(cls, 0x9B) * (s32(lvl - 1) if e.flip == "spec_lvl_m1" else lvl))
        q = (prod >> 3) if e.flip == "spec_floor8" else (u32(prod) >> 3) if e.flip == "spec_udiv8" else tdiv(prod, 8)
        v = u32(s32(q + mrow(cls, 0x9A)) << 8)
    if e.t("canslow", mrow(cls, 4) & img8(BITMASK + 12)) and e.t("st87", has_state(M, owner, 0x57)):
        sl = find_state_list(M, owner, 0x57)
        if e.t("sl_found", sl != 0):
            v = u32(div100(s32(base_stat(M, sl, 0xA1) * s32(v)), "slow"))
    if e.t("v_nz", v != 0):
        v = u32(div100(s32(s32(v) * 75), "75"))
    tg = M.d(p + 0xC)
    if e.t("v_nz2", v != 0):
        if not e.t("t_nz", tg != 0):
            if e.t("txy_eq", tx == x and ty == y):
                tx, ty = u32(tx + 1), u32(ty + 1)
        elif not e.t("t_owner", tg == owner):
            ox, tt = unit_xy(M, owner), unit_xy(M, tg)
            if e.t("same_x", tt[0] == ox[0]) and e.t("same_y", tt[1] == ox[1]):
                tg = 0
                tx, ty = u32(tx + 1), u32(ty + 1)
        ex, ey = unit_xy(M, tg) if tg else (tx, ty)
        e.names.add("spec_abs")

        def dist(a_, b_):
            d = s32(a_ - b_)
            if e.flip == "spec_abs":
                return abs(d)
            return s32(-d) if d < 0 else d
        if e.c("dx_ge100", dist(ex, x), ">=", 100) or e.c("dy_ge100", dist(ey, y), ">=", 100):
            return REF
    frame = struct.pack("<7I", tg, x, y, v, tx, ty, row)
    return ("obs", SUNIT, (3, u32(cls)), (x, y, a["game"], room, 1, mrow(cls, 0x183), 0), frame)


GEN = {"zz": gen_zz, "mcr": gen_mcr}
MODEL = {"zz": m_zz, "mcr": m_mcr}


class Sites(dict):
    def __missing__(self, key):
        return MCR_SITE


SITE = Sites()


# ----------------------------------------------------------------------------------------------- spec, check
def write_spec(d):
    with open(os.path.join(d, "missiles.bin"), "wb") as f:
        f.write(bytes(tables()))
    with open(os.path.join(d, "isc.bin"), "wb") as f:
        f.write(bytes(ISC_N * ISC_SZ))
    dt = bytearray(0x1000)
    for off, v in ((0xC4, NSTATES), (0xB64, MIS), (0xB6C, MIS_N), (0xBCC, ISC), (0xBD4, ISC_N)):
        struct.pack_into("<I", dt, off, v)
    with open(os.path.join(d, "dt.bin"), "wb") as f:
        f.write(bytes(dt))
    lines = ["# plan 0066 S2ae part 4 (tools/skills_s2ae4_emu.py): declared tables",
             "dword %08x %08x" % (G_DT, DT),
             "load %08x %s" % (DT, os.path.join(d, "dt.bin")),
             "load %08x %s" % (MIS, os.path.join(d, "missiles.bin")),
             "load %08x %s" % (ISC, os.path.join(d, "isc.bin"))]
    lines += ["guard %08x" % x for x in FATAL + ALLOC]
    lines += ["observe %08x" % SUNIT]
    with open(os.path.join(d, "s2ae.mem"), "w") as f:
        f.write("\n".join(lines) + "\n")


def observed(fam, k):
    if "stop" in k:
        return ("stop", k["stop"], k["msg"]), None
    dumps = k["dumps"]
    if "obs" in k:
        st = k["stack"]
        ret = struct.unpack_from("<I", st, 0)[0]
        regs = k["regs"]
        return ("obs", k["obs"], (int(regs["ecx"], 16), int(regs["edx"], 16)), struct.unpack_from("<7I", st, 4),
                dumps[FRAME]), ret
    if k["pop"] != POP[fam]:
        return ("pop", k["pop"]), None
    if fam == "zz":
        return ("ret", tuple(dumps[va] for va in sorted(dumps))), None
    return ("ret", k["eax"]), None


def norm(fam, want):
    return want


READS = ((BITMASK, BITMASK + 128, "g_BitMask32 0x006CE268 (.rdata)"),
         (PDT, PDT + 12 * PDT_N, "g_PathDirTable 0x006EB7E0 (.rdata)"),
         (PT_FLAGS, PT_FLAGS + 4 * 18, "PathSetType's flags 0x006EB690 (.rdata)"),
         (PT_W98, PT_W98 + 4 * 18, "PathSetType's +0x98 words 0x006EB648 (.rdata)"),
         (DIRY, DIRX + 32, "the 8-direction steps 0x006E328C, 0x006E32AC (.rdata)"),
         (DIR64, DIR64 + 64, "the 64-to-8 direction bytes 0x00745600 (.data; reference scan in `static`)"),
         (ZZ_PERIOD, ZZ_BASE + 4, "the zig-zag words 0x00741B0C, 0x00741B10 (.data; reference scan in `static`)"))


def account(reads, writes):
    bad = []
    for pc, addr, n, cnt in reads:
        if not any(lo <= addr and addr + n <= hi for lo, hi, _ in READS):
            bad.append(("R", pc, addr, n, cnt))
    for pc, addr, n, cnt in writes:
        bad.append(("W", pc, addr, n, cnt))
    return bad


def install():
    """Point part 1's check machinery at this part's families (its module state only; part 1's file is unchanged)."""
    B.FNS, B.FAMILIES, B.NCASES, B.POP, B.SITE = FNS, FAMILIES, NCASES, POP, SITE
    B.GEN, B.MODEL = GEN, MODEL
    B.observed, B.norm, B.account, B.write_spec = observed, norm, account, write_spec
    B.Case = Case

    def build(limit=None):
        cases = []
        for fam in FAMILIES:
            rnd = random.Random("n66sa-s2ae4-" + fam)
            for _ in range(NCASES[fam] if limit is None else min(limit, NCASES[fam])):
                cases.append(GEN[fam](rnd))
        return cases
    B.build = build


# ----------------------------------------------------------------------------------------------- static reads
STATIC = (
    ("zz", 0x005D4680, 0x005D486E),
    ("mrange", 0x0064A300, 0x0064A322),
    ("setrange", 0x0064A2B0, 0x0064A2F0),
    ("setrange2", 0x0064A330, 0x0064A370),
    ("seed", 0x00650E40, 0x00650E4A),
    ("pathsettype", 0x00648CF0, 0x00648DBE),
    ("pathbyte90", 0x00648E70, 0x00648E92),
    ("pathlist", 0x006487D0, 0x006487E8),
    ("pathcount", 0x00648790, 0x006487B4),
    ("pathsx", 0x006488C0, 0x006488F0),
    ("pathsy", 0x00648900, 0x00648930),
    ("pathtx", 0x00648A00, 0x00648A0E),
    ("pathty", 0x00648A10, 0x00648A1E),
    ("dirtopoint", 0x00621DC0, 0x00621E33),
    ("dir4", 0x0064FDC0, 0x0064FE0F),
    ("dir64", 0x0063E7A0, 0x0063E7B0),
    ("mcr", 0x0059FA30, 0x0059FC7A),
    ("mcr-refuse", 0x0059FD18, 0x0059FD21),
    ("missrec", 0x0046ACE0, 0x0046AD04),
    ("subx", 0x0045ADF0, 0x0045AE19),
    ("suby", 0x0045AE20, 0x0045AE49),
    ("unitroom", 0x00620BB0, 0x00620C01),
    ("pathroom", 0x00648A80, 0x00648A8B),
    ("roomat", 0x00463740, 0x004637E8),
    ("roomnb", 0x00619790, 0x006197CC),
    ("hasstate", 0x00639DF0, 0x00639E2E),
    ("hasstate2", 0x00625B70, 0x00625BAA),
    ("findbystate", 0x006256B0, 0x006256D8),
    ("findbystate2", 0x00625650, 0x006256AA),
    ("basestat", 0x00625D00, 0x00625D06),
    ("basestat2", 0x00625350, 0x006253A3),
    ("basestat3", 0x00624ED0, 0x00624F36),
    ("bsearch", 0x00624B90, 0x00624BC5),
)


def table_refs(A, lo, hi):
    """Part 3's operand scan (P3.table_refs) plus the `ds:0x...` absolute form it does not split."""
    hits = []
    for va in sorted(A.ins):
        mn, ops = A.ins[va]
        for tok in ops.replace(",", " ").replace("[", " ").replace("]", " ").replace("+", " ").replace(
                "*", " ").replace("ds:", " ").split():
            if tok.startswith("0x"):
                try:
                    v = int(tok, 16)
                except ValueError:
                    continue
                if lo <= v < hi:
                    hits.append("%08x %s %s" % (va, mn, ops))
    return hits


def cmd_static():
    if p1.img() is None:
        return 1
    for label, lo, hi in STATIC:
        for ln in P3.objdump(lo, hi):
            print("%s %s" % (label, ln))
    import sweep_s4b as W
    A = W.asm()
    print("ZZ period=%d base=%d" % (imgs32(ZZ_PERIOD), imgs32(ZZ_BASE)))
    print("DIR64 " + " ".join("%d" % img8(DIR64 + i) for i in range(64)))
    print("DIRX " + " ".join("%d" % imgs32(DIRX + 4 * i) for i in range(8)))
    print("DIRY " + " ".join("%d" % imgs32(DIRY + 4 * i) for i in range(8)))
    print("PATHTYPE10 flags=%08x w98=%08x" % (img32(PT_FLAGS + 40), img32(PT_W98 + 40)))
    print("CANSLOW-BIT %02x" % img8(BITMASK + 12))
    for name, lo, hi in (("DIR64", DIR64, DIR64 + 0x100), ("ZZW", ZZ_PERIOD, ZZ_BASE + 4),
                         ("P3-DOF", P3.G_DOF, P3.G_DOF + 4 * P3.N_DOF), ("P3-UMF", P3.G_UMF, P3.G_UMF + 24 * P3.N_UMOD)):
        print("SECTION %s %08x %s" % (name, lo, W.section_of(lo)))
        h = table_refs(A, lo, hi)
        for x in h:
            print("%s-REF %s" % (name, x))
        print("%s-REF count=%d" % (name, len(h)))
    return 0


SITE_ROOTS = (   # (label, entry, rows)
    ("SKILLS_TargetCheck", 0x0056CC60, "d47"),
    ("ItemTargetRandomPoint", 0x005FD850, "d83"),
    ("ItemTargetCorpse", 0x005FD9C0, "d84"),
    ("SorSkillStaticMin", 0x005C9800, "d164"),
    ("MISSILE_BuildDamage", 0x005A89A0, "m63"),
    ("MissCbReseedZigzag", 0x005D4680, "m76"),
    ("SkillDo30Curse", 0x005C37C0, "m69"),
    ("MissileCreate", 0x0059FA30, "m14, m16-19"),
)


def cmd_sites():
    P3.SITE_ROOTS = SITE_ROOTS
    return P3.cmd_sites()


# ----------------------------------------------------------------------------------------------- reach
def cmd_reach(limit=None):
    cases = B.build(limit)
    outs, reach = {}, {}
    for c in cases:
        e = P3.RE()
        try:
            w = MODEL[c.fam](e, c.a)
        except (KeyError, IndexError) as x:
            w = ("model-error", str(x))
        k = "%s%s" % (w[0], (":%x" % w[1]) if w[0] in ("obs", "stop") else "")
        outs.setdefault(c.fam, {}).setdefault(k, 0)
        outs[c.fam][k] += 1
        for name, r in e.seen:
            d = reach.setdefault(c.fam, {}).setdefault(name, [0, 0])
            d[0 if r else 1] += 1
    for f in FAMILIES:
        print("OUTCOMES %s %s" % (f, " ".join("%s=%d" % kv for kv in sorted(outs.get(f, {}).items()))))
        for name, (tt, ff) in sorted(reach.get(f, {}).items()):
            print("REACH %s %s true=%d false=%d" % (f, name, tt, ff))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("cases", "check", "reach", "static", "sites", "manifest"))
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    o = ap.parse_args(argv)
    install()
    if o.cmd == "cases":
        B.cmd_cases(o.dir, o.limit)
        return 0
    if o.cmd == "check":
        return B.cmd_check(o.dir, o.limit)
    if o.cmd == "reach":
        return cmd_reach(o.limit)
    if o.cmd == "static":
        return cmd_static()
    if o.cmd == "sites":
        return cmd_sites()
    B.cmd_manifest(o.dir, o.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S1e (`lane/n66e`): the monsters/ai catalogue's search callbacks and helpers run whole under
Ghidra's p-code emulator (ADR-0015, ADR-0021, ADR-0029) with re/ghidra_scripts/EmuBoundary.java, compared with the
models below. No game, no slot. Unlike the plan 0052 catalogue batches, no callee is an observed boundary: every
callee these functions reach runs emulated on the declared image (ruling R2 of the plan 0066 inventory: no declared
callee return), so each case's claim is the function's whole map, from the declared image to its return value, the
bytes it writes and the seed states.

    python3 -I tools/ai_s1e_emu.py cases [--dir D]     write D/s1e.cases, D/s1e.mem and the zeroed table images
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s1e.cases D/s1e.mem > D/s1e.out
    python3 -I tools/ai_s1e_emu.py check [--dir D]     compare D/s1e.out with the models, account for every traced
                                                        read and write, run the per-test controls
    python3 -I tools/ai_s1e_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/ai/sweep2-s1e. Every case draw comes from random.Random("n66e-<family>"), so `cases`
regenerates identical files.

The declared image (memory spec, re-applied before every case, then the case's own `w` lines):
  the DataTables pointer 0x00744304 -> DT; the skill-level cap pointer 0x0096C8A8 -> a word array in the arena;
  DT +0x0C4 state count, +0x150 the state-set-33 mask array, +0xA78/+0xA80 MonStats base and count (records 0x1A8),
  +0xA90/+0xA98 MonStats2 (0x134), +0xB98/+0xBA0 Skills (0x23C), +0xBCC/+0xBD4 ItemStatCost (0x144);
  the tables zero but for each MonStats record's +0x02 (its own index, so MonBaseId is the class unless a case
  writes it); the game (+0x6D difficulty, +0xA8 frame, +0xF0 the region array by level, the unit hash slots at
  +0x1120.. as g_UnitHashOffsets 0x006E10E0 gives, +0x1B20 for type 5); a zeroed arena for units (+0x00 type,
  +0x04 class, +0x0C guid, +0x10 mode, +0x14 monster or player data, +0x20/+0x24 seed, +0x2C path, +0x5C stat list,
  +0x94/+0x98 owner type and guid, +0xC4 flags (byte +0xC6 bit 0 the dead flag UnitIsDead reads), +0xC8 bit 10,
  +0xE4 hash next, +0xE8 room-list next), monster data (+0x00 MonStats pointer, +0x16 type flags, +0x28 AI
  control, +0x54 state, +0x58 level), AI controls (+0x14, +0x18, +0x1C, owner words +0x28/+0x2C/+0x30), paths
  (+0x00 room for static units, +0x02/+0x06 u16 x/y, +0x0C/+0x10 static x/y, +0x1C room), stat lists (+0x10 bit 31,
  the arrays at +0x24 and +0x48 (pointer, i16 count) of {u32 stat<<16|param, i32 value} sorted, the node chains
  +0x3C/+0x40 linked by +0x2C with the id at +0x14, +0x44 the owner, +0x58 the state bits), player data (+0x38 the
  relation list {+0 guid, +4 flags, +0x10 next}), rooms (+0x00 near list, +0x24 its count, +0x10 -> +0x58 ->
  +0x1D0 level id, +0x74 unit list), regions (+0x10 entry count, +0x14 + 0x34 i the entry's class, +0x2D4 the
  trap-arrow kind word), the weight block, seeds, the search block.
Image constants read (no code writes them; .rdata or .text): g_BitMask32 0x006CE268 (32 words), g_UnitHashOffsets
0x006E10E0 (5 words), g_AiSearchKinds 0x006E3300 (kind 1 at +8), the ShadowMaster callback's jump table and byte
table 0x005EB7D8..0x005EB7E7, AiShadowSkillFits's jump table and byte table 0x005EAD34..0x005EAD47. Guards: the
fatal path (0x00408090, 0x00408A60, 0x00681E09). No observe line: every callee runs.

Families (function, inventory row of monsters-ai-catalogue.md):
  nearally 0x005F06B0 AiNearAllyCb (31)        samebase 0x005B0D00 AiSameBaseNearCb (66)
  wounded  0x005F30F0 AiWoundedNearCb (72)     zakheal  0x005F7240 AiZakarumHealCb (135)
  fetrev   0x005F99A0 AiFetishReviveCb (154)   regurg   0x005FA690 AiRegurgitatorCb (172)
  oblkn    0x005FAE40 AiOblivionKnightCb (182) trkind   0x005FB650 AiTrapArrowKind (194, 196)
  randlohi 0x004BC500 RNG_RandLoHi (196)       shroll   0x005EAD50 AiShadowSkillRoll (229)
  shmcb    0x005EB6D0 AiShadowMasterCb (242)   mephcb   0x005F7700 Mephisto's pick callback (288)
  mephpick 0x005F77C0 Mephisto's pick, with AiUnitSearch kind 1 and its walker run whole (288)
  priest   0x005E0430 AiPriestHealCb (314)     imp      0x005E1720 AiImpNearCb (332)
  overseer 0x005E26D0 AiOverseerMinionCb (356) mincount 0x005E2B70 AiMinionCountCb (360)
  genspawn 0x005E6020 AiGenSpawnPickClass (385) wpick   0x005FC130 the weighted pick (420)
  alife    0x005DD280 AiLifePct (3, 518)       ulife    0x00621F20 UnitLifePct (3, 518), on alife's images
  st319    0x005DD2B0 AiMonState3or19 (3)      owner    0x0058F0D0 MonsterOwner (3)
  entry    0x005B15D0 MonAiEntryGet (15)

Controls. Every named test of a model (the callback's own tests and the callee tests its claim names) is reversed
alone, and every ordered compare has its strictness switched alone (`<` and `<=`, `>` and `>=`; name + "~"). For each
control the check counts the cases whose predicted outputs it changes (`sep`) and how many of those the emulator
output still matches (`passed`, must be 0). A control with sep 0 is listed as unseparated: no case of the run tells
that test or that strictness from its reversal, and the claim on it stays `[I]`. The site control of ADR-0021 does not
apply (no case ends at a boundary). Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "ai", "sweep2-s1e")

MUL = 0x6AC690C5
G_DT, G_MAXLVL = 0x00744304, 0x0096C8A8
GAME, GAME_LEN = 0x12000000, 0x2000
DT, DT_LEN = 0x12A00000, 0x1000
MS, MS_N, MS_SZ = 0x13000000, 0x300, 0x1A8
MS2, MS2_N, MS2_SZ = 0x13100000, 0x100, 0x134
ISC, ISC_N, ISC_SZ = 0x13200000, 0x180, 0x144
SK, SK_N, SK_SZ = 0x13300000, 0x180, 0x23C
ARENA, ARENA_LEN = 0x14000000, 0x20000
STACK_TOP = 0x7FF00000                      # ESP at entry (the return sentinel), EmuBoundary.java
HASHOFF = (0x1120, 0x1320, 0x1520, 0x1920, 0x1720)      # 0x006E10E0 (objdump -s of .rdata)
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
CONST_READS = ((0x006CE268, 0x80, "g_BitMask32"), (0x006E10E0, 0x14, "g_UnitHashOffsets"),
               (0x006E3300, 0x68, "g_AiSearchKinds"), (0x005EB7D8, 0x10, "AiShadowMasterCb jump and byte tables"),
               (0x005EAD34, 0x14, "AiShadowSkillFits jump and byte tables"))
SHM_TABLE = (0, 0, 0, 0, 1, 0, 0)            # 0x005EB7E0: base 410+k, 1 = on to the hostile part (objdump -s)
FITS_TABLE = (0, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0)   # 0x005EAD3C: kind 2+k with no target, 1 = go on (objdump -s)

NCASES = 240
FNS = {"nearally": 0x005F06B0, "samebase": 0x005B0D00, "wounded": 0x005F30F0, "zakheal": 0x005F7240,
       "fetrev": 0x005F99A0, "regurg": 0x005FA690, "oblkn": 0x005FAE40, "trkind": 0x005FB650,
       "randlohi": 0x004BC500, "shroll": 0x005EAD50, "shmcb": 0x005EB6D0, "mephcb": 0x005F7700,
       "mephpick": 0x005F77C0, "priest": 0x005E0430, "imp": 0x005E1720, "overseer": 0x005E26D0,
       "mincount": 0x005E2B70, "genspawn": 0x005E6020, "wpick": 0x005FC130, "alife": 0x005DD280,
       "ulife": 0x00621F20, "st319": 0x005DD2B0, "owner": 0x0058F0D0, "entry": 0x005B15D0}
FAMILIES = tuple(FNS)


def u32(v):
    return v & 0xFFFFFFFF


def s32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


def s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def s8(v):
    v &= 0xFF
    return v - 0x100 if v & 0x80 else v


def tdiv(a, b):                             # idiv: truncating
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


class Mem:
    """The declared image: the zeroed spec regions (with MonStats +0x02 = index) under the case's overlay."""

    REGIONS = ((GAME, GAME_LEN), (DT, DT_LEN), (MS, MS_N * MS_SZ), (MS2, MS2_N * MS2_SZ), (ISC, ISC_N * ISC_SZ),
               (SK, SK_N * SK_SZ), (ARENA, ARENA_LEN))

    def __init__(self):
        self.ov = {}
        self.top = ARENA

    def copy(self):
        m = Mem()
        m.ov = dict(self.ov)
        m.top = self.top
        return m

    def base(self, a):
        if MS <= a < MS + MS_N * MS_SZ:
            off, idx = (a - MS) % MS_SZ, (a - MS) // MS_SZ
            return idx & 0xFF if off == 2 else (idx >> 8) & 0xFF if off == 3 else 0
        for lo, n in self.REGIONS:
            if lo <= a < lo + n:
                return 0
        if G_DT <= a < G_DT + 4:
            return (DT >> (8 * (a - G_DT))) & 0xFF
        raise KeyError("model read outside the declared image: %08x" % a)

    def r8(self, a):
        a = u32(a)
        return self.ov[a] if a in self.ov else self.base(a)

    def r16(self, a):
        return self.r8(a) | self.r8(a + 1) << 8

    def r32(self, a):
        return self.r16(a) | self.r16(a + 2) << 16

    def w8(self, a, v):
        self.ov[u32(a)] = v & 0xFF

    def w16(self, a, v):
        self.w8(a, v)
        self.w8(a + 1, v >> 8)

    def w32(self, a, v):
        self.w16(a, v)
        self.w16(a + 2, v >> 16)

    def alloc(self, n):
        a = self.top
        self.top = (self.top + n + 15) & ~15
        if self.top > ARENA + ARENA_LEN:
            raise ValueError("arena full")
        return a

    def runs(self):
        out, cur, start = [], [], None
        for a in sorted(self.ov):
            if cur and a == start + len(cur):
                cur.append(self.ov[a])
            else:
                if cur:
                    out.append((start, bytes(cur)))
                start, cur = a, [self.ov[a]]
        if cur:
            out.append((start, bytes(cur)))
        return out


def step(m, sp):                            # one LCG step of the seed at sp
    t = m.r32(sp) * MUL + m.r32(sp + 4)
    m.w32(sp, t)
    m.w32(sp + 4, t >> 32)
    return t & 0xFFFFFFFF


def rng_range(m, sp, n):                    # 0x0045C390: n <= 0 gives 0 with no step
    n = s32(n)
    if n <= 0:
        return 0
    low = step(m, sp)
    return low & (n - 1) if n & (n - 1) == 0 else low % n


class E:
    """One model run: the memory copy, the named tests and the reversal or strictness control."""

    def __init__(self, m, flip=None):
        self.m = m
        self.flip = flip
        self.names = set()
        self.tags = set()

    def tag(self, name):
        self.tags.add(name)

    def t(self, name, cond):
        self.names.add(name)
        return (not cond) if self.flip == name else bool(cond)

    def c(self, name, a, op, b):            # an ordered signed compare; name~ switches its strictness
        self.names.add(name)
        self.names.add(name + "~")
        if self.flip == name + "~":
            op = {"<": "<=", "<=": "<", ">": ">=", ">=": ">"}[op]
        r = {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]
        return (not r) if self.flip == name else r


# ---- the callees' maps, on the declared image ----

def ms_count(m):
    return s32(m.r32(DT + 0xA80))


def ms_rec(m, c):                           # 0x00451F80
    c = s32(c)
    return MS + c * MS_SZ if 0 <= c < ms_count(m) else 0


def utype(m, u):
    return m.r32(u)


def baseid(m, u):                           # 0x00463860 MonBaseId
    if u == 0 or utype(m, u) != 1:
        return -1
    c = s32(m.r32(u + 4))
    if c < 0 or c >= ms_count(m):
        return c
    return s16(m.r16(MS + c * MS_SZ + 2))


def classcheck(m, c):                       # 0x00463900 MonClassCheck
    return c if 0 <= c < ms_count(m) else -1


def isdeath(m, u):                          # 0x0063EA40 MonIsDeathMode
    return u != 0 and utype(m, u) == 1 and m.r32(u + 0x10) in (0, 12)


def isdead(m, u):                           # 0x005541B0 UnitIsDead
    if u == 0 or m.r8(u + 0xC6) & 1:
        return True
    t, md = utype(m, u), m.r32(u + 0x10)
    if t == 0:
        return md in (0, 17)
    if t == 1:
        return md in (0, 12)
    return True


def pos(m, u):                              # the position words UnitDistSq reads
    t = s32(utype(m, u))
    p = m.r32(u + 0x2C)
    if t == 2 or 4 <= t <= 5:
        return m.r32(p + 0x0C), m.r32(p + 0x10)
    if p == 0:
        return 0, 0
    return m.r16(p + 2), m.r16(p + 6)


def distsq(m, a, b):                        # 0x005B0BD0 UnitDistSq
    (xa, ya), (xb, yb) = pos(m, a), pos(m, b)
    dx, dy = u32(xa - xb), u32(ya - yb)
    return s32(dy * dy + dx * dx)


def lookup(m, lst, key, rec):               # 0x00624F60 with 0x00624B90
    flag = m.r32(lst + 0x10) & 0x80000000
    arr = lst + 0x48 if flag else lst + 0x24
    ptr, n = m.r32(arr), s16(m.r16(arr + 4))
    lo, hi, found = 0, n, -1
    key = s32(key)
    while lo < hi:
        mid = lo + tdiv(hi - lo, 2)
        k = s32(m.r32(ptr + 8 * mid))
        if key > k:
            lo = mid + 1
        elif key < k:
            hi = mid
        else:
            found = mid
            break
    if found < 0:
        return 0
    v = s32(m.r32(ptr + 8 * found + 4))
    if rec and (m.r8(rec + 5) & 0x04) and flag:
        own = m.r32(lst + 0x44)
        if own and m.r32(own) in (0, 1):
            lim = s32(m.r32(rec + 0x2C))
            if v < lim:
                v = s32(lim << (m.r8(rec + 0x18) & 31))
    return v


def isc_n(m):
    return s32(m.r32(DT + 0xBD4))


def getstat(m, u, stat):                    # 0x00625480 (u, stat, 0)
    if u == 0:
        return 0
    lst = m.r32(u + 0x5C)
    if lst == 0 or not 0 <= stat < isc_n(m):
        return 0
    return lookup(m, lst, stat << 16, ISC + stat * ISC_SZ)


def maxhp(m, u):                            # 0x00625D10
    if u == 0:
        return 0
    lst = m.r32(u + 0x5C)
    if lst == 0 or isc_n(m) <= 7:
        return 0
    return lookup(m, lst, 0x70000, ISC + 7 * ISC_SZ)


def lifepct(m, u):                          # 0x00621F20 UnitLifePct
    hp = getstat(m, u, 6) >> 8
    mx = maxhp(m, u) >> 8
    if mx == 0:
        return 0
    return tdiv(s32(hp * 100), mx)


def findnode(m, lst, ident):                # 0x00625650
    for head in (0x3C, 0x40):
        n = m.r32(lst + head)
        while n:
            if m.r32(n + 0x14) == ident:
                return n
            n = m.r32(n + 0x2C)
    return 0


def align(m, u):                            # 0x006259B0 UnitAlignGet
    if u == 0 or m.r32(u + 0x5C) == 0:
        return 0
    if utype(m, u) > 1:
        return 2
    lst = m.r32(u + 0x5C)
    if not m.r32(lst + 0x10) & 0x80000000:
        return 0
    node = findnode(m, lst, 0x69)
    if node == 0 or not 0 <= 0xAC < isc_n(m):
        return 0
    return lookup(m, node, 0xAC << 16, ISC + 0xAC * ISC_SZ)


def alignsame(m, a, b):                     # 0x00650D70 AlignSame02(a, b)
    if a == 0 or b == 0:
        return False
    if a == b:
        return True
    A, B = s32(align(m, a)), s32(align(m, b))
    if A == 0:
        return B == 0
    if A == 2:
        return B == 2
    return False


def findunit(m, g, t, guid):                # 0x00552F60 GameFindUnit
    if g == 0:
        raise ValueError("fatal path")
    if t == 5:
        slot = g + 0x1B20
    elif t <= 4:
        slot = g + HASHOFF[t] + 4 * (guid & 0x7F)
    else:
        raise ValueError("a read at 0")
    n = m.r32(slot)
    while n:
        if m.r32(n + 0x0C) == guid:
            return n
        n = m.r32(n + 0xE4)
    return 0


def mowner(m, u):                           # 0x0058F0D0 MonsterOwner
    if u == 0 or utype(m, u) != 1:
        return 0
    md = m.r32(u + 0x14)
    ctl = m.r32(md + 0x28) if md else 0
    g = m.r32(ctl + 0x28) if ctl else 0
    if g == 0:
        return 0
    return findunit(m, g, m.r32(ctl + 0x30), m.r32(ctl + 0x2C))


def uowner(m, g, u):                        # 0x00552FD0 UnitGetOwner
    if u == 0 or not (m.r32(u + 0xC8) >> 10) & 1:
        return 0
    return findunit(m, g, m.r32(u + 0x94), m.r32(u + 0x98))


def hostile(m, g, a, b):                    # 0x00554200 UnitsHostile(G, a, b)
    if a:
        o = 0
        if utype(m, a) == 1:
            o = mowner(m, a)
        elif utype(m, a) == 3 and (m.r32(a + 0xC8) >> 10) & 1:
            o = findunit(m, g, m.r32(a + 0x94), m.r32(a + 0x98))
        if o:
            a = o
    while b and utype(m, b) == 1:
        o = mowner(m, b)
        if o == 0 or o == b:
            break
        b = o
    if a == b:
        return 0
    if a and utype(m, a) == 0 and b and utype(m, b) == 0:
        pd, g2 = m.r32(a + 0x14), m.r32(b + 0x0C)
        n = m.r32(pd + 0x38)
        while n:
            if m.r32(n) == g2:
                return m.r32(n + 4) & 8
            n = m.r32(n + 0x10)
        return 0
    return 0 if alignsame(m, a, b) else 1


def hasstate(m, u, s):                      # 0x00639DF0 UNIT_HasState
    if u == 0:
        return False
    t = s32(utype(m, u))
    if t < 0 or (t > 1 and t != 3) or not 0 <= s < s32(m.r32(DT + 0xC4)):
        return False
    lst = m.r32(u + 0x5C)
    if lst == 0 or not m.r32(lst + 0x10) & 0x80000000:
        return False
    bits = m.r32(lst + 0x58)
    return bool(m.r32(bits + 4 * (s >> 5)) & (1 << (s & 31)))


def set33(m, u):                            # 0x0063A770 with 0x0063A130
    lst = m.r32(u + 0x5C) if u else 0
    bits = m.r32(lst + 0x58) if lst and m.r32(lst + 0x10) & 0x80000000 else 0
    if bits == 0:
        return False
    n = tdiv(s32(m.r32(DT + 0xC4)) + 31, 32)
    mask = m.r32(DT + 0x150)
    return any(m.r32(mask + 4 * i) & m.r32(bits + 4 * i) for i in range(max(0, n)))


def typeflag(m, u, mask):                   # 0x005A0180 MonTypeFlag (the mask itself, `and ax, dx`)
    if u == 0 or utype(m, u) != 1:
        return False
    md = m.r32(u + 0x14)
    return bool(md and m.r16(md + 0x16) & mask)


def ms2flag(m, cls, bit):                   # 0x004638A0 MonStats2FlagTest
    if not 0 <= s32(cls) < ms_count(m):
        return False
    i = s16(m.r16(MS + s32(cls) * MS_SZ + 0x18))
    if not 0 <= i < s32(m.r32(DT + 0xA98)):
        return False
    return bool(m.r8(MS2 + i * MS2_SZ + 4 + (bit >> 3)) & (1 << (bit & 7)))


def ctlget(m, u):                           # 0x00541860
    if u == 0 or utype(m, u) != 1:
        return 0
    md = m.r32(u + 0x14)
    return m.r32(md + 0x28) if md else 0


def prio(m, U, c):                          # 0x005EB650 AiShadowPriorityTarget
    if c == 0 or c == U or utype(m, c) != 1 or isdead(m, c):
        return False
    rec = ms_rec(m, m.r32(c + 4))
    if rec == 0:
        return False
    b = m.r8(rec + 0x0D)
    if b & 0x01 or not b & 0x80:
        return False
    if m.r8(rec + 0x0C) & 0x40 or m.r8(rec + 0x0C) & 0x80:
        return True
    return typeflag(m, c, 0x0E)


# ---- the models of the claims ----

def m_nearally(e, a):                       # R8b: AiNearAllyCb(G, U; cand, blk)
    m, U, c, b = e.m, a["U"], a["cand"], a["blk"]
    if e.t("cand!=U", c != U) and e.t("cand", c != 0) and e.t("type1", utype(m, c) == 1) \
            and e.t("align0", align(m, c) == 0) and e.t("!death", not isdeath(m, c)):
        d = distsq(m, U, c)
        (x0, y0), (x1, y1) = pos(m, U), pos(m, c)
        if (x0 - x1) ** 2 + (y0 - y1) ** 2 >= 1 << 31:
            e.tag("distsq wraps")
        if e.c("d<best", d, "<", s32(m.r32(b + 4))):
            m.w32(b, c)
            m.w32(b + 4, d)
            e.tag("taken")
    return 0


def m_samebase(e, a):                       # R18a: AiSameBaseNearCb
    m, U, c, b = e.m, a["U"], a["cand"], a["blk"]
    if e.t("cand", c != 0) and e.t("type1", utype(m, c) == 1) and e.t("cand!=U", c != U) \
            and e.t("base=", baseid(m, U) == baseid(m, c)) and e.t("!death", not isdeath(m, c)):
        d = distsq(m, U, c)
        if e.c("d<best", d, "<", s32(m.r32(b + 4))):
            m.w32(b, c)
            m.w32(b + 4, d)
            e.tag("taken")
    return 0


def m_wounded(e, a):                        # R23b: AiWoundedNearCb
    m, U, c, b = e.m, a["U"], a["cand"], a["blk"]
    if e.t("cand", c != 0) and e.t("type0or1", utype(m, c) in (0, 1)) and e.t("cand!=U", c != U) \
            and e.t("!death", not isdeath(m, c)):
        d = distsq(m, U, c)
        if e.c("d<=best", d, "<=", s32(m.r32(b + 4))):
            lim = s32(tdiv(maxhp(m, c), 100) * s32(m.r32(b + 8)))
            if e.c("hp<=lim", getstat(m, c, 6), "<=", lim):
                m.w32(b, c)
                m.w32(b + 4, d)
                e.tag("taken, type %d" % utype(m, c))
                if utype(m, c) == 0 and m.r32(c + 0x10) in (0, 17):
                    e.tag("taken, a player in mode 0 or 17")
    return 0


def m_zakheal(e, a):                        # R49b: AiZakarumHealCb
    m, U, c, b = e.m, a["U"], a["cand"], a["blk"]
    if e.t("cand!=U", c != U) and e.t("cand", c != 0) and e.t("type1", utype(m, c) == 1) \
            and e.t("alignsame", alignsame(m, U, c)) and e.t("align!=2", align(m, c) != 2) \
            and e.t("!death", not isdeath(m, c)) \
            and e.t("class235|238", classcheck(m, baseid(m, c)) in (235, 238)) \
            and e.c("d<=bound", distsq(m, U, c), "<=", s32(m.r32(b + 0xC))):
        life = lifepct(m, c)
        if e.c("life<=60", life, "<=", 60):
            if e.c("best<=0", s32(m.r32(b + 8)), "<=", 0):
                m.w32(b + 8, 0x7FFFFFFF)
                e.tag("best rewritten")
            else:
                e.tag("best kept %s" % ("> 60" if s32(m.r32(b + 8)) > 60 else "<= 60"))
            m.w32(b + 4, m.r32(b + 4) + 1)
            if e.c("life<best", life, "<", s32(m.r32(b + 8))):
                m.w32(b, c)
                e.tag("taken")
            else:
                e.tag("counted, not taken")
    return 0


def m_fetrev(e, a):                         # R65c: AiFetishReviveCb
    m, U, c, b = e.m, a["U"], a["cand"], a["blk"]
    filt = s32(m.r32(b + 0x18))
    if not (e.t("cand!=U", c != U) and e.t("cand", c != 0) and e.t("type1", utype(m, c) == 1)
            and e.t("c4&2", m.r32(c + 0xC4) & 2) and e.t("!set33", not set33(m, c))):
        return 0
    if e.t("filter0", filt == 0) and not e.t("owner=U", mowner(m, c) == U):
        return 0
    cls = classcheck(m, baseid(m, c))
    if not e.t("class141", cls == 141):
        if not (e.t("class396", cls == 396) and e.t("filter!=1", filt != 1)):
            return 0
    if not e.t("align0", align(m, c) == 0):
        return 0
    if e.c("filter<3", filt, "<", 3) and e.t("typeflag12", typeflag(m, c, 0x0C)):
        return 0
    d = distsq(m, U, c)
    if not e.c("d<=r2", d, "<=", s32(m.r32(b + 8))):
        return 0
    if e.t("mode12", m.r32(c + 0x10) == 12):
        if e.c("d<dead", d, "<", s32(m.r32(b + 4))):
            m.w32(b, c)
            m.w32(b + 4, d)
            e.tag("dead taken")
    else:
        e.tag("live counted")
        m.w32(b + 0x14, m.r32(b + 0x14) + 1)
        if e.c("d<live", d, "<", s32(m.r32(b + 0x10))):
            m.w32(b + 0x0C, c)
            m.w32(b + 0x10, d)
    return 0


def m_regurg(e, a):                         # R71b: AiRegurgitatorCb
    m, U, c, b = e.m, a["U"], a["cand"], a["blk"]
    if e.t("cand!=U", c != U) and e.t("cand", c != 0) and e.t("type1", utype(m, c) == 1) \
            and e.t("!c4&200", not m.r32(c + 0xC4) & 0x200) and e.t("c4&2", m.r32(c + 0xC4) & 2) \
            and e.t("death", isdeath(m, c)) and e.t("!set33", not set33(m, c)) \
            and e.t("align0", align(m, c) == 0) and e.t("ms2flag12", ms2flag(m, m.r32(c + 4), 12)):
        d = distsq(m, U, c)
        if e.c("d<=best", d, "<=", s32(m.r32(b + 4))):
            e.tag("taken at an equal distance" if d == s32(m.r32(b + 4)) else "taken")
            m.w32(b, c)
            m.w32(b + 4, d)
    return 0


def m_oblkn(e, a):                          # R74b: AiOblivionKnightCb
    m, U, c, b = e.m, a["U"], a["cand"], a["blk"]
    if not (e.t("cand!=U", c != U) and e.t("cand", c != 0) and e.t("type1", utype(m, c) == 1)
            and e.t("!death", not isdeath(m, c)) and e.t("c4&2", m.r32(c + 0xC4) & 2)):
        return 0
    bi = baseid(m, c)
    if not (e.t("base>=0", bi >= 0) and e.t("base<count", bi < ms_count(m)) and e.t("base310", bi == 0x136)):
        return 0
    d = distsq(m, U, c)
    if not (e.c("d<=bound", d, "<=", s32(m.r32(b + 8))) and e.t("alignsame", alignsame(m, U, c))
            and e.t("align0", align(m, c) == 0)):
        return 0
    if e.c("d<knight", d, "<", s32(m.r32(b + 0x0C))):
        m.w32(b, c)
        m.w32(b + 0x0C, d)
    if e.c("d<weak", d, "<", s32(m.r32(b + 0x10))) and e.c("life<40", lifepct(m, c), "<", 40):
        m.w32(b + 4, c)
        m.w32(b + 0x10, d)
        e.tag("weak taken")
    return 0


def randlohi(e, sp, lo, hi):                # 0x004BC500 RNG_RandLoHi(seed, lo, hi)
    m = e.m
    if e.c("hi<=lo", s32(hi), "<=", s32(lo)):
        e.tag("hi <= lo: lo, no step")
        return u32(lo)
    e.tag("span >= 2^31" if u32(hi - lo) >= 1 << 31 else "power of two" if u32(hi - lo) & u32(hi - lo - 1) == 0
          else "other span")
    span = u32(hi - lo)
    low = step(m, sp)
    r = low & (span - 1) if e.t("pow2", span & (span - 1) == 0) else low % span
    return u32(r + lo)


def m_randlohi(e, a):
    return randlohi(e, a["seed"], a["lo"], a["hi"])


def unit_room(m, u):                        # 0x00620BB0 UnitGetRoom (U non-null)
    t = s32(utype(m, u))
    p = m.r32(u + 0x2C)
    if t == 2 or 4 <= t <= 5:
        return m.r32(p)
    return m.r32(p + 0x1C) if p else 0


def m_trkind(e, a):                         # the R78 block: AiTrapArrowKind(G, U)
    m, G, U = e.m, a["G"], a["U"]
    room = unit_room(m, U)
    lvl = s32(m.r32(m.r32(m.r32(room + 0x10) + 0x58) + 0x1D0)) if room else 0
    r = m.r32(G + 0xF0 + 4 * lvl)
    if e.c("word<0", s32(m.r32(r + 0x2D4)), "<", 0):
        if e.c("lvl<40", lvl, "<", 40):
            m.w32(r + 0x2D4, 0)
            e.tag("set 0 below 40")
        else:
            m.w32(r + 0x2D4, randlohi(e, U + 0x20, 0, 3))
            e.tag("drawn")
    else:
        e.tag("kept")
    return m.r32(r + 0x2D4)


def fits(e, a):                             # AiShadowSkillFits on the declared paths (callee, not claimed)
    m, U, i, ctx = e.m, a["U"], a["id"], a["ctx"]
    if not 0 <= s32(i) < s32(m.r32(DT + 0xBA0)):
        return False
    rec = SK + s32(i) * SK_SZ
    assert m.r16(rec + 0xBC) == 0           # 0x005EAB20 returns 1 at once
    melee, tgt = m.r32(ctx + 0x18), m.r32(ctx + 8)
    k = m.r8(rec + 0x230)
    if (k in (4, 13)) != (melee != 0):
        return False
    w80, w82 = s16(m.r16(rec + 0x80)), s16(m.r16(rec + 0x82))
    if k == 1 and w80 > 0 and hasstate(m, U, w80):
        return False
    if tgt == 0 and 0 <= k - 2 <= 11 and not FITS_TABLE[k - 2]:
        return False
    if k == 2 and ((w80 > 0 and hasstate(m, U, w80)) or (w82 > 0 and hasstate(m, tgt, w82))):
        return False
    if m.r8(rec + 4) & 0x04 and w80 > 0 and hasstate(m, U, w80):
        raise AssertionError("an undeclared path (0x006256B0, 0x00625D00)")
    return True


def m_shroll(e, a):                         # the R105 block: AiShadowSkillRoll(owner, skill, id, -, ctx)
    m, G, U, O, sk, i, ctx = e.m, a["G"], a["U"], a["owner"], a["skill"], a["id"], a["ctx"]
    if sk == 0 or O == 0 or ctx == 0 or m.r32(ctx) == 0:
        return 0
    ctl = m.r32(ctx)
    ok = 0 <= s32(i) < s32(m.r32(DT + 0xBA0))
    cls = s8(m.r8(SK + s32(i) * SK_SZ + 0xC)) if ok else 7
    if cls < 0:
        cls = 7
    if not e.t("class=owner", cls == s32(m.r32(O + 4))) or not e.t("fits", fits(e, a)):
        return 0
    lvl = s32(m.r32(sk + 0x28))
    lvl = lvl if lvl > 0 else 0
    cap = s32(m.r32(m.r32(G_MAXLVL)))
    lvl = lvl if lvl < cap else cap
    if e.t("id0", i == 0):
        e.tag("id 0: 1, no draw")
        return 1
    rec = SK + s32(i) * SK_SZ
    q = s32(s16(m.r16(rec + 0x18C)) * (lvl - 1) + s16(m.r16(rec + 0x18A)))
    q = s32(q << (m.r8(rec + 0x188) & 31)) >> 8
    q = q if q >= 0 else 0
    d = rng_range(m, U + 0x20, 100)
    if e.c("draw>100-160q/100", d, ">", 100 - tdiv(s32(q * 160), 100)):
        return 0
    if e.c("v14>T", s32(m.r32(ctl + 0x14)), ">", s32(m.r32(G + 0xA8))):
        return 0
    ms = m.r32(ctx + 0x1C)
    lo, hi = s16(m.r16(ms + 0x82)), s16(m.r16(ms + 0x84))
    lo = 1 if lo <= 1 else 0x80 if lo >= 0x80 else lo
    hi = 1 if hi <= 1 else 0x100 if hi >= 0x100 else hi
    v = s32(m.r32(ctl + 0x18))
    if e.c("v18<lo", v, "<", lo) or e.c("v18>32hi", v, ">", s32(hi << 5)):
        m.w32(ctl + 0x18, lo)
        e.tag("v18 reset to lo")
    x = rng_range(m, U + 0x20, m.r32(ctl + 0x18))
    y = rng_range(m, U + 0x20, 100)
    if e.c("b<a", y, "<", x):
        e.tag("refused at the third draw")
        return 0
    v1c = s32(m.r32(ctl + 0x1C))
    m.w32(ctl + 0x18, s32(m.r32(ctl + 0x18)) + tdiv(s32((320 - v1c) * q), v1c + 100))
    e.tag("accepted, three draws")
    return 1


def m_shmcb(e, a):                          # R106b: AiShadowMasterCb(G, U; cand, blk)
    m, G, U, c, b = e.m, a["G"], a["U"], a["cand"], a["blk"]
    if not (e.t("cand!=U", c != U) and e.t("!dead", not isdead(m, c)) and e.t("cand", c != 0)):
        return 0
    if e.t("type1", utype(m, c) == 1) and e.t("alignsame", alignsame(m, U, c)):
        bi = baseid(m, c)
        bi = bi if 0 <= bi < ms_count(m) else -1
        k = bi - 410
        if e.t("base410..416", 0 <= k <= 6) and e.t("table!=414", not (SHM_TABLE[k] if 0 <= k <= 6 else 1)):
            m.w32(b + 0x20, m.r32(b + 0x20) + 1)
            e.tag("ally %d counted" % bi)
            return 0
        if 0 <= k <= 6:
            e.tag("ally 414 on to the hostile part")
    if not (e.t("c4&4", m.r32(c + 0xC4) & 4) and e.t("hostile", hostile(m, G, U, c))):
        return 0
    O = m.r32(b)
    if e.t("O", O != 0):
        dO = distsq(m, O, c)
        if e.c("dO<=100", dO, "<=", 100):
            m.w32(b + 0x18, m.r32(b + 0x18) + 1)
        if e.c("dO<min", dO, "<", s32(m.r32(b + 0x14))):
            m.w32(b + 0x10, c)
            m.w32(b + 0x14, dO)
    d = distsq(m, U, c)
    if not e.c("d<=1024", d, "<=", 0x400):
        return 0
    m.w32(b + 0x1C, m.r32(b + 0x1C) + 1)
    if e.c("d<=100", d, "<=", 100):
        m.w32(b + 0x0C, m.r32(b + 0x0C) + 1)
    if e.c("d<min", d, "<", s32(m.r32(b + 8))):
        m.w32(b + 4, c)
        m.w32(b + 8, d)
    if e.t("prio", prio(m, U, c)):
        m.w32(b + 0x24, c)
        e.tag("priority target")
    return 0


def m_mephcb(e, a):                         # R50c: the pick's callback 0x005F7700(G, U; cand, blk)
    m, G, U, c, b = e.m, a["G"], a["U"], a["cand"], a["blk"]
    if not (e.t("cand!=U", c != U) and e.t("!dead", not isdead(m, c)) and e.t("cand", c != 0)
            and e.t("c4&4", m.r32(c + 0xC4) & 4) and e.t("hostile", hostile(m, G, U, c))):
        return 0
    d = distsq(m, U, c)
    if not e.c("d<=1024", d, "<=", 0x400):
        return 0
    m.w32(b + 0x1C, m.r32(b + 0x1C) + 1)
    if e.c("d<=225", d, "<=", 225):
        m.w32(b + 8, m.r32(b + 8) + 1)
    if e.c("d<near", d, "<", s32(m.r32(b + 4))):
        m.w32(b, c)
        m.w32(b + 4, d)
    h = s32(getstat(m, c, 6)) >> 8
    if e.c("hp<low", h, "<", s32(m.r32(b + 0x10))):
        m.w32(b + 0x0C, c)
        m.w32(b + 0x10, h)
    if e.c("d<plr", d, "<", s32(m.r32(b + 0x18))) and e.t("Uplayer", U != 0 and utype(m, U) == 0):
        m.w32(b + 0x14, c)
        m.w32(b + 0x18, d)
        e.tag("blk[5] set (searcher a player)")
    return 0


MEPH_BLK = STACK_TOP - 4 - 0x28             # EBP - 0x28 in the pick's frame


def m_mephpick(e, a):                       # R50c: the pick (G, U; M, t), AiUnitSearch kind 1 run whole
    m, G, U, M, t = e.m, a["G"], a["U"], a["M"], a["t"]
    b = MEPH_BLK
    for k, v in enumerate((0, 0x7FFFFFFF, 0, 0, 0x7FFFFFFF, 0, 0x7FFFFFFF, 0, 0, 0)):
        m.w32(b + 4 * k, v)
    room = unit_room(m, U)                  # AiSearchNearRooms: the near rooms' unit lists, in order
    if room:
        near, n = m.r32(room), m.r32(room + 0x24)
        for i in range(n):
            c = m.r32(m.r32(near + 4 * i) + 0x74)
            while c:
                m_mephcb(e, {"G": G, "U": U, "cand": c, "blk": b})
                c = m.r32(c + 0xE8)
    diff = m.r8(G + 0x6D)
    if e.t("blk3", m.r32(b + 0x0C) != 0):
        if e.c("D100<aip2", step(m, U + 0x20) % 100, "<", s16(m.r16(M + 0x5C + 2 * diff))):
            e.tag("first draw: blk[3]")
            return m.r32(b + 0x0C)
    else:
        e.tag("blk[3] 0: no first draw")
    if e.t("blk5", m.r32(b + 0x14) != 0):
        if e.c("D100<aip3", step(m, U + 0x20) % 100, "<", s16(m.r16(M + 0x62 + 2 * diff))):
            e.tag("second draw: blk[3]%s" % (" (not blk[5])" if m.r32(b + 0x0C) != m.r32(b + 0x14) else ""))
            return m.r32(b + 0x0C)
        e.tag("second draw: t")
    else:
        e.tag("blk[5] 0: t" if m.r32(b + 0x0C) == 0 or True else "")
    return t


def m_priest(e, a):                         # R85b: AiPriestHealCb
    m, U, c, b = e.m, a["U"], a["cand"], a["blk"]
    if e.t("cand", c != 0) and e.t("type1", utype(m, c) == 1) and e.t("!death", not isdeath(m, c)) \
            and e.t("alignsame", alignsame(m, U, c)) and e.t("align0", align(m, c) == 0) \
            and e.c("d<=bound", distsq(m, U, c), "<=", s32(m.r32(b + 8))):
        life = lifepct(m, c)
        if e.c("life<=75", life, "<=", 75) and e.c("life<best", life, "<", s32(m.r32(b + 4))):
            m.w32(b + 4, life)
            m.w32(b, c)
            e.tag("taken, the searcher itself" if c == U else "taken")
    return 0


def m_imp(e, a):                            # R113b: AiImpNearCb(G, U; cand, blk)
    m, G, U, c, b = e.m, a["G"], a["U"], a["cand"], a["blk"]
    want = 492 if ms_count(m) > 492 else -1
    if e.t("cand!=U", c != U) and e.t("cand", c != 0) and e.t("type1", utype(m, c) == 1) \
            and e.t("!death", not isdeath(m, c)) and e.t("base492", baseid(m, c) == want) \
            and e.t("alignsame", alignsame(m, U, c)) and e.t("align0", align(m, c) == 0) \
            and e.t("U no owner", uowner(m, G, U) == 0) \
            and e.t("ctl+14=-1", m.r32(ctlget(m, c) + 0x14) == 0xFFFFFFFF):
        if e.c("d<=bound", distsq(m, U, c), "<=", s32(m.r32(b))):
            e.tag("returned")
            return c
    return 0


def m_overseer(e, a):                       # R120b: AiOverseerMinionCb(G, U; cand, blk)
    m, G, U, c, b = e.m, a["G"], a["U"], a["cand"], a["blk"]
    if not (e.t("cand!=U", c != U) and e.t("cand", c != 0) and e.t("type1", utype(m, c) == 1)):
        return 0
    bi = baseid(m, c)
    if not (e.t("base>=0", bi >= 0) and e.t("base<count", bi < ms_count(m)) and e.t("base453", bi == 0x1C5)
            and e.t("!death", not isdeath(m, c)) and e.t("!hostile", not hostile(m, G, U, c))
            and e.t("!state141", not hasstate(m, c, 141))):
        return 0
    m.w32(b + 0x14, m.r32(b + 0x14) + 1)
    e.tag("counted")
    if e.t("blk3=0", m.r32(b + 0x0C) == 0):
        if e.c("d<=d1", distsq(m, U, c), "<=", s32(m.r32(b))) \
                and e.c("life<lim", lifepct(m, c), "<", s32(m.r32(b + 8))):
            m.w32(b + 0x0C, c)
            e.tag("blk[3] taken")
    if e.t("blk4=0", m.r32(b + 0x10) == 0):
        if e.c("d<=d2", distsq(m, U, c), "<=", s32(m.r32(b + 4))) and e.t("!unique", not typeflag(m, c, 8)):
            m.w32(b + 0x10, c)
            e.tag("blk[4] taken")
    return 0


def m_mincount(e, a):                       # R121a: AiMinionCountCb
    m, U, c, b = e.m, a["U"], a["cand"], a["blk"]
    if e.t("cand!=U", c != U) and e.t("cand", c != 0) and e.t("type1", utype(m, c) == 1) \
            and e.t("!death", not isdeath(m, c)):
        bi = baseid(m, c)
        bi = bi if 0 <= bi < ms_count(m) else -1
        if e.t("base453|461", bi in (0x1C5, 0x1CD)) and e.t("align0", align(m, c) == 0):
            m.w32(b, m.r32(b) + 1)
            e.tag("counted %d" % bi)
    return 0


def m_genspawn(e, a):                       # the R129 block: AiGenSpawnPickClass(G, U; out)
    m, G, U, out = e.m, a["G"], a["U"], a["out"]
    n_ms = ms_count(m)
    m.w32(out, 453 if e.c("count>453", n_ms, ">", 453) else -1)
    md = m.r32(U + 0x14) if U and utype(m, U) == 1 else 0
    lvl = s32(m.r32(md + 0x58)) if md else 0
    r = m.r32(G + 0xF0 + 4 * lvl)
    n = m.r8(r + 0x10)

    def ok(cls):
        rec = MS + cls * MS_SZ
        return 0 <= cls < n_ms and m.r8(rec + 0x0E) & 0x20

    if e.t("n>0", n > 0):
        low = step(m, U + 0x20)
        i = low & (n - 1) if e.t("pow2", n & (n - 1) == 0) else low % n
    else:
        i = 0
    ci = s16(m.r16(r + 0x14 + 0x34 * i))
    if e.t("entry i", ok(ci)):
        m.w32(out, ci)
        e.tag("n = 0: entry 0's class taken, no draw" if n == 0 else "drawn entry taken")
        return 1
    if n == 0:
        e.tag("n = 0: fallback")
    for j in range(n):
        cj = s16(m.r16(r + 0x14 + 0x34 * j))
        if e.t("entry j", ok(cj)):
            m.w32(out, cj)
            e.tag("first flagged entry")
            return 1
    m.w32(out, 496 if e.c("count>496", n_ms, ">", 496) else -1)
    return 1


def m_wpick(e, a):                          # the R51 pick(w, n), 0x005FC130 (EAX the unit; w, n)
    m, U, w, n = e.m, a["U"], a["w"], s32(a["n"])
    s = 0
    for k in range(max(0, n)):
        s = s32(s + m.r32(w + 4 * k))
    r = 0
    if e.c("sum>0", s, ">", 0):
        low = step(m, U + 0x20)
        r = low & (s - 1) if e.t("pow2", s & (s - 1) == 0) else low % s
    c = 0
    for k in range(max(0, n)):
        c = s32(c + m.r32(w + 4 * k))
        if e.c("r<run", s32(r), "<", c):
            e.tag("sum <= 0, no draw, k returned" if s <= 0 else "sum > 0, k returned")
            return k
    e.tag("sum <= 0, fallback 1" if s <= 0 else "sum > 0, fallback 1")
    return 1


def m_life(e, a):                           # AiLifePct and UnitLifePct: the same map
    m, u = e.m, a["U"]
    hp, mx = getstat(m, u, 6), maxhp(m, u)
    if e.t("sar8", True):
        hp, mx = hp >> 8, mx >> 8
    if e.t("max=0", mx == 0):
        return 0
    return u32(tdiv(s32(hp * 100), mx) if e.t("trunc", True) else (s32(hp * 100) // mx if mx else 0))


def m_st319(e, a):
    m, U = e.m, a["U"]
    md = m.r32(U + 0x14) if U and utype(m, U) == 1 else 0
    w = m.r32(md + 0x54) if md else 1
    e.tag("word %s" % (w if w in (3, 19) else "other"))
    return 1 if e.t("3|19", w in (3, 19)) else 0


def m_owner(e, a):                          # MonsterOwner: the AI control's owner words looked up by GameFindUnit
    m, u = e.m, a["U"]
    if not (e.t("U", u != 0) and e.t("type1", utype(m, u) == 1)):
        return 0
    md = m.r32(u + 0x14)
    ctl = m.r32(md + 0x28) if e.t("md", md != 0) else 0
    g = m.r32(ctl + 0x28) if e.t("ctl", ctl != 0) else 0
    if not e.t("game", g != 0):
        return 0
    t, guid = m.r32(ctl + 0x30), m.r32(ctl + 0x2C)
    slot = g + 0x1B20 if e.t("type5", t == 5) else g + HASHOFF[t] + 4 * (guid & 0x7F)
    n = m.r32(slot)
    while n:
        if e.t("guid=", m.r32(n + 0x0C) == guid):
            return n
        n = m.r32(n + 0xE4)
    return 0


def m_entry(e, a):                          # MonAiEntryGet(U, state)
    m, U, st = e.m, a["U"], a["state"]
    if e.t("state!=0", st != 0):
        e.tag("state row")
        return 0x0073D358 + 16 * st
    md = m.r32(U + 0x14) if U and utype(m, U) == 1 else 0
    p = m.r32(md) if md else 0
    w = m.r16(p + 0x1E)
    if e.t("row in range", s16(w) >= 0 and w < 0x94):
        e.tag("state 0: the class's row")
        return 0x0073CA18 + 16 * s16(w)
    e.tag("state 0: row 0 (index out of range)")
    return 0x0073CA18


MODELS = {"nearally": m_nearally, "samebase": m_samebase, "wounded": m_wounded, "zakheal": m_zakheal,
          "fetrev": m_fetrev, "regurg": m_regurg, "oblkn": m_oblkn, "trkind": m_trkind, "randlohi": m_randlohi,
          "shroll": m_shroll, "shmcb": m_shmcb, "mephcb": m_mephcb, "mephpick": m_mephpick, "priest": m_priest,
          "imp": m_imp, "overseer": m_overseer, "mincount": m_mincount, "genspawn": m_genspawn, "wpick": m_wpick,
          "alife": m_life, "ulife": m_life, "st319": m_st319, "owner": m_owner, "entry": m_entry}


# ---- the case writer ----

class W:
    """One case's world: the memory overlay and the unit factory."""

    def __init__(self, rnd):
        self.rnd = rnd
        self.m = Mem()
        m = self.m
        self.guid = rnd.randrange(1, 1 << 20)
        m.w8(GAME + 0x6D, rnd.randrange(3))
        m.w32(GAME + 0xA8, rnd.randrange(1 << 20))
        m.w32(DT + 0xA78, MS)
        m.w32(DT + 0xA80, rnd.choice((0x2DD, 0x2DD, 0x300, 0x1ED, 0x1EC, 0x1F1, 0x1F0, 0x1C6, 0x1C5, 0x137, 0x136,
                                      0x18D, 0x18C, 0xEF, 0x8E, 0x8D)))
        m.w32(DT + 0xA90, MS2)
        m.w32(DT + 0xA98, rnd.choice((0x100, 0x100, 0x80, 0x10)))
        m.w32(DT + 0xB98, SK)
        m.w32(DT + 0xBA0, rnd.choice((SK_N, SK_N, 0x100, 0x10)))
        m.w32(DT + 0xBCC, ISC)
        m.w32(DT + 0xBD4, rnd.choice((ISC_N, ISC_N, ISC_N, 0x16D, 0xAD, 0xAC, 0x08, 0x07)))
        m.w32(DT + 0xC4, rnd.choice((0x1B8, 0x1B8, 0x100, 0x8E, 0x8D, 0x40, 0x22, 0x21)))
        mask = m.alloc(0x40)
        m.w32(DT + 0x150, mask)
        for i in range(16):
            m.w32(mask + 4 * i, rnd.getrandbits(32) & rnd.getrandbits(32) & rnd.getrandbits(32))
        cap = m.alloc(0x20)
        self.cap = cap
        for k in (6, 7, 0xAC):
            rec = ISC + k * ISC_SZ
            if rnd.randrange(5) == 0:
                m.w8(rec + 5, 0x04)
                m.w32(rec + 0x2C, rnd.choice((0, 1, 50, 1 << 10, rnd.getrandbits(16))))
                m.w8(rec + 0x18, rnd.choice((0, 8, 1, 33)))

    def ms(self, cls):
        return MS + cls * MS_SZ

    def statlist(self, typ, hp, mx, al, states, flag=True):
        m, rnd = self.m, self.rnd
        lst = m.alloc(0x60)
        m.w32(lst + 0x10, (0x80000000 if flag else 0) | rnd.getrandbits(8))
        live = [(0x60000, hp), (0x70000, mx)] + [(rnd.randrange(1 << 31), rnd.getrandbits(32))
                                                 for _ in range(rnd.randrange(3))]
        other = [(0x60000, rnd.getrandbits(20)), (0x70000, rnd.getrandbits(20))]
        for off, entries in ((0x48, live), (0x24, other)) if flag else ((0x24, live), (0x48, other)):
            entries = sorted(dict(entries).items(), key=lambda kv: s32(kv[0]))
            arr = m.alloc(8 * len(entries) + 8)
            for i, (k, v) in enumerate(entries):
                m.w32(arr + 8 * i, k)
                m.w32(arr + 8 * i + 4, v)
            m.w32(lst + off, arr)
            m.w16(lst + off + 4, len(entries))
        if rnd.randrange(4) == 0:
            m.w32(lst + 0x44, self.bare(rnd.choice((0, 1, 2, 3))))
        if al is not None:                  # the alignment node (id 0x69), after a decoy or two
            node = m.alloc(0x60)
            m.w32(node + 0x10, rnd.choice((0x80000000, 0x80000000, 0)))
            m.w32(node + 0x14, 0x69)
            arr = m.alloc(0x18)
            ks = sorted({0xAC0000: al, rnd.randrange(1 << 20): 7}.items(), key=lambda kv: s32(kv[0]))
            for i, (k, v) in enumerate(ks):
                m.w32(arr + 8 * i, k)
                m.w32(arr + 8 * i + 4, v)
            for off in (0x24, 0x48):
                m.w32(node + off, arr)
                m.w16(node + off + 4, len(ks))
            head = rnd.choice((0x3C, 0x40))
            chain = [node]
            for _ in range(rnd.randrange(3)):
                d = m.alloc(0x30)
                m.w32(d + 0x14, rnd.choice((0x68, 0x6A, 0, 0x169)))
                chain.insert(rnd.randrange(len(chain) + 1), d)
            for x, y in zip(chain, chain[1:]):
                m.w32(x + 0x2C, y)
            m.w32(lst + head, chain[0])
        bits = m.alloc(0x40)
        m.w32(lst + 0x58, bits)
        for s in states:
            m.w32(bits + 4 * (s >> 5), m.r32(bits + 4 * (s >> 5)) | 1 << (s & 31))
        return lst

    def bare(self, typ):
        u = self.m.alloc(0x100)
        self.m.w32(u, typ)
        return u

    def unit(self, typ=1, cls=None, mode=None, x=None, y=None, hp=None, mx=None, al=0, c4=0, mdflags=0,
             states=(), stats=True, flag=True, path=True, md=True, ctl=True, near=None, dead=False):
        m, rnd = self.m, self.rnd
        u = m.alloc(0x100)
        self.guid += rnd.randrange(1, 300)
        m.w32(u, typ)
        m.w32(u + 4, rnd.randrange(0x300) if cls is None else cls)
        m.w32(u + 0x0C, self.guid)
        m.w32(u + 0x10, rnd.choice((1, 2, 3, 4, 5, 6, 7, 8, 10, 13, 15)) if mode is None else mode)
        m.w32(u + 0x20, rnd.getrandbits(32))
        m.w32(u + 0x24, rnd.getrandbits(32))
        m.w32(u + 0xC4, c4 | (0x10000 if dead else 0))
        if path:
            p = m.alloc(0x20)
            m.w32(u + 0x2C, p)
            if near is not None:
                x, y = near
            x = rnd.randrange(0x10000) if x is None else x
            y = rnd.randrange(0x10000) if y is None else y
            if typ == 2 or 4 <= typ <= 5:
                m.w32(p + 0x0C, x)
                m.w32(p + 0x10, y)
            else:
                m.w16(p + 2, x)
                m.w16(p + 6, y)
        if stats:
            hp = rnd.getrandbits(20) if hp is None else hp
            mx = rnd.getrandbits(20) if mx is None else mx
            m.w32(u + 0x5C, self.statlist(typ, hp, mx, al, states, flag))
        if typ == 1 and md:
            d = m.alloc(0x60)
            m.w32(u + 0x14, d)
            m.w16(d + 0x16, mdflags)
            if ctl:
                c = m.alloc(0x40)
                m.w32(d + 0x28, c)
                m.w32(c + 0x14, rnd.choice((0xFFFFFFFF, 0xFFFFFFFF, 0, 1, rnd.getrandbits(32))))
        if typ == 0:
            d = m.alloc(0x40)
            m.w32(u + 0x14, d)
        return u

    def hash_in(self, u, typ=None):
        m = self.m
        t = m.r32(u) if typ is None else typ
        g = m.r32(u + 0x0C)
        slot = GAME + 0x1B20 if t == 5 else GAME + HASHOFF[t] + 4 * (g & 0x7F)
        m.w32(u + 0xE4, m.r32(slot))
        m.w32(slot, u)

    def set_owner(self, u, o, game=GAME):   # the monster's AI-control owner words, MonsterOwner's lookup
        m = self.m
        d = m.r32(u + 0x14)
        c = m.r32(d + 0x28)
        m.w32(c + 0x28, game)
        m.w32(c + 0x2C, m.r32(o + 0x0C))
        m.w32(c + 0x30, m.r32(o))
        self.hash_in(o)

    def setbase(self, cls, base):
        self.m.w16(self.ms(cls) + 2, base)

    def near_xy(self, U, d2):
        """A position whose UnitDistSq from U is d2 when d2 is a sum of two squares, else about d2; now and then
        a far one (a coordinate difference near 0xFFFF, whose square wraps)."""
        rnd, m = self.rnd, self.m
        x0, y0 = pos(m, U)
        if rnd.randrange(16) == 0:
            return (x0 + rnd.randrange(0x8000, 0x10000)) & 0xFFFF, (y0 + rnd.randrange(0x10000)) & 0xFFFF
        d2 = max(0, min(d2, 1 << 30))
        r = int(d2 ** 0.5)
        pairs = [(a, int(round((d2 - a * a) ** 0.5))) for a in range(0, r + 1)
                 if int(round((d2 - a * a) ** 0.5)) ** 2 == d2 - a * a] if r < 3000 else []
        if pairs and rnd.randrange(4):
            dx, dy = rnd.choice(pairs)
        else:
            dx = rnd.randrange(0, r + 1)
            dy = int(max(0, d2 - dx * dx) ** 0.5)
        if rnd.randrange(2):
            dx = -dx
        if rnd.randrange(2):
            dy = -dy
        return (x0 + dx) & 0xFFFF, (y0 + dy) & 0xFFFF


def pick(rnd, *opts):
    return rnd.choice(opts)


def gen_cb(fam, rnd):
    """A callback case: U, one candidate meeting the claim's tests, with one of them broken now and then."""
    w = W(rnd)
    m = w.m
    n_ms = s32(m.r32(DT + 0xA80))
    brk = rnd.randrange(14) if rnd.randrange(3) == 0 else -1     # which test to break, if any
    Utyp = 1 if rnd.randrange(8) else pick(rnd, 0, 2, 3, 4)
    U = w.unit(typ=Utyp, mode=pick(rnd, 1, 2, 3, 8), al=pick(rnd, 0, 0, 0, 1, 2, None),
               x=rnd.randrange(0x400, 0xFC00), y=rnd.randrange(0x400, 0xFC00))
    G = GAME
    blk = m.alloc(0x40)
    bound = pick(rnd, 0, 1, 25, 100, 121, 225, 400, 625, 1024, 2500, 3000, 0x7FFFFFFF, -1, rnd.getrandbits(16),
                 100, 1024, 225)
    if fam in ("shmcb", "mephcb") and rnd.randrange(2):
        bound = pick(rnd, 99, 100, 101, 224, 225, 226, 1023, 1024, 1025)
    d2 = max(0, s32(bound) + pick(rnd, -1, 0, 0, 1, -50, 30)) if s32(bound) >= 0 else 0
    if rnd.randrange(6) == 0:
        d2 = rnd.getrandbits(18)
    xy = w.near_xy(U, d2)
    ctyp = 1
    if brk == 0:
        ctyp = pick(rnd, 0, 2, 3, 4, 5)
    if fam == "wounded" and rnd.randrange(4) == 0:
        ctyp = 0
    cls = rnd.randrange(n_ms) if n_ms > 0 else 0
    mode = pick(rnd, 1, 2, 3, 4, 5, 8, 13, 15)
    if brk == 1 or (fam == "regurg" and brk != 1):
        mode = pick(rnd, 0, 12)
    if fam == "fetrev" and rnd.randrange(3) == 0:
        mode = 12
    al = 0
    if brk == 2:
        al = pick(rnd, 1, 2, None, 3)
    c4 = {"fetrev": 2, "regurg": 2, "oblkn": 2, "shmcb": 4, "mephcb": 4}.get(fam, 0)
    if brk == 3:
        c4 ^= pick(rnd, 2, 4, 0x200)
    if rnd.randrange(4) == 0:
        c4 |= rnd.getrandbits(12) & ~0x206
    mx = pick(rnd, 0, 0xFF, 0x100, 100 << 8, rnd.getrandbits(20), rnd.getrandbits(14) << 8)
    hp = rnd.randrange(0, max(1, s32(mx) + 1)) if rnd.randrange(3) else rnd.getrandbits(20)
    if rnd.randrange(3) == 0:               # an exact percentage at a bound of the claims
        mx = 100 << 8
        hp = pick(rnd, 39, 40, 41, 59, 60, 61, 74, 75, 76, 49, 50, 51, 0, 100) << 8 | rnd.getrandbits(8)
    if fam == "oblkn" and rnd.randrange(3) == 0:
        mx, hp = 100 << 8, pick(rnd, 39, 40, 40, 41) << 8
    states = []
    if brk == 4:
        states = [pick(rnd, 141, 0x21, rnd.randrange(0x1C0))]
    if rnd.randrange(3) == 0:
        states += [rnd.randrange(0x1C0) for _ in range(3)]
    mdflags = 0 if brk != 5 else pick(rnd, 8, 4, 0xC, 0x2)
    if rnd.randrange(5) == 0:
        mdflags |= rnd.getrandbits(16) & ~0xC
    want = {"zakheal": pick(rnd, 235, 238), "fetrev": pick(rnd, 141, 396), "oblkn": 0x136, "imp": 492,
            "overseer": 0x1C5, "mincount": pick(rnd, 0x1C5, 0x1CD),
            "shmcb": pick(rnd, 410, 411, 412, 413, 414, 415, 416, 409, 417)}.get(fam)
    c = w.unit(typ=ctyp, cls=cls, mode=mode, near=xy, hp=hp, mx=mx, al=al, c4=c4, mdflags=mdflags,
               states=states, flag=rnd.randrange(10) != 0, dead=(brk == 6), stats=rnd.randrange(12) != 0)
    if want is not None and brk != 7 and ctyp == 1 and 0 <= cls < n_ms:
        w.setbase(cls, want)
    if fam == "samebase" and Utyp == 1 and brk != 7:
        w.setbase(s32(m.r32(U + 4)) if 0 <= s32(m.r32(U + 4)) < n_ms else 0, baseid(m, c))
    if fam in ("regurg",) and ctyp == 1:
        ms = w.ms(cls) if 0 <= cls < n_ms else 0
        if ms:
            i2 = rnd.randrange(0x100)
            m.w16(ms + 0x18, pick(rnd, i2, i2, i2, -1, 0x7FFF))
            if brk != 8:
                m.w8(MS2 + i2 * MS2_SZ + 5, 0x10 | rnd.getrandbits(8))
            else:
                m.w8(MS2 + i2 * MS2_SZ + 5, rnd.getrandbits(8) & ~0x10)
    if fam == "shmcb" and ctyp == 1 and 0 <= cls < n_ms and rnd.randrange(2):
        rec = w.ms(cls)
        m.w8(rec + 0x0D, pick(rnd, 0x80, 0x80, 0x81, 0x00, 0x82))
        m.w8(rec + 0x0C, pick(rnd, 0, 0, 0x40, 0x80))
    if fam in ("fetrev",) and ctyp == 1 and rnd.randrange(5):
        w.set_owner(c, U if brk != 9 else w.unit(typ=1))
    if fam in ("overseer", "shmcb", "mephcb") and rnd.randrange(3) == 0 and ctyp == 1:
        w.set_owner(c, w.unit(typ=pick(rnd, 0, 1, 1), al=pick(rnd, 0, 1, 2)))
    if fam == "imp":
        if brk == 9 or rnd.randrange(8) == 0:
            o = w.unit(typ=pick(rnd, 0, 1, 4))
            w.hash_in(o)
            m.w32(U + 0xC8, 0x400 | rnd.getrandbits(8))
            m.w32(U + 0x94, m.r32(o))
            m.w32(U + 0x98, m.r32(o + 0x0C) if rnd.randrange(4) else m.r32(o + 0x0C) + 1)
        if ctyp == 1:
            ctl = ctlget(m, c)
            if ctl:
                m.w32(ctl + 0x14, 0xFFFFFFFF if brk != 10 else pick(rnd, 0, 1, 0x7FFFFFFF))
    if fam == "mephcb" and Utyp != 0 and rnd.randrange(3) == 0:
        U2 = w.unit(typ=0, x=rnd.randrange(0x400, 0xFC00), y=rnd.randrange(0x400, 0xFC00))
        U = U2
        c2 = c
        p = m.r32(c2 + 0x2C)
        if p and ctyp in (0, 1, 3):
            x, y = w.near_xy(U, d2)
            m.w16(p + 2, x)
            m.w16(p + 6, y)
    if fam in ("shmcb", "mephcb") and ctyp == 0 and Utyp == 0 or (fam == "shmcb" and rnd.randrange(10) == 0):
        pd = m.r32(U + 0x14) if utype(m, U) == 0 else 0
        if pd and ctyp == 0:
            node = m.alloc(0x20)
            m.w32(node, m.r32(c + 0x0C))
            m.w32(node + 4, pick(rnd, 8, 0, 9, 0xFF))
            m.w32(pd + 0x38, node)
    if fam == "fetrev" and rnd.randrange(3) == 0:
        m.w16(m.r32(c + 0x14) + 0x16, pick(rnd, 4, 8, 0xC)) if utype(m, c) == 1 and m.r32(c + 0x14) else None
    cand = c if brk != 11 else pick(rnd, 0, U)
    if fam == "nearally" or fam == "samebase" or fam == "regurg":
        m.w32(blk, pick(rnd, 0, U))
        m.w32(blk + 4, bound)
    elif fam == "wounded":
        m.w32(blk + 4, bound)
        m.w32(blk + 8, pick(rnd, 0, 1, 25, 50, 100, -1, rnd.getrandbits(8)))
    elif fam == "zakheal":
        m.w32(blk + 4, rnd.randrange(4))
        m.w32(blk + 8, pick(rnd, 0x7FFFFFFF, 0, 1, -1, 0x7FFFFFFF, 30, 61, 60, 59, 40, rnd.randrange(62)))
        if cand and rnd.randrange(3) == 0:
            m.w32(blk + 8, max(1, lifepct(m, cand)))
        m.w32(blk + 0x0C, bound)
    elif fam == "fetrev":
        m.w32(blk + 4, pick(rnd, 0x7FFFFFFF, d2, d2 + 1, 0))
        m.w32(blk + 8, bound)
        m.w32(blk + 0x10, pick(rnd, 0x7FFFFFFF, d2, d2 + 1, 0))
        m.w32(blk + 0x14, rnd.randrange(5))
        m.w32(blk + 0x18, pick(rnd, 0, 0, 1, 2, 3, 4, -1, 3, 3))
    elif fam == "oblkn":
        m.w32(blk + 8, bound)
        m.w32(blk + 0x0C, pick(rnd, 0x7FFFFFFF, d2, d2 + 1, 0))
        m.w32(blk + 0x10, pick(rnd, 0x7FFFFFFF, d2, d2 + 1, 0))
    elif fam == "shmcb":
        m.w32(blk, pick(rnd, 0, w.unit(typ=1), U, w.unit(typ=pick(rnd, 1, 2))))
        if m.r32(blk) and m.r32(blk) != U and m.r32(m.r32(blk)) == 1:
            p = m.r32(m.r32(blk) + 0x2C)
            x, y = w.near_xy(c, pick(rnd, 99, 100, 101, 50, 400, 0))
            m.w16(p + 2, x)
            m.w16(p + 6, y)
        for k in range(1, 10):
            m.w32(blk + 4 * k, rnd.randrange(4))
        m.w32(blk + 8, pick(rnd, 0x7FFFFFFF, d2, d2 + 1, 0))
        m.w32(blk + 0x14, pick(rnd, 0x7FFFFFFF, 100, 101, 0))
        m.w32(blk + 0x24, 0)
    elif fam == "mephcb":
        for k, v in enumerate((0, 0x7FFFFFFF, 0, 0, 0x7FFFFFFF, 0, 0x7FFFFFFF, 0, 0, 0)):
            m.w32(blk + 4 * k, v if rnd.randrange(3) else rnd.choice((d2, d2 + 1, hp >> 8, (hp >> 8) + 1, 3)))
        if cand and utype(m, U) == 0 and rnd.randrange(2):
            m.w32(blk + 0x18, distsq(m, U, cand) + pick(rnd, 0, 0, 1))
        if cand and rnd.randrange(3) == 0:
            m.w32(blk + 0x10, (s32(getstat(m, cand, 6)) >> 8) + pick(rnd, 0, 0, 1))
        if cand and rnd.randrange(3) == 0:
            m.w32(blk + 4, distsq(m, U, cand) + pick(rnd, 0, 0, 1))
    elif fam == "priest":
        m.w32(blk + 4, pick(rnd, 75, 75, 76, 0, 50, 100))
        m.w32(blk + 8, bound)
    elif fam == "imp":
        m.w32(blk, bound)
    elif fam == "overseer":
        m.w32(blk, bound)
        m.w32(blk + 4, pick(rnd, bound, d2, d2 - 1, 0x7FFFFFFF))
        m.w32(blk + 8, pick(rnd, 50, 50, 0, 100, 101))
        m.w32(blk + 0x0C, pick(rnd, 0, 0, 0, U))
        m.w32(blk + 0x10, pick(rnd, 0, 0, 0, U))
        m.w32(blk + 0x14, rnd.randrange(5))
    elif fam == "mincount":
        m.w32(blk, rnd.randrange(10))
    args = {"G": G, "U": U, "cand": cand, "blk": blk}
    call = (FNS[fam], G, U, [cand, blk], [])
    dumps = [(blk, 0x28), (U + 0x20, 8)]
    if cand:
        dumps.append((cand + 0x20, 8))
    return w.m, args, call, dumps


def gen_trkind(rnd):
    w = W(rnd)
    m = w.m
    t = pick(rnd, 1, 1, 1, 0, 2, 3, 4)
    U = w.unit(typ=t)
    lvl = pick(rnd, 0, 1, 39, 40, 41, rnd.randrange(0x80))
    p = m.r32(U + 0x2C)
    room = m.alloc(0x80)
    x1, x2 = m.alloc(0x60), m.alloc(0x200)
    m.w32(room + 0x10, x1)
    m.w32(x1 + 0x58, x2)
    m.w32(x2 + 0x1D0, lvl)
    if rnd.randrange(8):
        m.w32(p if (t == 2 or 4 <= t <= 5) else p + 0x1C, room)
    elif not (t == 2 or 4 <= t <= 5) and rnd.randrange(2):
        m.w32(U + 0x2C, 0)
    for L in sorted({0, lvl}):
        if True:
            r = m.alloc(0x2E0)
            m.w32(GAME + 0xF0 + 4 * L, r)
            m.w32(r + 0x2D4, pick(rnd, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0, 1, 2, 0x80000000, 7))
    args = {"G": GAME, "U": U}
    return m, args, (FNS["trkind"], GAME, U, [], []), [(U + 0x20, 8)] + \
        [(m.r32(GAME + 0xF0 + 4 * L) + 0x2D4, 4) for L in (0, lvl)]


def gen_randlohi(rnd):
    w = W(rnd)
    m = w.m
    sp = m.alloc(8)
    m.w32(sp, rnd.getrandbits(32))
    m.w32(sp + 4, rnd.getrandbits(32))
    lo = pick(rnd, 0, 0, 1, -1, -5, 100, 0x7FFFFFF0, -0x80000000, rnd.getrandbits(32), rnd.randrange(-50, 50))
    span = pick(rnd, 0, 1, 2, 3, 4, 7, 8, 16, 100, 0x80000000, 0xFFFFFFFF, -1, -3, rnd.getrandbits(31),
                rnd.randrange(1, 40))
    hi = u32(lo + span)
    return m, {"seed": sp, "lo": u32(lo), "hi": hi}, (FNS["randlohi"], sp, u32(lo), [hi], []), [(sp, 8)]


def lcg(s0, s1):
    t = s0 * MUL + s1
    return t & 0xFFFFFFFF, (t >> 32) & 0xFFFFFFFF


def rng_n(seed, n):                         # Range(n) on a (lo, hi) pair: (value, new pair)
    if n <= 0:
        return 0, seed
    seed = lcg(*seed)
    return (seed[0] & (n - 1) if n & (n - 1) == 0 else seed[0] % n), seed


def gen_shroll(rnd):
    w = W(rnd)
    m = w.m
    m.w32(G_MAXLVL, w.cap)
    m.w32(w.cap, pick(rnd, 20, 30, 99, 1, 0, 5))
    U = w.unit(typ=1)
    O = w.bare(0)
    good = rnd.randrange(3) != 0            # most cases pass the class, fits and id tests
    nsk = s32(m.r32(DT + 0xBA0))
    i = rnd.randrange(1, nsk) if good else pick(rnd, 0, rnd.randrange(nsk), rnd.randrange(nsk), -1, nsk, nsk + 3)
    ocls = rnd.randrange(8)
    m.w32(O + 4, ocls)
    melee = pick(rnd, 0, 1)
    tgt = w.unit(typ=1) if (good or rnd.randrange(3)) else 0
    q = 0
    if 0 <= i < nsk:
        rec = SK + i * SK_SZ
        m.w8(rec + 0x0C, ocls if (good or rnd.randrange(5)) else pick(rnd, 0xFF, 0x80, (ocls + 1) & 7))
        k = pick(rnd, 0, 1, 2, 3, 4, 13, 5, 6, 8, 11, 12, 14)
        if good:
            k = pick(rnd, 4, 13) if melee else pick(rnd, 0, 1, 2, 3, 5, 6, 8, 14)
        m.w8(rec + 0x230, k)
        m.w16(rec + 0x80, pick(rnd, 0, 0, -1, rnd.randrange(1, 0x1C0)))
        m.w16(rec + 0x82, pick(rnd, 0, 0, -1, rnd.randrange(1, 0x1C0)))
        m.w8(rec + 4, rnd.getrandbits(8))
        if good and rnd.randrange(2):       # q = B >> 8 with A 0 and no shift: a chosen q
            q = pick(rnd, 0, 0, 1, 2, 3, 5, 10, 20, 40, 62, 63, 64, 127)
            m.w16(rec + 0x18C, 0)
            m.w16(rec + 0x18A, q << 8 | rnd.getrandbits(8))
            m.w8(rec + 0x188, 0)
        else:
            m.w16(rec + 0x18C, pick(rnd, 0, 1, 5, 10, -3, rnd.getrandbits(16)))
            m.w16(rec + 0x18A, pick(rnd, 0, 64, 128, 256, 1000, -40, rnd.getrandbits(16)))
            m.w8(rec + 0x188, pick(rnd, 0, 0, 1, 2, 4, 8, 31, 32, 33))
    elif rnd.randrange(2):
        m.w32(O + 4, 7)
    sk = w.bare(0)
    m.w32(sk + 0x28, pick(rnd, 1, 2, 5, 10, 20, 0, -2, 40))
    m.w32(sk + 0x34, pick(rnd, 0, 1, 5, 0x7FFFFFFF))
    ctl = m.alloc(0x40)
    T = s32(m.r32(GAME + 0xA8))
    m.w32(ctl + 0x14, pick(rnd, T, T - 1, T + 1, 0, T - 100) if not good else pick(rnd, T, T - 1, 0, T + 1))
    ms = w.ms(rnd.randrange(0x2DD))
    m.w16(ms + 0x82, pick(rnd, 0, 1, 2, 5, 20, 127, 128, 200, -3))
    m.w16(ms + 0x84, pick(rnd, 0, 1, 2, 5, 20, 255, 256, 300, -3))
    lo, hi = s16(m.r16(ms + 0x82)), s16(m.r16(ms + 0x84))
    lo = 1 if lo <= 1 else 0x80 if lo >= 0x80 else lo
    hi = 1 if hi <= 1 else 0x100 if hi >= 0x100 else hi
    m.w32(ctl + 0x18, pick(rnd, lo, lo - 1, lo + 1, hi << 5, (hi << 5) + 1, 0, 1, 50, 300, 8192, 8193, -1,
                           rnd.getrandbits(14)))
    v1c = pick(rnd, 0, 1, 50, 100, 320, 400, -50, rnd.getrandbits(10))
    m.w32(ctl + 0x1C, v1c)
    ctx = m.alloc(0x40)
    m.w32(ctx, ctl if rnd.randrange(20) else 0)
    m.w32(ctx + 8, tgt)
    m.w32(ctx + 0x18, melee)
    m.w32(ctx + 0x1C, ms)
    if 0 <= i < nsk:                         # states named by the record, on U and the target
        rec = SK + i * SK_SZ
        for who, off in ((U, 0x80), (tgt, 0x82)):
            st = s16(m.r16(rec + off))
            if who and st > 0 and rnd.randrange(3 if not good else 12) == 0:
                bits = m.r32(m.r32(who + 0x5C) + 0x58)
                m.w32(bits + 4 * (st >> 5), m.r32(bits + 4 * (st >> 5)) | 1 << (st & 31))
        st = s16(m.r16(rec + 0x80))
        if m.r8(rec + 4) & 0x04 and st > 0 and hasstate(m, U, st):     # keep off the undeclared path
            m.w8(rec + 4, m.r8(rec + 4) & ~0x04)
    if good and rnd.randrange(2):           # seeds that meet a compare at equality
        v18 = s32(m.r32(ctl + 0x18))
        v18 = lo if v18 < lo or v18 > hi << 5 else v18
        want = rnd.randrange(2)
        for _ in range(4000):
            seed = (rnd.getrandbits(32), rnd.getrandbits(32))
            d, s1 = rng_n(seed, 100)
            th = 100 - tdiv(s32(q * 160), 100)
            if want == 0 and d in (th, th + 1):
                break
            if want == 1 and d <= th:
                x, s2 = rng_n(s1, v18)
                y, _ = rng_n(s2, 100)
                if x == y:
                    break
        m.w32(U + 0x20, seed[0])
        m.w32(U + 0x24, seed[1])
    sk_arg = sk if rnd.randrange(30) else 0
    O_arg = O if rnd.randrange(30) else 0
    ctx_arg = ctx if rnd.randrange(30) else 0
    a = {"G": GAME, "U": U, "owner": O_arg, "skill": sk_arg, "id": u32(i), "ctx": ctx_arg}
    call = (FNS["shroll"], GAME, U, [O_arg, sk_arg, u32(i), rnd.getrandbits(1), ctx_arg], [])
    return m, a, call, [(U + 0x20, 8), (ctl + 0x14, 12)]


def gen_mephpick(rnd):
    w = W(rnd)
    m = w.m
    Ut = pick(rnd, 1, 1, 0, 0)
    U = w.unit(typ=Ut, x=rnd.randrange(0x400, 0xFC00), y=rnd.randrange(0x400, 0xFC00))
    rooms = [m.alloc(0x80) for _ in range(rnd.randrange(1, 5))]
    near = m.alloc(0x20)
    for i, r in enumerate(rooms):
        m.w32(near + 4 * i, r)
    r0 = rooms[0]
    m.w32(r0, near)
    m.w32(r0 + 0x24, len(rooms) if rnd.randrange(10) else 0)
    if rnd.randrange(12):
        m.w32(m.r32(U + 0x2C) + 0x1C, r0)
    lists = {r: [] for r in rooms}
    lists[r0].append(U)
    for _ in range(rnd.randrange(0, 9)):
        d2 = pick(rnd, 0, 1, 100, 224, 225, 226, 1023, 1024, 1025, 3000, rnd.randrange(1100), 225, 1024)
        if rnd.randrange(2):                # repeated distances: ties between candidates
            d2 = pick(rnd, 100, 400, 625)
        c = w.unit(typ=pick(rnd, 0, 1, 1, 1, 1, 2, 3), near=w.near_xy(U, d2), c4=pick(rnd, 4, 4, 4, 0),
                   al=pick(rnd, 1, 1, 0, 2), mode=pick(rnd, 1, 2, 3, 12, 0),
                   hp=pick(rnd, 0, 0xFF, 0x100, rnd.getrandbits(18), -0x500), dead=rnd.randrange(12) == 0)
        lists[rnd.choice(rooms)].append(c)
    if Ut == 0 and rnd.randrange(2):        # two live hostile monsters at one distance from a player
        d2 = pick(rnd, 100, 400, 625, 900)
        for _ in range(2):
            lists[r0].append(w.unit(typ=1, near=w.near_xy(U, d2), c4=4, al=1, mode=pick(rnd, 1, 2, 3)))
    for r, us in lists.items():
        rnd.shuffle(us)
        m.w32(r + 0x74, us[0] if us else 0)
        for x, y in zip(us, us[1:]):
            m.w32(x + 0xE8, y)
    M = w.ms(rnd.randrange(0x2DD))
    for d in range(3):
        m.w16(M + 0x5C + 2 * d, pick(rnd, 0, 1, 30, 50, 99, 100, -1))
        m.w16(M + 0x62 + 2 * d, pick(rnd, 0, 1, 30, 50, 99, 100, -1))
    if rnd.randrange(2):                    # aip(2), aip(3) at the draws' values (the search draws nothing)
        diff = m.r8(GAME + 0x6D)
        s1 = lcg(m.r32(U + 0x20), m.r32(U + 0x24))
        s2 = lcg(*s1)
        m.w16(M + 0x5C + 2 * diff, s1[0] % 100 + pick(rnd, 0, 0, 1))
        m.w16(M + 0x62 + 2 * diff, s2[0] % 100 + pick(rnd, 0, 0, 1))
    t = pick(rnd, 0, U, 0x12345678)
    a = {"G": GAME, "U": U, "M": M, "t": t}
    return m, a, (FNS["mephpick"], GAME, U, [M, t], []), [(MEPH_BLK, 0x28), (U + 0x20, 8)]


def gen_genspawn(rnd):
    w = W(rnd)
    m = w.m
    Ut = pick(rnd, 1, 1, 1, 1, 0, 2)
    U = w.unit(typ=Ut, md=rnd.randrange(10) != 0)
    lvl = pick(rnd, 0, 1, 5, rnd.randrange(0x80))
    md = m.r32(U + 0x14) if Ut == 1 else 0
    if md:
        m.w32(md + 0x58, lvl)
    n_ms = s32(m.r32(DT + 0xA80))
    for L in {0, lvl}:
        r = m.alloc(0x14 + 0x34 * 256)
        m.w32(GAME + 0xF0 + 4 * L, r)
        n = pick(rnd, 0, 0, 1, 2, 3, 4, 5, 8, 13, rnd.randrange(256))
        m.w8(r + 0x10, n)
        for j in range(max(n, 1)):
            cls = pick(rnd, rnd.randrange(max(1, n_ms)), rnd.randrange(max(1, n_ms)), -1, n_ms, 0x7FFF)
            m.w16(r + 0x14 + 0x34 * j, cls)
            if 0 <= cls < n_ms and rnd.randrange(pick(rnd, 2, 4, 8, 40)) == 0:
                m.w8(MS + cls * MS_SZ + 0x0E, 0x20 | rnd.getrandbits(8))
            elif 0 <= cls < n_ms and rnd.randrange(3) == 0:
                m.w8(MS + cls * MS_SZ + 0x0E, rnd.getrandbits(8) & ~0x20)
    out = m.alloc(8)
    m.w32(out, rnd.getrandbits(32))
    a = {"G": GAME, "U": U, "out": out}
    return m, a, (FNS["genspawn"], GAME, U, [out], []), [(out, 4), (U + 0x20, 8)]


def gen_wpick(rnd):
    w = W(rnd)
    m = w.m
    U = w.unit(typ=1)
    n = pick(rnd, 17, 17, 17, 4, 1, 0, -1, rnd.randrange(1, 32))
    wb = m.alloc(0x80)
    style = rnd.randrange(5)
    for k in range(max(0, n)):
        if style == 0:
            v = pick(rnd, 0, 0, 5, 10, 15, 20, 25, 40)
        elif style == 1:
            v = pick(rnd, 0, 1, 2, 4, 8, 16)
        elif style == 2:
            v = rnd.randrange(-20, 30)
        elif style == 3:
            v = pick(rnd, 0, 0, 0, -5, 5)
        else:
            v = rnd.getrandbits(31) if rnd.randrange(4) == 0 else rnd.randrange(100)
        m.w32(wb + 4 * k, v)
    if style == 1 and n > 0 and rnd.randrange(2):        # a power-of-two sum
        s = sum(s32(m.r32(wb + 4 * k)) for k in range(n))
        tgt = 1 << max(0, s.bit_length())
        m.w32(wb, s32(m.r32(wb)) + tgt - s)
    a = {"U": U, "w": wb, "n": u32(n)}
    return m, a, (FNS["wpick"], 0, 0, [wb, u32(n)], [("eax", U)]), [(U + 0x20, 8)]


def gen_life(rnd):
    w = W(rnd)
    m = w.m
    mx = pick(rnd, 0, 0xFF, 0x100, 0x101, -0x100, 100 << 8, rnd.getrandbits(20), rnd.getrandbits(32))
    hp = pick(rnd, 0, 0xFF, mx, s32(mx) // 2, rnd.getrandbits(20), rnd.getrandbits(32), -0x500)
    U = w.unit(typ=pick(rnd, 1, 1, 0, 2, 3), hp=hp, mx=mx, stats=rnd.randrange(15) != 0,
               flag=rnd.randrange(8) != 0)
    if rnd.randrange(20) == 0:
        U = 0
    return m, {"U": U}, U, [(U + 0x20, 8)] if U else []


def gen_st319(rnd):
    w = W(rnd)
    m = w.m
    U = w.unit(typ=pick(rnd, 1, 1, 1, 0, 2), md=rnd.randrange(8) != 0)
    md = m.r32(U + 0x14) if m.r32(U) == 1 else 0
    if md:
        m.w32(md + 0x54, pick(rnd, 3, 19, 0, 2, 4, 18, 20, 0x103, 0x13 | 0x10000, rnd.getrandbits(32)))
    if rnd.randrange(20) == 0:
        U = 0
    return m, {"U": U}, (FNS["st319"], U, 0, [], []), []


def gen_owner(rnd):
    w = W(rnd)
    m = w.m
    U = w.unit(typ=pick(rnd, 1, 1, 1, 1, 0, 2), md=rnd.randrange(10) != 0, ctl=rnd.randrange(10) != 0)
    ctl = ctlget(m, U)
    if ctl:
        for _ in range(rnd.randrange(4)):   # decoys in the hash table
            w.hash_in(w.unit(typ=pick(rnd, 0, 1, 2, 3, 4, 5), stats=False))
        o = w.unit(typ=pick(rnd, 0, 1, 1, 2, 3, 4, 5), stats=False)
        w.hash_in(o)
        m.w32(ctl + 0x28, GAME if rnd.randrange(8) else 0)
        m.w32(ctl + 0x2C, u32(m.r32(o + 0x0C) + pick(rnd, 0, 0, 0, 0, 1, 0x80)))
        m.w32(ctl + 0x30, m.r32(o) if rnd.randrange(8) else pick(rnd, 0, 1, 2, 3, 4, 5))
    if rnd.randrange(20) == 0:
        U = 0
    return m, {"U": U}, (FNS["owner"], U, 0, [], []), []


def gen_entry(rnd):
    w = W(rnd)
    m = w.m
    U = w.unit(typ=1)
    p = m.alloc(0x40)
    m.w32(m.r32(U + 0x14), p)
    m.w16(p + 0x1E, pick(rnd, 0, 1, 0x93, 0x94, 0x95, -1, 0x7FFF, 0x8000, rnd.randrange(0x94)))
    st = pick(rnd, 0, 0, 0, 1, 2, 9, 13, 18, 19, 0x20, rnd.randrange(13, 40))
    if st:
        if rnd.randrange(3) == 0:
            m.w32(U, pick(rnd, 0, 2, 3))
        if rnd.randrange(6) == 0:
            U = 0
    return m, {"U": U, "state": st}, (FNS["entry"], U, st, [], []), []


def gen_case(fam, rnd):
    if fam in ("trkind",):
        return gen_trkind(rnd)
    if fam == "randlohi":
        return gen_randlohi(rnd)
    if fam == "shroll":
        return gen_shroll(rnd)
    if fam == "mephpick":
        return gen_mephpick(rnd)
    if fam == "genspawn":
        return gen_genspawn(rnd)
    if fam == "wpick":
        return gen_wpick(rnd)
    if fam == "st319":
        return gen_st319(rnd)
    if fam == "owner":
        return gen_owner(rnd)
    if fam == "entry":
        return gen_entry(rnd)
    return gen_cb(fam, rnd)


def all_cases():
    """[(fam, k, mem, args, call, dumps)] in file order; alife and ulife share their images."""
    out = []
    for fam in FAMILIES:
        if fam == "ulife":
            continue
        rnd = random.Random("n66e-" + fam)
        for k in range(NCASES):
            if fam == "alife":
                m, a, U, dumps = gen_life(rnd)
                out.append(("alife", k, m, a, (FNS["alife"], U, 0, [], []), dumps))
                out.append(("ulife", k, m, a, (FNS["ulife"], 0, 0, [U], []), dumps))
                continue
            m, a, call, dumps = gen_case(fam, rnd)
            out.append((fam, k, m, a, call, dumps))
    return out


def predict(fam, m, a, flip=None):
    mm = m.copy()
    e = E(mm, flip)
    ret = MODELS[fam](e, a)
    return u32(ret if ret is not None else 0), mm, e.names, e.tags


POP = {"randlohi": 4, "shroll": 0x14, "genspawn": 4, "wpick": 8, "mephpick": 8, "alife": 0, "ulife": 4,
       "st319": 0, "owner": 0, "entry": 0, "trkind": 0}


def mem_spec(d):
    os.makedirs(d, exist_ok=True)
    ms = bytearray(MS_N * MS_SZ)
    for i in range(MS_N):
        struct.pack_into("<H", ms, i * MS_SZ + 2, i)
    files = {"ms.bin": bytes(ms), "zero-game.bin": bytes(GAME_LEN), "zero-dt.bin": bytes(DT_LEN),
             "zero-ms2.bin": bytes(MS2_N * MS2_SZ), "zero-isc.bin": bytes(ISC_N * ISC_SZ),
             "zero-sk.bin": bytes(SK_N * SK_SZ), "zero-arena.bin": bytes(ARENA_LEN)}
    for name, b in files.items():
        with open(os.path.join(d, name), "wb") as f:
            f.write(b)
    lines = ["# plan 0066 batch S1e: the declared image (tools/ai_s1e_emu.py)",
             "dword 00744304 %08x" % DT, "dword 0096c8a8 00000000",
             "load %08x %s" % (GAME, os.path.join(d, "zero-game.bin")),
             "load %08x %s" % (DT, os.path.join(d, "zero-dt.bin")),
             "load %08x %s" % (MS, os.path.join(d, "ms.bin")),
             "load %08x %s" % (MS2, os.path.join(d, "zero-ms2.bin")),
             "load %08x %s" % (ISC, os.path.join(d, "zero-isc.bin")),
             "load %08x %s" % (SK, os.path.join(d, "zero-sk.bin")),
             "load %08x %s" % (ARENA, os.path.join(d, "zero-arena.bin"))]
    lines += ["guard %08x" % a for a in FATAL]
    return "\n".join(lines) + "\n"


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    spec = mem_spec(d)
    with open(os.path.join(d, "s1e.mem"), "w") as f:
        f.write(spec)
    with open(os.path.join(d, "s1e.cases"), "w") as f:
        for fam, k, m, a, call, dumps in all_cases():
            f.write("# %s %d\n" % (fam, k))
            for lo, b in m.runs():
                if G_DT <= lo < G_DT + 4:
                    continue
                f.write("w %08x %s\n" % (lo, b.hex()))
            for reg, v in call[4]:
                f.write("r %s %08x\n" % (reg, v))
            for lo, n in dumps:
                f.write("d %08x %d\n" % (lo, n))
            fn, ecx, edx, stack, _ = call
            f.write("call %08x %08x %08x%s\n" % (fn, ecx, edx, "".join(" %08x" % u32(x) for x in stack)))
    print("cases written to", d)


def read_out(path):
    cases, reads, writes = [], [], []
    with open(path) as f:
        for line in f:
            p = line.split()
            if not p:
                continue
            if p[0] == "C":
                cases.append({"line": line.strip(), "d": []})
            elif p[0] == "D":
                cases[-1]["d"].append((int(p[1], 16), bytes.fromhex(p[2]) if len(p) > 2 else b""))
            elif p[0] == "R":
                reads.append((int(p[1], 16), int(p[2], 16), int(p[3]), int(p[4])))
            elif p[0] == "W":
                writes.append((int(p[1], 16), int(p[2], 16), int(p[3]), int(p[4])))
    return cases, reads, writes


def parse_c(line):
    p = line.split()
    if p[3] in ("STOP", "OBS"):
        return None
    kv = dict(x.split("=") for x in p[3:])
    return int(kv["eax"], 16), int(kv["pop"])


RETMASK = {"genspawn": 0xFF}


def outputs(fam, ret, mm, dumps):
    return (ret & RETMASK.get(fam, 0xFFFFFFFF), tuple(bytes(mm.r8(lo + i) for i in range(n)) for lo, n in dumps))


def cmd_check(d):
    cases = all_cases()
    got, reads, writes = read_out(os.path.join(d, "s1e.out"))
    lines = []
    ok = True
    if len(got) != len(cases):
        lines.append("S1E cases=%d outputs=%d result=FAIL" % (len(cases), len(got)))
        print("\n".join(lines))
        return 1
    per = {f: {"cases": 0, "match": 0, "bad": 0, "stopped": 0, "ctl": {}, "drew": 0, "names": set(), "ret": {}, "tags": {}}
           for f in FAMILIES}
    life = {"alife": {}, "ulife": {}}
    for (fam, k, m, a, call, dumps), g in zip(cases, got):
        P = per[fam]
        P["cases"] += 1
        pc = parse_c(g["line"])
        if pc is None:
            P["stopped"] += 1
            lines.append("STOP %s %d %s" % (fam, k, g["line"]))
            continue
        eax, pop = pc
        ret, mm, names, tags = predict(fam, m, a)
        for tg in tags:
            P["tags"][tg] = P["tags"].get(tg, 0) + 1
        if fam in ("alife", "ulife"):
            life[fam][k] = (eax, want[0])
        want = outputs(fam, ret, mm, dumps)
        have = (eax & RETMASK.get(fam, 0xFFFFFFFF), tuple(b for _, b in g["d"]))
        exp_pop = POP.get(fam, 8)
        if have == want and pop == exp_pop:
            P["match"] += 1
        else:
            P["bad"] += 1
            if P["bad"] <= 5:
                lines.append("BAD %s %d want=%08x %s have=%08x %s pop=%d" % (
                    fam, k, want[0], [x.hex() for x in want[1]], have[0], [x.hex() for x in have[1]], pop))
        sd = [i for i, (lo, n) in enumerate(dumps) if n == 8 and lo == U_seed(a)]
        if sd and bytes(m.r8(dumps[sd[0]][0] + i) for i in range(8)) != want[1][sd[0]]:
            P["drew"] += 1
        P["ret"][want[0]] = P["ret"].get(want[0], 0) + 1
        P["names"] |= names
        for nm in names:
            try:
                r2, mm2, _, _ = predict(fam, m, a, flip=nm)
                alt = outputs(fam, r2, mm2, dumps)
            except (KeyError, ValueError, IndexError, AssertionError, ZeroDivisionError):
                alt = None                  # the reversed model leaves the declared image: it predicts no output
            c = P["ctl"].setdefault(nm, [0, 0])
            if alt != want:
                c[0] += 1
                if alt == have and pop == exp_pop:
                    c[1] += 1
    total = sum(P["cases"] for P in per.values())
    tmatch = sum(P["match"] for P in per.values())
    for fam in FAMILIES:
        P = per[fam]
        unsep = sorted(n for n, c in P["ctl"].items() if c[0] == 0)
        passed = sorted(n for n, c in P["ctl"].items() if c[1] > 0)
        lines.append("S1E %s fn=%08x cases=%d match=%d bad=%d stopped=%d drew=%d controls=%d separated=%d "
                     "passed=%d" % (fam, FNS[fam], P["cases"], P["match"], P["bad"], P["stopped"], P["drew"],
                                    len(P["ctl"]), len(P["ctl"]) - len(unsep), len(passed)))
        lines.append("  CTL " + " ".join("%s:%d/%d" % (n, c[0], c[1]) for n, c in sorted(P["ctl"].items())))
        lines.append("  UNSEPARATED " + (" ".join(unsep) if unsep else "-"))
        lines.append("  TAGS " + ("; ".join("%s %d" % kv for kv in sorted(P["tags"].items())) or "-"))
        if passed:
            ok = False
            lines.append("  PASSED " + " ".join(passed))
        if P["bad"] or P["stopped"]:
            ok = False
    same = sum(1 for k in life["alife"] if life["alife"][k][0] == life["ulife"].get(k, (None,))[0])
    nz = sum(1 for k in life["alife"] if life["alife"][k][0] not in (0,))
    lines.append("S1E life pairs: AiLifePct = UnitLifePct on %d of %d images (%d non-zero)" % (same, len(life["alife"]), nz))
    acc = {}
    unacc = []
    for pc, addr, n, cnt in reads:
        hit = [nm for lo, ln, nm in CONST_READS if lo <= addr and addr + n <= lo + ln]
        if hit:
            acc[hit[0]] = acc.get(hit[0], 0) + cnt
        else:
            unacc.append("R %08x %08x %d %d" % (pc, addr, n, cnt))
    for pc, addr, n, cnt in writes:
        unacc.append("W %08x %08x %d %d" % (pc, addr, n, cnt))
    lines.append("S1E traced reads accounted: " + ", ".join("%s %d" % kv for kv in sorted(acc.items())))
    lines.append("S1E traced unaccounted: %d" % len(unacc))
    lines += ["  " + x for x in unacc[:40]]
    if unacc:
        ok = False
    lines.append("S1E total cases=%d match=%d" % (total, tmatch))
    lines.append("S1E result=%s" % ("ok" if ok else "FAIL"))
    print("\n".join(lines))
    return 0 if ok else 1


def U_seed(a):
    return a.get("U", 0) + 0x20


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

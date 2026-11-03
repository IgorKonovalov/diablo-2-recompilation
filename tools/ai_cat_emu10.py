#!/usr/bin/env python3
"""Plan 0052 phase 1.2, catalogue batch 10 (pool-G, `lane/r52j`): the think and init functions of AI rows 126, 127,
129-134, 136, 137, 139 and 141 run under Ghidra's p-code emulator (ADR-0015, ADR-0021) with
re/ghidra_scripts/EmuBoundary.java and compared with the models below. No game run, no slot. Same method as
tools/ai_cat_emu9.py (batch 9): one family per function (row 133's class dispatch and its three class thinks in one
family), the `le`, `d0`, `cmp` and `u16` controls and the site control, the EDGES line per family. Additions: two
controls of this batch, `abs` (row 129's frame distance read as `T - v14` without its absolute value) and `self`
(row 126's strike point taken from the spotter's own position instead of its target's); the AI control's +0x3C word
(row 129) compared with +0x14/+0x18/+0x1C; a declared quest list (QUESTS_FindById runs on the image, rows 132 and
133); UnitGetRoom run on the image.

    python3 -I tools/ai_cat_emu10.py cases [--dir D]      write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/ai_cat_emu10.py check [--dir D]      compare every D/<family>.out with its model, account for
                                                          every traced access, run the negative and site controls
    python3 -I tools/ai_cat_emu10.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r52j/emu. Every case draw comes from random.Random("r52j-<family>"), so `cases` regenerates
identical files.

Each family runs one function `(ECX game, EDX unit; ctx)` (ai/0011) on a declared image: the game's difficulty byte
(+0x6D), frame (+0xA8), quest list pointer (+0x10F4: 0, or a list whose first word is the first node; a node holds
its quest id at +0x00, its data pointer at +0x18 and the next node at +0xF4; the data's byte +0x11 and word +0x0C)
and the unit hash slot a lookup reads (+0x1120 + ... as 0x006E10E0 gives, or +0x1B20 for type 5); the unit's type
(+0x00, 1), class (+0x04), mode (+0x10), monster data pointer (+0x14), seed (+0x20/+0x24), path pointer (+0x2C),
game pointer (+0x80), owner type and guid (+0x94/+0x98), +0xC4, the flag word +0xC8 and the target-list index +0xD0;
the unit path's x (+0x02, u16), y (+0x06, u16) and room (+0x1C); the target's type (+0x00), guid (+0x0C), mode
(+0x10), path pointer (+0x2C), byte +0xC6 and hash next (+0xE4), that path's u16 +0x00, x (+0x02), y (+0x06), the
static words +0x0C/+0x10 and room (+0x1C); a second unit (0x12E00000: type, guid, mode, +0xC6, +0xE4); the monster
data's AI control pointer (+0x28); the AI control's state (+0x00), +0x14, +0x18, +0x1C and +0x3C; the AiCtx (+0x00
ctl, +0x08 target, +0x14 distance, +0x18 melee, +0x1C MonStats record or 0, +0x20 MonStats2 record); the MonStats
record of the unit's class (DataTables +0xA78 + class * 0x1A8: aip block +0x56..+0x85, Skill1..8 +0x170..+0x17F and
Sk1..8mode +0x180..+0x187), which is also the ctx record; the DataTables pointer (0x00744304), its MonStats base
(+0xA78) and count (+0xA80).

Callees that run on the declared image (not boundaries): RNG_Range 0x0045C390; the position getters 0x0045ADF0,
0x0045AE20 with 0x006488C0, 0x00648900; sub_00620BB0_UnitGetRoom with 0x00648A80; sub_00552F60_GameFindUnit (one
slot, one unit); sub_005541B0_UnitIsDead; sub_00552FD0_UnitGetOwner; QUESTS_FindById 0x00543640 with 0x0058CF90,
0x0058CFB0 and 0x0058CFE0 (quest 35); sub_005F6630_AiNestInit. Every other callee the function reaches is an
observed boundary. The claim per case: the first boundary reached (or the function's return), its call site (the
return address), the registers and stack arguments the callee takes, the unit seed, the AI control's +0x14/+0x18/
+0x1C/+0x3C and the unit's +0xC4 at the boundary, and where a pointer argument addresses the frame, the words it
addresses.

Families (function, row):
  spotter  0x005EE040 row 126 CatapultSpotter   barbi    0x005EDC40 row 127 init (NpcBarb)
  barb     0x005EDC50 row 127 NpcBarb           genspi   0x005E6190 row 129 init (GenericSpawner)
  genspawn 0x005E61B0 row 129 GenericSpawner    mauler   0x005EE260 row 130 DeathMauler
  wussie   0x005EE3C0 row 131 Wussie            statue   0x005EEAA0 row 132 AncientStatue
  ancient  0x005EF1A0 row 133 Ancient (with 0x005EEB70, 0x005EEDA0, 0x005EF010 to their first boundary)
  thronei  0x005EF310 row 134 init (BaalThrone)  throne   0x005EF320 row 134 BaalThrone
  taunt    0x005EF710 row 136 BaalTaunt         defiler  0x005EFA90 row 137 PutridDefiler
  tentacle 0x005EF820 row 139 BaalTentacle      bminion  0x005EF910 row 141 BaalMinion
The `entry` family (ENTRY below) reaches its first boundary before any test of its own: wussie (0x00588D60).

Controls: `le` compares each draw with `<=` instead of `<`; `d0` reads every aip from the Normal column; `cmp`
switches the strictness of every compare that is not a draw (`<` and `<=`, `>` and `>=`); `u16` reads Skill1 as an
unsigned word in its sign tests; `abs` drops row 129's absolute value; `self` takes row 126's strike point from the
spotter; `site` expects each call site one byte later. Each must fail every case it separates. The `EDGES` line under
each family counts, per compare, the cases that meet it at equality (the only cases in which a strictness control
can separate that compare); a compare missing from it has no control in the run.

Not covered (ADR-0021): every callee at or after a boundary and so every branch that a boundary call's result
decides, and every store after the boundary. Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r52j", "emu")

MUL = 0x6AC690C5
GAME = 0x12000000
UNIT = 0x12100000
UPATH = 0x12200000
ROOM = 0x12300000
TARGET = 0x12400000
MDATA = 0x12500000
CTX = 0x12700000
CTL = 0x12800000
MS2 = 0x12900000
DTBL = 0x12A00000
TPATH = 0x12B00000
TROOM = 0x12B10000
OTHER = 0x12E00000
QLIST = 0x12F00000
QNODE = 0x12F00100           # node k at QNODE + 0x100 k, its data at QDATA + 0x100 k
QDATA = 0x12F01000
MSBASE = 0x13000000          # DataTables +0xA78: MonStats record c at MSBASE + 0x1A8 c
G_DATATABLES = 0x00744304
HASHOFF = (0x1120, 0x1320, 0x1520, 0x1920, 0x1720)   # 0x006E10E0, u32 per unit type 0..4 (objdump -s of .rdata)
STK_LO = 0x7FEFFC00
STK_LEN = 1040
EBP = 0x7FEFFFFC
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)

SETMODEAT, IDLE, WALK, WALKZ, USESKILL, SETMODE, DELAY, PATHOVR, WALKPT, TLADD = (
    0x005DDF90, 0x005DE080, 0x005DEC80, 0x005DECA0, 0x005DEAD0, 0x005DDFC0, 0x005DE0F0, 0x005DE190, 0x005DEE50,
    0x005B1990)
HASSTATE, SEARCH, TELEPORT, KILLED, FREENEAR, CELLTEST, PICKCLASS, FINDCAT, WUSSIEQ, PICKPLR = (
    0x00639DF0, 0x005DD0B0, 0x00554EA0, 0x0057CCB0, 0x0064E7E0, 0x005FD350, 0x005E6020, 0x005EDF70, 0x00588D60,
    0x005E8F20)
EXTRA = (0x005DE000, 0x005DEFE0, 0x005DEF80, 0x00622C40, 0x006416D0, 0x0061AED0, 0x005DD2D0, 0x00574370,
         0x005B0E00, 0x00639DB0, 0x00586B30, 0x006556E0, 0x005DE200, 0x00588830, 0x005DDF20, 0x005DC5C0)
OBSERVE = tuple(sorted(set((SETMODEAT, IDLE, WALK, WALKZ, USESKILL, SETMODE, DELAY, PATHOVR, WALKPT, TLADD,
                            HASSTATE, SEARCH, TELEPORT, KILLED, FREENEAR, CELLTEST, PICKCLASS, FINDCAT, WUSSIEQ,
                            PICKPLR) + EXTRA)))
RET = "ret"

FNS = {"spotter": 0x005EE040, "barbi": 0x005EDC40, "barb": 0x005EDC50, "genspi": 0x005E6190,
       "genspawn": 0x005E61B0, "mauler": 0x005EE260, "wussie": 0x005EE3C0, "statue": 0x005EEAA0,
       "ancient": 0x005EF1A0, "thronei": 0x005EF310, "throne": 0x005EF320, "taunt": 0x005EF710,
       "defiler": 0x005EFA90, "tentacle": 0x005EF820, "bminion": 0x005EF910}
FAMILIES = tuple(FNS)
ENTRY = ("wussie",)
NCASES = 240
CONTROLS = ("le", "d0", "cmp", "u16", "abs", "self")


def u32(v):
    return v & 0xFFFFFFFF


def s32(v):
    v = u32(v)
    return v - (1 << 32) if v & 0x80000000 else v


def s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def s8(v):
    v &= 0xFF
    return v - 0x100 if v & 0x80 else v


def hx32(v):
    return struct.pack("<I", u32(v)).hex()


def hx16(v):
    return struct.pack("<H", v & 0xFFFF).hex()


def step(s):
    t = s[0] * MUL + s[1]
    s[0], s[1] = t & 0xFFFFFFFF, (t >> 32) & 0xFFFFFFFF


def slot_addr(typ, guid):                   # GameFindUnit's hash slot for a lookup (type 0..5)
    if typ == 5:
        return GAME + 0x1B20
    return GAME + HASHOFF[typ] + 4 * (guid & 0x7F)


# ------------------------------------------------------------------------------------------------- the models
class Hit(Exception):
    pass


def C(addr):                                # the return address of a 5-byte call at addr
    return addr + 5


class Env:
    """One case's inputs and the model's running state (the unit seed, the AI control's +0x14/+0x18/+0x1C/+0x3C,
    +0xC4)."""

    def __init__(self, inp, neg=None):
        self.i, self.neg = inp, neg
        self.seed = list(inp["seed"])
        self.c14, self.c18, self.c1c, self.c3c = inp["ctl14"], inp["ctl18"], inp["ctl1c"], inp["ctl3c"]
        self.c4 = inp["c4"]
        self.eq = set()                     # the compares this case met at equality
        self.reads = set()                  # the image-table reads the case makes (traced, to be accounted)
        self.tags = set()                   # path marks counted by `check` (TAGS line)

    def dcol(self):
        return 0 if self.neg == "d0" else self.i["diff"]

    def aip(self, k):
        return s16(self.i["aip"][k - 1][self.dcol()])

    def draw(self):
        step(self.seed)
        return self.seed[0] % 100

    def rng(self, n):                       # RNG_Range(seed, n): 0 and no step when n <= 0
        if s32(n) <= 0:
            return 0
        step(self.seed)
        return self.seed[0] % u32(n)

    def _cmp(self, d, c, edge):
        if d == c:
            self.eq.add(edge)
        return d <= c if self.neg == "le" else d < c

    def chance(self, k):
        return self._cmp(self.draw(), self.aip(k), "draw<aip%d" % k)

    def rchance(self, k):
        return self._cmp(self.rng(100), self.aip(k), "Range<aip%d" % k)

    def chance_c(self, c):
        return self._cmp(self.draw(), c, "draw<%d" % c)

    def lt(self, a, b, edge):
        if a == b:
            self.eq.add(edge)
        return a <= b if self.neg == "cmp" else a < b

    def le(self, a, b, edge):
        if a == b:
            self.eq.add(edge)
        return a < b if self.neg == "cmp" else a <= b

    def sk(self, k):
        return s16(self.i["skill"][k - 1])

    def has(self, k):                       # SkillK >= 0 (u16: always)
        return True if self.neg == "u16" else self.sk(k) >= 0

    def skm(self, k):
        return self.i["skmode"][k - 1]

    # ---- the callees run on the image
    def ufield(self, u):
        i = self.i
        if u == TARGET:
            return i["ttype"], i["tguid"], i["tmode"], i["tc6"]
        return i["wtype"], i["wguid"], i["wmode"], i["wc6"]

    def findunit(self, typ, guid):          # sub_00552F60_GameFindUnit on the declared slot
        if typ <= 4:
            self.reads.add((0x00552F9C, 0x006E10E0 + 4 * typ))
        u = self.i["slotval"]
        if u and self.ufield(u)[1] == u32(guid):
            return u
        return 0

    def dead(self, u):                      # sub_005541B0_UnitIsDead
        typ, _, mode, c6 = self.ufield(u)
        if c6 & 1:
            return True
        if typ == 0:
            return mode in (0, 17)
        if typ == 1:
            return mode in (0, 12)
        return True

    def tpos(self):                         # UnitGetSubX/Y of the target
        i = self.i
        if i["ttype"] in (2, 4, 5):
            return i["tsx"], i["tsy"]
        if i["tpnull"]:
            return 0, 0
        return i["tx"], i["ty"]

    def troom(self):                        # sub_00620BB0_UnitGetRoom(target)
        i = self.i
        if i["ttype"] in (2, 4, 5):
            return (i["tx"] << 16) | i["tlo"]
        return 0 if i["tpnull"] else TROOM

    def quest35(self):                      # QUESTS_FindById(G, 35): the data pointer's index, or None
        for k, qid in enumerate(self.i["quests"]):
            if qid == 0x23:
                return k
        return None

    def hit(self, fn, site, args, ecx=GAME, edx=UNIT, block=None):
        raise Hit((fn, site, ecx, edx, [u32(a) for a in args], list(self.seed), u32(self.c14), u32(self.c18),
                   u32(self.c1c), u32(self.c3c), u32(self.c4), block))

    def ret(self):
        self.hit(RET, 0, [])


def m_spotter(e):                                       # row 126, 0x005EE040
    i, t = e.i, (0 if e.i["tnull"] else TARGET)
    T = s32(i["frame"])
    if e.c1c == 0 or e.chance_c(3):
        e.hit(FINDCAT, C(0x005EE0A3), [])
    a2 = e.aip(2)
    if e.lt(0, s32(a2 - T + s32(e.c1c)), "aip2-T+v1C>0"):
        e.hit(IDLE, C(0x005EE252), [a2])
    if not t or not e.chance(1):
        e.hit(IDLE, C(0x005EE252), [a2])
    if e.lt(0, s32(e.c18), "v18>0"):
        k = e.c14
        e.c18 = u32(e.c18 - 1)
    else:
        k = e.rng(5)
        e.c14 = k
        e.c18 = u32(e.aip(5))
    a4 = e.aip(4)
    px, py = (i["ux"], i["uy"]) if e.neg == "self" else e.tpos()
    x = u32(e.rng(u32(2 * a4)) - a4 + px)
    y = u32(e.rng(u32(2 * a4)) - a4 + py)
    e.tags.add("radius<=0" if 2 * a4 <= 0 else "radius>0")
    e.hit(FREENEAR, C(0x005EE1EE), [ROOM, EBP - 0x20, 2, 0x805, 3], ecx=None, edx=None,
          block=(EBP - 0x20, [x, y]))


def m_barbi(e):                                         # row 127 init, 0x005EDC40: ret 4
    e.ret()


def m_barb(e):                                          # row 127, 0x005EDC50
    i, t = e.i, (0 if e.i["tnull"] else TARGET)
    if i["ud0"] == 0xB:
        e.hit(TLADD, C(0x005EDC8C), [0, 8])
    if t:
        if i["melee"]:
            e.hit(SETMODEAT, C(0x005EDCA6), [4, t])
        if e.lt(i["dist"], e.aip(3), "dist<aip3") and e.chance(2):
            e.hit(PATHOVR, C(0x005EDD1C), [100, 0], ecx=UNIT, edx=0)
    step(e.seed)
    s1 = e.seed[0]
    step(e.seed)
    s2 = e.seed[0]
    x = u32(s1 % 20 + i["ux"] - 40)
    y = u32(s2 % 20 + i["uy"] - 10)
    e.hit(WALKPT, C(0x005EDE0A), [x, y])


def m_genspi(e):                                        # row 129 init, 0x005E6190
    e.c14, e.c18 = e.i["frame"], 0                      # sub_005F6630_AiNestInit
    e.c3c = 0xFFFFFFFF
    e.ret()


def m_genspawn(e):                                      # row 129, 0x005E61B0
    i = e.i
    t = 0 if i["tnull"] else TARGET
    T = s32(i["frame"])
    if not t:
        e.hit(IDLE, C(0x005E62EE), [20])
    if s32(e.c3c) == -1:
        e.hit(PICKCLASS, C(0x005E61EA), [CTL + 0x3C])
    if e.lt(20, i["dist"], "dist>20"):
        e.hit(IDLE, C(0x005E62EE), [20])
    if e.le(e.aip(3), s32(e.c18), "v18>=aip3"):
        e.c4 = u32(e.c4 | 0x20000)
        e.hit(SETMODE, C(0x005E624C), [0, 0, 0])
    d = s32(T - s32(e.c14))
    if d < 0 and e.neg != "abs":
        d = s32(-d)
    if e.lt(d, e.aip(1), "|T-v14|<aip1"):
        e.hit(IDLE, C(0x005E62EE), [20])
    e.c14 = i["frame"]
    cls = 0x210 if s32(i["mscount"]) > 0x210 else 0xFFFFFFFF
    e.hit(CELLTEST, C(0x005E62BC), [i["ux"], i["uy"], 0], ecx=cls, edx=ROOM)


def m_mauler(e):                                        # row 130, 0x005EE260
    i, t = e.i, TARGET
    if i["melee"]:
        if e.chance(1):
            e.hit(SETMODEAT, C(0x005EE2C9), [4, t])
        e.hit(IDLE, C(0x005EE3A8), [15])
    if e.has(1) and e.lt(i["dist"], e.aip(3), "dist<aip3") and e.chance(4):
        e.hit(USESKILL, C(0x005EE345), [e.skm(1), e.sk(1), t, 0, 0])
    if e.chance(2):
        e.hit(WALK, C(0x005EE398), [t, 0])
    e.hit(IDLE, C(0x005EE3A8), [15])


def m_wussie(e):                                        # row 131, 0x005EE3C0
    e.hit(WUSSIEQ, C(0x005EE3DB), [EBP - 4], block=(EBP - 4, [0]))


def m_statue(e):                                        # row 132, 0x005EEAA0
    i = e.i
    k = e.quest35()
    if k is None or not i["q11"][k]:                    # 0x0058CFE0
        e.hit(IDLE, C(0x005EEB03), [25])
    if i["q0c"][k]:                                     # 0x0058CFB0
        e.hit(IDLE, C(0x005EEB03), [25])
    e.hit(HASSTATE, C(0x005EEAC0), [UNIT, 0x92], ecx=None, edx=None)


def m_ancient(e):                                       # row 133, 0x005EF1A0 and its three class thinks
    i = e.i
    cls = i["cls"]
    if cls not in (540, 541, 542):
        e.ret()
    k = e.quest35()                                     # 0x0058CF90: always present in this family
    done = i["q11"][k] == 0
    e.tags.add("cls%d" % cls)
    if cls == 540:                                      # 0x005EEB70
        if done:
            e.hit(IDLE, C(0x005EED88), [25])
        e.hit(HASSTATE, C(0x005EEB93), [UNIT, 0x36], ecx=None, edx=None)
    if cls == 541:                                      # 0x005EEDA0
        if done:
            e.hit(IDLE, C(0x005EEDC6), [25])
        e.hit(PICKPLR, C(0x005EEDE4), [EBP - 8, EBP - 0xC, 0, 0x005EEB10])
    if done:                                            # 0x005EF010
        e.hit(IDLE, C(0x005EF036), [25])
    e.hit(PICKPLR, C(0x005EF055), [EBP - 8, EBP - 4, 0, 0x005EEB10])


def m_thronei(e):                                       # row 134 init, 0x005EF310: ret 4
    e.ret()


def m_throne(e):                                        # row 134, 0x005EF320
    i = e.i
    T = s32(i["frame"])
    if i["mnull"]:
        e.hit(IDLE, C(0x005EF5CF), [10])
    if e.lt(T, s32(e.c1c), "T<v1C"):
        e.hit(IDLE, C(0x005EF354), [T - s32(e.c1c)])
    e.hit(SEARCH, C(0x005EF386), [EBP - 0x2C, 0, 3], block=(EBP - 0x2C, [0, 0x40, 0, 0x40]))


def m_taunt(e):                                         # row 136, 0x005EF710
    i = e.i
    t = 0 if i["tnull"] else TARGET
    if not t:
        e.hit(IDLE, C(0x005EF809), [25])
    still = i["ttype"] in (0, 1) and i["tmode"] == 1
    fire = False
    if still:
        e.c14 = u32(e.c14 + 1)
        fire = e.lt(e.aip(2), s32(e.c14), "v14>aip2")
    if fire or not still:
        e.c14 = 0
    if fire:
        e.hit(USESKILL, C(0x005EF798), [4, 0x11C, t, 0, 0])
    dist = i["dist"]
    if e.lt(e.aip(3), dist, "dist>aip3"):
        x, y = e.tpos()
        e.hit(TELEPORT, C(0x005EF7D6), [e.troom(), x, y, 0, 0])
    if e.lt(e.aip(1), dist, "dist>aip1"):
        e.hit(WALKZ, C(0x005EF7F5), [t])
    e.hit(IDLE, C(0x005EF809), [25])


def m_defiler(e):                                       # row 137, 0x005EFA90
    i = e.i
    if not i["tnull"] and i["melee"]:
        e.hit(SETMODEAT, C(0x005EFAC2), [4, TARGET])
    e.hit(SEARCH, C(0x005EFAED), [EBP - 0x30, 0x005EFA50, 1], block=(EBP - 0x30, [0, 0x19]))


def m_tentacle(e):                                      # row 139, 0x005EF820
    i = e.i
    T = s32(i["frame"])
    u = e.findunit(i["otype"], i["oguid"]) if i["c8"] & 0x400 else 0    # sub_00552FD0_UnitGetOwner
    if not u or e.dead(u):
        e.hit(KILLED, C(0x005EF8FB), [0, 1])
    e.tags.add("owner-alive")
    if e.c1c == 0:
        n = e.aip(3)
        r = e.rng(u32(n))
        e.c1c = u32(i["frame"] + (r + n) * 25)
    if e.lt(s32(e.c1c), T, "T>v1C"):
        e.hit(KILLED, C(0x005EF8FB), [0, 1])
    if i["melee"] and e.rchance(1):
        e.hit(SETMODEAT, C(0x005EF8C8), [4, 0 if i["tnull"] else TARGET])
    e.hit(IDLE, C(0x005EF8E6), [e.aip(2)])


def m_bminion(e):                                       # row 141, 0x005EF910
    i = e.i
    t = 0 if i["tnull"] else TARGET
    if t and i["melee"]:
        if e.chance(1):
            if e.has(1) and e.rchance(3):
                e.hit(USESKILL, C(0x005EF9B8), [e.skm(1), e.sk(1), t, 0, 0])
            e.hit(SETMODEAT, C(0x005EF9CA), [4, t])
        e.hit(IDLE, C(0x005EF9DC), [e.aip(3)])
    if e.chance(2):
        e.hit(WALKZ, C(0x005EFA27), [t])
    e.hit(DELAY, C(0x005EFA3B), [e.aip(4)])


MODELS = {"spotter": m_spotter, "barbi": m_barbi, "barb": m_barb, "genspi": m_genspi, "genspawn": m_genspawn,
          "mauler": m_mauler, "wussie": m_wussie, "statue": m_statue, "ancient": m_ancient, "thronei": m_thronei,
          "throne": m_throne, "taunt": m_taunt, "defiler": m_defiler, "tentacle": m_tentacle, "bminion": m_bminion}


def run_model(inp, neg=None, edges=None, reads=None, tags=None):
    e = Env(inp, neg)
    try:
        MODELS[inp["fam"]](e)
    except Hit as h:
        if edges is not None:
            for x in e.eq:
                edges[x] = edges.get(x, 0) + 1
        if reads is not None:
            reads |= e.reads
        if tags is not None:
            for x in e.tags:
                tags[x] = tags.get(x, 0) + 1
        return h.args[0]
    raise AssertionError("model returned without a boundary")


# ---------------------------------------------------------------------------------------------- case writer
def first_draws(seed, n):
    s, out = list(seed), []
    for _ in range(n):
        step(s)
        out.append(s[0] % 100)
    return out


def gen_family(fam, rnd):
    cases, meta = [], []
    for k in range(NCASES):
        seed = (rnd.randrange(1 << 32), rnd.randrange(1 << 32))
        ds = first_draws(seed, 4)
        aip = []
        for _ in range(8):
            aip.append([rnd.choice(ds + ds + [rnd.randrange(0, 101), rnd.randrange(-3, 111), 0, 1, 2, 5, 6, 10, 12,
                                              14, 15, 20, 24, 25, 50, 80, -1]) for _ in range(3)])
        diff = k % 3
        frame = rnd.randrange(100, 100000)
        a = [aip[j][diff] for j in range(8)]
        cls = rnd.randrange(0x2E0)
        inp = {
            "fam": fam, "seed": seed, "diff": diff, "aip": aip, "frame": frame,
            "melee": rnd.randrange(2),
            "dist": max(0, rnd.choice([0, 1, 5, 6, 7, 10, 20, 21, 24, 25, rnd.randrange(0, 60)]
                                      + [a[j] + rnd.choice((-1, 0, 1)) for j in (0, 2, 3)])),
            "ctl14": rnd.choice([0, 0, 1, 2, -1, u32(frame + rnd.choice((-1, 0, 1)))]),
            "ctl18": rnd.choice([0, 0, 1, 2, 7, -1, u32(frame + rnd.choice((-1, 0, 1)))]),
            "ctl1c": rnd.choice([0, 0, 1, -1, u32(frame + rnd.choice((-1, 0, 1)))]),
            "ctl3c": rnd.choice([0xFFFFFFFF, 0xFFFFFFFF, 453, 0, 496]),
            "c4": rnd.choice([0, 0x20000, rnd.randrange(1 << 32)]),
            "skill": [rnd.choice([-1, -1, 0x8000, 0xFFFE, 0x7FFF, 0, 1, rnd.randrange(0, 400), rnd.randrange(0, 400)])
                      & 0xFFFF for _ in range(8)],
            "skmode": [rnd.choice([rnd.randrange(16), rnd.randrange(16), rnd.randrange(0x80, 0x100)])
                       for _ in range(8)],
            "ux": rnd.randrange(1 << 16), "uy": rnd.randrange(1 << 16),
            "tx": rnd.randrange(1 << 16), "ty": rnd.randrange(1 << 16), "tlo": rnd.randrange(1 << 16),
            "tsx": rnd.randrange(1 << 31), "tsy": rnd.randrange(1 << 31),
            "ttype": rnd.choice([0, 0, 1, 1, 1, 2, 3, 4, 5]), "tguid": rnd.randrange(1 << 32),
            "tmode": rnd.choice([0, 1, 4, 12, 17]), "tc6": rnd.choice([0, 0, 0, 1]),
            "state": rnd.randrange(18), "cls": cls,
            "mscount": rnd.choice([0x2E0, 0x2E0, 0x210, 0x211, 0x20F, rnd.randrange(0, 0x400)]),
            "c8": rnd.choice([0, 0x400, 0x20000, 0x20400, rnd.randrange(1 << 32)]),
            "ud0": rnd.choice([11, 11, 8, 0, 3]),
            "otype": rnd.randrange(6), "oguid": rnd.randrange(1 << 32),
            "wtype": rnd.choice([0, 0, 1, 1, 2, 3]), "wmode": rnd.choice([0, 1, 4, 12, 17]),
            "wc6": rnd.choice([0, 0, 0, 1]), "wguid": 0, "slotval": 0,
            "tnull": 0, "mnull": 0, "quests": [], "q11": [], "q0c": [],
        }
        inp["tpnull"] = int(inp["ttype"] not in (2, 4, 5) and rnd.randrange(6) == 0)
        if fam in ("spotter", "barb", "genspawn", "taunt", "defiler", "tentacle", "bminion") and rnd.randrange(6) == 0:
            inp["tnull"] = 1
        look = None                                     # the one GameFindUnit lookup a family can make: (type, guid)
        if fam == "spotter":
            inp["ctl1c"] = rnd.choice([0, u32(frame - a[1] + rnd.choice((-1, 0, 1))), u32(frame - a[1] - 50),
                                       u32(frame + 100), 1])
            inp["ctl18"] = rnd.choice([0, 0, 1, 2, -1, 0x80000000])
            inp["ctl14"] = rnd.randrange(5)
            if rnd.randrange(3) == 0:
                aip[0][diff] = rnd.choice([100, 90, ds[1] + 1])
            if rnd.randrange(4) == 0:
                aip[3][diff] = rnd.choice([0, -1, -3, 16, 8])
        if fam == "barb":
            inp["dist"] = max(0, rnd.choice([a[2] + rnd.choice((-1, 0, 1)), rnd.randrange(0, 40)]))
            inp["melee"] = rnd.choice([0, 0, 1])
        if fam == "genspawn":
            inp["ctl3c"] = rnd.choice([0xFFFFFFFF, 453, 453, 300, 0])
            inp["dist"] = rnd.choice([19, 20, 21, 0, 5, rnd.randrange(0, 40)])
            inp["ctl18"] = u32(a[2] + rnd.choice((-1, 0, 1, -5)))
            inp["ctl14"] = u32(frame + rnd.choice((a[0], -a[0])) + rnd.choice((-1, 0, 1, 100, -100)))
            if rnd.randrange(8) == 0:
                inp["ctl14"] = u32(frame + 0x80000000)
        if fam == "mauler":
            inp["dist"] = max(0, rnd.choice([a[2] + rnd.choice((-1, 0, 1)), rnd.randrange(0, 40)]))
            if rnd.randrange(3) == 0:                   # to the Skill1 use: not in melee, in range, Skill1 set
                inp["melee"] = 0
                inp["skill"][0] = rnd.randrange(0, 400)
                aip[2][diff] = max(1, inp["dist"] + rnd.choice((0, 1, 5)))
                aip[3][diff] = rnd.choice([100, 60, ds[0] + 1, ds[0]])
        if fam in ("statue", "ancient"):
            n = rnd.choice([0, 1, 1, 2, 2]) if fam == "statue" else rnd.choice([1, 2])
            ids = [rnd.choice([0x23, 0x23, 0x22, 0x24, 0]) for _ in range(n)]
            if fam == "ancient" and 0x23 not in ids:
                ids[-1] = 0x23
            inp["quests"] = ids
            inp["q11"] = [rnd.choice([0, 0, 1, 0xFF]) for _ in ids]
            inp["q0c"] = [rnd.choice([0, 0, 0, 1, rnd.randrange(1 << 32)]) for _ in ids]
            if fam == "statue" and rnd.randrange(3) == 0:   # to the state test: quest 35 met, its word 0
                inp["quests"] = [rnd.choice([0x22, 0x24]), 0x23][rnd.randrange(2):]
                inp["q11"] = [rnd.choice([1, 0xFF]) for _ in inp["quests"]]
                inp["q0c"] = [0 for _ in inp["quests"]]
            if fam == "ancient":
                inp["cls"] = rnd.choice([540, 541, 542, 540, 541, 542, rnd.randrange(0x2E0), 539, 543])
        if fam == "throne":
            inp["mnull"] = int(rnd.randrange(8) == 0)
            inp["ctl1c"] = rnd.choice([0, u32(frame + rnd.choice((-1, 0, 1, 100, -100, 250)))])
        if fam == "taunt":
            inp["ttype"] = rnd.choice([0, 0, 1, 1, 2, 3, 4])
            inp["tpnull"] = int(inp["ttype"] not in (2, 4, 5) and rnd.randrange(8) == 0)
            inp["tmode"] = rnd.choice([1, 1, 1, 0, 4])
            inp["ctl14"] = u32(a[1] + rnd.choice((-2, -1, 0, 1)))
            inp["dist"] = max(0, rnd.choice([a[2] + rnd.choice((-1, 0, 1)), a[0] + rnd.choice((-1, 0, 1)),
                                             rnd.randrange(0, 40)]))
        if fam == "bminion" and rnd.randrange(3) == 0:  # to the Skill1 use: a target in melee, Skill1 set
            inp["tnull"], inp["melee"] = 0, 1
            inp["skill"][0] = rnd.randrange(0, 400)
            aip[0][diff] = rnd.choice([100, ds[0] + 1, ds[0]])
            aip[2][diff] = rnd.choice([100, 60, 50])
        if fam == "tentacle":
            look = (inp["otype"], inp["oguid"])
            inp["c8"] |= rnd.choice([0x400, 0x400, 0x400, 0])
            inp["ctl1c"] = rnd.choice([0, 0, u32(frame + rnd.choice((-1, 0, 1, 100)))])
            if rnd.randrange(4) == 0:
                aip[2][diff] = rnd.choice([0, -1, 1, 16, 10])
            if rnd.randrange(2) == 0:                   # a living owner
                inp["c8"] |= 0x400
                look = (inp["otype"], inp["oguid"])
                inp["forceowner"] = 1
        if look is not None:
            sv = OTHER if inp.get("forceowner") else rnd.choice([0, OTHER, OTHER, OTHER, OTHER, TARGET])
            if sv == OTHER:
                inp["wguid"] = u32(look[1] + (0 if inp.get("forceowner") else rnd.choice((0, 0, 0, 0, 1))))
                inp["wmode"] = rnd.choice([1, 4, 2]) if inp.get("forceowner") else rnd.choice([1, 4, 2, 0, 12, 17])
                inp["wtype"] = 1 if inp.get("forceowner") else rnd.choice([0, 1, 1, 1, 2])
                if inp.get("forceowner"):
                    inp["wc6"] = 0
                    if rnd.randrange(2):
                        inp["ctl1c"] = 0
            elif sv == TARGET:
                inp["tguid"] = u32(look[1] + rnd.choice((0, 0, 0, 1)))
            inp["slotval"] = sv
        mrec = MSBASE + 0x1A8 * inp["cls"]
        sk = "".join(hx16(s) for s in inp["skill"])
        lines = [
            "w %08x %s" % (GAME + 0x6D, "%02x" % diff),
            "w %08x %s" % (GAME + 0xA8, hx32(frame)),
            "w %08x %s" % (GAME + 0x10F4, hx32(QLIST if inp["quests"] else 0)),
            "w %08x %s" % (UNIT, hx32(1) + hx32(inp["cls"])),
            "w %08x %s" % (UNIT + 0x10, hx32(1) + hx32(MDATA)),
            "w %08x %s%s" % (UNIT + 0x20, hx32(seed[0]), hx32(seed[1])),
            "w %08x %s" % (UNIT + 0x2C, hx32(UPATH)),
            "w %08x %s" % (UNIT + 0x80, hx32(GAME)),
            "w %08x %s" % (UNIT + 0x94, hx32(inp["otype"]) + hx32(inp["oguid"])),
            "w %08x %s" % (UNIT + 0xC4, hx32(inp["c4"]) + hx32(inp["c8"])),
            "w %08x %s" % (UNIT + 0xD0, hx32(inp["ud0"])),
            "w %08x %s" % (UPATH + 0x02, hx16(inp["ux"])), "w %08x %s" % (UPATH + 0x06, hx16(inp["uy"])),
            "w %08x %s" % (UPATH + 0x1C, hx32(ROOM)),
            "w %08x %s" % (TARGET, hx32(inp["ttype"])),
            "w %08x %s" % (TARGET + 0x0C, hx32(inp["tguid"]) + hx32(inp["tmode"])),
            "w %08x %s" % (TARGET + 0x2C, hx32(0 if inp["tpnull"] else TPATH)),
            "w %08x %s" % (TARGET + 0xC6, "%02x" % inp["tc6"]),
            "w %08x %s" % (TARGET + 0xE4, hx32(0)),
            "w %08x %s" % (TPATH + 0x00, hx16(inp["tlo"]) + hx16(inp["tx"])),
            "w %08x %s" % (TPATH + 0x06, hx16(inp["ty"])),
            "w %08x %s" % (TPATH + 0x0C, hx32(inp["tsx"]) + hx32(inp["tsy"])),
            "w %08x %s" % (TPATH + 0x1C, hx32(TROOM)),
            "w %08x %s" % (MDATA + 0x28, hx32(CTL)),
            "w %08x %s" % (CTL, hx32(inp["state"])),
            "w %08x %s%s%s" % (CTL + 0x14, hx32(inp["ctl14"]), hx32(inp["ctl18"]), hx32(inp["ctl1c"])),
            "w %08x %s" % (CTL + 0x3C, hx32(inp["ctl3c"])),
            "w %08x %s" % (CTX, hx32(CTL) + hx32(0) + hx32(0 if inp["tnull"] else TARGET) + hx32(0) + hx32(0)
                           + hx32(inp["dist"]) + hx32(inp["melee"]) + hx32(0 if inp["mnull"] else mrec)
                           + hx32(MS2)),
            "w %08x %s" % (mrec + 0x56, "".join(hx16(aip[j][d]) for j in range(8) for d in range(3))),
            "w %08x %s" % (mrec + 0x170, sk),
            "w %08x %s" % (mrec + 0x180, "".join("%02x" % m for m in inp["skmode"])),
            "w %08x %s" % (G_DATATABLES, hx32(DTBL)),
            "w %08x %s" % (DTBL + 0xA78, hx32(MSBASE)),
            "w %08x %s" % (DTBL + 0xA80, hx32(inp["mscount"])),
        ]
        if inp["quests"]:
            lines.append("w %08x %s" % (QLIST, hx32(QNODE)))
            for n, qid in enumerate(inp["quests"]):
                node, data = QNODE + 0x100 * n, QDATA + 0x100 * n
                nxt = QNODE + 0x100 * (n + 1) if n + 1 < len(inp["quests"]) else 0
                lines.append("w %08x %s" % (node, hx32(qid)))
                lines.append("w %08x %s" % (node + 0x18, hx32(data)))
                lines.append("w %08x %s" % (node + 0xF4, hx32(nxt)))
                lines.append("w %08x %s" % (data + 0x0C, hx32(inp["q0c"][n])))
                lines.append("w %08x %s" % (data + 0x11, "%02x" % inp["q11"][n]))
        if look is not None:
            lines.append("w %08x %s" % (slot_addr(*look), hx32(inp["slotval"])))
            if inp["slotval"] == OTHER:
                lines.append("w %08x %s" % (OTHER, hx32(inp["wtype"])))
                lines.append("w %08x %s" % (OTHER + 0x0C, hx32(inp["wguid"]) + hx32(inp["wmode"])))
                lines.append("w %08x %s" % (OTHER + 0xC6, "%02x" % inp["wc6"]))
                lines.append("w %08x %s" % (OTHER + 0xE4, hx32(0)))
        lines += [
            "d %08x %d" % (STK_LO, STK_LEN), "d %08x 8" % (UNIT + 0x20), "d %08x 44" % (CTL + 0x14),
            "d %08x 4" % (UNIT + 0xC4),
            "call %08x %08x %08x %08x" % (FNS[fam], GAME, UNIT, CTX),
        ]
        cases.append(lines)
        meta.append(inp)
    mem = ["observe %08x" % a for a in OBSERVE] + ["guard %08x" % a for a in FATAL + ALLOC]
    return cases, meta, mem


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        cases, meta, mem = gen_family(fam, random.Random("r52j-" + fam))
        with open(os.path.join(d, fam + ".cases"), "w") as f:
            for c in cases:
                f.write("\n".join(c) + "\n")
        with open(os.path.join(d, fam + ".mem"), "w") as f:
            f.write("\n".join(mem) + "\n")
        print("CASES %s %d" % (fam, len(cases)))


# ------------------------------------------------------------------------------------------------- the output
def read_out(path):
    calls, traced = [], []
    for ln in open(path):
        p = ln.split()
        if not p:
            continue
        if p[0] == "C":
            c = {"n": int(p[1]), "dumps": {}}
            if p[3] == "STOP":
                c["stop"] = " ".join(p[4:])
            elif p[3] == "OBS":
                c["obs"] = int(p[4], 16)
                kv = dict(x.split("=") for x in p[5:])
                c["regs"] = {k: int(v, 16) for k, v in kv.items() if k != "steps"}
            else:
                c["obs"] = RET
                kv = dict(x.split("=") for x in p[3:])
                c["eax"] = int(kv["eax"], 16)
            calls.append(c)
        elif p[0] == "A":
            calls[-1]["args"] = bytes.fromhex(p[1])
        elif p[0] == "D":
            calls[-1]["dumps"][int(p[1], 16)] = bytes.fromhex(p[2]) if len(p) > 2 else b""
        elif p[0] in ("R", "W"):
            traced.append(ln.strip())
    return calls, traced


def stack_words(c, addr, n):
    stk = c["dumps"][STK_LO]
    return list(struct.unpack_from("<%dI" % n, stk, addr - STK_LO))


def matches(c, want, site_shift=0):
    fn, site, ecx, edx, args, seed, c14, c18, c1c, c3c, c4, block = want
    if c.get("obs") != fn:
        return False
    gseed = list(struct.unpack("<II", c["dumps"][UNIT + 0x20]))
    g14, g18, g1c = struct.unpack_from("<III", c["dumps"][CTL + 0x14], 0)
    g3c = struct.unpack_from("<I", c["dumps"][CTL + 0x14], 0x28)[0]
    gc4 = struct.unpack("<I", c["dumps"][UNIT + 0xC4])[0]
    ok = gseed == seed and g14 == c14 and g18 == c18 and g1c == c1c and g3c == c3c and gc4 == c4
    if fn == RET:
        return ok and site_shift == 0
    a = c.get("args", b"")
    got = [struct.unpack_from("<I", a, 4 + 4 * k)[0] for k in range(len(args))]
    ret = struct.unpack_from("<I", a, 0)[0]
    ok = ok and ret == site + site_shift and got == args
    if ecx is not None:
        ok = ok and c["regs"]["ecx"] == u32(ecx)
    if edx is not None:
        ok = ok and c["regs"]["edx"] == u32(edx)
    if block is not None:
        addr, words = block
        ok = ok and stack_words(c, addr, len(words)) == [u32(w) for w in words]
    return ok


def check_family(fam, d):
    _, meta, _ = gen_family(fam, random.Random("r52j-" + fam))
    calls, traced = read_out(os.path.join(d, fam + ".out"))
    bad, match, stops = [], 0, 0
    ctl = {n: [0, 0] for n in CONTROLS}
    site_pass = 0
    bounds = {}
    ndraws = 0
    edges = {}
    reads = set()
    tags = {}
    if len(calls) != len(meta):
        bad.append("case count %d != %d" % (len(calls), len(meta)))
    for c, inp in zip(calls, meta):
        if "stop" in c:
            stops += 1
            bad.append("case %d STOP %s" % (c["n"], c["stop"]))
            continue
        want = run_model(inp, edges=edges, reads=reads, tags=tags)
        ok = matches(c, want)
        match += ok
        if not ok:
            bad.append("case %d mismatch want=%s@%s obs=%s args=%s" % (
                c["n"], want[0] if want[0] == RET else hex(want[0]), hex(want[1]),
                c.get("obs") if c.get("obs") == RET else hex(c.get("obs", 0)), c.get("args", b"")[:24].hex()))
        key = RET if want[0] == RET else "%x@%x" % (want[0], want[1])
        bounds[key] = bounds.get(key, 0) + 1
        ndraws += want[5] != list(inp["seed"])
        site_pass += matches(c, want, site_shift=1) if want[0] != RET else 0
        for n in ctl:
            nw = run_model(inp, neg=n)
            if nw != want:
                ctl[n][0] += 1
                ctl[n][1] += matches(c, nw)
    # The image-table reads the models account for (the unit hash offsets 0x006E10E0 read at 0x00552F9C); every
    # other traced access stays.
    expect = set("R %08x %08x 4" % (pc, addr) for pc, addr in reads)
    seen = set(" ".join(x.split()[:4]) for x in traced)
    accounted = len(seen & expect)
    if expect - seen:
        bad.append("accounted reads missing %s" % sorted(expect - seen))
    traced = [x for x in traced if " ".join(x.split()[:4]) not in expect]
    line = ("AI52J %s cases=%d match=%d bad=%d stopped=%d traced=%d accounted=%d drew=%d " % (
        fam, len(meta), match, len(bad), stops, len(traced), accounted, ndraws)
        + " ".join("%s_separating=%d %s_passed=%d" % (n, ctl[n][0], n, ctl[n][1]) for n in CONTROLS)
        + " site_control_passed=%d boundaries=%d" % (site_pass, len(bounds)))
    return line, bad[:20], traced[:20], bounds, ctl, edges, tags


def cmd_check(d):
    allok = True
    tot = [0, 0]
    for fam in FAMILIES:
        line, bad, traced, bounds, ctl, edges, tags = check_family(fam, d)
        print(line)
        print("  SITES " + " ".join("%s:%d" % kv for kv in sorted(bounds.items())))
        print("  EDGES " + " ".join("%s:%d" % kv for kv in sorted(edges.items())))
        if tags:
            print("  TAGS " + " ".join("%s:%d" % kv for kv in sorted(tags.items())))
        for b in bad:
            print("  BAD", b)
        for t in traced:
            print("  TRACED", t)
        if bad or traced or any(ctl[n][1] for n in ctl) or "site_control_passed=0" not in line:
            allok = False
        tot[0] += NCASES
        tot[1] += int(line.split("match=")[1].split()[0])
    print("AI52J total cases=%d match=%d" % tuple(tot))
    print("AI52J result=%s" % ("ok" if allok else "FAIL"))


def cmd_manifest(d, write):
    rows = []
    for fam in FAMILIES:
        for ext in ("cases", "mem", "out", "err"):
            p = os.path.join(d, "%s.%s" % (fam, ext))
            if os.path.exists(p):
                rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.basename(p)))
    for extra in ("check.txt", "ai_cat_emu10.py.rev"):
        p = os.path.join(d, extra)
        if os.path.exists(p):
            rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), extra))
    text = "\n".join(rows) + "\n"
    if write:
        with open(os.path.join(d, "manifest.sha256"), "w") as f:
            f.write(text)
    sys.stdout.write(text)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["cases", "check", "manifest"])
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "cases":
        cmd_cases(a.dir)
    elif a.cmd == "check":
        cmd_check(a.dir)
    else:
        cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    main(sys.argv[1:])

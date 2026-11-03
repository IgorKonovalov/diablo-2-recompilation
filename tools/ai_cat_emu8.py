#!/usr/bin/env python3
"""Plan 0052 phase 1.2, catalogue batch 8 (pool-E, `lane/r52h`): the think functions of AI rows 82, 83, 85, 89,
93-98 and 113-115 run under Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java
and compared with the models below. No game run, no slot. Same method as tools/ai_cat_emu4.py (batch 4) and
tools/ai_cat_emu5.py (batch 5): one family per function, the `le`, `d0`, `cmp` and `u16` controls and the site
control, the EDGES line per family. Two additions: RNG_RangePow2 and AiParamsHead run on the declared image (row 85's
corner pick, row 96's parameter record), and the row 85 corner table 0x006E337C is read from the image.

    python3 -I tools/ai_cat_emu8.py cases [--dir D]      write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/ai_cat_emu8.py check [--dir D]      compare every D/<family>.out with its model, account for
                                                         every traced access, run the negative and site controls
    python3 -I tools/ai_cat_emu8.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r52h/emu. Every case draw comes from random.Random("r52h-<family>"), so `cases` regenerates
identical files.

Each family runs one think function `(ECX game, EDX unit; ctx)` (ai/0009) on a declared image: the game's difficulty
byte (+0x6D) and frame (+0xA8); the unit's type (+0x00, 1), class (+0x04), mode (+0x10), monster data pointer
(+0x14), seed (+0x20/+0x24), path pointer (+0x2C) and flag word (+0xC4); the unit path's x (+0x02, u16), y (+0x06,
u16) and room (+0x1C); the target's type (+0x00), guid (+0x0C) and path pointer (+0x2C), that path's x and y (u16 at
+0x02/+0x06) and the static-unit words +0x0C/+0x10; the monster data's AI control pointer (+0x28); the AI control's
state (+0x00), +0x14, +0x18, +0x1C and +0x20 (the parameter record pointer, 0 or a record with kind +0x08 and the
words +0x0C/+0x10); the AiCtx (+0x00 ctl, +0x08 target, +0x14 distance, +0x18 melee, +0x1C MonStats record, +0x20
MonStats2 record); the MonStats record's +0x3E word, aip block (+0x56..+0x85), Skill1..3 (+0x170..+0x175) and
Sk1..3mode (+0x180..+0x182); the DataTables pointer (0x00744304) and its MonStats count (+0xA80). Every callee the
function reaches is an observed boundary, except RNG_Range (0x0045C390), RNG_RangePow2 (0x00472210), the position
getters 0x0045ADF0/0x0045AE20 with 0x006488C0/0x00648900, sub_00620BB0_UnitGetRoom with 0x00648A80 and
sub_0058EE80_AiParamsHead, which run on the declared image. The claim per case: the first boundary reached, its call
site (the return address), the registers and stack arguments the callee takes, the unit seed, the AI control's
+0x14/+0x18/+0x1C and the unit's +0xC4 at the boundary, and where a pointer argument addresses the frame, the words
it addresses.

Families (function, row):
  spawner  0x005E0160 row 82 InvisoSpawner     nest     0x005E0260 row 83 MosquitoNest
  priest   0x005E0490 row 85 HighPriest        mega     0x005E0C80 row 89 Megademon
  arcane   0x005E0F60 row 93 ArcaneTower       turret   0x005E0980 row 94 DesertTurret
  javelin  0x005E1080 row 95 PantherJavelin    blowgun  0x005E1250 row 96 FetishBlowgun
  spirit   0x005E3840 row 97 Spirit            smith    0x005E3890 row 98 Smith
  stower   0x005E1860 row 113 SiegeTower       horde    0x005E1540 row 114 ReanimatedHorde
  sbeast   0x005E1900 row 115 SiegeBeast
The `entry` families (ENTRY below) reach their first callee before any test: their claim is that call's site and
arguments.

Controls: `le` compares each draw with `<=` instead of `<`; `d0` reads every aip from the Normal column; `cmp`
switches the strictness of every compare that is not a draw (`<` and `<=`, `>` and `>=`); `u16` reads Skill1..3 as
unsigned words in their sign tests; `site` expects each call site one byte later. Each must fail every case it
separates. The `EDGES` line under each family counts, per compare, the cases that meet it at equality (the only cases
in which a strictness control can separate that compare); a compare missing from it has no control in the run.

Not covered (ADR-0021): every callee at or after a boundary (the commands, the move helpers, the searches and their
callbacks, the skill lookups, the spawn helpers, the owner lookup) and so every branch that a boundary call's result
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
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r52h", "emu")

MUL = 0x6AC690C5
GAME = 0x12000000
UNIT = 0x12100000
UPATH = 0x12200000
ROOM = 0x12300000
TARGET = 0x12400000
MDATA = 0x12500000
MREC = 0x12600000
CTX = 0x12700000
CTL = 0x12800000
MS2 = 0x12900000
DTBL = 0x12A00000
TPATH = 0x12B00000
PARAM = 0x12F00000
G_DATATABLES = 0x00744304
STK_LO = 0x7FEFFC00
STK_LEN = 1040              # to 0x7FF00010: the frame, the return address and the ctx argument slot
EBP = 0x7FEFFFFC            # the think function's frame pointer (entry ESP 0x7FF00000, `push ebp; mov ebp,esp`)
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)
CORNER = ((-5, -5), (5, -5), (5, 5), (-5, 5))     # 0x006E337C, 8 bytes a row (objdump -s of .rdata)

SETMODEAT, IDLE, WALK, PATHOVR, T56, WALKSTOP, FINDHOSTILE, USESKILL, SETMODE = (
    0x005DDF90, 0x005DE080, 0x005DEC80, 0x005DE190, 0x005DF7D0, 0x005DEF80, 0x005DDC30, 0x005DEAD0, 0x005DDFC0)
SKILLFIND, HASSTATE, LIFEPCT, STEPAWAY, FINDUNIT, SEARCH, POP, OWNER, APPROACH, TOWARD, WRING, DIRPT, VARIANT, \
    CELLTEST, MISREC = (
        0x006439B0, 0x00639DF0, 0x00621F20, 0x005DEFE0, 0x00552F60, 0x005DD0B0, 0x0058ED10, 0x00552FD0, 0x005DC640,
        0x005DE6D0, 0x005DE200, 0x00621DC0, 0x0063EC70, 0x005FD350, 0x0046ACE0)
OTHER = (0x005DF530, 0x0054DC40, 0x005B2F20, 0x006442A0, 0x00639DB0, 0x005541B0, 0x0063EA40, 0x006259B0,
         0x004E6C70, 0x005E17E0, 0x00620C10, 0x0063E7A0, 0x005FD470, 0x00648AD0, 0x005DE0F0, 0x005DEFB0,
         0x005B0BD0, 0x00554010)
OBSERVE = tuple(sorted(set((SETMODEAT, IDLE, WALK, PATHOVR, T56, WALKSTOP, FINDHOSTILE, USESKILL, SETMODE,
                            SKILLFIND, HASSTATE, LIFEPCT, STEPAWAY, FINDUNIT, SEARCH, POP, OWNER, APPROACH, TOWARD,
                            WRING, DIRPT, VARIANT, CELLTEST, MISREC) + OTHER)))
RET = "ret"

FNS = {"spawner": 0x005E0160, "nest": 0x005E0260, "priest": 0x005E0490, "mega": 0x005E0C80, "arcane": 0x005E0F60,
       "turret": 0x005E0980, "javelin": 0x005E1080, "blowgun": 0x005E1250, "spirit": 0x005E3840,
       "smith": 0x005E3890, "stower": 0x005E1860, "horde": 0x005E1540, "sbeast": 0x005E1900}
FAMILIES = tuple(FNS)
ENTRY = ("mega", "javelin", "stower", "sbeast")
NCASES = 240


def u32(v):
    return v & 0xFFFFFFFF


def s32(v):
    v = u32(v)
    return v - (1 << 32) if v & 0x80000000 else v


def s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def hx32(v):
    return struct.pack("<I", u32(v)).hex()


def hx16(v):
    return struct.pack("<H", v & 0xFFFF).hex()


def step(s):
    t = s[0] * MUL + s[1]
    s[0], s[1] = t & 0xFFFFFFFF, (t >> 32) & 0xFFFFFFFF


# ------------------------------------------------------------------------------------------------- the models
class Hit(Exception):
    pass


class Env:
    """One case's inputs and the model's running state (the unit seed, the AI control's +0x14/+0x18/+0x1C, +0xC4)."""

    def __init__(self, inp, neg=None):
        self.i, self.neg = inp, neg
        self.seed = list(inp["seed"])
        self.c14, self.c18, self.c1c = inp["ctl14"], inp["ctl18"], inp["ctl1c"]
        self.c4 = inp["c4"]
        self.eq = set()                     # the compares this case met at equality (the cases a control can separate)

    def aip(self, k):
        d = 0 if self.neg == "d0" else self.i["diff"]
        return s16(self.i["aip"][k - 1][d])

    def draw(self):                         # an inline step, then the low word mod 100 (unsigned)
        step(self.seed)
        return self.seed[0] % 100

    def rng(self, n):                       # RNG_Range(seed, n), n >= 1 here
        step(self.seed)
        return self.seed[0] % n

    def _cmp(self, d, c, edge):
        if d == c:
            self.eq.add(edge)
        return d <= c if self.neg == "le" else d < c

    def chance(self, k, edge=None):         # inline draw < aipK (le: <=)
        return self._cmp(self.draw(), self.aip(k), edge or "draw<aip%d" % k)

    def rchance(self, k):                   # RNG_Range(seed, 100) < aipK
        return self._cmp(self.rng(100), self.aip(k), "Range<aip%d" % k)

    def chance_c(self, c):                  # inline draw < constant
        return self._cmp(self.draw(), c, "draw<%d" % c)

    def rchance_c(self, c):                 # RNG_Range(seed, 100) < constant
        return self._cmp(self.rng(100), c, "Range<%d" % c)

    def lt(self, a, b, edge):               # a non-draw a < b (cmp: <=)
        if a == b:
            self.eq.add(edge)
        return a <= b if self.neg == "cmp" else a < b

    def le(self, a, b, edge):               # a non-draw a <= b (cmp: <)
        if a == b:
            self.eq.add(edge)
        return a < b if self.neg == "cmp" else a <= b

    def sk(self, k):                        # MonStats SkillK, s16
        return s16(self.i["skill"][k - 1])

    def has(self, k):                       # the sign test `SkillK >= 0` (u16: always)
        return True if self.neg == "u16" else self.sk(k) >= 0

    def skm(self, k):
        return self.i["skmode"][k - 1]

    def tpos(self):                         # the position getters on the target (0x0045ADF0/0x0045AE20 shape)
        i = self.i
        if i["ttype"] in (2, 4, 5):
            return i["tsx"], i["tsy"]
        if i["tpnull"]:
            return 0, 0
        return i["tx"], i["ty"]

    def hit(self, fn, site, args, ecx=GAME, edx=UNIT, block=None):
        raise Hit((fn, site, ecx, edx, [u32(a) for a in args], list(self.seed), u32(self.c14), u32(self.c18),
                   u32(self.c1c), u32(self.c4), block))


def at(fn, site, args=(), ecx=GAME, edx=UNIT):
    def m(e):
        e.hit(fn, site, list(args), ecx=ecx, edx=edx)
    return m


def m_spawner(e):                                       # row 82, 0x005E0160
    i = e.i
    if e.c14 == 0:
        e.c18 = u32(e.aip(1))
    if e.le(i["dist"], e.aip(2), "dist<=aip2"):
        if e.le(s32(e.c18), 0, "v18<=0"):
            e.hit(SETMODE, 0x005E01B7, [0, 0, 0])
        if e.le(s32(e.c14), s32(i["frame"]), "v14<=T"):
            cls = 0x60 if i["mscount"] > 0x60 else -1
            e.hit(VARIANT, 0x005E01F6, [ROOM, cls], ecx=None, edx=None)
    e.hit(IDLE, 0x005E0257, [15])


def m_nest(e):                                          # row 83, 0x005E0260
    i = e.i
    if e.le(i["dist"], e.aip(2), "dist<=aip2"):
        if e.lt(e.aip(1), s32(e.c18), "v18>aip1"):
            e.c4 |= 0x20000
            e.hit(SETMODE, 0x005E02BA, [0, 0, 0])
        if e.has(1) and e.lt(s32(e.c14), s32(i["frame"]), "T>v14"):
            cls = 0x14E if i["mscount"] > 0x14E else -1
            e.hit(CELLTEST, 0x005E0327, [i["ux"], i["uy"], 0], ecx=cls, edx=ROOM)
    e.hit(IDLE, 0x005E0379, [25])


def m_priest(e):                                        # row 85, 0x005E0490
    i, t = e.i, TARGET
    T, dist = s32(i["frame"]), i["dist"]
    if e.c14 == 0:
        if i["melee"]:
            if e.chance(1):
                e.c14 = 1
                e.hit(SETMODEAT, 0x005E0521, [4, t])
            e.hit(STEPAWAY, 0x005E053C, [t, 6, 1])
        if e.has(2) and e.lt(s32(e.c18), T, "T>v18") and e.rchance(2):
            e.hit(SEARCH, 0x005E05A5, [EBP - 0x48, 0x005E0430, 1], block=(EBP - 0x48, [0, 0x4B, 0x9C4]))
        if e.has(1) and e.lt(s32(e.c18), T, "T>v18") and e.lt(dist, e.aip(8), "dist<aip8") and e.rchance(4):
            step(e.seed)
            k = e.seed[0] & 3                           # RNG_RangePow2(seed, 4)
            x, y = e.tpos()
            e.hit(USESKILL, 0x005E068C, [e.skm(1), e.sk(1), t, x + CORNER[k][0], y + CORNER[k][1]])
        if e.lt(0, e.aip(5), "aip5>0") and s16(i["m3e"]) > 0:
            e.hit(MISREC, 0x005E06C1, [], ecx=s16(i["m3e"]), edx=None)
        if e.chance_c(80):
            if e.le(dist, e.aip(8), "dist<=aip8"):
                e.hit(T56, 0x005E0775, [t, 3, 0])
            e.hit(WALKSTOP, 0x005E075C, [t, 6])
    e.c14 = 1
    if i["melee"]:
        if e.chance(7):
            e.hit(SETMODEAT, 0x005E06FD, [8, t])
        if e.chance(6):
            e.hit(STEPAWAY, 0x005E0823, [t, 6, 1])
        if e.rchance_c(90):
            e.hit(SETMODEAT, 0x005E0857, [4, t])
        e.hit(IDLE, 0x005E086A, [10])
    if e.lt(dist, 6, "dist<6") and e.chance(7):
        e.hit(SETMODEAT, 0x005E06FD, [8, t])
    if e.chance(6):
        e.c14 = 0
        e.hit(IDLE, 0x005E0912, [10])
    if e.chance_c(70):
        e.hit(WALK, 0x005E0956, [t, 7])
    e.hit(WRING, 0x005E0968, [12])


def m_mega(e):                                          # row 89, 0x005E0C80
    if e.has(1):
        e.hit(SKILLFIND, 0x005E0CC8, [u32(-1)], ecx=UNIT, edx=e.sk(1))
    e.hit(HASSTATE, 0x005E0CF6, [UNIT, 12], ecx=None, edx=None)


def m_arcane(e):                                        # row 93, 0x005E0F60
    i, t = e.i, TARGET
    if e.c18 == 0:
        e.c18 = u32(e.aip(1))
    if e.lt(s32(i["frame"]), s32(e.c1c), "T<v1c"):
        e.hit(IDLE, 0x005E0F99, [10])
    if e.has(1) and e.c14 == 0:
        e.hit(USESKILL, 0x005E0FCA, [e.skm(1), e.sk(1), t, 0, 0])
    e.hit(SETMODEAT, 0x005E1023, [4, t])


def m_turret(e):                                        # row 94, 0x005E0980
    i = e.i
    if e.has(1) and e.c14 == 0:
        e.hit(USESKILL, 0x005E09D3, [e.skm(1), e.sk(1), 0, 0, 0])
    if e.lt(s32(i["frame"]), s32(e.c14), "T<v14"):
        e.hit(IDLE, 0x005E0A03, [10])
    if e.lt(e.aip(4), i["dist"], "dist>aip4"):
        if e.lt(0, s32(e.c18), "v18>0"):
            e.c18 = u32(e.c18 - 1)
        e.hit(IDLE, 0x005E0A30, [15])
    x, y = e.tpos()
    e.hit(DIRPT, 0x005E0B0C, [UNIT, x, y], ecx=None, edx=None)


def m_javelin(e):                                       # row 95, 0x005E1080
    e.hit(FINDHOSTILE, 0x005E10AE, [EBP + 8, 0], block=(EBP + 8, [e.i["dist"]]))


def m_blowgun(e):                                       # row 96, 0x005E1250
    i = e.i
    if i["param"] is not None:
        kind, w1, w2 = i["param"]
        if kind == 1:
            e.hit(FINDUNIT, 0x005E12A0, [w1], edx=w2)
        if kind == 14:
            e.hit(FINDUNIT, 0x005E12E1, [w1], edx=w2)
        e.hit(POP, 0x005E1327, [])
    if i["melee"] == 0:
        if e.lt(e.aip(1), i["dist"], "dist>aip1"):
            e.hit(PATHOVR, 0x005E134D, [0x32, 0], ecx=UNIT, edx=0)
        go = e.lt(i["dist"], 6, "dist<6")
    else:
        go = True
    if go and e.chance(2):
        e.c14 = 2
    e.hit(FINDHOSTILE, 0x005E13C2, [EBP - 0x18, 0])


def m_spirit(e):                                        # row 97, 0x005E3840
    if e.c14 != 0:
        e.hit(IDLE, 0x005E385D, [50])
    if e.i["melee"]:
        e.c14 = 1
        e.hit(SETMODEAT, 0x005E3876, [4, TARGET])
    e.hit(IDLE, 0x005E3883, [10])


def m_smith(e):                                         # row 98, 0x005E3890
    if e.i["melee"]:
        e.hit(SETMODEAT, 0x005E38AE, [4, TARGET])
    e.hit(LIFEPCT, 0x005E38BB, [UNIT], ecx=None, edx=None)


def m_horde(e):                                         # row 114, 0x005E1540
    t = TARGET
    e.c4 |= 0xE
    if e.i["melee"]:
        if e.chance(1):
            e.hit(SETMODEAT, 0x005E15C4, [4, t])
        e.hit(IDLE, 0x005E15DD, [e.aip(2)])
    if e.has(2):
        e.hit(APPROACH, 0x005E15FA, [], ecx=UNIT, edx=t)
    if e.chance(5):
        e.hit(WALK, 0x005E16A7, [t, 0])
    if e.chance(6):
        e.hit(TOWARD, 0x005E16FA, [t, 4, 0])
    e.hit(IDLE, 0x005E1713, [e.aip(7)])


MODELS = {"spawner": m_spawner, "nest": m_nest, "priest": m_priest, "mega": m_mega, "arcane": m_arcane,
          "turret": m_turret, "javelin": m_javelin, "blowgun": m_blowgun, "spirit": m_spirit, "smith": m_smith,
          "stower": at(OWNER, 0x005E1880), "horde": m_horde, "sbeast": at(OWNER, 0x005E1930)}
CONTROLS = ("le", "d0", "cmp", "u16")


def run_model(inp, neg=None, edges=None):
    e = Env(inp, neg)
    try:
        MODELS[inp["fam"]](e)
    except Hit as h:
        if edges is not None:
            for x in e.eq:
                edges[x] = edges.get(x, 0) + 1
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
            col = []
            for _ in range(3):
                col.append(rnd.choice(ds + ds + [rnd.randrange(0, 101), rnd.randrange(-3, 111), 0, 1, 2, 5, 6, 12,
                                                 20, 50, 80, -1]))
            aip.append(col)
        diff = k % 3
        frame = rnd.randrange(100, 100000)
        a = [aip[j][diff] for j in range(8)]
        inp = {
            "fam": fam, "seed": seed, "diff": diff, "aip": aip, "frame": frame,
            "melee": rnd.randrange(2),
            "dist": max(0, rnd.choice([0, 1, 5, 6, 7, 10, 20, rnd.randrange(0, 60)]
                                      + [a[j] + rnd.choice((-1, 0, 1)) for j in (0, 1, 3, 7)])),
            "ctl14": rnd.choice([0, 0, 1, 2, -1, u32(frame + rnd.choice((-1, 0, 1)))]),
            "ctl18": rnd.choice([0, 0, 1, 2, 7, -1, u32(frame + rnd.choice((-1, 0, 1)))]),
            "ctl1c": rnd.choice([0, 0, 1, -1, u32(frame + rnd.choice((-1, 0, 1)))]),
            "c4": rnd.choice([0, 0x20000, rnd.randrange(1 << 32)]),
            "skill": [rnd.choice([-1, 0x8000, 0xFFFE, 0x7FFF, 0, rnd.randrange(0, 400), rnd.randrange(0, 400)])
                      for _ in range(3)],
            "skmode": [rnd.randrange(16) for _ in range(3)],
            "ux": rnd.randrange(1 << 16), "uy": rnd.randrange(1 << 16),
            "tx": rnd.randrange(1 << 16), "ty": rnd.randrange(1 << 16),
            "tsx": rnd.randrange(1 << 31), "tsy": rnd.randrange(1 << 31),
            "ttype": rnd.choice([0, 1, 1, 1, 2, 3, 4, 5]), "tguid": rnd.randrange(1 << 32),
            "state": rnd.randrange(18), "cls": rnd.randrange(0x2E0),
            "mscount": rnd.choice([0x2E0, 0x2E0, 0x60, 0x61, 0x14E, 0x14F]),
            "m3e": rnd.choice([0, -1, 1, 5, 300, 0x8000]),
            "param": None,
        }
        inp["tpnull"] = int(inp["ttype"] not in (2, 4, 5) and rnd.randrange(6) == 0)
        if fam == "spawner":
            inp["ctl14"] = rnd.choice([0, 0, 1, -1, u32(frame + rnd.choice((-1, 0, 1))), frame])
            inp["ctl18"] = rnd.choice([0, 1, 2, -1, 5])
            inp["dist"] = max(0, a[1] + rnd.choice((-1, 0, 1, -5)))
        if fam == "nest":
            inp["ctl18"] = u32(a[0] + rnd.choice((-1, 0, 1, -5)))
            inp["ctl14"] = u32(frame + rnd.choice((-1, 0, 1, -100, 100)))
            inp["dist"] = max(0, a[1] + rnd.choice((-1, 0, 1, -5)))
        if fam == "priest":                      # mostly the unarmed first pass, to reach the later draws
            inp["ctl14"] = rnd.choice([0, 0, 0, 1])
            inp["melee"] = rnd.choice([0, 0, 0, 1])
            inp["m3e"] = rnd.choice([0, 0, 0, inp["m3e"]])
            if rnd.randrange(2):
                inp["skill"][1] = -1
            if rnd.randrange(6) == 0:              # the corner skill: no Skill2, Skill1 set, inside aip8, aip4 100
                inp["ctl14"], inp["melee"] = 0, 0
                inp["skill"][1], inp["skill"][0] = -1, rnd.randrange(0, 400)
                inp["ctl18"] = u32(frame - rnd.choice((1, 100)))
                aip[7][diff] = max(inp["dist"] + 1, aip[7][diff])
                aip[3][diff] = 100
            elif rnd.randrange(7) == 0:            # the armed pass to its last idle: two misses, a third draw >= 90
                while first_draws(seed, 3)[2] < 90:
                    seed = (rnd.randrange(1 << 32), rnd.randrange(1 << 32))
                inp["seed"] = seed
                inp["ctl14"], inp["melee"] = 1, 1
                aip[5][diff] = aip[6][diff] = 0
            inp["ctl18"] = u32(frame + rnd.choice((-1, 0, 1, -100, -100, 100)))
            inp["dist"] = max(0, rnd.choice([a[7] + rnd.choice((-1, 0, 1)), 5, 6, 7, rnd.randrange(0, 40)]))
        if fam == "turret":
            inp["ctl14"] = rnd.choice([0, 0, u32(frame + rnd.choice((-1, 0, 1, -100)))])
            inp["dist"] = max(0, a[3] + rnd.choice((-1, 0, 1, -5)))
        if fam == "arcane":
            inp["ctl1c"] = u32(frame + rnd.choice((-1, 0, 1, -100, 100)))
            inp["ctl14"] = rnd.choice([0, 1])
            inp["ctl18"] = rnd.choice([0, 1, 2, -1])
        if fam == "blowgun":
            p = rnd.choice([None, None, None, None, 1, 14, 0, 2])
            if p is not None:
                inp["param"] = (p, rnd.randrange(1 << 32), rnd.randrange(1 << 32))
            inp["dist"] = max(0, rnd.choice([a[0] + rnd.choice((-1, 0, 1)), 5, 6, 7, rnd.randrange(0, 40)]))
        sk = "".join(hx16(s) for s in inp["skill"])
        lines = [
            "w %08x %s" % (GAME + 0x6D, "%02x" % diff),
            "w %08x %s" % (GAME + 0xA8, hx32(frame)),
            "w %08x %s" % (UNIT, hx32(1) + hx32(inp["cls"])),
            "w %08x %s" % (UNIT + 0x10, hx32(1) + hx32(MDATA)),
            "w %08x %s%s" % (UNIT + 0x20, hx32(seed[0]), hx32(seed[1])),
            "w %08x %s" % (UNIT + 0x2C, hx32(UPATH)),
            "w %08x %s" % (UNIT + 0xC4, hx32(inp["c4"])),
            "w %08x %s" % (UPATH + 0x02, hx16(inp["ux"])), "w %08x %s" % (UPATH + 0x06, hx16(inp["uy"])),
            "w %08x %s" % (UPATH + 0x1C, hx32(ROOM)),
            "w %08x %s" % (TARGET, hx32(inp["ttype"])), "w %08x %s" % (TARGET + 0x0C, hx32(inp["tguid"])),
            "w %08x %s" % (TARGET + 0x2C, hx32(0 if inp["tpnull"] else TPATH)),
            "w %08x %s" % (TPATH + 0x02, hx16(inp["tx"])), "w %08x %s" % (TPATH + 0x06, hx16(inp["ty"])),
            "w %08x %s" % (TPATH + 0x0C, hx32(inp["tsx"]) + hx32(inp["tsy"])),
            "w %08x %s" % (MDATA + 0x28, hx32(CTL)),
            "w %08x %s" % (CTL, hx32(inp["state"])),
            "w %08x %s%s%s%s" % (CTL + 0x14, hx32(inp["ctl14"]), hx32(inp["ctl18"]), hx32(inp["ctl1c"]),
                                 hx32(0 if inp["param"] is None else PARAM)),
            "w %08x %s" % (CTX, hx32(CTL) + hx32(0) + hx32(TARGET) + hx32(0) + hx32(0)
                           + hx32(inp["dist"]) + hx32(inp["melee"]) + hx32(MREC) + hx32(MS2)),
            "w %08x %s" % (MREC + 0x3E, hx16(inp["m3e"])),
            "w %08x %s" % (MREC + 0x56, "".join(hx16(aip[j][d]) for j in range(8) for d in range(3))),
            "w %08x %s" % (MREC + 0x170, sk + hx16(-1) + "00" * 8),
            "w %08x %s" % (MREC + 0x180, "".join("%02x" % m for m in inp["skmode"]) + "00" * 5),
            "w %08x %s" % (G_DATATABLES, hx32(DTBL)),
            "w %08x %s" % (DTBL + 0xA80, hx32(inp["mscount"])),
        ]
        if inp["param"] is not None:
            lines.append("w %08x %s" % (PARAM + 0x08, "".join(hx32(v) for v in inp["param"])))
        lines += [
            "d %08x %d" % (STK_LO, STK_LEN), "d %08x 8" % (UNIT + 0x20), "d %08x 12" % (CTL + 0x14),
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
        cases, meta, mem = gen_family(fam, random.Random("r52h-" + fam))
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
    fn, site, ecx, edx, args, seed, c14, c18, c1c, c4, block = want
    if c.get("obs") != fn:
        return False
    gseed = list(struct.unpack("<II", c["dumps"][UNIT + 0x20]))
    g14, g18, g1c = struct.unpack("<III", c["dumps"][CTL + 0x14])
    gc4 = struct.unpack("<I", c["dumps"][UNIT + 0xC4])[0]
    ok = gseed == seed and g14 == c14 and g18 == c18 and g1c == c1c and gc4 == c4
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
    _, meta, _ = gen_family(fam, random.Random("r52h-" + fam))
    calls, traced = read_out(os.path.join(d, fam + ".out"))
    bad, match, stops = [], 0, 0
    ctl = {n: [0, 0] for n in CONTROLS}
    site_pass = 0
    bounds = {}
    ndraws = 0
    edges = {}
    kseen = set()
    if len(calls) != len(meta):
        bad.append("case count %d != %d" % (len(calls), len(meta)))
    for c, inp in zip(calls, meta):
        if "stop" in c:
            stops += 1
            bad.append("case %d STOP %s" % (c["n"], c["stop"]))
            continue
        want = run_model(inp, edges=edges)
        ok = matches(c, want)
        match += ok
        if not ok:
            bad.append("case %d mismatch want=%s@%s obs=%s args=%s" % (
                c["n"], want[0] if want[0] == RET else hex(want[0]), hex(want[1]),
                c.get("obs") if c.get("obs") == RET else hex(c.get("obs", 0)), c.get("args", b"")[:24].hex()))
        key = RET if want[0] == RET else "%x@%x" % (want[0], want[1])
        bounds[key] = bounds.get(key, 0) + 1
        ndraws += want[5] != list(inp["seed"])
        if want[0] == USESKILL and want[1] == 0x005E068C:   # row 85's corner pick: which table row the case read
            x, y = Env(inp).tpos()
            kseen.add(CORNER.index((s32(want[4][3] - x), s32(want[4][4] - y))))
        site_pass += matches(c, want, site_shift=1) if want[0] != RET else 0
        for n in ctl:
            nw = run_model(inp, neg=n)
            if nw != want:
                ctl[n][0] += 1
                ctl[n][1] += matches(c, nw)
    # The one image read a model accounts for: row 85's corner table 0x006E337C (dx at 0x005E0656, dy at
    # 0x005E0665), one row per corner the cases picked. Every other traced access is left in `traced`.
    expect = set()
    for k in kseen:
        expect.add("R 005e0656 %08x 4" % (0x006E337C + 8 * k))
        expect.add("R 005e0665 %08x 4" % (0x006E3380 + 8 * k))
    seen = set(" ".join(x.split()[:4]) for x in traced)
    accounted = len(seen & expect)
    if expect - seen:
        bad.append("corner reads missing %s" % sorted(expect - seen))
    traced = [x for x in traced if " ".join(x.split()[:4]) not in expect]
    line = ("AI52H %s cases=%d match=%d bad=%d stopped=%d traced=%d accounted=%d drew=%d " % (
        fam, len(meta), match, len(bad), stops, len(traced), accounted, ndraws)
        + " ".join("%s_separating=%d %s_passed=%d" % (n, ctl[n][0], n, ctl[n][1]) for n in CONTROLS)
        + " site_control_passed=%d boundaries=%d" % (site_pass, len(bounds)))
    return line, bad[:20], traced[:20], bounds, ctl, edges


def cmd_check(d):
    allok = True
    tot = [0, 0]
    for fam in FAMILIES:
        line, bad, traced, bounds, ctl, edges = check_family(fam, d)
        print(line)
        print("  SITES " + " ".join("%s:%d" % kv for kv in sorted(bounds.items())))
        print("  EDGES " + " ".join("%s:%d" % kv for kv in sorted(edges.items())))
        for b in bad:
            print("  BAD", b)
        for t in traced:
            print("  TRACED", t)
        if bad or traced or any(ctl[n][1] for n in ctl) or "site_control_passed=0" not in line:
            allok = False
        tot[0] += NCASES
        tot[1] += int(line.split("match=")[1].split()[0])
    print("AI52H total cases=%d match=%d" % tuple(tot))
    print("AI52H result=%s" % ("ok" if allok else "FAIL"))


def cmd_manifest(d, write):
    rows = []
    for fam in FAMILIES:
        for ext in ("cases", "mem", "out", "err"):
            p = os.path.join(d, "%s.%s" % (fam, ext))
            if os.path.exists(p):
                rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.basename(p)))
    for extra in ("check.txt", "ai_cat_emu8.py.rev"):
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

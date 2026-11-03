#!/usr/bin/env python3
"""Plan 0052 phase 1.2, catalogue batch 4 (pool-D, `lane/r52e`): the think functions of AI rows 64-80, 87 and 92
(and row 65's alt) run under Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java
and compared with the models below. No game run, no slot. Same method as tools/ai_cat_emu3.py (batch 3), with three
additions: a function return is an outcome of its own (row 66), the trap-arrow kind helper 0x005FB650 runs on the
declared image with its region word compared, and a fourth control, `cmp`, for the compares that are not draws.

    python3 -I tools/ai_cat_emu4.py cases [--dir D]      write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/ai_cat_emu4.py check [--dir D]      compare every D/<family>.out with its model, account for
                                                         every traced access, run the negative and site controls
    python3 -I tools/ai_cat_emu4.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r52e/emu. Every case draw comes from random.Random("r52e-<family>"), so `cases` regenerates
identical files. The development run (emu/dev-1) used the writer before the trap arrows' tuning below (its copy,
emu/dev-1/ai_cat_emu4.py.rev, checks it); the models are the same in both runs.

Each family runs one think function `(ECX game, EDX unit; ctx)` (ai/0005) on a declared image: the game's difficulty
byte (+0x6D), frame (+0xA8) and, for the trap arrows, one region pointer at +0xF0 + 4*level; the unit's type (+0x00,
1), class (+0x04), mode (+0x10), monster data pointer (+0x14), seed (+0x20/+0x24), path pointer (+0x2C) and flag
word (+0xC4); the path's x (+0x02, u16), y (+0x06, u16) and room (+0x1C); the room's +0x10 (the DRLG room), that
room's +0x58 (the level) and the level's +0x1D0 (its id); the region's +0x2D4 word; the target's type (+0x00), guid
(+0x0C) and path (+0x2C) with that path's x and y; the monster data's AI control pointer (+0x28) and +0x54 word; the
AI control's state (+0x00), +0x14, +0x18, +0x1C and +0x20 (no parameter record); the AiCtx (+0x00 ctl, +0x08 target,
+0x14 distance, +0x18 melee, +0x1C MonStats record, +0x20 MonStats2 record); the MonStats record's aip block
(+0x56..+0x85), Skill1..3 (+0x170..+0x175) and Sk1..3mode (+0x180..+0x182); the DataTables pointer (0x00744304) and
its MonStats count (+0xA80). Every callee the function reaches is an observed boundary, except RNG_Range
(0x0045C390), RNG_RandLoHi (0x004BC500), sub_005DD2B0_AiMonState3or19 with its callee 0x005734E0, the position
getters 0x0045ADF0/0x0045AE20 and sub_00620870_UnitGetPos with 0x006488C0/0x00648900, sub_00620BB0_UnitGetRoom with
0x00648A80, sub_0061A1B0_RoomGetLevelId with 0x0066BAB0, sub_00547BB0_MonRegionGet and the trap-arrow kind helper
0x005FB650, which run on the declared image. The claim per case: the first boundary reached (or the return), its call
site (the return address), the registers and stack arguments the callee takes, the unit seed, the AI control's
+0x14/+0x18/+0x1C, the unit's +0xC4 and the region's +0x2D4 at the boundary, and where a pointer argument addresses
the frame, the words it addresses.

Families (function, row):
  skmage    0x005F96C0 row 64 SkeletonMage      fetish    0x005F9A80 row 65 FetishShaman
  fetishalt 0x005F9950 row 65's alt             queen     0x005F9CF0 row 66 SandMaggotQueen
  vmother   0x005FA010 row 68 VileMother        vdog      0x005FA280 row 69 VileDog
  fmage     0x005FA380 row 70 FingerMage        regurg    0x005FA710 row 71 Regurgitator
  dknight   0x005FAA90 row 72 DoomKnight        aknight   0x005FAB80 row 73 AbyssKnight
  oknight   0x005FAF00 row 74 OblivionKnight    quill     0x005FB2A0 row 75 QuillMother
  ehole     0x005FB410 row 76 EvilHole          tmissile  0x005FB5B0 row 77 Trap-Missile
  trarrow   0x005FB6C0 row 78 Trap-RightArrow   tlarrow   0x005FB7E0 row 79 Trap-LeftArrow
  tpoison   0x005FB900 row 80 Trap-Poison       tmelee    0x005FBA60 row 87 Trap-Melee
  tnova     0x005FB9B0 row 92 Trap-Nova
The six `entry` families (skmage, fetishalt, vmother, fmage, aknight, oknight) reach their first callee before any
test: their claim is that call's site and arguments (and the search block's words for oknight) only.

Controls: `le` compares each draw with `<=` instead of `<`; `d0` reads every aip from the Normal column; `cmp`
switches the strictness of every compare that is not a draw (`<` and `<=`, `>` and `>=`); `r4` makes the trap-arrow
kind draw `low mod 4` for `low mod 3`; `site` expects each call site one byte later. Each must fail every case it
separates. The `EDGES` line under each family counts, per compare, the cases that meet it at equality (the only cases
in which a strictness control can separate that compare); a compare missing from it has no control in the run.

Not covered (ADR-0021): every callee at or after a boundary (the commands, the move helpers, the path override, the
hostile search, the unit searches and their callbacks, the skill-level and skill-target tests, the state tests, the
spawns, the life percent, the class chain) and so every branch that a boundary call's result decides. Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r52e", "emu")

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
DROOM = 0x12C00000
LEVEL = 0x12D00000
REGION = 0x12E00000
G_DATATABLES = 0x00744304
STK_LO = 0x7FEFFC00
STK_LEN = 1040              # to 0x7FF00010: the frame, the return address and the ctx argument slot
EBP = 0x7FEFFFFC            # the think function's frame pointer (entry ESP 0x7FF00000, `push ebp; mov ebp,esp`)
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)

SETMODEAT, IDLE, WALK, PATHOVR, T56, WALKSTOP, DELAY, FINDHOSTILE, USESKILL, SETMODE = (
    0x005DDF90, 0x005DE080, 0x005DEC80, 0x005DE190, 0x005DF7D0, 0x005DEF80, 0x005DE0F0, 0x005DDC30, 0x005DEAD0,
    0x005DDFC0)
SKILLFIND, HASSTATE, MOVETOPT, SPAWNBASE, CHAINPOS, LIFEPCT, STEPAWAY, FINDUNIT, SEARCH, WALK13, HELPBLK = (
    0x006439B0, 0x00639DF0, 0x005DE440, 0x0063EFA0, 0x006510C0, 0x00621F20, 0x005DEFE0, 0x00552F60, 0x005DD0B0,
    0x005DED40, 0x0058F730)
OTHER = (0x005DE200, 0x005DEFB0, 0x005DE6D0, 0x005DED20, 0x005DF530, 0x005DE000, 0x005FD470, 0x0058F0D0,
         0x006442A0, 0x00639DB0, 0x005B0E00, 0x005F9E30, 0x0054DA60, 0x006259B0, 0x005B0BD0, 0x00463740,
         0x005B2F20, 0x00621E40, 0x005FD350, 0x00621DC0, 0x00649070, 0x00553540, 0x0057CCB0, 0x005417D0)
OBSERVE = tuple(sorted(set((SETMODEAT, IDLE, WALK, PATHOVR, T56, WALKSTOP, DELAY, FINDHOSTILE, USESKILL, SETMODE,
                            SKILLFIND, HASSTATE, MOVETOPT, SPAWNBASE, CHAINPOS, LIFEPCT, STEPAWAY, FINDUNIT, SEARCH,
                            WALK13, HELPBLK) + OTHER)))
RET = "ret"

FNS = {"skmage": 0x005F96C0, "fetish": 0x005F9A80, "fetishalt": 0x005F9950, "queen": 0x005F9CF0,
       "vmother": 0x005FA010, "vdog": 0x005FA280, "fmage": 0x005FA380, "regurg": 0x005FA710, "dknight": 0x005FAA90,
       "aknight": 0x005FAB80, "oknight": 0x005FAF00, "quill": 0x005FB2A0, "ehole": 0x005FB410,
       "tmissile": 0x005FB5B0, "trarrow": 0x005FB6C0, "tlarrow": 0x005FB7E0, "tpoison": 0x005FB900,
       "tmelee": 0x005FBA60, "tnova": 0x005FB9B0}
FAMILIES = tuple(FNS)
ENTRY = ("skmage", "fetishalt", "vmother", "fmage", "aknight", "oknight")
NCASES = 240


def u32(v):
    return v & 0xFFFFFFFF


def s32(v):
    v = u32(v)
    return v - (1 << 32) if v & 0x80000000 else v


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
    """One case's inputs and the model's running state (the unit seed, the AI control's +0x14/+0x18/+0x1C, +0xC4,
    the region's +0x2D4)."""

    def __init__(self, inp, neg=None):
        self.i, self.neg = inp, neg
        self.seed = list(inp["seed"])
        self.c14, self.c18, self.c1c = inp["ctl14"], inp["ctl18"], inp["ctl1c"]
        self.c4 = inp["c4"]
        self.rk = inp["rk"]
        self.eq = set()                     # the compares this case met at equality (the cases a control can separate)

    def aip(self, k):
        d = 0 if self.neg == "d0" else self.i["diff"]
        return self.i["aip"][k - 1][d]

    def draw(self):
        step(self.seed)
        return self.seed[0] % 100

    def rng(self, n):                       # RNG_Range: n < 1 gives 0 without a step
        if s32(n) < 1:
            return 0
        step(self.seed)
        return self.seed[0] % u32(n)

    def chance(self, k):                    # draw < aipK (le: <=)
        d = self.draw()
        if d == self.aip(k):
            self.eq.add("draw<aip%d" % k)
        return d <= self.aip(k) if self.neg == "le" else d < self.aip(k)

    def rchance(self, k):                   # the same through RNG_Range(seed, 100)
        d = self.rng(100)
        if d == self.aip(k):
            self.eq.add("Range<aip%d" % k)
        return d <= self.aip(k) if self.neg == "le" else d < self.aip(k)

    def lt(self, a, b, edge):               # a non-draw a < b (cmp: <=)
        if a == b:
            self.eq.add(edge)
        return a <= b if self.neg == "cmp" else a < b

    def le(self, a, b, edge):               # a non-draw a <= b (cmp: <)
        if a == b:
            self.eq.add(edge)
        return a < b if self.neg == "cmp" else a <= b

    def st(self):
        return self.i["m54"] in (3, 19)

    def sk(self, k):
        return self.i["skill"][k - 1]

    def skm(self, k):
        return self.i["skmode"][k - 1]

    def hit(self, fn, site, args, ecx=GAME, edx=UNIT, block=None):
        raise Hit((fn, site, ecx, edx, [u32(a) for a in args], list(self.seed), u32(self.c14), u32(self.c18),
                   u32(self.c1c), u32(self.c4), u32(self.rk), block))

    def ret(self):
        self.hit(RET, 0, [], ecx=None, edx=None)


def m_skmage(e):                                        # row 64, 0x005F96C0
    e.hit(FINDHOSTILE, 0x005F96EE, [EBP + 8, 0], block=(EBP + 8, [e.i["dist"]]))


def m_fetish(e):                                        # row 65, 0x005F9A80
    if e.sk(1) >= 0:
        e.hit(SKILLFIND, 0x005F9AB7, [u32(-1)], ecx=UNIT, edx=e.sk(1))
    e.hit(HASSTATE, 0x005F9B50, [UNIT, 12], ecx=None, edx=None)


def m_fetishalt(e):                                     # row 65's alt, 0x005F9950
    e.hit(HASSTATE, 0x005F996A, [UNIT, 12], ecx=None, edx=None)


def m_queen(e):                                         # row 66, 0x005F9CF0
    i = e.i
    if e.c1c != 0:
        e.hit(IDLE, 0x005F9D22, [s32(e.aip(2) * 25)])
    if e.c18 == 0:
        if e.lt(s32(e.c14), e.aip(1), "v14<aip1"):
            e.hit(MOVETOPT, 0x005F9D62, [i["ux"], i["uy"], 8])
        e.ret()
    e.hit(SPAWNBASE, 0x005F9DAD, [UNIT, EBP - 0x10, EBP - 4, EBP + 8, EBP - 0xC, 0, 0x0058F710], ecx=None, edx=None)


def m_vmother(e):                                       # row 68, 0x005FA010
    e.hit(CHAINPOS, 0x005FA04A, [e.i["cls"], 0, 0], ecx=None, edx=None)


def m_vdog(e):                                          # row 69, 0x005FA280
    t = e.i["target"]
    if e.c14 == 0:
        e.c14 = 1
        e.hit(IDLE, 0x005FA2B2, [5])
    if e.i["melee"]:
        if e.chance(1):
            e.hit(SETMODEAT, 0x005FA306, [4, t])
        e.hit(IDLE, 0x005FA31C, [e.aip(2)])
    if e.chance(3):
        e.hit(WALK, 0x005FA362, [t, 7])
    e.hit(IDLE, 0x005FA374, [10])


def m_fmage(e):                                         # row 70, 0x005FA380
    e.hit(LIFEPCT, 0x005FA3B0, [UNIT], ecx=None, edx=None)


def m_regurg(e):                                        # row 71, 0x005FA710
    t, v = e.i["target"], s32(e.c14)
    if v == 5:
        e.hit(STEPAWAY, 0x005FA74A, [t, 16, 1])
    if v == 2:
        e.hit(FINDUNIT, 0x005FA771, [e.c18], edx=1)
    if v == 3:
        e.hit(FINDUNIT, 0x005FA80D, [e.c18], edx=1)
    if v == 4:
        if e.i["melee"] == 0:
            e.hit(SETMODEAT, 0x005FA886, [5, t])
        e.hit(STEPAWAY, 0x005FA8A2, [t, 8, 1])
    r = e.aip(6)
    e.hit(SEARCH, 0x005FA8D7, [EBP - 0x34, 0x005FA690, 1], block=(EBP - 0x34, [0, s32(r * r)]))


def m_dknight(e):                                       # row 72, 0x005FAA90
    t = e.i["target"]
    if e.i["melee"] == 0:
        if e.chance(3):
            e.hit(WALK13, 0x005FAB58, [t, 7])
        e.hit(IDLE, 0x005FAB6E, [e.aip(4)])
    if e.chance(1):
        e.hit(SETMODEAT, 0x005FAAF7, [4, t])
    e.hit(IDLE, 0x005FAB0D, [e.aip(2)])


def m_aknight(e):                                       # row 73, 0x005FAB80
    e.hit(LIFEPCT, 0x005FABB4, [UNIT], ecx=None, edx=None)


def m_oknight(e):                                       # row 74, 0x005FAF00
    e.hit(SEARCH, 0x005FAF52, [EBP - 0x40, 0x005FAE40, 1],
          block=(EBP - 0x40, [0, 0, 0x9C4, 0x7FFFFFFF, 0x7FFFFFFF]))


def m_quill(e):                                         # row 75, 0x005FB2A0
    i, t = e.i, e.i["target"]
    if e.st():
        e.hit(HELPBLK, 0x005FB2FE, [EBP - 0x28], block=(EBP - 0x20, [1, i["ttype"], i["tguid"]]))
    if i["melee"] == 0:
        if e.chance(2):
            e.hit(WALK, 0x005FB3E6, [t, 7])
        e.hit(IDLE, 0x005FB3FC, [e.aip(4)])
    if e.chance(1):
        e.hit(SETMODEAT, 0x005FB37E, [4, t])
    e.hit(IDLE, 0x005FB394, [e.aip(3)])


def m_ehole(e):                                         # row 76, 0x005FB410
    i = e.i
    T = s32(i["frame"])
    if e.le(s32(e.c14), 0, "v14<=0"):
        e.c14 = u32(e.aip(2) + T)
        e.c18 = u32(e.aip(1))
    m = i["umode"]
    if m == 1:
        if e.lt(5, i["dist"], "dist>5"):
            e.hit(IDLE, 0x005FB473, [5])
        e.hit(SETMODE, 0x005FB487, [10, 0, 0])
    if m == 10:
        e.hit(SETMODE, 0x005FB487, [11, 0, 0])
    if m == 11 and e.lt(0, s32(e.c18), "v18>0"):
        if e.lt(s32(e.c14), T, "T>v14"):
            e.c14 = u32(e.aip(2) + T)
            e.hit(SPAWNBASE, 0x005FB4F6, [UNIT, EBP - 0x10, EBP - 4, EBP + 8, EBP - 0xC, 0, 0], ecx=None, edx=None)
        e.hit(DELAY, 0x005FB580, [e.aip(2)])
    e.hit(SETMODE, 0x005FB598, [0, 0, 0])


def trap_shot(e, use_skill, site_die, site_shot, site_idle):
    i, t = e.i, e.i["target"]
    if t != 0 and e.le(i["dist"], e.aip(1), "dist<=aip1") and e.lt(s32(e.c14), e.aip(2), "v14<aip2"):
        if use_skill:
            if e.sk(1) >= 0 and e.c18 == 0:
                e.hit(USESKILL, site_shot, [e.skm(1), e.sk(1), t, 0, 0])
        elif e.c18 == 0:
            e.hit(SETMODEAT, site_shot, [4, t])
        e.c18 = 0
        e.hit(IDLE, site_idle, [e.aip(3)])
    e.c4 |= 0x20000
    e.hit(SETMODE, site_die, [0, 0, 0])


def m_tmissile(e):                                      # row 77, 0x005FB5B0
    trap_shot(e, False, 0x005FB5E4, 0x005FB615, 0x005FB63D)


def m_tpoison(e):                                       # row 80, 0x005FB900
    trap_shot(e, True, 0x005FB934, 0x005FB97F, 0x005FB9A7)


def m_tnova(e):                                         # row 92, 0x005FB9B0
    trap_shot(e, True, 0x005FB9E4, 0x005FBA2F, 0x005FBA57)


def arrow(e, axis, site_far, site_mode, site_skill, site_idle, kind_site):
    i, t = e.i, e.i["target"]
    T = s32(i["frame"])
    if e.lt(i["dist"], e.aip(1), "dist<aip1") or e.lt(e.aip(2), i["dist"], "dist>aip2"):
        e.hit(IDLE, site_far, [40])
    a = i["ux"] - i["tx"] if axis == "x" else i["uy"] - i["ty"]
    if e.le(abs(a), 2, "|a|<=2") and e.lt(s32(e.c14), T, "T>v14"):
        e.c14 = u32(e.aip(3) + T)
        if s32(e.rk) < 0:                       # the arrow-kind helper 0x005FB650
            if e.lt(i["lvl"], 40, "lvl<40"):
                e.rk = 0
            else:
                n = 4 if e.neg == "r4" else 3
                step(e.seed)
                e.rk = e.seed[0] % n
        if e.rk != 1:
            e.hit(SETMODEAT, site_mode, [4, t])
        if e.sk(1) >= 0:
            e.c1c = u32(e.aip(4) + T)
            e.hit(USESKILL, site_skill, [e.skm(1), e.sk(1), t, 0, 0])
    e.hit(IDLE, site_idle, [30])


def m_trarrow(e):                                       # row 78, 0x005FB6C0
    arrow(e, "x", 0x005FB7D3, 0x005FB762, 0x005FB7AB, 0x005FB7BF, 0x005FB74E)


def m_tlarrow(e):                                       # row 79, 0x005FB7E0
    arrow(e, "y", 0x005FB8F3, 0x005FB882, 0x005FB8CB, 0x005FB8DF, 0x005FB86E)


def m_tmelee(e):                                        # row 87, 0x005FBA60
    t = e.i["target"]
    if e.i["melee"] == 0:
        e.hit(IDLE, 0x005FBAED, [40])
    if e.chance(1):
        e.hit(SETMODEAT, 0x005FBAC5, [4, t])
    e.hit(IDLE, 0x005FBADB, [e.aip(2)])


MODELS = {"skmage": m_skmage, "fetish": m_fetish, "fetishalt": m_fetishalt, "queen": m_queen, "vmother": m_vmother,
          "vdog": m_vdog, "fmage": m_fmage, "regurg": m_regurg, "dknight": m_dknight, "aknight": m_aknight,
          "oknight": m_oknight, "quill": m_quill, "ehole": m_ehole, "tmissile": m_tmissile, "trarrow": m_trarrow,
          "tlarrow": m_tlarrow, "tpoison": m_tpoison, "tmelee": m_tmelee, "tnova": m_tnova}
CONTROLS = ("le", "d0", "cmp", "r4")


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
                col.append(rnd.choice(ds + ds + [rnd.randrange(0, 101), rnd.randrange(-3, 111), 0, 1, 2, 3, 5, 12,
                                                 20, 50]))
            aip.append(col)
        diff = k % 3
        frame = rnd.randrange(100, 100000)
        inp = {
            "fam": fam, "seed": seed, "diff": diff, "aip": aip, "frame": frame,
            "melee": rnd.randrange(2),
            "dist": rnd.choice([0, 1, 4, 5, 6, 10, 14, 15, 20, rnd.randrange(0, 60)]
                               + [aip[j][diff] + rnd.choice((-1, 0, 1)) for j in (0, 1, 4)]),
            "m54": rnd.choice([0, 3, 19, 7, 2]),
            "ctl14": rnd.choice([0, 0, 1, 2, 3, 4, 5, 6, -1]), "ctl18": rnd.choice([0, 0, 1, 2, 7, -1]),
            "ctl1c": rnd.choice([0, 0, 1, 2, -1]),
            "c4": rnd.choice([0, 0x20000, rnd.randrange(1 << 32)]),
            "skill": [rnd.choice([-1, rnd.randrange(0, 400), rnd.randrange(0, 400)]) for _ in range(3)],
            "skmode": [rnd.randrange(16) for _ in range(3)],
            "ux": rnd.randrange(1 << 16), "uy": rnd.randrange(1 << 16),
            "umode": rnd.choice([1, 1, 10, 11, 11, 0, 2, 12]), "state": rnd.randrange(18),
            "cls": rnd.randrange(0x2E0), "ttype": rnd.choice([0, 1]), "tguid": rnd.randrange(1 << 32),
            "lvl": rnd.choice([1, 39, 40, 41, rnd.randrange(0, 137)]), "rk": rnd.choice([-1, -1, 0, 1, 2]),
        }
        inp["tx"] = u32(inp["ux"] + rnd.choice([-3, -2, -1, 0, 1, 2, 3, rnd.randrange(-50, 50)])) & 0xFFFF
        inp["ty"] = u32(inp["uy"] + rnd.choice([-3, -2, -1, 0, 1, 2, 3, rnd.randrange(-50, 50)])) & 0xFFFF
        if fam == "queen":                       # counts around aip1
            inp["ctl14"] = aip[0][diff] + rnd.choice((-1, 0, 1, -5))
            inp["ctl1c"] = rnd.choice([0, 0, 0, 1])
            inp["ctl18"] = rnd.choice([0, 0, 1])
        if fam == "ehole":                       # frames and counts around their tests
            inp["ctl14"] = rnd.choice([0, -1, 1, u32(frame + rnd.choice((-1, 0, 1, 100))), u32(frame - 1)])
            inp["ctl18"] = rnd.choice([0, 1, 2, -1])
            inp["dist"] = rnd.choice([4, 5, 6, inp["dist"]])
        if fam in ("tmissile", "tpoison", "tnova"):
            inp["ctl14"] = aip[1][diff] + rnd.choice((-1, 0, 1, -3))
            inp["ctl18"] = rnd.choice([0, 0, 1])
            inp["dist"] = max(0, aip[0][diff] + rnd.choice((-1, 0, 1, -4)))
        if fam in ("trarrow", "tlarrow"):
            inp["dist"] = rnd.choice([aip[0][diff], aip[1][diff], aip[0][diff] - 1, aip[1][diff] + 1,
                                      rnd.randrange(0, 30)])
            if rnd.randrange(3):                 # most cases inside the window
                lo, hi = sorted((aip[0][diff], aip[1][diff]))
                inp["dist"] = max(0, rnd.randrange(lo, hi + 1))
            inp["ctl14"] = u32(frame + rnd.choice((-1, 0, 1, -100, 100, -1, -100)))
            if rnd.randrange(3):                 # the axis within 3 (dev-1 had 4 and 10 cases reaching the draw)
                inp["tx"] = (inp["ux"] + rnd.choice((-3, -2, -1, 0, 1, 2, 3))) & 0xFFFF
                inp["ty"] = (inp["uy"] + rnd.choice((-3, -2, -1, 0, 1, 2, 3))) & 0xFFFF
            if rnd.randrange(2):                 # an unset region word, in a level from 40 up
                inp["rk"], inp["lvl"] = -1, rnd.choice([40, 41, rnd.randrange(40, 137)])
        if fam == "regurg":
            inp["ctl14"] = rnd.choice([0, 1, 2, 3, 4, 5, 6, -1])
            inp["ctl18"] = rnd.randrange(1 << 32)
        if fam in ("tmissile", "tpoison", "tnova") and rnd.randrange(6) == 0:
            inp["target"] = 0                    # row kind 2 runs without a target (row 77, 80); 92 is kind 1
        else:
            inp["target"] = TARGET
        sk = "".join(hx16(s) for s in inp["skill"])
        lines = [
            "w %08x %s" % (GAME + 0x6D, "%02x" % diff),
            "w %08x %s" % (GAME + 0xA8, hx32(frame)),
            "w %08x %s" % (GAME + 0xF0 + 4 * inp["lvl"], hx32(REGION)),
            "w %08x %s" % (UNIT, hx32(1) + hx32(inp["cls"])),
            "w %08x %s" % (UNIT + 0x10, hx32(inp["umode"]) + hx32(MDATA)),
            "w %08x %s%s" % (UNIT + 0x20, hx32(seed[0]), hx32(seed[1])),
            "w %08x %s" % (UNIT + 0x2C, hx32(UPATH)),
            "w %08x %s" % (UNIT + 0xC4, hx32(inp["c4"])),
            "w %08x %s" % (UPATH + 0x02, hx16(inp["ux"])), "w %08x %s" % (UPATH + 0x06, hx16(inp["uy"])),
            "w %08x %s" % (UPATH + 0x1C, hx32(ROOM)),
            "w %08x %s" % (ROOM + 0x10, hx32(DROOM)), "w %08x %s" % (DROOM + 0x58, hx32(LEVEL)),
            "w %08x %s" % (LEVEL + 0x1D0, hx32(inp["lvl"])), "w %08x %s" % (REGION + 0x2D4, hx32(inp["rk"])),
            "w %08x %s" % (TARGET, hx32(inp["ttype"])), "w %08x %s" % (TARGET + 0x0C, hx32(inp["tguid"])),
            "w %08x %s" % (TARGET + 0x2C, hx32(TPATH)),
            "w %08x %s" % (TPATH + 0x02, hx16(inp["tx"])), "w %08x %s" % (TPATH + 0x06, hx16(inp["ty"])),
            "w %08x %s" % (MDATA + 0x28, hx32(CTL)), "w %08x %s" % (MDATA + 0x54, hx32(inp["m54"])),
            "w %08x %s" % (CTL, hx32(inp["state"])),
            "w %08x %s%s%s%s" % (CTL + 0x14, hx32(inp["ctl14"]), hx32(inp["ctl18"]), hx32(inp["ctl1c"]), hx32(0)),
            "w %08x %s" % (CTX, hx32(CTL) + hx32(0) + hx32(inp["target"]) + hx32(0) + hx32(0)
                           + hx32(inp["dist"]) + hx32(inp["melee"]) + hx32(MREC) + hx32(MS2)),
            "w %08x %s" % (MREC + 0x56, "".join(hx16(aip[j][d]) for j in range(8) for d in range(3))),
            "w %08x %s" % (MREC + 0x170, sk + hx16(-1) + "00" * 8),
            "w %08x %s" % (MREC + 0x180, "".join("%02x" % m for m in inp["skmode"]) + "00" * 5),
            "w %08x %s" % (G_DATATABLES, hx32(DTBL)),
            "w %08x %s" % (DTBL + 0xA80, hx32(0x2E0)),
            "d %08x %d" % (STK_LO, STK_LEN), "d %08x 8" % (UNIT + 0x20), "d %08x 12" % (CTL + 0x14),
            "d %08x 4" % (UNIT + 0xC4), "d %08x 4" % (REGION + 0x2D4),
            "call %08x %08x %08x %08x" % (FNS[fam], GAME, UNIT, CTX),
        ]
        cases.append(lines)
        meta.append(inp)
    mem = ["observe %08x" % a for a in OBSERVE] + ["guard %08x" % a for a in FATAL + ALLOC]
    return cases, meta, mem


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        cases, meta, mem = gen_family(fam, random.Random("r52e-" + fam))
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
    fn, site, ecx, edx, args, seed, c14, c18, c1c, c4, rk, block = want
    if c.get("obs") != fn:
        return False
    gseed = list(struct.unpack("<II", c["dumps"][UNIT + 0x20]))
    g14, g18, g1c = struct.unpack("<III", c["dumps"][CTL + 0x14])
    gc4 = struct.unpack("<I", c["dumps"][UNIT + 0xC4])[0]
    grk = struct.unpack("<I", c["dumps"][REGION + 0x2D4])[0]
    ok = gseed == seed and g14 == c14 and g18 == c18 and g1c == c1c and gc4 == c4 and grk == rk
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
    _, meta, _ = gen_family(fam, random.Random("r52e-" + fam))
    calls, traced = read_out(os.path.join(d, fam + ".out"))
    bad, match, stops = [], 0, 0
    ctl = {n: [0, 0] for n in CONTROLS}
    site_pass = 0
    bounds = {}
    ndraws = 0
    edges = {}
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
        site_pass += matches(c, want, site_shift=1) if want[0] != RET else 0
        for n in ctl:
            nw = run_model(inp, neg=n)
            if nw != want:
                ctl[n][0] += 1
                ctl[n][1] += matches(c, nw)
    line = ("AI52E %s cases=%d match=%d bad=%d stopped=%d traced=%d drew=%d " % (
        fam, len(meta), match, len(bad), stops, len(traced), ndraws)
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
    print("AI52E total cases=%d match=%d" % tuple(tot))
    print("AI52E result=%s" % ("ok" if allok else "FAIL"))


def cmd_manifest(d, write):
    rows = []
    for fam in FAMILIES:
        for ext in ("cases", "mem", "out", "err"):
            p = os.path.join(d, "%s.%s" % (fam, ext))
            if os.path.exists(p):
                rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.basename(p)))
    for extra in ("check.txt", "ai_cat_emu4.py.rev"):
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

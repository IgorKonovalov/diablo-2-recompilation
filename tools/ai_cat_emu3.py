#!/usr/bin/env python3
"""Plan 0052 phase 1.2, catalogue batch 3 (pool-C, `lane/r52d`): fourteen think functions of AI rows 33-63 run under
Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java and compared with the models
below. No game run, no slot. Same method as tools/ai_cat_emu2.py (batch 2), with the AI-control words +0x14, +0x18
and +0x1C and the unit's flag word +0xC4 compared at every boundary, and the stack words a pointer argument addresses
compared where the boundary takes one.

    python3 -I tools/ai_cat_emu3.py cases [--dir D]      write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/ai_cat_emu3.py check [--dir D]      compare every D/<family>.out with its model, account for
                                                         every traced access, run the negative and site controls
    python3 -I tools/ai_cat_emu3.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r52d/emu. Every case draw comes from random.Random("r52d-<family>"), so `cases` regenerates
identical files. The development run (emu/dev-1) used the writer before the nest, sarcophagus, elemental beast and
tentacle head tuning below (its copy, emu/dev-1/ai_cat_emu3.py.rev, checks it), and the second (emu/dev-2) the writer
before the tentacle head's distance tuning (emu/dev-2/ai_cat_emu3.py.rev); the models are the same in all three.

Each family runs one think function `(ECX game, EDX unit; ctx)` (ai/0004) on a declared image: the game's difficulty
byte (+0x6D) and frame (+0xA8); the unit's type (+0x00, 1), class (+0x04), mode (+0x10), monster data pointer
(+0x14), seed (+0x20/+0x24), path pointer (+0x2C) and flag word (+0xC4); the path's x (+0x02, u16), y (+0x06, u16)
and room (+0x1C); the monster data's AI control pointer (+0x28) and +0x54 word; the AI control's state (+0x00), +0x14,
+0x18, +0x1C and +0x20 (no parameter record); the AiCtx (+0x00 ctl, +0x08 target, +0x14 distance, +0x18 melee,
+0x1C MonStats record, +0x20 MonStats2 record); the MonStats record's aip block (+0x56..+0x85), Skill1..3
(+0x170..+0x175) and Sk1..3mode (+0x180..+0x182); the MonStats2 record's +0x0E byte; the DataTables pointer
(0x00744304) and its MonStats count (+0xA80). Every callee the function reaches is an observed boundary, except
RNG_Range (0x0045C390), RNG_RangeB (0x0045C3E0), sub_005DD2B0_AiMonState3or19 with its callee 0x005734E0, the
position getters 0x0045ADF0/0x0045AE20 with 0x006488C0/0x00648900, and sub_00620BB0_UnitGetRoom with
0x00648A80, which run on the declared image. The claim per case: the first boundary reached, its call site (the
return address), the registers and stack arguments the callee takes, the unit seed, the AI control's +0x14/+0x18/+0x1C
and the unit's +0xC4 at the boundary, and where a pointer argument addresses the frame, the word it addresses.

Families (function, row):
  meteor   0x005F56D0 row 33 HellMeteor       lancer   0x005F5D50 row 36 CorruptLancer
  skelbow  0x005F6070 row 37 SkeletonBow      larva    0x005F6220 row 38 MaggotLarva
  pinhead  0x005F6340 row 39 PinHead          egg      0x005F6530 row 40 MaggotEgg
  nest     0x005F6650 row 43 FoulCrowNest     sarco    0x005F6A10 row 45 Sarcophagus
  beast    0x005F6B70 row 46 ElementalBeast   scimitar 0x005F6CA0 row 47 FlyingScimitar
  frog     0x005F8260 row 52 FrogDemon        frogalt  0x005F81D0 row 52 FrogDemon's alt
  thead    0x005F9270 row 57 TentacleHead     garg     0x005F9490 row 63 GargoyleTrap

Controls: `le` compares each draw with `<=` instead of `<` (and `>=` with `>`); `d0` reads every aip from the Normal
column; `site` expects each call site one byte later. Each must fail every case it separates.

Not covered (ADR-0021): every callee at or after a boundary (the commands, the move helpers, the path override and
stop distance setters, the hostile search, the skill target test, the cell tests, the take-off and landing, the
unit kill, the event queue, the AI init) and so every branch that a boundary call's result decides (the frog's
landing and cell test, the nest's and sarcophagus's cell test, the skeleton archer's and tentacle head's hostile).
Rows 35, 48, 49 and 56 are not emulated (ai/0004 § 3). Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r52d", "emu")

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
G_DATATABLES = 0x00744304
STK_LO = 0x7FEFFC00
STK_LEN = 1040              # to 0x7FF00010: the frame, the return address and the ctx argument slot
EBP = 0x7FEFFFFC            # the think function's frame pointer (entry ESP 0x7FF00000, `push ebp; mov ebp,esp`)
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)

SETMODE, IDLE, WALK, PATHOVR, RING, T56, WALKSTOP, RUNSTOP, DELAY, TOWARD = (
    0x005DDF90, 0x005DE080, 0x005DEC80, 0x005DE190, 0x005DE200, 0x005DF7D0, 0x005DEF80, 0x005DEFB0, 0x005DE0F0,
    0x005DE6D0)
FINDHOSTILE, USESKILL, SETMODE2, STOPDIST, GETTARGET, KILLED, QUEUE, SPAWNCELL, COLLTEST, TAKEOFF, LAND, AIINIT, \
    SETPATHTGT = (
        0x005DDC30, 0x005DEAD0, 0x005DDFC0, 0x00649070, 0x00553540, 0x0057CCB0, 0x005417D0, 0x005FD350, 0x0064CB30,
        0x005F2EB0, 0x005F2FC0, 0x005B0E00, 0x00620C10)
OTHER = (0x00621F20, 0x005DD0B0, 0x005DD290, 0x005FD470, 0x005DF140, 0x0058F0D0, 0x00552F60, 0x00621DC0, 0x006488A0,
         0x005DED20, 0x005DE190)
OBSERVE = tuple(sorted(set((SETMODE, IDLE, WALK, PATHOVR, RING, T56, WALKSTOP, RUNSTOP, DELAY, TOWARD, FINDHOSTILE,
                            USESKILL, SETMODE2, STOPDIST, GETTARGET, KILLED, QUEUE, SPAWNCELL, COLLTEST, TAKEOFF,
                            LAND, AIINIT, SETPATHTGT) + OTHER)))

FNS = {"meteor": 0x005F56D0, "lancer": 0x005F5D50, "skelbow": 0x005F6070, "larva": 0x005F6220,
       "pinhead": 0x005F6340, "egg": 0x005F6530, "nest": 0x005F6650, "sarco": 0x005F6A10, "beast": 0x005F6B70,
       "scimitar": 0x005F6CA0, "frog": 0x005F8260, "frogalt": 0x005F81D0, "thead": 0x005F9270, "garg": 0x005F9490}
FAMILIES = tuple(FNS)
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
    """One case's inputs and the model's running state (the unit seed, the AI control's +0x14/+0x18/+0x1C, +0xC4)."""

    def __init__(self, inp, neg=None):
        self.i, self.neg = inp, neg
        self.seed = list(inp["seed"])
        self.c14, self.c18, self.c1c = inp["ctl14"], inp["ctl18"], inp["ctl1c"]
        self.c4 = inp["c4"]

    def aip(self, k):
        d = 0 if self.neg == "d0" else self.i["diff"]
        return self.i["aip"][k - 1][d]

    def draw(self):
        step(self.seed)
        return self.seed[0] % 100

    def rng(self, n):                       # RNG_Range / RNG_RangeB: n < 1 gives 0 without a step
        if s32(n) < 1:
            return 0
        step(self.seed)
        return self.seed[0] % u32(n)

    def lt(self, a, b):
        return a <= b if self.neg == "le" else a < b

    def chance(self, k):
        return self.lt(self.draw(), self.aip(k))

    def rchance(self, k):                   # the same through RNG_Range(seed, 100)
        return self.lt(self.rng(100), self.aip(k))

    def st(self):
        return self.i["m54"] in (3, 19)

    def sk(self, k):
        return self.i["skill"][k - 1]

    def skm(self, k):
        return self.i["skmode"][k - 1]

    def hit(self, fn, site, args, ecx=GAME, edx=UNIT, block=None):
        raise Hit((fn, site, ecx, edx, [u32(a) for a in args], list(self.seed), u32(self.c14), u32(self.c18),
                   u32(self.c1c), u32(self.c4), block))


def m_meteor(e):                                        # row 33, 0x005F56D0
    i = e.i
    if e.sk(1) >= 0 and e.chance(1):
        a3 = e.aip(3)
        x = i["ux"] + e.rng(2 * a3) - a3
        y = i["uy"] + e.rng(2 * a3) - a3
        e.hit(USESKILL, 0x005F5807, [e.skm(1), e.sk(1), 0, x, y])
    e.hit(IDLE, 0x005F5823, [e.aip(2)])


def m_lancer(e):                                        # row 36, 0x005F5D50
    i, t = e.i, e.i["target"]
    if i["dist"] > e.aip(5):
        e.hit(STOPDIST, 0x005F5D9A, [UPATH, i["mrng"]], ecx=None, edx=None)
    if i["melee"]:
        if e.c14 == 0 and not e.chance(2):
            e.hit(IDLE, 0x005F5E35, [e.aip(3)])
        e.c14 = 0
        if e.sk(1) >= 0 and e.chance(6):
            e.hit(USESKILL, 0x005F5EB1, [e.skm(1), e.sk(1), t, 0, 0])
        if e.sk(2) >= 0 and e.rchance(7):
            e.hit(USESKILL, 0x005F5EFF, [e.skm(2), e.sk(2), t, 0, 0])
        if e.sk(3) >= 0 and e.rchance(8):
            e.hit(USESKILL, 0x005F5F50, [e.skm(3), e.sk(3), t, 0, 0])
        e.hit(SETMODE, 0x005F5F69, [4, t])
    if not e.chance(1):
        e.hit(IDLE, 0x005F6062, [e.aip(3)])
    e.hit(STOPDIST, 0x005F5FCA, [UPATH, i["mrng"]], ecx=None, edx=None)


def m_skelbow(e):                                       # row 37, 0x005F6070
    blk = (EBP + 8, [e.i["dist"]])
    if e.st():
        e.hit(FINDHOSTILE, 0x005F60AB, [EBP + 8, 0], block=blk)
    e.hit(FINDHOSTILE, 0x005F60D3, [EBP + 8, 0], block=blk)


def m_larva(e):                                         # row 38, 0x005F6220
    t = e.i["target"]
    if e.i["melee"]:
        if e.c14 == 0 and e.chance(1):
            e.c14 = 1
            e.hit(SETMODE, 0x005F62A0, [4, t])
        e.c14 = 0
        e.hit(IDLE, 0x005F62C4, [e.aip(2)])
    e.c14 = 0
    if e.chance(3):
        e.hit(WALK, 0x005F631B, [t, 1])
    e.hit(IDLE, 0x005F6331, [e.aip(4)])


def m_pinhead(e):                                       # row 39, 0x005F6340
    t = e.i["target"]
    if e.i["melee"]:
        if e.c14 != 0 and not e.chance(1):
            e.hit(IDLE, 0x005F63B6, [e.aip(2)])
        e.c14 = 1
        if e.sk(1) >= 0 and e.chance(5):
            e.hit(USESKILL, 0x005F642F, [e.skm(1), e.sk(1), t, 0, 0])
        if e.sk(2) >= 0 and e.chance(6):
            e.hit(USESKILL, 0x005F649E, [e.skm(2), e.sk(2), t, 0, 0])
        e.hit(SETMODE, 0x005F64B4, [4, t])
    e.c14 = 0
    if e.chance(3):
        e.hit(WALK, 0x005F650E, [t, 7])
    e.hit(IDLE, 0x005F6524, [e.aip(4)])


def m_egg(e):                                           # row 40, 0x005F6530
    t = e.i["target"]
    if e.sk(1) >= 0 and e.c14 != 1 and e.chance(2):
        e.hit(USESKILL, 0x005F65C4, [e.skm(1), e.sk(1), t, 0, 0])
    if e.c14 == 1:
        e.hit(GETTARGET, 0x005F65FC, [GAME, UNIT, 1], ecx=None, edx=None)
    e.hit(IDLE, 0x005F6619, [e.aip(1)])


def nest_like(e, far, site_far, strict, site_die, cls, site_cell, set14_before, site_idle):
    i = e.i
    if i["dist"] > far:
        e.hit(IDLE, site_far, [25])
    a3 = e.aip(3)
    if (s32(e.c18) > a3) if strict else (s32(e.c18) >= a3):
        e.c4 |= 0x20000
        e.hit(SETMODE2, site_die, [0, 0, 0])
    d = s32(i["frame"] - e.c14)
    if d < 0:
        d = s32(-d)
    if e.sk(1) >= 0 and d >= e.aip(1):
        if set14_before:
            e.c14 = i["frame"]
        c = cls if i["mscount"] > cls else 0xFFFFFFFF
        e.hit(SPAWNCELL, site_cell, [i["ux"], i["uy"], 0], ecx=c, edx=ROOM)
    e.draw()
    e.hit(IDLE, site_idle, [e.seed[0] % 10 + 20])


def m_nest(e):                                          # row 43, 0x005F6650
    nest_like(e, 20, 0x005F667D, False, 0x005F66B1, 0xCE, 0x005F6733, True, 0x005F67A4)


def m_sarco(e):                                         # row 45, 0x005F6A10
    nest_like(e, 25, 0x005F6A3D, True, 0x005F6A71, 0xE4, 0x005F6AEA, False, 0x005F6B64)


def m_beast(e):                                         # row 46, 0x005F6B70
    i, t = e.i, e.i["target"]
    if e.c14 == 2:
        e.hit(KILLED, 0x005F6BAE, [t, 1])
    if e.c14 == 0 and (i["dist"] < e.aip(2) or e.st()):
        e.hit(SETMODE, 0x005F6BE3, [8, t])
    if e.c14 != 1:
        e.hit(IDLE, 0x005F6C95, [e.aip(3)])
    if i["melee"]:
        e.hit(SETMODE, 0x005F6C59, [8, t])
    if e.rchance(1):
        e.hit(WALK, 0x005F6C32, [t, 0])
    e.hit(RING, 0x005F6C44, [8])


def m_scimitar(e):                                      # row 47, 0x005F6CA0
    t = e.i["target"]
    if not e.i["melee"]:
        if e.chance(1):
            e.hit(TOWARD, 0x005F6DB2, [t, 8, 1])
        if e.chance(1):
            e.hit(WALK, 0x005F6DFC, [t, 7])
    else:
        if e.chance(2):
            e.hit(SETMODE, 0x005F6D10, [4, t])
        if e.chance(4):
            e.hit(T56, 0x005F6D60, [t, 2, 0])
    e.hit(IDLE, 0x005F6E12, [e.aip(3)])


def m_frog(e):                                          # row 52, 0x005F8260
    i, t, dist = e.i, e.i["target"], e.i["dist"]
    if e.c1c == 0:
        if e.sk(1) >= 0 and dist > 12:
            e.hit(USESKILL, 0x005F82BF, [e.skm(1), e.sk(1), t, 0, 0])
        if e.sk(2) >= 0:
            e.hit(LAND, 0x005F82F9, [])
        e.hit(COLLTEST, 0x005F836A, [ROOM, i["ux"], i["uy"], 0xC01], ecx=None, edx=None)
    if e.c1c == 1:
        if e.sk(2) >= 0:
            if dist < e.aip(8):
                e.hit(LAND, 0x005F83BA, [])
            if dist < 20 and s32(e.c18) > 64:
                e.hit(LAND, 0x005F8411, [])
        e.hit(TAKEOFF, 0x005F841E, [])
    if t == 0:
        e.hit(DELAY, 0x005F844F, [32])
    if i["melee"]:
        if e.rchance(2):
            e.hit(SETMODE, 0x005F848B, [5, t])
        if e.rchance(1):
            e.hit(SETMODE, 0x005F84BD, [4, t])
        if e.rchance(3):
            e.hit(T56, 0x005F84F7, [t, 3, 0])
        e.hit(DELAY, 0x005F850D, [e.aip(7)])
    if dist < e.aip(6):
        if e.rchance(5):
            e.hit(SETMODE, 0x005F848B, [5, t])
        if e.rchance(4):
            e.hit(T56, 0x005F8570, [t, 4, 0])
        e.hit(DELAY, 0x005F850D, [e.aip(7)])
    if e.rchance(4):
        e.hit(T56, 0x005F859C, [t, 3, 0])
    e.hit(WALKSTOP, 0x005F85B2, [t, 4])


def m_frogalt(e):                                       # row 52's alt, 0x005F81D0
    i = e.i
    if i["state"] not in (10, 11) and e.sk(1) >= 0 and s32(e.c1c) >= 2:
        e.hit(USESKILL, 0x005F8223, [e.skm(1), e.sk(1), i["target"], 0, 0])
    e.hit(AIINIT, 0x005F8245, [CTL, i["state"]])


def m_thead(e):                                         # row 57, 0x005F9270
    i, t, dist = e.i, e.i["target"], e.i["dist"]
    T = s32(i["frame"])
    if e.sk(1) >= 0:
        if e.c1c == 0:
            e.hit(USESKILL, 0x005F92CA, [e.skm(1), e.sk(1), t, 0, 0])
        if e.c1c == 2 and s32(e.c18) < T and (dist > e.aip(6) or (not i["melee"] and e.rchance(2))):
            e.hit(USESKILL, 0x005F9362, [e.skm(1), e.sk(1), t, 0, 0])
    if e.sk(2) >= 0 and e.c1c == 1:
        if s32(e.c18) < T and (i["melee"] or dist < e.aip(6)):
            e.hit(USESKILL, 0x005F93BB, [e.skm(2), e.sk(2), UNIT, 0, 0])
    if e.c1c == 1:
        e.hit(DELAY, 0x005F93FC, [e.aip(5)])
    e.hit(FINDHOSTILE, 0x005F9414, [EBP - 4, 0], block=(EBP - 4, [dist]))


def m_garg(e):                                          # row 63, 0x005F9490
    if s32(e.c14) > 0:
        e.hit(IDLE, 0x005F94C7, [e.c14])
    e.hit(SETPATHTGT, 0x005F94DE, [UNIT, e.i["target"]], ecx=None, edx=None)


MODELS = {"meteor": m_meteor, "lancer": m_lancer, "skelbow": m_skelbow, "larva": m_larva, "pinhead": m_pinhead,
          "egg": m_egg, "nest": m_nest, "sarco": m_sarco, "beast": m_beast, "scimitar": m_scimitar, "frog": m_frog,
          "frogalt": m_frogalt, "thead": m_thead, "garg": m_garg}


def run_model(inp, neg=None):
    try:
        MODELS[inp["fam"]](Env(inp, neg))
    except Hit as h:
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
        ds = first_draws(seed, 6)
        aip = []
        for _ in range(8):
            col = []
            for _ in range(3):
                col.append(rnd.choice(ds + ds + [rnd.randrange(0, 101), rnd.randrange(-3, 111), 0, 1, 2, 3, 12, 20,
                                                 50]))
            aip.append(col)
        diff = k % 3
        frame = rnd.randrange(100, 100000)
        inp = {
            "fam": fam, "seed": seed, "diff": diff, "aip": aip, "frame": frame,
            "melee": rnd.randrange(2),
            "dist": rnd.choice([0, 1, 4, 5, 6, 10, 11, 12, 13, 19, 20, 21, 25, 26, 40, rnd.randrange(0, 60)]
                               + [aip[j][diff] + rnd.choice((-1, 0, 1)) for j in (1, 4, 5, 7)]),
            "m54": rnd.choice([0, 3, 19, 7, 2]),
            "ctl14": rnd.choice([0, 0, 1, 1, 2, 3, -1]), "ctl18": rnd.choice([0, 0, 1, 2, 64, 65, -1]),
            "ctl1c": rnd.choice([0, 0, 1, 1, 2, 2, 3, -1]),
            "c4": rnd.choice([0, 0x20000, rnd.randrange(1 << 32)]),
            "skill": [rnd.choice([-1, rnd.randrange(0, 400), rnd.randrange(0, 400)]) for _ in range(3)],
            "skmode": [rnd.randrange(16) for _ in range(3)],
            "mrng": rnd.randrange(256), "ux": rnd.randrange(1 << 16), "uy": rnd.randrange(1 << 16),
            "mscount": rnd.choice([0x2E0, 0x2E0, 0x2E0, 0xCE, 0xCF, 0xE4, 0xE5]),
            "umode": rnd.choice([1, 2, 11, 12]), "state": rnd.choice([rnd.randrange(18), 10, 11, 52]),
            "cls": rnd.randrange(0x2E0),
        }
        if fam in ("nest", "sarco"):            # frame distances around aip1 and spawn counts around aip3
            inp["ctl14"] = u32(frame - aip[0][diff] + rnd.choice((-1, 0, 1, 0, -50, 50)))
            if rnd.randrange(2):
                inp["ctl14"] = u32(frame + aip[0][diff] + rnd.choice((-1, 0, 1)))
            inp["ctl18"] = aip[2][diff] + rnd.choice((-1, 0, 1))
            inp["dist"] = rnd.choice([inp["dist"], 3, 3, 10, 10, 19, 20, 21, 24, 25, 26])
            if inp["dist"] > 26:                # most cases inside the range (dev-1 had 134 nest cases beyond 20)
                inp["dist"] = rnd.randrange(0, 21)
        if fam == "beast":                      # more cases in the flight state (dev-1 had 29 reaching the draw)
            inp["ctl14"] = rnd.choice([0, 1, 1, 1, 2, 3])
        if fam == "thead":                      # skill timers around the frame
            inp["ctl18"] = u32(frame + rnd.choice((-1, 0, 1, -100, 100)))
            inp["ctl1c"] = rnd.choice([0, 1, 2, 2, 2, 3])   # dev-1 had 9 cases reaching the draw
            inp["melee"] = int(rnd.randrange(3) == 0)
            if rnd.randrange(2):                # at or inside aip6 (dev-2 had 7 cases reaching the draw)
                inp["dist"] = max(0, aip[5][diff] - rnd.randrange(3))
        if fam == "frog":
            inp["ctl18"] = rnd.choice([0, 63, 64, 65, 200, -1])
        if fam in ("frog", "frogalt", "thead") and rnd.randrange(5) == 0:
            inp["target"] = 0                   # row kinds 5 and 2 run without a target
        else:
            inp["target"] = rnd.randrange(1, 1 << 31) & ~3
        sk = "".join(hx16(s) for s in inp["skill"])
        lines = [
            "w %08x %s" % (GAME + 0x6D, "%02x" % diff),
            "w %08x %s" % (GAME + 0xA8, hx32(frame)),
            "w %08x %s" % (UNIT, hx32(1) + hx32(inp["cls"])),
            "w %08x %s" % (UNIT + 0x10, hx32(inp["umode"]) + hx32(MDATA)),
            "w %08x %s%s" % (UNIT + 0x20, hx32(seed[0]), hx32(seed[1])),
            "w %08x %s" % (UNIT + 0x2C, hx32(UPATH)),
            "w %08x %s" % (UNIT + 0xC4, hx32(inp["c4"])),
            "w %08x %s" % (UPATH + 0x02, hx16(inp["ux"])), "w %08x %s" % (UPATH + 0x06, hx16(inp["uy"])),
            "w %08x %s" % (UPATH + 0x1C, hx32(ROOM)),
            "w %08x %s" % (MDATA + 0x28, hx32(CTL)), "w %08x %s" % (MDATA + 0x54, hx32(inp["m54"])),
            "w %08x %s" % (CTL, hx32(inp["state"])),
            "w %08x %s%s%s%s" % (CTL + 0x14, hx32(inp["ctl14"]), hx32(inp["ctl18"]), hx32(inp["ctl1c"]), hx32(0)),
            "w %08x %s" % (CTX, hx32(CTL) + hx32(0) + hx32(inp["target"]) + hx32(0) + hx32(0)
                           + hx32(inp["dist"]) + hx32(inp["melee"]) + hx32(MREC) + hx32(MS2)),
            "w %08x %s" % (MREC + 0x56, "".join(hx16(aip[j][d]) for j in range(8) for d in range(3))),
            "w %08x %s" % (MREC + 0x170, sk + hx16(-1) + "00" * 8),
            "w %08x %s" % (MREC + 0x180, "".join("%02x" % m for m in inp["skmode"]) + "00" * 5),
            "w %08x %s" % (MS2 + 0x0E, "%02x" % inp["mrng"]),
            "w %08x %s" % (G_DATATABLES, hx32(DTBL)),
            "w %08x %s" % (DTBL + 0xA80, hx32(inp["mscount"])),
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
        cases, meta, mem = gen_family(fam, random.Random("r52d-" + fam))
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
    a = c.get("args", b"")
    got = [struct.unpack_from("<I", a, 4 + 4 * k)[0] for k in range(len(args))]
    ret = struct.unpack_from("<I", a, 0)[0]
    gseed = list(struct.unpack("<II", c["dumps"][UNIT + 0x20]))
    g14, g18, g1c = struct.unpack("<III", c["dumps"][CTL + 0x14])
    gc4 = struct.unpack("<I", c["dumps"][UNIT + 0xC4])[0]
    ok = (ret == site + site_shift and got == args and gseed == seed and g14 == c14 and g18 == c18 and g1c == c1c
          and gc4 == c4)
    if ecx is not None:
        ok = ok and c["regs"]["ecx"] == u32(ecx)
    if edx is not None:
        ok = ok and c["regs"]["edx"] == u32(edx)
    if block is not None:
        addr, words = block
        ok = ok and stack_words(c, addr, len(words)) == [u32(w) for w in words]
    return ok


def check_family(fam, d):
    _, meta, _ = gen_family(fam, random.Random("r52d-" + fam))
    calls, traced = read_out(os.path.join(d, fam + ".out"))
    bad, match, stops = [], 0, 0
    ctl = {n: [0, 0] for n in ("le", "d0")}
    site_pass = 0
    bounds = {}
    ndraws = 0
    if len(calls) != len(meta):
        bad.append("case count %d != %d" % (len(calls), len(meta)))
    for c, inp in zip(calls, meta):
        if "stop" in c:
            stops += 1
            bad.append("case %d STOP %s" % (c["n"], c["stop"]))
            continue
        want = run_model(inp)
        ok = matches(c, want)
        match += ok
        if not ok:
            bad.append("case %d mismatch want=%s@%s obs=%s args=%s" % (
                c["n"], hex(want[0]), hex(want[1]), hex(c.get("obs", 0)), c.get("args", b"")[:24].hex()))
        key = "%x@%x" % (want[0], want[1])
        bounds[key] = bounds.get(key, 0) + 1
        ndraws += want[5] != list(inp["seed"])
        site_pass += matches(c, want, site_shift=1)
        for n in ctl:
            nw = run_model(inp, neg=n)
            if nw != want:
                ctl[n][0] += 1
                ctl[n][1] += matches(c, nw)
    line = ("AI52D %s cases=%d match=%d bad=%d stopped=%d traced=%d drew=%d le_separating=%d le_passed=%d "
            "d0_separating=%d d0_passed=%d site_control_passed=%d boundaries=%d" % (
                fam, len(meta), match, len(bad), stops, len(traced), ndraws, ctl["le"][0], ctl["le"][1],
                ctl["d0"][0], ctl["d0"][1], site_pass, len(bounds)))
    return line, bad[:20], traced[:20], bounds


def cmd_check(d):
    allok = True
    tot = [0, 0]
    for fam in FAMILIES:
        line, bad, traced, bounds = check_family(fam, d)
        print(line)
        print("  SITES " + " ".join("%s:%d" % kv for kv in sorted(bounds.items())))
        for b in bad:
            print("  BAD", b)
        for t in traced:
            print("  TRACED", t)
        if bad or traced or "le_passed=0" not in line or "d0_passed=0" not in line \
                or "site_control_passed=0" not in line:
            allok = False
        tot[0] += NCASES
        tot[1] += int(line.split("match=")[1].split()[0])
    print("AI52D total cases=%d match=%d" % tuple(tot))
    print("AI52D result=%s" % ("ok" if allok else "FAIL"))


def cmd_manifest(d, write):
    rows = []
    for fam in FAMILIES:
        for ext in ("cases", "mem", "out", "err"):
            p = os.path.join(d, "%s.%s" % (fam, ext))
            if os.path.exists(p):
                rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.basename(p)))
    for extra in ("check.txt", "ai_cat_emu3.py.rev"):
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

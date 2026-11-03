#!/usr/bin/env python3
"""Plan 0052 phase 1.2, catalogue batches 6 (hirelings) and 7 (bosses-A), `lane/r52g`: the think functions of AI
row 61 and state rows 4-6 (with MERCAI_PickSkill and the two hireling helpers), and of rows 34, 44, 50, 53, 55, 59,
90, 144 and 146 (with Mephisto's target pick), run under Ghidra's p-code emulator (ADR-0015, ADR-0021) with
re/ghidra_scripts/EmuBoundary.java and compared with the models below. No game run, no slot. Same method as
tools/ai_cat_emu4.py (batch 4): one family per function, the first observed callee (or the return) is the outcome,
controls `le`, `d0`, `cmp` and the site control, and an `EDGES` line per family.

    python3 -I tools/ai_cat_emu6.py cases [--dir D]      write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/ai_cat_emu6.py check [--dir D]      compare every D/<family>.out with its model, account for
                                                         every traced access, run the negative and site controls
    python3 -I tools/ai_cat_emu6.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r52g/emu. Every case draw comes from random.Random("r52g-<family>"), so `cases` regenerates
identical files.

Each family runs one function on a declared image: the game's difficulty byte (+0x6D) and frame (+0xA8); the unit's
type (+0x00, 1), class (+0x04), mode (+0x10), monster data pointer (+0x14), seed (+0x20/+0x24), path pointer (+0x2C)
and flag word (+0xC4); the unit path's x (+0x02, u16), y (+0x06, u16) and room (+0x1C); the target's type (+0x00),
guid (+0x0C) and path (+0x2C), that path's x and y (u16 at +0x02/+0x06, the dynamic path) and its words +0x0C/+0x10
(the static path of types 2, 4, 5); an owner unit (the hireling helper's EDX: +0x10 mode, +0x2C path); the monster
data's AI control pointer (+0x28) and +0x54 word; the AI control's state (+0x00), +0x14, +0x18, +0x1C and +0x20 (0:
no parameter record); the AiCtx (+0x00 ctl, +0x08 target, +0x14 distance, +0x18 melee, +0x1C MonStats record);
the MonStats record's aidel bytes (+0x4F..+0x51), aip block (+0x56..+0x85), Skill1..8 (+0x170..+0x17F) and
Sk1..8mode (+0x180..+0x187); the DataTables pointer (0x00744304) with the MonStats records and count (+0xA78,
+0xA80) and the Skills records and count (+0xB98, +0xBA0), one Skills record's aurastate (+0x80). Every callee the
function reaches is an observed boundary, except RNG_Range (0x0045C390), the path getters 0x006488C0/0x00648900,
sub_00620BB0_UnitGetRoom with 0x00648A80, which run on the declared image. The claim per case: the first boundary
reached (or the return), its call site (the return address), the registers and stack arguments the callee takes,
the unit seed and the AI control's +0x14/+0x18/+0x1C at the boundary, and for the search block the words it
addresses.

Families (function, row):
  hire      0x005E52D0 row 61 Hireable (state 4)  hirealt   0x005E5280 row 61's alt (state 4's +C)
  st5       0x005E7AC0 state 5                    st6       0x005E7C10 state 6
  pick      0x005E4D30 MERCAI_PickSkill           fight     0x005E5050 the hireling's fight step
  follow    0x005E3930 the hireling's follow step
  andariel  0x005F5830 row 34 Andariel            duriel    0x005F67B0 row 44 Duriel
  mephisto  0x005F78B0 row 50 Mephisto            mpick     0x005F77C0 Mephisto's target pick
  summoner  0x005F85C0 row 53 Summoner            izual     0x005F89B0 row 55 Izual
  brinit    0x005E6300 row 59 BloodRaven init     braven    0x005E6320 row 59 BloodRaven
  griswold  0x005E5AC0 row 90 Griswold            uizual    0x005F8C80 row 144 UberIzual
  umeph     0x005F81C0 row 146 UberMephisto
The `entry` families (hire, hirealt, follow, mephisto, mpick, braven) reach their first callee before any test
(mpick: its search block is compared too): their claim is that call's site and arguments only.

Controls: `le` compares each draw with `<=` instead of `<`; `d0` reads every aip from the Normal column; `cmp`
switches the strictness of every compare that is not a draw (`<` and `<=`, `>` and `>=`); `site` expects each call
site one byte later. Each must fail every case it separates. The `EDGES` line under each family counts, per compare,
the cases that meet it at equality; a compare missing from it has no strictness control in the run.

Not covered (ADR-0021): every callee at or after a boundary and so every branch that a boundary call's result
decides. Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r52g", "emu")

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
DTBL = 0x12A00000
TPATH = 0x12B00000
SKREC = 0x12C00000
OWNER = 0x12D00000
OPATH = 0x12E00000
MSBASE = 0x13000000
G_DATATABLES = 0x00744304
STK_LO = 0x7FEFFC00
STK_LEN = 1040              # to 0x7FF00010: the frame, the return address and the first stack argument slots
EBP = 0x7FEFFFFC            # the function's frame pointer (entry ESP 0x7FF00000, `push ebp; mov ebp,esp`)
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)
NCLS = 0x2E0                # the MonStats count declared at DataTables+0xA80

SETMODEAT, IDLE, WALK, PATHOVR, T56, DELAY, FINDHOSTILE, USESKILL = (
    0x005DDF90, 0x005DE080, 0x005DEC80, 0x005DE190, 0x005DF7D0, 0x005DE0F0, 0x005DDC30, 0x005DEAD0)
HASSTATE, STEPAWAY, SEARCH, LIFEPCT, OWNERF, STATS, DISTU, PLRDATA = (
    0x00639DF0, 0x005DEFE0, 0x005DD0B0, 0x00621F20, 0x0058F0D0, 0x00625480, 0x005DC380, 0x006221A0)
ROOMTOWN, GETRSKILL, BOSSSEEN, QUEST, LINEBLK, PARAMSFIND, WTOWARD = (
    0x0061AB00, 0x006201D0, 0x0059C330, 0x005B4390, 0x00622AA0, 0x0058EEF0, 0x005DE6D0)
OTHER = (0x005DE200, 0x005DEFB0, 0x005DED20, 0x005DF530, 0x005DE000, 0x005B0E00, 0x00639DB0, 0x0058EE80,
         0x00649180, 0x0064D910, 0x0061B130, 0x00540E60, 0x005DED90, 0x005E3930, 0x005E5050, 0x005E4D30,
         0x006562F0, 0x006439B0, 0x006442A0, 0x006416D0, 0x005701B0, 0x00622C40, 0x00574BD0, 0x00649070,
         0x005DED00, 0x00648A20, 0x00648A30, 0x00621DC0, 0x0063E7A0, 0x0063E7E0, 0x005DEE50, 0x005DF400,
         0x005A6190, 0x005DC5C0, 0x005A6260, 0x005DEDE0, 0x0061AD30, 0x0054DC40, 0x00463740, 0x00554EA0,
         0x0064C040, 0x00574DE0, 0x0056DEB0, 0x005F77C0, 0x005DF680, 0x005DF140, 0x005DC480, 0x0058EF40,
         0x005DD2B0, 0x0045C3E0, 0x00472210, 0x005DD7F0, 0x005541B0, 0x00554200, 0x005B0BD0)
OBSERVE = tuple(sorted(set((SETMODEAT, IDLE, WALK, PATHOVR, T56, DELAY, FINDHOSTILE, USESKILL, HASSTATE, STEPAWAY,
                            SEARCH, LIFEPCT, OWNERF, STATS, DISTU, PLRDATA, ROOMTOWN, GETRSKILL, BOSSSEEN, QUEST,
                            LINEBLK, PARAMSFIND, WTOWARD) + OTHER)))
RET = "ret"

FNS = {"hire": 0x005E52D0, "hirealt": 0x005E5280, "st5": 0x005E7AC0, "st6": 0x005E7C10, "pick": 0x005E4D30,
       "fight": 0x005E5050, "follow": 0x005E3930, "andariel": 0x005F5830, "duriel": 0x005F67B0,
       "mephisto": 0x005F78B0, "mpick": 0x005F77C0, "summoner": 0x005F85C0, "izual": 0x005F89B0,
       "brinit": 0x005E6300, "braven": 0x005E6320, "griswold": 0x005E5AC0, "uizual": 0x005F8C80,
       "umeph": 0x005F81C0}
FAMILIES = tuple(FNS)
ENTRY = ("hire", "hirealt", "follow", "mephisto", "mpick", "braven")
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
    """One case's inputs and the model's running state (the unit seed, the AI control's +0x14/+0x18/+0x1C)."""

    def __init__(self, inp, neg=None):
        self.i, self.neg = inp, neg
        self.seed = list(inp["seed"])
        self.c14, self.c18, self.c1c = inp["ctl14"], inp["ctl18"], inp["ctl1c"]
        self.eq = set()                     # the compares this case met at equality (the cases a control can separate)

    def d(self):
        return 0 if self.neg == "d0" else self.i["diff"]

    def aip(self, k):
        return self.i["aip"][k - 1][self.d()]

    def draw(self):
        step(self.seed)
        return self.seed[0] % 100

    def rng(self, n):                       # RNG_Range: n < 1 gives 0 without a step
        if s32(n) < 1:
            return 0
        step(self.seed)
        return self.seed[0] % u32(n)

    def _lt(self, d, b, edge):
        if d == b:
            self.eq.add(edge)
        return d <= b if self.neg == "le" else d < b

    def chance(self, k):                    # inline draw < aipK (le: <=)
        return self._lt(self.draw(), self.aip(k), "draw<aip%d" % k)

    def rchance(self, k):                   # RNG_Range(seed, 100) < aipK
        return self._lt(self.rng(100), self.aip(k), "Range<aip%d" % k)

    def cdraw(self, c):                     # inline draw < constant c
        return self._lt(self.draw(), c, "draw<%d" % c)

    def lt(self, a, b, edge):               # a non-draw a < b (cmp: <=)
        if a == b:
            self.eq.add(edge)
        return a <= b if self.neg == "cmp" else a < b

    def le(self, a, b, edge):               # a non-draw a <= b (cmp: <)
        if a == b:
            self.eq.add(edge)
        return a < b if self.neg == "cmp" else a <= b

    def sk(self, k):
        return self.i["skill"][k - 1]

    def skm(self, k):
        return self.i["skmode"][k - 1]

    def tpos(self):                         # the target's x, y as Izual and UberIzual read them
        i = self.i
        if i["ttype"] in (2, 4, 5):
            return i["tpx"], i["tpy"]
        if i["tpath"] == 0:
            return 0, 0
        return i["tx"], i["ty"]

    def hit(self, fn, site, args, ecx=GAME, edx=UNIT, block=None):
        raise Hit((fn, site, ecx, edx, [u32(a) for a in args], list(self.seed), u32(self.c14), u32(self.c18),
                   u32(self.c1c), block))

    def ret(self):
        self.hit(RET, 0, [], ecx=None, edx=None)


T = TARGET


def m_hire(e):                                          # row 61 / state 4, 0x005E52D0
    e.hit(OWNERF, 0x005E52F7, [], ecx=UNIT, edx=None)


def m_hirealt(e):                                       # row 61's alt, 0x005E5280
    e.hit(HASSTATE, 0x005E529A, [UNIT, 12], ecx=None, edx=None)


def m_st5(e):                                           # state 5, 0x005E7AC0
    if e.i["umode"] != 1:
        e.hit(IDLE, 0x005E7AE8, [5])
    e.hit(ROOMTOWN, 0x005E7B00, [ROOM], ecx=None, edx=None)


def m_st6(e):                                           # state 6, 0x005E7C10
    if e.i["umode"] != 1:
        e.hit(IDLE, 0x005E7C2D, [5])
    e.hit(ROOMTOWN, 0x005E7C45, [ROOM], ecx=None, edx=None)


def m_pick(e):                                          # MERCAI_PickSkill, 0x005E4D30
    c = s32(e.i["cls"])
    if e.lt(c, 0, "cls<0"):
        e.ret()
    if not e.lt(c, NCLS, "cls<count"):
        e.ret()
    e.hit(STATS, 0x005E4D7F, [UNIT, 12, 0], ecx=None, edx=None)


def m_fight(e):                                         # the hireling's fight step, 0x005E5050
    c = s32(e.i["cls"])
    if c == 338 or (not e.le(c, 559, "cls<=559") and e.le(c, 561, "cls<=561")):
        e.hit(DISTU, 0x005E50BE, [], ecx=UNIT, edx=TARGET)
    e.hit(STATS, 0x005E5099, [UNIT, 12, 0], ecx=None, edx=None)


def m_follow(e):                                        # the hireling's follow step, 0x005E3930
    e.hit(PLRDATA, 0x005E3952, [OWNER], ecx=None, edx=None)


def m_andariel(e):                                      # row 34, 0x005F5830
    if e.i["melee"]:
        if e.sk(1) >= 0 and e.chance(1):
            e.hit(USESKILL, 0x005F58BE, [e.skm(1), e.sk(1), T, 0, 0])
        e.hit(SETMODEAT, 0x005F58D7, [4, T])
    if e.chance(2):
        e.hit(IDLE, 0x005F592C, [5])
    if e.chance(3):
        if e.sk(1) >= 0 and e.rchance(4):
            e.hit(USESKILL, 0x005F59B0, [e.skm(1), e.sk(1), T, 0, 0])
        if e.sk(2) >= 0:
            e.hit(USESKILL, 0x005F59E3, [e.skm(2), e.sk(2), T, 0, 0])
    e.hit(PATHOVR, 0x005F59FF, [0, 0], ecx=UNIT, edx=1)


def m_duriel(e):                                        # row 44, 0x005F67B0
    if e.sk(4) >= 0:
        e.hit(GETRSKILL, 0x005F67DF, [UNIT], ecx=None, edx=None)
    if e.i["melee"] == 0:
        if e.sk(1) >= 0 and e.chance(5):
            e.hit(USESKILL, 0x005F69D5, [e.skm(1), e.sk(1), T, 0, 0])
        e.hit(PATHOVR, 0x005F69EE, [0, 0], ecx=UNIT, edx=13)
    if e.sk(3) >= 0 and e.chance(2):
        e.hit(USESKILL, 0x005F6884, [e.skm(3), e.sk(3), T, 0, 0])
    if e.sk(2) >= 0 and e.chance(3):
        e.hit(USESKILL, 0x005F68F7, [e.skm(2), e.sk(2), T, 0, 0])
    if e.chance(4):
        e.hit(SETMODEAT, 0x005F694E, [5, T])
    e.hit(SETMODEAT, 0x005F6964, [4, T])


def m_mephisto(e):                                      # row 50, 0x005F78B0
    e.hit(LIFEPCT, 0x005F78E6, [UNIT], ecx=None, edx=None)


def m_mpick(e):                                         # Mephisto's target pick, 0x005F77C0
    e.hit(SEARCH, 0x005F780B, [EBP - 0x28, 0x005F7700, 1],
          block=(EBP - 0x28, [0, 0x7FFFFFFF, 0, 0, 0x7FFFFFFF, 0, 0x7FFFFFFF, 0, 0, 0]))


def m_summoner(e):                                      # row 53, 0x005F85C0
    if e.c14 == 0:
        e.hit(BOSSSEEN, 0x005F85F2, [])
    if e.lt(e.i["dist"], 5, "dist<5") and e.chance(6):
        e.hit(STEPAWAY, 0x005F864D, [T, 6, 0])
    e.hit(STATS, 0x005F8657, [T, 43, 0], ecx=None, edx=None)


def izual_skill(e, x, y):
    e.hit(USESKILL, 0x005F8AE8, [e.skm(1), e.sk(1), T, x, y])


def m_izual(e):                                         # row 55, 0x005F89B0
    i = e.i
    x, y = e.tpos()
    if e.c14 == 0:
        e.c14 = 1
        e.hit(QUEST, 0x005F8A5C, [], edx=None)
    if e.c18 != 0:
        e.hit(IDLE, 0x005F8A71, [s32(e.c18)])
    aidel = i["aidel"][e.d()]
    if i["melee"]:
        if e.lt(0, s32(e.c1c), "v1C>0") or e.chance(1):
            if s32(e.c1c) > 0:
                e.c1c = u32(s32(e.c1c) - 1)
            e.hit(SETMODEAT, 0x005F8C73, [4, T])
        e.c1c = 0
        if e.sk(1) >= 0 and e.rchance(4):
            izual_skill(e, x, y)
        e.hit(IDLE, 0x005F8C4D, [aidel])
    if e.sk(1) >= 0 and e.lt(i["dist"], 10, "dist<10"):
        if e.lt(0, s32(e.c1c), "v1C>0"):
            e.hit(WALK, 0x005F8BA7, [T, 7])
        if e.rchance(3):
            izual_skill(e, x, y)
    if e.lt(0, s32(e.c1c), "v1C>0"):
        e.hit(WALK, 0x005F8BA7, [T, 7])
    if e.chance(2):
        e.hit(WALK, 0x005F8BA7, [T, 7])
    if e.lt(10, i["dist"], "dist>10"):
        e.hit(WTOWARD, 0x005F8B75, [T, 6, 9])
    e.hit(IDLE, 0x005F8B8E, [aidel])


def m_brinit(e):                                        # row 59's init, 0x005E6300
    e.c1c = 0
    e.ret()


def m_braven(e):                                        # row 59, 0x005E6320
    e.hit(PARAMSFIND, 0x005E6356, [0], ecx=UNIT, edx=10)


def m_griswold(e):                                      # row 90, 0x005E5AC0
    if e.i["melee"]:
        if e.cdraw(80):
            e.hit(SETMODEAT, 0x005E5B12, [4, T])
    elif e.cdraw(50):
        e.hit(WALK, 0x005E5B4B, [T, 7])
    e.hit(IDLE, 0x005E5B5B, [10])


def m_uizual(e):                                        # row 144, 0x005F8C80
    i = e.i
    s2 = e.sk(2)
    if s2 >= 0 and e.lt(s2, i["skcount"], "s2<count") and i["aura"] >= 0:
        e.hit(HASSTATE, 0x005F8D5B, [UNIT, i["aura"]], ecx=None, edx=None)
    e.hit(LINEBLK, 0x005F8D90, [UNIT, T, 6], ecx=None, edx=None)


def m_umeph(e):                                         # row 146, 0x005F81C0
    e.ret()


MODELS = {f: globals()["m_" + f] for f in FAMILIES}
CONTROLS = ("le", "d0", "cmp")


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


def seed_with_first(rnd, want):
    """A seed whose first draw is in `want` (the constant thresholds of Griswold)."""
    while True:
        seed = (rnd.randrange(1 << 32), rnd.randrange(1 << 32))
        if first_draws(seed, 1)[0] in want:
            return seed


def gen_family(fam, rnd):
    cases, meta = [], []
    for k in range(NCASES):
        seed = (rnd.randrange(1 << 32), rnd.randrange(1 << 32))
        if fam == "griswold" and rnd.randrange(4) == 0:
            seed = seed_with_first(rnd, (49, 50, 51, 79, 80, 81))
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
            "dist": rnd.choice([0, 1, 4, 5, 6, 9, 10, 11, 15, 20, rnd.randrange(0, 60)]),
            "ctl14": rnd.choice([0, 0, 1, 2, 3, 17, 18, 19, 20, -1]), "ctl18": rnd.choice([0, 0, 0, 1, 2, 7, -1]),
            "ctl1c": rnd.choice([0, 0, 1, 2, -1, 3]),
            "skill": [rnd.choice([-1, rnd.randrange(0, 400), rnd.randrange(0, 400)]) for _ in range(8)],
            "skmode": [rnd.randrange(16) for _ in range(8)],
            "aidel": [rnd.randrange(1, 16) for _ in range(3)],
            "ux": rnd.randrange(1 << 16), "uy": rnd.randrange(1 << 16),
            "umode": rnd.choice([1, 1, 1, 0, 2, 3, 12]), "state": rnd.randrange(18),
            "cls": rnd.choice([-1, 0, 271, 337, 338, 339, 359, 559, 560, 561, 562, NCLS - 1, NCLS, NCLS + 1,
                               rnd.randrange(0, NCLS)]),
            "ttype": rnd.choice([0, 1, 2, 3, 4, 5]), "tguid": rnd.randrange(1 << 32),
            "tx": rnd.randrange(1 << 16), "ty": rnd.randrange(1 << 16),
            "tpx": rnd.randrange(1 << 16), "tpy": rnd.randrange(1 << 16),
            "tpath": rnd.choice([TPATH, TPATH, TPATH, 0]),
            "skcount": rnd.choice([0x16D, 10, 100, 300]), "aura": rnd.choice([-1, 0, 12, 184, rnd.randrange(300)]),
        }
        if fam == "uizual":                      # Skill2 around the Skills count
            inp["skill"][1] = rnd.choice([-1, 0, inp["skcount"] - 1, inp["skcount"], inp["skcount"] + 1,
                                          rnd.randrange(0, 400)])
        if fam == "izual":
            inp["ctl14"] = rnd.choice([0, 1, 1, 1, 2])
            inp["ctl18"] = rnd.choice([0, 0, 0, 0, 3, -1])
        if fam == "summoner":
            inp["ctl14"] = rnd.choice([0, 1, 1, 1])
            inp["dist"] = rnd.choice([3, 4, 5, 6, inp["dist"]])
        if fam in ("duriel",) and rnd.randrange(3):
            inp["skill"][3] = -1                 # most cases past the right-skill test
        if inp["ttype"] in (2, 4, 5) and inp["tpath"] == 0:
            inp["tpath"] = TPATH                 # a static-path type always has its path read
        sk = "".join(hx16(s) for s in inp["skill"])
        skbase = u32(SKREC - (inp["skill"][1] & 0xFFFF if inp["skill"][1] >= 0 else 0) * 0x23C)
        lines = [
            "w %08x %s" % (GAME + 0x6D, "%02x" % diff),
            "w %08x %s" % (GAME + 0xA8, hx32(frame)),
            "w %08x %s" % (UNIT, hx32(1) + hx32(inp["cls"])),
            "w %08x %s" % (UNIT + 0x10, hx32(inp["umode"]) + hx32(MDATA)),
            "w %08x %s%s" % (UNIT + 0x20, hx32(seed[0]), hx32(seed[1])),
            "w %08x %s" % (UNIT + 0x2C, hx32(UPATH)),
            "w %08x %s" % (UNIT + 0xC4, hx32(0)),
            "w %08x %s" % (UPATH + 0x02, hx16(inp["ux"])), "w %08x %s" % (UPATH + 0x06, hx16(inp["uy"])),
            "w %08x %s" % (UPATH + 0x1C, hx32(ROOM)),
            "w %08x %s" % (TARGET, hx32(inp["ttype"])), "w %08x %s" % (TARGET + 0x0C, hx32(inp["tguid"])),
            "w %08x %s" % (TARGET + 0x2C, hx32(inp["tpath"])),
            "w %08x %s" % (TPATH + 0x02, hx16(inp["tx"])), "w %08x %s" % (TPATH + 0x06, hx16(inp["ty"])),
            "w %08x %s" % (TPATH + 0x0C, hx32(inp["tpx"]) + hx32(inp["tpy"])),
            "w %08x %s" % (OWNER + 0x10, hx32(2)), "w %08x %s" % (OWNER + 0x2C, hx32(OPATH)),
            "w %08x %s" % (MDATA + 0x28, hx32(CTL)), "w %08x %s" % (MDATA + 0x54, hx32(0)),
            "w %08x %s" % (CTL, hx32(inp["state"])),
            "w %08x %s%s%s%s" % (CTL + 0x14, hx32(inp["ctl14"]), hx32(inp["ctl18"]), hx32(inp["ctl1c"]), hx32(0)),
            "w %08x %s" % (CTX, hx32(CTL) + hx32(0) + hx32(TARGET) + hx32(0) + hx32(0)
                           + hx32(inp["dist"]) + hx32(inp["melee"]) + hx32(MREC) + hx32(0)),
            "w %08x %s" % (MREC + 0x4F, "".join("%02x" % a for a in inp["aidel"])),
            "w %08x %s" % (MREC + 0x56, "".join(hx16(aip[j][d]) for j in range(8) for d in range(3))),
            "w %08x %s" % (MREC + 0x170, sk + "".join("%02x" % m for m in inp["skmode"])),
            "w %08x %s" % (G_DATATABLES, hx32(DTBL)),
            "w %08x %s" % (DTBL + 0xA78, hx32(MSBASE)), "w %08x %s" % (DTBL + 0xA80, hx32(NCLS)),
            "w %08x %s" % (DTBL + 0xB98, hx32(skbase)), "w %08x %s" % (DTBL + 0xBA0, hx32(inp["skcount"])),
            "w %08x %s" % (SKREC + 0x80, hx16(inp["aura"])),
            "d %08x %d" % (STK_LO, STK_LEN), "d %08x 8" % (UNIT + 0x20), "d %08x 12" % (CTL + 0x14),
        ]
        f = FNS[fam]
        if fam == "pick":                        # (ECX game, EDX unit; class, hireling id, target, seed)
            lines.append("call %08x %08x %08x %08x %08x %08x %08x" % (f, GAME, UNIT, u32(inp["cls"]), 0x77, TARGET,
                                                                     UNIT + 0x20))
        elif fam == "fight":                     # (ECX game, EDX unit; class, owner, target, seed, ctx)
            lines.append("call %08x %08x %08x %08x %08x %08x %08x %08x" % (f, GAME, UNIT, u32(inp["cls"]), OWNER,
                                                                          TARGET, UNIT + 0x20, CTX))
        elif fam == "follow":                    # (ECX game, EDX owner; unit, kind, a, b, c)
            lines.append("call %08x %08x %08x %08x %08x %08x %08x %08x" % (f, GAME, OWNER, UNIT, rnd.choice([0, 1, 3]),
                                                                          rnd.randrange(2), 0x3C, 0))
        elif fam == "mpick":                     # (ECX game, EDX unit; MonStats record, target)
            lines.append("call %08x %08x %08x %08x %08x" % (f, GAME, UNIT, MREC, TARGET))
        else:
            lines.append("call %08x %08x %08x %08x" % (f, GAME, UNIT, CTX))
        cases.append(lines)
        meta.append(inp)
    mem = ["observe %08x" % a for a in OBSERVE if a != FNS[fam]] + ["guard %08x" % a for a in FATAL + ALLOC]
    return cases, meta, mem


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        cases, meta, mem = gen_family(fam, random.Random("r52g-" + fam))
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
    fn, site, ecx, edx, args, seed, c14, c18, c1c, block = want
    if c.get("obs") != fn:
        return False
    gseed = list(struct.unpack("<II", c["dumps"][UNIT + 0x20]))
    g14, g18, g1c = struct.unpack("<III", c["dumps"][CTL + 0x14])
    ok = gseed == seed and g14 == c14 and g18 == c18 and g1c == c1c
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
    _, meta, _ = gen_family(fam, random.Random("r52g-" + fam))
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
    line = ("AI52G %s cases=%d match=%d bad=%d stopped=%d traced=%d drew=%d " % (
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
    print("AI52G total cases=%d match=%d" % tuple(tot))
    print("AI52G result=%s" % ("ok" if allok else "FAIL"))


def cmd_manifest(d, write):
    rows = []
    for fam in FAMILIES:
        for ext in ("cases", "mem", "out", "err"):
            p = os.path.join(d, "%s.%s" % (fam, ext))
            if os.path.exists(p):
                rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.basename(p)))
    for extra in ("check.txt", "ai_cat_emu6.py.rev"):
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

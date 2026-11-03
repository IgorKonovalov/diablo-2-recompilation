#!/usr/bin/env python3
"""Plan 0052 phase 1.2, catalogue batch 12 (towns, NPCs and the state rows, `lane/r52l`): the think and init functions of
AI rows 31, 32, 41, 42, 54, 58, 62, 81, 88, 91, 99, 100 and of state rows 2, 3, 8-14, 17 (row 60 is state row 5's think,
emulated by batch 6), and the town helpers they reach, run under Ghidra's p-code emulator (ADR-0015, ADR-0021) with
re/ghidra_scripts/EmuBoundary.java and compared with the models below. No game run, no slot. Same method as
tools/ai_cat_emu11.py (batch 11): one family per function, the `le`, `d0`, `cmp`, `u16` controls, the site control, the
EDGES line per family. Additions of this batch: `lo8` (the low-byte draws of state row 2 read mod 100), `arg` (the
`al` return of a helper flipped), memory checks at a boundary or return (`mem`: a parameter record, an out word, a frame
local).

    python3 -I tools/ai_cat_emu12.py cases [--dir D]      write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/ai_cat_emu12.py check [--dir D]      compare every D/<family>.out with its model, account for
                                                          every traced access, run the negative and site controls
    python3 -I tools/ai_cat_emu12.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r52l/emu. Every case draw comes from random.Random("r52l-<family>"), so `cases` regenerates
identical files.

The declared image: the game's difficulty byte (+0x6D) and frame (+0xA8); the unit's type (+0x00, 1), class (+0x04),
guid (+0x0C), mode (+0x10), monster data (+0x14), seed (+0x20/+0x24), path (+0x2C or 0), +0xC4 and hash next (+0xE4);
the unit path's u16 x (+0x02), y (+0x06), room (+0x1C); the target's type, class, guid, mode, path (+0x2C), that path's u16 x, y,
the static words +0x0C/+0x10 and room (+0x1C); the owner unit (0x12E10000: type 1, guid, path = the target's); the
monster data's AI control (+0x28), interact list pointer (+0x30, a head word whose nodes hold a word at +0x00 and next at
+0x08) and the word +0x54; the AI control's state, +0x14, +0x18, +0x1C, the parameter ring (+0x20, nodes at 0x13100000 + 0x40 k:
+0x00 next, +0x08 kind, +0x0C, +0x10, +0x14, +0x18), the owner words +0x28/+0x2C/+0x30 and the path list +0x38 ({count,
nodes}, 12-byte nodes {action, x, y}); the AiCtx (+0x00 ctl, +0x08 target, +0x14 distance, +0x18 melee, +0x1C MonStats
record); the MonStats record's byte +0x0D and Skill1 (+0x170); DataTables (0x00744304) +0xA78, +0xA80, +0xBA0; the
counter 0x0088CADC.

Callees that run on the declared image (not boundaries): AiParamsFind 0x0058EEF0, AiCtlParamGet 0x0058EFA0 (its find branch),
AiParamsHead 0x0058EE80, the position getters 0x0045ADF0, 0x0045AE20, 0x00620870 with 0x006488C0, 0x00648900; UnitGetRoom
0x00620BB0 with 0x00648A80; AiDistUnits 0x005DC380; AiPathDistToPoint 0x005DC5C0; AiMonState3or19 0x005DD2B0 with 0x005734E0;
MonsterOwner 0x0058F0D0 with GameFindUnit 0x00552F60; RNG_Range 0x0045C390, RNG_RangeB 0x0045C3E0; the list tests 0x00572DC0
and 0x00572DE0; UNIT_GetSizeX 0x00620510 with no MonStats2 row (the declared MonStats +0x18 is -1, so AiDistUnits subtracts its no-record value, the size branch unreached); the batch's helpers 0x005E6800, 0x005E6860, 0x005E6AE0, 0x005E7080 (with the handlers 0x005E6DE0, 0x005E6E80,
0x005E6EF0, 0x005E6F00, 0x005E6FC0), 0x005E7350, 0x005E77A0 and 0x005DDF20 when they are reached from another function. Every
other callee is an observed boundary. The claim per case: the first boundary reached (or the function's return with its EAX or
AL), its call site, the registers and stack arguments the callee takes, the unit seed, the AI control's +0x14/+0x18/+0x1C and the
named memory words.

Not covered (ADR-0021): every callee at or after a boundary and so every branch that a boundary call's result decides. Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r52l", "emu")

MUL = 0x6AC690C5
GAME, UNIT, UPATH, ROOM, TARGET, MDATA, CTX, CTL = (0x12000000, 0x12100000, 0x12200000, 0x12300000, 0x12400000,
                                                    0x12500000, 0x12700000, 0x12800000)
MS2, DTBL, TPATH, TROOM, OWNER = 0x12900000, 0x12A00000, 0x12B00000, 0x12B10000, 0x12E10000
MSBASE, PRM, WTS, NL, LIST, NODES = 0x13000000, 0x13100000, 0x13200000, 0x13300000, 0x13400000, 0x13410000
G_DATATABLES, G_COUNTER = 0x00744304, 0x0088CADC
HASHOFF = (0x1120, 0x1320, 0x1520, 0x1920, 0x1720)
STK_LO, STK_LEN, EBP = 0x7FEFFC00, 1040, 0x7FEFFFFC
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)

IDLE, SETMODE, SETMODEAT, WALKPT, WANDNEAR, RING, WALKTOW, WALKU = (0x005DE080, 0x005DDFC0, 0x005DDF90, 0x005DED90,
                                                                    0x005DF530, 0x005DE200, 0x005DE6D0, 0x005DEC80)
OVERRIDE, PARAMSPUSH, SEARCH, FINDHOST, H68F0, MONINIT, MODEOK, ROOMTOWN = (0x005DE190, 0x0058EF40, 0x005DD0B0, 0x005DDC30,
                                                                           0x005E68F0, 0x005B0E00, 0x0046C140, 0x0061AB00)
GETTGT, HASSTATE, GROUPEACH, F160, LOGICID, USESKILL, ISDEATH, WALKTGT = (0x00553540, 0x00639DF0, 0x0058F380, 0x0058F160,
                                                                         0x0061B130, 0x005DEAD0, 0x0063EA40, 0x005BD0D0)
PATHFACE, C544 = 0x00648820, 0x00544590
Q_JERHYN, Q_ALKOR, Q_ORMUS, Q_CAIN, Q_ANYA, Q_TYRAEL, Q_IZUAL, Q_GUARD, Q_CAINPT, Q_ANYAPT, Q_ANYA2 = (
    0x0059F570, 0x005BAD20, 0x005B9CA0, 0x00594360, 0x0058BC80, 0x0059DF50, 0x005B43F0, 0x0059B8B0, 0x005944B0,
    0x0058A940, 0x0058AA10)
EXTRA = (0x00457490, 0x00472210, 0x00535060, 0x00540E60, 0x005417D0, 0x00553380, 0x00573090, 0x00573120, 0x0058A9F0,
         0x0058ED10, 0x0058F730, 0x005945F0, 0x0059AEC0, 0x0059B6E0, 0x0059B8F0, 0x0059C750, 0x0059F580, 0x005A6260,
         0x005B4440, 0x005B9CD0, 0x005BAD40, 0x005BD4A0, 0x005DD7F0, 0x005DE890, 0x005DED20, 0x005DED40, 0x005DEDE0,
         0x005DEE50, 0x005DEF30, 0x005DEFE0, 0x005DF140, 0x005DF7D0, 0x00620C10, 0x00622C40, 0x00627260, 0x00648730,
         0x005944F0, 0x0058A980, 0x00594450, 0x0058A8D0, 0x005943B0, 0x0058A820)
OBSERVE = tuple(sorted(set((IDLE, SETMODE, SETMODEAT, WALKPT, WANDNEAR, RING, WALKTOW, WALKU, OVERRIDE, PARAMSPUSH, SEARCH,
                            FINDHOST, H68F0, MONINIT, MODEOK, ROOMTOWN, GETTGT, HASSTATE, GROUPEACH, F160, LOGICID,
                            USESKILL, ISDEATH, WALKTGT, PATHFACE, C544, Q_JERHYN, Q_ALKOR, Q_ORMUS, Q_CAIN, Q_ANYA,
                            Q_TYRAEL, Q_IZUAL, Q_GUARD, Q_CAINPT, Q_ANYAPT, Q_ANYA2) + EXTRA)))
RET = "ret"

FNS = {"npc": 0x005E7130, "nstat": 0x005E73A0, "towner": 0x005E7540, "jarjar": 0x005E7590, "oot": 0x005E7880,
       "trogue": 0x005E7D60, "st8": 0x005E7DC0, "navi": 0x005E7E20, "buffy": 0x005E7F50, "st9": 0x005E7F80,
       "st10": 0x005E8020, "st11i": 0x005E80E0, "st11": 0x005E8140, "st12": 0x005E8340, "vendor": 0x005E9E00,
       "soul": 0x005E9F10, "illus": 0x005EA080, "dark": 0x005EA130, "st2": 0x005B14E0, "st3i": 0x005E5730,
       "st3": 0x005E5870, "st13": 0x005E5C50, "st14": 0x005E2610,
       "h6800": 0x005E6800, "h6860": 0x005E6860, "h6ae0": 0x005E6AE0, "h7080": 0x005E7080, "act1": 0x005E6DE0,
       "act2": 0x005E6E80, "act3": 0x005E6EF0, "act4": 0x005E6F00, "act5": 0x005E6FC0, "h7350": 0x005E7350,
       "h77a0": 0x005E77A0, "h5b70": 0x005E5B70, "h5710": 0x005E5710, "h7d30": 0x005E7D30, "hp": 0x005DDF20,
       "hcb": 0x005DDE80, "il0": 0x00572DC0, "il1": 0x00572DE0}
FAMILIES = tuple(FNS)
NCASES = 240
CONTROLS = ("le", "d0", "cmp", "u16", "lo8", "arg")


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


def slot_addr(typ, guid):
    return GAME + 0x1B20 if typ == 5 else GAME + HASHOFF[typ] + 4 * (guid & 0x7F)


class Hit(Exception):
    pass


def C(addr):
    return addr + 5


class Env:
    def __init__(self, inp, neg=None):
        self.i, self.neg = inp, neg
        self.seed = list(inp["seed"])
        self.c14, self.c18, self.c1c = inp["ctl14"], inp["ctl18"], inp["ctl1c"]
        self.eq, self.reads, self.tags = set(), set(), set()
        self.mem = []

    def lt(self, a, b, edge):
        if a == b:
            self.eq.add(edge)
        return a <= b if self.neg == "cmp" else a < b

    def le(self, a, b, edge):
        if a == b:
            self.eq.add(edge)
        return a < b if self.neg == "cmp" else a <= b

    def dlt(self, a, b, edge):
        if a == b:
            self.eq.add(edge)
        return a <= b if self.neg == "le" else a < b

    def draw(self):
        step(self.seed)
        return self.seed[0] % 100

    def rng(self, n):
        n = s32(n)
        if n <= 0:
            return 0
        step(self.seed)
        return self.seed[0] & (n - 1) if n & (n - 1) == 0 else self.seed[0] % n

    def upos(self):
        return (0, 0) if self.i["upnull"] else (self.i["ux"], self.i["uy"])

    def tpos(self):
        i = self.i
        if i["ttype"] in (2, 4, 5):
            return i["tsx"], i["tsy"]
        return (0, 0) if i["tpnull"] else (i["tx"], i["ty"])

    def pdist(self, x, y):                  # AiPathDistToPoint 0x005DC5C0 and AiDistUnits' shape
        ux, uy = self.upos()
        dx, dy = s32(ux - x), s32(uy - y)
        dx = s32(-dx) if dx < 0 else dx
        dy = s32(-dy) if dy < 0 else dy
        v = s32(dy + 2 * dx) if dx > dy else s32(dx + 2 * dy)
        return s32(int(v / 2)) if v < 0 else v >> 1

    def params(self, kind):                 # AiParamsFind(U, kind, 0): the node index or None
        ring = self.i["ring"]
        if not ring:
            return None
        n = len(ring)
        k = 1 % n
        while True:
            if ring[k][0] == kind:
                return k
            if k == 0:
                return None
            k = (k + 1) % n

    def get(self, kind):                    # AiCtlParamGet: absent pushes a record (the boundary)
        k = self.params(kind)
        if k is None:
            self.hit(PARAMSPUSH, C(0x0058EFD8), [None], ecx=GAME, edx=UNIT)
        return k

    def wr(self, addr, val):
        self.mem = [m for m in self.mem if m[0] != addr] + [(addr, u32(val))]

    def hit(self, fn, site, args, ecx=GAME, edx=UNIT, regs=None, eax=None, al=None):
        raise Hit((fn, site, ecx, edx, [None if a is None else u32(a) for a in args], list(self.seed), u32(self.c14),
                   u32(self.c18), u32(self.c1c), tuple(self.mem), regs or {}, eax, al))

    def ret(self, eax=None, al=None):
        if al is not None and self.neg == "arg":
            al ^= 1
        self.hit(RET, 0, [], eax=eax, al=al)


class Back(Exception):                      # a helper running on the image returned its AL to the caller
    def __init__(self, al):
        self.al = al


R = lambda k: PRM + 0x40 * k


def f6800(e):                               # 0x005E6800: true when it idled (never returns true: the Idle is the boundary)
    k = e.get(10)
    _, x, y, _, _ = e.i["ring"][k]
    if x == 0 and y == 0:
        ux, uy = e.upos()
        e.wr(R(k) + 0x0C, ux)
        e.wr(R(k) + 0x10, uy)
        e.tags.add("home-saved")
        e.hit(IDLE, C(0x005E683C), [20])
    return 0


def f6ae0(e):                               # 0x005E6AE0: kinds 4, 5, 7; returns AL
    i = e.i
    k = e.params(4)
    if k is not None and e.lt(0, s32(i["ring"][k][3]), "4.w14>0"):
        _, x, y, _, w18 = i["ring"][k]
        if x != 0 and y != 0 and not e.le(u32(e.pdist(x, y)), 3, "4.d<=3"):
            if i["g88"] & 3 == 0:
                e.hit(OVERRIDE, C(0x005E6B42), [0, 0], ecx=UNIT, edx=5)
            e.hit(OVERRIDE, C(0x005E6B56), [0, 0], ecx=UNIT, edx=1)
        e.hit(IDLE, C(0x005E6B87), [w18])
    k = e.params(5)
    if k is not None:
        _, a, _, w14, w18 = i["ring"][k]
        a = s32(a)
        if a <= 0:
            if e.lt(0, s32(w14), "5.w14>0"):
                e.hit(IDLE, C(0x005E6C6B), [w18])
        elif a & 1:
            e.hit(RING, C(0x005E6BD1), [i["ring"][k][2] & 0xFF])
        else:
            if e.lt(0, s32(w14), "5.w14>0"):
                e.hit(IDLE, C(0x005E6BF0), [w18])
            e.wr(R(k) + 0x0C, a - 1)
    k = e.params(7)
    if k is None or i["ring"][k][1] == 0:
        return 0
    _, m, x, y, w18 = i["ring"][k]
    if m not in (8, 9, 10, 11):
        e.wr(R(k) + 0x0C, 0)
        e.hit(IDLE, C(0x005E6C50), [50])
    d = e.pdist(x, y)
    if e.lt(0, d, "7.d>0"):
        if e.lt(0, s32(w18), "7.w18>0"):
            e.hit(OVERRIDE, C(0x005E6C9F), [0, 0], ecx=UNIT, edx=7)
        if not e.le(d, 1, "7.d<=1"):
            m = 0
            e.wr(R(k) + 0x0C, 0)
    c = i["cls"]
    if c == 0x9A:
        e.hit(PATHFACE, C(0x005E6CF3), [UPATH, 0x38], ecx=None, edx=None)
    if c == 0x9B:
        e.hit(PATHFACE, C(0x005E6D08), [UPATH, 0x34], ecx=None, edx=None)
    if c == 0xB2:
        e.hit(PATHFACE, C(0x005E6D1C), [UPATH, 4], ecx=None, edx=None)
    if c == 0x195:
        if m == 8:
            e.hit(PATHFACE, C(0x005E6D36), [UPATH, 0x34], ecx=None, edx=None)
        if m == 9:
            e.hit(PATHFACE, C(0x005E6D47), [UPATH, 0x30], ecx=None, edx=None)
    if c == 0x1FF and not e.le(e.rng(100), 4, "1ff.r<=4"):
        e.wr(R(k) + 0x0C, 0)
        e.hit(IDLE, C(0x005E6C50), [50])
    if m != 0:
        if i["umode"] == m:
            e.hit(IDLE, C(0x005E6D87), [50])
        e.hit(SETMODEAT, C(0x005E6D96), [m, UNIT])
    return 0


def fact(e, a, node):                       # the handlers of 0x00741D74; returns AL
    x, y = node[1], node[2]
    n = NODES + 12 * e.i["nodeidx"]
    if x == 0 or y == 0:
        return 0
    if u32(e.pdist(x, y)) != 0:
        e.hit(OVERRIDE, C(0x005E6E1C), [0, 0], ecx=UNIT, edx=7)
    al = 0
    if a == 2:
        k = e.get(4)
        e.wr(R(k) + 0x0C, x); e.wr(R(k) + 0x10, y); e.wr(R(k) + 0x14, 0x14); e.wr(R(k) + 0x18, 10)
    elif a in (4, 5):
        k = e.get(7)
        if a == 4:
            e.hit(MODEOK, C(0x005E6F5B), [], ecx=e.i["cls"], edx=8)
        e.hit(MODEOK, C(0x005E701B), [], ecx=e.i["cls"], edx=9)
    return al


def f7080(e):                               # 0x005E7080; returns AL
    i = e.i
    if not i["c38"]:
        return 0
    if not e.dlt(e.draw(), 66, "7080.r<66"):
        return 0
    cnt = i["lcount"]
    if cnt == 0:
        return 0
    k = e.rng(cnt)
    e.i["nodeidx"] = k
    node = i["nodes"][k]
    a = s32(node[0])
    e.reads.add((0x005E70FB, 0x00741D74 + 4 * a)) if 0 <= a < 7 else None
    if a < 0 or a >= 7 or a in (0, 6):
        return 0
    return fact(e, a, node)


def fhp(e, site):                           # 0x005DDF20: returns 0 with no room (a search otherwise, the boundary)
    if e.i["upnull"]:
        return 0
    e.hit(SEARCH, C(0x005DDF5B), [None, 0x005DDE80, 2])


def m_npc(e):
    f6800(e)
    c, i = e.i["cls"], e.i
    if c == 201:
        e.hit(Q_JERHYN, C(0x005E71AB), [], edx=None)
    if c == 254:
        e.hit(Q_ALKOR, C(0x005E717D), [], edx=None)
    if c == 255:
        e.hit(Q_ORMUS, C(0x005E724A), [], edx=EBP - 0x10)
    if c == 0x109:
        e.hit(Q_CAIN, C(0x005E72C2), [EBP - 0x10])
    if c == 0x200:
        e.hit(Q_ANYA, C(0x005E72B3), [])
    e.hit(H68F0, C(0x005E730B), [CTX])


def m_nstat(e):
    r = fhp(e, 0)
    c = e.i["cls"]
    if c == 0xFB:
        e.hit(Q_TYRAEL, C(0x005E74B5), [])
    if c == 0x196:
        e.hit(Q_IZUAL, C(0x005E74F9), [])
    e.hit(IDLE, C(0x005E7456), [20])


def m_towner(e):
    f6800(e)
    if f6ae0(e):
        e.ret()
    if f7080(e):
        e.ret()
    e.hit(IDLE, C(0x005E7579), [12])


def m_jarjar(e):
    f6800(e)
    e.hit(Q_GUARD, C(0x005E75C0), [], edx=None)


def m_oot(e):
    i = e.i
    anya = i["cls"] == 0x20F
    k = e.get(3)
    _, x, y, _, _ = i["ring"][k]
    if x == 0 and y == 0:
        ux, uy = e.upos()
        e.wr(R(k) + 0x0C, ux + 3)
        e.wr(R(k) + 0x10, uy + 3)
        e.hit(Q_ANYAPT if anya else Q_CAINPT, 0x005E7817, [])
    if anya:
        e.hit(Q_ANYA2, C(0x005E78B9), [], edx=None)
    if i["nl"]:
        e.hit(IDLE, C(0x005E78E4), [40])
    if i["umode"] == 12:
        e.ret()
    e.hit(H68F0, C(0x005E7918), [CTX])


def m_h77a0(e):
    i = e.i
    k = e.get(3)
    _, x, y, _, _ = i["ring"][k]
    if x == 0 and y == 0:
        ux, uy = e.upos()
        e.wr(R(k) + 0x0C, ux + 3)
        e.wr(R(k) + 0x10, uy + 3)
        e.hit(Q_ANYAPT if i["cls"] == 0x20F else Q_CAINPT, 0x005E7817, [])
    e.ret(eax=0)


def m_trogue(e, site=0x005E7D85):
    i = e.i
    e.wr(EBP + 8, i["dist"])
    e.wr(EBP - 4, i["melee"])
    e.hit(FINDHOST, C(site), [EBP + 8, EBP - 4])


def m_st8(e):
    m_trogue(e, 0x005E7DE5)


def m_navi(e):
    if e.i["nl"]:
        e.hit(IDLE, C(0x005E7E54), [10])
    if not e.i["upnull"]:
        e.hit(SEARCH, C(0x005DDF5B), [None, 0x005DDE80, 2])
    e.hit(FINDHOST, C(0x005E7F0A), [EBP - 8, EBP - 0xC])


def m_buffy(e):
    if e.i["upnull"]:
        e.ret()
    e.hit(IDLE, C(0x005E7F69), [200])


def m_st9(e):
    if e.head_kind() == 8:
        e.hit(F160, C(0x005E7FA9), [], ecx=UNIT, edx=None)
    e.wr(EBP + 8, 0)
    e.hit(GROUPEACH, C(0x005E7FC8), [0, 0x005E5710], ecx=UNIT, edx=EBP + 8)


def m_st3(e):
    if e.head_kind() == 8:
        e.hit(F160, C(0x005E5A93), [], ecx=UNIT, edx=None)
    e.wr(EBP - 0x10, 0)
    e.hit(GROUPEACH, C(0x005E58B2), [0, 0x005E5710], ecx=UNIT, edx=EBP - 0x10)


def head_kind(self):
    return self.i["ring"][0][0] if self.i["ring"] else None


Env.head_kind = head_kind


def m_st10(e):
    i = e.i
    if i["melee"]:
        c = s32(i["cls"])
        e.reads.add((0x005E8063, 0x006CE26C)) if 0 <= c < s32(i["mscount"]) else None
        if not (0 <= c < s32(i["mscount"]) and i["ms0d"] & 2):
            e.hit(MODEOK, C(0x005E80B4), [], ecx=i["cls"], edx=4)
    if e.dlt(e.draw(), 20, "r<20"):
        e.hit(RING, C(0x005E80A0), [3])
    e.hit(IDLE, C(0x005E80D2), [10])


def m_st11i(e):
    e.hit(GETTGT, C(0x005E80E5), [GAME, UNIT], ecx=None, edx=None)


def m_st11(e):
    e.hit(HASSTATE, C(0x005E816A), [UNIT, 0x38], ecx=None, edx=None)


def m_st12(e):
    e.hit(GETTGT, C(0x005E834F), [GAME, UNIT], ecx=None, edx=None)


def m_vendor(e):
    if e.dlt(e.draw(), 20, "r<20"):
        e.hit(SETMODE, C(0x005E9E3A), [8, 0, 0])
    e.hit(IDLE, C(0x005E9E47), [30])


def m_soul(e):
    i = e.i
    e.wr(UNIT + 0xC4, i["c4"] | 0x20000)
    t = 0 if i["tnull"] else TARGET
    if t == 0 or not e.lt(i["dist"], 5, "dist<5"):
        if i["ctl14"] != 0:
            e.hit(SETMODEAT, C(0x005EA05B), [8, t])
        e.hit(IDLE, C(0x005EA06B), [15])
    if i["ctl14"] == 0:
        e.c14, e.c18 = 1, i["frame"]
        e.hit(SETMODEAT, C(0x005E9F7E), [9, t])
    if i["melee"] == 0 or e.le(s32(i["frame"]), s32(i["ctl18"]), "frame<=c18"):
        e.hit(SETMODEAT, C(0x005EA03D), [8, t])
    ux, uy = e.upos()
    tx, ty = e.tpos()
    ux, uy, tx, ty = u32(ux), u32(uy), u32(tx), u32(ty)
    if ux == tx:
        e.eq.add("ux=tx")
    if uy == ty:
        e.eq.add("uy=ty")
    if ux >= tx and uy <= ty:
        e.hit(SETMODEAT, C(0x005E9FC8), [4, t])
    if ux > tx or uy < ty:
        e.hit(SETMODEAT, C(0x005EA019), [8, t])
    e.hit(SETMODEAT, C(0x005E9FF5), [5, t])


def m_illus(e):
    i = e.i
    if i["ctl18"] == 1:
        e.wr(UNIT + 0xC4, i["c4"] | 0x20000)
        e.hit(SETMODE, C(0x005EA0AA), [0, 0, 0])
    ux, uy = e.upos()
    e.hit(SETMODE, C(0x005EA11A), [4, ux - 10, uy])


def m_dark(e):
    e.hit(WALKTGT, C(0x005EA156), [EBP - 0xC])


def m_st2(e):
    i = e.i
    if i["m54"] in (3, 19) or e.lt(i["dist"], 4, "dist<4"):
        e.hit(MONINIT, C(0x005B15B3), [CTL, 0])
    if e.lt(10, i["dist"], "dist>10") and i["ctl14"] == 0:
        e.c14 = 1
        e.hit(WANDNEAR, C(0x005B152E), [TARGET, 12])
    step(e.seed)
    v = e.seed[0] % 100 if e.neg == "lo8" else e.seed[0] & 0xFF
    if e.dlt(v, 0x4D, "a<0x4D"):
        e.hit(RING, C(0x005B1566), [4])
    step(e.seed)
    v = e.seed[0] % 100 if e.neg == "lo8" else e.seed[0] & 0xFF
    if e.dlt(v, 0x1A, "b<0x1A"):
        e.c14 = 0
    e.hit(IDLE, C(0x005B1599), [10])


def m_st3i(e):
    i = e.i
    e.reads.add((0x00552F9C, 0x006E10E4))    # GameFindUnit's slot table, type 1
    ux, uy = e.upos()
    if i["selfowner"]:
        ox, oy = ux, uy
    else:
        ox, oy = i["tx"], i["ty"]
    e.c14, e.c18 = ux - ox, uy - oy
    if i["selfowner"]:
        e.c1c = e.draw()
    e.ret()


def m_st13(e):
    i = e.i
    if i["msnull"] or i["upnull"]:
        e.ret()
    k = e.params(10)
    if k is None:
        e.hit(PARAMSPUSH, C(0x005E5CCB), [EBP - 0x38])
    _, x, y, _, _ = i["ring"][k]
    if x == 0 or y == 0:
        x, y = e.upos()
        e.wr(R(k) + 0x0C, x)
        e.wr(R(k) + 0x10, y)
    e.hit(LOGICID, C(0x005E5D4F), [ROOM, x, y], ecx=None, edx=None)


def m_st14(e):
    i = e.i
    r = e.draw()
    if i["melee"]:
        if e.dlt(r, 95, "melee r<95"):
            step(e.seed)
            e.hit(SETMODEAT, C(0x005E2677), [5, TARGET])
    elif e.dlt(r, 89, "r<89"):
        e.hit(WALKU, C(0x005E26B1), [TARGET, 0])
    e.hit(IDLE, C(0x005E26C1), [10])


def m_h6800(e):
    f6800(e)
    e.ret(al=0)


def m_h6860(e):
    i = e.i
    k = e.params(10)
    if k is None:
        k = e.get(10)                       # 0x005E6800 pushes
    _, x, y, _, _ = i["ring"][k]
    if e.le(u32(e.pdist(x, y)), u32(i["n"]), "d<=n"):
        e.ret(al=0)
    h = e.get(4)
    e.wr(R(h) + 0x0C, x); e.wr(R(h) + 0x10, y); e.wr(R(h) + 0x14, 12); e.wr(R(h) + 0x18, 10)
    e.hit(IDLE, C(0x005E68D6), [10])


def m_h6ae0(e):
    e.ret(al=f6ae0(e))


def m_h7080(e):
    e.ret(al=f7080(e))


def m_act(e):
    a = int(e.i["fam"][3])
    e.i["nodeidx"] = 0
    e.ret(al=fact(e, a, e.i["nodes"][0]))


def m_h7350(e):
    if e.i["nl"]:
        e.ret(eax=0)
    e.hit(SETMODE, C(0x005E737F), [0, 0, 0])


def m_h77a0_(e):
    m_h77a0(e)


def m_h5b70(e):
    i = e.i
    c14 = s32(i["ctl14"])
    if not i["c38"] or not e.lt(c14, s32(i["lcount"]), "c14<count"):
        d = s32(i["frame"] - i["ctl18"])
        d = s32(-d) if d < 0 else d
        if not e.le(d, 700, "d<=700"):
            e.c14 = 0
        e.ret(eax=0)
    c = s32(i["cls"])
    if c < 0 or c >= s32(i["mscount"]):
        e.ret(eax=0)
    sk = s16(i["sk1"])
    if e.neg == "u16":
        sk = i["sk1"] & 0xFFFF
    if sk < 0 or sk >= i["skcount"]:
        e.ret(eax=0)
    _, x, y = i["nodes"][c14] if c14 < len(i["nodes"]) else (0, 0, 0)      # only the `cmp` control reaches the else
    e.hit(USESKILL, C(0x005E5BFD), [4, sk, 0, x, y])


def m_h5710(e):
    if e.i["tnull"]:
        e.wr(WTS, 1)
        e.ret()
    e.hit(ISDEATH, C(0x005E5718), [TARGET], ecx=None, edx=None)


def m_h7d30(e):
    if e.i["tnull"] or e.i["tpnull"]:
        e.ret(eax=1)
    e.hit(ROOMTOWN, C(0x005E7D45), [TROOM], ecx=None, edx=None)


def m_hp(e):
    if e.i["upnull"]:
        e.ret(eax=0)
    e.wr(EBP - 0x28, 0)
    e.wr(EBP - 0x24, 0x7FFFFFFF)
    e.hit(SEARCH, C(0x005DDF5B), [EBP - 0x28, 0x005DDE80, 2])


def m_hcb(e):
    i = e.i
    if i["tnull"] or i["ttype"] != 0:
        e.ret(eax=0)
    e.reads.add((0x00620521, 0x00620580))    # UNIT_GetSizeX's jump table, type 1
    tx, ty = e.tpos()
    d = e.pdist(tx, ty)                     # AiDistUnits with the declared size 0
    if not e.le(d, 15, "d<=15"):
        e.ret(eax=0)
    c = s32(i["cls"])
    if 0 <= c < s32(i["mscount"]):
        e.reads.add((0x005DDEDF, 0x006CE26C))
        if i["ms0d"] & 2:
            e.hit(C544, C(0x005DDF00), [UNIT], edx=TARGET)
    e.wr(WTS, TARGET)
    e.wr(WTS + 4, d)
    e.ret(eax=TARGET)


def m_il0(e):
    e.ret(eax=int(any(w != 0 for w in e.i["nlw"])))


def m_il1(e):
    e.ret(eax=int(e.i["needle"] in e.i["nlw"]))


MODELS = {"npc": m_npc, "nstat": m_nstat, "towner": m_towner, "jarjar": m_jarjar, "oot": m_oot, "trogue": m_trogue,
          "st8": m_st8, "navi": m_navi, "buffy": m_buffy, "st9": m_st9, "st10": m_st10, "st11i": m_st11i, "st11": m_st11,
          "st12": m_st12, "vendor": m_vendor, "soul": m_soul, "illus": m_illus, "dark": m_dark, "st2": m_st2,
          "st3i": m_st3i, "st3": m_st3, "st13": m_st13, "st14": m_st14, "h6800": m_h6800, "h6860": m_h6860,
          "h6ae0": m_h6ae0, "h7080": m_h7080, "act1": m_act, "act2": m_act, "act3": m_act, "act4": m_act, "act5": m_act,
          "h7350": m_h7350, "h77a0": m_h77a0_, "h5b70": m_h5b70, "h5710": m_h5710, "h7d30": m_h7d30, "hp": m_hp,
          "hcb": m_hcb, "il0": m_il0, "il1": m_il1}


def run_model(inp, neg=None, edges=None, reads=None, tags=None):
    inp = dict(inp)
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
DRAW_EDGES = {"vendor": (20,), "st10": (20,), "st14": (95, 89), "h7080": (66,), "towner": (66,)}


def edge_seed(fam, rnd, k):
    """A seed whose first draw (mod 100) sits on one of the family's limits; state row 2: low byte 0x4D, or above it and then 0x1A."""
    want = DRAW_EDGES[fam][(k // 4) % len(DRAW_EDGES[fam])]
    while True:
        seed = [rnd.randrange(1 << 32), rnd.randrange(1 << 32)]
        s = list(seed)
        step(s)
        if s[0] % 100 == want:
            return tuple(seed)


def edge_seed_st2(rnd, k):
    while True:
        seed = [rnd.randrange(1 << 32), rnd.randrange(1 << 32)]
        s = list(seed)
        step(s)
        a = s[0] & 0xFF
        step(s)
        if (k // 4) % 2 == 0 and a == 0x4D:
            return tuple(seed)
        if (k // 4) % 2 == 1 and a > 0x4D and s[0] & 0xFF == 0x1A:
            return tuple(seed)


def gen_family(fam, rnd):
    cases, meta = [], []
    for k in range(NCASES):
        seed = (rnd.randrange(1 << 32), rnd.randrange(1 << 32))
        if k % 4 == 0 and fam in DRAW_EDGES:         # a quarter of the cases sit on a draw's edge
            seed = edge_seed(fam, rnd, k)
        if k % 4 == 0 and fam == "st2":
            seed = edge_seed_st2(rnd, k)
        cls = rnd.choice([201, 254, 255, 0x109, 0x200, 0xFB, 0x196, 0x20F, 0x9A, 0x9B, 0xB2, 0x195, 0x1FF, 146, 266,
                          rnd.randrange(0x2E0), rnd.randrange(0x2E0)])
        ux, uy = rnd.randrange(0x100, 0xFF00), rnd.randrange(0x100, 0xFF00)
        near = lambda v, r: (v + rnd.randrange(-r, r + 1)) & 0xFFFF
        inp = {
            "fam": fam, "seed": seed, "diff": k % 3, "frame": rnd.randrange(100, 100000), "cls": cls,
            "melee": rnd.randrange(2), "dist": rnd.choice([0, 3, 4, 5, 10, 11, 19, 20, 24, 25, rnd.randrange(60)]),
            "ctl14": rnd.choice([0, 0, 1, 2, 3, 5, rnd.randrange(1 << 32)]),
            "ctl18": rnd.choice([0, 0, 1, 2, -1 & 0xFFFFFFFF, rnd.randrange(1 << 32)]),
            "ctl1c": rnd.choice([0, 1, rnd.randrange(100)]),
            "ux": ux, "uy": uy, "upnull": 0, "tx": rnd.choice([ux, near(ux, 40), rnd.randrange(1 << 16)]),
            "ty": rnd.choice([uy, near(uy, 40), rnd.randrange(1 << 16)]), "tsx": rnd.randrange(1 << 16),
            "tsy": rnd.randrange(1 << 16), "ttype": rnd.choice([0, 0, 1, 1, 2, 3, 4, 5]), "tguid": rnd.randrange(1 << 32),
            "tpnull": 0, "tnull": 0, "umode": rnd.choice([1, 2, 8, 9, 10, 11, 12]), "uguid": rnd.randrange(1 << 32),
            "m54": rnd.choice([0, 1, 2, 3, 19, 4]), "c4": rnd.choice([0, 0x1000, rnd.randrange(1 << 32)]),
            "ring": [], "nl": 0, "nlw": [], "needle": rnd.randrange(1, 5), "c38": 0, "lcount": 0, "nodes": [],
            "g88": rnd.randrange(1 << 32), "mscount": rnd.choice([0x2E0, 0x2E0, 0x2E0, cls, cls + 1, 0]),
            "ms0d": rnd.randrange(256), "msnull": 0, "sk1": rnd.choice([0xFFFF, 0x8000, 0x7FFF, 0, 1, rnd.randrange(400)]),
            "skcount": rnd.choice([400, 0x16D, 0x7FFF, 0x10000, 1, 0]), "n": rnd.choice([0, 1, 16, 3, rnd.randrange(60)]),
            "selfowner": 0, "nodeidx": 0,
        }
        inp["ctl18frame"] = 0
        pt = lambda: rnd.choice([(0, rnd.randrange(1 << 16)), (rnd.randrange(1 << 16), 0), (0, 0), (ux, uy),
                                 (near(ux, 4), near(uy, 4)), (near(ux, 2), near(uy, 2)),
                                 (rnd.randrange(1 << 16), rnd.randrange(1 << 16))])
        def rec(kind, zero=True):
            x, y = pt() if zero else (near(ux, 30) or 1, near(uy, 30) or 1)
            return [kind, x, y, rnd.choice([0, 0, 1, 5, -1 & 0xFFFFFFFF]), rnd.choice([0, 1, 4, 10, -1 & 0xFFFFFFFF])]
        ring = []
        if fam in ("npc", "towner", "jarjar", "h6800", "st13", "h6860"):
            ring.append(rec(10))
            if fam in ("npc", "towner", "jarjar", "h6860") and rnd.randrange(8):
                ring[0][1], ring[0][2] = near(ux, 30) or 1, near(uy, 30) or 1
            if fam == "st13" and rnd.randrange(4) == 0:
                ring = []
        if fam in ("towner", "h6ae0"):
            for kd in (4, 5, 7):
                if rnd.randrange(2):
                    r = rec(kd)
                    if kd == 5:
                        r[1] = rnd.choice([0, 1, 2, 3, 4, -1 & 0xFFFFFFFF])
                        r[2] = rnd.randrange(16)
                    if kd == 7:
                        m = rnd.choice([0, 8, 9, 10, 11, 8, 9, 1, 12])
                        x, y = pt()
                        r = [7, m, x, y, rnd.choice([0, 1, 4])]
                        inp["umode"] = rnd.choice([m, 1, 8])
                    ring.append(r)
        if fam in ("oot", "h77a0"):
            if rnd.randrange(6):
                ring.append(rec(3))
                if rnd.randrange(4):
                    ring[-1][1], ring[-1][2] = 7, 9
        if fam == "h6860" and rnd.randrange(3):
            ring.append(rec(4))
        if fam in ("act2", "act4", "act5", "h7080", "towner") and rnd.randrange(4):
            ring += [rec(4), rec(7)] if fam != "towner" else []
            if rnd.randrange(4) == 0:
                ring = ring[:-1]
        if fam in ("st9", "st3") :
            n = rnd.choice([0, 1, 2])
            ring = [[rnd.choice([8, 8, 2, 4]), rnd.randrange(1 << 16), rnd.randrange(1 << 16), 0, 0] for _ in range(n)]
        inp["ring"] = ring
        if fam in ("nstat", "navi", "buffy", "hp", "st13"):
            inp["upnull"] = int(rnd.randrange(3) == 0)
        if fam in ("soul", "h5710", "h7d30", "hcb") and rnd.randrange(5) == 0:
            inp["tnull"] = 1
        if fam == "h7d30":
            inp["ttype"] = 1
            inp["tpnull"] = int(rnd.randrange(4) == 0)
        if fam == "soul":
            inp["ttype"] = rnd.choice([0, 1])
            inp["tx"] = rnd.choice([ux, ux - 1, ux + 1, rnd.randrange(1 << 16)])
            inp["ty"] = rnd.choice([uy, uy - 1, uy + 1, rnd.randrange(1 << 16)])
            if rnd.randrange(2):
                inp["ctl18"] = rnd.choice([inp["frame"], inp["frame"] - 1, inp["frame"] + 1, 0])
            inp["ctl14"] = rnd.choice([0, 1, 1, 1, 7])
        if fam == "illus":
            inp["ctl18"] = rnd.choice([0, 1, 1, 2])
        if fam == "st2":
            inp["ttype"] = 1
            inp["ctl14"] = rnd.choice([0, 0, 1])
        if fam == "st13":
            inp["msnull"] = int(rnd.randrange(6) == 0)
        if fam == "hcb":
            inp["ttype"] = rnd.choice([0, 0, 0, 1])
            inp["tx"], inp["ty"] = rnd.choice([(near(ux, 8), near(uy, 8)), (near(ux, 20), uy),
                                               (ux + rnd.choice([15, 16, -15, -16]), uy)])
        if fam == "st3i":
            inp["selfowner"] = rnd.randrange(2)
        if fam == "h5b70":
            if rnd.randrange(2):
                inp["ctl18"] = rnd.choice([inp["frame"] - 700, inp["frame"] - 701, inp["frame"] + 700, inp["frame"] + 701])
            inp["ctl14"] = rnd.choice([0, 0, 1, 2, 3])
            inp["mscount"] = rnd.choice([0x2E0, 0x2E0, 0x2E0, cls])
        if fam in ("towner", "h7080", "h5b70") and rnd.randrange(4):
            inp["c38"] = 1
            cnt = rnd.choice([0, 1, 2, 3, 4, 5]) if fam != "h5b70" else rnd.choice([1, 2, 3])
            inp["lcount"] = cnt
            inp["nodes"] = []
            for _ in range(cnt):
                x, y = rnd.choice([(ux, uy), (ux, uy), (near(ux, 9), near(uy, 9)), (0, 5), (5, 0)])
                inp["nodes"].append([rnd.choice([0, 1, 2, 3, 4, 5, 6, 7, -1 & 0xFFFFFFFF]), x, y])
        if fam.startswith("act"):
            x, y = rnd.choice([(ux, uy), (ux, uy), (ux, uy), (near(ux, 9), near(uy, 9)), (0, 5), (5, 0)])
            inp["nodes"] = [[int(fam[3]), x, y]]
        if fam in ("npc", "towner", "jarjar", "oot", "navi", "h7350", "il0", "il1", "h6800", "h6ae0", "h7080"):
            n = rnd.choice([0, 0, 1, 2])
            inp["nlw"] = [rnd.choice([0, 0, 1, 2, 3, 4]) for _ in range(n)]
            inp["nl"] = int(any(w != 0 for w in inp["nlw"]))
        mrec = MSBASE + 0x1A8 * (inp["cls"] & 0xFFFF)
        lines = [
            "w %08x %s" % (GAME + 0x6D, "%02x" % inp["diff"]),
            "w %08x %s" % (GAME + 0xA8, hx32(inp["frame"])),
            "w %08x %s" % (UNIT, hx32(1) + hx32(inp["cls"])),
            "w %08x %s" % (UNIT + 0x0C, hx32(inp["uguid"]) + hx32(inp["umode"]) + hx32(MDATA)),
            "w %08x %s%s" % (UNIT + 0x20, hx32(seed[0]), hx32(seed[1])),
            "w %08x %s" % (UNIT + 0x2C, hx32(0 if inp["upnull"] else UPATH)),
            "w %08x %s" % (UNIT + 0xC4, hx32(inp["c4"])),
            "w %08x %s" % (UNIT + 0xE4, hx32(0)),
            "w %08x %s" % (UPATH + 0x02, hx16(inp["ux"])), "w %08x %s" % (UPATH + 0x06, hx16(inp["uy"])),
            "w %08x %s" % (UPATH + 0x1C, hx32(ROOM)),
            "w %08x %s" % (TARGET, hx32(inp["ttype"]) + hx32(0)),
            "w %08x %s" % (TARGET + 0x0C, hx32(inp["tguid"])),
            "w %08x %s" % (TARGET + 0x2C, hx32(0 if inp["tpnull"] else TPATH)),
            "w %08x %s" % (TPATH + 0x02, hx16(inp["tx"])), "w %08x %s" % (TPATH + 0x06, hx16(inp["ty"])),
            "w %08x %s" % (TPATH + 0x0C, hx32(inp["tsx"]) + hx32(inp["tsy"])),
            "w %08x %s" % (TPATH + 0x1C, hx32(TROOM)),
            "w %08x %s" % (MDATA + 0x28, hx32(CTL)),
            "w %08x %s" % (MDATA + 0x30, hx32(NL)),
            "w %08x %s" % (MDATA + 0x54, hx32(inp["m54"])),
            "w %08x %s" % (CTL, hx32(0)),
            "w %08x %s%s%s%s" % (CTL + 0x14, hx32(inp["ctl14"]), hx32(inp["ctl18"]), hx32(inp["ctl1c"]),
                                 hx32(PRM if inp["ring"] else 0)),
            "w %08x %s" % (CTL + 0x38, hx32(LIST if inp["c38"] else 0)),
            "w %08x %s" % (CTX, hx32(CTL) + hx32(0) + hx32(0 if inp["tnull"] else TARGET) + hx32(0) + hx32(0)
                           + hx32(inp["dist"]) + hx32(inp["melee"]) + hx32(0 if inp["msnull"] else mrec) + hx32(MS2)),
            "w %08x %s" % (mrec + 0x0D, "%02x" % inp["ms0d"]),
            "w %08x %s" % (mrec + 0x170, hx16(inp["sk1"])),
            "w %08x %s" % (mrec + 0x18, hx16(0xFFFF)),      # no MonStats2 row: UNIT_GetSizeX 0x00620510 on the image gives its no-record value
            "w %08x %s" % (G_DATATABLES, hx32(DTBL)),
            "w %08x %s" % (DTBL + 0xA78, hx32(MSBASE)),
            "w %08x %s" % (DTBL + 0xA80, hx32(inp["mscount"])),
            "w %08x %s" % (DTBL + 0xBA0, hx32(inp["skcount"])),
            "w %08x %s" % (G_COUNTER, hx32(inp["g88"])),
            "w %08x %s" % (WTS, hx32(0x5A5A5A5A) * 2),
        ]
        for n, (kind, x, y, w14, w18) in enumerate(inp["ring"]):
            nxt = PRM + 0x40 * ((n + 1) % len(inp["ring"]))
            lines.append("w %08x %s" % (PRM + 0x40 * n, hx32(nxt) + hx32(0) + hx32(kind) + hx32(x) + hx32(y) + hx32(w14) + hx32(w18)))
        lines.append("w %08x %s" % (NL, hx32(NL + 0x100 if inp["nlw"] else 0)))
        for n, w in enumerate(inp["nlw"]):
            nxt = NL + 0x100 * (n + 2) if n + 1 < len(inp["nlw"]) else 0
            lines.append("w %08x %s" % (NL + 0x100 * (n + 1), hx32(w) + hx32(0) + hx32(nxt)))
        if inp["c38"]:
            lines.append("w %08x %s" % (LIST, hx32(inp["lcount"]) + hx32(NODES)))
            for n, (a, x, y) in enumerate(inp["nodes"]):
                lines.append("w %08x %s" % (NODES + 12 * n, hx32(a) + hx32(x) + hx32(y)))
        if inp["nodes"] and not inp["c38"]:
            a, x, y = inp["nodes"][0]
            lines.append("w %08x %s" % (NODES, hx32(a) + hx32(x) + hx32(y)))
        if fam == "st3i":
            inp_c = inp["uguid"] if inp["selfowner"] else inp["tguid"]
            lines.append("w %08x %s" % (CTL + 0x28, hx32(GAME) + hx32(inp_c) + hx32(1)))
            u = UNIT if inp["selfowner"] else OWNER
            lines.append("w %08x %s" % (slot_addr(1, inp_c), hx32(u)))
            lines.append("w %08x %s" % (OWNER, hx32(1)))
            lines.append("w %08x %s" % (OWNER + 0x0C, hx32(inp["tguid"])))
            lines.append("w %08x %s" % (OWNER + 0x2C, hx32(TPATH)))
            lines.append("w %08x %s" % (OWNER + 0xE4, hx32(0)))
        lines += ["d %08x %d" % (STK_LO, STK_LEN), "d %08x 8" % (UNIT + 0x20), "d %08x 12" % (CTL + 0x14),
                  "d %08x 4" % (UNIT + 0xC4), "d %08x %d" % (PRM, 0x100), "d %08x 8" % WTS]
        f = FNS[fam]
        t = 0 if inp["tnull"] else TARGET
        if fam == "h6860":
            call = "call %08x %08x %08x %08x %08x" % (f, GAME, UNIT, CTX, inp["n"])
        elif fam.startswith("act"):
            call = "call %08x %08x %08x %08x %08x" % (f, GAME, UNIT, CTX, NODES)
        elif fam == "h5710":
            call = "call %08x %08x %08x" % (f, t, WTS)
        elif fam == "h7d30":
            call = "call %08x %08x %08x" % (f, t, 0)
        elif fam == "hcb":
            call = "call %08x %08x %08x %08x %08x" % (f, GAME, UNIT, t, WTS)
        elif fam == "h7350":
            call = "call %08x %08x %08x" % (f, GAME, UNIT)
        elif fam == "il0":
            call = "call %08x %08x %08x" % (f, NL, 0)
        elif fam == "il1":
            call = "call %08x %08x %08x" % (f, NL, inp["needle"])
        elif fam == "hp":
            call = "call %08x %08x %08x %08x" % (f, GAME, UNIT, WTS)
        else:
            call = "call %08x %08x %08x %08x" % (f, GAME, UNIT, CTX)
        lines.append(call)
        cases.append(lines)
        meta.append(inp)
    mem = ["observe %08x" % a for a in OBSERVE] + ["guard %08x" % a for a in FATAL + ALLOC]
    return cases, meta, mem


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        cases, meta, mem = gen_family(fam, random.Random("r52l-" + fam))
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
                c["regs"] = {k: int(v, 16) for k, v in kv.items() if k != "steps"}
            calls.append(c)
        elif p[0] == "A":
            calls[-1]["args"] = bytes.fromhex(p[1])
        elif p[0] == "D":
            calls[-1]["dumps"][int(p[1], 16)] = bytes.fromhex(p[2]) if len(p) > 2 else b""
        elif p[0] in ("R", "W"):
            traced.append(ln.strip())
    return calls, traced


def readm(c, addr):
    for base, b in c["dumps"].items():
        if base <= addr and addr + 4 <= base + len(b):
            return struct.unpack_from("<I", b, addr - base)[0]
    return None


def matches(c, want, site_shift=0):
    fn, site, ecx, edx, args, seed, c14, c18, c1c, mem, regs, eax, al = want
    if c.get("obs") != fn:
        return False
    gseed = list(struct.unpack("<II", c["dumps"][UNIT + 0x20]))
    g14, g18, g1c = struct.unpack_from("<III", c["dumps"][CTL + 0x14], 0)
    ok = gseed == seed and g14 == c14 and g18 == c18 and g1c == c1c
    for addr, val in mem:
        ok = ok and readm(c, addr) == val
    if fn == RET:
        if eax is not None:
            ok = ok and c["regs"]["eax"] == u32(eax)
        if al is not None:
            ok = ok and c["regs"]["eax"] & 0xFF == al
        return ok and site_shift == 0
    a = c.get("args", b"")
    got = [struct.unpack_from("<I", a, 4 + 4 * k)[0] for k in range(len(args))]
    ret = struct.unpack_from("<I", a, 0)[0]
    ok = ok and ret == site + site_shift and all(w is None or g == w for g, w in zip(got, args))
    if ecx is not None:
        ok = ok and c["regs"]["ecx"] == u32(ecx)
    if edx is not None:
        ok = ok and c["regs"]["edx"] == u32(edx)
    for r, v in regs.items():
        ok = ok and c["regs"][r] == u32(v)
    return ok


def check_family(fam, d):
    _, meta, _ = gen_family(fam, random.Random("r52l-" + fam))
    calls, traced = read_out(os.path.join(d, fam + ".out"))
    bad, match, stops = [], 0, 0
    ctl = {n: [0, 0] for n in CONTROLS}
    site_pass = 0
    bounds, edges, tags = {}, {}, {}
    ndraws = 0
    reads = set()
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
            bad.append("case %d mismatch want=%s@%s args=%s mem=%s obs=%s args=%s regs=%s" % (
                c["n"], want[0] if want[0] == RET else hex(want[0]), hex(want[1]), want[4], want[9],
                c.get("obs") if c.get("obs") == RET else hex(c.get("obs", 0)), c.get("args", b"")[:24].hex(),
                {k: hex(v) for k, v in c.get("regs", {}).items() if k in ("eax", "ecx", "edx")}))
        key = RET if want[0] == RET else "%x@%x" % (want[0], want[1])
        bounds[key] = bounds.get(key, 0) + 1
        ndraws += want[5] != list(inp["seed"])
        site_pass += matches(c, want, site_shift=1) if want[0] != RET else 0
        for n in ctl:
            nw = run_model(inp, neg=n)
            if nw != want:
                ctl[n][0] += 1
                ctl[n][1] += matches(c, nw)
    expect = set("R %08x %08x 4" % (pc, addr) for pc, addr in reads)
    seen = set(" ".join(x.split()[:4]) for x in traced)
    accounted = len(seen & expect)
    if expect - seen:
        bad.append("accounted reads missing %s" % sorted(expect - seen))
    traced = [x for x in traced if " ".join(x.split()[:4]) not in expect]
    line = ("AI52L %s cases=%d match=%d bad=%d stopped=%d traced=%d accounted=%d drew=%d " % (
        fam, len(meta), match, len(bad), stops, len(traced), accounted, ndraws)
        + " ".join("%s_separating=%d %s_passed=%d" % (n, ctl[n][0], n, ctl[n][1]) for n in CONTROLS)
        + " site_control_passed=%d boundaries=%d" % (site_pass, len(bounds)))
    return line, bad[:20], traced[:20], bounds, ctl, edges, tags


def cmd_check(d, fams=None):
    allok = True
    tot = [0, 0]
    for fam in (fams or FAMILIES):
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
    print("AI52L total cases=%d match=%d" % tuple(tot))
    print("AI52L result=%s" % ("ok" if allok else "FAIL"))


def cmd_manifest(d, write):
    rows = []
    for fam in FAMILIES:
        for ext in ("cases", "mem", "out", "err"):
            p = os.path.join(d, "%s.%s" % (fam, ext))
            if os.path.exists(p):
                rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.basename(p)))
    for extra in ("check.txt", "ai_cat_emu12.py.rev"):
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
    ap.add_argument("--fam", default="")
    a = ap.parse_args(argv)
    if a.cmd == "cases":
        cmd_cases(a.dir)
    elif a.cmd == "check":
        cmd_check(a.dir, a.fam.split(",") if a.fam else None)
    else:
        cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    main(sys.argv[1:])

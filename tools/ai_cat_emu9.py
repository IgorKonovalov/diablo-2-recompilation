#!/usr/bin/env python3
"""Plan 0052 phase 1.2, catalogue batch 9 (pool-F, `lane/r52i`): the think and init functions of AI rows 116-125
and state rows 15 and 16 run under Ghidra's p-code emulator (ADR-0015, ADR-0021) with
re/ghidra_scripts/EmuBoundary.java and compared with the models below. No game run, no slot. Same method as
tools/ai_cat_emu8.py (batch 8): one family per function, the `le`, `d0`, `cmp` and `u16` controls and the site
control, the EDGES line per family. Additions: a fifth control `own` (the imp functions' aip read from the unit's own
MonStats record instead of the fixed records 492-495), more small callees run on the declared image (listed below),
and the accounting of every traced read of the image's own tables (the unit hash offsets 0x006E10E0 that
GameFindUnit reads, the slot table 0x006E34E0 of state row 16's init).

    python3 -I tools/ai_cat_emu9.py cases [--dir D]      write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/ai_cat_emu9.py check [--dir D]      compare every D/<family>.out with its model, account for
                                                         every traced access, run the negative and site controls
    python3 -I tools/ai_cat_emu9.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r52i/emu. Every case draw comes from random.Random("r52i-<family>"), so `cases` regenerates
identical files.

Each family runs one function `(ECX game, EDX unit; ctx)` (ai/0010) on a declared image: the game's difficulty byte
(+0x6D), frame (+0xA8), quest list head (+0x10F4, always 0) and the unit hash slot a lookup reads (+0x1120 + ... as
0x006E10E0 gives, or +0x1B20 for type 5); the unit's type (+0x00, 1), class (+0x04), mode (+0x10), monster data
pointer (+0x14), seed (+0x20/+0x24), path pointer (+0x2C), game pointer (+0x80), owner type and guid (+0x94/+0x98),
stored unit type and guid (+0x9C/+0xA0), skill list (+0xA8), +0xC4 and the flag word +0xC8; the unit path's x (+0x02,
u16), y (+0x06, u16) and room (+0x1C); the target's type (+0x00), guid (+0x0C), mode (+0x10), path pointer (+0x2C),
stat list (+0x5C, 0 or a list with +0x10 and a node +0x3C with +0x10 and +0x2C), byte +0xC6 and hash next (+0xE4),
that path's x and y and the static words +0x0C/+0x10; a second unit (0x12E00000: type, guid, mode, +0xC6, +0xE4); the
monster data's +0x54 and AI control pointer (+0x28); the AI control's state (+0x00), +0x14, +0x18, +0x1C and +0x20 (0
or a parameter record with kind +0x08 and the words +0x0C, +0x10, +0x14); the AiCtx (+0x00 ctl, +0x08 target, +0x14
distance, +0x18 melee, +0x1C MonStats record, +0x20 MonStats2 record); the MonStats record of the unit's class
(DataTables +0xA78 + class * 0x1A8: its +0x3E word, aip block +0x56..+0x85, Skill1..8 +0x170..+0x17F and
Sk1..8mode +0x180..+0x187), which is also the ctx record; the aip blocks of the MonStats records 492-495 (rows 122 and
state 16); the skill list's nodes (+0x04 first, node +0x00 a skill record whose s16 +0x00 is the id, +0x04 next,
+0x34 the owner word); the DataTables pointer (0x00744304), its MonStats base (+0xA78) and count (+0xA80).

Callees that run on the declared image (not boundaries): RNG_Range 0x0045C390; the position getters 0x0045ADF0,
0x0045AE20 with 0x006488C0, 0x00648900; sub_0058EE80_AiParamsHead; sub_00552F60_GameFindUnit (one slot, one unit);
sub_005541B0_UnitIsDead; sub_00552FD0_UnitGetOwner; sub_00553010_UnitStoredUnit9C; 0x005DE830 (the overseer's stored
hostile); 0x00587900 with QUESTS_FindById 0x00543640 (no quest list: it returns at once); sub_005DD2B0_AiMonState3or19
with sub_005734E0_MonData54Get; sub_005DD2D0_MonHasSkill; sub_00625760_StatListFindFlag with 0x006256E0;
sub_006439B0_SkillFindByOwner; 0x005DF850 (the skill-near-self helper) with sub_00554010_UnitGetGame. Every other
callee the function reaches is an observed boundary. The claim per case: the first boundary reached (or the
function's return), its call site (the return address), the registers and stack arguments the callee takes, the unit
seed, the AI control's +0x14/+0x18/+0x1C and the unit's +0xC4 at the boundary, and where a pointer argument addresses
the frame, the words it addresses.

Families (function, row):
  minion   0x005E1B60 row 116 Minion            suicide  0x005E1D30 row 117 SuicideMinion = state row 15
  succubus 0x005E1E00 row 118 Succubus          witch    0x005E2120 row 119 SuccubusWitch
  overseer 0x005E27A0 row 120 Overseer          spawner  0x005E2BD0 row 121 MinionSpawner
  imp16i   0x005E2CD0 state row 16 init          imp16    0x005E2D80 state row 16 think
  impi     0x005E2FD0 row 122 init               imp      0x005E2FF0 row 122 Imp
  catapult 0x005E34C0 row 123 Catapult          horror   0x005E3530 row 124 FrozenHorror
  blood    0x005E36F0 row 125 BloodLord
The `entry` families (ENTRY below) reach their first boundary before any test of their own: imp16 (HasState after the
owner lookup) and horror (its skill-sign test only).

Controls: `le` compares each draw with `<=` instead of `<`; `d0` reads every aip from the Normal column; `cmp`
switches the strictness of every compare that is not a draw (`<` and `<=`, `>` and `>=`); `u16` reads Skill1..8 as
unsigned words in their sign tests; `own` reads the imp functions' fixed-record aip from the unit's own record;
`site` expects each call site one byte later. Each must fail every case it separates. The `EDGES` line under each
family counts, per compare, the cases that meet it at equality (the only cases in which a strictness control can
separate that compare); a compare missing from it has no control in the run.

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
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r52i", "emu")

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
TSL = 0x12C00000
TNODE = 0x12C00100
SKL = 0x12D00000
SKNODE = 0x12D00100          # node k at SKNODE + 0x40 k, its skill record at SKREC + 0x10 k
SKREC = 0x12D01000
OTHER = 0x12E00000
PARAM = 0x12F00000
MSBASE = 0x13000000          # DataTables +0xA78: MonStats record c at MSBASE + 0x1A8 c
IMPREC = tuple(MSBASE + 0x1A8 * c for c in (492, 493, 494, 495))
G_DATATABLES = 0x00744304
HASHOFF = (0x1120, 0x1320, 0x1520, 0x1920, 0x1720)   # 0x006E10E0, u32 per unit type 0..4 (objdump -s of .rdata)
SLOTTBL = ((2, 0), (4, 0))                            # 0x006E34E0, two rows of two u32 (objdump -s of .rdata)
STK_LO = 0x7FEFFC00
STK_LEN = 1040
EBP = 0x7FEFFFFC
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)

SETMODEAT, IDLE, WALK, WALKZ, T56, WALKSTOP, FINDHOSTILE, USESKILL, SETMODE = (
    0x005DDF90, 0x005DE080, 0x005DEC80, 0x005DECA0, 0x005DF7D0, 0x005DEF80, 0x005DDC30, 0x005DEAD0, 0x005DDFC0)
HASSTATE, STATESET, LIFEPCT, MAXHP, MAXMANA, STEPAWAY, POP, EDGEDIST, MELEE, SEARCH, HOSTILE, ALIGN, AILIFE, WRING, \
    GETSKILL, SKLEVEL, AIINIT = (
        0x00639DF0, 0x00639DB0, 0x00621F20, 0x00625D10, 0x00625D60, 0x005DEFE0, 0x0058ED10, 0x006416D0, 0x00622C40,
        0x005DD0B0, 0x00554200, 0x006259B0, 0x005DD280, 0x005DE200, 0x006439F0, 0x006442A0, 0x005B0E00)
EXTRA = (0x00463860, 0x005B0BD0, 0x005A0180, 0x0063EA40, 0x00544300, 0x005A01E0, 0x006256B0, 0x00625420,
         0x00625B70, 0x0058F0D0, 0x005DD7F0, 0x00620BB0)
OBSERVE = tuple(sorted(set((SETMODEAT, IDLE, WALK, WALKZ, T56, WALKSTOP, FINDHOSTILE, USESKILL, SETMODE, HASSTATE,
                            STATESET, LIFEPCT, MAXHP, MAXMANA, STEPAWAY, POP, EDGEDIST, MELEE, SEARCH, HOSTILE, ALIGN,
                            AILIFE, WRING, GETSKILL, SKLEVEL, AIINIT) + EXTRA)))
RET = "ret"

FNS = {"minion": 0x005E1B60, "suicide": 0x005E1D30, "succubus": 0x005E1E00, "witch": 0x005E2120,
       "overseer": 0x005E27A0, "spawner": 0x005E2BD0, "imp16i": 0x005E2CD0, "imp16": 0x005E2D80,
       "impi": 0x005E2FD0, "imp": 0x005E2FF0, "catapult": 0x005E34C0, "horror": 0x005E3530, "blood": 0x005E36F0}
FAMILIES = tuple(FNS)
ENTRY = ("imp16", "horror")
NCASES = 240
CONTROLS = ("le", "d0", "cmp", "u16", "own")


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


class Env:
    """One case's inputs and the model's running state (the unit seed, the AI control's +0x14/+0x18/+0x1C, +0xC4)."""

    def __init__(self, inp, neg=None):
        self.i, self.neg = inp, neg
        self.seed = list(inp["seed"])
        self.c14, self.c18, self.c1c = inp["ctl14"], inp["ctl18"], inp["ctl1c"]
        self.c4 = inp["c4"]
        self.eq = set()                     # the compares this case met at equality
        self.reads = set()                  # the image-table reads the case makes (traced, to be accounted)
        self.tags = set()                   # path marks counted by `check` (TAGS line)

    def dcol(self):
        return 0 if self.neg == "d0" else self.i["diff"]

    def aip(self, k):
        return s16(self.i["aip"][k - 1][self.dcol()])

    def raip(self, r, k):                   # aipK of the fixed MonStats record 491 + r (r = 1..4)
        if self.neg == "own":
            return self.aip(k)
        return s16(self.i["raip"][r - 1][k - 1][self.dcol()])

    def draw(self):
        step(self.seed)
        return self.seed[0] % 100

    def rng(self, n):
        step(self.seed)
        return self.seed[0] % n

    def _cmp(self, d, c, edge):
        if d == c:
            self.eq.add(edge)
        return d <= c if self.neg == "le" else d < c

    def chance(self, k):
        return self._cmp(self.draw(), self.aip(k), "draw<aip%d" % k)

    def rchance(self, k):
        return self._cmp(self.rng(100), self.aip(k), "Range<aip%d" % k)

    def rdraw(self, r, k):                  # inline draw < aipK of record 491 + r
        return self._cmp(self.draw(), self.raip(r, k), "draw<R%d.aip%d" % (r, k))

    def rrange(self, r, k):                 # RNG_Range(seed, 100) < aipK of record 491 + r
        return self._cmp(self.rng(100), self.raip(r, k), "Range<R%d.aip%d" % (r, k))

    def chance_c(self, c):
        return self._cmp(self.draw(), c, "draw<%d" % c)

    def rchance_c(self, c):
        return self._cmp(self.rng(100), c, "Range<%d" % c)

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

    def neg_(self, k):                      # SkillK < 0 (u16: never)
        return False if self.neg == "u16" else self.sk(k) < 0

    def pos(self, k):                       # SkillK > 0 (u16: != 0)
        return (self.i["skill"][k - 1] & 0xFFFF) != 0 if self.neg == "u16" else self.sk(k) > 0

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

    def slff(self):                         # sub_00625760_StatListFindFlag(target, 0x20) with 0x006256E0
        t = self.i["tsl"]
        if t is None:
            return False
        sl10, node, n10 = t
        return bool(sl10 & 0x80000000) and node and bool(n10 & 0x20)

    def skfind(self, sid):                  # sub_006439B0_SkillFindByOwner(U, sid; -1) on the declared list
        if self.i["sklnull"]:
            return False
        for nid, n34 in self.i["skl"]:
            if s16(nid) == sid and n34 == 0xFFFFFFFF:
                return True
        return False

    def tpos(self):
        i = self.i
        if i["ttype"] in (2, 4, 5):
            return i["tsx"], i["tsy"]
        if i["tpnull"]:
            return 0, 0
        return i["tx"], i["ty"]

    def hit(self, fn, site, args, ecx=GAME, edx=UNIT, block=None):
        raise Hit((fn, site, ecx, edx, [u32(a) for a in args], list(self.seed), u32(self.c14), u32(self.c18),
                   u32(self.c1c), u32(self.c4), block))

    def ret(self):
        self.hit(RET, 0, [])


def m_minion(e):                                        # row 116, 0x005E1B60
    i, t = e.i, TARGET
    T = s32(i["frame"])
    f = 0
    p = i["param"]
    if p is not None:
        kind, w0c, w10, w14 = p
        if kind == 1 and e.lt(T, s32(w14), "w14>T"):
            u = e.findunit(w0c, w10)
            if u and not e.dead(u):
                f = 1
                e.tags.add("found" if u != t else "found-is-target")
                if u != t:
                    e.hit(EDGEDIST, 0x005E1BDA, [UNIT, u], ecx=None, edx=None)
            else:
                e.hit(POP, 0x005E1BF1, [])
        else:
            e.hit(POP, 0x005E1BF1, [])
    if i["melee"]:
        if not f and not e.chance(1):
            e.hit(IDLE, 0x005E1C4A, [e.aip(2)])
        if e.chance(2):
            e.hit(SETMODEAT, 0x005E1C9C, [5, t])
        e.hit(SETMODEAT, 0x005E1CB2, [4, t])
    if not f and not e.chance(3):
        e.hit(IDLE, 0x005E1D0A, [e.aip(4)])
    e.hit(WALK, 0x005E1D22, [t, 0])


def m_suicide(e):                                       # row 117 and state row 15, 0x005E1D30
    i, t = e.i, TARGET
    T = s32(i["frame"])
    if e.c14 != 0:
        if e.lt(s32(e.c14), T, "T>v14"):
            e.hit(SETMODEAT, 0x005E1D68, [0, t])
        e.hit(IDLE, 0x005E1D9E, [e.aip(2)])
    if i["melee"]:
        e.c14 = u32(e.aip(5) + T)
        e.hit(IDLE, 0x005E1D9E, [e.aip(2)])
    if e.chance(3):
        e.hit(WALK, 0x005E1DF1, [t, 0])
    e.hit(IDLE, 0x005E1D9E, [e.aip(2)])


def m_succubus(e):                                      # row 118, 0x005E1E00
    i, t = e.i, TARGET
    dist = i["dist"]
    if not e.slff() and e.lt(dist, e.aip(4), "dist<aip4") and e.chance(3):
        if e.pos(1):
            e.hit(LIFEPCT, 0x005E1EA2, [t], ecx=None, edx=None)
        if e.pos(2):
            e.hit(LIFEPCT, 0x005E1EED, [UNIT], ecx=None, edx=None)
        if e.pos(3):
            e.hit(MAXHP, 0x005E1F3B, [t], ecx=None, edx=None)
        if e.pos(4) and i["ttype"] == 0:
            e.hit(USESKILL, 0x005E1FB5, [e.skm(4), e.sk(4), t, 0, 0])
    if i["melee"]:
        if e.chance(1):
            e.hit(SETMODEAT, 0x005E2011, [4, t])
        e.hit(IDLE, 0x005E202A, [e.aip(5)])
    if e.pos(5) and e.lt(0, e.aip(8), "aip8>0"):
        e.hit(FINDHOSTILE, 0x005E205C, [EBP - 0x0C, 0], block=(EBP - 0x0C, [dist]))
    if e.chance(2):
        e.hit(WALK, 0x005E20F5, [t, 0])
    e.hit(IDLE, 0x005E210E, [e.aip(6)])


def m_witch(e):                                         # row 119, 0x005E2120
    i = e.i
    t = 0 if i["tnull"] else TARGET
    dist = i["dist"]
    if t and not e.slff() and e.lt(dist, e.aip(4), "dist<aip4") and e.chance(3):
        if e.pos(1):
            e.hit(LIFEPCT, 0x005E21CA, [t], ecx=None, edx=None)
        if e.pos(2):
            e.hit(LIFEPCT, 0x005E2215, [UNIT], ecx=None, edx=None)
        if e.pos(3):
            e.hit(MAXHP, 0x005E2263, [t], ecx=None, edx=None)
        if e.pos(4) and i["ttype"] == 0:
            e.hit(USESKILL, 0x005E22D9, [e.skm(4), e.sk(4), t, 0, 0])
    if i["melee"]:
        if e.chance(3):
            e.hit(STEPAWAY, 0x005E233D, [t, e.aip(4) & 0xFF, 1])
        if e.chance(1):
            e.hit(SETMODEAT, 0x005E2390, [4, t])
        e.hit(IDLE, 0x005E23A9, [e.aip(6)])
    if e.has(5) and e.lt(0, e.aip(8), "aip8>0") and e.chance(5):
        e.hit(FINDHOSTILE, 0x005E2420, [EBP - 8, 0], block=(EBP - 8, [dist]))
    if e.lt(dist, e.aip(4), "dist<aip4") and e.chance(3):
        e.hit(STEPAWAY, 0x005E24CD, [t, e.aip(4) & 0xFF, 1])
    if e.neg_(5):
        e.hit(FINDHOSTILE, 0x005E24EF, [EBP - 8, 0], block=(EBP - 8, [dist]))
    if e.chance(2):
        e.hit(WALK, 0x005E259E, [t, 0])
    if e.chance_c(50):
        e.hit(T56, 0x005E25E9, [t, 6, 1])
    e.hit(IDLE, 0x005E2601, [e.aip(6)])


def m_overseer(e):                                      # row 120, 0x005E27A0
    i, t = e.i, TARGET
    T = s32(i["frame"])
    w = 0                                               # 0x00587900 returns at once: no quest list
    if i["c8"] & 0x20000:                               # 0x005DE830 -> sub_00553010_UnitStoredUnit9C
        u = e.findunit(i["stype"], i["sguid"])
        if u:
            typ, _, mode, _ = e.ufield(u)
            if typ == 0:
                w = 0 if mode in (0, 17) else u
                e.tags.add("stored-player" if w else "stored-player-dead")
            elif typ == 1 and mode not in (0, 12):
                e.hit(HOSTILE, 0x005DE864, [u])
    if e.has(1) and i["m54"] in (3, 19) and e.lt(s32(e.c14), T, "T>v14") and w:
        if 0 <= i["cls"] < i["mscount"]:                # sub_005DD2D0_MonHasSkill: Skill1 is in the record's list
            e.hit(USESKILL, 0x005E2841, [e.skm(1), e.sk(1), w, 0, 0])
    if i["melee"]:
        if e.chance(6):
            if e.chance(7):
                e.hit(SETMODEAT, 0x005E28F4, [5, t])
            e.hit(SETMODEAT, 0x005E290A, [4, t])
    e.hit(SEARCH, 0x005E2948, [EBP - 0x50, 0x005E26D0, 1], block=(EBP - 0x50, [0x240, 0x190, 0x32, 0, 0, 0]))


def m_spawner(e):                                       # row 121, 0x005E2BD0
    i = e.i
    T = s32(i["frame"])
    if e.le(e.aip(1), s32(e.c18), "v18>=aip1"):
        e.ret()
    if e.lt(e.aip(4), i["dist"], "dist>aip4"):
        e.hit(IDLE, 0x005E2C18, [e.aip(2)])
    if e.lt(T, s32(e.c14), "T<v14"):
        e.hit(IDLE, 0x005E2C3C, [e.aip(2)])
    e.hit(SEARCH, 0x005E2C5E, [EBP - 0x2C, 0x005E2B70, 1], block=(EBP - 0x2C, [0]))


def m_imp16i(e):                                        # state row 16 init, 0x005E2CD0
    step(e.seed)
    k = e.seed[0] & 1
    for _ in range(2):
        k = (k + 1) % 2
        e.reads.add((0x005E2D16, 0x006E34E0 + 8 * k))
        slot, word = SLOTTBL[k]
        if e.skfind(e.sk(slot + 1)):
            e.reads.add((0x005E2D55, 0x006E34E0 + 8 * k))
            e.reads.add((0x005E2D61, 0x006E34E4 + 8 * k))
            e.c18, e.c1c = slot, word
            e.ret()
    e.c18 = e.c1c = 0
    e.ret()


def m_imp16(e):                                         # state row 16 think, 0x005E2D80
    i = e.i
    if i["c8"] & 0x400:                                 # sub_00552FD0_UnitGetOwner's lookup (its result not tested yet)
        e.findunit(i["otype"], i["oguid"])
    e.hit(HASSTATE, 0x005E2DBA, [UNIT, 0x8F], ecx=None, edx=None)


def m_impi(e):                                          # row 122 init, 0x005E2FD0
    e.c14 = 0xFFFFFFFF
    e.ret()


def near_self(e, r, skill, mode):                       # 0x005DF850(ECX unit, EDX r; skill, mode)
    i = e.i
    n = s32(2 * r)

    e.tags.add("radius<=0" if n <= 0 else "radius-pow2" if n & (n - 1) == 0 else "radius-other")

    def off():
        if n <= 0:
            return 0
        step(e.seed)
        low = e.seed[0]
        return low & (n - 1) if n & (n - 1) == 0 else low % n
    x = u32(off() - r + i["ux"])
    y = u32(off() - r + i["uy"])
    e.hit(USESKILL, 0x005DF97B, [mode, skill, 0, x, y])


def m_imp(e):                                           # row 122, 0x005E2FF0
    i, t = e.i, TARGET
    dist = i["dist"]
    if s32(e.c14) != -1:
        e.hit(ALIGN, 0x005E30BB, [UNIT], ecx=None, edx=None)
    if i["melee"]:
        if e.has(1):
            e.hit(AILIFE, 0x005E31C0, [], ecx=UNIT, edx=None)
        if e.rdraw(3, 2):
            e.hit(STEPAWAY, 0x005E324B, [t, 5, 1])
    if e.has(1) and e.rdraw(1, 3):
        near_self(e, e.raip(1, 2), e.sk(1), s8(e.skm(1)))
    if e.lt(dist, e.raip(3, 1), "dist<R3.aip1") and e.rdraw(3, 2):
        e.hit(STEPAWAY, 0x005E332D, [t, 5, 0])
    if e.has(4):
        e.hit(FINDHOSTILE, 0x005E3356, [EBP - 8, 0], block=(EBP - 8, [dist]))
    if e.chance_c(33):
        e.hit(WALKSTOP, 0x005E3461, [t, 4])
    if e.chance_c(20):
        e.hit(WRING, 0x005E34A6, [8])
    e.hit(IDLE, 0x005E34B6, [10])


def m_catapult(e):                                      # row 123, 0x005E34C0
    if e.chance(1):
        e.hit(SETMODEAT, 0x005E3515, [4, 0])
    e.hit(IDLE, 0x005E3523, [15])


def m_horror(e):                                        # row 124, 0x005E3530
    if e.has(1):
        e.hit(GETSKILL, 0x005E3572, [], ecx=UNIT, edx=e.sk(1))
    e.hit(HASSTATE, 0x005E361F, [UNIT, 12], ecx=None, edx=None)


def m_blood(e):                                         # row 125, 0x005E36F0
    t = TARGET
    if e.i["melee"]:
        if e.chance(1):
            if e.chance(3):
                e.hit(USESKILL, 0x005E37A2, [5, e.sk(1), t, 0, 0])
            e.hit(SETMODEAT, 0x005E37B5, [4, t])
        e.hit(IDLE, 0x005E37CF, [e.aip(4)])
    if e.chance(2):
        e.hit(WALKZ, 0x005E3818, [t])
    e.hit(IDLE, 0x005E382E, [e.aip(4)])


MODELS = {"minion": m_minion, "suicide": m_suicide, "succubus": m_succubus, "witch": m_witch,
          "overseer": m_overseer, "spawner": m_spawner, "imp16i": m_imp16i, "imp16": m_imp16, "impi": m_impi,
          "imp": m_imp, "catapult": m_catapult, "horror": m_horror, "blood": m_blood}


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

        def aipblock():
            blk = []
            for _ in range(8):
                blk.append([rnd.choice(ds + ds + [rnd.randrange(0, 101), rnd.randrange(-3, 111), 0, 1, 2, 5, 6,
                                                  12, 14, 20, 24, 50, 80, -1]) for _ in range(3)])
            return blk
        aip = aipblock()
        raip = [aipblock() for _ in range(4)]
        diff = k % 3
        frame = rnd.randrange(100, 100000)
        a = [aip[j][diff] for j in range(8)]
        cls = rnd.randrange(0x2E0)
        while 488 <= cls <= 499:
            cls = rnd.randrange(0x2E0)
        inp = {
            "fam": fam, "seed": seed, "diff": diff, "aip": aip, "raip": raip, "frame": frame,
            "melee": rnd.randrange(2),
            "dist": max(0, rnd.choice([0, 1, 5, 6, 7, 10, 20, 24, 25, rnd.randrange(0, 60)]
                                      + [a[j] + rnd.choice((-1, 0, 1)) for j in (0, 1, 3, 7)])),
            "ctl14": rnd.choice([0, 0, 1, 2, -1, u32(frame + rnd.choice((-1, 0, 1)))]),
            "ctl18": rnd.choice([0, 0, 1, 2, 7, -1, u32(frame + rnd.choice((-1, 0, 1)))]),
            "ctl1c": rnd.choice([0, 0, 1, -1, u32(frame + rnd.choice((-1, 0, 1)))]),
            "c4": rnd.choice([0, 0x20000, rnd.randrange(1 << 32)]),
            "skill": [rnd.choice([-1, -1, 0x8000, 0xFFFE, 0x7FFF, 0, 1, rnd.randrange(0, 400), rnd.randrange(0, 400)])
                      & 0xFFFF for _ in range(8)],
            "skmode": [rnd.choice([rnd.randrange(16), rnd.randrange(16), rnd.randrange(0x80, 0x100)])
                       for _ in range(8)],
            "ux": rnd.randrange(1 << 16), "uy": rnd.randrange(1 << 16),
            "tx": rnd.randrange(1 << 16), "ty": rnd.randrange(1 << 16),
            "tsx": rnd.randrange(1 << 31), "tsy": rnd.randrange(1 << 31),
            "ttype": rnd.choice([0, 0, 1, 1, 1, 2, 3, 4, 5]), "tguid": rnd.randrange(1 << 32),
            "tmode": rnd.choice([0, 1, 4, 12, 17]), "tc6": rnd.choice([0, 0, 0, 1]),
            "state": rnd.randrange(18), "cls": cls,
            "mscount": rnd.choice([0x2E0, 0x2E0, 0x2E0, max(1, cls - rnd.randrange(0, 3))]),
            "m3e": rnd.choice([0, -1, 1, 5, 300, 0x8000]),
            "m54": rnd.choice([3, 19, 3, 19, 0, 1, 2, 18, 20]),
            "c8": rnd.choice([0, 0x400, 0x20000, 0x20400, rnd.randrange(1 << 32)]),
            "stype": rnd.randrange(6), "sguid": rnd.randrange(1 << 32),
            "otype": rnd.randrange(6), "oguid": rnd.randrange(1 << 32),
            "wtype": rnd.choice([0, 0, 1, 1, 2, 3]), "wmode": rnd.choice([0, 1, 4, 12, 17]),
            "wc6": rnd.choice([0, 0, 0, 1]), "wguid": 0, "slotval": 0,
            "tsl": None, "tnull": 0, "param": None, "sklnull": 0, "skl": [],
        }
        inp["tpnull"] = int(inp["ttype"] not in (2, 4, 5) and rnd.randrange(6) == 0)
        if rnd.randrange(3):
            inp["tsl"] = (rnd.choice([0x80000000, 0x80000000, 0, rnd.randrange(1 << 32)]), rnd.randrange(4) != 0,
                          rnd.choice([0x20, 0x20, 0, 0x10, rnd.randrange(1 << 32)]))
        look = None                                     # the one GameFindUnit lookup a family can make: (type, guid)
        if fam == "minion":
            p = rnd.choice([None, None, None, None, 1, 1, 1, 1, 0, 2, 14])
            if p is not None:
                inp["param"] = (p, rnd.randrange(6), rnd.randrange(1 << 32),
                                u32(frame + rnd.choice((-1, 0, 1, -100, 100, 100, 100))))
                look = (inp["param"][1], inp["param"][2])
            inp["ttype"] = rnd.choice([0, 1, 1, 1, 2])
            inp["tmode"] = rnd.choice([1, 4, 4, 0, 12, 17])
        if fam == "overseer":
            look = (inp["stype"], inp["sguid"])
            inp["melee"] = rnd.choice([0, 1, 1])
            if rnd.randrange(4) == 0:                   # to the Skill1 use: a live stored player, state word 3 or 19
                inp["c8"] |= 0x20000
                inp["wtype"], inp["wmode"], inp["wc6"] = 0, rnd.choice([1, 2, 6]), 0
                inp["m54"] = rnd.choice([3, 19])
                inp["skill"][0] = rnd.randrange(0, 400)
                inp["ctl14"] = u32(frame - rnd.choice((1, 1, 0, 100)))
                inp["forceother"] = 1
            if rnd.randrange(3):
                inp["c8"] |= 0x20000
            inp["ctl14"] = rnd.choice([0, u32(frame + rnd.choice((-1, 0, 1))), u32(frame + 100)])
        if fam == "imp16":
            look = (inp["otype"], inp["oguid"])
        if look is not None:
            sv = rnd.choice([0, OTHER, OTHER, TARGET, TARGET] if fam == "minion" else [0, OTHER, OTHER, TARGET])
            if inp.get("forceother"):
                sv = OTHER
            if sv == OTHER:
                inp["wguid"] = u32(look[1] + (0 if inp.get("forceother") else rnd.choice((0, 0, 0, 1))))
            elif sv == TARGET:
                inp["tguid"] = u32(look[1] + rnd.choice((0, 0, 0, 1)))
            inp["slotval"] = sv
        if fam == "suicide":
            inp["ctl14"] = rnd.choice([0, 0, u32(frame + rnd.choice((-1, 0, 1))), 1, -1])
        if fam in ("succubus", "witch"):
            inp["dist"] = max(0, rnd.choice([a[3] + rnd.choice((-1, 0, 1)), rnd.randrange(0, 40), 0]))
            if fam == "witch":
                inp["tnull"] = int(rnd.randrange(6) == 0)
            if rnd.randrange(3) == 0:                   # the stock succubus shape: Skill1..3 unset, Skill4 set
                for j in (0, 1, 2):
                    inp["skill"][j] = rnd.choice([0xFFFF, 0])
                inp["skill"][3] = rnd.randrange(1, 400)
                inp["ttype"], inp["tsl"] = rnd.choice([0, 0, 1]), None
                inp["dist"] = max(0, a[3] - 1)
        if fam == "spawner":
            inp["ctl18"] = u32(a[0] + rnd.choice((-1, 0, 1, -5)))
            inp["ctl14"] = u32(frame + rnd.choice((-1, 0, 1, -100, 100)))
            inp["dist"] = max(0, a[3] + rnd.choice((-1, 0, 1, -5)))
        if fam == "imp16i":
            inp["sklnull"] = int(rnd.randrange(8) == 0)
            for _ in range(rnd.randrange(0, 4)):
                nid = rnd.choice([inp["skill"][2], inp["skill"][4], inp["skill"][2], inp["skill"][4],
                                  rnd.randrange(1 << 16)])
                inp["skl"].append((nid, rnd.choice([0xFFFFFFFF, 0xFFFFFFFF, 0])))
        if fam == "imp":
            inp["ctl14"] = rnd.choice([0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0, 5])
            inp["mscount"] = 0x2E0
            r3 = [raip[2][j][diff] for j in range(8)]
            inp["dist"] = max(0, rnd.choice([r3[0] + rnd.choice((-1, 0, 1)), rnd.randrange(0, 40), 0]))
            for j in range(3):                          # the jitter radius: powers of two and others, 0 and below
                raip[0][1][j] = rnd.choice([14, 8, 16, 7, 1, 0, -3, 4, 25])
            if rnd.randrange(3) == 0:                   # to the helper: no host, at range, Skill1 set, R1.aip3 high
                inp["ctl14"], inp["melee"] = 0xFFFFFFFF, 0
                inp["skill"][0] = rnd.randrange(0, 400)
                raip[0][2][diff] = rnd.choice([100, 90, ds[0] + 1])
        mrec = MSBASE + 0x1A8 * cls
        sk = "".join(hx16(s) for s in inp["skill"])
        tsl = inp["tsl"]
        lines = [
            "w %08x %s" % (GAME + 0x6D, "%02x" % diff),
            "w %08x %s" % (GAME + 0xA8, hx32(frame)),
            "w %08x %s" % (GAME + 0x10F4, hx32(0)),
            "w %08x %s" % (UNIT, hx32(1) + hx32(cls)),
            "w %08x %s" % (UNIT + 0x10, hx32(1) + hx32(MDATA)),
            "w %08x %s%s" % (UNIT + 0x20, hx32(seed[0]), hx32(seed[1])),
            "w %08x %s" % (UNIT + 0x2C, hx32(UPATH)),
            "w %08x %s" % (UNIT + 0x80, hx32(GAME)),
            "w %08x %s" % (UNIT + 0x94, hx32(inp["otype"]) + hx32(inp["oguid"]) + hx32(inp["stype"])
                           + hx32(inp["sguid"])),
            "w %08x %s" % (UNIT + 0xA8, hx32(0 if inp["sklnull"] else SKL)),
            "w %08x %s" % (UNIT + 0xC4, hx32(inp["c4"]) + hx32(inp["c8"])),
            "w %08x %s" % (UPATH + 0x02, hx16(inp["ux"])), "w %08x %s" % (UPATH + 0x06, hx16(inp["uy"])),
            "w %08x %s" % (UPATH + 0x1C, hx32(ROOM)),
            "w %08x %s" % (TARGET, hx32(inp["ttype"])),
            "w %08x %s" % (TARGET + 0x0C, hx32(inp["tguid"]) + hx32(inp["tmode"])),
            "w %08x %s" % (TARGET + 0x2C, hx32(0 if inp["tpnull"] else TPATH)),
            "w %08x %s" % (TARGET + 0x5C, hx32(0 if tsl is None else TSL)),
            "w %08x %s" % (TARGET + 0xC6, "%02x" % inp["tc6"]),
            "w %08x %s" % (TARGET + 0xE4, hx32(0)),
            "w %08x %s" % (TPATH + 0x02, hx16(inp["tx"])), "w %08x %s" % (TPATH + 0x06, hx16(inp["ty"])),
            "w %08x %s" % (TPATH + 0x0C, hx32(inp["tsx"]) + hx32(inp["tsy"])),
            "w %08x %s" % (MDATA + 0x28, hx32(CTL)),
            "w %08x %s" % (MDATA + 0x54, hx32(inp["m54"])),
            "w %08x %s" % (CTL, hx32(inp["state"])),
            "w %08x %s%s%s%s" % (CTL + 0x14, hx32(inp["ctl14"]), hx32(inp["ctl18"]), hx32(inp["ctl1c"]),
                                 hx32(0 if inp["param"] is None else PARAM)),
            "w %08x %s" % (CTX, hx32(CTL) + hx32(0) + hx32(0 if inp["tnull"] else TARGET) + hx32(0) + hx32(0)
                           + hx32(inp["dist"]) + hx32(inp["melee"]) + hx32(mrec) + hx32(MS2)),
            "w %08x %s" % (mrec + 0x3E, hx16(inp["m3e"])),
            "w %08x %s" % (mrec + 0x56, "".join(hx16(aip[j][d]) for j in range(8) for d in range(3))),
            "w %08x %s" % (mrec + 0x170, sk),
            "w %08x %s" % (mrec + 0x180, "".join("%02x" % m for m in inp["skmode"])),
            "w %08x %s" % (G_DATATABLES, hx32(DTBL)),
            "w %08x %s" % (DTBL + 0xA78, hx32(MSBASE)),
            "w %08x %s" % (DTBL + 0xA80, hx32(inp["mscount"])),
        ]
        for r in range(4):
            lines.append("w %08x %s" % (IMPREC[r] + 0x56,
                                        "".join(hx16(raip[r][j][d]) for j in range(8) for d in range(3))))
        if tsl is not None:
            lines.append("w %08x %s" % (TSL + 0x10, hx32(tsl[0])))
            lines.append("w %08x %s" % (TSL + 0x3C, hx32(TNODE if tsl[1] else 0)))
            lines.append("w %08x %s" % (TNODE + 0x10, hx32(tsl[2])))
            lines.append("w %08x %s" % (TNODE + 0x2C, hx32(0)))
        if inp["param"] is not None:
            lines.append("w %08x %s" % (PARAM + 0x08, "".join(hx32(v) for v in inp["param"])))
        if look is not None:
            lines.append("w %08x %s" % (slot_addr(*look), hx32(inp["slotval"])))
            if inp["slotval"] == OTHER:
                lines.append("w %08x %s" % (OTHER, hx32(inp["wtype"])))
                lines.append("w %08x %s" % (OTHER + 0x0C, hx32(inp["wguid"]) + hx32(inp["wmode"])))
                lines.append("w %08x %s" % (OTHER + 0xC6, "%02x" % inp["wc6"]))
                lines.append("w %08x %s" % (OTHER + 0xE4, hx32(0)))
        if not inp["sklnull"]:
            nodes = inp["skl"]
            lines.append("w %08x %s" % (SKL + 0x04, hx32(SKNODE if nodes else 0)))
            for n, (nid, n34) in enumerate(nodes):
                node = SKNODE + 0x40 * n
                nxt = SKNODE + 0x40 * (n + 1) if n + 1 < len(nodes) else 0
                lines.append("w %08x %s" % (node, hx32(SKREC + 0x10 * n) + hx32(nxt)))
                lines.append("w %08x %s" % (node + 0x34, hx32(n34)))
                lines.append("w %08x %s" % (SKREC + 0x10 * n, hx16(nid)))
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
        cases, meta, mem = gen_family(fam, random.Random("r52i-" + fam))
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
    _, meta, _ = gen_family(fam, random.Random("r52i-" + fam))
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
    # The image-table reads the models account for (the unit hash offsets 0x006E10E0 read at 0x00552F9C, state
    # row 16's slot table 0x006E34E0 read at 0x005E2D16, 0x005E2D55 and 0x005E2D61); every other traced access stays.
    expect = set("R %08x %08x 4" % (pc, addr) for pc, addr in reads)
    seen = set(" ".join(x.split()[:4]) for x in traced)
    accounted = len(seen & expect)
    if expect - seen:
        bad.append("accounted reads missing %s" % sorted(expect - seen))
    traced = [x for x in traced if " ".join(x.split()[:4]) not in expect]
    line = ("AI52I %s cases=%d match=%d bad=%d stopped=%d traced=%d accounted=%d drew=%d " % (
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
    print("AI52I total cases=%d match=%d" % tuple(tot))
    print("AI52I result=%s" % ("ok" if allok else "FAIL"))


def cmd_manifest(d, write):
    rows = []
    for fam in FAMILIES:
        for ext in ("cases", "mem", "out", "err"):
            p = os.path.join(d, "%s.%s" % (fam, ext))
            if os.path.exists(p):
                rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.basename(p)))
    for extra in ("check.txt", "ai_cat_emu9.py.rev"):
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

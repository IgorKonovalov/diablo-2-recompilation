#!/usr/bin/env python3
"""Plan 0052 phase 1.2, catalogue batch 11 (bosses-B, `lane/r52k`): the think, init and `alt` functions of AI rows 51
`Diablo`, 128 `Nihlathak`, 135 `BaalCrab`, 138 `BaalToStairs`, 140 `BaalCrabClone`, 145 `UberBaal` and 147
`UberDiablo`, and the helpers they reach first (Diablo's decision 0x005E8810 and pick callback 0x005E8EB0, Baal's
decision 0x005FC630, its three weight tables and its action 0x005FCB60, the pick callbacks 0x005FC000 and 0x005EF5E0,
the unreferenced weighted pick 0x005FC130), run under Ghidra's p-code emulator (ADR-0015, ADR-0021) with
re/ghidra_scripts/EmuBoundary.java and compared with the models below. No game run, no slot. Same method as
tools/ai_cat_emu10.py (batch 10): one family per function, the `le`, `d0`, `cmp` and `u16` controls and the site
control, the EDGES line per family. Additions: two controls of this batch, `abs` (the pick callbacks' distance
without the absolute values) and `uns` (the weighted pick's cumulative compare read unsigned); register checks at a
boundary (EBX, ESI, EDI where the model predicts them) and the return value of a function that returns; a declared
parameter-record ring (AiParamsFind runs on the image), two hash slots for GameFindUnit, and a declared weight block.

    python3 -I tools/ai_cat_emu11.py cases [--dir D]      write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/ai_cat_emu11.py check [--dir D]      compare every D/<family>.out with its model, account for
                                                          every traced access, run the negative and site controls
    python3 -I tools/ai_cat_emu11.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r52k/emu. Every case draw comes from random.Random("r52k-<family>"), so `cases` regenerates
identical files.

The declared image: the game's difficulty byte (+0x6D), frame (+0xA8), quest list pointer (+0x10F4: 0, or a list
whose first word is the first node; a node holds its quest id at +0x00, the bytes +0x09, +0x0B and +0x14 and the next
node at +0xF4) and the unit hash slots GameFindUnit reads (+0x1120 + ... as 0x006E10E0 gives, or +0x1B20 for type 5);
the unit's type (+0x00, 1), class (+0x04), mode (+0x10), monster data pointer (+0x14), byte +0x18, seed (+0x20/+0x24),
path pointer (+0x2C or 0), game pointer (+0x80), owner type and guid (+0x94/+0x98), the flag word +0xC8; the unit
path's x (+0x02, u16), y (+0x06, u16) and room (+0x1C); the target's type (+0x00), class (+0x04), guid (+0x0C), mode
(+0x10), byte +0x18, path pointer (+0x2C), game pointer (+0x80), byte +0xC6 and hash next (+0xE4), that path's u16
x (+0x02) and y (+0x06), the static words +0x0C/+0x10 and room (+0x1C); two more units (0x12E00000, 0x12E10000:
type, guid, mode, +0xC6, +0xE4); the monster data's AI control pointer (+0x28); the AI control's state (+0x00),
+0x14, +0x18, +0x1C, the parameter ring pointer (+0x20) and the owner words +0x28 (a game pointer or 0), +0x2C
(guid) and +0x30 (type); the parameter ring (node k at 0x13100000 + 0x40 k: +0x00 next, +0x08 kind, +0x0C x, +0x10
y; the last node's next is the first); the AiCtx (+0x00 ctl, +0x08 target, +0x14 distance, +0x18 melee, +0x1C
MonStats record, +0x20 MonStats2 record); the MonStats record of the unit's class (DataTables +0xA78 + class *
0x1A8: aip block +0x56..+0x85, Skill1..8 +0x170..+0x17F and Sk1..8mode +0x180..+0x187); the DataTables pointer
(0x00744304), its MonStats base (+0xA78) and count (+0xA80); the weight block (0x13200000, sixteen words).

Callees that run on the declared image (not boundaries): AiParamsFind 0x0058EEF0; the position getters 0x0045ADF0,
0x0045AE20 with 0x006488C0, 0x00648900; UnitGetRoom 0x00620BB0 with 0x00648A80; AiDistToPoint 0x005DC530;
UnitGetGame 0x00554010; QUESTS_FindById 0x00543640 (inside A5Q4_NihlathakSeen 0x0058BC40, which runs whole up to its
QUESTS_SetState call); MonsterOwner 0x0058F0D0; GameFindUnit 0x00552F60; UnitIsDead 0x005541B0; UnitGetOwner
0x00552FD0; Baal's action calling itself (0x005FCD80, 0x005FCE81). Every other callee the function reaches is an
observed boundary. The claim per case: the first boundary reached (or the function's return and its EAX), its call
site (the return address), the registers and stack arguments the callee takes, the unit seed, the AI control's
+0x14/+0x18/+0x1C at the boundary, and where the model names them the frame words a pointer argument or the code's
own locals hold (the parameter block, the search block, a weight table) and the quest node's byte +0x14.

Families (function, row):
  dalt     0x005E8480 rows 51/147 alt        balt     0x005FCF30 rows 135/140/145 alt
  diablo   0x005E9170 row 51 Diablo          ddec     0x005E8810 Diablo's decision
  dcb      0x005E8EB0 Diablo's pick callback bcb      0x005FC000 Baal's pick callback
  nihli    0x005EE5C0 row 128 init           nihl     0x005EE5D0 row 128 Nihlathak (with 0x0058BC40)
  stairs   0x005EF620 row 138 BaalToStairs   pcb      0x005EF5E0 row 138's search callback
  bcrab    0x005FCFE0 row 135 BaalCrab       bclone   0x005FD210 row 140 BaalCrabClone
  bdec     0x005FC630 Baal's decision        bact     0x005FCB60 Baal's action
  bmelee   0x005FC1C0 Baal's melee table     bblock   0x005FC300 Baal's blocked-line table
  branged  0x005FC450 Baal's clear-line table wpick   0x005FC130 the unreferenced weighted pick
  uberd    0x005E9DF0 row 147 UberDiablo     uberb    0x005FD200 row 145 UberBaal

Controls: `le` compares each draw (the weighted pick's draw against its cumulative weight) with `<=` instead of `<`;
`d0` reads the difficulty as Normal; `cmp` switches the strictness of every compare that is not a draw (`<` and `<=`,
`>` and `>=`); `u16` reads the Skill6/Skill7 tests of Baal's action unsigned, though the kept run's 6 separating cases all hold a
negative Skill6 and none separates the Skill7 test (ai/0012 section 4); `abs` drops the pick callbacks'
absolute values; `uns` reads the weighted pick's cumulative compare unsigned; `site` expects each call site one byte
later. Each must fail every case it separates. The `EDGES` line under each family counts, per compare, the cases that
meet it at equality (the only cases in which a strictness control can separate that compare); a compare missing from
it has no control in the run.

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
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r52k", "emu")

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
OTHER2 = 0x12E10000
QLIST = 0x12F00000
QNODE = 0x12F00100           # node k at QNODE + 0x100 k
MSBASE = 0x13000000          # DataTables +0xA78: MonStats record c at MSBASE + 0x1A8 c
PRM = 0x13100000             # parameter ring node k at PRM + 0x40 k
WTS = 0x13200000             # the weighted pick's weight block
G_DATATABLES = 0x00744304
HASHOFF = (0x1120, 0x1320, 0x1520, 0x1920, 0x1720)   # 0x006E10E0, u32 per unit type 0..4 (objdump -s of .rdata)
STK_LO = 0x7FEFFC00
STK_LEN = 1040
EBP = 0x7FEFFFFC
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)

HASSTATE, PARAMSPUSH, PICKPLR, COLL, PORTALGET, LEFTSKILL, QSETSTATE, SEARCH, EDGEDIST, BPICK = (
    0x00639DF0, 0x0058EF40, 0x005E8F20, 0x0064D910, 0x005353F0, 0x00620190, 0x00544300, 0x005DD0B0, 0x006416D0,
    0x005FBDD0)
KILLED, DISTSIZED, MELEE, IDLE, WALKTOWARD, T56, RING, WALKPOINT, MAXHP, USESKILL = (
    0x0057CCB0, 0x005DC480, 0x00622C40, 0x005DE080, 0x005DE6D0, 0x005DF7D0, 0x005DE200, 0x005DED90, 0x00625D10,
    0x005DEAD0)
SETMODEAT, SKADD, CLONESPAWN, LIFEPCT, DISTUNITS = (0x005DDF90, 0x00647280, 0x005FC860, 0x00621F20, 0x005DC380)
EXTRA = (0x00639DB0, 0x006201D0, 0x00625480, 0x005DD290, 0x005DE190, 0x005DECA0, 0x005DEE50, 0x005DE0F0,
         0x0058E600, 0x005DF850, 0x00643CE0, 0x006439F0, 0x005FC0C0, 0x0061A1B0, 0x006417F0,
         0x0063EFA0, 0x00573930, 0x005DDFC0, 0x00540E60)   # 0x005FC630 is a family entry, not observed
OBSERVE = tuple(sorted(set((HASSTATE, PARAMSPUSH, PICKPLR, COLL, PORTALGET, LEFTSKILL, QSETSTATE, SEARCH, EDGEDIST,
                            BPICK, KILLED, DISTSIZED, MELEE, IDLE, WALKTOWARD, T56, RING, WALKPOINT, MAXHP, USESKILL,
                            SETMODEAT, SKADD, CLONESPAWN, LIFEPCT, DISTUNITS) + EXTRA)))
RET = "ret"

FNS = {"dalt": 0x005E8480, "balt": 0x005FCF30, "diablo": 0x005E9170, "ddec": 0x005E8810, "dcb": 0x005E8EB0,
       "bcb": 0x005FC000, "nihli": 0x005EE5C0, "nihl": 0x005EE5D0, "stairs": 0x005EF620, "pcb": 0x005EF5E0,
       "bcrab": 0x005FCFE0, "bclone": 0x005FD210, "bdec": 0x005FC630, "bact": 0x005FCB60, "bmelee": 0x005FC1C0,
       "bblock": 0x005FC300, "branged": 0x005FC450, "wpick": 0x005FC130, "uberd": 0x005E9DF0, "uberb": 0x005FD200}
FAMILIES = tuple(FNS)
NCASES = 240
CONTROLS = ("le", "d0", "cmp", "u16", "abs", "uns")


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
    """One case's inputs and the model's running state (the unit seed, the AI control's +0x14/+0x18/+0x1C)."""

    def __init__(self, inp, neg=None):
        self.i, self.neg = inp, neg
        self.seed = list(inp["seed"])
        self.c14, self.c18, self.c1c = inp["ctl14"], inp["ctl18"], inp["ctl1c"]
        self.eq = set()
        self.reads = set()
        self.tags = set()

    def diff(self):
        return 0 if self.neg == "d0" else self.i["diff"]

    def lt(self, a, b, edge):               # signed a < b
        if a == b:
            self.eq.add(edge)
        return a <= b if self.neg == "cmp" else a < b

    def le(self, a, b, edge):
        if a == b:
            self.eq.add(edge)
        return a < b if self.neg == "cmp" else a <= b

    def sk(self, k):
        return s16(self.i["skill"][k - 1])

    def skm(self, k):
        return self.i["skmode"][k - 1]

    # ---- the callees run on the image
    def ufield(self, u):                    # type, guid, mode, +0xC6 of a unit the lookups can return
        i = self.i
        if u == TARGET:
            return i["ttype"], i["tguid"], i["tmode"], i["tc6"]
        if u == OTHER:
            return i["wtype"], i["wguid"], i["wmode"], i["wc6"]
        return i["w2type"], i["w2guid"], i["w2mode"], i["w2c6"]

    def findunit(self, typ, guid):          # sub_00552F60_GameFindUnit on the declared slots
        if typ > 5:
            return 0
        if typ <= 4:
            self.reads.add((0x00552F9C, 0x006E10E0 + 4 * typ))
        u = self.i["slots"].get(slot_addr(typ, guid), 0)
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

    def upos(self):                         # UnitGetSubX/Y (and PathGetX/Y) of the acting unit (type 1)
        i = self.i
        return (0, 0) if i["upnull"] else (i["ux"], i["uy"])

    def tpos(self):                         # UnitGetSubX/Y of the target
        i = self.i
        if i["ttype"] in (2, 4, 5):
            return i["tsx"], i["tsy"]
        if i["tpnull"]:
            return 0, 0
        return i["tx"], i["ty"]

    def params(self, kind):                 # sub_0058EEF0_AiParamsFind(U, kind, 0): the node index or None
        ring = self.i["ring"]
        if not ring:
            return None
        n = len(ring)
        e = 1 % n                            # [P]: the first node's next
        while True:
            if ring[e][0] == kind:
                return e
            if e == 0:
                return None
            e = (e + 1) % n

    def hit(self, fn, site, args, ecx=GAME, edx=UNIT, block=None, regs=None, eax=None, qbyte=None):
        raise Hit((fn, site, ecx, edx, [u32(a) for a in args], list(self.seed), u32(self.c14), u32(self.c18),
                   u32(self.c1c), block, regs or {}, eax, qbyte))

    def ret(self, eax=None):
        self.hit(RET, 0, [], eax=eax)


def m_alt(e, base):                                     # 0x005E8480 / 0x005FCF30 (the same code)
    k = e.params(10)
    x, y = (e.i["ring"][k][1], e.i["ring"][k][2]) if k is not None else (0, 0)
    e.tags.add("found" if k is not None else "none")
    e.hit(HASSTATE, C(base + 0x35), [UNIT, 12], ecx=None, edx=None, block=(EBP - 4, [y]), regs={"ebx": x})


def m_dalt(e):
    m_alt(e, 0x005E8480)


def m_balt(e):
    m_alt(e, 0x005FCF30)


def m_diablo(e):                                        # row 51, 0x005E9170
    k = e.params(10)
    if k is None:
        x, y = e.upos()
        e.hit(PARAMSPUSH, C(0x005E9204), [EBP - 0x34], block=(EBP - 0x2C, [10, x, y]))
    e.hit(PICKPLR, C(0x005E922C), [EBP - 0x14, EBP - 0x10, PRM + 0x40 * k, 0x005E8EB0])


def m_ddec(e):                                          # 0x005E8810 (ECX ctl, EDX U; t, score, count, h)
    i = e.i
    if e.c14 != 0:
        e.ret(eax=e.c14)
    if i["tnull"]:
        x, y = e.upos()
        e.hit(COLL, C(0x005E889C), [0 if i["upnull"] else ROOM, x, y, 2, 0x40], ecx=None, edx=None)
    if i["ttype"] == 0:
        e.hit(PORTALGET, C(0x005E8920), [], ecx=TARGET, edx=None)
    e.hit(LEFTSKILL, C(0x005E8971), [TARGET], ecx=None, edx=None)


def dist_to_point(e, ux, uy, x, y):                     # sub_005DC530_AiDistToPoint
    dx, dy = s32(ux - x), s32(uy - y)
    if e.neg != "abs":
        dx = s32(-dx) if dx < 0 else dx
        dy = s32(-dy) if dy < 0 else dy
    if dx > dy:
        v = s32(dy + 2 * dx)
    else:
        v = s32(dx + 2 * dy)
    return s32(int(v / 2)) if v < 0 else v >> 1        # cdq; sub eax,edx; sar 1: toward zero


def m_cb(e):                                            # 0x005E8EB0 / 0x005FC000 (ECX a = TARGET, EDX b = UNIT)
    i = e.i
    if i["tb18"] != i["ub18"]:
        e.ret(eax=0)
    x, y = e.tpos()
    ux, uy = e.upos()
    d = dist_to_point(e, ux, uy, x, y)
    if u32(d) == 0x3FC:
        e.eq.add("d<1020")
    below = u32(d) <= 0x3FC if e.neg == "cmp" else u32(d) < 0x3FC
    e.tags.add("near" if below else "far")
    e.ret(eax=1 if below else 0)


def m_nihli(e):                                         # row 128 init, 0x005EE5C0: ret 4
    e.ret()


def m_nihl(e):                                          # row 128, 0x005EE5D0 (with 0x0058BC40 on the image)
    i = e.i
    k = None
    for n, qid in enumerate(i["quests"]):
        if qid == 0x22:
            k = n
            break
    if k is not None and i["q09"][k] != 0:
        if e.lt(i["q0b"][k], 3, "q0b<3"):
            e.tags.add("quest-step")
            e.hit(QSETSTATE, C(0x0058BC6D), [0, 0x0058AEA0, 1], ecx=QNODE + 0x100 * k, edx=None,
                  qbyte=(QNODE + 0x100 * k + 0x14, 0))
    e.hit(HASSTATE, C(0x005EE601), [UNIT, 12], ecx=None, edx=None,
          qbyte=(QNODE + 0x100 * k + 0x14, i["q14"][k]) if k is not None else None)


def m_stairs(e):                                        # row 138, 0x005EF620
    e.hit(SEARCH, C(0x005EF653), [EBP - 0x28, 0x005EF5E0, 1], block=(EBP - 0x28, [0, 0x19]))


def m_pcb(e):                                           # 0x005EF5E0 (ECX -, EDX searcher; cand, blk)
    i = e.i
    if i["tnull"] or i["ttype"] != 2 or i["tcls"] != 0x233:
        e.ret(eax=0)
    e.hit(EDGEDIST, C(0x005EF5FB), [TARGET, UNIT], ecx=None, edx=None)


def m_bcrab(e):                                         # row 135, 0x005FCFE0
    e.hit(BPICK, C(0x005FD007), [GAME, EBP - 8, EBP - 4, 0, 0x005FC000], ecx=EBP - 8, regs={"ebx": UNIT},
          block=(EBP - 8, [0, 0]))


def m_bclone(e):                                        # row 140, 0x005FD210
    i = e.i
    o = 0
    if i["c28"]:                                        # sub_0058F0D0_MonsterOwner
        o = e.findunit(i["c30"], i["c2c"])
    if o and e.dead(o):
        e.tags.add("owner-dead")
        e.hit(KILLED, C(0x005FD338), [0, 1])
    w = e.findunit(i["otype"], i["oguid"]) if i["c8"] & 0x400 else 0     # sub_00552FD0_UnitGetOwner
    if not w or e.dead(w):
        e.tags.add("no-owner" if not w else "owner2-dead")
        e.hit(KILLED, C(0x005FD338), [0, 1])
    e.tags.add("alive")
    e.hit(BPICK, C(0x005FD26E), [GAME, EBP - 8, EBP - 4, 0, 0x005FC000], ecx=EBP - 8, edx=None, regs={"ebx": UNIT},
          block=(EBP - 8, [0, 0]))


def m_bdec(e):                                          # 0x005FC630 (ECX U, EAX t; G, ctl, score, count, h)
    i = e.i
    if e.c14 != 0:
        e.ret(eax=e.c14)
    if i["tnull"]:
        x, y = e.upos()
        e.hit(COLL, C(0x005FC6B5), [0 if i["upnull"] else ROOM, x, y, 2, 0x40], ecx=None, edx=None)
    if i["ttype"] == 0:
        e.hit(PORTALGET, C(0x005FC72A), [], ecx=TARGET, edx=None)
    if i["hnull"] == 0:
        k = i["hidx"]
        e.hit(DISTSIZED, C(0x005FC78C), [i["ring"][k][2]], ecx=TARGET, edx=i["ring"][k][1])
    e.hit(MELEE, C(0x005FC7AB), [UNIT, TARGET, 0], ecx=None, edx=None)


def m_bact(e):                                          # 0x005FCB60 (ECX G, EDX U; ctl, t, k, h)
    i = e.i
    t = 0 if i["tnull"] else TARGET
    h = None if i["hnull"] else PRM + 0x40 * i["hidx"]
    k = i["k"]
    cls = s32(i["cls"])
    while True:
        if cls < 0 or e.le(i["mscount"], cls, "count<=cls"):
            e.ret()
        k1 = u32(k - 1)
        if k1 > 14:
            e.hit(IDLE, C(0x005FCE9F), [5])
        e.reads.add((0x005FCBC0, 0x005FCEF0 + 4 * k1))      # g_AiBaalActJumps
        if k == 1:
            d = e.diff()
            if d == 1:
                e.hit(IDLE, C(0x005FCEE2), [15])
            if d == 2:
                e.hit(IDLE, C(0x005FCECA), [5])
            e.hit(IDLE, C(0x005FCEE2), [35])
        if k in (2, 6):
            e.hit(WALKTOWARD, C(0x005FCC2C), [t, 12, 0])
        if k == 3:
            e.hit(T56, C(0x005FCC15), [t, 6, 1])
        if k == 4:
            e.hit(RING, C(0x005FCBFE), [16])
        if k == 5:
            if h is None:
                e.hit(IDLE, C(0x005FCE9F), [5])
            r = i["ring"][i["hidx"]]
            e.hit(WALKPOINT, C(0x005FCBEA), [r[1], r[2]])
        if k == 7:
            e.hit(IDLE, C(0x005FCE9F), [5])
        if k == 8:
            if not t:
                k = 0
                continue
            s6, s7 = e.sk(6), e.sk(7)
            if e.neg == "u16":
                s6, s7 = s6 & 0xFFFF, s7 & 0xFFFF
            if s6 > 0:
                e.hit(MAXHP, C(0x005FCCEB), [TARGET], ecx=None, edx=None)
            if s7 > 0 and i["ttype"] == 0:
                e.hit(USESKILL, C(0x005FCD60), [e.skm(7), e.sk(7), t, 0, 0])
            e.tags.add("k8-nothing")
            e.ret()
        if k == 9:
            e.hit(USESKILL, C(0x005FCC4A), [9, 0x13B, t, 0, 0])
        if k == 10:
            e.hit(SETMODEAT, C(0x005FCCB4), [5, t])
        if k == 11:
            e.hit(SKADD, C(0x005FCC6C), [UNIT, 0x13C, 1, 0, 0x006E3580, 0x452], ecx=None, edx=None)
        if k == 12:
            e.hit(USESKILL, C(0x005FCCD2), [8, 0x13D, t, 0, 0])
        if k == 13:
            e.hit(USESKILL, C(0x005FCC9F), [4, 0x13E, t, 0, 0])
        if k == 14:
            if not t:
                e.tags.add("k14-recurse")
                k = 0
                continue
            e.hit(EDGEDIST, C(0x005FCDB8), [UNIT, TARGET], ecx=None, edx=None)
        if k == 15:
            e.hit(CLONESPAWN, C(0x005FCE94), [GAME, CTL], ecx=None, edx=None, regs={"esi": UNIT})
        raise AssertionError("bact k=%d" % k)


def m_bmelee(e):                                        # 0x005FC1C0 (EAX U; G, t, lc)
    nm = e.diff() == 0
    w = [0, None, 0, 0, 0, 0, 0, 0, 20, 30, 150, 10, 10, 45 if nm else 70, 40, 0]
    e.hit(LIFEPCT, C(0x005FC22C), [TARGET], ecx=None, edx=None, block=(EBP - 0x40, w), regs={"edi": 75 if nm else 50})


def m_bblock(e):                                        # 0x005FC300 (ESI U; G, t, n, far, vfar)
    i = e.i
    nm = e.diff() == 0
    few = e.lt(s32(i["count"]), 2, "n<2")
    w = [0, None, 45 if few else 20, 20, 20, 0, 20, 0, 80, 70, 25 if few else 0, 0, 0, 0, 0, 0]
    e.hit(LIFEPCT, C(0x005FC367), [UNIT], ecx=None, edx=None, block=(EBP - 0x48, w), regs={"edi": 125 if nm else 100})


def m_branged(e):                                       # 0x005FC450 (EAX U; G, ctl, t, n, far, vfar, P, score)
    nm = e.diff() == 0
    v = u32(10 * u32(2 - e.c18))
    w15 = 0 if s32(v) < 0 else v
    w = [0, None, 5, 5, 5, 0, 5, 0, 40, 40, 0, 70, 80, 40 if nm else 60, 20, w15]
    e.hit(DISTUNITS, C(0x005FC4CF), [], ecx=UNIT, edx=TARGET, block=(EBP - 0x54, w), regs={"edi": 125 if nm else 100})


def m_wpick(e):                                         # 0x005FC130 (EAX unit; w, n): pure
    i = e.i
    n = s32(i["n"])
    w = i["w"]
    s = 0
    if n > 0:
        for k in range(n):
            s = u32(s + w[k])
    r = 0
    if s32(s) > 0:
        step(e.seed)
        r = e.seed[0] & (s - 1) if s & (s - 1) == 0 else e.seed[0] % s
    c = 0
    for k in range(max(0, n)):
        c = u32(c + w[k])
        if s32(r) == s32(c):
            e.eq.add("r<c")
        if e.neg == "uns":
            hitk = u32(r) < u32(c)
        elif e.neg == "le":
            hitk = s32(r) <= s32(c)
        else:
            hitk = s32(r) < s32(c)
        if hitk:
            e.tags.add("picked")
            e.ret(eax=k)
    e.tags.add("fallback")
    e.ret(eax=1)


def m_uber(e):
    e.ret()


MODELS = {"dalt": m_dalt, "balt": m_balt, "diablo": m_diablo, "ddec": m_ddec, "dcb": m_cb, "bcb": m_cb,
          "nihli": m_nihli, "nihl": m_nihl, "stairs": m_stairs, "pcb": m_pcb, "bcrab": m_bcrab, "bclone": m_bclone,
          "bdec": m_bdec, "bact": m_bact, "bmelee": m_bmelee, "bblock": m_bblock, "branged": m_branged,
          "wpick": m_wpick, "uberd": m_uber, "uberb": m_uber}


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
def gen_family(fam, rnd):
    cases, meta = [], []
    for k in range(NCASES):
        seed = (rnd.randrange(1 << 32), rnd.randrange(1 << 32))
        diff = k % 3
        frame = rnd.randrange(100, 100000)
        cls = rnd.choice([243, 333, 705, 526, 544, 559, 570, 709, rnd.randrange(0x2E0)])
        inp = {
            "fam": fam, "seed": seed, "diff": diff, "frame": frame, "cls": cls,
            "melee": rnd.randrange(2), "dist": rnd.randrange(0, 60),
            "ctl14": rnd.choice([0, 0, 0, 5, 1, 9, 15, rnd.randrange(1 << 32)]),
            "ctl18": rnd.choice([0, 0, 1, 2, 3, -1 & 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF, rnd.randrange(1 << 32)]),
            "ctl1c": rnd.choice([0, 1, rnd.randrange(1 << 32)]),
            "skill": [rnd.choice([0xFFFF, 0xFFFF, 0x8000, 0xFFFE, 0x7FFF, 0, 1, rnd.randrange(0, 400)]) & 0xFFFF
                      for _ in range(8)],
            "skmode": [rnd.choice([rnd.randrange(16), rnd.randrange(0x80, 0x100)]) for _ in range(8)],
            "ux": rnd.randrange(1 << 16), "uy": rnd.randrange(1 << 16), "upnull": 0,
            "tx": rnd.randrange(1 << 16), "ty": rnd.randrange(1 << 16),
            "tsx": rnd.randrange(1 << 32), "tsy": rnd.randrange(1 << 32),
            "ttype": rnd.choice([0, 0, 1, 1, 2, 3, 4, 5]), "tguid": rnd.randrange(1 << 32),
            "tcls": rnd.choice([0x233, 0x233, 0x232, 0x234, rnd.randrange(0x300)]),
            "tmode": rnd.choice([0, 1, 4, 12, 17]), "tc6": rnd.choice([0, 0, 0, 1]),
            "tb18": rnd.randrange(5), "ub18": rnd.randrange(5),
            "mscount": rnd.choice([0x2E0, 0x2E0, 0x2E0, cls, cls + 1, cls - 1, 0]),
            "c8": rnd.choice([0, 0x400, 0x400, rnd.randrange(1 << 32)]),
            "otype": rnd.randrange(6), "oguid": rnd.randrange(1 << 32),
            "c28": 0, "c2c": rnd.randrange(1 << 32), "c30": rnd.randrange(6),
            "wtype": 1, "wguid": 0, "wmode": 1, "wc6": 0, "w2type": 1, "w2guid": 0, "w2mode": 1, "w2c6": 0,
            "slots": {}, "tnull": 0, "hnull": 1, "hidx": 0, "ring": [], "k": 0, "count": rnd.randrange(-2, 6),
            "quests": [], "q09": [], "q0b": [], "q14": [], "n": 0, "w": [0] * 16,
        }
        inp["tpnull"] = int(inp["ttype"] not in (2, 4, 5) and rnd.randrange(6) == 0)
        if fam in ("ddec", "bdec") and rnd.randrange(3):
            inp["ctl14"] = 0                            # most cases past the forced-action test
        if fam in ("dalt", "balt", "diablo", "bdec", "bact"):          # the parameter ring
            n = rnd.choice([0, 0, 1, 1, 2, 3])
            inp["ring"] = [[rnd.choice([10, 10, 9, 11, 0]), rnd.choice([0, rnd.randrange(1 << 16)]),
                            rnd.choice([0, rnd.randrange(1 << 16)])] for _ in range(n)]
            if fam in ("bdec", "bact") and n and rnd.randrange(3):
                inp["hnull"], inp["hidx"] = 0, rnd.randrange(n)
        if fam in ("diablo", "ddec", "bdec", "dcb", "bcb") and rnd.randrange(6) == 0:
            inp["upnull"] = 1
        if fam in ("ddec", "bdec", "bact", "pcb") and rnd.randrange(5) == 0:
            inp["tnull"] = 1
        if fam in ("dcb", "bcb"):
            if rnd.randrange(3):
                inp["tb18"] = inp["ub18"]
            if rnd.randrange(3) == 0:                   # near the 1020 edge
                ux, uy = inp["ux"], inp["uy"]
                inp["ttype"] = rnd.choice([0, 1])
                inp["tpnull"] = 0
                dx, dy = rnd.choice([(0x3FC, 0), (0x3FB, 0), (0x3FD, 0), (0x2A8, 0x2A8), (0x2A8, 0x2A9),
                                     (0x2A7, 0x2A8), (0x1FE, 0), (0, 0x3FC)])
                inp["tx"] = (ux + rnd.choice([dx, -dx])) & 0xFFFF
                inp["ty"] = (uy + rnd.choice([dy, -dy])) & 0xFFFF
                inp["upnull"] = 0
        if fam == "pcb" and rnd.randrange(2):
            inp["ttype"] = 2
        if fam == "nihl":
            n = rnd.choice([0, 1, 1, 2, 2])
            inp["quests"] = [rnd.choice([0x22, 0x22, 0x21, 0x23, 0]) for _ in range(n)]
            inp["q09"] = [rnd.choice([0, 1, 1, 0xFF]) for _ in range(n)]
            inp["q0b"] = [rnd.choice([0, 1, 2, 3, 3, 4, 0xFF]) for _ in range(n)]
            inp["q14"] = [rnd.choice([0, 1, 0x7F]) for _ in range(n)]
        if fam == "bclone":
            inp["c28"] = rnd.choice([0, GAME, GAME])
            inp["c8"] |= rnd.choice([0x400, 0x400, 0])
            looks = []
            if inp["c28"]:
                looks.append((inp["c30"], inp["c2c"], OTHER2))
            if inp["c8"] & 0x400:
                looks.append((inp["otype"], inp["oguid"], OTHER))
            for typ, guid, u in looks:                  # every slot a lookup reads is declared (0: no unit)
                inp["slots"].setdefault(slot_addr(typ, guid), 0)
            for typ, guid, u in looks:
                if rnd.randrange(5) == 0:
                    continue
                inp["slots"][slot_addr(typ, guid)] = u
                g = u32(guid + rnd.choice((0, 0, 0, 0, 1)))
                mode = rnd.choice([1, 1, 4, 0, 12, 17])
                ut = rnd.choice([1, 1, 0, 2])
                c6 = rnd.choice([0, 0, 0, 1])
                if u == OTHER:
                    inp["wguid"], inp["wmode"], inp["wtype"], inp["wc6"] = g, mode, ut, c6
                else:
                    inp["w2guid"], inp["w2mode"], inp["w2type"], inp["w2c6"] = g, mode, ut, c6
        if fam == "bact":
            inp["k"] = rnd.choice(list(range(16)) + list(range(1, 16)) + [8, 8, 8, 14, 14, 16, 0xFFFFFFFF, 100])
            if rnd.randrange(8) == 0:
                inp["cls"] = rnd.choice([0xFFFFFFFF, 0x80000000])
            if inp["k"] == 8 and rnd.randrange(2):
                inp["skill"][5] = rnd.choice([0, 0xFFFF, 1])
        if fam == "wpick":
            inp["n"] = rnd.choice([0, 1, 2, 4, 8, 16, 16, 16, -1 & 0xFFFFFFFF])
            mode = rnd.randrange(4)
            ws = []
            for _ in range(16):
                if mode == 0:
                    ws.append(rnd.choice([0, 0, 5, 10, 20, 25, 40, 50, 75, 100]))
                elif mode == 1:
                    ws.append(rnd.choice([0, 1, 2, 4, 8, 16]))
                elif mode == 2:
                    ws.append(rnd.choice([0, 0, 10, -10 & 0xFFFFFFFF, 30, -5 & 0xFFFFFFFF]))
                else:
                    ws.append(rnd.choice([0, 0, 0, 0x40000000, 0x7FFFFFFF, 3]))
            if mode == 1 and rnd.randrange(2):          # a power-of-two sum
                ws = [0] * 16
                ws[rnd.randrange(16)] = rnd.choice([1, 2, 4, 8, 16, 32, 64, 128])
                ws[rnd.randrange(16)] += rnd.choice([0, 0])
            inp["w"] = ws
        mrec = MSBASE + 0x1A8 * (inp["cls"] & 0xFFFF)
        sk = "".join(hx16(s) for s in inp["skill"])
        lines = [
            "w %08x %s" % (GAME + 0x6D, "%02x" % diff),
            "w %08x %s" % (GAME + 0xA8, hx32(frame)),
            "w %08x %s" % (GAME + 0x10F4, hx32(QLIST if inp["quests"] else 0)),
            "w %08x %s" % (UNIT, hx32(1) + hx32(inp["cls"])),
            "w %08x %s" % (UNIT + 0x10, hx32(1) + hx32(MDATA)),
            "w %08x %s" % (UNIT + 0x18, "%02x" % inp["ub18"]),
            "w %08x %s%s" % (UNIT + 0x20, hx32(seed[0]), hx32(seed[1])),
            "w %08x %s" % (UNIT + 0x2C, hx32(0 if inp["upnull"] else UPATH)),
            "w %08x %s" % (UNIT + 0x80, hx32(GAME)),
            "w %08x %s" % (UNIT + 0x94, hx32(inp["otype"]) + hx32(inp["oguid"])),
            "w %08x %s" % (UNIT + 0xC8, hx32(inp["c8"])),
            "w %08x %s" % (UPATH + 0x02, hx16(inp["ux"])), "w %08x %s" % (UPATH + 0x06, hx16(inp["uy"])),
            "w %08x %s" % (UPATH + 0x1C, hx32(ROOM)),
            "w %08x %s" % (TARGET, hx32(inp["ttype"]) + hx32(inp["tcls"])),
            "w %08x %s" % (TARGET + 0x0C, hx32(inp["tguid"]) + hx32(inp["tmode"])),
            "w %08x %s" % (TARGET + 0x18, "%02x" % inp["tb18"]),
            "w %08x %s" % (TARGET + 0x2C, hx32(0 if inp["tpnull"] else TPATH)),
            "w %08x %s" % (TARGET + 0x80, hx32(GAME)),
            "w %08x %s" % (TARGET + 0xC6, "%02x" % inp["tc6"]),
            "w %08x %s" % (TARGET + 0xE4, hx32(0)),
            "w %08x %s" % (TPATH + 0x02, hx16(inp["tx"])),
            "w %08x %s" % (TPATH + 0x06, hx16(inp["ty"])),
            "w %08x %s" % (TPATH + 0x0C, hx32(inp["tsx"]) + hx32(inp["tsy"])),
            "w %08x %s" % (TPATH + 0x1C, hx32(TROOM)),
            "w %08x %s" % (MDATA + 0x28, hx32(CTL)),
            "w %08x %s" % (CTL, hx32(0)),
            "w %08x %s%s%s%s" % (CTL + 0x14, hx32(inp["ctl14"]), hx32(inp["ctl18"]), hx32(inp["ctl1c"]),
                                 hx32(PRM if inp["ring"] else 0)),
            "w %08x %s" % (CTL + 0x28, hx32(inp["c28"]) + hx32(inp["c2c"]) + hx32(inp["c30"])),
            "w %08x %s" % (CTX, hx32(CTL) + hx32(0) + hx32(0 if inp["tnull"] else TARGET) + hx32(0) + hx32(0)
                           + hx32(inp["dist"]) + hx32(inp["melee"]) + hx32(mrec) + hx32(MS2)),
            "w %08x %s" % (mrec + 0x170, sk),
            "w %08x %s" % (mrec + 0x180, "".join("%02x" % m for m in inp["skmode"])),
            "w %08x %s" % (G_DATATABLES, hx32(DTBL)),
            "w %08x %s" % (DTBL + 0xA78, hx32(MSBASE)),
            "w %08x %s" % (DTBL + 0xA80, hx32(inp["mscount"])),
            "w %08x %s" % (WTS, "".join(hx32(x) for x in inp["w"])),
        ]
        for n, (kind, x, y) in enumerate(inp["ring"]):
            nxt = PRM + 0x40 * ((n + 1) % len(inp["ring"]))
            lines.append("w %08x %s" % (PRM + 0x40 * n, hx32(nxt) + hx32(0) + hx32(kind) + hx32(x) + hx32(y)))
        if inp["quests"]:
            lines.append("w %08x %s" % (QLIST, hx32(QNODE)))
            for n, qid in enumerate(inp["quests"]):
                node = QNODE + 0x100 * n
                nxt = QNODE + 0x100 * (n + 1) if n + 1 < len(inp["quests"]) else 0
                lines.append("w %08x %s" % (node, hx32(qid)))
                lines.append("w %08x %s" % (node + 0x09, "%02x" % inp["q09"][n]))
                lines.append("w %08x %s" % (node + 0x0B, "%02x" % inp["q0b"][n]))
                lines.append("w %08x %s" % (node + 0x14, "%02x" % inp["q14"][n]))
                lines.append("w %08x %s" % (node + 0xF4, hx32(nxt)))
        for addr, u in sorted(inp["slots"].items()):
            lines.append("w %08x %s" % (addr, hx32(u)))
        for u, (ty, gu, mo, c6) in ((OTHER, (inp["wtype"], inp["wguid"], inp["wmode"], inp["wc6"])),
                                    (OTHER2, (inp["w2type"], inp["w2guid"], inp["w2mode"], inp["w2c6"]))):
            lines.append("w %08x %s" % (u, hx32(ty)))
            lines.append("w %08x %s" % (u + 0x0C, hx32(gu) + hx32(mo)))
            lines.append("w %08x %s" % (u + 0xC6, "%02x" % c6))
            lines.append("w %08x %s" % (u + 0xE4, hx32(0)))
        lines += ["d %08x %d" % (STK_LO, STK_LEN), "d %08x 8" % (UNIT + 0x20), "d %08x 12" % (CTL + 0x14)]
        if inp["quests"]:
            lines.append("d %08x %d" % (QNODE, 0x100 * len(inp["quests"])))
        f = FNS[fam]
        t = 0 if inp["tnull"] else TARGET
        h = 0 if inp["hnull"] else PRM + 0x40 * inp["hidx"]
        if fam == "ddec":
            call = "call %08x %08x %08x %08x %08x %08x %08x" % (f, CTL, UNIT, t, inp["frame"] & 0xFF, inp["count"] & 0xFFFFFFFF, h)
        elif fam in ("dcb", "bcb"):
            call = "call %08x %08x %08x" % (f, TARGET, UNIT)
        elif fam == "pcb":
            call = "call %08x %08x %08x %08x %08x" % (f, GAME, UNIT, t, CTX)
        elif fam == "bdec":
            lines.append("r eax %08x" % t)
            call = "call %08x %08x %08x %08x %08x %08x %08x %08x" % (f, UNIT, 0, GAME, CTL, 0, inp["count"] & 0xFFFFFFFF, h)
        elif fam == "bact":
            call = "call %08x %08x %08x %08x %08x %08x %08x" % (f, GAME, UNIT, CTL, t, inp["k"], h)
        elif fam == "bmelee":
            lines.append("r eax %08x" % UNIT)
            call = "call %08x %08x %08x %08x %08x %08x" % (f, 0, 0, GAME, TARGET, inp["melee"])
        elif fam == "bblock":
            lines.append("r esi %08x" % UNIT)
            call = "call %08x %08x %08x %08x %08x %08x %08x %08x" % (f, 0, 0, GAME, TARGET, inp["count"] & 0xFFFFFFFF, 0, 0)
        elif fam == "branged":
            lines.append("r eax %08x" % UNIT)
            call = "call %08x %08x %08x %08x %08x %08x %08x %08x %08x %08x %08x" % (
                f, 0, 0, GAME, CTL, TARGET, inp["count"] & 0xFFFFFFFF, 0, 0, 0, 0)
        elif fam == "wpick":
            lines.append("r eax %08x" % UNIT)
            call = "call %08x %08x %08x %08x %08x" % (f, 0, 0, WTS, inp["n"])
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
        cases, meta, mem = gen_family(fam, random.Random("r52k-" + fam))
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


def stack_words(c, addr, n):
    stk = c["dumps"][STK_LO]
    return list(struct.unpack_from("<%dI" % n, stk, addr - STK_LO))


def matches(c, want, site_shift=0):
    fn, site, ecx, edx, args, seed, c14, c18, c1c, block, regs, eax, qbyte = want
    if c.get("obs") != fn:
        return False
    gseed = list(struct.unpack("<II", c["dumps"][UNIT + 0x20]))
    g14, g18, g1c = struct.unpack_from("<III", c["dumps"][CTL + 0x14], 0)
    ok = gseed == seed and g14 == c14 and g18 == c18 and g1c == c1c
    if qbyte is not None:
        addr, val = qbyte
        ok = ok and c["dumps"][QNODE][addr - QNODE] == val
    if fn == RET:
        if eax is not None:
            ok = ok and c["regs"]["eax"] == u32(eax)
        return ok and site_shift == 0
    a = c.get("args", b"")
    got = [struct.unpack_from("<I", a, 4 + 4 * k)[0] for k in range(len(args))]
    ret = struct.unpack_from("<I", a, 0)[0]
    ok = ok and ret == site + site_shift and got == args
    if ecx is not None:
        ok = ok and c["regs"]["ecx"] == u32(ecx)
    if edx is not None:
        ok = ok and c["regs"]["edx"] == u32(edx)
    for r, v in regs.items():
        ok = ok and c["regs"][r] == u32(v)
    if block is not None:
        addr, words = block
        got = stack_words(c, addr, len(words))
        ok = ok and all(w is None or g == u32(w) for g, w in zip(got, words))
    return ok


def check_family(fam, d):
    _, meta, _ = gen_family(fam, random.Random("r52k-" + fam))
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
            bad.append("case %d mismatch want=%s@%s obs=%s args=%s regs=%s" % (
                c["n"], want[0] if want[0] == RET else hex(want[0]), hex(want[1]),
                c.get("obs") if c.get("obs") == RET else hex(c.get("obs", 0)), c.get("args", b"")[:28].hex(),
                {k: hex(v) for k, v in c.get("regs", {}).items() if k in ("eax", "ebx", "ecx", "edx", "esi", "edi")}))
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
    line = ("AI52K %s cases=%d match=%d bad=%d stopped=%d traced=%d accounted=%d drew=%d " % (
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
    print("AI52K total cases=%d match=%d" % tuple(tot))
    print("AI52K result=%s" % ("ok" if allok else "FAIL"))


def cmd_manifest(d, write):
    rows = []
    for fam in FAMILIES:
        for ext in ("cases", "mem", "out", "err"):
            p = os.path.join(d, "%s.%s" % (fam, ext))
            if os.path.exists(p):
                rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.basename(p)))
    for extra in ("check.txt", "ai_cat_emu11.py.rev"):
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

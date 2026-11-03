#!/usr/bin/env python3
"""Plan 0052 phase 1.2, catalogue batch 5 (summons, `lane/r52f`): the think and init functions of AI rows 67, 84, 86,
101-112 and 143 (and state row 7, which shares row 67's think) run under Ghidra's p-code emulator (ADR-0015,
ADR-0021) with re/ghidra_scripts/EmuBoundary.java and compared with the models below. No game run, no slot. Same
method as tools/ai_cat_emu4.py (batch 4): one family per function, a function return is an outcome of its own (the
init functions), the `le`, `d0` and `cmp` controls and the site control, the EDGES line per family; `r4` is replaced
by `u16` (Skill1 read as an unsigned word, for the functions that bound it).

    python3 -I tools/ai_cat_emu5.py cases [--dir D]      write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/ai_cat_emu5.py check [--dir D]      compare every D/<family>.out with its model, account for
                                                         every traced access, run the negative and site controls
    python3 -I tools/ai_cat_emu5.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r52f/emu. Every case draw comes from random.Random("r52f-<family>"), so `cases` regenerates
identical files. The development run (emu/dev-1) used the writer before two tunings below (a Skills count of 0x10000
for `bwinit` and `blade`, where dev-1's `u16` control separated nothing in `blade`, and `hydra` seeds whose first draw
is 59, 60 or 61, where dev-1 met `draw<60` at equality twice); its copy, emu/dev-1/ai_cat_emu5.py.rev, checks it. The
models are the same in both runs.

Each family runs one function `(ECX game, EDX unit; ctx)` (ai/0006) on a declared image: the game's difficulty byte
(+0x6D) and frame (+0xA8); the unit's type (+0x00, 1), class (+0x04), mode (+0x10), monster data pointer (+0x14),
seed (+0x20/+0x24), path pointer (+0x2C), skill list head (+0xA8) and flag word (+0xC4); the monster data's AI
control pointer (+0x28); the AI control's state (+0x00), +0x14, +0x18, +0x1C and +0x20 (no parameter record); the
AiCtx (+0x00 ctl, +0x08 target, +0x14 distance, +0x18 melee, +0x1C MonStats record, +0x20 MonStats2 record; an init
function's block has the same layout); the MonStats record's aip block (+0x56..+0x85), Skill1..3 (+0x170..+0x175)
and Sk1..3mode (+0x180..+0x182); the DataTables pointer (0x00744304), its Skills count (+0xBA0) and Skills records
pointer (+0xB98), and the case's Skill1 record's Param2 (+0x14C). Every callee the function reaches is an observed
boundary. The claim per case: the first boundary reached (or the return), its call site (the return address), the
registers and stack arguments the callee takes, the unit seed and the AI control's +0x14/+0x18/+0x1C at the boundary.

Families (function, rows):
  bwinit   0x005E0390 row 84's init           bwall    0x005E0400 row 84 BoneWall
  necropet 0x005E4CF0 row 67, state row 7     hydra    0x005E9E60 row 86 Hydra
  sentinit 0x005EA290 rows 101, 104 init      asentry  0x005EA3D0 row 101 AssassinSentry
  bladeinit 0x005EA510 row 102's init         blade    0x005EA540 row 102 BladeCreeper
  inviso   0x005EA7A0 row 103 InvisoPet       dsentry  0x005EA980 row 104 DeathSentry
  swinit   0x005EAF50 row 105's init          swarrior 0x005EAFA0 row 105 ShadowWarrior
  sminit   0x005EB490 row 106's init          sm2init  0x005EB5C0 row 143's init
  smaster  0x005EB970 rows 106, 143           vinit    0x005EC6A0 rows 110, 111 init
  vines    0x005EC6C0 row 110 Vines           cycle    0x005EC8C0 row 111 CycleOfLife
  ravinit  0x005ECB70 row 107's init          raven    0x005ECC10 row 107 Raven
  dwolf    0x005ED710 row 108 DruidWolf       bear     0x005ED730 row 112 DruidBear
  totem    0x005ED9E0 row 109 Totem
The `entry` families (ENTRY below) reach their first callee before any test: their claim is that call's site and
arguments, and the AI-control words written before it.

Controls: `le` compares each draw with `<=` instead of `<`; `d0` reads every aip from the Normal column; `cmp`
switches the strictness of every compare that is not a draw (`<` and `<=`, `>` and `>=`); `u16` reads Skill1 as an
unsigned word; `site` expects each call site one byte later. Each must fail every case it separates. The `EDGES` line
under each family counts, per compare, the cases that meet it at equality (the only cases in which a strictness
control can separate that compare); a compare missing from it has no control in the run.

Not covered (ADR-0021): every callee at or after a boundary (the owner lookup, the commands, the move helpers, the
skill lookups, the event cancel) and so every branch that a boundary call's result decides. Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r52f", "emu")

MUL = 0x6AC690C5
GAME = 0x12000000
UNIT = 0x12100000
UPATH = 0x12200000
TARGET = 0x12400000
MDATA = 0x12500000
MREC = 0x12600000
CTX = 0x12700000
CTL = 0x12800000
MS2 = 0x12900000
DTBL = 0x12A00000
SKREC = 0x13000000
SKSIZE = 0x23C
G_DATATABLES = 0x00744304
STK_LO = 0x7FEFFC00
STK_LEN = 1040              # to 0x7FF00010: the frame, the return address and the ctx argument slot
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)

SETMODE, IDLE, USESKILL, OWNER, CANCEL, GETUNITSKILL, SKLEVEL, SETMODEAT, DELAY, FINDUNIT = (
    0x005DDFC0, 0x005DE080, 0x005DEAD0, 0x0058F0D0, 0x00540E60, 0x006439F0, 0x006442A0, 0x005DDF90, 0x005DE0F0,
    0x00552F60)
OTHER = (0x005DD2B0, 0x00620BB0, 0x0061AB00, 0x006416D0, 0x005E3EA0, 0x005E45D0, 0x005DDC30, 0x005DD7F0, 0x005DC380,
         0x005DDE50, 0x00621F20, 0x005B0BD0, 0x00639DF0, 0x006439B0, 0x005DE190, 0x005DEC80, 0x005DEFE0, 0x00554EA0,
         0x0045ADF0, 0x0045AE20, 0x006488C0, 0x00648900, 0x0057CCB0, 0x004EFCB0, 0x00646CA0, 0x0056EDE0, 0x0058EE80,
         0x005541B0, 0x00554200, 0x00622AA0, 0x00622C40, 0x005A7C20, 0x005A7E60, 0x00649070)
OBSERVE = tuple(sorted(set((SETMODE, IDLE, USESKILL, OWNER, CANCEL, GETUNITSKILL, SKLEVEL, SETMODEAT, DELAY,
                            FINDUNIT) + OTHER)))
RET = "ret"

FNS = {"bwinit": 0x005E0390, "bwall": 0x005E0400, "necropet": 0x005E4CF0, "hydra": 0x005E9E60,
       "sentinit": 0x005EA290, "asentry": 0x005EA3D0, "bladeinit": 0x005EA510, "blade": 0x005EA540,
       "inviso": 0x005EA7A0, "dsentry": 0x005EA980, "swinit": 0x005EAF50, "swarrior": 0x005EAFA0,
       "sminit": 0x005EB490, "sm2init": 0x005EB5C0, "smaster": 0x005EB970, "vinit": 0x005EC6A0,
       "vines": 0x005EC6C0, "cycle": 0x005EC8C0, "ravinit": 0x005ECB70, "raven": 0x005ECC10, "dwolf": 0x005ED710,
       "bear": 0x005ED730, "totem": 0x005ED9E0}
FAMILIES = tuple(FNS)
ENTRY = ("necropet", "asentry", "inviso", "dsentry", "swinit", "swarrior", "sminit", "sm2init", "vines", "cycle",
         "raven", "bear", "totem")
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
    """One case's inputs and the model's running state (the unit seed, the AI control's +0x14/+0x18/+0x1C)."""

    def __init__(self, inp, neg=None):
        self.i, self.neg = inp, neg
        self.seed = list(inp["seed"])
        self.c14, self.c18, self.c1c = inp["ctl14"], inp["ctl18"], inp["ctl1c"]
        self.eq = set()                     # the compares this case met at equality (the cases a control can separate)

    def aip(self, k):
        d = 0 if self.neg == "d0" else self.i["diff"]
        return self.i["aip"][k - 1][d]

    def draw(self):
        step(self.seed)
        return self.seed[0] % 100

    def chance_c(self, c, edge):            # draw < constant (le: <=)
        d = self.draw()
        if d == c:
            self.eq.add(edge)
        return d <= c if self.neg == "le" else d < c

    def lt(self, a, b, edge):               # a non-draw a < b (cmp: <=)
        if a == b:
            self.eq.add(edge)
        return a <= b if self.neg == "cmp" else a < b

    def le(self, a, b, edge):               # a non-draw a <= b (cmp: <)
        if a == b:
            self.eq.add(edge)
        return a < b if self.neg == "cmp" else a <= b

    def skill1(self):                       # MonStats Skill1, s16 (u16: unsigned)
        v = self.i["skill"][0] & 0xFFFF
        return v if self.neg == "u16" else s16(v)

    def hit(self, fn, site, args, ecx=GAME, edx=UNIT):
        raise Hit((fn, site, ecx, edx, [u32(a) for a in args], list(self.seed), u32(self.c14), u32(self.c18),
                   u32(self.c1c)))

    def ret(self):
        self.hit(RET, 0, [], ecx=None, edx=None)


def owner_at(site):                         # MonsterOwner(ECX unit), no stack argument
    def m(e):
        e.hit(OWNER, site, [], ecx=UNIT, edx=None)
    return m


def m_bwinit(e):                                        # row 84's init, 0x005E0390
    i = e.i
    s = e.skill1()
    if e.le(s, 0, "s<=0"):                              # test ax,ax; jle (s16)
        return e.ret()
    if s < 0 or not e.lt(s, i["skcount"], "s<count") or i["recnull"]:
        e.c14 = i["frame"]
        return e.ret()
    e.c14 = i["frame"] + i["param2"]
    e.ret()


def m_bwall(e):                                         # row 84, 0x005E0400
    if e.lt(s32(e.c14), s32(e.i["frame"]), "v14<T"):
        e.hit(SETMODE, 0x005E041E, [0, 0, 0])
    e.hit(IDLE, 0x005E0429, [15])


def m_necropet(e):                                      # row 67 and state row 7, 0x005E4CF0
    e.hit(CANCEL, 0x005E4D02, [2, 0])


def m_hydra(e):                                         # row 86, 0x005E9E60
    i = e.i
    if e.lt(s32(e.c14), s32(i["frame"]), "v14<T"):
        e.hit(SETMODE, 0x005E9E8A, [0, 0, 0])
    if i["target"] and e.lt(i["dist"], 25, "dist<25") and e.chance_c(60, "draw<60"):
        e.hit(USESKILL, 0x005E9EF6, [i["skmode"][0], s16(i["skill"][0]), i["target"], 0, 0])
    e.hit(IDLE, 0x005E9F06, [10])


def m_sentinit(e):                                      # rows 101 and 104 init, 0x005EA290
    e.c14 = e.i["frame"]
    e.c18 = 0xFFFFFFFF
    e.ret()


def m_bladeinit(e):                                     # row 102's init, 0x005EA510
    e.c14, e.c18, e.c1c = 0xFFFFFFFF, 1, 0
    e.ret()


def m_blade(e):                                         # row 102, 0x005EA540
    s = e.skill1()
    if s < 0 or not e.lt(s, e.i["skcount"], "s<count") or e.i["recnull"]:
        e.hit(SETMODE, 0x005EA594, [0, 0, 0])
    e.hit(GETUNITSKILL, 0x005EA5A6, [], ecx=UNIT, edx=s)


def m_swinit(e):                                        # row 105's init, 0x005EAF50
    e.c1c = 1
    e.hit(OWNER, 0x005EAF69, [], ecx=UNIT, edx=None)


def m_swarrior(e):                                      # row 105, 0x005EAFA0
    e.hit(CANCEL, 0x005EAFD4, [2, 0])


def m_sminit(e):                                        # row 106's init, 0x005EB490
    e.c14, e.c18, e.c1c = 0, 0, 1
    e.hit(OWNER, 0x005EB4B9, [], ecx=UNIT, edx=None)


def m_sm2init(e):                                       # row 143's init, 0x005EB5C0
    e.c1c = 1
    e.hit(OWNER, 0x005EB5DB, [], ecx=UNIT, edx=None)


def m_smaster(e):                                       # rows 106 and 143, 0x005EB970
    if e.i["sklist"] == 0:
        e.hit(IDLE, 0x005EB9BD, [100])
    e.hit(OWNER, 0x005EB9CD, [], ecx=UNIT, edx=None)


def m_vinit(e):                                         # rows 110 and 111 init, 0x005EC6A0
    e.c14 = 0
    e.ret()


def m_ravinit(e):                                       # row 107's init, 0x005ECB70
    e.c14 = 0xFFFFFFFF
    e.c18 = u32(e.aip(3) + 1)
    step(e.seed)
    e.c1c = e.seed[0] & 1
    e.ret()


def m_dwolf(e):                                         # row 108, 0x005ED710: jmp to the wolf or the fenris think
    if e.i["cls"] == 0x1A4:
        e.hit(OWNER, 0x005ECF02, [], ecx=UNIT, edx=None)
    e.hit(OWNER, 0x005ED2C2, [], ecx=UNIT, edx=None)


MODELS = {"bwinit": m_bwinit, "bwall": m_bwall, "necropet": m_necropet, "hydra": m_hydra, "sentinit": m_sentinit,
          "asentry": owner_at(0x005EA2C6), "bladeinit": m_bladeinit, "blade": m_blade,
          "inviso": owner_at(0x005EA7C5), "dsentry": owner_at(0x005EA2C6), "swinit": m_swinit,
          "swarrior": m_swarrior, "sminit": m_sminit, "sm2init": m_sm2init, "smaster": m_smaster, "vinit": m_vinit,
          "vines": owner_at(0x005EC6E2), "cycle": owner_at(0x005EC8E2), "ravinit": m_ravinit,
          "raven": owner_at(0x005ECC2C), "dwolf": m_dwolf, "bear": owner_at(0x005ED74C),
          "totem": owner_at(0x005ED9F4)}
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
        ds = first_draws(seed, 2)
        aip = []
        for _ in range(8):
            col = []
            for _ in range(3):
                col.append(rnd.choice(ds + [rnd.randrange(0, 101), rnd.randrange(-3, 111), 0, 1, 5, 10, 35,
                                            -1, 0x7FFF, -0x8000]))
            aip.append(col)
        diff = k % 3
        frame = rnd.randrange(100, 100000)
        sk1 = rnd.choice([-1, 0, 1, rnd.randrange(0, 400), rnd.randrange(0, 400), 0x7FFF, 0x8000, 0xFFFE])
        inp = {
            "fam": fam, "seed": seed, "diff": diff, "aip": aip, "frame": frame,
            "melee": rnd.randrange(2),
            "dist": rnd.choice([0, 1, 10, 24, 25, 26, rnd.randrange(0, 60)]),
            "ctl14": rnd.choice([0, 0, 1, -1, u32(frame + rnd.choice((-1, 0, 1, -50, 50))),
                                 rnd.randrange(1 << 32)]),
            "ctl18": rnd.choice([0, 0, 1, 2, 7, -1]), "ctl1c": rnd.choice([0, 0, 1, 2, -1]),
            "skill": [sk1, rnd.choice([-1, rnd.randrange(0, 400)]), rnd.choice([-1, rnd.randrange(0, 400)])],
            "skmode": [rnd.randrange(16) for _ in range(3)],
            "state": rnd.randrange(18),
            "cls": rnd.choice([0x1A3, 0x1A4, 0x1A4, 0x1A5, rnd.randrange(0x2E0)]),
            "sklist": rnd.choice([0, 0x12F00000]),
            "param2": rnd.choice([0, 1, 20, rnd.randrange(-50, 2000)]),
            "recnull": 0,
        }
        s = s16(sk1)
        inp["skcount"] = rnd.choice([357, max(0, s + rnd.choice((-1, 0, 1)))]) if s > 0 else 357
        if fam in ("bwinit", "blade") and s >= 0 and rnd.randrange(8) == 0:
            inp["recnull"] = 1                   # a records pointer that puts the case's record at address 0
            inp["skcount"] = max(inp["skcount"], s + 1)
        if fam in ("bwinit", "blade") and s16(sk1) < 0 and rnd.randrange(2):
            inp["skcount"] = 0x10000             # a count above 0x8000, where a sign-extended and an unsigned Skill1 differ
        if fam in ("bwall", "hydra"):
            inp["ctl14"] = u32(frame + rnd.choice((-1, 0, 1, -1000, 1000)))
        if fam == "hydra" and rnd.randrange(3) == 0:
            while first_draws(seed, 1)[0] not in (59, 60, 61):    # a first draw at the 60 threshold (dev-1: 2 cases)
                seed = (rnd.randrange(1 << 32), rnd.randrange(1 << 32))
            inp["seed"] = seed
            inp["ctl14"] = u32(frame + rnd.choice((0, 1, 1000)))
            inp["dist"] = rnd.choice((0, 10, 24))
        if fam == "hydra" and rnd.randrange(5) == 0:
            inp["target"] = 0
        else:
            inp["target"] = TARGET
        skrec = u32(-SKSIZE * s) if inp["recnull"] else SKREC
        sk = "".join(hx16(v) for v in inp["skill"])
        lines = [
            "w %08x %s" % (GAME + 0x6D, "%02x" % diff),
            "w %08x %s" % (GAME + 0xA8, hx32(frame)),
            "w %08x %s" % (UNIT, hx32(1) + hx32(inp["cls"])),
            "w %08x %s" % (UNIT + 0x10, hx32(1) + hx32(MDATA)),
            "w %08x %s%s" % (UNIT + 0x20, hx32(seed[0]), hx32(seed[1])),
            "w %08x %s" % (UNIT + 0x2C, hx32(UPATH)),
            "w %08x %s" % (UNIT + 0xA8, hx32(inp["sklist"])),
            "w %08x %s" % (UNIT + 0xC4, hx32(0)),
            "w %08x %s" % (MDATA + 0x28, hx32(CTL)),
            "w %08x %s" % (CTL, hx32(inp["state"])),
            "w %08x %s%s%s%s" % (CTL + 0x14, hx32(inp["ctl14"]), hx32(inp["ctl18"]), hx32(inp["ctl1c"]), hx32(0)),
            "w %08x %s" % (CTX, hx32(CTL) + hx32(0) + hx32(inp["target"]) + hx32(0) + hx32(0)
                           + hx32(inp["dist"]) + hx32(inp["melee"]) + hx32(MREC) + hx32(MS2)),
            "w %08x %s" % (MREC + 0x56, "".join(hx16(aip[j][d]) for j in range(8) for d in range(3))),
            "w %08x %s" % (MREC + 0x170, sk + hx16(-1) + "00" * 8),
            "w %08x %s" % (MREC + 0x180, "".join("%02x" % m for m in inp["skmode"]) + "00" * 5),
            "w %08x %s" % (G_DATATABLES, hx32(DTBL)),
            "w %08x %s" % (DTBL + 0xB98, hx32(skrec)),
            "w %08x %s" % (DTBL + 0xBA0, hx32(inp["skcount"])),
        ]
        if not inp["recnull"] and 0 <= s:
            lines.append("w %08x %s" % (SKREC + SKSIZE * s + 0x14C, hx32(inp["param2"])))
        lines += [
            "d %08x %d" % (STK_LO, STK_LEN), "d %08x 8" % (UNIT + 0x20), "d %08x 12" % (CTL + 0x14),
            "call %08x %08x %08x %08x" % (FNS[fam], GAME, UNIT, CTX),
        ]
        cases.append(lines)
        meta.append(inp)
    mem = ["observe %08x" % a for a in OBSERVE] + ["guard %08x" % a for a in FATAL + ALLOC]
    return cases, meta, mem


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        cases, meta, mem = gen_family(fam, random.Random("r52f-" + fam))
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


def matches(c, want, site_shift=0):
    fn, site, ecx, edx, args, seed, c14, c18, c1c = want
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
    return ok


def check_family(fam, d):
    _, meta, _ = gen_family(fam, random.Random("r52f-" + fam))
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
    line = ("AI52F %s cases=%d match=%d bad=%d stopped=%d traced=%d drew=%d " % (
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
    print("AI52F total cases=%d match=%d" % tuple(tot))
    print("AI52F result=%s" % ("ok" if allok else "FAIL"))


def cmd_manifest(d, write):
    rows = []
    for fam in FAMILIES:
        for ext in ("cases", "mem", "out", "err"):
            p = os.path.join(d, "%s.%s" % (fam, ext))
            if os.path.exists(p):
                rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.basename(p)))
    for extra in ("check.txt", "ai_cat_emu5.py.rev"):
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

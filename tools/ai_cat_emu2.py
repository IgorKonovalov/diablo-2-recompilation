#!/usr/bin/env python3
"""Plan 0052 phase 1.2, catalogue batch 2 (pool-B, `lane/r52c`): ten think functions of AI rows 17-30 run under
Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java and compared with the models
below. No game run, no slot. Same method as tools/ai_cat_emu.py (batch 1), with the AI-control words +0x14/+0x18
compared at every boundary and the unit-search block compared where the boundary is the search.

    python3 -I tools/ai_cat_emu2.py cases [--dir D]      write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/ai_cat_emu2.py check [--dir D]      compare every D/<family>.out with its model, account for
                                                         every traced access, run the negative and site controls
    python3 -I tools/ai_cat_emu2.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r52c/emu. The development run (emu/dev-1) used the writer before the thorn hulk and scarab
tuning below (its copy, emu/dev-1/ai_cat_emu2.py.rev, checks it); the models are the same. Every case draw comes from
random.Random("r52c-<family>"), so `cases` regenerates identical files.

Each family runs one think function `(ECX game, EDX unit; ctx)` (ai/0003) on a declared image: the game's difficulty
byte (+0x6D) and frame (+0xA8); the unit's type (+0x00), class (+0x04), mode (+0x10), monster data pointer (+0x14) and
seed (+0x20/+0x24); the monster data's AI control pointer (+0x28) and +0x54 word; the AI control's state (+0x00),
+0x14, +0x18, +0x1C, +0x20 (the parameter-list head) and the owner link +0x28/+0x2C/+0x30; one parameter record; the
AiCtx (+0x00 ctl, +0x08 target, +0x14 distance, +0x18 melee, +0x1C MonStats record); the MonStats record's aip block
(+0x56..+0x85), Skill1..3 (+0x170..+0x175) and Sk1..3mode (+0x180..+0x182); the DataTables pointer (0x00744304) and
its MonStats count (+0xA80). Every callee the function reaches is an observed boundary, except RNG_Range (0x0045C390),
sub_005DD2B0_AiMonState3or19 with its callee 0x005734E0, sub_0058EE80_AiParamsHead and sub_0058F0D0_MonsterOwner
(whose own call, GameFindUnit, is observed), which run on the declared image. The claim per case: the first boundary
reached, its call site (the return address), the registers and stack arguments the callee takes, the unit seed, the
AI control's +0x14 and +0x18 at the boundary, and at an AiUnitSearch boundary the search block the pointer argument
addresses (its address and the words the function writes before the call).

Families (function, row):
  leaper    0x005F20A0 row 17 SandLeaper     panther   0x005F22B0 row 18 PantherWoman
  swarm     0x005F2460 row 19 Swarm          scarab    0x005F2540 row 20 Scarab
  mummy     0x005F2850 row 21 Mummy          gmummy    0x005F2B10 row 22 GreaterMummy
  mosquito  0x005F3730 row 24 Mosquito       thornhulk 0x005F4850 row 27 ThornHulk
  fetish    0x005F53E0 row 30 Fetish         batalt    0x005F4FD0 row 29 BatDemon's alt

Controls: `le` compares each draw with `<=` instead of `<` (and `>` with `>=`); `d0` reads every aip from the Normal
column; `site` expects each call site one byte later. Each must fail every case it separates.

Not covered (ADR-0021): every callee at or after a boundary (the commands, the move helpers, the override setter, the
unit search and its callbacks, the life percent, the hostile search, the skill target test, A2Q1_BossSeen) and so
every branch that a boundary call's result decides (the scarab's walk result, the panther's and greater mummy's search
results, the thorn hulk's delay, the fetish's life test). Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r52c", "emu")

MUL = 0x6AC690C5
GAME = 0x12000000
UNIT = 0x12100000
TARGET = 0x12300000
MDATA = 0x12500000
MREC = 0x12600000
CTX = 0x12700000
CTL = 0x12800000
REC = 0x12900000
DTBL = 0x12A00000
G_DATATABLES = 0x00744304
STK_LO = 0x7FEFFC00
EBP = 0x7FEFFFFC            # the think function's frame pointer (entry ESP 0x7FF00000, `push ebp; mov ebp,esp`)
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)

SETMODE, IDLE, WALK, PATHOVR, WALK13, RING, T56, STEPAWAY, WALKSTOP, DELAY = (
    0x005DDF90, 0x005DE080, 0x005DEC80, 0x005DE190, 0x005DED40, 0x005DE200, 0x005DF7D0, 0x005DEFE0, 0x005DEF80,
    0x005DE0F0)
FINDHOSTILE, UNITLIFE, SKILLOK, USESKILL, USESEQ, FINDUNIT, PARAMSPOP, PARAMSPUSH, HELPBLOCK, SEARCH = (
    0x005DDC30, 0x00621F20, 0x005FD470, 0x005DEAD0, 0x005DE000, 0x00552F60, 0x0058ED10, 0x0058EF40, 0x0058F730,
    0x005DD0B0)
WANDERNEAR, BOSSSEEN, SETPATHTGT, EVFIRST, AIINIT, AILIFE, TOWARD, RUN, GETROOM, DISTSQ = (
    0x005DF530, 0x00599420, 0x00620C10, 0x005415A0, 0x005B0E00, 0x005DD280, 0x005DE6D0, 0x005DED20, 0x00620BB0,
    0x005B0BD0)
OBSERVE = (SETMODE, IDLE, WALK, PATHOVR, WALK13, RING, T56, STEPAWAY, WALKSTOP, DELAY, FINDHOSTILE, UNITLIFE, SKILLOK,
           USESKILL, USESEQ, FINDUNIT, PARAMSPOP, PARAMSPUSH, HELPBLOCK, SEARCH, WANDERNEAR, BOSSSEEN, SETPATHTGT,
           EVFIRST, AIINIT, AILIFE, TOWARD, RUN, GETROOM, DISTSQ, 0x005DEFB0, 0x00639DB0, 0x0063A770)

FNS = {"leaper": 0x005F20A0, "panther": 0x005F22B0, "swarm": 0x005F2460, "scarab": 0x005F2540, "mummy": 0x005F2850,
       "gmummy": 0x005F2B10, "mosquito": 0x005F3730, "thornhulk": 0x005F4850, "fetish": 0x005F53E0,
       "batalt": 0x005F4FD0}
FAMILIES = tuple(FNS)
NCASES = 240


def u32(v):
    return v & 0xFFFFFFFF


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
    """One case's inputs and the model's running state (the unit seed, the AI control's +0x14/+0x18)."""

    def __init__(self, inp, neg=None):
        self.i, self.neg = inp, neg
        self.seed = list(inp["seed"])
        self.ctl14 = inp["ctl14"]
        self.ctl18 = inp["ctl18"]

    def aip(self, k):
        d = 0 if self.neg == "d0" else self.i["diff"]
        return self.i["aip"][k - 1][d]

    def draw(self):
        step(self.seed)
        return self.seed[0] % 100

    def lt(self, a, b):
        return a <= b if self.neg == "le" else a < b

    def gt(self, a, b):
        return a >= b if self.neg == "le" else a > b

    def chance(self, k):
        return self.lt(self.draw(), self.aip(k))

    def st(self):
        return self.i["m54"] in (3, 19)

    def hit(self, fn, site, args, ecx=GAME, edx=UNIT, block=None):
        raise Hit((fn, site, ecx, edx, [u32(a) for a in args], list(self.seed), u32(self.ctl14), u32(self.ctl18),
                   block))


def m_leaper(e):
    i, t, dist = e.i, e.i["target"], e.i["dist"]
    if i["skill1"] >= 0 and dist < 5 and e.chance(1):
        e.hit(SKILLOK, 0x005F2134, [i["skill1"], t, 0, 0])
    if not i["melee"]:
        if dist > 10:
            e.hit(PATHOVR, 0x005F21D6, [75, 0], ecx=UNIT, edx=0)
        if e.chance(3):
            e.hit(WALK, 0x005F223F, [t, 7])
        if e.chance(4):
            e.hit(T56, 0x005F2293, [t, 4, 0])
    elif e.chance(2):
        e.hit(SETMODE, 0x005F21BB, [5, t])
    e.hit(IDLE, 0x005F22A3, [10])


def m_panther(e):
    t = e.i["target"]
    if e.i["melee"]:
        if e.chance(2):
            e.hit(SETMODE, 0x005F231C, [4, t])
        e.hit(IDLE, 0x005F2332, [e.aip(4)])
    if e.chance(1):
        e.hit(PATHOVR, 0x005F237D, [75, 0], ecx=UNIT, edx=0)
    blk = EBP - 0x2C
    e.hit(SEARCH, 0x005F23B3, [blk, 0x005B0D00, 1], block=(blk, [0, 0x7FFFFFFF]))


def m_swarm(e):
    t = e.i["target"]
    if not e.i["melee"]:
        if e.chance(1):
            e.hit(WALK, 0x005F2512, [t, 7])
    elif e.chance(3):
        e.hit(SETMODE, 0x005F24C7, [4, t])
    e.hit(IDLE, 0x005F2528, [e.aip(2)])


def m_scarab(e):
    i, t, dist = e.i, e.i["target"], e.i["dist"]
    kind = i["rec_kind"] if i["head"] else None
    if kind is None and dist < 20:
        if i["own28"]:                                       # MonsterOwner on the image reaches GameFindUnit
            e.hit(FINDUNIT, 0x0058F0FF, [i["own2c"]], ecx=i["own28"], edx=i["own30"])
        # owner 0 is never the unit: on to the decision below
    if kind == 1:
        if i["melee"] and i["skill1"] >= 0:
            e.hit(PARAMSPOP, 0x005F2618, [])
        e.hit(PATHOVR, 0x005F2652, [100, 0], ecx=UNIT, edx=2)
    if not i["melee"]:
        if e.ctl14 != 0:
            e.hit(PATHOVR, 0x005F2803, [0, 4], ecx=UNIT, edx=2)
        e.hit(T56, 0x005F27E3, [t, 0, 0])
    if not e.chance(1):
        e.hit(IDLE, 0x005F27C0, [e.aip(3)])
    if i["skill1"] >= 0 and e.chance(4):
        e.hit(USESKILL, 0x005F2737, [i["sk1mode"], i["skill1"], t, 0, 0])
    if not e.chance(2):
        e.hit(SETMODE, 0x005F27A4, [5, t])
    e.hit(SETMODE, 0x005F278E, [4, t])


def m_mummy(e):
    t, dist = e.i["target"], e.i["dist"]
    if e.st() and not e.i["melee"]:
        e.hit(WALK, 0x005F2895, [t, 7])
    if dist <= e.aip(1):
        if e.i["melee"]:
            if e.chance(3):
                if e.chance(4):
                    e.hit(SETMODE, 0x005F29A8, [4, t])
                e.hit(SETMODE, 0x005F29C0, [5, t])
            e.hit(IDLE, 0x005F29DC, [e.aip(5)])
        e.hit(WALK, 0x005F29EB, [t, 7])
    if e.chance(2):
        e.hit(RING, 0x005F28F4, [3])
    e.hit(IDLE, 0x005F2908, [e.aip(5)])


def m_gmummy(e):
    i, t, dist = e.i, e.i["target"], e.i["dist"]
    if i["melee"] and e.chance(1):
        e.hit(SETMODE, 0x005F2B84, [4, t])
    if dist < 5 and e.chance(1):
        e.hit(SETMODE, 0x005F2BE3, [5, t])
    radament = 0xE5 if i["mscount"] > 0xE5 else 0xFFFFFFFF
    if u32(i["cls"]) == radament:
        e.hit(BOSSSEEN, 0x005F2C4C, [])
    a5 = e.aip(5)
    blk = EBP - 0x40
    e.hit(SEARCH, 0x005F2C85, [blk, 0x005F2A00, 1], block=(blk, [0, 0, 0, 0, a5 * a5, 0, 0]))


def m_mosquito(e):
    i, t = e.i, e.i["target"]
    if i["melee"]:
        if e.chance(3) or e.ctl18 == 0:
            e.ctl18 += 1
            if i["skill1"] >= 0 and e.chance(4):
                e.hit(USESKILL, 0x005F389B, [i["sk1mode"], i["skill1"], t, 0, 0])
            e.hit(SETMODE, 0x005F38B3, [4, t])
        if e.gt(e.draw(), 20):
            e.hit(IDLE, 0x005F37EB, [15])
        e.ctl14, e.ctl18 = 2, 0
    if e.ctl14 == 0:
        e.hit(PATHOVR, 0x005F381C, [100, 0], ecx=UNIT, edx=13)
    if e.ctl14 == 1:
        e.hit(PATHOVR, 0x005F38CD, [50, 0], ecx=UNIT, edx=0)
    if e.ctl14 == 2:
        e.hit(PATHOVR, 0x005F3911, [100, 0], ecx=UNIT, edx=2)
    e.ctl14, e.ctl18 = 0, 0
    e.hit(IDLE, 0x005F394A, [10])


def m_thornhulk(e):
    i, t = e.i, e.i["target"]
    if not i["melee"]:
        e.ctl14 = 0
        e.hit(WALK13, 0x005F4A58, [t, 7])
    if e.ctl14 < 1:
        if not e.chance(1):
            if not e.chance(3):
                e.hit(IDLE, 0x005F4A3C, [15])
            e.hit(T56, 0x005F4A2A, [t, 4, 0])
        if e.ctl18 < 1 and e.chance(4):
            e.hit(USESKILL, 0x005F496C, [5, i["skill1"], t, 0, 0])
        e.ctl18 -= 1
        if not e.chance(2):
            e.hit(SETMODE, 0x005F49F6, [4, t])
        e.hit(SETMODE, 0x005F49E0, [5, t])
    e.hit(USESKILL, 0x005F489E, [5, i["skill1"], t, 0, 0])


def m_fetish(e):
    i = e.i
    if i["head"]:
        if i["rec_kind"] == 1:
            e.hit(FINDUNIT, 0x005F5430, [i["rec_0c"]], ecx=GAME, edx=i["rec_10"])
        if i["rec_kind"] == 14:
            e.hit(FINDUNIT, 0x005F5484, [i["rec_0c"]], ecx=GAME, edx=i["rec_10"])
        e.hit(PARAMSPOP, 0x005F54AE, [])
    e.hit(UNITLIFE, 0x005F54B7, [i["target"]], ecx=None, edx=None)


def m_batalt(e):
    i = e.i
    if i["umode"] == 11:
        e.ctl14 = 1
        e.hit(DELAY, 0x005F4FF6, [1])
    if e.ctl14 == 4:
        e.ctl14 = 1
        e.hit(SETMODE, 0x005F5012, [10, 0])
    e.hit(AIINIT, 0x005F5023, [CTL, i["state"]], ecx=GAME, edx=None)


MODELS = {"leaper": m_leaper, "panther": m_panther, "swarm": m_swarm, "scarab": m_scarab, "mummy": m_mummy,
          "gmummy": m_gmummy, "mosquito": m_mosquito, "thornhulk": m_thornhulk, "fetish": m_fetish,
          "batalt": m_batalt}


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
        ds = first_draws(seed, 5)
        aip = []
        for _ in range(8):
            col = []
            for _ in range(3):
                col.append(rnd.choice(ds + ds + [rnd.randrange(0, 101), rnd.randrange(-3, 111), 0, 1, 2, 3, 50]))
            aip.append(col)
        inp = {
            "fam": fam, "seed": seed, "diff": k % 3, "aip": aip,
            "melee": rnd.randrange(2),
            "dist": rnd.choice([0, 1, 4, 5, 6, 10, 11, 12, 19, 20, 21, 25, 40, rnd.randrange(0, 60)]
                               + [a for a in aip[0]]),
            "m54": rnd.choice([0, 3, 19, 7, 2]),
            "ctl14": rnd.choice([0, 0, 1, 1, 2, 3, 4, -1]), "ctl18": rnd.choice([0, 0, 1, 2, 3, -1]),
            "frame": rnd.randrange(100, 100000), "head": rnd.randrange(3) == 0,
            "rec_kind": rnd.choice([1, 1, 14, 14, 0, 5]), "rec_0c": rnd.randrange(1 << 32),
            "rec_10": rnd.randrange(1 << 32),
            "own28": rnd.choice([0, 0, GAME]), "own2c": rnd.randrange(1 << 32), "own30": rnd.randrange(6),
            "skill1": rnd.choice([-1, rnd.randrange(0, 400), rnd.randrange(0, 400)]),
            "sk1mode": rnd.randrange(16), "cls": rnd.choice([0xE5, 0xE5, 0xE4, 0xE6, 0x65, 0xFFFFFFFF]),
            "mscount": rnd.choice([0x2E0, 0x2E0, 0x2E0, 0xE5, 0xE6]), "umode": rnd.choice([1, 2, 11, 11, 12]),
            "state": rnd.randrange(18),
        }
        if fam == "thornhulk":                 # reach the in-melee branches more often (the dev-1 writer had none)
            inp["melee"] = int(rnd.randrange(4) != 0)
            inp["ctl14"] = rnd.choice([0, 0, -1, 1, 2])
            inp["ctl18"] = rnd.choice([0, 0, -1, 1, 3])
        if fam == "scarab":                    # more melee cases with Skill1 set (dev-1 had 13 reaching the skill draw)
            inp["skill1"] = rnd.choice([-1, rnd.randrange(0, 400), rnd.randrange(0, 400), rnd.randrange(0, 400)])
            inp["melee"] = int(rnd.randrange(3) != 0)
        if fam == "mummy":
            inp["dist"] = rnd.choice([inp["dist"], aip[0][inp["diff"]], aip[0][inp["diff"]] + 1])
        inp["target"] = rnd.randrange(1, 1 << 31) & ~3
        rk = inp["rec_kind"]
        lines = [
            "w %08x %s" % (GAME + 0x6D, "%02x" % inp["diff"]),
            "w %08x %s" % (GAME + 0xA8, hx32(inp["frame"])),
            "w %08x %s" % (UNIT, hx32(1) + hx32(inp["cls"])),
            "w %08x %s" % (UNIT + 0x10, hx32(inp["umode"]) + hx32(MDATA)),
            "w %08x %s%s" % (UNIT + 0x20, hx32(seed[0]), hx32(seed[1])),
            "w %08x %s" % (MDATA + 0x28, hx32(CTL)), "w %08x %s" % (MDATA + 0x54, hx32(inp["m54"])),
            "w %08x %s" % (CTL, hx32(inp["state"])),
            "w %08x %s%s%s" % (CTL + 0x14, hx32(inp["ctl14"]), hx32(inp["ctl18"]), hx32(inp["frame"] + 7)),
            "w %08x %s" % (CTL + 0x20, hx32(REC if inp["head"] else 0)),
            "w %08x %s%s%s" % (CTL + 0x28, hx32(inp["own28"]), hx32(inp["own2c"]), hx32(inp["own30"])),
            "w %08x %s%s%s%s" % (REC + 0x08, hx32(rk), hx32(inp["rec_0c"]), hx32(inp["rec_10"]), hx32(0)),
            "w %08x %s" % (CTX, hx32(CTL) + hx32(0) + hx32(inp["target"]) + hx32(0) + hx32(0)
                           + hx32(inp["dist"]) + hx32(inp["melee"]) + hx32(MREC) + hx32(0)),
            "w %08x %s" % (MREC + 0x56, "".join(hx16(aip[j][d]) for j in range(8) for d in range(3))),
            "w %08x %s" % (MREC + 0x170, hx16(inp["skill1"]) + hx16(-1) + hx16(-1) + "00" * 10),
            "w %08x %s" % (MREC + 0x180, "%02x" % inp["sk1mode"] + "00" * 7),
            "w %08x %s" % (G_DATATABLES, hx32(DTBL)),
            "w %08x %s" % (DTBL + 0xA80, hx32(inp["mscount"])),
            "d %08x 1024" % STK_LO, "d %08x 8" % (UNIT + 0x20), "d %08x 8" % (CTL + 0x14),
            "call %08x %08x %08x %08x" % (FNS[fam], GAME, UNIT, CTX),
        ]
        cases.append(lines)
        meta.append(inp)
    mem = ["observe %08x" % a for a in OBSERVE] + ["guard %08x" % a for a in FATAL + ALLOC]
    return cases, meta, mem


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        cases, meta, mem = gen_family(fam, random.Random("r52c-" + fam))
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
    off = addr - STK_LO
    return list(struct.unpack_from("<%dI" % n, stk, off))


def matches(c, want, site_shift=0):
    fn, site, ecx, edx, args, seed, c14, c18, block = want
    if c.get("obs") != fn:
        return False
    a = c.get("args", b"")
    got = [struct.unpack_from("<I", a, 4 + 4 * k)[0] for k in range(len(args))]
    ret = struct.unpack_from("<I", a, 0)[0]
    gseed = list(struct.unpack("<II", c["dumps"][UNIT + 0x20]))
    g14, g18 = struct.unpack("<II", c["dumps"][CTL + 0x14])
    ok = ret == site + site_shift and got == args and gseed == seed and g14 == c14 and g18 == c18
    if ecx is not None:
        ok = ok and c["regs"]["ecx"] == u32(ecx)
    if edx is not None:
        ok = ok and c["regs"]["edx"] == u32(edx)
    if block is not None:
        addr, words = block
        ok = ok and stack_words(c, addr, len(words)) == [u32(w) for w in words]
    return ok


def check_family(fam, d):
    _, meta, _ = gen_family(fam, random.Random("r52c-" + fam))
    calls, traced = read_out(os.path.join(d, fam + ".out"))
    bad, match, stops = [], 0, 0
    ctl = {n: [0, 0] for n in ("le", "d0")}
    site_pass = 0
    bounds = {}
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
            bad.append("case %d mismatch want=%s@%s obs=%s" % (c["n"], hex(want[0]), hex(want[1]),
                                                               hex(c.get("obs", 0))))
        key = "%x@%x" % (want[0], want[1])
        bounds[key] = bounds.get(key, 0) + 1
        site_pass += matches(c, want, site_shift=1)
        for n in ctl:
            nw = run_model(inp, neg=n)
            if nw != want:
                ctl[n][0] += 1
                ctl[n][1] += matches(c, nw)
    line = ("AI52C %s cases=%d match=%d bad=%d stopped=%d traced=%d le_separating=%d le_passed=%d "
            "d0_separating=%d d0_passed=%d site_control_passed=%d boundaries=%d" % (
                fam, len(meta), match, len(bad), stops, len(traced), ctl["le"][0], ctl["le"][1], ctl["d0"][0],
                ctl["d0"][1], site_pass, len(bounds)))
    return line, bad[:20], traced[:20], bounds


def cmd_check(d):
    allok = True
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
    print("AI52C result=%s" % ("ok" if allok else "FAIL"))


def cmd_manifest(d, write):
    rows = []
    for fam in FAMILIES:
        for ext in ("cases", "mem", "out"):
            p = os.path.join(d, "%s.%s" % (fam, ext))
            if os.path.exists(p):
                rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.basename(p)))
    p = os.path.join(d, "check.txt")
    if os.path.exists(p):
        rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), "check.txt"))
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

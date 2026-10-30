#!/usr/bin/env python3
"""Plan 0052 phase 1.2, catalogue batch 1 (pool-A, `lane/r52b`): ten think functions of the AI table run under
Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java and compared with the models
below. No game run, no slot.

    python3 -I tools/ai_cat_emu.py cases [--dir D]      write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/ai_cat_emu.py check [--dir D]      compare every D/<family>.out with its model, account for every
                                                        traced access, run the negative and site controls
    python3 -I tools/ai_cat_emu.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r52b/emu. `--no-tune` (with `--dir workspace/logs/r52b/emu/dev`) writes and checks the
development run's cases: the same writer without the per-family tuning of the viper and quill-rat inputs. Every case draw comes from random.Random("r52b-<family>"), so `cases` regenerates
identical files.

Each family runs one think function `(ECX game, EDX unit; ctx)` (ai/0002) on a declared image: the game's difficulty
byte (+0x6D) and frame (+0xA8); the unit's type, monster data pointer (+0x14) and seed (+0x20/+0x24); the monster data's
AI control pointer (+0x28) and +0x54 word; the AI control's +0x14, +0x18, +0x20; the AiCtx (+0x00 ctl, +0x08 target,
+0x14 distance, +0x18 melee, +0x1C MonStats record); the MonStats record's aip block (+0x56..+0x85) and Skill1/Sk1mode
(+0x170, +0x180); for the two viper families the target unit with a path (its subtile position). Every callee the
function reaches is an observed boundary, except RNG_Range (0x0045C390), sub_005DD2B0_AiMonState3or19 and its callee
0x005734E0, sub_0058EE80_AiParamsHead and the target position getters 0x0045ADF0/0x0045AE20 (with 0x006488C0/
0x00648900), which run on the declared image. The claim per case: the first boundary reached, its call site (the
return address), the registers and stack arguments the callee takes, the unit seed at the boundary and, for
`bloodhawk`, the AI control's +0x14 at the boundary.

Families (function, row):
  brute     0x005EFB80 row 7  Brute         skeleton  0x005EFCF0 row 2  Skeleton
  zombie    0x005EFE20 row 3  Zombie        bighead   0x005EFF50 row 4  Bighead
  bloodhawk 0x005F00E0 row 5  BloodHawk     wraith    0x005F0A20 row 9  Wraith
  goatman   0x005F12A0 row 12 Goatman       quillrat  0x005F1140 row 14 QuillRat
  viper     0x005F1B60 row 16 ClawViper     viperex   0x005F1DE0 row 142 ClawViperEx

Controls: `le` compares each draw with `<=` instead of `<`; `d0` reads every aip from the Normal column; `site`
expects each call site one byte later. Each must fail every case it separates.

Not covered (ADR-0021): every callee at or after a boundary (the mode command, the move helpers, the override setter,
the life percent, the room, the state setter, the skill target test) and so every branch that a boundary call's result
decides (Brute's and Bighead's life tests, Zombie's level test, the StepAway results, ClawViperEx's +0x18 write).
Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r52b", "emu")

MUL = 0x6AC690C5
GAME = 0x12000000
UNIT = 0x12100000
TARGET = 0x12300000
TPATH = 0x12400000
MDATA = 0x12500000
MREC = 0x12600000
CTX = 0x12700000
CTL = 0x12800000
REC = 0x12900000
STK_LO = 0x7FEFFC00
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)

SETMODE, IDLE, WALK, PATHOVR, WALK13, RUN, RING, T56, STEPAWAY, WALKSTOP = (
    0x005DDF90, 0x005DE080, 0x005DEC80, 0x005DE190, 0x005DED40, 0x005DED20, 0x005DE200, 0x005DF7D0, 0x005DEFE0,
    0x005DEF80)
FINDHOSTILE, AILIFE, UNITLIFE, TOWARD, GETROOM, STATESET, SKILLOK, USESKILL, FINDUNIT, PARAMSPOP = (
    0x005DDC30, 0x005DD280, 0x00621F20, 0x005DE6D0, 0x00620BB0, 0x00639DB0, 0x005FD470, 0x005DEAD0, 0x00552F60,
    0x0058ED10)
OBSERVE = (SETMODE, IDLE, WALK, PATHOVR, WALK13, RUN, RING, T56, STEPAWAY, WALKSTOP, FINDHOSTILE, AILIFE, UNITLIFE,
           TOWARD, GETROOM, STATESET, SKILLOK, USESKILL, FINDUNIT, PARAMSPOP, 0x0061A1B0, 0x00540E60, 0x005DEFB0)

FNS = {"brute": 0x005EFB80, "skeleton": 0x005EFCF0, "zombie": 0x005EFE20, "bighead": 0x005EFF50,
       "bloodhawk": 0x005F00E0, "wraith": 0x005F0A20, "goatman": 0x005F12A0, "quillrat": 0x005F1140,
       "viper": 0x005F1B60, "viperex": 0x005F1DE0}
FAMILIES = tuple(FNS)
NCASES = 240


def u32(v):
    return v & 0xFFFFFFFF


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
    """One case's inputs and the model's running state (the unit seed)."""

    def __init__(self, inp, neg=None):
        self.i, self.neg = inp, neg
        self.seed = list(inp["seed"])
        self.ctl14 = inp["ctl14"]

    def aip(self, k):
        d = 0 if self.neg == "d0" else self.i["diff"]
        return self.i["aip"][k - 1][d]

    def draw(self):
        step(self.seed)
        return self.seed[0] % 100

    def lt(self, a, b):
        return a <= b if self.neg == "le" else a < b

    def chance(self, k):
        return self.lt(self.draw(), self.aip(k))

    def st(self):
        return self.i["m54"] in (3, 19)

    def hit(self, fn, site, args, ecx=GAME, edx=UNIT):
        raise Hit((fn, site, ecx, edx, [u32(a) for a in args], list(self.seed), self.ctl14))


def m_brute(e):
    t = e.i["target"]
    if not e.i["melee"]:
        e.hit(UNITLIFE, 0x005EFCA9, [UNIT], ecx=None, edx=None)
    if e.chance(3):
        if e.chance(4):
            e.hit(SETMODE, 0x005EFC27, [4, t])
        e.hit(SETMODE, 0x005EFC3F, [5, t])
    if e.chance(3):
        e.hit(T56, 0x005EFC88, [t, 4, 0])
    e.hit(IDLE, 0x005EFC9A, [15])


def m_skeleton(e):
    t = e.i["target"]
    if not e.i["melee"]:
        if e.chance(1):
            e.hit(WALK, 0x005EFE11, [t, 7])
    elif e.chance(3):
        if e.chance(4):
            e.hit(SETMODE, 0x005EFD96, [4, t])
        e.hit(SETMODE, 0x005EFDAC, [5, t])
    e.hit(IDLE, 0x005EFDC6, [e.aip(2)])


def m_zombie(e):
    t = e.i["target"]
    if e.i["melee"]:
        if e.chance(4):
            e.hit(SETMODE, 0x005EFE93, [4, t])
        e.hit(SETMODE, 0x005EFEA9, [5, t])
    if not e.st():
        if not (e.i["dist"] < e.aip(2) and e.chance(1)):
            e.hit(GETROOM, 0x005EFF0E, [UNIT], ecx=None, edx=None)
    e.hit(PATHOVR, 0x005EFF26, [100, 0], ecx=UNIT, edx=0)


def m_bighead(e):
    t = e.i["target"]
    if not e.i["melee"] and e.st():
        e.hit(SETMODE, 0x005F003E, [5, t])
    e.hit(AILIFE, 0x005EFF8F, [], ecx=UNIT, edx=None)


def m_bloodhawk(e):
    t, dist = e.i["target"], e.i["dist"]
    if e.ctl14 == 1 and e.i["melee"]:
        e.ctl14 = 0
        e.hit(SETMODE, 0x005F0124, [4, t])
    e.ctl14 = 0
    if not e.i["melee"]:
        if e.chance(1):
            e.hit(PATHOVR, 0x005F01DD, [e.aip(5), dist], ecx=UNIT, edx=0)
        if dist > 3:
            if e.chance(2):
                e.hit(PATHOVR, 0x005F0246, [-50, 0], ecx=UNIT, edx=0)
            e.hit(PATHOVR, 0x005F0261, [0, 0], ecx=UNIT, edx=0)
    elif e.chance(3):
        e.hit(SETMODE, 0x005F0188, [4, t])
    e.hit(PATHOVR, 0x005F028A, [e.aip(4), 0], ecx=UNIT, edx=0)


def m_wraith(e):
    t = e.i["target"]
    if not e.i["melee"]:
        if e.chance(1):
            e.hit(TOWARD, 0x005F0AD4, [t, 12, 0])
    elif e.chance(3):
        e.hit(SETMODE, 0x005F0A87, [4, t])
    e.hit(IDLE, 0x005F0AEA, [e.aip(2)])


def m_goatman(e):
    t = e.i["target"]
    if not e.i["melee"]:
        if e.chance(1):
            e.hit(WALK, 0x005F1352, [t, 7])
    elif e.chance(3):
        e.hit(SETMODE, 0x005F1307, [4, t])
    e.hit(IDLE, 0x005F1368, [e.aip(2)])


def m_quillrat(e):
    t, dist = e.i["target"], e.i["dist"]
    if e.i["head"]:
        e.hit(FINDUNIT, 0x005F1181, [e.i["rec_guid"]], ecx=GAME, edx=e.i["rec_type"])
    if e.i["melee"]:
        e.hit(SETMODE, 0x005F11C0, [4, t])
    if e.st():
        e.hit(SETMODE, 0x005F11E3, [5, t])
    if dist < e.aip(1):
        if e.chance(2):
            e.hit(SETMODE, 0x005F1243, [5, t])
        e.hit(STEPAWAY, 0x005F1261, [t, e.aip(4) & 0xFF, 1])
    a4 = e.aip(4)
    r = 3 if a4 < 3 else a4 & 0xFF
    e.hit(RING, 0x005F1293, [(t & 0xFFFFFF00) | r])


def viper_state_clear(e):
    a6 = e.aip(6)
    if e.ctl14 != 0 and a6 != 0:
        e.hit(STATESET, 0x005F1BAE if e.i["fam"] == "viper" else 0x005F1E2E,
              [UNIT, 0x5B if a6 == 2 else 0x5A, 0], ecx=None, edx=None)


def m_viper(e):
    t, dist = e.i["target"], e.i["dist"]
    viper_state_clear(e)
    if e.i["melee"]:
        if not e.chance(3):
            e.hit(IDLE, 0x005F1C7D, [e.aip(5)])
        if e.chance(4):
            e.hit(SETMODE, 0x005F1C4B, [4, t])
        e.hit(SETMODE, 0x005F1C61, [5, t])
    if e.i["skill1"] >= 0 and dist < e.aip(2) and e.chance(1):
        e.hit(SKILLOK, 0x005F1D0E, [e.i["skill1"], t, e.i["tx"], e.i["ty"]])
    if e.lt(e.draw(), 50):
        e.hit(WALK, 0x005F1DAD, [t, 7])
    e.hit(IDLE, 0x005F1DC9, [e.aip(5)])


def m_viperex(e):
    t, dist = e.i["target"], e.i["dist"]
    viper_state_clear(e)
    if e.i["melee"]:
        if e.chance(3):
            e.hit(SETMODE, 0x005F1E82, [5, t])
        e.hit(IDLE, 0x005F1E98, [e.aip(5)])
    if dist < e.aip(7) and e.chance(4):
        if e.i["ctl18"] < e.i["frame"]:
            e.hit(SETMODE, 0x005F1F11, [4, t])
        e.hit(IDLE, 0x005F1F43, [e.aip(5)])
    if e.i["skill1"] >= 0 and dist < e.aip(2) and e.chance(1):
        e.hit(SKILLOK, 0x005F1FD6, [e.i["skill1"], t, e.i["tx"], e.i["ty"]])
    if e.lt(e.draw(), 50):
        e.hit(WALK, 0x005F2075, [t, 7])
    e.hit(IDLE, 0x005F2091, [e.aip(5)])


MODELS = {"brute": m_brute, "skeleton": m_skeleton, "zombie": m_zombie, "bighead": m_bighead,
          "bloodhawk": m_bloodhawk, "wraith": m_wraith, "goatman": m_goatman, "quillrat": m_quillrat,
          "viper": m_viper, "viperex": m_viperex}


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


def gen_family(fam, rnd, tune=True):
    cases, meta = [], []
    for k in range(NCASES):
        seed = (rnd.randrange(1 << 32), rnd.randrange(1 << 32))
        ds = first_draws(seed, 4)
        aip = []
        for _ in range(8):
            col = []
            for _ in range(3):
                col.append(rnd.choice(ds + ds + [rnd.randrange(0, 101), rnd.randrange(-3, 111), 0, 1, 2, 3, 50]))
            aip.append(col)
        inp = {
            "fam": fam, "seed": seed, "diff": k % 3, "aip": aip,
            "melee": rnd.randrange(2), "dist": rnd.choice([0, 1, 2, 3, 4, 5, 10, 14, 15, 16, 25, 40,
                                                           rnd.randrange(0, 60)] + [a for a in aip[1]]),
            "m54": rnd.choice([0, 3, 19, 7, 2]), "ctl14": rnd.choice([0, 0, 1, 1, 2]),
            "frame": rnd.randrange(100, 100000), "head": rnd.randrange(3) == 0,
            "rec_type": rnd.randrange(6), "rec_guid": rnd.randrange(1 << 32),
            "skill1": rnd.choice([-1, rnd.randrange(0, 400)]), "sk1mode": rnd.randrange(16),
            "tx": rnd.randrange(1 << 16), "ty": rnd.randrange(1 << 16),
        }
        inp["ctl18"] = inp["frame"] + rnd.choice([-50, -1, 0, 1, 50])
        if tune and fam in ("viper", "viperex", "quillrat"):   # reach the later branches more often (not --no-tune)
            inp["ctl14"] = rnd.choice([0, 0, 0, 0, 1])
            inp["head"] = rnd.randrange(6) == 0
            inp["melee"] = int(rnd.randrange(4) == 0)
            inp["m54"] = rnd.choice([0, 0, 0, 3, 19])
            inp["skill1"] = rnd.choice([-1, rnd.randrange(0, 400), rnd.randrange(0, 400)])
            inp["dist"] = rnd.choice([inp["dist"], rnd.randrange(0, 8)])
        if fam == "viperex":
            inp["dist"] = rnd.choice([inp["dist"], aip[6][inp["diff"]], aip[6][inp["diff"]] - 1])
        inp["target"] = TARGET if fam in ("viper", "viperex") else (rnd.randrange(1, 1 << 31) & ~3)
        lines = [
            "w %08x %s" % (GAME + 0x6D, "%02x" % inp["diff"]),
            "w %08x %s" % (GAME + 0xA8, hx32(inp["frame"])),
            "w %08x %s" % (UNIT, hx32(1)), "w %08x %s" % (UNIT + 0x14, hx32(MDATA)),
            "w %08x %s%s" % (UNIT + 0x20, hx32(seed[0]), hx32(seed[1])),
            "w %08x %s" % (MDATA + 0x28, hx32(CTL)), "w %08x %s" % (MDATA + 0x54, hx32(inp["m54"])),
            "w %08x %s%s%s" % (CTL + 0x14, hx32(inp["ctl14"]), hx32(inp["ctl18"]), hx32(0)),
            "w %08x %s" % (CTL + 0x20, hx32(REC if inp["head"] else 0)),
            "w %08x %s%s%s%s" % (REC + 0x08, hx32(1), hx32(inp["rec_type"]), hx32(inp["rec_guid"]), hx32(0)),
            "w %08x %s" % (CTX, hx32(CTL) + hx32(0) + hx32(inp["target"]) + hx32(0) + hx32(0)
                           + hx32(inp["dist"]) + hx32(inp["melee"]) + hx32(MREC) + hx32(0)),
            "w %08x %s" % (MREC + 0x56, "".join(hx16(aip[j][d]) for j in range(8) for d in range(3))),
            "w %08x %s" % (MREC + 0x170, hx16(inp["skill1"]) + "00" * 14),
            "w %08x %s" % (MREC + 0x180, "%02x" % inp["sk1mode"] + "00" * 7),
        ]
        if fam in ("viper", "viperex"):
            lines += ["w %08x %s" % (TARGET, hx32(1)), "w %08x %s" % (TARGET + 0x2C, hx32(TPATH)),
                      "w %08x %s" % (TPATH + 0x02, hx16(inp["tx"])), "w %08x %s" % (TPATH + 0x06, hx16(inp["ty"]))]
        lines += ["d %08x 1024" % STK_LO, "d %08x 8" % (UNIT + 0x20), "d %08x 4" % (CTL + 0x14),
                  "call %08x %08x %08x %08x" % (FNS[fam], GAME, UNIT, CTX)]
        cases.append(lines)
        meta.append(inp)
    mem = ["observe %08x" % a for a in OBSERVE] + ["guard %08x" % a for a in FATAL + ALLOC]
    return cases, meta, mem


def cmd_cases(d, tune=True):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        cases, meta, mem = gen_family(fam, random.Random("r52b-" + fam), tune)
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


def observed(c, nargs):
    a = c.get("args", b"")
    args = [struct.unpack_from("<I", a, 4 + 4 * i)[0] for i in range(nargs)]
    ret = struct.unpack_from("<I", a, 0)[0]
    seed = list(struct.unpack("<II", c["dumps"][UNIT + 0x20]))
    ctl14 = struct.unpack("<I", c["dumps"][CTL + 0x14])[0]
    return args, ret, seed, ctl14


def matches(c, want, fam, site_shift=0):
    fn, site, ecx, edx, args, seed, ctl14 = want
    if c.get("obs") != fn:
        return False
    got_args, ret, got_seed, got14 = observed(c, len(args))
    ok = ret == site + site_shift and got_args == args and got_seed == seed
    if ecx is not None:
        ok = ok and c["regs"]["ecx"] == ecx
    if edx is not None:
        ok = ok and c["regs"]["edx"] == u32(edx)
    if fam == "bloodhawk":
        ok = ok and got14 == ctl14
    return ok


def check_family(fam, d, tune=True):
    _, meta, _ = gen_family(fam, random.Random("r52b-" + fam), tune)
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
        ok = matches(c, want, fam)
        match += ok
        if not ok:
            bad.append("case %d mismatch want=%s obs=%s" % (c["n"], hex(want[0]), hex(c.get("obs", 0))))
        bounds["%x@%x" % (want[0], want[1])] = bounds.get("%x@%x" % (want[0], want[1]), 0) + 1
        site_pass += matches(c, want, fam, site_shift=1)
        for n in ctl:
            nw = run_model(inp, neg=n)
            if nw != want:
                ctl[n][0] += 1
                ctl[n][1] += matches(c, nw, fam)
    line = ("AI52B %s cases=%d match=%d bad=%d stopped=%d traced=%d le_separating=%d le_passed=%d "
            "d0_separating=%d d0_passed=%d site_control_passed=%d boundaries=%d" % (
                fam, len(meta), match, len(bad), stops, len(traced), ctl["le"][0], ctl["le"][1], ctl["d0"][0],
                ctl["d0"][1], site_pass, len(bounds)))
    return line, bad[:20], traced[:20], bounds


def cmd_check(d, tune=True):
    allok = True
    for fam in FAMILIES:
        line, bad, traced, bounds = check_family(fam, d, tune)
        print(line)
        print("  SITES " + " ".join("%s:%d" % kv for kv in sorted(bounds.items())))
        for b in bad:
            print("  BAD", b)
        for t in traced:
            print("  TRACED", t)
        if bad or traced or "le_passed=0" not in line or "d0_passed=0" not in line \
                or "site_control_passed=0" not in line:
            allok = False
    print("AI52B result=%s" % ("ok" if allok else "FAIL"))


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
    ap.add_argument("--no-tune", action="store_true", help="the development run's case writer (emu/dev)")
    a = ap.parse_args(argv)
    if a.cmd == "cases":
        cmd_cases(a.dir, not a.no_tune)
    elif a.cmd == "check":
        cmd_check(a.dir, not a.no_tune)
    else:
        cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    main(sys.argv[1:])

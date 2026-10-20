#!/usr/bin/env python3
"""Plan 0046 Phase 1 (the skills and missiles function catalogue): numbered functions of the pinned image run under
Ghidra's p-code emulator (ADR-0015) with re/ghidra_scripts/EmuBoundary.java and compared with the models below. No
game run, no slot. Batch 9a (missile server do functions 1-18) is the first user; later batches add families.

    python3 -I tools/skills_catalogue_emu.py cases [FAMILY ...] [--dir D]   write D/<family>.cases, .mem, .json
    tools/ghidra.sh emuboundary D/<family>.cases D/<family>.mem > D/<family>.out
    python3 -I tools/skills_catalogue_emu.py check [FAMILY ...] [--dir D]   compare D/<family>.out with the models,
                                                                           account for every traced access, run the
                                                                           negative controls
    python3 -I tools/skills_catalogue_emu.py static                        objdump pins (ADR-0015 (5)), the writer
                                                                           scan of the declared .data reads, the
                                                                           image tables the models read
    python3 -I tools/skills_catalogue_emu.py manifest [--write] [--dir D]  sha256 of every file under D

**Boundaries.** Most do functions end by calling a function outside the claim (MissileCreate, the path planner, a
spawn, an item creation, the do-1 step `sub_005AE1F0_MissileMoveCollide`). The memory spec names each of them with an
`observe` line: a case that reaches one ends there, and EmuBoundary prints its registers and the 64 bytes at ESP (the
return address, then the stack arguments). The claim of such a case is the map from the inputs to that call's
arguments and to the bytes written before it; nothing after the call. A case that returns (no boundary reached) is
compared on EAX and the bytes popped.

Families (function, Missiles rows with that pSrvDoFunc):
  cellsub   do 6 0x005AE680, do 9 0x005AE940, do 12 0x005AECA0: SubMissile1 at the missile's position on a frame
            with path flag 8 (firewallmaker, bat lightning bolt, diabwallmaker ...)
  orb       do 15 0x005AF030: frozenorb's bolts, one per Param1 frames, direction from MissileData+0x28
  spiral    do 16 0x005AF170: frozenorbnova's turn of the path target, from MissileData+0x28/+0x2C
  scatter   do 8 0x005AE8A0, do 10 0x005AEA60, do 17 0x005AF240 through sub_005A9820_MissSubNearReseed: the re-seed
            of the missile from its position and the two RNG_RangeB offsets (monblizcenter, blizzardcenter,
            cairnstones), and do 17's portal test
  chest     do 18 0x005AF300: towerchestspawner (the chest's events, the gold drops' two RNG_RangeB offsets)
  homing    do 11 0x005AEB60: fingermagespider's step towards its target
  periodic  do 14 0x005AEF70: the grim wards' skill do-function call
  guided    do 7 0x005AE780: guidedarrow and bonespirit's gates (owner alive, not in town, MissileData+0x28 bit 0),
            with a missile as the stored target (UnitIsDead is 1 for it, so UnitsHostile is never reached)
  sublob    do 2 0x005AE400 and sub_005A9720: SubMissile1 per path flag 8 with SrvCalc1 as the loop switch

Each check prints `CAT9A <family> key=value ...`: cases, matches, mismatches (bad), the negative control's mismatch
count (neg, must be > 0), traced accesses outside the stack, spec and case memory (traced), those outside the declared
read set (undeclared, must be 0), cases stopped other than at a boundary (stopped, must be 0), then the outcome and
branch counters. Every case-writer draw comes from random.Random("cat9a-<family>").

Stdlib only, plus objdump for `static` (through tools/sweep_s4b.py). Writes only under D (default
workspace/logs/skills-cat-9a/).
"""
import argparse
import collections
import hashlib
import json
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rng as RNG  # noqa: E402
import sweep_s4b as S4  # noqa: E402

ROOT = os.path.dirname(HERE)
DEFDIR = os.path.join(ROOT, "workspace", "logs", "skills-cat-9a")
M32 = 0xFFFFFFFF


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def cdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def cmod(a, b):
    return a - b * cdiv(a, b)


def hx(b):
    return b.hex()


def le32(v):
    return struct.pack("<I", v & M32)


def le16(v):
    return struct.pack("<H", v & 0xFFFF)


# ------------------------------------------------------------------------------------------------ image addresses
G_PDATATABLES = 0x00744304
COOKIE = 0x00749DE0
HASH_OFF = 0x006E10E0           # .rdata: per unit type 0..4, the offset of its 128 hash buckets in the game
CIRCLE_X = 0x006E2B78           # .rdata: 64 s32, x of 64 directions on a radius-30 circle (do 15)
CIRCLE_Y = 0x006E2A78           # .rdata: the y
SK_NFUNCS = 0x007457AC          # .data: the skills calc function count CALC_Eval is passed (SKILLS_EvalCalc)
MS_NFUNCS = 0x00745848          # .data: the missiles calc function count (MISS_EvalCalc)

FN = {
    "do2": 0x005AE400, "do6": 0x005AE680, "do7": 0x005AE780, "do8": 0x005AE8A0, "do9": 0x005AE940, "do10": 0x005AEA60,
    "do11": 0x005AEB60, "do12": 0x005AECA0, "do14": 0x005AEF70, "do15": 0x005AF030, "do16": 0x005AF170,
    "do17": 0x005AF240, "do18": 0x005AF300,
}
BOUND = {   # observe addresses: callees outside the claims
    0x005AE1F0: "MoveCollide", 0x0059FA30: "MissileCreate", 0x00649970: "PathPlan", 0x0064CB30: "CellTestAt",
    0x005A9930: "PermPortalAtUnit", 0x00553380: "UnitSetEvent", 0x00585E00: "ChestDrop", 0x00555DA0: "FreeSpot",
    0x0056D810: "CallDoFunc",
}
BOUND_BY_NAME = {v: k for k, v in BOUND.items()}
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)

# scratch memory (outside the image)
DT = 0x12000000          # a scratch DataTables (only the fields the code reads are written)
MREC = 0x12010000        # missile records (0x1A4)
SREC = 0x12020000        # skills records (0x23C)
SPOOL = 0x12030000       # skills calc pool
MPOOL = 0x12038000       # missiles calc pool
GAME = 0x12100000        # a game (hash buckets only)
MU = 0x12200000          # the missile unit
MD = 0x12200400          # its MissileData
MP = 0x12200800          # its path
OWN = 0x12210000         # the owner unit
OWNP = 0x12210400        # its path
TGT = 0x12220000         # a target unit (homing)
TGTP = 0x12220400
DECOY = 0x12230000       # a unit in the owner's hash chain ahead of it
OBJ = 0x12240000         # an object (chest)
STK_LO, STK_LEN = 0x7FEFFC00, 0x400    # the emulated stack below the entry ESP 0x7FF00000
NREC = 4
NSREC = 3

FAMILIES = {}


def family(name):
    def deco(f):
        FAMILIES[name] = f
        return f
    return deco


# --------------------------------------------------------------------------------------------------- the world
class Case:
    """One call: the bytes it writes (`w` lines, one per field read), its dumps and its model's expectation."""

    def __init__(self, fn):
        self.fn = fn
        self.w = []
        self.fields = {}

    def put(self, addr, b):
        self.w.append("w %08x %s" % (addr, hx(b)))
        self.fields[addr] = b

    def lines(self, ecx, edx, regs=None, extra_dumps=()):
        out = list(self.w)
        for r, v in (regs or {}).items():
            out.append("r %s %08x" % (r, v & M32))
        out.append("d %08x %d" % (STK_LO, STK_LEN))
        out.append("d %08x %d" % (MD, 0x34))
        out.append("d %08x 8" % (MU + 0x20))
        for a, n in extra_dumps:
            out.append("d %08x %d" % (a, n))
        out.append("call %08x %08x %08x" % (self.fn, ecx, edx))
        return out


def hash_slot(typ, guid):
    if typ == 5:
        return GAME + 0x1B20
    return GAME + S4.dword(HASH_OFF + 4 * typ) + 4 * (guid & 0x7F)


def put_unit_found(c, rnd, base, typ, guid, decoy=None):
    """Make GameFindUnit(game, typ, guid) find `base` (optionally behind a decoy with another guid)."""
    slot = hash_slot(typ, guid)
    if decoy is not None:
        c.put(slot, le32(DECOY))
        c.put(DECOY + 0x0C, le32(decoy))
        c.put(DECOY + 0xE4, le32(base))
    else:
        c.put(slot, le32(base))
    c.put(base + 0x0C, le32(guid))
    c.put(base + 0xE4, le32(0))


def put_unit_absent(c, rnd, typ, guid):
    slot = hash_slot(typ, guid)
    if rnd.random() < 0.5:
        c.put(slot, le32(0))
    else:
        g2 = (guid + 1 + rnd.randrange(1000)) & M32
        c.put(slot, le32(DECOY))
        c.put(DECOY + 0x0C, le32(g2))
        c.put(DECOY + 0xE4, le32(0))


def put_owner(c, rnd, present_p=0.85, types=(0, 1)):
    """The missile's owner link (Unit+0xC8 bit 10, +0x94 type, +0x98 guid) and the hash chain. -> owner address or 0."""
    c8 = rnd.getrandbits(32)
    mode = rnd.random()
    typ = rnd.choice(types)
    guid = rnd.getrandbits(32)
    if mode < present_p:
        c8 |= 0x400
        c.put(MU + 0xC8, le32(c8))
        c.put(MU + 0x94, le32(typ))
        c.put(MU + 0x98, le32(guid))
        put_unit_found(c, rnd, OWN, typ, guid, decoy=(guid ^ 0x80) if rnd.random() < 0.3 else None)
        return OWN
    if mode < present_p + (1 - present_p) / 2:
        c.put(MU + 0xC8, le32(c8 & ~0x400))
        return 0
    c8 |= 0x400
    c.put(MU + 0xC8, le32(c8))
    c.put(MU + 0x94, le32(typ))
    c.put(MU + 0x98, le32(guid))
    put_unit_absent(c, rnd, typ, guid)
    return 0


def owner_of(c):
    """Model of sub_00552FD0_UnitGetOwner over the fields the case wrote."""
    c8 = struct.unpack("<I", c.fields[MU + 0xC8])[0]
    if not c8 & 0x400:
        return 0
    typ = struct.unpack("<I", c.fields[MU + 0x94])[0]
    guid = struct.unpack("<I", c.fields[MU + 0x98])[0]
    return find_unit(c, typ, guid)


def find_unit(c, typ, guid):
    """Model of sub_00552F60_GameFindUnit (types 0..5 only)."""
    slot = hash_slot(typ, guid)
    u = struct.unpack("<I", c.fields[slot])[0]
    while u:
        if struct.unpack("<I", c.fields[u + 0x0C])[0] == guid:
            return u
        u = struct.unpack("<I", c.fields[u + 0xE4])[0]
    return 0


def put_missile(c, rnd, cls, path=True, room=None):
    """The missile unit: type 3, class, data pointer, path; position (path +0x02, +0x06)."""
    c.put(MU + 0x00, le32(3))
    c.put(MU + 0x04, le32(cls))
    c.put(MU + 0x14, le32(MD))
    c.put(MU + 0x2C, le32(MP if path else 0))
    st = {"x": rnd.getrandbits(16), "y": rnd.getrandbits(16), "path": path}
    if path:
        c.put(MP + 0x02, le16(st["x"]))
        c.put(MP + 0x06, le16(st["y"]))
        if room is not None:
            c.put(MP + 0x1C, le32(room))
    return st


def put_mdata(c, rnd, **kw):
    """MissileData fields: skill +0x0A, level +0x0C, range +0x0E, left +0x10 (s16), +0x28, +0x2C (s32)."""
    v = {}
    for name, off, n in (("skill", 0x0A, 2), ("lvl", 0x0C, 2), ("range", 0x0E, 2), ("left", 0x10, 2),
                         ("w28", 0x28, 4), ("w2c", 0x2C, 4)):
        if name in kw:
            val = kw[name]
            v[name] = val
            c.put(MD + off, le16(val) if n == 2 else le32(val))
    return v


def small(rnd, lo=-3, hi=40):
    return rnd.choice([rnd.randint(lo, hi)] * 6 + [0, 1, -1, rnd.randint(-0x8000, 0x7FFF)])


def put_rec(c, rnd, cls, **kw):
    """One missile record: only the fields named (SubMissile1 +0x18 s16, Param1..5 +0x38.., SrvCalc1 +0x80,
    Range +0x96 s16, Size +0x18A u8)."""
    base = MREC + 0x1A4 * cls
    offs = {"sub": (0x18, 2), "p1": (0x38, 4), "p2": (0x3C, 4), "p3": (0x40, 4), "p4": (0x44, 4), "p5": (0x48, 4),
            "calc": (0x80, 4), "range": (0x96, 2), "size": (0x18A, 1)}
    for k, val in kw.items():
        off, n = offs[k]
        c.put(base + off, le16(val) if n == 2 else (bytes([val & 0xFF]) if n == 1 else le32(val)))
    return base


def mem_spec(extra=()):
    lines = ["dword %08x %08x" % (G_PDATATABLES, DT),
             "dword %08x %08x" % (DT + 0xB64, MREC), "dword %08x %08x" % (DT + 0xB6C, NREC),
             "dword %08x 6b3a11f5" % COOKIE]
    lines += list(extra)
    lines += ["observe %08x" % a for a in sorted(BOUND)]
    lines += ["guard %08x" % a for a in FATAL + ALLOC]
    return lines


# ------------------------------------------------------------------------------------------------- the output
def read_out(path):
    calls, reads, writes = [], [], []
    for ln in open(path):
        p = ln.split()
        if not p:
            continue
        if p[0] == "C":
            c = {"n": int(p[1]), "fn": int(p[2], 16), "dumps": {}}
            if p[3] == "STOP":
                c["stop"] = " ".join(p[4:])
            elif p[3] == "OBS":
                c["obs"] = int(p[4], 16)
                kv = dict(x.split("=") for x in p[5:])
                c["regs"] = {k: int(v, 16) for k, v in kv.items() if k != "steps"}
            else:
                kv = dict(x.split("=") for x in p[3:])
                c.update(eax=int(kv["eax"], 16), pop=int(kv["pop"]))
            calls.append(c)
        elif p[0] == "A":
            calls[-1]["args"] = bytes.fromhex(p[1])
        elif p[0] == "D":
            calls[-1]["dumps"][int(p[1], 16)] = bytes.fromhex(p[2]) if len(p) > 2 else b""
        elif p[0] in ("R", "W"):
            (reads if p[0] == "R" else writes).append((int(p[1], 16), int(p[2], 16), int(p[3]), int(p[4])))
    return calls, reads, writes


def stack_bytes(c, addr, n):
    s = c["dumps"][STK_LO]
    o = addr - STK_LO
    if o < 0 or o + n > len(s):
        return None
    return s[o:o + n]


def arg(c, i):
    return struct.unpack_from("<I", c["args"], 4 + 4 * i)[0]


class Report:
    def __init__(self, fam):
        self.fam = fam
        self.c = collections.Counter()
        self.notes = []
        self.br = collections.Counter()

    def bad(self, why):
        self.c["bad"] += 1
        if self.c["bad"] <= 25:
            self.notes.append("BAD " + why)

    def line(self):
        keys = ["cases", "match", "bad", "neg", "traced", "undeclared", "stopped"]
        return "CAT9A %s " % self.fam + " ".join("%s=%d" % (k, self.c[k]) for k in keys)


def account(rep, reads, writes, declared):
    seen = collections.Counter()
    for kind, rows in (("R", reads), ("W", writes)):
        for pc, a, n, cnt in rows:
            rep.c["traced"] += 1
            hit = None
            for lo, hi, k, why in declared:
                if lo <= a and a + n <= hi and (kind == "R" or "w" in k):
                    hit = why
                    break
            if hit is None:
                rep.c["undeclared"] += 1
                rep.bad("undeclared %s pc=0x%08X addr=0x%08X size=%d count=%d" % (kind, pc, a, n, cnt))
            else:
                seen[hit] += cnt
    for why, cnt in sorted(seen.items()):
        rep.notes.append("read-set %s: %d accesses" % (why, cnt))


RS_COOKIE = (COOKIE, COOKIE + 4, "r", "security cookie 0x00749DE0 (xor in, xor out; do 18 only)")
RS_HASH = (HASH_OFF, HASH_OFF + 20, "r", "hash-offset table 0x006E10E0 (.rdata)")
RS_CIRCLE = (CIRCLE_Y, CIRCLE_X + 256, "r", "64-direction circle 0x006E2A78/0x006E2B78 (.rdata)")
RS_SKN = (SK_NFUNCS, SK_NFUNCS + 4, "r", "skills calc function count 0x007457AC (.data; constant programs call none)")
RS_CALC_JT = (0x006C1164, 0x006C1164 + 4 * 22, "r", "CALC_Eval jump table 0x006C1164, opcodes 01-16 (.text)")
RS_SIZE_JT = (0x0062057C, 0x0062057C + 4 * 6, "r", "UNIT_GetSizeX jump table 0x0062057C, unit types 0-5 (.text)")
RS_MSN = (MS_NFUNCS, MS_NFUNCS + 4, "r", "missiles calc function count 0x00745848 (.data; constant programs call none)")


def compare(rep, c, exp, br):
    """exp: ('ret', eax, pop) or ('obs', name, {reg: value}, [arg values], {addr: bytes}, {stack addr: bytes})."""
    rep.c["cases"] += 1
    if "stop" in c:
        rep.c["stopped"] += 1
        rep.bad("case %d stopped: %s" % (c["n"], c["stop"]))
        return False
    ok = True
    why = ""
    if exp[0] == "ret":
        if "obs" in c:
            ok, why = False, "observed %s, want return" % BOUND.get(c["obs"], hex(c["obs"]))
        elif (c["eax"] & M32) != (exp[1] & M32) or c["pop"] != exp[2]:
            ok, why = False, "eax=%08x pop=%d want %08x %d" % (c["eax"], c["pop"], exp[1] & M32, exp[2])
    else:
        _, name, regs, args, mem, stk = exp
        if "obs" not in c:
            ok, why = False, "returned eax=%08x, want %s" % (c.get("eax", 0), name)
        elif c["obs"] != BOUND_BY_NAME[name]:
            ok, why = False, "observed %s, want %s" % (BOUND.get(c["obs"], hex(c["obs"])), name)
        else:
            for r, v in regs.items():
                if (c["regs"][r] & M32) != (v & M32):
                    ok, why = False, "%s=%08x want %08x" % (r, c["regs"][r], v & M32)
            for i, v in enumerate(args):
                if v is not None and arg(c, i) != (v & M32):
                    ok, why = False, "arg%d=%08x want %08x" % (i, arg(c, i), v & M32)
            for a, b in mem.items():
                if c["dumps"].get(a) != b:
                    ok, why = False, "mem %08x=%s want %s" % (a, c["dumps"].get(a, b"").hex(), b.hex())
            for reg, (off, b) in stk.items():
                got = stack_bytes(c, (c["regs"][reg] + off) & M32, len(b))
                if got != b:
                    ok, why = False, "[%s+%x]=%s want %s" % (reg, off, got.hex() if got else None, b.hex())
    if ok:
        rep.c["match"] += 1
        rep.br.update(br)
    else:
        rep.bad("case %d: %s" % (c["n"], why))
    return ok


def block(**kw):
    """A MissileCreate parameter block (0x5C bytes, zeroed by every caller)."""
    b = bytearray(0x5C)
    offs = {"flags": 0x00, "owner": 0x04, "source": 0x08, "cls": 0x10, "x": 0x14, "y": 0x18, "tx": 0x1C, "ty": 0x20,
            "skill": 0x2C, "lvl": 0x30, "loops": 0x34, "range": 0x4C}
    for k, v in kw.items():
        struct.pack_into("<I", b, offs[k], v & M32)
    return bytes(b)


def obs_create(game, blk):
    return ("obs", "MissileCreate", {"ecx": game}, [], {}, {"edx": (0, blk)})


def obs_move(game):
    return ("obs", "MoveCollide", {"ecx": game, "edx": MU}, [], {}, {})


# =============================================================================================== cellsub
@family("cellsub")
def cellsub(rnd, game):
    cases, exp = [], []
    for k in range(1800):
        which = ("do6", "do9", "do12")[k % 3]
        c = Case(FN[which])
        cls = rnd.randrange(NREC)
        invalid = which != "do9" and rnd.random() < 0.06
        if invalid:
            cls = rnd.choice([NREC, NREC + 5, -1, -0x1000])
        has_path = rnd.random() > 0.05
        st = put_missile(c, rnd, cls, path=has_path)
        sub = rnd.choice([rnd.randrange(700)] * 8 + [-1, -0x8000, 0x7FFF])
        if not invalid:
            put_rec(c, rnd, cls, sub=sub)
        own = put_owner(c, rnd)
        flag = rnd.getrandbits(32)
        if rnd.random() < 0.5:
            flag |= 8
        else:
            flag &= ~8
        if has_path:
            c.put(MP + 0x34, le32(flag))
        md = put_mdata(c, rnd, skill=small(rnd, 0, 400), lvl=small(rnd, 0, 60))
        br = collections.Counter([which])
        e = cellsub_model(which, invalid, sub, own, has_path, flag, st, md, game, br)
        cases += c.lines(game, MU)
        exp.append([which, invalid, sub, own, has_path, flag, st, md])
    return cases, mem_spec(), {"cases": exp}


def cellsub_model(which, invalid, sub, own, has_path, flag, st, md, game, br, neg=False):
    skill, lvl = s16(md["skill"]), s16(md["lvl"])
    if which == "do6":
        if not own or invalid or sub < 0 or not has_path:
            br["ret2"] += 1
            return ("ret", 2, 0)
        if flag & 8:
            br["create"] += 1
            return obs_create(game, block(flags=0x21, owner=own, cls=sub, x=st["x"], y=st["y"], tx=st["x"],
                                          ty=st["y"], skill=skill, lvl=lvl))
        br["move"] += 1
        return obs_move(game)
    if which == "do12":
        if invalid or sub < 0 or not own:
            br["ret2"] += 1
            return ("ret", 2, 0)
        if has_path and flag & 8:
            br["create"] += 1
            return obs_create(game, block(flags=0x21 if not neg else 0x01, owner=own, cls=sub, x=st["x"], y=st["y"],
                                          tx=st["x"], ty=st["y"], skill=skill, lvl=lvl))
        br["nopath_move" if not has_path else "move"] += 1
        return obs_move(game)
    # do 9: no owner or SubMissile1 test before the creation
    x = st["x"] if has_path else 0
    y = st["y"] if has_path else 0
    if has_path and flag & 8:
        br["create_noowner" if not own else "create"] += 1
        br["create_subneg"] += sub < 0
        return obs_create(game, block(flags=1, owner=own, cls=sub, x=x, y=y, skill=skill, lvl=lvl))
    br["move"] += 1
    return obs_move(game)


def cellsub_check(d, meta, calls, game):
    rep = Report("cellsub")
    neg = 0
    for c, row in zip(calls, meta["cases"]):
        br = collections.Counter()
        ok = compare(rep, c, cellsub_model(*row, game, br), br)
        if ok:
            negb = collections.Counter()
            e2 = cellsub_model(*row, game, negb, neg=True)
            r2 = Report("neg")
            compare(r2, c, e2, negb)
            neg += r2.c["bad"]
    return rep, neg, [RS_HASH]


# =============================================================================================== orb (do 15)
@family("orb")
def orb(rnd, game):
    cases, exp = [], []
    for k in range(1500):
        c = Case(FN["do15"])
        cls = rnd.randrange(NREC)
        invalid = rnd.random() < 0.04
        if invalid:
            cls = rnd.choice([NREC, -1])
        put_missile(c, rnd, cls)
        sub = rnd.choice([rnd.randrange(700)] * 10 + [-1])
        p1 = rnd.choice([1, 1, 2, 3, 5, 0, -4, rnd.randint(-100, 100)])
        p2 = rnd.choice([19, rnd.randint(-200, 200), rnd.getrandbits(32), 0x7FFFFFFF, s32(0x80000000)])
        if not invalid:
            put_rec(c, rnd, cls, sub=sub, p1=p1, p2=p2)
        own = put_owner(c, rnd, present_p=0.9)
        rng_ = rnd.choice([30, rnd.randint(-5, 300), rnd.getrandbits(16)])
        left = rnd.choice([rnd.randint(0, 30), rnd.getrandbits(16)])
        w28 = rnd.choice([rnd.randrange(64), rnd.getrandbits(32), 0x80000000, 0xFFFFFFC0, 0xFFFFFFFF])
        md = put_mdata(c, rnd, skill=small(rnd, 0, 400), lvl=small(rnd, 0, 60), range=rng_, left=left, w28=w28)
        cases += c.lines(game, MU)
        exp.append([invalid, sub, p1, p2, own, md])
    return cases, mem_spec(), {"cases": exp}


def orb_model(invalid, sub, p1, p2, own, md, game, br, neg=False):
    if invalid or sub < 0 or not own:
        br["ret2"] += 1
        return ("ret", 2, 0)
    period = p1 if p1 >= 1 else 1
    el = s16(md["range"]) - s16(md["left"])
    if cmod(el, period) > 0:
        br["move"] += 1
        return obs_move(game)
    br["elapsed_neg"] += el < 0
    w = s32(md["w28"])
    k = cmod(w, 64)
    if k < 0 and not neg:
        k = -k
        br["k_negated"] += 1
    k &= 63 if neg else 0xFFFFFFFF
    nxt = cmod(s32(p2 + k), 64)
    br["create"] += 1
    br["next_neg"] += nxt < 0
    x = s32(S4.dword(CIRCLE_X + 4 * k))
    y = s32(S4.dword(CIRCLE_Y + 4 * k))
    blk = block(flags=2, owner=own, source=MU, cls=sub, tx=x, ty=y, skill=s16(md["skill"]), lvl=s16(md["lvl"]))
    mdb = bytearray(dump_md(md))
    struct.pack_into("<I", mdb, 0x28, nxt & M32)
    return ("obs", "MissileCreate", {"ecx": game}, [], {MD: bytes(mdb)}, {"edx": (0, blk)})


def dump_md(md):
    b = bytearray(0x34)
    for name, off, n in (("skill", 0x0A, 2), ("lvl", 0x0C, 2), ("range", 0x0E, 2), ("left", 0x10, 2),
                         ("w28", 0x28, 4), ("w2c", 0x2C, 4)):
        if name in md:
            b[off:off + n] = le16(md[name]) if n == 2 else le32(md[name])
    return bytes(b)


def md_mask(c):
    """Only the MissileData bytes the case wrote are compared (the rest is left from earlier cases)."""
    return None


def orb_check(d, meta, calls, game):
    rep = Report("orb")
    neg = 0
    for c, row in zip(calls, meta["cases"]):
        br = collections.Counter()
        e = orb_model(*row, game, br)
        e = masked_md(e, row[-1], c)
        if compare(rep, c, e, br):
            r2 = Report("neg")
            compare(r2, c, masked_md(orb_model(*row, game, collections.Counter(), neg=True), row[-1], c), {})
            neg += r2.c["bad"]
    return rep, neg, [RS_HASH, RS_CIRCLE]


def masked_md(e, md, c):
    """Compare only the MissileData fields the case wrote: copy the other bytes from the dump."""
    if e[0] != "obs" or MD not in e[4] or MD not in c["dumps"]:
        return e
    want = bytearray(e[4][MD])
    got = c["dumps"][MD]
    keep = set()
    for name, off, n in (("skill", 0x0A, 2), ("lvl", 0x0C, 2), ("range", 0x0E, 2), ("left", 0x10, 2),
                         ("w28", 0x28, 4), ("w2c", 0x2C, 4)):
        if name in md:
            keep.update(range(off, off + n))
    for i in range(0x34):
        if i not in keep:
            want[i] = got[i]
    mem = dict(e[4])
    mem[MD] = bytes(want)
    return e[:4] + (mem,) + e[5:]


# =============================================================================================== spiral (do 16)
@family("spiral")
def spiral(rnd, game):
    cases, exp = [], []
    for k in range(1500):
        c = Case(FN["do16"])
        cls = rnd.randrange(NREC)
        invalid = rnd.random() < 0.04
        if invalid:
            cls = rnd.choice([NREC, -1])
        st = put_missile(c, rnd, cls)
        p1 = rnd.choice([6, rnd.randint(-5, 40), rnd.getrandbits(32)])
        p2 = rnd.choice([2, 1, 3, 0, -2, rnd.randint(-10, 10)])
        if not invalid:
            put_rec(c, rnd, cls, p1=p1, p2=p2)
        rng_ = rnd.choice([25, rnd.randint(0, 40), rnd.getrandbits(16)])
        left = rnd.choice([rnd.randint(0, 25), rnd.getrandbits(16)])
        a = rnd.choice([rnd.randint(-40, 40), rnd.getrandbits(32), 0x7FFFFFFF, 0x80000000])
        b = rnd.choice([rnd.randint(-40, 40), rnd.getrandbits(32), 0x7FFFFFFF, 0x80000000])
        md = put_mdata(c, rnd, range=rng_, left=left, w28=a, w2c=b)
        tgt = rnd.getrandbits(32)
        c.put(MP + 0x10, le32(tgt))
        c.put(MP + 0x58, le32(rnd.getrandbits(32)))
        cases += c.lines(game, MU, extra_dumps=[(MP + 0x10, 4), (MP + 0x58, 4)])
        exp.append([invalid, p1, p2, st, md, tgt])
    return cases, mem_spec(), {"cases": exp}


def spiral_model(invalid, p1, p2, st, md, tgt, game, br, neg=False):
    if invalid:
        br["ret2"] += 1
        return ("ret", 2, 0)
    step = p2 if p2 >= 1 else 1
    el = s16(md["range"]) - s16(md["left"])
    if not (el < s32(p1) and cmod(el, step) == 0):
        br["move"] += 1
        return obs_move(game)
    a, b = s32(md["w28"]), s32(md["w2c"])
    na = cdiv(s32(a - b), 2) if not neg else s32(a - b) >> 1
    nb = cdiv(s32(a + b), 2) if not neg else s32(a + b) >> 1
    br["turn"] += 1
    br["odd_negative"] += (s32(a - b) < 0 and (a - b) & 1) or (s32(a + b) < 0 and (a + b) & 1)
    px = (st["x"] + na) & 0xFFFF
    py = (st["y"] + nb) & 0xFFFF
    return ("obs", "PathPlan", {"edi": na, "ebx": nb}, [MP, MU, 0],
            {MP + 0x10: le16(px) + le16(py), MP + 0x58: le32(0)}, {})


def spiral_check(d, meta, calls, game):
    rep = Report("spiral")
    neg = 0
    for c, row in zip(calls, meta["cases"]):
        br = collections.Counter()
        if compare(rep, c, spiral_model(*row, game, br), br):
            r2 = Report("neg")
            compare(r2, c, spiral_model(*row, game, collections.Counter(), neg=True), {})
            neg += r2.c["bad"]
    return rep, neg, []


# =============================================================================================== scatter (8, 10, 17)
def rangeb(lo, hi, n):
    """RNG_RangeB: n <= 0 -> 0 and no step; a power of two -> low & (n - 1); else low % n."""
    n = s32(n)
    if n <= 0:
        return 0, lo, hi
    lo, hi = RNG.step(lo, hi)
    if n & (n - 1) == 0:
        return lo & (n - 1), lo, hi
    return lo % n, lo, hi


def near_model(c_own, st, md, period, r, cls, mask, game, room, br, neg=False):
    """sub_005A9820_MissSubNearReseed(EAX period, ESI missile; game, r, cls, mask) up to COLL_CellTestAt.
    -> None (returned 0) or the observation."""
    period = s32(period)
    if period == 0:
        br["near_period0"] += 1
        return None
    el = s16(md["range"]) - s16(md["left"])
    if cmod(el, period) != 0:
        br["near_offbeat"] += 1
        return None
    if not c_own:
        br["near_noowner"] += 1
        return None
    if not room:
        br["near_noroom"] += 1
        return None
    lo, hi = (st["x"] + el) & M32, 666
    if neg:
        lo = st["x"] & M32
    r1 = s32(r - 1)
    n = s32(2 * r1)
    dx, lo, hi = rangeb(lo, hi, n)
    dy, lo, hi = rangeb(lo, hi, n)
    br["near_draws%d" % (0 if n <= 0 else 2)] += 1
    x = s32(st["x"] + s32(dx - r1))
    y = s32(st["y"] + s32(dy - r1))
    return ("obs", "CellTestAt", {}, [room, x, y, mask], {MU + 0x20: le32(lo) + le32(hi)}, {})


@family("scatter")
def scatter(rnd, game):
    cases, exp = [], []
    for k in range(2400):
        which = ("do8", "do10", "do17")[k % 3]
        c = Case(FN[which])
        cls = rnd.randrange(NREC)
        room = rnd.choice([0x13000000 + 0x100 * rnd.randrange(16)] * 12 + [0])
        st = put_missile(c, rnd, cls, room=room)
        own = put_owner(c, rnd, present_p=0.9)
        sub = rnd.choice([rnd.randrange(700)] * 8 + [-1, 0, -0x8000])
        rng_ = rnd.choice([rnd.randint(0, 300), rnd.getrandbits(16)])
        left = rnd.choice([rnd.randint(0, 300), rnd.getrandbits(16)])
        lvl = small(rnd, 0, 60)
        seed0 = (rnd.getrandbits(32), rnd.getrandbits(32))
        c.put(MU + 0x20, le32(seed0[0]) + le32(seed0[1]))
        row = {"which": which, "cls": cls, "room": room, "st": st, "own": own, "sub": sub}
        if which == "do8":
            p1, p2, p3 = rnd.choice([5, rnd.randint(-5, 20)]), rnd.choice([8, rnd.randint(-5, 20)]), \
                rnd.choice([4, rnd.randint(-3, 10), 0])
            put_rec(c, rnd, cls, sub=sub, p1=p1, p2=p2, p3=p3)
            row.update(p1=p1, p2=p2, p3=p3)
            md = put_mdata(c, rnd, skill=small(rnd, 0, 300), lvl=lvl, range=rng_, left=left)
        elif which == "do10":
            skill = rnd.choice([rnd.randrange(NSREC)] * 10 + [NSREC, -1, 0x7FFF])
            md = put_mdata(c, rnd, skill=skill, lvl=lvl, range=rng_, left=left)
            put_rec(c, rnd, cls, sub=sub)
            # the skill's calc1 (radius) and calc2 (period): constant programs `09 <s32> 00` in a pool
            vals = [rnd.choice([rnd.randint(-3, 12), 1, 0, rnd.getrandbits(32)]) for _ in range(2)]
            pool = b"".join(b"\x09" + le32(v) + b"\x00" for v in vals)
            offs = [0, 6]
            if rnd.random() < 0.08:
                offs[rnd.randrange(2)] = rnd.choice([len(pool), 0xFFFFFFFF])
            c.put(SPOOL, pool)
            if 0 <= s16(skill) < NSREC:
                sbase = SREC + 0x23C * s16(skill)
                c.put(sbase + 0x138, le32(offs[0]))
                c.put(sbase + 0x13C, le32(offs[1]))
            c.put(DT + 0x44, le32(len(pool)))
            row.update(vals=vals, offs=offs, pool=len(pool))
        else:
            p1 = rnd.choice([40, rnd.randint(-5, 120)])
            p2 = rnd.choice([2, rnd.randint(-3, 6), 0])
            p3 = rnd.choice([17, rnd.randint(-3, 30), 1, 0])
            p4 = rnd.choice([38, -1, rnd.randint(-3, 130)])
            p5 = rnd.choice([100, rnd.randint(-5, 200)])
            mrange = rnd.choice([300, rnd.randint(0, 400), rnd.getrandbits(16)])
            put_rec(c, rnd, cls, sub=sub, p1=p1, p2=p2, p3=p3, p4=p4, p5=p5, range=mrange)
            w28 = rnd.choice([0, 0, 1, rnd.getrandbits(32)])
            md = put_mdata(c, rnd, skill=small(rnd, 0, 300), lvl=lvl, range=rng_, left=left, w28=w28)
            row.update(p1=p1, p2=p2, p3=p3, p4=p4, p5=p5, mrange=mrange)
        row["md"] = md
        row["seed0"] = seed0
        cases += c.lines(game, MU)
        exp.append(row)
    extra = ["dword %08x %08x" % (DT + 0xB98, SREC), "dword %08x %08x" % (DT + 0xBA0, NSREC),
             "dword %08x %08x" % (DT + 0x40, SPOOL)]
    return cases, mem_spec(extra), {"cases": exp}


def scatter_model(row, game, br, neg=False):
    w = row["which"]
    st, md, own = row["st"], row["md"], row["own"]
    br[w] += 1
    if w == "do8":
        lvl = s16(md["lvl"])
        dd = row["p3"] if row["p3"] >= 1 else 1
        q = cdiv(lvl, dd)
        a = q if q >= 2 else 2
        r = s32(row["p1"] + a)
        period = s32(row["p2"] - q)
        period = period if period >= 3 else 3
        o = near_model(own, st, md, period, r, row["sub"], 5, game, row["room"], br, neg)
        return o if o else obs_move(game)
    if w == "do10":
        skill = s16(md["skill"])
        if skill < 0 or skill >= NSREC:
            br["skill_invalid"] += 1
            return ("ret", 2, 0)

        def ev(i):
            off = row["offs"][i] & M32
            if off >= row["pool"]:
                br["calc_out"] += 1
                return 0
            return s32(row["vals"][off // 6])
        r, period = ev(0), ev(1)
        if neg:
            r, period = period, r
        o = near_model(own, st, md, period, r, row["sub"], 5, game, row["room"], br)
        return o if o else obs_move(game)
    left = s16(md["left"])
    p1 = s32(row["p1"])
    if row["sub"] > 0 and left < s16(row["mrange"]) - p1 and left > p1:
        br["window"] += 1
        o = near_model(own, st, md, row["p2"], row["p3"], row["sub"], 5, game, row["room"], br)
        if o:
            return o
    if row["p4"] >= 0 and md["w28"] == 0 and left <= s32(row["p5"] + p1) + (1 if neg else 0):
        br["portal"] += 1
        return ("obs", "PermPortalAtUnit", {"ecx": game, "edx": MU}, [row["p4"]], {}, {})
    return obs_move(game)


def scatter_check(d, meta, calls, game):
    rep = Report("scatter")
    neg = 0
    for c, row in zip(calls, meta["cases"]):
        br = collections.Counter()
        if compare(rep, c, scatter_model(row, game, br), br):
            r2 = Report("neg")
            compare(r2, c, scatter_model(row, game, collections.Counter(), neg=True), {})
            neg += r2.c["bad"]
    return rep, neg, [RS_HASH, RS_SKN, RS_CALC_JT]


# =============================================================================================== chest (do 18)
@family("chest")
def chest(rnd, game):
    cases, exp = [], []
    for k in range(1500):
        c = Case(FN["do18"])
        cls = rnd.randrange(NREC)
        room = rnd.choice([0x13000000 + 0x100 * rnd.randrange(16)] * 10 + [0])
        st = put_missile(c, rnd, cls, room=room)
        p1 = rnd.choice([150, rnd.randint(-5, 400)])
        p2 = rnd.choice([2, rnd.randint(-3, 5), 0, 0x40000000])
        p3 = rnd.choice([5, rnd.randint(-3, 12), 0, 1])
        mrange = rnd.choice([400, rnd.randint(0, 500)])
        put_rec(c, rnd, cls, p1=p1, p2=p2, p3=p3, range=mrange)
        guid = rnd.getrandbits(32)
        found = rnd.random() < 0.7
        if found:
            put_unit_found(c, rnd, OBJ, 2, guid, decoy=(guid ^ 0x100) if rnd.random() < 0.3 else None)
            c.put(OBJ + 0x04, le32(rnd.getrandbits(16)))
        else:
            put_unit_absent(c, rnd, 2, guid)
        r = rnd.random()
        if r < 0.2:
            left = 1
        elif r < 0.45:
            left = s16(mrange - p1) & 0xFFFF
        else:
            left = rnd.choice([rnd.randint(0, 400), rnd.getrandbits(16)])
        w2c = rnd.choice([0, 1, rnd.getrandbits(32)])
        md = put_mdata(c, rnd, left=left, w28=guid, w2c=w2c)
        seed0 = (rnd.getrandbits(32), rnd.getrandbits(32))
        c.put(MU + 0x20, le32(seed0[0]) + le32(seed0[1]))
        cases += c.lines(game, MU)
        exp.append({"room": room, "st": st, "p1": p1, "p2": p2, "p3": p3, "mrange": mrange, "guid": guid,
                    "found": found, "md": md, "seed0": seed0, "objcls": struct.unpack("<I", c.fields[OBJ + 4])[0]
                    if found else 0})
    return cases, mem_spec(), {"cases": exp}


def chest_model(row, game, br, neg=False):
    md = row["md"]
    left = s16(md["left"])
    if left == 1 and row["found"]:
        br["left1_event"] += 1
        return ("obs", "UnitSetEvent", {"ecx": OBJ, "edx": 0x5C}, [0], {}, {})
    w2c = md["w2c"]
    if left == s16(row["mrange"]) - s32(row["p1"]):
        if row["found"]:
            br["open_drop"] += 1
            want = le32(game) + le32(OBJ) + le32(0) + le32(OBJ + 0x20) + le32(row["objcls"])
            return ("obs", "ChestDrop", {}, [], {}, {"ecx": (0, want)})
        br["open_notfound"] += 1
        w2c = 1
    if w2c == 0:
        br["idle"] += 1
        return obs_move(game)
    period = s32(row["p2"] * 4)
    period = period if period >= 1 else 1
    if cmod(left, period) != 0:
        br["offbeat"] += 1
        return obs_move(game)
    r = s32(row["p3"])
    lo, hi = row["seed0"]
    n = s32(2 * r + 1)
    dx, lo, hi = rangeb(lo, hi, n)
    dy, lo, hi = rangeb(lo, hi, n)
    if neg:
        dx, dy = dy, dx
    br["drop_draws"] += 1
    x = s32(row["st"]["x"] + s32(dx - r))
    y = s32(row["st"]["y"] + s32(dy - r))
    return ("obs", "FreeSpot", {"ecx": row["room"]}, [None, 1, 1], {MU + 0x20: le32(lo) + le32(hi)},
            {"edx": (0, le32(x) + le32(y))})


def chest_check(d, meta, calls, game):
    rep = Report("chest")
    neg = 0
    for c, row in zip(calls, meta["cases"]):
        br = collections.Counter()
        if compare(rep, c, chest_model(row, game, br), br):
            r2 = Report("neg")
            compare(r2, c, chest_model(row, game, collections.Counter(), neg=True), {})
            neg += r2.c["bad"]
    return rep, neg, [RS_HASH, RS_COOKIE]


# =============================================================================================== homing (do 11)
def put_target_link(c, rnd, unit, path, tgt, tgtpath):
    """unit's path +0x58 = tgt (found by type/guid), or 0. -> the unit UNIT_GetTargetUnit returns."""
    c.put(unit + 0x2C, le32(path))
    k = rnd.random()
    if k < 0.25:
        c.put(path + 0x58, le32(0))
        return 0
    if k < 0.32:      # the unit itself: UNIT_GetTargetUnit returns 0
        typ, guid = 3, rnd.getrandbits(32)
        c.put(path + 0x58, le32(unit))
        c.put(path + 0x5C, le32(typ))
        c.put(path + 0x60, le32(guid))
        put_unit_found(c, rnd, unit, typ, guid)
        c.put(unit + 0x00, le32(3))
        c.put(unit + 0x10, le32(rnd.getrandbits(32)))
        return 0
    typ, guid = 3, rnd.getrandbits(32)
    c.put(path + 0x58, le32(tgt))
    c.put(path + 0x5C, le32(typ))
    c.put(path + 0x60, le32(guid))
    put_unit_found(c, rnd, tgt, typ, guid)
    c.put(tgt + 0x00, le32(3))
    c.put(tgt + 0x10, le32(rnd.getrandbits(32)))
    c.put(tgt + 0x2C, le32(tgtpath))
    return tgt


@family("homing")
def homing(rnd, game):
    cases, exp = [], []
    for k in range(1500):
        c = Case(FN["do11"])
        cls = rnd.randrange(NREC)
        tcls = rnd.randrange(NREC)
        st = put_missile(c, rnd, cls)
        c.put(MU + 0x10, le32(rnd.getrandbits(32)))
        sizes = [rnd.choice([1, 2, 3, 0, rnd.getrandbits(8)]) for _ in range(NREC)]
        p1 = rnd.choice([5, rnd.randint(-3, 10)])
        p2 = rnd.choice([20, rnd.randint(-5, 60)])
        p3 = rnd.choice([2, rnd.randint(-3, 6)])
        for i in range(NREC):
            put_rec(c, rnd, i, size=sizes[i])
        put_rec(c, rnd, cls, p1=p1, p2=p2, p3=p3)
        own = put_owner(c, rnd, present_p=0.85, types=(1,))
        t = put_target_link(c, rnd, MU, MP, TGT, TGTP)
        via_owner = False
        if not t and own:
            c.put(OWN + 0x00, le32(1))
            t = put_target_link(c, rnd, OWN, OWNP, TGT, TGTP)
            via_owner = bool(t)
        tst = None
        if t:
            c.put(TGT + 0x04, le32(tcls))
            near = rnd.random() < 0.6
            tx = (st["x"] + (rnd.randint(-12, 12) if near else rnd.randint(-200, 200))) & 0xFFFF
            ty = (st["y"] + (rnd.randint(-12, 12) if near else rnd.randint(-200, 200))) & 0xFFFF
            if rnd.random() < 0.1:
                tx = st["x"]
            if rnd.random() < 0.1:
                ty = st["y"]
            c.put(TGTP + 0x02, le16(tx))
            c.put(TGTP + 0x06, le16(ty))
            tst = {"x": tx, "y": ty}
        left = rnd.choice([rnd.randint(0, 80), rnd.getrandbits(16)])
        md = put_mdata(c, rnd, left=left)
        c.put(MP + 0x10, le32(rnd.getrandbits(32)))
        cases += c.lines(game, MU, extra_dumps=[(MP + 0x10, 4), (MP + 0x58, 4)])
        exp.append({"cls": cls, "tcls": tcls, "sizes": sizes, "p1": p1, "p2": p2, "p3": p3, "st": st, "t": t,
                    "tst": tst, "md": md, "via_owner": via_owner, "own": own})
    return cases, mem_spec(), {"cases": exp}


def homing_model(row, game, br, neg=False):
    if not row["t"]:
        br["no_target"] += 1
        return obs_move(game)
    br["via_owner"] += row["via_owner"]
    period = row["p1"] if row["p1"] >= 1 else 5
    if cmod(s16(row["md"]["left"]), period) != 0:
        br["offbeat"] += 1
        return obs_move(game)
    st, tst = row["st"], row["tst"]
    dx, dy = abs(tst["x"] - st["x"]), abs(tst["y"] - st["y"])
    s1, s2 = row["sizes"][row["cls"]], row["sizes"][row["tcls"]]
    adj = -cdiv(s2, 2) - cdiv(s1, 2)
    if not neg:          # the negative control leaves the two half sizes out
        dx, dy = max(dx + adj, 0), max(dy + adj, 0)
    dist = cdiv(dy + 2 * dx, 2) if dx > dy else cdiv(dx + 2 * dy, 2)
    if dist > row["p2"]:
        br["far"] += 1
        return obs_move(game)
    s = row["p3"] if row["p3"] >= 1 else 1
    sx = s if tst["x"] > st["x"] else (-s if tst["x"] < st["x"] else 0)
    sy = s if tst["y"] > st["y"] else (-s if tst["y"] < st["y"] else 0)
    br["step"] += 1
    br["step_axis0"] += (sx == 0) or (sy == 0)
    px, py = (st["x"] + sx) & 0xFFFF, (st["y"] + sy) & 0xFFFF
    return ("obs", "PathPlan", {}, [MP, MU, 0], {MP + 0x10: le16(px) + le16(py), MP + 0x58: le32(0)}, {})


def homing_check(d, meta, calls, game):
    rep = Report("homing")
    neg = 0
    for c, row in zip(calls, meta["cases"]):
        br = collections.Counter()
        if compare(rep, c, homing_model(row, game, br), br):
            r2 = Report("neg")
            compare(r2, c, homing_model(row, game, collections.Counter(), neg=True), {})
            neg += r2.c["bad"]
    return rep, neg, [RS_HASH, RS_SIZE_JT]


# =============================================================================================== periodic (do 14)
@family("periodic")
def periodic(rnd, game):
    cases, exp = [], []
    for k in range(1200):
        c = Case(FN["do14"])
        cls = rnd.randrange(NREC)
        invalid = rnd.random() < 0.04
        if invalid:
            cls = rnd.choice([NREC, -1])
        put_missile(c, rnd, cls)
        p1 = rnd.choice([6, rnd.randint(-3, 12), 0])
        p2 = rnd.choice([30, rnd.randint(0, 200), rnd.getrandbits(32)])
        if not invalid:
            put_rec(c, rnd, cls, p1=p1, p2=p2)
        md = put_mdata(c, rnd, skill=small(rnd, -3, 300), lvl=small(rnd, -3, 40),
                       range=rnd.choice([200, rnd.randint(0, 300)]), left=rnd.randint(0, 300))
        cases += c.lines(game, MU)
        exp.append([invalid, p1, p2, md])
    return cases, mem_spec(), {"cases": exp}


def periodic_model(invalid, p1, p2, md, game, br, neg=False):
    if invalid:
        br["ret2_rec"] += 1
        return ("ret", 2, 0)
    period = p1 if p1 > 0 else 1
    el = s16(md["range"]) - s16(md["left"])
    if cmod(el, period) != 0:
        br["move"] += 1
        return obs_move(game)
    sk, lv = s16(md["skill"]), s16(md["lvl"])
    if sk > 0 and (lv > 0 or neg):
        br["calldo"] += 1
        return ("obs", "CallDoFunc", {"ecx": game, "edx": MU}, [p2, sk, lv], {}, {})
    br["ret2_skill"] += 1
    return ("ret", 2, 0)


def periodic_check(d, meta, calls, game):
    rep = Report("periodic")
    neg = 0
    for c, row in zip(calls, meta["cases"]):
        br = collections.Counter()
        if compare(rep, c, periodic_model(*row, game, br), br):
            r2 = Report("neg")
            compare(r2, c, periodic_model(*row, game, collections.Counter(), neg=True), {})
            neg += r2.c["bad"]
    return rep, neg, []


# =============================================================================================== sublob (do 2)
@family("sublob")
def sublob(rnd, game):
    cases, exp = [], []
    for k in range(1200):
        c = Case(FN["do2"])
        cls = rnd.randrange(NREC)
        st = put_missile(c, rnd, cls)
        sub = rnd.choice([rnd.randrange(700)] * 8 + [-1, -0x8000])
        val = rnd.choice([rnd.randint(-3, 5), 0, 1, rnd.getrandbits(32)])
        pool = b"\x09" + le32(val) + b"\x00"
        off = rnd.choice([0] * 10 + [len(pool), 0xFFFFFFFF])
        put_rec(c, rnd, cls, sub=sub, calc=off)
        c.put(MPOOL, pool)
        c.put(DT + 0x64, le32(len(pool)))
        own = put_owner(c, rnd, present_p=0.85)
        flag = rnd.getrandbits(32) | 8 if rnd.random() < 0.6 else rnd.getrandbits(32) & ~8
        c.put(MP + 0x34, le32(flag))
        md = put_mdata(c, rnd, skill=small(rnd, 0, 300), lvl=small(rnd, -3, 40))
        cases += c.lines(game, MU)
        exp.append({"sub": sub, "val": val, "off": off, "pool": len(pool), "own": own, "flag": flag, "st": st,
                    "md": md})
    return cases, mem_spec(["dword %08x %08x" % (DT + 0x60, MPOOL)]), {"cases": exp}


def sublob_model(row, game, br, neg=False):
    if row["sub"] < 0:
        br["nosub"] += 1
        return obs_move(game)
    v = s32(row["val"]) if (row["off"] & M32) < row["pool"] else 0
    br["calc_out"] += (row["off"] & M32) >= row["pool"]
    if not row["flag"] & 8:
        br["noflag"] += 1
        return obs_move(game)
    if not row["own"]:
        br["noowner"] += 1
        return obs_move(game)
    lvl = s16(row["md"]["lvl"])
    flags = 5
    loops = s32(2 * lvl - 2)          # written whether or not flag 8 is set (0x005A97FD)
    if v > 0 or (neg and v >= 0):
        flags |= 8
        br["loops"] += 1
    else:
        br["noloops"] += 1
    blk = block(flags=flags, owner=row["own"], source=MU, cls=row["sub"], x=row["st"]["x"], y=row["st"]["y"],
                skill=s16(row["md"]["skill"]), lvl=lvl, loops=loops)
    return obs_create(game, blk)


def sublob_check(d, meta, calls, game):
    rep = Report("sublob")
    neg = 0
    for c, row in zip(calls, meta["cases"]):
        br = collections.Counter()
        if compare(rep, c, sublob_model(row, game, br), br):
            r2 = Report("neg")
            compare(r2, c, sublob_model(row, game, collections.Counter(), neg=True), {})
            neg += r2.c["bad"]
    return rep, neg, [RS_HASH, RS_MSN, RS_CALC_JT]


# =============================================================================================== guided (do 7)
ROOM, RLEV, LEVEL = 0x13000000, 0x13100000, 0x13200000


def is_town(lid):
    """sub_006426A0 (the town test RoomIsTown ends in) read from the image: byte table 0x006426C8, jumps 0x006426C0."""
    i = (lid - 1) & M32
    if i > 0x6C:
        return 0
    b = S4.image()[0][S4.va_off(0x006426C8 + i)]
    return int(S4.dword(0x006426C0 + 4 * b) == 0x006426B6)


@family("guided")
def guided(rnd, game):
    cases, exp = [], []
    for k in range(1200):
        c = Case(FN["do7"])
        cls = rnd.randrange(NREC)
        invalid = rnd.random() < 0.04
        if invalid:
            cls = rnd.choice([NREC, -1])
        room = rnd.choice([ROOM] * 12 + [0])
        put_missile(c, rnd, cls, room=room)
        p1 = rnd.choice([5, rnd.randint(-3, 10), 0])
        if not invalid:
            put_rec(c, rnd, cls, p1=p1)
        own = put_owner(c, rnd, present_p=0.85)
        dead = None
        if own:
            otyp = struct.unpack("<I", c.fields[MU + 0x94])[0]
            c.put(OWN + 0x00, le32(otyp))
            c6 = rnd.getrandbits(8) & ~1 if rnd.random() < 0.85 else 1
            mode = rnd.choice([rnd.randrange(1, 20)] * 6 + [0, 0x11 if otyp == 0 else 0xC])
            c.put(OWN + 0xC6, bytes([c6]))
            if not c6 & 1:
                c.put(OWN + 0x10, le32(mode))
            dead = int(bool(c6 & 1) or mode == 0 or mode == (0x11 if otyp == 0 else 0xC))
        lid = None
        if room:
            lid = rnd.choice([1, 40, 75, 103, 109, rnd.randint(0, 140), rnd.randint(2, 39)])
            c.put(ROOM + 0x10, le32(RLEV))
            c.put(RLEV + 0x58, le32(LEVEL))
            c.put(LEVEL + 0x1D0, le32(lid))
        w28 = rnd.getrandbits(32)
        md = put_mdata(c, rnd, w28=w28, left=rnd.randint(0, 200))
        t = put_target_link(c, rnd, MU, MP, TGT, TGTP)    # a missile target: UnitIsDead returns 1 for type 3
        if t:
            c.put(TGT + 0xC6, bytes([rnd.getrandbits(8)]))
        cases += c.lines(game, MU)
        exp.append({"invalid": invalid, "own": own, "dead": dead, "room": room, "lid": lid, "w28": w28, "t": t})
    return cases, mem_spec(), {"cases": exp}


def guided_model(row, game, br, neg=False):
    if row["invalid"] or not row["own"]:
        br["ret2_noowner" if not row["invalid"] else "ret2_rec"] += 1
        return ("ret", 2, 0)
    if row["dead"] and not neg:
        br["ret2_ownerdead"] += 1
        return ("ret", 2, 0)
    if row["room"] and is_town(row["lid"]):
        br["ret2_town"] += 1
        return ("ret", 2, 0)
    br["bit0" if row["w28"] & 1 else "nobit0"] += 1
    br["target_missile"] += bool(row["t"]) and bool(row["w28"] & 1)
    return obs_move(game)


def guided_check(d, meta, calls, game):
    rep = Report("guided")
    neg = 0
    for c, row in zip(calls, meta["cases"]):
        br = collections.Counter()
        if compare(rep, c, guided_model(row, game, br), br):
            r2 = Report("neg")
            compare(r2, c, guided_model(row, game, collections.Counter(), neg=True), {})
            neg += r2.c["bad"]
    return rep, neg, [RS_HASH, RS_TOWN]


RS_TOWN = (0x006426C0, 0x006426C8 + 0x6D, "r", "town-level tables 0x006426C0/0x006426C8 (.text)")

CHECKS = {"guided": guided_check, "cellsub": cellsub_check, "orb": orb_check, "spiral": spiral_check, "scatter": scatter_check,
          "chest": chest_check, "homing": homing_check, "periodic": periodic_check, "sublob": sublob_check}


# ================================================================================================= commands
def cmd_cases(a):
    for fam in a.family or list(FAMILIES):
        rnd = random.Random("cat9a-" + fam)
        cases, mem, meta = FAMILIES[fam](rnd, GAME)
        os.makedirs(a.dir, exist_ok=True)
        with open(os.path.join(a.dir, fam + ".cases"), "w") as f:
            f.write("\n".join(cases) + "\n")
        with open(os.path.join(a.dir, fam + ".mem"), "w") as f:
            f.write("\n".join(mem) + "\n")
        with open(os.path.join(a.dir, fam + ".json"), "w") as f:
            json.dump(meta, f)
        print("CAT9A cases %s calls=%d mem_lines=%d" % (fam, sum(1 for c in cases if c.startswith("call")), len(mem)))
    return 0


def cmd_check(a):
    rc = 0
    for fam in a.family or list(FAMILIES):
        calls, reads, writes = read_out(os.path.join(a.dir, fam + ".out"))
        meta = json.load(open(os.path.join(a.dir, fam + ".json")))
        if len(calls) != len(meta["cases"]):
            print("CAT9A %s bad: %d calls in the output, %d cases" % (fam, len(calls), len(meta["cases"])))
            rc = 1
            continue
        rep, neg, declared = CHECKS[fam](a.dir, meta, calls, GAME)
        account(rep, reads, writes, declared)
        rep.c["neg"] = neg
        if neg == 0:
            rep.bad("negative control did not fail")
        print(rep.line())
        for n in rep.notes:
            print("  " + n)
        print("  outcomes: " + " ".join("%s=%d" % kv for kv in sorted(rep.br.items())))
        rc |= 1 if rep.c["bad"] else 0
    return rc


PINS = [  # (address, mnemonic, operand substring): the instructions the claims turn on (ADR-0015 (5))
    (0x005AF106, "and", "0x8000003f"), (0x005AF10B, "jns", ""), (0x005AF114, "neg", "eax"),
    (0x005AF12F, "and", "0x8000003f"), (0x005AF1E5, "cdq", ""), (0x005AF1F6, "sar", "edi,1"),
    (0x005AF1F8, "sar", "ebx,1"), (0x005A9827, "mov", "edi,eax"), (0x005A983D, "idiv", "edi"),
    (0x005A98B7, "lea", "edx,[eax+eax*1]"), (0x005AE8FD, "idiv", "ecx"), (0x005AE925, "push", "0x5"),
    (0x005AF436, "lea", "edx,[ebx+ebx*1+0x1]"), (0x005AF404, "add", "ecx,ecx"), (0x005AF0B7, "jle", ""),
    (0x005AF28E, "jle", ""), (0x005AEB3E, "call", "0x5a9820"), (0x005AF2B5, "call", "0x5a9820"),
]


def cmd_static(a):
    rep = Report("static")
    A = S4.asm()
    for va, mn, sub in PINS:
        ins = A.at(va)
        rep.c["pins"] += 1
        if ins is None or ins[0] != mn or sub not in ins[1]:
            rep.bad("pin 0x%08X: %r, want %s %s" % (va, ins, mn, sub))
        else:
            rep.c["pins_ok"] += 1
    # declared .data reads: no store in .text
    for lo, name in ((SK_NFUNCS, "skills calc function count"), (MS_NFUNCS, "missiles calc function count")):
        stores = []
        for va, (mn, ops) in A.ins.items():
            dst = ops.split(",")[0]
            if mn in ("mov", "add", "sub", "inc", "dec", "or", "and", "xor") and "PTR" in dst and \
                    ("ds:0x%x" % lo) in dst:
                stores.append((va, mn, ops))
        rep.c["data_stores"] += len(stores)
        rep.notes.append("%s 0x%08X: %d stores in .text" % (name, lo, len(stores)))
        for s in stores:
            rep.notes.append("  store 0x%08X %s %s" % s)
    for lo, name in ((HASH_OFF, "hash offsets"), (CIRCLE_X, "circle x"), (CIRCLE_Y, "circle y")):
        sec = S4.section_of(lo)
        flags = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.c["ro_reads"] += 1
        if flags & 0x80000000:
            rep.bad("%s 0x%08X in writable %s" % (name, lo, sec))
    xs = [s32(S4.dword(CIRCLE_X + 4 * i)) for i in range(64)]
    ys = [s32(S4.dword(CIRCLE_Y + 4 * i)) for i in range(64)]
    rep.notes.append("circle x: %s" % " ".join(map(str, xs)))
    rep.notes.append("circle y: %s" % " ".join(map(str, ys)))
    rep.notes.append("hash offsets: %s" % " ".join("0x%X" % S4.dword(HASH_OFF + 4 * i) for i in range(5)))
    rep.notes.append("do table 0..20: %s" % " ".join("%d:0x%08X" % (i, S4.dword(0x0073C768 + 4 * i))
                                                     for i in range(21)))
    print("CAT9A static " + " ".join("%s=%d" % (k, rep.c[k]) for k in sorted(rep.c)))
    for n in rep.notes:
        print("  " + n)
    return 1 if rep.c["bad"] else 0


def cmd_manifest(a):
    lines = []
    for root, _, files in sorted(os.walk(a.dir)):
        for f in sorted(files):
            if f == "manifest.sha256":
                continue
            p = os.path.join(root, f)
            lines.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.relpath(p, a.dir)))
    text = "\n".join(lines) + "\n"
    if a.write:
        open(os.path.join(a.dir, "manifest.sha256"), "w").write(text)
    print("CAT9A manifest files=%d sha256=%s" % (len(lines), hashlib.sha256(text.encode()).hexdigest()))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["cases", "check", "static", "manifest"])
    ap.add_argument("family", nargs="*")
    ap.add_argument("--dir", default=DEFDIR)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    return {"cases": cmd_cases, "check": cmd_check, "static": cmd_static, "manifest": cmd_manifest}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

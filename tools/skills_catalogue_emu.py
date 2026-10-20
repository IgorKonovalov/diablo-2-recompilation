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

Batch 9b (`--batch 9b`, files under workspace/logs/skills-cat-9b/, draws from random.Random("cat9b-<family>")):
  create9b  do 21, 22, 23, 26, 32 (one or two sub-missiles)      vines     do 20 (blade creeper)
  rabies    do 30 (contagion: draws on the target's seed)        reseed9b  do 28, 34, 35 (re-seeded missiles)
  scatter25 do 25 (through sub_005A9820)                         wake      do 31
  regen     do 29, 33 (owner life / mana; stat lists)            tornado   do 27 (up to MISSILE_BuildDamage)
  fx        do 19, 36                                            dmgconv   damage 1, 12 (EType conversion and roll)
  dmgelem   damage 5, 13                                         dmgpkt    damage 2, 3, 4, 7, 8, 9, 10, 11
  knock     damage 14
Every 9b model names the call site of each boundary (the return address at ESP, or SENTINEL for a tail jump) and
the checker fails a case reached from another one; a site control re-checks every matched boundary case with the
return address changed (each must fail), and each family runs two negative controls on different claims.

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


FAMILY_BATCH = {}


def family(name, batch="9a"):
    def deco(f):
        FAMILIES[name] = f
        FAMILY_BATCH[name] = batch
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

    def lines(self, ecx, edx, regs=None, extra_dumps=(), args=()):
        out = list(self.w)
        for r, v in (regs or {}).items():
            out.append("r %s %08x" % (r, v & M32))
        out.append("d %08x %d" % (STK_LO, STK_LEN))
        out.append("d %08x %d" % (MD, 0x34))
        out.append("d %08x 8" % (MU + 0x20))
        for a, n in extra_dumps:
            out.append("d %08x %d" % (a, n))
        out.append("call %08x %08x %08x" % (self.fn, ecx, edx) + "".join(" %08x" % (a & M32) for a in args))
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


def mem_spec(extra=(), bounds=None):
    lines = ["dword %08x %08x" % (G_PDATATABLES, DT),
             "dword %08x %08x" % (DT + 0xB64, MREC), "dword %08x %08x" % (DT + 0xB6C, NREC),
             "dword %08x 6b3a11f5" % COOKIE]
    lines += list(extra)
    lines += ["observe %08x" % a for a in sorted(BOUND if bounds is None else bounds)]
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
        self.batch = FAMILY_BATCH.get(fam, "9a").upper()
        self.c = collections.Counter()
        self.notes = []
        self.br = collections.Counter()

    def bad(self, why):
        self.c["bad"] += 1
        if self.c["bad"] <= 25:
            self.notes.append("BAD " + why)

    def line(self):
        keys = ["cases", "match", "bad", "neg", "traced", "undeclared", "stopped"]
        return "CAT%s %s " % (self.batch, self.fam) + " ".join("%s=%d" % (k, self.c[k]) for k in keys)


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
    """exp: ('ret', eax, pop[, {addr: bytes}]) or ('obs', name, {reg: value}, [arg values], {addr: bytes},
    {stack addr: bytes}[, site]). eax None: not compared (a void function). site: the return address at ESP when the
    boundary is reached (the call site + its length, or SENTINEL for a tail jump); batch 9b families give it always
    (ADR-0021 (b), lane/p46m1 review)."""
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
        elif (exp[1] is not None and (c["eax"] & M32) != (exp[1] & M32)) or c["pop"] != exp[2]:
            ok, why = False, "eax=%08x pop=%d want %s %d" % (c["eax"], c["pop"], "-" if exp[1] is None else
                                                            "%08x" % (exp[1] & M32), exp[2])
        else:
            for a, b in (exp[3] if len(exp) > 3 else {}).items():
                if c["dumps"].get(a) != b:
                    ok, why = False, "mem %08x=%s want %s" % (a, c["dumps"].get(a, b"").hex(), b.hex())
    else:
        _, name, regs, args, mem, stk = exp[:6]
        site = exp[6] if len(exp) > 6 else None
        if site is None and FAMILY_BATCH.get(rep.fam, "9a") != "9a" and rep.fam != "neg":
            ok, why = False, "model gives no call site for %s" % name
        if "obs" not in c:
            ok, why = False, "returned eax=%08x, want %s" % (c.get("eax", 0), name)
        elif c["obs"] != BOUND_BY_NAME[name]:
            ok, why = False, "observed %s, want %s" % (BOUND.get(c["obs"], hex(c["obs"])), name)
        elif site is not None and struct.unpack_from("<I", c["args"], 0)[0] != site:
            ok, why = False, "%s reached from return address %08x, want %08x" % (
                name, struct.unpack_from("<I", c["args"], 0)[0], site)
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


# ##################################################################################################################
# Batch 9b (plan 0046): missile server do functions 19-36 and damage functions 1-14. Same harness, with the call site
# of every observed boundary asserted (the return address at ESP, or SENTINEL for a tail jump: ADR-0021 (b), the
# lane/p46m1 review) and two negative controls per family (the 9a review: a control under 50 failures needs a second
# perturbation on another claim; here every family has two, and each must fail).
# ##################################################################################################################
SENTINEL = 0x7EEE0000            # EmuBoundary's return-address sentinel: a boundary reached by a tail jump sees it

FN9B = {
    "do19": 0x005B0940, "do20": 0x005AF540, "do21": 0x005AF590, "do22": 0x005AF620, "do23": 0x005AF790,
    "do25": 0x005AF880, "do26": 0x005AF980, "do27": 0x005AFA30, "do28": 0x005AFB80, "do29": 0x005AFD70,
    "do30": 0x005B0010, "do31": 0x005B01F0, "do32": 0x005B03E0, "do33": 0x005AFEC0, "do34": 0x005B04A0,
    "do35": 0x005B0640, "do36": 0x005B0A40,
    "dmg1": 0x005AD050, "dmg2": 0x005AD1B0, "dmg3": 0x005AD220, "dmg4": 0x005AD290, "dmg5": 0x005AD2F0,
    "dmg7": 0x005AD3E0, "dmg8": 0x005AD450, "dmg9": 0x005AD4A0, "dmg10": 0x005AD2B0, "dmg11": 0x005AD530,
    "dmg12": 0x005AD0F0, "dmg13": 0x005AD5C0, "dmg14": 0x005AD630,
}
BOUND9B = dict(BOUND)
BOUND9B.update({
    0x0056EDE0: "MissileCreateAt", 0x00650BE0: "PathToRoomXY", 0x005ADF10: "HitUnit", 0x005A89A0: "BuildDamage",
    0x00627260: "UnitSetStat", 0x00621E40: "OverlaySet", 0x005ADB00: "JustHitState", 0x0064EBA0: "SizeUnmark",
    0x005AE780: "Do07", 0x005AE480: "Do03", 0x005444B0: "QuestActive", 0x0056DDE0: "UnitsInRange",
})
DO20_ENTRY = {0x005AF540: "Do20"}            # observed only by the do-21 cases (its tail jump)
BOUND_BY_NAME.update({v: k for k, v in BOUND9B.items()})
BOUND_BY_NAME.update({v: k for k, v in DO20_ENTRY.items()})
ALLBOUND = dict(BOUND9B)
ALLBOUND.update(DO20_ENTRY)

PKT = 0x12250000                 # a DamagePacket (0x70 bytes, re/types/combat.h)
ISC = 0x12260000                 # ItemStatCost records (0x144)
NISC = 400
SLIST = {MU: 0x12400000, OWN: 0x12410000, TGT: 0x12420000}   # each unit's stat list (Unit+0x5C)
MSREC = 0x12500000               # MonStats records (0x1A8)
MS2REC = 0x12510000              # MonStats2 records (0x134)
NMON = 4
NMON2 = 4
FRAME = 0xA8                     # Game+0xA8, the server frame
BITMASK = 0x006CE268             # g_BitMask32 (.rdata): 1 << i for i = 0..31
RS_BITMASK = (BITMASK, BITMASK + 32, "r", "g_BitMask32 0x006CE268 (.rdata): StatListGetValue's ISC mask "
              "0x006CE270, do 31's Explosion mask 0x006CE26C, MonStats2FlagTest")
RS_JT8C70 = (0x005A8EE8, 0x005A8EE8 + 4 * 13, "r", "0x005A8C70's EType jump table 0x005A8EE8, 13 entries (.text)")
RS_JT91C0 = (0x005A9240, 0x005A9240 + 4 * 9, "r", "0x005A91C0's EType jump table 0x005A9240 (.text)")
RS_JT9270 = (0x005A9334, 0x005A9334 + 4 * 13, "r", "0x005A9270's EType jump table 0x005A9334 (.text)")


def u32f(c, a):
    return struct.unpack("<I", c.fields[a])[0]


def muldiv(a, b, c):
    """sub_00483360_MulDiv(a, b, c): tools/economy.py's model (signed 32-bit with its 64-bit escape)."""
    a, b, c = s32(a), s32(b), s32(c)
    if c == 0:
        return 0
    if a > 0x100000:
        if c > (a >> 4):
            return s32(cdiv(a * b, c))
        return s32(cdiv(a, c) * b)
    if b > 0x10000:
        if c > (b >> 4):
            return s32(cdiv(a * b, c))
        return s32(cdiv(b, c) * a)
    return cdiv(s32(a * b), c)


def rrange(lo, hi, n):
    """RNG_Range (tools/rng.py rng_range): n < 1 -> 0 and no step; else low % n after one step."""
    return RNG.rng_range(lo, hi, n & M32)


def el_of(md):
    return s16(md["range"]) - s16(md["left"])


def pick_cls(rnd, p=0.05):
    cls = rnd.randrange(NREC)
    if rnd.random() < p:
        return rnd.choice([NREC, NREC + 7, -1, -0x1000]), True
    return cls, False


def put_owner_state(c, rnd, present_p=0.85, types=(0, 1)):
    """put_owner, plus the fields UnitIsDead reads. -> (owner, dead)."""
    own = put_owner(c, rnd, present_p, types)
    if not own:
        return 0, None
    otyp = u32f(c, MU + 0x94)
    c.put(OWN + 0x00, le32(otyp))
    c6 = rnd.getrandbits(8) & ~1 if rnd.random() < 0.85 else (rnd.getrandbits(8) | 1)
    c.put(OWN + 0xC6, bytes([c6]))
    mode = rnd.choice([rnd.randrange(1, 20)] * 6 + [0, 0x11 if otyp == 0 else 0xC])
    if not c6 & 1:
        c.put(OWN + 0x10, le32(mode))
    dead = int(bool(c6 & 1) or mode == 0 or mode == (0x11 if otyp == 0 else 0xC))
    return own, dead


def put_owner_pos(c, rnd):
    """The owner's dynamic path: position (+0x02, +0x06) and room (+0x1C), for 0x005A99E0."""
    ox, oy, oroom = rnd.getrandbits(16), rnd.getrandbits(16), rnd.choice([0x13000000 + 0x100 * rnd.randrange(8), 0])
    c.put(OWN + 0x2C, le32(OWNP))
    c.put(OWNP + 0x02, le16(ox))
    c.put(OWNP + 0x06, le16(oy))
    c.put(OWNP + 0x1C, le32(oroom))
    return {"ox": ox, "oy": oy, "oroom": oroom}


def put_skill_calcs(c, rnd, skill, fields):
    """Constant calc programs `09 <s32> 00` in the skills pool; `fields` = Skills record offsets that hold one."""
    vals = [rnd.choice([rnd.randint(-3, 12), 1, 0, rnd.randint(-200, 300), rnd.getrandbits(32)]) for _ in fields]
    pool = b"".join(b"\x09" + le32(v) + b"\x00" for v in vals)
    offs = [6 * i for i in range(len(fields))]
    for i in range(len(offs)):
        if rnd.random() < 0.06:
            offs[i] = rnd.choice([len(pool), 0xFFFFFFFF])
    c.put(SPOOL, pool)
    c.put(DT + 0x44, le32(len(pool)))
    if 0 <= s16(skill) < NSREC:
        sbase = SREC + 0x23C * s16(skill)
        for f, o in zip(fields, offs):
            c.put(sbase + f, le32(o))
    return {"vals": vals, "offs": offs, "pool": len(pool), "fields": list(fields)}


def ev_skill(cal, field):
    i = cal["fields"].index(field)
    off = cal["offs"][i] & M32
    if off >= cal["pool"]:
        return 0
    return s32(cal["vals"][off // 6])


def skill_ok(md):
    return 0 <= s16(md["skill"]) < NSREC


def pick_skill(rnd):
    return rnd.choice([rnd.randrange(NSREC)] * 12 + [NSREC, -1, 0x7FFF])


def subxy(st):
    return (st["x"], st["y"]) if st["path"] else (0, 0)


def obs_move9(game, site, mem=None):
    return ("obs", "MoveCollide", {"ecx": game, "edx": MU}, [], mem or {}, {}, site)


def obs_create9(game, blk, site, mem=None):
    return ("obs", "MissileCreate", {"ecx": game}, [], mem or {}, {"edx": (0, blk)}, site)


def block9(**kw):
    """block() plus the fields 9b writes: +0x24 (do 28's Param5)."""
    w24 = kw.pop("w24", None)
    b = bytearray(block(**kw))
    if w24 is not None:
        struct.pack_into("<I", b, 0x24, w24 & M32)
    return bytes(b)


def mdbytes(md, **over):
    """The MissileData dump the model expects: the case's fields, with the named words replaced."""
    m = dict(md)
    m.update(over)
    return dump_md(m)


def masked9(e, md, c):
    """masked_md for both outcome kinds: compare only the MissileData bytes the case wrote or the model sets."""
    if e[0] == "obs":
        return masked_md(e, md, c)
    if len(e) < 4 or MD not in e[3] or MD not in c["dumps"]:
        return e
    fake = ("obs", "", {}, [], e[3], {})
    m = masked_md(fake, md, c)[4]
    return e[:3] + (m,) + e[4:]


def put_rec9(c, cls, **kw):
    """put_rec plus the 9b fields: b04 (+0x04 flag byte), sub2/sub3 (+0x1A, +0x1C), ovl (ProgOverlay +0x36 s16),
    dcalc (DmgCalc1 +0x90), dp1/dp2 (+0x78, +0x7C), etype (+0xE4 u8), ckill (+0x186), aexp (+0x18C)."""
    base = MREC + 0x1A4 * cls
    offs = {"sub": (0x18, 2), "sub2": (0x1A, 2), "sub3": (0x1C, 2), "ovl": (0x36, 2), "p1": (0x38, 4),
            "p2": (0x3C, 4), "p3": (0x40, 4), "p4": (0x44, 4), "p5": (0x48, 4), "dp1": (0x78, 4), "dp2": (0x7C, 4),
            "dcalc": (0x90, 4), "range": (0x96, 2), "size": (0x18A, 1), "b04": (0x04, 1), "etype": (0xE4, 1),
            "ckill": (0x186, 1), "aexp": (0x18C, 1)}
    for k, val in kw.items():
        off, n = offs[k]
        c.put(base + off, le16(val) if n == 2 else (bytes([val & 0xFF]) if n == 1 else le32(val)))
    return base


def mem9(extra=(), do20=False, isc=False, mons=False, skills=False, mpool=False):
    ex = list(extra)
    if skills:
        ex += ["dword %08x %08x" % (DT + 0xB98, SREC), "dword %08x %08x" % (DT + 0xBA0, NSREC),
               "dword %08x %08x" % (DT + 0x40, SPOOL)]
    if isc:
        ex += ["dword %08x %08x" % (DT + 0xBCC, ISC), "dword %08x %08x" % (DT + 0xBD4, NISC)]
    if mons:
        ex += ["dword %08x %08x" % (DT + 0xA78, MSREC), "dword %08x %08x" % (DT + 0xA80, NMON),
               "dword %08x %08x" % (DT + 0xA90, MS2REC), "dword %08x %08x" % (DT + 0xA98, NMON2)]
    if mpool:
        ex += ["dword %08x %08x" % (DT + 0x60, MPOOL)]
    b = dict(BOUND9B)
    if do20:
        b.update(DO20_ENTRY)
    return mem_spec(ex, bounds=b)


# ----------------------------------------------------------------------------------------------- stat lists
STATS_DMG = (21, 22, 25, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 62, 64, 66, 121, 122, 141, 315, 316, 317,
             326, 329, 330, 331, 332, 357)


def put_stats(c, rnd, unit, stats, p_nolist=0.04):
    """unit+0x5C -> a stat list holding {stat: value} at layer 0 (plus decoys at layer 1), sorted by key
    (stat << 16 | layer); the array and count at +0x24/+0x28, or +0x48/+0x4C when +0x10 bit 31 is set.
    -> {stat: value} as STATS_GetUnitStat(unit, stat, 0) reads it (0 when absent)."""
    if rnd.random() < p_nolist:
        c.put(unit + 0x5C, le32(0))
        return {}
    sl = SLIST[unit]
    c.put(unit + 0x5C, le32(sl))
    flags = rnd.getrandbits(32)
    ao, co = (0x48, 0x4C) if flags & 0x80000000 else (0x24, 0x28)
    keys = {}
    for s, v in stats.items():
        if v is None:
            continue
        keys[(s << 16)] = v & M32
        if rnd.random() < 0.15:
            keys[(s << 16) | 1] = rnd.getrandbits(32)
    for _ in range(rnd.randrange(3)):
        k = (rnd.randrange(1, 511) << 16)
        if k not in keys and (k >> 16) not in stats:
            keys[k] = rnd.getrandbits(32)
    ks = sorted(keys)
    arr = sl + 0x100
    c.put(sl + 0x10, le32(flags))
    c.put(sl + ao, le32(arr))
    c.put(sl + co, le16(len(ks)))
    for i, k in enumerate(ks):
        c.put(arr + 8 * i, le32(k) + le32(keys[k]))
    for k in ks:
        st = k >> 16
        if st < NISC:
            c.put(ISC + 0x144 * st + 5, b"\x00")      # no fMin floor (the branch is not reached)
    return {s: s32(v) for s, v in stats.items() if v is not None}


def stat_of(sv, s):
    return sv.get(s, 0) if sv is not None else 0


def rnd_stat(rnd):
    return rnd.choice([None, None, 0, rnd.randint(1, 40), rnd.randint(1, 500), rnd.randint(-20, 0),
                       rnd.getrandbits(32), rnd.randint(1, 3)])


# ----------------------------------------------------------------------------------------------- packets
ELEM_FIELD = {0: 0x08, 1: 0x10, 2: 0x1C, 3: 0x20, 4: 0x24, 5: 0x28, 6: 0x38, 7: 0x3C, 8: 0x40, 9: 0x44, 11: 0x14}


def pk_get(p, off):
    return struct.unpack_from("<i", p, off)[0]


def pk_set(p, off, v):
    struct.pack_into("<I", p, off, v & M32)


def add_elem(p, et, v):
    """0x005A9270: add v to the packet field of the missile's EType (12 sets the cold field; 10, 13+ nothing)."""
    if et == 12:
        pk_set(p, 0x24, v)
    elif et in ELEM_FIELD:
        pk_set(p, ELEM_FIELD[et], s32(pk_get(p, ELEM_FIELD[et]) + v))


def zero_elem(p, et, neg=None):
    """0x005A91C0: flags &= ~0x700, the damage fields cleared, the lengths by EType."""
    pk_set(p, 0, struct.unpack_from("<I", p, 0)[0] & 0xFFFFF8FF)
    for o in (0x08, 0x10, 0x1C, 0x20, 0x24, 0x28, 0x38, 0x3C, 0x40, 0x44, 0x14):
        pk_set(p, o, 0)
    if et in (4, 12):
        z = (0x2C, 0x18) if neg != "zero_all" else (0x2C, 0x18, 0x30)
    elif et == 5:
        z = (0x30, 0x34, 0x18)
    elif et == 11:
        z = (0x30, 0x2C, 0x34)
    else:
        z = (0x30, 0x34, 0x2C, 0x18)
    for o in z:
        pk_set(p, o, 0)


def elem_roll(sv, a, b, m, seed):
    """sub_005A8910_MissileElemRoll(EAX a; unit, b, m): both stats >= 1, ordered, the mastery m added through MulDiv,
    then RangeB(seed, hi - lo) + lo. -> (value, seed)."""
    hi = stat_of(sv, a)
    if hi < 1:
        return 0, seed
    lo = stat_of(sv, b)
    if lo <= 0:
        return 0, seed
    if lo > hi:
        lo, hi = hi, lo
    if m != -1:
        mv = stat_of(sv, m)
        if mv:
            lo = s32(lo + muldiv(lo, mv, 100))
            hi = s32(hi + muldiv(hi, mv, 100))
    r, l2, h2 = rangeb(seed[0], seed[1], s32(hi - lo))
    return s32(r + lo), (l2, h2)


def is_undead(row):
    return row["utype"] == 1 and 0 <= row["ucls"] < NMON and bool(row["mflags"][row["ucls"]] & 0x18)


def is_demon(row):
    return row["utype"] == 1 and 0 <= row["ucls"] < NMON and bool(row["mflags"][row["ucls"]] & 0x20)


def elem_8c70(p, et, row, sv, seed):
    """0x005A8C70 (ECX game, EDX missile; unit, packet): the roll of the missile's EType into the packet.
    -> (return value, seed)."""
    unit = row["unit"]
    if et == 0:
        v, seed = elem_roll(sv, 22, 21, -1, seed)
        pk_set(p, 0x08, v)
        if unit:
            pct = stat_of(sv, 25)
            if is_demon(row):
                pct = s32(pct + stat_of(sv, 121))
            if is_undead(row):
                pct = s32(pct + stat_of(sv, 122))
            if pct <= -90:
                pct = -90
            ph = pk_get(p, 0x08)
            pk_set(p, 0x08, s32(cdiv(s32(ph * pct), 100) + ph))
        if stat_of(sv, 141):
            struct.pack_into("<H", p, 4, struct.unpack_from("<H", p, 4)[0] | 0x2000)
            pk_set(p, 0x08, s32(pk_get(p, 0x08) * 2))
        return pk_get(p, 0x08), seed
    tab = {1: (49, 48, 329, 0x10), 2: (51, 50, 330, 0x1C), 3: (53, 52, 357, 0x20), 4: (55, 54, 331, 0x24),
           12: (55, 54, 331, 0x24), 5: (58, 57, 332, 0x28), 11: (317, 316, 329, 0x14)}
    if et in tab:
        a, b, m, off = tab[et]
        v, seed = elem_roll(sv, a, b, m, seed)
        pk_set(p, off, v)
        if et == 4:
            pk_set(p, 0x30, stat_of(sv, 56))
            return v, seed
        if et == 12:
            pk_set(p, 0x34, stat_of(sv, 56))
            return v, seed
        if et == 5:
            pk_set(p, 0x2C, stat_of(sv, 59))
            q = stat_of(sv, 326)
            if q > 1:
                pk_set(p, 0x2C, cdiv(pk_get(p, 0x2C), q))
            return s32(v * 25), seed
        if et == 11:
            pk_set(p, 0x18, stat_of(sv, 315))
            return s32(v * 25), seed
        return v, seed
    one = {6: (60, 0x38), 7: (62, 0x3C), 8: (64, 0x40), 9: (66, 0x44)}
    if et in one:
        s, off = one[et]
        pk_set(p, off, stat_of(sv, s))
    return 0, seed


def put_packet(c, rnd):
    p = bytearray(rnd.getrandbits(8) for _ in range(0x70))
    for off in (0x08, 0x10, 0x1C, 0x20, 0x24, 0x28, 0x2C, 0x30, 0x14, 0x18):
        if rnd.random() < 0.7:
            pk_set(p, off, rnd.choice([rnd.randint(-50, 3000), rnd.randint(0, 100), 0]))
    c.put(PKT, bytes(p))
    return bytes(p)


def put_target_unit(c, rnd):
    """The damage functions' unit argument: 0, a player, a monster of a MonStats class, or another type."""
    k = rnd.random()
    if k < 0.08:
        return {"unit": 0, "utype": None, "ucls": None}
    utype = rnd.choice([1, 1, 1, 0, 0, rnd.randrange(2, 6)])
    c.put(TGT + 0x00, le32(utype))
    ucls = rnd.choice([rnd.randrange(NMON)] * 8 + [NMON, -1])
    c.put(TGT + 0x04, le32(ucls))
    return {"unit": TGT, "utype": utype, "ucls": ucls}


def put_monstats(c, rnd, row):
    """MonStats +0x0D flag byte (undead 0x08/0x10, demon 0x20) and +0x18 (the MonStats2 index), MonStats2 +0x05
    (small bit 2, large bit 3), one record each per class."""
    mflags = [rnd.getrandbits(8) for _ in range(NMON)]
    m2i = [rnd.choice([rnd.randrange(NMON2)] * 6 + [NMON2, -1]) for _ in range(NMON)]
    m2f = [rnd.getrandbits(8) for _ in range(NMON2)]
    for i in range(NMON):
        c.put(MSREC + 0x1A8 * i + 0x0D, bytes([mflags[i]]))
        c.put(MSREC + 0x1A8 * i + 0x18, le16(m2i[i]))
    for i in range(NMON2):
        c.put(MS2REC + 0x134 * i + 0x05, bytes([m2f[i]]))
    row.update(mflags=mflags, m2i=m2i, m2f=m2f)


def check9b(fam, model, negs, declared, md_masked=True):
    def chk(d, meta, calls, game):
        rep = Report(fam)
        negc = collections.Counter({n: 0 for n in negs})
        sites = collections.Counter()
        site_ctl = [0, 0]
        for c, row in zip(calls, meta["cases"]):
            br = collections.Counter()
            e = model(row, game, br)
            if md_masked and "md" in row:
                e = masked9(e, row["md"], c)
            if "obs" in c:
                sites[(c["fn"], ALLBOUND.get(c["obs"], hex(c["obs"])),
                       struct.unpack_from("<I", c["args"], 0)[0])] += 1
            if compare(rep, c, e, br):
                if e[0] == "obs":                  # the call-site assertion is live: a wrong site must fail
                    r3 = Report("neg")
                    compare(r3, c, e[:6] + ((e[6] ^ 0x10) & M32,), {})
                    site_ctl[0] += 1
                    site_ctl[1] += r3.c["bad"]
                for nm in negs:
                    e2 = model(row, game, collections.Counter(), neg=nm)
                    if md_masked and "md" in row:
                        e2 = masked9(e2, row["md"], c)
                    r2 = Report("neg")
                    compare(r2, c, e2, {})
                    negc[nm] += r2.c["bad"]
        rep.negs = negc
        for (fn, bname, ret), n in sorted(sites.items()):
            rep.notes.append("site fn=0x%08X boundary=%s return=0x%08X cases=%d" % (fn, bname, ret, n))
        rep.notes.append("site control: %d of %d matched boundary cases fail with the return address changed" %
                         (site_ctl[1], site_ctl[0]))
        if site_ctl[1] != site_ctl[0]:
            rep.bad("site control: the call-site assertion missed %d cases" % (site_ctl[0] - site_ctl[1]))
        for nm in negs:
            rep.notes.append("negative control %s: %d failures" % (nm, negc[nm]))
            if negc[nm] == 0:
                rep.bad("negative control %s did not fail" % nm)
        return rep, sum(negc.values()), declared
    return chk


def lines9(c, game, args=(), dumps=()):
    return c.lines(game, MU, extra_dumps=list(dumps), args=args)


# =============================================================================================== create9b
@family("create9b", "9b")
def create9b(rnd, game):
    cases, exp = [], []
    order = ("do21", "do22", "do23", "do26", "do32")
    for k in range(1500):
        w = order[k % 5]
        c = Case(FN9B[w])
        cls, invalid = pick_cls(rnd)
        has_path = rnd.random() > 0.08
        st = put_missile(c, rnd, cls, path=has_path)
        sub = rnd.choice([rnd.randrange(700)] * 6 + [0, -1, -0x8000, 0x7FFF])
        p1 = rnd.choice([3, 9, 0, 5, rnd.randint(-5, 20), rnd.getrandbits(32)])
        if not invalid:
            put_rec9(c, cls, sub=sub, p1=p1)
        own = put_owner(c, rnd)
        flag = rnd.getrandbits(32)
        flag = flag | 8 if rnd.random() < 0.55 else flag & ~8
        if has_path:
            c.put(MP + 0x34, le32(flag))
        rng_ = rnd.choice([rnd.randint(0, 6), rnd.randint(0, 120), rnd.getrandbits(16)])
        left = rnd.choice([rnd.randint(0, 6), rnd.randint(0, 120), rnd.getrandbits(16)])
        md = put_mdata(c, rnd, skill=small(rnd, 0, 400), lvl=small(rnd, 0, 60), range=rng_, left=left,
                       w28=rnd.getrandbits(32), w2c=rnd.getrandbits(32))
        tx, ty = rnd.getrandbits(16), rnd.getrandbits(16)
        if has_path:
            c.put(MP + 0x10, le16(tx) + le16(ty))
        cases += lines9(c, game)
        exp.append({"w": w, "invalid": invalid, "st": st, "sub": sub, "p1": p1, "own": own, "flag": flag,
                    "md": md, "tx": tx, "ty": ty})
    return cases, mem9(do20=True), {"cases": exp}


def create9b_model(row, game, br, neg=None):
    w, md, st, sub, own = row["w"], row["md"], row["st"], row["sub"], row["own"]
    sk, lv = s16(md["skill"]), s16(md["lvl"])
    x, y = subxy(st)
    flag8 = st["path"] and row["flag"] & 8
    br[w] += 1
    if row["invalid"]:
        br["ret2_rec"] += 1
        return ("ret", 2, 0)
    if w == "do21":
        if (sub > 0 if neg == "subpos" else sub != 0) and flag8:
            br["createat"] += 1
            br["createat_subneg"] += sub < 0
            return ("obs", "MissileCreateAt", {"ecx": game, "edx": own}, [sk, lv, sub, x, y], {}, {}, 0x005AF612)
        br["to_do20"] += 1
        return ("obs", "Do20", {"ecx": game, "edx": MU}, [], {}, {}, SENTINEL)
    if w == "do22":
        if sub == 0 or not st["path"]:
            br["ret2"] += 1
            return ("ret", 2, 0)
        w28, w2c = md["w28"], md["w2c"]
        if el_of(md) < 2:
            dy = s32(row["ty"] - y)
            w28 = s32(-dy) if neg != "noneg" else dy
            w2c = s32(row["tx"] - x)
            br["sets_offset"] += 1
        mem = {MD: mdbytes(md, w28=w28 & M32, w2c=w2c & M32)}
        if flag8:
            br["create"] += 1
            blk = block(flags=0xB, owner=own, cls=sub, x=x, y=y, tx=w28, ty=w2c, skill=sk, lvl=lv, loops=row["p1"])
            return obs_create9(game, blk, 0x005AF749, mem)
        br["move"] += 1
        return obs_move9(game, 0x005AF772, mem)
    if w == "do23":
        if sub == 0:
            br["ret2"] += 1
            return ("ret", 2, 0)
        if flag8:
            loops = s32(row["p1"]) > 0 and neg != "noneg"
            br["create_loops" if loops else "create"] += 1
            blk = block(flags=9 if loops else 1, owner=own, x=x, y=y, skill=sk, lvl=lv, cls=sub,
                        loops=row["p1"] if loops else 0)
            return obs_create9(game, blk, 0x005AF859)
        br["move"] += 1
        return obs_move9(game, 0x005AF862)
    if w == "do26":
        if (sub <= 0 if neg == "subpos" else sub == 0):
            br["ret2"] += 1
            return ("ret", 2, 0)
        period = s32(row["p1"]) if s32(row["p1"]) >= 1 else 1
        if cmod(el_of(md), period) == 0:
            br["createat"] += 1
            return ("obs", "MissileCreateAt", {"ecx": game, "edx": own}, [sk, lv, sub, x, y], {}, {}, 0x005AFA0E)
        br["move_tail"] += 1
        return obs_move9(game, SENTINEL)
    # do32
    if sub < 0:
        br["ret2"] += 1
        return ("ret", 2, 0)
    if flag8:
        br["create"] += 1
        return obs_create9(game, block(flags=1, owner=own, source=MU, skill=sk, lvl=lv, cls=sub), 0x005B047B)
    br["to_do7"] += 1
    return ("obs", "Do07", {"ecx": game, "edx": MU}, [], {}, {}, 0x005B0484)


# =============================================================================================== vines (do 20)
@family("vines", "9b")
def vines(rnd, game):
    cases, exp = [], []
    for k in range(1200):
        c = Case(FN9B["do20"])
        has_path = rnd.random() < 0.6
        st = put_missile(c, rnd, rnd.randrange(NREC), path=has_path)
        own, dead = put_owner_state(c, rnd, 0.85, (0, 1, 1, 0, 2))
        pos = put_owner_pos(c, rnd) if own else None
        md = put_mdata(c, rnd, range=rnd.getrandbits(16), left=rnd.getrandbits(16))
        cases += lines9(c, game, dumps=[(MD + 0x10, 2)])
        exp.append({"st": st, "own": own, "dead": dead, "pos": pos, "otyp": u32f(c, MU + 0x94) if own else None})
    return cases, mem9(), {"cases": exp}


def vines_model(row, game, br, neg=None):
    own = row["own"]
    dead = row["dead"] or row["otyp"] not in (0, 1) if own else None
    if neg == "alive_c6" and own:
        dead = row["otyp"] not in (0, 1)
    if not own or dead:
        br["hitunit_noowner" if not own else "hitunit_dead"] += 1
        return ("obs", "HitUnit", {"ecx": game, "edx": MU}, [0, 1], {}, {}, 0x005AF587)
    if row["st"]["path"]:
        br["retarget"] += 1
        p = row["pos"]
        return ("obs", "PathToRoomXY", {}, [MP, MU, p["oroom"], p["ox"], p["oy"]], {}, {}, 0x005A9A66)
    br["nopath_move"] += 1
    return obs_move9(game, 0x005AF572, {MD + 0x10: le16(9 if neg == "rem9" else 10)})


# =============================================================================================== rabies (do 30)
@family("rabies", "9b")
def rabies(rnd, game):
    cases, exp = [], []
    for k in range(1200):
        c = Case(FN9B["do30"])
        cls, invalid = pick_cls(rnd)
        has_path = rnd.random() < 0.45
        st = put_missile(c, rnd, cls, path=has_path)
        sub = rnd.choice([rnd.randrange(700)] * 8 + [-1, -0x8000])
        p1 = rnd.choice([4, rnd.randint(-3, 8), 0])
        p2 = rnd.choice([7, rnd.randint(-3, 20), 0, rnd.getrandbits(32)])
        if not invalid:
            put_rec9(c, cls, sub=sub, p1=p1, p2=p2)
        ttyp = rnd.choice([0, 1, 1, 1, 2, 3, 4, 5])
        tguid = rnd.getrandbits(32)
        found = rnd.random() < 0.8
        # the target first, the owner after it; the models read every link back from the case's own writes
        if found:
            put_unit_found(c, rnd, TGT, ttyp, tguid)
        else:
            put_unit_absent(c, rnd, ttyp, tguid)
        own, dead = put_owner_state(c, rnd, 0.85, (0, 1))
        pos = put_owner_pos(c, rnd) if own else None
        for u in (TGT, OWN, DECOY, MU):
            c.put(u + 0x20, le32(rnd.getrandbits(32)) + le32(rnd.getrandbits(32)))
        md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=small(rnd, 0, 40), range=rnd.randint(0, 80),
                       left=rnd.choice([rnd.randint(-3, 80), rnd.getrandbits(16), 0, 0]), w28=ttyp, w2c=tguid)
        cases += lines9(c, game, dumps=[(TGT + 0x20, 8), (OWN + 0x20, 8), (DECOY + 0x20, 8)])
        exp.append({"invalid": invalid, "st": st, "sub": sub, "p1": p1, "p2": p2, "ttyp": ttyp, "tguid": tguid,
                    "dead": dead, "pos": pos, "md": md,
                    "t": find_unit(c, ttyp, tguid), "own": owner_of(c),
                    "seeds": {str(u): list(struct.unpack("<II", c.fields[u + 0x20])) for u in (TGT, OWN, DECOY, MU)}})
    return cases, mem9(skills=True), {"cases": exp}


def rabies_model(row, game, br, neg=None):
    if row["invalid"] or row["sub"] < 0:
        br["ret2"] += 1
        return ("ret", 2, 0)
    md = row["md"]
    if not skill_ok(md):
        br["ret2_skill"] += 1
        return ("ret", 2, 0)
    t, own = row["t"], row["own"]
    left = s16(md["left"])
    dead = row["dead"] if own == OWN else None
    if not t or not own or dead or (left <= 0 if neg == "left_gt0" else left < 0):
        br["hitunit_" + ("notarget" if not t else "noowner" if not own else "dead" if dead else "left")] += 1
        return ("obs", "HitUnit", {"ecx": game, "edx": MU}, [0, 1], {}, {}, 0x005B01DE)
    if row["st"]["path"]:
        br["retarget"] += 1
        p = row["pos"]
        return ("obs", "PathToRoomXY", {}, [MP, MU, p["oroom"], p["ox"], p["oy"]], {}, {}, 0x005A9A66)
    p1 = s32(row["p1"])
    period = p1 if p1 >= 1 else 1
    if cmod(el_of(md), period) != 0:
        br["offbeat"] += 1
        return obs_move9(game, 0x005B01C4)
    su = MU if neg == "mseed" else t
    lo, hi = row["seeds"][str(su)]
    r = s32(row["p2"])
    n = s32(2 * r + 1)
    dx, lo, hi = rrange(lo, hi, n)
    dy, lo, hi = rrange(lo, hi, n)
    br["create_t%d" % row["ttyp"]] += 1
    br["draws_none"] += n < 1
    blk = block(flags=2, owner=t, source=MU, cls=row["sub"], skill=s16(md["skill"]), lvl=s16(md["lvl"]),
                tx=s32(dx - r), ty=s32(dy - r))
    return obs_create9(game, blk, 0x005B0187, {t + 0x20: le32(lo) + le32(hi)})


# =============================================================================================== reseed9b (28, 34, 35)
@family("reseed9b", "9b")
def reseed9b(rnd, game):
    cases, exp = [], []
    for k in range(1500):
        w = ("do28", "do34", "do35")[k % 3]
        c = Case(FN9B[w])
        cls, invalid = pick_cls(rnd)
        st = put_missile(c, rnd, cls, path=(w == "do35") or rnd.random() > 0.08)
        seed0 = (rnd.getrandbits(32), rnd.getrandbits(32))
        c.put(MU + 0x20, le32(seed0[0]) + le32(seed0[1]))
        own = put_owner(c, rnd)
        row = {"w": w, "invalid": invalid, "st": st, "own": own, "seed0": seed0}
        dumps = []
        if w == "do28":
            sub = rnd.choice([rnd.randrange(700)] * 8 + [-1])
            p = dict(p1=rnd.choice([0, 0, rnd.randint(-3, 10)]), p2=rnd.choice([0, 0, rnd.randint(-3, 12)]),
                     p3=rnd.choice([2, rnd.randint(-5, 30)]), p4=rnd.choice([128, rnd.randint(-5, 200)]),
                     p5=rnd.choice([30, rnd.getrandbits(32)]))
            if not invalid:
                put_rec9(c, cls, sub=sub, **p)
            md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=small(rnd, 0, 40), range=rnd.randint(0, 200),
                           left=rnd.randint(0, 200), w28=rnd.getrandbits(32))
            row.update(sub=sub, cal=put_skill_calcs(c, rnd, md["skill"], (0x64, 0x144)), **p)
        elif w == "do34":
            subs = [rnd.choice([rnd.randrange(700)] * 5 + [-1]) for _ in range(3)]
            ps = [rnd.choice([3, 45, 1, 2, rnd.randint(-3, 50), 0]) for _ in range(3)]
            p1 = rnd.choice([25, rnd.randint(-5, 60)])
            if not invalid:
                put_rec9(c, cls, sub=subs[0], sub2=subs[1], sub3=subs[2], p1=p1, p2=ps[0], p3=ps[1], p4=ps[2])
            md = put_mdata(c, rnd, skill=small(rnd, 0, 300), lvl=small(rnd, 0, 40), range=rnd.randint(0, 120),
                           left=rnd.randint(0, 120))
            row.update(subs=subs, ps=ps, p1=p1)
        else:
            p1 = rnd.choice([3, rnd.randint(-3, 6), 1])
            if not invalid:
                put_rec9(c, cls, p1=p1)
            md = put_mdata(c, rnd, range=rnd.randint(0, 60), left=rnd.randint(0, 60), w28=rnd.getrandbits(32),
                           w2c=rnd.choice([rnd.getrandbits(32), (rnd.randint(-30, 30) & 0xFFFF) |
                                           ((rnd.randint(-30, 30) & 0xFFFF) << 16)]))
            c.put(MP + 0x10, le32(rnd.getrandbits(32)))
            c.put(MP + 0x58, le32(rnd.getrandbits(32)))
            dumps = [(MP + 0x10, 4), (MP + 0x58, 4)]
            row.update(p1=p1)
        row["md"] = md
        cases += lines9(c, game, dumps=dumps)
        exp.append(row)
    return cases, mem9(skills=True), {"cases": exp}


def reseed9b_model(row, game, br, neg=None):
    w, md, st = row["w"], row["md"], row["st"]
    br[w] += 1
    if row["invalid"]:
        br["ret2_rec"] += 1
        return ("ret", 2, 0)
    seedb = le32(row["seed0"][0]) + le32(row["seed0"][1])
    x, y = subxy(st)
    if w == "do28":
        if row["sub"] < 0:
            br["ret2_sub"] += 1
            return ("ret", 2, 0)
        if not skill_ok(md):
            br["ret2_skill"] += 1
            return ("ret", 2, 0)
        if not row["own"]:
            br["noowner"] += 1
            return obs_move9(game, 0x005AFD5A, {MU + 0x20: seedb})
        r = s32(row["p2"]) if s32(row["p2"]) > 0 else max(ev_skill(row["cal"], 0x64), 1)
        period = s32(row["p1"]) if s32(row["p1"]) > 0 else max(ev_skill(row["cal"], 0x144), 1)
        e = el_of(md)
        if not (s32(row["p3"]) < e < s32(row["p4"]) and cmod(e, period) == 0):
            br["outside"] += 1
            return obs_move9(game, 0x005AFD5A, {MU + 0x20: seedb})
        lo, hi = md["w28"] & M32, 666
        n = s32(2 * r + 1)
        dx, lo, hi = rrange(lo, hi, n)
        dy, lo, hi = rrange(lo, hi, n)
        dx, dy = s32(dx - r), s32(dy - r)
        if neg == "swapxy":
            dx, dy = dy, dx
        br["create"] += 1
        blk = block9(flags=0x520, owner=row["own"], source=MU, tx=s32(x + dx), ty=s32(y + dy), w24=row["p5"],
                     skill=s16(md["skill"]), lvl=s16(md["lvl"]), cls=row["sub"])
        return obs_create9(game, blk, 0x005AFD50, {MU + 0x20: le32(lo) + le32(hi), MD: mdbytes(md, w28=lo)})
    if w == "do34":
        n = 0
        for i in range(3):
            if s16(row["subs"][i]) < 0 or s32(row["ps"][i]) <= 0:
                break
            n += 1
        if n == 0:
            br["ret2_none"] += 1
            return ("ret", 2, 0)
        e = el_of(md)
        if e < s32(row["p1"]):
            br["early"] += 1
            return ("obs", "Do03", {"ecx": game, "edx": MU}, [], {MU + 0x20: seedb}, {}, 0x005B0530)
        lo, hi = RNG.step(x & M32, 666)
        if n & (n - 1) == 0:
            k = lo & (n - 1)
        else:
            k = (s32(lo) % n) if neg == "signed" else lo % n
            k = k if k >= 0 else k + n
        br["n%d" % n] += 1
        if cmod(e, s32(row["ps"][k])) == 0:
            br["create"] += 1
            blk = block(owner=row["own"], source=MU, skill=s16(md["skill"]), lvl=s16(md["lvl"]),
                        cls=s16(row["subs"][k]))
            return obs_create9(game, blk, 0x005B0614, {MU + 0x20: le32(lo) + le32(hi)})
        br["offbeat"] += 1
        return ("obs", "Do03", {"ecx": game, "edx": MU}, [], {MU + 0x20: le32(lo) + le32(hi)}, {}, 0x005B0530)
    p1 = s32(row["p1"])
    period = p1 if p1 >= 1 else 1
    if cmod(el_of(md), period) != 0:
        br["offbeat"] += 1
        return obs_move9(game, 0x005B06A9, {MU + 0x20: seedb})
    a, b = s16(md["w2c"]), s16(md["w2c"] >> 16)
    lo, hi = RNG.step(md["w28"] & M32, 666)
    odd = bool(lo & 1) != (neg == "parity")
    if odd:
        nx, ny = cdiv(4 * a - b, 4), cdiv(4 * b + a, 4)
    else:
        nx, ny = cdiv(4 * a + b, 4), cdiv(4 * b - a, 4)
    nx, ny = nx or 1, ny or 1
    br["turn_" + ("odd" if odd else "even")] += 1
    px, py = (x + nx) & 0xFFFF, (y + ny) & 0xFFFF
    return ("obs", "PathPlan", {}, [MP, MU, 0], {MP + 0x10: le16(px) + le16(py), MP + 0x58: le32(0),
                                                MU + 0x20: le32(lo) + le32(hi)}, {}, 0x005B076C)


# =============================================================================================== scatter25 (do 25)
@family("scatter25", "9b")
def scatter25(rnd, game):
    cases, exp = [], []
    for k in range(900):
        c = Case(FN9B["do25"])
        cls, invalid = pick_cls(rnd)
        room = rnd.choice([0x13000000 + 0x100 * rnd.randrange(16)] * 12 + [0])
        st = put_missile(c, rnd, cls, room=room)
        own = put_owner(c, rnd, present_p=0.9)
        sub = rnd.choice([rnd.randrange(700)] * 8 + [-1, 0])
        if not invalid:
            put_rec9(c, cls, sub=sub)
        seed0 = (rnd.getrandbits(32), rnd.getrandbits(32))
        c.put(MU + 0x20, le32(seed0[0]) + le32(seed0[1]))
        md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=small(rnd, 0, 40), range=rnd.randint(0, 100),
                       left=rnd.randint(0, 100))
        cal = put_skill_calcs(c, rnd, md["skill"], (0x138, 0x13C))
        cases += lines9(c, game)
        exp.append({"invalid": invalid, "room": room, "st": st, "own": own, "sub": sub, "seed0": seed0, "md": md,
                    "cal": cal})
    return cases, mem9(skills=True), {"cases": exp}


def scatter25_model(row, game, br, neg=None):
    if row["invalid"] or row["sub"] == 0:
        br["ret2"] += 1
        return ("ret", 2, 0)
    md = row["md"]
    if not skill_ok(md):
        br["ret2_skill"] += 1
        return ("ret", 2, 0)
    r, period = ev_skill(row["cal"], 0x138), ev_skill(row["cal"], 0x13C)
    if neg == "swapcalc":
        r, period = period, r
    c = {"x": row["st"]["x"], "y": row["st"]["y"]}
    o = near_model(row["own"], c, md, period, r, row["sub"], 5 if neg == "mask5" else 0x45, game, row["room"], br)
    if o:
        br["celltest"] += 1
        return o + (0x005A9908,)
    br["move"] += 1
    return obs_move9(game, 0x005AF96A)


# =============================================================================================== wake (do 31)
@family("wake", "9b")
def wake(rnd, game):
    cases, exp = [], []
    for k in range(1200):
        c = Case(FN9B["do31"])
        cls, invalid = pick_cls(rnd)
        room = rnd.choice([0x13000000 + 0x100 * rnd.randrange(16)] * 8 + [0])
        has_path = rnd.random() > 0.06
        st = put_missile(c, rnd, cls, path=has_path, room=room)
        sub = rnd.choice([rnd.randrange(700)] * 8 + [-1])
        b04, ck, ae = rnd.getrandbits(8), rnd.choice([0, 1, 0x80]), rnd.choice([0, 0, 1])
        sizes = [rnd.choice([1, 2, 3, 0, rnd.getrandbits(8)]) for _ in range(NREC)]
        for i in range(NREC):
            put_rec9(c, i, size=sizes[i])
        if not invalid:
            put_rec9(c, cls, sub=sub, b04=b04, ckill=ck, aexp=ae)
        own = put_owner(c, rnd, present_p=0.6)
        flag = rnd.getrandbits(32)
        flag = flag | 8 if rnd.random() < 0.6 else flag & ~8
        if has_path:
            c.put(MP + 0x34, le32(flag))
        md = put_mdata(c, rnd, skill=small(rnd, 0, 300), lvl=small(rnd, 0, 40), w28=rnd.getrandbits(32),
                       w2c=rnd.getrandbits(32))
        cases += lines9(c, game)
        exp.append({"invalid": invalid, "room": room if has_path else 0, "st": st, "sub": sub, "b04": b04, "ck": ck,
                    "ae": ae, "size": sizes[cls] if not invalid else None, "own": own, "flag": flag, "md": md})
    return cases, mem9(), {"cases": exp}


def wake_model(row, game, br, neg=None):
    if row["invalid"] or row["sub"] < 0:
        br["ret2"] += 1
        return ("ret", 2, 0)
    md, st = row["md"], row["st"]
    if row["own"]:
        if st["path"] and row["flag"] & 8:
            br["create"] += 1
            tx, ty = md["w28"], md["w2c"]
            if neg == "swaptxy":
                tx, ty = ty, tx
            blk = block(flags=2, owner=row["own"], source=MU, cls=row["sub"], skill=s16(md["skill"]),
                        lvl=s16(md["lvl"]), tx=tx, ty=ty)
            return obs_create9(game, blk, 0x005B03A0)
        br["move"] += 1
        return obs_move9(game, 0x005B03C1)
    cc = 0 if row["b04"] & 2 else 2        # Explosion: bit 1 of cc, which no path up to a boundary reads
    if row["ck"] and neg != "nokill":
        cc |= 1
    if row["ae"]:
        br["noowner_alwaysexplode"] += 1
        return ("obs", "JustHitState", {"ecx": MU}, [], {}, {}, 0x005B02C0)
    if cc & 1 and row["room"]:
        br["noowner_unmark"] += 1
        x, y = subxy(st)
        return ("obs", "SizeUnmark", {}, [row["room"], x, y, row["size"], 0x40], {}, {}, 0x005B032A)
    br["noowner_ret2_" + ("kill_noroom" if cc & 1 else "nokill")] += 1
    return ("ret", 2, 0)


# =============================================================================================== regen (do 29, 33)
@family("regen", "9b")
def regen(rnd, game):
    cases, exp = [], []
    for k in range(1200):
        w = ("do29", "do33")[k % 2]
        c = Case(FN9B[w])
        cls, invalid = pick_cls(rnd)
        st = put_missile(c, rnd, cls)
        p1 = rnd.choice([45, rnd.randint(-3, 60)])
        if not invalid:
            put_rec9(c, cls, p1=p1)
        own, dead = put_owner_state(c, rnd, 0.95, (0, 1))
        rng_ = rnd.randint(0, 80)
        left = (rng_ - s32(p1)) & 0xFFFF if rnd.random() < 0.8 else rnd.randint(0, 80)
        md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=small(rnd, 0, 40), range=rng_, left=left)
        cal = put_skill_calcs(c, rnd, md["skill"], (0x138,))
        sv = None
        if own:
            mx = rnd.choice([rnd.randint(1, 3000) << 8, rnd.getrandbits(32), 0, rnd.randint(1, 50) << 8])
            cur = rnd.choice([rnd.randint(0, 3000) << 8 | rnd.getrandbits(8), mx, mx + 0x100, rnd.getrandbits(32)] +
                             [s32(mx - (rnd.randint(1, 400) << 8) - rnd.getrandbits(8))] * 4)
            a, b = (6, 7) if w == "do29" else (8, 9)
            sv = put_stats(c, rnd, OWN, {a: cur if rnd.random() < 0.95 else None,
                                          b: mx if rnd.random() < 0.95 else None})
        cases += lines9(c, game)
        exp.append({"w": w, "invalid": invalid, "p1": p1, "own": own, "dead": dead, "md": md, "cal": cal, "sv": sv})
    return cases, mem9(skills=True, isc=True), {"cases": exp}


def regen_model(row, game, br, neg=None):
    w, md = row["w"], row["md"]
    site_move, site_set = (0x005AFEAD, 0x005AFE7A) if w == "do29" else (0x005AFFFD, 0x005AFFCA)
    br[w] += 1
    if row["invalid"]:
        br["ret2_rec"] += 1
        return ("ret", 2, 0)
    if not skill_ok(md):
        br["ret2_skill"] += 1
        return ("ret", 2, 0)
    if not row["own"] or row["dead"]:
        br["noowner" if not row["own"] else "ownerdead"] += 1
        return obs_move9(game, site_move)
    if el_of(md) != s32(row["p1"]):
        br["notframe"] += 1
        return obs_move9(game, site_move)
    a, b = (6, 7) if w == "do29" else (8, 9)
    sv = {int(k): v for k, v in row["sv"].items()} if row["sv"] else {}
    hp, mx = stat_of(sv, a) >> 8, stat_of(sv, b) >> 8
    if hp >= mx:
        br["full"] += 1
        return obs_move9(game, site_move)
    add = muldiv(hp if neg == "hpbase" else mx, ev_skill(row["cal"], 0x138), 100)
    nv = s32(hp + add)
    if nv >= mx and neg != "nocap":
        nv = mx
        br["capped"] += 1
    br["set"] += 1
    return ("obs", "UnitSetStat", {}, [OWN, a, s32(nv << 8), 0], {}, {}, site_set)


# =============================================================================================== tornado (do 27)
@family("tornado", "9b")
def tornado(rnd, game):
    cases, exp = [], []
    for k in range(900):
        c = Case(FN9B["do27"])
        cls, invalid = pick_cls(rnd)
        put_missile(c, rnd, cls)
        p1 = rnd.choice([0, 0, rnd.randint(-3, 8)])
        if not invalid:
            put_rec9(c, cls, p1=p1)
        own = put_owner(c, rnd)
        md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=small(rnd, 0, 40), range=rnd.randint(0, 80),
                       left=rnd.randint(0, 80))
        cal = put_skill_calcs(c, rnd, md["skill"], (0x144, 0x138))
        cases += lines9(c, game)
        exp.append({"invalid": invalid, "p1": p1, "own": own, "md": md, "cal": cal})
    return cases, mem9(skills=True), {"cases": exp}


def tornado_model(row, game, br, neg=None):
    if row["invalid"]:
        br["ret2_rec"] += 1
        return ("ret", 2, 0)
    md = row["md"]
    if not skill_ok(md):
        br["ret2_skill"] += 1
        return ("ret", 2, 0)
    p1 = s32(row["p1"])
    if p1 > 0 or (neg == "p1ge0" and p1 == 0):
        period = p1 if p1 > 0 else 1
        br["period_param"] += 1
    else:
        period = max(ev_skill(row["cal"], 0x138 if neg == "calc1" else 0x144), 1)
        br["period_calc4"] += 1
    if cmod(el_of(md), period) == 0:
        br["build"] += 1
        return ("obs", "BuildDamage", {"ecx": game, "edx": row["own"]}, [MU, 0], {}, {}, 0x005AFB14)
    br["move"] += 1
    return obs_move9(game, 0x005AFB75)


# =============================================================================================== fx (do 19, 36)
@family("fx", "9b")
def fx(rnd, game):
    cases, exp = [], []
    for k in range(1200):
        w = ("do19", "do36")[k % 2]
        c = Case(FN9B[w])
        room = rnd.choice([0x13000000 + 0x100 * rnd.randrange(16)] * 8 + [0])
        has_path = rnd.random() > 0.1
        st = put_missile(c, rnd, rnd.randrange(NREC), path=has_path, room=room)
        if w == "do19":
            left = rnd.choice([rnd.randint(-3, 30), 1, 2, 24, 25, rnd.getrandbits(16)])
            md = put_mdata(c, rnd, left=left)
        else:
            left = rnd.choice([rnd.randint(-3, 200), 100, 101, rnd.getrandbits(16)])
            md = put_mdata(c, rnd, left=left, w28=rnd.choice([0, 0, 1, rnd.getrandbits(32)]))
        cases += lines9(c, game)
        exp.append({"w": w, "st": st, "room": room if has_path else 0, "md": md})
    return cases, mem9(), {"cases": exp}


def fx_model(row, game, br, neg=None):
    md, st = row["md"], row["st"]
    left = s16(md["left"])
    br[row["w"]] += 1
    if row["w"] == "do19":
        x, y = subxy(st)
        hi = 23 if neg == "r23" else 24
        if 2 <= left <= hi:
            br["heal"] += 1
            return ("obs", "UnitsInRange", {"ecx": game, "edx": 0x3002}, [x, y, MU, 0x7C, 1, 0x005AD8F0], {}, {},
                    0x005B0A2F)
        if left == 1:
            br["last"] += 1
            return ("obs", "UnitsInRange", {"ecx": game, "edx": 0x3002}, [x, y, MU, 0x7C, 1, 0x005AD910], {}, {},
                    0x005B0A2F)
        br["move"] += 1
        return obs_move9(game, SENTINEL)
    if md["w28"] == 0 and (left < 100 if neg == "lt100" else left <= 100):
        br["quest"] += 1
        return ("obs", "QuestActive", {}, [game, 0x24], {MD: mdbytes(md, w28=1)}, {}, 0x005B0A76)
    br["move"] += 1
    return obs_move9(game, SENTINEL)


# =============================================================================================== damage functions
def dmg_common(c, rnd, game, which, row):
    """Packet, unit, record class; -> the call lines with (unit, packet) on the stack."""
    return lines9(c, game, args=[row["unit"], PKT], dumps=[(PKT, 0x70)])


def dmg_ret(row, p, seed=None):
    mem = {PKT: bytes(p)}
    if seed is not None:
        mem[MU + 0x20] = le32(seed[0]) + le32(seed[1])
    return ("ret", None, 8, mem)


@family("dmgconv", "9b")
def dmgconv(rnd, game):
    cases, exp = [], []
    for k in range(1500):
        w = ("dmg1", "dmg12")[k % 2]
        c = Case(FN9B[w])
        cls, invalid = pick_cls(rnd)
        put_missile(c, rnd, cls)
        et = rnd.choice(list(range(13)) * 2 + [13, 0xFF])
        val = rnd.choice([rnd.randint(-5, 150), 0, 100, 50, 25, rnd.getrandbits(32)])
        pool = b"\x09" + le32(val) + b"\x00"
        off = rnd.choice([0] * 12 + [len(pool), 0xFFFFFFFF])
        if not invalid:
            put_rec9(c, cls, dcalc=off, etype=et)
        c.put(MPOOL, pool)
        c.put(DT + 0x64, le32(len(pool)))
        put_owner(c, rnd)
        put_mdata(c, rnd, lvl=small(rnd, 0, 40))      # MISS_EvalCalc(.., -1, -1) reads the missile's level
        row = {"w": w, "invalid": invalid, "et": et, "val": val, "off": off, "pool": len(pool)}
        row.update(put_target_unit(c, rnd))
        put_monstats(c, rnd, row)
        sv = put_stats(c, rnd, MU, {s: rnd_stat(rnd) for s in STATS_DMG}) if w == "dmg12" else {}
        seed0 = (rnd.getrandbits(32), rnd.getrandbits(32))
        c.put(MU + 0x20, le32(seed0[0]) + le32(seed0[1]))
        row.update(sv=sv, seed0=seed0, pkt=put_packet(c, rnd).hex())
        cases += dmg_common(c, rnd, game, w, row)
        exp.append(row)
    return cases, mem9(isc=True, mons=True, mpool=True), {"cases": exp}


def svi(row):
    return {int(k): v for k, v in row["sv"].items()} if row.get("sv") else {}


def dmgconv_model(row, game, br, neg=None):
    p = bytearray(bytes.fromhex(row["pkt"]))
    seed = tuple(row["seed0"])
    br[row["w"]] += 1
    if row["invalid"]:
        br["norec"] += 1
        return dmg_ret(row, p, seed)
    v = s32(row["val"]) if (row["off"] & M32) < row["pool"] else 0
    if v <= 0:
        br["calc_le0"] += 1
        return dmg_ret(row, p, seed)
    if v >= 100 and neg != "nocap":
        v = 100
        br["capped"] += 1
    et = row["et"]
    phys = pk_get(p, 0x08)
    d = muldiv(phys, v, 100)
    if not d < phys:
        d = phys
        br["d_is_phys"] += 1
    if row["w"] == "dmg1":
        pk_set(p, 0x08, s32(phys - d) if neg != "keep_phys" else phys)
        add_elem(p, et, d)
        br["conv_et%d" % et if et <= 13 else "conv_etff"] += 1
        return dmg_ret(row, p, seed)
    e, seed = elem_8c70(p, et, row, svi(row), seed)
    zero_elem(p, et, neg)
    add_elem(p, et, s32(d + e))
    br["roll_et%d" % et if et <= 13 else "roll_etff"] += 1
    return dmg_ret(row, p, seed)


@family("dmgelem", "9b")
def dmgelem(rnd, game):
    cases, exp = [], []
    for k in range(1200):
        w = ("dmg5", "dmg13")[k % 2]
        c = Case(FN9B[w])
        cls, invalid = pick_cls(rnd)
        put_missile(c, rnd, cls)
        et = rnd.choice(list(range(13)) * 2 + [13, 0xFF])
        dp1 = rnd.choice([50, 0, rnd.randint(-10, 200), rnd.getrandbits(32)])
        dp2 = rnd.choice([50, 0, rnd.randint(-10, 200)])
        if not invalid:
            put_rec9(c, cls, dp1=dp1, dp2=dp2, etype=et)
        own = put_owner(c, rnd)
        row = {"w": w, "invalid": invalid, "et": et, "dp1": dp1, "dp2": dp2, "own": own}
        row.update(put_target_unit(c, rnd))
        put_monstats(c, rnd, row)
        sv = put_stats(c, rnd, MU, {s: rnd_stat(rnd) for s in STATS_DMG})
        osv = put_stats(c, rnd, OWN, {25: rnd.choice([rnd.randint(-100, 400), 0, rnd.getrandbits(32)])}) \
            if own and w == "dmg13" else {}
        seed0 = (rnd.getrandbits(32), rnd.getrandbits(32))
        c.put(MU + 0x20, le32(seed0[0]) + le32(seed0[1]))
        row.update(sv=sv, osv={str(k_): v for k_, v in osv.items()}, seed0=seed0, pkt=put_packet(c, rnd).hex())
        cases += dmg_common(c, rnd, game, w, row)
        exp.append(row)
    return cases, mem9(isc=True, mons=True), {"cases": exp}


def dmg5_body(row, p, seed, br, neg=None):
    if row["invalid"]:
        br["norec"] += 1
        return seed
    et = row["et"]
    e, seed = elem_8c70(p, et, row, svi(row), seed)
    und = is_undead(row) if neg != "undead8" else (row["utype"] == 1 and 0 <= row["ucls"] < NMON and
                                                    bool(row["mflags"][row["ucls"]] & 0x08))
    if s32(row["dp1"]) > 0 and und:
        add_elem(p, et, muldiv(e, row["dp1"], 100))
        br["undead_bonus"] += 1
    if s32(row["dp2"]) > 0 and is_demon(row):
        add_elem(p, et, muldiv(e, row["dp2"], 100))
        br["demon_bonus"] += 1
    br["roll_et%d" % et if et <= 13 else "roll_etff"] += 1
    return seed


def dmgelem_model(row, game, br, neg=None):
    p = bytearray(bytes.fromhex(row["pkt"]))
    seed = tuple(row["seed0"])
    br[row["w"]] += 1
    if row["w"] == "dmg13":
        if not row["unit"] or row["utype"] != 1:
            br["not_monster"] += 1
            return dmg_ret(row, p, seed)
        if row["own"] and neg != "dmg13_pct":
            ph = pk_get(p, 0x08)
            pct = int(row["osv"].get("25", 0))
            pk_set(p, 0x08, s32(cdiv(s32(pct * ph), 100) + ph))
            br["owner_ed"] += 1
    seed = dmg5_body(row, p, seed, br, neg)
    return dmg_ret(row, p, seed)


@family("dmgpkt", "9b")
def dmgpkt(rnd, game):
    cases, exp = [], []
    order = ("dmg2", "dmg3", "dmg4", "dmg7", "dmg8", "dmg9", "dmg10", "dmg11")
    for k in range(2400):
        w = order[k % 8]
        c = Case(FN9B[w])
        cls, invalid = pick_cls(rnd)
        put_missile(c, rnd, cls)
        dp1 = rnd.choice([0, 19, 100, rnd.randint(-10, 130), rnd.getrandbits(32)])
        ovl = rnd.choice([0, 81, -1, rnd.randint(-5, 300)])
        if not invalid:
            put_rec9(c, cls, dp1=dp1, ovl=ovl)
        row = {"w": w, "invalid": invalid, "dp1": dp1, "ovl": ovl}
        row.update(put_target_unit(c, rnd))
        seed0 = (rnd.getrandbits(32), rnd.getrandbits(32))
        c.put(MU + 0x20, le32(seed0[0]) + le32(seed0[1]))
        row["seed0"] = seed0
        if w == "dmg2":
            row["sv"] = put_stats(c, rnd, MU, {56: rnd_stat(rnd)})
        md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=small(rnd, -3, 40), w28=rnd.getrandbits(32))
        row["md"] = md
        if w in ("dmg7", "dmg9", "dmg11") and 0 <= s16(md["skill"]) < NSREC:
            sb = SREC + 0x23C * s16(md["skill"])
            sp = {"sp1": rnd.choice([rnd.randint(-5, 50), rnd.getrandbits(32)]),
                  "sp2": rnd.choice([rnd.randint(-5, 50), rnd.getrandbits(32)])}
            c.put(sb + 0x148, le32(sp["sp1"]))
            c.put(sb + 0x14C, le32(sp["sp2"]))
            row.update(sp)
        if w == "dmg11":
            row["own"] = put_owner(c, rnd)
            frame = rnd.getrandbits(32)
            r = rnd.random()
            if r < 0.6:
                md["w28"] = (frame + rnd.choice([rnd.randint(-5, 300), 10, 9])) & M32
                c.put(MD + 0x28, le32(md["w28"]))
            c.put(GAME + FRAME, le32(frame))
            row["frame"] = frame
            if 0 <= s16(md["skill"]) < NSREC:
                sb = SREC + 0x23C * s16(md["skill"])
                el = {"len0": rnd.randint(-10, 200), "l1": rnd.randint(-5, 30), "l2": rnd.randint(-5, 30),
                      "l3": rnd.randint(-5, 30)}
                v = rnd.choice([0, 50, rnd.randint(-100, 200)])
                pool = b"\x09" + le32(v) + b"\x00"
                coff = rnd.choice([0, 0, 0xFFFFFFFF, len(pool)])
                c.put(SPOOL, pool)
                c.put(DT + 0x44, le32(len(pool)))
                for name, o in (("len0", 0x214), ("l1", 0x218), ("l2", 0x21C), ("l3", 0x220)):
                    c.put(sb + o, le32(el[name]))
                c.put(sb + 0x224, le32(coff))
                el.update(v=v, coff=coff, pool=len(pool))
                row["el"] = el
        row["pkt"] = put_packet(c, rnd).hex()
        cases += dmg_common(c, rnd, game, w, row)
        exp.append(row)
    return cases, mem9(isc=True, skills=True), {"cases": exp}


def elemlen(row):
    """SKILLS_GetElemLen(unit, skill, lvl, 1): the level bands of ELevLen1..3 plus ELen, then + MulDiv(len, calc,
    100) when the ELen calc is in the pool and non-zero."""
    md = row["md"]
    lvl = s16(md["lvl"])
    if not skill_ok(md) or lvl <= 0:
        return 0
    el = row["el"]
    if lvl < 9:
        n = s32((lvl - 1) * el["l1"])
    elif lvl < 17:
        n = s32((lvl - 8) * el["l2"] + el["l1"] * 7)
    else:
        n = s32((lvl - 16) * el["l3"] + el["l2"] * 8 + el["l1"] * 7)
    n = s32(el["len0"] + n)
    if (el["coff"] & M32) != M32 and (el["coff"] & M32) < el["pool"]:
        v = s32(el["v"])
        if v:
            n = s32(n + muldiv(n, v, 100))
    return n


def dmgpkt_model(row, game, br, neg=None):
    p = bytearray(bytes.fromhex(row["pkt"]))
    seed = tuple(row["seed0"])
    w, md = row["w"], row["md"]
    br[w] += 1
    if w == "dmg4":
        pk_set(p, 0x34, pk_get(p, 0x30))
        pk_set(p, 0x30, 0)
        br["moved"] += 1
        return dmg_ret(row, p, seed)
    if w == "dmg11":
        if not row["own"] or not row["unit"]:
            br["zero_noowner" if not row["own"] else "zero_nounit"] += 1
            pk_set(p, 0x28, 0)
            pk_set(p, 0x2C, 0)
            return dmg_ret(row, p, seed)
        v = s32(md["w28"] - row["frame"])
        if v >= 10 and v <= elemlen(row):
            br["poison_len"] += 1
            pk_set(p, 0x2C, v)
        else:
            br["zero_" + ("short" if v < 10 else "long")] += 1
            pk_set(p, 0x28, 0)
            pk_set(p, 0x2C, 0)
        return dmg_ret(row, p, seed)
    if row["invalid"]:
        br["norec"] += 1
        return dmg_ret(row, p, seed)
    dp1 = s32(row["dp1"])
    if w == "dmg2":
        v = stat_of(svi(row), 56)
        pk_set(p, 0x34, muldiv(v, dp1 if dp1 >= 0 else 0, 100))
        pk_set(p, 0x30, 0)
        br["freeze"] += 1
        return dmg_ret(row, p, seed)
    if w == "dmg3":
        lo, hi = RNG.step(seed[0], seed[1])
        seed = (lo, hi)
        if ((lo & 0xFF) if neg == "dmg3_mask" else (lo & 0x7F)) < dp1:
            struct.pack_into("<H", p, 4, struct.unpack_from("<H", p, 4)[0] | 0x4000)
            br["pass"] += 1
        return dmg_ret(row, p, seed)
    if w == "dmg7":
        if dp1 > 0:
            s = dp1
            br["stun_param"] += 1
        else:
            lvl = s16(md["lvl"])
            if skill_ok(md) and lvl > 0:
                s = s32((lvl if neg == "dmg7_lvl" else lvl - 1) * s32(row["sp2"]) + s32(row["sp1"]))
                br["stun_skill"] += 1
            else:
                s = 0
                br["stun_zero"] += 1
        pk_set(p, 0x44, s)
        pk_set(p, 0x60, 0x60)
        return dmg_ret(row, p, seed)
    if w == "dmg8":
        ov = s16(row["ovl"])
        if not row["unit"] or ov <= 0:
            br["no_overlay"] += 1
            return dmg_ret(row, p, seed)
        br["overlay"] += 1
        return ("obs", "OverlaySet", {}, [row["unit"], ov, 0], {}, {}, 0x005AD498)
    if w == "dmg9":
        if dp1 > 0:
            s = dp1
            br["stun_param"] += 1
        elif skill_ok(md):
            s = s32(row["sp2"])
            br["stun_skillp2"] += 1
        else:
            s = 0
            br["stun_zero"] += 1
        pk_set(p, 0x44, s)
        pk_set(p, 0x60, 0x60)
        return dmg_ret(row, p, seed)
    # dmg10
    pk_set(p, 0x34, pk_get(p, 0x30))
    br["copied"] += 1
    return dmg_ret(row, p, seed)


@family("knock", "9b")
def knock(rnd, game):
    cases, exp = [], []
    for k in range(1200):
        c = Case(FN9B["dmg14"])
        cls, invalid = pick_cls(rnd)
        put_missile(c, rnd, cls)
        mtype = 3 if rnd.random() < 0.9 else rnd.choice([0, 1, 2, 4, 5])
        c.put(MU + 0x00, le32(mtype))
        dp1 = rnd.choice([1, 0, 2, 3, rnd.randint(-2, 4)])
        dp2 = rnd.choice([50, 33, 100, 0, rnd.randint(-10, 120)])
        if not invalid:
            put_rec9(c, cls, dp1=dp1, dp2=dp2)
        row = {"invalid": invalid, "mtype": mtype, "dp1": dp1, "dp2": dp2}
        row.update(put_target_unit(c, rnd))
        put_monstats(c, rnd, row)
        seed0 = (rnd.getrandbits(32), rnd.getrandbits(32))
        c.put(MU + 0x20, le32(seed0[0]) + le32(seed0[1]))
        row.update(seed0=seed0, pkt=put_packet(c, rnd).hex())
        cases += dmg_common(c, rnd, game, "dmg14", row)
        exp.append(row)
    return cases, mem9(mons=True), {"cases": exp}


def ms2_flag(row, bit):
    """sub_004638A0_MonStats2FlagTest(class, bit): MonStats +0x18 -> MonStats2 +0x04 flag bit."""
    cls = row["ucls"]
    if not (0 <= cls < NMON):
        return False
    i = s16(row["m2i"][cls])
    if not (0 <= i < NMON2):
        return False
    return bool(row["m2f"][i] & (1 << (bit - 8)))


def knock_model(row, game, br, neg=None):
    p = bytearray(bytes.fromhex(row["pkt"]))
    seed = tuple(row["seed0"])
    if row["mtype"] != 3 or row["invalid"] or not row["unit"]:
        br["none_" + ("mtype" if row["mtype"] != 3 else "rec" if row["invalid"] else "unit")] += 1
        return dmg_ret(row, p, seed)
    dp1, dp2 = s32(row["dp1"]), s32(row["dp2"])
    small_, large = 10, 11
    if neg == "large_swap":
        small_, large = 11, 10
    ch = None
    if row["utype"] == 0:
        if dp1 >= 1:
            ch = dp2
            br["player"] += 1
    elif row["utype"] == 1:
        if dp1 < 1:
            ch = dp2 if ms2_flag(row, small_) else None
            br["mon_p0_" + ("small" if ch is not None else "skip")] += 1
        elif dp1 == 1:
            if ms2_flag(row, small_):
                ch = s32(dp2 * (3 if neg == "x3" else 2))
                br["mon_p1_small"] += 1
            elif ms2_flag(row, large):
                br["mon_p1_large"] += 1
            else:
                ch = dp2
                br["mon_p1_medium"] += 1
        else:
            if ms2_flag(row, small_):
                ch = s32(dp2 * 3)
                br["mon_p2_small"] += 1
            elif ms2_flag(row, large):
                ch = dp2
                br["mon_p2_large"] += 1
            else:
                ch = s32(dp2 * 2)
                br["mon_p2_medium"] += 1
    else:
        br["none_utype"] += 1
    if ch is not None and ch > 0:
        r, lo, hi = rrange(seed[0], seed[1], 100)
        seed = (lo, hi)
        if r < ch:
            struct.pack_into("<H", p, 4, struct.unpack_from("<H", p, 4)[0] | 8)
            br["knockback"] += 1
    return dmg_ret(row, p, seed)


CHECKS.update({
    "create9b": check9b("create9b", create9b_model, ["subpos", "noneg"], [RS_HASH]),
    "vines": check9b("vines", vines_model, ["alive_c6", "rem9"], [RS_HASH]),
    "rabies": check9b("rabies", rabies_model, ["mseed", "left_gt0"], [RS_HASH]),
    "reseed9b": check9b("reseed9b", reseed9b_model, ["swapxy", "parity"], [RS_HASH, RS_SKN, RS_CALC_JT]),
    "scatter25": check9b("scatter25", scatter25_model, ["mask5", "swapcalc"], [RS_HASH, RS_SKN, RS_CALC_JT]),
    "wake": check9b("wake", wake_model, ["nokill", "swaptxy"], [RS_HASH, RS_BITMASK, RS_SIZE_JT]),
    "regen": check9b("regen", regen_model, ["nocap", "hpbase"], [RS_HASH, RS_SKN, RS_CALC_JT, RS_BITMASK]),
    "tornado": check9b("tornado", tornado_model, ["calc1", "p1ge0"], [RS_HASH, RS_SKN, RS_CALC_JT]),
    "fx": check9b("fx", fx_model, ["r23", "lt100"], []),
    "dmgconv": check9b("dmgconv", dmgconv_model, ["nocap", "keep_phys", "zero_all"],
                        [RS_HASH, RS_MSN, RS_CALC_JT, RS_BITMASK, RS_JT8C70, RS_JT91C0, RS_JT9270]),
    "dmgelem": check9b("dmgelem", dmgelem_model, ["undead8", "dmg13_pct"],
                       [RS_HASH, RS_BITMASK, RS_JT8C70, RS_JT9270]),
    "dmgpkt": check9b("dmgpkt", dmgpkt_model, ["dmg3_mask", "dmg7_lvl"], [RS_HASH, RS_SKN, RS_CALC_JT, RS_BITMASK]),
    "knock": check9b("knock", knock_model, ["large_swap", "x3"], [RS_BITMASK]),
})

PINS9B = [  # (address, mnemonic, operand substring): instructions the 9b claims turn on (ADR-0015 (5))
    (0x005AF5C9, "cmp", "WORD PTR [edi+0x18],0x0"), (0x005AF5CE, "je", ""),          # do 21: SubMissile1 != 0
    (0x005AF6BB, "neg", "eax"), (0x005AF69C, "cmp", "eax,0x2"),                       # do 22: -(dy), elapsed < 2
    (0x005AFCBF, "lea", "edx,[edx+edx*1+0x1]"), (0x005AFC90, "jle", ""), (0x005AFC99, "jge", ""),   # do 28
    (0x005AFE30, "sar", "esi,0x8"), (0x005AFE3A, "sar", "edi,0x8"),                   # do 29: arithmetic >> 8
    (0x005B0154, "lea", "edi,[esi+esi*1+0x1]"), (0x005B0158, "add", "ecx,0x20"),      # do 30: the target's seed
    (0x005B0572, "test", "edi,ecx"), (0x005B058E, "div", "edi"), (0x005B05B7, "and", "esi,eax"),    # do 34
    (0x005B0712, "and", "edx,0x3"), (0x005B0725, "sar", "edi,0x2"), (0x005B06FF, "test", "al,0x1"),  # do 35
    (0x005B0950, "cmp", "ecx,0x16"), (0x005B0953, "ja", ""), (0x005B0A59, "cmp", "ebx,0x64"),       # do 19, 36
    (0x005AD0A0, "cmp", "eax,0x64"), (0x005AD1EE, "setl", "cl"), (0x005AD267, "and", "eax,0x7f"),   # dmg 1, 2, 3
    (0x005AD5F8, "mov", "eax,0x51eb851f"), (0x005AD709, "lea", "esi,[esi+esi*2]"),   # dmg 13, 14
    (0x005A8CF3, "cmp", "edi,0xffffffa6"),                                            # the -90 floor
]


# ================================================================================================= commands
def batch_families(a):
    if a.family:
        return a.family
    return [f for f in FAMILIES if FAMILY_BATCH[f] == a.batch]


def batch_dir(a):
    return a.dir or os.path.join(ROOT, "workspace", "logs", "skills-cat-" + a.batch)


def cmd_cases(a):
    a.dir = batch_dir(a)
    for fam in batch_families(a):
        rnd = random.Random("cat%s-" % FAMILY_BATCH[fam] + fam)
        cases, mem, meta = FAMILIES[fam](rnd, GAME)
        os.makedirs(a.dir, exist_ok=True)
        with open(os.path.join(a.dir, fam + ".cases"), "w") as f:
            f.write("\n".join(cases) + "\n")
        with open(os.path.join(a.dir, fam + ".mem"), "w") as f:
            f.write("\n".join(mem) + "\n")
        with open(os.path.join(a.dir, fam + ".json"), "w") as f:
            json.dump(meta, f)
        print("CAT%s cases %s calls=%d mem_lines=%d" % (FAMILY_BATCH[fam].upper(), fam, sum(1 for c in cases if c.startswith("call")), len(mem)))
    return 0


def cmd_check(a):
    rc = 0
    a.dir = batch_dir(a)
    for fam in batch_families(a):
        calls, reads, writes = read_out(os.path.join(a.dir, fam + ".out"))
        meta = json.load(open(os.path.join(a.dir, fam + ".json")))
        if len(calls) != len(meta["cases"]):
            print("CAT%s %s bad: %d calls in the output, %d cases" % (FAMILY_BATCH[fam].upper(), fam, len(calls), len(meta["cases"])))
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


def cmd_static9b(a):
    rep = Report("static")
    rep.batch = "9B"
    A = S4.asm()
    for va, mn, sub in PINS9B:
        ins = A.at(va)
        rep.c["pins"] += 1
        if ins is None or ins[0] != mn or sub not in ins[1]:
            rep.bad("pin 0x%08X: %r, want %s %s" % (va, ins, mn, sub))
        else:
            rep.c["pins_ok"] += 1
    for lo, n, name in ((BITMASK, 32, "g_BitMask32"), (0x006E10E0, 20, "hash offsets"),
                        (0x0062057C, 24, "UNIT_GetSizeX jump table"), (0x006C1164, 88, "CALC_Eval jump table")):
        sec = S4.section_of(lo)
        flags = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.c["ro_reads"] += 1
        if flags & 0x80000000:
            rep.bad("%s 0x%08X in writable %s" % (name, lo, sec))
        rep.notes.append("%s 0x%08X: %s" % (name, lo, sec))
    masks = [S4.dword(BITMASK + 4 * i) for i in range(8)]
    rep.notes.append("g_BitMask32[0..7]: %s" % " ".join("0x%X" % m for m in masks))
    if masks != [1 << i for i in range(8)]:
        rep.bad("g_BitMask32 is not 1 << i")
    for lo, name in ((SK_NFUNCS, "skills calc function count"), (MS_NFUNCS, "missiles calc function count")):
        stores = [(va, mn, ops) for va, (mn, ops) in A.ins.items()
                  if mn in ("mov", "add", "sub", "inc", "dec", "or", "and", "xor") and "PTR" in ops.split(",")[0]
                  and ("ds:0x%x" % lo) in ops.split(",")[0]]
        rep.c["data_stores"] += len(stores)
        rep.notes.append("%s 0x%08X: %d stores in .text" % (name, lo, len(stores)))
    rep.notes.append("do table 19..36: %s" % " ".join("%d:0x%08X" % (i, S4.dword(0x0073C768 + 4 * i))
                                                      for i in range(19, 37)))
    rep.notes.append("damage table 0..15: %s" % " ".join("%d:0x%08X" % (i, S4.dword(0x0073C960 + 4 * i))
                                                        for i in range(16)))
    for name, va in sorted(FN9B.items(), key=lambda kv: kv[1]):
        num = int(name[2:]) if name.startswith("do") else int(name[3:])
        tab = 0x0073C768 if name.startswith("do") else 0x0073C960
        rep.c["table_entries"] += 1
        if S4.dword(tab + 4 * num) != va:
            rep.bad("%s: table entry 0x%08X, model address 0x%08X" % (name, S4.dword(tab + 4 * num), va))
    print("CAT9B static " + " ".join("%s=%d" % (k, rep.c[k]) for k in sorted(rep.c)))
    for n in rep.notes:
        print("  " + n)
    return 1 if rep.c["bad"] else 0


def cmd_static(a):
    if a.batch == "9b":
        return cmd_static9b(a)
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
    a.dir = batch_dir(a)
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
    print("CAT%s manifest files=%d sha256=%s" % (a.batch.upper(), len(lines), hashlib.sha256(text.encode()).hexdigest()))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["cases", "check", "static", "manifest"])
    ap.add_argument("family", nargs="*")
    ap.add_argument("--dir", default=None, help="default workspace/logs/skills-cat-<batch>")
    ap.add_argument("--batch", default="9a", choices=["9a", "9b"], help="the families of one batch (default 9a)")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    return {"cases": cmd_cases, "check": cmd_check, "static": cmd_static, "manifest": cmd_manifest}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

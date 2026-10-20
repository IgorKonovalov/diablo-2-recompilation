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

Batch sor (`--batch sor`, files under workspace/logs/skills-cat-sor/, draws from random.Random("catsor-<family>")):
the sorceress start functions 11-14 and do functions 17-29 and 144 (g_SkillStartFuncs, g_SkillDoFuncs), each
(ECX game, EDX unit; id, lvl), and the Inferno helpers 0x005C8CA0 / 0x005C8E30 called directly:
  start_sor  start 11, 12, 13, 14, do 19           inferno_sor  0x005C8CA0, 0x005C8E30
  create_sor do 17, 20, 22, 24, 26, 28             state_sor    do 18, 23, 25, 29
  tk_sor     do 21 (the stun draw)                 hydra_sor    do 144
The caster's and the target's seeds are compared in every case; UnitsHostile and UnitsSameParty run emulated
(PlayerPairFlags and PartyIdOfUnit observed); `static --batch sor` pins the instructions and reads the tables.

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
            for i, b in (exp[7] if len(exp) > 7 else {}).items():     # 9c: a pointer argument's bytes
                got = stack_bytes(c, arg(c, i), len(b))
                if got != b:
                    ok, why = False, "*arg%d=%s want %s" % (i, got.hex() if got else None, b.hex())
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


# ##################################################################################################################
# Batch 9c (plan 0046): missile server hit functions 1-29 (g_MissileSrvHitFuncs, `pSrvHitFunc`). A hit function is
# (ECX game, EDX missile; unit) -> result, `ret 4` (skills/0002 § 5). Conventions of 9b: the return address of every
# observed boundary asserted (with a site control), two negative controls per family, plus (lane/p46m2 review) the
# untouched-seed comparison: every 9c case writes and dumps the missile's, the owner's and the target's seeds and the
# model gives all three at the boundary or the return, so a family that steps a seed it should not fails. A boundary
# argument that is a pointer to the caller's frame (a packet, a context block) is compared by content (exp[7]).
# ##################################################################################################################
FN9C = {
    "hit1": 0x005A9A70, "hit2": 0x005A9D80, "hit3": 0x005A9F90, "hit4": 0x005B07A0, "hit7": 0x005A9FB0,
    "hit8": 0x005AA180, "hit9": 0x005AA250, "hit10": 0x005AA650, "hit12": 0x005AA730, "hit13": 0x005AA8B0,
    "hit14": 0x005AABB0, "hit15": 0x005AAD40, "hit16": 0x005AAE10, "hit17": 0x005AAFB0, "hit18": 0x005AB0B0,
    "hit19": 0x005AB110, "hit20": 0x005AB370, "hit21": 0x005AB500, "hit22": 0x005ADD20, "hit24": 0x005A9BF0,
    "hit25": 0x005AB820, "hit26": 0x005AB8D0, "hit27": 0x005ABA00, "hit28": 0x005ABA10, "hit29": 0x005ABB00,
}
HIT_TABLE = 0x0073C840
BOUND9C = dict(BOUND9B)
BOUND9C.update({
    0x0056BAD0: "AreaHitAt", 0x00554D20: "AllyTest", 0x0056BD10: "NearestUnit", 0x006251F0: "StatListAlloc",
    0x005C6CC0: "ApplyAuraStats", 0x005DDD00: "Flee", 0x0056B3E0: "UnitFilter", 0x00554DE0: "SameParty",
    0x0056B7E0: "ForUnitsInRange", 0x005AA5B0: "GuidedRetarget", 0x0064D9B0: "CollisionTest",
})
BOUND_BY_NAME.update({v: k for k, v in BOUND9C.items()})
ALLBOUND.update(BOUND9C)
NSTATES = 190                      # DataTables+0xC4, the States count the hit functions test a state index against
RING16 = (0x006E2618, 0x006E25F8)  # hit 25's eight (x, y) offsets (.rdata)
RING64 = (0x006E2738, 0x006E2638)  # hit 29's 64 (x, y) offsets (.rdata)
RS_RING16 = (0x006E25F8, 0x006E2638, "r", "hit 25's offsets 0x006E25F8/0x006E2618 (.rdata)")
RS_RING64 = (0x006E2638, 0x006E2838, "r", "hit 29's offsets 0x006E2638/0x006E2738 (.rdata)")
RS_JT8F20 = (0x005A8F84, 0x005A8F84 + 4 * 9, "r", "0x005A8F20's EType jump table 0x005A8F84, EType 4-12 (.text)")
RS_BITMASK9C = (BITMASK, BITMASK + 32 * 4, "r", "g_BitMask32 0x006CE268 (.rdata): 1 << i, the state-bit and "
                "Skills-flag masks")


def put_rec9c(c, cls, **kw):
    """put_rec9 plus the hit fields: hsub (HitSubMissile1..4 +0x24..+0x2A s16, a list), hp1..hp3 (sHitPar1..3
    +0x4C/+0x50/+0x54), hcalc (SHitCalc1 +0x88), hflags (HitFlags +0xA8 u32), rflags (ResultFlags +0xAC u16)."""
    base = MREC + 0x1A4 * cls
    nine = {}
    for k, v in kw.items():
        if k == "hsub":
            for i, s in enumerate(v):
                c.put(base + 0x24 + 2 * i, le16(s))
        elif k in ("hp1", "hp2", "hp3"):
            c.put(base + {"hp1": 0x4C, "hp2": 0x50, "hp3": 0x54}[k], le32(v))
        elif k == "hcalc":
            c.put(base + 0x88, le32(v))
        elif k == "hflags":
            c.put(base + 0xA8, le32(v))
        elif k == "rflags":
            c.put(base + 0xAC, le16(v))
        else:
            nine[k] = v
    put_rec9(c, cls, **nine)
    return base


def mem9c(extra=(), isc=False, mons=False, skills=False, states=False):
    ex = list(extra)
    if skills:
        ex += ["dword %08x %08x" % (DT + 0xB98, SREC), "dword %08x %08x" % (DT + 0xBA0, NSREC),
               "dword %08x %08x" % (DT + 0x40, SPOOL)]
    if isc:
        ex += ["dword %08x %08x" % (DT + 0xBCC, ISC), "dword %08x %08x" % (DT + 0xBD4, NISC)]
    if mons:
        ex += ["dword %08x %08x" % (DT + 0xA78, MSREC), "dword %08x %08x" % (DT + 0xA80, NMON),
               "dword %08x %08x" % (DT + 0xA90, MS2REC), "dword %08x %08x" % (DT + 0xA98, NMON2)]
    if states:
        ex += ["dword %08x %08x" % (DT + 0xC4, NSTATES)]
    return mem_spec(ex, bounds=BOUND9C)


SEEDS9C = (MU + 0x20, OWN + 0x20, TGT + 0x20)


def put_seeds9c(c, rnd):
    """The three seeds every 9c case writes and dumps (the missile's is dumped by Case.lines already)."""
    s = [(rnd.getrandbits(32), rnd.getrandbits(32)) for _ in SEEDS9C]
    for a, v in zip(SEEDS9C, s):
        c.put(a, le32(v[0]) + le32(v[1]))
    return s


def seeds_mem(row, mseed=None):
    """The seeds at the boundary or return: the missile's as given (unchanged when None), the others unchanged."""
    s = [tuple(x) for x in row["seeds"]]
    if mseed is not None:
        s[0] = tuple(mseed)
    return {a: le32(v[0]) + le32(v[1]) for a, v in zip(SEEDS9C, s)}


def lines9c(c, game, unit, dumps=()):
    return c.lines(game, MU, extra_dumps=[(OWN + 0x20, 8), (TGT + 0x20, 8)] + list(dumps), args=[unit])


def ret9c(row, eax, mseed=None, mem=None):
    m = seeds_mem(row, mseed)
    m.update(mem or {})
    return ("ret", eax, 4, m)


def obs9c(row, name, regs, args, site, mseed=None, ptrs=None, mem=None, blk=None):
    """An observed boundary: blk is a MissileCreate block at EDX (compared whole)."""
    m = seeds_mem(row, mseed)
    m.update(mem or {})
    return ("obs", name, regs, args, m, {"edx": (0, blk)} if blk is not None else {}, site, ptrs or {})


def put_hit_unit(c, rnd, types=(1, 1, 1, 0, 0, 2, 3, 4, 5), p0=0.08):
    """The hit's unit argument: 0, or TGT of a type and a MonStats class (+0x04), guid +0x0C."""
    if rnd.random() < p0:
        return {"unit": 0, "utype": None, "ucls": None, "uguid": None}
    utype = rnd.choice(types)
    ucls = rnd.choice([rnd.randrange(NMON)] * 8 + [NMON, -1])
    guid = rnd.getrandbits(32)
    c.put(TGT + 0x00, le32(utype))
    c.put(TGT + 0x04, le32(ucls))
    c.put(TGT + 0x0C, le32(guid))
    return {"unit": TGT, "utype": utype, "ucls": ucls, "uguid": guid}


def rnd_par(rnd):
    return rnd.choice([0, 0, rnd.randint(1, 30), rnd.randint(1, 30), rnd.randint(-5, -1), rnd.getrandbits(32), 1])


def cal_or(row, p, field, floor):
    """`p > 0 ? p : max(calc(field), floor)` (floor None: no clamp)."""
    if s32(p) > 0:
        return s32(p)
    v = ev_skill(row["cal"], field)
    if floor is not None and v < floor:
        v = floor
    return v


# =============================================================================================== area9c
AREA_ORDER = ("hit1", "hit3", "hit9", "hit13", "hit14", "hit24")


@family("area9c", "9c")
def area9c(rnd, game):
    """Hits 1, 9, 13 (EType roll, then AreaHitAt), hits 14, 24 and 3 -> 44 (BuildDamage, then AreaHitAt)."""
    cases, exp = [], []
    for k in range(1800):
        w = AREA_ORDER[k % 6]
        c = Case(FN9C[w])
        cls, invalid = pick_cls(rnd)
        has_path = rnd.random() > 0.06
        st = put_missile(c, rnd, cls, path=has_path)
        sub = rnd.choice([rnd.randrange(700)] * 4 + [0, -1, -1, -0x8000])
        hp1, hp2 = rnd_par(rnd), rnd_par(rnd)
        et = rnd.choice(list(range(13)) * 2 + [13, 0xFF])
        hfl = rnd.choice([rnd.getrandbits(32), 0, 2, 5])
        rfl = rnd.choice([rnd.getrandbits(16), 0, 4, 9])
        if not invalid:
            put_rec9c(c, cls, hsub=[sub], hp1=hp1, hp2=hp2, etype=et, hflags=hfl, rflags=rfl)
        own = put_owner(c, rnd)
        md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=small(rnd, 0, 40))
        cal = put_skill_calcs(c, rnd, md["skill"], (0x138, 0x13C, 0x64, 0x60))
        row = {"w": w, "invalid": invalid, "st": st, "sub": sub, "hp1": hp1, "hp2": hp2, "et": et, "hfl": hfl,
               "rfl": rfl, "own": own, "md": md, "cal": cal}
        row.update(put_hit_unit(c, rnd, p0=0.5 if w == "hit3" else 0.08))
        put_monstats(c, rnd, row)
        row["sv"] = put_stats(c, rnd, MU, {s: rnd.choice([rnd_stat(rnd), rnd.randint(1, 300)]) for s in STATS_DMG}) \
            if w in ("hit1", "hit9", "hit13") else {}
        row["seeds"] = put_seeds9c(c, rnd)
        cases += lines9c(c, game, row["unit"])
        exp.append(row)
    return cases, mem9c(isc=True, mons=True, skills=True), {"cases": exp}


def area_pkt(row, neg=None):
    """The packet the EType hits hand to AreaHitAt: zeroed, the EType roll on the hit unit, then the flags."""
    p = bytearray(0x70)
    e, seed = elem_8c70(p, row["et"], row, svi(row), tuple(row["seeds"][0]))
    return p, seed


def or_flags(p, row, neg=None):
    struct.pack_into("<I", p, 0, struct.unpack_from("<I", p, 0)[0] | (row["hfl"] & M32))
    if neg != "noresult":
        struct.pack_into("<H", p, 4, struct.unpack_from("<H", p, 4)[0] | (row["rfl"] & 0xFFFF))


def len_by_etype(p, et, v):
    """0x005A8F20 (ECX game, EDX m; packet, v): the length field of the missile's EType."""
    off = {4: 0x30, 5: 0x2C, 9: 0x44, 11: 0x18, 12: 0x34}.get(et)
    if off is not None:
        pk_set(p, off, v)


def area9c_model(row, game, br, neg=None):
    w, md, st = row["w"], row["md"], row["st"]
    sk, lv = s16(md["skill"]), s16(md["lvl"])
    x, y = subxy(st)
    own, unit = row["own"], row["unit"]
    br[w] += 1
    if w == "hit3" and unit:
        br["hit3_unit_ret0"] += 1
        return ret9c(row, 0)
    if row["invalid"]:
        br["norec"] += 1
        return ret9c(row, 1)
    if w == "hit1":
        if not own:
            br["noowner"] += 1
            return ret9c(row, 1)
        if s32(row["hp1"]) <= 0 and not skill_ok(md):
            br["noskill"] += 1
            return ret9c(row, 1)
        r = cal_or(row, row["hp1"], 0x138 if neg != "calc64" else 0x64, 1)
        p, seed = area_pkt(row)
        or_flags(p, row, neg)
        br["area_hp1" if s32(row["hp1"]) > 0 else "area_calc"] += 1
        return obs9c(row, "AreaHitAt", {"ecx": game, "edx": own}, [x, y, r, None, 0], 0x005A9BE1, seed, {3: bytes(p)})
    if w == "hit24":
        if not own:
            br["noowner"] += 1
            return ret9c(row, 1)
        if s32(row["hp1"]) <= 0 and not skill_ok(md):
            br["noskill"] += 1
            return ret9c(row, 1)
        r = cal_or(row, row["hp1"], 0x138, 1)
        br["build"] += 1
        return obs9c(row, "BuildDamage", {"ecx": game, "edx": own, "ebx": r}, [MU, unit, None], 0x005A9D36,
                     ptrs={2: bytes(0x70)})
    if w == "hit3":                    # unit 0: hit 44 with unit 0 (no owner test; sHitPar1 != 0, not > 0)
        h1 = s32(row["hp1"])
        if (h1 > 0) if neg == "hp1pos" else (h1 != 0):
            r = h1
        else:
            if not skill_ok(md):
                br["noskill"] += 1
                return ret9c(row, 1)
            r = max(ev_skill(row["cal"], 0x64), 1)
        br["build44_hp1neg" if s32(row["hp1"]) < 0 else "build44"] += 1
        return obs9c(row, "BuildDamage", {"ecx": game, "edx": own, "edi": r, "ebx": y}, [MU, 0, None], 0x005A9F4C,
                     ptrs={2: bytes(0x70)})
    if w == "hit14":
        if not skill_ok(md):
            br["noskill"] += 1
            return ret9c(row, 1)
        if not own:
            br["noowner"] += 1
            return ret9c(row, 1)
        r = cal_or(row, row["hp1"], 0x64, 1)
        br["build14"] += 1
        return obs9c(row, "BuildDamage", {"ecx": game, "edx": own, "esi": r}, [MU, unit, None], 0x005AACB7,
                     ptrs={2: bytes(0x70)})
    if not skill_ok(md):
        br["noskill"] += 1
        return ret9c(row, 1)
    if w == "hit9":
        if row["sub"] >= 0:
            br["setstat56"] += 1
            return obs9c(row, "UnitSetStat", {}, [MU, 0x38 if neg != "stat86" else 0x86, 0, 0], 0x005AA2FA)
        r = cal_or(row, row["hp2"], 0x13C, 1)
        p, seed = area_pkt(row)
        or_flags(p, row, neg)
        br["area9"] += 1
        return obs9c(row, "AreaHitAt", {"ecx": game, "edx": own}, [x, y, r, None, 0], 0x005AA44D, seed, {3: bytes(p)})
    # hit13
    r = cal_or(row, row["hp1"], 0x64, 1)
    ln = s32(row["hp2"]) if s32(row["hp2"]) > 0 else ev_skill(row["cal"], 0x60)
    p, seed = area_pkt(row)
    if ln > 0 and neg != "nolen":
        len_by_etype(p, row["et"] if 0 <= row["et"] < 256 else 0, ln)
        br["len_et%d" % row["et"]] += 1
    or_flags(p, row, neg)
    br["area13"] += 1
    return obs9c(row, "AreaHitAt", {"ecx": game, "edx": own}, [x, y, r, None, 0], 0x005AAA7C, seed, {3: bytes(p)})


# =============================================================================================== holy9c (hits 7, 8)
@family("holy9c", "9c")
def holy9c(rnd, game):
    """Hit 7 (holy bolt: heal a pet, else the undead/demon test) and hit 8 (blaze: the owner in state 13)."""
    cases, exp = [], []
    for k in range(1500):
        w = ("hit7", "hit7", "hit8")[k % 3]
        c = Case(FN9C[w])
        cls, invalid = pick_cls(rnd)
        st = put_missile(c, rnd, cls)
        hp1 = rnd.choice([0, 1, 1, 1, rnd.getrandbits(32)])
        hp2 = rnd.choice([0, 1, 2, 2, rnd.randint(3, 9)])
        if not invalid and w == "hit7":
            put_rec9c(c, cls, hp1=hp1, hp2=hp2, ovl=rnd.choice([rnd.randrange(1, 40), 0, -1]))
        row = {"w": w, "invalid": invalid, "hp1": hp1, "hp2": hp2}
        if w == "hit8":
            own = put_owner(c, rnd, 0.9)
            row.update(put_hit_unit(c, rnd))
            if own and rnd.random() < 0.6:          # the owner is hit by its own blaze
                row.update(unit=OWN, utype=None)
            if own:
                otyp = u32f(c, MU + 0x94)
                c.put(OWN + 0x00, le32(otyp))
                row["otyp"] = otyp
                row["st13"] = put_state_bits(c, rnd, OWN, [13])
            row["own"] = own
            row["seeds"] = put_seeds9c(c, rnd)
            cases += lines9c(c, game, row["unit"])
            exp.append(row)
            continue
        own = put_owner(c, rnd, 0.9)
        row["own"] = own
        md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=small(rnd, 0, 40))
        row["md"] = md
        row.update(put_hit_unit(c, rnd, types=(0, 1, 1, 1, 1, 2, 3)))
        put_monstats(c, rnd, row)
        if own:
            otyp = u32f(c, MU + 0x94)
            c.put(OWN + 0x00, le32(otyp))
            c.put(OWN + 0x0C, le32(u32f(c, MU + 0x98)))
            row["otyp"], row["oguid"] = otyp, u32f(c, MU + 0x98)
        if skill_ok(md):
            fl = rnd.getrandbits(8)
            c.put(SREC + 0x23C * s16(md["skill"]) + 0x07, bytes([fl]))
            row["sflags"] = fl
        row["cal"] = put_skill_calcs(c, rnd, md["skill"], (0x138, 0x13C))
        if row["unit"] and row["utype"] == 1:        # MonsterOwnerRef: MonsterData+0x28 -> {+0x28 set, +0x2C, +0x30}
            mdat = TGT + 0x300
            c.put(TGT + 0x14, le32(mdat))
            if True:                                 # MonsterData+0x28 is read through: never 0 here
                ref = TGT + 0x380
                c.put(mdat + 0x28, le32(ref))
                on = rnd.random() < 0.85
                c.put(ref + 0x28, le32(1 if on else 0))
                if on:
                    rt = rnd.choice([0, 0, 0, 1])
                    rg = row.get("oguid", 0) if rnd.random() < 0.7 else rnd.getrandbits(32)
                    c.put(ref + 0x2C, le32(rg))
                    c.put(ref + 0x30, le32(rt))
                    row["oref"] = (rg, rt)
                else:
                    row["oref"] = None
        if row["unit"]:
            mx = rnd.choice([rnd.randint(1, 3000) << 8, rnd.getrandbits(32), 0])
            cur = rnd.choice([rnd.randint(0, 3000) << 8 | rnd.getrandbits(8), mx, rnd.getrandbits(32)])
            row["tsv"] = {str(k_): v for k_, v in put_stats(c, rnd, TGT, {6: cur if rnd.random() < 0.95 else None,
                                                                          7: mx if rnd.random() < 0.95 else None}).items()}
        row["sv"] = put_stats(c, rnd, MU, {21: rnd_stat(rnd), 22: rnd_stat(rnd)})
        row["seeds"] = put_seeds9c(c, rnd)
        cases += lines9c(c, game, row["unit"])
        exp.append(row)
    return cases, mem9c(isc=True, mons=True, skills=True, states=True), {"cases": exp}


def put_state_bits(c, rnd, unit, states):
    """unit+0x5C -> a stat list with +0x10 bit 31 and +0x58 -> state bit words; -> {state: bit}."""
    sl = SLIST[unit]
    k = rnd.random()
    if k < 0.06:
        c.put(unit + 0x5C, le32(0))
        return {s: 0 for s in states}
    fl = rnd.getrandbits(32)
    if k < 0.12:
        fl &= 0x7FFFFFFF
    else:
        fl |= 0x80000000
    c.put(unit + 0x5C, le32(sl))
    c.put(sl + 0x10, le32(fl))
    if not fl & 0x80000000:
        return {s: 0 for s in states}
    words = sl + 0x200
    c.put(sl + 0x58, le32(words))
    out = {}
    for wi in sorted({s >> 5 for s in states}):
        v = rnd.getrandbits(32)
        c.put(words + 4 * wi, le32(v))
        for s in states:
            if s >> 5 == wi:
                out[s] = (v >> (s & 31)) & 1
    return out


def holy9c_model(row, game, br, neg=None):
    w, unit, own = row["w"], row["unit"], row["own"]
    br[w] += 1
    if w == "hit8":
        if unit and own and unit == own and row["st13"].get("13", 0) and row["otyp"] in (0, 1, 3):
            br["owner_blaze_0"] += 1
            return ret9c(row, 0 if neg != "always2" else 2)
        br["ret2"] += 1
        return ret9c(row, 2)
    if row["invalid"] or not unit:
        br["norec" if row["invalid"] else "nounit"] += 1
        return ret9c(row, 1)
    md = row["md"]
    sk, lv = s16(md["skill"]), s16(md["lvl"])
    if s32(row["hp1"]) != 0 and own:
        pet = (row["otyp"] == 0 or row["utype"] == 1) and skill_ok(md) and row["sflags"] & 2
        if pet:
            ref = row.get("oref") if row["utype"] == 1 else None
            rg, rt = (ref if ref else (-1 & M32, None))
            pet = ref is not None and rt == 0 and rg == row["oguid"]
        if not pet:
            br["allytest"] += 1
            return obs9c(row, "AllyTest", {"ecx": game, "edx": own}, [unit, sk], 0x005AA053)
        if not skill_ok(md):
            return ret9c(row, 1)
        lo = s32(ev_skill(row["cal"], 0x138) << 8)
        hi = s32(ev_skill(row["cal"], 0x13C) << 8)
        r, l2, h2 = rangeb(row["seeds"][0][0], row["seeds"][0][1], s32(hi - lo))
        seed = (l2, h2)
        heal = s32(r + lo)
        if heal <= 0 and neg != "noroll":
            heal, seed = elem_roll(svi(row), 22, 21, -1, seed)
            br["heal_elemroll"] += 1
        tsv = {int(k_): v for k_, v in row["tsv"].items()}
        cur, mx = stat_of(tsv, 6), stat_of(tsv, 7)
        nv = s32(cur + heal)
        if nv >= mx and neg != "nocap":
            nv = mx
            br["heal_capped"] += 1
        br["heal"] += 1
        return obs9c(row, "UnitSetStat", {}, [unit, 6, nv, 0], 0x005AA0EC, seed)
    t = row["utype"]
    if t == 0:
        r = 3 if s32(row["hp2"]) == 0 else 4
    elif t == 1:
        h2 = s32(row["hp2"])
        if h2 == 0:
            r = 3
        elif h2 == 2:
            r = 3 if is_demon(row) else 4
        else:
            und = is_undead(row) if neg != "undead8" else (0 <= row["ucls"] < NMON and
                                                          bool(row["mflags"][row["ucls"]] & 0x08))
            r = 3 if und else 4
    else:
        r = 4
    br["type%d_ret%d" % (t, r)] += 1
    return ret9c(row, r)


# =============================================================================================== create9c
CREATE_ORDER = ("hit4", "hit15", "hit25", "hit26", "hit29", "hit12")


@family("create9c", "9c")
def create9c(rnd, game):
    """Hits 4, 15, 25, 26, 29 (sub-missiles up to the first MissileCreate) and 12 (up to the nearest-unit search)."""
    cases, exp = [], []
    for k in range(1800):
        w = CREATE_ORDER[k % 6]
        c = Case(FN9C[w])
        cls, invalid = pick_cls(rnd)
        has_path = rnd.random() > 0.06
        st = put_missile(c, rnd, cls, path=has_path)
        subs = [rnd.choice([rnd.randrange(NREC)] * 3 + [rnd.randrange(700), 0, -1, -1]) for _ in range(4)]
        hp1 = rnd_par(rnd)
        if not invalid:
            put_rec9c(c, cls, hsub=subs, hp1=hp1)
        p1s = {}
        if w == "hit25":
            for i in range(NREC):
                p1s[i] = rnd.choice([rnd.randint(0, 40), rnd.getrandbits(32)])
                c.put(MREC + 0x1A4 * i + 0x38, le32(p1s[i]))
        own = put_owner(c, rnd, 0.9)
        rng_ = rnd.randint(0, 60)
        left = rnd.choice([0, 0, rnd.randint(-3, 60)])
        md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=small(rnd, 0, 40), range=rng_, left=left & 0xFFFF,
                       w28=rnd.choice([0, 1, 2, rnd.randint(3, 8), rnd.getrandbits(32)]))
        cal = put_skill_calcs(c, rnd, md["skill"], (0x138, 0x64))
        row = {"w": w, "invalid": invalid, "st": st, "subs": subs, "hp1": hp1, "own": own, "md": md, "cal": cal,
               "p1s": p1s, "cls": cls}
        row.update(put_hit_unit(c, rnd))
        if row["unit"] and w == "hit25":
            tp = rnd.random() < 0.85 or row["utype"] in (2, 4, 5)   # types 2, 4, 5 read the path unchecked
            c.put(TGT + 0x2C, le32(TGTP if tp else 0))
            tx, ty = rnd.getrandbits(16), rnd.getrandbits(16)
            if tp:
                c.put(TGTP + 0x02, le16(tx))
                c.put(TGTP + 0x06, le16(ty))
                c.put(TGTP + 0x0C, le32(rnd.getrandbits(32)))
                c.put(TGTP + 0x10, le32(rnd.getrandbits(32)))
            row["tpos"] = (tx, ty) if tp else (0, 0)
            row["tstatic"] = (u32f(c, TGTP + 0x0C), u32f(c, TGTP + 0x10)) if tp else None
        row["seeds"] = put_seeds9c(c, rnd)
        cases += lines9c(c, game, row["unit"])
        exp.append(row)
    return cases, mem9c(skills=True), {"cases": exp}


def unit_pos9c(row):
    """UnitGetSubX/Y of the hit unit (types 2, 4, 5: the static path's +0x0C/+0x10; else the path's +0x02/+0x06)."""
    if row["utype"] in (2, 4, 5):
        return row["tstatic"] if row["tstatic"] else None
    return row["tpos"]


def create9c_model(row, game, br, neg=None):
    w, md, st, own, unit = row["w"], row["md"], row["st"], row["own"], row["unit"]
    sk, lv = s16(md["skill"]), s16(md["lvl"])
    x, y = subxy(st)
    s1 = s16(row["subs"][0] & 0xFFFF)
    br[w] += 1
    if row["invalid"]:
        br["norec"] += 1
        return ret9c(row, 1)
    if w == "hit4":
        for i, s in enumerate(row["subs"]):
            if s16(s & 0xFFFF) > 0 or (neg == "ge0" and s16(s & 0xFFFF) == 0):
                br["create_sub%d" % (i + 1)] += 1
                return obs9c(row, "MissileCreate", {"ecx": game}, [], 0x005B0838,
                             blk=block(owner=own, source=MU, cls=s, skill=sk, lvl=lv))
        br["none_ret3"] += 1
        return ret9c(row, 3)
    if w == "hit12":
        if not own or not unit:
            br["noowner" if not own else "nounit"] += 1
            return ret9c(row, 3)
        n = s32(md["w28"])
        if n <= (0 if neg == "count0" else 1):
            br["count_le1"] += 1
            return ret9c(row, 3)
        if s32(row["hp1"]) > 0:
            r = s32(row["hp1"])
        else:
            if not skill_ok(md):
                br["noskill"] += 1
                return ret9c(row, 3)
            r = max(ev_skill(row["cal"], 0x64), 1)
        br["nearest"] += 1
        return obs9c(row, "NearestUnit", {"ecx": game, "edx": own}, [x, y, r, 0x88583, row["uguid"], 0], 0x005AA819)
    if s1 < 0:
        br["sub_neg"] += 1
        return ret9c(row, 1)
    if w == "hit29" and ((s16(md["left"]) > 0) if neg == "leftpos" else (s16(md["left"]) != 0)):
        br["left_ret2"] += 1
        return ret9c(row, 2)
    if not own:
        br["noowner"] += 1
        return ret9c(row, 1)
    if w == "hit15":
        br["create15"] += 1
        return obs9c(row, "MissileCreate", {"ecx": game}, [], 0x005AADF5,
                     blk=block(flags=1, owner=own, x=x, y=y, skill=sk, lvl=lv, cls=s1))
    if w == "hit25":
        src = unit or MU
        step = max(s32(row["hp1"]), 1)
        if not 0 <= s1 < NREC:
            br["sub_norec"] += 1
            return ret9c(row, 3)
        if src == MU:
            sx, sy = x, y
        else:
            pos = unit_pos9c(row)
            sx, sy = pos if pos else (0, 0)
        b = bytearray(block(flags=0x1F, owner=own, source=src, cls=s1, x=sx, y=sy, skill=sk, lvl=lv,
                            loops=s32(lv - 1)))
        r16x, r16y = S4.dword(RING16[0]), S4.dword(RING16[1])
        struct.pack_into("<I", b, 0x1C, r16x)
        struct.pack_into("<I", b, 0x20, r16y)
        struct.pack_into("<I", b, 0x28, (row["p1s"][str(s1)] << 7) & M32 if neg != "vel" else row["p1s"][str(s1)])
        br["create25_unit" if unit else "create25_self"] += 1
        return obs9c(row, "MissileCreate", {"ecx": game}, [], 0x005AB7FD, blk=bytes(b))
    if w == "hit26":
        if not skill_ok(md):
            br["noskill"] += 1
            return ret9c(row, 1)
        rg = cal_or(row, row["hp1"], 0x138, 5)
        b = bytearray(block(flags=0x8001, owner=own, cls=s1, x=x, y=y, skill=sk, lvl=lv, range=rg))
        br["create26"] += 1
        return obs9c(row, "MissileCreate", {"ecx": game}, [], 0x005AB9ED, blk=bytes(b))
    # hit29
    b = bytearray(block(flags=2, owner=own, source=MU, skill=sk, lvl=lv, cls=s1))
    struct.pack_into("<I", b, 0x1C, S4.dword(RING64[0]))
    struct.pack_into("<I", b, 0x20, S4.dword(RING64[1]))
    br["create29"] += 1
    return obs9c(row, "MissileCreate", {"ecx": game}, [], 0x005ABBED, blk=bytes(b))


# =============================================================================================== state9c
STATE_ORDER = ("hit16", "hit19", "hit17", "hit28", "hit21", "hit18")
WARD = OBJ                        # hit 28's grim ward: a missile found by MissileData+0x28 as a type-3 guid
WARDP = OBJ + 0x400


def put_state_lists(c, rnd, unit, state):
    """unit+0x5C -> a stat list (+0x10 bit 31) whose +0x3C and +0x40 chains (next +0x2C) hold lists of states
    (+0x14), the asked state among them or not. -> the list UNIT_FindStatListByState returns (0 when none)."""
    sl = SLIST[unit]
    k = rnd.random()
    if k < 0.06:
        c.put(unit + 0x5C, le32(0))
        return 0
    fl = rnd.getrandbits(32) | 0x80000000
    if k < 0.12:
        fl &= 0x7FFFFFFF
    c.put(unit + 0x5C, le32(sl))
    c.put(sl + 0x10, le32(fl))
    if not fl & 0x80000000:
        return 0
    found = 0
    nodes = [sl + 0x400 + 0x40 * i for i in range(8)]
    pos = 0
    for head in (0x3C, 0x40):
        n = rnd.randrange(4)
        chain = nodes[pos:pos + n]
        pos += n
        c.put(sl + head, le32(chain[0] if chain else 0))
        for i, nd in enumerate(chain):
            stv = rnd.choice([state, rnd.randrange(NSTATES)]) if rnd.random() < 0.35 else rnd.randrange(NSTATES)
            if not found and (stv == state) and state != 0:
                found = nd
            c.put(nd + 0x14, le32(stv))
            c.put(nd + 0x2C, le32(chain[i + 1] if i + 1 < len(chain) else 0))
        if found:
            break
    return found


def add_state_words(c, rnd, unit, states):
    """The state bit words at stat list +0x58 (the list put_stats wrote, when its +0x10 bit 31 is set)."""
    a = u32f(c, unit + 0x5C) if (unit + 0x5C) in c.fields else 0
    if not a or not u32f(c, a + 0x10) & 0x80000000:
        return {s: 0 for s in states}
    words = a + 0x200
    c.put(a + 0x58, le32(words))
    out = {}
    for wi in sorted({s >> 5 for s in states}):
        v = rnd.getrandbits(32)
        c.put(words + 4 * wi, le32(v))
        for s in states:
            if s >> 5 == wi:
                out[s] = (v >> (s & 31)) & 1
    return out


@family("state9c", "9c")
def state9c(rnd, game):
    """Hits 16, 19 (a timed state on the unit), 17, 28 (flee), 21 (battle cry's filter) and 18 (the party test)."""
    cases, exp = [], []
    for k in range(1800):
        w = STATE_ORDER[k % 6]
        c = Case(FN9C[w])
        cls = rnd.randrange(NREC)
        st = put_missile(c, rnd, cls)
        own = put_owner(c, rnd, 0.9)
        md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=small(rnd, 0, 40),
                       w28=rnd.getrandbits(32))
        row = {"w": w, "st": st, "own": own, "md": md}
        row.update(put_hit_unit(c, rnd, types=(1, 1, 1, 1, 0, 3), p0=0.1))
        state = rnd.choice([rnd.randrange(1, NSTATES)] * 6 + [0, -1, NSTATES, NSTATES + 5])
        row["state"] = state
        if skill_ok(md):
            sb = SREC + 0x23C * s16(md["skill"])
            c.put(sb + 0x82, le16(state))
            sp = {"p1": rnd.randint(-5, 30), "p2": rnd.randint(-3, 10), "p3": rnd.randint(-50, 300),
                  "p4": rnd.randint(-10, 50), "p5": rnd.randint(-75, 300), "p6": rnd.randint(-1, 30),
                  "pp2": rnd.randint(-2, 40), "filt": rnd.choice([0, 0, 2, rnd.getrandbits(32)])}
            for f, o in (("p1", 0x148), ("pp2", 0x14C), ("p3", 0x150), ("p4", 0x154), ("p5", 0x158),
                         ("p6", 0x15C), ("filt", 0x50)):
                c.put(sb + o, le32(sp[f]))
            sp["p2"] = sp["pp2"]
            row["sp"] = sp
        row["cal"] = put_skill_calcs(c, rnd, md["skill"], (0x144, 0x60))
        if own:
            otyp = u32f(c, MU + 0x94)
            c.put(OWN + 0x00, le32(otyp))
            row["otyp"], row["oguid"] = otyp, u32f(c, MU + 0x98)
        if w in ("hit16", "hit19"):
            c.put(game + 0x1C, le32(0x12A00000 + rnd.randrange(16)))
            frame = rnd.choice([rnd.randrange(100000), rnd.getrandbits(32)])
            c.put(game + FRAME, le32(frame))
            row["pool"], row["frame"] = u32f(c, game + 0x1C), frame
            if row["unit"] and 0 <= state < NSTATES:
                row["found"] = put_state_lists(c, rnd, TGT, state)
        if w == "hit17" and row["unit"] and row["utype"] == 1:
            ol = rnd.choice([rnd.randint(1, 99), rnd.getrandbits(32)])
            osv = put_stats(c, rnd, OWN, {12: ol}) if own else {}
            near = s32(stat_of(osv, 12) + s16(md["lvl"]) + row.get("sp", {}).get("p2", 0)) + rnd.randint(-3, 3)
            tsv = put_stats(c, rnd, TGT, {12: rnd.choice([rnd.randint(1, 99), rnd.getrandbits(32), near, near])})
            row["osv"] = {str(a): b for a, b in osv.items()}
            row["tsv"] = {str(a): b for a, b in tsv.items()}
            row["bits"] = add_state_words(c, rnd, TGT, [state]) if 0 <= state < NSTATES else {}
        if w == "hit28":
            wguid = md["w28"]
            if rnd.random() < 0.85:
                put_unit_found(c, rnd, WARD, 3, wguid)
                c.put(WARD + 0x00, le32(3))
                c.put(WARD + 0x2C, le32(WARDP))
                wx, wy = rnd.getrandbits(16), rnd.getrandbits(16)
                if rnd.random() < 0.5 and row["unit"]:
                    wx, wy = None, None
                row["ward"] = True
            else:
                put_unit_absent(c, rnd, 3, wguid)
                row["ward"] = False
            if row["unit"] and row["utype"] == 1:
                tx, ty = rnd.getrandbits(16), rnd.getrandbits(16)
                c.put(TGT + 0x2C, le32(TGTP))
                c.put(TGTP + 0x02, le16(tx))
                c.put(TGTP + 0x06, le16(ty))
                row["tpos"] = (tx, ty)
                if row["ward"] and wx is None:          # close to the unit, or exactly r away on x
                    r = lvl_param(row["sp"], s16(md["lvl"]), "p1", "p2") if "sp" in row else 0
                    if rnd.random() < 0.4 and 0 < r < 0x7000:
                        wx, wy = (tx + rnd.choice([r, -r])) & 0xFFFF, ty
                    else:
                        wx = (tx + rnd.randint(-12, 12)) & 0xFFFF
                        wy = (ty + rnd.randint(-12, 12)) & 0xFFFF
            if row["ward"]:
                wx = rnd.getrandbits(16) if wx is None else wx
                wy = rnd.getrandbits(16) if wy is None else wy
                c.put(WARDP + 0x02, le16(wx))
                c.put(WARDP + 0x06, le16(wy))
                row["wpos"] = (wx, wy)
        row["seeds"] = put_seeds9c(c, rnd)
        cases += lines9c(c, game, row["unit"])
        exp.append(row)
    return cases, mem9c(isc=True, skills=True, states=True), {"cases": exp}


def lvl_param(sp, lv, a, b):
    """0x004CC7C0 / 0x004EFCB0 / SkillParamByLevel: sp[a] + (lvl - 1) * sp[b], 0 when lvl <= 0."""
    if lv <= 0:
        return 0
    return s32(s32((lv - 1) * sp[b]) + sp[a])


def state9c_model(row, game, br, neg=None):
    w, md, own, unit = row["w"], row["md"], row["own"], row["unit"]
    sk, lv = s16(md["skill"]), s16(md["lvl"])
    state = row["state"]
    br[w] += 1
    if w == "hit18":
        if not own:
            br["noowner"] += 1
            return ret9c(row, 1)
        if not unit:
            br["nounit"] += 1
            return ret9c(row, 0)
        br["sameparty"] += 1
        return obs9c(row, "SameParty", {"ecx": game, "edx": own}, [unit], 0x005AB0E0)
    if w == "hit21":
        if not own or not unit:
            br["noowner" if not own else "nounit"] += 1
            return ret9c(row, 1)
        hi = NSTATES if neg != "state_lt" else NSTATES - 1
        if not skill_ok(md) or not 0 <= s16(state & 0xFFFF) <= hi:
            br["noskill" if not skill_ok(md) else "badstate"] += 1
            return ret9c(row, 1)
        filt = 0xA783 if row["sp"]["filt"] else 0
        br["filter_a783" if filt else "filter_0"] += 1
        br["state_eq_count"] += s16(state & 0xFFFF) == NSTATES
        return obs9c(row, "UnitFilter", {"ecx": own, "edx": unit}, [filt], 0x005AB599)
    if not skill_ok(md):
        br["noskill"] += 1
        return ret9c(row, 1)
    if not own:
        br["noowner"] += 1
        return ret9c(row, 1)
    sp = row["sp"]
    if w == "hit28":
        if not unit or row["utype"] != 1:
            br["notmonster"] += 1
            return ret9c(row, 1)
        if not row["ward"]:
            br["noward"] += 1
            return ret9c(row, 1)
        r = lvl_param(sp, lv, "p1", "p2")
        (tx, ty), (wx, wy) = row["tpos"], row["wpos"]
        d2 = s32(s32((ty - wy) * (ty - wy)) + s32((tx - wx) * (tx - wx)))
        if not d2 < s32(r * r) if neg != "le" else not d2 <= s32(r * r):
            br["far"] += 1
            return ret9c(row, 1)
        br["flee28"] += 1
        return obs9c(row, "Flee", {"ecx": game, "edx": WARD}, [unit, sk, sp["p5"], sp["p6"]], 0x005ABAF0)
    if w == "hit17":
        if not unit or row["utype"] != 1:
            br["notmonster"] += 1
            return ret9c(row, 0)
        if not 0 <= s16(state & 0xFFFF) < NSTATES:
            br["badstate"] += 1
            return ret9c(row, 1)
        if row["bits"].get(str(state), row["bits"].get(state, 0)):
            br["hasstate"] += 1
            return ret9c(row, 0)
        ol = s32(row["osv"].get("12", 0))
        ul = s32(row["tsv"].get("12", 0))
        lhs = s32(sp["p2"] + s32(ol + lv)) if neg != "nolvl" else s32(sp["p2"] + ol)
        if not lhs > ul:
            br["toohigh"] += 1
            return ret9c(row, 0)
        br["flee17"] += 1
        return obs9c(row, "Flee", {"ecx": game, "edx": own},
                     [unit, sk, lvl_param(sp, lv, "p3", "p4"), lvl_param(sp, lv, "p5", "p6")], 0x005AB09B)
    # hit16, hit19
    if not unit:
        br["nounit"] += 1
        return ret9c(row, 0 if w == "hit16" else 1)
    if not 0 <= s16(state & 0xFFFF) < NSTATES:
        br["badstate"] += 1
        return ret9c(row, 1)
    field = 0x144 if w == "hit16" else 0x60
    if neg == "swapcalc":
        field = 0x60 if w == "hit16" else 0x144
    ln = max(ev_skill(row["cal"], field), 5)
    end = s32(row["frame"] + ln)
    if row["found"]:
        br["found"] += 1
        return obs9c(row, "ApplyAuraStats", {"ecx": unit, "edx": row["found"]},
                     [SREC + 0x23C * sk, sk, lv], 0x005AAF58 if w == "hit16" else 0x005AB24E)
    br["alloc"] += 1
    return obs9c(row, "StatListAlloc", {}, [row["pool"], 2, end, row["otyp"], row["oguid"]],
                 0x005AAEF9 if w == "hit16" else 0x005AB1F6)


# =============================================================================================== range9c
RANGE_ORDER = ("hit20", "hit22", "hit10", "hit10", "hit27")


@family("range9c", "9c")
def range9c(rnd, game):
    """Hit 20 (lightning fury: ForUnitsInRange), 22 (the stored unit's BuildDamage), 10 (guided arrow's keep/end
    test) and 27 (returns 1)."""
    cases, exp = [], []
    for k in range(1500):
        w = RANGE_ORDER[k % 5]
        c = Case(FN9C[w])
        row = {"w": w}
        if w == "hit10":
            room = rnd.choice([ROOM] * 10 + [0])
            st = put_missile(c, rnd, rnd.randrange(NREC), room=room)
            lid = None
            if room:
                lid = rnd.choice([1, 40, 75, 103, 109] + [rnd.randint(2, 39)] * 6 + [rnd.randint(0, 140)])
                c.put(ROOM + 0x10, le32(RLEV))
                c.put(RLEV + 0x58, le32(LEVEL))
                c.put(LEVEL + 0x1D0, le32(lid))
            s28 = rnd.getrandbits(32) if rnd.random() < 0.5 else rnd.randrange(8)
            left = rnd.choice([0, rnd.randint(-5, 5), rnd.randint(1, 100)])
            md = put_mdata(c, rnd, w28=s28, left=left & 0xFFFF)
            p7c = rnd.choice([1, 1, 1, rnd.getrandbits(32), 0])
            c.put(MP + 0x7C, le32(p7c))
            coll = rnd.getrandbits(16)
            if p7c:
                c.put(MP + 0x54, le16(coll))
            else:
                c.put(MP + 0x44, le32(rnd.getrandbits(32)))
                if not room:
                    c.put(MP + 0x1C, le32(0))
            t = put_target_link(c, rnd, MU, MP, TGT, TGTP)
            unit = rnd.choice([0, 0, TGT, TGT, OBJ])
            row.update(st=st, room=room, lid=lid, md=md, p7c=p7c, coll=coll, t=t, unit=unit,
                       p44=u32f(c, MP + 0x44) if not p7c else None, proom=u32f(c, MP + 0x1C) if not p7c else None)
            row["seeds"] = put_seeds9c(c, rnd)
            cases += lines9c(c, game, unit)
            exp.append(row)
            continue
        cls, invalid = pick_cls(rnd)
        st = put_missile(c, rnd, cls)
        sub = rnd.choice([rnd.randrange(700)] * 5 + [0, -1, -0x8000])
        hp1, hp2 = rnd_par(rnd), rnd_par(rnd)
        if not invalid:
            put_rec9c(c, cls, hsub=[sub], hp1=hp1, hp2=hp2)
        own = put_owner(c, rnd, 0.9)
        md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=small(rnd, 0, 40), w28=rnd.randrange(6),
                       w2c=rnd.getrandbits(32))
        cal = put_skill_calcs(c, rnd, md["skill"], (0x64, 0x138, 0x144))
        filt = rnd.choice([0, 0, 2, rnd.getrandbits(32)])
        if skill_ok(md):
            c.put(SREC + 0x23C * s16(md["skill"]) + 0x50, le32(filt))
        row.update(invalid=invalid, st=st, sub=sub, hp1=hp1, hp2=hp2, own=own, md=md, cal=cal, filt=filt)
        if w == "hit22":
            while (MU + 0x94) in c.fields and md["w28"] == u32f(c, MU + 0x94) and hash_slot(md["w28"], md["w2c"]) == \
                    hash_slot(u32f(c, MU + 0x94), u32f(c, MU + 0x98)):     # keep the owner's bucket apart
                md["w2c"] = rnd.getrandbits(32)
                c.put(MD + 0x2C, le32(md["w2c"]))
            if rnd.random() < 0.8:                       # no decoy: DECOY may be in the owner's chain
                put_unit_found(c, rnd, TGT, md["w28"], md["w2c"])
                row["t"] = TGT
            else:
                c.put(hash_slot(md["w28"], md["w2c"]), le32(0))
                row["t"] = 0
        unit = rnd.choice([0, TGT, OBJ])
        row["unit"] = unit
        row["seeds"] = put_seeds9c(c, rnd)
        cases += lines9c(c, game, unit)
        exp.append(row)
    return cases, mem9c(skills=True), {"cases": exp}


def range9c_model(row, game, br, neg=None):
    w, unit = row["w"], row["unit"]
    br[w] += 1
    if w == "hit27":
        return ret9c(row, 1)
    if w == "hit10":
        md = row["md"]
        if row["room"] and is_town(row["lid"]):
            br["town"] += 1
            return ret9c(row, 1)
        s = md["w28"] & M32
        if not unit and s & 4:
            br["nounit_s4"] += 1
            return ret9c(row, 1)
        if not row["p7c"]:
            br["collisiontest"] += 1
            st = row["st"]
            return obs9c(row, "CollisionTest", {}, [row["proom"], st["x"], st["y"], row["p44"], 0x7FFF], 0x00648ED9)
        if not unit and row["coll"] & 4:
            br["nounit_coll4"] += 1
            return ret9c(row, 1)
        if s & 1:
            if not unit:
                br["s1_nounit"] += 1
                return ret9c(row, 3)
            r = 3 if unit == row["t"] else 4
            if neg == "tgt_inv":
                r = 7 - r
            br["s1_ret%d" % r] += 1
            return ret9c(row, r)
        if s & 2:
            if s16(md["left"]) <= 0 if neg != "left_lt0" else s16(md["left"]) < 0:
                br["s2_retarget"] += 1
                return obs9c(row, "GuidedRetarget", {"eax": MU}, [game], 0x005AA6ED)
            r = 3 if s & 4 else 4
            br["s2_ret%d" % r] += 1
            return ret9c(row, r)
        br["plain_ret3"] += 1
        return ret9c(row, 3)
    md, own = row["md"], row["own"]
    sk, lv = s16(md["skill"]), s16(md["lvl"])
    x, y = subxy(row["st"])
    sub = s16(row["sub"] & 0xFFFF)
    if row["invalid"] or sub < 0:
        br["norec" if row["invalid"] else "sub_neg"] += 1
        return ret9c(row, 1)
    if w == "hit20":
        if not skill_ok(md) or not own:
            br["noskill" if not skill_ok(md) else "noowner"] += 1
            return ret9c(row, 1)
        r = cal_or(row, row["hp1"], 0x64, 1)
        n = cal_or(row, row["hp2"], 0x138 if neg != "calc144" else 0x144, 1)
        fl = (row["filt"] & M32) or 0xA783
        ctx = le32(own) + le32(MU) + le32(sk) + le32(lv) + le32(n) + le32(sub)
        br["range20"] += 1
        return obs9c(row, "ForUnitsInRange", {"ecx": game, "edx": own},
                     [x, y, r, fl, 0x005AB2A0, None, 1, 0x006E25E0, 0xEC3], 0x005AB4D6, ptrs={5: ctx})
    # hit22
    if not own:
        br["noowner"] += 1
        return ret9c(row, 1)
    if not skill_ok(md):
        br["noskill"] += 1
        return ret9c(row, 1)
    if not row["t"]:
        br["notarget"] += 1
        return ret9c(row, 0 if neg != "notgt1" else 1)
    br["build22"] += 1
    return obs9c(row, "BuildDamage", {"ecx": game, "edx": own}, [MU, row["t"], None], 0x005ADE82)


def ownseed_neg(model):
    """A seed control (the untouched-seed comparison is live): neg 'ownseed' moves the missile's draws to the
    owner's seed (the missile's left as written, the owner's stepped as the missile's would be)."""
    def m(row, game, br, neg=None):
        if neg != "ownseed":
            return model(row, game, br, neg)
        e = model(row, game, br, None)
        mem = dict(e[4] if e[0] == "obs" else e[3])
        if MU + 0x20 in mem and mem[MU + 0x20] != seeds_mem(row)[MU + 0x20]:     # only where the missile drew
            mem[MU + 0x20], mem[OWN + 0x20] = seeds_mem(row)[MU + 0x20], mem[MU + 0x20]
        return e[:4] + (mem,) + e[5:] if e[0] == "obs" else e[:3] + (mem,) + e[4:]
    return m


CHECKS.update({
    "area9c": check9b("area9c", ownseed_neg(area9c_model), ["calc64", "noresult", "hp1pos", "stat86", "nolen", "ownseed"],
                      [RS_HASH, RS_SKN, RS_CALC_JT, RS_BITMASK, RS_JT8C70, RS_JT8F20]),
    "holy9c": check9b("holy9c", ownseed_neg(holy9c_model), ["nocap", "undead8", "noroll", "always2", "ownseed"],
                      [RS_HASH, RS_SKN, RS_CALC_JT, RS_BITMASK9C]),
    "create9c": check9b("create9c", create9c_model, ["ge0", "count0", "vel", "leftpos"],
                        [RS_HASH, RS_SKN, RS_CALC_JT, RS_RING16, RS_RING64]),
    "state9c": check9b("state9c", state9c_model, ["state_lt", "le", "nolvl", "swapcalc"],
                       [RS_HASH, RS_SKN, RS_CALC_JT, RS_BITMASK9C]),
    "range9c": check9b("range9c", range9c_model, ["tgt_inv", "left_lt0", "calc144", "notgt1"],
                       [RS_HASH, RS_SKN, RS_CALC_JT, RS_TOWN]),
})

PINS9C = [  # (address, mnemonic, operand substring): instructions the 9c claims turn on (ADR-0015 (5))
    (0x005A9AD6, "jg", ""), (0x005A9E6D, "jne", ""),                                 # hit 1: > 0; hit 44: != 0
    (0x005A9EAE, "mov", "eax,DWORD PTR [ecx+0x64]"), (0x005A9B15, "mov", "eax,DWORD PTR [ecx+0x138]"),
    (0x005AA091, "shl", "esi,0x8"), (0x005AA09C, "shl", "eax,0x8"), (0x005AA0A1, "sub", "edx,esi"),   # hit 7
    (0x005AA0B1, "jg", ""), (0x005AA0DD, "jl", ""),
    (0x00554301, "mov", "dl,BYTE PTR ds:0x6ce26c"),                                  # TargetPet mask 2
    (0x005AA795, "cmp", "eax,0x1"), (0x005AA804, "push", "0x88583"),                 # hit 12
    (0x005AAEB9, "cmp", "ebx,0x5"), (0x005AB1B3, "cmp", "eax,0x5"),                  # hits 16, 19: max(.., 5)
    (0x005AB073, "cmp", "edi,eax"), (0x005AB075, "jle", ""),                         # hit 17
    (0x005AB57C, "jg", ""),                                                           # hit 21: state <= count
    (0x005ABAD0, "cmp", "eax,edx"), (0x005ABAD2, "jge", ""),                         # hit 28: d2 < r*r
    (0x005ABBC2, "lea", "ebx,[edi*4+0x0]"), (0x005ABC0F, "cmp", "esi,0x100"),        # hit 29
    (0x005AB7D4, "shl", "ecx,0x7"), (0x005AB7FF, "cmp", "esi,0x20"),                 # hit 25's helper
    (0x005AA700, "and", "bl,0x4"), (0x005AA6E8, "call", "0x5aa5b0"),                 # hit 10
    (0x005B0826, "jle", ""),                                                          # hit 4: > 0
]


def cmd_static9c(a):
    rep = Report("static")
    rep.batch = "9C"
    A = S4.asm()
    for va, mn, sub in PINS9C:
        ins = A.at(va)
        rep.c["pins"] += 1
        if ins is None or ins[0] != mn or sub not in ins[1]:
            rep.bad("pin 0x%08X: %r, want %s %s" % (va, ins, mn, sub))
        else:
            rep.c["pins_ok"] += 1
    for lo, n, name in ((BITMASK, 128, "g_BitMask32"), (0x006E10E0, 20, "hash offsets"),
                        (0x006C1164, 88, "CALC_Eval jump table"), (0x006426C0, 8 + 0x6D, "town tables"),
                        (RING16[1], 64, "hit 25 offsets"), (RING64[1], 512, "hit 29 offsets")):
        sec = S4.section_of(lo)
        flags = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.c["ro_reads"] += 1
        if flags & 0x80000000:
            rep.bad("%s 0x%08X in writable %s" % (name, lo, sec))
        rep.notes.append("%s 0x%08X: %s" % (name, lo, sec))
    rep.notes.append("hit 25 offsets x: %s" % " ".join(str(s32(S4.dword(RING16[0] + 4 * i))) for i in range(8)))
    rep.notes.append("hit 25 offsets y: %s" % " ".join(str(s32(S4.dword(RING16[1] + 4 * i))) for i in range(8)))
    rep.notes.append("hit 29 offsets x: %s" % " ".join(str(s32(S4.dword(RING64[0] + 4 * i))) for i in range(64)))
    rep.notes.append("hit 29 offsets y: %s" % " ".join(str(s32(S4.dword(RING64[1] + 4 * i))) for i in range(64)))
    rep.notes.append("hit table 0..30: %s" % " ".join("%d:0x%08X" % (i, S4.dword(HIT_TABLE + 4 * i))
                                                     for i in range(31)))
    rep.notes.append("hit table count 0x0073C83C: %d" % S4.dword(0x0073C83C))
    for name, va in sorted(FN9C.items(), key=lambda kv: kv[1]):
        rep.c["table_entries"] += 1
        if S4.dword(HIT_TABLE + 4 * int(name[3:])) != va:
            rep.bad("%s: table entry 0x%08X, model address 0x%08X" % (name, S4.dword(HIT_TABLE + 4 * int(name[3:])),
                                                                      va))
    print("CAT9C static " + " ".join("%s=%d" % (k, rep.c[k]) for k in sorted(rep.c)))
    for n in rep.notes:
        print("  " + n)
    return 1 if rep.c["bad"] else 0


# ##################################################################################################################
# Batch 9d (plan 0046): missile server hit functions 31-59 (g_MissileSrvHitFuncs) and hit 2 (tier A, carried from 9c,
# lane/p46m3 review ruling 3). 9c's conventions: the return address of every observed boundary asserted (site
# control), the missile's, the owner's and the target's seeds written and compared in every case, a boundary pointer
# argument compared by content, two or more negative controls per family (one failing >= 50 cases). A value that
# reaches a boundary only in a callee-saved register is not a boundary argument (lane/p46m3 review ruling 1): no 9d
# model compares one. Row 568's 64 948 is a static claim (`static --batch 9d`: every read of the hit table and its
# signed test).
# ##################################################################################################################
FN9D = {
    "hit31": 0x005ABD70, "hit32": 0x005ABE50, "hit33": 0x005ABEB0, "hit35": 0x005ABEE0, "hit36": 0x005ABF70,
    "hit37": 0x005AC020, "hit38": 0x005AC0A0, "hit39": 0x005AC1D0, "hit40": 0x005AC250, "hit43": 0x005AC350,
    "hit44": 0x005A9E10, "hit45": 0x005AC480, "hit47": 0x005AC550, "hit48": 0x005AC6D0, "hit50": 0x005AC800,
    "hit51": 0x005AC870, "hit52": 0x005AC940, "hit53": 0x005ACA50, "hit54": 0x005ACAF0, "hit55": 0x005ACB60,
    "hit56": 0x005ACC50, "hit57": 0x005AD970, "hit58": 0x005ACDF0, "hit59": 0x005ACF20,
    "hit2": 0x005A9D80,
}
BOUND9D = dict(BOUND9C)
BOUND9D.update({
    0x0061AED0: "RoomPinSet", 0x00624690: "SetMode", 0x005B3570: "RoomSpawnLevelMon", 0x005D5BF0: "ScatterAtTarget",
    0x005C7DB0: "RabiesApply", 0x0054E600: "PresetMonSpawn", 0x00623990: "WeaponGet", 0x00644C20: "KickMax",
    0x00408090: "Fatal",
})
BOUND_BY_NAME.update({v: k for k, v in BOUND9D.items()})
ALLBOUND.update(BOUND9D)
OBJP = OBJ + 0x400                 # the object's static path (+0x00 room)
OSK = OWN + 0x2000                 # the owner's skill list (+0x04 first node) and its nodes
RING16T = (0x006E2510, 0x006E24D0)  # MissSubRing16's 16 (x, y) directions, first ring (.rdata)
RING8B = (0x006E2A58, 0x006E2A38)   # hit 52's 8 (x, y) directions (.rdata)
RS_RING16T = (0x006E24D0, 0x006E2550, "r", "MissSubRing16's offsets 0x006E24D0/0x006E2510 (.rdata)")
RS_RING8B = (0x006E2A38, 0x006E2A78, "r", "hit 52's offsets 0x006E2A38/0x006E2A58 (.rdata)")


def mem9d(states=False):
    ex = ["dword %08x %08x" % (DT + 0xB98, SREC), "dword %08x %08x" % (DT + 0xBA0, NSREC),
          "dword %08x %08x" % (DT + 0x40, SPOOL),
          "dword %08x %08x" % (DT + 0xBCC, ISC), "dword %08x %08x" % (DT + 0xBD4, NISC),
          "dword %08x %08x" % (DT + 0xA78, MSREC), "dword %08x %08x" % (DT + 0xA80, NMON),
          "dword %08x %08x" % (DT + 0xA90, MS2REC), "dword %08x %08x" % (DT + 0xA98, NMON2)]
    if states:
        ex += ["dword %08x %08x" % (DT + 0xC4, NSTATES)]
    return mem_spec(ex, bounds=BOUND9D)


def common9d(rnd, w, p_path=0.94, room=None):
    """The case, the missile (class, path, room), its record (HitSubMissile1..4, sHitPar1..3, EType, ProgOverlay,
    CollideKill, Param1..4), the owner (its type at +0x00 and guid at +0x0C) and MissileData; -> (case, row)."""
    c = Case(FN9D[w])
    cls, invalid = pick_cls(rnd)
    has_path = rnd.random() < p_path
    st = put_missile(c, rnd, cls, path=has_path, room=room)
    subs = [rnd.choice([rnd.randrange(NREC)] * 4 + [rnd.randrange(700), 0, -1, -1, -0x8000]) for _ in range(4)]
    hp = [rnd_par(rnd) for _ in range(3)]
    ps = [rnd.choice([rnd.randint(0, 200), rnd.getrandbits(32), 0]) for _ in range(4)]
    et = rnd.choice(list(range(13)) * 2 + [13, 0xFF])
    ovl = rnd.choice([rnd.randrange(1, 200), 0, -1, rnd.randint(-0x8000, -1)])
    ck = rnd.choice([0, 1, 1, rnd.getrandbits(8)])
    if not invalid:
        put_rec9c(c, cls, hsub=subs, hp1=hp[0], hp2=hp[1], hp3=hp[2], etype=et, ovl=ovl, ckill=ck,
                  p1=ps[0], p2=ps[1], p3=ps[2], p4=ps[3])
    own = put_owner(c, rnd, 0.88)
    row = {"w": w, "invalid": invalid, "cls": cls, "st": st, "subs": subs, "hp": hp, "ps": ps, "et": et, "ovl": ovl,
           "ck": ck, "own": own, "otyp": None}
    if own:
        otyp = u32f(c, MU + 0x94)
        c.put(OWN + 0x00, le32(otyp))
        c.put(OWN + 0x0C, le32(u32f(c, MU + 0x98)))
        row["otyp"] = otyp
    return c, row


def put_sub_vel(c, rnd, row):
    """Param1 and Param2 (+0x38, +0x3C) of every record: the sub-missile row's velocity in MissSubRing16."""
    v = {}
    for i in range(NREC):
        if row["invalid"] or i != row["cls"]:
            p1 = rnd.choice([rnd.randint(0, 40), rnd.getrandbits(32)])
            c.put(MREC + 0x1A4 * i + 0x38, le32(p1))
        else:
            p1 = row["ps"][0]
        v[i] = p1
    row["p1s"] = v


def put_tgt_pos(c, rnd, row, force_path=False):
    """The hit unit's position (UnitGetSubX/Y: types 2, 4, 5 read the static path's +0x0C/+0x10 unchecked)."""
    if not row["unit"]:
        return
    tp = force_path or rnd.random() < 0.85 or row["utype"] in (2, 4, 5)
    c.put(TGT + 0x2C, le32(TGTP if tp else 0))
    tx, ty = rnd.getrandbits(16), rnd.getrandbits(16)
    if tp:
        c.put(TGTP + 0x02, le16(tx))
        c.put(TGTP + 0x06, le16(ty))
        c.put(TGTP + 0x0C, le32(rnd.getrandbits(32)))
        c.put(TGTP + 0x10, le32(rnd.getrandbits(32)))
    row["tpos"] = (tx, ty) if tp else (0, 0)
    row["tstatic"] = (u32f(c, TGTP + 0x0C), u32f(c, TGTP + 0x10)) if tp else None


def finish9d(c, rnd, row, game, cases, exp):
    row["seeds"] = put_seeds9c(c, rnd)
    cases += lines9c(c, game, row["unit"])
    exp.append(row)


def blk9d(**kw):
    """A MissileCreate block (block()) plus +0x28 (vel) and +0x54 (cb, the creation callback)."""
    vel, cb = kw.pop("vel", None), kw.pop("cb", None)
    b = bytearray(block(**kw))
    if vel is not None:
        struct.pack_into("<I", b, 0x28, vel & M32)
    if cb is not None:
        struct.pack_into("<I", b, 0x54, cb & M32)
    return bytes(b)


def level_bands(lvl, b):
    """SKILLS_LevelBands(ECX lvl, EDX bands): lvl <= 1 -> 0; bands 2-8, 9-16, 17-22, 23-28, 29+ (32-bit)."""
    if lvl <= 1:
        return 0
    if lvl > 28:
        return s32((lvl - 28) * b[4] + 6 * b[3] + 6 * b[2] + 8 * b[1] + 7 * b[0])
    if lvl > 22:
        return s32((lvl - 22) * b[3] + 6 * b[2] + 8 * b[1] + 7 * b[0])
    if lvl > 16:
        return s32((lvl - 16) * b[2] + 8 * b[1] + 7 * b[0])
    if lvl > 8:
        return s32((lvl - 8) * b[1] + 7 * b[0])
    return s32((lvl - 1) * b[0])


# =============================================================================================== heal9d
HEAL_ORDER = ("hit31", "hit43", "hit55", "hit37", "hit50")


def put_phys_rec(c, rnd, row, md):
    """Skills +0x05 (Kick bit 1), HitShift +0x1A4, SrcDam +0x1A5, MinDam/MaxDam +0x1A8/+0x1AC, the level bands
    +0x1B0/+0x1C4 (5 each), DmgSymPerCalc +0x1D8 (a constant program)."""
    row["cal"] = put_skill_calcs(c, rnd, md["skill"], (0x1D8,))
    if not skill_ok(md):
        row["srec"] = None
        return
    base = SREC + 0x23C * s16(md["skill"])
    b05 = rnd.getrandbits(8) & ~2
    if rnd.random() < 0.15 and row["own"]:
        b05 |= 2
    sh = rnd.choice([0, 0, 8, rnd.randint(1, 8), rnd.randint(9, 255)])
    src = 0 if rnd.random() < 0.9 else rnd.randint(1, 255)
    mn, mx = rnd.choice([rnd.randint(0, 30), rnd.getrandbits(32)]), rnd.choice([rnd.randint(0, 60), rnd.getrandbits(32)])
    bmin = [rnd.choice([rnd.randint(0, 10), rnd.getrandbits(32)]) for _ in range(5)]
    bmax = [rnd.choice([rnd.randint(0, 10), rnd.getrandbits(32)]) for _ in range(5)]
    c.put(base + 0x05, bytes([b05]))
    c.put(base + 0x1A4, bytes([sh]))
    c.put(base + 0x1A5, bytes([src]))
    c.put(base + 0x1A8, le32(mn))
    c.put(base + 0x1AC, le32(mx))
    for i in range(5):
        c.put(base + 0x1B0 + 4 * i, le32(bmin[i]))
        c.put(base + 0x1C4 + 4 * i, le32(bmax[i]))
    row["srec"] = {"b05": b05, "sh": sh, "src": src, "mn": mn, "mx": mx, "bmin": bmin, "bmax": bmax}


@family("heal9d", "9d")
def heal9d(rnd, game):
    """Hit 31 (firehead: the owner's life + the EType roll), 43 (healing vortex: RangeB of the skill's physical
    damage), 55 (baal inferno: the player's mana drained by sHitPar1 %), 37 (blade creeper) and 50 (plague vines)."""
    cases, exp = [], []
    for k in range(1500):
        w = HEAL_ORDER[k % 5]
        c, row = common9d(rnd, w)
        md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=small(rnd, 0, 40), range=rnd.randint(-5, 120) & 0xFFFF,
                       left=rnd.choice([rnd.randint(-5, 120), 0, rnd.getrandbits(16)]) & 0xFFFF)
        row["md"] = md
        if w == "hit55":
            row["hp"][0] = rnd.choice([rnd.randint(1, 100), 1, 100, 101, rnd.randint(101, 1000), 0, -1,
                                       rnd.getrandbits(32)])
            if not row["invalid"]:
                c.put(MREC + 0x1A4 * row["cls"] + 0x4C, le32(row["hp"][0]))
            row.update(put_hit_unit(c, rnd, types=(0, 0, 0, 0, 1, 2)))
        else:
            row.update(put_hit_unit(c, rnd))
        put_monstats(c, rnd, row)
        if w == "hit31":
            row["sv"] = put_stats(c, rnd, MU, {s: rnd.choice([rnd_stat(rnd), rnd.randint(1, 300)]) for s in STATS_DMG})
            mxh = rnd.choice([rnd.randint(1, 3000) << 8, rnd.getrandbits(32), 0])
            cur = rnd.choice([rnd.randint(0, 3000) << 8, mxh, rnd.getrandbits(32)])
            row["osv"] = put_stats(c, rnd, OWN, {6: cur, 7: mxh})
        elif w == "hit43":
            put_phys_rec(c, rnd, row, md)
            row["osv"] = put_stats(c, rnd, OWN, {0: rnd_stat(rnd), 2: rnd_stat(rnd), 12: rnd_stat(rnd)})
            if row["unit"]:
                mxh = rnd.choice([rnd.randint(1, 3000) << 8, rnd.getrandbits(32), 0])
                cur = rnd.choice([rnd.randint(0, 3000) << 8, mxh, mxh, rnd.getrandbits(32)])
                row["tsv"] = put_stats(c, rnd, TGT, {6: cur, 7: mxh})
        elif w == "hit55" and row["unit"]:
            row["tsv"] = put_stats(c, rnd, TGT, {8: rnd.choice([rnd.randint(1, 500) << 8, rnd.randint(-3, 3),
                                                                 rnd.getrandbits(32), 0])})
        row = json.loads(json.dumps(row))
        finish9d(c, rnd, row, game, cases, exp)
    return cases, mem9d(), {"cases": exp}


def isv(d):
    return {int(k): v for k, v in (d or {}).items()}


def phys9d(row, which, own):
    """SKILLS_GetPhysMin/Max(owner, skill, lvl, 1): -> ('v', value) or ('obs', name, args, site)."""
    md = row["md"]
    sk, lv = s16(md["skill"]), s16(md["lvl"])
    r = row["srec"]
    if r is None:
        return ("v", 1 if which == "min" else 2)
    osv = isv(row.get("osv"))
    if r["b05"] & 2:
        if which == "max":
            return ("obs", "KickMax", [0], 0x00647D46)
        if own and row["otyp"] == 0:
            v = s32(stat_of(osv, 2) - 20 + stat_of(osv, 0))
        else:
            v = s32(stat_of(osv, 12) * 3) if own else 0
        v = max(v, 1)
        return ("v", s32(cdiv(v, 4) << 8))
    if r["src"]:
        return ("obs", "WeaponGet", [own, 0], 0x00647C66 if which == "min" else 0x00647D66)
    bands = r["bmin"] if which == "min" else r["bmax"]
    v = s32(level_bands(lv, [s32(x) for x in bands]) + s32(r["mn"] if which == "min" else r["mx"]))
    cv = ev_skill(row["cal"], 0x1D8)
    if (row["cal"]["offs"][0] & M32) != M32 and cv:
        v = s32(v + muldiv(v, cv, 100))
    return ("v", s32(v << (r["sh"] & 31)))


def heal9d_model(row, game, br, neg=None):
    w, unit, own = row["w"], row["unit"], row["own"]
    br[w] += 1
    if w == "hit37":
        r = 2 if unit else 0
        br["ret%d" % r] += 1
        return ret9c(row, r)
    if w == "hit55":
        if not unit or row["utype"] != 0:
            br["notplayer"] += 1
            return ret9c(row, 2)
        if row["invalid"] or s32(row["hp"][0]) <= 0:
            br["norec" if row["invalid"] else "par_le0"] += 1
            return ret9c(row, 1)
        mana = stat_of(isv(row.get("tsv")), 8)
        if mana <= 0:
            br["nomana"] += 1
            return ret9c(row, 1)
        pct = s32(row["hp"][0])
        pct = 1 if pct <= 1 else (100 if pct >= 100 and neg != "pct100" else pct)
        v = muldiv(mana, pct, 100)
        d = max(v, 1) if neg != "nofloor55" else v
        d = d if d < mana else mana
        br["drain_capped" if d == mana else "drain"] += 1
        return obs9c(row, "UnitSetStat", {}, [unit, 8, s32(mana - d), 0], 0x005ACC29)
    if row["invalid"]:
        br["norec"] += 1
        return ret9c(row, 1)
    md = row["md"]
    if w == "hit50":
        el = s16(md["range"]) - s16(md["left"])
        lim = s32(s16(md["range"]) - s32(row["hp"][0]))
        if unit and (el < lim if neg != "le50" else el <= lim):
            br["ret2"] += 1
            return ret9c(row, 2)
        br["ret0"] += 1
        return ret9c(row, 0)
    if w == "hit31":
        if not own or not unit:
            br["noowner" if not own else "nounit"] += 1
            return ret9c(row, 1)
        p = bytearray(0x70)
        e, seed = elem_8c70(p, row["et"], row, svi(row), tuple(row["seeds"][0]))
        e = s32(e)
        h = e if (e >= 0 or neg == "nofloor31") else 0
        osv = isv(row["osv"])
        v = s32(stat_of(osv, 6) + h)
        mx = stat_of(osv, 7)
        if not v < mx:
            v = mx
            br["capped"] += 1
        br["heal_owner"] += 1
        return obs9c(row, "UnitSetStat", {}, [OWN, 6, v, 0], 0x005ABE1C, seed)
    # hit43
    if not unit:
        br["nounit"] += 1
        return ret9c(row, 1)
    if not skill_ok(md):
        br["noskill"] += 1
        return ret9c(row, 1)
    mn = phys9d(row, "min", own)
    if mn[0] == "obs":
        br["min_" + mn[1]] += 1
        return obs9c(row, mn[1], {}, mn[2], mn[3])
    mx = phys9d(row, "max", own)
    if mx[0] == "obs":
        br["max_" + mx[1]] += 1
        return obs9c(row, mx[1], {}, mx[2], mx[3])
    s0 = row["seeds"][0]
    r, l2, h2 = rangeb(s0[0], s0[1], s32(mx[1] - mn[1]))
    seed = (l2, h2)
    h = s32(r + mn[1])
    tsv = isv(row.get("tsv"))
    life, mxh = stat_of(tsv, 6), stat_of(tsv, 7)
    if life != mxh and s16(row["ovl"]) > 0:
        br["overlay"] += 1
        return obs9c(row, "OverlaySet", {}, [unit, s16(row["ovl"]), 0], 0x005AC452, seed)
    v = s32(life + h)
    if not v < mxh and neg != "nocap43":
        v = mxh
        br["capped"] += 1
    br["heal_unit_drew" if seed != tuple(s0) else "heal_unit"] += 1
    return obs9c(row, "UnitSetStat", {}, [unit, 6, v, 0], 0x005AC468, seed)


# =============================================================================================== create9d
CREATE9D_ORDER = ("hit2", "hit36", "hit48", "hit51", "hit52", "hit58", "hit59")


@family("create9d", "9d")
def create9d(rnd, game):
    """Hit 2 and 59 (MissSubRing16, up to its first MissileCreate), 36 (MissileCreateAt at the end of life), 48, 51,
    52 and 58 (up to the first MissileCreate; 58 re-seeds the missile and draws two offsets)."""
    cases, exp = [], []
    for k in range(2100):
        w = CREATE9D_ORDER[k % 7]
        c, row = common9d(rnd, w, p_path=1.0 if w == "hit48" else 0.94)
        if w in ("hit2", "hit59"):
            put_sub_vel(c, rnd, row)
        if w == "hit58":
            row["hp"][0] = rnd.choice([rnd.randint(-2, 20), 10, 0, rnd.getrandbits(32)])
            if not row["invalid"]:
                c.put(MREC + 0x1A4 * row["cls"] + 0x4C, le32(row["hp"][0]))
        md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=small(rnd, 0, 40))
        row["md"] = md
        if w == "hit48":
            row["p10"], row["p12"] = rnd.getrandbits(16), rnd.getrandbits(16)
            c.put(MP + 0x10, le16(row["p10"]) + le16(row["p12"]))
        row.update(put_hit_unit(c, rnd, p0=0.3 if w == "hit36" else 0.08))
        if w == "hit2":
            put_tgt_pos(c, rnd, row)
        row = json.loads(json.dumps(row))
        finish9d(c, rnd, row, game, cases, exp)
    return cases, mem9d(), {"cases": exp}


def ring16_9d(row, game, own, src, sx, sy, a5, a6, a7, neg=None):
    """sub_005A9370_MissSubRing16(ECX game, EDX owner; src, cls, skill, lvl, a5, a6, a7) up to its first
    MissileCreate (@0x005A945D): -> the outcome, or None when it returns 0."""
    md = row["md"]
    s1 = s16(row["subs"][0])
    if not 0 <= s1 < NREC or not own or not src:
        return None
    a7 = s32(a7)
    fl, loops = (0x1F, a7) if a7 > 0 and neg != "loops0" else (0x17, None)
    kw = dict(flags=fl, owner=own, source=src, cls=s1, x=sx, y=sy, skill=s16(md["skill"]), lvl=s16(md["lvl"]),
              tx=S4.dword(RING16T[0]), ty=S4.dword(RING16T[1]), vel=(row["p1s"][str(s1)] << 7))
    if loops is not None:
        kw["loops"] = loops
    return obs9c(row, "MissileCreate", {"ecx": game}, [], 0x005A945D, blk=blk9d(**kw))


def create9d_model(row, game, br, neg=None):
    w, md, st, own, unit = row["w"], row["md"], row["st"], row["own"], row["unit"]
    br[w] += 1
    s1 = s16(row["subs"][0])
    sk, lv = s16(md["skill"]), s16(md["lvl"])
    x, y = subxy(st)
    if w == "hit2":
        if row["invalid"] or s1 < 0:
            br["norec" if row["invalid"] else "sub_neg"] += 1
            return ret9c(row, 3)
        src = unit if unit and neg != "ring_self" else MU
        if src == MU:
            sx, sy = x, y
        else:
            pos = unit_pos9c(row)
            sx, sy = pos if pos else (0, 0)
        e = ring16_9d(row, game, own, src, sx, sy, row["hp"][0], row["hp"][1], row["hp"][2], neg)
        if e is None:
            br["ring_refused"] += 1
            return ret9c(row, 3)
        br["ring_unit" if unit else "ring_self"] += 1
        return e
    if row["invalid"] or s1 < 0:
        br["norec" if row["invalid"] else "sub_neg"] += 1
        return ret9c(row, 1)
    if w == "hit36":
        if unit:
            br["unit_ret0"] += 1
            return ret9c(row, 0)
        br["create_at"] += 1
        return obs9c(row, "MissileCreateAt", {"ecx": game, "edx": own}, [sk, lv, s1, x, y], 0x005ABFF2)
    if w == "hit48":
        br["create48"] += 1
        return obs9c(row, "MissileCreate", {"ecx": game}, [], 0x005AC7E6,
                     blk=blk9d(flags=0x21, owner=own, cls=s1, x=x, y=y, skill=sk, lvl=lv, tx=row["p10"],
                               ty=row["p12"]))
    if w == "hit51":
        br["create51"] += 1
        return obs9c(row, "MissileCreate", {"ecx": game}, [], 0x005AC8FB,
                     blk=blk9d(owner=own, source=MU, cls=s1, skill=sk, lvl=lv))
    if not own:
        br["noowner"] += 1
        return ret9c(row, 1)
    if w == "hit52":
        kw = dict(flags=2, owner=own, source=MU, skill=sk, lvl=lv, tx=S4.dword(RING8B[0]), ty=S4.dword(RING8B[1]))
        if neg == "cls52":
            kw["cls"] = s1
        br["create52"] += 1
        return obs9c(row, "MissileCreate", {"ecx": game}, [], 0x005ACA0D, blk=blk9d(**kw))
    if w == "hit58":
        r = s32(row["hp"][0])
        r = r if r >= 1 else 1
        lo, hi = x & M32, 666
        n = s32(2 * r + 1)
        dx, lo, hi = rrange(lo, hi, n)
        dy, lo, hi = rrange(lo, hi, n)
        if neg == "swap58":
            dx, dy = dy, dx
        br["create58"] += 1
        return obs9c(row, "MissileCreate", {"ecx": game}, [], 0x005ACF0A, (lo, hi),
                     blk=blk9d(flags=0x20, owner=own, source=MU, skill=sk, lvl=lv, cls=s1, tx=s32(dx + x - r),
                               ty=s32(dy + y - r)))
    # hit59
    a5 = s32(row["hp"][0])
    e = ring16_9d(row, game, own, MU, x, y, a5 if a5 >= 1 else 1, 2, 0, neg)
    if e is None:
        br["ring_refused"] += 1
        return ret9c(row, 1)
    br["ring59"] += 1
    return e


# =============================================================================================== nova9d
NOVA_ORDER = ("hit38", "hit45", "hit40")


@family("nova9d", "9d")
def nova9d(rnd, game):
    """Hits 38 and 45 (sub_0056D4E0_MissNovaCreate up to its first MissileCreate, or its fatal path) and 40 (up to
    sub_005D5BF0_MissScatterAtTarget)."""
    cases, exp = [], []
    for k in range(1500):
        w = NOVA_ORDER[k % 3]
        c, row = common9d(rnd, w)
        hp1 = rnd.choice([rnd.randint(1, 40), rnd.randint(-5, 0), rnd.randint(36, 46), rnd.getrandbits(32), 4, 10])
        hp2 = rnd.choice([0, 0, 1, 2, rnd.randint(-3, 6), rnd.getrandbits(32)])
        row["hp"][0], row["hp"][1] = hp1, hp2
        if not row["invalid"]:
            c.put(MREC + 0x1A4 * row["cls"] + 0x4C, le32(hp1) + le32(hp2))
        md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=rnd.choice([rnd.randint(0, 12), 1, 1, rnd.randint(-3, 40)]))
        row["md"] = md
        row["cal"] = put_skill_calcs(c, rnd, md["skill"], (0x144,))
        row.update(put_hit_unit(c, rnd))
        row = json.loads(json.dumps(row))
        finish9d(c, rnd, row, game, cases, exp)
    return cases, mem9d(), {"cases": exp}


def nova_n(row):
    """(lvl - 1) * sHitPar2 + sHitPar1 (32-bit), else max(calc4, 1) (None: no Skills row, returns 1)."""
    md = row["md"]
    n = s32(s32((s16(md["lvl"]) - 1) * s32(row["hp"][1])) + s32(row["hp"][0]))
    if n > 0:
        return n
    if not skill_ok(md):
        return None
    return max(ev_skill(row["cal"], 0x144), 1)


def nova9d_model(row, game, br, neg=None):
    w, md, st, own = row["w"], row["md"], row["st"], row["own"]
    br[w] += 1
    s1 = s16(row["subs"][0])
    sk, lv = s16(md["skill"]), s16(md["lvl"])
    x, y = subxy(st)
    if row["invalid"] or s1 < 0:
        br["norec" if row["invalid"] else "sub_neg"] += 1
        return ret9c(row, 1)
    if w == "hit45":
        n = s32(row["hp"][0])
        if n <= 0:
            br["par_le0"] += 1
            return ret9c(row, 1)
        cb = 0x005AC040 if (s32(row["hp"][1]) != 0 or neg == "cb45") else None
    else:
        if not own:
            br["noowner"] += 1
            return ret9c(row, 1)
        if neg == "hp_swap":
            row = dict(row, hp=[row["hp"][1], row["hp"][0], row["hp"][2]])
        n = nova_n(row)
        if n is None:
            br["noskill"] += 1
            return ret9c(row, 1)
        if w == "hit40":
            br["scatter"] += 1
            return obs9c(row, "ScatterAtTarget", {"ecx": game, "edx": MU}, [own, s1, n, cdiv(n, 4), sk, lv],
                         0x005AC334)
        cb = 0x005AC040
    if cdiv(n - 1, 5) > (7 if neg != "fatal8" else 8):
        br["fatal"] += 1
        return obs9c(row, "Fatal", {}, [0xF0D], 0x0056D50C)
    br["nova_" + w] += 1
    return obs9c(row, "MissileCreate", {"ecx": game}, [], 0x0056D539,
                 blk=blk9d(flags=3, owner=own, cls=s1, x=x, y=y, skill=sk, lvl=lv, tx=0xE, ty=-0xE, cb=cb))


# =============================================================================================== area9d
AREA9D_ORDER = ("hit47", "hit56", "hit53")


@family("area9d", "9d")
def area9d(rnd, game):
    """Hits 47 (molten boulder) and 56 (armageddon control) up to MISSILE_BuildDamage, 53 (rabies contagion) up to
    sub_005C7DB0 (the contagion's end frame against SKILLS_GetElemLen)."""
    cases, exp = [], []
    for k in range(1500):
        w = AREA9D_ORDER[k % 3]
        c, row = common9d(rnd, w)
        frame = rnd.getrandbits(32) if rnd.random() < 0.2 else rnd.randint(0, 100000)
        c.put(GAME + FRAME, le32(frame))
        d = rnd.choice([rnd.randint(-5, 30), 9, 10, 11, rnd.randint(30, 400), rnd.getrandbits(32)])
        md = put_mdata(c, rnd, skill=pick_skill(rnd), lvl=rnd.choice([rnd.randint(-2, 30), 1, 8, 9, 16, 17]),
                       w28=(frame + d) & M32)
        row.update(md=md, frame=frame)
        if w == "hit53":
            row["cal"] = put_skill_calcs(c, rnd, md["skill"], (0x224,))
            if skill_ok(md):
                base = SREC + 0x23C * s16(md["skill"])
                el = [rnd.choice([rnd.randint(0, 200), rnd.randint(0, 20), rnd.getrandbits(32)]) for _ in range(4)]
                for i, v in enumerate(el):
                    c.put(base + 0x214 + 4 * i, le32(v))
                row["el"] = el
                if rnd.random() < 0.3:      # the end frame at the length, one under or one over (the `jg` edge)
                    md["w28"] = (frame + elem_len9d(json.loads(json.dumps(row))) + rnd.choice((-1, 0, 0, 1))) & M32
                    c.put(MD + 0x28, le32(md["w28"]))
        row.update(put_hit_unit(c, rnd))
        put_monstats(c, rnd, row)
        row = json.loads(json.dumps(row))
        finish9d(c, rnd, row, game, cases, exp)
    return cases, mem9d(), {"cases": exp}


def elem_len9d(row):
    """SKILLS_GetElemLen(owner, skill, lvl, 1): ELen + the bands 1-8, 9-16, 17+ of ELevLen1..3, plus
    ELenSymPerCalc % (MulDiv) when the calc is set and non-zero."""
    md = row["md"]
    lv = s16(md["lvl"])
    if not skill_ok(md) or lv <= 0:
        return 0
    e = [s32(v) for v in row["el"]]
    if lv > 16:
        b = s32((lv - 16) * e[3] + 8 * e[2] + 7 * e[1])
    elif lv > 8:
        b = s32((lv - 8) * e[2] + 7 * e[1])
    else:
        b = s32((lv - 1) * e[1])
    v = s32(e[0] + b)
    off = row["cal"]["offs"][0] & M32
    if off != M32 and off < row["cal"]["pool"]:
        cv = ev_skill(row["cal"], 0x224)
        if cv:
            v = s32(v + muldiv(v, cv, 100))
    return v


def area9d_model(row, game, br, neg=None):
    w, md, own, unit = row["w"], row["md"], row["own"], row["unit"]
    br[w] += 1
    sk, lv = s16(md["skill"]), s16(md["lvl"])
    if w == "hit53":
        if not own or not unit:
            br["noowner" if not own else "nounit"] += 1
            return ret9c(row, 1)
        s = s32(md["w28"] - row["frame"])
        if s < 10 if neg != "s10" else s <= 10:
            br["early"] += 1
            return ret9c(row, 1)
        ln = elem_len9d(row)
        if s > ln if neg != "lenlt" else s >= ln:
            br["over_len"] += 1
            return ret9c(row, 1)
        br["apply"] += 1
        return obs9c(row, "RabiesApply", {"ecx": game, "edx": own}, [unit, s, sk, lv], 0x005ACAB9)
    if row["invalid"]:
        br["norec"] += 1
        return ret9c(row, 1)
    if not own:
        br["noowner"] += 1
        return ret9c(row, 1)
    if w == "hit56":
        br["build56"] += 1
        return obs9c(row, "BuildDamage", {"ecx": game, "edx": own}, [MU, 0 if neg != "unit56" else unit, None],
                     0x005ACD38)
    if unit and (row["utype"] != 1 or not ms2_flag(row, 11 if neg != "flag10" else 10)):
        br["pass_ret2"] += 1
        return ret9c(row, 2)
    br["build47_unit" if unit else "build47_end"] += 1
    return obs9c(row, "BuildDamage", {"ecx": game, "edx": own}, [MU, unit, None], 0x005AC609, ptrs={2: bytes(0x70)})


# =============================================================================================== event9d
EVENT_ORDER = ("hit32", "hit33", "hit35", "hit39", "hit54", "hit57")


@family("event9d", "9d")
def event9d(rnd, game):
    """Hits 32 (cairnstones portal), 33 and 35 (room pins; 35's object mode and event), 39 (imp spawn), 54 (baal
    spawn: the owner's unit skill) and 57 (baalfx control's quest test)."""
    cases, exp = [], []
    for k in range(1800):
        w = EVENT_ORDER[k % 6]
        room = rnd.choice([0x13000000 + 0x100 * rnd.randrange(16)] * 6 + [0])
        c, row = common9d(rnd, w, room=room)
        row["room"] = room if row["st"]["path"] else 0
        w28 = rnd.choice([0, 0, 1, rnd.getrandbits(32)])
        md = put_mdata(c, rnd, skill=rnd.choice([rnd.randrange(400), 0x7FFF, -1, rnd.randrange(8)]),
                       lvl=small(rnd, 0, 40), w28=w28)
        row["md"] = md
        row.update(put_hit_unit(c, rnd, p0=0.7 if w != "hit54" else 0.5))
        if w == "hit35":
            if rnd.random() < 0.8:
                put_unit_found(c, rnd, OBJ, 2, w28 & M32, decoy=(w28 ^ 0x40) & M32 if rnd.random() < 0.2 else None)
                orm = rnd.choice([0x13000000 + 0x100 * rnd.randrange(16), 0, 0])
                c.put(OBJ + 0x00, le32(2))          # the type UnitGetRoom (0x00620BB0) tests: 2 reads the static path
                c.put(OBJ + 0x2C, le32(OBJP))
                c.put(OBJP + 0x00, le32(orm))
                mode = rnd.choice([0, 0, 1, rnd.getrandbits(32)])
                c.put(OBJ + 0x10, le32(mode))
                row.update(obj=OBJ, oroom=orm, omode=mode)
            else:
                put_unit_absent(c, rnd, 2, w28 & M32)
                row["obj"] = 0
        if w == "hit54" and row["own"]:
            nodes = []
            if rnd.random() < 0.9:
                c.put(OWN + 0xA8, le32(OSK))
                n = rnd.randrange(0, 5)
                for i in range(n):
                    a = OSK + 0x100 + 0x40 * i
                    sid = s16(md["skill"]) if rnd.random() < 0.6 else rnd.randrange(400)
                    rec = OSK + 0x800 + 0x10 * i
                    c.put(a + 0x00, le32(rec))
                    c.put(rec, le16(sid))
                    v3c = 0 if rnd.random() < 0.8 else rnd.getrandbits(32)
                    v34 = rnd.choice([0xFFFFFFFF, rnd.randrange(8), rnd.getrandbits(32)])
                    v28 = rnd.choice([rnd.randint(0, 30), rnd.getrandbits(32)])
                    v18 = rnd.getrandbits(32)
                    c.put(a + 0x3C, le32(v3c))
                    c.put(a + 0x34, le32(v34))
                    c.put(a + 0x28, le32(v28))
                    c.put(a + 0x18, le32(v18))
                    nodes.append({"a": a, "sid": sid, "v3c": v3c, "v34": v34, "v28": v28, "v18": v18})
                for i in range(n):
                    c.put(OSK + 0x100 + 0x40 * i + 0x04, le32(OSK + 0x100 + 0x40 * (i + 1) if i + 1 < n else 0))
                c.put(OSK + 0x04, le32(OSK + 0x100 if n else 0))
                row["skl"] = nodes
            else:
                c.put(OWN + 0xA8, le32(0))
                row["skl"] = None
        row = json.loads(json.dumps(row))
        finish9d(c, rnd, row, game, cases, exp)
    return cases, mem9d(), {"cases": exp}


def find_unit_skill9d(row, sid, neg=None):
    """SKILLS_FindUnitSkill(EAX unit, ESI id): the node of that id with +0x3C == 0; a later match replaces the best
    one when the best is unset or the match's +0x34 is -1, is skipped when the best's +0x34 is -1, and else wins on
    a higher +0x28 (signed)."""
    if row.get("skl") is None:
        return None
    best = None
    for nd in row["skl"]:
        if nd["sid"] != sid or nd["v3c"] != 0:
            continue
        if neg == "skillfirst":
            if best is None:
                best = nd
            continue
        if best is None or nd["v34"] == 0xFFFFFFFF:
            best = nd
        elif best["v34"] == 0xFFFFFFFF:
            continue
        elif s32(nd["v28"]) > s32(best["v28"]):
            best = nd
    return best


def event9d_model(row, game, br, neg=None):
    w, md, st, own, unit = row["w"], row["md"], row["st"], row["own"], row["unit"]
    br[w] += 1
    x, y = subxy(st)
    room = row["room"]
    if w == "hit39":
        br["spawn39"] += 1
        return obs9c(row, "RoomSpawnLevelMon", {"ecx": game, "edx": room}, [x, y], 0x005AC23E)
    if w == "hit54":
        if unit or not own:
            br["unit" if unit else "noowner"] += 1
            return ret9c(row, 1)
        nd = find_unit_skill9d(row, s16(md["skill"]), neg)
        if nd is None:
            br["noskill"] += 1
            return ret9c(row, 1)
        br["spawn54"] += 1
        return obs9c(row, "PresetMonSpawn", {"ecx": game, "edx": room}, [nd["v18"], x, y, 1], 0x005ACB48)
    if unit:
        br["unit_ret0"] += 1
        return ret9c(row, 0)
    if w == "hit32":
        if row["invalid"] or md["w28"] != 0:
            br["norec" if row["invalid"] else "done"] += 1
            return ret9c(row, 0)
        br["portal"] += 1
        return obs9c(row, "PermPortalAtUnit", {"ecx": game, "edx": MU}, [row["ps"][3 if neg != "p3portal" else 2]],
                     0x005ABEA0)
    if w == "hit33":
        if not room:
            br["noroom"] += 1
            return ret9c(row, 0)
        br["pin33"] += 1
        return obs9c(row, "RoomPinSet", {}, [room, 1], 0x005ABECB)
    if w == "hit57":
        if md["w28"] != 0:
            br["done"] += 1
            return ret9c(row, 0)
        br["quest57"] += 1
        return obs9c(row, "QuestActive", {}, [game, 0x24], 0x005AD9A2, mem={MD: mdbytes(md, w28=1)})
    # hit35
    if not row["obj"]:
        br["noobj"] += 1
        return ret9c(row, 0)
    if row["oroom"]:
        br["pin35"] += 1
        return obs9c(row, "RoomPinSet", {}, [row["oroom"], 1], 0x005ABF25)
    if (row["omode"] == 0) != (neg == "mode1"):
        br["setmode"] += 1
        return obs9c(row, "SetMode", {}, [OBJ, 1], 0x005ABF33)
    br["mode_ret1"] += 1
    return ret9c(row, 1)


CHECKS.update({
    "heal9d": check9b("heal9d", ownseed_neg(heal9d_model), ["nofloor31", "nocap43", "nofloor55", "pct100", "le50",
                                                            "ownseed"],
                      [RS_HASH, RS_SKN, RS_CALC_JT, RS_BITMASK9C, RS_JT8C70]),
    "create9d": check9b("create9d", ownseed_neg(create9d_model), ["ring_self", "loops0", "cls52", "swap58",
                                                                  "ownseed"],
                        [RS_HASH, RS_RING16T, RS_RING8B]),
    "nova9d": check9b("nova9d", nova9d_model, ["cb45", "hp_swap", "fatal8"], [RS_HASH, RS_SKN, RS_CALC_JT]),
    "area9d": check9b("area9d", area9d_model, ["s10", "lenlt", "flag10", "unit56"],
                      [RS_HASH, RS_SKN, RS_CALC_JT, RS_BITMASK9C]),
    "event9d": check9b("event9d", event9d_model, ["p3portal", "skillfirst", "mode1"], [RS_HASH]),
})

PINS9D = [  # (address, mnemonic, operand substring): instructions the 9d claims turn on (ADR-0015 (5))
    (0x005ABE01, "setl", "dl"), (0x005ABE04, "sub", "edx,0x1"), (0x005ABE0D, "jl", ""),          # hit 31
    (0x005ABE87, "jne", ""), (0x005ABE93, "mov", "eax,DWORD PTR [esi+0x44]"),                     # hit 32: Param4
    (0x005AC026, "neg", "eax"), (0x005AC028, "sbb", "eax,eax"), (0x005AC02A, "and", "eax,0x2"),   # hit 37
    (0x005AC15A, "imul", "eax,DWORD PTR [edi+0x50]"), (0x005AC163, "jg", ""),                     # hit 38
    (0x005AC180, "mov", "edx,DWORD PTR [eax+0x144]"), (0x005AC14B, "mov", "DWORD PTR [ebp-0xc],0x5ac040"),
    (0x0056D4EA, "mov", "eax,0x66666667"), (0x0056D4F1, "sar", "edx,1"), (0x0056D4FA, "cmp", "eax,0x7"),
    (0x0056D500, "jle", ""), (0x0056D526, "mov", "DWORD PTR [esi+0x1c],0xe"),                    # the nova helper
    (0x005AC30B, "cdq", ""), (0x005AC30C, "and", "edx,0x3"), (0x005AC314, "sar", "eax,0x2"),      # hit 40: n / 4
    (0x005AC40E, "sub", "edx,ebx"), (0x005AC435, "je", ""), (0x005AC441, "jle", ""),              # hit 43
    (0x005AC456, "jl", ""), (0x00647CF1, "shl", "eax,cl"), (0x00647BF0, "mov", "al,ds:0x6ce26c"),
    (0x005AC4CD, "jle", ""), (0x005AC523, "je", ""),                                               # hit 45
    (0x005AC5AC, "jne", ""), (0x005AC5B5, "mov", "edx,0xb"),                                       # hit 47
    (0x005AC856, "jge", ""), (0x005AC850, "sub", "eax,DWORD PTR [esi+0x4c]"),                     # hit 50
    (0x005AC9F0, "mov", "ecx,DWORD PTR [esi+0x6e2a58]"), (0x005AC9BE, "mov", "DWORD PTR [ebp-0x58],esi"),  # hit 52
    (0x005ACA91, "cmp", "esi,0xa"), (0x005ACA94, "jl", ""), (0x005ACAA5, "jg", ""),               # hit 53
    (0x00644FD8, "jae", ""),                                                                        # GetElemLen
    (0x005ACB72, "jne", ""), (0x005ACBDD, "cmp", "eax,0x64"), (0x005ACC0C, "jge", ""),            # hit 55
    (0x005ACE8F, "lea", "edx,[edx+edx*1+0x1]"), (0x005ACE64, "call", "0x650e40"),                 # hit 58
    (0x005ACF78, "push", "0x2"), (0x005A93DC, "jle", ""), (0x005A941A, "shl", "ecx,0x7"),         # hits 59, 2 / ring
    (0x005A9DC3, "mov", "ebx,edi"), (0x005A9DFC, "mov", "eax,0x3"),
    (0x005AD987, "jne", ""), (0x005AD98A, "push", "0x1"),                                          # hit 57
]


def tabread_scan(A, rep):
    """Row 568's 64 948: every .text instruction that reads g_MissileSrvHitFuncs (0x0073C840), and the signed test
    `test ax,ax; jle` of the function word ahead of it (within 12 instructions)."""
    vas = sorted(A.ins)
    idx = {va: i for i, va in enumerate(vas)}
    sites = [va for va in vas if "0x73c840" in A.ins[va][1]]
    for va in sites:
        i = idx[va]
        back = [(vas[j], A.ins[vas[j]]) for j in range(max(0, i - 12), i)]
        t = [b for b, (mn, ops) in back if mn == "test" and ops == "ax,ax"]
        ok = False
        if t:
            nxt = vas[idx[t[-1]] + 1]
            ok = A.ins[nxt][0] == "jle"
        rep.c["tabreads"] += 1
        rep.c["tabreads_signed"] += 1 if ok else 0
        rep.notes.append("hit-table read 0x%08X: %s %s; signed test %s" % (
            va, A.ins[va][0], A.ins[va][1], ("at 0x%08X (test ax,ax; jle)" % t[-1]) if ok else "MISSING"))
        if not ok:
            rep.bad("hit-table read 0x%08X without a signed test" % va)


def cmd_static9d(a):
    rep = Report("static")
    rep.batch = "9D"
    A = S4.asm()
    for va, mn, sub in PINS9D:
        ins = A.at(va)
        rep.c["pins"] += 1
        if ins is None or ins[0] != mn or sub not in ins[1]:
            rep.bad("pin 0x%08X: %r, want %s %s" % (va, ins, mn, sub))
        else:
            rep.c["pins_ok"] += 1
    for lo, n, name in ((BITMASK, 128, "g_BitMask32"), (0x006E10E0, 20, "hash offsets"),
                        (0x006C1164, 88, "CALC_Eval jump table"), (RING16T[1], 128, "MissSubRing16 offsets"),
                        (RING8B[1], 64, "hit 52 offsets")):
        sec = S4.section_of(lo)
        flags = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.c["ro_reads"] += 1
        if flags & 0x80000000:
            rep.bad("%s 0x%08X in writable %s" % (name, lo, sec))
        rep.notes.append("%s 0x%08X: %s" % (name, lo, sec))
    rep.notes.append("MissSubRing16 offsets x: %s" % " ".join(str(s32(S4.dword(RING16T[0] + 4 * i))) for i in range(17)))
    rep.notes.append("MissSubRing16 offsets y: %s" % " ".join(str(s32(S4.dword(RING16T[1] + 4 * i))) for i in range(17)))
    rep.notes.append("hit 52 offsets x: %s" % " ".join(str(s32(S4.dword(RING8B[0] + 4 * i))) for i in range(8)))
    rep.notes.append("hit 52 offsets y: %s" % " ".join(str(s32(S4.dword(RING8B[1] + 4 * i))) for i in range(8)))
    rep.notes.append("hit table 30..70: %s" % " ".join("%d:0x%08X" % (i, S4.dword(HIT_TABLE + 4 * i))
                                                      for i in range(30, 71)))
    rep.notes.append("hit table count 0x0073C83C: %d" % S4.dword(0x0073C83C))
    for name, va in sorted(FN9D.items(), key=lambda kv: kv[1]):
        rep.c["table_entries"] += 1
        if S4.dword(HIT_TABLE + 4 * int(name[3:])) != va:
            rep.bad("%s: table entry 0x%08X, model address 0x%08X" % (name, S4.dword(HIT_TABLE + 4 * int(name[3:])),
                                                                      va))
    tabread_scan(A, rep)
    print("CAT9D static " + " ".join("%s=%d" % (k, rep.c[k]) for k in sorted(rep.c)))
    for n in rep.notes:
        print("  " + n)
    return 1 if rep.c["bad"] else 0


# ##################################################################################################################
# Batch sor (plan 0046 Phase 1, the sorceress class batch): the start functions 11-14 and the do functions 17-29 and
# 144 of g_SkillStartFuncs (0x00732140) and g_SkillDoFuncs (0x007322B0), with the two Inferno helpers 0x005C8CA0 and
# 0x005C8E30 they share. Every function is (ECX game, EDX unit; skill id, level), `ret 8` (the helpers take the
# missile class as a third argument, `ret 0xC`). 9c/9d's conventions: the call site of every observed boundary
# asserted (site control), the caster's and the target's seeds written and compared in every case, a boundary
# pointer argument compared by content, two or more negative controls per family (one failing >= 50 cases); a
# value that reaches a boundary only in a callee-saved register is not compared (lane/p46m3 review ruling 1), and a
# meaning a boundary callee gives to a compared word is not part of the claim (lane/p46m4 review).
# ##################################################################################################################
FNS = {
    "st11": 0x005C8FA0, "st12": 0x005C9030, "st13": 0x005C91C0, "st14": 0x005C9220,
    "do17": 0x005C9300, "do18": 0x005C9480, "do19": 0x005C9640, "do20": 0x005C9800, "do21": 0x005C98F0,
    "do22": 0x005C9B50, "do23": 0x005C9C10, "do24": 0x005C9EA0, "do25": 0x005CA030, "do26": 0x005CA1B0,
    "do28": 0x005CA3E0, "do29": 0x005CA4D0, "do144": 0x005CA910,
    "h8ca0": 0x005C8CA0, "h8e30": 0x005C8E30,
}
START_TABLE, DO_TABLE = 0x00732140, 0x007322B0
BOUNDS = dict(BOUND9D)
BOUNDS.update({
    0x005C8E30: "Inf8E30", 0x005C8CA0: "Inf8CA0", 0x00553C70: "Sub553C70", 0x00540E60: "CancelEvents",
    0x005C8C10: "Inf8C10", 0x0056E970: "ApplyTimed", 0x0056C740: "GroupClear", 0x0055B300: "PairFlags",
    0x0064D800: "WHTest", 0x0056ECB0: "SkillMissileCreate", 0x0056D940: "SpawnOwned", 0x0056E170: "RollPhys",
    0x00584420: "ObjOperate", 0x00629BB0: "ItemIsType", 0x00540710: "PartyId",
})
BOUNDS.pop(0x00554DE0)               # UnitsSameParty runs emulated here (do 25)
BOUND_BY_NAME.update({v: k for k, v in BOUNDS.items()})
ALLBOUND.update(BOUNDS)

U, UP = OWN, OWNP                  # the caster and its dynamic path
UDATA = OWN + 0x800                # its monster data (+0x28 owner link) or player data (+0x4C)
ULINK = OWN + 0x900
UINV = OWN + 0xA00                 # its inventory (+0x00 magic 0x01020304, +0x20 cursor item)
USL = SLIST[OWN]                   # its stat list (+0x5C)
T, TP = TGT, TGTP                  # the target unit and its path
TDATA = TGT + 0x800
TLINK = TGT + 0x900
TSL = SLIST[TGT]
OWNER2 = 0x12280000                # a third unit: the caster's owner (do 144's hireling swap)
ROOMS = [0x13000000 + 0x100 * i for i in range(4)]
SEEDS_S = (U + 0x20, T + 0x20)
NPET = 20                          # DataTables+0xBF0, the PetType count
DIFF = 0x12600000                  # a difficulty table (0x58 per row), g_pDifficultyLevels (0x0096C8AC)
NDIFF = 3
MISS2 = (0x0096C794, 0x0096C79C)   # the missile table and count 0x00663270 reads (.data, set at run time)
NOVA_DIR = (0x006E1288, 0x006E1388)   # NovaAtUnit's 64 target offsets x / y (.rdata)
HYDRA_OFF = (0x006E312C, 0x006E3120)  # do 144's three spawn offsets x / y (.rdata)
RS_NOVA = (0x006E1288, 0x006E1488, "r", "NovaAtUnit's offsets 0x006E1288/0x006E1388 (.rdata)")
RS_HYDRA = (0x006E3120, 0x006E3138, "r", "do 144's offsets 0x006E3120/0x006E312C (.rdata)")
RS_TOWN_S = RS_TOWN
RS_MISS2 = (MISS2[0], MISS2[1] + 4, "r", "missile table 0x0096C794 and count 0x0096C79C (.data, set in the spec)")
RS_DIFF = (0x0096C8AC, 0x0096C8B4, "r", "g_pDifficultyLevels/g_nDifficultyLevels 0x0096C8AC/0x0096C8B0 (.data, set "
           "in the spec)")
RS_DO21JT = (0x005C9B34, 0x005C9B34 + 20, "r", "do 21's type jump table 0x005C9B34 (.text)")


def mem_sor(skip=(), extra=()):
    """The DataTables fields (Skills, ISC, MonStats, States, Missiles), the pet type count, the missile table that
    0x00663270 reads and the difficulty table, then the boundaries (less `skip`: a function called directly)."""
    lines = ["dword %08x %08x" % (G_PDATATABLES, DT),
             "dword %08x %08x" % (DT + 0xB64, MREC), "dword %08x %08x" % (DT + 0xB6C, NREC),
             "dword %08x 6b3a11f5" % COOKIE,
             "dword %08x %08x" % (DT + 0xB98, SREC), "dword %08x %08x" % (DT + 0xBA0, NSREC),
             "dword %08x %08x" % (DT + 0x40, SPOOL),
             "dword %08x %08x" % (DT + 0xBCC, ISC), "dword %08x %08x" % (DT + 0xBD4, NISC),
             "dword %08x %08x" % (DT + 0xA78, MSREC), "dword %08x %08x" % (DT + 0xA80, NMON),
             "dword %08x %08x" % (DT + 0xA90, MS2REC), "dword %08x %08x" % (DT + 0xA98, NMON2),
             "dword %08x %08x" % (DT + 0xC4, NSTATES), "dword %08x %08x" % (DT + 0xBF0, NPET),
             "dword %08x %08x" % (MISS2[0], MREC), "dword %08x %08x" % (MISS2[1], NREC),
             "dword %08x %08x" % (0x0096C8AC, DIFF), "dword %08x %08x" % (0x0096C8B0, NDIFF)]
    lines += list(extra)
    lines += ["observe %08x" % a for a in sorted(BOUNDS) if a not in skip]
    lines += ["guard %08x" % a for a in FATAL + ALLOC if a not in BOUNDS]
    return lines


def lines_s(c, game, args, dumps=()):
    out = list(c.w)
    out.append("d %08x %d" % (STK_LO, STK_LEN))
    for a in SEEDS_S:
        out.append("d %08x 8" % a)
    out.append("d %08x 4" % (U + 0xC4))
    out.append("d %08x 4" % ARG2)
    for a, n in dumps:
        out.append("d %08x %d" % (a, n))
    out.append("call %08x %08x %08x" % (c.fn, game, U) + "".join(" %08x" % (a & M32) for a in args))
    return out


ARG2 = 0x7FF00008                  # the second stack argument's slot ([ebp+0xC] in the callee's frame)


def seeds_s(row, useed=None):
    s = [tuple(x) for x in row["seeds"]]
    if useed is not None:
        s[0] = tuple(useed)
    return {a: le32(v[0]) + le32(v[1]) for a, v in zip(SEEDS_S, s)}


def c4_of(row, bit6):
    return {U + 0xC4: le32(row["c4"] | (0x40 if bit6 else 0))}


def ret_s(row, eax, pop=8, bit6=False, mem=None, useed=None):
    m = seeds_s(row, useed)
    m.update(c4_of(row, bit6))
    m.update(mem or {})
    return ("ret", eax, pop, m)


def obs_s(row, name, regs, args, site, bit6=False, stk=None, ptrs=None, mem=None, useed=None):
    m = seeds_s(row, useed)
    m.update(c4_of(row, bit6))
    m.update(mem or {})
    return ("obs", name, regs, args, m, stk or {}, site, ptrs or {})


def sor_calcs(c, rnd, sid, fields, big=True):
    """put_skill_calcs with the values kept small where a loop count reads them (big False)."""
    vals = []
    for _ in fields:
        if big:
            vals.append(rnd.choice([rnd.randint(-3, 12), 1, 0, rnd.randint(-200, 300), rnd.getrandbits(32)]))
        else:
            vals.append(rnd.choice([rnd.randint(-3, 12), 1, 0, rnd.randint(13, 40), -rnd.getrandbits(31)]))
    pool = b"".join(b"\x09" + le32(v) + b"\x00" for v in vals)
    offs = [6 * i for i in range(len(fields))]
    for i in range(len(offs)):
        if rnd.random() < 0.06:
            offs[i] = rnd.choice([len(pool), 0xFFFFFFFF])
    c.put(SPOOL, pool)
    c.put(DT + 0x44, le32(len(pool)))
    if 0 <= s16(sid) < NSREC:
        sbase = SREC + 0x23C * s16(sid)
        for f, o in zip(fields, offs):
            c.put(sbase + f, le32(o))
    return {"vals": vals, "offs": offs, "pool": len(pool), "fields": list(fields)}


def sid_ok(row):
    return 0 <= s16(row["sid"]) < NSREC


def srec(row):
    return SREC + 0x23C * s16(row["sid"])


def pick_lvl(rnd):
    return rnd.choice([rnd.randint(1, 30), rnd.randint(1, 30), 0, -1, rnd.randint(31, 60)])


def put_room(c, rnd, room, town_p=0.25):
    """A room (its +0x10 -> level record -> level id), its bounds (+0x4C x, +0x50 y, +0x54 w, +0x58 h) and its
    near-room list (+0x00 array, +0x24 count). -> {room: (lid, x0, y0, w, h)} for the rooms written."""
    i = ROOMS.index(room)
    lid = rnd.choice([1, 40, 75, 103, 109]) if rnd.random() < town_p else rnd.choice([rnd.randint(2, 39),
                                                                                     rnd.randint(41, 74), 0, 200])
    rlev, lev = 0x13100000 + 0x100 * i, 0x13200000 + 0x1000 * i
    c.put(room + 0x10, le32(rlev))
    c.put(rlev + 0x58, le32(lev))
    c.put(lev + 0x1D0, le32(lid))
    return lid


def put_world_rooms(c, rnd, row):
    """All four rooms with level ids, bounds around (bx, by), and near lists."""
    bx, by = rnd.randint(1000, 30000), rnd.randint(1000, 30000)
    rooms = {}
    for i, r in enumerate(ROOMS):
        lid = put_room(c, rnd, r)
        x0, y0 = bx + 40 * (i % 2), by + 40 * (i // 2)
        w, h = rnd.choice([40, 40, 0, rnd.randint(1, 60)]), rnd.choice([40, 40, rnd.randint(1, 60)])
        c.put(r + 0x4C, le32(x0) + le32(y0) + le32(w) + le32(h))
        rooms[r] = [lid, x0, y0, w, h]
    for i, r in enumerate(ROOMS):
        n = rnd.randrange(0, 5)
        arr = r + 0x80
        near = [rnd.choice(ROOMS + [0]) for _ in range(n)]
        c.put(r + 0x00, le32(arr))
        c.put(r + 0x24, le32(n))
        for j, nr in enumerate(near):
            c.put(arr + 4 * j, le32(nr))
        rooms[r].append(near)
    row["rooms"] = {str(k): v for k, v in rooms.items()}
    row["bx"], row["by"] = bx, by
    return bx, by


def room_at(row, room, x, y):
    """sub_00463740_RoomAtSubtile(ECX room, EDX x; y)."""
    if not room:
        return 0
    rr = row["rooms"]
    near = rr[str(room)][5]

    def ins(r):
        _, a, b, ww, hh, _n = rr[str(r)]
        return a <= s32(x) < s32(a + ww) and b <= s32(y) < s32(b + hh)
    if ins(room):
        return room
    for nr in near:
        if nr and ins(nr):
            return nr
    return 0


def town_of(row, room):
    if not room:
        return 0
    return is_town(row["rooms"][str(room)][0])


def put_caster(c, rnd, row, types=(0, 0, 1), room_p=0.9):
    """The caster U: type, class, guid, mode, its path (position +0x02/+0x06, target point +0x10/+0x12, room
    +0x1C, target link +0x58), +0xC4 (bit 6 cleared or set at random)."""
    ut = rnd.choice(types)
    ug = (rnd.getrandbits(32) & ~0x7F) | 0x11
    c.put(U + 0x00, le32(ut))
    ucls = rnd.choice([rnd.randrange(NMON), 271, 338, 359, 560, 561, rnd.randrange(600)])
    c.put(U + 0x04, le32(ucls))
    c.put(U + 0x0C, le32(ug))
    c.put(U + 0x2C, le32(UP))
    ux, uy = rnd.choice([rnd.getrandbits(16), rnd.randint(1, 0x7FFF)]), rnd.getrandbits(16)
    if rnd.random() < 0.03:
        ux = 0
    c.put(UP + 0x02, le16(ux))
    c.put(UP + 0x06, le16(uy))
    px, py = rnd.getrandbits(16), rnd.getrandbits(16)
    if rnd.random() < 0.06:
        px = 0
    if rnd.random() < 0.06:
        py = 0
    c.put(UP + 0x10, le16(px) + le16(py))
    uroom = rnd.choice(ROOMS) if rnd.random() < room_p else 0
    c.put(UP + 0x1C, le32(uroom))
    c4 = rnd.getrandbits(32)
    c.put(U + 0xC4, le32(c4))
    row.update(ut=ut, ucls=ucls, ug=ug, ux=ux, uy=uy, px=px, py=py, uroom=uroom, c4=c4)


def put_target(c, rnd, row, game, types=(0, 1, 1, 1, 2, 3, 4, 5)):
    """U's path target: none, U itself, T (found, stale or a picked-up item). T: type, guid, mode, position (a
    dynamic path +0x02/+0x06 and room +0x1C, none, or for types 2, 4, 5 a static path +0x0C/+0x10 and room +0x00)."""
    k = rnd.random()
    row["tlink"] = None
    row["t"] = 0
    if k < 0.2:
        c.put(UP + 0x58, le32(0))
        return
    if k < 0.26:
        c.put(UP + 0x58, le32(U))
        c.put(UP + 0x5C, le32(row["ut"]))
        c.put(UP + 0x60, le32(row["ug"]))
        put_unit_found(c, rnd, U, row["ut"], row["ug"])
        row["tlink"] = "self"
        return
    tt = rnd.choice(types)
    tg = (rnd.getrandbits(32) & ~0x7F) | 0x22
    stale = rnd.random() < 0.07
    c.put(UP + 0x58, le32(T))
    c.put(UP + 0x5C, le32(tt))
    c.put(UP + 0x60, le32(tg))
    if stale:
        put_unit_absent(c, rnd, tt, tg)
        row["tlink"] = "stale"
        return
    put_unit_found(c, rnd, T, tt, tg, decoy=(tg ^ 0x80) if rnd.random() < 0.2 else None)
    c.put(T + 0x00, le32(tt))
    mode = rnd.choice([rnd.randrange(0, 12), 1, 2, 3])
    c.put(T + 0x10, le32(mode))
    row.update(tt=tt, tg=tg, tmode=mode)
    if tt == 4 and mode in (1, 2):
        row["tlink"] = "item_taken"
        return
    row["tlink"] = "t"
    row["t"] = T
    if tt in (2, 4, 5):
        c.put(T + 0x2C, le32(TP))
        tx, ty = rnd.choice([rnd.getrandbits(32), rnd.randint(1, 0x7FFF), 0]), rnd.choice([rnd.randint(1, 0x7FFF),
                                                                                            rnd.getrandbits(32)])
        troom = rnd.choice(ROOMS + [0])
        c.put(TP + 0x0C, le32(tx))
        c.put(TP + 0x10, le32(ty))
        c.put(TP + 0x00, le32(troom))
        row.update(tx=tx, ty=ty, troom=troom)
        return
    if rnd.random() < 0.9:
        c.put(T + 0x2C, le32(TP))
        tx, ty = rnd.getrandbits(16), rnd.getrandbits(16)
        if rnd.random() < 0.04:
            tx = 0
        troom = rnd.choice(ROOMS + [0])
        c.put(TP + 0x02, le16(tx))
        c.put(TP + 0x06, le16(ty))
        c.put(TP + 0x1C, le32(troom))
        row.update(tx=tx, ty=ty, troom=troom)
    else:
        c.put(T + 0x2C, le32(0))
        row.update(tx=0, ty=0, troom=0)


def tgt_unit(row):
    """UNIT_GetTargetUnit(game, U) after sub_00553490_PathTargetRevalidate."""
    return row["t"]


def target_xy(row):
    """SKILLS_GetTargetXY: the target unit's position, else U's path target point (+0x10/+0x12). -> (x, y, ok)."""
    if row["t"]:
        x, y = row["tx"], row["ty"]
    else:
        x, y = row["px"], row["py"]
    return x, y, int(x != 0 and y != 0)


def room_of_t(row):
    return row.get("troom", 0) if row["t"] else 0


def put_seeds_s(c, rnd, row):
    s = [(rnd.getrandbits(32), rnd.getrandbits(32)) for _ in SEEDS_S]
    for a, v in zip(SEEDS_S, s):
        c.put(a, le32(v[0]) + le32(v[1]))
    row["seeds"] = s


def put_state_list_s(c, rnd, unit, sl, state, p_found=0.4, stat=None):
    """unit+0x5C -> a list (+0x10 bit 31) whose chains +0x3C/+0x40 (next +0x2C) hold state lists (+0x14); the state
    asked among them or not; a found list carries {stat: value} in its base array (+0x24, count +0x28; +0x10 bit 31
    clear). -> (found list or 0, value or None)."""
    k = rnd.random()
    if k < 0.08:
        c.put(unit + 0x5C, le32(0))
        return 0, None
    fl = rnd.getrandbits(32) | 0x80000000
    if k < 0.15:
        fl &= 0x7FFFFFFF
    c.put(unit + 0x5C, le32(sl))
    c.put(sl + 0x10, le32(fl))
    if not fl & 0x80000000:
        return 0, None
    nodes = [sl + 0x400 + 0x80 * i for i in range(6)]
    want = rnd.random() < p_found
    pos = 0
    found = 0
    for head in (0x3C, 0x40):
        n = rnd.randrange(3)
        chain = nodes[pos:pos + n]
        pos += n
        c.put(sl + head, le32(chain[0] if chain else 0))
        for i, nd in enumerate(chain):
            stv = rnd.randrange(NSTATES)
            if stv == state:
                stv = (state + 1) % NSTATES
            if want and not found:
                stv = state
                found = nd
            c.put(nd + 0x14, le32(stv))
            c.put(nd + 0x2C, le32(chain[i + 1] if i + 1 < len(chain) else 0))
    val = None
    if found and stat is not None:
        val = rnd.choice([0, 0, 1, 2, rnd.randint(3, 5), rnd.getrandbits(32)])
        c.put(found + 0x10, le32(0))
        arr = found + 0x40
        keys = sorted({(stat << 16): val, ((stat + 1) << 16): rnd.getrandbits(32)}.items())
        if rnd.random() < 0.15:
            keys = [k for k in keys if k[0] != (stat << 16)]
            val = 0
        c.put(found + 0x24, le32(arr))
        c.put(found + 0x28, le16(len(keys)))
        for i, (kk, vv) in enumerate(keys):
            c.put(arr + 8 * i, le32(kk) + le32(vv))
        c.put(ISC + 0x144 * stat + 5, b"\x00")
    return found, val


def put_relation(c, rnd, row, p_align=0.4):
    """For UnitsHostile / UnitsSameParty: T's monster data owner link (U, absent or none), U's (none or absent),
    the alignment lists of U and T (state 105 with stat 172), U's and T's +0x80 (party) for two players."""
    if row["ut"] == 1:
        c.put(U + 0x14, le32(UDATA))
        if rnd.random() < 0.2:
            c.put(UDATA + 0x28, le32(ULINK))
            c.put(ULINK + 0x28, le32(GAME))
            og = (rnd.getrandbits(32) & ~0x7F) | 0x33
            c.put(ULINK + 0x2C, le32(og))
            c.put(ULINK + 0x30, le32(0))
            c.put(hash_slot(0, og), le32(0))
        else:
            c.put(UDATA + 0x28, le32(0))
    row["towner"] = 0
    if row["t"] and row["tt"] == 1:
        k = rnd.random()
        if k < 0.15:
            c.put(T + 0x14, le32(0))
        else:
            c.put(T + 0x14, le32(TDATA))
            if k < 0.5:
                c.put(TDATA + 0x28, le32(0))
            else:
                c.put(TDATA + 0x28, le32(TLINK))
                c.put(TLINK + 0x28, le32(GAME))
                if k < 0.8:
                    c.put(TLINK + 0x2C, le32(row["ug"]))
                    c.put(TLINK + 0x30, le32(row["ut"]))
                    put_unit_found(c, rnd, U, row["ut"], row["ug"])
                    row["towner"] = U
                else:
                    og = (rnd.getrandbits(32) & ~0x7F) | 0x44
                    c.put(TLINK + 0x2C, le32(og))
                    c.put(TLINK + 0x30, le32(1))
                    c.put(hash_slot(1, og), le32(0))
    ua = put_state_list_s(c, rnd, U, USL, 105, p_found=p_align, stat=172)
    row["ualign"] = align_of(row["ut"], ua, c, U)
    if row["t"]:
        ta = put_state_list_s(c, rnd, T, TSL, 105, p_found=p_align, stat=172)
        row["talign"] = align_of(row["tt"], ta, c, T)
        if row["ut"] == 0 and row["tt"] == 0:
            c.put(U + 0x80, le32(rnd.choice([0, 0, rnd.getrandbits(32)])))
            c.put(T + 0x80, le32(rnd.choice([0, 0, rnd.getrandbits(32)])))
            row["u80"], row["t80"] = u32f(c, U + 0x80), u32f(c, T + 0x80)


def align_of(typ, found_val, c, unit):
    """0x006259B0: no stat list 0; type > 1 (unsigned) 2; else the state-105 list's stat 172, 0 without one."""
    if u32f(c, unit + 0x5C) == 0:
        return 0
    if (typ & M32) > 1:
        return 2
    found, val = found_val
    if not found:
        return 0
    return s32(val or 0)


def allied(a, b):
    """0x00650D70's alignment rule on two different units: both 0 or both 2."""
    return int((a == 0 and b == 0) or (a == 2 and b == 2))


def hostile(row, site_pair):
    """sub_00554200_UnitsHostile(ECX game, EDX U; T) -> ('v', 0/1) or ('obs', 'PairFlags', site)."""
    a = U
    au = row["ut"]
    b, bt = T, row["tt"]
    if b == T and bt == 1 and row["towner"]:
        b, bt = row["towner"], row["ut"]
    if a == b:
        return ("v", 0)
    if au == 0 and bt == 0:
        return ("obs", "PairFlags", a, b)
    al = row["ualign"]
    bl = row["talign"] if b == T else row["ualign"]
    return ("v", 0 if allied(al, bl) else 1)


def finish_s(c, rnd, row, game, cases, exp, args, dumps=()):
    if "seeds" not in row:
        put_seeds_s(c, rnd, row)
    cases += lines_s(c, game, args, dumps)
    exp.append(json.loads(json.dumps(row)))


def has_state(row, st):
    """UNIT_HasState(U, st): U type 0, 1 or 3, 0 <= st < States count, then the state bit of U's list."""
    if row["ut"] not in (0, 1, 3) or not 0 <= st < NSTATES:
        return 0
    return row["bits"].get(str(st), 0)


def put_bits(c, rnd, row, states):
    """U's state bits (the list put_stats wrote, or a bare list): {state: bit}."""
    if (U + 0x5C) not in c.fields or u32f(c, U + 0x5C) == 0:
        row["bits"] = {}
        return
    b = add_state_words(c, rnd, U, [s for s in states if 0 <= s < NSTATES])
    row["bits"] = {str(k): v for k, v in b.items()}


def ev_s(row, field):
    return ev_skill(row["cal"], field)


# ------------------------------------------------------------------------------------------- start family
START_ORDER = ("st11", "st12", "st13", "st14", "do19")


@family("start_sor", "sor")
def start_sor(rnd, game):
    """Start 11 (Inferno, Arctic Blast: state 12 or mana, then 0x005C8E30), start 12 (Telekinesis, Dragon
    Flight: the target within aurarangecalc, hostile and out of town), start 13 (Thunder Storm: the unit skill's
    +0x18/+0x1C), start 14 (Hydra: the target point's room out of town) and do 19 (Inferno: 0x005C8CA0)."""
    cases, exp = [], []
    for k in range(1500):
        w = START_ORDER[k % 5]
        c = Case(FNS[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1, 1, 3) if w == "st11" else (0, 0, 1))
        dumps = []
        if sid_ok(row):
            b = srec(row)
            miss = rnd.choice([rnd.randrange(NREC)] * 5 + [-1, NREC, rnd.randint(-0x8000, -2)])
            c.put(b + 0x48, le16(miss))
            sm = rnd.choice([6, 6, 0, rnd.randint(1, 30), rnd.randint(-0x8000, -1)])
            c.put(b + 0x184, le16(sm))
            row.update(miss=miss, sm=sm)
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x64,))
        if w == "st11":
            sm = row.get("sm", 0)
            near = rnd.choice([s16(sm) << 8, (s16(sm) << 8) - 1, (s16(sm) << 8) + 1])
            mana = rnd.choice([rnd.randint(0, 3000) << 8, near, near, rnd.getrandbits(32)])
            row["sv"] = {str(a): v for a, v in put_stats(c, rnd, U, {8: mana}).items()}
            put_bits(c, rnd, row, [12])
        if w in ("st12", "st14"):
            put_world_rooms(c, rnd, row)
            put_target(c, rnd, row, game)
            if w == "st12" and row["t"]:
                if rnd.random() < 0.5:     # near the caster: inside the range often
                    if row["tt"] in (2, 4, 5):
                        row["tx"] = (row["ux"] + rnd.randint(-20, 20)) & M32
                        row["ty"] = (row["uy"] + rnd.randint(-20, 20)) & M32
                        c.put(TP + 0x0C, le32(row["tx"]))
                        c.put(TP + 0x10, le32(row["ty"]))
                    elif u32f(c, T + 0x2C):
                        row["tx"] = (row["ux"] + rnd.randint(-20, 20)) & 0xFFFF
                        row["ty"] = (row["uy"] + rnd.randint(-20, 20)) & 0xFFFF
                        c.put(TP + 0x02, le16(row["tx"]))
                        c.put(TP + 0x06, le16(row["ty"]))
                rv = abs(ev_s(row, 0x64)) if sid_ok(row) else 0
                if rnd.random() < 0.45 and 1 <= rv <= 0x3000:      # exactly r away on x, or one off (the `jg` edge)
                    d = rv + rnd.choice((-1, 0, 0, 1))
                    if row["tt"] in (2, 4, 5):
                        row["tx"], row["ty"] = (row["ux"] + d) & M32, row["uy"]
                        c.put(TP + 0x0C, le32(row["tx"]))
                        c.put(TP + 0x10, le32(row["ty"]))
                    elif u32f(c, T + 0x2C) and row["ux"] + d < 0x10000:
                        row["tx"], row["ty"] = row["ux"] + d, row["uy"]
                        c.put(TP + 0x02, le16(row["tx"]))
                        c.put(TP + 0x06, le16(row["ty"]))
                put_relation(c, rnd, row)
            if w == "st14" and rnd.random() < 0.85:   # the target point inside a room often
                r = row["uroom"] if row["uroom"] and rnd.random() < 0.6 else rnd.choice(ROOMS)
                _, x0, y0, ww, hh, _n = row["rooms"][str(r)]
                if ww > 0 and hh > 0:
                    x, y = x0 + rnd.randrange(ww), y0 + rnd.randrange(hh)
                    if row["t"] and row["tt"] in (2, 4, 5):
                        c.put(TP + 0x0C, le32(x))
                        c.put(TP + 0x10, le32(y))
                        row["tx"], row["ty"] = x, y
                    elif row["t"] and u32f(c, T + 0x2C):
                        c.put(TP + 0x02, le16(x))
                        c.put(TP + 0x06, le16(y))
                        row["tx"], row["ty"] = x, y
                    elif not row["t"]:
                        c.put(UP + 0x10, le16(x) + le16(y))
                        row["px"], row["py"] = x, y
        if w == "st13":
            nodes = []
            if rnd.random() < 0.9:
                c.put(U + 0xA8, le32(OSK))
                n = rnd.randrange(0, 5)
                for i in range(n):
                    a = OSK + 0x100 + 0x40 * i
                    sid = s16(row["sid"]) if rnd.random() < 0.6 else rnd.randrange(400)
                    rec = OSK + 0x800 + 0x10 * i
                    c.put(a + 0x00, le32(rec))
                    c.put(rec, le16(sid))
                    v3c = 0 if rnd.random() < 0.8 else rnd.getrandbits(32)
                    v34 = rnd.choice([0xFFFFFFFF, rnd.randrange(8), rnd.getrandbits(32)])
                    v28 = rnd.choice([rnd.randint(0, 30), rnd.getrandbits(32)])
                    v18, v1c = rnd.getrandbits(32), rnd.getrandbits(32)
                    c.put(a + 0x3C, le32(v3c))
                    c.put(a + 0x34, le32(v34))
                    c.put(a + 0x28, le32(v28))
                    c.put(a + 0x18, le32(v18) + le32(v1c))
                    nodes.append({"a": a, "sid": sid, "v3c": v3c, "v34": v34, "v28": v28, "v18": v18, "v1c": v1c})
                    dumps.append((a + 0x18, 8))
                for i in range(n):
                    c.put(OSK + 0x100 + 0x40 * i + 0x04, le32(OSK + 0x100 + 0x40 * (i + 1) if i + 1 < n else 0))
                c.put(OSK + 0x04, le32(OSK + 0x100 if n else 0))
                row["skl"] = nodes
            else:
                c.put(U + 0xA8, le32(0))
                row["skl"] = None
        finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]], dumps)
    return cases, mem_sor(), {"cases": exp}


def start_sor_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    sid, lv = s16(row["sid"]), row["lvl"]
    if w == "st14":
        room = row["uroom"]
        if not room:
            br["noroom"] += 1
            return ret_s(row, 0)
        x, y, ok = target_xy(row)
        if not ok:
            br["noxy"] += 1
            return ret_s(row, 0)
        r = room_at(row, room, x, y)
        if not r:
            br["noroomat"] += 1
            return ret_s(row, 0)
        t = town_of(row, r)
        if neg == "town14":
            t = town_of(row, room)
        br["town" if t else "ok"] += 1
        return ret_s(row, (0 if t else 1) if neg != "inv14" else (1 if t else 0))
    if w == "st12":
        t = tgt_unit(row)
        if not t:
            br["notarget"] += 1
            return ret_s(row, 0)
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_s(row, 0)
    if w == "st11":
        st = has_state(row, 12)
        if neg == "nostate":
            st = 0
        if not st:
            mana = stat_of(isv(row["sv"]), 8)
            need = s16(row["sm"]) << 8
            if (mana < need) if neg != "mana_le" else (mana <= need):
                br["lowmana"] += 1
                return ret_s(row, 0)
        miss = s16(row["miss"])
        if not 0 <= miss < NREC:
            br["nomiss"] += 1
            return ret_s(row, 0)
        br["state12" if st else "mana_ok"] += 1
        return obs_s(row, "Inf8E30", {"ecx": game, "edx": U}, [row["sid"], lv, miss], 0x005C9019)
    if w == "do19":
        miss = s16(row["miss"])
        if not 0 <= miss < NREC:
            br["nomiss"] += 1
            return ret_s(row, 0)
        br["call8ca0"] += 1
        return obs_s(row, "Inf8CA0", {"ecx": game, "edx": U}, [row["sid"], lv, miss], 0x005C9685)
    if w == "st13":
        nd = find_unit_skill9d(row, sid, "skillfirst" if neg == "skillfirst" else None)
        if nd is None:
            br["nonode"] += 1
            return ret_s(row, 0, mem={n["a"] + 0x18: le32(n["v18"]) + le32(n["v1c"]) for n in (row["skl"] or [])})
        mem = {}
        for n in row["skl"]:
            mem[n["a"] + 0x18] = (le32(0xFFFFFFFF) + le32(1)) if n is nd else (le32(n["v18"]) + le32(n["v1c"]))
        br["node"] += 1
        return ret_s(row, 1, mem=mem)
    # st12
    r = ev_s(row, 0x64)
    rr = s32(r * r)
    if row["tt"] in (2, 4, 5):
        tx, ty = s32(row["tx"]), s32(row["ty"])
    else:
        tx, ty = row["tx"], row["ty"]
    d = s32(s32((tx - row["ux"]) * (tx - row["ux"])) + s32((ty - row["uy"]) * (ty - row["uy"])))
    if (d > rr) if neg != "dist_ge" else (d >= rr):
        br["far"] += 1
        return ret_s(row, 0)
    if (row["tt"] & M32) > 1:
        br["nonactor_ret1"] += 1
        return ret_s(row, 1)
    h = hostile(row, None)
    if h[0] == "obs":
        br["pairflags"] += 1
        return obs_s(row, "PairFlags", {"ecx": h[2], "edx": h[3]}, [8], 0x00554297)
    if not h[1]:
        br["not_hostile"] += 1
        return ret_s(row, 0)
    if town_of(row, room_of_t(row)) or town_of(row, row["uroom"]):
        br["town"] += 1
        return ret_s(row, 0)
    br["hostile_ok"] += 1
    return ret_s(row, 1)


# ------------------------------------------------------------------------------------------- the Inferno helpers
HELP_ORDER = ("h8ca0", "h8e30")


@family("inferno_sor", "sor")
def inferno_sor(rnd, game):
    """0x005C8CA0 (Inferno's creation: the used skill's +0x18, then MissileCreate or the end-of-cast branches) and
    0x005C8E30 (start 11's: a monster's used-skill +0x18, then state 12's list), called directly."""
    cases, exp = [], []
    for k in range(1200):
        w = HELP_ORDER[k % 2]
        c = Case(FNS[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1, 1))
        row["miss"] = rnd.choice([rnd.randrange(NREC)] * 6 + [-1, NREC])
        frame = rnd.choice([rnd.randint(0, 100000), 0, 1, rnd.getrandbits(32)])
        c.put(game + FRAME, le32(frame))
        c.put(game + 0x1C, le32(0x12A00000 + rnd.randrange(16)))
        row["frame"], row["pool"] = frame, u32f(c, game + 0x1C)
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x138, 0x13C))
        dumps = []
        has_used = rnd.random() < 0.9 or (w == "h8e30" and row["ut"] == 1)
        if has_used:
            c.put(U + 0xA8, le32(OSK))
            nd = OSK + 0x100
            v18 = rnd.choice([0, 0, rnd.randint(1, 50), rnd.getrandbits(32)])
            c.put(OSK + 0x10, le32(nd))
            c.put(nd + 0x18, le32(v18))
            row["v18"] = v18
            dumps.append((nd + 0x18, 4))
        else:
            c.put(U + 0xA8, le32(rnd.choice([0, OSK])))
            if u32f(c, U + 0xA8):
                c.put(OSK + 0x10, le32(0))
            row["v18"] = None
        dumps.append((U + 0x44, 4))
        c.put(U + 0x44, le32(rnd.getrandbits(32)))
        row["u44"] = u32f(c, U + 0x44)
        if w == "h8ca0":
            put_world_rooms(c, rnd, row)
            put_target(c, rnd, row, game)
            put_stats(c, rnd, U, {0: 1}, p_nolist=0.1)
            put_bits(c, rnd, row, [12])
        else:
            f, _v = put_state_list_s(c, rnd, U, USL, 12, p_found=0.5)
            row["found12"] = f
        finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"], row["miss"]], dumps)
    return cases, mem_sor(skip=(0x005C8CA0, 0x005C8E30)), {"cases": exp}


def inferno_sor_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    sid, lv, miss = s16(row["sid"]), row["lvl"], row["miss"]
    nd = OSK + 0x100
    mem = {}
    if row["v18"] is not None:
        mem[nd + 0x18] = le32(row["v18"])
    mem[U + 0x44] = le32(row["u44"])
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_s(row, 0, 12, mem=mem)
    frame = s32(row["frame"])
    if w == "h8e30":
        if row["ut"] == 1:
            c2 = ev_s(row, 0x13C)
            if c2 < 1 and neg != "nofloor":
                c2 = 1
            mem[nd + 0x18] = le32(s32(frame + c2))
            br["monster_end"] += 1
        if row["found12"]:
            br["found12"] += 1
            return obs_s(row, "Sub553C70", {"ecx": game, "edx": U}, [1], 0x005C8F51, mem=mem)
        br["alloc"] += 1
        return obs_s(row, "StatListAlloc", {}, [row["pool"], 2, s32(frame + 0x14), row["ut"], row["ug"]],
                     0x005C8EE2, mem=mem)
    if not 0 <= miss < NREC:
        br["nomiss"] += 1
        return ret_s(row, 0, 12, mem=mem)
    x, y, ok = target_xy(row)
    if not ok:
        br["noxy"] += 1
        return ret_s(row, 0, 12, mem=mem)
    if row["v18"] is None:
        br["noused"] += 1
        return ret_s(row, 0, 12, mem=mem)
    if row["v18"] != 0 and neg != "inv18":
        c1 = ev_s(row, 0x138)
        if c1 < 1:
            c1 = 1
        blk = bytearray(blk9d(flags=0x8020, owner=U, source=U, cls=miss, tx=x, ty=y, skill=sid, lvl=lv))
        struct.pack_into("<I", blk, 0x4C, c1 & M32)
        br["create"] += 1
        return obs_s(row, "MissileCreate", {"ecx": game}, [], 0x005C8D8D, stk={"edx": (0, bytes(blk))}, mem=mem)
    mem[nd + 0x18] = le32(1)
    if row["ut"] != 1:
        br["end_player"] += 1
        return obs_s(row, "Sub553C70", {"ecx": game, "edx": U}, [1], 0x005C8DAC, mem=mem)
    mem[U + 0x44] = le32(0xB00)
    if frame >= 1 or not has_state(row, 12):
        br["end_monster_8c10"] += 1
        return obs_s(row, "Inf8C10", {}, [], 0x005C8E14, mem=mem)
    br["end_monster_cancel"] += 1
    return obs_s(row, "CancelEvents", {"ecx": game, "edx": U}, [1, 0], 0x005C8DE8, mem=mem)


# ------------------------------------------------------------------------------------------- creations
CREATE_ORDER_S = ("do17", "do22", "do24", "do26", "do28", "do20")


def put_bycharge(c, rnd, row):
    """sub_005D3CF0_SkillSrvMissileByCharge's reads: Skills +0x04 bit 2, aurastate +0x80, aurastat1 +0x54,
    srvmissile..c +0x46..+0x4C; U's list of that state and its base stat."""
    b = srec(row)
    f04 = rnd.getrandbits(8)
    if rnd.random() < 0.5:
        f04 &= ~4
    st = rnd.choice([rnd.randrange(NSTATES)] * 8 + [-1, NSTATES])
    a1 = rnd.choice([rnd.randrange(NISC)] * 8 + [-1, NISC])
    ms = [rnd.choice([rnd.randrange(NREC)] * 6 + [-1, rnd.randint(-0x8000, -2)]) for _ in range(4)]
    c.put(b + 0x04, bytes([f04]))
    c.put(b + 0x80, le16(st))
    c.put(b + 0x54, le16(a1))
    for i, m in enumerate(ms):
        c.put(b + 0x46 + 2 * i, le16(m))
    row.update(f04=f04, cst=st, ca1=a1, ms=ms, bc_found=0, bc_val=None)
    if f04 & 4 and 0 <= st < NSTATES and 0 <= a1 < NISC:
        f, v = put_state_list_s(c, rnd, U, USL, st, p_found=0.8, stat=a1)
        row["bc_found"], row["bc_val"] = f, v


def bycharge(row):
    if not sid_ok(row):
        return -1
    ms = [s16(m) for m in row["ms"]]
    if row["f04"] & 4 and 0 <= row["cst"] < NSTATES and 0 <= row["ca1"] < NISC and row["bc_found"]:
        v = s32(row["bc_val"] or 0)
        if v > 1:
            return ms[min(v, 3)]
    return ms[1]


@family("create_sor", "sor")
def create_sor(rnd, game):
    """Do 17 (Charged Bolt: calc1 creations with the re-seed callback), do 22 (Nova, Frost Nova: NovaAtUnit up to
    its first creation), do 24 (Fire Wall) and do 28 (Meteor) up to the target cell test, do 26 (Chain Lightning)
    up to SkillMissileCreate, do 20 (Static Field) up to SKILLS_ForUnitsInRange."""
    cases, exp = [], []
    for k in range(1800):
        w = CREATE_ORDER_S[k % 6]
        c = Case(FNS[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1))
        put_world_rooms(c, rnd, row)
        put_target(c, rnd, row, game)
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x138, 0x13C, 0x64, 0x224), big=(w != "do17"))
        if sid_ok(row):
            put_bycharge(c, rnd, row)
            b = srec(row)
            if w == "do20":
                el = [rnd.choice([rnd.randint(0, 200), rnd.randint(0, 20), rnd.getrandbits(32)]) for _ in range(4)]
                for i, v in enumerate(el):
                    c.put(b + 0x214 + 4 * i, le32(v))
                row["el"] = el
                et = rnd.getrandbits(8)
                filt = rnd.getrandbits(32)
                c.put(b + 0x1DC, bytes([et]))
                c.put(b + 0x50, le32(filt))
                row.update(et=et, filt=filt)
        for i in range(NREC):
            c.put(MREC + 0x1A4 * i + 0x9A, bytes([rnd.getrandbits(8), rnd.getrandbits(8)]))
            c.put(MREC + 0x1A4 * i + 0x18A, bytes([rnd.getrandbits(8)]))
        row["mvel"] = [list(c.fields[MREC + 0x1A4 * i + 0x9A]) for i in range(NREC)]
        row["msize"] = [c.fields[MREC + 0x1A4 * i + 0x18A][0] for i in range(NREC)]
        if w == "do20":
            d = rnd.choice([0, 1, 2, 3, 200, 255])
            ex = rnd.choice([0, 1, rnd.getrandbits(32)])
            c.put(game + 0x6D, bytes([d]))
            c.put(game + 0x70, le32(ex))
            for i in range(NDIFF):
                c.put(DIFF + 0x58 * i + 0x40, le32(rnd.getrandbits(32)))
            row.update(diff=d, ex=ex, d40=[u32f(c, DIFF + 0x58 * i + 0x40) for i in range(NDIFF)])
        finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]])
    return cases, mem_sor(), {"cases": exp}


def cellfree(row, miss, game, bit6):
    """sub_0056E450_SkillTargetCellFree(ECX game, EDX U; miss) up to COLL_WHTest (@0x0056E4EF)."""
    if not row["uroom"]:
        return None
    x, y, _ok = target_xy(row)
    if not x or not y:
        return None
    sz = row["msize"][miss]
    return obs_s(row, "WHTest", {}, [row["uroom"], x, y, sz, sz, 5], 0x0056E4EF, bit6=bit6)


def create_sor_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    sid, lv = s16(row["sid"]), row["lvl"]
    pre6 = w in ("do17", "do22")
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_s(row, 0, bit6=pre6)
    if w == "do20":
        d = row["diff"]
        idx = min(d if d > 0 else 0, NDIFF - 1)
        c2, c1 = ev_s(row, 0x13C), ev_s(row, 0x138)
        dv = row["d40"][idx] if row["ex"] else 0
        if neg == "noexp":
            dv = row["d40"][idx]
        el = elem_len9d({"md": {"skill": row["sid"], "lvl": lv}, "el": row["el"],
                         "cal": {"offs": [row["cal"]["offs"][3]], "pool": row["cal"]["pool"],
                                 "vals": row["cal"]["vals"], "fields": [0x224]}})
        blk = le32(c2) + le32(c1) + le32(dv) + le32(el) + le32(row["et"])
        r = ev_s(row, 0x64)
        br["static" + ("_exp" if row["ex"] else "")] += 1
        return obs_s(row, "ForUnitsInRange", {"ecx": game, "edx": U},
                     [0, 0, r, row["filt"], 0x005C96A0, None, 0, 0x006E30C4, 0x273], 0x005C98E2, ptrs={5: blk})
    if w in ("do17", "do22"):
        cls = bycharge(row)
        if neg == "charge_a":
            cls = s16(row["ms"][1])
        if not 0 <= cls < NREC:
            br["nomiss"] += 1
            return ret_s(row, 0, bit6=True)
        br["charged" if cls != s16(row["ms"][1]) else "srvmissilea"] += 1
        if w == "do22":
            vb, vl = row["mvel"][cls][0], row["mvel"][cls][1]
            v = s32(vl * lv)
            v = cdiv(v, 8) + vb
            vel = s32(v + ev_s(row, 0x138))
            fl = 3 | (4 if vel else 0)
            kw = dict(flags=fl, owner=U, cls=cls, x=row["ux"], y=row["uy"], skill=sid, lvl=lv,
                      tx=S4.dword(NOVA_DIR[0]), ty=S4.dword(NOVA_DIR[1]))
            if vel:
                kw["vel"] = vel
            br["nova"] += 1
            return obs_s(row, "MissileCreate", {"ecx": game}, [], 0x0056D4CC, bit6=True,
                         stk={"edx": (0, blk9d(**kw))})
        n = ev_s(row, 0x138)
        x, y, ok = target_xy(row)
        if n <= 0 or not ok:
            br["n0" if n <= 0 else "noxy"] += 1
            return ret_s(row, 1, bit6=True)
        blk = bytearray(blk9d(flags=0x21, owner=U, cls=cls, x=row["ux"], y=row["uy"], skill=sid, lvl=lv, tx=x,
                              ty=y, cb=0x005C9290))
        if neg == "idx1":
            struct.pack_into("<I", blk, 0x58, 1)
        br["bolt"] += 1
        return obs_s(row, "MissileCreate", {"ecx": game}, [], 0x005C9400, bit6=True, stk={"edx": (0, bytes(blk))})
    miss = s16(row["ms"][1])
    if not 0 <= miss < NREC:
        br["nomiss"] += 1
        return ret_s(row, 0)
    if w == "do26":
        c1 = ev_s(row, 0x138)
        br["chain"] += 1
        return obs_s(row, "SkillMissileCreate", {"ecx": game, "edx": miss}, [U, sid, lv, 0, 0, 0, 0, 0],
                     0x005CA230, bit6=True, mem={ARG2: le32(c1 if neg != "c1lvl" else lv)})
    bit6 = (w == "do28")
    e = cellfree(row, miss, game, bit6)
    if e is None:
        br["cell_refused"] += 1
        return ret_s(row, 0, bit6=bit6)
    br["whtest"] += 1
    return e


# ------------------------------------------------------------------------------------------- timed states
STATE_ORDER_S = ("do18", "do23", "do25", "do29")


@family("state_sor", "sor")
def state_sor(rnd, game):
    """Do 18 (the armours: up to STATE_GroupClear), do 23 (Blaze, Energy Shield: STATE_ApplyTimed on the caster),
    do 25 (Enchant: on the target when the same party, else on the caster), do 29 (Thunder Storm: the state, or the
    nearest-unit search)."""
    cases, exp = [], []
    for k in range(1600):
        w = STATE_ORDER_S[k % 4]
        c = Case(FNS[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1))
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x60,))
        dumps = []
        if sid_ok(row):
            b = srec(row)
            st = rnd.choice([rnd.randrange(NSTATES)] * 6 + [-1, NSTATES, rnd.randint(-0x8000, -2)])
            a1 = rnd.choice([rnd.randrange(NISC)] * 5 + [-1, -1, -2, NISC, rnd.randint(-0x8000, -3)])
            miss = rnd.choice([rnd.randrange(NREC)] * 6 + [-1, NREC])
            p7 = rnd.choice([rnd.randint(0, 40), rnd.getrandbits(32)])
            c.put(b + 0x80, le16(st))
            c.put(b + 0x54, le16(a1))
            c.put(b + 0x48, le16(miss))
            c.put(b + 0x160, le32(p7))
            row.update(st=st, a1=a1, miss=miss, p7=p7)
        if w == "do25":
            put_world_rooms(c, rnd, row)
            put_target(c, rnd, row, game)
            put_relation(c, rnd, row)
        if w == "do29":
            put_stats(c, rnd, U, {0: 1}, p_nolist=0.1)
            put_bits(c, rnd, row, [s16(row["st"])] if sid_ok(row) else [])
            if sid_ok(row) and 0 <= s16(row["st"]) < NSTATES and str(s16(row["st"])) in row["bits"] \
                    and (USL + 0x58) in c.fields and rnd.random() < 0.6:      # the state on more often
                st = s16(row["st"])
                wa = u32f(c, USL + 0x58) + 4 * (st >> 5)
                c.put(wa, le32(u32f(c, wa) | (1 << (st & 31))))
                row["bits"][str(st)] = 1
            nodes = []
            c.put(U + 0xA8, le32(OSK))
            n = rnd.randrange(0, 4)
            for i in range(n):
                a = OSK + 0x100 + 0x40 * i
                sid = s16(row["sid"]) if rnd.random() < 0.7 else rnd.randrange(400)
                rec = OSK + 0x800 + 0x10 * i
                c.put(a + 0x00, le32(rec))
                c.put(rec, le16(sid))
                v3c = 0 if rnd.random() < 0.85 else rnd.getrandbits(32)
                v34 = rnd.choice([0xFFFFFFFF, rnd.randrange(8), rnd.getrandbits(32)])
                v28 = rnd.choice([rnd.randint(0, 30), rnd.getrandbits(32)])
                v18, v1c = rnd.getrandbits(32), rnd.choice([0, 0, 0, 1, rnd.getrandbits(32)])
                c.put(a + 0x3C, le32(v3c))
                c.put(a + 0x34, le32(v34))
                c.put(a + 0x28, le32(v28))
                c.put(a + 0x18, le32(v18) + le32(v1c))
                nodes.append({"a": a, "sid": sid, "v3c": v3c, "v34": v34, "v28": v28, "v18": v18, "v1c": v1c})
            for i in range(n):
                c.put(OSK + 0x100 + 0x40 * i + 0x04, le32(OSK + 0x100 + 0x40 * (i + 1) if i + 1 < n else 0))
            c.put(OSK + 0x04, le32(OSK + 0x100 if n else 0))
            row["skl"] = nodes
        finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]], dumps)
    return cases, mem_sor(), {"cases": exp}


def timed_blk(owner, unit, sid, lv, ln, st, cb=0):
    return b"".join(le32(v) for v in (owner, unit, sid, lv, ln, -1, 0, st, cb))


def same_party(row):
    """sub_00554DE0_UnitsSameParty(ECX game, EDX U; T) -> ('v', 0/1) or ('obs', 'PartyId', unit)."""
    a, at = U, row["ut"]
    b, bt = T, row["tt"]
    if bt == 1 and row["towner"]:
        b, bt = row["towner"], row["ut"]
    if a == b:
        return ("v", 1)
    if at == 0 and bt == 0:
        if row["u80"]:
            return ("obs", "PartyId", U)
        if row["t80"]:
            return ("obs", "PartyId", T)
        return ("v", 0)
    al = row["ualign"]
    bl = row["talign"] if b == T else row["ualign"]
    return ("v", allied(al, bl))


def state_sor_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    sid, lv = s16(row["sid"]), row["lvl"]
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_s(row, 0)
    st, a1 = s16(row["st"]), s16(row["a1"])
    st_ok = 0 <= st < NSTATES
    if w == "do18":
        if not st_ok:
            br["nostate"] += 1
            return ret_s(row, 0)
        br["groupclear"] += 1
        return obs_s(row, "GroupClear", {"ecx": U, "edx": st}, [1], 0x005C94F9, bit6=True)
    if w in ("do23", "do25"):
        lo = -1 if neg != "a1_ge0" else 0
        if not (lo <= a1 < NISC) or not st_ok:
            br["noaura"] += 1
            return ret_s(row, 0)
        ln = ev_s(row, 0x60)
        tgt = U
        if w == "do25":
            t = tgt_unit(row)
            if t:
                p = same_party(row)
                if p[0] == "obs":
                    br["partyid"] += 1
                    return obs_s(row, "PartyId", {"edx": p[2]}, [], 0x00554E4C if p[2] == U else 0x00554E6F)
                if p[1] or neg == "party_any":
                    tgt = T
            br["enchant_" + ("target" if tgt == T else "self")] += 1
        else:
            br["self_state"] += 1
        site = 0x005C9CD4 if w == "do23" else 0x005CA11E
        return obs_s(row, "ApplyTimed", {}, [], site, stk={"ecx": (0, timed_blk(U, tgt, sid, lv, ln, st))})
    # do29
    miss = s16(row["miss"])
    if not 0 <= miss < NREC or not st_ok:
        br["norec"] += 1
        return ret_s(row, 0)
    nd = find_unit_skill9d(row, sid)
    if nd is None:
        br["nonode"] += 1
        return ret_s(row, 0)
    hs = has_state(row, st)
    if hs and (nd["v1c"] == 0 or neg == "ign1c"):
        br["strike"] += 1
        return obs_s(row, "NearestUnit", {"ecx": game, "edx": U}, [0, 0, row["p7"], 3, nd["v18"], 0], 0x005CA5AA)
    ln = ev_s(row, 0x60)
    br["storm_state" + ("_restart" if hs else "")] += 1
    return obs_s(row, "ApplyTimed", {}, [], 0x005CA672, stk={"ecx": (0, timed_blk(U, U, sid, lv, ln, st))})


# ------------------------------------------------------------------------------------------- telekinesis
@family("tk_sor", "sor")
def tk_sor(rnd, game):
    """Do 21 (Telekinesis): a player not busy, its target by type: a hostile actor out of town (the stun draw on
    the caster's seed, then SkillRollPhys), an object (OBJ_OperateDispatch), an item (its type tests), a missile."""
    cases, exp = [], []
    for k in range(1200):
        c = Case(FNS["do21"])
        row = {"w": "do21", "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 0, 0, 0, 1))
        put_world_rooms(c, rnd, row)
        for r in ROOMS:                     # out of town more often, so that the draw is reached
            if rnd.random() < 0.6:
                lid = rnd.randint(2, 39)
                c.put(0x13200000 + 0x1000 * ROOMS.index(r) + 0x1D0, le32(lid))
                row["rooms"][str(r)][0] = lid
        put_target(c, rnd, row, game, types=(0, 1, 1, 1, 1, 1, 1, 1, 2, 3, 4, 5))
        put_relation(c, rnd, row, p_align=0.75)
        c.put(U + 0x64, le32(rnd.getrandbits(32)) + le32(rnd.getrandbits(32)))
        c.put(U + 0x6C, bytes([0 if rnd.random() < 0.93 else rnd.randrange(1, 256)]))
        inv = rnd.choice([UINV] * 8 + [0])
        c.put(U + 0x60, le32(inv))
        if inv:
            c.put(UINV + 0x00, le32(0x01020304 if rnd.random() < 0.9 else rnd.getrandbits(32)))
            c.put(UINV + 0x20, le32(0 if rnd.random() < 0.95 else rnd.getrandbits(32)))
        if row["ut"] == 0:
            c.put(U + 0x14, le32(UDATA))
            c.put(UDATA + 0x4C, le32(0 if rnd.random() < 0.95 else rnd.getrandbits(32)))
        row["busy"] = int(bool(c.fields[U + 0x6C][0]) or (bool(inv) and u32f(c, UINV) == 0x01020304 and
                                                          bool(u32f(c, UINV + 0x20))) or
                          (row["ut"] == 0 and bool(u32f(c, UDATA + 0x4C))))
        put_seeds_s(c, rnd, row)
        if sid_ok(row):
            p2 = rnd.choice([rnd.randint(0, 100), 35, rnd.randint(-5, 120), rnd.getrandbits(32)])
            if rnd.random() < 0.35:          # at the draw, or one off it (the `jge` edge)
                s0 = row["seeds"][0]
                p2 = rrange(s0[0], s0[1], 100)[0] + rnd.choice((0, 0, 1, -1))
            c.put(srec(row) + 0x14C, le32(p2))
            row["p2"] = p2
        finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]])
    return cases, mem_sor(), {"cases": exp}


def tk_sor_model(row, game, br, neg=None):
    br["do21"] += 1
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_s(row, 0)
    if row["ut"] != 0:
        br["notplayer"] += 1
        return ret_s(row, 0)
    if row["busy"]:
        br["busy"] += 1
        return ret_s(row, 0)
    t = tgt_unit(row)
    if not t:
        br["notarget"] += 1
        return ret_s(row, 0)
    tt = row["tt"] & M32
    if tt > 4 or tt == 3:
        br["ret1_type%d" % min(tt, 5)] += 1
        return ret_s(row, 1, bit6=True)
    if tt == 2:
        br["object"] += 1
        return obs_s(row, "ObjOperate", {"ecx": game, "edx": U}, [2, row["tg"], None], 0x005C9B18, bit6=True)
    if tt == 4:
        br["item"] += 1
        return obs_s(row, "ItemIsType", {}, [T, 0x16], 0x005C9A8C, bit6=True)
    h = hostile(row, None)
    if h[0] == "obs":
        br["pairflags"] += 1
        return obs_s(row, "PairFlags", {"ecx": h[2], "edx": h[3]}, [8], 0x00554297, bit6=True)
    if not h[1]:
        br["not_hostile"] += 1
        return ret_s(row, 0, bit6=True)
    if town_of(row, room_of_t(row)) or town_of(row, row["uroom"]):
        br["town"] += 1
        return ret_s(row, 0, bit6=True)
    s0 = row["seeds"][0]
    r, lo, hi = rrange(s0[0], s0[1], 100)
    p2 = s32(row["p2"])
    stun = int(r < p2) if neg != "stun_le" else int(r <= p2)
    seed = (lo, hi)
    if neg == "tseed":
        seed = None
    br["stun" if stun else "nostun"] += 1
    e = obs_s(row, "RollPhys", {"ecx": U}, [row["sid"], row["lvl"]], 0x005C9A0B, bit6=True,
              stk={"edx": (0, bytes(0x70)), "ebp": (-8 & M32, le32(stun))}, useed=seed)
    if neg == "tseed":
        m = dict(e[4])
        m[T + 0x20] = le32(lo) + le32(hi)
        e = e[:4] + (m,) + e[5:]
    return e


# ------------------------------------------------------------------------------------------- hydra
@family("hydra_sor", "sor")
def hydra_sor(rnd, game):
    """Do 144 (Hydra): the summon class and mode, the pet type, the target point's room out of town, a hireling's
    owner, then the first of three SpawnOwnedMonster blocks."""
    cases, exp = [], []
    for k in range(1200):
        c = Case(FNS["do144"])
        row = {"w": "do144", "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1))
        put_world_rooms(c, rnd, row)
        put_target(c, rnd, row, game)
        if rnd.random() < 0.85 and row["uroom"]:      # the target point inside the caster's room often
            _, x0, y0, ww, hh, _n = row["rooms"][str(row["uroom"])]
            if ww > 0 and hh > 0:
                x, y = x0 + rnd.randrange(ww), y0 + rnd.randrange(hh)
                if not row["t"]:
                    c.put(UP + 0x10, le16(x) + le16(y))
                    row["px"], row["py"] = x, y
                elif row["tt"] in (2, 4, 5):
                    c.put(TP + 0x0C, le32(x))
                    c.put(TP + 0x10, le32(y))
                    row["tx"], row["ty"] = x, y
                elif u32f(c, T + 0x2C):
                    c.put(TP + 0x02, le16(x))
                    c.put(TP + 0x06, le16(y))
                    row["tx"], row["ty"] = x, y
        frame = rnd.choice([rnd.randint(0, 100000), rnd.getrandbits(32)])
        c.put(game + FRAME, le32(frame))
        row["frame"] = frame
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0xC0,))
        if sid_ok(row):
            b = srec(row)
            summ = rnd.randrange(NMON)
            mode = rnd.choice([rnd.randrange(16), rnd.randrange(16), -1, 16, rnd.randint(17, 127)])
            pet = rnd.choice([rnd.randrange(NPET)] * 12 + [-1, NPET, rnd.randint(-128, -2)])
            p1, p2 = rnd.randint(-50, 3600), rnd.randint(-2, 1500)
            c.put(b + 0xBC, le16(summ))
            c.put(b + 0xBE, bytes([pet & 0xFF, mode & 0xFF]))
            c.put(b + 0x148, le32(p1) + le32(p2))
            row.update(summ=summ, mode=mode, pet=pet, p1=p1, p2=p2)
        row["owner"] = U
        if row["ut"] == 1:
            c.put(U + 0x14, le32(UDATA))
            if rnd.random() < 0.6:
                c.put(UDATA + 0x28, le32(ULINK))
                c.put(ULINK + 0x28, le32(GAME))
                og = (rnd.getrandbits(32) & ~0x7F) | 0x55
                c.put(ULINK + 0x2C, le32(og))
                c.put(ULINK + 0x30, le32(0))
                if rnd.random() < 0.8:
                    put_unit_found(c, rnd, OWNER2, 0, og)
                    c.put(OWNER2 + 0x00, le32(0))
                    row["mowner"] = OWNER2
                else:
                    c.put(hash_slot(0, og), le32(0))
                    row["mowner"] = 0
            else:
                c.put(UDATA + 0x28, le32(0))
                row["mowner"] = 0
        finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]])
    return cases, mem_sor(), {"cases": exp}


def hireling(cls):
    return cls in (271, 338, 359, 560, 561)


def hydra_sor_model(row, game, br, neg=None):
    br["do144"] += 1
    sid, lv = s16(row["sid"]), row["lvl"]
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_s(row, 0)
    mode = row["mode"]
    mode = mode if 0 <= mode < 16 else 1
    pet = row["pet"]
    if not 0 <= pet < NPET:
        br["nopet"] += 1
        return ret_s(row, 0)
    if not row["uroom"]:
        br["noroom"] += 1
        return ret_s(row, 0)
    x, y, ok = target_xy(row)
    if not ok:
        br["noxy"] += 1
        return ret_s(row, 0)
    r = room_at(row, row["uroom"], x, y)
    if not r:
        br["noroomat"] += 1
        return ret_s(row, 0)
    if town_of(row, r):
        br["town"] += 1
        return ret_s(row, 0)
    own = U
    if row["ut"] == 1 and hireling(row["ucls"]) and row.get("mowner") and neg != "nohire":
        own = row["mowner"]
    br["owner_swap" if own != U else "own"] += 1
    life = s32((lv - 1) * row["p2"] + row["p1"]) if lv > 0 else 0
    if neg == "lvl_p2":
        life = s32(lv * row["p2"] + row["p1"]) if lv > 0 else 0
    blk = b"".join(le32(v) for v in (1, own, row["summ"], 0, mode, x + s32(S4.dword(HYDRA_OFF[0])),
                                     y + s32(S4.dword(HYDRA_OFF[1])), pet, ev_s(row, 0xC0),
                                     s32(life + row["frame"])))
    return obs_s(row, "SpawnOwned", {"ecx": game}, [], 0x005CAAA1, stk={"edx": (0, blk)})


RS_SOR = [RS_HASH, RS_SKN, RS_CALC_JT, RS_BITMASK9C, RS_TOWN]
CHECKS.update({
    "start_sor": check9b("start_sor", start_sor_model, ["nostate", "mana_le", "skillfirst", "town14", "dist_ge", "inv14"],
                         RS_SOR, md_masked=False),
    "inferno_sor": check9b("inferno_sor", inferno_sor_model, ["nofloor", "inv18"], RS_SOR, md_masked=False),
    "create_sor": check9b("create_sor", create_sor_model, ["noexp", "charge_a", "idx1", "c1lvl"],
                          RS_SOR + [RS_NOVA, RS_MISS2, RS_DIFF], md_masked=False),
    "state_sor": check9b("state_sor", state_sor_model, ["a1_ge0", "party_any", "ign1c"], RS_SOR, md_masked=False),
    "tk_sor": check9b("tk_sor", tk_sor_model, ["stun_le", "tseed"], RS_SOR + [RS_DO21JT], md_masked=False),
    "hydra_sor": check9b("hydra_sor", hydra_sor_model, ["nohire", "lvl_p2"], RS_SOR + [RS_HYDRA], md_masked=False),
})

PINS_SOR = [  # (address, mnemonic, operand substring): instructions the sor claims turn on (ADR-0015 (5))
    (0x005C8FEC, "shl", "ecx,0x8"), (0x005C8FF1, "jl", ""),                                        # start 11
    (0x005C908B, "imul", "ebx,eax"), (0x005C9169, "jg", ""), (0x005C9174, "ja", ""),             # start 12
    (0x005C91FD, "push", "0xffffffff"), (0x005C9205, "push", "0x1"),                              # start 13
    (0x005C9274, "sbb", "eax,eax"),                                                                # start 14
    (0x005C9395, "mov", "DWORD PTR [ebp-0x60],0x21"), (0x005C93C4, "mov", "DWORD PTR [ebp-0xc],0x5c9290"),
    (0x005C9405, "jl", ""),                                                                         # do 17
    (0x005C99C3, "lea", "edx,[eax+0x64]"), (0x005C99C9, "call", "0x45c390"), (0x005C99D8, "cmp", "ebx,eax"),
    (0x005C99DA, "jge", ""), (0x005C9A47, "or", "WORD PTR [ebp-0x80],0x9"), (0x005C9975, "cmp", "eax,0x4"),
    (0x006632A5, "and", "edx,0x7"), (0x006632AA, "sar", "eax,0x3"),                                # do 22's speed
    (0x0056D49D, "or", "DWORD PTR [ebp-0x5c],0x4"),
    (0x005C9C50, "cmp", "ax,0xffff"), (0x005C9C54, "jl", ""), (0x005C9CB4, "mov", "DWORD PTR [ebp-0x18],0xffffffff"),
    (0x005CA071, "cmp", "ax,0xffff"),                                                               # do 25
    (0x005C9F82, "mov", "DWORD PTR [ebp-0x6c],0x21"),                                              # do 24
    (0x005CA59C, "push", "0x3"),                                                                    # do 29
    (0x005CAA39, "or", "eax,0x1"), (0x005CAA79, "mov", "ecx,DWORD PTR [eax*4+0x6e312c]"),          # do 144
    (0x005C8D75, "mov", "DWORD PTR [ebp-0x68],0x8020"), (0x005C8D3E, "jge", ""),                  # 0x005C8CA0
    (0x005C8DCD, "jge", ""), (0x005C8EBD, "add", "eax,0x14"), (0x005C8E87, "jge", ""),             # 0x005C8E30
    (0x00611D3A, "setle", "cl"), (0x00611D4D, "jl", ""),                                            # DifficultyRec
]


def cmd_static_sor(a):
    rep = Report("static")
    rep.batch = "SOR"
    A = S4.asm()
    for va, mn, sub in PINS_SOR:
        ins = A.at(va)
        rep.c["pins"] += 1
        if ins is None or ins[0] != mn or sub not in ins[1]:
            rep.bad("pin 0x%08X: %r, want %s %s" % (va, ins, mn, sub))
        else:
            rep.c["pins_ok"] += 1
    for lo, n, name in ((BITMASK, 128, "g_BitMask32"), (0x006E10E0, 20, "hash offsets"),
                        (0x006C1164, 88, "CALC_Eval jump table"), (NOVA_DIR[0], 512, "NovaAtUnit offsets"),
                        (HYDRA_OFF[1], 24, "do 144 offsets"), (0x005C9B34, 20, "do 21 jump table"),
                        (0x006426C0, 8 + 0x6D, "town tables")):
        sec = S4.section_of(lo)
        flags = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.c["ro_reads"] += 1
        if flags & 0x80000000:
            rep.bad("%s 0x%08X in writable %s" % (name, lo, sec))
        rep.notes.append("%s 0x%08X: %s" % (name, lo, sec))
    rep.notes.append("NovaAtUnit offsets x: %s" % " ".join(str(s32(S4.dword(NOVA_DIR[0] + 4 * i))) for i in range(64)))
    rep.notes.append("NovaAtUnit offsets y: %s" % " ".join(str(s32(S4.dword(NOVA_DIR[1] + 4 * i))) for i in range(64)))
    rep.notes.append("do 144 offsets x: %s" % " ".join(str(s32(S4.dword(HYDRA_OFF[0] + 4 * i))) for i in range(3)))
    rep.notes.append("do 144 offsets y: %s" % " ".join(str(s32(S4.dword(HYDRA_OFF[1] + 4 * i))) for i in range(3)))
    rep.notes.append("do 21 jump table 0..4: %s" % " ".join("0x%08X" % S4.dword(0x005C9B34 + 4 * i) for i in range(5)))
    for lo, name in ((MISS2[0], "missile table 0x0096C794"), (MISS2[1], "missile count 0x0096C79C"),
                     (0x0096C8AC, "g_pDifficultyLevels"), (0x0096C8B0, "g_nDifficultyLevels")):
        stores = [(va, mn, ops) for va, (mn, ops) in A.ins.items()
                  if mn in ("mov", "add", "sub", "inc", "dec", "or", "and", "xor") and "PTR" in ops.split(",")[0]
                  and ("ds:0x%x" % lo) in ops.split(",")[0]]
        rep.c["data_stores"] += len(stores)
        rep.notes.append("%s: %d stores in .text%s" % (name, len(stores), "".join(" 0x%08X" % s[0] for s in stores)))
    for name, va in sorted(FNS.items(), key=lambda kv: kv[1]):
        if name.startswith("h"):
            continue
        tab = START_TABLE if name.startswith("st") else DO_TABLE
        num = int(name[2:])
        rep.c["table_entries"] += 1
        if S4.dword(tab + 4 * num) != va:
            rep.bad("%s: table entry 0x%08X, model address 0x%08X" % (name, S4.dword(tab + 4 * num), va))
    rep.notes.append("start table 11..14: %s" % " ".join("%d:0x%08X" % (i, S4.dword(START_TABLE + 4 * i))
                                                        for i in range(11, 15)))
    rep.notes.append("do table 17..29, 144: %s" % " ".join("%d:0x%08X" % (i, S4.dword(DO_TABLE + 4 * i))
                                                          for i in list(range(17, 30)) + [144]))
    print("CATSOR static " + " ".join("%s=%d" % (k, rep.c[k]) for k in sorted(rep.c)))
    for n in rep.notes:
        print("  " + n)
    return 1 if rep.c["bad"] else 0


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
    if a.batch == "9c":
        return cmd_static9c(a)
    if a.batch == "9d":
        return cmd_static9d(a)
    if a.batch == "sor":
        return cmd_static_sor(a)
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
    ap.add_argument("--batch", default="9a", choices=["9a", "9b", "9c", "9d", "sor"], help="the families of one batch (default 9a)")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    return {"cases": cmd_cases, "check": cmd_check, "static": cmd_static, "manifest": cmd_manifest}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

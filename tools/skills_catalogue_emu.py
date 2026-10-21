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

Batch nec (`--batch nec`, files under workspace/logs/skills-cat-nec/, draws from random.Random("catnec-<family>")):
the necromancer start functions 15-21 and do functions 30-32 and 55-63:
  start_nec  start 15-21, do 32 (target, town, corpse, item, revive tests)   curse_nec  do 30, 61 (the curse block)
  corpse_nec do 31, 55, 58, 59, 63                                            summon_nec do 56, 57, 60, 62 (spawn blocks)
A boundary inside a helper the batch function called is checked with the helper's return address at its stack slot.

Batch pal (`--batch pal`, files under workspace/logs/skills-cat-pal/, draws from random.Random("catpal-<family>")):
the paladin start functions 29, 31, 35, 36, 37 and do functions 64-67, 73, 79-82 and 150:
  aura_pal   do 65, 66, 81, 82 (the aura block, up to AURA_ApplyToTarget through 0x0056B740)
  melee_pal  start 29, 35, 36, 37, do 64, 79, 150 (used skill, target, queued hit)
  move_pal   start 31, do 67, 73, 80 (Charge's speed, the hammer and the fist's MissileCreate blocks)

Batch bar (`--batch bar`, files under workspace/logs/skills-cat-bar/, draws from random.Random("catbar-<family>")):
the barbarian start functions 32-34, 38-41 and do functions 2, 9, 68-72 and 74-78:
  hit_bar    start 32, 39, do 2, 9, 70 (target, town, queued hit, overlay and states, the frame parity)
  corpse_bar start 33, 34, do 69, 72, 75 (the corpse tests, state 118, the free spot)
  cry_bar    do 68, 71 (the warcries' NovaAtUnit block, Taunt's test and search)
  move_bar   start 38, 40, 41, do 74, 76-78 (the unit's skill node, the leap point, the continuations)

Batch dru (`--batch dru`, files under workspace/logs/skills-cat-dru/, draws from random.Random("catdru-<family>")):
the druid start functions 56-58 and do functions 114-124, and do-table entries 145 and 146 (States srvactivefunc):
  summon_dru do 114, 115, 119 (SkillSummonClass, the pet type, the SpawnOwnedMonster block)
  shape_dru  do 116, 120, 124, 145, 146 (the aurastate, the used skill's id, do 124's draw, the timed list, the town
             test and the re-arm of the periodic states)
  melee_dru  start 56, 57, 58, do 121, 122 (the hit tests, 0x0056E680's ResultFlags shortcut, Rabies' summed to-hit)
  miss_dru   do 117, 118, 123 (Firestorm, Twister/Tornado's 0x005C7040, Volcano's cell test with COLL_WHTest run, its
             draw)

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
            for a, b in (exp[8] if len(exp) > 8 else {}).items():     # ama: bytes at an absolute stack address
                got = stack_bytes(c, a, len(b))
                if got != b:
                    ok, why = False, "[%08x]=%s want %s" % (a, got.hex() if got else None, b.hex())
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


# ##################################################################################################################
# Batch ama (plan 0046 Phase 1, the amazon class batch): the start functions 4-10 and the do functions 6-8 and 10-16
# of g_SkillStartFuncs (0x00732140) and g_SkillDoFuncs (0x007322B0), each (ECX game, EDX unit; skill id, level),
# `ret 8`. sor's conventions: the call site of every observed boundary asserted (site control), the caster's and the
# target's seeds written and compared in every case, a boundary pointer argument compared by content, two or more
# negative controls per family (one failing >= 50 cases); no model compares a callee-saved register that is not a
# boundary argument (lane/p46m3 review ruling 1), a meaning a boundary callee gives to a compared word is not part of
# the claim (lane/p46m4 review). New here: bytes in the frame of a function that is not the boundary's direct caller
# (do 8's start point and step at the inventory query inside 0x00623990) are compared at their absolute stack address
# (each function's frame is at EBP = 0x7FEFFFFC, the entry ESP 0x7FF00000 less the pushed EBP).
# Emulated, not observed: 0x0056C4E0 (the ammunition test) with UnitGetWeapon (0x00535BC0), 0x00623C60 with
# 0x00623990 (the weapon's class), 0x00622870 (a unit's melee reach) with MonStats2Rec, SKILLS_GetToHit, GameFindUnit,
# the used skill's getters, SkillSummonClass (0x0056E620 / 0x0063EA70), and sor's UNIT_GetTargetUnit,
# SKILLS_GetTargetXY, UnitsHostile. Their inventory calls (0x0063C9B0, 0x0064F380) are boundaries.
# ##################################################################################################################
FNA = {
    "st4": 0x005DA8B0, "st5": 0x005DA8F0, "st6": 0x005DA940, "st7": 0x005DAB40, "st8": 0x005DACD0,
    "st9": 0x005DAE30, "st10": 0x005DB020,
    "do6": 0x005DB1C0, "do7": 0x005DB2D0, "do8": 0x005DB410, "do10": 0x005DB6D0, "do11": 0x005DB850,
    "do12": 0x005DBA40, "do13": 0x005DBC60, "do14": 0x005DBE50, "do15": 0x005DC000, "do16": 0x005DC1E0,
}
BOUNDS_A = dict(BOUNDS)
BOUNDS_A.update({
    0x0063C9B0: "InvQuery", 0x00580310: "HandsRefresh", 0x0064F380: "MeleeInv", 0x0057EC10: "MeleeHitTest",
    0x005A4F50: "MonAttackStats", 0x0057D4F0: "DeliverQueued", 0x00620C10: "SetPathTarget",
    0x00622C40: "InMeleeRange",
})
BOUNDS_A.pop(0x00623990)             # the weapon's class runs emulated up to its inventory query
BOUND_BY_NAME.update({v: k for k, v in BOUNDS_A.items()})
ALLBOUND.update(BOUNDS_A)
FRAME_EBP = 0x7FEFFFFC               # EBP of every function here after its `push ebp; mov ebp, esp`
UNODE = OSK + 0x100                  # the used skill's node (skill list +0x10)


def fr(off):
    """An address in the called function's frame: EBP + off."""
    return (FRAME_EBP + off) & M32


def mem_ama():
    lines = ["dword %08x %08x" % (G_PDATATABLES, DT),
             "dword %08x %08x" % (DT + 0xB64, MREC), "dword %08x %08x" % (DT + 0xB6C, NREC),
             "dword %08x 6b3a11f5" % COOKIE,
             "dword %08x %08x" % (DT + 0xB98, SREC), "dword %08x %08x" % (DT + 0xBA0, NSREC),
             "dword %08x %08x" % (DT + 0x40, SPOOL),
             "dword %08x %08x" % (DT + 0xBCC, ISC), "dword %08x %08x" % (DT + 0xBD4, NISC),
             "dword %08x %08x" % (DT + 0xA78, MSREC), "dword %08x %08x" % (DT + 0xA80, NMON),
             "dword %08x %08x" % (DT + 0xA90, MS2REC), "dword %08x %08x" % (DT + 0xA98, NMON2),
             "dword %08x %08x" % (DT + 0xC4, NSTATES), "dword %08x %08x" % (DT + 0xBF0, NPET)]
    lines += ["observe %08x" % a for a in sorted(BOUNDS_A)]
    lines += ["guard %08x" % a for a in FATAL + ALLOC if a not in BOUNDS_A]
    return lines


def obs_a(row, name, regs, args, site, bit6=False, stk=None, ptrs=None, mem=None, frame=None):
    """obs_s plus frame: {absolute stack address: bytes} compared from the stack dump (compare's exp[8])."""
    e = obs_s(row, name, regs, args, site, bit6=bit6, stk=stk, ptrs=ptrs, mem=mem)
    return e + (frame or {},)


def put_used_node(c, rnd, row, p=0.9):
    """UNIT_GetUsedSkill (0x00620250 -> 0x006439A0): U+0xA8 -> a skill list, its +0x10 the used node, whose +0x18,
    +0x1C, +0x20 the strafe and fend functions read (the count, the last target's type and guid)."""
    k = rnd.random()
    if k < p:
        c.put(U + 0xA8, le32(OSK))
        c.put(OSK + 0x10, le32(UNODE))
        n18 = rnd.choice([0, 1, rnd.randint(2, 10), rnd.getrandbits(32)])
        ty = rnd.choice([0, 1, 1, 1, 2, 3, 4, 5])
        g = (rnd.getrandbits(32) & ~0x7F) | 0x66 if rnd.random() < 0.9 else 0xFFFFFFFF
        c.put(UNODE + 0x18, le32(n18) + le32(ty) + le32(g))
        row["node"] = {"n18": n18, "ty": ty, "g": g}
    else:
        if rnd.random() < 0.5:
            c.put(U + 0xA8, le32(0))
        else:
            c.put(U + 0xA8, le32(OSK))
            c.put(OSK + 0x10, le32(0))
        row["node"] = None


def put_inv_a(c, rnd, row, p=0.5):
    inv = UINV if rnd.random() < p else 0
    c.put(U + 0x60, le32(inv))
    row["inv"] = inv


def put_reach(c, rnd, row):
    """0x00622870's monster path: MonStats +0x18 (the MonStats2 row, s16), MonStats2 +0x0E (the melee reach)."""
    if row["ut"] == 1 and rnd.random() < 0.5:      # a MonStats class in range more often
        row["ucls"] = rnd.randrange(NMON)
        c.put(U + 0x04, le32(row["ucls"]))
    m2i = [rnd.choice([rnd.randrange(NMON2)] * 6 + [NMON2, -1]) for _ in range(NMON)]
    rch = [rnd.choice([rnd.randint(0, 10), 0xFF, rnd.getrandbits(8)]) for _ in range(NMON2)]
    for i in range(NMON):
        c.put(MSREC + 0x1A8 * i + 0x18, le16(m2i[i]))
    for i in range(NMON2):
        c.put(MS2REC + 0x134 * i + 0x0E, bytes([rch[i]]))
    row.update(m2i=m2i, rch=rch)


def reach_a(row, site_ret):
    """0x00622870(unit) (from 0x0056E510, + 4 there): type 0 -> the inventory query; type 1 -> the MonStats2 row's
    +0x0E, 0xFF -> 0x0064F380, no row -> 0; any other type 0. -> ('v', r) or an expectation tuple."""
    t = row["ut"]
    if t == 0:
        return ("obs", "InvQuery", {}, [row["inv"], None, None, None], 0x006228FD)
    if t != 1:
        return ("v", 0)
    cls = row["ucls"]
    if not 0 <= cls < NMON:
        return ("v", 0)
    i = s16(row["m2i"][cls])
    if not 0 <= i < NMON2:
        return ("v", 0)
    b = row["rch"][i]
    if b == 0xFF:
        return ("obs", "MeleeInv", {}, [U, row["inv"], None, 0xFFFFFFFF, 1], 0x006228D2)
    return ("v", b)


def ammo_a(row):
    """0x0056C4E0(ECX unit): a non-player 1; a player: UnitGetWeapon -> no inventory 0, else the inventory query."""
    if row["ut"] != 0:
        return ("v", 1)
    if not row["inv"]:
        return ("v", 0)
    return ("obs", "InvQuery", {}, [row["inv"], None, None, None], 0x00535BF9)


def weapcls_a(row):
    """0x00623C60(unit) through 0x00623990(unit, 1): no inventory 0, else the inventory query."""
    if not row["inv"]:
        return ("v", 0)
    return ("obs", "InvQuery", {}, [row["inv"], None, None, None], 0x006239BE)


def put_tohit(c, rnd, row):
    """Skills ToHit +0x198, LevToHit +0x19C, ToHitCalc +0x1A0 (-1, the linear form, or a calc offset)."""
    if not sid_ok(row):
        return
    b = srec(row)
    base, lev = rnd.choice([rnd.randint(0, 300), rnd.getrandbits(32)]), rnd.choice([rnd.randint(0, 35),
                                                                                    rnd.getrandbits(32)])
    c.put(b + 0x198, le32(base) + le32(lev))
    i = row["cal"]["fields"].index(0x1A0)
    if rnd.random() < 0.55:
        c.put(b + 0x1A0, le32(0xFFFFFFFF))
        row["cal"]["offs"][i] = 0xFFFFFFFF
    row["thc"] = None if row["cal"]["offs"][i] == 0xFFFFFFFF else 1
    row.update(th=base, lth=lev)


def tohit_a(row, neg=None):
    """SKILLS_GetToHit(unit, id, lvl), ret 0xC: lvl <= 0 -> 0; ToHitCalc -1 -> (lvl - 1)·LevToHit + ToHit (32-bit),
    else the calc (offset at or past the pool -> 0)."""
    lv = s32(row["lvl"])
    if lv <= 0:
        return 0
    if row["thc"] is None:
        k = lv if neg == "tohit_lvl" else lv - 1
        return s32(k * row["lth"] + row["th"])
    return ev_s(row, 0x1A0)


def put_target_a(c, rnd, row, game, types=(0, 1, 1, 1, 2, 3, 4, 5)):
    put_world_rooms(c, rnd, row)
    put_target(c, rnd, row, game, types)


def ret_a(row, eax, bit6=False):
    return ret_s(row, eax, bit6=bit6)


def sub_obs(row, sub, bit6=False, frame=None):
    """An expectation tuple from a helper (reach_a, ammo_a, weapcls_a) as a full expectation."""
    _, name, regs, args, site = sub
    return obs_a(row, name, regs, args, site, bit6=bit6, frame=frame)


# ------------------------------------------------------------------------------------------- start family
START_ORDER_A = ("st4", "st5", "st8", "st9")


@family("start_ama", "ama")
def start_ama(rnd, game):
    """Start 4 (the bows and javelins: the ammunition test), start 5 (Jab: a target), start 8 (Strafe) and start 9
    (Fend): the used skill, the ammunition test or the melee reach, then the target count up to the unit search."""
    cases, exp = [], []
    for k in range(1600):
        w = START_ORDER_A[k % 4]
        c = Case(FNA[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1, 1, 3) if w == "st4" else (0, 1, 1))
        put_inv_a(c, rnd, row)
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x64, 0x138, 0x140))
        put_target_a(c, rnd, row, game)
        if w in ("st8", "st9"):
            put_used_node(c, rnd, row)
        if w == "st9":
            put_reach(c, rnd, row)
        finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]])
    return cases, mem_ama(), {"cases": exp}


def search_a(row, w, r, neg=None):
    """Start 8 / 9 after their range: no target -> NearestUnitInRange(0, 0, r, filt, -1, &n), else 0x0056BC80 ->
    SKILLS_ForUnitsInRange(0, 0, r, filt | 0xA783, 0x0056BC70, &n, 0, file, 0x2E0); n zeroed before."""
    filt = 3 if w == "st8" else 0x20003
    if neg == "filt_swap":
        filt = 0x20003 if w == "st8" else 3
    if not tgt_unit(row):
        site = 0x005DAD7B if w == "st8" else 0x005DAEB3
        return obs_a(row, "NearestUnit", {"ecx": GAME, "edx": U}, [0, 0, r, filt, 0xFFFFFFFF, fr(-4)], site,
                     ptrs={5: le32(0)})
    return obs_a(row, "ForUnitsInRange", {"ecx": GAME, "edx": U},
                 [0, 0, r, filt | 0xA783, 0x0056BC70, None, 0, 0x006DAB88, 0x2E0], 0x0056BCBA, ptrs={5: le32(0)})


def start_ama_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    if w == "st4":
        a = ammo_a(row)
        if a[0] == "obs":
            br["invquery"] += 1
            return sub_obs(row, a)
        if a[1]:
            br["ret1"] += 1
            return ret_a(row, 1 if neg != "ammo_inv" else 0)
        br["hands"] += 1
        return obs_a(row, "HandsRefresh", {"ecx": game, "edx": U}, [], 0x005DA8CA)
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_a(row, 0)
    if w == "st5":
        t = int(bool(tgt_unit(row)))
        br["target" if t else "notarget"] += 1
        return ret_a(row, t if neg != "st5_inv" else 1 - t)
    if row["node"] is None:
        br["noused"] += 1
        return ret_a(row, 0)
    if w == "st8":
        a = ammo_a(row)
        if a[0] == "obs":
            br["invquery"] += 1
            return sub_obs(row, a)
        if not a[1]:
            br["hands"] += 1
            return obs_a(row, "HandsRefresh", {"ecx": game, "edx": U}, [], 0x005DAD26)
        r = ev_s(row, 0x64)
    else:
        a = reach_a(row, None)
        if a[0] == "obs":
            br["reach_" + a[1]] += 1
            return sub_obs(row, a)
        r = s32(a[1] + (4 if neg != "reach0" else 0))
    br[w + ("_near" if not tgt_unit(row) else "_count")] += 1
    return search_a(row, w, r, neg)


# ------------------------------------------------------------------------------------------- hit family
HIT_ORDER_A = ("st6", "st7", "st10", "do7")


@family("hit_ama", "ama")
def hit_ama(rnd, game):
    """Start 6 (Power Strike, Charged Strike), start 7 (Impale), start 10 (Lightning Strike) and do 7 (Jab): the
    target, the hostility test (start 7), the used skill (start 10), the to-hit, up to COMBAT_MeleeHitTest."""
    cases, exp = [], []
    for k in range(1600):
        w = HIT_ORDER_A[k % 4]
        c = Case(FNA[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1, 1))
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x138, 0x1A0))
        put_tohit(c, rnd, row)
        put_target_a(c, rnd, row, game, types=(0, 0, 1, 1, 1, 1, 2, 3, 4, 5))
        if w == "st7" and row["t"]:
            put_relation(c, rnd, row, p_align=0.6)
        if w == "st10":
            put_used_node(c, rnd, row)
        finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]])
    return cases, mem_ama(), {"cases": exp}


def hit_ama_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    t = tgt_unit(row)
    if w == "st6":
        if not t:
            br["notarget"] += 1
            return ret_a(row, 0)
        if not sid_ok(row):
            br["nosid"] += 1
            return ret_a(row, 0)
        br["hittest"] += 1
        return obs_a(row, "MeleeHitTest", {"ecx": game, "edx": U}, [T, 0, 0], 0x005DA9B4,
                     frame={fr(-0x78): bytes(0x70)})
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_a(row, 0)
    if w == "st10":
        if row["node"] is None:
            br["noused"] += 1
            return ret_a(row, 0)
        if not t:
            br["notarget"] += 1
            return ret_a(row, 0)
        br["hittest"] += 1
        return obs_a(row, "MeleeHitTest", {"ecx": game, "edx": U}, [T, 0, 0], 0x005DB09A,
                     frame={fr(-0x78): bytes(0x70)})
    if not t:
        br["notarget"] += 1
        return ret_a(row, 0)
    if w == "st7" and neg != "nohostile":
        h = hostile(row, None)
        if h[0] == "obs":
            br["pairflags"] += 1
            return obs_a(row, "PairFlags", {"ecx": h[2], "edx": h[3]}, [8], 0x00554297)
        if not h[1]:
            br["not_hostile"] += 1
            return ret_a(row, 0)
    th = tohit_a(row, neg) if neg != "tohit0" else 0
    if w == "do7" and row["ut"] == 1:
        br["monattack"] += 1
        return obs_a(row, "MonAttackStats", {"ecx": U, "edx": 8}, [], 0x005DB35D,
                     frame={fr(-0x7C): bytes(0x70), fr(-0x0C): le32(th)})
    br["hittest_" + ("lin" if row["thc"] is None else "calc")] += 1
    site = 0x005DABCF if w == "st7" else 0x005DB371
    return obs_a(row, "MeleeHitTest", {"ecx": game, "edx": U}, [T, th, 0], site, frame={fr(-0x7C): bytes(0x70)})


# ------------------------------------------------------------------------------------------- inner sight
@family("aura_ama", "ama")
def aura_ama(rnd, game):
    """Do 6 (Inner Sight, Slow Missiles): auratargetstate and aurastat1 in range, the block {id, lvl,
    auralencalc, auratargetstate, aurastat1, aurastatcalc1} and SKILLS_ForUnitsInRange(aurarangecalc, aurafilter)."""
    cases, exp = [], []
    for k in range(900):
        c = Case(FNA["do6"])
        row = {"w": "do6", "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1))
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x60, 0x64, 0x68))
        if sid_ok(row):
            b = srec(row)
            st = rnd.choice([rnd.randrange(NSTATES)] * 6 + [-1, NSTATES, rnd.randint(-0x8000, -2), 0x7FFF])
            a1 = rnd.choice([rnd.randrange(NISC)] * 6 + [-1, NISC, rnd.randint(-0x8000, -2)])
            filt = rnd.getrandbits(32)
            c.put(b + 0x82, le16(st))
            c.put(b + 0x54, le16(a1))
            c.put(b + 0x50, le32(filt))
            row.update(st=st, a1=a1, filt=filt)
        finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]])
    return cases, mem_ama(), {"cases": exp}


def aura_ama_model(row, game, br, neg=None):
    br["do6"] += 1
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_a(row, 0)
    st, a1 = s16(row["st"]), s16(row["a1"])
    if not 0 <= st < NSTATES or not 0 <= a1 < NISC:
        br["norange"] += 1
        return ret_a(row, 0)
    sid, lv = s16(row["sid"]), row["lvl"]
    ln, r, c1 = ev_s(row, 0x60), ev_s(row, 0x64), ev_s(row, 0x68)
    if neg == "blk_swap":
        st, a1 = a1, st
    if neg == "range_len":
        r = ln
    blk = b"".join(le32(v) for v in (sid, lv, ln, st, a1, c1))
    br["search"] += 1
    return obs_a(row, "ForUnitsInRange", {"ecx": game, "edx": U},
                 [0, 0, r, row["filt"], 0x005DB150, fr(-0x20), 1, 0x006E32E4, 0x20F], 0x005DB2AD, ptrs={5: blk})


# ------------------------------------------------------------------------------------------- creations
CREATE_ORDER_A = ("do8", "do10", "do8", "do10", "do11", "do14")


@family("create_ama", "ama")
def create_ama(rnd, game):
    """Do 8 (Multiple Shot, Teeth, PrimePoisonball, Shock Wave: the fan across the target line), do 10 (Guided
    Arrow, Bone Spirit), do 11 (Charged Strike) and do 14 (Lightning Strike) up to MissileCreate, the weapon's
    inventory query, or COMBAT_DeliverQueued."""
    cases, exp = [], []
    for k in range(1800):
        w = CREATE_ORDER_A[k % 6]
        c = Case(FNA[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1))
        put_inv_a(c, rnd, row, p=0.25)
        put_target_a(c, rnd, row, game)
        if w == "do8" and rnd.random() < 0.5 and row["t"] and row["tt"] not in (2, 4, 5) and u32f(c, T + 0x2C):
            # the target near the caster: the scaling of short vectors (0x0056D370) is reached
            row["tx"] = (row["ux"] + rnd.randint(-3, 3)) & 0xFFFF
            row["ty"] = (row["uy"] + rnd.randint(-3, 3)) & 0xFFFF
            c.put(TP + 0x02, le16(row["tx"]))
            c.put(TP + 0x06, le16(row["ty"]))
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x138, 0x13C, 0x140), big=False)
        if w == "do8" and sid_ok(row) and rnd.random() < 0.15:
            # n <= 0 and calc3 = n - 1: the first group empty, no centre group, one missile in the last group
            n = rnd.randint(-6, 0)
            set_calcs(c, row, [n, rnd.randint(-3, 12), n - 1])
        if sid_ok(row):
            b = srec(row)
            ma = rnd.choice([rnd.randrange(NREC)] * 5 + [-1, NREC, rnd.randint(-0x8000, -2)])
            mb = rnd.choice([rnd.randrange(NREC)] * 4 + [-1, -1, NREC])
            c.put(b + 0x48, le16(ma) + le16(mb))
            row.update(ma=ma, mb=mb)
            if w == "do11" or w == "do14":
                put_bycharge(c, rnd, row)
        finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]])
    return cases, mem_ama(), {"cases": exp}


def set_calcs(c, row, vals):
    """Replace the case's constant calc programs by `vals`, every field at its own valid offset."""
    pool = b"".join(b"\x09" + le32(v) + b"\x00" for v in vals)
    c.put(SPOOL, pool)
    c.put(DT + 0x44, le32(len(pool)))
    offs = [6 * i for i in range(len(vals))]
    for f, o in zip(row["cal"]["fields"], offs):
        c.put(srec(row) + f, le32(o))
    row["cal"].update(vals=list(vals), offs=offs, pool=len(pool))


def unit_xy_a(row, which):
    """The caster's position (types 0, 1: the dynamic path +0x02/+0x06)."""
    return (row["ux"], row["uy"]) if which == "u" else (row["tx"], row["ty"])


def trunc2(v):
    """`cdq; sub eax, edx; sar eax, 1`: v / 2 truncated toward 0 (signed 32-bit)."""
    v = s32(v)
    return -((-v) >> 1) if v < 0 else v >> 1


def fan_step(dx, dy, neg=None):
    """0x0056D370 then 0x0056D3B0 on (dx, dy), 32-bit: |d|² < 4 -> ×4, then < 16 -> ×2; then (a, b) = (-dx, dy)
    halved (truncating) while a² + b² > 3; the step is (b, a)."""
    sq = lambda a, b: s32(s32(a * a) + s32(b * b))
    if neg != "nonorm":
        if sq(dx, dy) < 4:
            dx, dy = s32(dx * 4), s32(dy * 4)
        if sq(dx, dy) < 16:
            dx, dy = s32(dx * 2), s32(dy * 2)
    a, b = s32(-dx), dy
    while sq(a, b) > 3:
        b, a = trunc2(b), trunc2(a)
    return b, a


def cls_ab(row, neg=None):
    """srvmissilea, or srvmissileb (when not negative) since 0x00623C60 gives 0 (no inventory) != 1."""
    cls = s16(row["ma"])
    if s16(row["mb"]) >= 0 and neg != "src_a":
        cls = s16(row["mb"])
    return cls


def create_ama_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    sid, lv = s16(row["sid"]), row["lvl"]
    bit6 = w in ("do8", "do10", "do11")
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_a(row, 0, bit6=bit6)
    if w in ("do11", "do14"):
        t = tgt_unit(row)
        if not t:
            br["notarget"] += 1
            return ret_a(row, 0, bit6=bit6)
        br["deliver"] += 1
        return obs_a(row, "DeliverQueued", {"ecx": game, "edx": U}, [T, 0],
                     0x005DB8B3 if w == "do11" else 0x005DBEAB, bit6=bit6)
    x, y, ok = target_xy(row)
    if w == "do10":
        t = tgt_unit(row)
        if not ok:
            br["noxy"] += 1
            return ret_a(row, 0, bit6=True)
        n = ev_s(row, 0x138)
        wc = weapcls_a(row)
        if wc[0] == "obs":
            br["invquery"] += 1
            return sub_obs(row, wc, bit6=True, frame={fr(-0x14): le32(n), fr(-0x10): le32(t), fr(-0x8): le32(x),
                                                       fr(-0xC): le32(y)})
        cls = cls_ab(row, neg)
        if not 0 <= cls < NREC:
            br["nomiss"] += 1
            return ret_a(row, 0, bit6=True)
        blk = bytearray(blk9d(flags=0x20 if t else 0x420, owner=U, source=U, cls=cls, tx=x, ty=y, skill=sid,
                              lvl=lv))
        struct.pack_into("<I", blk, 0x0C, t)
        if n != 0 or neg == "cb_always":
            struct.pack_into("<I", blk, 0x54, 0x005DB6A0)
        struct.pack_into("<I", blk, 0x58, n & M32)
        br["guided_" + ("unit" if t else "point")] += 1
        return obs_a(row, "MissileCreate", {"ecx": game}, [], 0x005DB7ED, bit6=True, stk={"edx": (0, bytes(blk))})
    # do 8
    if not ok:
        br["noxy"] += 1
        return ret_a(row, 1, bit6=True)
    n = ev_s(row, 0x138)
    ux, uy = row["ux"], row["uy"]
    sx, sy = fan_step(s32(x - ux), s32(y - uy), neg)
    half = trunc2 if neg != "floor2" else (lambda v: s32(v) >> 1)
    x0 = s32(x - half(s32(sx * n)))
    y0 = s32(y - half(s32(sy * n)))
    wc = weapcls_a(row)
    if wc[0] == "obs":
        br["invquery"] += 1
        return sub_obs(row, wc, bit6=True, frame={fr(-0x4): le32(x0), fr(-0x8): le32(y0), fr(-0xC): le32(sx),
                                                   fr(-0x10): le32(sy), fr(-0x14): le32(s16(row["ma"]))})
    cls = cls_ab(row, neg)
    if not 0 <= cls < NREC:
        br["nomiss"] += 1
        return ret_a(row, 0, bit6=True)
    c3 = ev_s(row, 0x140)
    if c3 == 0:
        c3 = n
    g1 = trunc2(s32(n - c3))
    g3 = s32(s32(n - g1) - c3)
    if g1 > 0:
        fl, site, grp = 0x10820, 0x005DB5F1, "outer1"
    elif c3 > 0:
        fl, site, grp = 0x820, 0x005DB628, "centre"
    elif g3 > 0:
        fl, site, grp = 0x10820, 0x005DB661, "outer2"
    else:
        br["nocreate"] += 1
        return ret_a(row, 1, bit6=True)
    blk = bytearray(block(flags=fl, owner=U, source=U, cls=cls, tx=x0, ty=y0, skill=sid, lvl=lv))
    struct.pack_into("<I", blk, 0x44, ev_s(row, 0x13C) & M32)
    br["fan_" + grp] += 1
    return obs_a(row, "MissileCreate", {"ecx": game}, [], site, bit6=True, stk={"edx": (0, bytes(blk))})


# ------------------------------------------------------------------------------------------- strafe and fend do
NODE_ORDER_A = ("do12", "do13")


@family("node_ama", "ama")
def node_ama(rnd, game):
    """Do 12 (Strafe) and do 13 (Fend, Zeal, Fury): the used skill's count and last target (+0x18, +0x1C, +0x20),
    GameFindUnit, then UnitSetPathTargetUnit / InMeleeRange or the nearest-unit search."""
    cases, exp = [], []
    for k in range(1200):
        w = NODE_ORDER_A[k % 2]
        c = Case(FNA[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 1, 1, 1))
        put_inv_a(c, rnd, row)
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x64,))
        put_used_node(c, rnd, row, p=0.92)
        put_reach(c, rnd, row)
        nd = row["node"]
        row["found"] = 0
        if nd is not None:
            if rnd.random() < 0.6:
                put_unit_found(c, rnd, T, nd["ty"], nd["g"], decoy=(nd["g"] ^ 0x80) if rnd.random() < 0.2 else None)
                row["found"] = T
            else:
                put_unit_absent(c, rnd, nd["ty"], nd["g"])
        finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]])
    return cases, mem_ama(), {"cases": exp}


def node_ama_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_a(row, 0)
    nd = row["node"]
    if nd is None:
        br["noused"] += 1
        return ret_a(row, 0)
    if w == "do12":
        r = ev_s(row, 0x64)
        if nd["n18"] == 0:
            br["count0"] += 1
            return ret_a(row, 0)
        if row["found"]:
            br["settarget"] += 1
            return obs_a(row, "SetPathTarget", {}, [U, T], 0x005DBB06)
        br["near"] += 1
        return obs_a(row, "NearestUnit", {"ecx": game, "edx": U},
                     [0, 0, r, 3, nd["g"] if neg != "g_any" else 0xFFFFFFFF, 0], 0x005DBAF4)
    a = reach_a(row, None)
    if a[0] == "obs":
        br["reach_" + a[1]] += 1
        return sub_obs(row, a)
    r = s32(a[1] + 4)
    if row["found"]:
        br["meleerange"] += 1
        return obs_a(row, "InMeleeRange", {}, [U, T, 0], 0x005DBCE5)
    br["near"] += 1
    return obs_a(row, "NearestUnit", {"ecx": game, "edx": U},
                 [0, 0, r, 0x20003 if neg != "filt3" else 3, nd["g"], 0], 0x005DBD06)


# ------------------------------------------------------------------------------------------- summons
@family("summon_ama", "ama")
def summon_ama(rnd, game):
    """Do 15 (Dopplezon) and do 16 (Valkyrie, players only): the summon class and mode, the pet type, then the
    SpawnOwnedMonster block."""
    cases, exp = [], []
    for k in range(1200):
        w = ("do15", "do16")[k % 2]
        c = Case(FNA[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1, 2))
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0xC0, 0x13C, 0x140))
        if sid_ok(row):
            b = srec(row)
            summ = rnd.randrange(NMON)
            mode = rnd.choice([rnd.randrange(16), rnd.randrange(16), -1, 16, rnd.randint(17, 127)])
            pet = rnd.choice([rnd.randrange(NPET)] * 8 + [0xFF, NPET, rnd.randint(NPET, 255)])
            c.put(b + 0xBC, le16(summ))
            c.put(b + 0xBE, bytes([pet & 0xFF, mode & 0xFF]))
            row.update(summ=summ, mode=mode, pet=pet)
        finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]])
    return cases, mem_ama(), {"cases": exp}


def summon_ama_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_a(row, 0)
    if w == "do16" and row["ut"] != 0:
        br["notplayer"] += 1
        return ret_a(row, 0)
    mode = row["mode"] if 0 <= row["mode"] < 16 else 1
    pet = row["pet"] if row["pet"] < NPET else 0
    if neg == "pet_refuse" and row["pet"] >= NPET:
        return ret_a(row, 0)
    w24 = mode if w == "do15" else srec(row)
    if neg == "w24_zero":
        w24 = 0
    blk = b"".join(le32(v) for v in (0, U, row["summ"], 0, mode, 0, 0, pet, ev_s(row, 0xC0), w24))
    br["spawn_pet%s" % ("0" if row["pet"] >= NPET else "")] += 1
    return obs_a(row, "SpawnOwned", {"ecx": game}, [], 0x005DC0DA if w == "do15" else 0x005DC2BF, bit6=True,
                 stk={"edx": (0, blk)})


RS_AMA = [RS_HASH, RS_SKN, RS_CALC_JT, RS_BITMASK9C, RS_TOWN]
CHECKS.update({
    "start_ama": check9b("start_ama", start_ama_model, ["ammo_inv", "st5_inv", "filt_swap", "reach0"], RS_AMA,
                         md_masked=False),
    "hit_ama": check9b("hit_ama", hit_ama_model, ["tohit0", "tohit_lvl", "nohostile"], RS_AMA, md_masked=False),
    "aura_ama": check9b("aura_ama", aura_ama_model, ["blk_swap", "range_len"], RS_AMA, md_masked=False),
    "create_ama": check9b("create_ama", create_ama_model, ["nonorm", "floor2", "src_a", "cb_always"], RS_AMA,
                          md_masked=False),
    "node_ama": check9b("node_ama", node_ama_model, ["g_any", "filt3"], RS_AMA, md_masked=False),
    "summon_ama": check9b("summon_ama", summon_ama_model, ["w24_zero", "pet_refuse"], RS_AMA, md_masked=False),
})

PINS_AMA = [  # (address, mnemonic, operand substring): instructions the ama claims turn on (ADR-0015 (5))
    (0x0056C4F2, "cmp", "DWORD PTR [esi],0x0"), (0x00535BD8, "mov", "edi,DWORD PTR [esi+0x60]"),  # ammo test
    (0x00623C6A, "je", ""), (0x0062399B, "mov", "edi,DWORD PTR [esi+0x60]"),                       # weapon class
    (0x006228B5, "movzx", "eax,BYTE PTR [eax+0xe]"), (0x006228B9, "cmp", "eax,0xff"),             # melee reach
    (0x0056E516, "add", "eax,0x4"),
    (0x00644A3C, "cmp", "edx,0xffffffff"), (0x00644A86, "lea", "eax,[edi-0x1]"),                  # GetToHit
    (0x00644A2A, "jg", ""),
    (0x005DABBB, "call", "0x6449f0"), (0x005DABC6, "push", "eax"),                                # start 7
    (0x005DAD6C, "push", "0x3"), (0x005DAEA3, "push", "0x20003"), (0x0056BC9C, "or", "eax,0xa783"),
    (0x005DB351, "mov", "edx,0x8"),                                                                # do 7
    (0x005DB1FF, "movzx", "eax,WORD PTR [esi+0x82]"), (0x005DB292, "push", "0x1"),                 # do 6
    (0x0056D380, "cmp", "eax,0x4"), (0x0056D39F, "cmp", "eax,0x10"), (0x0056D3C7, "cmp", "eax,0x3"),
    (0x0056D3D5, "sar", "eax,1"), (0x005DB507, "sar", "eax,1"), (0x005DB5D6, "sar", "esi,1"),     # do 8
    (0x005DB52C, "cmp", "eax,0x1"), (0x005DB596, "mov", "DWORD PTR [ebp-0x78],0x820"),
    (0x005DB5BD, "or", "DWORD PTR [ebp-0x78],0x10000"),
    (0x005DB7DB, "mov", "DWORD PTR [ebp-0x70],0x420"), (0x005DB7CD, "mov", "DWORD PTR [ebp-0x1c],0x5db6a0"),
    (0x005DC06C, "cmp", "ecx,DWORD PTR [edx+0xbf0]"), (0x005DC0B2, "mov", "DWORD PTR [ebp-0x24],eax"),  # do 15
    (0x005DC224, "cmp", "DWORD PTR [esi],0x0"), (0x005DC210, "mov", "DWORD PTR [ebp-0xc],edi"),   # do 16
    (0x005DBE3F, "xor", "eax,eax"),                                                                 # do 13's return
]


def ref_scan(A, lo):
    """Every .text instruction whose operands name `lo` in any form: a PTR-form or moffs (`ds:0x…`) destination
    (a store), an immediate (`push 0x…`, `mov reg, 0x…`: the address taken), or a read. -> (stores, imms, reads)."""
    tag = "0x%x" % lo
    stores, imms, reads = [], [], []
    for va, (mn, ops) in sorted(A.ins.items()):
        if tag not in ops:
            continue
        parts = ops.split(",")
        dst = parts[0]
        if tag in dst and ("PTR" in dst or "ds:" in dst) and mn in ("mov", "add", "sub", "inc", "dec", "or", "and",
                                                                      "xor", "pop", "stos", "movs", "xchg"):
            stores.append(va)
        elif "PTR" not in ops and "ds:" not in ops:
            imms.append(va)
        else:
            reads.append(va)
    return stores, imms, reads


def cmd_static_ama(a):
    rep = Report("static")
    rep.batch = "AMA"
    A = S4.asm()
    for va, mn, sub in PINS_AMA:
        ins = A.at(va)
        rep.c["pins"] += 1
        if ins is None or ins[0] != mn or sub not in ins[1]:
            rep.bad("pin 0x%08X: %r, want %s %s" % (va, ins, mn, sub))
        else:
            rep.c["pins_ok"] += 1
    for lo, n, name in ((BITMASK, 128, "g_BitMask32"), (0x006E10E0, 20, "hash offsets"),
                        (0x006C1164, 88, "CALC_Eval jump table"), (0x006426C0, 8 + 0x6D, "town tables")):
        sec = S4.section_of(lo)
        flags = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.c["ro_reads"] += 1
        if flags & 0x80000000:
            rep.bad("%s 0x%08X in writable %s" % (name, lo, sec))
        rep.notes.append("%s 0x%08X: %s" % (name, lo, sec))
    st, im, rd = ref_scan(A, SK_NFUNCS)
    rep.c["data_stores"] += len(st)
    rep.c["data_imms"] += len(im)
    rep.notes.append("skills calc function count 0x%08X: %d stores (PTR or moffs), %d immediates, %d reads in .text"
                     % (SK_NFUNCS, len(st), len(im), len(rd)))
    for name, va in sorted(FNA.items(), key=lambda kv: kv[1]):
        tab = START_TABLE if name.startswith("st") else DO_TABLE
        num = int(name[2:])
        rep.c["table_entries"] += 1
        if S4.dword(tab + 4 * num) != va:
            rep.bad("%s: table entry 0x%08X, model address 0x%08X" % (name, S4.dword(tab + 4 * num), va))
    rep.notes.append("start table 4..10: %s" % " ".join("%d:0x%08X" % (i, S4.dword(START_TABLE + 4 * i))
                                                       for i in range(4, 11)))
    rep.notes.append("do table 6..16: %s" % " ".join("%d:0x%08X" % (i, S4.dword(DO_TABLE + 4 * i))
                                                    for i in range(6, 17)))
    print("CATAMA static " + " ".join("%s=%d" % (k, rep.c[k]) for k in sorted(rep.c)))
    for n in rep.notes:
        print("  " + n)
    return 1 if rep.c["bad"] else 0


# ##################################################################################################################
# Batch nec (plan 0046): the necromancer start functions 15-21 and do functions 30-32 and 55-63 of g_SkillStartFuncs
# (0x00732140) and g_SkillDoFuncs (0x007322B0), each (ECX game, EDX unit; skill id, level), `ret 8`. The conventions
# of 9c, 9d, sor and ama: the call site of every observed boundary asserted (site control), the caster's and the
# target's seeds compared in every case, a boundary pointer argument compared by content, two or more negative
# controls per family (one failing >= 50 cases), no callee-saved register compared that is not a boundary argument,
# no meaning a boundary callee gives to a compared word in the claim. Where a boundary sits inside a helper the batch
# function called (0x005C2FF0, 0x005C3300, 0x005C31F0, 0x005C5BC0), the helper's return address into the batch
# function is compared at its absolute stack slot (the condition of ruling 1 of the lane/p46m6 review), with the batch
# function's frame words.
# Emulated, not observed: UNIT_GetTargetUnit, SKILLS_GetTargetXY, UnitGetRoom, RoomIsTown, RoomAtSubtile, UnitGetSubX/Y
# (sor's); the corpse tests 0x00645510 / 0x00645680 with MonStats2FlagTest, 0x0063A770 (DataTables+0x150's state
# set) and UnitIsDead; 0x005C3300 (start 21's test); 0x005C31F0 (do 59's test) with 0x006259B0; start 20's item test
# (ITEMS_GetRecord, 0x00629CC0, ITEMS_CheckFlags, STATLIST_GetOwnerUnit); 0x005C2FF0 up to its COMBAT_ApplyDamage,
# with UnitGetMaxHp; the curse helpers 0x005C3400, 0x005C37A0 (0x00611D30), 0x0045C4F0; SkillSummonClass.
# Observed (new here): SkillForUnitsNearTarget, COMBAT_ApplyDamage, 0x0061A270 (the corpse's room removal), STATE_Set,
# 0x0056E2F0 (a monster test not read).
# ##################################################################################################################
FNN = {
    "st15": 0x005C3070, "st16": 0x005C30A0, "st17": 0x005C31C0, "st18": 0x005C3260, "st19": 0x005C3270,
    "st20": 0x005C32A0, "st21": 0x005C3350,
    "do30": 0x005C37C0, "do31": 0x005C4B00, "do32": 0x005C4CD0, "do55": 0x005C4DF0, "do56": 0x005C5100,
    "do57": 0x005C5250, "do58": 0x005C56C0, "do59": 0x005C3B90, "do60": 0x005C58B0, "do61": 0x005C3F20,
    "do62": 0x005C5D00, "do63": 0x005C5E60,
}
BOUNDS_N = dict(BOUNDS_A)
BOUNDS_N.update({
    0x0056E780: "NearTarget", 0x0057C6C0: "ApplyDamage", 0x0061A270: "RoomUnitRemove", 0x00639DB0: "StateSet",
    0x0056E2F0: "MonTest2F0",
})
BOUND_BY_NAME.update({v: k for k, v in BOUNDS_N.items()})
ALLBOUND.update(BOUNDS_N)
ITREC = 0x12620000                   # item records (0x1A8), ITEMS_GetRecord's table (0x0096CA5C) in the spec
NITEM = 4
IDATA = TGT + 0xA00                  # the target item's data (+0x18 flags)
TSL2 = TSL + 0x800                   # the stat list STATLIST_GetOwnerUnit follows (+0x34)
MASK33 = 0x12630000                  # DataTables+0x150: state bit-set 33, 6 words for 190 states
NSW = (NSTATES + 31) // 32
BP_OFF = (0x006E304C, 0x006E307C)    # do 62's twelve (x, y) offsets (.rdata)
RS_BP = (0x006E304C, 0x006E30AC, "r", "do 62's offsets 0x006E304C/0x006E307C (.rdata)")
RS_ITEMS = (0x0096CA58, 0x0096CA60, "r", "ITEMS_GetRecord's count and table 0x0096CA58/0x0096CA5C (.data, set in "
            "the spec)")
RS_NEC = [RS_HASH, RS_SKN, RS_CALC_JT, RS_BITMASK9C, RS_TOWN, RS_DIFF, RS_ITEMS, RS_BP]


def abs_ret(a, v):
    """A return address (or any word) at an absolute stack address."""
    return {a: le32(v)}


def mem_nec():
    lines = ["dword %08x %08x" % (G_PDATATABLES, DT),
             "dword %08x %08x" % (DT + 0xB64, MREC), "dword %08x %08x" % (DT + 0xB6C, NREC),
             "dword %08x 6b3a11f5" % COOKIE,
             "dword %08x %08x" % (DT + 0xB98, SREC), "dword %08x %08x" % (DT + 0xBA0, NSREC),
             "dword %08x %08x" % (DT + 0x40, SPOOL),
             "dword %08x %08x" % (DT + 0xBCC, ISC), "dword %08x %08x" % (DT + 0xBD4, NISC),
             "dword %08x %08x" % (DT + 0xA78, MSREC), "dword %08x %08x" % (DT + 0xA80, NMON),
             "dword %08x %08x" % (DT + 0xA90, MS2REC), "dword %08x %08x" % (DT + 0xA98, NMON2),
             "dword %08x %08x" % (DT + 0xC4, NSTATES), "dword %08x %08x" % (DT + 0xBF0, NPET),
             "dword %08x %08x" % (DT + 0x150, MASK33),
             "dword %08x %08x" % (0x0096C8AC, DIFF), "dword %08x %08x" % (0x0096C8B0, NDIFF),
             "dword %08x %08x" % (0x0096CA58, NITEM), "dword %08x %08x" % (0x0096CA5C, ITREC)]
    lines += ["observe %08x" % a for a in sorted(BOUNDS_N)]
    lines += ["guard %08x" % a for a in FATAL + ALLOC if a not in BOUNDS_N]
    return lines


def pick_sid_n(rnd, w):
    """The ids a function's own code admits without a fault: do 55-63 read the record (0 when the id is out of range)
    after testing only id != 0, and SkillSummonClass faults on a player for a refused id."""
    if w in ("do56", "do57", "do58", "do60", "do62", "do63", "do31"):
        return rnd.choice([rnd.randrange(1, NSREC)] * 6 + [0]) if w != "do31" else pick_skill(rnd)
    return pick_skill(rnd)


def put_mon_tables(c, rnd, row):
    """MonStats +0x18 (the MonStats2 row, s16) and +0x32 (u16), MonStats2 +0x04/+0x05 (flag bits 0-15)."""
    m2i = [rnd.choice([rnd.randrange(NMON2)] * 6 + [NMON2, -1]) for _ in range(NMON)]
    w32 = [rnd.choice([0, 1, rnd.getrandbits(16)]) for _ in range(NMON)]
    m2f = [rnd.getrandbits(16) for _ in range(NMON2)]
    for i in range(NMON):
        c.put(MSREC + 0x1A8 * i + 0x18, le16(m2i[i]))
        c.put(MSREC + 0x1A8 * i + 0x32, le16(w32[i]))
    for i in range(NMON2):
        c.put(MS2REC + 0x134 * i + 0x04, le16(m2f[i]))
    row.update(m2i=m2i, w32=w32, m2f=m2f)


def ms2bit(row, cls, bit):
    """sub_004638A0_MonStats2FlagTest(ECX class, EDX bit): MonStats2 byte +4 + bit / 8, bit bit % 8."""
    if not 0 <= s32(cls) < NMON:
        return 0
    i = s16(row["m2i"][cls])
    if not 0 <= i < NMON2:
        return 0
    return (row["m2f"][i] >> bit) & 1


def put_corpse(c, rnd, row):
    """The target monster's class, mode, +0xC6 and state words (stat list +0x58, the list's +0x10 bit 31), and the
    bit-set DataTables+0x150; MonStats/MonStats2 rows."""
    put_mon_tables(c, rnd, row)
    mask = [rnd.choice([0, 0, 1 << rnd.randrange(32), rnd.getrandbits(32)]) for _ in range(NSW)]
    for i, m in enumerate(mask):
        c.put(MASK33 + 4 * i, le32(m))
    row["mask"] = mask
    if not row["t"]:
        return
    cls = rnd.choice([rnd.randrange(NMON)] * 7 + [NMON, rnd.randint(NMON, 700)])
    mode = rnd.choice([12] * 5 + [0, 0, rnd.randrange(1, 18), 17])
    c6 = rnd.choice([0, 0, 0, 0, 1, rnd.getrandbits(8)])
    c.put(T + 0x04, le32(cls))
    if row["tt"] == 4:
        mode = row["tmode"]                # an item keeps the mode its target link was revalidated with
    else:
        c.put(T + 0x10, le32(mode))
    c.put(T + 0xC6, bytes([c6]))
    k = rnd.random()
    words = None
    if k < 0.07:
        c.put(T + 0x5C, le32(0))
    else:
        fl = rnd.getrandbits(32) | 0x80000000
        if k < 0.13:
            fl &= 0x7FFFFFFF
        c.put(T + 0x5C, le32(TSL))
        c.put(TSL + 0x10, le32(fl))
        if fl & 0x80000000:
            wa = TSL + 0x200
            c.put(TSL + 0x58, le32(wa))
            words = []
            for i in range(NSW):
                v = rnd.getrandbits(32) if rnd.random() < 0.3 else 0
                words.append(v)
                c.put(wa + 4 * i, le32(v))
    if row["tt"] == 1 and rnd.random() < 0.55:
        # a corpse the tests pass more often: mode 12, a class whose MonStats2 row has flags 7 and 8, MonStats +0x32
        cls = rnd.randrange(NMON)
        c.put(T + 0x04, le32(cls))
        if not 0 <= s16(row["m2i"][cls]) < NMON2:
            row["m2i"][cls] = rnd.randrange(NMON2)
            c.put(MSREC + 0x1A8 * cls + 0x18, le16(row["m2i"][cls]))
        i2 = row["m2i"][cls]
        row["m2f"][i2] |= (0x80 if rnd.random() < 0.92 else 0) | (0x100 if rnd.random() < 0.85 else 0)
        c.put(MS2REC + 0x134 * i2 + 0x04, le16(row["m2f"][i2]))
        if row["w32"][cls] == 0 and rnd.random() < 0.9:
            row["w32"][cls] = rnd.randint(1, 0xFFFF)
            c.put(MSREC + 0x1A8 * cls + 0x32, le16(row["w32"][cls]))
        mode = 12 if rnd.random() < 0.85 else rnd.choice([0, 17])
        c.put(T + 0x10, le32(mode))
        c6 = 0 if rnd.random() < 0.9 else 1
        c.put(T + 0xC6, bytes([c6]))
        if words is not None and rnd.random() < 0.8:
            words = [0] * NSW
            for i in range(NSW):
                c.put(TSL + 0x200 + 4 * i, le32(0))
    row.update(tcls=cls, tmode=mode, c6=c6, twords=words)


def set33(row):
    """0x0063A770 -> sub_0063A130_UnitHasStateInMask(EAX unit, EBX DataTables+0x150)."""
    if row["twords"] is None:
        return 0
    return int(any(w & m for w, m in zip(row["twords"], row["mask"])))


def corpse510(row, flag):
    """0x00645510(unit, flag): a monster (type 1) in mode 12, or in mode 0 when flag != 0; not in set 33;
    MonStats2 flag 7; MonStats +0x32 != 0."""
    if not row["t"] or row["tt"] != 1:
        return 0
    if row["tmode"] != 12 and not (flag and row["tmode"] == 0):
        return 0
    if set33(row) or not ms2bit(row, row["tcls"], 7):
        return 0
    return int(row["w32"][row["tcls"]] != 0)


def corpse680(row, neg=None):
    """0x00645680(unit): a monster in mode 12, not in set 33 (unless the control), MonStats2 flag 7."""
    if not row["t"] or row["tt"] != 1 or row["tmode"] != 12:
        return 0
    if set33(row) and neg != "set33_skip":
        return 0
    return ms2bit(row, row["tcls"], 7)


def is_dead_t(row):
    """sub_005541B0_UnitIsDead(ECX unit) on the target: +0xC6 bit 0; a player in mode 0 or 17, a monster in mode 0
    or 12; any other type dead."""
    if row["c6"] & 1:
        return 1
    if row["tt"] == 0:
        return int(row["tmode"] in (0, 17))
    if row["tt"] == 1:
        return int(row["tmode"] in (0, 12))
    return 1


def test3300(row, neg=None):
    """0x005C3300 (ESI unit): a monster, MonStats2 flag 8, dead, 0x00645510(unit, 0), then 0x0056E2F0(unit, 7)."""
    if not row["t"] or row["tt"] != 1:
        return ("v", 0)
    if not ms2bit(row, row["tcls"], 7 if neg == "flag7" else 8):
        return ("v", 0)
    dead = is_dead_t(row)
    if neg == "notdead":
        dead = 1 - dead
    if not dead or not corpse510(row, 0):
        return ("v", 0)
    return ("obs",)


def ret_n(row, eax, bit6=False):
    return ret_s(row, eax, bit6=bit6)


def finish_n(c, rnd, row, game, cases, exp):
    finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]])


def town_t(row):
    return town_of(row, room_of_t(row)) if row["t"] else 0


# ------------------------------------------------------------------------------------------- the item test (st 20)
def put_item_t(c, rnd, row):
    """For an item target: its class (ITEMS_GetRecord, record +0xDC bit 1), its data (+0x14, flags +0x18) and the
    stat list STATLIST_GetOwnerUnit follows (+0x5C, +0x34, +0x10 bit 31, +0x44)."""
    rec_dc = [rnd.choice([2, 2, 2, 0, rnd.getrandbits(32)]) for _ in range(NITEM)]
    for i in range(NITEM):
        c.put(ITREC + 0x1A8 * i + 0xDC, le32(rec_dc[i]))
    row["rec_dc"] = rec_dc
    if not row["t"] or row["tt"] != 4:
        return
    mode = rnd.choice([3] * 6 + [0, 4, 5])
    c.put(T + 0x10, le32(mode))
    row["tmode"] = mode
    cls = rnd.choice([rnd.randrange(NITEM)] * 12 + [NITEM])
    c.put(T + 0x04, le32(cls))
    row["icls"] = cls
    if rnd.random() < 0.9:
        c.put(T + 0x14, le32(IDATA))
        fl = rnd.choice([0x10] * 4 + [0, rnd.getrandbits(32)])
        c.put(IDATA + 0x18, le32(fl))
        row["iflags"] = fl
    else:
        c.put(T + 0x14, le32(0))
        row["iflags"] = None
    k = rnd.random()
    own = 0
    if k < 0.3:
        c.put(T + 0x5C, le32(0))
    else:
        c.put(T + 0x5C, le32(TSL))
        if k < 0.45:
            c.put(TSL + 0x34, le32(0))
        else:
            c.put(TSL + 0x34, le32(TSL2))
            fl2 = rnd.getrandbits(32)
            c.put(TSL2 + 0x10, le32(fl2))
            if fl2 & 0x80000000:
                own = rnd.choice([0, 0, U, rnd.getrandbits(32)])
                c.put(TSL2 + 0x44, le32(own))
    if rnd.random() < 0.4 and (cls & M32) < NITEM:
        # an item the test admits: record bit 1, flag 0x10, no owner list
        rec_dc[cls] |= 2
        c.put(ITREC + 0x1A8 * cls + 0xDC, le32(rec_dc[cls]))
        c.put(T + 0x14, le32(IDATA))
        row["iflags"] = 0x10 | (rnd.getrandbits(32) if rnd.random() < 0.3 else 0)
        c.put(IDATA + 0x18, le32(row["iflags"]))
        c.put(T + 0x5C, le32(0))
        own = 0
    row["iown"] = own


def item_test(row, neg=None):
    """Start 20 (0x005C32A0) after the target: type 4, mode 3, 0x00629CC0 (ITEMS_GetRecord's +0xDC bit 1; no record
    -> the fatal path), ITEMS_CheckFlags(0x10), STATLIST_GetOwnerUnit == 0. -> ('v', r) or the fatal boundary."""
    t = tgt_unit(row)
    if not t:
        return ("v", 0)
    if row["tt"] != 4 or (row["tmode"] != 3 and neg != "item_mode"):
        return ("v", 0)
    cls = row["icls"]
    if (cls & M32) >= NITEM:
        return ("fatal",)
    if not row["rec_dc"][cls] & 2:
        return ("v", 0)
    if row["iflags"] is None or not row["iflags"] & 0x10:
        return ("v", 0)
    return ("v", int(row["iown"] == 0))


# ------------------------------------------------------------------------------------------- start family
START_ORDER_N = ("st15", "st16", "st17", "st18", "st19", "st20", "st21", "do32")


@family("start_nec", "nec")
def start_nec(rnd, game):
    """Start 15 (Raise Skeleton), 16 (Poison Dagger), 17 (Corpse Explosion), 18 (Attract), 19 (Bone Prison), 20
    (IronGolem), 21 (Revive) and do 32 (Poison Dagger): the target, the town, corpse, item and revive tests, up to
    their returns, COMBAT_MeleeHitTest, 0x0056E2F0 or COMBAT_DeliverQueued."""
    cases, exp = [], []
    for k in range(1600):
        w = START_ORDER_N[k % 8]
        c = Case(FNN[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1))
        ttypes = (4, 4, 4, 4, 1, 0, 2) if w == "st20" else (1, 1, 1, 1, 1, 0, 2, 3, 4)
        put_target_a(c, rnd, row, game, types=ttypes)
        if w == "st16":
            row["cal"] = sor_calcs(c, rnd, row["sid"], (0x1A0,))
            put_tohit(c, rnd, row)
        if w == "st20":
            put_item_t(c, rnd, row)
        else:
            put_corpse(c, rnd, row)
        finish_n(c, rnd, row, game, cases, exp)
    return cases, mem_nec(), {"cases": exp}


def start_nec_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    t = tgt_unit(row)
    town = town_t(row)
    if neg == "town_inv":
        town = 1 - town
    if w == "st18":
        br["ret1"] += 1
        return ret_n(row, 1)
    if w == "do32":
        if not t:
            br["notarget"] += 1
            return ret_n(row, 0, bit6=True)
        br["deliver"] += 1
        return obs_a(row, "DeliverQueued", {"ecx": game, "edx": U}, [T, 0], 0x005C4CFD, bit6=True)
    if w == "st20":
        r = item_test(row, neg)
        if r[0] == "fatal":
            br["fatal"] += 1
            return obs_a(row, "Fatal", {}, [0x104A], 0x00629CDA)
        br["item%d" % r[1]] += 1
        return ret_n(row, r[1])
    if not t:
        br["notarget"] += 1
        return ret_n(row, 0)
    if w == "st21":
        r = test3300(row, neg)
        if r[0] == "v":
            br["norevive"] += 1
            return ret_n(row, 0)
        br["montest"] += 1
        return obs_a(row, "MonTest2F0", {"ecx": T, "edx": 7}, [], 0x005C3340, frame=abs_ret(0x7FEFFFF8, 0x005C3366))
    if w == "st19":
        br["town" if town else "outside"] += 1
        return ret_n(row, 0 if town else 1)
    if town:
        br["town"] += 1
        return ret_n(row, 0)
    if w == "st15":
        r = corpse510(row, 0) if neg != "set33_skip" else corpse510(dict(row, twords=None), 0)
        br["corpse%d" % r] += 1
        return ret_n(row, r)
    if w == "st17":
        r = corpse680(row, neg)
        br["corpse%d" % r] += 1
        return ret_n(row, r)
    # st16
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_n(row, 0)
    br["hittest"] += 1
    return obs_a(row, "MeleeHitTest", {"ecx": game, "edx": U}, [T, tohit_a(row), 0], 0x005C3130,
                 frame={fr(-0x78): bytes(0x70)})


# ------------------------------------------------------------------------------------------- the curses
CURSE_ORDER_N = ("do30", "do61")


def diff_div(row, v):
    """0x005C37A0 (AL difficulty, ESI v): 0x00611D30(d) clamps d to [0, n - 1]; the record's +0x1C non-zero -> v /
    it (idiv, truncating), else v."""
    d = row["diff"]
    d = d if d > 0 else 0
    d = min(d, NDIFF - 1)
    q = row["div"][d]
    if q == 0:
        return v
    return s32(cdiv(s32(v), s32(q)))


@family("curse_nec", "nec")
def curse_nec(rnd, game):
    """Do 30 (the eight curses, Defense Curse, Blood Mana) and do 61 (Confuse): the state and stat range tests, the
    length (divided by the difficulty record's +0x1C for states 23 and 56, always for do 61), the block, up to
    sub_0056E780_SkillForUnitsNearTarget."""
    cases, exp = [], []
    for k in range(1400):
        w = CURSE_ORDER_N[k % 2]
        c = Case(FNN[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1, 3))
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x60, 0x64, 0x68, 0x6C, 0x70, 0x74, 0x78, 0x7C))
        diff = rnd.choice([0, 1, 2, 3, 0xFF, 0x80])
        c.put(GAME + 0x6D, bytes([diff]))
        row["diff"] = diff if diff < 0x80 else diff     # movzx: 0..255, never negative
        div = [rnd.choice([1, 2, 3, 4, 0, rnd.randint(5, 40), rnd.randint(-9, -2)]) for _ in range(NDIFF)]
        for i, q in enumerate(div):
            c.put(DIFF + 0x58 * i + 0x1C, le32(q))
        row["div"] = div
        if sid_ok(row):
            b = srec(row)
            stats = []
            for i in range(6):
                s = rnd.choice([rnd.randrange(NISC)] * 8 + [-1, NISC, rnd.randint(-0x8000, -2), rnd.randint(NISC, 0x7FFF)])
                stats.append(s)
                c.put(b + 0x54 + 2 * i, le16(s))
            ts = rnd.choice([rnd.randrange(NSTATES)] * 4 + [23, 23, 56, 56, -1, NSTATES, rnd.randint(-0x8000, -2)])
            c.put(b + 0x82, le16(ts))
            evs = [rnd.getrandbits(16) for _ in range(6)]
            c.put(b + 0x84, b"".join(le16(v) for v in evs))
            filt = rnd.getrandbits(32)
            c.put(b + 0x50, le32(filt))
            isc5 = {}
            for s in stats:
                if 0 <= s < NISC and s not in isc5:
                    isc5[s] = rnd.getrandbits(8)
                    c.put(ISC + 0x144 * s + 5, bytes([isc5[s]]))
            row.update(stats=stats, ts=ts, evs=evs, filt=filt, isc5={str(k2): v for k2, v in isc5.items()})
        finish_n(c, rnd, row, game, cases, exp)
    return cases, mem_nec(), {"cases": exp}


def curse_nec_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_n(row, 0)
    a1, ts = s16(row["stats"][0]), s16(row["ts"])
    if a1 < (-1 if neg != "minus1" else 0) or a1 >= NISC:
        br["norange_stat"] += 1
        return ret_n(row, 0)
    if not 0 <= ts < NSTATES:
        br["norange_state"] += 1
        return ret_n(row, 0)
    sid, lv = s16(row["sid"]), row["lvl"]
    r, ln = ev_s(row, 0x64), ev_s(row, 0x60)
    flag = int(ts in (23, 56))
    if w == "do61" or (flag and neg != "noflag"):
        ln = diff_div(row, ln)
    blk = bytearray(0x68)
    struct.pack_into("<IIi", blk, 0, game, U, flag if w == "do30" else 0)
    struct.pack_into("<IIi", blk, 0x10, sid & M32, lv & M32, ln)
    first = 0 if (w == "do30" or neg == "aura1_read") else 1
    sflag = 0
    for i in range(first, 6):
        s = s16(row["stats"][i])
        if not 0 <= s < NISC:
            struct.pack_into("<i", blk, 0x1C + 4 * i, -1)
            break
        if row["isc5"][str(s)] & 2:
            sflag = 1
        struct.pack_into("<i", blk, 0x1C + 4 * i, s)
        struct.pack_into("<i", blk, 0x34 + 4 * i, ev_s(row, 0x68 + 4 * i))
    struct.pack_into("<i", blk, 0x0C, sflag)
    struct.pack_into("<i", blk, 0x4C, ts)
    if w == "do30":
        for i, v in enumerate(row["evs"]):
            struct.pack_into("<i", blk, 0x50 + 4 * i, s16(v))
    br["search_%s" % ("div" if (w == "do61" or flag) else "len")] += 1
    if w == "do30":
        return obs_a(row, "NearTarget", {"ecx": game, "edx": row["filt"]}, [U, r, 0x005C35C0, fr(-0x7C)],
                     0x005C39A3, bit6=True, ptrs={3: bytes(blk)})
    return obs_a(row, "NearTarget", {"ecx": game, "edx": row["filt"]}, [U, r, 0x005C3DE0, fr(-0x78)],
                 0x005C40AF, bit6=True, ptrs={3: bytes(blk)})


# ------------------------------------------------------------------------------------------- corpses
CORPSE_ORDER_N = ("do31", "do55", "do58", "do59", "do63")


@family("corpse_nec", "nec")
def corpse_nec(rnd, game):
    """Do 31 (Raise Skeleton, Raise Skeletal Mage: up to COMBAT_ApplyDamage inside 0x005C2FF0 or the corpse's room
    removal 0x0061A270), do 55 (Corpse Explosion) and do 63 (Poison Explosion) up to STATE_Set, do 58 (Revive) up to
    0x0056E2F0 inside 0x005C3300, do 59 (Attract) up to 0x0056E2F0 inside 0x005C31F0."""
    cases, exp = [], []
    for k in range(1500):
        w = CORPSE_ORDER_N[k % 5]
        c = Case(FNN[w])
        row = {"w": w, "sid": pick_sid_n(rnd, w), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 0, 1))
        if row["ut"] == 0:
            row["ucls"] = rnd.choice([3, 3, 3, 2, 0, 1, 4, 5, 6])
            c.put(U + 0x04, le32(row["ucls"]))
        put_target_a(c, rnd, row, game, types=(1, 1, 1, 1, 1, 1, 0, 2, 3, 4))
        put_corpse(c, rnd, row)
        if w == "do31":
            sv = put_stats(c, rnd, U, {7: rnd.choice([rnd.randint(0, 1 << 20), rnd.getrandbits(32), 8, 7, -9])})
            row["maxhp"] = stat_of(sv, 7)
        if w == "do59" and row["t"]:
            ta = put_state_list_s(c, rnd, T, TSL, 105, p_found=0.5, stat=172)
            row["talign"] = align_of(row["tt"], ta, c, T)
        if w in ("do31", "do58") and sid_ok(row):
            b = srec(row)
            summ = rnd.randrange(NMON)
            pet = rnd.choice([rnd.randrange(NPET)] * 7 + [0xFF, 0x80, NPET, rnd.randint(NPET, 0x7F)])
            mode = rnd.choice([rnd.randrange(16), rnd.randrange(16), 0xFF, 16, rnd.randint(17, 255)])
            c.put(b + 0xBC, le16(summ))
            c.put(b + 0xBE, bytes([pet, mode]))
            row.update(summ=summ, pet=pet, mode=mode)
            row["cal"] = sor_calcs(c, rnd, row["sid"], (0xC0,))
        if w == "do63" and sid_ok(row):
            ma = rnd.choice([rnd.randrange(NREC)] * 6 + [-1, NREC, rnd.randint(-0x8000, -2)])
            c.put(srec(row) + 0x48, le16(ma))
            row["ma"] = ma
        finish_n(c, rnd, row, game, cases, exp)
    return cases, mem_nec(), {"cases": exp}


def sum_mode(m):
    """SkillSummonClass's mode out-value: summode (+0xBF, movsx) in 0..15, else 1."""
    v = m - 0x100 if m & 0x80 else m
    return v if 0 <= v < 16 else 1


def corpse_nec_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    t = tgt_unit(row)
    if w == "do59":
        if not sid_ok(row):
            br["nosid"] += 1
            return ret_n(row, 0)
        if not t:
            br["notarget"] += 1
            return ret_n(row, 0)
        if row["talign"] != 0 and neg != "align_any":
            br["aligned"] += 1
            return ret_n(row, 0)
        br["montest"] += 1
        return obs_a(row, "MonTest2F0", {"ecx": T, "edx": 0x13}, [], 0x005C321E,
                     frame=abs_ret(0x7FEFFF98, 0x005C3BE1))
    if w == "do55":
        if not t:
            br["notarget"] += 1
            return ret_n(row, 0)
        if not corpse680(row, neg):
            br["nocorpse"] += 1
            return ret_n(row, 0)
        br["stateset"] += 1
        return obs_a(row, "StateSet", {}, [T, 0x68, 1], 0x005C4E29)
    if w == "do63":
        if s16(row["sid"]) == 0:
            br["id0"] += 1
            return ret_n(row, 0)
        ma = s16(row["ma"])
        if not 0 <= ma < NREC:
            br["nomiss"] += 1                  # both range tests jump to the `mov eax, 1` exit (0x005C5EFC)
            return ret_n(row, 1 if neg != "nomiss0" else 0)
        if not t:
            br["notarget"] += 1
            return ret_n(row, 0)
        if not corpse680(row, neg):
            br["nocorpse"] += 1
            return ret_n(row, 0)
        br["stateset"] += 1
        return obs_a(row, "StateSet", {}, [T, 0x76, 1], 0x005C5EDA)
    if w == "do58":
        if s16(row["sid"]) == 0:
            br["id0"] += 1
            return ret_n(row, 0)
        pet = row["pet"] if row["pet"] < NPET else 0
        if not t:
            br["notarget"] += 1
            return ret_n(row, 0)
        r = test3300(row, neg)
        if r[0] == "v":
            br["norevive"] += 1
            return ret_n(row, 0)
        br["montest"] += 1
        fr_ = abs_ret(0x7FEFFFA4, 0x005C5738)
        fr_[fr(-0x1)] = bytes([pet])
        return obs_a(row, "MonTest2F0", {"ecx": T, "edx": 7}, [], 0x005C3340, frame=fr_)
    # do 31
    if not t:
        br["notarget"] += 1
        return ret_n(row, 0)
    if not corpse510(row, 0 if neg != "flag1" else 1):
        br["nocorpse"] += 1
        return ret_n(row, 0)
    if row["ut"] == 0 and row["ucls"] == 3:
        hp = row["maxhp"]
        q = s32(hp) // 8 if s32(hp) >= 0 else -((-s32(hp)) // 8)
        if neg == "hp4":
            q = s32(hp) >> 2
        pkt = bytearray(0x70)
        struct.pack_into("<I", pkt, 0, 0x1000)
        struct.pack_into("<H", pkt, 4, 4)
        struct.pack_into("<i", pkt, 8, q)
        struct.pack_into("<i", pkt, 0x4C, q)
        br["apply"] += 1
        return obs_a(row, "ApplyDamage", {"ecx": game, "edx": U}, [U, 0, None], 0x005C3051, ptrs={2: bytes(pkt)},
                     frame=abs_ret(0x7FEFFFA8, 0x005C4B3F))
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_n(row, 0)
    p = row["pet"]
    ps = p - 0x100 if p & 0x80 else p
    if ps < 0 or ps >= NPET:
        if neg != "pet_zero":
            br["nopet"] += 1
            return ret_n(row, 0)
        ps = 0
    tx, ty = row["tx"], row["ty"]
    room = room_of_t(row)
    br["remove"] += 1
    frame = {fr(-0x4): le32(srec(row)), fr(-0x8): le32(row["summ"]), fr(-0xC): le32(sum_mode(row["mode"])),
             fr(-0x10): le32(tx), fr(-0x14): le32(ty), fr(-0x18): le32(ps)}
    return obs_a(row, "RoomUnitRemove", {}, [room, row["tt"], row["tg"]], 0x005C4BE2, frame=frame)


# ------------------------------------------------------------------------------------------- summons
SUMMON_ORDER_N = ("do56", "do57", "do60", "do62")


@family("summon_nec", "nec")
def summon_nec(rnd, game):
    """Do 56 (Clay, Blood and Fire Golem), do 57 (IronGolem, after start 20's item test), do 60 (Bone Wall) and do 62
    (Bone Prison, its twelve pieces through 0x005C5BC0): up to the first SpawnOwnedMonster."""
    cases, exp = [], []
    for k in range(1600):
        w = SUMMON_ORDER_N[k % 4]
        c = Case(FNN[w])
        row = {"w": w, "sid": pick_sid_n(rnd, w), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1))
        put_target_a(c, rnd, row, game, types=(4, 4, 4, 1, 0) if w == "do57" else (0, 1, 1, 2, 3, 4, 5))
        if w in ("do60", "do62") and rnd.random() < 0.65:
            put_point_in_room(c, rnd, row, edge=(w == "do62"))
        if w == "do57":
            put_item_t(c, rnd, row)
            g = rnd.getrandbits(32)
            c.put(fr(-0x10), le32(g))         # the block's last word: a slot do 57 does not write before the spawn
            row["slot10"] = g
        if sid_ok(row):
            b = srec(row)
            summ = rnd.choice([rnd.randrange(NMON)] * 8 + [-1, NMON, rnd.randint(-0x8000, -2)]) if w == "do56" \
                else rnd.randrange(NMON)
            pet = rnd.choice([rnd.randrange(NPET)] * 7 + [0xFF, 0x80, NPET, rnd.randint(NPET, 0x7F)])
            mode = rnd.choice([rnd.randrange(16), rnd.randrange(16), 0xFF, 16, rnd.randint(17, 255)])
            c.put(b + 0xBC, le16(summ))
            c.put(b + 0xBE, bytes([pet, mode]))
            row.update(summ=summ, pet=pet, mode=mode)
            row["cal"] = sor_calcs(c, rnd, row["sid"], (0xC0,))
        finish_n(c, rnd, row, game, cases, exp)
    return cases, mem_nec(), {"cases": exp}


def put_point_in_room(c, rnd, row, edge=False):
    """No target unit; the caster's path target point inside a room the caster's room reaches (itself or a near
    room); for do 62 near a room's lower or right edge and the room made a town at times, so that the first pieces
    fall in town and a later one outside it."""
    c.put(UP + 0x58, le32(0))
    row.update(t=0, tlink=None)
    rooms = [r for r in ROOMS if row["rooms"][str(r)][3] >= 10 and row["rooms"][str(r)][4] >= 10]
    if not rooms:
        return
    r = rnd.choice(rooms)
    if rnd.random() < 0.7:
        c.put(UP + 0x1C, le32(r))
        row["uroom"] = r
    lid, x0, y0, ww, hh = row["rooms"][str(r)][:5]
    if edge and rnd.random() < 0.6:
        lev = 0x13200000 + 0x1000 * ROOMS.index(r)
        c.put(lev + 0x1D0, le32(1))
        row["rooms"][str(r)][0] = 1
    if edge:
        if rnd.random() < 0.5:
            x, y = x0 + rnd.randrange(4, ww - 4), y0 + hh - 1 - rnd.randrange(4)
        else:
            x, y = x0 + ww - 1 - rnd.randrange(4), y0 + rnd.randrange(4, hh - 4)
    else:
        x, y = x0 + rnd.randrange(ww), y0 + rnd.randrange(hh)
    px, py = x & 0xFFFF, y & 0xFFFF
    c.put(UP + 0x10, le16(px) + le16(py))
    row.update(px=px, py=py)


def summon_nec_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    sid, lv = s16(row["sid"]), row["lvl"]
    pet = row.get("pet", 0)
    pet = pet if (pet < NPET or neg == "pet_keep") else 0
    if w == "do56":
        if sid == 0:
            br["id0"] += 1
            return ret_n(row, 0, bit6=True)
        summ = s16(row["summ"])
        if not 0 <= summ < NMON:
            br["nosumm"] += 1
            return ret_n(row, 0, bit6=True)
        mode = row["mode"] if row["mode"] < 16 else 1
        w24 = game if neg != "w24_zero" else 0
        blk = b"".join(le32(v) for v in (0, U, summ, 0, mode, 0, 0, pet, ev_s(row, 0xC0), w24))
        br["spawn"] += 1
        return obs_a(row, "SpawnOwned", {"ecx": game}, [], 0x005C51E8, bit6=True, stk={"edx": (0, blk)})
    if w == "do57":
        r = item_test(row)
        if r[0] == "fatal":
            br["fatal"] += 1
            return obs_a(row, "Fatal", {}, [0x104A], 0x00629CDA)
        if not r[1]:
            br["noitem"] += 1
            return ret_n(row, 0)
        if sid == 0:
            br["id0"] += 1
            return ret_n(row, 0, bit6=True)
        x, y = row["tx"], row["ty"]
        w24 = row["slot10"] if neg != "w24_zero" else 0
        blk = b"".join(le32(v) for v in (1, U, row["summ"], 0, sum_mode(row["mode"]), x, y, pet, ev_s(row, 0xC0),
                                         w24))
        br["spawn"] += 1
        return obs_a(row, "SpawnOwned", {"ecx": game}, [], 0x005C537C, bit6=True, stk={"edx": (0, blk)})
    x, y, ok = target_xy(row)
    if not ok:
        br["noxy"] += 1
        return ret_n(row, 0)
    if w == "do60":
        room = room_at(row, row["uroom"], x, y)
        if not room:
            br["noroom"] += 1
            return ret_n(row, 0)
        if town_of(row, room):
            br["town"] += 1
            return ret_n(row, 0)
        if sid == 0:
            br["id0"] += 1
            return ret_n(row, 0, bit6=True)
        w24 = game if neg != "w24_zero" else 0
        blk = b"".join(le32(v) for v in (9, U, row["summ"], 0, sum_mode(row["mode"]), x, y, pet, ev_s(row, 0xC0),
                                         w24))
        br["spawn"] += 1
        return obs_a(row, "SpawnOwned", {"ecx": game}, [], 0x005C59F0, bit6=True, stk={"edx": (0, blk)})
    # do 62
    if sid == 0:
        br["id0"] += 1
        return ret_n(row, 1, bit6=True)
    for i in range(12):
        dx, dy = s32(S4.dword(BP_OFF[0] + 4 * i)), s32(S4.dword(BP_OFF[1] + 4 * i))
        X, Y = s32(x + dx), s32(y + dy)
        if neg == "bp_swap":
            X, Y = s32(x + dy), s32(y + dx)
        room = room_at(row, row["uroom"], X, Y)
        if town_of(row, room):
            continue
        mode = sum_mode(row["mode"])
        w24 = mode if neg != "w24_zero" else 0
        blk = b"".join(le32(v) for v in (9, U, row["summ"], 0, mode, X, Y, pet, ev_s(row, 0xC0), w24))
        br["spawn_piece%d" % i] += 1
        return obs_a(row, "SpawnOwned", {"ecx": game}, [], 0x005C5CBA, bit6=True, stk={"edx": (0, blk)},
                     frame={0x7FEFFFC8: le32(0x005C5D69), fr(-0x8): le32(4 * i), fr(-0xC): le32(0)})
    br["alltown"] += 1
    return ret_n(row, 1, bit6=True)


CHECKS.update({
    "start_nec": check9b("start_nec", start_nec_model, ["town_inv", "set33_skip", "flag7", "item_mode"], RS_NEC,
                         md_masked=False),
    "curse_nec": check9b("curse_nec", curse_nec_model, ["noflag", "aura1_read", "minus1"], RS_NEC, md_masked=False),
    "corpse_nec": check9b("corpse_nec", corpse_nec_model, ["notdead", "set33_skip", "hp4", "pet_zero",
                                                           "align_any", "flag1", "nomiss0"], RS_NEC, md_masked=False),
    "summon_nec": check9b("summon_nec", summon_nec_model, ["w24_zero", "pet_keep", "bp_swap"], RS_NEC,
                          md_masked=False),
})

PINS_NEC = [  # (address, mnemonic, operand substring): instructions the nec claims turn on (ADR-0015 (5))
    (0x00645523, "cmp", "eax,0xc"), (0x00645528, "cmp", "DWORD PTR [ebp+0xc],0x0"),               # 0x00645510
    (0x0064553F, "lea", "edx,[eax+0x7]"), (0x00645573, "cmp", "WORD PTR [esi+0x32],ax"),
    (0x006456A5, "lea", "edx,[eax+0x7]"), (0x00645692, "cmp", "DWORD PTR [esi+0x10],0xc"),          # 0x00645680
    (0x0063A779, "mov", "ebx,DWORD PTR [eax+0x150]"),                                                # set 33
    (0x005C330F, "mov", "edx,0x8"), (0x005C331F, "call", "0x5541b0"), (0x005C3334, "mov", "edx,0x7"),  # 0x005C3300
    (0x005C32B4, "cmp", "DWORD PTR [esi],0x4"), (0x005C32B9, "cmp", "DWORD PTR [esi+0x10],0x3"),    # start 20
    (0x00629CEF, "mov", "eax,DWORD PTR [eax+0xdc]"), (0x00629CF5, "and", "eax,0x2"),
    (0x005C3803, "cmp", "ax,0xffff"), (0x005C3803 + 4, "jl", ""),                                    # do 30
    (0x005C3400, "cmp", "ecx,0x17"), (0x005C3407, "cmp", "ecx,0x38"), (0x005C37B7, "idiv", "ecx"),
    (0x005C38F4, "mov", "cl,BYTE PTR ds:0x6ce26c"),
    (0x005C400C, "mov", "esi,0x1"), (0x005C3FF6, "lea", "ecx,[edi+0x56]"), (0x005C3FD0, "call", "0x5c37a0"),  # do 61
    (0x005C3005, "cmp", "DWORD PTR [esi+0x4],0x3"), (0x005C303C, "sar", "eax,0x3"),                 # 0x005C2FF0
    (0x005C3021, "or", "DWORD PTR [ebp-0x70],0x1000"), (0x005C3028, "or", "WORD PTR [ebp-0x6c],0x4"),
    (0x005C4B97, "movsx", "eax,BYTE PTR [ecx+0xbe]"),                                                # do 31 pettype
    (0x005C5144, "je", ""), (0x005C510F, "mov", "DWORD PTR [ebp-0x4],ecx"),                          # do 56
    (0x005C5186, "cmp", "dl,0x10"),
    (0x005C58C9, "mov", "DWORD PTR [ebp-0x14],ebx"), (0x005C59C8, "mov", "DWORD PTR [ebp-0x38],0x9"),  # do 60
    (0x005C5C8E, "mov", "DWORD PTR [ebp-0x30],0x9"), (0x005C5E3B, "cmp", "eax,0x30"),               # do 62
    (0x005C4E21, "push", "0x68"), (0x005C5ED2, "push", "0x76"),                                      # do 55, 63
    (0x005C3214, "lea", "edx,[eax+0x13]"),                                                           # 0x005C31F0
]


def cmd_static_nec(a):
    rep = Report("static")
    rep.batch = "NEC"
    A = S4.asm()
    for va, mn, sub in PINS_NEC:
        ins = A.at(va)
        rep.c["pins"] += 1
        if ins is None or ins[0] != mn or sub not in ins[1]:
            rep.bad("pin 0x%08X: %r, want %s %s" % (va, ins, mn, sub))
        else:
            rep.c["pins_ok"] += 1
    for lo, n, name in ((BITMASK, 128, "g_BitMask32"), (0x006E10E0, 20, "hash offsets"),
                        (0x006C1164, 88, "CALC_Eval jump table"), (0x006426C0, 8 + 0x6D, "town tables"),
                        (BP_OFF[0], 96, "do 62's offsets")):
        sec = S4.section_of(lo)
        flags = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.c["ro_reads"] += 1
        if flags & 0x80000000:
            rep.bad("%s 0x%08X in writable %s" % (name, lo, sec))
        rep.notes.append("%s 0x%08X: %s" % (name, lo, sec))
    rep.notes.append("do 62's offsets x: %s" % " ".join(str(s32(S4.dword(BP_OFF[0] + 4 * i))) for i in range(12)))
    rep.notes.append("do 62's offsets y: %s" % " ".join(str(s32(S4.dword(BP_OFF[1] + 4 * i))) for i in range(12)))
    st, im, rd = ref_scan(A, SK_NFUNCS)
    rep.c["data_stores"] += len(st)
    rep.c["data_imms"] += len(im)
    rep.notes.append("skills calc function count 0x%08X: %d stores (PTR or moffs), %d immediates, %d reads in .text"
                     % (SK_NFUNCS, len(st), len(im), len(rd)))
    for hlp, n_in in ((0x5C2FF0, ("do31", "do58")), (0x5C3300, ("st21", "do58")), (0x5C31F0, ("do59",)),
                      (0x5C5BC0, ("do62",)), (0x5C32A0, ("do57",))):
        sites = sorted(va for va, (mn, ops) in A.ins.items() if mn == "call" and ops.strip() == "0x%x" % hlp)
        rep.notes.append("calls of 0x%08X: %s" % (hlp, " ".join("0x%08X" % s for s in sites)))
        rep.c["helper_sites"] += len(sites)
    for name, va in sorted(FNN.items(), key=lambda kv: kv[1]):
        tab = START_TABLE if name.startswith("st") else DO_TABLE
        num = int(name[2:])
        rep.c["table_entries"] += 1
        if S4.dword(tab + 4 * num) != va:
            rep.bad("%s: table entry 0x%08X, model address 0x%08X" % (name, S4.dword(tab + 4 * num), va))
    rep.notes.append("start table 15..21: %s" % " ".join("%d:0x%08X" % (i, S4.dword(START_TABLE + 4 * i))
                                                        for i in range(15, 22)))
    rep.notes.append("do table 30..32, 55..63: %s" % " ".join("%d:0x%08X" % (i, S4.dword(DO_TABLE + 4 * i))
                                                             for i in list(range(30, 33)) + list(range(55, 64))))
    print("CATNEC static " + " ".join("%s=%d" % (k, rep.c[k]) for k in sorted(rep.c)))
    for n in rep.notes:
        print("  " + n)
    return 1 if rep.c["bad"] else 0


# ##################################################################################################################
# Batch pal (plan 0046 Phase 1, the paladin class batch): the start functions 29, 31, 35, 36, 37 and the do functions
# 64-67, 73, 79-82 and 150 of g_SkillStartFuncs (0x00732140) and g_SkillDoFuncs (0x007322B0); each (ECX game, EDX
# unit; skill id, level), `ret 8`. The conventions of 9c-nec: the call site of every boundary asserted (site control),
# the caster's and the target's seeds compared in every case, a pointer argument compared by content, where a boundary
# sits inside a helper the batch function called the helper's return address compared at its stack slot (ruling 1 of
# the lane/p46m6 review), two or more negative controls per family. New here: the aura functions' self-application
# goes through 0x0056B740 (emulated: a 16-byte context {game, unit, 0, &block} and an indirect call of its first
# argument), so AURA_ApplyToTarget (0x005CEDC0) is the boundary, entered with ECX = &context and EDX = the caster
# (its two register arguments). Emulated, not observed (new for this batch): 0x0056B740, sub_0057D690_QueuedHitFind
# (with UnitGetType 0x0044BE50 and UnitGetId 0x00451F50), 0x005D02B0 (Conversion's test, up to 0x0056E2F0) with
# sub_0063EE90_HirelingType, the mana cost 0x00644B10, SKILLS_NextPeriodicFrame, the used-skill node setters
# (0x00644560, 0x006445A0, 0x006445E0, 0x00644620), CHARSTATS_GetRecord, MONSTATS_GetRecord, the Param1 getter
# 0x004C9460, sub_00483360_MulDiv. Observed (new): AURA_ApplyToTarget, the inventory call 0x0063C8F0, 0x006633B0
# (do 67's first call: the animation data), sub_00648690_PathSetSpeed, 0x00649050 (a path call).
# ##################################################################################################################
FNP = {
    "st29": 0x005CE790, "st31": 0x005CF6B0, "st35": 0x005CFE10, "st36": 0x005D0180, "st37": 0x005DAF40,
    "do64": 0x005CE8E0, "do65": 0x005CF010, "do66": 0x005CF3A0, "do67": 0x005CF900, "do73": 0x005D0040,
    "do79": 0x005D0350, "do80": 0x005D0670, "do81": 0x005D0920, "do82": 0x005D0E90, "do150": 0x005CE9F0,
}
BOUNDS_P = dict(BOUNDS_N)
BOUNDS_P.update({
    0x005CEDC0: "AuraApply", 0x0063C8F0: "InvShield", 0x006633B0: "AnimSeq", 0x00648690: "PathSetSpeed",
    0x00649050: "Path9050",
})
BOUND_BY_NAME.update({v: k for k, v in BOUNDS_P.items()})
ALLBOUND.update(BOUNDS_P)
CHREC = 0x12640000                   # CharStats records (0xC4), DataTables+0xBC4 / +0xBC8
NCH = 7
QH = OWN + 0x3000                    # the caster's queued hits (+0xAC chain; next +0x84; packet at +0x14)
RS_PAL = [RS_HASH, RS_SKN, RS_CALC_JT, RS_BITMASK9C, RS_TOWN]
HIRE_CLS = (0x10F, 0x152, 0x167, 0x230, 0x231)   # sub_0063EE90_HirelingType's monster classes (1, 2, 3, 4, 4)


def mem_pal():
    lines = ["dword %08x %08x" % (G_PDATATABLES, DT),
             "dword %08x %08x" % (DT + 0xB64, MREC), "dword %08x %08x" % (DT + 0xB6C, NREC),
             "dword %08x 6b3a11f5" % COOKIE,
             "dword %08x %08x" % (DT + 0xB98, SREC), "dword %08x %08x" % (DT + 0xBA0, NSREC),
             "dword %08x %08x" % (DT + 0x40, SPOOL),
             "dword %08x %08x" % (DT + 0xBCC, ISC), "dword %08x %08x" % (DT + 0xBD4, NISC),
             "dword %08x %08x" % (DT + 0xA78, MSREC), "dword %08x %08x" % (DT + 0xA80, NMON),
             "dword %08x %08x" % (DT + 0xA90, MS2REC), "dword %08x %08x" % (DT + 0xA98, NMON2),
             "dword %08x %08x" % (DT + 0xC4, NSTATES), "dword %08x %08x" % (DT + 0xBF0, NPET),
             "dword %08x %08x" % (DT + 0xBC4, CHREC), "dword %08x %08x" % (DT + 0xBC8, NCH)]
    lines += ["observe %08x" % a for a in sorted(BOUNDS_P)]
    lines += ["guard %08x" % a for a in FATAL + ALLOC if a not in BOUNDS_P]
    return lines


def finish_p(c, rnd, row, game, cases, exp, dumps=()):
    finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]], dumps=dumps)


def ret_p(row, eax, bit6=False, mem=None):
    return ret_s(row, eax, bit6=bit6, mem=mem)


NODE_DUMP = (UNODE + 0x18, 16)


def put_node_full(c, rnd, row, p=0.9):
    """put_used_node plus the node's +0x24 word (written so that a setter's store is compared, never a stale word)."""
    put_used_node(c, rnd, row, p=p)
    if row["node"] is not None:
        w24 = rnd.getrandbits(32)
        c.put(UNODE + 0x24, le32(w24))
        row["node"]["w24"] = w24


def node_bytes(row, n18=None, ty=None, g=None, w24=None):
    nd = row["node"]
    vals = [nd["n18"] if n18 is None else n18, nd["ty"] if ty is None else ty, nd["g"] if g is None else g,
            nd["w24"] if w24 is None else w24]
    return {UNODE + 0x18: b"".join(le32(v) for v in vals)}


# ------------------------------------------------------------------------------------------- the aura functions
AURA_ORDER_P = ("do65", "do66", "do81", "do82")
AURA_FS = {"do65": 0x64, "do66": 0x12C, "do81": 0x128, "do82": 0x70}         # frame sizes (sub esp)
AURA_BLK = {"do65": -0x64, "do66": -0xBC, "do81": -0xB8, "do82": -0x70}      # the 0x50-byte block (ebp-relative)
AURA_RET = {"do65": 0x005CF148, "do66": 0x005CF4FA, "do81": 0x005D0A80, "do82": 0x005D0FD2}   # after 0x0056B740


def put_cost(c, rnd, row):
    """Skills manashift +0x188 (the byte is read), mana +0x18A, lvlmana +0x18C (s16)."""
    b = srec(row)
    msh = rnd.choice([8, 4, 2, rnd.randrange(32), rnd.getrandbits(16)])
    mn = rnd.choice([0, 0, rnd.randint(1, 76), rnd.randint(-0x8000, 0x7FFF)])
    lm = rnd.choice([0, 0, rnd.randint(-3, 10), rnd.randint(-0x8000, 0x7FFF)])
    c.put(b + 0x188, le16(msh) + le16(mn) + le16(lm))
    row.update(msh=msh, mn=mn, lm=lm)


def cost_p(row, neg=None):
    """0x00644B10(id, lvl): ((lvl - 1) * lvlmana + mana) << (manashift byte & 31), 32-bit."""
    v = s32(s32(s16(row["lm"]) * s32(s32(row["lvl"]) - 1)) + s16(row["mn"]))
    return s32(v << ((row["msh"] & 0xFF) & 31))


def npf_end(row, neg=None):
    """SKILLS_NextPeriodicFrame(ECX game, EDX unit; rec, id, lvl) + 1 - frame: p = perdelay calc, 5 when <= 5;
    ((frame + p - 1) / p) * p + 1 (idiv, truncating)."""
    p = ev_s(row, 0x128)
    if p <= (5 if neg != "npf6" else 6):
        p = 5 if neg != "npf6" else 6
    f = s32(row["frame"])
    n = s32(s32(cdiv(s32(f + p - 1), p) * p) + 1)
    return s32(n + 1 - f)


@family("aura_pal", "pal")
def aura_pal(rnd, game):
    """Do 65 (the paladin auras, Barbs, Wolverine and Oak Sage), do 66 (Holy Fire, Holy Shock, Sanctuary,
    Conviction), do 81 (Holy Freeze), do 82 (Redemption): the mana cost and gate, the period end, the 0x50-byte
    block, up to AURA_ApplyToTarget through 0x0056B740 (or do 65's SKILLS_ForUnitsInRange)."""
    cases, exp = [], []
    for k in range(1600):
        w = AURA_ORDER_P[k % 4]
        c = Case(FNP[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 0, 1, 3))
        fields = (0x68, 0x6C, 0x70, 0x74, 0x78, 0x7C, 0x128, 0x64) if w == "do65" else \
            (0xA4, 0xA8, 0xAC, 0xB0, 0xB4, 0x128)
        row["cal"] = sor_calcs(c, rnd, row["sid"], fields)
        frame = rnd.choice([rnd.randint(0, 30), rnd.randint(0, 100000), rnd.getrandbits(31)])
        c.put(game + 0xA8, le32(frame))
        row["frame"] = frame
        mana = None
        if sid_ok(row):
            b = srec(row)
            put_cost(c, rnd, row)
            cost = cost_p(row)
            mana = rnd.choice([cost, cost - 1, cost + 1, rnd.randint(0, 0x7FFFF), rnd.getrandbits(32)]) & M32
            st = [rnd.choice([rnd.randrange(NISC)] * 6 + [-1, rnd.randint(-0x8000, -2), rnd.randint(NISC, 0x7FFF)])
                  for _ in range(6)]
            c.put(b + 0x54, b"".join(le16(s) for s in st))
            pst = [rnd.choice([rnd.randrange(NISC)] * 4 + [-1, rnd.randint(-0x8000, -2), rnd.randint(NISC, 0x7FFF)])
                   for _ in range(5)]
            c.put(b + 0x98, b"".join(le16(s) for s in pst))
            states = [rnd.choice([rnd.randrange(1, NSTATES)] * 5 + [0, -1, NSTATES, rnd.randint(-0x8000, -2)])
                      for _ in range(2)]
            c.put(b + 0x80, le16(states[0]) + le16(states[1]))
            ps = rnd.choice([-1, -1, 0, rnd.randrange(1, NSTATES), rnd.randint(-0x8000, 0x7FFF)])
            c.put(b + 0x94, le16(ps))
            filt = rnd.getrandbits(32)
            c.put(b + 0x50, le32(filt))
            row.update(st=st, pst=pst, ast=states[0], tst=states[1], ps=ps, filt=filt)
        sv = put_stats(c, rnd, U, {8: mana})
        row["mana"] = stat_of(sv, 8)
        finish_p(c, rnd, row, game, cases, exp)
    return cases, mem_pal(), {"cases": exp}


def aura_gate(row, neg=None):
    """The stats are evaluated unless the caster is a player (type 0) whose mana is below the cost (signed)."""
    if neg == "nogate":
        return True
    return row["ut"] != 0 or s32(row["mana"]) >= cost_p(row)


def aura_pal_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_p(row, 0)
    sid, lv = s16(row["sid"]), row["lvl"]
    ast, tst = s16(row["ast"]), s16(row["tst"])
    if w != "do65" and not 0 <= ast < NSTATES:
        br["nostate"] += 1
        return ret_p(row, 0)
    blk = bytearray(0x50)
    struct.pack_into("<III", blk, 4, sid & M32, lv & M32, npf_end(row, neg) & M32)
    gate = aura_gate(row, neg)
    br["gate" if gate else "nogate"] += 1
    if w == "do65":
        if s16(row["ps"]) > 0:
            struct.pack_into("<i", blk, 0x48, s16(row["ps"]))
        if gate:
            for i in range(6 if neg != "len5" else 5):
                s = s16(row["st"][i])
                if s < 0:
                    break
                struct.pack_into("<i", blk, 0x10 + 4 * i, s)
                struct.pack_into("<i", blk, 0x28 + 4 * i, ev_s(row, 0x68 + 4 * i))
        if (0 < ast or (neg == "as0" and ast == 0)) and ast < NSTATES:
            struct.pack_into("<i", blk, 0, ast)
        elif 0 <= tst < NSTATES:
            struct.pack_into("<i", blk, 0, tst)
            br["search"] += 1
            return obs_a(row, "ForUnitsInRange", {"ecx": game, "edx": U},
                         [0, 0, ev_s(row, 0x64), row["filt"], 0x005CEDC0, fr(-0x64), 1, 0x006E323C, 0x1F6],
                         0x005CF229, ptrs={5: bytes(blk)})
        else:
            br["nostates"] += 1
            return ret_p(row, 1)
    else:
        struct.pack_into("<i", blk, 0, ast)
        if w == "do81":
            struct.pack_into("<I", blk, 0x4C, 0x005D0770)
        for i in range(5):
            s = s16(row["pst"][i])
            struct.pack_into("<i", blk, 0x10 + 4 * i, s)
            if w == "do82" and s < 0 and neg != "neg82":
                continue
            if gate:
                struct.pack_into("<i", blk, 0x28 + 4 * i, ev_s(row, 0xA4 + 4 * i))
    slot = (FRAME_EBP - AURA_FS[w] - 0x18) & M32
    ctx = (slot - 0x14) & M32
    cb = le32(game) + le32(U) + le32(0) + le32(fr(AURA_BLK[w]))
    br["apply"] += 1
    return obs_a(row, "AuraApply", {"ecx": ctx, "edx": U}, [], 0x0056B75F, stk={"ecx": (0, cb)},
                 frame={fr(AURA_BLK[w]): bytes(blk), slot: le32(AURA_RET[w])})


# ------------------------------------------------------------------------------------------- melee and hit tests
MELEE_ORDER_P = ("st29", "st35", "st36", "st37", "do64", "do79", "do150")


def put_queued(c, rnd, row):
    """The caster's queued hits (U+0xAC): 0-3 nodes {+4 type, +8 guid, +0xC target type, +0x10 target guid, packet
    at +0x14 (+0x1C its +0x08), +0x84 next}; one matches the caster and the target at times, the others differ in one
    word."""
    n = rnd.choice([0, 1, 1, 2, 3])
    nodes = [QH + 0x100 * i for i in range(n)]
    c.put(U + 0xAC, le32(nodes[0] if nodes else 0))
    t = row["t"]
    tt, tg = (row["tt"], u32f(c, T + 0x0C)) if t else (6, 0xFFFFFFFF)
    match = rnd.randrange(n) if n and t and rnd.random() < 0.7 else -1
    q = []
    for i, nd in enumerate(nodes):
        w = [row["ut"], row["ug"], tt, tg]
        if i != match:
            j = rnd.randrange(4)
            w[j] = (w[j] + rnd.choice([1, 2, 0x80, rnd.getrandbits(32) | 1])) & M32
        dmg = rnd.choice([rnd.randint(0, 0x10000), rnd.getrandbits(32), rnd.randint(0, 255) << 8])
        c.put(nd + 0x04, b"".join(le32(v) for v in w))
        c.put(nd + 0x1C, le32(dmg))
        c.put(nd + 0x84, le32(nodes[i + 1] if i + 1 < n else 0))
        q.append({"w": w, "dmg": dmg, "a": nd})
    row["q"] = q


def qhf(row, neg=None):
    """sub_0057D690_QueuedHitFind(ECX caster, EDX target): the first node whose four words are the caster's type and
    guid and the target's type and guid -> node + 0x14 (the packet), else 0."""
    t = row["t"]
    want = [row["ut"], row["ug"], row["tt"] if t else 6, row["tguid"] if t else 0xFFFFFFFF]
    for nd in row["q"]:
        w = nd["w"]
        if (w == want) or (neg == "qhf_tgt" and w[:2] == want[:2]):
            return nd
    return None


@family("melee_pal", "pal")
def melee_pal(rnd, game):
    """Start 29 (Sacrifice), 35 (Vengeance), 36 (Holy Shield), 37 (Zeal, Fury), do 64 (Sacrifice), do 79
    (Conversion), do 150 (Smite): the used skill, the target, the queued hit, up to InMeleeRange, MeleeHitTest, the
    inventory call, the nearest-unit search, COMBAT_ApplyDamage, 0x0056E2F0 or COMBAT_DeliverQueued."""
    cases, exp = [], []
    for k in range(1750):
        w = MELEE_ORDER_P[k % 7]
        c = Case(FNP[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1) if w != "do79" else (0, 0, 1, 3))
        put_inv_a(c, rnd, row)
        put_target_a(c, rnd, row, game, types=(0, 1, 1, 1, 2, 3, 4, 5) if w != "do79" else (1, 1, 1, 1, 0, 2, 4))
        row["tguid"] = u32f(c, T + 0x0C) if row["t"] else None
        dumps = ()
        if w in ("st29", "st35", "st37"):
            put_node_full(c, rnd, row)
            dumps = (NODE_DUMP,)
        if w == "st35":
            row["cal"] = sor_calcs(c, rnd, row["sid"], (0x1A0,))
            put_tohit(c, rnd, row)
        if w == "st37":
            row["cal"] = sor_calcs(c, rnd, row["sid"], (0x138,))
            put_reach(c, rnd, row)
        if w in ("do64", "do79"):
            put_queued(c, rnd, row)
        if w == "do64":
            row["cal"] = sor_calcs(c, rnd, row["sid"], (0x13C,))
            if row["t"]:
                hp = rnd.choice([rnd.randint(0, 0x10000), rnd.getrandbits(32), rnd.randint(0, 2000) << 8])
                if row["q"] and rnd.random() < 0.3:
                    hp = (row["q"][0]["dmg"] + rnd.choice([-1, 0, 1])) & M32
                row["thp"] = stat_of(put_stats(c, rnd, T, {6: hp}), 6)
        if w == "do79":
            if sid_ok(row):
                c.put(srec(row) + 0x82, le16(rnd.choice([rnd.randrange(NSTATES), -1, NSTATES])))
            if row["t"]:
                tcls = rnd.choice([rnd.randrange(NMON), rnd.randrange(600)] * 3 + list(HIRE_CLS))
                c.put(T + 0x04, le32(tcls))
                row["tcls"] = tcls
                ta = put_state_list_s(c, rnd, T, TSL, 105, p_found=0.5, stat=172)
                row["talign"] = align_of(row["tt"], ta, c, T)
        finish_p(c, rnd, row, game, cases, exp, dumps=dumps)
    return cases, mem_pal(), {"cases": exp}


def hire_type_p(cls_t, tt):
    """sub_0063EE90_HirelingType(unit): a monster of class 271, 338, 359, 560 or 561 -> 1, 2, 3, 4, 4; else 0."""
    if tt != 1:
        return 0
    return {0x10F: 1, 0x152: 2, 0x167: 3, 0x230: 4, 0x231: 4}.get(cls_t & M32, 0)


def melee_pal_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    t = tgt_unit(row)
    if w == "st36":
        if not row["inv"]:
            br["noinv"] += 1
            return ret_p(row, 0 if neg != "inv_any" else 1)
        br["invshield"] += 1
        return obs_a(row, "InvShield", {}, [row["inv"], 0], 0x005D0192)
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_p(row, 0, bit6=False)
    if w in ("st29", "st35", "st37") and row["node"] is None:
        br["noused"] += 1
        return ret_p(row, 0)
    if w == "st37":
        a = reach_a(row, None)
        if a[0] == "obs":
            br["reach_" + a[1]] += 1
            return sub_obs(row, a)
        r = s32(a[1] + (4 if neg != "reach0" else 0))
        if not t:
            br["near"] += 1
            return obs_a(row, "NearestUnit", {"ecx": game, "edx": U}, [0, 0, r, 0x20003, 0xFFFFFFFF, 0], 0x005DAFAE)
        br["settarget"] += 1
        return ret_p(row, 1, mem=node_bytes(row, n18=ev_s(row, 0x138), ty=row["tt"], g=row["tguid"]))
    if w == "do79":
        if not t:
            br["notarget"] += 1
            return ret_p(row, 0, bit6=True)
        q = qhf(row, neg)
        if q is not None and hire_type_p(row["tcls"], row["tt"]) == 0 and row["tt"] == 1 and \
                (row["talign"] == 0 or neg == "align_any"):
            br["montest"] += 1
            return obs_a(row, "MonTest2F0", {"ecx": T, "edx": 0xB}, [], 0x005D0305, bit6=True,
                         frame=abs_ret(0x7FEFFFD4, 0x005D03CC))
        br["deliver_" + ("found" if q is not None else "none")] += 1
        return obs_a(row, "DeliverQueued", {"ecx": game, "edx": U}, [T, 0], 0x005D03FF, bit6=True)
    if not t:
        br["notarget"] += 1
        return ret_p(row, 0)
    if w in ("st29", "do150"):
        br["meleerange"] += 1
        return obs_a(row, "InMeleeRange", {}, [U, T, 0], 0x005CE7F1 if w == "st29" else 0x005CEA46)
    if w == "st35":
        br["hittest"] += 1
        return obs_a(row, "MeleeHitTest", {"ecx": game, "edx": U}, [T, tohit_a(row), 0], 0x005CFE9A,
                     frame={fr(-0x80): bytes(0x70)})
    # do 64
    q = qhf(row, neg)
    if q is None:
        br["noqueued"] += 1
        return ret_p(row, 1)
    v = s32(q["dmg"])
    hp = s32(row["thp"])
    if hp < v and neg != "hp_nomin":
        v = hp
    d = muldiv(v, ev_s(row, 0x13C), 100)
    pkt = bytearray(0x70)
    struct.pack_into("<I", pkt, 0, 0x1000)
    struct.pack_into("<i", pkt, 8, d)
    struct.pack_into("<i", pkt, 0x4C, d)
    br["selfhit"] += 1
    return obs_a(row, "ApplyDamage", {"ecx": game, "edx": U}, [U, 0, fr(-0x78)], 0x005CE9C1, ptrs={2: bytes(pkt)})


# ------------------------------------------------------------------------------------------- charge and missiles
MOVE_ORDER_P = ("st31", "do67", "do73", "do80")


@family("move_pal", "pal")
def move_pal(rnd, game):
    """Start 31 (Charge, SerpentCharge: the used skill's words, the run speed, up to PathSetSpeed, 0x00649050 or
    InMeleeRange), do 67 (Charge: up to its animation-data call 0x006633B0), do 73 (Blessed Hammer) and do 80 (Fist of
    the Heavens) up to MissileCreate."""
    cases, exp = [], []
    for k in range(1600):
        w = MOVE_ORDER_P[k % 4]
        c = Case(FNP[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1, 1))
        dumps = ()
        if w in ("st31", "do67"):
            put_node_full(c, rnd, row)
            dumps = (NODE_DUMP,)
        if w == "st31":
            if rnd.random() < 0.08:
                c.put(U + 0x2C, le32(0))
                row["upath"] = 0
            else:
                row["upath"] = UP
            if row["ut"] == 0:
                row["ucls"] = rnd.choice([rnd.randrange(NCH)] * 6 + [NCH, rnd.randint(NCH, 300)])
                c.put(U + 0x04, le32(row["ucls"]))
            elif rnd.random() < 0.6:
                row["ucls"] = rnd.randrange(NMON)
                c.put(U + 0x04, le32(row["ucls"]))
            run = [rnd.getrandbits(8) for _ in range(NCH)]
            for i in range(NCH):
                c.put(CHREC + 0xC4 * i + 0x41, bytes([run[i]]))
            mrun = [rnd.choice([rnd.randint(0, 20), rnd.randint(-0x8000, 0x7FFF)]) for _ in range(NMON)]
            for i in range(NMON):
                c.put(MSREC + 0x1A8 * i + 0x34, le16(mrun[i]))
            row.update(run=run, mrun=mrun)
            if sid_ok(row):
                p1 = rnd.choice([rnd.randint(-50, 3600), 180, rnd.getrandbits(32)])
                c.put(srec(row) + 0x148, le32(p1))
                row["p1"] = p1
            v67 = rnd.choice([None, 0, rnd.randint(-100, 49), 50, 51, rnd.randint(51, 400), rnd.getrandbits(32)])
            row["v67"] = stat_of(put_stats(c, rnd, U, {67: v67}), 67)
        put_target_a(c, rnd, row, game)
        if w in ("do73", "do80") and sid_ok(row):
            put_bycharge(c, rnd, row)
        finish_p(c, rnd, row, game, cases, exp, dumps=dumps)
    return cases, mem_pal(), {"cases": exp}


def charge_speed(row, neg=None):
    """Start 31's speed: MulDiv(base, max(stat 67, 50) + Param1, 100); base = CharStats +0x41 << 8 for a player,
    MonStats +0x34 (s16) << 8 for a monster, 0x100 without a record."""
    if row["ut"] == 0:
        cl = row["ucls"]
        base = (row["run"][cl] << 8) if 0 <= s32(cl) < NCH and neg != "base100" else 0x100
    else:
        cl = row["ucls"]
        base = s32(s16(row["mrun"][cl]) << 8) if 0 <= s32(cl) < NMON else 0x100
    v = s32(row["v67"])
    if v <= 50 and neg != "v67_floor":
        v = 50
    return muldiv(base, s32(v + row["p1"]), 100)


def move_pal_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_p(row, 0)
    sid, lv = s16(row["sid"]), row["lvl"]
    t = tgt_unit(row)
    if w in ("st31", "do67") and row["node"] is None:
        br["noused"] += 1
        return ret_p(row, 0)
    if w == "do67":
        br["anim"] += 1
        return obs_a(row, "AnimSeq", {}, [U], 0x005CF956)
    if w == "st31":
        if not row["upath"]:
            br["nopath"] += 1
            return ret_p(row, 0)
        if t:
            br["meleerange"] += 1
            return obs_a(row, "InMeleeRange", {}, [U, T, 0], 0x005CF728)
        nb = node_bytes(row, n18=6, ty=0, w24=7)
        if row["ut"] != 0 and 0 <= s32(row["ucls"]) < NMON:
            br["mon_path"] += 1
            return obs_a(row, "Path9050", {}, [UP], 0x005CF82B, mem=nb)
        br["speed_" + ("player" if row["ut"] == 0 else "mon_norec")] += 1
        return obs_a(row, "PathSetSpeed", {}, [UP, charge_speed(row, neg)], 0x005CF873, mem=nb)
    m = bycharge(row)
    if m <= 0 and not (neg == "m0" and m == 0):
        br["nomiss"] += 1
        return ret_p(row, 0)
    if w == "do73":
        x, y, ok = target_xy(row)
        if not ok:
            br["noxy"] += 1
            return ret_p(row, 0)
        kw = dict(flags=0x20, owner=U, source=U, cls=m, tx=x, ty=y, skill=sid, lvl=lv)
        if neg == "xy73":
            kw.update(x=row["ux"], y=row["uy"])
        br["hammer"] += 1
        return obs_a(row, "MissileCreate", {"ecx": game}, [], 0x005D00ED, bit6=True, stk={"edx": (0, blk9d(**kw))})
    if not t:
        br["notarget"] += 1
        return ret_p(row, 0)
    blk = blk9d(flags=1, owner=U, cls=m, x=row["tx"], y=row["ty"], skill=sid, lvl=lv)
    br["fist"] += 1
    return obs_a(row, "MissileCreate", {"ecx": game}, [], 0x005D071B, bit6=(neg == "bit6_80"),
                 stk={"edx": (0, blk)})


CHECKS.update({
    "aura_pal": check9b("aura_pal", aura_pal_model, ["nogate", "npf6", "len5", "as0", "neg82"], RS_PAL,
                        md_masked=False),
    "melee_pal": check9b("melee_pal", melee_pal_model, ["inv_any", "reach0", "qhf_tgt", "hp_nomin", "align_any"],
                         RS_PAL, md_masked=False),
    "move_pal": check9b("move_pal", move_pal_model, ["base100", "v67_floor", "m0", "xy73", "bit6_80"], RS_PAL,
                        md_masked=False),
})

PINS_PAL = [  # (address, mnemonic, operand substring): instructions the pal claims turn on (ADR-0015 (5))
    (0x00644B4B, "imul", "eax,edx"), (0x00644B5D, "shl", "eax,cl"), (0x00644B55, "mov", "cl,BYTE PTR [ecx+0x188]"),
    (0x0056CD70, "cmp", "ecx,0x5"), (0x0056CD73, "jg", ""), (0x0056CD85, "idiv", "ecx"),             # NPF
    (0x0056B75C, "call", "DWORD PTR [ebp+0x8]"), (0x0056B755, "mov", "DWORD PTR [ebp-0x8],0x0"),     # 0x0056B740
    (0x005CF0C4, "jl", ""), (0x005CF0DF, "jl", ""), (0x005CF117, "jle", ""), (0x005CF1D8, "jl", ""),  # do 65
    (0x005CF0AD, "jle", ""), (0x005CF0B2, "mov", "DWORD PTR [ebp-0x1c],edx"),
    (0x005CF3EC, "jl", ""), (0x005CF4E2, "jl", ""), (0x005CF4B1, "jl", ""),                            # do 66
    (0x005D0A02, "mov", "DWORD PTR [ebp-0x6c],0x5d0770"), (0x005D0A62, "cmp", "eax,0x5"),              # do 81
    (0x005D0F7C, "jl", ""), (0x005D0FB7, "cmp", "ecx,0x5"),                                            # do 82
    (0x0057D6F0, "lea", "eax,[esi+0x14]"), (0x0057D6E0, "mov", "esi,DWORD PTR [esi+0x84]"),           # QHF
    (0x005CE973, "jge", ""), (0x005CE954, "or", "DWORD PTR [ebp-0x78],0x1000"),                       # do 64
    (0x005D02FB, "lea", "edx,[eax+0xb]"), (0x005D02DC, "push", "ebx"),                                # 0x005D02B0
    (0x005D0390, "or", "DWORD PTR [edi+0xc4],0x40"),                                                   # do 79
    (0x005D0180, "mov", "eax,DWORD PTR [edx+0x60]"),                                                   # start 36
    (0x005DAF9F, "push", "0x20003"),                                                                   # start 37
    (0x005CF844, "mov", "edi,0x32"), (0x005CF842, "jg", ""), (0x005CF7F2, "mov", "ch,BYTE PTR [eax+0x41]"),  # st 31
    (0x005CF808, "movsx", "eax,WORD PTR [eax+0x34]"), (0x005CF7DB, "mov", "DWORD PTR [ebp-0x4],0x100"),
    (0x004C9484, "mov", "eax,DWORD PTR [ecx+0x148]"),
    (0x005D008A, "jle", ""), (0x005D00D2, "mov", "DWORD PTR [ebp-0x64],0x20"),                        # do 73
    (0x005D06BE, "jle", ""), (0x005D06E5, "mov", "DWORD PTR [ebp-0x64],0x1"),                         # do 80
]


def cmd_static_pal(a):
    rep = Report("static")
    rep.batch = "PAL"
    A = S4.asm()
    for va, mn, sub in PINS_PAL:
        ins = A.at(va)
        rep.c["pins"] += 1
        if ins is None or ins[0] != mn or sub not in ins[1]:
            rep.bad("pin 0x%08X: %r, want %s %s" % (va, ins, mn, sub))
        else:
            rep.c["pins_ok"] += 1
    for lo, n, name in ((BITMASK, 128, "g_BitMask32"), (0x006E10E0, 20, "hash offsets"),
                        (0x006C1164, 88, "CALC_Eval jump table"), (0x006426C0, 8 + 0x6D, "town tables")):
        sec = S4.section_of(lo)
        flags = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.c["ro_reads"] += 1
        if flags & 0x80000000:
            rep.bad("%s 0x%08X in writable %s" % (name, lo, sec))
        rep.notes.append("%s 0x%08X: %s" % (name, lo, sec))
    st, im, rd = ref_scan(A, SK_NFUNCS)
    rep.c["data_stores"] += len(st)
    rep.c["data_imms"] += len(im)
    rep.notes.append("skills calc function count 0x%08X: %d stores (PTR or moffs), %d immediates, %d reads in .text"
                     % (SK_NFUNCS, len(st), len(im), len(rd)))
    rng = {name: (va, va + 0x800) for name, va in FNP.items()}
    for hlp in (0x56B740, 0x5D02B0, 0x56E510, 0x622870):
        sites = sorted(va for va, (mn, ops) in A.ins.items() if mn == "call" and ops.strip() == "0x%x" % hlp)
        rep.notes.append("calls of 0x%08X: %s" % (hlp, " ".join("0x%08X" % s for s in sites)))
        rep.c["helper_sites"] += len(sites)
    for name, va in sorted(FNP.items(), key=lambda kv: kv[1]):
        tab = START_TABLE if name.startswith("st") else DO_TABLE
        num = int(name[2:])
        rep.c["table_entries"] += 1
        if S4.dword(tab + 4 * num) != va:
            rep.bad("%s: table entry 0x%08X, model address 0x%08X" % (name, S4.dword(tab + 4 * num), va))
    rep.notes.append("start table 29, 31, 35, 36, 37: %s" % " ".join(
        "%d:0x%08X" % (i, S4.dword(START_TABLE + 4 * i)) for i in (29, 31, 35, 36, 37)))
    rep.notes.append("do table 64-67, 73, 79-82, 150: %s" % " ".join(
        "%d:0x%08X" % (i, S4.dword(DO_TABLE + 4 * i)) for i in (64, 65, 66, 67, 73, 79, 80, 81, 82, 150)))
    print("CATPAL static " + " ".join("%s=%d" % (k, rep.c[k]) for k in sorted(rep.c)))
    for n in rep.notes:
        print("  " + n)
    return 1 if rep.c["bad"] else 0


# ##################################################################################################################
# Batch bar (plan 0046 Phase 1, the barbarian class batch): the start functions 32-34 and 38-41 and the do functions 2,
# 9, 68-72 and 74-78 of g_SkillStartFuncs (0x00732140) and g_SkillDoFuncs (0x007322B0); each (ECX game, EDX unit;
# skill id, level), `ret 8`. The conventions of 9c-pal: the call site of every boundary asserted (site control), the
# caster's and the target's seeds compared in every case, a pointer argument compared by content, where a boundary sits
# inside a helper the batch function called the helper's return address compared at its absolute stack slot (ruling 1
# of the lane/p46m6 review), register arguments a boundary callee reads before it writes them compared (ruling 1 of
# the lane/p46m8 review), two or more negative controls per family. Emulated, not observed (new for this batch):
# 0x00645590 and 0x006455E0 (the corpse tests) with 0x00621F60, UNIT_HasState (0x00639DF0, 0x00625B70),
# SKILLS_GetUnitSkill (0x006439F0 -> 0x00643810), 0x00571B70 up to its STATE_Set, UNIT_SetUsedSkill (0x00620210,
# 0x00643990), the leap helpers 0x005D9CE0 and 0x005D9A10 up to their free-spot call, 0x00645CA0 (leap attack's point)
# up to its collision test, sub_006417F0_UnitDistance, UNIT_GetSizeX (0x00620510), the path getters 0x006488C0,
# 0x00648900, 0x00648A00, 0x00648A10, 0x00649180, PathSetCollMask (0x00648CE0), 0x005D8510 up to 0x0056E2F0,
# 0x0056BBC0 up to SKILLS_ForUnitsInRange, UnitGetWeapon up to its inventory query; skills/0008-0011's emulated helpers
# (UNIT_GetTargetUnit, UNIT_GetUsedSkill, SKILLS_GetTargetXY, SrvMissileByCharge, NovaAtUnit up to MissileCreate,
# QueuedHitFind, UNIT_FindStatListByState, UnitIsDead, RoomIsTown, RoomAtSubtile, the node getters and setters).
# Observed (new): 0x0056E520 (stat 68's list), UnitQueueEvent (0x005417D0), 0x0064E7B0 (a free spot near a point),
# PathSetType (0x00648CF0), sub_005D9C80_MonSkillAttackDo, 0x0064D910 (a collision test), 0x005D9460, 0x00553DC0,
# 0x006212C0, 0x005DA120, 0x005D9F70, 0x005DA660 (the whirlwind and leap-attack continuations).
# ##################################################################################################################
FNB = {
    "st32": 0x005D7EA0, "st33": 0x005D80C0, "st34": 0x005D8760, "st38": 0x005D8F50, "st39": 0x005D97F0,
    "st40": 0x005D9D50, "st41": 0x005DA540,
    "do2": 0x0056F1F0, "do9": 0x005D8E00, "do68": 0x005D83E0, "do69": 0x005D81C0, "do70": 0x005D8470,
    "do71": 0x005D8570, "do72": 0x005D8780, "do74": 0x005D88B0, "do75": 0x005D89B0, "do76": 0x005D9580,
    "do77": 0x005DA370, "do78": 0x005DA7E0,
}
BOUNDS_B = dict(BOUNDS_P)
BOUNDS_B.update({
    0x0056E520: "AttackRate", 0x005417D0: "QueueEvent", 0x0064E7B0: "FreeNear", 0x00648CF0: "PathSetType",
    0x005D9C80: "MonSkillAtk", 0x0064D910: "CollTest910", 0x005D9460: "Ww9460", 0x00553DC0: "Mode553DC0",
    0x006212C0: "Mode6212C0", 0x005DA120: "Leap5DA120", 0x005D9F70: "Leap5D9F70", 0x005DA660: "Leap5DA660",
})
BOUND_BY_NAME.update({v: k for k, v in BOUNDS_B.items()})
ALLBOUND.update(BOUNDS_B)
NOVL = 40                            # DataTables+0xBC0, the overlay count do 2 tests srvoverlay against
SKN_B = [OSK + 0x400 + 0x80 * i for i in range(3)]     # SKILLS_GetUnitSkill's chain (list +0x04, next +0x04)
SKR_B = [OSK + 0x600 + 0x10 * i for i in range(3)]     # each node's +0x00 record (s16 id at +0x00)
GAMEPOOL = 0x5EED0000                # the game's +0x1C (the stat-list pool argument)
RS_BAR = [RS_HASH, RS_SKN, RS_CALC_JT, RS_BITMASK9C, RS_TOWN, RS_SIZE_JT, RS_NOVA]


def mem_bar():
    lines = ["dword %08x %08x" % (G_PDATATABLES, DT),
             "dword %08x %08x" % (DT + 0xB64, MREC), "dword %08x %08x" % (DT + 0xB6C, NREC),
             "dword %08x 6b3a11f5" % COOKIE,
             "dword %08x %08x" % (DT + 0xB98, SREC), "dword %08x %08x" % (DT + 0xBA0, NSREC),
             "dword %08x %08x" % (DT + 0x40, SPOOL),
             "dword %08x %08x" % (DT + 0xBCC, ISC), "dword %08x %08x" % (DT + 0xBD4, NISC),
             "dword %08x %08x" % (DT + 0xA78, MSREC), "dword %08x %08x" % (DT + 0xA80, NMON),
             "dword %08x %08x" % (DT + 0xA90, MS2REC), "dword %08x %08x" % (DT + 0xA98, NMON2),
             "dword %08x %08x" % (DT + 0xC4, NSTATES), "dword %08x %08x" % (DT + 0xBF0, NPET),
             "dword %08x %08x" % (DT + 0x150, MASK33), "dword %08x %08x" % (DT + 0xBC0, NOVL)]
    lines += ["observe %08x" % a for a in sorted(BOUNDS_B)]
    lines += ["guard %08x" % a for a in FATAL + ALLOC if a not in BOUNDS_B]
    return lines


def finish_b(c, rnd, row, game, cases, exp, dumps=()):
    finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]], dumps=dumps)


def ret_b(row, eax, bit6=False, mem=None):
    return ret_s(row, eax, bit6=bit6, mem=mem)


def put_game_b(c, rnd, row, game):
    frame = rnd.choice([rnd.randint(0, 30), rnd.randint(0, 100000), rnd.getrandbits(31)])
    c.put(game + 0xA8, le32(frame))
    c.put(game + 0x1C, le32(GAMEPOOL))
    row["frame"] = frame


def put_unit_skills(c, rnd, row):
    """SKILLS_GetUnitSkill(ECX unit, EDX id) -> 0x00643810: U+0xA8 -> the skill list, +0x04 the chain (next +0x04);
    a node whose record's s16 +0x00 is the id and whose +0x3C is 0 qualifies; the first one is kept, a later one
    replaces it when its +0x34 is -1, or when the kept one's +0x34 is not -1 and its +0x28 is greater (signed). The
    chosen node's +0x0C, +0x18, +0x1C, +0x20, +0x24 are written (the getters and setters read and write them)."""
    if rnd.random() < 0.06:
        c.put(U + 0xA8, le32(0))
        row["skn"] = None
        return
    c.put(U + 0xA8, le32(OSK))
    n = rnd.choice([0, 1, 1, 1, 2, 3])
    c.put(OSK + 0x04, le32(SKN_B[0] if n else 0))
    sid = s16(row["sid"])
    nodes = []
    for i in range(n):
        nd = SKN_B[i]
        rid = sid if rnd.random() < 0.85 else rnd.choice([sid + 1, rnd.randrange(NSREC), -1])
        w3c = 0 if rnd.random() < 0.9 else rnd.getrandbits(32) | 1
        w34 = rnd.choice([0xFFFFFFFF, 0xFFFFFFFF, rnd.randint(0, 5), rnd.getrandbits(32)])
        w28 = rnd.choice([rnd.randint(0, 40), rnd.getrandbits(32)])
        c.put(nd + 0x00, le32(SKR_B[i]))
        c.put(SKR_B[i], le16(rid))
        c.put(nd + 0x04, le32(SKN_B[i + 1] if i + 1 < n else 0))
        c.put(nd + 0x28, le32(w28))
        c.put(nd + 0x34, le32(w34))
        c.put(nd + 0x3C, le32(w3c))
        f0c = rnd.choice([rnd.getrandbits(32), rnd.getrandbits(16), 0, 1, 1, 1, 5, 3, 2, 0x100, 0x80, 0x200,
                          0x1080, 0x300, 0x281])
        n18 = rnd.choice([0, rnd.getrandbits(16), rnd.getrandbits(16), rnd.getrandbits(32)])
        n1c = rnd.choice([0, rnd.getrandbits(16), rnd.getrandbits(16), rnd.getrandbits(32)])
        w20, w24 = rnd.getrandbits(32), rnd.getrandbits(32)
        c.put(nd + 0x0C, le32(f0c))
        c.put(nd + 0x18, le32(n18) + le32(n1c) + le32(w20) + le32(w24))
        nodes.append({"a": nd, "rid": rid, "w3c": w3c, "w34": w34, "w28": w28, "f0c": f0c, "n18": n18, "n1c": n1c,
                      "w20": w20, "w24": w24})
    row["skn"] = nodes


def unit_skill(row, neg=None):
    """SKILLS_GetUnitSkill(U, id) -> the node dict or None (see put_unit_skills)."""
    if row["skn"] is None:
        return None
    sid = s32(row["sid"])
    best = None
    for nd in row["skn"]:
        if s16(nd["rid"]) != sid or nd["w3c"] != 0:
            continue
        if best is None:
            best = nd
        elif nd["w34"] == 0xFFFFFFFF and neg != "sk34":
            best = nd
        elif best["w34"] == 0xFFFFFFFF and neg != "sk34":
            continue
        elif s32(nd["w28"]) > s32(best["w28"]):
            best = nd
    return best


def put_dead_u(c, rnd, row):
    """sub_005541B0_UnitIsDead(U): +0xC6 bit 0; a player in mode 0 or 17, a monster in mode 0 or 12."""
    c6 = rnd.choice([0, 0, 0, 0, 1, rnd.getrandbits(8)])
    mode = rnd.choice([rnd.randrange(1, 18), rnd.randrange(1, 18), 0, 12, 17])
    c.put(U + 0xC6, bytes([c6]))
    c.put(U + 0x10, le32(mode))
    row.update(uc6=c6, umode=mode, c4=(row["c4"] & 0xFF00FFFF) | (c6 << 16))


def is_dead_u(row):
    if row["uc6"] & 1:
        return 1
    if row["ut"] == 0:
        return int(row["umode"] in (0, 17))
    if row["ut"] == 1:
        return int(row["umode"] in (0, 12))
    return 1


def put_size_b(c, rnd, row):
    """UNIT_GetSizeX(U): type 0 -> 2; type 1 -> sub_00451FE0_MonStats2Rec(class) +0x08 (movsx), 0 without a row
    (MonStats +0x18 the MonStats2 row)."""
    if row["ut"] == 1 and rnd.random() < 0.6:
        row["ucls"] = rnd.randrange(NMON)
        c.put(U + 0x04, le32(row["ucls"]))
    m2i = [rnd.choice([rnd.randrange(NMON2)] * 6 + [NMON2, -1]) for _ in range(NMON)]
    sz = [rnd.choice([1, 2, 3, rnd.getrandbits(8)]) for _ in range(NMON2)]
    for i in range(NMON):
        c.put(MSREC + 0x1A8 * i + 0x18, le16(m2i[i]))
    for i in range(NMON2):
        c.put(MS2REC + 0x134 * i + 0x08, bytes([sz[i]]))
    row.update(sm2i=m2i, msz=sz)


def size_u(row, neg=None):
    if row["ut"] == 0 or neg == "size2":
        return 2
    if row["ut"] != 1:
        return 0
    cl = s32(row["ucls"])
    if not 0 <= cl < NMON:
        return 0
    i = s16(row["sm2i"][cl])
    if not 0 <= i < NMON2:
        return 0
    v = row["msz"][i]
    return v - 256 if v & 0x80 else v


def dist_b(ux, uy, x, y):
    """sub_006417F0_UnitDistance(unit, x, y): dx = |x - ux|, dy = |y - uy| (a negative result, INT_MIN, taken as 0);
    (max + 2·... ): dx > dy -> (dy + 2dx) / 2, else (dx + 2dy) / 2, truncating."""
    def ab(v):
        v = s32(v)
        if v < 0:
            v = s32(-v)
        return 0 if v < 0 else v
    dx, dy = ab(x - ux), ab(y - uy)
    if dx > dy:
        return trunc2(s32(dy + 2 * dx))
    return trunc2(s32(dx + 2 * dy))


# ------------------------------------------------------------------------------------------- the melee hits
HIT_ORDER_B = ("st32", "st39", "do2", "do9", "do70")
ST32_SLOT70 = (0x7FEFFFE4, 0x005D84F3)   # do 70's return address from start 32, at its stack slot


def put_queued_b(c, rnd, row):
    """put_queued (pal) plus each packet's +0x04 result word (node +0x18): bit 0 tested by do 2."""
    put_queued(c, rnd, row)
    for nd in row["q"]:
        r = rnd.getrandbits(32)
        c.put(nd["a"] + 0x18, le32(r))
        nd["res"] = r


@family("hit_bar", "bar")
def hit_bar(rnd, game):
    """Start 32 (Bash, Stun, Concentrate, Conversion, BearSmite), start 39 (Berserk), do 2 (the melee delivery), do 9
    (Frenzy), do 70 (Double Swing): up to 0x0056E520, MeleeHitTest, OverlaySet, STATLIST_Alloc, UnitQueueEvent,
    STATE_Set, DeliverQueued, NearestUnitInRange or the reach helpers' inventory calls."""
    cases, exp = [], []
    for k in range(1750):
        w = HIT_ORDER_B[k % 5]
        c = Case(FNB[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1))
        put_game_b(c, rnd, row, game)
        put_inv_a(c, rnd, row)
        put_target_a(c, rnd, row, game)
        row["tguid"] = u32f(c, T + 0x0C) if row["t"] else None
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x140, 0x1A0, 0x60))
        if w == "st39":
            put_tohit(c, rnd, row)
        if w in ("do9", "do70"):
            w38 = rnd.getrandbits(32)
            c.put(U + 0x38, le32(w38))
            row["w38"] = w38
        if w == "do70":
            put_reach(c, rnd, row)
        if w == "do2":
            put_queued_b(c, rnd, row)
            if sid_ok(row):
                b = srec(row)
                ovl = rnd.choice([0, 0, -1, rnd.randint(1, NOVL), NOVL, NOVL + 1, rnd.randint(-0x8000, 0x7FFF)])
                ats = rnd.choice([rnd.randrange(NSTATES)] * 3 + [-1, -1, NSTATES, 0])
                ast = rnd.choice([rnd.randrange(1, NSTATES)] * 3 + [-1, 0, 0, NSTATES])
                c.put(b + 0x4E, le16(ovl))
                c.put(b + 0x80, le16(ast) + le16(ats))
                row.update(ovl=ovl, ats=ats, ast=ast)
                row["tsl"] = put_state_lists(c, rnd, T, ats if ats > 0 else 1) if row["t"] else 0
                row["usl"] = put_state_lists(c, rnd, U, ast if ast > 0 else 1)
        finish_b(c, rnd, row, game, cases, exp)
    return cases, mem_bar(), {"cases": exp}


def st32_model(row, game, br, neg=None, frame=None):
    """Start 32: the record, the target, its room's town test, then 0x0056E520(ECX unit, EDX calc3)."""
    if not sid_ok(row):
        br["nosid"] += 1
        return None
    if not tgt_unit(row):
        br["notarget"] += 1
        return None
    if town_t(row) and neg != "town_any":
        br["town"] += 1
        return None
    br["attackrate"] += 1
    return obs_a(row, "AttackRate", {"ecx": U, "edx": ev_s(row, 0x140)}, [], 0x005D7F16, frame=frame)


def odd38(row, neg=None):
    """`mov eax, [esi+0x38]; sar eax, 8; and eax, 0x80000001; jns; dec; or -2; inc`: (+0x38 >> 8) % 2 != 0."""
    return (s32(row["w38"]) >> (0 if neg == "par_low" else 8)) & 1


def hit_bar_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    t = tgt_unit(row)
    if w == "st32":
        e = st32_model(row, game, br, neg)
        return e if e is not None else ret_b(row, 0)
    if w == "do9":
        if not t:
            br["notarget"] += 1
            return ret_b(row, 0)
        if odd38(row, neg):
            br["odd"] += 1
            return obs_a(row, "DeliverQueued", {"ecx": game, "edx": U}, [T, 0], 0x005D8E90, bit6=True)
        br["even"] += 1
        return obs_a(row, "DeliverQueued", {"ecx": game, "edx": U}, [T, 0], 0x005D8E3E, bit6=(neg == "bit6_9"))
    if w == "do70":
        if not t:
            br["notarget"] += 1
            return ret_b(row, 0)
        if odd38(row, neg):
            a = reach_a(row, None)
            if a[0] == "obs":
                br["reach_" + a[1]] += 1
                return sub_obs(row, a, bit6=True)
            br["near"] += 1
            return obs_a(row, "NearestUnit", {"ecx": game, "edx": U},
                         [0, 0, s32(a[1] + 4), 0x20003, row["tguid"], 0], 0x005D84D5, bit6=True)
        e = st32_model(row, game, br, neg, frame=abs_ret(*ST32_SLOT70))
        if e is not None:
            br["even_st32"] += 1
            return e
        br["even_deliver"] += 1
        return obs_a(row, "DeliverQueued", {"ecx": game, "edx": U}, [T, 0], 0x005D84FF)
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_b(row, 0)
    if w == "st39":
        if not t:
            br["notarget"] += 1
            return ret_b(row, 0)
        br["hittest"] += 1
        return obs_a(row, "MeleeHitTest", {"ecx": game, "edx": U}, [T, tohit_a(row), 0], 0x005D9867,
                     frame={fr(-0x7C): bytes(0x70)})
    # do 2
    ovl, ats, ast = s16(row["ovl"]), s16(row["ats"]), s16(row["ast"])
    if 0 < ovl and (ovl <= NOVL if neg != "ovl_lt" else ovl < NOVL):
        if not t:
            br["ovl_notarget"] += 1
            return ret_b(row, 0)
        q = qhf(row)
        if q is None:
            br["ovl_noqueued"] += 1
            return ret_b(row, 1)
        if q["res"] & 1:
            br["overlay"] += 1
            return obs_a(row, "OverlaySet", {}, [T, ovl, 0], 0x0056F273)
        br["ovl_miss"] += 1
    if 0 <= ats < NSTATES:
        if not t:
            br["ats_notarget"] += 1
            return ret_b(row, 0)
        q = qhf(row)
        if q is None:
            br["ats_noqueued"] += 1
            return ret_b(row, 1)
        if q["res"] & 1:
            v = ev_s(row, 0x60)
            if v < 1 and neg != "end_nomax":
                v = 1
            end = s32(row["frame"] + v)
            if not row["tsl"] or ats == 0:
                br["ats_alloc"] += 1
                return obs_a(row, "StatListAlloc", {}, [GAMEPOOL, 2, end, row["tt"], row["tguid"]], 0x0056F326)
            br["ats_event"] += 1
            return obs_a(row, "QueueEvent", {"ecx": game, "edx": T}, [0xC, end, 0, 0], 0x0056F344)
        br["ats_miss"] += 1
    if 0 < ast < NSTATES:
        if not row["usl"]:
            br["ast_alloc"] += 1
            return obs_a(row, "StatListAlloc", {}, [GAMEPOOL, 4, 0, row["ut"], row["ug"]], 0x0056F3DC)
        br["ast_set"] += 1
        return obs_a(row, "StateSet", {}, [U, ast, 1], 0x0056F414)
    if not t:
        br["notarget"] += 1
        return ret_b(row, 0, bit6=True)
    br["deliver"] += 1
    return obs_a(row, "DeliverQueued", {"ecx": game, "edx": U}, [T, 0], 0x0056F44F, bit6=True)


# ------------------------------------------------------------------------------------------- the corpse skills
CORPSE_ORDER_B = ("st33", "st34", "do69", "do72", "do75")


@family("corpse_bar", "bar")
def corpse_bar(rnd, game):
    """Start 33 (Find Potion, Grim Ward), start 34 (Find Item), do 69 (Find Potion), do 72 (Find Item), do 75 (Grim
    Ward): the corpse tests 0x00645590 / 0x006455E0, state 118, up to STATE_Set or the free-spot call 0x0064E7B0."""
    cases, exp = [], []
    for k in range(2500):
        w = CORPSE_ORDER_B[k % 5]
        c = Case(FNB[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1))
        put_target_a(c, rnd, row, game, types=(1, 1, 1, 1, 1, 1, 1, 0, 3, 4))
        put_corpse(c, rnd, row)
        if row["t"] and row["tt"] == 1 and rnd.random() < 0.5:
            force_corpse(c, rnd, row)
        m2f = row["m2f"]
        for i in range(NMON2):                     # flag 12 (0x00621F60) at random
            m2f[i] = (m2f[i] | 0x1000) if rnd.random() < 0.6 else (m2f[i] & ~0x1000)
            c.put(MS2REC + 0x134 * i + 0x04, le16(m2f[i]))
        if w == "do75" and row["t"] and row.get("troom") and rnd.random() < 0.75:
            put_in_room_t(c, rnd, row)
        if row.get("twords") is not None and rnd.random() < 0.3:
            row["twords"][3] |= 1 << (118 - 96)
            c.put(TSL + 0x200 + 12, le32(row["twords"][3]))
        finish_b(c, rnd, row, game, cases, exp)
    return cases, mem_bar(), {"cases": exp}


def force_corpse(c, rnd, row):
    """A monster target the corpse tests pass more often: a class with a MonStats2 row, mode 12, clear state words."""
    cls = rnd.randrange(NMON)
    c.put(T + 0x04, le32(cls))
    if not 0 <= s16(row["m2i"][cls]) < NMON2:
        row["m2i"][cls] = rnd.randrange(NMON2)
        c.put(MSREC + 0x1A8 * cls + 0x18, le16(row["m2i"][cls]))
    i2 = row["m2i"][cls]
    row["m2f"][i2] |= 0x80 if rnd.random() < 0.95 else 0
    c.put(MS2REC + 0x134 * i2 + 0x04, le16(row["m2f"][i2]))
    c.put(T + 0x10, le32(12))
    row.update(tcls=cls, tmode=12)
    if row["twords"] is not None:
        row["twords"] = [0] * NSW
        for i in range(NSW):
            c.put(TSL + 0x200 + 4 * i, le32(0))


def put_in_room_t(c, rnd, row):
    """The target's dynamic-path position inside its room (+0x1C), so that RoomAtSubtile finds it."""
    r = row["troom"]
    _, x0, y0, ww, hh = row["rooms"][str(r)][:5]
    if ww < 1 or hh < 1 or not u32f(c, T + 0x2C):
        return
    tx, ty = (x0 + rnd.randrange(ww)) & 0xFFFF, (y0 + rnd.randrange(hh)) & 0xFFFF
    c.put(TP + 0x02, le16(tx))
    c.put(TP + 0x06, le16(ty))
    row.update(tx=tx, ty=ty)


def put_leap_world(c, rnd, row):
    """Start 40 and 41: the caster inside a room (its path +0x1C and position) and the path target point inside a room
    or near the caster, at times with no target unit."""
    rooms = [r for r in ROOMS if row["rooms"][str(r)][3] >= 4 and row["rooms"][str(r)][4] >= 4]
    if not rooms or rnd.random() < 0.15:
        return
    r = rnd.choice(rooms)
    _, x0, y0, ww, hh = row["rooms"][str(r)][:5]
    ux, uy = (x0 + rnd.randrange(ww)) & 0xFFFF, (y0 + rnd.randrange(hh)) & 0xFFFF
    c.put(UP + 0x1C, le32(r))
    c.put(UP + 0x02, le16(ux))
    c.put(UP + 0x06, le16(uy))
    row.update(uroom=r, ux=ux, uy=uy)
    if rnd.random() < 0.6:
        c.put(UP + 0x58, le32(0))
        row.update(t=0, tlink=None)
    r2 = rnd.choice(rooms)
    _, a0, b0, w2, h2 = row["rooms"][str(r2)][:5]
    k = rnd.random()
    if k < 0.5:
        px, py = a0 + rnd.randrange(w2), b0 + rnd.randrange(h2)
    elif k < 0.85:
        px, py = ux + rnd.randint(-30, 30), uy + rnd.randint(-30, 30)
    else:
        px, py = ux, uy
    px, py = px & 0xFFFF, py & 0xFFFF
    c.put(UP + 0x10, le16(px) + le16(py))
    row.update(px=px, py=py)


def corpse5e0(row, neg=None):
    """0x006455E0(unit): a monster in mode 12, not in set 33, MonStats2 flag 7."""
    if not row["t"] or row["tt"] != 1 or row["tmode"] != 12:
        return 0
    if set33(row):
        return 0
    return ms2bit(row, row["tcls"], 7)


def corpse590(row, neg=None):
    """0x00645590(unit): 0x006455E0's tests, then 0x00621F60(unit): a monster with MonStats2 flag 12."""
    if not corpse5e0(row):
        return 0
    if neg == "no12":
        return 1
    return ms2bit(row, row["tcls"], 12)


def has118_t(row, neg=None):
    """UNIT_HasState(target, 118): types 0, 1, 3; the list's +0x10 bit 31; word 3 bit 22 of +0x58."""
    if neg == "no118" or row["twords"] is None or row["tt"] not in (0, 1, 3):
        return 0
    return (row["twords"][3] >> 22) & 1


def corpse_bar_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    t = tgt_unit(row)
    if w in ("do69", "do72", "do75") and not sid_ok(row):
        br["nosid"] += 1
        return ret_b(row, 0)
    if not t:
        br["notarget"] += 1
        return ret_b(row, 0)
    if w == "st34":
        v = corpse5e0(row, neg)
        br["c5e0_%d" % v] += 1
        return ret_b(row, v)
    if w == "do72":
        if not corpse5e0(row, neg) or has118_t(row, neg):
            br["refused"] += 1
            return ret_b(row, 0)
        br["stateset"] += 1
        return obs_a(row, "StateSet", {}, [T, 118, 1], 0x005D87ED)
    v = corpse590(row, neg)
    if w == "st33":
        if v and has118_t(row, neg):
            br["has118"] += 1
            return ret_b(row, 0)
        br["c590_%d" % v] += 1
        return ret_b(row, v)
    if not v:
        br["refused"] += 1
        return ret_b(row, 0)
    if w == "do69":
        if has118_t(row, neg):
            br["has118"] += 1
            return ret_b(row, 0)
        br["stateset"] += 1
        return obs_a(row, "StateSet", {}, [T, 118, 1], 0x005D8230)
    # do 75
    x, y = row["tx"], row["ty"]
    room = row["troom"]
    if not room:
        br["noroom"] += 1
        return ret_b(row, 0)
    r2 = room_at(row, room, x, y)
    if not r2:
        br["nosub"] += 1
        return ret_b(row, 0)
    pt = le32(x) + le32(y) if neg != "pt_swap" else le32(y) + le32(x)
    br["freenear"] += 1
    return obs_a(row, "FreeNear", {}, [r2, None, 2, 0x1000, 1], 0x005D8A43, ptrs={1: pt})


# ------------------------------------------------------------------------------------------- the warcries, Taunt
CRY_ORDER_B = ("do68", "do71")
NOVA68_SLOT = (0x7FEFFFD4, 0x005D844A)   # do 68's return address from NovaAtUnit
TAUNT_SLOT = (0x7FEFFF74, 0x005D85E2)    # do 71's return address from 0x005D8510
SEARCH_SLOT = (0x7FEFFF6C, 0x005D8606)   # do 71's return address from 0x0056BBC0


@family("cry_bar", "bar")
def cry_bar(rnd, game):
    """Do 68 (Shout, Battle Cry, Battle Orders, War Cry, Battle Command: SrvMissileByCharge, NovaAtUnit up to its first
    MissileCreate) and do 71 (Taunt: auratargetstate, the target's test 0x005D8510 up to 0x0056E2F0, or the search
    0x0056BBC0 up to SKILLS_ForUnitsInRange)."""
    cases, exp = [], []
    for k in range(800):
        w = CRY_ORDER_B[k % 2]
        c = Case(FNB[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1))
        put_target_a(c, rnd, row, game, types=(1, 1, 1, 0, 2, 3, 4))
        if w == "do68" and sid_ok(row):
            put_bycharge(c, rnd, row)
        if w == "do71" and sid_ok(row):
            ats = rnd.choice([rnd.randrange(NSTATES)] * 5 + [-1, NSTATES, rnd.randint(-0x8000, -2)])
            c.put(srec(row) + 0x82, le16(ats))
            row["ats"] = ats
        finish_b(c, rnd, row, game, cases, exp)
    return cases, mem_bar(), {"cases": exp}


def cry_bar_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    sid, lv = s16(row["sid"]), row["lvl"]
    if w == "do68":
        b6 = neg != "nobit68"
        if not sid_ok(row):
            br["nosid"] += 1
            return ret_b(row, 0, bit6=b6)
        m = bycharge(row)
        if not (0 <= m < NREC) or (neg == "m0refuse" and m == 0):
            br["nomiss"] += 1
            return ret_b(row, 0, bit6=b6)
        fl = 3 if neg != "vel1" else 7
        kw = dict(flags=fl, owner=U, cls=m, x=row["ux"], y=row["uy"], skill=sid, lvl=lv,
                  tx=S4.dword(NOVA_DIR[0]), ty=S4.dword(NOVA_DIR[1]))
        if neg == "vel1":
            kw["vel"] = 1
        br["nova_" + ("charged" if m != s16(row["ms"][1]) else "a")] += 1
        return obs_a(row, "MissileCreate", {"ecx": game}, [], 0x0056D4CC, bit6=True, stk={"edx": (0, blk9d(**kw))},
                     frame=abs_ret(*NOVA68_SLOT))
    # do 71
    if not sid_ok(row) or not 0 <= s16(row["ats"]) < NSTATES:
        br["nostate"] += 1
        return ret_b(row, 0)
    t = tgt_unit(row)
    if t and row["tt"] == 1:
        br["montest"] += 1
        return obs_a(row, "MonTest2F0", {"ecx": T, "edx": 0xC}, [], 0x005D8537, frame=abs_ret(*TAUNT_SLOT))
    x, y = (row["ux"], row["uy"]) if neg != "ctx_swap" else (row["uy"], row["ux"])
    ctx = le32(0) + le32(0x7FFFFFFF) + le32(x) + le32(y) + le32(0x005D8510)
    br["search_" + ("t%d" % row["tt"] if t else "none")] += 1
    return obs_a(row, "ForUnitsInRange", {"ecx": game, "edx": U},
                 [0, 0, 0x14, 0x8783, 0x0056BB20, None, 0, 0x006DAB88, 0x2B8], 0x0056BC65, ptrs={5: ctx},
                 frame=abs_ret(*SEARCH_SLOT))


# ------------------------------------------------------------------------------------------- whirlwind, leaps, throws
MOVE_ORDER_B = ("st38", "st40", "st41", "do74", "do76", "do77", "do78")
STSET_SLOT38 = 0x7FEFFFAC                # start 38's return address from 0x00571B70
LEAP_SLOT40 = (0x7FEFFFC8, 0x005D9EC9)   # start 40's return address from 0x005D9A10
LEAP_SLOT41 = (0x7FEFFFD0, 0x005DA583)   # start 41's return address from 0x00645CA0
WEAP_SLOT74 = (0x7FEFFFE8, 0x005D88F6)   # do 74's return address from UnitGetWeapon


@family("move_bar", "bar")
def move_bar(rnd, game):
    """Start 38 (Whirlwind), 40 (Leap), 41 (Leap Attack), do 74 (Double Throw), do 76 (Whirlwind), do 77 (Leap), do 78
    (Leap Attack): the unit's skill node, the target and points, up to STATE_Set, InMeleeRange, PathSetType, the
    free-spot and collision calls, MonSkillAttackDo, the inventory query, CancelEvents and the continuations."""
    cases, exp = [], []
    for k in range(1750):
        w = MOVE_ORDER_B[k % 7]
        c = Case(FNB[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1))
        put_game_b(c, rnd, row, game)
        put_inv_a(c, rnd, row)
        put_target_a(c, rnd, row, game)
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x64,))
        put_unit_skills(c, rnd, row)
        if w == "st38":
            put_stats(c, rnd, U, {})
            put_bits(c, rnd, row, [12])
            w50 = rnd.getrandbits(32)
            c.put(UP + 0x50, le32(w50))
        if w == "st40":
            put_used_node(c, rnd, row)
            if row["node"] is not None:
                c.put(UNODE + 0x24, le32(rnd.getrandbits(32)))
            if sid_ok(row):
                b05 = rnd.getrandbits(8)
                c.put(srec(row) + 0x05, bytes([b05]))
                row["b05"] = b05
        if w in ("st40", "st41"):
            put_leap_world(c, rnd, row)
            put_size_b(c, rnd, row)
            c.put(UP + 0x48, le32(rnd.getrandbits(32)))
            row["mask48"] = u32f(c, UP + 0x48)
            if w == "st41" and rnd.random() < 0.3:     # points near the caster (the zero distance)
                px, py = (row["ux"] + rnd.randint(-12, 12)) & 0xFFFF, (row["uy"] + rnd.randint(-12, 12)) & 0xFFFF
                if rnd.random() < 0.15:
                    px, py = row["ux"], row["uy"]
                c.put(UP + 0x10, le16(px) + le16(py))
                row.update(px=px, py=py)
        if w == "do76":
            put_dead_u(c, rnd, row)
        dumps = {"st38": [(UP + 0x50, 4)], "st40": [(UNODE + 0x24, 4), (OSK + 0x10, 4)],
                 "do78": [(a + 0x0C, 4) for a in SKN_B]}.get(w, [])
        finish_b(c, rnd, row, game, cases, exp, dumps=dumps)
    return cases, mem_bar(), {"cases": exp}


def leap_point(row, x, y, neg=None):
    """0x005D9A10 up to its free-spot call: range = aurarangecalc; d = max(UnitDistance(U, x, y), 1); when d > range,
    x = (x - ux)·range / d + ux and y likewise (32-bit, truncating)."""
    rg = ev_s(row, 0x64)
    d = dist_b(row["ux"], row["uy"], x, y)
    if d <= 1:
        d = 1
    if d > rg and neg != "noscale":
        x = s32(cdiv(s32(s32(x - row["ux"]) * rg), d) + row["ux"])
        y = s32(cdiv(s32(s32(y - row["uy"]) * rg), d) + row["uy"])
    return x, y


def move_bar_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    sid, lv = s16(row["sid"]), row["lvl"]
    t = tgt_unit(row)
    if w in ("st38", "st40", "do74", "do76", "do77") and not sid_ok(row):
        br["nosid"] += 1
        return ret_b(row, 0)
    if w == "st40":
        nd = row["node"]
        if nd is None:
            br["noused"] += 1
            return ret_b(row, 0)
        if row["ut"] == 1:
            if t:
                br["mon_attack"] += 1
                return obs_a(row, "MonSkillAtk", {}, [game], 0x005D9DFD)
            x, y, ok = target_xy(row)
            if not ok:
                br["mon_noxy"] += 1
                return ret_b(row, 0, mem={OSK + 0x10: le32(0)})
            br["mon_free"] += 1
            return obs_a(row, "FreeNear", {}, [row["uroom"], None, size_u(row, neg), 0x3C01, 0], 0x005D9E66,
                         ptrs={1: le32(x) + le32(y)}, mem={UNODE + 0x24: le32(0xFFFFFFFF)})
        x, y, ok = target_xy(row)
        if not ok:
            br["noxy"] += 1
            return ret_b(row, 0)
        r1 = room_at(row, row["uroom"], x, y)
        if not row["uroom"] or not r1:
            br["noroom"] += 1
            return ret_b(row, 0)
        if not row["b05"] & 1 and town_of(row, r1):
            br["town"] += 1
            return ret_b(row, 0)
        x, y = leap_point(row, x, y, neg)
        r2 = room_at(row, row["uroom"], x, y)
        br["leap_free"] += 1
        return obs_a(row, "FreeNear", {}, [r2, None, size_u(row, neg), 0x1C09, 1], 0x005D9BAE,
                     ptrs={1: le32(x) + le32(y)}, frame=abs_ret(*LEAP_SLOT40))
    nd = unit_skill(row, neg)
    if w == "st38":
        if nd is None:
            br["noskill"] += 1
            return obs_a(row, "StateSet", {}, [U, 0x12, 0], 0x00571B80, frame=abs_ret(STSET_SLOT38, 0x005D8F9B))
        x, y, ok = target_xy(row)
        if not ok:
            br["noxy"] += 1
            return obs_a(row, "StateSet", {}, [U, 0x12, 0], 0x00571B80, frame=abs_ret(STSET_SLOT38, 0x005D8F9B))
        if has_state(row, 12):
            br["state12"] += 1
            return ret_b(row, 0)
        if t:
            br["meleerange"] += 1
            return obs_a(row, "InMeleeRange", {}, [U, T, 0], 0x005D8FE2)
        m = 0x1C09 if (row["ut"] == 0) != (neg == "mask_swap") else 0x3C01
        br["settype"] += 1
        return obs_a(row, "PathSetType", {}, [UP, 7], 0x005D9060, mem={UP + 0x50: le32(0xC01)},
                     frame={fr(-0x14): le32(m)})
    if w == "st41":
        if nd is None:
            br["noskill"] += 1
            return ret_b(row, 0)
        if t:
            br["meleerange"] += 1
            return obs_a(row, "InMeleeRange", {}, [U, T, 0], 0x00645CBD, frame=abs_ret(*LEAP_SLOT41))
        px, py = row["px"], row["py"]
        d = dist_b(row["ux"], row["uy"], px, py)
        if d == 0:
            br["d0"] += 1
            return ret_b(row, 0)
        f = 2 if neg != "x1" else 1
        x = s32(cdiv(s32(f * s32(px - row["ux"])), d) + px)
        y = s32(cdiv(s32(f * s32(py - row["uy"])), d) + py)
        if not row["uroom"]:
            br["fatal"] += 1
            return obs_a(row, "Fatal", {}, [], 0x00645DEE, frame=abs_ret(*LEAP_SLOT41))
        br["colltest"] += 1
        return obs_a(row, "CollTest910", {}, [row["uroom"], x, y, row["mask48"], 0x1C09], 0x00645E1A,
                     frame=abs_ret(*LEAP_SLOT41))
    if w == "do74":
        if not row["inv"]:
            br["noinv"] += 1
            return ret_b(row, 0)
        br["invquery"] += 1
        return obs_a(row, "InvQuery", {}, [row["inv"], None, None, None], 0x00535BF9, frame=abs_ret(*WEAP_SLOT74))
    if nd is None:
        br["noskill"] += 1
        return ret_b(row, 0)
    if w == "do77":
        br["cancel"] += 1
        return obs_a(row, "CancelEvents", {"ecx": game, "edx": U}, [1, 0], 0x005DA3D0)
    f0c = nd["f0c"]
    if w == "do76":
        if nd["n18"] == 0 or nd["n1c"] == 0:
            br["ww_nopt"] += 1
            return obs_a(row, "Ww9460", {"ecx": game, "edx": U}, [nd["a"], row["sid"], nd["n18"], nd["n1c"]],
                         0x005D97D6)
        if f0c & 3 == 3:
            br["ww_done"] += 1
            return obs_a(row, "Ww9460", {"ecx": game, "edx": U}, [nd["a"], row["sid"], nd["n18"], nd["n1c"]],
                         0x005D9621)
        if not f0c & 1:
            br["ww_bit0"] += 1
            return ret_b(row, 0)
        if is_dead_u(row):
            br["ww_dead"] += 1
            return ret_b(row, 0)
        if row["ut"] == 0:
            br["ww_player"] += 1
            return obs_a(row, "Mode553DC0", {"ecx": game, "edx": U}, [3], 0x005D9659)
        br["ww_mon"] += 1
        return obs_a(row, "Mode6212C0", {}, [U, 0], 0x005D9663)
    # do 78
    order = ((0x100, "a"), (0x80, "b"), (0x200, "c")) if neg != "f200" else ((0x200, "c"), (0x100, "a"), (0x80, "b"))
    for bit, k in order:
        if f0c & bit:
            if k == "a":
                br["la_100"] += 1
                return obs_a(row, "Leap5DA120", {"eax": U}, [game, nd["a"]], 0x005DA810)
            if k == "b":
                br["la_80"] += 1
                return obs_a(row, "Leap5D9F70", {"edi": U}, [nd["a"]], 0x005DA86D)
            br["la_200"] += 1
            return obs_a(row, "Leap5DA660", {"eax": U}, [game, row["sid"], lv], 0x005DA890)
    br["la_set"] += 1
    return ret_b(row, 1, mem={nd["a"] + 0x0C: le32(0x1000)})


CHECKS.update({
    "hit_bar": check9b("hit_bar", hit_bar_model, ["town_any", "par_low", "ovl_lt", "end_nomax", "bit6_9"], RS_BAR,
                       md_masked=False),
    "corpse_bar": check9b("corpse_bar", corpse_bar_model, ["no118", "no12", "pt_swap"], RS_BAR, md_masked=False),
    "cry_bar": check9b("cry_bar", cry_bar_model, ["nobit68", "m0refuse", "vel1", "ctx_swap"], RS_BAR,
                       md_masked=False),
    "move_bar": check9b("move_bar", move_bar_model, ["sk34", "size2", "noscale", "mask_swap", "x1", "f200"], RS_BAR,
                        md_masked=False),
})

PINS_BAR = [  # (address, mnemonic, operand substring): instructions the bar claims turn on (ADR-0015 (5))
    (0x005D7F08, "call", "0x646ca0"), (0x005D7F11, "call", "0x56e520"),                              # start 32
    (0x005D80E2, "call", "0x639df0"), (0x005D80F2, "mov", "eax,edi"),                                 # start 33
    (0x005D8774, "neg", "eax"),                                                                       # start 34
    (0x006455A0, "cmp", "DWORD PTR [esi+0x10],0xc"), (0x00621F78, "mov", "edx,0xc"),                  # corpse tests
    (0x005D8E21, "sar", "eax,0x8"), (0x005D8E24, "and", "eax,0x80000001"),                            # do 9
    (0x005D8493, "sar", "eax,0x8"), (0x005D84C2, "push", "0x20003"),                                  # do 70
    (0x0056F235, "jle", ""), (0x0056F240, "jg", ""), (0x0056F27D, "jl", ""), (0x0056F2E7, "jl", ""),  # do 2
    (0x0056F395, "jle", ""), (0x0056F42A, "or", "DWORD PTR [edi+0xc4],0x40"),
    (0x005D83EF, "or", "DWORD PTR [esi+0xc4],0x40"), (0x005D8426, "jl", ""), (0x005D843D, "push", "0x0"),  # do 68
    (0x005D85BA, "jl", ""), (0x0056BC4F, "push", "0x8783"), (0x0056BBD8, "mov", "DWORD PTR [ebp-0x10],0x7fffffff"),
    (0x005D903D, "and", "eax,0xffffe008"), (0x005D9042, "push", "0xc01"), (0x005D9058, "push", "0x7"),  # start 38
    (0x0064382D, "cmp", "edi,esi"), (0x0064383B, "cmp", "DWORD PTR [ecx+0x34],edx"),                  # GetUnitSkill
    (0x00643848, "cmp", "edi,DWORD PTR [eax+0x28]"),
    (0x005D9D35, "jne", ""), (0x005D9AD8, "cmp", "ecx,0x1"), (0x005D9AE4, "jle", ""),                  # leap
    (0x005D9AF5, "idiv", "ecx"), (0x005D9B96, "push", "0x1c09"),
    (0x0064186E, "cmp", "edi,eax"), (0x00641879, "sar", "eax,1"),                                     # UnitDistance
    (0x00645DBF, "add", "eax,eax"), (0x00645DC2, "idiv", "ecx"), (0x00645E09, "push", "0x1c09"),      # st 41
    (0x005D9606, "cmp", "cl,0x3"), (0x005D964E, "push", "0x3"),                                       # do 76
    (0x005DA800, "test", "eax,0x100"), (0x005DA866, "jns", ""), (0x005DA879, "test", "eax,0x200"),     # do 78
    (0x005DA897, "push", "0x1000"),
]


def cmd_static_bar(a):
    rep = Report("static")
    rep.batch = "BAR"
    A = S4.asm()
    for va, mn, sub in PINS_BAR:
        ins = A.at(va)
        rep.c["pins"] += 1
        if ins is None or ins[0] != mn or sub not in ins[1]:
            rep.bad("pin 0x%08X: %r, want %s %s" % (va, ins, mn, sub))
        else:
            rep.c["pins_ok"] += 1
    for lo, n, name in ((BITMASK, 128, "g_BitMask32"), (0x006E10E0, 20, "hash offsets"),
                        (0x006C1164, 88, "CALC_Eval jump table"), (0x006426C0, 8 + 0x6D, "town tables"),
                        (0x0062057C, 24, "UNIT_GetSizeX jump table"), (NOVA_DIR[0], 512, "NovaAtUnit offsets")):
        sec = S4.section_of(lo)
        flags = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.c["ro_reads"] += 1
        if flags & 0x80000000:
            rep.bad("%s 0x%08X in writable %s" % (name, lo, sec))
        rep.notes.append("%s 0x%08X: %s" % (name, lo, sec))
    st, im, rd = ref_scan(A, SK_NFUNCS)
    rep.c["data_stores"] += len(st)
    rep.c["data_imms"] += len(im)
    rep.notes.append("skills calc function count 0x%08X: %d stores (PTR or moffs), %d immediates, %d reads in .text"
                     % (SK_NFUNCS, len(st), len(im), len(rd)))
    for hlp in (0x56E510, 0x622870, 0x571B70, 0x5D9A10, 0x5D9CE0, 0x645CA0, 0x535BC0, 0x56D400, 0x5D8510, 0x56BBC0,
                0x5D7EA0):
        sites = sorted(va for va, (mn, ops) in A.ins.items() if mn == "call" and ops.strip() == "0x%x" % hlp)
        rep.notes.append("calls of 0x%08X: %d in the image: %s" % (hlp, len(sites), " ".join("0x%08X" % s for s in sites)))
        rep.c["helper_sites"] += len(sites)
    imm = sorted(va for va, (mn, ops) in A.ins.items() if "0x5d8510" in ops)
    rep.notes.append("operands naming 0x005D8510: %s" % " ".join("0x%08X %s" % (v, A.ins[v][0]) for v in imm))
    for name, va in sorted(FNB.items(), key=lambda kv: kv[1]):
        tab = START_TABLE if name.startswith("st") else DO_TABLE
        num = int(name[2:])
        rep.c["table_entries"] += 1
        if S4.dword(tab + 4 * num) != va:
            rep.bad("%s: table entry 0x%08X, model address 0x%08X" % (name, S4.dword(tab + 4 * num), va))
    rep.notes.append("start table 32-34, 38-41: %s" % " ".join(
        "%d:0x%08X" % (i, S4.dword(START_TABLE + 4 * i)) for i in (32, 33, 34, 38, 39, 40, 41)))
    rep.notes.append("do table 2, 9, 68-72, 74-78: %s" % " ".join(
        "%d:0x%08X" % (i, S4.dword(DO_TABLE + 4 * i)) for i in (2, 9, 68, 69, 70, 71, 72, 74, 75, 76, 77, 78)))
    print("CATBAR static " + " ".join("%s=%d" % (k, rep.c[k]) for k in sorted(rep.c)))
    for n in rep.notes:
        print("  " + n)
    return 1 if rep.c["bad"] else 0


# ##################################################################################################################
# Batch dru (plan 0046 Phase 1): the druid start functions 56-58 and do functions 114-124, and the do-table entries
# 145 and 146 that the States rows 144 hurricane and 145 armageddon name as srvactivefunc (StateDoFunc, unit event 5).
# Emulated (new): 0x00643CE0 (a node's record id), sub_0056E620_SkillSummonClass with sub_0063EA70_SkillSummonRec,
# UNIT_GetUsedSkill, sub_006444A0_UnitSkillGet18, sub_00644560_UnitSkillSet18, 0x004EFC80 (Param4), 0x0056E680 (the
# hit test or the ResultFlags shortcut), 0x005C7040 up to its first MissileCreate, 0x005C8980 (Rabies' summed to-hit)
# with STATLIST_GetBaseStat and SKILLS_GetRecord, COLL_WHTest (0x0064D800, a boundary in sor) with COLL_CellTestNb and
# DUNGEON_GetCollMap; and the earlier batches' helpers. Observed (new): COMBAT_BuildDamage (0x0057B7D0),
# sub_006260B0_StatListSetEnd, UNIT_UnlinkStatList, COLL_RectTest (0x0064CEB0).
# ##################################################################################################################
FND = {
    "st56": 0x005C7690, "st57": 0x005C79E0, "st58": 0x005C7E00,
    "do114": 0x005C6910, "do115": 0x005C6A80, "do116": 0x005C6EC0, "do117": 0x005C7160, "do118": 0x005C72F0,
    "do119": 0x005C7390, "do120": 0x005C77C0, "do121": 0x005C8AD0, "do122": 0x005C7F10, "do123": 0x005C8080,
    "do124": 0x005C8190, "do145": 0x005C8380, "do146": 0x005C8520,
}
BOUNDS_D = {a: n for a, n in BOUNDS_B.items() if a != 0x0064D800}    # COLL_WHTest runs emulated here
BOUNDS_D.update({0x0057B7D0: "CombatBuildDmg", 0x006260B0: "StatListSetEnd", 0x006277E0: "UnlinkStatList",
                 0x0064CEB0: "RectTest"})
BOUND_BY_NAME.update({v: k for k, v in BOUNDS_D.items()})
ALLBOUND.update(BOUNDS_D)
SHAPE_D = 0x12660000                 # DataTables+0x17C: the u16 state list 0x005C8980 walks (count s16 at +0x180)
STREC_D = 0x12670000                 # DataTables+0xBC: the States records (0x3C; only the address is formed)
CMAP_D = 0x12680000                  # a room's +0x20 collision map (0x4000 per room; words at +0x100)
USKR_D = OSK + 0x700                 # the used node's record (+0x00 s16 id, 0x00643CE0)
ARG1 = 0x7FF00004                    # the first stack argument's slot ([ebp+0x8])
RS_DRU = [RS_HASH, RS_SKN, RS_CALC_JT, RS_BITMASK9C, RS_TOWN]


def mem_dru():
    lines = ["dword %08x %08x" % (G_PDATATABLES, DT),
             "dword %08x %08x" % (DT + 0xB64, MREC), "dword %08x %08x" % (DT + 0xB6C, NREC),
             "dword %08x 6b3a11f5" % COOKIE,
             "dword %08x %08x" % (DT + 0xB98, SREC), "dword %08x %08x" % (DT + 0xBA0, NSREC),
             "dword %08x %08x" % (DT + 0x40, SPOOL),
             "dword %08x %08x" % (DT + 0xBCC, ISC), "dword %08x %08x" % (DT + 0xBD4, NISC),
             "dword %08x %08x" % (DT + 0xA78, MSREC), "dword %08x %08x" % (DT + 0xA80, NMON),
             "dword %08x %08x" % (DT + 0xA90, MS2REC), "dword %08x %08x" % (DT + 0xA98, NMON2),
             "dword %08x %08x" % (DT + 0xC4, NSTATES), "dword %08x %08x" % (DT + 0xBF0, NPET),
             "dword %08x %08x" % (DT + 0xBC, STREC_D)]
    lines += ["observe %08x" % a for a in sorted(BOUNDS_D)]
    lines += ["guard %08x" % a for a in FATAL + ALLOC if a not in BOUNDS_D]
    return lines


def finish_d(c, rnd, row, game, cases, exp, dumps=()):
    finish_s(c, rnd, row, game, cases, exp, [row["sid"], row["lvl"]], dumps=dumps)


def put_used_d(c, rnd, row, p=0.9):
    """put_used_node plus the node's +0x00 record, whose s16 +0x00 0x00643CE0 returns (the id the functions test)."""
    put_used_node(c, rnd, row, p)
    if row["node"] is not None:
        sid = s16(row["sid"])
        rid = sid if rnd.random() < 0.85 else rnd.choice([sid + 1, rnd.randrange(NSREC), -1, 0x7FFF])
        c.put(UNODE + 0x00, le32(USKR_D))
        c.put(USKR_D, le16(rid))
        row["node"]["rid"] = rid


def node_id_ok(row):
    """UNIT_GetUsedSkill(U) non-null and 0x00643CE0(node) (movsx of the record's +0x00) equal to the id."""
    nd = row["node"]
    return nd is not None and s16(nd["rid"]) == s32(row["sid"])


def put_ustate_d(c, rnd, row, st):
    """U's stat list: put_state_lists for UNIT_FindStatListByState(U, st) and, for st in range, the +0x58 state word
    with st's bit set or cleared (UNIT_HasState). row: usl (the list found, 0 for none), usl_st, hs."""
    s = st if 0 < st < NSTATES else 1
    row["usl"] = put_state_lists(c, rnd, U, s)
    row["usl_st"] = s
    row["hs"] = 0
    if not 0 <= st < NSTATES or (U + 0x5C) not in c.fields or not u32f(c, U + 0x5C):
        return
    if not u32f(c, USL + 0x10) & 0x80000000:
        return
    add_state_words(c, rnd, U, [st])
    wa = USL + 0x200 + 4 * (st >> 5)
    v = u32f(c, wa)
    on = rnd.random() < 0.65
    v = (v | (1 << (st & 31))) if on else (v & ~(1 << (st & 31)))
    c.put(wa, le32(v))
    row["hs"] = int(on)


def find_list_d(row, st):
    """UNIT_FindStatListByState(U, st): 0 for st 0 (`test edx, edx; je`), else the list put_state_lists made."""
    if st == 0 or row["usl_st"] != st:
        return 0
    return row["usl"]


def has_state_d(row):
    return row["hs"] if row["ut"] in (0, 1, 3) else 0


# ------------------------------------------------------------------------------------------- the summons
SUMMON_ORDER_D = ("do114", "do115", "do119")


@family("summon_dru", "dru")
def summon_dru(rnd, game):
    """Do 114 (Raven), do 115 (Plague Poppy, Cycle of Life, Vines), do 119 (the spirits, Oak Sage, Heart of Wolverine,
    Spirit of Barbs, Summon Spirit Wolf, Fenris, Grizzly): SkillSummonClass, the pet type, up to SpawnOwnedMonster."""
    cases, exp = [], []
    for k in range(1500):
        w = SUMMON_ORDER_D[k % 3]
        c = Case(FND[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1))
        put_target_a(c, rnd, row, game)
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0xC0, 0x13C))
        if sid_ok(row):
            b = srec(row)
            summ = rnd.randrange(NMON)
            mode = rnd.choice([rnd.randrange(16), rnd.randrange(16), -1, 16, rnd.randint(17, 127), -0x80])
            pet = rnd.choice([rnd.randrange(NPET)] * 7 + [0xFF, 0x80, NPET, rnd.randint(NPET, 0x7F)])
            c.put(b + 0xBC, le16(summ))
            c.put(b + 0xBE, bytes([pet & 0xFF, mode & 0xFF]))
            row.update(summ=summ, mode=mode, pet=pet)
        finish_d(c, rnd, row, game, cases, exp)
    return cases, mem_dru(), {"cases": exp}


def summon_dru_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_s(row, 0)
    pet = row["pet"]
    if pet >= 0x80 or pet >= NPET:          # movsx < 0, then >= the PetType count: refused
        if neg != "pet_zero":
            br["pet_refused"] += 1
            return ret_s(row, 0)
        pet = 0
    mode = row["mode"] if 0 <= row["mode"] < 16 else 1
    pm = ev_s(row, 0xC0)
    if w == "do119":
        x, y, ok = target_xy(row)
        if not ok:
            br["noxy"] += 1
            return ret_s(row, 0, bit6=True)
        pos = (0, 0) if neg != "xy_pos" else (x, y)
        w24 = x if neg != "w24_zero" else 0
        blk = b"".join(le32(v) for v in (0, U, row["summ"], 0, mode, pos[0], pos[1], pet, pm, w24))
        br["spawn"] += 1
        return obs_a(row, "SpawnOwned", {"ecx": game}, [], 0x005C74A0, bit6=True, stk={"edx": (0, blk)},
                     frame={fr(-0x14): le32(y)})
    m10 = mode if w == "do114" or neg == "mode10" else 8
    w24 = mode if neg != "w24_zero" else 0
    blk = b"".join(le32(v) for v in (0, U, row["summ"], 0, m10, 0, 0, pet, pm, w24))
    br["spawn"] += 1
    return obs_a(row, "SpawnOwned", {"ecx": game}, [], 0x005C6A00 if w == "do114" else 0x005C6B71, bit6=True,
                 stk={"edx": (0, blk)})


# ------------------------------------------------------------------------------------------- shapes and timed states
SHAPE_ORDER_D = ("do116", "do120", "do124", "do145", "do146")


@family("shape_dru", "dru")
def shape_dru(rnd, game):
    """Do 116 (Werewolf, Werebear, Delerium Change: up to STATE_GroupClear), do 120 (Feral Rage, Maul), do 124
    (Armageddon, Hurricane, Diablogeddon: the draw, the timed list), do 145 and do 146 (the hurricane and armageddon
    states' srvactivefunc: the state, the town test, up to UNIT_CancelEvents or the state's removal)."""
    cases, exp = [], []
    for k in range(2500):
        w = SHAPE_ORDER_D[k % 5]
        c = Case(FND[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        if w in ("do145", "do146") and rnd.random() < 0.6:
            row["lvl"] = rnd.randint(1, 30)
        put_caster(c, rnd, row, types=(0, 0, 1))
        put_game_b(c, rnd, row, game)
        put_target_a(c, rnd, row, game)
        if w in ("do145", "do146") and row["uroom"] and rnd.random() < 0.35:     # the caster's room in town
            lev = 0x13200000 + 0x1000 * ROOMS.index(row["uroom"])
            c.put(lev + 0x1D0, le32(1))
            row["rooms"][str(row["uroom"])][0] = 1
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x60, 0x64))
        ast = 1
        if sid_ok(row):
            b = srec(row)
            if w == "do146":
                put_bycharge(c, rnd, row)
                row["f04"] &= ~4                      # the plain srvmissilea path (no state list of its own)
                c.put(b + 0x04, bytes([row["f04"]]))
            ast = rnd.choice([rnd.randrange(1, NSTATES)] * (6 if w not in ("do145", "do146") else 20) +
                             [0, -1, NSTATES, rnd.randint(-0x8000, -2)])
            c.put(b + 0x80, le16(ast))
            b05 = rnd.getrandbits(8)
            if rnd.random() < 0.6:
                b05 &= ~1
            c.put(b + 0x05, bytes([b05]))
            p4 = rnd.choice([rnd.randint(0, 40), rnd.getrandbits(32)])
            c.put(b + 0x154, le32(p4))
            row.update(ast=ast, b05=b05, p4=p4)
            if w == "do146":
                row["cst"] = ast
        put_ustate_d(c, rnd, row, ast)
        if w in ("do120", "do124"):
            put_used_d(c, rnd, row)
        if w == "do146":
            put_unit_skills(c, rnd, row)
        dumps = [(UNODE + 0x18, 4)] if w in ("do120", "do124") else []
        if w == "do145":
            dumps.append((ARG1, 4))
        finish_d(c, rnd, row, game, cases, exp, dumps=dumps)
    return cases, mem_dru(), {"cases": exp}


def shape_dru_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    sid, lv = s16(row["sid"]), row["lvl"]
    gu = {"ecx": game, "edx": U}
    if w in ("do145", "do146"):
        early = 0x005C8443 if w == "do145" else 0x005C85E3
        cancel = (row, "CancelEvents", gu, [5, row["sid"]])
        if not sid_ok(row) or s32(lv) <= 0 or not 0 <= s16(row["ast"]) < NSTATES:
            br["refused"] += 1
            return obs_a(*cancel, early)
        ast = s16(row["ast"])
        if not has_state_d(row):
            br["nostate"] += 1
            return obs_a(*cancel, early)
        if not row["b05"] & 1 and (neg != "notown") and row["uroom"] and town_of(row, row["uroom"]):
            l = find_list_d(row, ast)
            if l:
                br["town_unlink"] += 1
                return obs_a(row, "UnlinkStatList", {}, [U, l], 0x005C841D if w == "do145" else 0x005C85BD)
            br["town_clear"] += 1
            return obs_a(row, "StateSet", {}, [U, ast, 0], 0x005C8436 if w == "do145" else 0x005C85D6)
        if w == "do146":
            if bycharge(row) <= 0:
                br["nomiss"] += 1
                return obs_a(*cancel, early)
            if unit_skill(row) is None:
                br["noskill"] += 1
                return obs_a(*cancel, early)
        if ev_s(row, 0x64) <= 0:
            br["norange"] += 1
            return obs_a(*cancel, early)
        br["rearm"] += 1
        if w == "do145":
            p4 = row["p4"] if neg == "p4_noframe" else row["p4"] + row["frame"]
            return obs_a(*cancel, 0x005C8481, mem={ARG1: le32(p4)})
        return obs_a(*cancel, 0x005C8647)
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_s(row, 0)
    ast = s16(row["ast"])
    lo = 0 if neg != "ast_le" else 1
    if not lo <= ast < NSTATES:
        br["nostate"] += 1
        return ret_s(row, 0)
    if w == "do116":
        br["groupclear"] += 1
        return obs_a(row, "GroupClear", {"ecx": U, "edx": ast}, [1], 0x005C6F25, bit6=True)
    if row["node"] is None:
        br["noused"] += 1
        return ret_s(row, 0)
    if not node_id_ok(row):
        br["otherid"] += 1
        return ret_s(row, 0)
    useed = None
    fr_ = {}
    if w == "do120":
        if tgt_unit(row):
            br["deliver"] += 1
            return obs_a(row, "DeliverQueued", gu, [T, 0], 0x005C786A, bit6=True)
        if row["node"]["n18"] == 0:
            br["n18_0"] += 1
            return ret_s(row, 1, bit6=True)
        ln = ev_s(row, 0x60)
        if neg == "noclamp":
            ln = max(ln, 1)
        sites = (0x005C78D1, 0x005C7917)
    else:
        s0 = row["seeds"][0]
        r, lo_, hi_ = rrange(s0[0], s0[1], 0x10000)
        if neg != "seed_none":
            useed = (lo_, hi_)
        fr_ = {fr(-0xC): le32(r)}
        ln = ev_s(row, 0x60)
        if ln < 1 and neg != "noclamp":
            ln = 1
        sites = (0x005C8295, 0x005C82E1)
    end = s32(row["frame"] + ln)
    l = find_list_d(row, ast)
    e = None
    if l:
        br["setend"] += 1
        e = obs_s(row, "StatListSetEnd", {}, [l, end], sites[1], bit6=True, useed=useed)
    else:
        br["alloc"] += 1
        e = obs_s(row, "StatListAlloc", {}, [GAMEPOOL, 2, end, row["ut"], row["ug"]], sites[0], bit6=True,
                  useed=useed)
    return e + (fr_,)


# ------------------------------------------------------------------------------------------- the melee functions
MELEE_ORDER_D = ("st56", "st57", "st58", "do121", "do122", "do121")
HIT680_SLOT = {"st58": (0x7FEFFF60, 0x005C7E7A), "do122": (0x7FEFFF5C, 0x005C7F90)}   # 0x0056E680's return slots
RAB_SLOT = (0x7FEFFFE0, 0x005C8B5F)  # do 121's return address from 0x005C8980
RAB_EBP = 0x7FEFFFDC                 # 0x005C8980's EBP


def put_shape_d(c, rnd, row):
    """0x005C8980's inputs: the state list at DataTables+0x17C (count s16 +0x180); U's stat list with the +0x58 state
    words (UNIT_HasState) and the +0x3C/+0x40 chains (UNIT_FindStatListByState), each found list holding stat 350
    (STATLIST_GetBaseStat, base array +0x24/+0x28); the skills' ToHit, LevToHit, ToHitCalc -1 and SrcDam."""
    n = rnd.choice([0, 1, 2, 2, 3, 3, 3])
    pool = list(range(1, NSTATES))
    sts = rnd.sample(pool, n)
    for i in range(n):
        if rnd.random() < 0.1:
            sts[i] = rnd.choice([-1, NSTATES, rnd.randint(-0x8000, -2)])
    cnt = n if rnd.random() < 0.95 else rnd.choice([0, -1, -0x8000])
    c.put(DT + 0x17C, le32(SHAPE_D))
    c.put(DT + 0x180, le16(cnt))
    row["shape_cnt"] = cnt
    for i, s in enumerate(sts):
        c.put(SHAPE_D + 2 * i, le16(s))
    row["shape"] = []
    if rnd.random() < 0.04:
        c.put(U + 0x5C, le32(0))
        row["shape_list"] = 0
    else:
        c.put(U + 0x5C, le32(USL))
        fl = rnd.getrandbits(32) | 0x80000000
        if rnd.random() < 0.05:
            fl &= 0x7FFFFFFF
        c.put(USL + 0x10, le32(fl))
        row["shape_list"] = fl >> 31
        words = USL + 0x200
        c.put(USL + 0x58, le32(words))
        wv = {}
        nodes = [USL + 0x400 + 0x80 * i for i in range(8)]
        chains = {0x3C: [], 0x40: []}
        for s in sts:
            on = rnd.random() < 0.8
            ent = {"s": s, "has": 0, "list": 0, "sk": None}
            if 0 <= s < NSTATES:
                wi = s >> 5
                if wi not in wv:
                    wv[wi] = rnd.getrandbits(32)
                wv[wi] = (wv[wi] | (1 << (s & 31))) if on else (wv[wi] & ~(1 << (s & 31)))
                if rnd.random() < 0.85:
                    chains[rnd.choice((0x3C, 0x40))].append(ent)
            row["shape"].append(ent)
        for wi, v in wv.items():
            c.put(words + 4 * wi, le32(v))
        for e in row["shape"]:
            s = e["s"]
            if 0 <= s < NSTATES:
                e["has"] = int(bool(fl >> 31) and (wv[s >> 5] >> (s & 31)) & 1)
        pos = 0
        for head in (0x3C, 0x40):
            ch = chains[head]
            if rnd.random() < 0.3:                    # a decoy node of another state first
                ch = [{"s": None}] + ch
            c.put(USL + head, le32(nodes[pos] if ch else 0))
            for i, e in enumerate(ch):
                nd = nodes[pos]
                pos += 1
                nxt = nodes[pos] if i + 1 < len(ch) else 0
                if e["s"] is None:
                    c.put(nd + 0x14, le32(rnd.choice([0, NSTATES + 5, 999])))
                    c.put(nd + 0x2C, le32(nxt))
                    continue
                c.put(nd + 0x14, le32(e["s"]))
                c.put(nd + 0x2C, le32(nxt))
                sk = rnd.choice([rnd.randrange(NSREC)] * 6 + [-1, NSREC, rnd.getrandbits(32)])
                keys = {350 << 16: sk}
                if rnd.random() < 0.3:
                    keys[351 << 16] = rnd.getrandbits(32)
                if rnd.random() < 0.08:
                    keys = {351 << 16: rnd.getrandbits(32)}
                    sk = 0
                arr = nd + 0x40
                c.put(nd + 0x10, le32(0))
                c.put(nd + 0x24, le32(arr))
                c.put(nd + 0x28, le16(len(keys)))
                for j, kk in enumerate(sorted(keys)):
                    c.put(arr + 8 * j, le32(kk) + le32(keys[kk]))
                e["list"] = nd
                e["sk"] = sk & M32
        c.put(ISC + 0x144 * 350 + 5, b"\x00")
    recs = []
    for i in range(NSREC):
        b = SREC + 0x23C * i
        base, lev = rnd.choice([rnd.randint(0, 300), rnd.getrandbits(32)]), rnd.choice([rnd.randint(0, 35),
                                                                                        rnd.getrandbits(32)])
        sd = rnd.choice([0, 128, rnd.getrandbits(8), rnd.getrandbits(8)])
        c.put(b + 0x198, le32(base) + le32(lev) + le32(0xFFFFFFFF))
        c.put(b + 0x1A5, bytes([sd]))
        recs.append([base, lev, sd])
    row["trec"] = recs


def rabies_hit_d(row, neg=None):
    """0x005C8980 up to its MeleeHitTest: the sum of SKILLS_GetToHit(U, skill, lvl) over the listed states U has, whose
    list's stat 350 names a skill in range, and the last such skill's non-zero SrcDam (0x80 by default)."""
    tot, sd = 0, 0x80
    lv = s32(row["lvl"])
    for e in row["shape"][:max(row["shape_cnt"], 0)]:
        s = e["s"]
        if not 0 <= s < NSTATES or not e["has"]:
            continue
        if not e["list"]:
            continue
        sk = s32(e["sk"])
        if not 0 <= sk < NSREC:
            continue
        base, lev, d = row["trec"][sk]
        th = 0 if lv <= 0 else s32((lv - 1) * lev + base)
        tot = s32(tot + th)
        if d and neg not in ("sd_first", "sd_none"):
            sd = d
        elif d and neg == "sd_first" and sd == 0x80:
            sd = d
    return tot, sd


@family("melee_dru", "dru")
def melee_dru(rnd, game):
    """Start 56 (Feral Rage, Maul), start 57 (Rabies), start 58 (Fire Claws), do 121 (Rabies: 0x005C8980's summed
    to-hit), do 122 (Hunger): the used skill and its id, the target, the shape state, up to MeleeHitTest (inside
    0x0056E680 or 0x005C8980) or COMBAT_BuildDamage (the ResultFlags shortcut)."""
    cases, exp = [], []
    for k in range(2400):
        w = MELEE_ORDER_D[k % 6]
        c = Case(FND[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1))
        put_target_a(c, rnd, row, game)
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x138, 0x1A0))
        if w in ("st56", "st57", "st58", "do122"):
            put_tohit(c, rnd, row)
        if w in ("st56", "st57", "do121"):
            put_used_d(c, rnd, row)
        ast = 1
        if sid_ok(row):
            b = srec(row)
            if w == "st57":
                ast = rnd.choice([rnd.randrange(1, NSTATES)] * 6 + [0, -1, NSTATES, rnd.randint(-0x8000, -2)])
                c.put(b + 0x80, le16(ast))
                row["ast"] = ast
            if w in ("st58", "do122"):
                rf = rnd.choice([0, 0, 1, rnd.getrandbits(16), rnd.getrandbits(16) | 1, rnd.getrandbits(16) & ~1])
                hf = rnd.choice([0, 2, rnd.getrandbits(32)])
                hc = rnd.choice([0, 0, rnd.randint(1, 160), rnd.getrandbits(32)])
                sd = rnd.choice([0, 128, rnd.getrandbits(8)])
                c.put(b + 0x12E, le16(rf) + le32(hf) + le32(hc))
                c.put(b + 0x1A5, bytes([sd]))
                row.update(rf=rf, hf=hf, hc=hc, sd=sd)
        if w == "st57":
            put_ustate_d(c, rnd, row, ast)
        if w == "do121":
            put_shape_d(c, rnd, row)
        dumps = [(UNODE + 0x18, 4)] if w in ("st57", "do121") else []
        finish_d(c, rnd, row, game, cases, exp, dumps=dumps)
    return cases, mem_dru(), {"cases": exp}


def hit680_d(row, game, w, neg=None):
    """0x0056E680(ECX game, EDX U; target, rec, id, lvl, &packet, 0) and the caller's code up to its next boundary:
    ResultFlags (+0x12E) bit 0 set -> packet +0x04 = ResultFlags, then (the caller) packet +0x00 = 2 | HitFlags,
    HitClass into +0x60 when non-zero, start 58 also calc1 into +0x0C, COMBAT_BuildDamage(target, &packet, 0,
    SrcDam); clear -> MeleeHitTest(target, SKILLS_GetToHit(U, id, lvl), 0) inside 0x0056E680."""
    pkt_at = fr(-0x74) if w == "st58" else fr(-0x78)
    if not row["rf"] & 1 or neg == "rf_ignored":
        slot = HIT680_SLOT[w]
        f = abs_ret(*slot)
        f[pkt_at] = bytes(0x70)
        return obs_a(row, "MeleeHitTest", {"ecx": game, "edx": U}, [T, tohit_a(row), 0], 0x0056E6B8,
                     bit6=(w == "do122"), frame=f)
    p = bytearray(0x70)
    struct.pack_into("<I", p, 0x00, (2 | row["hf"]) & M32)
    struct.pack_into("<H", p, 0x04, row["rf"])
    if row["hc"] and neg != "hc_never":
        struct.pack_into("<I", p, 0x60, row["hc"])
    if w == "st58":
        struct.pack_into("<I", p, 0x0C, ev_s(row, 0x138) & M32)
    return obs_a(row, "CombatBuildDmg", {"ecx": game, "edx": U}, [T, None, 0, row["sd"]],
                 0x005C7ED2 if w == "st58" else 0x005C7FE0, bit6=(w == "do122"), ptrs={1: bytes(p)})


def melee_dru_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_s(row, 0)
    t = tgt_unit(row)
    gu = {"ecx": game, "edx": U}
    if w in ("st58", "do122"):
        if not t:
            br["notarget"] += 1
            return ret_s(row, 0)
        br["rf1" if row["rf"] & 1 else "hittest"] += 1
        return hit680_d(row, game, w, neg)
    if row["node"] is None:
        br["noused"] += 1
        return ret_s(row, 0)
    if w == "st56":
        if not t:
            br["notarget"] += 1
            return ret_s(row, 0)
        br["hittest"] += 1
        return obs_a(row, "MeleeHitTest", gu, [T, tohit_a(row), 0], 0x005C7717, frame={fr(-0x78): bytes(0x70)})
    if w == "do121" and not t:
        br["notarget"] += 1
        return ret_s(row, 0)
    if not node_id_ok(row) and neg != "id_any":
        br["otherid"] += 1
        return ret_s(row, 0)
    if w == "st57":
        if not t:
            br["notarget"] += 1
            return ret_s(row, 0)
        ast = s16(row["ast"])
        if 0 <= ast < NSTATES and not has_state_d(row) and neg != "nostate57":
            br["noshape"] += 1
            return ret_s(row, 0)
        br["hittest_" + ("shape" if 0 <= ast < NSTATES else "any")] += 1
        return obs_a(row, "MeleeHitTest", gu, [T, tohit_a(row), 0], 0x005C7AAB, mem={UNODE + 0x18: le32(0)})
    # do 121
    if row["node"]["n18"] == 0:
        br["n18_0"] += 1
        return ret_s(row, 0)
    tot, sd = rabies_hit_d(row, neg)
    f = abs_ret(*RAB_SLOT)
    f[RAB_EBP - 0x80] = bytes(0x70)
    f[RAB_EBP - 0x8] = bytes([sd])
    br["rabies_" + ("sum" if tot else "zero")] += 1
    return obs_a(row, "MeleeHitTest", gu, [T, tot, 0], 0x005C8A9B, mem={UNODE + 0x18: le32(0)}, frame=f)


# ------------------------------------------------------------------------------------------- the missiles
MISS_ORDER_D = ("do117", "do118", "do123", "do123")
TW_SLOT = (0x7FEFFFD4, 0x005C7375)   # do 118's return address from 0x005C7040, its five arguments above it
CELL_SLOT = (0x7FEFFF80, 0x005C80F1)  # do 123's return address from sub_0056E450_SkillTargetCellFree
WH_SLOT = (0x7FEFFF4C, 0x0056E4EF)   # TargetCellFree's return address from COLL_WHTest
WH_RECT = 0x7FEFFF38                 # COLL_WHTest's rectangle (ebp-0x10)


def put_cmap_d(c, rnd, row):
    """COLL_CellTestNb's inputs: the room RoomAtSubtile(U's room, x; y) gives, its +0x20 collision map (+0x00 x0,
    +0x04 y0, +0x08 width, +0x20 the word array) and the one word at (y - y0)·width - x0 + x."""
    x, y, ok = target_xy(row)
    row["cmap"] = None
    if not ok:
        return
    r2 = room_at(row, row["uroom"], x, y)
    if not r2:
        return
    i = ROOMS.index(r2)
    if rnd.random() < 0.08:
        c.put(r2 + 0x20, le32(0))
        row["cmap"] = {"room": r2, "map": 0}
        return
    m = CMAP_D + 0x4000 * i
    _, x0, y0, ww, hh = row["rooms"][str(r2)][:5]
    arr = m + 0x100 if rnd.random() < 0.93 else 0
    c.put(r2 + 0x20, le32(m))
    c.put(m + 0x00, le32(x0) + le32(y0) + le32(ww))
    c.put(m + 0x20, le32(arr))
    v = None
    if arr:
        idx = s32(s32(s32(y - y0) * ww) - x0 + x)
        v = rnd.choice([0, 0, 0, 0, 0, 1, 4, 2, 2, 8, rnd.getrandbits(16)])
        c.put((arr + 2 * idx) & M32, le16(v))
    row["cmap"] = {"room": r2, "map": m, "arr": arr, "v": v}


@family("miss_dru", "dru")
def miss_dru(rnd, game):
    """Do 117 (Firestorm: up to SkillMissileCreate), do 118 (Twister, Tornado: 0x005C7040 up to its first
    MissileCreate), do 123 (Volcano: SkillTargetCellFree with COLL_WHTest run, the draw, up to MissileCreate)."""
    cases, exp = [], []
    for k in range(2000):
        w = MISS_ORDER_D[k % 4]
        c = Case(FND[w])
        row = {"w": w, "sid": pick_skill(rnd), "lvl": pick_lvl(rnd)}
        put_caster(c, rnd, row, types=(0, 0, 1))
        put_target_a(c, rnd, row, game)
        if w == "do123" and rnd.random() < 0.7:
            put_point_in_room(c, rnd, row)
        row["cal"] = sor_calcs(c, rnd, row["sid"], (0x138,))
        if sid_ok(row):
            put_bycharge(c, rnd, row)
            if w == "do123" and rnd.random() < 0.12:       # a class past the Missiles count (do 123 has no upper test)
                row["ms"][1] = rnd.choice([NREC, NREC + 1, 0x7FFF])
                c.put(srec(row) + 0x48, le16(row["ms"][1]))
        for i in range(NREC):
            c.put(MREC + 0x1A4 * i + 0x18A, bytes([rnd.choice([0, 1, 1, 1, 2, 3, rnd.getrandbits(8)])]))
        row["msize"] = [c.fields[MREC + 0x1A4 * i + 0x18A][0] for i in range(NREC)]
        if w == "do123":
            put_cmap_d(c, rnd, row)
        dumps = [(ARG1, 1)] if w == "do123" else []
        finish_d(c, rnd, row, game, cases, exp, dumps=dumps)
    return cases, mem_dru(), {"cases": exp}


def cellnb_d(row, neg=None):
    """COLL_CellTestNb(room, x, y, 5): 0x27 without a room at the point, a map or a word array; else the word & 5."""
    cm = row["cmap"]
    if cm is None or not cm["map"] or not cm["arr"]:
        return 0x27
    return cm["v"] & (5 if neg != "mask7" else 7)


def miss_dru_model(row, game, br, neg=None):
    w = row["w"]
    br[w] += 1
    sid, lv = s16(row["sid"]), row["lvl"]
    if not sid_ok(row):
        br["nosid"] += 1
        return ret_s(row, 0)
    m = bycharge(row)
    if w in ("do117", "do118"):
        if not 0 <= m < NREC:
            br["nomiss"] += 1
            return ret_s(row, 0)
        c1 = ev_s(row, 0x138)
        if c1 <= 0 and not (neg == "c1_ge0" and c1 == 0):
            br["c1_le0"] += 1
            return ret_s(row, 0, bit6=True)
        if w == "do117":
            br["skillcreate"] += 1
            return obs_a(row, "SkillMissileCreate", {"ecx": game, "edx": m}, [U, sid, lv, 0, 0, 0, 0, 0],
                         0x005C7206, bit6=True)
        x, y, ok = target_xy(row)
        if not ok:
            br["noxy"] += 1
            return ret_s(row, 1, bit6=True)
        blk = bytearray(blk9d(flags=0x21 if neg != "flags1" else 0x01, owner=U, cls=m, x=row["ux"], y=row["uy"],
                              skill=sid, lvl=lv, tx=x, ty=y, cb=0x005C9290))
        f = abs_ret(*TW_SLOT)
        f[TW_SLOT[0] + 4] = b"".join(le32(v) for v in (c1, m, sid, lv, 0))
        br["twister"] += 1
        return obs_a(row, "MissileCreate", {"ecx": game}, [], 0x005C7140, bit6=True, stk={"edx": (0, bytes(blk))},
                     frame=f)
    # do 123
    if m <= 0:
        br["nomiss"] += 1
        return ret_s(row, 0)
    x, y, ok = target_xy(row)
    if not ok:
        br["noxy"] += 1
        return ret_s(row, 0)
    if m >= NREC and neg != "cls_hi":
        br["fatal"] += 1
        return obs_a(row, "Fatal", {}, [0x1281], 0x0056E4A3, frame=abs_ret(*CELL_SLOT))
    if m >= NREC:
        return ret_s(row, 0)
    if not row["uroom"]:
        br["noroom"] += 1
        return ret_s(row, 0)
    sz = row["msize"][m]
    if sz > 1:
        x0, y0 = s32(x - (sz >> 1)), s32(y - (sz >> 1))
        rect = b"".join(le32(v) for v in (x0, y0, x0 + sz - 1, y0 + sz - 1))
        f = abs_ret(*CELL_SLOT)
        f.update(abs_ret(*WH_SLOT))
        f[WH_RECT] = rect
        br["recttest"] += 1
        return obs_a(row, "RectTest", {"ecx": row["uroom"], "edx": WH_RECT}, [5], 0x0064D866, frame=f)
    if cellnb_d(row, neg):
        br["busy"] += 1
        return ret_s(row, 0)
    s0 = row["seeds"][0]
    r, lo, hi = rrange(s0[0], s0[1], 0x100)
    useed = (lo, hi) if neg != "noseed" else None
    blk = block(flags=1, owner=U, cls=m, x=x, y=y, skill=sid, lvl=lv)
    br["volcano"] += 1
    e = obs_s(row, "MissileCreate", {"ecx": game}, [], 0x005C814D, bit6=True, stk={"edx": (0, blk)},
              mem={ARG1: bytes([r & 0xFF])}, useed=useed)
    return e + ({},)


CHECKS.update({
    "summon_dru": check9b("summon_dru", summon_dru_model, ["pet_zero", "xy_pos", "w24_zero", "mode10"], RS_DRU,
                          md_masked=False),
    "shape_dru": check9b("shape_dru", shape_dru_model, ["ast_le", "noclamp", "seed_none", "notown", "p4_noframe"],
                         RS_DRU, md_masked=False),
    "melee_dru": check9b("melee_dru", melee_dru_model, ["rf_ignored", "hc_never", "id_any", "nostate57", "sd_first",
                                                        "sd_none"],
                         RS_DRU, md_masked=False),
    "miss_dru": check9b("miss_dru", miss_dru_model, ["c1_ge0", "flags1", "cls_hi", "mask7", "noseed"], RS_DRU,
                        md_masked=False),
})

PINS_DRU = [  # (address, mnemonic, operand substring): instructions the dru claims turn on (ADR-0015 (5))
    (0x005C6975, "movsx", "eax,dl"), (0x005C697A, "jl", ""), (0x005C698E, "jge", ""),               # do 114: pet
    (0x005C6B4B, "mov", "DWORD PTR [ebp-0x20],0x8"),                                                  # do 115
    (0x005C7441, "je", ""), (0x005C7481, "mov", "DWORD PTR [ebp-0x20],eax"),                          # do 119
    (0x005C6EFD, "jl", ""), (0x005C6F1C, "push", "0x1"),                                              # do 116
    (0x005C71E5, "jle", ""), (0x005C71AC, "jl", ""), (0x005C71BE, "jge", ""),                         # do 117
    (0x005C735D, "jle", ""), (0x005C7046, "cmp", "DWORD PTR [ebp+0x18],0x0"),                         # do 118
    (0x005C70A0, "mov", "DWORD PTR [ebp-0x5c],0x21"), (0x005C711D, "mov", "DWORD PTR [ebp-0x8],0x5c9290"),
    (0x005C7809, "jl", ""), (0x005C7842, "jne", ""), (0x005C7875, "je", ""),                          # do 120
    (0x005C8228, "mov", "edx,0x10000"), (0x005C8247, "jge", ""),                                      # do 124
    (0x005C83BF, "jle", ""), (0x005C83E8, "test", "BYTE PTR [ebx+0x5],al"), (0x005C8462, "jle", ""),  # do 145
    (0x005C8479, "mov", "DWORD PTR [ebp+0x8],eax"),
    (0x005C85FC, "jle", ""), (0x005C8629, "jle", ""), (0x005C8688, "call", "0x650e40"),              # do 146
    (0x005C7A66, "jl", ""), (0x005C7A82, "je", ""),                                                   # start 57
    (0x0056E68E, "test", "al,0x1"), (0x005C7E83, "or", "eax,0x2"), (0x005C7FB3, "or", "WORD PTR [ebp-0x74],cx"),
    (0x005C89B3, "cmp", "WORD PTR [eax+0x180],bx"), (0x005C8A59, "je", ""), (0x005C89BD, "mov", "BYTE PTR [ebp-0x8],0x80"),
    (0x005C80CA, "jle", ""), (0x005C8103, "mov", "edx,0x100"), (0x005C8115, "mov", "BYTE PTR [ebp+0x8],al"),  # do 123
    (0x0056E46B, "cmp", "eax,DWORD PTR [ecx+0xb6c]"), (0x0064D80C, "cmp", "ecx,0x1"), (0x0064CA83, "and", "eax,DWORD PTR [ebp+0x8]"),
    (0x006256C3, "test", "DWORD PTR [eax+0x10],0x80000000"), (0x00625663, "test", "edx,edx"),       # FindStatList
]


def cmd_static_dru(a):
    rep = Report("static")
    rep.batch = "DRU"
    A = S4.asm()
    for va, mn, sub in PINS_DRU:
        ins = A.at(va)
        rep.c["pins"] += 1
        if ins is None or ins[0] != mn or sub not in ins[1]:
            rep.bad("pin 0x%08X: %r, want %s %s" % (va, ins, mn, sub))
        else:
            rep.c["pins_ok"] += 1
    for lo, n, name in ((BITMASK, 128, "g_BitMask32"), (0x006E10E0, 20, "hash offsets"),
                        (0x006C1164, 88, "CALC_Eval jump table"), (0x006426C0, 8 + 0x6D, "town tables")):
        sec = S4.section_of(lo)
        flags = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.c["ro_reads"] += 1
        if flags & 0x80000000:
            rep.bad("%s 0x%08X in writable %s" % (name, lo, sec))
        rep.notes.append("%s 0x%08X: %s" % (name, lo, sec))
    st, im, rd = ref_scan(A, SK_NFUNCS)
    rep.c["data_stores"] += len(st)
    rep.c["data_imms"] += len(im)
    rep.notes.append("skills calc function count 0x%08X: %d stores (PTR or moffs), %d immediates, %d reads in .text"
                     % (SK_NFUNCS, len(st), len(im), len(rd)))
    for hlp in (0x5C7040, 0x56E680, 0x5C8980, 0x56E450, 0x64D800):
        sites = sorted(va for va, (mn, ops) in A.ins.items() if mn == "call" and ops.strip() == "0x%x" % hlp)
        rep.notes.append("calls of 0x%08X: %d in the image: %s" % (hlp, len(sites), " ".join("0x%08X" % s for s in sites)))
        rep.c["helper_sites"] += len(sites)
    for lo in (0x17C, 0x180):
        refs = sorted(va for va, (mn, ops) in A.ins.items() if ("+0x%x]" % lo) in ops and va in range(0x5C8980, 0x5C8AC4))
        rep.notes.append("0x005C8980 operands naming +0x%X: %s" % (lo, " ".join("0x%08X" % v for v in refs)))
    for name, va in sorted(FND.items(), key=lambda kv: kv[1]):
        tab = START_TABLE if name.startswith("st") else DO_TABLE
        num = int(name[2:])
        rep.c["table_entries"] += 1
        if S4.dword(tab + 4 * num) != va:
            rep.bad("%s: table entry 0x%08X, model address 0x%08X" % (name, S4.dword(tab + 4 * num), va))
    rep.notes.append("start table 56-58: %s" % " ".join("%d:0x%08X" % (i, S4.dword(START_TABLE + 4 * i))
                                                        for i in (56, 57, 58)))
    rep.notes.append("do table 114-124, 145, 146: %s" % " ".join(
        "%d:0x%08X" % (i, S4.dword(DO_TABLE + 4 * i)) for i in list(range(114, 125)) + [145, 146]))
    print("CATDRU static " + " ".join("%s=%d" % (k, rep.c[k]) for k in sorted(rep.c)))
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
    if a.batch == "ama":
        return cmd_static_ama(a)
    if a.batch == "nec":
        return cmd_static_nec(a)
    if a.batch == "pal":
        return cmd_static_pal(a)
    if a.batch == "bar":
        return cmd_static_bar(a)
    if a.batch == "dru":
        return cmd_static_dru(a)
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
    ap.add_argument("--batch", default="9a", choices=["9a", "9b", "9c", "9d", "sor", "ama", "nec", "pal", "bar", "dru"], help="the families of one batch (default 9a)")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    return {"cases": cmd_cases, "check": cmd_check, "static": cmd_static, "manifest": cmd_manifest}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

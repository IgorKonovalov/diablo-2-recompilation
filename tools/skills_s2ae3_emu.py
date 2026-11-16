#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S2ae part 3 (`lane/n66sa`): the collide-type mask uses, three small missile functions
under Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java, and the route reads of
the rows whose claim lies past an allocator.

    python3 -I tools/skills_s2ae3_emu.py cases [--dir D] [--limit N]   write D/s2ae.cases, D/s2ae.mem and the tables
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s2ae.cases D/s2ae.mem > D/s2ae.out
    python3 -I tools/skills_s2ae3_emu.py check [--dir D] [--limit N]   compare, account for traced reads, controls
    python3 -I tools/skills_s2ae3_emu.py reach [--limit N]             model outcomes and branch reach per family
    python3 -I tools/skills_s2ae3_emu.py static                        objdump of the functions run; table references
    python3 -I tools/skills_s2ae3_emu.py masks                         the uses of the two g_MissileCollideTypes leas
    python3 -I tools/skills_s2ae3_emu.py sites                         per root: each direct call site, in address
                                                                        order, and whether its callee reaches the pool
                                                                        allocator or an import (the route reads)
    python3 -I tools/skills_s2ae3_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66sa/s2ae/run3. Parts 1 and 2 (tools/skills_s2ae_emu.py, tools/skills_s2ae2_emu.py) and
their run/ and run2/ are unchanged; this tool reuses part 1's check machinery (build, predict, cmd_check) in its module
state only. Every draw comes from random.Random("n66sa-s2ae3-<family>"); the declared Missiles rows from
random.Random("n66sa-s2ae3-tables").

The models read each case's own memory (the bytes the case writes; an unwritten read is a model error) and the image
(the .data tables g_SkillDoFuncs and g_UModEventFns, read from the pinned file). Every callee runs whole on the
declared image unless named as an observed boundary (ADR-0021): the case ends at that call and its claim ends there.
The allocator entries and the fatal path are guards.

Families (function, registers; inventory rows, d = skills/dispatch, m = skills/missiles):
  h27  0x005ABA00 missile hit function 27 (ECX, EDX, one stack argument), whole.                    m73
  cdo  0x0056D810 sub_0056D810_CallDoFunc (ECX, EDX passed through; n, skill, lvl): every non-null g_SkillDoFuncs entry
       (0x007322B0, 191 entries, .data, image bytes) is an observed boundary, from 0x0056D831.       m69
  uev  0x005A43B0 sub_005A43B0_MissileOwnerUModEvent (ECX game, EDX monster; missile) through
       sub_005A4270_UModEventRun (slot 5) and unique mod 29's slot-5 function 0x005A3610, whole through
       sub_00552FD0_UnitGetOwner, sub_00552F60_GameFindUnit (a declared game: the bucket heads the case uses),
       sub_005A0180_MonTypeFlag, UNIT_GetTargetUnit, sub_00553490_PathTargetRevalidate, the path getters,
       UnitGetSubX/Y, RNG_SeedInitOne, RNG_SeedInit, MISSDATA_GetLevel, MISSDATA_GetSkill. Observed boundaries:
       sub_0056ECB0_SkillMissileCreate (the first creation, from 0x005A377C) and the other two slot-5 functions,
       mod 19's 0x005A2E00 and mod 27's 0x005A30B0 (from 0x005A432D). The monster's unique-mod bytes are drawn
       from 0..42 (rows whose slot-5 entry is read from the image).                                  m21

Controls as parts 1 and 2: every named test reversed alone, every ordered compare's strictness switched alone; `sep`
counts the cases a control changes, `passed` those the emulator still matches (must be 0); `spec_*` controls are
the spec's own readings where they differ from the code. Stdlib only, plus objdump for `static`, `masks`, `sites`.
"""
import argparse
import os
import random
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import combat_s5e_emu as p1  # noqa: E402
import skills_s2ae_emu as B  # noqa: E402
from combat_s5e_emu import u32, s32, le32, G_DT, DT, FATAL, ALLOC, BITMASK  # noqa: E402

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66sa", "s2ae", "run3")
FNS = {"h27": 0x005ABA00, "cdo": 0x0056D810, "uev": 0x005A43B0}
FAMILIES = ("h27", "cdo", "uev")
NCASES = {"h27": 300, "cdo": 1500, "uev": 3000}
POP = {"h27": 4, "cdo": 12, "uev": 4}
p1.FNS.update(FNS)

G_DOF, N_DOF = 0x007322B0, 0xBF        # g_SkillDoFuncs
G_UMF, N_UMOD = 0x0073C0B8, 43         # g_UModEventFns: six code pointers per MonUMod row; rows 0..42 used here
MOD29 = 0x005A3610
SMC = 0x0056ECB0                       # sub_0056ECB0_SkillMissileCreate
CDO_SITE, UMR_SITE, MOD29_SITE = 0x0056D833, 0x005A432F, 0x005A3781

GAME = 0x20010000
MISU, MISD, MISP = 0x20003000, 0x20003400, 0x20003600
NODES = 0x20020000                     # node k: unit at +0x400k, data at +0x200, path at +0x300
MON = NODES                            # node 0: the monster at EDX
MIS, MIS_N, MIS_SZ = 0x21600000, 0x50, 0x1A4
BUCKET = (4384, 4896, 5408, 6432, 5920)  # 0x006E10E0, the five per-type bucket offsets (.rdata), type 5 at +0x1B20

TABLES = None


def tables():
    global TABLES
    if TABLES is None:
        r = random.Random("n66sa-s2ae3-tables")
        TABLES = bytearray(r.getrandbits(8) for _ in range(MIS_N * MIS_SZ))
        for i in range(MIS_N):                       # Missiles +5 bit 4 set in about one row of five
            if r.random() < 0.8:
                TABLES[i * MIS_SZ + 5] &= ~0x10
    return TABLES


IMG = {}


def img32(va):
    if va not in IMG:
        IMG[va] = struct.unpack("<I", B.img_bytes(va, 4))[0]
    return IMG[va]


class Case(p1.Case):
    pass


# ----------------------------------------------------------------------------------------------- memory views
class Mem:
    """The case's own bytes; an unwritten read raises KeyError (the model reads only what the case declares)."""

    def __init__(self, w):
        self.w = dict(w)

    def b(self, a):
        return self.w[a]

    def h(self, a):
        return self.w[a] | (self.w[a + 1] << 8)

    def d(self, a):
        return self.h(a) | (self.h(a + 2) << 16)

    def put(self, a, v, n=4):
        for i in range(n):
            self.w[a + i] = (v >> (8 * i)) & 0xFF


def sx16(v):
    return v - 0x10000 if v & 0x8000 else v


# ----------------------------------------------------------------------------------------------- h27
def gen_h27(rnd):
    c = Case("h27")
    c.ecx, c.edx = rnd.getrandbits(32), rnd.getrandbits(32)
    c.args = [rnd.getrandbits(32)]
    c.a = {}
    return c


def m_h27(e, a):
    e.names.add("spec_ret0")
    return ("ret", 0 if e.flip == "spec_ret0" else 1)


# ----------------------------------------------------------------------------------------------- cdo
def gen_cdo(rnd):
    c = Case("cdo")
    n = rnd.choice([rnd.randrange(N_DOF + 4), rnd.randrange(N_DOF + 4), 0xBE, 0xBF, 0, 30,
                    rnd.getrandbits(32), u32(-rnd.randint(1, 8))])
    c.ecx, c.edx = rnd.getrandbits(32), rnd.getrandbits(32)
    c.args = [n, rnd.getrandbits(32), rnd.getrandbits(32)]
    c.a = dict(n=n, sk=c.args[1], lv=c.args[2], ecx=c.ecx, edx=c.edx)
    return c


def m_cdo(e, a):
    n = a["n"]
    e.names.add("spec_signed")
    if e.flip == "spec_signed":
        ok = s32(n) <= 0xBE
        if ok and s32(n) < 0:
            return ("model-oob",)
    else:
        ok = e.c("n_le_be", n, "<=", 0xBE)
    if not ok:
        return ("ret", n)
    if n > 0x400:
        raise IndexError(n)          # a reversed bound past the table: the model has no image byte to give
    fn = img32(G_DOF + 4 * n)
    if not e.t("entry_nz", fn != 0):
        return ("ret", fn)
    return ("obs", fn, (a["ecx"], a["edx"], a["sk"]), (a["sk"], a["lv"]))


# ----------------------------------------------------------------------------------------------- uev
def put_node(c, rnd, k, typ, uid, data=True, path=True):
    base = NODES + 0x400 * k
    c.put(base, bytes(rnd.getrandbits(8) for _ in range(0x100)))
    c.put(base, le32(typ))
    c.put(base + 0xC, le32(uid))
    c.put(base + 0xE4, le32(0))
    d = base + 0x200 if data else 0
    c.put(base + 0x14, le32(d))
    if data:
        c.put(d, bytes(rnd.getrandbits(8) for _ in range(0x28)))
    p = base + 0x300 if path else 0
    c.put(base + 0x2C, le32(p))
    if path:
        c.put(p, bytes(rnd.getrandbits(8) for _ in range(0x64)))
        c.put(p + 0x58, le32(0))
    return dict(base=base, typ=typ, id=uid, data=d, path=p)


def bucket_addr(t, uid):
    if t == 5:
        return GAME + 0x1B20
    return GAME + BUCKET[t] + (uid & 0x7F) * 4


def gen_uev(rnd):
    c = Case("uev")
    k = 0
    chains = {}
    looks = []

    def link(node, decoy=False):
        nonlocal k
        ba = bucket_addr(node["typ"], node["id"])
        lst = chains.setdefault(ba, [])
        if decoy and rnd.random() < 0.5:
            dn = put_node(c, rnd, k, node["typ"], u32(node["id"] + rnd.choice([0x80, 1, 0x100])))
            k += 1
            lst.append(dn)
        lst.append(node)

    # the monster at EDX: a node of its own (k = 0), often the missile's owner as well
    mtyp = 1 if rnd.random() < 0.93 else rnd.choice([0, 2, 3])
    mon = put_node(c, rnd, k, mtyp, rnd.getrandbits(32), data=rnd.random() > 0.03)
    k += 1
    if mon["data"]:
        d = mon["data"]
        umods = []
        first = rnd.choice([29] * 8 + [0, 19, 27, rnd.randrange(N_UMOD)])
        umods.append(first)
        for _ in range(8):
            umods.append(rnd.choice([0, 0, 0, 0, 0, 0, 29, 29, 29, 19, 27, rnd.randrange(N_UMOD)]))
        c.put(d + 0x1C, bytes(umods))
        w16 = rnd.getrandbits(16)
        if rnd.random() < 0.8:
            w16 |= 0x08
        if rnd.random() < 0.7:
            w16 &= ~0x80
        c.put(d + 0x16, struct.pack("<H", w16))
    # the missile
    mtype = 3 if rnd.random() < 0.94 else rnd.choice([0, 1, 2, 4])
    cls = rnd.choice([rnd.randrange(MIS_N)] * 5 + [rnd.randint(0x3F, 0x42)] * 2 + [-1, 0, MIS_N, 0x3E, 0x43])
    c.put(MISU, bytes(rnd.getrandbits(8) for _ in range(0x100)))
    c.put(MISU, le32(mtype) + le32(u32(cls)))
    if rnd.random() < 0.95:
        c.put(MISU + 0x14, le32(MISD))
        c.put(MISD, bytes(rnd.getrandbits(8) for _ in range(0x20)))
    else:
        c.put(MISU + 0x14, le32(0))
    c.put(MISU + 0x2C, le32(MISP))
    c.put(MISP, bytes(rnd.getrandbits(8) for _ in range(0x20)))
    c8 = rnd.getrandbits(32)
    c8 = (c8 | 0x400) if rnd.random() < 0.9 else (c8 & ~0x400)
    c.put(MISU + 0xC8, le32(c8))
    # the owner: the monster itself, another node, or absent
    r = rnd.random()
    if r < 0.45 and mon["path"]:
        owner = mon
    else:
        owner = put_node(c, rnd, k, rnd.choice([1, 1, 0, 0, 2, 3, 4, 5]), rnd.getrandbits(32))
        k += 1
        if owner["typ"] == 1 and owner["data"]:
            w16 = rnd.getrandbits(16)
            if rnd.random() < 0.8:
                w16 &= ~0x80
            c.put(owner["data"] + 0x16, struct.pack("<H", w16))
    absent = rnd.random() < 0.06
    if not absent:
        link(owner, decoy=True)
    ot, oid = owner["typ"], owner["id"]
    if rnd.random() < 0.05:
        oid = u32(oid + 0x80)                        # a stale id: the bucket holds another unit
    c.put(MISU + 0x94, le32(ot) + le32(oid))
    # the owner's path target
    tr = rnd.random()
    p = owner["path"]
    if tr < 0.2:
        pass
    elif tr < 0.3:                                    # the owner itself
        c.put(p + 0x58, le32(owner["base"]) + le32(owner["typ"]) + le32(owner["id"]))
    else:
        tt = rnd.choice([0, 1, 1, 2, 3, 4, 4, 5])
        tgt = put_node(c, rnd, k, tt, rnd.getrandbits(32), path=rnd.random() > 0.05 or tt in (2, 4, 5))
        k += 1
        c.put(tgt["base"] + 0x10, le32(rnd.choice([0, 1, 2, 3, rnd.getrandbits(32)])))
        stale = rnd.random() < 0.12
        c.put(p + 0x58, le32(tgt["base"]) + le32(tt) + le32(u32(tgt["id"] + (1 if stale else 0))))
        if rnd.random() > 0.05:
            link(tgt, decoy=True)
        looks.append(bucket_addr(tt, u32(tgt["id"] + (1 if stale else 0))))
    for ba, lst in chains.items():
        c.put(ba, le32(lst[0]["base"]))
        for x, y in zip(lst, lst[1:]):
            c.put(x["base"] + 0xE4, le32(y["base"]))
    # every other bucket a lookup reads (a stale id's, an absent unit's): empty
    for ba in looks + [bucket_addr(ot, oid)]:
        if ba not in chains:
            c.put(ba, le32(0))
    for (va, n) in ((owner["path"] + 0x58, 4),) + (((owner["data"] + 0x14, 4),) if owner["data"] else ()):
        c.dumps.append((va, n))
    c.dumps.sort()
    c.ecx = GAME
    c.edx = 0 if rnd.random() < 0.02 else MON
    arg = 0 if rnd.random() < 0.02 else MISU
    c.args = [arg]
    c.a = dict(w=dict(c.w), edx=c.edx, arg=arg, dumps=list(c.dumps))
    return c


def find_unit(M, t, uid):
    if t == 5:
        head = GAME + 0x1B20
    elif t <= 4:
        head = GAME + BUCKET[t] + (uid & 0x7F) * 4
    else:
        raise KeyError("type")
    q = M.d(head)
    for _ in range(32):
        if q == 0:
            return 0
        if M.d(q + 0xC) == uid:
            return q
        q = M.d(q + 0xE4)
    raise KeyError("chain")


def sub_xy(M, u):
    t = s32(M.d(u))
    if t == 2 or 3 < t <= 5:
        p = M.d(u + 0x2C)
        return M.d(p + 0xC), M.d(p + 0x10)
    p = M.d(u + 0x2C)
    if p == 0:
        return 0, 0
    return M.h(p + 2), M.h(p + 6)


def sign(v):
    return -1 if v < 0 else (1 if v > 0 else 0)


def mod29(e, M, mis, um, flag, idx):
    if not e.t("z_flag", flag != 0):
        return None
    if not e.t("z_type3", M.d(mis) == 3):
        return None
    cls = s32(M.d(mis + 4))
    owner = 0
    if e.t("o_bit10", (M.d(mis + 0xC8) >> 10) & 1):
        owner = find_unit(M, M.d(mis + 0x94), M.d(mis + 0x98))
    if not e.t("z_owner", owner != 0):
        return None
    if not e.c("z_cls_ge0", cls, ">=", 0) or not e.c("z_cls_lt", cls, "<", MIS_N):
        return None
    if e.t("z_rowbit", tables()[cls * MIS_SZ + 5] & 0x10):
        return None
    od = M.d(owner + 0x14) if M.d(owner) == 1 else 0
    if e.t("z_busy", od != 0 and M.h(od + 0x16) & 0x80):
        return None
    # UNIT_GetTargetUnit(game, owner) through PathTargetRevalidate
    p = M.d(owner + 0x2C)
    pt = M.d(p + 0x58)
    if e.t("t_has", pt != 0):
        found = find_unit(M, M.d(p + 0x5C), M.d(p + 0x60))
        if e.t("t_moved", found != pt):
            M.put(p + 0x58, 0)
        if found and e.t("t_item", M.d(found) == 4) and e.t("t_mode12", M.d(found + 0x10) in (1, 2)):
            M.put(p + 0x58, 0)
    tgt = M.d(p + 0x58)
    if e.t("t_self", tgt == owner):
        tgt = 0
    if e.t("z_tgt", tgt != 0):
        x0, y0 = sub_xy(M, tgt)
    else:
        mp = M.d(mis + 0x2C)
        x0, y0 = M.h(mp + 0x10), M.h(mp + 0x12)
    seed = (0x53454953, M.d(owner + 0xC))
    ox, oy = sub_xy(M, owner)
    dx, dy = sign(s32(ox - x0)), sign(s32(oy - y0))
    e.names.add("spec_no_zero")
    if e.flip != "spec_no_zero" and e.c("z_c3f", cls, ">=", 0x3F) and e.c("z_c42", cls, "<=", 0x42):
        dx = dy = 0
    if e.t("z_ownmon", M.d(owner) == 1) and e.t("z_owndata", M.d(owner + 0x14) != 0):
        a = M.d(owner + 0x14) + 0x16
        M.put(a, M.h(a) | 0x80, 2)
    md = M.d(mis + 0x14)
    lvl = sx16(M.h(md + 0xC)) if md else 0
    skl = sx16(M.h(md + 0xA)) if md else 0
    e.names.add("spec_same_side")
    sgn = -1 if e.flip == "spec_same_side" else 1
    args = (owner, u32(skl), u32(lvl), 0, 0, u32(x0 - sgn * dy), u32(y0 + sgn * dx), 0,
            MOD29, MON, idx, seed[0], seed[1], GAME, u32(cls))
    return ("obs", SMC, (GAME, u32(cls)), args)


def m_uev(e, a):
    M = Mem(a["w"])
    mon, mis = a["edx"], a["arg"]
    out = None
    if e.t("e_mon", mon != 0) and e.t("e_type1", M.d(mon) == 1) and e.t("e_arg", mis != 0):
        d = M.d(mon + 0x14)
        flag = (M.b(d + 0x16) >> 3) & 1 if d else 0
        if e.t("r_data", d != 0) and e.t("r_first", M.b(d + 0x1C) != 0):
            for i in range(9):
                um = M.b(d + 0x1C + i)
                fn = img32(G_UMF + 4 * (6 * um + 5))
                if not e.t("r_fn", fn != 0):
                    continue
                if fn != MOD29:
                    out = ("obs", fn, (GAME, mis), (um, flag))
                    break
                r = mod29(e, M, mis, um, flag, i)
                if r is not None:
                    out = r
                    break
    dumps = tuple(bytes(M.w.get(va + i, 0) for i in range(n)) for va, n in a["dumps"])
    if out is None:
        return ("ret", dumps)
    return out + (dumps,)


GEN = {"h27": gen_h27, "cdo": gen_cdo, "uev": gen_uev}
MODEL = {"h27": m_h27, "cdo": m_cdo, "uev": m_uev}


def site_of(fam, addr):
    if fam == "cdo":
        return CDO_SITE
    return MOD29_SITE if addr == SMC else UMR_SITE


class Sites(dict):
    def __missing__(self, key):
        return site_of(*key)


SITE = Sites()


# ----------------------------------------------------------------------------------------------- spec, check
def do_targets():
    return sorted({img32(G_DOF + 4 * i) for i in range(N_DOF)} - {0})


def write_spec(d):
    with open(os.path.join(d, "missiles.bin"), "wb") as f:
        f.write(bytes(tables()))
    dt = bytearray(0x1000)
    for off, v in ((0xB64, MIS), (0xB6C, MIS_N)):
        struct.pack_into("<I", dt, off, v)
    with open(os.path.join(d, "dt.bin"), "wb") as f:
        f.write(bytes(dt))
    lines = ["# plan 0066 S2ae part 3 (tools/skills_s2ae3_emu.py): declared tables",
             "dword %08x %08x" % (G_DT, DT),
             "load %08x %s" % (DT, os.path.join(d, "dt.bin")),
             "load %08x %s" % (MIS, os.path.join(d, "missiles.bin"))]
    lines += ["guard %08x" % x for x in FATAL + ALLOC]
    obs = set(do_targets()) | {SMC, 0x005A2E00, 0x005A30B0}
    lines += ["observe %08x" % x for x in sorted(obs)]
    with open(os.path.join(d, "s2ae.mem"), "w") as f:
        f.write("\n".join(lines) + "\n")


def observed(fam, k):
    if "stop" in k:
        return ("stop", k["stop"], k["msg"]), None
    dumps = k["dumps"]
    if "obs" in k:
        st = k["stack"]
        ret = struct.unpack_from("<I", st, 0)[0]
        regs = k["regs"]
        if fam == "cdo":
            return ("obs", k["obs"], (int(regs["ecx"], 16), int(regs["edx"], 16), int(regs["esi"], 16)),
                    struct.unpack_from("<2I", st, 4)), ret
        if k["obs"] == SMC:
            return ("obs", k["obs"], (int(regs["ecx"], 16), int(regs["edx"], 16)),
                    struct.unpack_from("<15I", st, 4), tuple(dumps[va] for va in sorted(dumps))), ret
        return ("obs", k["obs"], (int(regs["ecx"], 16), int(regs["edx"], 16)), struct.unpack_from("<2I", st, 4),
                tuple(dumps[va] for va in sorted(dumps))), ret
    if k["pop"] != POP[fam]:
        return ("pop", k["pop"]), None
    if fam == "uev":
        return ("ret", tuple(dumps[va] for va in sorted(dumps))), None
    return ("ret", k["eax"]), None


def norm(fam, want):
    if fam == "uev" and want[0] in ("ret", "obs"):
        return want     # dumps are in the cases' dump order, which is address order (path +0x58 below data +0x14)
    return want


READS = ((BITMASK, BITMASK + 128, "g_BitMask32 0x006CE268 (.rdata)"),
         (G_DOF, G_DOF + 4 * N_DOF, "g_SkillDoFuncs 0x007322B0 (.data; reference scan in `static`)"),
         (G_UMF, G_UMF + 24 * N_UMOD, "g_UModEventFns 0x0073C0B8 (.data; reference scan in `static`)"),
         (0x006E10E0, 0x006E10E0 + 20, "the bucket offsets 0x006E10E0 (.rdata)"))


def account(reads, writes):
    bad = []
    for pc, addr, n, cnt in reads:
        if not any(lo <= addr and addr + n <= hi for lo, hi, _ in READS):
            bad.append(("R", pc, addr, n, cnt))
    for pc, addr, n, cnt in writes:
        bad.append(("W", pc, addr, n, cnt))
    return bad


def install():
    """Point part 1's check machinery at this part's families (its module state only; part 1's file is unchanged)."""
    B.FNS, B.FAMILIES, B.NCASES, B.POP, B.SITE = FNS, FAMILIES, NCASES, POP, SITE
    B.GEN, B.MODEL = GEN, MODEL
    B.observed, B.norm, B.account, B.write_spec = observed, norm, account, write_spec
    B.Case = Case

    def build(limit=None):
        cases = []
        for fam in FAMILIES:
            rnd = random.Random("n66sa-s2ae3-" + fam)
            for _ in range(NCASES[fam] if limit is None else min(limit, NCASES[fam])):
                cases.append(GEN[fam](rnd))
        return cases
    B.build = build


# ----------------------------------------------------------------------------------------------- static reads
STATIC = (
    ("h27", 0x005ABA00, 0x005ABA08),
    ("cdo", 0x0056D810, 0x0056D838),
    ("uev", 0x005A43B0, 0x005A43D4),
    ("umrun", 0x005A4270, 0x005A4340),
    ("mod29", 0x005A3610, 0x005A37C9),
    ("owner", 0x00552FD0, 0x00553002),
    ("findunit", 0x00552F60, 0x00552FCD),
    ("typeflag", 0x005A0180, 0x005A01A2),
    ("gettarget", 0x00553540, 0x00553569),
    ("revalidate", 0x00553490, 0x00553534),
    ("pathtgt", 0x00648BF0, 0x00648C03),
    ("pathtgtid", 0x00648BB0, 0x00648BED),
    ("pathsettgt", 0x00648B90, 0x00648BAD),
    ("pathx", 0x00648A00, 0x00648A0C),
    ("pathy", 0x00648A10, 0x00648A1C),
    ("subx", 0x0045ADF0, 0x0045AE19),
    ("suby", 0x0045AE20, 0x0045AE49),
    ("pathsx", 0x006488C0, 0x006488EF),
    ("pathsy", 0x00648900, 0x0064892F),
    ("seed1", 0x00650E30, 0x00650E3E),
    ("seed", 0x00650E40, 0x00650E4A),
    ("lvl", 0x0064A210, 0x0064A232),
    ("skill", 0x0064A280, 0x0064A2A2),
    ("collide", 0x005AE1F0, 0x005AE3FB),
    ("pathlist", 0x00648F40, 0x00648F83),
)


def objdump(lo, hi):
    out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "-M", "intel", "--start-address=0x%x" % lo,
                          "--stop-address=0x%x" % hi, p1.EXE], capture_output=True, text=True, check=True).stdout
    for ln in out.splitlines():
        ln = ln.strip()
        if ln and ln[0] in "0123456789abcdef" and ":\t" in ln:
            yield " ".join(ln.split())


def table_refs(A, lo, hi):
    hits = []
    for va in sorted(A.ins):
        mn, ops = A.ins[va]
        for tok in ops.replace(",", " ").replace("[", " ").replace("]", " ").replace("+", " ").replace("*", " ").split():
            if tok.startswith("0x"):
                try:
                    v = int(tok, 16)
                except ValueError:
                    continue
                if lo <= v < hi:
                    hits.append("%08x %s %s" % (va, mn, ops))
    return hits


def cmd_static():
    if p1.img() is None:
        return 1
    for label, lo, hi in STATIC:
        for ln in objdump(lo, hi):
            print("%s %s" % (label, ln))
    import sweep_s4b as W
    A = W.asm()
    for i in range(N_DOF):
        print("DOF %d %08x" % (i, img32(G_DOF + 4 * i)))
    print("DOF entry 191 (past the bound) %08x" % img32(G_DOF + 4 * N_DOF))
    for m in range(N_UMOD):
        print("UMF mod=%d slot5=%08x" % (m, img32(G_UMF + 4 * (6 * m + 5))))
    for name, lo, hi in (("DOF", G_DOF, G_DOF + 4 * N_DOF), ("UMF", G_UMF, G_UMF + 24 * N_UMOD)):
        print("SECTION %s %08x %s" % (name, lo, W.section_of(lo)))
        h = table_refs(A, lo, hi)
        for x in h:
            print("%s-REF %s" % (name, x))
        print("%s-REF count=%d" % (name, len(h)))
    print("CALLERS CallDoFunc " + " ".join("%08x" % va for va in sorted(A.ins) if A.ins[va][0] == "call"
                                           and A.ins[va][1].split()[0] == "0x56d810"))
    return 0


# ----------------------------------------------------------------------------------------------- the mask uses
LEA_FN = (0x005AE1F0, 0x005AE3FB)       # sub_005AE1F0_MissileMoveCollide
GCT = 0x0073C720


def cmd_masks():
    """Def-use of the two g_MissileCollideTypes addresses that sub_005AE1F0 forms with lea: the register each lea
    defines and the stack slot it is spilled to, every later instruction that names that register (until it is
    redefined) or slot, and for each load from the slot the register's uses until it is redefined. A store through
    either pointer would be a use with the register as the base of a memory destination."""
    import sweep_s4b as W
    A = W.asm()
    ins = list(A.range(*LEA_FN))
    print("MASKS function %08x-%08x instructions=%d" % (LEA_FN[0], LEA_FN[1], len(ins)))
    stores = 0

    def follow(start, reg, why):
        nonlocal stores
        for va, (mn, ops) in ins:
            if va <= start:
                continue
            parts = [x.strip() for x in ops.split(",")]
            dst = parts[0] if parts else ""
            mem_dst = "[" in dst
            names_reg = reg in ops.replace("[", " ").replace("]", " ").replace("+", " ").replace("*", " ").replace(
                ",", " ").split()
            if mn == "call" and reg in ("eax", "ecx", "edx"):
                print("  %s %08x %s %s  redefines %s (a call's return or scratch register)" % (why, va, mn, ops, reg))
                return
            if not names_reg:
                continue
            if mem_dst and reg in dst and mn not in ("cmp", "test", "push"):
                kind = "STORE-THROUGH"
                stores += 1
            elif mn in ("mov", "lea", "movzx", "movsx", "pop", "xor") and dst == reg and not (
                    "[" in (parts[1] if len(parts) > 1 else "") and reg in parts[1]):
                print("  %s %08x %s %s  redefines %s" % (why, va, mn, ops, reg))
                return
            elif mem_dst:
                kind = "SPILL"
            elif len(parts) > 1 and "[" in parts[1] and reg in parts[1]:
                kind = "LOAD-THROUGH"
            else:
                kind = "USE"
            print("  %s %08x %s %s  %s" % (why, va, mn, ops, kind))
            if mn in ("call", "ret", "jmp"):
                print("  %s %08x ends the straight line" % (why, va))
                return
        return

    for va, (mn, ops) in ins:
        if mn == "lea" and ("0x73c72" in ops):
            reg = ops.split(",")[0].strip()
            print("LEA %08x %s %s defines %s" % (va, mn, ops, reg))
            follow(va, reg, "use")
    slots = ("[ebp-0x20]", "[ebp-0x18]")
    for slot in slots:
        print("SLOT %s" % slot)
        for va, (mn, ops) in ins:
            if slot in ops:
                parts = [x.strip() for x in ops.split(",")]
                role = "WRITE" if slot in parts[0] else "READ"
                print("  %08x %s %s  %s" % (va, mn, ops, role))
                if role == "READ" and mn == "mov":
                    follow(va, parts[0], "load")
    for va, (mn, ops) in ins:
        if mn == "lea" and "[ebp-" in ops:
            print("FRAME-ADDRESS %08x %s %s" % (va, mn, ops))
        if mn.startswith("j"):
            t = W.branch_target(ops)
            if t is not None and t <= va:
                print("BACKWARD %08x %s %s" % (va, mn, ops))
    print("MASKS stores-through=%d" % stores)
    return 0


# ----------------------------------------------------------------------------------------------- route reads
SITE_ROOTS = (   # (label, entry, rows)
    ("MissileOwnerUModEvent's mod-29 function", 0x005A3610, "m21"),
    ("SkillDo30Curse", 0x005C37C0, "m69"),
)


def cmd_sites(depth=4):
    import sweep_s4b as W
    import sweep2_s7e_routes as R
    A = W.asm()
    print("S2AE3-SITES depth=%d roots=%d" % (depth, len(SITE_ROOTS)))
    memo = {}
    for label, root, rows in SITE_ROOTS:
        vas, calls, icalls = W.body(A, root)[:3]
        print("ROOT %s %08X (%s): direct=%d indirect=%d" % (label, root, rows, len(calls), len(icalls)))
        for site, t in sorted(calls):
            if t in R.POOL:
                print("  SITE %08X -> %08X %s" % (site, t, R.POOL[t]))
                continue
            if t in R.FATAL:
                print("  SITE %08X -> %08X fatal" % (site, t))
                continue
            if t not in memo:
                memo[t] = R.walk(A, t, depth - 1)
            seen, pool, imports, ic, fatal = memo[t]
            first = sorted(pool.items(), key=lambda kv: kv[1][0])
            print("  SITE %08X -> %08X functions=%d pool=%d imports=%d indirect=%d%s" % (
                site, t, len(seen), len(pool), len(imports), ic,
                (" first %s at %08X via %s" % (R.POOL[first[0][0]], first[0][1][0], first[0][1][1])) if first else ""))
        for va in icalls:
            print("  ICALL %08X %s" % (va, A.at(va)[1]))
    return 0


# ----------------------------------------------------------------------------------------------- reach
class RE(p1.E):
    def __init__(self):
        super().__init__(None)
        self.seen = []

    def t(self, name, cond):
        r = super().t(name, cond)
        self.seen.append((name, r))
        return r

    def c(self, name, a, op, b):
        r = super().c(name, a, op, b)
        self.seen.append((name, r))
        return r


def cmd_reach(limit=None):
    cases = B.build(limit)
    outs, reach = {}, {}
    for c in cases:
        e = RE()
        w = MODEL[c.fam](e, c.a)
        k = "%s:%s" % (w[0], ("%x" % w[1]) if w[0] == "obs" else (w[1] if c.fam != "uev" else ""))
        outs.setdefault(c.fam, {}).setdefault(k, 0)
        outs[c.fam][k] += 1
        for name, r in e.seen:
            d = reach.setdefault(c.fam, {}).setdefault(name, [0, 0])
            d[0 if r else 1] += 1
    for f in FAMILIES:
        o = outs.get(f, {})
        if f == "cdo":
            o = {("obs" if k.startswith("obs") else k if k in ("ret:0",) else "ret:n>0xbe"): 0 for k in o} | {}
            agg = {}
            for k, v in outs.get(f, {}).items():
                kk = "obs" if k.startswith("obs") else ("ret:0" if k == "ret:0" else "ret:n")
                agg[kk] = agg.get(kk, 0) + v
            o = agg
        print("OUTCOMES %s %s" % (f, " ".join("%s=%d" % kv for kv in sorted(o.items()))))
        for name, (tt, ff) in sorted(reach.get(f, {}).items()):
            print("REACH %s %s true=%d false=%d" % (f, name, tt, ff))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("cases", "check", "reach", "static", "masks", "sites", "manifest"))
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    o = ap.parse_args(argv)
    install()
    if o.cmd == "cases":
        B.cmd_cases(o.dir, o.limit)
        return 0
    if o.cmd == "check":
        return B.cmd_check(o.dir, o.limit)
    if o.cmd == "reach":
        return cmd_reach(o.limit)
    if o.cmd == "static":
        return cmd_static()
    if o.cmd == "masks":
        return cmd_masks()
    if o.cmd == "sites":
        return cmd_sites()
    B.cmd_manifest(o.dir, o.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

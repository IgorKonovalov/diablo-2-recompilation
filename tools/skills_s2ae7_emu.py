#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S2ae part 7 (`lane/n66sa`): SKILLS_ItemChargesOk, SkillWeaponWear and stat-event handlers
26 and 27 under Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java, compared with
the models below; plus `static`, the objdump listing of every function the cases run.

    python3 -I tools/skills_s2ae7_emu.py cases [--dir D] [--limit N]   write D/s2ae.cases, D/s2ae.mem and the tables
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s2ae.cases D/s2ae.mem > D/s2ae.out
    python3 -I tools/skills_s2ae7_emu.py check [--dir D] [--limit N]   compare, account for traced reads, controls
    python3 -I tools/skills_s2ae7_emu.py reach [--limit N]             model outcomes and deciding tests per family
    python3 -I tools/skills_s2ae7_emu.py static                        objdump of the functions run
    python3 -I tools/skills_s2ae7_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66sa/s2ae/run7. Parts 1-6 (tools/skills_s2ae_emu.py, skills_s2ae2..6_emu.py) and their
run/ to run6/ are unchanged; this tool reuses part 1's check machinery (cmd_cases, cmd_check, cmd_manifest), batch
S5e part 1's unit builder (tools/combat_s5e_emu.py put_unit), part 5's GameFindUnit/MonsterOwner and stat-list models
and part 6's unit, owner-link and seed helpers, in its module state only. Every draw comes from
random.Random("n66sa-s2ae7-<family>"); the declared tables from random.Random("n66sa-s2ae7-tables").

Every callee runs whole on the declared image (ruling R2: no declared return) unless named as an observed boundary
(ADR-0021): the case ends at that call, the registers the code sets for it, its stack arguments and the declared
dumps are compared, and the claim ends there. The allocator entries and the fatal path are guards.

Families (rows: d = skills/dispatch):
  chg   0x00647840 SKILLS_ItemChargesOk (EAX unit, EBX skill entry), whole: SKILLS_GetSkillLevel 0x006442A0 (flag 0,
        so no bonus call) with sub_00611830_ExpMaxLevel (its table pointer 0x0096C8A8 declared), INV_GetFirstItem
        0x0063B2C0, sub_0063DFD0_InvNodeItem, INV_GetNextItem 0x0063DFA0, STATS_GetUnitStat (stat 204 at layer
        skill * 64 + (level & 0x3F)).                                                                        d40
  wear  0x005DAA40 sub_005DAA40_SkillWeaponWear (EBX item, ESI unit; stack game, chance, amount; ret 0xC) to its
        three calls PLAYER_UseAmmo 0x0056C3F0, sub_00627260_UnitSetStat, sub_0055F850_ItemBreak (observed):
        ITEMS_UnitIsType 0x00629BB0 (type 45; the ItemTypes equivalence words at DataTables +0xBFC/+0xC00/+0xC04
        declared), ITEMS_GetRecord 0x006335F0 (count and records 0x0096CA58/0x0096CA5C declared), 0x00628700,
        sub_006289F0_ItemBaseStackable, sub_00629930_ItemHasDurability with 0x00625E00 (stat 73's base array and
        its value), STATS_GetUnitStat (stats 70, 72, 152), the inline seed step.                             d156, d181
  h26   0x005C6690 sub_005C6690_StatEv26BloodGolemDamaged to UnitSetStat 0x00627260 (observed, from 0x005C6731):
        sub_0058F0D0_MonsterOwner with GameFindUnit, sub_005541B0_UnitIsDead, STATS_GetUnitStat (stat 6),
        MONSTATS_GetRecord 0x00451F80 (+0x170), sub_004E6C70_SkillGetParam5 (Skills +0x158), sub_00483360_MulDiv. d130
  h27   0x005C6760 sub_005C6760_StatEv27ClayGolemSlow to STATE_ApplyTimed 0x0056E970 (observed, from 0x005C6819; its
        parameter block on the stack is dumped): UnitGetStat (stat 150), sub_005A0180_MonTypeFlag (mask 0xC). d131

Domain (each outside it reads an undeclared address or reaches the fatal path, which the run would not account):
chg's entry has a skill record; wear's item class is below the items count (ITEMS_UnitIsType reads its record
whatever the unit type) and its record's first type is a declared ItemTypes row (0x00628700's type is not range
tested); h26's MonsterOwner chains as part 6's; the handlers' units are non-null where UnitGetStat reads them.

Controls as parts 1-6: every named test reversed alone, every ordered compare's strictness switched alone; `sep`
counts the cases a control changes, `passed` those the emulator still matches (must be 0); `spec_*` controls are
readings the spec states or rules out. Stdlib only, plus objdump for `static`.
"""
import argparse
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import combat_s5e_emu as p1  # noqa: E402
import skills_s2ae_emu as B  # noqa: E402
import skills_s2ae3_emu as P3  # noqa: E402
import skills_s2ae5_emu as P5  # noqa: E402
import skills_s2ae6_emu as P6  # noqa: E402
from combat_s5e_emu import u32, s32, le32, tdiv, G_DT, DT, FATAL, ALLOC, ISC, ISC_N, NSTATES  # noqa: E402

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66sa", "s2ae", "run7")
FNS = {"chg": 0x00647840, "wear": 0x005DAA40, "h26": 0x005C6690, "h27": 0x005C6760}
FAMILIES = ("chg", "wear", "h26", "h27")
NCASES = {"chg": 3000, "wear": 4000, "h26": 4000, "h27": 2500}
POP = {"chg": 0, "wear": 0xC, "h26": 0x14, "h27": 0x14}
p1.FNS.update(FNS)

OBS_AMMO, OBS_SETSTAT, OBS_BREAK, OBS_STATE = 0x0056C3F0, 0x00627260, 0x0055F850, 0x0056E970
OBSERVES = (OBS_AMMO, OBS_SETSTAT, OBS_BREAK, OBS_STATE)
NARGS = {OBS_AMMO: 0, OBS_SETSTAT: 4, OBS_BREAK: 1, OBS_STATE: 0}
SITES_OBS = {("wear", OBS_AMMO): 0x005DAAAD, ("wear", OBS_SETSTAT): 0x005DAB0A, ("wear", OBS_BREAK): 0x005DAB3B,
             ("h26", OBS_SETSTAT): 0x005C6736, ("h27", OBS_STATE): 0x005C681E}
STACK = P6.STACK
BLK = STACK - 0x28                    # h27: the parameter block at EBP - 0x24 (EBP = STACK - 4)
GAME = P6.GAME
U, O, X = P6.U, P6.O, P6.X
UPKT = 0x20008000
INV, ENT, SKREC, XP = 0x20009000, 0x20009100, 0x20009200, 0x20009300
ITB = 0x20018000                      # chg's item chain: up to four items, 0x1000 apart (above part 5's game image)
G_XP, G_ITN, G_ITR = 0x0096C8A8, 0x0096CA58, 0x0096CA5C
MS, MS_N, MS_SZ = P6.MS, P6.MS_N, P6.MS_SZ
SK, SK_N, SK_SZ = P6.SK, P6.SK_N, P6.SK_SZ
IT, IT_N, IT_SZ = 0x21500000, 64, 0x1A8
EQ, NTYPES, EQ_STRIDE = 0x21600000, 64, 2
T45_WORD, T45_BIT = 45 >> 5, 1 << (45 & 31)
SL_OFF, LIVE_OFF, BASE_OFF, MD_OFF = 0x200, 0x300, 0x400, 0x780
INV_MAGIC = 0x01020304
A_LCG = 0x6AC690C5

TABLES = None


def tables():
    """The declared MonStats (+0x170 the skill), Skills (+0x158 param 5), item records (+0x112, +0x113, +0x11E,
    +0x120, +0x132) and ItemTypes equivalence words."""
    global TABLES
    if TABLES is None:
        r = random.Random("n66sa-s2ae7-tables")
        ms = bytearray(r.getrandbits(8) for _ in range(MS_N * MS_SZ))
        for i in range(MS_N):
            sk = r.choice([r.randrange(SK_N)] * 7 + [-1, SK_N, SK_N + 3, 0x7FFF, -0x8000])
            struct.pack_into("<h", ms, i * MS_SZ + 0x170, sk)
        sk = bytearray(r.getrandbits(8) for _ in range(SK_N * SK_SZ))
        for i in range(SK_N):
            v = r.choice([0, 100, r.randint(1, 99), r.randint(101, 400), r.randint(-50, -1), r.getrandbits(32)])
            struct.pack_into("<I", sk, i * SK_SZ + 0x158, u32(v))
        it = bytearray(r.getrandbits(8) for _ in range(IT_N * IT_SZ))
        for i in range(IT_N):
            o = i * IT_SZ
            struct.pack_into("<h", it, o + 0x11E, r.randrange(NTYPES))
            struct.pack_into("<h", it, o + 0x120, r.choice([0, 0, -1, r.randrange(1, NTYPES), NTYPES, 0x7FFF]))
            it[o + 0x132] = r.choice([0, 0, 1, r.getrandbits(8)])
            it[o + 0x113] = r.choice([0, 0, 0, 1, r.getrandbits(8)])
            it[o + 0x112] = r.choice([0, 1, r.getrandbits(8), r.getrandbits(8)])
        eq = bytearray(r.getrandbits(8) for _ in range(NTYPES * EQ_STRIDE * 4))
        for t in range(NTYPES):
            w = struct.unpack_from("<I", eq, (t * EQ_STRIDE + T45_WORD) * 4)[0]
            w = (w | T45_BIT) if r.random() < 0.45 else (w & ~T45_BIT)
            struct.pack_into("<I", eq, (t * EQ_STRIDE + T45_WORD) * 4, w & 0xFFFFFFFF)
        TABLES = (ms, sk, it, eq)
    return TABLES


class Case(p1.Case):
    pass


Mem = P6.Mem
rbytes, gid, ret = P6.rbytes, P6.gid, P6.ret
get_stat, stats_get, step, mon_type_flag = P6.get_stat, P6.stats_get, P6.step, P6.mon_type_flag


def finish(c, dumps):
    P6.finish(c, dumps)
    c.a["regs"] = dict(c.regs)
    return c


def sx16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def M32(c, a):
    return int.from_bytes(bytes(c.w[a + i] for i in range(4)), "little")


def obs(pc, regs, args, M, dumps):
    return ("obs", pc, None if regs is None else tuple(u32(x) for x in regs), tuple(u32(x) for x in args),
            P5.P4.dumped(M, dumps))


def put_list(c, rnd, base, live, basekeys=None, flag=None):
    """A stat list at base + SL_OFF hung on base + 0x5C: the live array at +0x48 when +0x10 bit 31 is set (else
    +0x24), the base array at +0x24 (the live one itself when the bit is clear). Keys stat << 16 | layer."""
    sl = base + SL_OFF
    c.put(base + 0x5C, le32(sl))
    c.put(sl, rbytes(rnd, 0x60))
    flag = rnd.random() < 0.8 if flag is None else flag
    c.put(sl + 0x10, le32((0x80000000 if flag else 0) | rnd.getrandbits(31)))
    c.put(sl + 0x44, le32(0))

    def arr(at, keys):
        ks = sorted(keys)
        for i, k in enumerate(ks):
            c.put(at + 8 * i, le32(k) + le32(u32(keys[k])))
        return len(ks)
    if flag:
        n = arr(base + LIVE_OFF, live)
        c.put(sl + 0x48, le32(base + LIVE_OFF) + struct.pack("<H", n) + bytes(2))
        n = arr(base + BASE_OFF, basekeys or {})
        c.put(sl + 0x24, le32(base + BASE_OFF) + struct.pack("<H", n) + bytes(2))
    else:
        keys = dict(basekeys or {})
        keys.update(live)
        n = arr(base + LIVE_OFF, keys)
        c.put(sl + 0x24, le32(base + LIVE_OFF) + struct.pack("<H", n) + bytes(2))
        c.put(sl + 0x48, le32(base + BASE_OFF) + struct.pack("<H", 0) + bytes(2))


def search(M, desc, key):
    """0x00624B90 on an array descriptor (pointer, signed word count): signed binary search, the value or None."""
    arr, n = M.d(desc), P3.sx16(M.h(desc + 4))
    lo, hi = 0, n
    while lo < hi:
        mid = lo + tdiv(hi - lo, 2)
        k = s32(M.d(arr + 8 * mid))
        if key > k:
            lo = mid + 1
        elif key < k:
            hi = mid
        else:
            return s32(M.d(arr + 8 * mid + 4))
    return None


# ----------------------------------------------------------------------------------------------- chg
def skill_level(e, M, ent):
    """SKILLS_GetSkillLevel(unit, entry, 0): max(entry +0x28, 0), capped at ExpMaxLevel(0) (signed)."""
    lvl = s32(M.d(ent + 0x28))
    if not e.c("lvl_gt0", lvl, ">", 0):
        lvl = 0
    mx = s32(M.d(XP))
    return lvl if e.c("lvl_lt_max", lvl, "<", mx) else mx


def gen_chg(rnd):
    c = Case("chg")
    c.put(U, rbytes(rnd, 0x100))
    used = set()
    c.put(SKREC, rbytes(rnd, 0x20))
    sid = rnd.choice([rnd.randrange(400)] * 6 + [0, 1023, rnd.randrange(1024)])
    c.put(SKREC, struct.pack("<h", sid))
    base = rnd.choice([0, 1, 20, 63, 64, 65, 99, 100, 127, -1, rnd.randint(1, 60), rnd.getrandbits(32)])
    xp = rnd.choice([99, 99, 20, 64, 1, 0, 70])
    c.put(XP, le32(xp))
    lvl = max(s32(base), 0)
    lvl = lvl if lvl < xp else xp
    item_guid = rnd.choice([gid(rnd, used)] * 9 + [0xFFFFFFFF])
    c.put(ENT, rbytes(rnd, 0x40))
    c.put(ENT, le32(SKREC))
    c.put(ENT + 0x28, le32(u32(base)))
    c.put(ENT + 0x34, le32(item_guid))
    c.put(U + 0x60, le32(INV if rnd.random() < 0.94 else 0))
    c.put(INV, rbytes(rnd, 0x20))
    c.put(INV, le32(INV_MAGIC if rnd.random() < 0.93 else rnd.choice([0, INV_MAGIC + 1, rnd.getrandbits(32)])))
    n = rnd.choice([0, 1, 2, 3, 4, 4])
    items = [ITB + 0x1000 * k for k in range(n)]
    match = rnd.choice([None] + list(range(n)) * 3) if n else None
    layer = (lvl & 0x3F) + (sid << 6)
    for k, it in enumerate(items):
        c.put(it, rbytes(rnd, 0x100))
        c.put(it, le32(4 if rnd.random() < 0.93 else rnd.choice([0, 1, 3, 5])))
        c.put(it + 0xC, le32(item_guid if k == match else gid(rnd, used)))
        md = it + MD_OFF
        c.put(it + 0x14, le32(md))
        c.put(md, rbytes(rnd, 0x70))
        c.put(md + 0x64, le32(items[k + 1] if k + 1 < n else 0))
        keys = {}
        v = rnd.choice([None, 0, 1, 0x100, 0x1FF, 0x80, 0xFF, rnd.randint(1, 20), rnd.getrandbits(32), -1])
        if v is not None:
            keys[(204 << 16) | (layer & 0xFFFF)] = v
        for dl in rnd.sample([-1, 1, 64, -64, 0x40 * 7], rnd.randrange(3)):
            keys.setdefault((204 << 16) | ((layer + dl) & 0xFFFF), rnd.getrandbits(32))
        if rnd.random() < 0.3:
            keys.setdefault(rnd.randrange(1, ISC_N) << 16, rnd.getrandbits(32))
        if rnd.random() < 0.05:
            c.put(it + 0x5C, le32(0))
        else:
            put_list(c, rnd, it, keys)
    c.put(INV + 0xC, le32(items[0] if items else 0))
    c.regs = {"EAX": U, "EBX": ENT}
    pick = rnd.random()
    if pick < 0.03:
        c.regs["EAX"] = 0
    elif pick < 0.06:
        c.regs["EBX"] = 0
    c.ecx, c.edx = rnd.getrandbits(32), rnd.getrandbits(32)
    c.args = []
    return finish(c, [])


def m_chg(e, a):
    M = Mem(a["w"])
    u, ent = a["regs"]["EAX"], a["regs"]["EBX"]
    if not e.t("u_nz", u != 0) or not e.t("ent_nz", ent != 0):
        return ("ret", 0, ())
    inv = M.d(u + 0x60)
    if not e.t("inv_nz", inv != 0):
        return ("ret", 1, ())
    g = M.d(ent + 0x34)
    if not e.t("item_skill", g != 0xFFFFFFFF):
        return ("ret", 1, ())
    sid = sx16(M.h(M.d(ent)))
    lvl = skill_level(e, M, ent)
    e.names.add("spec_no_mask")
    layer = u32((lvl if e.flip == "spec_no_mask" else lvl & 0x3F) + (sid << 6))
    node = M.d(inv + 0xC) if e.t("inv_magic", M.d(inv) == INV_MAGIC) else 0
    for _ in range(8):
        if not e.t("node_nz", node != 0):
            return ("ret", 1, ())
        it = node if e.t("node_item", M.d(node) == 4) else 0
        if it and e.t("guid_eq", M.d(it + 0xC) == g):
            v = stats_get(M, it, 204, layer)
            e.names.add("spec_full_value")
            if e.flip == "spec_full_value":
                return ("ret", 1 if s32(v) > 0 else 0, ())
            return ("ret", 1 if e.t("low_nz", v & 0xFF) else 0, ())
        # INV_GetNextItem on the node: type 4 and item data, else 0
        if M.d(node) != 4 or M.d(node + 0x14) == 0:
            node = 0
        else:
            node = M.d(M.d(node + 0x14) + 0x64)
    raise IndexError("item chain")


# ----------------------------------------------------------------------------------------------- wear
def rec_off(M, it):
    """ITEMS_GetRecord by the item's class (+4), unsigned below the count."""
    cls = M.d(it + 4)
    if cls >= IT_N:
        raise IndexError("item class outside the domain")
    return cls * IT_SZ


def eq_has45(t):
    return struct.unpack_from("<I", tables()[3], (t * EQ_STRIDE + T45_WORD) * 4)[0] & T45_BIT


def is_type45(e, M, it):
    """ITEMS_UnitIsType(item, 45): the record's type, then (when > 0 and below the count) its second type."""
    if not e.t("it_nz", it != 0):
        return 0
    ro = rec_off(M, it)
    t = struct.unpack_from("<h", tables()[2], ro + 0x11E)[0]
    if e.t("eq1", eq_has45(t)):
        return 1
    t2 = struct.unpack_from("<h", tables()[2], ro + 0x120)[0]
    if not e.c("t2_gt0", t2, ">", 0) or not e.c("t2_lt_n", t2, "<", NTYPES):
        return 0
    return 1 if e.t("eq2", eq_has45(t2)) else 0


def stackable(M, it):
    """sub_006289F0_ItemBaseStackable: a type-4 unit's record byte +0x132."""
    if M.d(it) != 4:
        return 0
    return tables()[2][rec_off(M, it) + 0x132]


def base73(e, M, it):
    """0x00625E00: stat 73's base value (the +0x24 array); when non-zero, its value (0x00624F60)."""
    sl = M.d(it + 0x5C)
    if sl == 0:
        return 0
    b = search(M, sl + 0x24, 73 << 16)
    if not e.t("b73_nz", b):
        return 0
    return P5.stat_on(M, sl, 73, 0)


def has_dur(e, M, it):
    """sub_00629930_ItemHasDurability."""
    if not e.t("d_item", M.d(it) == 4):
        return 0
    ro = rec_off(M, it)
    if not e.t("nodur0", tables()[2][ro + 0x113] == 0) or not e.t("dur_gt0", tables()[2][ro + 0x112] > 0):
        return 0
    if not e.t("max_nz", base73(e, M, it) != 0):
        return 0
    return 1 if e.c("indes_le0", s32(stats_get(M, it, 152)), "<=", 0) else 0


def pick_class(rnd):
    """Half the cases on a type-45, non-stackable record with durability, a fifth on a type-45 stackable one."""
    it = tables()[2]
    dur = [i for i in range(IT_N) if eq_has45(struct.unpack_from("<h", it, i * IT_SZ + 0x11E)[0])
           and it[i * IT_SZ + 0x132] == 0 and it[i * IT_SZ + 0x113] == 0 and it[i * IT_SZ + 0x112] > 0]
    stk = [i for i in range(IT_N) if eq_has45(struct.unpack_from("<h", it, i * IT_SZ + 0x11E)[0])
           and it[i * IT_SZ + 0x132] != 0]
    k = rnd.random()
    if k < 0.5 and dur:
        return rnd.choice(dur)
    if k < 0.7 and stk:
        return rnd.choice(stk)
    return rnd.randrange(IT_N)


def gen_wear(rnd):
    c = Case("wear")
    it = X
    c.put(U, rbytes(rnd, 0x100))
    c.put(it, rbytes(rnd, 0x100))
    c.put(it, le32(4 if rnd.random() < 0.9 else rnd.choice([0, 1, 3])))
    c.put(it + 4, le32(pick_class(rnd)))
    live = {}
    q = rnd.choice([None, 0, 1, rnd.randint(2, 500), -1, rnd.getrandbits(32)])
    dur = rnd.choice([None, 0, 1, rnd.randint(1, 250), rnd.randint(1, 250), 0x7FFFFFFF, 0x80000000, -3,
                      rnd.getrandbits(32)])
    amount = rnd.choice([0, 1, 1, rnd.randint(1, 10), rnd.randint(1, 300), -1, 0x80000000, 0x7FFFFFFF,
                         rnd.getrandbits(32)])
    if dur is not None and rnd.random() < 0.15:
        amount = dur
    for s, v in ((70, q), (72, dur), (152, rnd.choice([None, None, None, None, 0, 1, -1]))):
        if v is not None:
            live[s << 16] = v
    mx = rnd.choice([None, 0, rnd.randint(1, 250), rnd.randint(1, 250), rnd.randint(1, 250), rnd.getrandbits(32)])
    if mx is not None:
        live[73 << 16] = mx
    bk = {}
    if rnd.random() < 0.85:
        bk[73 << 16] = rnd.choice([0, rnd.randint(1, 250), rnd.randint(1, 250), rnd.getrandbits(32)])
    if rnd.random() < 0.2:
        bk[rnd.randrange(1, 70) << 16] = rnd.getrandbits(32)
    if rnd.random() < 0.04:
        c.put(it + 0x5C, le32(0))
    else:
        put_list(c, rnd, it, live, bk)
    chance = rnd.choice([0, 1, 50, 99, 100, 101, -1, rnd.getrandbits(32)] + [rnd.randint(0, 100)] * 6)
    if rnd.random() < 0.12:
        lo = (M32(c, U + 0x20) * A_LCG + M32(c, U + 0x24)) & 0xFFFFFFFF
        chance = lo % 100     # the roll at the bound (the strictness of both chance compares)
    c.regs = {"EBX": it, "ESI": U}
    if rnd.random() < 0.03:
        c.regs["EBX"] = 0
    c.ecx, c.edx = rnd.getrandbits(32), rnd.getrandbits(32)
    c.args = [rnd.getrandbits(32), u32(chance), u32(amount)]
    return finish(c, [(U + 0x20, 8)])


def m_wear(e, a):
    M = Mem(a["w"])
    it, u = a["regs"]["EBX"], a["regs"]["ESI"]
    game, chance, amount = a["args"]
    dumps = a["dumps"]

    def done():
        return ("ret", None, P5.P4.dumped(M, dumps))
    if not e.t("is45", is_type45(e, M, it)):
        return done()
    if e.t("stack", stackable(M, it)):
        if not e.c("q_gt0", s32(stats_get(M, it, 70)), ">", 0):
            return done()
        r = step(M, u) % 100
        if not e.c("ra_lt_ch", r, "<", s32(chance)):
            return done()
        return obs(OBS_AMMO, (game, u), (), M, dumps)
    if not e.t("hasdur", has_dur(e, M, it)):
        return done()
    r = step(M, u) % 100
    if not e.c("rd_lt_ch", r, "<", s32(chance)):
        return done()
    dur = stats_get(M, it, 72)
    d = u32(dur - amount)
    e.names.add("spec_math_le0")
    if e.flip == "spec_math_le0":
        brk = s32(dur) - s32(amount) <= 0
    else:
        brk = e.t("d_sign", d >> 31) or e.t("d_zero", d == 0)
    if brk:
        return obs(OBS_BREAK, (game, u), (it,), M, dumps)
    return obs(OBS_SETSTAT, None, (it, 0x48, d, 0), M, dumps)


# ----------------------------------------------------------------------------------------------- h26, h27
def is_dead(e, M, p):
    """sub_005541B0_UnitIsDead: +0xC6 bit 0, else a player in mode 0 or 17, a monster in mode 0 or 12; other types 1."""
    if e.t("dead_bit", M.b(p + 0xC6) & 1):
        return 1
    t, m = M.d(p), M.d(p + 0x10)
    if t == 0:
        return 1 if e.t("dead_pmode", m in (0, 0x11)) else 0
    if t == 1:
        return 1 if e.t("dead_mmode", m in (0, 0xC)) else 0
    return 1


def gen_h26(rnd):
    c = Case("h26")
    used = set()
    cls = rnd.randrange(MS_N) if rnd.random() < 0.95 else rnd.choice([-1, MS_N, 0x7FFFFFFF])
    shape = rnd.choice(["ok"] * 7 + ["miss", "nogame", "norec"])
    P6.unit(c, rnd, U, 1 if rnd.random() < 0.92 else rnd.choice([0, 3]), cls=cls)
    life = rnd.choice([None, 0, 255, 256, 257, -256, 0x7FFFFF00, 0x80000000] + [rnd.randint(1, 3000) << 8,
                                                                               rnd.randint(0, 3000 << 8)] * 4)
    st = {6: life} if life is not None else {}
    P6.unit(c, rnd, X, rnd.choice([0] * 6 + [1, 1, 2, 3]), stats=st)
    c.put(X + 0xC4, le32(rnd.getrandbits(32) & ~0x10000 if rnd.random() < 0.85 else rnd.getrandbits(32)))
    c.put(X + 0x10, le32(rnd.choice([rnd.randrange(20)] * 6 + [0, 0xC, 0x11])))
    P6.place(c, X, used, rnd)
    if M32(c, U) == 1:
        P6.link(c, U, X, rnd, used, shape)
    c.put(U + 0xC, le32(gid(rnd, used)))
    c.put(UPKT, rbytes(rnd, 0x70))
    dmg = rnd.choice([0, -1, rnd.randint(1, 1000) << 8, rnd.randint(1, 255), rnd.getrandbits(32),
                      rnd.randint(0x100000, 0x7FFFFFFF), rnd.randint(1, 0x100000)])
    c.put(UPKT + 0x4C, le32(u32(dmg)))
    P6.handler_args(c, rnd, U, O, rnd.getrandbits(32))
    c.args[1] = rnd.choice([0, O, rnd.getrandbits(32)])
    pick = rnd.random()
    if pick < 0.03:
        c.args[0] = 0
    elif pick < 0.06:
        c.args[2] = 0
    return finish(c, [(UPKT + 0x4C, 4)])


def m_h26(e, a):
    M = Mem(a["w"])
    u, _, pkt = a["args"][:3]
    dumps = a["dumps"]
    if not e.t("u_nz", u != 0) or not e.t("pkt_nz", pkt != 0) or not e.t("u_mon", M.d(u) == 1):
        return ret(0, M, dumps)
    d = s32(M.d(pkt + 0x4C))
    if not e.c("dmg_gt0", d, ">", 0):
        return ret(0, M, dumps)
    p = P5.mon_owner(e, M, u)
    if not e.t("p_found", p != 0) or e.t("p_dead", is_dead(e, M, p)):
        return ret(0, M, dumps)
    life = s32(stats_get(M, p, 6))
    if not e.c("life_ge256", life, ">=", 0x100):
        return ret(0, M, dumps)
    cls = s32(M.d(u + 4))
    if not e.t("ms_rec", 0 <= cls < MS_N):
        return ret(0, M, dumps)
    sk = struct.unpack_from("<h", tables()[0], cls * MS_SZ + 0x170)[0]
    if not e.t("sk_ge0", sk >= 0):
        return ret(0, M, dumps)
    par = struct.unpack_from("<I", tables()[1], sk * SK_SZ + 0x158)[0] if e.t("sk_rec", sk < SK_N) else 0
    e.names.add("spec_pct")
    loss = s32(tdiv(d * s32(par), 100)) if e.flip == "spec_pct" else p1.muldiv(d, par, 100)
    nv = s32(life - loss)
    e.names.add("spec_no_floor")
    if e.c("nv_lt256", nv, "<", 0x100) and e.flip != "spec_no_floor":
        nv = 0x100
    return obs(OBS_SETSTAT, None, (p, 6, nv, 0), M, dumps)


def gen_h27(rnd):
    c = Case("h27")
    v = rnd.choice([None, 0, rnd.randint(1, 49), 49, 50, 51, rnd.randint(51, 89), 89, 90, 91, rnd.randint(91, 300),
                    rnd.randint(-60, -1), rnd.getrandbits(32), 0x80000000])
    st = {150: v} if v is not None else {}
    P6.unit(c, rnd, U, rnd.choice([0, 1, 1, 3]), stats=st)
    P6.unit(c, rnd, O, rnd.choice([0, 0, 1, 1, 1, 2, 3, 4]),
            md_flags=rnd.choice([0, 0, 4, 8, 0xC, 0x10, 0x3, rnd.getrandbits(16), -1]))
    P6.handler_args(c, rnd, U, O, rnd.getrandbits(32))
    pick = rnd.random()
    if pick < 0.03:
        c.args[0] = 0
    elif pick < 0.06:
        c.args[1] = 0
    return finish(c, [(BLK, 0x24)])


def m_h27(e, a):
    M = Mem(a["w"])
    u, o = a["args"][:2]
    dumps = a["dumps"]
    if not e.t("u_nz", u != 0) or not e.t("o_nz", o != 0):
        return ("ret", 0, None)
    v = s32(get_stat(M, u, 150, 0))
    if not e.t("v_nz", v != 0):
        return ("ret", 0, None)
    ot = M.d(o)
    e.names.add("spec_cap_swap")
    if e.t("o_player", ot == 0):
        cap = 50
    elif e.t("o_mon", ot == 1):
        cap = 50 if e.t("mt_c", mon_type_flag(M, o, 0xC)) else 90
    else:
        return ("ret", 0, None)
    if e.flip == "spec_cap_swap":
        cap = 90 if cap == 50 else 50
    if e.c("v_ge_cap", v, ">=", cap):
        v = cap
    blk = struct.pack("<9I", u, o, 0, 1, 0x2EE, 0x43, u32(-v), 0x18, 0)
    M.w.update({BLK + i: b for i, b in enumerate(blk)})
    return obs(OBS_STATE, (BLK,), (), M, dumps)


GEN = {"chg": gen_chg, "wear": gen_wear, "h26": gen_h26, "h27": gen_h27}
MODEL = {"chg": m_chg, "wear": m_wear, "h26": m_h26, "h27": m_h27}


class Sites(dict):
    def __missing__(self, key):
        return SITES_OBS.get(key, 0)


SITE = Sites()


# ----------------------------------------------------------------------------------------------- spec, check
def write_spec(d):
    ms, sk, it, eq = tables()
    for name, data in (("monstats.bin", ms), ("skills.bin", sk), ("items.bin", it), ("itemtypes-eq.bin", eq),
                       ("isc.bin", bytes(ISC_N * p1.ISC_SZ))):
        with open(os.path.join(d, name), "wb") as f:
            f.write(bytes(data))
    dt = bytearray(0x1000)
    for off, v in ((0xC4, NSTATES), (0xA78, MS), (0xA80, MS_N), (0xB98, SK), (0xBA0, SK_N), (0xBCC, ISC),
                   (0xBD4, ISC_N), (0xBFC, NTYPES), (0xC00, EQ_STRIDE), (0xC04, EQ)):
        struct.pack_into("<I", dt, off, v)
    with open(os.path.join(d, "dt.bin"), "wb") as f:
        f.write(bytes(dt))
    with open(os.path.join(d, "game.bin"), "wb") as f:
        f.write(bytes(P6.GAME_SZ))
    lines = ["# plan 0066 S2ae part 7 (tools/skills_s2ae7_emu.py): declared tables",
             "dword %08x %08x" % (G_DT, DT),
             "dword %08x %08x" % (G_XP, XP),
             "dword %08x %08x" % (G_ITN, IT_N),
             "dword %08x %08x" % (G_ITR, IT),
             "load %08x %s" % (DT, os.path.join(d, "dt.bin")),
             "load %08x %s" % (MS, os.path.join(d, "monstats.bin")),
             "load %08x %s" % (SK, os.path.join(d, "skills.bin")),
             "load %08x %s" % (IT, os.path.join(d, "items.bin")),
             "load %08x %s" % (EQ, os.path.join(d, "itemtypes-eq.bin")),
             "load %08x %s" % (ISC, os.path.join(d, "isc.bin")),
             "load %08x %s" % (GAME, os.path.join(d, "game.bin"))]
    lines += ["guard %08x" % x for x in FATAL + ALLOC]
    lines += ["observe %08x" % x for x in OBSERVES]
    with open(os.path.join(d, "s2ae.mem"), "w") as f:
        f.write("\n".join(lines) + "\n")


def observed(fam, k):
    if "stop" in k:
        return ("stop", k["stop"], None), None
    dumps = k["dumps"]
    dt = tuple(dumps[va] for va in sorted(dumps))
    if "obs" in k:
        st = k["stack"]
        rt = struct.unpack_from("<I", st, 0)[0]
        n = NARGS[k["obs"]]
        ecx, edx = int(k["regs"]["ecx"], 16), int(k["regs"]["edx"], 16)
        regs = (ecx,) if k["obs"] == OBS_STATE else (ecx, edx)
        return ("obs", k["obs"], regs, struct.unpack_from("<%dI" % n, st, 4), dt), rt
    if k["pop"] != POP[fam]:
        return ("pop", k["pop"]), None
    return ("ret", k["eax"], dt), None


def norm(fam, want):
    return want


B_same = B.same


def same(want, got):
    if want[0] == "ret" and want[2] is None and got[0] == "ret":
        return want[1] == got[1]
    return B_same(want, got)


READS = P6.READS


def account(reads, writes):
    bad = []
    for pc, addr, n, cnt in reads:
        if not any(lo <= addr and addr + n <= hi for lo, hi, _ in READS):
            bad.append(("R", pc, addr, n, cnt))
    for pc, addr, n, cnt in writes:
        bad.append(("W", pc, addr, n, cnt))
    return bad


def predict(fam, a, flip=None):
    e = p1.E(flip)
    try:
        out = MODEL[fam](e, a)
    except (TypeError, KeyError, IndexError, AttributeError, ZeroDivisionError, struct.error):
        return ("model-null",), e.names
    return out, e.names


def install():
    """Point part 1's check machinery at this part's families (its module state only; part 1's file is unchanged)."""
    B.FNS, B.FAMILIES, B.NCASES, B.POP, B.SITE = FNS, FAMILIES, NCASES, POP, SITE
    B.GEN, B.MODEL = GEN, MODEL
    B.observed, B.norm, B.account, B.write_spec, B.predict, B.same = observed, norm, account, write_spec, predict, same
    B.Case = Case

    def build(limit=None):
        cases = []
        for fam in FAMILIES:
            rnd = random.Random("n66sa-s2ae7-" + fam)
            for _ in range(NCASES[fam] if limit is None else min(limit, NCASES[fam])):
                cases.append(GEN[fam](rnd))
        return cases
    B.build = build


# ----------------------------------------------------------------------------------------------- static reads
STATIC = (
    ("chg", 0x00647840, 0x006478E4), ("wear", 0x005DAA40, 0x005DAB3E), ("h26", 0x005C6690, 0x005C675E),
    ("h27", 0x005C6760, 0x005C686B),
    ("getlvl", 0x006442A0, 0x006442FC), ("expmax", 0x00611830, 0x00611859), ("invfirst", 0x0063B2C0, 0x0063B2DD),
    ("invnext", 0x0063DFA0, 0x0063DFC8), ("invnode", 0x0063DFD0, 0x0063DFEF), ("statsget", 0x00625480, 0x006254DE),
    ("slvalue", 0x00624F60, 0x00624FD8), ("istype", 0x00629BB0, 0x00629C7C), ("itemrec", 0x006335F0, 0x00633637),
    ("itemtype", 0x00628700, 0x00628738), ("stackable", 0x006289F0, 0x00628A3A),
    ("hasdur", 0x00629930, 0x00629989), ("base73", 0x00625E00, 0x00625E5B), ("baseval", 0x00624ED0, 0x00624F36),
    ("isdead", 0x005541B0, 0x005541F7), ("msrec", 0x00451F80, 0x00451FA4), ("param5", 0x004E6C70, 0x004E6C9B),
    ("muldiv", 0x00483360, 0x004833E0), ("montypeflag", 0x005A0180, 0x005A01A2),
    ("unitgetstat", 0x00625500, 0x0062551B), ("monowner", 0x0058F0D0, 0x0058F100),
)


def cmd_static():
    if p1.img() is None:
        return 1
    for label, lo, hi in STATIC:
        calls = 0
        for ln in P6.objdump(lo, hi):
            print("%s %s" % (label, ln))
            if " call " in ln:
                calls += 1
        print("%s CALLS %d" % (label, calls))
    return 0


def cmd_reach(limit=None):
    """Per family: the model's outcomes and which tests decided (counted once per case)."""
    cases = B.build(limit)
    for fam in FAMILIES:
        out, tests = {}, {}
        for c in cases:
            if c.fam != fam:
                continue
            want, names = predict(fam, c.a)
            if want[0] == "ret":
                k = "ret" if want[1] is None else "ret=%d" % s32(want[1])
            elif want[0] == "obs":
                k = "obs:%08x" % want[1]
            else:
                k = want[0]
            out[k] = out.get(k, 0) + 1
            for nm in names:
                if not nm.endswith("~") and not nm.startswith("spec_"):
                    alt = predict(fam, c.a, flip=nm)[0]
                    if not B_same(want, alt) or not B_same(alt, want):
                        tests[nm] = tests.get(nm, 0) + 1
        print("REACH %s outcomes %s" % (fam, " ".join("%s:%d" % kv for kv in sorted(out.items()))))
        print("REACH %s deciding %s" % (fam, " ".join("%s:%d" % kv for kv in sorted(tests.items()))))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("cases", "check", "reach", "static", "manifest"))
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    o = ap.parse_args(argv)
    install()
    if o.cmd == "cases":
        os.makedirs(o.dir, exist_ok=True)
        B.cmd_cases(o.dir, o.limit)
        return 0
    if o.cmd == "check":
        return B.cmd_check(o.dir, o.limit)
    if o.cmd == "static":
        return cmd_static()
    if o.cmd == "reach":
        return cmd_reach(o.limit)
    B.cmd_manifest(o.dir, o.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

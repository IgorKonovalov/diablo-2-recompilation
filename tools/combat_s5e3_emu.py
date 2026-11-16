#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S5e part 3 (`lane/n66t`): the defence roll with a player's shield, UNIT_GetDefense and the
COMBAT_ApplyDamage prologue under Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java,
compared with the models below. Parts 1 and 2 (tools/combat_s5e_emu.py, tools/combat_s5e2_emu.py and their kept runs)
stay unchanged; this file imports their unit, stat-list and MonStats builders, and S6f's inventory, item and
COMPOSIT_WeaponClass models (tools/anim_s6f_emu.py, unchanged) with its declared item tables.

    python3 -I tools/combat_s5e3_emu.py cases [--dir D] [--limit N]   write D/s5e3.cases, D/s5e3.mem and the images
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s5e3.cases D/s5e3.mem > D/s5e3.out
    python3 -I tools/combat_s5e3_emu.py check [--dir D] [--limit N]   compare, account for every traced read and write
    python3 -I tools/combat_s5e3_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66t/s5e/run3. Every draw comes from random.Random("n66t-s5e3-<family>"); the declared
tables: part 1's MonStats and ItemStatCost images, S6f's item records, ItemTypes bits, CharStats codes and
g_ItemWeaponClassIndex (random.Random("n66s-s6f-image")), and this file's CharStats BlockFactor bytes and Skills calc
words (random.Random("n66t-s5e3-image")).

Families (function, registers; inventory rows). Every callee not named as an observed boundary runs whole; the
allocator entries and the fatal path are guards.
  blk  0x0057DFB0 COMBAT_DefenceRoll (ECX game, EDX att; def, isMissile, useBlock), a player defender (type 0) with a
       scratch inventory (page 0 declared at the descriptor's size, so sub_0063ADD0_InvPageGet allocates nothing).
       Callees whole: sub_00622720_UnitBlockChance, sub_0063C8F0_InvItemQuery, sub_0063ADD0_InvPageGet,
       sub_0062A4E0_ItemNotDisabled, ITEMS_UnitIsType, ITEMS_GetType/GetRecord, STATS_GetUnitStat,
       sub_00622D00_UnitIsMoving, 0x00621190, sub_00554010_UnitGetGame, DEBUG_DefenceRollStub, COMBAT_AvoidRoll,
       sub_0057DCA0_WeaponBlockChance, sub_0063BDE0_InvGetBodyLocItem, sub_006261D0_StatListGetEntries, 0x0064F380
       and COMPOSIT_WeaponClass 0x0064F060 with its callees (S6f's `wc` closure; unit +0xC8 bit 3 clear, so
       UNIT_AnimTransform is not reached), RNG_Range.                to-hit 20, 22; remainders 24 and 31.
  def  0x006223F0 UNIT_GetDefense (unit), callees whole: STATS_GetUnitStat, sub_00625500_UnitGetStat, UNIT_HasState,
       UNIT_FindStatListByState, sub_00625D00/00625350/00624ED0 (the state list's base stats), STATLIST_FindIndex,
       SKILLS_GetRecord, InvItemQuery (as blk), sub_00483360_MulDiv. Observed boundary SKILLS_EvalCalc 0x00646CA0
       (from 0x006224BA).                                             to-hit 14, 15.
  adp  0x0057C6C0 COMBAT_ApplyDamage's prologue (ECX game, EDX att; def, flag, pkt) to its first call after the
       tests: observed boundary 0x00621D50 (from 0x0057C78E). Callees whole: sub_00554200_UnitsHostile,
       sub_0058F0D0_MonsterOwner (MonsterData +0x28 null or its +0x28 zero, so sub_00552F60_GameFindUnit is not
       reached; a missile attacker's +0xC8 bit 10 clear), sub_0055B300_PlayerPairFlags, UNIT_GetPlayerData,
       sub_00650D70_AlignSame02, sub_006259B0_UnitAlignGet, sub_00620BB0_UnitGetRoom, sub_00648A80_PathGetRoom,
       sub_0061AB00_RoomIsTown (room +0x10), sub_0066BAB0_RoomLevelId (+0x58, level +0x1D0), sub_006426A0_LevelIsTown, MONSTATS_GetRecord,
       MONSTATS_FlagTest, sub_005541B0_UnitIsDead.                   delivery 22.

Controls as parts 1-2: every named test reversed alone, every ordered compare's strictness switched alone; `sep`
counts the cases a control changes, `passed` those the emulator still matches (must be 0); `spec_*` controls are the
spec's own readings. Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import combat_s5e_emu as p1  # noqa: E402
import combat_s5e2_emu as p2  # noqa: E402
import anim_s6f_emu as f6  # noqa: E402
from anim_s6e_emu import Fatal  # noqa: E402
from combat_s5e_emu import (E, u32, s32, le32, tdiv, muldiv, put_unit, stat, has_state, put_ms, rnd_cls, lcg,  # noqa
                            rng_range, img, ATT, DEF, PKT, GAME, SL_OFF, ARR_OFF, MS, MS_N, MS_SZ, ISC, ISC_N,
                            ISC_SZ, NSTATES, G_DT, DT, BITMASK, FATAL, ALLOC)

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66t", "s5e", "run3")
FNS = {"blk": 0x0057DFB0, "def": 0x006223F0, "adp": 0x0057C6C0}
FAMILIES = ("blk", "def", "adp")
NCASES = {"blk": 6000, "def": 3000, "adp": 3000}
POP = {"blk": 0xC, "def": 4, "adp": 0xC}
OBS_EVAL, OBS_ADP = 0x00646CA0, 0x00621D50
SITE = {("def", OBS_EVAL): 0x006224BF, ("adp", OBS_ADP): 0x0057C793}
INV, PAGES, LOCS = 0x20005000, 0x20005100, 0x20005200
IT, IDATA = f6.IT, f6.IDATA                      # 0x20002000 (+0x40 k), 0x20003000 (+0x80 k)
SL2, ARR2 = DEF + 0x800, DEF + 0x900
PATHU, ROOM, LVL = DEF + 0x800, DEF + 0x900, DEF + 0xA00
PNODE = ATT + 0x800
CS, CS_N, CS_SZ = f6.CS, f6.CS_N, f6.CS_SZ        # 0x21300000, 7, 0xC4
SK, SK_N, SK_SZ = 0x21600000, 64, 0x23C
TOWNS = (1, 0x28, 0x4B, 0x67, 0x6D)
p1.FNS.update(FNS)


class Img3:
    def __init__(self):
        r = random.Random("n66t-s5e3-image")
        self.bf = [r.choice([0, r.randrange(256), r.randint(10, 40)]) for _ in range(CS_N)]
        self.calc = [r.getrandbits(32) for _ in range(SK_N)]
        f = f6.img()
        self.sh = [i for i, x in enumerate(f.irec) if self.typ(i, 51)]
        self.wp = [i for i, x in enumerate(f.irec) if x["comp"] in (5, 6) and self.typ(i, 45)]
        self.both = [i for i in self.sh if i in self.wp]

    @staticmethod
    def typ(i, t):
        f = f6.img()
        r = f.irec[i]
        if f.tyb[r["ty"]][t >> 5] & (1 << (t & 31)):
            return True
        return 0 < r["ty2"] < f6.TY_N and bool(f.tyb[r["ty2"]][t >> 5] & (1 << (t & 31)))


I3 = Img3()


# ----------------------------------------------------------------------------------------------- inventory
def inv_put(c, a):
    """A case's inventory (S6f's layout at this file's addresses) and its two hand items."""
    if a is None:
        return
    c.put(INV, le32(a["magic"]))
    c.put(INV + 0x14, le32(PAGES) + le32(1))
    c.put(INV + 0x1C, le32(a["prim"]) + le32(0))
    c.put(PAGES + 8, bytes(a["pagesz"]) + b"\0\0" + le32(LOCS))
    c.put(LOCS, bytes(0x34))
    for k, h in enumerate(a["hands"]):
        if h is None:
            continue
        iu, idd = IT + 0x40 * k, IDATA + 0x80 * k
        c.put(LOCS + 4 * (4 + k), le32(iu))
        c.put(iu, le32(h["type"]) + le32(h["cls"]) + le32(0) + le32(h["id"]) + le32(0) +
              le32(idd if h["d"] is not None else 0))
        if h["d"] is not None:
            c.put(idd + 0x18, le32(h["d"]["f"]))
            c.put(idd + 0x44, bytes([h["d"]["loc"]]))


def gen_inv(rnd, bias):
    a = f6.gen_inv(rnd)
    if bias:
        a["magic"], a["pagesz"] = f6.MAGIC, (0x0D, 0x01)
        for j in range(2):
            h = f6.gen_item(rnd)
            h["type"] = rnd.choice([4, 4, 4, 4, 4, 2])
            h["cls"] = rnd.choice([rnd.choice(I3.both), rnd.choice(I3.both), rnd.choice(I3.sh), rnd.choice(I3.wp),
                                   rnd.randrange(f6.IREC_N)])
            if rnd.random() < 0.85:
                h["d"] = dict(f=rnd.choice([0, 0, 0, 0, 0x100, 0x4000, 0x10]), loc=rnd.choice([4, 5, 4, 5, 1]))
            a["hands"][j] = h if rnd.random() < 0.93 else None
        ids = [h["id"] for h in a["hands"] if h is not None]
        a["prim"] = rnd.choice([0xFFFFFFFF, rnd.getrandbits(16)] + ids * 2)
    return a


def shield_query(e, inva):
    """sub_0063C8F0_InvItemQuery(inv, out): the first of hands 4, 5 enabled and of type 51."""
    if not e.t("inv_set", inva is not None):
        return None
    inv = f6.Inv(inva)
    for k in (4, 5):
        it = f6.loc(e, inv, k) if e.t("magic_q", inva["magic"] == f6.MAGIC) else None
        if it is not None and e.t("q_notdis", f6.notdis(e, it)) and e.t("q_t51", f6.is_type(e, it, 51)):
            return it
    return None


# ----------------------------------------------------------------------------------------------- blk
def put_c8(c, u, v):
    c.put(u["base"] + 0xC8, le32(v))
    u["c8"] = v


def gen_blk(rnd):
    c = p1.Case("blk")
    cls = rnd.choice([6, 6, 6, 4, rnd.randrange(7)])
    mode = rnd.choice([2, 3, 6, 1, 4, 0, 17, 7, 8, 2, 3, rnd.randrange(20)])
    f30 = rnd.choice([0, 0, 0, rnd.getrandbits(32)])
    f40 = rnd.choice([2, 3, 6, 1, 4, 5, rnd.randrange(20)])
    sv = {20: rnd.choice([0, rnd.randint(1, 80), rnd.randint(1, 80), rnd.randint(-10, -1), rnd.randint(70, 200),
                          rnd.getrandbits(32)]),
          2: rnd.choice([rnd.randint(0, 250), 15, rnd.randint(10, 30), rnd.getrandbits(32)]),
          12: rnd.choice([0, 1, 2, rnd.randint(1, 99), -3]),
          340: rnd.choice([0, rnd.randint(1, 99), -4, 100]),
          338: rnd.choice([0, rnd.randint(1, 99), -4, 100]),
          339: rnd.choice([0, rnd.randint(1, 99), -4, 100])}
    sv = {k: v for k, v in sv.items() if rnd.random() < 0.92}
    dfn = put_unit(c, rnd, DEF, 0, cls, sv, [], mode=mode, listflag=True, f30=f30, f40=f40)
    put_c8(c, dfn, rnd.getrandbits(32) & ~0x8)
    inva = gen_inv(rnd, rnd.random() < 0.85) if rnd.random() < 0.97 else None
    if inva is not None:
        c.put(DEF + 0x60, le32(INV))
        inv_put(c, inva)
    ent = []
    if rnd.random() < 0.6:                                     # stat-348 entries (layer = an item type)
        tys = [0, 45, 51, rnd.randrange(f6.TY_N)]
        for h in (inva or {}).get("hands", []):
            if h is not None and f6.rec(h["cls"]) is not None:
                tys.append(f6.rec(h["cls"])["ty"])
        for ly in sorted(set(rnd.choice(tys) for _ in range(rnd.randint(1, 3)))):
            ent.append((ly, rnd.choice([rnd.randint(1, 60), rnd.randint(1, 60), 0, -5, 100])))
    keys = {(s << 16): u32(v) for s, v in dfn["stats"].items()}
    for ly, v in ent:
        keys[(348 << 16) | ly] = u32(v)
    ks = sorted(keys)
    arr = DEF + ARR_OFF
    for i, k in enumerate(ks):
        c.put(arr + 8 * i, le32(k) + le32(keys[k]))
    c.put(DEF + SL_OFF + 0x4C, struct.pack("<H", len(ks)) + bytes(2))
    exp = rnd.choice([0, 1, 1, rnd.getrandbits(32)])
    c.put(GAME + 0x70, le32(exp))
    att = put_unit(c, rnd, ATT, rnd.choice([0, 1]), 0, {}, [], nolist=True)
    ub = rnd.choice([1, 1, 1, 0, rnd.getrandbits(32)])
    miss = rnd.choice([0, 0, 1, rnd.getrandbits(32)])
    c.ecx, c.edx = GAME, ATT
    c.args = [DEF, miss, ub]
    c.dumps = [(DEF + 0x20, 8), (INV + 0x1C, 4)]
    c.a = dict(dfn=dfn, inv=inva, ent=ent, exp=exp, ub=ub, miss=miss, cls=cls)
    return c


def block_chance(e, d, inva, exp):
    if shield_query(e, inva) is None:
        return 0
    b = s32(stat(d, 20) + I3.bf[d["cls"]])
    if e.t("exp", exp != 0):
        lv = stat(d, 12)
        if e.c("lv_lt2", lv, "<", 2):
            lv = 1
        b = tdiv(s32(s32(stat(d, 2) - 15) * b), s32(lv * 2))
    if e.c("b_lt75", b, "<", 75):
        return b
    return 75


def is_moving(e, d):
    m = d["f40"] if e.t("mv_f30", d["f30"] != 0) else d["mode"]
    m = u32(m)
    return e.c("mv_gt1", m, ">", 1) and (e.c("mv_lt4", m, "<", 4) or e.t("mv_eq6", m == 6))


def wblock_chance(e, a):
    inva = a["inv"]
    inv = f6.Inv(inva) if inva is not None else None
    h4 = f6.loc(e, inv, 4) if inv is not None and inva["magic"] == f6.MAGIC else None
    h5 = f6.loc(e, inv, 5) if inv is not None and inva["magic"] == f6.MAGIC else None
    best = 0
    for ly, v in a["ent"]:
        v = s32(v)
        if e.t("wb_l0", ly == 0):
            best = v
            continue
        m = (h5 is not None and e.t("wb_h5", f6.is_type(e, h5, ly))) or \
            (h4 is not None and e.t("wb_h4", f6.is_type(e, h4, ly)))
        if m and e.c("wb_lt", best, "<", v):
            best = v
    return best


def m_blk(e, a):
    d = a["dfn"]
    seed = list(d["seed"])
    inva = None if a["inv"] is None else dict(a["inv"], hands=list(a["inv"]["hands"]))
    a2 = dict(a, inv=inva)
    draws = []

    def out(v):
        e.hit("draws%d" % len(draws))
        return ("ret", v, tuple(seed), None if inva is None else u32(inva["prim"]))

    def avoid():
        m = u32(d["mode"])
        if e.t("av_m3", m == 3) or e.t("av_m2", m == 2):
            ev = stat(d, 340)
            if not e.c("ev_gt0", ev, ">", 0):
                return out(0)
            r = lcg(seed) % 100
            draws.append("ev")
            return out(8 if e.c("r_lt_ev", r, "<", ev) else 0)
        wb = wblock_chance(e, a2)
        if e.c("wb_gt0", wb, ">", 0):
            mode = d["f40"] if d["f30"] != 0 else d["mode"]
            inv = f6.Inv(inva) if inva is not None else None
            _, idx = f6.m_wc(e, dict(type=0, ucls=a["cls"]), a["cls"], mode, inv)
            if e.t("wc_d", idx == 0xD):
                r = rng_range(seed, 100)
                draws.append("wb")
                if e.c("r_lt_wb", r, "<", wb):
                    return out(0x10)
        if e.t("melee", a["miss"] == 0):
            ch, res, nm = stat(d, 338), 4, "dodge"
        else:
            ch, res, nm = stat(d, 339), 2, "avoid"
        if e.c(nm + "_gt0", ch, ">", 0):
            r = rng_range(seed, 100)
            draws.append(nm)
            if e.c("r_lt_" + nm, r, "<", ch):
                return out(res)
        return out(0)

    if not e.t("useblock", a["ub"] != 0):
        return avoid()
    b = block_chance(e, d, inva, a["exp"])
    e.hit("b_pos", b > 0)
    if not e.c("b_ge1", b, ">=", 1):
        return avoid()
    mv = is_moving(e, d)
    e.hit("moving_mode2", mv and d["mode"] == 2)
    e.hit("moving_div", mv and d["mode"] != 2 and b // 3 != b)
    if mv and e.t("mode_ne2", u32(d["mode"]) != 2):
        b = tdiv(b, 3)
    e.names.add("spec_b_gt0_after")       # control: C2's pseudocode, the b > 0 test after the divide
    if e.flip == "spec_b_gt0_after" and b < 1:
        return avoid()
    r = lcg(seed) % 100
    draws.append("blk")
    if e.c("r_ge_b", b, "<=", r):
        return avoid()
    return out(1)


# ----------------------------------------------------------------------------------------------- def
def gen_def(rnd):
    c = p1.Case("def")
    hs = rnd.random() < 0.6
    sv = {31: rnd.choice([0, rnd.randint(1, 3000), rnd.randint(-300, 0), rnd.randint(1, 50), rnd.getrandbits(32)]),
          2: rnd.choice([0, rnd.randint(1, 300), rnd.randint(-40, -1), 3, -3]),
          171: rnd.choice([0, 0, rnd.randint(1, 300), rnd.randint(-100, -1)]),
          16: rnd.choice([0, 0, rnd.randint(1, 300), rnd.randint(-100, -1)]),
          182: rnd.choice([0, 0, rnd.randint(1, 200), rnd.randint(-99, -1), rnd.getrandbits(32)])}
    sv = {k: v for k, v in sv.items() if rnd.random() < 0.95}
    sts = [101] if (hs and rnd.random() < 0.9) or rnd.random() < 0.1 else []
    dfn = put_unit(c, rnd, DEF, rnd.choice([0, 0, 1]), rnd.randrange(7), sv, sts, listflag=True if hs else None)
    sl = DEF + SL_OFF
    node = rnd.choice([0, SL2, SL2, SL2]) if hs else 0
    nst = rnd.choice([101, 101, 101, rnd.randrange(1, NSTATES)])
    h3c = node if rnd.random() < 0.85 else 0
    h40 = node if not h3c else 0
    c.put(sl + 0x3C, le32(h3c))
    c.put(sl + 0x40, le32(h40))
    hs_vals = {}
    if node:
        c.put(SL2, bytes(rnd.getrandbits(8) for _ in range(0x60)))
        c.put(SL2 + 0x14, le32(nst))
        c.put(SL2 + 0x2C, le32(0))
        hs_vals = {350: rnd.choice([rnd.randrange(SK_N), rnd.randrange(SK_N), 0, -2, SK_N + 5]),
                   351: rnd.choice([rnd.randint(1, 30), rnd.randint(1, 30), 0, -1])}
        hs_vals = {k: v for k, v in hs_vals.items() if rnd.random() < 0.95}
        keys = {(s << 16): u32(v) for s, v in hs_vals.items()}
        keys[(350 << 16) | 1] = rnd.getrandbits(32)
        keys[(200 << 16)] = rnd.getrandbits(32)
        ks = sorted(keys)
        for i, k in enumerate(ks):
            c.put(ARR2 + 8 * i, le32(k) + le32(keys[k]))
        c.put(SL2 + 0x24, le32(ARR2) + struct.pack("<H", len(ks)) + bytes(2))
    inva = gen_inv(rnd, rnd.random() < 0.8) if rnd.random() < 0.95 else None
    c.put(DEF + 0x60, le32(INV if inva is not None else 0))
    inv_put(c, inva)
    c.args = [DEF]
    c.ecx, c.edx = rnd.getrandbits(32), rnd.getrandbits(32)
    c.a = dict(dfn=dfn, node=h3c or h40, nst=nst, hs=hs_vals, inv=inva)
    return c


def neg_div100(x):
    """0x006224DD-0x006224EE: imul by 0xAE147AE1, sar edx 5, plus the sign bit."""
    hi = (s32(x) * s32(0xAE147AE1)) >> 32
    q = s32(hi) >> 5
    return s32(q + ((q >> 31) & 1))


def m_def(e, a):
    d = a["dfn"]
    v = s32(stat(d, 31) + tdiv(stat(d, 2), 4))
    p = s32(stat(d, 171) + stat(d, 16))
    if e.t("st101", has_state(d, 101)):
        if e.t("sl_found", d["listflag"] and a["node"] != 0 and a["nst"] == 101):
            sk, lv = s32(a["hs"].get(350, 0)), s32(a["hs"].get(351, 0))
            if e.c("sk_gt0", sk, ">", 0) and e.c("lv_gt0", lv, ">", 0):
                if e.t("sk_rec", sk < SK_N):
                    if e.t("hs_shield", shield_query(e, a["inv"]) is not None):
                        e.hit("evalcalc")
                        return ("obs", OBS_EVAL, (DEF, I3.calc[sk], u32(sk), u32(lv)))
    x = s32(p * v)
    e.hit("neg_d_differs", v < 1 and neg_div100(x) != tdiv(x, 100))
    e.names.add("spec_def_plain")          # control: B1's text, d + (d * p) / 100 for every d
    if e.c("d_ge1", v, ">=", 1) or e.flip == "spec_def_plain":
        q = tdiv(x, 100)
    else:
        q = neg_div100(x)
    v = s32(v + q)
    s = stat(d, 182)
    if e.t("s182", s != 0):
        v = s32(v + muldiv(v, s, 100))
    e.hit("pct_terms", p != 0 or s != 0)
    return ("ret", u32(v))


# ----------------------------------------------------------------------------------------------- adp
def gen_adp(rnd):
    c = p1.Case("adp")
    units = {}
    for base, role in ((ATT, "att"), (DEF, "def")):
        typ = rnd.choice([0, 0, 1, 1, 1, 2, 3, 4, 5])
        cls = rnd_cls(rnd, 0.1) if typ == 1 else rnd.randrange(7)
        sv = {172: rnd.choice([0, 1, 2, 0, rnd.randrange(5)])} if rnd.random() < 0.8 else {}
        mode = rnd.choice([0, 0x11, 0xC, 1, 4, rnd.randrange(20)])
        u = put_unit(c, rnd, base, typ, cls, sv, [], mode=mode, listflag=True)
        p2.rewrite_list(c, rnd, base, u, chain=(rnd.choice([0x69, 0x69, rnd.randrange(1, 200)]),
                                                rnd.random() < 0.8))
        uid = rnd.getrandbits(32)
        c.put(base + 0x0C, le32(uid))
        u["id"] = uid
        c6 = rnd.choice([0, 0, 0, 1, rnd.getrandbits(8)])
        c.put(base + 0xC6, bytes([c6]))
        u["c6"] = c6
        c.put(base + 0xC8, le32(rnd.getrandbits(32) & ~0x400 & ~0x20000))
        md = base + p1.MD_OFF
        if typ == 1:                                           # MonsterOwner: a record with +0x28 = 0, or none
            rec = rnd.choice([0, md + 0x40])
            c.put(md + 0x28, le32(rec))
            if rec:
                c.put(rec + 0x28, le32(0))
        units[role] = u
    att, dfn = units["att"], units["def"]
    # a player pair: att's PlayerData +0x38 list
    if att["type"] == 0:
        md = ATT + p1.MD_OFF
        n = rnd.choice([0, 1, 2, 3])
        head = 0
        nodes = []
        for i in range(n):
            nid = rnd.choice([dfn["id"], rnd.getrandbits(32)])
            fl = rnd.choice([8, 0, 0xFFFFFFFF, rnd.getrandbits(32), 1])
            nodes.append((nid, fl))
        for i, (nid, fl) in enumerate(nodes):
            at = PNODE + 0x20 * i
            nxt = PNODE + 0x20 * (i + 1) if i + 1 < n else 0
            c.put(at, le32(nid) + le32(fl) + le32(0) + le32(0) + le32(nxt))
        c.put(md + 0x38, le32(PNODE if n else 0))
        att["pnodes"] = nodes
    # the defender's room
    lvl = rnd.choice(list(TOWNS) + [2, 3, 39, 41, 74, 76, 102, 104, 108, 110, rnd.randrange(140)])
    room = rnd.choice([ROOM, ROOM, ROOM, ROOM, 0])
    if dfn["type"] in (2, 4, 5):
        c.put(DEF + 0x2C, le32(PATHU))
        c.put(PATHU, le32(room))
    else:
        path = rnd.choice([PATHU, PATHU, PATHU, 0])
        c.put(DEF + 0x2C, le32(path))
        c.put(PATHU + 0x1C, le32(room))
        room = room if path else 0
    if room:                                                   # room +0x10 -> its DRLG room, +0x58 -> level
        c.put(ROOM + 0x10, le32(ROOM + 0x80))
        c.put(ROOM + 0x80 + 0x58, le32(LVL))
        c.put(LVL + 0x1D0, le32(lvl))
    patch = {}
    if att["type"] == 1:
        patch.update(put_ms(c, rnd, att["cls"], o0d=rnd.choice([0, 4, 0xFF, rnd.getrandbits(8)])))
    if dfn["type"] == 1:
        patch.update(put_ms(c, rnd, dfn["cls"], o0d=rnd.choice([0, 0x80, 0xFF, rnd.getrandbits(8)])))
    pk0 = rnd.choice([0, 0x1000, rnd.getrandbits(32)])
    pk4 = rnd.getrandbits(32)
    c.put(PKT, le32(pk0) + le32(pk4))
    pa = rnd.choice([ATT] * 30 + [0, 0, DEF])
    pd = 0 if rnd.random() < 0.03 else DEF
    c.ecx, c.edx = GAME, pa
    c.args = [pd, rnd.choice([0, 1]), PKT]
    c.dumps = [(PKT, 8)]
    c.a = dict(att=(att if pa == ATT else dfn if pa == DEF else None), dfn=dfn if pd else None, pk0=pk0, pk4=pk4,
               room=room, lvl=lvl, patch=patch, pa=pa, pd=pd)
    return c


def ms_rec_ok(u):
    return 0 <= u["cls"] < MS_N


def hostile(e, att, dfn):
    if att is dfn:                                             # the same unit, or both null
        return 0
    if e.t("h_pp", att is not None and att["type"] == 0 and dfn is not None and dfn["type"] == 0):
        for nid, fl in att.get("pnodes", []):
            if e.t("pn_id", nid == dfn["id"]):
                return fl & 8
        return 0
    if att is None or dfn is None:
        return 1
    al, bl = p2.align(att, e), p2.align(dfn, e)
    if e.t("al_a0", al == 0):
        same = e.t("al_b0", bl == 0)
    else:
        same = e.t("al_a2", al == 2) and e.t("al_b2", bl == 2)
    return 0 if same else 1


def m_adp(e, a):
    att, dfn, pk4 = a["att"], a["dfn"], a["pk4"]
    h = hostile(e, att, dfn)
    e.hit("hostile0", h == 0)
    if not e.t("hostile", h != 0) and not e.t("f1000", a["pk0"] & 0x1000):
        return ("ret", pk4 & 0xFFFFFFFC)
    if dfn is None:
        return ("fatal",)
    room = a["room"]
    if not e.t("room", room != 0):
        return ("ret", pk4 & 0xFFFFFFFC)
    if e.t("town", a["lvl"] in TOWNS):
        ok = att is not None and att["type"] == 1 and ms_rec_ok(att) and \
            e.t("ms0d4", p1.ms_byte(att["cls"], 0x0D) & 4)
        e.hit("town_kept", ok)
        if not ok:
            return ("ret", pk4 & 0xFFFFFFFD)
    if dfn["type"] == 1:
        if not (ms_rec_ok(dfn) and e.t("ms0d80", p1.ms_byte(dfn["cls"], 0x0D) & 0x80)):
            return ("ret", pk4)
    dead = True
    if not e.t("c6", dfn["c6"] & 1):
        m = dfn["mode"]
        if dfn["type"] == 0:
            dead = e.t("p_m0", m == 0) or e.t("p_m11", m == 0x11)
        elif dfn["type"] == 1:
            dead = e.t("m_m0", m == 0) or e.t("m_mc", m == 0xC)
    if e.t("dead", dead):
        return ("ret", pk4)
    e.hit("reached")
    return ("obs", OBS_ADP, (a["pd"], a["pa"]), pk4)


GEN = {"blk": gen_blk, "def": gen_def, "adp": gen_adp}
MODEL = {"blk": m_blk, "def": m_def, "adp": m_adp}


def predict(fam, a, flip=None):
    e = p2.E2(flip)
    try:
        out = p1.with_patch(a, lambda: MODEL[fam](e, a))
    except Fatal:
        out = ("fatal",)
    except (TypeError, KeyError, IndexError, ZeroDivisionError, AttributeError):
        return ("model-null",), e.names
    if flip is None:
        HITS.append(e.hits)
    return out, e.names


HITS = []


# ----------------------------------------------------------------------------------------------- files
def write_spec(d):
    im = img()
    f = f6.img()
    files = {}
    files["monstats"] = bytes(im.ms)
    files["isc"] = bytes(ISC_N * ISC_SZ)
    dt = bytearray(0x1000)
    for off, v in ((0xC4, NSTATES), (0xA78, MS), (0xA80, MS_N), (0xBCC, ISC), (0xBD4, ISC_N), (0xBC4, CS),
                   (0xBC8, CS_N), (0xBFC, f6.TY_N), (0xC00, f6.TY_W), (0xC04, f6.TYB), (0xB98, SK), (0xBA0, SK_N)):
        struct.pack_into("<I", dt, off, v)
    files["dt"] = bytes(dt)
    cs = bytearray(CS_N * CS_SZ)
    for i, code in enumerate(f.cs):
        struct.pack_into("<I", cs, i * CS_SZ + 0x4C, code)
        cs[i * CS_SZ + 0x49] = I3.bf[i]
    files["cs"] = bytes(cs)
    sk = bytearray(SK_N * SK_SZ)
    for i, v in enumerate(I3.calc):
        struct.pack_into("<I", sk, i * SK_SZ + 0x138, v)
    files["sk"] = bytes(sk)
    files["tyb"] = b"".join(struct.pack("<4I", *w) for w in f.tyb)
    ir = bytearray(f6.IREC_N * f6.IREC_SZ)
    for i, r in enumerate(f.irec):
        o = i * f6.IREC_SZ
        struct.pack_into("<II", ir, o + 0xC0, r["c0"], r["c4"])
        ir[o + 0x115] = r["comp"]
        ir[o + 0x11C] = r["twoh"]
        struct.pack_into("<hh", ir, o + 0x11E, r["ty"], r["ty2"])
        ir[o + 0x13D] = r["b13d"]
    files["irec"] = bytes(ir)
    iwc = bytearray(0x44)
    for i, (k, v) in enumerate(f.iwc):
        struct.pack_into("<II", iwc, 8 * i, k, v)
    struct.pack_into("<I", iwc, 0x40, len(f.iwc))
    files["iwc"] = bytes(iwc)
    at = {"monstats": MS, "isc": ISC, "dt": DT, "cs": CS, "sk": SK, "tyb": f6.TYB, "irec": f6.IREC, "iwc": f6.IWC}
    lines = ["# plan 0066 S5e part 3 (tools/combat_s5e3_emu.py): declared tables", "dword %08x %08x" % (G_DT, DT)]
    for k, v in files.items():
        p = os.path.join(d, "s5e3-%s.bin" % k)
        with open(p, "wb") as fh:
            fh.write(v)
        lines.append("load %08x %s" % (at[k], p))
    lines += ["dword %08x %08x" % (f6.ITP, f6.IREC_N), "dword %08x %08x" % (f6.ITP + 4, f6.IREC),
              "bytes %08x 0d01" % f6.DESC]
    lines += ["guard %08x" % x for x in FATAL + ALLOC]
    lines += ["observe %08x" % x for x in (OBS_EVAL, OBS_ADP)]
    with open(os.path.join(d, "s5e3.mem"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


def build(limit=None):
    cases = []
    for fam in FAMILIES:
        rnd = random.Random("n66t-s5e3-" + fam)
        for _ in range(NCASES[fam] if limit is None else min(limit, NCASES[fam])):
            cases.append(GEN[fam](rnd))
    return cases


def cmd_cases(d, limit=None):
    os.makedirs(d, exist_ok=True)
    write_spec(d)
    cases = build(limit)
    with open(os.path.join(d, "s5e3.cases"), "w") as fh:
        for c in cases:
            fh.write("\n".join(c.lines()) + "\n")
    print("cases %d -> %s" % (len(cases), os.path.join(d, "s5e3.cases")))


def observed(fam, c):
    if c.get("stop") == FATAL[0]:
        return ("fatal",), None
    if "stop" in c:
        return ("stop", c["stop"], c["msg"]), None
    dw = lambda addr, n: struct.unpack("<%dI" % (n // 4), c["dumps"][addr])  # noqa: E731
    if "obs" in c:
        st = c["stack"]
        ret = struct.unpack_from("<I", st, 0)[0]
        o = c["obs"]
        if o == OBS_EVAL:
            return ("obs", o, struct.unpack_from("<4I", st, 4)), ret
        if o == OBS_ADP:
            return ("obs", o, struct.unpack_from("<2I", st, 4), dw(PKT, 8)[1]), ret
        return ("obs?", o), ret
    if c["pop"] != POP[fam]:
        return ("pop", c["pop"]), None
    if fam == "blk":
        return ("ret", c["eax"], dw(DEF + 0x20, 8), dw(INV + 0x1C, 4)[0]), None
    if fam == "def":
        return ("ret", c["eax"]), None
    return ("ret", dw(PKT, 8)[1]), None


def same(fam, want, got, a):
    if fam == "blk" and want[0] == "ret" and got[0] == "ret":
        return want[1] == got[1] and tuple(want[2]) == tuple(got[2]) and (want[3] is None or want[3] == got[3])
    return p2.same(fam, want, got, a)


CONST_READS = ((BITMASK, BITMASK + 128, "g_BitMask32 0x006CE268 (.rdata), read by UNIT_TestStateBit, ITEMS_UnitIsType "
                "and COMBAT_ApplyDamage 0x0057C727"),
               (G_DT, G_DT + 4, "g_pDataTables 0x00744304 (.data), written by the spec's dword line"),
               (f6.WTOK, f6.WTOK + 13 * 8, "g_WeaponClassTokens 0x006EB748 (.rdata), read by COMPOSIT_WeaponClass"),
               (0x006426C0, 0x006426C8, "LevelIsTown's jump table 0x006426C0 (.text), 2 dwords (0x006426AF)"),
               (0x006426C8, 0x006426C8 + 0x6D, "LevelIsTown's index bytes 0x006426C8 (.text), 109 (id - 1 <= 0x6C, "
                "0x006426A3; 0x006426A8)"))


def account(reads, writes):
    bad = []
    for pc, addr, n, cnt in reads:
        if not any(lo <= addr and addr + n <= hi for lo, hi, _ in CONST_READS):
            bad.append(("R", pc, addr, n, cnt))
    for pc, addr, n, cnt in writes:
        bad.append(("W", pc, addr, n, cnt))
    return bad


def kind(want):
    return "obs:%x" % want[1] if want[0] == "obs" else want[0]


def cmd_check(d, limit=None, controls=True):
    cases = build(limit)
    calls, reads, writes = p1.read_out(os.path.join(d, "s5e3.out"))
    if len(calls) != len(cases):
        print("CASES %d emulated %d: mismatch" % (len(cases), len(calls)))
        return 1
    bad = 0
    per = {f: [0, 0, {}] for f in FAMILIES}
    names_by_fam = {f: set() for f in FAMILIES}
    got_all = []
    for i, (c, k) in enumerate(zip(cases, calls)):
        fam = c.fam
        want, names = predict(fam, c.a)
        names_by_fam[fam] |= names
        got, site = observed(fam, k)
        ok = same(fam, want, got, c.a)
        if ok and want[0] == "obs":
            ok = site == SITE[(fam, want[1])]
        per[fam][0] += 1
        kd = kind(want)
        per[fam][2][kd] = per[fam][2].get(kd, 0) + 1
        if not ok:
            per[fam][1] += 1
            bad += 1
            if bad <= 25:
                print("MISMATCH %d %s want=%r got=%r site=%r" % (i, fam, want, got, site))
        got_all.append(got)
    tally = {}
    for c, h in zip(cases, HITS[:len(cases)]):
        for x in h:
            tally[c.fam + " " + x] = tally.get(c.fam + " " + x, 0) + 1
    print("ROWS " + " ".join("%s=%d" % (k.replace(" ", ":"), v) for k, v in sorted(tally.items())))
    for f in FAMILIES:
        n, b, kinds = per[f]
        print("FAMILY %s cases=%d mismatches=%d outcomes %s" % (f, n, b, " ".join(
            "%s:%d" % kv for kv in sorted(kinds.items()))))
    ctl_bad, ctl_lines = 0, []
    if controls:
        for f in FAMILIES:
            fc = [(c, g) for c, g in zip(cases, got_all) if c.fam == f]
            base = [predict(f, c.a)[0] for c, _ in fc]
            for nm in sorted(names_by_fam[f]):
                sep = passed = 0
                for (c, got), b in zip(fc, base):
                    alt, _ = predict(f, c.a, flip=nm)
                    if not same(f, b, alt, c.a) or not same(f, alt, b, c.a):
                        sep += 1
                        if same(f, alt, got, c.a):
                            passed += 1
                ctl_lines.append("CONTROL %s %s sep=%d passed=%d" % (f, nm, sep, passed))
                if passed:
                    ctl_bad += 1
        print("\n".join(ctl_lines))
    nsep0 = sum(1 for x in ctl_lines if " sep=0 " in x)
    acc = account(reads, writes)
    for x in acc[:40]:
        print("UNACCOUNTED %s pc=%08x addr=%08x n=%d count=%d" % x)
    stops = sum(1 for k in calls if "stop" in k and k.get("stop") != FATAL[0])
    print("S5E3 total cases=%d mismatches=%d stops=%d controls=%d unseparated=%d controls_passed=%d unaccounted=%d"
          % (len(cases), bad, stops, len(ctl_lines), nsep0, ctl_bad, len(acc)))
    return 1 if bad or ctl_bad or acc else 0


def cmd_manifest(d, write):
    names = sorted(x for x in os.listdir(d) if os.path.isfile(os.path.join(d, x)) and x != "manifest.sha256")
    out = []
    for n in names:
        with open(os.path.join(d, n), "rb") as fh:
            out.append("%s  %s" % (hashlib.sha256(fh.read()).hexdigest(), n))
    text = "\n".join(out) + "\n"
    if write:
        with open(os.path.join(d, "manifest.sha256"), "w") as fh:
            fh.write(text)
    print(text, end="")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("cases", "check", "manifest"))
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--no-controls", action="store_true")
    o = ap.parse_args(argv)
    if o.cmd == "cases":
        cmd_cases(o.dir, o.limit)
        return 0
    if o.cmd == "check":
        return cmd_check(o.dir, o.limit, not o.no_controls)
    cmd_manifest(o.dir, o.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S5e part 2 (`lane/n66t`): the stat events, the life tick and COMBAT_BuildDamage under
Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java, compared with the models below.
Part 1 (tools/combat_s5e_emu.py, its kept run workspace/logs/n66t/s5e/run) stays unchanged; this file imports its
unit, stat-list, MonStats and arithmetic helpers and the same declared MonStats image.

    python3 -I tools/combat_s5e2_emu.py cases [--dir D]     write D/s5e2.cases, D/s5e2.mem and the table images
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s5e2.cases D/s5e2.mem > D/s5e2.out
    python3 -I tools/combat_s5e2_emu.py check [--dir D]     compare, account for every traced read and write, controls
    python3 -I tools/combat_s5e2_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66t/s5e/run2. Every draw comes from random.Random("n66t-s5e2-<family>"); the declared
MonStats image is part 1's (random.Random("n66t-s5e-image")), the MonType table random.Random("n66t-s5e2-montype").

Families (function, registers; inventory rows). Every callee not named as an observed boundary runs whole; the
allocator entries and the fatal path are guards.
  cb     0x005BFFC0 STATEVENT_CrushingBlow (EDX event; att, def, pkt, stat key, x); observed boundary
         sub_00627260_UnitSetStat (from 0x005C00F6). Callees whole: UnitGetStat, STATS_GetUnitStat,
         HirelingType, MONSTATS_IsBoss, MonTypeFlag, sub_005738F0_PlayerHpPct (its .rdata table), MulDiv.
         delivery 39, 40, 41, 46; README 12's remainder.
  ow     0x005BFE60 STATEVENT_OpenWounds (EDX event; att, def, pkt, key, x); observed boundary STATE_ApplyTimed
         (from 0x005BFFA2). Callees whole: sub_005BFDA0_OpenWoundsBand, MonTypeFlag.     delivery 42, 43, 47.
  frz    0x005BFC60 STATEVENT_Freeze (ECX game, EDX event; att, def, pkt, key, x); observed boundary
         COMBAT_ApplyDamage (from 0x005BFD75); the CRT memset 0x00681EF0 runs whole (0x70 < 0x100: the SSE flag
         0x00994C88 is not read).                                                           delivery 44.
  regen  0x00580610 sub_00580610_LifeRegenTick (ESI unit); observed boundaries sub_00627260_UnitSetStat (from
         0x0058066E) and UNIT_UnlinkStatList 0x006277E0 (from 0x00580650); UnitGetMaxHp and
         UNIT_FindStatListByState (0x006256B0, 0x00625650) run whole.                       delivery 48.
  bd     0x0057B7D0 COMBAT_BuildDamage (ECX game, EDX att; def, pkt, critFlag, srcdam), an attacker with no
         inventory (+0x60 = 0, so sub_00535BC0_UnitGetWeapon returns 0 and the weapon relinks 0x00535D10 and
         0x00535E20 find no item). Callees whole: COMBAT_RollPhysical, COMBAT_RollElemStat, COMBAT_RollRange,
         RNG_RangeB, RNG_Range, RNG_RangeOffset, sub_006259B0_UnitAlignGet, UNIT_FindStatListByState,
         sub_0057B660_UndeadDmgBonus, sub_0057B6A0_DmgVsMonType (sub_006261D0 and 0x00626110, 0x00624C10, the
         declared MonType table), sub_005A5560_MonCritDouble, MONSTATS_IsDemon/IsUndead, HirelingType, 0x006235A0.
         Observed boundaries: sub_00627260_UnitSetStat (stat 120, from 0x0057B852), UNIT_DispatchEvent (step 8,
         from 0x0057BCAD), sub_00621E40_UnitSetOverlayStat (from MonCritDouble 0x005A5641).
         damage 3, 4, 5, 7 and 12 (the no-weapon half), 8, 10, 11, 18, 22-26; remainders 6, 9, 13, 14, 15, 34.

Controls as part 1: every named test reversed alone, every ordered compare's strictness switched alone; `sep` counts
the cases a control changes, `passed` those the emulator still matches (must be 0). Stdlib only.
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
from combat_s5e_emu import (E, u32, s32, le32, tdiv, muldiv, put_unit, stat, ms_byte, ms_rec, is_undead,  # noqa: E402
                            is_demon, is_boss, hire, mon_type_flag, put_ms, rnd_cls, lcg, rng_range, img,
                            ATT, DEF, PKT, GAME, CTX, SL_OFF, ARR_OFF, MS, MS_N, MS_SZ, ISC, ISC_N, ISC_SZ, NSTATES,
                            G_DT, DT, BITMASK, FATAL, ALLOC, HIRE, PKT_SZ)

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66t", "s5e", "run2")
FNS = {"cb": 0x005BFFC0, "ow": 0x005BFE60, "frz": 0x005BFC60, "regen": 0x00580610, "bd": 0x0057B7D0}
FAMILIES = ("cb", "ow", "frz", "regen", "bd")
NCASES = {"cb": 2000, "ow": 1500, "frz": 1500, "regen": 1200, "bd": 5000}
POP = {"cb": 0x14, "ow": 0x14, "frz": 0x14, "regen": 0, "bd": 0x10}
OBS_SETSTAT, OBS_STATE, OBS_APPLY, OBS_UNLINK, OBS_EVENT, OBS_OVERLAY = (0x00627260, 0x0056E970, 0x0057C6C0,
                                                                          0x006277E0, 0x005C0C30, 0x00621E40)
SITE = {("cb", OBS_SETSTAT): 0x005C00FB, ("ow", OBS_STATE): 0x005BFFA7, ("frz", OBS_APPLY): 0x005BFD7A,
        ("regen", OBS_SETSTAT): 0x00580673, ("regen", OBS_UNLINK): 0x00580655, ("bd", OBS_SETSTAT): 0x0057B857,
        ("bd", OBS_EVENT): 0x0057BCB2, ("bd", OBS_OVERLAY): 0x005A5641}
MT, MT_N = 0x21300000, 40
MT_STRIDE = (MT_N + 31) // 32
STACK_TOP = 0x7FF00000
FRZ_PKT = STACK_TOP - 4 - 0x78           # EBP = entry ESP - 4; the packet at EBP - 0x78
HPPCT_TABLE = 0x006E1590
JTAB = 0x0057BD94


class E2(E):
    """part 1's model run plus hits: named points a case reaches (the ROWS tallies of the check)."""

    def __init__(self, flip=None):
        super().__init__(flip)
        self.hits = []

    def hit(self, name, cond=True):
        if cond:
            self.hits.append(name)


class Case(p1.Case):
    """part 1's case; its call line names this file's function (p1.FNS gains these keys in memory only)."""


p1.FNS.update(FNS)


def exe_dwords(va, n):
    """n dwords of the pinned image at va (img() checked the hash)."""
    d = open(p1.EXE, "rb").read()
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    ns, so = struct.unpack_from("<H", d, pe + 6)[0], struct.unpack_from("<H", d, pe + 20)[0]
    v = va - 0x400000
    for i in range(ns):
        o = pe + 24 + so + 40 * i
        vs, vaddr, rs, ra = struct.unpack_from("<IIII", d, o + 8)
        if vaddr <= v < vaddr + vs:
            return struct.unpack_from("<%di" % n, d, ra + v - vaddr)
    raise ValueError(hex(va))


_HP = None


def hp_pct(n):
    """sub_005738F0_PlayerHpPct(n): the .rdata table below 9, else (n - 2) * 50."""
    global _HP
    if _HP is None:
        _HP = exe_dwords(HPPCT_TABLE, 9)
    if n < 9:
        return _HP[n]
    return s32((n - 2) * 50)


class MonType:
    def __init__(self):
        r = random.Random("n66t-s5e2-montype")
        self.words = [r.getrandbits(32) for _ in range(MT_N * MT_STRIDE)]

    def test(self, mt, layer):
        return bool(self.words[mt * MT_STRIDE + (layer >> 5)] & (1 << (layer & 31)))


MTY = MonType()


def rewrite_list(c, rnd, base, view, extra=None, chain=None):
    """Rebuild the unit's live array from view['stats'] at layer 0 plus extra {key: value}; set the list's state chain
    fields (+0x14 state, +0x2c next, +0x3c/+0x40 heads) so UNIT_FindStatListByState reads only case memory."""
    sl, arr = base + SL_OFF, base + ARR_OFF
    keys = {(s << 16): u32(v) for s, v in view["stats"].items()}
    for k, v in (extra or {}).items():
        keys[k] = u32(v)
    ks = sorted(keys)
    assert len(ks) < 64
    for i, k in enumerate(ks):
        c.put(arr + 8 * i, le32(k) + le32(keys[k]))
    live = 0x48 if view["listflag"] else 0x24
    c.put(sl + live, le32(arr))
    c.put(sl + live + 4, struct.pack("<H", len(ks)) + bytes(2))
    st, head = chain if chain else (rnd.getrandbits(32), 0)
    c.put(sl + 0x14, le32(st))
    c.put(sl + 0x2C, le32(0))
    c.put(sl + 0x3C, le32(sl if head else 0))
    c.put(sl + 0x40, le32(0))
    view["keys"] = keys
    view["chain"] = (u32(st), bool(head))


def find_state_list(u, st):
    """UNIT_FindStatListByState over the declared one-node chain: the list itself when its +0x14 is st."""
    if u is None or not u.get("listflag") or "chain" not in u:
        return False
    s, head = u["chain"]
    return head and s == st


def sval(rnd, small=(0, 50)):
    return rnd.choice([0, 0, rnd.randint(*small), rnd.randint(1, 10), rnd.randint(-20, -1), rnd.getrandbits(32),
                       rnd.randint(1, 300)])


# ----------------------------------------------------------------------------------------------- stat events
def gen_cb(rnd):
    c = Case("cb")
    ch = rnd.choice([0, -5, rnd.randint(1, 99), 100, rnd.randint(30, 100), rnd.getrandbits(32)])
    att = put_unit(c, rnd, ATT, rnd.choice([0, 0, 1, 1]), rnd_cls(rnd, 0.1), {136: ch}, [])
    dt = rnd.choice([0, 0, 1, 1, 1, 1, 2, 3])
    dcls = rnd_cls(rnd, 0.3) if dt == 1 else rnd.randrange(7)
    life = rnd.choice([rnd.randint(1, 1 << 20), rnd.randint(1, 4000), 0, rnd.randint(-5000, -1), rnd.getrandbits(32),
                       rnd.randint(256, 512)])
    r36 = rnd.choice([0, rnd.randint(1, 99), 99, 100, 101, rnd.randint(100, 300), rnd.randint(-50, -1),
                      rnd.getrandbits(32), None])
    np_ = rnd.choice([None, 0, 1, 2, 3, 5, 8, 9, 12, rnd.randint(-3, 0)])
    sv = {6: life, 36: r36, 100: np_}
    dfn = put_unit(c, rnd, DEF, dt, dcls, sv, [], md_flags=rnd.choice([0, 2, 4, 8, 0xC, rnd.getrandbits(16)]))
    patch = put_ms(c, rnd, dcls, o0c=rnd.choice([0, 0x40, rnd.getrandbits(8)])) if dt == 1 else {}
    ev = rnd.choice([5, 6, 6, rnd.randrange(10)])
    pa = 0 if rnd.random() < 0.03 else ATT
    pd = 0 if rnd.random() < 0.03 else DEF
    c.ecx, c.edx = rnd.getrandbits(32), ev
    c.args = [pa, pd, PKT, 136 << 16, rnd.getrandbits(32)]
    c.dumps = [(ATT + 0x20, 8)]
    c.a = dict(att=att if pa else None, dfn=dfn if pd else None, ev=ev, patch=patch, pd=pd, seed0=att["seed"])
    return c


def m_cb(e, a):
    att, dfn = a["att"], a["dfn"]
    if not e.t("att_set", att is not None) or not e.t("def_set", dfn is not None):
        return ("ret", 0, tuple(a["seed0"]))
    seed = list(att["seed"])
    ch = stat(att, 136)
    if not e.c("ch_gt0", ch, ">", 0):
        return ("ret", 0, tuple(seed))
    r = lcg(seed) % 100
    if not e.c("r_lt_ch", r, "<", ch):
        return ("ret", 0, tuple(seed))
    k = 4
    if e.t("def_player", dfn["type"] == 0):
        k = 10
    elif e.t("def_mon", dfn["type"] == 1):
        if e.t("def_hire", hire(dfn) != 0):
            k = 10
        else:
            if e.t("boss", is_boss(dfn)) or e.t("flag02", mon_type_flag(dfn, 2)):
                k = 8
            n = stat(dfn, 100)
            n = n if e.c("n_ge1", n, ">=", 1) else 1
            pct = hp_pct(n)
            if e.t("pct_nz", pct != 0):
                k = s32(k + muldiv(k, pct, 100))
    if e.t("ev6", a["ev"] == 6):
        k = s32(k * 2)
    e.hit("cb_k%d_%s_ev%s" % (k, "player" if dfn["type"] == 0 else "hire" if hire(dfn) else
                                "mon" if dfn["type"] == 1 else "other", 6 if a["ev"] == 6 else "x"))
    e.hit("cb_r36_ge100", stat(dfn, 36) >= 100)
    e.hit("cb_r36_ge100_player", stat(dfn, 36) >= 100 and dfn["type"] == 0)
    e.hit("cb_r36_ge100_cut_all", stat(dfn, 36) >= 100 and tdiv(stat(dfn, 6), k) != 0)
    life = stat(dfn, 6)
    cb = tdiv(life, k)
    e.hit("cb_r36_ge100_left", stat(dfn, 36) >= 100 and s32(cb - muldiv(cb, 100, 100)) != 0)
    e.hit("cb_r36_mid_big", 0 < stat(dfn, 36) < 100 and abs(cb) > 0x100000)
    r36 = stat(dfn, 36)
    if e.c("r36_ge100", r36, ">=", 100):
        cb = s32(cb - muldiv(cb, 100, 100))
    elif e.c("r36_gt0", r36, ">", 0):
        cb = s32(cb - muldiv(cb, r36, 100))
    new = s32(life - cb)
    if e.c("new_le0", new, "<=", 0):
        new = 0
    return ("obs", OBS_SETSTAT, (a["pd"], 6, u32(new), 0), tuple(seed))


def gen_ow(rnd):
    c = Case("ow")
    ch = rnd.choice([0, -3, rnd.randint(1, 99), 100, rnd.getrandbits(32)])
    lvl = rnd.choice([None, 0, 1, 2, rnd.randint(2, 15), 15, 16, rnd.randint(16, 30), 30, 31, 45, 46, 60, 61,
                      rnd.randint(61, 120), rnd.randint(-10, 0), rnd.getrandbits(32)])
    att = put_unit(c, rnd, ATT, rnd.choice([0, 1]), rnd_cls(rnd, 0.1), {135: ch, 12: lvl}, [])
    dt = rnd.choice([0, 0, 1, 1, 1, 2, 3])
    dfn = put_unit(c, rnd, DEF, dt, rnd_cls(rnd), {}, [], md_flags=rnd.choice([0, 4, 8, 0xC, 2, rnd.getrandbits(16)]))
    ev = rnd.choice([5, 6, 6, rnd.randrange(10)])
    pa = 0 if rnd.random() < 0.03 else ATT
    pd = 0 if rnd.random() < 0.03 else DEF
    c.ecx, c.edx = rnd.getrandbits(32), ev
    c.args = [pa, pd, PKT, 135 << 16, rnd.getrandbits(32)]
    c.dumps = [(ATT + 0x20, 8)]
    c.a = dict(att=att if pa else None, dfn=dfn if pd else None, ev=ev, pa=pa, pd=pd, seed0=att["seed"])
    return c


def band(L, e):
    t = (9, 18, 27, 36, 45)
    if e.c("L_le1", L, "<=", 1):
        return 0
    if e.c("L_le15", L, "<=", 15):
        return s32((L - 1) * t[0])
    if e.c("L_le30", L, "<=", 30):
        return s32(s32((L - 15) * t[1]) + 14 * t[0])
    if e.c("L_le45", L, "<=", 45):
        return s32(s32((L - 30) * t[2]) + 15 * t[1] + 14 * t[0])
    if e.c("L_le60", L, "<=", 60):
        return s32(s32((L - 45) * t[3]) + 15 * (t[1] + t[2]) + 14 * t[0])
    return s32(s32((L - 60) * t[4]) + 15 * (t[1] + t[2] + t[3]) + 14 * t[0])


def m_ow(e, a):
    att, dfn = a["att"], a["dfn"]
    if not e.t("att_set", att is not None) or not e.t("def_set", dfn is not None):
        return ("ret", 0, tuple(a["seed0"]))
    seed = list(att["seed"])
    ch = stat(att, 135)
    if not e.c("ch_gt0", ch, ">", 0):
        return ("ret", 0, tuple(seed))
    r = lcg(seed) % 100
    if not e.c("r_lt_ch", r, "<", ch):
        return ("ret", 0, tuple(seed))
    L = stat(att, 12)
    L = L if e.c("L_gt1", L, ">", 1) else 1
    dmg = s32(band(L, e) + 40)
    e.hit("ow_player_ev6", dfn["type"] == 0 and a["ev"] == 6)
    e.hit("ow_player_evx", dfn["type"] == 0 and a["ev"] != 6)
    e.hit("ow_flag04_only", dfn["type"] == 1 and mon_type_flag(dfn, 4) and not mon_type_flag(dfn, 8))
    e.hit("ow_boss_no08", dfn["type"] == 1 and is_boss(dfn) and not mon_type_flag(dfn, 0xC))
    if e.t("def_player", dfn["type"] == 0):
        dmg = tdiv(dmg, 4)
        if e.t("ev6", a["ev"] == 6):
            dmg = tdiv(dmg, 2)
    elif e.t("def_mon", dfn["type"] == 1) and e.t("flag0c", mon_type_flag(dfn, 0xC)):
        dmg = tdiv(dmg, 2)
    return ("obs", OBS_STATE, (a["pa"], a["pd"], 0, 1, 200, 0x4A, u32(-dmg), 0x3E, 0), tuple(seed))


def gen_frz(rnd):
    c = Case("frz")
    s = rnd.choice([0, -2, 1, 2, rnd.randint(1, 10), rnd.randint(1, 40), rnd.getrandbits(32)])
    al = rnd.choice([None, rnd.randint(1, 99), rnd.randint(1, 20), rnd.randint(-10, 0), rnd.getrandbits(32)])
    dl = rnd.choice([None, rnd.randint(1, 99), rnd.randint(1, 20), rnd.getrandbits(32)])
    att = put_unit(c, rnd, ATT, rnd.choice([0, 1]), rnd_cls(rnd, 0.1), {134: s, 12: al}, [])
    dfn = put_unit(c, rnd, DEF, rnd.choice([0, 1, 1, 2]), rnd_cls(rnd), {12: dl}, [])
    ev = rnd.choice([5, 6, 6, rnd.randrange(10)])
    pa = 0 if rnd.random() < 0.03 else ATT
    pd = 0 if rnd.random() < 0.03 else DEF
    c.ecx, c.edx = rnd.getrandbits(32), ev
    c.args = [pa, pd, PKT, 134 << 16, rnd.getrandbits(32)]
    c.dumps = [(ATT + 0x20, 8), (FRZ_PKT, 0x70)]
    c.a = dict(att=att if pa else None, dfn=dfn if pd else None, ev=ev, pa=pa, pd=pd, game=c.ecx,
               seed0=att["seed"])
    return c


def m_frz(e, a):
    att, dfn = a["att"], a["dfn"]
    if not e.t("att_set", att is not None) or not e.t("def_set", dfn is not None):
        return ("ret", 0, tuple(a["seed0"]), None)
    seed = list(att["seed"])
    s = stat(att, 134)
    if not e.c("s_gt0", s, ">", 0):
        return ("ret", 0, tuple(seed), None)
    al, dl = stat(att, 12), stat(dfn, 12)
    x = s - 1
    x = x if e.c("x_ge0", x, ">=", 0) else 0
    if e.t("ev6_a", a["ev"] == 6):
        al = s32(al - 6)
    e.names.add("spec_x_minus1")          # control: E3's text, ((x - 1) * 4 ...) with x = max(stat 134 - 1, 0)
    xx = x - 1 if e.flip == "spec_x_minus1" else x
    ch = s32(s32(s32(s32(xx * 4) - dl) + al + 10) * 5)
    if e.t("ev6_b", a["ev"] == 6):
        ch = tdiv(ch, 3)
    ch = ch if e.c("ch_gt0", ch, ">", 0) else 0
    if e.c("ch_ge100", ch, ">=", 100):
        ch = 100
    r = lcg(seed) % 100
    if not e.c("r_lt_ch", r, "<", ch):
        return ("ret", 0, tuple(seed), None)
    ln = (ch - r) * 2 + 25
    if e.c("ln_le25", ln, "<=", 25):
        ln = 25
    elif e.c("ln_ge250", ln, ">=", 250):
        ln = 250
    e.hit("frz_hit_ev6", a["ev"] == 6)
    e.hit("frz_hit_evx", a["ev"] != 6)
    pk = [0] * (0x70 // 4)
    pk[0x34 // 4] = ln
    return ("obs", OBS_APPLY, (a["game"], a["pa"], a["pd"], 1, FRZ_PKT), tuple(seed), tuple(pk))


def gen_regen(rnd):
    c = Case("regen")
    s74 = rnd.choice([0, rnd.randint(-5000, -1), rnd.randint(-300, -1), rnd.randint(1, 3000), rnd.getrandbits(32),
                      -256, rnd.randint(-70000, -1)])
    life = rnd.choice([rnd.randint(0, 2000), rnd.randint(256, 600), rnd.randint(1, 1 << 20), 256, 255, 0,
                       rnd.randint(-100, -1)])
    mx = rnd.choice([rnd.randint(0, 2000), rnd.randint(1, 1 << 20), life, 100, 0, rnd.randint(-10, 300)])
    flag = rnd.random() < 0.8
    u = put_unit(c, rnd, ATT, rnd.choice([0, 0, 1]), rnd_cls(rnd), {74: s74, 6: life, 7: mx}, [], listflag=flag)
    chain = (rnd.choice([100, 100, 0x69, rnd.getrandbits(32)]), rnd.random() < 0.5)
    rewrite_list(c, rnd, ATT, u, chain=chain)
    c.regs = {"ESI": ATT}
    c.a = dict(u=u)
    return c


def m_regen(e, a):
    u = a["u"]
    s74 = stat(u, 74)
    if not e.t("s74_nz", s74 != 0):
        return ("ret", 1)
    hp = s32(stat(u, 6) + s74)
    mx = stat(u, 7)
    if e.c("hp_gt_max", hp, ">", mx):
        hp = mx
        if e.t("found", find_state_list(u, 100)):
            return ("obs", OBS_UNLINK, (ATT, ATT + SL_OFF))
    e.hit("regen_floor", hp < 0x100)
    e.hit("regen_floor_neg74", hp < 0x100 and s74 < 0)
    if e.c("hp_lt256", hp, "<", 0x100):
        hp = 0x100
    return ("obs", OBS_SETSTAT, (ATT, 6, u32(hp), 0))


# ----------------------------------------------------------------------------------------------- BuildDamage
BD_STATS = (0, 12, 17, 18, 21, 22, 25, 111, 120, 121, 122, 141, 337, 48, 49, 50, 51, 52, 53, 54, 55, 329, 330, 331,
            357, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 101, 103, 104, 106, 315, 326, 332, 172)


def bd_val(rnd, s):
    if s in (329, 330, 331, 357, 332, 25, 17, 18):          # percents
        return rnd.choice([0, 0, rnd.randint(1, 150), rnd.randint(-100, -1), -90, rnd.getrandbits(32)])
    if s == 172:
        return rnd.choice([0, 1, 2, 2, rnd.getrandbits(32)])
    if s in (141, 337):
        return rnd.choice([0, 0, rnd.randint(1, 99), 100, rnd.randint(-5, 0)])
    if s == 0:
        return rnd.choice([0, rnd.randint(10, 300), rnd.randint(-200, -1)])
    return rnd.choice([0, 0, rnd.randint(1, 40), rnd.randint(1, 500), rnd.randint(-40, -1), rnd.getrandbits(32),
                       rnd.choice([0x7FFFFF, 0x800000, 0x7FFFFFFF, 0x80000000])])


def gen_bd(rnd):
    c = Case("bd")
    at = rnd.choice([0, 0, 0, 1, 1, 1, 2, 3, 4])
    acls = rnd_cls(rnd, 0.3) if at == 1 else rnd.randrange(7)
    sv = {s: bd_val(rnd, s) for s in BD_STATS if rnd.random() < 0.45}
    flag = rnd.random() < 0.9
    att = put_unit(c, rnd, ATT, at, acls, sv, [], listflag=flag)
    c.put(ATT + 0x60, le32(0))
    e180 = {}
    for _ in range(rnd.choice([0, 0, 1, 2, 4])):
        e180[(180 << 16) | rnd.choice([0, rnd.randrange(1, MT_N), rnd.randrange(1, MT_N), MT_N, 0xFFFF])] = \
            rnd.choice([rnd.randint(1, 100), rnd.randint(-50, -1), rnd.getrandbits(32)])
    rewrite_list(c, rnd, ATT, att, extra=e180, chain=(rnd.choice([0x69, 0x69, rnd.getrandbits(32)]),
                                                      rnd.random() < 0.6))
    dt = rnd.choice([1, 1, 1, 1, 0, 2, 3])
    dcls = rnd_cls(rnd, 0.1) if dt == 1 else rnd.randrange(7)
    dfn = put_unit(c, rnd, DEF, dt, dcls, {31: rnd.choice([0, rnd.randint(1, 3000), rnd.getrandbits(32)])}, [])
    patch = {}
    if at == 1:
        patch.update(put_ms(c, rnd, acls, oa6=rnd.choice([0, 0, rnd.randint(1, 99), 100, rnd.getrandbits(8)])))
    if dt == 1:
        mt = rnd.choice([0, rnd.randrange(1, MT_N), rnd.randrange(1, MT_N), MT_N, 0xFFFF, rnd.getrandbits(16)])
        patch.update(put_ms(c, rnd, dcls, o0d=rnd.choice([0, 0x08, 0x10, 0x20, 0x28, rnd.getrandbits(8)]),
                            o1c=mt & 0xFF, o1d=mt >> 8))
    pk = [rnd.choice([0, 0, rnd.randint(1, 5000), rnd.randint(-500, -1), rnd.getrandbits(32)])
          for _ in range(PKT_SZ // 4)]
    pk[0] = rnd.choice([0, 1, 4, 8, 0x10, 0x1C, 0x1000, rnd.getrandbits(32)])
    pk[1] = (rnd.getrandbits(16) & rnd.choice([0, 0xFFFF, 0xFFDF, 0x20])) | (rnd.getrandbits(16) << 16)
    for off in (0x14, 0x18, 0x2C, 0x30, 0x34, 0x44):
        pk[off // 4] = rnd.choice([0, 0, rnd.randint(1, 100), rnd.randint(-50, -1), rnd.getrandbits(32)])
    conv = rnd.choice([0, 0, 1, 2, 3, 4, 5, 10, 11, 12, 6, 13, rnd.getrandbits(8)])
    w = pk[0x64 // 4]
    pk[0x64 // 4] = (w & 0xFFFF00FF) | (conv << 8)
    pk[0x68 // 4] = rnd.choice([0, rnd.randint(1, 100), rnd.randint(-50, 0), rnd.getrandbits(32), 100])
    pk[0x60 // 4] = rnd.choice([0, 0x10, 0x20, 0xF0, rnd.getrandbits(32)])
    c.put(PKT, b"".join(le32(x) for x in pk))
    crit = rnd.choice([0, 0, 1, rnd.getrandbits(32)])
    sd = rnd.choice([0, 0x80, 0x80, rnd.randint(1, 255), 0x40, 0xFF, 0x100, rnd.getrandbits(32)])
    pa = 0 if rnd.random() < 0.02 else ATT
    pd = 0 if rnd.random() < 0.02 else DEF
    c.ecx, c.edx = rnd.getrandbits(32), pa
    c.args = [pd, PKT, crit, sd]
    c.dumps = [(PKT, PKT_SZ), (ATT + 0x20, 8)]
    c.a = dict(att=att if pa else None, dfn=dfn if pd else None, pk=pk, crit=crit, sd=sd, patch=patch,
               game=c.ecx, pd=pd, seed0=att["seed"])
    return c


def align(u, e):
    """sub_006259B0_UnitAlignGet on the declared chain."""
    if e.t("al_type_gt1", u["type"] > 1):
        return 2
    if not e.t("al_found", find_state_list(u, 0x69)):
        return 0
    return stat(u, 172)


def roll_range(e, seed, hi, lo, plo, phi, field, tag):
    """COMBAT_RollRange(ECX hi, EAX field, att, lo, phi; EDX plo)."""
    if not e.c(tag + "_hi_gt0", hi, ">", 0):
        return field if field >= 0 else 0
    lo2 = s32(lo + muldiv(lo, plo, 100))
    hi2 = s32(hi + muldiv(hi, phi, 100))
    v = s32(field + lo2)
    if e.c(tag + "_hi_gt_lo", hi2, ">", lo2):
        v = s32(v + rng_range(seed, s32(hi2 - lo2)))
    return v if v >= 0 else 0


def elem(e, att, seed, mn_s, mx_s, m_s, field, tag):
    """COMBAT_RollElemStat(EAX max stat; min stat, mastery stat, 0, 0, field)."""
    mx = s32(stat(att, mx_s) << 8)
    if not e.c(tag + "_mx_ge8", mx, ">=", 8):
        e.hit("elem_nodraw_pos_field", field > 0)
        return field if field >= 0 else 0
    mn = s32(stat(att, mn_s) << 8)
    p = stat(att, m_s) if m_s != -1 else 0
    return roll_range(e, seed, mx, mn, p, p, field, tag)


def roll_phys(e, att, seed, edpct, phys, sd):
    """COMBAT_RollPhysical(ECX att, EDX 1; 0, 0, 0, edPct, phys, srcdam) with no weapon."""
    e.hit("rp_clamp_min", stat(att, 21) < 1)
    e.hit("rp_clamp_max", stat(att, 22) < 2)
    mn = stat(att, 21)
    mn = mn if e.c("rp_mn_ge1", mn, ">", 0) else 1
    mx = stat(att, 22)
    mx = mx if e.c("rp_mx_ge2", mx, ">", 1) else 2
    mn, mx = s32(mn << 8), s32(mx << 8)
    s111 = s32(stat(att, 111) << 8)
    mx, mn = s32(mx + s111), s32(mn + s111)
    if e.c("rp_mn_lt1", mn, "<", 1):
        mn = 0x100
    if e.c("rp_mx_le_mn", mx, "<=", mn):
        mx = s32(mn + 0x100)
    b = s32(edpct + stat(att, 25))
    b = s32(b + stat(att, 0))              # no weapon: the strength term
    if e.c("rp_b_le_m90", b, "<=", -90):
        b = -90
    v = phys
    if e.c("rp_mx_gt0", mx, ">", 0):
        lo = s32(muldiv(mn, s32(stat(att, 18) + b), 100) + mn)
        hi = s32(muldiv(mx, s32(stat(att, 17) + b), 100) + mx)
        v = s32(lo + phys)
        if e.c("rp_hi_gt_lo", hi, ">", lo):
            v = s32(v + rng_range(seed, s32(hi - lo)))
    v = v if v >= 0 else 0
    e.hit("rp_muldiv_differs", sd & 0xFF != 0x80 and muldiv(v, sd & 0xFF, 0x80) != tdiv(s32(v * (sd & 0xFF)), 128))
    e.names.add("spec_rp_plain")          # control: the physical scale as the elements' multiply and divide
    if e.flip == "spec_rp_plain" and sd & 0xFF != 0x80:
        return tdiv(s32(v * (sd & 0xFF)), 128)
    if e.t("rp_sd_not80", sd & 0xFF != 0x80):
        v = muldiv(v, sd & 0xFF, 0x80)
    return v


FLIP = [None]


def scale(v, sd):
    if FLIP[0] == "spec_scale_floor":      # control: an arithmetic shift (floor) in place of the truncating divide
        return s32(v * sd) >> 7
    return tdiv(s32(v * sd), 128)


def m_bd(e, a):
    att, dfn = a["att"], a["dfn"]
    if not e.t("att_set", att is not None) or not e.t("def_set", dfn is not None):
        return ("ret", tuple(u32(x) for x in a["pk"]), tuple(a["seed0"]))
    pk = [s32(x) for x in a["pk"]]
    seed = list(att["seed"])
    sdw = a["sd"]
    e.names.add("spec_scale_floor")
    FLIP[0] = e.flip
    if e.t("sd_zero", sdw & 0xFF == 0):
        sdw = (sdw & ~0xFF) | 0x80
    sd = sdw & 0xFF
    e.names.add("spec_sd_dword")          # control: srcdam read as the whole dword (0 -> 128) in BuildDamage's scales
    if e.flip == "spec_sd_dword":
        sd = a["sd"] if a["sd"] != 0 else 0x80
    F, R = 0, 1
    pk[F] = s32(pk[F] | 0x20)
    # step 1
    e.names.add("spec_s1_hireling")       # control: A's text, "a player or a hireling" in place of the alignment
    if e.flip == "spec_s1_hireling":
        s1 = att["type"] == 0 or hire(att) != 0
    else:
        s1 = e.t("s1_att_player", att["type"] == 0) or e.t("s1_align2", align(att, e) == 2)
    if s1 and e.t("s1_def_mon", dfn["type"] == 1):
        e.hit("s1_ran_" + ("player" if att["type"] == 0 else "type%d" % att["type"] if att["type"] != 1 else
                           "hire" if hire(att) else "mon"))
        v120 = stat(att, 120)
        if e.t("s120_nz", v120 != 0):
            e.names.add("spec_s120_sub")      # control: A's text, stat 31 - stat 120
            x = s32(stat(dfn, 31) - v120) if e.flip == "spec_s120_sub" else s32(stat(dfn, 31) + v120)
            x = x if e.c("s31_ge0", x, ">=", 0) else 0
            return ("obs", OBS_SETSTAT, (a["pd"], 0x1F, u32(x), 0), tuple(u32(v) for v in pk), tuple(seed))
        if e.t("demon", is_demon(dfn)):
            v = stat(att, 121)
            if e.c("s121_gt0", v, ">", 0):
                pk[3] = s32(pk[3] + v)
        if e.t("undead", is_undead(dfn)):
            v = stat(att, 122)                 # + 0: no weapon, so no blunt bonus
            if e.c("s122_gt0", v, ">", 0):
                pk[3] = s32(pk[3] + v)
        k = ms_rec(dfn)
        mt = struct.unpack("<h", bytes([ms_byte(k, 0x1C), ms_byte(k, 0x1D)]))[0] if k is not None else 0
        if e.c("mt_gt0", mt, ">", 0) and e.t("s180_list", att["listflag"]):
            ents = sorted(kk for kk in att["keys"] if kk >> 16 == 180)
            for kk in ents[:0x80]:
                ly = kk & 0xFFFF
                if e.c("ly_gt0", ly, ">", 0) and e.c("ly_lt_n", ly, "<", MT_N) and e.c("mt_lt_n", mt, "<", MT_N) \
                        and e.t("mt_match", MTY.test(mt, ly)):
                    pk[3] = s32(pk[3] + s32(att["keys"][kk]))
    # steps 2, 3
    e.hit("flag1_s141", bool(pk[F] & 1) and stat(att, 141) > 0)
    if not e.t("flag1", pk[F] & 1):
        pk[2] = roll_phys(e, att, seed, pk[3], pk[2], sdw)
        e.names.add("order_141_first")      # control: stat 141 drawn before stat 337
        order = (("s337", 337), ("s141", 141))
        if e.flip == "order_141_first":
            order = order[::-1]
        e.hit("crit_both", stat(att, 337) > 0 and stat(att, 141) > 0)
        for nm, s in order:
            ch = stat(att, s)
            if e.c(nm + "_gt0", ch, ">", 0):
                r = rng_range(seed, 100)
                if e.c(nm + "_r_lt", r, "<", ch):
                    pk[1] = s32(pk[1] | 0x2000)
                    pk[2] = s32(pk[2] * 2)
                    break
    # step 4
    for off, mn_s, mx_s, m_s, tag in ((0x10, 48, 49, 329, "fire"), (0x1C, 50, 51, 330, "light"),
                                      (0x24, 54, 55, 331, "cold"), (0x20, 52, 53, 357, "magic")):
        nodraw_pos = s32(stat(att, mx_s) << 8) < 8 and pk[off // 4] > 0
        v = elem(e, att, seed, mn_s, mx_s, m_s, pk[off // 4], tag)
        e.hit("elem_scaled_nodraw_pos", sd != 0x80 and nodraw_pos)
        e.hit("elem_scaled", sd != 0x80)
        e.hit("elem_scaled_neg_product", sd != 0x80 and s32(v * sd) < 0)
        if e.t("sd_not80", sd != 0x80):
            v = scale(v, sd)
        pk[off // 4] = v
    # step 5
    hr = hire(att)
    if e.t("s5_mon", att["type"] == 1) and e.t("s5_nohire", hr == 0):
        for bit, off, mn_s, tag in ((4, 0x38, 60, "life"), (8, 0x3C, 62, "mana"), (0x10, 0x40, 64, "stam")):
            if not e.t("s5_bit%x" % bit, pk[F] & bit):
                e.hit("drain_base_nz", pk[off // 4] != 0)
                v = elem(e, att, seed, mn_s, mn_s + 1, -1, pk[off // 4], tag)
                pk[off // 4] = s32(pk[off // 4] + scale(v, sd))
    elif e.t("s5_player", att["type"] == 0) or e.t("s5_hire", hr != 0):
        if not e.t("p5_bit4", pk[F] & 4):
            pk[0x38 // 4] = s32(pk[0x38 // 4] + stat(att, 60))
        if not e.t("p5_bit8", pk[F] & 8):
            pk[0x3C // 4] = s32(pk[0x3C // 4] + stat(att, 62))
        for s, b in ((103, 0x100), (104, 0x200), (106, 0x400)):
            if e.t("s%d_nz" % s, stat(att, s) != 0):
                pk[F] = s32(pk[F] | b)
    # step 6
    s57, s58 = stat(att, 57), stat(att, 58)
    p = stat(att, 332) if e.c("s58_gt0", s58, ">", 0) else 0
    e.names.add("spec_pois_add")          # control: A's text, poison += RollRange(57, 58) x srcdam / 128 if stat 58 > 0
    if e.flip == "spec_pois_add":
        if s58 > 0:
            pk[0x28 // 4] = s32(pk[0x28 // 4] + scale(roll_range(e, seed, s58, s57, p, p, 0, "pois"), sd))
    else:
        v = roll_range(e, seed, s58, s57, p, p, pk[0x28 // 4], "pois")
        pk[0x28 // 4] = scale(v, sd)
    if e.t("pois_nz", pk[0x28 // 4] != 0):
        s101 = stat(att, 101)
        if e.c("s101_gt0", s101, ">", 0):
            pk[0x2C // 4] = s32(pk[0x2C // 4] + s101)
        else:
            pk[0x2C // 4] = s32(pk[0x2C // 4] + stat(att, 59))
            d = stat(att, 326)
            if e.c("s326_gt1", d, ">", 1):
                pk[0x2C // 4] = tdiv(pk[0x2C // 4], d)
    if e.c("cold_gt0", pk[0x24 // 4], ">", 0):
        pk[0x30 // 4] = s32(pk[0x30 // 4] + scale(stat(att, 56), sd))
    e.hit("stun_s66_len0", pk[0x44 // 4] == 0 and stat(att, 66) != 0)
    e.hit("stun_s66_len_nz", pk[0x44 // 4] != 0 and stat(att, 66) != 0)
    if e.t("stun_zero", pk[0x44 // 4] == 0):
        pk[0x44 // 4] = s32(pk[0x44 // 4] + scale(stat(att, 66), sd))
    # step 7
    e.hit("burn_general", pk[0x14 // 4] != 0 or sd != 0x80)
    x = s32(s32(pk[0x14 // 4] * sd) + 0x13C)
    x = s32(x + rng_range(seed, 1))
    e.names.add("burn_c316")              # control: any other constant (here 256) in place of 316
    if e.flip == "burn_c316":
        x = s32(x - 60)
    e.names.add("burn_c317")              # control: 317 in place of 316
    if e.flip == "burn_c317":
        x = s32(x + 1)
    x = x if e.c("burn_ge0", x, ">=", 0) else 0
    pk[0x14 // 4] = s32(pk[0x14 // 4] + tdiv(x, 128))
    if e.t("burnlen_nz", pk[0x18 // 4] != 0):
        pk[0x18 // 4] = s32(pk[0x18 // 4] + scale(stat(att, 315), sd))
    # step 8
    if (e.t("s8_player", att["type"] == 0) or e.t("s8_hire", hr != 0)) and not e.t("s8_r20", pk[R] & 0x20):
        e.hit("event3_" + ("player" if att["type"] == 0 else "hire"))
        return ("obs", OBS_EVENT, (a["game"], 3, a["pd"], ATT, PKT), tuple(u32(v) for v in pk), tuple(seed))
    e.hit("event3_skip_r20", pk[R] & 0x20 and (att["type"] == 0 or hr != 0))
    e.hit("event3_skip_" + ("mon" if att["type"] == 1 else "other"), att["type"] != 0 and hr == 0)
    # step 9
    t = (pk[0x64 // 4] >> 8) & 0xFF
    if e.t("conv_nz", t != 0):
        m = muldiv(pk[2], pk[0x68 // 4], 100)
        ph = s32(pk[2] - m)
        pk[2] = ph if e.c("ph_gt0", ph, ">", 0) else 0
        e.hit("conv_t%s" % (t if t <= 12 else "other"))
        if e.t("t10", t == 10):
            t = (rng_range(seed, 5) + 1) & 0xFF
        if e.t("t1", t == 1):
            pk[0x10 // 4] = s32(pk[0x10 // 4] + m)
        elif e.t("t2", t == 2):
            pk[0x1C // 4] = s32(pk[0x1C // 4] + m)
        elif e.t("t3", t == 3):
            pk[0x20 // 4] = s32(pk[0x20 // 4] + m)
        elif e.t("t4", t == 4):
            pk[0x24 // 4] = s32(pk[0x24 // 4] + m)
            pk[0x30 // 4] = pk[0x30 // 4] if e.c("t4_ge50", pk[0x30 // 4], ">=", 50) else 50
        elif e.t("t5", t == 5):
            pk[0x28 // 4] = s32(pk[0x28 // 4] + tdiv(m, 8))
            pk[0x2C // 4] = pk[0x2C // 4] if e.c("t5_ge50", pk[0x2C // 4], ">=", 50) else 50
        elif e.t("t11", t == 11):
            pk[0x10 // 4] = s32(pk[0x10 // 4] + m)
            pk[0x18 // 4] = pk[0x18 // 4] if e.c("t11_ge50", pk[0x18 // 4], ">=", 50) else 50
        elif e.t("t12", t == 12):
            pk[0x24 // 4] = s32(pk[0x24 // 4] + m)
            pk[0x34 // 4] = pk[0x34 // 4] if e.c("t12_ge50", pk[0x34 // 4], ">=", 50) else 50
    # step 10 (MonCritDouble, part 1's crit family)
    k = ms_rec(att)
    if e.t("crit_mon", k is not None) and e.t("crit_nz", ms_byte(k, 0xA6) != 0):
        r = (lcg(seed) % 100) & 0xFF
        if e.c("crit_r_lt", r, "<", ms_byte(k, 0xA6)):
            for off in (0x08, 0x10, 0x1C, 0x20, 0x24, 0x28):
                pk[off // 4] = s32(pk[off // 4] * 2)
            if e.t("crit_taken", u32(pk[0x60 // 4]) & 0xF0):
                return ("obs", OBS_OVERLAY, (a["pd"], 0x36, 0), tuple(u32(v) for v in pk), tuple(seed))
            pk[0x60 // 4] = s32(pk[0x60 // 4] | 0x10)
    return ("ret", tuple(u32(v) for v in pk), tuple(seed))


GEN = {"cb": gen_cb, "ow": gen_ow, "frz": gen_frz, "regen": gen_regen, "bd": gen_bd}
MODEL = {"cb": m_cb, "ow": m_ow, "frz": m_frz, "regen": m_regen, "bd": m_bd}


def predict(fam, a, flip=None):
    e = E2(flip)
    try:
        out = p1.with_patch(a, lambda: MODEL[fam](e, a))
    except (TypeError, KeyError, IndexError, ZeroDivisionError):   # a reversed null or bound test reads nothing declared: no case can match
        return ("model-null",), e.names
    if flip is None:
        HITS.append(e.hits)
    return out, e.names


HITS = []


# ----------------------------------------------------------------------------------------------- files
def write_spec(d):
    im = img()
    with open(os.path.join(d, "monstats.bin"), "wb") as f:
        f.write(bytes(im.ms))
    with open(os.path.join(d, "isc.bin"), "wb") as f:
        f.write(bytes(ISC_N * ISC_SZ))
    with open(os.path.join(d, "montype.bin"), "wb") as f:
        f.write(b"".join(le32(x) for x in MTY.words))
    dt = bytearray(0x1000)
    for off, v in ((0xC4, NSTATES), (0xA78, MS), (0xA80, MS_N), (0xBCC, ISC), (0xBD4, ISC_N), (0xC40, MT_N),
                   (0xC44, MT), (0xC48, MT_STRIDE)):
        struct.pack_into("<I", dt, off, v)
    with open(os.path.join(d, "dt.bin"), "wb") as f:
        f.write(bytes(dt))
    lines = ["# plan 0066 S5e part 2 (tools/combat_s5e2_emu.py): declared tables",
             "dword %08x %08x" % (G_DT, DT),
             "load %08x %s" % (DT, os.path.join(d, "dt.bin")),
             "load %08x %s" % (MS, os.path.join(d, "monstats.bin")),
             "load %08x %s" % (ISC, os.path.join(d, "isc.bin")),
             "load %08x %s" % (MT, os.path.join(d, "montype.bin"))]
    lines += ["guard %08x" % x for x in FATAL + ALLOC]
    lines += ["observe %08x" % x for x in (OBS_SETSTAT, OBS_STATE, OBS_APPLY, OBS_UNLINK, OBS_EVENT, OBS_OVERLAY)]
    with open(os.path.join(d, "s5e2.mem"), "w") as f:
        f.write("\n".join(lines) + "\n")


def build(limit=None):
    cases = []
    for fam in FAMILIES:
        rnd = random.Random("n66t-s5e2-" + fam)
        for _ in range(NCASES[fam] if limit is None else min(limit, NCASES[fam])):
            cases.append(GEN[fam](rnd))
    return cases


def cmd_cases(d, limit=None):
    os.makedirs(d, exist_ok=True)
    write_spec(d)
    cases = build(limit)
    with open(os.path.join(d, "s5e2.cases"), "w") as f:
        for c in cases:
            f.write("\n".join(c.lines()) + "\n")
    print("cases %d -> %s" % (len(cases), os.path.join(d, "s5e2.cases")))


def observed(fam, c):
    """-> (outcome in the model's shape, call site or None)."""
    if "stop" in c:
        return ("stop", c["stop"], c["msg"]), None
    dw = lambda addr, n: struct.unpack("<%dI" % (n // 4), c["dumps"][addr])  # noqa: E731
    seed = dw(ATT + 0x20, 8) if ATT + 0x20 in c["dumps"] else None
    if "obs" in c:
        st, regs = c["stack"], c["regs"]
        ret = struct.unpack_from("<I", st, 0)[0]
        o = c["obs"]
        if o == OBS_STATE:
            off = int(regs["ecx"], 16) - int(regs["esp"], 16)
            args = struct.unpack_from("<9I", st, off) if 0 <= off <= 64 - 36 else None
            return ("obs", o, args, seed), ret
        if o == OBS_APPLY:
            a = struct.unpack_from("<3I", st, 4)
            return ("obs", o, (int(regs["ecx"], 16), int(regs["edx"], 16)) + a, seed, dw(FRZ_PKT, 0x70)), ret
        if o == OBS_SETSTAT:
            a = struct.unpack_from("<4I", st, 4)
        elif o == OBS_UNLINK:
            a = struct.unpack_from("<2I", st, 4)
        elif o == OBS_EVENT:
            a = (int(regs["ecx"], 16), int(regs["edx"], 16)) + struct.unpack_from("<3I", st, 4)
        elif o == OBS_OVERLAY:
            a = struct.unpack_from("<3I", st, 4)
        else:
            return ("obs?", o), ret
        if fam == "bd":
            return ("obs", o, a, dw(PKT, PKT_SZ), seed), ret
        if fam == "regen":
            return ("obs", o, a), ret
        return ("obs", o, a, seed), ret
    if c["pop"] != POP[fam]:
        return ("pop", c["pop"]), None
    if fam == "regen":
        return ("ret", c["eax"]), None
    if fam == "bd":
        return ("ret", dw(PKT, PKT_SZ), seed), None
    if fam == "frz":
        return ("ret", c["eax"], seed, None), None
    return ("ret", c["eax"], seed), None


def same(fam, want, got, a):
    if want[0] == "model-null" or want[0] != got[0] or len(want) != len(got):
        return False
    for w, g in zip(want, got):
        if w is None:                 # a part the model leaves free (an untouched seed of a null unit)
            continue
        if isinstance(w, (tuple, list)):
            if g is None or tuple(w) != tuple(g):
                return False
        elif w != g:
            return False
    return True


# reads the image holds as constants (traced only when outside a declared range)
CONST_READS = ((BITMASK, BITMASK + 128, "g_BitMask32 0x006CE268 (.rdata), read by UNIT_TestStateBit and DmgVsMonType"),
               (G_DT, G_DT + 4, "g_pDataTables 0x00744304 (.data), written by the spec's dword line"),
               (HPPCT_TABLE, HPPCT_TABLE + 36, "the PlayerHpPct table 0x006E1590 (.rdata), 9 dwords"),
               (JTAB, JTAB + 48, "the conversion switch table 0x0057BD94 (.text), 12 dwords"))


def account(reads, writes):
    bad = []
    for pc, addr, n, cnt in reads:
        if not any(lo <= addr and addr + n <= hi for lo, hi, _ in CONST_READS):
            bad.append(("R", pc, addr, n, cnt))
    for pc, addr, n, cnt in writes:
        bad.append(("W", pc, addr, n, cnt))
    return bad


def kind(want):
    if want[0] == "obs":
        return "obs:%x" % want[1]
    return want[0]


def cmd_check(d, limit=None, controls=True):
    cases = build(limit)
    calls, reads, writes = p1.read_out(os.path.join(d, "s5e2.out"))
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
    for x in acc:
        print("UNACCOUNTED %s pc=%08x addr=%08x n=%d count=%d" % x)
    stops = sum(1 for k in calls if "stop" in k)
    print("S5E2 total cases=%d mismatches=%d stops=%d controls=%d unseparated=%d controls_passed=%d unaccounted=%d"
          % (len(cases), bad, stops, len(ctl_lines), nsep0, ctl_bad, len(acc)))
    return 1 if bad or ctl_bad or acc else 0


def cmd_manifest(d, write):
    names = sorted(x for x in os.listdir(d) if os.path.isfile(os.path.join(d, x)) and x != "manifest.sha256")
    out = []
    for n in names:
        with open(os.path.join(d, n), "rb") as f:
            out.append("%s  %s" % (hashlib.sha256(f.read()).hexdigest(), n))
    text = "\n".join(out) + "\n"
    if write:
        with open(os.path.join(d, "manifest.sha256"), "w") as f:
            f.write(text)
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

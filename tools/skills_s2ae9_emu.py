#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S2ae part 9 (`lane/n66sa`): SummonSetLevel whole and handler 25 (Cyclone Armor) with the
stat setter whole, under Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java,
compared with the models below; plus `static`, the objdump listing of the functions the cases run.

    python3 -I tools/skills_s2ae9_emu.py cases [--dir D] [--limit N]   write D/s2ae.cases, D/s2ae.mem and the tables
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s2ae.cases D/s2ae.mem > D/s2ae.out
    python3 -I tools/skills_s2ae9_emu.py check [--dir D] [--limit N]   compare, account for traced reads, controls
    python3 -I tools/skills_s2ae9_emu.py reach [--limit N]             model outcomes and deciding tests per family
    python3 -I tools/skills_s2ae9_emu.py static                        objdump of the functions the cases run
    python3 -I tools/skills_s2ae9_emu.py wrap                          SummonSetLevel's 3L wrap bounds, computed
    python3 -I tools/skills_s2ae9_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66sa/s2ae/run9. Parts 1-8 (tools/skills_s2ae_emu.py, skills_s2ae2..8_emu.py) and their
run/ to run8/ are unchanged; this tool reuses part 1's check machinery and part 8's setter model and world
(skills_s2ae8_emu: set_stat_ex, unit_set_stat, put_world, the ItemStatCost rows of seed "n66sa-s2ae8-isc" with the
shipped bytes of its SHIPPED_ROWS) in its module state only. Every draw comes from random.Random("n66sa-s2ae9-<family>").

Declared inputs (S1e ruling 3): the units, lists, chains and packet are case memory, and only the fields named below
are written, so any other read of them is a traced, unaccounted read: the summon unit's +0x00 and +0x5C only (no class,
no MonStats pointer), the owner's +0x5C, the game's +0x6A, +0x6D and +0x74; MonLvl rows (stride 0x78) at ML with the
data table's +0xB70/+0xB74 written per case; the Skills record's +0x54, +0x56 and +0x80 per case.

Observed boundaries (ADR-0021; the case ends there, registers, stack arguments and dumps compared): part 8's four
(STATLIST_InsertEntry 0x00624C80, the resize 0x0040B4B0, the stat callback 0x0055B800, sub_006266C0_StatRecompute);
and for h25 sub_0064C040_UnitMarkUpdated (from 0x00639E76, inside sub_00639E30_UnitSetStateBit) and STATE_Set
0x00639DB0 (from 0x005C893F).

Families (rows: d = skills/dispatch):
  ssl  sub_005C49E0_SummonSetLevel (ECX game, EDX owner; summon, level, bonus), whole: STATS_GetUnitStat 0x00625480
       -> 0x00624F60, sub_00627260_UnitSetStat (part 8's model), the MonLvl row, sub_006272B0_UnitAddStat ->
       0x00627030 (search, add, RemoveEntry, Propagate, MarkClientDirty) twice.                     d142, d143
  h25  sub_005C87A0_StatEv25CycloneArmor (unit, -, packet, skill, -): UNIT_FindStatListByState 0x006256B0 ->
       0x00625650, sub_00625D00 -> 0x00625350 -> 0x00624ED0 (base stats), 0x005C8780 (the absorb step),
       STATLIST_SetStat 0x00627150 -> STATLIST_SetStatEx (part 8's model), sub_00483360_MulDiv, and
       sub_00639E30_UnitSetStateBit with 0x00625BE0 to its UnitMarkUpdated call.                         d129

Controls as parts 1-8: every named test reversed alone, every ordered compare's strictness switched alone; `sep`
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
import skills_s2ae6_emu as P6  # noqa: E402
import skills_s2ae7_emu as P7  # noqa: E402
import skills_s2ae8_emu as P8  # noqa: E402
from combat_s5e_emu import u32, s32, le32, tdiv, G_DT, DT, FATAL, ALLOC, ISC, ISC_N, ISC_SZ, NSTATES, BITMASK  # noqa: E402
from skills_s2ae8_emu import Hit, wd, find8, remove, propagate, mark_dirty, hit_out, dumped  # noqa: E402

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66sa", "s2ae", "run9")
FNS = {"ssl": 0x005C49E0, "h25": 0x005C87A0}
FAMILIES = ("ssl", "h25")
NCASES = {"ssl": 6000, "h25": 8000}
POP = {"ssl": 0xC, "h25": 0x14}
p1.FNS.update(FNS)
B_SAME = B.same                            # part 1's comparison, taken before P8.install() replaces B.same

F_INSERT, F_POOL, F_CB, F_RECOMP = P8.F_INSERT, P8.F_POOL, P8.F_CB, P8.F_RECOMP
OBS_MARK, OBS_STSET = 0x0064C040, 0x00639DB0
OBSERVES = (F_INSERT, F_POOL, F_CB, F_RECOMP, OBS_MARK, OBS_STSET)
NARGS = {F_INSERT: 1, F_POOL: 4, F_CB: 4, F_RECOMP: 2, OBS_MARK: 1, OBS_STSET: 3}
REGS = {F_INSERT: ("eax", "esi"), F_POOL: ("ecx", "edx"), F_CB: ("ecx", "edx"), F_RECOMP: ("ecx", "edx"),
        OBS_MARK: (), OBS_STSET: ()}
SU, SL = P8.SU, P8.SU + P8.SL_OFF          # the summon / the handler's unit; the list put_world builds
OWN, OL = 0x23400000, 0x23400200           # ssl: the owner and its list
OA = 0x23400400                            # ssl: the owner's live array
GM = 0x23500000                            # ssl: the game
ML, ML_SZ = 0x23600000, 0x78               # ssl: the MonLvl rows
L0, SB = 0x23700000, 0x23700100            # h25: the unit's own list, its state arrays (+0x58)
DN = 0x23710000                            # h25: decoy lists of the state chains (0x100 apart)
PK = 0x23800000                            # h25: the damage packet
SK, SK_N, SK_SZ = P6.SK, P6.SK_N, P6.SK_SZ
NW = tdiv(NSTATES + 31, 32)                # 0x00625BE0: the words of one state bit set


def ib(stat, off):
    return P8.ib(stat, off)


def sx16(v):
    return P8.sx16(v)


# ----------------------------------------------------------------------------------------------- shared models
def base_get(e, M, sl, stat):
    """sub_00625D00 -> 0x00625350 -> 0x00624ED0: the list's +0x24 base array, signed search; +0x05 bit 2 clear."""
    if sl == 0 or not 0 <= s32(stat) < ISC_N:
        return 0
    i = find8(M, sl + 0x24, u32(stat << 16))
    if i is None:
        return 0
    if ib(stat, 5) & 4:
        raise KeyError("ItemStatCost +0x05 bit 2 set: the getter's minimum is not modelled")
    return s32(M.d(M.d(sl + 0x24) + 8 * i + 4))


def live_get(M, u, stat):
    """STATS_GetUnitStat 0x00625480 -> 0x00624F60 (layer 0): 0 for no unit or no list; +0x05 bit 2 clear."""
    if u == 0:
        return 0
    sl = M.d(u + 0x5C)
    if sl == 0 or not 0 <= stat < ISC_N:
        return 0
    off = 0x48 if M.d(sl + 0x10) & 0x80000000 else 0x24
    i = find8(M, sl + off, u32(stat << 16))
    if i is None:
        return 0
    if ib(stat, 5) & 4:
        raise KeyError("ItemStatCost +0x05 bit 2 set")
    return s32(M.d(M.d(sl + off) + 8 * i + 4))


def add_stat_ex(e, M, sl, stat, val, param):
    """0x00627030 (list, stat, value, param): nothing for no list or a zero value; the entry += value (an absent key:
    STATLIST_InsertEntry, observed), RemoveEntry at 0, Propagate(value), MarkClientDirty."""
    if not e.t("ax_list", sl != 0) or not e.t("ax_val", val != 0):
        return
    key = u32((stat << 16) + (param & 0xFFFF))
    i = find8(M, sl + 0x24, key)
    if not e.t("ax_found", i is not None):
        raise Hit(F_INSERT, 0x00627070, (key, sl + 0x24), (M.d(sl),))
    ent = M.d(sl + 0x24) + 8 * i
    new = u32(M.d(ent + 4) + val)
    wd(M, ent + 4, new)
    if e.t("ax_zero", new == 0):
        remove(e, M, sl + 0x24, i, M.d(sl))
    propagate(e, M, sl, key, u32(val))
    if e.t("ax_ext", M.d(sl + 0x10) & 0x80000000) and e.t("ax_8", M.d(sl + 8) == 0):
        mark_dirty(e, M, sl, key)


def unit_add_stat(e, M, u, stat, val, param):
    """sub_006272B0_UnitAddStat: a zero value returns at once; the unit is not tested (+0x5C read)."""
    if not e.t("ua_val", val != 0):
        return
    add_stat_ex(e, M, M.d(u + 0x5C), stat, val, param)


# ----------------------------------------------------------------------------------------------- ssl
def gen_ssl(rnd):
    c = P7.Case("ssl")
    typ = rnd.choice([1, 1, 1, 0, 2, 3])
    c.put(SU, le32(typ))
    c.put(SU + 0x5C, le32(SL))
    c.put(SL, P6.rbytes(rnd, 0x64))
    k12, k31, k19 = 12 << 16, 31 << 16, 19 << 16
    ext = rnd.random() < 0.85
    ents = {rnd.randrange(1, ISC_N) << 16: rnd.getrandbits(32) for _ in range(rnd.randrange(6))}
    for k in (k12, k31, k19):
        if rnd.random() < 0.92:
            ents[k] = rnd.choice([0, 1, rnd.randint(1, 120), rnd.randint(1, 3000), rnd.getrandbits(32)])
        else:
            ents.pop(k, None)
    if ext:
        live = {k: v for k, v in ents.items() if rnd.random() < 0.6}
        for k in (k12, k31, k19):
            if rnd.random() < 0.93:
                live[k] = rnd.choice([ents.get(k, 0), rnd.randint(1, 3000), rnd.getrandbits(32), 1])
        base = ents
    else:
        live, base = ents, None
    dumps = P8.put_world(c, rnd, SU, SL, k12, live, ext, base=base, wide=True)
    # the owner: its +0x5C list holding (or not) stat 12 at layer 0 in its live array
    owner = 0 if rnd.random() < 0.04 else OWN
    if owner:
        olist = 0 if rnd.random() < 0.03 else OL
        c.put(OWN + 0x5C, le32(olist))
        if olist:
            c.put(OL, P6.rbytes(rnd, 0x64))
            oext = rnd.random() < 0.7
            c.put(OL + 0x10, le32((0x80000000 if oext else 0) | rnd.getrandbits(31)))
            L = rnd.choice([0, 1, 2, 3, 4, 5, 30, 84, 86, 98, 99, 110, rnd.randint(1, 120), rnd.randint(1, 120),
                            rnd.randint(-8, -1), rnd.getrandbits(32), 0x55555556, 0x7FFFFFFF, 0x80000000])
            oe = {rnd.randrange(1, ISC_N) << 16 | rnd.choice([0, 0, 1]): rnd.getrandbits(32) for _ in range(rnd.randrange(6))}
            if rnd.random() < 0.93:
                oe[k12] = u32(L)
            else:
                oe.pop(k12, None)
            oe.pop(k12 | 1, None)
            oe = sorted(oe.items(), key=lambda kv: s32(kv[0]))
            P8.put_arr(c, OA, oe, len(oe))
            P8.desc(c, OL + (0x48 if oext else 0x24), OA, len(oe), len(oe))
    level = rnd.choice([0] * 7 + [rnd.randint(1, 120), 1, rnd.randint(-5, -1), rnd.getrandbits(32)])
    bonus = rnd.choice([0, 1, rnd.randint(1, 25), rnd.randint(1, 25), 20, rnd.randint(-30, -1), rnd.getrandbits(32)])
    # the game: difficulty byte +0x6D, expansion byte +0x6A and dword +0x74
    c.put(GM + 0x6A, bytes([rnd.choice([0, 0, 1, rnd.getrandbits(8)])]))
    c.put(GM + 0x6D, bytes([rnd.choice([0, 1, 2, 0, 1, 2, 3, rnd.getrandbits(8)])]))
    c.put(GM + 0x74, le32(rnd.choice([0, 0, 1, rnd.getrandbits(32)])))
    # MonLvl: the count and the rows the level can index
    n = rnd.choice([rnd.randint(100, 130), 111, 111, rnd.randint(1, 100), rnd.randint(1, 5)]) if rnd.random() < 0.95 \
        else rnd.choice([0, rnd.randint(-5, -1)])
    c.put(DT + 0xB70, le32(ML))
    c.put(DT + 0xB74, le32(u32(n)))
    rows = set()
    for v in (level, s32(level), 0, n - 1, n - 2, rnd.randint(0, 130)):
        if 0 <= s32(v) < max(n, 0):
            rows.add(s32(v))
    if level == 0 and owner and M_owner_level(c) is not None:
        Lv = M_owner_level(c)
        for v in range(-2, 3):
            q = s32(tdiv(s32(3 * Lv), 4) + s32(bonus) + v)
            for x in (q, Lv, 1):
                if 0 <= x < max(n, 0):
                    rows.add(x)
    c.ecx, c.edx = GM, owner
    c.args = [SU, u32(level), u32(bonus)]
    for _ in range(4):        # the row the reading indexes, found by the model on the case itself, joins the rows
        for r in sorted(rows):
            if not any(ML + r * ML_SZ + i in c.w for i in range(ML_SZ)):
                c.put(ML + r * ML_SZ, struct.pack("<30I", *(u32(rnd.choice([0, rnd.randint(1, 3000),
                                                                              rnd.randint(1, 400), rnd.getrandbits(32),
                                                                              rnd.randint(-50, -1)]))
                                                            for _ in range(30))))
        P7.finish(c, dumps)
        try:
            m_ssl(p1.E(None), c.a, strict=True)
            break
        except KeyError as x:
            ad = x.args[0] if x.args and isinstance(x.args[0], int) else None
            if ad is None or not ML <= ad < ML + 200 * ML_SZ:
                break
            rows.add((ad - ML) // ML_SZ)
    return c


def M_owner_level(c):
    try:
        return live_get(P6.Mem(c.w), OWN, 12)
    except KeyError:
        return None


def m_ssl(e, a, strict=False):
    M = P6.Mem(a["w"])
    game, owner = a["ecx"], a["edx"]
    summon, level, bonus = a["args"]
    try:
        lvl = s32(level)
        if not e.c("lv_pos", lvl, ">", 0):
            L = live_get(M, owner, 12)
            t = s32(3 * L)
            q = tdiv(t, 4)
            e.names.update(("spec_floor", "spec_ceil"))
            if e.flip == "spec_floor":
                q = t // 4
            elif e.flip == "spec_ceil":
                q = -((-t) // 4)
            nn = s32(q + s32(bonus))
            m1 = nn if e.c("n_gt1", nn, ">", 1) else 1
            if e.c("cap_ge", m1, ">=", L):
                lvl = L
            else:
                lvl = nn if e.c("n_gt1b", nn, ">", 1) else 1
            if e.t("lvl_nz", lvl != 0):
                P8.unit_set_stat(e, M, summon, 12, u32(lvl), 0)
        else:
            P8.unit_set_stat(e, M, summon, 12, u32(lvl), 0)
        n = s32(M.d(DT + 0xB74))
        last = s32(n - 1)
        if not e.c("ml_lt", lvl, "<", last):
            lvl = last
        if not e.c("ml_ge0", lvl, ">=", 0) or not e.c("ml_ltn", lvl, "<", n):
            return ("ret", 0, dumped(M, a["dumps"]))
        rec = u32(M.d(DT + 0xB70) + lvl * ML_SZ)
        b = M.b(game + 0x6D)
        df = 0 if not e.t("df_nz", b != 0) else (2 if e.c("df_ge2", b, ">=", 2) else b)
        x = 1 if e.t("x_6a", M.b(game + 0x6A) != 0) or e.t("x_74", M.d(game + 0x74) != 0) else 0
        e.names.add("spec_cells")
        if e.flip == "spec_cells":
            i1, i2 = 3 * df + x, 3 * df + x + 2
        else:
            i1, i2 = df + 3 * x, df + 3 * (x + 2)
        if strict:
            M.d(rec + 4 * i1), M.d(rec + 4 * i2)
            return None
        unit_add_stat(e, M, summon, 31, M.d(rec + 4 * i1), 0)
        unit_add_stat(e, M, summon, 19, M.d(rec + 4 * i2), 0)
    except Hit as h:
        if strict:
            return None
        return hit_out(h, M, a["dumps"])
    return ("ret", 1, dumped(M, a["dumps"]))


# ----------------------------------------------------------------------------------------------- h25
def gen_h25(rnd):
    c = P7.Case("h25")
    c.put(SU + 0x5C, le32(0 if rnd.random() < 0.01 else L0))
    c.put(L0 + 0x10, le32((0x80000000 if rnd.random() < 0.98 else 0) | rnd.getrandbits(31)))
    c.put(L0 + 0x58, le32(SB))
    c.put(SB, P6.rbytes(rnd, 8 * NW))
    skill = rnd.randrange(SK_N) if rnd.random() < 0.96 else rnd.choice([-1, SK_N, rnd.getrandbits(32)])
    state = rnd.randrange(1, NSTATES) if rnd.random() < 0.96 else rnd.choice([0, -1, NSTATES, rnd.getrandbits(16)])
    s56 = rnd.randrange(1, ISC_N) if rnd.random() < 0.95 else rnd.choice([84, -1, ISC_N, rnd.getrandbits(16)])
    s54 = rnd.randrange(1, ISC_N) if rnd.random() < 0.94 else rnd.choice([84, s56, -3, ISC_N + 5])
    if 0 <= s32(skill) < SK_N:
        r = SK + s32(skill) * SK_SZ
        c.put(r + 0x54, struct.pack("<H", s54 & 0xFFFF))
        c.put(r + 0x56, struct.pack("<H", s56 & 0xFFFF))
        c.put(r + 0x80, struct.pack("<H", state & 0xFFFF))
    # the state chains (+0x3C, +0x40): decoys with other states, the target list somewhere or nowhere
    st16 = sx16(state)
    where = rnd.choice(["3c", "40"]) if rnd.random() < 0.95 else "none"
    chains = {"3c": [], "40": []}
    k = 0
    for ch in ("3c", "40"):
        for _ in range(rnd.choice([0, 0, 1, 2, 3])):
            d = DN + 0x100 * k
            k += 1
            other = rnd.randrange(1, NSTATES)
            while other == st16:
                other = rnd.randrange(1, NSTATES)
            c.put(d + 0x14, le32(other))
            chains[ch].append(d)
    if where != "none":
        chains[where].insert(rnd.randrange(len(chains[where]) + 1), SL)
    c.put(SL, P6.rbytes(rnd, 0x64))
    for ch, off in (("3c", 0x3C), ("40", 0x40)):
        lst = chains[ch]
        c.put(L0 + off, le32(lst[0] if lst else 0))
        for i, d in enumerate(lst):
            c.put(d + 0x2C, le32(lst[i + 1] if i + 1 < len(lst) else 0))
    c.put(SL + 0x14, le32(u32(st16) if where != "none" else rnd.randrange(NSTATES)))
    # the target list's base entries: max (s56), pool (s54), the shown percent (84)
    k54, k56, k84 = u32(s54 << 16), u32(s56 << 16), 84 << 16
    mx = rnd.choice([rnd.randint(1, 5000), rnd.randint(1, 400), rnd.randint(1, 400), 1]) if rnd.random() < 0.92 else rnd.choice([0, rnd.randint(-50, -1), rnd.getrandbits(32)])
    pool = rnd.choice([rnd.randint(1, 5000), rnd.randint(1, 400), 0, rnd.randint(-50, -1), rnd.getrandbits(32)])
    if rnd.random() < 0.3 and s32(mx) > 0:
        pool = rnd.randint(1, s32(mx))
    old = rnd.choice([0, rnd.randint(0, 100), rnd.randint(0, 100), rnd.randint(50, 100), 100, rnd.getrandbits(32)])
    ents = {rnd.randrange(1, ISC_N) << 16: rnd.getrandbits(32) for _ in range(rnd.randrange(5))}
    for kk, v, p in ((k84, old, 0.85), (k56, mx, 0.97), (k54, pool, 0.96)):
        if rnd.random() < p:
            ents[kk] = u32(v)
        else:
            ents.pop(kk, None)
    ext = rnd.random() < 0.5
    if ext:
        live = {kk: v for kk, v in ents.items() if rnd.random() < 0.5}
        for kk in (k54, k84):
            if rnd.random() < 0.9:
                live[kk] = rnd.choice([ents.get(kk, 0), rnd.randint(1, 3000), rnd.getrandbits(32)])
        base = ents
    else:
        live, base = ents, None
    dumps = P8.put_world(c, rnd, SU, SL, k54, live, ext, base=base, wide=True)
    # the packet: fire +0x10, cold +0x24, lightning +0x1C (absorbed in that order while positive)
    c.put(PK, P6.rbytes(rnd, 0x40))
    for off in (0x10, 0x24, 0x1C):
        c.put(PK + off, le32(u32(rnd.choice([0, rnd.randint(1, 300), rnd.randint(1, 3000), rnd.randint(-40, -1),
                                             rnd.getrandbits(32)]))))
    pk = 0 if rnd.random() < 0.01 else PK
    unit = 0 if rnd.random() < 0.01 else SU
    dumps = dumps + [(PK, 0x40), (SB, 8 * NW)]
    c.args = [unit, rnd.getrandbits(32), pk, u32(skill), rnd.getrandbits(32)]
    return P7.finish(c, dumps)


def absorb(e, M, name, pool, p):
    """0x005C8780 (EAX pool, EDX the packet field): the field absorbs all of a smaller pool, or the pool all of it."""
    v = s32(M.d(p))
    if e.c(name, pool, ">", v):
        wd(M, p, 0)
        return s32(pool - v)
    wd(M, p, u32(v - pool))
    return 0


def state_bit(e, M, u, state):
    """sub_00639E30_UnitSetStateBit(unit, state, 1) to its UnitMarkUpdated call: the second bit set of the unit's
    list (+0x58 + NW words) gets the state's bit."""
    sl = M.d(u + 0x5C)
    if not e.t("sb_list", sl != 0) or not e.t("sb_ext", M.d(sl + 0x10) & 0x80000000):
        return
    arr = u32(M.d(sl + 0x58) + 4 * NW)
    if not e.t("sb_arr", arr != 0):
        return
    if not e.c("sb_ge0", state, ">=", 0) or not e.c("sb_ltn", state, "<", NSTATES):
        return
    w = arr + 4 * (state >> 5)
    wd(M, w, M.d(w) | (1 << (state & 31)))
    raise Hit(OBS_MARK, 0x00639E76, (), (u,))


def find_by_state(e, M, u, state):
    """UNIT_FindStatListByState 0x006256B0 -> 0x00625650: the +0x3C chain, then the +0x40 chain, by +0x14."""
    L = M.d(u + 0x5C)
    if not e.t("fs_list", L != 0) or not e.t("fs_ext", M.d(L + 0x10) & 0x80000000):
        return 0
    if not e.t("fs_state", state != 0):
        return 0
    for off in (0x3C, 0x40):
        cur = M.d(L + off)
        for _ in range(16):
            if cur == 0:
                break
            if e.t("fs_eq", M.d(cur + 0x14) == u32(state)):
                return cur
            cur = M.d(cur + 0x2C)
    return 0


def m_h25(e, a):
    M = P6.Mem(a["w"])
    unit, _, pk, skill, _ = a["args"]
    try:
        if not e.t("u_nz", unit != 0) or not e.t("pk_nz", pk != 0):
            return ("ret", 0, dumped(M, a["dumps"]))
        if not e.c("sk_ge0", s32(skill), ">=", 0) or not e.c("sk_ltn", s32(skill), "<", SK_N):
            return ("ret", 0, dumped(M, a["dumps"]))
        rec = SK + s32(skill) * SK_SZ
        st = sx16(M.h(rec + 0x80))
        if not e.c("st_ge0", st, ">=", 0) or not e.c("st_ltn", st, "<", NSTATES):
            return ("ret", 0, dumped(M, a["dumps"]))
        sl = find_by_state(e, M, unit, st)
        if not e.t("sl_nz", sl != 0):
            return ("ret", 0, dumped(M, a["dumps"]))
        s56 = sx16(M.h(rec + 0x56))
        if not e.c("s56_ge0", s56, ">=", 0) or not e.c("s56_ltn", s56, "<", ISC_N):
            return ("ret", 0, dumped(M, a["dumps"]))
        mx = base_get(e, M, sl, s56)
        if not e.c("mx_pos", mx, ">", 0):
            return ("ret", 0, dumped(M, a["dumps"]))
        s54 = sx16(M.h(rec + 0x54))
        if not e.c("s54_ge0", s54, ">=", 0) or not e.c("s54_ltn", s54, "<", ISC_N):
            return ("ret", 0, dumped(M, a["dumps"]))
        pool = base_get(e, M, sl, s54)
        if e.t("pool_nz", pool != 0):
            order = (0x10, 0x24, 0x1C)
            e.names.add("spec_order")
            if e.flip == "spec_order":
                order = (0x10, 0x1C, 0x24)
            for off in order:
                if e.c("pk%x_pos" % off, s32(M.d(pk + off)), ">", 0):
                    pool = absorb(e, M, "ab%x" % off, pool, pk + off)
            P8.set_stat_ex(e, M, sl, s54, u32(pool), 0)
            if e.c("left_pos", pool, ">", 0):
                pct = p1.muldiv(pool, 100, mx)
                old = base_get(e, M, sl, 84)
                if e.c("pct_ge5", s32(pct - old), ">=", 5):
                    state_bit(e, M, unit, st)
                    P8.set_stat_ex(e, M, sl, 84, u32(pct), 0)
                return ("ret", 1, dumped(M, a["dumps"]))
        raise Hit(OBS_STSET, 0x005C8944, (), (unit, u32(st), 0))
    except Hit as h:
        return hit_out(h, M, a["dumps"])


GEN = {"ssl": gen_ssl, "h25": gen_h25}
MODEL = {"ssl": m_ssl, "h25": m_h25}


# ----------------------------------------------------------------------------------------------- spec, check
def write_spec(d):
    P8.merge_tables()
    ms, ms2, sk = P6.tables()
    for name, data in (("skills.bin", sk), ("isc.bin", P8.isc_rows())):
        with open(os.path.join(d, name), "wb") as f:
            f.write(bytes(data))
    dt = bytearray(0x1000)
    for off, v in ((0xC4, NSTATES), (0xB98, SK), (0xBA0, SK_N), (0xBCC, ISC), (0xBD4, ISC_N)):
        struct.pack_into("<I", dt, off, v)
    with open(os.path.join(d, "dt.bin"), "wb") as f:
        f.write(bytes(dt))
    lines = ["# plan 0066 S2ae part 9 (tools/skills_s2ae9_emu.py): declared tables",
             "dword %08x %08x" % (G_DT, DT),
             "dword %08x %08x" % (P8.SSE_FLAG, 1),
             "load %08x %s" % (DT, os.path.join(d, "dt.bin")),
             "load %08x %s" % (SK, os.path.join(d, "skills.bin")),
             "load %08x %s" % (ISC, os.path.join(d, "isc.bin"))]
    lines += ["guard %08x" % x for x in FATAL + ALLOC if x not in OBSERVES]
    lines += ["observe %08x" % x for x in OBSERVES]
    with open(os.path.join(d, "s2ae.mem"), "w") as f:
        f.write("\n".join(lines) + "\n")


def observed(fam, k):
    if "stop" in k:
        return ("stop", k["stop"], k.get("msg")), None
    dumps = k["dumps"]
    dt = tuple(dumps[va] for va in sorted(dumps))
    if "obs" in k:
        st = k["stack"]
        rt = struct.unpack_from("<I", st, 0)[0]
        n = NARGS.get(k["obs"], 0)
        regs = tuple(int(k["regs"][r], 16) for r in REGS.get(k["obs"], ()))
        return ("obs", k["obs"], regs, struct.unpack_from("<%dI" % n, st, 4), dt, rt), None
    if k["pop"] != POP[fam]:
        return ("pop", k["pop"]), None
    return ("ret", k["eax"], dt), None


def norm(fam, want):
    return want


def same(want, got):
    """Part 8's comparison, with part 1's for the other outcomes (model-null, stop, pop)."""
    if want[0] != got[0]:
        return False
    if want[0] == "ret":
        return (want[1] is None or want[1] == got[1]) and (want[2] is None or tuple(want[2]) == tuple(got[2]))
    if want[0] == "obs":
        return len(want) == len(got) and all(w is None or w == g for w, g in zip(want, got))
    return B_SAME(want, got)


def predict(fam, a, flip=None):
    e = p1.E(flip)
    try:
        out = MODEL[fam](e, a)
    except (TypeError, KeyError, IndexError, AttributeError, ZeroDivisionError, struct.error):
        return ("model-null",), e.names
    return out, e.names


def install():
    P8.install()
    B.FNS, B.FAMILIES, B.NCASES, B.POP, B.SITE = FNS, FAMILIES, NCASES, POP, P8.NoSite()
    B.GEN, B.MODEL = GEN, MODEL
    B.observed, B.norm, B.account, B.write_spec, B.predict, B.same = observed, norm, P8.account, write_spec, predict, same
    B.Case = P7.Case

    def build(limit=None):
        cases = []
        for fam in FAMILIES:
            rnd = random.Random("n66sa-s2ae9-" + fam)
            for _ in range(NCASES[fam] if limit is None else min(limit, NCASES[fam])):
                cases.append(GEN[fam](rnd))
        return cases
    B.build = build


# ----------------------------------------------------------------------------------------------- static reads
STATIC = (
    ("ssl", 0x005C49E0, 0x005C4AF2), ("getunitstat", 0x00625480, 0x006254DE), ("getvalue", 0x00624F60, 0x00624FD8),
    ("unitaddstat", 0x006272B0, 0x006272D1), ("addstatex", 0x00627030, 0x006270AB),
    ("h25", 0x005C87A0, 0x005C897B), ("absorb", 0x005C8780, 0x005C8796), ("findbystate", 0x006256B0, 0x006256D8),
    ("findbystate2", 0x00625650, 0x006256A8), ("basestat", 0x00625D00, 0x00625D09),
    ("basestat2", 0x00625350, 0x006253A3), ("basestat3", 0x00624ED0, 0x00624F36),
    ("setstat", 0x00627150, 0x00627170), ("statebit", 0x00639E30, 0x00639E8D), ("statebits", 0x00625BE0, 0x00625C1F),
    ("markupdated", 0x0064C040, 0x0064C0BB), ("stateset", 0x00639DB0, 0x00639DE0),
    ("freeifplain", 0x00626CD0, 0x00626D36), ("statlistfree", 0x00626C00, 0x00626CD0),
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
    cases = B.build(limit)
    for fam in FAMILIES:
        out, tests = {}, {}
        for c in cases:
            if c.fam != fam:
                continue
            want, names = predict(fam, c.a)
            k = want[0] if want[0] != "obs" else "obs:%08x@%08x" % (want[1], want[5])
            if want[0] == "ret":
                k += "=%d" % want[1]
            out[k] = out.get(k, 0) + 1
            for nm in names:
                if not nm.endswith("~") and not nm.startswith("spec_"):
                    alt = predict(fam, c.a, flip=nm)[0]
                    if not same(want, alt) or not same(alt, want):
                        tests[nm] = tests.get(nm, 0) + 1
        print("REACH %s outcomes %s" % (fam, " ".join("%s:%d" % kv for kv in sorted(out.items()))))
        print("REACH %s deciding %s" % (fam, " ".join("%s:%d" % kv for kv in sorted(tests.items()))))
    return 0


def cmd_wrap():
    """The `lea eax, [ecx + ecx*2]` (3L, 32-bit) bounds and what the model gives on each side (review-fixes 15)."""
    hi = (0x7FFFFFFF) // 3
    lo = -(0x80000000 // 3)
    for L in (hi, hi + 1, lo, lo - 1):
        t = s32(3 * L)
        print("WRAP L=%d 3L=%d s32(3L)=%d wraps=%d q=trunc(s32/4)=%d" % (L, 3 * L, t, int(t != 3 * L), tdiv(t, 4)))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("cases", "check", "reach", "static", "manifest", "wrap"))
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
    if o.cmd == "wrap":
        return cmd_wrap()
    B.cmd_manifest(o.dir, o.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S2ae part 6 (`lane/n66sa`): six stat-event handlers and Kick's start function under
Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java, compared with the models
below; plus `static`, the objdump listing of every function the cases run and of the triage reads.

    python3 -I tools/skills_s2ae6_emu.py cases [--dir D] [--limit N]   write D/s2ae.cases, D/s2ae.mem and the tables
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s2ae.cases D/s2ae.mem > D/s2ae.out
    python3 -I tools/skills_s2ae6_emu.py check [--dir D] [--limit N]   compare, account for traced reads, controls
    python3 -I tools/skills_s2ae6_emu.py reach [--limit N]             model outcomes and deciding tests per family
    python3 -I tools/skills_s2ae6_emu.py static                        objdump of the functions run and read
    python3 -I tools/skills_s2ae6_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66sa/s2ae/run6. Parts 1-5 (tools/skills_s2ae_emu.py, skills_s2ae2..5_emu.py) and their
run/ to run5/ are unchanged; this tool reuses part 1's check machinery (cmd_cases, cmd_check, cmd_manifest), batch
S5e part 1's unit builder (tools/combat_s5e_emu.py put_unit, unchanged) and part 5's GameFindUnit, MonsterOwner,
UNIT_GetTargetUnit and stat-list models, in its module state only. Every draw comes from
random.Random("n66sa-s2ae6-<family>"); the declared tables from random.Random("n66sa-s2ae6-tables").

Every callee runs whole on the declared image (ruling R2: no declared return) unless named as an observed boundary
(ADR-0021): the case ends at that call, its registers ECX/EDX, its stack arguments and the declared dumps are
compared, and the claim ends there. The allocator entries and the fatal path are guards.

Handlers (g_StatEventFuncs, ECX game, EDX the event id; stack: unit, other, packet, event word, x; ret 0x14):
  h7   0x005BF960 StatEv07Knockback, whole: sub_00625500_UnitGetStat (-> 0x00625420 -> 0x00624F60 ->
       STATLIST_FindIndex), MonStats2 record 0x00451FE0, the inline seed step.
  h8   0x005BFA10 StatEv08Howl to its call 0x005DDD00 (observed; it reaches the pool free 0x0040B480 at 0x0058EE65
       via 0x0058EDE0 <- 0x005B0E00): sub_005A0180_MonTypeFlag, UnitGetStat, RangePow2 0x00472210.
  h9   0x005BFAA0 StatEv09Stupidity to its call 0x005C39C0 (observed; pool free at 0x005C0BC4): UnitGetStat,
       STATS_GetUnitStat 0x00625480 (stat 12 of both units), RNG_Range 0x0045C390.
  h10  0x005BF720 StatEv10ThornsLightning to COMBAT_ApplyDamage 0x0057C6C0 (observed; pool free at 0x005C0CDD):
       UnitGetStat, memset 0x00681EF0; the packet on the stack is dumped.
  h18  0x005C0260 StatEv18HealAfterDemonKill to UnitSetStat 0x00627260 (observed; it reaches 0x0040B4B0 at
       0x00624E73 when the list grows): MONSTATS_IsDemon 0x0063E940, UnitGetStat, 0x00625D10 (stat 7),
       STATS_GetUnitStat (stat 6).
  h31  0x005C09E0 STATEVENT_Reanimate to 0x005C0AD0 (observed; it allocates at 0x005C0AF2): MonTypeFlag,
       UnitGetStat, RNG_Range 0x0045C3E0, MonsterOwner 0x0058F0D0 with GameFindUnit 0x00552F60.
Start function:
  st2  0x0056CAF0 sub_0056CAF0_SkillSt02Kick (ECX game, EDX unit; stack skill, level; ret 8) to
       COMBAT_ResolveAndQueue 0x0057DBF0 (observed; it reaches 0x0040B430 at 0x0057CABE via 0x0057CA80):
       UNIT_GetTargetUnit 0x00553540 (-> 0x00553490, GameFindUnit), memset; the packet on the stack is dumped.

Domain (each outside it reads an undeclared address or the fatal path, which the run would not account): the
handlers' units are non-null when UnitGetStat is reached (the code does not test the unit there); MonsterOwner's
chains end within three links and their types are 0..5; st2's skill id is inside the Skills table (a null record
is read at +0x1A4), its unit has a path and the game is non-null (UNIT_GetTargetUnit's fatal path).

Controls as parts 1-5: every named test reversed alone, every ordered compare's strictness switched alone; `sep`
counts the cases a control changes, `passed` those the emulator still matches (must be 0); `spec_*` controls are
readings the spec states or rules out. Stdlib only, plus objdump for `static`.
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
import skills_s2ae3_emu as P3  # noqa: E402
import skills_s2ae5_emu as P5  # noqa: E402
from combat_s5e_emu import u32, s32, le32, tdiv, G_DT, DT, FATAL, ALLOC, BITMASK, ISC, ISC_N, NSTATES  # noqa: E402

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66sa", "s2ae", "run6")
FNS = {"h7": 0x005BF960, "h8": 0x005BFA10, "h9": 0x005BFAA0, "h10": 0x005BF720, "h18": 0x005C0260,
       "h31": 0x005C09E0, "st2": 0x0056CAF0}
FAMILIES = ("h7", "h8", "h9", "h10", "h18", "h31", "st2")
NCASES = {"h7": 2000, "h8": 3000, "h9": 2500, "h10": 1500, "h18": 4000, "h31": 4000, "st2": 1500}
POP = {f: (8 if f == "st2" else 0x14) for f in FAMILIES}
p1.FNS.update(FNS)

OBS_FLEE, OBS_STUPID, OBS_APPLY, OBS_SETSTAT, OBS_REANIM, OBS_RESOLVE = (0x005DDD00, 0x005C39C0, 0x0057C6C0,
                                                                         0x00627260, 0x005C0AD0, 0x0057DBF0)
OBSERVES = (OBS_FLEE, OBS_STUPID, OBS_APPLY, OBS_SETSTAT, OBS_REANIM, OBS_RESOLVE)
NARGS = {OBS_FLEE: 4, OBS_STUPID: 2, OBS_APPLY: 3, OBS_SETSTAT: 4, OBS_REANIM: 6, OBS_RESOLVE: 3}
SITES_OBS = {("h8", OBS_FLEE): 0x005BFA8D, ("h9", OBS_STUPID): 0x005BFB8D, ("h10", OBS_APPLY): 0x005BF7A7,
             ("h18", OBS_SETSTAT): 0x005C02E1, ("h31", OBS_REANIM): 0x005C0A79, ("st2", OBS_RESOLVE): 0x0056CB85}
STACK = 0x7FF00000                    # EmuBoundary's entry ESP (the return address); EBP = STACK - 4 after the prologue
PKT = STACK - 0x78                    # h10 and st2: the packet at EBP - 0x74
GAME, GAME_SZ = P5.GAME, 0x2000
UB = 0x20000000
U, O, X, Y, T, F = (UB + 0x1000 * k for k in range(6))
PATH_OFF, REC_OFF = 0x900, 0xA00
UPKT = 0x20008000                     # h7's packet (case memory)
MS, MS_N, MS_SZ = 0x21200000, 0x240, 0x1A8
MS2, MS2_N, MS2_SZ = 0x21400000, 0x80, 0x134
SK, SK_N, SK_SZ = 0x21300000, 48, 0x23C
A_LCG = 0x6AC690C5

TABLES = None


def tables():
    """The declared MonStats (+0x0D the type bits, +0x18 the MonStats2 index), MonStats2 (+0x05) and Skills
    (+0x1A4 HitShift, +0x1A8 MinDam) images."""
    global TABLES
    if TABLES is None:
        r = random.Random("n66sa-s2ae6-tables")
        ms = bytearray(r.getrandbits(8) for _ in range(MS_N * MS_SZ))
        for i in range(MS_N):
            ix = r.choice([r.randrange(MS2_N)] * 8 + [-1, MS2_N, MS2_N + 7, -0x8000])
            struct.pack_into("<h", ms, i * MS_SZ + 0x18, ix)
        ms2 = bytearray(r.getrandbits(8) for _ in range(MS2_N * MS2_SZ))
        sk = bytearray(r.getrandbits(8) for _ in range(SK_N * SK_SZ))
        for i in range(SK_N):
            sk[i * SK_SZ + 0x1A4] = r.choice([0, 8, r.randrange(32), r.getrandbits(8)])
            struct.pack_into("<I", sk, i * SK_SZ + 0x1A8,
                             u32(r.choice([0, 1, r.randint(1, 40), r.randint(-20, -1), r.getrandbits(32)])))
        TABLES = (ms, ms2, sk)
    return TABLES


class Case(p1.Case):
    pass


class Mem(P3.Mem):
    """Part 3's view of the case's bytes, with the declared game image (game.bin, zero) behind the case's writes."""

    def b(self, a):
        if a not in self.w and GAME <= a < GAME + GAME_SZ:
            return 0
        return self.w[a]

    def h(self, a):
        return self.b(a) | (self.b(a + 1) << 8)


Stop = P5.Stop


def rbytes(rnd, n):
    return bytes(rnd.getrandbits(8) for _ in range(n))


def gid(rnd, used):
    while True:
        g = rnd.choice([rnd.getrandbits(32), rnd.randrange(0x100)])
        if g not in used:
            used.add(g)
            return g


def ev_word(rnd, stats):
    """The event word (stat << 16 | layer) and the handler unit's stat dict holding (or not) its value."""
    s = rnd.choice([rnd.randrange(1, ISC_N)] * 9 + [rnd.randrange(ISC_N, 0x10000)])
    layer = rnd.choice([0] * 8 + [1, rnd.getrandbits(16)])
    v = rnd.choice([None, 0, rnd.randint(1, 3), rnd.randint(1, 60), rnd.randint(60, 128), rnd.randint(-40, -1),
                    rnd.getrandbits(32), 0x7FFFFFFF, 0x80000000, rnd.randint(0x00800000, 0x01000000)])
    if layer == 0 and v is not None and s < ISC_N:
        stats[s] = v
    return u32((s << 16) | layer)


def unit(c, rnd, base, typ, cls=None, stats=None, md_flags=None, nolist=False):
    cls = rnd.choice([rnd.randrange(MS_N)] * 10 + [-1, MS_N, 0x7FFFFFFF]) if cls is None else cls
    view = p1.put_unit(c, rnd, base, typ, u32(cls), stats or {}, [], md_flags=md_flags, nolist=nolist)
    c.put(base + 0x60, le32(0))
    return view


def handler_args(c, rnd, a_unit, a_other, word, pkt=None):
    c.ecx = GAME
    c.edx = rnd.choice([rnd.randrange(40), 6, 6])
    c.args = [a_unit, a_other, UPKT if pkt is None else pkt, word, rnd.getrandbits(32)]


def finish(c, dumps):
    c.dumps = dumps
    c.a = dict(w=dict(c.w), ecx=c.ecx, edx=c.edx, args=list(c.args), dumps=list(dumps))
    return c


# ----------------------------------------------------------------------------------------------- shared models
def get_stat(M, u, s, layer):
    """sub_00625500_UnitGetStat / STATS_GetUnitStat: the unit's +0x5C list (UnitGetStat does not test the unit)."""
    sl = M.d(u + 0x5C)
    if sl == 0 or not 0 <= s < ISC_N:
        return 0
    return P5.stat_on(M, sl, s, layer & 0xFFFF)


def stats_get(M, u, s, layer=0):
    """STATS_GetUnitStat 0x00625480: 0 for no unit."""
    if u == 0:
        return 0
    return get_stat(M, u, s, layer)


def step(M, u):
    v = M.d(u + 0x20) * A_LCG + M.d(u + 0x24)
    M.put(u + 0x20, v & 0xFFFFFFFF)
    M.put(u + 0x24, (v >> 32) & 0xFFFFFFFF)
    return v & 0xFFFFFFFF


def rng_range(M, u, n):
    """RNG_Range 0x0045C390 / 0x0045C3E0: n <= 0 gives 0 with no step; a power of two masks, else mod."""
    if n <= 0:
        return 0
    lo = step(M, u)
    return lo & (n - 1) if n & (n - 1) == 0 else lo % n


def mon_type_flag(M, u, mask):
    """sub_005A0180_MonTypeFlag: a type-1 unit's MonsterData +0x16 word & mask, as 0/1."""
    if u == 0 or M.d(u) != 1:
        return 0
    md = M.d(u + 0x14)
    return 1 if md and (M.h(md + 0x16) & mask) else 0


def ms_rec(cls):
    return cls if 0 <= s32(cls) < MS_N else None


def is_demon(M, u):
    """MONSTATS_IsDemon 0x0063E940: MonStats +0x0D & g_BitMask32[5]."""
    if u == 0 or M.d(u) != 1:
        return 0
    k = ms_rec(M.d(u + 4))
    return 1 if k is not None and tables()[0][k * MS_SZ + 0xD] & 0x20 else 0


def ms2_byte5(M, cls):
    """0x00451FE0: the MonStats2 record by MonStats +0x18 (signed, below the count), its byte +5; None for none."""
    k = ms_rec(cls)
    if k is None:
        return None
    ix = struct.unpack_from("<h", tables()[0], k * MS_SZ + 0x18)[0]
    if not 0 <= ix < MS2_N:
        return None
    return tables()[1][ix * MS2_SZ + 5]


def obs(pc, regs, args, M, dumps):
    """An observed call: (ECX, EDX) as the code sets them for the call, or None where they are a callee's leftovers
    (h18's UnitSetStat takes none), its stack arguments and the dumps."""
    return ("obs", pc, None if regs is None else tuple(u32(x) for x in regs), tuple(u32(x) for x in args),
            P5.P4.dumped(M, dumps))


def ret(eax, M, dumps):
    return ("ret", u32(eax), P5.P4.dumped(M, dumps))


# ----------------------------------------------------------------------------------------------- h7, h8, h9, h10
def gen_h7(rnd):
    c = Case("h7")
    st = {}
    word = ev_word(rnd, st)
    unit(c, rnd, U, rnd.choice([0, 1, 1, 3]), stats=st)
    ot = rnd.choice([1] * 6 + [0, 2, 3, 4])
    unit(c, rnd, O, ot)
    c.put(UPKT, rbytes(rnd, 0x70))
    handler_args(c, rnd, U, O, word)
    pick = rnd.random()
    if pick < 0.04:
        c.args[0] = 0
    elif pick < 0.08:
        c.args[1] = 0
    elif pick < 0.12:
        c.args[2] = 0
    return finish(c, [(U + 0x20, 8), (UPKT, 8)])


def m_h7(e, a):
    M = Mem(a["w"])
    u, o, pkt, word = a["args"][:4]
    dumps = a["dumps"]
    if not e.t("u_nz", u != 0) or not e.t("o_nz", o != 0) or not e.t("pkt_nz", pkt != 0):
        return ret(0, M, dumps)
    v = s32(get_stat(M, u, word >> 16, word))
    if not e.c("v_gt0", v, ">", 0):
        return ret(0, M, dumps)
    cap = 0x40
    if e.t("o_mon", M.d(o) == 1):
        b5 = ms2_byte5(M, M.d(o + 4))
        if e.t("ms2_rec", b5 is not None):
            if e.t("b5_8", b5 & 8):
                cap = 0x20
            elif e.t("b5_4", b5 & 4):
                cap = 0x80
    lo = step(M, u)
    e.names.add("spec_mask_ff")
    r = lo & (0xFF if e.flip == "spec_mask_ff" else 0x7F)
    if not e.c("roll_lt_cap", r, "<", cap):
        return ret(0, M, dumps)
    M.put(pkt + 4, M.h(pkt + 4) | 8, 2)
    return ret(1, M, dumps)


def gen_h8(rnd):
    c = Case("h8")
    st = {}
    word = ev_word(rnd, st)
    unit(c, rnd, U, rnd.choice([0, 1, 1, 3]), stats=st)
    ot = rnd.choice([1] * 8 + [0, 2, 3])
    unit(c, rnd, O, ot, md_flags=rnd.choice([0, 0, 0x1, 0x10, 0x4, 0x8, 0xC, rnd.getrandbits(16), -1]))
    handler_args(c, rnd, U, O, word)
    pick = rnd.random()
    if pick < 0.03:
        c.args[0] = 0
    elif pick < 0.06:
        c.args[1] = 0
    return finish(c, [(U + 0x20, 8)])


def m_h8(e, a):
    M = Mem(a["w"])
    u, o, _, word = a["args"][:4]
    dumps = a["dumps"]
    if not e.t("u_nz", u != 0) or not e.t("o_nz", o != 0) or not e.t("o_mon", M.d(o) == 1):
        return ret(0, M, dumps)
    e.names.add("spec_mask_4")
    if e.t("mt_c", mon_type_flag(M, o, 0x4 if e.flip == "spec_mask_4" else 0xC)):
        return ret(0, M, dumps)
    v = s32(get_stat(M, u, word >> 16, word))
    if not e.c("v_gt0", v, ">", 0):
        return ret(0, M, dumps)
    r = step(M, u) & 0x7F
    if not e.c("roll_lt_v", r, "<", v):
        return ret(0, M, dumps)
    return obs(OBS_FLEE, (a["ecx"], u), (o, 0x82, 0x14, 0x14), M, dumps)


def gen_h9(rnd):
    c = Case("h9")
    st = {}
    word = ev_word(rnd, st)
    lv = rnd.choice([rnd.randint(1, 99), rnd.randint(1, 99), None, rnd.getrandbits(32), rnd.randint(-5, 0)])
    if lv is not None and 12 not in st:
        st[12] = lv
    unit(c, rnd, U, rnd.choice([0, 1, 1, 3]), stats=st)
    ost = {}
    olv = rnd.choice([rnd.randint(1, 99), rnd.randint(1, 99), None, rnd.getrandbits(32)])
    if olv is not None:
        ost[12] = olv
    unit(c, rnd, O, rnd.choice([1] * 8 + [0, 2]), stats=ost, nolist=rnd.random() < 0.04)
    handler_args(c, rnd, U, O, word)
    if rnd.random() < 0.03:
        c.args[1] = 0
    return finish(c, [(U + 0x20, 8)])


def m_h9(e, a):
    M = Mem(a["w"])
    u, o, _, word = a["args"][:4]
    dumps = a["dumps"]
    if not e.t("u_nz", u != 0) or not e.t("o_nz", o != 0) or not e.t("o_mon", M.d(o) == 1):
        return ret(0, M, dumps)
    v = get_stat(M, u, word >> 16, word)
    if not e.t("v_nz", v != 0):
        return ret(0, M, dumps)
    la, lb = stats_get(M, u, 12), stats_get(M, o, 12)
    t = u32(la + 4 * v - lb + 6)
    ch = s32(u32(5 * t))
    e.names.add("spec_no_third")
    if e.t("ev6", s32(a["edx"]) == 6) and e.c("ch_gt0", ch, ">", 0) and e.flip != "spec_no_third":
        ch = tdiv(ch, 3)
    if not e.c("ch_gt1", ch, ">", 1):
        ch = 1
    elif not e.c("ch_lt99", ch, "<", 99):
        ch = 99
    r = rng_range(M, u, 100)
    if not e.c("roll_lt_ch", r, "<", ch):
        return ret(0, M, dumps)
    n = tdiv(s32(ch - r), 5) + 1
    if not e.c("n_gt1", n, ">", 1):
        n = 1
    elif not e.c("n_lt20", n, "<", 20):
        n = 20
    return obs(OBS_STUPID, (a["ecx"], u), (o, n), M, dumps)


def gen_h10(rnd):
    c = Case("h10")
    st = {}
    word = ev_word(rnd, st)
    unit(c, rnd, U, rnd.choice([0, 1, 1, 3]), stats=st)
    unit(c, rnd, O, rnd.choice([0, 1, 1, 3]))
    c.put(O + 0xC4, le32(rnd.getrandbits(32) | (4 if rnd.random() < 0.75 else 0)))
    handler_args(c, rnd, U, O, word, pkt=0)
    pick = rnd.random()
    if pick < 0.03:
        c.args[0] = 0
    elif pick < 0.06:
        c.args[1] = 0
    return finish(c, [(U + 0x20, 8), (PKT, 0x70)])


def m_h10(e, a):
    M = Mem(a["w"])
    u, o, _, word = a["args"][:4]
    dumps = a["dumps"]
    if not e.t("u_nz", u != 0) or not e.t("o_nz", o != 0) or not e.t("o_c4_b2", (M.d(o + 0xC4) >> 2) & 1):
        return ("ret", 0, None)
    v = s32(get_stat(M, u, word >> 16, word))
    if not e.c("v_gt0", v, ">", 0):
        return ("ret", 0, None)
    pkt = bytearray(0x70)
    e.names.add("spec_no_shift")
    struct.pack_into("<H", pkt, 4, 0x4021)
    struct.pack_into("<I", pkt, 0x1C, u32(v if e.flip == "spec_no_shift" else v << 8))
    struct.pack_into("<I", pkt, 0x60, 0x4D)
    M.w.update({PKT + i: b for i, b in enumerate(pkt)})
    return obs(OBS_APPLY, (a["ecx"], u), (o, 1, PKT), M, dumps)


# ----------------------------------------------------------------------------------------------- h18, h31
def gen_h18(rnd):
    c = Case("h18")
    st = {}
    word = ev_word(rnd, st)
    mx = rnd.choice([rnd.randint(1, 3000) << 8, rnd.randint(1, 30) << 8, 0, None, rnd.getrandbits(32)])
    life = rnd.choice([None, 0, rnd.randint(1, 3000) << 8, rnd.randint(0, 3000 << 8), 0x7FFFFF00, -256])
    if mx is not None and 7 not in st:
        st[7] = mx
    if life is not None and 6 not in st:
        st[6] = life
    if rnd.random() < 0.3 and mx is not None and 6 not in (word >> 16,):
        st[6] = u32(s32(mx) - rnd.randint(0, 600))
    unit(c, rnd, U, rnd.choice([0, 1, 3]), stats=st)
    unit(c, rnd, O, rnd.choice([1] * 8 + [0, 2]))
    handler_args(c, rnd, U, O, word)
    pick = rnd.random()
    if pick < 0.03:
        c.args[0] = 0
    elif pick < 0.06:
        c.args[1] = 0
    return finish(c, [(U + 0x20, 8)])


def m_h18(e, a):
    M = Mem(a["w"])
    u, o, _, word = a["args"][:4]
    dumps = a["dumps"]
    if not e.t("u_nz", u != 0) or not e.t("o_nz", o != 0) or not e.t("demon", is_demon(M, o)):
        return ret(0, M, dumps)
    v = s32(get_stat(M, u, word >> 16, word))
    if not e.t("v_nz", v != 0):
        return ret(v, M, dumps)
    mx = s32(get_stat(M, u, 7, 0))
    life = s32(stats_get(M, u, 6))
    if not e.c("life_lt_max", life, "<", mx):
        return ret(0, M, dumps)
    nl = s32(life + u32(v << 8))
    e.names.add("spec_no_floor")
    if e.t("nl_le0", nl <= 0) and e.flip != "spec_no_floor":
        nl = 0
    if e.c("nl_lt_max", nl, "<", mx):
        val = nl
    else:
        val = mx
    return obs(OBS_SETSTAT, None, (u, 6, val, 0), M, dumps)


def link(c, base, owner_base, rnd, used, kind):
    """base's MonsterData +0x28 record naming owner_base (kind 'ok'), a guid nobody has ('miss'), no game ('nogame')
    or no record ('norec')."""
    rec = base + REC_OFF
    c.put(base + p1.MD_OFF + 0x28, le32(0 if kind == "norec" else rec))
    c.put(rec, rbytes(rnd, 0x40))
    c.put(rec + 0x28, le32(0 if kind == "nogame" else GAME))
    if kind == "ok":
        t, g = s32(int.from_bytes(bytes(c.w[owner_base + i] for i in range(4)), "little")), \
            int.from_bytes(bytes(c.w[owner_base + 0xC + i] for i in range(4)), "little")
        c.put(rec + 0x30, le32(t))
        c.put(rec + 0x2C, le32(g))
    else:
        c.put(rec + 0x30, le32(rnd.randrange(6)))
        c.put(rec + 0x2C, le32(gid(rnd, used)))


def place(c, base, used, rnd):
    """Give base a fresh guid and put it at the head of its type's bucket (types 0..5)."""
    g = gid(rnd, used)
    c.put(base + 0xC, le32(g))
    c.put(base + 0xE4, le32(0))
    t = s32(int.from_bytes(bytes(c.w[base + i] for i in range(4)), "little"))
    c.put(P5.head_addr(t, g), le32(base))
    return g


def gen_h31(rnd):
    c = Case("h31")
    used = set()
    st = {}
    word = ev_word(rnd, st)
    if word >> 16 < ISC_N and (word & 0xFFFF) == 0 and rnd.random() < 0.9:
        st[word >> 16] = rnd.choice([rnd.randint(1, 99)] * 6 + [rnd.randint(100, 150), 100])
    shape = rnd.choice(["player", "player", "mon1", "mon1", "mon2", "miss", "nogame", "norec", "nomd", "other"])
    ut = {"player": 0, "other": rnd.choice([2, 3, 4])}.get(shape, 1)
    unit(c, rnd, U, ut, stats=st, md_flags=-1 if shape == "nomd" else None)
    for b in (X, Y):
        c.put(b, rbytes(rnd, 0x100))
    unit(c, rnd, O, rnd.choice([1] * 8 + [0, 3]),
         md_flags=rnd.choice([0, 0, 0x1, 0x10, 0x4, 0x8, 0xC, rnd.getrandbits(16)]))
    if shape in ("mon1", "mon2"):
        c.put(X, le32(0 if shape == "mon1" else 1))
        c.put(X + 0x14, le32(X + p1.MD_OFF))
        c.put(X + p1.MD_OFF, rbytes(rnd, 0x40))
        place(c, X, used, rnd)
        link(c, U, X, rnd, used, "ok")
        if shape == "mon2":
            c.put(Y, le32(rnd.choice([0, 0, 0, 2])))
            place(c, Y, used, rnd)
            link(c, X, Y, rnd, used, rnd.choice(["ok", "ok", "ok", "miss"]))
    elif shape in ("miss", "nogame", "norec"):
        link(c, U, X, rnd, used, shape)
    c.put(U + 0xC, le32(gid(rnd, used)))
    handler_args(c, rnd, U, O, word)
    pick = rnd.random()
    if pick < 0.03:
        c.args[0] = 0
    elif pick < 0.06:
        c.args[1] = 0
    return finish(c, [(U + 0x20, 8)])


def owner_walk(e, M, u):
    for _ in range(4):
        if u == 0:
            return 0
        if e.t("is_player", M.d(u) == 0):
            return u
        u = P5.mon_owner(e, M, u)
    raise IndexError("owner chain")


def m_h31(e, a):
    M = Mem(a["w"])
    u, o, _, word = a["args"][:4]
    dumps = a["dumps"]
    if not e.t("u_nz", u != 0) or not e.t("o_nz", o != 0) or not e.t("o_mon", M.d(o) == 1):
        return ret(0, M, dumps)
    if e.t("mt_c", mon_type_flag(M, o, 0xC)):
        return ret(0, M, dumps)
    v = s32(get_stat(M, u, word >> 16, word))
    if not e.c("v_gt0", v, ">", 0):
        return ret(0, M, dumps)
    r = rng_range(M, u, 100)
    if not e.c("roll_lt_v", r, "<", v):
        return ret(0, M, dumps)
    p = owner_walk(e, M, u)
    if not e.t("p_found", p != 0):
        return ret(0, M, dumps)
    g = M.d(p + 0xC)
    return obs(OBS_REANIM, (a["ecx"], o), (0xD, word & 0xFFFF, g, 0x005C07A0, 0, g), M, dumps)


# ----------------------------------------------------------------------------------------------- st2
def gen_st2(rnd):
    c = Case("st2")
    used = set()
    unit(c, rnd, U, rnd.choice([0, 1]))
    p = U + PATH_OFF
    c.put(U + 0x2C, le32(p))
    c.put(p, rbytes(rnd, 0x80))
    place(c, U, used, rnd)
    shape = rnd.choice(["none", "found", "found", "found", "found", "miss", "self", "item1", "item2", "item0", "other"])
    tt = {"item1": 4, "item2": 4, "item0": 4}.get(shape, rnd.choice([0, 1, 1, 2, 3, 5]))
    unit(c, rnd, T, tt)
    c.put(T + 0x10, le32({"item1": 1, "item2": 2, "item0": rnd.choice([0, 3, 4])}.get(shape, rnd.randrange(20))))
    if shape == "none":
        c.put(p + 0x58, le32(0))
    elif shape == "self":
        c.put(p + 0x58, le32(U))
        c.put(p + 0x5C, le32(M32(c, U)))
        c.put(p + 0x60, struct.pack("<I", int.from_bytes(bytes(c.w[U + 0xC + i] for i in range(4)), "little")))
    else:
        g = place(c, T, used, rnd)
        c.put(p + 0x58, le32(T))
        c.put(p + 0x5C, le32(tt))
        if shape == "miss":
            g2 = gid(rnd, used)
            c.put(p + 0x60, le32(g2))
        elif shape == "other":
            unit(c, rnd, F, tt)
            c.put(F + 0xC, le32(g))
            c.put(F + 0xE4, le32(0))
            c.put(P5.head_addr(tt, g), le32(F))
            c.put(p + 0x60, le32(g))
        else:
            c.put(p + 0x60, le32(g))
    c.ecx, c.edx = GAME, U
    c.args = [rnd.randrange(SK_N), rnd.getrandbits(32)]
    return finish(c, [(p + 0x58, 4), (PKT, 0x70)])


def M32(c, a):
    return int.from_bytes(bytes(c.w[a + i] for i in range(4)), "little")


def m_st2(e, a):
    M = Mem(a["w"])
    game, u = a["ecx"], a["edx"]
    skill = a["args"][0]
    dumps = a["dumps"]
    try:
        t = P5.get_target(e, M, game, u)
    except Stop:
        return ("stop", P5.FATAL_PC, None)
    if not e.t("t_nz", t != 0):
        return ("ret", 0, None)
    rec = skill * SK_SZ
    sh = tables()[2][rec + 0x1A4]
    md = struct.unpack_from("<I", tables()[2], rec + 0x1A8)[0]
    pkt = bytearray(0x70)
    e.names.add("spec_maxdam")
    e.names.add("spec_shift_full")
    struct.pack_into("<I", pkt, 0, 2)
    struct.pack_into("<H", pkt, 4, 9)
    if e.flip == "spec_maxdam":
        md = struct.unpack_from("<I", tables()[2], rec + 0x1AC)[0]
    sh = sh if e.flip == "spec_shift_full" else sh & 31
    struct.pack_into("<I", pkt, 8, u32(md << sh) if sh < 32 else 0)
    struct.pack_into("<I", pkt, 0x60, 1)
    M.w.update({PKT + i: b for i, b in enumerate(pkt)})
    return obs(OBS_RESOLVE, (game, u), (t, PKT, 0x80), M, dumps)


GEN = {"h7": gen_h7, "h8": gen_h8, "h9": gen_h9, "h10": gen_h10, "h18": gen_h18, "h31": gen_h31, "st2": gen_st2}
MODEL = {"h7": m_h7, "h8": m_h8, "h9": m_h9, "h10": m_h10, "h18": m_h18, "h31": m_h31, "st2": m_st2}


class Sites(dict):
    def __missing__(self, key):
        return SITES_OBS.get(key, 0)


SITE = Sites()


# ----------------------------------------------------------------------------------------------- spec, check
def write_spec(d):
    ms, ms2, sk = tables()
    for name, data in (("monstats.bin", ms), ("monstats2.bin", ms2), ("skills.bin", sk),
                       ("isc.bin", bytes(ISC_N * p1.ISC_SZ))):
        with open(os.path.join(d, name), "wb") as f:
            f.write(bytes(data))
    dt = bytearray(0x1000)
    for off, v in ((0xC4, NSTATES), (0xA78, MS), (0xA80, MS_N), (0xA90, MS2), (0xA98, MS2_N), (0xB98, SK),
                   (0xBA0, SK_N), (0xBCC, ISC), (0xBD4, ISC_N)):
        struct.pack_into("<I", dt, off, v)
    with open(os.path.join(d, "dt.bin"), "wb") as f:
        f.write(bytes(dt))
    # the game: every bucket head zero unless a case writes it (a declared, read-only background)
    with open(os.path.join(d, "game.bin"), "wb") as f:
        f.write(bytes(GAME_SZ))
    lines = ["# plan 0066 S2ae part 6 (tools/skills_s2ae6_emu.py): declared tables",
             "dword %08x %08x" % (G_DT, DT),
             "load %08x %s" % (DT, os.path.join(d, "dt.bin")),
             "load %08x %s" % (MS, os.path.join(d, "monstats.bin")),
             "load %08x %s" % (MS2, os.path.join(d, "monstats2.bin")),
             "load %08x %s" % (SK, os.path.join(d, "skills.bin")),
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
        regs = (int(k["regs"]["ecx"], 16), int(k["regs"]["edx"], 16))
        return ("obs", k["obs"], regs, struct.unpack_from("<%dI" % n, st, 4), dt), rt
    if k["pop"] != POP[fam]:
        return ("pop", k["pop"]), None
    return ("ret", k["eax"], dt), None


def norm(fam, want):
    return want


def same(want, got):
    if want[0] == "ret" and want[2] is None and got[0] == "ret":
        return want[1] == got[1]
    return B_same(want, got)


B_same = B.same

READS = ((BITMASK, BITMASK + 128, "g_BitMask32 0x006CE268 (.rdata)"),
         (P5.BUCKET_TBL, P5.BUCKET_TBL + 20, "GameFindUnit's per-type bucket offsets 0x006E10E0 (.rdata)"))


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
    except (TypeError, KeyError, IndexError, AttributeError, ZeroDivisionError):
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
            rnd = random.Random("n66sa-s2ae6-" + fam)
            for _ in range(NCASES[fam] if limit is None else min(limit, NCASES[fam])):
                cases.append(GEN[fam](rnd))
        return cases
    B.build = build


# ----------------------------------------------------------------------------------------------- static reads
STATIC = (
    ("h7", 0x005BF960, 0x005BFA04), ("h8", 0x005BFA10, 0x005BFA99), ("h9", 0x005BFAA0, 0x005BFBA2),
    ("h10", 0x005BF720, 0x005BF7C3), ("h18", 0x005C0260, 0x005C02FF), ("h31", 0x005C09E0, 0x005C0A85),
    ("st2", 0x0056CAF0, 0x0056CB91),
    ("unitgetstat", 0x00625500, 0x0062551B), ("statsget", 0x00625480, 0x006254DE), ("slget", 0x00625420, 0x00625473),
    ("slvalue", 0x00624F60, 0x00624FD8), ("maxlife", 0x00625D10, 0x00625D58), ("montypeflag", 0x005A0180, 0x005A01A2),
    ("isdemon", 0x0063E940, 0x0063E98B), ("ms2rec", 0x00451FE0, 0x0045201F), ("rangepow2", 0x00472210, 0x00472237),
    ("range", 0x0045C390, 0x0045C3DB), ("range2", 0x0045C3E0, 0x0045C42B), ("monowner", 0x0058F0D0, 0x0058F100),
    ("findunit", 0x00552F60, 0x00552FCD),
    # triage reads (route decisions of part 6, not emulated)
    ("do146", 0x005C8520, 0x005C877A), ("h2", 0x005CAC50, 0x005CAD36), ("h3", 0x005CAD40, 0x005CAE31),
    ("h1", 0x005CAB40, 0x005CAC50), ("firestorm", 0x005C7160, 0x005C72E8), ("mdo3", 0x005AE480, 0x005AE515),
    ("mdo5", 0x005AE520, 0x005AE67D), ("itemcast", 0x005FDA80, 0x005FDC86), ("wear", 0x005DAA40, 0x005DAB40),
    ("summoninit", 0x005C4470, 0x005C49E0),
)


def objdump(lo, hi):
    out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "-M", "intel", "--start-address=0x%x" % lo,
                          "--stop-address=0x%x" % hi, p1.EXE], capture_output=True, text=True, check=True).stdout
    for ln in out.splitlines():
        ln = ln.strip()
        if ln and ln[0] in "0123456789abcdef" and ":\t" in ln:
            yield " ".join(ln.split())


def cmd_static():
    if p1.img() is None:
        return 1
    for label, lo, hi in STATIC:
        calls = 0
        for ln in objdump(lo, hi):
            print("%s %s" % (label, ln))
            if " call " in ln:
                calls += 1
        print("%s CALLS %d" % (label, calls))
    return 0


def cmd_reach(limit=None):
    """Per family: the model's outcomes (a return with its value, or the observed call), and the branch tallies the
    findings cite: which tests decided (the names a case's run evaluated, counted once per case)."""
    cases = B.build(limit)
    for fam in FAMILIES:
        out, tests = {}, {}
        for c in cases:
            if c.fam != fam:
                continue
            want, names = predict(fam, c.a)
            k = want[0] + ("=%d" % s32(want[1]) if want[0] == "ret" else ":%08x" % want[1] if want[0] == "obs" else "")
            out[k] = out.get(k, 0) + 1
            for nm in names:
                if not nm.endswith("~") and not nm.startswith("spec_"):
                    alt = predict(fam, c.a, flip=nm)[0]
                    if not B_same(want, alt) or not B_same(alt, want):
                        tests[nm] = tests.get(nm, 0) + 1
        print("REACH %s outcomes %s" % (fam, " ".join("%s:%d" % kv for kv in sorted(out.items()))))
        print("REACH %s deciding %s" % (fam, " ".join("%s:%d" % kv for kv in sorted(tests.items()))))
        if fam == "h18":
            kinds = {}
            for c in cases:
                if c.fam != fam:
                    continue
                want = predict(fam, c.a)[0]
                if want[0] != "obs":
                    continue
                M = Mem(c.a["w"])
                u, word = c.a["args"][0], c.a["args"][3]
                v = s32(get_stat(M, u, word >> 16, word))
                mx, life = s32(get_stat(M, u, 7, 0)), s32(stats_get(M, u, 6))
                nl = s32(life + u32(v << 8))
                kd = "floor0" if nl <= 0 else "cap_max" if nl >= mx else "sum"
                kinds[kd] = kinds.get(kd, 0) + 1
            print("REACH h18 value %s" % " ".join("%s:%d" % kv for kv in sorted(kinds.items())))
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

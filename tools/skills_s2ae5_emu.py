#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S2ae part 5 (`lane/n66sa`): SKILLS_TargetCheck whole, and the two re-seed callbacks
0x005D40F0 and 0x005CD110 to PathPlan, under Ghidra's p-code emulator (ADR-0015, ADR-0021) with
re/ghidra_scripts/EmuBoundary.java; and the route reads (per call site: allocator and import reach) of the open rows.

    python3 -I tools/skills_s2ae5_emu.py cases [--dir D] [--limit N]   write D/s2ae.cases, D/s2ae.mem and the tables
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s2ae.cases D/s2ae.mem > D/s2ae.out
    python3 -I tools/skills_s2ae5_emu.py check [--dir D] [--limit N]   compare, account for traced reads, controls
    python3 -I tools/skills_s2ae5_emu.py reach [--limit N]             model outcomes and branch reach per family
    python3 -I tools/skills_s2ae5_emu.py static                        objdump of the functions run
    python3 -I tools/skills_s2ae5_emu.py sites                         per root: each direct call site and whether
                                                                        its callee reaches the pool allocator or an
                                                                        import (tools/skills_s2ae3_emu.py's walk)
    python3 -I tools/skills_s2ae5_emu.py split [--dir D]               tc: the dead-flag cells with the emulator's
                                                                        outcome and the spec D2 reading's differences
    python3 -I tools/skills_s2ae5_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66sa/s2ae/run5. Parts 1-4 (tools/skills_s2ae_emu.py, skills_s2ae2_emu.py,
skills_s2ae3_emu.py, skills_s2ae4_emu.py) and their run/ to run4/ are unchanged; this tool reuses part 1's check
machinery (build, predict, cmd_check), part 3's Mem view, objdump and site walk, and part 4's zig-zag case generator
(gen_zz) and range/path-type pieces, in its module state only. Every draw comes from
random.Random("n66sa-s2ae5-<family>"); the declared Skills rows from random.Random("n66sa-s2ae5-tables").

The models read each case's own memory (an unwritten read is a model error) and the image (.rdata: g_BitMask32,
the per-type unit bucket offsets 0x006E10E0, PathSetType's two type tables). Every callee runs whole on the declared
image unless named as an observed boundary (ADR-0021): the case ends at that call and its claim ends there. The
allocator entries and the fatal path are guards.

Families (function, registers; inventory rows, d = skills/dispatch, m = skills/missiles):
  tc   0x0056CC60 SKILLS_TargetCheck (EAX skill, stack game, unit), whole, with UNIT_GetTargetUnit 0x00553540 ->
       0x00553490 (the stored target re-found by type and guid, 0x00648BB0/0x00648B90/0x00648BF0),
       GameFindUnit 0x00552F60 (the bucket chains), sub_00554200_UnitsHostile with MonsterOwner 0x0058F0D0,
       PlayerPairFlags 0x0055B300 (0x006221A0), AlignSame 0x00650D70 and UnitAlignGet 0x006259B0 (state 105's list
       0x006256B0/0x00625650, stat 172 0x00625420 -> 0x00624F60 -> 0x00624B90), sub_005542C0_SkillPetTest with
       sub_0058F090_MonsterOwnerRef, sub_00554D20_SkillAllyTest with 0x0045C4B0 and the party id 0x00554630 ->
       0x00540710 (0x0063D450), and sub_00620C10_UnitSetPathTargetUnit -> 0x00648B90.            d47
  rfa  0x005D40F0 sub_005D40F0_MissCbReseedFromArg (ECX missile, EDX the argument) to its PathPlan call: observed
       boundary 0x00649970 from 0x005D4141. Whole before it: MISSDATA_GetRange 0x0064A300, the range setters
       0x0064A2B0/0x0064A330, RNG_SeedInit 0x00650E40, sub_00648CF0_PathSetType (type 10),
       sub_00648E70_PathSetByte90.                                                                m75, m82 (part)
  rro  0x005CD110 sub_005CD110_MissCbReseedRoll (ECX missile, EDX the argument), the same, with the path word
       getter 0x00648A00 and its one inline step; observed boundary 0x00649970 from 0x005CD1AE.   m77, m82 (part)

Controls as parts 1-4: every named test reversed alone, every ordered compare's strictness switched alone; `sep`
counts the cases a control changes, `passed` those the emulator still matches (must be 0); `spec_*` controls are
the alternatives the spec names or rules out. Stdlib only, plus objdump for `static` and `sites`.
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
import skills_s2ae4_emu as P4  # noqa: E402
from combat_s5e_emu import u32, s32, le32, tdiv, G_DT, DT, FATAL, ALLOC, BITMASK  # noqa: E402

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66sa", "s2ae", "run5")
FNS = {"tc": 0x0056CC60, "rfa": 0x005D40F0, "rro": 0x005CD110}
FAMILIES = ("tc", "rfa", "rro")
NCASES = {"tc": 4000, "rfa": 1500, "rro": 2000}
POP = {"tc": 8, "rfa": 0, "rro": 0}
p1.FNS.update(FNS)

PATHPLAN = 0x00649970
SITES_OBS = {("rfa", PATHPLAN): 0x005D4146, ("rro", PATHPLAN): 0x005CD1B3}
FATAL_PC = 0x00408090
GAME = 0x20010000
BUCKET_TBL = 0x006E10E0                        # 5 dwords (.rdata): the per-type bucket offsets in the game
PARTY_OFF = 0x1D2C
PL = 0x20018000                                # the party list, its parties at +0x100, members at +0x400
CL = 0x20019000                                # the client records, 0x40 apart
UB = 0x20000000                                # units 0x1000 apart: U (caster), T (target), O, X, F
U, T, O, X, F = (UB + 0x1000 * k for k in range(5))
SL_OFF, ARR_OFF, OARR_OFF, MD_OFF, REC_OFF, PN_OFF, PATH_OFF = 0x200, 0x300, 0x400, 0x780, 0x7C0, 0x800, 0x900
NSTATES = 0xC0
SK, SK_N, SK_SZ = 0x21300000, 48, 0x23C
ISC, ISC_N, ISC_SZ = 0x21100000, 0x200, 0x144
MAGIC = 0x01020304

TABLES = None


def tables():
    global TABLES
    if TABLES is None:
        r = random.Random("n66sa-s2ae5-tables")
        TABLES = bytearray(r.getrandbits(8) for _ in range(SK_N * SK_SZ))
        for i in range(SK_N):
            rec = i * SK_SZ
            TABLES[rec + 6] = (TABLES[rec + 6] | 0x10) if r.random() < 0.5 else (TABLES[rec + 6] & ~0x10)
            b7 = TABLES[rec + 7] & ~0x07
            for bit, pr in ((1, 0.5), (2, 0.4), (4, 0.4)):
                if r.random() < pr:
                    b7 |= bit
            TABLES[rec + 7] = b7
    return TABLES


def skb(sk, off):
    return tables()[sk * SK_SZ + off]


BUCKETS = None


def buckets():
    global BUCKETS
    if BUCKETS is None:
        BUCKETS = struct.unpack("<5I", B.img_bytes(BUCKET_TBL, 20))
    return BUCKETS


def head_addr(t, gid):
    if t == 5:
        return GAME + 0x1B20
    return GAME + buckets()[t] + (gid & 0x7F) * 4


class Case(p1.Case):
    pass


Mem = P3.Mem
rbytes = P4.rbytes


# ----------------------------------------------------------------------------------------------- tc: cases
def gen_tc(rnd):
    c = Case("tc")
    guids = set()
    lookups = set()

    def gid():
        while True:
            g = rnd.choice([rnd.getrandbits(32), rnd.getrandbits(32), rnd.randrange(0x100), 0x40 + rnd.randrange(3)])
            if g not in guids and g != 0xFFFFFFFF:
                guids.add(g)
                return g
    units = {}

    def mk(base, typ, mode=None, align_list=True):
        c.put(base, rbytes(rnd, 0x100))
        g = gid()
        mode = rnd.randrange(20) if mode is None else mode
        for off, v in ((0, typ), (0xC, g), (0x10, mode), (0x14, base + MD_OFF), (0x60, 0), (0x80, GAME),
                       (0xE4, 0)):
            c.put(base + off, le32(v))
        c.put(base + MD_OFF, rbytes(rnd, 0x40))
        c.put(base + MD_OFF + 0x28, le32(base + REC_OFF))
        c.put(base + MD_OFF + 0x38, le32(0))
        c.put(base + REC_OFF, rbytes(rnd, 0x40))
        c.put(base + REC_OFF + 0x28, le32(0))
        # the stat list (UnitAlignGet: state 105's list, stat 172 on it)
        sl = base + SL_OFF
        if align_list and rnd.random() < 0.93:
            c.put(base + 0x5C, le32(sl))
            c.put(sl, rbytes(rnd, 0x60))
            flag = rnd.random() < 0.88
            c.put(sl + 0x10, le32((0x80000000 if flag else 0) | rnd.getrandbits(31)))
            st = rnd.choice([0x69, 0x69, 0x69, rnd.randrange(1, NSTATES)])
            head = rnd.random() < 0.85
            c.put(sl + 0x14, le32(st))
            c.put(sl + 0x2C, le32(0))
            c.put(sl + 0x3C, le32(sl if head else 0))
            c.put(sl + 0x40, le32(0))
            v172 = rnd.choice([0, 0, 1, 2, 2, 3, rnd.getrandbits(32), None])
            for arr_off, live in ((ARR_OFF, True), (OARR_OFF, False)):
                keys = {}
                if v172 is not None or not live:
                    keys[172 << 16] = u32(v172 if (v172 is not None and live) else rnd.getrandbits(32))
                if rnd.random() < 0.3:
                    keys[(172 << 16) | 1] = rnd.getrandbits(32)
                for _ in range(rnd.randrange(3)):
                    keys[rnd.randrange(1, ISC_N) << 16] = rnd.getrandbits(32)
                if v172 is None and live:
                    keys.pop(172 << 16, None)
                ks = sorted(keys, key=s32)
                arr = base + arr_off
                for i, k in enumerate(ks):
                    c.put(arr + 8 * i, le32(k) + le32(keys[k]))
                at = (0x48 if live else 0x24) if flag else (0x24 if live else 0x48)
                c.put(sl + at, le32(arr) + struct.pack("<H", len(ks)) + bytes(2))
        else:
            c.put(base + 0x5C, le32(0))
        c.put(base + 0xC4, le32(rnd.getrandbits(32)))
        c.put(base + 0xC8, le32(rnd.getrandbits(32) & ~0x400))
        units[base] = (typ, g)
        return g

    def owner(base, who):
        """A monster's owner record: GameFindUnit(rec +0x28, type rec +0x30, guid rec +0x2C)."""
        rec = base + REC_OFF
        if who is None:
            c.put(rec + 0x28, le32(0))
            return
        t, g = who
        c.put(rec + 0x28, le32(GAME))
        c.put(rec + 0x2C, le32(g))
        c.put(rec + 0x30, le32(t))
        lookups.add((t, g))

    ut = rnd.choice([0] * 9 + [1] * 5 + [3] * 3 + [2, 4])
    ug = mk(U, ut)
    tt = rnd.choice([0] * 4 + [1] * 8 + [2, 3, 4, 4, 5])
    tmode = rnd.choice([12, 12, 12, 0, 1, 2, rnd.randrange(20)])
    tg = mk(T, tt, mode=tmode)
    fc4 = rnd.getrandbits(32)
    fc4 = (fc4 | 2) if rnd.random() < 0.55 else (fc4 & ~2)
    c.put(T + 0xC4, le32(fc4))
    ot = rnd.choice([0, 0, 1])
    og = mk(O, ot)
    xg = mk(X, tt if rnd.random() < 0.7 else rnd.choice([0, 1, 4]))
    fg = mk(F, 0)
    # owners: O monster owned by F or nobody; T monster owned by U, O, F, an unknown guid, or nobody
    if ot == 1:
        owner(O, rnd.choice([(0, fg), None, None]))
    choices = [(0, ug) if ut == 0 else (ut, ug), (ot, og), (0, fg), (rnd.choice([0, 1]), gid()), None]
    if tt == 1:
        owner(T, rnd.choice(choices[:1] * 4 + choices[1:]))
    if ut == 1:
        owner(U, rnd.choice([(ot, og), (0, fg), None, None]))
    if ut == 3:
        if rnd.random() < 0.6:
            c.put(U + 0xC8, le32(rnd.getrandbits(32) | 0x400))
        who = rnd.choice([(ot, og), (0, fg), (0, gid())])
        c.put(U + 0x94, le32(who[0]) + le32(who[1]))
        lookups.add(who)
    for base in (U, O, F, T):         # players' pair lists (PlayerPairFlags reads the first unit's)
        if units[base][0] == 0 and rnd.random() < 0.8:
            n = rnd.choice([1, 1, 2, 3])
            nodes = []
            for i in range(n):
                nid = rnd.choice([tg, og, fg, ug, rnd.getrandbits(32)])
                fl = rnd.choice([8, 0, 0xFFFFFFFF, rnd.getrandbits(32), 1, 9])
                nodes.append((nid, fl))
            pn = base + PN_OFF
            for i, (nid, fl) in enumerate(nodes):
                nxt = pn + 0x20 * (i + 1) if i + 1 < n else 0
                c.put(pn + 0x20 * i, le32(nid) + le32(fl) + le32(0) + le32(0) + le32(nxt))
            c.put(base + MD_OFF + 0x38, le32(pn))
    # the clients: +0x60 of a player read by the party lookup
    for k, base in enumerate((U, F, T, O)):
        if units[base][0] == 0 and rnd.random() < 0.15:
            cl = CL + 0x40 * k
            c.put(cl, rbytes(rnd, 0x28))
            c.put(cl, le32(MAGIC if rnd.random() < 0.8 else rnd.getrandbits(32)))
            c.put(cl + 0x24, le32(rnd.choice([units[base][1], fg, ug, rnd.getrandbits(32)])))
            c.put(base + 0x60, le32(cl))
    # the parties
    if rnd.random() < 0.9:
        c.put(GAME + PARTY_OFF, le32(PL))
        c.put(PL, rbytes(rnd, 0x10))
        nparty = rnd.choice([0, 1, 2, 2])
        c.put(PL + 4, le32(PL + 0x100 if nparty else 0))
        pool = [ug, fg, tg, og, xg]
        mem = PL + 0x400
        for j in range(nparty):
            node = PL + 0x100 + 0x20 * j
            c.put(node, rbytes(rnd, 0x10))
            c.put(node, struct.pack("<H", rnd.choice([j, 0xFFFF if rnd.random() < 0.05 else j + 1, rnd.getrandbits(16)])))
            ms = rnd.sample(pool, rnd.randrange(0, 4))
            c.put(node + 4, le32(mem if ms else 0))
            for i, m in enumerate(ms):
                c.put(mem, le32(m) + le32(mem + 8 if i + 1 < len(ms) else 0))
                mem += 8
            c.put(node + 8, le32(PL + 0x100 + 0x20 * (j + 1) if j + 1 < nparty else 0))
    else:
        c.put(GAME + PARTY_OFF, le32(0))
    # U's path and its stored target
    pth = U + PATH_OFF
    c.put(U + 0x2C, le32(pth if rnd.random() < 0.98 else 0))
    c.put(pth, rbytes(rnd, 0x70))
    tr = rnd.random()
    if tr < 0.72:
        stored, st_t, st_g = T, tt, tg
        if rnd.random() < 0.06:
            st_g = gid()                                   # a stale guid: not found, cleared
        lookups.add((st_t, st_g))
    elif tr < 0.82:
        stored, st_t, st_g = 0, rnd.choice([0, 1]), rnd.getrandbits(32)
    elif tr < 0.9:
        stored, st_t, st_g = U, ut if 0 <= ut <= 5 else 0, ug       # the unit itself
        lookups.add((st_t, st_g))
    else:
        stored, st_t, st_g = X, units[X][0], units[X][1]
        if rnd.random() < 0.5:
            st_t, st_g = tt, tg                            # found as T, stored as X: cleared
        lookups.add((st_t, st_g))
    c.put(pth + 0x58, le32(stored) + le32(st_t) + le32(st_g))
    # the ally test's lookup: T's own (type, guid) for a player target
    lookups.add((tt, tg)) if tt in (0, 1) else None
    # the bucket chains: every unit in its bucket (two orders), every looked-up bucket declared
    heads = {}
    order = list(units.items())
    rnd.shuffle(order)
    for base, (t, g) in order:
        if 0 <= t <= 5:
            heads.setdefault(head_addr(t, g), []).append(base)
    for t, g in lookups:
        heads.setdefault(head_addr(t, g), [])
    for ha, lst in heads.items():
        c.put(ha, le32(lst[0] if lst else 0))
        for i, base in enumerate(lst):
            c.put(base + 0xE4, le32(lst[i + 1] if i + 1 < len(lst) else 0))
    sk = rnd.choice([rnd.randrange(SK_N)] * 14 + [-1, SK_N, SK_N + 3, rnd.getrandbits(32)])
    c.regs = {"EAX": u32(sk)}
    c.ecx, c.edx = 0, 0
    c.args = [GAME, U]
    c.dumps = [(pth + 0x58, 12)]
    c.a = dict(w=dict(c.w), sk=s32(u32(sk)), dumps=list(c.dumps))
    return c


# ----------------------------------------------------------------------------------------------- tc: model
class Stop(Exception):
    pass


def find(e, M, game, t, g):
    """GameFindUnit 0x00552F60: the type's bucket (type 5: one list) walked by +0x0C, next +0xE4."""
    if game == 0:
        raise Stop()
    if t == 5:
        q = M.d(game + 0x1B20)
    elif 0 <= t <= 4:
        q = M.d(game + buckets()[t] + (g & 0x7F) * 4)
    else:
        raise KeyError("find type")
    for _ in range(16):
        if q == 0:
            return 0
        if M.d(q + 0xC) == g:
            return q
        q = M.d(q + 0xE4)
    raise IndexError("chain")


def get_target(e, M, game, u):
    """UNIT_GetTargetUnit 0x00553540 (0x00553490 first): the stored target re-found and kept only when it is found
    as itself and is not an item in mode 1 or 2; the unit itself counts as none."""
    p = M.d(u + 0x2C)
    if p == 0 or game == 0:
        raise Stop()
    if e.t("gt_stored", M.d(p + 0x58) != 0):
        f = find(e, M, game, M.d(p + 0x5C), M.d(p + 0x60))
        if e.t("gt_other", f != M.d(p + 0x58)):
            M.put(p + 0x58, 0)
        if e.t("gt_found", f != 0) and e.t("gt_item", M.d(f) == 4) and (
                e.t("gt_mode2", M.d(f + 0x10) == 2) or e.t("gt_mode1", M.d(f + 0x10) == 1)):
            M.put(p + 0x58, 0)
    t = M.d(p + 0x58)
    return 0 if e.t("gt_self", t == u) else t


def mon_owner(e, M, m):
    """MonsterOwner 0x0058F0D0: a monster's owner unit by its record, else 0."""
    if m == 0 or M.d(m) != 1:
        return 0
    md = M.d(m + 0x14)
    if md == 0:
        return 0
    rec = M.d(md + 0x28)
    if rec == 0 or M.d(rec + 0x28) == 0:
        return 0
    return find(e, M, M.d(rec + 0x28), M.d(rec + 0x30), M.d(rec + 0x2C))


def stat_on(M, sl, stat, layer=0):
    """0x00625420 -> 0x00624F60 -> 0x00624B90: the list's live array (+0x48 when +0x10 bit 31, else +0x24), signed
    binary search; the ItemStatCost records are declared zero."""
    if sl == 0 or not 0 <= stat < ISC_N:
        return 0
    off = 0x48 if M.d(sl + 0x10) & 0x80000000 else 0x24
    arr, n = M.d(sl + off), P3.sx16(M.h(sl + off + 4))
    key = s32((stat << 16) + layer)
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
    return 0


def align(e, M, u):
    """UnitAlignGet 0x006259B0."""
    if u == 0 or M.d(u + 0x5C) == 0:
        return 0
    if e.t("al_gt1", M.d(u) > 1):
        return 2
    sl = P4.find_state_list(M, u, 0x69)
    if not e.t("al_list", sl != 0):
        return 0
    return stat_on(M, sl, 172)


def align_same(e, M, a, b):
    """AlignSame 0x00650D70."""
    if a == 0 or b == 0:
        return 0
    if a == b:
        return 1
    x, y = align(e, M, a), align(e, M, b)
    if e.t("as_a0", x == 0):
        return 1 if (y != 2 and y != 1 and e.t("as_b0", y == 0)) else 0
    if x == 1:
        return 0
    return 1 if (e.t("as_a2", x == 2) and e.t("as_b2", y == 2)) else 0


def pair_flags(e, M, a, b, mask):
    """PlayerPairFlags 0x0055B300: a's PlayerData +0x38 list, the node naming b's guid, its flags & mask."""
    if M.d(a) != 0:
        raise Stop()
    pd = M.d(a + 0x14)
    gid = M.d(b + 0xC) if b else 0xFFFFFFFF
    if a == b:
        return 0
    q = M.d(pd + 0x38)
    for _ in range(8):
        if q == 0:
            return 0
        if e.t("pp_id", M.d(q) == gid):
            return M.d(q + 4) & mask
        q = M.d(q + 0x10)
    raise IndexError("pnodes")


def hostile(e, M, game, a, b):
    """sub_00554200_UnitsHostile(game, a, b)."""
    if a:
        ta = M.d(a)
        if e.t("h_a_mon", ta == 1):
            o = mon_owner(e, M, a)
            if e.t("h_a_owner", o != 0):
                a = o
        elif e.t("h_a_mis", ta == 3) and e.t("h_a_c8", M.d(a + 0xC8) & 0x400):
            o = find(e, M, game, M.d(a + 0x94), M.d(a + 0x98))
            if e.t("h_a_mis_owner", o != 0):
                a = o
    for _ in range(8):
        if not (b and M.d(b) == 1):
            break
        o = mon_owner(e, M, b)
        if not e.t("h_b_owner", o != 0) or o == b:
            break
        b = o
    else:
        raise IndexError("owner chain")
    if e.t("h_same", a == b):
        return 0
    if e.t("h_pp", a != 0 and M.d(a) == 0 and b != 0 and M.d(b) == 0):
        return pair_flags(e, M, a, b, 8)
    return 0 if align_same(e, M, a, b) else 1


def owner_ref(M, m):
    """sub_0058F090_MonsterOwnerRef: -> (guid, type) of the record, or (-1, None) when it names none."""
    if m == 0 or M.d(m) != 1:
        return 0xFFFFFFFF, None
    md = M.d(m + 0x14)
    rec = M.d(md + 0x28) if md else 0
    if M.d(rec + 0x28) == 0:
        return 0xFFFFFFFF, None
    return M.d(rec + 0x2C), M.d(rec + 0x30)


def pet(e, M, u, t, sk):
    """sub_005542C0_SkillPetTest(unit, target, skill)."""
    if u == 0 or t == 0:
        return 0
    if not e.t("pet_u0", M.d(u) == 0) and not e.t("pet_t1", M.d(t) == 1):
        return 0
    if not e.t("pet_row2", skb(sk, 7) & 2):
        return 0
    g, ty = owner_ref(M, t)
    tslot = t if ty is None else ty
    return 1 if (e.t("pet_type0", tslot == 0) and e.t("pet_guid", g == M.d(u + 0xC))) else 0


def party(e, M, x):
    """0x00554630 -> 0x00540710: a player's party id (u16), 0xFFFF for none."""
    if x == 0 or M.d(x + 0x80) == 0 or M.d(x) != 0:
        return 0xFFFF
    game = M.d(x + 0x80)
    gid = M.d(x + 0xC)
    cl = M.d(x + 0x60)
    if e.t("pa_client", cl != 0):
        gid = M.d(cl + 0x24) if e.t("pa_magic", M.d(cl) == MAGIC) else 0xFFFFFFFF
    pl = M.d(game + PARTY_OFF)
    if not e.t("pa_list", pl != 0):
        return 0xFFFF
    n = M.d(pl + 4)
    for _ in range(8):
        if n == 0:
            return 0xFFFF
        m = M.d(n + 4)
        for _ in range(8):
            if m == 0:
                break
            if e.t("pa_member", M.d(m) == gid):
                return M.h(n)
            m = M.d(m + 4)
        n = M.d(n + 8)
    raise IndexError("parties")


def ally(e, M, game, u, t, sk):
    """sub_00554D20_SkillAllyTest(game, unit, target, skill)."""
    if u == 0 or t == 0 or not e.t("al_u0", M.d(u) == 0):
        return 0
    tt = M.d(t)
    if not (e.t("al_t0", tt == 0) or e.t("al_t1", tt == 1)):
        return 0
    if not e.t("al_row4", skb(sk, 7) & 4):
        return 0
    g, ty = M.d(t + 0xC), tt
    if tt == 1:
        g2, ty2 = owner_ref(M, t)
        g = g2
        if ty2 is not None:
            ty = ty2
        if not e.t("al_owner", g != 0xFFFFFFFF) or not e.t("al_owner0", ty == 0):
            return 0
    si = party(e, M, u)
    if not e.t("al_party", si != 0xFFFF):
        return 0
    f = find(e, M, game, ty, g)
    if not e.t("al_found", f != 0):
        return 0
    return 1 if e.t("al_same", party(e, M, f) == si) else 0


def clear_target(M, u):
    """sub_00620C10_UnitSetPathTargetUnit(unit, 0): types 0, 1, 3 only (else the fatal path); path +0x58 <- 0."""
    if M.d(u) not in (0, 1, 3):
        raise Stop()
    M.put(M.d(u + 0x2C) + 0x58, 0)


def m_tc(e, a):
    M = Mem(a["w"])
    sk = a["sk"]
    out = lambda r: ("ret", r, P4.dumped(M, a["dumps"]))  # noqa: E731
    try:
        t = get_target(e, M, GAME, U)
        if not e.t("t_nz", t != 0):
            return out(1)
        if not e.c("sk_ge0", sk, ">=", 0) or not e.c("sk_lt_n", sk, "<", SK_N):
            return out(0)
        if e.t("tonly", skb(sk, 6) & 0x10):
            if not e.t("hostile", hostile(e, M, GAME, U, t) != 0):
                if not e.t("pet", pet(e, M, U, t, sk) != 0):
                    if not e.t("ally", ally(e, M, GAME, U, t, sk) != 0):
                        return out(0)
        corpse = skb(sk, 7) & 1
        e.names.add("spec_d2")
        dead = M.d(t + 0xC4) >> 1 & 1
        if e.flip == "spec_d2":                              # spec D2: a dead target kept only by TargetCorpse,
            if dead and not corpse:                          # any other target kept
                clear_target(M, U)
            return out(1)
        if not e.t("dead", dead):
            clear_target(M, U)
            return out(1)
        if e.t("t_mon", M.d(t) == 1) and e.t("t_mode12", M.d(t + 0x10) == 12):
            if not e.t("corpse_a", corpse):
                clear_target(M, U)
            return out(1)
        if e.t("corpse_b", corpse):
            clear_target(M, U)
        return out(1)
    except Stop:
        return ("stop", FATAL_PC, None)


# ----------------------------------------------------------------------------------------------- rfa, rro
def gen_rfa(rnd):
    c = P4.gen_zz(rnd)
    c.fam = "rfa"
    return c


def gen_rro(rnd):
    c = P4.gen_zz(rnd)
    c.fam = "rro"
    return c


def getter_and_cap(e, M, u):
    """MISSDATA_GetRange, and from 78 on the cap 77 through both setters (type 3 with data, as the getter read)."""
    d = M.d(u + 0x14)
    r = 0
    if e.t("type3", s32(M.d(u)) == 3) and e.t("data_nz", d != 0):
        r = P3.sx16(M.h(d + 0xE))
    if e.c("r_ge_4e", r, ">=", 0x4E):
        r = 0x4D
        M.put(d + 0xE, 0x4D, 2)
        M.put(d + 0x10, 0x4D, 2)
    return r


def path_type10(e, M, p):
    """sub_00648CF0_PathSetType(p, 10), as part 4's zz family ran it."""
    c30 = M.d(p + 0x30)
    if c30:
        M.d(c30)
    M.put(p + 0x34, (M.d(p + 0x34) & 0xFFF800FF) | P4.img32(P4.PT_FLAGS + 4 * 10))
    M.put(p + 0x3C, 10)
    M.put(p + 0x98, P4.img32(P4.PT_W98 + 4 * 10))
    f40 = M.d(p + 0x40)
    if e.t("f40_b", f40 == 0xB) or e.t("f40_8", f40 == 8):
        raise Stop()


def byte90(e, M, p, r):
    b = r & 0xFF
    if not e.c("b_lt_4d", b, "<", 0x4D):
        b = 0x4D
    M.put(p + 0x91, b, 1)
    M.put(p + 0x90, b, 1)


def m_rfa(e, a):
    M = Mem(a["w"])
    u = a["ecx"]
    if not e.t("unit_nz", u != 0):
        return ("ret", P4.dumped(M, a["dumps"]))
    try:
        r = getter_and_cap(e, M, u)
        p = M.d(u + 0x2C)
        e.names.add("spec_plus_x")
        lo = a["edx"] if e.flip != "spec_plus_x" else u32(M.h(p + 0x10) + a["edx"])
        M.put(u + 0x20, lo)
        M.put(u + 0x24, 0x29A)
        path_type10(e, M, p)
        byte90(e, M, p, r)
    except Stop:
        return ("stop", FATAL_PC, None)
    return ("obs", PATHPLAN, (p, u, 0), P4.dumped(M, a["dumps"]))


def m_rro(e, a):
    M = Mem(a["w"])
    u = a["ecx"]
    if not e.t("unit_nz", u != 0):
        return ("ret", P4.dumped(M, a["dumps"]))
    try:
        r = getter_and_cap(e, M, u)
        p = M.d(u + 0x2C)
        lo0 = u32(M.h(p + 0x10) + a["edx"])
        e.names.add("spec_no_step")
        e.names.add("spec_smod")
        lo, hi = P4.lcg2(lo0, 0x29A)
        if e.flip == "spec_no_step":
            lo, hi = lo0, 0x29A
        M.put(u + 0x20, lo)
        M.put(u + 0x24, hi)
        roll = (s32(lo) - 100 * tdiv(s32(lo), 100)) if e.flip == "spec_smod" else lo % 100
        if not e.c("roll_ge20", roll, ">=", 20):
            return ("ret", P4.dumped(M, a["dumps"]))
        path_type10(e, M, p)
        byte90(e, M, p, r)
    except Stop:
        return ("stop", FATAL_PC, None)
    return ("obs", PATHPLAN, (p, u, 0), P4.dumped(M, a["dumps"]))


GEN = {"tc": gen_tc, "rfa": gen_rfa, "rro": gen_rro}
MODEL = {"tc": m_tc, "rfa": m_rfa, "rro": m_rro}


class Sites(dict):
    def __missing__(self, key):
        return SITES_OBS.get(key, 0)


SITE = Sites()


# ----------------------------------------------------------------------------------------------- spec, check
def write_spec(d):
    with open(os.path.join(d, "skills.bin"), "wb") as f:
        f.write(bytes(tables()))
    with open(os.path.join(d, "isc.bin"), "wb") as f:
        f.write(bytes(ISC_N * ISC_SZ))
    dt = bytearray(0x1000)
    for off, v in ((0xC4, NSTATES), (0xB98, SK), (0xBA0, SK_N), (0xBCC, ISC), (0xBD4, ISC_N)):
        struct.pack_into("<I", dt, off, v)
    with open(os.path.join(d, "dt.bin"), "wb") as f:
        f.write(bytes(dt))
    lines = ["# plan 0066 S2ae part 5 (tools/skills_s2ae5_emu.py): declared tables",
             "dword %08x %08x" % (G_DT, DT),
             "load %08x %s" % (DT, os.path.join(d, "dt.bin")),
             "load %08x %s" % (SK, os.path.join(d, "skills.bin")),
             "load %08x %s" % (ISC, os.path.join(d, "isc.bin"))]
    lines += ["guard %08x" % x for x in FATAL + ALLOC]
    lines += ["observe %08x" % PATHPLAN]
    with open(os.path.join(d, "s2ae.mem"), "w") as f:
        f.write("\n".join(lines) + "\n")


def observed(fam, k):
    if "stop" in k:
        return ("stop", k["stop"], None), None
    dumps = k["dumps"]
    if "obs" in k:
        st = k["stack"]
        ret = struct.unpack_from("<I", st, 0)[0]
        return ("obs", k["obs"], struct.unpack_from("<3I", st, 4), tuple(dumps[va] for va in sorted(dumps))), ret
    if k["pop"] != POP[fam]:
        return ("pop", k["pop"]), None
    if fam == "tc":
        return ("ret", k["eax"], tuple(dumps[va] for va in sorted(dumps))), None
    return ("ret", tuple(dumps[va] for va in sorted(dumps))), None


def norm(fam, want):
    return want


READS = ((BITMASK, BITMASK + 128, "g_BitMask32 0x006CE268 (.rdata)"),
         (BUCKET_TBL, BUCKET_TBL + 20, "GameFindUnit's per-type bucket offsets 0x006E10E0 (.rdata)"),
         (P4.PT_FLAGS, P4.PT_FLAGS + 4 * 18, "PathSetType's flags 0x006EB690 (.rdata)"),
         (P4.PT_W98, P4.PT_W98 + 4 * 18, "PathSetType's +0x98 words 0x006EB648 (.rdata)"))


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
    B.observed, B.norm, B.account, B.write_spec, B.predict = observed, norm, account, write_spec, predict
    B.Case = Case

    def build(limit=None):
        cases = []
        for fam in FAMILIES:
            rnd = random.Random("n66sa-s2ae5-" + fam)
            for _ in range(NCASES[fam] if limit is None else min(limit, NCASES[fam])):
                cases.append(GEN[fam](rnd))
        return cases
    B.build = build


# ----------------------------------------------------------------------------------------------- static reads
STATIC = (
    ("tc", 0x0056CC60, 0x0056CD46),
    ("gettarget", 0x00553540, 0x00553569),
    ("gettarget2", 0x00553490, 0x00553534),
    ("pathtarget-set", 0x00648B90, 0x00648BAF),
    ("pathtarget-ref", 0x00648BB0, 0x00648BEF),
    ("pathtarget-get", 0x00648BF0, 0x00648C05),
    ("findunit", 0x00552F60, 0x00552FCD),
    ("hostile", 0x00554200, 0x005542B5),
    ("monowner", 0x0058F0D0, 0x0058F100),
    ("pairflags", 0x0055B300, 0x0055B34D),
    ("playerdata", 0x006221A0, 0x006221DA),
    ("alignsame", 0x00650D70, 0x00650DCB),
    ("alignget", 0x006259B0, 0x006259EF),
    ("findbystate", 0x006256B0, 0x006256D8),
    ("findbystate2", 0x00625650, 0x006256AA),
    ("unitstat", 0x00625420, 0x00625473),
    ("liststat", 0x00624F60, 0x00624FD8),
    ("bsearch", 0x00624B90, 0x00624BC5),
    ("pettest", 0x005542C0, 0x00554335),
    ("ownerref", 0x0058F090, 0x0058F0CB),
    ("allytest", 0x00554D20, 0x00554DD9),
    ("skillrow", 0x0045C4B0, 0x0045C4D4),
    ("partyid", 0x00554630, 0x0055464F),
    ("partyid2", 0x00540710, 0x00540793),
    ("clientid", 0x0063D450, 0x0063D46E),
    ("settarget", 0x00620C10, 0x00620C60),
    ("rfa", 0x005D40F0, 0x005D414D),
    ("rro", 0x005CD110, 0x005CD1BA),
    ("mrange", 0x0064A300, 0x0064A322),
    ("setrange", 0x0064A2B0, 0x0064A2F0),
    ("setrange2", 0x0064A330, 0x0064A370),
    ("seed", 0x00650E40, 0x00650E4A),
    ("pathtx", 0x00648A00, 0x00648A0E),
    ("pathsettype", 0x00648CF0, 0x00648DBE),
    ("pathbyte90", 0x00648E70, 0x00648E92),
)


def cmd_static():
    if p1.img() is None:
        return 1
    for label, lo, hi in STATIC:
        for ln in P3.objdump(lo, hi):
            print("%s %s" % (label, ln))
    print("BUCKETS " + " ".join("%d" % x for x in buckets()))
    print("BITMASK0-4 " + " ".join("%02x" % B.img_bytes(BITMASK + 4 * i, 1)[0] for i in range(5)))
    print("PATHTYPE10 flags=%08x w98=%08x" % (P4.img32(P4.PT_FLAGS + 40), P4.img32(P4.PT_W98 + 40)))
    return 0


SITE_ROOTS = (   # (label, entry, rows)
    ("SKILLS_TargetCheck", 0x0056CC60, "d47"),
    ("MissCbReseedFromArg", 0x005D40F0, "m75, m82"),
    ("MissCbReseedRoll", 0x005CD110, "m77, m82"),
    ("StatEv01MissileAtSource", 0x005CAB40, "d110, d135, d178"),
    ("StatEv02CalcHitAttacker", 0x005CAC50, "d111, d135, d178"),
    ("StatEv03ElemHitAttacker", 0x005CAD40, "d112, d135, d178"),
    ("StatEv07Knockback", 0x005BF960, "d135, d178"),
    ("StatEv08Howl", 0x005BFA10, "d117, d135, d178"),
    ("StatEv09Stupidity", 0x005BFAA0, "d135, d178"),
    ("StatEv10ThornsLightning", 0x005BF720, "d119, d135, d178"),
    ("StatEv18HealAfterDemonKill", 0x005C0260, "d124, d135, d178"),
    ("StatEv23BloodGolemHit", 0x005C6530, "d127, d135, d178"),
    ("StatEv24EnergyShield", 0x005CA6C0, "d128, d135, d178"),
    ("StatEv25CycloneArmor", 0x005C87A0, "d129, d135, d178"),
    ("StatEv26BloodGolemDamaged", 0x005C6690, "d130, d135, d178"),
    ("StatEv27ClayGolemSlow", 0x005C6760, "d131, d135, d178"),
    ("StatEv30SkillOnDeathOrLevel", 0x005C0670, "d135, d178"),
    ("STATEVENT_Reanimate", 0x005C09E0, "d133, d135, d178"),
    ("SkillWeaponWear", 0x005DAA40, "d156, d181"),
    ("SkillDo146Armageddon", 0x005C8520, "d182, d184"),
    ("SummonSetLevel", 0x005C49E0, "d142, d143"),
    ("SummonInitStats", 0x005C4470, "d144"),
    ("MonAttackStats", 0x005A4F50, "d152"),
    ("MonOwnerSkillDamage", 0x0056E050, "d153, d154"),
    ("KickItemDamage", 0x00646280, "d96"),
    ("SkillSt02Kick", 0x0056CAF0, "d93"),
    ("SkillSt06Hit", 0x005DA940, "d89"),
    ("DualAttackAlternate", 0x00549960, "d31"),
    ("SKILLS_CanUse", 0x00647960, "d3, d32-35"),
    ("SKILLS_GetRangeType", 0x00645460, "d30"),
    ("SKILLS_ItemChargesOk", 0x00647840, "d40"),
    ("SkillDo117Firestorm", 0x005C7160, "d172"),
    ("MissDo03CloudMark", 0x005AE480, "m71"),
    ("MissDo05Loop", 0x005AE520, "m72"),
    ("AreaHitUnit", 0x0056B9C0, "m74"),
    ("MissHit58", 0x005ACDF0, "m85"),
    ("MissCb5BF0", 0x005D5BF0, "m85"),
    ("MissileDamageBlock", 0x0064B860, "m26, m29"),
    ("MissileDamageToStats", 0x0064AC60, "m27, m95"),
)


def cmd_sites():
    P3.SITE_ROOTS = SITE_ROOTS
    return P3.cmd_sites()


# ----------------------------------------------------------------------------------------------- reach
def cmd_reach(limit=None):
    cases = B.build(limit)
    outs, reach = {}, {}
    for c in cases:
        e = P3.RE()
        try:
            w = MODEL[c.fam](e, c.a)
        except (KeyError, IndexError) as x:
            w = ("model-error", str(x))
        k = "%s%s" % (w[0], (":%x" % w[1]) if w[0] in ("obs", "stop") or c.fam == "tc" and w[0] == "ret" else "")
        outs.setdefault(c.fam, {}).setdefault(k, 0)
        outs[c.fam][k] += 1
        for name, r in e.seen:
            d = reach.setdefault(c.fam, {}).setdefault(name, [0, 0])
            d[0 if r else 1] += 1
    for f in FAMILIES:
        print("OUTCOMES %s %s" % (f, " ".join("%s=%d" % kv for kv in sorted(outs.get(f, {}).items()))))
        for name, (tt, ff) in sorted(reach.get(f, {}).items()):
            print("REACH %s %s true=%d false=%d" % (f, name, tt, ff))
    return 0


def cmd_split(d, limit=None):
    """tc: the cases that reach the dead-flag test, by cell (target +0xC4 bit 1, a type-1 target in mode 12, the
    skill's TargetCorpse bit), each with the emulator's outcome (target kept or cleared) read from its own dump, and
    how many of the cell the spec's D2 reading (spec_d2) predicts otherwise."""
    cases = B.build(limit)
    calls = p1.read_out(os.path.join(d, "s2ae.out"))[0]
    cells = {}
    for c, k in zip(cases, calls):
        if c.fam != "tc" or "stop" in k:
            continue
        e = P3.RE()
        want = m_tc(e, c.a)
        if not any(n == "dead" for n, _ in e.seen):
            continue
        M = Mem(c.a["w"])
        t = M.d(M.d(U + 0x2C) + 0x58)
        dead = M.d(t + 0xC4) >> 1 & 1
        m12 = int(M.d(t) == 1 and M.d(t + 0x10) == 12)
        corpse = skb(c.a["sk"], 7) & 1
        got = observed("tc", k)[0]
        kept = int(struct.unpack("<I", got[2][0][:4])[0] != 0)
        spec = predict("tc", c.a, flip="spec_d2")[0]
        spec_kept = None if spec[0] != "ret" else int(struct.unpack("<I", spec[2][0][:4])[0] != 0)
        key = (dead, m12, corpse)
        v = cells.setdefault(key, [0, 0, 0, 0])
        v[0] += 1
        v[1] += kept
        v[2] += 1 - kept
        v[3] += int(spec_kept != kept)
        assert got == want, "emulator and model differ"
    print("TC-SPLIT dead m12 corpse cases kept cleared spec_d2_differs")
    for key in sorted(cells):
        print("CELL %d %d %d cases=%d kept=%d cleared=%d spec_d2_differs=%d" % (key + tuple(cells[key])))
    print("TC-SPLIT total=%d spec_d2_differs=%d" % (sum(v[0] for v in cells.values()),
                                                   sum(v[3] for v in cells.values())))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("cases", "check", "reach", "static", "sites", "split", "manifest"))
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
    if o.cmd == "sites":
        return cmd_sites()
    if o.cmd == "split":
        return cmd_split(o.dir, o.limit)
    B.cmd_manifest(o.dir, o.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

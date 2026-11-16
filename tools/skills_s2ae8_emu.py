#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S2ae part 8 (`lane/n66sa`): the stat setter sub_00627260_UnitSetStat run whole on a
declared stat-list world, alone and behind handlers 18, 26 and SkillWeaponWear, under Ghidra's p-code emulator
(ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java, compared with the models below; plus `static`, the
objdump listing of every function the setter runs.

    python3 -I tools/skills_s2ae8_emu.py cases [--dir D] [--limit N]   write D/s2ae.cases, D/s2ae.mem and the tables
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s2ae.cases D/s2ae.mem > D/s2ae.out
    python3 -I tools/skills_s2ae8_emu.py check [--dir D] [--limit N]   compare, account for traced reads, controls
    python3 -I tools/skills_s2ae8_emu.py reach [--limit N]             model outcomes and deciding tests per family
    python3 -I tools/skills_s2ae8_emu.py static                        objdump of the setter's functions
    python3 -I tools/skills_s2ae8_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66sa/s2ae/run8. Parts 1-7 (tools/skills_s2ae_emu.py, skills_s2ae2..7_emu.py) and their
run/ to run7/ are unchanged; this tool reuses part 1's check machinery, part 6's h18 and part 7's h26 and wear
generators and models in its module state only (their MonStats and Skills images merged: part 6's rows with part
7's +0x170 and +0x158 columns copied in). Every draw comes from random.Random("n66sa-s2ae8-<family>"); the declared
ItemStatCost rows from random.Random("n66sa-s2ae8-isc").

The approach follows batch S4e part 5d (lane/n66z, tools/items_s4e8_emu.py `addst`, read on its branch, not
imported): the list and its arrays are declared, the calls that allocate are the observed boundary, the CRT
memmove 0x00683840 runs whole. Here the world is a unit's whole stat list: the base array (+0x24), the cache (+0x48),
the client's changed-key array (+0x50, int32 keys), the stat callback (+0x5C, 0x0055B800 or none) with its argument
(+0x60), the parent chain (+0x34, up to two lists) and the declared ItemStatCost rows (+0x04, +0x05, +0x50..+0x53;
+0x05 bit 2, the getter's minimum, kept clear so the handlers' getters read as in parts 6 and 7); the rows of the
handlers' and mdts's stats (SHIPPED_ROWS) carry the shipped itemstatcost.bin's bytes at those six offsets (read from
workspace/merged at case time).

Observed boundaries (ADR-0021; the case ends there, registers, stack arguments and dumps compared):
  STATLIST_InsertEntry 0x00624C80   the key absent from the base array (from 0x006270F2) or a cache (0x006250D5)
  0x0040B4B0                        the array resize: RemoveEntry's shrink (0x00624D7E) or the changed-key array's
                                    growth (0x00624E73)
  0x0055B800                        the stat callback (indirect, 0x0062513E), when the list has one and the row's
                                    +0x05 bit 3 is set
  sub_006266C0_StatRecompute        a row with +0x51 or +0x52 non-zero (0x006269B4)
  h18: 0x00621E40 (0x005C02E9) after the setter; wear: 0x005531C0 (0x005DAB1D) after the setter, and part 7's
  PLAYER_UseAmmo, ItemBreak.

Families (rows: d = skills/dispatch):
  set    0x00627260 UnitSetStat (unit, stat, value, param; stdcall), whole: STATLIST_SetStatEx 0x006270B0 with the
         search 0x00624B90, STATLIST_RemoveEntry 0x00624D10 (memmove), STATLIST_Propagate 0x00626920 with
         STATLIST_CacheAdd 0x006250B0, STATLIST_MarkClientDirty 0x00624DD0 with 0x00624D90.     d124, d130, d156
  h18w   part 6's h18 (0x005C0260) with the setter whole, to 0x00621E40.                                     d124
  h26w   part 7's h26 (0x005C6690) with the setter whole, to the return (the packet's reduction).            d130
  wearw  part 7's wear (0x005DAA40) with the setter whole, to 0x005531C0.                                    d156
  mdts   sub_0064AC60_MissileDamageToStats (owner, missile, block, stat-12 value; stdcall), whole: its 35 setter
         calls and the owner's stat-180 entries by sub_006261D0_StatListGetEntries -> 0x00626110 with the lower-bound
         search 0x00624C10.                                                                       missiles 27, 95

Controls as parts 1-7: every named test reversed alone, every ordered compare's strictness switched alone; `sep`
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
import skills_s2ae5_emu as P5  # noqa: E402
import skills_s2ae6_emu as P6  # noqa: E402
import skills_s2ae7_emu as P7  # noqa: E402
from combat_s5e_emu import u32, s32, le32, tdiv, G_DT, DT, FATAL, ALLOC, ISC, ISC_N, ISC_SZ, NSTATES  # noqa: E402

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66sa", "s2ae", "run8")
FNS = {"set": 0x00627260, "h18w": 0x005C0260, "h26w": 0x005C6690, "wearw": 0x005DAA40, "mdts": 0x0064AC60}
FAMILIES = ("set", "h18w", "h26w", "wearw", "mdts")
NCASES = {"set": 6000, "h18w": 3000, "h26w": 3000, "wearw": 3000, "mdts": 3000}
POP = {"set": 0x10, "h18w": 0x14, "h26w": 0x14, "wearw": 0xC, "mdts": 0x10}
OLD = {"h18w": (P6, "h18"), "h26w": (P7, "h26"), "wearw": (P7, "wear")}
p1.FNS.update(FNS)

F_INSERT, F_POOL, F_CB, F_RECOMP = 0x00624C80, 0x0040B4B0, 0x0055B800, 0x006266C0
OBS_OVL, OBS_PKT = 0x00621E40, 0x005531C0
OBS_AMMO, OBS_BREAK, OBS_SETSTAT = P7.OBS_AMMO, P7.OBS_BREAK, P7.OBS_SETSTAT
OBSERVES = (F_INSERT, F_POOL, F_CB, F_RECOMP, OBS_OVL, OBS_PKT, OBS_AMMO, OBS_BREAK)
NARGS = {F_INSERT: 1, F_POOL: 4, F_CB: 4, F_RECOMP: 2, OBS_OVL: 3, OBS_PKT: 5, OBS_AMMO: 0, OBS_BREAK: 1}
REGS = {F_INSERT: ("eax", "esi"), F_POOL: ("ecx", "edx"), F_CB: ("ecx", "edx"), F_RECOMP: ("ecx", "edx"),
        OBS_OVL: (), OBS_PKT: ("ecx", "edx"), OBS_AMMO: ("ecx", "edx"), OBS_BREAK: ("ecx", "edx")}
OLD_SITES = {OBS_AMMO: 0x005DAAAD, OBS_BREAK: 0x005DAB3B}
POOL = 0x7E570000
W = 0x23000000                        # the setter world: the target's arrays and the parent lists
WB, WC, WD = W + 0x400, W + 0x800, W + 0xC00          # base, cache, changed-key arrays (0x400 bytes each)
PL, PC, QL, QC = W + 0x1000, W + 0x1400, W + 0x2000, W + 0x2400
SU = 0x23100000                       # set: the unit (its list at SU + SL_OFF)
SL_OFF = 0x200
SWITCH = (0, 1, 0, 1, 0, 1, 1, 0, 0)  # 0x00624EB8: stats 6..14 -> 0 return, 1 the ItemStatCost test
BITMASK = 0x006CE268
SSE_FLAG = 0x00994C88   # the CRT's copy-path flag (set once at start-up, 0x0069A8C5): memmove reads it for 256 bytes+

ISCT = None
SHIPPED_ISC = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel", "itemstatcost.bin")
MDTS = (0x15, 0x16, 0x30, 0x31, 0x13B, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B, 0x146, 0x3C, 0x3D,
        0x3E, 0x3F, 0x40, 0x41, 0x42, 0x13C, 0x13D, 0x13B, 0x79, 0x7A, 0x78, 0x19)   # block dwords 1..30, in call order
MDTS_FLAGS = ((0x100, 0x67), (0x200, 0x68), (0x400, 0x6A), (0x2, 0x8D))
SHIPPED_ROWS = tuple(sorted({6, 72, 0xC, 0xB4} | set(MDTS) | {s for _, s in MDTS_FLAGS}))


def isc_rows():
    """The declared ItemStatCost rows: +0x04, +0x05 (bit 2 clear), +0x50 keepzero, +0x51/+0x52 (op links, mostly 0),
    +0x53."""
    global ISCT
    if ISCT is None:
        r = random.Random("n66sa-s2ae8-isc")
        t = bytearray(ISC_N * ISC_SZ)
        for s in range(ISC_N):
            o = s * ISC_SZ
            t[o + 4] = r.getrandbits(8)
            t[o + 5] = r.getrandbits(8) & ~0x04
            t[o + 0x50] = r.choice([0, 0, 0, 1])
            t[o + 0x51] = 0 if r.random() < 0.85 else r.choice([1, r.getrandbits(8)])
            t[o + 0x52] = 0 if r.random() < 0.9 else 1
            t[o + 0x53] = r.choice([0, 0, 1])
        with open(SHIPPED_ISC, "rb") as f:   # rows 6 and 72 (the handlers' stats): the shipped bytes there
            raw = f.read()
        if struct.unpack_from("<I", raw, 0)[0] != 359:
            raise SystemExit("skills_s2ae8_emu: unexpected itemstatcost.bin")
        for s in SHIPPED_ROWS:
            for off in (4, 5, 0x50, 0x51, 0x52, 0x53):
                t[s * ISC_SZ + off] = raw[4 + s * ISC_SZ + off]
        ISCT = t
    return ISCT


def ib(stat, off):
    return isc_rows()[stat * ISC_SZ + off]


def merge_tables():
    """Part 6's MonStats and Skills images with part 7's +0x170 (MonStats) and +0x158 (Skills) columns copied in;
    both parts' models then read the same declared bytes."""
    ms6, ms2, sk6 = P6.tables()
    ms7, sk7, it, eq = P7.tables()
    ms, sk = bytearray(ms6), bytearray(sk6)
    for i in range(P6.MS_N):
        ms[i * P6.MS_SZ + 0x170:i * P6.MS_SZ + 0x172] = ms7[i * P6.MS_SZ + 0x170:i * P6.MS_SZ + 0x172]
    for i in range(P6.SK_N):
        sk[i * P6.SK_SZ + 0x158:i * P6.SK_SZ + 0x15C] = sk7[i * P6.SK_SZ + 0x158:i * P6.SK_SZ + 0x15C]
    P6.TABLES = (ms, ms2, sk)
    P7.TABLES = (ms, sk, it, eq)


# ----------------------------------------------------------------------------------------------- the setter model
class Hit(Exception):
    """An observed boundary reached inside the model: (address, return address, registers, stack arguments)."""


def wd(M, a, v):
    for i in range(4):
        M.w[a + i] = (u32(v) >> (8 * i)) & 0xFF


def wh(M, a, v):
    M.w[a] = v & 0xFF
    M.w[a + 1] = (v >> 8) & 0xFF


def sx16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def find8(M, desc, key):
    """0x00624B90: signed binary search of the (key, value) array; the index or None."""
    arr, n = M.d(desc), sx16(M.h(desc + 4))
    lo, hi = 0, n
    while lo < hi:
        mid = lo + tdiv(hi - lo, 2)
        k = s32(M.d(arr + 8 * mid))
        if s32(key) > k:
            lo = mid + 1
        elif s32(key) < k:
            hi = mid
        else:
            return mid
    return None


def remove(e, M, desc, idx, pool):
    """STATLIST_RemoveEntry 0x00624D10 (ESI desc, EDX entry; pool): close the gap, count - 1, and when the spare
    room exceeds 8 the capacity - 4 and the resize 0x0040B4B0 (observed)."""
    arr, n = M.d(desc), sx16(M.h(desc + 4))
    if idx >= n:
        raise KeyError("entry past the count")
    if e.c("rm_mid", idx, "<", n - 1):
        body = [M.b(arr + 8 * (idx + 1) + i) for i in range(8 * (n - idx - 1))]
        for i, x in enumerate(body):
            M.w[arr + 8 * idx + i] = x
    cnt = (M.h(desc + 4) + 0xFFFF) & 0xFFFF
    wh(M, desc + 4, cnt)
    cap = M.h(desc + 6)
    if e.c("rm_shrink", sx16(cap) - sx16(cnt), ">", 8):
        nc = (cap - 4) & 0xFFFF
        wh(M, desc + 6, nc)
        raise Hit(F_POOL, 0x00624D83, (pool, arr), (u32(sx16(nc) * 8), 0x006E90A4, 0x110, 0))


def cache_add(e, M, L, key, delta, stat):
    """STATLIST_CacheAdd 0x006250B0 (EBX list; key, delta, row, 0)."""
    desc = L + 0x48
    i = find8(M, desc, key)
    if not e.t("ca_found", i is not None):
        raise Hit(F_INSERT, 0x006250DA, (key, desc), (M.d(L),))
    ent = M.d(desc) + 8 * i
    old = M.d(ent + 4)
    new = u32(old + delta)
    wd(M, ent + 4, new)
    if e.c("ca_pos", s32(new), ">", 0) and e.t("ca_53", ib(stat, 0x53) != 0):
        wd(M, L + 0x10, M.d(L + 0x10) | 0x20000000)
    if e.t("ca_zero", new == 0) and not e.t("ca_keep", ib(stat, 0x50) != 0):
        remove(e, M, desc, i, M.d(L))
    cb = M.d(L + 0x5C)
    if e.t("ca_cb", cb != 0) and e.t("ca_cbbit", ib(stat, 5) & 8):
        raise Hit(cb, 0x00625140, (M.d(L + 0x60), M.d(L + 0x44)), (0, key, old, new))


def propagate(e, M, sl, key, delta):
    """STATLIST_Propagate 0x00626920 (ECX list, EDX key; delta, 0)."""
    stat = (key >> 16) & 0xFFFF
    if not e.t("pr_isc", stat < ISC_N):
        return
    fl = M.d(sl + 0x10)
    if e.t("pr_2000", fl & 0x2000):
        return
    dmg = ib(stat, 4) & 4
    cur = sl if e.t("pr_ext", fl & 0x80000000) else M.d(sl + 0x34)
    for _ in range(8):
        if not e.t("pr_cur", cur != 0):
            return
        if e.t("pr_op", ib(stat, 0x51) != 0 or ib(stat, 0x52) != 0):
            raise Hit(F_RECOMP, 0x006269B9, (cur, key), (ISC + stat * ISC_SZ, 0))
        cache_add(e, M, cur, key, delta, stat)
        f2 = M.d(cur + 0x10)
        cur = M.d(cur + 0x34)
        if e.t("pr_stop", f2 & 0x2000):
            return
        if dmg and e.t("pr_nodmg", f2 & 0x40000000):
            return
    raise KeyError("parent chain past 8")


def mark_dirty(e, M, L, key):
    """STATLIST_MarkClientDirty 0x00624DD0 (EBX list; key): the key into the sorted +0x50 int32 array."""
    if not e.t("md_ext", M.d(L + 0x10) & 0x80000000):
        return
    stat = (key >> 16) & 0xFFFF
    e.names.add("spec_md_all")
    if 6 <= stat <= 14 and e.flip != "spec_md_all":
        if not e.t("md_sw", SWITCH[stat - 6]):
            return
    if not e.t("md_isc", stat < ISC_N):
        return
    if not e.t("md_send", ib(stat, 5) & 0x10):
        return
    desc = L + 0x50
    arr, n = M.d(desc), sx16(M.h(desc + 4))
    lo, hi = 0, n
    while lo < hi:
        mid = lo + tdiv(hi - lo, 2)
        k = s32(M.d(arr + 4 * mid))
        if s32(key) > k:
            lo = mid + 1
        elif s32(key) < k:
            hi = mid
        else:
            return
    cap = M.h(L + 0x56)
    if not e.c("md_room", sx16(M.h(L + 0x54)), "<", sx16(cap)):
        nc = (cap + 4) & 0xFFFF
        wh(M, L + 0x56, nc)
        raise Hit(F_POOL, 0x00624E78, (M.d(L), arr), (u32(sx16(nc) * 4), 0x006E90A4, 0x162, 0))
    if lo < n:
        body = [M.b(arr + 4 * lo + i) for i in range(4 * (n - lo))]
        for i, x in enumerate(body):
            M.w[arr + 4 * lo + 4 + i] = x
    wd(M, arr + 4 * lo, key)
    wh(M, L + 0x54, (M.h(L + 0x54) + 1) & 0xFFFF)


def set_stat_ex(e, M, sl, stat, val, param):
    """STATLIST_SetStatEx 0x006270B0 (list, stat, value, param): 1 when the value changed."""
    if not e.t("sx_list", sl != 0):
        return 0
    key = u32((stat << 16) + (param & 0xFFFF))
    i = find8(M, sl + 0x24, key)
    if not e.t("sx_found", i is not None):
        if not e.t("sx_val", val != 0):
            return 0
        raise Hit(F_INSERT, 0x006270F7, (key, sl + 0x24), (M.d(sl),))
    ent = M.d(sl + 0x24) + 8 * i
    delta = u32(val - M.d(ent + 4))
    e.names.add("spec_add")
    if e.flip == "spec_add":
        delta, val = u32(val), u32(M.d(ent + 4) + val)
    if not e.t("sx_delta", delta != 0):
        return 0
    if e.t("sx_zero", u32(val) == 0):
        remove(e, M, sl + 0x24, i, M.d(sl))
    else:
        wd(M, ent + 4, val)
    propagate(e, M, sl, key, delta)
    if e.t("sx_ext", M.d(sl + 0x10) & 0x80000000) and e.t("sx_8", M.d(sl + 8) == 0):
        mark_dirty(e, M, sl, key)
    return 1


def unit_set_stat(e, M, u, stat, val, param):
    """sub_00627260_UnitSetStat (unit, stat, value, param): SetStatEx on unit +0x5C, then for a player the key."""
    sl = M.d(u + 0x5C)
    r = set_stat_ex(e, M, sl, stat, val, param)
    if e.t("us_ret", r != 0) and e.t("us_player", M.d(u) == 0):
        mark_dirty(e, M, M.d(u + 0x5C), u32((stat << 16) + (param & 0xFFFF)))


def dumped(M, dumps):
    """The dumps in address order (as the emulator's output is read)."""
    return tuple(bytes(M.b(va + i) for i in range(n)) for va, n in sorted(dumps))


def by_addr(dt, dumps):
    """A part 6/7 model's dumps (declared order) put in address order."""
    if dt is None:
        return None
    return tuple(x for _, x in sorted(zip([va for va, _ in dumps], dt)))


def hit_out(h, M, dumps):
    addr, rt, regs, args = h.args
    return ("obs", addr, tuple(u32(x) for x in regs), tuple(u32(x) for x in args), dumped(M, dumps), rt)


# ----------------------------------------------------------------------------------------------- the world
def put_arr(c, at, entries, cap, width=8):
    body = b"".join((le32(k) + le32(v)) if width == 8 else le32(k) for k, v in entries)
    body += b"\xEE" * (width * (cap - len(entries)))
    if body:
        c.put(at, body)


def desc(c, at, arr, n, cap):
    c.put(at, le32(arr) + struct.pack("<hH", n, cap & 0xFFFF))


def put_parent(c, rnd, L, CA, key, depth, more=()):
    """A parent list: the header fields CacheAdd and Propagate read, its cache with (or without) the key. -> dumps"""
    c.put(L, P6.rbytes(rnd, 0x64))
    c.put(L, le32(POOL + depth))
    c.put(L + 0x10, le32(rnd.choice([0, 0, 0x80000000, 0x2000, 0x40000000, 0xC0000000, rnd.getrandbits(32)])))
    ents = {rnd.randrange(1, ISC_N) << 16: rnd.getrandbits(32) for _ in range(rnd.randrange(5))}
    if rnd.random() < 0.9:
        ents[key] = rnd.choice([0, 1, rnd.getrandbits(32), rnd.randint(1, 5000)])
        for k in more:
            ents[k] = rnd.getrandbits(32)
    ents = sorted(ents.items(), key=lambda kv: s32(kv[0]))
    cap = len(ents) + rnd.choice([0, 0, 1, 3, 6, 9, 12])
    put_arr(c, CA, ents, cap)
    desc(c, L + 0x48, CA, len(ents), cap)
    c.put(L + 0x44, le32(rnd.choice([0, SU, rnd.getrandbits(32)])))
    c.put(L + 0x5C, le32(rnd.choice([0, 0, F_CB])))
    nxt = QL if depth == 0 and rnd.random() < 0.4 else 0
    c.put(L + 0x34, le32(nxt))
    dumps = [(L + 0x10, 4), (L + 0x48, 8)] + ([(CA, 8 * cap)] if cap else [])
    if nxt:
        dumps += put_parent(c, rnd, QL, QC, key, 1, more)
    return dumps


def put_world(c, rnd, u, sl, key, live, ext, val=None, base=None, wide=False, zero=False):
    """Rebuild the list at sl (unit u) as the setter's world, keeping its live entries `live` ({key: value}) where the
    handler read them: an extended list's cache holds them, a plain list's base array does."""
    c.put(sl + 0x00, le32(POOL))
    c.put(sl + 0x08, le32(0 if rnd.random() < 0.7 else rnd.getrandbits(32)))
    fl = rnd.choice([0, 0, 0, 0x2000, 0x40000000, 0x20000000, rnd.getrandbits(31)])
    c.put(sl + 0x10, le32((0x80000000 if ext else 0) | fl))
    c.put(sl + 0x44, le32(u))
    c.put(sl + 0x60, le32(rnd.getrandbits(32)))
    c.put(sl + 0x5C, le32(rnd.choice([0, F_CB, F_CB])))
    if ext:
        be = dict(base) if base is not None else {k: rnd.getrandbits(32) for k in live if rnd.random() < 0.5}
        if wide:
            pass
        elif rnd.random() < 0.88:
            be[key] = rnd.choice([live.get(key, 0), rnd.getrandbits(32), rnd.randint(1, 5000), 1]
                                 + ([val] if val is not None else []))
        else:
            be.pop(key, None)
        if zero and key in be and key in live and val is not None and rnd.random() < 0.2:
            live = dict(live)
            live[key] = u32(be[key] - val)           # the cache reaches 0 by the change
        ce = sorted(live.items(), key=lambda kv: s32(kv[0]))
        ccap = len(ce) + (rnd.choice([0, 0, 1, 2, 4, 7, 8]) if wide else rnd.choice([0, 0, 1, 2, 4, 7, 8, 9, 10, 12]))
        put_arr(c, WC, ce, ccap)
        desc(c, sl + 0x48, WC, len(ce), ccap)
        be = sorted(be.items(), key=lambda kv: s32(kv[0]))
    else:
        be = sorted(live.items(), key=lambda kv: s32(kv[0]))
    bcap = len(be) + (rnd.choice([0, 0, 1, 2, 4, 7, 8, 8, 9]) if wide else rnd.choice([0, 0, 1, 2, 4, 7, 8, 9, 10, 12]))
    put_arr(c, WB, be, bcap)
    desc(c, sl + 0x24, WB, len(be), bcap)
    dk = sorted({rnd.choice([rnd.randrange(1, ISC_N) << 16, key, rnd.getrandbits(32)]) for _ in range(rnd.randrange(7))},
                key=s32)
    dcap = len(dk) + (rnd.choice([0, 1, 40, 40, 40]) if wide else rnd.choice([0, 0, 1, 2, 5]))
    put_arr(c, WD, [(k, None) for k in dk], dcap, width=4)
    desc(c, sl + 0x50, WD, len(dk), dcap)
    par = PL if rnd.random() < 0.6 else 0
    c.put(sl + 0x34, le32(par))
    dumps = [(sl, 0x64)] + [(at, n) for at, n in ((WB, 8 * bcap), (WD, 4 * dcap)) if n]
    if ext and ccap:
        dumps.append((WC, 8 * ccap))
    if par:
        dumps += put_parent(c, rnd, PL, PC, key, 0, tuple(live) if wide else ())
    return dumps


def arr_of(M, d):
    arr, n = M.d(d), sx16(M.h(d + 4))
    return {M.d(arr + 8 * i): M.d(arr + 8 * i + 4) for i in range(max(n, 0))}


def live_of(M, sl):
    """The entries a getter reads: +0x48 when +0x10 bit 31 is set, else +0x24."""
    off = 0x48 if M.d(sl + 0x10) & 0x80000000 else 0x24
    arr, n = M.d(sl + off), sx16(M.h(sl + off + 4))
    return {M.d(arr + 8 * i): M.d(arr + 8 * i + 4) for i in range(max(n, 0))}, off == 0x48


# ----------------------------------------------------------------------------------------------- set
def gen_set(rnd):
    c = P7.Case("set")
    typ = rnd.choice([0, 0, 1, 1, 2, 3, 4, 5])
    c.put(SU, P6.rbytes(rnd, 0x100))
    c.put(SU, le32(typ))
    sl = SU + SL_OFF
    c.put(SU + 0x5C, le32(sl if rnd.random() < 0.98 else 0))
    c.put(sl, P6.rbytes(rnd, 0x64))
    stat = rnd.choice([6, 7, 8, 9, 10, 11, 12, 13, 14, 72, 70, 0x13B, 0xB4] + [rnd.randrange(ISC_N)] * 8
                      + [rnd.randrange(ISC_N, 0x10000), rnd.getrandbits(32)])
    param = rnd.choice([0] * 8 + [1, rnd.getrandbits(16), rnd.getrandbits(32)])
    key = u32((stat << 16) + (param & 0xFFFF))
    live = {rnd.randrange(1, ISC_N) << 16: rnd.getrandbits(32) for _ in range(rnd.randrange(8))}
    if rnd.random() < 0.9:
        live[key] = rnd.choice([0, 1, rnd.randint(1, 5000) << 8, rnd.getrandbits(32)])
    val = rnd.choice([0, 1, rnd.randint(1, 5000) << 8, rnd.getrandbits(32), 0x80000000, -1])
    dumps = put_world(c, rnd, SU, sl, key, live, rnd.random() < 0.85, val=u32(val), zero=True)
    c.args = [SU, u32(stat), u32(val), u32(param)]
    return P7.finish(c, dumps)


def m_set(e, a):
    M = P6.Mem(a["w"])
    u, stat, val, param = a["args"]
    try:
        unit_set_stat(e, M, u, stat, val, param)
    except Hit as h:
        return hit_out(h, M, a["dumps"])
    return ("ret", None, dumped(M, a["dumps"]))


# ----------------------------------------------------------------------------------------------- wrapped handlers
CAP = {}


def capture_obs(pc, regs, args, M, dumps):
    CAP["M"] = M
    return ("obs", pc, None if regs is None else tuple(u32(x) for x in regs), tuple(u32(x) for x in args),
            dumped(M, dumps))


def capture_muldiv(*xs):
    v = MULDIV(*xs)
    CAP["muldiv"] = v
    return v


MULDIV = p1.muldiv


def old_model(fam, e, a):
    mod, name = OLD[fam]
    CAP.clear()
    sv6, sv7, svm = P6.obs, P7.obs, p1.muldiv
    P6.obs, P7.obs, p1.muldiv = capture_obs, capture_obs, capture_muldiv
    try:
        return mod.MODEL[name](e, a)
    finally:
        P6.obs, P7.obs, p1.muldiv = sv6, sv7, svm


KEEP_OFF = {"h18w": 0.015, "h26w": 0.02, "wearw": 0.006}


def gen_wrapped(fam):
    mod, name = OLD[fam]

    def gen(rnd):
        for _ in range(400):      # most cases on the setter's path: a case off it is kept at KEEP_OFF
            c = mod.GEN[name](rnd)
            want = old_model(fam, p1.E(None), c.a)
            if want[0] == "obs" and want[1] == OBS_SETSTAT or rnd.random() < KEEP_OFF[fam]:
                break
        c.fam = fam
        if want[0] == "obs" and want[1] == OBS_SETSTAT:
            u, stat = want[3][0], want[3][1]
            M = P6.Mem(c.a["w"])
            sl = M.d(u + 0x5C)
        if want[0] == "obs" and want[1] == OBS_SETSTAT and sl:
            live, ext = live_of(M, sl)
            base = arr_of(M, sl + 0x24) if ext else None
            extra = put_world(c, rnd, u, sl, u32(stat << 16), live, ext, val=want[3][2], base=base)
        else:
            extra = []
        dumps = list(c.a["dumps"]) + extra
        old = c.a.get("regs")
        P7.finish(c, dumps)
        if old is not None:
            c.a["regs"] = old
        return c
    return gen


def m_wrapped(fam):
    def m(e, a):
        want = old_model(fam, e, a)
        dumps = a["dumps"]
        if want[0] == "ret":
            return want[:2] + (by_addr(want[2], dumps),)
        if want[0] != "obs":
            return want
        M = CAP.get("M")
        if want[1] != OBS_SETSTAT:
            return want[:4] + (by_addr(want[4], dumps), OLD_SITES[want[1]])
        u, stat, val, param = want[3]
        loss = CAP.get("muldiv")
        try:
            unit_set_stat(e, M, u, stat, val, param)
        except Hit as h:
            return hit_out(h, M, dumps)
        if fam == "h18w":
            return ("obs", OBS_OVL, (), (u, 0x97, 0), dumped(M, dumps), 0x005C02EE)
        if fam == "wearw":
            return ("obs", OBS_PKT, (a["regs"]["ESI"], 0x006E32E4), (0x9B, 1, 0x48, val, 0),
                    dumped(M, dumps), 0x005DAB22)
        pkt = a["args"][2]
        v = s32(M.d(pkt + 0x4C) - loss)
        e.names.add("spec_no_zero_floor")
        if not e.c("pk_pos", v, ">", 0) and e.flip != "spec_no_zero_floor":
            v = 0
        wd(M, pkt + 0x4C, v)
        return ("ret", 1, dumped(M, dumps))
    return m


# ----------------------------------------------------------------------------------------------- mdts
MU, MO, MDATA, MBLK = SU, SU + 0x1000, SU + 0x2000, SU + 0x2100
OARR = SU + 0x3000


def gen_mdts(rnd):
    c = P7.Case("mdts")
    c.put(MU, P6.rbytes(rnd, 0x100))
    c.put(MU, le32(3 if rnd.random() < 0.95 else rnd.choice([0, 1, 4])))
    c.put(MDATA, P6.rbytes(rnd, 0x20))
    c.put(MU + 0x14, le32(MDATA if rnd.random() < 0.9 else 0))
    sl = MU + SL_OFF
    c.put(MU + 0x5C, le32(sl))
    c.put(sl, P6.rbytes(rnd, 0x64))
    pz = rnd.choice([0.0, 0.03, 0.1, 0.3])                  # the share of zero values (each zero removes an entry)
    blk = [0 if rnd.random() < pz else rnd.choice([rnd.randint(1, 5000), rnd.getrandbits(32)]) for _ in range(31)]
    blk[0] = rnd.getrandbits(16) if rnd.random() < 0.8 else rnd.getrandbits(32)
    if rnd.random() < 0.3:
        blk[26] = blk[5]                     # 315 set twice to the same value
    c.put(MBLK, b"".join(le32(x) for x in blk))
    v12 = rnd.choice([0, rnd.randint(1, 99), rnd.getrandbits(32)])
    # the owner: stat 180 entries at layers, neighbours 179 and 181
    c.put(MO, P6.rbytes(rnd, 0x100))
    c.put(MO + 0x5C, le32(MO + SL_OFF if rnd.random() < 0.95 else 0))
    osl = MO + SL_OFF
    c.put(osl, P6.rbytes(rnd, 0x64))
    oext = rnd.random() < 0.85
    c.put(osl + 0x10, le32((0x80000000 if oext else 0) | rnd.getrandbits(31)))
    lay = sorted(rnd.sample(range(0x10000), rnd.choice([0, 0, 1, 2, 3, 5, 8])))
    oent = {(0xB4 << 16) | l: rnd.getrandbits(32) for l in lay}
    for st in (0xB3, 0xB5, rnd.randrange(1, ISC_N)):
        if rnd.random() < 0.6:
            oent[(st << 16) | rnd.choice([0, 1, rnd.getrandbits(16)])] = rnd.getrandbits(32)
    oe = sorted(oent.items(), key=lambda kv: s32(kv[0]))
    put_arr(c, OARR, oe, len(oe))
    desc(c, osl + 0x48, OARR, len(oe), len(oe))
    desc(c, osl + 0x24, OARR, len(oe), len(oe))
    # the missile's list: every key it sets present in base and cache (or one left out), values random
    keys = [0xC << 16] + [s << 16 for s in MDTS] + [s << 16 for _, s in MDTS_FLAGS] + [0xB4 << 16 | l for l in lay]
    keys = sorted(set(keys), key=s32)
    if keys and rnd.random() < 0.1:
        keys.remove(rnd.choice(keys))
    live = {k: rnd.choice([0, 1, rnd.getrandbits(32), rnd.getrandbits(32)]) for k in keys}
    for _ in range(rnd.randrange(4)):
        live[rnd.randrange(1, ISC_N) << 16] = rnd.getrandbits(32)
    base = {k: rnd.choice([0, 1, rnd.getrandbits(32)]) for k in live}
    dumps = put_world(c, rnd, MU, sl, keys[0] if keys else 0, live, rnd.random() < 0.9, base=base, wide=True)
    owner = MO if rnd.random() < 0.9 else 0
    c.args = [owner, MU, MBLK, v12]
    return P7.finish(c, dumps + [(MDATA + 0x14, 4)])


def entries(e, M, u, stat, mx):
    """sub_006261D0_StatListGetEntries -> 0x00626110: the extended list's +0x48 entries of the stat from its
    lower bound (0x00624C10), at most mx."""
    sl = M.d(u + 0x5C)
    if not e.t("ge_list", sl != 0) or not e.t("ge_ext", M.d(sl + 0x10) & 0x80000000):
        return []
    d = sl + 0x48
    arr, n = M.d(d), sx16(M.h(d + 4))
    key = s32(stat << 16)
    lo, hi = 0, n
    found = None
    while lo < hi:
        mid = lo + tdiv(hi - lo, 2)
        k = s32(M.d(arr + 8 * mid))
        if key > k:
            lo = mid + 1
        elif key < k:
            hi = mid
        else:
            found = mid
            break
    i = found if found is not None else (lo if lo < n else -1)
    out = []
    if i < 0:
        return out
    while i < n:
        k = M.d(arr + 8 * i)
        if not e.t("ge_stat", (k >> 16) & 0xFFFF == stat) or not e.c("ge_max", len(out), "<", mx):
            break
        out.append((k, M.d(arr + 8 * i + 4)))
        i += 1
    return out


def m_mdts(e, a):
    M = P6.Mem(a["w"])
    owner, mis, blk, v12 = a["args"]
    dumps = a["dumps"]
    if not e.t("mi_nz", mis != 0) or not e.t("mi_type3", M.d(mis) == 3):
        return ("ret", None, dumped(M, dumps))
    data = M.d(mis + 0x14)
    fl = M.d(data + 0x14) if e.t("mi_data", data != 0) else 0
    f = M.d(blk)
    if e.t("f_1", f & 1):
        fl |= 1
    if e.t("f_4", f & 4):
        fl |= 2
    if data:
        wd(M, data + 0x14, fl)
    seq = [(0xC, v12)] + [(st, M.d(blk + 4 * i)) for i, st in enumerate(MDTS, 1)]
    e.names.add("spec_315_once")
    if e.flip == "spec_315_once":
        seq = seq[:26] + seq[27:]
    e.names.add("spec_sorted")                               # the calls in stat order, not the code's
    if e.flip == "spec_sorted":
        seq = sorted(seq, key=lambda sv: sv[0])
    try:
        for st, v in seq:
            unit_set_stat(e, M, mis, st, v, 0)
        for bit, st in MDTS_FLAGS:
            if e.t("fl_%x" % st, f & bit):
                unit_set_stat(e, M, mis, st, 1, 0)
        if e.t("own_nz", owner != 0):
            for k, v in entries(e, M, owner, 0xB4, 0x80):
                unit_set_stat(e, M, mis, 0xB4, v, k & 0xFFFF)
    except Hit as h:
        return hit_out(h, M, dumps)
    return ("ret", None, dumped(M, dumps))


GEN = {"set": gen_set, "h18w": gen_wrapped("h18w"), "h26w": gen_wrapped("h26w"), "wearw": gen_wrapped("wearw"), "mdts": gen_mdts}
MODEL = {"set": m_set, "h18w": m_wrapped("h18w"), "h26w": m_wrapped("h26w"), "wearw": m_wrapped("wearw"), "mdts": m_mdts}


class NoSite(dict):
    def __missing__(self, key):
        return None


# ----------------------------------------------------------------------------------------------- spec, check
def write_spec(d):
    ms, ms2, sk = P6.tables()
    _, _, it, eq = P7.tables()
    for name, data in (("monstats.bin", ms), ("monstats2.bin", ms2), ("skills.bin", sk), ("items.bin", it),
                       ("itemtypes-eq.bin", eq), ("isc.bin", isc_rows())):
        with open(os.path.join(d, name), "wb") as f:
            f.write(bytes(data))
    dt = bytearray(0x1000)
    for off, v in ((0xC4, NSTATES), (0xA78, P6.MS), (0xA80, P6.MS_N), (0xA90, P6.MS2), (0xA98, P6.MS2_N),
                   (0xB98, P6.SK), (0xBA0, P6.SK_N), (0xBCC, ISC), (0xBD4, ISC_N), (0xBFC, P7.NTYPES),
                   (0xC00, P7.EQ_STRIDE), (0xC04, P7.EQ)):
        struct.pack_into("<I", dt, off, v)
    with open(os.path.join(d, "dt.bin"), "wb") as f:
        f.write(bytes(dt))
    with open(os.path.join(d, "game.bin"), "wb") as f:
        f.write(bytes(P6.GAME_SZ))
    lines = ["# plan 0066 S2ae part 8 (tools/skills_s2ae8_emu.py): declared tables",
             "dword %08x %08x" % (G_DT, DT),
             "dword %08x %08x" % (P7.G_ITN, P7.IT_N),
             "dword %08x %08x" % (P7.G_ITR, P7.IT),
             "dword %08x %08x" % (SSE_FLAG, 1),
             "load %08x %s" % (DT, os.path.join(d, "dt.bin")),
             "load %08x %s" % (P6.MS, os.path.join(d, "monstats.bin")),
             "load %08x %s" % (P6.MS2, os.path.join(d, "monstats2.bin")),
             "load %08x %s" % (P6.SK, os.path.join(d, "skills.bin")),
             "load %08x %s" % (P7.IT, os.path.join(d, "items.bin")),
             "load %08x %s" % (P7.EQ, os.path.join(d, "itemtypes-eq.bin")),
             "load %08x %s" % (ISC, os.path.join(d, "isc.bin")),
             "load %08x %s" % (P6.GAME, os.path.join(d, "game.bin"))]
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
    if want[0] == "ret" and len(want) == 3 and want[2] is not None and isinstance(want[2], tuple):
        return want
    return want


def same(want, got):
    if want[0] != got[0]:
        return False
    if want[0] == "ret":
        return (want[1] is None or want[1] == got[1]) and (want[2] is None or tuple(want[2]) == tuple(got[2]))
    if want[0] == "obs":
        return len(want) == len(got) and all(w is None or w == g for w, g in zip(want, got))
    return B.same(want, got)


READS = P6.READS + ((0x00683840, 0x00683C00, "the CRT memmove 0x00683840's jump tables (.text)"),
                    (0x00624EB0, 0x00624EC1, "MarkClientDirty's switch tables 0x00624EB0/0x00624EB8 (.text)"))


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
    merge_tables()
    B.FNS, B.FAMILIES, B.NCASES, B.POP, B.SITE = FNS, FAMILIES, NCASES, POP, NoSite()
    B.GEN, B.MODEL = GEN, MODEL
    B.observed, B.norm, B.account, B.write_spec, B.predict, B.same = observed, norm, account, write_spec, predict, same
    B.Case = P7.Case

    def build(limit=None):
        cases = []
        for fam in FAMILIES:
            rnd = random.Random("n66sa-s2ae8-" + fam)
            for _ in range(NCASES[fam] if limit is None else min(limit, NCASES[fam])):
                cases.append(GEN[fam](rnd))
        return cases
    B.build = build


# ----------------------------------------------------------------------------------------------- static reads
STATIC = (
    ("unitsetstat", 0x00627260, 0x0062729F), ("setstatex", 0x006270B0, 0x00627150), ("search", 0x00624B90, 0x00624BC5),
    ("remove", 0x00624D10, 0x00624D89), ("dirtyfind", 0x00624D90, 0x00624DCA), ("markdirty", 0x00624DD0, 0x00624EAE),
    ("propagate", 0x00626920, 0x006269E2), ("cacheadd", 0x006250B0, 0x0062514A),
    ("h18tail", 0x005C02D6, 0x005C02FA), ("h26tail", 0x005C6728, 0x005C6757), ("weartail", 0x005DAAFF, 0x005DAB2E),
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
            out[k] = out.get(k, 0) + 1
            for nm in names:
                if not nm.endswith("~") and not nm.startswith("spec_"):
                    alt = predict(fam, c.a, flip=nm)[0]
                    if not same(want, alt) or not same(alt, want):
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

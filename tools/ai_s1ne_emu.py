#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S1ne (`lane/n66ne`), part 1: monsters/ai machinery and README functions run under Ghidra's
p-code emulator (ADR-0015, ADR-0021, ADR-0029) with re/ghidra_scripts/EmuBoundary.java, compared with the models
below. No game, no slot. Ruling R2 of the plan 0066 inventory: no callee has a declared return. A callee either runs
whole on the declared image, or it is an observed boundary at which the case ends (ADR-0021): the case then claims the
map from the declared inputs to that call's registers and stack arguments, and nothing after it.

    python3 -I tools/ai_s1ne_emu.py cases [--dir D]    write D/s1ne.cases, D/s1ne.mem and the zeroed table images
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s1ne.cases D/s1ne.mem > D/s1ne.out
    python3 -I tools/ai_s1ne_emu.py check [--dir D]    compare D/s1ne.out with the models, account for every traced
                                                        read and write, run the per-test controls
    python3 -I tools/ai_s1ne_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66ne/s1ne/run. Every case draw comes from random.Random("n66ne-<family>"), so `cases`
regenerates identical files.

The declared image is tools/ai_s1e_emu.py's (its Mem, W and callee models are imported unchanged), plus a second state
mask array at DataTables +0x0D4 (the one 0x0063A320 reads) written by every world of this tool.

Observed boundaries (the memory spec's `observe` lines): 0x005417D0 UnitQueueEvent (MonModeStartNeutral's and
MonAiDelayEarlier's queue call; its route reaches EventBlockNew's pool allocation, tools/ai_s1ne_routes.py). Guards:
the fatal path (0x00408090, 0x00408A60, 0x00681E09) and the pool entries 0x0040B430, 0x0040B480, 0x0040B4B0.

Families (function; inventory rows, m = monsters-ai-machinery.md, r = monsters-ai-README.md):
  adu     0x005DC380 AiDistUnits, with UNIT_GetSizeX 0x00620510 and the path getters run whole (m17, m65)
  adps    0x005DC480 AiDistToPointSized (m17)
  dsq     0x005B0BD0 UnitDistSq over full-width static positions (m18)
  ovr     0x005DE190 MonAiPathOverride, AiPathOverrideSet run whole (m8, m36)
  ovs     0x005A6260 AiPathOverrideSet (m8, m37)
  neutral 0x005A73E0 MonModeStartNeutral to its UnitQueueEvent call, SUNIT_SetMode run whole for a monster already
          in mode NU (r5, r6, r17)
  dearl   0x005DE130 MonAiDelayEarlier to its UnitQueueEvent call, UNIT_CancelEvents run whole on records whose
          +0x02 bit 0 is set (r20)
  entry   0x005B15D0 MonAiEntryGet, states 10 to 12 through the gate and states 18 and past (r24, r25, r50)
  gate    0x00623470 the state 10-12 gate, MonModeAllowed 0x0046C140 run whole (r25)
  deadmin 0x005DCDA0 AiDeadMinionCb (m65, m111)
  fallen  0x005F1380 AiFallenCorpseCb (m65, m111)
  gmummy  0x005F2A00 AiGreaterMummyCb (m73, m111, r56)

Controls: as tools/ai_s1e_emu.py (every named test reversed alone, every ordered compare's strictness switched alone;
`sep` cases separate it, `passed` must be 0; a control with sep 0 is listed unseparated). Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ai_s1e_emu as S  # noqa: E402
from ai_s1e_emu import (DT, GAME, MS, MS2, MS_SZ, MS2_SZ, E, W, u32, s32, s8, s16, tdiv, pick)  # noqa: E402

ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66ne", "s1ne", "run")
NCASES = 240
OBSERVE = (0x005417D0,)
GUARDS = (0x00408090, 0x00408A60, 0x00681E09, 0x0040B430, 0x0040B480, 0x0040B4B0)
CONST_READS = ((0x006CE268, 0x80, "g_BitMask32"), (0x0062057C, 0x18, "UNIT_GetSizeX jump table"),
               (0x006E10E0, 0x14, "g_UnitHashOffsets"))
FNS = {"adu": 0x005DC380, "adps": 0x005DC480, "dsq": 0x005B0BD0, "ovr": 0x005DE190, "ovs": 0x005A6260,
       "neutral": 0x005A73E0, "dearl": 0x005DE130, "entry": 0x005B15D0, "gate": 0x00623470,
       "deadmin": 0x005DCDA0, "fallen": 0x005F1380, "gmummy": 0x005F2A00}
FAMILIES = tuple(FNS)
POP = {"adu": 0, "adps": 4, "dsq": 0, "ovr": 8, "ovs": 8, "neutral": 0, "dearl": 4, "entry": 0, "gate": 0,
       "deadmin": 8, "fallen": 8, "gmummy": 8}
FATAL = "fatal"


# ---- callee maps not in tools/ai_s1e_emu.py ----

def maskany(m, u, off):                     # 0x0063A130 with the mask array at DataTables + off (0x63A770, 0x63A320)
    lst = m.r32(u + 0x5C) if u else 0
    bits = m.r32(lst + 0x58) if lst and m.r32(lst + 0x10) & 0x80000000 else 0
    if bits == 0:
        return False
    n = tdiv(s32(m.r32(DT + 0xC4)) + 31, 32)
    mask = m.r32(DT + off)
    return any(m.r32(mask + 4 * i) & m.r32(bits + 4 * i) for i in range(max(0, n)))


def ms2rec(m, cls):                         # 0x00451FE0
    rec = S.ms_rec(m, cls)
    if rec == 0:
        return 0
    i = s16(m.r16(rec + 0x18))
    return MS2 + i * MS2_SZ if 0 <= i < s32(m.r32(DT + 0xA98)) else 0


def sizex(m, u):                            # 0x00620510 UNIT_GetSizeX (types 0, 1, 2, 4, 5 here)
    t = m.r32(u)
    if t == 0:
        return 2
    if t == 1:
        r = ms2rec(m, m.r32(u + 4))
        return s8(m.r8(r + 8)) if r else 0
    if t == 2:
        return m.r32(m.r32(m.r32(u + 0x14)) + 0xD0)
    if t == 4:
        return 1
    if t == 5:
        return 0
    raise ValueError("type outside the declared map")


def upos(m, u):                             # the inline position reads of AiDistUnits, AiDistToPointSized, UnitDistSq
    t = s32(m.r32(u))
    p = m.r32(u + 0x2C)
    if t == 2 or 4 <= t <= 5:
        return m.r32(p + 0x0C), m.r32(p + 0x10)
    if p == 0:
        return 0, 0
    return m.r16(p + 2), m.r16(p + 6)


def iabs(v):                                # test; jge; neg (INT_MIN stays)
    v = s32(v)
    return s32(-v) if v < 0 else v


def signcmp(e, name, a, b, signed):         # a > b; the control `name` takes the other signedness
    e.names.add(name)
    if e.flip == name:
        signed = not signed
    return s32(a) > s32(b) if signed else u32(a) > u32(b)


def octile(e, a, b):                        # the shared tail: floor 0, the larger doubled, cdq; sub; sar 1
    # The floor and the max are named tests with no strictness control: a 0 floored to 0 and a tie give the same
    # value under either strictness, so no case could separate those switches.
    if e.t("dx<0", s32(a) < 0):
        e.tag("dx floored")
        a = 0
    if e.t("dy<0", s32(b) < 0):
        e.tag("dy floored")
        b = 0
    v = u32(b + 2 * a) if e.t("dx>dy", s32(a) > s32(b)) else u32(a + 2 * b)
    if s32(v) < 0:
        e.tag("sum negative as i32 (sar of a wrapped sum)")
    return u32(s32(v + (1 if s32(v) < 0 else 0)) >> 1)


def m_adu(e, a):                            # AiDistUnits(a; b)
    m, A, B = e.m, a["A"], a["B"]
    (xa, ya), (xb, yb) = upos(m, A), upos(m, B)
    dx, dy = iabs(u32(xa - xb)), iabs(u32(ya - yb))
    sz = sizex(m, A)
    e.tag("size %s" % ("negative" if s32(sz) < 0 else "0" if sz == 0 else "positive"))
    return octile(e, u32(dx - sz), u32(dy - sz))


def m_adps(e, a):                           # AiDistToPointSized(u; x, y)
    m, U = e.m, a["U"]
    ux, uy = upos(m, U)
    dx, dy = iabs(u32(ux - a["x"])), iabs(u32(uy - a["y"]))
    h = (u32(sizex(m, U)) >> 1) + 1
    e.tag("size %s" % ("negative (shr of the unsigned word)" if s32(sizex(m, U)) < 0 else "0 or positive"))
    return octile(e, u32(dx - h), u32(dy - h))


def m_dsq(e, a):
    m = e.m
    (xa, ya), (xb, yb) = upos(m, a["A"]), upos(m, a["B"])
    dx, dy = u32(xa - xb), u32(ya - yb)
    if s32(dx) * s32(dx) >= 1 << 32 or s32(dy) * s32(dy) >= 1 << 32:
        e.tag("a square past 2^32 (wrapped)")
    if not 0 <= s32(dx) * s32(dx) + s32(dy) * s32(dy) < 1 << 31:
        e.tag("sum past 2^31 - 1 (wrapped)")
    else:
        e.tag("sum fits")
    return u32(dy * dy + dx * dx)


def ovset(e, ctl, typ, param, byte):        # 0x005A6260 AiPathOverrideSet
    m = e.m
    if e.t("type!=0", typ != 0):
        m.w32(ctl + 0x18, typ)
    if e.t("param!=0", param != 0):
        m.w32(ctl + 0x1C, param)
    byte &= 0xFF
    if e.t("byte!=0", byte != 0):
        if e.c("byte>=78", byte, ">=", 0x4E):
            e.tag("byte capped at 77")
            byte = 0x4D
        m.w8(ctl + 0x20, byte)


def m_ovs(e, a):
    ovset(e, a["ctl"], a["type"], a["param"], a["byte"])
    return None


def m_ovr(e, a):                            # MonAiPathOverride(unit, type; param, byte)
    m, U, typ, prm = e.m, a["U"], a["type"], a["param"]
    if e.t("param out", u32(prm + 0x7E) > 0xFC):     # lea esi, [eax+0x7E]; cmp esi, 0xFC; ja: the fatal entry
        e.tag("param outside -126..126: fatal")
        return FATAL
    if e.t("type=1", typ == 1):
        e.tag("type 1 -> 7")
        typ = 7
    md = m.r32(U + 0x14) if U and m.r32(U) == 1 else 0
    ctl = m.r32(md + 0x2C) if e.t("monster", md != 0) else 0
    e.tag("MonPathCtl" if ctl else "no MonsterData: AiPathOverrideSet with ECX 0")
    ovset(e, ctl, typ, prm, a["byte"])
    return None


def first_frame(m, U, kind):                # 0x005415A0 UnitEventFirstFrame(unit; kind)
    r, best = m.r32(U + 0xDC), 0
    while r:
        if m.r8(r) == kind:
            f = s32(m.r32(r + 4))
            if f > 0 and (f < s32(best) or best == 0):
                best = f
        r = m.r32(r + 0x24)
    return best


def m_neutral(e, a):                        # MonModeStartNeutral(game, cmd): to UnitQueueEvent or the return
    m, G, U = e.m, GAME, a["U"]
    T = m.r32(G + 0xA8)
    e.names.add("pending>T unsigned")
    if e.c("pending>T", s32(first_frame(m, U, 2)), ">", s32(T)) if e.flip != "pending>T unsigned" else \
            u32(first_frame(m, U, 2)) > u32(T):
        e.tag("pending later: no queue")
        return 1
    if e.t("state21", S.hasstate(m, U, 0x15)):
        e.tag("state 21")
        return ("obs", G, U, [2, u32(T + 0x2D), 0, 0])
    md = m.r32(U + 0x14)
    rec = m.r32(md) if md else 0
    if rec == 0:
        e.tag("no MonStats record: no queue")
        return 1
    if e.t("hell byte", m.r8(G + 0x6A) != 0 or m.r32(G + 0x74) != 0):
        n = m.r8(rec + 0x4F + m.r8(G + 0x6D))
        e.tag("aidel by difficulty")
    else:
        n = m.r8(rec + 0x4F)
        e.tag("aidel column 0")
    if e.c("aidel>0", n, ">", 0):
        e.tag("aidel %s" % ("non-zero"))
    else:
        n = 15
        e.tag("aidel 0: 15")
    return ("obs", G, U, [2, u32(T + n), 0, 0])


def m_dearl(e, a):                          # MonAiDelayEarlier(game, unit; n)
    m, G, U = e.m, GAME, a["U"]
    n = a["n"]
    if e.t("n=0", n == 0):
        e.tag("n 0: 1")
        n = 1
    elif s32(n) < 0:
        e.tag("n negative: T + n")
    T = m.r32(G + 0xA8)
    f = first_frame(m, U, 2)
    go = True
    e.names.add("pending<T+n~")
    if e.t("pending", f != 0) and e.t("pending!=T", f != T):
        if signcmp(e, "pending<T+n signed", u32(T + n), f, False) if e.flip != "pending<T+n~" else \
                u32(T + n) >= u32(f):
            go = False
    if not go:
        e.tag("pending earlier than T + n: kept")
        return f                            # EAX still holds UnitEventFirstFrame's return
    e.tag("requeued" if f else "none pending")
    r = m.r32(U + 0xDC)                     # UNIT_CancelEvents(game, unit, 2, 0): records with +0x02 bit 0 marked
    while r:
        nxt = m.r32(r + 0x24)
        if m.r8(r) == 2:
            m.w16(r + 2, m.r16(r + 2) | 8)
        r = nxt
    return ("obs", G, U, [2, u32(T + n), 0, 0])


def gate(e, cls):                           # 0x00623470
    m = e.m
    rec = S.ms_rec(m, cls)
    if rec == 0:
        return 0
    r2 = ms2rec(m, cls)
    if not e.t("allowed", r2 != 0 and m.r8(r2 + 0xF0) & 4):
        return 0
    if e.t("boss", m.r8(rec + 0x0C) & 0x40):
        return 0
    return 1 if e.t("e0 bit0", m.r8(rec + 0x0E) & 1) else 0


def m_gate(e, a):
    r = gate(e, a["cls"])
    e.tag("gate %d" % r)
    return r


def m_entry(e, a):                          # MonAiEntryGet(U, state)
    m, U, st = e.m, a["U"], a["state"]
    md = m.r32(U + 0x14) if U and m.r32(U) == 1 else 0
    rec = m.r32(md) if md else 0
    if e.t("state!=0", st != 0):
        if e.t("state 10-12", st in (10, 11, 12)):
            g = gate(e, s32(m.r32(U + 4)) if U else -1)
            if e.t("gate", g != 0):
                e.tag("state 10-12, gate true")
                return 0x0073D358 + 16 * st
            e.tag("state 10-12, gate false: class row")
        else:
            e.tag("state %s" % ("18 and past" if st >= 18 else "1-9, 13-17"))
            return u32(0x0073D358 + 16 * st)
    w = m.r16(rec + 0x1E)
    if e.t("row in range", s16(w) >= 0 and w < 0x94):
        return 0x0073CA18 + 16 * s16(w)
    return 0x0073CA18


def m_deadmin(e, a):                        # AiDeadMinionCb(G, U; cand, blk)
    m, U, c, blk = e.m, a["U"], a["cand"], a["blk"]
    d = s32(m_adu(E(m), {"A": U, "B": c}))
    if e.c("dist>bound", d, ">", s32(m.r32(blk + 0xC))):
        return 0
    if not e.t("type1", m.r32(c) == 1):
        return 0
    if not e.t("mode12", m.r32(c + 0x10) == 12):
        return 0
    if not e.t("c4 bit1", m.r32(c + 0xC4) >> 1 & 1):
        return 0
    if e.t("set33", maskany(m, c, 0x150)):
        return 0
    if not e.t("owner=U", S.mowner(m, c) == U):
        return 0
    e.tag("taken")
    m.w32(blk + 4, m.r32(blk + 4) + 1)
    m.w32(blk, c)
    m.w32(blk + 8, d)
    return 0


def m_fallen(e, a):                         # AiFallenCorpseCb(G, U; cand, blk)
    m, U, c, blk = e.m, a["U"], a["cand"], a["blk"]
    if not e.t("cand!=U", c != U) or c == 0 or not e.t("type1", m.r32(c) == 1):
        return 0
    b = S.baseid(m, c)
    if b < 0 or b >= S.ms_count(m):
        return 0
    if not e.t("base 19 or 58", b in (0x13, 0x3A)):
        return 0
    if not e.t("align0", S.align(m, c) == 0):
        return 0
    if not e.t("c4 bit1", m.r32(c + 0xC4) >> 1 & 1):
        return 0
    if e.t("set33", maskany(m, c, 0x150)):
        return 0
    if not e.t("mode12", m.r32(c + 0x10) == 12):
        return 0
    if e.t("setD4", maskany(m, c, 0xD4)):
        return 0
    d = s32(S.distsq(m, U, c))
    if d < 0:
        e.tag("UnitDistSq negative (wrapped)")
    e.names.add("dsq unsigned")
    if e.c("dsq>bound", d, ">", s32(m.r32(blk + 0xC))) if e.flip != "dsq unsigned" else \
            u32(d) > m.r32(blk + 0xC):
        return 0
    if e.t("champ or unique", S.typeflag(m, c, 0xC)):
        return 0
    e.tag("taken")
    m.w32(blk + 4, m.r32(blk + 4) + 1)
    m.w32(blk, c)
    m.w32(blk + 8, d)
    return 0


def isundead(m, c):                         # 0x0063E990 MONSTATS_IsUndead
    if c == 0 or m.r32(c) != 1:
        return 0
    rec = S.ms_rec(m, m.r32(c + 4))
    return 1 if rec and m.r8(rec + 0xD) & 0x18 else 0


def m_gmummy(e, a):                         # AiGreaterMummyCb(G, U; cand, blk)
    m, U, c, blk = e.m, a["U"], a["cand"], a["blk"]
    if c == 0 or not e.t("type1", m.r32(c) == 1) or not e.t("cand!=U", c != U):
        return 0
    if not e.t("alignsame", S.alignsame(m, U, c)):
        return 0
    if not e.t("align!=2", S.align(m, c) != 2):
        return 0
    if not e.t("c4 bit1", m.r32(c + 0xC4) >> 1 & 1):
        return 0
    if e.t("set33", maskany(m, c, 0x150)):
        return 0
    rec = S.ms_rec(m, m.r32(c + 4))
    if e.t("undead mode", m.r32(blk + 0x14) != 0):
        if not e.t("IsUndead", isundead(m, c)):
            return 0
    elif not e.t("lUndead", m.r8(rec + 0xD) & 8):
        return 0
    if not e.t("uniquesToo", m.r32(blk + 0x18) != 0):
        e.names.add("mask 0xC")             # the control: champion or unique refused (the mask 0x0C), not 8 alone
        if e.t("unique", S.typeflag(m, c, 0xC if e.flip == "mask 0xC" else 8)):
            return 0
    d = s32(S.distsq(m, U, c))
    if d < 0:
        e.tag("UnitDistSq negative (wrapped)")
    e.names.add("dsq unsigned")
    if e.c("dsq>bound", d, ">", s32(m.r32(blk + 0x10))) if e.flip != "dsq unsigned" else \
            u32(d) > m.r32(blk + 0x10):
        return 0
    m.w32(blk + 0xC, m.r32(blk + 0xC) + 1)
    if e.t("mode12", m.r32(c + 0x10) == 12) and not e.t("setD4", maskany(m, c, 0xD4)):
        e.tag("corpse")
        if S.typeflag(m, c, 4) and not S.typeflag(m, c, 8):
            e.tag("corpse, champion flag 4 only, uniquesToo %d" % (m.r32(blk + 0x18) != 0))
        m.w32(blk + 8, m.r32(blk + 8) + 1)
        m.w32(blk, c)
        return 0
    if e.t("hp!=max", S.getstat(m, c, 6) != S.maxhp(m, c)) and e.t("mode!=0", m.r32(c + 0x10) != 0):
        e.tag("wounded")
        m.w32(blk + 8, m.r32(blk + 8) + 1)
        m.w32(blk + 4, c)
        return 0
    e.tag("in range only")
    return 0


MODELS = {"adu": m_adu, "adps": m_adps, "dsq": m_dsq, "ovr": m_ovr, "ovs": m_ovs, "neutral": m_neutral,
          "dearl": m_dearl, "entry": m_entry, "gate": m_gate, "deadmin": m_deadmin, "fallen": m_fallen,
          "gmummy": m_gmummy}


# ---- the case writer ----

def world(rnd):
    w = W(rnd)
    m = w.m
    mask = m.alloc(0x40)
    m.w32(DT + 0xD4, mask)
    for i in range(16):
        m.w32(mask + 4 * i, rnd.getrandbits(32) & rnd.getrandbits(32) & rnd.getrandbits(32))
    return w, m


def place(w, u, typ, x, y):
    m = w.m
    p = m.r32(u + 0x2C)
    if typ == 2 or 4 <= typ <= 5:
        m.w32(p + 0x0C, u32(x))
        m.w32(p + 0x10, u32(y))
    else:
        m.w16(p + 2, x)
        m.w16(p + 6, y)


def mk(w, typ, **kw):
    """A unit of any type 0..5 with the fields the size and position reads take."""
    rnd, m = w.rnd, w.m
    u = w.unit(typ=typ, **kw)
    if typ == 2:
        d = m.alloc(0x10)
        rec = m.alloc(0x100)
        m.w32(u + 0x14, d)
        m.w32(d, rec)
        m.w32(rec + 0xD0, pick(rnd, 0, 1, 2, 3, 5, 0xFFFFFFFF, rnd.getrandbits(32)))
    if typ in (2, 4, 5) and rnd.randrange(3) == 0:
        place(w, u, typ, rnd.getrandbits(32), rnd.getrandbits(32))
    if typ in (0, 1, 3) and rnd.randrange(10) == 0:
        m.w32(u + 0x2C, 0)
    return u


def ms2size(w, cls):
    m, rnd = w.m, w.rnd
    rec = ms2rec(m, cls)
    if rec:
        m.w8(rec + 8, pick(rnd, 0, 1, 2, 3, 4, 0xFF, 0xFE, 0x80, 0x7F))


def gen_dist(fam, rnd):
    w, m = world(rnd)
    ta = pick(rnd, 0, 1, 1, 2, 4, 5)
    A = mk(w, ta)
    if ta == 1:
        ms2size(w, m.r32(A + 4))
    if fam == "adps":
        ax, ay = upos(m, A)
        x = u32(ax + pick(rnd, 0, 1, -1, 2, -2, rnd.randrange(-40, 40), rnd.randrange(-40, 40),
                          rnd.getrandbits(32)))
        y = u32(ay + pick(rnd, 0, 1, -1, 3, rnd.randrange(-40, 40), rnd.randrange(-40, 40), rnd.getrandbits(32)))
        return m, {"U": A, "x": x, "y": y}, (FNS[fam], A, x, [y], []), []
    tb = pick(rnd, 0, 1, 1, 2, 3, 4, 5)
    B = mk(w, tb)
    if m.r32(A + 0x2C) and m.r32(B + 0x2C) and rnd.randrange(3):
        ax, ay = upos(m, A)
        dx = pick(rnd, 0, 1, -1, 2, 5, -7, rnd.randrange(-60, 60), rnd.randrange(-300, 300))
        dy = pick(rnd, 0, 1, -1, 3, -4, rnd.randrange(-60, 60), rnd.randrange(-300, 300))
        if fam == "dsq" and rnd.randrange(3) == 0:
            dx = pick(rnd, 46340, -46340, 46341, 0xFFFF, -0xFFFF, rnd.getrandbits(31))
            dy = pick(rnd, 0, 1, 46340, 46341, rnd.getrandbits(31))
        place(w, B, tb, (ax + dx) & (0xFFFFFFFF if tb in (2, 4, 5) else 0xFFFF),
              (ay + dy) & (0xFFFFFFFF if tb in (2, 4, 5) else 0xFFFF))
    return m, {"A": A, "B": B}, (FNS[fam], A, B, [], []), []


def gen_ov(fam, rnd):
    w, m = world(rnd)
    typ = pick(rnd, 0, 1, 2, 5, 6, 7, 13, 100, 101, rnd.getrandbits(32))
    prm = pick(rnd, 0, 1, -1, 5, 126, -126, 127, -127, 128, 0x7FFFFFFF, rnd.randrange(-126, 127),
               rnd.randrange(-126, 127), rnd.randrange(-126, 127), rnd.getrandbits(32))
    byt = pick(rnd, 0, 1, 5, 76, 77, 78, 79, 0xFF, rnd.getrandbits(8), rnd.getrandbits(32))
    ctl = m.alloc(0x40)
    for off in (0x18, 0x1C):
        m.w32(ctl + off, pick(rnd, 0, rnd.getrandbits(32)))
    m.w8(ctl + 0x20, pick(rnd, 0, rnd.getrandbits(8)))
    dumps = [(ctl + 0x18, 9)]
    scratch = []
    if fam == "ovs":
        return m, {"ctl": ctl, "type": u32(typ), "param": u32(prm), "byte": byt}, \
            (FNS[fam], ctl, u32(typ), [u32(prm), byt], []), dumps
    ut = pick(rnd, 1, 1, 1, 1, 0, 2, 4)
    U = mk(w, ut, md=rnd.randrange(8) != 0) if ut == 1 else mk(w, ut)
    if ut == 1 and m.r32(U + 0x14):
        m.w32(m.r32(U + 0x14) + 0x2C, ctl)
    else:                                   # no MonsterData: the stores go to 0 + 0x18.. (case memory)
        scratch = [(0, 0x40)]
        dumps = [(0x18, 9)]
        for i in range(0, 0x40, 4):
            m.w32(i, 0)
    if ut == 2:
        m.w32(U + 0x14, 0)
    return m, {"U": U, "type": u32(typ), "param": u32(prm), "byte": byt, "scratch": scratch}, \
        (FNS[fam], U, u32(typ), [u32(prm), byt], []), dumps


def events(w, U, kinds, T):
    m, rnd = w.m, w.rnd
    prev = U + 0xDC
    recs = []
    for k in kinds:
        r = m.alloc(0x30)
        m.w8(r, k)
        m.w16(r + 2, 1 | (rnd.getrandbits(15) << 1 if k != 2 else 0))
        m.w32(r + 4, pick(rnd, 0, T, u32(T + 1), u32(T - 1), u32(T + rnd.randrange(1, 60)),
                          u32(T - rnd.randrange(1, 60)), rnd.getrandbits(32), 0xFFFFFFFF))
        m.w32(prev if prev == U + 0xDC else prev + 0x24, r)
        prev = r
        recs.append(r)
    return recs


def gen_queue(fam, rnd):
    w, m = world(rnd)
    T = pick(rnd, rnd.randrange(1, 1 << 20), rnd.randrange(1, 100), 0x7FFFFFF0 + rnd.randrange(16),
             rnd.randrange(1 << 20), 0x80000000 + rnd.randrange(1 << 20))       # the last: a frame past 2^31
    m.w32(GAME + 0xA8, T)
    U = w.unit(typ=1, mode=1, states=(0x15,) if rnd.randrange(4) == 0 else ())
    md = m.r32(U + 0x14)
    if fam == "neutral":
        if rnd.randrange(12) == 0:
            m.w32(md, 0)
        else:
            rec = S.ms_rec(m, m.r32(U + 4)) or S.MS
            m.w32(U + 4, (rec - S.MS) // MS_SZ)
            m.w32(md, rec)
            for i in range(3):
                m.w8(rec + 0x4F + i, pick(rnd, 0, 0, 1, 15, 20, 255, rnd.getrandbits(8)))
        m.w8(GAME + 0x6A, pick(rnd, 0, 0, 1, rnd.getrandbits(8)))
        m.w32(GAME + 0x74, pick(rnd, 0, 0, 1, rnd.getrandbits(32)))
        if rnd.randrange(4) == 0:           # a queued-hit list with no record of this unit (no free)
            q = m.alloc(0x90)
            m.w32(q + 4, pick(rnd, 0, 2, 3, 4))         # another unit type: 0x0057C980 frees no record
            m.w32(q + 8, m.r32(U + 0x0C))
            m.w32(U + 0xAC, q)
    kinds = [pick(rnd, 2, 2, 1, 3, 0) for _ in range(pick(rnd, 0, 1, 1, 2, 3, 4))]
    recs = events(w, U, kinds, T)
    dumps = [(r, 4) for r in recs]
    if fam == "neutral":
        cmd = m.alloc(0x20)
        m.w32(cmd + 4, U)
        return m, {"U": U}, (FNS[fam], GAME, cmd, [], []), dumps
    n = pick(rnd, 0, 1, 2, 10, 20, 25, -1, rnd.randrange(1, 100), rnd.getrandbits(32))
    return m, {"U": U, "n": u32(n)}, (FNS[fam], GAME, U, [u32(n)], []), dumps


def gen_entry(rnd):
    w, m = world(rnd)
    U = w.unit(typ=1)
    rec = S.ms_rec(m, m.r32(U + 4)) or S.MS
    m.w32(U + 4, (rec - S.MS) // MS_SZ if rnd.randrange(8) else pick(rnd, 0x300, 0xFFFFFFFF))
    p = m.alloc(0x40)
    m.w32(m.r32(U + 0x14), p)
    m.w16(p + 0x1E, pick(rnd, 0, 1, 0x93, 0x94, -1, rnd.randrange(0x94)))
    gate_bits(w, m.r32(U + 4))
    st = pick(rnd, 10, 11, 12, 10, 11, 12, 18, 19, 20, 0x20, 0xFF, 0x1000, rnd.randrange(18, 1 << 16),
              rnd.getrandbits(32), 0, 9, 13, 17)
    return m, {"U": U, "state": u32(st)}, (FNS["entry"], U, u32(st), [], []), []


def gate_bits(w, cls):
    m, rnd = w.m, w.rnd
    rec = S.ms_rec(m, cls)
    if rec == 0:
        return
    m.w16(rec + 0x18, pick(rnd, 0, 1, 5, 0x7F, -1, 0x200, rnd.randrange(0x10)))
    r2 = ms2rec(m, cls)
    if r2:
        m.w8(r2 + 0xF0, pick(rnd, 4, 4, 4, 0, 0xFB, 0xFF, rnd.getrandbits(8)))
    m.w8(rec + 0x0C, pick(rnd, 0, 0, 0x40, 0xBF, rnd.getrandbits(8)))
    m.w8(rec + 0x0E, pick(rnd, 1, 1, 0, 0xFE, 0xFF, rnd.getrandbits(8)))


def gen_gate(rnd):
    w, m = world(rnd)
    cls = pick(rnd, rnd.randrange(S.ms_count(m)), rnd.randrange(S.ms_count(m)), rnd.randrange(S.ms_count(m)),
               -1, S.ms_count(m), 0x7FFFFFFF)
    gate_bits(w, cls)
    return m, {"cls": u32(cls)}, (FNS["gate"], u32(cls), 0, [], []), []


def gen_cb(fam, rnd):
    w, m = world(rnd)
    brk = rnd.randrange(12) if rnd.randrange(3) == 0 else -1
    U = w.unit(typ=1, mode=pick(rnd, 1, 2, 3), al=pick(rnd, 0, 0, 0, 1, 2),
               x=rnd.randrange(0x400, 0xFC00), y=rnd.randrange(0x400, 0xFC00))
    blk = m.alloc(0x40)
    bound = pick(rnd, 0, 1, 25, 100, 225, 400, 625, 1024, 2500, 0x7FFFFFFF, -1, rnd.getrandbits(16), 100, 225, 9, 16)
    d2 = max(0, s32(bound) + pick(rnd, -1, 0, 0, 1, -50, 30)) if s32(bound) >= 0 else 0
    if fam == "deadmin":                    # an AI distance: a near point by its own measure
        d2 = max(0, s32(bound) + pick(rnd, -1, 0, 0, 1, -5, 3)) if 0 <= s32(bound) < 4000 else rnd.getrandbits(10)
    if rnd.randrange(6) == 0:
        d2 = rnd.getrandbits(18)
    if fam == "deadmin":
        x0, y0 = upos(m, U)
        k = d2 + rnd.randrange(3)
        dx = rnd.randrange(0, k + 1)
        xy = ((x0 + (dx if rnd.randrange(2) else -dx)) & 0xFFFF, (y0 + rnd.choice((k, -k))) & 0xFFFF)
    else:
        xy = w.near_xy(U, d2)
    ctyp = pick(rnd, 0, 2, 4) if brk == 0 else 1
    mode = 12 if brk != 1 else pick(rnd, 0, 1, 2, 3, 4)
    if fam == "gmummy" and rnd.randrange(3) == 0:
        mode = pick(rnd, 0, 1, 2, 3, 8)
    c4 = 2 if brk != 2 else pick(rnd, 0, 4, 0x200)
    al = 0 if brk != 3 else pick(rnd, 1, 2)
    if fam == "gmummy":
        al = S.align(m, U) if brk != 3 else pick(rnd, 0, 1, 2)
    states = ()
    if brk == 4 or rnd.randrange(6) == 0:
        states = (rnd.randrange(32 * 8),)
    hp = rnd.getrandbits(20)
    mx = hp if rnd.randrange(3) == 0 else rnd.getrandbits(20)
    c = mk(w, ctyp, cls=rnd.randrange(S.ms_count(m)), mode=mode, x=xy[0], y=xy[1], c4=c4, al=al, states=states, hp=hp, mx=mx,
           mdflags=pick(rnd, 0, 0, 0, 4, 8, 0xC, 0x10) if brk != 5 else pick(rnd, 4, 8))
    cls = m.r32(c + 4)
    if ctyp == 1 and S.ms_rec(m, cls):
        rec = S.ms_rec(m, cls)
        if fam == "fallen":
            w.setbase(cls, pick(rnd, 0x13, 0x3A, 0x13, 0x3A, 0x14, 0x39, cls) if brk != 6 else 0x12)
        m.w8(rec + 0xD, pick(rnd, 8, 8, 0x10, 0x18, 0, 0xF7) if brk != 7 else 0)
    if fam == "deadmin":
        o = U if brk != 8 else w.unit(typ=1)
        if rnd.randrange(10) and m.r32(c) == 1:
            w.set_owner(c, o)
        if c != 0 and m.r32(c) == 1 and rnd.randrange(3) == 0:
            ms2size(w, m.r32(U + 4))
        elif rnd.randrange(2):
            ms2size(w, m.r32(U + 4))
    if fam == "fallen" and brk == 9:
        c = U
    if fam == "gmummy" and brk == 9:
        c = U
    m.w32(blk + 0xC if fam != "gmummy" else blk + 0x10, u32(bound))
    if fam == "gmummy":
        m.w32(blk + 0x14, pick(rnd, 0, 1))
        m.w32(blk + 0x18, pick(rnd, 0, 1))
        for off in (0, 4, 8, 0xC):
            m.w32(blk + off, pick(rnd, 0, 0, 1, rnd.getrandbits(8)))
    else:
        for off in (0, 4, 8):
            m.w32(blk + off, pick(rnd, 0, 0, 1, rnd.getrandbits(8)))
    return m, {"U": U, "cand": c, "blk": blk}, (FNS[fam], GAME, U, [c, blk], []), [(blk, 0x1C)]


def gen_case(fam, rnd):
    if fam in ("adu", "adps", "dsq"):
        return gen_dist(fam, rnd)
    if fam in ("ovr", "ovs"):
        return gen_ov(fam, rnd)
    if fam in ("neutral", "dearl"):
        return gen_queue(fam, rnd)
    if fam == "entry":
        return gen_entry(rnd)
    if fam == "gate":
        return gen_gate(rnd)
    return gen_cb(fam, rnd)


def all_cases():
    out = []
    for fam in FAMILIES:
        rnd = random.Random("n66ne-" + fam)
        for k in range(NCASES):
            m, a, call, dumps = gen_case(fam, rnd)
            out.append((fam, k, m, a, call, dumps))
    return out


def predict(fam, m, a, flip=None):
    mm = m.copy()
    e = E(mm, flip)
    r = MODELS[fam](e, a)
    return r, mm, e.names, e.tags


def outputs(fam, r, mm, dumps):
    """The comparable outcome: ("ret", eax) or ("obs", ecx, edx, args) or ("fatal",), with the dumped bytes."""
    if r == FATAL:
        head = ("fatal",)
    elif isinstance(r, tuple):
        head = ("obs",) + tuple(r[1:3]) + tuple(u32(x) for x in r[3])
    elif r is None:
        head = ("ret",)
    else:
        head = ("ret", u32(r))
    if head[0] == "fatal":
        return head
    return head + tuple(bytes(mm.r8(lo + i) for i in range(n)) for lo, n in dumps)


def observed(fam, g, dumps):
    p = g["line"].split()
    ds = tuple(b for _, b in g["d"])
    if p[3] == "STOP":
        return ("fatal",) if int(p[4], 16) in (0x00408090,) else ("stop", p[4]), None
    if p[3] == "OBS":
        kv = dict(x.split("=") for x in p[5:])
        A = bytes.fromhex(g["a"])
        args = struct.unpack_from("<4I", A, 4)
        return ("obs", int(kv["ecx"], 16), int(kv["edx"], 16)) + args + ds, struct.unpack_from("<I", A, 0)[0]
    kv = dict(x.split("=") for x in p[3:])
    pop = int(kv["pop"])
    if fam in ("ovr", "ovs"):
        return ("ret",) + ds, pop
    return ("ret", int(kv["eax"], 16)) + ds, pop


def mem_spec(d):
    base = S.mem_spec(d).splitlines()
    out = ["# plan 0066 batch S1ne: tools/ai_s1e_emu.py's declared image, its guards, plus the guards and observes below"]
    out += [x for x in base if not x.startswith("#") and not x.startswith("guard")]
    out += ["guard %08x" % a for a in GUARDS]
    out += ["observe %08x" % a for a in OBSERVE]
    return "\n".join(out) + "\n"


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "s1ne.mem"), "w") as f:
        f.write(mem_spec(d))
    with open(os.path.join(d, "s1ne.cases"), "w") as f:
        for fam, k, m, a, call, dumps in all_cases():
            f.write("# %s %d\n" % (fam, k))
            for lo, n in a.get("scratch", []):
                f.write("s %08x %d\n" % (lo, n))
            for lo, b in m.runs():
                if S.G_DT <= lo < S.G_DT + 4:
                    continue
                f.write("w %08x %s\n" % (lo, b.hex()))
            for lo, n in dumps:
                f.write("d %08x %d\n" % (lo, n))
            fn, ecx, edx, stack, _ = call
            f.write("call %08x %08x %08x%s\n" % (fn, u32(ecx), u32(edx), "".join(" %08x" % u32(x) for x in stack)))
    print("cases written to", d)


def read_out(path):
    cases, reads, writes = [], [], []
    with open(path) as f:
        for line in f:
            p = line.split()
            if not p:
                continue
            if p[0] == "C":
                cases.append({"line": line.strip(), "d": [], "a": ""})
            elif p[0] == "A":
                cases[-1]["a"] = p[1]
            elif p[0] == "D":
                cases[-1]["d"].append((int(p[1], 16), bytes.fromhex(p[2]) if len(p) > 2 else b""))
            elif p[0] == "R":
                reads.append((int(p[1], 16), int(p[2], 16), int(p[3]), int(p[4])))
            elif p[0] == "W":
                writes.append((int(p[1], 16), int(p[2], 16), int(p[3]), int(p[4])))
    return cases, reads, writes


SITES = {"neutral": (0x005A7428, 0x005A7482), "dearl": (0x005DE186,)}


def cmd_check(d):
    cases = all_cases()
    got, reads, writes = read_out(os.path.join(d, "s1ne.out"))
    lines, ok = [], True
    if len(got) != len(cases):
        print("S1NE cases=%d outputs=%d result=FAIL" % (len(cases), len(got)))
        return 1
    per = {f: {"cases": 0, "match": 0, "bad": 0, "ctl": {}, "tags": {}, "obs": 0, "fatal": 0} for f in FAMILIES}
    for (fam, k, m, a, call, dumps), g in zip(cases, got):
        P = per[fam]
        P["cases"] += 1
        r, mm, names, tags = predict(fam, m, a)
        want = outputs(fam, r, mm, dumps)
        have, extra = observed(fam, g, dumps)
        for tg in tags:
            P["tags"][tg] = P["tags"].get(tg, 0) + 1
        good = have == want
        if have[0] == "ret" and extra != POP[fam]:
            good = False
        if have[0] == "obs":
            P["obs"] += 1
            if extra not in SITES.get(fam, ()):
                good = False
        if have[0] == "fatal":
            P["fatal"] += 1
        if good:
            P["match"] += 1
        else:
            P["bad"] += 1
            if P["bad"] <= 5:
                lines.append("BAD %s %d want=%s have=%s extra=%s" % (fam, k, _fmt(want), _fmt(have), extra))
        for nm in names:
            try:
                r2, mm2, _, _ = predict(fam, m, a, flip=nm)
                alt = outputs(fam, r2, mm2, dumps)
            except (KeyError, ValueError, IndexError, ZeroDivisionError):
                alt = None
            c = P["ctl"].setdefault(nm, [0, 0])
            if alt != want:
                c[0] += 1
                if alt == have:
                    c[1] += 1
    for fam in FAMILIES:
        P = per[fam]
        unsep = sorted(n for n, c in P["ctl"].items() if c[0] == 0)
        passed = sorted(n for n, c in P["ctl"].items() if c[1] > 0)
        lines.append("S1NE %s fn=%08x cases=%d match=%d bad=%d obs=%d fatal=%d controls=%d separated=%d passed=%d"
                     % (fam, FNS[fam], P["cases"], P["match"], P["bad"], P["obs"], P["fatal"], len(P["ctl"]),
                        len(P["ctl"]) - len(unsep), len(passed)))
        lines.append("  CTL " + " ".join("%s:%d/%d" % (n, c[0], c[1]) for n, c in sorted(P["ctl"].items())))
        lines.append("  UNSEPARATED " + (" ".join(unsep) if unsep else "-"))
        lines.append("  TAGS " + ("; ".join("%s %d" % kv for kv in sorted(P["tags"].items())) or "-"))
        if passed:
            ok = False
            lines.append("  PASSED " + " ".join(passed))
        if P["bad"]:
            ok = False
    acc, unacc = {}, []
    for pc, addr, n, cnt in reads:
        hit = [nm for lo, ln, nm in CONST_READS if lo <= addr and addr + n <= lo + ln]
        if hit:
            acc[hit[0]] = acc.get(hit[0], 0) + cnt
        else:
            unacc.append("R %08x %08x %d %d" % (pc, addr, n, cnt))
    for pc, addr, n, cnt in writes:
        unacc.append("W %08x %08x %d %d" % (pc, addr, n, cnt))
    lines.append("S1NE traced reads accounted: " + (", ".join("%s %d" % kv for kv in sorted(acc.items())) or "-"))
    lines.append("S1NE traced unaccounted: %d" % len(unacc))
    lines += ["  " + x for x in unacc[:40]]
    if unacc:
        ok = False
    lines.append("S1NE total cases=%d match=%d" % (sum(P["cases"] for P in per.values()),
                                                   sum(P["match"] for P in per.values())))
    lines.append("S1NE result=%s" % ("ok" if ok else "FAIL"))
    print("\n".join(lines))
    return 0 if ok else 1


def _fmt(t):
    return "(" + ",".join(x.hex() if isinstance(x, bytes) else ("%x" % x if isinstance(x, int) else str(x))
                          for x in t) + ")"


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
    o = ap.parse_args(argv)
    if o.cmd == "cases":
        cmd_cases(o.dir)
        return 0
    if o.cmd == "check":
        return cmd_check(o.dir)
    cmd_manifest(o.dir, o.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

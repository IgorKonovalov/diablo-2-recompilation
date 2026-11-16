#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S1ne (`lane/n66ne`), part 2: the monsters/ai walkers, MonAiUseSeqSkill, AiParamsHead and
AiParamsFind and the three RNG range functions under Ghidra's p-code emulator (ADR-0015, ADR-0021, ADR-0029) with
re/ghidra_scripts/EmuBoundary.java, compared with the models below; plus a count over the kept run:2026-11-03-ai-cat-emu-9
outputs (`catcount`). Ruling R2 of the plan 0066 inventory: a callee runs whole on the declared image or is an observed
boundary at which the case ends (ADR-0021); the case claims the map from its inputs to that call's arguments, the
memory the caller built for it (MonSetMode's command block, read from the stack dump), the unit seed and the words
dumped, and nothing after the call.

    python3 -I tools/ai_s1ne2_emu.py cases [--dir D]    write D/s1ne2.cases, D/s1ne2.mem and the zeroed table images
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s1ne2.cases D/s1ne2.mem > D/s1ne2.out
    python3 -I tools/ai_s1ne2_emu.py check [--dir D]    compare, account for every traced access, run the controls
    python3 -I tools/ai_s1ne2_emu.py catcount            the cat-emu-9 counts (kept outputs, workspace/logs/r52i/emu)
    python3 -I tools/ai_s1ne2_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66ne/s1ne/run2. Every case draw comes from random.Random("n66ne2-<family>").

The declared image is tools/ai_s1ne_emu.py's (tools/ai_s1e_emu.py's plus the DataTables +0x0D4 mask array). Image
constants read: g_BitMask32 0x006CE268 and the mode table 0x006E23D0 (16 rows of {always, never, by MonStats2}, read
by MonModeEveryFrame 0x005A6B10; objdump -s of .rdata, transcribed in MODETAB). Observed boundaries: 0x005DEB60
MonAiMove and 0x005A7C20 MonSetMode (their routes reach the pool and PathPlan's import, tools/ai_s1ne_routes.py).
Run whole: MonCmdInit 0x005A7E60 (UNIT_SetUsedSkill 0x00620210, 0x00643990, MonModeEveryFrame), PathSetStopDist
0x00649070, PathGetX/Y 0x006488C0/0x00648900, AiDistUnits, MonAiPathOverride and AiPathOverrideSet, the override clear
0x005A61F0, UNIT_HasState, RNG_RangeB, SkillFindByOwner 0x006439B0, MonAiWanderRing (to its own MonAiMove call).

Families (function; inventory rows, m = monsters-ai-machinery.md):
  wunit 0x005DEC80 MonAiWalkToUnit, runf 0x005DED00 MonAiRunToUnitFlags, run 0x005DED20 MonAiRunToUnit,
  w13 0x005DED40 MonAiWalkToUnitType13, wustop 0x005DEF80 MonAiWalkToUnitStop, runstop 0x005DEFB0 MonAiRunToUnitStop
  (to MonAiMove; m27)
  wunitz 0x005DECA0 MonAiWalkToUnitOrZero, wpt 0x005DED90 MonAiWalkToPoint, runpt 0x005DEDE0 MonAiRunToPoint,
  wptstop 0x005DEE50 MonAiWalkToPointOrStop, wptcmd 0x005DEF30 (to MonSetMode; m27)
  stepaway 0x005DEFE0 MonAiStepAway (m30), stepxy 0x005DF140 MonAiStepAwayXY (m31), t56 0x005DF7D0 (m32, m50)
  ringd 0x005DF400 MonAiWanderRingDirect, nearu 0x005DF530 MonAiWanderNearUnit, runnear 0x005DF680 MonAiRunNearUnit
  (m29, m48)
  toward 0x005DE6D0 MonAiWalkTowardUnit, movedist 0x005DE4E0 MonAiMoveToUnitDist (m33)
  seqskill 0x005DE000 MonAiUseSeqSkill (m24)
  phead 0x0058EE80 AiParamsHead, pfind 0x0058EEF0 AiParamsFind (m46)
  range 0x0045C390 RNG_Range, rangeb 0x0045C3E0 RNG_RangeB, pow2 0x00472210 RNG_RangePow2 (m9, m108)

Controls as tools/ai_s1ne_emu.py. Stdlib only.
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
import ai_s1ne_emu as N  # noqa: E402
from ai_s1e_emu import DT, GAME, MS2, MS2_SZ, MUL, E, u32, s32, s16, pick  # noqa: E402

ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66ne", "s1ne", "run2")
CAT9_DIR = os.path.join(ROOT, "workspace", "logs", "r52i", "emu")
NCASES = 120
MOVE, SETMODE = 0x005DEB60, 0x005A7C20
OBSERVE = (MOVE, SETMODE)
STK_LO, STK_LEN = 0x7FEFFE00, 0x200                 # EmuBoundary's ESP at entry is 0x7FF00000
CONST_READS = N.CONST_READS + ((0x006E23D0, 0xC0, "MonModeEveryFrame's mode table"),)
MODETAB = (0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1,    # 0x006E23D0, 48 dwords (objdump -s .rdata)
           0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1,
           0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0)
FNS = {"wunit": 0x005DEC80, "runf": 0x005DED00, "run": 0x005DED20, "w13": 0x005DED40, "wustop": 0x005DEF80,
       "runstop": 0x005DEFB0, "wunitz": 0x005DECA0, "wpt": 0x005DED90, "runpt": 0x005DEDE0, "wptstop": 0x005DEE50,
       "wptcmd": 0x005DEF30, "stepaway": 0x005DEFE0, "stepxy": 0x005DF140, "t56": 0x005DF7D0, "ringd": 0x005DF400,
       "nearu": 0x005DF530, "runnear": 0x005DF680, "toward": 0x005DE6D0, "movedist": 0x005DE4E0,
       "seqskill": 0x005DE000, "phead": 0x0058EE80, "pfind": 0x0058EEF0, "range": 0x0045C390,
       "rangeb": 0x0045C3E0, "pow2": 0x00472210}
FAMILIES = tuple(FNS)
NSTACK = {"wunit": 2, "runf": 2, "run": 1, "w13": 2, "wustop": 2, "runstop": 2, "wunitz": 1, "wpt": 2, "runpt": 2,
          "wptstop": 2, "wptcmd": 2, "stepaway": 3, "stepxy": 3, "t56": 3, "ringd": 2, "nearu": 2, "runnear": 2,
          "toward": 3, "movedist": 4, "seqskill": 4, "phead": 0, "pfind": 1, "range": 0, "rangeb": 0, "pow2": 0}
FATAL = "fatal"
REDRAWN = {}


# ---- callee maps ----

def mode_table(i):
    return MODETAB[3 * i:3 * i + 3]


def everyframe(m, U, mode):                 # 0x005A6B10 MonModeEveryFrame (ECX unit, EAX mode)
    if U == 0 or s32(mode) >= 16:
        return 0
    always, never, by2 = mode_table(mode)
    if always:
        return 1
    if never or not by2:
        return 0
    r2 = N.ms2rec(m, m.r32(U + 4))
    if r2 == 0:
        return 0
    return m.r8(r2 + 0x104 + (mode >> 3)) & (1 << (mode & 7))


def cmdinit(e, U, mode):                    # 0x005A7E60 MonCmdInit(unit, mode, cmd): the block, as a dict
    m = e.m
    lst = m.r32(U + 0xA8)                   # UNIT_SetUsedSkill(unit, 0) -> 0x00643990
    if lst:
        m.w32(lst + 0x10, 0)
    ef = everyframe(m, U, mode)
    e.tag("cmd byte 101 (every-frame mode)" if ef else "cmd byte 100")
    return {"mode": u32(mode), "unit": U, "t": 0, "x": 0, "y": 0, "b15": 0x65 if ef else 0x64}


def cmdbytes(c):
    b = bytearray(0x20)
    struct.pack_into("<IIIII", b, 0, c["mode"], c["unit"], u32(c["t"]), u32(c["x"]), u32(c["y"]))
    b[0x15] = c["b15"]
    return bytes(b)


def stopdist(e, path, n):                   # 0x00649070 PathSetStopDist(path, n)
    if path == 0:
        return
    b = n & 0xFF
    e.names.add("stop 1..19")
    ok = ((b - 1) & 0xFF) <= 0x12
    if e.flip == "stop 1..19":
        ok = not ok
    e.m.w8(path + 0x93, (b - 1) & 0xFF if ok else 0)


def ovclear(e, U):                          # 0x005A61F0: the one-shot override words cleared (ECX 0 path: address 0)
    m = e.m
    md = m.r32(U + 0x14) if U and m.r32(U) == 1 else 0
    ctl = m.r32(md + 0x2C) if md else 0
    m.w32(ctl + 0x18, 0)
    m.w32(ctl + 0x1C, 0)
    m.w8(ctl + 0x20, 0)


def mctl(m, U):                             # the inline MonPathCtl read of StepAwayXY and WalkToUnitType13
    md = m.r32(U + 0x14) if U and m.r32(U) == 1 else 0
    return m.r32(md + 0x2C) if md else 0


def rangeb(m, sp, n):                       # 0x0045C3E0, the same map as RNG_Range
    return S.rng_range(m, sp, n)


def ring_draws(e, U, r):                    # the shared draw block of the ring walkers on U's seed
    m = e.m
    sp = U + 0x20
    r8 = r & 0xFF
    odd = S.step(m, sp) & 1
    e.names.add("parity")
    if e.flip == "parity":
        odd ^= 1
    if odd:
        dx, dy = r8, rangeb(m, sp, r8)
    else:
        dx, dy = rangeb(m, sp, r8), r8
    e.tag("r 0: no RangeB step" if r8 == 0 else "r > 0")
    if S.step(m, sp) & 1:
        dx = -dx
    if S.step(m, sp) & 1:
        dy = -dy
    return dx, dy


def move(site, U, t, mode, x, y, stop, flags):
    return ("obs", site, GAME, U, [u32(t), u32(mode), u32(x), u32(y), u32(stop), u32(flags)], None)


def setmode(site, c, flag):
    return ("obs", site, GAME, None, [GAME, None, flag], c)


# ---- models ----

def m_wunit(e, a):
    return move(0x005DEC98, a["U"], a["s"][0], 2, 0, 0, 1, a["s"][1])


def m_runf(e, a):
    return move(0x005DED18, a["U"], a["s"][0], 15, 0, 0, 1, a["s"][1])


def m_run(e, a):
    return move(0x005DED36, a["U"], a["s"][0], 15, 0, 0, 1, 0)


def m_w13(e, a):
    N.ovset(e, mctl(e.m, a["U"]), 13, 0, 0)
    return move(0x005DED87, a["U"], a["s"][0], 2, 0, 0, 1, a["s"][1])


def stopword(e, n):
    if e.t("stop byte 0", n & 0xFF == 0):
        e.tag("stop byte 0 -> 1, high bytes kept" if n >> 8 else "stop 0 -> 1")
        return (n & 0xFFFFFF00) | 1
    return n


def m_wustop(e, a):
    return move(0x005DEFA2, a["U"], a["s"][0], 2, 0, 0, stopword(e, a["s"][1]), 0)


def m_runstop(e, a):
    return move(0x005DEFD2, a["U"], a["s"][0], 15, 0, 0, stopword(e, a["s"][1]), 0)


def m_wunitz(e, a):
    U, t = a["U"], a["s"][0]
    stopdist(e, e.m.r32(U + 0x2C), 1)
    c = cmdinit(e, U, 2)
    if e.t("target", t != 0):
        c["t"] = t
        return setmode(0x005DECDB, c, 1)
    return setmode(0x005DECF5, c, 1)


def pointcmd(e, a, mode, site, stop=1):
    U = a["U"]
    stopdist(e, e.m.r32(U + 0x2C), stop)
    c = cmdinit(e, U, mode)
    c["x"], c["y"] = a["s"][0], a["s"][1]
    return setmode(site, c, 1)


def m_wpt(e, a):
    return pointcmd(e, a, 2, 0x005DEDCB)


def state60(e, U):
    if e.t("state60", S.hasstate(e.m, U, 0x3C)):
        e.tag("state 60: override cleared, WL")
        ovclear(e, U)
        return 2
    return 15


def m_runpt(e, a):
    return pointcmd(e, a, state60(e, a["U"]), 0x005DEE38)


def m_wptstop(e, a):
    return pointcmd(e, a, 2, 0x005DEE8C)


def m_wptcmd(e, a):
    return pointcmd(e, a, 2, 0x005DEF6B, stop=0)


def sgn(e, name, o, u, signed):             # -1 when o > u, +1 when o < u, 0 equal
    e.names.add(name)
    if e.flip == name:
        signed = not signed
    a, b = (s32(o), s32(u)) if signed else (u32(o), u32(u))
    return -1 if a > b else 1 if a < b else 0


def m_stepaway(e, a):                       # (other, d, flag)
    m, U = e.m, a["U"]
    o, d, f = a["s"]
    if not e.t("U and other", U != 0 and o != 0):
        e.tag("null: 0")
        return 0
    (ux, uy), (ox, oy) = N.upos(m, U), N.upos(m, o)
    sx, sy = sgn(e, "sx unsigned", ox, ux, True), sgn(e, "sy unsigned", oy, uy, True)
    n = d & 0xFF
    x, y = u32(ux + n * sx), u32(uy + n * sy)
    if e.c("d>5", n, ">", 5):
        e.tag("override")
        N.m_ovr(e, {"U": U, "type": 0, "param": 0, "byte": d})
    return move(0x005DF122, U, 0, 2, x, y, 1, 4 if f else 0)


def m_stepxy(e, a):                         # (o, n, f), unsigned signs
    m, U = e.m, a["U"]
    o, d, f = a["s"]
    (ux, uy), (ox, oy) = N.upos(m, U), N.upos(m, o)
    sx, sy = sgn(e, "sx signed", ox, ux, False), sgn(e, "sy signed", oy, uy, False)
    n = d & 0xFF
    x, y = u32(ux + n * sx), u32(uy + n * sy)
    if e.c("n>5", n, ">", 5):
        e.tag("override")
        N.ovset(e, mctl(m, U), 0, 0, d)
    return move(0x005DF292, U, 0, 15, x, y, 1, 4 if f else 0)


def m_t56(e, a):                            # (target, byte, flag)
    m, U = e.m, a["U"]
    t, b, f = a["s"]
    low = S.step(m, U + 0x20)
    typ = 6 if e.c("low8>=0x80", low & 0xFF, ">=", 0x80) else 5
    e.tag("type %d" % typ)
    N.m_ovr(e, {"U": U, "type": typ, "param": 0, "byte": b})
    return move(0x005DF839, U, t, 2, 0, 0, 1, 4 if f else 0)


def ringcmd(e, U, cx, cy, r, mode_fn, site):
    dx, dy = ring_draws(e, U, r)
    mode = mode_fn()
    stopdist(e, e.m.r32(U + 0x2C), 1)
    c = cmdinit(e, U, mode)
    c["x"], c["y"] = u32(cx + dx), u32(cy + dy)
    return setmode(site, c, 1)


def m_ringd(e, a):
    U = a["U"]
    ux, uy = N.upos(e.m, U)
    return ringcmd(e, U, ux, uy, a["s"][1], lambda: 2, 0x005DF527)


def m_nearu(e, a):
    m, U = e.m, a["U"]
    o, r = a["s"]
    if not e.t("other", o != 0):            # MonAiWanderRing(2), run whole to its MonAiMove call
        e.tag("no other: Ring(2)")
        ux, uy = N.upos(m, U)
        dx, dy = ring_draws(e, U, 2)
        return move(0x005DE313, U, 0, 2, u32(ux + dx), u32(uy + dy), 1, 0)
    ox, oy = N.upos(m, o)
    return ringcmd(e, U, ox, oy, r, lambda: 2, 0x005DF66D)


def m_runnear(e, a):
    U = a["U"]
    o, r = a["s"]
    ox, oy = N.upos(e.m, o)
    return ringcmd(e, U, ox, oy, r, lambda: state60(e, U), 0x005DF7C6)


def movedist(e, U, t, mode, mx, ring, site):
    m = e.m
    D = s32(N.m_adu(E(m), {"A": U, "B": t}))
    dirn = -1 if e.c("D<ring", D, "<", s32(ring)) else 1
    n = N.iabs(u32(D - ring))
    if e.c("n>max", n, ">", s32(mx)):
        n = s32(mx)
    (tx, ty), (ux, uy) = N.upos(m, t), N.upos(m, U)
    dx, dy = N.iabs(u32(tx - ux)), N.iabs(u32(ty - uy))
    s = s32(u32(dx + dy))
    if e.c("s<n", s, "<", n):
        s = n
    ix = iy = 0
    if e.c("s>0", s, ">", 0):
        ix = S.tdiv(s32(u32(dx * n)), s)
        iy = S.tdiv(s32(u32(dy * n)), s)
        k = 0
        while e.c("ix+iy<n", s32(u32(ix + iy)), "<", n):
            ix, iy = s32(u32(ix + 1)), s32(u32(iy + 1))
            k += 1
            if k > 100000:
                raise ValueError("loop bound")
        e.tag("rounded up %s" % ("0" if k == 0 else "1" if k == 1 else "2+"))
    else:
        e.tag("s 0")
    gx = sgn(e, "gx unsigned", ux, tx, True)        # +1 when tx > ux
    gy = sgn(e, "gy unsigned", uy, ty, True)
    e.tag("toward" if dirn > 0 else "away")
    c = cmdinit(e, U, mode)
    stopdist(e, m.r32(U + 0x2C), 1)
    c["x"] = u32(gx * ix * dirn + ux)
    c["y"] = u32(gy * iy * dirn + uy)
    return setmode(site, c, 1)


def m_toward(e, a):
    t, mx, ring = a["s"]
    return movedist(e, a["U"], t, 2, mx, ring, 0x005DE6BB)


def m_movedist(e, a):
    t, mode, mx, ring = a["s"]
    if s32(mode) >= 16:
        N.m_adu(E(e.m), {"A": a["U"], "B": t})
        return FATAL
    return movedist(e, a["U"], t, mode, mx, ring, 0x005DE6BB)


def findbyowner(m, U, skill):               # 0x006439B0 SkillFindByOwner(unit, skill, -1)
    lst = m.r32(U + 0xA8)
    node = m.r32(lst + 4) if lst else 0
    while node:
        if s16(m.r16(m.r32(node))) == s32(skill) and m.r32(node + 0x34) == 0xFFFFFFFF:
            return node
        node = m.r32(node + 4)
    return 0


def m_seqskill(e, a):                       # (skill, target, x, y)
    m, U = e.m, a["U"]
    sk, t, x, y = a["s"]
    if not e.t("skill>=0", s32(sk) >= 0) or e.c("skill>=count", s32(sk), ">=", s32(m.r32(DT + 0xBA0))):
        e.tag("skill outside 0..count-1: 0")
        return 0
    c = cmdinit(e, U, 14)
    node = findbyowner(m, U, sk)
    e.tag("skill node found" if node else "no skill node")
    lst = m.r32(U + 0xA8)
    if lst:
        m.w32(lst + 0x10, node)
    stopdist(e, m.r32(U + 0x2C), 1)
    c["t"], c["x"], c["y"] = t, x, y
    return setmode(0x005DE068, c, 0)


def aictl(m, U):
    md = m.r32(U + 0x14) if U and m.r32(U) == 1 else 0
    return m.r32(md + 0x28) if md else 0


def m_phead(e, a):
    ctl = aictl(e.m, a["U"])
    e.tag("control" if ctl else "no control: 0")
    return e.m.r32(ctl + 0x20) if ctl else 0


def m_pfind(e, a):                          # AiParamsFind(unit, kind; makeHead)
    m = e.m
    kind, mk = a["kind"], a["s"][0]
    ctl = aictl(m, a["U"])
    if ctl == 0:
        return 0
    head = m.r32(ctl + 0x20)
    if head == 0:
        e.tag("empty list")
        return 0
    order, r = [], m.r32(head)              # from the head's next round to the head itself, last
    while True:
        order.append(r)
        if r == head or len(order) > 64:
            break
        r = m.r32(r)
    e.names.add("head first")
    if e.flip == "head first":
        order = [head] + order[:-1]
    hit = [x for x in order if m.r32(x + 8) == kind]
    if not hit:
        e.tag("not found")
        return 0
    r = hit[0]
    if len(hit) > 1 and hit[0] != head and head in hit:
        e.tag("kind also at the head, another taken first")
    e.tag("found the head" if r == head else "found another")
    if e.t("makeHead", mk != 0):
        m.w32(ctl + 0x20, r)
    return r


def m_range(e, a):
    m = e.m
    n = a["n"]
    if m.r32(a["sp"]) == 0 and m.r32(a["sp"] + 4) == 1234567 and n == 100:
        e.tag("worked example: new low 1 234 567, n 100")
    if not e.c("n>0", s32(n), ">", 0):
        e.tag("n < 1: 0, no step")
        return 0
    low = S.step(m, a["sp"])
    p2 = e.t("pow2", n & (n - 1) == 0)
    e.tag("power of two" if n & (n - 1) == 0 else "other n")
    return low & (n - 1) if p2 else low % n


def m_pow2(e, a):
    low = S.step(e.m, a["sp"])
    return low & u32(a["n"] - 1)


MODELS = {"wunit": m_wunit, "runf": m_runf, "run": m_run, "w13": m_w13, "wustop": m_wustop, "runstop": m_runstop,
          "wunitz": m_wunitz, "wpt": m_wpt, "runpt": m_runpt, "wptstop": m_wptstop, "wptcmd": m_wptcmd,
          "stepaway": m_stepaway, "stepxy": m_stepxy, "t56": m_t56, "ringd": m_ringd, "nearu": m_nearu,
          "runnear": m_runnear, "toward": m_toward, "movedist": m_movedist, "seqskill": m_seqskill,
          "phead": m_phead, "pfind": m_pfind, "range": m_range, "rangeb": m_range, "pow2": m_pow2}


# ---- the case writer ----

def coord(rnd, typ):
    if typ in (2, 4, 5):
        return pick(rnd, rnd.randrange(0x10000), rnd.randrange(0x10000), 0, 0x7FFFFFFF, 0x80000000,
                    0xFFFFFFFF, rnd.getrandbits(32))
    return pick(rnd, rnd.randrange(0x10000), rnd.randrange(0x10000), rnd.randrange(0x10000), 0, 0xFFFF, 1, 0xFFFE)


def actor(w, fam, rnd):
    """The acting unit: mostly a monster with MonsterData, its path control at +0x2C and a skill list; now and then
    another type or none of those (the ECX 0 and null paths)."""
    m = w.m
    typ = 1 if fam in ("seqskill",) else pick(rnd, 1, 1, 1, 1, 1, 1, 0, 2)
    md = typ == 1 and (fam in ("phead", "pfind") or rnd.randrange(8) != 0)
    st = (0x3C,) if fam in ("runpt", "runnear") and rnd.randrange(2) else ()
    U = w.unit(typ=typ, md=md, states=st)
    if typ == 2:
        d = m.alloc(0x10)
        r = m.alloc(0x100)
        m.w32(U + 0x14, d)
        m.w32(d, r)
        m.w32(r + 0xD0, pick(rnd, 0, 1, 2, rnd.getrandbits(8)))
    N.place(w, U, typ, coord(rnd, typ), coord(rnd, typ))
    ctl = 0
    if md:
        ctl = m.alloc(0x40)
        m.w32(m.r32(U + 0x14) + 0x2C, ctl)
        for off in (0x18, 0x1C):
            m.w32(ctl + off, pick(rnd, 0, rnd.getrandbits(32)))
        m.w8(ctl + 0x20, pick(rnd, 0, rnd.getrandbits(8)))
    cls = m.r32(U + 4)
    rec = S.ms_rec(m, cls)
    if rec:
        m.w16(rec + 0x18, pick(rnd, 0, 1, 5, rnd.randrange(0x10), -1, 0x200))
        r2 = N.ms2rec(m, cls)
        if r2:
            m.w16(r2 + 0x104, rnd.getrandbits(16))
    if rnd.randrange(3):                    # a skill list (UNIT_SetUsedSkill's +0x10, SkillFindByOwner's nodes)
        lst = m.alloc(0x20)
        m.w32(U + 0xA8, lst)
        m.w32(lst + 0x10, rnd.getrandbits(32))
        prev = lst + 4
        for _ in range(rnd.randrange(4)):
            node = m.alloc(0x40)
            srec = m.alloc(0x10)
            m.w16(srec, pick(rnd, 0, 1, 5, 0x40, rnd.randrange(0x180), 0xFFFF))
            m.w32(node, srec)
            m.w32(node + 0x34, pick(rnd, 0xFFFFFFFF, 0xFFFFFFFF, 0, 1))
            m.w32(prev, node)
            prev = node + 4
    if m.r32(U + 0x2C) and rnd.randrange(2):
        m.w8(m.r32(U + 0x2C) + 0x93, rnd.getrandbits(8))
    return U, ctl


def other(w, rnd, U, near=False):
    m = w.m
    typ = pick(rnd, 1, 1, 0, 0, 2, 4, 5, 3)
    o = N.mk(w, typ)
    if m.r32(o + 0x2C):
        ux, uy = N.upos(m, U)
        if near and typ not in (2, 4, 5) and rnd.randrange(3):
            N.place(w, o, typ, (ux + pick(rnd, 0, 1, -1, 2, -5, rnd.randrange(-40, 40))) & 0xFFFF,
                    (uy + pick(rnd, 0, 1, -1, 3, -7, rnd.randrange(-40, 40))) & 0xFFFF)
        elif rnd.randrange(3) == 0:
            N.place(w, o, typ, ux, coord(rnd, typ))
        elif typ in (2, 4, 5) or rnd.randrange(4) == 0:
            N.place(w, o, typ, coord(rnd, typ), coord(rnd, typ))
    if typ == 1:
        N.ms2size(w, m.r32(o + 4))
    return o


def plist(w, rnd, ctl):
    m = w.m
    n = pick(rnd, 0, 1, 1, 2, 3, 4, 6)
    recs = [m.alloc(0x1C) for _ in range(n)]
    for i, r in enumerate(recs):
        m.w32(r, recs[(i + 1) % n])
        m.w32(r + 4, recs[(i - 1) % n])
        m.w32(r + 8, pick(rnd, 1, 2, 3, 14, 1, 2, rnd.getrandbits(32)))
        for off in (0x0C, 0x10, 0x14, 0x18):
            m.w32(r + off, rnd.getrandbits(32))
    m.w32(ctl + 0x20, recs[rnd.randrange(n)] if n else 0)
    return recs


def gen_case(fam, rnd):
    w, m = N.world(rnd)
    if fam in ("range", "rangeb", "pow2"):
        sp = m.alloc(8)
        m.w32(sp, rnd.getrandbits(32))
        m.w32(sp + 4, rnd.getrandbits(32))
        n = pick(rnd, 0, 1, 2, 3, 100, 128, 255, 256, 7, rnd.randrange(1, 1000), 1 << rnd.randrange(31),
                 0x80000000, 0xFFFFFFFF, rnd.getrandbits(32), rnd.getrandbits(16))
        if fam == "pow2":
            n = pick(rnd, 1, 2, 4, 8, 16, 32, 128, 256, 1 << rnd.randrange(32), 0, 3, 100, rnd.getrandbits(32))
        if rnd.randrange(10) == 0:          # the machinery worked example: a step whose new low word is 1 234 567
            m.w32(sp, 0)
            m.w32(sp + 4, 1234567)
            n = 100
        return m, {"sp": sp, "n": n, "s": []}, (FNS[fam], sp, n, []), [(sp, 8)]
    U, ctl = actor(w, fam, rnd)
    if fam == "t56" and rnd.randrange(4) == 0:     # a step whose new low byte is 0x7F, 0x80 or 0x81
        lo = m.r32(U + 0x20)
        m.w32(U + 0x24, u32(((rnd.getrandbits(24) << 8) | pick(rnd, 0x7F, 0x80, 0x80, 0x81)) - lo * MUL))
    dumps = [(U + 0x20, 8)]
    if m.r32(U + 0x2C):
        dumps.append((m.r32(U + 0x2C) + 0x90, 4))
    if m.r32(U + 0xA8):
        dumps.append((m.r32(U + 0xA8) + 0x10, 4))
    scratch = []
    if ctl:
        dumps.append((ctl + 0x18, 9))
    elif fam in ("w13", "stepaway", "stepxy", "t56", "runpt", "runnear"):
        scratch = [(0, 0x40)]               # the stores through ECX 0 land at 0x18.. (case memory)
        for i in range(0, 0x40, 4):
            m.w32(i, 0)
        dumps.append((0x18, 9))
    if fam in ("phead", "pfind"):
        actl = m.r32(m.r32(U + 0x14) + 0x28) if m.r32(U) == 1 and m.r32(U + 0x14) else 0
        if actl == 0:
            return m, {"U": U, "kind": 0, "s": [0], "scratch": scratch}, (FNS[fam], U, 0, [0] if fam == "pfind" else []), dumps
        recs = plist(w, rnd, actl)
        dumps.append((actl + 0x20, 4))
        kinds = [m.r32(r + 8) for r in recs]
        kind = pick(rnd, *(kinds or [1])) if rnd.randrange(4) else pick(rnd, 1, 2, 7, 14)
        mkh = pick(rnd, 0, 1, 2)
        if fam == "phead":
            return m, {"U": U, "s": [], "scratch": scratch}, (FNS[fam], U, 0, []), dumps
        return m, {"U": U, "kind": kind, "s": [mkh], "scratch": scratch}, (FNS[fam], U, kind, [mkh]), dumps
    o = 0
    if fam in ("wunit", "runf", "run", "w13", "wustop", "runstop", "wunitz", "seqskill", "t56"):
        o = pick(rnd, rnd.getrandbits(32) | 0x10, 0x14000000, 0) if fam != "wunitz" else pick(rnd, 0, 0x14000100, rnd.getrandbits(32))
    if fam in ("stepaway", "stepxy", "nearu", "runnear", "toward", "movedist"):
        o = other(w, rnd, U, near=fam in ("stepaway", "stepxy", "toward", "movedist"))
        if fam in ("stepaway", "nearu") and rnd.randrange(8) == 0:
            o = 0
        if fam == "stepaway" and rnd.randrange(12) == 0:
            o, U = U, 0
    if fam == "stepaway" and U == 0:
        return m, {"U": 0, "s": [o, 5, 1], "scratch": scratch}, (FNS[fam], GAME, 0, [o, 5, 1]), []
    flags = pick(rnd, 0, 1, 2, 4, 7, rnd.getrandbits(32))
    byte = pick(rnd, 0, 1, 5, 6, 19, 77, 78, 0xFF, rnd.getrandbits(8), rnd.getrandbits(32))
    if fam in ("wunit", "runf", "w13"):
        s = [o, flags]
    elif fam == "run":
        s = [o]
    elif fam in ("wustop", "runstop"):
        s = [o, pick(rnd, 0, 1, 2, 19, 20, 0xFF, 0x100, 0x1200, rnd.getrandbits(32))]
    elif fam == "wunitz":
        s = [o]
    elif fam in ("wpt", "runpt", "wptstop", "wptcmd"):
        s = [coord(rnd, 1), coord(rnd, 2)]
    elif fam in ("stepaway", "stepxy"):
        s = [o, byte, pick(rnd, 0, 1, 2, 0x100, rnd.getrandbits(32))]
    elif fam == "t56":
        s = [o, byte, pick(rnd, 0, 1, rnd.getrandbits(32))]
    elif fam in ("ringd",):
        s = [rnd.getrandbits(32), pick(rnd, 0, 1, 2, 4, 19, 0xFF, 0x104, rnd.getrandbits(32))]
    elif fam in ("nearu", "runnear"):
        s = [o, pick(rnd, 0, 1, 2, 4, 6, 19, 0xFF, 0x113, rnd.getrandbits(32))]
    elif fam == "toward":
        s = [o, pick(rnd, 0, 1, 3, 5, 10, 40, -1, rnd.randrange(100), 0x7FFFFFFF),
             pick(rnd, 0, 1, 2, 3, 5, 10, 20, -3, rnd.randrange(40))]
    elif fam == "movedist":
        s = [o, pick(rnd, 2, 15, 1, 0, 4, 13, rnd.randrange(16), rnd.randrange(16), 16),
             pick(rnd, 0, 1, 3, 5, 10, 40, -1, rnd.randrange(100), 0x7FFFFFFF),
             pick(rnd, 0, 1, 2, 3, 5, 10, 20, -3, rnd.randrange(40))]
    elif fam == "seqskill":
        cnt = s32(m.r32(DT + 0xBA0))
        s = [pick(rnd, 0, 1, 5, 0x40, cnt - 1, cnt, cnt + 1, -1, 0x80000000, rnd.randrange(0x180), rnd.getrandbits(32)),
             o, coord(rnd, 1), coord(rnd, 2)]
        lst = m.r32(U + 0xA8)
        if lst and rnd.randrange(2) and m.r32(lst + 4) and 0 <= s32(s[0]) < 0x8000:
            m.w16(m.r32(m.r32(lst + 4)), s[0])       # the first node carries the asked skill
    s = [u32(x) for x in s]
    if fam in ("toward", "movedist"):         # a wrapped product can make the round-up loop run for ~2^31 steps:
        try:                                # such a case is drawn again (counted in the check's header)
            predict(fam, m, {"U": U, "s": s})
        except ValueError:
            REDRAWN[fam] = REDRAWN.get(fam, 0) + 1
            return gen_case(fam, rnd)
    dumps.append((STK_LO, STK_LEN))
    return m, {"U": U, "s": s, "scratch": scratch}, (FNS[fam], GAME, U, s), dumps


def all_cases():
    out = []
    for fam in FAMILIES:
        rnd = random.Random("n66ne2-" + fam)
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
    """("fatal",) | ("ret", eax, dumps…) | ("obs", site, ecx, edx, args…, cmd bytes or None, dumps…)."""
    if r == FATAL:
        return ("fatal",)
    ds = tuple(bytes(mm.r8(lo + i) for i in range(n)) for lo, n in dumps if lo != STK_LO)
    if isinstance(r, tuple):
        _, site, ecx, edx, args, c = r
        if c is not None:
            return ("obs", site, args[0], args[2], cmdbytes(c)) + ds
        return ("obs", site, ecx, edx) + tuple(args) + ds
    return ("ret", u32(r)) + ds


def observed(fam, g, dumps):
    p = g["line"].split()
    stk = None
    ds = []
    for (lo, n), (_, b) in zip(dumps, g["d"]):
        if lo == STK_LO:
            stk = b
        else:
            ds.append(b)
    ds = tuple(ds)
    if p[3] == "STOP":
        return ("fatal",) if int(p[4], 16) == 0x00408090 else ("stop", p[4]), None
    if p[3] == "OBS":
        kv = dict(x.split("=") for x in p[5:])
        A = bytes.fromhex(g["a"])
        site = struct.unpack_from("<I", A, 0)[0]
        if int(p[4], 16) == SETMODE:
            g_, cmd, flag = struct.unpack_from("<3I", A, 4)
            off = cmd - STK_LO
            cb = stk[off:off + 0x20] if stk is not None and 0 <= off <= STK_LEN - 0x20 else b"?"
            return ("obs", site, g_, flag, cb) + ds, None
        args = struct.unpack_from("<6I", A, 4)
        return ("obs", site, int(kv["ecx"], 16), int(kv["edx"], 16)) + args + ds, None
    kv = dict(x.split("=") for x in p[3:])
    return ("ret", int(kv["eax"], 16)) + ds, int(kv["pop"])


def mem_spec(d):
    base = N.mem_spec(d).splitlines()
    out = ["# plan 0066 batch S1ne part 2: tools/ai_s1ne_emu.py's declared image and guards, the observes below"]
    out += [x for x in base if not x.startswith("#") and not x.startswith("observe")]
    out += ["observe %08x" % a for a in OBSERVE]
    return "\n".join(out) + "\n"


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "s1ne2.mem"), "w") as f:
        f.write(mem_spec(d))
    with open(os.path.join(d, "s1ne2.cases"), "w") as f:
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
            fn, ecx, edx, stack = call
            f.write("call %08x %08x %08x%s\n" % (fn, u32(ecx), u32(edx), "".join(" %08x" % u32(x) for x in stack)))
    print("cases written to", d)


def cmd_check(d):
    cases = all_cases()
    got, reads, writes = N.read_out(os.path.join(d, "s1ne2.out"))
    lines, ok = [], True
    if len(got) != len(cases):
        print("S1NE2 cases=%d outputs=%d result=FAIL" % (len(cases), len(got)))
        return 1
    per = {f: {"cases": 0, "match": 0, "bad": 0, "ctl": {}, "tags": {}, "obs": 0, "fatal": 0} for f in FAMILIES}
    for (fam, k, m, a, call, dumps), g in zip(cases, got):
        P = per[fam]
        P["cases"] += 1
        r, mm, names, tags = predict(fam, m, a)
        want = outputs(fam, r, mm, dumps)
        have, pop = observed(fam, g, dumps)
        for tg in tags:
            P["tags"][tg] = P["tags"].get(tg, 0) + 1
        good = have == want
        if have[0] == "ret" and pop != 4 * NSTACK[fam]:
            good = False
        P["obs"] += have[0] == "obs"
        P["fatal"] += have[0] == "fatal"
        if good:
            P["match"] += 1
        else:
            P["bad"] += 1
            if P["bad"] <= 5:
                lines.append("BAD %s %d want=%s have=%s pop=%s" % (fam, k, N._fmt(want), N._fmt(have), pop))
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
        lines.append("S1NE2 %s fn=%08x cases=%d match=%d bad=%d obs=%d fatal=%d controls=%d separated=%d passed=%d"
                     % (fam, FNS[fam], P["cases"], P["match"], P["bad"], P["obs"], P["fatal"], len(P["ctl"]),
                        len(P["ctl"]) - len(unsep), len(passed)))
        lines.append("  CTL " + (" ".join("%s:%d/%d" % (n, c[0], c[1]) for n, c in sorted(P["ctl"].items())) or "-"))
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
    lines.append("S1NE2 traced reads accounted: " + (", ".join("%s %d" % kv for kv in sorted(acc.items())) or "-"))
    lines.append("S1NE2 traced unaccounted: %d" % len(unacc))
    lines += ["  " + x for x in unacc[:40]]
    if unacc:
        ok = False
    lines.append("S1NE2 redrawn (round-up loop past 100 000 steps): " + (", ".join("%s %d" % kv for kv in sorted(REDRAWN.items())) or "-"))
    lines.append("S1NE2 total cases=%d match=%d" % (sum(P["cases"] for P in per.values()),
                                                    sum(P["match"] for P in per.values())))
    lines.append("S1NE2 result=%s" % ("ok" if ok else "FAIL"))
    print("\n".join(lines))
    return 0 if ok else 1


def cmd_catcount():
    """Over the kept run:2026-11-03-ai-cat-emu-9 outputs (tools/ai_cat_emu9.py's cases regenerated, its .out files
    read): (1) the cases whose prediction changes when every inline draw-against-aip compare is taken unsigned, and how
    many of those still match the emulator (must be 0); (2) the same for the draw taken as a signed remainder of the
    low word; (3) row 125's cases that reach UseSkill with a negative i16 Skill1, and their mode argument."""
    import ai_cat_emu9 as C
    base_cmp = C.Env._cmp
    base_draw = C.Env.draw
    mode = {"v": None}

    def cmp2(self, d, c, edge):
        if mode["v"] == "unsigned":
            return u32(d) < u32(c)
        return base_cmp(self, d, c, edge)

    def draw2(self):
        if mode["v"] == "sdraw":
            C.step(self.seed)
            v = s32(self.seed[0])
            return int(abs(v) % 100) * (1 if v >= 0 else -1)
        return base_draw(self)

    C.Env._cmp = cmp2
    C.Env.draw = draw2
    out = []
    tot = {"unsigned": [0, 0], "sdraw": [0, 0]}
    for fam in C.FAMILIES:
        _, meta, _ = C.gen_family(fam, random.Random("r52i-" + fam))
        calls, _ = C.read_out(os.path.join(CAT9_DIR, fam + ".out"))
        sep = {"unsigned": [0, 0], "sdraw": [0, 0]}
        neg = [0, 0, 0]
        for c, inp in zip(calls, meta):
            if "stop" in c:
                continue
            mode["v"] = None
            want = C.run_model(inp)
            ok = C.matches(c, want)
            for v in sep:
                mode["v"] = v
                alt = C.run_model(inp)
                mode["v"] = None
                if alt != want:
                    sep[v][0] += 1
                    sep[v][1] += C.matches(c, alt)
            if fam == "blood" and want[0] == C.USESKILL and s16(inp["skill"][0]) < 0:
                neg[0] += 1
                neg[1] += ok
                neg[2] += want[4][0] == 5
        for v in sep:
            tot[v][0] += sep[v][0]
            tot[v][1] += sep[v][1]
        out.append("CAT9 %s unsigned_cmp_separating=%d passed=%d signed_draw_separating=%d passed=%d" % (
            fam, sep["unsigned"][0], sep["unsigned"][1], sep["sdraw"][0], sep["sdraw"][1]))
        if fam == "blood":
            out.append("CAT9 blood useskill_with_negative_skill1=%d matched=%d mode5=%d" % tuple(neg))
    out.append("CAT9 total unsigned_cmp_separating=%d passed=%d signed_draw_separating=%d passed=%d" % (
        tot["unsigned"][0], tot["unsigned"][1], tot["sdraw"][0], tot["sdraw"][1]))
    C.Env._cmp, C.Env.draw = base_cmp, base_draw
    print("\n".join(out))
    return 0 if tot["unsigned"][1] == 0 and tot["sdraw"][1] == 0 else 1


def bloodx_cases():
    """Row 125 (AiBloodLord 0x005E36F0) cases on tools/ai_cat_emu9.py's image: its case writer, then per case the
    seed, the melee word, the aip block and Skill1 rewritten in both the inputs and the lines. Cases 0..7: the machinery
    worked example (new low word 1 234 567, aip1 50, melee); the rest: melee with aip1 and aip3 at 100 (both chances
    taken), Skill1 a negative i16 in most, so that the UseSkill call carries it."""
    import ai_cat_emu9 as C
    rnd = random.Random("n66ne2-bloodx")
    cases, meta, mem = C.gen_family("blood", random.Random("n66ne2-bloodx-base"))
    out = []
    for k, (lines, inp) in enumerate(zip(cases, meta)):
        if k >= 60:
            break
        d = inp["diff"]
        if k < 8:
            inp["seed"] = (0, 1234567) if k < 4 else (rnd.randrange(1 << 32), rnd.randrange(1 << 32))
            inp["aip"][0][d] = 50
        else:
            inp["seed"] = (rnd.randrange(1 << 32), rnd.randrange(1 << 32))
            inp["aip"][0][d] = 100
            inp["aip"][2][d] = 100
            inp["skill"][0] = pick(rnd, 0xFFFF, 0x8000, 0xFFFE, 0xFF00, 0x8001, 0xFFFF, rnd.randrange(0x8000, 0x10000),
                                   rnd.randrange(0, 400))
        inp["melee"] = 1
        i = next(j for j, x in enumerate(lines) if x.startswith("w %08x " % (C.UNIT + 0x20)))
        lines[i] = "w %08x %s%s" % (C.UNIT + 0x20, C.hx32(inp["seed"][0]), C.hx32(inp["seed"][1]))
        i = next(j for j, x in enumerate(lines) if x.startswith("w %08x " % C.CTX))
        w = bytearray(bytes.fromhex(lines[i].split()[2]))
        struct.pack_into("<I", w, 0x18, 1)
        lines[i] = "w %08x %s" % (C.CTX, w.hex())
        mrec = C.MSBASE + 0x1A8 * inp["cls"]
        i = lines.index(next(x for x in lines if x.startswith("w %08x " % (mrec + 0x56))))
        lines[i] = "w %08x %s" % (mrec + 0x56, "".join(C.hx16(inp["aip"][j][dd]) for j in range(8) for dd in range(3)))
        i = lines.index(next(x for x in lines if x.startswith("w %08x " % (mrec + 0x170))))
        lines[i] = "w %08x %s" % (mrec + 0x170, "".join(C.hx16(v) for v in inp["skill"]))
        out.append((lines, inp))
    return out, mem


def cmd_bloodx_cases(d):
    cs, mem = bloodx_cases()
    with open(os.path.join(d, "bloodx.cases"), "w") as f:
        for lines, _ in cs:
            f.write("\n".join(lines) + "\n")
    with open(os.path.join(d, "bloodx.mem"), "w") as f:
        f.write("\n".join(mem) + "\n")
    print("CASES bloodx %d" % len(cs))


def cmd_bloodx_check(d):
    import ai_cat_emu9 as C
    cs, _ = bloodx_cases()
    calls, traced = C.read_out(os.path.join(d, "bloodx.out"))
    lines, ok = [], len(calls) == len(cs)
    match = ex = neg = neg5 = 0
    ctl = {n: [0, 0] for n in C.CONTROLS}
    for k, (c, (_, inp)) in enumerate(zip(calls, cs)):
        want = C.run_model(inp)
        good = "stop" not in c and C.matches(c, want)
        match += good
        if not good:
            ok = False
            lines.append("BAD bloodx %d want=%s@%x" % (k, want[0], want[1]))
        if k < 4:
            ex += good and want[0] == C.IDLE and want[1] == 0x005E37CF and want[5] == [1234567, 0]
        if want[0] == C.USESKILL and s16(inp["skill"][0]) < 0:
            neg += good
            neg5 += good and want[4][0] == 5 and want[4][1] == u32(s16(inp["skill"][0]))
        for n in ctl:
            nw = C.run_model(inp, neg=n)
            if nw != want:
                ctl[n][0] += 1
                ctl[n][1] += C.matches(c, nw)
    if any(v[1] for v in ctl.values()):
        ok = False
    lines.append("BLOODX cases=%d match=%d worked_example_idle_after_one_step=%d useskill_negative_skill1=%d "
                 "mode5_skill_sign_extended=%d traced=%d" % (len(cs), match, ex, neg, neg5, len(traced)))
    lines.append("  CTL " + " ".join("%s:%d/%d" % (n, v[0], v[1]) for n, v in sorted(ctl.items())))
    lines.append("BLOODX result=%s" % ("ok" if ok and not traced else "FAIL"))
    print("\n".join(lines))
    return 0 if ok else 1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("cases", "check", "catcount", "bloodx-cases", "bloodx-check", "manifest"))
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    o = ap.parse_args(argv)
    if o.cmd == "cases":
        cmd_cases(o.dir)
        return 0
    if o.cmd == "check":
        return cmd_check(o.dir)
    if o.cmd == "catcount":
        return cmd_catcount()
    if o.cmd == "bloodx-cases":
        cmd_bloodx_cases(o.dir)
        return 0
    if o.cmd == "bloodx-check":
        return cmd_bloodx_check(o.dir)
    N.cmd_manifest(o.dir, o.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

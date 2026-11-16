#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S2ae (`lane/n66sa`), part 1: skills and missile leaf functions under Ghidra's p-code
emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java, compared with the models below.

    python3 -I tools/skills_s2ae_emu.py cases [--dir D] [--limit N]   write D/s2ae.cases, D/s2ae.mem and the tables
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s2ae.cases D/s2ae.mem > D/s2ae.out
    python3 -I tools/skills_s2ae_emu.py check [--dir D] [--limit N]   compare, account for traced reads, controls
    python3 -I tools/skills_s2ae_emu.py static                        objdump reads the record cites
    python3 -I tools/skills_s2ae_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66sa/s2ae/run. Every draw comes from random.Random("n66sa-s2ae-<family>"); the declared
Skills records from random.Random("n66sa-s2ae-skills"). The unit, stat-list and state builders are batch S5e part 1's
(tools/combat_s5e_emu.py, unchanged; its seeded MonStats and zero ItemStatCost tables are written under its names).

Every callee runs whole on the declared image (ruling R2: no declared return) unless named as an observed boundary
(ADR-0021): the case ends at that call and its claim ends there. The allocator entries and the fatal path are guards.

Families (function, registers; inventory rows, d = skills/dispatch, m = skills/missiles):
  pvs   0x006502D0 sub_006502D0_PathVelocityStep (EAX path, ECX multiplier), whole.                m35
  pdir  0x0064FC60 sub_0064FC60_PathDirection (ECX vector out, EDX index out; x1, y1, x2, y2), whole; reads
        g_PathDirTable 0x006EB7E0 (.rdata).                                                       m38, m98
  elem  0x005A8910 sub_005A8910_MissileElemRoll (EAX max stat; unit, min stat, mastery stat), whole, with
        STATS_GetUnitStat, sub_00483360_MulDiv, RNG_RangeB.                                          m60-62, m65, m66
  smana 0x006440F0 SKILLS_StartManaOk (ESI unit, EDI entry), whole, with UNIT_HasState.             d39
  rst   0x00644060 SKILLS_RestrictOk (EAX entry, EBX unit), whole, with 0x0063A510 / 0x0063A130 (the restricted
        state mask at DataTables +0x110) and UNIT_HasState.                                        d38
  dly   0x006478F0 SKILLS_DelayOk (EDI unit; entry); observed boundary SKILLS_GetSkillLevel 0x006442A0 from
        0x00647936.                                                                                d69 (the gate)
  kick  0x00644C20 sub_00644C20_SkillKickDamage (ESI unit; flag), whole.                            d91
  skel  0x005C4430 sub_005C4430_SummonClassRoll (ECX caster, EDX summon; id, lvl), whole through
        sub_005C4300_SkeletonParam1Roll, 0x005C43D0 and sub_005C4180_SummonSetDataBytes (the 9-byte rows at
        0x00741940, .data, image bytes); observed boundary 0x005B0D70 from 0x005C42CE (the class-364 path's
        last call). The caster's state 97 is off in every case.                                     d149

Controls as S5e: every named test reversed alone, every ordered compare's strictness switched alone; `sep` counts the
cases a control changes, `passed` those the emulator still matches (must be 0); `spec_*` controls are the spec's own
readings where they differ from the code. Stdlib only, plus objdump for `static`.
"""
import argparse
import hashlib
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
import sweep_s4b as W  # noqa: E402
from combat_s5e_emu import (E, u32, s32, le32, put_unit, stat, has_state, lcg, muldiv, ATT, DEF, GAME,  # noqa: E402
                            FATAL, ALLOC, G_DT, DT, MS, MS_N, ISC, ISC_N, ISC_SZ, NSTATES, BITMASK)

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66sa", "s2ae", "run")
FNS = {"pvs": 0x006502D0, "pdir": 0x0064FC60, "elem": 0x005A8910, "smana": 0x006440F0, "rst": 0x00644060,
       "dly": 0x006478F0, "kick": 0x00644C20, "skel": 0x005C4430}
FAMILIES = ("pvs", "pdir", "elem", "smana", "rst", "dly", "kick", "skel")
NCASES = {"pvs": 1500, "pdir": 3000, "elem": 2500, "smana": 1200, "rst": 2000, "dly": 1200, "kick": 1200,
          "skel": 1500}
POP = {"pvs": 0, "pdir": 16, "elem": 12, "smana": 0, "rst": 0, "dly": 4, "kick": 4, "skel": 8}
OBS_LVL, OBS_5B0D70 = 0x006442A0, 0x005B0D70
SITE = {("dly", OBS_LVL): 0x00647936, ("skel", OBS_5B0D70): 0x005C42CE}
p1.FNS.update(FNS)

PATH = 0x20003000
VOUT, IOUT = 0x20004500, 0x20004540
ENTRY, REC = 0x20004000, 0x20005000
MASKS = 0x21400000
SK, SK_N, SK_SZ = 0x21300000, 32, 0x23C
PDT = 0x006EB7E0                     # g_PathDirTable: 128 rows of 3 dwords
SDB = 0x00741940                     # SummonSetDataBytes' rows: 11 rows of 9 bytes (index clamped at 10)
NWORDS = (NSTATES + 31) // 32


def img_bytes(va, n):
    out = bytearray()
    for k in range(n):
        off = W.va_off(va + k)
        out.append(0 if off is None else W.image()[0][off])
    return bytes(out)


SKREC = None


def skrec():
    global SKREC
    if SKREC is None:
        r = random.Random("n66sa-s2ae-skills")
        SKREC = bytearray(r.getrandbits(8) for _ in range(SK_N * SK_SZ))
        for i in range(SK_N):           # Param1 at +0x148: small values and wide ones
            struct.pack_into("<i", SKREC, i * SK_SZ + 0x148, r.choice([0, 1, 50, 99, 100, 101, -5, r.randint(1, 99),
                                                                       r.randint(1, 99), r.getrandbits(32) - (1 << 31)]))
    return SKREC


RMASK = None


def rmask():
    global RMASK
    if RMASK is None:
        r = random.Random("n66sa-s2ae-rmask")
        RMASK = [r.getrandbits(32) & r.getrandbits(32) & r.getrandbits(32) for _ in range(NWORDS)]
    return RMASK


class Case(p1.Case):
    pass


# ----------------------------------------------------------------------------------------------- pvs
def gen_pvs(rnd):
    c = Case("pvs")
    raw = bytearray(rnd.getrandbits(8) for _ in range(0xA0))
    pick = lambda *v: rnd.choice(v)  # noqa: E731
    f = {0x7C: pick(0, rnd.randint(0, 0x4000), rnd.randint(1, 50), rnd.getrandbits(32), -rnd.randint(1, 300)),
         0x84: pick(rnd.randint(0, 0x4000), 0, rnd.randint(1, 200) << 8, -rnd.randint(1, 500), rnd.getrandbits(32)),
         0x88: pick(0, 0, rnd.randint(1, 300), -rnd.randint(1, 300), -rnd.randint(1, 0x3000), rnd.getrandbits(32)),
         0x8C: pick(0, 1, 2, 3, 4, 4, 5, 6, rnd.randint(-3, 9), rnd.getrandbits(32)),
         0x6A: pick(rnd.randint(-4096, 4096), 4096, -4096, 0, rnd.getrandbits(32)),
         0x6E: pick(rnd.randint(-4096, 4096), 4096, -4096, 0, rnd.getrandbits(32))}
    if rnd.random() < 0.3:              # bias toward a negative result of the acceleration: row 35
        f[0x88] = -rnd.randint(1, 0x3000)
        f[0x7C] = rnd.randint(0, 0x800)
        f[0x8C] = 4
    elif rnd.random() < 0.12:           # the sum equal to the maximum: the cap's strictness
        f[0x88] = rnd.randint(1, 300)
        f[0x7C] = rnd.randint(0, 0x800)
        f[0x84] = f[0x7C] + f[0x88]
        f[0x8C] = 4
    for o, v in f.items():
        struct.pack_into("<I", raw, o, u32(v))
    c.put(PATH, bytes(raw))
    mult = rnd.choice([0x400, 0x400, 0, 1, -rnd.randint(1, 100), rnd.randint(1, 0x2000), rnd.getrandbits(32)])
    c.regs = {"EAX": PATH}
    c.ecx = u32(mult)
    c.dumps = [(PATH, 0xA0)]
    c.a = dict(raw=bytes(raw), mult=s32(mult))
    return c


def m_pvs(e, a):
    raw = bytearray(a["raw"])
    g = lambda o: struct.unpack_from("<i", raw, o)[0]  # noqa: E731
    p = lambda o, v: struct.pack_into("<I", raw, o, u32(v))  # noqa: E731
    mult = a["mult"]
    if e.c("mult_lt1", mult, "<", 1):
        mult = 0x400
    if e.t("accel_nz", g(0x88) != 0):
        p(0x8C, g(0x8C) + 1)
        if e.c("count_gt4", g(0x8C), ">", 4):
            p(0x7C, g(0x7C) + g(0x88))
            e.names.add("spec_two_ifs")
            if e.c("v_gt_max", g(0x7C), ">", g(0x84)):
                p(0x7C, g(0x84))
                p(0x88, 0)
                if e.flip == "spec_two_ifs" and g(0x7C) < 0:
                    p(0x7C, 0)
            elif e.c("v_lt0", g(0x7C), "<", 0):
                p(0x7C, 0)
            p(0x8C, 0)
    s = s32(g(0x7C) * mult) >> 6
    p(0x72, s32(g(0x6A) * s) >> 12)
    p(0x76, s32(g(0x6E) * s) >> 12)
    return ("ret", bytes(raw))


# ----------------------------------------------------------------------------------------------- pdir
def pdt(i, k):
    return struct.unpack("<I", img_bytes(PDT + 12 * i + 4 * k, 4))[0]


def gen_pdir(rnd):
    c = Case("pdir")
    span = rnd.choice([8, 64, 600, 5000, 1 << 16, 1 << 23])
    x1 = rnd.choice([rnd.randrange(span, span + (1 << 16)), rnd.randrange(span, 1 << 31), rnd.randrange(span, (1 << 32) - span)])
    y1 = rnd.choice([rnd.randrange(span, span + (1 << 16)), rnd.randrange(span, 1 << 31), rnd.randrange(span, (1 << 32) - span)])
    dx = rnd.choice([0, rnd.randint(-span, span), rnd.randint(-span, span)])
    dy = rnd.choice([0, rnd.randint(-span, span), rnd.randint(-span, span), dx, -dx])
    x2, y2 = u32(x1 + dx), u32(y1 + dy)
    c.put(VOUT, bytes(rnd.getrandbits(8) for _ in range(8)))
    c.put(IOUT, bytes(rnd.getrandbits(8) for _ in range(4)))
    c.ecx, c.edx = VOUT, IOUT
    c.args = [x1, y1, x2, y2]
    c.dumps = [(VOUT, 8), (IOUT, 4)]
    c.a = dict(x1=x1, y1=y1, x2=x2, y2=y2)
    return c


def m_pdir(e, a):
    p1_, p2, p3, p4 = a["x1"], a["y1"], a["x2"], a["y2"]
    b1 = e.t("x2_lt_x1", p3 < p1_)                    # unsigned
    lo, hi = (p3, p1_) if b1 else (p1_, p3)
    if e.t("y2_ge_y1", p4 >= p2):                     # unsigned
        u5, u7 = p4, p2
    else:
        u5, u7 = p2, p4
    b2 = e.c("dx_le_dy", s32(hi - lo), "<=", s32(u5 - u7))
    if b2:
        major, minor = s32(u5 - u7), s32(hi - lo)
    else:
        major, minor = s32(hi - lo), s32(u5 - u7)
    if e.t("major0", major == 0):
        i = 0
    else:
        i = p1.tdiv(s32(minor * 0x7F), major)
    if not 0 <= i < 128:
        return ("model-oob",)
    t0, t1, t2 = pdt(i, 0), pdt(i, 1), pdt(i, 2)
    if b2:
        v0, v1, u = t0, t1, t2
    else:
        v1, v0, u = t0, t1, u32(-t2 - 1) & 0xF
    if e.t("y2_lt_y1", p4 < p2):
        v1 = u32(-v1)
        u = u32(-u - 1) & 0x1F
    if b1:
        v0 = u32(-v0)
        idx = (u + 8) & 0x3F
    else:
        idx = ((u32(-u - 1) & 0x3F) + 8) & 0x3F
    return ("ret", (u32(v0), u32(v1)), idx)


# ----------------------------------------------------------------------------------------------- elem
ELEMS = ((49, 48, 329), (51, 50, 330), (53, 52, 357), (55, 54, 331), (58, 57, 332), (22, 21, -1), (317, 316, 329))


def gen_elem(rnd):
    c = Case("elem")
    hi_s, lo_s, m_s = rnd.choice(ELEMS)
    if rnd.random() < 0.1:
        m_s = rnd.choice([-1, 600, rnd.randrange(ISC_N)])
    val = lambda: rnd.choice([0, rnd.randint(1, 30), rnd.randint(1, 3000), rnd.randint(-50, -1), 1,  # noqa: E731
                              rnd.randint(1, 1 << 20), None])
    sv = {hi_s: val(), lo_s: val()}
    if rnd.random() < 0.4:              # an inverted pair, both >= 1: rows 60, 66
        a_, b_ = sorted([rnd.randint(1, 5000), rnd.randint(1, 5000)])
        sv[hi_s], sv[lo_s] = a_, b_ + (1 if a_ == b_ else 0)
    elif rnd.random() < 0.1:            # an equal pair: no draw
        sv[hi_s] = sv[lo_s] = rnd.randint(1, 5000)
    if m_s >= 0 and m_s != hi_s and m_s != lo_s:
        sv[m_s] = rnd.choice([0, None, rnd.randint(1, 200), rnd.randint(-99, -1), rnd.randint(1, 1000)])
    u = put_unit(c, rnd, ATT, rnd.choice([0, 1, 3]), rnd.randrange(7), sv, [], listflag=True)
    c.regs = {"EAX": hi_s}
    c.args = [ATT, lo_s, u32(m_s)]
    c.dumps = [(ATT + 0x20, 8)]
    c.a = dict(u=u, hi=hi_s, lo=lo_s, m=m_s)
    return c


def m_elem(e, a):
    u = a["u"]
    seed = list(u["seed"])
    hi = stat(u, a["hi"])
    if e.c("hi_lt1", hi, "<", 1):
        return ("ret", 0, tuple(seed))
    lo = stat(u, a["lo"])
    if not e.c("lo_gt0", lo, ">", 0):
        return ("ret", 0, tuple(seed))
    e.names.add("spec_no_swap")
    if e.flip != "spec_no_swap" and e.c("inverted", hi, "<", lo):
        hi, lo = lo, hi
    if e.t("m_set", a["m"] != -1):
        k = stat(u, a["m"]) if a["m"] >= 0 else 0
        if e.t("m_nz", k != 0):
            lo = s32(lo + muldiv(lo, k, 100))
            hi = s32(hi + muldiv(hi, k, 100))
    n = s32(hi - lo)
    r = 0
    if e.c("n_gt0", n, ">", 0):
        low = lcg(seed)
        r = low & (n - 1) if n & (n - 1) == 0 else low % n
    return ("ret", u32(r + lo), tuple(seed))


# ----------------------------------------------------------------------------------------------- smana, rst, dly
def put_entry(c, rnd, rec_bytes=None, null_rec=False):
    rec = bytearray(rnd.getrandbits(8) for _ in range(0x240)) if rec_bytes is None else rec_bytes
    c.put(REC, bytes(rec))
    c.put(ENTRY, le32(0 if null_rec else REC) + bytes(rnd.getrandbits(8) for _ in range(0x3C)))
    return rec


def gen_smana(rnd):
    c = Case("smana")
    sm = rnd.choice([0, 0, rnd.randint(1, 40), rnd.randint(1, 40), -rnd.randint(1, 50), 0x7FFF, rnd.randint(-0x8000, 0x7FFF)])
    rec = bytearray(rnd.getrandbits(8) for _ in range(0x240))
    struct.pack_into("<h", rec, 0x184, sm)
    m8 = rnd.choice([0, sm * 256, sm * 256 - 1, sm * 256 - 1, sm * 256 + 1, rnd.randint(0, 20000), rnd.getrandbits(32),
                     None])
    if sm > 0 and rnd.random() < 0.3:
        m8 = rnd.randint(0, sm * 256 - 1)
    typ = rnd.choice([0, 0, 0, 0, 1, 3, 2])
    st = [12] if rnd.random() < 0.4 else []
    if rnd.random() < 0.08:
        c.put(ENTRY, le32(REC))
        c.put(REC, bytes(rec))
        c.regs = {"ESI": 0, "EDI": ENTRY}
        c.a = dict(u=None, sm=sm)
        return c
    u = put_unit(c, rnd, ATT, typ, rnd.randrange(7), {8: m8}, st)
    put_entry(c, rnd, rec)
    c.regs = {"ESI": ATT, "EDI": ENTRY}
    c.a = dict(u=u, sm=sm)
    return c


def m_smana(e, a):
    u = a["u"]
    if e.t("unit", u is not None) and e.t("player", u["type"] == 0) and e.c("sm_gt0", a["sm"], ">", 0):
        e.names.add("spec_unsigned")
        m = stat(u, 8)
        low = (u32(m) < u32(a["sm"] * 256)) if e.flip == "spec_unsigned" else e.c("m_lt", m, "<", a["sm"] * 256)
        if low and not e.t("st12", has_state(u, 12)):
            return ("ret", 0)
    return ("ret", 1)


def gen_rst(rnd):
    c = Case("rst")
    rec = bytearray(rnd.getrandbits(8) for _ in range(0x240))
    rv = rnd.choice([0, 0, 1, 2, 2, 2, rnd.randint(3, 255)])
    rec[0x228] = rv
    states = [rnd.choice([rnd.randrange(NSTATES), rnd.randrange(NSTATES), -1, -rnd.randint(2, 100),
                          rnd.randint(NSTATES, 0x7FFF)]) for _ in range(3)]
    for i, s in enumerate(states):
        struct.pack_into("<h", rec, 0x22A + 2 * i, s)
    typ = rnd.choice([0, 0, 1, 1, 3, 2, 4])
    on = set()
    mask_states = [s for s in range(NSTATES) if rmask()[s >> 5] >> (s & 31) & 1]
    if rnd.random() < 0.6 and mask_states:
        on.add(rnd.choice(mask_states))                 # a restricted state
    for s in states:
        if 0 <= s < NSTATES and rnd.random() < 0.4:
            on.add(s)
    for _ in range(rnd.randrange(3)):
        on.add(rnd.randrange(NSTATES))
    k = rnd.random()
    if k < 0.05:
        c.regs = {"EAX": ENTRY, "EBX": 0}
        put_entry(c, rnd, rec)
        c.a = dict(u=None, rv=rv, states=states, null="unit")
        return c
    u = put_unit(c, rnd, ATT, typ, rnd.randrange(7), {}, sorted(on))
    if k < 0.1:
        c.regs = {"EAX": 0, "EBX": ATT}
        c.a = dict(u=u, rv=rv, states=states, null="entry")
        return c
    nullrec = rnd.random() < 0.05
    put_entry(c, rnd, rec, null_rec=nullrec)
    c.regs = {"EAX": ENTRY, "EBX": ATT}
    c.a = dict(u=u, rv=rv, states=states, null="rec" if nullrec else None)
    return c


def restricted(e, u):
    """0x0063A510 -> 0x0063A130: any state bit of the unit (its bits only with the list flag) in the mask."""
    if u is None or not u.get("listflag"):
        return False
    return e.t("restricted", any(rmask()[s >> 5] >> (s & 31) & 1 for s in u["states"]))


def m_rst(e, a):
    u = a["u"]
    if not e.t("unit_nz", a["null"] != "unit") or not e.t("entry_nz", a["null"] != "entry"):
        return ("ret", 0)
    if not e.t("rec_nz", a["null"] != "rec"):
        return ("ret", 0)
    rv = a["rv"]
    if e.t("rv0", rv == 0):
        return ("ret", 0 if restricted(e, u) else 1)
    if e.t("rv1", rv == 1) or not e.t("rv2", rv == 2):
        return ("ret", 1)
    if not restricted(e, u):
        return ("ret", 0)
    for i, s in enumerate(a["states"]):
        if e.c("st_neg", s, "<", 0):
            return ("ret", 0)
        if e.t("has", has_state(u, s) and 0 <= s < NSTATES):
            return ("ret", 1)
    return ("ret", 0)


def gen_dly(rnd):
    c = Case("dly")
    typ = rnd.choice([0, 0, 0, 1, 3, 2])
    st = [121] if rnd.random() < 0.6 else []
    k = rnd.random()
    if k < 0.06:
        put_entry(c, rnd)
        c.regs = {"EDI": 0}
        c.args = [ENTRY]
        c.a = dict(u=None, entry="ok")
        return c
    u = put_unit(c, rnd, ATT, typ, rnd.randrange(7), {}, st)
    ent = rnd.choice(["ok", "ok", "ok", "null", "nullrec"])
    if ent == "null":
        c.args = [0]
    else:
        put_entry(c, rnd, null_rec=(ent == "nullrec"))
        c.args = [ENTRY]
    c.regs = {"EDI": ATT}
    c.dumps = [(ATT + 0x20, 8)]
    c.a = dict(u=u, entry=ent)
    return c


def m_dly(e, a):
    u = a["u"]
    if e.t("unit", u is not None) and e.t("player", u["type"] == 0) and e.t("st121", has_state(u, 121)):
        if e.t("entry", a["entry"] == "ok"):
            return ("obs", OBS_LVL, (ATT, ENTRY, 1))
        return ("ret", 1)
    return ("ret", 1)


# ----------------------------------------------------------------------------------------------- kick
def gen_kick(rnd):
    c = Case("kick")
    v = lambda: rnd.choice([0, rnd.randint(1, 200), rnd.randint(1, 30), rnd.randint(-50, -1), rnd.getrandbits(32),  # noqa: E731
                            None, rnd.randint(1, 1 << 20)])
    typ = rnd.choice([0, 0, 1, 1, 3, 2, 4])
    flag = rnd.choice([0, 1, 0, 1, rnd.getrandbits(32)])
    if rnd.random() < 0.08:
        c.regs = {"ESI": 0}
        c.args = [flag]
        c.a = dict(u=None, flag=flag)
        return c
    u = put_unit(c, rnd, ATT, typ, rnd.randrange(7), {0: v(), 2: v(), 12: v()}, [])
    c.regs = {"ESI": ATT}
    c.args = [flag]
    c.a = dict(u=u, flag=flag)
    return c


def m_kick(e, a):
    u = a["u"]
    if e.t("player", u is not None and u["type"] == 0):
        x = s32(stat(u, 0) + stat(u, 2) - 20)
    else:
        x = s32(stat(u, 12) * 3)
    if e.c("x_lt1", x, "<", 1):
        x = 1
    if e.t("flag", a["flag"] != 0):
        return ("ret", u32(p1.tdiv(x, 4) << 8))
    return ("ret", u32(p1.tdiv(x, 3) * 0x100))


# ----------------------------------------------------------------------------------------------- skel
MON = DEF
MDATA = DEF + 0x800


def gen_skel(rnd):
    c = Case("skel")
    cl = rnd.choice([0x16B, 0x16B, 0x16C, 0x16C, rnd.randrange(0x300), 0x16A, 0x16D])
    lvl = rnd.choice([0, 1, 2, 3, 3, rnd.randint(3, 30), rnd.randint(3, 30), rnd.randint(1, 30), -rnd.randint(1, 5),
                      rnd.getrandbits(32)])
    sid = rnd.choice([rnd.randrange(SK_N), rnd.randrange(SK_N), -1, SK_N, rnd.getrandbits(32)])
    seed = (rnd.getrandbits(32), rnd.getrandbits(32))
    cu = put_unit(c, rnd, ATT, rnd.choice([0, 0, 1, 3]), rnd.randrange(7), {}, [], seed=seed)
    k = rnd.random()
    mtype = 1 if k < 0.8 else rnd.choice([0, 2, 3, 4])
    md = rnd.random() < 0.9
    if k < 0.06:
        c.ecx, c.edx = ATT, 0
        c.args = [u32(sid), u32(lvl)]
        c.dumps = [(ATT + 0x20, 8)]
        c.a = dict(seed=seed, m=None, cls=None, lvl=s32(lvl), sid=s32(sid))
        return c
    c.put(MON, bytes(rnd.getrandbits(8) for _ in range(0x100)))
    c.put(MON, le32(mtype) + le32(cl))
    mdb = bytes(rnd.getrandbits(8) for _ in range(0x40))
    c.put(MDATA, mdb)
    c.put(MON + 0x14, le32(MDATA if md else 0))
    c.ecx, c.edx = ATT, MON
    c.args = [u32(sid), u32(lvl)]
    c.dumps = [(ATT + 0x20, 8), (MDATA, 0x40)]
    c.a = dict(seed=seed, m=mtype, cls=cl, lvl=s32(lvl), sid=s32(sid), md=md, mdb=mdb)
    return c


def sdb(i, k):
    return img_bytes(SDB + 9 * i + k, 1)[0]


def set_bytes(e, a, mdb, eax, b, draw, seed):
    """sub_005C4180_SummonSetDataBytes(EAX index, ECX summon; b, draw): the row's bytes into MonsterData, +0x0B
    only when b != 0, then either +0x09 or one step of the caster's seed (EDI) and the 0x005B0D70 call."""
    i = 10 if e.c("idx_gt10", eax, ">", 10) else eax
    ok = a["m"] == 1 and a["md"]
    if ok:
        for k, off in ((0, 4), (2, 5), (3, 0xC), (4, 0xD), (5, 6), (6, 7), (7, 8)):
            mdb[off] = sdb(i, k)
        if e.t("b_nz", b != 0):
            mdb[0xB] = sdb(i, 1)
    if not draw:
        if ok:
            mdb[9] = sdb(i, 8)
        return None
    low = lcg(seed)
    if ok:
        mdb[0xF] = low & 3
        mdb[0x10] = low & 3
    ecx = struct.unpack_from("<I", mdb, 0x28)[0] if ok else 0
    return ("obs", OBS_5B0D70, (ecx, 1), (0, u32(-666)))


def m_skel(e, a):
    seed = list(a["seed"])
    if a["m"] is None:
        return ("ret", tuple(seed), None)
    mdb = bytearray(a["mdb"])
    cl = a["cls"]
    if e.t("c363", cl == 0x16B):
        flag = 0
        if e.c("lvl_gt2", a["lvl"], ">", 2):
            sid = a["sid"]
            p = 0
            if 0 <= sid < SK_N:
                p = struct.unpack_from("<i", skrec(), sid * SK_SZ + 0x148)[0]
            low = lcg(seed)
            flag = 1 if e.c("roll_lt", s32(low % 100), "<", p) else 0
        set_bytes(e, a, mdb, 1, flag, False, seed)
        return ("ret", tuple(seed), bytes(mdb))
    if e.t("c364", cl == 0x16C):
        out = set_bytes(e, a, mdb, 1, 0, True, seed)
        return out + (tuple(seed), bytes(mdb))
    return ("ret", tuple(seed), bytes(mdb))


# ----------------------------------------------------------------------------------------------- driver
GEN = {"pvs": gen_pvs, "pdir": gen_pdir, "elem": gen_elem, "smana": gen_smana, "rst": gen_rst, "dly": gen_dly,
       "kick": gen_kick, "skel": gen_skel}
MODEL = {"pvs": m_pvs, "pdir": m_pdir, "elem": m_elem, "smana": m_smana, "rst": m_rst, "dly": m_dly,
         "kick": m_kick, "skel": m_skel}


def predict(fam, a, flip=None):
    e = E(flip)
    try:
        out = MODEL[fam](e, a)
    except (TypeError, KeyError, IndexError, AttributeError, ZeroDivisionError):
        return ("model-null",), e.names
    return out, e.names


def write_spec(d):
    im = p1.img()
    with open(os.path.join(d, "monstats.bin"), "wb") as f:
        f.write(bytes(im.ms))
    with open(os.path.join(d, "isc.bin"), "wb") as f:
        f.write(bytes(ISC_N * ISC_SZ))
    with open(os.path.join(d, "skills.bin"), "wb") as f:
        f.write(bytes(skrec()))
    with open(os.path.join(d, "rmask.bin"), "wb") as f:
        f.write(b"".join(le32(x) for x in rmask()))
    dt = bytearray(0x1000)
    for off, v in ((0xC4, NSTATES), (0x110, MASKS), (0xA78, MS), (0xA80, MS_N), (0xB98, SK), (0xBA0, SK_N),
                   (0xBCC, ISC), (0xBD4, ISC_N)):
        struct.pack_into("<I", dt, off, v)
    with open(os.path.join(d, "dt.bin"), "wb") as f:
        f.write(bytes(dt))
    lines = ["# plan 0066 S2ae part 1 (tools/skills_s2ae_emu.py): declared tables",
             "dword %08x %08x" % (G_DT, DT),
             "load %08x %s" % (DT, os.path.join(d, "dt.bin")),
             "load %08x %s" % (MS, os.path.join(d, "monstats.bin")),
             "load %08x %s" % (ISC, os.path.join(d, "isc.bin")),
             "load %08x %s" % (SK, os.path.join(d, "skills.bin")),
             "load %08x %s" % (MASKS, os.path.join(d, "rmask.bin"))]
    lines += ["guard %08x" % x for x in FATAL + ALLOC]
    lines += ["observe %08x" % x for x in (OBS_LVL, OBS_5B0D70)]
    with open(os.path.join(d, "s2ae.mem"), "w") as f:
        f.write("\n".join(lines) + "\n")


def build(limit=None):
    cases = []
    for fam in FAMILIES:
        rnd = random.Random("n66sa-s2ae-" + fam)
        for _ in range(NCASES[fam] if limit is None else min(limit, NCASES[fam])):
            cases.append(GEN[fam](rnd))
    return cases


def cmd_cases(d, limit=None):
    os.makedirs(d, exist_ok=True)
    write_spec(d)
    cases = build(limit)
    with open(os.path.join(d, "s2ae.cases"), "w") as f:
        for c in cases:
            f.write("\n".join(c.lines()) + "\n")
    print("cases %d -> %s" % (len(cases), os.path.join(d, "s2ae.cases")))


def observed(fam, k):
    if "stop" in k:
        return ("stop", k["stop"], k["msg"]), None
    dump = k["dumps"]
    if "obs" in k:
        st = k["stack"]
        ret = struct.unpack_from("<I", st, 0)[0]
        if fam == "dly":
            return ("obs", k["obs"], struct.unpack_from("<3I", st, 4)), ret
        if fam == "skel":
            regs = (int(k["regs"]["ecx"], 16), int(k["regs"]["edx"], 16))
            return ("obs", k["obs"], regs, struct.unpack_from("<2I", st, 4), struct.unpack("<2I", dump[ATT + 0x20]),
                    dump.get(MDATA)), ret
    if k["pop"] != POP[fam]:
        return ("pop", k["pop"]), None
    if fam == "pvs":
        return ("ret", dump[PATH]), None
    if fam == "pdir":
        return ("ret", struct.unpack("<2I", dump[VOUT]), struct.unpack("<I", dump[IOUT])[0]), None
    if fam == "elem":
        return ("ret", k["eax"], struct.unpack("<2I", dump[ATT + 0x20])), None
    if fam == "skel":
        return ("ret", struct.unpack("<2I", dump[ATT + 0x20]), dump.get(MDATA)), None
    if fam == "dly":
        return ("ret", k["eax"] & 0xFF), None
    if fam in ("smana", "rst"):
        return ("ret", k["eax"] & (0xFF if fam == "rst" else M32)), None
    return ("ret", k["eax"]), None


M32 = 0xFFFFFFFF


def norm(fam, want):
    if want[0] == "ret" and fam == "elem":
        return ("ret", want[1], tuple(want[2]))
    return want


def same(want, got):
    if want[0] in ("model-null", "model-oob") or want[0] != got[0] or len(want) != len(got):
        return False
    for w, g in zip(want, got):
        if w is None:
            continue
        if isinstance(w, (tuple, list)):
            if g is None or tuple(w) != tuple(g):
                return False
        elif w != g:
            return False
    return True


CONST_READS = ((BITMASK, BITMASK + 128, "g_BitMask32 0x006CE268 (.rdata)"),
               (PDT, PDT + 12 * 128, "g_PathDirTable 0x006EB7E0 (.rdata)"),
               (SDB, SDB + 9 * 11, "SummonSetDataBytes rows 0x00741940 (.data; reference scan in `static`)"))


def account(reads, writes):
    bad = []
    for pc, addr, n, cnt in reads:
        if not any(lo <= addr and addr + n <= hi for lo, hi, _ in CONST_READS):
            bad.append(("R", pc, addr, n, cnt))
    for pc, addr, n, cnt in writes:
        bad.append(("W", pc, addr, n, cnt))
    return bad


def cmd_check(d, limit=None):
    cases = build(limit)
    calls, reads, writes = p1.read_out(os.path.join(d, "s2ae.out"))
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
        want = norm(fam, want)
        names_by_fam[fam] |= names
        got, site = observed(fam, k)
        ok = same(want, got)
        if ok and want[0] == "obs":
            ok = site == SITE[(fam, want[1])]
        per[fam][0] += 1
        kd = want[0] + (":%x" % want[1] if want[0] == "obs" else "")
        if want[0] == "ret" and fam in ("smana", "rst", "dly"):
            kd += "=%d" % want[1]
        per[fam][2][kd] = per[fam][2].get(kd, 0) + 1
        if not ok:
            per[fam][1] += 1
            bad += 1
            if bad <= 25:
                print("MISMATCH %d %s want=%r got=%r site=%r" % (i, fam, want, got, site))
        got_all.append(got)
    rows = {}
    for c in cases:
        a = c.a
        if c.fam == "pvs":
            raw = a["raw"]
            g = lambda o: struct.unpack_from("<i", raw, o)[0]  # noqa: E731
            if g(0x88) != 0 and s32(g(0x8C) + 1) > 4:
                v = s32(g(0x7C) + g(0x88))
                key = "pvs:v_lt0_clamped" if v < 0 and not v > g(0x84) else \
                    "pvs:capped_negmax" if v > g(0x84) and g(0x84) < 0 else None
                if key:
                    rows[key] = rows.get(key, 0) + 1
                if s32(g(0x8C) + 1) > 5:
                    rows["pvs:count_gt5"] = rows.get("pvs:count_gt5", 0) + 1
            if a["mult"] < 1:
                rows["pvs:mult_lt1"] = rows.get("pvs:mult_lt1", 0) + 1
        elif c.fam == "elem":
            hi, lo = stat(a["u"], a["hi"]), stat(a["u"], a["lo"])
            if hi >= 1 and lo >= 1 and lo > hi:
                rows["elem:inverted"] = rows.get("elem:inverted", 0) + 1
                if a["m"] >= 0 and stat(a["u"], a["m"]) != 0:
                    rows["elem:inverted_mastery"] = rows.get("elem:inverted_mastery", 0) + 1
            if hi >= 1 and lo >= 1 and a["m"] >= 0 and stat(a["u"], a["m"]) != 0:
                rows["elem:mastery_nz"] = rows.get("elem:mastery_nz", 0) + 1
        elif c.fam == "skel" and a["m"] is not None:
            key = "skel:363_lvl_le2" if a["cls"] == 0x16B and a["lvl"] <= 2 else \
                "skel:363_lvl_gt2" if a["cls"] == 0x16B else "skel:364" if a["cls"] == 0x16C else "skel:other"
            rows[key] = rows.get(key, 0) + 1
    print("ROWS " + " ".join("%s=%d" % kv for kv in sorted(rows.items())))
    for f in FAMILIES:
        n, b, kinds = per[f]
        print("FAMILY %s cases=%d mismatches=%d outcomes %s" % (f, n, b, " ".join(
            "%s:%d" % kv for kv in sorted(kinds.items()))))
    ctl_bad, ctl_lines = 0, []
    for f in FAMILIES:
        fc = [(c, g) for c, g in zip(cases, got_all) if c.fam == f]
        base = [norm(f, predict(f, c.a)[0]) for c, _ in fc]
        for nm in sorted(names_by_fam[f]):
            sep = passed = 0
            for (c, got), b in zip(fc, base):
                alt = norm(f, predict(f, c.a, flip=nm)[0])
                if not same(b, alt) or not same(alt, b):
                    sep += 1
                    if same(alt, got):
                        passed += 1
            ctl_lines.append("CONTROL %s %s sep=%d passed=%d" % (f, nm, sep, passed))
            if passed:
                ctl_bad += 1
    print("\n".join(ctl_lines))
    nsep0 = sum(1 for x in ctl_lines if " sep=0 " in x)
    acc = account(reads, writes)
    for x in acc[:40]:
        print("UNACCOUNTED %s pc=%08x addr=%08x n=%d count=%d" % x)
    traced = {}
    for pc, addr, n, cnt in reads:
        traced[pc] = traced.get(pc, 0) + cnt
    print("TRACED " + " ".join("%08x:%d" % kv for kv in sorted(traced.items())))
    stops = sum(1 for k in calls if "stop" in k)
    print("S2AE total cases=%d mismatches=%d stops=%d controls=%d unseparated=%d controls_passed=%d unaccounted=%d"
          % (len(cases), bad, stops, len(ctl_lines), nsep0, ctl_bad, len(acc)))
    return 1 if bad or ctl_bad or acc else 0


STATIC = (
    ("pvs", 0x006502D0, 0x00650350),
    ("pdir", 0x0064FC60, 0x0064FDC0),
    ("elem", 0x005A8910, 0x005A89A0),
    ("smana", 0x006440F0, 0x0064414A),
    ("rst", 0x00644060, 0x006440E8),
    ("restricted", 0x0063A510, 0x0063A526),
    ("restricted2", 0x0063A130, 0x0063A180),
    ("dly", 0x006478F0, 0x00647954),
    ("kick", 0x00644C20, 0x00644C8F),
    ("classroll", 0x005C4430, 0x005C4468),
    ("skel", 0x005C4300, 0x005C43CA),
    ("skel364", 0x005C43D0, 0x005C4428),
    ("setbytes", 0x005C4180, 0x005C42F2),
    ("physmax-kick", 0x00647D00, 0x00647D4C),
    ("do2-calls", 0x005AE400, 0x005AE47F),
    ("create-sunit", 0x0059FC70, 0x0059FC7A),
)


def cmd_static():
    if p1.img() is None:
        return 1
    for label, lo, hi in STATIC:
        out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "-M", "intel", "--start-address=0x%x" % lo,
                              "--stop-address=0x%x" % hi, p1.EXE], capture_output=True, text=True, check=True).stdout
        for ln in out.splitlines():
            ln = ln.strip()
            if ln and ln[0] in "0123456789abcdef" and ":\t" in ln:
                print("%s %s" % (label, " ".join(ln.split())))
    for va in (PDT, SDB):
        print("SECTION %08x %s" % (va, W.section_of(va)))
    # every instruction of .text whose operand names an address inside the 0x00741940 rows (displacement or
    # immediate): the reference scan of ADR-0015 (2) for the one .data table the cases read
    A = W.asm()
    hits = []
    for va in sorted(A.ins):
        mn, ops = A.ins[va]
        for tok in ops.replace(",", " ").replace("[", " ").replace("]", " ").replace("+", " ").split():
            if tok.startswith("0x"):
                try:
                    v = int(tok, 16)
                except ValueError:
                    continue
                if SDB <= v < SDB + 9 * 11:
                    hits.append("%08x %s %s" % (va, mn, ops))
    for h in hits:
        print("SDB-REF " + h)
    print("SDB-REF count=%d" % len(hits))
    return 0


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
    ap.add_argument("cmd", choices=("cases", "check", "static", "manifest"))
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    o = ap.parse_args(argv)
    if o.cmd == "cases":
        cmd_cases(o.dir, o.limit)
        return 0
    if o.cmd == "check":
        return cmd_check(o.dir, o.limit)
    if o.cmd == "static":
        return cmd_static()
    cmd_manifest(o.dir, o.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

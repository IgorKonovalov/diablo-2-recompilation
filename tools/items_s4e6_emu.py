#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S4e part 5b (`lane/n66z`): the Blood Golem's heal with v = 0 and v > 0, the potion's doubling
draw at chosen draws, kind 3's return for amounts at and below 0, and StackRequest to the merge, run on the pinned
Game.exe under Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java and compared with
the models below and tools/item_inventory.py. Parts 1 to 5a (tools/stats_s4e_emu.py, items_s4e_emu.py to
items_s4e5_emu.py, run/ to run5/) stay unchanged; this tool builds its cases on tools/use_emu.py's world (golem, double,
potret) and on tools/items_s4e3_emu.py's units with tools/item_emu2.py's tables (stackreq), all unchanged.

    python3 -I tools/items_s4e6_emu.py cases [--dir D] [--limit N]   write D/<family>.cases, .mem, .json
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/items_s4e6_emu.py check [--dir D]               compare, account every traced access, controls
    python3 -I tools/items_s4e6_emu.py static                        objdump pins
    python3 -I tools/items_s4e6_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66z/s4e/run6. Every draw comes from random.Random("n66z-s4e6-<family>"); `check` regenerates
the cases' models from the same seeds (the .json files are a record of them).

Families (function, convention; boundaries; rows):
  golem    GolemHealShare 0x005C6870 (ECX game, EDX user; v), v = 0 weighted, and GolemHeal 0x005C5F10 (EAX v, EBX golem)
           called directly: to the return or UnitSetStat 0x00627260 (observed; return address 0x005C6901 or 0x005C5F47).
                                                                                            items/use 52
  double   ItemUsePotion 0x005BE3F0 (kind 3) with one slot of stat 6 or 8 and len 0, the seed built so that the two
           draws give a chosen (r1, r2) at and around r2 = r1 >> 1, players and non-players: to UnitAddStat 0x006272B0
           (observed) or the return.                                                      items/use 38
  potret   ItemUsePotion with amounts at and below 0 (zero, negative, and positive amounts the scale or the shift wraps
           negative), and refills whose len + rem ≤ 0: to the return or the first of UnitAddStat, STATLIST_Alloc,
           UnitQueueEvent, STATLIST_SetStat, GolemHeal (observed).                         items/use 34
  stackreq StackRequest 0x0055E7C0 (ECX game, EDX player; guid1, guid2, &out): equal guids, missing units, a non-item, the
           target's page, every ItemsCanStack break: to the return or StackMerge 0x0055E590 (observed, return address
           0x0055E8B1).                                                                    items/inventory 58

Controls: each a wrong reading (the spec's where it differs); `sep` counts the cases a control's prediction differs
from the model's, `passed` those where the emulator still equals the control (must be 0 when sep > 0).
Stdlib only, plus objdump for `static`.
"""
import argparse
import collections
import json
import os
import random
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import item_inventory as inv  # noqa: E402
import rng  # noqa: E402
import use_emu as U  # noqa: E402
import item_emu2 as IE2  # noqa: E402
import items_s4e3_emu as P3  # noqa: E402
from party_emu import parse_out  # noqa: E402

M32 = 0xFFFFFFFF
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
DEFDIR = os.path.join(ROOT, "workspace", "logs", "n66z", "s4e", "run6")
FAMILIES = ("golem", "double", "potret", "stackreq")
NCASES = {"golem": 1200, "double": 3000, "potret": 2400, "stackreq": 2000}
F_SHARE, F_GHEAL, F_SETSTAT = 0x005C6870, 0x005C5F10, 0x00627260
SITE_V0, SITE_HEAL = 0x005C6901, 0x005C5F47
F_REQ, F_MERGE, SITE_MERGE = 0x0055E7C0, 0x0055E590, 0x0055E8B1
GSL = U.GOLEM + 0x200                 # the golem's stat list; its array at GSL + 0x100
OUTW = P3.PKT + 0x30                  # StackRequest's flag word
OBSERVE = {"golem": (F_SETSTAT,), "double": (U.F_ADD, U.F_ALLOC, U.F_QUEUE, U.F_SET, U.F_GHEAL),
           "potret": (U.F_ADD, U.F_ALLOC, U.F_QUEUE, U.F_SET, U.F_GHEAL), "stackreq": (F_MERGE,)}
# zero-filled before every case (the image keeps earlier cases' writes otherwise)
ZERO_USE = [(U.GAME, 0x2000), (U.POOL, 0x200), (U.USER, 0x10000), (U.ISC, 0x144 * U.NISC)]


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


# ================================================================================================= golem
def put_golem_stats(c, life, mx):
    c.d32(U.GOLEM + 0x5C, GSL)
    U.put_stats(c, GSL, GSL + 0x100, {6: life & M32, 7: mx & M32}, special=True)


def model_golem(m, ctl=None):
    """-> ["ret", eax] or ["set", site, unit, stat, value, layer]."""
    if m["fn"] == "heal":
        return heal(m, m["v"], ctl)
    v = m["v"]
    if m["nouser"] or m["kind"] != "golem":
        return ["ret", v & M32]
    if v == 0 and ctl != "v0_as_heal":
        return ["set", SITE_V0, U.GOLEM, 6, m["mx"] & M32, 0]
    if m["row"] < 0:
        return ["ret", v & M32]
    share = inv.tdiv(s32(m["share"] * v), 100)
    r = heal(m, share, ctl)
    if r[0] == "set":
        return r
    return ["ret", s32(v - r[1]) & M32]


def heal(m, v, ctl=None):
    """GolemHeal 0x005C5F10: v ≤ 0 returns 0; else life + v, capped at the maximum, signed compare, i32 add."""
    if v <= 0 and not (ctl == "heal0_full" and v == 0):
        return ["ret", 0]
    e = s32(m["life"] + v)
    if ctl == "nocap":
        pass
    elif ctl == "cap_unsigned":
        if (e & M32) > (m["mx"] & M32):
            e = m["mx"]
    elif e > s32(m["mx"]):
        e = m["mx"]
    return ["set", SITE_HEAL, U.GOLEM, 6, e & M32, 0]


def gen_golem(r):
    c = U.Case()
    u = inv.Unit(typ=0, cls=r.randrange(7), uid=7, low=r.getrandbits(32), high=r.getrandbits(32))
    U.put_unit(c, u)
    fn = "heal" if r.random() < 0.3 else "share"
    kind = r.choice(("golem",) * 8 + ("nopet", "otherclass", "nottype1"))
    share = r.choice((0, 10, 20, 50, 100, 150, r.randrange(0, 200), -20))
    mx = r.choice((r.randrange(1, 4000) << 8, r.randrange(1, 1 << 24), 0, 0x7FFFFF00))
    life = r.choice((r.randrange(0, mx + 1) if mx > 0 else 0, mx, 0, mx - r.randrange(1, 300) if mx > 300 else mx,
                     mx + r.randrange(1, 500), 0x7FFFFFF0))
    wrap = r.random() < 0.12                  # life + v past 2^31 - 1: the i32 add wraps negative
    if wrap:
        mx, life = r.choice((0x7FFFFF00, r.randrange(1, 1 << 24))), 0x7FFFFFFF - r.randrange(0, 1 << 20)
    v = r.choice((0, 0, 0, r.randrange(1, 1 << 16), r.randrange(1, 1 << 24), 1, -r.randrange(1, 5000),
                  r.randrange(1 << 24, 1 << 31)))
    nouser = fn == "share" and r.random() < 0.03
    if fn == "heal":
        v = r.choice((0, 0, -1, -r.randrange(1, 1 << 20), -(1 << 31), r.randrange(1, 1 << 16), r.randrange(1, 1 << 31)))
        kind = "golem"
    if wrap:
        v = r.randrange(1 << 21, 1 << 30)
        share = r.choice((50, 100, 150))
    row = 0
    if kind != "nopet":
        U.put_golem(c, r, share)
        row = s32(r.choice((0, 1, 5)))
    if kind == "otherclass":
        c.d32(U.GOLEM + 4, 0x121)
    if kind == "nottype1":
        c.d32(U.GOLEM, 3)
    if kind != "nopet" and r.random() < 0.05 and fn == "share":
        c.d16(U.MS + 0x122 * 0x1A8 + 0x170, 0xFFFF)       # a MonStats row without a skill: row −1
        row = -1
    put_golem_stats(c, life, mx)
    m = dict(fn=fn, kind=kind, share=share, mx=mx, life=life, v=v, nouser=nouser, row=row, wrap=wrap)
    m["want"] = model_golem(m)
    m["ctl"] = {k: model_golem(m, k) for k in ("v0_as_heal", "heal0_full", "nocap", "cap_unsigned")}
    if fn == "heal":
        c.lines += ["r eax %08x" % (v & M32), "r ebx %08x" % U.GOLEM]
        return c.call(F_GHEAL, 0, 0), m
    return c.call(F_SHARE, U.GAME, 0 if nouser else U.USER, v & M32), m


# ================================================================================================= double, potret
def seed_for(r, n, r1, r2):
    """A seed (low, high) whose first RNG_Range(n) gives r1 and second RNG_Range(100) gives r2 (rng.step's LCG)."""
    for _ in range(100000):
        low1 = r1 + n * r.randrange(0, (1 << 32) // n - 1)
        t = r2 + 100 * r.randrange(0, (1 << 32) // 100 - 1)
        high1 = (t - low1 * rng.MULT) & M32
        if high1 >= rng.MULT:
            continue
        x = (high1 << 32) | low1
        low0, high0 = x // rng.MULT, x % rng.MULT
        if low0 >> 32:
            continue
        a, lo, hi = rng.rng_range(low0, high0, n)
        b, lo, hi = rng.rng_range(lo, hi, 100)
        assert (a, b) == (r1, r2)
        return low0, high0
    raise RuntimeError("no seed")


def stat_case(r, i, u, rec, frame, mode):
    c = U.Case()
    c.d32(U.GAME + U.FRAME_OFF, frame)
    c.d32(U.GAME + U.MEMCTX_OFF, 0x55AA0000 | i)
    row = r.randrange(0, 151)
    if mode == "norec":
        row = 200 + r.randrange(50)
    c.d32(U.ITEM, 4)
    c.d32(U.ITEM + 4, row)
    U.put_unit(c, u)
    if u.slist is not None:
        U.put_state_list(c, u, rec["state"], r)
    if mode != "norec":
        U.put_rec(c, row, rec)
    c.dump(U.USER + 0x20, 8)
    m = dict(f="stat3", entry=3, u=u.__dict__.copy(), rec=rec, frame=frame, mode=mode, norec=mode == "norec",
             memctx=0x55AA0000 | i)
    m["u"]["stats"] = dict(m["u"]["stats"])
    return c, m


def gen_double(r, i):
    u = U.rand_unit(r)
    u.type = r.choice((0, 0, 0, 1))
    u.cls = r.randrange(7) if u.type == 0 else r.randrange(700)
    s = r.choice((inv.LIFE, inv.MANA))
    src = inv.VIT if s == inv.LIFE else inv.ENE
    n = r.choice((1, 2, 3, 10, 25, 50, 100, 150, 165, 199, 200, 201, 202, 250, 500, r.randrange(1, 1000)))
    if u.type == 1 and r.random() < 0.4:
        n = 0
    if r.random() < 0.03:
        n = r.choice((-1, -100))
    u.stats[src] = n
    if n > 0:
        r1 = r.choice((r.randrange(n), n - 1, 0, min(n - 1, 199), min(n - 1, 200), min(n - 1, 201), r.randrange(n)))
        h = r1 >> 1
        r2 = min(99, r.choice((max(h - 1, 0), max(h - 1, 0), h, h, h + 1, 99, 0, r.randrange(100))))
        u.low, u.high = seed_for(r, n, r1, r2)
    else:
        r1 = r2 = None
    amt = r.choice((1, 2, 3, 30, 100, r.randrange(1, 5000)))
    rec = {"len": 0, "state": r.randrange(1, U.NSTATES), "slots": [(s, amt), (-1, 0), (-1, 0)],
           "isc": {s: (0, 0xFFFF)}, "blanklen": r.random() < 0.7}
    c, m = stat_case(r, i, u, rec, r.randrange(0, 1 << 20), "instant")
    m.update(n=n, r1=r1, r2=r2, s=s)
    m["want"] = form_model(stat3(m))
    m["ctl"] = {k: form_model(stat3(m, k)) for k in ("le", "half", "swap", "nodraw_nonplayer")}
    return c.call(U.ENTRY[3], U.GAME, U.USER, U.ITEM, 0, 0, 0, 0), m


WRAPS = (0x00800000, 0x00FFFFFF, 0x01000000, 0x40000000, 0x7FFFFFFF)


def gen_potret(r, i):
    u = U.rand_unit(r)
    frame = r.randrange(0, 1 << 20)
    mode = r.choice(("instant", "instant", "fresh", "refill0", "refill1", "refill1", "both", "both", "badstate",
                     "norec", "refill_end", "refill_end"))
    ln = 0 if mode in ("instant",) else r.choice((128, 160, 192, 256, 750, r.randrange(1, 2000), 0, -5))
    if mode == "both" and r.random() < 0.5:
        ln = 0
    state = r.randrange(1, U.NSTATES)
    if mode == "badstate":
        state = r.choice((0, -1, U.NSTATES, U.NSTATES + 5))
        ln = r.randrange(1, 500)
    pool = U.STAT_POOL
    s0, s1 = r.choice(pool), r.choice(pool)

    def amount():                             # an i32, as the calc returns it
        return s32(r.choice((0, 0, -1, -5, -300, -r.randrange(1, 1 << 30), -(1 << 31), r.choice(WRAPS),
                             r.choice(WRAPS) + r.randrange(0, 0x100), r.randrange(1, 300))))
    isc = {}
    for s in (s0, s1):
        isc[s] = (r.choice((0, 0, 8, r.randrange(0, 12), 24, 31)), U.MAXOF.get(s, 0xFFFF))
    if mode == "refill_end":                  # slot 0 at or below 0, slot 1 positive, len + rem <= 0 below
        ln = r.choice((128, 160, 192, 256, 750, r.randrange(1, 2000)))
        s1 = r.choice((inv.MANA, inv.MANAREC, 10, 13))
        isc[s1] = (r.choice((0, 0, 8)), U.MAXOF.get(s1, 0xFFFF))
        slots = [(s0, r.choice((0, -1, -50))), (s1, r.randrange(1, 400))]
    elif mode == "refill1":
        slots = [(s0, r.choice((0, -1, -50))), (s1, amount())]
    elif mode == "both":
        slots = [(s0, amount()), (s1, amount())]
    else:
        slots = [(s0, amount()), (-1, 0)]
    slots.append((-1, 0))
    if s0 == s1:
        isc[s0] = isc[s1]
    rec = {"len": ln, "state": state, "slots": slots, "isc": isc, "blanklen": r.random() < 0.7}
    if mode == "refill_end" or (mode in ("refill0", "refill1", "both") and ln > 0 and r.random() < 0.8):
        rem = r.choice((r.randrange(1, 300), r.randrange(-50, 0), 0, -ln, -ln - 3, -ln - r.randrange(1, 100)))
        if mode == "refill_end":
            rem = r.choice((-ln, -ln - 1, -ln - r.randrange(1, 1000), 1 - ln))
        base = {s: r.choice((r.randrange(0, 4000), -r.randrange(1, 900))) for s in {s0, s1}}
        if inv.LIFE in (s0, s1) and ln + rem <= 0:          # the loop's end would reach the life-percent message
            rem = 5
        u.slist = {"end": (frame + rem) & M32, "base": base}
    golem = u.type == 0 and r.random() < 0.08
    c, m = stat_case(r, i, u, rec, frame, mode)
    if golem:
        u.golem = {"share": r.choice((0, 10, 33, 50, 100))}
        U.put_golem(c, r, u.golem["share"])
        m["u"]["golem"] = u.golem
    m["want"] = form_model(stat3(m))
    m["ctl"] = {k: form_model(stat3(m, k)) for k in ("unsigned_amount", "applied_only")}
    item = U.ITEM if not (mode == "norec" and r.random() < 0.3) else 0
    return c.call(U.ENTRY[3], U.GAME, U.USER, item, 0, 0, 0, 0), m


def unit_of(m):
    d = m["u"]
    return inv.Unit(d["type"], d["cls"], d["uid"], d["low"], d["high"], {int(k): v for k, v in d["stats"].items()},
                    d["slist"] and {"end": d["slist"]["end"], "base": {int(k): v for k, v in d["slist"]["base"].items()}},
                    d["golem"])


def stat3(m, ctl=None):
    """Kind 3 (0x005BE3F0) as tools/item_inventory.py's use_stat_entry(3, ...) with the controls' changes; the real
    reading (ctl None) is use_stat_entry itself."""
    u = unit_of(m)
    rec = dict(m["rec"], isc={int(k): v for k, v in m["rec"]["isc"].items()})
    if m["norec"]:
        return ("ret", 0)
    if ctl is None:
        return inv.use_stat_entry(3, u, rec, m["frame"], m["memctx"], U.NISC, U.NSTATES)
    saved_scale, saved_entry = inv.potion_scale, None

    def scale(uu, s, v):
        if s in (inv.MANAREC, inv.HPREGEN):
            v = inv.i32(v << 8)
        if s in (inv.MANA, inv.MANAREC):
            v, src = inv.mana_mul(uu.type, uu.cls, v), inv.ENE
        elif s in (inv.LIFE, inv.HPREGEN):
            v, src = inv.life_mul(uu.type, uu.cls, v), inv.VIT
        else:
            return v
        n = uu.stat(src)
        if ctl == "nodraw_nonplayer" and uu.type != 0:
            return v
        if n > 0:
            if ctl == "swap":
                r2, r1 = uu.range(100), uu.range(n)
            else:
                r1, r2 = uu.range(n), uu.range(100)
            if ctl == "le":
                d = r2 <= (r1 >> 1)
            elif ctl == "half":
                d = r2 < r1
            else:
                d = r2 < (r1 >> 1)
            if d:
                v = inv.i32(v * 2)
        return v
    inv.potion_scale = scale
    try:
        if ctl in ("unsigned_amount", "applied_only"):
            return stat3_variant(u, rec, m, ctl)
        return inv.use_stat_entry(3, u, rec, m["frame"], m["memctx"], U.NISC, U.NSTATES)
    finally:
        inv.potion_scale = saved_scale
        del saved_entry


def stat3_variant(u, rec, m, ctl):
    """use_stat_entry(3) with one test changed: `unsigned_amount` skips a slot only at v = 0 (an unsigned v ≤ 0);
    `applied_only` returns 0 for a slot whose len + rem ≤ 0 (only an applied amount counts)."""
    ln, state, frame = rec["len"], rec["state"], m["frame"]
    sl, rem = None, 0
    if ln > 0:
        if state < 1 or state >= U.NSTATES:
            return ("ret", 0)
        sl = u.slist
        if sl is not None:
            rem = inv.i32(sl["end"] - frame)
    done = 0
    for k, (s, calc) in enumerate(rec["slots"]):
        if s < 0 or s >= U.NISC:
            break
        shift, maxstat = rec["isc"].get(s, (0, 0xFFFF))
        v = inv.potion_scale(u, s, calc)
        v = inv.i32(v << (shift & 31))
        if (v == 0) if ctl == "unsigned_amount" else (v <= 0):
            continue
        if s in (inv.LIFE, inv.HPREGEN) and u.type == 0:
            v2, share = inv.golem_split(u, v)
            if share is not None:
                return ("golem", share)
            v = v2
        if ln < 1:
            cur = u.stat(s)
            if maxstat < U.NISC:
                top = u.stat(maxstat)
                if inv.i32(cur + v) > top:
                    v = inv.i32(top - cur)
            return ("addstat", s, v)
        end = inv.i32(frame + rem + ln)
        if sl is None:
            return ("alloc", end)
        base = sl["base"].get(s, 0)
        if k == 0:
            return ("queue", end)
        d = inv.i32(ln + rem)
        if d > 0:
            return ("setstat", s, inv.tdiv(inv.i32(inv.i32(base * rem) + v), d), end)
        if ctl != "applied_only":
            done = 1
    return ("ret", done)


def form_model(t):
    """The model's outcome in the comparable form: ret, or the boundary and its compared arguments."""
    k = t[0]
    if k == "ret":
        return ["ret", t[1] & M32]
    if k == "addstat":
        return ["obs", U.F_ADD, t[1], t[2] & M32]
    if k == "alloc":
        return ["obs", U.F_ALLOC, t[1] & M32]
    if k == "queue":
        return ["obs", U.F_QUEUE, t[1] & M32]
    if k == "setstat":
        return ["obs", U.F_SET, t[1], t[2] & M32]
    if k == "golem":
        return ["obs", U.F_GHEAL, t[1] & M32]
    raise ValueError(k)


def form_got_stat(c, a):
    if c[3] == "STOP":
        return ["stop", c[4]]
    if c[3] != "OBS":
        return ["ret", int(c[3].split("=")[1], 16)]
    pc = int(c[4], 16)
    w = struct.unpack("<16I", a)
    if pc == U.F_ADD:
        return ["obs", pc, w[2], w[3]]
    if pc == U.F_ALLOC:
        return ["obs", pc, w[3]]
    if pc == U.F_QUEUE:
        return ["obs", pc, w[2]]
    if pc == U.F_SET:
        return ["obs", pc, w[2], w[3]]
    if pc == U.F_GHEAL:
        regs = dict(x.split("=") for x in c[6:])
        return ["obs", pc, int(regs["eax"], 16)]
    return ["obs-other", pc]


# ================================================================================================= stackreq
def gen_stackreq(r):
    w = P3.W()
    P3.put_player(w, r)
    P3.put_inv(w)
    c = w.c
    a = dict(cls=7, d0=r.choice((1, 2, 3, 2, 2, 10)), file=5, stackable=1, eth=0, stats={70: r.randrange(1, 40)})
    b = dict(a, stats={70: r.randrange(1, 40)})
    breaks = r.choice(("none",) * 6 + ("cls", "d0", "q0", "q4", "q9", "file", "stackable", "eth", "s21", "s160",
                                       "s194a", "s194b"))
    if breaks == "cls":
        b["cls"] = 8
    elif breaks == "d0":
        b["d0"] = a["d0"] + 1 if a["d0"] != 3 else 2
    elif breaks in ("q0", "q4", "q9"):
        a["d0"] = b["d0"] = int(breaks[1:])
    elif breaks == "file":
        b["file"] = 6
    elif breaks == "stackable":
        a["stackable"] = b["stackable"] = 0
    elif breaks == "eth":
        b["eth"] = 1
    elif breaks in ("s194a", "s194b"):
        (a if breaks == "s194a" else b)["stats"][194] = r.randrange(1, 6)
    elif breaks != "none":
        b["stats"][int(breaks[1:])] = r.randrange(1, 50)
    variant = r.choice(("ok",) * 10 + ("same", "miss1", "miss2", "nonitem1", "nonitem2", "page2", "page2", "pagex",
                                       "first2"))
    gs = P3.guids(r, 3)
    g1, g2 = gs[0], gs[1]
    if variant == "same":
        g2 = g1
    pages = [r.choice((0, 0, 1, 3, 4, 0xFF)), r.choice((0, 0, 1, 3, 4))]
    if variant in ("page2", "pagex"):
        pages[1] = 2 if variant == "page2" else r.choice((1, 3, 4, 5, 0xFE, 0xFF))
    if variant == "first2":
        pages[0] = 2
    addrs = []
    for k, (x, g) in enumerate(((a, g1), (b, g2))):
        if (variant == "miss1" and k == 0) or (variant == "miss2" and k == 1) or (variant == "same" and k == 1):
            addrs.append(0)
            continue
        base = P3.ITEMS[k]
        if k == 0 or b["cls"] == 8:
            IE2.put_rec(c, x["cls"], stackable=x["stackable"])
        IE2.put_item(c, base, base + 0x200, x["cls"], d0=x["d0"], file=x["file"], eth=x["eth"], sl=base + 0x100,
                     stats=x["stats"])
        w.unit(base, 4, g)
        c.d8(base + 0x200 + 0x45, pages[k])
        if variant == "nonitem%d" % (k + 1):
            c.d32(base, 3)                      # a later write wins: hashed with the items, +0 not 4
        addrs.append(base)
    w.finish()
    c.d32(OUTW, 0x55555555)
    c.dump(OUTW, 4)
    m = dict(variant=variant, breaks=breaks, pages=pages, ok=inv.stack_ok(a, b), cls=[a["cls"], b["cls"]],
             addrs=addrs, g=[g1, g2])
    m["want"] = model_stackreq(m)
    m["ctl"] = {k: model_stackreq(m, k) for k in ("same_ok", "page_first", "page_any", "miss_noflag", "nostack_flag",
                                                   "nonitem_flag")}
    return c.call(F_REQ, P3.GAME, P3.PLAYER, g1, g2, OUTW), m


def model_stackreq(m, ctl=None):
    """-> [kind, eax or the merge's arguments, out]."""
    v, p = m["variant"], m["pages"]
    if v == "same" and ctl != "same_ok":
        return ["ret", 0, 1]
    if v == "miss1" or v == "miss2":
        return ["ret", 0, 0 if ctl == "miss_noflag" else 1]
    if v in ("nonitem1", "nonitem2"):
        return ["ret", 0, 1 if ctl == "nonitem_flag" else 0]
    page = p[0] if ctl == "page_first" else p[1]
    if page == 2 or (ctl == "page_any" and page != 0):
        return ["ret", 0, 1]
    if not m["ok"]:
        return ["ret", 0, 1 if ctl == "nostack_flag" else 0]
    if m["cls"][0] != m["cls"][1]:
        return ["ret", 1, 0]
    return ["merge", [P3.GAME, m["addrs"][0], m["addrs"][1], P3.PLAYER], 0]


def form_got_stackreq(r):
    c, d = r["c"], dict(r["d"])
    out = struct.unpack("<I", d[OUTW])[0]
    if c[3] == "STOP":
        return ["stop", c[4], out]
    if c[3] == "OBS":
        a = struct.unpack("<16I", r["a"])
        regs = dict(x.split("=") for x in c[6:])
        if int(c[4], 16) != F_MERGE or a[0] != SITE_MERGE:
            return ["obs-other", c[4], a[0]]
        return ["merge", [a[1], a[2], int(regs["esi"], 16), int(regs["ebx"], 16)], out]
    return ["ret", int(c[3].split("=")[1], 16), out]


# ================================================================================================= commands
GEN = {"golem": lambda r, i: gen_golem(r), "double": gen_double, "potret": gen_potret,
       "stackreq": lambda r, i: gen_stackreq(r)}


def mem_spec(fam):
    out = ["# plan 0066 S4e part 5b (%s)" % fam]
    if fam == "stackreq":
        out += [x for x in IE2.mem_spec("stackok").splitlines() if not x.startswith(("#", "observe"))]
        out += [x for x in P3.mem_spec(fam if fam in P3.OBSERVE else "pos") if not x.startswith(("#", "observe"))]
    else:
        out += [x for x in U.mem_spec("classmul").splitlines() if not x.startswith(("#", "observe"))]
        for lo, n in ZERO_USE:
            out.append("bytes %08x %s" % (lo, "00" * n))
    seen = set()
    res = []
    for x in out:
        if x not in seen:
            seen.add(x)
            res.append(x)
    for g in (0x00408090, 0x00408A60, 0x00681E09, 0x0040B4B0, 0x0040B430, 0x0040B480):
        if ("guard %08x" % g) not in seen:
            res.append("guard %08x" % g)
    res += ["observe %08x" % a for a in OBSERVE[fam]]
    return "\n".join(res) + "\n"


def gen_all(fam, limit=None):
    r = random.Random("n66z-s4e6-%s" % fam)
    blocks, metas = [], []
    for i in range(limit or NCASES[fam]):
        b, m = GEN[fam](r, i)
        blocks.append(b)
        metas.append(m)
    return blocks, metas


def cmd_cases(d, limit=None):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        blocks, metas = gen_all(fam, limit)
        open(os.path.join(d, fam + ".cases"), "w").write("\n".join(blocks) + "\n")
        open(os.path.join(d, fam + ".mem"), "w").write(mem_spec(fam))
        json.dump({"cases": metas}, open(os.path.join(d, fam + ".json"), "w"), sort_keys=True)
        print("%s: %d cases" % (fam, len(metas)))


def form(x):
    return json.dumps(x, sort_keys=True)


def got_of(fam, r):
    c = r["c"]
    if fam == "stackreq":
        return form_got_stackreq(r)
    if fam == "golem":
        if c[3] == "STOP":
            return ["stop", c[4]]
        if c[3] == "OBS":
            a = struct.unpack("<16I", r["a"])
            if int(c[4], 16) != F_SETSTAT:
                return ["obs-other", c[4]]
            return ["set", a[0], a[1], a[2], a[3], a[4]]
        return ["ret", int(c[3].split("=")[1], 16)]
    return form_got_stat(c, r.get("a"))


ACCOUNTED = ((0x006E10E0, 0x006E10F4, "the unit-type hash offsets (.rdata)"),
             (0x005BE74C, 0x005BE7A5, "entry 3's switch tables (.text)"),
             (0x006CE200, 0x006CE300, "the bit masks (.rdata)"),
             (0x00744600, 0x00744700, "the calc function count (.data)"),
             (0x0062A60C, 0x0062A61F, "the life multiplier's switch (.text)"),
             (0x0062A65C, 0x0062A66F, "the mana multiplier's switch (.text)"),
             (0x006C1100, 0x006C1200, "the evaluator's switch (.text)"))


def accounted(kind, pc, addr):
    return kind == "R" and any(lo <= addr < hi for lo, hi, _ in ACCOUNTED + tuple(IE2.ACCOUNTED))


def outcome(fam, m, g):
    if fam == "golem":
        k = "v=0" if m["v"] == 0 else ("v<0" if m["v"] < 0 else "v>0")
        tail = ""
        if g[0] == "set":
            tail = " full" if g[4] == m["mx"] & M32 else " below-max"
        return "%s %s %s %s%s" % (m["fn"], m["kind"], k, g[0], tail)
    if fam == "potret":
        return "%s %s" % (m["mode"], g[0] if g[0] != "obs" else "obs %x" % g[1]) + (" %d" % g[1] if g[0] == "ret" else "")
    if fam == "stackreq":
        return "%s %s out=%d" % (m["variant"] if m["variant"] != "ok" else "ok:" + m["breaks"], g[0], g[-1])
    return g[0]


def doubled(m, g):
    """For a `double` case at the boundary: the amount equals the undoubled scale × 2."""
    u = unit_of(m)
    s, amt = m["s"], m["rec"]["slots"][0][1]
    v = inv.mana_mul(u.type, u.cls, amt) if s == inv.MANA else inv.life_mul(u.type, u.cls, amt)
    return g[0] == "obs" and g[1] == U.F_ADD and g[3] == inv.i32(v * 2) & M32 and v != 0


def cmd_check(d, fams=FAMILIES):
    rc = 0
    for fam in fams:
        p = os.path.join(d, fam + ".out")
        if not os.path.exists(p):
            print("S4E6 %s: no output" % fam)
            rc = 1
            continue
        cases, tail = parse_out(p)
        _, metas = gen_all(fam, len(cases) if len(cases) < NCASES[fam] else None)
        cnt = collections.Counter()
        sep, passed, outs = collections.Counter(), collections.Counter(), collections.Counter()
        bad = []
        if len(cases) != len(metas):
            bad.append("%d outputs for %d cases" % (len(cases), len(metas)))
        for m, r in zip(metas, cases):
            cnt["cases"] += 1
            g = got_of(fam, r)
            cnt["stops"] += g[0] == "stop"
            why = None
            if form(g) != form(m["want"]):
                why = "got %s want %s" % (g, m["want"])
            elif fam in ("double", "potret"):
                why = U.cmp_stat(dict(m, u=dict(m["u"], stats={int(k): v for k, v in m["u"]["stats"].items()})),
                                 r["c"], r.get("a"), r["d"])
            if why:
                bad.append("case %s: %s" % (r["c"][1], why))
                continue
            cnt["match"] += 1
            outs[outcome_line(fam, m, g)] += 1
            if fam == "potret" and m["mode"] not in ("badstate", "norec") and g == ["ret", 0]:
                pos = [cv for st, cv in m["rec"]["slots"] if st >= 0 and cv > 0]
                cnt["ret 0 with a slot whose calc > 0 (its scaled, doubled or shifted amount <= 0)"] += bool(pos)
                cnt["ret 0 with every calc <= 0"] += not pos
            for k, v in m["ctl"].items():
                if form(v) != form(m["want"]):
                    sep[k] += 1
                    passed[k] += form(v) == form(g)
        und = collections.Counter()
        traced = 0
        for kind in ("R", "W"):
            for pc, addr, size, n in tail[kind]:
                traced += 1
                if not accounted(kind, pc, addr):
                    und["%s pc=%06x addr=%08x size=%d" % (kind, pc, addr, size)] += n
        print("S4E6 %s cases=%d match=%d bad=%d stops=%d traced=%d undeclared=%d" % (
            fam, cnt["cases"], cnt["match"], len(bad), cnt["stops"], traced, len(und)))
        for k in sorted(cnt):
            if k not in ("cases", "match", "stops"):
                print("    count %s: %d" % (k, cnt[k]))
        for k in sorted(outs):
            print("    outcome %s: %d" % (k, outs[k]))
        ctls = sorted(set(k for m in metas for k in m["ctl"]))
        for k in ctls:
            print("    control %s: sep=%d passed=%d" % (k, sep[k], passed[k]))
            if passed[k] or not sep[k]:
                bad.append("control %s sep=%d passed=%d" % (k, sep[k], passed[k]))
        for u in sorted(und)[:20]:
            print("    UNDECLARED %s x%d" % (u, und[u]))
        for b in bad[:12]:
            print("    BAD " + b)
        if fam == "double":
            double_report(metas)
        rc |= 1 if (bad or und) else 0
    print("S4E6 %s" % ("OK" if rc == 0 else "FAILED"))
    return rc


def outcome_line(fam, m, g):
    if fam == "double":
        if g[0] != "obs":
            return "ret %d" % g[1]
        if not m["n"] or m["n"] <= 0:
            return "type %d, n %d: no draw, %s" % (m["u"]["type"], m["n"] or 0, "doubled" if doubled(m, g) else "not doubled")
        h = m["r1"] >> 1
        rel = "r2 < r1>>1" if m["r2"] < h else ("r2 = r1>>1" if m["r2"] == h else "r2 > r1>>1")
        return "type %d, %s: %s" % (m["u"]["type"], rel, "doubled" if doubled(m, g) else "not doubled")
    return outcome(fam, m, g)


def double_report(metas):
    """The chance for the spec's n: Σ min(100, r >> 1) ÷ (100 n), from the per-draw rule the cases hold."""
    for n in (10, 25, 50, 100, 150, 165, 200, 500):
        num, den = inv.double_chance(n)
        print("    chance n=%d: %d/%d = %.2f %%" % (n, num, den, 100.0 * num / den))
    ns = collections.Counter(m["n"] for m in metas if m["n"] and m["n"] > 0)
    print("    distinct n with draws: %d; r1 >> 1 >= 100 cases: %d" % (
        len(ns), sum(1 for m in metas if m["r1"] is not None and (m["r1"] >> 1) >= 100)))


PINS = [  # (va, mnemonic, operand substring)
    (0x005C5F13, "test", "edi,edi"), (0x005C5F15, "jg", "0x5c5f1b"), (0x005C5F30, "cmp", "esi,eax"),
    (0x005C5F32, "jle", "0x5c5f3c"), (0x005C68AA, "test", "esi,esi"), (0x005C68AC, "je", "0x5c68f0"),
    (0x005C68F1, "call", "0x625d10"), (0x005C68FC, "call", "0x627260"), (0x005C6901, "mov", "eax,esi"),
    (0x005C68E1, "call", "0x5c5f10"), (0x005C68E6, "sub", "esi,eax"), (0x005C5F47, "pop", "esi"),
    (0x005C5F48, "mov", "eax,edi"),
    (0x0055E819, "cmp", "eax,DWORD PTR [ebp+0xc]"), (0x0055E88E, "cmp", "al,0x2"), (0x0055E894, "call", "0x62c850"),
    (0x0055E8A3, "cmp", "eax,ecx"), (0x0055E8AC, "call", "0x55e590"), (0x0062C873, "cmp", "ecx,eax"),
    (0x0062C875, "je", "0x62c87f"),
    (0x0055E623, "call", "0x627260"), (0x0055E63E, "call", "0x5531c0"), (0x0055E647, "call", "0x53d130"),
    (0x0053D200, "call", "0x53b280"), (0x0053B2A4, "cmp", "ecx,0x200"), (0x0053B2B0, "mov", "esi,DWORD PTR [edi+0x1c0]"),
    (0x0053B2DD, "call", "0x40b430"),
    (0x005BE6D4, "mov", "DWORD PTR [ebp-0x20],0x1"), (0x005BE73D, "mov", "eax,DWORD PTR [ebp-0x20]"),
]


def cmd_static():
    ok = 0
    for va, mn, sub in PINS:
        out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % va,
                              "--stop-address=0x%x" % (va + 16), EXE], capture_output=True, text=True).stdout
        line = [ln for ln in out.splitlines() if ln.strip().startswith("%x:" % va)]
        txt = line[0].split(":", 1)[1].strip() if line else ""
        good = bool(line) and txt.startswith(mn) and sub in txt
        ok += good
        print("  %s 0x%08X %s" % ("ok " if good else "BAD", va, txt))
    print("S4E6 static pins=%d ok=%d" % (len(PINS), ok))
    return 0 if ok == len(PINS) else 1


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["cases", "check", "static", "manifest"])
    ap.add_argument("--dir", default=DEFDIR)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--fam", action="append")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "cases":
        cmd_cases(a.dir, a.limit)
        return 0
    if a.cmd == "check":
        return cmd_check(a.dir, tuple(a.fam) if a.fam else FAMILIES)
    if a.cmd == "static":
        return cmd_static()
    return P3.cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

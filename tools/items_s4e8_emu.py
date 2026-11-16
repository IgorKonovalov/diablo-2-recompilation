#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S4e part 5d (`lane/n66z`): ItemAutoEquipSlot and STATLIST_AddStat's add and removal, run on
the pinned Game.exe under Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java and
compared with the models below; `sites`, the static route read (ADR-0029, ruling R2); `static`, the objdump pins of
the static (c) remainders; `xref`, the full direct-call and argument scans those remainders rest on. Parts 1 to 5c
(tools/stats_s4e_emu.py, items_s4e_emu.py to items_s4e7_emu.py, run/ to run7/) stay unchanged; the world here is
declared from scratch.

    python3 -I tools/items_s4e8_emu.py cases [--dir D] [--limit N]   write D/<family>.cases, .mem, .json
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/items_s4e8_emu.py check [--dir D]               compare, account every traced access, controls
    python3 -I tools/items_s4e8_emu.py static                        objdump pins
    python3 -I tools/items_s4e8_emu.py sites                         the routes: first allocator or import per call
    python3 -I tools/items_s4e8_emu.py xref                          the scans of the static remainders
    python3 -I tools/items_s4e8_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66z/s4e/run8. Every draw comes from random.Random("n66z-s4e8-<family>").

Families (function, convention; boundaries; rows):
  auto   sub_0055D710_ItemAutoEquipSlot (ECX user, EDX item; &loc, skipReq): with skipReq non-zero to the return, every
         callee emulated (ItemTypeBodyByte, ITEMS_CheckFlags, ItemNotDisabled, ITEMS_GetBaseType, InvGetBodyLocItem
         with InvPageGet on a declared body page, ItemTypeQuiver, ItemTypeShoots, ITEMS_UnitIsType, ItemBodyLocs,
         EquipPairFlags with ItemTypeTwoHanded, ItemTypeThrowable and UnitGetStat, EquipPairCompatible); with skipReq 0
         to ItemReqCheck 0x0062EAF0 (observed).                                                 items/inventory 67
  addst  STATLIST_AddStat 0x00627030 (list, stat, add, param; stdcall) on a plain list with no parent (or flag 0x2000):
         to the return, STATLIST_InsertEntry 0x00624C80 or the pool's resize 0x0040B4B0 inside STATLIST_RemoveEntry
         (observed); FindIndex, RemoveEntry with the CRT memmove and STATLIST_Propagate emulated.   stats/aggregate 11

Controls: each a wrong reading (the spec's where it differs); `sep` counts the cases a control's prediction differs
from the model's, `passed` those where the emulator still equals the control (must be 0 when sep > 0).
Stdlib only, plus objdump for `static`, `sites` and `xref`.
"""
import argparse
import bisect
import collections
import csv
import json
import os
import random
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sweep_s1e as E  # noqa: E402
import sweep_s4b as S4  # noqa: E402
import items_s4e3_emu as P3  # noqa: E402
import items_s4e7_emu as P7  # noqa: E402
from use_emu import Case, le32  # noqa: E402
from anim_s6f_emu import read_out  # noqa: E402

M32 = 0xFFFFFFFF
DEFDIR = os.path.join(ROOT, "workspace", "logs", "n66z", "s4e", "run8")
FAMILIES = ("auto", "addst")
NCASES = {"auto": 6000, "addst": 2500}
F_FATAL = 0x00408090
GUARDS_ALL = (0x00408A60, 0x00681E09, 0x0040B4B0, 0x0040B430, 0x0040B480)


def s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def s32(v):
    v &= M32
    return v - 0x100000000 if v & 0x80000000 else v


# ---------------------------------------------------------------------------------------------------------- auto
F_AUTO, F_REQ = 0x0055D710, 0x0062EAF0
DTBL, TYPES, BITS, RECS = 0x24000000, 0x24010000, 0x24014000, 0x24020000
USER, INVB, PAGES, BODYC = 0x24040000, 0x24040400, 0x24040800, 0x24040C00
ITEM, IDATA, OTH, LOC = 0x24050000, 0x24050200, 0x24060000, 0x24070000
NTY, BSTRIDE, NREC = 70, 3, 24
AUTO_ZERO = [(DTBL, 0x1000), (TYPES, 0x4000), (BITS, 0x1000), (RECS, 0x2800), (USER, 0x1000), (ITEM, 0x400),
             (OTH, 0x3400), (LOC, 0x10)]
SIG = 0x01020304
# ItemTypes rows the code names: 5 bow quiver, 6 crossbow quiver, 10, 27 bow, 35 crossbow, 38, 45, 51, 67
NAMED = (5, 6, 10, 27, 35, 38, 45, 51, 67)
SKIP_PATH_RET = 0x0055D7A1


class AW:
    """The declared world of one auto case."""

    def __init__(self):
        self.c = Case()
        self.types = {}          # t -> dict(body, b1, b2, shoots, quiver, throw)
        self.bits = {}           # t -> set of types t is
        self.recs = {}           # row -> dict(t, t2, two)
        self.units = {}          # addr -> dict(type, file, flags)
        self.inv = None

    def is_type(self, it, T):
        """ITEMS_UnitIsType 0x00629BB0 (item, T): the record's type's bit T, else the second type's."""
        if not it:
            return 0
        if T < 0 or T >= NTY:
            return 0
        r = self.recs[self.units[it]["file"]]
        if T in self.bits.get(r["t"], ()):
            return 1
        t2 = r["t2"]
        if t2 <= 0 or t2 >= NTY:
            return 0
        return int(T in self.bits.get(t2, ()))

    def base(self, it):
        u = self.units[it]
        if u["type"] != 4:
            return 0
        return self.recs[u["file"]]["t"]

    def trow(self, t):
        return self.types.get(t) if 0 <= t < NTY else None

    def bodylocs(self, it):
        if not it or self.units[it]["type"] != 4:
            return 0, 0
        tr = self.trow(self.base(it))
        return (tr["b1"], tr["b2"]) if tr else (0, 0)

    def body(self, s):
        """InvGetBodyLocItem 0x0063BDE0 (inventory, slot): 0 for a null or unsigned inventory or a slot above 12; page 0
        by InvPageGet with the 13 x 1 row, 0 on a size mismatch."""
        v = self.inv
        if not v or v["sig"] != SIG or (s & M32) > 12:
            return 0
        if v["size"] != (13, 1):
            return 0
        return v["cells"][s]

    def pairflags(self, user, it, ctl=None):
        u = self.units[user]
        f = [0] * 10
        f[0], f[1], f[2], f[3] = (self.is_type(it, 27), self.is_type(it, 35), self.is_type(it, 5), self.is_type(it, 6))
        f[4], f[5] = self.is_type(it, 51), self.is_type(it, 45)
        iu = self.units[it]
        f[6] = self.recs[iu["file"]]["two"] if iu["type"] == 4 else 0
        if ctl == "no2h":
            f[6] = 0
        if u["type"] == 0 and u["cls"] == 4 or u["type"] == 0 and u["cls"] == 6 and self.is_type(it, 67):
            f[7] = 1
        if ctl == "classall":
            f[7] = 1
        f[9] = self.is_type(it, 10)
        return f


def compat(B, A, ctl=None):
    """EquipPairCompatible 0x0055D670 (ECX the worn item's flags B, EAX the new item's A)."""
    if A[0] and B[2] or A[2] and B[0]:
        return 1
    if A[1] and B[3] or A[3] and B[1]:
        return 1
    if A[5] and not A[6] and B[4]:
        return 1
    if B[5] and not B[6] and A[4]:
        return 1
    if A[5] and not A[6] and B[5] and not B[6] and A[7] and B[7]:
        return 1
    if A[9] and B[9] and ctl != "no10":
        return 1
    return 0


def model_auto(w, m, ctl=None):
    """-> ["ret", eax, loc or None] or ["obs", ...]; m: the case's inputs."""
    user, it, skip = USER, ITEM, m["skip"]
    if ctl == "reqinv":
        skip = not skip
    if not skip:
        return ["obs", F_REQ, SKIP_PATH_RET, {}, [it, user, 0, 0, 0, 0]]
    zero = ["ret", 0, None]
    tr = w.trow(w.base(it))
    b1, b2 = w.bodylocs(it)
    if ctl != "nobodybyte":
        if not (b1 or b2) or not tr or not tr["body"]:
            return zero
    if ctl != "noflag10" and not w.units[it]["flags"] & 0x10:
        return zero
    if ctl != "nodisabled" and w.units[it]["flags"] & 0x4100:
        return zero
    if ctl != "no38" and w.base(it) == 38:
        return zero
    l4, l5 = w.body(4), w.body(5)
    q = tr["quiver"] if tr else 0
    if q and ctl != "noquiver":
        ok = 0
        for h in (l4, l5):
            if h:
                ht = w.trow(w.base(h))
                sh = ht["shoots"] if ht and w.units[h]["type"] == 4 else 0
                if w.is_type(it, sh):
                    ok = 1
                    break
                if ctl == "firsthand":
                    break
        if not ok:
            return zero
    if b1 == b2:
        if w.body(b1) and ctl != "nooccupied":
            return zero
        return ["ret", 1, b1]
    A = w.pairflags(user, it, ctl)
    x1, x2 = w.body(b1), w.body(b2)
    if ctl == "bigslot" and (b1 > 12 or b2 > 12):
        return zero                                       # a slot above 12 read as taken
    if not x1:
        if not x2:
            return ["ret", 1, b2 if ctl == "secondfirst" else b1]
        if ctl == "nocompat" or compat(w.pairflags(user, x2, ctl), A, ctl):
            return ["ret", 1, b1]
        return zero
    if x2:
        return zero
    if ctl == "nocompat" or compat(w.pairflags(user, x1, ctl), A, ctl):
        return ["ret", 1, b2]
    return zero


AUTO_CTLS = ("reqinv", "nobodybyte", "noflag10", "nodisabled", "no38", "noquiver", "firsthand", "nooccupied",
             "secondfirst", "nocompat", "no2h", "classall", "no10", "bigslot")


def gen_auto(r, i):
    w = AW()
    c = w.c
    # ItemTypes: every row random; the named rows favoured as an item's type
    for t in range(NTY):
        b1 = r.choice([0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 4, 5, 7, 8])
        b2 = b1 if r.random() < 0.45 else r.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 4, 5, 7, 8])
        tr = dict(body=r.choice([0, 1, 1, 1, 1, 1, 1, 2, r.randrange(256)]), b1=b1, b2=b2,
                  shoots=r.choice([0, -1, 5, 6, r.randrange(NTY), r.randrange(NTY), NTY + r.randrange(40)]) if
                  r.random() < 0.7 else 0,
                  quiver=r.choice([0, 0, 0, 0, 0, 5, 6, r.randrange(1, NTY), -3]), throw=r.choice([0, 0, 1]))
        if t in (10, 27, 35, 45, 51, 67) and r.random() < 0.6:   # the hands, as the stock weapons and shields
            tr["b1"], tr["b2"] = b1, b2 = 4, 5
        if t in (27, 35) and r.random() < 0.7:          # the bows shoot their quivers
            tr["shoots"] = 5 if t == 27 else 6
        if t in (5, 6) and r.random() < 0.7:
            tr["quiver"] = 27 if t == 5 else 35
        w.types[t] = tr
        a = TYPES + t * 0xE4
        c.d8(a + 9, tr["body"])
        c.d8(a + 0xA, b1)
        c.d8(a + 0xB, b2)
        c.d16(a + 0xC, tr["shoots"] & 0xFFFF)
        c.d16(a + 0xE, tr["quiver"] & 0xFFFF)
        c.d8(a + 0x10, tr["throw"])
        bs = set()
        bs.add(t)
        for _ in range(r.choice([0, 1, 2, 3])):
            bs.add(r.choice(NAMED) if r.random() < 0.8 else r.randrange(NTY))
        w.bits[t] = bs
        words = [0] * BSTRIDE
        for b in bs:
            words[b >> 5] |= 1 << (b & 31)
        c.put(BITS + 4 * BSTRIDE * t, b"".join(le32(x) for x in words))
    for k in range(NREC):
        t = r.choice(NAMED) if r.random() < 0.6 else r.randrange(NTY)
        if k >= NREC - 3:                                   # rows only the item under test takes
            t = r.choice([-1, NTY, NTY + 5, 0x7FFF])
        t2 = r.choice([0, 0, 0, -1, r.randrange(NTY), r.choice(NAMED), NTY + 2])
        w.recs[k] = dict(t=t, t2=t2, two=r.choice([0, 0, 1]))
        a = RECS + k * 0x1A8
        c.d8(a + 0x11C, w.recs[k]["two"])
        c.d16(a + 0x11E, t & 0xFFFF)
        c.d16(a + 0x120, t2 & 0xFFFF)

    def pick(ts):
        ks = [k for k in range(NREC - 3) if w.recs[k]["t"] in ts]
        return r.choice(ks) if ks else r.randrange(NREC - 3)

    def put_item(addr, typ=4, bad=False, hand=False, favour=None):
        file = r.randrange(NREC - 3, NREC) if bad else r.randrange(NREC - 3)
        if hand and r.random() < 0.5:
            file = pick((27, 35) if r.random() < 0.6 else (45, 51))
        if favour:
            file = pick(favour)
        fl = r.choice([0x10] * 12 + [0, 0x110, 0x4010, r.getrandbits(32)])
        w.units[addr] = dict(type=typ, file=file, flags=fl)
        c.d32(addr, typ)
        c.d32(addr + 4, file)
        c.d32(addr + 0x14, addr + 0x200)
        c.d32(addr + 0x200 + 0x18, fl)
        c.d32(addr + 0x5C, 0)
        return addr

    scen = r.choices([None, (5, 6), (45,)], [0.6, 0.2, 0.2])[0]       # ammunition, one-handed weapons
    put_item(ITEM, bad=r.random() < 0.04, favour=scen)
    utype = r.choice([0, 0, 0, 0, 1, 2, 3])
    ucls = r.choice([0, 1, 2, 3, 4, 4, 5, 6, 6, r.randrange(8)])
    w.units[USER] = dict(type=utype, cls=ucls)
    c.d32(USER, utype)
    c.d32(USER + 4, ucls)
    inv_kind = r.choices(["ok", "null", "sig", "size"], [0.9, 0.03, 0.03, 0.04])[0]
    if inv_kind == "null":
        c.d32(USER + 0x60, 0)
    else:
        c.d32(USER + 0x60, INVB)
        size = (13, 1) if inv_kind != "size" else r.choice([(12, 1), (13, 2), (1, 13)])
        sig = SIG if inv_kind != "sig" else SIG ^ (1 << r.randrange(32))
        cells = [0] * 13
        for s in range(13):
            if r.random() < r.choice([0.05, 0.15, 0.4, 0.7]):
                cells[s] = put_item(OTH + 0x400 * s, hand=s in (4, 5))
        w.inv = dict(sig=sig, size=size, cells=cells)
        c.d32(INVB, sig)
        c.d32(INVB + 0x14, PAGES)
        c.d32(INVB + 0x18, r.randrange(1, 9))
        c.d8(PAGES + 8, size[0])
        c.d8(PAGES + 9, size[1])
        c.d32(PAGES + 0xC, BODYC)
        c.put(BODYC, b"".join(le32(x) for x in cells))
    skip = r.random() < 0.88
    sk = r.choice([1, 1, 1, 2, 0x80000000, r.getrandbits(32) | 1]) if skip else 0
    c.d32(LOC, 0xA5A5A5A5)
    c.dump(LOC, 4)
    m = dict(skip=int(skip))
    line = c.call(F_AUTO, USER, ITEM, LOC, sk)
    want = model_auto(w, m)
    ctl = {k: model_auto(w, m, k) for k in AUTO_CTLS}
    br = []
    if want[0] == "ret":
        br.append("ret%d" % want[1])
        if want[1]:
            b1, b2 = w.bodylocs(ITEM)
            br.append("same" if b1 == b2 else ("loc1" if want[2] == b1 else "loc2"))
            if w.trow(w.base(ITEM))["quiver"]:
                br.append("ammo_ok")
    else:
        br.append("req")
    m.update(want=want, ctl=ctl, br=br)
    return line, m


# ---------------------------------------------------------------------------------------------------------- addst
F_ADD, F_INSERT, F_POOL = 0x00627030, 0x00624C80, 0x0040B4B0
SDTBL, SISC, LIST, ARR = 0x25000000, 0x25010000, 0x25040000, 0x25050000
NISC = 300
ADD_ZERO = [(SDTBL, 0x1000), (SISC, NISC * 0x144), (LIST, 0x100), (ARR, 0x200)]


def model_addst(m, ctl=None):
    """-> (want, final entries or None). m: list (0 or LIST), ent [(key, value)], cap, stat, add, param."""
    if not m["list"] or m["add"] == 0 and ctl != "zeroadd":
        return ["ret"], m["ent"]
    key = ((m["stat"] << 16) + (m["param"] & 0xFFFF)) & M32
    if ctl == "keyswap":
        key = ((m["param"] & 0xFFFF) << 16) + (m["stat"] & 0xFFFF)
    keys = [k for k, _ in m["ent"]]
    sk = [s32(k) for k in keys]
    i = bisect.bisect_left(sk, s32(key))
    if i >= len(sk) or sk[i] != s32(key):
        return ["obs", F_INSERT, 0x00627070, {"eax": key}, [0x7E570000]], None
    ent = [list(e) for e in m["ent"]]
    v = (ent[i][1] + m["add"]) & M32 if ctl != "set" else m["add"] & M32
    ent[i][1] = v
    if v == 0 and ctl != "noremove":
        del ent[i]
        n, cap = len(ent), m["cap"]
        if cap - n > (4 if ctl == "shrink4" else 8):
            return ["obs", F_POOL, 0x00624D83, {"edx": ARR}, [(cap - 4) * 8, 0x006E90A4, 0x110, 0]], None
    return ["ret"], [tuple(e) for e in ent]


ADD_CTLS = ("zeroadd", "keyswap", "set", "noremove", "shrink4")


def gen_addst(r, i):
    c = Case()
    n = r.choice([0, 1, 2, 3, 5, 8, 12, r.randrange(20)])
    cap = n + r.choice([0, 0, 1, 2, 4, 6, 8, 9, 10, 12])
    stats = sorted(r.sample(range(0, NISC + 40), n))
    ent = [((s << 16) + r.choice([0, 0, 0, 1, r.randrange(0x10000)]), r.choice([1, 5, -3, 100, r.getrandbits(32)]) & M32)
           for s in stats]
    ent.sort(key=lambda e: s32(e[0]))
    ent = [e for k, e in enumerate(ent) if k == 0 or ent[k - 1][0] != e[0]]
    n = len(ent)
    lst = LIST if r.random() < 0.96 else 0
    if ent and r.random() < 0.8:
        k, v = r.choice(ent)
        stat, param = k >> 16, k & 0xFFFF
        if r.random() < 0.15:
            param |= r.randrange(1, 0x8000) << 16           # the param's high half: dropped by the u16 load
        add = (-s32(v)) & M32 if r.random() < 0.55 else r.choice([1, -1, 7, r.getrandbits(32)]) & M32
    else:
        stat, param = r.randrange(0, NISC + 40), r.choice([0, 1, r.randrange(0x10000)])
        add = r.choice([1, -1, 9, r.getrandbits(32)]) & M32
    if r.random() < 0.05:
        add = 0
    flags = r.choice([0, 0, 0x2000, 0x40, 0x2040])
    pool = 0x7E570000
    c.d32(LIST, pool)
    c.d32(LIST + 8, 0)
    c.d32(LIST + 0x10, flags)
    c.d32(LIST + 0x24, ARR)
    c.d16(LIST + 0x28, n)
    c.d16(LIST + 0x2A, cap)
    c.d32(LIST + 0x34, 0)
    body = b"".join(le32(k) + le32(v) for k, v in ent) + b"\xEE" * (8 * (cap - n))
    if body:
        c.put(ARR, body)
    for s in (stat & 0xFFFF,):
        if s < NISC:
            c.d8(SISC + s * 0x144 + 4, r.getrandbits(8))
            c.d8(SISC + s * 0x144 + 0x51, 0)
            c.d8(SISC + s * 0x144 + 0x52, 0)
    c.dump(LIST + 0x24, 8)
    c.dump(ARR, 8 * max(cap, 1))
    m = dict(list=lst, ent=ent, cap=cap, stat=stat, add=add, param=param, flags=flags)
    line = c.call(F_ADD, 0, 0, lst, stat, add, param)
    want, fin = model_addst(m)
    ctl = {}
    for k in ADD_CTLS:
        cw, cf = model_addst(m, k)
        ctl[k] = [cw, cf]
    br = [want[0] if want[0] == "ret" else "obs%08X" % want[1]]
    if want[0] == "ret" and fin is not None and lst and add and len(fin) < n:
        br.append("removed")
    m.update(want=[want, fin], ctl=ctl, br=br)
    return line, m


# ---------------------------------------------------------------------------------------------------------- cases
GEN = {"auto": gen_auto, "addst": gen_addst}
OBSERVE = {"auto": (F_REQ,), "addst": (F_INSERT, F_POOL)}


def mem_spec(fam):
    if fam == "auto":
        out = ["# plan 0066 S4e part 5d (auto): scratch tables, zero-filled before every case"]
        for lo, n in AUTO_ZERO:
            out.append("bytes %08x %s" % (lo, "00" * n))
        out += ["dword 00744304 %08x" % DTBL, "dword %08x %08x" % (DTBL + 0xBF8, TYPES),
                "dword %08x %08x" % (DTBL + 0xBFC, NTY), "dword %08x %08x" % (DTBL + 0xC00, BSTRIDE),
                "dword %08x %08x" % (DTBL + 0xC04, BITS), "dword 0096ca58 %08x" % NREC, "dword 0096ca5c %08x" % RECS]
    else:
        out = ["# plan 0066 S4e part 5d (addst): a plain list, its array and the ItemStatCost rows, zero-filled"]
        for lo, n in ADD_ZERO:
            out.append("bytes %08x %s" % (lo, "00" * n))
        out += ["dword 00744304 %08x" % SDTBL, "dword %08x %08x" % (SDTBL + 0xBCC, SISC),
                "dword %08x %08x" % (SDTBL + 0xBD4, NISC)]
    out += ["guard %08x" % g for g in GUARDS_ALL if g not in OBSERVE[fam]]
    out += ["observe %08x" % a for a in OBSERVE[fam] + (F_FATAL,)]
    return out


def cmd_cases(d, limit=None):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        r = random.Random("n66z-s4e8-%s" % fam)
        cases, meta = [], []
        for i in range(limit or NCASES[fam]):
            line, m = GEN[fam](r, i)
            cases.append(line)
            meta.append(m)
        E.write_family(d, fam, cases, mem_spec(fam), {"cases": meta})
        print("%s: %d cases" % (fam, len(meta)))


# ---------------------------------------------------------------------------------------------------------- check
def got_of(c):
    if "stop" in c:
        return ["stop", "%08X" % c["stop"], c.get("msg")]
    if "obs" not in c:
        return ["ret", c.get("eax")]
    return ["obs", c["obs"], c["args"][0]]


def judge_obs(c, want):
    g = got_of(c)
    if g[0] != "obs" or c["obs"] != want[1] or c["args"][0] != want[2]:
        return False, g
    if any(c["regs"].get(k) != v for k, v in want[3].items()):
        return False, g + [c["regs"]]
    for k, v in enumerate(want[4]):
        if v is not None and c["args"][1 + k] != v & M32:
            return False, g + [list(c["args"][1:1 + len(want[4])])]
    return True, g


def judge(fam, c, want):
    if fam == "auto":
        if want[0] == "obs":
            return judge_obs(c, want)
        g = got_of(c)
        if g[0] != "ret" or g[1] != want[1]:
            return False, g
        loc = c["dumps"].get(LOC, b"")
        lv = struct.unpack("<I", loc)[0] if len(loc) == 4 else None
        exp = 0xA5A5A5A5 if want[2] is None else want[2]
        return lv == exp, g + [lv]
    w, fin = want
    if w[0] == "obs":
        return judge_obs(c, w)
    g = got_of(c)
    if g[0] != "ret":
        return False, g
    hdr = c["dumps"].get(LIST + 0x24, b"")
    arr = c["dumps"].get(ARR, b"")
    if len(hdr) != 8:
        return False, g + ["no header"]
    n = struct.unpack("<h", hdr[4:6])[0]
    got = [struct.unpack("<II", arr[8 * k:8 * k + 8]) for k in range(n)] if 0 <= n and 8 * n <= len(arr) else None
    return got == [tuple(e) for e in fin], g + [n]


def form(x):
    return json.dumps(x, sort_keys=True)


RS = [(0x00744304, 0x00744308, "r", "the DataTables pointer (.data, declared)"),
      (0x0096CA58, 0x0096CA60, "r", "the Items count and rows (.data, declared)"),
      (0x0074479C, 0x0074479E, "r", "the body page's 13 x 1 row (.data)"),
      (0x006CE200, 0x006CE300, "r", "the bit masks (.rdata)"),
      (0x00749DE0, 0x00749DE4, "r", "the stack cookie (.data)"),
      (0x00683840, 0x00683C00, "r", "the CRT memmove 0x00683840's own jump tables (.text)")]


def declared():
    return list(RS)


class Report(E.Report):
    def line(self):
        keys = ["cases", "match", "bad", "neg", "traced", "undeclared", "stopped"]
        rest = sorted(k for k in self.c if k not in keys)
        return "S4E8 %s " % self.fam + " ".join("%s=%d" % (k, self.c[k]) for k in keys + rest)


def cmd_check(d, fams=FAMILIES):
    rc = 0
    for fam in fams:
        p = os.path.join(d, fam + ".out")
        if not os.path.exists(p):
            print("S4E8 %s: no output" % fam)
            rc = 1
            continue
        calls, reads, writes = read_out(p)
        meta = json.load(open(os.path.join(d, fam + ".json")))["cases"]
        rep = Report(fam)
        sep, passed, outs = collections.Counter(), collections.Counter(), collections.Counter()
        if len(calls) != len(meta):
            rep.bad("%d calls for %d cases" % (len(calls), len(meta)))
        for c, a in zip(calls, meta):
            rep.c["cases"] += 1
            if "stop" in c:
                rep.c["stopped"] += 1
                rep.bad("case %d stopped at %08X: %s" % (c["n"], c["stop"], c.get("msg")))
                continue
            ok, got = judge(fam, c, a["want"])
            rep.c["match"] += ok
            if not ok:
                rep.bad("case %d: got %s want %s" % (c["n"], got, a["want"]))
                continue
            rep.branches.update(a["br"])
            w = a["want"] if fam == "auto" else a["want"][0]
            outs[form(w[:3] if w[0] == "ret" else w[:2])] += 1
            for k, v in a["ctl"].items():
                if form(v) != form(a["want"]):
                    sep[k] += 1
                    passed[k] += judge(fam, c, v)[0]
        E.account(rep, reads, writes, declared())
        for k in sorted(outs):
            rep.notes.append("  outcome %s: %d" % (k, outs[k]))
        for k in sorted(set(k for a in meta for k in a["ctl"])):
            rep.notes.append("  control %s: sep=%d passed=%d" % (k, sep[k], passed[k]))
            if passed[k] or not sep[k]:
                rep.bad("control %s sep=%d passed=%d" % (k, sep[k], passed[k]))
        rc |= E.finish(rep, sum(sep.values()))
    return rc


# ---------------------------------------------------------------------------------------------------------- static
PINS = [  # (va, mnemonic, operand substring)
    # ItemAutoEquipSlot: skipReq, the first half's tests, the hands, the tail
    (0x0055D74D, "cmp", "DWORD PTR [ebp+0xc],0x0"), (0x0055D79C, "call", "0x62eaf0"), (0x0055D754, "call", "0x62fdf0"),
    (0x0055D767, "push", "0x10"), (0x0055D783, "cmp", "eax,0x26"), (0x0055D7A6, "call", "0x62fdf0"),
    (0x0055D7B9, "push", "0x10"), (0x0055D7D5, "cmp", "eax,0x26"), (0x0055D7DE, "push", "0x4"),
    (0x0055D7E6, "push", "0x5"), (0x0055D7FA, "call", "0x628480"), (0x0055D841, "cmp", "al,BYTE PTR [ebp-0x1]"),
    (0x0055D871, "call", "0x55d560"), (0x0055D8CC, "call", "0x55d670"), (0x0055D8FE, "call", "0x55d670"),
    (0x0063BE00, "cmp", "esi,0xc"), (0x0063BE05, "push", "0x74479c"),
    # STATLIST_AddStat: the key, the add, the removal at 0
    (0x0062704A, "shl", "edi,0x10"), (0x00627073, "add", "DWORD PTR [eax+0x4],ecx"), (0x00627076, "jne", "0x627082"),
    (0x0062707D, "call", "0x624d10"), (0x00624D57, "cmp", "edx,0x8"), (0x00624D7E, "call", "0x40b4b0"),
]
PINS_STATIC = [   # the static (c) remainders' pins, by row
    ("aggregate 13: StatListLinkOwner 0x00627910", [
        (0x00627924, "mov", "esi,DWORD PTR [edi+0x5c]"), (0x0062792B, "cmp", "DWORD PTR [edi],0x4"),
        (0x00627931, "call", "0x627d40"), (0x00627D56, "mov", "al,BYTE PTR [eax+0x44]"), (0x00627936, "cmp", "al,0xb"),
        (0x0062793A, "cmp", "al,0xc"), (0x0062793F, "call", "0x6269f0"), (0x0062794B, "cmp", "DWORD PTR [esi+0x4],ebx"),
        (0x00627950, "cmp", "DWORD PTR [ebp+0x10],0x0"), (0x00627956, "test", "DWORD PTR [esi+0x10],0x40000000"),
        (0x00627961, "call", "0x627860"), (0x0062796D, "test", "DWORD PTR [esi+0x10],0x40000000"),
        (0x00627978, "call", "0x627a40"), (0x0062798A, "call", "0x626e10"), (0x0062798F, "mov", "DWORD PTR [esi+0x4],ebx")]),
    ("aggregate 37: the set lookup 0x00663BC1..0x00663C3B", [
        (0x00663BC4, "mov", "edi,DWORD PTR [edx*4+0x6ee424]"), (0x00663BCD, "call", "0x6256b0"),
        (0x00663BDA, "push", "0x47"), (0x00663BDD, "call", "0x625d00"), (0x00625D04, "jmp", "0x625350"),
        (0x0062539A, "call", "0x624ed0"), (0x00663BE2, "cmp", "DWORD PTR [ebp-0xc],eax"), (0x00663C35, "cmp", "eax,0x6"),
        (0x00663C90, "push", "0x47"), (0x00663C93, "call", "0x627030")]),
    ("aggregate 17: PLAYER_SpendStatPoint 0x00570D60 and its energy and vitality adds", [
        (0x00570D66, "push", "0x4"), (0x00570D6B, "call", "0x625480"), (0x00570D79, "jmp", "DWORD PTR [edi*4+0x570df8]"),
        (0x00570DA6, "mov", "eax,0x1"), (0x00570DAB, "call", "0x570a80"), (0x00570DDE, "mov", "eax,0x1"),
        (0x00570DE3, "call", "0x570b60"), (0x00570AA4, "cmp", "eax,DWORD PTR [ecx+0xbc8]"),
        (0x00570AAC, "imul", "eax,eax,0xc4"), (0x00570AB2, "add", "eax,DWORD PTR [ecx+0xbc4]"),
        (0x00570AC4, "push", "0x4"), (0x00570ACF, "push", "0x1"), (0x00570AD9, "jle", "0x570af0"),
        (0x00570ADB, "movzx", "ecx,BYTE PTR [ebx+0x48]"), (0x00570AE4, "shl", "ecx,0x6"), (0x00570AE8, "push", "0x8"),
        (0x00570AF9, "shl", "edx,0x6"), (0x00570AFD, "push", "0x9"), (0x00570B1B, "cmp", "eax,edi"),
        (0x00570B25, "call", "0x627260"), (0x00570BBB, "push", "0x3"), (0x00570BC3, "movzx", "ecx,BYTE PTR [ebx+0x46]"),
        (0x00570BD0, "push", "0x7"), (0x00570BDA, "jle", "0x570bf1"), (0x00570BE9, "push", "0x6"),
        (0x00570C15, "call", "0x627260"), (0x00570C1A, "movzx", "eax,BYTE PTR [ebx+0x47]"), (0x00570C27, "push", "0xb"),
        (0x00570C31, "jle", "0x570c48"), (0x00570C40, "push", "0xa")]),
    ("aggregate 23: MonStatCallback 0x0055B800's event registration and its 107 test", [
        (0x0055B867, "cmp", "WORD PTR [ebx+0x48],0x0"), (0x0055B86E, "cmp", "DWORD PTR [ebp+0x14],0x0"),
        (0x0055B87A, "call", "0x5c0be0"), (0x0055B883, "movsx", "ecx,WORD PTR [ebx+0x4c]"),
        (0x0055B897, "call", "0x56e740"), (0x0055B89C, "movzx", "eax,WORD PTR [ebx+0x4a]"),
        (0x0055B8A5, "movsx", "ecx,WORD PTR [ebx+0x4e]"), (0x0055B8B9, "call", "0x56e740"),
        (0x0055B8C2, "call", "0x5c0b50"), (0x0055B8D0, "lea", "eax,[ebx-0x7]"), (0x0055B8D3, "cmp", "eax,0xc5"),
        (0x0055B8DE, "movzx", "eax,BYTE PTR [eax+0x55be04]"), (0x0055BADC, "cmp", "ebx,0x6b"),
        (0x0055BAE1, "cmp", "DWORD PTR [esi],0x0"), (0x0055BAEA, "movsx", "edx,BYTE PTR [eax+0xc]"),
        (0x0055BAF1, "cmp", "ecx,edx"), (0x0055BCB2, "call", "0x56dfa0")]),
    ("aggregate 10: STATLIST_Alloc 0x006251F0, STATLIST_SetRemoveCallback 0x00625CE0, UnitStatListCreate 0x00626D40", [
        (0x00625204, "mov", "edx,0x3c"), (0x0062520B, "call", "0x40b430"), (0x0062521C, "mov", "eax,DWORD PTR [ebp+0x14]"),
        (0x0062521F, "mov", "ecx,DWORD PTR [ebp+0x18]"), (0x00625225, "mov", "DWORD PTR [esi+0x8],eax"),
        (0x00625234, "mov", "DWORD PTR [esi+0xc],ecx"), (0x00663C5F, "mov", "ecx,DWORD PTR [eax+0xc]"),
        (0x00663C62, "mov", "eax,DWORD PTR [eax]"), (0x00663C6E, "call", "0x6251f0"),
        (0x00625CED, "mov", "DWORD PTR [eax+0x38],ecx"), (0x00626D74, "mov", "edx,0x64"),
        (0x00626DAC, "or", "ecx,0x80000000"), (0x00626DB5, "mov", "DWORD PTR [esi+0x44],edi"),
        (0x00626DBE, "mov", "eax,DWORD PTR [ecx+0xc4]"), (0x00626DC7, "add", "eax,0x1f"), (0x00626DD2, "sar", "ebx,0x5"),
        (0x00626DF5, "mov", "DWORD PTR [esi+0x58],eax"), (0x00626E00, "mov", "DWORD PTR [edi+0x5c],esi")]),
]


def pins_check(pins, tag):
    ok = 0
    for va, mn, sub in pins:
        out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % va,
                              "--stop-address=0x%x" % (va + 16), S4.EXE], capture_output=True, text=True).stdout
        line = [ln for ln in out.splitlines() if ln.strip().startswith("%x:" % va)]
        txt = line[0].split(":", 1)[1].strip() if line else ""
        good = bool(line) and txt.startswith(mn) and sub in txt
        ok += good
        print("  %s 0x%08X %s" % ("ok " if good else "BAD", va, txt))
    print("S4E8 static %s pins=%d ok=%d" % (tag, len(pins), ok))
    return ok == len(pins)


def cmd_static():
    good = pins_check(PINS, "families")
    for row, pins in PINS_STATIC:
        print("row %s" % row)
        good &= pins_check(pins, row)
    return 0 if good else 1


# ---------------------------------------------------------------------------------------------------------- sites
SITE_ROOTS = [(0x0055D710, "inventory 67: ItemAutoEquipSlot"), (0x0062EAF0, "inventory 67: ItemReqCheck"),
              (0x00563C00, "inventory 61: CursorDrop"), (0x00627030, "aggregate 11: STATLIST_AddStat"),
              (0x00624D10, "aggregate 11: STATLIST_RemoveEntry")]


def cmd_sites():
    P7.SITE_ROOTS = SITE_ROOTS
    return P7.cmd_sites()


# ---------------------------------------------------------------------------------------------------------- xref
def cmd_xref():
    """aggregate 23: the callback's key switch from the raw bytes (index bytes 0x0055BE04, 198 keys from 7; targets
    0x0055BDD8); aggregate 10: the rel32 callers of STATLIST_SetRemoveCallback and STATLIST_Alloc."""
    data = open(S4.EXE, "rb").read()
    tab = S4.dwords(0x0055BDD8, 11)
    idx = data[S4.va_off(0x0055BE04):S4.va_off(0x0055BE04) + 0xC6]
    groups = collections.defaultdict(list)
    for k, b in enumerate(idx):
        groups[b].append(k + 7)
    for b in sorted(groups):
        ks = groups[b]
        print("  case %d -> 0x%08X: %s" % (b, tab[b], ks if len(ks) < 20 else "%d other keys" % len(ks)))
    for t, nm in ((0x00625CE0, "STATLIST_SetRemoveCallback"), (0x006251F0, "STATLIST_Alloc")):
        cs, ab = S4.raw_callers(t), S4.raw_abs(t)
        print("  %s 0x%08X: %d rel32 sites, %d abs32: %s" % (nm, t, len(cs), len(ab), " ".join("0x%08X" % v for v in cs)))
    print("S4E8 xref switch_cases=%d keys=%d" % (len(groups), sum(len(v) for v in groups.values())))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["cases", "check", "static", "sites", "xref", "manifest"])
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
    if a.cmd == "sites":
        return cmd_sites()
    if a.cmd == "xref":
        return cmd_xref()
    return P3.cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

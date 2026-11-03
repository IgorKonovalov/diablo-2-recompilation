#!/usr/bin/env python3
"""Plan 0060 P1.1 (`lane/r60a`): the item-use entries under Ghidra's p-code emulator (ADR-0015, ADR-0021), compared with
tools/item_inventory.py. No game run, no slot.

    python3 -I tools/use_emu.py cases [--dir D]      write D/<family>.cases and D/<family>.mem
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/use_emu.py check [--dir D]      compare every D/<family>.out with the model, account for every traced
                                                     access, run the controls; prints the counts
    python3 -I tools/use_emu.py static [--dir D]     the use columns' u8 readers and getter calls, the pinned forms (D/static.txt)
    python3 -I tools/use_emu.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r60a/emu. Every case draw comes from random.Random("r60a-<family>"), so `cases` regenerates
identical files. A case is a declared scratch image, field by field; nothing is patched. Each boundary is a callee's
entry; the checker asserts the boundary, the call site (the return address), the arguments and the seed at it.

Families and what the claim covers:
  classmul  0x0062A5D0, 0x0062A620 return values, all classes, odd and negative amounts
  stat3, stat4, stat5  entries 3, 4, 5 up to their first boundary (UnitAddStat, STATLIST_Alloc, the event queue,
            STATLIST_SetStat, the golem's heal) or return
  golem     0x005C6870 called directly, up to the golem's heal or the return
  elix      entry 8; idtest entry 1's test; idfn entry 1's use; cube entry 7; dispatch ItemUse 0x005BF240; key 0x0055F140

Controls (each must fail the cases it separates; `check` prints the number each one fails):
  draw1      one draw in place of two (entry 3)            nodraw     no doubling
  half       r2 < r1 in place of r2 < r1 >> 1              floordiv   floor in place of truncation in the refill rate
  sar        v * 3 / 2 in place of v + (v >> 1)            nocap      no cap at the max stat
  pctflat    the rejuvenation's calc as a flat amount      no100      MulDiv at 100 percent in place of the maximum
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

import item_inventory as inv  # noqa: E402
from party_emu import parse_out  # noqa: E402

M32 = 0xFFFFFFFF
GAME, DTBL, POOL, ISC = 0x10000000, 0x10010000, 0x10020000, 0x10030000
RECS, USER, ITEM, IDATA = 0x10060000, 0x10100000, 0x10101000, 0x10102000
SLIST, ARR, NODE, NARR = 0x10103000, 0x10104000, 0x10105000, 0x10106000
UDATA, PETS, PETARR, PETN, GOLEM, MS, SKL = 0x10107000, 0x10107100, 0x10107200, 0x10107800, 0x10108000, 0x10110000, 0x10140000
INV, ITEMS2, TYPES, BOOKS, ITSL = 0x10180000, 0x10181000, 0x10190000, 0x101A0000, 0x101B0000
FRAME_OFF, MEMCTX_OFF = 0xA8, 0x1C
NISC, NSTATES, NTYPES = 400, 192, 110
TYPE_STRIDE = 4
GUARDS = (0x00408A60, 0x00681E09, 0x0040B4B0, 0x0040B430, 0x0040B480)
F_ADD, F_ALLOC, F_QUEUE, F_SET, F_GHEAL = 0x006272B0, 0x006251F0, 0x005417D0, 0x00627150, 0x005C5F10
F_FATAL = 0x00408090
ENTRY = {3: 0x005BE3F0, 4: 0x005BE7B0, 5: 0x005BEAC0}
SITES = {3: {F_ADD: 0x5BE5C7, F_ALLOC: 0x5BE607, F_QUEUE: 0x5BE6B3, F_SET: 0x5BE6D4},
         4: {F_ADD: 0x5BE93A, F_ALLOC: 0x5BE976, F_QUEUE: 0x5BEA1C, F_SET: 0x5BEA3D},
         5: {F_ADD: 0x5BEC43, F_ALLOC: 0x5BEC81, F_QUEUE: 0x5BED20, F_SET: 0x5BED42}}
GSITE = 0x5C68E6
USE_ENTRIES = {1: 0x5BE230, 2: 0x5BE290, 3: 0x5BE3F0, 4: 0x5BE7B0, 5: 0x5BEAC0, 6: 0x5BEF90, 7: 0x5BF0C0, 8: 0x5BF060,
               9: 0x5BEDA0, 10: 0x5BF170, 11: 0x5BF1F0}
FAMILIES = ("classmul", "stat3", "stat4", "stat5", "golem", "elix", "idtest", "idfn", "cube", "dispatch", "key")
COUNTS = {"classmul": 800, "stat3": 2400, "stat4": 800, "stat5": 1200, "golem": 300, "elix": 200, "idtest": 120,
          "idfn": 300, "cube": 300, "dispatch": 600, "key": 300}


def le32(v):
    return struct.pack("<I", v & M32)


def le16(v):
    return struct.pack("<H", v & 0xFFFF)


class Case:
    def __init__(self):
        self.lines, self.meta, self.dumps = [], {}, []

    def put(self, addr, data):
        self.lines.append("w %08x %s" % (addr, data.hex()))

    def d32(self, addr, v):
        self.put(addr, le32(v))

    def d16(self, addr, v):
        self.put(addr, le16(v))

    def d8(self, addr, v):
        self.put(addr, bytes([v & 0xFF]))

    def dump(self, addr, n):
        self.dumps.append((addr, n))

    def call(self, fn, ecx, edx, *args):
        for a, n in self.dumps:
            self.lines.append("d %08x %d" % (a, n))
        self.lines.append("call %08x %08x %08x %s" % (fn, ecx & M32, edx & M32, " ".join("%08x" % (a & M32) for a in args)))
        return "\n".join(self.lines)


def put_stats(c, sl, arr, stats, special=False):
    """A stat list holding {stat: value} at layer 0; special: flag bit 31, arrays at +0x48/+0x4C."""
    flags = 0x80000000 if special else 0
    ao, co = (0x48, 0x4C) if special else (0x24, 0x28)
    c.d32(sl + 0x10, flags)
    ks = sorted(stats)
    c.d32(sl + ao, arr)
    c.d16(sl + co, len(ks))
    for i, s in enumerate(ks):
        c.put(arr + 8 * i, le32(s << 16) + le32(stats[s]))
        c.d8(ISC + 0x144 * s + 5, 0)


def put_unit(c, u, base=USER, slist_chain=True):
    c.d32(base, u.type)
    c.d32(base + 4, u.cls)
    c.d32(base + 0xC, u.uid)
    c.d32(base + 0x14, UDATA)
    c.d32(base + 0x20, u.low)
    c.d32(base + 0x24, u.high)
    c.d32(base + 0x5C, SLIST)
    put_stats(c, SLIST, ARR, u.stats, special=True)
    c.d32(SLIST + 0x3C, 0)
    c.d32(SLIST + 0x40, 0)
    c.d32(UDATA + 0x44, 0)


def put_state_list(c, u, state, rnd):
    """The unit's state list chain at SLIST+0x3C: an optional decoy, then the list of `state`."""
    sl = u.slist
    head = NODE
    if rnd.random() < 0.3:
        dec = NODE + 0x100
        c.d32(dec + 0x14, state + 1 if state + 1 < NSTATES else state - 1)
        c.d32(dec + 0x2C, NODE)
        head = dec
    c.d32(SLIST + (0x40 if rnd.random() < 0.25 else 0x3C), head)
    c.d32(NODE + 0x14, state)
    c.d32(NODE + 0x18, sl["end"])
    c.d32(NODE + 0x2C, 0)
    put_stats(c, NODE, NARR, sl["base"], special=False)
    c.dump(NODE + 0x10, 12)


def put_golem(c, rnd, share):
    c.d32(UDATA + 0x44, PETS)
    c.d32(PETS, PETARR)
    c.d32(PETARR + 3 * 12, PETN)
    gid = rnd.randrange(1, 1 << 30)
    c.d32(PETN, 0)
    c.d32(PETN + 4, gid)
    c.d32(GAME + 0x1320 + (gid & 0x7F) * 4, GOLEM)
    c.d32(GOLEM, 1)
    c.d32(GOLEM + 4, 0x122)
    c.d32(GOLEM + 0xC, gid)
    c.d32(GOLEM + 0xE4, 0)
    row = rnd.randrange(1, 300)
    c.d16(MS + 0x122 * 0x1A8 + 0x170, row)
    c.d32(SKL + row * 0x23C + 0x15C, share)


def clear_hash(c, gid):
    c.d32(GAME + 0x1320 + (gid & 0x7F) * 4, 0)


def put_calc(c, off, v):
    c.put(POOL + off, b"\x09" + le32(v) + b"\x00")


def put_rec(c, row, rec):
    r = RECS + row * 0x1A8
    c.d16(r + 0x98, rec["state"])
    off = 0
    ln = rec["len"]
    if ln == 0 and rec.get("blanklen"):
        c.d32(r + 0xB0, M32)
    else:
        put_calc(c, off, ln)
        c.d32(r + 0xB0, off)
        off += 6
    for k, (s, calc) in enumerate(rec["slots"]):
        c.d16(r + 0x9E + 2 * k, s)
        if s < 0:
            c.d32(r + 0xA4 + 4 * k, M32)
        else:
            put_calc(c, off, calc)
            c.d32(r + 0xA4 + 4 * k, off)
            off += 6
    for s, (shift, maxstat) in rec["isc"].items():
        c.d8(ISC + 0x144 * s + 0x18, shift)
        c.d16(ISC + 0x144 * s + 0x32, maxstat)


# ------------------------------------------------------------------------------------------------- generators
def gen_classmul(rnd, i):
    c = Case()
    fn = rnd.choice((0x0062A5D0, 0x0062A620))
    typ = rnd.choice((0, 0, 0, 0, 1, 2))
    cls = rnd.randrange(8)
    v = rnd.choice((rnd.randrange(-(1 << 24), 1 << 24), rnd.randrange(1, 400) << 8, rnd.randrange(1, 1000)))
    null = rnd.random() < 0.05
    c.d32(USER, typ)
    c.d32(USER + 4, cls)
    c.meta = dict(f="classmul", fn=fn, typ=typ, cls=cls, v=v, null=null)
    return c.call(fn, 0, 0, 0 if null else USER, v), c.meta


def rand_unit(rnd):
    typ = rnd.choice((0, 0, 0, 1))
    u = inv.Unit(typ=typ, cls=rnd.randrange(7) if typ == 0 else rnd.randrange(700), uid=rnd.randrange(1, 1 << 30),
                 low=rnd.getrandbits(32), high=rnd.getrandbits(32))
    u.stats[inv.VIT] = rnd.choice((0, 25, 100, 512, rnd.randrange(1, 600), -3))
    u.stats[inv.ENE] = rnd.choice((0, 15, 100, 512, rnd.randrange(1, 600)))
    top = rnd.choice((rnd.randrange(1, 4000) << 8, rnd.randrange(4096, 9000) << 8, rnd.randrange(0x100001, 0x900000)))
    u.stats[inv.MAXLIFE] = top
    u.stats[inv.LIFE] = rnd.randrange(0, top + 1)
    top = rnd.choice((rnd.randrange(1, 2000) << 8, rnd.randrange(0x100001, 0x500000)))
    u.stats[inv.MAXMANA] = top
    u.stats[inv.MANA] = rnd.randrange(0, top + 1)
    return u


STAT_POOL = (inv.LIFE, inv.MANA, inv.MANAREC, inv.HPREGEN, 10, 13)
MAXOF = {inv.LIFE: inv.MAXLIFE, inv.MANA: inv.MAXMANA, 10: 11}


def gen_stat(entry, rnd, i):
    c = Case()
    u = rand_unit(rnd)
    frame = rnd.randrange(0, 1 << 20)
    mode = rnd.choice(("instant", "instant", "fresh", "refill0", "refill1", "refill1", "badstate", "norec", "badslot"))
    if entry == 5 and rnd.random() < 0.5:
        mode = "instant"
    ln = {"instant": 0}.get(mode, rnd.choice((128, 160, 171, 192, 256, 750, rnd.randrange(1, 2000))))
    state = rnd.randrange(1, NSTATES)
    if mode == "badstate":
        state = rnd.choice((0, -1, NSTATES, NSTATES + 5))
    s0 = rnd.choice(STAT_POOL)
    s1 = rnd.choice(STAT_POOL)
    amt = rnd.choice((30, 60, 100, 180, 320, 20, 40, 80, 150, 250, 35, 100, 1, rnd.randrange(1, 5000), 0, -5))
    if entry == 5:
        amt = rnd.choice((35, 100, 100, 1, 99, rnd.randrange(1, 200), 0, -5))
    isc = {}
    for s in (s0, s1):
        shift = rnd.choice((0, 0, 8, rnd.randrange(0, 6))) if entry != 5 else 8
        isc[s] = (shift, MAXOF.get(s, 0xFFFF))
    if rnd.random() < 0.1 and entry == 5:
        isc[s0] = (8, 0xFFFF)
    if mode in ("refill1",):
        slots = [(s0, 0 if entry != 5 else 0), (s1, amt)]
    elif mode == "badslot":
        slots = [(-1, 0), (s1, amt)]
    else:
        slots = [(s0, amt), (-1, 0)]
    slots.append((-1, 0))
    if s0 == s1:
        isc[s0] = isc[s1]
    rec = {"len": ln, "state": state, "slots": slots, "isc": isc, "blanklen": rnd.random() < 0.7}
    if mode in ("refill0", "refill1"):
        rem = rnd.choice((rnd.randrange(1, 300), rnd.randrange(-50, 0), 0, -ln, -ln - 3))
        base = {s: rnd.choice((rnd.randrange(0, 4000), rnd.randrange(0, 1 << 20), -rnd.randrange(1, 900))) for s in {s0, s1}}
        if (slots[1][0] == inv.LIFE) and ln + rem <= 0:      # the loop's end would reach the unmodelled life-percent message
            rem = 5
        u.slist = {"end": (frame + rem) & M32, "base": base}
    golem = entry != 4 and u.type == 0 and rnd.random() < 0.08
    c.d32(GAME + FRAME_OFF, frame)
    c.d32(GAME + MEMCTX_OFF, 0x55AA0000 | i)
    row = rnd.randrange(0, 151)
    if mode == "norec":
        row = 200 + rnd.randrange(50)
    c.d32(ITEM, 4)
    c.d32(ITEM + 4, row)
    put_unit(c, u)
    if u.slist is not None:
        put_state_list(c, u, state, rnd)
    if mode != "norec":
        put_rec(c, row, rec)
    if golem:
        u.golem = {"share": rnd.choice((0, 10, 20, 33, 50, 100, rnd.randrange(0, 150)))}
        put_golem(c, rnd, u.golem["share"])
    c.dump(USER + 0x20, 8)
    item = 0 if mode == "norec" and rnd.random() < 0.3 else ITEM
    c.meta = dict(f="stat%d" % entry, entry=entry, u=u.__dict__.copy(), rec=rec, frame=frame, mode=mode, norec=mode == "norec",
                  memctx=0x55AA0000 | i)
    return c.call(ENTRY[entry], GAME, USER, item, 0, 0, 0, 0), c.meta


def gen_golem(rnd, i):
    c = Case()
    u = inv.Unit(typ=0, cls=rnd.randrange(7), uid=7, low=rnd.getrandbits(32), high=rnd.getrandbits(32))
    put_unit(c, u)
    v = rnd.randrange(1, 1 << 24)
    kind = rnd.choice(("golem", "golem", "golem", "nopet", "otherclass"))
    share = rnd.choice((0, 10, 20, 50, 100, rnd.randrange(0, 150)))
    if kind != "nopet":
        put_golem(c, rnd, share)
    if kind == "otherclass":
        c.d32(GOLEM + 4, 0x121)
    c.dump(USER + 0x20, 8)
    c.meta = dict(f="golem", kind=kind, share=share, v=v, low=u.low, high=u.high)
    return c.call(0x005C6870, GAME, USER, v), c.meta


def put_item(c, base, data, row, flags=0, sl=None, stats=None):
    c.d32(base, 4)
    c.d32(base + 4, row)
    c.d32(base + 0xC, 0x4000 + (base & 0xFFF))
    c.d32(base + 0x14, data)
    c.d32(data + 0x18, flags)
    if sl:
        c.d32(base + 0x5C, sl)
        put_stats(c, sl, sl + 0x80, stats)


def gen_elix(rnd, i):
    c = Case()
    fi = rnd.choice((13, 6, 0, 399, 400, 500, -1, rnd.randrange(0, 400)))
    val = rnd.choice((0, 5, -2, rnd.randrange(1, 100)))
    put_item(c, ITEM, IDATA, 3, sl=ITSL, stats={71: val} if val or rnd.random() < 0.5 else {})
    c.d32(IDATA + 0x28, fi)
    c.meta = dict(f="elix", fi=fi, val=val)
    return c.call(0x005BF060, GAME, USER, ITEM, 0, 0, 0, 0), c.meta


def put_types(c, rows):
    """rows: {class row: [type ids]}: the record's type at +0x11E and that type's bit row in the type-equivalence bits."""
    for row, types in rows.items():
        tr = row % 60
        c.d16(RECS + row * 0x1A8 + 0x11E, tr)
        words = [0] * TYPE_STRIDE
        for t in types:
            words[t >> 5] |= 1 << (t & 31)
        c.put(TYPES + tr * TYPE_STRIDE * 4, b"".join(le32(w) for w in words))
        c.d16(RECS + row * 0x1A8 + 0x120, -1)


def gen_idtest(rnd, i):
    c = Case()
    kind = rnd.choice(("book", "scroll", "other", "badbook"))
    row = rnd.randrange(150)
    types = {"book": [18], "scroll": [22], "other": [41], "badbook": [22]}[kind]
    put_item(c, ITEM, IDATA, row, flags=rnd.getrandbits(32) & ~4)
    flags0 = None
    put_types(c, {row: types})
    suffix = rnd.randrange(0, 3)
    c.d16(IDATA + 0x3E, 9 if kind == "badbook" else suffix)
    icon = rnd.randrange(0, 200)
    c.d8(BOOKS + suffix * 0x20 + 2, icon)
    c.d8(RECS + row * 0x1A8 + 0x134, icon)
    skill = rnd.randrange(0, 0x10000)
    c.dump(IDATA + 0x18, 4)
    c.meta = dict(f="idtest", kind=kind, icon=icon, skill=skill)
    return c.call(0x005BE130, GAME, USER, ITEM, 0, 1, 2, skill), c.meta


def put_interact(c, kind, rnd):
    if kind == "none":
        c.d8(USER + 0x6C, 0)
        c.d32(USER + 0x68, 6)
        c.d32(USER + 0x64, M32)
    else:
        g = rnd.randrange(1, 1 << 30)
        c.d8(USER + 0x6C, 1)
        c.d32(USER + 0x68, {"player": 0, "player_gone": 0, "mon": 1, "obj": 2, "stash": 2, "objother": 2, "gone": 2}[kind])
        c.d32(USER + 0x64, g)
        off = {0: 0x1120, 1: 0x1320, 2: 0x1520}[{"player": 0, "player_gone": 0, "mon": 1, "obj": 2, "stash": 2, "objother": 2, "gone": 2}[kind]]
        bucket = GAME + off + (g & 0x7F) * 4
        if kind in ("player_gone", "gone"):
            c.d32(bucket, 0)
        else:
            c.d32(bucket, GOLEM)
            c.d32(GOLEM, {"player": 0, "mon": 1}.get(kind, 2))
            c.d32(GOLEM + 4, 0x10B if kind == "stash" else 0x10A)
            c.d32(GOLEM + 0xC, g)
            c.d32(GOLEM + 0xE4, 0)


def put_inv(c, items, cursor=0):
    c.d32(USER + 0x60, INV)
    c.d32(INV, 0x01020304)
    c.d32(INV + 0xC, items[0][0] if items else 0)
    c.d32(INV + 0x20, cursor)
    for k, (it, data) in enumerate(items):
        c.d32(data + 0x64, items[k + 1][0] if k + 1 < len(items) else 0)


def gen_idfn(rnd, i):
    c = Case()
    it = rnd.choice(("none", "none", "none", "player", "player_gone", "mon"))
    c.d32(USER, 0)
    put_interact(c, it, rnd)
    target_id = rnd.random() < 0.25
    inside = rnd.random() < 0.75
    others = [(ITEMS2 + 0x200 * k, ITEMS2 + 0x100 + 0x200 * k) for k in range(rnd.randrange(0, 4))]
    for a, dt in others:
        put_item(c, a, dt, 1)
    items = list(others)
    if inside:
        items.insert(rnd.randrange(len(items) + 1), (ITEM, IDATA))
    put_item(c, ITEM, IDATA, 2, flags=0x10 if target_id else rnd.getrandbits(32) & ~0x10)
    put_inv(c, items)
    c.meta = dict(f="idfn", it=it, target_id=target_id, inside=inside)
    return c.call(0x005BE230, GAME, USER, ITEMS2 + 0x1000, ITEM, 0, 0, 0), c.meta


def gen_cube(rnd, i):
    c = Case()
    utype = rnd.choice((0, 0, 0, 0, 1))
    c.d32(USER, utype)
    c.d32(USER + 0x14, UDATA)
    busy = rnd.choice(("no", "no", "stash", "objother", "mon", "gone", "cursor", "pdata"))
    put_interact(c, busy if busy in ("stash", "objother", "mon", "gone") else "none", rnd)
    put_inv(c, [], cursor=ITEM if busy == "cursor" else 0)
    c.d32(UDATA + 0x4C, 1 if busy == "pdata" else 0)
    null = rnd.random() < 0.05
    put_item(c, ITEM, IDATA, 2)
    c.meta = dict(f="cube", utype=utype, busy=busy, guid=0x4000 + (ITEM & 0xFFF))
    return c.call(0x005BF0C0, GAME, USER, ITEM, 0, 0, 0, 0), c.meta


def gen_dispatch(rnd, i):
    c = Case()
    utype = rnd.choice((0, 0, 0, 0, 1, 1, 2, 3))
    c.d32(USER, utype)
    nouser = rnd.random() < 0.03
    itype = rnd.choice((4, 4, 4, 4, 4, 4, 4, 4, 4, 1))
    noitem = rnd.random() < 0.03
    row = rnd.randrange(150)
    kind = rnd.choice(("book", "scroll", "other", "other", "other"))
    types = {"book": [18], "scroll": [22], "other": [9]}[kind]
    flag4 = rnd.random() < 0.4
    put_item(c, ITEM, IDATA, row, flags=(4 if flag4 else 0) | (rnd.getrandbits(32) & ~4))
    c.d32(ITEM, itype)
    put_types(c, {row: types})
    spell = rnd.choice((0, -1, 1, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 30, 31, 40))
    bookspell = rnd.choice((0, 1, 2, -1))
    suffix = rnd.randrange(0, 3)
    missing = rnd.random() < 0.1
    c.d16(IDATA + 0x3E, 9 if missing else suffix)
    bs = rnd.randrange(1, 300)
    c.d32(BOOKS + suffix * 0x20 + 4, bookspell)
    c.d32(BOOKS + suffix * 0x20 + 0xC, bs)
    c.d32(RECS + row * 0x1A8 + 0x94, spell)
    arg2, x, y = rnd.getrandbits(32), rnd.getrandbits(16), rnd.getrandbits(16)
    c.dump(IDATA + 0x18, 4)
    c.meta = dict(f="dispatch", utype=utype, nouser=nouser, itype=itype, noitem=noitem, kind=kind, flag4=flag4, spell=spell,
                  bookspell=bookspell, missing=missing, bs=bs, arg2=arg2, x=x, y=y)
    return c.call(0x005BF240, GAME, 0 if nouser else USER, 0 if noitem else ITEM, arg2, x, y), c.meta


def gen_key(rnd, i):
    c = Case()
    c.d32(USER, 0)
    n = rnd.randrange(0, 5)
    items = []
    keys = []
    for k in range(n):
        a, dt = ITEMS2 + 0x400 * k, ITEMS2 + 0x100 + 0x400 * k
        sl = ITEMS2 + 0x200 + 0x400 * k
        is_key = rnd.random() < 0.5
        page = rnd.choice((0, 0, 0, 2, 3, 4))
        q = rnd.choice((1, 1, 2, 3, 12, 0))
        put_item(c, a, dt, k + 1, sl=sl, stats={70: q})
        c.d8(dt + 0x45, page)
        put_types(c, {k + 1: [41] if is_key else [9]})
        items.append((a, dt))
        keys.append((a, is_key, page, q))
    put_inv(c, items)
    c.meta = dict(f="key", keys=keys)
    return c.call(0x0055F140, GAME, USER), c.meta


GEN = {"classmul": gen_classmul, "stat3": lambda r, i: gen_stat(3, r, i), "stat4": lambda r, i: gen_stat(4, r, i),
       "stat5": lambda r, i: gen_stat(5, r, i), "golem": gen_golem, "elix": gen_elix, "idtest": gen_idtest, "idfn": gen_idfn,
       "cube": gen_cube, "dispatch": gen_dispatch, "key": gen_key}


def mem_spec(f):
    out = ["# plan 0060 P1.1: the fixed part of the image", "dword 00744304 %08x" % DTBL,
           "dword %08x %08x" % (DTBL + 0xBD4, NISC), "dword %08x %08x" % (DTBL + 0xBCC, ISC),
           "dword %08x %08x" % (DTBL + 0xC4, NSTATES), "dword %08x %08x" % (DTBL + 0x98, POOL),
           "dword %08x 00010000" % (DTBL + 0x9C), "dword %08x 00000008" % (DTBL + 0xBF0),
           "dword %08x %08x" % (DTBL + 0xA78, MS), "dword %08x 00000200" % (DTBL + 0xA80),
           "dword %08x %08x" % (DTBL + 0xB98, SKL), "dword %08x 00000200" % (DTBL + 0xBA0),
           "dword %08x %08x" % (DTBL + 0xBFC, NTYPES), "dword %08x %08x" % (DTBL + 0xC00, TYPE_STRIDE),
           "dword %08x %08x" % (DTBL + 0xC04, TYPES), "dword 0096ca58 00000097", "dword 0096ca5c %08x" % RECS,
           "dword 0096cc60 00000003", "dword 0096cc64 %08x" % BOOKS]
    for g in GUARDS:
        out.append("guard %08x" % g)
    obs = {"classmul": (), "golem": (F_GHEAL,), "elix": (F_ADD,), "idtest": (0x005531C0,), "idfn": (0x00562590,),
           "cube": (0x00554120, 0x00554190), "key": (F_ADD, 0x0055E000),
           "dispatch": tuple(USE_ENTRIES.values()) + (0x005BE130,)}.get(f, (F_ADD, F_ALLOC, F_QUEUE, F_SET, F_GHEAL))
    for a in tuple(obs) + (F_FATAL,):
        out.append("observe %08x" % a)
    return "\n".join(out) + "\n"


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    for f in FAMILIES:
        rnd = random.Random("r60a-" + f)
        blocks, metas = [], []
        for i in range(COUNTS[f]):
            b, m = GEN[f](rnd, i)
            blocks.append(b)
            metas.append(m)
        open(os.path.join(d, f + ".cases"), "w").write("\n".join(blocks) + "\n")
        open(os.path.join(d, f + ".mem"), "w").write(mem_spec(f))
    print("cases written", sum(COUNTS.values()))


def metas(f):
    rnd = random.Random("r60a-" + f)
    return [GEN[f](rnd, i)[1] for i in range(COUNTS[f])]


# ------------------------------------------------------------------------------------------------- the model's verdicts
def model_stat(m, ctl=None):
    d = m["u"]
    u = inv.Unit(d["type"], d["cls"], d["uid"], d["low"], d["high"], d["stats"], d["slist"], d["golem"])
    rec = m["rec"]
    if m["norec"]:
        return ("ret", 0), u
    saved = inv.potion_scale
    if ctl:
        inv.potion_scale = control_scale(ctl, saved)
    try:
        r = inv.use_stat_entry(m["entry"], u, rec, m["frame"], m["memctx"], NISC, NSTATES)
    finally:
        inv.potion_scale = saved
    return r, u


def control_scale(ctl, real):
    def f(u, s, v):
        if ctl == "draw1" and s in (6, 8, 26, 74):
            src = 3 if s in (6, 74) else 1
            n = u.stat(src)
            v2 = inv.i32(v << 8) if s in (26, 74) else v
            v2 = inv.mana_mul(u.type, u.cls, v2) if s in (8, 26) else inv.life_mul(u.type, u.cls, v2)
            if n > 0:
                r1 = u.range(n)
                if r1 >> 1 > 50:
                    v2 *= 2
            return v2
        if ctl == "nodraw" and s in (6, 8, 26, 74):
            v2 = inv.i32(v << 8) if s in (26, 74) else v
            return inv.mana_mul(u.type, u.cls, v2) if s in (8, 26) else inv.life_mul(u.type, u.cls, v2)
        if ctl == "half" and s in (6, 8, 26, 74):
            src = 3 if s in (6, 74) else 1
            n = u.stat(src)
            v2 = inv.i32(v << 8) if s in (26, 74) else v
            v2 = inv.mana_mul(u.type, u.cls, v2) if s in (8, 26) else inv.life_mul(u.type, u.cls, v2)
            if n > 0:
                r1 = u.range(n)
                r2 = u.range(100)
                if r2 < r1:
                    v2 = inv.i32(v2 * 2)
            return v2
        return real(u, s, v)
    return f


def cmp_stat(m, c, a, dumps, ctl=None):
    """-> None when the case's output matches the model, else a reason."""
    r, u = model_stat(m, ctl)
    entry = m["entry"]
    f = c[3]
    if r[0] == "ret":
        if f == "STOP" or f == "OBS":
            return "model return, got %s %s" % (f, c[4])
        if int(c[3].split("=")[1], 16) != r[1]:
            return "ret %s, model %d" % (c[3], r[1])
        seed = dict(dumps).get(USER + 0x20)
        if seed is None or struct.unpack("<II", seed) != (u.low, u.high):
            return "seed at the return"
        return None
    if f != "OBS":
        return "model %s, got %s" % (r[0], " ".join(c[3:6]))
    pc = int(c[4], 16)
    words = struct.unpack("<16I", a)
    seed = dict(dumps).get(USER + 0x20)
    if seed is None or struct.unpack("<II", seed) != (u.low, u.high):
        return "seed at the boundary"
    if r[0] == "golem":
        regs = dict(x.split("=") for x in c[6:])
        if pc != F_GHEAL or words[0] != GSITE or inv.i32(int(regs["eax"], 16)) != r[1] or int(regs["ebx"], 16) != GOLEM:
            return "golem %s" % (c[3:],)
        return None
    want = {"addstat": F_ADD, "alloc": F_ALLOC, "queue": F_QUEUE, "setstat": F_SET}[r[0]]
    if pc != want or words[0] != SITES[entry][want]:
        return "boundary %x site %x, model %x" % (pc, words[0], want)
    if r[0] == "addstat" and (words[1] != USER or words[2] != r[1] or inv.i32(words[3]) != r[2] or words[4] != 0):
        return "addstat args %s model %s" % (words[1:5], r)
    if r[0] == "alloc" and (words[1] != m["memctx"] or words[2] != 2 or inv.i32(words[3]) != r[1] or words[4] != m["u"]["type"]
                            or words[5] != m["u"]["uid"]):
        return "alloc args %s model %s" % (words[1:6], r)
    if r[0] == "queue" and (words[1] != 0xC or inv.i32(words[2]) != r[1] or words[3] or words[4]):
        return "queue args %s model %s" % (words[1:5], r)
    if r[0] == "setstat" and (words[1] != NODE or words[2] != r[1] or inv.i32(words[3]) != r[2] or words[4]):
        return "setstat args %s model %s" % (words[1:5], r)
    if r[0] in ("queue", "setstat"):
        node = dict(dumps).get(NODE + 0x10)
        end = r[1] if r[0] == "queue" else r[3]
        if inv.i32(struct.unpack_from("<I", node, 8)[0]) != end:
            return "list end"
        if end > 0 and not struct.unpack_from("<I", node, 0)[0] & 2:
            return "list flag 2"
    return None


def cmp_case(m, c, a, dumps):
    f = m["f"]
    head = c[3]
    def ret():
        return int(head.split("=")[1], 16) if head.startswith("eax=") else None
    words = struct.unpack("<16I", a) if a else None
    if f == "classmul":
        if m["null"]:
            want = m["v"] * 2 if m["fn"] == 0x62A5D0 else m["v"]
            want = inv.i32(want)
        else:
            want = (inv.life_mul if m["fn"] == 0x62A5D0 else inv.mana_mul)(m["typ"], m["cls"], m["v"])
        return None if ret() is not None and inv.i32(ret()) == want else "classmul %s %d" % (head, want)
    if f.startswith("stat"):
        return cmp_stat(m, c, a, dumps)
    if f == "golem":
        hit = m["kind"] == "golem"
        if hit:
            if head != "OBS" or int(c[4], 16) != F_GHEAL:
                return "golem expected heal, %s" % head
            regs = dict(x.split("=") for x in c[6:])
            want = inv.tdiv(inv.i32(m["v"] * m["share"]), 100)
            return None if inv.i32(int(regs["eax"], 16)) == want and words[0] == GSITE else "share %s %d" % (regs["eax"], want)
        return None if ret() == m["v"] else "golem pass %s" % head
    if f == "elix":
        ok = 0 <= m["fi"] < NISC and m["val"] != 0
        if ok:
            if head != "OBS" or words[0] != 0x5BF09C or words[1:5] != (USER, m["fi"], m["val"] & M32, 0):
                return "elix %s" % (head,)
            return None
        if m["fi"] < 0 or m["fi"] >= NISC or m["val"] == 0:
            return None if ret() == 0 else "elix refused %s" % head
    if f == "idtest":
        flags = struct.unpack("<I", dict(dumps)[IDATA + 0x18])[0]
        if head == "OBS":
            if not flags & 4:
                return "flag 4 not set before the packet"
            if int(c[4], 16) != 0x5531C0 or words[0] != 0x5BE165 or words[1:6] != (0x40, m["icon"], 0, 1, m["skill"]):
                return "idtest args %s" % (words[:6],)
            if m["kind"] == "badbook":
                return "bad book reached the packet"
            return None
        if m["kind"] == "badbook" and ret() == 1 and flags & 4:
            return None
        return "idtest %s" % head
    if f == "idfn":
        refuse = m["it"] == "player" or m["target_id"] or not m["inside"]
        if refuse:
            return None if ret() == 0 else "idfn refused %s" % head
        if head != "OBS" or int(c[4], 16) != 0x562590 or words[0] != 0x5BE284 or words[1] != ITEM:
            return "idfn %s" % head
        return None
    if f == "cube":
        if m["utype"] != 0:
            return None if ret() == 0 else "cube non-player %s" % head
        b = m["busy"]
        if b == "no":
            want = (0x554120, 0x5BF141, (USER, 4, m["guid"]))
        elif b == "stash":
            want = (0x554190, 0x5BF106, (USER,))
        else:
            return None if ret() == 0 else "cube busy %s" % head
        if head != "OBS" or int(c[4], 16) != want[0] or words[0] != want[1] or words[1:1 + len(want[2])] != want[2]:
            return "cube %s %s" % (head, want)
        return None
    if f == "dispatch":
        return cmp_dispatch(m, c, words, dumps, ret())
    if f == "key":
        for a_, is_key, page, q in m["keys"]:
            if is_key and page == 0:
                if head != "OBS":
                    return "key expected boundary, %s" % head
                pc = int(c[4], 16)
                if q - 1 > 0:
                    return None if pc == F_ADD and words[0] == 0x55F1F0 and words[1:5] == (a_, 70, M32, 0) else "key add %x" % pc
                return None if pc == 0x55E000 else "key remove %x" % pc
        return None if ret() == 0 else "key none %s" % head
    return "unmodelled family"


def cmp_dispatch(m, c, words, dumps, ret):
    head = c[3]
    if m["nouser"] or m["utype"] not in (0, 1) or m["noitem"] or m["itype"] != 4:
        return None if ret == 0 else "dispatch refused %s" % head
    sp, skill = m["spell"], M32
    if m["kind"] in ("book", "scroll") and not m["missing"]:
        skill = m["bs"]
        if m["bookspell"] > 0:
            sp = m["bookspell"]
    if inv.i32(sp) < 1 or sp >= 31 or sp not in USE_ENTRIES:
        return None if ret == 0 else "dispatch no entry %s" % head
    if head != "OBS":
        return "dispatch expected boundary, %s" % head
    pc = int(c[4], 16)
    flags = struct.unpack("<I", dict(dumps)[IDATA + 0x18])[0]
    if sp == 1 and not m["flag4"]:
        if pc != 0x5BE130 or words[0] != 0x5BF320 or words[1:6] != (ITEM, 0, m["x"], m["y"], skill):
            return "dispatch test %x %s" % (pc, words[:6])
        return None
    if pc != USE_ENTRIES[sp] or words[0] != 0x5BF38A or words[1:6] != (ITEM, m["arg2"], m["x"], m["y"], skill):
        return "dispatch use %x %s" % (pc, words[:6])
    return None if flags & 4 else "dispatch flag 4 not set"


CONTROLS = ("draw1", "nodraw", "half", "floordiv", "sar", "nocap", "pctflat", "no100")


def control_fails(m, c, a, dumps, ctl):
    """True when the control's reading fails this case that the model passes."""
    if ctl in ("draw1", "nodraw", "half"):
        return m["f"] == "stat3" and cmp_stat(m, c, a, dumps, ctl) is not None
    if ctl == "sar":
        if m["f"] != "classmul" or m["null"] or m["typ"] != 0 or m["cls"] not in (0, 3, 6):
            return False
        return inv.tdiv(m["v"] * 3, 2) != inv.i32((m["v"] >> 1) + m["v"])
    if not m["f"].startswith("stat"):
        return False
    r, _ = model_stat(m)
    words = struct.unpack("<16I", a) if a else None
    if ctl == "floordiv" and r[0] == "setstat":
        d = m["u"]
        rem = inv.i32(d["slist"]["end"] - m["frame"])
        s = r[1]
        base = d["slist"]["base"].get(s, 0)
        ln = m["rec"]["len"]
        amt = r[2]
        n = inv.i32(words[3])
        # the numerator's floor differs from truncation exactly when the rate is negative and inexact
        return r[2] < 0 and (r[2] * (ln + rem) != 0) and floor_rate(m) != r[2]
    if ctl == "nocap" and r[0] == "addstat":
        s = r[1]
        return m["entry"] != 4 and s in MAXOF and r[2] != uncapped(m, s)
    if ctl == "pctflat" and m["entry"] == 5 and r[0] == "addstat":
        slot = [x for x in m["rec"]["slots"] if x[0] == r[1]]
        return slot and r[2] != slot[-1][1]
    if ctl == "no100" and m["entry"] == 5 and r[0] == "addstat":
        slot = [x for x in m["rec"]["slots"] if x[0] == r[1]]
        s = r[1]
        if not slot or slot[-1][1] != 100 or s not in MAXOF:
            return False
        top = m["u"]["stats"].get(MAXOF[s], 0)
        return inv.muldiv(top, 100, 100) != top
    return False


def floor_rate(m):
    d = m["u"]
    rem = inv.i32(d["slist"]["end"] - m["frame"])
    r, _ = model_stat(m)
    s = r[1]
    base = d["slist"]["base"].get(s, 0)
    ln = m["rec"]["len"]
    u = inv.Unit(d["type"], d["cls"], d["uid"], d["low"], d["high"], d["stats"], d["slist"], d["golem"])
    calc = [x[1] for x in m["rec"]["slots"] if x[0] == s][-1]
    # recover v from the model
    for k, (s2, calc2) in enumerate(m["rec"]["slots"]):
        if s2 < 0:
            continue
        v = inv.potion_scale(u, s2, calc2) if m["entry"] == 3 else (inv.i32(calc2 << 8) if s2 in (26, 74) else calc2)
        if k == 1:
            break
    shift = m["rec"]["isc"][s][0]
    v = inv.i32(v << (shift & 31))
    return (inv.i32(base * rem) + v) // (ln + rem)


def uncapped(m, s):
    if m["entry"] == 5:
        pct = [x for x in m["rec"]["slots"] if x[0] == s][0][1]
        top = m["u"]["stats"].get(MAXOF[s], 0)
        return top if pct == 100 else inv.muldiv(top, pct, 100)
    d = m["u"]
    u = inv.Unit(d["type"], d["cls"], d["uid"], d["low"], d["high"], d["stats"], None, d["golem"])
    calc = [x[1] for x in m["rec"]["slots"] if x[0] == s][0]
    v = inv.potion_scale(u, s, calc)
    return inv.i32(v << (m["rec"]["isc"][s][0] & 31))


# every traced read lies in the image's constant data or the code's own switch tables, each named here
ACCOUNTED = (((0x552F9C,), 0x006E10E0, 0x006E10F4, "the unit-type hash offsets"),
             ((0x5BE4E8, 0x5BE4EF), 0x005BE74C, 0x005BE7A5, "entry 3's switch tables"),
             ((0x5BF2D3,), 0x0074178C, 0x00741790, "the entry count"),
             ((0x5BF2DB, 0x5BF313, 0x5BF355, 0x5BF37F), 0x00741790, 0x00741888, "g_ItemUseFns"),
             ((0x624EFC, 0x624F9F, 0x629C0B), 0x006CE200, 0x006CE300, "the bit masks"),
             ((0x627C57,), 0x00744600, 0x00744700, "the calc function count"),
             ((0x62A5EC, 0x62A5F3), 0x0062A60C, 0x0062A61F, "the life multiplier's switch"),
             ((0x62A63C, 0x62A643), 0x0062A65C, 0x0062A66F, "the mana multiplier's switch"),
             ((0x6C0C07,), 0x006C1100, 0x006C1200, "the evaluator's switch"))


def accounted(k):
    f, kind, pc, addr, size = k
    if kind != "R":
        return False
    return any(pc in pcs and lo <= addr < hi for pcs, lo, hi, _ in ACCOUNTED)


def cmd_check(d):
    total = bad = stops = 0
    ctl_fail = {c: 0 for c in CONTROLS}
    reads = {}
    boundaries = {}
    for f in FAMILIES:
        path = os.path.join(d, f + ".out")
        if not os.path.exists(path):
            print("MISSING", f)
            bad += 1
            continue
        cases, tail = parse_out(path)
        ms = metas(f)
        if len(cases) != len(ms):
            print("COUNT", f, len(cases), len(ms))
            bad += 1
        fam_bad = 0
        for m, r in zip(ms, cases):
            total += 1
            c = r["c"]
            if c[3] == "STOP":
                stops += 1
            why = cmp_case(m, c, r.get("a"), r["d"])
            key = (f, c[4] if c[3] == "OBS" else "ret")
            boundaries[key] = boundaries.get(key, 0) + 1
            if why:
                fam_bad += 1
                if fam_bad <= 4:
                    print("MISMATCH", f, c[1], why, " ".join(c[3:6])[:80])
            elif r.get("a") or c[3] != "STOP":
                for ct in CONTROLS:
                    if control_fails(m, c, r.get("a"), r["d"], ct):
                        ctl_fail[ct] += 1
        bad += fam_bad
        for kind in ("R", "W"):
            for pc, addr, size, count in tail[kind]:
                reads.setdefault((f, kind, pc, addr, size), 0)
                reads[(f, kind, pc, addr, size)] += count
        print("family %-9s cases %5d mismatches %d" % (f, len(ms), fam_bad))
    print("total cases %d mismatches %d stops %d" % (total, bad, stops))
    print("controls failing cases:", " ".join("%s=%d" % kv for kv in ctl_fail.items()))
    for k in sorted(boundaries):
        print("boundary %-9s %s %d" % (k[0], k[1], boundaries[k]))
    un = [k for k in sorted(reads) if not accounted(k)]
    print("traced accesses outside the declared memory: %d, unaccounted %d" % (len(reads), len(un)))
    for k in un:
        print("  UNACCOUNTED %s %s pc=%06x addr=%08x size=%d count=%d" % (k[0], k[1], k[2], k[3], k[4], reads[k]))
    seen = {}
    for k in sorted(reads):
        seen.setdefault(k[2], set()).add(k[3] >> 8)
    for pc in sorted(seen):
        print("  read pc=%06x pages %s" % (pc, " ".join("%06x" % x for x in sorted(seen[pc]))))
    return 1 if bad or un else 0


READERS = ("0x11d", "0x130", "0x131", "0x135", "0x136")
GETTERS = {0x00628C20: "useable +0x11D", 0x00621ED0: "+0x130", 0x006297A0: "durwarning +0x135", 0x00629800: "qntwarning +0x136",
           0x0063C830: "the belt query reading +0x11D and +0x130"}
PINS = ((0x5BE4F6, 0x5BE544, "entry 3's scale and draws"), (0x5BE6BF, 0x5BE6C4, "the rate's idiv"),
        (0x5BEBC1, 0x5BEBE6, "entry 5's percent"), (0x5C68C6, 0x5C68E8, "the golem's share"),
        (0x55F1D8, 0x55F1EB, "the key's quantity test"))


def cmd_static(d, exe):
    """Every u8 read of the use columns' offsets in the image, the getters' call sites, the pinned instruction forms."""
    import re
    import subprocess
    txt = subprocess.run(["objdump", "-d", "-M", "intel", exe], capture_output=True, text=True).stdout.splitlines()
    out = []
    for o in READERS:
        pat = re.compile(r"BYTE PTR \[[a-z0-9*+]*\+%s\]" % o)
        hits = [ln.split("\t")[0].strip().rstrip(":") for ln in txt if pat.search(ln)]
        out.append("u8 readers of +%s: %d: %s" % (o, len(hits), " ".join(hits)))
    for a, name in sorted(GETTERS.items()):
        pat = "call   0x%x" % a
        hits = [ln.split("\t")[0].strip().rstrip(":") for ln in txt if ln.rstrip().endswith(pat)]
        out.append("calls of %08x (%s): %d: %s" % (a, name, len(hits), " ".join(hits)))
    for lo, hi, name in PINS:
        out.append("# %s" % name)
        for ln in txt:
            f = ln.split("\t")
            try:
                a = int(f[0].strip().rstrip(":"), 16)
            except ValueError:
                continue
            if lo <= a <= hi and len(f) > 2:
                out.append("%x %s" % (a, f[2].strip()))
    open(os.path.join(d, "static.txt"), "w").write("\n".join(out) + "\n")
    print("\n".join(out[:len(READERS) + len(GETTERS)]))


def cmd_manifest(d, write):
    lines = []
    for n in sorted(os.listdir(d)):
        if n.startswith("manifest") or os.path.isdir(os.path.join(d, n)):
            continue
        lines.append("%s  %s" % (hashlib.sha256(open(os.path.join(d, n), "rb").read()).hexdigest(), n))
    text = "\n".join(lines) + "\n"
    if write:
        open(os.path.join(d, "manifest.txt"), "w").write(text)
    print(text, end="")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("cases", "check", "manifest", "static"))
    ap.add_argument("--dir", default="workspace/logs/r60a/emu")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    if a.cmd == "cases":
        cmd_cases(a.dir)
    elif a.cmd == "check":
        sys.exit(cmd_check(a.dir))
    elif a.cmd == "static":
        cmd_static(a.dir, "workspace/install/app/game.exe")
    else:
        cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Plan 0060 P1.3 (`lane/r60c`): the ground drop's cell search, ground expiry, the sweep's test, pickup's distance and line ends, the
packet gate, under Ghidra's p-code emulator (ADR-0015, ADR-0021), compared with tools/item_inventory.py. No game run, no slot.

    python3 -I tools/item_emu3.py cases --dir D      write D/<family>.cases, .mem, .meta
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/item_emu3.py check --dir D      compare, account for each traced access, run the controls, count outcomes
    python3 -I tools/item_emu3.py static --dir D     each call site's arguments, the expiry's writers, the field file's table check
    python3 -I tools/item_emu3.py manifest --dir D [--write]

Every case draw comes from random.Random("r60c-<family>"). A case is a declared scratch image; no instruction is patched.
drop, line, expiry, ground, dist and dispatch run to the function's return (dispatch to the call of the handler's pointer test);
sweep ends at the first unit reached (UnitGetRoom), los at COLL_LineTest or UNIT_CollUnmark (ADR-0021).

The search allocates its 8-byte field state from the shared pool. The pool's page is declared (data only), and the two lock imports'
table slots hold 0x0066A250, a `ret 4` of the image, so the allocator's own code runs unpatched on a declared page; what the locks
do is not evidenced. The field file's bytes are loaded as the game's loader leaves them (the file past its 10-byte header).

Controls (a wrong reading; `check` prints how many cases each fails, 0 means the run cannot separate it):
  drop: noline nooffset offset32 first leq capsfirst noitembit linecellmask r48 r50 alwaysfallback linediag lineorigin lineroom0 fixedbase
  line: linediag lineorigin lineall (cell mask ignored)    expiry: q4eq45 goldgeq fillerplain
  sweep: ltframe zerofrees                dist: plainmanh sizeless        los: swapsizes noshorten    dispatch: nogate noexempt
"""
import argparse
import hashlib
import json
import os
import random
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import item_inventory as inv  # noqa: E402
from party_emu import parse_out  # noqa: E402
from use_emu import Case, le32, put_stats  # noqa: E402

M32 = 0xFFFFFFFF
FIELD_FILE = "workspace/merged/data/global/expfield.d2"
EXE = "workspace/install/app/game.exe"
DTBL, ISC, RECS, TYPEBITS = 0x10010000, 0x10030000, 0x10060000, 0x10190000
ROOMS, MAPS, CELLS = 0x10400000, 0x10500000, 0x10600000
FIELDB, POSB, OUTB, STATE = 0x10300000, 0x10200000, 0x10200100, 0x10201000
POOLPAGE, POOLBITS, POOLMEM = 0x10202000, 0x10202100, 0x10202200
GAME, UNITA, UNITB, DATAA, DATAB, PATHA, PATHB = 0x10210000, 0x10220000, 0x10221000, 0x10222000, 0x10223000, 0x10224000, 0x10225000
ACT, SL1, PKT = 0x10226000, 0x10227000, 0x10228000
ITEMS0, IDATA0 = 0x10230000, 0x10240000
F_DROP, F_LINE, F_EXP, F_GROUND, F_SWEEP, F_DIST, F_LOS, F_DISP = (0x00555DA0, 0x0066A670, 0x00558A10, 0x00558AA0, 0x00558B90, 0x00641530,
                                                                  0x00622B50, 0x0054D750)
O_ROOM, O_LINE, O_UNMARK, O_BADPTR = 0x00620BB0, 0x0064E260, 0x00649560, 0x0054D7DC
GUARDS = (0x00408A60, 0x00681E09, 0x0040B4B0)
PTABLE = 0x006E0D18
A_BITS, OTHER_BITS = (0x1, 0x200, 0x400, 0x800, 0x1000, 0x2000), (0x2, 0x4, 0x8, 0x10, 0x20, 0x40, 0x80, 0x100, 0x4000, 0x8000)
LINE_BITS = (0x1, 0x800)
FAMILIES = ("drop", "line", "expiry", "ground", "sweep", "dist", "los", "dispatch")
COUNTS = dict(drop=4000, line=800, expiry=600, ground=200, sweep=600, dist=1500, los=600, dispatch=0)
CONTROLS = dict(drop=("noline", "nooffset", "offset32", "first", "leq", "capsfirst", "noitembit", "linecellmask", "r48", "r50",
                      "alwaysfallback", "linediag", "lineorigin", "lineroom0", "fixedbase"),
                line=("linediag", "lineorigin", "lineall"), expiry=("q4eq45", "goldgeq", "fillerplain"),
                sweep=("ltframe", "zerofrees"), dist=("plainmanh", "sizeless"), los=("swapsizes", "noshorten"),
                dispatch=("nogate", "noexempt"))


def field_bytes():
    return open(FIELD_FILE, "rb").read()[10:]


def va2off(exe, va):
    pe = struct.unpack_from("<I", exe, 0x3C)[0]
    n = struct.unpack_from("<H", exe, pe + 6)[0]
    o = struct.unpack_from("<H", exe, pe + 20)[0]
    for i in range(n):
        vs, ra, sz, ptr = struct.unpack_from("<IIII", exe, pe + 24 + o + 40 * i + 8)
        if ra <= va - 0x400000 < ra + sz:
            return ptr + va - 0x400000 - ra
    return None


def exe_table():
    exe = open(EXE, "rb").read()
    return (list(struct.unpack_from("<64i", exe, va2off(exe, 0x006EB180))),
            [struct.unpack_from("<I", exe, va2off(exe, PTABLE + 8 * i))[0] != 0 for i in range(0x67)])


# ------------------------------------------------------------------ the world


def room_addr(k):
    return ROOMS + k * 0x200


def put_world(c, rooms):
    """rooms: list of dicts x y w h near(list of indices or None) cells({(x,y):v}) nomap(0 none, 1 no map, 2 map without cells)."""
    for k, r in enumerate(rooms):
        a, m, cl = room_addr(k), MAPS + k * 0x100, CELLS + k * 0x80000
        c.d32(a + 0x4C, r["x"])
        c.d32(a + 0x50, r["y"])
        c.d32(a + 0x54, r["w"])
        c.d32(a + 0x58, r["h"])
        c.d32(a, a + 0x100)
        c.d32(a + 0x24, len(r["near"]))
        if r["near"]:
            c.put(a + 0x100, b"".join(le32(0 if n is None else room_addr(n)) for n in r["near"]))
        c.d32(a + 0x20, 0 if r["nomap"] == 1 else m)
        c.d32(m, r["x"])
        c.d32(m + 4, r["y"])
        c.d32(m + 8, r["w"])
        c.d32(m + 0x20, 0 if r["nomap"] == 2 else cl)
        if r["nomap"] != 2:
            buf = bytearray(2 * r["w"] * r["h"])
            for (x, y), v in r["cells"].items():
                struct.pack_into("<H", buf, 2 * ((y - r["y"]) * r["w"] + x - r["x"]), v)
            c.put(cl, bytes(buf))


def jsonable(rooms):
    return [dict(r, cells=[[x, y, v] for (x, y), v in r["cells"].items()]) for r in rooms]


def model_rooms(rooms):
    out = [inv.Room(r["x"], r["y"], r["w"], r["h"], None if r["nomap"] else {(x, y): v for x, y, v in r["cells"]}) for r in rooms]
    for o, r in zip(out, rooms):
        o.near = [None if n is None else out[n] for n in r["near"]]
    return out


def noise(rnd, density, a_bits=A_BITS):
    """A cell's flags: non-zero under the search's masks with `density`, always possibly with bits no mask reads."""
    v = 0
    if rnd.random() < density:
        v |= rnd.choice(a_bits)
    if rnd.random() < 0.3:
        v |= rnd.choice(OTHER_BITS)
    return v


def fill(rnd, r, density, a_bits=A_BITS):
    for y in range(r["y"], r["y"] + r["h"]):
        for x in range(r["x"], r["x"] + r["w"]):
            v = noise(rnd, density, a_bits)
            if v:
                r["cells"][(x, y)] = v


def new_room(x, y, w, h):
    return dict(x=x, y=y, w=w, h=h, near=[], cells={}, nomap=0)


def gen_drop(rnd, i):
    c = Case()
    px, py = rnd.randrange(3000, 9000), rnd.randrange(3000, 9000)
    fallback = 1 if i % 4 else 0
    kind = ("open", "crowded", "pile", "walls", "edge", "rooms", "nomap", "wedge", "detached")[i % 9] if i >= 36 else "far"
    if kind == "far":
        # one free cell at the given ring, or none: the ring's bound. A strip of 8 x 121 holding the position, or (the first six) the
        # whole square, every cell with the item bit, so that the walk back to the position stays in the room and passes
        ring = (47, 48, 49, 50, 51, None)[i % 6]
        sx, sy = px + 2, py + 3
        if i < 6:
            r0 = new_room(px - 58, py - 57, 121, 121)
        elif i % 2:
            r0 = new_room(px - 58, py - 1, 121, 8)
        else:
            r0 = new_room(px - 1, py - 57, 8, 121)
        for y in range(r0["y"], r0["y"] + r0["h"]):
            for x in range(r0["x"], r0["x"] + r0["w"]):
                r0["cells"][(x, y)] = 0x200
        if ring:
            on = [p for p in inv.ring_cells(sx, sy, ring) if r0["x"] <= p[0] < r0["x"] + r0["w"] and r0["y"] <= p[1] < r0["y"] + r0["h"]]
            r0["cells"][rnd.choice(on)] = 0
        rooms = [r0]
    else:
        w, h = rnd.randrange(6, 41), rnd.randrange(6, 41)
        ox = rnd.randrange(0, w)
        oy = rnd.randrange(0, h)
        if kind == "edge":
            ox, oy = (w - 1 - rnd.randrange(0, 2), oy) if rnd.random() < 0.5 else (ox, h - 1 - rnd.randrange(0, 3))
        r0 = new_room(px - ox, py - oy, w, h)
        if kind == "detached":     # the position and its offset cell in no room the first room can see, or a null first room
            r0 = new_room(px + rnd.randrange(6, 20), py + rnd.randrange(6, 20), w, h)
        rooms = [r0]
        if kind in ("rooms", "wedge", "nomap") or rnd.random() < 0.3:
            for (dx, dy, nw, nh) in rnd.sample(((w, 0, 12, h), (-12, 0, 12, h), (0, h, w, 12), (0, -12, w, 12)), rnd.randrange(1, 5)):
                rooms.append(new_room(r0["x"] + dx, r0["y"] + dy, nw, nh))
        dens = dict(open=0.05, crowded=0.75, pile=0.0, walls=0.0, edge=0.3, rooms=0.5, nomap=0.5, wedge=0.0, detached=0.1)[kind]
        for r in rooms:
            fill(rnd, r, dens)
        if kind == "pile":     # a pile of ground items: the cell bit only, lines pass
            for r in rooms:
                fill(rnd, r, rnd.choice((0.5, 0.9, 0.99)), (0x200,))
        if kind in ("walls", "wedge"):     # straight blocks of a line-mask bit, so free cells have blocked lines
            for r in rooms:
                for _ in range(rnd.randrange(1, 7)):
                    b = rnd.choice(LINE_BITS)
                    x0, y0 = rnd.randrange(r["x"], r["x"] + r["w"]), rnd.randrange(r["y"], r["y"] + r["h"])
                    for t in range(rnd.randrange(2, 12)):
                        x, y = (x0 + t, y0) if rnd.random() < 0.5 else (x0, y0 + t)
                        if r["x"] <= x < r["x"] + r["w"] and r["y"] <= y < r["y"] + r["h"]:
                            r["cells"][(x, y)] = r["cells"].get((x, y), 0) | b
        if kind == "nomap":
            rooms[rnd.randrange(0, len(rooms))]["nomap"] = rnd.choice((1, 2))
        n = len(rooms)
        for k, r in enumerate(rooms):
            others = [j for j in range(n) if j != k]
            rnd.shuffle(others)
            # the near list: all, or some (a line then leaves what the candidate's room can see), sometimes with itself or a null entry
            keep = others if rnd.random() < 0.5 else others[:rnd.randrange(0, n)]
            r["near"] = list(keep)
            if rnd.random() < 0.2:
                r["near"].insert(rnd.randrange(0, len(r["near"]) + 1), k)
            if rnd.random() < 0.1:
                r["near"].insert(rnd.randrange(0, len(r["near"]) + 1), None)
    put_world(c, rooms)
    c.put(POSB, le32(px) + le32(py))
    c.put(OUTB, le32(0x55555555) + le32(0x55555555))
    c.lines.append("s %08x 16" % POOLMEM)
    c.dump(OUTB, 8)
    null_room = kind == "detached" and i % 5 == 0
    meta = dict(f="drop", px=px, py=py, fallback=fallback, rooms=jsonable(rooms), kind=kind, null=null_room)
    return c.call(F_DROP, 0 if null_room else room_addr(0), POSB, OUTB, 1, fallback), meta


def gen_line(rnd, i):
    c = Case()
    ox, oy = rnd.randrange(3000, 9000), rnd.randrange(3000, 9000)
    span = 127 if i % 5 == 0 else rnd.choice((3, 6, 12, 30, 52))
    x, y = ox + rnd.randrange(-span, span + 1), oy + rnd.randrange(-span, span + 1)
    if i < 16:
        x, y = (ox, oy) if i < 2 else (x, y)
    x0, y0 = min(x, ox) - 2, min(y, oy) - 2
    r = new_room(x0, y0, abs(x - ox) + 5, abs(y - oy) + 5)
    mask = rnd.choice((0x801, 0x801, 0x3E01, 0xFFFF))
    dens = rnd.choice((0.0, 0.01, 0.03, 0.1, 0.3))
    fill(rnd, r, dens, LINE_BITS + (0x200,))
    put_world(c, [r])
    c.put(STATE, le32(ox) + le32(oy))
    null_room = i % 37 == 0
    meta = dict(f="line", ox=ox, oy=oy, x=x, y=y, mask=mask, rooms=jsonable([r]), null=null_room)
    return c.call(F_LINE, 0, 0, STATE, 0 if null_room else room_addr(0), x, y, mask), meta


def put_item(c, base, data, row, quality, typ, type2=0, quest=0, gold=None, mode=3):
    r = RECS + row * 0x1A8
    c.d32(base, 4)
    c.d32(base + 4, row)
    c.d32(base + 0x10, mode)
    c.d32(base + 0x14, data)
    c.d32(data, quality)
    c.d16(r + 0x11E, typ)
    c.d16(r + 0x120, type2)
    c.d8(r + 0x12A, quest)
    c.d32(base + 0x5C, SL1 if gold is not None else 0)
    if gold is not None:
        put_stats(c, SL1, SL1 + 0x80, {14: gold})


def set_filler_bit(c, typ, on):
    """ITEMS_UnitIsType's bit array: one u32 per row of 2 words; type 0x35 is word 1, bit 21."""
    c.d32(TYPEBITS + 4 * (typ * 2 + 1), (1 << 21) if on else 0)


def gen_expiry(rnd, i):
    c = Case()
    frame = rnd.choice((0, 1, 1500, rnd.randrange(0, 2000000), 0x7FFFFFFF - rnd.randrange(0, 40000)))
    quest = 1 if i % 10 == 0 else 0
    quality = i % 13 if i < 200 else rnd.choice((1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
    base = rnd.choice((4, 4, 7, 9, 0x35, 20))
    gold = rnd.choice((0, 1, 9999, 10000, 10001, 10002, 2000000000, -1, rnd.randrange(0, 50000)))
    filler_bit = rnd.random() < 0.4
    use2 = rnd.random() < 0.3
    typ, type2 = (9, base) if use2 and base != 4 else (base, 0)
    for t in (typ, type2):
        set_filler_bit(c, t, False)
    if filler_bit:
        set_filler_bit(c, type2 if use2 and base != 4 else typ, True)
    put_item(c, UNITA, DATAA, 7, quality, typ, type2, quest, gold if typ == 4 else None)
    c.d32(GAME + 0xA8, frame)
    meta = dict(f="expiry", frame=frame, quest=quest, quality=quality, base=typ, gold=gold, filler=filler_bit)
    return c.call(F_EXP, GAME, UNITA), meta


def gen_ground(rnd, i):
    c = Case()
    px, py = rnd.randrange(3000, 9000), rnd.randrange(3000, 9000)
    r = new_room(px - 5, py - 5, 12, 12)
    r["cells"][(px, py)] = rnd.choice((0, 0x1000, 0x8000))
    put_world(c, [r])
    quality = rnd.choice((2, 3, 4, 5, 7))
    mode0 = rnd.choice((3, 4))
    put_item(c, UNITA, DATAA, 7, quality, 9, 0, 0, None, mode0)
    set_filler_bit(c, 9, False)
    frame = rnd.randrange(0, 2000000)
    c.d32(GAME + 0xA8, frame)
    c.d32(UNITA + 0x2C, PATHA)
    c.d32(UNITA + 0xC4, rnd.choice((0, 0x40, 0x10)))
    c.d32(UNITA + 0xE8, 0)
    c.d32(room_addr(0) + 0x74, 0)
    c.d32(room_addr(0) + 0x34, 4)        # the room's flag 4: UnitMarkUpdated's list is not entered (0x0061AB60), not part of the claim
    c.d32(DATAA + 0x24, 0x55555555)
    null_room = i % 20 == 0
    m = MAPS
    for a, n in ((UNITA, 0x100), (DATAA, 0x100), (PATHA, 0x40), (room_addr(0), 0x100)):
        c.lines.append("s %08x %d" % (a, n))
    c.dump(UNITA + 0x10, 4)
    c.dump(UNITA + 0xC4, 4)
    c.dump(DATAA + 0x24, 4)
    c.dump(PATHA, 0x20)
    c.dump(CELLS + 2 * ((py - r["y"]) * r["w"] + px - r["x"]), 2)
    meta = dict(f="ground", px=px, py=py, frame=frame, quality=quality, cell0=r["cells"][(px, py)], null=null_room, mode0=mode0,
                flags0=None)
    meta["c4"] = None
    return c.call(F_GROUND, GAME, 0, UNITA, 0 if null_room else room_addr(0), px, py), meta


def gen_sweep(rnd, i):
    c = Case()
    frame = rnd.choice((1500, 3000, 15000, rnd.randrange(1, 2000000) * 1500 & 0x7FFFFFFF))
    c.d32(GAME + 0xA8, frame)
    act = rnd.randrange(0, 5)
    c.d32(GAME + 0xBC + 4 * act, ACT)
    nrooms = rnd.randrange(0, 4)
    c.d32(ACT + 0x10, room_addr(0) if nrooms else 0)
    items, n = [], 0
    for k in range(nrooms):
        ra = room_addr(k)
        c.d32(ra + 0x7C, room_addr(k + 1) if k + 1 < nrooms else 0)
        m = rnd.randrange(0, 5)
        first = ITEMS0 + n * 0x200 if m else 0
        c.d32(ra + 0x74, first)
        for j in range(m):
            u, d = ITEMS0 + n * 0x200, IDATA0 + n * 0x100
            typ = rnd.choice((4, 4, 4, 4, 1, 0, 2))
            exp = rnd.choice((0, frame, frame + 1, frame - 1, frame + 15000, -5, 0x7FFFFFFF, 1))
            exp = inv.i32(exp)
            c.d32(u, typ)
            c.d32(u + 0x14, d)
            c.d32(d + 0x24, exp & M32)
            c.d32(u + 0xE8, ITEMS0 + (n + 1) * 0x200 if j + 1 < m else 0)
            items.append((typ, exp))
            n += 1
    meta = dict(f="sweep", frame=frame, items=items)
    return c.call(F_SWEEP, GAME, act), meta


def put_pos_unit(c, u, d, p, typ, x, y, size):
    c.d32(u, typ)
    c.d32(u + 0x14, d)
    c.d32(u + 0x2C, p)
    if typ in (2, 4):
        c.d32(p + 0xC, x)
        c.d32(p + 0x10, y)
        if typ == 2:
            c.d32(d, d + 0x100)
            c.d32(d + 0x100 + 0xD0, size)
            c.lines.append("s %08x 512" % (d + 0x100))      # the object record, zero but for its size: mask 0x400 (0x006209D0)
    else:
        c.d16(p + 2, x)
        c.d16(p + 6, y)


def size_of(typ, sz):
    return {0: 2, 4: 1, 2: sz}[typ]


def gen_dist(rnd, i):
    c = Case()
    ta, tb = (0, 4) if i < 700 else (rnd.choice((0, 2, 4)), rnd.choice((0, 2, 4)))
    sa, sb = rnd.randrange(0, 7), rnd.randrange(0, 7)
    ax, ay = rnd.randrange(3000, 9000), rnd.randrange(3000, 9000)
    if i < 225:
        dx, dy = i % 15 - 7, i // 15 - 7
    else:
        span = rnd.choice((4, 8, 9, 16, 60))
        dx, dy = rnd.randrange(-span, span + 1), rnd.randrange(-span, span + 1)
    put_pos_unit(c, UNITA, DATAA, PATHA, ta, ax, ay, sa)
    put_pos_unit(c, UNITB, DATAB, PATHB, tb, ax + dx, ay + dy, sb)
    meta = dict(f="dist", ax=ax, ay=ay, bx=ax + dx, by=ay + dy, sa=size_of(ta, sa), sb=size_of(tb, sb), ta=ta, tb=tb)
    return c.call(F_DIST, 0, 0, UNITA, UNITB), meta


def gen_los(rnd, i):
    c = Case()
    ta, tb = (0, 4) if i < 300 else (rnd.choice((0, 2, 4)), rnd.choice((0, 2, 4)))
    sa, sb = rnd.randrange(0, 5), rnd.randrange(0, 5)
    ax, ay = rnd.randrange(3000, 9000), rnd.randrange(3000, 9000)
    span = rnd.choice((1, 2, 3, 5, 9, 40))
    bx, by = ax + rnd.randrange(-span, span + 1), ay + rnd.randrange(-span, span + 1)
    put_pos_unit(c, UNITA, DATAA, PATHA, ta, ax, ay, sa)
    put_pos_unit(c, UNITB, DATAB, PATHB, tb, bx, by, sb)
    # the room comes from the first unit's path; the player's mask from its path
    c.d32(PATHA + 0x00 if ta in (2, 4) else PATHA + 0x1C, room_addr(0))
    pm = rnd.choice((0x80, 0x100, 0x80, 0x100, 0x1C00, 0x804, 0x4))
    if ta == 0:
        c.d32(PATHA + 0x4C, pm)
    if tb == 0:
        c.d32(PATHB + 0x4C, pm)
    mask = rnd.choice((0x804, 0x804, 0x804, 0x200, 0xFFFF))
    meta = dict(f="los", ax=ax, ay=ay, bx=bx, by=by, sa=size_of(ta, sa), sb=size_of(tb, sb), ta=ta, tb=tb, pm=pm, mask=mask)
    return c.call(F_LOS, 0, 0, UNITA, UNITB, mask), meta


def gen_dispatch_all():
    out, metas = [], []
    for op in list(range(0, 0x69)) + [0x80, 0xFF]:
        for mode, st in ((1, 0), (0, 0), (0x11, 0), (6, 1)):
            c = Case()
            c.d32(UNITA, 0)
            c.d32(UNITA + 0x10, mode)
            c.d8(PKT, op)
            c.d32(GAME + 0x1DC4, 0)
            c.d32(DTBL + 0xC4, 200)
            # the state bit array UNIT_TestStateBit reads, word 1 for state 54
            c.d32(UNITA + 0x5C, SL1)
            c.d32(SL1 + 0x10, 0x80000000)
            c.d32(SL1 + 0x58, SL1 + 0x100)
            c.d32(SL1 + 0x104, (1 << 22) if st else 0)
            out.append(c.call(F_DISP, GAME, UNITA, PKT, 4))
            metas.append(dict(f="dispatch", op=op, mode=mode, st=st))
    return out, metas


GEN = dict(drop=gen_drop, line=gen_line, expiry=gen_expiry, ground=gen_ground, sweep=gen_sweep, dist=gen_dist, los=gen_los)
OBSERVES = dict(sweep=(O_ROOM,), los=(O_LINE, O_UNMARK), dispatch=(O_BADPTR,))
FIELD_FAMS = ("drop", "line")


def mem_spec(f):
    out = ["# plan 0060 P1.3: the fixed part of the image", "dword 00744304 %08x" % DTBL,
           "dword %08x %08x" % (DTBL + 0xBD4, 400), "dword %08x %08x" % (DTBL + 0xBCC, ISC),
           "dword %08x %08x" % (DTBL + 0xBFC, 64), "dword %08x %08x" % (DTBL + 0xBF8, ISC + 0x40000),
           "dword %08x %08x" % (DTBL + 0xC00, 2), "dword %08x %08x" % (DTBL + 0xC04, TYPEBITS),
           "dword 0096ca58 00000097", "dword 0096ca5c %08x" % RECS]
    if f in FIELD_FAMS:
        out += ["const load %08x %s" % (FIELDB, os.path.abspath(FIELD_FILE)), "dword 0096d654 %08x" % (FIELDB + 10), "dword 0096d664 00000080",
                "dword 0096d668 00000080"]
    if f == "drop":
        # the shared pool's first bucket, one page, nothing used; the two lock imports' slots hold a `ret 4` of the image
        pool = 0x0074F104
        b = pool + 0x20
        out += ["dword 0074f0e8 00000001", "dword %08x 00000000" % pool, "dword %08x 00000001" % (pool + 0x1C), "dword %08x 00000010" % (b + 0x18),
                "dword %08x 00000020" % (b + 0x1C), "dword %08x %08x" % (b + 0x28, POOLPAGE), "dword %08x %08x" % (b + 0x2C, POOLPAGE),
                "dword %08x %08x" % (POOLPAGE, POOLMEM), "dword %08x %08x" % (POOLPAGE + 4, POOLBITS), "dword %08x 00000000" % (POOLPAGE + 8),
                "dword %08x 00000000" % (POOLPAGE + 0xC), "dword %08x 00000000" % (POOLPAGE + 0x10), "dword %08x %08x" % (POOLPAGE + 0x14, b),
                "dword %08x 00000000" % POOLBITS, "dword 006cc218 0066a250", "dword 006cc214 0066a250",
                "dword %08x 00000001" % (pool + 0x7A0), "dword %08x %08x" % (pool + 0x7A8, POOLPAGE + 0x20),
                "dword %08x %08x" % (POOLPAGE + 0x20, POOLPAGE), "dword %08x %08x" % (POOLPAGE + 0x24, POOLMEM)]
    out += ["guard %08x" % g for g in GUARDS + (() if f == "drop" else (0x0040B430, 0x0040B480))]
    out += ["observe %08x" % a for a in OBSERVES.get(f, ())]
    return "\n".join(out) + "\n"


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    total = 0
    for f in FAMILIES:
        if f == "dispatch":
            blocks, metas = gen_dispatch_all()
        else:
            rnd = random.Random("r60c-" + f)
            blocks, metas = [], []
            for i in range(COUNTS[f]):
                b, m = GEN[f](rnd, i)
                blocks.append(b)
                metas.append(m)
        total += len(metas)
        open(os.path.join(d, f + ".cases"), "w").write("\n".join(blocks) + "\n")
        open(os.path.join(d, f + ".mem"), "w").write(mem_spec(f))
        json.dump(metas, open(os.path.join(d, f + ".meta"), "w"))
    print("cases written", total)


# ------------------------------------------------------------------ the check


def field(c, name):
    for x in c:
        if x.startswith(name + "="):
            return int(x.split("=")[1], 16)
    return None


def stack_words(a, n):
    return struct.unpack("<%dI" % n, a[:4 * n])


def predict_drop(m, FB, ctl=None):
    rooms = model_rooms(m["rooms"])
    r, x, y = inv.ground_drop_cell(None if m["null"] else rooms[0], m["px"], m["py"], FB, m["fallback"], ctl)
    return (room_addr(rooms.index(r)) if r is not None else 0), x, y


def control_expiry(m, ctl):
    q = m["quality"]
    if ctl == "q4eq45" and q == 4:
        q = 5
    gold = m["gold"]
    if ctl == "goldgeq" and gold == 10000:
        gold = 10001
    return inv.ground_expiry(m["frame"], m["quest"], q, m["base"], gold, m["filler"] and ctl != "fillerplain")


def cmp_case(m, r, FB, TB, PT, ctl=None):
    c, a, dumps = r["c"], r.get("a"), r["d"]
    kind, f = c[3], m["f"]
    eax = field(c, "eax")
    if kind == "STOP":
        return "stop " + " ".join(c[4:8])
    if f == "drop":
        if kind == "OBS":
            return "boundary"
        ra, x, y = predict_drop(m, FB, ctl)
        out = struct.unpack("<II", dumps[0][1])
        if eax != ra:
            return "room %x for %x" % (eax, ra)
        if out != (x, y):
            return "cell %s for %s" % (out, (x, y))
        return None
    if f == "line":
        rooms = model_rooms(m["rooms"])
        room = None if m["null"] else rooms[0]
        if ctl == "lineall":
            want = 0 if room is None else int(any(inv.cell_test(room, cx, cy, 0xFFFF) for cx, cy in inv.line_cells(FB, m["ox"], m["oy"], m["x"], m["y"])))
        else:
            want = inv.line_blocked(FB, m["ox"], m["oy"], room, m["x"], m["y"], m["mask"], ctl)
        return None if eax == want else "line %d for %d" % (eax, want)
    if f == "expiry":
        want = control_expiry(m, ctl) & M32 if ctl else inv.ground_expiry(m["frame"], m["quest"], m["quality"], m["base"], m["gold"], m["filler"]) & M32
        return None if eax == want else "expiry %x for %x" % (eax, want)
    if f == "ground":
        mode, c4, exp, path, cell = dumps[0][1], dumps[1][1], dumps[2][1], dumps[3][1], dumps[4][1]
        if m["null"]:
            return None if struct.unpack("<I", exp)[0] == 0x55555555 else "null room wrote the expiry"
        want = inv.ground_expiry(m["frame"], 0, m["quality"], 9, None, False) & M32
        if struct.unpack("<I", exp)[0] != want:
            return "expiry %s for %x" % (exp.hex(), want)
        if struct.unpack("<I", mode)[0] != 3:
            return "mode %s" % mode.hex()
        fl = struct.unpack("<I", c4)[0]
        if fl & 0x2001002 != 0x2001002:
            return "flags %x" % fl
        w = struct.unpack("<8I", path)
        if (w[0], w[3], w[4]) != (room_addr(0), m["px"], m["py"]):
            return "path %s" % (w,)
        if struct.unpack("<H", cell)[0] != m["cell0"] | 0x200:
            return "cell %s for %x" % (cell.hex(), m["cell0"] | 0x200)
        return None
    if f == "sweep":
        i = inv.sweep_first([tuple(x) for x in m["items"]], m["frame"], ctl)
        if i is None:
            return None if kind != "OBS" else "reached a unit, none expected"
        if kind != "OBS" or int(c[4], 16) != O_ROOM:
            return "no boundary for item %d" % i
        got = stack_words(a, 2)[1]
        return None if got == ITEMS0 + i * 0x200 else "reached %x for %d" % (got, i)
    if f == "dist":
        args = (TB, m["ax"], m["ay"], m["sa"], m["bx"], m["by"], m["sb"])
        if ctl == "plainmanh":
            want = abs(m["ax"] - m["bx"]) + abs(m["ay"] - m["by"])
        elif ctl == "sizeless":
            want = inv.interact_distance(TB, m["ax"], m["ay"], 0, m["bx"], m["by"], 0)
        else:
            want = inv.interact_distance(*args)
        return None if eax == want & M32 else "dist %d for %d" % (eax, want)
    if f == "los":
        sa, sb = (m["sb"], m["sa"]) if ctl == "swapsizes" else (m["sa"], m["sb"])
        ends = inv.line_ends(m["ax"], m["ay"], sa, m["bx"], m["by"], sb)
        if ctl == "noshorten":
            ends = ((m["ax"], m["ay"]), (m["bx"], m["by"]))
        mask_a = {0: m["pm"], 4: 0x200, 2: 0x400}[m["ta"]]
        mask_b = {0: m["pm"], 4: 0x200, 2: 0x400}[m["tb"]]
        if mask_a & m["mask"] or mask_b & m["mask"]:
            return None if kind == "OBS" and int(c[4], 16) == O_UNMARK else "no unmark"
        if ends is None:
            return None if kind != "OBS" and eax == 0 else "touching units reached the line test"
        if kind != "OBS":
            return "no line test"
        w = stack_words(a, 5)
        esp = field(c, "esp")
        def at(ptr):
            o = ptr - esp
            return struct.unpack_from("<II", a, o) if 0 <= o <= len(a) - 8 else None
        if w[1] != room_addr(0) or w[4] != m["mask"]:
            return "line test args %s" % [hex(x) for x in w]
        p1, p2 = at(w[2]), at(w[3])
        if p1 is None or p2 is None:
            return "ends outside the dump"
        return None if (p1, p2) == ends else "ends %s %s for %s" % (p1, p2, ends)
    if f == "dispatch":
        tn = m["op"] <= 0x66 and PT[m["op"]]
        want = inv.dispatch_gate(m["op"], tn, m["mode"], m["st"])
        if ctl == "nogate" and want == "gate":
            want = "handler"
        if ctl == "noexempt" and want == "handler" and m["op"] in (0x14, 0x15, 0x3C, 0x43, 0x66) and (m["mode"] in (0, 0x11) or m["st"]):
            want = "gate"
        if want == "handler":
            return None if kind == "OBS" and int(c[4], 16) == O_BADPTR else "no pointer test"
        ret = {"bad": 3, "gate": 0}[want]
        return None if kind != "OBS" and eax == ret else "ret %s for %d" % (c[3:5], ret)
    return "unknown family"


ACCOUNTED = ((0x0096CA58, 0x0096CA60, "the item table's count and base, spec"),
             (0x00749780, 0x007497C8, "the field's step tables: image data, written by no code but 0x0066A2B0's copies to 0x0096D630"),
             (0x006EB180, 0x006EB280, "the distance table: image data"),
             (0x006CE268, 0x006CE368, "the allocator's and the type test's bit masks: image data"),
             (PTABLE, PTABLE + 0x340, "g_SrvPacketTable: image data"), (0x0054D840, 0x0054D8B0, "the dispatch switch's tables: image data"),
             (0x006E10F8, 0x006E1100, "a string: image data"), (0x006EED30, 0x006EED4C, "a file name: image data"),
             (0x0054D838, 0x0054D840, "the dispatch switch's table, in .text"), (0x00620570, 0x00620590, "UNIT_GetSizeX's switch table, in .text"),
             (0x00620630, 0x00620650, "UNIT_GetSizeY's switch table, in .text"), (0x0064DA20, 0x0064DA40, "CollisionTest's switch table, in .text"),
             (0x00409340, 0x00409350, "0x00409240's table, in .text"), (0x00624680, 0x00624690, "a switch table, in .text"),
             (0x00708000, 0x00708004, "the allocator's pool switch: ANDed with a pool argument of 0, so its value cannot matter here"))


def accounted(k):
    f, kind, pc, addr, size = k
    if kind != "R":
        return False
    return any(lo <= addr < hi for lo, hi, _ in ACCOUNTED)


def outcome(m, r, FB):
    """A label per case: the family's distinct outcomes."""
    c, f = r["c"], m["f"]
    if f == "drop":
        ra, x, y = predict_drop(m, FB)
        sx, sy = m["px"] + 2, m["py"] + 3
        rooms = model_rooms(m["rooms"])
        first = None if m["null"] else rooms[0]
        start = (sx, sy) if inv.room_at(first, sx, sy) is not None else (m["px"], m["py"])
        if ra == 0:
            return "no room, fallback %d" % m["fallback"]
        if (x, y) == start:
            refused = predict_drop(dict(m, fallback=0), FB)[0] == 0
            return ("start+2+3" if start == (sx, sy) else "start=position") + (" fallback on a blocked cell" if refused else "")
        ring = max(abs(x - start[0]), abs(y - start[1]))
        side = "side" if abs(x - start[0]) == ring else "cap"
        return "ring %d %s %s" % (ring, side, "room0" if ra == room_addr(0) else "other room")
    if f == "line":
        return "ret %d" % field(c, "eax")
    if f == "expiry":
        return "add %d" % (inv.i32(field(c, "eax") - m["frame"]) if not m["quest"] else 0) if field(c, "eax") else "zero"
    if f == "ground":
        return "null room" if m["null"] else "placed, mode was %d" % m["mode0"]
    if f == "sweep":
        i = inv.sweep_first([tuple(x) for x in m["items"]], m["frame"])
        return "none" if i is None else "unit %d" % i
    if f == "dist":
        return "d %d" % field(c, "eax")
    if f == "los":
        return "OBS " + c[4] if c[3] == "OBS" else "ret %d" % field(c, "eax")
    if f == "dispatch":
        return "OBS " + c[4] if c[3] == "OBS" else "ret %d" % field(c, "eax")
    return ""


def cmd_check(d):
    FB = field_bytes()
    TB, PT = exe_table()
    total = bad = stops = 0
    ctl_cases, ctl_fail, outs, reads = {}, {}, {}, {}
    print("expfield sha256 " + hashlib.sha256(open(FIELD_FILE, "rb").read()).hexdigest())
    for f in FAMILIES:
        cases, tail = parse_out(os.path.join(d, f + ".out"))
        ms = json.load(open(os.path.join(d, f + ".meta")))
        if len(cases) != len(ms):
            print("COUNT", f, len(cases), len(ms))
            bad += 1
        fam_bad = 0
        seen = {}
        for m, r in zip(ms, cases):
            total += 1
            if r["c"][3] == "STOP":
                stops += 1
            why = cmp_case(m, r, FB, TB, PT)
            if why:
                fam_bad += 1
                if fam_bad <= 6:
                    print("MISMATCH", f, r["c"][1], why, " ".join(r["c"][3:6])[:90])
            else:
                lab = outcome(m, r, FB)
                seen[lab] = seen.get(lab, 0) + 1
                for ct in CONTROLS.get(f, ()):
                    ctl_cases[(f, ct)] = ctl_cases.get((f, ct), 0) + 1
                    if cmp_case(m, r, FB, TB, PT, ct):
                        ctl_fail[(f, ct)] = ctl_fail.get((f, ct), 0) + 1
        bad += fam_bad
        outs[f] = seen
        for kind in ("R", "W"):
            for pc, addr, size, count in tail[kind]:
                reads[(f, kind, pc, addr, size)] = reads.get((f, kind, pc, addr, size), 0) + count
        print("family %-9s cases %5d mismatches %d distinct outcomes %d" % (f, len(ms), fam_bad, len(seen)))
    print("total cases %d mismatches %d stops %d" % (total, bad, stops))
    for k in sorted(ctl_cases):
        print("control %-9s %-14s fails %d of %d" % (k[0], k[1], ctl_fail.get(k, 0), ctl_cases[k]))
    un = [k for k in sorted(reads) if not accounted(k)]
    print("traced accesses outside the declared memory: %d, unaccounted %d" % (len(reads), len(un)))
    for k in un[:40]:
        print("  UNACCOUNTED %s %s pc=%06x addr=%08x size=%d count=%d" % (k[0], k[1], k[2], k[3], k[4], reads[k]))
    for f in FAMILIES:
        if f in ("dist",):
            continue
        for lab in sorted(outs[f], key=lambda s: (len(s), s)):
            print("outcome %-9s %-46s %d" % (f, lab, outs[f][lab]))
    return 1 if bad or un or stops else 0


# ------------------------------------------------------------------ static


def objdump(lo, hi):
    t = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=%d" % lo, "--stop-address=%d" % hi, EXE],
                       capture_output=True, text=True).stdout
    return [re.sub(r"\s+", " ", x.strip()) for x in t.splitlines() if re.match(r"^\s+[0-9a-f]+:", x)]


def calls_to(text, base, target):
    return [base + i for i in range(len(text) - 5) if text[i] == 0xE8 and (base + i + 5 + struct.unpack_from("<i", text, i + 1)[0]) & M32 == target]


def cmd_static(d):
    exe = open(EXE, "rb").read()
    pe = struct.unpack_from("<I", exe, 0x3C)[0]
    o = struct.unpack_from("<H", exe, pe + 20)[0]
    vs, ra, sz, ptr = struct.unpack_from("<IIII", exe, pe + 24 + o + 8)
    text, base = exe[ptr:ptr + sz], 0x400000 + ra
    out = ["image sha256 " + hashlib.sha256(exe).hexdigest()]
    for name, target, back in (("the drop cell search 0x00555DA0", 0x00555DA0, 0x40), ("the pair form 0x0064E810", 0x0064E810, 0x40),
                               ("the ground placement 0x00558AA0", 0x00558AA0, 0x18), ("the expiry 0x00558A10", 0x00558A10, 0),
                               ("the sweep 0x00558B90", 0x00558B90, 0), ("the distance 0x00641530", 0x00641530, 0), ("UnitInteract 0x00548B00", 0x00548B00, 0)):
        sites = calls_to(text, base, target)
        out.append("%s: %d direct calls" % (name, len(sites)))
        for a in sites:
            out.append("  site %08x" % a)
            if back:
                out += ["    " + x for x in objdump(a - back, a + 5) if x.split()[1] == "push" or x.split()[1] == "lea" or a == int(x.split(":")[0], 16)]
    # every 32-bit access through an item data pointer's +0x24: the writers and readers by the form `mov r, [s+0x14]` then `[r+0x24]`
    t = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", EXE], capture_output=True, text=True).stdout
    lines = [x for x in t.splitlines() if re.match(r"^\s+[0-9a-f]+:\t", x)]
    hits = []
    for i, x in enumerate(lines):
        m = re.search(r"mov\s+(e[a-ds][xip]|e[sd]i),DWORD PTR \[(e[a-ds][xip]|e[sd]i)\+0x14\]", x)
        if not m:
            continue
        reg = m.group(1)
        for j in range(i + 1, min(i + 15, len(lines))):
            k = lines[j]
            if re.search(r"\[" + reg + r"\+0x24\]", k):
                w = re.search(r"\t(mov|or|and|add|sub)\s+DWORD PTR \[" + reg + r"\+0x24\],", k) is not None
                hits.append("  %s %s (loaded at %s)" % ("W" if w else "R", re.sub(r"\s+", " ", k.strip()), x.split(":")[0].strip()))
                break
            if re.match(r".*\t(mov|lea|pop|xor)\s+" + reg + ",", k) or "\tret" in k:
                break
    out.append("accesses of [r+0x24] within 14 instructions of `mov r,[s+0x14]`: %d" % len(hits))
    out += hits
    # the field file, the whole table
    FB = field_bytes()
    bad = steps = 0
    worst = 0
    for row in range(256):
        for col in range(256):
            x, y, n = col, row, 0
            while FB[y * 256 + x] != 8 and n < 600:
                dd = FB[y * 256 + x]
                x, y, n = x + inv.DIR_DX[dd], y + inv.DIR_DY[dd], n + 1
                if not (0 <= x < 256 and 0 <= y < 256):
                    n = 9999
                    break
            if n >= 600:
                bad += 1
            worst = max(worst, n if n < 600 else 0)
            steps += n if n < 600 else 0
    hd = open(FIELD_FILE, "rb").read()[:10]
    out.append("field file header %s, %d bytes; cells whose walk leaves the table or does not reach byte 8: %d; longest walk %d; byte 8 at %s" % (
        hd.hex(), len(FB), bad, worst, [(i % 256, i // 256) for i, b in enumerate(FB) if b == 8]))
    worse = sum(1 for row in range(256) for col in range(256) if max(abs(col - 128), abs(row - 128)) != len(inv.line_cells(FB, 128, 128, col, row)) and (col, row) != (128, 128))
    out.append("cells whose walk is longer than the Chebyshev distance: %d" % worse)
    TB, PT = exe_table()
    out.append("distance table 0x006EB180 (row dy, column dx):")
    for r in range(8):
        out.append("  " + " ".join("%3d" % v for v in TB[r * 8:r * 8 + 8]))
    pick = sorted((dx, dy) for dy in range(8) for dx in range(8) if inv.interact_distance(TB, 0, 0, 2, dx, dy, 1) < 5)
    out.append("|dx|,|dy| with player-to-item distance below 5: %s" % pick)
    open(os.path.join(d, "static.txt"), "w").write("\n".join(out) + "\n")
    print("\n".join(x for x in out if not x.startswith("  ")))


def cmd_manifest(d, write):
    lines = []
    for n in sorted(os.listdir(d)):
        if n.endswith((".cases", ".mem", ".out", ".meta")) or n in ("check.txt", "static.txt") or n.startswith("rcg-"):
            lines.append("%s  %s" % (hashlib.sha256(open(os.path.join(d, n), "rb").read()).hexdigest(), n))
    if write:
        open(os.path.join(d, "manifest.txt"), "w").write("\n".join(lines) + "\n")
    print(len(lines), "files")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("cases", "check", "static", "manifest"))
    ap.add_argument("--dir", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    if a.cmd == "cases":
        cmd_cases(a.dir)
    elif a.cmd == "check":
        return cmd_check(a.dir)
    elif a.cmd == "static":
        cmd_static(a.dir)
    else:
        cmd_manifest(a.dir, a.write)
    return 0


if __name__ == "__main__":
    sys.exit(main())

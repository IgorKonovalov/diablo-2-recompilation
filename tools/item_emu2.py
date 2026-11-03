#!/usr/bin/env python3
"""Plan 0060 P1.2 (`lane/r60b`): grids, the placement search, belts and stacks under Ghidra's p-code emulator (ADR-0015,
ADR-0021), compared with tools/item_inventory.py. No game run, no slot.

    python3 -I tools/item_emu2.py cases --dir D      write D/<family>.cases, D/<family>.mem, D/<family>.meta
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/item_emu2.py check --dir D      compare, account for each traced access, run the controls, count outcomes
    python3 -I tools/item_emu2.py static --dir D     the pinned forms: each table reader's set argument and the byte widths
    python3 -I tools/item_emu2.py manifest --dir D [--write]

Every case draw comes from random.Random("r60b-<family>"), so `cases` regenerates identical files. A case is a declared
scratch image; nothing is patched. search, invrec, beltrec, rowfor, stackok and belt run to the function's return, all callees
emulated; place, put, beltplace and merge end at a named callee (ADR-0021), and what follows it is not covered.

Controls (a control is a wrong reading; `check` prints how many cases each fails, so 0 means the run cannot separate it):
  geq        later spot wins a tie            no255      no early stop at 255          noedge     outside sides do not count
  rowfirst   one-high order rows outer        colright   general order columns right   h1general  one-high takes the general order
  firstall   a player gets the first fit      bestall    every owner gets the score
  wide       gridX, gridY read as u16 (bytes +0x12, +0x13 are declared non-zero, the same for the bound test)
  secondset  the belt count from rows 7..13   defaultbelt the worn belt ignored   nogroup    potions match by class only
  walk1      column walk by 1, not 4          noauto     autobelt ignored          stashsmall page 4 always row 8
"""
import argparse
import hashlib
import json
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import item_inventory as inv  # noqa: E402
from party_emu import parse_out  # noqa: E402
from use_emu import Case, le32, put_stats  # noqa: E402

M32 = 0xFFFFFFFF
DTBL, ISC, RECS, TYPES = 0x10010000, 0x10030000, 0x10060000, 0x10190000
INVT, BELTT = 0x10200000, 0x10210000
USER, INVB, PAGES, CELLS = 0x10100000, 0x10180000, 0x10181000, 0x10182000
ITEM, IDATA, ITEM2, IDATA2, WORN, WDATA, OUT = 0x10101000, 0x10102000, 0x10103000, 0x10104000, 0x10105000, 0x10106000, 0x10107000
SL1, SL2, BOXI = 0x10108000, 0x10109000, 0x10110000
NISC, NTYPES = 400, 8
F_GRIDPUT, F_UNLINK, F_SETSTAT, F_FATAL = 0x0063AFD0, 0x0063AAF0, 0x00627260, 0x00408090
GUARDS = (0x00408A60, 0x00681E09, 0x0040B4B0, 0x0040B430, 0x0040B480)
STOCK_GRIDS = ((10, 4), (6, 4), (6, 8), (3, 4), (10, 10))
NUMBOX = (12, 8, 4, 16, 8, 12, 16)          # the stock first set's counts, declared
SET2_NUMBOX = (4, 16, 12, 8, 16, 4, 8)      # declared unlike the stock second set, so reading it would show
CODES = ("hp1 ", "hp3 ", "hp5 ", "mp1 ", "mp2 ", "mp5 ", "rvl ", "rvs ", "yps ", "tsc ", "isc ", "vps ")
AUTOBELT = {"hp1 ", "hp3 ", "hp5 ", "mp1 ", "mp2 ", "mp5 ", "rvl ", "rvs ", "yps ", "vps "}
BELTABLE_TYPE, PLAIN_TYPE = 1, 2
PAGE_INDEX_INV = 2


def code32(s):
    return struct.unpack("<I", s.encode())[0]


def put_rec(c, row, w=1, h=1, code="xxx ", typ=PLAIN_TYPE, autobelt=0, beltbyte=0, stackable=1, maxst=0, dur=None):
    r = RECS + row * 0x1A8
    c.d32(r + 0x80, code32(code))
    c.d32(r + 0xE8, maxst)
    c.d8(r + 0x10F, w)
    c.d8(r + 0x110, h)
    c.d8(r + 0x112, 1 if dur else 0)
    c.d8(r + 0x113, 0 if dur else 1)
    c.d16(r + 0x11E, typ)
    c.d8(r + 0x130, beltbyte)
    c.d8(r + 0x131, autobelt)
    c.d8(r + 0x132, stackable)


def put_item(c, base, data, row, d0=2, file=0, eth=0, sl=None, stats=None, mode=0):
    c.d32(base, 4)
    c.d32(base + 4, row)
    c.d32(base + 0xC, 0x4000 + ((base >> 8) & 0xFFF))
    c.d32(base + 0x10, mode)
    c.d32(base + 0x14, data)
    c.d32(data, d0)
    c.d32(data + 0x18, 0x400000 if eth else 0)
    c.d32(data + 0x28, file)
    if sl:
        c.d32(base + 0x5C, sl)
        put_stats(c, sl, sl + 0x80, stats or {})


def put_inv(c, owner_type):
    c.d32(INVB, 0x01020304)
    if owner_type is not None:
        c.d32(USER, owner_type)
        c.d32(INVB + 8, USER)
    else:
        c.d32(INVB + 8, 0)      # the image keeps earlier cases' writes, so a null owner is written
    c.d32(INVB + 0x14, PAGES)
    c.d32(INVB + 0x18, 8)


def put_page(c, index, w, h, cells, stride_cells=CELLS):
    """Page `index`: width and height bytes, cells (a list of u32 by cell)."""
    p = PAGES + index * 0x10
    c.d8(p + 8, w)
    c.d8(p + 9, h)
    c.d32(p + 0xC, stride_cells)
    c.put(stride_cells, b"".join(le32(v) for v in cells))


def put_row(c, row, w, h, junk=True):
    """An inventory row: gridX, gridY bytes; +0x12, +0x13 declared non-zero, so a wider read would differ."""
    r = INVT + row * 0xF0
    c.d8(r + 0x10, w)
    c.d8(r + 0x11, h)
    if junk:
        c.d8(r + 0x12, 0x7F)
        c.d8(r + 0x13, 0x7F)


def rand_grid(rnd, w, h):
    level = rnd.choice((0, 0.1, 0.25, 0.4, 0.6, 0.8, 0.95))
    return [(r, c) for r in range(h) for c in range(w) if rnd.random() < level]


def gen_search(rnd, i):
    c = Case()
    if i < 400:   # every size on every stock grid, empty and for both owners
        w0, h0 = STOCK_GRIDS[i % 5]
        iw, ih = (i // 5) % 4 + 1, (i // 20) % 4 + 1
        occ = []
        owner = 0 if (i // 80) % 2 == 0 else 1
    else:
        w0, h0 = rnd.choice(STOCK_GRIDS) if rnd.random() < 0.8 else (rnd.randrange(1, 13), rnd.randrange(1, 13))
        iw, ih = rnd.choice(((1, 1), (1, 2), (1, 3), (1, 4), (2, 1), (2, 2), (2, 3), (2, 4), (3, 3), (3, 2), (4, 1), (3, 1)))
        occ = rand_grid(rnd, w0, h0)
        owner = rnd.choice((0, 0, 0, 1, 2, None))
    put_rec(c, 7, iw, ih)
    put_item(c, ITEM, IDATA, 7)
    put_inv(c, owner)
    page = rnd.randrange(0, 5)
    row = rnd.randrange(0, 32)
    put_row(c, row, w0, h0)
    cells = [0] * (w0 * h0)
    for r, col in occ:
        cells[r * w0 + col] = ITEM2
    put_page(c, page + 2, w0, h0, cells)
    c.d32(OUT, 0x55555555)
    c.d32(OUT + 4, 0x55555555)
    c.dump(OUT, 8)
    c.meta = dict(f="search", w0=w0, h0=h0, iw=iw, ih=ih, occ=occ, owner=owner)
    return c.call(0x0063B850, 0, 0, INVB, ITEM, row, OUT, OUT + 4, page), c.meta


def gen_place(rnd, i):
    c = Case()
    w0, h0 = rnd.choice(STOCK_GRIDS)
    iw, ih = rnd.choice(((1, 1), (1, 3), (2, 2), (2, 3), (2, 4), (1, 2)))
    put_rec(c, 7, iw, ih)
    put_item(c, ITEM, IDATA, 7)
    owner = rnd.choice((0, 0, 1))
    put_inv(c, owner)
    page, row = rnd.randrange(0, 5), rnd.randrange(0, 32)
    put_row(c, row, w0, h0)
    occ = rand_grid(rnd, w0, h0)
    cells = [0] * (w0 * h0)
    for r, col in occ:
        cells[r * w0 + col] = ITEM2
    put_page(c, page + 2, w0, h0, cells)
    c.meta = dict(f="place", w0=w0, h0=h0, iw=iw, ih=ih, occ=occ, owner=owner, page=page, row=row)
    return c.call(0x0063B950, 0, 0, INVB, ITEM, row, 0, page, 0, 0), c.meta


def gen_put(rnd, i):
    c = Case()
    kind = rnd.choice(("page", "page", "page", "body", "belt"))
    iw, ih = rnd.randrange(0, 4), rnd.randrange(0, 5)
    if rnd.random() < 0.8:
        iw, ih = max(iw, 1), max(ih, 1)
    put_rec(c, 7, iw, ih)
    put_item(c, ITEM, IDATA, 7, mode=0)
    put_inv(c, 0)
    row = rnd.randrange(0, 32)
    if kind == "page":
        idx = rnd.randrange(2, 7)
        w0, h0 = rnd.choice(STOCK_GRIDS)
        col, r0 = rnd.randrange(-1, w0 + 1), rnd.randrange(-1, h0 + 1)
    else:
        idx = 0 if kind == "body" else 1
        w0, h0 = inv.BODY_GRID if kind == "body" else inv.BELT_GRID
        col, r0 = rnd.randrange(0, w0), 0
    put_row(c, row, w0, h0)
    occ = rand_grid(rnd, w0, h0)
    cells = [0] * (w0 * h0)
    for r, cc in occ:
        cells[r * w0 + cc] = ITEM2
    put_page(c, idx, w0, h0, cells)
    lines = ["r eax %08x" % INVB, "r ebx %08x" % ITEM]
    c.lines.extend(lines)
    c.meta = dict(f="put", kind=kind, idx=idx, w0=w0, h0=h0, iw=iw, ih=ih, occ=occ, col=col, r0=r0)
    return c.call(F_GRIDPUT, 0, 0, col, r0, idx, row), c.meta


def belt_setup(c, rnd):
    worn = rnd.choice((None, 0, 1, 3, 4, 5, 6))
    code = rnd.choice(CODES)
    autobelt = 1 if (code in AUTOBELT and rnd.random() < 0.85) else 0
    typ = BELTABLE_TYPE if rnd.random() < 0.95 else PLAIN_TYPE
    size = (1, 1) if rnd.random() < 0.95 else (1, 2)
    cls = 7
    put_rec(c, cls, size[0], size[1], code=code, typ=typ, autobelt=autobelt)
    put_item(c, ITEM, IDATA, cls)
    put_inv(c, 0)
    body = [0] * 13
    if worn is not None:
        put_rec(c, 9, beltbyte=worn)
        put_item(c, WORN, WDATA, 9)
        body[8] = WORN
    put_page(c, 0, 13, 1, body, CELLS + 0x400)
    n = NUMBOX[2 if worn is None else worn]
    level = rnd.choice((0, 0.2, 0.5, 0.8, 1))
    boxes, same, cells = [None] * 16, set(), [0] * 16
    for b in range(n):
        if rnd.random() < level:
            hc = rnd.choice(CODES)
            k = CODES.index(hc)
            irow = 20 + k
            base = BOXI + 0x100 * b
            put_rec(c, irow, code=hc)
            c.d32(base, 4)
            c.d32(base + 4, irow)
            boxes[b] = hc
            cells[b] = base
            if hc == code:
                # the same code as a different row, except where it is the same class
                if rnd.random() < 0.5:
                    c.d32(base + 4, cls)
                    same.add(b)
    put_page(c, 1, 16, 1, cells)
    for k, nb in enumerate(NUMBOX):
        c.d32(BELTT + k * 0x108 + 4, nb)
        c.d32(BELTT + (k + 7) * 0x108 + 4, SET2_NUMBOX[k])
    return dict(worn=worn, code=code, autobelt=autobelt, typ=typ, size=size, boxes=boxes, same=sorted(same))


def gen_belt(rnd, i):
    c = Case()
    m = belt_setup(c, rnd)
    c.d32(OUT, 0x55555555)
    c.dump(OUT, 4)
    c.meta = dict(f="belt", **m)
    return c.call(0x0063C600, 0, 0, INVB, ITEM, OUT), c.meta


def gen_beltplace(rnd, i):
    c = Case()
    m = belt_setup(c, rnd)
    c.meta = dict(f="beltplace", **m)
    return c.call(0x0063C790, 0, 0, INVB, ITEM), c.meta


def gen_rowfor(rnd, i):
    c = Case()
    t = rnd.choice((0, 0, 0, 1, 2, 3, 5))
    cls = rnd.choice((0, 1, 2, 3, 4, 5, 6, 7, 0x152, 0x153, 100))
    page = rnd.choice((0, 1, 2, 3, 4, 5, 0xFF))
    exp = rnd.choice((0, 1, 2))
    c.d32(USER, t)
    c.d32(USER + 4, cls)
    c.meta = dict(f="rowfor", t=t, cls=cls, page=page, exp=exp)
    return c.call(0x00621050, 0, 0, USER, page, exp), c.meta


def gen_invrec(rnd, i):
    c = Case()
    row, st = rnd.randrange(0, 33), rnd.choice((0, 0, 1, 2))
    bs = bytes(rnd.randrange(256) for _ in range(24))
    idx = st * 16 + row
    if idx <= 32:
        c.put(INVT + idx * 0xF0 + 0x10, bs)
    c.put(OUT, bytes(24))
    c.dump(OUT, 24)
    c.meta = dict(f="invrec", row=row, st=st, bs=bs.hex())
    return c.call(0x0065C1F0, 0, 0, row, st, OUT), c.meta


def gen_beltrec(rnd, i):
    c = Case()
    row, st = rnd.randrange(0, 7), rnd.choice((0, 1))
    bs = bytes(rnd.randrange(256) for _ in range(0x108))
    c.put(BELTT + (st * 7 + row) * 0x108, bs)
    c.put(OUT, bytes(0x108))
    c.dump(OUT, 0x108)
    c.meta = dict(f="beltrec", row=row, st=st, bs=bs.hex())
    return c.call(0x00660CB0, 0, 0, row, st, OUT), c.meta


def gen_stackok(rnd, i):
    c = Case()
    a = dict(cls=7, d0=rnd.choice((1, 2, 3, 2, 2, 10)), file=5, stackable=1, eth=0, stats={70: 3})
    b = dict(a, stats=dict(a["stats"]))
    breaks = rnd.choice(("none", "none", "none", "cls", "d0", "q0", "q4", "q9", "q3", "q10", "file", "stackable", "eth", "s21", "s22",
                         "s23", "s24", "s159", "s160", "s194a", "s194b", "s194c"))
    if breaks == "cls":
        b["cls"] = 8
    elif breaks == "d0":
        b["d0"] = a["d0"] + 1 if a["d0"] != 3 else 2
    elif breaks in ("q0", "q4", "q9", "q3", "q10"):
        a["d0"] = b["d0"] = int(breaks[1:])
    elif breaks == "file":
        b["file"] = 6
    elif breaks == "stackable":
        a["stackable"] = b["stackable"] = 0
    elif breaks == "eth":
        b["eth"] = 1
    elif breaks in ("s194a", "s194b"):
        (a if breaks == "s194a" else b)["stats"][194] = rnd.randrange(1, 6)
    elif breaks == "s194c":
        a["stats"][194] = b["stats"][194] = 0x100    # a low byte of 0
    elif breaks != "none":
        b["stats"][int(breaks[1:])] = rnd.randrange(1, 50)
    for row, x in ((7, a), (8, b)):
        if row == 7 or b["cls"] == 8:
            put_rec(c, x["cls"], stackable=x["stackable"])
    put_item(c, ITEM, IDATA, a["cls"], d0=a["d0"], file=a["file"], eth=a["eth"], sl=SL1, stats=a["stats"])
    put_item(c, ITEM2, IDATA2, b["cls"], d0=b["d0"], file=b["file"], eth=b["eth"], sl=SL2, stats=b["stats"])
    c.meta = dict(f="stackok", a=a, b=b, breaks=breaks)
    return c.call(0x0062C850, 0, 0, ITEM, ITEM2), c.meta


def gen_merge(rnd, i):
    """0x0055E590 with ESI the target, EBX the user, argument 2 the source, up to the first UnitSetStat."""
    c = Case()
    mx = rnd.choice((20, 50, 60, 100, 350, 500))
    s254 = rnd.choice((0, 0, 0, 3, 40))
    dur = rnd.random() < 0.4
    limit = inv.max_stack(mx, s254)
    sq, tq = rnd.randrange(0, limit + 1), rnd.randrange(0, limit + 1)
    if rnd.random() < 0.3:
        tq = limit - sq if rnd.random() < 0.5 else limit - sq + 1     # the exact bound and one above
        tq = max(0, tq)
    sd, td = rnd.randrange(1, 30), rnd.randrange(1, 30)
    if rnd.random() < 0.15:
        td = sd
    put_rec(c, 7, stackable=1, maxst=mx, dur=dur)
    common = {73: 50} if dur else {}
    put_item(c, ITEM, IDATA, 7, sl=SL1, stats={**common, 70: sq, 72: sd})
    put_item(c, ITEM2, IDATA2, 7, sl=SL2, stats={**common, 70: tq, 72: td, 254: s254})
    c.d8(ISC + 0x144 * 73 + 5, 0)
    c.d32(USER, 0)
    c.d32(USER + 0x60, INVB)
    c.lines.extend(["r esi %08x" % ITEM2, "r ebx %08x" % USER])
    c.meta = dict(f="merge", sq=sq, tq=tq, mx=mx, s254=s254, dur=dur, sd=sd, td=td)
    return c.call(0x0055E590, 0, 0, 0x10000000, ITEM), c.meta


GEN = {"search": gen_search, "place": gen_place, "put": gen_put, "belt": gen_belt, "beltplace": gen_beltplace, "rowfor": gen_rowfor,
       "invrec": gen_invrec, "beltrec": gen_beltrec, "stackok": gen_stackok, "merge": gen_merge}
COUNTS = {"search": 4000, "place": 500, "put": 800, "belt": 2000, "beltplace": 400, "rowfor": 400, "invrec": 200, "beltrec": 100,
          "stackok": 660, "merge": 500}
OBSERVES = {"place": (F_GRIDPUT,), "put": (F_UNLINK,), "beltplace": (F_GRIDPUT,), "merge": (F_SETSTAT,)}
FAMILIES = tuple(GEN)


def mem_spec(f):
    out = ["# plan 0060 P1.2: the fixed part of the image", "dword 00744304 %08x" % DTBL,
           "dword %08x %08x" % (DTBL + 0xBD4, NISC), "dword %08x %08x" % (DTBL + 0xBCC, ISC),
           "dword %08x %08x" % (DTBL + 0xBFC, NTYPES), "dword %08x %08x" % (DTBL + 0xBF8, TYPES),
           "bytes %08x 01" % (TYPES + BELTABLE_TYPE * 0xE4 + 0x19), "bytes %08x 00" % (TYPES + PLAIN_TYPE * 0xE4 + 0x19),
           "dword 0096ca58 00000097", "dword 0096ca5c %08x" % RECS,
           "dword 0096d4f0 00000020", "dword 0096d4f4 %08x" % INVT, "dword 0096d4f8 %08x" % BELTT]
    out += ["guard %08x" % g for g in GUARDS]
    out += ["observe %08x" % a for a in OBSERVES.get(f, ()) + (F_FATAL,)]
    return "\n".join(out) + "\n"


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    for f in FAMILIES:
        rnd = random.Random("r60b-" + f)
        blocks, metas = [], []
        for i in range(COUNTS[f]):
            b, m = GEN[f](rnd, i)
            blocks.append(b)
            metas.append(m)
        open(os.path.join(d, f + ".cases"), "w").write("\n".join(blocks) + "\n")
        open(os.path.join(d, f + ".mem"), "w").write(mem_spec(f))
        json.dump(metas, open(os.path.join(d, f + ".meta"), "w"))
    print("cases written", sum(COUNTS.values()))


def grid_of(m):
    return inv.InvGrid(m["w0"], m["h0"], m["occ"])


def predict_search(m, ctl=None):
    """-> (ret, col, row) for search: None spot gives ret 0 with the outputs untouched."""
    if m["iw"] == 0 or m["ih"] == 0:
        return (0, None, None)
    w0, h0 = m["w0"], m["h0"]
    if ctl == "wide":
        return (0, None, None)      # a u16 read of the bytes is a width above 0x7F00, unlike the page: 0x0063ADD0 refuses
    at = inv.spot_find(inv.InvGrid(w0, h0, m["occ"]), m["iw"], m["ih"], m["owner"] == 0, ctl)
    return (1, at[0], at[1]) if at else (0, None, None)


def predict_belt(m, ctl=None):
    """-> (ret, box or None)."""
    if m["typ"] != BELTABLE_TYPE or tuple(m["size"]) != (1, 1):
        return (0, None)
    worn = m["worn"]
    if ctl == "defaultbelt":
        worn = None
    row = 2 if worn is None else worn
    n = SET2_NUMBOX[row] if ctl == "secondset" else NUMBOX[row]
    box = inv.belt_slot(n, m["boxes"], m["code"], set(m["same"]), m["autobelt"] and ctl != "noauto", ctl)
    return (1, box) if box is not None else (0, None)


def ret_of(c):
    return int(c[5].split("=")[1], 16) if False else None


def field(c, name):
    for x in c:
        if x.startswith(name + "="):
            return int(x.split("=")[1], 16)
    return None


def stack_words(a, n):
    return struct.unpack("<%dI" % n, a[:4 * n])


def cmp_case(m, r, ctl=None):
    """-> None when the record equals the model (or the control's reading), else why."""
    c, a, dumps = r["c"], r.get("a"), r["d"]
    kind = c[3]
    f = m["f"]
    eax = field(c, "eax")
    if f == "search":
        ret, col, row = predict_search(m, ctl)
        out = struct.unpack("<II", dumps[0][1])
        if kind == "OBS":
            return "boundary %s" % c[4]
        if (eax != 0) != (ret != 0):
            return "ret %x for %d" % (eax, ret)
        if ret and out != (col, row):
            return "spot %s for %s" % (out, (col, row))
        if not ret and out != (0x55555555, 0x55555555):
            at = None
            return "outputs written %s %s" % (out, at)
        return None
    if f == "place":
        g = inv.InvGrid(m["w0"], m["h0"], m["occ"])
        at = inv.spot_find(g, m["iw"], m["ih"], m["owner"] == 0, ctl)
        if at is None:
            return None if kind != "OBS" and eax == 0 else "refusal expected"
        if kind != "OBS" or int(c[4], 16) != F_GRIDPUT:
            return "no boundary"
        w = stack_words(a, 5)
        if w[0] != 0x63B9A9 or w[1:5] != (at[0], at[1], m["page"] + 2, m["row"]):
            return "args %s for %s" % ([hex(x) for x in w], at)
        return None
    if f == "put":
        ok = m["iw"] > 0 and m["ih"] > 0
        iw, ih = (1, 1) if m["kind"] != "page" else (m["iw"], m["ih"])
        col, r0 = m["col"], m["r0"]
        if m["kind"] == "page" and ctl != "wide":
            ok = ok and 0 <= col and col + iw <= m["w0"] and 0 <= r0 and r0 + ih <= m["h0"]
        elif m["kind"] == "page":
            ok = ok and 0 <= col and 0 <= r0
        ok = ok and inv.InvGrid(m["w0"], m["h0"], m["occ"]).free(col, r0, iw, ih) if ok and ctl != "wide" else ok
        if ok:
            return None if kind == "OBS" and int(c[4], 16) == F_UNLINK else "boundary expected"
        return None if kind != "OBS" and eax == 0 else "refusal expected, %s" % c[3:5]
    if f == "belt":
        ret, box = predict_belt(m, ctl)
        out = struct.unpack("<I", dumps[0][1])[0]
        if kind == "OBS":
            return "boundary %s" % c[4]
        if (eax != 0) != (ret != 0):
            return "ret %x for %s" % (eax, (ret, box))
        if ret and out != box:
            return "box %d for %d" % (out, box)
        return None
    if f == "beltplace":
        ret, box = predict_belt(m, ctl)
        if ret:
            if kind != "OBS" or int(c[4], 16) != F_GRIDPUT:
                return "no boundary for box %d" % box
            w = stack_words(a, 5)
            if w[0] != 0x63C7D9 or w[1:5] != (box, 0, 1, 0):
                return "args %s for %d" % ([hex(x) for x in w], box)
            return None
        return None if kind != "OBS" and eax == 0 else "refusal expected %s" % c[3:5]
    if f == "rowfor":
        want = inv.inv_row(m["t"], m["cls"], m["page"], m["exp"], ctl)
        return None if eax == (want & M32) else "row %x for %d" % (eax, want)
    if f == "invrec":
        if m["st"] * 16 + m["row"] > 32:
            return None if kind == "OBS" and int(c[4], 16) == F_FATAL else "fatal expected"
        return None if dumps[0][1].hex() == m["bs"] else "copy"
    if f == "beltrec":
        return None if dumps[0][1].hex() == m["bs"] else "copy"
    if f == "stackok":
        a0 = {**m["a"], "stats": {int(k): v for k, v in m["a"]["stats"].items()}}
        b0 = {**m["b"], "stats": {int(k): v for k, v in m["b"]["stats"].items()}}
        return None if (eax != 0) == inv.stack_ok(a0, b0) else "ret %x, breaks %s" % (eax, m["breaks"])
    if f == "merge":
        limit = inv.max_stack(m["mx"], m["s254"])
        st, val = inv.merge_first_set(m["sq"], m["tq"], limit, m["sd"] if m["dur"] else None, m["td"] if m["dur"] else None)
        if kind != "OBS" or int(c[4], 16) != F_SETSTAT:
            return "no boundary %s" % c[3:5]
        w = stack_words(a, 5)
        if w[1:5] != (ITEM2, st, val & M32, 0):
            return "args %s for %s" % ([hex(x) for x in w], (st, val))
        return None
    return "family"


CONTROLS = {"search": ("geq", "no255", "noedge", "rowfirst", "colright", "h1general", "firstall", "bestall", "wide"),
            "place": ("geq", "firstall", "bestall"), "put": ("wide",),
            "belt": ("secondset", "defaultbelt", "nogroup", "walk1", "noauto"), "rowfor": ("stashsmall",)}
# traced reads the case does not declare: the image's own tables, each named
ACCOUNTED = ((0x00744544, 0x00744580, "class to row pairs and their count"), (0x0074479C, 0x007447CC, "the body and belt page sizes"),
             (0x00744660, 0x007446A0, "the three potion lists and their counts"), (0x00749DE0, 0x00749DE4, "the stack cookie"),
             (0x006CE200, 0x006CE300, "the image's stat bit masks"), (0x00621100, 0x00621200, "the page switch's jump table"))
# reads of a table row's other fields by the row copies: 24 bytes at 0x0065C23B..0x0065C25B and 264 at 0x00660D07. The consumer reads
# only gridX, gridY of the first and numboxes of the second (the families hold every other field at whatever an earlier case left).
COPY_PCS = (0x65C23B, 0x65C243, 0x65C249, 0x65C24F, 0x65C255, 0x65C25B, 0x660D07)


def accounted(k):
    f, kind, pc, addr, size = k
    if kind != "R":
        return False
    if pc in COPY_PCS and (INVT <= addr < INVT + 0x10000 or BELTT <= addr < BELTT + 0x10000):
        return True
    return any(lo <= addr < hi for lo, hi, _ in ACCOUNTED)


def outcome(m, r):
    c, dumps = r["c"], r["d"]
    if c[3] == "OBS":
        return ("OBS", c[4], r["a"][4:20].hex())
    return ("RET", field(c, "eax") if m["f"] not in ("search", "belt", "invrec", "beltrec") else None,
            dumps[0][1].hex()[:16] if dumps else "")


def cmd_check(d):
    total = bad = stops = 0
    ctl_fail, ctl_cases = {}, {}
    reads, outs = {}, {}
    for f in FAMILIES:
        path = os.path.join(d, f + ".out")
        if not os.path.exists(path):
            print("MISSING", f)
            bad += 1
            continue
        cases, tail = parse_out(path)
        ms = json.load(open(os.path.join(d, f + ".meta")))
        if len(cases) != len(ms):
            print("COUNT", f, len(cases), len(ms))
            bad += 1
        fam_bad = 0
        seen = set()
        for m, r in zip(ms, cases):
            total += 1
            if r["c"][3] == "STOP":
                stops += 1
            why = cmp_case(m, r)
            seen.add(outcome(m, r))
            if why:
                fam_bad += 1
                if fam_bad <= 4:
                    print("MISMATCH", f, r["c"][1], why, " ".join(r["c"][3:6])[:90])
            else:
                for ct in CONTROLS.get(f, ()):
                    ctl_cases[(f, ct)] = ctl_cases.get((f, ct), 0) + 1
                    if cmp_case(m, r, ct):
                        ctl_fail[(f, ct)] = ctl_fail.get((f, ct), 0) + 1
        bad += fam_bad
        outs[f] = len(seen)
        for kind in ("R", "W"):
            for pc, addr, size, count in tail[kind]:
                reads[(f, kind, pc, addr, size)] = reads.get((f, kind, pc, addr, size), 0) + count
        print("family %-10s cases %5d mismatches %d distinct outcomes %d" % (f, len(ms), fam_bad, len(seen)))
    print("total cases %d mismatches %d stops %d" % (total, bad, stops))
    for k in sorted(ctl_cases):
        print("control %-10s %-11s fails %d of %d" % (k[0], k[1], ctl_fail.get(k, 0), ctl_cases[k]))
    un = [k for k in sorted(reads) if not accounted(k)]
    print("traced accesses outside the declared memory: %d, unaccounted %d" % (len(reads), len(un)))
    for k in un[:40]:
        print("  UNACCOUNTED %s %s pc=%06x addr=%08x size=%d count=%d" % (k[0], k[1], k[2], k[3], k[4], reads[k]))
    return 1 if bad or un or stops else 0


READERS = (("inventory slot rectangle 0x0065C270", 0x0065C270), ("inventory record 0x0065C140", 0x0065C140),
           ("inventory count or row 0x0065C180", 0x0065C180), ("belts box rectangle 0x00660D10", 0x00660D10),
           ("belts 0x00660C70", 0x00660C70), ("belts 0x00660C60", 0x00660C60), ("inventory 0x0065C130", 0x0065C130))
SEARCH_BODIES = (0x0063B790, 0x0063B7D0, 0x0063B810)
BYTE_PINS = ((0x0063A8B6, "0FB64708", "grid width u8 at page +8, InvGridFree"), (0x0055E9A0, "33C0C20800", "packet 0x22's callee: returns 0"),
             (0x00628BFD, "83F8FF", "the autobelt test compares 0x0063C560's return with -1"),
             (0x00560918, "6A00", "0x00560921's set argument, pushed before the belt byte's call"),
             (0x00560939, "6A00", "0x0056093D's set argument"))


def va2off(exe, va):
    pe = struct.unpack_from("<I", exe, 0x3C)[0]
    n = struct.unpack_from("<H", exe, pe + 6)[0]
    o = struct.unpack_from("<H", exe, pe + 20)[0]
    for i in range(n):
        vs, ra, sz, ptr = struct.unpack_from("<IIII", exe, pe + 24 + o + 40 * i + 8)
        if ra <= va - 0x400000 < ra + max(vs, sz):
            return ptr + va - 0x400000 - ra
    return None


def cmd_static(d, path):
    """Direct calls of the three table readers with the set argument's push, and absolute references to the two table bases."""
    exe = open(path, "rb").read()
    pe = struct.unpack_from("<I", exe, 0x3C)[0]
    o = struct.unpack_from("<H", exe, pe + 20)[0]
    vs, ra, sz, ptr = struct.unpack_from("<IIII", exe, pe + 24 + o + 8)
    text = exe[ptr:ptr + sz]
    base = 0x400000 + ra
    out = ["image sha256 " + hashlib.sha256(exe).hexdigest()]
    for name, target in (("inventory record 0x0065C1F0", 0x0065C1F0), ("belts record 0x00660CB0", 0x00660CB0), ("row for unit 0x00621050", 0x00621050)):
        sites = []
        for i in range(len(text) - 5):
            if text[i] == 0xE8 and (base + i + 5 + struct.unpack_from("<i", text, i + 1)[0]) & M32 == target:
                sites.append(base + i)
        out.append("%s: %d direct calls" % (name, len(sites)))
        for a in sites:
            before = text[a - base - 4:a - base]
            if target == 0x00621050:
                out.append("  %08x" % a)
                continue
            # the pushes right before the call: row (last), set (one before), so a set of literal 0 ends 6A 00 + one push
            lit0 = (before[-3:-1] == b"\x6a\x00") or (before[-4:-2] == b"\x6a\x00")
            out.append("  %08x %s before %s" % (a, "set 0" if lit0 else "set not a literal next to the call", before.hex()))
    for name, target in READERS:
        sites = [base + i for i in range(len(text) - 5) if text[i] == 0xE8 and (base + i + 5 + struct.unpack_from("<i", text, i + 1)[0]) & M32 == target]
        client = [a for a in sites if a < 0x500000]
        out.append("%s: %d direct calls, %d at or above 0x00500000 %s" % (name, len(sites), len(sites) - len(client),
                                                                          " ".join("%08x" % a for a in sites if a >= 0x500000)))
    for name, ref in (("inventory base 0x0096D4F4", 0x0096D4F4), ("inventory count 0x0096D4F0", 0x0096D4F0), ("belts base 0x0096D4F8", 0x0096D4F8)):
        pat = struct.pack("<I", ref)
        sites, i = [], text.find(pat)
        while i >= 0:
            sites.append(base + i)
            i = text.find(pat, i + 1)
        out.append("%s: %d operand matches at %s" % (name, len(sites), " ".join("%08x" % s for s in sites)))
    def masked(a):
        b = bytearray(exe[va2off(exe, a):va2off(exe, a) + 0x3B])
        for i in range(len(b) - 4):
            if b[i] == 0xE8:
                b[i + 1:i + 5] = b"\0\0\0\0"
        return bytes(b).hex()
    out.append("the three general search bodies (0x3B bytes, call displacements masked): %s" % (
        "equal" if len({masked(a) for a in SEARCH_BODIES}) == 1 else "differ"))
    for a, want, why in BYTE_PINS:
        got = exe[va2off(exe, a):va2off(exe, a) + len(want) // 2].hex().upper()
        out.append("pin %08x %s %s: %s" % (a, got, "ok" if got == want else "DIFFERS " + want, why))
    open(os.path.join(d, "static.txt"), "w").write("\n".join(out) + "\n")
    print("\n".join(x for x in out if not x.startswith("  ")))


def cmd_manifest(d, write):
    lines = []
    for n in sorted(os.listdir(d)):
        if n.endswith((".cases", ".mem", ".out", ".meta")) or n in ("check.txt", "static.txt") or n.startswith("rcg-"):
            lines.append("%s  %s" % (hashlib.sha256(open(os.path.join(d, n), "rb").read()).hexdigest(), n))
    text = "\n".join(lines) + "\n"
    if write:
        open(os.path.join(d, "manifest.txt"), "w").write(text)
    print(len(lines), "files")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("cases", "check", "static", "manifest"))
    ap.add_argument("--dir", required=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--exe", default="workspace/install/app/game.exe")
    a = ap.parse_args()
    if a.cmd == "cases":
        cmd_cases(a.dir)
    elif a.cmd == "check":
        return cmd_check(a.dir)
    elif a.cmd == "static":
        cmd_static(a.dir, a.exe)
    else:
        cmd_manifest(a.dir, a.write)
    return 0


if __name__ == "__main__":
    sys.exit(main())

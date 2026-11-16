#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S4e part 5 (`lane/n66z`): the placement search on full and near-full pages and in sequence,
InvGridFree's bounds, the belt group test and the autobelt test, BeltPutItem, the ground expiry's quality 9 and
ItemPlaceOnGround's quest call, run on the pinned Game.exe under Ghidra's p-code emulator (ADR-0015, ADR-0021) with
re/ghidra_scripts/EmuBoundary.java and compared with the models below and tools/item_inventory.py. Parts 1 to 4
(tools/stats_s4e_emu.py, items_s4e_emu.py, items_s4e3_emu.py, items_s4e4_emu.py, run/ to run4/) stay unchanged; this
tool builds its cases on tools/item_emu2.py's and tools/item_emu3.py's declared worlds, unchanged.

    python3 -I tools/items_s4e5_emu.py cases [--dir D] [--limit N]   write D/<family>.cases, .mem, .json
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/items_s4e5_emu.py check [--dir D]               compare, account every traced access, controls
    python3 -I tools/items_s4e5_emu.py static                        objdump pins
    python3 -I tools/items_s4e5_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66z/s4e/run5. Every draw comes from random.Random("n66z-s4e5-<family>"); `seq` also
replays the two sequences of the spec's worked example.

Families (function, convention; boundaries; inventory rows):
  search   InvSpotFindBySize 0x0063B850 (inv, item, row, &col, &row, page), full, near-full and one-hole pages, every
           owner kind: to the return.                                                                 inventory 22
  seq      the same function run as a sequence: each case's page is the previous cases' placements (each item its own
           cell pointer), until a refusal; the worked example's two sequences first.                  inventory 98
  gridfree InvGridFree 0x0063A8A0 (EAX page, ECX row, DL w; col, h): rectangles inside, across and outside the page,
           the cells around the array declared: to the return.                                       inventory 23
  holds    BeltHoldsSameGroup 0x0063C560 (inv, item): to the return.                              inventory 47
  autobelt ItemAutoBeltTest 0x00628BA0 (inv, item): to the return, or the error routine 0x00408090 (observed). 47, 55
  beltput  BeltPutItem 0x0063C4F0 (inv, item, box): to the return or InvItemRemove 0x0063AAF0 (inside InvGridPut).  48
  expiry   ItemGroundExpiry 0x00558A10 (ECX game, EDX item): every quality 0..12 with quality 9 weighted: to the return. 87
  ground   ItemPlaceOnGround 0x00558AA0 (ECX game, EDX flag; item, room, x, y), the flag 0 or not: to the return or
           QUESTS_RaiseItemDropped 0x00543DB0 (observed), the writes dumped.                       inventory 84

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
import item_emu2 as IE2  # noqa: E402
import item_emu3 as IE3  # noqa: E402
import items_s4e3_emu as P3  # noqa: E402
from party_emu import parse_out  # noqa: E402
from use_emu import Case, le32  # noqa: E402

M32 = 0xFFFFFFFF
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
DEFDIR = os.path.join(ROOT, "workspace", "logs", "n66z", "s4e", "run5")
FAMILIES = ("search", "seq", "gridfree", "holds", "autobelt", "beltput", "expiry", "ground")
NCASES = {"search": 3000, "seq": None, "gridfree": 1500, "holds": 1500, "autobelt": 1200, "beltput": 1500,
          "expiry": 800, "ground": 400}
F_SEARCH, F_GRIDFREE, F_HOLDS, F_AUTOBELT, F_BELTPUT = 0x0063B850, 0x0063A8A0, 0x0063C560, 0x00628BA0, 0x0063C4F0
F_FATAL, F_UNLINK, F_RAISE = 0x00408090, 0x0063AAF0, 0x00543DB0
SITE_UNLINK, SITE_RAISE = 0x0063B138, 0x00558B2B          # the return addresses of the two observed calls
GF_PAGE, GF_CELLS, GF_PAD = IE2.PAGES, 0x10184100, 0x100  # gridfree: the cells, 0x100 bytes declared before and 0x400 after
SEQ_PTR = 0x10120000                                      # seq: item k's cells hold SEQ_PTR + 0x100 * k (never read through)
OBSERVE = {"search": (), "seq": (), "gridfree": (), "holds": (), "autobelt": (), "beltput": (F_UNLINK,),
           "expiry": (), "ground": (F_RAISE,)}
# zero-filled before every case (the IE2 image keeps earlier cases' writes otherwise)
ZERO2 = [(IE2.USER, 0x8000), (IE2.BOXI, 0x1000), (IE2.INVB, 0x2000), (0x10182000, 0x3000), (IE2.RECS, 40 * 0x1A8),
         (IE2.INVT, 32 * 0xF0), (IE2.BELTT, 14 * 0x108), (SEQ_PTR, 0x1000)]


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


# ================================================================================================= search and seq
def page_case(c, w0, h0, cells_by_rc, owner, iw, ih, page, row):
    """IE2's world for InvSpotFindBySize: the item (row 7), the inventory, the row's grid, the page's cells."""
    IE2.put_rec(c, 7, iw, ih)
    IE2.put_item(c, IE2.ITEM, IE2.IDATA, 7)
    IE2.put_inv(c, owner)
    IE2.put_row(c, row, w0, h0)
    cells = [0] * (w0 * h0)
    for (r, col), v in cells_by_rc.items():
        cells[r * w0 + col] = v
    IE2.put_page(c, page + 2, w0, h0, cells)
    c.d32(IE2.OUT, 0x55555555)
    c.d32(IE2.OUT + 4, 0x55555555)
    c.dump(IE2.OUT, 8)
    return c.call(F_SEARCH, 0, 0, IE2.INVB, IE2.ITEM, row, IE2.OUT, IE2.OUT + 4, page)


def any_fit(w0, h0, occ, iw, ih):
    """Independent of the search's orders: some free rectangle of the size lies inside the page."""
    g = inv.InvGrid(w0, h0, occ)
    return any(g.free(c, r, iw, ih) for r in range(h0 - ih + 1) for c in range(w0 - iw + 1)) if iw and ih else False


def model_search(m, ctl=None):
    if m["iw"] == 0 or m["ih"] == 0:
        return ["ret", 0]
    g = inv.InvGrid(m["w0"], m["h0"], [tuple(x) for x in m["occ"]])
    at = inv.spot_find(g, m["iw"], m["ih"], m["owner"] == 0, ctl)
    return ["ret", 1, at[0], at[1]] if at else ["ret", 0]


def dense_grid(r, w0, h0, iw, ih):
    kind = r.choice(("level", "level", "full", "hole", "hole", "smallhole"))
    if kind == "level":
        lv = r.choice((0.5, 0.6, 0.7, 0.8, 0.9, 0.95))
        return kind, [(y, x) for y in range(h0) for x in range(w0) if r.random() < lv]
    occ = {(y, x) for y in range(h0) for x in range(w0)}
    if kind in ("hole", "smallhole") and iw <= w0 and ih <= h0:
        hw, hh = (iw, ih) if kind == "hole" else (max(iw - 1, 1), max(ih - 1, 1) if iw > 1 else max(ih - 1, 0))
        x0, y0 = r.randrange(0, w0 - hw + 1), r.randrange(0, h0 - hh + 1)
        for y in range(y0, y0 + hh):
            for x in range(x0, x0 + hw):
                occ.discard((y, x))
        for _ in range(r.choice((0, 0, 1, 3))):      # a few other free cells, scattered
            occ.discard((r.randrange(h0), r.randrange(w0)))
    return kind, sorted(occ)


def gen_search(r):
    c = Case()
    w0, h0 = r.choice(IE2.STOCK_GRIDS) if r.random() < 0.85 else (r.randrange(1, 13), r.randrange(1, 13))
    iw, ih = r.choice(((1, 1), (1, 2), (1, 3), (1, 4), (2, 1), (2, 2), (2, 3), (2, 4), (3, 3), (3, 2), (4, 1), (3, 1)))
    kind, occ = dense_grid(r, w0, h0, iw, ih)
    owner = r.choice((0, 0, 0, 0, 1, 2, None))
    page, row = r.randrange(0, 5), r.randrange(0, 32)
    blk = page_case(c, w0, h0, {tuple(x): IE2.ITEM2 for x in occ}, owner, iw, ih, page, row)
    m = dict(w0=w0, h0=h0, iw=iw, ih=ih, occ=[list(x) for x in occ], owner=owner, kind=kind)
    m["fit"] = any_fit(w0, h0, occ, iw, ih)
    m["want"] = model_search(m)
    m["ctl"] = {k: model_search(m, k) for k in ("noedge", "firstall")}
    return [blk], m


SEQ_EXAMPLE = (((1, 1),) * 5, ((2, 3), (1, 4), (2, 2), (1, 1)))
SEQ_WANT = ([(9, 3), (9, 2), (9, 1), (9, 0), (8, 3)], [(0, 0), (9, 0), (2, 0), (0, 3)])


def gen_seq_all(limit=None):
    r = random.Random("n66z-s4e5-seq")
    seqs = [(10, 4, 0, list(s), True) for s in SEQ_EXAMPLE]
    sizes = ((1, 1), (1, 1), (1, 2), (1, 3), (2, 2), (2, 3), (2, 4), (1, 4), (2, 1), (3, 1))
    for _ in range(60):
        w0, h0 = r.choice(IE2.STOCK_GRIDS)
        owner = r.choice((0, 0, 0, 1))
        seqs.append((w0, h0, owner, [r.choice(sizes) for _ in range(40)], False))
    blocks, metas = [], []
    for si, (w0, h0, owner, items, until_full) in enumerate(seqs):
        cells = {}
        for k, (iw, ih) in enumerate(items):
            c = Case()
            page, row = r.randrange(0, 5), r.randrange(0, 32)
            blk = page_case(c, w0, h0, cells, owner, iw, ih, page, row)
            m = dict(seq=si, step=k, w0=w0, h0=h0, iw=iw, ih=ih, occ=[list(x) for x in sorted(cells)], owner=owner)
            m["want"] = model_search(m)
            m["ctl"] = {kk: model_search(m, kk) for kk in ("firstall", "h1general", "geq")}
            blocks.append(blk)
            metas.append(m)
            if m["want"][1] == 0:
                break
            x, y = m["want"][2], m["want"][3]
            for yy in range(y, y + ih):
                for xx in range(x, x + iw):
                    cells[(yy, xx)] = SEQ_PTR + 0x100 * k
    if limit:
        blocks, metas = blocks[:limit], metas[:limit]
    return blocks, metas


# ================================================================================================= gridfree
def gen_gridfree(r):
    c = Case()
    w0, h0 = r.choice(IE2.STOCK_GRIDS + ((16, 1), (13, 1))) if r.random() < 0.8 else (r.randrange(1, 13), r.randrange(1, 13))
    lv = r.choice((0, 0.05, 0.2, 0.5))
    words = {}
    lo, hi = GF_CELLS - GF_PAD, GF_CELLS + 0x400
    blob = bytearray()
    for a in range(lo, hi, 4):
        inside = 0 <= a - GF_CELLS < 4 * w0 * h0
        v = 0
        if r.random() < (lv if inside else r.choice((0.0, 0.3, 0.9))):
            v = r.choice((IE2.ITEM2, 1, 0x80000000))
        words[a] = v
        blob += le32(v)
    c.put(lo, bytes(blob))
    c.d8(GF_PAGE + 8, w0)
    c.d8(GF_PAGE + 9, h0)
    c.d32(GF_PAGE + 0xC, GF_CELLS)
    iw, ih = r.choice((0, 1, 1, 2, 2, 3, 4)), r.choice((0, 1, 1, 2, 3, 4))
    x = r.choice((r.randrange(0, max(w0 - iw + 1, 1)), r.randrange(-2, w0 + 3), w0 - iw + 1, w0 - 1))
    y = r.choice((r.randrange(0, max(h0 - ih + 1, 1)), r.randrange(-1, h0 + 2), h0 - ih + 1))
    m = dict(w0=w0, h0=h0, iw=iw, ih=ih, x=x, y=y)
    cells = [(yy, xx) for yy in range(y, y + ih) for xx in range(x, x + iw)]
    m["inside"] = all(0 <= xx < w0 and 0 <= yy < h0 for yy, xx in cells)

    def model(ctl=None):
        if ctl == "bounded" and not (0 <= x and x + iw <= w0 and 0 <= y and y + ih <= h0):
            return ["ret", 0]
        for yy, xx in cells:
            if ctl == "clip" and not (0 <= xx < w0 and 0 <= yy < h0):
                continue
            if ctl == "colwrap" and not 0 <= xx < w0:
                continue
            if words[GF_CELLS + 4 * (yy * w0 + xx)]:
                return ["ret", 0]
        return ["ret", 1]
    m["want"] = model()
    m["ctl"] = {k: model(k) for k in ("bounded", "clip", "colwrap")}
    c.lines.append("r eax %08x" % GF_PAGE)
    return [c.call(F_GRIDFREE, y & M32, iw, x & M32, ih)], m


# ================================================================================================= holds, autobelt, beltput
def belt_world(r):
    c = Case()
    m = IE2.belt_setup(c, r)
    m["same"] = list(m["same"])
    v = r.random()
    m["variant"] = "ok"
    if v < 0.04:
        m["variant"] = "nosig"
        c.d32(IE2.INVB, 0x01020305)
    elif v < 0.08:
        m["variant"] = "page1size"
        c.d8(IE2.PAGES + 0x10 + 8, r.choice((12, 8, 4)))
    elif v < 0.11:
        m["variant"] = "notitem"
        c.d32(IE2.ITEM, r.choice((0, 1, 3, 5)))
    return c, m


def same_group(m, b):
    held = m["boxes"][b]
    return held is not None and (b in m["same"] or inv.same_potion_group(m["code"], held))


def model_holds(m, ctl=None):
    if m["variant"] in ("nosig", "notitem", "page1size"):
        return ["ret", 0]
    if m["code"] in ("isc ", "tsc ") and ctl != "tsc_ok":
        return ["ret", 0]
    boxes = range(16) if ctl == "allboxes" else range(4)
    if ctl == "nogroup":
        return ["ret", int(any(m["boxes"][b] is not None and b in m["same"] for b in boxes))]
    return ["ret", int(any(same_group(m, b) for b in boxes))]


def gen_holds(r):
    c, m = belt_world(r)
    m["want"] = model_holds(m)
    m["ctl"] = {k: model_holds(m, k) for k in ("allboxes", "nogroup", "tsc_ok")}
    return [c.call(F_HOLDS, 0, 0, IE2.INVB, IE2.ITEM)], m


def model_autobelt(m, ctl=None):
    if m["variant"] == "notitem":
        return ["obs", F_FATAL]
    if m["autobelt"]:
        return ["ret", 1]
    if ctl == "holds_ret":
        return model_holds(m)
    if ctl == "auto_only":
        return ["ret", 0]
    return ["ret", 1]


def gen_autobelt(r):
    c, m = belt_world(r)
    item = IE2.ITEM
    if m["variant"] == "notitem":
        m["how"] = r.choice(("type", "norow", "null"))
        if m["how"] == "norow":
            c.d32(IE2.ITEM, 4)                # a later write wins: a type-4 unit ...
            c.d32(IE2.ITEM + 4, 0x500)        # ... whose row is past the table's count 0x97: no record
        elif m["how"] == "null":
            item = 0
    m["want"] = model_autobelt(m)
    m["ctl"] = {k: model_autobelt(m, k) for k in ("holds_ret", "auto_only")}
    return [c.call(F_AUTOBELT, 0, 0, IE2.INVB, item)], m


def model_beltput(m, ctl=None):
    if m["variant"] == "notitem":
        return ["ret", 0]
    if m["typ"] != IE2.BELTABLE_TYPE:
        return ["ret", 0]
    if tuple(m["size"]) != (1, 1) and ctl != "size_any":
        return ["ret", 0]
    box = m["box"]
    if ctl == "signed_box":
        if s32(box) > 15:
            return ["ret", 0]
    elif box > 15:
        return ["ret", 0]
    if ctl == "numboxes" and box >= IE2.NUMBOX[2 if m["worn"] is None else m["worn"]]:
        return ["ret", 0]
    if m["variant"] in ("nosig", "page1size"):
        return ["ret", 0]
    if 0 <= s32(box) < 16 and m["boxes"][box] is not None:
        return ["ret", 0]
    return ["obs", F_UNLINK, IE2.ITEM]


def gen_beltput(r):
    c, m = belt_world(r)
    box = r.choice((r.randrange(0, 16), r.randrange(0, 16), r.randrange(0, 16), r.randrange(8, 16), 16, 17,
                    r.randrange(16, 64), 0xFFFFFFFF, 0x80000000))
    m["box"] = box
    m["want"] = model_beltput(m)
    m["ctl"] = {k: model_beltput(m, k) for k in ("numboxes", "signed_box", "size_any")}
    return [c.call(F_BELTPUT, 0, 0, IE2.INVB, IE2.ITEM, box)], m


# ================================================================================================= expiry, ground
def model_expiry(m, ctl=None):
    q = m["quality"]
    if ctl == "q9plain" and q == 9:
        q = 0
    if ctl == "q9as4" and q == 9:
        q = 4
    return ["ret", inv.ground_expiry(m["frame"], m["quest"], q, m["base"], m["gold"], m["filler"]) & M32]


def gen_expiry(r):
    c = Case()
    frame = r.choice((0, 1, 1500, r.randrange(0, 2000000), 0x7FFFFFFF - r.randrange(0, 60000)))
    quest = 1 if r.random() < 0.08 else 0
    quality = r.choice((9, 9, 9, 9, 5, 6, 7, 8, 4, 10, 11, 12, 0, 1, 2, 3))
    base = r.choice((4, 4, 7, 9, 0x35, 20))
    gold = r.choice((0, 1, 9999, 10000, 10001, 2000000000, -1, r.randrange(0, 50000)))
    filler = r.random() < 0.4
    use2 = r.random() < 0.3
    typ, type2 = (9, base) if use2 and base != 4 else (base, 0)
    for t in (typ, type2):
        IE3.set_filler_bit(c, t, False)
    if filler:
        IE3.set_filler_bit(c, type2 if use2 and base != 4 else typ, True)
    IE3.put_item(c, IE3.UNITA, IE3.DATAA, 7, quality, typ, type2, quest, gold if typ == 4 else None)
    c.d32(IE3.GAME + 0xA8, frame)
    m = dict(frame=frame, quest=quest, quality=quality, base=typ, gold=gold, filler=filler)
    m["want"] = model_expiry(m)
    m["ctl"] = {k: model_expiry(m, k) for k in ("q9plain", "q9as4")}
    return [c.call(IE3.F_EXP, IE3.GAME, IE3.UNITA)], m


def model_ground(m, ctl=None):
    if m["null"]:
        if ctl == "null_raises" and m["flag"]:
            return ["obs", F_RAISE, {}]
        return ["ret", {"exp": 0x55555555}]
    exp = inv.ground_expiry(m["frame"], 0, m["quality"], 9, None, False) & M32
    # +0xC4: 0x1002 and 0x2000000 by ItemPlaceOnGround (0x00558ADF, 0x00558B00), bit 1 by UNIT_SetMode (0x006246B3/E3)
    c4 = m["c40"] | 0x2001002 | (0 if ctl == "nomodebit" else 1)
    writes = {"exp": exp, "mode": 3, "c4": c4, "cell": m["cell0"] | 0x200,
              "path": [IE3.room_addr(0), m["px"], m["py"]]}
    if m["flag"] and ctl != "flag_ignored":
        if ctl == "raise_first":
            writes = dict(writes, exp=0x55555555)
        return ["obs", F_RAISE, writes]
    return ["ret", writes]


def gen_ground(r):
    c = Case()
    px, py = r.randrange(3000, 9000), r.randrange(3000, 9000)
    room = IE3.new_room(px - 5, py - 5, 12, 12)
    room["cells"][(px, py)] = r.choice((0, 0x1000, 0x8000, 0x4))
    IE3.put_world(c, [room])
    quality = r.choice((2, 3, 4, 5, 7, 9))
    mode0 = r.choice((3, 4))
    IE3.put_item(c, IE3.UNITA, IE3.DATAA, 7, quality, 9, 0, 0, None, mode0)
    IE3.set_filler_bit(c, 9, False)
    frame = r.randrange(0, 2000000)
    c.d32(IE3.GAME + 0xA8, frame)
    c.d32(IE3.UNITA + 0x2C, IE3.PATHA)
    c40 = r.choice((0, 0x40, 0x10))
    c.d32(IE3.UNITA + 0xC4, c40)
    c.d32(IE3.UNITA + 0xE8, 0)
    c.d32(IE3.room_addr(0) + 0x74, 0)
    c.d32(IE3.room_addr(0) + 0x34, 4)     # the room's flag 4, as item_emu3's ground family declares it
    c.d32(IE3.DATAA + 0x24, 0x55555555)
    null = r.random() < 0.1
    flag = r.choice((0, 1, 1, 1, 0x100, 0xFFFFFFFF))
    for a, n in ((IE3.UNITA, 0x100), (IE3.DATAA, 0x100), (IE3.PATHA, 0x40), (IE3.room_addr(0), 0x100)):
        c.lines.append("s %08x %d" % (a, n))
    c.dump(IE3.UNITA + 0x10, 4)
    c.dump(IE3.UNITA + 0xC4, 4)
    c.dump(IE3.DATAA + 0x24, 4)
    c.dump(IE3.PATHA, 0x20)
    c.dump(IE3.CELLS + 2 * ((py - room["y"]) * room["w"] + px - room["x"]), 2)
    m = dict(px=px, py=py, frame=frame, quality=quality, cell0=room["cells"][(px, py)], null=null, mode0=mode0,
             c40=c40, flag=flag)
    m["want"] = model_ground(m)
    m["ctl"] = {k: model_ground(m, k) for k in ("flag_ignored", "raise_first", "null_raises", "nomodebit")}
    return [c.call(IE3.F_GROUND, IE3.GAME, flag, IE3.UNITA, 0 if null else IE3.room_addr(0), px, py)], m


GEN = {"search": gen_search, "gridfree": gen_gridfree, "holds": gen_holds, "autobelt": gen_autobelt,
       "beltput": gen_beltput, "expiry": gen_expiry, "ground": gen_ground}


# ================================================================================================= commands
def mem_spec(fam):
    out = ["# plan 0066 S4e part 5 (%s)" % fam]
    if fam in ("expiry", "ground"):
        out += IE3.mem_spec(fam).splitlines()
    else:
        out += IE2.mem_spec(fam).splitlines()
        for lo, n in ZERO2:
            out.append("bytes %08x %s" % (lo, "00" * n))
        out.append("dword %08x %08x" % (IE2.ITEM2, 4))       # the occupying item: a type-4 unit
    out += ["observe %08x" % a for a in OBSERVE[fam]]
    if fam not in ("expiry", "ground") or True:
        out += ["guard %08x" % g for g in (0x0040B430, 0x0040B480) if ("guard %08x" % g) not in out]
    return "\n".join(out) + "\n"


def cmd_cases(d, limit=None):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        if fam == "seq":
            blocks, metas = gen_seq_all(limit)
        else:
            r = random.Random("n66z-s4e5-%s" % fam)
            blocks, metas = [], []
            for _ in range(limit or NCASES[fam]):
                b, m = GEN[fam](r)
                blocks.extend(b)
                metas.append(m)
        open(os.path.join(d, fam + ".cases"), "w").write("\n".join(blocks) + "\n")
        open(os.path.join(d, fam + ".mem"), "w").write(mem_spec(fam))
        json.dump({"cases": metas}, open(os.path.join(d, fam + ".json"), "w"), sort_keys=True)
        print("%s: %d cases" % (fam, len(metas)))


def field(c, name):
    for x in c:
        if x.startswith(name + "="):
            return int(x.split("=")[1], 16)
    return None


def got_of(fam, r):
    """The emulated outcome in the model's form."""
    c, d = r["c"], dict(r["d"])
    if c[3] == "STOP":
        return ["stop", " ".join(c[4:8])]
    if c[3] == "OBS":
        fn = int(c[4], 16)
        a = r.get("a", b"")
        ra = struct.unpack("<I", a[:4])[0] if len(a) >= 4 else None
        if fam == "beltput":
            return ["obs", fn, field(c, "ecx")] if ra == SITE_UNLINK else ["obs-site", fn, ra]
        if fam == "ground":
            if ra != SITE_RAISE or field(c, "ecx") != IE3.GAME or struct.unpack("<I", a[4:8])[0] != IE3.UNITA:
                return ["obs-args", fn, ra, field(c, "ecx")]
            return ["obs", fn, ground_writes(d)]
        return ["obs", fn]
    eax = field(c, "eax")
    if fam in ("search", "seq"):
        out = struct.unpack("<II", d[IE2.OUT])
        if eax == 0:
            return ["ret", 0] if out == (0x55555555, 0x55555555) else ["ret", 0, "written", list(out)]
        return ["ret", 1, out[0], out[1]]
    if fam == "ground":
        return ["ret", ground_writes(d)]
    if fam in ("gridfree", "holds", "autobelt", "beltput"):
        return ["ret", eax]
    return ["ret", eax]


def ground_writes(d):
    exp = struct.unpack("<I", d[IE3.DATAA + 0x24])[0]
    if exp == 0x55555555:
        return {"exp": exp}
    path = struct.unpack("<8I", d[IE3.PATHA])
    cell = [v for k, v in d.items() if IE3.CELLS <= k < IE3.CELLS + 0x100000][0]
    return {"exp": exp, "mode": struct.unpack("<I", d[IE3.UNITA + 0x10])[0],
            "c4": struct.unpack("<I", d[IE3.UNITA + 0xC4])[0], "cell": struct.unpack("<H", cell)[0],
            "path": [path[0], path[3], path[4]]}


def form(x):
    return json.dumps(x, sort_keys=True)


ACCOUNTED = IE2.ACCOUNTED + IE3.ACCOUNTED + ((0x007447B4, 0x007447B6, "the belt page's row 16 x 1 (.data)"),)


def accounted(fam, kind, pc, addr):
    if kind != "R":
        return False
    if pc in IE2.COPY_PCS and (IE2.INVT <= addr < IE2.INVT + 0x10000 or IE2.BELTT <= addr < IE2.BELTT + 0x10000):
        return True
    return any(lo <= addr < hi for lo, hi, _ in ACCOUNTED)


def outcome(fam, m, g):
    if fam in ("search", "seq"):
        o = "ret %d" % g[1]
        if fam == "search":
            o += " fit=%d %s owner=%s" % (m["fit"], m["kind"], m["owner"])
        return o
    if fam == "gridfree":
        return "ret %d inside=%d" % (g[1], m["inside"])
    if fam in ("holds", "autobelt", "beltput"):
        return "%s %s %s" % (g[0], "%x" % g[1] if isinstance(g[1], int) else g[1], m["variant"])
    if fam == "expiry":
        return "q%d add %s" % (m["quality"], "quest" if m["quest"] else s32(g[1] - m["frame"]))
    if fam == "ground":
        return "%s flag=%s null=%d" % (g[0], "0" if not m["flag"] else "set", m["null"])
    return g[0]


def cmd_check(d, fams=FAMILIES):
    rc = 0
    for fam in fams:
        p = os.path.join(d, fam + ".out")
        if not os.path.exists(p):
            print("S4E5 %s: no output" % fam)
            rc = 1
            continue
        cases, tail = parse_out(p)
        metas = json.load(open(os.path.join(d, fam + ".json")))["cases"]
        cnt = collections.Counter()
        sep, passed, outs = collections.Counter(), collections.Counter(), collections.Counter()
        bad = []
        if len(cases) != len(metas):
            bad.append("%d outputs for %d cases" % (len(cases), len(metas)))
        for m, r in zip(metas, cases):
            cnt["cases"] += 1
            g = got_of(fam, r)
            cnt["stops"] += g[0] == "stop"
            if form(g) != form(m["want"]):
                bad.append("case %s: got %s want %s" % (r["c"][1], g, m["want"]))
                continue
            cnt["match"] += 1
            outs[outcome(fam, m, g)] += 1
            for k, v in m["ctl"].items():
                if form(v) != form(m["want"]):
                    sep[k] += 1
                    passed[k] += form(v) == form(g)
            extra_counts(fam, m, g, cnt)
        und = collections.Counter()
        traced = 0
        for kind in ("R", "W"):
            for pc, addr, size, n in tail[kind]:
                traced += 1
                if not accounted(fam, kind, pc, addr):
                    und["%s pc=%06x addr=%08x size=%d" % (kind, pc, addr, size)] += n
        print("S4E5 %s cases=%d match=%d bad=%d stops=%d traced=%d undeclared=%d" % (
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
        if fam == "seq":
            seq_report(metas, cases)
        rc |= 1 if (bad or und) else 0
    print("S4E5 %s" % ("OK" if rc == 0 else "FAILED"))
    return rc


def extra_counts(fam, m, g, cnt):
    if fam == "search" and m["owner"] == 0:
        cnt["player cases, a fit exists, ret 1"] += m["fit"] and g[1] == 1
        cnt["player cases, a fit exists, ret 0"] += m["fit"] and g[1] == 0
        cnt["player cases, no fit, ret 0"] += (not m["fit"]) and g[1] == 0
        cnt["player cases, no fit, ret 1"] += (not m["fit"]) and g[1] == 1
        if g[1] == 1:
            s = inv.InvGrid(m["w0"], m["h0"], [tuple(x) for x in m["occ"]]).score(g[2], g[3], m["iw"], m["ih"])
            cnt["player spots scoring 255"] += s == 255
            cnt["player spots scoring below 255"] += s != 255
    if fam == "search" and m["owner"] != 0:
        cnt["other owners, fit=%d ret=%d" % (m["fit"], g[1])] += 1
    if fam == "gridfree":
        cnt["outside the page, ret %d" % g[1]] += not m["inside"]
        cnt["outside the page, ret differs from a bounded test"] += (not m["inside"]) and \
            form(m["ctl"]["bounded"]) != form(g)


def seq_report(metas, cases):
    for si in range(2):
        got = []
        for m, r in zip(metas, cases):
            if m["seq"] == si:
                g = got_of("seq", r)
                got.append((g[2], g[3]) if g[1] else None)
        print("    worked example %d: emulated %s, spec %s, %s" % (si + 1, got, SEQ_WANT[si],
                                                                    "equal" if got == SEQ_WANT[si] else "DIFFERENT"))
    n = collections.Counter(m["seq"] for m in metas)
    ends = collections.Counter(m["want"][1] == 0 for m in metas)
    print("    sequences %d, steps %d, refusals ending a sequence %d" % (len(n), sum(n.values()), ends[True]))


PINS = [  # (va, mnemonic, operand substring)
    (0x00628BF8, "call", "0x63c560"), (0x00628BFD, "cmp", "eax,0xffffffff"), (0x00628C09, "mov", "eax,0x1"),
    (0x00628BEA, "cmp", "BYTE PTR [eax+0x131],0x0"), (0x0063C5C0, "xor", "esi,esi"), (0x0063C5DA, "cmp", "esi,0x10"),
    (0x0063C59C, "cmp", "eax,0x20637369"), (0x0063C5A3, "cmp", "eax,0x20637374"), (0x0063C4D0, "cmp", "ecx,0xf"),
    (0x0063C4D3, "ja", ""), (0x0063A8AC, "cmp", "ecx,esi"), (0x0063A8D6, "cmp", "eax,edx"),
    (0x00558B1F, "test", "edx,edx"), (0x00558B26, "call", "0x543db0"), (0x00558B2B, "pop", "esi"),
    (0x00558B31, "ret", "0x10"), (0x00558AB2, "je", "0x558b2d"),
    (0x00563716, "call", "0x628ba0"), (0x0056371B, "test", "eax,eax"), (0x0056371D, "je", "0x563816"),
    (0x00563728, "call", "0x63c790"), (0x006246B3, "or", "DWORD PTR [esi+0xc4],0x1"),
    (0x006246E3, "or", "DWORD PTR [esi+0xc4],0x1"), (0x00558AE9, "push", "0x3"), (0x00558AEC, "call", "0x624690"),
]


def cmd_static():
    ok = 0
    for va, mn, sub in PINS:
        out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % va,
                              "--stop-address=0x%x" % (va + 16), EXE], capture_output=True, text=True).stdout
        line = [ln for ln in out.splitlines() if ln.strip().startswith("%x:" % va)]
        txt = line[0].split(":", 1)[1].strip() if line else ""
        good = txt.startswith(mn) and sub in txt
        ok += good
        print("  %s 0x%08X %s" % ("ok " if good else "BAD", va, txt))
    print("S4E5 static pins=%d ok=%d" % (len(PINS), ok))
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

#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S4e part 4 (`lane/n66z`): the other item request handlers, InvItemToCursor, InvPlaceItem's
refusals, InvPageGet and InvRowForUnit, run on the pinned Game.exe under Ghidra's p-code emulator (ADR-0015, ADR-0021)
with re/ghidra_scripts/EmuBoundary.java, compared with the models below. Parts 1 to 3 (tools/stats_s4e_emu.py,
tools/items_s4e_emu.py, tools/items_s4e3_emu.py, run/, run2/, run3/) stay unchanged; this tool imports part 3's world.

    python3 -I tools/items_s4e4_emu.py cases [--dir D] [--limit N]   write D/<family>.cases, .mem, .json
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/items_s4e4_emu.py check [--dir D]               compare, account every traced access, controls
    python3 -I tools/items_s4e4_emu.py static                        objdump pins, the read-only sections, the writers
    python3 -I tools/items_s4e4_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66z/s4e/run4. Every draw comes from random.Random("n66z-s4e4-<family>").

A case is a declared scratch image (part 3's, plus the inventory's page array, its body cells, the item list and an
Items/ItemTypes/inventory table set as tools/item_emu2.py declares them). Nothing is patched. Every callee before a
family's boundaries runs emulated: part 3's (GameFindUnit, PktIsCursorItem, PktInvItemBad, PktBeltItemBad,
PktOwnedItemBad, INV_GetCursorItem, PlayerIsBusy, PlayerGetInteract, InvMoveInteractTest, TradeItemTest's first tests),
and InvGetBodyLocItem with InvPageGet, TradeBeltLock with the item-list walk, ItemGetPage, ItemTypeBeltable
(ITEMS_GetType, the Items and ItemTypes rows), InvClearUseMarks over an item list with no flagged item, InvRowForUnit,
0x0063BCC0 and InvGridPut with InvRecordGrid.

Families (function, convention; boundaries; inventory rows):
  body    the handlers of 0x1A..0x1E (0x0054AD90, 0x0054AE30, 0x0054AEC0, 0x0054AF50, 0x0054B030): to the return,
          ItemEquip 0x005606B0, EquipCursorAtSlot 0x00563D20, BodyToCursor 0x00560CD0, BodySwapCursor 0x00560F00,
          BodySwapCursor2 0x00561220, or InvMoveInteractTest's boundaries (part 3's).               inventory 32, 40
  req     the handlers of 0x1F, 0x21..0x25, 0x63: to the return, PageSwapCursor 0x00561B00, StackRequest 0x0055E7C0,
          the stub 0x0055E9A0, ItemToBelt 0x0055E9B0, BeltToCursor 0x00562250, BeltSwapCursor 0x0055EB30, NoManaMsg
          0x00549A60, BeltFreeSlot 0x0063C600, or InvMoveInteractTest's boundaries.  inventory 33, 34, 36, 37, 38, 39, 40
  tocur   InvItemToCursor 0x00560420 (ECX game, EDX player, guid, &out, a3, a4, inv, force): to the return or
          InvTakeItem 0x0063AD90.                                                                     inventory 42, 46
  place   InvPlaceItem 0x00560200 (game, player, guid, x, y, 0, f20, 0), the item on the cursor with a page byte:
          to the return or InvItemRemove 0x0063AAF0 (inside InvGridPut), the page byte dumped.   inventory 23, 45, 99
  pageget InvPageGet 0x0063ADD0 (EAX page, EDI inventory, row): to the return; the allocators are guards.  inventory 15
  rowfor  InvRowForUnit 0x00621050 (unit, page, expansion): to the return, every page byte.            inventory 17

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

import sweep_s1e as E  # noqa: E402
import sweep_s4b as S4  # noqa: E402
import item_inventory as inv  # noqa: E402
import item_emu2 as IE2  # noqa: E402
import items_s4e3_emu as P3  # noqa: E402
from anim_s6f_emu import read_out  # noqa: E402

M32 = 0xFFFFFFFF
DEFDIR = os.path.join(ROOT, "workspace", "logs", "n66z", "s4e", "run4")
FAMILIES = ("body", "req", "tocur", "place", "pageget", "rowfor")
NCASES = {"body": 3000, "req": 4000, "tocur": 1500, "place": 2500, "pageget": 1000, "rowfor": None}
GAME, PLAYER, PDATA, INVB, ITEMS, OTHERS, PKT = P3.GAME, P3.PLAYER, P3.PDATA, P3.INVB, P3.ITEMS, P3.OTHERS, P3.PKT
SIG = P3.SIG
PAGES, BODYC, GRIDC, OUTP = 0x23060100, 0x23060300, 0x23060400, 0x23061F00   # page array, body cells, grid cells
ROWU = 0x23062000                                                               # rowfor's unit
ZERO = P3.ZERO + [(0x23060000, 0x2000), (ROWU, 0x20), (IE2.RECS + 7 * 0x1A8, 6 * 0x1A8), (IE2.INVT, 16 * 0xF0),
                  (IE2.TYPES, 4 * 0xE4)]
GUARDS = P3.GUARDS
BODYROW = 0x0074479C            # InvGetBodyLocItem's row argument: the body page's 13 x 1 (.data, two bytes)
ROWTAB, ROWCNT = 0x00744544, 0x0074457C
CLS_BELT, CLS_PLAIN = 7, 8      # Items rows declared: 7 beltable type, 8 plain type

F_H = {0x1A: 0x0054AD90, 0x1B: 0x0054AE30, 0x1C: 0x0054AEC0, 0x1D: 0x0054AF50, 0x1E: 0x0054B030, 0x1F: 0x0054B0F0,
       0x21: 0x0054B300, 0x22: 0x0054B380, 0x23: 0x0054B3E0, 0x24: 0x0054B450, 0x25: 0x0054B4E0, 0x63: 0x0054D520}
B = {"equip": (0x005606B0, 0x0054ADFC), "equipslot": (0x00563D20, 0x0054AE95), "body2cur": (0x00560CD0, 0x0054AF30),
     "bodyswap": (0x00560F00, 0x0054B00B), "bodyswap2": (0x00561220, 0x0054B0CE), "pageswap": (0x00561B00, 0x0054B1AC),
     "stack": (0x0055E7C0, 0x0054B352), "unstack": (0x0055E9A0, 0x0054B3B9), "tobelt": (0x0055E9B0, 0x0054B428),
     "belt2cur": (0x00562250, 0x0054B4B8), "beltswap": (0x0055EB30, 0x0054B536), "nomana": (0x00549A60, 0x0054D56C),
     "beltfree": (0x0063C600, 0x0054D5C4), "take": (0x0063AD90, 0x00560535), "unlink": (0x0063AAF0, None)}
MOVE_OBS = (P3.B_CLEAR, P3.B_NPC, P3.B_TRADE)
F_TOCUR, F_PLACE, F_PAGEGET, F_ROWFOR = 0x00560420, 0x00560200, 0x0063ADD0, 0x00621050
ALLOC = 0x0040B430
OBSERVE = {"body": tuple(B[k][0] for k in ("equip", "equipslot", "body2cur", "bodyswap", "bodyswap2")) + MOVE_OBS,
           "req": tuple(B[k][0] for k in ("pageswap", "stack", "unstack", "tobelt", "belt2cur", "beltswap", "nomana",
                                          "beltfree")) + MOVE_OBS,
           "tocur": (B["take"][0],), "place": (B["unlink"][0],), "pageget": (), "rowfor": ()}


def s32(v):
    return P3.s32(v)


def obs(name, regs, args, dumps=None):
    fn, site = B[name]
    out = ["obs", fn, site, regs, args]
    if dumps:
        out.append(dumps)
    return out


# ================================================================================================= the world
def put_inv4(w, r, cursor=0, sig=SIG, body=None, bodysize=(13, 1), chain=(), count=8):
    """Part 3's inventory plus the page array (+0x14, count +0x18), page 0's body cells and the item list (+0xC: the
    first item; each item's data +0x64 the next, +0x69 the location byte)."""
    P3.put_inv(w, cursor=cursor, sig=sig)
    c = w.c
    c.d32(INVB + 0x14, PAGES)
    c.d32(INVB + 0x18, count)
    c.d8(PAGES + 8, bodysize[0])
    c.d8(PAGES + 9, bodysize[1])
    c.d32(PAGES + 0xC, BODYC)
    w.body = [0] * 13
    for s, a in (body or {}).items():
        w.body[s] = a
        c.d32(BODYC + 4 * s, a)
    w.bodysize = bodysize
    w.chain = list(chain)
    if chain:
        c.d32(INVB + 0xC, chain[0][0])
        for (a, loc), nxt in zip(chain, list(chain[1:]) + [(0, 0)]):
            c.d32(a + 0x200 + 0x64, nxt[0])
            c.d8(a + 0x200 + 0x69, loc)


def body_item(w, s):
    """InvGetBodyLocItem 0x0063BDE0 (inventory, slot): page 0 by InvPageGet with the 13 x 1 row; 0 on a size mismatch."""
    if w.inv[INVB]["sig"] != SIG or s > 12:
        return 0
    if w.bodysize != (13, 1):
        return 0
    return w.body[s]


def trade_belt_lock(w):
    """TradeBeltLock 0x00567840 (EDX player): 0 when interacting with a player (type 0) and a listed item's location
    byte is 2 (a belt), else 1."""
    fl, _, ity = w.interact(PLAYER)
    if not fl or ity != 0:
        return 1
    for a, loc in w.chain:
        if loc == 2:
            return 0
    return 1


def partner(w, r):
    """The interaction partner and PlayerData words as part 3's `mv` family draws them."""
    w.pd = collections.defaultdict(dict)
    iflag = r.choice([0, 0, 0, 1, 1, 0x80])
    ity = r.choice([0, 0, 0, 1, 2, 3, 4, 5])
    others = []
    for k in range(2):
        t = ity if k == 0 else r.choice([0, 1, 2])
        g = r.randrange(1, 0x400)
        a = OTHERS[k]
        w.unit(a, t, g, data=a + 0x200 if t == 0 else 0)
        if t == 0:
            v = r.choice([0, 0, 1, r.getrandbits(32)])
            w.pd[a][0x5C] = v
            w.c.d32(a + 0x200 + 0x5C, v)
        others.append((a, t, g))
    iid = r.choice([others[0][2], others[0][2], others[1][2], r.randrange(1, 0x400)])
    return dict(iflag=iflag, iid=iid, itype=ity)


def pd_words(w, r):
    for off, choices in ((0x4C, [0, 0, 0, 1, r.getrandbits(32)]), (0x50, [0, 0, 4, 5, 1, -1 & M32, 0x80000000])):
        v = r.choice(choices)
        w.pd[PLAYER][off] = v
        w.c.d32(PDATA + off, v)


def tables(w, item_classes):
    for row, typ in ((CLS_BELT, IE2.BELTABLE_TYPE), (CLS_PLAIN, IE2.PLAIN_TYPE)):
        IE2.put_rec(w.c, row, 1, 1, typ=typ)
    for a, cls in item_classes.items():
        w.c.d32(a + 4, cls)
        w.u[a]["cls"] = cls


def move_res(w):
    """InvMoveInteractTest, part 3's model: 0, non-zero, or an observed boundary."""
    t = P3.move_test(w)
    if isinstance(t, tuple):
        return ["obs", t[1], None, {}, []]
    return t


def world(r, modes, fav, ptyp=0, chainp=0.5):
    w = P3.W()
    w.pd = collections.defaultdict(dict)
    kw = partner(w, r)
    P3.put_player(w, r, ptyp, **kw)
    pd_words(w, r)
    w.pd[PLAYER].setdefault(0x4C, 0)
    its, missing = P3.items_world(w, r, 4, modes=modes, fav=fav)
    tables(w, {a: r.choice([CLS_BELT, CLS_BELT, CLS_PLAIN]) for a, _ in its})
    return w, its, missing


def chain_of(w, r, its, p=0.5):
    if r.random() > p:
        return ()
    with_data = [a for a, _ in its if w.u[a].get("data")]
    r.shuffle(with_data)
    return tuple((a, r.choice([0, 1, 2, 3, 2, 0xFF])) for a in with_data[:r.randrange(0, len(with_data) + 1)])


def bodymap(r, its):
    m = {}
    for s in range(1, 11):
        if r.random() < 0.6:
            m[s] = r.choice([a for a, _ in its])
    return m


# ================================================================================================= body
def model_body(w, op, length, f, ctl=None):
    good = 3 if op == 0x1C else 9
    if length != good:
        return ["ret", 3, 8]
    rg = {"ecx": GAME, "edx": PLAYER}
    if op == 0x1C:
        s = f[1] & 0xFFFF
    else:
        c = P3.cursor_bad(w, f[1])
        if c:
            return ["ret", c, 8]
        s = f[5] & 0xFF
    if (s - 1 > 9 or s - 1 < 0) if ctl != "slot_signed" else s - 1 > 9:
        return ["ret", 2, 8]
    if op == 0x1A:
        return obs("equip", rg, [f[1], ("lo8", s), 0, None])
    if op == 0x1B:
        return obs("equipslot", rg, [f[1], s, 0, None])
    if op == 0x1C:
        t = move_res(w)
        if isinstance(t, list):
            return t
        if not t:
            return ["ret", 0, 8]
        if s == 8 and not trade_belt_lock(w) and ctl != "no_lock":
            return ["ret", 0, 8]
        return obs("body2cur", rg, [s, 0, None])
    if op == 0x1D:
        if not body_item(w, s) and ctl != "nobody_ok":
            return ["ret", 1, 8]
        if s == 8 and not trade_belt_lock(w) and ctl != "no_lock":
            return ["ret", 0, 8]
        t = move_res(w)
        if isinstance(t, list):
            return t
        if not t:
            return ["ret", 0, 8]
        return obs("bodyswap", rg, [f[1], s, 0, None])
    if s not in (4, 5) and ctl != "swap2_any":
        return ["ret", 3, 8]
    if not body_item(w, s) and ctl != "nobody_ok":
        return ["ret", 1, 8]
    t = move_res(w)
    if isinstance(t, list):
        return t
    if not t:
        return ["ret", 0, 8]
    return obs("bodyswap2", rg, [f[1], s, None])


def gen_body(r):
    op = r.choice([0x1A, 0x1B, 0x1C, 0x1C, 0x1D, 0x1D, 0x1E, 0x1E])
    w, its, missing = world(r, (4, 4, 4, 0, 1, 2), 4)
    if r.random() < 0.3:                 # an interaction with a player, so TradeBeltLock walks the item list
        w.u[PLAYER].update(iflag=1, itype=0)
        w.c.d8(PLAYER + P3.IFLAG, 1)
        w.c.d32(PLAYER + P3.ITYPE, 0)
    cur = its[0][0] if r.random() < 0.8 else r.choice([a for a, _ in its] + [0])
    bs = (13, 1) if r.random() < 0.93 else r.choice([(12, 1), (13, 2), (10, 4)])
    put_inv4(w, r, cursor=cur, body=bodymap(r, its), bodysize=bs, chain=chain_of(w, r, its, 0.7))
    w.finish()
    good = 3 if op == 0x1C else 9
    length = good if r.random() < 0.92 else r.choice([0, 3, 5, 9, 13])
    sl = r.choice([1, 2, 3, 4, 4, 5, 5, 6, 7, 8, 8, 8, 8, 9, 10, 0, 11, 12, 13, 0xFF])
    if op == 0x1C:
        f = {1: sl | (r.choice([0, 0, r.getrandbits(16)]) << 16)}
    else:
        g = P3.pick_guid(r, its, missing) if r.random() < 0.85 or not cur else w.u[cur]["guid"]
        f = {1: g, 5: sl | (r.getrandbits(24) << 8)}
    P3.pkt(w, length, f)
    want = model_body(w, op, length, f)
    ctl = {k: model_body(w, op, length, f, k) for k in ("slot_signed", "no_lock", "nobody_ok", "swap2_any")}
    tag = ("ret%d" % want[1]) if want[0] == "ret" else "%08X" % want[1]
    br = {"b%02X_%s" % (op, tag): 1}
    if want[0] == "obs" and op != 0x1C:
        br["b%02X_slot%d" % (op, f[5] & 0xFF)] = 1
    return [w.c.call(F_H[op], GAME, PLAYER, PKT, length)], {"fn": F_H[op], "op": op, "want": want, "ctl": ctl, "br": br}


# ================================================================================================= req
def beltable(w, it):
    return int(w.u[it].get("cls") == CLS_BELT)


def model_req(w, op, length, f, ctl=None):
    rg = {"ecx": GAME, "edx": PLAYER}
    good = {0x1F: 17, 0x21: 9, 0x22: 5, 0x23: 9, 0x24: 5, 0x25: 9, 0x63: 5}[op]
    if length != good:
        return ["ret", 3, 8]
    if op == 0x1F:
        for b in (P3.cursor_bad(w, f[1]), P3.inv_item_bad(w, f[5])):
            if b:
                return ["ret", b, 8]
        it = w.find(4, f[5])
        if w.u[it]["page"] in (1, 2) and ctl != "page12_ok":
            return ["ret", 3, 8]
        t = move_res(w)
        if isinstance(t, list):
            return t
        if not t:
            return ["ret", 0, 8]
        return obs("pageswap", rg, [f[1], f[5], f[9], f[13], None])
    if op in (0x21, 0x22):
        gs = (f[1], f[5]) if op == 0x21 else (f[1],)
        for g in gs:
            if P3.owned_item_bad(w, g):
                return ["ret", 1, 8]
        if op == 0x22:
            return obs("unstack", rg, [f[1], None])
        if f[1] == f[5] and ctl != "same_ok":
            return ["ret", 3, 8]
        return obs("stack", rg, [f[1], f[5], None])
    if op == 0x23:
        if P3.cursor_bad(w, f[1]):
            return ["ret", 1, 8]
        return obs("tobelt", rg, [f[1], f[5], 0, None])
    if op == 0x24:
        if P3.belt_item_bad(w, f[1]):
            return ["ret", 1, 8]
        if ctl == "cursor_first" and w.cursor(INVB):
            return ["ret", 2, 8]
        t = move_res(w)
        if isinstance(t, list):
            return t
        if not t:
            return ["ret", 0, 8]
        if w.cursor(INVB):
            return ["ret", 2, 8]
        return obs("belt2cur", rg, [f[1], None])
    if op == 0x25:
        if P3.cursor_bad(w, f[1]) or P3.belt_item_bad(w, f[5]):
            return ["ret", 1, 8]
        return obs("beltswap", rg, [f[1], f[5], None])
    b = P3.inv_item_bad(w, f[1])
    if b:
        return ["ret", b, 8]
    if w.cursor(INVB):
        return obs("nomana", {"ecx": PLAYER}, [])
    it = w.find(4, f[1])
    if not beltable(w, it) and ctl != "beltable_ignored":
        return ["ret", 2, 8]
    if w.u[it]["page"] != 0 and ctl != "page_any":
        return ["ret", 3, 8]
    return obs("beltfree", {}, [INVB, it, None])


def gen_req(r):
    op = r.choice([0x1F, 0x1F, 0x21, 0x21, 0x22, 0x23, 0x24, 0x24, 0x25, 0x63, 0x63])
    fav = {0x1F: 4, 0x21: 0, 0x22: 0, 0x23: 4, 0x24: 2, 0x25: 4, 0x63: 0}[op]
    w, its, missing = world(r, (0, 0, 2, 2, 4, 4, 1, 3), fav)
    if op in (0x1F, 0x25) and r.random() < 0.8:      # a second item: owned, mode 0 (0x1F) or 2 (0x25)
        a = its[1][0]
        if w.u[a].get("data"):
            m = 0 if op == 0x1F else 2
            w.u[a].update(mode=m, owner=INVB)
            w.c.d32(a + 0x10, m)
            w.c.d32(a + 0x200 + 0x5C, INVB)
    if op in (0x1F, 0x23, 0x25):
        cur = its[0][0] if r.random() < 0.8 else r.choice([a for a, _ in its] + [0])
    else:
        cur = r.choice([0, 0, 0, 0] + [a for a, _ in its])
    put_inv4(w, r, cursor=cur, chain=chain_of(w, r, its, 0.4))
    w.finish()
    good = {0x1F: 17, 0x21: 9, 0x22: 5, 0x23: 9, 0x24: 5, 0x25: 9, 0x63: 5}[op]
    length = good if r.random() < 0.92 else r.choice([0, 3, 5, 9, 13, 17])

    def g(k):
        if op in (0x1F, 0x23, 0x25) and k == 1 and cur and r.random() < 0.7:
            return w.u[cur]["guid"]
        if op == 0x1F and k == 5:
            return r.choice([a for a in [w.u[x]["guid"] for x, _ in its[1:]]] + [missing])
        if op == 0x25 and k == 5:
            return r.choice([w.u[x]["guid"] for x, _ in its] + [missing])
        return P3.pick_guid(r, its, missing)
    f = {1: g(1), 5: g(5), 9: r.getrandbits(32), 13: r.getrandbits(32)}
    if op == 0x21 and r.random() < 0.2:
        f[5] = f[1]
    if op == 0x23:
        f[5] = r.choice([0, 1, 3, 15, 16, r.getrandbits(32)])
    P3.pkt(w, length, f)
    want = model_req(w, op, length, f)
    ctl = {k: model_req(w, op, length, f, k) for k in ("page12_ok", "same_ok", "cursor_first", "beltable_ignored",
                                                       "page_any")}
    tag = ("ret%d" % want[1]) if want[0] == "ret" else "%08X" % want[1]
    return [w.c.call(F_H[op], GAME, PLAYER, PKT, length)], {"fn": F_H[op], "op": op, "want": want, "ctl": ctl,
                                                             "br": {"r%02X_%s" % (op, tag): 1}}


# ================================================================================================= tocur
def model_tocur(w, guid, a3, a4, invov, force, ctl=None):
    ib = invov or INVB
    if w.cursor(ib) and not force and ctl != "force_ignored":
        return ["ret", 0, 0x18, {"out": (OUTP, 0)}]
    if ctl == "force_ignored" and w.cursor(ib) and not force:
        pass
    it = w.find(4, guid)
    if not it:
        return ["ret", 0, 0x18, {"out": (OUTP, 1)}]
    u = w.u[it]
    page = u["page"] if u.get("data") else 0xFF
    if w.u[PLAYER]["type"] == 0 and not P3.is_busy(w) and page != 0 and ctl != "busy_ignored":
        return ["ret", 0, 0x18, {"out": (OUTP, 1)}]
    if u["mode"] != 0 and ctl != "mode_any":
        return ["ret", 0, 0x18, {"out": (OUTP, 1)}]
    return ["obs", B["take"][0], B["take"][1], {}, [ib, it], {"out": (OUTP, 0), "c4": (it + 0xC4, u["c4"] & ~2 & M32)}]


def gen_tocur(r):
    ptyp = 0 if r.random() < 0.85 else 1
    w, its, missing = world(r, (0, 0, 0, 1, 2, 4), 0, ptyp=ptyp)
    for a, _ in its:
        v = r.getrandbits(32)
        w.u[a]["c4"] = v
        w.c.d32(a + 0xC4, v)
    cur = r.choice([0, 0, 0] + [a for a, _ in its])
    put_inv4(w, r, cursor=cur, chain=chain_of(w, r, its, 0.5))
    w.finish()
    guid = P3.pick_guid(r, its, missing)
    a3, a4 = r.choice([1, 1, 0, 2]), r.choice([0, 0, 1])
    force = r.choice([0, 0, 0, 1])
    invov = 0
    w.c.d32(OUTP, 0x55555555)
    w.c.dump(OUTP, 4)
    for a, _ in its:
        w.c.dump(a + 0xC4, 4)
    want = model_tocur(w, guid, a3, a4, invov, force)
    ctl = {k: model_tocur(w, guid, a3, a4, invov, force, k) for k in ("busy_ignored", "mode_any", "force_ignored")}
    tag = ("ret_out%d" % want[3]["out"][1]) if want[0] == "ret" else "take"
    pg = w.u[w.find(4, guid)]["page"] if w.find(4, guid) and w.u[w.find(4, guid)].get("data") else -1
    br = {"tc_%s" % tag: 1, "tc_page%s" % ("0" if pg == 0 else "n"): 1, "tc_busy%d" % bool(P3.is_busy(w)): 1}
    return [w.c.call(F_TOCUR, GAME, PLAYER, guid, OUTP, a3, a4, invov, force)], {"fn": F_TOCUR, "want": want,
                                                                                  "ctl": ctl, "br": br}


# ================================================================================================= place
def model_place(w, guid, x, y, ctl=None):
    it = w.find(4, guid)
    if not it or w.u[it]["mode"] != 4:
        return ["ret", 0, 0x20]
    u = w.u[it]
    if not u.get("data"):
        return ["ret", 0, 0x20]          # InvGridPut refuses an item with no data (0x0063B003) before its size
    page = u["page"]
    keep = {"page": (it + 0x200 + 0x45, page)} if u.get("data") else {}
    if ctl == "page_reset" and u.get("data"):
        keep = {"page": (it + 0x200 + 0x45, 0xFF)}
    row = inv.inv_row(w.u[PLAYER]["type"], w.u[PLAYER].get("cls", 0), page, w.exp)
    if ctl != "noclamp":
        x, y = max(s32(x), 0), max(s32(y), 0)
    else:
        x, y = s32(x), s32(y)
    idx = page + 2
    if idx >= 8:
        return ["stop", 0x0040B4B0]
    gw, gh = w.rows[row]
    pw, ph, occ = w.pages[idx]
    iw, ih = w.isize[it]
    ok = iw > 0 and ih > 0
    if (pw, ph) != (gw, gh) and ctl != "size_ignored":
        ok = False
    if idx >= 2:
        ok = ok and 0 <= x and x + iw <= pw and 0 <= y and y + ih <= ph
    else:
        iw = ih = 1
    if ok:
        ok = inv.InvGrid(pw, ph, occ).free(x, y, iw, ih)
    if ok:
        return ["obs", B["unlink"][0], None, {}, [], keep]
    return ["ret", 0, 0x20, keep]


def gen_place(r):
    w, its, missing = world(r, (4, 4, 4, 0, 3), 4)
    w.isize = {}
    for k, (a, _) in enumerate(its):
        iw, ih = r.choice([(1, 1), (1, 1), (2, 2), (1, 3), (2, 3), (2, 4), (1, 2), (0, 1)])
        row = 9 + k
        IE2.put_rec(w.c, row, iw, ih)
        w.c.d32(a + 4, row)
        w.isize[a] = (iw, ih)
    # the item's page byte, as packet 0x18 leaves it before the call
    pages = {a: r.choice([0, 0, 2, 3, 4, 4, 1]) for a, _ in its}
    for a, p in pages.items():
        w.u[a]["page"] = p
        if w.u[a].get("data"):
            w.c.d8(a + 0x200 + 0x45, p)
    w.exp = r.choice([0, 1, 1])
    w.c.d32(GAME + 0x70, w.exp)
    cls = r.choice([0, 1, 2, 3, 4, 5, 6])
    w.u[PLAYER]["cls"] = cls
    w.c.d32(PLAYER + 4, cls)
    put_inv4(w, r, cursor=its[0][0], chain=chain_of(w, r, its, 0.4))
    # inventory rows (gridX, gridY) and the pages made: each page 2..6 at its row's size, or another size
    w.rows = {}
    for row in range(16):
        gw, gh = r.choice(IE2.STOCK_GRIDS)
        w.rows[row] = (gw, gh)
        IE2.put_row(w.c, row, gw, gh)
    w.pages = {}
    for idx in range(2, 7):
        rowof = inv.inv_row(0, cls, idx - 2, w.exp)
        gw, gh = w.rows[rowof]
        if r.random() < 0.15:
            gw, gh = r.choice([s for s in IE2.STOCK_GRIDS if s != (gw, gh)])
        occ = IE2.rand_grid(r, gw, gh)
        cells = [0] * (gw * gh)
        for rr, cc in occ:
            cells[rr * gw + cc] = ITEMS[3]
        base = GRIDC + (idx - 2) * 0x200
        w.c.d8(PAGES + idx * 0x10 + 8, gw)
        w.c.d8(PAGES + idx * 0x10 + 9, gh)
        w.c.d32(PAGES + idx * 0x10 + 0xC, base)
        w.c.put(base, b"".join(P3.le32(v) for v in cells))
        w.pages[idx] = (gw, gh, occ)
    w.finish()
    guid = its[0][1] if r.random() < 0.9 else P3.pick_guid(r, its, missing)
    pw = w.pages[(w.u[its[0][0]]["page"]) + 2][0]
    x = r.choice([r.randrange(-3, pw + 2), r.randrange(-3, 2), -1 & M32, 0x80000000, r.getrandbits(32)])
    y = r.choice([r.randrange(-3, 6), r.randrange(-3, 2), -1 & M32, 0x80000000])
    f20 = r.choice([1, 1, 0])
    it = w.find(4, guid)
    if it and w.u[it].get("data"):
        w.c.dump(it + 0x200 + 0x45, 1)
    want = model_place(w, guid, x, y)
    ctl = {k: model_place(w, guid, x, y, k) for k in ("noclamp", "page_reset", "size_ignored")}
    neg = s32(x) < 0 or s32(y) < 0
    br = {"pl_%s" % ("unlink" if want[0] == "obs" else "ret0"): 1, "pl_neg%d" % neg: 1}
    if it:
        br["pl_page%d" % w.u[it]["page"]] = 1
    return [w.c.call(F_PLACE, 0x006E1050, 0xBF6, GAME, PLAYER, guid, x & M32, y & M32, 0, f20, 0)], \
        {"fn": F_PLACE, "want": want, "ctl": ctl, "br": br}


# ================================================================================================= pageget
def model_pageget(w, idx, rec, ctl=None):
    cnt = s32(w.count)
    if not (cnt > s32(idx)) if ctl != "unsigned_idx" else not (idx & M32) < (cnt & M32):
        if not rec:
            return ["ret", 0, 4]
        return ["stop", 0x0040B4B0]
    off = (idx << 4) & M32                  # shl esi, 4: the index wraps (0x80000000 names page 0)
    ent = (PAGES + off) & M32
    cells, size = w.pg.get(s32(off) // 16, (0, (0, 0)))
    if not rec:
        return ["ret", ent if cells else 0, 4]
    if not cells:
        return ["stop", ALLOC]
    if size != w.recsize and ctl != "size_ignored":
        return ["ret", 0, 4]
    return ["ret", ent, 4]


def gen_pageget(r):
    w = P3.W()
    w.count = r.choice([8, 8, 8, 1, 3, 0])
    w.c.d32(INVB, SIG)
    w.c.d32(INVB + 0x14, PAGES)
    w.c.d32(INVB + 0x18, w.count)
    w.pg = {}
    w.recsize = r.choice(IE2.STOCK_GRIDS + ((13, 1), (16, 1)))
    REC = 0x23061E00
    w.c.d8(REC, w.recsize[0])
    w.c.d8(REC + 1, w.recsize[1])
    for i in range(-1, 9):
        if r.random() < 0.8:
            size = w.recsize if r.random() < 0.6 else r.choice(IE2.STOCK_GRIDS + ((13, 1), (16, 1)))
            cells = GRIDC + 0x100 * (i + 1)
            w.c.d8(PAGES + 0x10 * i + 8, size[0])
            w.c.d8(PAGES + 0x10 * i + 9, size[1])
            w.c.d32(PAGES + 0x10 * i + 0xC, cells)
            w.pg[i] = (cells, size)
    idx = r.choice(list(range(-1, 10)) + [0x80000000, 0x7FFFFFFF])
    rec = REC if r.random() < 0.7 else 0
    want = model_pageget(w, idx, rec)
    ctl = {k: model_pageget(w, idx, rec, k) for k in ("size_ignored", "unsigned_idx")}
    tag = want[0] + ("_%x" % want[1] if want[0] == "stop" else ("_ent" if want[1] else "_0"))
    lines = ["r eax %08x" % (idx & M32), "r edi %08x" % INVB, w.c.call(F_PAGEGET, 0, 0, rec)]
    return lines, {"fn": F_PAGEGET, "want": want, "ctl": ctl, "br": {"pg_%s" % tag: 1, "pg_rec%d" % bool(rec): 1}}


# ================================================================================================= rowfor
def model_rowfor(t, cls, page, exp, ctl=None):
    v = inv.inv_row(t, cls, page & 0xFF, exp, "stashsmall" if ctl == "stashsmall" else None)
    if ctl == "page_dword" and t == 0:
        v = inv.inv_row(t, cls, page, exp)
    return ["ret", v & M32, 0xC]


def rowfor_cases():
    """Every page byte for each player class 0..7 and two expansion words; the other types over their classes."""
    out = []
    rnd = random.Random("n66z-s4e4-rowfor")
    for cls in list(range(8)) + [0x152, rnd.getrandbits(32)]:
        for page in range(256):
            for exp in (0, rnd.choice([1, 2, 0x80000000, rnd.getrandbits(32) | 1])):
                out.append((0, cls, page | (rnd.choice([0, 0, rnd.getrandbits(24)]) << 8), exp))
    for t in (1, 2, 3, 4, 5, 6, 0x80000000, rnd.getrandbits(32)):
        for cls in list(range(8)) + [0x151, 0x152, 0x153, 0x154, rnd.getrandbits(32)]:
            for page in (0, 1, 2, 3, 4, 5, 0xFF, rnd.getrandbits(32)):
                out.append((t, cls, page, rnd.choice([0, 1])))
    return out


def gen_rowfor_all():
    lines, meta = [], []
    for t, cls, page, exp in rowfor_cases():
        c = P3.Case()
        c.d32(ROWU, t)
        c.d32(ROWU + 4, cls)
        want = model_rowfor(t, cls, page, exp)
        ctl = {k: model_rowfor(t, cls, page, exp, k) for k in ("stashsmall", "page_dword")}
        lines.append(c.call(F_ROWFOR, 0, 0, ROWU, page, exp))
        meta.append({"fn": F_ROWFOR, "want": want, "ctl": ctl, "br": {"row_%d" % s32(want[1]): 1, "rf_t%d" % min(t, 7): 1}})
    return lines, meta


GEN = {"body": gen_body, "req": gen_req, "tocur": gen_tocur, "place": gen_place, "pageget": gen_pageget}


# ================================================================================================= commands
def mem_spec(fam):
    out = ["# plan 0066 S4e part 4: zero-filled scratch regions, re-applied before every case"]
    for lo, n in ZERO:
        out.append("bytes %08x %s" % (lo, "00" * n))
    out += ["dword 00744304 %08x" % IE2.DTBL, "dword %08x %08x" % (IE2.DTBL + 0xBFC, IE2.NTYPES),
            "dword %08x %08x" % (IE2.DTBL + 0xBF8, IE2.TYPES),
            "bytes %08x 01" % (IE2.TYPES + IE2.BELTABLE_TYPE * 0xE4 + 0x19),
            "bytes %08x 00" % (IE2.TYPES + IE2.PLAIN_TYPE * 0xE4 + 0x19),
            "dword 0096ca58 00000097", "dword 0096ca5c %08x" % IE2.RECS,
            "dword 0096d4f0 00000020", "dword 0096d4f4 %08x" % IE2.INVT]
    out += ["guard %08x" % g for g in GUARDS]
    out += ["observe %08x" % b for b in OBSERVE[fam]]
    return out


def cmd_cases(d, limit=None):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        if fam == "rowfor":
            cases, meta = gen_rowfor_all()
            if limit:
                cases, meta = cases[:limit], meta[:limit]
        else:
            rnd = random.Random("n66z-s4e4-%s" % fam)
            cases, meta = [], []
            for _ in range(limit or NCASES[fam]):
                lines, a = GEN[fam](rnd)
                cases.extend(lines)
                meta.append(a)
        E.write_family(d, fam, cases, mem_spec(fam), {"cases": meta})
        print("%s: %d cases" % (fam, len(meta)))


RS = P3.RS + [(BODYROW, BODYROW + 2, "r", "InvGetBodyLocItem's row 0x0074479C (.data, 13 x 1)"),
              (ROWTAB, ROWCNT + 4, "r", "InvRowForUnit's class table and count 0x00744544..0x0074457F (.data)"),
              (0x00621134, 0x00621144, "r", "InvRowForUnit's switch table 0x00621134 (.text)")]
DATA_OK = {BODYROW, ROWTAB}     # .data ranges: `static` lists every instruction that names them (no writer)


def judge(c, want):
    if want[0] == "stop":
        return ("stop" in c and c["stop"] == want[1]), ["stop", "%08X" % c.get("stop", 0)]
    if "stop" in c:
        return False, ["stop", "%08X" % c["stop"], c.get("msg")]
    dumps = want[3] if want[0] == "ret" and len(want) > 3 else (want[5] if want[0] == "obs" and len(want) > 5 else {})
    for k, (addr, v) in dumps.items():
        got = c["dumps"].get(addr, b"")
        n = 1 if k == "page" else 4
        if got[:n] != (bytes([v]) if n == 1 else struct.pack("<I", v & M32)):
            return False, [k, got.hex()]
    if want[0] == "ret":
        got = ["ret", c.get("eax"), c.get("pop")] if "obs" not in c else ["obs", "%08X" % c["obs"]]
        return got[:3] == want[:3], got
    if "obs" not in c:
        return False, ["ret", c.get("eax"), c.get("pop")]
    args = list(c.get("args", (0,) * 16))
    got = ["obs", "%08X" % c["obs"], "%08X" % args[0], [hex(x) for x in args[1:1 + len(want[4])]]]
    if c["obs"] != want[1] or (want[2] is not None and args[0] != want[2]):
        return False, got
    if any(c["regs"].get(k) != v for k, v in want[3].items()):
        return False, got + [c["regs"]]
    for i, v in enumerate(want[4]):
        a = args[1 + i]
        if v is None:
            continue
        if isinstance(v, (list, tuple)) and v[0] == "lo8":
            if a & 0xFF != v[1]:
                return False, got
        elif a != v & M32:
            return False, got
    return True, got


class Report(E.Report):
    def line(self):
        keys = ["cases", "match", "bad", "neg", "traced", "undeclared", "guard_stops"]
        rest = sorted(k for k in self.c if k not in keys)
        return "S4E4 %s " % self.fam + " ".join("%s=%d" % (k, self.c[k]) for k in keys + rest)


def form(x):
    return json.dumps(x, sort_keys=True)


def cmd_check(d, fams=FAMILIES):
    rc = 0
    for fam in fams:
        p = os.path.join(d, fam + ".out")
        if not os.path.exists(p):
            print("S4E4 %s: no output" % fam)
            rc = 1
            continue
        calls, reads, writes = read_out(p)
        meta = json.load(open(os.path.join(d, fam + ".json")))["cases"]
        rep = Report(fam)
        sep, passed, sites = collections.Counter(), collections.Counter(), collections.Counter()
        hi8 = collections.Counter()
        if len(calls) != len(meta):
            rep.bad("%d calls for %d cases" % (len(calls), len(meta)))
        for c, a in zip(calls, meta):
            rep.c["cases"] += 1
            if "stop" in c:
                rep.c["guard_stops"] += 1     # a stop is a mismatch unless the model expects that guard
            ok, got = judge(c, a["want"])
            rep.c["match"] += ok
            if not ok:
                rep.bad("case %d: got %s want %s" % (c["n"], got, a["want"]))
                continue
            if "stop" in c:
                sites["stop at %08X (a guard)" % c["stop"]] += 1
            elif "obs" in c:
                sites["%08X<-%08X" % (c["obs"], c["args"][0])] += 1
                if c["obs"] == B["equip"][0]:
                    hi8["non-zero" if c["args"][2] >> 8 else "zero"] += 1
            else:
                sites["ret %d pop %d" % (s32(c["eax"]), c["pop"])] += 1
            rep.branches.update(a["br"])
            for k, v in a["ctl"].items():
                if form(v) != form(a["want"]):
                    sep[k] += 1
                    passed[k] += judge(c, v)[0]
        E.account(rep, reads, writes, RS)
        for k in sorted(sites):
            rep.notes.append("  outcome %s: %d" % (k, sites[k]))
        if hi8:
            rep.notes.append("  ItemEquip's slot argument, bits 8..31: %s" % dict(sorted(hi8.items())))
        for k in sorted(set(k for a in meta for k in a["ctl"])):
            rep.notes.append("  control %s: sep=%d passed=%d" % (k, sep[k], passed[k]))
            if passed[k]:
                rep.bad("control %s passed %d" % (k, passed[k]))
        rc |= E.finish(rep, sum(sep.values()))
    return rc


PINS = [  # (va, mnemonic, operand substring): the instructions the record cites (ADR-0015 (5))
    (0x0054AD99, "cmp", "DWORD PTR [ebp+0xc],0x9"), (0x0054ADBB, "mov", "BYTE PTR [ebp-0x4],al"),
    (0x0054ADE1, "mov", "edx,DWORD PTR [ebp-0x4]"), (0x0054ADCE, "cmp", "eax,0x9"), (0x0054ADD1, "jbe", ""),
    (0x0054AE56, "mov", "BYTE PTR [ebp+0xc],al"), (0x0054AEC4, "mov", "eax,0x3"), (0x0054AED7, "movzx", "ebx,WORD PTR [eax+0x1]"),
    (0x0054AEFE, "call", "0x535610"), (0x0054AF07, "cmp", "ebx,0x8"), (0x0054AF10, "call", "0x567840"),
    (0x0054AFC2, "cmp", "BYTE PTR [ebp+0xc],0x8"), (0x0054AFDD, "call", "0x63bde0"), (0x0054B084, "cmp", "edi,0x4"),
    (0x0054B089, "cmp", "edi,0x5"), (0x0054B0F9, "cmp", "DWORD PTR [ebp+0xc],0x11"), (0x0054B16B, "call", "0x628250"),
    (0x0054B33E, "cmp", "ebx,esi"), (0x0054B383, "cmp", "DWORD PTR [ebp+0xc],0x5"), (0x0054B3E3, "cmp", "DWORD PTR [ebp+0xc],0x9"),
    (0x0054B47C, "push", "eax"), (0x0054B48E, "call", "0x63c1e0"), (0x0054B4E3, "cmp", "DWORD PTR [ebp+0xc],0x9"),
    (0x0054D526, "cmp", "DWORD PTR [ebp+0xc],0x5"), (0x0054D58E, "call", "0x62bad0"), (0x0054D598, "call", "0x628250"),
    (0x0054D5BF, "call", "0x63c600"), (0x005604CB, "cmp", "DWORD PTR [edi],0x0"), (0x005604DC, "call", "0x628250"),
    (0x005604F9, "cmp", "DWORD PTR [esi+0x10],0x0"), (0x00560527, "and", "DWORD PTR [esi+0xc4],0xfffffffd"),
    (0x00560259, "cmp", "DWORD PTR [esi+0x10],0x4"), (0x005602E5, "jge", ""), (0x005602EE, "jge", ""),
    (0x0063AE53, "cmp", "dl,BYTE PTR [ebx]"), (0x0063AE5A, "cmp", "al,BYTE PTR [ebx+0x1]"), (0x0063ADDA, "jle", ""),
    (0x00567876, "cmp", "eax,0x2"), (0x0063E043, "movsx", "eax,BYTE PTR [eax+0xd]"),
]


def cmd_static():
    rep = Report("static")
    for va, mn, sub in PINS:
        out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % va,
                              "--stop-address=0x%x" % (va + 16), S4.EXE], capture_output=True, text=True).stdout
        line = [ln for ln in out.splitlines() if ln.strip().startswith("%x:" % va)]
        rep.c["pins"] += 1
        txt = line[0].split(":", 1)[1].strip() if line else ""
        if not txt.startswith(mn) or sub not in txt:
            rep.bad("pin 0x%08X: %r, want %s %s" % (va, txt, mn, sub))
        else:
            rep.c["pins_ok"] += 1
            rep.notes.append("  0x%08X %s" % (va, txt))
    for lo, hi, _, name in RS:
        sec = S4.section_of(lo)
        fl = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.notes.append("  %s in %s (writable %s)" % (name, sec, bool(fl & 0x80000000)))
        if fl & 0x80000000 and lo not in DATA_OK:
            rep.bad("%s writable" % name)
    # the .data ranges: every instruction of .text naming an address in them, by a full disassembly
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "-j", ".text", S4.EXE],
                         capture_output=True, text=True).stdout
    names = {"0x74479c": "body row", "0x744544": "class table", "0x744548": "class table rows",
             "0x74457c": "class count"}
    for ln in out.splitlines():
        for k, nm in names.items():
            if k in ln:
                ins = ln.split(":", 1)[1].strip()
                rep.c["data_refs"] += 1
                store = ins.startswith("mov") and ins.split(",")[0].endswith("]") and k in ins.split(",")[0]
                rep.c["data_stores"] += store
                rep.notes.append("  %s: %s%s" % (nm, ln.strip(), "  STORE" if store else ""))
    if rep.c["data_stores"]:
        rep.bad("a store names a .data range read as a constant")
    rep.c["neg"] = 1
    print(rep.line())
    for n in rep.notes:
        print("  " + n)
    return 1 if rep.c["bad"] else 0


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

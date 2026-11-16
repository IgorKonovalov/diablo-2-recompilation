#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S4e part 3 (`lane/n66z`): the item request handlers and UnitInteract's item case, run on the
pinned Game.exe under Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java, compared
with the models below. Parts 1 and 2 (tools/stats_s4e_emu.py, tools/items_s4e_emu.py, run/, run2/) stay unchanged.

    python3 -I tools/items_s4e3_emu.py cases [--dir D] [--limit N]   write D/<family>.cases, .mem, .json
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/items_s4e3_emu.py check [--dir D]               compare, account every traced access, controls
    python3 -I tools/items_s4e3_emu.py static                        objdump pins and the read-only sections
    python3 -I tools/items_s4e3_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66z/s4e/run3. Every draw comes from random.Random("n66z-s4e3-<family>").

A case is a declared scratch image: the memory spec zero-fills the game's unit hash heads, the player, its data, path
and inventory, four items and the other units before every case, and the case writes the non-zero fields. Nothing is
patched. Every callee before a family's boundaries runs emulated: GameFindUnit, PktInvItemBad, PktBeltItemBad,
PktOwnedItemBad, PktIsCursorItem, PktPosFar, PathGetX/Y, INV_GetCursorItem, the owner test 0x0063AD50, PlayerIsBusy,
PlayerGetInteract, InteractIsPlayer, UNIT_GetPlayerData, UnitGetRoom, RoomIsTown (RoomLevelId, LevelIsTown),
ItemSetPage, ItemGetPage, InvMoveInteractTest and TradeItemTest's first tests, UnitInteractDistance and
UnitsLineBlocked's tests before its line test.

Families (function, convention; boundaries; inventory rows):
  pos   PktPosFar 0x00548EF0 called directly: EAX unit, EBX bound, x, y on the stack; to the return.   use 6
  use   the handlers of 0x20 (0x0054B1E0), 0x26 (0x0054B560), 0x27 (0x0054B280): ECX game, EDX player, packet, length;
        to the return or the use function's entry: PlayerUseInvItem 0x0055E170, PlayerUseBeltItem 0x00562390,
        PlayerUseItemOnItem 0x00561ED0.                                                       use 18, 19, 20 (and 6)
  act   the handlers of 0x13 (0x0054AA90) and 0x16 (0x0054AAD0) to UnitInteract's entry 0x00548B00. inventory 1, 28
  pick  UnitInteract 0x00548B00 with EDX 4 (the item case): to the return, InteractWalkTo 0x00548A50, PickupToCursor
        0x0055CF50, PickupToInv 0x00563560, COLL_LineTest 0x0064E260 or UNIT_CollUnmark 0x00649560.  inventory 9, 10, 64
  mv    the handlers of 0x17 (0x0054AB40), 0x18 (0x0054ABB0), 0x19 (0x0054ACD0): to the return, CursorDrop 0x00563C00,
        InvPlaceItem 0x00560200, InvItemToCursor 0x00560420, NoManaMsg 0x00549A60, PlayerClearInteract 0x00554190,
        0x00573140 (an NPC interaction), 0x005B5810 (a player trade).          inventory 29, 30, 31, 40, 41, 43, 45, 99

Controls: each a wrong reading (the spec's where it differs); `sep` counts the cases a control's prediction differs
from the model's, `passed` those where the emulator still equals the control (must be 0 when sep > 0).
Stdlib only, plus objdump for `static`.
"""
import argparse
import collections
import hashlib
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
from anim_s6f_emu import read_out  # noqa: E402
from item_emu3 import exe_table  # noqa: E402
from use_emu import Case  # noqa: E402

M32 = 0xFFFFFFFF
DEFDIR = os.path.join(ROOT, "workspace", "logs", "n66z", "s4e", "run3")
FAMILIES = ("pos", "use", "act", "pick", "mv")
NCASES = {"pos": 1500, "use": 3000, "act": 1200, "pick": 2500, "mv": 4500}
GUARDS = (0x00408090, 0x00408A60, 0x00681E09, 0x0040B4B0, 0x0040B430, 0x0040B480)

F_POS, F_H20, F_H26, F_H27 = 0x00548EF0, 0x0054B1E0, 0x0054B560, 0x0054B280
F_H13, F_H16, F_INTERACT = 0x0054AA90, 0x0054AAD0, 0x00548B00
F_H17, F_H18, F_H19 = 0x0054AB40, 0x0054ABB0, 0x0054ACD0
B_USEINV, B_USEBELT, B_USEON = 0x0055E170, 0x00562390, 0x00561ED0
B_WALK, B_TOCUR, B_TOINV, B_LINE, B_UNMARK = 0x00548A50, 0x0055CF50, 0x00563560, 0x0064E260, 0x00649560
B_DROP, B_PLACE, B_TOCURSOR, B_NOMANA, B_CLEAR, B_NPC, B_TRADE = (0x00563C00, 0x00560200, 0x00560420, 0x00549A60,
                                                               0x00554190, 0x00573140, 0x005B5810)
OBSERVE = {"pos": (), "use": (B_USEINV, B_USEBELT, B_USEON), "act": (F_INTERACT,),
           "pick": (B_WALK, B_TOCUR, B_TOINV, B_LINE, B_UNMARK),
           "mv": (B_DROP, B_PLACE, B_TOCURSOR, B_NOMANA, B_CLEAR, B_NPC, B_TRADE)}
SITE = {B_USEINV: 0x0054B24C, B_USEBELT: 0x0054B62F, B_USEON: 0x0054B2D4, 0x13: 0x0054AAC9, 0x16: 0x0054AB2C,
        B_WALK: 0x00548CDD, B_TOCUR: 0x00548CA2, B_TOINV: 0x00548CB1, B_DROP: 0x0054AB9C, B_PLACE: 0x0054ACA6,
        B_TOCURSOR: 0x0054AD6C, B_NOMANA: 0x0054AD14}

# scratch memory (zero-filled by the spec before each case)
GAME, HASH0 = 0x23000000, 0x23001120          # GameFindUnit's heads: game + 0x6E10E0[type] (types 0..4), + 0x1B20 (5)
HEADS = {0: 0x1120, 1: 0x1320, 2: 0x1520, 3: 0x1920, 4: 0x1720, 5: 0x1B20}
PLAYER, PDATA, PPATH, INVB = 0x23010000, 0x23010400, 0x23010800, 0x23010C00
ITEMS = [0x23020000 + 0x400 * k for k in range(4)]     # item k at ITEMS[k], its data at +0x200, its path at +0x300
OTHERS = [0x23030000 + 0x400 * k for k in range(4)]    # interaction partners: unit at +0, player data at +0x200
ROOM, DROOM, LVL = 0x23040000, 0x23040100, 0x23040200
PKT = 0x23050000
ZERO = [(GAME, 0x2000), (PLAYER, 0x1000), (ITEMS[0], 0x1000), (OTHERS[0], 0x1000), (ROOM, 0x400), (PKT, 0x40)]
SIG = 0x01020304
IID, ITYPE, IFLAG = 0x64, 0x68, 0x6C          # the player's interaction: id, type, flag byte (PlayerGetInteract)
TOWNS_TAB, TOWNS_IDX = 0x006426C0, 0x006426C8


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def le32(v):
    return struct.pack("<I", v & M32)


def level_is_town(lid):
    """0x006426A0: LevelIsTown, its byte index and jump table read from the image (.text)."""
    i = (lid - 1) & M32
    if i > 0x6C:
        return 0
    b = E.img_bytes(TOWNS_IDX + i, 1)[0]
    tgt = struct.unpack("<I", E.img_bytes(TOWNS_TAB + 4 * b, 4))[0]
    return {0x006426B6: 1, 0x006426BC: 0}[tgt]


# ================================================================================================= the world
class W:
    """A declared world: units by address; writes the hash chains GameFindUnit walks."""

    def __init__(self):
        self.c = Case()
        self.u = {}          # addr -> dict(type, guid, mode, data, path, inv, ...)
        self.hashed = []     # (type, guid, addr), in chain order

    def unit(self, addr, typ, guid, hashed=True, **kw):
        d = dict(type=typ, guid=guid & M32, **kw)
        self.u[addr] = d
        c = self.c
        c.d32(addr, typ)
        c.d32(addr + 0xC, guid)
        for k, off in (("cls", 4), ("mode", 0x10), ("data", 0x14), ("path", 0x2C), ("inv", 0x60), ("iid", IID),
                       ("itype", ITYPE)):
            if kw.get(k):
                c.d32(addr + off, kw[k])
        if kw.get("iflag"):
            c.d8(addr + IFLAG, kw["iflag"])
        if hashed:
            self.hashed.append((typ, guid & M32, addr))
        return d

    def finish(self):
        chains = collections.defaultdict(list)
        for typ, guid, addr in self.hashed:
            chains[(typ, 0 if typ == 5 else guid & 0x7F)].append(addr)
        for (typ, b), addrs in chains.items():          # type 5: one list from game + 0x1B20, no bucket
            self.c.d32(GAME + HEADS[typ] + 4 * b, addrs[0])
            for a, nxt in zip(addrs, addrs[1:]):
                self.c.d32(a + 0xE4, nxt)

    def find(self, typ, guid):
        """GameFindUnit 0x00552F60 (typ 0..5 only)."""
        for t, g, a in self.hashed:
            if t == typ and (g & 0x7F) == (guid & 0x7F) and g == guid & M32:
                return a
        return 0

    # ----------------------------------------------------------------------- the readers the code calls
    def cursor(self, invb):
        """INV_GetCursorItem 0x0063C1E0: the signature, then +0x20."""
        if not invb:
            return 0
        x = self.inv.get(invb)
        return x["cursor"] if x and x["sig"] == SIG else 0

    def owned(self, invb, it):
        """0x0063AD50 (inventory, item): the item's data +0x5C is the inventory."""
        if not invb or not it:
            return 0
        u = self.u[it]
        return int(u["type"] == 4 and bool(u.get("data")) and u.get("owner") == invb)

    def pos_of(self, a):
        """PktPosFar's and the 0x26 handler's unit position: types 2, 4, 5 the static path's dwords +0xC, +0x10, else
        PathGetX/Y's u16 at +2, +6 of the dynamic path, 0 with no path."""
        u = self.u[a]
        t = u["type"]
        if t == 2 or 3 < t <= 5:
            return u["sx"], u["sy"]
        if not u.get("path"):
            return 0, 0
        return u["px"], u["py"]

    def interact(self, p):
        u = self.u[p]
        return u.get("iflag", 0), u.get("iid", 0), u.get("itype", 0)


def posfar(ux, uy, bound, x, y, ctl=None):
    """PktPosFar 0x00548EF0 after the position reads: |ux - u16(x)| > bound or |uy - u16(y)| > bound, 32-bit neg,
    signed compares."""
    def far(a, b):
        b = b if ctl == "pos_full" else b & 0xFFFF
        d = s32(a - b)
        if d < 0:
            d = s32(-d)
        if ctl == "pos_unsigned":
            return (d & M32) > (bound & M32)
        if ctl == "pos_ge":
            return d >= s32(bound)
        return d > s32(bound)
    return 1 if far(ux, x) or far(uy, y) else 0


def put_player(w, r, typ=0, **kw):
    """The player: dynamic path (x, y u16 at +2, +6, room at +0x1C, collision mask at +0x4C), inventory, data."""
    px, py = r.randrange(0, 0x10000), r.randrange(0, 0x10000)
    if typ in (2, 4, 5):
        sx, sy = r.choice([px, px | (r.randrange(1, 0x8000) << 16), r.getrandbits(32)]), r.getrandbits(32) if \
            r.random() < 0.3 else py
        w.c.d32(PPATH + 0xC, sx)
        w.c.d32(PPATH + 0x10, sy)
        kw.update(sx=sx, sy=sy)
    else:
        w.c.put(PPATH + 2, struct.pack("<H", px))
        w.c.put(PPATH + 6, struct.pack("<H", py))
    w.unit(PLAYER, typ, kw.pop("guid", r.randrange(1, 0x200)), hashed=False, data=PDATA, path=PPATH, inv=INVB,
           px=px, py=py, **kw)
    return px, py


def put_inv(w, cursor=0, sig=SIG):
    w.inv = {INVB: dict(sig=sig, cursor=cursor)}
    w.c.d32(INVB, sig)
    if cursor:
        w.c.d32(INVB + 0x20, cursor)


def put_item(w, k, guid, mode, owner, data=True, page=0, x=0, y=0):
    a = ITEMS[k]
    d = a + 0x200 if data else 0
    w.unit(a, 4, guid, mode=mode, data=d, path=a + 0x300, owner=owner if data else None, page=page, sx=x, sy=y)
    if d:
        if owner:
            w.c.d32(d + 0x5C, owner)
        w.c.d8(d + 0x45, page)
    w.c.d32(a + 0x300 + 0xC, x)
    w.c.d32(a + 0x300 + 0x10, y)
    return a


def guids(r, n):
    """n distinct guids, some sharing a hash bucket (guid & 0x7F) so chains are walked."""
    out = []
    base = r.randrange(0, 0x7F)
    while len(out) < n:
        g = r.choice([r.randrange(1, 0x10000), base + 0x80 * r.randrange(0, 40), r.getrandbits(32)])
        if g not in out:
            out.append(g)
    return out


def pkt(w, length, fields):
    """The packet bytes: opcode at +0, then the u32 fields at +1, +5, ..."""
    b = bytearray(0x40)
    for off, v in fields.items():
        struct.pack_into("<I", b, off, v & M32)
    w.c.put(PKT, bytes(b))
    return length


def items_world(w, r, n_items=3, modes=(0, 0, 1, 2, 3, 4), fav=None):
    """Item 0 is the favoured one when `fav` (a mode) is given: owned, with data, in that mode."""
    gs = guids(r, n_items + 1)
    its = []
    for k in range(n_items):
        owner = r.choice([INVB, INVB, INVB, 0, 0x23011000])
        mode, data = r.choice(modes), r.random() > 0.05
        if k == 0 and fav is not None and r.random() < 0.85:
            mode, owner, data = fav, INVB, True
        its.append((put_item(w, k, gs[k], mode, owner, data=data, page=r.choice([0, 0, 0, 1, 2, 3, 4, 0xFF])), gs[k]))
    return its, gs[n_items]          # the last guid names no unit


def pick_guid(r, its, missing):
    if r.random() < 0.6:
        return its[0][1]
    return r.choice([g for _, g in its] + [missing])


# ================================================================================================= pos
def gen_pos(r):
    w = W()
    typ = r.choice([0, 0, 1, 3, 2, 4, 5, 6, 7])
    nopath = typ not in (2, 4, 5) and r.random() < 0.08
    a = PLAYER
    px, py = r.randrange(0, 0x10000), r.randrange(0, 0x10000)
    kw = dict(path=0 if nopath else PPATH, px=px, py=py)
    if typ in (2, 4, 5):
        sx = r.choice([px, px | (r.randrange(1, 0x8000) << 16), 0x80000000 | px, r.getrandbits(32)])
        sy = r.choice([py, py | (r.randrange(1, 0x8000) << 16), r.getrandbits(32)])
        w.c.d32(PPATH + 0xC, sx)
        w.c.d32(PPATH + 0x10, sy)
        kw.update(sx=sx, sy=sy)
    else:
        w.c.put(PPATH + 2, struct.pack("<H", px))
        w.c.put(PPATH + 6, struct.pack("<H", py))
    w.unit(a, typ, 1, hashed=False, **kw)
    ux, uy = w.pos_of(a)
    bound = r.choice([50, 50, 50, 0, 1, 49, 51, 200, 0x7FFFFFFF, -1 & M32])

    def near(v):
        return r.choice([(v + r.randrange(-60, 61)) & 0xFFFF, (v + bound) & 0xFFFF, (v - bound) & 0xFFFF,
                         (v + bound + 1) & 0xFFFF, (v - bound - 1) & 0xFFFF, r.getrandbits(16)])
    x = near(ux) | (r.choice([0, 0, r.getrandbits(16)]) << 16)
    y = near(uy) | (r.choice([0, 0, r.getrandbits(16)]) << 16)
    want = ["ret", posfar(ux, uy, bound, x, y), 8]
    ctl = {k: ["ret", posfar(ux, uy, bound, x, y, k), 8] for k in ("pos_unsigned", "pos_ge", "pos_full")}
    lines = ["r eax %08x" % a, "r ebx %08x" % bound, w.c.call(F_POS, 0, 0, x, y)]
    br = {"pos_t%d" % typ: 1, "pos_ret%d" % want[1]: 1, "pos_nopath": int(nopath),
          "pos_wrap": int(typ in (2, 4, 5) and (s32(ux - (x & 0xFFFF)) == -0x80000000 or s32(uy - (y & 0xFFFF)) == -0x80000000))}
    return lines, {"fn": F_POS, "want": want, "ctl": ctl, "br": br}


# ================================================================================================= use
def inv_item_bad(w, guid):
    """PktInvItemBad 0x00549150: the item, mode 0, owned."""
    it = w.find(4, guid)
    if not it or w.u[it]["mode"] != 0:
        return 1
    return 0 if w.owned(INVB, it) else 1


def belt_item_bad(w, guid):
    """PktBeltItemBad 0x005492F0: the item, mode 2, owned."""
    it = w.find(4, guid)
    if not it or w.u[it]["mode"] != 2:
        return 1
    return 0 if w.owned(INVB, it) else 1


def owned_item_bad(w, guid, ctl=None):
    """PktOwnedItemBad 0x00549220: the item; owned, or else the cursor item."""
    it = w.find(4, guid)
    if not it:
        return 1
    if w.owned(INVB, it):
        return 0
    if ctl == "owned_only":
        return 1
    return int(w.cursor(INVB) != it)


def model_use(w, op, length, f, ctl=None):
    if op == 0x20:
        if length != 13:
            return ["ret", 3, 8]
        b = inv_item_bad(w, f[1]) if ctl != "inv_nomode" else (0 if w.find(4, f[1]) and w.owned(INVB, w.find(4, f[1])) else 1)
        if b:
            return ["ret", b, 8]
        ux, uy = w.pos_of(PLAYER)
        if posfar(ux, uy, 50, f[5], f[9]):
            return ["ret", 1, 8]
        return ["obs", B_USEINV, SITE[B_USEINV], {"ecx": GAME, "edx": PLAYER}, [f[1], f[5], f[9]]]
    if op == 0x26:
        if length != 13:
            return ["ret", 3, 8]
        if belt_item_bad(w, f[1]):
            return ["ret", 1, 8]
        ux, uy = w.pos_of(PLAYER)
        if ctl != "spec_anypos" and posfar(ux, uy, 50, ux, uy):
            return ["ret", 1, 8]
        return ["obs", B_USEBELT, SITE[B_USEBELT], {"ecx": GAME, "edx": PLAYER}, [f[1], ux & M32, uy & M32, None, f[5]]]
    if length != 9:
        return ["ret", 3, 8]
    for g in (f[1], f[5]):
        if owned_item_bad(w, g, ctl):
            return ["ret", 1, 8]
    return ["obs", B_USEON, SITE[B_USEON], {"ecx": GAME, "edx": PLAYER}, [f[1], f[5]]]


def gen_use(r):
    w = W()
    op = r.choice([0x20, 0x26, 0x27])
    ptyp = 0 if op != 0x26 or r.random() < 0.7 else r.choice([1, 2, 4, 5])
    px, py = put_player(w, r, ptyp)
    its, missing = items_world(w, r, 3, modes=(0, 0, 2, 2, 4, 1, 3), fav={0x20: 0, 0x26: 2, 0x27: r.choice([0, 1, 2, 4])}[op])
    cur = r.choice([0, 0, 0, 0] + [a for a, _ in its])
    if op == 0x27 and r.random() < 0.3:      # the cursor item, owned or not, against PktOwnedItemBad's second test
        cur = r.choice(its[1:])[0]
    put_inv(w, cursor=cur, sig=SIG if r.random() > 0.05 else 0x01020305)
    w.finish()
    good = {0x20: 13, 0x26: 13, 0x27: 9}[op]
    length = good if r.random() < 0.9 else r.choice([0, 3, 5, 9, 13, 17, 12, 14])
    ux, uy = w.pos_of(PLAYER)
    f = {1: pick_guid(r, its, missing), 5: pick_guid(r, its, missing) if op == 0x27 else
         (((ux + r.choice([0, 0, 0, 3, -7, 50, -50, 51, -51, r.randrange(-80, 81)])) & 0xFFFF) | (r.choice([0, 0, 0, 1]) << 16)),
         9: ((uy + r.choice([0, 0, 0, 5, -2, 50, -50, 51, -51, r.randrange(-80, 81)])) & 0xFFFF) | (r.choice([0, 0, 0, 1]) << 16)}
    if op == 0x26:
        f[5] = r.getrandbits(32)
    pkt(w, length, f)
    want = model_use(w, op, length, f)
    ctl = {k: model_use(w, op, length, f, k) for k in ("inv_nomode", "spec_anypos", "owned_only")}
    fn = {0x20: F_H20, 0x26: F_H26, 0x27: F_H27}[op]
    br = {"use%02X_%s" % (op, want[0] if want[0] == "ret" and want[1] != 1 else
                          ("obs" if want[0] == "obs" else "refused")): 1, "use_ptype%d" % ptyp: 1}
    if want[0] == "ret" and want[1] == 3:
        br = {"use%02X_len" % op: 1}
    return [w.c.call(fn, GAME, PLAYER, PKT, length)], {"fn": fn, "op": op, "want": want, "ctl": ctl, "br": br}


# ================================================================================================= act
def model_act(op, length, f, pguid, ctl=None):
    if length != (9 if op == 0x13 else 13):
        return ["ret", 3, 8]
    typ = f[1]
    if (typ > 6 if ctl == "type_le6" else typ >= 6):
        return ["ret", 2, 8]
    if op == 0x13:
        return ["obs", F_INTERACT, SITE[0x13], {"ecx": PLAYER, "edx": typ}, [f[5], 0, GAME]]
    if ctl != "noself" and pguid == f[5] and typ == 0:
        return ["ret", 3, 8]
    return ["obs", F_INTERACT, SITE[0x16], {"ecx": PLAYER if pguid != -1 else 0, "edx": typ}, [f[5], f[9], GAME]]


def gen_act(r):
    w = W()
    op = r.choice([0x13, 0x16])
    nop = op == 0x16 and r.random() < 0.05
    pg = r.choice([r.randrange(1, 0x10000), r.getrandbits(32)])
    if not nop:
        w.unit(PLAYER, 0, pg, hashed=False)
    length = (9 if op == 0x13 else 13) if r.random() < 0.9 else r.choice([0, 5, 9, 13, 17])
    typ = r.choice([0, 0, 1, 2, 3, 4, 5, 6, 7, r.getrandbits(32)])
    g = r.choice([pg, pg, r.getrandbits(32), r.randrange(0, 100)]) if op == 0x16 else r.getrandbits(32)
    f = {1: typ, 5: g, 9: r.choice([0, 0, 1, 2, r.getrandbits(32)])}
    pkt(w, length, f)
    pguid = -1 if nop else pg
    want = model_act(op, length, f, pguid)
    ctl = {k: model_act(op, length, f, pguid, k) for k in ("type_le6", "noself")}
    fn = F_H13 if op == 0x13 else F_H16
    br = {"act%02X_%s" % (op, "obs" if want[0] == "obs" else "ret%d" % want[1]): 1}
    return [w.c.call(fn, GAME, 0 if nop else PLAYER, PKT, length)], {"fn": fn, "want": want, "ctl": ctl, "br": br}


# ================================================================================================= pick
TB = None


def model_pick(w, guid, action, pm, ctl=None):
    it = w.find(4, guid)
    if not it or w.u[it]["mode"] != 3:
        return ["ret", 1, 12]
    ax, ay = w.pos_of(PLAYER)
    bx, by = w.u[it]["sx"], w.u[it]["sy"]
    d = inv.interact_distance(TB, ax, ay, 2, bx, by, 1)
    if (d >= 50 if ctl == "reach50" else d > 50):
        return ["ret", 1, 12]
    if (d > 5 if ctl == "reach6" else d > 4):
        return ["obs", B_WALK, SITE[B_WALK], {"ecx": GAME, "edi": 4}, [(-2 if action else -1) & M32]]
    mask = 0x801 if ctl == "mask801" else 0x804
    if pm & mask:
        return ["obs", B_UNMARK, None, {}, []]
    ends = inv.line_ends(ax, ay, 2, bx, by, 1)
    if ends is not None:
        return ["obs", B_LINE, None, {}, ["line", ROOM, 0x804, ends]]
    tocur = bool(action) != (ctl == "actswap")
    b = B_TOCUR if tocur else B_TOINV
    return ["obs", b, SITE[b], {"ecx": GAME, "edx": PLAYER}, [guid]]


def gen_pick(r):
    global TB
    if TB is None:
        TB = exe_table()[0]
    w = W()
    pm = r.choice([0, 0x80, 0x100, 0x80, 0x1C00, 0x804, 0x4, 0x1])
    put_player(w, r, 0)
    w.c.d32(PPATH + 0x1C, ROOM)
    w.c.d32(PPATH + 0x4C, pm)
    ax, ay = w.pos_of(PLAYER)
    gs = guids(r, 4)
    its = []
    for k in range(3):
        span = r.choice([1, 2, 3, 4, 6, 8, 30, 60, 0])
        if span:
            x, y = ax + r.randrange(-span, span + 1), ay + r.randrange(-span, span + 1)
        else:                 # around the two bounds: d of 4, 5, 6 and 49, 50, 51, 52
            dx, dy = r.choice([(3, 0), (4, 0), (2, 1), (3, 1), (2, 2), (4, 1), (25, 0), (26, 0), (27, 0), (24, 2), (25, 1),
                               (26, 1), (17, 17), (18, 17)])
            if r.random() < 0.5:
                dx, dy = dy, dx
            x, y = ax + dx * r.choice([1, -1]), ay + dy * r.choice([1, -1])
        its.append((put_item(w, k, gs[k], r.choice([3, 3, 3, 3, 0, 4]), 0, x=x, y=y), gs[k]))
    w.finish()
    guid = pick_guid(r, its, gs[3])
    action = r.choice([0, 0, 1, 2, r.getrandbits(32)])
    want = model_pick(w, guid, action, pm)
    ctl = {k: model_pick(w, guid, action, pm, k) for k in ("reach50", "reach6", "mask801", "actswap")}
    br = {"pick_%s" % (("ret%d" % want[1]) if want[0] == "ret" else "%08X" % want[1]): 1}
    return [w.c.call(F_INTERACT, PLAYER, 4, guid, action, GAME)], {"fn": F_INTERACT, "want": want, "ctl": ctl, "br": br}


# ================================================================================================= mv
def cursor_bad(w, guid):
    """PktIsCursorItem 0x005490E0: the item, mode 4, the player's cursor item."""
    it = w.find(4, guid)
    if not it or w.u[it]["mode"] != 4 or w.cursor(INVB) != it:
        return 1
    return 0


def pdata(w, p):
    return w.pd[p]


def is_busy(w):
    """PlayerIsBusy 0x00535060."""
    u = w.u[PLAYER]
    if u["type"] != 0:
        return 0
    if w.interact(PLAYER)[0]:
        return 1
    if w.cursor(INVB):
        return 1
    return pdata(w, PLAYER).get(0x4C, 0)


def interact_is_player(w):
    """InteractIsPlayer 0x005678A0 (its stack argument is not read): the flag, type 0, the unit found."""
    fl, iid, ity = w.interact(PLAYER)
    return int(bool(fl) and ity == 0 and bool(w.find(0, iid)))


def trade_test(w):
    """TradeItemTest 0x00567620 as far as these cases go: -> value, or an observed boundary."""
    fl, iid, ity = w.interact(PLAYER)
    pd = pdata(w, PLAYER)
    if fl:
        if ity != 0:
            return 1
        u = w.find(0, iid)
        if u:
            if not w.pd[u].get(0x5C, 0):
                return 0
            return ("obs", B_TRADE)
    return int(s32(pd.get(0x50, 0)) <= 4)


def move_test(w):
    """InvMoveInteractTest 0x00535610."""
    fl, iid, ity = w.interact(PLAYER)
    if fl:
        u = w.find(ity, iid)
        if not u:
            return ("obs", B_CLEAR)
        if ity == 1:
            return ("obs", B_NPC)
        return trade_test(w)
    if pdata(w, PLAYER).get(0x4C, 0):
        return 0
    return trade_test(w)


def model_mv(w, op, length, f, ctl=None):
    if op == 0x17:
        if length != 5:
            return ["ret", 3, 8]
        c = cursor_bad(w, f[1])
        if c:
            return ["ret", c, 8]
        if (is_busy(w) or ctl == "iip_always") and interact_is_player(w):
            return ["ret", 3, 8]
        return ["obs", B_DROP, SITE[B_DROP], {"ecx": GAME, "edx": PLAYER}, [f[1]]]
    if op == 0x18:
        if length != 17:
            return ["ret", 3, 8]
        c = cursor_bad(w, f[1])
        if c:
            return ["ret", c, 8]
        page = f[13]
        if w.u[PLAYER]["type"] == 0:
            if not is_busy(w) and page != 0:
                return ["ret", 2, 8]
            if page == 4:
                room = w.room
                if not room or not level_is_town(w.lid):
                    return ["ret", 3, 8]
            elif page == 2:
                if not interact_is_player(w):
                    return ["ret", 3, 8]
            elif page not in (0, 3) and not (ctl == "page1_ok" and page == 1):
                return ["ret", 2, 8]
        elif page >= 5:
            return ["ret", 2, 8]
        it = w.find(4, f[1])
        pb = (page & 0xFF) if ctl != "page_after" else w.u[it]["page"]
        if not w.u[it].get("data"):
            pb = 0                    # ItemSetPage writes nothing on an item with no data; the zero-filled byte stays
        return ["obs", B_PLACE, SITE[B_PLACE], {"ecx": 0x006E1050, "edx": 0xBF6},
                [GAME, PLAYER, f[1], f[5], f[9], 0, 1, 0], {"page": [it + 0x200 + 0x45, pb]}]
    if length != 5:
        return ["ret", 3, 8]
    b = inv_item_bad(w, f[1])
    if b:
        return ["ret", b, 8]
    if w.cursor(INVB):
        return ["obs", B_NOMANA, SITE[B_NOMANA], {"ecx": PLAYER}, []]
    it = w.find(4, f[1])
    if w.u[it]["page"] == 1 and ctl != "page1_ok":
        return ["ret", 3, 8]
    t = move_test(w) if ctl != "trade_ignored" else 1
    if isinstance(t, tuple):
        return ["obs", t[1], None, {}, []]
    if not t:
        return ["ret", 0, 8]
    return ["obs", B_TOCURSOR, SITE[B_TOCURSOR], {"ecx": GAME, "edx": PLAYER}, [f[1], None, 1, 0, 0, 0]]


def gen_mv(r):
    w = W()
    op = r.choice([0x17, 0x18, 0x18, 0x19, 0x19])
    ptyp = 0 if op == 0x19 or r.random() < 0.8 else r.choice([1, 3])
    w.pd = collections.defaultdict(dict)
    iflag = r.choice([0, 0, 0, 1, 1, 0x80])
    # the interaction partner: an id of a unit of the type, or of none
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
    put_player(w, r, ptyp, iflag=iflag, iid=iid, itype=ity)
    for off, choices in ((0x4C, [0, 0, 0, 1, r.getrandbits(32)]), (0x50, [0, 0, 4, 5, 1, -1 & M32, 0x80000000])):
        v = r.choice(choices)
        w.pd[PLAYER][off] = v
        w.c.d32(PDATA + off, v)
    w.pd[PLAYER].setdefault(0x4C, 0)
    its, missing = items_world(w, r, 3, modes=(0, 0, 4, 4, 1, 2) if op == 0x19 else (4, 4, 4, 0, 2),
                               fav=0 if op == 0x19 else 4)
    if op == 0x19:
        cur = r.choice([0, 0, 0, 0, 0] + [a for a, _ in its])
    else:
        cur = its[0][0] if r.random() < 0.8 else r.choice([a for a, _ in its] + [0])
    put_inv(w, cursor=cur)
    # the room for page 4: path +0x1C -> room +0x10 -> +0x58 -> +0x1D0 the level id
    w.room = ROOM if r.random() > 0.1 else 0
    w.lid = r.choice([1, 40, 75, 103, 109, 2, 8, 39, 41, 100, 110, 132, 0, 200])
    if w.room:
        w.c.d32(PPATH + 0x1C, ROOM)
        w.c.d32(ROOM + 0x10, DROOM)
        w.c.d32(DROOM + 0x58, LVL)
        w.c.d32(LVL + 0x1D0, w.lid)
    w.finish()
    good = {0x17: 5, 0x18: 17, 0x19: 5}[op]
    length = good if r.random() < 0.92 else r.choice([0, 1, 5, 9, 13, 17, 21])
    f = {1: pick_guid(r, its, missing) if r.random() < 0.85 or not cur else w.u[cur]["guid"]}
    if op == 0x18:
        f[5], f[9] = r.randrange(0, 12), r.randrange(0, 12)
        f[13] = r.choice([0, 0, 1, 2, 2, 3, 3, 4, 4, 4, 5, 6, 0xFF, 0x104, r.getrandbits(32)])
    pkt(w, length, f)
    want = model_mv(w, op, length, f)
    ctl = {k: model_mv(w, op, length, f, k) for k in ("iip_always", "page_after", "page1_ok", "trade_ignored")}
    fn = {0x17: F_H17, 0x18: F_H18, 0x19: F_H19}[op]
    tag = ("ret%d" % want[1]) if want[0] == "ret" else "%08X" % want[1]
    br = {"mv%02X_%s" % (op, tag): 1}
    if op == 0x18 and want[0] == "obs":
        br["mv18_page%X" % f[13]] = 1
    if op == 0x18 and want == ["ret", 3, 8] and length == 17:
        br["mv18_ret3_page%X" % f[13]] = 1
    if want[0] == "obs":
        dumps = want[5] if len(want) > 5 else {}
        for k, (addr, _) in dumps.items():
            w.c.dump(addr, 1)
    return [w.c.call(fn, GAME, PLAYER, PKT, length)], {"fn": fn, "op": op, "want": want, "ctl": ctl, "br": br}


GEN = {"pos": gen_pos, "use": gen_use, "act": gen_act, "pick": gen_pick, "mv": gen_mv}


# ================================================================================================= commands
def mem_spec(fam):
    out = ["# plan 0066 S4e part 3: zero-filled scratch regions, re-applied before every case"]
    for lo, n in ZERO:
        out.append("bytes %08x %s" % (lo, "00" * n))
    out += ["guard %08x" % g for g in GUARDS]
    out += ["observe %08x" % b for b in OBSERVE[fam]]
    return out


def cmd_cases(d, limit=None):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        rnd = random.Random("n66z-s4e3-%s" % fam)
        cases, meta = [], []
        n = limit or NCASES[fam]
        for _ in range(n):
            lines, a = GEN[fam](rnd)
            cases.extend(lines)
            meta.append(a)
        E.write_family(d, fam, cases, mem_spec(fam), {"cases": meta})
        print("%s: %d cases" % (fam, n))


# image reads (instruction fetches are not traced): each a constant of a read-only section (`static` checks the flags)
RS = [(0x006E10E0, 0x006E10F4, "r", "GameFindUnit's head offsets 0x006E10E0 (.rdata)"),
      (0x006EB180, 0x006EB280, "r", "UnitInteractDistance's table 0x006EB180 (.rdata)"),
      (0x00548E8C, 0x00548EA4, "r", "UnitInteract's switch table 0x00548E8C (.text)"),
      (0x006426C0, 0x00642735, "r", "LevelIsTown's tables 0x006426C0, 0x006426C8 (.text)"),
      (0x00620570, 0x00620590, "r", "UNIT_GetSizeX's switch table (.text)"),
      (0x00620630, 0x00620650, "r", "UNIT_GetSizeY's switch table (.text)")]


def judge(fam, c, a, ctl=None):
    want = a["want"] if ctl is None else a["ctl"][ctl]
    if "stop" in c:
        return False, ["stop", "%08X" % c["stop"], c.get("msg")]
    if want[0] == "ret":
        got = ["ret", c.get("eax"), c.get("pop")] if "obs" not in c else ["obs", "%08X" % c["obs"]]
        return got == want, got
    if "obs" not in c:
        return False, ["ret", c.get("eax"), c.get("pop")]
    args = list(c.get("args", (0,) * 16))
    got = ["obs", c["obs"], args[0], {k: c["regs"].get(k) for k in want[3]}, args[1:1 + len(want[4])]]
    if c["obs"] != want[1]:
        return False, got
    if want[2] is not None and args[0] != want[2]:
        return False, got
    if any(c["regs"].get(k) != v for k, v in want[3].items()):
        return False, got
    exp = want[4]
    if exp and exp[0] == "line":
        _, room, mask, ends = exp
        esp = c["regs"]["esp"]
        raw = struct.pack("<16I", *args)

        def at(p):
            o = p - esp
            return list(struct.unpack_from("<II", raw, o)) if 0 <= o <= len(raw) - 8 else None
        ok = args[1] == room and args[4] == mask and [at(args[2]), at(args[3])] == [list(e) for e in ends]
        return ok, got + [[hex(x) for x in args[:5]]]
    for i, v in enumerate(exp):
        if v is not None and args[1 + i] != v & M32:
            return False, got
    if len(want) > 5:
        for k, (addr, v) in want[5].items():
            if c["dumps"].get(addr, b"\xff\xff")[:1] != bytes([v]):
                return False, got + [k, c["dumps"].get(addr, b"").hex()]
    return True, got


class Report(E.Report):
    def line(self):
        keys = ["cases", "match", "bad", "neg", "traced", "undeclared", "stopped"]
        rest = sorted(k for k in self.c if k not in keys)
        return "S4E3 %s " % self.fam + " ".join("%s=%d" % (k, self.c[k]) for k in keys + rest)


def obsform(x):
    return json.dumps(x[:5] if x[0] == "obs" else x, sort_keys=True) + (json.dumps(x[5]) if len(x) > 5 else "")


def cmd_check(d, fams=FAMILIES):
    rc = 0
    for fam in fams:
        p = os.path.join(d, fam + ".out")
        if not os.path.exists(p):
            print("S4E3 %s: no output" % fam)
            rc = 1
            continue
        calls, reads, writes = read_out(p)
        meta = json.load(open(os.path.join(d, fam + ".json")))["cases"]
        rep = Report(fam)
        sep, passed, sites = collections.Counter(), collections.Counter(), collections.Counter()
        if len(calls) != len(meta):
            rep.bad("%d calls for %d cases" % (len(calls), len(meta)))
        for c, a in zip(calls, meta):
            rep.c["cases"] += 1
            if "stop" in c:
                rep.c["stopped"] += 1
                rep.bad("case %d stopped at %08X: %s" % (c["n"], c["stop"], c.get("msg")))
                continue
            ok, got = judge(fam, c, a)
            rep.c["match"] += ok
            if not ok:
                rep.bad("case %d: got %s want %s" % (c["n"], got, a["want"]))
                continue
            if "obs" in c:
                sites["%08X<-%08X" % (c["obs"], c["args"][0])] += 1
            else:
                sites["ret %d pop %d" % (c["eax"], c["pop"])] += 1
            rep.branches.update(a["br"])
            for k, v in a["ctl"].items():
                if obsform(v) != obsform(a["want"]):
                    sep[k] += 1
                    passed[k] += judge(fam, c, a, k)[0]
        E.account(rep, reads, writes, RS)
        for k in sorted(sites):
            rep.notes.append("  outcome %s: %d" % (k, sites[k]))
        for k in sorted(set(k for a in meta for k in a["ctl"])):
            rep.notes.append("  control %s: sep=%d passed=%d" % (k, sep[k], passed[k]))
            if passed[k]:
                rep.bad("control %s passed %d" % (k, passed[k]))
        rc |= E.finish(rep, sum(sep.values()))
    return rc


PINS = [  # (va, mnemonic, operand substring): the instructions the record cites (ADR-0015 (5))
    (0x0054B222, "lea", "ebx,[eax+0x32]"), (0x0054B602, "lea", "ebx,[eax+0x32]"), (0x00548F4D, "movzx", "WORD PTR [ebp+0x8]"),
    (0x00548F57, "jns", ""), (0x00548F59, "neg", "ecx"), (0x00548F5B, "cmp", "ecx,ebx"), (0x00548F5D, "jg", ""),
    (0x00548F5F, "movzx", "WORD PTR [ebp+0xc]"), (0x00548F6B, "jg", ""),
    (0x0054AAAC, "cmp", "edx,0x6"), (0x0054AAB2, "jb", ""), (0x0054AB10, "cmp", "ebx,esi"), (0x0054AB15, "test", "edx,edx"),
    (0x00548C60, "cmp", "eax,0x3"), (0x00548C70, "cmp", "eax,0x32"), (0x00548C73, "jg", ""), (0x00548C79, "cmp", "eax,0x4"),
    (0x00548C7E, "push", "0x804"), (0x00548C8E, "cmp", "DWORD PTR [ebp+0xc],eax"),
    (0x0054AB7D, "call", "0x5678a0"), (0x0054AC4E, "call", "0x5678a0"), (0x0054AC4A, "push", "0x1"), (0x005678A0, "push", "ebp"), (0x005678E4, "ret", "0x4"),
    (0x0054AC68, "jae", ""), (0x0054AC7E, "call", "0x628280"), (0x0054ACA1, "call", "0x560200"),
    (0x0054AD35, "call", "0x628250"), (0x0054AD3A, "cmp", "al,0x1"), (0x0054AD46, "call", "0x535610"),
    (0x0053568D, "jne", "0x535646"), (0x00567834, "setle", "al"),
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
        rep.c["ro"] += not fl & 0x80000000
        rep.notes.append("  %s in %s (writable %s)" % (name, sec, bool(fl & 0x80000000)))
        if fl & 0x80000000:
            rep.bad("%s writable" % name)
    towns = [lid for lid in range(0, 0x70) if level_is_town(lid)]
    rep.notes.append("  LevelIsTown true for level ids %s" % towns)
    # InteractIsPlayer does not read its stack argument: no [ebp+0x8] in 0x005678A0..0x005678E7
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x5678a0",
                          "--stop-address=0x5678e7", S4.EXE], capture_output=True, text=True).stdout
    rep.c["iip_arg_reads"] = out.count("[ebp+0x8]")
    rep.notes.append("  InteractIsPlayer 0x005678A0..0x005678E6: %d reads of [ebp+0x8]" % rep.c["iip_arg_reads"])
    if rep.c["iip_arg_reads"]:
        rep.bad("InteractIsPlayer reads its argument")
    rep.c["neg"] = 1
    print(rep.line())
    for n in rep.notes:
        print("  " + n)
    return 1 if rep.c["bad"] else 0


def cmd_manifest(d, write):
    lines = []
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if os.path.isfile(p) and not name.startswith("manifest"):
            lines.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), name))
    txt = "\n".join(lines) + "\n"
    if write:
        open(os.path.join(d, "manifest.sha256"), "w").write(txt)
    sys.stdout.write(txt)
    return 0


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
    return cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

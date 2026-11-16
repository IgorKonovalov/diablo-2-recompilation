#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S4e part 2 (`lane/n66z`): the price core and the gold, wear and replenish helpers, run on
the pinned Game.exe under Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java,
compared with the models below. Part 1 (tools/stats_s4e_emu.py and its kept run/) stays unchanged.

    python3 -I tools/items_s4e_emu.py cases [--dir D] [--limit N]   write D/<family>.cases, .mem, .json and the tables
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/items_s4e_emu.py check [--dir D]               compare, account every traced access, controls
    python3 -I tools/items_s4e_emu.py static                        objdump pins the record cites
    python3 -I tools/items_s4e_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66z/s4e/run2. Every draw comes from random.Random("n66z-s4e2-<family>"); the declared
tables from random.Random("n66z-s4e2-image").

The model of `price` follows tools/economy.py's Model.price (the reviewed model of run:2026-10-17-economy) step for
step, rewritten here over the declared scratch tables: the ItemTypes equivalence bits are read from the declared bit
rows (DataTables +0xC04, stride +0xC00) instead of a closure of Equiv1/2, the NPC row is the first with the class
(NpcGetByClass's linear search), the quest bit is QUESTRECORD_GetState's BITFIELD_Get, the normcode lookup is
EXCEL_FindCode's binary search over the declared link, and Encode 4 (STAT_ByTimeValue) is modelled.

Families (function, convention; inventory rows of items/economy):
  price  ITEMS_TradePriceCore 0x0062EFB0 (ECX player, EDX item; d, questRecord, npcClass, mode), every callee whole:
         STATS_GetUnitStat/BaseStat, ItemCanRepair, ItemHasCharges, ItemHasDurability, ItemMaxDurability,
         RepairableStack, the ItemData getters, ITEMS_UnitIsType, ITEMS_GetRecord/GetType/GetBaseType,
         ITEMTYPES_GetRecord, MAGICAFFIX/UNIQUEITEMS/SETITEMS/MONSTATS/BOOKS getters, ItemNormCode, ItemIndexByCode,
         ITEMS_GetByCode, EXCEL_FindCode, GamblePrice, StaffModTerm, PriceStatTerms (StatListCopyFull,
         UnitStatDelta, STAT_ByTimeValue), PriceSocketTerm (INV_GetFirstItem, InvNodeItem, INV_GetNextItem),
         NpcGetByClass, QUESTRECORD_GetState, BITFIELD_Get, RechargeCost, MulDiv (__alldiv).
         Observed boundary (ADR-0021): the error routine 0x00408090 (a missing Books row, no NPC row): the case ends
         there with the error code at [ESP+4]. Guards: 0x00408A60, 0x00681E09 and the pool allocator's entries.
                                    rows 4, 5, 12-20, 22, 23, 25, 26, 28-34, 46 (and 27, 35, 36, 43 as callees)
  rep    sub_0062E660_ItemCanRepair (item; stdcall), sub_00629930_ItemHasDurability (item; stdcall) and
         sub_00628D30_RechargeCost (ECX item, EDX 10000) called directly.                rows 27, 35, 36, 43
  gold   PLAYER_GoldCap 0x00622E70 (unit; stdcall), PLAYER_StashGoldCap 0x00623460 (unit; stdcall) whole, and
         sub_0053FF00_UnitAddGoldStat (ECX unit, EDX stat; delta) to its write: observed boundaries
         sub_00627260_UnitSetStat and 0x006272B0 (the add).                             rows 7, 47, 48, 85
  wear   ITEMS_DurabilityLossRoll 0x00559E30 (ECX game, EDX seed owner; item) to its first write or callee after the
         roll: observed boundaries UnitSetStat 0x00627260, ItemBreak 0x0055F850, ItemReplenishDurTimer 0x00558530,
         0x005531C0; the unit seed (+0x20/+0x24) dumped.                                  row 69
  timer  sub_00558530_ItemReplenishDurTimer (ECX game, EDX item) to the queue call: observed boundaries
         0x005415A0 (the queued-event test) and 0x005417D0 (the queue).                   rows 11, 79 (the timer)

Controls: each named test reversed or replaced alone, and the spec's readings (`spec_*`); `sep` counts the cases a
control's prediction differs from the model's, `passed` those where the emulator still equals the control (must be 0
when sep > 0). Stdlib only, plus objdump for `static`.
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
from anim_s6f_emu import read_out  # noqa: E402
from economy import w32, imul, tdiv, d1024, d4096, muldiv  # noqa: E402

M32 = 0xFFFFFFFF
DEFDIR = os.path.join(ROOT, "workspace", "logs", "n66z", "s4e", "run2")
FAMILIES = ("price", "rep", "gold", "wear", "timer", "repl")
NCASES = {"price": 6000, "rep": 2000, "gold": 1500, "wear": 2500, "timer": 800, "repl": 1500}

FN_PRICE, FN_CANREP, FN_HASDUR, FN_RECHARGE = 0x0062EFB0, 0x0062E660, 0x00629930, 0x00628D30
FN_GOLDCAP, FN_STASHCAP, FN_ADDGOLD = 0x00622E70, 0x00623460, 0x0053FF00
FN_WEAR, FN_TIMER = 0x00559E30, 0x00558530
OBS_ERR = 0x00408090
OBS_SETSTAT, OBS_ADDSTAT = 0x00627260, 0x006272B0
OBS_BREAK, OBS_PKT, OBS_QFIND, OBS_QADD = 0x0055F850, 0x005531C0, 0x005415A0, 0x005417D0
GUARDS = (0x00408A60, 0x00681E09, 0x0040B4B0, 0x0040B430, 0x0040B480)

# image globals the loader writes at start-up (declared by the memory spec)
G_DT, G_NITEMS, G_PITEMS, G_LINK = 0x00744304, 0x0096CA58, 0x0096CA5C, 0x0096BCC4
G_NAFF, G_PAFF, G_NBOOK, G_PBOOK, G_PNPC, G_NNPC = 0x0096CA7C, 0x0096CA80, 0x0096CC60, 0x0096CC64, 0x0096C5D8, 0x0096C5DC
BITMASK = 0x006CE268            # g_BitMask32 (.rdata)

# scratch memory
DT = 0x22000000
ITEMS, NIT, IT_SZ = 0x22010000, 40, 0x1A8
TYPES, NTY, TY_SZ = 0x22020000, 56, 0xE4
BITS, BSTRIDE = 0x22028000, 2
ISC, NISC, ISC_SZ = 0x22030000, 260, 0x144
SKL, NSK, SK_SZ = 0x22050000, 48, 0x23C
AFF, NAF, AF_SZ = 0x22060000, 40, 0x90
UNQ, NUQ, UQ_SZ = 0x22062000, 10, 0x14C
SETS, NSET, SET_SZ = 0x22064000, 10, 0x1B8
NPC, NNPC, NPC_SZ = 0x22066000, 8, 0x4C
BOOKS, NBK, BK_SZ = 0x22067000, 4, 0x20
MONST, NMS, MS_SZ = 0x22068000, 10, 0x1A8
LINK, PAIRS = 0x2206A000, 0x2206A100
QR, QBUF, QLEN = 0x2206B000, 0x2206B100, 0x80
PLAYER, PLIST, POWN = 0x22070000, 0x22070100, 0x22070200
ITEM, IDATA, ILIST, IOWN, ICACHE = 0x22071000, 0x22071100, 0x22071200, 0x22071400, 0x22071800
INV, CHILD = 0x22072000, 0x22073000
GAME, OWNER = 0x22078000, 0x22079000

T_BOOK, T_BODY, T_ARMO, T_WEAP = 18, 40, 50, 45
ST_LVL, ST_QTY, ST_DUR, ST_MAXDUR, ST_RP, ST_AC = 12, 70, 72, 73, 87, 31
ST_STAFF, ST_INDESTR, ST_CHARGED, ST_REPDUR, ST_REPQTY, ST_STACK = 107, 152, 204, 252, 253, 254
NPC_CLASSES = (154, 147, 178, 199, 253, 257, 511, 513)   # 513 last: its max buy[3] lies past the table


def u32(v):
    return v & M32


def le32(v):
    return struct.pack("<I", v & M32)


def w(addr, data):
    return "w %08x %s" % (addr, bytes(data).hex())


def code(i):
    """The scratch item code of Items row i (unique): row 0 'rin ', row 1 'amu ', the rest letters and a digit."""
    if i == 0:
        return 0x206E6972
    if i == 1:
        return 0x20756D61
    return struct.unpack("<I", bytes([0x61 + i // 26, 0x61 + i % 26, 0x30 + i % 10, 0x20]))[0]


LINKED = sorted((code(i), i) for i in range(40))      # EXCEL_FindCode's pairs, sorted by code (unsigned)


RIN, AMU, ZERO = 0x206E6972, 0x20756D61, 0x20202030


class Rec(bytearray):
    def g(self, o, f="<i"):
        return struct.unpack_from(f, self, o)[0]

    def p(self, o, v, f="<i"):
        if f in ("<i", "<I"):
            struct.pack_into("<I", self, o, v & M32)
        elif f in ("<h", "<H"):
            struct.pack_into("<H", self, o, v & 0xFFFF)
        else:
            struct.pack_into(f, self, o, v)


# ================================================================================================= the tables
def pick_val(r, kind):
    if kind == "cost":
        return r.choice([r.randrange(0, 3000), r.randrange(0, 3000), r.randrange(3000, 70000),
                         r.randrange(0x10000, 0x200000), r.randrange(0x10000, 0x200000), -r.randrange(1, 5000),
                         r.choice([0, 1, 0xFFFF, 0x10000, 0x7FFFFFFF]), r.getrandbits(31)])
    if kind == "mult":
        return r.choice([r.randrange(0, 2049), r.randrange(0, 2049), 1024, 0, r.randrange(2049, 0x30000),
                         -r.randrange(1, 2000), r.getrandbits(20)])
    if kind == "add":
        return r.choice([0, r.randrange(0, 5000), r.randrange(0, 50000), -r.randrange(1, 3000), r.getrandbits(18)])
    raise ValueError(kind)


class World:
    """The declared tables: baseline records (seeded once), copied per case before the case's overrides."""

    def __init__(self):
        r = random.Random("n66z-s4e2-image")
        self.r = r
        self.items = [self.rand_item(r, i) for i in range(NIT)]
        self.types = [self.rand_type(r) for _ in range(NTY)]
        self.bits = [self.rand_bits(r, t) for t in range(NTY)]
        self.isc = [self.rand_isc(r, s) for s in range(NISC)]
        self.skills = [self.rand_skill(r) for _ in range(NSK)]
        self.aff = []
        for _ in range(NAF):
            a = Rec(r.getrandbits(8) for _ in range(AF_SZ))
            a.p(0x88, pick_val(r, "mult"))
            a.p(0x8C, pick_val(r, "add"))
            self.aff.append(a)
        self.unq, self.sets = [], []
        for _ in range(NUQ):
            a = Rec(r.getrandbits(8) for _ in range(UQ_SZ))
            a.p(0x7C, pick_val(r, "mult"))
            a.p(0x80, pick_val(r, "add"))
            self.unq.append(a)
        for _ in range(NSET):
            a = Rec(r.getrandbits(8) for _ in range(SET_SZ))
            a.p(0x38, pick_val(r, "mult"))
            a.p(0x3C, pick_val(r, "add"))
            self.sets.append(a)
        self.npc = [self.rand_npc(r, c) for c in NPC_CLASSES]
        self.books = []
        for _ in range(NBK):
            a = Rec(r.getrandbits(8) for _ in range(BK_SZ))
            a.p(0x14, r.choice([r.randrange(0, 200), r.randrange(0, 100000), -r.randrange(1, 100)]))
            a.p(0x10, r.randrange(0, 100000))
            self.books.append(a)
        self.ms = []
        for _ in range(NMS):
            a = Rec(r.getrandbits(8) for _ in range(MS_SZ))
            for k in range(4):
                a.p(0xAA + 2 * k, r.choice([r.randrange(0, 100), r.randrange(-0x8000, 0x8000)]), "<h")
            self.ms.append(a)
        self.shift, self.mask = 6, 0x3F

    @staticmethod
    def rand_item(r, i):
        a = Rec(r.getrandbits(8) for _ in range(IT_SZ))
        a.p(0x80, code(i))
        a.p(0x84, 0)
        for o in (0x88, 0x8C):
            a.p(o, r.choice([0, 0, ZERO, code(r.randrange(NIT)), 0x7A7A7A7A]))
        a.p(0xE0, pick_val(r, "cost"))
        a.p(0xE4, r.randrange(0, 100))
        a.p(0xE8, r.choice([0, 1, r.randrange(2, 600)]))
        a.p(0xCC, r.randrange(0, 200))
        a.p(0xD0, r.choice([0, r.randrange(1, 400)]))
        a.p(0xD4, r.randrange(0, 200000))
        a[0x112] = r.choice([0, r.randrange(1, 256)])
        a[0x113] = r.choice([0, 0, 1])
        a.p(0x11E, r.randrange(NTY), "<h")
        a.p(0x120, r.choice([0, 0, -1, r.randrange(NTY), NTY + 3]), "<h")
        a[0x132] = r.choice([0, 0, 1, r.randrange(256)])
        return a

    @staticmethod
    def rand_type(r):
        a = Rec(r.getrandbits(8) for _ in range(TY_SZ))
        a[0x08] = r.choice([0, 1, 1, r.randrange(256)])
        a.p(0x0E, r.choice([0, 0, 0, 1, -1]), "<h")
        a[0x10] = r.choice([0, 0, 1])
        a[0x1F] = r.choice([1, 2, 3, 4, 5, 6, 255, 7])
        a[0x21] = r.choice([7, 7, 7, r.randrange(0, 7), r.randrange(8, 256)])
        return a

    @staticmethod
    def rand_bits(r, t):
        ws = [r.getrandbits(32) & 0 for _ in range(BSTRIDE)]
        for b in (T_BOOK, T_BODY, T_ARMO, T_WEAP):
            if r.random() < 0.25:
                ws[b >> 5] |= 1 << (b & 31)
        for _ in range(3):
            b = r.randrange(BSTRIDE * 32)
            ws[b >> 5] |= 1 << (b & 31)
        return ws

    @staticmethod
    def rand_isc(r, s):
        a = Rec(r.getrandbits(8) for _ in range(ISC_SZ))
        a[0x05] &= ~4
        a[0x18] = r.choice([0, 0, 0, 8, r.randrange(1, 12), r.randrange(32)])
        a[0x30] = r.choice([0, 0, 0, 1, 2, 3, 4, 4, 5, 7, r.randrange(256)])
        a.p(0x10, pick_val(r, "mult"))
        a.p(0x14, pick_val(r, "add"))
        return a

    @staticmethod
    def rand_skill(r):
        a = Rec(r.getrandbits(8) for _ in range(SK_SZ))
        a.p(0x174, r.choice([0, r.randrange(0, 100), r.randrange(-0x8000, 0x8000)]), "<h")
        a.p(0x234, r.choice([0, r.randrange(0, 897), r.randrange(897, 0x20000), -r.randrange(1, 900)]))
        a.p(0x238, r.choice([0, r.randrange(0, 10000), -r.randrange(1, 1000)]))
        return a

    @staticmethod
    def rand_npc(r, cls):
        a = Rec(r.getrandbits(8) for _ in range(NPC_SZ))
        a.p(0, cls)
        for o in (4, 8, 0xC):
            a.p(o, r.choice([1024, r.randrange(0, 2049), r.randrange(0, 2049), 0, r.randrange(2049, 0x20000)]))
        for k in range(3):
            a.p(0x10 + 4 * k, r.choice([0, 0, r.randrange(1, 48)]))
            for o in (0x1C, 0x28, 0x34):
                a.p(o + 4 * k, r.choice([1024, r.randrange(0, 2049), 0, r.randrange(2049, 0x20000)]))
        for k in range(3):
            a.p(0x40 + 4 * k, r.choice([r.randrange(0, 100000), r.randrange(0, 0x7FFFFFFF), -r.randrange(1, 100)]))
        return a

    def spec_lines(self, d):
        """The memory spec's table directives (load files written under d) and the globals."""
        blobs = {
            "items.bin": (ITEMS, b"".join(self.items)), "types.bin": (TYPES, b"".join(self.types)),
            "bits.bin": (BITS, b"".join(struct.pack("<%dI" % BSTRIDE, *ws) for ws in self.bits)),
            "isc.bin": (ISC, b"".join(self.isc)), "skills.bin": (SKL, b"".join(self.skills)),
            "aff.bin": (AFF, b"".join(self.aff)), "unq.bin": (UNQ, b"".join(self.unq)),
            "sets.bin": (SETS, b"".join(self.sets)), "npc.bin": (NPC, b"".join(self.npc)),
            "books.bin": (BOOKS, b"".join(self.books)), "ms.bin": (MONST, b"".join(self.ms)),
            "pairs.bin": (PAIRS, b"".join(struct.pack("<Ii", c, i) for c, i in LINKED)),
        }
        out = []
        for name in sorted(blobs):
            addr, data = blobs[name]
            with open(os.path.join(d, name), "wb") as f:
                f.write(data)
            out.append("load %08x %s" % (addr, os.path.join(d, name)))
        dt = bytearray(0x1000)
        for off, v in ((0xA78, MONST), (0xA80, NMS), (0xB98, SKL), (0xBA0, NSK), (0xBCC, ISC), (0xBD4, NISC),
                       (0xBF8, TYPES), (0xBFC, NTY), (0xC00, BSTRIDE), (0xC04, BITS), (0xC18, SETS), (0xC1C, NSET),
                       (0xC24, UNQ), (0xC28, NUQ), (0xC6C, 6), (0xC70, 0x3F)):
            struct.pack_into("<I", dt, off, v)
        out.append("bytes %08x %s" % (DT, bytes(dt).hex()))
        for addr, v in ((G_DT, DT), (G_NITEMS, NIT), (G_PITEMS, ITEMS), (G_LINK, LINK), (G_NAFF, NAF), (G_PAFF, AFF),
                        (G_NBOOK, NBK), (G_PBOOK, BOOKS), (G_PNPC, NPC), (G_NNPC, NNPC), (LINK, NIT),
                        (LINK + 8, PAIRS), (QR, QBUF)):
            out.append("dword %08x %08x" % (addr, v))
        return out


WORLD = None


def world():
    global WORLD
    if WORLD is None:
        WORLD = World()
    return WORLD


class View:
    """A case's tables: the baseline with the case's record overrides (copy on write)."""

    def __init__(self, W):
        self.W = W
        self.over = {}
        self.dt = {0xC6C: W.shift, 0xC70: W.mask}

    def rec(self, tab, i):
        if (tab, i) in self.over:
            return self.over[(tab, i)]
        return getattr(self.W, tab)[i]

    def mut(self, tab, i):
        if (tab, i) not in self.over:
            src = getattr(self.W, tab)[i]
            self.over[(tab, i)] = Rec(src) if tab != "bits" else list(src)
        return self.over[(tab, i)]

    def lines(self):
        base = {"items": (ITEMS, IT_SZ), "types": (TYPES, TY_SZ), "isc": (ISC, ISC_SZ), "skills": (SKL, SK_SZ),
                "aff": (AFF, AF_SZ), "unq": (UNQ, UQ_SZ), "sets": (SETS, SET_SZ), "npc": (NPC, NPC_SZ),
                "books": (BOOKS, BK_SZ), "ms": (MONST, MS_SZ)}
        out = []
        for (tab, i), v in sorted(self.over.items()):
            if tab == "bits":
                out.append(w(BITS + 4 * BSTRIDE * i, struct.pack("<%dI" % BSTRIDE, *v)))
            else:
                a, sz = base[tab]
                old = getattr(self.W, tab)[i]
                lo = next((k for k in range(sz) if v[k] != old[k]), None)
                if lo is not None:
                    hi = max(k for k in range(sz) if v[k] != old[k]) + 1
                    out.append(w(a + sz * i + lo, v[lo:hi]))
        for off in (0xC6C, 0xC70):
            if self.dt[off] != (self.W.shift if off == 0xC6C else self.W.mask):
                out.append(w(DT + off, le32(self.dt[off])))
        return out

    # table getters as the game's
    def item_rec(self, c):
        return self.rec("items", c) if 0 <= c < NIT else None

    def find_code(self, cd):
        """EXCEL_FindCode over the declared link (pairs sorted by code)."""
        lo, hi = 0, NIT
        if hi > 0:
            while True:
                mid = tdiv(hi - lo, 2) + lo
                c, row = LINKED[mid]
                if c < cd:
                    lo, mid = mid + 1, hi
                elif c == cd:
                    return row
                hi = mid
                if not lo < mid:
                    break
        return -1

    def by_code(self, cd):
        i = self.find_code(cd)
        return self.rec("items", i) if i >= 0 else None

    def type_rec(self, t):
        return self.rec("types", t) if 0 <= t < NTY else None

    def bit(self, t, b):
        ws = self.rec("bits", t)
        return ws[b >> 5] >> (b & 31) & 1

    def isc_rec(self, s):
        return self.rec("isc", s) if 0 <= s < NISC else None

    def skill(self, k):
        return self.rec("skills", k) if 0 <= k < NSK else None


# ================================================================================================= units
class Unit:
    """A unit with an extended stat list: own (+0x24) and cache (+0x48) arrays, list owner 0 (no floor)."""

    def __init__(self, base, lst, own_at, cache_at, ext=True):
        self.base, self.lst, self.own_at, self.cache_at = base, lst, own_at, cache_at
        self.type = 4
        self.cls = 0
        self.own = {}
        self.cache = {}
        self.ext = ext
        self.has_list = True

    def getstat(self, V, s, p=0):
        """STATS_GetUnitStat."""
        if not self.has_list or not 0 <= s < NISC:
            return 0
        k = u32((s << 16) + (p & M32))
        d = self.cache if self.ext else self.own
        return w32(d.get(k, 0))

    def basestat(self, V, s, p=0):
        if not self.has_list or not 0 <= s < NISC:
            return 0
        return w32(self.own.get(u32((s << 16) + p), 0))

    def entries(self, sid, cap=0x40):
        """StatListGetEntries: the cache's entries of stat sid (extended lists only)."""
        if not self.has_list or not self.ext:
            return []
        out = [(k & 0xFFFF, w32(v)) for k, v in sorted(self.cache.items(), key=lambda kv: w32(kv[0]))
               if k >> 16 == sid]
        return out[:cap]

    @staticmethod
    def arr(d):
        return b"".join(struct.pack("<Ii", k, w32(v)) for k, v in sorted(d.items(), key=lambda kv: w32(kv[0])))

    def lines(self):
        out = [w(self.base, le32(self.type) + le32(self.cls))]
        out.append(w(self.base + 0x5C, le32(self.lst if self.has_list else 0)))
        if self.has_list:
            fl = 0x80000000 if self.ext else 0
            out.append(w(self.lst + 0x10, le32(fl)))
            out.append(w(self.lst + 0x44, le32(0)))
            out.append(w(self.own_at, self.arr(self.own) or b"\0"))
            out.append(w(self.lst + 0x24, le32(self.own_at) + struct.pack("<hH", len(self.own), len(self.own))))
            if self.ext:
                out.append(w(self.cache_at, self.arr(self.cache) or b"\0"))
                out.append(w(self.lst + 0x48, le32(self.cache_at) + struct.pack("<hH", len(self.cache),
                                                                                  len(self.cache))))
        return out


# ================================================================================================= the item model
class Item(Unit):
    def __init__(self):
        Unit.__init__(self, ITEM, ILIST, IOWN, ICACHE)
        self.has_data = True
        self.q = 2
        self.fl = 0
        self.fi = -1
        self.ver = 1
        self.auto = 0
        self.pre = [0, 0, 0]
        self.suf = [0, 0, 0]
        self.ear = 0
        self.children = []           # Items rows of socketed children
        self.inv = False

    def lines(self):
        out = Unit.lines(self)
        out.append(w(self.base + 0x14, le32(IDATA if self.has_data else 0)))
        out.append(w(self.base + 0x60, le32(INV if self.inv else 0)))
        if self.has_data:
            out.append(w(IDATA, le32(self.q)))
            out.append(w(IDATA + 0x18, le32(self.fl)))
            out.append(w(IDATA + 0x28, le32(self.fi)))
            out.append(w(IDATA + 0x30, struct.pack("<H", self.ver & 0xFFFF)))
            out.append(w(IDATA + 0x36, struct.pack("<7H", self.auto, *(self.pre + self.suf))))
            out.append(w(IDATA + 0x48, bytes([self.ear & 0xFF])))
        if self.inv:
            first = CHILD if self.children else 0
            out.append(w(INV, le32(0x01020304) + le32(0) + le32(0) + le32(first)))
            for k, c in enumerate(self.children):
                u = CHILD + 0x200 * k
                nxt = CHILD + 0x200 * (k + 1) if k + 1 < len(self.children) else 0
                out.append(w(u, le32(4) + le32(c)))
                out.append(w(u + 0x14, le32(u + 0x100)))
                out.append(w(u + 0x100 + 0x64, le32(nxt)))
        return out


class Fatal(Exception):
    def __init__(self, err):
        Exception.__init__(self, "fatal 0x%X" % err)
        self.err = err


class Model:
    """ITEMS_TradePriceCore and its callees over a View. `ctl` names one control (a reversed test or a spec reading)."""

    def __init__(self, V, ctl=None):
        self.V, self.ctl = V, ctl
        self.br = collections.Counter()

    def b(self, k):
        self.br[k] += 1

    # ---- item getters
    def irec(self, it):
        r = self.V.item_rec(it.cls)
        if r is None:
            raise Fatal(0x1EF)
        return r

    def own_type(self, it):
        return self.irec(it).g(0x11E, "<h")

    def is_type(self, it, t):
        V = self.V
        if not 0 <= t < NTY:
            return 0
        ot = self.own_type(it)
        if V.bit(ot, t):
            return 1
        t2 = self.irec(it).g(0x120, "<h")
        if 0 < t2 < NTY:
            return V.bit(t2, t)
        return 0

    def trec(self, it):
        return self.V.type_rec(self.own_type(it))

    def stackable(self, it):
        return self.irec(it)[0x132]

    def max_stack(self, it):
        v = w32(self.irec(it).g(0xE8) + it.getstat(self.V, ST_STACK))
        return 0x1FF if v > 0x1FE else v

    def quiver(self, it):
        t = self.trec(it)
        return t.g(0x0E, "<h") if t is not None else 0

    def throwable(self, it):
        t = self.trec(it)
        return t[0x10] if t is not None else 0

    def class_item(self, it):
        t = self.trec(it)
        return t is not None and t[0x21] < 7

    def eth(self, it):
        return it.fl & 0x400000

    def max_dur(self, it):
        if not it.has_list:
            return 0
        if it.basestat(self.V, ST_MAXDUR) == 0:
            return 0
        return it.getstat(self.V, ST_MAXDUR)

    def has_dur(self, it):
        r = self.irec(it)
        if r[0x113] != 0 or r[0x112] == 0:
            self.b("hasdur_base_no")
            return False
        if self.max_dur(it) == 0:
            self.b("hasdur_maxdur0")
            return False
        v = it.getstat(self.V, ST_INDESTR)
        if self.ctl == "hasdur_no152":
            return True
        self.b("hasdur_152_%s" % ("lt1" if v < 1 else "ge1"))
        return v < 1

    def has_charges(self, it):
        es = it.entries(ST_CHARGED)
        if not es:
            return False, True
        return True, all(not ((v & 0xFF) < (v >> 8)) for _, v in es)

    def repairable_stack(self, it):
        t = self.trec(it)
        if t is None or t[0x08] == 0:
            return False
        return bool(self.throwable(it) and self.stackable(it) and not self.eth(it))

    def can_repair(self, it):
        if it.type != 4 or not it.has_data or not it.fl & 0x10:
            self.b("canrep_unid")
            return False
        if self.eth(it) and self.ctl != "canrep_eth":
            self.b("canrep_eth")
            return False
        has, full = self.has_charges(it)
        if has and not full:
            self.b("canrep_charges")
            return True
        t = self.trec(it)
        if t is None or t[0x08] == 0:
            self.b("canrep_norepair")
            return False
        if self.repairable_stack(it):
            self.b("canrep_stack")
            return True
        self.b("canrep_hasdur")
        return self.has_dur(it)

    # ---- the terms
    def staff_mods(self, it, P, S, R, n):
        t = self.trec(it)
        if t is None or t[0x1F] == 7:
            self.b("staff_skip7")
            return P, S, R
        tP = tS = tR = 0
        for param, v in it.entries(ST_STAFF):
            k = self.V.skill(param)
            if k is None:
                self.b("staff_skill_out")
                continue
            m, a = k.g(0x234), k.g(0x238)
            c = w32(2 * v - 1)
            if P > 0xFFFF and m != 0 and self.ctl != "staff_small":
                self.b("staff_large")
                e = d1024(m)
                tP = w32(tP + imul(w32(imul(e, P) + a), c))
                tS = w32(tS + imul(w32(imul(d4096(m), S) + a), c))
                tR = w32(tR + imul(w32(imul(R, e) + a), c))
            else:
                self.b("staff_small")
                tP = w32(tP + imul(w32(d1024(imul(m, P)) + a), c))
                tS = w32(tS + imul(w32(d4096(imul(S, m)) + a), c))
                tR = w32(tR + imul(w32(d1024(imul(R, m)) + a), c))
        n = u32(n)
        return w32(P + u32(tP) // n), w32(S + u32(tS) // n), w32(R + u32(tR) // n)

    def stat_terms(self, it, P, S, R, n):
        V = self.V
        sP = sS = sR = 0
        if not (it.has_list and it.ext):
            return P, S, R
        for key, full in sorted(it.cache.items(), key=lambda kv: w32(kv[0]))[:0x1FF]:
            sid, param = key >> 16, key & 0xFFFF
            v = w32(it.getstat(V, sid, param) - it.basestat(V, sid, param))
            rec = V.isc_rec(sid)
            if v == 0 or rec is None:
                continue
            if rec[0x18]:
                v = v >> (rec[0x18] & 31)
            enc = rec[0x30]
            if enc == 1:
                k = V.skill(param)
                if k is None:
                    self.b("enc1_skill_out")
                    continue
                m, a, x, sk = k.g(0x234), k.g(0x238), v, True
            elif enc in (2, 3):
                kk = param >> (V.dt[0xC6C] & 31)
                x = u32(V.dt[0xC70] & param)
                k = V.skill(kk)
                m, a, sk = k.g(0x234), k.g(0x238), True
                x = w32(x)
            elif enc == 4 and self.ctl != "enc4_plain":
                lo = ((v >> 2) & 0x3FF) - 0x100
                hi = ((v >> 12) & 0x3FF) - 0x100
                x = tdiv(lo + hi, 2)
                m, a, sk = rec.g(0x10), rec.g(0x14), False
                self.b("enc4")
            else:
                m, a, x, sk = rec.g(0x10), rec.g(0x14), v, False
            self.b("enc%s" % (enc if enc < 5 else "5+"))
            sdiv = d4096 if sk else d1024
            if imul(P, x) > 0xFFFF and m != 0:
                self.b("terms_large")
                sP = w32(sP + imul(d1024(imul(P, x)), m) + a)
                sS = w32(sS + imul(sdiv(imul(S, x)), m) + a)
                sR = w32(sR + imul(d1024(imul(R, x)), m) + a)
            else:
                sP = w32(sP + d1024(imul(imul(m, P), x)) + a)
                sS = w32(sS + sdiv(imul(imul(m, S), x)) + a)
                sR = w32(sR + d1024(imul(imul(m, R), x)) + a)
        n = u32(n)
        return w32(P + u32(sP) // n), w32(S + u32(sS) // n), w32(R + u32(sR) // n)

    def recharge(self, it):
        V = self.V
        tot = 0
        for param, v in it.entries(ST_CHARGED):
            c, x = v & 0xFF, v >> 8
            kk = param >> (V.dt[0xC6C] & 31)
            k = V.skill(kk)
            if not c < x or k is None:
                self.b("rc_skip")
                continue
            K = w32((V.dt[0xC70] & param) + 2 + tdiv(k.g(0x174, "<h"), 6) * 2)
            T = imul(K, 10000)
            m = k.g(0x234)
            if T > 0xFFFF and m != 0 and self.ctl != "recharge_small":
                self.b("rc_large")
                t = imul(d1024(T), m)
            else:
                self.b("rc_small")
                t = d1024(imul(imul(m, K), 10000))
            tot = w32(tot + tdiv(imul(x - c, w32(t + k.g(0x238))), x))
        return tot

    def gamble(self, it, L):
        V = self.V
        b0 = self.irec(it)
        cd = b0.g(0x84, "<I") or b0.g(0x80, "<I")
        b = V.by_code(cd)
        if b is None:
            raise Fatal(0xB1A)
        if b.g(0x80, "<I") in (RIN, AMU):
            self.b("gamble_rinamu")
            return b.g(0xD4)
        avg = tdiv(w32(b.g(0xE8) + b.g(0xE4)), 2)
        avg = avg if avg >= 1 else 1
        cost, lvl = b.g(0xE0), b[0xFD]
        x = e = xc = ec = 0
        floor = self.ctl != "gamble_nofloor"
        uc = b.g(0x88, "<I")
        if uc != 0 and uc != ZERO:
            u = V.by_code(uc)
            if u is not None:
                x = (tdiv(w32(imul(w32(L - u[0xFD]), 100) + 1), 2) if self.ctl == "gamble_plus1_first"
                     else tdiv(imul(w32(L - u[0xFD]), 100), 2) + 1)
                if x < 0 and floor:
                    self.b("gamble_x_floor")
                    x = 0
                xc = u.g(0xE0)
        tc = b.g(0x8C, "<I")
        if tc != 0 and tc != ZERO:
            t = V.by_code(tc)
            if t is not None:
                e = (tdiv(w32(imul(w32(L - t[0xFD]), 100) + 1), 4) if self.ctl == "gamble_plus1_first"
                     else tdiv(imul(w32(L - t[0xFD]), 100), 4) + 1)
                if e < 0 and floor:
                    self.b("gamble_e_floor")
                    e = 0
                ec = t.g(0xE0)
        if 10000 - e - x < 0:
            self.b("gamble_neg_weight")
            if self.ctl == "gamble_cap":
                x, e = (x, 10000 - x) if x <= 10000 else (10000, 0)
        tot = w32(imul(imul(w32(10000 - e - x), cost), avg) + imul(ec, e) + imul(xc, x))
        avgc = tdiv(tot, 10000)
        L2 = L if L >= 6 else 5
        lv = w32((lvl - 45 if lvl >= 45 else 0) - lvl // 2 + L2)
        return tdiv(imul(w32(tdiv(imul(lv, 250), 3) + avgc), w32(tdiv(w32(2 * L2 + 1), 3) + 20)), 15)

    def qbit(self, qbuf, qid, bit):
        i = w32(w32(qid * 16) + bit)
        return bool(qbuf[i >> 3] >> (i & 7) & 1)

    # ---- the core
    def price(self, pl, it, d, qbuf, npc, mode):
        V, ctl = self.V, self.ctl
        if pl is None or it is None or (it.type != 4 and ctl != "b1_any"):
            self.b("B1")
            return 0x7FFFFFFF
        L = pl.getstat(V, ST_LVL)
        if mode == 3 and not self.can_repair(it) and ctl != "b2_off":
            self.b("B2")
            return 0
        if it.type == 4 and it.has_data and it.fl & 0x20000 and ctl != "b3_off":
            self.b("B3_m%d" % mode if mode < 4 else "B3_mx")
            return 1
        b = self.irec(it)
        cost = b.g(0xE0)
        q = it.getstat(V, ST_QTY)
        q = q if q >= 1 else 1
        r = pl.getstat(V, ST_RP)
        if ctl == "rcap_100":
            r = 100 if r > 100 else r
        elif r > 0x62:
            self.b("r_capped")
            r = 99
        if mode == 2:
            if it.ver & 0xFFFF == 0 and ctl != "v0_compute":
                self.b("E1_v0")
                cd = b.g(0x84, "<I") or b.g(0x80, "<I")
                bb = V.by_code(cd)
                return bb.g(0xD4)
            G = self.gamble(it, L)
            self.b("E1_gamble_r%s" % ("0" if r == 0 else "x"))
            return G if r == 0 else w32(G - muldiv(G, r, 100))
        R, n = 0, 1
        if it.fl & 0x10000:
            self.b("base_ear")
            P = S = imul(it.ear & 0xFF, cost)
            if ctl in ("ear_r", "tome_body_r"):
                R = P
        elif self.is_type(it, T_BODY):
            fi = it.fi
            ms = V.rec("ms", fi) if 0 <= fi < NMS else None
            if ms is None:
                self.b("base_body_norec")
                P = S = cost
            else:
                self.b("base_body")
                P = S = w32(cost + 8 * ms.g(0xAA + 2 * d, "<h"))
            if ctl == "tome_body_r":
                R = P
        elif self.is_type(it, T_BOOK):
            s0 = it.suf[0]
            if not (s0 < NBK and s0 != 0xFFFF and s0 != -1):
                raise Fatal(0xBBA)
            bk = V.rec("books", s0)
            self.b("base_tome")
            P = S = w32(imul(bk.g(0x14), q) + (bk.g(0x10) if ctl == "tome_basecost" else cost))
            if ctl == "tome_body_r":
                R = P
        elif self.quiver(it):
            self.b("base_quiver")
            P = S = d1024(imul(cost, q))
            R = d1024(imul(self.max_stack(it), cost))
        else:
            P = S = R = cost
            if self.stackable(it):
                ms = self.max_stack(it)
                n = ms if ms >= 2 else 1
                self.b("base_stack" if n > 1 else "base_stack1")
            else:
                self.b("base_cost")
        if self.is_type(it, T_ARMO):
            ac = it.basestat(V, ST_AC)
            maxac, minac = b.g(0xD0), b.g(0xCC)
            if w32(maxac - minac) != -1 and maxac != 0:
                if ctl == "armor_keep_base" and (it.fl & 0x10000 or self.is_type(it, T_BODY) or
                                                 self.is_type(it, T_BOOK)):
                    pass
                else:
                    self.b("armor_step" + ("_over_ear" if it.fl & 0x10000 else ""))
                    P = S = R = tdiv(imul(cost, ac), maxac)
            else:
                self.b("armor_skip")
        ident = it.fl & 0x10
        mp = 4 <= it.q <= 9
        if not mp:
            P, S, R = self.staff_mods(it, P, S, R, n)
        if ident:
            dP = dS = dR = 0
            Pt = P

            def add(m, a, acc):
                dP, dS, dR = acc
                if Pt > 0xFFFF and m != 0 and ctl != "addterm_small":
                    self.b("add_large")
                    return (w32(dP + imul(d1024(P), m) + a), w32(dS + imul(d1024(S), m) + a),
                            w32(dR + imul(d1024(R), m) + a))
                return (w32(dP + d1024(imul(m, P)) + a), w32(dS + d1024(imul(m, S)) + a),
                        w32(dR + d1024(imul(m, R)) + a))

            def affix(aid):
                aid = aid & 0xFFFF
                if 0 < aid <= NAF:
                    a = V.rec("aff", aid - 1)
                    return a.g(0x88), a.g(0x8C)
                return None

            acc = (0, 0, 0)
            a0 = affix(it.auto)
            if a0:
                self.b("auto")
                acc = add(a0[0], a0[1], (0, 0, 0))
            terms = False
            qq = it.q
            if qq == 1:
                acc = (-tdiv(P, 2), -tdiv(S, 2), -tdiv(R, 2))
            elif qq in (3, 9):
                terms = True
            elif qq in (6, 8):
                for i in range(3):
                    for aid in (it.pre[i], it.suf[i]):
                        a = affix(aid)
                        if a:
                            acc = add(a[0], a[1], acc)
                terms = True
            elif qq == 5:
                rec = V.rec("sets", it.fi) if 0 <= it.fi < NSET else None
                if rec is not None:
                    acc = add(rec.g(0x38), rec.g(0x3C), acc)
            elif qq in (4, 7):
                rec = V.rec("unq", it.fi) if qq == 7 and 0 <= it.fi < NUQ else None
                if rec is not None:
                    self.b("q7_rec")
                    acc = add(rec.g(0x7C), rec.g(0x80), acc)
                elif qq == 7 and ctl == "q7_norec_none":
                    pass
                else:
                    if qq == 7:
                        self.b("q7_norec_magic")
                    for aid in (it.pre[0], it.suf[0]):
                        a = affix(aid)
                        if a:
                            acc = add(a[0], a[1], acc)
                    terms = True
            self.b("q%d" % qq if 0 <= qq <= 10 else "q_other")
            if terms:
                P, S, R = self.stat_terms(it, P, S, R, n)
            dP, dS, dR = acc
            P, S, R = w32(P + tdiv(dP, n)), w32(S + tdiv(dS, n)), w32(R + tdiv(dR, n))
            if mp:
                P, S, R = self.staff_mods(it, P, S, R, n)
        if it.inv:
            h = 0
            for c in it.children:
                h = w32(h + tdiv(V.rec("items", c).g(0xE0), 2))
            if it.children:
                self.b("sockets")
            P, S, R = w32(P + h), w32(S + h), w32(R + h)
        if self.eth(it):
            S = tdiv(S, 4)
        if self.class_item(it):
            S = tdiv(S, 4)
        if mode == 1:
            if self.eth(it) and self.has_dur(it) and ctl != "d1_off":
                if self.max_dur(it) != 0 and it.getstat(V, ST_DUR) < 1:
                    self.b("D1_zero")
                    S = 0
        elif mode == 3:
            if not self.quiver(it) and not self.throwable(it) and self.has_dur(it):
                D, M = it.getstat(V, ST_DUR), self.max_dur(it)
                if M == 0 or M <= D:
                    if ctl != "fulldur_keep":
                        self.b("D2_full")
                        R = 0
                elif it.getstat(V, ST_REPDUR) != 0 and ctl != "rep252_plain":
                    self.b("D2_252")
                    R = tdiv(imul(M - 1, R), M) if D < w32(M - 1) else 0
                else:
                    self.b("D2_frac")
                    R = tdiv(imul(w32(M - D), R), M)
        rec = None
        for i in range(NNPC):
            if V.rec("npc", i).g(0) == npc:
                rec = V.rec("npc", i)
                break
        if rec is None:
            raise Fatal(0xCDC)
        self.b("npc_step")
        sell, buy, rep = rec.g(4), rec.g(8), rec.g(0xC)

        def scale(v, m, t):
            return imul(d1024(v), m) if v > 0xFFFF and t != 0 else d1024(imul(m, v))

        if ctl == "recharge_before_npc" and mode == 3 and not self.eth(it):
            R = w32(R + self.recharge(it))
        P = scale(P, sell, sell)
        if S > 0xFFFF and sell != buy and (sell == 0) != (buy == 0):
            self.b("S_test_sell_vs_buy")
        S = scale(S, buy, buy if ctl == "s_test_buy" else sell)
        R = scale(R, rep, rep)
        for k in range(3):
            f = rec.g(0x10 + 4 * k)
            if f != 0 and (self.qbit(qbuf, f, 0) or self.qbit(qbuf, f, 1)):
                self.b("quest_%s" % "ABC"[k])
                mp_, ms_, mr = rec.g(0x1C + 4 * k), rec.g(0x28 + 4 * k), rec.g(0x34 + 4 * k)
                P = scale(P, mp_, mp_)
                S = scale(S, ms_, ms_)
                R = scale(R, mr, mr)
        if not self.is_type(it, T_BOOK) and not self.quiver(it):
            P = imul(P, q)
            if self.stackable(it) and self.can_repair(it):
                Ms = self.max_stack(it)
                if q < Ms and it.getstat(V, ST_REPQTY) == 0:
                    self.b("D4_partial")
                    R = imul(R, w32(Ms - q))
                    S = w32(imul(Ms, S) - R)
                else:
                    self.b("D4_full")
                    S = imul(S, Ms)
                    R = 0
            else:
                S = imul(S, q)
        if mode == 3 and ctl != "recharge_before_npc" and (not self.eth(it) or ctl == "d5_eth"):
            rc = self.recharge(it)
            if rc:
                self.b("D5_recharge")
            R = w32(R + rc)
        mb = rec.g(0x40 + 4 * d) if d < 3 else NEXT_DWORD.get(npc, 0)
        S2 = mb if S > mb else S
        if mode == 1:
            return S2 if S2 >= 1 else 1
        if mode == 3:
            if r != 0 and ctl != "repair_noreduce":
                self.b("D7_rep_r")
                R = w32(R - muldiv(R, r, 100))
            return R if R >= 1 else 1
        if ctl == "maxbuy_mode0":
            P = S2 if P > S2 else P
        if r != 0:
            self.b("D7_buy_r")
            P = w32(P - muldiv(P, r, 100))
        return P if P >= 1 else 1


NEXT_DWORD = {}     # npc class -> the dword after its record (max buy [3]); filled by the generator per case


# ================================================================================================= generators
def gen_stats(r, it, V, want=()):
    """The item's own and cache lists: the price stats with a chance each, and random others."""
    keys = {}
    pick = [ST_QTY, ST_DUR, ST_MAXDUR, ST_AC, ST_INDESTR, ST_REPDUR, ST_REPQTY, ST_STACK, ST_STAFF, ST_CHARGED]
    for s in pick:
        if s in want or r.random() < 0.35:
            for _ in range(1 if s not in (ST_STAFF, ST_CHARGED) else r.randrange(1, 4)):
                p = 0 if s not in (ST_STAFF, ST_CHARGED) else r.choice([r.randrange(NSK), r.randrange(NSK * 64),
                                                                         r.randrange(NSK * 64)])
                keys[(s << 16) | p] = s
    for _ in range(r.choice([0, 1, 3, 6, 12])):
        s = r.choice([r.randrange(NISC), r.randrange(NISC), r.randrange(NISC, 400)])
        p = r.choice([0, 0, r.randrange(NSK), r.randrange(NSK * 64)])
        keys[(s << 16) | p] = s
    for k, s in keys.items():
        if s == ST_QTY:
            v = r.choice([0, 1, 2, r.randrange(1, 600), -r.randrange(1, 5)])
        elif s in (ST_DUR, ST_MAXDUR):
            v = r.choice([0, 1, r.randrange(1, 256), r.randrange(-5, 300)])
        elif s == ST_INDESTR:
            v = r.choice([0, 1, 1, -1, 2])
        elif s in (ST_REPDUR, ST_REPQTY):
            v = r.choice([0, 1, r.randrange(1, 40), r.randrange(-3, 200)])
        elif s == ST_STACK:
            v = r.choice([0, r.randrange(0, 600), -r.randrange(1, 50)])
        elif s == ST_STAFF:
            v = r.choice([1, 2, 3, r.randrange(0, 20), -r.randrange(1, 5)])
        elif s == ST_CHARGED:
            mx = r.choice([0, 1, r.randrange(1, 100), r.randrange(100, 256)])
            v = (mx << 8) | r.choice([0, mx, r.randrange(0, 256), max(mx - 1, 0)])
        else:
            v = r.choice([r.randrange(-50, 300), r.randrange(0, 5000), r.getrandbits(20), -r.getrandbits(16)])
        c = v
        o = v
        roll = r.random()
        if roll < 0.35:
            o = 0
        elif roll < 0.5:
            o = r.choice([v - 1, v + r.randrange(1, 100), r.randrange(-50, 50)])
        if r.random() < 0.15 and s not in (ST_MAXDUR,):
            o = None
        if o is not None:
            it.own[k] = o
        it.cache[k] = c
    if ST_MAXDUR in want and not any(k >> 16 == ST_MAXDUR for k in it.own):
        it.own[ST_MAXDUR << 16] = r.randrange(1, 200)
        it.cache.setdefault(ST_MAXDUR << 16, it.own[ST_MAXDUR << 16])


def gen_item(r, V, scen):
    it = Item()
    it.cls = r.randrange(NIT)
    rec = V.mut("items", it.cls)
    W = V.W
    t = rec.g(0x11E, "<h")
    tr = V.mut("types", t)
    bits = V.mut("bits", t)
    if r.random() < 0.7:
        # re-draw the base and its type for this case
        for o, kind in ((0xE0, "cost"),):
            rec.p(o, pick_val(r, kind))
        rec.p(0xE8, r.choice([0, 1, r.randrange(2, 600), r.randrange(2, 40)]))
        rec.p(0xE4, r.randrange(0, 100))
        rec.p(0xCC, r.randrange(0, 200))
        rec.p(0xD0, r.choice([0, r.randrange(1, 400), rec.g(0xCC) - 1]))
        rec[0x112] = r.choice([0, r.randrange(1, 256), r.randrange(1, 256)])
        rec[0x113] = r.choice([0, 0, 0, 1])
        rec[0x132] = r.choice([0, 0, 1])
        rec.p(0x84, r.choice([0, 0, 0, code(r.randrange(NIT))]))
        rec.p(0x88, r.choice([0, ZERO, code(r.randrange(NIT)), code(r.randrange(NIT)), 0x7A7A7A7A]))
        rec.p(0x8C, r.choice([0, ZERO, code(r.randrange(NIT)), code(r.randrange(NIT)), 0x7A7A7A7A]))
        rec.p(0x120, r.choice([0, 0, -1, r.randrange(NTY), NTY + 3]), "<h")
        tr[0x08] = r.choice([0, 1, 1, 1])
        tr.p(0x0E, r.choice([0, 0, 0, 0, 1]), "<h")
        tr[0x10] = r.choice([0, 0, 1])
        tr[0x1F] = r.choice([1, 3, 6, 255, 7])
        tr[0x21] = r.choice([7, 7, 7, r.randrange(0, 7), r.randrange(8, 256)])
        for b in (T_BOOK, T_BODY, T_ARMO, T_WEAP):
            bits[b >> 5] &= ~(1 << (b & 31))
        kind = scen.get("base") or r.choice(["plain", "plain", "plain", "armo", "armo", "body", "book", "weap"])
        if kind != "plain":
            b = {"armo": T_ARMO, "body": T_BODY, "book": T_BOOK, "weap": T_WEAP}[kind]
            bits[b >> 5] |= 1 << (b & 31)
        if scen.get("also_armo"):
            bits[T_ARMO >> 5] |= 1 << (T_ARMO & 31)
    it.type = 4 if r.random() > 0.01 else r.choice([0, 1, 2, 3, 5])
    it.q = r.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 2, 4, 7, 0, 10])
    fl = r.getrandbits(32) & ~(0x10 | 0x10000 | 0x20000 | 0x400000 | 0x100)
    if r.random() < 0.8:
        fl |= 0x10
    if r.random() < 0.06:
        fl |= 0x10000
    if r.random() < 0.04:
        fl |= 0x20000
    if r.random() < 0.25:
        fl |= 0x400000
    if r.random() < 0.1:
        fl |= 0x100
    it.fl = fl
    it.fi = r.choice([-1, r.randrange(NUQ), r.randrange(NSET), r.randrange(NMS), r.randrange(NMS, 30), -5])
    it.ver = r.choice([1, 1, 0x65, 0, 0x8000, r.getrandbits(16)])
    it.auto = r.choice([0, 0, r.randrange(1, NAF + 1), NAF + 2])
    it.pre = [r.choice([0, r.randrange(1, NAF + 1), r.randrange(1, NAF + 1), NAF + 1]) for _ in range(3)]
    it.suf = [r.choice([0, r.randrange(1, NAF + 1), r.randrange(1, NAF + 1), NAF + 1]) for _ in range(3)]
    if V.W.bits[t] is not None and V.bit(t, T_BOOK) or (rec.g(0x120, "<h") > 0 and rec.g(0x120, "<h") < NTY
                                                       and V.bit(rec.g(0x120, "<h"), T_BOOK)):
        it.suf[0] = r.choice([0, 1, 2, 3, NBK, NBK + 7]) if scen.get("book_fatal") else r.randrange(NBK)
    it.ear = r.randrange(256)
    gen_stats(r, it, V, scen.get("want", ()))
    if r.random() < 0.3:
        it.inv = True
        it.children = [r.randrange(NIT) for _ in range(r.choice([0, 1, 2, 3]))]
    for k, v in scen.get("set", {}).items():
        setattr(it, k, v)
    return it


SCEN = [  # (weight, scenario): steer the draws to every row's branch
    (10, {}), (2, {"base": "armo"}), (2, {"base": "body"}), (2, {"base": "book"}), (1, {"base": "book", "book_fatal": 1}),
    (1, {"also_armo": 1, "set": {"fl": 0x10010}}), (1, {"base": "book", "also_armo": 1}), (1, {"base": "body", "also_armo": 1}),
    (2, {"mode": 3, "want": (ST_DUR, ST_MAXDUR, ST_REPDUR)}), (2, {"mode": 3, "want": (ST_CHARGED,)}),
    (2, {"mode": 1, "want": (ST_DUR, ST_MAXDUR), "eth": 1}), (2, {"mode": 2}), (1, {"mode": 2, "v0": 1}),
    (1, {"q7": 1}), (1, {"enc4": 1}), (1, {"d3": 1}), (1, {"start": 1}), (1, {"npc_missing": 1}),
    (3, {"mode": 3, "rep_dur": 1, "want": (ST_DUR, ST_MAXDUR, ST_REPDUR)}), (1, {"mode": 2, "hi_level": 1}),
]


def gen_price(r):
    W = world()
    V = View(W)
    tot = sum(x for x, _ in SCEN)
    k = r.randrange(tot)
    for wt, scen in SCEN:
        if k < wt:
            break
        k -= wt
    it = gen_item(r, V, scen)
    pl = Unit(PLAYER, PLIST, POWN, 0, ext=False)
    pl.type = 0
    pl.own[ST_LVL << 16] = r.choice([r.randrange(1, 100), r.randrange(1, 6), r.randrange(60, 100), r.randrange(100, 400),
                                     0, -3])
    if r.random() < 0.4:
        pl.own[ST_RP << 16] = r.choice([r.randrange(1, 30), 99, 100, r.randrange(100, 1000), -r.randrange(1, 50)])
    mode = scen.get("mode", r.choice([0, 0, 1, 1, 3, 3, 2, 4, 7]))
    d = r.choice([0, 1, 2])
    if scen.get("d3"):
        d, mode = 3, r.choice([0, 0, 0, 1])
    if scen.get("eth"):
        it.fl |= 0x400000
    if scen.get("v0"):
        it.ver = 0
    if scen.get("start"):
        it.fl |= 0x20000
    if scen.get("q7"):
        it.q = 7
        it.fi = r.choice([-1, -7, NUQ, NUQ + 3, r.randrange(NUQ)])
        it.fl |= 0x10
    if scen.get("rep_dur"):                                   # a repairable item with durability: every D2 branch
        it.type, it.has_data = 4, True
        it.fl = (it.fl | 0x10) & ~0x400000
        tr = V.mut("types", V.rec("items", it.cls).g(0x11E, "<h"))
        tr[0x08], tr[0x10] = 1, 0
        tr.p(0x0E, 0, "<h")
        ir = V.mut("items", it.cls)
        ir[0x112], ir[0x113] = r.randrange(1, 256), 0
        it.cache.pop(ST_INDESTR << 16, None)
        for k in [k for k in it.cache if k >> 16 == ST_CHARGED]:
            it.cache.pop(k)
        md = r.choice([r.randrange(1, 250), r.randrange(1, 10), 1, 2])
        it.own[ST_MAXDUR << 16] = r.choice([md, md, 7])
        it.cache[ST_MAXDUR << 16] = md
        it.cache[ST_DUR << 16] = r.choice([md, md + r.randrange(1, 5), md - 1, md - 2, r.randrange(0, md + 1), 0])
        it.cache[ST_REPDUR << 16] = r.choice([0, 0, r.randrange(1, 30)])
    if scen.get("hi_level"):                                  # high clvl against elite bases: 10000 - e - x < 0
        pl.own[ST_LVL << 16] = r.randrange(150, 2000)
    if scen.get("enc4"):
        s = r.randrange(NISC)
        isc = V.mut("isc", s)
        isc[0x30] = 4
        isc[0x18] = r.choice([0, 0, 1])
        it.cache[s << 16] = r.getrandbits(22)
        it.own.pop(s << 16, None)
        it.q = r.choice([3, 4, 6, 8, 9])
        it.fl |= 0x10
    idx = r.randrange(NNPC)
    npc_rec = V.mut("npc", idx)
    for o in (4, 8, 0xC):
        npc_rec.p(o, r.choice([1024, r.randrange(0, 2049), r.randrange(0, 2049), 0, r.randrange(2049, 0x20000)]))
    if r.random() < 0.3:
        npc_rec.p(4, 0)
        npc_rec.p(8, r.randrange(1, 4096))
    for k3 in range(3):
        npc_rec.p(0x10 + 4 * k3, r.choice([0, 0, r.randrange(1, 48)]))
        for o in (0x1C, 0x28, 0x34):
            npc_rec.p(o + 4 * k3, r.choice([1024, r.randrange(0, 2049), 0, r.randrange(2049, 0x20000)]))
    for k3 in range(3):
        npc_rec.p(0x40 + 4 * k3, r.choice([r.randrange(0, 100000), r.randrange(0, 0x7FFFFFFF), -r.randrange(1, 100)]))
    npc = npc_rec.g(0)
    if scen.get("npc_missing"):
        npc = r.choice([0, 1, 999, 512])
    NEXT_DWORD.clear()
    for i in range(NNPC):
        NEXT_DWORD[V.rec("npc", i).g(0)] = V.rec("npc", i + 1).g(0) if i + 1 < NNPC else 0
    qbuf = bytes(r.getrandbits(8) for _ in range(QLEN))
    player = pl if r.random() > 0.01 else None
    item = it if r.random() > 0.01 else None
    lines = list(V.lines())
    lines.append(w(QBUF, qbuf))
    if player:
        lines += pl.lines()
    if item:
        lines += it.lines()
    lines.append("d %08x 4" % ITEM)
    lines.append("call %08x %08x %08x %08x %08x %08x %08x" % (FN_PRICE, PLAYER if player else 0, ITEM if item else 0,
                                                           d, QR, npc & M32, mode))
    want = {}
    m = Model(V)
    try:
        want["eax"] = u32(m.price(player, item, d, qbuf, npc, mode))
    except Fatal as f:
        want["fatal"] = f.err
    ctl = {}
    for c in PRICE_CTL:
        mc = Model(V, c)
        try:
            ctl[c] = u32(mc.price(player, item, d, qbuf, npc, mode))
        except Fatal as f:
            ctl[c] = "fatal %X" % f.err
        except Exception:                               # a control that leaves the model's domain separates
            ctl[c] = "domain"
    a = {"want": want, "ctl": ctl, "br": dict(m.br), "mode": mode, "d": d,
         "last_npc_d3": int(d == 3 and npc == NPC_CLASSES[-1])}
    return lines, a


PRICE_CTL = ("b1_any", "b2_off", "b3_off", "rcap_100", "v0_compute", "ear_r", "tome_basecost", "armor_keep_base",
             "addterm_small", "staff_small", "recharge_small", "q7_norec_none", "enc4_plain", "d1_off",
             "fulldur_keep", "rep252_plain", "s_test_buy", "recharge_before_npc", "repair_noreduce",
             "gamble_nofloor", "gamble_plus1_first", "gamble_cap", "tome_body_r", "maxbuy_mode0", "hasdur_no152", "canrep_eth")


def gen_rep(r):
    W = world()
    V = View(W)
    scen = r.choice([{}, {"want": (ST_DUR, ST_MAXDUR)}, {"want": (ST_CHARGED,)}, {"want": (ST_MAXDUR, ST_INDESTR)}])
    it = gen_item(r, V, scen)
    fn = r.choice([FN_CANREP, FN_CANREP, FN_HASDUR, FN_RECHARGE])
    item = it if r.random() > 0.02 or fn == FN_RECHARGE else None
    lines = list(V.lines())
    if item:
        lines += it.lines()
    m = Model(V)
    if fn == FN_RECHARGE:
        lines.append("call %08x %08x %08x" % (fn, ITEM if item else 0, 10000))
        want = u32(m.recharge(it)) if item and it.has_list else 0
        ctl = {"recharge_small": u32(Model(V, "recharge_small").recharge(it)) if item else 0}
        pop = 0
    elif fn == FN_CANREP:
        lines.append("call %08x %08x %08x %08x" % (fn, 0, 0, ITEM if item else 0))
        want = int(m.can_repair(it)) if item else 0
        ctl = {"canrep_eth": int(Model(V, "canrep_eth").can_repair(it)) if item else 0,
               "hasdur_no152": int(Model(V, "hasdur_no152").can_repair(it)) if item else 0}
        pop = 4
    else:
        lines.append("call %08x %08x %08x %08x" % (fn, 0, 0, ITEM if item else 0))
        want = int(m.has_dur(it)) if item and it.type == 4 else 0
        ctl = {"hasdur_no152": int(Model(V, "hasdur_no152").has_dur(it)) if item and it.type == 4 else 0}
        pop = 4
    return lines, {"fn": fn, "want": {"eax": want}, "pop": pop, "ctl": ctl, "br": dict(m.br)}


# ---------------------------------------------------------------------------------------------------- gold
SITE_ADDGOLD = {"neg": 0x0053FF29, "stash": 0x0053FF57, "carried": 0x0053FF74, "add": 0x0053FF88}


def gen_gold(r):
    fn = r.choice([FN_GOLDCAP, FN_STASHCAP, FN_ADDGOLD, FN_ADDGOLD, FN_ADDGOLD])
    u = Unit(PLAYER, PLIST, POWN, ICACHE, ext=r.random() < 0.5)
    u.type = r.choice([0, 0, 0, 1, 4])
    L = r.choice([r.randrange(1, 100), 0, 1, 99, r.randrange(100, 300000), -r.randrange(1, 100), r.getrandbits(32)])
    d = u.cache if u.ext else u.own
    d[ST_LVL << 16] = w32(L)
    if fn == FN_ADDGOLD:
        stat = r.choice([14, 15, 14, 15, 12, 0])
        cur = r.choice([0, r.randrange(0, 3000000), r.randrange(0, 1000000), 2500000, 0x7FFFFFFF])
        d[stat << 16] = cur if stat != 12 else w32(L)
        cap = imul(w32(L), 10000) if stat != 15 else 2500000
        delta = r.choice([r.randrange(-100000, 100000), cap - cur, cap - cur + 1, -cur, -cur - 1,
                          r.randrange(-3000000, 3000000), r.getrandbits(31), -r.getrandbits(31)])
        delta = w32(delta)
        lines = u.lines() + ["call %08x %08x %08x %08x" % (fn, PLAYER, stat, u32(delta))]
        v = w32(w32(d.get(stat << 16, 0)) + delta)
        ctl = {}
        if v < 0:
            want = ("neg", stat, 0)
        elif u.type == 0 and stat == 14 and imul(w32(L), 10000) < v:
            want = ("carried", 14, 0)
        elif u.type == 0 and stat == 15 and 2500000 < v:
            want = ("stash", 15, 0)
        else:
            want = ("add", stat, delta)
        ctl["spec_clamp"] = (want[0], want[1], (imul(w32(L), 10000) if want[0] == "carried" else 2500000))\
            if want[0] in ("carried", "stash") else want
        ctl["no_type_test"] = want
        if u.type != 0 and stat in (14, 15):
            c = imul(w32(L), 10000) if stat == 14 else 2500000
            if want[0] == "add" and c < v:
                ctl["no_type_test"] = ("carried" if stat == 14 else "stash", stat, 0)
        return lines, {"fn": fn, "want": list(want), "ctl": {k: list(x) for k, x in ctl.items()},
                       "br": {"addgold_" + want[0]: 1}}
    lines = u.lines() + ["call %08x %08x %08x %08x" % (fn, 0, 0, PLAYER)]
    if fn == FN_GOLDCAP:
        want = u32(imul(w32(L), 10000))
        ctl = {"cap_100": u32(imul(w32(L), 100))}
        br = {"goldcap": 1}
    else:
        want = 2500000
        ctl = {"stash_by_level": u32(imul(w32(L), 10000))}
        br = {"stashcap": 1}
    return lines, {"fn": fn, "want": want, "ctl": ctl, "br": br}


# ---------------------------------------------------------------------------------------------------- wear
SITE_WEAR = {"timer": 0x00559EF9, "break": 0x00559F3F, "qty": 0x00559F77, "zero": 0x00559FD8, "v0": 0x0055A058}


def lcg(lo, hi):
    v = lo * 0x6AC690C5 + hi
    return v & M32, (v >> 32) & M32


def wear_model(M, it, exp, lo, hi, ctl=None):
    armo, weap = M.is_type(it, T_ARMO), M.is_type(it, T_WEAP)
    if not armo and not weap:
        return ("ret", "notype"), (lo, hi)
    if not M.has_dur(it):
        return ("ret", "nodur"), (lo, hi)
    if armo:
        ch = 10
    elif M.throwable(it):
        if exp == 0 and ctl != "classic_draws":
            return ("ret", "classic"), (lo, hi)
        ch = 10
    else:
        ch = 4
    lo, hi = lcg(lo, hi)
    roll = lo % 100
    if roll >= ch:
        return ("ret", "miss"), (lo, hi)
    D1 = w32(it.getstat(M.V, ST_DUR) - 1)
    if D1 >= 1:
        return ("timer",), (lo, hi)
    if not weap and not it.fl & 0x100 and ctl != "break_any":
        return ("break",), (lo, hi)
    if it.ver & 0xFFFF and ctl != "v0_all":
        q = it.getstat(M.V, ST_QTY)
        if q > 1:
            return ("qty", ST_QTY, w32(q - 1)), (lo, hi)
        return ("zero", ST_DUR, 0), (lo, hi)
    return ("v0", ST_DUR, 0), (lo, hi)


def gen_wear(r):
    V = View(world())
    scen = r.choice([{"base": "armo"}, {"base": "weap"}, {"base": "weap"}, {}, {"base": "armo"}])
    it = gen_item(r, V, dict(scen, want=(ST_DUR, ST_MAXDUR, ST_QTY)))
    it.type = 4
    if r.random() < 0.6:                                      # durability 1 or 0: the D' < 1 branches
        it.cache[ST_DUR << 16] = r.choice([0, 1, 1, -2])
    if r.random() < 0.5:
        it.cache.pop(ST_INDESTR << 16, None)
    exp = r.choice([0, 1, 0x101])
    lo, hi = r.getrandbits(32), r.getrandbits(32)
    if r.random() < 0.7:                                      # a seed whose step rolls below 10
        for _ in range(200):
            if lcg(lo, hi)[0] % 100 < 10:
                break
            lo = r.getrandbits(32)
    M = Model(V)
    want, seed = wear_model(M, it, exp, lo, hi)
    ctl = {c: list(wear_model(Model(V), it, exp, lo, hi, c)[0]) for c in ("classic_draws", "break_any", "v0_all")}
    lines = list(V.lines()) + it.lines()
    lines += [w(GAME + 0x70, le32(exp)), w(OWNER + 0x20, le32(lo) + le32(hi)), "d %08x 8" % (OWNER + 0x20)]
    lines.append("call %08x %08x %08x %08x" % (FN_WEAR, GAME, OWNER, ITEM))
    return lines, {"want": list(want), "seed": list(seed), "ctl": ctl,
                   "br": dict(M.br, **{"wear_" + "_".join(str(x) for x in want[:2]): 1})}


# ---------------------------------------------------------------------------------------------------- timer
EVT = 0x2207A000


def gen_timer(r):
    V = View(world())
    it = gen_item(r, V, {})
    it.type = 4
    rate = r.choice([0, 1, 3, 5, 20, 21, r.randrange(1, 200), r.randrange(200, 5000), -r.randrange(1, 50), 2501, 2500])
    if r.random() < 0.95:
        it.cache[ST_REPDUR << 16] = rate
    else:
        it.cache.pop(ST_REPDUR << 16, None)
        rate = 0
    frame = r.choice([r.randrange(0, 100000), r.getrandbits(31)])
    evs = []
    for _ in range(r.choice([0, 0, 1, 2])):
        evs.append((r.choice([3, 3, 1, 4]), r.choice([0, r.randrange(1, 100000), -r.randrange(1, 100)])))
    lines = list(V.lines()) + it.lines()
    lines.append(w(GAME + 0xA8, le32(frame)))
    lines.append(w(ITEM + 0xDC, le32(EVT if evs else 0)))
    for k, (t, f) in enumerate(evs):
        lines.append(w(EVT + 0x40 * k, bytes([t]) + b"\0\0\0" + le32(f)))
        lines.append(w(EVT + 0x40 * k + 0x24, le32(EVT + 0x40 * (k + 1) if k + 1 < len(evs) else 0)))
    lines.append("call %08x %08x %08x" % (FN_TIMER, GAME, ITEM))
    queued = any(t == 3 and f > 0 for t, f in evs)
    if rate == 0:
        want = ["ret", "rate0"]
    elif queued:
        want = ["ret", "queued"]
    else:
        want = ["queue", 3, u32(w32(tdiv(2500, rate) + 1 + frame))]
    ctl = {"spec_floor125": want if want[0] != "queue" else ["queue", 3, u32(w32(max(125, tdiv(2500, rate) + 1)
                                                                               + frame))],
           "no_plus1": want if want[0] != "queue" else ["queue", 3, u32(w32(tdiv(2500, rate) + frame))]}
    return lines, {"want": want, "ctl": ctl, "br": {"timer_" + str(want[1]) if want[0] == "ret" else
                                                    "timer_queue": 1}}


# ---------------------------------------------------------------------------------------------------- repl
FN_REPL, SITE_REPL = 0x00562D30, 0x00562C7C


def repl_model(M, it, ctl=None):
    if not it.fl & 0x100 and M.has_dur(it):
        Mx = M.max_dur(it)
        if it.getstat(M.V, ST_REPDUR) != 0:
            v = w32(it.getstat(M.V, ST_DUR) + 1)
            if v <= Mx:
                return ["write", ST_DUR, u32(v)]
            if ctl != "atmax_qty":
                return ["ret", "dur_atmax"]
    if M.stackable(it) and ctl != "no_stack_test":
        Ms = M.max_stack(it)
        if it.getstat(M.V, ST_REPQTY) == 0:
            return ["ret", "qty_rate0"]
        v = w32(it.getstat(M.V, ST_QTY) + 1)
        if v <= Ms:
            return ["write", ST_QTY, u32(v)]
        return ["ret", "qty_atmax"]
    return ["ret", "none"]


def gen_repl(r):
    V = View(world())
    it = gen_item(r, V, {"want": (ST_DUR, ST_MAXDUR, ST_REPDUR, ST_REPQTY, ST_QTY)})
    it.type = 4
    if r.random() < 0.4:
        md = it.getstat(V, ST_MAXDUR)
        it.cache[ST_DUR << 16] = r.choice([md, md - 1, md + 1])
    M = Model(V)
    want = repl_model(M, it)
    ctl = {c: repl_model(Model(V), it, c) for c in ("atmax_qty", "no_stack_test")}
    lines = list(V.lines()) + it.lines()
    lines.append("call %08x %08x %08x" % (FN_REPL, GAME, ITEM))
    return lines, {"want": want, "ctl": ctl, "br": dict(M.br, **{"repl_" + str(want[1]): 1})}


GEN = {"price": gen_price, "rep": gen_rep, "gold": gen_gold, "wear": gen_wear, "timer": gen_timer, "repl": gen_repl}


# ================================================================================================= commands
OBSERVE = {"price": (OBS_ERR,), "rep": (), "gold": (OBS_SETSTAT, OBS_ADDSTAT, OBS_ERR),
           "wear": (OBS_SETSTAT, OBS_BREAK, FN_TIMER, OBS_PKT, OBS_ERR), "timer": (OBS_QADD, OBS_ERR),
           "repl": (OBS_SETSTAT, OBS_ERR)}
TABLES = FAMILIES


def cmd_cases(d, limit=None):
    os.makedirs(d, exist_ok=True)
    spec = world().spec_lines(d)
    for fam in FAMILIES:
        rnd = random.Random("n66z-s4e2-%s" % fam)
        cases, meta = [], []
        n = limit or NCASES[fam]
        for _ in range(n):
            lines, a = GEN[fam](rnd)
            cases.extend(lines)
            meta.append(a)
        mem = ["guard %08x" % x for x in GUARDS + ((OBS_ERR,) if OBS_ERR not in OBSERVE[fam] else ())]
        mem += ["observe %08x" % x for x in OBSERVE[fam]]
        if fam in TABLES:
            mem += spec
        E.write_family(d, fam, cases, mem, {"cases": meta})
        print("%s: %d cases, %d lines" % (fam, n, len(cases)))


# image reads the code makes (instruction fetches are not traced): each a constant of a read-only section
RS = [(BITMASK, BITMASK + 0x80, "r", "g_BitMask32 0x006CE268 (.rdata)"),
      (0x0062FD9C, 0x0062FD9C + 36, "r", "the quality jump table 0x0062FD9C (.text)"),
      (0x006292DC, 0x006292DC + 20, "r", "PriceStatTerms' Encode jump table 0x006292DC (.text)")]
NPC_END = NPC + NNPC * NPC_SZ


def observed(fam, c, a):
    """-> the observation in the model's terms."""
    if "stop" in c:
        return ["stop", "%08X" % c["stop"], c.get("msg")]
    if "obs" in c:
        args = c.get("args", (0,) * 16)
        return ["obs", c["obs"], args[0], list(args[1:5]), c["regs"].get("edx"), c["regs"].get("ecx")]
    return ["ret", c["eax"], c["pop"]]


def judge(fam, c, a, ctl=None):
    """-> (ok, got) of one case against the model's prediction (or a control's)."""
    o = observed(fam, c, a)
    want = a["want"] if ctl is None else a["ctl"][ctl]
    if fam == "price":
        if isinstance(want, str) and want.startswith("fatal "):
            want = {"fatal": int(want.split()[1], 16)}
        if "fatal" in (want if isinstance(want, dict) else {}):
            return o[0] == "obs" and o[1] == OBS_ERR and o[3][0] == want["fatal"], o
        exp = want["eax"] if isinstance(want, dict) else want
        if isinstance(exp, str):
            return False, o
        return o[0] == "ret" and o[1] == exp and o[2] == 16, o
    if fam == "rep":
        exp = want["eax"] if isinstance(want, dict) else want
        return o[0] == "ret" and o[1] == exp and o[2] == a["pop"], o
    if fam == "gold":
        if a["fn"] != FN_ADDGOLD:
            return o[0] == "ret" and o[1] == want and o[2] == 4, o
        kind, stat, val = want
        tgt = OBS_ADDSTAT if kind == "add" else OBS_SETSTAT
        return (o[0] == "obs" and o[1] == tgt and o[2] == SITE_ADDGOLD[kind]
                and o[3] == [PLAYER, stat, u32(val), 0]), o
    if fam == "wear":
        seed = list(struct.unpack("<II", c["dumps"].get(OWNER + 0x20, b"\0" * 8)))
        if ctl is None and seed != a["seed"]:
            return False, o + ["seed", seed]
        k = want[0]
        if k == "ret":
            return o[0] == "ret", o
        if o[0] != "obs" or o[2] != SITE_WEAR[k]:
            return False, o
        if k == "timer":
            return o[1] == FN_TIMER and o[4] == ITEM and o[5] == GAME, o
        if k == "break":
            return o[1] == OBS_BREAK and o[3][0] == ITEM and o[4] == OWNER, o
        return o[1] == OBS_SETSTAT and o[3] == [ITEM, want[1], u32(want[2]), 0], o
    if fam == "timer":
        if want[0] == "ret":
            return o[0] == "ret", o
        return o[0] == "obs" and o[1] == OBS_QADD and o[3][:4] == [3, want[2], 0, 0] and o[4] == ITEM, o
    if fam == "repl":
        if want[0] == "ret":
            return o[0] == "ret", o
        return (o[0] == "obs" and o[1] == OBS_SETSTAT and o[2] == SITE_REPL
                and o[3] == [ITEM, want[1], want[2], 0]), o
    raise ValueError(fam)


def obsform(fam, x):
    """What a case can show of a prediction: a return's reason is not observable in wear, timer and repl."""
    if fam in ("wear", "timer", "repl") and isinstance(x, list) and x and x[0] == "ret":
        return ["ret"]
    if isinstance(x, dict):
        return x.get("eax", "fatal %X" % x.get("fatal", 0))
    return x


class Report(E.Report):
    def line(self):
        keys = ["cases", "match", "bad", "neg", "traced", "undeclared", "stopped"]
        rest = sorted(k for k in self.c if k not in keys)
        return "S4E2 %s " % self.fam + " ".join("%s=%d" % (k, self.c[k]) for k in keys + rest)


def cmd_check(d, fams=FAMILIES):
    rc = 0
    for fam in fams:
        p = os.path.join(d, fam + ".out")
        if not os.path.exists(p):
            print("S4E2 %s: no output" % fam)
            rc = 1
            continue
        calls, reads, writes = read_out(p)
        meta = json.load(open(os.path.join(d, fam + ".json")))["cases"]
        rep = Report(fam)
        sep, passed = collections.Counter(), collections.Counter()
        sites = collections.Counter()
        if len(calls) != len(meta):
            rep.bad("%d calls for %d cases" % (len(calls), len(meta)))
        d3_last = 0
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
            rep.branches.update(a["br"])
            if fam == "price" and a.get("last_npc_d3") and a["br"].get("npc_step"):
                d3_last += 1
            if fam == "price" and "fatal" in a["want"]:
                rep.c["fatal_%X" % a["want"]["fatal"]] += 1
            for k, v in a["ctl"].items():
                if obsform(fam, v) != obsform(fam, a["want"]):
                    sep[k] += 1
                    passed[k] += judge(fam, c, a, k)[0]
        declared = list(RS)
        if fam == "price":
            declared.append((NPC_END, NPC_END + 4, "r", "max buy [3] of the last Npc record: the dword past the table "
                                                       "(Npc +0x4C, d = 3), read and not used in mode 0"))
            npc_end = [x for x in reads if x[1] == NPC_END]
            rep.c["d3_last_reads"] = sum(x[3] for x in npc_end)
            rep.c["d3_last_cases"] = d3_last
            rep.notes.append("  reads of 0x%08X (max buy [3] past the table): %s" % (NPC_END, npc_end))
        E.account(rep, reads, writes, declared)
        for k in sorted(sites):
            rep.notes.append("  boundary %s: %d" % (k, sites[k]))
        for k in sorted(set(sep) | set(k for a in meta for k in a["ctl"])):
            rep.notes.append("  control %s: sep=%d passed=%d" % (k, sep[k], passed[k]))
            if passed[k]:
                rep.bad("control %s passed %d" % (k, passed[k]))
        rc |= E.finish(rep, sum(sep.values()))
    return rc


PINS = [  # (va, mnemonic, operand substring): the instructions the record cites (ADR-0015 (5))
    (0x0062EFD1, "cmp", "eax,0x4"), (0x0062F052, "cmp", "esi,0x63"), (0x0062F058, "jl", ""),
    (0x0062F06E, "cmp", "ax,0x1"), (0x0062FAA2, "push", "0xcdc"), (0x0062FAAF, "cmp", "edx,0xffff"),
    (0x0062FAE5, "cmp", "edi,0xffff"), (0x0062FAF0, "test", "ecx,ecx"), (0x0062FCE6, "mov", "edx,0x2710"),
    (0x0062FCFA, "mov", "+0x40]"), (0x00629450, "sar", "ebx,1"), (0x00629452, "add", "ebx,0x1"),
    (0x00629455, "jns", ""), (0x00623460, "mov", "eax,0x2625a0"), (0x00622E80, "imul", "eax,eax,0x2710"),
    (0x00558561, "idiv", "ebx"), (0x00558569, "lea", "[eax+ecx*1+0x1]"), (0x00559E88, "cmp", "[eax+0x70]"),
    (0x00559EB5, "mul", "ecx"), (0x00559EC2, "cmp", "[ebp+0x8]"), (0x00559F4E, "cmp", "ax,0x1"),
    (0x00562C6C, "jg", ""),
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
    for lo, n, name in ((BITMASK, 0x80, "g_BitMask32"), (0x0062FD9C, 36, "quality jump table"),
                        (0x006292DC, 20, "Encode jump table")):
        sec = S4.section_of(lo)
        fl = [x[5] for x in S4.image()[2] if x[4] == sec][0]
        rep.c["ro"] += not fl & 0x80000000
        rep.notes.append("  %s 0x%08X in %s (writable %s): %s" % (name, lo, sec, bool(fl & 0x80000000),
                                                                 E.img_bytes(lo, n).hex()))
        if fl & 0x80000000:
            rep.bad("%s writable" % name)
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

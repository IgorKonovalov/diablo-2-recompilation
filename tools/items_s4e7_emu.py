#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S4e part 5c (`lane/n66z`): the mercenary button's request, ItemUse after its test and use
entries, and ItemSkillQtyAdjust, run on the pinned Game.exe under Ghidra's p-code emulator (ADR-0015, ADR-0021) with
re/ghidra_scripts/EmuBoundary.java, compared with the models below; plus `sites`, the static route read that sends a
row to the harness (ADR-0029, ruling R2) when its route crosses an allocator or an import. Parts 1 to 5b
(tools/stats_s4e_emu.py, items_s4e_emu.py to items_s4e6_emu.py, run/ to run6/) stay unchanged; this tool builds its
cases on tools/items_s4e3_emu.py's world (merc), tools/use_emu.py's world with items_s4e6_emu.py's kind-3 cases (c2)
and tools/use_emu.py's world (qty), all unchanged.

    python3 -I tools/items_s4e7_emu.py cases [--dir D] [--limit N]   write D/<family>.cases, .mem, .json
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/items_s4e7_emu.py check [--dir D]               compare, account every traced access, controls
    python3 -I tools/items_s4e7_emu.py static                        objdump pins
    python3 -I tools/items_s4e7_emu.py sites                         the routes: first allocator or import per call
    python3 -I tools/items_s4e7_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66z/s4e/run7. Every draw comes from random.Random("n66z-s4e7-<family>").

Families (function, convention; boundaries; rows):
  merc  Pkt61MercItem 0x0054D430 (ECX game, EDX player; packet, length): to the return, MercGiveCursorItem 0x0054D230
        or 0x0054D130 (observed). Every callee before them runs emulated: PlayerIsBusy, InteractIsPlayer,
        UNIT_GetUsedSkill, UnitIsDead, PETS_GetUnitOfType (PlayerGetData, GameFindUnit), 0x0065A590 (UnitGetRoom, the
        room's near list), INV_GetCursorItem, ItemBaseIsQuest (ItemsGetRecord).                    items/use 21
  c2    ItemUse 0x005BF240 (ECX game, EDX user; item, arg2, x, y) with the stock entries run emulated: kind 1's test
        0x005BE130 on a book or scroll whose Books row is absent or present, and kind 3's use 0x005BE3F0 on
        items_s4e6_emu.py's `potret` worlds: to the return, InvClearUseMark 0x005BE1C0, SendUnitPacket6 0x0053B3D0, the
        test's message 0x0053D220, kind 1's use 0x005BE230, or kind 3's callees (observed).          items/use 22
  qty   ItemSkillQtyAdjust 0x0055C110 (EAX item, EDI unit; add) and ItemSkillQtyAdd 0x0055C270 (ECX unit, EDX item):
        to the return, the message builder 0x005531C0, UnitAddStat 0x006272B0, 0x00570080 or the error routine
        0x00408090 (observed).                                                     items/inventory 26, 27 (and 25)

Controls: each a wrong reading (the spec's where it differs); `sep` counts the cases a control's prediction differs
from the model's, `passed` those where the emulator still equals the control (must be 0 when sep > 0).
Stdlib only, plus objdump for `static` and `sites`.
"""
import argparse
import collections
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
import use_emu as U  # noqa: E402
import items_s4e3_emu as P3  # noqa: E402
import items_s4e6_emu as P6  # noqa: E402
from anim_s6f_emu import read_out  # noqa: E402

M32 = 0xFFFFFFFF
DEFDIR = os.path.join(ROOT, "workspace", "logs", "n66z", "s4e", "run7")
FAMILIES = ("merc", "c2", "qty")
NCASES = {"merc": 3000, "c2": 2500, "qty": 2500}
GUARDS = (0x00408A60, 0x00681E09, 0x0040B4B0, 0x0040B430, 0x0040B480)
F_FATAL = 0x00408090

# ---------------------------------------------------------------------------------------------------------- merc
F_MERC, B_GIVE, B_OTHER = 0x0054D430, 0x0054D230, 0x0054D130
DTBL2, PETL, RECS2 = 0x23060000, 0x23061000, 0x23070000
SKB = P3.OTHERS[3]                       # the player's used-skill block: [+0x10] the skill
PET = P3.OTHERS[1]
PARTNER = P3.OTHERS[0]
ROOMS = [P3.ROOM, P3.ROOM + 0x100, P3.ROOM + 0x200]
NEAR = P3.ROOM + 0x300                    # each room's near array at NEAR + 0x20·k
MERC_ZERO = [(DTBL2, 0x1000), (PETL, 0x400), (RECS2, 0x2000)]
NROWS = 16


def unit_dead(typ, mode, flag):
    """UnitIsDead 0x005541B0: the +0xC6 bit 0; a player in mode 0 or 17, a monster in mode 0 or 12; other types dead."""
    if flag & 1:
        return 1
    if typ == 0:
        return int(mode in (0, 0x11))
    if typ == 1:
        return int(mode in (0, 0xC))
    return 1


def model_merc(w, m, ctl=None):
    if (m["length"] != 3 and ctl != "len_ignored") or (not m["exp"] and ctl != "exp_ignored"):
        return ["ret", 3, 8]
    busy = P3.is_busy(w)
    if busy and P3.interact_is_player(w) and ctl != "iip_ignored":
        return ["ret", 3, 8]
    used = m["skill"] if m["skb"] else 0
    if (m["skb"] != 0) if ctl == "skill_any" else used:
        return ["ret", 0, 8]
    if unit_dead(0, m["pmode"], m["pflag"]) and ctl != "pdead_ignored":
        return ["ret", 0, 8]
    pet = 0
    if m["ptypes"] > 7 and m["entry"]:
        for fl, g in m["nodes"]:
            if ctl == "pet_first" or not fl & 1:
                pet = w.find(1, g)
                break
    if not pet:
        return ["ret", 0, 8]
    if unit_dead(1, m["petmode"], m["petflag"]) and ctl != "petdead_ignored":
        return ["ret", 0, 8]
    if ctl != "spec_noroom":
        pr, qr = m["proom"], m["petroom"]
        if not pr or not qr or qr not in m["near"].get(str(pr), []):
            return ["ret", 0, 8]
    if not m["inv"]:
        return ["ret", 3, 8]
    cur = w.cursor(P3.INVB)
    if not cur:
        if m["u16"] == 0:
            return ["ret", 0, 8]
        return ["obs", B_OTHER, 0x0054D4EE, {"ebx": P3.GAME}, [P3.PLAYER, m["u16"]]]
    if m["quest"] and ctl != "quest_ignored":
        return ["ret", 0, 8]
    return ["obs", B_GIVE, 0x0054D50F, {"eax": cur, "ecx": PET}, [P3.GAME, P3.PLAYER]]


def gen_merc(r, i):
    w = P3.W()
    w.pd = collections.defaultdict(dict)
    m = {}
    # the interaction partner (a player, hashed) for InteractIsPlayer
    pg = r.randrange(1, 0x400)
    w.unit(PARTNER, 0, pg, data=PARTNER + 0x200)
    iflag = r.choice([0, 0, 0, 0, 0, 1])
    iid = r.choice([pg, pg, r.randrange(1, 0x400)])
    ity = r.choice([0, 0, 1])
    m["pmode"] = r.choice([1, 1, 1, 1, 1, 1, 2, 3, 0, 0x11])
    m["pflag"] = r.choice([0] * 9 + [1, 2])
    P3.put_player(w, r, 0, iflag=iflag, iid=iid, itype=ity, mode=m["pmode"])
    w.c.d8(P3.PLAYER + 0xC6, m["pflag"])
    w.pd[P3.PLAYER][0x4C] = r.choice([0, 0, 0, 1])
    w.c.d32(P3.PDATA + 0x4C, w.pd[P3.PLAYER][0x4C])
    # the used skill
    m["skb"] = SKB if r.random() < 0.6 else 0
    m["skill"] = r.choice([0] * 7 + [1, 2, 0x3F]) if m["skb"] else 0
    w.c.d32(P3.PLAYER + 0xA8, m["skb"])
    if m["skb"]:
        w.c.d32(SKB + 0x10, m["skill"])
    # pets: pdata +0x44 -> list; [list] the array; type 7's entry its first node; node +0 flags, +4 guid, +0x14 next
    m["ptypes"] = r.choice([8] * 8 + [9, 12, 7, 3])
    w.c.d32(DTBL2 + 0xBF0, m["ptypes"])
    petg = r.randrange(0x400, 0x800)
    m["petmode"] = r.choice([1] * 7 + [2, 3, 0, 0xC])
    m["petflag"] = r.choice([0] * 9 + [1])
    pet_hashed = r.random() > 0.05
    w.unit(PET, 1, petg, hashed=pet_hashed, path=PET + 0x300, mode=m["petmode"])
    w.c.d8(PET + 0xC6, m["petflag"])
    nodes = []
    m["entry"] = int(r.random() > 0.05)
    has_list = r.random() > 0.03
    w.c.d32(P3.PDATA + 0x44, PETL if has_list else 0)
    if has_list:
        w.c.d32(PETL, PETL + 0x10)
    else:
        m["entry"] = 0
    if m["entry"]:
        n = r.choice([1, 1, 1, 2, 3])
        gl = [r.choice([petg, petg, petg, r.randrange(0x800, 0xA00)]) for _ in range(n)]
        for k in range(n):
            fl = r.choice([0, 0, 0, 0, 1, 2, 3])
            nodes.append((fl, gl[k]))
            a = PETL + 0x100 + 0x20 * k
            w.c.d32(a, fl)
            w.c.d32(a + 4, gl[k])
            w.c.d32(a + 0x14, a + 0x20 if k + 1 < n else 0)
        w.c.d32(PETL + 0x10 + 12 * 7, PETL + 0x100)
    m["nodes"] = nodes
    # rooms: player and pet path +0x1C; near list [room] array, [room+0x24] count
    m["proom"] = r.choice(ROOMS + [ROOMS[0]] * 3 + [0])
    m["petroom"] = r.choice(ROOMS + [m["proom"]] * 6 + [0])
    w.c.d32(P3.PPATH + 0x1C, m["proom"])
    w.c.d32(PET + 0x300 + 0x1C, m["petroom"])
    near = {}
    for k, rm in enumerate(ROOMS):
        lst = r.sample(ROOMS, r.randrange(0, 4))
        if r.random() < 0.85 and rm not in lst:
            lst.append(rm)
        cnt = len(lst) if r.random() > 0.05 else r.choice([0, -1 & M32])
        arr = NEAR + 0x20 * k
        w.c.d32(rm, arr)
        w.c.d32(rm + 0x24, cnt)
        for j, x in enumerate(lst):
            w.c.d32(arr + 4 * j, x)
        near[str(rm)] = lst if cnt == len(lst) else []
    m["near"] = near
    # inventory, cursor item and its record's quest byte
    m["inv"] = int(r.random() > 0.04)
    gs = P3.guids(r, 2)
    row = r.randrange(NROWS)
    it = P3.put_item(w, 0, gs[0], 4, P3.INVB)
    w.c.d32(it + 4, row)
    m["quest"] = r.choice([0] * 6 + [1, 2, 0x80])
    w.c.d8(RECS2 + row * 0x1A8 + 0x12A, m["quest"])
    cur = it if r.random() < 0.7 else 0
    P3.put_inv(w, cursor=cur)
    if not m["inv"]:
        w.c.d32(P3.PLAYER + 0x60, 0)
        w.inv = {}
    w.finish()
    m["exp"] = r.choice([1, 1, 1, 1, 0, 2])
    w.c.d32(P3.GAME + 0x70, m["exp"])
    m["length"] = 3 if r.random() < 0.93 else r.choice([0, 1, 2, 4, 5, 9])
    m["u16"] = r.choice([0, 0, 1, r.randrange(1, 0x10000)])
    hi = r.getrandbits(16)
    w.c.put(P3.PKT, bytes([0x61]) + struct.pack("<HH", m["u16"], hi))
    m["want"] = model_merc(w, m)
    m["ctl"] = {k: model_merc(w, m, k) for k in ("iip_ignored", "skill_any", "pet_first", "spec_noroom", "quest_ignored",
                                                  "len_ignored", "exp_ignored", "pdead_ignored", "petdead_ignored")}
    want = m["want"]
    m["br"] = {"merc_%s" % (("ret%d" % want[1]) if want[0] == "ret" else "%08X" % want[1]): 1}
    return w.c.call(F_MERC, P3.GAME, P3.PLAYER, P3.PKT, m["length"]), m


# ---------------------------------------------------------------------------------------------------------- c2
F_USE, B_CLEAR, B_SEND6, B_TESTMSG, B_ID1 = 0x005BF240, 0x005BE1C0, 0x0053B3D0, 0x0053D220, 0x005BE230
POT_OBS = (U.F_ADD, U.F_ALLOC, U.F_QUEUE, U.F_SET, U.F_GHEAL)


def model_c2(m, ctl=None):
    if m["kind"] == "test":
        if m["flag4"]:
            return ["obs", B_ID1, 0x005BF38A, {}, []]
        if m["books"]:
            return ["obs", B_TESTMSG, 0x005BE16E, {}, []]
        if ctl == "clear_on_test":
            return ["obs", B_CLEAR, 0x005BF329, {}, []]
        return ["ret", 0, 16]
    pw = m["pot"]
    if pw[0] == "ret":
        if pw[1] == 0:
            if ctl == "no_clear":
                return ["ret", 0, 16]
            return ["obs", B_CLEAR, 0x005BF395, {}, []]
        if ctl == "use_ret0":
            return ["ret", 0, 16]
        return ["ret", pw[1], 16]
    return ["pot"] + pw[1:]


def gen_c2(r, i):
    if r.random() < 0.3:
        c = U.Case()
        utype = r.choice((0, 0, 1))
        c.d32(U.USER, utype)
        c.d32(U.USER + 0x14, U.UDATA)
        row = r.randrange(150)
        flag4 = r.random() < 0.25
        U.put_item(c, U.ITEM, U.IDATA, row, flags=(4 if flag4 else 0) | (r.getrandbits(32) & ~4))
        U.put_types(c, {row: [r.choice((18, 22))]})
        for k in range(3):
            c.put(U.BOOKS + 0x20 * k, bytes(0x20))
        missing = r.random() < 0.65
        suffix = 3 + r.randrange(0, 6) if missing else r.randrange(0, 3)
        c.d16(U.IDATA + 0x3E, suffix)
        if not missing:
            c.d32(U.BOOKS + suffix * 0x20 + 4, r.choice((0, -1, 1)))
            c.d8(U.BOOKS + suffix * 0x20 + 2, r.randrange(0, 256))
        c.d32(U.RECS + row * 0x1A8 + 0x94, 1)
        c.dump(U.IDATA + 0x18, 4)
        m = dict(kind="test", flag4=int(flag4), books=int(not missing), utype=utype)
        call = c.call(F_USE, U.GAME, U.USER, U.ITEM, r.getrandbits(32), r.getrandbits(16), r.getrandbits(16))
    else:
        while True:
            line, pm = P6.gen_potret(r, i)
            if pm["mode"] != "norec":
                break
        lines = line.split("\n")
        row = [int(x.split()[2][:8], 16) for x in lines if x.startswith("w %08x " % (U.ITEM + 4))][-1]
        row = struct.unpack("<I", struct.pack(">I", row))[0]
        c = U.Case()
        U.put_types(c, {row: [9]})
        c.d32(U.ITEM + 0x14, U.IDATA)
        c.d32(U.IDATA + 0x18, r.getrandbits(32) & ~4)
        c.d32(U.RECS + row * 0x1A8 + 0x94, 3)
        call = "\n".join(lines[:-1] + c.lines + ["d %08x 4" % (U.IDATA + 0x18), "call %08x %08x %08x %08x 00000000 00000000 00000000" % (
            F_USE, U.GAME, U.USER, U.ITEM)])
        m = dict(kind="use", mode=pm["mode"], pot=pm["want"], utype=pm["u"]["type"])
    m["want"] = model_c2(m)
    m["ctl"] = {k: model_c2(m, k) for k in ("clear_on_test", "no_clear", "use_ret0")}
    w = m["want"]
    m["br"] = {"c2_%s_%s" % (m["kind"], ("ret%d" % w[1]) if w[0] == "ret" else ("%08X" % w[1])): 1}
    return call, m


# ---------------------------------------------------------------------------------------------------------- qty
F_ADJ, F_QADD, B_MSG, B_ADDSTAT, B_GRANT = 0x0055C110, 0x0055C270, 0x005531C0, 0x006272B0, 0x00570080
SKLIST = 0x101C0000
QTY_ZERO = [(SKLIST, 0x400), (U.BOOKS, 0x60), (U.ITSL, 0x200)]


def model_qty(m, ctl=None):
    if m["entry"] == "add" and m["utype"] != 0:
        return ["ret", U.ITEM, 0]
    add = 1 if m["entry"] == "add" else m["add"]
    t = m["types"]
    bk = m["book"]
    skill = -1
    if bk is not None and (22 in t or 18 in t):
        if 22 in t:
            skill = bk[1] if ctl == "swap_books" else bk[0]
        else:
            skill = bk[0] if ctl == "swap_books" else bk[1]
    skill = U.inv.i32(skill & M32)
    if skill == -1:
        return ["ret", 0, 4 if m["entry"] == "adj" else 0]
    if ctl == "page4_nothing" and m["page"] == 4:
        return ["ret", 0, 4 if m["entry"] == "adj" else 0]
    q = m["s70"]
    if q == 0:
        if 18 in t and ctl != "tome0_adds0":
            return ["ret", 0, 4 if m["entry"] == "adj" else 0]
        q = 1 if 18 not in t and ctl != "nontome0_zero" else 0
    elif ctl == "spec_max":
        q = max(q, 1)
    have = None
    for sid, owner, qty in m["skills"]:
        if U.inv.i32(sid) == skill and owner == M32:
            have = qty
            break
    if add:
        if have is None:
            return ["obs", B_ADDSTAT, 0x0055C17B, {}, [U.USER, 5, q & M32, 0]]
        n = U.inv.i32(have + q)
    else:
        if have is None:
            return ["obs", F_FATAL, 0x0055C1A2, {}, [0x230]]
        n = U.inv.i32(have - q)
        if n < 0 and ctl != "noclamp":
            n = 0
    return ["obs", B_MSG, 0x0055C211, {"ecx": U.USER, "edx": 0x006E1164}, [0x234, m["uid"], skill & M32, n & M32]]


def gen_qty(r, i):
    c = U.Case()
    m = {}
    m["entry"] = "adj" if r.random() < 0.8 else "add"
    m["utype"] = 0 if m["entry"] == "adj" or r.random() < 0.7 else r.choice((1, 2, 3))
    m["uid"] = r.randrange(1, 1 << 30)
    c.d32(U.USER, m["utype"])
    c.d32(U.USER + 0xC, m["uid"])
    row = r.randrange(150)
    m["types"] = r.choice(([22], [18], [22], [18], [9], [22, 18]))
    m["s70"] = r.choice((0, 0, 1, 2, 5, 20, 40, 99, r.randrange(1, 300), -3))
    U.put_item(c, U.ITEM, U.IDATA, row, sl=U.ITSL, stats={70: m["s70"]} if m["s70"] or r.random() < 0.5 else {})
    U.put_types(c, {row: m["types"]})
    m["page"] = r.choice((0, 0, 1, 2, 3, 4, 4, 0xFF))
    c.d8(U.IDATA + 0x45, m["page"])
    for k in range(3):
        c.put(U.BOOKS + 0x20 * k, bytes(0x20))
    missing = r.random() < 0.08
    suffix = r.choice((3, 5)) if missing else r.randrange(0, 3)
    c.d16(U.IDATA + 0x3E, suffix)
    sk = (r.choice((217, 218, 219, 220, 1, -1 & M32)), r.choice((217, 218, 219, 220, 2, -1 & M32)))
    if not missing:
        c.d32(U.BOOKS + suffix * 0x20 + 8, sk[0])
        c.d32(U.BOOKS + suffix * 0x20 + 0xC, sk[1])
    m["book"] = None if missing else sk
    # the unit's skill list: +0xA8 -> list; [list+4] the first node: [+0] record (u16 id), +4 next, +0x30 qty, +0x34 owner
    skills = []
    if r.random() > 0.05:
        c.d32(U.USER + 0xA8, SKLIST)
        ids = r.sample([217, 218, 219, 220, 1, 2, 3, 4], r.randrange(0, 5))
        for k, sid in enumerate(ids):
            a = SKLIST + 0x40 + 0x60 * k
            owner = M32 if r.random() > 0.1 else 0
            qty = r.choice((0, 1, 5, 20, r.randrange(0, 200)))
            skills.append((sid, owner, qty))
            c.d32(a, a + 0x50)
            c.d16(a + 0x50, sid)
            c.d32(a + 4, a + 0x60 if k + 1 < len(ids) else 0)
            c.d32(a + 0x30, qty)
            c.d32(a + 0x34, owner)
        c.d32(SKLIST + 4, SKLIST + 0x40 if ids else 0)
    m["skills"] = skills
    m["add"] = r.choice((0, 1, 1, 2, r.getrandbits(32)))
    m["want"] = model_qty(m)
    m["ctl"] = {k: model_qty(m, k) for k in ("swap_books", "page4_nothing", "tome0_adds0", "spec_max", "noclamp",
                                              "nontome0_zero")}
    w = m["want"]
    m["br"] = {"qty_%s_%s" % (m["entry"], ("ret%d" % (w[1] & 0xFF)) if w[0] == "ret" else "%08X" % w[1]): 1}
    if m["entry"] == "adj":
        c.lines += ["r eax %08x" % U.ITEM, "r edi %08x" % U.USER]
        return c.call(F_ADJ, 0, 0, m["add"]), m
    return c.call(F_QADD, U.USER, U.ITEM), m


GEN = {"merc": gen_merc, "c2": gen_c2, "qty": gen_qty}
OBSERVE = {"merc": (B_GIVE, B_OTHER, F_FATAL), "c2": (B_CLEAR, B_SEND6, B_TESTMSG, B_ID1, F_FATAL) + POT_OBS,
           "qty": (B_MSG, B_ADDSTAT, B_GRANT, F_FATAL)}


def mem_spec(fam):
    if fam == "merc":
        out = ["# plan 0066 S4e part 5c (merc): items_s4e3_emu.py's scratch world, the tables below zero-filled"]
        out += [x for x in P3.mem_spec("pos") if not x.startswith(("#", "observe", "guard"))]
        for lo, n in MERC_ZERO:
            out.append("bytes %08x %s" % (lo, "00" * n))
        out += ["dword 00744304 %08x" % DTBL2, "dword 0096ca58 %08x" % NROWS, "dword 0096ca5c %08x" % RECS2]
    else:
        out = ["# plan 0066 S4e part 5c (%s): use_emu.py's world" % fam]
        out += [x for x in P6.mem_spec("potret").splitlines() if not x.startswith(("#", "observe", "guard"))]
        if fam == "qty":
            for lo, n in QTY_ZERO:
                out.append("bytes %08x %s" % (lo, "00" * n))
    out += ["guard %08x" % g for g in GUARDS]
    out += ["observe %08x" % a for a in OBSERVE[fam]]
    return out


def cmd_cases(d, limit=None):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        r = random.Random("n66z-s4e7-%s" % fam)
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
        return ["ret", c.get("eax"), c.get("pop")]
    return ["obs", c["obs"], c["args"][0]]


def judge(c, want):
    g = got_of(c)
    if want[0] == "ret":
        return g == want, g
    if g[0] != "obs":
        return False, g
    args = c["args"]
    if want[0] == "pot":                     # kind 3's boundary in items_s4e6_emu.py's form
        pc = c["obs"]
        if pc != want[1]:
            return False, g
        if pc == U.F_GHEAL:
            return [pc, c["regs"]["eax"]] == want[1:], g + [c["regs"]["eax"]]
        if pc in (U.F_ADD, U.F_SET):
            return [pc, args[2], args[3]] == want[1:], g + [args[2], args[3]]
        if pc == U.F_ALLOC:
            return [pc, args[3]] == want[1:], g + [args[3]]
        return [pc, args[2]] == want[1:], g + [args[2]]
    if c["obs"] != want[1] or args[0] != want[2]:
        return False, g
    if any(c["regs"].get(k) != v for k, v in want[3].items()):
        return False, g + [c["regs"]]
    for k, v in enumerate(want[4]):
        if v is not None and args[1 + k] != v & M32:
            return False, g + [list(args[1:1 + len(want[4])])]
    return True, g


def form(x):
    return json.dumps(x, sort_keys=True)


RS = [(0x006E10E0, 0x006E10F4, "r", "GameFindUnit's head offsets 0x006E10E0 (.rdata)"),
      (0x005541E0, 0x005541F0, "r", "UnitIsDead (.text)"),
      (0x00741790, 0x00741890, "r", "g_ItemUseFns and its count 0x0074178C (.data)"),
      (0x0074178C, 0x00741790, "r", "the use table's count (.data)"),
      (0x00749DE0, 0x00749DE4, "r", "the stack cookie (.data)")]


def declared():
    out = list(RS)
    for lo, hi, why in P6.ACCOUNTED:
        out.append((lo, hi, "r", why))
    for lo, hi, why in P6.IE2.ACCOUNTED:
        out.append((lo, hi, "r", why))
    return out


class Report(E.Report):
    def line(self):
        keys = ["cases", "match", "bad", "neg", "traced", "undeclared", "stopped"]
        rest = sorted(k for k in self.c if k not in keys)
        return "S4E7 %s " % self.fam + " ".join("%s=%d" % (k, self.c[k]) for k in keys + rest)


def cmd_check(d, fams=FAMILIES):
    rc = 0
    for fam in fams:
        p = os.path.join(d, fam + ".out")
        if not os.path.exists(p):
            print("S4E7 %s: no output" % fam)
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
            ok, got = judge(c, a["want"])
            if ok and fam == "c2" and a["kind"] == "use" or ok and fam == "c2" and not a["flag4"] and not a.get("books"):
                fl = c["dumps"].get(U.IDATA + 0x18, b"")
                if len(fl) != 4 or not struct.unpack("<I", fl)[0] & 4:
                    ok, got = False, got + ["flag 4 clear"]
                else:
                    rep.c["flag4_set_before_use_or_test"] += 1
            rep.c["match"] += ok
            if not ok:
                rep.bad("case %d: got %s want %s" % (c["n"], got, a["want"]))
                continue
            rep.branches.update(a["br"])
            if fam == "c2" and a["kind"] == "use":
                outs["use %s -> %s" % (a["mode"], form(a["want"][:2]))] += 1
            else:
                outs[form(a["want"][:2])] += 1
            for k, v in a["ctl"].items():
                if form(v) != form(a["want"]):
                    sep[k] += 1
                    passed[k] += judge(c, v)[0]
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
    (0x0054D434, "cmp", "DWORD PTR [ebp+0xc],0x3"), (0x0054D450, "cmp", "DWORD PTR [esi+0x70],0x0"),
    (0x0054D462, "call", "0x535060"), (0x0054D471, "call", "0x5678a0"), (0x0054D47B, "call", "0x620250"),
    (0x0054D490, "call", "0x5541b0"), (0x0054D49A, "push", "0x7"), (0x0054D4A0, "call", "0x574ec0"),
    (0x0054D4AD, "call", "0x5541b0"), (0x0054D4B8, "call", "0x65a590"), (0x0054D4C1, "mov", "eax,DWORD PTR [edi+0x60]"),
    (0x0054D4CE, "call", "0x63c1e0"), (0x0054D4E9, "call", "0x54d130"), (0x0054D4F8, "call", "0x628cd0"),
    (0x0054D50A, "call", "0x54d230"), (0x00628D19, "movzx", "BYTE PTR [eax+0x12a]"),
    (0x0065A5F5, "cmp", "DWORD PTR [edx+eax*4],edi"), (0x00574F05, "test", "BYTE PTR [eax],0x1"),
    (0x005BF31E, "call", "eax"), (0x005BF324, "call", "0x5be1c0"), (0x005BF341, "mov", "dl,0x7c"),
    (0x005BF345, "call", "0x53b3d0"), (0x005BF388, "call", "eax"), (0x005BF390, "call", "0x5be1c0"),
    (0x005BF3B1, "call", "0x53b3d0"), (0x005BF3B6, "mov", "eax,edi"), (0x005BE14C, "jl", "0x5be16e"),
    (0x005BE16F, "mov", "eax,0x1"), (0x0053B3EE, "call", "0x53b280"), (0x0053B2DD, "call", "0x40b430"),
    (0x0055C121, "cmp", "ebx,0xffffffff"), (0x0055C13E, "push", "0x12"), (0x0055C14E, "mov", "DWORD PTR [ebp-0x4],0x1"),
    (0x0055C176, "call", "0x6272b0"), (0x0055C182, "call", "0x570080"), (0x0055C1D7, "jns", "0x55c1db"),
    (0x0055C1DD, "call", "0x645120"), (0x0055C20C, "call", "0x5531c0"), (0x0055C216, "call", "0x53c520"),
    (0x0055C2A0, "cmp", "DWORD PTR [ecx],0x0"),
    (0x0063AB93, "call", "0x629ed0"), (0x0063ABA4, "call", "0x6277f0"), (0x00627802, "call", "0x6269f0"),
    (0x00626B24, "call", "0x6266c0"), (0x00626BE7, "call", "eax"), (0x0063B133, "call", "0x63aaf0"),
    (0x0063B26E, "call", "0x63aaf0"), (0x0054D628, "call", "0x63ad90"),
]


def cmd_static():
    ok = 0
    for va, mn, sub in PINS:
        out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % va,
                              "--stop-address=0x%x" % (va + 16), S4.EXE], capture_output=True, text=True).stdout
        line = [ln for ln in out.splitlines() if ln.strip().startswith("%x:" % va)]
        txt = line[0].split(":", 1)[1].strip() if line else ""
        good = bool(line) and txt.startswith(mn) and sub in txt
        ok += good
        print("  %s 0x%08X %s" % ("ok " if good else "BAD", va, txt))
    print("S4E7 static pins=%d ok=%d" % (len(PINS), ok))
    return 0 if ok == len(PINS) else 1


# ---------------------------------------------------------------------------------------------------------- sites
ALLOC = {0x0040B430: "pool alloc 0x0040B430", 0x0040B4B0: "pool 0x0040B4B0", 0x0040B480: "pool 0x0040B480"}
FATAL = {0x00408090, 0x00408A60, 0x00681E09, 0x006889D6}     # the error routine, its import calls, the cookie report
IMP = re.compile(r"ds:0x6c[cd][0-9a-f]{3}\b")
SITE_ROOTS = [  # (root, rows)
    (0x0054D430, "use 21: Pkt61MercItem"), (0x0054D230, "use 21: MercGiveCursorItem"), (0x0054D130, "use 21: 0x0054D130"),
    (0x005BF240, "use 22: ItemUse"), (0x005BE130, "use 22: kind 1's test"), (0x006272B0, "use 34: UnitAddStat"),
    (0x00627150, "use 34: STATLIST_SetStat"), (0x0055E170, "use 54: PlayerUseInvItem"),
    (0x00562390, "use 54: PlayerUseBeltItem"), (0x0063AFD0, "inventory 20: InvGridPut"),
    (0x0063AAF0, "inventory 20, 39, 42, 45: InvItemRemove"), (0x0063B210, "inventory 45/99: InvPlaceSocketed"),
    (0x00560200, "inventory 25: InvPlaceItem"), (0x0055C270, "inventory 25: ItemSkillQtyAdd"),
    (0x0055C110, "inventory 26, 27: ItemSkillQtyAdjust"), (0x0055D710, "inventory 67: ItemAutoEquipSlot"),
    (0x0054D520, "inventory 39: the 0x63 handler"), (0x0063AD90, "inventory 39, 42: InvTakeItem"),
    (0x00560420, "inventory 42: InvItemToCursor"),
]


def cmd_sites():
    """Per root, each direct call of its body in address order and the shortest direct-call path from the callee to an
    allocator entry or an import call (the error routine's branches not followed); indirect calls listed."""
    A = S4.asm()
    memo = {}

    def info(e):
        if e not in memo:
            vas, calls, ic = S4.body(A, e)
            memo[e] = (calls, ic, [v for v in ic if IMP.search(A.ins[v][1])])
        return memo[e]

    def path(root):
        prev = {root: None}
        q = collections.deque([root])
        while q:
            e = q.popleft()
            hit = None
            if e in ALLOC:
                hit = ALLOC[e]
            elif info(e)[2]:
                hit = "import %s at 0x%08X" % (A.ins[info(e)[2][0]][1], info(e)[2][0])
            if hit:
                p, x = [], e
                while x is not None:
                    p.append(x)
                    x = prev[x]
                return hit, p[::-1]
            for s, t in sorted(info(e)[0]):
                if t in FATAL or t in prev:
                    continue
                prev[t] = e
                q.append(t)
        return None, len(prev)

    n_routes = 0
    for root, why in SITE_ROOTS:
        calls, ic, imps = info(root)
        print("root 0x%08X (%s): direct calls %d, indirect %d" % (root, why, len(calls), len(ic)))
        for s, t in sorted(calls):
            if t in FATAL:
                print("  0x%08X -> 0x%08X  the error path" % (s, t))
                continue
            hit, p = path(t)
            if hit:
                n_routes += 1
                print("  0x%08X -> 0x%08X  %s via %s" % (s, t, hit, " > ".join("0x%08X" % x for x in p)))
            else:
                print("  0x%08X -> 0x%08X  no allocator or import (%d functions)" % (s, t, p))
        for v in ic:
            print("  indirect 0x%08X %s" % (v, A.ins[v][1]))
    print("S4E7 sites roots=%d calls_reaching=%d" % (len(SITE_ROOTS), n_routes))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["cases", "check", "static", "sites", "manifest"])
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
    return P3.cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

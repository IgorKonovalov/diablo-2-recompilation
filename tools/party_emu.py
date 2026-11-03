#!/usr/bin/env python3
"""Plan 0058 Phase 1 (`lane/r58a`): XP_OnMonsterKill (0x0057E990), XP_PartyShare (0x0057E6C0) and
sub_0057E5A0_PartyXpCollect (0x0057E5A0) run under Ghidra's p-code emulator (ADR-0015, ADR-0021) over generated member
sets for n = 1 to 8 and a ninth member, and compared with tools/player.py's kill_events. No game run, no slot.

    python3 -I tools/party_emu.py cases [--dir D]      write D/<family>.cases and D/<family>.mem, D/xp.bin
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/party_emu.py check [--dir D]      compare every D/<family>.out with the model, account for every
                                                       traced access, run the negative and site controls
    python3 -I tools/party_emu.py static [--dir D]     pin the instruction forms and scan the call sites (D/static.txt)
    python3 -I tools/party_emu.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r58a/emu. Every case draw comes from random.Random("r58a-<family>"), so `cases` regenerates

A case calls XP_OnMonsterKill(ECX game, EDX killer; monster), or XP_PartyShare directly (family `direct`, the null
monster's branch, which the only caller cannot send) on a declared image, field by field: the game's unit hash and party
root, each unit, its path and room chain, its stat lists, the pet table, the Experience table (synthetic: D/xp.bin), the
hire rows. Nothing is patched. Every callee runs emulated, except two observed boundaries (ADR-0021): the fatal path's
first call 0x00408090, and PLAYER_LevelUp 0x00570880. `trace` lines print each XP_Compute (0x0057E480), MERC_AddExp
(0x0057E860) and PLAYER_AddExperience (0x0057E510) entry with its registers, arguments and return address and run on,
and the collector's block (ctx) with the f32 quotient at each share member's XP_Compute.

The claim per case: the whole sequence of those calls (site, every argument), the collector's block, the boundary or
return reached, the bytes popped, and each player's experience and stat 29 after it.

Families: share (n = 1..8, 240 each), edge (the distance edge, the wrap, the ninth member, the party list, the room and
level tests, the wrap of the total), credit (killer, owner, state lists, null and bad units), merc (the mercenary's award
beside the share), direct (null monster, unpartied).

Controls (each must fail every case it separates): le (d2 < 6400), bound (d2 <= 6401), cap (9), fromcredit (the distance
from the credited player: the model before this plan), n1member (n = 1 credits the collected member: the same),
unwrapped (d2 not reduced to 32 bits), f32product, floortotal, mercfull, site (each site one byte later).

Not covered: PLAYER_LevelUp and everything after it; the fatal path after 0x00408090's entry; MERC_AddExp past the
owner's-level test (the generator keeps L >= the owner's level; run:2026-10-27-sweep-hirelings covers the rest); x87
results stay ADR-0015 (5): the emulator's values agree with the model, the evidence for the float steps themselves is
run:2026-10-20-two-clients at n = 2 on the same instructions. Stdlib only.
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
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r58a", "emu")

import player  # noqa: E402

FAMILIES = ("share", "edge", "credit", "merc", "direct")
M32 = 0xFFFFFFFF
GAME, DTBL, MASK, ISC, XPT, HIRE, PROOT = (0x12000000, 0x12100000, 0x12101000, 0x12110000, 0x12200000, 0x12300000,
                                           0x12400000)
UBASE, USIZE = 0x13000000, 0x2000
F_KILL, F_SHARE, F_XC, F_AE, F_MA = 0x0057E990, 0x0057E6C0, 0x0057E480, 0x0057E510, 0x0057E860
F_FATAL, F_LEVELUP = 0x00408090, 0x00570880
HASH_OFF = {0: 0x1120, 1: 0x1320, 2: 0x1520}   # data 0x006E10E0
EXP_STATES = (53, 57, 59)                      # tbl:States.txt:exp (docs/tables/States.md)
NSTATES = 192
IMAGE_READS = {   # image data no code writes: pc ranges are not needed, the addresses are constants
    0x006E10E0, 0x006E10E4, 0x006E10E8, 0x006CE270, 0x006CE278}
IMAGE_READ_RANGES = ((0x006E1668, 0x006E1694 + 44),    # data:g_XpPenaltyBelow, data:g_XpPenaltyAbove
                     (0x00624EB0, 0x00624EC1))          # the switch of 0x00624DD0, in .text (its pc 0x00624DF6, 0x00624DFD)
HIRE_ROW = 0x118
OTHER_LEVEL = 77


class XT(player.Tables):
    """The synthetic Experience table of D/xp.bin behind the model's own Tables methods."""

    def __init__(self):
        caps = [99, 99, 99, 90, 99, 75, 99]
        rows = [dict(zip(player.CLASSES, caps), ExpRatio=10)]
        for k in range(1, 102):
            lvl = k - 1
            ratio = 1024 if lvl < 70 else max(5, 1024 - (lvl - 69) * 34)
            rows.append(dict({c: lvl << 25 for c in player.CLASSES}, ExpRatio=ratio))
        self.xp = rows

    def image(self):
        out = bytearray()
        for r in self.xp:
            for c in player.CLASSES:
                out += struct.pack("<I", r[c])
            out += struct.pack("<I", r["ExpRatio"])
        return bytes(out)


T = XT()


# ------------------------------------------------------------------------------------------------- the image
def ua(i):
    return UBASE + i * USIZE


def field(w, addr, val, n=4):
    w.append("w %08x %s" % (addr, (val & ((1 << (8 * n)) - 1)).to_bytes(n, "little").hex()))


def write_case(C):
    """-> the case's lines. C: dict(world, killer, monster, direct, sse, hirefactor)."""
    W = C["world"]
    L = []
    w = []
    field(w, 0x00994C88, C.get("sse", 1))
    field(w, GAME + 0x70, W.expansion)
    index = {}
    for i, u in enumerate(W.units):
        u["addr"] = ua(i)
        index[id(u)] = i
    # the unit hash
    for typ, off in HASH_OFF.items():
        buckets = [0] * 128
        chains = {}
        for u in W.units:
            if u.get("hash", u["type"]) == typ:
                chains.setdefault(u["id"] & 0x7F, []).append(u)
        for b, us in chains.items():
            buckets[b] = us[0]["addr"]
            for a, nxt in zip(us, us[1:] + [None]):
                a["next"] = nxt["addr"] if nxt else 0
        w.append("w %08x %s" % (GAME + off, b"".join(struct.pack("<I", x) for x in buckets).hex()))
    # the party list
    if W.parties or C.get("emptyroot"):
        field(w, GAME + 0x1D2C, PROOT)
        rec, nodes = PROOT + 0x100, PROOT + 0x1000
        field(w, PROOT + 4, rec if W.parties else 0)
        for k, p in enumerate(W.parties):
            r = rec + k * 16
            field(w, r, p["id"], 2)
            head = nodes + k * 0x100 if p["guids"] else 0
            field(w, r + 4, head)
            field(w, r + 8, r + 16 if k + 1 < len(W.parties) else 0)
            for j, g in enumerate(p["guids"]):
                na = nodes + k * 0x100 + j * 8
                field(w, na, g)
                field(w, na + 4, na + 8 if j + 1 < len(p["guids"]) else 0)
    else:
        field(w, GAME + 0x1D2C, 0)
    for u in W.units:
        a = u["addr"]
        field(w, a, u["type"])
        field(w, a + 4, u.get("cls", 0))
        field(w, a + 0x0C, u["id"])
        field(w, a + 0x10, u.get("mode", 1))
        field(w, a + 0x60, a + 0x500 if u.get("inv") is not None else 0)
        field(w, a + 0x80, GAME if u.get("game", 1) else 0)
        field(w, a + 0xC6, u.get("c6", 0), 1)
        field(w, a + 0xE4, u.get("next", 0))
        if u.get("inv") is not None:
            field(w, a + 0x500, 0 if u["inv"] == "bad" else 0x01020304)
            if u["inv"] != "bad":
                field(w, a + 0x524, u["inv"])
        # position and room
        static = u["type"] == 2 or 3 < u["type"] <= 5
        r1 = a + 0x800
        room = u.get("room")
        if static:
            field(w, a + 0x2C, a + 0x200)
            field(w, a + 0x200, r1 if room is not None else 0)
            field(w, a + 0x20C, u["x"])
            field(w, a + 0x210, u["y"])
        elif u.get("path", 1):
            field(w, a + 0x2C, a + 0x200)
            field(w, a + 0x202, u["x"], 2)
            field(w, a + 0x206, u["y"], 2)
            field(w, a + 0x21C, r1 if room is not None else 0)
        else:
            field(w, a + 0x2C, 0)
        if room is not None:
            field(w, r1 + 0x10, a + 0x840)
            field(w, a + 0x840 + 0x58, a + 0x900)
            field(w, a + 0x900 + 0x1D0, room)
        # stat lists
        la = a + 0x300
        field(w, a + 0x5C, la)
        ev = u.get("ev")
        special = ev is not None or u.get("states") is not None or u.get("flag0x800") is not None or u.get("flaglist")
        field(w, la + 0x10, 0x2000 | (0x80000000 if special else 0))
        field(w, la + 0x08, 0)
        ents = sorted(u["base"].items())
        field(w, la + 0x24, a + 0x400)
        field(w, la + 0x28, len(ents), 2)
        for k, (s, v) in enumerate(ents):
            field(w, a + 0x400 + k * 8, s << 16)
            field(w, a + 0x404 + k * 8, v)
        if special:
            evs = sorted((ev if ev is not None else u["base"]).items())
            field(w, la + 0x48, a + 0x480)
            field(w, la + 0x4C, len(evs), 2)
            for k, (s, v) in enumerate(evs):
                field(w, a + 0x480 + k * 8, s << 16)
                field(w, a + 0x484 + k * 8, v)
            bits = [0] * ((NSTATES + 31) >> 5)
            if u.get("states"):
                st = u["states"]
                bits[st >> 5] |= 1 << (st & 31)
            field(w, la + 0x58, a + 0x4C0)
            for k, b in enumerate(bits):
                field(w, a + 0x4C0 + k * 4, b)
            nodes = list(u.get("flaglist", ()))
            if u.get("flag0x800") is not None:
                nodes.append((0x800, u["flag0x800"]))
            field(w, la + 0x3C, a + 0x780 if nodes else 0)
            for k, (fl, own) in enumerate(nodes):
                na = a + 0x780 + k * 0x40
                field(w, na + 0x10, fl)
                field(w, na + 0x2C, na + 0x40 if k + 1 < len(nodes) else 0)
                field(w, na + 0x08, own[0])
                field(w, na + 0x0C, own[1])
        # monster owner link; a player's PlayerData and pet table
        if u["type"] == 1:
            m = u.get("mdata", "ok")
            field(w, a + 0x14, 0 if m == "nomdata" else a + 0x600)
            if m != "nomdata":
                field(w, a + 0x628, 0 if m == "noctl" else a + 0x640)
                if m != "noctl":
                    link = u.get("link")
                    field(w, a + 0x640 + 0x28, GAME if link is not None else 0)
                    if link is not None:
                        field(w, a + 0x640 + 0x2C, link[1])
                        field(w, a + 0x640 + 0x30, link[0])
        elif u["type"] == 0:
            field(w, a + 0x14, a + 0x540)
            if u.get("nopets"):
                field(w, a + 0x540 + 0x44, 0)
                continue
            field(w, a + 0x540 + 0x44, a + 0x580)
            field(w, a + 0x580, a + 0x5A0)
            for row in range(1, 8):
                field(w, a + 0x5A0 + row * 12, 0)
            pets = u.get("merc", ())
            if pets:
                field(w, a + 0x5A0 + 7 * 12, a + 0xC00)
                for k, (fl, uid) in enumerate(pets):
                    na = a + 0xC00 + k * 0x20
                    field(w, na, fl)
                    field(w, na + 4, uid)
                    field(w, na + 0x10, 1)
                    field(w, na + 0x14, na + 0x20 if k + 1 < len(pets) else 0)
    L.extend(w)
    for u in W.units:
        if u["type"] == 0:
            L.append("d %08x %d" % (u["addr"] + 0x400, len(u["base"]) * 8))
    if C.get("direct"):
        cr, exp, clvl, mlvl = C["direct"]
        mon = C.get("monster")
        L.append("r eax %x" % (exp & M32))
        L.append("call %x %x 0 %x %x %x %x" % (F_SHARE, cr["addr"], GAME, mon["addr"] if mon else 0, clvl & M32, mlvl & M32))
    else:
        k, mon = C.get("killer"), C.get("monster")
        L.append("call %x %x %x %x" % (F_KILL, GAME, k["addr"] if k else 0, mon["addr"] if mon else 0))
    return L


def mem_spec(d):
    out = ["# plan 0058 Phase 1: the fixed part of the image",
           "dword 00744304 %08x" % DTBL,
           "dword %08x 00000190" % (DTBL + 0xBD4),
           "dword %08x %08x" % (DTBL + 0xBCC, ISC),
           "dword %08x %08x" % (DTBL + 0x144, MASK),
           "dword %08x %08x" % (DTBL + 0xC4, NSTATES),
           "dword %08x 00000008" % (DTBL + 0xBF0)]
    for s in (12, 13, 29, 85):
        out.append("bytes %08x 00" % (ISC + s * 0x144 + 5))
    mask = [0] * ((NSTATES + 31) >> 5)
    for st in EXP_STATES:
        mask[st >> 5] |= 1 << (st & 31)
    for k, m in enumerate(mask):
        out.append("dword %08x %08x" % (MASK + k * 4, m))
    out.append("dword 0096C8A8 %08x" % XPT)
    out.append("const load %08x %s" % (XPT, os.path.join(os.path.abspath(d), "xp.bin")))
    # the hire rows: one row of id 1, version 0x64, level 0 and Exp/Lvl HIRE_FACTOR
    out += ["dword 0096BDD0 %08x" % HIRE, "dword 0096BDD4 00000002",
            "dword %08x 00000000" % (0x0096BDD8 + (0x100 + 1) * 4),
            "bytes %08x 6400" % HIRE, "dword %08x 00000001" % (HIRE + 4), "dword %08x 00000000" % (HIRE + 0x1C),
            "dword %08x %08x" % (HIRE + 0x20, HIRE_FACTOR),
            "bytes %08x 6400" % (HIRE + HIRE_ROW), "dword %08x 00000002" % (HIRE + HIRE_ROW + 4)]
    for g in (0x00408A60, 0x00681E09, 0x0040B4B0, 0x0040B430, 0x0040B480):
        out.append("guard %08x" % g)
    out += ["observe %08x" % F_FATAL, "observe %08x" % F_LEVELUP]
    out += ["trace %08x" % F_XC, "trace %08x" % F_AE, "trace %08x" % F_MA]
    return "\n".join(out) + "\n"


HIRE_FACTOR = 110


# ------------------------------------------------------------------------------------------------- the generators
def player_unit(uid, rng, x, y, room=2, level=None, **kw):
    lv = rng.randint(1, 99) if level is None else level
    cls = rng.choice((0, 1, 2, 4, 6)) if lv > 75 else rng.randint(0, 6)
    if lv > T.maxlvl(cls):
        cls = 0
    exp = ((max(lv, 1) - 1) << 25) + rng.randint(1, (1 << 24))
    base = {12: lv, 13: exp, 29: 0}
    s85 = kw.pop("s85", 0)
    if s85:
        base[85] = s85
    u = dict(type=0, cls=cls, id=uid, mode=rng.choice((1, 1, 1, 2, 3, 5)), x=x, y=y, room=room, base=base, path=1)
    u.update(kw)
    return u


def monster_unit(uid, rng, x, y, exp, mlvl, **kw):
    u = dict(type=1, cls=rng.randint(0, 700), id=uid, mode=rng.choice((0, 12, 1)), x=x, y=y, room=2,
             base={12: mlvl, 13: exp})
    u.update(kw)
    return u


def edge_pairs(lo, hi):
    out = []
    for dx in range(0, 81):
        for dy in range(0, 81):
            if lo <= dx * dx + dy * dy <= hi:
                out.append((dx, dy))
    return out


def draw_exp(rng):
    k = rng.random()
    if k < 0.55:
        return rng.randint(1, 5000)
    if k < 0.85:
        return rng.randint(5000, 1000000)
    if k < 0.93:
        return rng.randint(0x7FFF00, 0x800100)
    if k < 0.97:
        return rng.randint(1000000, 24129276)
    return rng.randint(24129277, 0x7FFFFFFF)


def uids(rng, n):
    if rng.random() < 0.25:        # one hash chain
        low = rng.randint(0, 0x7F)
        return [low + (k + 1) * 0x80 for k in range(n)]
    return rng.sample(range(1, 5000), n)


def eligible_at(rng, mx, my):
    r = rng.random()
    if r < 0.5:
        return mx + rng.randint(-40, 40), my + rng.randint(-40, 40)
    if r < 0.8:
        dx, dy = rng.choice(edge_pairs(6000, 6400))
        return mx + rng.choice((-1, 1)) * dx, my + rng.choice((-1, 1)) * dy
    dx, dy = rng.choice(edge_pairs(6400, 6400))
    return mx + rng.choice((-1, 1)) * dx, my + rng.choice((-1, 1)) * dy


def ineligible(u, rng, mx, my):
    r = rng.randint(0, 7)
    if r == 0:
        u["mode"] = 0
    elif r == 1:
        u["mode"] = 0x11
    elif r == 2:
        u["c6"] = 1
    elif r == 3:
        u["room"] = OTHER_LEVEL
    elif r == 4:
        u["room"] = None
    elif r == 5:
        u["x"] = 0
    elif r == 6:
        dx, dy = rng.choice(edge_pairs(6401, 6500))
        u["x"], u["y"] = mx + rng.choice((-1, 1)) * dx, my + rng.choice((-1, 1)) * dy
    else:
        u["x"], u["y"] = mx + rng.randint(81, 3000), my + rng.randint(-3000, 3000)
    return u


def share_case(rng, n, extra=None, credit_eligible=None):
    mx, my = rng.randint(4000, 60000), rng.randint(4000, 60000)
    extra = rng.randint(0, 3) if extra is None else extra
    total = n + extra
    if total == 0:
        total, extra = 1, 1
    ids = uids(rng, total + 1)
    mid = ids.pop()
    us = []
    for k in range(total):
        x, y = eligible_at(rng, mx, my)
        lv = 0 if rng.random() < 0.01 else None
        us.append(player_unit(ids[k], rng, x, y, level=lv, s85=rng.choice((0, 0, 0, rng.randint(1, 300)))))
    for u in us[n:]:
        ineligible(u, rng, mx, my)
    order = list(range(total))
    rng.shuffle(order)
    guids = [us[i]["id"] for i in order]
    # the credited player: an eligible one unless the case asks otherwise; a player killer here
    if credit_eligible is None:
        credit_eligible = rng.random() < 0.8 or extra == 0
    pool = us[:n] if (credit_eligible and n) else (us[n:] or us)
    cr = rng.choice([u for u in pool if u["room"] is not None] or [us[0]])
    if cr["room"] is None or cr["room"] == OTHER_LEVEL:
        cr["room"] = 2
    if cr.get("c6") or cr["mode"] in (0, 0x11):
        pass        # a dead killer's kill: the party's other members still count
    mon = monster_unit(ids and rng.randint(5000, 9000), rng, mx, my, draw_exp(rng), rng.randint(0, 110))
    parties = [dict(id=rng.randint(1, 0xFFFE), guids=guids)]
    if rng.random() < 0.2:
        parties.insert(0, dict(id=parties[0]["id"] ^ 0x5555 or 7, guids=[9001, 9002]))
    world = player.KillWorld(us + [mon], parties)
    return dict(world=world, killer=cr, monster=mon, sse=rng.choice((1, 1, 1, 0)))


def gen_share():
    rng = random.Random("r58a-share")
    out = []
    for n in range(1, 9):
        for k in range(240):
            c = share_case(rng, n)
            c["tag"] = "n%d" % n
            out.append(c)
    return out


def base_edge(rng, offs, levels=None, mexp=None, parties_guids=None):
    """A party at offsets from the monster, all alive at level 2; the first is the killer."""
    mx, my = 30000, 30000
    ids = list(range(11, 11 + len(offs)))
    us = [player_unit(ids[i], rng, mx + o[0], my + o[1], level=(levels[i] if levels else None))
          for i, o in enumerate(offs)]
    mon = monster_unit(7000, rng, mx, my, mexp if mexp is not None else rng.randint(100, 50000), rng.randint(1, 90))
    world = player.KillWorld(us + [mon], [dict(id=3, guids=parties_guids or [u["id"] for u in us])])
    return dict(world=world, killer=us[0], monster=mon, sse=1)


def gen_edge():
    rng = random.Random("r58a-edge")
    out = []

    def add(tag, c):
        c["tag"] = tag
        out.append(c)

    # the distance edge: a second member and the killer himself, every representation of d2 6396..6410 in every sign
    for dx, dy in edge_pairs(6396, 6410):
        for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            add("edge-other", base_edge(rng, [(1, 1), (sx * dx, sy * dy), (2, 2)]))
            add("edge-self", base_edge(rng, [(sx * dx, sy * dy), (1, 1), (2, 2)]))
    # distance from the monster, not the killer: both sides of the bound against each
    for _ in range(40):
        add("ref-a", base_edge(rng, [(90, 0), (10, 0), (5, 5)]))      # member within the monster's bound, far from none
        add("ref-b", base_edge(rng, [(0, 60), (0, -60), (3, 3)]))     # 120 from the killer, 60 from the monster
        add("ref-c", base_edge(rng, [(60, 0), (130, 0), (2, 2)]))     # 70 from the killer, 130 from the monster
    # n = 1 with the killer out: the sole member is another; the killer dead, far, alone, none
    for _ in range(30):
        add("n1-far", base_edge(rng, [(200, 0), (3, 3)]))
        c = base_edge(rng, [(1, 1), (3, 3)]); c["killer"]["mode"] = 0x11; add("n1-dead", c)
        add("n0-far", base_edge(rng, [(200, 0), (300, 0)]))
        c = base_edge(rng, [(1, 1), (300, 0)]); c["killer"]["c6"] = 1; add("n0-dead", c)
    # unpartied: no test at all
    for _ in range(30):
        c = base_edge(rng, [(5000, 0)]); c["world"].parties = []; add("solo-far", c)
        c = base_edge(rng, [(1, 1)]); c["world"].parties = []; c["killer"]["mode"] = 0; add("solo-dead", c)
        c = base_edge(rng, [(1, 1)]); c["emptyroot"] = 1; c["world"].parties = []; add("solo-emptyroot", c)
    # position words of 0
    for _ in range(12):
        c = base_edge(rng, [(1, 1), (3, 3)]); c["monster"]["x"] = 0; add("mon-x0", c)
        c = base_edge(rng, [(1, 1), (3, 3)]); c["monster"]["y"] = 0
        c["killer"]["y"] = 30; c["world"].units[1]["y"] = 40; add("mon-y0", c)
        c = base_edge(rng, [(1, 1), (3, 3)]); c["monster"]["path"] = 0; add("mon-nopath", c)
        c = base_edge(rng, [(1, 1), (3, 3)]); c["world"].units[1]["x"] = 0; add("mem-x0", c)
        c = base_edge(rng, [(1, 1), (3, 3)]); c["world"].units[1]["path"] = 0; add("mem-nopath", c)
        c = base_edge(rng, [(1, 1), (0, 3)]); c["world"].units[1]["y"] = 30000; c["world"].units[1]["x"] = 30000
        add("mem-y", c)
    # a static victim: types 2, 4, 5 read the dwords
    for ty in (2, 4, 5):
        for _ in range(6):
            c = base_edge(rng, [(1, 1), (70, 0), (90, 0)]); c["monster"]["type"] = ty; c["monster"]["hash"] = 2
            add("mon-static", c)
    # the wrap of d2: 65534^2 + 512^2 = 2^32 + 4
    for dy in (510, 511, 512, 513, 517, 518):
        c = base_edge(rng, [(1, 1), (3, 3)])
        c["monster"].update(x=65535, y=1000)
        c["killer"].update(x=65530, y=1000)
        c["world"].units[1].update(x=1, y=1000 + dy)
        add("wrap", c)
    for d in (46340, 46341):
        c = base_edge(rng, [(1, 1), (3, 3)])
        c["monster"].update(x=60000, y=60000)
        c["killer"].update(x=60001, y=60001)
        c["world"].units[1].update(x=60000 - d, y=60000 - d)
        add("wrap", c)
    # the cap: a ninth and tenth eligible; a ninth that fails a test before the cap; eight exactly in a longer list
    for _ in range(60):
        add("nine", base_edge(rng, [(k % 5, k % 7) for k in range(9)]))
        add("ten", base_edge(rng, [(k % 5, k % 7) for k in range(10)]))
    for tag, fn in (("nine-dead", lambda u: u.update(mode=0)), ("nine-far", lambda u: u.update(x=u["x"] + 900)),
                    ("nine-level", lambda u: u.update(room=OTHER_LEVEL)), ("nine-noroom", lambda u: u.update(room=None))):
        for _ in range(20):
            c = base_edge(rng, [(k % 5, k % 7) for k in range(9)])
            fn(c["world"].units[rng.randint(1, 8)])
            add(tag, c)
    for _ in range(20):         # the ninth node lost in the hash, and duplicated guids: a duplicate is counted twice
        c = base_edge(rng, [(k % 5, k % 7) for k in range(8)])
        c["world"].parties[0]["guids"].append(4242)
        add("nine-missing", c)
        c = base_edge(rng, [(1, 1), (2, 2)])
        g = c["world"].parties[0]["guids"]
        g.append(g[1])
        add("dup-guid", c)
    # the party list
    for _ in range(20):
        c = base_edge(rng, [(1, 1), (2, 2), (3, 3)])
        c["world"].parties.insert(0, dict(id=9, guids=[8001, 8002]))
        add("second-party", c)
        c = base_edge(rng, [(1, 1), (2, 2), (3, 3)])
        c["world"].parties[0]["id"] = 3
        c["world"].parties.append(dict(id=3, guids=[c["killer"]["id"]]))
        c["world"].parties[0]["guids"].remove(c["killer"]["id"])
        add("same-id", c)      # the killer's list is the second, the first list of the id is walked
        c = base_edge(rng, [(1, 1), (2, 2), (3, 3)])
        c["killer"]["inv"] = c["killer"]["id"]
        add("inv-guid", c)
        c = base_edge(rng, [(1, 1), (2, 2), (3, 3)])
        c["killer"]["inv"] = "bad"
        add("inv-bad", c)
        c = base_edge(rng, [(1, 1), (2, 2), (3, 3)])
        c["killer"]["game"] = 0
        add("nogame", c)
        c = base_edge(rng, [(1, 1), (2, 2)])
        c["killer"]["room"] = None
        add("killer-noroom", c)
        c = base_edge(rng, [(1, 1), (2, 2), (3, 3)])
        c["killer"]["room"] = OTHER_LEVEL      # the level is the killer's, not the monster's
        c["world"].units[1]["room"] = OTHER_LEVEL
        add("killer-level", c)
        c = base_edge(rng, [(1, 1), (2, 2), (3, 3)])
        c["monster"]["room"] = OTHER_LEVEL     # the victim's level is not read
        add("mon-level", c)
    # level sums and the evaluated list
    for _ in range(15):
        add("sigma0", base_edge(rng, [(1, 1), (2, 2)], levels=[0, 0]))
        add("sigma0-1", base_edge(rng, [(1, 1)], levels=[0]))
    for _ in range(40):
        c = base_edge(rng, [(1, 1), (2, 2), (3, 3)])
        for u in c["world"].units[:3]:
            u["ev"] = {12: rng.randint(1, 99), 85: rng.choice((0, 50))}
        add("evaluated", c)
        c = base_edge(rng, [(1, 1)])
        c["killer"]["ev"] = {12: rng.randint(1, 99), 85: rng.choice((0, 50))}
        add("evaluated-n1", c)
    # the wrap of the total, each side of the bound for each n; and exp at the 0x7FFFFF clamp
    for n in range(2, 9):
        top = (2 ** 31 - 1) // (89 * (n - 1))
        for e in (top - 1, top, top + 1, top + 2, top * 2, 2 ** 31 // (n - 1), 0x7FFFFFFF):
            add("wrap-total", base_edge(rng, [(k % 5, k % 7) for k in range(n)], mexp=e))
        for e in (0x7FFFFE, 0x7FFFFF, 0x800000):
            add("clamp", base_edge(rng, [(k % 5, k % 7) for k in range(n)], mexp=e))
    # the two ftol2 paths on close quotients
    for sse in (0, 1):
        for _ in range(60):
            n = rng.randint(2, 8)
            c = base_edge(rng, [(k % 5, k % 7) for k in range(n)], mexp=rng.randint(1, 400))
            c["sse"] = sse
            add("ftol%d" % sse, c)
    return out


def killer_monster(uid, rng, x, y, link=None, **kw):
    u = dict(type=1, cls=rng.randint(0, 700), id=uid, mode=1, x=x, y=y, room=2, base={12: 5}, link=link)
    u.update(kw)
    return u


def gen_credit():
    rng = random.Random("r58a-credit")
    out = []

    def world(extra=(), party=False, far=False):
        p = player_unit(21, rng, 30000 + (900 if far else 3), 30000)
        q = player_unit(22, rng, 30004, 30000)
        mon = monster_unit(7000, rng, 30000, 30000, rng.randint(50, 90000), rng.randint(1, 90))
        units = [p, q, mon] + list(extra)
        parties = [dict(id=5, guids=[22, 21])] if party else []
        return units, parties, p, q, mon

    def add(tag, killer, units, parties, mon, **kw):
        c = dict(world=player.KillWorld(units, parties), killer=killer, monster=mon, sse=1, tag=tag)
        c.update(kw)
        out.append(c)

    for rep in range(30):
        for party in (False, True):
            # player killer; a state on the victim changes nothing
            u, ps, p, q, m = world(party=party)
            m.update(states=57, flag0x800=(0, 22))
            add("player", p, u, ps, m)
            # owner link
            k = killer_monster(300, rng, 30001, 30001, link=(0, 21))
            u, ps, p, q, m = world([k], party)
            add("owner", k, u, ps, m)
            # the owner far from the victim
            k = killer_monster(300, rng, 30001, 30001, link=(0, 21))
            u, ps, p, q, m = world([k], party, far=True)
            add("owner-far", k, u, ps, m)
            # a chain's end is a monster, no link, no mdata, no ai control, link to a lost unit
            k = killer_monster(300, rng, 30001, 30001, link=(1, 301))
            k2 = killer_monster(301, rng, 30001, 30001, link=(0, 21))
            u, ps, p, q, m = world([k, k2], party)
            add("owner-monster", k, u, ps, m)
            k = killer_monster(300, rng, 30001, 30001, link=None)
            u, ps, p, q, m = world([k], party)
            add("no-link", k, u, ps, m)
            k = killer_monster(300, rng, 30001, 30001, link=None, mdata="nomdata")
            u, ps, p, q, m = world([k], party)
            add("no-mdata", k, u, ps, m)
            k = killer_monster(300, rng, 30001, 30001, link=None, mdata="noctl")
            u, ps, p, q, m = world([k], party)
            add("no-ctl", k, u, ps, m)
            k = killer_monster(300, rng, 30001, 30001, link=(0, 4444))
            u, ps, p, q, m = world([k], party)
            add("link-lost", k, u, ps, m)
            # a state in the exp mask: the stat list's owner replaces the link; the victim's wins
            for st in EXP_STATES:
                k = killer_monster(300, rng, 30001, 30001, link=(0, 21), states=st, flag0x800=(0, 22))
                u, ps, p, q, m = world([k], party)
                add("state-killer", k, u, ps, m)
                k = killer_monster(300, rng, 30001, 30001, link=(0, 21))
                u, ps, p, q, m = world([k], party)
                m.update(states=st, flag0x800=(0, 22))
                add("state-victim", k, u, ps, m)
                k = killer_monster(300, rng, 30001, 30001, link=(0, 21), states=st, flag0x800=(0, 22))
                u, ps, p, q, m = world([k], party)
                m.update(states=st, flag0x800=(0, 21))
                add("state-both", k, u, ps, m)
            # the state without a 0x800 list; the victim's without it clears the killer's; a state outside the mask
            k = killer_monster(300, rng, 30001, 30001, link=(0, 21), states=57)
            k["flaglist"] = [(0x400, (0, 22))]
            u, ps, p, q, m = world([k], party)
            add("state-nolist", k, u, ps, m)
            k = killer_monster(300, rng, 30001, 30001, link=(0, 21), states=57, flag0x800=(0, 22))
            u, ps, p, q, m = world([k], party)
            m.update(states=59)
            m["flaglist"] = [(0x400, (0, 22))]
            add("state-victim-nolist", k, u, ps, m)
            k = killer_monster(300, rng, 30001, 30001, link=(0, 21), states=60, flag0x800=(0, 22))
            u, ps, p, q, m = world([k], party)
            add("state-outside", k, u, ps, m)
            # a list node of another flag first, then 0x800
            k = killer_monster(300, rng, 30001, 30001, link=(0, 21), states=53, flag0x800=(0, 22))
            k["flaglist"] = [(0x400, (0, 21))]
            u, ps, p, q, m = world([k], party)
            add("state-second-node", k, u, ps, m)
            # the list's owner is a monster or lost: no credit, the link does not come back
            k = killer_monster(300, rng, 30001, 30001, link=(0, 21), states=53, flag0x800=(1, 300))
            u, ps, p, q, m = world([k], party)
            add("state-owner-monster", k, u, ps, m)
            k = killer_monster(300, rng, 30001, 30001, link=(0, 21), states=53, flag0x800=(0, 4444))
            u, ps, p, q, m = world([k], party)
            add("state-owner-lost", k, u, ps, m)
            # a player as the victim: its experience stands for the monster's, its level for the monster level
            v = player_unit(23, rng, 30000, 30000)
            u, ps, p, q, m = world(party=party)
            v["hash"] = 0
            u = [x for x in u if x is not m] + [v]
            add("victim-player", p, u, ps, v)
            u, ps, p, q, m = world(party=party)
            p["nopets"] = 1
            add("nopets", p, u, ps, m)
            # no experience, no monster, no killer, a killer of another type
            u, ps, p, q, m = world(party=party)
            m["base"][13] = 0
            add("exp0", p, u, ps, m)
            u, ps, p, q, m = world(party=party)
            m["base"][13] = -5
            add("expneg", p, u, ps, m)
            u, ps, p, q, m = world(party=party)
            del m["base"][13]
            add("expabsent", p, u, ps, m)
            u, ps, p, q, m = world(party=party)
            add("nomon", p, u, ps, None)
            u, ps, p, q, m = world(party=party)
            add("nokiller", None, u, ps, m)
            k = dict(type=2, cls=0, id=44, mode=1, x=1, y=1, room=2, base={}, hash=2)
            u, ps, p, q, m = world([k], party)
            add("killer-type2", k, u, ps, m)
    return out


def gen_merc():
    rng = random.Random("r58a-merc")
    out = []

    def world(party, mercl, mexp, owner_level, far=False):
        p = player_unit(21, rng, 30000 + (900 if far else 3), 30000, level=owner_level)
        q = player_unit(22, rng, 30004, 30000, s85=rng.choice((0, 25)))
        mon = monster_unit(7000, rng, 30000, 30000, mexp, rng.randint(1, 90))
        merc = killer_monster(300, rng, 30001, 30001, link=(0, 21))
        merc["base"] = {12: mercl}
        if rng.random() < 0.3:
            merc["ev"] = {12: mercl, 85: rng.randint(1, 100)}
        p["merc"] = [(0, 300)]
        return [p, q, mon, merc], ([dict(id=5, guids=[22, 21])] if party else []), p, q, mon, merc

    for rep in range(120):
        party = rep % 2 == 1
        lv = rng.randint(1, 60)
        mercl = lv + rng.randint(0, 30)      # at or above the owner: MERC_AddExp ends at its level test
        mexp = rng.choice((rng.randint(1, 500), rng.randint(500, 50000), rng.randint(50000, 9000000)))
        for tag, killer_is in (("merc-kills", "merc"), ("owner-kills", "owner"), ("other-kills", "other")):
            u, ps, p, q, m, mc = world(party, mercl, mexp, lv)
            k = mc if killer_is == "merc" else p
            if killer_is == "other":
                k = killer_monster(301, rng, 30001, 30001, link=(0, 21))
                u = u + [k]
            out.append(dict(world=player.KillWorld(u, ps, hire_factor=HIRE_FACTOR), killer=k, monster=m, sse=1, tag=tag))
        # the mercenary's award stands when the owner is out of the share
        u, ps, p, q, m, mc = world(True, mercl, mexp, lv, far=True)
        out.append(dict(world=player.KillWorld(u, ps, hire_factor=HIRE_FACTOR), killer=mc, monster=m, sse=1, tag="merc-owner-far"))
        # the first node has flag bit 0: skipped; no node alive; the hire row absent (id 3); the mercenary's node lost
        u, ps, p, q, m, mc = world(party, mercl, mexp, lv)
        p["merc"] = [(1, 300), (0, 300)]
        out.append(dict(world=player.KillWorld(u, ps, hire_factor=HIRE_FACTOR), killer=p, monster=m, sse=1, tag="merc-flag"))
        u, ps, p, q, m, mc = world(party, mercl, mexp, lv)
        p["merc"] = [(1, 300)]
        out.append(dict(world=player.KillWorld(u, ps, hire_factor=HIRE_FACTOR), killer=p, monster=m, sse=1, tag="merc-dead"))
        u, ps, p, q, m, mc = world(party, mercl, mexp, lv)
        p["merc"] = [(0, 4444)]
        out.append(dict(world=player.KillWorld(u, ps, hire_factor=HIRE_FACTOR), killer=p, monster=m, sse=1, tag="merc-lost"))
        u, ps, p, q, m, mc = world(party, mercl, mexp, lv)
        mc["link"] = None
        out.append(dict(world=player.KillWorld(u, ps, hire_factor=HIRE_FACTOR), killer=p, monster=m, sse=1, tag="merc-nolink"))
    return out


def gen_direct():
    rng = random.Random("r58a-direct")
    out = []
    for rep in range(60):
        n = rng.randint(1, 8)
        c = share_case(rng, n, extra=0)
        cr = c["killer"]
        c["direct"] = (cr, c["monster"]["base"][13], cr["base"][12], c["monster"]["base"][12])
        if rep % 2:
            c["monster"] = None          # the null victim: no distance test
            for u in c["world"].units:
                if u["type"] == 0:
                    u["x"] += 500
        c["tag"] = "direct-null" if rep % 2 else "direct"
        out.append(c)
    for rep in range(30):              # an unpartied credit: the collector still runs on it
        c = base_edge(rng, [(rng.choice((3, 200)), 0)])
        c["world"].parties = []
        cr = c["killer"]
        c["direct"] = (cr, c["monster"]["base"][13], cr["base"][12], c["monster"]["base"][12])
        c["tag"] = "direct-solo"
        out.append(c)
    return out


GEN = {"share": gen_share, "edge": gen_edge, "credit": gen_credit, "merc": gen_merc, "direct": gen_direct}


# ------------------------------------------------------------------------------------------------- the check
def predict(C, O):
    """Fresh base dicts per call: kill_events writes experience into them."""
    W = C["world"]
    saved = [dict(u["base"]) for u in W.units]
    try:
        if C.get("direct"):
            ev, end = player.kill_events(W, T, None, C.get("monster"), O, entry="share", direct=C["direct"])
        else:
            ev, end = player.kill_events(W, T, C.get("killer"), C.get("monster"), O)
        finals = {u["id"]: dict(u["base"]) for u in W.units if u["type"] == 0}
    finally:
        for u, b in zip(W.units, saved):
            u["base"] = b
    return ev, end, finals


def controls():
    def o(**kw):
        return type("O", (player.KillOpts,), kw)
    return {"le": (o(strict=True), 0), "bound": (o(bound=6401), 0), "cap": (o(cap=9), 0),
            "fromcredit": (o(from_credit=True), 0), "n1member": (o(n1_member=True), 0),
            "unwrapped": (o(unwrapped=True), 0), "f32product": (o(f32_product=True), 0),
            "floortotal": (o(floor_total=True), 0), "mercfull": (o(merc_full=True), 0),
            "site": (player.KillOpts, 1)}


def parse_out(path):
    """-> list per case of {"t": [(pc, regs, stack)], "c": str, "d": [(addr, bytes)]}."""
    cases, cur = [], {"t": [], "d": []}
    tail = {"R": [], "W": []}
    obs_stack = None
    for line in open(path):
        f = line.split()
        if not f:
            continue
        if f[0] == "T":
            regs = dict(x.split("=") for x in f[3:11])
            cur["t"].append((int(f[2], 16), {k: int(v, 16) for k, v in regs.items()}, bytes.fromhex(f[11])))
        elif f[0] == "C":
            cur["c"] = f
            cases.append(cur)
            cur = {"t": [], "d": []}
        elif f[0] == "A":
            cases[-1]["a"] = bytes.fromhex(f[1])
        elif f[0] == "D":
            cases[-1]["d"].append((int(f[1], 16), bytes.fromhex(f[2])))
        elif f[0] in tail:
            tail[f[0]].append((int(f[1], 16), int(f[2], 16), int(f[3]), int(f[4])))
    return cases, tail


def compare(C, got, O, site_off):
    """-> None when the record equals the model, else the first difference."""
    W = C["world"]
    ids = {u["addr"]: u["id"] for u in W.units}
    ev, end, finals = predict(C, O)
    i = 0
    tr = got["t"]
    n_loop = 0

    def d32(b, off):
        return struct.unpack_from("<I", b, off)[0]
    pending = None
    for e in ev:
        if e[0] == "SHARE":
            pending = e
            n_loop = 0
            continue
        if i >= len(tr):
            return "events: model has %s, the record ended" % (e,)
        pc, r, st = tr[i]
        i += 1
        ret = d32(st, 0)
        if e[0] == "XC":
            if pc != F_XC:
                return "pc %x for %s" % (pc, e)
            want = (e[1], e[2] & M32, e[3] & M32, GAME, e[4] & M32, e[5] + site_off)
            have = (ids.get(r["ebx"]), r["eax"], r["edi"], d32(st, 4), d32(st, 8), ret)
            if want != have:
                return "XC want %s have %s" % (want, have)
            if e[5] == 0x0057E78A:
                q_bits = struct.pack("<f", pending[3])
                ctx = st[0x18:0x18 + 0x4C]
                if st[0x64:0x68] != q_bits:
                    return "q %s want %s" % (st[0x64:0x68].hex(), q_bits.hex())
                nm, sigma = d32(ctx, 0x44), d32(ctx, 0x48)
                if nm != pending[1] or sigma != pending[2] & M32:
                    return "ctx n, sigma %d %d want %d %d" % (nm, sigma, pending[1], pending[2])
                units = [ids.get(d32(ctx, 4 + 4 * k)) for k in range(nm)]
                lvls = [d32(ctx, 0x24 + 4 * k) for k in range(nm)]
                if tuple(units) != pending[4] or tuple(lvls) != tuple(v & M32 for v in pending[5]):
                    return "ctx members %s %s want %s" % (units, lvls, pending)
                mon = C.get("monster")
                if d32(ctx, 0) != (mon["addr"] if mon else 0):
                    return "ctx+0"
                if r["ebp"] - 0x68 != r["esp"]:
                    return "frame"
        elif e[0] == "AE":
            if pc != F_AE:
                return "pc %x for %s" % (pc, e)
            want = (e[1], GAME, e[2] & M32, e[3] & M32, e[4] + site_off)
            have = (ids.get(r["esi"]), d32(st, 4), d32(st, 8), d32(st, 12), ret)
            if want != have:
                return "AE want %s have %s" % (want, have)
        elif e[0] == "MA":
            if pc != F_MA:
                return "pc %x for %s" % (pc, e)
            want = (e[1] & M32, e[2], GAME, e[3], e[4] & M32, e[5] + site_off)
            have = (r["eax"], ids.get(r["edi"]), d32(st, 4), ids.get(d32(st, 8)), d32(st, 12), ret)
            if want != have:
                return "MA want %s have %s" % (want, have)
    if i != len(tr):
        return "extra trace at %x" % tr[i][0]
    c = got["c"]
    if end == "ret":
        if c[3].startswith("OBS") or c[3] == "STOP":
            return "model returns, record %s" % " ".join(c[3:6])
        want_pop = 0x10 if C.get("direct") else 4
        if not c[-2].endswith("=%d" % want_pop) and "pop=%d" % want_pop not in c:
            return "pop %s" % c
    else:
        if c[3] != "OBS":
            return "model boundary %s, record %s" % (end, " ".join(c[3:7]))
        if int(c[4], 16) != end[0]:
            return "boundary %s want %x" % (c[4], end[0])
        a = got["a"]
        if d32(a, 0) != end[1] + site_off:
            return "boundary site %x want %x" % (d32(a, 0), end[1] + site_off)
        if end[0] == F_FATAL and d32(a, 4) != end[2]:
            return "fatal line %x" % d32(a, 4)
    # the players' experience and stat 29 after the case
    dumps = {a: b for a, b in got["d"]}
    for u in W.units:
        if u["type"] != 0:
            continue
        b = dumps.get(u["addr"] + 0x400)
        if b is None:
            return "no dump"
        keys = sorted(u["base"])
        have = {k: struct.unpack_from("<I", b, 4 + 8 * j)[0] for j, k in enumerate(keys)}
        for s in (13, 29):
            if have.get(s) != finals[u["id"]][s] & M32:
                return "unit %d stat %d: %s want %s" % (u["id"], s, have.get(s), finals[u["id"]][s] & M32)
    return None


STATIC_SITES = [
    (0x0057E654, "cmp", "edx,0x1900"), (0x0057E65A, "ja", ""), (0x0057E662, "cmp", "eax,0x8"), (0x0057E665, "jl", ""),
    (0x0057E667, "push", "0xf25"), (0x0057E66C, "call", "0x408090"), (0x0057E681, "call", "0x681e09"),
    (0x0057E64C, "imul", "edx,edi"), (0x0057E64F, "imul", "eax,ecx"), (0x0057E652, "add", "edx,eax"),
    (0x0057E5AC, "call", "0x5541b0"), (0x0057E622, "je", ""), (0x0057E640, "je", ""),
    (0x0057E6E7, "mov", "DWORD PTR [ebp-0x50],ecx"), (0x0057E6EA, "push", "0x57e5a0"), (0x0057E6F3, "call", "0x5405a0"),
    (0x0057E710, "jne", ""), (0x0057E726, "mov", "esi,ebx"), (0x0057E739, "imul", "eax,edi"), (0x0057E73C, "imul", "eax,eax,0x59"),
    (0x0057E748, "sar", "eax,0x8"), (0x0057E754, "fild", "DWORD PTR [ebp+0x10]"), (0x0057E75A, "fidiv", "DWORD PTR [ebp-0x8]"),
    (0x0057E75D, "fstp", "DWORD PTR [ebp-0x4]"), (0x0057E775, "fild", "DWORD PTR [ebp+0xc]"), (0x0057E778, "fmul", "DWORD PTR [ebp-0x4]"),
    (0x0057E77B, "call", "0x682fd0"), (0x0057EA2D, "imul", "eax,eax,0x56"), (0x0057EA2B, "je", ""), (0x0057EA68, "je", ""),
    (0x0057EA6D, "mov", "ecx,DWORD PTR [ebp+0x8]"), (0x005405DF, "jne", ""), (0x0054062C, "jne", ""), (0x005A4F04, "shr", "edx,0x1a"),
    (0x0057CD51, "call", "0x5a4ef0"), (0x005A4F12, "call", "0x57e990")]


def cmd_static(d, exe):
    """The instruction forms the claims turn on (ADR-0015 (5)), and raw call scans; written to D/static.txt."""
    import subprocess
    if hashlib.sha256(open(exe, "rb").read()).hexdigest() != "631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf":
        raise SystemExit("not the pinned Game.exe")
    txt = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", exe], capture_output=True, text=True).stdout
    ins = {}
    for line in txt.splitlines():
        p = line.split(":", 1)
        if len(p) == 2 and p[0].strip() and all(c in "0123456789abcdef" for c in p[0].strip()):
            f = p[1].split(None, 1)
            if f:
                ins[int(p[0], 16)] = (f[0], f[1].strip() if len(f) > 1 else "")
    out, bad = [], 0
    for a, m, ops in STATIC_SITES:
        got = ins.get(a)
        ok = got is not None and got[0] == m and (not ops or got[1].replace(" ", "").startswith(ops.replace(" ", "")))
        bad += 0 if ok else 1
        out.append("%s 0x%08X %s %s" % ("ok " if ok else "BAD", a, got[0] if got else "?", got[1] if got else ""))
    for name, tgt in (("XP_OnMonsterKill", 0x57E990), ("sub_005A4EF0", 0x5A4EF0), ("XP_PartyShare", 0x57E6C0),
                      ("sub_005405A0_PartyForEachInLevel", 0x5405A0), ("XP_Compute", 0x57E480), ("PLAYER_AddExperience", 0x57E510),
                      ("MERC_AddExp", 0x57E860), ("sub_0057E5A0_PartyXpCollect", 0x57E5A0)):
        sites = sorted(a for a, (m, ops) in ins.items() if m in ("call", "jmp", "push") and ops.split(" ")[0] == "0x%x" % tgt)
        out.append("refs to %s 0x%08X: %d: %s" % (name, tgt, len(sites), " ".join("0x%08X" % a for a in sites)))
    for name, tgt in (("sub_00535790_PlayerCount", 0x535790), ("sub_00573930_MonPlayerBonus", 0x573930),
                      ("sub_005408E0_PartyCountInLevel", 0x5408E0)):
        sites = sorted(a for a, (m, ops) in ins.items() if m in ("call", "jmp", "push") and ops.split(" ")[0] == "0x%x" % tgt)
        out.append("refs to %s 0x%08X: %d: %s" % (name, tgt, len(sites), " ".join("0x%08X" % a for a in sites)))
    pov = sorted(a for a, (m, ops) in ins.items() if "0x883d70" in ops)
    out.append("instructions naming data:g_PlayersOverride 0x00883D70: %d: %s" % (len(pov), " ".join("0x%08X" % a for a in pov)))
    wr = sorted(a for a, (m, ops) in ins.items() if m == "or" and "+0xc4]" in ops and ops.endswith(",0x4000000"))
    out.append("or [unit+0xC4],0x4000000 sites: %d: %s" % (len(wr), " ".join("0x%08X" % a for a in wr)))
    out.append("%d of %d instruction forms differ" % (bad, len(STATIC_SITES)))
    text = "\n".join(out) + "\n"
    with open(os.path.join(d, "static.txt"), "w") as f:
        f.write(text)
    print(text, end="")
    return 1 if bad else 0


def in_image(a):
    return a in IMAGE_READS or any(lo <= a < hi for lo, hi in IMAGE_READ_RANGES)


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "xp.bin"), "wb") as f:
        f.write(T.image())
    for fam in FAMILIES:
        cases = GEN[fam]()
        with open(os.path.join(d, fam + ".cases"), "w") as f:
            for C in cases:
                f.write("\n".join(write_case(C)) + "\n")
        with open(os.path.join(d, fam + ".mem"), "w") as f:
            f.write(mem_spec(d))
        print(fam, len(cases))
    return 0


def wrap_table():
    out = ["the total's product (n - 1) * E * 89, i32 (0x0057E739 imul, 0x0057E73C imul): largest E that fits, first that wraps"]
    for n in range(2, 9):
        top = (2 ** 31 - 1) // (89 * (n - 1))
        out.append("  n=%d  E=%d: %d fits; E=%d: %d > 2^31-1 wraps to %d; total %d" % (
            n, top, (n - 1) * top * 89, top + 1, (n - 1) * (top + 1) * 89, player.i32((n - 1) * (top + 1) * 89),
            player.xp_share_total(top + 1, n)))
    out.append("d2 = dx*dx + dy*dy (0x0057E64C, 0x0057E64F imul, 0x0057E652 add, 32 bits; unsigned ja at 0x0057E65A)")
    out.append("  |dx| = |dy| = 46340: %d fits; 46341: %d wraps to %d" % (2 * 46340 ** 2, 2 * 46341 ** 2, (2 * 46341 ** 2) & M32))
    out.append("  dx = 65534, dy = 512 (word coordinates 65535 and 1 reach it): %d wraps to %d, inside the bound" % (
        65534 ** 2 + 512 ** 2, (65534 ** 2 + 512 ** 2) & M32))
    return out


def cmd_check(d):
    total = bad = 0
    per = {}
    ctl = controls()
    ctl_fail = {k: 0 for k in ctl}
    ctl_sep = {k: {} for k in ctl}
    reads, writes = set(), set()
    evn = {}
    first = []
    lines = []
    calls = {"members": {}, "n1_other": 0, "n1_self": 0, "n0": 0, "fatal": 0, "levelup": 0, "mismatch_sigma": 0,
             "edge_in": 0, "edge_out": 0, "ftol0": 0, "ftol1": 0, "merc": 0, "wrapped": 0}
    for fam in FAMILIES:
        cases = GEN[fam]()
        # write_case fills the addresses and links
        for C in cases:
            write_case(C)
        got, tail = parse_out(os.path.join(d, fam + ".out"))
        if len(got) != len(cases):
            print("FAIL %s: %d records for %d cases" % (fam, len(got), len(cases)))
            return 1
        for a in tail["R"]:
            reads.add(a)
        for a in tail["W"]:
            writes.add(a)
        for C, g in zip(cases, got):
            total += 1
            tag = C.get("tag", "?")
            r = compare(C, g, player.KillOpts, 0)
            p = per.setdefault((fam, tag), [0, 0])
            p[0] += 1
            if r is not None:
                bad += 1
                p[1] += 1
                if len(first) < 40:
                    first.append("%s case %d (%s): %s" % (fam, got.index(g) + 1, tag, r))
            ev, end, _ = predict(C, player.KillOpts)
            sh = [e for e in ev if e[0] == "SHARE"]
            for e in ev:
                evn[e[0]] = evn.get(e[0], 0) + 1
            if sh:
                calls["members"][sh[0][1]] = calls["members"].get(sh[0][1], 0) + 1
            calls["ftol%d" % C.get("sse", 1)] += 1 if sh else 0
            if end != "ret":
                calls["fatal" if end[0] == F_FATAL else "levelup"] += 1
            if any(e[0] == "MA" for e in ev):
                calls["merc"] += 1
            if any(e[0] == "XC" and e[5] == 0x0057E721 for e in ev):
                W = C["world"]
                members, _ = player.party_collect(W, C["direct"][0] if C.get("direct") else W.credit(C.get("killer"), C.get("monster")), C.get("monster"))
                who = C["direct"][0] if C.get("direct") else W.credit(C.get("killer"), C.get("monster"))
                calls["n1_self" if members and members[0][0] is who else "n1_other"] += 1
            for k, (O, off) in ctl.items():
                rr = compare(C, g, O, off)
                ctl_fail[k] += 1 if rr is not None else 0
                if rr is not None:
                    ctl_sep[k][tag] = ctl_sep[k].get(tag, 0) + 1
    lines.append("# run: plan 0058 Phase 1, tools/party_emu.py check")
    lines.append("cases %d, mismatches %d" % (total, bad))
    for (fam, tag), (n, b) in sorted(per.items()):
        lines.append("  %-7s %-22s %5d cases %d mismatches" % (fam, tag, n, b))
    lines.append("calls compared: XP_Compute %d, PLAYER_AddExperience %d, MERC_AddExp %d; shares %d" % (
        evn.get("XC", 0), evn.get("AE", 0), evn.get("MA", 0), evn.get("SHARE", 0)))
    lines.append("shares by n (cases with n >= 2 reaching a member): %s" % sorted(calls["members"].items()))
    for k in ("n1_self", "n1_other", "fatal", "levelup", "merc", "ftol0", "ftol1"):
        lines.append("%s %d" % (k, calls[k]))
    lines.append("controls (cases failed; tags that fail):")
    for k in ctl:
        lines.append("  %-11s %5d  %s" % (k, ctl_fail[k], " ".join("%s:%d" % x for x in sorted(ctl_sep[k].items())[:14])))
    unacc = sorted(a for a in reads if not in_image(a[1]))
    lines.append("traced reads outside spec and case memory: %d, not image constants: %d" % (len(reads), len(unacc)))
    for a in sorted(reads):
        lines.append("  R pc %08x addr %08x size %d count %d%s" % (a + ("" if in_image(a[1]) else " UNACCOUNTED",)))
    lines.append("traced writes outside spec and case memory: %d" % len(writes))
    for a in sorted(writes):
        lines.append("  W pc %08x addr %08x size %d count %d" % a)
    lines.extend(wrap_table())
    for x in first:
        lines.append("MISMATCH " + x)
    print("\n".join(lines))
    fail = bad or unacc or writes or any(v == 0 for v in ctl_fail.values())
    print("RESULT %s" % ("FAIL" if fail else "PASS"))
    return 1 if fail else 0


def cmd_manifest(d, write):
    rows = []
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if os.path.isfile(p) and not name.startswith("manifest"):
            rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), name))
    text = "\n".join(rows) + "\n"
    if write:
        with open(os.path.join(d, "manifest.txt"), "w") as f:
            f.write(text)
    print(text, end="")
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("cases", "check", "manifest", "static"))
    ap.add_argument("--exe", default=os.path.join(ROOT, "workspace", "install", "app", "game.exe"))
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    ns = ap.parse_args(argv[1:])
    if ns.cmd == "static":
        return cmd_static(ns.dir, ns.exe)
    if ns.cmd == "cases":
        return cmd_cases(ns.dir)
    if ns.cmd == "check":
        return cmd_check(ns.dir)
    return cmd_manifest(ns.dir, ns.write)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

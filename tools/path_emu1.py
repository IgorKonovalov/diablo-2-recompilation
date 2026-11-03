#!/usr/bin/env python3
"""Plan 0054 Phase 1.1 (`lane/r54a`): PathPlan's entry, its helpers and the path record's setters, run under Ghidra's
p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java over declared images built from predicted
room grids, and compared with the models below. No game run, no slot. docs/findings/path/0001-pathplan-register.md.

    python3 -I tools/path_emu1.py grids  [--dir D]     predict the room grids (tools/collision.py's activation model on
                                                       two kept run:2026-10-14-collision logs) into D/grid-*.bin
    python3 -I tools/path_emu1.py cases  [--dir D]     write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/path_emu1.py check  [--dir D]     compare every D/<family>.out with its model, account for every
                                                       traced access, run the negative and site controls
    python3 -I tools/path_emu1.py manifest [--dir D] [--write]

Default D: workspace/logs/r54a/emu. Every case draw comes from random.Random("r54a-<family>"); `cases` reads the grids
`grids` wrote, so both regenerate identical files.

The emulation image (plan 0054 P1.1). Eight active rooms, as DungeonRoom records (re/types/collision.h) written by
the memory spec once (`const`): two 2 x 2 blocks of 40 x 40-subtile rooms whose cells are the activation model of
tools/collision.py (`World.model`, COLL_MapBuild from the logged tile entries and the DT1 bytes, which the model
reproduces cell for cell in those logs) for one game of each log: block T, Act III town (level 75) beside Jungle 1
(level 76) (collision-s3); block J, Act I Jail 1 (level 29) (collision-s6). Each block is written twice: as predicted
(rooms 0-3, 4-7 ... see ROOMS), and with unit marks stamped in (PATH_SetMarkMask's player 0x80 and monster 0x100 as
the plus and 3 x 3 footprints, at seeded spots), so a plan meets other units on the grid. Each room's near list is
its own block (self included), as DUNGEON_NearRoomsBuild leaves for four mutually adjacent rooms; the DRLG room's
level (+0x10 -> +0x58 -> +0x1D0) carries the level id RoomIsTown reads. Units, paths, targets, the MonStats and
MonStats2 fields and the DataTables pointer (0x00744304, an input on purpose) are written per case.

Families (function; boundaries observed, ADR-0021):
  plan     0x00649970 sub_00649970_PathPlan(path, unit, force): the entry checks, PathTargetRefresh 0x006498A0 (and
           its object step 0x006497D0), the target-room lookup, PathTargetNotTown, the unit unmark, the target unmark,
           the flag-0x1000 free-target step (0x00648120, 0x00648050 for a player), the path's +0x18 / +0x24 / +0x28 /
           +0x54 writes, the slot read; and, for a path with flag 0x40000, PathPlanStraight 0x00649760 with type 4 run
           through PathPlanToUnit 0x006492F0 and PathAimNextPoint to the return. Boundaries: UNIT_CollUnmark
           0x00649560 (a unit whose unmark marks the grid), the IsBadCodePtr import (IAT slot 0x006CC34C, observed at
           the slot's value in the emulator image, 0x00303946; its argument is the planner g_PathPlanFuncs[type]),
           UNIT_CollMark 0x00649400 (the re-mark after a refused free step), 0x00679190 (the +0x68 target offset: x87,
           not emulated evidence), PathPlanRandomWalk 0x0067A240 and PathPlanSpiral 0x0067A140 (types 10, 14).
  free     0x00648120 (EAX ctx) direct: the free-target step and the player extension 0x00648050.
  town     0x006483A0 sub_006483A0_PathTargetNotTown (ECX unit, ESI ctx) direct, the midpoint branch included.
  outside  0x00647FB0 (ECX path) direct: flag bit 0 when a point lies outside the path's room.
  settype  0x00648CF0 sub_00648CF0_PathSetType(path, type): the flags copy, the saved type and speed, +0x98; the four
           asserts observed at 0x00408090 (their line numbers).
  setters  0x00648E70 PathSetByte90, 0x00649070 PathSetStopDist, 0x006490E0 PathSetByte94, 0x00649140 (+0x94 add),
           0x00648E40 PathSetKnockDist, 0x00648F00 (+0x92, assert on a typed path observed at 0x00408090).
  aim      0x0064FE40 sub_0064FE40_PathAimNextPoint (ECX path, EDX f, arg) direct, with PathDirection 0x0064FC60 and
           the facing step 0x006485F0.
  replan   0x00650350 sub_00650350_PathReplan(unit, flag) to its first boundary: PathPlan 0x00649970 (sites
           0x006503CE, 0x006503E2) or UnitMarkUpdated 0x0064C040.
  create   0x00554850 sub_00554850_SUnitPathCreate(ECX unit, EDX x; y, game, room, flag) to its first boundary:
           PATH_DynamicCreate 0x00649D00 (types 0, 1, 3), 0x00640E90 (objects), 0x00620AE0 / 0x00553060 (items,
           type 5).

Domain (the case writers resample outside it): every collision test point lies inside a room at least one subtile
from that room's edge for the plus and 3 x 3 patterns (the edge branches of COLL_PlusTestBool and the rectangle split of
COLL_RectTestBool are drlg/collision's, not modelled here); no assert input except where a family observes the
assert; no target unit whose unmark would mark the grid (the claim stops at the unit's unmark instead).

Controls (each must fail every case it separates): plan `cmp` (the 100-subtile window as >= 100), `force` (the town
refusal ignores the third argument), `npc` (MonIsNpc ignored); free `noalt` (no alternate directions), `ext4` (the
player extension stops at 4), `sign` (PathDirCell's minor term as a sign instead of `& 1`); town `floor` (the midpoint rounds down instead of toward zero), `npc`; outside `le`;
settype `mask` (bits 8..17 replaced instead of 8..18); setters `cap` (0x4E for 0x4D); aim `face0` (no facing step),
`sar7`; replan `swap` (13 and 2 swapped); create `act` (<= for < in DRLG_ActFromLevelId); and the site control
(every call site one byte later) for every boundary case.

Not covered (ADR-0021): every planner (g_PathPlanFuncs; P1.2 / P1.3), everything after the IsBadCodePtr call in
PathPlan (the planner call, the re-marks, PathAimNextPoint on the planned points, 0x00647FB0, the +0x14 / +0x10 copies,
flag 0x20 and the return: an import sits between the slot read and the planner call, so the program's own flow cannot
pass it here), UNIT_CollUnmark and UNIT_CollMark themselves, the x87 offset 0x00679190, PATH_DynamicCreate (it
allocates first) and every callee after a boundary. Stdlib only.
"""
import argparse
import hashlib
import json
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r54a", "emu")
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
PINNED = "631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf"
LOGS = os.path.join(ROOT, "workspace", "logs")
BLOCKS = (   # (name, log, level ids, the top-left subtile (x0, y0) of a 2 x 2 block, room side in subtiles)
    ("T", "collision-s3-2026-normal-a3.log", (75, 76), (5160, 4960), 40),
    ("J", "collision-s6-2026-normal-a1.log", (29,), (17560, 5060), 60),
)

# ---------------------------------------------------------------------------------------------- the image layout
UNIT = 0x12100000
UPATH = 0x12200000
TARGET = 0x12400000
TPATH = 0x12B00000
OBJDATA = 0x12C00000
OBJREC = 0x12D00000
MSBASE = 0x12600000
MS2BASE = 0x12900000
DTBL = 0x12A00000
CTX = 0x12700000
GAMEP = 0x12000000
G_DATATABLES = 0x00744304
ROOM0 = 0x13000000          # DungeonRoom i at ROOM0 + 0x1000 i; its near array at +0x100
DRLG0 = 0x13100000          # DRLG room i at DRLG0 + 0x100 i (+0x58 -> level)
LEVEL0 = 0x13200000         # level record i at LEVEL0 + 0x400 i (+0x1D0 level id)
MAP0 = 0x14000000           # CollMap i at MAP0 + 0x10000 i (0x24 header, cells at +0x24)
STK_LO = 0x7FEFFF00
STK_LEN = 0x110
EBP_PLAN = 0x7FEFFFFC       # PathPlan's frame pointer (entry ESP 0x7FF00000, push ebp)
CTXS = EBP_PLAN - 0x34      # PathPlan's local request context
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)
IAT_VAL = 0x00303946        # the emulator image's value of the IAT slot 0x006CC34C (IsBadCodePtr)
UNMARK, MARK, X87, RWALK, SPIRAL = 0x00649560, 0x00649400, 0x00679190, 0x0067A240, 0x0067A140
PATHPLAN, MARKUPD, DYNCREATE = 0x00649970, 0x0064C040, 0x00649D00
OBJREC_FN, STATICCREATE, CREATEEND = 0x00640E90, 0x00620AE0, 0x00553060
RET = "ret"

# image tables (read from the pinned file; the models use them and the checker accounts for their traced reads)
TABLES = {
    "slots": (0x006EB6D8, 68), "flags": (0x006EB690, 68), "t98": (0x006EB648, 68), "d8": (0x006EB398, 64),
    "t1648": (0x006F1648, 75), "t490": (0x006EB490 - 160, 324), "dirtab": (0x006EB7E0, 128 * 12),
    "d4d8": (0x006EB7D4, 8), "t548": (0x006EB548, 256), "acts": (0x006EB2F0, 28), "iat": (0x006CC34C, 4),
    "npcmask": (0x006CE268, 12),                                  # MonIsNpc's two flag masks (0x0063E89E, 0x0063E8AF)
    "jt_refresh": (0x00649958, 20), "jt_ptb": (0x0064D994, 24), "jt_plus": (0x0064D784, 52),   # switch tables in .text
    "jt_create": (0x00554A18, 24), "jt_size": (0x0062057C, 24), "jt_town": (0x006426C0, 8 + 0x6D),                    # LevelIsTown's two tables
}


def u32(v):
    return v & 0xFFFFFFFF


def s32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


def s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


class Image:
    """The pinned image's tables."""

    def __init__(self):
        data = open(EXE, "rb").read()
        if hashlib.sha256(data).hexdigest() != PINNED:
            raise SystemExit("path_emu1: not the pinned Game.exe")
        import path_scan
        self.t = {k: path_scan.va_bytes(data, a, n) for k, (a, n) in TABLES.items()}

    def u32(self, k, i):
        return struct.unpack_from("<I", self.t[k], 4 * i)[0]

    def flags(self, t):
        return self.u32("flags", t)

    def slot(self, t):
        return self.u32("slots", t)

    def t98(self, t):
        return self.u32("t98", t)

    def d8(self, d):
        x, y = struct.unpack_from("<ii", self.t["d8"], 8 * d)
        return x, y

    def dirs3(self, idx):
        b = self.t["t1648"]
        return b[3 * idx], b[3 * idx + 1], b[3 * idx + 2]

    def t490(self, i):
        return struct.unpack_from("<i", self.t["t490"], 4 * (i + 40))[0]

    def dirrow(self, q):
        return struct.unpack_from("<iii", self.t["dirtab"], 12 * q)

    def t548(self, i):
        return self.t["t548"][4 * i]

    def acts(self, i):
        return struct.unpack_from("<i", self.t["acts"], 4 * i)[0]


IMG = None


def img():
    global IMG
    if IMG is None:
        IMG = Image()
    return IMG


# ------------------------------------------------------------------------------------------------ the grids
def cmd_grids(d):
    """Predicted grids: tools/collision.py's World on the TL / RRESEED / CB lines of each block's log; per block, the
    four rooms of one game (the last game of the log that holds the block's rects). Writes grid-<block><k>.bin
    (w * h u16 LE, rows of w) and grids.json."""
    import collision
    os.makedirs(d, exist_ok=True)
    meta = {"blocks": []}
    for name, logname, lids, at, side in BLOCKS:
        path = os.path.join(LOGS, logname)
        W = collision.World(os.path.join(ROOT, "workspace", "merged"), None)
        game = 0
        found = {}
        for ln, line in enumerate(open(path, errors="replace"), 1):
            tag, _, rest = line.rstrip("\n").partition(" ")
            if tag == "GP":
                game += 1
                continue
            if tag not in ("TL", "CB", "RRESEED") or not rest.startswith("{"):
                continue
            dd = json.loads(rest)
            W.event(tag, dd, ln, path)
            if tag == "CB":
                m = W.model[dd["room"]]
                found[(game, dd["lid"], m.x0, m.y0, m.w, m.h)] = (list(m.c), ln)
        if W.fail:
            raise SystemExit("path_emu1 grids: the activation model differs from %s" % logname)
        pick = None
        for (g, lid, x0, y0, w, h) in sorted(found, reverse=True):
            if lid not in lids or w != side or h != side:
                continue
            ox, oy = at
            keys = [(g, l2, ox + side * i, oy + side * j, side, side) for j in (0, 1) for i in (0, 1) for l2 in lids]
            have = [k for k in keys if k in found]
            if len(have) == 4:
                pick = have
                break
        if pick is None:
            raise SystemExit("path_emu1 grids: no 2 x 2 block in %s" % logname)
        rooms = []
        for k, key in enumerate(pick):
            cells, ln = found[key]
            fn = "grid-%s%d.bin" % (name, k)
            with open(os.path.join(d, fn), "wb") as f:
                f.write(struct.pack("<%dH" % len(cells), *cells))
            rooms.append({"file": fn, "lid": key[1], "rect": list(key[2:]), "log_line": ln,
                          "nonzero": sum(1 for c in cells if c)})
        meta["blocks"].append({"name": name, "log": logname, "game": pick[0][0], "rooms": rooms,
                               "checks": W.checks, "fail": W.fail})
        print("GRIDS %s %s game=%d rooms=%s checks=%d fail=%d" % (
            name, logname, pick[0][0], " ".join("%d@%d,%d" % (r["lid"], r["rect"][0], r["rect"][1]) for r in rooms),
            W.checks, W.fail))
    with open(os.path.join(d, "grids.json"), "w") as f:
        json.dump(meta, f, indent=1, sort_keys=True)


class Room:
    def __init__(self, i, lid, rect, cells):
        self.i, self.lid = i, lid
        self.x0, self.y0, self.w, self.h = rect
        self.c = cells
        self.addr = ROOM0 + 0x1000 * i
        self.near = []

    def has(self, x, y):
        return self.x0 <= x < self.x0 + self.w and self.y0 <= y < self.y0 + self.h

    def cell(self, x, y):
        return self.c[(y - self.y0) * self.w + (x - self.x0)]


def load_rooms(d):
    meta = json.load(open(os.path.join(d, "grids.json")))
    rooms = []
    for b in meta["blocks"]:
        base = []
        for r in b["rooms"]:
            raw = open(os.path.join(d, r["file"]), "rb").read()
            base.append((r["lid"], r["rect"], list(struct.unpack("<%dH" % (len(raw) // 2), raw))))
        for variant in (0, 1):
            rnd = random.Random("r54a-marks-%s" % b["name"])
            grp = []
            for lid, rect, cells in base:
                c = list(cells)
                if variant:
                    x0, y0, w, h = rect
                    for _ in range(60):
                        cx, cy = rnd.randrange(1, w - 1), rnd.randrange(1, h - 1)
                        v = rnd.choice((0x80, 0x100))
                        foot = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)) if rnd.random() < 0.5 else \
                            tuple((a, bb) for a in (-1, 0, 1) for bb in (-1, 0, 1))
                        for a, bb in foot:
                            c[(cy + bb) * w + cx + a] |= v
                room = Room(len(rooms), lid, rect, c)
                rooms.append(room)
                grp.append(room)
            for r in grp:
                r.near = list(grp)
    return rooms


def room_spec(rooms):
    """The const directives of the rooms, their near arrays, DRLG rooms, levels and maps."""
    out = []
    for r in rooms:
        a = r.addr
        hdr = struct.pack("<I", a + 0x100) + b"\0" * 12 + struct.pack("<I", DRLG0 + 0x100 * r.i) + b"\0" * 12 + \
            struct.pack("<II", MAP0 + 0x10000 * r.i, len(r.near))
        out.append("const bytes %08x %s" % (a, hdr.hex()))
        out.append("const bytes %08x %s" % (a + 0x4C, struct.pack("<iiii", r.x0, r.y0, r.w, r.h).hex()))
        out.append("const bytes %08x %s" % (a + 0x100, b"".join(struct.pack("<I", n.addr) for n in r.near).hex()))
        out.append("const dword %08x %08x" % (DRLG0 + 0x100 * r.i + 0x58, LEVEL0 + 0x400 * r.i))
        out.append("dword %08x %08x" % (LEVEL0 + 0x400 * r.i + 0x1D0, r.lid))   # re-applied: create overrides it
        m = MAP0 + 0x10000 * r.i
        out.append("const bytes %08x %s" % (m, struct.pack("<9I", r.x0, r.y0, r.w, r.h, r.x0 // 5, r.y0 // 5,
                                                            r.w // 5, r.h // 5, m + 0x24).hex()))
        out.append("const bytes %08x %s" % (m + 0x24, struct.pack("<%dH" % len(r.c), *r.c).hex()))
    return out


# ------------------------------------------------------------------------------------------ the collision model
class Domain(Exception):
    pass


def by_addr(rooms):
    return {r.addr: r for r in rooms}


def room_at(R, hint, x, y):
    """sub_00463740_RoomAtSubtile: the hint, else the first of its near list that holds the point."""
    if not hint:
        return 0
    h = R[hint]
    if h.has(x, y):
        return hint
    for n in h.near:
        if n.has(x, y):
            return n.addr
    return 0


def ptb(R, hint, x, y, pattern, mask):
    """COLL_PatternTestBool (0x0064D910): 0 cell, 1 / 3 / 5 plus, 2 / 4 3 x 3, other 1. Non-zero = blocked."""
    x, y = x & 0xFFFF, y & 0xFFFF
    if pattern == 0:                                   # COLL_CellTest: the masked cell, 0x27 without a room
        r = room_at(R, hint, x, y)
        if not r:
            return 0x27
        return R[r].cell(x, y) & mask & 0xFFFF
    if pattern in (1, 3, 5):                           # COLL_PlusTestBool, interior branch only
        r = room_at(R, hint, x, y)
        if not r:
            return 1
        m = R[r]
        if not (m.x0 < x < m.x0 + m.w - 1 and m.y0 < y < m.y0 + m.h - 1):
            raise Domain("plus at an edge")
        return int(any(m.cell(x + a, y + b) & mask for a, b in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))))
    if pattern in (2, 4):                              # COLL_Square3TestBool -> COLL_RectTestBool, one-room rect only
        r = room_at(R, hint, x - 1, y - 1)
        if not r:
            return 1
        m = R[r]
        if not (m.has(x - 1, y - 1) and m.has(x + 1, y + 1)):
            raise Domain("3x3 across a room edge")
        return int(any(m.cell(x + a, y + b) & mask for a in (-1, 0, 1) for b in (-1, 0, 1)))
    return 1


# ------------------------------------------------------------------------------------------------ case memory
class Mem:
    """The case's writes, readable by the models (little-endian), plus the const rooms."""

    def __init__(self, rooms=None):
        self.b = {}
        self.lines = []
        self.rooms = rooms or []
        self.reason = None
        self.refresh = None

    def w(self, addr, data, line=True):
        for k, v in enumerate(data):
            self.b[addr + k] = v
        if line:
            self.lines.append("w %08x %s" % (addr, data.hex()))

    def w8(self, a, v, line=True):
        self.w(a, bytes([v & 0xFF]), line)

    def w16(self, a, v, line=True):
        self.w(a, struct.pack("<H", v & 0xFFFF), line)

    def w32(self, a, v, line=True):
        self.w(a, struct.pack("<I", u32(v)), line)

    def r8(self, a):
        if a not in self.b:
            raise KeyError("model read of an unwritten byte %08x" % a)
        return self.b[a]

    def r16(self, a):
        return self.r8(a) | self.r8(a + 1) << 8

    def r32(self, a):
        return self.r16(a) | self.r16(a + 2) << 16

    def snap(self, a, n):
        return bytes(self.b.get(a + k, 0) for k in range(n))


def put_path(M, p, f):
    """A path record written whole (0x200 bytes): zeros but for the fields in f (offset -> (size, value))."""
    buf = bytearray(0x200)
    for off, (sz, v) in f.items():
        struct.pack_into({1: "<B", 2: "<H", 4: "<I"}[sz], buf, off, v & ((1 << (8 * sz)) - 1))
    M.w(p, bytes(buf))


# ------------------------------------------------------------------------------------------------ the models
def unit_pos(M, u):
    """UnitGetSubX/Y (0x0045ADF0/0x0045AE20): types 2, 4, 5 the static path's dwords +0x0C/+0x10, others the dynamic
    path's words +0x02/+0x06, 0 without a path."""
    t = M.r32(u)
    p = M.r32(u + 0x2C)
    if t == 2 or 4 <= t <= 5:
        return M.r32(p + 0x0C), M.r32(p + 0x10)
    if not p:
        return 0, 0
    return M.r16(p + 2), M.r16(p + 6)


def size_x(M, u):
    """UNIT_GetSizeX (0x00620510)."""
    t = M.r32(u)
    if t == 0:
        return 2
    if t == 1:
        c = s32(M.r32(u + 4))
        dt = M.r32(G_DATATABLES)
        if c < 0 or c >= s32(M.r32(dt + 0xA80)):
            return 0
        i2 = s16(M.r16(M.r32(dt + 0xA78) + 0x1A8 * c + 0x18))
        if i2 < 0 or i2 >= s32(M.r32(dt + 0xA98)):
            return 0
        b = M.r8(M.r32(dt + 0xA90) + 0x134 * i2 + 8)
        return b - 0x100 if b & 0x80 else b
    if t == 2:
        return M.r32(M.r32(M.r32(u + 0x14)) + 0xD0)
    if t == 4:
        return 1
    if t == 5:
        return 0
    raise Domain("size of a type-%d target" % t)


def unmark_noop(M, u):
    """UNIT_CollUnmark(u, 0) returns 0 without a grid access: a player in mode 0 or 17, a monster in mode 0 or 12."""
    t = M.r32(u)
    md = M.r32(u + 0x10)
    if t == 0:
        return md in (0, 0x11)
    if t == 1:
        return md in (0, 0xC)
    return False


def mon_is_npc(M, u):
    """sub_0063E860_MonIsNpc."""
    if not u or M.r32(u) != 1:
        return False
    c = s32(M.r32(u + 4))
    dt = M.r32(G_DATATABLES)
    if c < 0 or c >= s32(M.r32(dt + 0xA80)):
        return False
    rec = M.r32(dt + 0xA78) + 0x1A8 * c
    if not rec:
        return False
    b = M.r8(rec + 0xD)
    if b & img().u32("npcmask", 0) or b & img().u32("npcmask", 2):
        return True
    return s32(M.r32(u + 0xC4)) < 0


def room_is_town(R, r):
    return bool(r) and R[r].lid in (1, 40, 75, 103, 109)


def target_not_town(M, R, u, ctx, neg=None):
    """sub_006483A0_PathTargetNotTown (ECX unit, ESI ctx)."""
    if not u or M.r32(u) != 1:
        return 1
    if neg != "npc" and mon_is_npc(M, u):
        return 1
    r = M.r32(ctx + 0xC)
    if not r:
        sx, sy, tx, ty = M.r16(ctx), M.r16(ctx + 2), M.r16(ctx + 4), M.r16(ctx + 6)
        if neg == "floor":
            my, mx = sy + ((ty - sy) >> 1), sx + ((tx - sx) >> 1)
        else:
            my, mx = sy + int((ty - sy) / 2), sx + int((tx - sx) / 2)
        r1 = room_at(R, M.r32(ctx + 8), mx, my)
        r = room_at(R, r1, tx, ty)
    return 0 if room_is_town(R, r) else 1


def dir_index(a, b, neg=None):
    """0x00678C10: the 5 x 5 direction cell from point a to point b (words x | y << 16). Control `sign`: the minor
    term as the sign (-1, 0, 1) instead of the code's `dy & 1` for a non-negative term."""
    dx = (b & 0xFFFF) - (a & 0xFFFF)
    dy = (b >> 16) - (a >> 16)
    adx, ady = abs(dx), abs(dy)
    if neg == "sign":
        mn = lambda v: (v > 0) - (v < 0)
    else:
        mn = lambda v: -1 if v < 0 else v & 1
    if adx >= 2 * ady:
        dy = mn(dy)
    elif ady >= 2 * adx:
        dx = mn(dx)
    dx = max(-2, min(2, dx))
    dy = max(-2, min(2, dy))
    return 5 * dx + dy + 12


def free_target(M, R, ctx, neg=None, trace=None):
    """0x00648120 (EAX ctx): from the blocked target, step toward the start; the first free point of the main step
    (direction recomputed each round) or of the two alternates (fixed) becomes the target. 0 if the walk reaches the
    start. For a player, 0x00648050 extends the target away from the start while free, to 5 subtiles."""
    I = img()
    path = M.r32(ctx + 0x30)
    u = M.r32(path + 0x30)
    sx, sy = M.r16(ctx), M.r16(ctx + 2)
    tx, ty = M.r16(ctx + 4), M.r16(ctx + 6)
    room, pat, mask = M.r32(ctx + 8), M.r32(ctx + 0x28), M.r32(ctx + 0x2C)
    utype = M.r32(u) if u else 6
    d0, d1, d2 = I.dirs3(dir_index(M.r32(ctx + 4), M.r32(ctx), neg))
    cx, cy = tx, ty
    ax, ay = tx, ty
    bx, by = tx, ty
    found = None
    for _ in range(400):
        if cx == sx and cy == sy:
            return 0
        x, y = I.d8(d0)
        cx, cy = (cx + x) & 0xFFFF, (cy + y) & 0xFFFF
        if trace is not None:
            trace.append(("main", cx, cy))
        if not ptb(R, room, cx, cy, pat, mask):
            found = (cx, cy)
            break
        if neg != "noalt":
            x, y = I.d8(d1)
            ax, ay = (ax + x) & 0xFFFF, (ay + y) & 0xFFFF
            if not ptb(R, room, ax, ay, pat, mask):
                found = (ax, ay)
                break
            if d2 != 0xFF:
                x, y = I.d8(d2)
                bx, by = (bx + x) & 0xFFFF, (by + y) & 0xFFFF
                if not ptb(R, room, bx, by, pat, mask):
                    found = (bx, by)
                    break
        d0 = I.dirs3(dir_index(cx | cy << 16, M.r32(ctx), neg))[0]
    else:
        raise Domain("free walk too long")
    M.w16(ctx + 4, found[0], False)
    M.w16(ctx + 6, found[1], False)
    if found == (sx, sy):
        return 0
    if utype == 0:
        extend_player(M, R, ctx, neg)
    return 1


def extend_player(M, R, ctx, neg=None):
    """0x00648050 (ESI ctx)."""
    I = img()
    sx, sy, tx, ty = M.r16(ctx), M.r16(ctx + 2), M.r16(ctx + 4), M.r16(ctx + 6)
    dx, dy = tx - sx, ty - sy
    adx, ady = abs(dx), abs(dy)
    lim = 4 if neg == "ext4" else 5
    if adx >= 5 or ady >= 5 or (adx == 0 and ady == 0):
        return
    stx, sty = I.t490(dx + 9 * dy), I.t490(dy + 9 * dx)
    room, pat, mask = M.r32(ctx + 8), M.r32(ctx + 0x28), M.r32(ctx + 0x2C)
    m = max(adx, ady)
    x, y = tx, ty
    while m < lim:
        y += sty
        x += stx
        if ptb(R, room, x, y, pat, mask):
            return
        m += 1
        M.w16(ctx + 4, x, False)
        M.w16(ctx + 6, y, False)


def face(M, p, d):
    """0x006485F0 (ECX path, DL direction)."""
    I = img()
    d &= 0x3F
    u = M.r32(p + 0x30)
    t = M.r32(u) if u else 6
    if t in (2, 4):
        M.w8(p + 0x64, d, False)
    elif t == 3:
        if not M.r32(p + 0x34) & 0x40:
            M.w8(p + 0x64, d, False)
    else:
        if d == M.r8(p + 0x65):
            return
        M.w8(p + 0x65, d, False)
        M.w8(p + 0x66, I.t548((d - M.r8(p + 0x64)) & 0x3F), False)


def path_direction(x0, y0, x1, y1):
    """sub_0064FC60_PathDirection (16.16 positions): the g_PathDirTable unit vector and the 64-step direction."""
    I = img()
    if x0 > x1:
        xmax, xmin, sxp = x0, x1, 0
    else:
        xmax, xmin, sxp = x1, x0, 1
    if y0 > y1:
        ymax, ymin, syp = y0, y1, 0
    else:
        ymax, ymin, syp = y1, y0, 1
    dx, dy = s32(xmax - xmin), s32(ymax - ymin)
    if dx <= dy:
        a, b, c, e, swap = xmax, xmin, ymax, ymin, 0
    else:
        a, b, c, e, swap = ymax, ymin, xmax, xmin, 1
    maj = s32(c - e)
    if maj == 0:
        q = 0
    else:
        num = s32(u32((a - b) * 0x7F))
        q = int(num / maj)
    t0, t1, t2 = I.dirrow(q)
    if swap:
        vx, vy, d = t1, t0, (-1 - t2) & 0xF
    else:
        vx, vy, d = t0, t1, t2
    if not syp:
        vy = -vy
        d = (-1 - d) & 0x1F
    if sxp:
        d = (-1 - d) & 0x3F
    else:
        vx = -vx
    return vx, vy, (d + 8) & 0x3F


def aim(M, p, f2, arg, neg=None):
    """sub_0064FE40_PathAimNextPoint (ECX path, EDX f2, [esp+4] arg)."""
    I = img()
    i = s32(M.r32(p + 0x24))
    px = u32((M.r16(p + 0x9C + 4 * i) << 16) + 0x8000)
    py = u32((M.r16(p + 0x9E + 4 * i) << 16) + 0x8000)
    if px == M.r32(p):
        posy = M.r32(p + 4)
        while True:
            if py != posy:
                break
            n = s32(M.r32(p + 0x28))
            if i >= n - 1:
                v4, v8 = struct.unpack("<ii", I.t["d4d8"])
                M.w32(p + 0x6A, v4, False)
                M.w32(p + 0x72, v4, False)
                M.w32(p + 0x24, n, False)
                M.w32(p + 0x6E, v8, False)
                M.w32(p + 0x76, v8, False)
                M.w32(p + 0x7C, 0, False)
                return 1
            i += 1
            M.w32(p + 0x24, i, False)
            px = u32((M.r16(p + 0x9C + 4 * i) << 16) + 0x8000)
            py = u32((M.r16(p + 0x9E + 4 * i) << 16) + 0x8000)
            if px != M.r32(p):
                break
    vx, vy, d = path_direction(M.r32(p), M.r32(p + 4), px, py)
    M.w32(p + 0x6A, vx, False)
    M.w32(p + 0x6E, vy, False)
    if M.r32(p + 0x34) & 0x200:
        d = (d - 0x20) & 0x3F
    v = s32(M.r32(p + 0x7C))
    sh = 7 if neg == "sar7" else 8
    stx, sty = s32(u32(v * vx)) >> sh, s32(u32(v * vy)) >> sh
    M.w32(p + 0x72, stx, False)
    M.w32(p + 0x76, sty, False)
    reached = int((px >> 16) == (u32(M.r32(p) + stx) >> 16) and (py >> 16) == (u32(M.r32(p + 4) + sty) >> 16))
    if neg != "face0" and (arg or (reached and f2)):
        face(M, p, d)
    return reached


def plan_to_unit(M, R, p):
    """sub_006492F0_PathPlanToUnit (ESI path)."""
    M.w32(p + 0x24, 0, False)
    t = M.r32(p + 0x58)
    if t:
        x, y = unit_pos(M, t)
        M.w16(p + 0x10, x, False)
        M.w16(p + 0x12, y, False)
    tx, ty = M.r16(p + 0x10), M.r16(p + 0x12)
    sx, sy = M.r16(p + 2), M.r16(p + 6)
    if abs(sx - tx) >= 100 or abs(sy - ty) >= 100 or tx == 0 or ty == 0:
        return 0
    M.w32(p + 0x9C, M.r32(p + 0x10), False)
    M.w32(p + 0x28, 1, False)
    M.w32(p + 0x38, 0, False)
    aim(M, p, 1, 1)
    r = M.r32(p + 0x1C)
    if not r or not R[r].has(tx, ty):
        M.w32(p + 0x34, M.r32(p + 0x34) | 1, False)
    return M.r32(p + 0x28)


def target_refresh(M, R, p):
    """0x006498A0 (EBX ctx): the target unit's position into path +0x10/+0x12; 0 (no position), 1 or 2, or the x87
    boundary (OBS) for a player or monster target with +0x68 set."""
    t = M.r32(p + 0x58)
    if not t:
        M.refresh = "no target"
        return 1, None
    x, y = unit_pos(M, t)
    M.refresh = "target type %d" % M.r32(t)
    M.w16(p + 0x10, x, False)
    M.w16(p + 0x12, y, False)
    if (x & 0xFFFF) == 0 and (y & 0xFFFF) == 0:
        return 0, None
    tt = M.r32(t)
    if tt > 4:
        return 1, None
    if tt in (0, 1):
        if M.r8(p + 0x68):
            return None, ("obs", X87, 0x00649950, [], {"ecx": p})
        return 1, None
    if tt == 3:
        return 1, None
    if tt == 4:
        return 2, None
    rec = M.r32(M.r32(t + 0x14))
    if not M.r8(rec + 0x13A):
        return 2, None
    M.refresh = "object, 2-subtile step on %s" % ("y" if M.r8(rec + 0x13C) == 1 else "x")
    if M.r8(rec + 0x13C) == 1:                         # 0x006497D0: 2 subtiles toward the start on one axis
        ty_full = M.r32(M.r32(t + 0x2C) + 0x10)
        M.w16(p + 0x12, M.r16(p + 0x12) + (0xFFFE if M.r16(p + 6) < ty_full else 2), False)
    else:
        tx_full = M.r32(M.r32(t + 0x2C) + 0x0C)
        M.w16(p + 0x10, M.r16(p + 0x10) + (0xFFFE if M.r16(p + 2) < tx_full else 2), False)
    return 2, None


def m_plan(M, R, p, u, force, neg=None, observe_unmark=True):
    """sub_00649970_PathPlan to its first boundary or its return. Returns (outcome, ctx written?)."""
    I = img()
    if not p:
        M.reason = "no path"
        return (RET, 0), False
    flags = M.r32(p + 0x34)
    if flags & 0x40000:
        t = M.r32(p + 0x3C)
        if t == 4:
            n = plan_to_unit(M, R, p)
            if n:
                M.reason = "type 4: one point"
                M.w32(p + 0x34, M.r32(p + 0x34) | 0x20, False)
                return (RET, M.r32(p + 0x28)), False
            M.reason = "type 4: refused"
            M.w32(p + 0x34, M.r32(p + 0x34) & ~0x20, False)
            return (RET, 0), False
        if t == 10:
            M.reason = "type 10: random walk"
            return ("obs", RWALK, 0x006497B1, [], {"ecx": p, "edx": u + 0x20}), False
        if t == 14:
            M.reason = "type 14: spiral"
            return ("obs", SPIRAL, 0x0064979E, [], {"ecx": p, "edx": u + 0x20}), False
        raise Domain("straight type %d" % t)
    M.w16(p + 0x54, 0, False)
    tgt = M.r32(p + 0x58)
    if tgt:
        x, y = unit_pos(M, tgt)
        if x == 0 or y == 0:
            M.reason = "target unit at 0"
            return (RET, 0), False

    def fail():
        M.w32(p + 0x24, 0, False)
        M.w32(p + 0x28, 0, False)
        M.w32(p + 0x34, M.r32(p + 0x34) & ~0x20, False)
        return (RET, 0)

    sx, sy = M.r16(p + 2), M.r16(p + 6)
    if sx == 0 and sy == 0:
        M.reason = "start 0"
        return fail(), False
    c = CTXS
    M.w32(c + 0x00, sx | sy << 16, False)
    M.w32(c + 0x24, M.r32(p + 0x44), False)
    M.w32(c + 0x28, M.r32(p + 0x48), False)
    M.w32(c + 0x2C, M.r32(p + 0x50), False)
    M.w32(c + 0x18, M.r8(p + 0x91), False)
    M.w8(c + 0x1C, M.r8(p + 0x92), False)
    M.w32(c + 0x30, p, False)
    b14, obs = target_refresh(M, R, p)
    if obs:
        M.reason = "x87 offset"
        return obs, "early"
    M.w8(c + 0x14, b14, False)
    tx, ty = M.r16(p + 0x10), M.r16(p + 0x12)
    if tx == 0 and ty == 0:
        M.reason = "target 0"
        return fail(), "early"
    M.w32(c + 4, tx | ty << 16, False)
    if tx == sx and ty == sy:
        M.reason = "target = start"
        return fail(), "target"
    dx, dy = tx - sx, ty - sy
    if neg == "cmp":
        if dx >= 100 or -dx >= 100 or dy >= 100 or -dy >= 100:
            M.reason = "window"
            return fail(), "target"
    elif dx > 100 or -dx > 100 or dy > 100 or -dy > 100:
        M.reason = "window"
        return fail(), "target"
    room = M.r32(p + 0x1C)
    M.w32(c + 8, room, False)
    troom = room_at(R, room, tx, ty)
    M.w32(c + 0xC, troom, False)
    if not room or not troom:
        M.reason = "no room"
        return fail(), "rooms"
    ok = target_not_town(M, R, u, c, neg if neg == "npc" else None)
    if not ok and (force == 0 or neg == "force"):
        M.reason = "town"
        return fail(), "rooms"
    t = M.r32(p + 0x3C)
    M.w32(c + 0x20, t, False)
    if observe_unmark:
        M.reason = "to the unit unmark" + (" (forced past town)" if not ok else "")
        return ("obs", UNMARK, 0x00649B0C, [u, 0], {}), "full"
    if not unmark_noop(M, u):
        raise Domain("unit unmark")
    if tgt and size_x(M, tgt) and flags & 0x800:
        if not unmark_noop(M, tgt):
            raise Domain("target unmark")
    go = 1
    if flags & 0x1000:
        if ptb(R, room, tx, ty, M.r32(p + 0x48), M.r32(p + 0x50)):
            go = free_target(M, R, c, None)
    M.w16(p + 0x18, M.r16(c + 4), False)
    M.w16(p + 0x1A, M.r16(c + 6), False)
    M.w32(p + 0x24, 0, False)
    M.w32(p + 0x28, 0, False)
    if go:
        M.reason = "to the slot" + (" (target moved)" if (M.r16(c + 4), M.r16(c + 6)) != (tx, ty) else "") + (" (forced past town)" if not ok else "")
        return ("obs", IAT_VAL, 0x00649B93, [I.slot(t)], {}), "full"
    M.reason = "free step reached the start"
    return ("obs", MARK, 0x00649BE5, [u], {}), "full"


# ---------------------------------------------------------------------------------------------- the generators
MASKS = (0x1C09, 0x3C01, 0x3401, 0x1C01, 0x0804, 0x0409, 0x0001, 0x0000, 0xFFFF, 0x0100, 0x0080, 0x0004)


def put_tables(M, rnd, classes):
    """DataTables (+0xA78 MonStats base, +0xA80 count, +0xA90 MonStats2 base, +0xA98 count) and, per class, the
    MonStats byte +0x0D and word +0x18 and the MonStats2 SizeX byte +0x08."""
    M.w32(G_DATATABLES, DTBL)
    cnt = 24
    M.w32(DTBL + 0xA78, MSBASE)
    M.w32(DTBL + 0xA80, cnt)
    M.w32(DTBL + 0xA90, MS2BASE)
    M.w32(DTBL + 0xA98, 16)
    for c in sorted(set(classes)):
        if 0 <= c < cnt:
            rec = MSBASE + 0x1A8 * c
            M.w8(rec + 0xD, rnd.choice((0, 0, 0, 1, 4, 5, 2, 8, 0x10)))
            i2 = rnd.choice((c % 16, c % 16, -1, 17))
            M.w16(rec + 0x18, i2)
            if 0 <= i2 < 16:
                M.w8(MS2BASE + 0x134 * i2 + 8, rnd.choice((0, 1, 2, 3, 0xFF)))


def put_unit(M, rnd, addr, typ, path, pos, mode=None, cls=None, static=False):
    M.w32(addr, typ)
    M.w32(addr + 4, cls if cls is not None else rnd.randrange(0, 30))
    M.w32(addr + 0x10, mode if mode is not None else rnd.randrange(0, 20))
    M.w32(addr + 0xC4, rnd.choice((0, 0, 0x80000000, 0x1, 0x80000004)))
    M.w32(addr + 0x2C, path)
    if path and pos is not None:
        if static:
            M.w(path, b"\0" * 0x20)
            M.w32(path + 0x0C, pos[0])
            M.w32(path + 0x10, pos[1])
        else:
            buf = bytearray(0x40)
            struct.pack_into("<HHHH", buf, 0, 0, pos[0] & 0xFFFF, 0, pos[1] & 0xFFFF)
            M.w(path, bytes(buf))


def interior(rnd, r, m=3):
    return rnd.randrange(r.x0 + m, r.x0 + r.w - m), rnd.randrange(r.y0 + m, r.y0 + r.h - m)


def near_point(rnd, sx, sy):
    k = rnd.random()
    if k < 0.08:
        return sx, sy
    if k < 0.25:
        return sx + rnd.randrange(-105, 106), sy + rnd.randrange(-105, 106)
    if k < 0.35:
        e = rnd.choice((99, 100, 101, -99, -100, -101))
        return (sx + e, sy + rnd.randrange(-20, 21)) if rnd.random() < 0.5 else (sx + rnd.randrange(-20, 21), sy + e)
    return sx + rnd.randrange(-25, 26), sy + rnd.randrange(-25, 26)


def gen_plan(rnd, rooms, live, n=600):
    R = by_addr(rooms)
    I = img()
    out = []
    while len(out) < n:
        M = Mem(rooms)
        utype = rnd.choice((0, 0, 0, 1, 1, 1, 1, 3)) if live else rnd.choice((0, 1))
        noop = not live
        mode = rnd.choice((0, 0x11) if utype == 0 else (0, 0xC)) if noop else rnd.choice((1, 2, 3, 4, 6))
        room = rnd.choice(rooms)
        sx, sy = interior(rnd, room)
        if rnd.random() < 0.03:
            sx, sy = 0, 0
        tx, ty = near_point(rnd, sx, sy)
        if rnd.random() < 0.12:             # the 100-subtile window inside a 120-subtile block (J): |d| 99, 100, 101
            room = rnd.choice([r for r in rooms if r.w == 60])
            bx0 = min(r.x0 for r in room.near)
            by0 = min(r.y0 for r in room.near)
            e = rnd.choice((99, 100, 101))
            if rnd.random() < 0.5:
                sx, sy = bx0 + rnd.randrange(3, 16), by0 + rnd.randrange(3, 117)
                tx, ty = sx + e, sy + rnd.randrange(-2, 3)
                if rnd.random() < 0.5:
                    sx, tx = tx, sx
            else:
                sx, sy = bx0 + rnd.randrange(3, 117), by0 + rnd.randrange(3, 16)
                tx, ty = sx + rnd.randrange(-2, 3), sy + e
                if rnd.random() < 0.5:
                    sy, ty = ty, sy
            room = [r for r in room.near if r.has(sx, sy)][0]
        if rnd.random() < 0.15:             # a hostile monster's target in a town room (block T, level 75)
            room = rnd.choice([r for r in rooms if r.lid == 76])
            sx, sy = interior(rnd, room)
            twn = rnd.choice([r for r in room.near if r.lid == 75])
            tx, ty = interior(rnd, twn)
        if rnd.random() < 0.03:
            tx = 0
        t = rnd.randrange(0, 17)
        flags = I.flags(t) if rnd.random() < 0.8 else rnd.choice((0, 0x1000, 0x800, 0x1800, 0x21900, 0x100))
        if t in (4, 10, 14) and rnd.random() < 0.2:
            flags &= ~0x40000
        if flags & 0x40000 and t not in (4, 10, 14):
            flags &= ~0x40000
        flags |= rnd.choice((0, 0, 0x10, 0x1, 0x20, 0x200, 0x4000, 0x31))
        tgt = 0
        ttype = None
        if rnd.random() < 0.45:
            tgt = TARGET
            ttype = rnd.choice((0, 0, 1, 1, 2, 2, 3, 4, 5))
            if noop and ttype == 3:
                ttype = 4
        cls = rnd.randrange(0, 24) if rnd.random() < 0.9 else rnd.choice((-1, 30))
        tcls = rnd.randrange(0, 24)
        path = {0x02: (2, sx), 0x06: (2, sy), 0x10: (2, tx), 0x12: (2, ty), 0x1C: (4, 0 if rnd.random() < 0.04 else
                                                                                       room.addr),
                0x30: (4, UNIT), 0x34: (4, flags), 0x3C: (4, t), 0x44: (4, rnd.randrange(0, 4)),
                0x48: (4, rnd.choice((0, 1, 2, 3, 4, 5, 1, 2, 6))), 0x50: (4, rnd.choice(MASKS)),
                0x58: (4, tgt), 0x68: (1, 0 if rnd.random() < 0.85 else rnd.randrange(1, 20)),
                0x91: (1, rnd.randrange(0, 78)), 0x92: (1, rnd.randrange(0, 256)),
                0x7C: (4, rnd.choice((0x800, 0x400, 0x1000, 0))), 0x64: (1, rnd.randrange(0, 64)),
                0x65: (1, rnd.randrange(0, 64)), 0x24: (4, rnd.randrange(0, 3)), 0x28: (4, rnd.randrange(0, 3)),
                0x00: (4, (sx << 16) + 0x8000), 0x04: (4, (sy << 16) + 0x8000)}
        put_path(M, UPATH, path)
        put_unit(M, rnd, UNIT, utype, UPATH, None, mode=mode, cls=cls)
        if tgt:
            static = ttype in (2, 4, 5)
            tp = TPATH if rnd.random() < 0.95 or ttype in (2, 4, 5) else 0
            pos = (tx, ty) if rnd.random() < 0.9 else (rnd.choice((0, tx)), rnd.choice((0, ty)))
            tmode = None
            if ttype == 0 and noop:
                tmode = rnd.choice((0, 0x11))
            if ttype == 1 and noop:
                tmode = rnd.choice((0, 0xC))
            put_unit(M, rnd, TARGET, ttype, tp, pos, mode=tmode, cls=tcls, static=static)
            if ttype == 2:
                M.w32(TARGET + 0x14, OBJDATA)
                M.w32(OBJDATA, OBJREC)
                M.w8(OBJREC + 0x13A, rnd.choice((0, 1)))
                M.w8(OBJREC + 0x13C, rnd.choice((0, 1, 2)))
                M.w32(OBJREC + 0xD0, 0)
            if noop and ttype in (3, 4) and flags & 0x800:
                M.w32(UPATH + 0x34, flags & ~0x800)
        put_tables(M, rnd, (cls, tcls))
        force = 1 if rnd.random() < 0.3 else 0
        snap = dict(M.b)
        try:
            want = m_plan(M, R, UPATH, UNIT, force, observe_unmark=live)
        except Domain:
            continue
        M.b = snap
        out.append({"lines": list(M.lines), "b": snap, "force": force})
    return out


# --------------------------------------------------------------------------------------------- free / town / ...
def gen_ctx_case(rnd, rooms, M, utype):
    room = rnd.choice(rooms)
    sx, sy = interior(rnd, room, 4)
    tx, ty = sx + rnd.randrange(-14, 15), sy + rnd.randrange(-14, 15)
    if rnd.random() < 0.1:
        tx, ty = sx + rnd.randrange(-5, 6), sy + rnd.randrange(-5, 6)
    put_path(M, UPATH, {0x30: (4, UNIT), 0x34: (4, rnd.choice((0, 0x1000, 0x21900, 0x10)))})
    M.w32(UNIT, utype)
    buf = bytearray(0x34)
    struct.pack_into("<HHHHII", buf, 0, sx, sy, tx & 0xFFFF, ty & 0xFFFF, room.addr, 0)
    struct.pack_into("<II", buf, 0x28, rnd.choice((0, 1, 2, 3, 4, 5, 0, 1, 2)), rnd.choice(MASKS[:8]))
    struct.pack_into("<I", buf, 0x30, UPATH)
    M.w(CTX, bytes(buf))
    return room


def gen_free(rnd, rooms, n=500, nsep=60):
    """n cases as drawn, then nsep cases kept only when the `sign` control's walk differs from the model's (a target
    along an axis, |dx| >= 2|dy| or the reverse with the minor term even and non-zero, whose third direction is used)."""
    R = by_addr(rooms)
    out = []
    tries = 0
    while len(out) < n + nsep:
        M = Mem(rooms)
        sep = len(out) >= n
        room = gen_ctx_case(rnd, rooms, M, rnd.choice((0, 0, 1, 3)))
        if sep:
            tries += 1
            if tries > 200000:
                raise SystemExit("path_emu1: no separating free case")
            sx, sy = M.r16(CTX), M.r16(CTX + 2)
            a = rnd.choice((6, 8, 10, 12, 14)) * rnd.choice((-1, 1))
            b = rnd.choice((2, 4, 6)) * rnd.choice((-1, 1))
            if abs(b) * 2 > abs(a):
                b = 2 * (1 if b > 0 else -1)
            tx, ty = (sx + a, sy + b) if rnd.random() < 0.5 else (sx + b, sy + a)
            M.w(CTX + 4, struct.pack("<HH", tx & 0xFFFF, ty & 0xFFFF))
        snap = dict(M.b)
        try:
            free_target(M, R, CTX)
            if sep:
                M2 = Mem(rooms)
                M2.b = dict(snap)
                r2 = free_target(M2, R, CTX, "sign")
                M3 = Mem(rooms)
                M3.b = dict(snap)
                r3 = free_target(M3, R, CTX)
                if r2 == r3 and M2.snap(CTX, 52) == M3.snap(CTX, 52):
                    continue
        except Domain:
            continue
        out.append({"lines": list(M.lines), "b": snap})
    return out


def gen_town(rnd, rooms, n=400):
    R = by_addr(rooms)
    out = []
    while len(out) < n:
        M = Mem(rooms)
        r = rnd.choice(rooms)
        sx, sy = interior(rnd, r, 1)
        tx, ty = sx + rnd.randrange(-90, 91), sy + rnd.randrange(-90, 91)
        utype = rnd.choice((1, 1, 1, 1, 0, 3))
        cls = rnd.randrange(0, 24) if rnd.random() < 0.9 else rnd.choice((-1, 40))
        M.w32(UNIT, utype)
        M.w32(UNIT + 4, cls)
        M.w32(UNIT + 0xC4, rnd.choice((0, 0, 0x80000000, 2)))
        troom = room_at(R, r.addr, tx & 0xFFFF, ty & 0xFFFF) if rnd.random() < 0.5 else 0
        hint = r.addr if rnd.random() < 0.95 else 0
        if rnd.random() < 0.15:     # the midpoint on a block's outer edge: trunc and floor give different rooms
            r = rnd.choice([q for q in rooms if q.lid == 75])
            hint, troom, utype, cls = r.addr, 0, 1, 3
            k = rnd.randrange(0, 30)
            ey = max(q.y0 + q.h for q in r.near)
            sx = rnd.randrange(r.x0 + 1, r.x0 + r.w - 1)
            sy, tx = ey + k, sx
            ty = sy - (2 * k + 1)
            M.w32(UNIT, utype)
            M.w32(UNIT + 4, cls)
            M.w32(UNIT + 0xC4, 0)
        M.w(CTX, struct.pack("<HHHHII", sx, sy, tx & 0xFFFF, ty & 0xFFFF, hint, troom))
        put_tables(M, rnd, (cls,))
        if cls == 3 and troom == 0 and hint and R[hint].lid == 75:
            M.w8(MSBASE + 0x1A8 * 3 + 0xD, 0)
        out.append({"lines": list(M.lines), "b": dict(M.b)})
    return out


def gen_outside(rnd, rooms, n=300):
    out = []
    for _ in range(n):
        M = Mem(rooms)
        r = rnd.choice(rooms)
        cnt = rnd.choice((0, 1, 2, 3, 5, 8, -1))
        f = {0x1C: (4, r.addr if rnd.random() < 0.9 else 0), 0x28: (4, cnt),
             0x34: (4, rnd.choice((0, 1, 0x21, 0x20, 0x1001)))}
        for k in range(max(cnt, 0)):
            if rnd.random() < 0.8:
                x, y = rnd.randrange(r.x0, r.x0 + r.w), rnd.randrange(r.y0, r.y0 + r.h)
            else:
                x, y = rnd.choice((r.x0 - 1, r.x0, r.x0 + r.w - 1, r.x0 + r.w)), rnd.choice(
                    (r.y0 - 1, r.y0, r.y0 + r.h - 1, r.y0 + r.h))
            f[0x9C + 4 * k] = (2, x)
            f[0x9E + 4 * k] = (2, y)
        put_path(M, UPATH, f)
        out.append({"lines": list(M.lines), "b": dict(M.b)})
    return out


def m_outside(M, R, p, neg=None):
    M.w32(p + 0x34, M.r32(p + 0x34) & ~1, False)
    r = M.r32(p + 0x1C)
    n = s32(M.r32(p + 0x28))
    for i in range(max(n, 0)):
        if not r:
            M.w32(p + 0x34, M.r32(p + 0x34) | 1, False)
            return
        m = R[r]
        x, y = M.r16(p + 0x9C + 4 * i), M.r16(p + 0x9E + 4 * i)
        hi = 1 if neg == "le" else 0
        if not (m.x0 <= x < m.x0 + m.w + hi and m.y0 <= y < m.y0 + m.h + hi):
            M.w32(p + 0x34, M.r32(p + 0x34) | 1, False)
            return


def gen_settype(rnd, n=400):
    out = []
    while len(out) < n:
        M = Mem()
        t = rnd.randrange(0, 17)
        utype = rnd.choice((0, 1, 3, None))
        old = rnd.choice((0, 2, 7, 13, 15, 8, 11, 9, 1))
        f = {0x30: (4, UNIT if utype is not None else 0), 0x34: (4, rnd.choice((0, 0x4000, 0x10000, 0x7FF00, 0x40020,
                                                                                0x14031, 0xFFFFFFFF, 0x21900))),
             0x3C: (4, old), 0x40: (4, rnd.choice((0, 2, 7, 8, 11, 13))), 0x7C: (4, rnd.randrange(0, 0x2000)),
             0x80: (4, rnd.randrange(0, 0x2000)), 0x91: (1, rnd.choice((0, 5, 77, 78, 0x4D, 0x4E, 200)))}
        put_path(M, UPATH, f)
        if utype is not None:
            M.w32(UNIT, utype)
        out.append({"lines": list(M.lines), "b": dict(M.b), "type": t})
    return out


def m_settype(M, p, t, neg=None):
    I = img()
    u = M.r32(p + 0x30)
    if u and M.r32(u) == 0 and t == 2:
        return ("obs", FATAL[0], 0x00648D14, [0x861], {})
    f = I.flags(t)
    old = M.r32(p + 0x34)
    if f & 0x2000 and not old & 0x4000:
        M.w32(p + 0x40, M.r32(p + 0x3C), False)
    if f & 0x8000 and not old & 0x10000:
        M.w32(p + 0x80, M.r32(p + 0x7C), False)
    keep = 0xFFFC00FF if neg == "mask" else 0xFFF800FF
    M.w32(p + 0x34, (old & keep) | f, False)
    M.w32(p + 0x3C, t, False)
    M.w32(p + 0x98, I.t98(t), False)
    v40 = M.r32(p + 0x40)
    if v40 == 0xB:
        return ("obs", FATAL[0], 0x00648D14, [0x871], {})
    if v40 == 8:
        return ("obs", FATAL[0], 0x00648D14, [0x872], {})
    if t == 4 and M.r8(p + 0x91) >= 0x4E:
        return ("obs", FATAL[0], 0x00648D14, [0x873], {})
    return (RET, None)


SETTERS = {0x00648E70: "s90", 0x00649070: "stop", 0x006490E0: "s94", 0x00649140: "a94", 0x00648E40: "knock",
           0x00648F00: "s92"}


def gen_setters(rnd, n=360):
    out = []
    fns = sorted(SETTERS)
    for k in range(n):
        M = Mem()
        fn = fns[k % len(fns)]
        nul = rnd.random() < 0.05 and fn in (0x00648E70, 0x00649070)
        put_path(M, UPATH, {0x3C: (4, rnd.choice((0, 0, 2))), 0x90: (1, rnd.randrange(0, 256)),
                            0x91: (1, rnd.randrange(0, 256)), 0x92: (1, rnd.randrange(0, 256)),
                            0x93: (1, rnd.randrange(0, 256)), 0x94: (1, rnd.randrange(0, 256))})
        if fn == 0x006490E0:
            v = rnd.choice((rnd.randrange(0, 256), 255, 256, 0, 0x1FF))
        elif fn == 0x00649140:
            v = u32(rnd.choice((rnd.randrange(-300, 300), -255, 255, -256, 256, 0)))
        else:
            v = rnd.choice((rnd.randrange(0, 256), 0, 1, 19, 20, 0x4C, 0x4D, 0x4E, 0xFF)) | rnd.choice((0, 0x100,
                                                                                                   0xFFFF00))
        out.append({"lines": list(M.lines), "b": dict(M.b), "fn": fn, "v": v, "p": 0 if nul else UPATH})
    return out


def m_setter(M, fn, p, v, neg=None):
    name = SETTERS[fn]
    b = v & 0xFF
    if name == "s90":
        if not p:
            return (RET, None)
        cap = 0x4E if neg == "cap" else 0x4D
        b = cap if b >= cap else b
        M.w8(p + 0x91, b, False)
        M.w8(p + 0x90, b, False)
    elif name == "stop":
        if not p:
            return (RET, None)
        M.w8(p + 0x93, (b - 1) & 0xFF if ((b - 1) & 0xFF) <= 0x12 else 0, False)
    elif name == "s94":
        if v > 0xFF:
            return ("obs", FATAL[0], 0x006490FF + 5, [0x965], {})
        M.w8(p + 0x94, v, False)
    elif name == "a94":
        s = u32(M.r8(p + 0x94) + v)
        M.w8(p + 0x94, 0 if s & 0x80000000 else (0xFF if s32(s) > 0xFF else s), False)
    elif name == "knock":
        M.w8(p + 0x90, b, False)
    elif name == "s92":
        if M.r32(p + 0x3C):
            return ("obs", FATAL[0], 0x00648F16, [0x8E8], {})
        M.w8(p + 0x92, b, False)
    return (RET, None)


def gen_aim(rnd, rooms, n=500):
    out = []
    while len(out) < n:
        M = Mem()
        sx, sy = rnd.randrange(4000, 6000), rnd.randrange(4000, 6000)
        fx, fy = rnd.choice((0x8000, rnd.randrange(0, 0x10000))), rnd.choice((0x8000, rnd.randrange(0, 0x10000)))
        cnt = rnd.randrange(1, 6)
        i0 = rnd.randrange(0, cnt)
        f = {0x00: (4, (sx << 16) + fx), 0x04: (4, (sy << 16) + fy), 0x24: (4, i0), 0x28: (4, cnt),
             0x30: (4, UNIT if rnd.random() < 0.95 else 0), 0x34: (4, rnd.choice((0, 0x200, 0x40, 0x240, 0x20))),
             0x7C: (4, rnd.choice((0x800, 0x400, 0x1000, 0x100, 0, 0x2000, 0x1800))),
             0x64: (1, rnd.randrange(0, 64)), 0x65: (1, rnd.randrange(0, 64)), 0x66: (1, rnd.randrange(0, 256))}
        x, y = sx, sy
        for k in range(cnt):
            if rnd.random() < 0.25:
                pass
            else:
                x, y = x + rnd.randrange(-12, 13), y + rnd.randrange(-12, 13)
            f[0x9C + 4 * k] = (2, x)
            f[0x9E + 4 * k] = (2, y)
        put_path(M, UPATH, f)
        M.w32(UNIT, rnd.choice((0, 1, 2, 3, 4, 5)))
        out.append({"lines": list(M.lines), "b": dict(M.b), "f2": rnd.choice((0, 1)), "arg": rnd.choice((0, 1, 1))})
    return out


def gen_replan(rnd, n=300):
    out = []
    for _ in range(n):
        M = Mem()
        has = rnd.random() < 0.95
        f = {0x34: (4, rnd.choice((0x10, 0x10, 0, 0x30, 0x20))), 0x3C: (4, rnd.choice((2, 13, 15, 7, 1, 0, 9))),
             0x10: (4, rnd.randrange(0, 1 << 32)), 0x18: (4, rnd.randrange(0, 1 << 32)),
             0x24: (4, rnd.randrange(0, 4)), 0x94: (1, rnd.choice((0, 0, 3, 20)))}
        put_path(M, UPATH, f)
        M.w32(UNIT, rnd.choice((0, 1, 1, 3)))
        M.w32(UNIT + 0x2C, UPATH if has else 0)
        M.w32(UNIT + 0xC4, rnd.choice((0, 2, 0x80000000)))
        out.append({"lines": list(M.lines), "b": dict(M.b), "flag": rnd.choice((0, 1))})
    return out


def m_replan(M, u, flag, neg=None):
    p = M.r32(u + 0x2C)
    if not p:
        return (RET, 0)
    if not M.r32(p + 0x34) & 0x10:
        if M.r32(u) == 1 and M.r8(p + 0x94) == 0:
            return (RET, 0)
        return ("obs", MARKUPD, 0x00650384, [u], {})
    t = M.r32(p + 0x3C)
    if t in (2, 13, 15):
        a, b = (2, 13) if neg == "swap" else (13, 2)
        if flag:
            M.w32(p + 0x3C, a, False)
        else:
            M.w32(p + 0x3C, b, False)
            if neg != "swap":
                M.w32(p + 0x10, M.r32(p + 0x18), False)
        return ("obs", PATHPLAN, 0x006503CE, [p, u, 0], {})
    return ("obs", PATHPLAN, 0x006503E2, [p, u, 0], {})


def gen_create(rnd, rooms, n=300):
    out = []
    for _ in range(n):
        M = Mem(rooms)
        r = rnd.choice(rooms) if rnd.random() < 0.85 else None
        typ = rnd.choice((0, 1, 2, 3, 4, 4, 5))
        M.w(UNIT, b"\0" * 0x20)
        M.w32(UNIT, typ)
        M.w32(UNIT + 4, rnd.randrange(0, 600))
        M.w32(UNIT + 0x10, rnd.choice((0, 3, 1, 4)))
        g = bytearray(0xD0)
        for k in range(5):
            struct.pack_into("<I", g, 0xBC + 4 * k, 0x15000000 + 0x100 * k)
        struct.pack_into("<I", g, 0x1C, 0x16000000)
        M.w(GAMEP, bytes(g))
        lid = None
        if r is not None and rnd.random() < 0.4:   # a level id of the other acts and the bounds of the act table
            lid = rnd.choice((0, 1, 39, 40, 74, 75, 102, 103, 108, 109, 136, 1023, 1024, 5000))
        out.append({"lines": list(M.lines), "b": dict(M.b), "room": r.addr if r else 0, "lid": lid,
                    "x": rnd.randrange(0, 0x10000), "y": rnd.randrange(0, 0x10000), "flag": rnd.choice((0, 1))})
    return out


def m_create(M, R, case, neg=None):
    I = img()
    room = case["room"]
    lid = 0
    if room:
        lid = case["lid"] if case["lid"] is not None else R[room].lid
    act = 0
    for k in range(1, 6):
        if (lid <= I.acts(k)) if neg == "act" else (lid < I.acts(k)):
            act = k - 1
            break
    M.w8(UNIT + 0x18, act, False)
    M.w32(UNIT + 0x1C, M.r32(GAMEP + 0xBC + 4 * act), False)
    typ = M.r32(UNIT)
    x, y = case["x"], case["y"]
    site = {0: 0x005548D0, 1: 0x005548F6, 3: 0x005549AF}
    if typ in site:
        return ("obs", DYNCREATE, site[typ], [M.r32(GAMEP + 0x1C), room, x, y, UNIT, 0], {})
    if typ == 2:
        return ("obs", OBJREC_FN, 0x00554937, [M.r32(UNIT + 4)], {})
    if typ == 4:
        if M.r32(UNIT + 0x10) != 3:
            return ("obs", CREATEEND, 0x005549E8, [], {"ecx": UNIT, "edx": GAMEP})
        return ("obs", STATICCREATE, 0x00554982, [UNIT, room, x, y], {})
    return ("obs", STATICCREATE, 0x005549BD, [UNIT, room, x, y], {})


# ------------------------------------------------------------------------------------------------- the families
FAMILIES = ("plan", "plannoop", "free", "town", "outside", "settype", "setters", "aim", "replan", "create")
CONTROLS = {"plan": ("cmp", "force", "npc"), "plannoop": ("cmp", "force", "npc"), "free": ("noalt", "ext4", "sign"), "town": ("floor", "npc"), "outside": ("le",),
            "settype": ("mask",), "setters": ("cap",), "aim": ("face0", "sar7"), "replan": ("swap",),
            "create": ("act",)}


def family(fam, rooms):
    rnd = random.Random("r54a-" + fam)
    gens = {"plan": lambda: gen_plan(rnd, rooms, True), "plannoop": lambda: gen_plan(rnd, rooms, False), "free": lambda: gen_free(rnd, rooms),
            "town": lambda: gen_town(rnd, rooms), "outside": lambda: gen_outside(rnd, rooms),
            "settype": lambda: gen_settype(rnd), "setters": lambda: gen_setters(rnd),
            "aim": lambda: gen_aim(rnd, rooms), "replan": lambda: gen_replan(rnd), "create": lambda: gen_create(rnd, rooms)}
    cases = gens[fam]()
    room_lines = room_spec(rooms) if fam in ("plan", "plannoop", "free", "town", "outside", "create") else []
    obs = {"plan": (UNMARK, MARK, X87, RWALK, SPIRAL, IAT_VAL), "plannoop": (MARK, X87, RWALK, SPIRAL, IAT_VAL),
           "replan": (PATHPLAN, MARKUPD),
           "create": (DYNCREATE, OBJREC_FN, STATICCREATE, CREATEEND), "settype": (FATAL[0],), "setters": (FATAL[0],)}
    mem = room_lines + ["observe %08x" % a for a in obs.get(fam, ())]
    guards = [a for a in FATAL + ALLOC if a not in obs.get(fam, ())]
    mem += ["guard %08x" % a for a in guards]
    blocks = []
    for c in cases:
        L = list(c["lines"])
        if fam in ("plan", "plannoop"):
            L += ["d %08x %d" % (STK_LO, STK_LEN), "d %08x 512" % UPATH,
                  "call %08x 00000000 00000000 %08x %08x %08x" % (PATHPLAN, UPATH, UNIT, c["force"])]
        elif fam == "free":
            L += ["r EAX %08x" % CTX, "d %08x 52" % CTX, "call 00648120 00000000 00000000"]
        elif fam == "town":
            L += ["r ESI %08x" % CTX, "call 006483a0 %08x 00000000" % UNIT]
        elif fam == "outside":
            L += ["d %08x 512" % UPATH, "call 00647fb0 %08x 00000000" % UPATH]
        elif fam == "settype":
            L += ["d %08x 512" % UPATH, "call 00648cf0 00000000 00000000 %08x %08x" % (UPATH, c["type"])]
        elif fam == "setters":
            L += ["d %08x 512" % UPATH, "call %08x 00000000 00000000 %08x %08x" % (c["fn"], c["p"], c["v"])]
        elif fam == "aim":
            L += ["d %08x 512" % UPATH, "call 0064fe40 %08x %08x %08x" % (UPATH, c["f2"], c["arg"])]
        elif fam == "replan":
            L += ["d %08x 512" % UPATH, "call 00650350 00000000 00000000 %08x %08x" % (UNIT, c["flag"])]
        elif fam == "create":
            L += ["d %08x 32" % UNIT, "call 00554850 %08x %08x %08x %08x %08x %08x" % (
                UNIT, c["x"], c["y"], GAMEP, c["room"], c["flag"])]
        blocks.append(L)
    return cases, blocks, mem


def predict(fam, c, rooms, neg=None):
    """(outcome, memory after) for one case: outcome = (RET, eax-or-None) or ("obs", fn, site, args, regs)."""
    R = by_addr(rooms)
    M = Mem(rooms)
    M.b = dict(c["b"])
    try:
        if fam in ("plan", "plannoop"):
            out, stage = m_plan(M, R, UPATH, UNIT, c["force"], neg, observe_unmark=fam == "plan")
            return out, M, stage
        if fam == "free":
            return (RET, free_target(M, R, CTX, neg)), M, None
        if fam == "town":
            return (RET, target_not_town(M, R, UNIT, CTX, neg)), M, None
        if fam == "outside":
            m_outside(M, R, UPATH, neg)
            return (RET, None), M, None
        if fam == "settype":
            return m_settype(M, UPATH, c["type"], neg), M, None
        if fam == "setters":
            return m_setter(M, c["fn"], c["p"], c["v"], neg), M, None
        if fam == "aim":
            return (RET, aim(M, UPATH, c["f2"], c["arg"], neg)), M, None
        if fam == "replan":
            return m_replan(M, UNIT, c["flag"], neg), M, None
        if fam == "create":
            if c["lid"] is not None and c["room"]:
                pass
            return m_create(M, R, c, neg), M, None
    except Domain:
        return None, M, None
    raise ValueError(fam)


def cmd_cases(d):
    rooms = load_rooms(d)
    for fam in FAMILIES:
        cases, blocks, mem = family(fam, rooms)
        if fam == "create":   # a declared level id overrides the room's level record for that case
            for c, L in zip(cases, blocks):
                if c["lid"] is not None and c["room"]:
                    r = by_addr(rooms)[c["room"]]
                    L.insert(0, "w %08x %s" % (LEVEL0 + 0x400 * r.i + 0x1D0, struct.pack("<I", u32(c["lid"])).hex()))
        with open(os.path.join(d, fam + ".cases"), "w") as f:
            for L in blocks:
                f.write("\n".join(L) + "\n")
        with open(os.path.join(d, fam + ".mem"), "w") as f:
            f.write("\n".join(mem) + "\n")
        print("CASES %s %d" % (fam, len(blocks)))


# ------------------------------------------------------------------------------------------------- the checker
def read_out(path):
    calls, traced = [], []
    for ln in open(path):
        p = ln.split()
        if not p:
            continue
        if p[0] == "C":
            c = {"n": int(p[1]), "dumps": {}}
            if p[3] == "STOP":
                c["stop"] = " ".join(p[4:])
            elif p[3] == "OBS":
                c["obs"] = int(p[4], 16)
                kv = dict(x.split("=") for x in p[5:])
                c["regs"] = {k: int(v, 16) for k, v in kv.items() if k != "steps"}
            else:
                c["obs"] = RET
                kv = dict(x.split("=") for x in p[3:])
                c["eax"] = int(kv["eax"], 16)
            calls.append(c)
        elif p[0] == "A":
            calls[-1]["args"] = bytes.fromhex(p[1])
        elif p[0] == "D":
            calls[-1]["dumps"][int(p[1], 16)] = bytes.fromhex(p[2]) if len(p) > 2 else b""
        elif p[0] in ("R", "W"):
            traced.append(ln.strip())
    return calls, traced


CTX_FIELDS_EARLY = ((0x00, 4), (0x18, 4), (0x1C, 1), (0x24, 4), (0x28, 4), (0x2C, 4), (0x30, 4))
CTX_FIELDS_FULL = CTX_FIELDS_EARLY + ((0x04, 4), (0x08, 4), (0x0C, 4), (0x14, 1), (0x20, 4))


def matches(fam, c, want, M, stage, shift=0):
    if want is None:
        return False
    if want[0] == RET:
        if c.get("obs") != RET or shift:
            return False
        if want[1] is not None:
            eax = c["eax"] & (0xFF if fam == "town" and False else 0xFFFFFFFF)
            if eax != u32(want[1]):
                return False
    else:
        _, fn, site, args, regs = want
        if c.get("obs") != fn:
            return False
        a = c.get("args", b"")
        if struct.unpack_from("<I", a, 0)[0] != site + shift:
            return False
        got = [struct.unpack_from("<I", a, 4 + 4 * k)[0] for k in range(len(args))]
        if got != [u32(x) for x in args]:
            return False
        for k, v in regs.items():
            if c["regs"][k] != u32(v):
                return False
    # the dumped memory
    for addr, data in c["dumps"].items():
        if addr == STK_LO:
            if fam in ("plan", "plannoop") and stage in ("early", "target", "rooms", "full") and want[0] != RET:
                fields = CTX_FIELDS_FULL if stage == "full" else CTX_FIELDS_EARLY
                for off, sz in fields:
                    a = CTXS + off - STK_LO
                    if data[a:a + sz] != M.snap(CTXS + off, sz):
                        return False
            continue
        if data != M.snap(addr, len(data)):
            return False
    return True


def table_of(addr):
    for k, (a, n) in TABLES.items():
        if a <= addr < a + n:
            return k
    return None


def check_family(fam, d, rooms):
    cases, blocks, _ = family(fam, rooms)
    calls, traced = read_out(os.path.join(d, fam + ".out"))
    bad, match, stops = [], 0, 0
    ctl = {n: [0, 0] for n in CONTROLS[fam]}
    site_pass = 0
    nbound = 0
    bounds = {}
    reasons = {}
    if len(calls) != len(cases):
        bad.append("case count %d != %d" % (len(calls), len(cases)))
    for c, case in zip(calls, cases):
        if "stop" in c:
            stops += 1
            bad.append("case %d STOP %s" % (c["n"], c["stop"]))
            continue
        want, M, stage = predict(fam, case, rooms)
        ok = matches(fam, c, want, M, stage)
        match += ok
        if not ok:
            bad.append("case %d mismatch want=%s got=%s %s" % (
                c["n"], want if want is None or want[0] == RET else (hex(want[1]), hex(want[2]), [hex(x) for x in want[3]]),
                c.get("obs") if c.get("obs") == RET else hex(c.get("obs", 0)),
                ("eax=%x" % c["eax"]) if "eax" in c else c.get("args", b"")[:16].hex()))
        if M.reason:
            reasons[M.reason] = reasons.get(M.reason, 0) + 1
        if M.refresh:
            reasons["refresh: " + M.refresh] = reasons.get("refresh: " + M.refresh, 0) + 1
        key = RET if want is None or want[0] == RET else "%x@%x" % (want[1], want[2])
        bounds[key] = bounds.get(key, 0) + 1
        if want is not None and want[0] != RET:
            nbound += 1
            site_pass += matches(fam, c, want, M, stage, shift=1)
        for n in ctl:
            nw, nM, nstage = predict(fam, case, rooms, neg=n)
            if nw is None or nw != want or any(nM.snap(a, len(x)) != M.snap(a, len(x)) for a, x in c["dumps"].items()
                                              if a != STK_LO):
                ctl[n][0] += 1
                ctl[n][1] += matches(fam, c, nw, nM, nstage) if nw is not None else 0
    acc = {}
    rest = []
    for t in traced:
        p = t.split()
        k = table_of(int(p[2], 16)) if p[0] == "R" else None
        if k:
            acc[k] = acc.get(k, 0) + int(p[4])
        else:
            rest.append(t)
    line = ("PATH54 %s cases=%d match=%d bad=%d stopped=%d traced=%d accounted=%s " % (
        fam, len(cases), match, len(bad), stops, len(rest), ",".join("%s:%d" % kv for kv in sorted(acc.items())) or "-")
        + " ".join("%s_separating=%d %s_passed=%d" % (n, ctl[n][0], n, ctl[n][1]) for n in ctl)
        + " boundary_cases=%d site_control_passed=%d boundaries=%d" % (nbound, site_pass, len(bounds)))
    return line, bad[:25], rest[:25], bounds, ctl, site_pass, reasons


def cmd_check(d):
    rooms = load_rooms(d)
    allok = True
    tot = [0, 0]
    for fam in FAMILIES:
        line, bad, traced, bounds, ctl, sp, reasons = check_family(fam, d, rooms)
        print(line)
        print("  SITES " + " ".join("%s:%d" % kv for kv in sorted(bounds.items())))
        if reasons:
            print("  OUTCOMES " + "; ".join("%s:%d" % kv for kv in sorted(reasons.items())))
        for b in bad:
            print("  BAD", b)
        for t in traced:
            print("  TRACED", t)
        if bad or traced or any(ctl[n][1] for n in ctl) or any(ctl[n][0] == 0 for n in ctl) or sp:
            allok = False
        tot[0] += int(line.split("cases=")[1].split()[0])
        tot[1] += int(line.split("match=")[1].split()[0])
    print("PATH54 total cases=%d match=%d" % tuple(tot))
    print("PATH54 result=%s" % ("ok" if allok else "FAIL"))


def cmd_manifest(d, write):
    rows = []
    names = sorted(os.listdir(d))
    for fn in names:
        p = os.path.join(d, fn)
        if os.path.isfile(p) and fn != "manifest.sha256":
            rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), fn))
    text = "\n".join(rows) + "\n"
    if write:
        with open(os.path.join(d, "manifest.sha256"), "w") as f:
            f.write(text)
    sys.stdout.write(text)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["grids", "cases", "check", "manifest"])
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "grids":
        cmd_grids(a.dir)
    elif a.cmd == "cases":
        cmd_cases(a.dir)
    elif a.cmd == "check":
        cmd_check(a.dir)
    else:
        cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    main(sys.argv[1:])

"""Model of the server room collision grid and the four spawn position predicates (plan 0017 Phase 2).

Usage:
  python3 -I tools/collision.py check <run.log> [...] [--excel DIR] [--root workspace/merged] [-v]

<run.log> is written by tools/d2run.py with tools/gdb/collision.gdb (the tags of tools/gdb/drlg-gen.py,
tools/gdb/drlg-roomk.py, tools/gdb/mon-spawn.py and tools/gdb/collision.py). `check` runs the room-population checker
of tools/monspawn.py on the same logs with this model attached, so CollisionTest, LogicRegionIdAt, SpawnClassCellTest,
NearWarpTest and SpawnPosOnTile are predicted instead of taken (the logged results stay on as checks), and prints the
collision report after the population report. A plan 0014 log (no SN line) is checked as before, with the predicates
that need the grid left as oracles and counted as such.

The model is docs/findings/drlg/0005-collision.md (boundary B, plan 0017 Phase 1 ruling), written from the code:

  * Activation (CB, COLL_MapBuild 0x0064C900): the map is the room's subtile rectangle, zeroed; every floor, wall and
    shadow entry of every room in the near list at that moment whose top-left subtile lies in the room stamps its
    tile's 25 sub-tile bytes, rows reversed (COLL_StampTile), then ORs 0x10 / 0x01 / 0x04 over the same block for the
    entry flags 0x02 / 0x40 / 0x80. The bytes come from the DT1 file (tools/dt1.py) named by the tile record (TL); the
    TL copy of the bytes, orientation, main and sub index are checked against the file. Which tile each entry holds
    (the rarity pick, drlg/room-tiles) and the entry flags are inputs taken from the log. Compared cell for cell.
  * Later tile writes (TCU, sub_0064C860_TileCollisionUpdate): clear the entry's tile, stamp the new one, in the map
    that holds the tile's top-left subtile; applied to the activation model.
  * Pass entry (SN, 0x0054EC90): the grid snapshot of the room and of its near rooms is an ADR-0004 value oracle. The
    non-gating R3 consistency check reports, per populated room, the cells where the snapshot differs from the
    activation model (with the TCUs), before and after the marks logged in the presets / objects window (CM lines
    between RW1 and the pass), and the bits of what is left.
  * In the pass: every creation marks PatternMark(room, x, y, pattern, 0x100) with the pattern from MonStats2 SizeX
    (g_CollPatternBySize: 0, 1, 1, 2; > 3 -> 1), 3 / 4 for a non-interactive NPC, 5 for BaseId 38; checked against the
    logged CM call. CollisionTest (CellTest, PlusTest, RectTest with RectSplit), RoomAtSubtile, LogicRegionIdAt (the
    DRLG room's logic record: first box, or the box grid at (x/5 - tx, y/5 - ty)), SpawnClassCellTest (five BaseIds)
    and NearWarpTest (the level's warp points NWP and the type-11 point NWW are logged inputs, owner drlg/warps;
    WarpDist from levels.bin) are computed on the snapshot plus the in-pass marks. SpawnPosOnTile (spawnCol 1) is
    computed from the room's floor entries and the DT1 sound byte (flags16 bit 1).
  * Logic regions (LG0 / LG1, sub_0066D110_LogicRegionsFromDs1): LOGIC_FloodAll / LOGIC_FloodFill on the logged
    orientation, floor and barrier grids and the level counter, then LogicBoxesFromGrid; compared with the id grid and
    the box list. The barrier grid (LOGIC_BarrierGridBuild) is an input. The neighbour merge (LG2) is counted only.
  * Required cases counted: R1 (level seed +0x1C4 and the level's active rooms unchanged across every NearWarpTest),
    R2 (accepted placements whose footprint holds a cell with 0x100 and no masked bit), C1 (deadCol corpses, DC/DCX/
    DCR), C2 (Collision missiles, MS/MSX: the 0x40 SizeMark), crow nests and the other SpawnClassCellTest BaseIds,
    wraiths (pattern 5), size-3 tests rejected on in-pass marks of size-2 units and the reverse, Logicals 1 rooms,
    rooms whose left or top neighbour activated after them.

Plan 0027 Phase 2: in a log written with tools/gdb/objects.gdb, tools/objects.py (run by tools/monspawn.py) keeps its
own World fed with TL, CB, TCU and RRESEED and with the window's marks, makes each object's mark itself
(UNIT_CollMarkRect: RectOrWH with SizeX x SizeY and UNIT_GetCollMask's mask when HasCollision[mode]) and predicts every
COLL_WHTest of the objects window on the activation model (World.wh_test under World.model_state(): the model's own
near lists, built at CB as DUNGEON_NearRoomsBuild does). The report gains a block with those counters.

Exit 0 only if every check holds. Stdlib only. Read-only.
"""
import base64
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import dt1 as dt1mod  # noqa: E402
from rng import step  # noqa: E402

ROOT = os.path.dirname(HERE)
DEFAULT_ROOT = os.path.join(ROOT, "workspace", "merged")
DEFAULT_EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
COLL_TAGS = {"TL", "CB", "TCU", "CM", "SN", "SNP", "NWP", "NWW", "NW0", "NW1", "LG0", "LG1", "LG2", "DC", "DCX", "DCR", "MS",
             "MSX",
             # plan 0038 batch H5d (tools/gdb/collision.py): unwindowed before / after pairs
             "TCB0", "TCB1", "IM0", "IM1", "PN0", "PN1", "SCT0", "SCT1", "LPP0", "LPP1"}
LPP_GROUPS = 0x006EED88                                # 8-byte {flag, group} per level point type, read by 0x0066AC40
PATTERN_BY_SIZE = {0: 0, 1: 1, 2: 1, 3: 2}             # g_CollPatternBySize 0x006EB3DC
CLASS_CELL = {206: (0, 3, 0x3C01), 228: (0, 2, 0x3C01), 334: (-2, -2, 0x01C0), 528: (2, 4, 0x3C01)}  # 0x005FD350
TILE_OFFSETS = [(0, -3), (3, 0), (0, 3), (-3, 0)]      # g_SpawnTileOffsets 0x006E2D50
FLOOD_DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]        # g_LogicFloodDirs 0x006EEE14
FLOOD_RULES = 0x006EEE3C
FLOOD_ROW = 0x006EEEA0


class NotLogged(Exception):
    """The model needs a value the log does not hold (a room outside the snapshot)."""


class CollMismatch(Exception):
    pass


def s32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


def unz(s):
    return json.loads(zlib.decompress(base64.b64decode(s)))


def u16cells(hx):
    b = bytes.fromhex(hx)
    return list(struct.unpack("<%dH" % (len(b) // 2), b))


def exe_read(path, va, n):
    data = open(path, "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    base = struct.unpack_from("<I", data, pe + 24 + 28)[0]
    sec = pe + 24 + opt
    rva = va - base
    for i in range(nsec):
        vsize, vaddr, rawsize, raw = struct.unpack_from("<IIII", data, sec + 40 * i + 8)
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            off = raw + rva - vaddr
            return data[off:off + n]
    raise ValueError("VA 0x%08X not in any section" % va)


class TileDB:
    """TL records -> the DT1 file's tile (tools/dt1.py)."""

    def __init__(self, root):
        self.root = root
        self.files = {}
        self.tl = {}           # pointer -> (bytes25, sound, key)
        self.checked = self.bad = 0
        self.bad_list = []
        self.paths = set()

    def file_tiles(self, f):
        p = os.path.join(self.root, f.replace("\\", "/").lower())
        if p not in self.files:
            self.files[p] = dt1mod.parse(open(p, "rb").read())["tiles"]
        return self.files[p]

    def add(self, d):
        tiles = self.file_tiles(d["f"])
        b = bytes.fromhex(d["b"])
        i = d["i"]
        cand = None
        if i is not None and 0 <= i < len(tiles):
            cand = tiles[i]
        else:   # an early dev log without a valid index: the file's tiles of that key and those bytes
            for t in tiles:
                if (t["orientation"], t["main_index"], t["sub_index"]) == (d["o"], d["m"], d["s"]) and t["subtile_flags"] == b:
                    cand = t
                    break
        self.checked += 1
        ok = cand is not None and (cand["orientation"], cand["main_index"], cand["sub_index"]) == (d["o"], d["m"], d["s"]) \
            and cand["subtile_flags"] == b and (cand["sound"] | cand["animated"] << 8) == d["w6"]
        if not ok:
            self.bad += 1
            self.bad_list.append(d)
        self.paths.add(d["f"].lower())
        if cand is not None:
            self.tl[d["p"]] = (cand["subtile_flags"], cand["sound"] | cand["animated"] << 8, (d["f"], i))
        else:
            self.tl[d["p"]] = (b, d["w6"], (d["f"], i))

    def bytes_of(self, p):
        if p not in self.tl:
            raise CollMismatch("tile %08x has no TL record" % p)
        return self.tl[p][0]

    def w6(self, p):
        if p not in self.tl:
            raise CollMismatch("tile %08x has no TL record" % p)
        return self.tl[p][1]


class Map:
    """One room's u16 cells and rectangle (model or snapshot)."""
    __slots__ = ("x0", "y0", "w", "h", "c")

    def __init__(self, x0, y0, w, h, c):
        self.x0, self.y0, self.w, self.h, self.c = x0, y0, w, h, c

    def has(self, x, y):
        return self.x0 <= x < self.x0 + self.w and self.y0 <= y < self.y0 + self.h

    def idx(self, x, y):
        return (y - self.y0) * self.w + (x - self.x0)


def stamp(cells, w, row, col, b, clear=False):
    """COLL_StampTile / COLL_ClearTile: rows reversed, clipped at < 0 only (no upper clip)."""
    bad = 0
    for r in range(5):
        for c in range(5):
            if row + r < 0 or col + c < 0:
                continue
            i = (row + r) * w + col + c
            if i >= len(cells):
                bad += 1
                continue
            v = b[(4 - r) * 5 + c]
            if clear:
                cells[i] &= ~v & 0xFFFF
            else:
                cells[i] |= v
    return bad


def or_block(cells, w, row, col, v):
    for r in range(5):
        for c in range(5):
            if row + r < 0 or col + c < 0:
                continue
            i = (row + r) * w + col + c
            if i < len(cells):
                cells[i] |= v


class World:
    """Collision state of one log, fed every collision event in line order."""

    def __init__(self, root, tables, exe=DEFAULT_EXE, verbose=False):
        self.root, self.t, self.verbose = root, tables, verbose
        self.tiles = TileDB(root)
        self.fail = 0
        self.checks = 0
        self.msgs = []
        self.stats = {}
        self.rects = {}           # active room -> (x0, y0, w, h), from CB / SN
        self.model = {}           # active room -> Map (activation model + TCUs)
        self.cb_info = {}         # active room -> CB summary
        self.rr = {}              # DRLG room -> RRESEED summary (type, ltype, level)
        self.logicals1 = set()    # DRLG rooms with a flood (LG0)
        self.cb_order = []        # (line, room, rect, near entries) for the activation-order case
        self.pre_cm = []          # CM lines before the pass entry (presets / objects window)
        self.P = None             # pass state
        self.maps_override = None
        self.nears_override = None
        self.model_near = {}      # active room -> near list as the model keeps it (CB, then DUNGEON_NearRoomsBuild)
        self.dr_room = {}         # DRLG room -> its active room at the latest CB (plan 0038 H5b)
        self.cb_stamps = {}       # active room -> [(sx, sy, tile)] stamped at its CB (plan 0038 H5d)
        self.h5d = {}             # thread -> pending before-line of an H5d pair
        self.last_tcu = None
        self.exe = exe
        self.lpp_groups = None
        self.lg0 = {}
        self.nw = None
        self.nw_cbs = []
        self.nw_point = None
        self.nw_reached = False
        self.nwp = None
        self.nww = None
        self.dcs = []
        self.dead_dc = {}
        self.ms = []
        self.dcr = []
        self.late = []
        self.r3 = {"rooms": 0, "diff0": 0, "diff1": 0, "explained": 0, "resid_bits": {}, "rooms_resid": 0,
                   "rooms_exact": 0}
        rows = exe_read(exe, FLOOD_ROW, 4 * 32)
        self.flood_row = list(struct.unpack("<32i", rows))
        self.flood_rules = {}
        for row in range(-1, 5):
            for d in range(-1, 4):
                self.flood_rules[(row, d)] = struct.unpack("<I", exe_read(exe, FLOOD_RULES + 4 * (5 * row + d), 4))[0]

    # --- bookkeeping ------------------------------------------------------------------------------------------
    def hit(self, k, n=1):
        self.stats[k] = self.stats.get(k, 0) + n

    def ok(self, cond, msg):
        self.checks += 1
        if not cond:
            self.fail += 1
            self.msgs.append(msg)
            print("MISMATCH collision " + msg)

    # --- events -----------------------------------------------------------------------------------------------
    def event(self, tag, d, ln, path):
        fn = getattr(self, "ev_" + tag, None)
        if fn is not None:
            fn(d, ln, path)

    def ev_RRESEED(self, d, ln, path):
        self.rr[d["room"]] = {"type": d["type"], "ltype": d["ltype"], "level": d["level"],
                              "def": (d.get("preset") or {}).get("def")}

    def ev_TL(self, d, ln, path):
        self.tiles.add(d)

    def ev_CB(self, d, ln, path):
        z = unz(d["z"])
        x0, y0, w, h = d["rect"]
        room = d["room"]
        self.rects[room] = (x0, y0, w, h)
        cells = [0] * (w * h)
        alt80 = [0] * (w * h)    # plan 0038 H5d (collision 8): the same build without the 0x80 -> 0x04 OR
        bad = 0
        n_ent = 0
        n80 = 0
        stamps = []
        for n, _dr, trect, W, F, S in z["near"]:
            tx, ty = trect[0], trect[1]
            for lst in (F, W, S):
                for x, y, fl, tp, _o in lst:
                    sx, sy = (x + tx) * 5, (y + ty) * 5
                    if not (x0 <= sx < x0 + w and y0 <= sy < y0 + h):
                        continue
                    n_ent += 1
                    if not tp:
                        self.hit("activation: entry with no tile (skipped)")
                        continue
                    row, col = sy - y0, sx - x0
                    bad += stamp(cells, w, row, col, self.tiles.bytes_of(tp))
                    stamp(alt80, w, row, col, self.tiles.bytes_of(tp))
                    stamps.append((sx, sy, tp))
                    v = (0x10 if fl & 0x02 else 0) | (0x01 if fl & 0x40 else 0) | (0x04 if fl & 0x80 else 0)
                    if v:
                        or_block(cells, w, row, col, v)
                        self.hit("activation: entry flag bits 0x%02x over a tile" % v)
                    if v & ~0x04:
                        or_block(alt80, w, row, col, v & ~0x04)
                    if fl & 0x80:
                        n80 += 1
        logged = z["cells"]
        if logged[4] is None:
            self.hit("activation: map without cells")
            return
        lc = u16cells(logged[4])
        same = lc == cells
        ndiff = sum(1 for a, b in zip(lc, cells) if a != b)
        self.ok(same and bad == 0, "%s:%d CB room %08x level %s: %d of %d cells differ from the activation model"
                % (os.path.basename(path), ln, room, d["lid"], ndiff, len(cells)))
        self.hit("activation dumps compared")
        self.hit("activation cells compared", len(cells))
        if n80:
            # plan 0038 H5d (collision 8): cells whose logged value only the 0x80 -> 0x04 OR explains
            sep = sum(1 for a, b, c in zip(lc, cells, alt80) if a == b and a != c)
            self.hit("H5d entry flag 0x80: entries in activation dumps", n80)
            self.hit("H5d entry flag 0x80: dumps with such an entry")
            if sep:
                self.hit("H5d entry flag 0x80: cells only its 0x04 OR explains (model exact there)", sep)
                self.hit("H5d entry flag 0x80: dumps where its OR changes a cell")
            self.hit("H5d entry flag 0x80: entries by level %s" % d["lid"], n80)
        dr = d["dr"]
        rr = self.rr.get(dr, {})
        self.cb_info[room] = {"lid": d["lid"], "dr": dr, "th": d["th"], "type": rr.get("type"), "ltype": rr.get("ltype"),
                              "near": len(z["near"]), "entries": n_ent}
        self.model[room] = Map(x0, y0, w, h, cells)
        self.cb_stamps[room] = stamps
        # the model's near lists (plan 0027): the room's list at activation; DUNGEON_NearRoomsBuild adds the new room to
        # the list of each active neighbour
        nl = [e[0] for e in z["near"]]
        # plan 0038 H5b: a DRLG room activated again under a new active room while the old one is still listed as a
        # neighbour: the new room takes the old one's place in those lists
        key = (d["lid"], dr, tuple(d["rect"]))
        old = self.dr_room.get(key)
        if old is not None and old != room and self.rects.get(old) == (x0, y0, w, h) and self.cb_info.get(old, {}).get(
                "dr") == dr:                     # the old pointer is not reused by another room since
            for k in self.model_near:
                lst = self.model_near[k]
                if old in lst:
                    lst[lst.index(old)] = room
                    if lst.count(room) > 1:
                        del lst[len(lst) - 1 - lst[::-1].index(room)]
                    self.hit("near lists: a DRLG room's new active room in its old one's place")
        self.dr_room[key] = room
        self.model_near[room] = list(nl)
        for n in nl:
            if n != room and n in self.model_near and room not in self.model_near[n]:
                self.model_near[n].append(room)
        if self.nw is not None:
            self.nw_cbs.append(room)
        P = self.P
        if P is not None and d["th"] == P["th"]:
            # a room activated inside the pass (NearWarpTest's waypoint lookup): its grid joins the pass state and
            # DUNGEON_NearRoomsBuild adds it to the near list of each active neighbour
            P["rooms"][room] = Map(x0, y0, w, h, list(lc))
            P["pristine_maps"][room] = Map(x0, y0, w, h, list(lc))
            nl = [e[0] for e in z["near"]]
            P["near"][room] = nl
            for n in nl:
                if n != room and n in P["near"] and room not in P["near"][n]:
                    P["near"][n].append(room)
                    self.hit("rooms activated inside a pass that joined a snapshot room's near list")
            self.hit("rooms activated inside a pass")
        # activation order: this room's own border tiles (x == tw or y == th) land in a right / bottom room that
        # activated earlier only if that room is in the near list now; record them for the late-neighbour case
        own = [e for e in z["near"] if e[0] == room]
        border = []
        if own:
            _n, _dr, trect, W, F, S = own[0]
            tx, ty, tw, th = trect
            for lst in (F, W, S):
                for x, y, fl, tp, _o in lst:
                    if x == tw or y == th:
                        border.append(((x + tx) * 5, (y + ty) * 5, fl, tp))
        for r2, rect2, _ln2 in self.cb_order[-400:]:
            # an earlier room (r2) to the right of or below this room: this room's border tiles have their origin in
            # r2, so COLL_MapBuild stamps them into neither grid (r2 is never re-stamped)
            X0, Y0, W2, H2 = rect2
            touches = (X0 == x0 + w and Y0 < y0 + h and y0 < Y0 + H2) or (Y0 == y0 + h and X0 < x0 + w and x0 < X0 + W2)
            if not touches:
                continue
            lost = [b for b in border if X0 <= b[0] < X0 + W2 and Y0 <= b[1] < Y0 + H2]
            if not lost:
                continue
            self.hit("activation order: a room activated after its right/bottom neighbour (border tiles in it)")
            self.hit("activation order: border tiles stamped into no grid", len(lost))
            m2 = self.model.get(r2)
            if m2 is not None:
                tmp = list(m2.c)
                for bx, by, fl, tp in lost:
                    if tp:
                        stamp(tmp, m2.w, by - m2.y0, bx - m2.x0, self.tiles.bytes_of(tp))
                self.hit("activation order: cells of the earlier room those tiles would change",
                         sum(1 for a, b in zip(tmp, m2.c) if a != b))
            self.late.append((room, r2, lost))
        self.cb_order.append((room, (x0, y0, w, h), ln))
        lvt = rr.get("ltype")
        self.hit("activation dumps by LvlType %s" % lvt)
        self.hit("activation dumps by DRLG room type %s" % rr.get("type"))
        if dr in self.logicals1:
            self.hit("activation dumps of Logicals 1 rooms")

    def ev_TCU(self, d, ln, path):
        room = d["room"]
        self.last_tcu = d
        self.hit("TileCollisionUpdate calls")
        m0 = self.model.get(room)
        if m0 is None or d["t0"] is None:
            self.hit("TileCollisionUpdate on a room without a model map")
            return
        sx, sy = (d["t0"][0] + d["x"]) * 5, (d["t0"][1] + d["y"]) * 5
        tgt = None
        for r, m in self.model.items():
            if m.has(sx, sy):
                tgt = m
                break
        if tgt is None:
            self.hit("TileCollisionUpdate: no model map holds the tile")
            return
        row, col = sy - tgt.y0, sx - tgt.x0
        if d["old"]:
            stamp(tgt.c, tgt.w, row, col, self.tiles.bytes_of(d["old"]), clear=True)
        if d["new"]:
            stamp(tgt.c, tgt.w, row, col, self.tiles.bytes_of(d["new"]))
        self.hit("TileCollisionUpdate applied (%s)" % ("re-stamp" if d["new"] else "clear"))

    def ev_CM(self, d, ln, path):
        if self.P is not None and d["th"] == self.P["th"]:
            self.P["cm"].append((d, ln))
            if self.P.get("preset"):
                self.pre_cm.append((d, ln))      # still part of the presets window for R3
        else:
            self.pre_cm.append((d, ln))

    def ev_LG0(self, d, ln, path):
        self.logicals1.add(d["dr"])
        self.lg0[d["dr"]] = (d, unz(d["z"]))

    def ev_LG1(self, d, ln, path):
        got = self.lg0.pop(d["dr"], None)
        if got is None:
            return
        d0, z0 = got
        z1 = unz(d["z"])
        ids, boxes, nb, ctr = self.flood(d0, z0)
        lids = z1["ids"]
        self.ok(lids is not None and lids[2] == ids, "%s:%d LG1 DRLG room %08x: flood id grid differs" % (
            os.path.basename(path), ln, d["dr"]))
        self.ok(d["n"] == nb, "%s:%d LG1 nBoxes %d, model %d" % (os.path.basename(path), ln, d["n"], nb))
        self.ok(d["ctr"] == ctr, "%s:%d LG1 level counter %d, model %d" % (os.path.basename(path), ln, d["ctr"], ctr))
        got_b = [(b["r0"], b["r"], b["kind"], b["id"]) for b in z1["boxes"]]
        self.ok(got_b == boxes, "%s:%d LG1 box list differs (%d logged, %d model)" % (
            os.path.basename(path), ln, len(got_b), len(boxes)))
        self.hit("Logicals 1 floods compared")
        self.lg1 = (d["dr"], z1)

    def ev_LG2(self, d, ln, path):
        z2 = unz(d["z"])
        prev = getattr(self, "lg1", None)
        if prev and prev[0] == d["dr"]:
            a = [b["id"] for b in prev[1]["boxes"]]
            b = [x["id"] for x in z2["boxes"]]
            self.hit("Logicals 1 neighbour merges that relabelled boxes" if a != b else "Logicals 1 neighbour merges, no relabel")

    def flood(self, d0, z0):
        """LOGIC_FloodAll / LOGIC_FloodFill, then LogicBoxesFromGrid (drlg/0005 section 7)."""
        tx, ty, tw, th = d0["t"]
        W, H = tw + 1, th + 1
        orient = z0["orient"]
        floor = z0["floor"]
        barrier = z0["barrier"]

        def gv(g, x, y):
            if g is None or g[2] is None:
                return 0
            return g[2][y][x]

        def s32(v):
            return v - (1 << 32) if v & 0x80000000 else v

        ids = [[0] * W for _ in range(H)]
        base = d0["base"]
        nxt = base
        sys.setrecursionlimit(100000)
        cur = [0]

        def fill(x, y, d):
            while True:
                if not (0 <= x <= tw and 0 <= y <= th):
                    return
                if ids[y][x] & 0x10000000:
                    return
                if gv(barrier, x, y) == 0:
                    ids[y][x] |= cur[0]
                    for k in range(4):
                        fill(x + FLOOD_DIRS[k][0], y + FLOOD_DIRS[k][1], k)
                    return
                o = gv(orient, x, y) if (orient is not None and orient[2] is not None) else 0
                row = self.flood_row[o] if 0 <= o < len(self.flood_row) else 0
                b = self.flood_rules[(row, d)]
                if b & 1:
                    ids[y][x] |= cur[0]
                if b & 2 and d != 2:
                    fill(x + 1, y, 0)
                if b & 4 and d != 3:
                    fill(x, y + 1, 1)
                if b & 8 and d != 0:
                    fill(x - 1, y, 2)
                if b & 0x10 and d != 1:
                    fill(x, y - 1, 3)
                if not b & 0x20:
                    return
                x, y, d = x + 1, y + 1, -1

        for y in range(H):
            for x in range(W):
                if ids[y][x] & 0x10000000:
                    continue
                nxt += 1
                c = (nxt & 0x0FFFFFFF) | 0x10000000
                f = s32(gv(floor, x, y))
                if (f & 0x1E0FF00) == 0x1E00000 or f < 0:
                    c |= 0x20000000
                cur[0] = c
                fill(x, y, -1)
        nboxes = nxt - base + 1
        ctr = base + nboxes
        # LogicBoxesFromGrid
        boxed = [[False] * W for _ in range(H)]
        out = []
        for y in range(H):
            for x in range(W):
                if boxed[y][x]:
                    continue
                v = ids[y][x]
                x2 = x
                while x2 + 1 < W and ids[y][x2 + 1] == v and not boxed[y][x2 + 1]:
                    x2 += 1
                y2 = y
                while y2 + 1 < H and all(ids[y2 + 1][i] == v and not boxed[y2 + 1][i] for i in range(x, x2 + 1)):
                    y2 += 1
                for yy in range(y, y2 + 1):
                    for xx in range(x, x2 + 1):
                        boxed[yy][xx] = True
                r0 = [tx + x, ty + y, tx + x2 + 1, ty + y2 + 1]
                if r0[0] >= tx + tw or r0[1] >= ty + th:
                    r = [0, 0, 0, 0]
                else:
                    r = [r0[0], r0[1], min(r0[2], tx + tw), min(r0[3], ty + th)]
                out.insert(0, (r0, r, (v >> 29) & 1, v & 0x0FFFFFFF))
        out.append(([0, 0, 0, 0], [0, 0, 0, 0], 0, 0))
        return ids, out, nboxes, ctr

    # --- the pass ---------------------------------------------------------------------------------------------
    def ev_SNP(self, d, ln, path):
        """Plan 0018: the snapshot at a superunique or MonPlace 2/3 spawn in the presets window (same payload as SN);
        no R3 comparison, and the window's marks stay in pre_cm for the pass's R3."""
        keep = self.pre_cm
        self.ev_SN(d, ln, path, preset=True)
        self.pre_cm = keep

    def ev_SN(self, d, ln, path, preset=False):
        z = unz(d["z"])
        P = {"room": d["room"], "th": d["th"], "lseed": d["lseed"], "rooms": {}, "near": {}, "lg": {}, "trect": {},
             "floors": {d["room"]: z["floors"]}, "cm": [], "pristine": {}, "marks": {}, "ln": ln, "path": path}
        for r in z["rooms"]:
            x0, y0, w, h = r["rect"]
            self.rects[r["r"]] = (x0, y0, w, h)
            cells = u16cells(r["cells"][4]) if r["cells"] and r["cells"][4] else None
            P["rooms"][r["r"]] = Map(x0, y0, w, h, cells)
            P["pristine"][r["r"]] = list(cells) if cells else None
            P["near"][r["r"]] = r["near"]
            if "floors" in r:
                P["floors"][r["r"]] = r["floors"]
            P["lg"][r["r"]] = r["lg"]
            P["trect"][r["r"]] = r["trect"]
        P["pristine_maps"] = {r: Map(m.x0, m.y0, m.w, m.h, list(m.c) if m.c else None) for r, m in P["rooms"].items()}
        self.P = P
        if preset:
            P["preset"] = True
            self.hit("preset-window snapshots (superunique, MonPlace 2/3)")
            return
        self.hit("pass snapshots")
        self.r3_check(d["room"], P)
        self.pre_cm = []

    def r3_check(self, room, P):
        m = self.model.get(room)
        snap = P["rooms"].get(room)
        if m is None or snap is None or snap.c is None:
            self.hit("R3: no activation model for the pass room")
            return
        mc = list(m.c)
        d0 = sum(1 for a, b in zip(mc, snap.c) if a != b)
        # apply the presets / objects window marks to a copy of the model (lookups among the snapshot rooms)
        tmp = {r: Map(mm.x0, mm.y0, mm.w, mm.h, list(self.model[r].c) if r in self.model else None)
               for r, mm in P["rooms"].items()}
        for cm, _ln in self.pre_cm:
            if cm["th"] != P["th"]:
                continue
            try:
                self.apply_cm(cm, tmp, P["near"])
            except NotLogged:
                self.hit("R3: window mark outside the snapshot rooms")
        mc2 = tmp[room].c
        d1 = sum(1 for a, b in zip(mc2, snap.c) if a != b)
        self.r3["rooms"] += 1
        self.r3["diff0"] += d0
        self.r3["diff1"] += d1
        self.r3["explained"] += d0 - d1 if d0 >= d1 else 0
        if d1:
            self.r3["rooms_resid"] += 1
        else:
            self.r3["rooms_exact"] += 1
        rec = {"path": P.get("path"), "ln": P.get("ln"), "room": room, "th": P["th"], "bits": {}, "objcells": []}
        for i, (a, b) in enumerate(zip(mc2, snap.c)):
            if a != b:
                k = "+%04x -%04x" % (b & ~a & 0xFFFF, a & ~b & 0xFFFF)
                self.r3["resid_bits"][k] = self.r3["resid_bits"].get(k, 0) + 1
                rec["bits"][k] = rec["bits"].get(k, 0) + 1
                if (b ^ a) & 0x400:
                    # plan 0048 Phase 2 (oracle 20): an object-bit cell no window mark explains
                    rec["objcells"].append((snap.x0 + i % snap.w, snap.y0 + i // snap.w, b, a))
        if rec["bits"]:
            self.r3.setdefault("per_room", []).append(rec)
        self.hit("R3: window marks applied", sum(1 for cm, _ in self.pre_cm if cm["th"] == P["th"]))

    def pass_end(self):
        P = self.P
        if P is not None and P["cm"]:
            self.hit("in-pass marks not matched to a creation", len(P["cm"]))
        self.P = None

    # cell access on the pass grid
    def near_of(self, r, nears=None):
        if nears is None:
            nears = self.nears_override if self.nears_override is not None else (self.P["near"] if self.P else {})
        if r not in nears:
            raise NotLogged("near list of room %08x" % r)
        return nears[r]

    def room_at(self, hint, x, y, nears=None):
        """sub_00463740_RoomAtSubtile."""
        if not hint:
            return 0
        rc = self.rects.get(hint)
        if rc is None:
            raise NotLogged("rect of room %08x" % hint)
        if rc[0] <= x < rc[0] + rc[2] and rc[1] <= y < rc[1] + rc[3]:
            return hint
        for n in self.near_of(hint, nears):
            rc = self.rects.get(n)
            if rc is None:
                raise NotLogged("rect of room %08x" % n)
            if rc[0] <= x < rc[0] + rc[2] and rc[1] <= y < rc[1] + rc[3]:
                return n
        return 0

    def grid(self, r, maps=None):
        maps = maps if maps is not None else (self.maps_override or self.P["rooms"])
        m = maps.get(r)
        if m is None:
            raise NotLogged("cells of room %08x" % r)
        return m

    def cell_test(self, hint, x, y, mask, maps=None, nears=None):
        r = self.room_at(hint, x, y, nears)
        if not r:
            return 0x27
        m = self.grid(r, maps)
        if m.c is None:
            return 0x27
        return m.c[m.idx(x, y)] & mask

    def plus_test(self, hint, x, y, mask):
        r = self.room_at(hint, x, y)
        if not r:
            return mask
        m = self.grid(r)
        if m.c is None:
            return mask
        edge = (x == m.x0) | (y == m.y0) << 1 | (x == m.x0 + m.w - 1) << 2 | (y == m.y0 + m.h - 1) << 3
        if edge in (5, 7, 10, 11, 13, 14, 15):
            return mask
        out = {1: (-1, 0), 2: (0, -1), 4: (1, 0), 8: (0, 1)}
        res = 0
        cells = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
        for dx, dy in cells:
            outside = any(edge & k and (dx, dy) == v for k, v in out.items())
            if outside:
                res |= self.cell_test(r, x + dx, y + dy, mask)
            else:
                res |= m.c[m.idx(x + dx, y + dy)] & mask
        return res

    def rect_split(self, R, m):
        l, t, r, b = R
        if t > b or l > r:
            return []
        p0 = [l, t, r, b]
        pieces = [p0]
        if r >= m.x0 + m.w:
            p0[2] = m.x0 + m.w - 1
            pieces.append([m.x0 + m.w, t, r, b])
        if b >= m.y0 + m.h:
            p0[3] = m.y0 + m.h - 1
            pieces.append([p0[0], p0[3] + 1, p0[2], b])
        return pieces

    def rect_test(self, hint, R, mask):
        r = self.room_at(hint, R[0], R[1])
        if not r:
            return 0x27
        m = self.grid(r)
        if m.c is None:
            return 0x27
        pieces = self.rect_split(R, m)
        if not pieces:
            return 0x27
        l, t, rr, b = pieces[0]
        v = 0
        for yy in range(t, b + 1):
            for xx in range(l, rr + 1):
                v |= m.c[m.idx(xx, yy)] & mask
        for p in pieces[1:]:
            v |= self.rect_test(r, p, mask)
        return v

    def collision_test(self, hint, x, y, size, mask):
        """sub_0064D9B0_CollisionTest."""
        if size in (0, 1):
            return self.cell_test(hint, x, y, mask)
        if size == 2:
            return self.plus_test(hint, x, y, mask)
        if size == 3:
            return self.rect_test(hint, [x - 1, y - 1, x + 1, y + 1], mask)
        return 0xFFFF

    def collision_test_pristine(self, hint, x, y, size, mask):
        """The same test on the snapshot without the in-pass marks."""
        self.maps_override = self.P["pristine_maps"]
        try:
            return self.collision_test(hint, x, y, size, mask)
        finally:
            self.maps_override = None

    def model_state(self):
        """Run the next predicate on the activation model (with the TCUs and the marks applied to it) instead of a
        pass snapshot (plan 0027: the objects window, which runs before the pass-entry snapshot)."""
        w = self

        class _Ctx:
            def __enter__(self):
                w.maps_override, w.nears_override = w.model, w.model_near

            def __exit__(self, *a):
                w.maps_override = w.nears_override = None
        return _Ctx()

    def wh_test(self, room, x, y, w, h, mask):
        """COLL_WHTest 0x0064D800: w <= 1 and h <= 1 (signed): COLL_CellTestNb (the cell's room among the hint and its
        near list, the cell & mask, 0x27 unmasked when no room or no map holds it); otherwise COLL_RectTest on
        {x - (w >> 1), y - (h >> 1), x - (w >> 1) + w - 1, y - (h >> 1) + h - 1} (unsigned halving)."""
        if s32(w) <= 1 and s32(h) <= 1:
            return self.cell_test(room, x, y, mask)
        l, t = x - ((w & 0xFFFFFFFF) >> 1), y - ((h & 0xFFFFFFFF) >> 1)
        return self.rect_test(room, [l, t, l + w - 1, t + h - 1], mask)

    def apply_model_mark(self, d):
        """A mark (CM shape) applied to the activation model."""
        self.apply_cm(d, self.model, self.model_near)

    def reset_process(self):
        """A new log is a new game process: pointers, maps and pending state start over (counters stay)."""
        self.tiles.tl = {}
        self.rects, self.model, self.cb_info, self.rr = {}, {}, {}, {}
        self.model_near = {}
        self.logicals1, self.cb_order, self.pre_cm, self.lg0 = set(), [], [], {}
        self.P = self.nw = self.nwp = self.nww = None
        self.pend_dc = self.pend_ms = None

    def footprint(self, x, y, size):
        if size in (0, 1):
            return [(x, y)]
        if size == 2:
            return [(x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        if size == 3:
            return [(x + dx, y + dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
        return []

    def cell_value(self, hint, x, y, maps=None):
        r = self.room_at(hint, x, y)
        if not r:
            return None
        m = self.grid(r, maps)
        return None if m.c is None else m.c[m.idx(x, y)]

    # marks
    def cell_op(self, hint, x, y, v, clear, maps, nears):
        r = self.room_at(hint, x, y, nears)
        if not r:
            return
        m = self.grid(r, maps)
        if m.c is None:
            return
        i = m.idx(x, y)
        m.c[i] = (m.c[i] & ~v & 0xFFFF) if clear else (m.c[i] | v)

    def plus_op(self, hint, x, y, v, clear, maps, nears):
        for dx, dy in ((-1, 0), (0, 0), (1, 0), (0, -1), (0, 1)):
            self.cell_op(hint, x + dx, y + dy, v, clear, maps, nears)

    def rect_op(self, hint, R, v, clear, maps, nears):
        r = self.room_at(hint, R[0], R[1], nears)
        if not r:
            return
        m = self.grid(r, maps)
        if m.c is None:
            return
        pieces = self.rect_split(R, m)
        if not pieces:
            return
        l, t, rr, b = pieces[0]
        for yy in range(t, b + 1):
            for xx in range(l, rr + 1):
                i = m.idx(xx, yy)
                m.c[i] = (m.c[i] & ~v & 0xFFFF) if clear else (m.c[i] | v)
        for p in pieces[1:]:
            self.rect_op(r, p, v, clear, maps, nears)

    def pattern_op(self, hint, x, y, p, m, clear, maps=None, nears=None):
        """COLL_PatternMark / COLL_PatternUnmark."""
        if p in (1, 3):
            self.plus_op(hint, x, y, m, clear, maps, nears)
            if m:
                self.cell_op(hint, x, y, 0x1000 if p == 1 else 0x2000, clear, maps, nears)
        elif p in (2, 4):
            self.rect_op(hint, [x - 1, y - 1, x + 1, y + 1], m, clear, maps, nears)
            if m:
                self.plus_op(hint, x, y, 0x1000 if p == 2 else 0x2000, clear, maps, nears)
        elif p == 5:
            self.plus_op(hint, x, y, m, clear, maps, nears)

    def size_op(self, hint, x, y, s, m, clear, maps=None, nears=None):
        """COLL_SizeMark / COLL_SizeUnmark."""
        if s == 1:
            self.cell_op(hint, x, y, m, clear, maps, nears)
        elif s == 2:
            self.plus_op(hint, x, y, m, clear, maps, nears)
        elif s == 3:
            self.rect_op(hint, [x - 1, y - 1, x + 1, y + 1], m, clear, maps, nears)

    def rectwh_op(self, hint, x, y, w, h, m, clear, maps=None, nears=None):
        """COLL_RectOrWH / COLL_RectClearWH (w/2 unsigned)."""
        if clear and (w <= 0 or h <= 0):
            return
        if w == 1 and h == 1:
            self.cell_op(hint, x, y, m, clear, maps, nears)
            return
        l, t = x - (w >> 1), y - (h >> 1)
        self.rect_op(hint, [l, t, l + w - 1, t + h - 1], m, clear, maps, nears)

    def apply_cm(self, d, maps=None, nears=None):
        f, room, x, y, a, b = d["f"], d["room"], d["x"], d["y"], d["a"], d["b"]
        if f in ("PM", "PU"):
            self.pattern_op(room, x, y, a, b, f == "PU", maps, nears)
        elif f in ("SM", "SU"):
            self.size_op(room, x, y, a, b, f == "SU", maps, nears)
        else:
            self.rectwh_op(room, x, y, a, b, d["m"], f == "RC", maps, nears)

    def creation_marks(self, room, x, y, cls, wraith=True):
        """Pattern of a new monster: PATH_PatternFromSize (the size table, the NPC upgrade); PATH_DynamicCreate gives
        BaseId 38 (wraiths) pattern 5, which the post-create refresh (sub_00649CA0_PathPatternRefresh) drops."""
        t = self.t
        m2 = t.m2(cls)
        size = struct.unpack("b", m2[0x08:0x09])[0]
        pat = PATTERN_BY_SIZE.get(size, 1) if 0 <= size else 1
        fl = t.m(cls, 0x0D, "<B")
        if fl & 1 and not fl & 2 and pat in (1, 2):
            pat += 2
        if wraith and t.m(cls, 0x02, "<h") == 38:
            pat = 5
        return size, pat

    def expect_marks(self, want, what, path, ln):
        """The logged CM calls since the last check must be exactly `want`; they are applied in order."""
        P = self.P
        got = [c for c, _ in P["cm"]]
        P["cm"] = []
        keys = ("f", "room", "x", "y", "a", "b")
        same = len(got) == len(want) and all(all(g[k] == w[k] for k in keys) for g, w in zip(got, want))
        self.ok(same, "%s:%d %s: logged %s, model %s" % (os.path.basename(path), ln, what,
                                                         [[g[k] for k in keys] for g in got], [[w[k] for k in keys] for w in want]))
        for c in (want if same else got):
            self.apply_cm(c)

    def creation_mark(self, room, x, y, cls, path, ln):
        """In-pass marks inside SUnitCreate: UNIT_CollMark twice (both calls return to 0x006494D5)."""
        size, pat = self.creation_marks(room, x, y, cls)
        w = {"f": "PM", "room": room, "x": x, "y": y, "a": pat, "b": 0x100}
        self.expect_marks([w, dict(w)], "creation marks", path, ln)
        self.hit("in-pass creations marked (pattern %d)" % pat)
        for fx, fy in self.footprint(x, y, {0: 0, 1: 2, 2: 3, 3: 2, 4: 3, 5: 2}[pat]):
            self.P["marks"].setdefault((fx, fy), []).append(size)

    def creation_remark(self, room, x, y, cls, path, ln):
        """After SUnitCreate, before 0x005B2EE4: the alignment setter 0x005543B0 -> 0x00554340 ->
        sub_00649CA0_PathPatternRefresh: UNIT_CollUnmark with the creation pattern, the pattern recomputed by
        PATH_PatternFromSize (no wraith case), UNIT_CollMark."""
        size, pat0 = self.creation_marks(room, x, y, cls)
        _, pat = self.creation_marks(room, x, y, cls, wraith=False)
        if pat0 != pat:
            self.hit("post-create pattern refresh changed the pattern %d -> %d" % (pat0, pat))
        w = {"f": "PM", "room": room, "x": x, "y": y, "a": pat, "b": 0x100}
        u = dict(w, f="PU", a=pat0)
        self.expect_marks([u, w], "post-create unmark / re-mark", path, ln)

    # predicates
    def logic_region_id_at(self, hint, x, y):
        r = self.room_at(hint, x, y)
        if not r:
            return 0
        lg = self.P["lg"].get(r)
        if lg is None:
            raise NotLogged("logic record of room %08x" % r)
        if lg["fl"] & 1:
            return lg["first"] if lg["first"] is not None else -1
        tx, ty = lg["t"]
        gx = int(x / 5) - tx       # signed division truncated toward zero (0x66666667 multiply-shift)
        gy = int(y / 5) - ty
        g = lg.get("grid")
        if g is None:
            raise NotLogged("box grid of room %08x" % r)
        v = g[2][gy][gx]
        return -1 if v is None else v

    def spawn_class_cell_test(self, cls, hint, x, y, flag=1):
        t = self.t
        b = t.m(cls, 0x02, "<h") if t.valid(cls) else -1
        if b == 298:
            self.hit("SpawnClassCellTest: BaseId 298 (vilemother1) passes with flag 1")
            return 1 if flag else (1 if self.collision_test(hint, x, y, 2, 0x3C01) == 0 else 0)
        if b not in CLASS_CELL:
            return 1
        dx, dy, mask = CLASS_CELL[b]
        cx, cy = x + dx, y + dy
        r = self.room_at(hint, cx, cy)
        self.hit("SpawnClassCellTest: BaseId %d offset-cell tests" % b)
        if not r:
            return 0
        return 1 if self.collision_test(r, cx, cy, 2, mask) == 0 else 0

    def near_warp_test(self, room, x, y, lid):
        if not room or not lid:
            return 0
        p = self.nwp
        self.nwp = None
        if p is None:
            raise NotLogged("NearWarpTest warp points (NWP)")
        wd = struct.unpack_from("<i", self.t.lv[lid], 0x0C)[0]
        self.ok(p["wd"] == wd, "NearWarpTest WarpDist %d, levels.bin %d" % (p["wd"], wd))
        for i in range(max(p["n"], 0)):
            dx, dy = x - p["xs"][i], y - p["ys"][i]
            if dx * dx + dy * dy < wd:
                self.ok(self.nww is None, "NearWarpTest: the waypoint lookup ran after a warp-point hit")
                self.nww = None
                self.hit("NearWarpTest: near a warp point")
                return 1
        q = self.nww
        self.nww = None
        if q is None:
            raise CollMismatch("NearWarpTest: no type-11 point logged although no warp point is near")
        self.hit("NearWarpTest: type-11 point lookups")
        if q["x"] <= 0 or q["y"] <= 0:
            self.hit("NearWarpTest: no type-11 point")
            return 0
        dx, dy = x - 5 * q["x"], y - 5 * q["y"]
        if dx * dx + dy * dy < wd:
            self.hit("NearWarpTest: near the type-11 point")
            return 1
        return 0

    def ev_NWP(self, d, ln, path):
        """The level's warp points at NearWarpTest. Plan 0022 Phase 2: tools/drlg.py gen predicts the list each build
        leaves (sub_006423D0_LevelWarpPointsBuild on the room list, preset room flags from the DS1 scan); the
        prediction replaces the logged list. Plan 0026 Phase 2: an outdoor room's flags are its grid0 cell from the
        outdoor model (drlg/outdoor); a build whose prediction still has unknown rooms keeps the logged list as an input."""
        lev = d["p"] - 0x1E0
        pred = None
        for b in getattr(self, "wp_pred", {}).get(lev, []):
            if b[0] < ln:
                pred = b
        if pred is None:
            self.hit("NearWarpTest warp points: no build of the level in the log (logged input)")
            self.nwp = d
            return
        _ln, lid, xs, ys, unk = pred
        k = min(d["n"], 9)
        same = d["n"] == len(xs) and d["xs"][:k] == xs[:k] and d["ys"][:k] == ys[:k]
        if same:
            self.hit("NearWarpTest warp points predicted (level %d)" % lid)
            self.nwp = dict(d, xs=xs + [0] * (9 - len(xs)) if len(xs) < 9 else xs, ys=ys + [0] * (9 - len(ys)) if len(ys) < 9 else ys,
                            n=len(xs))
        elif unk:
            lg = list(zip(d["xs"][:k], d["ys"][:k]))
            it = iter(lg)
            sub = all(p in it for p in zip(xs, ys))      # the predicted (preset-room) points, in order, among the logged
            self.ok(sub and d["n"] <= 9, "%s:%d NearWarpTest level %d: predicted preset-room points %s not in order among the "
                    "logged %s" % (os.path.basename(path), ln, lid, list(zip(xs, ys)), lg))
            self.hit("NearWarpTest warp points: level %d, preset-room points predicted in order; the %d outdoor-room point(s) are "
                     "drlg/outdoor's (logged input)" % (lid, d["n"] - len(xs)))
            self.nwp = d
        else:
            self.ok(False, "%s:%d NearWarpTest level %d warp points %d %s %s, predicted %d %s %s" % (os.path.basename(path), ln, lid,
                    d["n"], d["xs"][:k], d["ys"][:k], len(xs), xs, ys))
            self.nwp = d

    def ev_NWW(self, d, ln, path):
        self.nww = d
        self.nw_reached = True
        self.nw_point = d

    def ev_NW0(self, d, ln, path):
        self.nw = d
        self.nw_reached = False
        self.nw_cbs = []
        self.nw_point = None

    def ev_NW1(self, d, ln, path):
        """R1: around every NearWarpTest call the level seed +0x1C4 and the level's active rooms. drlg/0005 section 9:
        only the waypoint lookup of a Position level steps the level seed (once) and may activate the waypoint room."""
        a = self.nw
        self.nw = None
        if a is None:
            return
        name = os.path.basename(path)
        lid = self.cb_info.get(a["room"], {}).get("lid")
        pos = lid is not None and self.t.position(lid)
        reached = self.nw_reached
        cbs = self.nw_cbs
        self.nw_cbs = []
        same_seed = a["lseed"] == d["lseed"]
        before, after = set(a["act"] or []), set(d["act"] or [])
        added = after - before
        self.hit("R1: NearWarpTest calls with the level seed and the active rooms asserted")
        if not reached:
            self.ok(same_seed and not added and before == after, "%s:%d R1: level seed or active rooms changed across "
                    "NearWarpTest without the waypoint lookup (level %s)" % (name, ln, lid))
            return
        # the waypoint lookup: RoomActivateB on the room holding the type-11 point (drlg/0005 section 9)
        q = self.nw_point
        ok_rooms = before <= after and len(added) <= 1
        if added:
            r = next(iter(added))
            rc = self.rects.get(r)
            holds = rc is not None and q is not None and rc[0] <= 5 * q["x"] < rc[0] + rc[2] and rc[1] <= 5 * q["y"] < rc[1] + rc[3]
            self.ok(holds and r in cbs, "%s:%d R1: the room activated inside NearWarpTest is not the waypoint room" % (name, ln))
            self.hit("R1: waypoint lookups that activated the waypoint room (level %s, a CB inside the call)" % lid)
        self.ok(ok_rooms, "%s:%d R1: active rooms changed by more than the waypoint room" % (name, ln))
        if not pos:
            self.ok(same_seed, "%s:%d R1: level %s (Position 0): level seed changed across NearWarpTest" % (name, ln, lid))
            self.hit("R1: waypoint lookups in a Position 0 level, level seed kept")
            return
        lo, hi = (int(v, 16) for v in a["lseed"].split(":"))
        st = "%08x:%08x" % step(lo, hi)
        self.ok(same_seed or d["lseed"] == st, "%s:%d R1: Position level %s: level seed %s -> %s, neither kept nor one step"
                % (name, ln, lid, a["lseed"], d["lseed"]))
        self.hit("R1: Position level %s, waypoint lookup reached: level seed %s" % (lid, "kept" if same_seed else "stepped once"))

    def spawn_pos_on_tile(self, room, rs):
        """sub_005B2700_SpawnPosOnTile: (x, y) or None; draws on the room seed rs."""
        P = self.P
        F = P["floors"].get(room)
        if F is None:
            raise NotLogged("floor entries of room %08x" % room)
        n = len(F)
        if n == 0:
            return None
        i = rs.rangeb(n)
        if i == 0:
            i = 1
        stop = i - 1
        tx, ty = P["trect"][room][0], P["trect"][room][1]
        if i == stop:
            return None
        while True:
            if i >= n:
                raise CollMismatch("SpawnPosOnTile reads floor entry %d of %d" % (i, n))
            x, y, _fl, tp, _o = F[i]
            if tp and self.tiles.w6(tp) & 2:
                cx, cy = (x + tx) * 5 + 3, (y + ty) * 5 + 3
                if self.cell_test(room, cx, cy, 0x100) == 0:
                    for ox, oy in TILE_OFFSETS:
                        if self.collision_test(room, cx + ox, cy + oy, 2, 0x1C09) == 0:
                            self.hit("SpawnPosOnTile: tile found")
                            return cx, cy
                else:
                    self.hit("SpawnPosOnTile: tile centre holds 0x100 (or no room)")
            i = (i + 1) % n
            if i == stop:
                return None

    # --- C1 / C2 ----------------------------------------------------------------------------------------------
    def ev_DC(self, d, ln, path):
        self.pend_dc = (d, ln)

    def ev_DCX(self, d, ln, path):
        got = getattr(self, "pend_dc", None)
        self.pend_dc = None
        if not got or "cells" not in got[0]:
            return
        d0, ln0 = got
        before, after = d0["cells"], d["cells"]
        plus = [(2, 2), (1, 2), (3, 2), (2, 1), (2, 3)]
        if d0["dc"]:
            keep = all((before[yy][xx] or 0) & 0x100 == (after[yy][xx] or 0) & 0x100 for xx, yy in plus) and \
                all((after[yy][xx] or 0) & 0x8000 == (before[yy][xx] or 0) & 0x8000 for yy in range(5) for xx in range(5))
            self.ok(keep and d["mm"] == d0["mm"] and d["pat"] == d0["pat"],
                    "%s:%d C1: deadCol 1 class %d corpse changed its mark" % (os.path.basename(path), ln, d0["cls"]))
            has = (after[2][2] or 0) & 0x100
            self.hit("C1: deadCol 1 deaths (class %d)%s" % (d0["cls"], "" if has else " (centre without 0x100)"))
        else:
            ok = all((after[yy][xx] or 0) & 0x8000 for xx, yy in plus if after[yy][xx] is not None) and d["mm"] == 0x8000 \
                and d["pat"] == 5
            self.ok(ok, "%s:%d C1: deadCol 0 class %d corpse is not a 0x8000 plus" % (os.path.basename(path), ln, d0["cls"]))
            self.hit("C1: deadCol 0 deaths re-marked as a 0x8000 plus")
        self.dcs.append((d0, d))
        self.dead_dc[d0["u"]] = d0["dc"]

    def ev_DCR(self, d, ln, path):
        dc = self.dead_dc.get(d["u"])
        if dc is None:
            return
        c = d["cells"][2][2]
        self.hit("C1: later re-dumps of a deadCol %d corpse centre: %s" % (dc, "0x100 kept" if c is not None and c & 0x100
                                                                          else "no 0x100"))

    def ev_MS(self, d, ln, path):
        self.pend_ms = d

    def ev_MSX(self, d, ln, path):
        d0 = getattr(self, "pend_ms", None)
        self.pend_ms = None
        if not d0 or "cells" not in d0:
            return
        coll = self.t.missile_collision(d0["cls"])
        self.ok(coll != 0, "C2: mask 0x40 set on missile class %d whose Collision is 0" % d0["cls"])
        # SizeMark(size, 0x40) on the 5x5 window around the missile
        exp = [row[:] for row in d0["cells"]]
        fp = {1: [(0, 0)], 2: [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)],
              3: [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]}.get(d0["size"], [])
        for dx, dy in fp:
            if exp[2 + dy][2 + dx] is not None:
                exp[2 + dy][2 + dx] |= 0x40
        self.ok(exp == d["cells"] and d["mm"] == 0x40, "C2: missile class %d size %d: cells after the 0x40 mark %s, model %s"
                % (d0["cls"], d0["size"], d["cells"], exp))
        self.hit("C2: Collision missiles marked 0x40 (class %d, size %d)" % (d0["cls"], d0["size"]))

    # --- plan 0038 batch H5d: unwindowed before / after pairs ---------------------------------------------------
    def ev_TCB0(self, d, ln, path):
        self.h5d[("TCB", d["th"])] = (d, ln, self.last_tcu)

    def ev_TCB1(self, d, ln, path):
        """sub_0064C860_TileCollisionUpdate (B1): in the map RoomAtSubtile finds for the entry's top-left subtile, AND-NOT
        the current tile's 25 bytes (rows reversed), then OR the new tile's when one is given; nothing when no room."""
        got = self.h5d.pop(("TCB", d["th"]), None)
        if not got:
            return
        d0, ln0, tcu = got
        name = os.path.basename(path)
        b0, b1 = d0["cells"], d["cells"]
        if tcu is None or tcu.get("e") != d0["e"]:
            self.ok(False, "%s:%d TCB0 without its TCU line" % (name, ln0))
            return
        if all(v is None for row in b0 for v in row):
            self.ok(b1 == b0, "%s:%d TileCollisionUpdate with no room at the tile changed cells" % (name, ln))
            self.hit("H5d TileCollisionUpdate: no room holds the tile's top-left (no write)")
            return
        flat = [v for row in b0 for v in row]
        exp = list(flat)
        if None in exp:
            self.ok(False, "%s:%d TileCollisionUpdate block only partly in a room" % (name, ln0))
            return
        old = self.tiles.bytes_of(tcu["old"]) if tcu["old"] else None
        new = self.tiles.bytes_of(tcu["new"]) if tcu["new"] else None
        if old:
            stamp(exp, 5, 0, 0, old, clear=True)
        if new:
            stamp(exp, 5, 0, 0, new)
        got1 = [v for row in b1 for v in row]
        self.ok(exp == got1, "%s:%d TileCollisionUpdate block: game %s, model %s" % (name, ln, got1, exp))
        kind = "re-stamp" if new else "clear"
        self.hit("H5d TileCollisionUpdate in an active room, block predicted (%s)" % kind)
        changed = sum(1 for a, b in zip(flat, got1) if a != b)
        self.hit("H5d TileCollisionUpdate: cells changed", changed)
        if old and new and old != new:
            self.hit("H5d TileCollisionUpdate: old and new tiles differ")
        # the separating case of the plain AND-NOT: a bit the old tile clears that another stamp of the activation
        # also set in that cell (a re-computation from the other tiles would keep it)
        sx, sy = d0["sx"], d0["sy"]
        tgt = None
        for r, m in self.model.items():
            if m.has(sx, sy):
                tgt = r
        others = [0] * 25
        skipped = False
        for (ex, ey, tp) in self.cb_stamps.get(tgt, []):
            if (ex, ey) == (sx, sy) and tp == tcu["old"] and not skipped:
                skipped = True
                continue
            if abs(ex - sx) < 5 and abs(ey - sy) < 5:
                tmp = [0] * 81
                stamp(tmp, 9, ey - sy + 2, ex - sx + 2, self.tiles.bytes_of(tp))
                for r in range(5):
                    for c in range(5):
                        others[r * 5 + c] |= tmp[(r + 2) * 9 + c + 2]
        if old:
            ob = [0] * 25
            stamp(ob, 5, 0, 0, old)
            nb = [0] * 25
            if new:
                stamp(nb, 5, 0, 0, new)
            sep = sum(1 for i in range(25) if flat[i] & ob[i] & others[i] & ~nb[i])
            if sep:
                self.hit("H5d TileCollisionUpdate: cells where the clear removed a bit another tile stamped", sep)
                kept = sum(1 for i in range(25) if flat[i] & ob[i] & others[i] & ~nb[i] & got1[i])
                self.ok(kept == 0, "%s:%d TileCollisionUpdate: %d cells kept a bit another tile stamped" % (name, ln, kept))

    def ev_IM0(self, d, ln, path):
        self.h5d[("IM", d["th"])] = (d, ln)

    def ev_IM1(self, d, ln, path):
        """An item's mark (F1, types 3-5 through SizeMark; UNIT_CollMarkRect through RectOrWH): one cell, 0x200."""
        got = self.h5d.pop(("IM", d["th"]), None)
        if not got:
            return
        d0, ln0 = got
        name = os.path.basename(path)
        if d0["f"] == "SM":
            args_ok = d0["args"] == [1, 0x200]
        else:
            args_ok = d0["args"] == [1, 1, 0x200]
        self.ok(args_ok, "%s:%d item mark (%s) of class %d: size / mask %s, model %s" % (
            name, ln0, d0["f"], d0["cls"], d0["args"], "[1, 512]" if d0["f"] == "SM" else "[1, 1, 512]"))
        b0, b1 = d0["cells"], d["cells"]
        if b0 is None or b0[2][2] is None:
            self.hit("H5d item marks: no room holds the cell")
            return
        exp = [row[:] for row in b0]
        exp[2][2] |= 0x200
        self.ok(exp == b1, "%s:%d item mark of class %d: cells after %s, model %s" % (name, ln, d0["cls"], b1, exp))
        self.hit("H5d item marks predicted (%s: one cell 0x200)" % d0["f"])
        if not b0[2][2] & 0x200:
            self.hit("H5d item marks on a cell without 0x200 before")

    def ev_PN0(self, d, ln, path):
        self.h5d[("PN", d["th"])] = (d, ln)

    def ev_PN1(self, d, ln, path):
        """PatternMark / PatternUnmark (F2) with pattern 3 (plus of m, 0x2000 on the centre) or 4 (3x3 of m, 0x2000 on
        the plus)."""
        got = self.h5d.pop(("PN", d["th"]), None)
        if not got:
            return
        d0, ln0 = got
        b0, b1 = d0["cells"], d["cells"]
        if b0 is None or b0[2][2] is None:
            self.hit("H5d patterns 3/4: no room holds the centre")
            return
        clear = d0["f"] == "PU"
        p, m = d0["p"], d0["m"]
        plus = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
        sq = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
        ops = []
        if p == 3:
            ops = [(plus, m)] + ([([(0, 0)], 0x2000)] if m else [])
        else:
            ops = [(sq, m)] + ([(plus, 0x2000)] if m else [])
        exp = [row[:] for row in b0]
        for cells, v in ops:
            for dx, dy in cells:
                if exp[2 + dy][2 + dx] is None:
                    continue
                if clear:
                    exp[2 + dy][2 + dx] &= ~v & 0xFFFF
                else:
                    exp[2 + dy][2 + dx] |= v
        self.ok(exp == b1, "%s:%d %s pattern %d mask %#x: cells after %s, model %s" % (
            os.path.basename(path), ln, d0["f"], p, m, b1, exp))
        self.hit("H5d %s pattern %d (mask %#x) predicted" % (d0["f"], p, m))

    def ev_SCT0(self, d, ln, path):
        self.h5d[("SCT", d["th"])] = (d, ln)

    def ev_SCT1(self, d, ln, path):
        """SpawnClassCellTest (H1) from the 11x11 cells the logger read around (x, y)."""
        got = self.h5d.pop(("SCT", d["th"]), None)
        if not got:
            return
        d0, ln0 = got
        b, fl = d0["base"], d0["flag"]
        site = "%08x" % d0["ret"]
        if b == 298 and fl:
            exp = 1
        elif b in CLASS_CELL or b == 298:
            dx, dy, mask = CLASS_CELL.get(b, (0, 0, 0x3C01))
            c = d0.get("cells")
            if c is None:
                self.hit("H5d SpawnClassCellTest: offset class without a room")
                return
            g = lambda xx, yy: c[5 + yy][5 + xx]
            def plus_ok(px, py, mk):
                if g(px, py) is None:
                    return 0
                v = 0
                for ox, oy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                    cv = g(px + ox, py + oy)
                    v |= 0x27 if cv is None else cv & mk
                return 1 if v == 0 else 0
            exp = plus_ok(dx, dy, mask)
            # plan 0038 H5d (collision 45): the cases a wrong reading would get wrong: the same size-2 test at the
            # unit's own cell (no offset), or with the other mask (0x3C01 <-> 0x01C0)
            if (dx, dy) != (0, 0) and plus_ok(0, 0, mask) != exp:
                self.hit("H5d SpawnClassCellTest BaseId %s: the offset decides (the own cell gives %d)" % (b, 1 - exp))
            alt = 0x01C0 if mask == 0x3C01 else 0x3C01
            if plus_ok(dx, dy, alt) != exp:
                self.hit("H5d SpawnClassCellTest BaseId %s: the mask decides (mask %#x gives %d)" % (b, alt, 1 - exp))
        else:
            exp = 1
        self.ok((d["r"] & 0xFF) == exp, "%s:%d SpawnClassCellTest class %d (BaseId %s) flag %d at %s: game %d, model %d" % (
            os.path.basename(path), ln, d0["cls"], b, fl, site, d["r"], exp))
        key = b if (b in CLASS_CELL or b == 298) else "other"
        self.hit("H5d SpawnClassCellTest predicted: BaseId %s, flag %d, caller %s, result %d" % (key, fl, site, exp))

    def ev_LPP0(self, d, ln, path):
        self.h5d[("LPP", d["th"])] = (d, ln)

    def ev_LPP1(self, d, ln, path):
        """sub_0066AC40_LevelPointPick: n = the points of the type or of its group; n >= 1: one draw on the level seed,
        r = low & (n - 1) for a power of two, else low mod n, the (r + 1)-th match; n = 0: entry 0, no draw."""
        got = self.h5d.pop(("LPP", d["th"]), None)
        if not got:
            return
        d0, ln0 = got
        if self.lpp_groups is None:
            raw = exe_read(self.exe, LPP_GROUPS, 8 * 64)
            self.lpp_groups = [struct.unpack_from("<Ii", raw, 8 * i) for i in range(64)]
        t = d0["type"]
        G = self.lpp_groups

        def match(pt):
            return pt == t or (0 <= t < len(G) and 0 <= pt < len(G) and G[t][0] != 0 and G[t][1] == G[pt][1])
        pts = d0["pts"]
        idx = [i for i, p in enumerate(pts) if match(p[2])]
        n = len(idx)
        lo, hi = (int(v, 16) for v in d0["seed"].split(":"))
        if n == 0:
            k, seed = 0, (lo, hi)
        else:
            seed = step(lo, hi)
            r = seed[0] & (n - 1) if n & (n - 1) == 0 else seed[0] % n
            k = idx[r]
        want = (pts[k][0], pts[k][1]) if pts else None
        st = "%08x:%08x" % seed
        self.ok(want == (d["x"], d["y"]) and st == d["seed"], "%s:%d LevelPointPick level %d type %d n %d: game (%d, %d) %s, "
                "model %s %s" % (os.path.basename(path), ln, d0["lid"], t, n, d["x"], d["y"], d["seed"], want, st))
        self.hit("H5d LevelPointPick predicted: level %d, type %d, matches %d%s" % (
            d0["lid"], t, n, " (Position %d)" % self.t.position(d0["lid"]) if d0["lid"] is not None else ""))
        if n >= 2:
            alt = [(pts[i][0], pts[i][1]) for i in idx if (pts[i][0], pts[i][1]) != want]
            if alt:
                self.hit("H5d LevelPointPick: n >= 2 with another match at a different point (the pick separates)")

    # --- report -----------------------------------------------------------------------------------------------
    def report(self):
        print("collision: TL %d tile records checked against the DT1 files, %d differ (%d DT1 files)" % (
            self.tiles.checked, self.tiles.bad, len(self.tiles.paths)))
        for k in sorted(self.stats):
            print("  %-86s %d" % (k, self.stats[k]))
        r = self.r3
        print("  R3 (snapshot vs activation model): %d pass rooms; cells differing %d before the window marks, %d after "
              "(%d explained by the logged preset/object marks); rooms exact %d, with residue %d" % (
                  r["rooms"], r["diff0"], r["diff1"], r["explained"], r["rooms_exact"], r["rooms_resid"]))
        for k, v in sorted(r["resid_bits"].items(), key=lambda kv: -kv[1])[:16]:
            print("    residue snapshot %s model: %d cells" % (k, v))


def cmd_check(argv):
    import monspawn
    return monspawn.cmd_check(argv)


def main(argv):
    if len(argv) < 2 or argv[1] != "check":
        print(__doc__)
        return 2
    return cmd_check(argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))

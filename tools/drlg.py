#!/usr/bin/env python3
"""DRLG models checked against runtime logs (plan 0008).

Usage:
  python3 -I tools/drlg.py roomk <run.log> [...] [--root workspace/merged] [--exe PATH] [-v]
  python3 -I tools/drlg.py tables [--exe PATH]
  python3 -I tools/drlg.py p1cmp <seed-tree.log> <roomk.log>
  python3 -I tools/drlg.py gen <gen.log> [...] [--root workspace/merged] [--exe PATH] [-v]

`roomk` replays every DRLG room window logged by tools/gdb/drlg-roomk.gdb (re-seed, LvlSub passes, tile
build, activation draw) and predicts the room seed at each LSUBX, at RACT and at AROOM, so k (the
room-seed steps between the re-seed from +0x04 and the activation draw) is predicted per room. The
model is docs/findings/drlg/0002-room-build-draws.md, written from the code:
  - k_sub: the LvlSub passes of a type-1 room (sub_006707A0_LvlSubApply), on the grids logged at the
    first LSUB line; each later LSUB grid and the TINIT grid are checks of the modelled stamping, the
    theme fill and the border bits;
  - k_tile: the tile build (sub_0066EC10_RoomCellsBuild per layer, sub_0066E9B0_RoomCellBuild per cell)
    on the grids logged at TINIT; one draw per DRLG_PickTileByRarity whose primary key has >= 1
    candidate with a signed rarity sum > 0, the candidates read from the room's DT1 list
    (tools/dt1.py, files under --root); the bit-2 path against the tile entries the model built
    for the neighbour rooms of the same act copy (state carried across rooms, in log order);
  - the boundary oracle sub_0066D9E0_Orient89Unit (row `objects`): each modelled call consumes the
    next logged O89 line of the room (seed in must match) and its O89D draw, if any.
  - the DT1 list (fix F2 of the plan 0008 P2 review): the logged list must equal LvlTypes File i+1 per
    bit i of the room's +0x50, prefixed "DATA/GLOBAL/TILES/" (backslashes in the game), then the three fixed files
    (DRLG_LevelDt1ListBuild); +0x50 must be LvlPrest.Dt1Mask for type 2, and for type 1 the level-type
    value of sub_006750F0 OR-ed with the Dt1Mask of every SubType LvlSub record the room picked;
  - the type-2 grids (fix F1): sub_006667D0_PresetRoomGridPrepare modelled on the DS1 (tools/ds1.py), views at
    the preset origin, the 0x84 border and the i << 18 layer bits written into a per-process DS1 cache
    as DS1_LoadCached shares it; each TINIT grid set must be reproduced by a LvlPrest File of the
    room's preset (the file index is not logged), the same with a fresh DS1 per room, and one file
    must fit every room of a preset instance.
Plan 0027 Phase 2: `gen` runs these passes too, in every log that has OD0 and LSUB lines, with the type-1 grids of the
first LSUB taken from GenModel's out-room prediction (drlg/0008 16.4) instead of the log (run_log(..., prep_pred));
the logged grids stay as the check. In logs with tools/gdb/collision.py lines (TL, CB) every activation dump's wall,
floor and shadow arrays of every near room are compared with the model's entries in creation order: position,
orientation and the full entry flags (setflags / cellflags: the cell bits, Orient89Unit's 0x20 from its row table,
the warp and AnimTilesBuild 0x8s; the tile's flags16 bits from the logged tile record), and AnimTilesBuild's frame
entries (sub_0066D440) against the formula of their kind.
Inputs taken from the log because they are run-time state, not data: the type-1 grids (first LSUB;
drlg/outdoor; predicted inside `gen`), the type-2 file index (Phase 3), the neighbour list and which neighbours are built,
the warp records (LvlWarp row per node) and the level's warp ids. The type-2 tile build walks the
logged TINIT grids, which the prepare model has checked. Exit 0 only if every RACT, LSUBX and AROOM
line is predicted and every check holds. Stdlib only.

`gen` (plan 0008 Phase 3) replays a tools/gdb/drlg-gen.gdb log: per level, the create-time and build-time
seed Init(act base + id), every level-seed draw of the three generators as docs/findings/drlg/0003 models
them (DRLG_RoomCreate, sub_00666ED0_PresetInstanceCreate, sub_00667430_PresetLevelCreate,
sub_006738C0_MazePresetFile), the preset file index of every instance (draw, level/cell/maze overrides,
maze rotation) against the File cell the game loads, room counts and creation order, and
sub_006706A0_LvlSubRoll. Exit 0 only if every check holds.

Plan 0026 Phase 2 (docs/findings/drlg/0008-outdoor.md): the outdoor window OD0..OD1 is modelled (class Outdoor: the
level outline, seam mark, border pass, border stamps, placers, waypoint and shrines, and the act generators of all
five acts; Act III's level rects and LevelLinks list from the jungle layout and the Kurast stack on the act seed,
act_links_a3), so the seed after the window, every preset anchor OutdoorRoomsCreate makes (Def, position, the file
index of cell bits 16-19 at PIO, the grid0 flags at PRC), every out room (rect, order) and each out room's +0x28
flags at LWP (grid0 | 0x80000) are predicted. With tools/gdb/drlg-outdoor.gdb logs it also checks every level-seed
draw in the window (ODD) and the final def grid, grid0 and cell grid cell for cell, with the outdoor flags (ODG).
Plan 0026 Phase 3 follow-up (drlg/0008 § 16.3-16.4): Act I roads keep their jittered polylines (sub_00681240), and in
logs that also carry tools/gdb/drlg-roomk.py lines, every type-1 room's first LSUB grids are predicted from the latest
outdoor model of its level (sub_0067D2D0_OutRoomGridPrepare: orientation and wall zero, floor 0x40002 on 8x8, the road
tiles of sub_00680C80_OutRoomRoadGrid through g_RoadCodes).

Plan 0022 Phase 2 (docs/findings/drlg/0006-maze.md, 0007-warps.md): the maze window MZ0..MZ1 is modelled (class Maze:
every level type's start, growth, merge, finisher specials, placement and themes), so the seed after the window, the
room list (absolute rects, Def, forced index) and each maze cell's forced index (MFR) are predicted. The inputs it
reads from the act (the two tombs, level 27's index and rect, level 108's rect, the level rect) come from the act
model (class Act: DRLG_ActCreate's draws and the act link builder, link_build / act_links, the one implementation that
tools/outdoor_replay.py imports). With tools/gdb/drlg-maze.gdb logs it also checks: every level-seed draw in the window
(MZD), the act inputs (MZA), each LevelLinkBuild call (LNK0/LNKL/LK27/LNK1: the act-seed copy, rects, choices, the
level-27 draw), the act's LevelLinks list (LNKS; Act III's from the plan 0026 jungle layout), and per build the room flags' warp-slot
and waypoint bits (DS1_PresetMapScan modelled on the DS1) and the warp point list +0x1E0 (LWP). At every LevelInit end
it predicts the warp points (wp_by_level, used by tools/collision.py for NearWarpTest).

Plan 0016 Phase 2 (docs/findings/drlg/0004-preset-units.md): DRLG_PresetUnitDropRolls is modelled
(PresetUnitData, DS1 units through tools/ds1.py's parser); `--preset-oracle` restores it as the plan 0008
boundary oracle (ADR-0004). With the tags of tools/gdb/drlg-preset.py the model also predicts the room seed into
the room-seed rolls (step(Init(level lo)) from the room's RL line), every instance list after both roll callers and
after DRLG_PresetRoomLoadDs1 (centre monster, client river objects), the instance and room lists around
DRLG_PresetUnitsToRoom (a re-prepared room's previous list as the tail of its list before), the tail of each list sub_005559A0_RoomPresetUnits walks (units other code
prepends are inputs), Populate 0 -> RoomPopLevelId 0, and the level-27 index draw (on the logged act seed). With tools/gdb/drlg-preset-wp.py:
the logic flags per Logicals and the pop index at every logged player position (PopPad); watch hits are counted.

`p1cmp` compares the RACT seeds of a tools/gdb/seed-tree.gdb log (run:2026-10-11-seed-tree-p1) with a
roomk log of the same -seed, room by room (keyed by room +0x04): equal seeds mean equal k. Exit 0 only
if every room of the old log is in the new one with the same seeds.

`tables` prints the two orientation remap tables (0x006EF620, 0x006EF574) read from the pinned
game.exe, which the bit-2 merge uses.
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ds1 as ds1mod  # noqa: E402
import dt1 as dt1mod  # noqa: E402
from rng import INIT_HIGH, MASK, step  # noqa: E402

ROOT = os.path.dirname(HERE)
DEFAULT_DATA = os.path.join(ROOT, "workspace", "merged")
DEFAULT_EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
PINNED = "631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf"

REMAP_O = 0x006EF620    # s32[20] per new orientation 0..19: row 0..5 of REMAP_T, -1 keep, -2 no merge
REMAP_T = 0x006EF574    # s32[row*7 + old orientation (0..7)], 43 cells: merged orientation


class ModelError(Exception):
    pass


# ---------------------------------------------------------------------------------------------- data

def exe_read(path, va, n):
    """Read n bytes at virtual address va of a PE file (image base 0x400000 assumed by the caller)."""
    data = open(path, "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    base = struct.unpack_from("<I", data, pe + 24 + 28)[0]
    sec = pe + 24 + opt
    rva = va - base
    for i in range(nsec):
        # IMAGE_SECTION_HEADER after the 8-byte name: VirtualSize, VirtualAddress, SizeOfRawData,
        # PointerToRawData (before 2026-10-12 the first two and the last two were swapped, so every
        # read landed at a wrong file offset; see drlg/0002 § Bit2TileMerge).
        vsize, vaddr, rawsize, raw = struct.unpack_from("<IIII", data, sec + 40 * i + 8)
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            off = raw + rva - vaddr
            return data[off:off + n]
    raise ModelError("VA 0x%08X not in any section" % va)


def remap_tables(exe):
    import hashlib
    h = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    if h != PINNED:
        raise ModelError("%s is not the pinned game.exe (sha256 %s)" % (exe, h))
    o = list(struct.unpack("<20i", exe_read(exe, REMAP_O, 80)))
    t = list(struct.unpack("<43i", exe_read(exe, REMAP_T, 172)))
    return o, t


def excel_bin(root, name):
    d = open(os.path.join(root, "data", "global", "excel", name + ".bin"), "rb").read()
    n = struct.unpack_from("<I", d)[0]
    size = (len(d) - 4) // n
    if 4 + n * size != len(d):
        raise ModelError("%s.bin: size does not divide" % name)
    return [d[4 + i * size: 4 + (i + 1) * size] for i in range(n)]


class LvlSub:
    def __init__(self, rec):
        self.type = struct.unpack_from("<i", rec, 0x00)[0]
        self.file = rec[0x04:0x40].split(b"\0", 1)[0].decode("latin-1")
        self.checkall = struct.unpack_from("<i", rec, 0x40)[0]
        self.prob = struct.unpack_from("<5i", rec, 0x11C)
        self.trials = struct.unpack_from("<5i", rec, 0x130)
        self.max = struct.unpack_from("<5i", rec, 0x144)


class LvlWarp:
    def __init__(self, rec):
        self.id = struct.unpack_from("<i", rec, 0x00)[0]
        self.exitwalk = struct.unpack_from("<ii", rec, 0x14)       # ExitWalkX, ExitWalkY (plan 0038 H5c)
        self.litversion = struct.unpack_from("<i", rec, 0x24)[0]
        self.tiles = struct.unpack_from("<i", rec, 0x28)[0]
        self.dir = rec[0x2C:0x2D].decode("latin-1")


class LvlPrest:
    def __init__(self, rec):
        self.defn = struct.unpack_from("<i", rec, 0x00)[0]
        self.files = [rec[0x44 + 0x3C * i:0x80 + 0x3C * i].split(b"\0", 1)[0].decode("latin-1") for i in range(6)]
        self.dt1mask = struct.unpack_from("<I", rec, 0x1AC)[0]


# Fixed DT1 files that DRLG_LevelDt1ListBuild (0x0066F240) appends after the mask files (drlg/0001).
FIXED_DT1 = ["DATA\\GLOBAL\\Tiles\\Act1\\Outdoors\\Blank.dt1", "DATA\\GLOBAL\\Tiles\\Act1\\Barracks\\InvisWal.dt1",
             "DATA\\GLOBAL\\Tiles\\Act1\\Barracks\\Warp.dt1"]
LVLTYPES_PREFIX = "DATA\\GLOBAL\\TILES\\"
# sub_006750F0_OutdoorRoomsCreate (0x00675105..0x00675139): DT1 mask passed to sub_0067D540_OutRoomCreate
# by level type (+0x1C0); other level types pass 0.
OUTROOM_MASK = {2: 0x44103, 16: 0x1, 22: 0x1, 27: 0x1, 28: 0x1, 21: 0x4, 30: 0x11, 31: 0x11}
DS1_OLD_ORIENT = 0x006EEF20   # u32[44]: v < 7 orientation remap (DS1_Parse step 7)


class Data:
    def __init__(self, root, exe):
        self.root = root
        self.exe = exe
        self.remap_o, self.remap_t = remap_tables(exe)
        self.old_orient = list(struct.unpack("<44I", exe_read(exe, DS1_OLD_ORIENT, 176)))
        self.lvlsub = [LvlSub(r) for r in excel_bin(root, "lvlsub")]
        self.lvlsub_dt1mask = [struct.unpack_from("<I", r, 0x48)[0] for r in excel_bin(root, "lvlsub")]
        self.lvlwarp = [LvlWarp(r) for r in excel_bin(root, "lvlwarp")]
        self.lvlprest = [LvlPrest(r) for r in excel_bin(root, "lvlprest")]
        self.drlgtype = [struct.unpack_from("<I", r, 0x30)[0] for r in excel_bin(root, "leveldefs")]
        self.lvltypes = [[r[0x3C * i:0x3C * (i + 1)].split(b"\0", 1)[0].decode("latin-1") for i in range(32)]
                         for r in excel_bin(root, "lvltypes")]
        # sub_0066D9E0_Orient89Unit's tables (plan 0027): per level (id, first, last) at 0x006EEFC8 (to 0x006EF18B), then
        # 0x1C-byte rows at 0x006EF188: main, sub, is-9, unit id, unit type, dx, dy (subtiles)
        lv = exe_read(exe, 0x006EEFC8, 0x006EF18C - 0x006EEFC8)
        self.o89_levels = [struct.unpack_from("<3i", lv, 12 * i) for i in range(len(lv) // 12)]
        self._o89_raw = exe
        self._o89_rows = {}
        self._dt1 = {}
        self._lists = {}
        self._subds1 = {}
        self._pristine = {}
        self.reset_process()

    def o89_row(self, i):
        if i not in self._o89_rows:
            self._o89_rows[i] = struct.unpack("<7i", exe_read(self._o89_raw, 0x006EF188 + 0x1C * i, 0x1C))
        return self._o89_rows[i]

    def o89_lookup(self, lid, cell, is9):
        """FUN_0066D960: the first row of the level's range whose main, sub and is-9 match the cell, else -1."""
        main, sub = (cell >> 20) & 0x3F, (cell >> 8) & 0xFF
        for lev, lo, hi in self.o89_levels:
            if lev != lid:
                continue
            for i in range(lo, hi + 1):
                r = self.o89_row(i)
                if (r[0], r[1], r[2]) == (main, sub, is9):
                    return i
        return -1

    def reset_process(self):
        """Per game process (one log): the DS1 cache of DS1_LoadCached (0x00665F40), whose buffers the
        type-2 prepare writes into."""
        self.preset_bufs = {}

    def dt1_list(self, ltype, mask):
        """DRLG_LevelDt1ListBuild (0x0066F240): LvlTypes File i+1 per set bit i of the room's +0x50, in
        bit order, prefixed, then the three fixed files."""
        out = []
        for i in range(32):
            if mask >> i & 1:
                out.append(LVLTYPES_PREFIX + self.lvltypes[ltype][i].replace("/", "\\"))
        return out + FIXED_DT1

    def preset_buf(self, cell):
        """DS1_LoadCached: one parsed DS1 per path per process, layers as mutable cell lists."""
        if cell not in self.preset_bufs:
            self.preset_bufs[cell] = buf_copy(self.preset_pristine(cell))
        return self.preset_bufs[cell]

    def preset_pristine(self, cell):
        """The DS1 as DS1_Parse leaves it (never written)."""
        if cell not in self._pristine:
            path = os.path.join(self.root, "data", "global", "tiles", cell.replace("\\", "/").lower())
            f = ds1mod.parse(open(path, "rb").read())
            L = f["layers"]
            orients = [list(L["orient%d" % i]) for i in range(f["wall_layers"])]
            if f["version"] < 7:     # DS1_Parse step 7, in the buffer, once per load
                for o in orients:
                    for j, c in enumerate(o):
                        if c >= len(self.old_orient):
                            raise ModelError("%s: v<7 orientation %d outside the remap table" % (cell, c))
                        o[j] = self.old_orient[c]
            self._pristine[cell] = dict(
                cols=f["cols"], rows=f["rows"], size=(f["size_x"], f["size_y"]),
                walls=[list(L["wall%d" % i]) for i in range(f["wall_layers"])], orients=orients,
                floors=[list(L["floor%d" % i]) for i in range(f["floor_layers"])], shadow=list(L["shadow"]))
        return self._pristine[cell]

    def tile_path(self, name):
        # The game prefixes DATA\GLOBAL\TILES; the merged tree is lower-case.
        p = name.replace("\\", "/").lower()
        return os.path.join(self.root, p)

    def dt1_keys(self, name):
        """{(orientation, main, sub): [rarity, ...] in file order} for one DT1."""
        if name not in self._dt1:
            h = dt1mod.parse(open(self.tile_path(name), "rb").read())
            keys = {}
            for t in h["tiles"]:
                keys.setdefault((t["orientation"], t["main_index"], t["sub_index"]), []).append(t["rarity"])
            self._dt1[name] = keys
        return self._dt1[name]

    def key_table(self, names):
        """Per DT1 list: key -> (n, sum) over the first 40 candidates, in slot order (TILE_FindInList)."""
        names = tuple(names)
        if names not in self._lists:
            per = [self.dt1_keys(n) for n in names]
            self._lists[names] = (per, {})
        return self._lists[names]

    def warp_lookup(self, wid, dirchar):
        """fn 0x0061F310: first LvlWarp row with Id == wid and a matching direction ('b' matches all)."""
        for i, w in enumerate(self.lvlwarp):
            if w.id == wid and (dirchar == "b" or w.dir == "b" or w.dir == dirchar):
                return i
        raise ModelError("no LvlWarp row for id %d dir %s (game: fatal)" % (wid, dirchar))

    def sub_ds1(self, rec):
        """LvlSub record's DS1 as the grids sub_006704E0_LvlSubLoadDs1 builds."""
        if rec not in self._subds1:
            s = self.lvlsub[rec]
            path = os.path.join(self.root, "data", "global", "tiles", s.file.replace("\\", "/").lower())
            raw = open(path, "rb").read()
            try:
                f = ds1mod.parse(raw)
                f["truncated"] = 0
            except ds1mod.Ds1Error:
                # Act1/Outdoors/Trees.ds1 ends 12 bytes into its last group (ds1.py KNOWN_MALFORMED);
                # DS1_Parse has no bounds check. Parse with zero padding: the layers are complete,
                # the missing group fields are taken from the run (LSUBX groups).
                f = ds1mod.parse(raw + b"\0" * 64)
                f["truncated"] = 1
            if f["version"] < 7:
                raise ModelError("LvlSub DS1 %s is v%d: orientation remap not modelled" % (s.file, f["version"]))
            cols = f["cols"]
            L = f["layers"]
            walls = []
            for i in range(f["wall_layers"]):
                w = list(L["wall%d" % i])
                if i >= 1:   # 0x006705CA: grid op 0 (or) with i << 18 on wall layers 1..
                    w = [c | (i << 18) for c in w]
                walls.append(w)
            orients = [list(L["orient%d" % i]) for i in range(f["wall_layers"])]
            floor = list(L["floor0"]) if f["floor_layers"] else None
            shadow = list(L["shadow"])
            groups = [(g["x"], g["y"], g["w"], g["h"]) for g in f["groups"]]
            self._subds1[rec] = dict(cols=cols, walls=walls, orients=orients, floor=floor,
                                     shadow=shadow, groups=groups, tag_type=f["tag_type"],
                                     nfloor=f["floor_layers"], nwall=f["wall_layers"],
                                     truncated=f["truncated"])
        return self._subds1[rec]


# ------------------------------------------------------------------------------- type-2 grid prepare

def preset_prepare(buf, rect, prect):
    """sub_006667D0_PresetRoomGridPrepare on the cached DS1 buffer `buf` (written in place, as the game
    does: the grids are views of the DS1 layers, sub_0067CCC0_GridView). Returns the views as
    {floor: [...], wall: [...], orient: [...], shadow: ...}, each [w, h, cells] like the logged grids.

    View: origin (room x - preset x, room y - preset y), (w+1) x (h+1) cells, row stride preset w + 1.
    Writes (grid op 0 = or): wall 0 border |= 0x84; wall i >= 1 all cells |= i << 18; floor i all cells
    |= i << 18; every floor border and the shadow border |= 0x84. Orientation layers are not written."""
    x, y, w, h = rect
    px, py, pw, ph = prect
    ox, oy, gw, gh, stride = x - px, y - py, w + 1, h + 1, pw + 1
    if ox < 0 or oy < 0 or (oy + gh - 1) * stride + ox + gw - 1 >= buf["cols"] * buf["rows"]:
        raise ModelError("type-2 view %r of preset %r outside the DS1 (%dx%d)" % (rect, prect, buf["cols"], buf["rows"]))
    allc = [(oy + j) * stride + ox + i for j in range(gh) for i in range(gw)]
    border = sorted({(oy + j) * stride + ox + i for j in range(gh) for i in range(gw)
                     if j in (0, gh - 1) or i in (0, gw - 1)})

    def orv(layer, idx, v):
        for k in idx:
            layer[k] = (layer[k] | v) & MASK

    if buf["walls"]:
        orv(buf["walls"][0], border, 0x84)
    for i in range(1, len(buf["walls"])):
        orv(buf["walls"][i], allc, i << 18)
    for i, fl in enumerate(buf["floors"]):
        orv(fl, allc, i << 18)
    for fl in buf["floors"]:
        orv(fl, border, 0x84)
    orv(buf["shadow"], border, 0x84)

    def view(layer):
        return [layer[k] for k in allc]
    return {"floor": [view(f) for f in buf["floors"]], "wall": [view(wl) for wl in buf["walls"]],
            "orient": [view(o) for o in buf["orients"]], "shadow": view(buf["shadow"])}


def buf_copy(buf):
    return dict(buf, walls=[list(v) for v in buf["walls"]], orients=[list(v) for v in buf["orients"]],
                floors=[list(v) for v in buf["floors"]], shadow=list(buf["shadow"]))


def grids_equal(model, logged):
    """model: views from preset_prepare; logged: the TINIT grids ([w, h, hex] per layer)."""
    def cells(g):
        return Grid.from_log(g).c
    if len(model["floor"]) != len(logged["floor"]) or len(model["wall"]) != len(logged["wall"]):
        return False
    pairs = list(zip(model["floor"], logged["floor"])) + list(zip(model["wall"], logged["wall"])) + \
        list(zip(model["orient"], logged["orient"])) + [(model["shadow"], logged["shadow"])]
    return all(m == cells(lg) for m, lg in pairs)


# --------------------------------------------------------------------------------------------- model

class Grid:
    def __init__(self, w, h, cells):
        self.w, self.h, self.c = w, h, cells

    @classmethod
    def from_log(cls, g):
        w, h, hx = g
        if not hx:
            return cls(max(w, 0), max(h, 0), [0] * (max(w, 0) * max(h, 0)))
        return cls(w, h, [int(hx[i:i + 8], 16) for i in range(0, len(hx), 8)])

    def get(self, x, y):
        if not (0 <= x < self.w and 0 <= y < self.h):
            raise ModelError("grid read out of range (%d,%d) in %dx%d" % (x, y, self.w, self.h))
        return self.c[y * self.w + x]

    def set(self, x, y, v):
        self.c[y * self.w + x] = v & MASK

    def copy(self):
        return Grid(self.w, self.h, list(self.c))


class Entry:
    __slots__ = ("o", "x", "y", "flags", "main", "sub", "tbits", "merged", "next", "mby")

    def __init__(self, o, x, y, flags, main, sub):
        self.o, self.x, self.y, self.flags, self.main, self.sub = o, x, y, flags, main, sub
        self.tbits = True          # the tile's flags16 bits apply (TILE_GetFlags16: bit 0 -> 0x4, bit 2 -> 0x800)
        self.merged = 0            # times sub_0066E740_Bit2TileMerge rewrote the flags (plan 0027 counters)
        self.mby = None            # plan 0038 H5c: the DRLG room whose build last merged into this entry
        self.next = None           # entry +0x20: the next entry of whatever list last linked it


class Chain:
    """A RoomTile node's entry list (node +0x04, linked through entry +0x20, head-inserted). Plan 0027: a real chain,
    because sub_0066E260_WarpTileAdd and sub_0066E360_HiddenWarpTilesAdd re-link an entry into a warp node's list
    (entry +0x20 = warp node +0x0C), which cuts the older entries off this node's chain for sub_0066E4C0's scan."""
    __slots__ = ("head",)

    def __init__(self):
        self.head = None

    def insert(self, _i, e):
        e.next = self.head
        self.head = e

    def __iter__(self):
        e, n = self.head, 0
        while e is not None and n < 100000:
            yield e
            e, n = e.next, n + 1


def cellflags(flags, cell):
    """The cell-bit part shared by sub_0066DB20_RoomTileSetFlags, sub_0066DDE0_TileEntryInit and
    sub_0066DF40_RoomShadowAdd (drlg/0002, plan 0027): bit 7 -> 0x1, bit 28 -> 0x102, bit 17 -> 0x40, bit 16 -> 0x80,
    bit 3 -> 0x4, bit 31 -> 0x8 set else 0x8 cleared, bit 26 -> 0x20C, bit 29 -> 0x800, bit 2 -> 0x2000. The tile's
    flags16 bits (bit 0 -> 0x4, bit 2 -> 0x800) come last; the model leaves them to entry_flags (the tile is an input)."""
    if cell & 0x80:
        flags |= 1
    if cell & 0x10000000:
        flags |= 0x102
    if cell & 0x20000:
        flags |= 0x40
    if cell & 0x10000:
        flags |= 0x80
    if cell & 8:
        flags |= 4
    if cell & 0x80000000:
        flags |= 8
    else:
        flags &= ~8
    if cell & 0x4000000:
        flags |= 0x20C
    if cell & 0x20000000:
        flags |= 0x800
    if cell & 4:
        flags |= 0x2000
    return flags & MASK


def setflags(flags, cell, o):
    """sub_0066DB20_RoomTileSetFlags (walls and the bit-2 merge): ((cell >> 18) & 3) + 1 << 14 unless o is 13; 0x4 for
    o 14, 0x2 for o 8..11; then the cell bits of cellflags (the tile's flags16 bits are added by entry_flags)."""
    if o != 13:
        flags |= (((cell >> 18) & 3) + 1) << 14
    if o == 14:
        flags |= 4
    elif o in (8, 9, 10, 11):
        flags |= 2
    return cellflags(flags, cell)


def entry_flags(e, w6):
    """An entry's flags with its tile's flags16 bits (TILE_GetFlags16 = tile +0x06: bit 0 -> 0x4, bit 2 -> 0x800)."""
    f = e.flags
    if e.tbits:
        if w6 & 1:
            f |= 4
        if w6 & 4:
            f |= 0x800
    return f


class Room:
    def __init__(self, d, data):
        self.ptr = d["room"]
        self.r04 = d["r04"]
        self.type = d["type"]
        self.x, self.y, self.w, self.h = d["rect"]
        self.level = d["level"]
        self.ltype = d["ltype"]
        self.dt1 = d["dt1"]
        self.nb = d["nb"]
        self.warpids = d["warpids"]
        self.warps = [dict(w) for w in d["warps"]]       # rec index, mutable (0x0066E160)
        self.preset = d.get("preset")
        self.per, self.cache = data.key_table(self.dt1)
        self.seed = (self.r04, INIT_HIGH)
        self.nodes = None        # RoomTile node list: [[kind, [Entry...]]], head first; None = no RoomTile
        self.built = False
        self.draws = 0
        self.k = None
        self.o89 = []
        self.sub_grids = None
        self.lsub_passes = []
        self.mask = d["mask"]
        self.f28 = d["f28"]
        self.arr = {"W": [], "F": [], "S": []}     # the RoomTile entry arrays in creation (index) order

    def lookup(self, o, main, sub):
        key = (o, main, sub)
        if key not in self.cache:
            n = s = 0
            for keys in self.per:
                for r in keys.get(key, ()):
                    if n < 40:
                        n += 1
                        s = (s + r) & MASK
            self.cache[key] = (n, s)
        return self.cache[key]


class Model:
    def __init__(self, data, verbose=False):
        self.data = data
        self.rooms = {}
        self.verbose = verbose
        self.fail = 0
        self.checks = 0
        self.report = []
        self.cov = {}
        self.tl = {}               # tile pointer -> u16 +0x06 (TL lines of tools/gdb/collision.py)

    def cb_entries(self, path, d, rooms):
        """Plan 0027: at each activation dump (CB, tools/gdb/collision.py) compare every near room's wall, floor and
        shadow arrays with the model's (position, orientation, flags), index by index. The flags are the model's
        (setflags / cellflags from the cell, Orient89Unit's 0x20, the warp 0x8s) plus the tile's flags16 bits from the
        logged tile record (the rarity pick is the tile-choice input of drlg/room-tiles). Entries past the model's are
        AnimTilesBuild's frames (sub_0066D440, animated tiles of an Animate preset): each is checked against the flags
        formula of its kind on the cell of its layer, | 0x8. In the near rooms other than the one activating, bits
        0x20000 and 0x40000 may have been added after their own activation (never present at a room's own dump; their
        writer is not in the build code) and are counted, not compared. On an animated tile (flags16 0x100) the 0x8 bit
        is the animation's frame visibility, run-time state, and is not compared either."""
        import base64
        import zlib
        z = json.loads(zlib.decompress(base64.b64decode(d["z"])))
        for n, dr, _trect, W, F, S in z["near"]:
            R = rooms.get(dr)
            if R is None or R.nodes is None or not R.built:
                self.hit("entry flags: near room not modelled (no roomk lines for it)")
                continue
            own = n == d["room"]
            for kind, got in (("W", W), ("F", F), ("S", S)):
                mine = R.arr[kind]
                name = {"W": "wall", "F": "floor", "S": "shadow"}[kind]
                ok, bad = len(got) >= len(mine), None
                for i, g in enumerate(got):
                    x, y, fl, tp, o = g
                    w6 = self.tl.get(tp)
                    if w6 is None:
                        self.hit("entry flags: tile without a TL record (not compared)")
                        continue
                    if i < len(mine):
                        e = mine[i]
                        if (x, y, o) != (e.x, e.y, e.o):
                            ok, bad = False, (i, g, (e.x, e.y, e.o))
                            break
                        want = entry_flags(e, w6)
                        what = "built, rewritten by the bit-2 merge" if e.merged else "built"
                        if not own and e.mby is not None and e.mby in getattr(self, "h5_ever", ()):
                            self.hit("entry flags: neighbour entry merged by a room since released, compared (H5c)")
                    else:
                        want = self.anim_frame_flags(R, kind, x, y, o, w6)
                        what = "AnimTilesBuild frame"
                        if want is None:
                            ok, bad = False, (i, g, "no animated original at (%d, %d, o %d) or tile not animated" % (x, y, o))
                            break
                    if w6 & 0x100 and (fl ^ want) & 8:
                        # an animated tile's 0x8 is the frame shown at the moment (the animation of AnimTilesBuild's
                        # frame list hides all frames but one); run-time state, not compared
                        self.hit("entry flags: animated tile, 0x8 differs (the frame shown; not compared)")
                        fl = (fl & ~8) | (want & 8)
                    extra = fl & ~want
                    if not own and extra and not extra & ~0x60000 and not want & ~fl:
                        self.hit("entry flags: bits 0x%x added after the room's activation (near room, not compared)" % extra)
                        fl = want
                    if fl != want:
                        ok, bad = False, (i, g[:3] + [o], "%#x" % want, what)
                        break
                    self.hit("entry flags compared: %s %s (%s)" % (what, name, "o %d" % o if kind == "W" else "kind"))
                    for bit, nm in ((0x2, "0x2"), (0x40, "0x40"), (0x80, "0x80"), (0x20, "0x20"), (0x100, "0x100 (cell bit 28)"),
                                    (0x200, "0x200 (cell bit 26)"), (0x800, "0x800"), (0x2000, "0x2000 (cell bit 2)"), (0x4, "0x4"),
                                    (0x8, "0x8")):
                        if want & bit:
                            self.hit("entry flags compared with bit %s set (%s)" % (nm, name))
                self.check(ok, "%s CB room %08x: DRLG room %08x %s entries: %d logged, %d model, first difference %s"
                           % (path, d["room"], dr, kind, len(got), len(mine), bad))
            self.hit("entry flags: near rooms compared at an activation dump (%s)" % ("own" if own else "neighbour"))

    def anim_frame_flags(self, R, kind, x, y, o, w6):
        """sub_0066D440_AnimTilesBuild: a frame entry of an animated original at the same (x, y, o): the cell is read
        from the original's layer grid ((flags >> 14) & 7) - 1 of the kind (walls: wall grids, floors: floor grids,
        shadows: index -1 below the shadow grid, i.e. floor grid 1), then the kind's adder (RoomTileAdd, RoomFloorAdd,
        RoomShadowAdd) and | 0x8 on the returned entry (0x0066D6B0)."""
        if not w6 & 0x100:
            return None
        orig = next((e for e in R.arr[kind] if (e.x, e.y, e.o) == (x, y, o)), None)
        g = getattr(R, "tgrids", None)
        if orig is None or g is None:
            return None
        layer = ((orig.flags >> 14) & 7) - 1
        if kind == "W":
            grids = g["wall"] if R.type == 2 else [g["wall"]]
        elif kind == "F":
            grids = g["floor"] if R.type == 2 else [g["floor"]]
        else:
            grids, layer = (g["floor"] if R.type == 2 else [g["floor"]]), 1
        if not 0 <= layer < len(grids):
            return None
        cell = Grid.from_log(grids[layer]).get(x, y)
        self.hit("AnimTilesBuild frames checked (%s)" % {"W": "wall", "F": "floor", "S": "shadow"}[kind])
        if kind == "W":
            f = setflags(0, cell, o)
        elif kind == "F":
            f = cellflags((((cell >> 18) & 3) + 1) << 14, cell)
        else:
            f = cellflags(0, cell)
        e = Entry(o, x, y, f | (8 if o != 4 else 0), 0, 0)
        return entry_flags(e, w6)

    def hit(self, what, n=1):
        self.cov[what] = self.cov.get(what, 0) + n

    # -- RNG on a room
    def stepr(self, R):
        R.seed = step(*R.seed)
        R.draws += 1

    def rrange(self, R, n):
        if n & 0x80000000 or n == 0:
            return 0
        self.stepr(R)
        lo = R.seed[0]
        return lo & (n - 1) if n & (n - 1) == 0 else lo % n

    def pick(self, R, o, cell):
        """DRLG_PickTileByRarity on room R: returns (main, sub) of the chosen key."""
        main = (cell >> 20) & 0x3F
        sub = (cell >> 8) & 0xFF
        n, s = R.lookup(o, main, sub)
        if n == 0:
            n2, _ = R.lookup(10, 0, 0)
            if n2 == 0:
                raise ModelError("room %08x: no tile for (%d,%d,%d) nor (10,0,0) (game: fatal)" % (R.ptr, o, main, sub))
            self.hit("pick: (10,0,0) fallback")
            return (0, 0)
        if s & 0x80000000 == 0 and s > 0:
            self.stepr(R)
            self.hit("pick: draw")
        else:
            self.hit("pick: candidates, rarity sum 0")
        return (main, sub)

    def oracle(self, R, tile, x=None, y=None, cell=None):
        """sub_0066D9E0_Orient89Unit: consume the room's next logged O89 (+ O89D) line. Plan 0027: with an entry, the
        model also makes the entry flag 0x20 (and predicts whether the one draw happens): the entry is skipped when it
        has 0x20; FUN_0066D960 finds the row of (level, cell main, cell sub, o == 9), else nothing; the unit's subtile
        ((x - room x) * 5 + dx, (y - room y) * 5 + dy) must lie in the room's w * 5 x h * 5; then the unit is created
        (or, unit type 2 with id 91 or 92, RNG_Range(room seed, 3) == 0 skips it) and the entry gets 0x20."""
        if not R.o89 or R.o89[0][0] != "O89":
            raise ModelError("room %08x: model calls Orient89Unit, no O89 line left" % R.ptr)
        _, d = R.o89.pop(0)
        self.hit("Orient89Unit oracle call")
        if d["seed"] != fmt(R.seed):
            raise ModelError("room %08x: O89 seed in %s, model %s" % (R.ptr, d["seed"], fmt(R.seed)))
        draw = None
        if tile is not None and cell is not None:
            draw = False
            if not tile.flags & 0x20:
                i = self.data.o89_lookup(R.level, cell, 1 if tile.o == 9 else 0)
                if i >= 0:
                    _m, _s, _9, uid, utype, dx, dy = self.data.o89_row(i)
                    sx, sy = (x - R.x) * 5 + dx, (y - R.y) * 5 + dy
                    if 0 <= sx < R.w * 5 and 0 <= sy < R.h * 5:
                        tile.flags |= 0x20
                        draw = utype == 2 and 91 <= uid <= 92
                        self.hit("Orient89Unit: entry flag 0x20 set (unit type %d id %d)" % (utype, uid))
                    else:
                        self.hit("Orient89Unit: unit subtile outside the room, no 0x20")
                else:
                    self.hit("Orient89Unit: no row for the level and cell, no 0x20")
            else:
                self.hit("Orient89Unit: entry already 0x20, skipped")
            nxt = bool(R.o89 and R.o89[0][0] == "O89D")
            self.check(nxt == draw, "room %08x: Orient89Unit draw logged %s, model %s" % (R.ptr, nxt, draw))
        if R.o89 and R.o89[0][0] == "O89D":
            _, dd = R.o89.pop(0)
            if dd["seed"] != fmt(R.seed):
                raise ModelError("room %08x: O89D seed %s, model %s" % (R.ptr, dd["seed"], fmt(R.seed)))
            self.stepr(R)
            self.hit("Orient89Unit oracle draw")
            R.o89_val = R.seed[0] % 3                   # plan 0038 H5c: RNG_Range(room seed, 3)
            if R.o89 and R.o89[0][0] == "O89R":
                _, dr = R.o89.pop(0)
                self.check(dr["v"] == R.o89_val, "room %08x: Orient89Unit Range(3) logged %d, model %d"
                           % (R.ptr, dr["v"], R.o89_val))
                self.hit("Orient89Unit Range(3) = %d (model)" % R.o89_val)
                unit = bool(R.o89 and R.o89[0][0] == "O89U")
                if unit:
                    R.o89.pop(0)
                self.check(unit == (R.o89_val != 0), "room %08x: Orient89Unit unit created %s, Range(3) %d"
                           % (R.ptr, unit, R.o89_val))
                self.hit("Orient89Unit draw: unit %s (Range(3) %d)" % ("created" if unit else "skipped", R.o89_val))
        elif R.o89 and R.o89[0][0] == "O89U":
            R.o89.pop(0)
            self.hit("Orient89Unit: unit created without a draw")

    # -- tile entries
    def node(self, R, kind):
        for nd in R.nodes:
            if (nd[0] != 0) == (kind != 0):
                return nd
        nd = [kind, Chain()]
        R.nodes.insert(0, nd)
        return nd

    def add_wall(self, R, x, y, cell, mainsub, o, lst):
        """sub_0066DC50_RoomTileAdd: entry, flags (SetFlags -> Orient89Unit for o 8/9), o-3 partner."""
        e = Entry(o, x - R.x, y - R.y, 0, *mainsub)
        if lst is not None:
            lst.insert(0, e)
        R.arr["W"].append(e)
        if o in (8, 9):
            self.oracle(R, e, x, y, cell)               # SetFlags calls Orient89Unit before it sets any bit
        e.flags = setflags(e.flags, cell, o)
        if o == 3:
            ms = self.pick(R, 4, cell)
            p = Entry(4, x - R.x, y - R.y, 0, *ms)
            if lst is not None:
                lst.insert(0, p)
            R.arr["W"].append(p)
            p.flags = setflags(0, cell, 4)
            # 0x0066DD07..: the caller ORs TileEntryInit's bits again over the partner (idempotent)
            p.flags = cellflags(p.flags | ((((cell >> 18) & 3) + 1) << 14), cell)
        return e

    def add_floor(self, R, x, y, cell, mainsub, lst):
        e = Entry(0, x - R.x, y - R.y, 0, *mainsub)
        e.flags = cellflags((((cell >> 18) & 3) + 1) << 14, cell)       # sub_0066DDE0_TileEntryInit
        if lst is not None:
            lst.insert(0, e)
        R.arr["F"].append(e)
        return e

    def add_shadow(self, R, x, y, cell, mainsub, lst):
        e = Entry(13, x - R.x, y - R.y, 0, *mainsub)
        e.flags = cellflags(0, cell)                                      # sub_0066DF40_RoomShadowAdd: no 0x4000 part
        if lst is not None:
            lst.insert(0, e)
        R.arr["S"].append(e)
        return e

    # -- warps
    def dirchar(self, o):
        return "r" if o == 11 else "l"

    def warp_unit_ok(self, R, cell, o, x, y):
        """sub_0066E1C0_WarpUnitAdd: the LvlWarp row must exist (fatal otherwise); unit iff not on the
        right or bottom edge column/row of the room."""
        m = (cell >> 20) & 0x3F
        self.data.warp_lookup(R.warpids[m], self.dirchar(o))
        return (x - R.x) != R.w and (y - R.y) != R.h

    def warp_node(self, R, cell):
        wid = R.warpids[(cell >> 20) & 0x3F]
        for w in R.warps:
            if w["rec"] >= 0 and self.data.lvlwarp[w["rec"]].id == wid:
                return w
        return None

    def warp_switch(self, w, o):
        """0x0066E160: re-look the node's LvlWarp row up when its direction does not fit o."""
        rec = self.data.lvlwarp[w["rec"]]
        dc = self.dirchar(o)
        if rec.dir != "b" and rec.dir != dc:
            w["rec"] = self.data.warp_lookup(rec.id, dc)

    def warp_tile_add(self, R, e, cell, o):
        """sub_0066E260_WarpTileAdd (visible orientation 10/11)."""
        w = self.warp_node(R, cell)
        if w is None:
            raise ModelError("room %08x: no warp node for cell %08x (game: fatal 0x2B1)" % (R.ptr, cell))
        s8 = (cell >> 8) & 0xFF
        if s8 in (0, 4) and not self.warp_unit_ok(R, cell, o, e.x + R.x, e.y + R.y):
            return
        self.warp_switch(w, o)
        if e.next is not None:
            self.hit("warp tile re-linked out of a node chain that continued (older entries cut off)")
        e.next = w.get("head")                 # 0x0066E2F2: entry +0x20 = warp node +0x0C; node +0x0C = entry
        w["head"] = e
        rec = self.data.lvlwarp[w["rec"]]
        self.hit("warp tile (visible)")
        if rec.litversion != 0:
            c2 = (cell | (rec.tiles << 8)) & MASK
            ms = self.pick(R, o, c2)
            lit = self.add_wall(R, e.x + R.x, e.y + R.y, c2, ms, o, None)
            lit.flags |= 8                         # 0x0066E345: the lit version's entry gets 0x8

    def hidden_warp(self, R, cell, o, x, y):
        """sub_0066E1C0 + sub_0066E360_HiddenWarpTilesAdd (bit-31 orientation 10/11)."""
        R.hwf_model = getattr(R, "hwf_model", 0) + 1     # plan 0038 H5c: 0x0066E37E ORs 0x800000 at the entry
        self.warp_unit_ok(R, cell, o, x, y)
        w = self.warp_node(R, cell)
        if w is None:
            return
        self.warp_switch(w, o)
        self.hit("warp tiles (hidden)")
        if self.data.lvlwarp[w["rec"]].litversion != 0:
            s8 = (cell >> 8) & 0xFF
            for i in range(4):
                c = (((s8 << 12) | i | 4) << 8) & MASK
                ms = self.pick(R, 0, c)
                # four floor entries at (x - 1, y - 1) + g_HiddenWarpOfs[i] (0x006EF554: (0,0) (1,0) (0,1) (1,1)),
                # TileEntryInit's flags, then | 8 (0x0066E45F)
                dx, dy = ((0, 0), (1, 0), (0, 1), (1, 1))[i]
                e = Entry(0, x - 1 + dx - R.x, y - 1 + dy - R.y, 0, *ms)
                e.flags = cellflags((((c >> 18) & 3) + 1) << 14, c) | 8
                R.arr["F"].append(e)
                e.next = w.get("head14")             # linked into warp node +0x14
                w["head14"] = e
                self.hit("hidden warp floor entries (0x8)")
            # then every floor entry of the room whose tile main index is s8 and sub index < 4 is re-linked into the
            # warp node's +0x0C list, in array order (0x0066E484..0x0066E4A5)
            for f in R.arr["F"]:
                if f.main == s8 and f.sub < 4:
                    f.next = w.get("head")
                    w["head"] = f

    # -- bit-2 path
    def scan(self, R, kind, x, y, cell):
        """sub_0066E580_NeighbourTileScan / sub_0066E4C0_NeighbourTileFind."""
        for q in R.nb:
            if q == R.ptr:
                continue
            N = self.rooms.get(q)
            if N is None or N.nodes is None:
                continue
            if not (N.x <= x <= N.x + N.w and N.y <= y <= N.y + N.h):
                continue
            for nd in N.nodes:
                if (nd[0] != 0) != (kind != 0):
                    continue
                for e in nd[1]:
                    if e.x + N.x == x and e.y + N.y == y and e.o != 4 and (e.o == 13 or not cell & 0x8000000):
                        if e.flags & 0x1C000 == 0 or ((e.flags >> 14) & 7) - 1 == (cell >> 18) & 3:
                            return N, e
        return None, None

    def bit2(self, R, x, y, o, cell):
        N, e = self.scan(R, o == 0, x, y, cell)
        if e is not None:
            self.hit("bit-2 merge")
            self.merge(R, N, e, o, cell, x, y)
        else:
            self.hit("bit-2 new")
            self.new(R, o, cell, x, y)

    def new(self, R, o, cell, x, y):
        """sub_0066E620_Bit2TileNew."""
        if o in (10, 11) and not (R.x <= x < R.x + R.w and R.y <= y < R.y + R.h):
            return
        nd = self.node(R, o == 0)
        ms = self.pick(R, o, cell)
        if o == 0:
            self.add_floor(R, x, y, cell, ms, nd[1])
        elif o == 13:
            self.add_shadow(R, x, y, cell, ms, nd[1])
        else:
            self.add_wall(R, x, y, cell, ms, o, nd[1])
            if o in (10, 11):
                self.warp_tile_add(R, nd[1].head, cell, o)

    def merge(self, R, N, E, o, cell, x, y):
        """sub_0066E740_Bit2TileMerge; E is the neighbour N's entry."""
        E.mby = R.ptr
        if E.next is not None and E.o == 3:
            E.next.mby = R.ptr
        T = self.data.remap_o[o]
        if E.flags & 1:
            self.hit("bit-2 merge: entry flag 0x1")
            if E.o in (8, 9):
                self.oracle(R, E, x, y, cell)            # SetFlags calls Orient89Unit before it sets any bit
                E.flags = setflags(E.flags, cell, E.o)
                E.merged += 1
            return
        if not cell & 0x80:
            remap = True
            if o in (8, 9):
                if x == R.x or y == R.y:
                    remap = False
            elif E.o in (8, 9):
                if x == N.x or y == N.y:
                    return
            if remap:
                if T >= 0 and E.o <= 7:
                    self.hit("bit-2 merge: remap row %d, old o %d -> %d" % (T, E.o, self.data.remap_t[T * 7 + E.o]))
                    o = self.data.remap_t[T * 7 + E.o]
                elif T != -1:
                    self.hit("bit-2 merge: row %d, no merge" % T)
                    return
                else:
                    self.hit("bit-2 merge: row -1 (o %d kept)" % o)
            else:
                self.hit("bit-2 merge: o 8/9 on the room edge, o kept")
        else:
            self.hit("bit-2 merge: cell bit 7, no remap")
        if E.o == 3:
            if o != 3:
                # 0x0066E8A7: the entry after E in its list (E +0x20) gets 0x8; no draw
                nxt = E.next
                if nxt is not None:
                    nxt.flags |= 8
                    nxt.merged += 1
                    self.hit("bit-2 merge: old orientation 3, the next entry of its list gets 0x8")
                else:
                    self.hit("bit-2 merge: old orientation 3, no next entry in the model's lists")
        elif o == 3:
            self.hit("bit-2 merge to orientation 3")
            E.flags |= 0xC008
            E.merged += 1
            nd = self.node(R, 0)
            ms = self.pick(R, 3, cell)             # 0x0066E87C, this room
            self.add_wall(R, x, y, cell, ms, 3, nd[1])
        blank = E.o == 0 and E.main == 30 and E.sub == 0
        if o != E.o or blank:
            self.hit("bit-2 merge re-pick on the neighbour seed")
            ms = self.pick(N, o, cell)             # 0x0066E8F7: ECX = the NEIGHBOUR room
            E.o = o
            E.main, E.sub = ms
        if E.o in (8, 9):
            self.oracle(R, E, x, y, cell)                # SetFlags calls Orient89Unit before it sets any bit
        E.flags = setflags(E.flags, cell, E.o)
        E.merged += 1

    # -- per cell
    def cell_build(self, R, cell, o, x, y, filler):
        """sub_0066E9B0_RoomCellBuild."""
        m = (cell >> 20) & 0x3F
        s8 = (cell >> 8) & 0xFF
        if o in (10, 11) and m >= 8:
            return
        if o == 0 and m == 30 and s8 in (0, 1):
            cell |= 0x80000000
        hidden = cell & 0x80000000
        if hidden:
            if o in (8, 9):
                if not (111 <= R.level <= 112 or R.level == 117):
                    self.oracle(R, None)
                    return
                self.hit("level exception: hidden orientation 8/9 built in level %d (111, 112, 117)" % R.level)
            elif o in (10, 11):
                self.hidden_warp(R, cell, o, x, y)
                return
        if cell & 4:
            if cell & 2:
                c = cell & ~0x80 if (m == 30 and s8 in (0, 1)) else cell
                self.bit2(R, x, y, 0, c)
                return
            if cell & 1:
                self.bit2(R, x, y, o, cell)
                return
            if cell & 0x8000000 and not hidden:
                self.bit2(R, x, y, 13, cell)
                return
        if cell & 2:
            ms = self.pick(R, 0, cell)
            self.add_floor(R, x, y, cell, ms, None)
        elif filler and R.x <= x < R.x + R.w and R.y <= y < R.y + R.h:
            self.hit("filler floor")
            if R.level == 74:
                self.hit("level exception: filler floor of level 74 (key sub 1, 0x1E00100)")
            c = 0x1E00100 if R.level == 74 else 0x1E00000
            ms = self.pick(R, 0, c)
            self.add_floor(R, x, y, (cell & ~0x80) | 0x80000000, ms, None)
        if cell & 1:
            ms = self.pick(R, o, cell)
            e = self.add_wall(R, x, y, cell, ms, o, None)
            if o in (10, 11) and R.level != 133:
                self.warp_tile_add(R, e, cell, o)
        if cell & 0x8000000:
            ms = self.pick(R, 13, cell)
            self.add_shadow(R, x, y, cell, ms, None)

    def cells_build(self, R, g, og, filler, kx, ky):
        """sub_0066EC10_RoomCellsBuild: rows outer, columns inner; one more row/column unless killed."""
        for yy in range(R.h + (0 if ky else 1)):
            for xx in range(R.w + (0 if kx else 1)):
                o = og.get(xx, yy) if og is not None else 0
                self.cell_build(R, g.get(xx, yy), o, R.x + xx, R.y + yy, filler)

    def tiles_build(self, R, d):
        g = d["grids"]
        R.tgrids = g
        if R.type == 1:
            self.cells_build(R, Grid.from_log(g["wall"]), Grid.from_log(g["orient"]), 0, False, False)
            self.cells_build(R, Grid.from_log(g["floor"]), None, 0, False, False)
        elif R.type == 2:
            P = R.preset
            kx = ky = False
            if P["killedge"]:
                px, py, pw, ph = P["prect"]
                kx = R.x + R.w == px + pw
                ky = R.y + R.h == py + ph
            for i, fg in enumerate(g["floor"]):
                self.cells_build(R, Grid.from_log(fg), None, 1 if (i == 0 and P["fillblanks"]) else 0, kx, ky)
            for wg, og in zip(g["wall"], g["orient"]):
                self.cells_build(R, Grid.from_log(wg), Grid.from_log(og), 0, kx, ky)
            self.cells_build(R, Grid.from_log(g["shadow"]), None, 0, kx, ky)
            # the Def 1/108 extra grid is allocated zeroed (0x0067CBF0) and never written: no work

    # -- LvlSub (type 1 prepare)
    def lsub_pass(self, R, d, grids):
        t, theme, mask = d["stype"], d["theme"], d["smask"]
        if t < 0:
            return
        rec0 = next(i for i, s in enumerate(self.data.lvlsub) if s.type == t)
        if d.get("rec") is not None and d["rec"] != rec0:
            raise ModelError("LvlSub type %d: first record %d, game index table %d" % (t, rec0, d["rec"]))
        m, rec = mask, rec0
        while m:
            if m & 1:
                s = self.data.lvlsub[rec]
                if s.type != t:
                    raise ModelError("LvlSub mask bit past the records of type %d" % t)
                if s.checkall:
                    raise ModelError("LvlSub CheckAll != 0 (ApplyAll) not modelled; no stock record has it")
                self.apply_pick(R, grids, rec, theme)
            m >>= 1
            rec += 1

    def apply_pick(self, R, grids, rec, theme):
        """sub_00670170_LvlSubApplyPick."""
        s = self.data.lvlsub[rec]
        S = self.data.sub_ds1(rec)
        G = S["groups"]
        mx = s.max[theme]
        if not G or mx < 1:
            return
        for _ in range(mx):
            gi = self.rrange(R, len(G))
            gx, gy, gw, gh = G[gi]
            if S["truncated"] and gi == len(G) - 1:
                self.hit("LvlSub truncated group drawn, w,h from memory = %d,%d" % (gw, gh))
            dx, dy = R.w - gw, R.h - gh
            if dx < 1 or dy < 1:
                continue
            tr = s.trials[theme]
            self.hit("LvlSub rec %d (Trials %d)" % (rec, tr))
            if tr == -1:
                n = dx * dy
                lst = [(i % dx, i // dx) for i in range(n)]
                for _ in range(n):
                    a = self.rrange(R, n)
                    b = self.rrange(R, n)
                    lst[a], lst[b] = lst[b], lst[a]
                for lx, ly in lst:
                    if self.fits(R, grids, S, (gx, gy, gw, gh), lx + 1, ly + 1):
                        self.stamp(R, grids, S, (gx, gy, gw, gh), lx + 1, ly + 1)
                        self.hit("LvlSub stamp")
                        break
            else:
                for _ in range(max(tr, 0)):
                    x = self.rrange(R, dx) + 1
                    y = self.rrange(R, dy) + 1
                    if self.fits(R, grids, S, (gx, gy, gw, gh), x, y):
                        self.stamp(R, grids, S, (gx, gy, gw, gh), x, y)
                        self.hit("LvlSub stamp")
                        break

    def fits(self, R, grids, S, g, x, y):
        """sub_0066FCF0_LvlSubFits."""
        gx, gy, gw, gh = g
        cols = S["cols"]
        for yy in range(gh):
            for xx in range(gw):
                si = (gy + yy) * cols + gx + xx
                sf = S["floor"][si] if S["floor"] is not None else 0
                if not sf & 2:
                    if not S["walls"] or not S["walls"][0][si] & 1:
                        continue
                rc = grids["floor"].get(x + xx, y + yy)
                if rc & 0x3F0FF00 or not rc & 2:
                    return False
                if grids["wall"].get(x + xx, y + yy) & 1:
                    return False
        return True

    def stamp(self, R, grids, S, g, x, y, xoff=0):
        """sub_0066FAD0_LvlSubStamp (preset units: no draw)."""
        gx, gy, gw, gh = g
        cols = S["cols"]
        for yy in range(gh):
            for xx in range(gw):
                si = (gy + yy) * cols + gx + xoff + xx
                rx, ry = x + xx, y + yy
                f = S["floor"][si] if S["nfloor"] else 0
                if f & 2:
                    grids["floor"].set(rx, ry, f | 0x80)
                if S["nwall"]:
                    w = S["walls"][0][si]
                    if w & 1:
                        grids["wall"].set(rx, ry, w)
                    o = S["orients"][0][si]
                    if o != 0:
                        grids["orient"].set(rx, ry, o)
                sh = S["shadow"][si]
                if sh & 0x8000000:
                    ms = self.pick(R, 13, sh)
                    self.add_shadow(R, R.x + xx + x, R.y + yy + y, sh, ms, None)

    def prepare_tail(self, R, grids):
        """0x0067D446..0x0067D500: theme fill on the floor grid, then bit 2 on the border of both grids."""
        v = {16: 0x100, 21: 0x120000, 22: 0x100000, 27: 0xA00000, 28: 0x1600000}.get(R.ltype, 0)
        if R.ltype == 31:
            v = 0x600000 if R.level == 117 else 0
        fl = grids["floor"]
        for y in range(fl.h):
            for x in range(fl.w):
                c = fl.get(x, y)
                if c & 0x3F0FF80 == 0:
                    fl.set(x, y, c | v)
        for g in (grids["wall"], grids["floor"]):
            for x in range(g.w):
                g.set(x, 0, g.get(x, 0) | 4)
                g.set(x, g.h - 1, g.get(x, g.h - 1) | 4)
            for y in range(1, g.h - 1):
                g.set(0, y, g.get(0, y) | 4)
                g.set(g.w - 1, y, g.get(g.w - 1, y) | 4)

    # -- F1/F2: DT1 list, room mask, type-2 grids
    def check_dt1(self, path, R, d):
        """DRLG_LevelDt1ListBuild: the logged list is LvlTypes File i+1 per bit of +0x50, then the fixed
        files; a type-2 room's +0x50 is its LvlPrest Dt1Mask (sub_00667ED0_PresetRoomsCreate)."""
        want = self.data.dt1_list(R.ltype, R.mask)
        self.check(d["dt1"] == want, "%s %08x DT1 list %s, model %s" % (path, R.ptr, d["dt1"], want))
        self.hit("DT1 list checked (type %d)" % R.type)
        if R.type == 2:
            pm = self.data.lvlprest[R.preset["lvlprest"]].dt1mask
            self.check(R.mask == pm, "%s %08x +0x50 %#x, LvlPrest[%d].Dt1Mask %#x"
                       % (path, R.ptr, R.mask, R.preset["lvlprest"], pm))
            self.hit("type-2 mask = LvlPrest.Dt1Mask checked" + (" (DrlgType %d level)" % self.data.drlgtype[R.level]))

    def check_outroom_mask(self, path, R):
        """sub_0067D540_OutRoomCreate: +0x50 = the level-type value of sub_006750F0, then
        sub_006706A0_LvlSubRoll ORs the Dt1Mask (+0x48) of every SubType record it picks; the picks are the
        mask of the SubType pass (the last LvlSub pass of the prepare)."""
        if not R.lsub_passes:
            self.check(False, "%s %08x type-1 room without an LSUB line" % (path, R.ptr))
            return
        last = R.lsub_passes[-1]
        want = OUTROOM_MASK.get(R.ltype, 0)
        if last["stype"] >= 0:
            rec0 = next(i for i, s in enumerate(self.data.lvlsub) if s.type == last["stype"])
            m, i = last["smask"], rec0
            while m:
                if m & 1:
                    want |= self.data.lvlsub_dt1mask[i]
                m >>= 1
                i += 1
        self.check(R.mask == want, "%s %08x type-1 +0x50 %#x, model %#x" % (path, R.ptr, R.mask, want))
        self.hit("type-1 mask = level-type value | picked SubType Dt1Masks checked")
        self.hit("type-1 mask checked, level type %d (level-type value %#x)" % (R.ltype, OUTROOM_MASK.get(R.ltype, 0)))

    def check_preset_grids(self, path, R, d):
        """sub_006667D0_PresetRoomGridPrepare against the logged TINIT grids. The file index is not
        logged by drlg-roomk.gdb: the room's DS1 is the LvlPrest File whose modelled views equal the
        logged grids; the files found for the rooms of one preset instance must agree."""
        P = R.preset
        rec = self.data.lvlprest[P["lvlprest"]]
        prect = P["prect"]
        cands = [f for f in rec.files if f not in ("", "0")]
        rect = (R.x, R.y, R.w, R.h)
        hit_p, hit_f = [], []
        for c in cands:
            pb = self.data.preset_pristine(c)
            if pb["size"] != (prect[2], prect[3]):
                continue
            try:
                if grids_equal(preset_prepare(buf_copy(self.data.preset_buf(c)), rect, prect), d["grids"]):
                    hit_p.append(c)
                if grids_equal(preset_prepare(buf_copy(pb), rect, prect), d["grids"]):
                    hit_f.append(c)
            except ModelError as e:
                self.check(False, "%s %08x %s" % (path, R.ptr, e))
        self.check(len(hit_p) >= 1, "%s %08x type-2 grids: no LvlPrest[%d] file reproduces them (fresh: %s)"
                   % (path, R.ptr, P["lvlprest"], hit_f))
        if hit_p != hit_f:
            self.hit("type-2 grids: persistent and fresh DS1 differ")
            self.check(False, "%s %08x type-2 grids: persistent DS1 matches %s, fresh %s" % (path, R.ptr, hit_p, hit_f))
        key = (R.f28 & 0x40000, R.level, tuple(prect), P["lvlprest"])
        prev = self.instances.get(key)
        self.instances[key] = set(hit_p) if prev is None else prev & set(hit_p)
        self.check(bool(self.instances[key]), "%s %08x preset instance %r: no file common to its rooms" % (path, R.ptr, key))
        if len(hit_p) == 1:
            self.hit("type-2 grids reproduced, file unique (%d candidate%s)" % (len(cands), "" if len(cands) == 1 else "s"))
        elif hit_p:
            self.hit("type-2 grids reproduced, %d files fit" % len(hit_p))
        for c in hit_p:     # the game's write into the cached buffer
            preset_prepare(self.data.preset_buf(c), rect, prect)
        b = self.data.preset_pristine(hit_p[0]) if hit_p else None
        if b is not None:
            self.check((P["nwall"], P["nfloor"]) == (len(b["walls"]), len(b["floors"])),
                       "%s %08x DS1 layer counts %d/%d, file %d/%d" % (path, R.ptr, P["nwall"], P["nfloor"],
                                                                       len(b["walls"]), len(b["floors"])))

    # -- checks
    def check(self, ok, what):
        self.checks += 1
        if not ok:
            self.fail += 1
            print("MISMATCH " + what)
        elif self.verbose:
            print("ok " + what)


def fmt(seed):
    return "%08x:%08x" % seed


# Plan 0038 batch H5c lines (tools/gdb/drlg-roomk.py, drlg-gen.py, collision.py): release, unload, restore, the
# activation flags and RoomTile counts, the TINIT exit, the hidden-warp flag, the Orient89Unit result, LevelInit's and
# PresetLevelBuild's callers and callbacks, the warp exit. Checked in run_log (H5c section); logs without them are
# unchanged.
H5C_TAGS = ("RA0", "TINITX", "HWF", "RREL", "RTR0", "RTR1", "LUL0", "LUL1", "LRS0", "LRS1", "O89R", "O89U", "LI0",
            "PLB", "PLBT", "PLBA", "PLBX", "WXP", "WXPX", "PLR", "RNE", "WPL", "WPLW", "WPLX")
# sub_0066C370_RoomNeighboursEnsure's call sites (return addresses): the room activation paths
RNE_CALLERS = {0x0061B1A7: "RoomActivateA", 0x0061B3AC: "sub_0061B390", 0x0061B77D: "RoomActivateB"}
# sub_006424A0_LevelInit's call sites (return addresses) -> caller
LI_CALLERS = {0x00642CE9: "RoomFromCoords", 0x00642F61: "ActCreate", 0x006681C0: "PresetLevelBuild",
              0x0066B05C: "sub_0066B030 (1)", 0x0066B075: "sub_0066B030 (2)", 0x0066B2F2: "sub_0066B2B0",
              0x0066C29E: "sub_0066C220"}
TOWN_CALLBACK_LEVELS = (40, 103, 109)


def parse_log(path):
    """The model's events of one log. A log that holds a second game (a second `WNDARM` line with `levels`, which
    tools/gdb/mon-spawn.py writes once per game at the regions init 0x005479C0) is refused: the DT1 lists the game
    keeps from the first game would not match the model's fresh ones (plan 0038 H4b review follow-up (b), plan
    0049). Split such a log at the second game's first line. Logs without that tag are not checked for it."""
    ev = []
    games = []
    for ln, line in enumerate(open(path, errors="replace"), 1):
        tag, _, rest = line.partition(" ")
        if tag == "WNDARM" and '"levels"' in rest:
            games.append(ln)
            if len(games) > 1:
                raise SystemExit("%s: a second game starts at line %d (WNDARM at lines %s); the DRLG models check "
                                 "one game per log: split the log at line %d" % (path, ln, ", ".join(map(str, games)),
                                                                                 ln))
            continue
        if tag in ("RRESEED", "LSUB", "LSUBX", "TINIT", "O89", "O89D", "RACT", "AROOM", "RTFREE", "TL", "CB") \
                or tag in H5C_TAGS:
            d = json.loads(rest)
            d["_ln"] = ln              # the file line (GenModel.prep_pred is keyed by it)
            ev.append((tag, d))
        elif tag == "LOGERR":
            ev.append((tag, {"msg": rest.strip()}))
    return ev


def h5c_ract(model, path, R, d, h5):
    """Plan 0038 H5c at a room's RACT, after the model built it: the activation flags (rng/seeds 6c), the RoomTile
    counts T[+0x18] / T[+0x20] (room-tiles step note 12), the TINIT-exit flags and the hidden-warp 0x800000, and k of
    a released room built again."""
    if "fl" in d:
        f28, r60 = d["f28"], d["r60"]
        want = 4 if f28 & 0x40000 else (1 if r60 & 1 else 0)
        model.check(d["fl"] == want, "%s %08x activation flags %d, model %d (+0x28 %#x, +0x60 %#x)"
                    % (path, R.ptr, d["fl"], want, f28, r60))
        model.hit("activation flags = %d (from %s)" % (want, "+0x28 & 0x40000" if f28 & 0x40000 else
                                                         ("+0x60 bit 0" if r60 & 1 else "neither")))
        nw, nf = d["nw"], d["nf"]
        mw, mf = len(R.arr["W"]), len(R.arr["F"])
        model.check(nw >= mw and nf >= mf and nw + nf > 0, "%s %08x RoomTile counts %d/%d, model %d/%d"
                    % (path, R.ptr, nw, nf, mw, mf))
        model.hit("RoomTile counts T[+0x18]/T[+0x20] %s the model's wall/floor entries"
                  % ("equal to" if (nw, nf) == (mw, mf) else "above (animation frames)"))
        R.nwnf = (nw, nf)
    tx = getattr(R, "tinitx", None)
    if tx is not None:
        model.check(tx["f28"] & 0x100000 != 0, "%s %08x TINIT exit without 0x100000" % (path, R.ptr))
        hm, hl = getattr(R, "hwf_model", 0), getattr(R, "hwf_log", 0)
        model.check(hm == hl, "%s %08x HiddenWarpTilesAdd calls logged %d, model %d" % (path, R.ptr, hl, hm))
        if hm:
            model.check(tx["f28"] & 0x800000 != 0, "%s %08x hidden warp room without 0x800000 at the TINIT exit"
                        % (path, R.ptr))
            model.hit("hidden-warp room: 0x800000 set by HiddenWarpTilesAdd (%s before the build)"
                      % ("already" if R.f28 & 0x800000 else "not"))
        model.hit("TINIT exit flags checked (0x100000 set)")
    key = (R.ptr, R.r04)
    if getattr(R, "reactivated", False):
        k0 = h5["k_first"].get(key)
        model.hit("re-activated room: k %s the first build's" % ("equal to" if k0 == R.k else
                                                                 ("differs from" if k0 is not None else "(first k not seen)")))
    else:
        h5["k_first"][key] = R.k


def plb_check(model, path, d0, d):
    """sub_00668100_PresetLevelBuild's tail: town levels 40, 103, 109 call act[+0x488] once when it and AutoMap are
    set; other levels call act[+0x454] per room when it and AutoMap are set; the server act's callbacks are null; the
    level seed does not change (d: the exit line, None when the log has none for this build)."""
    town = d0["id"] in TOWN_CALLBACK_LEVELS
    if town:
        want = (1 if d0["cb488"] and d0["automap"] else 0, 0)
    else:
        want = (0, "n" if d0["cb454"] and d0["automap"] else 0)
    got = (d0["_t"], "n" if d0["_a"] else 0)
    ok = got == want and (d is None or d["seed"] == d0["seed"])
    client = d0.get("dclient")
    if client == 0:
        ok = ok and d0["cb454"] == 0 and d0["cb488"] == 0
    model.check(ok, "%s PresetLevelBuild level %d client %s cb454 %#x cb488 %#x AutoMap %d: calls %s, model %s, "
                "seed %s -> %s" % (path, d0["id"], client, d0["cb454"], d0["cb488"], d0["automap"], got,
                                   want, d0["seed"], d and d["seed"]))
    model.hit("PresetLevelBuild callbacks: %s, %s, AutoMap %d -> %s%s" % (
        "town %d" % d0["id"] if town else "level %d" % d0["id"],
        {0: "server (callbacks null)", 1: "client"}.get(client, "act copy not logged"),
        d0["automap"], "town callback" if got[0] else ("per-room callback x%d" % d0["_a"] if d0["_a"] else "none"),
        "" if d is not None else " (no exit line)"))


def h5c_rne_close(model, path, r, st, at_end=False):
    """At the RRESEED after a RoomNeighboursEnsure: same room, the WarpPairLink calls are the warp bits' slots."""
    calls = st["calls"]
    ok = r == st["room"] and [c["slot"] for c in calls] == st["want"] and all("warp" in c and "ok" in c for c in calls)
    model.check(ok, "%s %08x RoomNeighboursEnsure: slots %s, calls %s, then RRESEED of %08x"
                % (path, st["room"], st["want"], calls, r))
    if not at_end:
        model.hit("RoomNeighboursEnsure, then the room's own re-seed")
    for c in calls:
        model.hit("WarpPairLink at activation: %s" % ("Warp -1, mark only" if c.get("warp") == -1 else
                                                      ("paired" if c.get("ok") else "warp id set, no pair found")))


def h5c_event(model, path, tag, d, rooms, pending, h5):
    """Plan 0038 H5c lines other than RACT's keys (see H5C_TAGS)."""
    r = d.get("room")
    if tag == "RNE":
        # warps F1: one WarpPairLink per warp bit 0x10 << slot of +0x28, in slot order, none in level 133; the callers
        # call it only while +0x2C is 0 (the line is after the neighbour step, which fills +0x2C)
        want = [] if d["lid"] == 133 else [i for i in range(8) if d["f28"] & (0x10 << i)]
        seen = h5.setdefault("reseeded", set())
        model.check(d["ret"] in RNE_CALLERS, "%s %08x RoomNeighboursEnsure ret %08x" % (path, r, d["ret"]))
        # the callers test +0x2C = 0: a room's first activation, or a later one after sub_00643060_LevelUnloadCheck
        # cleared the neighbour lists of the rooms of the levels linked to a level it unloads (0x006431C0)
        model.hit("RoomNeighboursEnsure on a room %s" % ("activated before (+0x2C cleared since)" if r in seen
                                                         else "not activated before"))
        st = {"room": r, "want": want, "calls": [], "ret": d["ret"]}
        h5.setdefault("rne", {})[r] = st
        model.hit("RoomNeighboursEnsure from %s" % RNE_CALLERS.get(d["ret"], "?"))
    elif tag in ("WPL", "WPLW", "WPLX"):
        # WarpPairLink can build the destination level (LevelInit), whose client preset build activates rooms, so a
        # whole RoomNeighboursEnsure can run inside a WarpPairLink call: attach each line to the latest open call
        open_ = list(h5.get("rne", {}).values())
        if tag == "WPL":
            st = next((x for x in reversed(open_) if x["room"] == r), None)
            model.check(st is not None, "%s WarpPairLink on room %08x outside its RoomNeighboursEnsure" % (path, r))
            if st is not None:
                st["calls"].append({"slot": d["slot"]})
                h5.setdefault("wpl_stack", []).append(st["calls"][-1])
        else:
            stk = h5.get("wpl_stack", [])
            if not stk:
                model.check(False, "%s %s without a WarpPairLink call" % (path, tag))
                return
            stk[-1].update(d)
            if tag == "WPLX":
                stk.pop()
    elif tag == "RA0":
        model.hit("RA0: no wall entry (%s floors)" % ("no" if d["nf"] == 0 else "with"))
        if d["nf"] == 0 and r in pending:
            R = rooms[r]
            td, _ = pending.pop(r)
            if R.nodes is None:
                R.nodes = []
                R.arr = {"W": [], "F": [], "S": []}
            model.tiles_build(R, td)
            R.built = True
            R.k = R.draws
            model.check(not R.arr["W"] and not R.arr["F"], "%s %08x RA0 with no entries, model has %d/%d"
                        % (path, r, len(R.arr["W"]), len(R.arr["F"])))
            model.check(d["seed"] == fmt(R.seed), "%s %08x RA0 seed %s model %s" % (path, r, d["seed"], fmt(R.seed)))
            model.hit("room with no wall and no floor entry: no activation draw, no active room")
    elif tag == "TINITX":
        if r in rooms:
            rooms[r].tinitx = d
    elif tag == "HWF":
        if r in rooms:
            rooms[r].hwf_log = getattr(rooms[r], "hwf_log", 0) + 1
    elif tag == "RREL":
        h5["rrel"][r] = d
        model.hit("release wrapper 0x0066B4C0 (%s)" % ("built room" if d["f28"] & 0x100000 else "unbuilt room"))
    elif tag == "RTR0":
        # RoomTilesRelease nests: with EDX 0 it frees the active room (0x0061A910), whose release wrapper calls
        # RoomTilesRelease again on the same room (EDX = act flag == 0); a stack per room pairs the lines
        h5["rtr"].setdefault(r, []).append(d)
        h5["rtfree"].discard(r)
        w = h5["rrel"].pop(r, None)
        if w is not None:
            model.check(w["f28"] & 0x100000 != 0 and d["edx"] == (1 if w["edx"] == 0 else 0)
                        and d["r60"] == w["arg"] & 1,
                        "%s %08x release wrapper: f28 %#x edx %d arg %d -> RTR edx %d +0x60 %d"
                        % (path, r, w["f28"], w["edx"], w["arg"], d["edx"], d["r60"]))
            model.hit("RoomTilesRelease from the wrapper: +0x60 = %d, EDX %d" % (d["r60"], d["edx"]))
        else:
            model.hit("RoomTilesRelease from return address %08x (no wrapper line)" % d["ret"])
    elif tag == "RTR1":
        st = h5["rtr"].get(r)
        d0 = st.pop() if st else None
        if d0 is None:
            model.check(False, "%s %08x RTR1 without RTR0" % (path, r))
            return
        inner = d0.get("_inner")
        if st:
            st[-1]["_inner"] = d               # this call ran inside the outer one on the same room
        if inner is not None:
            model.check(d["f28"] == inner["f28"] and d["ctr"] == inner["ctr"] and d["rt"] == inner["rt"]
                        and d["r30"] == 0 and d.get("r64", 0) == 0, "%s %08x outer RoomTilesRelease after the nested one changed the room: %s -> %s"
                        % (path, r, inner, d))
            model.hit("RoomTilesRelease: outer call after the nested release (active room freed first), nothing more")
            return
        built = d0["f28"] & 0x100000
        same = d["r04"] == d0["r04"] and d["n2c"] == d0["n2c"] and d["r30"] == 0
        if "r64" in d:
            # sub_0066C6E0_LogicRecordFree runs on every call, before the 0x100000 test (drlg/0005 § S4a): +0x64 = 0
            same = same and d["r64"] == 0
            model.hit("RoomTilesRelease: logic record +0x64 %s" % ("freed (was set)" if d0["r64"] else "already 0"))
        if built:
            want = (d0["f28"] ^ 0x100000) | (0x200000 if d0["edx"] else 0)
            ok = (d["f28"] == want and d["ctr"] == d0["ctr"] + 1 and d["rt"] == 0 and r in h5["rtfree"]
                  and all(w == [0, 0] for w in d["warps"]) and same)
            model.check(ok, "%s %08x RoomTilesRelease: %s -> %s" % (path, r, d0, d))
            model.hit("RoomTilesRelease of a built room: 0x100000 cleared, counter +1, RoomTile freed, warp nodes "
                      "zeroed%s" % (", 0x200000 set (EDX)" if d0["edx"] else ""))
            if d0["warps"]:
                model.hit("RoomTilesRelease: room with warp nodes, (+0x0C, +0x14) zeroed")
            if d0["f28"] & 0x3000000:
                model.hit("RoomTilesRelease: 0x1000000 / 0x2000000 kept")
            h5["released"].add(r)
            h5["ever"].add(r)
            R = rooms.get(r)
            if R is not None:
                R.f28_rel = d["f28"]
                R.nodes = None
                R.built = False
        else:
            model.check(d["f28"] == d0["f28"] and d["ctr"] == d0["ctr"] and d["rt"] == d0["rt"] and same,
                        "%s %08x RoomTilesRelease of an unbuilt room changed it: %s -> %s" % (path, r, d0, d))
            model.hit("RoomTilesRelease of an unbuilt room: only the active-room pointer cleared")
    elif tag == "LUL0":
        h5["lul"][d["level"]] = d
        h5["rtfree"] = set()
    elif tag == "LUL1":
        d0 = h5["lul"].pop(d["level"], None)
        if d0 is None:
            model.check(False, "%s LUL1 without LUL0 (level %d)" % (path, d["id"]))
            return
        ok = d["r10"] == 0 and d["n"] == 0 and d["rot"] == 0 and d["ps"] == 0
        built = {rm[0] for rm in d0["rooms"] if rm[3]}
        ok = ok and built <= h5["rtfree"]
        if d0["keep"]:
            want = [rm[2] & 1 for rm in d0["rooms"]]
            ok = ok and d["arr"] == want and d0["n"] == len(d0["rooms"])
            model.hit("LevelUnload (keep): +0x60 bit 0 saved per room, %d rooms, %d with bit 0"
                      % (len(want), sum(want)))
            h5["lul1"][d["level"]] = d["arr"]
        else:
            ok = ok and d["a22c"] == 0
            model.hit("LevelUnload (no keep): saved array freed")
            h5["lul1"].pop(d["level"], None)
        model.check(ok, "%s LevelUnload level %d: %s -> %s (RoomTiles freed %d of %d built)"
                    % (path, d["id"], {k: v for k, v in d0.items() if k != "rooms"}, d, len(built & h5["rtfree"]),
                       len(built)))
        model.hit("LevelUnload: rooms, rotation list, presets freed (%s rotation nodes)" % ("with" if d0["rot"] else "no"))
        if built:
            model.hit("LevelUnload: built rooms' RoomTiles freed through RoomFree", len(built))
        for rm in d0["rooms"]:
            rooms.pop(rm[0], None)
            h5.get("reseeded", set()).discard(rm[0])
            h5["released"].discard(rm[0])
        h5["li"].discard(d["level"])
        h5["unloaded"] = h5.get("unloaded", set()) | {d["level"]}
    elif tag == "LRS0":
        h5.setdefault("lrs", {})[d["level"]] = d
        saved = h5["lul1"].get(d["level"])
        if d["a22c"]:
            model.check(saved is not None and d["arr"] == saved and d["n"] == len(saved),
                        "%s LevelRoomStateRestore level %d: array %s, saved at unload %s" % (path, d["id"], d["arr"], saved))
            model.hit("LevelRoomStateRestore on a rebuild with the saved array")
        else:
            model.hit("LevelRoomStateRestore without a saved array (first build or no-keep unload)")
    elif tag == "LRS1":
        d0 = h5.get("lrs", {}).pop(d["level"], None)
        if d0 is None:
            return
        before = d0["rooms"]
        ok = [rm[0] for rm in before] == [rm[0] for rm in d["rooms"]]
        nset = 0
        for i, (rm0, rm1) in enumerate(zip(before, d["rooms"])):
            add = 1 if (d0["a22c"] and i < len(d0["arr"]) and d0["arr"][i]) else 0
            ok = ok and rm1[1] == (rm0[1] | add)
            nset += add and not rm0[1] & 1
        model.check(ok, "%s LevelRoomStateRestore level %d: %s -> %s" % (path, d["id"], before, d["rooms"]))
        if nset:
            model.hit("LevelRoomStateRestore: room +0x60 bit 0 restored from the saved array", nset)
    elif tag == "LI0":
        if "ret" not in d:
            return
        name = LI_CALLERS.get(d["ret"])
        model.check(name is not None, "%s LevelInit from an unknown return address %08x" % (path, d["ret"]))
        model.check(d["level"] not in h5["li"], "%s level %d (%08x) built twice without an unload"
                    % (path, d["id"], d["level"]))
        h5["li"].add(d["level"])
        model.hit("LevelInit caller %s%s" % (name, " (a rebuild after LevelUnload)" if d["level"] in h5.get("unloaded", ())
                                              else ""))
    elif tag == "PLB":
        d["_t"], d["_a"] = 0, 0
        h5["plb"].append(d)
    elif tag in ("PLBT", "PLBA"):
        if h5["plb"]:
            h5["plb"][-1]["_t" if tag == "PLBT" else "_a"] += 1
    elif tag == "PLBX":
        if "at" in d:
            h5["plbx_at"] = True
        else:
            # logs written before the 0x006681F0 exit line (sessions 1-2 of run:2026-10-16-sweep-roomk): a build that
            # left through that exit has no PLBX; check it without its exit seed when a later PLBX passes it
            while h5["plb"] and h5["plb"][-1]["level"] != d["level"]:
                plb_check(model, path, h5["plb"].pop(), None)
        d0 = h5["plb"].pop() if h5["plb"] else None
        if d0 is None or d0["level"] != d["level"]:
            model.check(False, "%s PLBX without its PLB (level %d)" % (path, d["id"]))
            return
        plb_check(model, path, d0, d)
    elif tag == "WXP":
        rec = model.data.lvlwarp[d["rec"]] if d["rec"] is not None and 0 <= d["rec"] < len(model.data.lvlwarp) else None
        ok = (rec is not None and rec.id == d["id"] and tuple(rec.exitwalk) == (d["ewx"], d["ewy"])
              and (d["tx"], d["ty"]) == (d["wx"] + d["ewx"], d["wy"] + d["ewy"]))
        model.check(ok, "%s warp exit %s, LvlWarp row %s" % (path, d, rec and (rec.id, rec.exitwalk)))
        model.hit("warp exit position = paired warp + LvlWarp ExitWalkX/Y (row %d, Id %d)" % (d["rec"], d["id"]))
        h5["wxp_open"][d["u"]] = (d["tx"], d["ty"])
    elif tag == "WXPX":
        model.hit("warp exit: unit placed at the warp (%s)" % ("yes" if d["pos"] else "no position"))
    elif tag == "PLR":
        for u, (tx, ty) in list(h5["wxp_open"].items()):
            if (d["x"], d["y"]) == (tx, ty):
                model.hit("warp exit: the player stood on the exit position afterwards")
                del h5["wxp_open"][u]


def run_log(model, path, prep_pred=None):
    """prep_pred (plan 0027): {LSUB line: grids} from GenModel.prep_pred, the out-room grids GenModel predicted for the
    first LvlSub pass of a type-1 room; when given, those grids replace the logged ones (which stay as the check)."""
    ev = parse_log(path)
    data = model.data
    rooms = model.rooms = {}        # pointers are per run
    data.reset_process()            # one log = one game process: fresh DS1 cache
    model.instances = {}
    pending = {}                    # room -> TINIT dict until its RACT
    h5 = {"rtr": {}, "rrel": {}, "released": set(), "k_first": {}, "lul": {}, "lul1": {}, "li": set(),
          "plb": [], "wxp": [], "wxp_open": {}, "rtfree": set(), "ever": set()}     # plan 0038 H5c state
    model.h5_ever = h5["ever"]
    lsub_grids = {}
    acts = []
    for i, (tag, d) in enumerate(ev):
        if tag == "LOGERR":
            model.check(False, "%s: logger error %s" % (path, d["msg"]))
            continue
        r = d.get("room")
        try:
            if tag == "RRESEED":
                st = h5.get("rne", {}).pop(r, None)
                if st is not None:
                    h5c_rne_close(model, path, r, st)
                h5.setdefault("reseeded", set()).add(r)
                old = rooms.get(r)
                R = Room(d, data)
                rooms[r] = R
                if r in h5["released"]:
                    # plan 0038 H5c: a released room activated again keeps its +0x04, DT1 list and DS1 bits
                    h5["released"].discard(r)
                    R.reactivated = True
                    model.check(old is not None and old.r04 == R.r04 and old.level == R.level,
                                "%s %08x re-activated room: +0x04 %08x, before %s" % (path, r, R.r04,
                                                                                      old and "%08x" % old.r04))
                    model.check((d["f28"] & 0x3000000) == (old.f28_rel & 0x3000000) if hasattr(old, "f28_rel") else True,
                                "%s %08x re-activated room lost 0x1000000/0x2000000" % (path, r))
                    model.hit("re-activation of a released room (RRESEED after RoomTilesRelease)")
                model.check(d["rt"] == 0, "%s %08x RRESEED with a RoomTile already" % (path, r))
                model.check(d["seed"] is not None, "")
                model.check_dt1(path, R, d)
            elif tag == "LSUB":
                R = rooms[r]
                model.check(d["seed"] == fmt(R.seed), "%s %08x LSUB seed %s model %s" % (path, r, d["seed"], fmt(R.seed)))
                logged = {k: Grid.from_log(d[k]) for k in ("orient", "wall", "floor")}
                if R.sub_grids is None:
                    pred = prep_pred.get(d["_ln"]) if prep_pred is not None else None
                    if pred is not None:
                        model.check(all((pred[k].w, pred[k].h, pred[k].c) == (logged[k].w, logged[k].h, logged[k].c)
                                        for k in logged),
                                    "%s %08x first LSUB grids differ from GenModel's out-room prediction" % (path, r))
                        R.sub_grids = {k: pred[k].copy() for k in pred}
                        model.hit("type-1 rooms: first LvlSub grids from GenModel's prediction (drlg/0008 16.4)")
                    else:
                        R.sub_grids = logged
                        if prep_pred is not None:
                            model.hit("type-1 rooms: first LvlSub grids from the log (no prediction)")
                else:
                    model.check(all(R.sub_grids[k].c == logged[k].c for k in logged),
                                "%s %08x LSUB grids differ from the modelled previous pass" % (path, r))
                    R.sub_grids = logged
                if R.nodes is None:
                    R.nodes = []          # sub_0066EEA0_RoomTileAlloc runs before the passes
                    R.arr = {"W": [], "F": [], "S": []}
                R.lsub = d
                R.lsub_passes.append(d)
            elif tag == "LSUBX":
                R = rooms[r]
                groups = {int(k): v for k, v in d["groups"].items()}
                for rec, gl in groups.items():
                    S = data.sub_ds1(rec)
                    filed = [list(g) for g in S["groups"]]
                    if S["truncated"]:
                        model.check(gl is not None and len(gl) == len(filed) and gl[:-1] == filed[:-1]
                                    and gl[-1][0] == filed[-1][0],
                                    "%s %08x LvlSub rec %d groups (truncated file) %s" % (path, r, rec, gl))
                        S["groups"] = [tuple(g) for g in gl]
                        S["runtime_groups"] = gl
                    else:
                        model.check(gl == filed, "%s %08x LvlSub rec %d groups %s, file %s" % (path, r, rec, gl, filed))
                model.lsub_pass(R, R.lsub, R.sub_grids)
                model.check(d["seed"] == fmt(R.seed), "%s %08x LSUBX seed %s model %s" % (path, r, d["seed"], fmt(R.seed)))
            elif tag == "TINIT":
                R = rooms[r]
                model.check(d["seed"] == fmt(R.seed), "%s %08x TINIT seed %s model %s" % (path, r, d["seed"], fmt(R.seed)))
                if R.type == 1:
                    model.check_outroom_mask(path, R)
                elif R.type == 2:
                    model.check_preset_grids(path, R, d)
                if R.type == 1 and R.sub_grids is not None:
                    model.prepare_tail(R, R.sub_grids)
                    tg = {k: Grid.from_log(v) for k, v in d["grids"].items()}
                    model.check(all(R.sub_grids[k].c == tg[k].c for k in tg),
                                "%s %08x TINIT grids differ from the modelled LvlSub + theme + border" % (path, r))
                for q, built, sd in d["nbstate"]:
                    if q == r:
                        continue
                    N = rooms.get(q)
                    mb = N is not None and N.nodes is not None and N.built
                    model.check(bool(built) == mb, "%s %08x neighbour %08x built=%d model %d" % (path, r, q, built, mb))
                    if built and N is not None:
                        model.check(sd == fmt(N.seed), "%s %08x neighbour %08x seed %s model %s" % (path, r, q, sd, fmt(N.seed)))
                pending[r] = (d, i)
            elif tag in ("O89", "O89D", "O89R", "O89U"):
                rooms[r].o89.append((tag, d))
            elif tag in H5C_TAGS:
                h5c_event(model, path, tag, d, rooms, pending, h5)
            elif tag == "RACT":
                R = rooms[r]
                if r in pending:
                    td, _ = pending.pop(r)
                    if R.nodes is None:
                        R.nodes = []
                        R.arr = {"W": [], "F": [], "S": []}
                    R.ktile0 = R.draws
                    model.tiles_build(R, td)
                    R.built = True
                    model.check(not R.o89, "%s %08x %d O89 line(s) not consumed by the model" % (path, r, len(R.o89)))
                    R.k = R.draws
                    model.check(d["seed"] == fmt(R.seed),
                                "%s %08x RACT seed %s model %s (k model %d)" % (path, r, d["seed"], fmt(R.seed), R.k))
                    acts.append(R)
                    h5c_ract(model, path, R, d, h5)
                else:
                    model.check(False, "%s %08x RACT without TINIT" % (path, r))
                model.stepr(R)                 # DRLG_RoomActivate's draw
                R.draws -= 1
            elif tag == "AROOM":
                R = rooms[r]
                model.check(d["seed"] == fmt(R.seed), "%s %08x AROOM seed %s model %s" % (path, r, d["seed"], fmt(R.seed)))
                model.check(d["aseed"] == "%08x:%08x" % (R.seed[0], INIT_HIGH),
                            "%s %08x AROOM active seed %s, model init(%08x)" % (path, r, d["aseed"], R.seed[0]))
                R.copy = "client" if d["flags"] & 4 else "server"
                if getattr(model, "aroom_pred", None) is not None:      # tools/monspawn.py: the model's active seed
                    model.aroom_pred.append((r, d["aroom"], R.r04, R.seed[0], R.k))
            elif tag == "TL":
                model.tl[d["p"]] = d["w6"]
            elif tag == "CB":
                model.cb_entries(path, d, rooms)
            elif tag == "RTFREE":
                R = rooms.get(r)
                if R is not None:
                    R.nodes = None
                    R.built = False
                h5["rtfree"].add(r)
        except ModelError as e:
            model.check(False, "%s %s %08x: %s" % (path, tag, r or 0, e))
        except (KeyError, StopIteration) as e:
            model.check(False, "%s %s %08x: missing input (%r)" % (path, tag, r or 0, e))
    for r in pending:
        model.check(False, "%s %08x TINIT without RACT" % (path, r))
    for d0 in h5["plb"]:
        if h5.get("plbx_at"):
            model.check(False, "%s PresetLevelBuild level %d without its exit line" % (path, d0["id"]))
        else:
            plb_check(model, path, d0, None)
    for r0, st in h5.get("rne", {}).items():
        h5c_rne_close(model, path, r0, st, True)
        model.hit("RoomNeighboursEnsure without a later re-seed of its room (session end or a neighbour-only call)")
    for k in h5["wxp_open"].values():
        model.hit("warp exit: the player's position never equalled the exit position (session ended or moved on)")
    return acts


def cmd_roomk(argv):
    root, exe, verbose, paths = DEFAULT_DATA, DEFAULT_EXE, False, []
    it = iter(argv)
    for a in it:
        if a == "--root":
            root = next(it)
        elif a == "--exe":
            exe = next(it)
        elif a == "-v":
            verbose = True
        else:
            paths.append(a)
    if not paths:
        print(__doc__)
        return 2
    model = Model(Data(root, exe), verbose)
    total = 0
    for p in paths:
        acts = run_log(model, p)
        total += len(acts)
        by = {}
        for R in acts:
            by.setdefault((getattr(R, "copy", "?"), R.type), []).append(R.k)
        summary = " ".join("%s/type%d=%d(k %d..%d)" % (c, t, len(v), min(v), max(v)) for (c, t), v in sorted(by.items()))
        levels = sorted({R.level for R in acts})
        print("%s: %d activations; %s; levels %s" % (p, len(acts), summary, levels))
    for k in sorted(model.cov):
        print("  coverage %-45s %d" % (k, model.cov[k]))
    print("roomk: %d activations, %d checks, %d mismatches" % (total, model.checks, model.fail))
    return 1 if model.fail else 0


def cmd_tables(argv):
    exe = argv[argv.index("--exe") + 1] if "--exe" in argv else DEFAULT_EXE
    o, t = remap_tables(exe)
    print("0x006EF620 (new orientation -> row):", o)
    for r in range(len(t) // 7):
        print("0x006EF574 row %d (old o 0..7):" % r, t[r * 7:r * 7 + 8])
    return 0


def cmd_p1cmp(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    old, new = {}, {}
    for line in open(argv[0], errors="replace"):
        if line.startswith("RACT "):
            kv = dict(item.split("=", 1) for item in line.split()[1:])
            old.setdefault(kv["r04"], []).append(kv["seed"])
    for tag, d in parse_log(argv[1]):
        if tag == "RACT":
            new.setdefault("%08x" % d["r04"], []).append(d["seed"])
    same = sum(1 for k, v in old.items() if new.get(k, [])[:len(v)] == v)
    for k, v in sorted(old.items()):
        if new.get(k, [])[:len(v)] != v:
            print("MISMATCH r04=%s old %s new %s" % (k, v, new.get(k)))
    print("p1cmp: %d rooms in %s, %d with the same RACT seeds (k) in %s" % (len(old), argv[0], same, argv[1]))
    return 0 if same == len(old) else 1


# --------------------------------------------------------------------- plan 0016 Phase 2: preset units
# docs/findings/drlg/0004-preset-units.md. A unit is a tuple (type, id, mode, x, y, flags, path), path None or a
# tuple of (action, x, y) points, as the logger prints them (tools/gdb/drlg-preset.py) without the pointer.

ACT2_REWRITES = {297: 382, 366: 404}             # DS1_Parse 0x00665CB2, act index 2, MonStats ids -> objects
ACT4_REWRITES = {514: 461, 537: 476, 538: 475, 539: 474}   # act index 4: nihlathak, ancientstatue1..3 (1013 - id)
CLIENT_OBJ_DEFS = {1, 3, 26, 27, 28, 300}        # DRLG_PresetRoomLoadDs1 -> DRLG_PresetClientObjects
B_SKIP3_MAINS = {0, 4, 8, 16, 29, 39}            # sub_00666220 switch (0x0066638C): style-4 mains that skip 3 rows
DROP_MON = {204, 205, 371, 372}                  # MonStats ids kept when r % 3 == 0


class PresetUnitData:
    """The DS1 side of the preset-unit model: DS1_Parse's unit list (drlg/0001 § Object entries plus the act
    rewrites of drlg/0004) from tools/ds1.py's byte parser, and the tables it maps through."""

    def __init__(self, root, exe):
        self.root = root
        t = ds1mod._tables(root)
        self.nm, self.ns = t["n_monstats"], t["n_superuniques"]
        self.monpreset = {}
        for r in t["monpreset"]:
            self.monpreset.setdefault(r["Act"] - 1, []).append((r["PlaceKind"], r["Place"]))
        self.objtab = ds1mod._object_table(exe)
        if self.objtab is None:
            raise ModelError("the preset-unit model needs the pinned game.exe (g_Ds1ObjectIds)")
        self._cache = {}

    def ds1(self, cell):
        """{units: head-first list (reverse file order), size_y, cols, floor0} for a LvlPrest File cell."""
        if cell in self._cache:
            return self._cache[cell]
        path = os.path.join(self.root, "data", "global", "tiles", cell.replace("\\", "/").lower())
        f = ds1mod.parse(open(path, "rb").read())
        v = f["version"]
        act = min(f["act"] or 0, 4) if v >= 8 else 0
        units = []                                   # head first: DS1_Parse prepends
        rewrites = []
        for o in f["objects"]:
            typ, uid, mode = o["type"], o["id"], 0
            if typ == 1:
                mode = 1
                if v > 4:
                    lst = self.monpreset.get(act, [])
                    if uid < len(lst):
                        kind, place = lst[uid]
                        uid = {0: self.nm + self.ns + place, 2: self.nm + place, 1: place}.get(kind, -1)
                    if act == 2 and uid < self.nm and uid in ACT2_REWRITES:
                        rewrites.append((act, uid, ACT2_REWRITES[uid]))
                        uid, typ, mode = ACT2_REWRITES[uid], 2, 0
                    elif act == 4 and 0 <= uid < self.nm and uid in ACT4_REWRITES:
                        rewrites.append((act, uid, ACT4_REWRITES[uid]))
                        uid, typ, mode = ACT4_REWRITES[uid], 2, 0
            elif typ == 2:
                if v < 6:
                    uid = -1 if uid == 0x23D else uid
                elif uid < 150:
                    uid = self.objtab[act][uid]
                else:
                    uid -= 150
            elif typ == 4:
                mode = 3
                raise ModelError("%s: item preset units are not modelled" % cell)
            flags = o["flags"] if v > 5 else 0
            if uid >= 0 and (o["type"] != 1 or v > 4):
                units.insert(0, [typ, uid, mode, o["x"], o["y"], flags or 0, None])
        for p in f["paths"]:
            if not p["points"]:
                continue
            for u in units:                          # first in the list = last in the file
                if (u[3], u[4]) == (p["x"], p["y"]):
                    u[6] = tuple((pt[2] if len(pt) > 2 else 1, pt[0], pt[1]) for pt in p["points"])
                    break
        out = dict(units=[tuple(u) for u in units], size_y=f["size_y"], cols=f["cols"], rewrites=rewrites,
                   floor0=list(f["layers"]["floor0"]) if f["floor_layers"] else None)
        self._cache[cell] = out
        return out

    def drop_rolls(self, units, seed, ox, oy):
        """DRLG_PresetUnitDropRolls: walk the DS1 list from its head, one draw for the ten ids, a kept
        unit copied with x/y and path points + (ox, oy) and prepended. Returns (instance list head first,
        seed, [(type, id, r, kept)])."""
        nm, ns = self.nm, self.ns
        inst, draws = [], []
        for u in units:
            typ, uid = u[0], u[1]
            test = None
            if typ == 1:
                if uid < nm:
                    if uid in DROP_MON:
                        test = lambda r: r % 3 == 0
                elif uid - nm >= ns:
                    test = {33: lambda r: r & 3 != 0, 34: lambda r: r & 1 != 0,
                            35: lambda r: r & 3 == 0}.get(uid - nm - ns)
            elif typ == 2:
                if uid in (196, 261):
                    test = lambda r: r & 1 == 0
                elif uid == 581:
                    test = lambda r: r & 3 != 0
            if test is not None:
                seed = step(*seed)
                keep = test(seed[0])
                draws.append((typ, uid, seed[0], keep))
                if not keep:
                    continue
            path = None if u[6] is None else tuple((a, x + ox, y + oy) for a, x, y in u[6])
            inst.insert(0, (typ, uid, u[2], u[3] + ox, u[4] + oy, u[5], path))
        return inst, seed, draws

    def centre_monster(self, prect):
        """sub_006664A0_PresetCentreMonster: MonStats 266 (or -1) at the instance centre, mode 1."""
        x, y, w, h = prect
        return (1, 266 if self.nm > 266 else -1, 1, (x + int(w / 2)) * 5, (y + int(h / 2)) * 5, 0, None)

    def client_objects(self, d, prect, defn, skips=None):
        """DRLG_PresetClientObjects with sub_006661A0 (column) and sub_00666220 (rows): the units it
        prepends, in creation order, every one with flags bit 0. `skips` (a list) receives (row, main) of every
        three-row skip sub_00666220 takes (0x00666368)."""
        x0, y0, w, h = prect
        out = []

        def col(xt, yt):                          # sub_006661A0: object 65 every 40 subtiles down the DS1
            ys, yend = yt * 5, (d["size_y"] + yt) * 5
            while ys < yend:
                out.append((2, 65, 0, xt * 5, ys, 1, None))
                ys += 40

        def rows(c):                              # sub_00666220: 40, 41, 41, 41, 42 one tile apart, per row
            cc = c if c > 0 else 0
            j = 0
            while j < h:
                xs, ys = (x0 + c) * 5 - 5, (y0 + j) * 5
                for k, oid in enumerate((40, 41, 41, 41, 42)):
                    out.append((2, oid, 0, xs + 5 * k, ys, 1, None))
                cell = d["floor0"][j * (w + 1) + cc]
                if (cell >> 20) & 0x3F == 4 and (cell >> 8) & 0xFF in B_SKIP3_MAINS:
                    if skips is not None:
                        skips.append((j, (cell >> 8) & 0xFF))
                    j += 3
                j += 1
        if defn == 27:
            col(x0, y0)
            rows(-1)
        else:
            c = 0
            while c < w:
                cell = d["floor0"][c]
                if (cell >> 20) & 0x3F == 2 and (cell >> 8) & 0xFF == 0x18:
                    col(c + x0 + 1, y0)
                    rows(c)
                    c += 4
                c += 1
        return out


def units_of(logged):
    """A logged unit list without the pointers."""
    return [(u[1], u[2], u[3], u[4], u[5], u[6], None if u[7] is None else tuple(tuple(p) for p in u[7]))
            for u in logged]


def pop_found(P, x, y, pad):
    """DRLG_PresetPopsUpdate's search: the first pop rectangle (tiles) that holds the player, its
    sides x5 and its width and height + PopPad (0x00667224..0x00667288, half-open sub_0066B980_RectContains);
    the pop index of that entry, or 0."""
    for (rx, ry, rw, rh), idx in zip(P["rects"], P["idx"]):
        x0, y0 = rx * 5, ry * 5
        if x0 <= x < x0 + rw * 5 + pad and y0 <= y < y0 + rh * 5 + pad:
            return idx
    return 0


def to_room(units, rect):
    """DRLG_PresetUnitsToRoom: the units inside the room rectangle (x5, half-open) leave the instance
    list and are prepended to the room list, re-expressed relative to the room origin (path points untouched)."""
    rx, ry, rw, rh = (v * 5 for v in rect)
    keep, moved = [], []
    for u in units:
        if rx <= u[3] < rx + rw and ry <= u[4] < ry + rh:
            moved.insert(0, u[:3] + (u[3] - rx, u[4] - ry) + u[5:])
        else:
            keep.append(u)
    return keep, moved


# ------------------------------------------------------------------------------ Phase 3: generators

GEN_TAGS = ("LC0", "LC1", "LI0", "LI1", "RC", "RL", "PIC", "PICX", "PIO", "MFR", "MFRX", "PRC", "PUR", "PURX",
            "MZ0", "MZ1", "OD0", "OD1", "LSR", "LSRX")
# plan 0022 Phase 2, tools/gdb/drlg-maze.py
MAZE_TAGS = ("MZA", "MZD", "MZF", "LNK0", "LNKL", "LK27", "LNK1", "LNKS", "LWP", "WPR", "ODD", "ODG")   # the last two:
# plan 0026 Phase 2, tools/gdb/drlg-outdoor.py
# plan 0016 Phase 2, tools/gdb/drlg-preset.py
# plan 0026 Phase 3 follow-up: roomk lines in gen logs (tools/gdb/drlg-roomk.py), the out-room grids at the first LvlSub pass
ROOMPREP_TAGS = ("RRESEED", "LSUB")
PRESET_TAGS = ("PSL", "PRR", "PRRX", "PLD", "PLDX", "PTR0", "PTR1", "RPU", "PSP", "RPL", "L27", "L27X", "LIP",
               "POPR", "POPU", "WPHIT", "LGB", "LGW", "FLG", "PUC",   # POPR..LGW: tools/gdb/drlg-preset-wp.py
               "RSK", "RSKON")                                         # plan 0020 Phase 4: the client row skip
# sub_006738C0_MazePresetFile: first LvlPrest Def of the maze-room range, by level type (+0x1C0)
MAZE_DEF_BASE = {3: 0x34, 4: 0x6C, 7: 0xA7, 8: 0xCD, 10: 0x101, 13: 0x12D, 17: 0x19D, 18: 0x1E1, 22: 0x2F1,
                 24: 0x298, 25: 0x2C0, 28: 0x344, 33: 0x3EA, 34: 0x422, 35: 0x41C}
# return addresses that tell which code called DRLG_RoomCreate / PresetInstanceCreate
RET_RC_PRESET_SPLIT = 0x00666694      # sub_00666680_PresetRoomCreate (8x8 split of a preset)
RET_RC_PRESET_SINGLE = 0x00667F7A     # sub_00667ED0_PresetRoomsCreate, one room for the preset
RET_RC_OUTROOM = 0x0067D554           # sub_0067D540_OutRoomCreate
RET_RC_MAZE_FIRST = 0x00673B41        # sub_00673B30_MazeLevelBuild, its first room
RET_RL_PRESET_SPLIT = 0x006666FC      # sub_0066B970 from sub_00666680_PresetRoomCreate
RET_RL_PRESET_SINGLE = 0x00667FD7     # sub_0066B970 from sub_00667ED0_PresetRoomsCreate (one room)
RET_RL_OUTROOM = 0x0067D574           # sub_0066B970 from sub_0067D540_OutRoomCreate
RET_PIC_LEVEL = 0x0066812E            # sub_00668100_PresetLevelBuild
RET_PIC_OUTDOOR = 0x006751CE          # sub_006750F0_OutdoorRoomsCreate
RET_PIC_MAZE = 0x00673A83             # sub_00673A60_MazeRoomToPreset


def seed_t(sv):
    lo, hi = sv.split(":")
    return (int(lo, 16), int(hi, 16))


class GenLevel:
    def __init__(self, d):
        self.ptr, self.id, self.drlg, self.ltype = d["level"], d["id"], d["drlg"], d["ltype"]
        self.seed = None
        self.window = None          # "maze" / "outdoor": inside a boundary-oracle window
        self.create_idx = None
        self.init_idx = None
        self.rooms = []             # RL events of this level's current build, in order
        self.maze_list = None
        self.maze_pic = []
        self.rot = {}               # sub_006738C0 counters per def
        self.inited = False
        self.prc_n = 0


class GenModel:
    def __init__(self, data, verbose=False, oracle=False, pu=None):
        self.data = data
        self.verbose = verbose
        self.oracle = oracle        # --preset-oracle: sub_00667620 as the plan 0008 boundary oracle (ADR-0004)
        self.pu = pu                # PresetUnitData, the model that replaces it
        self.checks = self.fail = 0
        self.cov = {}
        self.prooms = []            # (log, level id, Def, copy, units in the room, roll caller) per reproduced room
        self.populate = [struct.unpack_from("<i", r, 0x08)[0] for r in excel_bin(data.root, "lvlprest")]
        self.logicals = [struct.unpack_from("<i", r, 0x0C)[0] for r in excel_bin(data.root, "lvlprest")]
        self.poppad = [struct.unpack_from("<i", r, 0x3C)[0] for r in excel_bin(data.root, "lvlprest")]
        self.prest_by_level = {}
        for i, rec in enumerate(excel_bin(data.root, "lvlprest")):
            lid = struct.unpack_from("<i", rec, 0x04)[0]
            self.prest_by_level.setdefault(lid, i)
        self.files = [struct.unpack_from("<i", r, 0x40)[0] for r in excel_bin(data.root, "lvlprest")]
        load_outdoor(data.root, data.exe)        # also load_links (the act link builder's tables)
        self._prest_raw = excel_bin(data.root, "lvlprest")
        self._wgrid = {}
        self._pu = pu
        self.wp_pred = {}
        self.prep_pred = {}
        import excel_bin as xb
        import excel_layouts
        olay = [fl for fl in excel_layouts.LAYOUTS["objects"]["fields"] if fl.get("col") == "SubClass"][0]
        orecs, _ = xb.read_bin(xb.find_file(os.path.join(data.root, "data", "global", "excel"), "objects", ".bin"))
        self._subclass = [xb.decode_field(r, olay) for r in orecs]

    def check(self, ok, what):
        self.checks += 1
        if not ok:
            self.fail += 1
            print("MISMATCH " + what)
        elif self.verbose:
            print("ok " + what)

    def hit(self, what, n=1):
        self.cov[what] = self.cov.get(what, 0) + n

    @staticmethod
    def rng_range(seed, n):
        """RNG_Range / RNG_RangeB and the inlined copy in sub_00666ED0: n <= 0 (signed) -> 0, no step."""
        if n <= 0:
            return seed, 0
        seed = step(*seed)
        return seed, (seed[0] & (n - 1)) if n & (n - 1) == 0 else seed[0] % n

    def run(self, path):
        levels = {}
        ps_level = {}
        ps_idx = {}
        lsr = {}
        npre = 0
        # per process: preset instances, DRLG rooms, the model's room lists, level-27 indices
        self.inst, self.room, self.rlists, self.pend, self.l27 = {}, {}, {}, {}, {}
        if not hasattr(self, "rsk_logs"):
            self.rsk_logs = set()
        self.maze_reset(path)
        self.cur_levels = levels
        self.wp_by_level = {}       # level pointer -> [(line of LI1, level id, xs, ys, out rooms whose flags are unknown)]
        self.ln = 0
        self.spawn_room = {}
        self.pops = {}
        self.flag_other, self.flg_logged = {}, False
        self.od_last, self.prep_rooms = {}, {}
        self.prep_pred = {}         # LSUB line -> the predicted out-room grids (plan 0027: roomk's input)
        for line in open(path, errors="replace"):
            self.ln += 1
            tag, _, rest = line.partition(" ")
            if tag == "LOGERR":
                self.check(False, "%s: logger error %s" % (path, rest.strip()))
                continue
            if tag not in GEN_TAGS and tag not in MAZE_TAGS and (tag not in PRESET_TAGS or self.oracle) \
                    and tag not in ROOMPREP_TAGS:
                continue
            d = json.loads(rest)
            if tag == "RC" and "level" not in d:
                continue        # tools/gdb/affixes.py's RC (the rare affix count) in a combined log (plan 0048)
            try:
                if tag in ROOMPREP_TAGS:
                    self.room_prep_event(path, tag, d)
                elif tag in MAZE_TAGS:
                    self.maze_event(path, tag, d, levels)
                elif tag in PRESET_TAGS:
                    self.preset_event(path, tag, d, levels)
                else:
                    self.event(path, tag, d, levels, ps_level, ps_idx, lsr)
            except (KeyError, ModelError, Fatal) as e:
                self.check(False, "%s %s: %r" % (path, tag, e))
            npre += 1
        return levels

    # plan 0016 Phase 2: the preset-unit pipeline (docs/findings/drlg/0004-preset-units.md)
    def rolls(self, I, seed, caller):
        d1 = self.pu.ds1(I["cell"])
        x, y = I["prect"][0], I["prect"][1]
        units, out, draws = self.pu.drop_rolls(d1["units"], seed, x * 5, y * 5)
        I["units"], I["caller"] = units, caller
        self.hit("drop rolls %s: calls" % caller)
        for act, a, b in d1["rewrites"]:
            self.hit("act rewrite in a rolled DS1: act index %d, MonStats %d -> object %d" % (act, a, b))
        if draws:
            self.hit("drop rolls %s: calls that draw" % caller)
        mp = self.pu.nm + self.pu.ns
        for typ, uid, r, keep in draws:
            what = "object %d" % uid if typ == 2 else "MonStats %d" % uid if uid < mp else \
                "MonPlace %d (place_group%d)" % (uid - mp, {33: 25, 34: 50, 35: 75}[uid - mp])
            self.hit("drop roll %s: %s" % (what, "kept" if keep else "dropped"))
        I["draws"] = draws
        return out

    def preset_event(self, path, tag, d, levels):
        where = "%s %s" % (path, tag)
        if tag == "PSL":
            I = self.inst[d["ps"]]
            self.check(units_of(d["units"]) == I["units"], "%s ps %08x Def %d: instance list after the level-seed rolls "
                       "differs from the model (%d logged, %d model)" % (where, d["ps"], I["def"], len(d["units"]), len(I["units"])))
            self.hit("instance lists checked after the level-seed rolls")
        elif tag == "PRR":
            I = self.inst[d["ps"]]
            want = self.room.get(d["room"], {}).get("seed")
            self.check(d["isroom"] == 1, "%s: PresetRoomLoadDs1 rolls on a seed that is not room +0x14" % where)
            self.check(I["units"] is None, "%s ps %08x: a second roll for one instance" % (where, d["ps"]))
            self.check(want is not None and seed_t(d["seed"]) == want, "%s room %08x Def %d: room seed into the rolls %s, model "
                       "step(Init(level lo at RoomCreate)) %s" % (where, d["room"], I["def"], d["seed"], want and fmt(want)))
            self.pend[d["room"]] = self.rolls(I, want or seed_t(d["seed"]), "room seed")
        elif tag == "PRRX":
            I = self.inst[d["ps"]]
            out = self.pend.pop(d["room"])
            self.check(seed_t(d["seed"]) == out, "%s room %08x: room seed after the rolls %s, model %s (%d draws)"
                       % (where, d["room"], d["seed"], fmt(out), len(I["draws"])))
            self.check(units_of(d["units"]) == I["units"], "%s ps %08x Def %d: instance list after the room-seed rolls differs"
                       % (where, d["ps"], I["def"]))
            self.hit("instance lists checked after the room-seed rolls")
        elif tag == "PLD":
            I = self.inst[d["ps"]]
            self.check((d["ds1"] == 0) == (I["units"] is None), "%s ps %08x: DS1 slot %08x, model %s" % (where, d["ps"], d["ds1"],
                       "unrolled" if I["units"] is None else "rolled"))
            self.check(d["pending"] == I["pending"], "%s ps %08x: pending %d, model %d" % (where, d["ps"], d["pending"], I["pending"]))
            self.pend[("pld", d["room"])] = I
        elif tag == "PLDX":
            I = self.pend.pop(("pld", d["room"]))
            rsk = self.pend.pop(("rsk", d["ps"]), [])
            skips = []
            if I["pending"] == 1:
                I["pending"] = 0
                if 4 <= I["def"] <= 7:
                    if I["lid"] == 2 and I["idx"] == 3:
                        I["units"] = [self.pu.centre_monster(I["prect"])] + I["units"]
                        self.hit("centre monster added (Blood Moor, file index 3)")
                elif I["def"] in CLIENT_OBJ_DEFS and d["f28"] & 0x40000:
                    added = self.pu.client_objects(self.pu.ds1(I["cell"]), I["prect"], I["def"], skips)
                    I["units"] = added[::-1] + I["units"]
                    self.hit("client river objects added (Def %d)" % I["def"])
            if path in self.rsk_logs:       # logs whose logger has the RSK breakpoint (RSKON at load)
                self.check(rsk == skips, "%s ps %08x Def %d: client row skips (row, main) logged %s, model %s"
                           % (where, d["ps"], I["def"], rsk, skips))
            for row, main in skips if path in self.rsk_logs else ():
                self.hit("client row skip (RSK) reproduced: Def %d file index %d, row %d, floor main %d"
                         % (I["def"], I["idx"], row, main))
            self.check(d["pending"] == 0, "%s ps %08x: pending %d after PresetRoomLoadDs1" % (where, d["ps"], d["pending"]))
            self.check(units_of(d["units"]) == I["units"], "%s ps %08x Def %d: instance list after PresetRoomLoadDs1 differs "
                       "(%d logged, %d model)" % (where, d["ps"], I["def"], len(d["units"]), len(I["units"])))
            self.hit("instance lists checked after PresetRoomLoadDs1")
        elif tag == "RSKON":
            self.rsk_logs.add(path)
        elif tag == "RSK":
            self.pend.setdefault(("rsk", d["ps"]), []).append((d["row"], d["main"]))
        elif tag == "PTR0":
            I = self.inst[d["ps"]]
            self.check(units_of(d["units"]) == I["units"], "%s ps %08x Def %d: instance list before PresetUnitsToRoom differs"
                       % (where, d["ps"], I["def"]))
            pre = units_of(d["rlist"])
            if pre:
                # a re-prepared room keeps its list: the room's previous modelled list must be the tail; the head
                # is units other code prepended in between (as at RoomPresetUnits), taken from the log
                # (a path the list held may since have been detached: logged path None, the unit otherwise equal)
                prev = self.rlists.get(d["room"])
                k = len(pre) - len(prev) if prev is not None else -1
                tail = pre[k:] if k >= 0 else []
                ok = k >= 0 and all(a[:6] == b[:6] and (a[6] == b[6] or a[6] is None) for a, b in zip(tail, prev))
                for a, b in zip(tail, prev) if ok else ():
                    if a[6] is None and b[6] is not None:
                        self.hit("room list not empty before PresetUnitsToRoom: unit path detached in between, type %d id %d"
                                 % (a[0], a[1]))
                self.check(ok, "%s room %08x Def %d: list before PresetUnitsToRoom does not end "
                           "with the room's previous list (%d logged, %s model)" % (where, d["room"], I["def"], len(pre),
                                                                                   "none" if prev is None else len(prev)))
                self.hit("room list not empty before PresetUnitsToRoom: re-prepared room, previous list as tail")
                if k > 0:
                    self.hit("room list not empty before PresetUnitsToRoom: units added by other code in between")
            keep, moved = to_room(I["units"], d["rect"])
            self.pend[("ptr", d["room"])] = (keep, moved + pre, d)
        elif tag == "PTR1":
            keep, rl, d0 = self.pend.pop(("ptr", d["room"]))
            I = self.inst[d["ps"]]
            self.check(units_of(d["units"]) == keep, "%s ps %08x Def %d: instance list after PresetUnitsToRoom differs"
                       % (where, d["ps"], I["def"]))
            self.check(units_of(d["rlist"]) == rl, "%s room %08x Def %d: room unit list differs from the model "
                       "(%d logged, %d model)" % (where, d["room"], I["def"], len(d["rlist"]), len(rl)))
            I["units"] = keep
            self.rlists[d["room"]] = rl
            copy = "client" if d0["f28"] & 0x40000 else "server"
            self.hit("preset rooms: unit list reproduced (%s copy)" % copy)
            self.hit("preset rooms: unit list reproduced, act %d" % (d0["lid"] and self.act_of(d0["lid"])))
            if rl:
                self.hit("preset rooms with at least one unit (%s copy)" % copy)
            if d0["lid"] and self.data.drlgtype[d0["lid"]] == 1:
                self.hit("preset rooms in a maze level: unit list reproduced, act %d (%s copy)"
                         % (self.act_of(d0["lid"]), copy))
            self.prooms.append((path, d0["lid"], I["def"], copy, len(rl), I["caller"]))
        elif tag == "RPU":
            rl = self.rlists.get(d["room"])
            if rl is not None:
                lg = units_of(d["rlist"])
                k = len(lg) - len(rl)
                # units that other code prepends to room +0x5C after PresetUnitsToRoom (warp and object
                # placement through sub_0066BF30_PresetUnitCreate with a room; PUC lines when logged) are inputs:
                # the modelled list must be the tail
                self.check(k >= 0 and lg[k:] == rl, "%s room %08x: list at RoomPresetUnits does not end with the modelled "
                           "room list (%d logged, %d model)" % (where, d["room"], len(lg), len(rl)))
                self.hit("server handover: modelled room list is the list's tail (RoomPresetUnits)")
                for u in lg[:k]:
                    self.hit("server handover: unit added after PresetUnitsToRoom by other code, type %d id %d" % (u[0], u[1]))
            self.spawn_room = d
        elif tag == "PSP":
            what = {1: "monster", 2: "object"}.get(d["type"], "type %d" % d["type"])
            self.hit("server preset spawn %s: %s" % (what, "unit created" if d["unit"] else "no unit"))
            R = self.room.get(getattr(self, "spawn_room", {}).get("room"))
            if R and R.get("pdef") is not None and self.populate[R["pdef"]] == 0 and d["type"] == 1:
                self.hit("Populate 0 room: preset monster spawn %s" % ("unit created" if d["unit"] else "no unit"))
        elif tag == "RPL":
            R = self.room.get(d["room"])
            if R and R.get("pdef") is not None:
                pop0 = self.populate[R["pdef"]] == 0
                # Populate 0 sets 0x800000 (0x006666EC, 0x00667FC7); two other writers set it on Populate-1 rooms:
                # 0x0066BD92 (a neighbour room is in a town level, the room's is not) and 0x0066E37E (hidden warp
                # tiles). With FLG lines logged the room's writer must be one of those.
                other = self.flag_other.get(d["room"])
                ok = d["pop"] == 0 if pop0 else (d["pop"] != 0 or other is not None or not self.flg_logged)
                self.check(ok, "%s room %08x Def %d (Populate %d): RoomPopLevelId %d" % (where, d["room"], R["pdef"],
                           self.populate[R["pdef"]], d["pop"]))
                self.hit("RoomPopLevelId on a preset room, Populate %d%s" % (0 if pop0 else 1, ", pop level 0 (%s)" % (
                    other or "writer not logged") if not pop0 and d["pop"] == 0 else ""))
        elif tag == "FLG":
            self.flg_logged = True
            self.flag_other[d["room"]] = {0x0066BD92: "next to a town room", 0x0066E37E: "hidden warp tiles"}.get(d["site"], "?")
            self.hit("room flag 0x800000 set at 0x%08X" % d["site"])
        elif tag == "PUC":
            self.hit("PresetUnitCreate into a room list by other code: caller 0x%08X, type %d id %d" % (d["ret"], d["type"], d["id"]))
        elif tag == "L27":
            s = seed_t(d["seed"])
            if d["v"] == 1:
                s = step(*s)
                idx = 2 - (s[0] & 1)
            elif d["v"] == 3:
                s = step(*s)
                idx = (~s[0]) & 1
            else:
                idx = None
            self.pend[("l27", d["act"])] = (s, idx, d["v"])
        elif tag == "L27X":
            if ("l27", d["act"]) not in self.pend:   # the first drlg-maze.py logs named LK27 so
                self.maze_event(path, "LK27", d, levels)
                return
            s, idx, v = self.pend.pop(("l27", d["act"]))
            self.check(idx is not None and d["idx"] == idx and seed_t(d["seed"]) == s,
                       "%s: level-27 index %d act seed %s, model %s %s (link value %d)" % (where, d["idx"], d["seed"], idx, fmt(s), v))
            self.l27[d["pd"]] = d["idx"]
            self.hit("level-27 index draw (link value %d)" % v)
        elif tag == "POPR":
            self.pops[d["ps"]] = d
            self.check(d["poppad"] == self.poppad[d["def"]], "%s Def %d: PopPad %d, table %d" % (where, d["def"], d["poppad"],
                       self.poppad[d["def"]]))
        elif tag == "POPU":
            P = self.pops.get(d["ps"])
            if P is None:
                return
            found = pop_found(P, d["x"], d["y"], P["poppad"])
            self.check(d["found"] == found, "%s Def %d: player (%d, %d) pop index %d, model %d (PopPad %d)"
                       % (where, P["def"], d["x"], d["y"], d["found"], found, P["poppad"]))
            self.hit("pop trigger positions reproduced (PopPad %d)" % P["poppad"])
            if found:
                self.hit("pop trigger positions inside a pop area (PopPad %d)" % P["poppad"])
            if pop_found(P, d["x"], d["y"], 0) != found:
                self.hit("pop trigger positions where PopPad decides (PopPad 0 would differ)")
        elif tag == "WPHIT":
            kind = d["what"].split(",")[0]
            self.hit("watch read: %s at 0x%08X (ret 0x%08X)" % (kind, d["pc"], d["ret1"] or 0))
        elif tag == "LGW":
            self.hit("logic box watches placed (player box in a Logicals-1 room, level %d)" % d["lid"])
        elif tag == "LGB":
            R = self.room.get(d["room"])
            if R and R.get("pdef") is not None:
                want = 2 if self.logicals[R["pdef"]] else 1
                self.check(d["flags"] & 3 == want, "%s room %08x Def %d (Logicals %d): logic flags %#x"
                           % (where, d["room"], R["pdef"], self.logicals[R["pdef"]], d["flags"]))
                self.hit("logic record on a preset room, Logicals %d (%s)" % (self.logicals[R["pdef"]], d["copy"]))
        elif tag == "LIP":
            if d["id"] == 27 and d["pd"] in self.l27:
                self.check(d["idx"] == self.l27[d["pd"]], "%s: level 27 LevelInit index %d, LevelLinkBuild wrote %d"
                           % (where, d["idx"], self.l27[d["pd"]]))
                self.hit("level 27 built with the LevelLinkBuild index")

    @staticmethod
    def act_of(lid):
        return 1 if lid < 40 else 2 if lid < 75 else 3 if lid < 103 else 4 if lid < 109 else 5

    def event(self, path, tag, d, levels, ps_level, ps_idx, lsr):
        L = levels.get(d.get("level"))
        where = "%s %s level %s" % (path, tag, (L.id if L else d.get("id")))
        if tag == "LC0":
            L = levels[d["level"]] = GenLevel(d)
            want = ((d["base"] + d["id"]) & MASK, INIT_HIGH)
            self.check(seed_t(d["seed"]) == want, "%s: create seed %s, model Init(base+id)" % (where, d["seed"]))
            L.seed = want
            self.check(self.data.drlgtype[L.id] == L.drlg, "%s: DrlgType %d, leveldefs %d" % (where, L.drlg, self.data.drlgtype[L.id]))
            self.hit("levels created (DrlgType %d)" % L.drlg)
        elif tag == "LC1":
            if L.drlg == 2:                      # sub_00667430_PresetLevelCreate
                files = self.files[self.prest_by_level[L.id]]
                if files != 0:
                    L.seed, idx = self.rng_range(L.seed, files)
                else:
                    idx = -1
                L.create_idx = idx
                self.check(d["idx"] == idx, "%s: create-time file index %s, model %d (Files %d)" % (where, d["idx"], idx, files))
                self.hit("preset level create: index drawn (Files %s)" % ("0 -> -1" if files == 0 else ">0"))
            self.check(seed_t(d["seed"]) == L.seed, "%s: seed after create %s, model %s" % (where, d["seed"], fmt(L.seed)))
        elif tag == "LI0":
            if L is None:
                L = levels[d["level"]] = GenLevel(d)
            want = ((d["base"] + d["id"]) & MASK, INIT_HIGH)
            self.check(seed_t(d["seed"]) == want, "%s: LevelInit re-seed %s, model Init(base+id)" % (where, d["seed"]))
            L.seed, L.rooms, L.inited, L.maze_list, L.rot = want, [], True, None, {}   # sub_006738C0 counters: per build
            if L.drlg == 2:
                L.init_idx = d["idx"]
                if L.create_idx is not None and d["idx"] != L.create_idx:
                    self.hit("preset level index changed after create (level %d)" % L.id)
                    self.check(L.id in (1, 27, 40), "%s: index %d at init, %d at create: only levels 1, 40 (link value) "
                               "and 27 (level-6 link draw) are overwritten" % (where, d["idx"], L.create_idx))
            self.hit("LevelInit (DrlgType %d)" % L.drlg)
        elif tag == "LI1":
            self.check(L.window is None, "%s: LevelInit ends inside an oracle window" % where)
            self.check(seed_t(d["seed"]) == L.seed, "%s: seed at LevelInit end %s, model %s" % (where, d["seed"], fmt(L.seed)))
            # maze levels: the maze generator's own rooms are freed after the preset conversion
            # (sub_0066C100), so the level keeps only the rooms PresetRoomsCreate made
            kept = [r for r in L.rooms if L.drlg != 1 or r["ret"] in (RET_RL_PRESET_SPLIT, RET_RL_PRESET_SINGLE)]
            self.check(d["nrooms"] == len(kept), "%s: %d rooms in the level, model %d (%d RL logged)"
                       % (where, d["nrooms"], len(kept), len(L.rooms)))
            self.order_checks(path, L)
            if getattr(L, "od_q", None) is not None:
                self.check(not L.od_q, "%s: %d modelled outdoor items not created (first %s)" % (where, len(L.od_q), L.od_q[:1]))
                L.od_q = None
            # the warp points this build will get (sub_006423D0 runs right after): the level's list is newest first;
            # an out room's flags are its grid0 cell, from the outdoor model (None without one)
            g0 = getattr(L, "od_g0", None)
            L.wp_rooms = [(r["room"], r["type"]) + tuple(r["rect"]) +
                          ((g0.get(tuple(r["rect"][:2])) if g0 is not None else None) if r["type"] == 1 else r["f28"],)
                          for r in reversed(kept)]
            xs, ys, unk = self.points_for(path, L.id, L.wp_rooms, getattr(L, "mz_diff", None), False)
            self.wp_by_level.setdefault(L.ptr, []).append((self.ln, L.id, xs, ys, unk))
        elif tag == "RC":
            if L.window is not None:
                self.hit("RoomCreate inside a generator window (%s; the maze model makes them)" % L.window if L.window == "maze" else "RoomCreate inside oracle window (%s)" % L.window)
                return
            self.check(seed_t(d["seed"]) == L.seed, "%s: seed before RoomCreate %s, model %s" % (where, d["seed"], fmt(L.seed)))
            L.rc_seed = L.seed
            L.seed = step(*L.seed)
            L.pending_rc = d["ret"]
            self.hit("RoomCreate modelled (one level draw)")
        elif tag == "RL":
            # plan 0038 batch H5e: a new DRLG room at this address. A room list kept for a freed room that had the
            # same address (an act freed when the player changed act) is not this room's.
            self.rlists.pop(d["room"], None)
            if L is None:
                if getattr(self, "rl_pred", None) is not None:
                    self.rl_pred.append((d["room"], None, None))
                return
            if L.window is None:
                self.check(seed_t(d["seed"]) == L.seed, "%s: seed at room link %s, model %s" % (where, d["seed"], fmt(L.seed)))
                lo = step(L.seed[0], INIT_HIGH)[0]
                self.check(d["r04"] == lo, "%s: room +0x04 %08x, model step(Init(level.lo)) %08x" % (where, d["r04"], lo))
                if getattr(self, "rl_pred", None) is not None:          # tools/monspawn.py: the model's +0x04
                    self.rl_pred.append((d["room"], lo, L.id))
            elif getattr(self, "rl_pred", None) is not None:
                self.rl_pred.append((d["room"], None, L.id))
            if d["ret"] == RET_RL_OUTROOM and L.window is None and getattr(L, "od_q", None) is not None:
                it = L.od_q.pop(0) if L.od_q else None
                self.check(it is not None and it[0] == "R" and [it[1], it[2]] == d["rect"][:2] and d["rect"][2:] == [8, 8],
                           "%s: out room at %s, model %s" % (where, d["rect"], it))
                self.hit("out rooms predicted (rect, creation order)")
            L.rooms.append(dict(d, window=L.window, prc=L.prc_n))
            if d["ret"] in (RET_RL_PRESET_SPLIT, RET_RL_PRESET_SINGLE) and getattr(L, "prc", None):
                self.room_inst[d["room"]] = (L.prc, d["ret"] == RET_RL_PRESET_SINGLE)
            # plan 0016: DRLG_RoomCreate seeds room +0x14 with step(Init(level lo)) (0x0066B44A..0x0066B477)
            self.room[d["room"]] = dict(d, seed=step(seed_t(d["seed"])[0], INIT_HIGH) if L.window is None else None)
        elif tag == "PIC":
            if not d["islevel"]:
                self.check(False, "%s: PresetInstanceCreate on a seed that is not the level's" % where)
                return
            self.check(seed_t(d["seed"]) == L.seed, "%s: seed before PresetInstanceCreate %s, model %s" % (where, d["seed"], fmt(L.seed)))
            files = self.files[d["def"]]
            self.check(files == d["files"], "%s: Files %d, table %d" % (where, d["files"], files))
            L.seed, idx = self.rng_range(L.seed, files)
            L.pic_idx = idx
            L.pic_ret = d["ret"]
            if d["ret"] == RET_PIC_OUTDOOR and getattr(L, "od_q", None) is not None:
                it = L.od_q.pop(0) if L.od_q else None
                self.check(it is not None and it[0] == "P" and (it[1], it[2], it[3]) == (d["def"], d["rect"][0], d["rect"][1]),
                           "%s: outdoor preset Def %d at %s, model %s" % (where, d["def"], d["rect"][:2], it))
                L.od_pic = it
                self.hit("outdoor preset anchors predicted (Def, position)")
            if d["ret"] == RET_PIC_MAZE:
                L.maze_pic.append(d["rect"])
            self.hit("PresetInstanceCreate %s (%s)" % ({RET_PIC_LEVEL: "preset level", RET_PIC_OUTDOOR: "outdoor cell",
                                                        RET_PIC_MAZE: "maze room"}.get(d["ret"], "%08x" % d["ret"]),
                                                       "draw" if files > 0 else "Files 0: no draw"))
        elif tag == "PICX":
            self.check(d["idx"] == L.pic_idx, "%s: drawn index %d, model %d" % (where, d["idx"], L.pic_idx))
            self.check(seed_t(d["seed"]) == L.seed, "%s: seed after PresetInstanceCreate %s, model %s" % (where, d["seed"], fmt(L.seed)))
            ps_level[d["ps"]] = L.ptr
            want = L.pic_idx
            if L.pic_ret == RET_PIC_LEVEL:       # sub_00668100: the level's index wins unless it is -1
                want = L.pic_idx if L.init_idx == -1 else L.init_idx
            ps_idx[d["ps"]] = want
            if L.pic_ret == RET_PIC_OUTDOOR and getattr(L, "od_pic", None) is not None:
                self.od_ps[d["ps"]] = L.od_pic
                L.od_pic = None
        elif tag == "PIO":
            it = self.od_ps.get(d["ps"])
            if it is None:
                ps_idx[d["ps"]] = d["idx"]
                self.check(False, "%s PIO: outdoor preset index %d with no modelled anchor" % (path, d["idx"]))
                return
            self.check(d["idx"] == it[4], "%s PIO: outdoor preset Def %d index %d (cell bits 16-19), model %d"
                       % (path, it[1], d["idx"], it[4]))
            ps_idx[d["ps"]] = it[4]
            self.hit("outdoor preset index predicted from the model's cell bits 16-19")
        elif tag == "MFR":
            L.mfr = d
        elif tag == "MFRX":
            m = L.mfr
            idx = ps_idx[m["ps"]]
            mq = getattr(L, "mz_queue", None)
            if mq:
                want = mq.pop(0)
                self.check(m["forced"] == want.idx and m["def"] == want.d, "%s: maze room Def %d forced index %d, model Def %d "
                           "index %d" % (where, m["def"], m["forced"], want.d, want.idx))
                self.hit("maze preset forced index predicted (%s)" % ("forced" if want.idx != -1 else "none"))
            if m["forced"] != -1:
                idx = m["forced"]
                self.hit("maze preset index forced by the maze room")
            else:
                base = MAZE_DEF_BASE.get(L.ltype)
                if base is not None and base < m["def"] < base + 16:
                    n = self.files[m["def"]]
                    if m["def"] not in L.rot:
                        L.seed, r = self.rng_range(L.seed, n)
                        L.rot[m["def"]] = r
                        self.hit("maze preset rotation: first use, RangeB(level seed, Files)")
                    L.rot[m["def"]] = int(math_fmod(L.rot[m["def"]] + 1, n))
                    idx = L.rot[m["def"]]
                    self.hit("maze preset rotation: (counter + 1) % Files")
                else:
                    self.hit("maze preset index: the PresetInstanceCreate draw")
            ps_idx[m["ps"]] = idx
            self.check(d["idx"] == idx, "%s: maze preset index %d, model %d" % (where, d["idx"], idx))
            self.check(seed_t(d["seed"]) == L.seed, "%s: seed after sub_006738C0 %s, model %s" % (where, d["seed"], fmt(L.seed)))
        elif tag == "PRC":
            self.check(seed_t(d["seed"]) == L.seed, "%s: seed at PresetRoomsCreate %s, model %s" % (where, d["seed"], fmt(L.seed)))
            want = ps_idx.get(d["ps"])
            self.check(d["idx"] == want, "%s: file index at PresetRoomsCreate %d, model %s" % (where, d["idx"], want))
            files = self.data.lvlprest[d["def"]].files
            cell = files[d["idx"]] if 0 <= d["idx"] < 6 else None
            self.check(cell is not None and d["file"] == LVLTYPES_PREFIX + cell.replace("/", "\\"),
                       "%s: loads %s, LvlPrest[%d].File%d = %s" % (where, d["file"], d["def"], d["idx"] + 1, cell))
            self.hit("preset file checked (Files %d, named %d)" % (self.files[d["def"]], sum(1 for f in files if f not in ("", "0"))))
            it = self.od_ps.pop(d["ps"], None)
            if it is not None:
                self.check(d["flags"] == it[5] and d["prect"][:2] == [it[2], it[3]],
                           "%s: outdoor preset Def %d flags %#x at %s, model grid0 %#x at %s"
                           % (where, d["def"], d["flags"], d["prect"][:2], it[5], it[2:4]))
                self.hit("outdoor preset flags predicted (grid0)%s" % (" non-zero" if it[5] else ""))
            L.prc = d
            L.prc_n += 1
            self.inst[d["ps"]] = {"def": d["def"], "idx": d["idx"], "cell": cell, "prect": d["prect"], "lid": L.id,
                                  "units": None, "pending": 1, "caller": None, "draws": []}
        elif tag == "PUR":
            lv = d["seedp"] - 0x1C4
            L = levels.get(lv)
            self.check(L is not None, "%s: PresetUnitDropRolls on a seed that is not a level's" % path)
            self.check(seed_t(d["seed"]) == L.seed, "%s level %d: seed into sub_00667620 %s, model %s" % (path, L.id, d["seed"], fmt(L.seed)))
            if not self.oracle:
                L.pur_out = self.rolls(self.inst[d["ps"]], L.seed, "level seed")
        elif tag == "PURX":
            L = levels[d["seedp"] - 0x1C4]
            out = seed_t(d["seed"])
            if self.oracle:
                self.hit("oracle sub_00667620 calls (level seed), %s" % ("drew" if out != L.seed else "no draw"))
            else:
                self.check(out == L.pur_out, "%s level %d: seed after sub_00667620 %s, model %s" % (path, L.id, d["seed"], fmt(L.pur_out)))
                out = L.pur_out
            L.seed = out
        elif tag == "MZ0":
            self.check(seed_t(d["seed"]) == L.seed, "%s: seed at the maze window start %s, model %s" % (where, d["seed"], fmt(L.seed)))
            L.window = "maze"
            L.mzd = []
            L.mz_model = None
            if not self.has_mza:                 # logs without drlg-maze.py: the act model gives every input
                self.maze_run(path, L, None)
        elif tag == "MZ1":
            L.window = None
            L.maze_list = d["rooms"]
            L.maze_pic = []
            self.maze_check(path, L, d)
        elif tag == "OD0":
            self.check(seed_t(d["seed"]) == L.seed, "%s: seed into the outdoor window %s, model %s" % (where, d["seed"], fmt(L.seed)))
            L.window = "outdoor"
            self.outdoor_run(path, L)
        elif tag == "OD1":
            L.window = None
            self.outdoor_end(path, L, d)
        elif tag == "LSR":
            lsr[d["room"]] = d
        elif tag == "LSRX":
            e = lsr.pop(d["room"])
            seed, mask = seed_t(e["seed"]), 0
            if e["stype"] != -1 and e["theme"] != -1:
                rec = next(i for i, x in enumerate(self.data.lvlsub) if x.type == e["stype"])
                i = 0
                while rec + i < len(self.data.lvlsub) and self.data.lvlsub[rec + i].type == e["stype"]:
                    seed = step(*seed)
                    r = seed[0] % 100
                    if r < self.data.lvlsub[rec + i].prob[e["theme"]]:
                        mask |= 1 << i
                    i += 1
                self.hit("LvlSubRoll modelled (%d records)" % i)
            self.check(d["mask"] == mask and seed_t(d["seed"]) == seed,
                       "%s LvlSubRoll room %08x: mask %#x seed %s, model %#x %s" % (path, d["room"], d["mask"], d["seed"], mask, fmt(seed)))

    # ------------------------------------------------------------------ plan 0026 Phase 2: the outdoor window
    def outdoor_run(self, path, L):
        """OD0: sub_00675360_OutdoorLevelBuild's act generator on the level seed (class Outdoor), with the level rect,
        links, adjacency list and outdoor flags from the act model. Its output is the queue of what
        sub_006750F0_OutdoorRoomsCreate makes after OD1 (preset anchors, out rooms, rows outer)."""
        where = "%s level %d" % (path, L.id)
        diff = self.diff if self.diff is not None else self.diff_hint
        L.od_diff = diff
        L.od, L.od_q, L.od_g0 = None, None, None
        self.od_last[L.id] = None
        A = self.act_for(LV[L.id]["act"], diff)
        O = Outdoor(A, L.id, Seed(*L.seed))
        O.seed.log = []
        try:
            O.run()
        except (Fatal, NotImplementedError) as e:
            self.check(False, "%s: outdoor model: %s" % (where, e))
            return
        L.od = O
        self.od_last[L.id] = O
        L.od_q = O.items()
        L.od_g0 = {(O.rect[0] + 8 * cx, O.rect[1] + 8 * cy): O.g0[cy][cx] for cy in range(O.ch) for cx in range(O.cw)}
        self.hit("outdoor windows modelled: level %d" % L.id)
        self.hit("outdoor windows modelled: act %d difficulty %d" % (LV[L.id]["act"] + 1, diff))
        for k, v in O.cov.items():
            self.hit("outdoor branch: %s" % k, v)

    def room_prep_event(self, path, tag, d):
        """RRESEED (type 1) and its first LSUB: sub_0067D2D0_OutRoomGridPrepare's grids before the first LvlSub pass
        (orientation and wall zero, floor 0x40002 on 8x8, Act I road tiles), from the latest outdoor model of the level."""
        r = d["room"]
        if tag == "RRESEED":
            if d.get("type") == 1 and "rect" in d:
                self.prep_rooms[r] = (d["level"], d["rect"], self.od_last.get(d["level"]))
            else:
                self.prep_rooms.pop(r, None)
            return
        e = self.prep_rooms.pop(r, None)
        if e is None:
            return
        lid, rect, O = e
        where = "%s level %d room %s" % (path, lid, rect)
        if O is None:
            self.check(False, "%s: out room with no outdoor model of its level" % where)
            return
        got = {k: Grid.from_log(d[k]).c for k in ("orient", "wall", "floor")}
        fl = [v for row in out_room_prep_floor(O, rect) for v in row]
        gw, gh = rect[2] + 1, rect[3] + 1
        # plan 0027: the prediction feeds the roomk passes (run_log(..., prep_pred)) in place of the logged grids
        self.prep_pred[self.ln] = {"orient": Grid(gw, gh, [0] * (gw * gh)), "wall": Grid(gw, gh, [0] * (gw * gh)),
                                   "floor": Grid(gw, gh, list(fl))}
        self.check(all(v == 0 for v in got["orient"]) and all(v == 0 for v in got["wall"]),
                   "%s: orientation or wall grid not zero at the first LvlSub pass" % where)
        bad = [i for i, (a, b) in enumerate(zip(got["floor"], fl)) if a != b]
        self.check(len(got["floor"]) == len(fl) and not bad,
                   "%s: floor grid at the first LvlSub pass, %d cells differ (first %s)" % (where, len(bad), bad[:1]))
        self.hit("out-room grids at the first LvlSub pass: rooms checked (act %d)" % (LV[lid]["act"] + 1))
        if any(v & 0x80 for v in fl):
            self.hit("out-room grids at the first LvlSub pass: rooms with road tiles")

    def outdoor_end(self, path, L, d):
        where = "%s level %d" % (path, L.id)
        O = getattr(L, "od", None)
        if O is None:
            L.seed = seed_t(d["seed"])
            return
        self.check(O.seed.fmt() == d["seed"], "%s: seed after the outdoor window %s, model %s" % (where, d["seed"], O.seed.fmt()))
        L.seed = (O.seed.lo, O.seed.hi)

    def outdoor_draws(self, path, d, levels):
        """ODD (tools/gdb/drlg-outdoor.py at OD1): every level-seed step of the window, in order."""
        L = levels.get(d["level"])
        O = getattr(L, "od", None) if L is not None else None
        where = "%s ODD level %s" % (path, d["id"])
        if O is None:
            self.check(False, "%s: no outdoor model for the logged draws" % where)
            return
        dl = d["lo"]
        self.check(dl == O.seed.log, "%s: level-seed draws in the outdoor window: %d logged, %d model, first diff at %s"
                   % (where, len(dl), len(O.seed.log), next((i for i, (a, b) in enumerate(zip(dl, O.seed.log)) if a != b),
                                                            min(len(dl), len(O.seed.log)))))
        self.hit("outdoor window level-seed draws checked one by one (ODD)", len(dl))

    def outdoor_grids(self, path, d, levels):
        """ODG (tools/gdb/drlg-outdoor.py at OD1): the def grid, grid0 and the cell grid, cell for cell."""
        L = levels.get(d["level"])
        O = getattr(L, "od", None) if L is not None else None
        where = "%s ODG level %s" % (path, d["id"])
        if O is None:
            self.check(False, "%s: no outdoor model for the logged grids" % where)
            return
        self.check([d["cw"], d["ch"]] == [O.cw, O.ch] and d["rect"] == list(O.rect),
                   "%s: grid %dx%d rect %s, model %dx%d %s" % (where, d["cw"], d["ch"], d["rect"], O.cw, O.ch, O.rect))
        self.check(d["oflags"] & ~0x60 == O.flags0 & ~0x60 and d["oflags"] == O.flags,
                   "%s: outdoor flags %#x, model %#x (link input %#x)" % (where, d["oflags"], O.flags, O.flags0))
        for name, grid in (("cells", O.cell), ("defs", O.defg), ("grid0", O.g0)):
            got = d[name]
            exp = [v for row in grid for v in row]
            bad = [i for i, (a, b) in enumerate(zip(got, exp)) if a != b]
            self.check(len(got) == len(exp) and not bad, "%s: %s grid differs in %d cells (first at (%s), log %s model %s)"
                       % (where, name, len(bad) + abs(len(got) - len(exp)), bad and (bad[0] % O.cw, bad[0] // O.cw),
                          bad and "%#x" % got[bad[0]], bad and "%#x" % exp[bad[0]]))
            self.hit("outdoor grids checked cell for cell (%s)" % name, len(exp))

    # ------------------------------------------------------------------ plan 0022 Phase 2: maze, links, warp points
    def maze_reset(self, path):
        head = open(path, errors="replace").readline()
        self.mapseed = int(head.split("seed=")[1].split()[0]) if "seed=" in head else None
        n = os.path.basename(path)
        # the d2run header names the steps file (plan 0048 Phase 2's logs, e.g. p2-s1-4851-ch1.log, carry the
        # difficulty there only); older logs carry it in the file name
        st = head.split("steps=")[1].split()[0] if "steps=" in head else ""
        n = os.path.basename(st) + " " + n
        self.diff_hint = 2 if "hell" in n else 1 if "nightmare" in n else 0
        self.diff = None
        with open(path, errors="replace") as f:
            self.has_mza = any(line.startswith("MZA ") for line in f)
        self.acts = {}              # (act index, difficulty) -> Act model
        self.lnk_n = {}             # act pointer -> LevelLinkBuild calls seen
        self.lnk_cur = {}           # act pointer -> (Act, Builder) of the call in progress
        self.lnks_logged = {}       # act index -> {level: (vis, warp)} from LNKS (Act III: logged input)
        self.room_inst = {}         # DRLG room -> (PRC line, single-room flag)
        self.od_ps = {}             # preset instance -> its modelled outdoor anchor ("P", Def, x, y, index, grid0)

    def act_for(self, acti, diff):
        key = (acti, diff)
        if key not in self.acts:
            A = Act(acti, self.mapseed, diff)
            try:
                act_links(A)
                A.modelled = True
            except NotImplementedError:
                A.modelled = False
            self.acts[key] = A
        return self.acts[key]

    def maze_inputs(self, L, levels, diff):
        lid = L.id
        acti = LV[lid]["act"]
        A = self.act_for(acti, diff)
        k27 = A.idx27
        if k27 is None:                          # no level-6 draw: level 27 keeps its create-time index
            k27 = next((x.create_idx for x in levels.values() if x.id == 27 and x.create_idx is not None), None)
        return dict(acti=acti, rect=A.level_rect(lid), tombs=A.tombs, l27=(k27, A.level_rect(27)) if acti == 0 else None,
                    l108=A.level_rect(108) if acti == 3 else None)

    def maze_run(self, path, L, mza):
        diff = mza["diff"] if mza else (self.diff if self.diff is not None else self.diff_hint)
        L.mz_diff = diff
        levels = self.cur_levels
        inp = self.maze_inputs(L, levels, diff)
        where = "%s level %d" % (path, L.id)
        if getattr(L, "mz_placed", None) is not None:
            # plan 0038 batch H5e: LevelInit rebuilding the same level object (LI0 with no LC0 in between) finds the
            # rect its previous window's placement wrote (MazeLevelPlace / the level 28 and 107 placements)
            if list(L.mz_placed) != list(inp["rect"]):
                # H5e review follow-up (a): count apart the rebuilds whose previous placement moved the level
                self.hit("maze input: rebuild of a level object, previous placement differs from the act rect, level %d"
                         % L.id)
            inp["rect"] = list(L.mz_placed)
            self.hit("maze input: rebuild of a level object, rect from its previous placement")
        if mza:
            self.check(mza["tomb94"] == inp["tombs"][0] or inp["acti"] != 1, "%s: act +0x094 %d, model %d" % (where, mza["tomb94"], inp["tombs"][0]))
            self.check(mza["tomb484"] == inp["tombs"][1] or inp["acti"] != 1, "%s: act +0x484 %d, model %d" % (where, mza["tomb484"], inp["tombs"][1]))
            self.check(mza["rect"] == inp["rect"], "%s: level rect %s, model %s" % (where, mza["rect"], inp["rect"]))
            self.check(mza["acti"] == inp["acti"], "%s: act index %d, model %d" % (where, mza["acti"], inp["acti"]))
            if L.id == 28:
                self.check([mza["l27"]["idx"], mza["l27"]["rect"]] == list(inp["l27"]), "%s: level 27 index/rect %s, model %s"
                           % (where, [mza["l27"]["idx"], mza["l27"]["rect"]], inp["l27"]))
                self.hit("maze input: level 27 index and rect predicted (Barracks)")
            if L.id == 107:
                self.check(mza["l108"]["rect"] == inp["l108"], "%s: level 108 rect %s, model %s" % (where, mza["l108"]["rect"], inp["l108"]))
                self.hit("maze input: level 108 rect predicted (River of Flame)")
            self.hit("maze inputs checked against MZA (act fields, rects)")
        ML = MLevel(L.id, Seed(*L.rc_seed), diff, inp["rect"], inp["tombs"], inp["acti"], inp["l27"], inp["l108"])
        M = Maze(ML)
        try:
            M.run()
        except Fatal as e:
            self.check(False, "%s: maze model fatal: %s" % (where, e))
            return
        L.mz_model = M
        self.check(M.mz0.lo == L.seed[0] and M.mz0.hi == L.seed[1], "%s: model seed after the first room %s, gen %s"
                   % (where, M.mz0.fmt(), fmt(L.seed)))

    def maze_check(self, path, L, d):
        where = "%s level %d" % (path, L.id)
        M = getattr(L, "mz_model", None)
        if M is None:
            self.check(False, "%s: maze window without a model run" % where)
            L.seed = seed_t(d["seed"])
            return
        ML = M.L
        got = [[R.x, R.y, R.w, R.h, R.d, R.idx] for R in ML.rooms]
        exp = [r[2:8] for r in d["rooms"]]
        self.check(got == exp, "%s: maze room list differs (%d logged, %d model; first diff %s)" % (where, len(exp), len(got),
                   next(((i, a, b) for i, (a, b) in enumerate(zip(got, exp)) if a != b), None)))
        self.check(ML.seed.fmt() == d["seed"], "%s: seed after the maze window %s, model %s" % (where, d["seed"], ML.seed.fmt()))
        if L.mzd:
            dl = [seed_t(x["seed"])[0] for x in L.mzd]
            self.check(dl == M.draws, "%s: level-seed draws in the window: %d logged, %d model, first diff at %s" % (where, len(dl),
                       len(M.draws), next((i for i, (a, b) in enumerate(zip(dl, M.draws)) if a != b), None)))
            self.hit("maze window level-seed draws checked one by one (MZD)", len(dl))
        self.hit("maze windows modelled: level type %d" % ML.lt)
        self.hit("maze windows modelled: difficulty %d" % ML.diff)
        for b in sorted(M.branches):
            self.hit("maze level-specific branch reached: %d" % b)
        L.seed = (ML.seed.lo, ML.seed.hi)
        L.mz_placed = list(ML.rect)
        L.mz_queue = list(ML.rooms)              # MazeLevelRooms walks the list newest first: one MFR per room
        L.mz_rects = {}

    def maze_event(self, path, tag, d, levels):
        self.cur_levels = levels
        if tag == "MZA":
            L = levels.get(d["level"])
            self.diff = d["diff"]
            if L is not None and L.window == "maze":
                self.maze_run(path, L, d)
        elif tag == "MZD":
            L = levels.get(d["level"])
            if L is not None and L.window == "maze":
                L.mzd.append(d)
        elif tag == "MZF":
            self.hit("maze rooms freed inside the window (probes, failed placements)")
        elif tag == "LNK0":
            self.diff = d["diff"]
            A = self.act_for(d["acti"], d["diff"])
            if not A.modelled:
                return
            n = next((k for k, b in enumerate(A.builds) if b[0] == d["table"]), None)
            if n is None:
                self.check(False, "%s: LevelLinkBuild table %#x of act %d is not in the model" % (path, d["table"], d["acti"]))
                return
            va, B, sin, sout = A.builds[n]
            self.check(d["table"] == va and d["seed"] == sin.fmt(), "%s: LevelLinkBuild %d of act %d: table %#x seed %s, model %#x %s"
                       % (path, n, d["acti"], d["table"], d["seed"], va, sin.fmt()))
            self.lnk_cur[d["act"]] = (A, va, B, sin, sout)
        elif tag == "LNKL":
            cur = self.lnk_cur.get(d["act"])
            if cur is None:
                return
            A, va, B, sin, sout = cur
            i = next(i for i, e in enumerate(B.t) if e[1] == d["id"])
            self.check(d["rect"] == B.rect[i], "%s: level %d rect %s, link model %s" % (path, d["id"], d["rect"], B.rect[i]))
            if d["id"] in (1, 40):
                self.check(d["idx"] == A.townidx[d["id"]], "%s: town %d preset index %s, model %s" % (path, d["id"], d["idx"],
                           A.townidx[d["id"]]))
                self.hit("link builder: town preset index predicted (level %d)" % d["id"])
            self.hit("link builder: level rects predicted (act %d)" % A.idx)
        elif tag == "LK27":
            cur = self.lnk_cur.get(d["act"])
            if cur is None:
                return
            A = cur[0]
            self.check(d["idx"] == A.idx27 and d["seed"] == cur[4].fmt(), "%s: level-27 index %d act seed %s, model %s %s"
                       % (path, d["idx"], d["seed"], A.idx27, cur[4].fmt()))
            self.hit("link builder: level-27 index draw on the act seed predicted")
        elif tag == "LNK1":
            cur = self.lnk_cur.pop(d["act"], None)
            if cur is None:
                return
            A, va, B, sin, sout = cur
            n = len(B.t)
            ok = (d["bseed"] == B.seed.fmt() and d["rects"][:n] == B.rect[:n] and d["dir"][:n] == B.dir[:n]
                  and d["dir0"][:n] == B.dir0[:n] and d["step"][:n] == B.flip[:n] and d["flip0"][:n] == B.flip0[:n]
                  and d["seed"] == sout.fmt())
            self.check(ok, "%s: LevelLinkBuild table %#x: seed copy %s rects %s dir %s, model %s %s %s" % (path, va, d["bseed"],
                       d["rects"][:n], d["dir"][:n], B.seed.fmt(), B.rect[:n], B.dir[:n]))
            self.hit("link builder: calls predicted (act %d), act-seed-copy draws %d" % (A.idx, B.seed.n))
        elif tag == "LNKS":
            got = {lv: (vis, warp) for lv, vis, warp in d["links"]}
            self.lnks_logged[d["acti"]] = got
            A = self.act_for(d["acti"], self.diff if self.diff is not None else self.diff_hint)
            if not A.modelled:
                self.hit("link override list: logged input (act %d)" % d["acti"])
                return
            model = {lv: (N.vis, N.warp) for lv, N in A.links.items()}
            self.check(got == model, "%s: act %d LevelLinks list differs: logged %s, model %s" % (path, d["acti"],
                       sorted(got.items()), sorted(model.items())))
            self.hit("link override list predicted (act %d, %d levels)" % (d["acti"], len(got)))
        elif tag == "ODD":
            self.outdoor_draws(path, d, levels)
        elif tag == "ODG":
            self.outdoor_grids(path, d, levels)
        elif tag == "LWP":
            self.warp_points(path, d, levels)
        elif tag == "WPR":
            self.warp_pair(path, d, levels)

    def warp_pair(self, path, d, levels):
        """sub_0066C220_WarpPairLink: source slot m names vis[m]; k = earlier slots naming the same level; the paired
        slot is the k-th slot of the destination that names the source back (rank, no draw); the paired room is the
        first room of the destination list (newest first) whose flags hold that slot's bit."""
        slv, dlv, m = d["slv"], d["dlv"], d["m"]
        diff = self.diff if self.diff is not None else self.diff_hint
        vs, vd = self.vis_ids(slv, diff), self.vis_ids(dlv, diff)
        j = (d["dmask"]).bit_length() - 5
        where = "%s WPR %d slot %d -> %d" % (path, slv, m, dlv)
        self.check(vs[m] == dlv, "%s: Vis%d is %d" % (where, m, vs[m]))
        k = sum(1 for i in range(m) if vs[i] == dlv)
        back = [i for i in range(8) if vd[i] == slv]
        want = back[k] if k < len(back) else None
        Ld = next((x for x in levels.values() if x.id == dlv and getattr(x, "wp_rooms", None)
                   and any(r[0] == d["dst"] for r in x.wp_rooms)), None)

        def first_room(jj):                      # WarpPairRoomFind: the first room of the list with the slot's bit
            for r in Ld.wp_rooms:
                f = self.room_flags(path, dlv, r)
                if f is not None and f & (0x10 << jj):
                    return r[0]
            return None
        if Ld is None:
            self.check(want == j, "%s: paired slot %d, model slot %s (rank %d of %s)" % (where, j, want, k, back))
            self.hit("warp pairing: destination build not in the log (slot by rank only)")
            return
        how = "rank %d" % k
        jm = want if want is not None and first_room(want) is not None else None
        if jm is None:                            # no room with the rank slot's bit: the first back slot that has one
            jm = next((i for i in back if first_room(i) is not None), None)
            how = "rank %d slot has no room, first back slot with a room" % k
        room = first_room(jm) if jm is not None else None
        self.check(jm == j and room == d["dst"], "%s: paired slot %d room %08x, model slot %s room %s (%s; back slots %s)"
                   % (where, j, d["dst"], jm, room and "%08x" % room, how, back))
        self.hit("warp pairing predicted: %s%s" % (how, ", repeated destination" if sum(1 for v in vs if v == dlv) > 1 else ""))

    def room_flags(self, path, lid, r):
        """Predicted warp/waypoint flags of one room of a build's list (None for an outdoor room)."""
        ptr, typ, x, y, w, h, lf = r
        inst = self.room_inst.get(ptr)
        if typ != 2 or inst is None:
            return None if lf is None else lf & 0x30FF0
        diff = self.diff if self.diff is not None else self.diff_hint
        warp, vis = self.warp_ids(lid, diff)[0], self.vis_ids(lid, diff)
        prc, single = inst
        base = prc["flags"] | sum(0x10 << m for m in range(8) if vis[m] and warp[m] == -1)
        return (base | self.warp_grid(prc, single).get((0, 0) if single else ((x - prc["prect"][0]) // 8,
                                                                            (y - prc["prect"][1]) // 8), 0)) & 0x30FF0

    def warp_ids(self, lid, diff):
        acti = LV[lid]["act"]
        A = self.act_for(acti, diff)
        if A.modelled:
            return A.warp(lid), "model"
        got = self.lnks_logged.get(acti, {})
        if lid in got:
            return got[lid][1], "logged"
        return LV[lid]["warp"], "Levels (no override node)"

    def vis_ids(self, lid, diff):
        acti = LV[lid]["act"]
        A = self.act_for(acti, diff)
        if A.modelled:
            return A.vis(lid)
        got = self.lnks_logged.get(acti, {})
        return got[lid][0] if lid in got else LV[lid]["vis"]

    def warp_grid(self, prc, single):
        """DRLG_PresetMapScan's room flags for one preset instance: warp-slot bits 0x10 << m from the wall cells of
        orientation 10/11 (m = bits 20-25 < 8 with sub 0 or 4 or bit 31) and 0x30000 for a waypoint object, per 8x8
        room cell of the instance (all in cell (0, 0) for a single-room instance), when the record's Scan is set."""
        key = (prc["def"], prc["idx"], single)
        if key in self._wgrid:
            return self._wgrid[key]
        grid = collections.Counter()
        rec = self._prest_raw[prc["def"]]
        scan = struct.unpack_from("<i", rec, 0x34)[0]
        if scan:
            cell = self.data.lvlprest[prc["def"]].files[prc["idx"]]
            P = self.data.preset_pristine(cell)
            cols = P["cols"]
            sx, sy = P["size"]
            for walls, orients in zip(P["walls"], P["orients"]):
                for y in range(sy):
                    for x in range(sx):
                        k = y * cols + x
                        if orients[k] not in (10, 11):
                            continue
                        c = walls[k]
                        m, sub = (c >> 20) & 0x3F, (c >> 8) & 0xFF
                        if m < 8 and (sub in (0, 4) or c & 0x80000000):
                            grid[(0, 0) if single else (x // 8, y // 8)] |= 0x10 << m
            if self.pu is None and self._pu is None:
                self._pu = PresetUnitData(self.data.root, self.data.exe)
            pu = self.pu or self._pu
            for u in pu.ds1(cell)["units"]:
                if u[0] == 2 and 0 <= u[1] < 0x23D and u[1] < len(self._subclass) and self._subclass[u[1]] & 0x40:
                    grid[(0, 0) if single else ((u[3] // 5) // 8, (u[4] // 5) // 8)] |= 0x30000
        self._wgrid[key] = grid
        return grid

    def points_for(self, path, lid, rooms, diff, check, g0=None):
        """sub_006423D0_LevelWarpPointsBuild on a room list (newest first): one point per room whose flags have 0x30000,
        or a warp-slot bit whose slot has a LevelWarpId other than -1; the room centre in sub-tiles. Preset rooms take
        their flags from DS1_PresetMapScan's model (checked against the logged flags when `check`); a room whose flags
        are None (an outdoor room before its grid0 flags) counts as unknown and adds no point."""
        where = "%s level %d" % (path, lid)
        if diff is None:
            diff = self.diff if self.diff is not None else self.diff_hint
        warp, src = self.warp_ids(lid, diff)
        vis = self.vis_ids(lid, diff)
        if check:
            self.hit("warp points: warp ids from %s" % src)
        xs, ys, unk = [], [], 0
        for ptr, typ, x, y, w, h, lf in rooms:
            inst = self.room_inst.get(ptr)
            if typ == 2 and inst is not None:
                prc, single = inst
                # PresetMapScan fills the instance's room-flag grid first: the PresetRoomsCreate flags, plus 0x10 << k
                # for every Vis slot k with LevelWarpId -1 (a walkable seam)
                base = prc["flags"] | sum(0x10 << m for m in range(8) if vis[m] and warp[m] == -1)
                pf = (base | self.warp_grid(prc, single).get((0, 0) if single else ((x - prc["prect"][0]) // 8,
                                                                                   (y - prc["prect"][1]) // 8), 0)) & 0x30FF0
                if check:
                    self.check(pf == lf & 0x30FF0, "%s: room %08x flags %#x (warp/waypoint bits), DS1 scan %#x"
                               % (where, ptr, lf & 0x30FF0, pf))
                    self.hit("warp cells: preset room flags predicted from the DS1 scan%s" % (" (warp or waypoint bits set)"
                                                                                              if pf & ~base else ""))
                flags = pf
            elif lf is None:
                unk += 1
                continue
            else:
                flags = lf & 0x30FF0
                if check and typ == 1 and g0 is not None:
                    # OutRoomCreate: room +0x28 = grid0 | 0x80000 (| 0x40000 on the client copy)
                    want = g0.get((x, y))
                    self.check(want is not None and want == lf & ~0xC0000 and lf & 0x80000, "%s: out room %08x at (%d, %d) "
                               "flags %#x, outdoor model grid0 %s | 0x80000" % (where, ptr, x, y, lf,
                                                                                want if want is None else "%#x" % want))
                    self.hit("warp cells: out room flags predicted from the outdoor model's grid0%s"
                             % ("" if not want else " (%s)" % ", ".join(n for n, m in (("warp slot", 0xFF0), ("shrine", 0xF000),
                                                                                      ("waypoint", 0x30000)) if want & m)))
                elif check:
                    self.hit("warp cells: room flags taken from the log (DRLG room type %d)" % typ)
            ok = bool(flags & 0x30000) or any(flags & (0x10 << m) and warp[m] != -1 for m in range(8))
            if check and not flags & 0x30000 and any(flags & (0x10 << m) and warp[m] == -1 for m in range(8)):
                self.hit("warp points: a room whose only warp-slot bits have LevelWarpId -1 (no point)")
            if ok:
                xs.append(5 * (x + tdiv(w, 2)))
                ys.append(5 * (y + tdiv(h, 2)))
        return xs, ys, unk

    def warp_points(self, path, d, levels):
        L = levels.get(d["level"])
        lid = d["id"]
        where = "%s level %d" % (path, lid)
        rooms = [tuple(r[:7]) for r in d["rooms"]]
        if L is not None and getattr(L, "wp_rooms", None) is not None:
            self.check([r[0] for r in rooms] == [r[0] for r in L.wp_rooms], "%s: level room list order at the warp-point "
                       "build differs from the RL order reversed" % where)
            self.hit("warp points: level room list = RL order reversed")
        xs, ys, unk = self.points_for(path, lid, rooms, getattr(L, "mz_diff", None), True,
                                      getattr(L, "od_g0", None) if L is not None else None)
        n = d["n"]
        k = min(n, 9)
        self.check(n == len(xs) and d["xs"][:k] == xs[:k] and d["ys"][:k] == ys[:k], "%s: warp points %d %s %s, model %d %s %s"
                   % (where, n, d["xs"][:k], d["ys"][:k], len(xs), xs, ys))
        out = sum(1 for r in rooms if r[1] == 1)
        self.hit("warp point lists predicted (%s)" % ("no outdoor rooms" if not out else "outdoor room flags from the outdoor model"
                                                      if getattr(L, "od_g0", None) is not None else "outdoor room flags from the log"))
        self.hit("warp point lists predicted: DrlgType %d, %s points" % (LV[lid]["drlg"], "no" if not n else "some"))

    def order_checks(self, path, L):
        """Room-creation order: preset 8x8 split rows outer; outdoor rows outer on the 8-cell grid;
        maze: sub_00673A60 visits the level's room list (newest first) in list order."""
        if L.maze_list is not None:
            want = [r[2:6] for r in L.maze_list]
            self.check(L.maze_pic == want, "%s level %d: maze rooms turned into presets in order %s, list %s"
                       % (path, L.id, L.maze_pic[:4], want[:4]))
            self.hit("maze levels: preset conversion in level-list order")
        runs = {}
        for r in L.rooms:
            if r["ret"] == RET_RL_PRESET_SPLIT:
                runs.setdefault(r["prc"], []).append((r["rect"][1], r["rect"][0]))
        for run in runs.values():
            self.check(run == sorted(run), "%s level %d: preset split rooms not created rows-then-columns" % (path, L.id))
        out = [r for r in L.rooms if r["window"] is None and r["ret"] == RET_RL_OUTROOM]
        keys = [(r["rect"][1], r["rect"][0]) for r in out]
        self.check(keys == sorted(keys), "%s level %d: outdoor rooms not created rows-then-columns" % (path, L.id))



# ====================================================================================================================
# Plan 0022 Phase 2: the act link builder (docs/findings/drlg/0007-warps.md § 3), the maze generator
# (docs/findings/drlg/0006-maze.md) and the warp points (drlg/0007 § 4). The act link builder has one
# implementation, here; tools/outdoor_replay.py imports it (plan 0026). load_links() fills the module tables.
# ====================================================================================================================
import collections  # noqa: E402
import csv  # noqa: E402

M32 = 0xFFFFFFFF
COV = collections.Counter()


class Fatal(Exception):
    """A game fatal error (or an unbounded loop) reached by the model."""


class Seed:
    """The LCG seed {lo, hi}: step() is RNG_Step, range() RNG_Range / RNG_RangeB (n < 1 (signed): 0, no step).
    `log`, when a list, receives every new lo (the maze window's level-seed draws)."""

    def __init__(s, lo, hi=INIT_HIGH):
        s.lo, s.hi = lo & M32, hi & M32
        s.n = 0
        s.log = None

    def copy(s):
        return Seed(s.lo, s.hi)

    def step(s):
        v = s.lo * 0x6AC690C5 + s.hi
        s.lo, s.hi = v & M32, (v >> 32) & M32
        s.n += 1
        if s.log is not None:
            s.log.append(s.lo)
        return s.lo

    def range(s, n):
        if n < 1:
            return 0
        lo = s.step()
        return lo & (n - 1) if n & (n - 1) == 0 else lo % n

    def fmt(s):
        return "%08x:%08x" % (s.lo, s.hi)


def tdiv(a, b):
    """C signed division (idiv / sar after the sign fix-up): truncation towards zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def _tsv(path):
    rows = list(csv.reader(open(path, encoding="latin1"), delimiter="\t"))
    return rows[0], rows[1:]


LV = {}            # level id -> Levels row (sizes per difficulty, offsets, DrlgType, LevelType, Act, Vis, Warp)
LVLMAZE = {}       # level id -> LvlMaze row (first match on Level, sub_0061F490_LvlMazeByLevel)
TABLE = {}         # link-table VA -> [(pick, level, anchor, anchor2)]
T1158, T1258, T1F7C = [], [], []
_LX = {"exe": None}


def _lx_read(va, n):
    return exe_read(_LX["exe"], va, n)


def _lx_ints(va, n):
    return list(struct.unpack("<%di" % n, _lx_read(va, 4 * n)))


def load_links(excel, exe):
    """Fill LV, LVLMAZE and the link tables from the excel directory (txt tables) and the pinned game.exe."""
    if LV and _LX["exe"] == exe:
        return
    _LX["exe"] = exe
    excel = excel.rstrip("/") + "/"
    h, rows = _tsv(excel + "levels.txt")
    LV.clear()
    for r in rows:
        if len(r) > 5 and r[h.index("Id")].strip().isdigit():
            def g(c, r=r):
                v = r[h.index(c)].strip()
                return int(v) if v else 0
            LV[g("Id")] = dict(sx=[g("SizeX"), g("SizeX(N)"), g("SizeX(H)")], sy=[g("SizeY"), g("SizeY(N)"), g("SizeY(H)")],
                               ox=g("OffsetX"), oy=g("OffsetY"), dep=g("Depend"), drlg=g("DrlgType"),
                               ltype=g("LevelType"), act=g("Act"),
                               vis=[g("Vis%d" % k) for k in range(8)],
                               warp=[(int(r[h.index("Warp%d" % k)]) if r[h.index("Warp%d" % k)].strip() else -1)
                                     for k in range(8)])
    h, rows = _tsv(excel + "lvlmaze.txt")
    LVLMAZE.clear()
    for r in rows:
        if len(r) > 7 and r[h.index("Level")].strip().lstrip("-").isdigit():
            g = lambda c, r=r: int(r[h.index(c)])      # noqa: E731
            LVLMAZE.setdefault(g("Level"), dict(rooms=[g("Rooms"), g("Rooms(N)"), g("Rooms(H)")], sx=g("SizeX"),
                                                sy=g("SizeY"), merge=g("Merge")))
    TABLE.clear()
    for va in (0x6F0750, 0x6F0840, 0x6F0930, 0x6F0A20, 0x6F0B10, 0x6F0C00, 0x6F0CF0, 0x6F0DE0, 0x6F0ED0):
        t = []
        for i in range(15):
            p, lv, a, b = struct.unpack("<Iiii", _lx_read(va + 16 * i, 16))
            if lv == 0:
                break
            t.append((p, lv, a, b))
        TABLE[va] = t
    T1158[:] = _lx_ints(0x6F1158, 64)
    T1258[:] = _lx_ints(0x6F1258, 90)
    T1F7C[:] = _lx_ints(0x6F1F7C, 8)
    _maze_tables()


# ---------------------------------------------------------------------------------------- act link builder

class LinkNode:   # act +0x90 LevelLinks
    def __init__(s, lid):
        s.vis = list(LV[lid]["vis"])
        s.warp = list(LV[lid]["warp"])


class Act:
    """DRLG_ActCreate's act seed and its draws (rng/seeds 3c), then the link state the builder writes."""

    def __init__(A, idx, mapseed, diff):
        A.idx, A.diff = idx, diff
        A.seed = Seed(mapseed)
        A.base = A.seed.step()
        A.tombs = (0, 0)
        if idx == 1:
            while True:
                a = A.seed.step() % 7
                b = A.seed.step() % 7
                if a != b:
                    break
            A.tombs = (a + 66, b + 66)      # act +0x094 (the true tomb), +0x484
        elif idx == 2:
            A.bit474 = A.seed.step() & 1    # act +0x474 (rng/0002), the Kurast gate side
        A.rect = {}           # level id -> [x, y, w, h] written by the builder
        A.links = {}          # level id -> LinkNode (the override list)
        A.oflags = collections.Counter()   # level id -> outdoor flags (OR-ed)
        A.adj = {}            # level id -> adjacency nodes (sorted insert)
        A.flag96d66c = 0
        A.idx27 = None        # level 27's preset index from the level-6 draw
        A.townidx = {}
        A.builds = []         # (table VA, Builder, act seed at entry, act seed at exit) per LevelLinkBuild

    def lvl(A, lid):
        if lid not in A.rect:
            A.rect[lid] = [0, 0, 0, 0]
        return A.rect[lid]

    def links_of(A, lid):
        if lid not in A.links:
            A.links[lid] = LinkNode(lid)
        return A.links[lid]

    def vis(A, lid):
        return A.links[lid].vis if lid in A.links else LV[lid]["vis"]

    def warp(A, lid):
        return A.links[lid].warp if lid in A.links else LV[lid]["warp"]

    def link_set(A, lid, dest, warp=-1):   # sub_00642920_LevelLinkSet(node, dest, warp, slot=-1)
        N = A.links_of(lid)
        for k in range(8):
            if N.vis[k] == dest:
                N.warp[k] = warp
                return
        for k in range(8):
            if N.vis[k] == 0 and N.warp[k] == -1:
                N.vis[k] = dest
                N.warp[k] = warp
                return
        raise Fatal("LevelLinkSet: no free slot (writes slot -1)")

    def level_rect(A, lid):
        """A level's rectangle: the builder's, else sub_00642D10_LevelRectSet's: SizeX/SizeY of the difficulty
        at OffsetX/OffsetY, relative to the Depend level's position when Depend is set."""
        if lid in A.rect:
            return list(A.rect[lid])
        v = LV[lid]
        bx = by = 0
        if v["dep"]:
            bx, by = A.level_rect(v["dep"])[:2]
        return [v["ox"] + bx, v["oy"] + by, v["sx"][A.diff], v["sy"][A.diff]]


class Builder:
    def __init__(B, act, table):
        B.act, B.t = act, table
        B.seed = act.seed.copy()
        B.rect = [[0, 0, 0, 0] for _ in range(15)]
        B.dir = [-1] * 15
        B.dir0 = [-1] * 15
        B.flip = [-1] * 15
        B.flip0 = [-1] * 15
        for i, (p, lv, a, b) in enumerate(table):
            B.rect[i][2] = LV[lv]["sx"][act.diff]
            B.rect[i][3] = LV[lv]["sy"][act.diff]
        B.i = 0


def _anchor(B):
    i = B.i
    if B.dir0[i] == -1:
        B.dir[i] = B.dir0[i]
    lv = B.t[i][1]
    B.rect[i][0] = LV[lv]["ox"]
    B.rect[i][1] = LV[lv]["oy"]
    return 1


def _p_rect(B):
    return B.rect[B.t[B.i][2]]


def _cyc(B, mod):
    """first call: draw (stored as dir0 and dir); later: next choice, 0 when back at dir0."""
    i = B.i
    if B.dir0[i] == -1:
        B.dir0[i] = B.seed.step() & (mod - 1)
        B.dir[i] = B.dir0[i]
        return True
    u = (B.dir[i] + 1) % mod
    if u == B.dir0[i]:
        return False
    B.dir[i] = u
    return True


def _p676150(B):
    if not _cyc(B, 4):
        return 0
    i = B.i
    P = _p_rect(B)
    R = B.rect[i]
    d = B.dir[i]
    if d == 0:
        R[0] = P[0] - 16; R[1] = P[3] + P[1]
    elif d == 1:
        R[0] = P[0] - R[2]; R[1] = P[1] - 16
    elif d == 2:
        R[0] = P[2] - R[2] + P[0] + 16; R[1] = P[1] - R[3]
    elif d == 3:
        R[0] = P[2] + P[0]; R[1] = P[3] - R[3] + 16 + P[1]
    return 1


def _p676280(B):
    if not _cyc(B, 8):
        return 0
    i = B.i
    P = _p_rect(B)
    R = B.rect[i]
    d = B.dir[i]
    if d == 0:
        R[0] = P[0] + (-8 - tdiv(R[2], 2)); R[1] = P[3] + P[1]
    elif d == 1:
        R[0] = P[0] + tdiv(R[2], 2) + 8; R[1] = P[3] + P[1]
    elif d == 2:
        R[0] = P[0] - R[2]; R[1] = P[1] - tdiv(R[3], 2) - 8
    elif d == 3:
        R[0] = P[0] - R[2]; R[1] = tdiv(R[3], 2) + 8 + P[1]
    elif d == 4:
        R[0] = P[0] + (-8 - tdiv(R[2], 2)); R[1] = P[1] - R[3]
    elif d == 5:
        R[0] = P[0] + tdiv(R[2], 2) + 8; R[1] = P[1] - R[3]
    elif d == 6:
        R[0] = P[2] + P[0]; R[1] = P[1] - tdiv(R[3], 2) - 8
    elif d == 7:
        R[0] = P[2] + P[0]; R[1] = tdiv(R[3], 2) + 8 + P[1]
    return 1


def _cyc_flip(B):
    i = B.i
    if B.dir0[i] == -1:
        B.dir0[i] = B.seed.step() & 3
        B.dir[i] = B.dir0[i]
        B.flip0[i] = B.seed.step() & 1
        B.flip[i] = B.flip0[i]
        return True
    u = (B.dir[i] + B.flip[i]) % 4
    f = (B.flip[i] + 1) % 2
    if u == B.dir0[i] and f == B.flip0[i]:
        return False
    B.dir[i] = u
    B.flip[i] = f
    return True


def _p676450(B):
    if not _cyc_flip(B):
        return 0
    i = B.i
    P = _p_rect(B)
    R = B.rect[i]
    d = B.dir[i]
    if B.flip[i] == 1:
        if d == 0:
            R[0] = P[0]; R[1] = P[3] + P[1]
        elif d == 1:
            R[0] = P[0] - R[2]; R[1] = P[1] + 8
        elif d == 2:
            R[0] = P[2] - R[2] + P[0]; R[1] = P[1] - R[3]
        elif d == 3:
            R[0] = P[2] + P[0]; R[1] = P[3] - R[3] - 8 + P[1]
    else:
        if d == 0:
            R[0] = P[2] - R[2] + P[0]; R[1] = P[3] + P[1]
        elif d == 1:
            R[0] = P[0] - R[2]; R[1] = P[3] - R[3] - 8 + P[1]
        elif d == 2:
            R[0] = P[0]; R[1] = P[1] - R[3]
        elif d == 3:
            R[0] = P[2] + P[0]; R[1] = P[1] + 8
    return 1


def _p676650(B):
    if not _cyc_flip(B):
        return 0
    i = B.i
    P = _p_rect(B)
    R = B.rect[i]
    d = B.dir[i]
    R[2] = 0x60 if d % 2 else 0x38
    R[3] = 0x38 if d % 2 else 0x60
    if B.flip[i] == 1:
        if d == 0:
            R[0] = P[0] - 16; R[1] = P[3] + P[1]
        elif d == 1:
            R[0] = P[0] - R[2]; R[1] = P[1] - 16
        elif d == 2:
            R[0] = P[2] - R[2] + P[0] + 16; R[1] = P[1] - R[3]
        elif d == 3:
            R[0] = P[2] + P[0]; R[1] = P[3] - R[3] + 16 + P[1]
    else:
        if d == 0:
            R[0] = P[2] - R[2] + P[0] + 16; R[1] = P[3] + P[1]
        elif d == 1:
            R[0] = P[0] - R[2]; R[1] = P[3] - R[3] + 16 + P[1]
        elif d == 2:
            R[0] = P[0] - 16; R[1] = P[1] - R[3]
        elif d == 3:
            R[0] = P[2] + P[0]; R[1] = P[1] - 16
    return 1


def _p6768c0(B):
    i = B.i
    B.dir0[i] = 0
    B.dir[i] = 0
    P = _p_rect(B)
    R = B.rect[i]
    R[0] = P[0]
    R[1] = P[3] + P[1]
    return 1


def _p6769a0(B):
    i = B.i
    if B.dir0[i] == -1:
        B.dir0[i] = (B.seed.step() & 1) + 1
        B.dir[i] = B.dir0[i]
    else:
        u = 2 - (B.dir[i] != 1)
        if u == B.dir0[i]:
            return 0
        B.dir[i] = u
    P = _p_rect(B)
    R = B.rect[i]
    if B.dir[i] == 1:
        R[0] = P[0] - R[2]; R[1] = P[1]
    else:   # 2
        R[0] = P[0]; R[1] = P[1] - R[3]
    return 1


def _p676ae0(B):
    if not _cyc(B, 8):
        return 0
    i = B.i
    P = _p_rect(B)
    R = B.rect[i]
    d = B.dir[i]
    if d in (0, 1):
        R[0] = P[0]; R[1] = P[3] + P[1]
    elif d in (2, 3):
        R[0] = P[0] - R[2]; R[1] = P[1]
    elif d in (4, 5):
        R[0] = P[0]; R[1] = P[1] - R[3]
    else:
        R[0] = P[2] + P[0]; R[1] = P[1]
    return 1


def _p676c00(B):
    i = B.i
    B.dir0[i] = 3
    B.dir[i] = 3
    P = _p_rect(B)
    R = B.rect[i]
    lo = B.seed.step()
    if lo & 1:
        R[0] = P[2] + P[0]; R[1] = P[3] - R[3] + 8 + P[1]
        B.act.flag96d66c = 0x800000
    else:
        R[0] = P[2] + P[0]; R[1] = P[1] - 8
        B.act.flag96d66c = 0x400000
    return 1


def _p67d830(B):
    i = B.i
    b = B.seed.step() & 1
    B.dir[i] = b
    B.dir0[i] = b
    R = B.rect[i]
    if b == 0:
        R[2], R[3] = 0x40, 0xA0
    else:
        R[2], R[3] = 0xA0, 0x40
    P = _p_rect(B)
    R[0] = P[0] - R[2]
    R[1] = P[3] - R[3] - 16 + P[1]
    return 1


def _p67d8e0(B):
    i = B.i
    b = B.seed.step() & 1
    B.dir[i] = b
    B.dir0[i] = b
    R = B.rect[i]
    if b == 0:
        R[2], R[3] = 0x40, 0xA0
    else:
        R[2], R[3] = 0xA0, 0x40
    lv = B.t[i][1]
    R[0] = LV[lv]["ox"]
    R[1] = LV[lv]["oy"]
    return 1


def _p67d980(B):
    i = B.i
    if B.dir0[i] == -1:
        B.dir0[i] = B.seed.step() & 1
        B.dir[i] = B.dir0[i]
    else:
        u = 1 if B.dir[i] == 0 else 0
        if u == B.dir0[i]:
            return 0
        B.dir[i] = u
    a = B.t[i][2]
    u3 = B.dir[i]
    u5 = B.dir[a]
    R = B.rect[i]
    if u3 == 0:
        R[2], R[3] = 0x40, 0xA0
    elif u3 == 1:
        R[2], R[3] = 0xA0, 0x40
    k = u3 + u5 * 2
    R[0] = T1F7C[2 * k] + B.rect[a][0]
    R[1] = T1F7C[2 * k + 1] + B.rect[a][1]
    return 1


PICK = {0x6760F0: _anchor, 0x676150: _p676150, 0x676280: _p676280, 0x676450: _p676450, 0x676650: _p676650,
        0x6768C0: _p6768c0, 0x6769A0: _p6769a0, 0x676AE0: _p676ae0, 0x676C00: _p676c00, 0x67D830: _p67d830,
        0x67D8E0: _p67d8e0, 0x67D980: _p67d980}


def gap_overlap(A, Bq):   # sub_0066B860_RectGapTest(A, B, 0) == 0
    gx = (Bq[0] - A[2] - A[0]) if A[0] < Bq[0] else (A[0] - Bq[2] - Bq[0])
    gy = (Bq[1] - A[3] - A[1]) if A[1] < Bq[1] else (A[1] - Bq[3] - Bq[1])
    return gx < 0 and gy < 0


def _chk_plain(B):
    i = B.i
    a = B.t[i][2]
    for j in range(i):
        if j != a and gap_overlap(B.rect[i], B.rect[j]):
            return 0
    return 1


def _raw_anchor(va, j):
    return struct.unpack("<i", _lx_read(va + 16 * j + 8, 4))[0]


def _chk1a(B):
    i = B.i
    a = B.t[i][2]
    if not _chk_plain(B):
        return 0
    lv = B.t[i][1]
    if lv == 1:
        k = B.dir[i] + (B.flip[i] + (B.dir[a] + B.flip[a] * 4) * 2) * 4
        COV["link rogue side check"] += 1
        return T1158[k]
    if lv == 17:
        for j in range(15):    # the check walks the 15-entry table bound
            aj = TABLE[0x6F0750][j][2] if j < len(TABLE[0x6F0750]) else _raw_anchor(0x6F0750, j)
            if j != i and aj == a and B.dir[i] == B.dir[j]:
                return 0
    return 1


def _chk1b(B):
    i = B.i
    if not _chk_plain(B):
        return 0
    if i != 0:
        R = B.rect[0]
        R2 = [R[0], R[1] - 200, R[2], R[3] + 200]   # rect[0].y -= 200, .h += 200 (0x00676F10..0x00676F1F)
        return 0 if gap_overlap(R2, B.rect[i]) else 1
    return 1


def link_build(A, va, check=None, after=None):
    """sub_006772C0_LevelLinkBuild: the backtracking layout on a copy of the act seed, then the per-level writes
    (rect, town index of levels 1 and 40, level 27's index drawn on the act seed itself at level 6, seams)."""
    t = TABLE[va]
    seed_in = A.seed.copy()
    B = Builder(A, t)
    i = 0
    guard = 0
    while i < len(t):
        guard += 1
        if guard > 100000:
            raise Fatal("link builder loop")
        B.i = i
        r = PICK[t[i][0]](B)
        if r == 0:
            B.dir[i] = B.dir0[i] = B.flip[i] = B.flip0[i] = -1
            i -= 1
            COV["link backtrack"] += 1
            if i < 0:
                raise Fatal("link builder backtracked past entry 0")
            continue
        if check is None or check(B):
            i += 1
        else:
            COV["link check reject"] += 1
    for i, (p, lv, a, b) in enumerate(t):
        A.rect[lv] = list(B.rect[i])
        if lv == 6:
            d = B.dir[i]
            if d == 1:
                A.idx27 = 2 - (A.seed.step() & 1)
            elif d == 3:
                A.idx27 = (~A.seed.step()) & 1
        if after:
            after(A, lv, B, i)
        if A.idx != 4:
            for anc in (a, b):
                if anc != -1:
                    al = t[anc][1]
                    A.link_set(lv, al)
                    A.link_set(al, lv)
    for i, (p, lv, a, b) in enumerate(t):
        if lv == 1:
            A.townidx[1] = B.dir[i]
        if lv == 40:
            A.townidx[40] = B.dir[i + 1]
    A.builds.append((va, B, seed_in, A.seed.copy()))
    return B


def outdoor_flags(A, lv, B, i):   # sub_00677180_LinkOutdoorFlags (Act I tables)
    if LV[lv]["drlg"] != 3:
        return
    d0 = B.dir[i]
    d1 = B.dir[i + 1] if i + 1 < 15 else -1
    for r in range(15):
        e = T1258[6 * r: 6 * r + 6]
        if (lv == e[0] or e[0] == 0) and lv != e[1] and lv != e[2] and d0 == e[3] and d1 == e[4]:
            A.oflags[lv] |= e[5]


def rect_adj_dir(Ar, Br):   # 0x00642240
    if Ar[0] > Br[0]:
        if Ar[0] == Br[0] + Br[2]:
            return 0
    elif Br[0] == Ar[0] + Ar[2]:
        return 2
    if Ar[1] > Br[1]:
        if Ar[1] == Br[1] + Br[3]:
            return 1
    elif Br[1] == Ar[1] + Ar[3]:
        return 3
    return -1


def touch(Ar, Br):   # 0x0066B880(A, B, -1)
    gx = (Br[0] - Ar[2] - Ar[0]) if Ar[0] <= Br[0] else (Ar[0] - Br[2] - Br[0])
    gy = (Br[1] - Ar[3] - Ar[1]) if Ar[1] <= Br[1] else (Ar[1] - Br[3] - Br[1])
    return (gx == 0 and gy <= -1) or (gy == 0 and gx <= -1)


def seams_by_touch(A, lo, hi):
    for a in range(lo, hi + 1):
        A.links_of(a)
        for b in range(lo, hi + 1):
            if a != b and touch(A.rect[a], A.rect[b]):
                A.link_set(a, b)


def adj_less(n, m):   # 0x0066B6A0: n before m?
    if m["side"] > n["side"]:
        return True
    if m["side"] != n["side"]:
        return False
    s = n["side"]
    if s == 0:
        return m["rect"][1] > n["rect"][1]
    if s == 1:
        return m["rect"][0] < n["rect"][0]
    if s == 2:
        return m["rect"][1] < n["rect"][1]
    if s == 3:
        return m["rect"][0] > n["rect"][0]
    return False


def adj_insert(lst, n):   # 0x0066B720 with its quirk (the head is compared only while alone)
    if not lst:
        lst.append(n)
        return
    if len(lst) == 1:
        if adj_less(n, lst[0]):
            lst.insert(0, n)
        else:
            lst.append(n)
        return
    for k in range(1, len(lst)):
        if adj_less(n, lst[k]):
            lst.insert(k, n)
            return
    lst.append(n)


def border_adj(A, lo, hi):   # sub_00677680_LevelBorderAdj
    for lv in range(lo, hi + 1):
        if lv not in LV or LV[lv]["drlg"] != 3:
            continue
        vis, warp = A.vis(lv), A.warp(lv)
        lst = A.adj.setdefault(lv, [])
        for k in range(8):
            if vis[k] and warp[k] == -1:
                nb = vis[k]
                side = rect_adj_dir(A.rect.get(lv, [0, 0, 0, 0]), A.rect.get(nb, [0, 0, 0, 0]))
                adj_insert(lst, dict(nbr=nb, side=side, preset=LV[nb]["drlg"] == 2,
                                     rect=list(A.rect.get(nb, [0, 0, 0, 0]))))


def act_links(A):
    """sub_00678AD0_ActLinkInit: the link tables of acts I, II, IV and V; Act III's jungle layout (act_links_a3)."""
    if A.idx == 0:
        link_build(A, 0x6F0750, _chk1a, outdoor_flags)
        A.seed_after_t1 = A.seed.copy()
        link_build(A, 0x6F0840, _chk1b, outdoor_flags)
        border_adj(A, 1, 17)
    elif A.idx == 1:
        link_build(A, 0x6F0930, _chk_plain)
        link_build(A, 0x6F0A20, _chk_plain)
        border_adj(A, 40, 46)
    elif A.idx == 3:
        link_build(A, 0x6F0C00, _chk_plain)
        link_build(A, 0x6F0CF0, _chk_plain)
        A.oflags[104] |= A.flag96d66c
        border_adj(A, 103, 106)
    elif A.idx == 4:
        link_build(A, 0x6F0DE0)
        link_build(A, 0x6F0ED0)
        seams_by_touch(A, 111, 112)
        border_adj(A, 111, 112)
        seams_by_touch(A, 110, 111)
        seams_by_touch(A, 109, 110)
        link_build(A, 0x6F0B10, _chk_plain)
    else:
        act_links_a3(A)


# ---------------------------------------------------------------------------------------- the maze generator

# sub_006709B0_MazeRoomDefFromExits: base Def per level type (+ exit mask)
MAZE_BASE = {3: 0x34, 4: 0x6C, 7: 0xA7, 8: 0xCD, 10: 0x101, 13: 0x12D, 17: 0x19D, 18: 0x1E1, 19: 0x1FD, 22: 0x2F1,
             24: 0x298, 25: 0x2C0, 28: 0x344, 34: 0x422}
# sub_006735F0_MazeThemes: the types with a theme pass
THEME_BASE = {3: 0x34, 4: 0x6C, 7: 0xA7, 8: 0xCD, 10: 0x101, 13: 0x12D, 17: 0x19D, 22: 0x2F1, 24: 0x298, 25: 0x2C0}
MZT = {}   # static tables read from game.exe


def _maze_tables():
    MZT["corner"] = {14: _lx_ints(0x6EF758, 3 * 16)[0::3], 15: _lx_ints(0x6EF75C, 3 * 16)[0::3],
                     23: _lx_ints(0x6EF760, 3 * 16)[0::3], 32: _lx_ints(0x6EF6D8, 2 * 16)[0::2],
                     35: _lx_ints(0x6EF6DC, 2 * 16)[0::2]}
    MZT["hell"] = _lx_ints(0x6EF828, 24)
    MZT["tee"] = {17: _lx_ints(0x6EF888, 8)[0::2], 34: _lx_ints(0x6EF88C, 8)[0::2]}


def mz_special(va):
    """One MazeSpecial entry {matchDef, def, idx, dir} (16 bytes)."""
    return tuple(_lx_ints(va, 4))


class MRoom:
    __slots__ = ("seed", "r04", "x", "y", "w", "h", "d", "idx", "lock", "adj", "k")

    def __init__(R, M):
        lo = M.L.seed.step()                     # DRLG_RoomCreate: one level-seed step
        R.seed = Seed(lo)
        R.r04 = R.seed.step()                    # room +0x14 = step(Init(level lo)), +0x04 its lo
        R.x = R.y = 0
        R.w, R.h = M.maze["sx"], M.maze["sy"]
        R.d, R.idx, R.lock, R.adj = 0, -1, False, []
        M.nroom += 1
        R.k = M.nroom

    def rect(R):
        return [R.x, R.y, R.w, R.h]


class MLevel:
    """The level fields the maze code reads: id, type, seed, room list (newest first), rect, difficulty, act."""

    def __init__(L, lid, seed, diff, rect, tombs=(0, 0), acti=None, l27=None, l108=None):
        L.id, L.lt, L.seed, L.diff = lid, LV[lid]["ltype"], seed, diff
        L.rect = list(rect)
        L.tombs = tombs
        L.acti = LV[lid]["act"] if acti is None else acti
        L.l27 = l27          # (preset index, rect) of level 27, for level 28
        L.l108 = l108        # rect of level 108, for level 107
        L.rooms = []


def _gap(A, B):
    gx = B.x - A.w - A.x if A.x < B.x else A.x - B.w - B.x
    gy = B.y - A.h - A.y if A.y < B.y else A.y - B.h - B.y
    return gx, gy


class Maze:
    """sub_00673B30_MazeLevelBuild from its first room to the per-room preset loop (the MZ0..MZ1 window)."""

    def __init__(M, L):
        M.L = L
        M.maze = LVLMAZE[L.id]
        M.nroom = 0
        M.branches = set()

    # --- primitives
    def place(M, R, P, d):                       # sub_00670880_MazeRoomPlace
        if d == 0:
            R.x, R.y = P.x - P.w, P.y
        elif d == 1:
            R.x, R.y = P.x, P.y - P.h
        elif d == 2:
            R.x, R.y = P.x + P.w, P.y
        elif d == 3:
            R.x, R.y = P.x, P.y + P.h
        elif d == 4:
            R.x, R.y = P.x - P.w, P.y - P.h
        elif d == 5:
            R.x, R.y = P.x + P.w, P.y - P.h
        elif d == 6:
            R.x, R.y = P.x + P.w, P.y + P.h
        elif d == 7:
            R.x, R.y = P.x - P.w, P.y + P.h
        for (o, _) in P.adj:
            gx, gy = _gap(R, o)
            if gx < 0 and gy < 0:
                return False
        for Q in M.L.rooms:                      # sub_0066B900_LevelRectFree: all but R and P
            if Q is R or Q is P:
                continue
            gx, gy = _gap(R, Q)
            if gx < 0 and gy < 0:
                return False
        return True

    @staticmethod
    def adj_add(A, B, d):                        # sub_0066B560_RoomAdjAdd
        if any(o is B for (o, _) in A.adj):
            return
        A.adj.insert(0, (B, d))

    def connect(M, A, B, d):                     # sub_0066B5E0_RoomAdjLink
        M.adj_add(A, B, d)
        M.adj_add(B, A, (d - 2) & 3)

    @staticmethod
    def adj_dir(A, B):                           # sub_00642240_RectAdjDir
        if B.x < A.x:
            if A.x == B.x + B.w:
                return 0
        elif B.x == A.x + A.w:
            return 2
        if B.y < A.y:
            if A.y == B.y + B.h:
                return 1
        elif B.y == A.y + A.h:
            return 3
        return -1

    def defcalc(M, R):                           # sub_006709B0_MazeRoomDefFromExits (unlock = 1)
        L = M.L
        m = 0
        for (_, d) in R.adj:
            m |= {0: 1, 1: 8, 2: 2, 3: 4}.get(d, 0)
        idx = -1
        lt = L.lt
        if lt in MAZE_BASE:
            v = MAZE_BASE[lt] + m
        elif lt == 33:
            v = m if M.maze["rooms"][L.diff] == 1 else 0x3EA + m
        elif lt in MZT["corner"]:
            v = MZT["corner"][lt][m]
            if lt == 15:
                if L.id == 52 and v == 0x169:
                    idx = 2
                if L.id == 54 and v in (0x169, 0x167):
                    idx = 3
            if lt == 23:
                if L.id == 84 and v == 0x296:
                    v = 0x298
                if L.id == 85 and v == 0x295:
                    v = 0x297
        else:
            raise Fatal("MazeRoomDefFromExits: level type %d" % lt)
        if v:
            R.d, R.idx, R.lock = v, idx, False

    def merge(M, R):                             # sub_00670C70_MazeRoomMerge (R not yet in the list)
        if R.lock:
            return
        mg = M.maze["merge"]
        for P in list(M.L.rooms):
            if P is R or P.lock:
                continue
            gx, gy = _gap(R, P)
            if gx < 1 and gy < 1 and gx != gy:
                if any(o is P for (o, _) in R.adj):
                    continue
                if P.seed.step() % 1000 < mg:
                    d = M.adj_dir(P, R)
                    if d != -1:
                        M.connect(P, R, d)
                        M.defcalc(P)

    def free(M, R):                              # DRLG_RoomFree: unlink both ways, out of the list
        for (o, _) in R.adj:
            o.adj = [(x, d) for (x, d) in o.adj if x is not R]
        R.adj = []
        if R in M.L.rooms:
            M.L.rooms.remove(R)

    def link(M, R):                              # sub_0066B970_LevelRoomLink: prepend
        M.L.rooms.insert(0, R)

    def grow(M, P, d, merge=True):
        R = MRoom(M)
        if not M.place(R, P, d):
            return None
        M.connect(P, R, d)
        if merge:
            M.merge(R)
        M.link(R)
        M.defcalc(P)
        M.defcalc(R)
        return R

    def add_fixed(M, P, d, dfn, idx, recalc):    # sub_00670DE0_MazeRoomAddFixed (no merge)
        R = MRoom(M)
        if not M.place(R, P, d):
            return None
        M.connect(P, R, d)
        M.link(R)
        if recalc:
            M.defcalc(P)
        R.lock, R.d, R.idx = True, dfn, idx
        return R

    def special(M, va, rot=None):                # sub_006724E0_MazeSpecialPlace
        match, nd, ni, d = mz_special(va)
        for R in M.L.rooms:
            if not R.lock and R.d == match:
                R.lock, R.d, R.idx = True, nd, ni
                break
        else:
            for P in list(M.L.rooms):            # sub_00670EB0_MazeSpecialAttach
                if P.lock:
                    continue
                R = MRoom(M)
                if M.place(R, P, d):
                    M.connect(P, R, d)
                    M.link(R)
                    M.defcalc(P)
                    R.lock, R.d, R.idx = True, nd, ni
                    break
            else:
                COV["maze special: no room took it"] += 1
        if rot is not None:
            rot[0] = (rot[0] + 1) & 3

    def tsp(M, base, rot):                       # the finishers: entry rot of the table at base, rotate
        M.special(base + 16 * rot[0], rot)

    def ring(M, n):                              # sub_00670F60_MazeRing
        cur = first = M.L.rooms[-1]
        for d, cnt in ((1, n - 1), (0, n - 1), (3, n - 1), (2, n - 2)):
            for _ in range(cnt):
                nxt = M.grow(cur, d)
                if nxt is None:
                    raise Fatal("MazeRing: placement failed (null parent)")
                cur = nxt
        M.connect(cur, first, 2)
        M.defcalc(cur)
        M.defcalc(first)

    def probe(M, R, d):                          # sub_00672340_MazeProbe
        if R.lock or any(dd == d for (_, dd) in R.adj):
            return False
        T = MRoom(M)
        if not M.place(T, R, d):
            return False
        M.connect(R, T, d)
        M.link(T)
        M.defcalc(T)
        M.free(T)
        return True

    def finder(M, d):                            # FindWest/North/East/South: 0x00672420/0x006723E0/0x00672460/0x006724A0
        key = {0: lambda R: R.x, 1: lambda R: R.y, 2: lambda R: -R.x, 3: lambda R: -R.y}[d]
        best = None
        for R in list(M.L.rooms):
            if best is None or key(R) < key(best):
                if M.probe(R, d):
                    best = R
        return best

    def growth(M):                               # sub_00671210_MazeGrow
        L = M.L
        tgt = M.maze["rooms"][L.diff]
        if L.id == L.tombs[0]:
            tgt *= 3
        if L.id == L.tombs[1]:
            tgt *= 2
        while len(L.rooms) < tgt:
            k = L.seed.range(len(L.rooms))
            P = L.rooms[k]
            d = P.seed.step() & 3
            if not P.lock:
                M.grow(P, d)

    def fill_around(M, dfn, exclude):            # sub_00671320_MazeFillAround
        for P in list(M.L.rooms):
            if P is exclude:
                continue
            for d in range(8):
                R = MRoom(M)
                if M.place(R, P, d):
                    M.connect(P, R, d)
                    M.link(R)
                    R.lock, R.d, R.idx = True, dfn, -1

    def themes(M):                               # sub_006735F0_MazeThemes
        L = M.L
        if L.lt not in THEME_BASE or L.id == 8:
            return
        base = THEME_BASE[L.lt]
        perm = list(range(15))
        s = L.seed.step() % 15
        want = max(2, len(L.rooms) // 5 + 1)
        tries = len(L.rooms) * 2
        for _ in range(15):
            a = L.seed.step() % 15
            b = L.seed.step() % 15
            perm[a], perm[b] = perm[b], perm[a]
        while want and tries:
            dv = base + perm[s]
            for R in L.rooms:
                if not R.lock and R.d == dv:
                    R.lock, R.d, R.idx = True, dv + 15, -1
                    want -= 1
                    break
            tries -= 1
            s = (s + 1) % 15

    def bounds(M):                               # sub_00642520_LevelRoomsBounds
        rs = M.L.rooms
        x0 = min(R.x for R in rs)
        y0 = min(R.y for R in rs)
        x1 = max(R.x + R.w for R in rs)
        y1 = max(R.y + R.h for R in rs)
        return x0, y0, x1, y1

    def shift(M, dx, dy):
        for R in M.L.rooms:
            R.x += dx
            R.y += dy

    # --- the window
    def run(M):
        L = M.L
        R0 = MRoom(M)                            # the first room (0x00673B3C), centred in the level rect
        R0.x = tdiv(L.rect[2] - R0.w, 2) + L.rect[0]
        R0.y = tdiv(L.rect[3] - R0.h, 2) + L.rect[1]
        M.link(R0)
        M.r0 = R0
        seed_mz0 = L.seed.copy()
        L.seed.log = []
        M.mz0 = seed_mz0
        lt, lid = L.lt, L.id
        rot = [0]

        def first_draw():
            rot[0] = L.seed.step() & 3

        if lt == 3:
            M.growth()
            first_draw()
            M.tsp(0x6EF8A8, rot)
            M.tsp(0x6EF8E8 if lid == 8 else 0x6EF928, rot)
            if lid == 9:
                M.tsp(0x6EF968, rot)
            if lid == 10:
                M.tsp(0x6EF9A8, rot)
        elif lt == 4:
            M.growth()
            first_draw()
            M.tsp(0x6EF9E8, rot)
            if lid == 18:
                M.tsp(0x6EFA28, rot)
            if lid in (19, 133):
                M.tsp(0x6EFAA8, rot)
            if 21 <= lid <= 24:
                M.tsp(0x6EFAE8, rot)
        elif lt == 7:
            M.ring(2)
            M.growth()
        elif lt == 8:
            M.ring(2)
            M.growth()
            first_draw()
            M.tsp(0x6EFB28, rot)
            if lid == 29:
                M.tsp(0x6EFBE8, rot)
            if lid == 30:
                M.tsp(0x6EFC28, rot)
            if lid == 31:
                M.tsp(0x6EFB68, rot)
            else:
                M.tsp(0x6EFBA8, rot)
        elif lt == 10:
            M.catacombs_start(lid == 34)
            M.growth()
            first_draw()
            M.tsp(0x6EFC68, rot)
            if lid == 35:
                M.tsp(0x6EFCA8, rot)
        elif lt == 13:
            M.ring(2)
            M.growth()
            M.sewer_a2()
        elif lt in (14, 15, 23):
            M.ring(2)
        elif lt == 17:
            if lid == 61:
                R0.lock, R0.d, R0.idx = True, 0x1E0, -1
                M.branches.add(61)
            else:
                M.tee(17)
                M.growth()
                M.tomb_finisher()
        elif lt == 18:
            M.ring(2)
            M.growth()
            first_draw()
            if lid == 64:
                M.special(0x6F00E8, rot)
                rot[0] = 3
                M.special(0x6F00D8, rot)
            else:
                M.tsp(0x6F0068, rot)
            M.tsp(0x6F0028, rot)
        elif lt == 19:
            M.arcane()
            first_draw()
            M.tsp(0x6F00F8, rot)
        elif lt == 22:
            M.ring(2)
            M.growth()
            first_draw()
            M.tsp(0x6F0238, rot)
            if lid == 101:
                M.tsp(0x6F0278, rot)
                M.tsp(0x6F02B8, rot)
            if lid == 100:
                M.tsp(0x6F02B8, rot)
        elif lt == 24:
            M.ring(2)
            M.growth()
            first_draw()
            M.tsp(0x6F0138, rot)
            M.tsp(0x6F0178, rot)
        elif lt == 25:
            if lid == 92:
                M.branches.add(92)
                M.ring(5)
                for want, new in ((0x2C5, 735), (0x2C6, 736), (0x2C9, 737), (0x2CA, 738)):
                    R = next((R for R in L.rooms if not R.lock and R.d == want), None)
                    if R is None:
                        raise Fatal("level 92: no ring room with Def %d" % want)
                    R.lock, R.d, R.idx = True, new, -1
            else:
                M.ring(2)
            M.growth()
            first_draw()
            M.tsp(0x6F01B8, rot)
            M.tsp(0x6F01F8, rot)
        elif lt == 28:
            M.growth()
        elif lt == 32:
            M.ring(2)
            r = L.seed.step() % 3
            rot[0] = r
            if lid != 124:
                M.tsp(0x6F02F8, rot)
            if lid == 123:
                if rot[0] == r:
                    raise Fatal("temple finisher: the rotation did not move")
                M.tsp(0x6F0328, rot)
        elif lt == 33:
            if lid in (114, 116, 119):
                M.branches.add(lid)
                if lid == 114:
                    R0.d = 1038 if L.seed.range(2) else 1039
                else:
                    R0.d = {116: 0x410, 119: 0x411}[lid]
                R0.lock, R0.idx = True, -1
            else:
                M.ring(2)
                M.growth()
                first_draw()
                M.tsp(0x6F0498, rot)
                M.tsp(0x6F04D8, rot)
                M.tsp(0x6F0518, rot)
                if lid == 115:
                    M.tsp(0x6F0558, rot)
                if lid in (113, 115, 118):
                    M.tsp(0x6F0598, rot)
        elif lt == 34:
            M.tee(34)
            M.growth()
            first_draw()
            M.tsp(0x6F0368, rot)
            if lid == 129:
                M.tsp(0x6F03A8, rot)
        elif lt == 35:
            M.hell_start()
        else:
            raise Fatal("MazeLevelBuild: level type %d" % lt)
        if lid == 28:
            M.branches.add(28)
            M.barracks()
        elif lid == 107:
            M.branches.add(107)
            M.river()
        else:
            x0, y0, x1, y1 = M.bounds()          # sub_00642590_MazeLevelPlace
            if L.rect[2] < x1 - x0 or L.rect[3] < y1 - y0:
                raise Fatal("MazeLevelPlace: rooms larger than the level rect")
            M.shift(L.rect[0] - x0, L.rect[1] - y0)
        M.themes()
        L.seed.log, M.draws = None, L.seed.log
        return L.rooms

    # --- start shapes and finishers
    def catacombs_start(M, four):                # sub_006714D0_MazeCatacombsStart
        R0 = M.r0
        if four:
            for d in (1, 2, 3, 0):
                M.grow(R0, d)
            R0.d = 0x122
        else:
            if M.L.seed.step() & 1 == 0:
                M.grow(R0, 1)
                M.grow(R0, 3)
                R0.d = 0x121
            else:
                M.grow(R0, 0)
                M.grow(R0, 2)
                R0.d = 0x120
        R0.lock, R0.idx = True, -1

    def tee(M, lt):                              # sub_006718C0_MazeTeeStart
        R0 = M.r0
        r = M.L.seed.step() & 3
        for _ in range(3):
            M.grow(R0, r)
            r = (r + 1) & 3
        R0.d, R0.lock, R0.idx = MZT["tee"][lt][r], True, -1

    def sewer_a2(M):                             # sub_00672810_MazeSpecialsSewerA2
        L = M.L
        a = (L.seed.step() & 1) * 2 | 1
        rot = [L.seed.step() & 3]
        lid = L.id
        if lid == 47:
            P = M.finder(1)
            R1 = M.grow(P, 1)
            R2 = M.grow(R1, 1)
            M.add_fixed(R2, 0, 0x14D, 0, True)
            P = M.finder(2)
            R1 = M.grow(P, 2)
            R2 = M.grow(R1, 2)
            dock = M.add_fixed(R2, a, 0x150, 0, True)
            R = MRoom(M)
            if M.place(R, dock, a):
                M.connect(dock, R, a)
                M.link(R)
                M.defcalc(R)
            M.tsp(0x6EFD28, rot)
        elif lid == 48:
            for t in (0x6EFCE8, 0x6EFD68, 0x6EFD28):
                M.tsp(t, rot)
        elif lid == 49:
            for t in (0x6EFCE8, 0x6EFDA8):
                M.tsp(t, rot)
        elif lid == 65:
            for t in (0x6EFCE8, 0x6EFDE8):
                M.tsp(t, rot)

    def tomb_finisher(M):                        # sub_00672BE0_MazeSpecialsTomb
        L = M.L
        R = None
        for R in L.rooms:
            if R.d > 0x1AC:
                break
        rot = [{0x1BC: 3, 0x1BD: 1, 0x1BE: 0, 0x1BF: 2}.get(R.d if R else -1, -1)]
        if rot[0] < 0:
            raise Fatal("tomb finisher: first room with Def > 428 is %s" % (R.d if R else None))
        lid = L.id
        if 55 <= lid <= 58:
            M.tsp(0x6EFE28, rot)
        if lid == 57:
            M.tsp(0x6EFE68, rot)
        if lid in (59, 61):
            M.tsp(0x6EFEA8, rot)
        if 66 <= lid <= 72 and lid != L.tombs[0]:
            M.tsp(0x6EFEA8, rot)
        if lid == 59:
            M.tsp(0x6EFEE8, rot)
        if lid == 60:
            M.tsp(0x6EFF28, rot)
        if lid in (59, 61):
            M.tsp(0x6EFF68, rot)
        if lid == L.tombs[0]:
            M.tsp(0x6EFFA8, rot)
        if lid == L.tombs[1]:
            M.tsp(0x6EFFE8, rot)

    def arcane(M):                               # sub_006719F0_MazeArcane
        L = M.L
        R0 = M.r0
        r = L.seed.step() & 3
        slots = []
        for a in range(4):
            d = a
            A1, A2, A3 = (a + 1) & 3, (a + 2) & 3, (a + 3) & 3
            s = []
            cur = R0
            for dd in (d, d, A3, d, d, d, d, A1):          # s0..s7
                cur = M.grow(cur, dd)
                s.append(cur)
            s7 = cur
            M.grow(s7, d)                                   # dead end, not recorded
            cur = M.grow(s7, A1)                            # s9
            s.append(cur)
            for dd in (A2, A2):                             # s10, s11
                cur = M.grow(cur, dd)
                s.append(cur)
            s11 = cur
            M.grow(s11, A3)                                 # dead end, not recorded
            cur = M.grow(s11, A2)                           # s13
            s.append(cur)
            cur = M.grow(cur, A2)                           # s14
            s.append(cur)
            slots.append(s)
        for a, s in enumerate(slots):
            for R in s:
                if R is not None:
                    R.idx = (a + r) & 3
        R0.idx = 4
        M.branches.add(74)

    def hell_start(M):                           # sub_00671430_MazeHellStart
        R0 = M.r0
        k = (R0.seed.step() & 3) * 2
        t = MZT["hell"]
        for e in (k, k + 1):
            dfn, d, idx = t[3 * e: 3 * e + 3]
            M.add_fixed(R0, d, dfn, idx, True)
        M.fill_around(0x344, None)

    def barracks(M):                             # sub_00673120_MazeBarracksPlace
        L = M.L
        k, r27 = L.l27
        P = M.finder({0: 2, 1: 3, 2: 0}[k])
        sx, sy = M.maze["sx"], M.maze["sy"]
        x27, y27, w27, h27 = r27
        if k == 0:
            R = M.add_fixed(P, 2, 0xA7, 0, True)
            dx = x27 - (R.x + sx)
            dy = y27 + tdiv(h27, 2) - R.y
        elif k == 1:
            R = M.add_fixed(P, 3, 0xA7, 1, True)
            dx = x27 + tdiv(w27, 2) - R.x - 6
            dy = y27 - (R.y + sy)
        elif k == 2:
            R = M.add_fixed(P, 0, 0xA7, 2, True)
            dx = x27 + w27 - R.x
            dy = y27 + tdiv(h27, 2) - R.y + 1
        else:
            raise Fatal("Barracks: level 27 index %s" % k)
        rot = [k]
        if L.seed.step() & 1:
            M.tsp(0x6F03E8, rot)
            M.tsp(0x6F0428, rot)
        else:
            M.tsp(0x6F0428, rot)
            M.tsp(0x6F03E8, rot)
        M.shift(dx, dy)
        x0, y0, x1, y1 = M.bounds()
        L.rect = [x0, y0, x1 - x0, y1 - y0]

    def river(M):                                # sub_00673320_MazeRiverOfFlame
        L = M.L
        if L.acti == 4:
            return
        P = M.finder(3)
        M.add_fixed(P, 3, 0x354, -1, True)
        P = M.finder(1)
        cur = M.add_fixed(P, 1, 0x357, -1, True)
        for _ in range(2):
            R = MRoom(M)
            if not M.place(R, cur, 1):
                cur = None
                raise Fatal("River of Flame: bridge placement failed (null parent)")
            M.connect(cur, R, 1)
            M.link(R)
            R.lock, R.d, R.idx = True, 0x358, -1
            cur = R
        x8, y8, w8, h8 = L.l108
        dy = h8 - cur.y + y8
        dx = 2 * cur.w - cur.x + x8
        r = L.seed.step() & 1
        M.special(0x6F0474 + 16 * r, None)
        M.fill_around(0x344, cur)
        M.shift(dx, dy)
        x0, y0, x1, y1 = M.bounds()
        L.rect = [x0, y0, x1 - x0, y1 - y0]


# ====================================================================================================================
# Plan 0026 Phase 2: the outdoor generators (docs/findings/drlg/0008-outdoor.md), the window OD0 -> OD1 of
# sub_00675360_OutdoorLevelBuild for every act, and Act III's link layout (sub_00677880_JungleLayout,
# sub_00678910_KurastStack on the act seed). One implementation, here: tools/outdoor_replay.py and
# tools/jungle_replay.py import it. load_outdoor() fills the tables (after load_links()).
# ====================================================================================================================

PREST = {}         # LvlPrest Def -> {files, sx, sy}
LVLSUB = []        # LvlSub records: type, file, BordType (+0x44), GridSize (+0x4C)
_SUBDS1 = {}
_OD = {"root": None}


def _odi(va, n):
    return _lx_ints(va, n)


def tmod(a, b):
    """C signed % (idiv)."""
    return a - tdiv(a, b) * b


def load_outdoor(root, exe):
    """The outdoor generators' data: LvlPrest sizes and Files, the LvlSub border records, the tables in game.exe."""
    excel = os.path.join(root, "data", "global", "excel")
    load_links(excel, exe)
    if _OD["root"] == (root, exe):
        return
    _OD["root"] = (root, exe)
    h, rows = _tsv(os.path.join(excel, "lvlprest.txt"))
    PREST.clear()
    for r in rows:
        if len(r) > 10 and r[h.index("Def")].strip().isdigit():
            PREST[int(r[h.index("Def")])] = dict(files=int(r[h.index("Files")]), sx=int(r[h.index("SizeX")]),
                                                 sy=int(r[h.index("SizeY")]))
    b = open(os.path.join(excel, "lvlsub.bin"), "rb").read()
    n = struct.unpack_from("<I", b)[0]
    LVLSUB[:] = []
    for i in range(n):
        rec = b[4 + i * 0x15C: 4 + (i + 1) * 0x15C]
        LVLSUB.append(dict(type=struct.unpack_from("<i", rec, 0)[0], file=rec[4:0x40].split(b"\0")[0].decode("latin-1"),
                           bord=struct.unpack_from("<i", rec, 0x44)[0], gs=struct.unpack_from("<i", rec, 0x4C)[0]))
    _SUBDS1.clear()
    g = globals()
    g["PROBE"] = _odi(0x6F05D8, 8)
    g["BDEFS"] = _odi(0x6F0620, 13 * 4)       # g_BorderDefs rows 0..12 x 4 styles (row 0 is another table's tail)
    g["BDEFS5"] = _odi(0x6F06F0, 12 * 2)      # Act V families
    g["DIRIDX"] = {(-1, 0): _odi(0x6F0FD0 - 4, 1)[0], (0, -1): _odi(0x6F0FD0 - 12, 1)[0], (1, 0): _odi(0x6F0FD0 + 4, 1)[0],
                   (0, 1): _odi(0x6F0FD0 + 12, 1)[0], (0, 0): _odi(0x6F0FD0, 1)[0]}
    g["CORNER"] = _odi(0x6F1088 - 40 * 4, 81)  # centre-based
    g["PAIR"] = _odi(0x6F112C, 10)
    g["NBR_DY"] = list(struct.unpack("<8b", _lx_read(0x6F060C, 8)))
    g["NBR_DX"] = list(struct.unpack("<8b", _lx_read(0x6F0614, 8)))
    g["SHRINE_FLAG"] = _odi(0x6F061C, 4)
    g["A5MAP"] = _odi(0x6F2038, 50)
    g["RIVER_T"] = _odi(0x6F2680, 32)
    g["HUB_DX"] = _odi(0x6F2810, 4)
    g["HUB_DY"] = _odi(0x6F2800, 4)
    g["T2840"] = list(_lx_read(0x6F2840, 16))
    g["DY4"] = list(struct.unpack("<4b", _lx_read(0x6F2850, 4)))
    g["DX4"] = list(struct.unpack("<4b", _lx_read(0x6F2854, 4)))
    g["T8"] = _odi(0x6F1518, 75)
    g["A5STEP"] = _odi(0x6F1FD8, 24)
    g["A5CAVE"] = _odi(0x6F1F9C, 15)
    g["A5TABLE"] = _odi(0x6F2100, 105)
    g["T_CLR"] = _odi(0x006F13BC, 16)          # clearing cell (exit mask >> 4) -> Def
    g["T_SIDE"] = _odi(0x006F13F0, 4 * 16)     # [def or mask][side 0x10,0x20,0x40,0x80] -> Def
    g["PERM"] = _odi(0x006F2328, 18)           # clearing file indices, 6 rows of 3
    g["CLR_OFF"] = _odi(0x006F2240, 0x54)      # per level id: clearing family offset
    g["JIT_DX"] = _odi(0x6F2820, 4)            # g_A1JitterDx (sub_00681240_A1PathJitter)
    g["JIT_DY"] = _odi(0x6F2830, 4)            # g_A1JitterDy
    g["ROAD_CODES"] = list(_lx_read(0x6F2700, 256))   # g_RoadCodes (sub_00680B10_RoadCodes)


def od_sub_ds1(i):
    """A LvlSub border record's DS1 (wall layer 0, floor layer 0, the groups with their variant count)."""
    if i not in _SUBDS1:
        s = LVLSUB[i]
        path = os.path.join(_OD["root"][0], "data", "global", "tiles", s["file"].replace("\\", "/").lower())
        f = ds1mod.parse(open(path, "rb").read())
        L = f["layers"]
        _SUBDS1[i] = dict(cols=f["cols"], wall=list(L["wall0"]) if f["wall_layers"] else None,
                          floor=list(L["floor0"]) if f["floor_layers"] else None,
                          groups=[(g["x"], g["y"], g["w"], g["h"], g["unk"] or 0) for g in f["groups"]])
    return _SUBDS1[i]


def od_act(lid):
    """DRLG_ActFromLevelId (0-based act index)."""
    return LV[lid]["act"]



def dir4(x, y, tx, ty):   # 0x00678CF0 / 0x00678B80, then /2
    dx, dy = tx - x, ty - y
    ax, ay = abs(dx), abs(dy)
    if ax >= 2 * ay:
        dy = -1 if dy < 0 else dy & 1
    elif ay >= 2 * ax:
        dx = -1 if dx < 0 else dx & 1
    dx = max(-2, min(2, dx)); dy = max(-2, min(2, dy))
    return tdiv(T8[3 * (5 * dx + dy + 12)], 2)


def grid_line_or(G, rect, a, b, n=2):
    """sub_0067C8E0_GridLineOp(G, a -> b, rect, value 1, op or, width n); G row-major lists, rect (x, y, w, h)."""
    gx, gy, gw, gh = rect
    x, y = a
    dx, dy = b[0] - x, b[1] - y
    sx, sy = (-1 if dx < 0 else 1), (-1 if dy < 0 else 1)
    adx, ady, err = abs(dx), abs(dy), 0

    def put(px, py):
        if gx <= px < gx + gw and gy <= py < gy + gh:
            G[py - gy][px - gx] |= 1
    if adx < ady:
        for k in range(n):
            put(x + k, y)
        for _ in range(ady):
            y += sy; err += adx
            if err > ady:
                x += sx; err -= ady
            for k in range(n):
                put(x + k, y)
    else:
        for k in range(n):
            put(x, y + k)
        for _ in range(adx):
            x += sx; err += ady
            if err > adx:
                y += sy; err -= adx
            for k in range(n):
                put(x, y + k)


def out_room_prep_floor(O, rect):
    """sub_0067D2D0_OutRoomGridPrepare up to its first LvlSub pass: the floor grid ((w+1) x (h+1), row-major);
    the orientation and wall grids are zero. Act I: sub_00680C80_OutRoomRoadGrid (rasterise O.polys,
    sub_00680B10_RoadCodes)."""
    x0, y0, w, h = rect
    F = [[0x40002 if (xx < 8 and yy < 8) else 0 for xx in range(w + 1)] for yy in range(h + 1)]
    if LV[O.lid]["act"] != 0:
        return F
    gr = (x0 - 1, y0 - 1, w + 3, h + 3)
    G = [[0] * (w + 3) for _ in range(h + 3)]
    for P in getattr(O, "polys", []):
        for a, b in zip(P, P[1:]):
            grid_line_or(G, gr, a, b)
    for X in range(1, w + 2):
        for Y in range(h + 1, 0, -1):
            if not G[Y][X]:
                continue
            m = ((G[Y - 1][X + 1] != 0) << 7 | (G[Y][X + 1] != 0) << 6 | (G[Y + 1][X + 1] != 0) << 5 |
                 (G[Y - 1][X] != 0) << 4 | (G[Y + 1][X] != 0) << 3 | (G[Y - 1][X - 1] != 0) << 2 |
                 (G[Y][X - 1] != 0) << 1 | (G[Y + 1][X - 1] != 0))
            if m and ROAD_CODES[m]:
                F[Y - 1][X - 1] = (ROAD_CODES[m] << 8) | 0x82
    return F


class V:
    __slots__ = ("x", "y", "type", "flags", "next")

    def __init__(s, x, y, t=0):
        s.x, s.y, s.type, s.flags, s.next = x, y, t, 0, None


def sgn(z):
    return -1 if z < 0 else 1 if z > 0 else 0


def e2(z):
    return z - 2 if z < 0 else z + 2 if z > 0 else 0


class Outdoor:
    def __init__(O, A, lid, seed):
        O.A, O.lid, O.seed = A, lid, seed
        O.rect = list(A.rect[lid])
        O.cw, O.ch = tdiv(O.rect[2], 8), tdiv(O.rect[3], 8)
        O.cell = [[0] * O.cw for _ in range(O.ch)]
        O.defg = [[0] * O.cw for _ in range(O.ch)]
        O.g0 = [[0] * O.cw for _ in range(O.ch)]
        O.rot = {}
        O.flags = O.flags0 = A.oflags[lid]
        O.cov = collections.Counter()
        O.adj = A.adj.get(lid, [])
        O.act = od_act(lid)
        O.ltype = LV[lid]["ltype"]

    def hit(O, what, n=1):
        O.cov[what] += n
        COV[what] += n

    # ---- grids
    def inb(O, x, y):
        return 0 <= x < O.cw and 0 <= y < O.ch

    def rotation(O, d):
        if d not in O.rot:
            n = PREST[d]["files"]
            O.rot[d] = [n, O.seed.range(n)]
            O.hit("rotation first use", 1)
        r = O.rot[d]
        if r[0] == 0:
            raise Fatal("rotation of def %d with Files 0 (idiv by zero)" % d)
        r[1] = tmod(r[1] + 1, r[0])
        return r[1]

    def place(O, x, y, d, idx, flag=0):   # 0x006743C0
        P = PREST[d]
        w, h = tdiv(P["sx"], 8), tdiv(P["sy"], 8)
        if idx == -1:
            idx = O.rotation(d)
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                c = (O.cell[yy][xx] & ~0xF0000) | ((idx << 16) & M32) | 0x200
                if flag and (4 <= d <= 15 or 364 <= d <= 375):
                    c |= 1
                O.cell[yy][xx] = c
                O.defg[yy][xx] = 0
        O.defg[y][x] = d

    def fits(O, x, y, d, pad=0, sides=0):   # 0x00674230
        if d == 0:
            w = h = 1
        else:
            P = PREST[d]; w, h = tdiv(P["sx"], 8), tdiv(P["sy"], 8)
        if pad:
            if sides & 1: y -= pad; h += pad
            if sides & 2: w += pad
            if sides & 4: h += pad
            if sides & 8: x -= pad; w += pad
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if not O.inb(xx, yy) or O.cell[yy][xx] & 0x1B81:
                    return False
        return True

    def shuffle(O, w, h):
        n = w * h
        a = [(i % w, i // w) for i in range(n)]
        for _ in range(n):
            u = O.seed.range(n); v = O.seed.range(n)
            a[u], a[v] = a[v], a[u]
        return a

    def place_random(O, d, idx=-1, pad=0, sides=0xF):   # 0x00674730
        N = (O.cw - 2) * (O.ch - 2)
        if N <= 0:
            return 0
        for (x, y) in O.shuffle(O.cw - 2, O.ch - 2):
            if O.fits(x + 1, y + 1, d, pad, sides):
                O.place(x + 1, y + 1, d, idx, 0)
                O.hit("PlaceRandom placed", 1)
                return 1
        O.hit("PlaceRandom failed", 1)
        return 0

    def place_near(O, d, idx=-1):   # 0x00674920
        N = (O.cw - 2) * (O.ch - 2)
        if N <= 0:
            return 0
        for (x, y) in O.shuffle(O.cw - 2, O.ch - 2):
            if O.cell[y + 1][x + 1] & 0x80:
                for k in range(8):
                    X, Y = x + 1 + NBR_DX[k], y + 1 + NBR_DY[k]
                    if O.fits(X, Y, d, 0, 0xF):
                        O.place(X, Y, d, idx, 0)
                        O.hit("PlaceNear placed", 1)
                        return 1
        O.hit("PlaceNear fallback", 1)
        return O.place_random(d, idx, 0, 0xF)

    def place_far(O, rect, d, idx, pad, sides):   # 0x006744F0
        W, H = O.cw - 2, O.ch - 2
        ox = O.seed.range(W); oy = O.seed.range(H)
        tx = rect[0] + tdiv(rect[2], 2); ty = rect[1] + tdiv(rect[3], 2)
        best = 0; bx = by = -1
        for r in range(H + 1):
            y = tmod(r + oy, H) + 1
            for c in range(W + 1):
                x = tmod(c + ox, W) + 1
                if O.fits(x, y, d, pad, sides):
                    a = abs(8 * x + O.rect[0] + 4 - tx); b = abs(8 * y + O.rect[1] + 4 - ty)
                    dd = tdiv(b + 2 * a if a > b else a + 2 * b, 2)
                    if dd > best:
                        best, bx, by = dd, x, y
        if bx != -1 and by != -1:
            O.place(bx, by, d, idx, 0)
            return 1
        return 0

    # ---- vertex ring
    def ring_build(O):
        R = O.rect
        x, y, w, h = R[0], R[1], R[2] - 1, R[3] - 1
        v0, v1, v2, v3 = V(x, y + h), V(x, y), V(x + w, y), V(x + w, y + h)
        v0.next, v1.next, v2.next, v3.next = v1, v2, v3, v0
        for n in O.adj:   # 0x0067CE20, node list order
            r = list(n["rect"]); r[2] -= 1; r[3] -= 1
            side = n["side"]
            if side == 0: p, vert, c, a, b, s, e = v0, True, -1, r[1] + r[3], r[1], v0.y, v1.y
            elif side == 1: p, vert, c, a, b, s, e = v1, False, 1, r[0], r[0] + r[2], v1.x, v2.x
            elif side == 2: p, vert, c, a, b, s, e = v2, True, 1, r[1], r[1] + r[3], v2.y, v3.y
            elif side == 3: p, vert, c, a, b, s, e = v3, False, -1, r[0] + r[2], r[0], v3.x, v0.x
            else:
                raise Fatal("adjacency side %d" % side)

            def ins(p, coord):
                q = V(p.x if vert else coord, coord if vert else p.y)
                q.next = p.next; p.next = q
                return q
            if a * c <= s * c:
                if s * c > b * c:
                    continue
            else:
                if a * c > e * c:
                    continue
                p = ins(p, a)
            p.flags |= 1
            if n["preset"]:
                p.flags |= 2
            if b * c < e * c:
                ins(p, b)
            O.hit("ring seam side %d" % side, 1)
        v = v0
        while True:
            v.x -= O.rect[0]; v.y -= O.rect[1]
            v = v.next
            if v is v0:
                break
        # 0x00675080: to cells, merge equal consecutive vertices
        head = v0
        v = head
        while True:
            v.x, v.y = tdiv(v.x, 8), tdiv(v.y, 8)
            v = v.next
            if v is head:
                break
        v = head
        while True:
            n = v.next
            if v.x == n.x and v.y == n.y:
                if n is head:
                    head = v
                v.next = n.next; v.flags |= n.flags; v.type = n.type
                O.hit("ring merge", 1)
            v = v.next
            if v is head:
                break
        O.ring = head

    def ring_list(O):
        out = []; v = O.ring
        while True:
            out.append(v); v = v.next
            if v is O.ring:
                return out

    def seam_warp_flag(O, v):   # 0x00674040
        x, y, cw, ch = v.x, v.y, O.cw, O.ch
        if x == 0:
            side = 1 if y == 0 else 0
        elif y == 0:
            side = (x == cw - 1) + 1
        elif x == cw - 1:
            side = (y == ch - 1) + 2
        elif y == ch - 1:
            side = 3
        else:
            return 0
        px = PROBE[2 * side] + 8 * x + O.rect[0]; py = PROBE[2 * side + 1] + 8 * y + O.rect[1]
        for n in O.adj:
            r = n["rect"]
            if n["side"] == side and r[0] <= px < r[0] + r[2] and r[1] <= py < r[1] + r[3]:
                vis = O.A.vis(O.lid)
                for k in range(8):
                    if vis[k] == n["nbr"]:
                        return 0x10 << k
                return 0
        return 0

    def seg_cells(O, v):
        n = v.next
        if v.x == n.x:
            if v.y == n.y:
                return [(v.x, v.y)]
            a, b = sorted((v.y, n.y))
            return [(v.x, y) for y in range(a, b + 1)]
        a, b = sorted((v.x, n.x))
        return [(x, v.y) for x in range(a, b + 1)]

    def seam_mark(O):   # 0x00675770
        for v in O.ring_list():
            if v.flags & 1:
                f = O.seam_warp_flag(v)
                cv = 3 if v.type else 1
                for (x, y) in O.seg_cells(v):
                    if O.inb(x, y):
                        O.g0[y][x] |= f
                        O.cell[y][x] |= cv
                    else:
                        raise Fatal("seam cell out of grid")

    def style(O, t):
        lt = O.ltype
        if lt == 2: return 1 if t == 0 else 0
        if lt == 16: return 2
        if lt == 27: return 3
        if lt == 31: return 4 + (O.lid == 117)
        return -1

    def border_build(O):   # 0x00675850
        for v in O.ring_list():
            n = v.next
            dx, dy = sgn(n.x - v.x), sgn(n.y - v.y)
            dx2, dy2 = sgn(n.next.x - n.x), sgn(n.next.y - n.y)
            ax, ay = abs(dx), abs(dy)
            ln = abs(v.x - n.x) if ax else abs(v.y - n.y)
            cv = 3 if v.type else 1
            s = O.style(v.type)
            di = DIRIDX[(dx, dy)]
            d = BDEFS[4 * (1 + di) + s] if s < 4 else BDEFS5[(s - 4) + 2 * di]
            if not (v.flags & 2):
                x, y = v.x, v.y
                while (x, y) != (n.x, n.y):
                    y += dy; x += dx
                    O.place(x, y, d, -1, 0)
                    O.cell[y][x] |= cv
            if (v.flags & 1) and not (v.flags & 2):
                mx = min(v.x, n.x) + tdiv(ln * ax, 2); my = min(v.y, n.y) + tdiv(ln * ay, 2)
                if O.act in (0, 4, 3):
                    val = 0x40400 if (O.lid == 17 and O.act in (0, 4)) else 0x30400
                    O.cell[my][mx] = (O.cell[my][mx] & ~0xF0000) | val
                    O.hit("seam opening", 1)
                elif O.act == 1:
                    k = dx + 2 * dy + 2
                    O.place(mx, my, PAIR[2 * k], -1, 0)
                    O.place(mx + ax, my + ay, PAIR[2 * k + 1], -1, 0)
                    O.hit("seam opening (Act II pair)", 1)
            t = v.type if v.type else n.type
            if t:
                cv |= 2
            s = O.style(t)
            a = e2(dx) if v.flags & 2 else e2(2 * dx)
            b = (e2(dx2) + dy2) if n.flags & 2 else (e2(2 * dx2) + 2 * dy2)
            c = dy if v.flags & 2 else 2 * dy
            k = CORNER[40 + a + 9 * b + c]
            if k == -1:
                continue
            cd = BDEFS[s + 4 * k] if s < 4 else BDEFS5[(s - 6) + 2 * k]
            if cd == 0x13:
                cd = (0x13 + (n.type != 1)) if v.type == 1 else 0x15
            elif cd == 0:
                continue
            O.place(n.x, n.y, cd, -1, 0)
            O.cell[n.y][n.x] |= cv
        O.corner_flood()

    def corner_flood(O):   # 0x00675670
        for (xf, yf, dx, dy) in ((0, 0, 1, 1), (1, 0, -1, 1), (0, 1, 1, -1), (1, 1, -1, -1)):
            x0 = O.cw - 1 if xf else 0
            y = O.ch - 1 if yf else 0
            while not (O.cell[y][x0] & 1):
                x = x0
                while not (O.cell[y][x] & 1):
                    O.cell[y][x] |= 0x100
                    x += dx
                y += dy

    # ---- tag-2 LvlSub border substitutions (0x006752A0 -> 0x00670750 -> 0x0066F990 -> 0x0066F690)
    def border_sub(O, typ, base, act5=False):
        ctx = dict(type=typ, base=base, wild=-1, act5=act5)
        i = next(k for k, s in enumerate(LVLSUB) if s["type"] == typ)
        while i < len(LVLSUB) and LVLSUB[i]["type"] == typ:
            O.bsub_record(i, ctx)
            i += 1

    def bsub_record(O, ri, ctx):
        rec = LVLSUB[ri]; S = od_sub_ds1(ri); G = S["groups"]
        if not G:
            return
        if ctx["wild"] == -1:
            ctx["wild"] = 62
        s = O.seed.range(len(G)) if rec["bord"] == 0 else 0
        for i in range(len(G)):
            ok = O.bsub_group(ctx, rec, S, G[(s + i) % len(G)])
            if ok and rec["bord"] == 0:
                return

    def bsub_group(O, ctx, rec, S, g):
        GS = rec["gs"]
        off = -1 if (ctx["type"] == 1 and (O.flags & 0xC)) else 1
        nx = O.cw - g[2] * GS + off; ny = O.ch - g[3] * GS + 1
        N = nx * ny
        if N == 0:
            return 0
        if N < 0:
            O.hit("border sub N < 0", 1)
            return 0
        skip22 = ctx["type"] == 1 and 2 <= O.lid <= 7 and nx < 6 and ny < 6
        lst = [(i % nx, i // nx) for i in range(N)]
        for _ in range(N):
            a = O.seed.range(N); b = O.seed.range(N)
            lst[a], lst[b] = lst[b], lst[a]
        ret = 0
        for (px, py) in lst:
            if skip22 and px == 2 and py == 2:
                continue
            if O.bsub_fits(ctx, S, g, GS, px, py):
                v = O.seed.range(g[4])
                O.bsub_stamp(ctx, S, g, GS, px, py, (g[2] + 1) * (v + 1))
                O.hit("border sub stamp (type %d)" % ctx["type"], 1)
                ret = 1
                if rec["bord"] in (0, 1):
                    return 1
        return ret

    def bsub_cells(O, S, g, GS, px, py, srcx):
        px -= tmod(px, GS); py -= tmod(py, GS)
        cols = S["cols"]
        for gy in range(g[3]):
            for gx in range(g[2]):
                si = (g[1] + gy) * cols + g[0] + gx + srcx
                W = S["wall"][si] if S["wall"] else 0
                F = S["floor"][si] if S["floor"] else 0
                yield px + GS * gx, py + GS * gy, W, F

    def bsub_fits(O, ctx, S, g, GS, px, py):
        for X, Y, W, F in O.bsub_cells(S, g, GS, px, py, 0):
            if not O.inb(X, Y):
                raise NotImplementedError("border sub cell outside the grid")
            D = O.defg[Y][X]
            if ctx["act5"]:
                if not O.a5_match(X, Y, D, F, W):
                    return False
            elif W & 1:
                o = ((W >> 8) & 0xFF) - 1
                if o != ctx["wild"] and ctx["base"] + o != D:
                    return False
                if O.cell[Y][X] & 0x400:
                    return False
            elif F & 2:
                if not O.fits(X, Y, 0, 0, 0):
                    return False
        return True

    def bsub_stamp(O, ctx, S, g, GS, px, py, srcx):
        for X, Y, W, F in O.bsub_cells(S, g, GS, px, py, srcx):
            if W & 1:
                o = ((W >> 8) & 0xFF) - 1
                d = O.a5_map((W >> 20) & 0x3F, (W >> 8) & 0xFF) if ctx["act5"] else ctx["base"] + o
                if d != -5 and o != ctx["wild"]:
                    O.place(X, Y, d, 0, 1)
            elif F & 2:
                O.defg[Y][X] = 0; O.cell[Y][X] = 0
            else:
                O.defg[Y][X] = 0; O.cell[Y][X] = 0x100

    # ---- output: what OutdoorRoomsCreate makes
    def items(O):
        out = []
        for cy in range(O.ch):
            for cx in range(O.cw):
                c = O.cell[cy][cx]
                x, y = O.rect[0] + 8 * cx, O.rect[1] + 8 * cy
                if c & 0x200:
                    if O.defg[cy][cx]:
                        out.append(("P", O.defg[cy][cx], x, y, (c >> 16) & 0xF, O.g0[cy][cx]))
                elif not (c & 0x100):
                    out.append(("R", x, y))
        return out

    def run(O):
        O.ring_build()
        a = O.act
        if O.lid == 134:
            a = 1
        getattr(O, "act%d" % (a + 1))()

    # ---- Act I (sub_006807F0_OutdoorAct1)
    def a1_cliff_mark(O):   # 0x00680070
        head = O.ring
        p = head
        while p.next is not head:
            p = p.next
        v = head; first = head; done = False
        while True:
            w = v
            n0 = v.next
            if ((v.x < n0.x and v.y < p.y and not v.flags & 1 and not p.flags & 1) or
                    (n0.y < v.y and v.x < p.x and not v.flags & 1 and not p.flags & 1)):
                last = None
                while True:
                    if w is first:
                        done = True
                    n = w.next
                    if w.y < n.y or n.x < w.x or w.flags & 1 or n.flags & 1:
                        break
                    if (w.x < n.x and n.y < n.next.y and not n.flags & 1) or (n.y < w.y and n.x < n.next.x and not n.flags & 1):
                        last = w
                    w = n
                    if n is v:
                        break
                if last is not None:
                    q = v
                    while q is not last:
                        q.type = 1; q = q.next
                    q.type = 1
                    O.flags |= 0x20
                    O.hit("A1 cliff run", 1)
            v = w.next
            if done:
                return
            p = w; first = O.ring
            if v is O.ring:
                return

    def a1_river_clear(O, x):   # 0x0067FC70
        for y in range(O.ch):
            if O.cell[y][x] & 2 or O.cell[y][x + 1] & 2:
                return False
        return True

    def a1_river(O, x):   # 0x0067FE90
        for y in range(O.ch):
            for col, d, k in ((x, 26, 0), (x + 1, 27, 1)):
                c = O.cell[y][col]; pd = O.defg[y][col]
                if pd == 0:
                    idx = 0 if c & 0x100 else 3
                elif pd == 7 and (c & 0xF0000) == 0x30000:
                    idx = 3
                else:
                    idx = RIVER_T[2 * pd + k]
                O.place(col, y, d, idx)
        O.hit("A1 river", 1)
        if O.flags & 0x14:
            O.a1_bridge(x)

    def free(O, x, y):   # 0x00674200
        return not (O.cell[y][x] & 0x1B81)

    def a1_bridge(O, x):   # 0x0067FD20
        n = O.ch - 2
        s0 = O.seed.range(n)
        for k in range(max(n, 0)):
            y = tmod(k + s0, n) + 1
            if not (O.flags & 4) and not O.free(x - 1, y):
                continue
            if not O.free(x + 2, y) if not (O.flags & 4) else not O.free(x - 1, y):
                continue
            if (O.cell[y][x] & 0xF0000) != 0x30000 or (O.cell[y][x + 1] & 0xF0000) != 0x30000:
                continue
            O.place(x, y, 28, 1); O.place(x + 1, y, 28, 2 + ((O.flags & 4) != 0))
            O.hit("A1 bridge", 1)
            return

    def a1_cave_try(O, x, y):   # 0x006801A0
        d = O.defg[y][x]
        if d == 16: O.place(x, y, 25, -1)
        elif d == 17: O.place(x, y, 24, -1)
        else: return 0
        O.flags |= 0x40
        return 1

    def a1_river_east_cave(O):   # 0x00680200
        if O.flags & 0xC and O.a1_river_clear(O.cw - 2):
            O.a1_river(O.cw - 2)
        if O.flags & 0x20 and not O.flags & 0x40:
            r = O.seed.step()
            hit = 0
            if r & 1 == 0:
                for y in range(O.ch):
                    for x in range(O.cw):
                        hit = O.a1_cave_try(x, y)
                        if hit: break
                    if hit: break
            else:
                for x in range(O.ch):
                    for y in range(O.cw):
                        hit = O.a1_cave_try(x, y)
                        if hit: break
                    if hit: break
            if not hit:
                raise Fatal("cliff cave not placed")
            O.hit("A1 cliff cave", 1)
        if O.flags & 0x1C and not O.flags & 0x40:
            x0 = O.cw - (4 if O.flags & 0x10 else 5)
            r = O.seed.step() & 3
            x = 3 if r & 1 else x0
            y = 3 if r >> 1 else O.ch - 4
            O.place(x, y, 51 + (O.lid == 2), -1)
            O.flags |= 0x40
            O.hit("A1 corner cave", 1)

    def a1_mid_trans_cave(O):   # 0x006803D0
        if O.flags & 0x10 and O.a1_river_clear(tdiv(O.cw, 2) - 1):
            O.a1_river(tdiv(O.cw, 2) - 1)
        if O.flags & 0x80: O.place(0, 0, 3, 1)
        if O.flags & 0x100: O.place(O.cw - 7, 0, 3, 2)
        if O.flags & 0x200: O.place(0, 1, 2, 1)
        if O.flags & 0x400: O.place(0, O.ch - 6, 2, 1)
        if not O.flags & 0x40:
            if O.lid == 2:
                ok = O.place_far(O.A.rect[1], 52, -1, 1, 0xF)
            else:
                ok = O.place_random(51, -1, 1, 0xF)
            if not ok:
                raise Fatal("cave not placed")
            O.flags |= 0x40

    # roads (0x00681420)
    def snap(O, pt):   # 0x00680CC0
        x, y, d = pt
        x -= O.rect[0]; y -= O.rect[1]
        if d == 0: x = tdiv(x, 8) * 8 + 11
        elif d == 1: y = tdiv(y, 8) * 8 + 11
        elif d == 2: x = tdiv(x, 8) * 8 - 5
        elif d == 3: y = tdiv(y, 8) * 8 - 5
        return [x + O.rect[0], y + O.rect[1], d]

    def a1_paths(O):
        Lx, Ly = O.rect[0], O.rect[1]
        O.polys = []
        A = []
        for n in O.adj:   # 0x00680D70
            if n["nbr"] == 1:
                r = n["rect"]; off = {0: (59, 19), 1: (29, 35), 2: (4, 22), 3: (29, 3)}.get(n["side"])
                if off is None:
                    raise NotImplementedError("town node side %d" % n["side"])
                A.append([r[0] + off[0], r[1] + off[1], n["side"]])
            elif n["nbr"] == 26:
                r = n["rect"]; A.append([r[0] + 27, r[1] + 13, 1])
        for x in range(O.cw):
            for y in range(O.ch):
                d = O.defg[y][x]; idx = (O.cell[y][x] >> 16) & 0xF
                dr = 4
                if d == 4 and idx == 3: dr = 3
                elif d == 5 and idx == 3: dr = 0
                elif d == 6 and idx == 3: dr = 1
                elif d == 7 and idx == 3: dr = 2
                elif d == 24: dr = 1
                elif d == 25: dr = 0
                elif d == 28 and idx == 1 and x == O.cw - 2: dr = 2
                elif d in (51, 52): dr = 1 if idx != 0 else 0
                if dr != 4:
                    A.append([Lx + 3 + 8 * x, Ly + 3 + 8 * y, dr])
        if len(A) > 6:
            raise NotImplementedError("more than 6 road endpoints")
        Bp = [O.snap(a) for a in A]
        cnt = len(A)
        O.hit("A1 road endpoints %d" % cnt, 1)
        # 0x00681000 hubs
        D = []
        bx = by = -1
        if O.flags & 0x10:
            xc = tdiv(O.cw, 2) - 1
            for yy in range(1, O.cw - 1):   # row bound cw-1 as in the code
                if yy >= O.ch:
                    raise NotImplementedError("BridgeFind reads past the grid")
                if O.defg[yy][xc] == 28 and ((O.cell[yy][xc] >> 16) & 0xF) == 1:
                    bx, by = xc, yy; break
        if bx != -1:
            X = Lx + 3 + bx * 8
            for a in A:
                D.append([X + 8, Ly + 3 + by * 8, 0] if X < a[0] else [X, Ly + 3 + by * 8, 2])
            O.hit("A1 road hub at the bridge", 1)
        elif cnt > 0:
            if cnt == 1:
                cx, cy = tdiv(O.cw, 2), tdiv(O.ch, 2)
            else:
                cx = tdiv(sum(a[0] - Lx for a in A), cnt * 8); cy = tdiv(sum(a[1] - Ly for a in A), cnt * 8)
            found = False
            for r in range(8):
                for j in range(4):
                    hx = HUB_DX[j] * r + cx; hy = HUB_DY[j] * r + cy
                    if 0 <= hx < O.cw and 0 <= hy < O.ch and O.free(hx, hy):
                        found = True; break
                if found: break
            hub = [Lx + 3 + hx * 8, Ly + 3 + hy * 8, 4]
            D = [list(hub) for _ in A]
        C = [O.snap(dd) for dd in D]
        for i in range(cnt):
            path = O.a1_search(Bp[i], C[i])
            if path is not None:
                for (x, y) in path:
                    if O.inb(x, y):
                        O.cell[y][x] |= 0x80
                # 0x00681240 A1PathJitter: r = step & 3, then per interior vertex (target -> start) two draws.
                # The polyline in level tiles: [raw hub if a bridge hub] C, jittered interior, Bp, A.
                r = O.seed.step() & 3
                pts = [list(p) for p in path]
                for q in pts[1:-1]:
                    s1 = O.seed.step(); s2 = O.seed.step()
                    q[0] = O.rect[0] + 8 * q[0] + 3 + ((s1 & 1) + 2) * JIT_DX[r]
                    q[1] = O.rect[1] + 8 * q[1] + 3 + ((s2 & 1) + 2) * JIT_DY[r]
                    r = (r + 1) & 3
                pts[0] = list(C[i][:2]); pts[-1] = list(Bp[i][:2])
                if D[i][2] != 4:
                    pts.insert(0, list(D[i][:2]))
                pts.append(list(A[i][:2]))
                O.polys.append(pts)
                O.hit("A1 road path found", 1)
            else:
                O.hit("A1 road path not found", 1)

    def a1_search(O, Bw, Cw):   # 0x006817D0
        sx, sy = tdiv(Bw[0] - O.rect[0], 8), tdiv(Bw[1] - O.rect[1], 8)
        tx, ty = tdiv(Cw[0] - O.rect[0], 8), tdiv(Cw[1] - O.rect[1], 8)
        if abs(sx - tx) + abs(sy - ty) <= 1:
            return [(sx, sy), (tx, ty)]
        def h(x, y):
            a, b = abs(x - tx), abs(y - ty)
            return min(a, b) + 2 * max(a, b)
        h0 = h(sx, sy)
        d0 = dir4(sx, sy, tx, ty)
        bound = h0 + tdiv(h0, 2); top = bound + 35
        while True:
            res, cnt = O.a1_ida(sx, sy, tx, ty, d0, h0, bound)
            bound += 5
            if cnt > 899:
                O.hit("A1 road search pool exhausted", 1)
                return None
            if res is not None:
                return res
            if not bound < top:
                return None

    def a1_ida(O, sx, sy, tx, ty, d0, h0, bound):   # 0x00681630 on a fresh pool
        class N:
            __slots__ = ("f", "h", "g", "x", "y", "tried", "row", "ptr", "dir", "parent", "child")
        root = N(); root.f = root.h = h0; root.g = 0; root.x, root.y = sx, sy; root.tried = -1; root.row = 0; root.ptr = 0
        root.dir = d0 & 3; root.parent = None; root.child = None
        cnt = [1]
        node = root
        while True:
            if node.x == tx and node.y == ty:
                path = []; q = node
                while q is not None:
                    path.append((q.x, q.y)); q = q.parent
                return path, cnt[0]
            nx = node.x + DX4[node.dir]; ny = node.y + DY4[node.dir]
            ok = False
            if nx == tx and ny == ty:
                ok = True
            elif 0 <= nx < O.cw and 0 <= ny < O.ch and not O.cell[ny][nx] & 0x200:
                ok = True; q = node
                while q is not None:
                    if q.x == nx and q.y == ny:
                        ok = False; break
                    q = q.parent
            if ok:
                cost = 2 if (node.x == nx or node.y == ny) else 3
                a, b = abs(nx - tx), abs(ny - ty)
                hh = min(a, b) + 2 * max(a, b)
                f = hh + node.g + cost
                if f <= bound:
                    if node.child is None:
                        if cnt[0] == 900:
                            return None, cnt[0]
                        cnt[0] += 1
                        c = N(); c.child = None; c.parent = node; node.child = c
                    c = node.child
                    c.h = hh; c.f = f; c.g = node.g + cost; c.tried = 0
                    td = dir4(nx, ny, tx, ty)
                    row = (node.dir - td) & 3
                    c.row = row; c.ptr = 0
                    c.dir = (T2840[4 * row] + td) & 3
                    c.x, c.y = nx, ny
                    node = c
                    continue
            # 0x00681560 backtrack
            n = node
            if n.tried < 4:
                n.ptr += 1; n.dir = (T2840[(4 * n.row + n.ptr) % 16] + n.dir) & 3
            n.tried += 1
            if n.tried == 3:
                while True:
                    if n is root:
                        return None, cnt[0]
                    n = n.parent
                    n.ptr += 1; n.dir = (T2840[(4 * n.row + n.ptr) % 16] + n.dir) & 3
                    n.tried += 1
                    if n.tried != 3:
                        break
            node = n

    def act1(O):
        lid = O.lid
        if lid not in (2, 3, 17):
            O.a1_cliff_mark()
        O.seam_mark()
        O.border_build()
        if 2 <= lid <= 7:
            O.border_sub(0, 4)
            O.a1_river_east_cave()
            O.border_sub(1, 4); O.border_sub(2, 4)
            O.a1_mid_trans_cave()
            O.border_sub(3, 4)
            O.a1_paths()
        if lid == 39:
            for t in range(4):
                O.border_sub(t, 4)
        if 3 <= lid <= 6:
            O.waypoint()
        if 2 <= lid <= 7:
            O.shrines()
        Near, Rand = O.place_near, (lambda d: O.place_random(d, -1, 0, 0xF))
        def one_or_two(d, s):
            r = O.seed.step()
            if r & 3 == 0:
                Near(d); Near(d)
            else:
                Near(d)
                if s and O.seed.step() & 1:
                    Near(49)
        if lid == 2: Near(46); one_or_two(47, 0); Rand(29); Rand(30)
        elif lid == 3: one_or_two(48, 1); Rand(44); Rand(29); Rand(30)
        elif lid == 4: Near(160); Near(45); Rand(162); one_or_two(47, 1); one_or_two(42, 0); Rand(31)
        elif lid == 5: Rand(161); Rand(41); Rand(40); one_or_two(48, 1); one_or_two(43, 0); Rand(29); Rand(30)
        elif lid == 6: Rand(163); Rand(38); Rand(39); one_or_two(47, 1); one_or_two(42, 0); Rand(29); Rand(30)
        elif lid == 7: one_or_two(48, 1); one_or_two(43, 0); Rand(31)
        elif lid == 17: O.place(1, 1, 108, -1)
        elif lid == 39:
            for d in (50, 46, 31, 38, 39, 29, 30): Rand(d)

    def waypoint(O):   # 0x00674B70
        if O.lid == 3:
            vis = O.A.vis(3)
            k = next((k for k in range(8) if vis[k] == 2), 8)
            f = 0x10 << k
            for y in range(O.ch):
                for x in range(O.cw):
                    if (O.g0[y][x] & f) and (O.cell[y][x] & 0x400):
                        x = 1 if x == 0 else x; y = 1 if y == 0 else y
                        if x == O.cw - 1: x -= 1
                        if y == O.ch - 1: y -= 1
                        O.g0[y][x] |= 0x20000; O.cell[y][x] |= 0x800
                        O.hit("waypoint by the Blood Moor seam", 1)
                        return
        N = (O.cw - 2) * (O.ch - 2)
        if N <= 0:
            return
        for (x, y) in O.shuffle(O.cw - 2, O.ch - 2):
            if not O.cell[y + 1][x + 1] & 0x1B81:
                O.g0[y + 1][x + 1] |= 0x10000; O.cell[y + 1][x + 1] |= 0x800
                O.hit("waypoint placed", 1)
                return
        O.hit("waypoint not placed", 1)

    def shrines(O, count=5):   # 0x00674E40
        r = O.seed.step() & 3
        N = (O.cw - 2) * (O.ch - 2)
        if N <= 0:
            return
        for (x, y) in O.shuffle(O.cw - 2, O.ch - 2):
            if count <= 0:
                break
            if not O.cell[y + 1][x + 1] & 0x1B81:
                O.g0[y + 1][x + 1] |= SHRINE_FLAG[r]; O.cell[y + 1][x + 1] |= 0x1000
                r = (r + 1) & 3; count -= 1
                O.hit("shrine placed", 1)

    def place_list(O, defs, perfile):   # 0x0067F470
        n = len(defs)
        k = O.seed.range(n)
        for _ in range(n):
            if not perfile:
                O.place_random(defs[k], -1, 0, 0xF)
            else:
                for i in range(PREST[defs[k]]["files"]):
                    O.place_random(defs[k], i, 0, 0xF)
            k = tmod(k + 1, n)

    def a2_subs(O):   # 0x0067F630
        for t in (2, 1, 3):
            O.border_sub(t, 364)

    def a2_special(O):   # 0x0067F670
        d = {41: 388, 42: 388, 43: 390, 44: 412, 45: 389}.get(O.lid)
        if d is None or not O.place_random(d, -1, 0, 0xF):
            raise Fatal("Act II special area")

    def a2_cliff(O):   # 0x0067F5C0
        k = O.seed.step() & 7
        O.hit("Act II cliff layout %d" % k, 1)
        e = _odi(0x6F2390 + 0x50 * k, 20)
        for j in range(5):
            d, idx, x, y = e[4 * j: 4 * j + 4]
            O.place(x, y, d, idx)

    def act2(O):   # sub_0067F980_OutdoorAct2
        O.seam_mark()
        O.border_build()
        lid = O.lid
        if lid == 41:
            node = next((n for n in O.adj if n["nbr"] == 40), None)
            if node is not None:
                if node["side"] == 3: O.place(0, O.ch - 1, 363, -1)
                else: O.place(O.cw - 1, 0, 362, -1)
            O.a2_subs(); O.a2_special(); O.shrines()
            O.place_list([395, 411, 401, 402, 399, 398, 403], 0)
        elif lid in (42, 43, 44):
            O.a2_cliff(); O.a2_subs(); O.a2_special()
            if lid == 42:
                O.waypoint(); O.shrines()
                O.place_list([395, 411, 400, 398], 0); O.place_list([404, 405, 406, 407], 1)
            elif lid == 43:
                O.place_list([396, 397], 0); O.waypoint(); O.shrines()
                O.place_list([411, 399, 398, 403], 0); O.place_list([395], 1); O.place_list([395], 1)
            else:
                O.place_list([413, 408, 409, 410], 0); O.waypoint(); O.shrines()
                O.place_list([395, 400, 398, 404, 405], 0); O.place_list([411], 1); O.place_list([411], 1)
        elif lid == 45:
            O.a2_special()
        elif lid == 46:
            e = _odi(0x6F2610, 36)
            for j in range(9):
                d, idx, x, y = e[4 * j: 4 * j + 4]
                O.place(x, y, d, idx)
            O.place(4, 4, 394, -1)
            O.a2_subs(); O.shrines()
            O.place_list([401, 402, 406, 407, 403], 0); O.place_list([392, 393], 1)
        elif lid == 134:
            O.place(4, 4, 394, -1)
            O.a2_subs()
            O.place_list([401, 402, 406, 407, 403], 0); O.place_list([392, 393], 1)
            O.shrines()

    # ---- Act III (sub_0067F450_OutdoorAct3: OutSeamMark, OutJungleCells, OutKurastLevel, OutTravincal)
    def fill(O, lo, hi, maxn):   # 0x0067EED0
        n = 0
        for (x, y) in O.shuffle(O.cw, O.ch):
            d = lo + O.seed.range(hi - lo + 1)
            if O.fits(x, y, d):
                O.place(x, y, d, -1)
                n += 1
                if maxn > 0 and n >= maxn:
                    return

    def act3(O):
        O.seam_mark()
        lid, cw, ch = O.lid, O.cw, O.ch
        if 76 <= lid <= 78:   # 0x0067E910
            J = O.A.jungle[lid]
            defs = J["defs"]
            nx, ny = J["nx"], J["ny"]
            r = O.seed.range(6 if J["clr"] == 3 else 2)
            e = kk = 0
            for j in range(ny):
                if lid == 76 and j == ny - 1:
                    O.place(0, j * 4, 0x23D, 1 if defs[ny * nx - 1] == 0 else 0)
                    e += 2
                elif lid == 78 and j == 0:
                    O.place(0, 0, 0x23E, 1 if defs[1] == 0 else 0)
                    e += 2
                else:
                    for i in range(nx):
                        d = defs[e]
                        e += 1
                        idx = -1
                        if d > 0x23E:
                            if kk > 2:
                                raise Fatal("jungle cells: more than 3 clearings")
                            d += CLR_OFF[lid]
                            idx = PERM[kk + r * 3]
                            kk += 1
                        if d:
                            O.place(i * 4, j * 4, d, idx)
        if lid in (79, 80, 81):   # 0x0067F190 and the rings 0x0067EAD0 / 0x0067EC30 / 0x0067ED70
            S, N_, E_, W_, NE, NW, SE, SW = {79: (606, 605, 607, 608, 609, 610, 611, 612),
                                             80: (620, 619, 621, 622, 623, 624, 625, 626),
                                             81: (637, 636, 638, 639, 640, 641, 642, 643)}[lid]
            mid = tdiv(cw - 1, 2)
            bit = O.A.bit474
            if lid == 79:
                gate = 1 if bit else cw - 2
                for x in range(1, cw - 1):
                    O.place(x, 0, N_ + 8 * (x == gate), -1)
                x = 1
                while x < cw - 1:
                    O.place(x, ch - 1, S + 8 * (x == mid), -1)
                    x += 1 + (x == mid)
            elif lid == 80:
                sg, ng = (1, cw - 2) if bit else (cw - 2, 1)
                for x in range(1, cw - 1):
                    O.place(x, 0, N_ + 8 * (x == ng), -1)
                    O.place(x, ch - 1, S + 8 * (x == sg), -1)
            else:
                sg = cw - 2 if bit else 1
                x = 1
                while x < cw - 1:
                    O.place(x, 0, N_ + 8 * (x == mid), -1)
                    x += 1 + (x == mid)
                for x in range(1, cw - 1):
                    O.place(x, ch - 1, S + 8 * (x == sg), -1)
            for y in range(1, ch - 1):
                O.place(cw - 1, y, E_, -1)
                O.place(0, y, W_, -1)
            O.place(0, 0, NW, -1); O.place(cw - 1, 0, NE, -1); O.place(0, ch - 1, SW, -1); O.place(cw - 1, ch - 1, SE, -1)
            O.hit("A3 Kurast ring %d" % lid, 1)
            if lid == 79:
                O.place_random(0x277, 0)
                O.fill(0x26A, 0x26A, 4); O.fill(0x268, 0x269, 0); O.fill(0x267, 0x267, 0)
            elif lid == 80:
                O.place(3, 3, 0x275, 0); O.place(cw - 4, 3, 0x275, 1)
                O.place_random(0x276, 0); O.place_random(0x276, 1); O.place_random(0x277, 0)
                O.fill(0x27B, 0x27B, 4); O.fill(0x279, 0x27A, 0); O.fill(0x278, 0x278, 0)
            else:
                O.place(3, ch - 4, 0x286, 0); O.place(cw - 4, ch - 4, 0x286, 1)
                O.place_random(0x287, 0); O.place_random(0x287, 1); O.place_random(0x277, 0)
                O.fill(0x28B, 0x28B, 4); O.fill(0x289, 0x28A, 0); O.fill(0x288, 0x288, 0)
        elif lid == 82:
            O.place(0, 0, 0x28C, 0)
        elif lid == 83:   # 0x0067F3B0
            for (x, y, d) in ((0, 0, 0x28D), (2, 0, 0x28E), (6, 0, 0x28F), (0, 4, 0x290), (2, 4, 0x291), (6, 4, 0x292)):
                O.place(x, y, d, -1)


    def act4(O):   # sub_0067E890_OutdoorAct4
        if O.lid == 108:
            O.seam_mark()
            T = _odi(0x6F22C0, 25)
            for i in range(25):
                O.place((i % 5) * 3, (i // 5) * 3, T[i], -1)
            return
        O.seam_mark()
        O.border_build()
        if O.lid in (104, 105, 106):
            if O.flags & 0x400000: O.place(0, 1, 798, -1)
            if O.flags & 0x800000: O.place(0, 4, 798, -1)
            for t in (1, 2, 3):
                O.border_sub(t, 799)
            if O.lid == 106:
                O.place_random(811)
            aa = {104: 812, 105: 817, 106: 823}[O.lid]; p = {104: 828, 105: 832, 106: 832}[O.lid]
            for d, k in ((aa, 1), (aa + 1, 2), (aa + 2, 2), (aa + 3, 2)):
                for _ in range(k): O.place_random(d)
            if O.lid == 105:
                O.place_random(822)
            for _ in range(4): O.place_random(aa + 4)
            for d, k in ((p, 1), (p + 1, 2), (p + 2, 2), (p + 3, 4)):
                for _ in range(k): O.place_random(d)

    # ---- Act V (sub_0067E600_OutdoorAct5)
    def a5_map(O, main, sub):   # 0x0067E000
        if main in (0x30, 0x31):
            for r in range(10):
                e = A5MAP[5 * r: 5 * r + 5]
                if main == e[0] and e[1] <= sub <= e[2]:
                    return (e[4] if O.lid == 117 else e[3]) - e[1] + sub
        raise Fatal("BarricadeSubDefMap main %d sub %d" % (main, sub))

    def a5_match(O, X, Y, D, F, W):   # 0x0067E080
        m = O.a5_map((W >> 20) & 0x3F, (W >> 8) & 0xFF)
        if m == -5:
            return True
        if m != D:
            return False
        return not (O.cell[Y][X] & 0x400)

    def defat(O, x, y):   # 0x00674120
        return O.defg[y][x] if O.cell[y][x] & 0x200 else 0

    def act5(O):
        cw, ch, lid = O.cw, O.ch, O.lid
        if lid == 110:   # 0x0067E560
            sw = tdiv(PREST[865]["sx"], 8); x = cw - sw; k = 0
            while x >= 0:
                O.place(x, 0, 865 + k, 0); k += 1; x -= sw
                if k > 14:
                    return
            raise Fatal("siege strips do not fit")
        O.seam_mark()
        fam = 4 + (lid == 117)
        # 0x0067DCF0 border ring
        for v in O.ring_list():
            n = v.next
            dx, dy = sgn(n.x - v.x), sgn(n.y - v.y)
            dx2, dy2 = sgn(n.next.x - n.x), sgn(n.next.y - n.y)
            ax, ay = abs(dx), abs(dy)
            tx, ty = n.x & ~1, n.y & ~1
            x, y = v.x & ~1, v.y & ~1
            side = BDEFS5[(fam - 4) + 2 * DIRIDX[(dx, dy)]]
            if not (v.flags & 2):
                while (x, y) != (tx, ty):
                    y += 2 * dy; x += 2 * dx
                    O.place(x, y, side, -1); O.cell[y][x] |= 1
            if v.flags & 1:
                gx = (max(v.x, n.x) - 4 * ax) & ~1; gy = (max(v.y, n.y) - 4 * ay) & ~1
                O.cell[gy][gx] |= 0x400; O.cell[gy + 2 * ay][gx + 2 * ax] |= 0x400
                O.hit("A5 seam gate marks", 1)
            k = CORNER[40 + e2(2 * dx) + 9 * (e2(2 * dx2) + 2 * dy2) + 2 * dy]
            if k != -1:
                cd = BDEFS5[(fam - 6) + 2 * k]
                if cd:
                    O.place(tx, ty, cd, -1); O.cell[ty][tx] |= 1
        if lid == 111:
            O.cell[ch - 4][cw - 2] |= 0x400; O.cell[ch - 3][cw - 2] |= 0x400
        # 0x0067DEF0 ravine
        snow = 76 if lid == 117 else 0
        x, y = cw - 2, 0
        while x != 0 or y != ch - 2:
            k = O.defg[y][x] - (881 + snow)
            if not 0 <= k < 12:
                raise Fatal("ravine walk on def %d" % O.defg[y][x])
            O.place(x, y, 893 + snow + k, -1)
            x += 2 * A5STEP[2 * k]; y += 2 * A5STEP[2 * k + 1]
        O.place(cw - 2, 0, 906 + snow, -1)
        O.place(0, ch - 2, 905 + snow, -1)
        # 0x0067DB50 gates
        for x in range(cw):
            if O.cell[0][x] & 0x400: O.place(x, 0, 909, -1); O.hit("A5 gate 909", 1); break
        for x in range(cw):
            if O.cell[ch - 2][x] & 0x400: O.place(x, ch - 2, 908, -1); O.hit("A5 gate 908", 1); break
        for y in range(ch):
            if O.cell[y][0] & 0x400: O.place(0, y, 910, -1); O.hit("A5 gate 910", 1); break
        for y in range(ch):
            if O.cell[y][cw - 2] & 0x400: O.place(cw - 2, y, 907, -1); O.hit("A5 gate 907", 1); break
        # 0x0067DA70 cave entries
        for r in range(3):
            e = A5CAVE[5 * r: 5 * r + 5]
            if e[0] == lid:
                if O.rect[3] < O.rect[2]:
                    O.place(cw - 2 if e[2] else 0, 2, e[4], e[1])
                else:
                    O.place(2, ch - 2 if e[2] else 0, e[3], e[1])
        if lid == 111:   # 0x0067E4B0
            y = ch - tdiv(PREST[880]["sy"], 8)
            O.place(cw - 2, y, 880, -1); O.place(cw - 2, y - 2, 896, -1)
        O.border_sub(12, 0, act5=True)   # 0x0067E0E0
        if lid == 111:   # 0x0067E240 prisons
            n = 0
            for a in range(90):
                if n > 2:
                    break
                x = 2 * O.seed.range(tdiv(cw, 2)); y = 2 * O.seed.range(tdiv(ch, 2))
                d = O.defat(x, y)
                if 915 <= d <= 922:
                    O.place(x, y, d + 16, -1); n += 1
            ox = O.seed.range(tdiv(cw, 2)); oy = O.seed.range(tdiv(ch, 2))
            for r in range(ch):
                if n > 2: break
                for c in range(cw):
                    if n > 2: break
                    y = tmod(r + 2 * oy, ch); x = tmod(c + 2 * ox, cw)
                    d = O.defat(x, y)
                    if 915 <= d <= 922:
                        O.place(x, y, d + 16, -1); n += 1; O.hit("A5 prison by scan", 1)
            if n < 3:
                raise Fatal("fewer than 3 prisons")
        for r in range(15):   # 0x0067E160
            e = A5TABLE[7 * r: 7 * r + 7]
            if e[0] != lid:
                continue
            d = e[1] if O.rect[2] < O.rect[3] else e[2]
            res = 0
            for _ in range(e[5]):
                res = O.place_random(d, e[3], 0, 0xF)
            if (e[5] <= 0 or not res) and e[6]:
                raise Fatal("required table row failed")




def side_lookup(v, side):
    if 0 <= v < 16:
        return T_SIDE[4 * v + side]
    raise Fatal("side lookup with Def %d (outside the 16-row table)" % v)


# ---------------------------------------------------------------- 0x006777D0
def rel_rect(P, w, h, d):
    dx = dy = 0
    if d == 0:
        dy = -h
    elif d in (1, 2):
        dy = tdiv(-h, 3)  # (hi(h*0x55555555) - h) >> 1, sign-corrected
        dx = -w if d == 1 else w
    elif d in (3, 4):
        dy = tdiv(-2 * h, 3)
        dx = -w if d == 3 else w
    return dict(x=P["x"] + dx, y=P["y"] + dy, w=w, h=h, dir=d, kids=[], parent=P)


def _jgap(A, B):  # RectGapTest(A, B, 0) == 0
    gx = (B["x"] - A["w"] - A["x"]) if A["x"] < B["x"] else (A["x"] - B["w"] - B["x"])
    gy = (B["y"] - A["h"] - A["y"]) if A["y"] < B["y"] else (A["y"] - B["h"] - B["y"])
    return gx < 0 and gy < 0


# ---------------------------------------------------------------- 0x00677880
def jungle_layout(act, diff, town):
    """sub_00677880_JungleLayout on the act seed `act` (town = level 75's rect), then sub_00678910_KurastStack."""
    town = dict(x=town[0], y=town[1])
    W, H = LV[76]["sx"][diff], LV[76]["sy"][diff]
    nx, ny = tdiv(W, 32), tdiv(H, 32)
    recs = [dict(x=town["x"], y=town["y"] - H, w=W, h=H, dir=0, kids=[], parent=None)]
    minx, miny, maxx, maxy = town["x"], town["y"] - H, town["x"] + W, town["y"]
    while len(recs) < 3:
        k = act.range(len(recs))
        d = act.step() % 5
        R = rel_rect(recs[k], W, H, d)
        if any(_jgap(A, R) for A in recs):
            continue
        recs[k]["kids"].append(R)
        if len(recs[k]["kids"]) > 3:
            raise Fatal("fatal 0x63e")
        minx, miny, maxx = min(minx, R["x"]), min(miny, R["y"]), max(maxx, R["x"] + R["w"])
        recs.append(R)
    if (maxx - minx) % 32 or (maxy - miny) % 32:
        raise Fatal("fatal 0x64d/0x64e")
    gh, gw = tdiv(maxy - miny, 32) + 2, tdiv(maxx - minx, 32) + 2
    restarts = 0
    while True:  # LAB_00677b80
        owner = [0] * (gw * gh); order = [0] * (gw * gh); marks = [0] * (gw * gh); res = [0] * (gw * gh)
        for k, R in enumerate(recs):
            cx0, cy0 = tdiv(R["x"] - minx, 32) + 1, tdiv(R["y"] - miny, 32) + 1
            R["cx0"], R["cy0"] = cx0, cy0
            s = act.step() & 1 if k == 0 else (1 if R["dir"] % 2 == 1 else 0)
            bottom = cy0 + ny - 1
            while True:
                for j in range(ny):
                    for i in range(nx):
                        c = (cy0 + j) * gw + cx0 + i
                        owner[c] = k + 1; order[c] = 0; marks[c] = 0; res[c] = 0
                col = s + cx0
                if k != 0:
                    marks[gw * bottom + col] = 1
                    marks[gw * bottom + col + (1 if s == 0 else -1)] = 2
                for K in R["kids"]:
                    cd = K["dir"]
                    if cd == 0: marks[cy0 * gw + cx0] = 1
                    elif cd == 1: marks[(cy0 + 3) * gw + cx0] = 1
                    elif cd == 2: marks[(cy0 + 3) * gw + cx0 + 1] = 1
                    elif cd == 3: marks[(cy0 + 1) * gw + cx0] = 1
                    elif cd == 4: marks[(cy0 + 1) * gw + cx0 + 1] = 1
                cnt2 = 1 if k != 0 else 0
                run = 0
                row = bottom
                num = (k + 1) * 100
                while cy0 <= row:
                    order[row * gw + col] = num; num += 1
                    up = True
                    if not (run == 0 or row == cy0):
                        r = act.step() % 3
                        if r == 0:
                            up = False
                            run = 0
                            if s == 0: col += 1; s = 1
                            else: col -= 1; s = 0
                    if up:
                        run += 1
                        o = row * gw + col + (1 if s == 0 else -1)
                        if run > 1 and row > 1 and marks[o] == 0:
                            cnt2 += 1; marks[o] = 2
                        row -= 1
                if cnt2 >= 2:
                    break
                COV["jungle path retry"] += 1
            while cnt2 > 3:
                j2 = act.range(cnt2); COV["jungle mark2 trim"] += 1
                n2 = 0; done = False
                for j in range(ny):
                    if done: break
                    for i in range(nx):
                        if done: break
                        c = (cy0 + j) * gw + cx0 + i
                        if marks[c] == 2:
                            if n2 == j2:
                                marks[c] = 0; done = True; cnt2 -= 1
                            n2 += 1
        # phase 3: exit masks
        for row in range(gh):
            for col in range(gw):
                c = row * gw + col
                ow = owner[c]; m = 0; best = 0x7FFFFFFF
                if marks[c] == 1:
                    U, D, Rr, Lf = c - gw, c + gw, c + 1, c - 1
                    if order[U] and order[U] < best and owner[U] == ow: m = 8; best = order[U]
                    if order[D] and order[D] < best and owner[D] == ow: m = 4; best = order[D]
                    if order[Rr] and order[Rr] < best and owner[Rr] == ow: m = 2; best = order[Rr]
                    if order[Lf] and order[Lf] < best and owner[Lf] == ow: m = 1
                    if m & 8: res[U] |= 4
                    if m & 4: res[D] |= 8
                    if m & 2: res[Rr] |= 1
                    if m & 1: res[Lf] |= 2
                    if marks[U] == 1 and owner[U] != ow: m |= 8
                    if marks[D] == 1 and owner[D] != ow: m |= 4
                    if marks[Rr] == 1 and owner[Rr] != ow: m |= 2
                    if marks[Lf] == 1 and owner[Lf] != ow: m |= 1
                o = order[c]
                if o:
                    if abs(o - order[c - gw]) == 1: m |= 8
                    if abs(o - order[c + gw]) == 1: m |= 4
                    if abs(o - order[c + 1]) == 1: m |= 2
                    if abs(o - order[c - 1]) == 1: m |= 1
                res[c] |= m
        # phase 4: clearings
        restart = False
        for row in range(gh):
            if restart: break
            for col in range(gw):
                c = row * gw + col
                v = res[c]; ow = owner[c]
                r = act.step() & 3
                zero = v == 0
                if marks[c] == 2:
                    nb = [c - gw, c + gw, c + 1, c - 1]; bit = [0x80, 0x40, 0x20, 0x10]
                    for i in range(4):
                        q = (i + r) & 3; n = nb[q]
                        if owner[n] == ow and res[n] != 0 and res[n] < 15:
                            v |= bit[q]; break
                    if v == 0:
                        restart = True; break
                    if zero:
                        found = False
                        for i in range(4):
                            q = (i + r) & 3; n = nb[q]
                            if owner[n] != ow and marks[n] == 2:
                                v |= bit[q]; found = True; COV["jungle clearing 2nd loop link"] += 1; break
                        third = (act.step() & 1) and not found
                        r = act.step() & 3
                        COV["jungle clearing zero-v cells"] += 1
                        if third:
                            COV["jungle clearing 3rd loop"] += 1
                            for i in range(4):
                                q = (i + r) & 3; n = nb[q]
                                if res[n] != 0 and res[n] < 15 and not (v & bit[q]):
                                    v |= bit[q]; break
                    if v & 0x80: res[c - gw] |= 0x40
                    if v & 0x40: res[c + gw] |= 0x80
                    if v & 0x20: res[c + 1] |= 0x10
                    if v & 0x10: res[c - 1] |= 0x20
                    marks[c] = 0
                res[c] |= v
        if restart:
            COV["jungle restart"] += 1
            restarts += 1
            continue
        break
    # phase 5: Defs
    for c in range(gw * gh):
        v = res[c]; low = v & 15
        if low == 0:
            d = T_CLR[v >> 4] if v >= 16 else 0
            if v >= 16 and d == 0: raise Fatal("fatal 0x799")
        elif v < 16:
            d = low + 0x211
        else:
            d = low
            for b, side in ((0x10, 0), (0x20, 1), (0x40, 2), (0x80, 3)):
                if v & b: d = side_lookup(d, side); COV["jungle side bits"] += 1
            if d == 0: raise Fatal("fatal 0x78c")
        res[c] = d
    for R in recs:
        R["defs"] = [res[(R["cy0"] + j) * gw + i + R["cx0"]] for j in range(ny) for i in range(nx)]
        R["clr"] = sum(1 for d in R["defs"] if d > 0x23E)
        R["nx"], R["ny"] = nx, ny
    recs.sort(key=lambda R: -R["y"])  # bubble sort, descending y, stable
    out = {}
    for i, R in enumerate(recs):
        out[76 + i] = R
    # 0x00678910: 79..83 stacked north of 78
    P = out[78]; acc = 0
    for lid in range(79, 84):
        w, hh = LV[lid]["sx"][diff], LV[lid]["sy"][diff]
        acc -= hh
        out[lid] = dict(x=tdiv(P["w"], 2) - tdiv(w, 2) + P["x"], y=P["y"] + acc, w=w, h=hh)
    return out, restarts



def act_links_a3(A):
    """sub_006789B0_ActLinkAct3: level 75 at its Levels offset, the jungle layout and the Kurast stack on the act
    seed itself, then LevelSeamsByTouch(75, 83) and LevelBorderAdj(75..83)."""
    T = A.level_rect(75)
    A.rect[75] = list(T)
    n0 = A.seed.n
    out, A.jungle_restarts = jungle_layout(A.seed, A.diff, T)
    A.jungle_steps = A.seed.n - n0
    A.jungle = {}
    for lid in range(76, 84):
        R = out[lid]
        A.rect[lid] = [R["x"], R["y"], R["w"], R["h"]]
        if lid <= 78:
            A.jungle[lid] = dict(defs=R["defs"], clr=R["clr"], nx=R["nx"], ny=R["ny"])
    seams_by_touch(A, 75, 83)
    border_adj(A, 75, 83)



def math_fmod(a, n):
    """C signed % (idiv): sign of the dividend."""
    q = abs(a) // abs(n)
    r = abs(a) - q * abs(n)
    return -r if a < 0 else r


def cmd_gen(argv):
    root, exe, verbose, oracle, paths = DEFAULT_DATA, DEFAULT_EXE, False, False, []
    it = iter(argv)
    for a in it:
        if a == "--root":
            root = next(it)
        elif a == "--exe":
            exe = next(it)
        elif a == "-v":
            verbose = True
        elif a == "--preset-oracle":
            oracle = True
        else:
            paths.append(a)
    if not paths:
        print(__doc__)
        return 2
    m = GenModel(Data(root, exe), verbose, oracle, None if oracle else PresetUnitData(root, exe))
    rk = Model(Data(root, exe), verbose)      # plan 0027: the roomk passes on GenModel's out-room grids
    rk_logs = rk_acts = 0
    for p in paths:
        levels = m.run(p)
        if m.prep_pred:
            acts = run_log(rk, p, m.prep_pred)
            rk_logs += 1
            rk_acts += len(acts)
        by = {}
        for L in levels.values():
            if L.inited:
                by.setdefault(L.drlg, []).append(L.id)
        print("%s: %d levels created; LevelInit by DrlgType: %s" % (p, len(levels), {k: sorted(v) for k, v in sorted(by.items())}))
    for k in sorted(m.cov):
        print("  coverage %-62s %d" % (k, m.cov[k]))
    if m.prooms:
        acts = sorted({GenModel.act_of(r[1]) for r in m.prooms})
        lv = {}
        for r in m.prooms:
            lv.setdefault(r[1], set()).add(r[2])
        print("  preset rooms reproduced %d (%d with units), acts %s, levels %s"
              % (len(m.prooms), sum(1 for r in m.prooms if r[4]), acts, sorted(lv)))
    if rk_logs:
        for k in sorted(rk.cov):
            print("  roomk coverage %-56s %d" % (k, rk.cov[k]))
        print("roomk inside gen (logs with OD0 and LSUB lines: %d): %d activations, %d checks, %d mismatches"
              % (rk_logs, rk_acts, rk.checks, rk.fail))
    print("gen: %d checks, %d mismatches (sub_00667620 %s)" % (m.checks, m.fail, "oracle" if oracle else "modelled"))
    return 1 if (m.fail or rk.fail) else 0


def main(argv):
    cmds = {"roomk": cmd_roomk, "tables": cmd_tables, "p1cmp": cmd_p1cmp, "gen": cmd_gen}
    if len(argv) < 2 or argv[1] not in cmds:
        print(__doc__)
        return 2
    return cmds[argv[1]](argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))

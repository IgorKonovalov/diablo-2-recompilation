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
Inputs taken from the log because they are run-time state, not data: the type-1 grids (first LSUB;
drlg/outdoor), the type-2 file index (Phase 3), the neighbour list and which neighbours are built,
the warp records (LvlWarp row per node) and the level's warp ids. The type-2 tile build walks the
logged TINIT grids, which the prepare model has checked. Exit 0 only if every RACT, LSUBX and AROOM
line is predicted and every check holds. Stdlib only.

`gen` (plan 0008 Phase 3) replays a tools/gdb/drlg-gen.gdb log: per level, the create-time and build-time
seed Init(act base + id), every level-seed draw of the three generators as docs/findings/drlg/0003 models
them (DRLG_RoomCreate, sub_00666ED0_PresetInstanceCreate, sub_00667430_PresetLevelCreate,
sub_006738C0_MazePresetFile), the preset file index of every instance (draw, level/cell/maze overrides,
maze rotation) against the File cell the game loads, room counts and creation order, and
sub_006706A0_LvlSubRoll. Boundary oracles (seed in asserted, seed out taken from the log): the maze
generator (MZ0..MZ1), the outdoor act generators (OD0..OD1) and sub_00667620_PresetUnitDropRolls.
Inputs from the log: the outdoor cell's file index (PIO) and the maze cell's forced index (MFR).
Exit 0 only if every check holds.

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
        self.remap_o, self.remap_t = remap_tables(exe)
        self.old_orient = list(struct.unpack("<44I", exe_read(exe, DS1_OLD_ORIENT, 176)))
        self.lvlsub = [LvlSub(r) for r in excel_bin(root, "lvlsub")]
        self.lvlsub_dt1mask = [struct.unpack_from("<I", r, 0x48)[0] for r in excel_bin(root, "lvlsub")]
        self.lvlwarp = [LvlWarp(r) for r in excel_bin(root, "lvlwarp")]
        self.lvlprest = [LvlPrest(r) for r in excel_bin(root, "lvlprest")]
        self.drlgtype = [struct.unpack_from("<I", r, 0x30)[0] for r in excel_bin(root, "leveldefs")]
        self.lvltypes = [[r[0x3C * i:0x3C * (i + 1)].split(b"\0", 1)[0].decode("latin-1") for i in range(32)]
                         for r in excel_bin(root, "lvltypes")]
        self._dt1 = {}
        self._lists = {}
        self._subds1 = {}
        self._pristine = {}
        self.reset_process()

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
    __slots__ = ("o", "x", "y", "flags", "main", "sub")

    def __init__(self, o, x, y, flags, main, sub):
        self.o, self.x, self.y, self.flags, self.main, self.sub = o, x, y, flags, main, sub


def setflags(flags, cell, o):
    """sub_0066DB20_RoomTileSetFlags / 0x0066DDE0 bits the model needs: 0x1 and 0x1C000 (+0x2/0x4/0x8)."""
    if o != 13:
        flags |= (((cell >> 18) & 3) + 1) << 14
    if o == 14:
        flags |= 4
    elif o in (8, 9, 10, 11):
        flags |= 2
    if cell & 0x80:
        flags |= 1
    if cell & 0x80000000:
        flags |= 8
    else:
        flags &= ~8
    return flags


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

    def oracle(self, R, tile):
        """sub_0066D9E0_Orient89Unit: consume the room's next logged O89 (+ O89D) line."""
        if not R.o89 or R.o89[0][0] != "O89":
            raise ModelError("room %08x: model calls Orient89Unit, no O89 line left" % R.ptr)
        _, d = R.o89.pop(0)
        self.hit("Orient89Unit oracle call")
        if d["seed"] != fmt(R.seed):
            raise ModelError("room %08x: O89 seed in %s, model %s" % (R.ptr, d["seed"], fmt(R.seed)))
        if R.o89 and R.o89[0][0] == "O89D":
            _, dd = R.o89.pop(0)
            if dd["seed"] != fmt(R.seed):
                raise ModelError("room %08x: O89D seed %s, model %s" % (R.ptr, dd["seed"], fmt(R.seed)))
            self.stepr(R)
            self.hit("Orient89Unit oracle draw")

    # -- tile entries
    def node(self, R, kind):
        for nd in R.nodes:
            if (nd[0] != 0) == (kind != 0):
                return nd
        nd = [kind, []]
        R.nodes.insert(0, nd)
        return nd

    def add_wall(self, R, x, y, cell, mainsub, o, lst):
        """sub_0066DC50_RoomTileAdd: entry, flags (SetFlags -> Orient89Unit for o 8/9), o-3 partner."""
        e = Entry(o, x - R.x, y - R.y, 0, *mainsub)
        if lst is not None:
            lst.insert(0, e)
        e.flags = setflags(0, cell, o)
        if o in (8, 9):
            self.oracle(R, e)
        if o == 3:
            ms = self.pick(R, 4, cell)
            p = Entry(4, x - R.x, y - R.y, 0, *ms)
            if lst is not None:
                lst.insert(0, p)
            p.flags = setflags(0, cell, 4)
        return e

    def add_floor(self, R, x, y, cell, mainsub, lst):
        e = Entry(0, x - R.x, y - R.y, 0, *mainsub)
        e.flags = (((cell >> 18) & 3) + 1) << 14 | (1 if cell & 0x80 else 0) | (8 if cell & 0x80000000 else 0)
        if lst is not None:
            lst.insert(0, e)
        return e

    def add_shadow(self, R, x, y, cell, mainsub, lst):
        e = Entry(13, x - R.x, y - R.y, 0, *mainsub)
        e.flags = (1 if cell & 0x80 else 0) | (8 if cell & 0x80000000 else 0)
        if lst is not None:
            lst.insert(0, e)
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
        rec = self.data.lvlwarp[w["rec"]]
        self.hit("warp tile (visible)")
        if rec.litversion != 0:
            c2 = (cell | (rec.tiles << 8)) & MASK
            ms = self.pick(R, o, c2)
            self.add_wall(R, e.x + R.x, e.y + R.y, c2, ms, o, None)

    def hidden_warp(self, R, cell, o, x, y):
        """sub_0066E1C0 + sub_0066E360_HiddenWarpTilesAdd (bit-31 orientation 10/11)."""
        self.warp_unit_ok(R, cell, o, x, y)
        w = self.warp_node(R, cell)
        if w is None:
            return
        self.warp_switch(w, o)
        self.hit("warp tiles (hidden)")
        if self.data.lvlwarp[w["rec"]].litversion != 0:
            s8 = (cell >> 8) & 0xFF
            for i in range(4):
                self.pick(R, 0, ((s8 << 12) | i | 4) << 8)

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
                self.warp_tile_add(R, nd[1][0], cell, o)

    def merge(self, R, N, E, o, cell, x, y):
        """sub_0066E740_Bit2TileMerge; E is the neighbour N's entry."""
        T = self.data.remap_o[o]
        if E.flags & 1:
            self.hit("bit-2 merge: entry flag 0x1")
            if E.o in (8, 9):
                E.flags = setflags(E.flags, cell, E.o)
                self.oracle(R, E)
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
            pass                                   # partner flag only (no draw)
        elif o == 3:
            self.hit("bit-2 merge to orientation 3")
            E.flags |= 0xC008
            nd = self.node(R, 0)
            ms = self.pick(R, 3, cell)             # 0x0066E87C, this room
            self.add_wall(R, x, y, cell, ms, 3, nd[1])
        blank = E.o == 0 and E.main == 30 and E.sub == 0
        if o != E.o or blank:
            self.hit("bit-2 merge re-pick on the neighbour seed")
            ms = self.pick(N, o, cell)             # 0x0066E8F7: ECX = the NEIGHBOUR room
            E.o = o
            E.main, E.sub = ms
        E.flags = setflags(E.flags, cell, E.o)
        if E.o in (8, 9):
            self.oracle(R, E)

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


def parse_log(path):
    ev = []
    for line in open(path, errors="replace"):
        tag, _, rest = line.partition(" ")
        if tag in ("RRESEED", "LSUB", "LSUBX", "TINIT", "O89", "O89D", "RACT", "AROOM", "RTFREE"):
            ev.append((tag, json.loads(rest)))
        elif tag == "LOGERR":
            ev.append((tag, {"msg": rest.strip()}))
    return ev


def run_log(model, path):
    ev = parse_log(path)
    data = model.data
    rooms = model.rooms = {}        # pointers are per run
    data.reset_process()            # one log = one game process: fresh DS1 cache
    model.instances = {}
    pending = {}                    # room -> TINIT dict until its RACT
    lsub_grids = {}
    acts = []
    for i, (tag, d) in enumerate(ev):
        if tag == "LOGERR":
            model.check(False, "%s: logger error %s" % (path, d["msg"]))
            continue
        r = d.get("room")
        try:
            if tag == "RRESEED":
                R = Room(d, data)
                rooms[r] = R
                model.check(d["rt"] == 0, "%s %08x RRESEED with a RoomTile already" % (path, r))
                model.check(d["seed"] is not None, "")
                model.check_dt1(path, R, d)
            elif tag == "LSUB":
                R = rooms[r]
                model.check(d["seed"] == fmt(R.seed), "%s %08x LSUB seed %s model %s" % (path, r, d["seed"], fmt(R.seed)))
                logged = {k: Grid.from_log(d[k]) for k in ("orient", "wall", "floor")}
                if R.sub_grids is None:
                    R.sub_grids = logged
                else:
                    model.check(all(R.sub_grids[k].c == logged[k].c for k in logged),
                                "%s %08x LSUB grids differ from the modelled previous pass" % (path, r))
                    R.sub_grids = logged
                if R.nodes is None:
                    R.nodes = []          # sub_0066EEA0_RoomTileAlloc runs before the passes
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
            elif tag in ("O89", "O89D"):
                rooms[r].o89.append((tag, d))
            elif tag == "RACT":
                R = rooms[r]
                if r in pending:
                    td, _ = pending.pop(r)
                    if R.nodes is None:
                        R.nodes = []
                    R.ktile0 = R.draws
                    model.tiles_build(R, td)
                    R.built = True
                    model.check(not R.o89, "%s %08x %d O89 line(s) not consumed by the model" % (path, r, len(R.o89)))
                    R.k = R.draws
                    model.check(d["seed"] == fmt(R.seed),
                                "%s %08x RACT seed %s model %s (k model %d)" % (path, r, d["seed"], fmt(R.seed), R.k))
                    acts.append(R)
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
            elif tag == "RTFREE":
                R = rooms.get(r)
                if R is not None:
                    R.nodes = None
                    R.built = False
        except ModelError as e:
            model.check(False, "%s %s %08x: %s" % (path, tag, r or 0, e))
        except (KeyError, StopIteration) as e:
            model.check(False, "%s %s %08x: missing input (%r)" % (path, tag, r or 0, e))
    for r in pending:
        model.check(False, "%s %08x TINIT without RACT" % (path, r))
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


# ------------------------------------------------------------------------------ Phase 3: generators

GEN_TAGS = ("LC0", "LC1", "LI0", "LI1", "RC", "RL", "PIC", "PICX", "PIO", "MFR", "MFRX", "PRC", "PUR", "PURX",
            "MZ0", "MZ1", "OD0", "OD1", "LSR", "LSRX")
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
    def __init__(self, data, verbose=False):
        self.data = data
        self.verbose = verbose
        self.checks = self.fail = 0
        self.cov = {}
        self.prest_by_level = {}
        for i, rec in enumerate(excel_bin(data.root, "lvlprest")):
            lid = struct.unpack_from("<i", rec, 0x04)[0]
            self.prest_by_level.setdefault(lid, i)
        self.files = [struct.unpack_from("<i", r, 0x40)[0] for r in excel_bin(data.root, "lvlprest")]

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
        for line in open(path, errors="replace"):
            tag, _, rest = line.partition(" ")
            if tag == "LOGERR":
                self.check(False, "%s: logger error %s" % (path, rest.strip()))
                continue
            if tag not in GEN_TAGS:
                continue
            d = json.loads(rest)
            try:
                self.event(path, tag, d, levels, ps_level, ps_idx, lsr)
            except (KeyError, ModelError) as e:
                self.check(False, "%s %s: %r" % (path, tag, e))
            npre += 1
        return levels

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
        elif tag == "RC":
            if L.window is not None:
                self.hit("RoomCreate inside oracle window (%s)" % L.window)
                return
            self.check(seed_t(d["seed"]) == L.seed, "%s: seed before RoomCreate %s, model %s" % (where, d["seed"], fmt(L.seed)))
            L.seed = step(*L.seed)
            L.pending_rc = d["ret"]
            self.hit("RoomCreate modelled (one level draw)")
        elif tag == "RL":
            if L is None:
                return
            if L.window is None:
                self.check(seed_t(d["seed"]) == L.seed, "%s: seed at room link %s, model %s" % (where, d["seed"], fmt(L.seed)))
                lo = step(L.seed[0], INIT_HIGH)[0]
                self.check(d["r04"] == lo, "%s: room +0x04 %08x, model step(Init(level.lo)) %08x" % (where, d["r04"], lo))
            L.rooms.append(dict(d, window=L.window, prc=L.prc_n))
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
        elif tag == "PIO":
            ps_idx[d["ps"]] = d["idx"]           # outdoor cell bits 16-19: drlg/outdoor input
            self.hit("outdoor preset index set from the cell (input)")
        elif tag == "MFR":
            L.mfr = d
        elif tag == "MFRX":
            m = L.mfr
            idx = ps_idx[m["ps"]]
            if m["forced"] != -1:
                idx = m["forced"]
                self.hit("maze preset index forced by the maze cell (input)")
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
            L.prc = d
            L.prc_n += 1
        elif tag == "PUR":
            lv = d["seedp"] - 0x1C4
            L = levels.get(lv)
            self.check(L is not None, "%s: PresetUnitDropRolls on a seed that is not a level's" % path)
            self.check(seed_t(d["seed"]) == L.seed, "%s level %d: seed into the oracle sub_00667620 %s, model %s" % (path, L.id, d["seed"], fmt(L.seed)))
        elif tag == "PURX":
            L = levels[d["seedp"] - 0x1C4]
            out = seed_t(d["seed"])
            self.hit("oracle sub_00667620 calls (level seed), %s" % ("drew" if out != L.seed else "no draw"))
            L.seed = out
        elif tag in ("MZ0", "OD0"):
            self.check(seed_t(d["seed"]) == L.seed, "%s: seed into the %s oracle %s, model %s" % (where, tag, d["seed"], fmt(L.seed)))
            L.window = "maze" if tag == "MZ0" else "outdoor"
        elif tag in ("MZ1", "OD1"):
            L.seed = seed_t(d["seed"])
            L.window = None
            if tag == "MZ1":
                L.maze_list = d["rooms"]
                L.maze_pic = []
            self.hit("oracle window %s" % ("maze generator" if tag == "MZ1" else "outdoor act generator"))
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


def math_fmod(a, n):
    """C signed % (idiv): sign of the dividend."""
    q = abs(a) // abs(n)
    r = abs(a) - q * abs(n)
    return -r if a < 0 else r


def cmd_gen(argv):
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
    m = GenModel(Data(root, exe), verbose)
    for p in paths:
        levels = m.run(p)
        by = {}
        for L in levels.values():
            if L.inited:
                by.setdefault(L.drlg, []).append(L.id)
        print("%s: %d levels created; LevelInit by DrlgType: %s" % (p, len(levels), {k: sorted(v) for k, v in sorted(by.items())}))
    for k in sorted(m.cov):
        print("  coverage %-62s %d" % (k, m.cov[k]))
    print("gen: %d checks, %d mismatches" % (m.checks, m.fail))
    return 1 if m.fail else 0


def main(argv):
    cmds = {"roomk": cmd_roomk, "tables": cmd_tables, "p1cmp": cmd_p1cmp, "gen": cmd_gen}
    if len(argv) < 2 or argv[1] not in cmds:
        print(__doc__)
        return 2
    return cmds[argv[1]](argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))

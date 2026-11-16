"""Render maze levels as PNG images: an isometric tile composite and a top-down tile map per level.

Usage:
  python3 -I tools/maze_render.py log <root> <drlg-gen log> <out> [--scale N]
  python3 -I tools/maze_render.py gen <root> <out> <level> <seed> [<level> <seed> ...] [--scale N]

`log` draws the maze levels a tools/gdb/drlg-gen.gdb log recorded: the room rectangles of each level's
first MZ1 line and the preset file its PRC lines name. `gen` generates levels offline with the
tools/maze_replay.py reading model (docs/findings/drlg/0006-maze.md) from a chosen level seed, picks each
room's DS1 file as the conversion of docs/specs/drlg/README.md steps 9a/9b does (`convert`: newest room first,
the instance's level-seed draw, a forced index, else the per-build rotation of MAZE_DEF_BASE < Def < base + 16;
the level draws of step 5 between rooms) and draws them; it also writes <out>/gen.json. The seeds
are illustrative inputs, not the level seeds a given game seed produces (that link is plan 0022 Phase 2's).

<root> is the merged data tree (workspace/merged). Images go to <out>, which is disposable (ADR-0005) and
must stay under workspace/. --scale divides the tile size (default 4). Stdlib only.
"""
import collections
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds1  # noqa: E402
import palette  # noqa: E402
import png  # noqa: E402

MAP_PX = 6                        # top-down map: pixels per tile
MAP_RGB = [(0, 0, 0), (200, 190, 160), (70, 50, 40), (110, 110, 110)]   # empty, floor, wall, room border


def _excel(root):
    return os.path.join(root, "data", "global", "excel")


def level_names(root):
    names = {}
    with open(os.path.join(_excel(root), "levels.txt"), newline="", encoding="latin-1") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            try:
                names[int(row["Id"])] = row.get("LevelName") or row.get("Name")
            except (ValueError, TypeError):
                pass
    return names


class Renderer:
    def __init__(self, root, scale):
        self.root = root
        tiles_dir = os.path.join(root, "data", "global", "tiles")
        self.present = {os.path.relpath(p, tiles_dir).replace(os.sep, "/").lower(): p
                        for p in ds1.ds1_files(tiles_dir)}
        self.tiles = ds1._Tiles(root, scale)
        self.tw, self.th = ds1.TILE_W // scale, ds1.TILE_H // scale
        self.pad = 1024 // scale

    def _load(self, file):
        low = file.replace("\\", "/").lower()
        key = "data/global/tiles/"
        rel = low[low.find(key) + len(key):] if key in low else low
        return rel, ds1.parse(open(self.present[rel], "rb").read())

    def draw(self, rooms, base):
        """rooms: [((x, y, w, h), ds1 file)] in tile units. Writes <base>-iso.png and <base>-map.png."""
        x0 = min(r[0] for r, _ in rooms)
        y0 = min(r[1] for r, _ in rooms)
        gw = max(r[0] + r[2] for r, _ in rooms) + 1 - x0
        gh = max(r[1] + r[3] for r, _ in rooms) + 1 - y0
        cells = []                    # (gx, gy, kind, tile key, own dt1s)
        floor_map, wall_map = bytearray(gw * gh), bytearray(gw * gh)
        pal_name = None
        for (rx, ry, _rw, _rh), f in rooms:
            rel, d = self._load(f)
            pal_name = pal_name or palette.palette_for_tiles(rel)
            own = ds1._own_dt1s(d, self.tiles)
            layers = d["layers"]
            for name in layers:
                kind = "floor" if name.startswith("floor") else "wall" if name.startswith("wall") else None
                if not kind:
                    continue
                orients = layers.get("orient" + name[4:]) if kind == "wall" else None
                for cy in range(d["rows"]):
                    for cx in range(d["cols"]):
                        c = layers[name][cy * d["cols"] + cx]
                        if not c or c >> 31 or (kind == "floor" and ds1.blank_floor(c)):
                            continue
                        o = 0 if kind == "floor" else (orients[cy * d["cols"] + cx] if orients else 0)
                        if o in ds1.SKIP_ORIENT:
                            continue
                        gx, gy = rx - x0 + cx, ry - y0 + cy
                        if gx >= gw or gy >= gh:
                            continue
                        cells.append((gx, gy, kind, (o, (c >> 20) & 63, (c >> 8) & 63), own))
                        if o == 3:                   # second pick for orientation 4 (drlg/0001, 0x0066E9B0)
                            cells.append((gx, gy, kind, (4, (c >> 20) & 63, (c >> 8) & 63), own))
                        (floor_map if kind == "floor" else wall_map)[gy * gw + gx] = 1
        # isometric composite: floors first, then walls in depth order
        tw, th = self.tw, self.th
        W = (gw + gh) * tw // 2 + tw
        H = (gw + gh) * th // 2 + self.pad + th
        canvas = bytearray(W * H)
        ox, oy = gh * tw // 2, self.pad
        cells.sort(key=lambda c: (c[2] != "floor", c[0] + c[1]))
        for gx, gy, _kind, key, own in cells:
            runs, _ = self.tiles.lookup(key, own)
            if not runs:
                continue
            bx, by = ox + (gx - gy) * tw // 2, oy + (gx + gy) * th // 2
            for dy, dx, run in runs:
                y, x = by + dy, bx + dx
                if 0 <= y < H:
                    a, b = max(x, 0), min(x + len(run), W)
                    if a < b:
                        canvas[y * W + a:y * W + b] = run[a - x:b - x]
        png.write_indexed(base + "-iso.png", W, H, canvas, palette.load(self.root, pal_name))
        # top-down map: floor light, wall dark, room borders grey
        S = MAP_PX
        mw, mh = gw * S, gh * S
        px = bytearray(mw * mh)
        for gy in range(gh):
            for gx in range(gw):
                v = 2 if wall_map[gy * gw + gx] else 1 if floor_map[gy * gw + gx] else 0
                for yy in range(S):
                    row = (gy * S + yy) * mw + gx * S
                    px[row:row + S] = bytes([v]) * S
        for (rx, ry, rw, rh), _ in rooms:
            X, Y = (rx - x0) * S, (ry - y0) * S
            for i in range(rw * S):
                for yy in (Y, min(Y + rh * S, mh - 1)):
                    if X + i < mw:
                        px[yy * mw + X + i] = 3
            for j in range(rh * S):
                for xx in (X, min(X + rw * S, mw - 1)):
                    if Y + j < mh:
                        px[(Y + j) * mw + xx] = 3
        pal = bytes(sum((list(c) for c in MAP_RGB + [(0, 0, 0)] * (256 - len(MAP_RGB))), []))
        png.write_indexed(base + "-map.png", mw, mh, px, pal, transparent=())
        return gw, gh, W, H


def _report(lid, name, rooms, base, dims):
    gw, gh, W, H = dims
    print("level %d %s: %d rooms, grid %dx%d tiles -> %s-{iso,map}.png (%dx%d)"
          % (lid, name, len(rooms), gw, gh, base, W, H))


def from_log(root, log, out, scale):
    mazes, prc = collections.OrderedDict(), collections.defaultdict(dict)
    for line in open(log, encoding="latin-1"):
        tag, _, js = line.partition(" ")
        if tag == "MZ1":
            d = json.loads(js)
            mazes.setdefault(d["level"], d)
        elif tag == "PRC":
            d = json.loads(js)
            prc[d["level"]][tuple(d["prect"])] = d["file"]
    names, r = level_names(root), Renderer(root, scale)
    for lp, mz in mazes.items():
        rooms = [(tuple(x[2:6]), prc[lp].get(tuple(x[2:6]))) for x in mz["rooms"]]
        rooms = [(rc, f) for rc, f in rooms if f]
        if not rooms:
            print("level %d: no PRC files logged, skipped" % mz["id"])
            continue
        nm = names.get(mz["id"]) or "level"
        base = os.path.join(out, "maze-%d-%s" % (mz["id"], nm.replace(" ", "_")))
        _report(mz["id"], nm, rooms, base, r.draw(rooms, base))
    return 0


_PREST = {}


def _prest(root):
    """lvlprest.bin records by Def (the form the game reads), with the LvlPrest.txt Name."""
    if root not in _PREST:
        recs = {r["Def"]: dict(r) for r in ds1._tables(root)["lvlprest"]}
        rows = list(csv.reader(open(os.path.join(_excel(root), "lvlprest.txt"), encoding="latin-1"), delimiter="\t"))
        h = rows[0]
        for row in rows[1:]:
            if len(row) > 20 and row[h.index("Def")].strip().isdigit() and int(row[h.index("Def")]) in recs:
                recs[int(row[h.index("Def")])]["Name"] = row[h.index("Name")]
        _PREST[root] = recs
    return _PREST[root]


def convert(root, level_type, seed, rooms, units=None):
    """The maze-room conversion of docs/specs/drlg/README.md step 9: for each maze room in list order (newest first),
    9a PresetInstanceCreate (step 4: Range(L.seed, Files), one level draw iff Files >= 1), 9b MazePresetFile (forced
    index, else for MAZE_DEF_BASE[type] < Def < base + 16 the per-build rotation: first use RangeB(L.seed, Files),
    every use c <- (c + 1) mod Files), then step 5 PresetRoomsCreate's level draws (5a map scan drop rolls when Scan or
    Pops is set, preset.md steps 2a and 3; 5b one DRLG_RoomCreate draw per room: one room when the maze room is at most
    12 x 12, else the 8 x 8 split of the preset's size).

    seed: (lo, hi) level seed after the maze generator. rooms: [(x, y, w, h, def, forced index)] in conversion order.
    units: a tools/drlg.py PresetUnitData, made on first need. Returns ([{d, name, idx, file, draws, rooms, seed9,
    calc}], seed, units); draws counts the level draws, rooms the rooms step 5b creates (each also steps its own new
    seed once, rng/seeds step 5), seed9 is the level seed after 9b, calc are the step's calculation lines."""
    from rng import step
    prest, base = _prest(root), ds1.MAZE_DEF_BASE.get(level_type)
    rot, out = {}, []
    for x, y, w, h, d, forced in rooms:
        rec, calc, n0 = prest[d], [], 0
        n = rec["Files"]
        if n >= 1:
            seed = step(*seed)
            idx = seed[0] % n
            n0 += 1
            calc.append("9a, step 4 PresetInstanceCreate: Files %d, one level draw Range(L.seed, %d): lo %#010x mod %d "
                        "= %d." % (n, n, seed[0], n, idx))
        else:
            idx = 0
            calc.append("9a, step 4 PresetInstanceCreate: Files %d, no draw, index 0." % n)
        if forced != -1:
            idx = forced
            calc.append("9b MazePresetFile: forced index %d replaces it (the drawn value is spent)." % forced)
        elif base is None:
            calc.append("9b MazePresetFile: level type %d has no rotation base; the drawn index stays." % level_type)
        elif not base < d < base + 16:
            calc.append("9b MazePresetFile: Def %d is outside the rotation range (%d, %d); the drawn index stays."
                        % (d, base, base + 16))
        else:
            if d not in rot:
                if n < 1:
                    raise ValueError("Def %d rotates with Files %d (idiv by zero in MazePresetFile)" % (d, n))
                seed = step(*seed)
                rot[d] = [n, seed[0] % n]
                n0 += 1
                first = "first use of Def %d in this build: one level draw RangeB(L.seed, %d): lo %#010x mod %d = %d; " % (
                    d, n, seed[0], n, rot[d][1])
            else:
                first = "Def %d used before in this build, counter %d; " % (d, rot[d][1])
            c = (rot[d][1] + 1) % rot[d][0]
            calc.append("9b MazePresetFile: Def %d is in the rotation range (%d, %d); %sthe counter advances "
                        "(%d + 1) mod %d = %d and replaces the drawn index." % (d, base, base + 16, first, rot[d][1],
                                                                                 rot[d][0], c))
            rot[d][1] = idx = c
        s9 = seed
        f = rec["File%d" % (idx + 1)] if 0 <= idx < 6 else None
        f = f if f not in ("", "0") else None
        calc.append("The instance loads File%d of LvlPrest Def %d: %s." % (idx + 1, d, f or "none"))
        nd = 0
        if rec["Scan"] or rec["Pops"]:
            if f is None:
                raise ValueError("Def %d: map scan of an empty File cell" % d)
            if units is None:
                import drlg
                units = drlg.PresetUnitData(root, drlg.DEFAULT_EXE)
            _inst, seed, dr = units.drop_rolls(units.ds1(f)["units"], seed, x * 5, y * 5)
            nd = len(dr)
            calc.append("5a map scan (Scan %d, Pops %d): the DS1 is loaded and its keep/drop rolls run on the level "
                        "seed, %d draws (preset.md steps 2a, 3)." % (rec["Scan"], rec["Pops"], nd))
        pw, ph = (rec["SizeX"], rec["SizeY"]) if rec["SizeX"] and rec["SizeY"] else (w, h)
        nr = 1 if w <= 12 and h <= 12 else ((pw + 7) // 8 if pw > 0 else 0) * ((ph + 7) // 8 if ph > 0 else 0)
        for _ in range(nr):
            seed = step(*seed)
        calc.append("5b PresetRoomsCreate: %s; one level draw per room (DRLG_RoomCreate)." % (
            "one room (the maze room is %d x %d, at most 12 x 12)" % (w, h) if w <= 12 and h <= 12 else
            "%d rooms (%d x %d split 8 x 8)" % (nr, pw, ph)))
        out.append(dict(d=d, name=rec.get("Name"), idx=idx, file=f, draws=n0 + nd + nr, rooms=nr, seed9=s9,
                        calc=calc))
    return out, seed, units


def generate(root, pairs):
    """[(level id, seed)] -> [{level, seed, rooms: [{rect, def, name, file}]}] via the maze_replay model."""
    excel = _excel(root)
    saved, sys.argv = sys.argv, ["maze_replay.py", excel]    # maze_replay reads its excel dir at import
    try:
        import maze_replay as M
    finally:
        sys.argv = saved
    jobs, units = [], None
    for lid, seed in pairs:
        M.Room.n = 0
        L = M.Level(lid, M.Seed(seed & 0xFFFFFFFF, 0x29A))
        s = M.Seed(seed ^ 0x5bd1e995, 0x29A)
        first = M.Seed(s.step(), 666)
        first.step()
        M.run(L, first)
        conv, _s, units = convert(root, L.lt, (L.seed.lo, L.seed.hi),
                                  [(R.x, R.y, R.w, R.h, R.d, R.idx) for R in L.rooms], units)
        rooms = [{"rect": [R.x, R.y, R.w, R.h], "def": R.d, "name": q["name"], "file": q["file"]}
                 for R, q in zip(L.rooms, conv)]
        jobs.append({"level": lid, "seed": seed, "rooms": rooms})
    return jobs


def from_gen(root, out, pairs, scale):
    jobs = generate(root, pairs)
    with open(os.path.join(out, "gen.json"), "w") as fh:
        json.dump(jobs, fh, indent=1)
    names, r = level_names(root), Renderer(root, scale)
    for job in jobs:
        rooms = [(tuple(x["rect"]), x["file"]) for x in job["rooms"] if x["file"]]
        if not rooms:
            print("level %d seed %#x: no rooms with a preset file, skipped" % (job["level"], job["seed"]))
            continue
        nm = names.get(job["level"]) or "level"
        base = os.path.join(out, "gen-%d-%s-seed%x" % (job["level"], nm.replace(" ", "_"), job["seed"]))
        _report(job["level"], nm, rooms, base, r.draw(rooms, base))
    return 0


def main(argv):
    argv = list(argv)
    scale = 4
    if "--scale" in argv:
        i = argv.index("--scale")
        scale = int(argv[i + 1])
        del argv[i:i + 2]
    if len(argv) >= 4 and argv[0] == "log":
        _, root, log, out = argv[:4]
        os.makedirs(out, exist_ok=True)
        return from_log(root, log, out, scale)
    if len(argv) >= 5 and argv[0] == "gen" and len(argv[3:]) % 2 == 0:
        root, out = argv[1], argv[2]
        pairs = [(int(argv[i]), int(argv[i + 1], 0)) for i in range(3, len(argv), 2)]
        os.makedirs(out, exist_ok=True)
        return from_gen(root, out, pairs, scale)
    print(__doc__.strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

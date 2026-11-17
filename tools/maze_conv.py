"""The maze-room conversion of docs/specs/drlg/README.md step 9 (LvlPrest instance draws, MazePresetFile rotation, step 5
room draws), split out of tools/maze_render.py so that tools/maze_anim.py --schematic can use it without importing
anything that draws tiles. No art decoder is imported here. Stdlib only; reads the tables of the user's own files.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds1  # noqa: E402  (tables and MAZE_DEF_BASE only; no tile layer is read here)


def _excel(root):
    return os.path.join(root, "data", "global", "excel")


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

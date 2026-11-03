"""Largest DRLG room a stock level can have, against the path search's frame overrun (plan 0054, path/0002 § 9).

Usage:
  python3 -I tools/room_extent.py scan <merged-root> [--out DIR]
  python3 -I tools/room_extent.py manifest DIR [--write]

scan reads leveldefs.bin (DrlgType, SizeX/SizeY per difficulty), lvlmaze.bin (SizeX/SizeY), lvlprest.bin
(SizeX/SizeY, File1..6) and the DS1 files lvlprest.bin names (width and height from the header), and applies the
room rules of docs/findings/drlg/0003-generator-dispatch.md and drlg/0004-preset-units.md:

  preset rect (DrlgType 2): rooms of min(8, rest) x min(8, rest) tiles, so at most 8 x 8;
  outdoor level (DrlgType 3): one 8 x 8 room per cell;
  maze level (DrlgType 1): the room is LvlMaze SizeX x SizeY; a room of at most 12 x 12 is one room, a larger one
  is split into the 8 x 8 blocks.

A room's subtile rectangle is its tile rectangle x 5 (drlg/0005). The search's rectangle for a same-room request
is room + 20 on each axis (path/0002 § 2); it asserts when w*h > 50 000 and its clear covers (w + 6)(h + 6) cells of
a frame that holds 50 010 before the saved EBP (path/0002 § 9). The report prints the largest room, its levels and
the rectangle numbers, writes report.txt and the per-source tables to --out and a manifest.sha256. Stdlib only.
Read-only on the data tree.
"""
import hashlib
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import ds1 as ds1mod  # noqa: E402

SPLIT = 8                # tiles per block of the 8 x 8 split
SINGLE_MAX = 12          # a maze room of at most 12 x 12 tiles is kept whole
SUBTILES = 5             # subtiles per tile
MARGIN = 20              # the search rectangle's margin on each axis (room + 20)
ASSERT_AREA = 50000      # PathSearchRun asserts when w*h exceeds it
FRAME_CELLS = 50010      # cells from the grid start to the saved EBP
CLEAR_PAD = 6            # the clear covers (w + 6)(h + 6) cells
DRLG_MAZE, DRLG_PRESET, DRLG_OUTDOOR = 1, 2, 3


def maze_room(sx, sy):
    """Largest room (tiles) the maze builder keeps for a maze room of sx x sy tiles."""
    if sx <= SINGLE_MAX and sy <= SINGLE_MAX:
        return (sx, sy)
    return (min(SPLIT, sx), min(SPLIT, sy))


def split_room(sx, sy):
    """Largest room (tiles) of the 8 x 8 split of an sx x sy rect."""
    return (min(SPLIT, sx), min(SPLIT, sy))


def rect_numbers(wt, ht):
    """For a room of wt x ht tiles: the subtile room, the same-room search rectangle, its product and clear."""
    return rect_numbers_sub(wt * SUBTILES, ht * SUBTILES)


def threshold_square():
    """Smallest square room (subtiles) whose same-room rectangle overruns the frame while passing the assert."""
    n = 1
    while True:
        r = rect_numbers_sub(n, n)
        if r["overruns"] and not r["asserts"]:
            return n
        if r["asserts"]:
            return None
        n += 1


def rect_numbers_sub(w, h):
    rw, rh = w + MARGIN, h + MARGIN
    prod = rw * rh
    clear = (rw + CLEAR_PAD) * (rh + CLEAR_PAD)
    return dict(room=(w, h), rect=(rw, rh), product=prod, asserts=prod > ASSERT_AREA,
                clear=clear, overruns=clear > FRAME_CELLS)


def excel(root, name):
    d = open(os.path.join(root, "data", "global", "excel", name + ".bin"), "rb").read()
    n = struct.unpack_from("<I", d)[0]
    size = (len(d) - 4) // n
    if 4 + n * size != len(d):
        raise ValueError("%s.bin: size does not divide" % name)
    return [d[4 + i * size: 4 + (i + 1) * size] for i in range(n)]


def level_names(root):
    """Id -> Name from levels.txt (the .bin has no Name)."""
    with open(os.path.join(root, "data", "global", "excel", "levels.txt"), "rb") as f:
        rows = f.read().decode("latin-1").replace("\r\n", "\n").split("\n")
    head = rows[0].split("\t")
    ni, ii = head.index("Name"), head.index("Id")
    out = {}
    for r in rows[1:]:
        c = r.split("\t")
        if len(c) > max(ni, ii) and c[ii].lstrip("-").isdigit():
            out[int(c[ii])] = c[ni]
    return out


def scan(root):
    names = level_names(root)
    lv = []
    for i, r in enumerate(excel(root, "leveldefs")):
        drlg = struct.unpack_from("<I", r, 0x30)[0]
        sx = struct.unpack_from("<3i", r, 0x0C)
        sy = struct.unpack_from("<3i", r, 0x18)
        lv.append(dict(id=i, name=names.get(i, "?"), drlg=drlg, sx=sx, sy=sy))
    maze = {}
    for r in excel(root, "lvlmaze"):
        lid = struct.unpack_from("<I", r, 0)[0]
        sx, sy = struct.unpack_from("<ii", r, 0x10)
        maze.setdefault(lid, []).append((sx, sy))
    prest = []
    missing = 0
    for i, r in enumerate(excel(root, "lvlprest")):
        defn = struct.unpack_from("<i", r, 0)[0]
        sx, sy = struct.unpack_from("<ii", r, 0x28)
        files = [r[0x44 + 0x3C * k: 0x80 + 0x3C * k].split(b"\0", 1)[0].decode("latin-1") for k in range(6)]
        dims = []
        for fn in files:
            if not fn or fn == "0":     # an empty File slot is the text "0"
                continue
            p = os.path.join(root, "data", "global", "tiles", fn.replace("\\", "/").lower())
            if not os.path.isfile(p):
                missing += 1
                continue
            f = ds1mod.parse(open(p, "rb").read())
            dims.append((fn, f["size_x"], f["size_y"]))
        prest.append(dict(rec=i, defn=defn, sx=sx, sy=sy, ds1=dims))
    return lv, maze, prest, missing


def analyse(lv, maze, prest):
    """Rooms per source: (tiles w, tiles h, label). The maximum by area, ties by order of discovery."""
    rooms = []
    for L in lv:
        if L["drlg"] == DRLG_OUTDOOR:
            for d in range(3):
                if L["sx"][d] > 0 and L["sy"][d] > 0:
                    rooms.append(("outdoor", split_room(L["sx"][d], L["sy"][d]), "level %d %s diff %d (%dx%d)" % (
                        L["id"], L["name"], d, L["sx"][d], L["sy"][d])))
        elif L["drlg"] == DRLG_MAZE:
            for (sx, sy) in maze.get(L["id"], []):
                rooms.append(("maze", maze_room(sx, sy), "level %d %s (maze room %dx%d)" % (L["id"], L["name"], sx, sy)))
    for P in prest:
        if P["sx"] > 0 and P["sy"] > 0:
            rooms.append(("preset", split_room(P["sx"], P["sy"]), "lvlprest %d (%dx%d)" % (P["rec"], P["sx"], P["sy"])))
    return rooms


def report(root):
    lv, maze, prest, missing = scan(root)
    rooms = analyse(lv, maze, prest)
    best = max(r[1][0] * r[1][1] for r in rooms)
    top = [r for r in rooms if r[1][0] * r[1][1] == best]
    w, h = top[0][1]
    nums = rect_numbers(w, h)
    L = []
    L.append("levels=%d lvlmaze_levels=%d lvlprest=%d ds1_missing=%d" % (len(lv), len(maze), len(prest), missing))
    for kind in ("maze", "outdoor", "preset"):
        k = [r for r in rooms if r[0] == kind]
        if k:
            m = max(r[1][0] * r[1][1] for r in k)
            mm = max(k, key=lambda r: (r[1][0] * r[1][1]))
            L.append("%s: rooms=%d largest=%dx%d tiles (%s)" % (kind, len(k), mm[1][0], mm[1][1], mm[2]))
    L.append("lvlmaze SizeX/SizeY: max %dx%d" % (max(s[0] for v in maze.values() for s in v), max(s[1] for v in maze.values() for s in v)))
    L.append("lvlprest SizeX/SizeY: max %dx%d" % (max(p["sx"] for p in prest), max(p["sy"] for p in prest)))
    ds = [(d[1], d[2], d[0]) for p in prest for d in p["ds1"]]
    L.append("DS1 named by lvlprest: %d files; max size_x %d, max size_y %d" % (
        len(ds), max((d[0] for d in ds), default=0), max((d[1] for d in ds), default=0)))
    L.append("levels with DrlgType 3 (outdoor) max SizeX/SizeY: %dx%d" % (
        max(max(l["sx"]) for l in lv if l["drlg"] == DRLG_OUTDOOR), max(max(l["sy"]) for l in lv if l["drlg"] == DRLG_OUTDOOR)))
    L.append("LARGEST ROOM %dx%d tiles = %dx%d subtiles; %d sources:" % (w, h, w * SUBTILES, h * SUBTILES, len(top)))
    seen = set()
    for r in top:
        if r[2] not in seen:
            seen.add(r[2])
            L.append("  %s: %s" % (r[0], r[2]))
    L.append("same-room rectangle %dx%d, product %d (assert > %d: %s), clear %d (overrun > %d: %s)" % (
        nums["rect"][0], nums["rect"][1], nums["product"], ASSERT_AREA, nums["asserts"], nums["clear"], FRAME_CELLS, nums["overruns"]))
    t = threshold_square()
    L.append("smallest square room (subtiles) that overruns while passing the assert: %s = %s tiles" % (t, t / SUBTILES if t else None))
    L.append("headroom: largest room %d subtiles a side against %s" % (w * SUBTILES, t))
    return L, rooms, lv, maze, prest


def write_tables(out, lv, maze, prest):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "levels.tsv"), "w") as f:
        f.write("id\tname\tdrlgtype\tsizex\tsizey\tsizex_n\tsizey_n\tsizex_h\tsizey_h\tmaze_sizes\n")
        for L in lv:
            f.write("%d\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s\n" % (
                L["id"], L["name"], L["drlg"], L["sx"][0], L["sy"][0], L["sx"][1], L["sy"][1], L["sx"][2], L["sy"][2],
                ";".join("%dx%d" % s for s in maze.get(L["id"], []))))
    with open(os.path.join(out, "lvlprest.tsv"), "w") as f:
        f.write("rec\tdef\tsizex\tsizey\tds1_sizes\n")
        for p in prest:
            f.write("%d\t%d\t%d\t%d\t%s\n" % (p["rec"], p["defn"], p["sx"], p["sy"],
                                              ";".join("%dx%d" % (d[1], d[2]) for d in p["ds1"])))


def manifest(d, write):
    lines = []
    for fn in sorted(os.listdir(d)):
        p = os.path.join(d, fn)
        if os.path.isfile(p) and fn != "manifest.sha256":
            lines.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), fn))
    if write:
        open(os.path.join(d, "manifest.sha256"), "w").write("\n".join(lines) + "\n")
    return lines


def main(argv):
    if len(argv) >= 3 and argv[1] == "scan":
        out = None
        if "--out" in argv:
            out = argv[argv.index("--out") + 1]
        L, rooms, lv, maze, prest = report(argv[2])
        print("\n".join(L))
        if out:
            write_tables(out, lv, maze, prest)
            open(os.path.join(out, "report.txt"), "w").write("\n".join(L) + "\n")
            manifest(out, True)
        return 0
    if len(argv) >= 3 and argv[1] == "manifest":
        for ln in manifest(argv[2], "--write" in argv):
            print(ln)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

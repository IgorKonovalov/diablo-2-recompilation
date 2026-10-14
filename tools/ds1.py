"""Parse Diablo II DS1 preset maps and check them against LvlPrest.

Usage:
  python3 -I tools/ds1.py survey <root>               parse every .ds1 under <root>; histograms, failures
  python3 -I tools/ds1.py dump <file.ds1> [--cells]   print one file's header, lists and layer summary
  python3 -I tools/ds1.py lvlprest <root>             resolve lvlprest.bin File1..6 against <root>/data/global/tiles
  python3 -I tools/ds1.py units <root> [game.exe]     preset-unit, path, group and LvlPrest-column survey over
                                                      every DS1 lvlprest.bin names (plan 0016 Phase 0); object
                                                      ids < 150 are translated with g_Ds1ObjectIds from the
                                                      pinned game.exe (default <root>/../install/app/game.exe)
  python3 -I tools/ds1.py warps <root> [game.exe] [--quiet]
                                                      warp-slot survey (plan 0022 Phase 2): per LvlPrest record,
                                                      the slots 0..7, level points 30..33 and waypoint units its
                                                      DS1s carry, as DRLG_PresetMapScan reads them (drlg/0007 § 1);
                                                      records the maze code places, per level type, beside the
                                                      levels' Vis/Warp; --quiet drops the per-record lines
  python3 -I tools/ds1.py objects <root> [game.exe] [--quiet]
                                                      object-class survey (plan 0023 Phase 2 prep): the
                                                      LvlPrest records whose DS1s place objects 269, 397,
                                                      455, 573 and the pseudo-objects 574..582 (after the
                                                      DS1_Parse id mapping); --quiet drops the per-record lines
  python3 -I tools/ds1.py render <root> [out] [--all] [--hidden] [--only SUBSTR]
                                                      isometric floor+wall preview of every DS1 that
                                                      lvlprest.bin names (--all: every DS1) to
                                                      <out>/ds1/<path>.png (default out: workspace/render);
                                                      --hidden also draws bit-31 cells

<root> is a merged data tree (e.g. workspace/merged). Layout in docs/formats/ds1.md. All fields are
little-endian 32-bit. Header, then layers of (size_x+1) x (size_y+1) u32 cells, then the object list,
the substitution-group list and the NPC-path list, each present from some file version on. survey
exits 0 only if every file parses and ends exactly at its last byte, except the KNOWN_MALFORMED
files, which must fail exactly as recorded. lvlprest exits 0 only if every File1..6 resolves.
render (the only subcommand that writes) is an illustration, not DRLG behaviour: see
docs/formats/ds1.md, Preview. Stdlib only.
"""
import collections
import os
import struct
import sys

SUBST_TYPES = (1, 2)   # tag_type values that carry a substitution layer and group list


class Ds1Error(ValueError):
    pass


class Reader:
    def __init__(self, data):
        self.d, self.p = data, 0

    def i32(self):
        if self.p + 4 > len(self.d):
            raise Ds1Error("read past end at 0x%X" % self.p)
        v = struct.unpack_from("<i", self.d, self.p)[0]
        self.p += 4
        return v

    def u32s(self, n):
        if n < 0 or self.p + 4 * n > len(self.d):
            raise Ds1Error("array of %d u32 past end at 0x%X" % (n, self.p))
        v = struct.unpack_from("<%dI" % n, self.d, self.p)
        self.p += 4 * n
        return v

    def cstr(self):
        end = self.d.find(b"\0", self.p)
        if end < 0:
            raise Ds1Error("unterminated string at 0x%X" % self.p)
        s = self.d[self.p:end].decode("latin-1")
        self.p = end + 1
        return s


def parse(data):
    """Return a dict with every field of the file. Raises Ds1Error on a short or malformed file."""
    r = Reader(data)
    f = {"version": r.i32()}
    v = f["version"]
    f["size_x"] = r.i32()             # = LvlPrest SizeX / SizeY; the cell grid is one larger
    f["size_y"] = r.i32()
    f["cols"], f["rows"] = f["size_x"] + 1, f["size_y"] + 1
    if not (0 < f["cols"] <= 1024 and 0 < f["rows"] <= 1024):
        raise Ds1Error("implausible size %d x %d" % (f["size_x"], f["size_y"]))
    f["act"] = r.i32() if v >= 8 else None          # stored 0-based
    f["tag_type"] = r.i32() if v >= 10 else 0
    f["files"] = [r.cstr() for _ in range(r.i32())] if v >= 3 else []
    f["unk_skip"] = (r.i32(), r.i32()) if 9 <= v <= 13 else None
    if v >= 4:
        f["wall_layers"] = r.i32()
        f["floor_layers"] = r.i32() if v >= 16 else 1
    else:
        f["wall_layers"] = f["floor_layers"] = 1
    if not (0 <= f["wall_layers"] <= 64 and 0 <= f["floor_layers"] <= 64):
        raise Ds1Error("implausible layer counts %d/%d" % (f["wall_layers"], f["floor_layers"]))
    has_subst = v < 4 or f["tag_type"] in SUBST_TYPES
    # Stream order of the cell layers.
    if v < 4:
        order = ["wall0", "floor0", "orient0", "subst", "shadow"]
    else:
        order = []
        for i in range(f["wall_layers"]):
            order += ["wall%d" % i, "orient%d" % i]
        order += ["floor%d" % i for i in range(f["floor_layers"])]
        order.append("shadow")
        if has_subst:
            order.append("subst")
    n = f["cols"] * f["rows"]
    f["layers"] = collections.OrderedDict((name, r.u32s(n)) for name in order)

    f["objects"] = []
    if v >= 2:
        for _ in range(r.i32()):
            o = {"type": r.i32(), "id": r.i32(), "x": r.i32(), "y": r.i32()}
            o["flags"] = r.i32() if v >= 6 else None
            f["objects"].append(o)

    f["groups"], f["group_unk"] = [], None
    if v >= 12 and f["tag_type"] in SUBST_TYPES:
        if v >= 18:
            f["group_unk"] = r.i32()
        for _ in range(r.i32()):
            g = {"x": r.i32(), "y": r.i32(), "w": r.i32(), "h": r.i32()}
            g["unk"] = r.i32() if v >= 13 else None
            f["groups"].append(g)

    # v12..13 only: one more dword after the group list (0 in every such file).
    f["unk_trailer"] = r.i32() if 12 <= v <= 13 else None

    f["paths"] = []
    if v >= 14:
        for _ in range(r.i32()):
            npts, x, y = r.i32(), r.i32(), r.i32()
            if not 0 <= npts <= 4096:
                raise Ds1Error("implausible path length %d" % npts)
            pts = []
            for _ in range(npts):
                pt = (r.i32(), r.i32()) + ((r.i32(),) if v >= 15 else ())
                pts.append(pt)
            f["paths"].append({"x": x, "y": y, "points": pts})

    f["leftover"] = len(data) - r.p
    return f


def ds1_files(root):
    for d, _, names in os.walk(root):
        for name in sorted(names):
            if name.lower().endswith(".ds1"):
                yield os.path.join(d, name)


# Files that do not parse cleanly, with the failure the parser must reproduce. None is named by
# LvlPrest.txt File1..6 (docs/formats/ds1.md, "Malformed files").
KNOWN_MALFORMED = {
    "data/global/tiles/act1/outdoors/swamp2.ds1": "leftover 44",
    "data/global/tiles/act1/outdoors/trees.ds1": "short",
    "data/global/tiles/expansion/siege/xtransition.ds1": "short",
}

CELL_FIELDS = [("b0..7", 0, 8), ("b8..13", 8, 6), ("b14..19", 14, 6), ("b20..25", 20, 6),
               ("b26..30", 26, 5), ("b31", 31, 1)]


def _status(data):
    try:
        f = parse(data)
    except Ds1Error as e:
        return None, "short", str(e)
    if f["leftover"]:
        return f, "leftover %d" % f["leftover"], ""
    return f, "ok", ""


def _show(stats, key, limit=24):
    items = sorted(stats[key].items(), key=lambda kv: (-kv[1], str(kv[0])))
    print("%-24s %3d distinct: %s%s" % (key, len(items), ", ".join("%s=%d" % kv for kv in items[:limit]),
                                       " ..." if len(items) > limit else ""))


def survey(root):
    hist = collections.Counter()
    ok = expected = unexpected = nfiles = 0
    nobj = npath = leftover = 0
    tiles = os.path.join(root, "data", "global", "tiles")
    tile_files = {os.path.relpath(os.path.join(d, n), root).replace(os.sep, "/").lower()
                  for d, _, names in os.walk(tiles) for n in names}
    s = collections.defaultdict(collections.Counter)
    for path in ds1_files(root):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        data = open(path, "rb").read()
        nfiles += 1
        f, status, msg = _status(data)
        if f is not None:
            leftover += f["leftover"]
        want = KNOWN_MALFORMED.get(rel.lower())
        if status != "ok":
            if want == status:
                expected += 1
                print("expected anomaly %s: %s (version %d)" % (rel, status, struct.unpack_from("<i", data)[0]))
            else:
                unexpected += 1
                print("FAIL %s: %s %s" % (rel, status, msg))
            continue
        if want:
            unexpected += 1
            print("FAIL %s: listed as malformed (%s) but parses cleanly" % (rel, want))
        ok += 1
        nobj += len(f["objects"])
        npath += len(f["paths"])
        v = f["version"]
        hist[v] += 1
        top = rel.split("/")[3] if rel.count("/") >= 4 else "?"
        s["act (dir, stored)"][(top, f["act"])] += 1
        s["tag_type (ver, value)"][(v, f["tag_type"])] += 1
        s["layers (walls, floors)"][(f["wall_layers"], f["floor_layers"])] += 1
        s["file count"][len(f["files"])] += 1
        for name in f["files"]:
            low = name.replace("\\", "/").lower()
            k = low.find("data/global/tiles/")
            s["file prefix"][low[:k] if k >= 0 else "(none)"] += 1
            s["file extension"][os.path.splitext(low)[1]] += 1
            if k >= 0:
                dt1 = os.path.splitext(low[k:])[0] + ".dt1"
                s["file resolves as .dt1"][dt1 in tile_files] += 1
                if dt1 not in tile_files:
                    s["file missing (.dt1)"][dt1] += 1
        for i in range(f["wall_layers"]):
            for w, o in zip(f["layers"]["wall%d" % i], f["layers"]["orient%d" % i]):
                s["(wall==0, orient==0)"][(w == 0, o == 0)] += 1
        s["grid cols"][f["cols"]] += 1
        s["unk_skip"][f["unk_skip"]] += 1
        s["unk_trailer"][f["unk_trailer"]] += 1
        s["group_unk"][(v, f["group_unk"])] += 1
        s["group count"][len(f["groups"])] += 1
        for g in f["groups"]:
            s["group.unk"][g["unk"]] += 1
        if f["tag_type"] in SUBST_TYPES:
            cells = set(f["layers"]["subst"])
            s["subst cells within 0..groups"][max(cells) <= len(f["groups"])] += 1
        for o in f["objects"]:
            s["object.type"][o["type"]] += 1
            s["object.flags"][o["flags"]] += 1
            s["object inside map"][0 <= o["x"] < 5 * f["cols"] and 0 <= o["y"] < 5 * f["rows"]] += 1
        s["path count"][len(f["paths"])] += 1
        objpos = collections.Counter((o["x"], o["y"]) for o in f["objects"])
        for p in f["paths"]:
            s["path at an object"][objpos[(p["x"], p["y"])] > 0] += 1
            s["path.points"][len(p["points"])] += 1
            for pt in p["points"]:
                if len(pt) == 3:
                    s["path.action"][pt[2]] += 1
        for name, cells in f["layers"].items():
            kind = name.rstrip("0123456789")
            for c in cells:
                s[kind + " zero"][c == 0] += 1
                if kind in ("orient", "subst"):
                    s[kind + " value"][c] += 1
                elif c:
                    for fname, shift, width in CELL_FIELDS:
                        s["%s %s" % (kind, fname)][(c >> shift) & ((1 << width) - 1)] += 1
    print("parsed cleanly %d, expected anomalies %d, unexpected failures %d" % (ok, expected, unexpected))
    print("version histogram (clean files):", " ".join("%d:%d" % kv for kv in sorted(hist.items())))
    for key in sorted(s):
        _show(s, key)
    # gate summary (tools/gate.py --full): integer counts only; objects/paths over clean files
    print("SURVEY ds1 files=%d parsed=%d malformed=%d errors=%d objects=%d paths=%d leftover_bytes=%d"
          % (nfiles, ok, expected, unexpected, nobj, npath, leftover))
    return 1 if unexpected or expected != len(KNOWN_MALFORMED) else 0


def dump(path, cells=False):
    f = parse(open(path, "rb").read())
    for k in ("version", "size_x", "size_y", "act", "tag_type", "unk_skip", "wall_layers", "floor_layers",
              "group_unk", "unk_trailer", "leftover"):
        print("%-13s %s" % (k, f[k]))
    for i, name in enumerate(f["files"]):
        print("file[%d]      %s" % (i, name))
    for name, layer in f["layers"].items():
        nz = sum(1 for c in layer if c)
        print("layer %-8s %d non-zero of %d" % (name, nz, len(layer)))
        if cells:
            w = f["cols"]
            for y in range(f["rows"]):
                print("  " + " ".join("%08X" % c for c in layer[y * w:(y + 1) * w]))
    for o in f["objects"]:
        print("object type=%d id=%d x=%d y=%d flags=%s" % (o["type"], o["id"], o["x"], o["y"], o["flags"]))
    for g in f["groups"]:
        print("group x=%d y=%d w=%d h=%d unk=%s" % (g["x"], g["y"], g["w"], g["h"], g["unk"]))
    for p in f["paths"]:
        print("path at (%d,%d), %d points: %s" % (p["x"], p["y"], len(p["points"]), p["points"]))


def lvlprest(root):
    """Resolve File1..6 of every lvlprest.bin record (the form the game loads; the layout in
    excel_layouts.py diffs clean against LvlPrest.txt) against the .ds1 files under data/global/tiles."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import excel_bin
    import excel_layouts
    excel = os.path.join(root, "data", "global", "excel")
    lay = {f["col"]: f for f in excel_layouts.LAYOUTS["lvlprest"]["fields"] if "col" in f}
    recs, _ = excel_bin.read_bin(excel_bin.find_file(excel, "lvlprest", ".bin"))
    tiles = os.path.join(root, "data", "global", "tiles")
    present = {os.path.relpath(p, tiles).replace(os.sep, "/").lower(): p for p in ds1_files(tiles)}
    refs = hits = 0
    used, misses = set(), []
    files_mismatch = []
    for rec in recs:
        rid = excel_bin.decode_field(rec, lay["Def"])
        names = [excel_bin.decode_field(rec, lay["File%d" % i]) for i in range(1, 7)]
        named = [n for n in names if n not in ("", "0")]
        if len(named) != excel_bin.decode_field(rec, lay["Files"]):
            files_mismatch.append((rid, excel_bin.decode_field(rec, lay["Files"]), len(named)))
        for i, cell in enumerate(names, 1):
            if cell in ("", "0"):
                continue
            refs += 1
            key = cell.replace("\\", "/").lower()
            if key in present:
                hits += 1
                used.add(key)
            else:
                misses.append((rid, "File%d" % i, cell))
    print("lvlprest.bin records %d; File1..6 references %d, resolved %d, missing %d"
          % (len(recs), refs, hits, len(misses)))
    for m in misses:
        print("MISS Def=%d %s %s" % m)
    print("distinct .ds1 referenced %d of %d present; %d present but unreferenced"
          % (len(used), len(present), len(present) - len(used)))
    vers = collections.Counter(struct.unpack_from("<i", open(present[k], "rb").read(4))[0] for k in used)
    print("versions of referenced files:", " ".join("%d:%d" % kv for kv in sorted(vers.items())))
    bad = sorted(k for k in used if "data/global/tiles/" + k in KNOWN_MALFORMED)
    print("referenced files listed as malformed: %d" % len(bad))
    print("records whose Files count differs from the non-blank File1..6 cells: %d %s"
          % (len(files_mismatch), files_mismatch[:10]))
    return 1 if misses or bad else 0


def lvlprest_names(root):
    """Lower-case paths (relative to data/global/tiles) of every .ds1 that lvlprest.bin File1..6 names."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import excel_bin
    import excel_layouts
    excel = os.path.join(root, "data", "global", "excel")
    lay = {f["col"]: f for f in excel_layouts.LAYOUTS["lvlprest"]["fields"] if "col" in f}
    recs, _ = excel_bin.read_bin(excel_bin.find_file(excel, "lvlprest", ".bin"))
    out = set()
    for rec in recs:
        for i in range(1, 7):
            cell = excel_bin.decode_field(rec, lay["File%d" % i])
            if cell not in ("", "0"):
                out.add(cell.replace("\\", "/").lower())
    return out


# ---------------------------------------------------------------------------------------- units survey
# Plan 0016 Phase 0. Data-side survey of the preset units, substitution groups and LvlPrest columns,
# with the DS1_Parse unit mapping as drlg/0001 reads it ([I]): MonPreset per act (header act, clamped
# to 4), the act-index-2 and act-index-4 rewrites of MonStats ids into objects (drlg/0004), object ids < 150
# through g_Ds1ObjectIds (read from the pinned game.exe when it is present), paths owned by the last unit in
# file order at the path's (x, y).

UNIT_TYPES = {1: "monster", 2: "object", 4: "item"}
DS1_OBJECT_IDS = 0x00748AD8                        # data:g_Ds1ObjectIds, s32[5][150] (drlg/0001)
# DS1_Parse's act rewrites (0x00665CB2, drlg/0004 § Where the unit list comes from): by act index, a MonStats
# id after the MonPreset mapping -> object row; the unit becomes type 2, mode 0. Act index 2: natalya 297 -> 382,
# compellingorb 366 -> 404. Act index 4: nihlathak 514 -> 461, ancientstatue1..3 537..539 -> 1013 - id.
ACT2_REWRITES = {297: 382, 366: 404}
ACT4_REWRITES = {0x202: 0x1CD, 0x219: 0x3F5 - 0x219, 0x21A: 0x3F5 - 0x21A, 0x21B: 0x3F5 - 0x21B}
ACT_REWRITES = {2: ACT2_REWRITES, 4: ACT4_REWRITES}
LVLPREST_COLS = ["Populate", "Logicals", "Outdoors", "Animate", "KillEdge", "FillBlanks", "Expansion",
                 "unk_024", "SizeX", "SizeY", "AutoMap", "Scan", "Pops", "PopPad", "Files", "Dt1Mask"]
DRLG_KIND = {1: "maze", 2: "preset", 3: "outdoor"}  # Levels.DrlgType value -> generator (drlg/0003)
# sub_006738C0_MazePresetFile: first Def of the maze rotation range by level type (drlg/0003, tools/drlg.py)
MAZE_DEF_BASE = {3: 0x34, 4: 0x6C, 7: 0xA7, 8: 0xCD, 10: 0x101, 13: 0x12D, 17: 0x19D, 18: 0x1E1, 22: 0x2F1,
                 24: 0x298, 25: 0x2C0, 28: 0x344, 33: 0x3EA, 34: 0x422, 35: 0x41C}


def _tables(root):
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import excel_bin
    import excel_layouts
    excel = os.path.join(root, "data", "global", "excel")

    def load(name):
        lay = {f.get("name", f.get("col")): f for f in excel_layouts.LAYOUTS[name]["fields"]
               if "col" in f or "name" in f}
        recs, _ = excel_bin.read_bin(excel_bin.find_file(excel, name, ".bin"))
        return [{k: excel_bin.decode_field(r, f) for k, f in lay.items()} for r in recs]
    t = {n: load(n) for n in ("lvlprest", "levels", "leveldefs", "lvltypes", "lvlsub", "monpreset")}
    t["n_monstats"] = len(excel_bin.read_bin(excel_bin.find_file(excel, "monstats", ".bin"))[0])
    t["n_superuniques"] = len(excel_bin.read_bin(excel_bin.find_file(excel, "superuniques", ".bin"))[0])
    hp, mon_rows = excel_bin.read_txt(excel_bin.find_file(excel, "monstats", ".txt"))
    ci, ni = hp.index("Id"), hp.index("npc")
    ids = list(dict.fromkeys(r[ci] for r in mon_rows))       # distinct-Id ordinals, as the .bin stores them
    npc = {}
    for r in mon_rows:
        npc.setdefault(r[ci], r[ni] == "1")
    t["mon_npc"] = [npc[i] for i in ids]
    t["mon_names"] = ids
    return t


def _object_table(exe):
    """g_Ds1ObjectIds from the pinned game.exe, or None when it is absent."""
    if not exe or not os.path.exists(exe):
        return None
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import hashlib
    import drlg
    if hashlib.sha256(open(exe, "rb").read()).hexdigest() != drlg.PINNED:
        raise Ds1Error("%s is not the pinned game.exe" % exe)
    v = struct.unpack("<750i", drlg.exe_read(exe, DS1_OBJECT_IDS, 3000))
    return [list(v[a * 150:(a + 1) * 150]) for a in range(5)]


def _dt1_key(name):
    low = name.replace("\\", "/").lower()
    k = low.find("data/global/tiles/")
    if k < 0:
        return None
    return os.path.splitext(low[k + len("data/global/tiles/"):])[0] + ".dt1"


def _units(f, t, objtab):
    """DS1_Parse's unit list for a parsed file (file order): dicts with type, raw id, id, range, path."""
    v = f["version"]
    act = min(f["act"] or 0, 4) if v >= 8 else 0
    lists = collections.defaultdict(list)
    for r in t["monpreset"]:
        lists[r["Act"] - 1].append(r)
    nm, ns = t["n_monstats"], t["n_superuniques"]
    out = []
    for o in f["objects"]:
        u = dict(o, act=act, raw=o["id"], rng=None)
        if o["type"] == 1:
            if v <= 4:
                u["id"], u["rng"] = -1, "dropped (v<5)"
            else:
                lst = lists.get(act, [])
                if o["id"] < len(lst):
                    kind, idx = lst[o["id"]]["PlaceKind"], lst[o["id"]]["Place"]
                    u["id"], u["rng"] = {1: (idx, "MonStats"), 2: (nm + idx, "SuperUniques"),
                                         0: (nm + ns + idx, "MonPlace")}.get(kind, (-1, "bad kind"))
                else:
                    u["rng"] = "raw (id >= act count)"
                rw = ACT_REWRITES.get(act, {})
                if 0 <= u["id"] < nm and u["id"] in rw:     # only MonStats-range ids (DS1_Parse)
                    u["rewrite"] = (u["id"], rw[u["id"]])
                    u["type"], u["id"], u["mode"], u["rng"] = 2, rw[u["id"]], 0, "act rewrite"
        elif o["type"] == 2:
            if v < 6:
                u["id"] = -1 if o["id"] == 0x23D else o["id"]
                u["rng"] = "raw (v<6)"
            elif o["id"] < 150:
                u["id"] = objtab[act][o["id"]] if objtab else None
                u["rng"] = "table"
            else:
                u["id"], u["rng"] = o["id"] - 150, "direct (id-150)"
        else:
            u["id"], u["rng"] = o["id"], "other type"
        u["paths"] = []
        out.append(u)
    for p in f["paths"]:
        owner = None
        for u in out:                      # the list is prepended, so the first match is the last in file order
            if (u["x"], u["y"]) == (p["x"], p["y"]) and (u["id"] is None or u["id"] >= 0):
                owner = u
        if owner is not None and p["points"]:
            owner["paths"].append(p)
    return out


def _classify(t):
    """Generator kind of each LvlPrest record, from data only (see docs/tables/LvlPrest.md § Survey):
    'preset' for a record with LevelId (its level's DrlgType is checked), else the DrlgType of the level
    types that best cover the DT1s its DS1s name under its Dt1Mask (preset levels left out: they take
    their own LevelId record)."""
    levels = {r["Id"]: (r, d) for r, d in zip(t["levels"], t["leveldefs"])}
    by_type = collections.defaultdict(set)
    for r, d in levels.values():
        by_type[d["LevelType"]].add(d["DrlgType"])
    ltfiles = [[(r["File %d" % (i + 1)] or "").replace("\\", "/").lower() for i in range(32)]
               for r in t["lvltypes"]]
    return levels, by_type, ltfiles


def units_survey(root, exe=None):
    t = _tables(root)
    objtab = _object_table(exe)
    if objtab is None:
        print("NOTE no pinned game.exe at %s: object ids < 150 are not translated, so the table -1 check "
              "does not run (objtab=0 in the SURVEY line)" % exe)
    tiles = os.path.join(root, "data", "global", "tiles")
    present = {os.path.relpath(p, tiles).replace(os.sep, "/").lower(): p for p in ds1_files(tiles)}
    levels, by_type, ltfiles = _classify(t)
    parsed, errors = {}, 0

    def get(rel):
        nonlocal errors
        if rel not in parsed:
            data = open(present[rel], "rb").read()
            f, status, msg = _status(data)
            want = KNOWN_MALFORMED.get("data/global/tiles/" + rel)
            if status != "ok" and want != status:
                errors += 1
                print("FAIL %s: %s %s" % (rel, status, msg))
            parsed[rel] = f
        return parsed[rel]

    # ---- references and generator kind per record
    refs, recs = [], t["lvlprest"]
    first_by_level = {}
    for r in recs:
        if r["LevelId"]:
            first_by_level.setdefault(r["LevelId"], r["Def"])
    kind_of, kind_detail = {}, collections.Counter()
    for r in recs:
        names = [(i, r["File%d" % i].replace("\\", "/").lower()) for i in range(1, 7)
                 if r["File%d" % i] not in ("", "0")]
        for i, n in names:
            if n not in present:
                errors += 1
                print("FAIL Def=%d File%d %s: not present" % (r["Def"], i, n))
            else:
                refs.append((r, i, n))
        if r["LevelId"]:
            d = levels[r["LevelId"]][1]["DrlgType"]
            k = "preset" if d == 2 else "LevelId of DrlgType %d" % d
            kind_detail["LevelId: level DrlgType %d, %s" % (
                d, "first record" if first_by_level[r["LevelId"]] == r["Def"] else "not first")] += 1
        else:
            need = set()
            for _, n in names:
                if n in present and get(n):
                    need |= {k for k in map(_dt1_key, get(n)["files"]) if k}
            mask = r["Dt1Mask"]
            score = {}
            for ti, files in enumerate(ltfiles):
                bits = [b for b in range(32) if mask >> b & 1]
                if bits and all(files[b] not in ("", "0") for b in bits):
                    score[ti] = len(need & {files[b] for b in bits})
            top = max(score.values(), default=0)
            kinds = set()
            for ti, sc in score.items():
                if sc == top and (top or not need):
                    kinds |= by_type[ti] - {2}
            if len(kinds) > 1 and any(b < r["Def"] < b + 16 for b in MAZE_DEF_BASE.values()):
                kinds &= {1}                # a maze rotation Def (drlg/0003) settles a shared level type
            if not names:
                k = "no file"
            elif len(kinds) == 1:
                k = DRLG_KIND.get(next(iter(kinds)), "DrlgType %d" % next(iter(kinds)))
            elif not kinds:
                k = "unmatched"
            else:
                k = "|".join(DRLG_KIND[d] for d in sorted(kinds))
            kind_detail["no LevelId: %s" % k] += 1
        kind_of[r["Def"]] = k
    print("LvlPrest records %d, File1..6 references %d (resolved), distinct files %d"
          % (len(recs), len(refs), len({n for _, _, n in refs})))
    for k, n in sorted(kind_detail.items()):
        print("  kind %-48s %d" % (k, n))

    # maze rotation ranges (drlg/0003) against the data classification
    rot = collections.Counter()
    for r in recs:
        if any(b < r["Def"] < b + 16 for b in MAZE_DEF_BASE.values()):
            rot[kind_of[r["Def"]]] += 1
    print("records in a maze rotation range (base < Def < base+16), by data kind:",
          ", ".join("%s=%d" % kv for kv in sorted(rot.items())))

    # ---- LvlPrest columns per generator kind
    print("\nLvlPrest columns by generator kind (value=records)")
    kinds = sorted(set(kind_of.values()))
    for col in LVLPREST_COLS:
        for k in kinds:
            c = collections.Counter(r[col] for r in recs if kind_of[r["Def"]] == k)
            items = sorted(c.items())
            shown = ", ".join("%s=%d" % kv for kv in items[:12]) + (" ..." if len(items) > 12 else "")
            print("  %-10s %-12s %3d distinct: %s" % (col, k, len(items), shown))
    for k in kinds:
        c = collections.Counter((r["Files"], sum(r["File%d" % i] not in ("", "0") for i in range(1, 7)))
                                for r in recs if kind_of[r["Def"]] == k)
        bad = sum(n for (a, b), n in c.items() if a != b)
        print("  Files!=named %-10s %d of %d" % (k, bad, sum(c.values())))

    # ---- units per act and type, over distinct referenced files
    files = sorted({n for _, _, n in refs})
    kinds_by_file = collections.defaultdict(set)
    for r, _, n in refs:
        kinds_by_file[n].add(kind_of[r["Def"]])
    s = collections.defaultdict(collections.Counter)
    tot = collections.Counter()
    for n in files:
        f = get(n)
        if f is None:
            continue
        us = _units(f, t, objtab)
        for u in us:
            a = u["act"] + 1
            tname = UNIT_TYPES.get(u["type"], "type %d" % u["type"])
            if u["type"] == 1 and u["rng"] == "MonStats" and t["mon_npc"][u["id"]]:
                tname = "npc"
            tot[tname] += 1
            s["units (act, type)"][(a, tname)] += 1
            raw_t = tname
            if "rewrite" in u:                                  # raw ids by the entry's own type
                raw_t = "npc" if t["mon_npc"][u["rewrite"][0]] else "monster"
            s["_raw"][(a, raw_t, u["raw"])] += 1
            if "rewrite" in u:
                s["act rewrites (act, file, monster id, object, paths)"][(a, n) + u["rewrite"] + (len(u["paths"]),)] += 1
            if u["type"] == 1:
                s["monster range (act, range)"][(a, u["rng"])] += 1
                if u["rng"] == "MonPlace":
                    s["MonPlace rows hit (act, row)"][(a, u["id"] - t["n_monstats"] - t["n_superuniques"])] += 1
            if u["type"] == 1 and u["rng"] in ("MonStats", "SuperUniques"):
                s["_mon"][(a, u["rng"], u["id"])] += 1
            if u["type"] == 2:
                s["object id route (act, route)"][(a, u["rng"])] += 1
                if u["id"] is not None:
                    s["_obj"][(a, "object", u["id"])] += 1
                if u["id"] is not None and u["id"] < 0:
                    s["object dropped (table -1) (act, raw)"][(a, u["raw"])] += 1
            s["flags (type, flags)"][(tname, u["flags"])] += 1
            if u["flags"]:
                s["flags!=0 (file, type, raw id)"][(n, tname, u["raw"])] += 1
            s["paths per unit (type, n)"][(tname, len(u["paths"]))] += 1
            for p in u["paths"]:
                tot["paths"] += 1
                tot["path points"] += len(p["points"])
                for pt in p["points"]:
                    s["path action (act, type, action)"][(a, tname, pt[2] if len(pt) == 3 else 1)] += 1
        owned = sum(len(u["paths"]) for u in us)
        if len(f["paths"]) != owned:
            s["paths not attached (file)"][n] += len(f["paths"]) - owned
        s["paths per file kind (kind, count>0)"][(tuple(sorted(kinds_by_file[n])), len(f["paths"]) > 0)] += 1
    print("\nunit totals:", ", ".join("%s=%d" % kv for kv in sorted(tot.items())))
    rng = collections.defaultdict(list)
    for (a, tn, raw), c in s.pop("_raw").items():
        rng[(a, tn)] += [raw] * c
    print("raw id range (act, type): min..max/distinct:",
          ", ".join("%s=%d..%d/%d" % (k, min(v), max(v), len(set(v))) for k, v in sorted(rng.items())))
    for key, label in (("_obj", "object row after g_Ds1ObjectIds or an act rewrite (act)"),
                       ("_mon", "monster id after MonPreset (act, range)")):
        rng = collections.defaultdict(set)
        for k, c in s.pop(key, {}).items():
            rng[k[:2] if key == "_mon" else k[0]].add(k[-1])
        print(label + ": min..max/distinct:",
              ", ".join("%s=%d..%d/%d" % (k, min(v), max(v), len(v)) for k, v in sorted(rng.items())) or "none")
    for key in sorted(s):
        _show(s, key, limit=60)

    # ---- substitution groups: LvlPrest files (by generator kind) and LvlSub files
    sub_files = {}
    for i, r in enumerate(t["lvlsub"]):
        if r["File"] not in ("", "0"):
            sub_files.setdefault(r["File"].replace("\\", "/").lower(), []).append(i)
    g = collections.defaultdict(collections.Counter)
    for src, names in (("lvlprest", files), ("lvlsub", sorted(sub_files))):
        for n in names:
            if n not in present:
                errors += 1
                print("FAIL lvlsub file %s: not present" % n)
                continue
            f = get(n)
            if f is None:
                continue
            kk = src if src == "lvlsub" else "lvlprest/" + "+".join(sorted(kinds_by_file[n]))
            g["files (source, tag_type)"][(kk, f["tag_type"])] += 1
            g["files with groups (source, n>0)"][(kk, len(f["groups"]) > 0)] += 1
            g["groups (source)"][kk] += len(f["groups"])
            g["group_unk (source, value)"][(kk, f["group_unk"])] += 1
            for gr in f["groups"]:
                g["group unk (source, value)"][(kk, gr["unk"])] += 1
            if f["tag_type"] in SUBST_TYPES:
                nz = sum(1 for c in f["layers"]["subst"] if c)
                g["subst cells != 0 (source)"][kk] += nz
                if src == "lvlprest" and f["groups"] and "outdoor" not in kk:
                    g["type-2-only files with groups (file, groups)"][(n, len(f["groups"]))] += 1
    print()
    for key in sorted(g):
        _show(g, key, limit=60)
    gp = sum(v for k, v in g["groups (source)"].items() if k.startswith("lvlprest"))
    gs = g["groups (source)"]["lvlsub"]

    # ---- shared-DS1-buffer (0x84) candidates
    by_file = collections.defaultdict(list)
    for r, i, n in refs:
        by_file[n].append((r["Def"], i, r["SizeX"], r["SizeY"], kind_of[r["Def"]]))
    multi = {n: v for n, v in by_file.items() if len({d for d, *_ in v}) > 1}
    sizes = {n: v for n, v in multi.items() if len({(sx, sy) for _, _, sx, sy, _ in v}) > 1}
    print("\nfiles named by more than one LvlPrest record: %d; with differing SizeX/SizeY: %d"
          % (len(multi), len(sizes)))
    for n, v in sorted(multi.items()):
        f = get(n)
        print("  %s (%dx%d): %s" % (n, f["size_x"], f["size_y"],
                                    "; ".join("Def %d File%d %dx%d %s" % e for e in v)))
    same = {n: v for n, v in by_file.items() if len(v) > 1 and n not in multi}
    print("files named twice by the same record: %d %s" % (len(same), sorted(same)[:5]))
    kc = collections.Counter(kind_of.values())
    nrw = sum(s["act rewrites (act, file, monster id, object, paths)"].values())
    print("SURVEY ds1_units refs=%d files=%d records=%d kind_preset=%d kind_maze=%d kind_outdoor=%d "
          "kind_maze_or_outdoor=%d kind_nofile=%d monsters=%d npcs=%d objects=%d items=%d paths=%d "
          "path_points=%d rewrites=%d groups_lvlprest=%d groups_lvlsub=%d shared_files=%d shared_sizes=%d objtab=%d "
          "errors=%d"
          % (len(refs), len(files), len(recs), kc["preset"], kc["maze"], kc["outdoor"], kc["maze|outdoor"],
             kc["no file"], tot["monster"], tot["npc"], tot["object"], tot["item"], tot["paths"],
             tot["path points"], nrw, gp, gs, len(multi), len(sizes), objtab is not None, errors))
    return 1 if errors else 0


# ---------------------------------------------------------------------------------------- warps survey
# Plan 0022 Phase 2 (backlog reverser -> archivist 2026-10-14). The cells DRLG_PresetMapScan reads, as
# drlg/0007 § 1 gives them ([I]): a wall cell whose paired orientation is 10 or 11, with m = bits 20-25 and
# sub = bits 8-15. m < 8 with sub 0 or 4 or bit 31 sets the room's warp-slot flag 0x10 << m; 30 <= m < 34 is a
# level point of type {30: sub, 31: sub + 5, 32: 10, 33: 11}. An object unit whose Objects SubClass has bit 6
# (the waypoint) sets 0x30000. The scan runs only when the record's Scan (or Pops) is set; the survey reads every
# record's files and reports Scan beside them.

# The records the maze code places itself, per level type (block label, first Def, last Def): the finisher
# specials of drlg/0006 § 6, plus the fixed starts and quadrant/corner tables of § 4 and § 5 and the level 28/107
# placements of § 7. A maze room whose Def is base + exit mask (the rotation range) is not listed here.
MAZE_PLACED = {
    3: [("Prev", 83, 86), ("Next", 87, 90), ("Down", 91, 94), ("Den of Evil", 95, 98), ("Coldcrow", 99, 102)],
    4: [("Prev", 139, 142), ("Next", 143, 146), ("Bonebreak", 147, 150), ("Chest", 151, 154),
        ("Portal (unreferenced)", 155, 158)],
    7: [("Court Connect", 167, 167), ("Next", 198, 201), ("Forge", 202, 205)],
    8: [("Prev", 236, 239), ("Next", 240, 243), ("Cath", 244, 247), ("Waypoint", 248, 251), ("Pitspawn", 252, 255)],
    10: [("Prev (start R0)", 288, 290), ("Next", 291, 294), ("Waypoint", 295, 298)],
    13: [("Prev", 332, 335), ("Dock (level 47)", 336, 336), ("Next", 337, 340), ("Radament", 341, 344),
         ("Waypoint", 345, 348), ("Chest", 349, 352)],
    14: [("Quadrants NE SE SW NW", 354, 357)],
    15: [("Quadrants NE SE SW NW", 358, 361)],
    17: [("Prev (tee R0)", 444, 447), ("Next", 448, 451), ("Treasure", 452, 455), ("Cube", 456, 459),
         ("Tal Rasha", 460, 463), ("Leatherarm", 464, 467), ("Kaa", 468, 471), ("Chest", 472, 475),
         ("Waypoint", 476, 479), ("Tainted Sun (level 61)", 480, 480)],
    18: [("Prev", 497, 500), ("Next", 501, 504), ("Treasure", 505, 508), ("Tight Spot", 509, 509)],
    19: [("Arcane arms W..NSEW", 510, 524), ("Summoner", 525, 528)],
    22: [("Prev", 784, 787), ("Next", 788, 791), ("Waypoint", 792, 795)],
    23: [("Quadrants SW SE NW NE", 659, 662)],
    24: [("Prev", 695, 698), ("Next", 699, 702)],
    25: [("Corners (ring)", 735, 738), ("Drain", 739, 742), ("Chest", 743, 746)],
    28: [("Lava X (filler)", 836, 836), ("Lava Warp N", 852, 852), ("Forge W/E", 853, 854), ("Bridge 1", 855, 855),
         ("Bridge 2", 856, 856)],
    32: [("Quadrants NE NW SE SW", 1042, 1045), ("Down", 1046, 1048), ("Waypoint", 1049, 1052)],
    33: [("Prev", 1018, 1021), ("Next", 1022, 1025), ("Down", 1026, 1029), ("Theme", 1030, 1033),
         ("Waypoint", 1034, 1037), ("One-room 1A/2A/3A", 1038, 1041)],
    34: [("Prev (tee R0)", 1074, 1077), ("Next", 1078, 1081), ("Waypoint", 1082, 1085)],
    35: [("Hell start N S E W EW NS", 1053, 1058)],
}
POINT_TYPE = {30: lambda s: s, 31: lambda s: s + 5, 32: lambda s: 10, 33: lambda s: 11}


def _scan_cells(f):
    """The DRLG_PresetMapScan view of one parsed DS1: dict with 'slot' {m: [(x, y)]} for the qualifying m < 8
    cells, 'unq' {m: n} for m < 8 cells of orientation 10/11 that fail the sub/bit-31 test, 'pt' {(m, type): n}
    for 30..33, and 'pop' the number of 8..29 cells."""
    out = {"slot": collections.defaultdict(list), "unq": collections.Counter(), "pt": collections.Counter(),
           "pop": 0}
    cols = f["cols"]
    for i in range(f["wall_layers"]):
        walls, orients = f["layers"]["wall%d" % i], f["layers"]["orient%d" % i]
        for idx, (c, o) in enumerate(zip(walls, orients)):
            if (o & 0xFF) not in (10, 11):
                continue
            m, sub = (c >> 20) & 0x3F, (c >> 8) & 0xFF
            if m < 8:
                if sub in (0, 4) or c & 0x80000000:
                    out["slot"][m].append((idx % cols, idx // cols))
                else:
                    out["unq"][m] += 1
            elif m < 30:
                out["pop"] += 1
            elif m < 34:
                out["pt"][(m, POINT_TYPE[m](sub))] += 1
    return out


def _slots_str(sc):
    s = ",".join("%d" % m for m in sorted(sc["slot"]))
    extra = []
    if sc["unq"]:
        extra.append("unq " + ",".join("%d" % m for m in sorted(sc["unq"])))
    if sc["pt"]:
        extra.append("pt " + ",".join("%d:t%d" % k for k in sorted(sc["pt"])))
    if sc.get("wp"):
        extra.append("wp %d" % sc["wp"])
    return (s or "-") + ("" if not extra else " (" + "; ".join(extra) + ")")


def _vis_str(d):
    return " ".join("%d:%d/%d" % (k, d["Vis%d" % k], d["Warp%d" % k]) for k in range(8) if d["Vis%d" % k]) or "-"


def warps_survey(root, exe=None, quiet=False):
    t = _tables(root)
    import excel_bin
    import excel_layouts
    excel = os.path.join(root, "data", "global", "excel")
    olay = [fl for fl in excel_layouts.LAYOUTS["objects"]["fields"] if fl.get("col") == "SubClass"][0]
    orecs, _ = excel_bin.read_bin(excel_bin.find_file(excel, "objects", ".bin"))
    subclass = [excel_bin.decode_field(r, olay) for r in orecs]
    objtab = _object_table(exe)
    if objtab is None:
        print("NOTE no pinned game.exe at %s: DS1 object ids < 150 are not translated, so waypoint units "
              "with such ids are not found (objtab=0 in the SURVEY line)" % exe)
    hp, prows = excel_bin.read_txt(excel_bin.find_file(excel, "lvlprest", ".txt"))
    pname = [r[hp.index("Name")] for r in prows]
    hl, lrows = excel_bin.read_txt(excel_bin.find_file(excel, "levels", ".txt"))
    lname = {int(r[hl.index("Id")]): r[hl.index("Name")] for r in lrows if r[hl.index("Id")].strip()}
    tiles = os.path.join(root, "data", "global", "tiles")
    present = {os.path.relpath(p, tiles).replace(os.sep, "/").lower(): p for p in ds1_files(tiles)}
    levels = {r["Id"]: d for r, d in zip(t["levels"], t["leveldefs"])}
    recs = t["lvlprest"]
    assert len(pname) == len(recs), (len(pname), len(recs))
    errors = 0
    cache = {}

    def scan(rel):
        nonlocal errors
        if rel not in cache:
            cache[rel] = None
            if rel not in present:
                errors += 1
                print("FAIL %s: not present" % rel)
                return None
            f, status, msg = _status(open(present[rel], "rb").read())
            if status != "ok":
                errors += 1
                print("FAIL %s: %s %s" % (rel, status, msg))
                return None
            sc = _scan_cells(f)
            sc["wp"] = sum(1 for u in _units(f, t, objtab)
                           if u["type"] == 2 and u["id"] is not None and 0 <= u["id"] < min(0x23D, len(subclass))
                           and subclass[u["id"]] & 0x40)
            cache[rel] = sc
        return cache[rel]

    def files_str(scs):
        return " | ".join("%s: %s" % (n.rsplit("/", 1)[-1], _slots_str(s)) for n, s in scs)

    # ---- per record
    per, tot = {}, collections.Counter()
    for r, nm in zip(recs, pname):
        files = [r["File%d" % i].replace("\\", "/").lower() for i in range(1, 7) if r["File%d" % i] not in ("", "0")]
        scs = [(n, s) for n, s in ((n, scan(n)) for n in files) if s is not None]
        per[r["Def"]] = (r, nm, scs)
        if not scs:
            continue
        tot["records_with_files"] += 1
        if any(s["slot"] for _, s in scs):
            tot["records_with_slots"] += 1
            tot["records_with_slots_scan0"] += not r["Scan"]
            tot["records_files_differ"] += len({frozenset(s["slot"]) for _, s in scs}) > 1
        if any(s["pt"] for _, s in scs):
            tot["records_with_points"] += 1
            tot["records_with_points_scan0"] += not r["Scan"]
        tot["records_with_waypoint"] += any(s["wp"] for _, s in scs)
        tot["records_with_unqualified"] += any(s["unq"] for _, s in scs)
    for sc in cache.values():
        if sc is None:
            continue
        tot["files"] += 1
        tot["slot_cells"] += sum(len(v) for v in sc["slot"].values())
        tot["unqualified_cells"] += sum(sc["unq"].values())
        tot["point_cells"] += sum(sc["pt"].values())
        tot["pop_cells"] += sc["pop"]
        tot["waypoint_units"] += sc["wp"]
        tot["files_multi_slot"] += len(sc["slot"]) > 1
        tot["files_unqualified_only"] += bool(set(sc["unq"]) - set(sc["slot"]))
        for m in sc["slot"]:
            tot["files_slot%d" % m] += 1

    # ---- 1. maze level types: specials and their slots, beside the levels' Vis/Warp
    print("== 1. Records the maze code places (drlg/0006 §§ 4-7) per level type: warp slots of their DS1 files\n"
          "   slots[ (unq: m<8 cells failing the sub 0/4/bit-31 test; pt: level point m:type; wp: waypoint units)]\n"
          "   levels: Vis slot:dest/Warp")
    maze_types = collections.defaultdict(list)
    for lid, d in sorted(levels.items()):
        if d["DrlgType"] == 1:
            maze_types[d["LevelType"]].append(lid)
    placed_defs = set()
    for lt in sorted(set(maze_types) | set(MAZE_PLACED)):
        print("\n-- type %d: maze levels %s" % (lt, ", ".join(map(str, maze_types.get(lt, []))) or "none"))
        for lid in maze_types.get(lt, []):
            print("   level %3d %-28s %s" % (lid, lname.get(lid, "?"), _vis_str(levels[lid])))
        for label, a, b in MAZE_PLACED.get(lt, []):
            summary = collections.Counter()
            for dfn in range(a, b + 1):
                placed_defs.add(dfn)
                r, nm, scs = per[dfn]
                summary[" | ".join(_slots_str(s) for _, s in scs) + ("" if r["Scan"] else " [Scan 0]")] += 1
                if not quiet:
                    print("      Def %4d %-34s Scan %d  %s" % (dfn, nm, r["Scan"], files_str(scs)))
            print("   %-22s Def %d-%d: %s" % (label, a, b, "; ".join("%s x%d" % kv for kv in sorted(summary.items()))))
            tot["placed_records"] += b - a + 1
            tot["placed_records_with_slots"] += sum(1 for dfn in range(a, b + 1)
                                                      if any(s["slot"] for _, s in per[dfn][2]))
    rot_bad = [dfn for base in sorted(MAZE_DEF_BASE.values()) for dfn in range(base + 1, base + 16)
               if dfn in per and dfn not in placed_defs and any(s["slot"] or s["pt"] for _, s in per[dfn][2])]
    tot["rotation_records_with_slots"] = len(rot_bad)
    print("\nrotation-range records (base+1..base+15, placed records above left out) with warp or point cells: %d %s"
          % (len(rot_bad), rot_bad))

    # ---- 2. every other record with warp, point or waypoint cells
    print("\n== 2. Other LvlPrest records (not placed by the maze code) with warp-slot, level-point or waypoint cells"
          " (Def, Name, LevelId, Scan, files, the level's Vis)")
    for dfn, (r, nm, scs) in sorted(per.items()):
        if dfn in placed_defs or not any(s["slot"] or s["pt"] or s["wp"] or s["unq"] for _, s in scs):
            continue
        tot["other_records"] += 1
        lid = r["LevelId"]
        d = levels.get(lid) if lid else None
        if not quiet:
            print("  Def %4d %-36s L%-3d Scan %d  %s%s" % (dfn, nm, lid, r["Scan"], files_str(scs),
                                                         "  Vis " + _vis_str(d) if d else ""))
        if d:
            got = set().union(*(set(s["slot"]) for _, s in scs))
            lost = got - {k for k in range(8) if d["Vis%d" % k]}
            if lost:
                tot["preset_slot_without_vis"] += 1
                print("  NOTE Def %d (level %d): slots %s have no Vis" % (dfn, lid, sorted(lost)))
    print("SURVEY ds1_warps records=%d records_with_files=%d files=%d slot_cells=%d unqualified_cells=%d "
          "point_cells=%d pop_cells=%d waypoint_units=%d records_with_slots=%d records_with_slots_scan0=%d "
          "records_files_differ=%d records_with_points=%d records_with_points_scan0=%d records_with_waypoint=%d "
          "records_with_unqualified=%d files_multi_slot=%d files_unqualified_only=%d %s placed_records=%d placed_records_with_slots=%d "
          "rotation_records_with_slots=%d other_records=%d preset_slot_without_vis=%d objtab=%d errors=%d"
          % (len(recs), tot["records_with_files"], tot["files"], tot["slot_cells"], tot["unqualified_cells"],
             tot["point_cells"], tot["pop_cells"], tot["waypoint_units"], tot["records_with_slots"],
             tot["records_with_slots_scan0"], tot["records_files_differ"], tot["records_with_points"],
             tot["records_with_points_scan0"], tot["records_with_waypoint"], tot["records_with_unqualified"],
             tot["files_multi_slot"], tot["files_unqualified_only"], " ".join("files_slot%d=%d" % (m, tot["files_slot%d" % m]) for m in range(8)),
             tot["placed_records"], tot["placed_records_with_slots"], tot["rotation_records_with_slots"],
             tot["other_records"], tot["preset_slot_without_vis"], objtab is not None, errors))
    return 1 if errors else 0


TILE_W, TILE_H = 160, 80          # floor diamond in pixels; a cell steps (+80, +40) in x, (-80, +40) in y
SKIP_ORIENT = (10, 11)            # special-tile orientations, not drawn (docs/formats/ds1.md, Preview)
MARKER = 255                      # palette index used to fill the diamond of a missing tile key


class _Tiles:
    """Tile key -> paintable runs, from the DS1's own DT1 list first, then from any DT1."""

    def __init__(self, root, scale):
        here = os.path.dirname(os.path.abspath(__file__))
        if here not in sys.path:
            sys.path.insert(0, here)
        import dt1
        self.dt1, self.scale = dt1, scale
        self.tiles_dir = os.path.join(root, "data", "global", "tiles")
        self.by_rel = {os.path.relpath(p, root).replace(os.sep, "/").lower(): p
                       for p in dt1.dt1_files(self.tiles_dir)}
        self.parsed, self.runs, self.anywhere = {}, {}, None

    def _file(self, path):
        if path not in self.parsed:
            data = open(path, "rb").read()
            try:
                h = self.dt1.parse(data)
            except self.dt1.Dt1Error:
                h = {"tiles": []}
            first = {}
            for t in h["tiles"]:
                first.setdefault((t["orientation"], t["main_index"], t["sub_index"]), t)
            self.parsed[path] = (data, first)
        return self.parsed[path]

    def _any(self):
        if self.anywhere is None:
            self.anywhere = {}
            for p in sorted(self.by_rel.values()):
                for k in self._file(p)[1]:
                    self.anywhere.setdefault(k, p)
        return self.anywhere

    def lookup(self, key, own):
        """Return (runs, source) with source 'own', 'other' or None (missing)."""
        for p in own:
            if key in self._file(p)[1]:
                return self._runs(p, key), "own"
        p = self._any().get(key)
        if p:
            return self._runs(p, key), "other"
        return None, None

    def _runs(self, path, key):
        if (path, key) not in self.runs:
            data, first = self._file(path)
            w, h, px, x0, y0 = self.dt1.render_tile(data, first[key])
            sc, runs = self.scale, []
            for y in range(0, h, sc):
                row = px[y * w:(y + 1) * w:sc]
                x = 0
                while x < len(row):
                    if row[x]:
                        e = x
                        while e < len(row) and row[e]:
                            e += 1
                        runs.append(((y0 + y) // sc, (x0 // sc) + x, bytes(row[x:e])))
                        x = e
                    else:
                        x += 1
            self.runs[(path, key)] = runs
        return self.runs[(path, key)]



# ---------------------------------------------------------------------------------------- objects survey
# Plan 0023 Phase 2 prep (backlog reverser -> archivist 2026-10-14). The DS1 object units whose class (after
# DS1_Parse's mapping, as _units gives it: ids < 150 through g_Ds1ObjectIds, ids >= 150 as id - 150) is one the
# object findings single out (objects/0001 §§ 7-8, [I] there): 269 (InitFn 28, the gold-pile dummy), 397 and 455
# (InitFn 57, sparkly chests), 573 (PresetUnitDispatch does nothing) and the pseudo-objects 574..582
# (OBJ_PresetPseudoDispatch: fixed shrines 574..579, super chest 580, random chest 581, quest object 582).
WATCH_OBJECTS = {269: "gold pile dummy (InitFn 28)", 397: "sparkly chest (InitFn 57)",
                 455: "sparkly chest (InitFn 57)", 573: "no-op preset id",
                 574: "fixed shrine (2..6)", 575: "fixed shrine (7)", 576: "fixed shrine (8..11)",
                 577: "fixed shrine (12)", 578: "fixed shrine (1..5)", 579: "fixed shrine (14)",
                 580: "super chest", 581: "random chest", 582: "quest object"}


def objects_survey(root, exe=None, quiet=False):
    t = _tables(root)
    import excel_bin
    excel = os.path.join(root, "data", "global", "excel")
    objtab = _object_table(exe)
    if objtab is None:
        print("NOTE no pinned game.exe at %s: DS1 object ids < 150 are not translated (objtab=0 in the "
              "SURVEY line)" % exe)
    hp, prows = excel_bin.read_txt(excel_bin.find_file(excel, "lvlprest", ".txt"))
    pname = [r[hp.index("Name")] for r in prows]
    ho, orows = excel_bin.read_txt(excel_bin.find_file(excel, "objects", ".txt"))
    oname = [r[ho.index("Name")] for r in orows]
    hl, lrows = excel_bin.read_txt(excel_bin.find_file(excel, "levels", ".txt"))
    lname = {int(r[hl.index("Id")]): r[hl.index("Name")] for r in lrows if r[hl.index("Id")].strip()}
    tiles = os.path.join(root, "data", "global", "tiles")
    present = {os.path.relpath(p, tiles).replace(os.sep, "/").lower(): p for p in ds1_files(tiles)}
    recs = t["lvlprest"]
    assert len(pname) == len(recs), (len(pname), len(recs))
    errors, cache = 0, {}

    def units(rel):
        """{class: [(act, x, y, raw, route)]} of the watched classes in one file."""
        nonlocal errors
        if rel not in cache:
            cache[rel] = None
            if rel not in present:
                errors += 1
                print("FAIL %s: not present" % rel)
                return None
            f, status, msg = _status(open(present[rel], "rb").read())
            if f is None:
                if KNOWN_MALFORMED.get("data/global/tiles/" + rel) != status:
                    errors += 1
                    print("FAIL %s: %s %s" % (rel, status, msg))
                return None
            got = collections.defaultdict(list)
            for u in _units(f, t, objtab):
                if u["type"] == 2 and u["id"] in WATCH_OBJECTS:
                    got[u["id"]].append((u["act"] + 1, u["x"], u["y"], u["raw"], u["rng"]))
            cache[rel] = got
        return cache[rel]

    # ---- 1. per watched class: the LvlPrest records (and files) that place it
    by_cls = collections.defaultdict(list)          # class -> [(Def, name, LevelId, file, n, act)]
    named = set()
    for r, nm in zip(recs, pname):
        for i in range(1, 7):
            if r["File%d" % i] in ("", "0"):
                continue
            n = r["File%d" % i].replace("\\", "/").lower()
            named.add(n)
            got = units(n)
            if not got:
                continue
            for c, us in got.items():
                by_cls[c].append((r["Def"], nm, r["LevelId"], n, len(us), us[0][0], us[0][4]))
    print("== 1. LvlPrest records whose DS1s place a watched object class (Def, Name, LevelId, file, units, act, route)")
    tot = collections.Counter()
    for c in sorted(WATCH_OBJECTS):
        rows = by_cls.get(c, [])
        label = oname[c] if c < len(oname) else "(pseudo id, no Objects row)"
        print("\nclass %d %s: %s; units %d in %d files of %d records"
              % (c, label, WATCH_OBJECTS[c], sum(x[4] for x in rows), len({x[3] for x in rows}),
                 len({x[0] for x in rows})))
        tot["obj%d_units" % c] = sum(x[4] for x in rows)
        tot["obj%d_files" % c] = len({x[3] for x in rows})
        tot["obj%d_records" % c] = len({x[0] for x in rows})
        if quiet:
            continue
        for d, nm, lid, n, k, act, route in rows:
            lv = ("L%d %s" % (lid, lname.get(lid, "?"))) if lid else "L0"
            print("  Def %4d %-40s %-28s act %d  %s x%d  (%s)" % (d, nm[:40], lv[:28], act, n, k, route))

    # ---- 2. DS1 files no LvlPrest record names (not loaded by the game, listed for completeness)
    print("\n== 2. DS1 files that no LvlPrest record names, with a watched class")
    for rel in sorted(present):
        if rel in named:
            continue
        got = units(rel)
        if not got:
            continue
        tot["unnamed_files"] += 1
        if not quiet:
            print("  %s: %s" % (rel, ", ".join("%d x%d" % (c, len(us)) for c, us in sorted(got.items()))))
    print("SURVEY ds1_objects files=%d %s unnamed_files=%d objtab=%d errors=%d"
          % (sum(1 for v in cache.values() if v is not None),
             " ".join("%s=%d" % (k, tot[k]) for c in sorted(WATCH_OBJECTS)
                      for k in ("obj%d_units" % c, "obj%d_files" % c, "obj%d_records" % c)),
             tot["unnamed_files"], objtab is not None, errors))
    return 1 if errors else 0

def _own_dt1s(f, tiles):
    out = []
    for name in f["files"]:
        low = name.replace("\\", "/").lower()
        k = low.find("data/global/tiles/")
        if k >= 0:
            p = tiles.by_rel.get(os.path.splitext(low[k:])[0] + ".dt1")
            if p:
                out.append(p)
    return out


def render_one(f, tiles, max_pixels=60_000_000, hidden=False):
    """Return (width, height, pixels, stats) for one parsed DS1."""
    cols, rows = f["cols"], f["rows"]
    sc = tiles.scale
    pad_top = 1024 // sc               # room for walls rising above the top row
    W = (cols + rows) * (TILE_W // 2) // sc + TILE_W // sc
    H = (cols + rows) * (TILE_H // 2) // sc + pad_top + TILE_H // sc
    if W * H > max_pixels:
        raise MemoryError("%dx%d over the pixel budget at scale %d" % (W, H, sc))
    canvas = bytearray(W * H)
    ox, oy = rows * (TILE_W // 2) // sc, pad_top
    own = _own_dt1s(f, tiles)
    st = collections.Counter()

    def paint(runs, cx, cy):
        bx = ox + (cx - cy) * (TILE_W // 2) // sc
        by = oy + (cx + cy) * (TILE_H // 2) // sc
        for dy, dx, run in runs:
            y, x = by + dy, bx + dx
            if 0 <= y < H:
                a, b = max(x, 0), min(x + len(run), W)
                if a < b:
                    canvas[y * W + a:y * W + b] = run[a - x:b - x]

    marker = []
    for r in range(0, TILE_H // 2 // sc):
        half = (r * 2 + 1) * (TILE_W // TILE_H)
        marker.append((r, (TILE_W // 2) // sc - half, bytes([MARKER]) * (2 * half)))
    marker += [((TILE_H // sc) - 1 - y, x, run) for y, x, run in reversed(marker)]

    layers = f["layers"]
    order = [n for n in layers if n.startswith("floor")] + [n for n in layers if n.startswith("wall")]
    for name in order:
        kind = "floor" if name.startswith("floor") else "wall"
        orients = layers["orient" + name[4:]] if kind == "wall" and ("orient" + name[4:]) in layers else None
        cells = layers[name]
        for cy in range(rows):
            for cx in range(cols):
                c = cells[cy * cols + cx]
                if not c:
                    continue
                if c >> 31 and not hidden:
                    st[kind + " skipped (hidden, bit 31)"] += 1
                    continue
                o = 0 if kind == "floor" else (orients[cy * cols + cx] if orients else 0)
                if o in SKIP_ORIENT:
                    st[kind + " skipped (special)"] += 1
                    continue
                key = (o, (c >> 20) & 63, (c >> 8) & 63)
                runs, src = tiles.lookup(key, own)
                st["%s %s" % (kind, src or "missing")] += 1
                paint(runs if runs else marker, cx, cy)
    return W, H, canvas, st


def render(root, out, all_files=False, only=None, scale=1, hidden=False):
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import palette
    import png
    tiles = _Tiles(root, scale)
    half = _Tiles(root, 2) if scale == 1 else None
    tiles_dir = tiles.tiles_dir
    present = {os.path.relpath(p, tiles_dir).replace(os.sep, "/").lower(): p for p in ds1_files(tiles_dir)}
    names = sorted(present) if all_files else sorted(lvlprest_names(root))
    if only:
        names = [n for n in names if only.lower() in n]
    pals, total = {}, collections.Counter()
    done = bad = halved = 0
    for rel in names:
        path = present.get(rel)
        if not path:
            bad += 1
            print("FAIL %s: not present" % rel)
            continue
        try:
            f = parse(open(path, "rb").read())
            if f["leftover"]:
                print("NOTE %s: malformed (leftover %d bytes), rendered as far as it parses" % (rel, f["leftover"]))
            try:
                w, h, px, st = render_one(f, tiles, hidden=hidden)
            except MemoryError:
                w, h, px, st = render_one(f, half, hidden=hidden)
                halved += 1
            pn = palette.palette_for_tiles(rel)
            if pn not in pals:
                pals[pn] = palette.load(root, pn)
            png.write_indexed(os.path.join(out, "ds1", os.path.splitext(rel)[0] + ".png"), w, h, px, pals[pn])
            total.update(st)
            done += 1
            if st["floor missing"] or st["wall missing"]:
                print("missing keys %s: floor %d, wall %d" % (rel, st["floor missing"], st["wall missing"]))
        except Exception as e:  # report and continue: the summary must name every failure
            bad += 1
            print("FAIL %s: %s: %s" % (rel, type(e).__name__, e))
    print("rendered %d of %d DS1 (%d at half scale), failures %d -> %s" % (done, len(names), halved, bad,
                                                                        os.path.join(out, "ds1")))
    print("cells:", ", ".join("%s=%d" % kv for kv in sorted(total.items())))
    return 1 if bad else 0


def main(argv):
    if len(argv) >= 2 and argv[0] == "survey":
        return survey(argv[1])
    if len(argv) >= 2 and argv[0] == "dump":
        dump(argv[1], "--cells" in argv)
        return 0
    if len(argv) >= 2 and argv[0] == "lvlprest":
        return lvlprest(argv[1])
    if len(argv) >= 2 and argv[0] == "units":
        exe = argv[2] if len(argv) >= 3 else os.path.join(argv[1], "..", "install", "app", "game.exe")
        return units_survey(argv[1], exe)
    if len(argv) >= 2 and argv[0] == "warps":
        rest = [a for a in argv[2:] if not a.startswith("--")]
        exe = rest[0] if rest else os.path.join(argv[1], "..", "install", "app", "game.exe")
        return warps_survey(argv[1], exe, quiet="--quiet" in argv)
    if len(argv) >= 2 and argv[0] == "objects":
        rest = [a for a in argv[2:] if not a.startswith("--")]
        exe = rest[0] if rest else os.path.join(argv[1], "..", "install", "app", "game.exe")
        return objects_survey(argv[1], exe, quiet="--quiet" in argv)
    if len(argv) >= 2 and argv[0] == "render":
        rest, only, i = [], None, 2
        while i < len(argv):
            if argv[i] == "--only" and i + 1 < len(argv):
                only, i = argv[i + 1], i + 2
                continue
            if not argv[i].startswith("--"):
                rest.append(argv[i])
            i += 1
        return render(argv[1], rest[0] if rest else os.path.join(argv[1], "..", "render"),
                      all_files="--all" in argv, only=only, hidden="--hidden" in argv)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Parse Diablo II DS1 preset maps and check them against LvlPrest.

Usage:
  python3 -I tools/ds1.py survey <root>               parse every .ds1 under <root>; histograms, failures
  python3 -I tools/ds1.py dump <file.ds1> [--cells]   print one file's header, lists and layer summary
  python3 -I tools/ds1.py lvlprest <root>             resolve lvlprest.bin File1..6 against <root>/data/global/tiles

<root> is a merged data tree (e.g. workspace/merged). Layout in docs/formats/ds1.md. All fields are
little-endian 32-bit. Header, then layers of (size_x+1) x (size_y+1) u32 cells, then the object list,
the substitution-group list and the NPC-path list, each present from some file version on. survey
exits 0 only if every file parses and ends exactly at its last byte, except the KNOWN_MALFORMED
files, which must fail exactly as recorded. lvlprest exits 0 only if every File1..6 resolves.
Stdlib only. Read-only.
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
    ok = expected = unexpected = 0
    tiles = os.path.join(root, "data", "global", "tiles")
    tile_files = {os.path.relpath(os.path.join(d, n), root).replace(os.sep, "/").lower()
                  for d, _, names in os.walk(tiles) for n in names}
    s = collections.defaultdict(collections.Counter)
    for path in ds1_files(root):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        data = open(path, "rb").read()
        f, status, msg = _status(data)
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


def main(argv):
    if len(argv) >= 2 and argv[0] == "survey":
        return survey(argv[1])
    if len(argv) >= 2 and argv[0] == "dump":
        dump(argv[1], "--cells" in argv)
        return 0
    if len(argv) >= 2 and argv[0] == "lvlprest":
        return lvlprest(argv[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

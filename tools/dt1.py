"""Parse Diablo II DT1 tile files: header, tile records, block headers; account for every byte.

Usage:
  python3 -I tools/dt1.py survey <root>          parse every .dt1 under <root>; byte accounting, histograms
  python3 -I tools/dt1.py dump <file.dt1> [N]    print the header and the first N tile records (default 5)
  python3 -I tools/dt1.py ds1keys <root> [MAIN SUB] [--all]
                                                 check DS1 cells against the tiles of the DT1s each DS1
                                                 lists (--all: every DT1); MAIN/SUB are the bit
                                                 positions of the 6-bit indices (default 20 8)
  python3 -I tools/dt1.py render <root> [out] [--no-sheet]
                                                 render every 7.6 tile to <out>/tiles/<dt1 path>/
                                                 <orientation>_<main>_<sub>_<n>.png plus a per-file
                                                 _sheet.png (default out: workspace/render)
  python3 -I tools/dt1.py lvltypes <root> [ID ...] [--base PREFIX]
                                                 print the File 1..32 DT1 paths of lvltypes.bin record ID
                                                 (= LvlTypes.txt Id) as the game prefixes them, with the
                                                 mask bit each one answers to and whether the file exists;
                                                 no ID: one summary line per level type

<root> is a merged data tree (e.g. workspace/merged). Layout in docs/formats/dt1.md. Little-endian.
A version 7.6 file is a 276-byte header, `tile_count` 96-byte tile records, then per tile a run of
20-byte block headers followed by the blocks' pixel data. Pixel data is not decoded beyond what is
needed to check each block's length (isometric blocks are a fixed 256 bytes; RLE blocks are walked
to their end). survey exits 0 only if every byte of every 7.6 file is covered exactly once and every
other file is a KNOWN_OTHER one. render decodes the pixel blocks (docs/formats/dt1.md, Pixel data)
and writes PNGs via tools/png.py; it is the only subcommand that writes. Stdlib only.
"""
import collections
import os
import struct
import sys

HEADER_SIZE = 276
TILE_SIZE = 96
BLOCK_SIZE = 20

# Files that are not version 7.6 (docs/formats/dt1.md, "Version 4.1 files"). None is named by
# LvlTypes.txt or by any DS1 tile list.
KNOWN_OTHER = {
    "data/global/tiles/act1/barracks/barracks.dt1",
    "data/global/tiles/act1/barracks/gargtrap.dt1",
    "data/global/tiles/act1/catacomb/catacombs.dt1",
    "data/global/tiles/act1/cathedrl/cathedrl.dt1",
    "data/global/tiles/act1/court/court.dt1",
    "data/global/tiles/act1/outdoors/outdoor1.dt1",
}


class Dt1Error(ValueError):
    pass


TILE_FIELDS = [  # (name, offset, struct format)
    ("direction", 0x00, "<i"),
    ("roof_height", 0x04, "<h"),
    ("sound", 0x06, "<B"),
    ("animated", 0x07, "<B"),
    ("height", 0x08, "<i"),
    ("width", 0x0C, "<i"),
    ("unk_10", 0x10, "<i"),
    ("orientation", 0x14, "<i"),
    ("main_index", 0x18, "<i"),
    ("sub_index", 0x1C, "<i"),
    ("rarity", 0x20, "<i"),
    ("unk_24", 0x24, "<I"),
    # 0x28: u8 subtile_flags[25]
    ("unk_41", 0x41, "7s"),
    ("block_ptr", 0x48, "<I"),
    ("block_len", 0x4C, "<I"),
    ("block_count", 0x50, "<i"),
    ("unk_54", 0x54, "12s"),
]

BLOCK_FIELDS = [
    ("x", 0x00, "<h"),
    ("y", 0x02, "<h"),
    ("unk_04", 0x04, "<H"),
    ("grid_x", 0x06, "<B"),
    ("grid_y", 0x07, "<B"),
    ("format", 0x08, "<H"),
    ("length", 0x0A, "<i"),
    ("unk_0E", 0x0E, "<H"),
    ("data_off", 0x10, "<i"),
]


def _unpack(fields, data, base):
    return {name: struct.unpack_from(fmt, data, base + off)[0] for name, off, fmt in fields}


def rle_length(data, pos, end):
    """Walk one RLE block (pairs of skip, count; count bytes of pixels; (0, 0) ends a row) and
    return (bytes consumed, rows). The block must end with a (0, 0) pair exactly at `end`."""
    start, rows = pos, 0
    while True:
        if pos + 2 > end:
            raise Dt1Error("RLE block runs past its length")
        skip, count = data[pos], data[pos + 1]
        pos += 2
        if skip == 0 and count == 0:
            rows += 1
            if pos == end:
                break
            continue
        pos += count
    return pos - start, rows


def parse(data):
    if len(data) < HEADER_SIZE:
        raise Dt1Error("short header")
    h = {"version": struct.unpack_from("<ii", data, 0), "unk_08": data[8:268],
         "tile_count": struct.unpack_from("<i", data, 268)[0],
         "tile_ptr": struct.unpack_from("<I", data, 272)[0]}
    if h["version"] != (7, 6):
        raise Dt1Error("version %d.%d" % h["version"])
    n = h["tile_count"]
    if h["tile_ptr"] + n * TILE_SIZE > len(data) or n < 0:
        raise Dt1Error("tile records past end")
    covered = [(0, HEADER_SIZE, "header"), (h["tile_ptr"], h["tile_ptr"] + n * TILE_SIZE, "tiles")]
    tiles = []
    for i in range(n):
        base = h["tile_ptr"] + i * TILE_SIZE
        t = _unpack(TILE_FIELDS, data, base)
        t["subtile_flags"] = data[base + 0x28: base + 0x41]
        bp, bc = t["block_ptr"], t["block_count"]
        if bc < 0 or bp + bc * BLOCK_SIZE > len(data):
            raise Dt1Error("tile %d: block headers past end" % i)
        if bp + t["block_len"] > len(data):
            raise Dt1Error("tile %d: block area past end" % i)
        covered.append((bp, bp + t["block_len"], "tile%d" % i))
        blocks = []
        inner = [(bp, bp + bc * BLOCK_SIZE)]
        for k in range(bc):
            b = _unpack(BLOCK_FIELDS, data, bp + k * BLOCK_SIZE)
            s, e = bp + b["data_off"], bp + b["data_off"] + b["length"]
            if b["data_off"] < bc * BLOCK_SIZE or e > bp + t["block_len"]:
                raise Dt1Error("tile %d block %d: data outside the tile's block area" % (i, k))
            if b["format"] == 1:
                if b["length"] != 256:
                    raise Dt1Error("tile %d block %d: isometric block of %d bytes" % (i, k, b["length"]))
                b["rows"] = 15
            else:
                used, b["rows"] = rle_length(data, s, e)
                if used != b["length"]:
                    raise Dt1Error("tile %d block %d: RLE uses %d of %d bytes" % (i, k, used, b["length"]))
            inner.append((s, e))
            blocks.append(b)
        inner.sort()
        pos = bp
        for s, e in inner:
            if s != pos:
                raise Dt1Error("tile %d: gap or overlap in block area at 0x%X" % (i, pos))
            pos = e
        if pos != bp + t["block_len"]:
            raise Dt1Error("tile %d: block area has %d unaccounted bytes" % (i, bp + t["block_len"] - pos))
        t["blocks"] = blocks
        tiles.append(t)
    covered.sort()
    pos = 0
    for s, e, what in covered:
        if s != pos:
            raise Dt1Error("%s at 0x%X: %s 0x%X" % ("gap" if s > pos else "overlap", pos, what, s))
        pos = e
    h["leftover"] = len(data) - pos
    h["tiles"] = tiles
    return h


def dt1_files(root):
    for d, _, names in os.walk(root):
        for name in sorted(names):
            if name.lower().endswith(".dt1"):
                yield os.path.join(d, name)


def _show(stats, key, limit=24):
    items = sorted(stats[key].items(), key=lambda kv: (-kv[1], str(kv[0])))
    print("%-30s %3d distinct: %s%s" % (key, len(items), ", ".join("%s=%d" % kv for kv in items[:limit]),
                                       " ..." if len(items) > limit else ""))


def survey(root):
    ok = other = bad = 0
    ntiles = nblocks = leftover = 0
    hist = collections.Counter()
    s = collections.defaultdict(collections.Counter)
    for path in dt1_files(root):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        data = open(path, "rb").read()
        v = struct.unpack_from("<ii", data, 0)
        hist[v] += 1
        if v != (7, 6):
            if rel.lower() in KNOWN_OTHER:
                other += 1
                print("version %d.%d (known, not parsed): %s" % (v + (rel,)))
            else:
                bad += 1
                print("FAIL %s: unexpected version %d.%d" % ((rel,) + v))
            continue
        try:
            h = parse(data)
        except Dt1Error as e:
            bad += 1
            print("FAIL %s: %s" % (rel, e))
            continue
        if h["leftover"]:
            bad += 1
            leftover += h["leftover"]
            print("LEFTOVER %s: %d bytes" % (rel, h["leftover"]))
            continue
        ok += 1
        ntiles += len(h["tiles"])
        nblocks += sum(len(t["blocks"]) for t in h["tiles"])
        s["header unk_08 all zero"][h["unk_08"] == bytes(260)] += 1
        s["tile_count"][h["tile_count"]] += 1
        s["tile_ptr"][h["tile_ptr"]] += 1
        prev_end = None
        for t in h["tiles"]:
            o = t["orientation"]
            for k in ("direction", "roof_height", "sound", "animated", "unk_10", "unk_24", "rarity"):
                s["tile." + k][t[k]] += 1
            s["tile.orientation"][o] += 1
            s["(orientation, direction)"][(o, t["direction"])] += 1
            s["(orientation, width, height)"][(o, t["width"], t["height"])] += 1
            s["tile.main_index"][t["main_index"]] += 1
            s["tile.sub_index"][t["sub_index"]] += 1
            s["tile.unk_41 zero"][t["unk_41"] == bytes(7)] += 1
            s["tile.unk_54 zero"][t["unk_54"] == bytes(12)] += 1
            s["tile.unk_54 dwords zero (0, 2)"][(t["unk_54"][:4] == bytes(4), t["unk_54"][8:] == bytes(4))] += 1
            for k in range(4):
                s["tile.unk_24 byte%d" % k][t["unk_24"] >> (8 * k) & 0xFF] += 1
            s["(orientation, roof_height != 0)"][(o, t["roof_height"] != 0)] += 1
            s["(animated, rarity)"][(t["animated"], t["rarity"])] += 1
            s["tile.block_count"][t["block_count"]] += 1
            s["block area follows previous"][prev_end is None or t["block_ptr"] == prev_end] += 1
            prev_end = t["block_ptr"] + t["block_len"]
            for f in t["subtile_flags"]:
                s["subtile flag byte"][f] += 1
                for bit in range(8):
                    if f >> bit & 1:
                        s["subtile flag bit set"][bit] += 1
            s["subtile flags all zero (by orientation)"][(o, t["subtile_flags"] == bytes(25))] += 1
            for b in t["blocks"]:
                s["block.format"][b["format"]] += 1
                s["(format, orientation==0)"][(b["format"], o == 0)] += 1
                s["block.unk_04"][b["unk_04"]] += 1
                s["block.unk_0E"][b["unk_0E"]] += 1
                s["block.grid"][(b["grid_x"], b["grid_y"])] += 1
                s["block x,y multiple of 32"][(b["x"] % 32 == 0, b["y"] % 32 == 0 if o else b["y"] % 16 == 0)] += 1
                s["(rows, format)"][(b["rows"], b["format"])] += 1
    print("version 7.6 parsed with every byte covered %d; other versions (known) %d; failures %d" % (ok, other, bad))
    print("version histogram:", " ".join("%d.%d:%d" % (k + (c,)) for k, c in sorted(hist.items())))
    for key in sorted(s):
        _show(s, key)
    # gate summary (tools/gate.py --full): integer counts only; tiles/blocks over parsed files
    print("SURVEY dt1 files=%d parsed=%d other_versions=%d errors=%d tiles=%d blocks=%d leftover_bytes=%d"
          % (ok + other + bad, ok, other, bad, ntiles, nblocks, leftover))
    return 1 if bad or other != len(KNOWN_OTHER) else 0


def dump(path, count=5):
    data = open(path, "rb").read()
    h = parse(data)
    print("version %d.%d tile_count %d tile_ptr %d leftover %d" % (h["version"] + (h["tile_count"], h["tile_ptr"],
                                                                     h["leftover"])))
    for i, t in enumerate(h["tiles"][:count]):
        print("tile %d: %s" % (i, " ".join("%s=%s" % (k, t[k]) for k, _, _ in TILE_FIELDS
                                         if not k.startswith("unk_4") and k != "unk_54")))
        print("  subtile_flags", " ".join("%02X" % f for f in t["subtile_flags"]))
        for b in t["blocks"][:4]:
            print("  block", b)


def _tile_keys(path, cache):
    """Set of (orientation, main_index, sub_index) for one DT1, or None if it is not a 7.6 file."""
    if path not in cache:
        try:
            cache[path] = {(t["orientation"], t["main_index"], t["sub_index"])
                           for t in parse(open(path, "rb").read())["tiles"]}
        except (Dt1Error, OSError):
            cache[path] = None
    return cache[path]


def ds1keys(root, main_shift=20, sub_shift=8, width=6, all_files=False):
    """For every non-zero wall, floor and shadow cell of every cleanly parsed DS1, build the key
    (orientation, main, sub) and look it up in the tiles of the DT1 files the DS1 lists. Walls take
    the orientation from the paired orient layer, floors use 0 and shadows 13. With all_files, look
    keys up in every 7.6 DT1 instead of the DS1's own list. Misses are also broken down by orientation
    and by whether any DT1 has the key, and keys found in no DT1 are counted per DS1 file."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import ds1
    tiles_dir = os.path.join(root, "data", "global", "tiles")
    by_rel = {os.path.relpath(p, root).replace(os.sep, "/").lower(): p for p in dt1_files(tiles_dir)}
    cache = {}
    every = set()
    for p in by_rel.values():
        every |= _tile_keys(p, cache) or set()
    mask = (1 << width) - 1
    s = collections.defaultdict(collections.Counter)
    for path in ds1.ds1_files(tiles_dir):
        try:
            f = ds1.parse(open(path, "rb").read())
        except ds1.Ds1Error:
            continue
        if f["leftover"]:
            continue
        rel = os.path.relpath(path, tiles_dir).replace(os.sep, "/")
        keys = set(every) if all_files else set()
        for name in f["files"] if not all_files else []:
            low = name.replace("\\", "/").lower()
            k = low.find("data/global/tiles/")
            if k < 0:
                continue
            p = by_rel.get(os.path.splitext(low[k:])[0] + ".dt1")
            got = _tile_keys(p, cache) if p else None
            if got:
                keys |= got
        for lname, cells in f["layers"].items():
            kind = lname.rstrip("0123456789")
            if kind not in ("wall", "floor", "shadow"):
                continue
            orients = f["layers"]["orient" + lname[4:]] if kind == "wall" else None
            for i, c in enumerate(cells):
                if not c:
                    continue
                o = orients[i] if kind == "wall" else (0 if kind == "floor" else 13)
                key = (o, (c >> main_shift) & mask, (c >> sub_shift) & mask)
                hit = key in keys
                if kind == "floor":
                    s["floor (low byte, key in list) -> key if not in list"][
                        ("0x%02X" % (c & 0xFF), hit, None if hit else key[1:])] += 1
                s[kind + " found"][hit] += 1
                s[kind + " found, by bit 31"][(hit, c >> 31)] += 1
                if not hit:
                    anywhere = key in every
                    s[kind + " missing orientation"][o] += 1
                    s[kind + " missing (orientation, in another DT1)"][(o, anywhere)] += 1
                    if not anywhere:
                        s[kind + " in no DT1, by file"][rel] += 1
    for key in sorted(s):
        _show(s, key, 40)
    return 0


ISO_X = (14, 12, 10, 8, 6, 4, 2, 0, 2, 4, 6, 8, 10, 12, 14)   # 0x0001 block: row start
ISO_N = (4, 8, 12, 16, 20, 24, 28, 32, 28, 24, 20, 16, 12, 8, 4)  # and row width (sum 256)


def block_pixels(data, bp, b):
    """Yield (x, y, bytes) runs of one block, relative to the block's own (x, y)."""
    s = bp + b["data_off"]
    if b["format"] == 1:
        for row in range(15):
            n = ISO_N[row]
            yield ISO_X[row], row, data[s:s + n]
            s += n
        return
    e, x, y = s + b["length"], 0, 0
    while s < e:
        skip, count = data[s], data[s + 1]
        s += 2
        if skip == 0 and count == 0:
            x, y = 0, y + 1
            continue
        x += skip
        yield x, y, data[s:s + count]
        s += count
        x += count


def block_height(b):
    return 15 if b["format"] == 1 else b["rows"]


def render_tile(data, t):
    """Composite one tile's blocks at their (x, y). Returns (width, height, pixels, x0, y0), where
    (x0, y0) is the tile-space position of the image's top-left pixel. Index 0 = transparent."""
    bl = t["blocks"]
    if not bl:
        return 1, 1, bytearray(1), 0, 0
    x0 = min(b["x"] for b in bl)
    y0 = min(b["y"] for b in bl)
    x1 = max(b["x"] + 32 for b in bl)
    y1 = max(b["y"] + block_height(b) for b in bl)
    w, h = x1 - x0, y1 - y0
    px = bytearray(w * h)
    for b in bl:
        bx, by = b["x"] - x0, b["y"] - y0
        for rx, ry, run in block_pixels(data, t["block_ptr"], b):
            off = (by + ry) * w + bx + rx
            for i, v in enumerate(run):  # never let index 0 overwrite an earlier block's pixel
                if v:
                    px[off + i] = v
    return w, h, px, x0, y0


def geometry_check(data, t):
    """Data-only checks of the pixel geometry for one tile (docs/formats/dt1.md, Pixel data).
    Returns (RLE runs ending past column 32, overlapping pixels if this is a floor tile made only of
    0x0001 blocks placed at their header (x, y) with the 4..32..4 row shape, else None)."""
    past = 0
    for b in t["blocks"]:
        if b["format"] != 1:
            past += sum(1 for x, _, run in block_pixels(data, t["block_ptr"], b) if x + len(run) > 32)
    bl = t["blocks"]
    if t["orientation"] != 0 or not bl or any(b["format"] != 1 for b in bl):
        return past, None
    seen, dup = set(), 0
    for b in bl:
        for x, y, run in block_pixels(data, t["block_ptr"], b):
            for i in range(len(run)):
                k = (b["x"] + x + i, b["y"] + y)
                if k in seen:
                    dup += 1
                seen.add(k)
    return past, dup


def contact_sheet(images, max_width=2048, gap=4):
    """Shelf-pack (w, h, pixels) images left to right. Returns (width, height, pixels)."""
    rows, row, rw, rh = [], [], 0, 0
    for im in images:
        if row and rw + im[0] > max_width:
            rows.append((row, rh))
            row, rw, rh = [], 0, 0
        row.append(im)
        rw += im[0] + gap
        rh = max(rh, im[1])
    if row:
        rows.append((row, rh))
    W = max(1, max(sum(im[0] + gap for im in r) for r, _ in rows) if rows else 1)
    H = max(1, sum(rh + gap for _, rh in rows))
    out = bytearray(W * H)
    y = 0
    for r, rh in rows:
        x = 0
        for w, h, px in r:
            for yy in range(h):
                out[(y + yy) * W + x:(y + yy) * W + x + w] = px[yy * w:(yy + 1) * w]
            x += w + gap
        y += rh + gap
    return W, H, out


def render(root, out, sheet=True):
    """Render every tile of every 7.6 DT1. Prints a summary; exits 0 only if no file fails."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import palette
    import png
    tiles_dir = os.path.join(root, "data", "global", "tiles")
    pals = {}
    files = tiles = sheets = bad = 0
    geo = collections.Counter()
    for path in dt1_files(tiles_dir):
        rel = os.path.relpath(path, tiles_dir).replace(os.sep, "/")
        data = open(path, "rb").read()
        if struct.unpack_from("<ii", data, 0) != (7, 6):
            continue
        try:
            h = parse(data)
            pal_name = palette.palette_for_tiles(rel)
            if pal_name not in pals:
                pals[pal_name] = palette.load(root, pal_name)
            pal = pals[pal_name]
            dest = os.path.join(out, "tiles", os.path.splitext(rel)[0])
            seen = collections.Counter()
            images = []
            for t in h["tiles"]:
                key = (t["orientation"], t["main_index"], t["sub_index"])
                n = seen[key]
                seen[key] += 1
                w, hh, px, _, _ = render_tile(data, t)
                past, dup = geometry_check(data, t)
                geo["RLE runs past column 32"] += past
                if dup is not None:
                    geo["iso-only floor tiles"] += 1
                    geo["iso-only floor tiles, %d blocks" % len(t["blocks"])] += 1
                    geo["overlapping pixels in iso-only floor tiles"] += dup
                png.write_indexed(os.path.join(dest, "%d_%d_%d_%d.png" % (key + (n,))), w, hh, px, pal)
                images.append((w, hh, px))
                tiles += 1
            if sheet:
                png.write_indexed(os.path.join(dest, "_sheet.png"), *contact_sheet(images), pal)
                sheets += 1
            files += 1
        except Exception as e:  # report and continue: the summary must name every failure
            bad += 1
            print("FAIL %s: %s: %s" % (rel, type(e).__name__, e))
    print("rendered %d files, %d tiles, %d sheets, failures %d -> %s" % (files, tiles, sheets, bad,
                                                                       os.path.join(out, "tiles")))
    print("geometry:", ", ".join("%s=%d" % kv for kv in sorted(geo.items())))
    geo_bad = geo["RLE runs past column 32"] or geo["overlapping pixels in iso-only floor tiles"]
    return 1 if bad or geo_bad else 0


LVLTYPES_BASE = "DATA\\GLOBAL\\TILES"   # [C] drlg/0002: the logged DT1 names of 520 rooms


def lvltypes(root, ids, base=LVLTYPES_BASE):
    """Dump LvlTypes File 1..32 from lvltypes.bin (layout in excel_layouts.py, diffed clean against
    LvlTypes.txt; docs/tables/LvlTypes.md). Bit i of a DRLG room's DT1 mask selects File i+1 of its
    level type (fn:DRLG_LevelDt1ListBuild@0x0066F240, docs/findings/drlg/0001). The prefixing follows
    sub_0061E4A0_TilePathPrefix as drlg/0001 reads it: '/' -> '\\', then "%s\\%s" (base, cell). The base
    is `DATA\\GLOBAL\\TILES` (upper-case TILES), the prefix of every LvlTypes file in the DT1 lists logged
    for 520 rooms (docs/findings/drlg/0002, plan 0008 P2 fix F2); the three fixed files of
    DRLG_LevelDt1ListBuild carry `DATA\\GLOBAL\\Tiles` instead. Cells holding "0" are printed
    unprefixed: what the loader does with them is not anchored (no mask bit hit one in that run)."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import excel_bin
    import excel_layouts
    excel = os.path.join(root, "data", "global", "excel")
    lay = {f["col"]: f for f in excel_layouts.LAYOUTS["lvltypes"]["fields"]}
    recs, size = excel_bin.read_bin(excel_bin.find_file(excel, "lvltypes", ".bin"))
    assert size == excel_layouts.LAYOUTS["lvltypes"]["size"], size
    names = {}
    tp = excel_bin.find_file(excel, "lvltypes", ".txt")
    if tp:
        header, rows = excel_bin.read_txt(tp)
        names = {i: r[0] for i, r in enumerate(rows)}
    tiles = os.path.join(root, "data", "global", "tiles")
    present = {os.path.relpath(p, tiles).replace(os.sep, "/").lower() for p in dt1_files(tiles)}

    def files(rec):
        return [excel_bin.decode_field(rec, lay["File %d" % (i + 1)]) for i in range(32)]

    if not ids:
        for i, rec in enumerate(recs):
            named = [c for c in files(rec) if c not in ("", "0")]
            print("%2d  act %d  exp %d  %2d files  %s" % (i, excel_bin.decode_field(rec, lay["Act"]),
                  excel_bin.decode_field(rec, lay["Expansion"]), len(named), names.get(i, "")))
        return 0
    bad = [i for i in ids if not 0 <= i < len(recs)]
    if bad:
        print("lvltypes: Id out of range (0..%d): %s" % (len(recs) - 1, " ".join(map(str, bad))),
              file=sys.stderr)
        return 2
    missing = 0
    for i in ids:
        rec = recs[i]
        print("lvltypes[%d] %s  Act %d  Expansion %d  (file offset 0x%X)" % (
            i, names.get(i, ""), excel_bin.decode_field(rec, lay["Act"]),
            excel_bin.decode_field(rec, lay["Expansion"]), 4 + i * size))
        for k, cell in enumerate(files(rec)):
            if cell in ("", "0"):
                print("  File %2d  bit %2d  +0x%03X  %r" % (k + 1, k, 0x3C * k, cell))
                continue
            ok = cell.replace("\\", "/").lower() in present
            missing += not ok
            print("  File %2d  bit %2d  +0x%03X  %s\\%s%s" % (k + 1, k, 0x3C * k, base, cell.replace("/", "\\"),
                                                       "" if ok else "   MISSING"))
    return 1 if missing else 0


def main(argv):
    if len(argv) >= 2 and argv[0] == "lvltypes":
        base = argv[argv.index("--base") + 1] if "--base" in argv else LVLTYPES_BASE
        skip = {argv.index("--base") + 1} if "--base" in argv else set()
        ids = [int(a) for j, a in enumerate(argv[2:], 2) if j not in skip and not a.startswith("--")]
        return lvltypes(argv[1], ids, base)
    if len(argv) >= 2 and argv[0] == "survey":
        return survey(argv[1])
    if len(argv) >= 2 and argv[0] == "dump":
        dump(argv[1], int(argv[2]) if len(argv) > 2 else 5)
        return 0
    if len(argv) >= 2 and argv[0] == "ds1keys":
        shifts = [int(a) for a in argv[2:] if a.isdigit()]
        return ds1keys(argv[1], *shifts[:2], all_files="--all" in argv)
    if len(argv) >= 2 and argv[0] == "render":
        rest = [a for a in argv[2:] if not a.startswith("--")]
        return render(argv[1], rest[0] if rest else os.path.join(argv[1], "..", "render"),
                      sheet="--no-sheet" not in argv)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

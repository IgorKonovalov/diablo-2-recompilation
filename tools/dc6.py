"""Decode Diablo II DC6 sprite files (inventory icons, UI panels, fonts, a few monsters/objects).

Usage:
  python3 -I tools/dc6.py survey <root>                      parse every .dc6, account for every byte
  python3 -I tools/dc6.py dump <file.dc6>                    print header and frame headers of one file
  python3 -I tools/dc6.py render <root> [out] [--palette P] [--only SUBSTR]
                                                             write <out>/dc6/<path>/<dir>_<frame>.png
                                                             (default out: workspace/render)

<root> is a merged data tree (e.g. workspace/merged). Layout in docs/formats/dc6.md. <path> is the
file path relative to <root>/data without the extension, lower-case. The palette is chosen by
palette_for_dc6() (a documented renderer heuristic, not game behaviour) unless --palette is given.
survey ends with one machine-readable line:
  SURVEY dc6 files=N frames=N errors=N leftover_bytes=N
and exits 0 only if errors == 0 and leftover_bytes == 0. Stdlib only. Read-only except render.
"""
import collections
import os
import struct
import sys

HEADER = struct.Struct("<6i")          # version, flags, encoding, terminator, directions, frames_per_dir
FRAME = struct.Struct("<8i")           # flip, width, height, offset_x, offset_y, unk_14, next_block, length
TERM_LEN = 3                           # terminator bytes after each frame's pixel stream


class DC6Error(ValueError):
    pass


def decode_rle(data, pos, end, width, height):
    """Decode one frame's stream data[pos:end]. Returns (rows, stats); rows is a list of bytearrays
    in stream order (stream row 0 = bottom row unless flip). Raises DC6Error on any inconsistency."""
    rows = []
    row = bytearray()
    over = 0
    p = pos
    while p < end:
        b = data[p]
        p += 1
        if b == 0x80:                  # end of row
            rows.append(row)
            row = bytearray()
        elif b & 0x80:                 # skip (b & 0x7F) transparent pixels
            row += b"\0" * (b & 0x7F)
        else:                          # b literal pixels follow
            if p + b > end:
                raise DC6Error("literal run past end of stream")
            row += data[p:p + b]
            p += b
        if len(row) > width:
            over += 1
    if row:
        raise DC6Error("stream does not end with an end-of-row byte")
    if len(rows) != height:
        raise DC6Error("rows %d != height %d" % (len(rows), height))
    if over:
        raise DC6Error("%d rows wider than width %d" % (over, width))
    return rows


def parse(data, decode=True):
    """Parse a whole DC6 file. Returns dict(header, frames) or raises DC6Error. Every byte must be
    covered by header, pointer table, frame headers, pixel streams and terminators."""
    if len(data) < HEADER.size:
        raise DC6Error("file shorter than header")
    version, flags, encoding, term, dirs, fpd = HEADER.unpack_from(data, 0)
    n = dirs * fpd
    if dirs <= 0 or fpd <= 0:
        raise DC6Error("bad direction/frame counts %d/%d" % (dirs, fpd))
    ptab = HEADER.size
    if ptab + 4 * n > len(data):
        raise DC6Error("pointer table past end")
    ptrs = struct.unpack_from("<%dI" % n, data, ptab)
    covered = ptab + 4 * n
    frames = []
    term_bytes = collections.Counter()
    for i, fp in enumerate(ptrs):
        if fp != covered:
            raise DC6Error("frame %d at %d, expected %d (gap or overlap)" % (i, fp, covered))
        if fp + FRAME.size > len(data):
            raise DC6Error("frame %d header past end" % i)
        flip, w, h, ox, oy, unk, nxt, length = FRAME.unpack_from(data, fp)
        s = fp + FRAME.size
        e = s + length
        if length < 0 or e + TERM_LEN > len(data):
            raise DC6Error("frame %d stream past end" % i)
        tb = data[e:e + TERM_LEN]
        term_bytes[tb.hex()] += 1
        rows = None
        if decode:
            if w < 0 or h < 0:
                raise DC6Error("frame %d negative size" % i)
            rows = decode_rle(data, s, e, w, h)
        frames.append(dict(index=i, dir=i // fpd, frame=i % fpd, flip=flip, width=w, height=h,
                           offset_x=ox, offset_y=oy, unk_14=unk, next_block=nxt, next_ok=(nxt == e + TERM_LEN), length=length,
                           term=tb, rows=rows))
        covered = e + TERM_LEN
    leftover = len(data) - covered
    return dict(version=version, flags=flags, encoding=encoding, terminator=term & 0xFFFFFFFF,
                directions=dirs, frames_per_dir=fpd, frames=frames, leftover=leftover,
                term_bytes=term_bytes)


def dc6_files(root):
    out = []
    for dp, dn, fn in os.walk(os.path.join(root, "data"), followlinks=True):
        dn.sort()
        for f in sorted(fn):
            if f.lower().endswith(".dc6"):
                out.append(os.path.join(dp, f))
    return out


def _hist(counter, limit=20, keyfmt=str):
    items = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    s = ", ".join("%s: %d" % (keyfmt(k), v) for k, v in items[:limit])
    if len(items) > limit:
        s += ", ... (%d distinct)" % len(items)
    return s


def _bucket(v):
    if v <= 0:
        return "0"
    lo = 1
    while lo * 2 <= v:
        lo *= 2
    return "%d-%d" % (lo, lo * 2 - 1)


def survey(root):
    files = dc6_files(root)
    errors = leftover = nframes = 0
    hdr = collections.Counter()
    term = collections.Counter()
    shape = collections.Counter()
    fpf = collections.Counter()
    wb = collections.Counter()
    hb = collections.Counter()
    flips = collections.Counter()
    unk = collections.Counter()
    tb = collections.Counter()
    zero = 0
    nxt_bad = collections.Counter()
    tmatch = collections.Counter()
    nxt_files = collections.Counter()
    total_bytes = 0
    largest = (0, "")
    for path in files:
        rel = os.path.relpath(path, root)
        data = open(path, "rb").read()
        total_bytes += len(data)
        try:
            d = parse(data)
        except DC6Error as e:
            errors += 1
            print("FAIL %s: %s" % (rel, e))
            continue
        if d["leftover"]:
            leftover += d["leftover"]
            print("LEFTOVER %s: %d bytes" % (rel, d["leftover"]))
        hdr[(d["version"], d["flags"], d["encoding"])] += 1
        term["%08x" % d["terminator"]] += 1
        shape["%dx%d" % (d["directions"], d["frames_per_dir"])] += 1
        fpf[len(d["frames"])] += 1
        tb.update(d["term_bytes"])
        hb3 = bytes([d["terminator"] & 0xFF] * 3)
        for f in d["frames"]:
            tmatch["header byte x3" if f["term"] == hb3 else ("000000" if f["term"] == b"\0\0\0" else "other")] += 1
        for f in d["frames"]:
            nframes += 1
            wb[_bucket(f["width"])] += 1
            hb[_bucket(f["height"])] += 1
            flips[f["flip"]] += 1
            unk[f["unk_14"]] += 1
            if not f["next_ok"]:
                nxt_bad["%08x" % (f["next_block"] & 0xFFFFFFFF)] += 1
                nxt_files[rel] += 1
            if f["width"] == 0 or f["height"] == 0:
                zero += 1
            if f["width"] * f["height"] > largest[0]:
                largest = (f["width"] * f["height"], "%s %dx%d" % (rel, f["width"], f["height"]))
    print("files %d, bytes %d" % (len(files), total_bytes))
    print("(version, flags, encoding): %s" % _hist(hdr))
    print("header terminator field: %s" % _hist(term))
    print("frame terminator bytes: %s" % _hist(tb))
    print("frame terminator vs header terminator: %s" % _hist(tmatch))
    print("directions x frames_per_dir: %s" % _hist(shape, 30))
    print("frames per file: %s" % _hist(fpf, 30))
    print("frame width buckets: %s" % _hist(wb, 30))
    print("frame height buckets: %s" % _hist(hb, 30))
    print("flip: %s" % _hist(flips))
    print("unk_14: %s" % _hist(unk))
    print("next_block != end of terminator: %d frames in %d files; values %s" % (
        sum(nxt_bad.values()), len(nxt_files), _hist(nxt_bad)))
    print("zero-size frames: %d; largest frame: %s" % (zero, largest[1]))
    print("SURVEY dc6 files=%d frames=%d errors=%d leftover_bytes=%d" % (len(files), nframes, errors, leftover))
    return 1 if errors or leftover else 0


def dump(path):
    d = parse(open(path, "rb").read())
    print("version %d flags %d encoding %d terminator %08x directions %d frames_per_dir %d leftover %d" % (
        d["version"], d["flags"], d["encoding"], d["terminator"], d["directions"], d["frames_per_dir"],
        d["leftover"]))
    for f in d["frames"]:
        print("  [%d,%d] flip %d %dx%d offset (%d,%d) unk_14 %d next %d length %d term %s" % (
            f["dir"], f["frame"], f["flip"], f["width"], f["height"], f["offset_x"], f["offset_y"],
            f["unk_14"], f["next_block"], f["length"], f["term"].hex()))
    return 0


def palette_for_dc6(rel):
    """Heuristic palette for a DC6 path relative to <root>/data (docs/formats/dc6.md). Not game behaviour."""
    r = rel.replace("\\", "/").lower()
    if r.startswith("global/ui/loading/"):
        return "loading"
    return "units"


def frame_pixels(f):
    """Indexed pixels, top row first: stream rows are bottom-up unless flip != 0."""
    w, h = f["width"], f["height"]
    px = bytearray(w * h)
    rows = f["rows"] if f["flip"] else list(reversed(f["rows"]))
    for y, row in enumerate(rows):
        px[y * w:y * w + len(row)] = row
    return px


def render_tree(root, out, palette=None, only=None):
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import palette as pal
    import png
    cache = {}
    nfiles = nframes = bad = 0
    for path in dc6_files(root):
        rel = os.path.relpath(path, os.path.join(root, "data")).replace("\\", "/").lower()
        if only and only.lower() not in rel:
            continue
        name = palette or palette_for_dc6(rel)
        if name not in cache:
            cache[name] = pal.load(root, name)
        try:
            d = parse(open(path, "rb").read())
        except DC6Error as e:
            bad += 1
            print("FAIL %s: %s" % (rel, e))
            continue
        dest = os.path.join(out, "dc6", os.path.splitext(rel)[0])
        for f in d["frames"]:
            png.write_indexed(os.path.join(dest, "%d_%d.png" % (f["dir"], f["frame"])),
                              f["width"], f["height"], frame_pixels(f), cache[name])
            nframes += 1
        nfiles += 1
    print("dc6 render: files %d, frames %d, failures %d -> %s" % (nfiles, nframes, bad, os.path.join(out, "dc6")))
    return 1 if bad else 0


def render(root, out):
    """render_all.py hook: every DC6 frame into <out>/dc6/ with the heuristic palettes."""
    return render_tree(root, out)


def main(argv):
    if len(argv) >= 2 and argv[0] == "survey":
        return survey(argv[1])
    if len(argv) >= 2 and argv[0] == "dump":
        return dump(argv[1])
    if len(argv) >= 2 and argv[0] == "render":
        args = argv[1:]
        opts = {}
        for key in ("--palette", "--only"):
            if key in args:
                i = args.index(key)
                opts[key] = args[i + 1]
                del args[i:i + 2]
        root = args[0]
        out = args[1] if len(args) > 1 else os.path.join(root, "..", "render")
        return render_tree(root, out, opts.get("--palette"), opts.get("--only"))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

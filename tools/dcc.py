"""Decode Diablo II DCC animation files (monsters, player layers, objects, missiles, overlays).

Usage:
  python3 -I tools/dcc.py survey <root> [--jobs N]          parse and decode every .dcc, account for every bit
  python3 -I tools/dcc.py dump <file.dcc>                    print header, direction and frame headers of one file
  python3 -I tools/dcc.py render <root> [out] [--palette P] [--only SUBSTR] [--jobs N]
                                                             write <out>/dcc/<path>/<dir>_<frame>.png
                                                             (default out: workspace/render)

<root> is a merged data tree (e.g. workspace/merged). Layout in docs/formats/dcc.md. <path> is the
file path relative to <root>/data without the extension, lower-case. Each frame is written at its
own box (width x height from its frame header); index 0 is transparent. The palette is `units`
unless --palette is given (a renderer heuristic, not game behaviour).
survey ends with one machine-readable line:
  SURVEY dcc files=N directions=N frames=N errors=N leftover_bits=N
where leftover_bits counts bits of a fixed-size stream that were not consumed (or that a decode
tried to read past its end) plus pixel-code-stream tail bits beyond byte padding (>= 8). It exits
0 only if errors == 0 and leftover_bits == 0. Stdlib only. Read-only except render.
"""
import collections
import os
import struct
import sys

SIGNATURE = 0x74
WIDTHS = (0, 1, 2, 4, 6, 8, 10, 12, 14, 16, 20, 24, 26, 28, 30, 32)   # 4-bit code -> field bit width
FIELDS = ("variable0", "width", "height", "offset_x", "offset_y", "optional_bytes", "coded_bytes")
SIGNED = ("offset_x", "offset_y")


class DCCError(ValueError):
    pass


class Bits:
    """LSB-first bit reader over data[start_bit:end_bit]."""
    __slots__ = ("d", "pos", "end")

    def __init__(self, data, pos, end):
        self.d, self.pos, self.end = data, pos, end

    def read(self, n):
        if n == 0:
            return 0
        p = self.pos
        if p + n > self.end:
            raise DCCError("read past end of stream (%d+%d > %d)" % (p, n, self.end))
        b = p >> 3
        v = int.from_bytes(self.d[b:b + ((p & 7) + n + 7 >> 3)], "little") >> (p & 7)
        self.pos = p + n
        return v & ((1 << n) - 1)


def parse_header(data):
    if len(data) < 15:
        raise DCCError("file shorter than header")
    sig, ver, ndir, fpd, tag, total = struct.unpack_from("<BBBIII", data, 0)
    if sig != SIGNATURE:
        raise DCCError("signature %#x" % sig)
    if ndir == 0 or fpd == 0:
        raise DCCError("no directions or frames")
    offs = list(struct.unpack_from("<%dI" % ndir, data, 15))
    hdr_end = 15 + 4 * ndir
    if offs[0] != hdr_end:
        raise DCCError("first direction at %d, header ends at %d" % (offs[0], hdr_end))
    ends = offs[1:] + [len(data)]
    for a, b in zip(offs, ends):
        if not a < b <= len(data):
            raise DCCError("direction bounds %d..%d" % (a, b))
    return dict(signature=sig, version=ver, directions=ndir, frames_per_dir=fpd, tag=tag,
                total=total, dir_bounds=list(zip(offs, ends)))


def _cells(start, size):
    """Split a span [start, start+size) (relative to the direction box) into 4-pixel grid cells.
    Returns [(pos, len)] aligned to multiples of 4 in direction coordinates."""
    out = []
    first = 4 - (start % 4)
    if size - first <= 1:     # fits in the first cell (one spare pixel is absorbed)
        return [(start, size)]
    out.append((start, first))
    p, rest = start + first, size - first
    while rest > 4:
        if rest - 4 <= 1:     # last cell absorbs a 1-pixel remainder
            break
        out.append((p, 4))
        p += 4
        rest -= 4
    out.append((p, rest))
    return out


def decode_direction(data, a, b, fpd, pixels=True):
    """Decode one direction stored in data[a:b]. Returns a dict with frame headers, stream
    accounting and (if pixels) a list of frame bitmaps (bytearray width*height, top row first)."""
    end = (b - a) * 8
    bs = Bits(data[a:b], 0, end)
    d = {}
    d["outsize_coded"] = bs.read(32)
    d["compression"] = bs.read(2)
    codes = [bs.read(4) for _ in FIELDS]
    d["field_bits"] = [WIDTHS[c] for c in codes]
    frames = []
    for i in range(fpd):
        f = {}
        for name, n in zip(FIELDS, d["field_bits"]):
            v = bs.read(n)
            if name in SIGNED and n and v & (1 << (n - 1)):
                v -= 1 << n
            f[name] = v
        f["bottom_up"] = bs.read(1)
        if f["width"] == 0 or f["height"] == 0:
            raise DCCError("frame %d has zero size" % i)
        f["xmin"] = f["offset_x"]
        f["xmax"] = f["xmin"] + f["width"] - 1
        if f["bottom_up"]:
            f["ymin"] = f["offset_y"]
            f["ymax"] = f["ymin"] + f["height"] - 1
        else:
            f["ymax"] = f["offset_y"]
            f["ymin"] = f["ymax"] - f["height"] + 1
        frames.append(f)
    d["frames"] = frames
    opt = sum(f["optional_bytes"] for f in frames)
    d["align_pad"] = 0
    if opt:
        pad = (-bs.pos) % 8
        d["align_pad"] = pad
        if bs.read(pad):
            d["align_pad_nonzero"] = True
        d["optional"] = [bytes(bs.read(8) for _ in range(f["optional_bytes"])) for f in frames]
    comp = d["compression"]
    sizes = {}
    sizes["equal_cell"] = bs.read(20) if comp & 2 else None
    sizes["pixel_mask"] = bs.read(20)
    if comp & 1:
        sizes["encoding_type"] = bs.read(20)
        sizes["raw_pixel"] = bs.read(20)
    else:
        sizes["encoding_type"] = sizes["raw_pixel"] = None
    key = [i for i in range(256) if bs.read(1)]
    d["pixel_values"] = key
    streams = {}
    p = bs.pos
    for name in ("equal_cell", "pixel_mask", "encoding_type", "raw_pixel"):
        n = sizes[name]
        if n is None:
            continue
        streams[name] = Bits(bs.d, p, p + n)
        p += n
    if p > end:
        raise DCCError("stream sizes overrun the direction (%d > %d bits)" % (p, end))
    streams["pixel_code"] = Bits(bs.d, p, end)
    d["sizes"] = sizes
    d["pixel_code_bits"] = end - p
    d["streams"] = streams

    # direction box and cell grid
    xmin = min(f["xmin"] for f in frames)
    xmax = max(f["xmax"] for f in frames)
    ymin = min(f["ymin"] for f in frames)
    ymax = max(f["ymax"] for f in frames)
    dw, dh = xmax - xmin + 1, ymax - ymin + 1
    d["box"] = (xmin, ymin, dw, dh)
    ncw = 1 + (dw - 1) // 4
    nch = 1 + (dh - 1) // 4
    for f in frames:
        f["cols"] = _cells(f["xmin"] - xmin, f["width"])
        f["rows"] = _cells(f["ymin"] - ymin, f["height"])

    eq = streams.get("equal_cell")
    pm = streams["pixel_mask"]
    et = streams.get("encoding_type")
    rp = streams.get("raw_pixel")
    pc = streams["pixel_code"]

    # stage 1: cell pixel-value entries
    last = [None] * (ncw * nch)       # last entry (4 values) per direction cell
    entries = []                      # per frame: list over frame cells of 4-tuple or None (equal cell)
    for f in frames:
        fe = []
        for (y0, h) in f["rows"]:
            cy = y0 // 4
            for (x0, w) in f["cols"]:
                ci = x0 // 4 + cy * ncw
                old = last[ci]
                if old is not None:
                    if eq is not None and eq.read(1):
                        fe.append(None)
                        continue
                    mask = pm.read(4)
                else:
                    mask = 0xF
                nb = (mask & 1) + (mask >> 1 & 1) + (mask >> 2 & 1) + (mask >> 3 & 1)
                enc = et.read(1) if (nb and et is not None) else 0
                got = []
                lastpix = 0
                for _ in range(nb):
                    if enc:
                        v = rp.read(8)
                    else:
                        v = lastpix
                        disp = pc.read(4)
                        v += disp
                        while disp == 15:
                            disp = pc.read(4)
                            v += disp
                    if v == lastpix:
                        break
                    got.append(v)
                    lastpix = v
                vals = [0, 0, 0, 0]
                k = len(got) - 1
                for i in range(4):
                    if mask & (1 << i):
                        if k >= 0:
                            vals[i] = got[k]
                            k -= 1
                    else:
                        vals[i] = old[i]
                last[ci] = vals
                fe.append(vals)
        entries.append(fe)
    nkey = len(key)
    for fe in entries:
        for vals in fe:
            if vals is not None:
                for v in vals:
                    if v >= nkey:
                        raise DCCError("pixel value index %d beyond key size %d" % (v, nkey))

    # stage 2: pixels
    canvas = bytearray(dw * dh)
    lastgeo = [None] * (ncw * nch)    # (x0, y0, w, h) where each direction cell was last drawn
    out = []
    read = pc.read
    for f, fe in zip(frames, entries):
        i = 0
        for (y0, h) in f["rows"]:
            cy = y0 // 4
            for (x0, w) in f["cols"]:
                ci = x0 // 4 + cy * ncw
                vals = fe[i]
                i += 1
                if vals is None:
                    lx, ly, lw, lh = lastgeo[ci]
                    if (lw, lh) == (w, h):
                        if (lx, ly) != (x0, y0):
                            rows = [bytes(canvas[(ly + r) * dw + lx:(ly + r) * dw + lx + w]) for r in range(h)]
                            for r in range(h):
                                canvas[(y0 + r) * dw + x0:(y0 + r) * dw + x0 + w] = rows[r]
                    else:
                        for r in range(h):
                            canvas[(y0 + r) * dw + x0:(y0 + r) * dw + x0 + w] = bytes(w)
                else:
                    c = [key[v] for v in vals]
                    if vals[0] == vals[1]:
                        row = bytes([c[0]]) * w
                        for r in range(h):
                            canvas[(y0 + r) * dw + x0:(y0 + r) * dw + x0 + w] = row
                    else:
                        nbit = 1 if vals[1] == vals[2] else 2
                        msk = (1 << nbit) - 1
                        for r in range(h):
                            bits = read(nbit * w)
                            row = bytearray(w)
                            for x in range(w):
                                row[x] = c[bits & msk]
                                bits >>= nbit
                            canvas[(y0 + r) * dw + x0:(y0 + r) * dw + x0 + w] = row
                lastgeo[ci] = (x0, y0, w, h)
        if pixels:
            fx, fy = f["xmin"] - xmin, f["ymin"] - ymin
            fw, fh = f["width"], f["height"]
            bm = bytearray(fw * fh)
            for r in range(fh):
                bm[r * fw:(r + 1) * fw] = canvas[(fy + r) * dw + fx:(fy + r) * dw + fx + fw]
            out.append(bm)
    d["bitmaps"] = out
    d["consumed"] = {k: s.pos - (s.end - (sizes[k] if k != "pixel_code" else d["pixel_code_bits"]))
                     for k, s in streams.items()}
    d["unread"] = {k: s.end - s.pos for k, s in streams.items()}
    return d


def parse(data, pixels=True):
    h = parse_header(data)
    h["dirs"] = [decode_direction(data, a, b, h["frames_per_dir"], pixels) for a, b in h["dir_bounds"]]
    return h


def dcc_files(root):
    out = []
    for dp, dn, fn in os.walk(os.path.join(root, "data"), followlinks=True):
        dn.sort()
        for f in sorted(fn):
            if f.lower().endswith(".dcc"):
                out.append(os.path.join(dp, f))
    return out


def _hist(counter, limit=20, keyfmt=str):
    items = sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0])))
    s = ", ".join("%s: %d" % (keyfmt(k), v) for k, v in items[:limit])
    if len(items) > limit:
        s += ", ... (%d distinct)" % len(items)
    return s


def _survey_one(args):
    root, path = args
    rel = os.path.relpath(path, root)
    data = open(path, "rb").read()
    r = dict(rel=rel, size=len(data), error=None, notes=[], leftover=0, dirs=0, frames=0, c={})
    c = collections.defaultdict(collections.Counter)
    try:
        h = parse(data, pixels=False)
    except (DCCError, IndexError) as e:
        r["error"] = str(e)
        return r
    c["version"][h["version"]] += 1
    c["tag"][h["tag"]] += 1
    c["directions"][h["directions"]] += 1
    c["frames_per_dir"][h["frames_per_dir"]] += 1
    r["dirs"] = h["directions"]
    r["frames"] = h["directions"] * h["frames_per_dir"]
    outsum = 0
    pixsum = 0
    for di, d in enumerate(h["dirs"]):
        c["compression"][d["compression"]] += 1
        c["field_bits"][tuple(d["field_bits"])] += 1
        c["align_pad"][d["align_pad"]] += 1
        if d.get("align_pad_nonzero"):
            r["notes"].append("dir %d: non-zero alignment pad bits" % di)
        outsum += d["outsize_coded"]
        npx = sum(f["width"] * f["height"] for f in d["frames"])
        pixsum += npx
        c["outsize_vs_pixels"]["eq" if d["outsize_coded"] == npx else "ne"] += 1
        c["key_size"][(len(d["pixel_values"]) + 31) // 32 * 32] += 1
        c["key_has_0"][0 in d["pixel_values"]] += 1
        for k, u in d["unread"].items():
            if k == "pixel_code":
                c["pixel_code_tail_bits"][u] += 1
                if u >= 8:
                    r["leftover"] += u
                    r["notes"].append("dir %d: pixel_code tail %d bits" % (di, u))
            elif u:
                r["leftover"] += u
                r["notes"].append("dir %d: %s stream %d bits unread" % (di, k, u))
        for f in d["frames"]:
            c["variable0"][f["variable0"]] += 1
            c["optional_bytes"][f["optional_bytes"]] += 1
            c["bottom_up"][f["bottom_up"]] += 1
            c["coded_bytes_zero"][f["coded_bytes"] == 0] += 1
    c["total_vs_sum_outsize"]["eq" if h["total"] == outsum else "ne"] += 1
    c["total_vs_pixels"]["eq" if h["total"] == pixsum else "ne"] += 1
    r["c"] = {k: dict(v) for k, v in c.items()}
    return r


def _pool(jobs):
    import multiprocessing
    return multiprocessing.Pool(jobs)


def survey(root, jobs=None):
    files = dcc_files(root)
    jobs = jobs or os.cpu_count() or 1
    tot = collections.defaultdict(collections.Counter)
    errors = leftover = ndirs = nframes = nbytes = 0
    fails = []
    with _pool(jobs) as pool:
        for r in pool.imap(_survey_one, [(root, p) for p in files], chunksize=8):
            nbytes += r["size"]
            if r["error"]:
                errors += 1
                fails.append(r)
                print("FAIL %s: %s" % (r["rel"], r["error"]))
                continue
            for n in r["notes"]:
                print("NOTE %s: %s" % (r["rel"], n))
            leftover += r["leftover"]
            ndirs += r["dirs"]
            nframes += r["frames"]
            for k, v in r["c"].items():
                tot[k].update(v)
    print("files %d, bytes %d" % (len(files), nbytes))
    for k in ("version", "tag", "directions", "frames_per_dir", "compression", "field_bits", "align_pad",
              "variable0", "optional_bytes", "bottom_up", "coded_bytes_zero", "key_size", "key_has_0",
              "outsize_vs_pixels", "total_vs_sum_outsize", "total_vs_pixels", "pixel_code_tail_bits"):
        print("%s: %s" % (k, _hist(tot[k], 25)))
    print("SURVEY dcc files=%d directions=%d frames=%d errors=%d leftover_bits=%d" % (
        len(files), ndirs, nframes, errors, leftover))
    return 1 if errors or leftover else 0


def dump(path):
    data = open(path, "rb").read()
    h = parse(data, pixels=False)
    print("signature %#x version %d directions %d frames_per_dir %d tag %d total %d" % (
        h["signature"], h["version"], h["directions"], h["frames_per_dir"], h["tag"], h["total"]))
    for di, ((a, b), d) in enumerate(zip(h["dir_bounds"], h["dirs"])):
        print("dir %d @%d len %d: outsize %d compression %d bits %s box %s key %d sizes %s pixel_code %d unread %s" % (
            di, a, b - a, d["outsize_coded"], d["compression"], d["field_bits"], d["box"],
            len(d["pixel_values"]), d["sizes"], d["pixel_code_bits"], d["unread"]))
        for fi, f in enumerate(d["frames"]):
            print("  [%d,%d] v0 %d %dx%d offset (%d,%d) opt %d coded %d bottom_up %d" % (
                di, fi, f["variable0"], f["width"], f["height"], f["offset_x"], f["offset_y"],
                f["optional_bytes"], f["coded_bytes"], f["bottom_up"]))
    return 0


def _render_one(args):
    root, out, path, palname = args
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import palette as pal
    import png
    rel = os.path.relpath(path, os.path.join(root, "data")).replace("\\", "/").lower()
    pl = pal.load(root, palname)
    try:
        h = parse(open(path, "rb").read())
    except (DCCError, IndexError) as e:
        return rel, -1, str(e)
    dest = os.path.join(out, "dcc", os.path.splitext(rel)[0])
    n = 0
    for di, d in enumerate(h["dirs"]):
        for fi, (f, bm) in enumerate(zip(d["frames"], d["bitmaps"])):
            png.write_indexed(os.path.join(dest, "%d_%d.png" % (di, fi)), f["width"], f["height"], bm, pl)
            n += 1
    return rel, n, None


def render_tree(root, out, palette=None, only=None, jobs=None):
    jobs = jobs or os.cpu_count() or 1
    work = []
    for path in dcc_files(root):
        rel = os.path.relpath(path, os.path.join(root, "data")).replace("\\", "/").lower()
        if only and only.lower() not in rel:
            continue
        work.append((root, out, path, palette or "units"))
    nfiles = nframes = bad = 0
    with _pool(jobs) as pool:
        for rel, n, err in pool.imap_unordered(_render_one, work, chunksize=4):
            if err:
                bad += 1
                print("FAIL %s: %s" % (rel, err))
                continue
            nfiles += 1
            nframes += n
    print("dcc render: files %d, frames %d, failures %d -> %s" % (nfiles, nframes, bad, os.path.join(out, "dcc")))
    return 1 if bad else 0


def render(root, out):
    """render_all.py hook: every DCC frame into <out>/dcc/ with the units palette."""
    return render_tree(root, out)


def main(argv):
    args = list(argv)
    opts = {}
    for key in ("--palette", "--only", "--jobs"):
        if key in args:
            i = args.index(key)
            opts[key] = args[i + 1]
            del args[i:i + 2]
    jobs = int(opts["--jobs"]) if "--jobs" in opts else None
    if len(args) >= 2 and args[0] == "survey":
        return survey(args[1], jobs)
    if len(args) >= 2 and args[0] == "dump":
        return dump(args[1])
    if len(args) >= 2 and args[0] == "render":
        root = args[1]
        out = args[2] if len(args) > 2 else os.path.join(root, "..", "render")
        return render_tree(root, out, opts.get("--palette"), opts.get("--only"), jobs)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Parse Diablo II COF files and compose one frame of a unit from its layer DCCs.

Usage:
  python3 -I tools/cof.py survey <root>                      parse every .cof, account for every byte
  python3 -I tools/cof.py dump <file.cof>                    print header, layers, frame bytes, order
  python3 -I tools/cof.py compose <root> <unit dir> <mode> <wclass> [out]
        [--dirs 0,4,...] [--frame N] [--part LAYER=PART,...] [--palette P]
                                                             write <out>/units/<token>/<mode>_<dir>.png
                                                             (default out: workspace/render)

<root> is a merged data tree (e.g. workspace/merged). <unit dir> is relative to <root>/data/global
(e.g. monsters/fa, chars/ai). Layout in docs/formats/cof.md.

survey ends with one machine-readable line:
  SURVEY cof files=N layers=N frames=N errors=N leftover_bytes=N
where layers sums the layer count over files, frames sums directions x frames_per_dir, and
leftover_bytes counts bytes between the frame bytes and the order block that no field accounts for
(3 known files, documented in cof.md; the gate baseline pins the count). It exits 0 iff errors == 0.

compose is a renderer heuristic, not game behaviour: layer index -> directory comes from
excel/composit.txt row order, the DCC part (lit, hvy, ...) is --part or else `lit` or else the
first in name order, the order block is read direction-major and drawn first-to-last (first
drawn = furthest back), index 0 is transparent, palette `units` by default. All of that is [L]
in cof.md. Stdlib only. Read-only except compose.
"""
import collections
import os
import struct
import sys

HEADER = 28
LAYER = 9
UNKNOWN = "unknown"


class COFError(ValueError):
    pass


def parse(data):
    """Return a dict: header fields, layers, frame_bytes, order (list of per-group tuples), extra."""
    if len(data) < HEADER:
        raise COFError("file shorter than the 28-byte header")
    nl, nf, nd, b3, b4 = data[0], data[1], data[2], data[3], data[4]
    if not nl or not nf or not nd:
        raise COFError("zero layers, frames or directions")
    box = struct.unpack_from("<4i", data, 8)
    rate = struct.unpack_from("<i", data, 24)[0]
    need = HEADER + LAYER * nl + nf + nd * nf * nl
    if len(data) < need:
        raise COFError("size %d < %d" % (len(data), need))
    layers = []
    for i in range(nl):
        r = data[HEADER + LAYER * i:HEADER + LAYER * (i + 1)]
        if r[0] > 15:
            raise COFError("layer %d: component %d > 15" % (i, r[0]))
        if r[8] != 0:
            raise COFError("layer %d: weapon-class field not NUL-terminated" % i)
        layers.append(dict(component=r[0], b1=r[1], b2=r[2], b3=r[3], b4=r[4],
                           wclass=r[5:8].decode("latin-1").rstrip("\0").lower()))
    comps = [l["component"] for l in layers]
    if len(set(comps)) != nl:
        raise COFError("duplicate component in layer records")
    fb_at = HEADER + LAYER * nl
    frame_bytes = data[fb_at:fb_at + nf]
    order_at = len(data) - nd * nf * nl
    extra = order_at - (fb_at + nf)
    want = sorted(comps)
    order = []
    for g in range(nd * nf):
        grp = tuple(data[order_at + g * nl:order_at + (g + 1) * nl])
        if sorted(grp) != want:
            raise COFError("order group %d is not a permutation of the layer components" % g)
        order.append(grp)
    return dict(layers_n=nl, frames_per_dir=nf, directions=nd, byte3=b3, byte4=b4,
                bytes5_7=data[5:8], box=box, rate=rate, layers=layers, frame_bytes=frame_bytes,
                order=order, extra=extra, extra_bytes=data[fb_at + nf:order_at])


def cof_files(root):
    out = []
    for dp, dn, fn in os.walk(os.path.join(root, "data"), followlinks=True):
        dn.sort()
        for f in sorted(fn):
            if f.lower().endswith(".cof"):
                out.append(os.path.join(dp, f))
    return out


def _hist(c, limit=16):
    items = sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0])))
    s = ", ".join("%s: %d" % kv for kv in items[:limit])
    if len(items) > limit:
        s += ", ... (%d distinct)" % len(items)
    return s


def survey(root):
    files = cof_files(root)
    c = collections.defaultdict(collections.Counter)
    errors = leftover = nlayers = nframes = nbytes = 0
    changes = collections.Counter()
    for p in files:
        rel = os.path.relpath(p, root)
        data = open(p, "rb").read()
        nbytes += len(data)
        try:
            h = parse(data)
        except COFError as e:
            errors += 1
            print("FAIL %s: %s" % (rel, e))
            continue
        if h["extra"]:
            leftover += h["extra"]
            print("NOTE %s: %d bytes between frame bytes and order block: %s" % (
                rel, h["extra"], h["extra_bytes"].hex()))
        nl, nf, nd = h["layers_n"], h["frames_per_dir"], h["directions"]
        nlayers += nl
        nframes += nd * nf
        c["layers"][nl] += 1
        c["frames_per_dir"][nf] += 1
        c["directions"][nd] += 1
        c["byte3"][h["byte3"]] += 1
        c["byte4"][h["byte4"]] += 1
        c["bytes5_7"][h["bytes5_7"].hex()] += 1
        for k, v in zip(("box0", "box1", "box2", "box3"), h["box"]):
            c[k + "_sign"][(v > 0) - (v < 0)] += 1
        c["box0<=box1"][h["box"][0] <= h["box"][1]] += 1
        c["box2<=box3"][h["box"][2] <= h["box"][3]] += 1
        c["rate"][h["rate"]] += 1
        for l in h["layers"]:
            c["component"][l["component"]] += 1
            for k in ("b1", "b2", "b3", "b4"):
                c["layer_" + k][l[k]] += 1
            c["wclass"][l["wclass"]] += 1
        for b in h["frame_bytes"]:
            c["frame_byte"][b] += 1
        c["nonzero_frame_bytes_per_file"][sum(1 for b in h["frame_bytes"] if b)] += 1
        o = h["order"]
        for d in range(nd):
            for f in range(1, nf):
                changes["dir_major"] += o[d * nf + f] != o[d * nf + f - 1]
                changes["frame_major"] += o[f * nd + d] != o[(f - 1) * nd + d]
    print("files %d, bytes %d" % (len(files), nbytes))
    for k in ("layers", "frames_per_dir", "directions", "byte3", "byte4", "bytes5_7", "box0_sign",
              "box1_sign", "box2_sign", "box3_sign", "box0<=box1", "box2<=box3", "rate", "component",
              "layer_b1", "layer_b2", "layer_b3", "layer_b4", "wclass", "frame_byte",
              "nonzero_frame_bytes_per_file"):
        print("%s: %s" % (k, _hist(c[k])))
    print("order groups that differ from the previous frame of the same direction: "
          "read direction-major %d, read frame-major %d" % (changes["dir_major"], changes["frame_major"]))
    print("SURVEY cof files=%d layers=%d frames=%d errors=%d leftover_bytes=%d" % (
        len(files), nlayers, nframes, errors, leftover))
    return 1 if errors else 0


def dump(path):
    h = parse(open(path, "rb").read())
    print("layers %d frames_per_dir %d directions %d byte3 %d byte4 %d bytes5_7 %s box %s rate %d extra %d" % (
        h["layers_n"], h["frames_per_dir"], h["directions"], h["byte3"], h["byte4"], h["bytes5_7"].hex(),
        h["box"], h["rate"], h["extra"]))
    for i, l in enumerate(h["layers"]):
        print("  layer %d: component %d b1 %d b2 %d b3 %d b4 %d wclass %s" % (
            i, l["component"], l["b1"], l["b2"], l["b3"], l["b4"], l["wclass"]))
    print("frame bytes: %s" % " ".join(str(b) for b in h["frame_bytes"]))
    nf = h["frames_per_dir"]
    for d in range(h["directions"]):
        print("  dir %2d: %s" % (d, " ".join("".join("%x" % x for x in g) for g in h["order"][d * nf:(d + 1) * nf])))
    return 0


# ---------------------------------------------------------------- composition (heuristic)

def components(root):
    """Layer index -> directory token, from excel/composit.txt row order (heuristic, cof.md)."""
    p = os.path.join(root, "data", "global", "excel", "composit.txt")
    rows = open(p, encoding="latin-1").read().splitlines()[1:]
    return [r.split("\t")[1].strip().lower() for r in rows if r.strip()]


def pick_dcc(unit, token, layer, mode, wclass, part=None):
    d = os.path.join(unit, layer)
    if not os.path.isdir(d):
        return None
    pre, suf = token + layer, mode + wclass + ".dcc"
    cands = sorted(f for f in os.listdir(d) if f.lower().startswith(pre) and f.lower().endswith(suf)
                   and len(f) == len(pre) + 3 + len(suf))
    if not cands:
        return None
    for want in ([part] if part else []) + ["lit"]:
        for f in cands:
            if f.lower()[len(pre):len(pre) + 3] == want:
                return os.path.join(d, f)
    return os.path.join(d, cands[0])


def compose(root, unit_rel, mode, wclass, out, dirs=None, frame=0, parts=None, palname="units"):
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import dcc
    import palette as pal
    import png
    parts = parts or {}
    unit = os.path.join(root, "data", "global", unit_rel)
    token = os.path.basename(unit_rel.rstrip("/")).lower()
    cof_path = os.path.join(unit, "cof", token + mode + wclass + ".cof")
    h = parse(open(cof_path, "rb").read())
    names = components(root)
    nd, nf = h["directions"], h["frames_per_dir"]
    frame = min(frame, nf - 1)
    pl = pal.load(root, palname)
    rc = 0
    for di in (dirs if dirs is not None else range(nd)):
        if di >= nd:
            print("skip dir %d: COF has %d directions" % (di, nd))
            continue
        group = h["order"][di * nf + frame]
        by_comp = {l["component"]: l for l in h["layers"]}
        placed = []
        for comp in group:
            l = by_comp[comp]
            name = names[comp]
            path = pick_dcc(unit, token, name, mode, l["wclass"], parts.get(name))
            if not path:
                print("  dir %d layer %s: no DCC (%s%s???%s%s.dcc)" % (di, name, token, name, mode, l["wclass"]))
                continue
            data = open(path, "rb").read()
            dh = dcc.parse_header(data)
            # same direction index when counts match; otherwise scale (heuristic)
            ddi = di if dh["directions"] == nd else di * dh["directions"] // nd
            a, b = dh["dir_bounds"][ddi]
            dd = dcc.decode_direction(data, a, b, dh["frames_per_dir"])
            fi = min(frame, dh["frames_per_dir"] - 1)
            placed.append((name, os.path.basename(path), dd["frames"][fi], dd["bitmaps"][fi]))
        if not placed:
            rc = 1
            continue
        x0 = min(f["xmin"] for _, _, f, _ in placed)
        y0 = min(f["ymin"] for _, _, f, _ in placed)
        x1 = max(f["xmax"] for _, _, f, _ in placed)
        y1 = max(f["ymax"] for _, _, f, _ in placed)
        w, hgt = x1 - x0 + 1, y1 - y0 + 1
        canvas = bytearray(w * hgt)
        for _, _, f, bm in placed:          # first in the order group is drawn first (furthest back)
            fx, fy, fw = f["xmin"] - x0, f["ymin"] - y0, f["width"]
            for r in range(f["height"]):
                row = (fy + r) * w + fx
                src = bm[r * fw:(r + 1) * fw]
                for c, v in enumerate(src):
                    if v:
                        canvas[row + c] = v
        dest = os.path.join(out, "units", token, "%s_%d.png" % (mode, di))
        png.write_indexed(dest, w, hgt, canvas, pl)
        print("dir %d frame %d: %s -> %s" % (di, frame, " ".join("%s:%s" % (n, f) for n, f, _, _ in placed), dest))
    return rc


def main(argv):
    args = list(argv)
    opts = {}
    for key in ("--dirs", "--frame", "--part", "--palette"):
        if key in args:
            i = args.index(key)
            opts[key] = args[i + 1]
            del args[i:i + 2]
    if len(args) >= 2 and args[0] == "survey":
        return survey(args[1])
    if len(args) >= 2 and args[0] == "dump":
        return dump(args[1])
    if len(args) >= 5 and args[0] == "compose":
        root = args[1]
        out = args[5] if len(args) > 5 else os.path.join(root, "..", "render")
        dirs = [int(x) for x in opts["--dirs"].split(",")] if "--dirs" in opts else None
        parts = dict(kv.split("=", 1) for kv in opts["--part"].lower().split(",")) if "--part" in opts else {}
        return compose(root, args[2], args[3].lower(), args[4].lower(), out, dirs,
                       int(opts.get("--frame", 0)), parts, opts.get("--palette", "units"))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

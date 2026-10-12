"""Decode Diablo II palettes (pal.dat) and check pal.pl2's leading palette copy.

Usage:
  python3 -I tools/palette.py survey <root>        check every palette/<name>/pal.dat (and pal.pl2 prefix)
  python3 -I tools/palette.py swatch <root> <out>  write one 16x16-swatch PNG per palette into <out>
  python3 -I tools/palette.py itempal <root>       check every items/palette/*.dat against colors.txt
                                                   (last line: SURVEY itempal files=N maps=N ... errors=N)
  python3 -I tools/palette.py itemswatch <root> <out> [--palette P]
                                                   one PNG per .dat: 21 rows (one per map) of 256 swatches

<root> is a merged data tree (e.g. workspace/merged). Layout in docs/formats/palette.md.
Item colour shifts (docs/formats/item-palette.md): items/palette/<name>.dat is 21 maps of 256
palette indices; shift_rgb() turns a palette plus one map into a shifted palette (index i shows the
colour of map[i], index 0 kept, since 0 is transparent in DC6/DCC renders). Which file and which map
the game uses for an item is not decided here: ITEM_SHIFT_FILES is a lead, see the format doc.
pal.dat is 256 entries of 3 bytes stored B, G, R; load() returns R, G, B (768 bytes) ready for
tools/png.py. Which palette the game uses for an asset is code behaviour and not decided here;
palette_for_tiles() is a documented renderer heuristic. Stdlib only. Read-only except swatch.
"""
import os
import sys

PALETTE_DIR = os.path.join("data", "global", "palette")
PL2_PREFIX = 1024
ITEM_PALETTE_DIR = os.path.join("data", "global", "items", "palette")
ITEM_MAP_SIZE = 256
# [L] transform type n (1..8) -> ITEM_SHIFT_FILES[n - 1]: the order in which two code sites push
# these names (0x00505556.., 0x00600B86..), not yet read by the reverser. docs/formats/item-palette.md
ITEM_SHIFT_FILES = ("grey", "grey2", "gold", "brown", "greybrown", "invgrey", "invgrey2", "invgreybrown")


class PaletteError(ValueError):
    pass


def decode_dat(data):
    """pal.dat bytes -> 768 bytes R,G,B (the file stores B,G,R)."""
    if len(data) != 768:
        raise PaletteError("pal.dat is %d bytes, not 768" % len(data))
    out = bytearray(768)
    for i in range(256):
        b, g, r = data[3 * i:3 * i + 3]
        out[3 * i:3 * i + 3] = bytes((r, g, b))
    return bytes(out)


def load(root, name):
    with open(os.path.join(root, PALETTE_DIR, name, "pal.dat"), "rb") as f:
        return decode_dat(f.read())


def colour_codes(root):
    """colors.txt Code column in row order (row index = colour index stored by the item tables)."""
    path = os.path.join(root, "data", "global", "excel", "colors.txt")
    with open(path, encoding="latin-1") as f:
        lines = f.read().splitlines()
    head = lines[0].split("\t")
    k = head.index("Code")
    return [ln.split("\t")[k] for ln in lines[1:] if ln.strip()]


def item_shift_maps(root, name):
    """items/palette/<name>.dat -> list of 256-byte maps (21 in stock data)."""
    with open(os.path.join(root, ITEM_PALETTE_DIR, name + ".dat"), "rb") as f:
        data = f.read()
    if len(data) == 0 or len(data) % ITEM_MAP_SIZE:
        raise PaletteError("%s.dat is %d bytes, not a multiple of 256" % (name, len(data)))
    return [data[i:i + ITEM_MAP_SIZE] for i in range(0, len(data), ITEM_MAP_SIZE)]


def shift_rgb(rgb, remap):
    """Palette (768 B R,G,B) + one 256-byte map -> palette where index i shows rgb[remap[i]].
    Index 0 keeps its colour: it is the transparent index of our DC6/DCC renders (renderer choice)."""
    out = bytearray(rgb)
    for i in range(1, 256):
        j = remap[i]
        out[3 * i:3 * i + 3] = rgb[3 * j:3 * j + 3]
    return bytes(out)


def parse_shift(root, spec):
    """'<file>:<code-or-index>' (e.g. 'invgreybrown:cred', 'grey:9') -> (file, index, map bytes)."""
    if ":" not in spec:
        raise PaletteError("shift %r is not <file>:<code-or-index>" % spec)
    name, sel = spec.split(":", 1)
    maps = item_shift_maps(root, name)
    if sel.isdigit():
        idx = int(sel)
    else:
        codes = colour_codes(root)
        if sel not in codes:
            raise PaletteError("colour code %r not in colors.txt" % sel)
        idx = codes.index(sel)
    if not 0 <= idx < len(maps):
        raise PaletteError("map %d out of range 0..%d" % (idx, len(maps) - 1))
    return name, idx, maps[idx]


def _hue_name(dr, dg, db):
    """Coarse colour family of the mean target colour of a map's changed entries (luminance removed).
    A data heuristic for the itempal check, not game behaviour."""
    m = (dr + dg + db) / 3.0
    r, g, b = dr - m, dg - m, db - m
    if max(abs(r), abs(g), abs(b)) < 4:
        return "grey"
    if r > 0 and b < 0 and g > -0.25 * r:
        return "yellow"   # yellow, gold, orange: red and green up, blue down
    if r > 0 and b > 0 and g < 0:
        return "purple"
    if r == max(r, g, b):
        return "red"
    if g == max(r, g, b):
        return "green"
    return "blue"


# colours.txt code -> expected family of its map's mean colour (from the code names; a heuristic)
CODE_FAMILY = {"whit": "grey", "lgry": "grey", "dgry": "grey", "blac": "grey", "bwht": "grey",
               "lblu": "blue", "dblu": "blue", "cblu": "blue", "lred": "red", "dred": "red",
               "cred": "red", "lgrn": "green", "dgrn": "green", "cgrn": "green", "lyel": "yellow",
               "dyel": "yellow", "lgld": "yellow", "dgld": "yellow", "lpur": "purple",
               "dpur": "purple", "oran": "yellow"}


def itempal(root, verbose=True):
    """Account for every items/palette/*.dat byte; check the 21 x 256 split against colors.txt."""
    import hashlib
    base = os.path.join(root, ITEM_PALETTE_DIR)
    codes = colour_codes(root)
    units = load(root, "units")
    names = sorted(n[:-4] for n in os.listdir(base) if n.lower().endswith(".dat"))
    files = maps = errors = identity = changed = maps_moved = family_ok = family_bad = 0
    nonid_hi_lo = [0, 0]   # changed entries whose source index is < 32 or >= 160 / elsewhere
    hashes = {}
    for name in names:
        try:
            ms = item_shift_maps(root, name)
        except (OSError, PaletteError) as e:
            errors += 1
            print("FAIL %s: %s" % (name, e))
            continue
        files += 1
        raw = b"".join(ms)
        if verbose:
            per = {w: sum(1 for k in range(len(raw)) if raw[k] == k % w) for w in (128, 192, 224, 256, 384, 768)}
            print("%-13s bytes equal to (offset mod W): %s" % (name, ", ".join(
                "W=%d %.1f%%" % (w, 100.0 * c / len(raw)) for w, c in per.items())))
            nm = len(raw) // 256
            tr = sum(1 for i in range(256) for n in range(nm) if raw[i * nm + n] == i)
            print("%-13s transposed (256 x %d, index-major) identity: %.1f%%" % (name, nm, 100.0 * tr / len(raw)))
        hashes.setdefault(hashlib.sha256(raw).hexdigest(), []).append(name)
        if len(ms) != len(codes):
            errors += 1
            print("FAIL %s: %d maps, colors.txt has %d rows" % (name, len(ms), len(codes)))
        fam_line = []
        for n, m in enumerate(ms):
            maps += 1
            ch = [j for j in range(256) if m[j] != j]
            identity += 256 - len(ch)
            changed += len(ch)
            if ch:
                maps_moved += 1
            for j in ch:
                nonid_hi_lo[0 if (j < 40 or j >= 160) else 1] += 1
            inner = [j for j in ch if 0 < j < 255]
            k = max(1, len(inner))
            d = [sum(units[3 * m[j] + c] for j in inner) / k for c in range(3)]
            fam = _hue_name(*d)
            code = codes[n] if n < len(codes) else "?"
            ok = CODE_FAMILY.get(code) == fam
            family_ok += ok
            family_bad += not ok
            fam_line.append("%s%s" % (code, "" if ok else "!=" + fam))
        if verbose:
            print("%-13s %d B = %d x 256; identity %d/%d entries; families %s" % (
                name, len(raw), len(ms), sum(1 for m in ms for j in range(256) if m[j] == j),
                256 * len(ms), " ".join(fam_line)))
    groups = sorted(sorted(v) for v in hashes.values())
    if verbose:
        print("byte-identical groups: %s" % "; ".join("+".join(g) for g in groups))
        print("changed entries by source index: outside 40..159 %d, inside %d" % tuple(nonid_hi_lo))
    print("SURVEY itempal files=%d maps=%d codes=%d identity=%d changed=%d distinct_files=%d "
          "family_ok=%d family_bad=%d errors=%d" % (files, maps, len(codes), identity, changed,
                                                     len(groups), family_ok, family_bad, errors))
    return 1 if errors else 0


def itemswatch(root, out, palette_name="units"):
    """One PNG per .dat: row n = map n applied to the 256 palette entries (8x8 px swatches)."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import png
    rgb = load(root, palette_name)
    base = os.path.join(root, ITEM_PALETTE_DIR)
    for name in sorted(n[:-4] for n in os.listdir(base) if n.lower().endswith(".dat")):
        ms = [bytes(range(256))] + item_shift_maps(root, name)   # row 0: unshifted reference
        w, h = 256 * 4, len(ms) * 8
        px = bytearray(w * h)
        for row, m in enumerate(ms):
            for y in range(row * 8, row * 8 + 8):
                for x in range(w):
                    px[y * w + x] = m[x // 4]
        png.write_indexed(os.path.join(out, name + ".png"), w, h, px, rgb, transparent=())
    return 0


def palette_for_tiles(rel):
    """Heuristic palette for a DT1/DS1 path relative to data/global/tiles (docs/formats/palette.md)."""
    top = rel.replace("\\", "/").lower().split("/", 1)[0]
    return {"act1": "act1", "act2": "act2", "act3": "act3", "act4": "act4",
            "expansion": "act5"}.get(top, "act1")


def survey(root):
    base = os.path.join(root, PALETTE_DIR)
    bad = 0
    names = sorted(os.listdir(base))
    for name in names:
        try:
            dat = open(os.path.join(base, name, "pal.dat"), "rb").read()
            rgb = decode_dat(dat)
        except (OSError, PaletteError) as e:
            bad += 1
            print("FAIL %s: %s" % (name, e))
            continue
        line = "%-10s pal.dat 768 B, index0 rgb=%s index255 rgb=%s" % (name, rgb[:3].hex(), rgb[765:].hex())
        p = os.path.join(base, name, "pal.pl2")
        if os.path.exists(p):
            q = open(p, "rb").read()
            pre = q[:PL2_PREFIX]
            same = all(pre[4 * i:4 * i + 3] == rgb[3 * i:3 * i + 3] for i in range(256))
            pad = {pre[4 * i + 3] for i in range(256)}
            line += "; pal.pl2 %d B, first 1024 B = R,G,B,pad copy of pal.dat: %s (pad bytes %s)" % (
                len(q), same, sorted(pad))
            if not same or pad != {0}:
                bad += 1
        else:
            line += "; no pal.pl2"
        print(line)
    print("palettes %d, failures %d" % (len(names), bad))
    return 1 if bad else 0


def swatch(root, out):
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import png
    base = os.path.join(root, PALETTE_DIR)
    for name in sorted(os.listdir(base)):
        rgb = load(root, name)
        px = bytearray(256 * 256)
        for y in range(256):
            for x in range(256):
                px[y * 256 + x] = (y // 16) * 16 + x // 16
        png.write_indexed(os.path.join(out, name + ".png"), 256, 256, px, rgb, transparent=())
    return 0


def main(argv):
    if len(argv) >= 2 and argv[0] == "survey":
        return survey(argv[1])
    if len(argv) >= 3 and argv[0] == "swatch":
        return swatch(argv[1], argv[2])
    if len(argv) >= 2 and argv[0] == "itempal":
        return itempal(argv[1])
    if len(argv) >= 3 and argv[0] == "itemswatch":
        p = argv[argv.index("--palette") + 1] if "--palette" in argv else "units"
        return itemswatch(argv[1], argv[2], p)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

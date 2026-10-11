"""Decode Diablo II palettes (pal.dat) and check pal.pl2's leading palette copy.

Usage:
  python3 -I tools/palette.py survey <root>        check every palette/<name>/pal.dat (and pal.pl2 prefix)
  python3 -I tools/palette.py swatch <root> <out>  write one 16x16-swatch PNG per palette into <out>

<root> is a merged data tree (e.g. workspace/merged). Layout in docs/formats/palette.md.
pal.dat is 256 entries of 3 bytes stored B, G, R; load() returns R, G, B (768 bytes) ready for
tools/png.py. Which palette the game uses for an asset is code behaviour and not decided here;
palette_for_tiles() is a documented renderer heuristic. Stdlib only. Read-only except swatch.
"""
import os
import sys

PALETTE_DIR = os.path.join("data", "global", "palette")
PL2_PREFIX = 1024


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
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

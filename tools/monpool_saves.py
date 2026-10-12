"""Build the test characters of run:2026-10-12-mon-pool-p2 (plan 0012 Phase 2) from the sample saves.

Usage:
  python3 -I tools/monpool_saves.py <out-dir>

Writes one directory per character under <out-dir> (never into the saves directory; install them with
`python3 -I tools/saves.py install <tag> <out-dir>/<name>/<file>.d2s`):

  expnm/smpsor.d2s        expansion Sorceress (samples/d2s-owner/smpsor-l50.d2s), Act I waypoints 0,2,6,8 in
                          every difficulty, progression 5 (Normal + Nightmare), difficulty bytes 00 80 00
  exphell/smpsor.d2s      same, progression 10 (all three), difficulty bytes 00 00 80
  exphellmerc/smpsor.d2s  exphell plus a mercenary: seed 12345, hireling id 4 (Rogue Scout, Fire - Hell,
                          class 271), name index 0, experience 500000; an empty mercenary item list
                          ('JM' 00 00) after 'jf'
  cls/smpsor.d2s          exphell made classic: status bit 5 cleared, the expansion trailer
                          ('jf' 'kf' 00) removed, progression 8 (all three in a classic save)
  nec/smpnec.d2s          Necromancer (samples/d2s/smpnec.d2s), Hell waypoints 0,2,6,8, Clay Golem
                          (skill 75, class index 9) at level 1 on the right button, progression 10,
                          difficulty bytes 00 00 80

Header offsets are those of docs/formats/d2s.md (progression 0x025, difficulty 0x0A8, merc 0x0B3..0x0BE,
right mouse skill 0x07C); every file gets its size (0x008) and checksum (0x00C) rewritten. Waypoints are
set with tools/d2s.py setwp. Check the result with `python3 -I tools/d2s.py survey <excel-dir> <files>`.
Stdlib only.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from d2s import checksum, setwp  # noqa: E402

ROOT = os.path.dirname(HERE)
SORC = os.path.join(ROOT, "workspace/samples/d2s-owner/smpsor-l50.d2s")
NEC = os.path.join(ROOT, "workspace/samples/d2s/smpnec.d2s")
TRAILER = b"jfkf\x00"  # expansion trailer of a save with no mercenary and no golem


def finish(b, path):
    struct.pack_into("<I", b, 0x08, len(b))
    struct.pack_into("<I", b, 0x0C, checksum(bytes(b)))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b)
    print("wrote %s (%d bytes)" % (path, len(b)))


def with_wps(src, tmp, diffs):
    cur = src
    for i, d in enumerate(diffs):
        nxt = "%s.%d" % (tmp, i)
        setwp(cur, nxt, d, "0,2,6,8")
        cur = nxt
    b = bytearray(open(cur, "rb").read())
    for i in range(len(diffs)):
        os.remove("%s.%d" % (tmp, i))
    return b


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    out = argv[0]
    os.makedirs(out, exist_ok=True)
    base = with_wps(SORC, os.path.join(out, "tmp-sorc"), ["nightmare", "hell"])
    assert base[-5:] == TRAILER, base[-5:]

    b = bytearray(base)
    b[0x25] = 5
    b[0xA8:0xAB] = b"\x00\x80\x00"
    finish(b, os.path.join(out, "expnm", "smpsor.d2s"))

    hell = bytearray(base)
    hell[0x25] = 10
    hell[0xA8:0xAB] = b"\x00\x00\x80"
    finish(bytearray(hell), os.path.join(out, "exphell", "smpsor.d2s"))

    b = bytearray(hell)
    struct.pack_into("<IHHI", b, 0xB3, 12345, 0, 4, 500000)  # seed, name index, hireling id, experience
    b[-5:] = b"jfJM\x00\x00kf\x00"
    finish(b, os.path.join(out, "exphellmerc", "smpsor.d2s"))

    b = bytearray(hell)
    del b[-5:]
    b[0x24] &= ~0x20
    b[0x25] = 8
    finish(b, os.path.join(out, "cls", "smpsor.d2s"))

    b = with_wps(NEC, os.path.join(out, "tmp-nec"), ["hell"])
    p = b.index(b"if", 0x2FD)
    b[p + 2 + 9] = 1  # Clay Golem
    struct.pack_into("<I", b, 0x7C, 75)
    b[0x25] = 10
    b[0xA8:0xAB] = b"\x00\x00\x80"
    finish(b, os.path.join(out, "nec", "smpnec.d2s"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

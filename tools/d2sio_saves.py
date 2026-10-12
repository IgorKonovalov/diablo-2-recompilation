"""Build the test characters of run:2026-10-12-d2s-io (plan 0013 Phase 2) from the sample saves.

Usage:
  python3 -I tools/d2sio_saves.py <excel-dir> <out-dir>

Writes one directory per case under <out-dir> (never into the saves directory; install them with
`python3 -I tools/saves.py install <tag> <out-dir>/<case>/<file>.d2s`):

  rt/qitsor.d2s       the round-trip save: samples/d2s/qitsor.d2s (expansion Sorceress, level 1, items of
                      qualities 2, 4 and 7) edited by tools/d2s.py: stat 9 `maxmana` = 8000 << 8 (one stat,
                      same 21-bit width), header `unk_2c` (0x02C) = 0x0BADF00D (one header field, a client
                      pass-through), and the `difficulty` bytes (0x0A8) = 00 00 00 so the first load does not
                      take the map-seed reuse branch (bit 7 clear)
  badsum/qitsor.d2s   rt with the stored checksum (0x00C) plus 1
  badsize/qitsor.d2s  rt with the file_size field (0x008) plus 1 and the checksum recomputed over that, so the
                      checksum test passes and only the size test can fail
  drop/seedtest.d2s   the strong Barbarian of run:2026-10-11-tc-drops (clvl 71, War Cry on the right button,
                      progression 5), unchanged: runtime/saves-backup/s5-human/seedtest-played.d2s

Every file is checked with tools/d2s.py (checksum, size) and its sha256 printed. Stdlib only.
"""
import hashlib
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from d2s import checksum, setstat  # noqa: E402

ROOT = os.path.dirname(HERE)
QITSOR = os.path.join(ROOT, "workspace/samples/d2s/qitsor.d2s")
STRONG = os.path.join(ROOT, "workspace/runtime/saves-backup/s5-human/seedtest-played.d2s")


def write(b, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b)
    print("%s  %d bytes  sha256 %s  size field %d  checksum stored %08X computed %08X" % (
        path, len(b), hashlib.sha256(b).hexdigest(), struct.unpack_from("<I", b, 8)[0],
        struct.unpack_from("<I", b, 12)[0], checksum(bytes(b))))


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    excel, out = argv
    os.makedirs(os.path.join(out, "rt"), exist_ok=True)
    tmp = os.path.join(out, "rt", "tmp-stat9.d2s")
    setstat(excel, QITSOR, tmp, 9, 8000 << 8)
    b = bytearray(open(tmp, "rb").read())
    os.remove(tmp)
    struct.pack_into("<I", b, 0x2C, 0x0BADF00D)
    b[0xA8:0xAB] = b"\x00\x00\x00"
    struct.pack_into("<I", b, 0x08, len(b))
    struct.pack_into("<I", b, 0x0C, checksum(bytes(b)))
    write(b, os.path.join(out, "rt", "qitsor.d2s"))

    bad = bytearray(b)
    struct.pack_into("<I", bad, 0x0C, (struct.unpack_from("<I", bad, 0x0C)[0] + 1) & 0xFFFFFFFF)
    write(bad, os.path.join(out, "badsum", "qitsor.d2s"))

    bad = bytearray(b)
    struct.pack_into("<I", bad, 0x08, len(bad) + 1)
    struct.pack_into("<I", bad, 0x0C, checksum(bytes(bad)))
    write(bad, os.path.join(out, "badsize", "qitsor.d2s"))

    os.makedirs(os.path.join(out, "drop"), exist_ok=True)
    shutil.copyfile(STRONG, os.path.join(out, "drop", "seedtest.d2s"))
    write(open(os.path.join(out, "drop", "seedtest.d2s"), "rb").read(), os.path.join(out, "drop", "seedtest.d2s"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

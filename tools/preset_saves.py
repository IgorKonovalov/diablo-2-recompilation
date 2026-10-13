"""Build the test characters of run:2026-10-13-drlg-preset (plan 0016 Phase 2) from the sample saves.

Usage:
  python3 -I tools/preset_saves.py <out-dir>

Writes one directory per character under <out-dir> (never into the saves directory; install them with
`python3 -I tools/saves.py install <tag> <out-dir>/<name>/smpsor.d2s`):

  actN/smpsor.d2s   (N = 1..5) the expansion Sorceress of tools/monpool_saves.py `exphell` (level 50,
                    progression 10: Normal, Nightmare and Hell offered), every waypoint (bits 0..38) in every
                    difficulty, and the three difficulty bytes (0x0A8) set to N - 1 with bit 7 clear, so a
                    game of any difficulty starts in act N and the -seed map seed is kept (docs/formats/d2s.md
                    § difficulty)

Every file gets its size (0x008) and checksum (0x00C) rewritten. Check the result with
`python3 -I tools/d2s.py survey <excel-dir> <files>`. Stdlib only.
"""
import os
import struct
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import monpool_saves  # noqa: E402
from d2s import setwp  # noqa: E402


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    out = argv[0]
    os.makedirs(out, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        if monpool_saves.main([tmp]):
            return 1
        cur = os.path.join(tmp, "exphell", "smpsor.d2s")
        for i, d in enumerate(("normal", "nightmare", "hell")):
            nxt = os.path.join(tmp, "wp%d.d2s" % i)
            setwp(cur, nxt, d, "all")
            cur = nxt
        base = open(cur, "rb").read()
    for act in range(1, 6):
        b = bytearray(base)
        b[0xA8:0xAB] = bytes([act - 1] * 3)
        monpool_saves.finish(b, os.path.join(out, "act%d" % act, "smpsor.d2s"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

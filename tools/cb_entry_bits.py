"""Count the room-tile entries of the activation dumps (CB lines of tools/gdb/collision.py) that carry given flag bits,
split by the dumped room's role (the activating room's own entries, or a near room's) and the array (W, F, S).

Usage:
  python3 -I tools/cb_entry_bits.py [--bits 0x400] <log> [...]

Per log: the CB lines, the entries scanned, and for each (role, array, DRLG room) holding a bit its count and its first
entry (line, index, the logged [x, y, flags, tile, o]). Lane/rbd (the H4a council mismatch: bit 0x400, the client wall
fade's alpha-0 mark, on a neighbour's wall entries). Stdlib only. Read-only.
"""
import base64
import collections
import json
import sys
import zlib


def scan(path, bits):
    cb = entries = 0
    c = collections.Counter()
    first = {}
    with open(path, errors="replace") as fh:
        for ln, line in enumerate(fh, 1):
            if not line.startswith("CB "):
                continue
            cb += 1
            d = json.loads(line[3:])
            z = json.loads(zlib.decompress(base64.b64decode(d["z"])))
            for n, dr, _rect, W, F, S in z["near"]:
                role = "own" if n == d["room"] else "near"
                for kind, arr in (("W", W), ("F", F), ("S", S)):
                    for i, g in enumerate(arr):
                        entries += 1
                        if g[2] & bits:
                            k = (role, kind, "%08x" % dr)
                            c[k] += 1
                            first.setdefault(k, (ln, i, g))
    return cb, entries, c, first


def main(argv):
    bits = 0x400
    if argv[:1] == ["--bits"]:
        bits, argv = int(argv[1], 0), argv[2:]
    if not argv:
        print(__doc__)
        return 2
    tot = collections.Counter()
    for path in argv:
        cb, entries, c, first = scan(path, bits)
        tot["logs"] += 1
        tot["CB"] += cb
        tot["entries"] += entries
        tot["with bits"] += sum(c.values())
        print("%s: %d CB, %d entries, %d with %#x" % (path, cb, entries, sum(c.values()), bits))
        for k, v in sorted(c.items()):
            print("   %s %s room %s: %d, first %s" % (k[0], k[1], k[2], v, first[k]))
    print("total: %d logs, %d CB, %d entries, %d with %#x" % (tot["logs"], tot["CB"], tot["entries"], tot["with bits"], bits))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

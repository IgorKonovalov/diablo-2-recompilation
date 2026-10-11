"""Read Diablo II string tables (.tbl) and resolve string keys to the indices compiled .bin files store.

Usage: python3 -I tools/tbl.py <file.tbl> [...]       print header fields and entry counts per file
       python3 -I tools/tbl.py --key <lng-dir> <key>   resolve one key with the three-table precedence

Layout (docs/formats/tbl.md): 21-byte header (u16 crc, u16 count, u32 hash_size, u8 version,
u32 string_start, u32 max_probes, u32 file_size), u16 index[count] (entry -> hash node), then
hash_size 17-byte nodes (u8 used, u16 entry, u32 hash, u32 key_off, u32 str_off, u16 str_len).
Offsets are from the start of the file.

Key -> compiled index, as observed in the item tables: index = base + entry, with base 0 for
string.tbl, 10000 for patchstring.tbl, 20000 for expansionstring.tbl. A key present in several
tables resolves to patchstring first, then expansionstring, then string. A key found nowhere
(including the empty key) resolves to 5382. Stdlib only. Read-only.
"""
import os
import struct
import sys

TABLES = [("patchstring.tbl", 10000), ("expansionstring.tbl", 20000), ("string.tbl", 0)]
NOT_FOUND = 5382


def read_tbl(path):
    with open(path, "rb") as fh:
        d = fh.read()
    crc, count, hsize = struct.unpack_from("<HHI", d, 0)
    version = d[8]
    sstart, probes, fsize = struct.unpack_from("<III", d, 9)
    index = struct.unpack_from("<%dH" % count, d, 21)
    nodes = 21 + 2 * count
    keys = []
    for e in range(count):
        used, entry, h, ko, so, sl = struct.unpack_from("<BHIIIH", d, nodes + 17 * index[e])
        if not used or entry != e:
            raise ValueError("%s: entry %d points at node %d (used=%d entry=%d)" % (path, e, index[e], used, entry))
        keys.append(d[ko:d.index(b"\0", ko)].decode("latin-1"))
    hdr = dict(crc=crc, count=count, hash_size=hsize, version=version, string_start=sstart,
               max_probes=probes, file_size=fsize, actual_size=len(d))
    return hdr, keys


class Strings:
    def __init__(self, lng_dir):
        self.map = {}
        for name, base in reversed(TABLES):  # lowest precedence first, overwritten by higher
            hdr, keys = read_tbl(os.path.join(lng_dir, name))
            local = {}
            for e, k in enumerate(keys):
                local.setdefault(k, base + e)  # first entry wins inside one file
            self.map.update(local)

    def index(self, key):
        return self.map.get(key, NOT_FOUND) if key else NOT_FOUND


def main(argv):
    if len(argv) == 3 and argv[0] == "--key":
        print(Strings(argv[1]).index(argv[2]))
        return 0
    if not argv:
        print(__doc__)
        return 2
    bad = 0
    for p in argv:
        try:
            hdr, keys = read_tbl(p)
            ok = hdr["file_size"] == hdr["actual_size"]
            bad += not ok
            print("%s\t%s\tkeys=%d\t%s" % (p, "ok" if ok else "SIZE-MISMATCH", len(keys),
                                          " ".join("%s=%d" % kv for kv in hdr.items())))
        except Exception as ex:  # report and keep going over every file
            bad += 1
            print("%s\tFAIL\t%s" % (p, ex))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

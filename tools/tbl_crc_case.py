"""Build the two game directories of the `.tbl` CRC case (run:2026-10-12-d2s-io, plan 0013 Phase 2; data/0003).

Usage:
  python3 -I tools/tbl_crc_case.py <game-dir> <patchstring.tbl> <out-root>

Makes <out-root>/game-tbl-fixed/ and <out-root>/game-tbl-bad/: every entry of <game-dir> symlinked, plus a real
data/local/lng/eng/patchstring.tbl (loose files are read only under -direct, docs/findings/data/0002):
  fixed  one value byte changed (the character before the last NUL of the file, a value byte of the last
         entry's string) and the header crc (+0x00) recomputed: CRC-16/CCITT-FALSE over [string_start, end)
         (tools/tbl.py crc16_ccitt). A crc check passes only if the game computes the same CRC, and the
         new crc differs from the stock file's, so a TBL log line with it proves the loose file was read.
  bad    the same byte change with the stock crc kept: the check must fail.
Prints the stock, fixed and bad crc. Run the game from either with tools/d2run.py --game-dir <dir>
--game-args "-direct". Stdlib only.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from tbl import crc16_ccitt  # noqa: E402


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    game, src, root = argv
    d = bytearray(open(src, "rb").read())
    start, size = struct.unpack_from("<I", d, 0x09)[0], struct.unpack_from("<I", d, 0x11)[0]
    stock = struct.unpack_from("<H", d, 0)[0]
    assert size == len(d) and crc16_ccitt(d[start:]) == stock, "stock file does not check"
    pos = len(d) - 2
    assert d[-1] == 0 and d[pos] != 0, "last value byte"
    d[pos] = ord("#") if d[pos] != ord("#") else ord("%")
    new = crc16_ccitt(d[start:])
    variants = {"fixed": struct.pack("<H", new) + bytes(d[2:]), "bad": bytes(d)}
    for name, data in variants.items():
        out = os.path.join(root, "game-tbl-" + name)
        os.makedirs(os.path.join(out, "data", "local", "lng", "eng"), exist_ok=True)
        for e in os.listdir(game):
            dst = os.path.join(out, e)
            if not os.path.lexists(dst):
                os.symlink(os.path.realpath(os.path.join(game, e)), dst)
        with open(os.path.join(out, "data", "local", "lng", "eng", "patchstring.tbl"), "wb") as f:
            f.write(data)
        print("%s: %s byte 0x%X, crc stored 0x%04X" % (name, out, pos, struct.unpack_from("<H", data, 0)[0]))
    print("stock crc 0x%04X (%d), recomputed after the change 0x%04X (%d)" % (stock, stock, new, new))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

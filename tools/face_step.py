#!/usr/bin/env python3
"""Check the facing step table g_PathFaceStep (0x006EB548) against its rule (plan 0063 Phase 2a, reading 4).

    python3 -I tools/face_step.py <game.exe>

The table has 64 dword entries, indexed by d = (target - current) & 63; `PathFaceDir` (0x00648620) and
`PathSetDir` (0x0064887B) read the low byte of entry d into path +0x66. The rule checked, as signed dwords:

    d = 0 -> 0;  1..8 -> +1;  9..16 -> +4;  17..31 -> +8;  32..47 -> -8;  48..55 -> -4;  56..63 -> -1

Prints each entry that differs from the rule and a summary line. Reads the image only.
"""
import struct
import sys

TABLE = 0x006EB548


def va2off(exe, va):
    pe = struct.unpack_from("<I", exe, 0x3C)[0]
    n = struct.unpack_from("<H", exe, pe + 6)[0]
    o = struct.unpack_from("<H", exe, pe + 20)[0]
    for i in range(n):
        _vs, ra, sz, ptr = struct.unpack_from("<IIII", exe, pe + 24 + o + 40 * i + 8)
        if ra <= va - 0x400000 < ra + sz:
            return ptr + va - 0x400000 - ra
    raise ValueError(hex(va))


def rule(d):
    if d == 0:
        return 0
    if d <= 8:
        return 1
    if d <= 16:
        return 4
    if d <= 31:
        return 8
    if d <= 47:
        return -8
    if d <= 55:
        return -4
    return -1


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    exe = open(argv[1], "rb").read()
    vals = struct.unpack_from("<64i", exe, va2off(exe, TABLE))
    bad = [(d, v, rule(d)) for d, v in enumerate(vals) if v != rule(d)]
    for d, v, r in bad:
        print("MISMATCH d=%d image=%d rule=%d" % (d, v, r))
    print("g_PathFaceStep 0x%08X: 64 entries, %d differ from the rule" % (TABLE, len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

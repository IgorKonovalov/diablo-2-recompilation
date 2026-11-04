"""Parse and check Diablo II expfield.d2 (the "expanding field": a 256 x 256 table of direction bytes).

Usage:
  python3 -I tools/expfield.py check <expfield.d2> [<game.exe>]   parse, every check, the whole-table walk, one SURVEY line
  python3 -I tools/expfield.py walk <expfield.d2> X Y             the cells of the walk from table cell (X, Y) to the centre

Layout in docs/formats/expfield.md (as the loader sub_0066A2B0_FieldLoad reads it, items/0014 sec. 1):
  +0x00 u16  unk       the loader skips it (266 in the shipped file)
  +0x02 u32  rows
  +0x06 u32  columns
  +0x0A u8[rows * columns]  direction bytes, row-major: byte d in 0..7 steps (dx[d], dy[d]); 8 is the centre

The step tables are image data at 0x00749780 (dx) and 0x007497A4 (dy), nine s32 each; with a game.exe argument
the check reads them from the image and compares them with the constants below. check exits 0 iff errors == 0.
Meanings are the findings', not this tool's. Stdlib only. Read-only.
"""
import os
import struct
import sys

HEADER = 10
DX = (0, 1, 1, 1, 0, -1, -1, -1, 0)
DY = (-1, -1, 0, 1, 1, 1, 0, -1, 0)
DX_VA = 0x00749780
DY_VA = 0x007497A4
CENTRE = 8


def parse(data):
    """Return (unk, rows, cols, cells) or raise ValueError. cells is the bytes after the header."""
    if len(data) < HEADER:
        raise ValueError("shorter than the 10-byte header")
    unk, rows, cols = struct.unpack_from("<HII", data, 0)
    if rows * cols != len(data) - HEADER:
        raise ValueError("rows * columns = %d but %d bytes follow the header" % (rows * cols, len(data) - HEADER))
    return unk, rows, cols, data[HEADER:]


def walk(cells, rows, cols, x, y, limit=100000):
    """The cells visited from (x, y) up to and including the centre byte; None if it leaves the table or loops."""
    out = []
    while True:
        if not (0 <= x < cols and 0 <= y < rows):
            return None
        out.append((x, y))
        d = cells[y * cols + x]
        if d == CENTRE:
            return out
        if d > CENTRE or len(out) > limit:
            return None
        x += DX[d]
        y += DY[d]


def va2off(exe, va):
    pe = struct.unpack_from("<I", exe, 0x3C)[0]
    n = struct.unpack_from("<H", exe, pe + 6)[0]
    o = struct.unpack_from("<H", exe, pe + 20)[0]
    for i in range(n):
        _vs, ra, sz, ptr = struct.unpack_from("<IIII", exe, pe + 24 + o + 40 * i + 8)
        if ra <= va - 0x400000 < ra + sz:
            return ptr + va - 0x400000 - ra
    return None


def exe_steps(exe):
    return (struct.unpack_from("<9i", exe, va2off(exe, DX_VA)), struct.unpack_from("<9i", exe, va2off(exe, DY_VA)))


def check(path, exe_path=None):
    data = open(path, "rb").read()
    errors = 0
    unk, rows, cols, cells = parse(data)
    hist = [0] * 256
    for b in cells:
        hist[b] += 1
    print("file %d bytes, header unk %d (0x%04X), rows %d, columns %d, cells %d" % (len(data), unk, unk, rows, cols, len(cells)))
    print("byte histogram: " + " ".join("%d:%d" % (i, n) for i, n in enumerate(hist) if n))
    other = sum(hist[9:])
    if other:
        errors += 1
        print("ERROR %d cells hold a byte above 8" % other)
    centres = [(i % cols, i // cols) for i, b in enumerate(cells) if b == CENTRE]
    print("byte 8 at %s" % centres)
    if len(centres) != 1:
        errors += 1
    bad = longest = steps = detour = 0
    if centres:
        cx, cy = centres[0]
        for y in range(rows):
            for x in range(cols):
                w = walk(cells, rows, cols, x, y)
                if w is None:
                    bad += 1
                    continue
                n = len(w) - 1
                longest = max(longest, n)
                steps += n
                if n != max(abs(x - cx), abs(y - cy)):
                    detour += 1
    print("cells whose walk leaves the table, loops or meets a byte above 8: %d; longest walk %d steps; total %d" % (bad, longest, steps))
    print("walks longer or shorter than the Chebyshev distance to the centre: %d" % detour)
    errors += bad
    steps_ok = -1
    if exe_path:
        dx, dy = exe_steps(open(exe_path, "rb").read())
        steps_ok = int(dx == DX and dy == DY)
        print("step tables in the image: dx %s dy %s, equal to the constants: %s" % (list(dx), list(dy), bool(steps_ok)))
        if not steps_ok:
            errors += 1
    print("SURVEY expfield size=%d unk=%d rows=%d cols=%d centres=%d above8=%d walk_bad=%d longest=%d detour=%d steps_eq=%d errors=%d" % (
        len(data), unk, rows, cols, len(centres), other, bad, longest, detour, steps_ok, errors))
    return errors


def main(argv):
    if len(argv) >= 3 and argv[1] == "check":
        return 1 if check(argv[2], argv[3] if len(argv) > 3 else None) else 0
    if len(argv) == 5 and argv[1] == "walk":
        _u, rows, cols, cells = parse(open(argv[2], "rb").read())
        w = walk(cells, rows, cols, int(argv[3]), int(argv[4]))
        print("leaves the table or loops" if w is None else " ".join("(%d,%d)" % p for p in w))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

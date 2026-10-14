#!/usr/bin/env python3
"""Write an edited copy of one compiled excel table, for a forced-path run (ADR-0010).

    python3 -I tools/excel_edit.py <excel-dir> <table> <out-dir> <record>:<column>=<value> [...]
    python3 -I tools/excel_edit.py <excel-dir> <table> <out-dir> '*:<column>=<value>' [...]   # every record

Reads <excel-dir>/<table>.bin and .txt (the stock pair), changes the named integer cells through the field layout
of tools/excel_layouts.py (the same layout excel_bin.py decodes with), and writes <out-dir>/<table>.bin and
<out-dir>/<table>.txt with exactly those cells changed. Record = the .bin record index (the .txt data row with the
'Expansion' marker rows dropped, as excel_bin.py counts them). Only integer fields (u8/s8/u16/s16/u32/s32) can be
edited; anything else is refused. Prints one line per changed cell, old -> new, and the sha256 of both outputs.
Check the pair afterwards with `python3 -I tools/excel_bin.py diff <out-dir> <table>` (0 mismatches) and against
the stock table with `excel_bin.py bindiff <excel-dir> <table> <out-dir>/<table>.bin` (only the listed cells).

The game reads a loose <table>.bin only under -direct (data/0001, data/0002): put the .bin alone in
<game-copy>/data/global/excel/ and run tools/d2run.py --game-dir <game-copy> --game-args=-direct (no -txt).
Stdlib only. Writes only into <out-dir>.
"""
import hashlib
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin  # noqa: E402

INT = {"u8": "<B", "s8": "<b", "u16": "<H", "s16": "<h", "u32": "<I", "s32": "<i"}


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    excel, table, out = argv[0], argv[1], argv[2]
    lay = excel_bin.get_layout(table)
    fields = {f["col"]: f for f in lay["fields"] if "col" in f}
    bp = excel_bin.find_file(excel, table, ".bin")
    tp = excel_bin.find_file(excel, table, ".txt")
    raw = bytearray(open(bp, "rb").read())
    count = struct.unpack_from("<I", raw, 0)[0]
    size = lay["size"]
    if 4 + count * size != len(raw):
        print("record size mismatch")
        return 1
    lines = open(tp, "rb").read().decode("latin-1").split("\n")
    head = lines[0].rstrip("\r").split("\t")
    data_lines = [i for i, ln in enumerate(lines[1:], 1)
                  if ln.rstrip("\r") != "" and ln.split("\t")[0] != "Expansion"]
    if len(data_lines) != count:
        print(".txt data rows %d, .bin records %d" % (len(data_lines), count))
        return 1
    edits = []
    for spec in argv[3:]:
        lhs, val = spec.split("=", 1)
        rec, col = lhs.split(":", 1)
        f = fields.get(col)
        if f is None or f["type"] not in INT:
            print("column %r: not an integer field of the %s layout" % (col, table))
            return 1
        recs = range(count) if rec == "*" else [int(rec)]
        for r in recs:
            edits.append((r, col, f, int(val)))
    for r, col, f, val in edits:
        o = 4 + r * size + f["off"]
        old = struct.unpack_from(INT[f["type"]], raw, o)[0]
        struct.pack_into(INT[f["type"]], raw, o, val)
        li = data_lines[r]
        cells = lines[li].rstrip("\r").split("\t")
        cells += [""] * (len(head) - len(cells))
        ci = head.index(col)
        oldt = cells[ci]
        cells[ci] = str(val)
        cr = "\r" if lines[li].endswith("\r") else ""
        lines[li] = "\t".join(cells) + cr
        print("record %d %-12s bin %d -> %d   txt %r -> %r" % (r, col, old, val, oldt, str(val)))
    os.makedirs(out, exist_ok=True)
    ob = os.path.join(out, os.path.basename(bp))
    ot = os.path.join(out, os.path.basename(tp))
    open(ob, "wb").write(bytes(raw))
    open(ot, "wb").write("\n".join(lines).encode("latin-1"))
    for p in (ob, ot):
        print("wrote %s sha256 %s" % (p, hashlib.sha256(open(p, "rb").read()).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

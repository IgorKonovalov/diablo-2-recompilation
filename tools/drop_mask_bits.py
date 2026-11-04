"""Per-bit controls for items/0014's masks, scored on the kept outputs of family `drop` (run:2026-11-04-ground-emu); no re-run.

Each control takes one bit out of a mask, or adds one bit no mask holds, and counts the cases of 4 000 whose predicted room or
cell then differs from the kept `.out`. A control at 0 means the run does not decide that bit.
Usage: python3 -I tools/drop_mask_bits.py <dir holding drop.out and drop.meta>
"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import item_emu3 as e
import item_inventory as inv


def main():
    d = sys.argv[1]
    FB = e.field_bytes()
    ms = json.load(open(os.path.join(d, "drop.meta")))
    cases, _ = e.parse_out(os.path.join(d, "drop.out"))
    cell0, line0 = inv.DROP_MASK_CELL, inv.DROP_MASK_LINE

    def fails():
        n = 0
        for m, r in zip(ms, cases):
            ra, x, y = e.predict_drop(m, FB)
            if e.field(r["c"], "eax") != ra or struct.unpack("<II", r["d"][0][1]) != (x, y):
                n += 1
        return n
    print("stock cell %04x line %04x fails %d of %d" % (cell0, line0, fails(), len(ms)))
    for name, base in (("cell", cell0), ("line", line0)):
        for b in range(16):
            bit = 1 << b
            v = base ^ bit
            inv.DROP_MASK_CELL, inv.DROP_MASK_LINE = (v, line0) if name == "cell" else (cell0, v)
            print("%s %s bit %04x fails %d" % (name, "without" if base & bit else "with", bit, fails()))
    inv.DROP_MASK_CELL, inv.DROP_MASK_LINE = cell0, line0


if __name__ == "__main__":
    main()

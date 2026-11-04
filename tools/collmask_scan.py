#!/usr/bin/env python3
"""Immediate values that reach a path record's move-mask field, and which of them hold bit 0x8000.

    python3 -I tools/collmask_scan.py <image> [--symbols re/symbols.csv]

Two forms, both from the objdump listing of the image (read only):
  (a) a direct `call 0x00648CE0` (sub_00648CE0_PathSetCollMask) with an immediate `push` among the 4 instructions before it;
  (b) a store of an immediate into a record field at `+0x50`: `mov DWORD PTR [reg+0x50],imm`.
Each hit prints the site, the enclosing function (nearest symbol row at or below) and the value; the last lines count the
hits whose value has bit 0x8000. Bounds: direct calls and direct stores of immediates only; a mask computed in a register,
read from a table or pushed from a variable is not seen; `+0x50` is also a field of other records, so (b) over-approximates.
"""
import argparse
import bisect
import csv
import re
import subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--symbols", default="re/symbols.csv")
    a = ap.parse_args()
    syms = sorted((int(r["address"], 16), r["name"]) for r in csv.DictReader(open(a.symbols)) if r["kind"] == "func")
    keys = [s[0] for s in syms]
    out = subprocess.run(["objdump", "-d", "-M", "intel", a.image], capture_output=True, text=True, check=True).stdout
    ins = []
    for line in out.splitlines():
        p = line.split("\t")
        if len(p) >= 3:
            try:
                ins.append((int(p[0].strip(" :"), 16), p[2].strip()))
            except ValueError:
                pass

    def fn(addr):
        k = bisect.bisect_right(keys, addr) - 1
        return "%s+0x%x" % (syms[k][1], addr - syms[k][0])

    hits = []
    for i, (addr, t) in enumerate(ins):
        if t == "call   0x648ce0":
            for j in range(i - 1, max(i - 5, 0) - 1, -1):
                m = re.match(r"push   (0x[0-9a-f]+)$", ins[j][1])
                if m:
                    hits.append(("call", addr, int(m.group(1), 16)))
                    break
        m = re.match(r"mov    DWORD PTR \[[a-z]{3}(?:\+[a-z]{3}\*\d)?\+0x50\],(0x[0-9a-f]+)$", t)
        if m:
            hits.append(("store", addr, int(m.group(1), 16)))
    for kind, addr, v in hits:
        print("%-5s 0x%08X  0x%04X  %s%s" % (kind, addr, v, fn(addr), "   BIT 0x8000" if v & 0x8000 else ""))
    print("# %d hits (%d calls, %d stores); %d with bit 0x8000" % (
        len(hits), sum(h[0] == "call" for h in hits), sum(h[0] == "store" for h in hits), sum(bool(h[2] & 0x8000) for h in hits)))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Direct call sites of a flag-test getter, with the index loaded into EDX just before each call.

    python3 -I tools/flagtest_sites.py <image> [--callee 0x4638a0] [--window 8] [--symbols re/symbols.csv]

Default callee is sub_004638A0_MonStats2FlagTest(ECX = class, EDX = bit index): it reads byte
`+4 + (EDX >> 3)` of the MonStats2 row (stride 0x134) and masks bit `EDX & 7`, so index 0x13 is
`+0x006` bit 3 (deadCol) and 0x14 is `+0x006` bit 4 (unflatDead).

For each direct `call callee` it prints the site, the enclosing function (the nearest row of the symbols
file at or below the site; a function without a row shows as the previous row's name plus the distance)
and the index, found as the last `mov edx, imm` or `xor edx, edx` among the `window` instructions before
the call with no other write to EDX after it. A site whose index is not an immediate in the window prints
`?` with the preceding instructions that touch edx. Bounds: direct calls only; an indirect call or a
call through a pointer table is not seen; a label between the load and the call is not followed.
Read-only (objdump on the image).
"""
import argparse
import bisect
import csv
import re
import subprocess


def instructions(image):
    out = subprocess.run(["objdump", "-d", "-M", "intel", image], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            try:
                yield int(parts[0].strip(" :"), 16), parts[2].strip()
            except ValueError:
                pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--callee", default="0x4638a0")
    ap.add_argument("--window", type=int, default=8)
    ap.add_argument("--symbols", default="re/symbols.csv")
    a = ap.parse_args()
    callee = int(a.callee, 16)
    syms = []
    with open(a.symbols) as f:
        for r in csv.DictReader(f):
            if r["kind"] == "func":
                syms.append((int(r["address"], 16), r["name"]))
    syms.sort()
    keys = [s[0] for s in syms]
    ins = list(instructions(a.image))
    want = "call   0x%x" % callee
    n = 0
    for i, (addr, text) in enumerate(ins):
        if text != want:
            continue
        n += 1
        idx = "?"
        touch = []
        for j in range(i - 1, max(i - a.window, 0) - 1, -1):
            t = ins[j][1]
            m = re.match(r"mov\s+edx,(0x[0-9a-f]+|\d+)$", t)
            if m:
                idx = hex(int(m.group(1), 0))
                break
            if t.startswith("xor    edx,edx"):
                idx = "0x0"
                break
            if re.search(r"\bedx\b|\bdl\b|\bdx\b", t.split(",")[0]) and not t.startswith(("push", "cmp", "test")):
                touch.append("%x %s" % (ins[j][0], t))
                break
        k = bisect.bisect_right(keys, addr) - 1
        fn = "%s+0x%x" % (syms[k][1], addr - syms[k][0]) if k >= 0 else "?"
        print("0x%08X  idx=%-5s %s%s" % (addr, idx, fn, ("   [" + "; ".join(touch) + "]") if idx == "?" else ""))
    print("# %d direct calls of 0x%08X" % (n, callee))


if __name__ == "__main__":
    main()

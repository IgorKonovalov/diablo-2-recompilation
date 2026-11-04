#!/usr/bin/env python3
"""Direct call sites of one function, with the immediates pushed just before each call.

    python3 -I tools/call_arg_sites.py <image> <callee-hex> [--imm 0x4c,0x4d] [--window 3]

Disassembles the pinned image with objdump (read only) and prints one line per direct call:
the site, and the `push imm` found among the `window` instructions before it. With --imm,
only the sites with one of those immediates. Bounds of a line or of its absence: a direct
`call` with an immediate pushed in the window; an indirect call or a register argument is
not seen.
"""
import argparse
import re
import subprocess


def instructions(image):
    out = subprocess.run(["objdump", "-d", "-M", "intel", image], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            yield int(parts[0].strip(" :"), 16), parts[2].strip()


def sites(image, callee, window=3):
    ins = list(instructions(image))
    want = "call   0x%x" % callee
    for i, (addr, text) in enumerate(ins):
        if text == want:
            imms = []
            for _, prev in ins[max(0, i - window):i]:
                m = re.fullmatch(r"push +(0x[0-9a-f]+)", prev)
                if m:
                    imms.append(int(m.group(1), 16))
            yield addr, imms


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image")
    ap.add_argument("callee", type=lambda s: int(s, 16))
    ap.add_argument("--imm", default="")
    ap.add_argument("--window", type=int, default=3)
    a = ap.parse_args()
    wanted = {int(x, 16) for x in a.imm.split(",") if x}
    n = 0
    for addr, imms in sites(a.image, a.callee, a.window):
        if wanted and not wanted & set(imms):
            continue
        n += 1
        print("0x%08X %s" % (addr, " ".join("0x%X" % x for x in imms)))
    print("total %d" % n)


if __name__ == "__main__":
    main()

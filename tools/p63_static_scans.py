#!/usr/bin/env python3
"""Raw instruction scans behind plan 0063 Phase 2a's static readings (lane n63r).

    python3 -I tools/p63_static_scans.py <game.exe> bit26     # unit +0xC4 bit 26: every `or [r+0xC4],0x4000000`,
                                                             # every `shr r,0x1A` within 3 instructions of a load
                                                             # of [r+0xC4], every `and [r+0xC4],0xFBFFFFFF`
    python3 -I tools/p63_static_scans.py <game.exe> facing    # every byte/word store and byte read at [r+0x64],
                                                             # [r+0x65], [r+0x66]

Disassembles the pinned image with objdump (read only). Bounds: a direct register-based operand only; a store
through another addressing form, or a test of bit 26 by another instruction shape, is not seen. Each line is the
instruction's address and text; a summary line ends each list.
"""
import re
import subprocess
import sys


def instructions(image):
    out = subprocess.run(["objdump", "-d", "-M", "intel", image], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            yield int(parts[0].strip(" :"), 16), parts[2].strip()


def bit26(ins):
    sets = [(a, t) for a, t in ins if re.search(r"\[e[a-z]{2}\+0xc4\],0x4000000$", t) and t.startswith("or ")]
    clears = [(a, t) for a, t in ins if re.search(r"\[e[a-z]{2}\+0xc4\],0xfbffffff$", t)]
    reads = []
    for i, (a, t) in enumerate(ins):
        if re.match(r"shr\s+e[a-z]{2},0x1a$", t) and any("+0xc4]" in x[1] for x in ins[max(0, i - 3):i]):
            reads.append((a, t))
    for name, rows in (("set", sets), ("clear", clears), ("read", reads)):
        for a, t in rows:
            print("%s 0x%08X %s" % (name, a, t))
        print("summary %s=%d" % (name, len(rows)))


def facing(ins):
    for off in ("0x64", "0x65", "0x66"):
        st = re.compile(r"^(mov|add|sub|or|and|xor|inc|dec)\s+(BYTE|WORD) PTR \[e[a-z]{2}\+%s\]," % off)
        rd = re.compile(r"BYTE PTR \[e[a-z]{2}\+%s\]" % off)
        stores = [(a, t) for a, t in ins if st.match(t)]
        reads = [(a, t) for a, t in ins if rd.search(t) and not st.match(t)]
        for a, t in stores:
            print("store +%s 0x%08X %s" % (off, a, t))
        for a, t in reads:
            print("read  +%s 0x%08X %s" % (off, a, t))
        print("summary +%s stores=%d reads=%d" % (off, len(stores), len(reads)))


def main(argv):
    if len(argv) < 3 or argv[2] not in ("bit26", "facing"):
        print(__doc__)
        return 2
    ins = list(instructions(argv[1]))
    (bit26 if argv[2] == "bit26" else facing)(ins)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

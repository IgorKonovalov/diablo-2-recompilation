#!/usr/bin/env python3
"""Raw byte scan for references to an address in the pinned Game.exe, independent of Ghidra's analysis.

    python3 -I tools/xrefscan.py <0xADDR> [<0xADDR> ...] [--exe workspace/install/app/game.exe]

For each target address it lists, from the bytes alone (no disassembler, no analysis database):
  - rel32 branches: every offset in an executable section where E8 (call), E9 (jmp) or 0F 80..8F (jcc) is followed by
    a rel32 whose destination is the target;
  - absolute: every 4-byte little-endian occurrence of the target's VA in any section (push imm32, mov imm32,
    pointer tables, relocations-backed data).
A byte pattern can match by accident inside another instruction, so the scan over-approximates: every hit is printed
with the bytes around it, and a reader decides which hits are instructions (a hit Ghidra also lists is one). It
under-approximates only an address computed at run time (base + offset), which neither tool sees.

Plan 0038 batch S2a uses it as the second tool next to `tools/ghidra.sh xrefs` for the caller claims of items/0001 and
items/0002. Stdlib only. Read-only.
"""
import argparse
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pe_info  # noqa: E402

EXE = os.path.join(os.path.dirname(HERE), "workspace", "install", "app", "game.exe")
IMAGE_SCN_MEM_EXECUTE = 0x20000000


def sections(path):
    p = pe_info.parse(path)
    return p["image_base"], p["sections"]


def scan(data, base, secs, target):
    """[(kind, va, hexbytes)] for one target VA."""
    hits = []
    tb = struct.pack("<I", target)
    for s in secs:
        raw, rsize, va = s["raw"], min(s["rsize"], s["vsize"]), s["va"]
        blob = data[raw:raw + rsize]
        if s["flags"] & IMAGE_SCN_MEM_EXECUTE:
            for i in range(len(blob) - 4):
                op = blob[i]
                if op in (0xE8, 0xE9):
                    n, kind = 5, "call" if op == 0xE8 else "jmp"
                    rel = struct.unpack_from("<i", blob, i + 1)[0]
                elif op == 0x0F and i + 6 <= len(blob) and 0x80 <= blob[i + 1] <= 0x8F:
                    n, kind = 6, "jcc"
                    rel = struct.unpack_from("<i", blob, i + 2)[0]
                else:
                    continue
                at = base + va + i
                if (at + n + rel) & 0xFFFFFFFF == target:
                    hits.append((kind, at, blob[max(0, i - 3):i + n + 2].hex()))
        k = blob.find(tb)
        while k >= 0:
            hits.append(("abs32 in %s" % s["name"], base + va + k, blob[max(0, k - 3):k + 6].hex()))
            k = blob.find(tb, k + 1)
    return hits


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--exe", default=EXE)
    ns = ap.parse_args(argv)
    data = open(ns.exe, "rb").read()
    base, secs = sections(ns.exe)
    for t in ns.targets:
        target = int(t, 16)
        hits = scan(data, base, secs, target)
        print("# 0x%08X: %d hit(s)" % (target, len(hits)))
        for kind, at, hx in hits:
            print("  %-16s 0x%08X  %s" % (kind, at, hx))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

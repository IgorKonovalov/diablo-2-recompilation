#!/usr/bin/env python3
"""Plan 0052 Phase 2 (second run): the return sites tools/gdb/ai.py arms to log the result of a boundary call.

    python3 -I tools/ai_retsites.py write [EXE]     # regenerate tools/gdb/ai-retsites.txt from the pinned game.exe
    python3 -I tools/ai_retsites.py check [EXE]     # the file equals a regeneration (exit 1 if not)

The logger puts a breakpoint at the instruction after each call (the return address) of the AI think code to one of the
136 boundary functions (the `BND` tuple of tools/gdb/ai.py). A breakpoint inside an instruction would corrupt it, so the
call sites come from objdump (Intel syntax) swept three times over each window, from the window start and from offsets 7 and
13 bytes on, and only the instruction starts all three sweeps agree on are used. The text file starts with comment lines
and holds one hex return address per line. Stdlib and objdump only.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "gdb", "ai-retsites.txt")
EXE = os.path.join(ROOT, "workspace", "runtime", "game", "game.exe")
WINDOWS = ((0x005B14E0, 0x005B1650), (0x005E0000, 0x00600000), (0x0058F0D0, 0x0058F130), (0x005DE830, 0x005DE8C0),
           (0x005DF850, 0x005DFC00))
HEAD = ("# return addresses (call site + 5) of the calls from the AI think windows (0x005B14E0..0x005B1650, 0x005E0000..0x005FFFFF,\n"
        "# 0x0058F0D0..0x0058F130, 0x005DE830..0x005DE8C0, 0x005DF850..0x005DFC00) to the 136 boundary functions of tools/gdb/ai.py (BND).\n"
        "# tools/ai_retsites.py regenerates it from the pinned game.exe by three objdump sweeps started at different offsets and keeps\n"
        "# the instruction starts all three agree on. One hex address per line.\n")


def bnd():
    src = open(os.path.join(HERE, "gdb", "ai.py")).read()
    m = re.search(r"BND = \((.*?)\n    \)", src, re.S)
    return set(int(x, 16) for x in re.findall(r"0x[0-9A-F]{8}", m.group(1)))


def sweep(exe, lo, hi):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--start-address=0x%x" % lo, "--stop-address=0x%x" % hi, exe],
                         capture_output=True, text=True, check=True).stdout
    ins = {}
    for ln in out.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\t([0-9a-f ]+)\t(.*)", ln)
        if m:
            ins[int(m.group(1), 16)] = (len(m.group(2).split()), m.group(3))
    return ins


def sites(exe=EXE):
    b = bnd()
    res = set()
    for lo, hi in WINDOWS:
        a, b2, c = sweep(exe, lo, hi), sweep(exe, lo + 7, hi), sweep(exe, lo + 13, hi)
        for ad in set(a) & set(b2) & set(c):
            n, t = a[ad]
            m = re.match(r"call\s+0x([0-9a-f]+)$", t.strip())
            if m and int(m.group(1), 16) in b:
                res.add(ad + n)
    return sorted(res)


def text(exe=EXE):
    return HEAD + "".join("%08x\n" % s for s in sites(exe))


def main(argv):
    if not argv or argv[0] not in ("write", "check"):
        print(__doc__)
        return 2
    exe = argv[1] if len(argv) > 1 else EXE
    t = text(exe)
    if argv[0] == "write":
        open(OUT, "w").write(t)
        print("%d sites -> %s" % (t.count("\n") - 4, OUT))
        return 0
    same = open(OUT).read() == t
    print("ai-retsites.txt %s a regeneration (%d sites)" % ("equals" if same else "DIFFERS from", t.count("\n") - 4))
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

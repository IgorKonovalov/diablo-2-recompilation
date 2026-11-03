#!/usr/bin/env python3
"""No-case-dependence test of the emulator scripts' per-case memory spec (plan 0055, lane/r55e).

EmuTrace.java, EmuBoundary.java and EmuCall.java re-write every non-`const` directive before each case. Before the
lane/r55e fix a directive that starts on a 4 KiB boundary and is 0x1000 bytes or more kept the previous case's
stores (Ghidra's MemoryPageBank.setPage keeps the caller's array as the page; frame/0003 Dead ends). This test puts
an RNG seed inside such a directive and calls RNG_Range (0x0045C390, a __fastcall that steps the seed it is given)
three times with the same inputs, plus a case `w` write in the first case only. With the spec re-applied, the three
cases return the same value and seed, the model's (tools/rng.py), and the `w` bytes are gone from cases 2 and 3.

Usage:
  python3 -I tools/emu_zerotest.py write <dir>              # specs, cases and load files (deterministic, no RNG)
  python3 -I tools/emu_zerotest.py runs <dir> <suffix>...   # print the -postScript argument list for analyzeHeadless
  python3 -I tools/emu_zerotest.py check <dir> <suffix>...  # one ZT line per script and spec; exit 1 on a failure
A <suffix> is '' (the scripts as they are) or a renamed copy's class suffix (e.g. 'Old' for EmuTraceOld.java, the
pre-fix control). The control is expected to fail exactly the aligned specs of 0x1000 bytes or more.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rng  # noqa: E402

FN = 0x0045C390  # RNG_Range
N = 0x10000
SEED = (0x12345678, 0x9ABCDEF0)
SEED_OFF, W_OFF = 0x78, 0x100
# name, directive kind, start, length; trace specs run under EmuTrace and EmuBoundary, call specs under EmuCall
TRACE = [("b800", "bytes", 0x10300000, 0x800), ("bFFF", "bytes", 0x10300000, 0xFFF),
         ("b1000", "bytes", 0x10300000, 0x1000), ("b1800", "bytes", 0x10300000, 0x1800),
         ("b2000u", "bytes", 0x10300800, 0x2000), ("l1000", "load", 0x10300000, 0x1000),
         ("l46230", "load", 0x7F800000, 0x46230)]
CALL = [("l800", "load", 0x10300000, 0x800), ("l1000", "load", 0x10300000, 0x1000),
        ("l1800", "load", 0x10300000, 0x1800), ("l2000u", "load", 0x10300800, 0x2000),
        ("l46230", "load", 0x7F800000, 0x46230)]
SCRIPTS = [("EmuTrace", TRACE), ("EmuBoundary", TRACE), ("EmuCall", CALL)]


def blob(n):
    b = bytearray(n)
    b[SEED_OFF:SEED_OFF + 8] = struct.pack("<II", *SEED)
    return bytes(b)


def aligned_long(start, n):
    return start % 0x1000 == 0 and n >= 0x1000


def write(d):
    for sub in ("trace", "call", "out"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    for sub, specs in (("trace", TRACE), ("call", CALL)):
        for name, kind, start, n in specs:
            p = os.path.join(d, sub, name)
            if kind == "load":
                with open(p + ".bin", "wb") as f:
                    f.write(blob(n))
                line = f"load {start:08x} {os.path.abspath(p)}.bin\n"
            else:
                line = f"bytes {start:08x} {blob(n).hex()}\n"
            with open(p + ".mem", "w") as f:
                f.write(f"# emu_zerotest {name}: {kind} 0x{n:x} bytes at 0x{start:08x}, seed at +0x{SEED_OFF:x}\n" + line)
            a, w = start + SEED_OFF, start + W_OFF
            with open(p + ".cases", "w") as f:
                if sub == "trace":
                    for i in range(3):
                        if i == 0:
                            f.write(f"w {w:08x} 05000000\n")
                        f.write(f"d {a:08x} 8\nd {w:08x} 4\ncall {FN:08x} {a:08x} {N:08x}\n")
                else:
                    f.write(f"{a:08x} {N:08x}\n" * 3)


def runs(d, suffixes):
    out = []
    for suf in suffixes:
        for script, specs in SCRIPTS:
            sub = "call" if script == "EmuCall" else "trace"
            for name, *_ in specs:
                p = os.path.join(d, sub, name)
                o = os.path.join(d, "out", f"{script}{suf}-{name}.out")
                if script == "EmuCall":
                    out += ["-postScript", f"{script}{suf}.java", o, f"0x{FN:08X}", p + ".cases", p + ".mem"]
                else:
                    out += ["-postScript", f"{script}{suf}.java", o, p + ".cases", p + ".mem"]
    print(" ".join(out))


def check(d, suffixes):
    eax, low, high = rng.rng_range(SEED[0], SEED[1], N)
    want_seed = struct.pack("<II", low, high).hex()
    bad = 0
    for suf in suffixes:
        for script, specs in SCRIPTS:
            for name, kind, start, n in specs:
                o = os.path.join(d, "out", f"{script}{suf}-{name}.out")
                lines = open(o).read().split("\n")
                got = []
                if script == "EmuCall":
                    rets = [l.split() for l in lines if l.strip()]
                    for r in rets:
                        got.append((int(r[0], 16), None, None))
                else:
                    cur = None
                    for l in lines:
                        f = l.split()
                        if not f:
                            continue
                        if f[0] == "C":
                            cur = [int(f[3].split("=")[1], 16), None, None]
                            got.append(cur)
                        elif f[0] == "D" and cur is not None:
                            if int(f[1], 16) == start + SEED_OFF:
                                cur[1] = f[2]
                            else:
                                cur[2] = f[2]
                ok = len(got) == 3
                for i, (e, s, w) in enumerate(got):
                    ok &= e == eax
                    if script != "EmuCall":
                        ok &= s == want_seed and w == ("05000000" if i == 0 else "00000000")
                expect = not (suf and aligned_long(start, n))
                vals = " ".join(f"{e:08x}" for e, _, _ in got)
                print(f"ZT {script}{suf} {name} {kind} start={start:08x} len={n:x} aligned_long={int(aligned_long(start, n))}"
                      f" pass={int(ok)} expected={int(expect)} eax={vals} model={eax:08x}")
                bad += ok != expect
    print(f"ZT summary outcomes_unexpected={bad}")
    return 1 if bad else 0


def main(argv):
    if len(argv) >= 2 and argv[0] == "write":
        write(argv[1])
    elif len(argv) >= 2 and argv[0] == "runs":
        runs(argv[1], argv[2:] or [""])
    elif len(argv) >= 2 and argv[0] == "check":
        return check(argv[1], argv[2:] or [""])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

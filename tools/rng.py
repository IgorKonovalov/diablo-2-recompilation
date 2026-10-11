"""Reference reimplementation of the Game.exe RNG primitives, and a checker against emulator output.

Usage:
  python3 -I tools/rng.py cases <out.txt> [count] [py-seed]
  python3 -I tools/rng.py check <kind> <cases.txt> <emu-out.txt>

The seed is two u32 words {low, high} (struct offset +0 and +4). Primitives, each modelled on one
function in the pinned Game.exe (docs/findings/rng/0001-rng-core.md):
  step      seed = low * 0x6AC690C5 + high (64-bit), low = bits 0..31, high = bits 32..63
  range     if (int32)n < 1: return 0 and leave the seed untouched; else step, return low % n
            (the binary uses low & (n-1) when n is a power of two, which is the same value)
  pow2      step, return low & (n-1)  (no guard; callers pass a power of two)
  init      low = value, high = 666
  init1     low = 1, high = 666

`cases` writes test vectors, one "low high edx" line each (hex u32), with every edge case first
(0, 1, all-ones, carry-out, n <= 0, n = 1, powers of two, n = 0x7FFFFFFF) and then pseudo-random lines.
`check` reads the "eax low high" lines that re/ghidra_scripts/EmuFastcall.java writes when it runs the
binary's own function on the same cases, and compares them line by line with this module. Exit 0 only if every line matches.
Stdlib only.
"""
import random
import sys

MASK = 0xFFFFFFFF
MULT = 0x6AC690C5
INIT_HIGH = 666


def step(low, high):
    v = low * MULT + high
    return v & MASK, (v >> 32) & MASK


def rng_range(low, high, n):
    """Returns (result, low, high)."""
    if n & 0x80000000 or n == 0:  # (int32)n < 1
        return 0, low, high
    low, high = step(low, high)
    return low % n, low, high


def rng_pow2(low, high, n):
    low, high = step(low, high)
    return low & ((n - 1) & MASK), low, high


def primitive(kind, low, high, edx):
    """Model of one emulated call: returns the (eax, low, high) the binary should produce.
    eax is None where the binary's return value is not meaningful (void functions)."""
    if kind == "step":
        return (None,) + step(low, high)
    if kind == "range":
        return rng_range(low, high, edx)
    if kind == "pow2":
        return rng_pow2(low, high, edx)
    if kind == "init":
        return None, edx, INIT_HIGH
    if kind == "init1":
        return None, 1, INIT_HIGH
    raise SystemExit(f"unknown kind {kind}")


def cases(path, count=5000, pyseed=1):
    rnd = random.Random(pyseed)
    seeds = [(0, 0), (1, 666), (MASK, MASK), (MASK, 0), (0, MASK), (0x80000000, 0x80000000), (0x12345678, 0x29A)]
    ns = [0, 1, 2, 3, 4, 7, 8, 10, 100, 0x10000, 0x7FFFFFFF, 0x80000000, MASK, 0xFFFFFFFE, 0x80000001, 0x40000000]
    lines = [(lo, hi, n) for lo, hi in seeds for n in ns]
    while len(lines) < count:
        r = rnd.random()
        n = rnd.randrange(1, 0x101) if r < 0.4 else (1 << rnd.randrange(0, 32)) if r < 0.6 else rnd.getrandbits(32)
        lines.append((rnd.getrandbits(32), rnd.getrandbits(32), n))
    with open(path, "w") as fh:
        for lo, hi, n in lines:
            fh.write(f"{lo:08x} {hi:08x} {n:08x}\n")
    print(f"{len(lines)} cases -> {path}")


def check(kind, cases_path, emu_path):
    with open(cases_path) as fh:
        inputs = [tuple(int(x, 16) for x in ln.split()) for ln in fh if ln.strip()]
    with open(emu_path) as fh:
        outputs = [tuple(int(x, 16) for x in ln.split()) for ln in fh if ln.strip()]
    if len(inputs) != len(outputs):
        raise SystemExit(f"{len(inputs)} cases but {len(outputs)} emulator lines")
    bad = 0
    for i, ((lo, hi, edx), (eax, elo, ehi)) in enumerate(zip(inputs, outputs)):
        want = primitive(kind, lo, hi, edx)
        got = (eax if want[0] is not None else None, elo, ehi)
        if got != want:
            bad += 1
            if bad <= 10:
                print(f"MISMATCH line {i + 1}: in {lo:08x} {hi:08x} {edx:08x} want {want} got {got}")
    print(f"{kind}: {len(inputs) - bad}/{len(inputs)} match")
    return 0 if bad == 0 else 1


def main(argv):
    if len(argv) >= 2 and argv[0] == "cases":
        cases(argv[1], *(int(x) for x in argv[2:4]))
        return 0
    if len(argv) == 4 and argv[0] == "check":
        return check(*argv[1:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

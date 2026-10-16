#!/usr/bin/env python3
"""Models of the calc-formula functions min, max and rand, checked against the binary run through Ghidra's emulator.

    python3 -I tools/calc_funcs.py cases <out.txt> [count] [py-seed]
    python3 -I tools/calc_funcs.py check <fn> <cases.txt> <emu-out.txt>
    python3 -I tools/calc_funcs.py fns
    python3 -I tools/calc_funcs.py misscases <dir> [count] [py-seed]
    python3 -I tools/calc_funcs.py misscheck <dir> <emu-out.txt>
    python3 -I tools/calc_funcs.py evalcases <excel-dir> <dir>
    python3 -I tools/calc_funcs.py evalcheck <excel-dir> <dir> <emu-out.txt>

docs/findings/data/0005-calc.md § 6. Each function is called by CALC_Eval as __fastcall(ECX = a, EDX = b), stack c, ctx
(re/ghidra_scripts/EmuCalcFunc.java). <fn> is one of the names `fns` lists, each the entry of a function table:

  skills_min  0x006436E0  items_min  0x00627B50  miss_min  0x0064B700   a < b ? a : b (signed)
  skills_max  0x006436F0  items_max  0x00627B60  miss_max  0x0064B710   a > b ? a : b (signed)
  skills_rand 0x00643700  items_rand 0x00627B70                          ctx NULL -> 0; a >= b (signed) -> a;
                                                                         else a + RNG_RangeB(&ctx->unit->seed (+0x20), b - a + 1)
  miss_rand   0x0064B720                                                 the same on the seed at ctx + 0x20

RNG_RangeB (fn:RNG_RangeB@0x0045C3E0) is tools/rng.py's range: (int32)n < 1 -> 0, no step; else one step, low % n.
b - a + 1 and a + r wrap at 32 bits.

`cases` writes "a b c ctx low high" lines (hex u32): edge cases first (equal, adjacent, INT32_MIN/MAX, a range that
wraps to n <= 0, NULL ctx), then pseudo-random lines. `check` compares the emulator's "eax ulow uhigh clow chigh"
lines with the model; only the seed the function may touch is compared, the other copy must be unchanged. Exit 0
only if every line matches.

`misscases` / `misscheck`: fn:MISS_CalcVar@0x0064B340 (__stdcall(missile, owner, code, missileId, lvl), pops 0x14)
through re/ghidra_scripts/EmuCall.java, on a synthetic missiles table: `misscases` writes into <dir> `miss-recs.bin`
(N records of 0x1A4 random bytes), `miss-mem.txt` (the memory spec: g_pDataTables 0x00744304 -> a scratch DataTables
with +0xB64 the records and +0xB6C the count N; a type-3 and a type-1 unit) and `miss-cases.txt`, covering the codes
that read only the record and the level (0-18, 28-42) and the guards (a non-missile unit, a missile id < 0 or >= N,
a code > 42, the code as a byte). `misscheck` compares the emulator's "eax pop" lines with the model:
  missile non-NULL and its type (+0x00) != 3 -> 0; id < 0 or id >= N -> 0; c = code & 0xFF; c > 42 -> 0;
  0-17: the i32 at OFFS[c]; 18: lvl; 28: s16 +0x98 * lvl + s16 +0x96; 29..41 odd: (lvl - 1) * B + A;
  30..42 even: SKILLS_DimReturns(lvl, A, B) = min(r, b), r = (lvl*110 / (lvl+6)) * (B - A) / 100 + A
  (C division, 32-bit wrap); pairs (A, B) as PAIRS. Codes 19-27 call the elemental and physical damage getters,
  which evaluate formulas, and are not cased.

`evalcases` / `evalcheck`: fn:MISS_EvalCalc@0x0064B7C0 (__stdcall(missile, owner, offset, missileId, lvl)) on the
stock data: the memory spec points g_pDataTables at a scratch DataTables whose +0x60/+0x64 are the stock `misscode`
pool and its size and +0xB64/+0xB6C the stock `missiles` records and count, so CALC_Eval, the variable reader
sub_0064B6E0, MISS_CalcVar and SKILLS_DimReturns all run on the binary's own code over the shipped cells. Every
distinct formula cell of missiles.txt whose value tools/calc.py can compute without a unit (row-only variables,
min/max) is cased at several levels, once with a NULL missile (missileId and lvl as given) and once with a scratch
missile unit (type 3, class = the row, Unit+0x14 -> data whose s16 +0x0C is the level) and missileId = lvl = -1, so
the context {missile, owner, missileId, lvl} must come from the unit; plus the guards (a type-1 unit, an offset at
the pool's end). The model is tools/calc.py's evaluate with its missiles Env. Stdlib only.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rng  # noqa: E402

MASK = 0xFFFFFFFF
FNS = {
    "skills_min": (0x006436E0, "min", None), "skills_max": (0x006436F0, "max", None),
    "skills_rand": (0x00643700, "rand", "unit"),
    "items_min": (0x00627B50, "min", None), "items_max": (0x00627B60, "max", None),
    "items_rand": (0x00627B70, "rand", "unit"),
    "miss_min": (0x0064B700, "min", None), "miss_max": (0x0064B710, "max", None),
    "miss_rand": (0x0064B720, "rand", "ctx"),
}


def s32(v):
    v &= MASK
    return v - (1 << 32) if v & 0x80000000 else v


def model(kind, seedsite, a, b, ctx, lo, hi):
    """Returns (eax, unit seed after, ctx seed after); both seeds start as (lo, hi)."""
    useed = cseed = (lo, hi)
    if kind == "min":
        return (a if s32(a) < s32(b) else b), useed, cseed
    if kind == "max":
        return (a if s32(a) > s32(b) else b), useed, cseed
    if not ctx:
        return 0, useed, cseed
    if s32(a) >= s32(b):
        return a & MASK, useed, cseed
    n = (b - a + 1) & MASK
    r, nlo, nhi = rng.rng_range(lo, hi, n)
    if seedsite == "unit":
        useed = (nlo, nhi)
    else:
        cseed = (nlo, nhi)
    return (a + r) & MASK, useed, cseed


def cases(path, count=5000, pyseed=1):
    rnd = random.Random(pyseed)
    vals = [0, 1, 2, 5, 0x7FFFFFFF, 0x80000000, 0x80000001, MASK, 0xFFFFFFFE, 100, 0xFFFFFF9C]
    seeds = [(0, 0), (0x12345678, 666), (MASK, MASK)]
    lines = []
    for a in vals:
        for b in vals:
            for ctx in (0, 1):
                lo, hi = seeds[(a ^ b ^ ctx) % 3]
                lines.append((a, b, 0, ctx, lo, hi))
    while len(lines) < count:
        r = rnd.random()
        if r < 0.5:             # small signed ranges, as formulas use
            a = rnd.randrange(-200, 200) & MASK
            b = (s32(a) + rnd.randrange(-50, 400)) & MASK
        else:
            a, b = rnd.getrandbits(32), rnd.getrandbits(32)
        lines.append((a, b, rnd.getrandbits(32) if rnd.random() < 0.1 else 0, 0 if rnd.random() < 0.05 else 1,
                      rnd.getrandbits(32), rnd.getrandbits(32)))
    with open(path, "w") as fh:
        for ln in lines:
            fh.write(" ".join("%08x" % v for v in ln) + "\n")
    print("%d cases -> %s" % (len(lines), path))


def check(fn, cases_path, emu_path):
    addr, kind, site = FNS[fn]
    with open(cases_path) as fh:
        inputs = [tuple(int(x, 16) for x in ln.split()) for ln in fh if ln.strip()]
    with open(emu_path) as fh:
        outputs = [tuple(int(x, 16) for x in ln.split()) for ln in fh if ln.strip()]
    if len(inputs) != len(outputs):
        raise SystemExit("%d cases but %d emulator lines" % (len(inputs), len(outputs)))
    bad = steps = 0
    for i, ((a, b, c, ctx, lo, hi), (eax, ulo, uhi, clo, chi)) in enumerate(zip(inputs, outputs)):
        want = model(kind, site, a, b, ctx, lo, hi)
        got = (eax, (ulo, uhi), (clo, chi))
        if got != want:
            bad += 1
            if bad <= 10:
                print("MISMATCH line %d: in %08x %08x %08x %x %08x:%08x want %s got %s" % (
                    i + 1, a, b, c, ctx, lo, hi, want, got))
        elif want[1] != (lo, hi) or want[2] != (lo, hi):
            steps += 1
    print("%s (0x%08X): %d/%d match, %d with a seed step" % (fn, addr, len(inputs) - bad, len(inputs), steps))
    return 0 if bad == 0 else 1


MISS_N, MISS_RSIZE = 4, 0x1A4
DT, RECS, MISSILE, OTHER = 0x7F300000, 0x7F400000, 0x7F500000, 0x7F510000
OFFS = [0x38, 0x3C, 0x40, 0x44, 0x48, 0x58, 0x5C, 0x60, 0x64, 0x68, 0x4C, 0x50, 0x54, 0x6C, 0x70, 0x74, 0x78, 0x7C]
PAIRS = [(0x38, 0x3C), (0x40, 0x44), (0x58, 0x5C), (0x60, 0x64), (0x4C, 0x50), (0x6C, 0x70), (0x78, 0x7C)]
MISS_CODES = list(range(0, 19)) + list(range(28, 43))


def cdiv(x, y):
    q = abs(x) // abs(y)
    return q if (x < 0) == (y < 0) else -q


def dimret(lvl, a, b):
    """fn:SKILLS_DimReturns@0x00645B20 with 32-bit wrap at each step."""
    q = cdiv(s32(lvl * 110), s32(lvl + 6))
    r = s32(cdiv(s32(q * s32(b - a)), 100) + a)
    return b if r > b else r


def miss_model(recs, missile_type, mid, code, lvl):
    if missile_type is not None and missile_type != 3:
        return 0
    mid, lvl, c = s32(mid), s32(lvl), code & 0xFF
    if mid < 0 or mid >= MISS_N or c > 42:
        return 0
    rec = recs[mid * MISS_RSIZE:(mid + 1) * MISS_RSIZE]
    i32 = lambda o: s32(int.from_bytes(rec[o:o + 4], "little"))  # noqa: E731
    i16 = lambda o: int.from_bytes(rec[o:o + 2], "little", signed=True)  # noqa: E731
    if c < 18:
        return i32(OFFS[c]) & MASK
    if c == 18:
        return lvl & MASK
    if c == 28:
        return (i16(0x98) * lvl + i16(0x96)) & MASK
    if 29 <= c <= 42:
        a_off, b_off = PAIRS[(c - 29) // 2]
        a, b = i32(a_off), i32(b_off)
        return (((lvl - 1) * b + a) if (c - 29) % 2 == 0 else dimret(lvl, a, b)) & MASK
    raise ValueError("code %d not modelled" % c)


def misscases(d, count=5000, pyseed=1):
    rnd = random.Random(pyseed)
    os.makedirs(d, exist_ok=True)
    recs = bytes(rnd.getrandbits(8) for _ in range(MISS_N * MISS_RSIZE))
    with open(os.path.join(d, "miss-recs.bin"), "wb") as fh:
        fh.write(recs)
    with open(os.path.join(d, "miss-mem.txt"), "w") as fh:
        fh.write("# tools/calc_funcs.py misscases: synthetic missiles table for MISS_CalcVar\n")
        fh.write("dword 00744304 %08x   # g_pDataTables -> scratch DataTables\n" % DT)
        fh.write("dword %08x %08x   # +0xB64 missiles records\n" % (DT + 0xB64, RECS))
        fh.write("dword %08x %08x   # +0xB6C missiles count\n" % (DT + 0xB6C, MISS_N))
        fh.write("load %08x %s\n" % (RECS, os.path.abspath(os.path.join(d, "miss-recs.bin"))))
        fh.write("dword %08x 00000003   # a missile unit (type 3)\n" % MISSILE)
        fh.write("dword %08x 00000001   # a monster unit (type 1)\n" % OTHER)
    lines = []
    for code in MISS_CODES:
        for mid in range(MISS_N):
            for lvl in (-5, 0, 1, 2, 7, 8, 9, 16, 17, 30, 99):
                lines.append((0, 0, 0, 0, code, mid, lvl & MASK))
    for missile in (MISSILE, OTHER):
        lines.append((0, 0, missile, 0, 18, 1, 5))
    for mid in (MASK, MISS_N, 0x7FFFFFFF):
        lines.append((0, 0, 0, 0, 0, mid, 5))
    for code in (43, 0xFF, 0x100, 0x112, 0xFFFFFF00 | 29):
        lines.append((0, 0, 0, 0, code, 0, 5))
    while len(lines) < count:
        code = rnd.choice(MISS_CODES) | (rnd.getrandbits(24) << 8 if rnd.random() < 0.1 else 0)
        lvl = rnd.randrange(-5, 120) if rnd.random() < 0.8 else rnd.randrange(-0x8000, 0x8000)
        if lvl == -6:
            lvl = -5
        missile = rnd.choice((0, 0, 0, MISSILE, OTHER))
        lines.append((rnd.getrandbits(32), rnd.getrandbits(32), missile, rnd.getrandbits(32), code,
                      rnd.randrange(-1, MISS_N + 1) & MASK, lvl & MASK))
    with open(os.path.join(d, "miss-cases.txt"), "w") as fh:
        for ln in lines:
            fh.write(" ".join("%08x" % v for v in ln) + "\n")
    print("%d cases, %d records -> %s" % (len(lines), MISS_N, d))


def misscheck(d, emu_path):
    with open(os.path.join(d, "miss-recs.bin"), "rb") as fh:
        recs = fh.read()
    with open(os.path.join(d, "miss-cases.txt")) as fh:
        inputs = [tuple(int(x, 16) for x in ln.split()) for ln in fh if ln.strip()]
    with open(emu_path) as fh:
        outputs = [ln.split() for ln in fh if ln.strip()]
    if len(inputs) != len(outputs):
        raise SystemExit("%d cases but %d emulator lines" % (len(inputs), len(outputs)))
    bad = 0
    seen = set()
    for i, ((_, _, missile, _, code, mid, lvl), (eax, pop)) in enumerate(zip(inputs, outputs)):
        mtype = None if missile == 0 else (3 if missile == MISSILE else 1)
        want = miss_model(recs, mtype, mid, code, lvl)
        if int(eax, 16) != want or int(pop) != 0x14:
            bad += 1
            if bad <= 10:
                print("MISMATCH line %d: code %08x id %08x lvl %08x missile %08x: want %08x pop 20, got %s pop %s" % (
                    i + 1, code, mid, lvl, missile, want, eax, pop))
        else:
            seen.add(code & 0xFF)
    print("MISS_CalcVar (0x0064B340): %d/%d match; codes reproduced: %s" % (
        len(inputs) - bad, len(inputs), " ".join(str(c) for c in sorted(seen))))
    return 0 if bad == 0 else 1


POOL, URECS, UNITS = 0x7F700000, 0x7F800000, 0x7F680000


def _missiles(excel_dir):
    import calc
    import excel_bin
    recs, size = excel_bin.read_bin(excel_bin.find_file(excel_dir, "missiles", ".bin"))
    with open(excel_bin.find_file(excel_dir, "misscode", ".bin"), "rb") as fh:
        pool = fh.read()
    names = calc.Names(excel_dir)
    return calc, recs, size, pool, names, calc.MissilesContext(names)


def _miss_value(calc, ctx, names, excel_dir, pool, off, row, lvl):
    env = calc.Env(ctx, names, {}, excel_dir, row, lvl)
    return calc.evaluate(pool[off:], env, len(pool) - off) & MASK


def evalcases(excel_dir, d):
    calc, recs, size, pool, names, ctx = _missiles(excel_dir)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "eval-recs.bin"), "wb") as fh:
        fh.write(b"".join(recs))
    with open(os.path.join(d, "eval-pool.bin"), "wb") as fh:
        fh.write(pool)
    cells = {}                                   # offset -> (row, column) of its first use
    for row, rec in enumerate(recs):
        for col, foff in calc.COLUMNS["missiles"]:
            off = int.from_bytes(rec[foff:foff + 4], "little")
            if off < len(pool) and off not in cells:
                try:
                    _miss_value(calc, ctx, names, excel_dir, pool, off, row, 5)
                except calc.EvalError:
                    continue
                cells[off] = (row, col)
    rows = sorted({r for r, _ in cells.values()})
    lvls = [0, 1, 2, 5, 9, 17, 23, 29, 40]
    units = []                                   # (row, lvl) per scratch missile unit
    lines = []
    for off, (row, col) in sorted(cells.items()):
        for lvl in lvls:
            lines.append((0, 0, 0, 0, off, row, lvl))
            lines.append(("U", row, lvl, off))
    with open(os.path.join(d, "eval-mem.txt"), "w") as fh:
        fh.write("# tools/calc_funcs.py evalcases: stock misscode pool and missiles records for MISS_EvalCalc\n")
        fh.write("dword 00744304 %08x   # g_pDataTables -> scratch DataTables\n" % DT)
        fh.write("dword %08x %08x   # +0x60 misscode pool\n" % (DT + 0x60, POOL))
        fh.write("dword %08x %08x   # +0x64 pool size\n" % (DT + 0x64, len(pool)))
        fh.write("dword %08x %08x   # +0xB64 missiles records\n" % (DT + 0xB64, URECS))
        fh.write("dword %08x %08x   # +0xB6C missiles count\n" % (DT + 0xB6C, len(recs)))
        fh.write("load %08x %s\n" % (POOL, os.path.abspath(os.path.join(d, "eval-pool.bin"))))
        fh.write("load %08x %s\n" % (URECS, os.path.abspath(os.path.join(d, "eval-recs.bin"))))
        out = []
        for ln in lines:
            if ln[0] != "U":
                out.append(ln)
                continue
            _, row, lvl, off = ln
            k = len(units)
            units.append((row, lvl))
            u = UNITS + 0x40 * k
            fh.write("dword %08x 00000003\ndword %08x %08x\ndword %08x %08x\ndword %08x %08x\n" % (
                u, u + 4, row, u + 0x14, u + 0x20, u + 0x2C, lvl & 0xFFFF))
            out.append((0, 0, u, 0, off, MASK, MASK))
        fh.write("dword %08x 00000001   # a monster unit (type 1)\n" % OTHER)
        out.append((0, 0, OTHER, 0, sorted(cells)[0], 0, 5))
        out.append((0, 0, 0, 0, len(pool), 0, 5))
    with open(os.path.join(d, "eval-cases.txt"), "w") as fh:
        for ln in out:
            fh.write(" ".join("%08x" % v for v in ln) + "\n")
    print("%d cases over %d cells (rows %s) -> %s" % (len(out), len(cells), " ".join(map(str, rows)), d))


def evalcheck(excel_dir, d, emu_path):
    calc, recs, size, pool, names, ctx = _missiles(excel_dir)
    units = {}
    for ln in open(os.path.join(d, "eval-mem.txt")):
        f = ln.split()
        if len(f) >= 3 and f[0] == "dword":
            units[int(f[1], 16)] = int(f[2], 16)
    with open(os.path.join(d, "eval-cases.txt")) as fh:
        inputs = [tuple(int(x, 16) for x in ln.split()) for ln in fh if ln.strip()]
    with open(emu_path) as fh:
        outputs = [ln.split() for ln in fh if ln.strip()]
    if len(inputs) != len(outputs):
        raise SystemExit("%d cases but %d emulator lines" % (len(inputs), len(outputs)))
    bad = 0
    cells = set()
    for i, ((_, _, missile, _, off, mid, lvl), (eax, pop)) in enumerate(zip(inputs, outputs)):
        if missile and units.get(missile) != 3:
            want = 0
        elif off >= len(pool):
            want = 0
        else:
            if missile:
                if s32(mid) < 0:
                    mid = units[missile + 4]
                if s32(lvl) < 0:
                    data = units.get(missile + 0x14, 0)
                    lvl = (units[data + 0xC] & 0xFFFF) if data else 0
                    lvl = lvl - 0x10000 if lvl & 0x8000 else lvl
            want = _miss_value(calc, ctx, names, excel_dir, pool, off, mid, s32(lvl))
            cells.add(off)
        if int(eax, 16) != want or int(pop) != 0x14:
            bad += 1
            if bad <= 10:
                print("MISMATCH line %d: missile %08x off %d id %d lvl %d: want %08x, got %s pop %s" % (
                    i + 1, missile, off, s32(mid), s32(lvl), want, eax, pop))
    print("MISS_EvalCalc (0x0064B7C0): %d/%d match over %d stock cells" % (len(inputs) - bad, len(inputs), len(cells)))
    return 0 if bad == 0 else 1


def main(argv):
    if argv[:1] == ["evalcases"] and len(argv) == 3:
        evalcases(argv[1], argv[2])
        return 0
    if argv[:1] == ["evalcheck"] and len(argv) == 4:
        return evalcheck(argv[1], argv[2], argv[3])
    if argv[:1] == ["misscases"] and len(argv) >= 2:
        misscases(argv[1], int(argv[2]) if len(argv) > 2 else 5000, int(argv[3]) if len(argv) > 3 else 1)
        return 0
    if argv[:1] == ["misscheck"] and len(argv) == 3:
        return misscheck(argv[1], argv[2])
    if argv[:1] == ["cases"] and len(argv) >= 2:
        cases(argv[1], int(argv[2]) if len(argv) > 2 else 5000, int(argv[3]) if len(argv) > 3 else 1)
        return 0
    if argv[:1] == ["check"] and len(argv) == 4 and argv[1] in FNS:
        return check(argv[1], argv[2], argv[3])
    if argv[:1] == ["fns"]:
        for k, (addr, _, _) in FNS.items():
            print("%-12s 0x%08X" % (k, addr))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Drop quality roll model (plan 0010; first cut at Phase 1, Phase 2 extends it), checked against tc-drops.gdb logs.

    python3 -I tools/quality.py check <log> [<log> ...] [--excel DIR] [--mf N] [-v]

Model of sub_00558640_DropRollQuality as read in docs/findings/items/0002-quality-roll.md (sections 1-7):
early returns (itemtypes Normal -> 2, item unique -> 7, Magic type + quest -> 7), ITEMRATIO_Select with the
constant version argument 100, then the unique, set, rare, magic, superior and normal/low tests, each drawing
RNG_RangeB on the source unit seed (tools/rng.py). Tables come from the compiled .bin files through
tools/excel_bin.py (weapons, armor, misc concatenated in that order = the items index; itemtypes; itemratio).

check reads every QIN line (item, ilvl, source seed, ratio words) and requires the very next QIN/QOUT line to be
its QOUT (quality code, source seed after the roll). For each pair it runs the model from the QIN seed and asserts
both the code and the exit seed. There is no resync: each pair starts from its own logged seed, and a QIN without
a QOUT fails. QOUT lines with no QIN (a forced quality, TCR fq != 0) are counted and skipped.

ASSUMPTION: the killer's magic find (stat 80 of the killer plus its owner) is not in the logs of
run:2026-10-11-tc-drops. check uses --mf (default 0) for every pair. That 0 is right for those logs is an
assumption until Phase 2 reads the killers' stat 80 from the saves.

Exit 0 only when every pair reproduces. Stdlib only. Read-only.
"""
import argparse
import os
import struct
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin  # noqa: E402
import rng  # noqa: E402

EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
M32 = 0xFFFFFFFF
NAMES = {0: "none", 1: "low", 2: "normal", 3: "superior", 4: "magic", 5: "set", 6: "rare", 7: "unique"}


def s32(x):
    x &= M32
    return x - (1 << 32) if x & 0x80000000 else x


def cdiv(a, b):
    """C int division (cdq; idiv): truncation toward zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def recs(excel, table):
    r, _ = excel_bin.read_bin(excel_bin.find_file(excel, table, ".bin"))
    return r


class Tables:
    def __init__(self, excel):
        self.itypes = recs(excel, "itemtypes")
        self.items = []
        for t in ("weapons", "armor", "misc"):
            self.items.extend(recs(excel, t))
        self.ratio = [dict(v=struct.unpack_from("<16I", r, 0), ver=struct.unpack_from("<H", r, 0x40)[0],
                           uber=r[0x42], cls=r[0x43]) for r in recs(excel, "itemratio")]

    def type_of(self, item):
        return struct.unpack_from("<h", self.items[item], 0x11E)[0]

    def is_type(self, item, t):
        """ITEMS_IsType: the item's type or type2 is t or has t among its Equiv ancestors."""
        def up(x, seen):
            if x == 0 or x in seen or x >= len(self.itypes):
                return False
            if x == t:
                return True
            seen.add(x)
            r = self.itypes[x]
            return up(struct.unpack_from("<H", r, 4)[0], seen) or up(struct.unpack_from("<H", r, 6)[0], seen)
        r = self.items[item]
        return up(struct.unpack_from("<H", r, 0x11E)[0], set()) or up(struct.unpack_from("<H", r, 0x120)[0], set())

    def select(self, item, version=100):
        """ITEMRATIO_Select@0x00637910: row index or None."""
        r = self.items[item]
        typ = self.type_of(item)
        cls = 1 if (0 <= typ < len(self.itypes) and self.itypes[typ][0x21] < 7) else 0
        uber = 0
        if self.is_type(item, 50) or self.is_type(item, 45):            # armo, weap
            code = r[0x80:0x84]
            if (r[0x88:0x8C] == code or r[0x8C:0x90] == code) and typ != 38 and r[0x12A] == 0:
                uber = 1
        best, bver = None, -1
        for i, row in enumerate(self.ratio):
            if row["cls"] == cls and row["uber"] == uber and row["ver"] <= version and row["ver"] >= bver:
                best, bver = i, row["ver"]
        return best


def diminish(m100, k):
    """sub_00558610_MagicFindDiminish: ECX = mf + 100, k = 250/500/600."""
    if m100 <= 110:
        return m100
    return cdiv(s32((m100 - 100) * k), m100 - 100 + k) + 100


def range_b(seed, n):
    """RNG_RangeB: n < 1 -> 0 without a step; else one step, low & (n-1) for a power of two, else low % n."""
    if s32(n) < 1:
        return 0, seed
    lo, hi = rng.step(*seed)
    v = lo & (n - 1) if n & (n - 1) == 0 else lo % n
    return v, (lo, hi)


def roll(T, item, ilvl, ratio, seed, mf=0):
    """Returns (code, seed after, exit label, draws, itemratio row)."""
    if item >= len(T.items):
        return 0, seed, "no-record", 0, None
    r = T.items[item]
    typ = T.type_of(item)
    if typ < 0 or typ >= len(T.itypes):
        return 0, seed, "no-type", 0, None
    ty = T.itypes[typ]
    if ty[0x16]:
        return 2, seed, "normal-type", 0, None
    if r[0x129]:
        return 7, seed, "unique-flag", 0, None
    if ty[0x14] and r[0x12A]:
        return 7, seed, "magic-type-quest", 0, None
    ri = T.select(item)
    if ri is None:
        raise ValueError("no itemratio row (the game stops with error 0xE8D)")
    v = T.ratio[ri]["v"]
    d = s32(ilvl - r[0xFD])
    draws = 0
    use_mf = False
    to_superior = False
    if mf != 0:
        if mf <= -100:
            to_superior = True
        else:
            use_mf = True
    m100 = mf + 100
    if not to_superior:
        # (base, divisor, min, ratio word, MF factor, code, itemtypes byte that must be set)
        for b, dv, mn, w, k, code, need in ((0, 1, 2, 3, 250, 7, None), (6, 7, 8, 2, 500, 5, None),
                                            (3, 4, 5, 1, 600, 6, 0x15)):
            if need is not None and not ty[need]:
                continue
            c = s32((v[b] - cdiv(d, s32(v[dv]))) << 7)
            if use_mf:
                f = diminish(m100, k)
                if f != 0:
                    c = cdiv(s32(c * 100), f)
            if c <= s32(v[mn]):
                c = s32(v[mn])
            c = s32(c - cdiv(s32(ratio[w] * c), 1024))
            if c < 1:
                return code, seed, "win-nodraw", draws, ri
            x, seed = range_b(seed, c)
            draws += 1
            if x < 128:
                return code, seed, "win-draw", draws, ri
        if ty[0x14]:
            return 4, seed, "magic-type", draws, ri
        c = s32((v[9] - cdiv(d, s32(v[10]))) << 7)
        if use_mf:
            c = cdiv(s32(c * 100), m100)
        if c <= s32(v[11]):
            c = s32(v[11])
        c = s32(c - cdiv(s32(ratio[0] * c), 1024))
        if c < 1:
            return 4, seed, "win-nodraw", draws, ri
        x, seed = range_b(seed, c)
        draws += 1
        if x < 128:
            return 4, seed, "win-draw", draws, ri
    c = s32((v[12] - cdiv(d, s32(v[13]))) << 7)
    if c < 1:
        return 3, seed, "win-nodraw", draws, ri
    x, seed = range_b(seed, c)
    draws += 1
    if x < 128:
        return 3, seed, "win-draw", draws, ri
    n = s32((v[14] - cdiv(d, s32(v[15]))) << 7)
    if n < 1:
        return 2, seed, "win-nodraw", draws, ri
    x, seed = range_b(seed, n)
    draws += 1
    return (2 if x < 128 else 1), seed, "win-draw" if x < 128 else "lose-draw", draws, ri


def kv(line):
    return dict(x.split("=", 1) for x in line.split()[1:] if "=" in x)


def seedpair(s):
    a, b = s.split(":")
    return int(a, 16), int(b, 16)


def cmd_check(ns):
    T = Tables(ns.excel)
    ok = bad = forced = 0
    codes, draws, rows = Counter(), Counter(), Counter()
    for path in ns.logs:
        lines = [ln.strip() for ln in open(path, errors="replace") if ln.startswith(("QIN ", "QOUT "))]
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln.startswith("QOUT"):
                forced += 1
                i += 1
                continue
            q = kv(ln)
            where = "%s QIN#%d" % (os.path.basename(path), ok + bad)
            if i + 1 >= len(lines) or not lines[i + 1].startswith("QOUT"):
                bad += 1
                print("FAIL %s: QIN without QOUT" % where)
                i += 1
                continue
            o = kv(lines[i + 1])
            i += 2
            item, ilvl = int(q["item"]), int(q["ilvl"])
            ratio = [int(x) for x in q["ratio"].split(",")]
            code, after, why, nd, ri = roll(T, item, ilvl, ratio, seedpair(q["seed"]), ns.mf)
            want = (int(o["q"]), seedpair(o["seed"]))
            if (code, after) == want:
                ok += 1
                codes[code] += 1
                draws[nd] += 1
                rows[ri] += 1
                if ns.verbose:
                    print("ok   %s item=%d ilvl=%d ratio=%s -> %d %s (%s, %d draws, itemratio %s)" % (
                        where, item, ilvl, q["ratio"], code, NAMES[code], why, nd, ri))
            else:
                bad += 1
                print("FAIL %s item=%d ilvl=%d ratio=%s: model q=%d seed=%08x:%08x (%s), log q=%d seed=%08x:%08x" % (
                    where, item, ilvl, q["ratio"], code, after[0], after[1], why, want[0], want[1][0], want[1][1]))
    print("%d pairs, %d reproduced, %d failed (mf=%d); codes %s; draws %s; itemratio rows %s; "
          "%d QOUT without QIN (forced quality) skipped" % (
              ok + bad, ok, bad, ns.mf, " ".join("%d:%d" % kc for kc in sorted(codes.items())),
              " ".join("%d:%d" % kc for kc in sorted(draws.items())),
              " ".join("%s:%d" % kc for kc in sorted(rows.items(), key=lambda t: (t[0] is None, t[0] or 0))),
              forced))
    return 0 if bad == 0 and ok > 0 else 1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("check", help="replay every QIN/QOUT pair of tc-drops logs (MF assumed --mf, default 0)")
    a.add_argument("logs", nargs="+")
    a.add_argument("--excel", default=EXCEL)
    a.add_argument("--mf", type=int, default=0, help="magic find used for every pair (not logged; assumed 0)")
    a.add_argument("-v", "--verbose", action="store_true")
    ns = ap.parse_args(argv)
    return cmd_check(ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

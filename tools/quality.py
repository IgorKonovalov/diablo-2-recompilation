#!/usr/bin/env python3
"""Drop quality roll model (plan 0010; first cut at Phase 1, Phase 2 extends it), checked against tc-drops.gdb logs.

    python3 -I tools/quality.py check <log> [<log> ...] [--excel DIR] [--mf N] [-v]

Model of ITEMS_DropRollQuality as read in docs/findings/items/0002-quality-roll.md (sections 1-7):
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
    """ITEMS_MagicFindDiminish: ECX = mf + 100, k = 250/500/600."""
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


def type_flags(T, item, how):
    """Counterfactual type reads (plan 0038 batch S2a): the itemtypes bytes +0x14 (Magic), +0x15 (Rare) and +0x16
    (Normal) OR-ed over the item's type and type2 ("type2"), or over both and their Equiv ancestors ("equiv")."""
    r = T.items[item]
    todo = [struct.unpack_from("<h", r, 0x11E)[0], struct.unpack_from("<h", r, 0x120)[0]]
    seen, out = set(), bytearray(3)
    while todo:
        x = todo.pop()
        if x <= 0 or x >= len(T.itypes) or x in seen:
            continue
        seen.add(x)
        ty = T.itypes[x]
        for k in range(3):
            out[k] |= 1 if ty[0x14 + k] else 0
        if how == "equiv":
            todo += [struct.unpack_from("<H", ty, 4)[0], struct.unpack_from("<H", ty, 6)[0]]
    return out


def roll(T, item, ilvl, ratio, seed, mf=0, linear=False, trace=None, cf=None):
    """Returns (code, seed after, exit label, draws, itemratio row).

    linear=True replaces ITEMS_MagicFindDiminish by its linear branch (F = mf + 100 for every mf), the
    counterfactual of plan 0010 Phase 2. trace, if a list, receives one (test, chance, draw or None, won) per test
    reached. cf (plan 0038 batch S2a counterfactuals, None for the game's roll): {"flags": "type2"|"equiv"} reads
    the Normal/Magic/Rare bytes through type_flags; {"div": "floor"} divides d by the divisors with floor division."""
    cf = cf or {}
    if item >= len(T.items):
        return 0, seed, "no-record", 0, None
    r = T.items[item]
    typ = T.type_of(item)
    if typ < 0 or typ >= len(T.itypes):
        return 0, seed, "no-type", 0, None
    ty = T.itypes[typ]
    if cf.get("flags"):
        fl = type_flags(T, item, cf["flags"])
        ty = bytearray(ty)
        ty[0x14:0x17] = fl
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
    if cf.get("div") == "floor":
        cdiv_ = lambda a, b: a // b  # noqa: E731
    else:
        cdiv_ = cdiv
    draws = 0
    use_mf = False
    to_superior = False
    if mf != 0:
        if mf <= -100:
            to_superior = True
        else:
            use_mf = True
    m100 = mf + 100

    def test(name, c, code):
        nonlocal seed, draws
        if c < 1:
            if trace is not None:
                trace.append((name, c, None, True))
            return True, "%s:win-nodraw" % name
        x, seed = range_b(seed, c)
        draws += 1
        won = x < 128
        if trace is not None:
            trace.append((name, c, x, won))
        return won, "%s:%s" % (name, "win-draw" if won else "lose-draw")

    if not to_superior:
        # (name, base, divisor, min, ratio word, MF factor, code, itemtypes byte that must be set)
        for name, b, dv, mn, w, k, code, need in (("unique", 0, 1, 2, 3, 250, 7, None),
                                                  ("set", 6, 7, 8, 2, 500, 5, None),
                                                  ("rare", 3, 4, 5, 1, 600, 6, 0x15)):
            if need is not None and not ty[need]:
                continue
            c = s32((v[b] - cdiv_(d, s32(v[dv]))) << 7)
            if use_mf:
                f = m100 if linear else diminish(m100, k)
                if f != 0:
                    c = cdiv(s32(c * 100), f)
            if c <= s32(v[mn]):
                c = s32(v[mn])
            c = s32(c - cdiv(s32(ratio[w] * c), 1024))
            won, why = test(name, c, code)
            if won:
                return code, seed, why, draws, ri
        if ty[0x14]:
            return 4, seed, "magic-type", draws, ri
        c = s32((v[9] - cdiv_(d, s32(v[10]))) << 7)
        if use_mf:
            c = cdiv(s32(c * 100), m100)
        if c <= s32(v[11]):
            c = s32(v[11])
        c = s32(c - cdiv(s32(ratio[0] * c), 1024))
        won, why = test("magic", c, 4)
        if won:
            return 4, seed, why, draws, ri
    c = s32((v[12] - cdiv_(d, s32(v[13]))) << 7)
    won, why = test("superior", c, 3)
    if won:
        return 3, seed, why, draws, ri
    n = s32((v[14] - cdiv_(d, s32(v[15]))) << 7)
    won, why = test("normal", n, 2)
    return (2 if won else 1), seed, why, draws, ri


def kv(line):
    return dict(x.split("=", 1) for x in line.split()[1:] if "=" in x)


def seedpair(s):
    a, b = s.split(":")
    return int(a, 16), int(b, 16)


QEXTRA = ("QROW", "QKMF", "QOWN", "QOMF", "QMF")


def pairs_of(path):
    """Yield (qin, extra, qout, tcr, err) per QIN of a log; qout None (with err) when the QIN has no QOUT.

    extra maps the QROW/QKMF/QOWN/QOMF/QMF heads logged between QIN and QOUT (tc-drops.gdb from plan 0010
    Phase 2 on) to their fields; tcr is the last TCR line's fields. QOUT lines with no QIN (a forced quality)
    are yielded as (None, None, qout, tcr, None)."""
    lines = [ln.strip() for ln in open(path, errors="replace")
             if ln.startswith(("TCR ", "QIN ", "QOUT ") + tuple(h + " " for h in QEXTRA))]
    tcr = {}
    i = 0
    while i < len(lines):
        ln = lines[i]
        i += 1
        if ln.startswith("TCR"):
            tcr = kv(ln)
            continue
        if ln.startswith("QOUT"):
            yield None, None, kv(ln), tcr, None
            continue
        if not ln.startswith("QIN"):
            continue                      # a Q* line outside a QIN/QOUT pair: ignored
        extra = {}
        while i < len(lines) and lines[i].split(" ", 1)[0] in QEXTRA:
            extra[lines[i].split(" ", 1)[0]] = kv(lines[i])
            i += 1
        if i < len(lines) and lines[i].startswith("QOUT"):
            yield kv(ln), extra, kv(lines[i]), tcr, None
            i += 1
        else:
            yield kv(ln), extra, None, tcr, "QIN without QOUT"


def magic_find(extra, tcr, default):
    """(mf, source): the logged QMF value if any; 0 without a player/monster killer (ITEMS_DropMagicFind);
    else the --mf input."""
    if "QMF" in extra:
        return int(extra["QMF"]["mf"]), "logged"
    if tcr.get("killer", "1") != "" and int(tcr.get("killer", "1"), 16) == 0:
        return 0, "no-killer"
    if "ktype" in tcr and int(tcr["ktype"]) > 1:
        return 0, "killer-type"
    return default, "input"


def fmt_trace(tr):
    return " ".join("%s(c=%d%s)%s" % (n, c, "" if x is None else ",x=%d" % x, "W" if w else "L") for n, c, x, w in tr)


def cmd_check(ns):
    T = Tables(ns.excel)
    ok = bad = forced = 0
    codes, draws, rows, mfsrc, exits = Counter(), Counter(), Counter(), Counter(), Counter()
    for path in ns.logs:
        n = 0
        for q, extra, o, tcr, err in pairs_of(path):
            if q is None:
                forced += 1
                continue
            where = "%s QIN#%d" % (os.path.basename(path), n)
            n += 1
            if err:
                bad += 1
                print("FAIL %s: %s" % (where, err))
                continue
            item, ilvl = int(q["item"]), int(q["ilvl"])
            ratio = [int(x) for x in q["ratio"].split(",")]
            mf, src = magic_find(extra, tcr, ns.mf)
            tr = []
            code, after, why, nd, ri = roll(T, item, ilvl, ratio, seedpair(q["seed"]), mf, ns.mf_linear, tr)
            want = (int(o["q"]), seedpair(o["seed"]))
            problems = []
            if (code, after) != want:
                problems.append("model q=%d seed=%08x:%08x (%s), log q=%d seed=%08x:%08x" % (
                    code, after[0], after[1], why, want[0], want[1][0], want[1][1]))
            if "QROW" in extra:
                lr = int(extra["QROW"]["row"])
                if lr != (-1 if ri is None else ri):
                    problems.append("itemratio row: model %s, log %d" % (ri, lr))
            elif ri is not None and any(h in extra for h in ("QKMF", "QMF")):
                problems.append("QROW missing while the model selects row %d" % ri)
            if "QMF" in extra and "QKMF" in extra:
                s_ = int(extra["QKMF"]["kmf"]) + (int(extra["QOMF"]["omf"]) if "QOMF" in extra else 0)
                if s_ != mf:
                    problems.append("QMF %d != QKMF + QOMF %d" % (mf, s_))
            if not problems:
                ok += 1
                codes[code] += 1
                draws[nd] += 1
                rows[ri] += 1
                mfsrc[src if ri is not None else "unused"] += 1   # early returns read no magic find
                exits[why] += 1
                if ns.verbose:
                    print("ok   %s item=%d ilvl=%d ratio=%s mf=%d(%s) -> %d %s (%s, %d draws, itemratio %s) %s" % (
                        where, item, ilvl, q["ratio"], mf, src, code, NAMES[code], why, nd, ri, fmt_trace(tr)))
            else:
                bad += 1
                line = "FAIL %s item=%d ilvl=%d ratio=%s mf=%d(%s): %s; trace %s" % (
                    where, item, ilvl, q["ratio"], mf, src, "; ".join(problems), fmt_trace(tr))
                if ns.mf_linear:
                    tr2 = []
                    c2, _, why2, _, _ = roll(T, item, ilvl, ratio, seedpair(q["seed"]), mf, False, tr2)
                    line += "; diminishing model q=%d (%s) trace %s" % (c2, why2, fmt_trace(tr2))
                print(line)
    print("%d pairs, %d reproduced, %d failed (mf input=%d%s; mf source %s); codes %s; draws %s; itemratio rows %s; "
          "%d QOUT without QIN (forced quality) skipped" % (
              ok + bad, ok, bad, ns.mf, ", LINEAR magic find (counterfactual)" if ns.mf_linear else "",
              " ".join("%s:%d" % kc for kc in sorted(mfsrc.items())),
              " ".join("%d:%d" % kc for kc in sorted(codes.items())),
              " ".join("%d:%d" % kc for kc in sorted(draws.items())),
              " ".join("%s:%d" % kc for kc in sorted(rows.items(), key=lambda t: (t[0] is None, t[0] or 0))),
              forced))
    if ns.verbose:
        print("exits: " + " ".join("%s:%d" % kc for kc in sorted(exits.items())))
    return 0 if bad == 0 and ok > 0 else 1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("check", help="replay every QIN/QOUT pair of tc-drops logs")
    a.add_argument("logs", nargs="+")
    a.add_argument("--excel", default=EXCEL)
    a.add_argument("--mf", type=int, default=0,
                   help="magic find of a player/monster killer when the log has no QMF line (an input, e.g. from "
                        "the save; default 0)")
    a.add_argument("--mf-linear", action="store_true",
                   help="counterfactual: replace the diminishing returns of unique/set/rare by F = mf + 100")
    a.add_argument("-v", "--verbose", action="store_true")
    ns = ap.parse_args(argv)
    return cmd_check(ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

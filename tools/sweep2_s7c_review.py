#!/usr/bin/env python3
"""Review check for plan 0066 batch S7c (`lane/n66m`, the Tier A audit): one question the kept check left at game level.

    python3 -I tools/sweep2_s7c_review.py [--out F]

For every monster request of type 2, 7, 9 or 13 from MonPathPlanType (0x005A62F4) that left `+0x28` = 0 and has no
logged type-15 follow-up from 0x005A6353 in its frame (check-s7c's 84), it places the game's type-15 CAP lines (reach
or ref) against the request by the logger's line counter (a CAP line's `n` and a plan's `k` share it): a cap line
before the request, or one after it, with the distance in lines. Same logs and the same stock cut as
`tools/sweep2_s7c.py` (imported, unchanged). Stdlib only. Read-only.
"""
import argparse
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import path as P  # noqa: E402
import sweep2_s7c as T  # noqa: E402


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    c = collections.Counter()
    lines = []
    for lp in T.logs():
        name = os.path.basename(lp)
        for g in P.parse(lp):
            first = next((pl.k for pl in g.plans if pl.pln.get("probe")), None)
            plans = [pl for pl in g.plans if first is None or pl.k < first]
            caps15 = {x["k"]: x["n"] for x in g.caps if x["key"] == 15}
            byu = collections.defaultdict(list)
            for pl in plans:
                byu[(pl.unit_type, pl.pln["u"][2])].append(pl)
            for pl in plans:
                if pl.unit_type != 1 or pl.plx is None or pl.pln["ra"] != T.RA_MON_REQ:
                    continue
                if pl.ty not in T.FALLBACK_TYPES or pl.plx["n28"] != 0:
                    continue
                lst = byu[(1, pl.pln["u"][2])]
                i = lst.index(pl)
                nxt = lst[i + 1] if i + 1 < len(lst) else None
                if nxt is not None and nxt.pln["ra"] == T.RA_MON_FALLBACK and nxt.pln["fr"] == pl.pln["fr"]:
                    continue
                c["empty request, no logged fallback"] += 1
                before = sorted(k for k, n in caps15.items() if n < pl.k)
                if before:
                    c["a type-15 cap line (%s) before the request" % "+".join(before)] += 1
                else:
                    after = sorted((n - pl.k, k) for k, n in caps15.items())
                    c["no type-15 cap line before; first after: %s" % (
                        "%s, %d lines later" % (after[0][1], after[0][0]) if after else "none")] += 1
                    lines.append("  %s k=%d type %d frame %d caps15 %s" % (name, pl.k, pl.ty, pl.pln["fr"], caps15))
    out = open(a.out, "w") if a.out else sys.stdout
    out.write("== the empty 2/7/9/13 requests with no logged type-15 fallback, against the type-15 cap lines\n")
    for k in sorted(c):
        out.write("  %-100s %6d\n" % (k, c[k]))
    out.write("== the cases with no cap line before\n")
    for ln in lines:
        out.write(ln + "\n")
    if a.out:
        out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

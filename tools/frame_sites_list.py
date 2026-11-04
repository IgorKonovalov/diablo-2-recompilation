#!/usr/bin/env python3
"""Plan 0055 Phase 2b: list the locations a window's XS lines step chained seeds at, outside the unit's own event, with the
function that holds each (re/symbols.csv, the nearest symbol at or below the address). It is how the touch and pass-draw tables
of tools/frame_window.py are drawn up from a development log: every location is then named from the specs by hand (rule 18).
No game, no write.    python3 -I tools/frame_sites_list.py LOG [LOG ...]
"""
import bisect
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import frame_window as fw  # noqa: E402
import frame_xs  # noqa: E402


def symbols():
    rows = []
    for ln in open(os.path.join(os.path.dirname(HERE), "re", "symbols.csv")):
        p = ln.split(",")
        if p[0].startswith("0x") and len(p) > 2 and p[1] == "func":
            rows.append((int(p[0], 16), p[2]))
    rows.sort()
    return rows


def main(paths):
    sym = symbols()
    keys = [a for a, _n in sym]

    def fn(a):
        i = bisect.bisect_right(keys, a) - 1
        return "%s+%#x" % (sym[i][1], a - sym[i][0]) if i >= 0 else "?"
    for p in paths:
        for w in fw.parse_log(p)[0]:
            x = frame_xs.check_chain2(w, touch=[], passdraw={})
            by = collections.defaultdict(collections.Counter)
            ctxs = collections.defaultdict(collections.Counter)
            for f in x["fails"]:
                m = re.search(r"at (0x[0-9a-f]+)", f["msg"])
                if m and f["kind"] in ("class", "nopair"):
                    k = f["key"]
                    by[(f["kind"], int(m.group(1), 16))][("room" if k[0] == "R" else "ty%d" % k[1]) if k != "G" else "G"] += 1
                    ctxs[(f["kind"], int(m.group(1), 16))][f["ctx"]] += 1
            print("WINDOW %s id=%s scene=%s start=%s: steps by class %s, untracked %d" % (
                os.path.basename(p), w["wid"], w["scene"], w["start"], dict(x["cls"]), sum(x["untracked"].values())))
            for (k, a), c in sorted(by.items(), key=lambda kv: -sum(kv[1].values())):
                print("  %-6s %#010x %-44s steps %d on %s; %s" % (k, a, fn(a), sum(c.values()), dict(c), dict(ctxs[(k, a)].most_common(3))))


if __name__ == "__main__":
    main(sys.argv[1:])

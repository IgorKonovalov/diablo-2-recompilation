#!/usr/bin/env python3
"""Plan 0056 Phase 2: per-game counts of the multi-case probe log (the numbers behind harness-play.md § Fresh process).

    python3 -I tools/probe0056_check.py LOG.log

Cuts the log by the `end` marks of LOG's .marks.tsv (game i = the lines after game i-1's end mark up to its own) and
prints per game: lines, LC0 lines and the distinct (level id -> seed, base) pairs, PST counter first/last and the
players-override values seen, HCP counter first/last/count, TL lines, TINIT lines. Then the level seeds compared across
games. Stdlib only.
"""
import collections
import json
import sys


def main(path):
    marks = [l.rstrip("\n").split("\t") for l in open(path[:-4] + ".marks.tsv")][1:]
    ends = [int(m[3]) for m in marks if m[1] == "end"]
    rows = open(path, errors="replace").read().split("\n")
    cuts = [0] + ends
    seeds = collections.defaultdict(set)
    for g in range(len(ends)):
        seg = rows[cuts[g]:cuts[g + 1]]
        lc = collections.OrderedDict()
        n = collections.Counter()
        pst, hcp, po = [], [], set()
        for r in seg:
            tag, _, rest = r.partition(" ")
            n[tag] += 1
            if tag == "LC0":
                d = json.loads(rest)
                lc[d["id"]] = (d["seed"], d["base"])
                seeds[d["id"]].add((d["seed"], d["base"]))
            elif tag == "PST":
                d = json.loads(rest)
                pst.append(d["hc"])
                po.add(d["po"])
            elif tag == "HCP":
                hcp.append(json.loads(rest)["hc"])
        print("g%d lines %d LC0 %d ids %s PST hc %s..%s po %s HCP n %d %s TL %d TINIT %d" % (
            g, len(seg), n["LC0"], list(lc), pst[:1], pst[-1:], sorted(po), len(hcp), hcp, n["TL"], n["TINIT"]))
    print("level seeds, distinct pairs per level id over all games:",
          {k: len(v) for k, v in sorted(seeds.items())})


if __name__ == "__main__":
    main(sys.argv[1])

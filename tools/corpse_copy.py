#!/usr/bin/env python3
"""Plan 0054, `lane/p54b` review: which copy of the room grids the `DC` lines of run:2026-10-14-collision were read on.

    python3 -I tools/corpse_copy.py LOG [LOG ...]

A room rectangle of one level is built under two DRLG rooms when the game holds a server act and a client act. `SN` (the pass entry 0x0054EC90, server code) names
the server's: for each (level, rectangle) the check counts the DRLG rooms and those with an `SN` line, then places every `DC` line (the tests 0x004B05DB, 0x004B09FB) by
the DRLG room its `room` pointer was last built under, so a room's later rebuild keeps its copy.
"""
import collections
import json
import sys


def read(lines):
    """One log: returns (Counter of the DC lines by where their room lies, Counter of the keys by (DRLG rooms, with SN), {unit: [the test's address per line]})."""
    cur, drs, snd, dcs, units = {}, collections.defaultdict(set), set(), [], collections.defaultdict(list)
    for line in lines:
        tag, _, rest = line.partition(" ")
        if tag not in ("CB", "SN", "DC") or not rest.startswith("{"):
            continue
        try:
            d = json.loads(rest)
        except ValueError:
            continue
        if tag == "CB":
            k = (d["lid"], tuple(d["rect"]))
            cur[d["room"]] = (k, d["dr"])
            drs[k].add(d["dr"])
        elif tag == "SN":
            if d["room"] in cur:
                snd.add(cur[d["room"]])
        else:
            dcs.append(cur.get(d["room"]))
            units[d["u"]].append(d["pc"])
    where = collections.Counter()
    for c in dcs:
        if c is None:
            where["room never built in this log"] += 1
            continue
        k, dr = c
        twins = [x for x in drs[k] if x != dr]
        where["own copy SN=%d, other copies %d, one with SN=%d" % ((k, dr) in snd, len(twins), any((k, x) in snd for x in twins))] += 1
    keys = collections.Counter((len(v), sum((k, x) in snd for x in v)) for k, v in drs.items())
    return where, keys, units


def main(paths):
    where, keys, units, seqs = collections.Counter(), collections.Counter(), 0, collections.Counter()
    for p in paths:
        with open(p, errors="replace") as fh:
            w, k, u = read(fh)
        where.update(w)
        keys.update(k)
        units += len(u)
        seqs.update(tuple("%08x" % a for a in v) for v in u.values())
    print("logs %d" % len(paths))
    print("level rectangles by (DRLG rooms, of them with SN): %s" % sorted(keys.items()))
    print("DC lines %d, unit addresses %d" % (sum(where.values()), units))
    for k, n in sorted(where.items()):
        print("  %-60s %d" % (k, n))
    print("tests hit per unit address: %s" % seqs.most_common())


if __name__ == "__main__":
    main(sys.argv[1:])

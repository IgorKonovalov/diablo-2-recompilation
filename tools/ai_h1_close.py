#!/usr/bin/env python3
"""Plan 0052 H1, `lane/p52d` review: what the gaps of the logs written with tools/gdb/ai-skills.gdb are, and what the original
331 share with them. Reads logs and gap lists, writes nothing.

    python3 -I tools/ai_h1_close.py new GAPLIST LOG [GAPLIST LOG ...]   # gap lists written by the first form of the walk
    python3 -I tools/ai_h1_close.py orig GAPLIST [GAPLIST ...]          # the original runs' lists, run from their log directory

`new`: for each monster gap of a list, in file order, the unit's AI decisions between the two skill events; whether the next
event starts inside the last of them (no AIX yet); the steps from that decision's last AIB seed to the event's entry seed;
and whether tools/ai_resume.py reproduces every one of those decisions (it asserts the seed at each boundary call, so a draw
it models is compared). Prints `H1GAP` per list and `H1NEW` totals, with the AI rows and the first-disagreement tags.
`orig`: each distinct monster gap by its unit's class (the event line's `u.c`) and its first-disagreement tag: `H1ORIG`.
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai  # noqa: E402
import ai_resume as R  # noqa: E402
import skills  # noqa: E402

GAP = re.compile(r"(\S+\.log) n=(\d+) monster unit (\d+) \[(.*?)\]: .*?first disagreement (\S+?)[; ]")


def raw_lines(path):
    out = []
    with open(path, errors="replace") as fh:
        for ln in fh:
            tag, _, rest = ln.partition(" ")
            if rest.startswith("{"):
                try:
                    out.append((tag, json.loads(rest)))
                except ValueError:
                    pass
    return out


def is_event(tag, d, u):
    return tag in ("SST0", "SDO0") and isinstance(d.get("u"), dict) and d["u"]["u"] == u


def new(pairs):
    code = R.Code()
    M = R.Machine(code, R.bnd_set())
    tot, rows, status = collections.Counter(), collections.Counter(), collections.Counter()
    for gaplist, log in pairs:
        decs = {d["aid"]["n"]: d for d in ai.parse(log)["dec"]}
        L = raw_lines(log)
        ev = {(d["n"], d["u"]["u"]): i for i, (t, d) in enumerate(L) if t in ("SST0", "SDO0") and isinstance(d.get("u"), dict)}
        one = collections.Counter()
        for g in open(gaplist, errors="replace"):
            m = GAP.search(g)
            if not m:
                continue
            n, u, tag = int(m[2]), int(m[3]), m[5]
            i = ev[(n, u)]
            s0 = skills.sd_parse(L[i][1]["u"]["s"])
            ds, closed, j = [], set(), i - 1
            while j >= 0 and not is_event(L[j][0], L[j][1], u):
                t, d = L[j]
                if t == "AIX":
                    closed.add(d["k"])
                elif t == "AID" and d["u"] == u:
                    ds.append(d["n"])
                j -= 1
            one["gaps"] += 1
            one["first disagreement " + tag] += 1
            if not ds or ds[0] in closed:
                one["no decision open at the next event"] += 1
                continue
            one["next event inside a decision"] += 1
            one["decisions"] += len(ds)
            last = [d for t, d in L[max(0, i - 400):i] if t == "AIB" and d.get("k") == ds[0]]
            k = skills.steps_between(skills.sd_parse(last[-1]["s"]), s0, 64) if last else None
            one["last AIB to the event: %s steps" % k] += 1
            good = True
            for dn in ds:
                r = R.check_decision(M, decs[dn])
                status[r.status] += 1
                rows[decs[dn]["aid"]["ai"]] += 1
                good = good and r.status == "ok"
            one["every decision resumed" if good else "a decision not resumed"] += 1
        print("H1GAP %s %s" % (os.path.basename(log), json.dumps(dict(sorted(one.items())))))
        tot.update(one)
    print("H1NEW %s" % json.dumps(dict(sorted(tot.items()))))
    print("H1NEW rows %s status %s" % (json.dumps(dict(sorted(rows.items()))), json.dumps(dict(status))))


def orig(lists):
    seen, cache = set(), {}
    cls, tags, pair = collections.Counter(), collections.Counter(), collections.Counter()
    for f in lists:
        for g in open(f, errors="replace"):
            m = GAP.search(g)
            if not m or (m[1], m[2], m[3]) in seen:
                continue
            seen.add((m[1], m[2], m[3]))
            if m[1] not in cache:
                cache[m[1]] = {(d["n"], d["u"]["u"]): d["u"].get("c") for t, d in raw_lines(m[1])
                               if t in ("SST0", "SDO0") and isinstance(d.get("u"), dict)}
            c = cache[m[1]].get((int(m[2]), int(m[3])))
            cls[c] += 1
            tags[m[5]] += 1
            pair["%s %s" % (c, m[5])] += 1
    print("H1ORIG gaps=%d logs=%d" % (len(seen), len(cache)))
    print("H1ORIG class %s" % json.dumps(dict(cls.most_common())))
    print("H1ORIG first_disagreement %s" % json.dumps(dict(tags.most_common())))
    print("H1ORIG class_tag %s" % json.dumps(dict(pair.most_common())))


def main(argv):
    if len(argv) < 2 or argv[0] not in ("new", "orig"):
        print(__doc__)
        return 2
    if argv[0] == "new":
        new(list(zip(argv[1::2], argv[2::2])))
    else:
        orig(argv[1:])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

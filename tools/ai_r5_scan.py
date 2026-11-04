#!/usr/bin/env python3
"""Plan 0052 Phase 2, lane/p52d: what a rev 5 logger run of tools/gdb/ai.py holds, per log.

    python3 -I tools/ai_r5_scan.py LOG [LOG ...]

Per log, one `R5` line: the logger line (`AI logger armed rev N bmax M`), the decisions (AID) per MonStats AI row, the
AID `st` (AiCtl state word) values with their decision counts, the AIL lines (the 600-call limit: how many, and how many
with `pend` 0, where nothing re-arms the breakpoints), and `aib_in_msm`: the AIB lines whose `k` equals an open
MSM0..MSM1 span's `k` and whose line number `n` lies between the two (rev 5 skips them); `aib_in_open_span`: such AIB
lines of a span whose MSM1 was never logged (the 600-call limit switches the MSM1 breakpoint off with the others), of
which `aib_in_open_span_ail` in a decision that has an AIL line (then the span's command may have returned already). Stdlib only; reads logs, writes nothing.
"""
import collections
import json
import re
import sys


def scan(path):
    rev = None
    rows, states = collections.Counter(), collections.Counter()
    ail, ail0 = 0, 0
    open_k = {}                     # k -> n of its open MSM0
    spans, aib_in, aib_total = 0, 0, 0
    inside = {}                     # k -> AIB lines seen since its open MSM0
    ail_k = set()
    with open(path, errors="replace") as fh:
        for line in fh:
            if line.startswith("AI logger armed"):
                m = re.search(r"rev (\d+) bmax (\d+)", line)
                rev = (int(m.group(1)), int(m.group(2))) if m else line.strip()
                continue
            tag, _, rest = line.partition(" ")
            if tag not in ("AID", "MSM0", "MSM1", "AIB", "AIL"):
                continue
            try:
                d = json.loads(rest)
            except ValueError:
                continue
            if tag == "AID":
                rows[d.get("ai")] += 1
                states[d.get("st")] += 1
            elif tag == "MSM0":
                open_k[d["k"]] = d["n"]
                inside[d["k"]] = 0
                spans += 1
            elif tag == "MSM1":
                if d["k"] in open_k:
                    aib_in += inside.pop(d["k"], 0)
                open_k.pop(d["k"], None)
            elif tag == "AIB":
                aib_total += 1
                n0 = open_k.get(d["k"])
                if n0 is not None and d.get("n", 0) > n0:
                    inside[d["k"]] = inside.get(d["k"], 0) + 1
            elif tag == "AIL":
                ail += 1
                ail_k.add(d["k"])
                if d.get("pend") == 0:
                    ail0 += 1
    return {"rev": rev, "decisions": sum(rows.values()), "rows": dict(sorted(rows.items(), key=lambda kv: (kv[0] is None, kv[0]))),
            "states": dict(sorted(states.items(), key=lambda kv: (kv[0] is None, kv[0]))), "ail": ail, "ail_pend0": ail0,
            "msm_spans": spans, "msm_open": len(open_k), "aib": aib_total, "aib_in_msm": aib_in,
            "aib_in_open_span": sum(inside.get(k, 0) for k in open_k),
            "aib_in_open_span_ail": sum(inside.get(k, 0) for k in open_k if k in ail_k)}


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    for p in argv:
        print("R5 %s %s" % (p, json.dumps(scan(p), sort_keys=False)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

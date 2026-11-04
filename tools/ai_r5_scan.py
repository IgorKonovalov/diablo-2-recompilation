#!/usr/bin/env python3
"""Plan 0052 Phase 2, lane/p52d: what a rev 5 logger run of tools/gdb/ai.py holds, per log.

    python3 -I tools/ai_r5_scan.py LOG [LOG ...]

Per log, one `R5` line: the logger line (`AI logger armed rev N bmax M`), the decisions (AID) per MonStats AI row, the
AID `st` (AiCtl state word) values with their decision counts, the AIL lines (the 600-call limit: how many, and how many
with `pend` 0, where nothing re-arms the breakpoints), and `aib_in_msm`: the AIB lines whose `k` equals an open
MSM0..MSM1 span's `k` and whose line number `n` lies between the two (rev 5 skips them). A span with no MSM1 is open
to the log's end and counted as `open`. Stdlib only; reads logs, writes nothing.
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
                spans += 1
            elif tag == "MSM1":
                open_k.pop(d["k"], None)
            elif tag == "AIB":
                aib_total += 1
                n0 = open_k.get(d["k"])
                if n0 is not None and d.get("n", 0) > n0:
                    aib_in += 1
            elif tag == "AIL":
                ail += 1
                if d.get("pend") == 0:
                    ail0 += 1
    return {"rev": rev, "decisions": sum(rows.values()), "rows": dict(sorted(rows.items(), key=lambda kv: (kv[0] is None, kv[0]))),
            "states": dict(sorted(states.items(), key=lambda kv: (kv[0] is None, kv[0]))), "ail": ail, "ail_pend0": ail0,
            "msm_spans": spans, "msm_open": len(open_k), "aib": aib_total, "aib_in_msm": aib_in}


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    for p in argv:
        print("R5 %s %s" % (p, json.dumps(scan(p), sort_keys=False)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

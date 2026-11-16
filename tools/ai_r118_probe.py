#!/usr/bin/env python3
"""Plan 0069 Phase 3b probe: R118 (Succubus, think 0x005E1E00), the unit-seed steps a decision really takes (AID `s` to AIX
`s`) against the checker's model, grouped by (dist < aip(4), melee word, the rev 7 word R118.flag0x20 logged or not).

    python3 -I tools/ai_r118_probe.py LOG [LOG ...]
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import ai  # noqa: E402
import ai_model_check as m  # noqa: E402


def steps(a, b):
    s, t = ai.seedval(a), ai.seedval(b)
    for k in range(8):
        if s == t:
            return k
        s = ai.step(s)
    return -1


def main(paths):
    c = Counter()
    first = Counter()
    for p in paths:
        for d in ai.parse(p)["dec"]:
            a = d["aid"]
            if a["th"] != 0x5E1E00 or d.get("trunc"):
                continue
            aixs = d["aix"]["s"] if isinstance(d["aix"], dict) else d["aix"][-1]["s"]
            aip4 = [ai.s16(x) for x in ai.le16(a["aip"], 24)][9 + a["diff"]]
            w = (d.get("r7") or {}).get("R118.flag0x20")
            o = m.check(m.m_r118, d)
            c[("near" if a["ctx"][5] < aip4 else "far", "melee" if a["ctx"][6] else "nomelee",
               "word=" + str(w), "real_seed_steps=%d" % steps(a["s"], aixs), "model=" + o.status)] += 1
            if a["ctx"][5] < aip4 and d["aib"]:
                first[("near", "word=" + str(w), "first boundary fn 0x%08X" % d["aib"][0]["fn"])] += 1
    for k, v in sorted(c.items(), key=str):
        print(v, *k)
    for k, v in sorted(first.items(), key=str):
        print(v, *k)
    print("DECISIONS", sum(c.values()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

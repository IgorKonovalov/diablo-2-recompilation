#!/usr/bin/env python3
"""Plan 0052 H1 (lane/p52d): the seed a monster carries out of an AI decision against the seed its next skill-side line
observes, in logs written with tools/gdb/ai-skills.gdb (both loggers in one game).

    python3 -I tools/ai_h1.py LOG [LOG ...]

For every AI decision (AID .. AIX, tools/gdb/ai.py) of a monster, the unit's seed at the decision's exit (AIX `s`) is
compared with the next later line of the skills logger that names the same unit and carries its seed: MAS0 (`u.s`), SST0,
SDO0 (`u.s`), MC0 (`o.s`) or MH0 (`d.s`), and the number of LCG steps between the two is counted (0..64, else `far`;
`none`: the unit has no such line before its next decision or the log's end). 0 steps means the decision's logged exit
closes the gap to that line. `AIN` or another decision of the unit first ends the search (`next decision`). Prints one
`H1` line per log and one `H1STEPS` histogram. Stdlib and tools/skills.py's LCG helpers; reads logs, writes nothing.
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import skills  # noqa: E402


def obs_of(tag, d):
    """(unit pointer, seed string) of a skills-logger line that observes a unit's seed, else None."""
    try:
        if tag in ("MAS0", "SST0", "SDO0") and isinstance(d.get("u"), dict):
            return d["u"]["u"], d["u"]["s"]
        if tag == "MC0" and d.get("o"):
            return d["o"]["u"], d["o"]["s"]
        if tag == "MH0" and d.get("d"):
            return d["d"]["u"], d["d"]["s"]
    except KeyError:
        return None
    return None


def scan(path):
    lines = skills.parse(path)
    exits = {}
    ai = {}
    for tag, d in lines:
        if tag == "AID":
            ai[d["n"]] = d
    res = collections.Counter()
    waiting = {}                    # unit -> exit seed tuple of its last decision
    for tag, d in lines:
        if tag == "AID":
            waiting.pop(d["u"], None)       # another decision of the unit ends the search
            continue
        if tag == "AIX" and d.get("k") in ai and d.get("s"):
            waiting[ai[d["k"]]["u"]] = skills.sd_parse(d["s"])
            continue
        o = obs_of(tag, d)
        if o and o[0] in waiting and o[1]:
            t = skills.sd_parse(o[1])
            k = skills.steps_between(waiting.pop(o[0]), t, 64)
            res["far" if k is None else k] += 1
    res["none"] = len(waiting)
    return res


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    tot = collections.Counter()
    for p in argv:
        r = scan(p)
        tot.update(r)
        print("H1 %s %s" % (os.path.basename(p), json.dumps({str(k): v for k, v in sorted(r.items(), key=lambda kv: str(kv[0]))})))
    print("H1STEPS %s" % json.dumps({str(k): v for k, v in sorted(tot.items(), key=lambda kv: str(kv[0]))}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

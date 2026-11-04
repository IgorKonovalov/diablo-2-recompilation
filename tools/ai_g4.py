#!/usr/bin/env python3
"""Plan 0052 Phase 2 case G4 (docs/findings/ai/0016-uber-event.md section 8): the G4 lines of tools/gdb/ai-g4.py in launch logs.

    python3 -I tools/ai_g4.py LAUNCH_LOG [LAUNCH_LOG ...]

Per log: the hits of each of the seven helper entries (a HELPER line each) and the highest hit count the live controls logged (a control
logs its 1st, 2nd, 4th, 8th ... hit, so the largest n printed is within a factor of two of the count). Exit 1 if a helper was hit or if no
control was live in a log. Stdlib only."""
import re
import sys


def main(paths):
    bad = 0
    tot_help, tot_ctl = {}, {}
    for p in paths:
        helpers, ctl, armed = {}, {}, False
        with open(p, errors="replace") as fh:
            for ln in fh:
                if ln.startswith("G4 armed"):
                    armed = True
                m = re.match(r"G4 (HELPER|control) (0x[0-9A-F]{8}) n=(\d+)", ln)
                if m:
                    d = helpers if m.group(1) == "HELPER" else ctl
                    d[m.group(2)] = max(d.get(m.group(2), 0), int(m.group(3)))
        print("G4LOG %s armed=%s helper_hits=%d controls=%s" % (p.split("/")[-1], armed, sum(helpers.values()),
              ",".join("%s:%d" % kv for kv in sorted(ctl.items())) or "-"))
        for k, v in helpers.items():
            tot_help[k] = tot_help.get(k, 0) + v
        for k, v in ctl.items():
            tot_ctl[k] = tot_ctl.get(k, 0) + 1
        if not armed or helpers or not ctl:
            bad = 1
    print("G4SUM logs=%d helper_hits=%d controls_live_in_logs=%s" % (len(paths), sum(tot_help.values()),
          ",".join("%s:%d" % kv for kv in sorted(tot_ctl.items()))))
    return bad


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) if len(sys.argv) > 1 else 2)

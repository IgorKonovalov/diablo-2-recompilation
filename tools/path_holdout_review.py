#!/usr/bin/env python3
"""The figures of the lane/p54c review (plan 0054 Phase 2) on run:2026-11-04-path-2's kept logs. Reads; changes nothing, and tools/path.py stays frozen.

    python3 -I tools/path_holdout_review.py ablate LOG... > ablate.txt   each of O1, T1, C1..C3 off in a copy of tools/path.py's source, the "code" pass of `grid`
    python3 -I tools/path_holdout_review.py eleven LOG... > eleven.txt   the 11 wrong plans: flags, self, target, held reservations, units within 4 of the decisive cell, L1 and COR lines near

Neither is a rule: no pass here adds a rule, so nothing here is a refit of the hold-out.
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

OFF = {
    "O1": "if code and not object_marked(u, tables[0]):",
    "T1": 'if code and sx and tgt and uid == tgt[1] and tgt[0] == 2 and plan.pln["fl"] & 0x800:',
    "C1..C3": "if code and t == 1 and mode in (0, 12):",
}
PASSES = """passes = [("frozen, units' own marks", None, False), ("frozen, the corpse reading", None, True), ("code rules O1, C1..C3, T1", "code", False), ("code rules with W1", "code+w1", False)]"""
ONLY = 'passes = [("code without one rule", "code", False)]'
L1PASS = 'passes.append(("code rules with W1 and L1", "code+w1+l1", False))'

# (case, k): the decisive cell of the `code rules with W1 and L1` pass's REST lines
ELEVEN = {
    ("k5-bar-cotd", 3291): (5596, 5443), ("k5-bar-stony", 1883): (5322, 5148), ("k5-bar-river", 4079): (7793, 6124), ("k5-bar-river", 4103): (7793, 6124),
    ("k5-bar-halls", 333): (15271, 8128), ("k5-bar-halls", 357): (15271, 8128), ("k5-pal-river", 1723): (7796, 5992), ("k5-pal-river", 2368): (7795, 5996),
    ("k5-pal-river", 2383): (7795, 5996), ("k5-bar-stony-2", 3149): (5191, 5095), ("k5-bar-river-2", 3622): (7798, 5988),
}


def ablate(logs):
    src = open(os.path.join(HERE, "path.py")).read()
    for name, old in OFF.items():
        assert src.count(old) == 1 and src.count(PASSES) == 1 and src.count(L1PASS) == 1, name
        s = src.replace(old, "if False:").replace(PASSES, ONLY).replace(L1PASS, "pass")
        mod = {"__name__": "path_off", "__file__": os.path.join(HERE, "path.py")}
        sys.modules["path_off"] = type(sys)("path_off")
        sys.modules["path_off"].__dict__.update(mod)
        exec(compile(s, "path_off", "exec"), sys.modules["path_off"].__dict__)
        print("%s off:" % name)
        sys.modules["path_off"].grid_report(logs, sys.stdout)
        sys.stdout.flush()


def near(u, c):
    x, y = (u[4], u[5]) if u[0] in (0, 1, 3) else (u[3], u[4])
    return abs(x - c[0]) <= 4 and abs(y - c[1]) <= 4


def eleven(logs):
    import path as P
    for log in logs:
        for (cs, k), c in ELEVEN.items():
            if not log.endswith("-%s.log" % cs):
                continue
            for g in P.parse(log):
                P.player_arrivals(g)
                P.reserved_landings(g)
                tags = [("M", e) for e in g.l1m] + [("U", e) for e in g.l1u]
                for p in g.plans:
                    if p.k != k or not p.plc:
                        continue
                    n = p.plc["n"]
                    print("%s k=%d type=%s fl=%x self=%s tgt=%s cell=%s held=%s" % (cs, k, p.ty, p.pln["fl"], p.plc["self"], p.plc.get("tgt"), c, p.l1))
                    print("  units", [u for u in p.plc["u"] if len(u) > 5 and near(u, c)])
                    for t, e in sorted(tags, key=lambda v: v[1]["n"]):
                        if n - 60 <= e["n"] <= n + 25:
                            print("  L1%s n=%d (plan n=%d) site=%08x player=%s at (%d, %d)" % (t, e["n"], n, e["site"], e["u"][3:], e["x"], e["y"]))
                    for e in g.cor:
                        if n - 300 <= e["n"] <= n + 25 and abs(e["x"] - c[0]) <= 3 and abs(e["y"] - c[1]) <= 3:
                            print("  COR n=%d site=%08x u=%s side=%s arg=%s" % (e["n"], e["site"], e["u"], e["side"], e["arg"]))


def main():
    cmd, logs = sys.argv[1], sorted(sys.argv[2:])
    {"ablate": ablate, "eleven": eleven}[cmd](logs)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Plan 0056 Phase 4: the pilot's figures recounted from the kept records of run:2026-11-03-ai.

Reads workspace/logs/ai only and prints: the wall of every launch (marks), the batches' wall (status files), the gaps
between launches of one batch, launch to ready, the switches, the distinct first boundaries and the distinct logged
call sequences per tier AI, the same in pairs of long and short cases, and tools/ai.py check over the logs without the
four cases that followed the town cases in launch 5202.

    python3 -I tools/pilot0056_recount.py > workspace/logs/p56/phase4-recount.txt
"""
import collections
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai  # noqa: E402

LOGS = os.path.join(HERE, "..", "workspace", "logs", "ai")
RUN = "2026-11-03-ai-s2"
TIER = [2, 6, 9, 13, 20, 21, 22, 28, 29, 30, 34, 35, 37, 61, 64, 67, 89, 125]
AFTER_TOWN = ("a5-glacial", "a1-cloister", "a1-catacombs", "a3-durance")
KEPT = 31


def marks(path):
    with open(path) as fh:
        return [ln.rstrip("\n").split("\t") for ln in fh][1:]


def walls():
    rows = []
    for path in glob.glob(os.path.join(LOGS, "*.marks.tsv")):
        m = marks(path)
        t = [float(x[2]) for x in m]
        ready = [float(x[2]) for x in m if x[1] == "ready"]
        rows.append((min(t), max(t), os.path.basename(path)[:-len(".marks.tsv")], ready[0] - t[0] if ready else None, m))
    rows.sort()
    kept = dev = failed = 0.0
    prev = None
    gaps, to_ready, switches = [], [], []
    for t0, t1, name, rdy, m in rows:
        wall = t1 - t0
        kind = "failed-try" if "failed-try" in name else "dev" if name.startswith("dev") else "kept"
        kept += wall if kind == "kept" else 0
        failed += wall if kind == "failed-try" else 0
        dev += wall if kind == "dev" else 0
        print("LAUNCH %-48s %-10s wall=%7.1f s ready=%s cases=%d" % (
            name, kind, wall, "%.1f" % rdy if rdy is not None else "-", sum(1 for x in m if x[1] == "start")))
        if kind != "dev":
            to_ready.append(rdy)
            if prev is not None and t0 - prev < 5:
                gaps.append(t0 - prev)
            prev = t1
            switches += [float(x[4].split()[1]) for x in m if x[1] == "ready" and x[4].startswith("switch")]
    batch = 0.0
    for path in sorted(glob.glob(os.path.join(LOGS, RUN + "*.status.json"))):
        with open(path) as fh:
            batch += json.load(fh)["wall"]
    print("WALL kept launches %.1f s = %.2f min, %.2f per kept case" % (kept, kept / 60, kept / 60 / KEPT))
    print("WALL batches (status) %.1f s = %.2f min, %.2f per kept case" % (batch, batch / 60, batch / 60 / KEPT))
    print("WALL development %.1f s = %.2f min; failed try %.1f s" % (dev, dev / 60, failed))
    every = kept + dev + failed
    print("WALL all 19 launches %.1f s = %.2f min, %.2f per kept case" % (every, every / 60, every / 60 / KEPT))
    print("WALL first launch to last end %.2f min" % ((rows[-1][1] - rows[0][0]) / 60))
    print("GAP end of a launch to the next launch in a batch (stop, restore, aside, install): n=%d, %.2f to %.2f s"
          % (len(gaps), min(gaps), max(gaps)))
    print("READY launch to ready: n=%d, %.1f to %.1f s, mean %.2f" % (
        len(to_ready), min(to_ready), max(to_ready), sum(to_ready) / len(to_ready)))
    print("SWITCH n=%d, %.1f to %.1f s, mean %.2f" % (
        len(switches), min(switches), max(switches), sum(switches) / len(switches)))


def first_boundary(dec, mods):
    ent = mods["_reg"].get(dec["aid"]["th"])
    b = ai.first_aib(dec, set(mods[ent[0]].OBSERVE)) if ent else (dec["aib"][0] if dec["aib"] else None)
    return (b["fn"], b["ra"]) if b else None


def separation(logs):
    mods = ai.load_mods()
    data = collections.defaultdict(list)
    for path in logs:
        case = re.sub(r".*-L\d+-", "", os.path.basename(path))[:-4]
        for d in ai.parse(path)["dec"]:
            data[d["aid"]["ai"]].append((case, first_boundary(d, mods), tuple((b["fn"], b["ra"]) for b in d["aib"])))
    for row in TIER:
        seen, last = set(), 0
        for i, (_, f, _q) in enumerate(data[row]):
            if f not in seen:
                seen.add(f)
                last = i + 1
        print("SEP row %3d decisions=%5d first=%d last_new_at=%d seqs=%d cases=%d" % (
            row, len(data[row]), len(seen), last, len({q for _, _, q in data[row]}), len({c for c, _, _ in data[row]})))
    for long_, short in (("a4-cotd-long", "a4-cotd"), ("a4-river-long", "a4-river"), ("a2-halls-long", "a2-halls")):
        for row in TIER:
            a = [x for x in data[row] if x[0] == long_]
            b = [x for x in data[row] if x[0] == short]
            if a and b:
                print("PAIR %s row %d long: %d decisions, %d first; short: %d decisions, %d first" % (
                    long_, row, len(a), len({x[1] for x in a}), len(b), len({x[1] for x in b})))


def main():
    walls()
    logs = sorted(glob.glob(os.path.join(LOGS, RUN + "-5*-L*-*.log")))
    print("LOGS", len(logs))
    separation(logs)
    rest = [p for p in logs if not any(("5202-L2-" + c + ".log") in p for c in AFTER_TOWN)]
    text, r = ai.run_check(rest, None)
    print("EXCL logs=%d decisions=%d mismatches=%d" % (len(rest), r["decisions"], r["mismatches"]))
    for ln in text.splitlines():
        if ln.startswith("ROW ") and int(ln.split()[1]) in TIER:
            print("EXCL", " ".join(ln.split()))
    return 0


if __name__ == "__main__":
    sys.exit(main())

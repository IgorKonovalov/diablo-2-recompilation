"""sim/frame's worked example, printed from the kept log (the `lane/s55` review): frame 1961 of window 5503 #1 and the
missiles' first readings in frame 1962. Read-only; stdlib only; no game. Exit 1 if any step does not hold.

    python3 -I tools/frame_example.py workspace/logs/frame/2026-11-04-frame2-s1-5503-maze1.log > OUT
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frame_window as fw  # noqa: E402

FRAME = 1961
SEED_SITES = (0x00552E31, 0x00552E9F)   # UnitSeedInit+0x41, ItemSeedInit+0xF
INIT_HIGH = 0x29A


def parse(s):
    low, high = s.split(":")
    return int(low, 16), int(high, 16)


def fmt(t):
    return "%08x:%08x" % t


def main(path):
    rows = []
    with open(path, errors="replace") as f:
        for ln in f:
            kind, _, rest = ln.partition(" ")
            if kind in ("FT0", "FT1", "UE0", "UE1", "XS", "QF", "KD") and rest.startswith("{"):
                d = json.loads(rest)
                if d.get("fr") in (FRAME, FRAME + 1):
                    rows.append((kind, d))
    bad = 0
    gs = None
    steps = 0
    made = []          # (missile id, game seed after the step that made it)
    pending = None
    first = {}
    for kind, d in rows:
        if d["fr"] == FRAME:
            if kind == "FT0":
                gs = parse(d["gs"])
                print("FT0 %d game seed %s" % (FRAME, fmt(gs)))
            elif kind == "KD":
                print("KD type %d id %d" % (d["ty"], d["id"]))
            elif kind == "XS" and d["site"] in SEED_SITES and d["low"] == gs[0]:
                gs = fw.step(gs)
                steps += 1
                pending = gs
                print("XS 0x%08X low %08x -> %s, step %d" % (d["site"], d["low"], fmt(gs), steps))
            elif kind == "QF" and d.get("ut") == 3 and pending is not None:
                made.append((d["id"], pending))
                pending = None
            elif kind == "UE0" and "gs" in d and parse(d["gs"]) != gs:
                print("MISMATCH at UE0 id %d: logged %s, kept %s" % (d["id"], d["gs"], fmt(gs)))
                bad += 1
            elif kind == "UE1" and parse(d["gs"]) != gs:
                print("MISMATCH at UE1 id %d: logged %s, kept %s" % (d["id"], d["gs"], fmt(gs)))
                bad += 1
            elif kind == "FT1":
                ok = parse(d["gs"]) == gs
                bad += 0 if ok else 1
                print("FT1 %d game seed %s, %d steps from FT0, %s" % (FRAME, d["gs"], steps, "equal" if ok else "MISMATCH"))
            if kind == "UE1" and d["id"] in (456, 1) and parse(d["gs"]) == gs:
                print("UE1 id %d exit game seed %s, %d steps from FT0" % (d["id"], d["gs"], steps))
        elif kind == "UE0" and d.get("ty") == 3 and d["id"] not in first:
            first[d["id"]] = (len(first), parse(d["us"]))
    print("missiles made in frame %d: %d, ids %d to %d" % (FRAME, len(made), made[0][0], made[-1][0]))
    for mid, after in made:
        want = (after[0], INIT_HIGH)
        got = first.get(mid, (None, None))[1]
        if got != want:
            print("MISMATCH missile %d: first reading %s, Init of the step's low %s" % (mid, got and fmt(got), fmt(want)))
            bad += 1
    print("first readings equal to Init of the step's low: %d of %d" % (len(made) - sum(1 for m, a in made if first.get(m, (0, None))[1] != (a[0], INIT_HIGH)), len(made)))
    for mid in (made[0][0], made[-1][0]):
        print("missile %d: first reading %s, made by the step to %s" % (mid, fmt(first[mid][1]), fmt(dict(made)[mid])))
    print("frame %d's missile walk starts: %s" % (FRAME + 1, " ".join(str(m) for m, _ in sorted(((m, v[0]) for m, v in first.items()), key=lambda x: x[1])[:5])))
    print("mismatches %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

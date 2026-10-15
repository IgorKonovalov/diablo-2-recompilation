"""Plan 0026 reading check (Act III), now a thin driver over tools/drlg.py: replay the jungle link layout
0x00677880 / 0x00678910 on the act seed (drlg.act_links_a3), then the Act III outdoor window OD0 -> OD1 (0x0067F450,
drlg.Outdoor) for the logged levels 76-83, and compare: the level rectangle, the OD1 seed, and the preset placement
list (def, rect, file index) that OutdoorRoomsCreate logs (PIC / PIO) after OD1.

Usage: python3 -I tools/jungle_replay.py <excel-dir> <exe> <log>... [--seed=N]

The jungle layout and the generators have one implementation, in tools/drlg.py. Evidence:
docs/findings/drlg/0008-outdoor.md. Acts I, II, IV and V (and Act III with out rooms): tools/outdoor_replay.py.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drlg  # noqa: E402

EXCEL, EXE = sys.argv[1].rstrip("/"), sys.argv[2]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(EXCEL)))
drlg.load_outdoor(ROOT, EXE)
from drlg import COV, Act, Outdoor, Seed, act_links  # noqa: E402


def parse_seed(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def act3(ms):
    A = Act(2, ms, 0)
    act_links(A)
    return A


def main():
    logs = [a for a in sys.argv[3:] if not a.startswith("--")]
    for ms in [int(a.split("=")[1]) for a in sys.argv[3:] if a.startswith("--seed=")]:
        A = act3(ms)
        print("seed %d: jungle layout act-seed steps %d (restarts %d)" % (ms, A.jungle_steps, A.jungle_restarts))
    bad = tot = 0
    for path in logs:
        head = open(path).readline()
        ms = int(head.split("seed=")[1].split()[0])
        A = act3(ms)
        print("%s: map seed %d, act base %d, bit474 %d, jungle steps %d, restarts %d" % (
            os.path.basename(path), ms, A.base, A.bit474, A.jungle_steps, A.jungle_restarts))
        ev = [(ln.split(" ", 1)[0], json.loads(ln.split(" ", 1)[1])) for ln in open(path, errors="replace")
              if ln[:4] in ("LC0 ", "OD0 ", "OD1 ", "PIC ", "PIO ", "LI1 ")]
        for i, (t, d) in enumerate(ev):
            if t == "LC0" and d["id"] == 75 and d["base"] != A.base:
                print("  act base mismatch", d["base"])
                bad += 1
            if t != "OD0" or not (76 <= d["id"] <= 83):
                continue
            lid, lvp = d["id"], d["level"]
            o = Outdoor(A, lid, Seed(*parse_seed(d["seed"])))
            o.run()
            j = [k for k in range(i, len(ev)) if ev[k][0] == "OD1" and ev[k][1]["level"] == lvp][0]
            od1 = ev[j][1]
            got = o.seed.fmt()
            pl = []
            cur = None
            j += 1
            while j < len(ev) and not (ev[j][0] == "LI1" and ev[j][1]["level"] == lvp):
                t2, d2 = ev[j]
                if t2 == "PIC" and d2["level"] == lvp:
                    cur = [d2["def"], d2["rect"][0], d2["rect"][1]]
                elif t2 == "PIO" and cur is not None:
                    pl.append(tuple(cur + [d2["idx"]]))
                    cur = None
                j += 1
            exp = [it[1:5] for it in o.items() if it[0] == "P"]
            ok = got == od1["seed"] and exp == pl
            tot += 1
            bad += not ok
            print("  level %d rect %s: OD1 %s %s, presets %d/%d %s" % (
                lid, tuple(A.rect[lid][:2]), got, "ok" if got == od1["seed"] else "!= " + od1["seed"], len(exp), len(pl),
                "ok" if exp == pl else "MISMATCH"))
            if exp != pl:
                for a, b in zip(exp, pl):
                    print("    ", a, b, "" if a == b else "<--")
    print("windows %d, mismatches %d" % (tot, bad))
    print(dict(COV))


main()

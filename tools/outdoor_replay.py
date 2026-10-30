"""Plan 0026 reading check, now a thin driver over tools/drlg.py: replay the outdoor window OD0 -> OD1
(sub_00675360_OutdoorLevelBuild's act generator, up to sub_006750F0_OutdoorRoomsCreate) for every logged outdoor level
of the five acts, with the act link builder (Acts I, II, IV, V) or the jungle layout (Act III) modelled for the level
rectangles, the level links, the border-adjacency lists and the outdoor flags the window reads. Compares the seed at
OD1, and the full list of what OutdoorRoomsCreate makes after OD1 (preset anchors: def, rect, file index, grid0 flags;
out rooms: rect).

Usage: python3 -I tools/outdoor_replay.py <merged-root> <exe> <log>... [-v] [--no-a3]
The generators and the link layouts have one implementation, in tools/drlg.py (Outdoor, Act, act_links).
Evidence: docs/findings/drlg/0008-outdoor.md.
"""
import collections, json, os, sys

VERBOSE = "-v" in sys.argv
NO_A3 = "--no-a3" in sys.argv
ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
ROOT, EXE = ARGS[0].rstrip("/"), ARGS[1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drlg            # noqa: E402

drlg.load_outdoor(ROOT, EXE)
from drlg import COV, Act, Fatal, Outdoor, Seed, act_links  # noqa: E402


# ================================================================ logs
def log_windows(path):
    """Per OD0: level ptr, id, seed0, seed1, and the OutdoorRoomsCreate output up to LI1 (anchors and out rooms)."""
    ev = []
    for l in open(path, errors="replace"):
        t, _, js = l.partition(" ")
        if t in ("OD0", "OD1", "PRC", "RL", "LI1", "LC0"):
            try:
                ev.append((t, json.loads(js)))
            except ValueError:
                pass
    out = []
    for i, (t, d) in enumerate(ev):
        if t != "OD0":
            continue
        lv = d["level"]; w = dict(id=d["id"], seed0=d["seed"], seed1=None, items=[], level=lv)
        for t2, d2 in ev[i + 1:]:
            if d2.get("level") != lv:
                continue
            if t2 == "OD1": w["seed1"] = d2["seed"]
            elif t2 == "PRC": w["items"].append(("P", d2["def"], d2["prect"][0], d2["prect"][1], d2["idx"], d2["flags"]))
            elif t2 == "RL" and d2["type"] == 1: w["items"].append(("R", d2["rect"][0], d2["rect"][1], d2["f28"]))
            # (RL logs room +0x28 at LevelRoomLink, before OutRoomCreate's grid0 is applied: compared as rect only)
            elif t2 == "LI1": break
        rs = [it for it in w["items"] if it[0] == "R"]
        w["client"] = bool(rs) and all(it[3] & 0x40000 for it in rs)
        COV["out room f28 at link (non-client) != 0"] += sum(1 for it in rs if it[3] & ~0x40000)
        # the client copy's out rooms carry room +0x28 bit 0x40000 (set by OutRoomCreate for the client; not a grid0 bit)
        if w["client"]:
            its = []
            for it in w["items"]:
                if it[0] == "R":
                    COV["client out room with 0x40000" if it[3] & 0x40000 else "client out room without 0x40000"] += 1
                its.append(it)
            w["items"] = its
        w["items"] = [it[:3] if it[0] == "R" else it for it in w["items"]]
        out.append(w)
    return out, ev


def log_meta(path):
    head = open(path).readline()
    ms = int(head.split("seed=")[1].split()[0])
    n = os.path.basename(path)
    diff = 2 if "hell" in n else 1 if "nightmare" in n else 0
    return ms, diff


def main():
    logs = ARGS[2:]
    tot = bad = 0
    per = collections.Counter(); perbad = collections.Counter()
    seen = set()
    for path in logs:
        ms, diff = log_meta(path)
        wins, ev = log_windows(path)
        acts = {}
        for w in wins:
            lid = w["id"]
            a = drlg.LV[lid]["act"]
            if a == 2 and NO_A3:
                continue
            key = (ms, diff, lid, w["seed0"])
            dup = key in seen
            seen.add(key)
            if a not in acts:
                A = Act(a, ms, diff)
                act_links(A)
                acts[a] = A
            A = acts[a]
            ok, msg = run_window(A, lid, w)
            if dup and ok and not VERBOSE:
                continue
            tot += 1; bad += not ok
            per[lid] += 1; perbad[lid] += not ok
            print("%s level %d seed %s: %s" % (os.path.basename(path), lid, w["seed0"], "ok" if ok else "MISMATCH " + msg))
    print("windows %d, mismatches %d" % (tot, bad))
    print("per level:", {k: (per[k], perbad[k]) for k in sorted(per)})
    print(dict(COV))


def run_window(A, lid, w):
    r = A.rect.get(lid)
    xs = [it[2] if it[0] == "P" else it[1] for it in w["items"]]
    ys = [it[3] if it[0] == "P" else it[2] for it in w["items"]]
    lr = (min(xs), min(ys)) if xs else None
    if r is None:
        return False, "no rect"
    if lr and (lr[0] < r[0] or lr[1] < r[1] or lr[0] >= r[0] + r[2] or lr[1] >= r[1] + r[3]):
        return False, "rect %s, logged rooms start %s" % (r, lr)
    try:
        O = Outdoor(A, lid, Seed(*[int(x, 16) for x in w["seed0"].split(":")]))
        O.run()
    except NotImplementedError as e:
        return False, "not modelled: %s" % e
    except Fatal as e:
        return False, "fatal %s" % e
    got = O.seed.fmt()
    exp = O.items()
    if got != w["seed1"]:
        msg = "OD1 %s, model %s; " % (w["seed1"], got)
    else:
        msg = ""
    if exp != w["items"]:
        n = next((k for k in range(min(len(exp), len(w["items"]))) if exp[k] != w["items"][k]), min(len(exp), len(w["items"])))
        msg += "items %d/%d, first diff at %d: model %s log %s" % (len(exp), len(w["items"]), n,
                                                                  exp[n] if n < len(exp) else None, w["items"][n] if n < len(w["items"]) else None)
    return msg == "", msg



if __name__ == "__main__":
    main()

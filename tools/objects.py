"""Room-seed accounting of the objects window, checked against runtime logs (plan 0023 Phase 1).

Usage:
  python3 -I tools/objects.py window <run.log> [...] [--excel DIR] [-v]

<run.log> is any log written by tools/d2run.py with tools/gdb/mon-spawn.gdb, collision.gdb or mon-special.gdb: they
log the room seed (rs, low:high) and game seed (gs) after each out-of-scope call of the room driver, RW1 (wanderer
tick) .. RW4 (object population). Tables are the .bin files the game loads (levels, objgroup, objects), decoded with
tools/excel_layouts.py, from --excel (default workspace/merged/data/global/excel).

The model is docs/findings/objects/0001-object-population.md, written from the code:

  * RW2 -> RW3 is the inactive-unit restore: on a first activation it must leave the room and game seed unchanged.
  * RW3 -> RW4 is sub_00552610_RoomObjectsPopulate. Gate closed (town, room flags 0x30000, no population level, the
    preset test): no room-seed draw. Gate open: for each Levels slot k = 0..7 one draw r = low % 100; when the forced
    health-shrine rule holds, r becomes 100 for a slot whose ObjGrp g has Objects[g].SubClass != 0; the slot passes
    when g != 0 and r <= ObjPrb[k]; then one draw r2 = low % 100 and the first member i (ID[i] != 0, in order) with
    r2 < PROB[0] + .. + PROB[i] and Gore <= 2 gets its PopulateFn. Room-seed draws inside the handlers: PopulateFn 2
    (shrine) 1 + 2a, PopulateFn 8 (well) 0 (cap) or 1 + 2a, PopulateFn 9 (trap) 1; the other handlers draw the object
    region seed (game +0x10F0), which the logs do not carry. InitFn 46 (object 369) spawns monsters on the room seed
    and is a wildcard.
  * The unknowns (gate result, forced flag, placement attempts a, cap state, InitFn 46's draws) are enumerated; a room
    passes when exactly the logged RW4 seed is reached. "exact" rooms needed no unknown besides the gate.

The last line is a summary with the counts. Stdlib only.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from obj_survey import decode  # noqa: E402

M = 0x6AC690C5


def step(s):
    v = s[0] * M + s[1]
    return (v & 0xFFFFFFFF, v >> 32)


def parse_seed(t):
    a, b = t.split(":")
    return (int(a, 16), int(b, 16))


def solve(s0, s1, lv, groups, objs, forced):
    """All ways the slot loop can turn s0 into s1; each is (branched, trace)."""
    sols = []

    def run(s, k, branched, trace):
        if k == 8:
            if s == s1:
                sols.append((branched, trace))
            return
        s = step(s)
        r = s[0] % 100
        g, p = lv["ObjGrp%d" % k], lv["ObjPrb%d" % k]
        if forced and objs[g]["SubClass"] != 0:
            r = 100
        if g == 0 or r > p:
            return run(s, k + 1, branched, trace)
        s = step(s)
        r2 = s[0] % 100
        gr = groups[g]
        cum, oid, fn = 0, None, None
        for i in range(8):
            o = gr["ID%d" % i]
            if o == 0:
                break
            cum += gr["PROB%d" % i]
            if r2 < cum and objs[o]["Gore"] <= 2:
                oid, fn = o, objs[o]["PopulateFn"]
                break
        tr = trace + [(k, g, oid, fn)]
        if oid is not None and objs[oid]["InitFn"] == 46:
            t = s
            for e in range(800):
                run(t, k + 1, True, tr + [("init46", e)])
                t = step(t)
            return
        if fn == 2:
            t = step(s)
            for a in range(151):
                run(t, k + 1, True, tr + [("shrine", a)])
                t = step(step(t))
            return
        if fn == 8:
            run(s, k + 1, True, tr + [("wellcap",)])
            t = step(s)
            for a in range(6):
                run(t, k + 1, True, tr + [("well", a)])
                t = step(step(t))
            return
        if fn == 9:
            s = step(s)
        return run(s, k + 1, branched, tr)

    run(s0, 0, False, [])
    return sols


def cmd_window(argv):
    excel, verbose, logs = "workspace/merged/data/global/excel", False, []
    it = iter(argv)
    for a in it:
        if a == "--excel":
            excel = next(it)
        elif a == "-v":
            verbose = True
        else:
            logs.append(a)
    levels, groups, objs = decode(excel, "levels"), decode(excel, "objgroup"), decode(excel, "objects")
    st = dict(logs=len(logs), rooms=0, restore_checked=0, restore_moved=0, closed=0, closed_town=0, exact=0,
              branched=0, forced=0, fail=0, slot_passes=0, member_none=0, shrine=0, well=0, trap=0, init46=0,
              other_handlers=0)
    towns = {1, 40, 75, 103, 109}
    for path in logs:
        rw = {}
        for line in open(path, errors="replace"):
            if not line.startswith("RW"):
                continue
            tag, js = line.split(" ", 1)
            try:
                d = json.loads(js)
            except ValueError:
                continue
            rw[tag] = d
            if tag == "RW3" and "RW2" in rw and rw["RW2"]["room"] == d["room"]:
                st["restore_checked"] += 1
                if (rw["RW2"]["rs"], rw["RW2"]["gs"]) != (d["rs"], d["gs"]):
                    st["restore_moved"] += 1
                    print("RESTORE-MOVED", os.path.basename(path), d["room"])
            if tag != "RW4" or "RW3" not in rw or rw["RW3"]["room"] != d["room"]:
                continue
            st["rooms"] += 1
            s0, s1, lid = parse_seed(rw["RW3"]["rs"]), parse_seed(d["rs"]), d["lid"]
            if s0 == s1:
                st["closed"] += 1
                st["closed_town"] += lid in towns
                continue
            if lid in towns:
                st["fail"] += 1
                print("FAIL town window drew", os.path.basename(path), d["room"], lid)
                continue
            sols = solve(s0, s1, levels[lid], groups, objs, False)
            if not sols:
                sols = solve(s0, s1, levels[lid], groups, objs, True)
                if sols:
                    st["forced"] += 1
                    if verbose:
                        print("FORCED", os.path.basename(path), d["room"], lid)
            if not sols:
                st["fail"] += 1
                print("FAIL", os.path.basename(path), d["room"], "lid", lid, rw["RW3"]["rs"], d["rs"])
                continue
            branched, trace = sols[0]
            st["branched" if branched else "exact"] += 1
            for t in trace:
                if len(t) == 4:
                    st["slot_passes"] += 1
                    if t[2] is None:
                        st["member_none"] += 1
                    elif objs[t[2]]["InitFn"] == 46:
                        st["init46"] += 1
                    elif t[3] == 2:
                        st["shrine"] += 1
                    elif t[3] == 8:
                        st["well"] += 1
                    elif t[3] == 9:
                        st["trap"] += 1
                    else:
                        st["other_handlers"] += 1
            if verbose:
                print("ROOM", os.path.basename(path), d["room"], lid, "exact" if not branched else "branched", trace)
    print("objects-window: " + " ".join("%s=%d" % kv for kv in st.items()))
    return 1 if st["fail"] or st["restore_moved"] else 0


def main(argv):
    if len(argv) < 3 or argv[1] != "window":
        print(__doc__)
        return 2
    return cmd_window(argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))

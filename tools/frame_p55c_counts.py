"""The `lane/p55c` review's reading of run:2026-11-04-frame2's kept logs (plan 0055 Phase 2b). Read-only; stdlib; no game.

    python3 -I tools/frame_p55c_counts.py workspace/logs/frame workspace/install/app/game.exe > OUT

Every count the review and frame/0007 § Review cite: the outcome mix of the counted windows, what the order test separates, what the
line volume is made of, the reader's alternatives, the steps on no chained seed, the KD segments, the touch rows' extents, the
modded monsters per window, the hooks not reached, and the shared-seed pairs of every frame2 and pilot log. The reader's mutation (one
in-tick XS line dropped, seed 55) is seeded, so the output is the same each run. The dev logs are read for the volume and the pairs
only and are named as dev.
"""
import bisect
import collections
import csv
import glob
import json
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import frame_window as fw  # noqa: E402
import frame_xs as fx  # noqa: E402

COUNTED = {("5501-pack1", 3486), ("5503-maze1", 1897), ("5503-maze1", 7942), ("5505-maze1", 7942), ("5507-mazeh", 2094)}
CLIENT_FN = (0x00473090, 0x00473240)      # the unnamed client function beside sub_00473910_WeatherTick (five draws per call)
CLIENT_SITES = (0x00473111, 0x004731FE)   # its two inlined sites; the other three are RNG_RangeOffset with `ra` inside it
OPENS = ("UE0", "RU0", "MSG0", "TQ0", "SV0")
CLOSES = ("UE1", "RU1", "MSG1", "TQ1", "SV1")


def symbols():
    rows = []
    with open(os.path.join(HERE, "..", "re", "symbols.csv")) as f:
        for r in csv.DictReader(f):
            if r["kind"] == "func":
                rows.append((int(r["address"], 16), r["name"]))
    rows.sort()
    return rows


SYMS = symbols()
ADDR = [a for a, _ in SYMS]


def fname(a):
    return SYMS[bisect.bisect_right(ADDR, a) - 1][1]


def tag_of(path):
    return re.sub(r"^.*?-s1-", "", os.path.basename(path))[:-4]


def volume(path):
    """-> per window of the raw log: frames, lines, UE0, XS, in-tick XS, the client function's XS."""
    out, d, tick = [], None, False
    with open(path) as f:
        for ln in f:
            t = ln.split(" ", 1)[0]
            if t == "WIN":
                d = collections.Counter()
                d["start"] = json.loads(ln[4:])["start"]
                out.append(d)
                tick = False
            elif t == "WEND":
                d = None
            elif d is not None:
                d["lines"] += 1
                if t == "FT0":
                    d["fr"] += 1
                    tick = True
                elif t == "FT1":
                    tick = False
                elif t == "UE0":
                    d["ue0"] += 1
                elif t == "XS":
                    o = json.loads(ln[3:])
                    d["xs"] += 1
                    d["xs_tick"] += tick
                    if o["site"] in CLIENT_SITES or CLIENT_FN[0] <= o.get("ra", 0) < CLIENT_FN[1]:
                        d["client_fn"] += 1
    return out


def pairs(w):
    """-> (G-moving top-level events, the frames with two or more different units among them as (a, b) of consecutive such events)."""
    stack, fr = [], collections.defaultdict(list)
    for _n, t, o in w["lines"]:
        if t in OPENS:
            stack.append((t, o, o.get("gs"), not stack))
        elif t in CLOSES and stack:
            tg, a, g0, top = stack.pop()
            if tg == "UE0" and top and g0 != o.get("gs"):
                fr[a["fr"]].append((a["ty"], a["id"], a["kind"], a["lst"]))
    found = []
    for k, v in sorted(fr.items()):
        for a, b in zip(v, v[1:]):
            if a[:2] != b[:2]:
                found.append((k, a, b))
    return sum(len(v) for v in fr.values()), found


def extents(image, hits, P):
    """How far a row's extent (to the next symbol) runs past its function: the first int3 padding after its start is read as the end.
    A location is an LCG site, or the return address of a call to one of rng/0001's six primitives."""
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--start-address=0x400000", "--stop-address=0x700000", image],
                         capture_output=True, text=True).stdout
    ins = []
    for ln in out.split("\n"):
        m = re.match(r"\s+([0-9a-f]+):\t[0-9a-f ]+\t(.*)", ln)
        if m:
            ins.append((int(m.group(1), 16), m.group(2).strip()))
    addr = [a for a, _ in ins]
    with open(os.path.join(HERE, "gdb", "lcg-sites.txt")) as f:
        sites = {int(m, 16) for m in re.findall(r"^0x[0-9a-fA-F]{6,8}", f.read(), re.M)}
    prims = {0x0045C370, 0x0045C390, 0x0045C3E0, 0x00472210, 0x00472240, 0x00472280}
    locs = set(sites)
    for i, (_a, t) in enumerate(ins[:-1]):
        m = re.match(r"call\s+0x([0-9a-f]+)$", t)
        if m and int(m.group(1), 16) in prims:
            locs.add(ins[i + 1][0])
    locs = sorted(locs)
    P("locations: %d (sites %d)\n" % (len(locs), len(sites)))
    for name, rows in (("TOUCH", fw.TOUCH), ("PASSDRAW", fw.PASSDRAW)):
        tot, seen = collections.Counter(), set()
        for r in rows:
            for lo, hi in r.get("ranges", ()):
                if (lo, hi) in seen:
                    continue
                seen.add((lo, hi))
                i, j = bisect.bisect_left(addr, lo), bisect.bisect_left(addr, hi)
                end = next((ins[k + 1][0] for k in range(i, j - 1) if ins[k][1] == "int3" and ins[k + 1][1] != "int3"), None)
                inside = [a for a in locs if lo <= a < hi]
                past = [a for a in inside if end and a >= end]
                hit = [a for a in past if hits[a]]
                tot["extents"] += 1
                tot["locations"] += len(inside)
                tot["past"] += len(past)
                tot["locations_hit"] += sum(1 for a in inside if hits[a])
                tot["past_hit"] += len(hit)
                tot["steps_past"] += sum(hits[a] for a in hit)
                if past:
                    P("%s %s end %#x past %s hit %s\n" % (name, r["fn"][3:36], end, ",".join("%#x" % a for a in past[:6]),
                                                       {hex(a): hits[a] for a in hit}))
        P("%s totals %s\n" % (name, sorted(tot.items())))


def main():
    root = sys.argv[1]
    P = sys.stdout.write
    run_id = sys.argv[3] if len(sys.argv) > 3 else "2026-11-04-frame2"      # `lane/p55d`: the same reading of run:2026-11-04-frame3
    kept = sorted(glob.glob(os.path.join(root, run_id + "-s1-*.log")))
    dev = sorted(glob.glob(os.path.join(root, "dev-" + run_id + "-*.log")))
    pilot = sorted(glob.glob(os.path.join(root, "2026-11-04-frame-s1-*.log")))

    P("== volume (lines per frame; without the client function; in-tick XS only)\n")
    for p in kept + dev:
        for v in volume(p):
            n = max(v["fr"], 1)
            P("%-44s %5d lpf %.1f UE0/f %.1f XS/f %.1f tickXS/f %.1f client_fn %d lpf_without %.1f lpf_tick_only %.1f\n" % (
                os.path.basename(p)[:44], v["start"], v["lines"] / n, v["ue0"] / n, v["xs"] / n, v["xs_tick"] / n, v["client_fn"],
                (v["lines"] - v["client_fn"]) / n, (v["lines"] - v["xs"] + v["xs_tick"]) / n))

    T = collections.Counter()
    gmov, rk, kd_hist, kd_other, kd_site, cli_chained, unt_tick_nopair, unt_tick_open, unt_between = (
        collections.Counter() for _ in range(9))
    kinds, kinds_moved = collections.Counter(), collections.Counter()
    deflike = [r for r in fw.TOUCH if r["trigger"] in ("defender", "owner", "killev")]
    defhits = collections.Counter()
    allhits = collections.Counter()
    drop = collections.Counter()
    counted = []
    random.seed(55)
    for p in kept:
        ws, _o = fw.parse_log(p)
        tag = tag_of(p)
        for w in ws:
            is_c = (tag, w["start"]) in COUNTED
            stack, tick = [], False
            for _n, t, o in w["lines"]:
                if t == "FT0":
                    tick = True
                elif t == "FT1":
                    tick = False
                elif t == "XS":
                    loc = o.get("ra") or o["site"]
                    allhits[loc] += 1
                    if any(fw.row_has(r, loc) for r in deflike):
                        defhits[(fname(loc), "ty%s" % stack[-1][1].get("ty") if stack else "none")] += 1
                if t in OPENS:
                    stack.append((t, o, o.get("gs"), o.get("us"), not stack))
                elif t in CLOSES and stack:
                    tg, a, g0, u0, top = stack.pop()
                    if tg == "UE0" and is_c:
                        gm = g0 != o.get("gs")
                        um = bool(u0 and o.get("us") and u0 != o.get("us"))
                        T["ue0"] += 1
                        T["ue0_game"] += gm
                        T["ue0_own"] += um
                        T["ue0_none"] += not gm and not um
                        k = (a["ty"], a["kind"], a["lst"])
                        kinds[k] += 1
                        kinds_moved[k] += gm or um
                        if gm:
                            gmov[k] += 1
            if not is_c:
                continue
            counted.append((tag, w))
            x = fx.check_chain2(w)
            T["fails"] += len(x["fails"])
            T["altreads"] += len(x["altreads"])
            T["altreads_game"] += sum(1 for g, _n in x["altreads"] if g)
            T["altreads_max"] = max([T["altreads_max"]] + [n for _g, n in x["altreads"]])
            for k, v in x["entries"].items():
                T["entries_" + k] += v
            for k, v in x["firsts"].items():
                T["first_" + k] += v
            for k, v in x["cls"].items():
                T["cls_" + k] += v
            T["client"] += sum(x["client"].values())
            cli_chained.update({fname(k): v for k, v in x["client_chained"].items()})
            T["client_chained"] += sum(x["client_chained"].values())
            for (tk, op), v in x["untracked_where"].items():
                T["untracked_%s_%s" % ("tick" if tk else "between", "open" if op else "nopair")] += v
            for k in x["kds"]:
                kd_hist[k.get("gk")] += 1
                for a in k.get("sites") or []:
                    if a in fw.KILL_GAME:
                        kd_site[hex(a)] += 1
                    else:
                        kd_other[fname(a)] += 1
            # the game seed's true steps, from its readings
            prev = None
            for _n, t, o in w["lines"]:
                gs = o.get("gs") if isinstance(o, dict) else None
                if gs:
                    s = fw.sd(gs)
                    if prev is not None and s != prev:
                        c, cur = 0, prev
                        while cur != s and c < 20000:
                            cur, c = fw.step(cur), c + 1
                        T["game_true_steps"] += c
                    prev = s
            # the XS classes by place
            tick = False
            for _n, t, o in w["lines"]:
                if t == "FT0":
                    tick = True
                elif t == "FT1":
                    tick = False
                elif t == "XS":
                    T["xs_all"] += 1
                    T["xs_tick"] += tick
            # what the order test separates
            qf, qe, depth, last, ef, sl = {}, collections.defaultdict(list), 0, None, collections.defaultdict(list), collections.defaultdict(list)
            for _n, t, o in w["lines"]:
                if t == "QF" and o.get("ut") is not None:
                    qf[(o["ut"], o["id"], o["kind"])] = _n
                elif t == "QE" and o.get("ut") is not None:
                    qe[(o["ut"], o["asked"])].append((o["id"], o["kind"]))
                elif t == "FT0":
                    last = None
                if t in OPENS:
                    if t == "UE0" and depth == 0:
                        r = fw.RANK.get(o["ty"], (0, 0))[0 if o["lst"] == "ef" else 1]
                        if last is not None and last != r:
                            rk[(last, r)] += 1
                        last = r
                        if o["lst"] == "ef":
                            q = qf.get((o["ty"], o["id"], o["kind"]))
                            if q is not None:
                                ef[(o["fr"], o["ty"])].append((q, o["id"]))
                        else:
                            e = (o["id"], o["kind"])
                            if e in qe.get((o["ty"], o["fr"]), ()):
                                sl[(o["fr"], o["ty"])].append(e)
                    depth += 1
                elif t in CLOSES:
                    depth = max(0, depth - 1)
            for v in ef.values():
                for a, b in zip(v, v[1:]):
                    T["ef_adjacent"] += 1
                    T["ef_newest_first"] += a[0] > b[0]
                    T["ef_not_descending_guid"] += a[1] <= b[1]
                T["ef_frames_ge2"] += len(v) >= 2
            for v in sl.values():
                for a, b in zip(v, v[1:]):
                    T["slot_adjacent"] += 1
                    T["slot_same_unit"] += a[0] == b[0]
                    T["slot_not_ascending_guid"] += a[0] > b[0]
                T["slot_frames_ge2"] += len(v) >= 2
            # one in-tick XS dropped: does the reader see it
            idx, tk = [], False
            for i, (_n, t, _o) in enumerate(w["lines"]):
                if t == "FT0":
                    tk = True
                elif t == "FT1":
                    tk = False
                elif t == "XS" and tk:
                    idx.append(i)
            if idx:
                for _ in range(25):
                    i = random.choice(idx)
                    w2 = dict(w)
                    w2["lines"] = w["lines"][:i] + w["lines"][i + 1:]
                    drop[(tag, w["start"], "seen" if fx.check_chain2(w2)["fails"] else "not seen")] += 1
    P("\n== counted windows, totals\n")
    for k in sorted(T):
        P("%s=%d\n" % (k, T[k]))
    P("\n== UE0 by (type, kind, list): events, moved a seed\n")
    for k, v in kinds.most_common():
        P("%s %d %d\n" % (k, v, kinds_moved[k]))
    P("game-seed-moving UE0: %s\n" % gmov.most_common())
    P("rank transitions (adjacent top-level walks): %s\n" % sorted(rk.items()))
    P("\n== client steps with a chained low word: %s\n" % cli_chained.most_common())
    P("\n== KD: item-site counts %s; steps at the sites %s; other steps classed game in a segment %s\n" % (
        sorted(kd_hist.items()), sorted(kd_site.items()), kd_other.most_common()))
    P("\n== dropped XS (seed 55): %s\n" % sorted(drop.items()))
    fresh = fw.FRESH_INIT
    fw.FRESH_INIT = frozenset()
    c = collections.Counter()
    for t, w in counted:
        for f in fx.check_chain2(w)["fails"]:
            c[(t, w["start"], f["kind"])] += 1
    fw.FRESH_INIT = fresh
    P("\n== the fresh-seed rule off: %s\n" % sorted(c.items()))

    P("\n== touch and pass rows (all seven windows): function, extent, hits, locations hit\n")
    seen = set()
    for r in fw.TOUCH + fw.PASSDRAW:
        for lo, hi in r.get("ranges", ()):
            if (lo, hi) in seen:
                continue
            seen.add((lo, hi))
            h = {a: n for a, n in allhits.items() if lo <= a < hi}
            P("%-9s %-40s %#x %#x hits %d at %s\n" % (r.get("trigger") or ("client" if r.get("client") else "tick"), r["fn"][3:40], lo, hi, sum(h.values()),
                                                  ",".join("%#x" % a for a in sorted(h))))
    extents(sys.argv[2], allhits, P)
    P("defender, owner and killev rows' hits by open event (all seven windows): %s\n" % defhits.most_common())

    P("\n== modded monsters (MON lines of the process) and whether a window's UE0 holds them; Corpsefire is zombie1 (5), Mod1 27\n")
    for p in kept:
        cur, win, ue, mm = None, 0, {}, {}
        with open(p) as f:
            for ln in f:
                t = ln.split(" ", 1)[0]
                if t == "WIN":
                    win += 1
                    cur = win
                    ue[win] = set()
                elif t == "WEND":
                    cur = None
                elif t == "UE0" and cur:
                    o = json.loads(ln[4:])
                    if o["ty"] == 1:
                        ue[cur].add(o["id"])
                elif t == "MON":
                    try:
                        o = json.loads(ln[4:])
                    except ValueError:
                        continue
                    for m in o.get("m", []):
                        if m.get("mods"):
                            mm[m["id"]] = (m["cls"], tuple(m["mods"]))
        P("%s modded %s; per window: %s\n" % (tag_of(p), sorted(mm.items())[:7], {
            k: ("monsters %d" % len(v), [(i, mm[i]) for i in sorted(v) if i in mm]) for k, v in ue.items()}))

    P("\n== hooks not reached (the 5509 window)\n")
    names = {}
    with open(os.path.join(HERE, "gdb", "frame-hooks.txt")) as f:
        for ln in f:
            m = re.match(r"0x([0-9A-Fa-f]{8})\s+(\S+)", ln)
            if m:
                names[int(m.group(1), 16)] = m.group(2) if m.group(2)[0].isalpha() else "0x" + m.group(1)
    for p in kept:
        if "5509" not in p:
            continue
        ws, _o = fw.parse_log(p)
        hk = (ws[0]["wend"] or {}).get("hk") or {}
        got = {int(a, 16) for a in hk}
        P("listed %d reached %d only-with-no-event-open %s\nnot reached: %s\n" % (
            len(names), len(got), sorted(names.get(int(a, 16), a) for a, h in hk.items() if set(h) == {"none"}),
            ", ".join(names[a] for a in sorted(names) if a not in got)))

    P("\n== shared-seed pairs: consecutive G-moving top-level events of different units in one frame\n")
    for p in kept + pilot + dev:
        ws, _o = fw.parse_log(p)
        for w in ws:
            n, found = pairs(w)
            P("%-44s %5d len %s G-events %d pairs %d %s\n" % (os.path.basename(p)[:44], w["start"], w["win"].get("len"), n, len(found), found))
    return 0


if __name__ == "__main__":
    sys.exit(main())

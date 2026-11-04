"""Plan 0055 Phase 2b: the frame-window reader and checker (the `window` subcommand of tools/frame.py).

    python3 -I tools/frame.py window [--pilot] [--allow-stray] [--out FILE] LOG [LOG ...]
    python3 -I tools/frame.py window-selftest                 # the synthetic logs and the negative controls

Reads the logs of tools/gdb/frame.gdb (lines `TAG {json}`; the header `# d2run ...` and everything outside a window are
not checked). A window runs from a `WIN` line to its `WEND` line. Per window it tests

  (a) WHOLE: an FT0 and an FT1 for each of the `len` consecutive frame numbers from `start` (no gap, repeat or
      reorder), every opened pair closed in its frame (FT0/FT1, UE0/UE1, RU0/RU1, MSG0/MSG1, TQ0/TQ1, SV0/SV1; pairs
      nest, a close with no open or an open left at the frame's FT1 fails), every other line stamped with the frame
      it sits in (a line after FT1 of frame k and before FT0 of k + 1 is stamped k: the message drain), the logger's
      own WEND ok, and 0 lines the reader cannot parse (a logger tag with a bad body, or text that is not `TAG {json}`;
      `--allow-stray` lets the second kind through, e.g. a wine message in the same file; the pilot's own tags are
      foreign and counted, not unparsed);
  (b) UNMOVED: each seed object's reading (the game seed `Game+0xD0`, a unit's seed by (type, guid), a room's seed by
      its pointer) at a boundary is the previous reading of that object, unchanged (`handed`); otherwise a mismatch is
      listed with the steps between (`stepped k`, `reversed`, `off`, the LCG of rng/0001) and the lines logged between
      the two readings. A boundary is an entry (UE0, MSG0, RU0, TQ0, SV0), FT0 and FT1 at depth 0 (no event pair open),
      or a point (FP, TM, RC). Readings inside an open event pair are checked only for direction (exit not before
      entry). The chain is never resynchronised: each reading is compared with the previous *logged* reading, a
      mismatch does not change what the next is compared with. A mismatch whose later reading is an FP or TM line is
      listed apart (`located`: the draw is in the pass before that site, outside every logged pair); the entries
      (UE0, MSG0, RU0, TQ0, SV0) and FT0 decide the pilot's (b).

and reports what the record must state (see `report`). `--pilot` judges the first window of the first log by (a) and
(b) and its completion (c: WEND ok, the window inside one log with no LOGERR or CAP) and exits 1 on a failure.
Stdlib only. Read-only on the logs.
"""
import collections
import json
import random
import re
import sys

import frame_volume

M32 = 0xFFFFFFFF
MULT = 0x6AC690C5   # rng/0001; tools/frame.py's own copy is asserted equal in `window-selftest`

LINE = re.compile(r"^([A-Z][A-Z0-9]*) (\{.*\})\s*$")
REQ = {
    "WIN": ("id", "scene", "len", "start"), "WEND": ("id", "ok", "frames", "hits", "mono0", "mono1"),
    "HB": ("fr",), "FT0": ("fr", "pre", "gs", "hc"), "FT1": ("fr", "gs"), "FP": ("fr", "site", "gs"),
    "ACL": ("fr", "act", "r"), "UE0": ("fr", "ty", "id", "kind", "site", "gs", "lst"), "UE1": ("fr", "id", "site", "gs"),
    "MSG0": ("fr", "pl", "len", "gs"), "MSG1": ("fr", "gs"), "SYS": ("fr", "ty"), "RU0": ("fr", "room", "gs"),
    "RU1": ("fr", "room", "gs"), "TM": ("fr", "which", "gs"), "TQ0": ("fr", "cb", "gs"), "TQ1": ("fr", "gs"),
    "RC": ("fr", "room"), "RR": ("fr", "room"), "QE": ("fr", "kind"), "QF": ("fr", "kind"), "SV0": ("fr", "gs"),
    "SV1": ("fr", "gs"),
}
LOGGER_TAGS = frozenset(REQ) | {"CAP", "LOGERR", "WSKIP"}
BOOKKEEPING = frozenset({"WIN", "WEND", "HB"})
OPEN = {"UE0": "UE1", "MSG0": "MSG1", "RU0": "RU1", "TQ0": "TQ1", "SV0": "SV1"}
CLOSE = {v: k for k, v in OPEN.items()}
ENTRIES = frozenset(OPEN)
# pass rank (tools/frame.py PASS_NAMES) of a unit-event list: type -> (every-frame walk, slot walk)
RANK = {3: (4, 5), 0: (6, 7), 1: (8, 9), 2: (10, 11), 4: (12, 13)}
SCENE_EST = {"town": "town (1 player, 8 NPCs)", "pack": "outdoor pack (1 player, 15 monsters)",
             "maze": "maze boss (1 player, boss + 10 minions)"}
PERIOD = {"T20": 20, "D12": 12, "U11": 11, "S1500": 1500}
# the P1 review's stated queue rates per run event (frame_volume.QRATES mid): records queued per UE0 of a list/type,
# per message (the stated inputs the measured QE+QF per UE0 is read against)
MID = frame_volume.QRATES["mid"]
Q2_SESSION_LINES = 177860     # ten times plan 0045's 17 786
FLOORS = dict(windows=10, frames=250, scenes=3, per_scene=2, chained=5000, shared=20)


# ------------------------------------------------------------------------------------------------------ RNG
def sd(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def step(t):
    v = t[0] * MULT + t[1]
    return v & M32, (v >> 32) & M32


def steps(a, b, limit=4096):
    t = a
    for i in range(limit + 1):
        if t == b:
            return i
        t = step(t)
    return None


def fmt(t):
    return "%08x:%08x" % t


def relation(prev, cur):
    """prev, cur: 'lo:hi' seeds -> ('handed', 0) | ('stepped', k) | ('reversed', k) | ('off', None)."""
    if prev == cur:
        return "handed", 0
    a, b = sd(prev), sd(cur)
    k = steps(a, b)
    if k is not None:
        return "stepped", k
    k = steps(b, a)
    if k is not None:
        return "reversed", k
    return "off", None


# ------------------------------------------------------------------------------------------------------ parse
def parse_log(path):
    """-> (windows, outside) where a window is a dict {wid, scene, len, start, win, wend, lines [(no, tag, obj)], bad
    [(no, why)], stray [(no, text)], foreign Counter, open (no WEND)}; outside = Counter of the tags between windows."""
    wins, outside, cur = [], collections.Counter(), None
    with open(path, errors="replace") as fh:
        for no, raw in enumerate(fh, 1):
            text = raw.rstrip("\n")
            if no == 1 and text.startswith("#"):
                continue
            m = LINE.match(text)
            obj = None
            tag = None
            if m:
                tag = m.group(1)
                try:
                    obj = json.loads(m.group(2))
                except ValueError:
                    obj = None
            if tag == "WIN" and obj is not None and cur is None:
                cur = {"path": path, "wid": obj.get("id"), "scene": obj.get("scene"), "len": obj.get("len"),
                       "start": obj.get("start"), "win": obj, "wend": None, "lines": [(no, tag, obj)], "bad": [],
                       "stray": [], "foreign": collections.Counter(), "open": True, "first": no}
                continue
            if cur is None:
                if tag:
                    outside[tag] += 1
                continue
            if not text.strip():
                continue
            if tag is None:
                cur["stray"].append((no, text[:80]))
                continue
            if tag in LOGGER_TAGS:
                if obj is None or not isinstance(obj, dict):
                    cur["bad"].append((no, "%s: body is not json" % tag))
                    continue
                miss = [k for k in REQ.get(tag, ()) if k not in obj]
                if miss:
                    cur["bad"].append((no, "%s: missing %s" % (tag, ",".join(miss))))
                    continue
                if tag == "WEND":
                    cur["wend"] = obj
                    cur["lines"].append((no, tag, obj))
                    cur["open"] = False
                    cur["last"] = no
                    wins.append(cur)
                    cur = None
                    continue
                cur["lines"].append((no, tag, obj))
            else:
                if obj is None:
                    cur["stray"].append((no, text[:80]))
                else:
                    cur["foreign"][tag] += 1
    if cur is not None:
        cur["last"] = None
        wins.append(cur)
    return wins, outside


# ------------------------------------------------------------------------------------------------------ (a)
def check_whole(w, allow_stray=False):
    """-> list of failure strings (empty: whole)."""
    fails = []
    win = w["win"]
    n, start = w["len"], w["start"]
    if w["open"]:
        fails.append("no WEND: the window is open at the end of the log")
    if w["bad"]:
        fails.append("%d logger lines with a bad body (first: line %d %s)" % (len(w["bad"]), w["bad"][0][0], w["bad"][0][1]))
    if w["stray"] and not allow_stray:
        fails.append("%d lines that are not `TAG {json}` (first: line %d %r)" % (len(w["stray"]), w["stray"][0][0],
                                                                                w["stray"][0][1]))
    for no, tag, o in w["lines"]:
        if tag in ("LOGERR", "CAP", "WSKIP"):
            fails.append("logger %s at line %d: %s" % (tag, no, json.dumps(o)[:80]))
    if w["wend"] is not None and not w["wend"].get("ok"):
        fails.append("WEND ok=0 (%s)" % w["wend"].get("why"))
    # frames
    expect = start
    seen0, seen1 = {}, {}
    cur_frame = None          # the frame whose FT0 is open
    last_closed = None        # the last frame closed by an FT1
    stack = []                # open pairs: (tag, key, line)
    for no, tag, o in w["lines"]:
        if tag in BOOKKEEPING:
            continue
        f = o.get("fr")
        if tag == "FT0":
            if cur_frame is not None:
                fails.append("line %d: FT0 of frame %s while frame %s is open (no FT1)" % (no, f, cur_frame))
                cur_frame = None
            if f in seen0:
                fails.append("line %d: repeat: FT0 of frame %d (first at line %d)" % (no, f, seen0[f]))
            else:
                if f != expect:
                    fails.append("line %d: gap or reorder: FT0 of frame %d, expected %d" % (no, f, expect))
                expect = f + 1
                seen0[f] = no
            cur_frame = f
            continue
        if tag == "FT1":
            if cur_frame is None:
                fails.append("line %d: FT1 of frame %s with no FT0 open" % (no, f))
                continue
            if f != cur_frame:
                fails.append("line %d: FT1 of frame %s closes FT0 of frame %s" % (no, f, cur_frame))
            if stack:
                fails.append("line %d: frame %s ends with %d open pair(s): %s" % (
                    no, f, len(stack), ",".join("%s@%d" % (t, ln) for t, _k, ln in stack)))
                stack = []
            seen1[f] = no
            last_closed, cur_frame = f, None
            continue
        want = cur_frame if cur_frame is not None else last_closed
        if want is None:
            fails.append("line %d: %s before any FT0" % (no, tag))
        elif f != want:
            fails.append("line %d: %s stamped %s inside frame %s" % (no, tag, f, want))
        if tag in OPEN:
            stack.append((tag, (o.get("id"), o.get("room"), o.get("site")), no))
        elif tag in CLOSE:
            if not stack:
                fails.append("line %d: %s with no open %s (a reversed pair, or a lost open)" % (no, tag, CLOSE[tag]))
            elif stack[-1][0] != CLOSE[tag]:
                fails.append("line %d: %s closes %s@%d (pairs must nest)" % (no, tag, stack[-1][0], stack[-1][2]))
                stack.pop()
            else:
                t, key, ln = stack.pop()
                if tag == "UE1" and key[0] != o.get("id"):
                    fails.append("line %d: UE1 of unit %s closes UE0 of unit %s (line %d)" % (no, o.get("id"), key[0], ln))
                if tag == "RU1" and key[1] != o.get("room"):
                    fails.append("line %d: RU1 of room %s closes RU0 of room %s (line %d)" % (no, o.get("room"), key[1], ln))
    if cur_frame is not None:
        fails.append("frame %s: FT0 with no FT1 at the end" % cur_frame)
    if stack:
        fails.append("%d pair(s) open at the end of the window: %s" % (len(stack), ",".join(t for t, _k, _l in stack)))
    exp_frames = set(range(start, start + n))
    miss = sorted(exp_frames - set(seen0))
    if miss:
        fails.append("missing FT0 for %d frame(s), first %d" % (len(miss), miss[0]))
    miss = sorted(exp_frames - set(seen1))
    if miss:
        fails.append("missing FT1 for %d frame(s), first %d" % (len(miss), miss[0]))
    extra = sorted(set(seen0) - exp_frames)
    if extra:
        fails.append("%d FT0 frame(s) outside %d..%d, first %d" % (len(extra), start, start + n - 1, extra[0]))
    if w["wend"] is not None and w["wend"].get("frames") != n:
        fails.append("WEND frames=%s, window len=%s" % (w["wend"].get("frames"), n))
    del win
    return fails


# ------------------------------------------------------------------------------------------------------ (b)
def check_chain(w):
    """-> dict(mismatches [...], located [...], inside_reversed [...], pairs Counter by tag and status, readings, draws)."""
    last = {}
    depth = 0
    stack = []          # open event pairs: dict(tag, line, entry {key: seed}, bad, first, handed, o)
    mism, located, inrev = [], [], []
    pairs = collections.defaultdict(collections.Counter)    # tag -> {chained, first, broken}
    nread = collections.Counter()
    drew = collections.Counter()                            # (tag) -> events whose exit differs from entry
    seq = []                                                # tag by line, for the "between" trace
    shared = []                                             # top-level game-seed-drawing pairs, per frame
    frame_draws = collections.defaultdict(list)
    ts = [(no, tag) for no, tag, _ in w["lines"]]
    idx = {no: i for i, (no, _t) in enumerate(ts)}

    def between(a, b):
        c = collections.Counter(t for no, t in ts[idx[a] + 1: idx[b]] if t not in ("QE", "QF"))
        return ", ".join("%s %d" % kv for kv in c.most_common(5))

    def reading(key, seed, role, no, tag, o, pair=None):
        if seed is None:
            return
        nread[role] += 1
        prev = last.get(key)
        last[key] = (seed, no, tag)
        if role == "exit":
            return
        inside = role == "entry" and (depth > 0 if key == "G" else any(key in p["entry"] for p in stack))
        if prev is None:
            if pair is not None and not inside:
                pair["first"] += 1
            return
        rel, k = relation(prev[0], seed)
        if inside:
            if rel == "reversed":
                inrev.append((no, tag, key, prev[1], k))
            return
        if rel == "handed":
            if pair is not None:
                pair["handed"] += 1
            return
        rec = dict(line=no, tag=tag, key=key, prev=prev[1], prev_tag=prev[2], rel=rel, k=k, between=between(prev[1], no),
                   fr=o.get("fr"))
        if tag in ("FP", "TM"):
            located.append(rec)
        else:
            mism.append(rec)
            if pair is not None:
                pair["bad"] += 1

    for no, tag, o in w["lines"]:
        if tag in BOOKKEEPING or tag in ("QE", "QF", "RR", "SYS", "ACL", "HB", "LOGERR", "CAP", "WSKIP"):
            continue
        if tag in ENTRIES:
            p = collections.Counter()
            keys = {}
            if tag == "UE0":
                if o.get("us"):
                    keys[("U", o["ty"], o["id"])] = o["us"]
            elif tag == "MSG0":
                if o.get("ps") and o.get("id") is not None:
                    keys[("U", 0, o["id"])] = o["ps"]
            elif tag == "RU0":
                if o.get("rs"):
                    keys[("R", o["room"])] = o["rs"]
            rec = {"tag": tag, "line": no, "entry": dict(keys), "cnt": p, "o": o, "gs0": o.get("gs")}
            reading("G", o.get("gs"), "entry", no, tag, o, p)
            for key, seed in keys.items():
                reading(key, seed, "entry", no, tag, o, p)
            stack.append(rec)
            depth += 1
        elif tag in CLOSE:
            if not stack:
                continue
            rec = stack.pop()
            depth -= 1
            reading("G", o.get("gs"), "exit", no, tag, o)
            gs0, gs1 = rec["gs0"], o.get("gs")
            if gs0 and gs1:
                r0 = relation(gs0, gs1)
                if r0[0] == "reversed":
                    inrev.append((no, tag, "G", rec["line"], r0[1]))
                if gs0 != gs1:
                    drew["G " + rec["tag"]] += 1
                    if depth == 0 and rec["tag"] == "UE0":
                        frame_draws[o["fr"]].append((rec["o"], gs0, gs1, rec["line"]))
            if tag == "UE1":
                us1 = o.get("us")
                key = ("U", rec["o"].get("ty"), rec["o"].get("id"))
                if us1 and rec["entry"].get(key):
                    r1 = relation(rec["entry"][key], us1)
                    if r1[0] == "reversed":
                        inrev.append((no, tag, key, rec["line"], r1[1]))
                    if r1[0] != "handed":
                        drew["U UE0"] += 1
                    reading(key, us1, "exit", no, tag, o)
            elif tag == "MSG1" and o.get("ps") and rec["o"].get("id") is not None:
                reading(("U", 0, rec["o"]["id"]), o["ps"], "exit", no, tag, o)
            elif tag == "RU1" and o.get("rs"):
                reading(("R", rec["o"]["room"]), o["rs"], "exit", no, tag, o)
            c = rec["cnt"]
            st = "broken" if c["bad"] else ("chained" if c["handed"] and not c["first"] else
                                            ("first" if c["first"] else "chained"))
            pairs[rec["tag"]][st] += 1
        elif tag in ("FT0", "FT1", "FP", "TM"):
            reading("G", o.get("gs"), "point", no, tag, o)
        elif tag == "RC":
            if o.get("rs"):
                reading(("R", o["room"]), o["rs"], "point", no, tag, o)
    return dict(mism=mism, located=located, inrev=inrev, pairs=pairs, nread=nread, drew=drew, frame_draws=frame_draws)


# ------------------------------------------------------------------------------------------------------ the record
def rank_of(o):
    ef, slot = RANK.get(o["ty"], (0, 0))
    return slot if o["lst"] == "slot" else ef


def stats(w, ch):
    """The numbers the record states for one window."""
    c = collections.Counter(tag for _no, tag, _o in w["lines"])
    n = w["len"]
    lines = sum(v for t, v in c.items() if t not in BOOKKEEPING)
    comparable = lines - sum(c.get(t, 0) for t in ("FP", "ACL", "SYS", "TQ0", "TQ1", "SV0", "SV1", "LOGERR", "CAP"))
    wend = w["wend"] or {}
    hits = wend.get("hits") or {}
    stops = sum(hits.values())
    wall = (wend["mono1"] - wend["mono0"]) if wend and "mono0" in wend else None
    ev = [o for _no, t, o in w["lines"] if t == "UE0"]
    # timers: the periods seen
    tm = collections.defaultdict(list)
    for _no, t, o in w["lines"]:
        if t == "TM":
            tm[o["which"]].append(o["fr"])
    frames = range(w["start"], w["start"] + n)
    per = {}
    for which, p in PERIOD.items():
        seen = sorted(set(tm.get(which, ())))
        due = [f for f in frames if f % p == 0]
        per[which] = dict(seen=len(seen), due=len(due), on_period=all(f % p == 0 for f in seen),
                          complete=(set(due) <= set(seen)) if which != "U11" else (not due or bool(seen)),
                          gaps=sorted({b - a for a, b in zip(seen, seen[1:])}))
    # the kind-11 and kind-6 runs
    dfree = collections.defaultdict(lambda: [0, 0])
    ue1 = {}
    open_ue = []
    for no, t, o in w["lines"]:
        if t == "UE0":
            open_ue.append(o)
        elif t == "UE1" and open_ue:
            e0 = open_ue.pop()
            if e0["kind"] in (6, 11):
                k = (e0["ty"], e0["kind"])
                dfree[k][0] += 1
                if e0.get("gs") == o.get("gs") and e0.get("us") == o.get("us"):
                    dfree[k][1] += 1
                else:
                    ue1.setdefault(k, []).append(no)
    # shared-seed pairs
    shared = dict(pairs=0, handed=0, rank_ok=0, rank_reversed=0)
    for f, seq in ch["frame_draws"].items():
        for (a, a0, a1, _la), (b, b0, b1, _lb) in zip(seq, seq[1:]):
            if (a["ty"], a["id"]) == (b["ty"], b["id"]):
                continue
            shared["pairs"] += 1
            shared["handed"] += a1 == b0
            ra, rb = rank_of(a), rank_of(b)
            shared["rank_ok"] += ra <= rb
            shared["rank_reversed"] += ra > rb
    # room activation and activations inside a NewRoomsUpdate walk
    rc = [(no, o) for no, t, o in w["lines"] if t == "RC"]
    in_walk = 0
    ru_open = 0
    walk_frame = None
    for no, t, o in w["lines"]:
        if t == "FT0":
            walk_frame = None
        elif t == "RU0":
            ru_open += 1
            walk_frame = o["fr"]
        elif t == "RU1":
            ru_open -= 1
        elif t == "UE0":
            walk_frame = None
        elif t == "RC" and (ru_open > 0 or walk_frame == o["fr"]):
            in_walk += 1
    qe = c.get("QE", 0) + c.get("QF", 0)
    mod1500 = [f for f in frames if f % 1500 == 0]
    mod8192 = [f for f in frames if f % 8192 == 0]
    chained = sum(v.get("chained", 0) for k, v in ch["pairs"].items())
    est = frame_volume.estimate13_rows().get((SCENE_EST.get(w["scene"], ""), "mid"))
    # predicted QE+QF per window from the stated mid rates and the measured UE0 mix
    pred_q = 0.0
    for o in ev:
        if o["ty"] == 3:
            pred_q += MID["mis"]
        elif o["ty"] in (2, 4):
            pred_q += MID["oth"]
        else:
            pred_q += MID["ef"] if o["lst"] == "ef" else MID["slot"]
    pred_q += MID["msg"] * c.get("MSG0", 0)
    return dict(n=n, lines=lines, comparable=comparable, counts=c, stops=stops, wall=wall, ue0=len(ev), qe=qe,
                pred_q=pred_q, per=per, dfree=dict(dfree), nondf=ue1, shared=shared, rc=len(rc), rc_in_walk=in_walk,
                mod1500=mod1500, mod8192=mod8192, sv0=c.get("SV0", 0), chained=chained, est=est, hits=hits,
                ghits=(w["wend"] or {}).get("ghits", {}))


def report(wins, ch_all, st_all, out, allow_stray=False):
    """Print the record's lines; return (all_whole, all_unmoved)."""
    P = out.write
    ok_whole = ok_unmoved = True
    per_scene = collections.Counter()
    tot = collections.Counter()
    hit_tot = collections.Counter()
    for w, ch, s in zip(wins, ch_all, st_all):
        fails = check_whole(w, allow_stray)
        ent = [m for m in ch["mism"]]
        whole = not fails
        unmoved = not ent
        ok_whole &= whole
        ok_unmoved &= unmoved
        per_scene[w["scene"]] += 1 if (whole and unmoved and w["len"] >= FLOORS["frames"]) else 0
        P("WINDOW %s id=%s scene=%s start=%s len=%s whole=%s unmoved=%s\n" % (
            w["path"].rsplit("/", 1)[-1], w["wid"], w["scene"], w["start"], w["len"], "yes" if whole else "NO",
            "yes" if unmoved else "NO"))
        for f in fails[:12]:
            P("  WHOLE-FAIL %s\n" % f)
        if len(fails) > 12:
            P("  WHOLE-FAIL ... %d more\n" % (len(fails) - 12))
        for m in ent[:20]:
            P("  MISMATCH line %d %s %s: previous reading line %d %s, %s%s; lines between: %s\n" % (
                m["line"], m["tag"], m["key"], m["prev"], m["prev_tag"], m["rel"],
                (" %d" % m["k"]) if m["k"] is not None else "", m["between"] or "none"))
        if len(ent) > 20:
            P("  MISMATCH ... %d more\n" % (len(ent) - 20))
        for m in ch["located"][:5]:
            P("  LOCATED line %d %s after line %d %s: %s%s (a draw outside every logged pair, before this site)\n" % (
                m["line"], m["tag"], m["prev"], m["prev_tag"], m["rel"], (" %d" % m["k"]) if m["k"] is not None else ""))
        for x in ch["inrev"][:5]:
            P("  REVERSED-INSIDE line %d %s %s (opened line %d)\n" % tuple(x[:4]))
        P("  unmoved: mismatches=%d located=%d reversed_inside=%d  readings=%s  events that moved a seed=%s\n" % (
            len(ent), len(ch["located"]), len(ch["inrev"]), dict(ch["nread"]), dict(ch["drew"])))
        n = s["n"]
        e = s["est"]
        lpf = s["lines"] / n if n else 0
        P("  lines=%d lines_per_frame=%.2f comparable_per_frame=%.2f" % (s["lines"], lpf, s["comparable"] / n))
        if e:
            P(" estimate13_mid=%.1f ratio=%.2f stop_at_3x=%s" % (e["lines"], lpf / e["lines"],
                                                                "YES" if lpf > 3 * e["lines"] else "no"))
        P("\n")
        if s["wall"]:
            P("  wall_s=%.1f frames_per_wall_s=%.1f stops=%d stops_per_frame=%.1f%s\n" % (
                s["wall"], n / s["wall"], s["stops"], s["stops"] / n, (" estimate13_stops=%.1f" % e["stops"]) if e else ""))
        P("  queue QE=%d QF=%d per_UE0=%.3f predicted_at_stated_mid=%.3f  UE0=%d MSG0=%d\n" % (
            s["counts"].get("QE", 0), s["counts"].get("QF", 0), s["qe"] / s["ue0"] if s["ue0"] else 0,
            s["pred_q"] / s["ue0"] if s["ue0"] else 0, s["ue0"], s["counts"].get("MSG0", 0)))
        pr = " ".join("%s=%s" % (k, dict(v)) for k, v in sorted(ch["pairs"].items()))
        P("  chained_events=%d (pairs by status: %s)\n" % (s["chained"], pr or "none"))
        P("  timers " + " ".join("%s(seen %d of %d due, on_period=%s, complete=%s, gaps=%s)" % (
            k, v["seen"], v["due"], v["on_period"], v["complete"], v["gaps"]) for k, v in s["per"].items()) + "\n")
        P("  rooms RC=%d (in a NewRoomsUpdate walk: %d) RR=%d  mod1500 frames=%s mod8192 frames=%s SV0=%d\n" % (
            s["rc"], s["rc_in_walk"], s["counts"].get("RR", 0), s["mod1500"], s["mod8192"], s["sv0"]))
        P("  shared-seed pairs=%(pairs)d handed=%(handed)d in_pass_order=%(rank_ok)d reversed_rank=%(rank_reversed)d\n" % s["shared"])
        P("  draw-free runs " + (" ".join("ty%d_kind%d=%d/%d" % (k[0], k[1], v[1], v[0]) for k, v in sorted(s["dfree"].items()))
                                or "none") + "\n")
        if s["nondf"]:
            P("  NOT draw-free " + "; ".join("ty%d kind%d lines %s" % (k[0], k[1], v[:5]) for k, v in s["nondf"].items()) + "\n")
        P("  foreign tags in the window (the pilot's): %s\n" % (dict(w["foreign"]) or "none"))
        for k, v in s["hits"].items():
            hit_tot[k] += v
        tot["frames"] += n
        tot["lines"] += s["lines"]
        tot["chained"] += s["chained"]
        tot["windows"] += 1
        tot["shared_handed"] += s["shared"]["handed"]
        tot["shared_ok"] += min(s["shared"]["handed"], s["shared"]["rank_ok"])
    P("TOTAL windows=%d frames=%d lines=%d chained_events=%d shared_pairs_handed=%d\n" % (
        tot["windows"], tot["frames"], tot["lines"], tot["chained"], tot["shared_handed"]))
    P("HITS " + " ".join("%s=%d" % kv for kv in sorted(hit_tot.items())) + "\n")
    P("SCENES kept windows (whole and unmoved, >= %d frames): %s\n" % (FLOORS["frames"], dict(per_scene)))
    return ok_whole, ok_unmoved


def run(paths, pilot=False, allow_stray=False, out=None):
    out = out or sys.stdout
    wins, session_lines, outside_tot = [], 0, collections.Counter()
    for p in paths:
        ws, outside = parse_log(p)
        wins += ws
        outside_tot += outside
        with open(p, errors="replace") as fh:
            session_lines += sum(1 for ln in fh if LINE.match(ln))
    if not wins:
        out.write("no window in %s\n" % ", ".join(paths))
        return 1
    if pilot:
        wins = wins[:1]
    ch = [check_chain(w) for w in wins]
    st = [stats(w, c) for w, c in zip(wins, ch)]
    ok_whole, ok_unmoved = report(wins, ch, st, out, allow_stray)
    out.write("SESSION logger/tag lines in the logs=%d (Q2's trigger: above %d) -> %s\n" % (
        session_lines, Q2_SESSION_LINES, "TRIGGER" if session_lines > Q2_SESSION_LINES else "below"))
    # Done-when counters
    per_scene = collections.Counter(w["scene"] for w, s in zip(wins, st) if w["len"] >= FLOORS["frames"])
    chained = sum(s["chained"] for s in st)
    shared = sum(s["shared"]["handed"] for s in st)
    out.write("DONE-WHEN windows>=%d:%d (%d) scenes>=%d,each>=%d:%s chained>=%d:%d (%d) shared>=%d:%d (%d)\n" % (
        FLOORS["frames"], len([1 for w in wins if w["len"] >= FLOORS["frames"]]), FLOORS["windows"], FLOORS["scenes"],
        FLOORS["per_scene"], dict(per_scene), FLOORS["chained"], chained, FLOORS["chained"], FLOORS["shared"], shared,
        FLOORS["shared"]))
    if pilot:
        w = wins[0]
        carried = w["wend"] is not None and w["wend"].get("ok") and not any(
            t in ("LOGERR", "CAP") for _n, t, _o in w["lines"])
        out.write("PILOT (a) whole: %s  (b) unmoved: %s  (c) completed in this log: %s  (the window's 250 frames: %s)\n" % (
            "PASS" if ok_whole else "FAIL", "PASS" if ok_unmoved else "FAIL", "PASS" if carried else "FAIL",
            "yes" if w["len"] == 250 else "NO, len=%s" % w["len"]))
        return 0 if (ok_whole and ok_unmoved and carried and w["len"] == 250) else 1
    return 0 if (ok_whole and ok_unmoved) else 1


# ------------------------------------------------------------------------------------------------------ synthetic logs
def synth(seed=1, frames=250, start=1000, scene="town", units=6, msg_rate=0.2, ps="pack"):
    """A consistent window as log lines: the game seed and each unit's seed advance only inside event pairs (plus a few
    pass draws that an FP line locates), so a clean window is whole and unmoved. -> list of text lines."""
    rnd = random.Random(seed)
    g = (0x2A, 0x29A)
    u = {}
    for i in range(units):
        u[i] = dict(ty=1 if i else 0, id=100 + i, s=(rnd.randrange(1, M32), rnd.randrange(M32)))

    def adv(t, k):
        for _ in range(k):
            t = step(t)
        return t

    L = []
    n = [0]

    def emit(tag, d):
        n[0] += 1
        d["n"] = n[0]
        L.append("%s %s" % (tag, json.dumps(d, separators=(",", ":"))))

    emit("WIN", dict(id=1, scene=scene, len=frames, start=start, fr=start, wall=1.0, mono=1.0, cover=0, rev=1))
    hits = collections.Counter()
    for f in range(start, start + frames):
        emit("FT0", dict(fr=f, pre=f - 1, gs=fmt(g), hc=f % 9, game=4096))
        for which, p in PERIOD.items():
            if f % p == 0:
                emit("TM", dict(fr=f, which=which, gs=fmt(g), **({"act": 0} if which == "U11" else {})))
        if rnd.random() < 0.1:                      # a pass draws outside every pair: located by the next FP
            g = adv(g, rnd.randrange(1, 3))
            emit("FP", dict(fr=f, site=0x52D8EB, gs=fmt(g)))
        order = sorted(u, key=lambda i: (u[i]["ty"] != 0, i))
        for i in order:
            if rnd.random() < 0.5:
                continue
            x = u[i]
            kind = 11 if x["ty"] == 0 and rnd.random() < 0.3 else (6 if rnd.random() < 0.1 else rnd.choice((1, 2, 3)))
            lst = rnd.choice(("slot", "ef"))
            site = 0x00540FB2 if x["ty"] == 0 else 0x005410B2
            free = kind in (6, 11)
            emit("UE0", dict(fr=f, ty=x["ty"], id=x["id"], lst=lst, kind=kind, rf=f, a=0, b=0, cb=1, site=site, u=0x1000 + i,
                             us=fmt(x["s"]), gs=fmt(g)))
            if rnd.random() < 0.6:
                emit("QE", dict(fr=f, kind=3, asked=f + 5, ut=x["ty"], id=x["id"], ra=0x5417E8))
            if not free:
                g = adv(g, rnd.randrange(0, 3))
                x["s"] = adv(x["s"], rnd.randrange(0, 3))
            emit("UE1", dict(fr=f, id=x["id"], site=site, u=0x1000 + i, us=fmt(x["s"]), gs=fmt(g), gone=0))
        if f % 97 == 0:
            emit("RU0", dict(fr=f, room=0x7000, f=1, rs="00000001:00000002", gs=fmt(g), act=0, ai=0))
            g = adv(g, 2)
            emit("RU1", dict(fr=f, room=0x7000, f=1, rs="00000001:00000002", gs=fmt(g), act=0, ai=0))
            emit("RC", dict(fr=f, act=0, room=0x7001, drlg=1, lv=2, rs="00000003:00000004", f=0))
        emit("FT1", dict(fr=f, gs=fmt(g)))
        if rnd.random() < msg_rate:
            emit("MSG0", dict(fr=f, pl=0x1000, id=100, op=3, len=5, hex="0300", ps=fmt(u[0]["s"]), gs=fmt(g)))
            g = adv(g, 1)
            u[0]["s"] = adv(u[0]["s"], 1)
            emit("MSG1", dict(fr=f, r=0, ps=fmt(u[0]["s"]), gs=fmt(g)))
    cnt = collections.Counter(ln.split(" ", 1)[0] for ln in L)
    emit("WEND", dict(id=1, ok=1, why="", frames=frames, lines=len(L) - 1, hits=dict(cnt), ghits={}, wall0=1.0,
                      wall1=11.0, mono0=1.0, mono1=11.0, fr=start + frames - 1))
    del hits, ps
    return L


def selftest(frame_mult=MULT, frame_step=None):
    """The clean synthetic window passes (a) and (b); each negative control fails the test it is for. Also asserts that
    this module's RNG is tools/frame.py's (the multiplier and the step on random inputs)."""
    import os
    import tempfile

    def verdict(lines):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "t.log")
        with open(p, "w") as f:
            f.write("# d2run seed=1 gdb=tools/gdb/frame.gdb slot=2\n" + "\n".join(lines) + "\n")
        ws, _o = parse_log(p)
        if not ws:
            return None, None
        w = ws[0]
        return check_whole(w), check_chain(w)["mism"]

    def frame_of(lines, k):
        return [i for i, ln in enumerate(lines) if json.loads(ln.split(" ", 1)[1]).get("fr") == k]

    base = synth()
    res = []
    rr = random.Random(7)
    same = frame_mult == MULT and (frame_step is None or all(
        frame_step(t) == step(t) for t in ((rr.randrange(M32), rr.randrange(M32)) for _ in range(200))))
    res.append(("RNG step equals tools/frame.py's", same, ""))
    f, m = verdict(base)
    res.append(("clean: whole and unmoved", not f and not m, "%s %s" % (f[:2], m[:2])))
    # gap: every line of one frame removed
    k = 1100
    idx = set(frame_of(base, k))
    gap = [ln for i, ln in enumerate(base) if i not in idx]
    f, m = verdict(gap)
    res.append(("gap fails (a)", bool(f) and any("gap" in x or "missing" in x for x in f), f[:2]))
    # repeat: one frame's lines duplicated
    ii = sorted(frame_of(base, k))
    rep = base[:ii[-1] + 1] + base[ii[0]: ii[-1] + 1] + base[ii[-1] + 1:]
    f, m = verdict(rep)
    res.append(("repeat fails (a)", bool(f) and any("repeat" in x for x in f), f[:2]))
    # unclosed pair: one UE1 dropped
    j = next(i for i, ln in enumerate(base) if ln.startswith("UE1 "))
    f, m = verdict(base[:j] + base[j + 1:])
    res.append(("unclosed pair fails (a)", bool(f) and any("open" in x or "nest" in x for x in f), f[:2]))
    # seed off by one: a UE0's game seed stepped once
    j = next(i for i, ln in enumerate(base) if ln.startswith("UE0 ") and i > 40)
    o = json.loads(base[j].split(" ", 1)[1])
    o["gs"] = fmt(step(sd(o["gs"])))
    bad = list(base)
    bad[j] = "UE0 " + json.dumps(o, separators=(",", ":"))
    f, m = verdict(bad)
    res.append(("seed off by one fails (b) and not (a)", not f and any(x["rel"] == "stepped" and x["k"] == 1 for x in m), m[:2]))
    # a unit seed off by one
    o = json.loads(base[j].split(" ", 1)[1])
    o["us"] = fmt(step(sd(o["us"])))
    bad = list(base)
    bad[j] = "UE0 " + json.dumps(o, separators=(",", ":"))
    f, m = verdict(bad)
    res.append(("unit seed off by one fails (b)", not f and any(x["key"][0] == "U" for x in m), m[:2]))
    # reversed pair: a UE1 logged before its UE0
    a0 = next(i for i, ln in enumerate(base) if ln.startswith("UE0 "))
    b0 = next(i for i, ln in enumerate(base) if ln.startswith("UE1 ") and i > a0)
    rv = list(base)
    rv[a0], rv[b0] = base[b0], base[a0]
    f, m = verdict(rv)
    res.append(("reversed pair fails (a)", bool(f), f[:2]))
    # unparsed: a mangled logger line, and stray text
    bad = list(base)
    bad[10] = "UE0 {not json"
    f, m = verdict(bad)
    res.append(("unparsed logger line fails (a)", bool(f), f[:1]))
    bad = list(base)
    bad.insert(10, "fixme:some wine text")
    f, m = verdict(bad)
    res.append(("stray text fails (a) unless allowed", bool(f), f[:1]))
    # a frame's FT1 lost
    j = next(i for i, ln in enumerate(base) if ln.startswith("FT1 ") and i > 50)
    f, m = verdict(base[:j] + base[j + 1:])
    res.append(("lost FT1 fails (a)", bool(f), f[:1]))
    ok = True
    for name, passed, why in res:
        sys.stdout.write("%s %s%s\n" % ("PASS" if passed else "FAIL", name, "" if passed else "  <- %s" % (why,)))
        ok &= bool(passed)
    return 0 if ok else 1

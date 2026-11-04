#!/usr/bin/env python3
"""Plan 0055 Phase 2b, the lane/p55b review: what a frame-window log holds about each seed that stepped between two logged
readings of its own unit, window by window. For each such pair it prints the steps, every QE on that unit between the readings
with the event open around it, and that event's game-seed steps; then the two order tests the log allows (each frame's walks
in rank order, slot events in the order their QE lines queued them, each with its count). No game, no write.

    python3 -I tools/frame_foreign.py LOG [LOG ...]
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rng  # noqa: E402

RANK = {3: (4, 5), 0: (6, 7), 1: (8, 9), 2: (10, 11), 4: (12, 13)}   # as tools/frame_window.py
TAGS = ("WIN", "WEND", "FT0", "UE0", "UE1", "QE")


def seed(s):
    a, b = s.split(":")
    return int(a, 16), int(b, 16)


def steps(a, b, limit=5000):
    lo, hi = seed(a)
    target = seed(b)
    for k in range(limit + 1):
        if (lo, hi) == target:
            return k
        lo, hi = rng.step(lo, hi)
    return None


def lines_of(path):
    for no, text in enumerate(open(path, errors="replace"), 1):
        tag, _, rest = text.partition(" ")
        if tag in TAGS:
            try:
                yield no, tag, json.loads(rest)
            except ValueError:
                pass


def read(path):
    print("LOG", os.path.basename(path))
    inside = False
    n = dict(ue0=0, rank_inverted=0, slot_placed=0, slot_inverted=0)
    for no, tag, d in lines_of(path):
        if tag == "WIN":
            inside = True
            stack = []
            last = {}              # (type, id) -> (seed, line, frame); a window starts with no reading
            queued = collections.defaultdict(list)   # (type, id) -> QE since its last reading
            game_steps = {}        # opening line of an event -> game-seed steps, known at its close
            slots = collections.defaultdict(list)    # (type, frame asked) -> queue order
            pos = collections.Counter()
            rank = -1
            continue
        if tag == "WEND":
            inside = False
            continue
        if not inside:
            continue
        if tag == "FT0":
            rank = -1
        elif tag == "UE0":
            n["ue0"] += 1
            r = RANK[d["ty"]][0 if d["lst"] == "ef" else 1]
            if not stack:
                n["rank_inverted"] += r < rank
                rank = max(rank, r)
            if d["lst"] == "slot":
                k = (d["ty"], d["fr"])
                q = slots.get(k, [])
                e = (d["id"], d["kind"])
                if e in q[pos[k]:]:
                    pos[k] = q.index(e, pos[k]) + 1
                    n["slot_placed"] += 1
                elif e in q:
                    n["slot_inverted"] += 1
            key = (d["ty"], d["id"])
            if key in last and last[key][0] != d["us"]:
                print("STEP unit %d:%d, %s steps, line %d (frame %d) to line %d (frame %d, kind %d)" % (
                    key[0], key[1], steps(last[key][0], d["us"]), last[key][1], last[key][2], no, d["fr"], d["kind"]))
                for m, fr, kind, asked, top in queued[key]:
                    print("  QE line %d frame %d kind %d at +%d, inside %s, game-seed steps of that event %s" % (
                        m, fr, kind, asked - fr, "%d:%d kind %d %s" % top[1:5] if top else "no event",
                        game_steps.get(top[0]) if top else None))
                if not queued[key]:
                    print("  no QE on this unit between the readings")
            last[key] = (d["us"], no, d["fr"])
            queued[key] = []
            stack.append((no, d["ty"], d["id"], d["kind"], d["lst"], d["gs"]))
        elif tag == "UE1" and stack:
            o = stack.pop()
            game_steps[o[0]] = steps(o[5], d["gs"])
            if d.get("us"):
                last[(o[1], o[2])] = (d["us"], no, d["fr"])
        elif tag == "QE" and d.get("ut") is not None:
            queued[(d["ut"], d["id"])].append((no, d["fr"], d["kind"], d["asked"], stack[-1] if stack else None))
            slots[(d["ut"], d["asked"])].append((d["id"], d["kind"]))
    print("ORDER UE0=%(ue0)d rank_inverted=%(rank_inverted)d slot_placed=%(slot_placed)d slot_inverted=%(slot_inverted)d" % n)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        read(p)

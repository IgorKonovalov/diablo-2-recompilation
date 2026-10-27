#!/usr/bin/env python3
"""Which built copy of level 91 the OBJS listing follows, and which copy is the client's (lane/h6e2f; items/0010 §
H6e2, the brain chest in level 91). Read-only over kept logs and the merged data tree; no harness. Built on
tools/rdp_brain91.py (unchanged): the same DS1 file of LvlPrest 704, the same level origin and room mapping.

Usage:
  python3 -I tools/h6e2f_copies.py [--root workspace/merged] [--exe workspace/install/app/game.exe] LOG [LOG ...]
  python3 -I tools/h6e2f_copies.py --warps LID ROW LOG

--warps: at each first WRP line of a room with a LvlWarp-row-ROW warp on level LID, and at the first PLR line on
another level after LID, the warps of that row on LID and the destination tools/d2pilot.py's LogState.warp_dest gives
each from the log up to that line (what --descend-to saw; eye4c's first descent).

Per log and per level-91 copy (level pointer):
  - the RL lines' room +0x28 ("f28", tools/gdb/pilot.py from lane/h6e2f on; absent in older logs): how many of the
    copy's rooms carry bit 0x40000, the client-copy flag of drlg/0004 row 10;
  - for each object of the level's DS1 file that an OBJS line lists (tools/gdb/vendors.py: the server game's object
    lists), the log line of its first listing against the line of its room's first RRESEED in that copy: "before"
    (the room activated in the copy before the object was first listed; consistent with the listing following the
    copy), "after" (first listed while the room was not yet activated in that copy: the listing cannot follow it),
    "never" (the room never activated in that copy);
  - the class-406 chest's room: its RRESEED line per copy and the chest's first OBJS line.
Stdlib only (and tools/ds1.py).
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ds1  # noqa: E402


def ds1_file(root, t, objtab, fn):
    for dp, _, fs in os.walk(os.path.join(root, "data", "global", "tiles")):
        for f_ in fs:
            if os.path.join(dp, f_).lower().endswith(fn.lower()):
                with open(os.path.join(dp, f_), "rb") as fh:
                    f = ds1.parse(fh.read())
                return {(u["id"], u["x"], u["y"]) for u in ds1._units(f, t, objtab) if u["type"] == 2}
    return set()


def warps(lid, row, path):
    import io
    import d2pilot
    lines = open(path, errors="replace").read().split("\n")
    cuts, seen, on = [], set(), False
    for n, l in enumerate(lines):
        tag, _, rest = l.partition(" ")
        if tag == "WRP":
            d = json.loads(rest)
            if d["lid"] == lid and d["rec"] == row and d["room"] not in seen:
                seen.add(d["room"])
                cuts.append(n)
        elif tag == "PLR":
            p = json.loads(rest)["lid"]
            if p == lid:
                on = True
            elif on:
                cuts.append(n)
                print("first PLR line on level %d after %d: %d" % (p, lid, n))
                break
    for cut in cuts:
        st = d2pilot.LogState(os.devnull)
        st.f.close()
        st.f = io.StringIO("\n".join(lines[:cut + 1]) + "\n")
        st.poll()
        print("line %d: %s" % (cut, [(k[2:], st.warp_dest(k)) for k in sorted(st.wrp) if k[0] == lid and k[1] == row]))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--warps":
        return warps(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(ROOT, "workspace", "merged"))
    ap.add_argument("--exe", default=os.path.join(ROOT, "workspace", "install", "app", "game.exe"))
    ap.add_argument("logs", nargs="+")
    a = ap.parse_args()
    t = ds1._tables(a.root)
    objtab = ds1._object_table(a.exe)
    rec = [r for r in t["lvlprest"] if r["Def"] == 704][0]
    files = {rec["File%d" % i]: ds1_file(a.root, t, objtab, rec["File%d" % i]) for i in range(1, 7)}
    for path in a.logs:
        rl, f28 = {}, {}
        org = None
        acts = {}           # level pointer -> {(rx, ry) room in tiles/8: first RRESEED line}
        first = {}          # (cls, x, y) level-relative -> first OBJS line
        lines = list(open(path, errors="replace"))
        for n, l in enumerate(lines):
            tag, _, rest = l.partition(" ")
            if tag == "RL":
                d = json.loads(rest)
                rl[d["room"]] = (d["level"], d["rect"])
                if d.get("lid") == 91 or d.get("pdef") == 704:
                    f28.setdefault(d["level"], []).append(d.get("f28"))
                if d.get("pdef") == 704:
                    org = (min(org[0], d["rect"][0]), min(org[1], d["rect"][1])) if org else (d["rect"][0], d["rect"][1])
        for n, l in enumerate(lines):
            tag, _, rest = l.partition(" ")
            if tag == "RRESEED":
                d = json.loads(rest)
                if d["level"] == 91 and d["room"] in rl and org:
                    lp, r = rl[d["room"]]
                    acts.setdefault(lp, {}).setdefault(((r[0] - org[0]) // 8, (r[1] - org[1]) // 8), n)
            elif tag == "OBJS" and org:
                for c, x, y in json.loads(rest)["o"]:
                    rx, ry = x - 5 * org[0], y - 5 * org[1]
                    if 0 <= rx < 200 and 0 <= ry < 200:
                        first.setdefault((c, rx, ry), n)
        seen = set(first)
        best = max(files, key=lambda k: len(seen & files[k]) - len(seen - files[k]))
        objs = files[best]
        print("%s: level 91 file %s (listed in it %d, listed not in it %d), origin (tiles) %s"
              % (os.path.basename(path), best, len(seen & objs), len(seen - objs), org))
        for lp in sorted(acts):
            fl = f28.get(lp, [])
            known = [v for v in fl if v is not None]
            flag = ("f28 not logged" if not known else "rooms with 0x40000: %d of %d" %
                    (sum(1 for v in known if v & 0x40000), len(known)))
            cnt = {"before": 0, "after": 0, "never": 0}
            for o in sorted(seen & objs):
                room = (o[1] // 40, o[2] // 40)
                an = acts[lp].get(room)
                cnt["never" if an is None else ("before" if an < first[o] else "after")] += 1
            print("  copy %d: RL rooms %d, %s; rooms activated %d; listed objects whose room activated in this copy "
                  "before the first listing %d, after it %d, never %d" % (lp, len(fl), flag, len(acts[lp]),
                                                                         cnt["before"], cnt["after"], cnt["never"]))
        for o in sorted(o for o in objs if o[0] == 406):
            room = (o[1] // 40, o[2] // 40)
            print("  chest 406 at %s, room (tiles) %s: first OBJS line %s; RRESEED line per copy %s"
                  % (o[1:], (8 * room[0], 8 * room[1]), first.get(o),
                     {lp: acts[lp].get(room) for lp in sorted(acts)}))


if __name__ == "__main__":
    main()

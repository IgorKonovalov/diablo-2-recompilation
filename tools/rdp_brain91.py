"""The brain chest of level 91 (lane/rdp; items/0010 § H6e2, open question): which of LvlPrest 704's six DS1 files a
session's level 91 used, which of that file's objects the OBJS lines listed (tools/gdb/vendors.py: every object unit
of the server game's lists, game +0x1520, no class or radius filter), and the rooms each built copy of the level
activated (RRESEED). Read-only over kept logs and the merged data tree; no harness.

Usage:
  python3 -I tools/rdp_brain91.py [--root workspace/merged] [--exe workspace/install/app/game.exe] LOG [LOG ...]

Per DS1 file: its class-406 objects (raw DS1 ids mapped through g_Ds1ObjectIds, tools/ds1.py). Per log: how many of
the objects listed inside the level's rect are in each file; for the best file and each level copy, the file's
objects in the copy's activated rooms against the listed ones; and whether the chest's room was activated per copy.
Stdlib only.
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(ROOT, "workspace", "merged"))
    ap.add_argument("--exe", default=os.path.join(ROOT, "workspace", "install", "app", "game.exe"))
    ap.add_argument("logs", nargs="+")
    a = ap.parse_args()
    root, exe = a.root, a.exe
    t = ds1._tables(root)
    objtab = ds1._object_table(exe)
    rec = [r for r in t["lvlprest"] if r["Def"] == 704][0]
    files = {}
    for i in range(1, 7):
        fn = rec["File%d" % i]
        path = None
        for dp, _, fs in os.walk(os.path.join(root, "data", "global", "tiles")):
            for f_ in fs:
                if os.path.join(dp, f_).lower().endswith(fn.lower()):
                    path = os.path.join(dp, f_)
        with open(path, "rb") as fh:
            f = ds1.parse(fh.read())
        files[fn] = {(u["id"], u["x"], u["y"]) for u in ds1._units(f, t, objtab) if u["type"] == 2}
        print("file", fn, "objects", len(files[fn]), "class 406 at", sorted((x, y) for c, x, y in files[fn] if c == 406))
    for path in a.logs:
        rl, act, seen = {}, {}, set()
        org = last = None
        copies = {}
        for l in open(path, errors="replace"):
            tag, _, rest = l.partition(" ")
            if tag == "RL":
                d = json.loads(rest); rl[d["room"]] = (d["level"], d["rect"])
                if d.get("pdef") == 704:
                    org = (min(org[0], d["rect"][0]), min(org[1], d["rect"][1])) if org else (d["rect"][0], d["rect"][1])
            elif tag == "RRESEED":
                d = json.loads(rest)
                if d["room"] in rl:
                    copies.setdefault(d["level"], set()).add(rl[d["room"]][0])
                if d["level"] == 91 and d["room"] in rl:
                    lp, r = rl[d["room"]]
                    act.setdefault(lp, set()).add(((r[0] - org[0]) // 8, (r[1] - org[1]) // 8))
                    last = lp
            elif tag == "OBJS" and org:
                for c, x, y in json.loads(rest)["o"]:
                    rx, ry = x - 5 * org[0], y - 5 * org[1]
                    if 0 <= rx < 200 and 0 <= ry < 200:
                        seen.add((c, rx, ry))
        print(os.path.basename(path), "level origin (tiles)", org, "objects listed in the level's rect", len(seen))
        for fn, objs in files.items():
            print("  %-26s listed and in the file %3d, listed not in the file %3d" % (fn, len(seen & objs), len(seen - objs)))
        best = max(files, key=lambda k: len(seen & files[k]) - len(seen - files[k]))
        objs = files[best]
        for lp, rooms in sorted(act.items()):
            pred = {o for o in objs if (o[1] // 40, o[2] // 40) in rooms}
            print("  copy %d: %d rooms activated; file objects in them %d; listed %d; predicted not listed %d; listed not predicted %d"
                  % (lp, len(rooms), len(pred), len(seen & objs), len(pred - seen), len(seen - pred)))
        c406 = [o for o in objs if o[0] == 406]
        print("  level pointers per level id (RRESEED):", {k: len(v) for k, v in sorted(copies.items())})
        print("  the last level-91 RRESEED names copy %s (d2pilot's default frontier copy at the end of the log)" % last)
        print("  %s: class 406 at %s, room (tiles) %s; listed: %s; that room activated per copy: %s"
              % (best, [o[1:] for o in c406], [(8 * (o[1] // 40), 8 * (o[2] // 40)) for o in c406],
                 any(o in seen for o in c406), {lp: any((o[1] // 40, o[2] // 40) in r for o in c406) for lp, r in act.items()}))


if __name__ == "__main__":
    main()

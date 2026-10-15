"""Build the mercenary save set of plan 0033 Phase 0: one save per hireling class and difficulty.

Usage:
  python3 -I tools/merc_saves.py <excel-dir> <out-dir>

Each save is tools/d2s_recipes/mercnova.json (expansion, on workspace/samples/d2s-owner/smpsor-l50.d2s) or
mercclassic.json (classic, on workspace/runtime/monspawn-chars/cls/smpsor.d2s) with its "merc" replaced: the lowest
Hireling.txt Id of that class and difficulty in the save's Version (100 or 0), name 0, no items, and
exp = Exp/Lvl x L^2 x (L + 1) for L = the lowest Level among that Id's rows. The experience formula is a lead
(docs/tables/Hireling.md), used only to give each mercenary a plausible level. Expansion: classes 271, 338, 359, 561
x difficulties 1..3 (12 saves); classic: 271, 338, 359 x 1..3 (9 saves). Out: <out-dir>/<Name>/<Name>.d2s, one
character per directory (a slot's saves directory takes one), Name = Merc<class><n|m|h>[c]. Prints the sha256 of each.
Stdlib only; writes only under <out-dir>.
"""
import contextlib
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import d2s  # noqa: E402

ROOT = os.path.dirname(HERE)
BASES = {"expansion": os.path.join(ROOT, "workspace", "samples", "d2s-owner", "smpsor-l50.d2s"),
         "classic": os.path.join(ROOT, "workspace", "runtime", "monspawn-chars", "cls", "smpsor.d2s")}
RECIPES = {"expansion": "mercnova.json", "classic": "mercclassic.json"}
CLASSES = {"expansion": ["271", "338", "359", "561"], "classic": ["271", "338", "359"]}
DIFF = {"1": "n", "2": "m", "3": "h"}


def plan(t, game):
    """[(name, merc dict)] for one game."""
    version = "100" if game == "expansion" else "0"
    out = []
    for cls in CLASSES[game]:
        for d in sorted(DIFF):
            rows = [r for r in t.hirelings if r["Class"] == cls and r["Difficulty"] == d and r["Version"] == version]
            hid = min(int(r["Id"]) for r in rows)
            mine = [r for r in rows if int(r["Id"]) == hid]
            lvl = min(int(r["Level"]) for r in mine)
            exp = int(mine[0]["Exp/Lvl"]) * lvl * lvl * (lvl + 1)
            name = "Merc%s%s%s" % (cls, DIFF[d], "c" if game == "classic" else "")
            out.append((name, dict(id=hid, seed=1000 * int(cls) + int(d), name=0, exp=exp, dead=False)))
    return out


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    excel, out = argv
    t = d2s.Tables(excel)
    for game in ("expansion", "classic"):
        with open(os.path.join(HERE, "d2s_recipes", RECIPES[game])) as fh:
            base_rc = json.load(fh)
        for name, merc in plan(t, game):
            rc = dict(base_rc, name=name, merc=merc)
            d = os.path.join(out, name)
            os.makedirs(d, exist_ok=True)
            dst = os.path.join(d, name + ".d2s")
            with contextlib.redirect_stdout(io.StringIO()):
                d2s.build(excel, rc, BASES[game], dst)
            with open(dst, "rb") as fh:
                sha = hashlib.sha256(fh.read()).hexdigest()
            print("%-14s id %2d exp %9d  %s" % (name, merc["id"], merc["exp"], sha))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

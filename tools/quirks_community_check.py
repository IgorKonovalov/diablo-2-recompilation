#!/usr/bin/env python3
"""Plan 0057 Phase 2: the table reads behind docs/findings/quirks/0001-community-bugs.md.
Run from the repo root with python3 -I. Prints no game data beyond the cells each row of the finding names."""
import csv

BASE = "workspace/merged/data/global/excel/"


def rows(name):
    with open(BASE + name, encoding="latin1") as f:
        return list(csv.DictReader(f, delimiter="\t"))


states = {r["state"]: r for r in rows("states.txt")}
for s in ("fade", "blessedaim", "penetrate"):
    print("state", s, "curse=%r" % states[s]["curse"])
for r in rows("skills.txt"):
    if r["skill"] in ("Blessed Aim", "Penetrate"):
        print("skill", r["skill"], "aurastate=%r passivestate=%r" % (r["aurastate"], r["passivestate"]))
props = {r["code"]: r for r in rows("properties.txt")}
runes = rows("runes.txt")
bad = [
    (r.get("Name"), i, r["T1Code%d" % i])
    for r in runes
    for i in range(1, 8)
    if r.get("T1Code%d" % i) and r["T1Code%d" % i] not in props
]
used = sum(1 for r in runes for i in range(1, 8) if r.get("T1Code%d" % i))
print("runes rows", len(runes), "code cells", used, "unknown codes", bad)
print("property reduce-ac stat1 =", props["reduce-ac"]["stat1"])
tc = {r["Treasure Class"]: r for r in rows("treasureclassex.txt")}
for n in ("Andariel", "Mephisto", "Diablo", "Baal", "Duriel - Base"):
    print("tc", n, "Picks", tc[n]["Picks"])
print("itemtypes row 45:", rows("itemtypes.txt")[45]["Code"])

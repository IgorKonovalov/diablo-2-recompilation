#!/usr/bin/env python3
"""Session layouts for plan 0035 Phase 2 (run:2026-10-16-calc): one test character per class, its recipe and the
xdrive steps that open the skill tree and hover every skill of the class (the description evaluates the skilldesc
formulas and, through the variables, the skill formulas).

    python3 -I tools/calc_sessions.py write [CLASS ...]    # tools/d2s_recipes/calc-<cls>.json, calc-<cls>-field.json,
                                                           # tools/gdb/calc-<cls>-hover.steps, calc-<cls>-cast.steps
    python3 -I tools/calc_sessions.py list                 # the class skills with their levels and tree cells

A character is clvl 80 with every skill of its class at a level from a fixed pattern (some 0, so the tree shows an
unlearned skill's first level), with overrides that put the stock ternaries on both sides of their test: the tree
shows the current and the next level, so level 3 shows `lvl < 4` true and false. Base saves are the
smp<cls>.d2s expansion saves; tools/d2s.py build checks the class. The hover steps press `t`, click each tab, and
move the pointer to each skill cell for HOVER seconds (the cell geometry was measured from a screenshot of the
skill tree in the 800x600 window), then open the inventory, hover the potions (stamina, antidote, thawing, elixir:
the misc rows with formula cells) and drink three. The cast steps (outside town) press each hotkey F1..F8 (the
learned non-passive skills with the most formula cells) and right-click three points around the character.
Stdlib only. Writes only the recipe and steps files.
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RECIPES = os.path.join(HERE, "d2s_recipes")
STEPS = os.path.join(HERE, "gdb")
EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")

CLASSES = {"sor": "Sorceress", "nec": "Necromancer", "pal": "Paladin", "dru": "Druid", "ass": "Assassin",
           "ama": "Amazon", "bar": "Barbarian"}
PATTERN = [1, 3, 0, 4, 8, 2, 5, 13, 20, 6]
OVERRIDES = {"Raise Skeleton": 3, "Raise Skeletal Mage": 3, "Zeal": 4, "Fire Wall": 5, "Warmth": 3, "Inferno": 2,
             "Summon Spirit Wolf": 3, "Summon Fenris": 2, "Holy Fire": 4, "Holy Bolt": 3, "Fists of Fire": 3,
             "Blades of Ice": 3, "Royal Strike": 3, "Fire Golem": 4, "Skeleton Mastery": 2, "Sacrifice": 2}
HOVER = 1.0
# skill tree cell centre (window-relative, 800x600): column c (1..3), row r (1..6); tab buttons (pages 1..3)
CELL_X0, CELL_DX, CELL_Y0, CELL_DY = 440, 68, 97, 69
TABS = {1: (675, 430), 2: (675, 325), 3: (675, 215)}
INV_X0, INV_Y0 = 418, 316     # inventory cell (0, 0) top-left, 29 x 29 cells (tooling.md § Inventory actions)


def rows(name):
    with open(os.path.join(EXCEL, name + ".txt"), newline="", encoding="latin-1") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def class_skills(cls):
    desc = {r["skilldesc"]: r for r in rows("skilldesc")}
    out = []
    for k, r in enumerate(x for x in rows("skills") if x["charclass"] == cls):
        d = desc[r["skilldesc"]]
        lvl = OVERRIDES.get(r["skill"], PATTERN[k % len(PATTERN)])
        out.append((r["skill"], lvl, int(d["SkillPage"]), int(d["SkillRow"]), int(d["SkillColumn"])))
    return out


def cast_skills(cls, n=8):
    """The class's learned non-passive skills with the most formula cells in their skills row, at most n, in file
    order: the hotkeys F1..Fn of the cast steps."""
    calc_cols = None
    score = []
    for r in rows("skills"):
        if r["charclass"] != cls or r["passive"] == "1":
            continue
        if calc_cols is None:
            calc_cols = [c for c in r if "calc" in c.lower() or c in ("petmax", "skpoints", "perdelay", "delay")]
        score.append((r["skill"], sum(1 for c in calc_cols if r[c].strip())))
    lv = {name: lvl for name, lvl, *_ in class_skills(cls)}
    best = sorted((x for x in score if lv.get(x[0])), key=lambda x: -x[1])[:n]
    keep = {x[0] for x in best}
    return [name for name, _ in score if name in keep]


POTIONS = ["vps", "yps", "wms", "elx", "vps", "yps", "wms"]


def recipe(cls, field=False):
    sk = class_skills(cls)
    r = {
        "game": "expansion",
        "class": CLASSES[cls],
        "seed": 3500 + list(CLASSES).index(cls),
        "name": "Calc" + cls.capitalize(),
        "stats": {"strength": 100, "energy": 200, "dexterity": 100, "vitality": 300, "hitpoints": 1500,
                  "maxhp": 1500, "mana": 1000, "maxmana": 1000, "stamina": 300, "maxstamina": 300, "level": 80,
                  "experience": 742730244},
        "skills": {name: lvl for name, lvl, *_ in sk if lvl},
        "waypoints": {"normal": "all"},
        "hotkeys": cast_skills(cls),
        "items": [{"code": c, "store": "inventory", "x": k, "y": 0} for k, c in enumerate(POTIONS)],
    }
    if field:
        # the field variant starts in the Act IV town, beside its waypoint (the reference builds' header)
        r.update({"name": r["name"] + "F", "progression": 15, "difficulty": [131, 131, 131], "quests": "all"})
    return r


def cell_xy(row, col):
    return CELL_X0 + (col - 1) * CELL_DX, CELL_Y0 + (row - 1) * CELL_DY


def steps(cls):
    out = ["# plan 0035 Phase 2: open the skill tree and hover every %s skill (tools/calc_sessions.py)" % CLASSES[cls],
           "key t", "sleep 1"]
    for page in (1, 2, 3):
        out += ["click %d %d   # tab %d" % (TABS[page][0], TABS[page][1], page), "sleep 0.5"]
        for name, lvl, p, r, c in class_skills(cls):
            if p == page:
                x, y = cell_xy(r, c)
                out += ["move %d %d   # %s (level %d)" % (x, y, name, lvl), "sleep %.1f" % HOVER]
        out += ["shot workspace/logs/calc-%s-tab%d.png" % (cls, page)]
    out += ["key t", "sleep 0.5", "key i", "sleep 1"]
    for k, code in enumerate(POTIONS):
        x, y = INV_X0 + 29 * k + 14, INV_Y0 + 14
        out += ["move %d %d   # inventory (%d, 0) %s" % (x, y, k, code), "sleep %.1f" % HOVER]
    for k in range(4, len(POTIONS)):
        out += ["rclick %d %d   # drink the %s at (%d, 0)" % (INV_X0 + 29 * k + 14, INV_Y0 + 14, POTIONS[k], k),
                "sleep 1"]
    out += ["shot workspace/logs/calc-%s-inv.png" % cls, "key i", "sleep 0.5"]
    return "\n".join(out) + "\n"


def cast_steps(cls):
    """Outside town: each hotkey, then right clicks around the character (window centre 400, 270)."""
    out = ["# plan 0035 Phase 2: cast the %s's hotkey skills (tools/calc_sessions.py)" % CLASSES[cls]]
    for k, name in enumerate(cast_skills(cls)):
        out += ["key F%d   # %s" % (k + 1, name), "sleep 0.4"]
        for x, y in ((520, 230), (300, 330), (480, 360)):
            out += ["rclick %d %d" % (x, y), "sleep 0.9"]
    out += ["shot workspace/logs/calc-%s-cast.png" % cls]
    return "\n".join(out) + "\n"


def main(argv):
    if not argv or argv[0] not in ("write", "list"):
        print(__doc__)
        return 2
    sel = argv[1:] or list(CLASSES)
    if argv[0] == "list":
        for cls in sel:
            for name, lvl, p, r, c in class_skills(cls):
                print(cls, name, lvl, "page %d row %d col %d" % (p, r, c))
        return 0
    for cls in sel:
        path = os.path.join(RECIPES, "calc-%s.json" % cls)
        with open(path, "w") as fh:
            json.dump(recipe(cls), fh, indent=2)
            fh.write("\n")
        print(path)
        path = os.path.join(RECIPES, "calc-%s-field.json" % cls)
        with open(path, "w") as fh:
            json.dump(recipe(cls, True), fh, indent=2)
            fh.write("\n")
        print(path)
        if CELL_DX:
            path = os.path.join(STEPS, "calc-%s-hover.steps" % cls)
            with open(path, "w") as fh:
                fh.write(steps(cls))
            print(path)
            path = os.path.join(STEPS, "calc-%s-cast.steps" % cls)
            with open(path, "w") as fh:
                fh.write(cast_steps(cls))
            print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

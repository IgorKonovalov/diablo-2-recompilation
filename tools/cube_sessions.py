#!/usr/bin/env python3
"""Session layouts for plan 0030 Phase 2 (run:2026-10-15-cube): one test character per session, its recipe and its
transmute plan.

    python3 -I tools/cube_sessions.py write [NAME ...]     # tools/d2s_recipes/cube-<name>.json and
                                                           # tools/gdb/cube-<name>.plan (every session, or the named)
    python3 -I tools/cube_sessions.py list                 # the sessions: game, difficulty, level, transmutes

A session is a character (game, level, difficulty, quest bits) and a list of steps. Every input starts in the
inventory (packed around the Horadric Cube at inventory (8, 2)), so the plan (tools/d2pilot.py cube tokens) opens
the inventory and the cube, then for each step moves the step's items from their inventory cells into the cube
(packed in the cube's 3 x 4 grid), presses Transmute, and then:
  - "out": the step is expected to produce one item: it is picked up at the cube's bottom-right corner (where
    the placement puts it, run:2026-10-15-cube calibration) and put into input 1's
    inventory cells;
  - "back": nothing is expected: the items go back to their inventory cells;
  - "keep": nothing is expected and the items stay in the cube for the next step (whose items are added to them);
  - "gone": a special output (the cow portal) is expected: the inputs are destroyed and nothing is placed.
The expectation only steers the clicks; tools/cube.py decides from the log what happened. A step's items are recipe
item entries of tools/d2s.py build (code, suffix, rare, unique, ilvl, sockets, ...), without placement.
Stdlib only. Writes only the recipe and plan files.
"""
import argparse
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin  # noqa: E402

RECIPES = os.path.join(HERE, "d2s_recipes")
PLANS = os.path.join(HERE, "gdb")
EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
INV_W, INV_H, CUBE_W, CUBE_H = 10, 4, 3, 4
CUBE_AT = (8, 2)

# experience to reach level L: experience.txt row L - 1 (Sorceress column)
EXP = None


def exp_for(level):
    global EXP
    if EXP is None:
        rows = open(excel_bin.find_file(EXCEL, "experience", ".txt")).read().splitlines()
        EXP = {}
        for r in rows[2:]:
            c = r.split("\t")
            if c[0].isdigit():
                EXP[int(c[0])] = int(c[2])
    return 0 if level <= 1 else EXP[level - 1]


SIZES = None


def size(code):
    global SIZES
    if SIZES is None:
        SIZES = {}
        for t in ("weapons", "armor", "misc"):
            rows = open(excel_bin.find_file(EXCEL, t, ".txt"), encoding="latin1").read().splitlines()
            head = rows[0].split("\t")
            ci, wi, hi = head.index("code"), head.index("invwidth"), head.index("invheight")
            for r in rows[1:]:
                c = r.split("\t")
                if len(c) > hi and c[ci]:
                    SIZES[c[ci]] = (int(c[wi] or 1), int(c[hi] or 1))
    return SIZES[code]


def item_code(it):
    if "code" in it:
        return it["code"]
    if it.get("unique") == "The Stone of Jordan":
        return "rin"
    raise ValueError("item %r: give code" % it)


class Grid:
    def __init__(self, w, h, blocked=()):
        self.w, self.h = w, h
        self.cells = set(blocked)

    def fits(self, x, y, w, h):
        if x + w > self.w or y + h > self.h:
            return False
        return all((x + i, y + j) not in self.cells for i in range(w) for j in range(h))

    def put(self, x, y, w, h):
        for i in range(w):
            for j in range(h):
                self.cells.add((x + i, y + j))

    def take(self, x, y, w, h):
        for i in range(w):
            for j in range(h):
                self.cells.discard((x + i, y + j))

    def place(self, w, h):
        """First fit, column by column (x outer), so tall items pack into columns."""
        for x in range(self.w):
            for y in range(self.h):
                if self.fits(x, y, w, h):
                    self.put(x, y, w, h)
                    return x, y
        return None


def S(code, **kw):
    d = dict(code=code)
    d.update(kw)
    return d


def MAG(code, sfx=53, **kw):
    return S(code, suffix=sfx, **kw)


def RARE(code, names=(160, 121), **kw):
    return S(code, rare=list(names), **kw)


SOJ = {"unique": "The Stone of Jordan"}
JEW = MAG("jew", 260)
GEMS = {"amethyst": "gcv gfv gsv gzv gpv", "sapphire": "gcb gfb gsb glb gpb", "emerald": "gcg gfg gsg glg gpg",
        "ruby": "gcr gfr gsr glr gpr", "diamond": "gcw gfw gsw glw gpw", "topaz": "gcy gfy gsy gly gpy",
        "skull": "skc skf sku skl skz"}


def R(n):
    return S("r%02d" % n)


def step(items, then="out", note="", out=None):
    return dict(items=items, then=then, note=note, out=out)


# crafted rings and amulets, all four families: (row, magic base code, rune, gem)
CRAFT_JEWELRY = [(71, "rin", 11, "gpb"), (70, "amu", 10, "gpb"), (80, "rin", 12, "gpr"), (79, "amu", 11, "gpr"),
                 (89, "rin", 11, "gpv"), (88, "amu", 8, "gpv"), (98, "rin", 11, "gpg"), (97, "amu", 10, "gpg")]


def craft_steps(ilvls, start=0):
    out = []
    for k, il in enumerate(ilvls):
        row, base, rune, gem = CRAFT_JEWELRY[(start + k) % len(CRAFT_JEWELRY)]
        out.append(step([MAG(base, ilvl=il), dict(JEW), R(rune), S(gem)], note="row %d crafted %s" % (row, base)))
    return out


PERFECT = ["gpv", "gpb", "gpg", "gpr", "gpw", "gpy", "skz"]


def reroll_steps(bases):
    out = []
    for k, b in enumerate(bases):
        g = [PERFECT[(k + i) % len(PERFECT)] for i in range(3)]
        out.append(step([b] + [S(x) for x in g], note="row 60 magic reroll %s" % b["code"]))
    return out


SESSIONS = {}


def session(name, steps, game="expansion", level=80, diff=0, quest_bits=None, extra=None, note=""):
    SESSIONS[name] = dict(name=name, steps=steps, game=game, level=level, diff=diff, quest_bits=quest_bits or [],
                          extra=extra or {}, note=note)


def gem_up(color, grade):
    """3 gems of a grade -> 1 of the next (rows 23..50)."""
    c = GEMS[color].split()[grade]
    return step([S(c), S(c), S(c)], note="gem upgrade %s x3" % c)


RUNE_UP = {k: (3, None) for k in range(1, 10)}                  # rows 51..59: 3 runes
RUNE_UP.update({10: (3, "gcy"), 11: (3, "gcv"), 12: (3, "gcb"), 13: (3, "gcr"), 14: (3, "gcg"), 15: (3, "gcw"),
                16: (3, "gfy"), 17: (3, "gfv"), 18: (3, "gfb"), 19: (3, "gfr"), 20: (3, "gfg"), 21: (2, "gfw"),
                22: (2, "gsy"), 23: (2, "gsv"), 24: (2, "gsb"), 25: (2, "gsr"), 26: (2, "gsg"), 27: (2, "gsw"),
                28: (2, "gly"), 29: (2, "glv"), 30: (2, "glb"), 31: (2, "glr"), 32: (2, "glg")})


def rune_up(n):
    k, g = RUNE_UP[n]
    return step([R(n)] * k + ([S(g)] if g else []), note="rune upgrade r%02d%s" % (n, " (ladder row)" if n >= 14 else ""))


def define():
    if SESSIONS:
        return SESSIONS
    # calibration: one of each output family
    session("cal", [
        step([S("gcv"), S("gcv"), S("gcv")], note="row 23 gem upgrade"),
        step([R(1), R(1), R(1)], note="row 51 rune upgrade"),
        step([MAG("rin", ilvl=30), S("gpv"), S("gpb"), S("gpg")], note="row 60 magic reroll"),
        step([MAG("rin", ilvl=40), dict(JEW), R(11), S("gpb")], note="row 71 crafted ring"),
        step([S("gcr"), S("gcr")], then="back", note="no row: two chipped rubies"),
    ], note="calibration")
    # crafted rings and amulets, all four families, character levels 80, 80, 20, 99, 50 (ilvl tiers 1..4)
    session("craft1", craft_steps([1, 41, 99, 20, 60, 80, 30, 50, 70], 0), level=80)
    session("craft2", craft_steps([99, 10, 45, 75, 25, 65, 5, 90, 35], 1), level=80)
    session("craft3", craft_steps([1, 20, 40, 50, 60, 70, 80, 99, 30], 2), level=20)
    session("craft4", craft_steps([1, 30, 50, 60, 70, 80, 90, 99, 45], 3), level=99)
    session("craft5", craft_steps([10, 30, 50, 60, 70, 85, 99, 40, 20], 4), level=50)
    # crafted gear: gloves, boots, belt, helm (the `upg` inputs)
    session("craftgear", [
        step([MAG("mgl", ilvl=60), dict(JEW), R(9), S("gpb")], note="row 66 hit power gloves"),
        step([MAG("tbt", ilvl=40), dict(JEW), R(5), S("gpr")], note="row 74 blood boots"),
        step([MAG("vbl", ilvl=80), dict(JEW), R(6), S("gpv")], note="row 85 caster belt"),
        step([MAG("crn", ilvl=99), dict(JEW), R(6), S("gpg")], note="row 91 safety helm"),
        step([MAG("hlm", ilvl=20), dict(JEW), R(8), S("gpr")], note="row 73 blood helm"),
    ], level=80)
    # magic rerolls (row 60): magic rings, amulets, jewels and small charms
    bases = [MAG("rin", ilvl=1), MAG("amu", ilvl=25), MAG("jew", 260, ilvl=50), MAG("cm1", 256, ilvl=75),
             MAG("rin", ilvl=99), MAG("amu", ilvl=60), MAG("jew", 260, ilvl=10), MAG("cm1", 256, ilvl=40),
             MAG("rin", ilvl=85)]
    session("reroll1", reroll_steps(bases))
    session("reroll2", reroll_steps(bases[3:] + bases[:3]))
    session("reroll3", reroll_steps(bases[6:] + bases[:6]), level=40)
    # forced prefixes: the Prismatic amulet (row 6, pre=331) and the four rings (rows 7..10)
    session("forced", [
        step([MAG("amu", ilvl=30)] + [S(g) for g in ("gpv", "gpy", "gpb", "gpg", "gpr", "gpw")], note="row 6 prismatic"),
        step([MAG("rin", ilvl=30), S("gpr"), S("opm")], note="row 7 garnet ring"),
        step([MAG("rin", ilvl=50), S("gpb"), S("wms")], note="row 8 cobalt ring"),
        step([MAG("rin", ilvl=70), S("gpy"), S("rvs")], note="row 9 coral ring"),
        step([MAG("rin", ilvl=90), S("gpg"), S("yps")], note="row 10 jade ring"),
        step([MAG("rin", ilvl=10), S("gpr"), S("opm")], note="row 7 garnet ring"),
        step([MAG("rin", ilvl=20), S("gpb"), S("wms")], note="row 8 cobalt ring"),
        step([MAG("rin", ilvl=40), S("gpy"), S("rvs")], note="row 9 coral ring"),
    ])
    # rare rerolls: six perfect skulls (row 61) and skull + Stone of Jordan (row 62)
    session("rare1", [step([RARE("rin", ilvl=50)] + [S("skz")] * 6, note="row 61 rare reroll"),
                      step([RARE("amu", (171, 135), ilvl=80)] + [S("skz")] * 6, note="row 61 rare reroll"),
                      step([RARE("jew", ilvl=20)] + [S("skz")] * 6, note="row 61 rare reroll")] +
            [step([RARE(b, ilvl=il), S("skz"), dict(SOJ)], note="row 62 rare reroll")
             for b, il in (("rin", 30), ("amu", 60), ("jew", 90), ("rin", 99), ("amu", 5))])
    session("rare2", [step([RARE(b, ilvl=il)] + [S("skz")] * 6, note="row 61 rare reroll")
                      for b, il in (("amu", 40), ("rin", 70), ("jew", 99), ("rin", 10))] +
            [step([RARE(b, ilvl=il), S("skz"), dict(SOJ)], note="row 62 rare reroll")
             for b, il in (("jew", 45), ("rin", 75))], level=60)
    # gem and rune upgrades (the ladder rows 104.. among them)
    session("upg1", [gem_up(c, g) for c, g in (("amethyst", 0), ("sapphire", 1), ("emerald", 2), ("ruby", 3),
                                               ("diamond", 0), ("topaz", 1), ("skull", 2), ("skull", 3),
                                               ("ruby", 0), ("emerald", 3), ("diamond", 2), ("topaz", 3))])
    session("upg2", [rune_up(n) for n in (1, 2, 5, 9, 10, 13, 14, 17, 21, 32)])
    # socket recipes: the rune recipes on a body armour, a helm, a shield and a weapon (rows 123..126), the gem
    # recipes on weapons (15, 16, 147) and the rare socket (63)
    session("sock1", [
        step([S("aar", ilvl=60), R(7), R(10), S("gpy")], note="row 123 socketed torso"),
        step([S("ghm", ilvl=60), R(8), R(10), S("gpb")], note="row 125 socketed helm"),
        step([S("kit", ilvl=60), R(7), R(11), S("gpr")], note="row 126 socketed shield"),
    ])
    session("sock2", [
        step([S("qui", ilvl=30), R(7), R(10), S("gpy")], note="row 123 socketed torso"),
        step([S("cap", ilvl=30), R(8), R(10), S("gpb")], note="row 125 socketed helm"),
        step([S("sml", ilvl=30), R(7), R(11), S("gpr")], note="row 126 socketed shield"),
        step([S("ssd", ilvl=50), R(8), R(11), S("gpv")], note="row 124 socketed weapon"),
    ])
    session("sock3", [
        step([S("crs", ilvl=60), R(8), R(11), S("gpv")], note="row 124 socketed weapon"),
        step([S("gth", ilvl=60), R(7), R(10), S("gpy")], note="row 123 socketed torso"),
        step([S("crn", ilvl=60), R(8), R(10), S("gpb")], note="row 125 socketed helm"),
    ])
    session("sock4", [
        step([S("ssd", ilvl=40, sockets=2), S("gsv"), S("gsb"), S("gsg")], note="row 15 socketed weapon + 3 gems"),
        step([MAG("ssd", 382, ilvl=40), S("gzv"), S("glb"), S("glg")], note="row 16 magic weapon + 3 flawless"),
        step([MAG("ssd", 382, ilvl=40), S("gcv"), S("gcb"), S("gcg")], note="row 147 magic weapon + 3 chipped"),
        step([RARE("amu", ilvl=60), S("skz"), S("skz"), S("skz"), dict(SOJ)], note="row 63 rare + socket"),
        step([RARE("rin", ilvl=60), S("skz"), S("skz"), S("skz"), dict(SOJ)], note="row 63 rare + socket"),
    ])
    # transmutes that match no row
    session("nomatch", [
        step([S("gcv"), S("gcv")], then="keep", note="no row: two chipped amethysts"),
        step([S("gcr")], then="keep", note="no row: two chipped amethysts and a chipped ruby"),
        step([S("gcv")], then="back", note="no row: three chipped amethysts and a chipped ruby (an extra item)"),
        step([MAG("rin")], then="back", note="no row: a magic ring alone"),
        step([S("rin"), S("gpv"), S("gpb"), S("gpg")], then="back", note="no row: a normal ring and three perfect gems"),
        step([RARE("rin")] + [S("skz")] * 5, then="back", note="no row: a rare ring and five perfect skulls"),
        step([R(1), R(1)], then="back", note="no row: two El"),
        step([R(14), R(14), R(14)], then="back", note="no row: three Hel without the chipped emerald"),
        step([S("amu"), dict(JEW), R(11), S("gpb")], then="back", note="no row: crafting with a normal amulet"),
        step([S("leg"), S("isc")], then="back", note="no row: Wirt's Leg and an Identify scroll"),
        step([S("gcv"), S("gcv"), S("gcv"), S("gcv")], then="back", note="no row: four chipped amethysts"),
    ])
    # the cow portal: open (Baal killed, Cow King alive), then refused once open in this game; the Pandemonium rows
    session("cowopen", [
        step([S("leg"), S("tbk", tome=0, quantity=20)], then="gone", note="row 2 cow portal: opens"),
        step([S("leg"), S("tbk", tome=0, quantity=20)], then="back", note="row 2 cow portal: one per game"),
        step([S("pk1"), S("pk2"), S("pk3")], then="back", note="row 148 Pandemonium key: nothing produced"),
        step([S("dhn"), S("bey"), S("mbr")], then="back", note="row 149 Pandemonium finale: nothing produced"),
        step([S("tes"), S("ceh"), S("bet"), S("fed")], note="row 150 Token of Absolution"),
    ], extra={"quests": "all"}, quest_bits=[["normal", 4, 10, 0]])
    session("cowking", [
        step([S("leg"), S("tbk", tome=0, quantity=20)], then="back", note="row 2: the Cow King killed (word 4 bit 10)"),
    ], extra={"quests": "all"}, quest_bits=[["normal", 4, 10, 1]])
    session("cowbaal", [
        step([S("leg"), S("tbk", tome=0, quantity=20)], then="back", note="row 2: Baal not killed (word 40 bit 0)"),
    ], extra={"quests": "all"}, quest_bits=[["normal", 4, 10, 0], ["normal", 40, 0, 0]])
    session("cownm", [
        step([S("leg"), S("tbk", tome=0, quantity=20)], then="back", note="row 2 in Nightmare, a Normal leg: no row"),
        step([S("leg", item_stats={"356": 1}), S("tbk", tome=0, quantity=20)], then="gone",
             note="row 2 in Nightmare, stat 356 = 1: opens"),
    ], diff=1, extra={"quests": "all"}, quest_bits=[["nightmare", 4, 10, 0]])
    session("cowhell", [
        step([S("leg", item_stats={"356": 1}), S("tbk", tome=0, quantity=20)], then="back",
             note="row 2 in Hell, stat 356 = 1: no row"),
        step([S("leg", item_stats={"356": 2}), S("tbk", tome=0, quantity=20)], then="gone",
             note="row 2 in Hell, stat 356 = 2: opens"),
    ], diff=2, extra={"quests": "all"}, quest_bits=[["hell", 4, 10, 0]])
    # classic: version-0 rows, and an expansion row refused
    session("classic", [
        gem_up("amethyst", 0), gem_up("ruby", 1), gem_up("skull", 0),
        step([S("rvs"), S("rvs"), S("rvs")], note="row 5 three small rejuvenations"),
        step([MAG("rin", ilvl=20), MAG("rin", ilvl=40), MAG("rin", ilvl=60)], note="row 13 three rings -> amulet"),
        step([MAG("rin", ilvl=30), S("gpr"), S("opm")], note="row 7 garnet ring"),
        step([MAG("rin", ilvl=50), S("gpv"), S("gpb"), S("gpg")], then="back", note="row 60 (version 100): refused"),
        step([RARE("rin", ilvl=50)] + [S("skz")] * 6, note="row 61 rare reroll"),
        step([S("hax"), S("dgr")], note="row 11 throwing axe"),
    ], game="classic", level=50)
    return SESSIONS


# ---------------------------------------------------------------- layout and plan

def layout(sess):
    """Pack every step's items into the inventory; returns (recipe items, plan tokens)."""
    inv = Grid(INV_W, INV_H)
    inv.put(CUBE_AT[0], CUBE_AT[1], 2, 2)
    items = [dict(code="box", store="inventory", x=CUBE_AT[0], y=CUBE_AT[1])]
    placed = []                      # per step: [(item, (x, y, w, h))]
    for st in sess["steps"]:
        row = []
        for it in st["items"]:
            w, h = size(item_code(it))
            at = inv.place(w, h)
            if at is None:
                raise SystemExit("%s: the inventory is full at step %r" % (sess["name"], st["note"]))
            e = copy.deepcopy(it)
            e.update(store="inventory", x=at[0], y=at[1])
            items.append(e)
            row.append((it, (at[0], at[1], w, h)))
        placed.append(row)
    toks = ["key:i", "rclick:inv:%d,%d,2,2" % CUBE_AT, "sleep:1",
            "shot:workspace/logs/cube-%s-open.png" % sess["name"]]
    cube = Grid(CUBE_W, CUBE_H)
    in_cube = []                     # (item, cube footprint, inventory footprint) kept from a "keep" step
    for k, (st, row) in enumerate(zip(sess["steps"], placed)):
        toks.append("# step %d: %s" % (k + 1, st["note"]))
        for it, (x, y, w, h) in row:
            at = cube.place(w, h)
            if at is None:
                raise SystemExit("%s: the cube is full at step %r" % (sess["name"], st["note"]))
            toks.append("mv:inv:%d,%d,%d,%d>cube:%d,%d,%d,%d" % (x, y, w, h, at[0], at[1], w, h))
            in_cube.append((it, (at[0], at[1], w, h), (x, y, w, h)))
        toks.append("tm")
        if st["then"] == "out":
            # the output, placed at the bottom-right corner of the emptied cube, goes back to input 1's inventory cells (the
            # panels cover the whole window, so there is no floor to drop it on); its size is the step's "out"
            # code's, else input 1's (usetype, useitem and every fixed-code output of the sessions fit)
            x, y, w, h = in_cube[0][2]
            ow, oh = size(st["out"]) if st.get("out") else (w, h)
            if ow > w or oh > h:
                raise SystemExit("%s: output %dx%d does not fit input 1's %dx%d at step %r" % (
                    sess["name"], ow, oh, w, h, st["note"]))
            toks.append("mv:cube:%d,%d,%d,%d>inv:%d,%d,%d,%d" % (CUBE_W - ow, CUBE_H - oh, ow, oh, x, y, ow, oh))
            cube = Grid(CUBE_W, CUBE_H)
            in_cube = []
        elif st["then"] == "gone":
            # a special output: the inputs are destroyed and nothing is placed
            cube = Grid(CUBE_W, CUBE_H)
            in_cube = []
        elif st["then"] == "back":
            for it, (cx, cy, w, h), (x, y, _, _) in in_cube:
                toks.append("mv:cube:%d,%d,%d,%d>inv:%d,%d,%d,%d" % (cx, cy, w, h, x, y, w, h))
            cube = Grid(CUBE_W, CUBE_H)
            in_cube = []
    toks.append("shot:workspace/logs/cube-%s-end.png" % sess["name"])
    return items, toks


def recipe(sess, items):
    base = json.load(open(os.path.join(RECIPES, "cubeclassic.json" if sess["game"] == "classic" else "cubecraft.json")))
    r = {k: v for k, v in base.items() if k != "items"}
    r["name"] = "Cube" + "".join(p.capitalize() for p in sess["name"].replace("-", " ").split())[:11]
    r["seed"] = 743100000 + sum(ord(c) * (i + 1) for i, c in enumerate(sess["name"]))
    r["stats"] = dict(r["stats"], level=sess["level"], experience=exp_for(sess["level"]))
    d = [0, 0, 0]
    d[sess["diff"]] = 128
    r["difficulty"] = d
    if sess["quest_bits"]:
        r["quest_bits"] = sess["quest_bits"]
    r.update(sess["extra"])
    r["items"] = items
    return r


def cmd_write(names):
    define()
    for name in names or sorted(SESSIONS):
        s = SESSIONS[name]
        items, toks = layout(s)
        rp = os.path.join(RECIPES, "cube-%s.json" % name)
        with open(rp, "w") as f:
            json.dump(recipe(s, items), f, indent=2)
            f.write("\n")
        pp = os.path.join(PLANS, "cube-%s.plan" % name)
        with open(pp, "w") as f:
            f.write("# tools/d2pilot.py cube --plan for tools/d2s_recipes/cube-%s.json (tools/cube_sessions.py)\n" % name)
            for t in toks:
                f.write(t + "\n")
        print("%s: %d steps, %d items -> %s, %s" % (name, len(s["steps"]), len(items), os.path.relpath(rp),
                                                      os.path.relpath(pp)))
    return 0


def cmd_list():
    define()
    for name, s in sorted(SESSIONS.items()):
        print("%-10s %-9s diff %d level %2d  %2d steps  %s" % (name, s["game"], s["diff"], s["level"], len(s["steps"]),
                                                             s["note"]))
        for st in s["steps"]:
            print("    %-5s %s" % (st["then"], st["note"]))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(prog="cube_sessions.py")
    ap.add_argument("cmd", choices=("write", "list"))
    ap.add_argument("names", nargs="*")
    ns = ap.parse_args(argv[1:])
    return cmd_write(ns.names) if ns.cmd == "write" else cmd_list()


if __name__ == "__main__":
    sys.exit(main(sys.argv))

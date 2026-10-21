#!/usr/bin/env python3
"""Seed to world: the reviewed models composed, with no boundary oracle inside the chain (plan 0048 Phase 1).

    python3 -I tools/chain.py gen --seed N [--diff 0|1|2] [--exp 0|1] [--excel DIR] [--levels ID,...] [--json]
    python3 -I tools/chain.py check <log> [<log> ...] [--excel DIR] [--root DIR] [--staff model|oracle] [--cf NAME] [-v]
    python3 -I tools/chain.py barrier <log> [<log> ...]        # oracle 20 probe: the LG0 barrier grids

gen: everything the game builds from the game seed alone, before any input of the chain (docs/findings/chain/0001
  § 3.1 and § 3.3): under `-seed N` the game seed and the map seed (rng/seeds step 1: Init(N), map seed N), the four
  game-seed draws of game creation (draw 1 the monster regions, tools/monpool.py build_all for the difficulty and game
  type; draw 2 the object-region seed O = Init(low); draw 3 the store seed; draw 4 the quest seed), each act's seed and
  levelSeedBase (tools/rng.py act_seeds) and each level's create seed Init(levelSeedBase + id). The level layouts, the
  activations and the populations need the activation order (an input, chain/0001 § 3.2): `check` replays them on a
  log that carries that order.

check: per log, the composition on the line sets the log carries (each sub-model is the reviewed tool, run with every
  oracle the plan retires switched to its model):
    * item lines (tools/gdb/affixes.gdb, props*.gdb, items-chain.gdb): tools/items_chain.py (affixes, props or both,
      by the line sets present) with ITEMS_RollStaffMods modelled (oracle 2, `--staff model`, the default);
    * TC lines (TCR .. TCEND, in the world logs that load tools/gdb/tc-drops.gdb): tools/tc.py replay with the quality
      roll modelled, every call to its TCEND seed (oracle 6: an object's drop; tools/objects.py takes the object's
      unit seed at OCX, which this predicts);
    * world lines (an RW1 or P0 line: tools/gdb/mon-spawn.gdb and its successors, objects.gdb): tools/monspawn.py's
      checker, which runs tools/drlg.py gen and roomk and tools/objects.py on the same log, then the population pass,
      with the unit seed SUnitCreate leaves predicted (oracle 14: MonRegionFindAdd on the tracked regions, then
      MonStatsInit's draws); then tools/monstats.py's SI checks on logs that carry SI lines;
  and prints, per oracle of docs/findings/chain/0001 § 2 still taken from a log, the count (the remaining oracles).
  Exit 0 only if every sub-check passes.

Stdlib only. Read-only.
"""
import argparse
import collections
import io
import json
import os
import re
import sys
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import affixes  # noqa: E402
import items_chain  # noqa: E402
import monpool  # noqa: E402
import rng  # noqa: E402

DEFAULT_EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
DEFAULT_ROOT = os.path.join(os.path.dirname(HERE), "workspace", "merged")


# --- gen ------------------------------------------------------------------------------------------------------------
def game_seeds(n):
    """rng/seeds step 1 (override branch) and step note 7a: the game seed Init(N) and its four creation draws."""
    s = (n & rng.MASK, rng.INIT_HIGH)
    out = {"game_seed": s, "map_seed": n & rng.MASK}
    names = ("monster_regions", "object_region", "store", "quest")
    for name in names:
        s = rng.step(*s)
        out[name] = (s[0], rng.INIT_HIGH)          # each is Init(low of the draw)
    out["game_seed_after_creation"] = s
    return out


def gen(n, diff, exp, excel, levels=None):
    g = game_seeds(n)
    T = monpool.Tables(excel)
    acts = []
    for a in range(5):
        base, lo, hi, t94, t484, bit = rng.act_seeds(n, a)
        acts.append({"act": a + 1, "levelSeedBase": base, "act_seed_after": (lo, hi),
                     "tombs": (t94, t484) if a == 1 else None, "bit474": bit if a == 2 else None})
    regs = {lid: reg for lid, reg, _ in monpool.build_all(T, g["monster_regions"][0], diff, exp)}
    lv = []
    for lid in sorted(regs):
        if levels and lid not in levels:
            continue
        reg = regs[lid]
        act = reg["act"]
        base = acts[act]["levelSeedBase"] if 0 <= act < 5 else None
        lv.append({"id": lid, "act": act + 1, "seed": (((base + lid) & rng.MASK), rng.INIT_HIGH) if base is not None else None,
                   "pool": [e[0] for e in reg["ents"]], "rarity": [e[1] for e in reg["ents"]],
                   "den": reg["den"], "umin": reg["umin"], "umax": reg["umax"], "mlvl": reg["mlvl"][0]})
    return g, acts, lv


def fmt(s):
    return "%08x:%08x" % tuple(s)


def cmd_gen(ns):
    levels = {int(x) for x in ns.levels.split(",")} if ns.levels else None
    g, acts, lv = gen(ns.seed, ns.diff, ns.exp, ns.excel, levels)
    if ns.json:
        def enc(x):
            if isinstance(x, tuple):
                return fmt(x)
            raise TypeError(x)
        print(json.dumps({"seed": ns.seed, "diff": ns.diff, "exp": ns.exp,
                          "game": {k: (fmt(v) if isinstance(v, tuple) else v) for k, v in g.items()},
                          "acts": acts, "levels": lv}, default=enc, sort_keys=True))
        return 0
    print("seed %d  difficulty %d  expansion %d" % (ns.seed, ns.diff, ns.exp))
    print("game seed %s  map seed %08x" % (fmt(g["game_seed"]), g["map_seed"]))
    for k in ("monster_regions", "object_region", "store", "quest"):
        print("  draw %-16s Init -> %s" % (k, fmt(g[k])))
    print("  game seed after creation %s" % fmt(g["game_seed_after_creation"]))
    for a in acts:
        extra = ""
        if a["tombs"]:
            extra = "  tombs %d %d" % a["tombs"]
        if a["bit474"] is not None:
            extra = "  +0x474 %d" % a["bit474"]
        print("act %d  levelSeedBase %08x  act seed after the act draws %s%s" % (a["act"], a["levelSeedBase"],
                                                                                fmt(a["act_seed_after"]), extra))
    for r in lv:
        print("level %3d act %d  seed %s  mlvl %3d  den %4d  uniques %d-%d  pool %s" % (
            r["id"], r["act"], fmt(r["seed"]) if r["seed"] else "-", r["mlvl"], r["den"], r["umin"], r["umax"],
            ",".join(map(str, r["pool"]))))
    return 0


# --- check ----------------------------------------------------------------------------------------------------------
CREATIONS = re.compile(r"^(chain: )?(\d+) creations reproduced, (\d+) failed")
# an item line set counts only in a log with an item creation (IC0): a world log can carry a short tag of the same name
AFFIX_TAGS = {"AF0", "AFC", "RN", "RC", "SUPD", "LOWR", "APR0"}     # the split of items/experiments.md (2026-10-15)
PROPS_TAGS = {"APE", "SLOT", "WR", "ROLL", "IIS0", "EVD"}


def line_sets(path):
    """Which of the composition's line sets the log carries."""
    aff = props = world = ic = False
    for line in open(path, errors="replace"):
        tag = line.split(" ", 1)[0]
        if tag == "IC0":
            ic = True
        if tag in AFFIX_TAGS:
            aff = True
        elif tag in PROPS_TAGS:
            props = True
        elif tag in ("RW1", "P0"):
            world = True
        if aff and props and world and ic:
            break
    return aff and ic, props and ic, world


class NS:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def run_quiet(fn, *a):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fn(*a)
    return rc, buf.getvalue()


def check_items(path, ns, R):
    aff, props, _ = line_sets(path)
    if not (aff or props):
        return None
    affixes.STAFF_MODEL = ns.staff == "model"
    sub = "both" if aff and props else ("affixes" if aff else "props")
    ins = NS(logs=[path], excel=ns.excel, verbose=False, staff=ns.staff)
    fn = {"affixes": items_chain.cmd_affixes, "props": items_chain.cmd_props, "both": items_chain.cmd_both}[sub]
    rc, out = run_quiet(fn, ins)
    if ns.verbose or rc:
        sys.stdout.write(out)
    first = True
    for line in out.splitlines():
        s = line.strip()
        m = CREATIONS.match(s)
        if m and sub != "props" and first and not s.startswith("chain:"):
            first = False
            R["items: creations reproduced from the affix lines (property roll and staff mods modelled)"] += int(m.group(2))
            R["items: creations failed from the affix lines"] += int(m.group(3))
        elif m and m.group(1):
            R["items: creations reproduced from the property lines (builders and staff mods modelled)"] += int(m.group(2))
            R["items: creations failed from the property lines"] += int(m.group(3))
        if s.startswith("staff mods exit seeds predicted (STF1)"):
            R["oracle 2 retired: staff-mods exit seeds predicted (STF1)"] += int(s.rsplit(None, 1)[1])
        if s.startswith("staff mods vs LX: 107 entries predicted"):
            R["oracle 2 retired: item_singleskill (107) entries predicted at LX"] += int(s.rsplit(None, 1)[1])
        if s.startswith("staff mods: exit not checkable"):
            R["ORACLE 2: staff mods exit taken (props builders)"] += int(s.rsplit(None, 1)[1])
    if ns.staff != "model":
        R["ORACLE 2: ITEMS_RollStaffMods taken from the log (--staff oracle)"] += 1
    return rc


# the counters of tools/monspawn.py (and tools/objects.py inside it) that say an oracle was retired
WORLD_PRED = ("unit seeds after SUnitCreate predicted", "region snapshots equal to the tracked region",
              "presets / restore / objects window predicted by tools/objects.py", "preset monsters",
              "windows RW1 -> RW4", "predicted by the collision model (presets window)",
              "preset tile units", "requests of ", "seed of another room")


class World:
    """The world part: tools/monspawn.py's checker (DRLG gen and roomk, tools/objects.py's window, the population
    pass, the special monsters), then tools/monstats.py's SI checks on logs that carry them (no second monspawn run)."""

    def __init__(self, ns):
        import monspawn
        import monstats
        self.monspawn, self.monstats = monspawn, monstats
        self.c = monspawn.Checker(ns.excel, ns.root, False)
        self.ms = None
        self.ns = ns

    def run(self, path):
        f0 = self.c.fail
        rc, out = run_quiet(self.c.run, path)
        if self.ns.verbose or self.c.fail > f0:
            sys.stdout.write(out)
        bad = self.c.fail > f0
        if any(line.startswith("SI0 ") for line in open(path, errors="replace")):
            if self.ms is None:
                self.ms = self.monstats.Checker(self.ns.excel, False)
            m0 = self.ms.fail
            rc, out = run_quiet(self.ms.run, path)
            if self.ms.fail > m0:
                sys.stdout.write(out)
                bad = True
        return 1 if bad else 0

    def summary(self, R):
        c = self.c
        for k, v in c.stats.items():
            if k.startswith(WORLD_PRED):
                R["world: " + k] += v
        for k, v in c.obj_grid.items():
            R["world: objects grid: " + k] += v
        for k, v in c.obj_stats.items():
            if k.startswith(("gold drops", "object drops")):
                R["world: objects: " + k] += v
        for k, v in c.oracles.items():
            R["ORACLE (world): " + k] += v
        for k, v in c.obj_oracles.items():
            R["ORACLE (objects window): " + k] += v
        # plan 0048 Phase 2: room populations end to end from the game seed with no seed oracle in the window or the
        # pass, by (difficulty, expansion); the populated end-to-end rooms that do not count, by reason
        for pth, ln, lid, room, df, ex, n in c.populated_clean:
            R["world: room populations end to end with no oracle (diff %d exp %d)" % (df, 1 if ex else 0)] += 1
            R["world: room populations end to end with no oracle"] += 1
            R["world: creations in those populations"] += n
            LEVELS.add((lid, df, 1 if ex else 0))
        for k, v in c.populated_unclean.items():
            R["world: populated end-to-end rooms that do not count (%s)" % k] += v
        for (cls, lid, src), v in sorted(c.unit_seed_taken.items()):
            R["ORACLE 14 remainder: unit seed taken, class %d level %d, appended by %s%s" % (
                cls, lid, src, creation_context(src))] += v
        R["world: specials: uniques and minion packs (pass and MonPlace 2)"] += len(c.uniques)
        R["world: specials: champion packs"] += len(c.champions)
        for k, v in c.stats.items():
            if k.startswith(("special mods rolls predicted", "superunique")):
                R["world: specials: " + k] += v
        for k, v in c.obj_stats.items():
            if k.startswith("objects created"):
                R["world: objects: " + k] += v
        r3 = getattr(getattr(c, "world", None), "r3", None)
        if r3:
            R["oracle 20: R3 pass rooms"] += r3["rooms"]
            R["oracle 20: R3 rooms exact"] += r3["rooms_exact"]
            R["oracle 20: R3 rooms with a residue"] += r3["rooms_resid"]
            for k, v in r3["resid_bits"].items():
                R["oracle 20: R3 residue cells, snapshot/model bits %s" % k] += v
            O20.extend(r3.get("per_room", []))
        R["world: monspawn checks"] += c.checks
        R["world: monspawn mismatches"] += c.fail
        R["world: creations"] += len(c.creations)
        if self.ms is not None:
            R["world: monstats checks"] += self.ms.checks
            R["world: monstats mismatches"] += self.ms.fail
            for k, v in self.ms.n.items():
                if k.startswith("MonEquip seed oracle"):
                    R["ORACLE (world): monstats " + k] += v
                elif k.startswith("MonEquipInit"):
                    R["oracle 13: monstats " + k] += v


CF = {
    # counterfactual models (negative controls): each must FAIL on logs where its rule decides
    "findadd-none": "oracle 14: MonRegionFindAdd returns no entry (no append, no variant draws)",
    "monprop-off": "oracle 14: MonStatsInit without its MonProp slots",
    "L0": "oracle 14: the MonLvl column set L = 0 (a control that must NOT fail: L does not change the draw count)",
    "lcv-off": "oracle 16: the MonPlace fixed rows without LevelClassVariant and PresetFallenVariant",
    "overlay-off": "oracle 16: the presets-window predicates on the activation model without the window's marks",
    "state-stale": "oracle 21: another room's seed from its activation seed only (its passes and windows ignored)",
    "i46-stored": "oracle 17: InitFn 46's direction draw stored like the others (one OD line per step)",
    "monequip-off": "oracle 13: MonEquipInit draws nothing on the unit seed (no location pick)",
    "recreation-off": "plan 0048 Phase 2 run 2: a revisit re-creation makes no marks in the objects grid",
}


def apply_cf(name):
    import mon_sweep
    import monspawn
    import monstats
    if name == "findadd-none":
        mon_sweep.findadd = lambda T, reg, cls, s: ("none", None)
    elif name == "monprop-off":
        monstats.Model.monprop = lambda self, seed, cls, d: ({}, [])
    elif name == "L0":
        monspawn.GAME_L = 0
    elif name == "lcv-off":
        monspawn.PresetMonPass.level_class_variant = lambda self, cls: cls
        monspawn.PresetMonPass.fallen_variant = lambda self, cls: cls
    elif name == "state-stale":
        class Frozen(dict):
            def __setitem__(self, k, v):
                if k not in self:
                    dict.__setitem__(self, k, v)
        monspawn.STATE_FROZEN = Frozen
    elif name == "i46-stored":
        import objects
        objects.Seed.draw_unstored = objects.Seed.draw
    elif name == "monequip-off":
        monstats.Model.monequip = lambda self, seed, cls, lvl: 0
    elif name == "overlay-off":
        monspawn.PresetMonPass.overlay = lambda self: self.chk.world.model
    elif name == "recreation-off":
        import objects
        objects.MonTables.recreation_marks = lambda self, room, x, y, cls, mode: []


def barrier_pred_ok(fl, o):
    """LOGIC_BarrierGridBuild 0x0066C870's tile test: flags (+0x14) & 0x1C000 = 0x4000, orientation (+0x1C) not 15,
    flag bit 11 clear."""
    return (fl & 0x1C000) == 0x4000 and o != 15 and not (fl >> 11) & 1


def cmd_barrier(ns):
    """Oracle 20, the barrier grid (a probe, not part of `check`): every LG0 barrier grid of the logs (tools/gdb/
    collision.py, before LOGIC_FloodAll) against LOGIC_BarrierGridBuild as read, on the wall entries of the room's
    last activation dump (CB): the room's own walls at their tile, the near rooms' walls at their tile relative to the
    room when inside its tile rect (bounds included, sub_0066B9D0_RectContainsIncl)."""
    from collision import unz
    c = collections.Counter()
    for path in ns.logs:
        cb = {}
        for line in open(path, errors="replace"):
            tag, _, rest = line.partition(" ")
            if tag == "CB":
                d = json.loads(rest)
                cb[d["dr"]] = d
            elif tag == "LG0":
                d = json.loads(rest)
                bar = unz(d["z"])["barrier"]
                if bar is None or bar[2] is None:
                    c["LG0 with no barrier grid logged"] += 1
                    continue
                b = cb.get(d["dr"])
                if b is None:
                    c["LG0 of a room with no activation dump (CB) in the log"] += 1
                    continue
                tx, ty, tw, th = d["t"]
                W, H = bar[0], bar[1]
                g = [[0] * W for _ in range(H)]
                for n, ndr, trect, walls, _f, _s in unz(b["z"])["near"]:
                    for x, y, fl, _tp, o in walls:
                        if not barrier_pred_ok(fl, o):
                            continue
                        if n == b["room"]:
                            rx, ry = x, y
                        else:
                            ax, ay = x + trect[0], y + trect[1]
                            if not (tx <= ax <= tx + tw and ty <= ay <= ty + th):
                                continue
                            rx, ry = ax - tx, ay - ty
                        if 0 <= rx < W and 0 <= ry < H:
                            g[ry][rx] = 1
                diff = [(x, y) for y in range(H) for x in range(W) if (1 if bar[2][y][x] else 0) != g[y][x]]
                if not diff:
                    c["LG0 barrier grids equal to the model"] += 1
                else:
                    edge = all(x in (0, W - 1) or y in (0, H - 1) for x, y in diff)
                    c["LG0 barrier grids that differ (%s)" % ("on the grid's edge only" if edge else "inside")] += 1
    for k in sorted(c):
        print("  %-80s %d" % (k, c[k]))
    return 0


TOWNS = {1, 40, 75, 103, 109}          # sub_006426A0_LevelIsTown


def gate_inputs(path, R):
    """Oracle 19 (plan 0048 Phase 1, in part): the OG line's DRLG inputs of OBJ_PopulateGate 0x00552560 against the
    reading: closed by flags & 0x30000 (sub_0066BB60) before anything else; pop = 0 when the DRLG room has 0x800000,
    else the room's level id (sub_0066BB20, the same field as sub_0066BAB0_RoomLevelId); the preset test only for a
    type-1 room (sub_0066BA90: +0x20 -> +0x54 & 0x80); the town test LevelIsTown(level id). What the reading does not
    give (which rooms carry 0x30000, 0x800000 or the out room's 0x80, and LevelRoomCount) stays logged."""
    for line in open(path, errors="replace"):
        if not line.startswith("OG "):
            continue
        d = json.loads(line[3:])
        if d.get("f"):
            R["oracle 19: gates closed by the room flags 0x30000 (no pop read: %s)" % ("ok" if "pop" not in d else "WRONG")] += 1
            continue
        pop = d.get("pop")
        R["oracle 19: pop is 0 or the room's level id: %s" % (pop in (0, d["lid"]))] += 1
        if pop:
            if "town" in d:
                R["oracle 19: town test equals LevelIsTown(level id): %s" % (bool(d["town"]) == (d["lid"] in TOWNS))] += 1
            if "pre" in d:
                R["oracle 19: preset test value in {0, 0x80}: %s" % (d["pre"] in (0, 0x80))] += 1


TC_STATE = {}
LEVELS = set()        # (level id, difficulty, expansion) with an oracle-free room population
O20 = []              # oracle 20: the R3 residue per pass room (tools/collision.py r3_check)
INPUT_TAGS = ("SN", "LG0", "NWW", "OG", "TCR", "QKMF", "QOMF", "QMF", "PLR", "AROOM")


BUILT = set()         # (level id, DrlgType, difficulty, expansion) built by the server (LI0 client 0) in a checked log


def act_of(lid):
    return 1 if lid < 40 else 2 if lid < 75 else 3 if lid < 103 else 4 if lid < 109 else 5


def levels_built(path):
    de, ids = None, set()
    for line in open(path, errors="replace"):
        if line.startswith("LI0 "):
            d = json.loads(line[4:])
            if not d.get("client"):
                ids.add((d["id"], d["drlg"]))
        elif de is None and line.startswith("P0 "):
            d = json.loads(line[3:])
            de = (d["diff"], 1 if d["exp"] else 0)
    if de is not None:
        for lid, k in ids:
            BUILT.add((lid, k, de[0], de[1]))


def count_inputs(path, R):
    """Plan 0048 Phase 2: the input lines (oracle 20's SN, LG0 and NWW; oracle 19's OG with its LevelRoomCount
    reads; the drops' game seed (TCR gseed) and the killer's / summon owner's magic find (QKMF, QOMF, QMF); the
    player's activations), counted."""
    for line in open(path, errors="replace"):
        tag = line.split(" ", 1)[0]
        if tag in INPUT_TAGS:
            R["input lines: %s" % tag] += 1
            if tag == "OG" and '"cnt"' in line:
                R["oracle 19: LevelRoomCount reads (OG cnt)"] += 1
            elif tag == "TCR" and " gseed=" in line:
                R["input: game seed at a drop (TCR gseed)"] += 1


LOGDIRS = []


def creation_context(src):
    """For an appender 'LOG MU line N ...': where the creation ran, from the last scope line before it (within 2 000
    lines): an object's InitFn (OI0), operate (OO0) or trap event (TT0), or the room driver's window (RW1: the presets
    window, up to RW2; RW2..RW4: the restore and objects window) or the population pass (P0)."""
    m = re.match(r"(\S+) MU line (\d+)", src)
    if not m:
        return ""
    path = next((p for p in LOGDIRS if os.path.basename(p) == m.group(1)), None)
    if path is None:
        return ""
    n = int(m.group(2))
    last = None
    for k, line in enumerate(open(path, errors="replace"), 1):
        if k >= n:
            break
        if k >= n - 2000 and line.startswith(("OI0 ", "OO0 ", "TT0 ", "RW1 ", "RW2 ", "RW4 ", "P0 ", "PX ")):
            last = (k, line)
    if last is None:
        return " (no scope line in the 2 000 lines before)"
    k, line = last
    tag = line.split(" ", 1)[0]
    d = json.loads(line.split(" ", 1)[1])
    what = {"OI0": "InitFn %s of object class %s" % (d.get("fn"), d.get("cls")),
            "OO0": "OperateFn %s of object class %s" % (d.get("fn"), d.get("cls")),
            "TT0": "trap event fn %s" % d.get("fn"),
            "RW1": "the presets window (RW1 -> RW2)", "RW2": "the restore / objects window (RW2 -> RW4)",
            "RW4": "after the objects window, before the pass", "P0": "the population pass", "PX": "after a pass"}[tag]
    return " in %s (%s line %d)" % (what, tag, k)


def o20_attribute(recs):
    """Oracle 20: for every object-bit cell (0x400) of the R3 residue that no window mark explains, the nearest line
    before the snapshot that names it: a CM mark whose rectangle covers the cell (the last before the snapshot), else
    the last object creation (OU0) within 4 sub-tiles of it; else the cell is listed unexplained."""
    out = []
    by_path = collections.defaultdict(list)
    for r in recs:
        if r["objcells"]:
            by_path[r["path"]].append(r)
    for path, rs in by_path.items():
        lines = open(path, errors="replace").readlines()
        for r in rs:
            for x, y, snap, model in r["objcells"]:
                best = None
                for j in range(min(r["ln"], len(lines)) - 1, -1, -1):
                    ln = lines[j]
                    if ln.startswith("CM "):
                        d = json.loads(ln[3:])
                        if d.get("m", 0) & 0x400 and d["x"] <= x < d["x"] + d.get("a", 1) and d["y"] <= y < d["y"] + d.get("b", 1):
                            best = ("CM", j + 1, d)
                            break
                if best is None:
                    for j in range(min(r["ln"], len(lines)) - 1, -1, -1):
                        ln = lines[j]
                        if ln.startswith("OU0 "):
                            d = json.loads(ln[4:])
                            if abs(d.get("x", 1 << 30) - x) <= 4 and abs(d.get("y", 1 << 30) - y) <= 4:
                                best = ("OU0", j + 1, d)
                                break
                out.append({"log": os.path.basename(path), "sn_line": r["ln"], "room": r["room"], "x": x, "y": y,
                            "snapshot": "%04x" % snap, "model": "%04x" % model,
                            "nearest": None if best is None else {"tag": best[0], "line": best[1], "d": best[2]}})
    return out


def check_tc(path, ns, R):
    """Every TC_ResolveDrops call of the log (TCR .. TCEND, tools/gdb/tc-drops.gdb) through tools/tc.py with the
    quality roll modelled (oracle 5 already retired): for an object's drop (oracle 6) this is the resolver
    tools/objects.py no longer needs as an oracle."""
    if not any(line.startswith("TCR ") for line in open(path, errors="replace")):
        return None
    import quality
    import tc
    if "T" not in TC_STATE:
        TC_STATE["T"] = tc.Tables(ns.excel)
        TC_STATE["q"] = (quality.Tables(ns.excel), 0, False)
    calls = tc.read_calls(path)
    res, out = run_quiet(lambda: tc.replay_calls(TC_STATE["T"], calls, TC_STATE["q"], False))
    ok, bad = res[0], res[1]
    nobj = sum(1 for call0, _err in calls if call0 and call0[0][0] == "TCR" and call0[0][1].get("stype") == "2")
    R["tc: TC_ResolveDrops calls reproduced (quality modelled)"] += ok
    R["tc: TC_ResolveDrops calls failed"] += bad
    R["tc: of them with an object source (stype 2)"] += nobj
    # plan 0048 Phase 2: the drops of a dying unit (stype 1), with the items each made (TCEND count)
    for call0, _err in calls:
        if not call0 or call0[0][0] != "TCR":
            continue
        st = call0[0][1].get("stype")
        end = [kv for h, kv in call0 if h == "TCEND"]
        n = int(end[-1].get("count", 0)) if end and end[-1] else 0
        if st == "1":
            R["tc: drops of a dying monster (stype 1)"] += 1
            if n > 0:
                R["tc: drops of a dying monster with at least one item"] += 1
                R["tc: items made by those drops"] += n
    if bad:
        sys.stdout.write(out)
    return 1 if bad else 0


def cmd_check(ns):
    if ns.cf:
        apply_cf(ns.cf)
        print("counterfactual: %s" % CF[ns.cf])
    R = collections.Counter()
    bad = 0
    world = None
    LOGDIRS.extend(ns.logs)
    for path in ns.logs:
        rcs = []
        rc = check_items(path, ns, R)
        if rc is not None:
            rcs.append(("items", rc))
        if line_sets(path)[2]:
            if world is None:
                world = World(ns)
            rcs.append(("world", world.run(path)))
            gate_inputs(path, R)
            count_inputs(path, R)
            levels_built(path)
            rc = check_tc(path, ns, R)
            if rc is not None:
                rcs.append(("tc", rc))
        if not rcs:
            R["logs with no line set of the composition"] += 1
            print("%s: no line set of the composition (no creation, no room window)" % os.path.basename(path))
            continue
        for what, rc in rcs:
            if rc:
                bad += 1
                print("FAIL %s: %s" % (os.path.basename(path), what))
        print("%s: %s" % (os.path.basename(path), ", ".join("%s %s" % (w, "ok" if not r else "FAIL") for w, r in rcs)
                           or "nothing to check"))
    if world is not None:
        world.summary(R)
    if world is not None:
        R["world: levels with an oracle-free room population"] = len(LEVELS)
        R["world: (level, difficulty) pairs with an oracle-free room population"] = len({(a, b) for a, b, _ in LEVELS})
    if BUILT:
        R["levels built (level, difficulty, game type)"] = len({(a, c, d) for a, _, c, d in BUILT})
        for k in (1, 2, 3):
            R["levels built (level, difficulty, game type), DrlgType %d" % k] = len({(a, c, d) for a, kk, c, d in BUILT
                                                                                       if kk == k})
        for c in (0, 1, 2):
            for d in (0, 1):
                acts = sorted({act_of(a) for a, _, cc, dd in BUILT if (cc, dd) == (c, d)})
                if acts:
                    R["levels built: difficulty %d game type %d: acts %s" % (c, d, "".join(map(str, acts)))] = len(
                        {a for a, _, cc, dd in BUILT if (cc, dd) == (c, d)})
    if ns.o20 and world is not None:
        att = o20_attribute(O20)
        for a in att:
            R["oracle 20: object-bit residue cells %s" % ("with a nearest line (%s)" % a["nearest"]["tag"]
                                                          if a["nearest"] else "unexplained")] += 1
        with open(ns.o20, "w") as fh:
            json.dump({"per_room": [{k: v for k, v in r.items()} for r in O20], "objcells": att,
                       "levels": sorted(LEVELS), "built": sorted(BUILT)}, fh, indent=0, sort_keys=True)
    print("== chain summary ==")
    for k in sorted(R):
        print("  %-90s %d" % (k, R[k]))
    print("chain: %d logs, %d sub-checks failed" % (len(ns.logs), bad))
    return 1 if bad else 0


def build_parser():
    ap = argparse.ArgumentParser(prog="chain.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen")
    g.add_argument("--seed", type=int, required=True)
    g.add_argument("--diff", type=int, default=0, choices=(0, 1, 2))
    g.add_argument("--exp", type=int, default=1, choices=(0, 1))
    g.add_argument("--excel", default=DEFAULT_EXCEL)
    g.add_argument("--levels")
    g.add_argument("--json", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("logs", nargs="+")
    c.add_argument("--excel", default=DEFAULT_EXCEL)
    c.add_argument("--root", default=DEFAULT_ROOT)
    c.add_argument("--staff", choices=("model", "oracle"), default="model",
                   help="ITEMS_RollStaffMods: the model (default, oracle 2 retired) or the plan 0021 seed oracle")
    b = sub.add_parser("barrier")
    b.add_argument("logs", nargs="+")
    c.add_argument("--cf", choices=sorted(CF), help="a counterfactual model (negative control)")
    c.add_argument("--o20", help="write oracle 20's residue per pass room, its object-bit cells with the nearest line "
                                 "before the snapshot, and the levels with an oracle-free population (JSON) here")
    c.add_argument("-v", "--verbose", action="store_true")
    return ap


def main(argv):
    ns = build_parser().parse_args(argv[1:])
    return {"gen": cmd_gen, "check": cmd_check, "barrier": cmd_barrier}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

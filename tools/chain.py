#!/usr/bin/env python3
"""Seed to world: the reviewed models composed, with no boundary oracle inside the chain (plan 0048 Phase 1).

    python3 -I tools/chain.py gen --seed N [--diff 0|1|2] [--exp 0|1] [--excel DIR] [--levels ID,...] [--json]
    python3 -I tools/chain.py check <log> [<log> ...] [--excel DIR] [--root DIR] [--staff model|oracle] [-v]

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
    * world lines (an RW1 or P0 line: tools/gdb/mon-spawn.gdb and its successors, objects.gdb): tools/monspawn.py's
      checker, which runs tools/drlg.py gen and roomk and tools/objects.py on the same log, then the population pass;
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
AFFIX_TAGS = {"AF0", "AFC", "RN", "RC", "SUPD", "LOWR", "APR0"}     # the split of items/experiments.md (2026-10-15)
PROPS_TAGS = {"APE", "SLOT", "WR", "ROLL", "IIS0", "EVD"}


def line_sets(path):
    """Which of the composition's line sets the log carries."""
    aff = props = world = False
    for line in open(path, errors="replace"):
        tag = line.split(" ", 1)[0]
        if tag in AFFIX_TAGS:
            aff = True
        elif tag in PROPS_TAGS:
            props = True
        elif tag in ("RW1", "P0"):
            world = True
        if aff and props and world:
            break
    return aff, props, world


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


def cmd_check(ns):
    R = collections.Counter()
    bad = 0
    for path in ns.logs:
        rcs = []
        rc = check_items(path, ns, R)
        if rc is not None:
            rcs.append(("items", rc))
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
    c.add_argument("-v", "--verbose", action="store_true")
    return ap


def main(argv):
    ns = build_parser().parse_args(argv[1:])
    return {"gen": cmd_gen, "check": cmd_check}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

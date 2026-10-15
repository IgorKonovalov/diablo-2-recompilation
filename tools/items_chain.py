#!/usr/bin/env python3
"""Chain tools/affixes.py and tools/props.py so that neither keeps the other's part as a seed oracle.

    python3 -I tools/items_chain.py affixes <log> [<log> ...] [--excel DIR] [-v]   # logs with the affix lines
    python3 -I tools/items_chain.py props <log> [<log> ...] [--excel DIR] [-v]     # logs with the property lines

affixes: tools/affixes.py check, with its ItemApplyProps boundary oracle (APR0 -> APR1) replaced by tools/props.py's
  table model of the call (props.apply_seed: the block walk of the affix or QualityItems row, every PROP_RollValue
  draw on the item seed). The logged APR1 seed is compared with the model's, no longer taken. Everything else is
  affixes.py's own check (ITEMS_RollStaffMods, the ethereal and socket rolls stay its boundary oracles).

props: tools/props.py check first (unchanged: base stats, every ItemApplyProps call between APE and APX, ethereal,
  sockets, the final lists). Then, per creation, the builders tools/props.py takes as seed oracles (magic, rare,
  superior, low, normal, and the automagic pick after the join) are run by tools/affixes.py's model with no log
  lines (Walk(free=True)), from the logged builder entry seed (BLD) and, for the automagic pick, from the item seed
  after the socket roll (SOKX, else ETHX, else ICJ); each ItemApplyProps call inside goes through props.apply_seed.
  Compared with the log: the sequence of ItemApplyProps calls (mode, affix id or QualityItems row, entry seed) with
  the logged APE lines of that builder; the builder's success (a failed builder is followed by another BLD, a
  successful one by the join); and the seed at the join (ICJ) or, for the automagic pick, at the return (ICX).
  A builder on a type with StaffMods ends in ITEMS_RollStaffMods, which these logs do not bracket: its calls are
  compared, its exit seed is not (counted as "staff mods: exit not checkable").

Neither run logs both line sets (no log has AF* and APE lines), so each direction is checked on its own run; see
docs/findings/items/experiments.md (re-analysis of 2026-10-15). Exit 0 only if everything reproduces. Stdlib only.
Read-only.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import affixes  # noqa: E402
import props  # noqa: E402
import uniques  # noqa: E402

fmt = uniques.fmt
seedpair = uniques.seedpair


def make_hook(PT):
    def hook(mode, rec, seed, it):
        try:
            return props.apply_seed(PT, mode, rec, seed, it.cls, it.ilvl, it.ver, it.q)
        except props.Mismatch as e:
            raise affixes.Mismatch("props model: %s" % e)
    return hook


def cmd_affixes(ns):
    affixes.PROPS_HOOK = make_hook(props.Tables(ns.excel))
    return affixes.cmd_check(ns)


def free_builder(AT, ic, k, q, seed, stats, auto=False):
    """Run one builder (or the automagic pick) of tools/affixes.py with no log lines. Returns (ok, apr, exit seed or
    None when ITEMS_RollStaffMods ends it on a StaffMods type)."""
    it = affixes.Item(AT, ic)
    it.q = q
    W = affixes.Walk(AT, [], it, stats, collections.defaultdict(list), "chain", free=True)
    W.seed = seed
    W.rare_info = None
    try:
        ok = W.automagic() if auto else getattr(W, affixes.BUILDERS[k])()
    except affixes.StaffModsUnmodelled:
        return True, W.apr, None
    return bool(ok), W.apr, W.seed


def check_creation(AT, blk, S):
    ic = blk[0][1]
    ev = blk[1:]
    apes = [(i, d) for i, (t, d) in enumerate(ev) if t == "APE"]
    used = set()

    def match(apr, lo, hi, what):
        """The model's ItemApplyProps calls against the APE lines with index in [lo, hi)."""
        logged = [(i, d) for i, d in apes if lo <= i < hi]
        affixes.eq("%s: ItemApplyProps calls" % what, len(apr), len(logged))
        for (mode, rec, seed, w), (i, d) in zip(apr, logged):
            affixes.eq("%s: %s mode" % (what, w), mode, d["mode"])
            if mode == 0:
                affixes.eq("%s: %s affix id" % (what, w), rec, d["aid"])
            affixes.eq("%s: %s entry seed" % (what, w), seed, d["seed"])
            used.add(i)
            S["ItemApplyProps calls predicted (affix model -> APE)"] += 1

    bld = [(i, d) for i, (t, d) in enumerate(ev) if t == "BLD" and d["k"] != "normalcase"]
    j = next(i for i, (t, _) in enumerate(ev) if t == "ICJ")
    for n, (i, d) in enumerate(bld):
        k = d["k"]
        nxt = bld[n + 1][0] if n + 1 < len(bld) else j
        if k in ("unique", "set"):
            continue
        ok, apr, out = free_builder(AT, ic, k, d["q"], seedpair(d["seed"]), S)
        match(apr, i, nxt, "builder %s" % k)
        affixes.eq("builder %s succeeded (next line)" % k, ok, nxt == j)
        S["builders run by the affix model: %s" % k] += 1
        if out is None:
            S["staff mods: exit not checkable"] += 1
        elif ok:
            affixes.eq("seed at the join after %s" % k, fmt(out), ev[j][1]["seed"])
            S["join seeds predicted (ICJ)"] += 1
    # the automagic pick after the join
    q = ev[j][1]["q"]
    if ic["ver"] >= 100 and q not in (5, 7) and AT.b(ic["cls"])["auto"]:
        start = ev[j][1]["seed"]
        x = None
        for t, d in ev[j + 1:]:
            if t in ("ETHX", "SOKX"):
                start = d["seed"]
            if t == "ICX":
                x = d
                break
        ok, apr, out = free_builder(AT, ic, None, q, seedpair(start), S, auto=True)
        xi = next(i for i, (t, _) in enumerate(ev) if t == "ICX")
        match(apr, j, len(ev), "automagic")
        S["automagic picks run by the affix model"] += 1
        affixes.eq("seed at the return after the automagic pick (ICX)", fmt(out), x["seed"])
        S["return seeds predicted after the automagic pick (ICX)"] += 1
        del xi
    left = [i for i, _ in apes if i not in used and i < j]
    S["APE lines of unique/set builders (props.py's own walk)"] += len(left)


def cmd_props(ns):
    rc = props.cmd_check(ns)
    print("== tools/items_chain.py: the affix model on the property logs ==")
    AT = affixes.Tables(ns.excel)
    affixes.PROPS_HOOK = make_hook(props.Tables(ns.excel))
    S = collections.Counter()
    ok = bad = 0
    for path in ns.logs:
        for kind, x in props.read_log(path):
            if kind != "IC":
                continue
            blk = x[0]
            ic = blk[0][1]
            if not any(t == "ICJ" for t, _ in blk) or ic.get("rest") or ic.get("q") is None:
                S["creations without a join (skipped)"] += 1
                continue
            try:
                check_creation(AT, blk, S)
                ok += 1
            except (affixes.Mismatch, props.Mismatch, KeyError, IndexError, TypeError, StopIteration) as e:
                bad += 1
                print("FAIL %s IC0 %s: %s" % (os.path.basename(path), json.dumps(ic)[:200], e))
    for k in sorted(S):
        print("  %-66s %d" % (k, S[k]))
    print("chain: %d creations reproduced, %d failed" % (ok, bad))
    return 1 if (rc or bad) else 0


def main(argv):
    ap = argparse.ArgumentParser(prog="items_chain.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("affixes", "props"):
        p = sub.add_parser(name)
        p.add_argument("logs", nargs="+")
        p.add_argument("--excel", default=uniques.EXCEL)
        p.add_argument("-v", "--verbose", action="store_true")
    ns = ap.parse_args(argv[1:])
    return cmd_affixes(ns) if ns.cmd == "affixes" else cmd_props(ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

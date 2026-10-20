#!/usr/bin/env python3
"""Chain tools/affixes.py and tools/props.py so that neither keeps the other's part as a seed oracle.

    python3 -I tools/items_chain.py affixes <log> [<log> ...] [--excel DIR] [-v]   # logs with the affix lines
    python3 -I tools/items_chain.py props <log> [<log> ...] [--excel DIR] [-v]     # logs with the property lines
    python3 -I tools/items_chain.py both <log> [<log> ...] [--excel DIR] [-v]      # logs with both line sets

affixes: tools/affixes.py check, with its ItemApplyProps boundary oracle (APR0 -> APR1) replaced by tools/props.py's
  table model of the call (props.apply_seed: the block walk of the affix or QualityItems row, every PROP_RollValue
  draw on the item seed). The logged APR1 seed is compared with the model's, no longer taken. Everything else is
  affixes.py's own check (the ethereal and socket rolls stay its boundary oracles; ITEMS_RollStaffMods is modelled by
  default since plan 0048 Phase 1, `--staff oracle` restores the plan 0021 oracle).

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

both: logs of tools/gdb/items-chain.gdb, which carry both line sets (plan 0027 Phase 3). Runs "affixes" and then
  "props" on the same logs, so every creation is checked twice: once from the affix lines with the property roll
  modelled (no APR1 seed taken), once from the property lines with the builders modelled (no APE entry seed taken).
  Then counts, per creation (IC0 .. ICX), what the two passes covered together: creations with both line sets, those
  with an affix or QualityItems pick whose ItemApplyProps call is checked from both sides (end to end: AF*/SUPD
  lines and the SLOT/ROLL/WR lines of the same call, no seed from the log in between), and the superior ethereal
  items with a `dur%` slot (func 13). The counts are printed only as a summary; the pass/fail is the two checks'.

The logs of run:2026-10-14-affixes and run:2026-10-14-props carry one line set each, so "affixes" and "props" check
each direction on its own run; see docs/findings/items/experiments.md (re-analysis of 2026-10-15). Exit 0 only if
everything reproduces. Stdlib only. Read-only.
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


def free_builder(AT, ic, k, q, seed, stats, auto=False, forced=None):
    """Run one builder (or the automagic pick) of tools/affixes.py with no log lines. Returns (ok, apr, exit seed or
    None when ITEMS_RollStaffMods ends it on a StaffMods type). forced: the creation record's (prefixes, suffixes)
    (the cube's pre=/suf=; zeros on a drop)."""
    it = affixes.Item(AT, ic)
    it.q = q
    if forced:
        it.fp, it.fs = list(forced[0]), list(forced[1])
    W = affixes.Walk(AT, [], it, stats, collections.defaultdict(list), "chain", free=True)
    W.seed = seed
    W.rare_info = None
    try:
        ok = W.automagic() if auto else getattr(W, affixes.BUILDERS[k])()
    except affixes.StaffModsUnmodelled:
        return True, W.apr, None
    free_builder.staff = getattr(W, "staff_out", None)
    return bool(ok), W.apr, W.seed


def check_creation(AT, blk, S, forced=None):
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
    staff = []                  # STAFF_MODEL: the predicted item_singleskill (107) writes of the builders, in order
    for n, (i, d) in enumerate(bld):
        k = d["k"]
        nxt = bld[n + 1][0] if n + 1 < len(bld) else j
        if k in ("unique", "set"):
            continue
        free_builder.staff = None
        ok, apr, out = free_builder(AT, ic, k, d["q"], seedpair(d["seed"]), S, forced=forced)
        if free_builder.staff:
            staff += free_builder.staff
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
    if affixes.STAFF_MODEL:
        check_staff_lx(ev, staff, S)


def check_staff_lx(ev, staff, S):
    """STAFF_MODEL (plan 0038 batch S2b): the item_singleskill (107) entries of the final main list (LX, state 0)
    against the staff-mods writes the model predicts (STATLIST_SetStat, so the last write of a skill wins). Compared
    only when no PROP_WriteStat call of the creation wrote stat 107 (WR), so that every 107 entry is a staff mod."""
    lx = [d for t, d in ev if t == "LX"]
    if not lx:
        return
    if any(t == "WR" and d.get("stat") == 107 for t, d in ev):
        S["staff mods vs LX: not compared (a property wrote stat 107)"] += 1
        return
    got = {}
    for st, fl, ents in lx[0].get("sub", []):
        if st == 0:
            for stat, param, v in ents:
                if stat == 107:
                    got[param] = v
    want = {}
    for skill, level in staff:
        want[skill] = level
    affixes.eq("item_singleskill (107) entries at LX (staff mods model)", sorted(want.items()), sorted(got.items()))
    S["staff mods vs LX: 107 lists compared"] += 1
    if want:
        S["staff mods vs LX: items with staff-mod entries, predicted"] += 1
        S["staff mods vs LX: 107 entries predicted"] += len(want)


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


AFFIX_SIDE = {"AF0", "AFC", "AFX", "AFR", "RN0", "RN", "RNX", "RC", "APR0", "APR1", "STF0", "STF1", "SUPD", "SUPT",
              "LOWR", "ETB0", "ETB1", "SCK0", "SCK1"}
PROPS_SIDE = {"APE", "SLOT", "SLOTR", "ROLL", "ROLLR", "WR", "EVD", "APX", "ETH0", "ETHR", "ETHX", "SOK0", "SOKM",
              "SOKR", "SSET", "SOKX"}


def both_blocks(path):
    """The lines of each creation, IC0 to ICX, as (tag, dict) (single game thread: the drop path)."""
    cur = None
    for line in open(path, errors="replace"):
        tag, _, rest = line.rstrip("\n").partition(" ")
        if not rest.startswith("{"):
            continue
        if tag == "IC0":
            cur = []
        if cur is None or not (tag in AFFIX_SIDE or tag in PROPS_SIDE or tag in ("IC0", "ICJ", "ICX", "BLD")):
            continue
        try:
            cur.append((tag, json.loads(rest)))
        except ValueError:
            continue
        if tag == "ICX":
            yield cur
            cur = None


def both_counts(logs):
    S = collections.Counter()
    for path in logs:
        for blk in both_blocks(path):
            tags = {t for t, _ in blk}
            S["creations (IC0 .. ICX)"] += 1
            if not (tags & AFFIX_SIDE and tags & PROPS_SIDE):
                continue
            S["creations with both line sets"] += 1
            apr = [d for t, d in blk if t == "APR0"]
            apes = [d for t, d in blk if t == "APE" and d.get("mode") in (0, 1)]
            if apr and len(apes) >= len(apr):
                S["creations with an affix/QualityItems pick checked from both sides (end to end)"] += 1
                for d in apr:
                    S["  ItemApplyProps calls of the picks: %s" % d["k"]] += 1
            if "AF0" in tags and apes:
                S["  of them with an ITEMS_PickMagicAffix pick"] += 1
            q = next((d.get("q") for t, d in blk if t == "ICJ"), None)
            eth = any(t == "ETHX" and d["fl"] & 0x400000 for t, d in blk)
            sup13 = False
            mode = None
            for t, d in blk:
                if t == "APE":
                    mode = d.get("mode")
                elif t == "APX":
                    mode = None
                elif t == "SLOT" and mode == 1 and d.get("func") == 13:
                    sup13 = True
            if eth:
                S["ethereal creations"] += 1
            if q == 3 and eth:
                S["superior ethereal creations"] += 1
                if sup13:
                    S["superior ethereal creations with a dur% slot (func 13)"] += 1
    return S


def cmd_both(ns):
    print("== tools/items_chain.py both: (1) the affix lines, property roll modelled ==")
    rc1 = cmd_affixes(ns)
    print("== tools/items_chain.py both: (2) the property lines, builders modelled ==")
    rc2 = cmd_props(ns)
    print("== tools/items_chain.py both: coverage ==")
    S = both_counts(ns.logs)
    order = ["creations (IC0 .. ICX)", "creations with both line sets",
             "creations with an affix/QualityItems pick checked from both sides (end to end)"]
    for k in order + sorted(k for k in S if k not in order):
        print("  %-80s %d" % (k, S[k]))
    ok = rc1 == 0 and rc2 == 0
    print("both: %s" % ("every creation reproduced by both passes" if ok else "FAILURES above"))
    return 0 if ok else 1


def main(argv):
    ap = argparse.ArgumentParser(prog="items_chain.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("affixes", "props", "both"):
        p = sub.add_parser(name)
        p.add_argument("logs", nargs="+")
        p.add_argument("--excel", default=uniques.EXCEL)
        p.add_argument("-v", "--verbose", action="store_true")
        p.add_argument("--staff", choices=("oracle", "model"), default="model",
                       help="ITEMS_RollStaffMods: tools/affixes.py's staff_mods model (default since plan 0048 "
                            "Phase 1) or the seed oracle")
    ns = ap.parse_args(argv[1:])
    affixes.STAFF_MODEL = ns.staff == "model"
    return {"affixes": cmd_affixes, "props": cmd_props, "both": cmd_both}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

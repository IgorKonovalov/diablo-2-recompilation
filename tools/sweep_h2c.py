#!/usr/bin/env python3
"""Plan 0038 batch H2c (forced): the ADR-0013 read lists of the claims, and the checks of the forced logs.

    python3 -I tools/sweep_h2c.py reads [--asm <objdump .text dump>]     # the static read lists (before the run)
    python3 -I tools/sweep_h2c.py logs <log> [<log> ...] [--excel DIR]   # the THR/THF/THL and E12/E23/E24 lines
    python3 -I tools/sweep_h2c.py control <stock log> [...] [--excel DIR] # throwable creations per game kind

reads: for each claim, the callee closure of its code in the pinned Game.exe (tools/callee_writes.py's walk, the same
stops for every claim: the fatal-error triple 0x00408090 / 0x00408A60 / 0x00681E09, the pool allocator 0x0040B430 and
its free 0x0040B4B0, memset 0x00681EF0, memmove 0x00683840), then every instruction of the closure that could read
TreasureClassEx data: an absolute reference to the runtime TC globals (g_TCLink 0x0096C5E8, g_pTreasureClasses
0x0096C5EC, g_nTreasureClasses 0x0096C5F0: DataTables +0x9B8/+0x9BC/+0x9C0, data/0001), a register-based operand with
displacement +0x9B8, +0x9BC or +0x9C0 (the same fields through *g_pDataTables 0x00744304), and a direct call to a
function whose name starts TC_ (re/symbols.csv). The same three searches over the whole .text are listed too, by
function, so the claim lists can be read against them. The raw treasureclassex.bin buffer is local to its loader and
freed after the conversion (data/0001), so these globals are the only way to TC data after load. Unresolved indirect
calls are printed (U lines) for reading by hand. For the throwable claim the read list of the code itself (every
memory operand of 0x0055AE6E..0x0055AEC7) is printed too.

logs: per log, the classic throwable re-pick (THR before the counter test, THF after a refund, THL after the 'lsd '
lookup): per resolver call (a TCR line), the counter values in order, refunds, Long Swords, and the checks the claims
need: every refund at a counter value < 10 and every 'lsd ' at >= 10, the counter starting at 0 in each call and
stepping by 1, picks left +1 after each refund, the created item after a THL is the 'lsd ' index (CPRE item), the
game classic. Then the handler entry states: per E12/E23/E24 line the item, its flags, the block, and the follow-up
lines, with the checks: func 12 writes param = the roll and value = par (WR line after E12V), func 23 makes an item
ethereal (flag 0x400000 set at E23X r 1) exactly when it was not ethereal at entry and ItemHasDurability returned
non-zero, func 24 writes value = prev or the roll. Exit 0 only when no check fails. Stdlib only. Read-only.
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import callee_writes as cw  # noqa: E402

STOPS = {0x00408090, 0x00408A60, 0x00681E09, 0x0040B430, 0x0040B4B0, 0x00681EF0, 0x00683840}
TC_ABS = {0x0096C5E8, 0x0096C5EC, 0x0096C5F0}
TC_DISP = {0x9B8, 0x9BC, 0x9C0}
# claim: (roots, extra stops, what)
CLAIMS = [
    ("throw (tc 10, 55, 56)", [(0x0055AE6E, 0x0055AEC8)], {0x0055AF5E},
     "TC_ResolveDrops 0x0055AE6E..0x0055AEC7: the expansion test, the throwable test, the counter, the refund and "
     "the 'lsd ' lookup; 0x0055AEC8 (the creation call) and 0x0055AF5E (the loop's next pick) are not followed"),
    ("func 12 (properties 12, L390)", [(0x0065FC40, None)], set(), "PROP_Func12_SkillRand and its callees"),
    ("func 23 (properties 14)", [(0x0065FD20, None)], set(), "PROP_Func23_Ethereal and its callees"),
    ("func 24 (properties 15)", [(0x0065F390, None)], set(), "PROP_Func24_ParParam and its callees"),
]
ABS_RE = re.compile(r"(?<![0-9a-fx(])0x([0-9a-f]{6,8})\b")
DISP_RE = re.compile(r"(?<![-\w])0x([0-9a-f]+)\(%e[a-z]{2}")
MEMOP = re.compile(r"(-?0x[0-9a-f]+)?\(%e[a-z]{2}(,%e[a-z]{2},\d)?\)|\b0x[0-9a-f]{6,8}\b")


def tc_hit(mn, ops):
    for m in ABS_RE.finditer(ops):
        if int(m.group(1), 16) in TC_ABS:
            return "abs 0x%08X" % int(m.group(1), 16)
    for m in DISP_RE.finditer(ops):
        if int(m.group(1), 16) in TC_DISP:
            return "disp +0x%X" % int(m.group(1), 16)
    return None


def cmd_reads(ns):
    lines = open(ns.asm).read().splitlines() if ns.asm else cw.disasm(ns.exe)
    ins, nxt = cw.parse(lines)
    names = cw.symbols()
    dword = cw.image(ns.exe)
    tcfuncs = {a for a, n in names.items() if n.startswith("TC_")}

    def nm(a):
        return names.get(a, "sub_%08X" % a)
    starts = sorted(names)

    def owner(va):
        import bisect
        i = bisect.bisect_right(starts, va) - 1
        return nm(starts[i]) if i >= 0 else "?"
    print("stops (every claim): " + " ".join("0x%08X" % s for s in sorted(STOPS)))
    print("TC globals: " + " ".join("0x%08X" % a for a in sorted(TC_ABS)) + "; displacements " +
          " ".join("+0x%X" % d for d in sorted(TC_DISP)) + "; TC_ functions %d" % len(tcfuncs))
    print("== whole .text (owner = the nearest named function at or below the site)")
    for va in sorted(ins):
        mn, ops = ins[va]
        h = tc_hit(mn, ops)
        if h:
            print("  TCREF 0x%08X %-34s %-16s %s %s" % (va, owner(va), h, mn, ops))
    bad = 0
    for title, roots, extra, what in CLAIMS:
        funcs, unres, stopped, tables = cw.walk(ins, nxt, roots, STOPS | extra, dword)
        print("== %s: %s" % (title, what))
        hits, calls = [], []
        for e, seen in sorted(funcs.items()):
            print("  F 0x%08X %s %d" % (e, nm(e), len(seen)))
            for va in sorted(seen):
                mn, ops = ins[va]
                h = tc_hit(mn, ops)
                if h:
                    hits.append((va, nm(e), mn + " " + ops, h))
                if mn == "call" and cw.target(ops) in tcfuncs:
                    calls.append((va, nm(e), nm(cw.target(ops))))
            if e in tcfuncs:
                calls.append((e, nm(e), "is a TC_ function"))
        for va, e, tab, n in sorted(tables):
            print("  T 0x%08X %s 0x%08X %d" % (va, nm(e), tab, n))
        for va, e, t in sorted(unres):
            print("  U 0x%08X %s %s" % (va, nm(e), t))
        for va, e, t in sorted(set(stopped)):
            print("  S 0x%08X %s -> 0x%08X %s" % (va, nm(e), t, nm(t)))
        for h in hits:
            print("  TCREF 0x%08X %s %s (%s)" % h)
        for c in calls:
            print("  TCCALL 0x%08X %s %s" % c)
        if roots[0][1] is not None:
            print("  reads of the code itself (memory operands, 0x%08X..0x%08X):" % (roots[0][0], roots[0][1] - 1))
            for va in sorted(funcs[roots[0][0]]):
                mn, ops = ins[va]
                if MEMOP.search(ops) and mn != "call" and not mn.startswith("j"):
                    print("    0x%08X %s %s" % (va, mn, ops))
        print("  totals: functions %d, instructions %d, unresolved %d, TC references %d, TC_ calls %d"
              % (len(funcs), sum(len(s) for s in funcs.values()), len(unres), len(hits), len(calls)))
        bad += len(hits) + len(calls)
    print("claims with a TC read: %d" % bad)
    return 0 if bad == 0 else 1


def read_lines(path):
    for ln in open(path, errors="replace"):
        tag, _, rest = ln.rstrip("\n").partition(" ")
        yield tag, rest


def kv(rest):
    return dict(p.split("=", 1) for p in rest.split() if "=" in p)


def weapon_index(excel, code):
    """The item index of a weapon code: its row in weapons.txt with the 'Expansion' marker rows dropped (weapons come
    first in the item index space, data/0001)."""
    import csv
    with open(os.path.join(excel, "weapons.txt"), encoding="latin-1") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    ci = rows[0].index("code")
    k = 0
    for r in rows[1:]:
        if not r or r[0] == "Expansion":
            continue
        if r[ci] == code:
            return k
        k += 1
    return None


def item_types(excel):
    """Item index -> (code, type) over weapons, armor, misc in that order (the item index space, data/0001), and the
    set of ItemTypes codes with Throwable 1."""
    import csv
    out = []
    for t in ("weapons", "armor", "misc"):
        with open(os.path.join(excel, t + ".txt"), encoding="latin-1") as f:
            rows = list(csv.reader(f, delimiter="\t"))
        ci, ti = rows[0].index("code"), rows[0].index("type")
        out += [(r[ci], r[ti]) for r in rows[1:] if r and r[0] != "Expansion"]
    with open(os.path.join(excel, "itemtypes.txt"), encoding="latin-1") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    ci, th = rows[0].index("Code"), rows[0].index("Throwable")
    thr = {r[ci] for r in rows[1:] if r and r[0] != "Expansion" and r[th] == "1"}
    return out, thr


def cmd_control(ns):
    """Stock control of 'classic only': in the given stock logs, the creations (CPRE) of throwable-type items per game
    kind (TCR exp) and the THR lines (none expected in a log without the H2c logger)."""
    types, thr = item_types(ns.excel)
    S = collections.Counter()
    for path in ns.logs:
        exp = None
        for tag, rest in read_lines(path):
            if tag == "TCR":
                exp = kv(rest).get("exp")
            elif tag == "CPRE" and exp is not None:
                code, ty = types[int(kv(rest)["item"])]
                S["%s creations" % ("expansion" if exp == "1" else "classic")] += 1
                if ty in thr:
                    S["%s creations of a throwable type (%s)" % ("expansion" if exp == "1" else "classic", ty)] += 1
    for k in sorted(S):
        print("%-60s %d" % (k, S[k]))
    return 0


def cmd_logs(ns):
    lsd_tbl = weapon_index(ns.excel, "lsd")
    types, thr_types = item_types(ns.excel)
    S = collections.Counter()
    fails = []
    lsd_idx = None
    for path in ns.logs:
        call = None
        calls = []
        pend = None          # the last THR of this thread
        last_e = {}
        name = os.path.basename(path)
        for tag, rest in read_lines(path):
            if tag == "TCR":
                call = {"thr": [], "exp": kv(rest).get("exp"), "cpre": []}
                calls.append(call)
                pend = None
            elif tag == "THR":
                d = json.loads(rest)
                if call is None:
                    fails.append("%s: THR outside a resolver call" % name)
                    continue
                call["thr"].append(d)
                pend = d
                S["THR lines"] += 1
                S["THR item %s (type %s)" % types[d["item"]]] += 1
                if types[d["item"]][1] not in thr_types:
                    fails.append("%s: THR on item %d of a non-throwable type" % (name, d["item"]))
                if d["exp"] != 0:
                    fails.append("%s: THR in an expansion game" % name)
            elif tag == "THF":
                d = json.loads(rest)
                if not pend or "after" in pend:
                    fails.append("%s: THF with no THR" % name)
                    continue
                pend["after"] = d["left"]
                pend["kind"] = "refund"
            elif tag == "THL":
                d = json.loads(rest)
                if not pend or "kind" in pend:
                    fails.append("%s: THL with no THR" % name)
                    continue
                pend["kind"] = "lsd"
                pend["lsd"] = d["lsd"]
                if lsd_idx is None:
                    lsd_idx = d["lsd"]
                elif d["lsd"] != lsd_idx:
                    fails.append("%s: 'lsd ' index %d, earlier %d" % (name, d["lsd"], lsd_idx))
            elif tag == "CPRE" and call is not None:
                k = kv(rest)
                call["cpre"].append(int(k["item"]))
                if call["exp"] == "0":
                    ty = types[int(k["item"])][1]
                    S["classic creations"] += 1
                    if ty in thr_types:
                        S["classic creations of a throwable type"] += 1
                        fails.append("%s: classic creation of %s (type %s)" % (name, types[int(k["item"])][0], ty))
                if pend and pend.get("kind") == "lsd" and "made" not in pend:
                    pend["made"] = int(k["item"])
            elif tag in ("E12", "E12V", "E23", "E23E", "E23D", "E23X", "E24", "E24V", "WR", "SLOTR"):
                if not rest.startswith("{"):
                    continue
                d = json.loads(rest)
                th = d.get("th")
                if tag in ("E12", "E23", "E24"):
                    last_e[th] = {"f": tag, "d": d, "seq": []}
                    S["%s entries" % tag] += 1
                    S["%s carrier %s q %s" % (tag, d.get("cls"), d.get("q"))] += 1
                elif th in last_e:
                    last_e[th]["seq"].append((tag, d))
                    if tag == "SLOTR":
                        check_handler(name, last_e.pop(th), S, fails)
        for c in calls:
            if not c["thr"]:
                continue
            S["resolver calls with a throwable"] += 1
            ns_ = [t["n"] for t in c["thr"]]
            if ns_ != list(range(len(ns_))):
                fails.append("%s: counter sequence %s" % (name, ns_))
            for t in c["thr"]:
                k = t.get("kind")
                if k == "refund":
                    S["refunds"] += 1
                    if t["n"] >= 10:
                        fails.append("%s: refund at counter %d" % (name, t["n"]))
                    if t["after"] != t["left"] + 1:
                        fails.append("%s: picks left %d -> %d at a refund" % (name, t["left"], t["after"]))
                elif k == "lsd":
                    S["long swords"] += 1
                    if t["n"] < 10:
                        fails.append("%s: 'lsd ' at counter %d" % (name, t["n"]))
                    if t.get("made") != t["lsd"]:
                        S["long sword: next CPRE item is not lsd (no creation logged)"] += 1
                    else:
                        S["long sword: CPRE item = lsd index"] += 1
                else:
                    fails.append("%s: THR with neither THF nor THL (counter %d)" % (name, t["n"]))
            nref = sum(1 for t in c["thr"] if t.get("kind") == "refund")
            nl = sum(1 for t in c["thr"] if t.get("kind") == "lsd")
            S["calls: %d refunds, %d long swords" % (nref, nl)] += 1
            if nl and nref != 10:
                fails.append("%s: a Long Sword after %d refunds" % (name, nref))
    for k in sorted(S):
        print("%-60s %d" % (k, S[k]))
    if lsd_idx is not None:
        print("'lsd ' index logged %d, weapons.txt row %s" % (lsd_idx, lsd_tbl))
        if lsd_idx != lsd_tbl:
            fails.append("'lsd ' index %d is not the weapons.txt row %s" % (lsd_idx, lsd_tbl))
    for f in fails:
        print("FAIL " + f)
    print("checks failed: %d" % len(fails))
    return 0 if not fails else 1


def check_handler(name, e, S, fails):
    f, d, seq = e["f"], e["d"], e["seq"]
    tags = [t for t, _ in seq]
    ret = seq[-1][1].get("v") if seq and seq[-1][0] == "SLOTR" else None
    wr = [x for t, x in seq if t == "WR"]
    if f == "E12":
        v = [x["v"] for t, x in seq if t == "E12V"]
        par, mn, mx = d["blk"][1], d["blk"][2], d["blk"][3]
        if len(v) != 1 or not (min(mn, mx) <= v[0] <= max(mn, mx)):
            fails.append("%s: func 12 roll %s outside [%d, %d]" % (name, v, mn, mx))
            return
        ok = len(wr) == 1 and wr[0].get("param") == v[0] and wr[0].get("v") == par
        S["func 12: WR param = roll, value = par" if ok else "func 12: WR other"] += 1
        if not ok:
            fails.append("%s: func 12 WR %s, roll %d par %d" % (name, wr, v[0], par))
        S["func 12 rolls %d..%d par %d" % (mn, mx, par)] += 1
    elif f == "E23":
        eth = [x["eth"] for t, x in seq if t == "E23E"]
        hd = [x["hasdur"] for t, x in seq if t == "E23D"]
        xs = [x for t, x in seq if t == "E23X"]
        fl0 = d.get("fl", 0)
        if not xs:
            fails.append("%s: func 23 with no E23X" % name)
            return
        x = xs[0]
        made = bool(x["fl"] & 0x400000) and not (fl0 & 0x400000)
        want = (not (fl0 & 0x400000)) and bool(hd and hd[0])
        S["func 23: entry eth %d hasdur %s dur %s nodur %s -> r %d eth %d" % (
            bool(fl0 & 0x400000), hd[0] if hd else "-", d.get("dur"), d.get("nodur"), x["r"],
            bool(x["fl"] & 0x400000))] += 1
        if made != want or x["r"] != int(want):
            fails.append("%s: func 23 entry fl %x hasdur %s -> r %d fl %x" % (name, fl0, hd, x["r"], x["fl"]))
        if eth and bool(eth[0]) != bool(fl0 & 0x400000):
            fails.append("%s: func 23 IsEthereal %s against flags %x" % (name, eth, fl0))
        if wr:
            fails.append("%s: func 23 wrote through PROP_WriteStat" % name)
    elif f == "E24":
        v = [x["v"] for t, x in seq if t == "E24V"]
        par, mn, mx, prev = d["blk"][1], d["blk"][2], d["blk"][3], d["prev"]
        rolled = [x for t, x in seq if t == "ROLL"]
        want = prev if prev else None
        if len(v) != 1 or (want is not None and v[0] != want) or (want is None and not
                                                                  (min(mn, mx) <= v[0] <= max(mn, mx))):
            fails.append("%s: func 24 prev %d -> v %s (block %s)" % (name, prev, v, d["blk"]))
            return
        ok = len(wr) == 1 and wr[0].get("param") == par and wr[0].get("v") == v[0]
        S["func 24 prev %d block %s: WR param = par, value = %s" % (prev, d["blk"],
                                                                   "prev" if prev else "roll")
          if ok else "func 24: WR other"] += 1
        if not ok:
            fails.append("%s: func 24 WR %s, v %d par %d" % (name, wr, v[0], par))
    S["handler lines seen: " + " ".join(tags)] += 1
    _ = ret, rolled if f == "E24" else None


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("reads")
    r.add_argument("--asm")
    r.add_argument("--exe", default=cw.EXE)
    lg = sub.add_parser("logs")
    lg.add_argument("logs", nargs="+")
    lg.add_argument("--excel", default=os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global",
                                                    "excel"))
    co = sub.add_parser("control")
    co.add_argument("logs", nargs="+")
    co.add_argument("--excel", default=lg.get_default("excel"))
    ns = ap.parse_args(argv)
    return {"reads": cmd_reads, "logs": cmd_logs, "control": cmd_control}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

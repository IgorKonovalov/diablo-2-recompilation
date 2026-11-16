#!/usr/bin/env python3
"""Plan 0069 Phase 4 (`lane/n69g`): the settle of the tour's inventory rows (batches H1a to H1d, H1g, H1h of plan 0066),
from the kept checker outputs over the 38 kept logs and the 46 tour logs. No game, no decompile.

    python3 -I tools/ai_tour_settle.py entries MODEL_CHECK [--out F]          # S1b's block rule per entry
    python3 -I tools/ai_tour_settle.py h1 RESUME FLIP [--out F]               # sentence H1's rule per row@think
    python3 -I tools/ai_tour_settle.py inits LOG [LOG ...] [--logs LIST] [--out F]   # the AII/AIQ init lines
    python3 -I tools/ai_tour_settle.py runs LABEL=MODEL_CHECK [...] [--out F]  # per entry, the log groups with decisions
    python3 -I tools/ai_tour_settle.py tally INVENTORY [--out F]              # the outcomes of the six batches' rows
    python3 -I tools/ai_tour_settle.py ready INVENTORY [--out F]              # the ready list for plan 0066 Phase 3

`entries` reads tools/ai_model_check.py's output (`ENTRY`, `ARM`, `FLIP`, `EDGE`, `CONTROL` lines) and prints, per entry,
the decision counts, whether S1b's floor holds (0 mismatches over all its decisions and at least 30 fork-free decisions),
and each named branch or store classed: `sep2` (both arms taken over the fork-free decisions and reversing it alone fails
at least one), `sep1-true`/`sep1-false` (one arm taken, the flip fails: that arm only), `nosep` (run, no decision fails
when it alone is reversed), `unrun` (no fork-free decision ran it). Stores (`set ...`) are `sep` or `nosep`/`unrun`.
`EDGE` names the compares met at an equal pair (the only ones whose `<` against `<=` a log can tell).

`h1` reads tools/ai_resume.py's `RROW` lines and tools/ai_resume_flip.py's `FREE`/`FREEPAST` lines (`--key rowthink`) and
prints per row@think sentence H1's four tests: 0 mismatches (RROW, every decision of the row's own think), at least 50
fork-free resumed decisions (FREE), at least one call past the first among them (FREEPAST), every two-way site of those
decisions failing alone (FREE `two_way_sep` = `two_way`).

`inits` reads the rev 7 `AII`/`AIQ` lines (`MonAiInit`'s call of a row's init function) and prints, per init function, the
pairs and the control words `+0x14` (v14) and `+0x18` (v18) before and after, against the frame `fr` of the line: for row
43's init 0x005F6630 the block's `v14 <- T; v18 <- 0`, with the pairs that separate a store from no store (the word before
differs from the word the block writes).

`tally` and `ready` read the plan 0066 inventory file and the outcome markers this phase writes into the Route cell
(`**Raised 2026-11-16 (`lane/n69g`…`, `**Raised in part 2026-11-16 (`lane/n69g`…`, `**Kept `[I]` 2026-11-16 (`lane/n69g`…`).
Stdlib only.
"""
import argparse
import json
import re
import sys
from collections import OrderedDict, defaultdict

BATCHES = ("H1a", "H1b", "H1c", "H1d", "H1g", "H1h")
FLOOR_BLOCK = 30
FLOOR_H1 = 50
MARK = re.compile(r"\*\*(Raised in part|Raised|Kept `\[I\]`) 2026-11-16 \(`lane/n69g`")


def out(lines, path):
    text = "\n".join(lines) + "\n"
    if path:
        with open(path, "w") as fh:
            fh.write(text)
    sys.stdout.write(text)


# ---------------------------------------------------------------- entries
ENT = re.compile(r"^ENTRY (\S+) think (\S+) \((.*)\): decisions (\d+), ok (\d+) \(fork-free (\d+), forked (\d+)\), "
                 r"mismatch (\d+), stop (\d+)")
ARM = re.compile(r"^  ARM (.+) true (\d+) false (\d+)$")
FLIP = re.compile(r"^  FLIP (.+) fail (\d+) of (\d+) ")
EDGE = re.compile(r"^  EDGE (.+) (\d+)$")
CTRL = re.compile(r"^  CONTROL (\S+) fail (\d+) of (\d+)")


def parse_model_check(path):
    ents = OrderedDict()
    cur = None
    with open(path) as fh:
        for line in fh:
            line = line.rstrip("\n")
            m = ENT.match(line)
            if m:
                cur = {"name": m.group(1), "think": m.group(2), "inv": m.group(3),
                       "dec": int(m.group(4)), "ok": int(m.group(5)), "ff": int(m.group(6)), "forked": int(m.group(7)),
                       "mm": int(m.group(8)), "stop": int(m.group(9)), "arm": {}, "flip": OrderedDict(), "edge": {},
                       "ctrl": {}}
                ents[cur["name"]] = cur
                continue
            if cur is None:
                continue
            for rx, key in ((ARM, "arm"), (FLIP, "flip"), (EDGE, "edge"), (CTRL, "ctrl")):
                m = rx.match(line)
                if m:
                    if key == "edge":
                        cur["edge"][m.group(1)] = int(m.group(2))
                    else:
                        cur[key][m.group(1)] = (int(m.group(2)), int(m.group(3)))
                    break
    return ents


def classify(e):
    """[(name, class)] for each FLIP name of the entry."""
    res = []
    for name, (fail, n) in e["flip"].items():
        t, f = e["arm"].get(name, (0, 0))
        if name.startswith("set "):
            cls = "unrun" if n == 0 else ("sep" if fail else "nosep")
        elif n == 0:
            cls = "unrun"
        elif fail == 0:
            cls = "nosep"
        elif t and f:
            cls = "sep2"
        else:
            cls = "sep1-true" if t else "sep1-false"
        res.append((name, cls, fail, n, t, f))
    return res


def cmd_entries(a):
    ents = parse_model_check(a.model_check)
    L = []
    for e in ents.values():
        floor = e["mm"] == 0 and e["ff"] >= FLOOR_BLOCK
        L.append("ENT %s think %s dec %d ff %d forked %d mm %d stop %d floor %s (%s)" % (
            e["name"], e["think"], e["dec"], e["ff"], e["forked"], e["mm"], e["stop"], "met" if floor else "not met",
            e["inv"]))
        cl = classify(e)
        groups = defaultdict(list)
        for name, cls, fail, n, t, f in cl:
            groups[cls].append(name)
        for cls in ("sep2", "sep1-true", "sep1-false", "sep", "nosep", "unrun"):
            if groups[cls]:
                L.append("  %s %d: %s" % (cls, len(groups[cls]), "; ".join(groups[cls])))
        if e["edge"]:
            L.append("  edge: %s" % "; ".join("%s %d" % kv for kv in sorted(e["edge"].items())))
        if e["ctrl"]:
            L.append("  controls: %s" % "; ".join("%s %d/%d" % (k, v[0], v[1]) for k, v in e["ctrl"].items()))
    n_met = sum(1 for e in ents.values() if e["mm"] == 0 and e["ff"] >= FLOOR_BLOCK)
    L.append("SUMMARY entries %d floor met %d with decisions %d zero %d" % (
        len(ents), n_met, sum(1 for e in ents.values() if e["dec"]), sum(1 for e in ents.values() if not e["dec"])))
    out(L, a.out)


def cmd_runs(a):
    groups = []
    for spec in a.pairs:
        label, path = spec.split("=", 1)
        groups.append((label, parse_model_check(path)))
    names = list(groups[0][1])
    L = []
    for n in names:
        parts = []
        for label, ents in groups:
            e = ents.get(n)
            if e and e["dec"]:
                parts.append("%s %d (fork-free %d, mismatch %d)" % (label, e["dec"], e["ff"], e["mm"]))
        L.append("RUNS %s: %s" % (n, "; ".join(parts) if parts else "none"))
    out(L, a.out)


# ---------------------------------------------------------------- h1
RROW = re.compile(r"^RROW (\S+) th=([0-9a-f]+) decisions=(\d+) resumed_ok=(\d+) mismatches=(\d+) stopped=(\d+) "
                  r"boundaries_matched=(\d+) past_first=(\d+)")
FREE = re.compile(r"^FREE (\S+) decisions=(\d+) sampled=(\d+) sites=(\d+) sep=(\d+) nosep=(\d+) two_way=(\d+) "
                  r"two_way_sep=(\d+)")
FREEPAST = re.compile(r"^FREEPAST (\S+) decisions=(\d+) past_first=(\d+) decisions_with_past=(\d+)")
FLIPL = re.compile(r"^FLIP (\S+) decisions_resumed=(\d+) ")


def cmd_h1(a):
    rrow, free, past, flip = {}, {}, {}, {}
    with open(a.resume) as fh:
        for line in fh:
            m = RROW.match(line)
            if m:
                key = "%s@%s" % (m.group(1), m.group(2).lstrip("0"))
                rrow[key] = tuple(int(x) for x in m.groups()[2:])
    with open(a.flip) as fh:
        for line in fh:
            for rx, d in ((FREE, free), (FREEPAST, past), (FLIPL, flip)):
                m = rx.match(line)
                if m:
                    d[m.group(1)] = tuple(int(x) for x in m.groups()[1:])
    L = []
    for key in sorted(set(rrow) | set(free), key=lambda k: (int(k.split("@")[0]) if k.split("@")[0].isdigit() else 9999, k)):
        r = rrow.get(key)
        f = free.get(key)
        p = past.get(key)
        if r is None or f is None:
            L.append("H1 %s missing resume=%s flip=%s" % (key, r is not None, f is not None))
            continue
        dec, ok, mis, stop, matched, pfirst = r
        fdec, fsamp, sites, sep, nosep, tw, twsep = f
        pdec, ppast, pwith = p if p else (0, 0, 0)
        tests = [("mismatch0", mis == 0), ("ff>=50", fdec >= FLOOR_H1), ("past>=1", ppast >= 1), ("twoway", tw == twsep)]
        verdict = "met" if all(t for _, t in tests) else "not met: " + ", ".join(n for n, t in tests if not t)
        L.append("H1 %s decisions %d resumed %d mismatches %d stopped %d; fork-free %d, past the first %d in %d, "
                 "sites %d sep %d, two-way %d of %d; %s" % (key, dec, ok, mis, stop, fdec, ppast, pwith, sites, sep, twsep,
                                                          tw, verdict))
    out(L, a.out)


# ---------------------------------------------------------------- inits
def words(cw):
    b = bytes.fromhex(cw)
    return int.from_bytes(b[0x14:0x18], "little"), int.from_bytes(b[0x18:0x1C], "little")


def cmd_inits(a):
    paths = list(a.logs)
    if a.loglist:
        with open(a.loglist) as fh:
            paths += [x.strip() for x in fh if x.strip()]
    per = defaultdict(lambda: {"pairs": 0, "logs": set(), "v14T": 0, "v14sep": 0, "v18z": 0, "v18sep": 0, "same": 0,
                               "unpaired": 0})
    for p in paths:
        pend = {}
        with open(p, errors="replace") as fh:
            for line in fh:
                if line.startswith("AII "):
                    d = json.loads(line[4:])
                    pend[d["u"]] = d
                elif line.startswith("AIQ "):
                    q = json.loads(line[4:])
                    i = pend.pop(q["u"], None)
                    if i is None:
                        continue
                    e = per["%08x" % i["fn"]]
                    e["pairs"] += 1
                    e["logs"].add(p)
                    b14, b18 = words(i["cw"])
                    q14, q18 = words(q["cw"])
                    e["v14T"] += q14 == i["fr"]
                    e["v14sep"] += q14 == i["fr"] and b14 != i["fr"]
                    e["v18z"] += q18 == 0
                    e["v18sep"] += q18 == 0 and b18 != 0
                    e["same"] += q["cw"] == i["cw"]
        for e in per.values():
            pass
        for d in pend.values():
            per["%08x" % d["fn"]]["unpaired"] += 1
    L = ["INITS logs %d" % len(paths)]
    for fn in sorted(per):
        e = per[fn]
        L.append("INIT %s pairs %d in %d logs; v14 = T after %d (word before differs %d); v18 = 0 after %d (word before "
                 "differs %d); control block unchanged %d; AII without AIQ %d" % (
                     fn, e["pairs"], len(e["logs"]), e["v14T"], e["v14sep"], e["v18z"], e["v18sep"], e["same"],
                     e["unpaired"]))
    out(L, a.out)


# ---------------------------------------------------------------- tally, ready
def inv_rows(path):
    rows = []
    with open(path) as fh:
        for line in fh:
            m = re.match(r"\| (\d+) \| (\d+) \| ([^|]*) \|", line)
            if not m:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append({"n": int(cells[0]), "line": int(cells[1]), "section": cells[2], "cls": cells[5],
                         "batch": cells[-2], "count": int(cells[-1]), "route": "|".join(cells[6:-2])})
    return rows


def outcome(route):
    m = MARK.search(route)
    if not m:
        return None
    return {"Raised": "raised", "Raised in part": "raised in part"}.get(m.group(1), "kept")


def cmd_tally(a):
    rows = [r for r in inv_rows(a.inventory) if r["batch"] in BATCHES]
    t = defaultdict(lambda: defaultdict(int))
    cls = defaultdict(lambda: defaultdict(int))
    for r in rows:
        o = outcome(r["route"]) or "unsettled"
        t[r["batch"]][o] += r["count"]
        cls[r["batch"]][r["cls"]] += r["count"]
    L = []
    tot = defaultdict(int)
    for b in BATCHES:
        s = sum(t[b].values())
        L.append("TALLY %s stmts %d raised %d raised-in-part %d kept %d unsettled %d; classes %s" % (
            b, s, t[b]["raised"], t[b]["raised in part"], t[b]["kept"], t[b]["unsettled"],
            ", ".join("%s %d" % kv for kv in sorted(cls[b].items()))))
        for k, v in t[b].items():
            tot[k] += v
    L.append("TOTAL stmts %d raised %d raised-in-part %d kept %d unsettled %d" % (
        sum(tot.values()), tot["raised"], tot["raised in part"], tot["kept"], tot["unsettled"]))
    for o in ("raised", "raised in part", "kept", "unsettled"):
        L.append("ROWS %s: %s" % (o, ", ".join(str(r["n"]) for r in rows if (outcome(r["route"]) or "unsettled") == o)))
    out(L, a.out)


def cmd_ready(a):
    rows = [r for r in inv_rows(a.inventory) if r["batch"] in BATCHES]
    L = []
    for r in rows:
        o = outcome(r["route"])
        if o not in ("raised", "raised in part"):
            continue
        m = re.search(r"\*\*Raised(?: in part)? 2026-11-16 \(`lane/n69g`[^)]*\)\.?\*\*\s*(.*)$", r["route"])
        body = m.group(1) if m else ""
        L.append("READY row %d line %d %s: %s; %s" % (r["n"], r["line"], r["section"], o, body))
    L.append("READY total %d" % len(L))
    out(L, a.out)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("entries")
    e.add_argument("model_check")
    e.add_argument("--out")
    h = sub.add_parser("h1")
    h.add_argument("resume")
    h.add_argument("flip")
    h.add_argument("--out")
    i = sub.add_parser("inits")
    i.add_argument("logs", nargs="*")
    i.add_argument("--logs", dest="loglist")
    i.add_argument("--out")
    r = sub.add_parser("runs")
    r.add_argument("pairs", nargs="+")
    r.add_argument("--out")
    for name in ("tally", "ready"):
        t = sub.add_parser(name)
        t.add_argument("inventory")
        t.add_argument("--out")
    a = p.parse_args(argv)
    {"entries": cmd_entries, "h1": cmd_h1, "inits": cmd_inits, "runs": cmd_runs, "tally": cmd_tally, "ready": cmd_ready}[a.cmd](a)


if __name__ == "__main__":
    main()

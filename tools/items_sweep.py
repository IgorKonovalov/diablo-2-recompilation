#!/usr/bin/env python3
"""Plan 0038 batch S2b: the items/affixes, items/properties and items/uniques-sets checks over the kept item logs,
the staff-mods model, the table checks and the static scans.

    python3 -I tools/items_sweep.py logs [--write FILE]  the log sets, sha256 checked against their manifests
    python3 -I tools/items_sweep.py staff                ITEMS_RollStaffMods modelled (no oracle) over every log set
    python3 -I tools/items_sweep.py cf                   staff-mods counterfactuals: each must FAIL where its rule
                                                         decides (a sensitivity check, not evidence)
    python3 -I tools/items_sweep.py scan                 per-creation log scans (qualities, flags, fallbacks, sets,
                                                         ethereal, sockets, damage and durability cases)
    python3 -I tools/items_sweep.py tables               full-table checks (affix, rare, automagic, set, unique,
                                                         base and override tables)
    python3 -I tools/items_sweep.py static               raw-byte scans of the pinned Game.exe (references and
                                                         displacements), next to the Ghidra readings

Log sets (`logs`): STOCK is every kept stock log of the five item-creation runs (run:2026-10-14-uniques,
-affixes, -props, run:2026-10-15-items-chain stock sessions, run:2026-10-16-quest-drops sessions), the set of
tools/tc_sweep.py for those runs. IR is the ItemRatio-only forced runs (run:2026-10-14-uniques-forced,
run:2026-10-14-props-forced, run:2026-10-15-items-chain-forced): ADR-0013 admits them for a claim whose code reads no
ItemRatio cell, which is every claim of this batch that cites them (the creation chain after the drop roll reads no
ItemRatio record: `static` § g_pItemRatio). Every count is printed per set, so a claim can rest on STOCK alone.

Each output line starts with `S2B <check>`; the "Plan 0038 batch S2b" sections of
docs/findings/items/0004-uniques-sets.md, 0005-affixes.md and 0006-properties.md map them to the statements they
back. Stdlib only. Read-only (logs --write writes the manifest file it is given).
"""
import argparse
import collections
import contextlib
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import affixes  # noqa: E402
import excel_bin  # noqa: E402
import items_chain  # noqa: E402
import props  # noqa: E402
import rng  # noqa: E402
import tc_sweep  # noqa: E402
import uniques  # noqa: E402
import xrefscan  # noqa: E402

ROOT = os.path.dirname(HERE)
LOGS = tc_sweep.LOGS
EXCEL = uniques.EXCEL
STOCK_RUNS = ("run:2026-10-14-uniques", "run:2026-10-14-affixes", "run:2026-10-14-props",
              "run:2026-10-15-items-chain", "run:2026-10-16-quest-drops")
# ADR-0013: ItemRatio cells edited, every other table stock (docs/findings/items/experiments.md).
IR_RUNS = [
    ("run:2026-10-14-uniques-forced", "uniques-forced-manifest.txt", ("uforced",)),
    ("run:2026-10-14-props-forced", "props-forced-manifest.txt", ("props",)),
    ("run:2026-10-15-items-chain-forced", "items-chain-manifest.txt", ("ichainf-", "ichainh-")),
]


def log_sets(check=True):
    """{"STOCK": [(run, path)], "IR": [(run, path)]}; sha256 checked against the manifests (and the pinned hashes of
    tools/tc_sweep.py)."""
    out = {"STOCK": [], "IR": []}
    for run, path, _, _, _ in tc_sweep.stock_logs(check=check):
        if run in STOCK_RUNS:
            out["STOCK"].append((run, path))
    for run, man, pre in IR_RUNS:
        for ln in open(os.path.join(LOGS, man)):
            if not ln.strip():
                continue
            h, name = ln.split()
            name = os.path.basename(name)
            if not name.startswith(pre):
                continue
            path = os.path.join(LOGS, name)
            if check and tc_sweep.sha256(path) != h:
                raise SystemExit("%s: sha256 differs from %s" % (name, man))
            out["IR"].append((run, path))
    return out


def cmd_logs(ns):
    sets = log_sets()
    lines = []
    for k in ("STOCK", "IR"):
        by = collections.Counter(r for r, _ in sets[k])
        for r in sorted(by):
            print("S2B logs %s %s files=%d" % (k, r, by[r]))
        lines += ["%s  %s" % (tc_sweep.sha256(p), os.path.relpath(p, ROOT)) for _, p in sets[k]]
    print("S2B logs total STOCK=%d IR=%d (sha256 checked against the run manifests)" % (
        len(sets["STOCK"]), len(sets["IR"])))
    if ns.write:
        with open(ns.write, "w") as f:
            f.write("\n".join(lines) + "\n")
        print("manifest written: %s (sha256 %s)" % (ns.write, tc_sweep.sha256(ns.write)))
    return 0


# ---------------------------------------------------------------- shared: log blocks

def blocks(path):
    """Every creation IC0 .. ICX of one log as (block, drop): block = [(tag, dict)] with every JSON line in between
    (the loggers log one creation per thread at a time; the drop path runs on one thread), plus the item's last
    ItemInitStats lines (IIS0, IIS1, logged before IC0) and the LX line that tools/gdb/props.py writes right after
    ICX; drop = the CPRE fields when the creation lies inside a CPRE .. CPOST window (tools/uniques.py read_log),
    else None. A GAME line is yielded as ("GAME", None)."""
    cur = None
    done = None                 # a block whose ICX was read, waiting for its LX line
    cpre = None
    iis = {}                    # item unit -> its last IIS0 / IIS1 lines (ItemInitStats runs before IC0)
    for line in open(path, errors="replace"):
        tag, _, rest = line.rstrip("\n").partition(" ")
        d = None
        if rest.startswith("{"):
            try:
                d = json.loads(rest)
            except ValueError:
                continue
        if done is not None:
            if tag == "LX" and d is not None:
                done[0].append((tag, d))
                yield done[0], done[1]
                done = None
                continue
            if tag in ("IC0", "GAME", "CPRE", "CPOST", "IIS0") or (d is not None and tag not in ("STALE", "STALEX")):
                yield done[0], done[1]
                done = None
        if tag == "GAME":
            yield "GAME", None
            continue
        if tag == "CPRE":
            cpre = dict(x.split("=", 1) for x in rest.split() if "=" in x)
            continue
        if tag == "CPOST":
            cpre = None
            continue
        if d is None:
            continue
        if tag in ("IIS0", "IIS1"):
            iis.setdefault(d.get("it"), {})[tag] = d
            continue
        if tag == "IC0":
            cur = [[], cpre]
            for t in ("IIS0", "IIS1"):
                x = iis.get(d.get("it"), {}).get(t)
                if x is not None:
                    cur[0].append((t, x))
            iis.pop(d.get("it"), None)
        if cur is None:
            continue
        cur[0].append((tag, d))
        if tag == "ICX":
            done = cur
            cur = None
    if done is not None:
        yield done[0], done[1]


def quiet(fn, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a)
    return rc, buf.getvalue()


def counted(text, *keys):
    """Pick 'key: n' or 'key   n' counter lines out of a tool's report."""
    out = {}
    for ln in text.splitlines():
        s = ln.strip()
        for k in keys:
            if s.startswith(k):
                rest = s[len(k):].strip(" :")
                if rest.split() and rest.split()[-1].lstrip("-").isdigit():
                    out[k] = int(rest.split()[-1])
    return out


# ---------------------------------------------------------------- staff mods

def run_staff(paths, kind, excel, show=True):
    """tools/affixes.py check and tools/items_chain.py props with ITEMS_RollStaffMods modelled. kind: the line sets
    the logs carry ("affix", "props", "both", "legacy")."""
    res = collections.Counter()
    affixes.STAFF_MODEL = True
    try:
        if kind in ("affix", "both"):
            ns = argparse.Namespace(logs=paths, excel=excel, verbose=False, staff="model")
            rc, txt = quiet(affixes.cmd_check, ns)
            for ln in txt.splitlines():
                if ln.startswith("FAIL") and show:
                    print("  " + ln[:300])
            first = next(ln for ln in txt.splitlines() if ln.endswith(" failed") and "creations reproduced" in ln)
            res["affix creations reproduced"] += int(first.split()[0])
            res["affix creations failed"] += int(first.split()[3])
            c = counted(txt, "staff mods exit seeds predicted (STF1)", "staff mods modelled: none",
                        "staff mods: class and firstSkill(c) compared (STFC)",
                        "staff mods: STFC not logged (seed 2101's logger had no STFC line)",
                        "staff mods modelled: fallback", "staff mods modelled: lowcap",
                        "staff mods modelled: lownodraw", "staff mods modelled: typerefused",
                        *["staff mods modelled: %d mods" % n for n in range(4)],
                        *["staff mods modelled: class %d" % n for n in range(7)])
            for k, v in c.items():
                res["affix pass: " + k] += v
        if kind in ("props", "both"):
            ns = argparse.Namespace(logs=paths, excel=excel, verbose=False, staff="model")
            rc, txt = quiet(items_chain.cmd_props, ns)
            for ln in txt.splitlines():
                if ln.startswith("FAIL"):
                    print("  " + ln[:300])
            for ln in txt.splitlines():
                if ln.startswith("chain:"):
                    res["chain creations reproduced"] += int(ln.split()[1])
                    res["chain creations failed"] += int(ln.split()[4])
            c = counted(txt, "join seeds predicted (ICJ)", "staff mods: exit not checkable",
                        "staff mods vs LX: 107 lists compared", "staff mods vs LX: 107 entries predicted",
                        "staff mods vs LX: items with staff-mod entries, predicted",
                        "staff mods vs LX: not compared (a property wrote stat 107)",
                        "staff mods modelled: none", "staff mods modelled: lownodraw",
                        *["staff mods modelled: %d mods" % n for n in range(4)],
                        *["staff mods modelled: class %d" % n for n in range(7)])
            for k, v in c.items():
                res["props pass: " + k] += v
    finally:
        affixes.STAFF_MODEL = False
    return res


def has(path, tags):
    with open(path, errors="replace") as f:
        for ln in f:
            if ln.startswith(tags):
                return True
    return False


def kind_of(path):
    a = has(path, ("AF0 ", "STF0 ", "RC "))
    p = has(path, ("APE ", "IIS0 ", "LX "))
    return "both" if a and p else "affix" if a else "props" if p else "legacy"


def cmd_staff(ns):
    sets = log_sets(check=not ns.nocheck)
    bad = 0
    for k in ("STOCK", "IR"):
        groups = collections.defaultdict(list)
        for run, p in sets[k]:
            groups[(run, kind_of(p))].append(p)
        for (run, kind), paths in sorted(groups.items()):
            if kind == "legacy":
                print("S2B staff %s %s files=%d kind=legacy (no affix or property lines: not checkable)" % (
                    k, run, len(paths)))
                continue
            res = run_staff(paths, kind, ns.excel)
            bad += res["affix creations failed"] + res["chain creations failed"]
            print("S2B staff %s %s files=%d kind=%s %s" % (k, run, len(paths), kind, " ".join(
                "%s=%d" % (x.replace(" ", "_"), v) for x, v in sorted(res.items()))))
    print("S2B staff failed=%d" % bad)
    return 1 if bad else 0


def run_props(paths, excel):
    ns = argparse.Namespace(logs=paths, excel=excel, verbose=False)
    rc, txt = quiet(props.cmd_check, ns)
    line = next(ln for ln in txt.splitlines() if "creations reproduced" in ln)
    w = line.split()
    return int(w[0]), int(w[3])


CF = ["count-ge", "tier-noexp", "signed-low", "notype", "nolowcap", "lowdraw"]


def cmd_cf(ns):
    """Each counterfactual staff_mods variant over the logs with STF brackets: the number of creations it breaks.
    A variant that breaks creations shows that the logs decide its rule; one that breaks none is only consistent."""
    sets = log_sets(check=not ns.nocheck)
    for k in ("STOCK", "IR"):
        paths = [p for _, p in sets[k] if kind_of(p) in ("affix", "both")]
        for v in [None] + CF:
            affixes.STAFF_CF = v
            try:
                res = run_staff(paths, "affix", ns.excel, show=v is None)
            finally:
                affixes.STAFF_CF = None
            print("S2B cf %s staff=%s files=%d reproduced=%d broken=%d" % (
                k, v or "model", len(paths), res["affix creations reproduced"], res["affix creations failed"]))
        for v in [None, "high-word", "unsigned-walk"]:
            affixes.PICK_CF = v
            try:
                ns2 = argparse.Namespace(logs=paths, excel=ns.excel, verbose=False, staff="oracle")
                rc, txt = quiet(affixes.cmd_check, ns2)
            finally:
                affixes.PICK_CF = None
            line = next(ln for ln in txt.splitlines() if "creations reproduced" in ln)
            print("S2B cf %s pick=%s files=%d reproduced=%s broken=%s" % (
                k, v or "model", len(paths), line.split()[0], line.split()[3]))
        ppaths = [p for _, p in sets[k] if kind_of(p) in ("props", "both")]
        for v in (False, True):
            props.FLOOR_CF = v
            try:
                ok, bad = run_props(ppaths, ns.excel)
            finally:
                props.FLOOR_CF = False
            print("S2B cf %s props division=%s files=%d reproduced=%d broken=%d" % (
                k, "floor" if v else "trunc (model)", len(ppaths), ok, bad))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("logs")
    p.add_argument("--write")
    for name in ("staff", "cf", "scan", "tables", "static"):
        p = sub.add_parser(name)
        p.add_argument("--excel", default=EXCEL)
        p.add_argument("--nocheck", action="store_true", help="skip the sha256 checks of the logs")
        if name == "static":
            p.add_argument("--closure", nargs="*", help="outputs of tools/ghidra.sh rngcallgraph to probe")
    ns = ap.parse_args(argv)
    return {"logs": cmd_logs, "staff": cmd_staff, "cf": cmd_cf, "scan": cmd_scan, "tables": cmd_tables,
            "static": cmd_static}[ns.cmd](ns)


# ---------------------------------------------------------------- per-creation scans

AUTOMAGIC_APE_RET = 0x00557A11


def lists(lx):
    base = {(a, b): v for a, b, v in lx.get("b", [])}
    main = {}
    for st, fl, ents in lx.get("sub", []):
        if st == 0:
            for a, b, v in ents:
                main[(a, b)] = v
    return base, main


def scan_block(T, PT, blk, drop, C, N, game):
    """One creation: count what the S2b rows read off it. C: Counter, N: notes (defaultdict(list)), game: per-game
    state (set builds, unique builds)."""
    tags = collections.defaultdict(list)
    for t, d in blk:
        tags[t].append(d)
    ic = tags["IC0"][0]
    icq, icj, icx = tags["ICQ"][0], tags["ICJ"][0], tags["ICX"][0]
    cls, ver = ic["cls"], ic["ver"]
    b = T.b(cls)
    pb = PT.base(cls)
    src = "drop" if drop is not None else "other"
    exp = "exp" if ver >= 100 else "classic"
    if ic.get("rest") or ver == 0 or not ic.get("rq"):
        C["creations skipped (restore, version 0 or record quality 0)"] += 1
        return
    C["creations %s" % src] += 1
    C["creations with ilvl < 1 at entry"] += ic["ilvl"] < 1
    C["unique picks with candidates (UPK)"] += len(tags["UPK"])
    C["unique picks (UPK): candidate pairs logged from g_UniqueCandidates"] += sum(len(d["cand"]) for d in tags["UPK"])
    if ic.get("rfl", 0) & 1:
        C["creations with record flag bit 0 (hellbovine source): %s" % src] += 1
    for d in tags["STF0"]:
        C["staff mods entered from builder %s" % d["k"]] += 1
    # aff 1: the qualities that reach the switch
    C["switch quality %s q=%d" % (src, icq["q"])] += 1
    for d in tags["BLD"]:
        C["builder entered: %s" % d["k"]] += 1
    # us 13, 15: the overrides
    if icq["q"] != ic["rq"]:
        C["override changed the quality: %s" % src] += 1
        N["override changed"].append("%s cls %d %s: record %d -> switch %d (ICQ rq %d)" % (
            src, cls, b["code"], ic["rq"], icq["q"], icq["rq"]))
        if icq["rq"] == ic["rq"]:
            C["override changed the quality, record quality unchanged at the switch: %s" % src] += 1
    else:
        C["override kept the quality: %s" % src] += 1
    # us 36: the fallback steps
    fbs = tags["FB"]
    if fbs:
        last = {"rare": 6, "magic": 4, "superior": 3, "normal": 2}[fbs[-1]["k"]]
        C["fallback chains (FB)"] += 1
        C["fallback: join record quality = the last step's quality"] += icj["rq"] == last
        C["fallback: join item quality = the last step's quality"] += icj["q"] == last
        C["fallback: join file index -1"] += icj["fi"] == -1
        C["fallback: first builder %s -> %s" % (tags["BLD"][0]["k"], fbs[0]["k"])] += 1
        C["fallback: record quality at entry %d, at the join %d" % (ic["rq"], icj["rq"])] += 1
    # us 20, 29: the identified flag (0x10) at entry and at the return
    lx = tags["LX"][0] if tags["LX"] else None
    if lx is not None:
        k = "q%d" % icj["q"] + (" row" if icj["fi"] >= 0 and icj["q"] in (5, 7) else "")
        C["LX flags 0x10 at entry set: %s" % k] += bool(ic["fl"] & 0x10)
        C["LX flags 0x10 at the return set: %s" % k] += bool(lx["fl"] & 0x10)
        C["LX creations: %s" % k] += 1
    # set builds (us 6, 28, 32, 33, 42), unique builds and UMADE (us 34)
    for d in tags["UMADE"]:
        C["UMADE lines"] += 1
        if game["sets"]:
            C["UMADE after a set build in the same game"] += 1
            rows = set(d["rows"])
            C["UMADE after a set build: rows = the unique rows built"] += rows == game["uniques"]
            if rows & set(r for r in game["sets"]):
                C["UMADE after a set build: a set row index is also marked"] += 1
    for d in tags["SPK"]:
        C["set picks (SPK)"] += 1
        cand = [r for r, _ in d["cand"]]
        rfl = ic.get("rfl", 0)
        il = max(ic["ilvl"], 1)
        # every row the version, lvl and code tests keep, without the set-29 test
        noflag = [i for i, r in enumerate(T.setit) if not (r["sver"] >= 100 and ver < 100) and r["lvl"] <= il
                  and r["code"] == T.items[cls][0x80:0x84]]
        s29 = [i for i in noflag if T.setit[i]["set"] == 29]
        if s29:
            C["set picks on a set-29 member base: rfl bit 0 %s" % ("set" if rfl & 1 else "clear")] += 1
            C["set picks on a set-29 member base: set-29 rows among the candidates: %s" % (
                "yes" if set(s29) & set(cand) else "no")] += 1
            N["set29"].append(game["log"] + " %s %s ilvl %d rfl %d: cand %s, set-29 rows passing the other tests %s" % (
                exp, b["code"], il, rfl, cand, s29))
        if ver < 100:
            C["classic set picks"] += 1
            nover = [i for i, r in enumerate(T.setit) if r["lvl"] <= il and r["code"] == T.items[cls][0x80:0x84]
                     and not (r["set"] == 29 and not rfl & 1)]
            dropped = [i for i in nover if T.setit[i]["sver"] >= 100]
            C["classic set picks where the version test removes a row"] += bool(dropped)
            if dropped:
                N["classicver"].append("%s %s ilvl %d: cand %s, expansion-set rows removed %s" % (
                    game["log"], b["code"], il, cand, dropped))
            C["classic set picks: candidates all of classic sets"] += all(T.setit[i]["sver"] < 100 for i in cand)
            if cand:
                C["classic set picks with candidates"] += 1
        else:
            if any(T.setit[i]["sver"] < 100 for i in cand):
                C["expansion set picks with a classic-set candidate"] += 1
    built = icj["fi"] if icj["q"] == 5 and icj["fi"] >= 0 else None
    if built is not None:
        C["set builds"] += 1
        if built in game["sets"]:
            C["set row built again in the same game"] += 1
            N["setrepeat"].append("%s %s %s row %d" % (game["log"], exp, b["code"], built))
        if built in game["uniques"]:
            C["set row index already marked in uniqueMade"] += 1
        game["sets"].add(built)
    if icj["q"] == 7 and icj["fi"] >= 0:
        game["uniques"].add(icj["fi"])
    # us 40: ethereal draws by quality (props logs: ETHR; affix logs: ETB0/ETB1 or ETH0/ETH1 seeds)
    q = icj["q"]
    if ver >= 100:
        drew = None
        if tags["ETHX"]:
            drew = bool(tags["ETHR"])
        elif tags["ETB0"] and tags["ETB1"]:
            drew = tags["ETB0"][0]["seed"] != tags["ETB1"][0]["seed"]
        elif tags["ETH0"] and tags["ETH1"]:
            drew = tags["ETH0"][0]["seed"] != tags["ETH1"][0]["seed"]
        if drew is not None and (T.is_type(cls, 45) or T.is_type(cls, 50)) and pb["dur"] and not pb["nodur"]:
            C["ethereal step, weapon or armour with durability, q%d: %s" % (q, "drew" if drew else "no draw")] += 1
            if q == 7:
                N["eth7"].append("%s %s row %d: %s" % (exp, b["code"], icj["fi"], "drew" if drew else "no draw"))
    # aff 34: qualities 5 and 7 on a base with an automagic group
    if ver >= 100 and q in (5, 7) and b["auto"]:
        auto = any(d.get("auto") for d in tags["AF0"]) or any(d.get("ret") == AUTOMAGIC_APE_RET for d in tags["APE"]) \
            or any(d.get("k") == "auto" for d in tags["APR0"])
        C["q%d on an automagic base: automagic pick %s" % (q, "made" if auto else "skipped")] += 1
        N["auto57"].append(game["log"] + " %s q%d %s auto %d row %d" % (exp, q, b["code"], b["auto"], icj["fi"]))
    # aff 37: frequency-0 version-0 rows never candidates
    for d in tags["AFC"]:
        C["AFC candidate lists"] += 1
        C["AFC candidates that are frequency-0 version-0 rows"] += sum(
            1 for a in d["ids"] if T.magic[a - 1]["freq"] == 0 and T.magic[a - 1]["ver"] == 0)
    for d in tags["AF0"]:
        C["AF0 picks with forcedId 0" if d["forced"] == 0 else "AF0 picks with a forced id"] += 1
    # prop 8: quality at ItemInitStats; stackable weapons of quality 4..9 keep their quantity
    for d in tags["IIS0"]:
        C["IIS0 item quality = %d" % d["q"]] += 1
    if lx is not None and pb["stackable"] and T.is_type(cls, 45):
        bl, _ = lists(lx)
        qty = bl.get((70, 0))
        C["stackable weapons at LX q%d" % q] += 1
        if 4 <= q <= 9 and qty is not None:
            C["stackable weapons of quality 4..9 with quantity > 1"] += qty > 1
            N["throw"].append("%s q%d quantity %s" % (b["code"], q, qty))
    # props slots: func 10 params, func 7 fallback, func 14 cap, rolls with negative bounds
    slots = [i for i, (t, _) in enumerate(blk) if t == "SLOT"]
    for i in slots:
        d = blk[i][1]
        f = d["func"]
        nxt = [x for x in blk[i + 1:]]
        roll = None
        for t, x in nxt:
            if t == "ROLLR":
                roll = x
                break
            if t in ("SLOTR", "SLOT"):
                break
        if f == 10:
            wr = next((x for t, x in nxt if t == "WR"), None)
            par = d["blk"][1]
            if wr is not None:
                C["func 10 writes"] += 1
                C["func 10 writes with param = par %% 3 + (par / 3) * 8"] += wr["param"] == par % 3 + (par // 3) * 8
        if f == 7 and T.is_type(cls, 45):
            m = max(pb["maxdam"], pb["max2"])
            v = d["prev"] or (roll["r"] if roll is not None and "r" in roll else None)
            if v is None:
                v = roll.get("v") if roll else None
            C["func 7 on a weapon"] += 1
            if v is not None and m * v < 100:
                C["func 7 on a weapon with max damage x v < 100 (the +1 fallback)"] += 1
                wrs = []
                for t, x in nxt:
                    if t in ("SLOTR", "SLOT"):
                        break
                    if t == "WR":
                        wrs.append((x["stat"], x["v"]))
                C["func 7 fallback: writes only max-damage stats with v = 1"] += bool(wrs) and all(
                    st in (22, 24, 160) and val == 1 for st, val in wrs)
                N["func7"].append("%s %s m %d v %s writes %s" % (game["log"], b["code"], m, v, wrs))
        if f == 14:
            cap = min(6, pb["invw"] * pb["invh"])
            if cap > 0:
                cap = min(cap, PT.max_sockets(cls, ic["ilvl"]))
                C["func 14 with cap < 1 after ItemMaxSockets" if cap < 1 else "func 14 with cap >= 1"] += 1
                if cap < 1:
                    N["sock0"].append("%s ilvl %d roll %s" % (b["code"], ic["ilvl"], bool(roll)))
                    C["func 14 with cap < 1: a roll was made"] += roll is not None
        if f == 19 and d["blk"][2] < 0:
            C["func 19 with a negative min"] += 1
    for t, d in blk:
        if t == "ROLL":
            lo, hi = d.get("min"), d.get("max")
            if lo is not None and (lo < 0 or hi < 0):
                C["PROP_RollValue calls with a negative bound"] += 1
            if lo is not None and lo > hi:
                C["PROP_RollValue calls with min > max"] += 1
    # prop 24: superior ethereal dur% items where the two orders differ
    if lx is not None and q == 3 and lx["fl"] & 0x400000:
        _, ml = lists(lx)
        dp = ml.get((75, 0))
        if dp:
            mx = pb["dur"]
            m = mx // 2
            C["superior ethereal with dur%"] += 1
            C["superior ethereal with dur% where the two orders differ"] += (m + 1) * dp // 100 > m * dp // 100
            N["durpct"].append("%s max %d dur%% %d" % (b["code"], mx, dp))
    # aff 27, 28: low-quality builds with the property lines (durability on the unit seed, the 75 % damage)
    if lx is not None and q == 1 and tags["IIS1"]:
        bl, _ = lists(lx)
        d = pb["dur"]
        if d and not pb["nodur"]:
            M = max(1, (d * 33) // 100)
            u = uniques.seedpair(tags["IIS1"][0]["useed"])
            half = M // 2
            cur = half
            if half >= 1:
                u = rng.step(*u)
                cur = half + u[0] % half
            cur = max(1, cur)
            C["low builds at LX with durability"] += 1
            C["low builds: stat 73 = max(1, durability x 33 / 100)"] += bl.get((73, 0)) == M
            C["low builds: stat 72 = M/2 + RangeB(unit seed after ItemInitStats, M/2)"] += bl.get((72, 0)) == cur
            N["low"].append(game["log"] + " %s d %d M %d pred cur %d: LX 72 %s 73 %s; base dmg %s" % (
                b["code"], d, M, cur, bl.get((72, 0)), bl.get((73, 0)),
                [(k, bl.get((k, 0))) for k in (21, 22, 23, 24, 31)]))
            if T.is_type(cls, 45):
                exp_dmg = {21: pb["mindam"], 22: pb["maxdam"], 23: pb["min2"], 24: pb["max2"]}
                floors = {21: 1, 22: 2, 23: 1, 24: 2}
                okd = all(bl.get((k, 0)) == max(floors[k], v * 75 // 100) for k, v in exp_dmg.items() if v)
                C["low weapons: base damage stats = max(floor, x * 75 / 100)"] += okd
                C["low weapons at LX"] += 1


def scan_set(paths, T, PT):
    C = collections.Counter()
    N = collections.defaultdict(list)
    for path in paths:
        log = os.path.basename(path)
        game = {"sets": set(), "uniques": set(), "log": log}
        for blk, drop in blocks(path):
            if blk == "GAME":
                game = {"sets": set(), "uniques": set(), "log": log}
                continue
            scan_block(T, PT, blk, drop, C, N, game)
    return C, N


def cmd_scan(ns):
    T = affixes.Tables(ns.excel)
    PT = props.Tables(ns.excel)
    sets = log_sets(check=not ns.nocheck)
    for k in ("STOCK", "IR"):
        C, N = scan_set([p for _, p in sets[k]], T, PT)
        for key in sorted(C):
            print("S2B scan %s %s = %d" % (k, key, C[key]))
        for key in sorted(N):
            vals = collections.Counter(N[key])
            for v, n in sorted(vals.items())[:40]:
                print("S2B note %s %s: %s%s" % (k, key, v, " (x%d)" % n if n > 1 else ""))
    return 0


# ---------------------------------------------------------------- full-table checks

def fake_item(T, cls, ilvl, ver, q=4):
    it = affixes.Item(T, {"cls": cls, "ilvl": ilvl, "ver": ver})
    it.q = q
    return it


def prop_codes(excel):
    _, rows = excel_bin.read_txt(excel_bin.find_file(excel, "properties", ".txt"))
    return [r[0].lower() for r in rows]


def blocks_of(rec, off, n):
    return [struct.unpack_from("<iiii", rec, off + 16 * k) for k in range(n)]


def cmd_tables(ns):
    T = affixes.Tables(ns.excel)
    PT = props.Tables(ns.excel)
    pc = prop_codes(ns.excel)
    P = lambda *a: print("S2B tables " + " ".join(str(x) for x in a))  # noqa: E731
    nb = len(T.items)
    # aff 9: the first rows of the two magic tables
    s0, p0 = T.magic[T.blk_s[0]], T.magic[T.blk_p[0]]
    P("aff9 magicsuffix row 0: name=%r frequency=%d itype=%s (id 1)" % (s0["name"], s0["freq"],
                                                                     [x for x in s0["itype"] if x > 0]))
    P("aff9 magicprefix row 0: name=%r frequency=%d itype=%s" % (p0["name"], p0["freq"],
                                                               [x for x in p0["itype"] if x > 0]))
    # aff 10: bases with `magic lvl`
    ml = collections.defaultdict(list)
    for c in range(nb):
        b = T.b(c)
        if b["mlvl"]:
            ml[(T.itypes[b["type"]][0:4].split(b"\0")[0].decode("latin1"), b["mlvl"])].append(b["code"])
    for (ty, m), codes in sorted(ml.items()):
        P("aff10 magic lvl %d on type %s: %d bases (%s)" % (m, ty, len(codes), " ".join(codes)))
    # aff 4: type lists and their first value < 1
    gaps = 0
    absent = 0
    for r in T.magic:
        for lst in (r["itype"], r["etype"]):
            seen_end = False
            for x in lst:
                if x < 1:
                    seen_end = True
                elif seen_end:
                    gaps += 1
        absent += r["etype"][3] == -1 or r["etype"][4] == -1
    for r in T.rare:
        for lst in (r["itype"], r["etype"]):
            seen_end = False
            for x in lst:
                if x < 1:
                    seen_end = True
                elif seen_end:
                    gaps += 1
    P("aff4 magic rows with 0xFFFF (-1) in etype4 or etype5: %d of %d; values >= 1 after a value < 1 in any "
      "itype/etype list (magic and rare tables): %d" % (absent, len(T.magic), gaps))
    # aff 15, aff 7/16: type-eligible rows per block, and sock rows on bases that cannot hold sockets
    best = (0, None)
    best2 = (0, None)
    sockcase = collections.Counter()
    sock_rows = [i for i, r in enumerate(T.magic) if r["mod1"] >= 0 and (r["mod1"] >= len(T.props)
                                                                            or T.props[r["mod1"]] == 194)]
    for c in range(nb):
        for ver in (1, 101):
            for ilvl in (1, 26, 41):
                it = fake_item(T, c, ilvl, ver)
                for name, (a0, a1) in (("suffix", T.blk_s), ("prefix", T.blk_p), ("automagic", T.blk_a)):
                    n = sum(1 for i in range(a0, a1) if T.magic[i]["ver"] < 100 or ver >= 100
                            if affixes.type_ok(T, it, T.magic[i]))
                    if n > best[0]:
                        best = (n, (T.b(c)["code"], ver, ilvl, name))
                    n2 = sum(1 for i in range(a0, a1) if (T.magic[i]["ver"] < 100 or ver >= 100)
                             and T.magic[i]["spawn"] and T.magic[i]["freq"] and affixes.type_ok(T, it, T.magic[i]))
                    if n2 > best2[0]:
                        best2 = (n2, (T.b(c)["code"], ver, ilvl, name))
    for c in range(nb):
        for ver in (1, 101):
            for ilvl in range(1, 100):
                it = fake_item(T, c, ilvl, ver)
                if T.b(c)["hasinv"] and T.maxsock(c, ilvl) > 0:
                    continue
                al = affixes.alvl_of(it)
                for i in sock_rows:
                    r = T.magic[i]
                    if (r["ver"] >= 100 and ver < 100) or r["level"] > al or (r["maxlevel"] and r["maxlevel"] < al):
                        continue
                    if r["freq"] == 0 or not r["spawn"]:
                        continue
                    if affixes.type_ok(T, it, r, skip_sock=True):
                        sockcase[(T.b(c)["code"], "exp" if ver >= 100 else "classic", r["name"])] += 1
    P("aff15 most type-eligible rows in one block, any base, version and ilvl band: %d (%s)" % best)
    P("aff15 of them also spawnable and frequency != 0 (every candidate of a drop pick): %d (%s)" % best2)
    P("aff7 sock rows (first property stat 194): %d; (base, game, row) pairs that the socket test alone refuses "
      "inside the level window, ilvl 1..99: %d" % (len(sock_rows), len(sockcase)))
    for k, v in sorted(sockcase.items())[:20]:
        P("aff7 socket test refuses: %s %s %s (ilvl values %d)" % (k + (v,)))
    # aff 22: rare version cells
    P("aff22 rare name rows with version != 0: %d of %d" % (sum(1 for r in T.rare if r["ver"] != 0), len(T.rare)))
    # aff 37: frequency 0, version 0 magic rows
    fz = [i for i, r in enumerate(T.magic) if r["freq"] == 0 and r["ver"] == 0]
    P("aff37 magic rows with frequency 0 and version 0: %d (merged ids %s..%s)" % (
        len(fz), fz[0] + 1 if fz else "-", fz[-1] + 1 if fz else "-"))
    # aff 35: automagic groups per base, every ilvl and quality that reaches the pick
    named = collections.Counter()
    empty = collections.Counter()
    checked = 0
    for c in range(nb):
        g = T.b(c)["auto"]
        if not g:
            continue
        named[g] += 1
        for q in (1, 2, 3, 4, 6, 8, 9):
            for ilvl in range(1, 100):
                it = fake_item(T, c, ilvl, 101, q)
                al = affixes.alvl_of(it)
                ok = 0
                for i in range(*T.blk_a):
                    r = T.magic[i]
                    if r["level"] > al or (r["maxlevel"] and r["maxlevel"] < al):
                        continue
                    if r["rare"] == 0 and q in (6, 8, 9):
                        continue
                    if not affixes.type_ok(T, it, r) or r["group"] != g or r["freq"] == 0:
                        continue
                    if r["cs"] != 0xFF and T.tclass(c) != 7 and r["cs"] != T.tclass(c):
                        continue
                    ok += 1
                checked += 1
                if not ok:
                    empty[(T.b(c)["code"], g, q)] += 1
    groups = sorted(set(T.magic[i]["group"] for i in range(*T.blk_a)))
    P("aff35 automagic groups in the table: %s; named by a base: %s; never named: %s" % (
        groups, sorted(named), [x for x in groups if x not in named]))
    P("aff35 (base, quality, ilvl) cases checked: %d; with no eligible automagic row: %d" % (checked, sum(empty.values())))
    for k, v in sorted(empty.items())[:20]:
        P("aff35 no eligible row: base %s group %d quality %d (%d ilvl values)" % (k + (v,)))
    # aff 30 I1: every character class has skills
    for c in range(7):
        P("aff30 class %d: %d skills, first %d" % (c, T.class_skill_count(c), T.first_class_skill(c)))
    # prop 9: set rows, add func and aprops
    srec, _ = excel_bin.read_bin(excel_bin.find_file(ns.excel, "setitems", ".bin"))
    addf = collections.Counter()
    for i, r in enumerate(srec):
        ap = [b for b in blocks_of(r, 0x118, 10) if b[0] >= 0]
        af = r[0x87]
        addf["add func %d, rows with aprops" % af] += bool(ap)
        addf["add func %d, rows" % af] += 1
        if ap and af == 0:
            P("prop9 add func 0 with aprops: row %d %s: %s" % (i, T.setit[i]["name"], [pc[b[0]] for b in ap]))
    for k in sorted(addf):
        P("prop9 setitems %s: %d" % (k, addf[k]))
    # prop 18 (L454): an `ethereal` block after a damage block in any unique or set row
    eth = pc.index("ethereal")
    dmgp = pc.index("dmg%")
    urec, _ = excel_bin.read_bin(excel_bin.find_file(ns.excel, "uniqueitems", ".bin"))
    rows_eth = 0
    late = 0
    for kind, recs_, off, n in (("unique", urec, 0x8C, 12), ("set", srec, 0x88, 9), ("set-aprop", srec, 0x118, 10)):
        for i, r in enumerate(recs_):
            codes = [b[0] for b in blocks_of(r, off, n)]
            if eth in codes:
                rows_eth += 1
                k = codes.index(eth)
                if any(c == dmgp or (0 <= c < len(PT.props) and 7 in PT.props[c]["func"]) for c in codes[k + 1:]):
                    late += 1
                    P("prop18 %s row %d: a func-7 block after ethereal" % (kind, i))
    P("prop18 rows with an `ethereal` block: %d; of them with a func-7 (dmg%%) block after it: %d" % (rows_eth, late))
    # prop 23: `sock` on a unique or set base whose socket cap is 0 at some ilvl the row can drop at
    sock = [i for i, c in enumerate(pc) if c == "sock"]
    code_of = {T.items[c][0x80:0x84]: c for c in range(nb)}
    zero = []
    for kind, recs_, off, n, codeoff, lvl in (("unique", urec, 0x8C, 12, 0x28, 0x34), ("set", srec, 0x88, 9, 0x28, 0x30),
                                             ("set-aprop", srec, 0x118, 10, 0x28, 0x30)):
        for i, r in enumerate(recs_):
            if not any(b[0] in sock for b in blocks_of(r, off, n)):
                continue
            c = code_of.get(r[codeoff:codeoff + 4])
            if c is None:
                continue
            pb = PT.base(c)
            for il in range(max(1, struct.unpack_from("<h", r, lvl)[0]), 100):
                cap = min(6, pb["invw"] * pb["invh"])
                if cap > 0 and PT.max_sockets(c, il) < 1:
                    zero.append((kind, i, pb["code"], il))
                    break
    P("prop23 unique/set rows with a `sock` block whose base has a socket cap < 1 at a reachable ilvl: %d %s" % (
        len(zero), zero[:10]))
    # us 23: unique row classes; us 27: nolimit
    lab = sum(1 for u in T.uniq if not u["code"].strip(b"\0 "))
    dis = sum(1 for u in T.uniq if u["code"].strip(b"\0 ") and not u["flags"] & 1)
    bases = set(T.items[c][0x80:0x84] for c in range(nb))
    nob = sum(1 for u in T.uniq if u["code"].strip(b"\0 ") and u["code"] not in bases)
    nob_en = sum(1 for u in T.uniq if u["code"].strip(b"\0 ") and u["code"] not in bases and u["flags"] & 1)
    P("us23 uniqueitems rows %d: label (blank code) %d, disabled %d, code of no base %d (of them enabled %d); "
      "bases with a blank code: %d" % (len(T.uniq), lab, dis, nob, nob_en,
                                        sum(1 for c in range(nb) if not T.items[c][0x80:0x84].strip(b"\0 "))))
    P("us27 uniqueitems rows with nolimit (flag bit 1): %d" % sum(1 for u in T.uniq if u["flags"] & 2))
    # us 32/42: classic sets
    sets_, _ = excel_bin.read_bin(excel_bin.find_file(ns.excel, "sets", ".bin"))
    cl = [i for i, r in enumerate(sets_) if struct.unpack_from("<I", r, 4)[0] < 100]
    rows = [i for i, r in enumerate(T.setit) if r["sver"] < 100]
    P("us32 sets with version < 100: %d (%s); setitems rows of them: %d (rows %d..%d, contiguous %s)" % (
        len(cl), cl, len(rows), rows[0], rows[-1], rows == list(range(rows[0], rows[-1] + 1))))
    lay = [f[0] if isinstance(f, tuple) else getattr(f, "name", str(f)) for f in excel_bin.get_layout("setitems")["fields"]]
    P("us33 setitems columns named enabled/ladder/nolimit/firstLadderSeason: %s" % (
        [x for x in map(str, lay) if any(w in x.lower() for w in ("enabled", "ladder", "nolimit"))] or "none"))
    # us 15: the pre-switch overrides over the roll's possible results, every base
    changed = []
    for c in range(nb):
        b = T.b(c)
        t = b["type"]
        tr = T.itypes[t] if 0 <= t < len(T.itypes) else None
        magic, rare, normal = (tr[0x14], tr[0x15], tr[0x16]) if tr else (0, 0, 1)
        unique, quest = T.items[c][0x129], T.items[c][0x12A]
        if unique or (magic and quest):
            continue                # neither base is an entry of any TC (items/0002 S2a, quality 11)
        if normal:
            out = {2}
        elif magic:
            out = {4, 5, 7} | ({6} if rare else set())
        else:
            out = {1, 2, 3, 4, 5, 7} | ({6} if rare else set())
        for q in out:
            q2 = q
            if magic:
                q2 = 7 if quest else (q2 if 4 <= q2 <= 9 else 4)
            if not rare and q2 == 6:
                q2 = 4
            if unique:
                q2 = 7
            if normal:
                q2 = 2
            if q2 != q:
                changed.append((b["code"], q, q2))
    P("us15 bases checked: %d; roll results an override would change: %d %s" % (nb, len(changed), changed[:10]))
    return 0


# ---------------------------------------------------------------- static scans

SYMBOLS = os.path.join(ROOT, "re", "symbols.csv")


def func_starts():
    out = []
    for ln in open(SYMBOLS):
        f = ln.split(",")
        if len(f) > 2 and f[1] == "func" and f[0].startswith("0x"):
            out.append((int(f[0], 16), f[2]))
    return sorted(out)


def containing(starts, va):
    """The named function (symbols.csv) whose start is the nearest at or below va, as 'name@0x...'. Only a hint:
    an unnamed function in between is not seen (tools/ghidra.sh instrat gives the containing function)."""
    best = None
    for a, n in starts:
        if a <= va:
            best = (a, n)
        else:
            break
    return "%s@0x%08X" % (best[1], best[0]) if best else "?"


def disasm(start, end, exe):
    """r2 linear disassembly of [start, end): [(va, text)]. r2 is a second tool next to Ghidra (tooling.md)."""
    import subprocess
    cmd = ["r2", "-q", "-e", "scr.color=0", "-e", "asm.lines=0", "-e", "asm.comments=0", "-e", "asm.bytes=0",
           "-e", "bin.relocs.apply=true", "-c", "s 0x%x; pD %d" % (start, end - start), exe]
    txt = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    out = []
    for ln in txt.splitlines():
        ln = ln.strip()
        if ln.startswith("0x"):
            va, _, rest = ln.partition(" ")
            out.append((int(va, 16), " ".join(rest.split())))
    return out


def insn_covering(va, needle, exe):
    """The instruction that holds the 4 displacement bytes at va: it starts 1..7 bytes before va, ends right after
    them (no immediate follows in these forms) and its text has needle; the earliest such start wins (a SIB form)."""
    import subprocess
    for k in range(7, 0, -1):
        out = subprocess.run(["r2", "-q", "-e", "scr.color=0", "-c", "pdj 1 @ 0x%x" % (va - k), exe],
                             capture_output=True, text=True, check=True).stdout
        try:
            d = json.loads(out)[0]
        except (ValueError, IndexError):
            continue
        if d.get("size", 0) == k + 4 and needle in d.get("disasm", ""):
            return "0x%08X %s" % (va - k, d["disasm"])
    return "?"


# (claim, [(function start, end)], forbidden substrings of an instruction): an instruction that contains one of them
# would be a read of the not-read column (the record's displacement, or the flag mask's g_BitMask32 slot)
NOT_READ = [
    ("us4 UniqueItems carry1 (+0x2C bit 2: the mask slot g_BitMask32[2] 0x6ce270) and lvl req (+0x36; +0xA from "
     "the +0x2C loop cursor EBX)",
     [(0x005566B0, 0x00556A5C), (0x00556530, 0x005565E0), (0x005564A0, 0x00556530)],
     ["0x6ce270", "+ 0x36]", "[ebx + 0xa]"]),
    ("aff3 magic affix levelreq +0x65, class +0x67, classlevelreq +0x68, transformcolor +0x56, +0x57, "
     "divide/multiply/add +0x84/+0x88/+0x8C",
     [(0x005C1560, 0x005C18E0), (0x0065E620, 0x0065E710), (0x005C1500, 0x005C1560), (0x005C0D00, 0x005C0D70),
      (0x005C18E0, 0x005C1940), (0x005C1940, 0x005C19A0)],
     ["+ 0x65]", "+ 0x67]", "+ 0x68]", "+ 0x56]", "+ 0x57]", "+ 0x84]", "+ 0x88]", "+ 0x8c]"]),
    ("aff3 rare name record +0x000..+0x00B in ITEMS_RareNameTypeOk (record in EBX = [ebp+0xc]; ITEMS_PickRareName "
     "only walks the g_RareAffixInfo block pointers and hands each record to it)",
     [(0x0065E710, 0x0065E7D0)],
     ["[ebx]", "[ebx + 1]", "[ebx + 2]", "[ebx + 3]", "[ebx + 4]", "[ebx + 5]", "[ebx + 6]", "[ebx + 7]",
      "[ebx + 8]", "[ebx + 9]", "[ebx + 0xa]", "[ebx + 0xb]"]),
    # S2b review: ITEMS_PickMagicAffix walks the records with ESI = record + 0x60 (add esi, 0x60 at 0x005C16D0; the
    # loop reads [esi - 0xc], [esi - 8], [esi - 4], [esi], [esi + 4], [esi + 6], [esi + 0x22], [esi - 0x3e]), so the
    # forbidden bytes also appear as cursor displacements. Operand sizes of the cursor reads were checked by hand: the
    # widest is a dword at +0x5C/+0x60, none overlaps +0x56/+0x57, +0x65, +0x67..+0x69 or +0x84..+0x8F.
    ("aff3 the same columns through the ESI = record + 0x60 cursor of ITEMS_PickMagicAffix",
     [(0x005C16D0, 0x005C18A0)],
     ["[esi + 5]", "[esi + 7]", "[esi + 8]", "[esi + 9]", "[esi - 0xa]", "[esi - 9]", "[esi + 0x24]", "[esi + 0x28]",
      "[esi + 0x2c]"]),
]


def cmd_static(ns):
    exe = xrefscan.EXE
    data = open(exe, "rb").read()
    base, secs = xrefscan.sections(exe)
    starts = func_starts()
    P = lambda *a: print("S2B static " + " ".join(str(x) for x in a))  # noqa: E731
    targets = [
        ("us3 g_pItemRatio", 0x0096CC4C), ("us3 g_nItemRatio", 0x0096CC48), ("us3 ITEMRATIO_Select", 0x00637910),
        ("us3 ItemRatio free (mov eax,[g_pItemRatio]; push; call)", 0x006378F0),
        ("us3 ItemRatio getter (mov eax,&g_nItemRatio; ret)", 0x00637900),
        ("us24 g_UniqueCandidates", 0x008846F8), ("us24 g_UniqueCandidates+4", 0x008846FC),
        ("us24 g_UniqueCandidates-8", 0x008846F0),
        ("prop1 ItemApplyProps", 0x0065FEC0), ("prop1 PROP_ApplyBlock", 0x0065FD70),
        ("prop1 SetBonusApply", 0x00660120),
        ("aff1 crafted builder", 0x005C21D0), ("aff1 quality-9 name pick", 0x005C1BC0),
        ("us34 made test", 0x005564D0), ("us34 made test v0", 0x005564A0), ("us34 UniqueMarkMade", 0x00556530),
    ]
    for what, t in targets:
        hits = xrefscan.scan(data, base, secs, t)
        P("xref %s 0x%08X: %d hit(s)" % (what, t, len(hits)))
        for kind, at, hx in hits:
            P("   %-16s 0x%08X after %s" % (kind, at, containing(starts, at)))
    # prop 5: is any data/calc function's address stored anywhere (an indirect-call target)?
    calc = []
    for ln in open(SYMBOLS):
        f = ln.split(",")
        if len(f) > 5 and f[1] == "func" and f[5] in ("data/calc",):
            calc.append(int(f[0], 16))
    stored = []
    for a in calc:
        for kind, at, hx in xrefscan.scan(data, base, secs, a):
            if kind.startswith("abs32") and at % 4 == 0:
                stored.append((a, kind, at))
    P("prop5 data/calc functions: %d; aligned abs32 occurrences of their addresses (stored pointers): %d %s" % (
        len(calc), len(stored), ["0x%08X@0x%08X" % (a, at) for a, _, at in stored]))
    # us 27, us 34: the made-uniques displacement 0x1B24 in executable code
    tb = struct.pack("<I", 0x1B24)
    sites = []
    for sct in secs:
        if not sct["flags"] & xrefscan.IMAGE_SCN_MEM_EXECUTE:
            continue
        blob = data[sct["raw"]:sct["raw"] + min(sct["rsize"], sct["vsize"])]
        k = blob.find(tb)
        while k >= 0:
            sites.append(base + sct["va"] + k)
            k = blob.find(tb, k + 1)
    P("us27 bytes 24 1b 00 00 (displacement 0x1B24) in executable sections: %d" % len(sites))
    for va in sites:
        P("   0x%08X after %s: %s" % (va, containing(starts, va), insn_covering(va, "0x1b24", exe)))
    # us 4, aff 3: not-read columns
    for what, ranges, bad in NOT_READ:
        n = 0
        hit = []
        for a, b in ranges:
            for va, t in disasm(a, b, exe):
                n += 1
                if any(x in t for x in bad):
                    hit.append("0x%08X %s" % (va, t))
        P("notread %s: %d instructions in %d functions, matching: %d %s" % (what, n, len(ranges), len(hit), hit[:6]))
    # the closure files of tools/ghidra.sh rngcallgraph, when given
    for f in ns.closure or []:
        fns = set()
        for ln in open(f):
            if ln.startswith("fn 0x"):
                fns.add(int(ln.split()[1], 16))
        icalls = sum(1 for ln in open(f) if ln.strip().startswith("icall"))
        names = {a: n for a, n in starts}
        probe = [0x004C0D20, 0x004E6720, 0x004E67D0, 0x0055C2C0, 0x00660120, 0x006600A0, 0x00637910, 0x00637620,
                 0x006378F0, 0x00637900, 0x00565AB0, 0x00450950, 0x00530930, 0x00530BF0, 0x006C0BC0, 0x005316D0,
                 0x005317B0, 0x005697B0, 0x0062AF80, 0x0062FFF0, 0x00626200, 0x006266C0] + calc
        inside = sorted(set(a for a in probe if a in fns))
        P("closure %s: functions %d, indirect call sites %d; of the probed functions inside: %s" % (
            os.path.basename(f), len(fns), icalls, ["%s@0x%08X" % (names.get(a, "?"), a) for a in inside]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

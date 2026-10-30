#!/usr/bin/env python3
"""Golden traces: seeds and their expected world and drops, as conformance cases (plan 0059 Phase 1).

    python3 -I tools/golden.py emit --out SET.jsonl [--run NAME] [--excel DIR] [--drops-per-log N] [--no-verify]
                                    [--chain-check] LOG [LOG ...]                        # observed cases from kept logs
    python3 -I tools/golden.py emit --out SET.jsonl --predicted --seeds 4802,100-103 [--diffs 0,1,2] [--exps 0,1]
                                    [--levels 1,57,103] [--excel DIR]                   # predicted cases from the model
    python3 -I tools/golden.py check SET.jsonl CANDIDATE.jsonl [--fields PREFIX] [--limit N]
    python3 -I tools/golden.py digest SET.jsonl          # the set's digest (header identity + canonical case lines)
    python3 -I tools/golden.py digest --value            # sha256 of the canonical JSON on stdin (bulky output values)
    python3 -I tools/golden.py fields                    # every field pattern with its spec step
    python3 -I tools/golden.py sample SET --out S.jsonl [--worlds N] [--drops N]   # a small spread subset of a set
    python3 -I tools/golden.py merge A.jsonl B.jsonl ... --out M.jsonl             # sets of one header, joined

Format: docs/formats/golden-trace.md (JSON Lines; line 1 the header, then one case per line). Two kinds, never mixed:
`observed` (expected values read from a kept log of the real game, and reproduced by the reviewed models before the
case is written) and `predicted` (the models alone). Nothing here reads game files except through the reviewed
tools (tools/chain.py gen, tools/tc.py); a case holds seeds, indices, codes, counts and digests, never table rows.

emit observed: per log, one `world` case (the seeds of game creation and of the levels the log created, compared with
  `tools/chain.py gen` from the log's -seed) and one `drop` case per TC_ResolveDrops call (TCR .. TCEND, tools/gdb/
  tc-drops.gdb), each replayed through tools/tc.py with the quality roll modelled; a case that does not reproduce is not
  written and is counted (the exit code is 1). --chain-check also runs `tools/chain.py check` on the logs
  (sub-process; slow) and makes a non-zero exit fatal.
check: a candidate file holds one JSON line per case, {"id": ..., "outputs": {field: value}} (a full case line of a set,
  with "expected", is accepted too: a set checks against itself). Every expected field of every case of the set is
  compared; the report is per field pattern and per case, the exit code 0 only when nothing is missing or different.

Stdlib only. Read-only on game files and logs.
"""
import argparse
import collections
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

ROOT = os.path.dirname(HERE)
DEFAULT_EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
VERSION = 1
KINDS = ("observed", "predicted")
SCOPE = "world,drops"

# field pattern -> (spec step, spec section). A trailing `.<n>` in a name is an index (level id, act number): the
# pattern ends in `.N`. docs/formats/golden-trace.md lists the same table.
FIELDS = collections.OrderedDict([
    ("chain.A1.game_seed", ("A1 game seed Init(N)", "chain#algorithm")),
    ("chain.A1.map_seed", ("A1 map seed N", "chain#algorithm")),
    ("chain.A2.monster_regions_seed", ("A2 game draw 1, Init(low)", "chain#algorithm")),
    ("chain.A3.object_region_seed", ("A3 game draw 2, object-region seed O", "chain#algorithm")),
    ("chain.A3.game_seed_after", ("A3 game seed after draw 2", "chain#algorithm")),
    ("chain.A4.store_seed", ("A4 game draw 3", "chain#algorithm")),
    ("chain.A4.quest_seed", ("A4 game draw 4", "chain#algorithm")),
    ("chain.A4.game_seed_after_creation", ("A4 game seed after draw 4", "chain#algorithm")),
    ("chain.B1.level_seed_base.N", ("B1 levelSeedBase of act N", "chain#algorithm")),
    ("chain.B2.level_seed.N", ("B2 create seed of level N, base + id", "chain#algorithm")),
    ("chain.B2.level_seeds_digest", ("B2 digest of {level id: seed} over every level", "chain#algorithm")),
    ("monsters.pool.mlvl.N", ("monster level of level N", "monsters/pool")),
    ("monsters.pool.den.N", ("monster density of level N", "monsters/pool")),
    ("monsters.pool.uniques.N", ("[min, max] unique count of level N", "monsters/pool")),
    ("monsters.pool.region.N", ("region pool (class ids) of level N", "monsters/pool")),
    ("monsters.pool.digest", ("digest of the pools of every level", "monsters/pool")),
    ("chain.G1.nodrop", ("G1 [NoDrop, total] per roll", "items/tc")),
    ("chain.G1.pick", ("G1 [range, roll] per pick", "items/tc")),
    ("chain.G1.select", ("G1 selected entry index per pick", "items/tc")),
    ("chain.G1.subtc", ("G1 sub-treasure-class ids entered, in order", "items/tc")),
    ("chain.G1.quality", ("G1 quality rolled per item", "items/quality")),
    ("chain.G1.item", ("G1 [base item id, quality, unique/set index] per item", "items/quality")),
    ("chain.G1.count", ("G1 items made", "items/tc")),
    ("chain.G1.end_seed", ("G1 the dying unit's seed at TCEND", "items/tc")),
])
_PAT = [(re.compile("^" + re.escape(p).replace(r"\.N", r"\.\d+") + "$"), p) for p in FIELDS]


def pattern(field):
    for rx, p in _PAT:
        if rx.match(field):
            return p
    return None


# --- canonical form and digests -------------------------------------------------------------------------------------
def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def value_digest(obj):
    return hashlib.sha256(canon(obj).encode()).hexdigest()


def set_digest(header, cases):
    """The identity of a set: header (version, exe, tables, scope) and every case line, ordered by id."""
    h = hashlib.sha256()
    h.update(canon({k: header.get(k) for k in ("golden", "version", "game_exe_sha256", "tables_digest", "scope")}).encode())
    for c in sorted(cases, key=lambda c: c["id"]):
        h.update(b"\n" + canon(c).encode())
    return h.hexdigest()


def fmt(s):
    return "%08x:%08x" % tuple(s)


def pinned_exe_sha():
    try:
        txt = open(os.path.join(ROOT, "docs", "inventory.md"), errors="replace").read(4000)
        m = re.search(r"\|\s*`game\.exe`\s*\|[^|]*\|\s*\*\*`([0-9a-f]{64})`\*\*", txt)
        return m.group(1) if m else None
    except OSError:
        return None


def tables_digest(excel):
    """sha256 over the sorted "name sha256" lines of the excel directory (the table set the cases were built on)."""
    if not os.path.isdir(excel):
        return None
    lines = []
    for n in sorted(os.listdir(excel)):
        p = os.path.join(excel, n)
        if os.path.isfile(p):
            lines.append("%s %s" % (n.lower(), hashlib.sha256(open(p, "rb").read()).hexdigest()))
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def make_header(excel, name):
    return {"golden": "trace", "version": VERSION, "set": name, "scope": SCOPE,
            "game_exe_sha256": pinned_exe_sha(), "tables_digest": tables_digest(excel),
            "case_kinds": list(KINDS)}


# --- world cases ---------------------------------------------------------------------------------------------------
def world_expected(seed, diff, exp, excel, levels):
    """The model's expected fields for one seed. levels: the level ids to give singly (None: none); the digests always
    cover every level."""
    import chain
    import rng
    g, acts, lv = chain.gen(seed, diff, exp, excel, None)
    out = collections.OrderedDict()
    out["chain.A1.game_seed"] = fmt(g["game_seed"])
    out["chain.A1.map_seed"] = g["map_seed"]
    out["chain.A2.monster_regions_seed"] = fmt(g["monster_regions"])
    out["chain.A3.object_region_seed"] = fmt(g["object_region"])
    s = rng.step(*rng.step(*g["game_seed"]))            # game draws 1 and 2 (rng/seeds step 1, note 7a)
    out["chain.A3.game_seed_after"] = fmt(s)
    out["chain.A4.store_seed"] = fmt(g["store"])
    out["chain.A4.quest_seed"] = fmt(g["quest"])
    out["chain.A4.game_seed_after_creation"] = fmt(g["game_seed_after_creation"])
    for a in acts:
        out["chain.B1.level_seed_base.%d" % a["act"]] = a["levelSeedBase"]
    byid = {r["id"]: r for r in lv}
    out["chain.B2.level_seeds_digest"] = value_digest({str(i): fmt(r["seed"]) for i, r in sorted(byid.items()) if r["seed"]})
    out["monsters.pool.digest"] = value_digest({str(i): [r["mlvl"], r["den"], r["umin"], r["umax"], r["pool"]]
                                                for i, r in sorted(byid.items())})
    for i in (levels or []):
        r = byid.get(i)
        if r is None:
            continue
        if r["seed"]:
            out["chain.B2.level_seed.%d" % i] = fmt(r["seed"])
        out["monsters.pool.mlvl.%d" % i] = r["mlvl"]
        out["monsters.pool.den.%d" % i] = r["den"]
        out["monsters.pool.uniques.%d" % i] = [r["umin"], r["umax"]]
        out["monsters.pool.region.%d" % i] = r["pool"]
    return out


def predicted_cases(seeds, diffs, exps, levels, excel):
    for seed in seeds:
        for diff in diffs:
            for exp in exps:
                yield {"id": "world:p:%d:d%d:e%d" % (seed, diff, exp), "kind": "predicted", "type": "world",
                       "source": {"model": "tools/chain.py gen"},
                       "inputs": {"seed": seed, "difficulty": diff, "expansion": exp, "levels": levels},
                       "expected": world_expected(seed, diff, exp, excel, levels), "quirks": []}


# --- observed cases ------------------------------------------------------------------------------------------------
def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def log_seed(path):
    with open(path, errors="replace") as fh:
        m = re.match(r"# d2run seed=(\d+)", fh.readline())
    return int(m.group(1)) if m else None


def read_world_lines(path):
    """GAME, OGC and LC0 lines of a log: the seeds the log itself shows."""
    game = ogc = None
    lc0 = {}
    base = None
    for line in open(path, errors="replace"):
        if line.startswith("GAME "):
            m = re.search(r"seed=([0-9a-f]{8}:[0-9a-f]{8})", line)
            if m and game is None:
                game = m.group(1)
        elif line.startswith("OGC {") and ogc is None:
            try:
                ogc = json.loads(line[4:])
            except ValueError:
                pass
        elif line.startswith("LC0 {"):
            try:
                o = json.loads(line[4:])
            except ValueError:
                continue
            lc0.setdefault(o["id"], o["seed"])
            base = o.get("base", base)
    return game, ogc, lc0, base


def first_diff_exp(path):
    for line in open(path, errors="replace"):
        if line.startswith("TCR "):
            m = re.search(r" diff=(\d+) exp=(\d+)", line)
            if m:
                return int(m.group(1)), int(m.group(2))
    return None, None


def observed_world(path, excel, src):
    """One observed world case, or (None, reason). Observed values are the log's; the model must agree first."""
    import chain
    seed = log_seed(path)
    game, ogc, lc0, base = read_world_lines(path)
    if seed is None or game is None or not lc0:
        return None, "no GAME/LC0 lines or no -seed in the header"
    diff, exp = first_diff_exp(path)
    mod = world_expected(seed, diff or 0, 1 if exp is None else exp, excel, sorted(lc0))
    exp_out = collections.OrderedDict()
    exp_out["chain.A1.game_seed"] = game
    exp_out["chain.A1.map_seed"] = seed
    if ogc:
        exp_out["chain.A3.object_region_seed"] = ogc["os"]
        exp_out["chain.A3.game_seed_after"] = ogc["gs"]
    if base is not None:
        for a in {chain.act_of(i) for i in lc0}:
            exp_out["chain.B1.level_seed_base.%d" % a] = base
    for i, s in sorted(lc0.items()):
        exp_out["chain.B2.level_seed.%d" % i] = s
    for k, v in exp_out.items():
        if mod.get(k) != v:
            return None, "model %r != log %r at %s" % (mod.get(k), v, k)
    return {"id": "world:o:%s" % src["log"], "kind": "observed", "type": "world", "source": src,
            "inputs": {"seed": seed, "difficulty": diff, "expansion": exp, "levels": sorted(lc0)},
            "expected": exp_out, "quirks": []}, None


def _i(v):
    return int(v)


def drop_case(call, k, src):
    """A case from one read_calls entry (TCR .. TCEND): inputs from the TCR line, expected from the events after it."""
    events = [(h, kv) for h, kv in call if not h.startswith("_")]
    tcr = events[0][1]
    inp = collections.OrderedDict()
    inp["tc"] = _i(tcr["tc"])
    inp["ilvl"] = _i(tcr["ilvl"])
    inp["unit_seed"] = tcr["seed"]
    inp["game_seed"] = tcr["gseed"]
    inp["difficulty"] = _i(tcr["diff"])
    inp["expansion"] = _i(tcr["exp"])
    inp["source_type"] = _i(tcr["stype"])
    inp["source_class"] = _i(tcr["sclass"])
    for k2, n in (("mflags", "monster_flags"), ("nonodrop", "nonodrop"), ("max", "max"), ("fq", "fq"),
                  ("suid", "super_unique"), ("ktype", "killer_type"), ("kclass", "killer_class"), ("g6a", "g6a")):
        if k2 in tcr:
            inp[n] = tcr[k2] if k2 == "mflags" else _i(tcr[k2])
    for h, n in (("PLAYERS", "players"), ("PARTY", "party"), ("CAP", "cap")):
        for hh, kv in events:
            if hh == h:
                inp[n] = _i(kv[n])
    ex = collections.OrderedDict()
    nodrop, pick, sel, sub, qual, items = [], [], [], [], [], []
    end = None
    for h, kv in events[1:]:
        if h == "NDP":
            nodrop.append([_i(kv["ndp"]), _i(kv["total"])])
        elif h == "PICK":
            pick.append([_i(kv["range"]), _i(kv["roll"])])
        elif h == "SEL":
            sel.append(_i(kv["i"]))
        elif h == "SUB":
            sub.append(_i(kv["tc"]))
        elif h == "QOUT":
            qual.append(_i(kv["q"]))
        elif h == "CPRE":
            items.append([_i(kv["item"]), _i(kv["q"]), _i(kv["uidx"])])
        elif h == "TCEND":
            end = kv
    ex["chain.G1.nodrop"] = nodrop
    ex["chain.G1.pick"] = pick
    ex["chain.G1.select"] = sel
    ex["chain.G1.subtc"] = sub
    ex["chain.G1.quality"] = qual
    ex["chain.G1.item"] = items
    ex["chain.G1.count"] = _i(end["count"])
    ex["chain.G1.end_seed"] = end["seed"]
    return {"id": "drop:o:%s:%d" % (src["log"], k), "kind": "observed", "type": "drop", "source": dict(src, call=k),
            "inputs": inp, "expected": ex, "quirks": []}


def observed_drops(path, src, T, q, verify, limit):
    import tc
    calls = tc.read_calls(path)
    n = bad = 0
    cases = []
    for k, (call0, err) in enumerate(calls):
        if err or not call0 or call0[0][0] != "TCR" or call0[-1][0] != "TCEND":
            bad += 1
            continue
        if verify:
            buf = io.StringIO()
            with redirect_stdout(buf):
                res = tc.replay_calls(T, [(call0, None)], q, False)
            if res[1]:
                bad += 1
                continue
        n += 1
        if limit is None or len(cases) < limit:
            cases.append(drop_case(call0, k, src))
    return cases, n, bad


def cmd_emit(ns):
    excel = ns.excel
    cases = []
    rc = 0
    if ns.predicted:
        seeds = []
        for part in ns.seeds.split(","):
            a, _, b = part.partition("-")
            seeds.extend(range(int(a), int(b or a) + 1))
        levels = [int(x) for x in ns.levels.split(",")] if ns.levels else []
        cases = list(predicted_cases(seeds, [int(x) for x in ns.diffs.split(",")],
                                     [int(x) for x in ns.exps.split(",")], levels, excel))
        name = ns.name or "predicted"
    else:
        import quality
        import tc
        T = tc.Tables(excel)
        q = (quality.Tables(excel), 0, False)
        name = ns.name or ns.run or "observed"
        tot = collections.Counter()
        for path in ns.logs:
            src = {"log": os.path.basename(path), "log_sha256": file_sha(path)[:16]}
            if ns.run:
                src["run"] = ns.run
            w, why = observed_world(path, excel, src)
            if w:
                cases.append(w)
                tot["world cases"] += 1
            else:
                tot["logs with no world case"] += 1
                print("%s: no world case (%s)" % (src["log"], why))
                if why and why.startswith("model"):
                    rc = 1
            if ns.drops_per_log != 0:
                dc, n, bad = observed_drops(path, src, T, q, not ns.no_verify,
                                            None if ns.drops_per_log < 0 else ns.drops_per_log)
                cases.extend(dc)
                tot["drop calls reproduced"] += n
                tot["drop calls failed or cut off"] += bad
                if bad:
                    rc = 1
        for k in sorted(tot):
            print("  %-40s %d" % (k, tot[k]))
        if ns.chain_check:
            r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "chain.py"), "check"] + ns.logs +
                               ["--excel", excel], capture_output=True, text=True)
            print("chain.py check: exit %d; %s" % (r.returncode, (r.stdout.strip().splitlines() or [""])[-1]))
            if r.returncode:
                rc = 1
    header = make_header(excel, name)
    with open(ns.out, "w") as fh:
        fh.write(canon(header) + "\n")
        for c in cases:
            fh.write(canon(c) + "\n")
    print("%s: %d cases (%s), set digest %s" % (ns.out, len(cases),
          ", ".join("%s %d" % kv for kv in sorted(collections.Counter(c["kind"] + " " + c["type"] for c in cases).items())),
          set_digest(header, cases)))
    return rc


# --- check and digest ----------------------------------------------------------------------------------------------
def read_set(path):
    with open(path) as fh:
        lines = [json.loads(x) for x in fh if x.strip()]
    if not lines or lines[0].get("golden") != "trace":
        raise SystemExit("%s: no golden-trace header on line 1" % path)
    h = lines[0]
    if h.get("version") != VERSION:
        raise SystemExit("%s: format version %r, this tool reads %d" % (path, h.get("version"), VERSION))
    return h, lines[1:]


def read_candidate(path):
    out = {}
    with open(path) as fh:
        for x in fh:
            if not x.strip():
                continue
            o = json.loads(x)
            if o.get("golden") == "trace":
                continue
            out[o["id"]] = o.get("outputs", o.get("expected", {}))
    return out


def cmd_check(ns):
    header, cases = read_set(ns.set)
    cand = read_candidate(ns.candidate)
    per_pat = collections.Counter()
    tot_pat = collections.Counter()
    missing_case = []
    bad_cases = []
    fields_checked = 0
    for c in cases:
        got = cand.get(c["id"])
        if got is None:
            missing_case.append(c["id"])
            continue
        diffs = []
        for f, v in c["expected"].items():
            if ns.fields and not f.startswith(ns.fields):
                continue
            p = pattern(f) or f
            tot_pat[p] += 1
            fields_checked += 1
            if f not in got:
                per_pat[p] += 1
                diffs.append((f, v, "<missing>"))
            elif canon(got[f]) != canon(v):
                per_pat[p] += 1
                diffs.append((f, v, got[f]))
        if diffs:
            bad_cases.append((c, diffs))
    ids = {c["id"] for c in cases}
    extra = [i for i in cand if i not in ids]
    print("%d cases in the set, %d fields compared" % (len(cases), fields_checked))
    for p in sorted(tot_pat):
        print("  %-36s %6d compared %6d different" % (p, tot_pat[p], per_pat[p]))
    for c, diffs in bad_cases[:ns.limit]:
        tag = (" quirks %s" % ",".join(c["quirks"])) if c.get("quirks") else ""
        print("MISMATCH %s [%s]%s" % (c["id"], c["kind"], tag))
        for f, want, got in diffs[:6]:
            print("    %s: expected %s, got %s" % (f, canon(want)[:100], canon(got)[:100] if got != "<missing>" else got))
    if len(bad_cases) > ns.limit:
        print("... %d more cases with differences" % (len(bad_cases) - ns.limit))
    if missing_case:
        print("MISSING %d cases, first %s" % (len(missing_case), ", ".join(missing_case[:3])))
    if extra:
        print("note: %d candidate cases are not in the set" % len(extra))
    ok = not bad_cases and not missing_case
    print("golden: %s" % ("pass" if ok else "FAIL (%d cases differ, %d missing)" % (len(bad_cases), len(missing_case))))
    return 0 if ok else 1


def cmd_digest(ns):
    if ns.value:
        print(value_digest(json.load(sys.stdin)))
        return 0
    header, cases = read_set(ns.set)
    print(set_digest(header, cases))
    return 0


def write_set(path, header, cases):
    with open(path, "w") as fh:
        fh.write(canon(header) + "\n")
        for c in cases:
            fh.write(canon(c) + "\n")


def spread(groups, n):
    """n items taken round-robin over the groups (each group's items in id order, evenly spaced)."""
    picked = []
    keys = sorted(groups)
    idx = {k: 0 for k in keys}
    while len(picked) < n and any(idx[k] < len(groups[k]) for k in keys):
        for k in keys:
            g = groups[k]
            if idx[k] < len(g) and len(picked) < n:
                picked.append(g[(idx[k] * 7919 + len(g) // 3) % len(g)] if idx[k] else g[len(g) // 3])
                idx[k] += 1
    seen, out = set(), []
    for c in picked:
        if c["id"] not in seen:
            seen.add(c["id"])
            out.append(c)
    return out


def cmd_sample(ns):
    header, cases = read_set(ns.set)
    w = collections.defaultdict(list)
    d = collections.defaultdict(list)
    for c in sorted(cases, key=lambda c: c["id"]):
        i = c["inputs"]
        if c["type"] == "world":
            w[(i.get("difficulty"), i.get("expansion"))].append(c)
        else:
            d[(i["difficulty"], i["expansion"], c["expected"]["chain.G1.count"] > 0, len(c["expected"]["chain.G1.subtc"]) > 1)].append(c)
    out = spread(w, ns.worlds) + spread(d, ns.drops)
    write_set(ns.out, header, out)
    print("%s: %d cases, set digest %s" % (ns.out, len(out), set_digest(header, out)))
    return 0


def cmd_merge(ns):
    header = None
    cases = {}
    for p in ns.sets:
        h, cs = read_set(p)
        if header is None:
            header = h
        for k in ("version", "game_exe_sha256", "tables_digest", "scope"):
            if h.get(k) != header.get(k):
                raise SystemExit("%s: header %s differs" % (p, k))
        for c in cs:
            cases[c["id"]] = c
    header = dict(header, set=ns.name or "+".join(os.path.basename(p) for p in ns.sets))
    write_set(ns.out, header, list(cases.values()))
    print("%s: %d cases, set digest %s" % (ns.out, len(cases), set_digest(header, list(cases.values()))))
    return 0


def cmd_fields(ns):
    for p, (step, sec) in FIELDS.items():
        print("%-36s %s  [%s]" % (p, step, sec))
    return 0


def build_parser():
    ap = argparse.ArgumentParser(prog="golden.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("emit")
    e.add_argument("logs", nargs="*")
    e.add_argument("--out", required=True)
    e.add_argument("--run")
    e.add_argument("--name")
    e.add_argument("--excel", default=DEFAULT_EXCEL)
    e.add_argument("--drops-per-log", type=int, default=-1, help="-1 all, 0 none, N the first N reproduced calls")
    e.add_argument("--no-verify", action="store_true")
    e.add_argument("--chain-check", action="store_true")
    e.add_argument("--predicted", action="store_true")
    e.add_argument("--seeds", default="1")
    e.add_argument("--diffs", default="0,1,2")
    e.add_argument("--exps", default="0,1")
    e.add_argument("--levels")
    c = sub.add_parser("check")
    c.add_argument("set")
    c.add_argument("candidate")
    c.add_argument("--fields")
    c.add_argument("--limit", type=int, default=20)
    d = sub.add_parser("digest")
    d.add_argument("set", nargs="?")
    d.add_argument("--value", action="store_true")
    sub.add_parser("fields")
    sa = sub.add_parser("sample")
    sa.add_argument("set")
    sa.add_argument("--out", required=True)
    sa.add_argument("--worlds", type=int, default=6)
    sa.add_argument("--drops", type=int, default=8)
    m = sub.add_parser("merge")
    m.add_argument("sets", nargs="+")
    m.add_argument("--out", required=True)
    m.add_argument("--name")
    return ap


def main(argv):
    ns = build_parser().parse_args(argv[1:])
    if ns.cmd == "emit" and not ns.predicted and not ns.logs:
        raise SystemExit("emit: give logs, or --predicted")
    if ns.cmd == "digest" and not ns.value and not ns.set:
        raise SystemExit("digest: give a set file or --value")
    return {"emit": cmd_emit, "check": cmd_check, "digest": cmd_digest, "fields": cmd_fields,
            "sample": cmd_sample, "merge": cmd_merge}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

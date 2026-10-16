#!/usr/bin/env python3
"""Plan 0038 batch S3a: checks over the kept stock logs of the monster, hireling and player runs, and the full-table
checks the batch rows name.

    python3 -I tools/mon_sweep.py logs [--write FILE]   the log set, sha256 checked against the run records
    python3 -I tools/mon_sweep.py pool                  monsters/pool rows (variant caps, FindAdd, monster level)
    python3 -I tools/mon_sweep.py spawn                 monsters/spawn rows (guards, boxes, player count, classic)
    python3 -I tools/mon_sweep.py special               monsters/special rows (handler table, aura, group walk, ...)
    python3 -I tools/mon_sweep.py stats                 monsters/stats rows (AddStat 0, MulDiv, hpregen, velocity, ...)
    python3 -I tools/mon_sweep.py hire                  hirelings rows (table layout, the hire's entry, empty header)
    python3 -I tools/mon_sweep.py player                player/creation rows (stub, act, 0x0057E3F0)
    python3 -I tools/mon_sweep.py tables                full-table checks (pools, minions, velocity, hireling ranges)

The log set is every kept log of the stock sessions of run:2026-10-12-mon-pool, -mon-pool-p2, run:2026-10-13-mon-spawn,
run:2026-10-14-mon-special, run:2026-10-15-mon-stats, run:2026-10-16-hirelings and run:2026-10-16-player, each hash
checked against its record (a record that gives a shortened hash "abcd1234…ef01" is checked on both ends). The forced
run:2026-10-15-berserk-forced is read only by `stats` for the x87 rows, which no MonUMod cell reaches.

Every model the checks call is an existing checker's (tools/monpool.py, monspawn.py, monspecial.py, monstats.py,
hirelings.py, player.py), run on the same logs first with 0 mismatches required; this file adds counts, the
MonRegionFindAdd append model (pool) and the per-row tests. A counterfactual (`cf`) line is a sensitivity check: it
must FAIL where the rule decides. Each output line starts with `S3A <check>`; the "Plan 0038 batch S3a" sections of
docs/findings/monsters/0001..0004, hirelings/0001 and player/0001 map them to the statements they back.
Stdlib only. Read-only (logs --write writes the manifest file it is given).
"""
import argparse
import collections
import contextlib
import hashlib
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import monpool  # noqa: E402
from rng import INIT_HIGH, MASK, step  # noqa: E402

ROOT = os.path.dirname(HERE)
LOGS = os.path.join(ROOT, "workspace", "logs")
EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
FORCED_EXCEL = os.path.join(ROOT, "workspace", "runtime", "excel-forced-umb")

# (run id, [(log name, record hash: full, or (prefix, suffix) of a shortened one)] or a manifest file)
RUNS = [
    ("run:2026-10-12-mon-pool", [
        ("monpool-1-normal.log", ("d4cf9a8f", "3b3d")), ("monpool-1-d1.log", ("eb514885", "1360")),
        ("monpool-1-d2.log", ("2036a0a6", "5f1d")), ("monpool-2-d0.log", ("fc6b83a0", "2337")),
        ("monpool-2-d2.log", ("e7518763", "8cde")), ("monpool-3-d0-a1.log", ("fc830d30", "1a84")),
        ("monpool-3-d0-a2.log", ("8a52c22f", "4598")), ("monpool-4-d0-a3.log", ("aaed7338", "50fe")),
        ("monpool-4-d0-a4.log", ("8c811ac4", "0fa4")), ("monpool-5-d0-a5.log", ("b28a526c", "d869"))]),
    ("run:2026-10-12-mon-pool-p2", [
        ("monpool-p2-1-hell-merc-town.log", ("a5a6231f", "892f")), ("monpool-p2-2-hell-jail.log", ("6f1986fd", "f071")),
        ("monpool-p2-3-nm-jail.log", ("0c4eeac1", "1cb3")), ("monpool-p2-4-classic-hell-jail.log", ("84d7492a", "6144")),
        ("monpool-p2-5-classic-nm-jail.log", ("434bb32b", "6269")),
        ("monpool-p2-6-hell-jail-golem.log", ("30342d58", "2abb")), ("monpool-p2-7-normal-stony.log", ("f853b6df", "07d8"))]),
    ("run:2026-10-13-mon-spawn", [
        ("monspawn-s1-12345-normal-a1.log", ("4dab869e", "b0193609")),
        ("monspawn-s2-12345-normal-a2-5.log", ("c50778b4", "06bb16b3")),
        ("monspawn-s3-1-hell-a1.log", ("c0556ed2", "6cd152d8"))]),
    ("run:2026-10-14-mon-special", [
        ("monspecial-s1-2101-normal.log", ("efa54deb", "eb88113b")), ("monspecial-s2-2102-hell.log", ("4c9554f7", "38db6d28")),
        ("monspecial-s3-2103-hell.log", ("269442d0", "9ce8567f")), ("monspecial-s4-2104-hell.log", ("6aa3b1d6", "17295a00")),
        ("monspecial-s5-2105-hell.log", ("771ff425", "6a90b577")), ("monspecial-s6-2106-nightmare.log", ("cf9a5915", "7df5e31c")),
        ("monspecial-s7-2107-classic-hell.log", ("b5246760", "04fbfaa4")),
        ("monspecial-s8-2108-classic-nightmare.log", ("758475db", "7daf3b44")),
        ("monspecial-s9-2109-classic-normal.log", ("9859863d", "85df0733")),
        ("monspecial-s10-2110-hell.log", ("2a12b36e", "8aef0ec4")), ("monspecial-s11-2111-hell.log", ("98f5fd1f", "75b28db2")),
        ("monspecial-s12-2112-nightmare.log", ("7c9de83f", "8de7abe1"))]),
    ("run:2026-10-15-mon-stats", [
        ("monstats-s1-2502-normal.log", ("560b87df", "f2f60fdf")), ("monstats-s2-2505-nightmare.log", ("10c52203", "8a567c5c")),
        ("monstats-s3-2508-hell.log", ("93bc469a", "f99c99d6")), ("monstats-s4-2505-nightmare.log", ("c026ade7", "b2d13600")),
        ("monstats-s5-2505-classic-nightmare.log", ("11230b0b", "0ff03c96")),
        ("monstats-s6-2508-classic-hell.log", ("c84e8f4d", "ed85eaf2")),
        ("monstats-s7-2509-classic-normal.log", ("1eb89d58", "571714e3")),
        ("monstats-s8-2510-hell.log", ("f6edfda2", "61ff077b")), ("monstats-s9-2511-nightmare.log", ("943663fd", "7d46e530")),
        ("monstats-s10-2512-hell.log", ("c8f3b38e", "b489f8f3")), ("monstats-s11-2513-hell.log", ("3c252b57", "3ed80e24"))]),
    ("run:2026-10-16-hirelings", "workspace/logs/hire-run-manifest.txt"),
    ("run:2026-10-16-player", "workspace/scratch-h34p2/player-run-manifest.txt"),
]
FORCED = ("run:2026-10-15-berserk-forced", "workspace/logs/berserk-forced-manifest.txt")
MANIFEST_HASH = {"workspace/logs/hire-run-manifest.txt": ("4559f158", None),
                 "workspace/scratch-h34p2/player-run-manifest.txt": ("ee2ce6bf", None),
                 "workspace/logs/berserk-forced-manifest.txt": ("bd0c98f4", "da1bf009")}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def hash_ok(got, want):
    if want is None:
        return True
    if isinstance(want, tuple):
        pre, suf = want
        return got.startswith(pre) and (suf is None or got.endswith(suf))
    return got == want


def manifest_items(rel):
    path = os.path.join(ROOT, rel)
    got = sha256(path)
    if not hash_ok(got, MANIFEST_HASH.get(rel)):
        raise SystemExit("%s: sha256 %s, the record says %s" % (rel, got, MANIFEST_HASH.get(rel)))
    out = []
    for ln in open(path):
        if ln.strip():
            h, name = ln.split()
            out.append((name if "/" in name else os.path.join("workspace", "logs", name), h))
    return out


def run_logs(run, check=True):
    """[(path, sha256)] of one run, each checked against its record."""
    for r, spec in RUNS + [FORCED]:
        if r != run:
            continue
        items = manifest_items(spec) if isinstance(spec, str) else [(os.path.join("workspace", "logs", n), h)
                                                                    for n, h in spec]
        out = []
        for rel, want in items:
            path = os.path.join(ROOT, rel)
            got = sha256(path) if check else None
            if check and not hash_ok(got, want):
                raise SystemExit("%s: sha256 %s, %s's record says %s" % (rel, got, run, want))
            out.append((path, got))
        return out
    raise KeyError(run)


_LOGS = {}


def logs_of(run):
    if run not in _LOGS:
        _LOGS[run] = [p for p, _ in run_logs(run)]
    return _LOGS[run]


def events(path, tags=None):
    """(tag, dict, line number) of every JSON line of a log, in order."""
    out = []
    with open(path, errors="replace") as fh:
        lines = list(fh)
    for ln, line in enumerate(lines, 1):
        tag, _, rest = line.partition(" ")
        if tags is not None and tag not in tags:
            continue
        if not rest.startswith("{"):
            continue
        try:
            out.append((tag, json.loads(rest), ln))
        except ValueError:
            pass
    return out


def log_seed(path):
    """The -seed value of a d2run log header."""
    with open(path, errors="replace") as fh:
        for line in fh:
            if line.startswith("# d2run seed="):
                return int(line.split("seed=")[1].split()[0])
    return None


def seed_t(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def fmt(t):
    return "%08x:%08x" % t


def say(check, msg):
    print("S3A %s %s" % (check, msg))


def quiet(fn, *a, **k):
    """Run a checker with its own output captured; returns (return value, output)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rv = fn(*a, **k)
    return rv, buf.getvalue()


def cmd_logs(ns):
    lines, total = [], 0
    for run, _ in RUNS + [FORCED]:
        lg = run_logs(run)
        total += len(lg)
        say("logs", "%s files=%d%s" % (run, len(lg), " (forced; stats x87 rows only)" if run == FORCED[0] else ""))
        lines += ["%s  %s" % (h, os.path.relpath(p, ROOT)) for p, h in lg]
    say("logs", "total=%d, every sha256 equal to its record" % total)
    if ns.write:
        with open(ns.write, "w") as f:
            f.write("\n".join(lines) + "\n")
        print("manifest written: %s (sha256 %s)" % (ns.write, sha256(ns.write)))
    return 0


# ---------------------------------------------------------------- monsters/pool

FINDADD_NONE = {0xC3, 0xC4, 0x126, 0x128}     # sub_00547BC0_MonRegionFindAdd returns no entry for these classes


def findadd(T, region, cls, useed):
    """sub_00547BC0_MonRegionFindAdd on a modelled region (list of [class, rarity, sets]) and the new unit's seed
    (a monpool.Seed, stepped in place). Returns (kind, entry): kind 'none' (excluded class or region full), 'found',
    'added' (class written, nEntries + 1, MonVariantRoll(unit seed, entry, 3)) or 'stale' (TotalPieces <= 2: the
    slot past the last entry is returned unwritten)."""
    if cls in FINDADD_NONE or not 0 <= cls < len(T.ms):
        return "none", None
    for e in region:
        if e[0] == cls:
            return "found", e
    if len(region) > 12:
        return "none", None
    m2 = T.ms2rec(cls)
    if m2 is None or m2[0xEC] <= 2:
        return "stale", None
    e = [cls, 0, []]
    region.append(e)
    monpool.variant_roll(T, useed, e, 3)
    return "added", e


def walk_creations(T, path, cf_none=False):
    """Every SI0 (MonStatsInit entry) of a mon-stats.gdb log against the FindAdd model: the regions start as
    tools/monpool.py builds them from -seed and the game's difficulty, then take every append in log order; each
    P0 / PM0 region snapshot is compared with the modelled region. The unit seed at FindAdd's entry is
    Init(step(game seed at MU0).low). Yields per-creation records; raises on a mismatch."""
    nseed = log_seed(path)
    regions = None
    mu0 = None
    for tag, d, ln in events(path, {"MU0", "SI0", "P0", "PM0", "MU"}):
        if tag == "MU0":
            mu0 = d
            continue
        if tag == "MU":
            mu0 = None
            continue
        if tag in ("P0", "PM0"):
            r = d.get("reg")
            if r and regions is not None:
                want = [e[0] for e in regions.get(r["lid"], [])]
                got = [e[0] for e in r["ents"]]
                yield {"kind": "snapshot", "ok": want == got, "ln": ln, "lid": r["lid"], "want": want, "got": got}
            continue
        if regions is None:
            low = monpool.first_draw_low(nseed, 1).low
            regions = {lid: [[c, r, [bytes.fromhex(s) for s in v]] for c, r, v in reg["ents"]]
                       for lid, reg, _ in ((a, b, c) for a, b, c in monpool.build_all(T, low, d["g6d"], d["exp"]))}
        reg = regions.setdefault(d["lid"], [])
        rec = {"kind": "creation", "ln": ln, "cls": d["cls"], "lid": d["lid"], "nvar": d["nvar"] if d["ent"] else 0,
               "mu0": mu0 is not None}
        if mu0 is None:
            # created on a path without a MonSpawnTry line: the unit seed is not known here; an append is taken
            # from the log (nvar of a class not in the region), not predicted
            if d["ent"] and d["nvar"] and all(e[0] != d["cls"] for e in reg) and len(reg) <= 12:
                reg.append([d["cls"], 0, [bytes.fromhex(d["vb"])[16 * i:16 * i + 16] for i in range(d["nvar"])]])
                rec["fa"] = "added (log)"
            else:
                rec["fa"] = "no MU0"
            yield rec
            continue
        lo, _hi = step(*seed_t(mu0["gs"]))
        s = monpool.Seed(lo, INIT_HIGH)
        init = str(s)
        if cf_none:
            kind, e = "none", None
        else:
            kind, e = findadd(T, reg, d["cls"], s)
        rec["fa"] = kind
        rec["draws"] = 0
        t = seed_t(init)
        while fmt(t) != str(s):
            t = step(*t)
            rec["draws"] += 1
        rec["ok_seed"] = str(s) == d["us"]
        rec["ok_sets"] = True
        if kind == "added":
            vb = bytes.fromhex(d["vb"]) if d.get("vb") else b""
            rec["ok_sets"] = d["nvar"] == len(e[2]) and all(vb[16 * i:16 * i + 16] == bytes(x) for i, x in
                                                           enumerate(e[2]))
            rec["nsets"] = len(e[2])
        yield rec


def check_findadd(T, paths, cf_none=False):
    c = collections.Counter()
    bad = []
    for p in paths:
        for r in walk_creations(T, p, cf_none):
            if r["kind"] == "snapshot":
                c["region snapshots (P0, PM0) equal to the modelled region"] += r["ok"]
                if not r["ok"]:
                    bad.append((os.path.basename(p), r["ln"], "snapshot level %d" % r["lid"], r["want"], r["got"]))
                continue
            c["creations (SI0)"] += 1
            if not r["mu0"]:
                c["creations without a MonSpawnTry line (unit seed not known): %s" % r["fa"]] += 1
                continue
            c["FindAdd %s" % r["fa"]] += 1
            if r["fa"] == "added":
                c["  appended: draws on the unit seed %d, sets %d" % (r["draws"], r["nsets"])] += 1
            if r["ok_seed"] and r["ok_sets"]:
                c["unit seed at MonStatsInit entry and the new entry's sets reproduced"] += 1
            else:
                bad.append((os.path.basename(p), r["ln"], "class %d level %d %s" % (r["cls"], r["lid"], r["fa"]),
                            r["ok_seed"], r["ok_sets"]))
    return c, bad


MON_LOG_RUNS = ("run:2026-10-12-mon-pool", "run:2026-10-12-mon-pool-p2", "run:2026-10-13-mon-spawn",
                "run:2026-10-14-mon-special", "run:2026-10-15-mon-stats")


def variant_sets_by_cap(T, paths):
    """Every logged region entry (MPR lines) by its MonStats2 +0x25 byte and its number of sets."""
    c = collections.Counter()
    dup2 = 0
    for p in paths:
        for _t, d, _ln in events(p, {"MPR"}):
            for cls, _r, sets in d["ents"]:
                m2 = T.ms2rec(cls)
                b = m2[0x25] if m2 is not None else None
                c[(b, len(sets))] += 1
                if len(sets) == 3 and sets[0] == sets[1]:
                    dup2 += 1
    return c, dup2


def variant_roll_counted(t, seed, ent, n=3, stop_le0=False, cnt=None):
    """monpool.variant_roll with counters (and, with stop_le0, the counterfactual `tries <= 0` stop). Counts, per
    duplicate test, how many existing sets the new one equals, and the tests that leave tries below 0."""
    m2 = t.ms2rec(ent[0])
    if m2 is None:
        return
    comp = list(m2[0x15:0x25])
    have = len(ent[2])
    n = min(n, (1 << (m2[0x25] & 31)) - have)
    if n <= 0:
        return
    if have + n > 3:
        n = 3 - have
    if n <= 0:
        return
    sets = ent[2]
    if have == 0:
        sets.append([0 if c < 2 else seed.range(c) for c in comp])
        n -= 1
    if n == 0:
        return
    cand = [i for i in range(16) if comp[i] > 1]
    k = len(cand)
    if k == 0:
        return
    if k == 1:
        a = b = cand[0]
    else:
        u = seed.range(k)
        a = cand[u]
        cand[u] = cand[k - 1]
        b = cand[seed.range(k - 1)]

    def roll(c):
        return 0 if c == 0 else seed.step() % c

    for _ in range(n):
        tries = 3
        while True:
            new = list(sets[0])
            new[a] = roll(comp[a])
            if a != b:
                new[b] = roll(comp[b])
            hits = sum(1 for s in sets if s == new)
            tries -= hits
            if cnt is not None and hits:
                cnt["duplicate tests meeting %d existing set(s)" % hits] += 1
                if tries < 0:
                    cnt["duplicate tests leaving tries below 0"] += 1
            if not hits or (tries <= 0 if stop_le0 else tries == 0):
                break
        if cnt is not None and tries < 0:
            cnt["sets appended after tries went below 0 (the loop ran on to a non-duplicate)"] += 1
        sets.append(new)


@contextlib.contextmanager
def patched_variant_roll(fn):
    orig = monpool.variant_roll
    monpool.variant_roll = fn
    try:
        yield
    finally:
        monpool.variant_roll = orig


def creation_levels(paths):
    """(SI0, SI2) pairs of the mon-stats.gdb logs, with the level and the handler lines (HST/TST) of each unit."""
    out = []
    for p in paths:
        cur, units = {}, {}
        for tag, d, ln in events(p, {"SI0", "SI2", "SIX", "HST", "TST"}):
            if tag == "SI0":
                cur = {"si0": d, "path": p, "ln": ln, "hst": [], "tst": []}
            elif tag == "SI2" and cur and cur["si0"]["u"] == d["u"]:
                cur["si2"] = d
            elif tag == "SIX" and cur and cur["si0"]["u"] == d["u"]:
                cur["six"] = d
                units[d["u"]] = cur
                out.append(cur)
                cur = {}
            elif tag in ("HST", "TST") and d["u"] in units:
                units[d["u"]][tag.lower()].append(d)
    return out


def stat_of(b, k):
    for s, p, v in b or []:
        if s == k and p == 0:
            return v
    return 0


def cmd_pool(ns):
    T = monpool.Tables(EXCEL)
    stats_logs = logs_of("run:2026-10-15-mon-stats")
    rc = 0
    # pool 22: MonRegionFindAdd
    c, bad = check_findadd(T, stats_logs)
    for k in sorted(c):
        say("pool findadd", "%s: %d" % (k, c[k]))
    say("pool findadd", "failed: %d" % len(bad))
    for b in bad[:10]:
        say("pool findadd", "FAIL %s" % (b,))
    rc |= 1 if bad else 0
    c2, bad2 = check_findadd(T, stats_logs, cf_none=True)
    say("pool findadd cf", "no append (FindAdd never draws): %d of %d creations fail (must be > 0)" % (
        len(bad2), c2["creations (SI0)"]))
    # pool 10, 27: variant caps and a try that meets two equal sets
    pool_logs = logs_of("run:2026-10-12-mon-pool") + logs_of("run:2026-10-12-mon-pool-p2")
    vc, dup2 = variant_sets_by_cap(T, pool_logs)
    by = collections.defaultdict(collections.Counter)
    for (b, n), k in vc.items():
        by["0" if b == 0 else ("1" if b == 1 else ("2..15" if b is not None and b < 16 else ">=16"))][n] += k
    for k in ("0", "1", "2..15", ">=16"):
        say("pool variants", "MonStats2 +0x25 %s: entries by number of sets %s" % (k, dict(sorted(by[k].items()))))
    k0 = sum(1 for cls in range(len(T.ms)) if T.ms2rec(cls) is not None and T.ms2rec(cls)[0x25] == 0
             and any(x > 1 for x in T.ms2rec(cls)[0x15:0x25]))
    say("pool variants", "classes with +0x25 = 0 and a component count > 1 (cap 0 separable from the k = 0 stop): %d" % k0)
    say("pool variants", "logged entries whose first two sets are equal and that hold a third: %d" % dup2)
    cnt = collections.Counter()
    with patched_variant_roll(lambda t, s, e, n=3: variant_roll_counted(t, s, e, n, False, cnt)):
        rv, out = quiet(monpool.check, EXCEL, pool_logs)
    say("pool variants", "tools/monpool.py check with the counted roll (tries = 0 stop): exit %d, %s" % (
        rv, out.strip().splitlines()[-1]))
    for k in sorted(cnt):
        say("pool variants", "  %s: %d" % (k, cnt[k]))
    with patched_variant_roll(lambda t, s, e, n=3: variant_roll_counted(t, s, e, n, True, None)):
        rv2, out2 = quiet(monpool.check, EXCEL, pool_logs)
    say("pool variants cf", "tries <= 0 stop: exit %d, %s (must fail)" % (rv2, out2.strip().splitlines()[-1]))
    rc |= rv
    # pool 8: classic normal reads mon
    cn = [p for p in logs_of("run:2026-10-15-mon-stats") + logs_of("run:2026-10-14-mon-special")
          if "classic-normal" in p]
    for p in cn:
        ok = region_snapshots(T, p)
        cf = region_snapshots(T, p, cf=True)
        lids = sorted(k[2] for k in ok if k[:2] == (0, 0))
        say("pool classic-normal", "%s: levels whose region was snapshotted %d %s, equal to the mon-column model %d; "
            "the nmon-column model (cf) equal on %d" % (os.path.basename(p), len(lids), lids,
                                                      sum(ok[(0, 0, l)] for l in lids), sum(cf[(0, 0, l)] for l in lids)))
        rc |= 0 if all(ok[(0, 0, l)] for l in lids) else 1
    # pool 11, 13, 16, 17, 28: the monster level
    cl = creation_levels(stats_logs)
    lv = collections.Counter()
    maxlvl = 0
    for u in cl:
        a, b = u["si0"], u.get("si2")
        if b is None:
            continue
        maxlvl = max(maxlvl, b["lvl"])
        cls, lid, g6d, exp = a["cls"], a["lid"], a["g6d"], 1 if a["exp"] else 0
        d = min(g6d, 2)
        if cls in monpool.HIRELINGS:
            continue
        ms_lvl = struct.unpack_from("<h", T.ms[cls], 0xAA + 2 * d)[0]
        want, _ = monpool.monster_level(T, cls, lid, g6d, exp)
        game = ("classic" if not exp else "expansion") + " " + ("normal", "nightmare", "hell")[d]
        lv["%s creations, SI2 level = the rule" % game] += (b["lvl"] == want)
        lv["%s creations, SI2 level != the rule" % game] += (b["lvl"] != want)
        if not exp:
            cm = T.monlvl(lid, d, 0)
            ce = T.monlvl(lid, d, 1)
            if cm != b["lvl"]:
                lv["%s: level = MonStats Level*, classic Levels MonLvl%d differs" % (game, d + 1)] += 1
            if d == 0 and ce != b["lvl"]:
                lv["%s: level = MonStats Level, Levels MonLvl1Ex (the expansion rule) differs" % game] += 1
            lv["%s: level = MonStats Level*" % game] += (b["lvl"] == ms_lvl)
        base = stat_of(u["six"]["b"], 12)          # the level stat MonStatsInit leaves (classic: Level + 25 d)
        if not exp and d:
            lv["%s: stat 12 at MonStatsInit exit = MonStats Level + 25 d" % game] += (
                base == struct.unpack_from("<h", T.ms[cls], 0xAA)[0] + 25 * g6d)
        else:
            lv["%s: stat 12 at MonStatsInit exit = SI2 level" % game] += (base == b["lvl"])
        if u["hst"]:
            mods = u["hst"][-1].get("mods")
            kind = "champion" if any(h.get("mf", 0) & 4 for h in u["hst"]) else "unique or superunique"
            lv["%s (flag-1 handlers): stat 12 after the handlers - stat 12 at MonStatsInit exit %+d" % (
                kind, stat_of(u["hst"][-1]["b"], 12) - base)] += 1
            if mods:
                pass
        elif u["tst"]:
            lv["group member (flag-0 handlers): stat 12 after the handlers - stat 12 at MonStatsInit exit %+d" % (
                stat_of(u["tst"][-1]["b"], 12) - base)] += 1
    for k in sorted(lv):
        say("pool level", "%s: %d" % (k, lv[k]))
    say("pool level", "highest SI2 level %d; MonLvl rows %d (row min(level, n - 1) clamps only above %d)" % (
        maxlvl, MONLVL_ROWS(), MONLVL_ROWS() - 1))
    hi_ms = max(struct.unpack_from("<h", r, 0xAA + 2 * k)[0] for r in T.ms for k in range(3))
    hi_lv = max(T.monlvl(l, d, e) for l in range(1, len(T.lv)) for d in range(3) for e in (0, 1))
    say("pool level", "highest stock MonStats Level* %d, highest Levels MonLvl*/MonLvl*Ex %d" % (hi_ms, hi_lv))
    # monsters/README 1: one game-seed draw per server monster
    mu = collections.Counter()
    for run in MON_LOG_RUNS:
        for p in logs_of(run):
            m0 = None
            for tag, d, _ln in events(p, {"MU0", "MU"}):
                if tag == "MU0":
                    m0 = d
                elif m0 is not None:
                    one = fmt(step(*seed_t(m0["gs"]))) == d["gs"]
                    mu["%s: SUnitCreate (MU0 -> MU) %s" % (run, "one game-seed step" if one else "OTHER")] += 1
                    m0 = None
    for k in sorted(mu):
        say("readme seed", "%s: %d" % (k, mu[k]))
    return rc


class ColumnSwap:
    """monpool.Tables with the pool column of normal difficulty (mon, +0x36) read from nmon (+0x68): the
    counterfactual 'classic normal reads nmon'."""
    def __init__(self, t):
        self._t = t

    def __getattr__(self, k):
        return getattr(self._t, k)

    def slots(self, lid, off):
        return self._t.slots(lid, 0x68 if off == 0x36 else off)


def region_snapshots(T, path, cf=False):
    """Every P0 / PM0 region snapshot of a log against tools/monpool.py's regions for the log's -seed, difficulty and
    game type (pool classes up to nPool, as tools/monspawn.py's region check). Returns {(diff, exp, lid): ok}."""
    nseed = log_seed(path)
    model, out = {}, {}
    for tag, d, _ln in events(path, {"P0", "PM0"}):
        r = d.get("reg")
        if not r:
            continue
        key = (d["diff"], d["exp"])
        if key not in model:
            low = monpool.first_draw_low(nseed, 1).low
            model[key] = {lid: reg for lid, reg, _ in monpool.build_all(ColumnSwap(T) if cf else T, low, *key)}
        w = model[key].get(r["lid"])
        got = [e[0] for e in r["ents"]][:r["npool"]]
        out.setdefault(key + (r["lid"],), w is not None and got == [e[0] for e in w["ents"]] and r["npool"] == w["n"])
    return out


# ---------------------------------------------------------------- monsters/spawn

SPAWN_RUNS = ("run:2026-10-13-mon-spawn", "run:2026-10-14-mon-special", "run:2026-10-15-mon-stats")


def run_monspawn(paths):
    """tools/monspawn.py's checker over the logs (its output captured). Returns the checker."""
    import drlg
    import monspawn
    c = monspawn.Checker(EXCEL, drlg.DEFAULT_DATA, False)
    for p in paths:
        quiet(c.run, p)
    return c


def div3(v):
    q = abs(v) // 3
    return q if v >= 0 else -q


def scan_spawn(path):
    """Counts from the raw lines of one population log (no model): region snapshots with nRooms 0, MonSpawnTry
    requests with a null room or radius 0, flag-0x80 requests whose CollisionTest refused a cell that was then used,
    boxes whose first rectangle (+0x00, from the LG1 box list) gives another attempt count than +0x10, SCI/SCD
    lines against the live count in every region snapshot, and passes per /players value and game type."""
    import collision
    c = collections.Counter()
    lg_boxes = {}               # box pointer -> r0 (latest LG1)
    stack = []                  # open MonSpawnTry requests
    nspec = {}                  # region pointer -> modelled live count (+0x2C8)
    special_units = set()       # units logged with monster flag 0x01
    players = 0
    in_pass = False
    window = None
    exp = diff = None
    for tag, d, ln in events(path):
        if tag in ("P0", "PM0", "SU0", "PR", "PX"):
            r = d.get("reg")
            if r:
                if r["nrooms"] == 0:
                    c["region snapshots with nRooms = 0"] += 1
                rp = r["r"]
                if rp in nspec:
                    c["region snapshots: live special count = SCI/SCD model" if nspec[rp] == r["nspec"] else
                      "region snapshots: live special count DIFFERS from the SCI/SCD model"] += 1
                nspec[rp] = r["nspec"]
        if tag in ("SU0", "PM0"):
            window = "superunique" if tag == "SU0" else "MonPlace %d" % d["case"]
        elif tag in ("SUX", "PMX"):
            window = None
        if tag == "P0":
            in_pass = True
            exp, diff = d["exp"], d["diff"]
            c["passes at /players %d (%s %s)" % (max(players, 1), "expansion" if exp else "classic",
                                                 ("normal", "nightmare", "hell")[min(diff, 2)])] += 1
        elif tag == "PC":
            c["first class picks (PC) %s" % ("with a record" if d["rec"] else "without a record")] += 1
        elif tag == "PS2":
            c["special class picks (PS2) in %s" % ("normal (umon)" if diff == 0 else "nightmare or hell (pool)")] += 1
        elif tag == "PX":
            in_pass = False
        elif tag == "PCHG":
            players = d["new"]
        elif tag == "LG1":
            for b in collision.unz(d["z"])["boxes"]:
                lg_boxes[b["b"]] = (tuple(b["r0"]), tuple(b["r"]))
        elif tag == "PB":
            got = lg_boxes.get(d["box"])
            if got and got[1] == tuple(d["rect"]) and d["rid"] != 0 and d["kind"] == 0:
                (l0, t0, r0, b0), (l, t, r, b) = got
                if (l, r) != (0, 0):
                    n = div3(5 * b - 5 * t) * div3(5 * r - 5 * l)
                    n0 = div3(5 * b0 - 5 * t0) * div3(5 * r0 - 5 * l0)
                    c["boxes used by a pass with an LG1 record: +0x00 = +0x10" if got[0] == got[1] else
                      ("boxes used by a pass, +0x00 != +0x10, attempts from +0x00 differ" if n != n0 else
                       "boxes used by a pass, +0x00 != +0x10, same attempt count")] += 1
        elif tag == "MT0":
            stack.append({"fl": d["fl"], "refused": set()})
            if d["room"] == 0:
                c["MonSpawnTry requests with a null room"] += 1
            if d["rad"] == 0:
                c["MonSpawnTry requests with radius 0"] += 1
            if d["fl"] & 0x80:
                c["MonSpawnTry requests with flag 0x80 (%s)" % ("in a pass" if in_pass else "outside a pass")] += 1
        elif tag == "MK0" and stack:
            stack[-1]["mk"] = (d["x"], d["y"])
        elif tag == "MK" and stack:
            if d["r"] != 0 and "mk" in stack[-1]:
                stack[-1]["refused"].add(stack[-1]["mk"])
        elif tag == "MU0" and stack:
            if (d["x"], d["y"]) in stack[-1]["refused"]:
                c["requests %s created on a cell CollisionTest refused" % (
                    "with flag 0x80" if stack[-1]["fl"] & 0x80 else "WITHOUT flag 0x80")] += 1
        elif tag == "MTX" and stack:
            stack.pop()
        elif tag == "SCI":
            rp = d["reg"]
            if rp in nspec:
                c["SCI: before = the live count" if nspec[rp] == d["before"] else "SCI: before DIFFERS"] += 1
            nspec[rp] = d["before"] + 1
            c["SCI (increments) %s" % ("in a pass" if in_pass else ("in a %s window" % window if window else
                                                                     "outside a pass and a preset window"))] += 1
        elif tag == "SCD":
            rp = d["reg"]
            if rp in nspec:
                c["SCD: before = the live count" if nspec[rp] == d["before"] else "SCD: before DIFFERS"] += 1
            nspec[rp] = d["before"] - 1
            c["SCD (decrements) %s" % ("in a pass" if in_pass else "outside a pass")] += 1
            c["SCD unit logged before with monster flag 0x01" if d["unit"] in special_units else
              "SCD unit not logged with flag 0x01 (no special line for it)"] += 1
        if tag in ("SMPX", "SUX", "SMAX"):
            u = d.get("bu") or d.get("u")
            if isinstance(u, dict) and u.get("mf", 0) & 1:
                special_units.add(u["u"])
        if tag == "MU" and d["unit"].get("mf", 0) & 1:
            special_units.add(d["unit"]["u"])
        if tag == "TH0" or tag == "HD0":
            pass
    return c


def cmd_spawn(ns):
    rc = 0
    tot = collections.Counter()
    for run in SPAWN_RUNS:
        paths = logs_of(run)
        ck = run_monspawn(paths)
        say("spawn monspawn", "%s: %d logs, %d checks, %d mismatches; collision %d checks, %d mismatches; passes %s" % (
            run, len(paths), ck.checks, ck.fail, ck.world.checks, ck.world.fail, dict(sorted(ck.results.items()))))
        rc |= 1 if (ck.fail or ck.world.fail) else 0
        for k, v in ck.stats.items():
            if k.startswith(("guard ", "CollisionTest bypassed", "MonSpawnTry exit", "special class from umon",
                             "spawn substitution", "closed gate")):
                tot[k] += v
        say("spawn monspawn", "%s: closed MonDen gates on levels %s" % (run, sorted(ck.closed_levels)))
        tot["type rolls reproduced"] += len(ck.type_rolls)
        tot["special type rolls (second class pick: umon in normal, the pool otherwise)"] += sum(
            1 for r in ck.type_rolls if r["res"] == 0)
        tot["creations"] += len(ck.creations)
        for k, v in ck.unit_steps.items():
            tot["unit-seed steps after Init(step(game).low) at MU: %s" % k] += v
        for p in paths:
            for k, v in scan_spawn(p).items():
                tot[k] += v
    for k in sorted(tot):
        say("spawn", "%s: %d" % (k, tot[k]))
    return rc


# ---------------------------------------------------------------- monsters/special

SPECIAL_RUNS = ("run:2026-10-14-mon-special", "run:2026-10-15-mon-stats")   # the logs with the plan 0018 tags


def scan_special(path, sp, c):
    """Raw-line counts of one plan 0018 / 0025 log (the model's own checks run first in cmd_special)."""
    import monspecial
    unit_cls = {}
    win = None                  # the open SpecialModsApply window
    wins = []
    su = None
    th_open = None
    mm = []                     # open MinionsSpawn calls: [unit, minions created]
    seen_pc = set()
    linked = collections.defaultdict(set)     # unit -> its MonStats minions (SetBoss classes link them)
    for tag, d, _ln in events(path):
        if tag == "MU":
            unit_cls[d["unit"]["u"]] = d["unit"]["cls"]
            linked.pop(d["unit"]["u"], None)        # unit addresses are reused within a game
            if win is not None and not win["closed_minions"]:
                win["minions"].add(d["unit"]["u"])
            if mm:
                mm[-1][1].add(d["unit"]["u"])
        elif tag == "MM0":
            mm.append([d["unit"], set()])
        elif tag == "MMX" and mm:
            u, ms = mm.pop()
            if u in unit_cls and sp.valid(unit_cls[u]) and sp.ms[unit_cls[u]][0x0C] & 0x10:
                linked[u] |= ms
        elif tag == "SMA0":
            win = {"boss": d["boss"], "minions": set(), "hd": [], "th": collections.defaultdict(list),
                   "closed_minions": False, "aur_in_th": 0}
        elif tag == "SMA1" and win is not None:
            win["closed_minions"] = True
        elif tag == "HD0" and win is not None and d["u"] == win["boss"]:
            win["hd"].append(d["m"])
            th_open = None
        elif tag == "TH0" and win is not None:
            win["th"][d["m"]].append(d["u"])
            th_open = d["m"]
        elif tag == "TH1":
            th_open = None
        elif tag == "AUR" and win is not None and th_open is not None:
            win["aur_in_th"] += 1
        elif tag == "SMAX" and win is not None:
            win["mods"] = d["u"]["mods"]
            win["mf"] = d["u"]["mf"]
            win["linked"] = set(linked.get(win["boss"], set()))
            wins.append(win)
            win = None
        elif tag == "SU0":
            su = d
        elif tag == "SU1" and su is not None:
            rec = sp.su_rec(su["id"])
            cls = unit_cls.get(d["u"])
            for m in [m for m in rec["mods"] if m]:
                if m == 24:
                    c["superunique fixed mods: thief (24), dropped"] += 1
                    continue
                ok = sp.eligible(m, su["exp"], cls, [])
                c["superunique fixed mods written that ModEligible %s" % ("accepts" if ok else "rejects")] += 1
                if not ok:
                    c["  written although ModEligible rejects it: superunique %d class %d mod %d (in SU1 %s)" % (
                        su["id"], cls, m, m in d["mods"])] += 1
            c["superuniques (SU0): placed bit at entry %d" % su["placed"]] += 1
            c["superuniques (SU0): Stacks %d" % rec["stacks"]] += 1
        elif tag == "SUX":
            su = None
        elif tag == "MPK":
            if d["k"] == "u" and d["total"] > 0:
                t = d["total"]
                c["unique picks with a draw, total a power of two" if t & (t - 1) == 0 else
                  "unique picks with a draw, total not a power of two"] += 1
        elif tag == "AUR":
            c["aura draws: n %d at level %s" % (d["n"], "< 20" if d["lvl"] < 20 else ">= 20")] += 1
        if tag in ("SMR0", "LIVE", "HST", "TST", "SU1"):
            # every unit line that shows a mod list after MonSpawnTry's post-create step: its list starts with the
            # BaseId's post-create mods (sub_005B21B0_MonPostCreateMods), or holds none for a class without them
            u = d["unit"] if tag == "SMR0" else d
            cls = u.get("cls", unit_cls.get(u["u"]))
            if cls is not None and u["u"] not in seen_pc:
                seen_pc.add(u["u"])
                want = monspecial.post_create_mods(sp, cls)
                base = sp.ms_s16(cls, 0x02)
                if want:
                    c["units whose BaseId has post-create mods %s (BaseId %d): list starts with them %s" % (
                        want, base, u["mods"][:len(want)] == want)] += 1
                else:
                    pc_all = {10, 11, 13, 14, 15, 20, 22, 33, 34, 35}
                    c["units of a BaseId with no post-create mod: none of 10, 11, 13-15, 20, 33-35 in the list %s" % (
                        not (pc_all - {22}) & set(u["mods"]))] += 1
    for w in wins:
        seq = sp.handler_seq(w["mods"])
        c["SpecialModsApply windows: handler calls = always-run mods with a handler, then the list's: %s" % (
            w["hd"] == seq)] += 1
        c["SpecialModsApply windows whose calls start rndname, hpmultiply, leveladd (1, 2, 4): %s" % (
            w["hd"][:3] == [1, 2, 4])] += 1
        for m in sp.handler_seq(w["mods"], every=True):
            has = 0 <= m < len(sp.handler) and sp.handler[m]
            c["mod rows in an applied list (%s): row %02d" % ("handler" if has else "null handler", m)] += 1
            if not has and m in w["hd"]:
                c["NULL-handler row with a handler call: %d" % m] += 1
        kind = "champion" if w["mf"] & 4 else "unique or superunique"
        want_any = w["linked"] if kind == "champion" else (w["minions"] | w["linked"])
        for m in w["hd"]:
            if want_any and m not in w["th"]:
                c["handler calls of a boss with linked units but no group walk (TH0)"] += 1
        for m, units in w["th"].items():
            if kind == "champion":
                ok = set(units) == w["linked"] and len(units) == len(w["linked"])
                c["group walks of a champion (TH0 per mod) whose units are exactly its SetBoss MonStats minions: %s"
                  % ok] += 1
            else:
                want = w["minions"] | w["linked"]
                ok = set(units) == want and len(units) == len(want)
                c["group walks of a unique or superunique (TH0 per mod) whose units are exactly its UniqueMinions "
                  "creations (and any SetBoss MonStats minions): %s" % ok] += 1
            if m == 30:
                c["aura group-member calls (flag 0)"] += len(units)
        c["AUR lines inside a group-member (flag 0) call"] += w["aur_in_th"]
    return c


def cmd_special(ns):
    import monspecial
    rc = 0
    sp = monspecial.Data(EXCEL)
    st = collections.Counter()
    for run in SPECIAL_RUNS:
        paths = logs_of(run)
        ck = run_monspawn(paths)
        say("special monspawn", "%s: %d logs, %d checks, %d mismatches" % (run, len(paths), ck.checks, ck.fail))
        rc |= 1 if ck.fail else 0
        for p in paths:
            scan_special(p, sp, st)
    for k in sorted(st):
        say("special", "%s: %d" % (k, st[k]))
    say("special", "g_UModHandlers rows with a handler: %s" % [i for i, h in enumerate(sp.handler) if h])
    say("special", "g_UModHandlers null rows: %s" % [i for i, h in enumerate(sp.handler) if not h])
    say("special", "g_UModAlwaysMods: %s" % sp.always)
    return rc


# ---------------------------------------------------------------- monsters/stats

def run_monstats(paths, excel=EXCEL, hooks=None):
    """tools/monstats.py's checker (no chain) with optional Model method wrappers {name: wrapper(orig)}; returns the
    checker. The wrappers only count: each calls the original and returns its result."""
    import monstats
    orig = {}
    for name, wrap in (hooks or {}).items():
        orig[name] = getattr(monstats.Model, name)
        setattr(monstats.Model, name, wrap(orig[name]))
    try:
        c = monstats.Checker(excel, False)
        for p in paths:
            quiet(c.run, p)
    finally:
        for name, f in orig.items():
            setattr(monstats.Model, name, f)
    return c


def cmd_stats(ns):
    import monstats
    rc = 0
    paths = logs_of("run:2026-10-15-mon-stats")
    cnt = collections.Counter()
    T = monstats.Tables(EXCEL)

    def w_add(orig):
        def f(self, st, k, v):
            if v == 0:
                cnt["AddStat(k, 0) calls in the handlers (stat absent before: %s)" % (k not in st or st[k] == 0)] += 1
            else:
                cnt["AddStat(k, v != 0) calls in the handlers"] += 1
            return orig(self, st, k, v)
        return f

    def w_handler(orig):
        def f(self, st, cls, mod, flag, mf, g6d, L):
            name = self.T.handler[mod] if 0 <= mod < len(self.T.handler) else None
            before = dict(st)
            r = orig(self, st, cls, mod, flag, mf, g6d, L)
            if name == "leveladd":
                cnt["leveladd SetStat(12) / SetStat(13) over a non-zero value"] += 1 if before.get(12) else 0
            if name in ("fast", "fanatic") and (name == "fast" or flag):
                v = self.T.m16(cls, 0x32)
                if v > 0:
                    cnt["%s calls on a class with Velocity %d (bonus %d)" % (name, v, self.velocity_bonus(cls))] += 1
            if name == "hpmultiply":
                cnt["hpmultiply flag %d %s" % (flag, ("champion flag set: c[4+d]" if mf & 4 else "c[7+d]") if flag
                                               else "c[1+d]")] += 1
                cnt["hpmultiply calls at difficulty %d" % g6d] += 1
            if name == "champion" and flag:
                cnt["champion flag-1 calls at difficulty %d (CDB %d)" % (g6d, self.T.dl32(g6d, 0x34))] += 1
            if name in ("ghostly", "fanatic", "possessed") and flag:
                cnt["%s flag-1 calls (champion part)" % name] += 1
            return r
        return f

    def w_base(orig):
        def f(self, cls, lvl, d, pb, o, draw, exp, g6d):
            st = orig(self, cls, lvl, d, pb, o, draw, exp, g6d)
            r = struct.unpack_from("<I", self.T.ms[cls], 0x1A0)[0]
            base = o[0] + draw
            hp = min(base + monstats.muldiv(base, pb[0], 100), 0x7FFFFF)
            hp8 = monstats.s32(hp << 8)
            if r:
                cnt["creations with DamageRegen != 0: overflow branch ((hp << 8) > 0x7FFFFFFF / r) %s" % (
                    hp8 > monstats.tdiv(0x7FFFFFFF, r))] += 1
            if exp == 0 and g6d != 0:
                cnt["classic nightmare/hell creations, Align %d: classic adjustment %s" % (
                    self.T.ms[cls][0x4C], "applied" if self.T.ms[cls][0x4C] != 1 else "skipped")] += 1
            return st
        return f

    md = collections.Counter()
    om = monstats.muldiv

    def counted_muldiv(a, b, c):
        a2, b2 = monstats.s32(a), monstats.s32(b)
        md["MulDiv calls: %s" % ("a > 0x100000" if a2 > 0x100000 else ("b > 0x10000" if b2 > 0x10000 else
                                                                        "the 32-bit branch"))] += 1
        return om(a, b, c)
    monstats.muldiv = counted_muldiv
    try:
        ck = run_monstats(paths, hooks={"add": w_add, "handler": w_handler, "base_stats": w_base})
    finally:
        monstats.muldiv = om
    say("stats monstats", "run:2026-10-15-mon-stats: %d logs, %d checks, %d mismatches" % (len(paths), ck.checks, ck.fail))
    rc |= 1 if ck.fail else 0
    for k in sorted(cnt):
        say("stats", "%s: %d" % (k, cnt[k]))
    for k in sorted(md):
        say("stats muldiv", "monstats model, %s: %d" % (k, md[k]))
    # zero-valued entries in the logged base lists
    z = collections.Counter()
    for p in paths:
        for tag, d, _ln in events(p, {"SI4", "SI5", "SIX", "HST", "TST"}):
            for s, _p, v in d.get("b") or []:
                z["logged base entries (%s)" % tag] += 1
                if v == 0:
                    z["logged base entries with value 0 (%s)" % tag] += 1
    for k in sorted(z):
        say("stats lists", "%s: %d" % (k, z[k]))
    # the x87 rows: fpsens on the stock logs and the forced berserk logs; the final conversion
    for run, excel in (("run:2026-10-15-mon-stats", EXCEL), (FORCED[0], FORCED_EXCEL)):
        calls = []
        orig = monstats.Model.set_maxhp

        def rec(self, st, cls, new, _o=orig):
            old, cur = st.get(7, 0), st.get(6, 0)
            if new != old and old > 0 and cur > 0:
                calls.append((new, 0x100 if old <= 0x100 else old, cur))
            return _o(self, st, cls, new)
        monstats.Model.set_maxhp = rec
        try:
            ck2 = run_monstats(logs_of(run), excel)
        finally:
            monstats.Model.set_maxhp = orig
        rc |= 1 if ck2.fail else 0

        def model(new, o, cur, conv):
            x = struct.unpack("<f", struct.pack("<f", (float(new) / float(o)) * float(cur)))[0]
            t = conv(x)
            return new if max(t, 1) >= new else max(t, 1)
        diff = {(p, ch): sum(1 for c in calls if monstats._fp_callback(*c, p, ch) != model(*c, int))
                for p in (24, 53, 64) for ch in (False, True)}
        say("stats x87", "%s: %d mismatches; stat-7 callback calls writing stat 6 %d (distinct %d); calls that differ "
            "from the model: %s" % (run, ck2.fail, len(calls), len(set(calls)),
                                    ", ".join("PC %d %s %d" % (p, "chop" if ch else "nearest", n)
                                              for (p, ch), n in sorted(diff.items()))))
        rnd = sum(1 for c in calls if model(*c, lambda x: int(x + 0.5) if x >= 0 else -int(-x + 0.5)) != model(*c, int))
        say("stats x87", "%s: final conversion rounded to nearest instead of truncated: %d calls differ" % (run, rnd))
    return rc


# ---------------------------------------------------------------- hirelings, player/creation

def parse_hire_table(hx):
    b = bytes.fromhex(hx)
    return [struct.unpack_from("<HHIII", b, 16 * i) for i in range(len(b) // 16)]   # name, pad, seed, hired, listed


def cmd_hire(ns):
    import hirelings
    t = hirelings.Tables(EXCEL)
    first = {}
    for r in t.rows:
        if r["Difficulty"] == 1:
            first.setdefault((r["Version"], r["Seller"]), (r["first"], r["last"]))
    c = collections.Counter()
    paths = logs_of("run:2026-10-16-hirelings")
    rv, out = quiet(hirelings.main, ["check", EXCEL] + paths) if hasattr(hirelings, "main") else (None, "")
    if rv is not None:
        say("hire hirelings", "tools/hirelings.py check: exit %s, %s" % (rv, out.strip().splitlines()[-1]))
    for p in paths:
        tabs, hire, vf = {}, None, None
        ev = events(p, {"HBT", "HHI", "HHX", "MIN", "MRH", "MCA", "MCX", "MLV", "MSL"})
        for i, (tag, d, _ln) in enumerate(ev):
            if tag == "MLV" and vf is None:
                vf = d["exp"]
            if tag == "HBT":
                tab = parse_hire_table(d["tab"])
                fr = next((v for (ver, s), v in first.items() if s == d["cls"]), None)
                n = sum(1 for e in tab if e[0])
                c["hire tables logged (0x450 bytes, 69 slots of 16)"] += 1
                c["hire tables whose slots past the seller's range are zero: %s" % all(
                    e == (0, 0, 0, 0, 0) for e in tab[n:])] += 1
                c["hire tables whose slot i holds name first + i: %s" % all(
                    tab[k][0] == fr[0] + k for k in range(n))] += 1
                c["hire table range %d (seller %d)" % (n, d["cls"])] += 1
                tabs[d["cls"]] = tab
            elif tag == "HHI":
                hire = d
            elif tag == "MIN" and hire is not None:
                tab = tabs.get(hire["cls"])
                fr = next((v for (ver, s), v in first.items() if s == hire["cls"]), None)
                if tab and fr:
                    k = hire["name"] - fr[0]
                    e = tab[k] if 0 <= k < len(tab) else None
                    ok = e is not None and e[0] == hire["name"] and e[2] == d["seed"] and e[3] == 0
                    c["hires: entry t[name - first] holds the name, is not hired, and its seed is MERC_Init's: %s" % ok] += 1
                    # the counterfactual: the k-th listed entry instead of the index
                    listed = [x for x in tab if x[4] and not x[3]]
                    c["cf hires: MERC_Init's seed equals another listed entry's seed (must be False): %s" % any(
                        x[2] == d["seed"] and x[0] != hire["name"] for x in listed)] += 1
                hire = None
            elif tag == "MRH":
                h = bytes.fromhex(d["hdr"])
                flags, seed, name, hid, exp = struct.unpack_from("<IIHHI", h, 0)
                nxt = None
                for t2, _d2, _l2 in ev[i + 1:]:
                    if t2 in ("MRH",):
                        break
                    if t2 == "MCA":
                        nxt = True
                        break
                kind = ("all zero" if seed == 0 and name == 0 and exp == 0 else
                        ("name 0, seed and experience set" if name == 0 else "name, seed and experience set"))
                c["merc headers (%s): MERC_Create entered %s" % (kind, bool(nxt))] += 1
                if flags & 0x10000:
                    c["merc headers with the dead bit"] += 1
    for k in sorted(c):
        say("hire", "%s: %d" % (k, c[k]))
    rng = sorted({(s, v[1] - v[0] + 1) for (ver, s), v in first.items()})
    say("hire", "stock seller ranges (seller, n): %s; largest %d of 69 slots" % (rng, max(n for _, n in rng)))
    return 0


def cmd_player(ns):
    import d2s
    c = collections.Counter()
    for p in logs_of("run:2026-10-16-player"):
        if "/logs/load-" in p:
            continue
        rh = None
        xc = {}
        for tag, d, _ln in events(p, {"RHDR", "NC0", "XC0", "XCR", "XC85", "XCX"}):
            if tag == "NC0" and "34109" not in p and rh is not None and bytes.fromhex(rh["hex"])[0x24] & 4:
                c["HARDCORE stub outside session 34109"] += 1
            if tag == "RHDR":
                rh = d
            elif tag == "NC0" and rh is not None:
                b = bytes.fromhex(rh["hex"])
                ok = d2s.checksum(b) == struct.unpack_from("<I", b, 0x0C)[0]
                c["stubs read by D2S_ReadHeader with the d2s checksum at 0x0C: %s" % ok] += 1
                st = b[0x24]
                hc = bool(st & 4)
                c["stubs with status bit 0x04 (hardcore) %s: %s" % (hc, os.path.basename(p) if hc else
                                                                      "the other sessions")] += 1
                c["stubs of class %s: status bit 0x20 %s, expansion game %s" % (
                    "5/6" if d["cls"] in (5, 6) else "0-4", bool(st & 0x20), bool(d["exp"]))] += 1
                c["stubs: act bytes 0xA8..0xAA zero %s; client act at NC0 %d" % (
                    b[0xA8:0xAB] == b"\0\0\0", d["act"])] += 1
                rh = None
            elif tag == "XC0":
                xc[d.get("th")] = {}
            elif tag in ("XCR", "XC85"):
                xc.setdefault(d.get("th"), {})[tag] = d["v"]
            elif tag == "XCX":
                x = xc.pop(d.get("th"), {})
                if "XCR" in x:
                    c["kills: stat 85 %s, value at 0x0057E3F0's return = after XP_ApplyExpRatio %s" % (
                        x.get("XC85"), d["v"] == x["XCR"])] += 1
    for k in sorted(c):
        say("player", "%s: %d" % (k, c[k]))
    return 0


# ---------------------------------------------------------------- full-table checks

def cmd_tables(ns):
    import monspecial
    import monstats
    T = monpool.Tables(EXCEL)
    ms = T.ms
    cells = set()
    for lid in range(1, len(T.lv)):
        for off in (0x36, 0x68, 0x9A):
            cells |= {(c, off) for c in T.slots(lid, off)}
    say("tables", "Levels mon/nmon/umon cells %d; naming a MonStats record with enabled 0 (+0x00F bit 1): %d" % (
        len(cells), sum(1 for c, _ in cells if not ms[c][0x0F] & 0x02)))
    same = sum(1 for lid in range(1, len(T.lv)) if T.slots(lid, 0x36) == T.slots(lid, 0x68))
    first = next(lid for lid in range(1, len(T.lv)) if T.slots(lid, 0x36) != T.slots(lid, 0x68))
    say("tables", "levels whose mon and nmon lists are equal: %d of %d; the first that differs: %d" % (
        same, len(T.lv) - 1, first))
    pool = {c for c, off in cells if off != 0x9A}
    lohi = sorted(c for c in pool if 0 <= struct.unpack_from("<h", ms[c], 0x26)[0] < len(ms)
                  and ms[c][0x2C] >= ms[c][0x2D])
    say("tables", "pool classes with a valid minion1 and PartyMin >= PartyMax (MinionsSpawn's no-draw count): %s" % lohi)
    for c in lohi:
        lids = sorted({lid for lid in range(1, len(T.lv)) for off in (0x36, 0x68) if c in T.slots(lid, off)})
        say("tables", "  class %d (PartyMin = PartyMax = %d) in the pools of levels %s" % (c, ms[c][0x2C], lids))
    vel = collections.Counter(struct.unpack_from("<h", ms[c], 0x32)[0] for c in pool)
    say("tables", "pool classes by Velocity: %s; bonus clamp(2048 / V - 128, 10, 100) per V: %s" % (
        dict(sorted(vel.items())), {v: max(10, min(100, 2048 // v - 128)) for v in range(1, 16)}))
    sp = monspecial.Data(EXCEL)
    rej = []
    for i in range(len(sp.su)):
        r = sp.su_rec(i)
        if r is None or r["cls"] < 0:
            continue
        for m in [m for m in r["mods"] if m]:
            for exp in (0, 1):
                if not sp.eligible(m, exp, r["cls"], []):
                    rej.append((i, r["cls"], m, exp))
    say("tables", "superunique fixed mods that ModEligible would refuse for the record's class (id, class, mod, exp): %s"
        % rej)
    up = collections.Counter(sp.mu_s16(r, 0x14 + 2 * d) for r in range(len(sp.mu)) for d in range(3)
                             if sp.mu_s16(r, 0x14 + 2 * d) > 0)
    say("tables", "MonUMod upick weights > 0 (all rows, three difficulties): %s" % dict(up))
    MT = monstats.Tables(EXCEL)
    M = monstats.Model(MT)
    reach = set()
    for c in range(len(MT.ms)):
        r = struct.unpack_from("<I", MT.ms[c], 0x1A0)[0]
        if not r:
            continue
        thr = monstats.tdiv(0x7FFFFFFF, r)
        for d in range(3):
            lvl = MT.m16(c, 0xAA + 2 * d)
            for L in range(max(lvl, 0), 111):       # the class's own level, or any area level above it
                o = M.monlvl_stats(c, 1, d, L)
                hp = min(o[1] + monstats.muldiv(o[1], MT.hp_pct[8], 100), 0x7FFFFF)
                if monstats.s32(hp << 8) > thr:
                    reach.add(c)
                    break
    say("tables", "classes whose largest HP (MonLvl row up to 110, 8 players) passes 0x7FFFFFFF / DamageRegen: %s; "
        "DamageRegen values %s" % (sorted(reach), sorted({struct.unpack_from("<I", r, 0x1A0)[0] for r in MT.ms})))
    return 0


def MONLVL_ROWS():
    from excel_bin import find_file, read_bin
    return len(read_bin(find_file(EXCEL, "monlvl", ".bin"))[0])


# ---------------------------------------------------------------- main

def main(argv):
    ap = argparse.ArgumentParser(prog="mon_sweep.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("logs")
    p.add_argument("--write")
    for name in COMMANDS:
        if name != "logs":
            sub.add_parser(name)
    ns = ap.parse_args(argv)
    return COMMANDS[ns.cmd](ns)


COMMANDS = {"logs": cmd_logs, "pool": cmd_pool, "spawn": cmd_spawn, "special": cmd_special, "stats": cmd_stats, "hire": cmd_hire, "player": cmd_player, "tables": cmd_tables}

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

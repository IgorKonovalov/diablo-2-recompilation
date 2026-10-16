#!/usr/bin/env python3
"""Plan 0038 batch S2a: the items/tc and items/quality checks over every kept stock log, and the table checks.

    python3 -I tools/tc_sweep.py logs [--write FILE]      the stock log set, sha256 checked against the run records
    python3 -I tools/tc_sweep.py replay                   tools/tc.py replay (quality modelled) over the set, counted
    python3 -I tools/tc_sweep.py drops                    DROP/TCR pairing; creation records (IC0) against CPRE/TCR
    python3 -I tools/tc_sweep.py cf                       counterfactual models: each must FAIL where its rule decides
    python3 -I tools/tc_sweep.py tables                   full-table checks of treasureclassex, items, itemratio
    python3 -I tools/tc_sweep.py chest                    object chest TC tier model against the OCT/TCR lines
    python3 -I tools/tc_sweep.py b6save                   the tc-champion Andariel drop from the input save's quest word

The stock log set is every kept log of the stock (no loose table, no -direct) sessions of the items runs that load
tools/gdb/tc-drops.gdb, listed per run below; the forced runs (-forced, ItemRatio or TreasureClassEx edits) are left
out. `replay` runs tools/tc.py's model with the quality roll modelled (tools/quality.py, no oracle) at the magic find
the run record gives, or the logged QMF; the two-client logs of plan 0011, whose players' magic find no record gives,
keep the ADR-0004 oracle. Every count printed is a count of reproduced calls: a call that fails is printed and
counted as failed, and the exit status is 1.

Each output line starts with `S2A <check>`; the "Plan 0038 batch S2a" sections of
docs/findings/items/0001-tc-resolution.md and 0002-quality-roll.md map them to the statements they back.
Stdlib only. Read-only (logs --write writes the manifest file it is given).
"""
import argparse
import collections
import glob
import hashlib
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import d2s  # noqa: E402
import excel_bin  # noqa: E402
import quality  # noqa: E402
import tc  # noqa: E402

ROOT = os.path.dirname(HERE)
LOGS = os.path.join(ROOT, "workspace", "logs")
EXCEL = tc.EXCEL

# Hashes the run records state for logs that have no manifest file (docs/findings/items/experiments.md).
PINNED = {
    "tc-run2.log": "4269d84cc4d5956fa5b91ddeed6619ae147ce69c4ab4c15f1b5c1472a403ee43",
    "tc-run4.log": "694069b8bc16c820bd6b7216df862ec4f7299f5aa5c4aebb8b1e11aaf0c47232",
    "tc-run5.log": "dabc6ebc338d3c68d4ad8e5bd89caf0536bfa54a49815e47778d33b934450331",
    "tc-run6.log": "1c9d1a109f91b802465520c15937c7f2fc1e36ac10003283ee36fc91e7ab2379",
    "tc-run9.log": "51fa25faf1b67c46abd8cf0fd427c4b926c82ffb61980fdd8953a2e404fcf752",
    "tc-run10.log": "7f3af58999aca4c1fccd7a5333fc6db759e3bce3bc435494d7762907d493a041",
    "tc-run13.log": "1aa4b12dcb312cfe8d42836b93c4d70d07ef592ef1c31b4136d4b41166cc56a5",
    "tc-run16.log": "af660d24f232c2901abb7ab69cd6d9cb3cd72d101ba8eb30aa88eda6e10f80c3",
    "tc-run17.log": "c0f26e57e6f078cfbb93e6c3f49d068c51f41ee11c7ec6b3ffb64690dea4a64f",
    "tc-run18.log": "89f28028c1d60190c3678f5b80a58c1771d78e79b4f52a1cd685bd336befeacd",
    "tc-run19.log": "dae5a7a4d646a160cf580144bdc48752b4688b6b1113edad3ef854360fed6b35",
    "tc-party-1.log": "583a4c61d522b09a13761bc5a1a69e00eb733d4385bbb4a28bf90058b1374cd6",
    "tc-party-2.log": "70630dd5d5673e3f0e93619d4a97347148813430187fd6eada9039d2dc8dbf01",
    "tc-party-3.log": "d729fc558fc6616ad600f1a986cb2661a3a89bb1978f0fd08774d81c262e4acd",
    "tc-champion-1.log": "934111ecc088a801b0c39f8972259929e96e96446d56da7a915e44a0cb8d3efe",
    "tc-quality-1.log": "f115a1a16275ad9247be76b440c57d8c2b93739358bdcb49936ea48d809c2121",
    "tc-quality-2.log": "a963b7eb4130c682df3eee70f79f8a56a5e9f124562ea729651b69df4053bb81",
    "tc-quality-3.log": "27605001c2238fe5a2b3192c8e9b7fac121f36f5a18a68683c9c45554a40e1d5",
}

# (run id, log names or a manifest whose names are taken with a prefix filter, magic find input; None = oracle)
RUNS = [
    ("run:2026-10-11-tc-drops", ["tc-run%d.log" % n for n in (2, 4, 5, 6, 9, 10, 13, 16, 17, 18, 19)], 0),
    ("run:2026-10-12-two-clients", ["tc-party-1.log"], None),
    ("run:2026-10-12-tc-party", ["tc-party-2.log", "tc-party-3.log"], None),
    ("run:2026-10-12-tc-champion", ["tc-champion-1.log"], 100),
    ("run:2026-10-12-quality", ["tc-quality-1.log"], 100),
    ("run:2026-10-13-quality", ["tc-quality-2.log", "tc-quality-3.log"], 0),
    ("run:2026-10-14-uniques", ("uniques-stock-manifest.txt", "uniques-"), 0),
    ("run:2026-10-14-affixes", ("affixes-manifest.txt", "affixes"), 0),
    ("run:2026-10-14-props", ("props-stock-manifest.txt", "props-"), 0),
    ("run:2026-10-15-items-chain", ("items-chain-manifest.txt", "ichain-"), 0),
    ("run:2026-10-16-quest-drops", ("quests-run-manifest.txt", "quests-s"), 0),
]
# run:2026-10-15-objects (findings/objects, the S4 cluster) is read only by `chest`: its OCT and PLR lines hold the
# tier and the level id. Sessions 2-30 are the run (session 1 and the smoke log are development logs).
OBJECT_SESSIONS = range(2, 31)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def stock_logs(check=True):
    """[(run, path, mf, sha256, source of the expected hash or None)]."""
    out = []
    for run, spec, mf in RUNS:
        items = []
        if isinstance(spec, list):
            items = [(n, PINNED.get(n), "record") for n in spec]
        elif isinstance(spec, tuple):
            man, pre = spec
            for ln in open(os.path.join(LOGS, man)):
                if not ln.strip():
                    continue
                h, name = ln.split()
                name = os.path.basename(name)
                if name.startswith(pre):
                    items.append((name, h, man))
        for name, want, src in items:
            path = os.path.join(LOGS, name)
            got = sha256(path) if check else None
            if check and want and got != want:
                raise SystemExit("%s: sha256 %s, %s says %s" % (name, got, src, want))
            out.append((run, path, mf, got, src if want else None))
    return out


def cmd_logs(ns):
    logs = stock_logs()
    lines = ["%s  %s" % (h, os.path.relpath(p, ROOT)) for _, p, _, h, _ in logs]
    objs = object_logs()
    lines += ["%s  %s" % (sha256(p), os.path.relpath(p, ROOT)) for p in objs]
    print("S2A logs run:2026-10-15-objects files=%d (chest only)" % len(objs))
    by = collections.Counter(r for r, *_ in logs)
    for r, _, _ in RUNS:
        print("S2A logs %s files=%d" % (r, by[r]))
    print("S2A logs total=%d checked_against_records=%d" % (len(logs), sum(1 for x in logs if x[4])))
    if ns.write:
        with open(ns.write, "w") as f:
            f.write("\n".join(lines) + "\n")
        print("manifest written: %s (sha256 %s)" % (ns.write, sha256(ns.write)))
    return 0


# ---------------------------------------------------------------- replay with counts

class Sweep:
    def __init__(self, excel):
        self.T = tc.Tables(excel)
        self.QT = quality.Tables(excel)
        self.st = {}
        self.mon = collections.Counter()
        self.notes = collections.defaultdict(set)
        self.q = collections.Counter()
        self.qnotes = collections.defaultdict(collections.Counter)
        self.runs = collections.OrderedDict()
        self.fail = 0

    def onsrc(self, tcr, drop, kind):
        T = self.T
        diff, exp, cls = int(tcr["diff"]), int(tcr["exp"]), int(tcr["sclass"])
        mfl = int(tcr.get("mflags", "0"), 16)
        rec = T.monstats(cls)
        boss, noratio = bool(rec[0x0C] & 0x40), bool(rec[0x0C] & 0x04)
        lvl, base = int(drop["lvl"]), int(drop["base"])
        m = self.mon
        m["monster"] += 1
        m["b7.fq%s.nonodrop%s.max%s" % (tcr["fq"], tcr["nonodrop"], tcr["max"])] += 1
        m["monster.diff%d.exp%d" % (diff, exp)] += 1
        m["kind.%s.diff%d.exp%d" % (kind, diff, exp)] += 1
        self.notes["classes.diff%d" % diff].add(cls)
        m["mflags.%s.%02x" % (kind, mfl)] += 1
        if kind == "champion":
            self.notes["champion.class"].add((cls, diff, exp))
        # level upgrade gates (C1)
        if exp and diff > 0 and not boss and not noratio:
            m["gate.open"] += 1
            m["gate.open.lvl_eq_ilvl"] += lvl == int(tcr["ilvl"])
            if kind == "superunique":
                m["gate.open.superunique"] += 1
            up = T.get(base, lvl)
            m["walk.moved" if up != base else "walk.kept"] += 1
            if up != base:
                self.notes["walk.steps"].add(up - base)
                m["walk.steps.%d" % (up - base)] += 1
            if T.tcs[base]["level"] > lvl:
                m["walk.base_above_mlvl"] += 1
        else:
            why = ("classic" if not exp else "normal" if diff == 0 else "boss" if boss else "noratio")
            m["gate.closed.%s" % why] += 1
            if why == "boss":
                self.notes["gate.boss.class"].add((cls, diff))
            if why == "classic" and diff > 0:
                m["gate.closed.classic.above_normal"] += 1

    def qhook(self, QT, item, ilvl, ratio, seed, mf, q, why, ndraw, ri, tcr, extra):
        c = self.q
        diff, exp = tcr.get("diff"), tcr.get("exp")
        c["rolls"] += 1
        c["rolls.diff%s.exp%s" % (diff, exp)] += 1
        r = QT.items[item]
        d = quality.s32(ilvl - r[0xFD])
        if ri is not None:
            c["reach_tests"] += 1
            c["row%d.diff%s" % (ri, diff)] += 1
            if "QROW" in extra:
                c["qrow.row%d.diff%s" % (ri, diff)] += 1
            if d < 0:
                c["reach_tests.d_negative"] += 1
            if ri in (3, 5):
                self.qnotes["uber.bases"][r[0x80:0x84].decode("latin1").strip()] += 1
        c["exit.%s" % why] += 1
        if why.startswith(("superior", "normal:")):
            key = "superior_test.max_d.%s" % ("uber" if ri in (3, 5) else "plain")
            c[key] = max(c.get(key, -999), d)
        if why == "superior:win-nodraw":
            c["superior.nodraw.diff%s" % diff] += 1
            self.qnotes["superior.nodraw.d"][(ri, d)] += 1
        if q == 1:
            self.qnotes["low.row_d"][(ri, d)] += 1
        # M1: the killer test before any stat read (QMF logged, no QKMF line)
        if "QMF" in extra and "QKMF" not in extra:
            k = tcr.get("killer", "")
            kt = int(tcr["ktype"]) if "ktype" in tcr else None
            tag = "null" if (k and int(k, 16) == 0) else ("type%s" % kt)
            c["m1.no_stat_read.%s.mf%s" % (tag, extra["QMF"]["mf"])] += 1
        if "QKMF" in extra:
            c["m2.stat_read.ktype%s" % extra["QKMF"].get("ktype")] += 1

    def run(self, run, path, mf, cf=None, quiet=False, collect=True):
        calls = tc.read_calls(path)
        qmodel = None if mf is None else (self.QT, mf, False)
        st = self.st if collect else {}
        if collect:
            st["qhook"] = self.qhook
        ok, bad, kinds, ccount, ncls, rolls = tc.replay_calls(
            self.T, calls, qmodel, st=st, cf=cf, quiet=quiet, onsrc=self.onsrc if collect else None)
        st.pop("qhook", None)
        r = self.runs.setdefault(run, collections.Counter())
        r["files"] += 1
        r["calls"] += ok + bad
        r["ok"] += ok
        r["bad"] += bad
        r["classic"] += ncls
        r["oracle" if mf is None else "model"] += ok
        self.fail += bad
        return ok, bad


def cmd_replay(ns):
    S = Sweep(ns.excel)
    logs = stock_logs()
    for run, path, mf, _, _ in logs:
        ok, bad = S.run(run, path, mf)
        if bad:
            print("FAIL %s: %d of %d calls" % (os.path.basename(path), bad, ok + bad))
    tot = collections.Counter()
    for run, r in S.runs.items():
        print("S2A replay %s files=%d calls=%d reproduced=%d failed=%d classic=%d quality=%s" % (
            run, r["files"], r["calls"], r["ok"], r["bad"], r["classic"],
            "oracle" if r["oracle"] else "model"))
        tot.update(r)
    print("S2A replay total files=%d calls=%d reproduced=%d failed=%d classic=%d modelled=%d oracle=%d" % (
        tot["files"], tot["calls"], tot["ok"], tot["bad"], tot["classic"], tot["model"], tot["oracle"]))
    st = {k: v for k, v in S.st.items() if not k.startswith("_")}
    print("S2A resolver " + " ".join("%s=%s" % kv for kv in sorted(st.items())))
    nd = sorted(S.st.get("_ndtriples", ()))
    print("S2A nodrop distinct (nd,T,n,nd',bits): %d: %s" % (len(nd), " ".join(
        "(%d,%d,%d,%d,%d)" % x for x in nd)))
    print("S2A monster " + " ".join("%s=%d" % kv for kv in sorted(S.mon.items())))
    for k in sorted(S.notes):
        print("S2A monster.%s %s" % (k, sorted(S.notes[k])))
    print("S2A quality " + " ".join("%s=%d" % kv for kv in sorted(S.q.items())))
    for k in sorted(S.qnotes):
        print("S2A quality.%s %s" % (k, sorted(S.qnotes[k].items(), key=lambda kv: str(kv[0]))))
    if tc.B6_COUNT:
        print("S2A b6 " + " ".join("class%d.diff%d.%s=%d" % (c, d, "taken" if t else "kept", n)
                                   for (c, d, t), n in sorted(tc.B6_COUNT.items())))
    return 0 if S.fail == 0 else 1


def cmd_drops(ns):
    """DROP (TC_DropByIndex, 0x0055AFED) against TCR (TC_ResolveDrops entry) pairing, and the creation record lines
    (IC0, tools/gdb/uniques.py) against the resolver's CPRE and TCR lines."""
    import json
    c = collections.Counter()
    for run, path, mf, _, _ in stock_logs(check=False):
        lines = [ln.strip() for ln in open(path, errors="replace")
                 if ln.startswith(("DROP ", "TCR ", "CPRE ", "TCEND", "IC0 "))]
        tcr = cpre = None
        for i, ln in enumerate(lines):
            if ln.startswith("DROP "):
                kv = tc.parse(ln)[1]
                nxt = lines[i + 1] if i + 1 < len(lines) else ""
                follows = nxt.startswith("TCR ") and ("src=" + kv["src"] + " ") in nxt
                c["drop.base%s.resolver_call=%s" % ("0" if kv["base"] == "0" else "_set", follows)] += 1
            elif ln.startswith("TCR "):
                tcr = tc.parse(ln)[1]
                prev = lines[i - 1] if i else ""
                own = prev.startswith("DROP ") and ("src=" + tcr["src"]) in prev
                c["tcr.stype%s.own_drop_line=%s" % (tcr["stype"], own)] += 1
            elif ln.startswith("CPRE "):
                cpre = tc.parse(ln)[1]
            elif ln.startswith("TCEND"):
                tcr = None
            elif ln.startswith("IC0 ") and cpre is not None and tcr is not None:
                d = json.loads(ln[4:])
                c["ic0.after_cpre.stype%s" % tcr["stype"]] += 1
                if tcr["stype"] == "1":
                    c["ic0.ilvl_eq_source_level=%s" % (d["ilvl"] == int(tcr["ilvl"]))] += 1
                hb = tcr["stype"] == "1" and tcr["sclass"] == "391"
                c["ic0.flag_bit0=%d.source_hellbovine=%s" % (d["rfl"] & 1, hb)] += 1
                c["ic0.upgrade_bits=%d" % (d["rfl"] & 0x14)] += 1
                c["ic0.quality_eq_cpre=%s" % (d["rq"] == int(cpre["q"]))] += 1
                c["ic0.item_seed_start_nonzero=%s" % (d["start"] != 0)] += 1
                c["ic0.seed_is_start_666=%s" % (d["seed"] == "%08x:0000029a" % d["start"])] += 1
                cpre = None
    print("S2A drops " + " ".join("%s=%d" % kv for kv in sorted(c.items())))
    return 0


# ---------------------------------------------------------------- counterfactuals

def tables_without(excel, clause):
    """The runtime TC table rebuilt with one A2 expansion-only clause switched off: "version" (an item whose
    version is >= 100), "subtc" (a sub-TC whose classic total is 0) or "uniqueset" (a unique or set entry). Later
    sub-TC flags follow the changed classic totals, as the loader's order makes them."""
    class TablesCF(tc.Tables):
        def add(self, t, index, flags, prob, aux=0):
            if flags & tc.F_EXPONLY:
                kind = ("subtc" if flags & tc.F_TC else "uniqueset" if flags & (tc.F_UNIQUE | tc.F_SET)
                        else "version")
                if kind == clause:
                    flags &= ~tc.F_EXPONLY
            tc.Tables.add(t, index, flags, prob, aux)
    return TablesCF(excel)


def tables_autoweight(excel):
    """Counterfactual of TC_BuildAutoTCs: every entry weighted by the Rarity of the auto TC's type t, not of the
    item's own type."""
    class TablesAW(tc.Tables):
        def _auto(self):
            self.n_auto_types = 0
            for t, ty in enumerate(self.itypes):
                if not ty["tc"]:
                    continue
                self.n_auto_types += 1
                code = ty["code"].split(" ")[0]
                for L in range(3, 97, 3):
                    t_ = self.new_tc("%s%d" % (code, L), 1, 0, L - 3, [0] * 6, 0)
                    for i, it_ in enumerate(self.items):
                        if it_["quest"] or not it_["spawnable"] or not self.is_type(i, t):
                            continue
                        if t != 38 and self.is_type(i, 38):
                            continue
                        if not (L - 3 < it_["level"] <= L):
                            continue
                        self.add(t_, i, tc.F_EXPONLY if it_["version"] >= 100 else 0, max(1, ty["rarity"]))
                    self._alloc(t_)
    return TablesAW(excel)


def cmd_cf(ns):
    variants = [
        ("nomax", "MAX_DROP: no stop at 6 created items (monster calls, max < 1)", {"nomax": True}, None),
        ("nopop", "D2: an exhausted frame ends the call (no resume of the parent)", {"nopop": True}, None),
        ("notail", "G1: a sub-TC always takes a new frame (no tail call)", {"notail": True}, None),
        ("nodrop-ptq", "F4: NoDrop' = p*T/(1-p) instead of (1-q)*T/q", {"nodrop": "ptq"}, None),
        ("nodrop-24", "F4: 24-bit precision instead of the logged control word", {"nodrop": 24}, None),
        ("nodrop-64", "F4: 64-bit precision instead of the logged control word", {"nodrop": 64}, None),
        ("classic-noskip", "E2: the classic scan does not skip expansion-only entries", {"noskip": True}, "classic"),
        ("classic-cumexp", "E2: classic selection by the expansion search over cumExp", {"cumexp": True}, "classic"),
        ("q-type2", "A2-A5: Normal/Magic/Rare read over type and type2", {"qcf": {"flags": "type2"}}, None),
        ("q-equiv", "A2-A5: Normal/Magic/Rare read over type, type2 and their Equiv ancestors",
         {"qcf": {"flags": "equiv"}}, None),
        ("q-floor", "C1/D4/E1/E3: d / divisor by floor division instead of truncation", {"qcf": {"div": "floor"}}, None),
    ]
    S = Sweep(ns.excel)
    logs = stock_logs(check=False)
    rc = 0
    for name, what, cf, only in variants:
        if ns.only and name not in ns.only:
            continue
        S.runs.clear()
        bad = ok = 0
        for run, path, mf, _, _ in logs:
            if only == "classic" and "exp=0" not in open(path, errors="replace").read(1 << 22):
                continue
            if mf is None and "qcf" in cf:
                continue
            o, b = S.run(run, path, mf, cf=cf, quiet=True, collect=False)
            ok += o
            bad += b
        print("S2A cf %s calls=%d reproduced=%d FAILED=%d  (%s)" % (name, ok + bad, ok, bad, what))
    if not ns.only or "autoweight" in ns.only:
        S2 = Sweep(ns.excel)
        S2.T = tables_autoweight(ns.excel)
        ok = bad = 0
        for run, path, mf, _, _ in logs:
            o, b = S2.run(run, path, mf, quiet=True, collect=False)
            ok += o
            bad += b
        print("S2A cf autoweight calls=%d reproduced=%d FAILED=%d  (I1: auto-TC weight from the TC's type, not the "
              "item's own type)" % (ok + bad, ok, bad))
    for clause in ("version", "subtc", "uniqueset"):
        if ns.only and "a2-" + clause not in ns.only:
            continue
        S2 = Sweep(ns.excel)
        S2.T = tables_without(ns.excel, clause)
        ok = bad = 0
        nchanged = sum(1 for a, b in zip(S.T.tcs[1:], S2.T.tcs[1:]) if a["tclassic"] != b["tclassic"])
        for run, path, mf, _, _ in logs:
            if "exp=0" not in open(path, errors="replace").read(1 << 22):
                continue
            o, b = S2.run(run, path, mf, quiet=True, collect=False)
            ok += o
            bad += b
        print("S2A cf a2-%s tcs_with_other_classic_total=%d classic_calls=%d reproduced=%d FAILED=%d  "
              "(A2: clause '%s' of the expansion-only flag switched off)" % (clause, nchanged, ok + bad, ok, bad, clause))
    return rc


# ---------------------------------------------------------------- tables

def cmd_tables(ns):
    T = tc.Tables(ns.excel)
    QT = quality.Tables(ns.excel)
    rows, _ = excel_bin.read_bin(excel_bin.find_file(ns.excel, "treasureclassex", ".bin"))
    loaded = [r for r in rows]
    n_loaded = next((i for i, r in enumerate(rows) if not tc.cstr(r[0:32])), len(rows))
    picks0 = [tc.cstr(r[0:32]) for r in rows[:n_loaded] if struct.unpack_from("<i", r, 0x20)[0] == 0]
    print("S2A tables tcex rows_loaded=%d (of %d records) picks0=%d %s" % (n_loaded, len(rows), len(picks0),
                                                                          picks0[:8]))
    low_prob, cells, mods = [], 0, collections.Counter()
    w30 = 0
    for r in rows[:n_loaded]:
        name = tc.cstr(r[0:32])
        if struct.unpack_from("<HH", r, 0x30) != (0, 0):
            w30 += 1
        for k in range(10):
            cell = tc.cstr(r[0x38 + 64 * k:0x78 + 64 * k]).replace('"', "")
            if not cell:
                break
            cells += 1
            prob = struct.unpack_from("<i", r, 0x2B8 + 4 * k)[0]
            if prob < 1:
                low_prob.append((name, cell, prob))
            for m in cell.split(",")[1:]:
                mods[m.partition("=")[0]] += 1
    print("S2A tables tcex item_cells=%d prob_below_1=%d %s" % (cells, len(low_prob), low_prob[:8]))
    print("S2A tables tcex modifiers %s; records with a non-zero +0x30/+0x32 word: %d" % (dict(mods), w30))
    neg = []
    for k, t in enumerate(T.tcs[1:], 1):
        if t["picks"] < 0:
            for tot, lab in ((t["texp"], "exp"), (t["tclassic"], "classic")):
                if tot and abs(t["picks"]) > tot:
                    neg.append((t["name"], t["picks"], lab, tot))
    nneg = sum(1 for t in T.tcs[1:] if t["picks"] < 0)
    print("S2A tables tcex negative_picks_tcs=%d with_|picks|>total=%d %s" % (nneg, len(neg), neg))
    # group runs (C2): each run of equal non-zero groups is followed by a loaded TC
    runs, end_bad = 0, []
    i = 1
    while i < len(T.tcs):
        g = T.tcs[i]["group"]
        if g:
            j = i
            while j + 1 < len(T.tcs) and T.tcs[j + 1]["group"] == g:
                j += 1
            runs += 1
            if j + 1 >= len(T.tcs):
                end_bad.append(T.tcs[j]["name"])
            i = j + 1
        else:
            i += 1
    last = T.tcs[-1]
    print("S2A tables tcex group_runs=%d runs_ending_on_the_last_tc=%d last_tc=#%d %r group=%d" % (
        runs, len(end_bad), len(T.tcs) - 1, last["name"], last["group"]))
    # runtime group offset (reimplementation note): the walk compares groups for equality only, so the offset
    # cannot change a walk; checked by walking every TC at every level with and without it
    diff = 0
    for k in range(1, len(T.tcs)):
        for lvl in range(0, 100):
            a = T.get(k, lvl)
            saved = [t["group"] for t in T.tcs[1:]]
            for t in T.tcs[1:]:
                if t["group"]:
                    t["group"] -= T.n_auto_types
            b = T.get(k, lvl)
            for t, g in zip(T.tcs[1:], saved):
                t["group"] = g
            diff += a != b
    print("S2A tables tcex group_offset n_auto_types=%d walks_differing_without_offset=%d (of %d)" % (
        T.n_auto_types, diff, (len(T.tcs) - 1) * 100))
    # classic scan (E2): the skip and the run off the end, over every TC and every roll
    skip_diff = miss = sel = 0
    for t in T.tcs[1:]:
        ents = t["entries"]
        if not any(e["flags"] & tc.F_EXPONLY for e in ents) or not t["tclassic"]:
            continue
        for roll in range(t["tclassic"]):
            sel += 1
            a = classic_sel(ents, roll, True)
            b = classic_sel(ents, roll, False)
            skip_diff += a != b
            miss += a >= len(ents)
    print("S2A tables classic_scan selections=%d (every roll of every TC with an expansion-only entry) "
          "noskip_differs=%d runs_off_the_end=%d" % (sel, skip_diff, miss))
    # A2 clauses: TCs whose classic total each clause changes
    cl = collections.Counter()
    for t in T.tcs[1:]:
        for e in t["entries"]:
            if e["flags"] & tc.F_EXPONLY:
                kind = ("subtc" if e["flags"] & tc.F_TC else "uniqueset" if e["flags"] & (tc.F_UNIQUE | tc.F_SET)
                        else "version")
                cl[kind] += 1
    print("S2A tables a2 expansion_only_entries %s unresolved_cells=%d %s" % (dict(cl), len(T.unresolved),
                                                                            T.unresolved[:4]))
    # items reachable from any TC entry (auto TCs included)
    reach = set()
    for t in T.tcs[1:]:
        for e in t["entries"]:
            if not e["flags"] & tc.F_TC:
                reach.add(e["index"])
    uniq = [i for i, r in enumerate(QT.items) if r[0x129]]
    magq = [i for i, r in enumerate(QT.items) if QT.itypes[QT.type_of(i)][0x14] and r[0x12A]]
    code = lambda i: QT.items[i][0x80:0x84].decode("latin1").strip()  # noqa: E731
    print("S2A tables items unique_flag=%d %s reachable=%d; magic_type_quest=%d %s reachable=%d" % (
        len(uniq), [code(i) for i in uniq], len(set(uniq) & reach), len(magq), [code(i) for i in magq],
        len(set(magq) & reach)))
    # own type against type2 / Equiv (A2-A5)
    for how in ("type2", "equiv"):
        diffs = [i for i in range(len(QT.items))
                 if bytes(quality.type_flags(QT, i, how)) != bytes(
                     1 if QT.itypes[QT.type_of(i)][0x14 + k] else 0 for k in range(3))]
        print("S2A tables items flags_differ_%s=%d reachable=%d e.g. %s" % (
            how, len(diffs), len(set(diffs) & reach), [code(i) for i in sorted(set(diffs) & reach)][:12]))
    lv = [QT.items[i][0xFD] for i in range(len(QT.items))]
    print("S2A tables items level_max=%d (u8 field; a value above 127 would tell u8 from s8)" % max(lv))
    # E3-E4: low quality needs n = (Normal - d / NormalDivisor) << 7 >= 129
    for ri, row in enumerate(QT.ratio):
        v = row["v"]
        ds = [d for d in range(-200, 201) if quality.s32((v[14] - quality.cdiv(d, quality.s32(v[15]))) << 7) >= 129]
        print("S2A tables itemratio row%d (ver %d uber %d class %d) Normal=%d NormalDivisor=%d low_possible_d=%s" % (
            ri, row["ver"], row["uber"], row["cls"], v[14], v[15],
            "%d..%d" % (min(ds), max(ds)) if ds else "none"))
    zero = [(ri, k) for ri, row in enumerate(QT.ratio) for k in (1, 4, 7, 10, 13, 15) if row["v"][k] == 0]
    print("S2A tables itemratio zero_divisors=%d" % len(zero))
    # F4 over every stock (NoDrop, total) pair and n = 2..8: the alternatives that the logged evaluations cannot
    # tell apart from the game's formula
    pairs = sorted({(t["nodrop"], tot) for t in T.tcs[1:] if t["nodrop"] and t["picks"] > 0
                    for tot in (t["texp"], t["tclassic"]) if tot})
    cnt = collections.Counter()
    for nd, tot in pairs:
        for n in range(2, 9):
            g = tc.nodrop_scaled(nd, tot, n, 53)
            cnt["cases"] += 1
            cnt["ptq_differs"] += tc.nodrop_ptq(nd, tot, n, 53) != g
            cnt["pc24_differs"] += tc.nodrop_scaled(nd, tot, n, 24) != g
            cnt["pc64_differs"] += tc.nodrop_scaled(nd, tot, n, 64) != g
            cnt["exact_differs"] += int(Fraction_nd(nd, tot, n)) != g
    print("S2A tables nodrop stock (NoDrop, total) pairs=%d, n=2..8: %s" % (len(pairs), dict(cnt)))
    return 0


def Fraction_nd(nd, tot, n):
    """F4 in exact rational arithmetic (no rounding), truncated."""
    from fractions import Fraction
    p = Fraction(nd, nd + tot) ** n
    return 0 if p == 1 else p * tot / (1 - p)


def classic_sel(ents, roll, skip):
    for k in range(len(ents)):
        if skip and ents[k]["flags"] & tc.F_EXPONLY:
            continue
        if k >= len(ents) - 1 or ents[k + 1]["cumc"] > roll:
            return k
    return len(ents)


# ---------------------------------------------------------------- object chest TC

ACT_BOUNDS = 0x006EB2F0     # DRLG_ActFromLevelId: level id < bound[k+1] -> act k
ACT_RANGE = 0x006E1988      # sub_00585B90_ObjectChestDrop: per act, two reference level ids


def image_dwords(va, n, exe):
    import pe_info
    p = pe_info.parse(exe)
    data = open(exe, "rb").read()
    for s in p["sections"]:
        if s["va"] <= va - p["image_base"] < s["va"] + s["vsize"]:
            off = s["raw"] + va - p["image_base"] - s["va"]
            return list(struct.unpack_from("<%di" % n, data, off))
    raise ValueError("va %x not in the image" % va)


def object_logs():
    return [p for k in OBJECT_SESSIONS for p in sorted(glob.glob(os.path.join(LOGS, "objects-s%d-*.log" % k)))]


def cmd_chest(ns):
    T = tc.Tables(ns.excel)
    lev, _ = excel_bin.read_bin(excel_bin.find_file(ns.excel, "levels", ".bin"))
    bounds = image_dwords(ACT_BOUNDS, 6, ns.exe)
    rng_ = image_dwords(ACT_RANGE, 10, ns.exe)

    def act_of(lid):
        for k in range(1, 6):
            if lid < bounds[k]:
                return k - 1
        return 5

    def monlvl(lid, diff, exp):
        if diff >= 3 or lid <= 0 or lid >= len(lev):
            return 1
        return struct.unpack_from("<h", lev[lid], (0x16 if exp else 0x10) + 2 * diff)[0]

    names = {}
    for d, suf in enumerate(("", " (N)", " (H)")):
        for a in range(5):
            for tier, lab in enumerate("ABC"):
                names[(d, a, tier)] = T.names.get(("act %d%s chest %s" % (a + 1, suf, lab)).lower())
    ok = bad = 0
    seen = collections.Counter()
    for path in object_logs():
        if True:
            lid = None
            oct_ = None
            for ln in open(path, errors="replace"):
                if ln.startswith("PLR {"):
                    lid = int(ln.split('"lid":', 1)[1].split(",", 1)[0])
                elif ln.startswith("OCT {"):
                    oct_ = ln
                elif ln.startswith("TCR ") and " stype=2 " in ln:
                    kv = tc.parse(ln.strip())[1]
                    diff, exp = int(kv["diff"]), int(kv["exp"])
                    a = act_of(lid)
                    m = monlvl(lid, diff, exp)
                    lo = monlvl(rng_[2 * a], diff, exp)
                    hi = monlvl(rng_[2 * a + 1], diff, exp)
                    w = (abs(hi - lo) + 1) // 3
                    tier = 0 if m < lo + w else (2 if m >= lo + 2 * w else 1)
                    want = names[(diff, a, tier)]
                    logged_tier = int(oct_.split('"tier":', 1)[1].split(",", 1)[0]) if oct_ else None
                    good = want == int(kv["tc"]) and logged_tier in (None, tier) and int(kv["ilvl"]) == tier
                    if good:
                        ok += 1
                        seen[(diff, exp, a, tier)] += 1
                    else:
                        bad += 1
                        print("FAIL %s lid=%s act=%d mlvl=%d range=%d..%d tier=%d tc=%s want=%s OCT tier=%s ilvl=%s" % (
                            os.path.basename(path), lid, a, m, lo, hi, tier, kv["tc"], want, logged_tier, kv["ilvl"]))
                    oct_ = None
    print("S2A chest calls=%d reproduced=%d failed=%d (tier from the area level of the player's level, act range "
          "%s; TC named 'Act a%%s Chest X'; TCR ilvl = tier)" % (ok + bad, ok, bad, rng_))
    print("S2A chest cases (diff, exp, act, tier): %s" % sorted(seen.items()))
    return 0 if bad == 0 else 1


# ---------------------------------------------------------------- B6 from the input save

def cmd_b6save(ns):
    T = tc.Tables(ns.excel)
    rec = T.monstats(156)
    qid, cp = rec[0x9E], rec[0x9F]
    with open(ns.save, "rb") as f:
        words = d2s.quest_words(f.read())
    w = words[1][qid]
    # QUESTRECORD_LoadBytes sets bit 15 when bit 1 was saved (save/0002 section 1)
    if w >> 1 & 1:
        w |= 0x8000
    tests = [(15, w >> 15 & 1), (1, w >> 1 & 1), (cp, w >> cp & 1)]
    taken = not any(r for _, r in tests)
    col = lambda k: struct.unpack_from("<H", rec, 0x86 + 8 * 1 + 2 * k)[0]  # noqa: E731
    want = col(3) if taken else col(2)
    logged = None
    for ln in open(os.path.join(LOGS, "tc-champion-1.log"), errors="replace"):
        if ln.startswith("DROP ") and logged is None:
            pass
        if ln.startswith("TCR ") and " sclass=156 " in ln:
            break
        if ln.startswith("DROP "):
            logged = int(tc.parse(ln.strip())[1]["base"])
    print("S2A b6save save=%s sha256=%s nightmare word %d = 0x%04x (after the loader) tests %s -> %s; model base %d, "
          "logged DROP base %s: %s" % (os.path.relpath(ns.save, ROOT), sha256(ns.save), qid, w, tests,
                                        "TreasureClass4(N)" if taken else "TreasureClass3(N)", want, logged,
                                        "match" if want == logged else "MISMATCH"))
    return 0 if want == logged else 1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("logs")
    a.add_argument("--write")
    for name in ("replay", "drops", "cf", "tables", "chest", "b6save"):
        p = sub.add_parser(name)
        p.add_argument("--excel", default=EXCEL)
        if name == "cf":
            p.add_argument("--only", nargs="*")
        if name == "chest":
            p.add_argument("--exe", default=os.path.join(ROOT, "workspace", "install", "app", "game.exe"))
        if name == "b6save":
            p.add_argument("--save", default=os.path.join(ROOT, "workspace", "runtime", "owner-chars",
                                                          "LightSorc-noacts.d2s"))
    ns = ap.parse_args(argv)
    return {"logs": cmd_logs, "replay": cmd_replay, "drops": cmd_drops, "cf": cmd_cf, "tables": cmd_tables, "chest": cmd_chest,
            "b6save": cmd_b6save}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

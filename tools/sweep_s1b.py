#!/usr/bin/env python3
"""Plan 0038 batch S1b: static second sources and kept-log re-checks for data/README, data/calc, data/excel,
data/strings, rng and rng/seeds (no game run, no slot).

    python3 -I tools/sweep_s1b.py logs [--write FILE]  the logs the checks read, sha256 checked against the run records
    python3 -I tools/sweep_s1b.py arch                  archive precedence: record sizes, DS1 and string-table counterfactuals
    python3 -I tools/sweep_s1b.py compile               the game's own `-direct -txt` compile (run:2026-10-15-cube-saves)
    python3 -I tools/sweep_s1b.py survey                excel_bin.py survey on the shipped and on the game-compiled .bin;
                                                        lookup-cell counts; the language counterfactual
    python3 -I tools/sweep_s1b.py tc                    the runtime TC array against every stock tc-drops call (tc.py replay)
    python3 -I tools/sweep_s1b.py items                 item code <-> index pairs (vendors, quest drops); the gamble list
    python3 -I tools/sweep_s1b.py strings               the strings run per caller (GetStringByKey, gems, rare names,
                                                        runes), the font map, duplicates over every shipped key
    python3 -I tools/sweep_s1b.py calc                  the calc run per pool (tables, contexts, callers, raw pools)
    python3 -I tools/sweep_s1b.py static                pinned instructions and image bytes (objdump), RNG-free closures,
                                                        operand scans
    python3 -I tools/sweep_s1b.py rng                   LCG sites, the primitives' memory operands, the pow2 n = 0 cases
    python3 -I tools/sweep_s1b.py seeds                 the seed-tree logs: room chains by type, client unit types
    python3 -I tools/sweep_s1b.py all

Each check prints one `S1B <check> key=value ...` line of counts plus detail lines, and exits 1 when an observation
contradicts the claim it tests (`bad` above 0). A counterfactual (`cf_*`) is a sensitivity check: it must FAIL (a count
above 0) where the claim decides. A claim with no stock case shows as a zero count, never as a failure. The batch record
is the "Plan 0038 batch S1b" section of docs/findings/data/0001..0005 and rng/0001..0002.

The second tool next to Ghidra is GNU objdump, through tools/sweep_s4b.py (its listing parser and call-graph walker,
accepted at the S4b review) and tools/xrefscan.py (raw byte scans). Heavy checks (tc, arch) are meant to run under
`systemd-run --user --scope -p MemoryMax=4G`. Stdlib only, plus objdump. Read-only, apart from symlink trees under
workspace/scratch-s1b/ (counterfactual data roots) and `logs --write`.
"""
import argparse
import collections
import contextlib
import functools
import hashlib
import io
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sweep_s4b as S4  # noqa: E402

ROOT = os.path.dirname(HERE)
WS = os.path.join(ROOT, "workspace")
LOGS = os.path.join(WS, "logs")
MERGED = os.path.join(WS, "merged")
EXCEL = os.path.join(MERGED, "data", "global", "excel")
ENG = os.path.join(MERGED, "data", "local", "lng", "eng")
MPQ = os.path.join(WS, "mpq")
GAME = os.path.join(WS, "runtime", "game")
PROBE = os.path.join(WS, "runtime", "game-cubeprobe", "data", "global", "excel")
SCRATCH = os.path.join(WS, "scratch-s1b")

# objdump decodes .text once per process
S4.asm = functools.lru_cache(maxsize=None)(S4.asm)


# ------------------------------------------------------------------------------------------------------------ report
class Report:
    def __init__(self, name):
        self.name = name
        self.c = collections.Counter()
        self.notes = []

    def add(self, k, n=1):
        self.c[k] += n

    def set(self, k, v):
        self.c[k] = v

    def bad(self, why):
        self.c["bad"] += 1
        self.notes.append("BAD " + why)

    def expect(self, ok, why):
        if not ok:
            self.bad(why)

    def note(self, s):
        self.notes.append(s)

    def done(self):
        self.c.setdefault("bad", 0)
        print("S1B %s %s" % (self.name, " ".join("%s=%d" % (k, self.c[k]) for k in sorted(self.c))))
        for s in self.notes:
            print("  " + s)
        return 1 if self.c["bad"] else 0


@contextlib.contextmanager
def quiet():
    buf, old = io.StringIO(), sys.stdout
    sys.stdout = buf
    try:
        yield buf
    finally:
        sys.stdout = old


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def jlines(path, tags):
    """(tag, dict) of the JSON lines `TAG {...}` of the given tags."""
    with open(path, errors="replace") as f:
        for ln in f:
            tag, _, rest = ln.partition(" ")
            if tag in tags and rest.startswith("{"):
                try:
                    yield tag, json.loads(rest)
                except ValueError:
                    continue


def kvlines(path, tags):
    """(tag, {k: v}) of the `TAG k=v k=v` lines of the seed-tree logger."""
    with open(path, errors="replace") as f:
        for ln in f:
            tag, _, rest = ln.rstrip("\n").partition(" ")
            if tag in tags:
                yield tag, dict(kv.split("=", 1) for kv in rest.split() if "=" in kv)


def bin_recs(path):
    b = open(path, "rb").read()
    n = struct.unpack_from("<I", b)[0]
    rs = (len(b) - 4) // n if n else 0
    return n, rs, [b[4 + i * rs: 4 + (i + 1) * rs] for i in range(n)]


def excel_file(d, name, ext=".bin"):
    want = (name + ext).lower()
    for f in os.listdir(d):
        if f.lower() == want:
            return os.path.join(d, f)
    return None


def walk_lower(top):
    """{relative path lower-cased: absolute path} of every file under top."""
    out = {}
    for r, _, fs in os.walk(top):
        for f in fs:
            p = os.path.join(r, f)
            out[os.path.relpath(p, top).lower()] = p
    return out


# ------------------------------------------------------------------------------------------------------------- logs
STRINGS_LOGS = ("strings-manifest.txt", ["strings-s2-2802-exp.log", "strings-s2-2803-cls.log"])
CALC_RUN = "calc-manifest.txt"
VENDORS_RUN = "vendors-run-manifest.txt"
QUESTS_RUN = "quests-run-manifest.txt"
# run:2026-10-11-seed-tree and -p1: the records give no per-file hash; the hashes are recorded here, at the batch
# run:2026-10-12-d2s-io: the logs whose item lines carry the code read at g_pItems + cls * 0x1A8 + 0x80
D2SIO_LOGS = ["d2sio-1.log", "d2sio-4-seed7.log", "d2sio-5-tblfixed.log", "d2sio-7-drop.log"]
SEED_LOGS = ["run-12345-a.log", "run-12345-b.log", "run-777-a.log", "run-12345-act2.log", "run-12345-act3.log",
             "run-12345-act4.log", "run-12345-act5.log", "run-34844169-act5.log", "run-p1-12345-a.log",
             "run-p1-12345-b.log", "run-p1-777-a.log", "run-p1-entropy-0.log"]


def manifest(name, only=None):
    """[(path, recorded sha256)] of a run manifest (sha256  name per line)."""
    out = []
    for ln in open(os.path.join(LOGS, name)):
        if not ln.strip():
            continue
        h, n = ln.split()[:2]
        n = os.path.basename(n)
        if only is None or n in only:
            out.append((os.path.join(LOGS, n), h))
    return out


def calc_logs():
    return [p for p, _ in manifest(CALC_RUN) if "-dev-" not in p]


def strings_logs():
    return [p for p, _ in manifest(STRINGS_LOGS[0], STRINGS_LOGS[1])]


def vendor_logs():
    return [p for p, _ in manifest(VENDORS_RUN)]


def quest_logs():
    return [p for p, _ in manifest(QUESTS_RUN)]


def d2sio_logs():
    return [os.path.join(LOGS, n) for n in D2SIO_LOGS]


def seed_logs():
    return [os.path.join(LOGS, n) for n in SEED_LOGS]


def cmd_logs(a):
    R = Report("logs")
    lines = []
    sets = [("run:2026-10-15-strings", manifest(STRINGS_LOGS[0], STRINGS_LOGS[1])),
            ("run:2026-10-16-calc", [(p, h) for p, h in manifest(CALC_RUN) if "-dev-" not in p]),
            ("run:2026-10-15-vendors", manifest(VENDORS_RUN)),
            ("run:2026-10-16-quest-drops", manifest(QUESTS_RUN))]
    for run, items in sets:
        n = 0
        for p, want in items:
            got = sha256(p)
            if got != want:
                R.bad("%s: sha256 %s, manifest says %s" % (p, got, want))
            lines.append("%s  %s" % (got, os.path.relpath(p, ROOT)))
            n += 1
        R.add("files_%s" % run.split(":")[1], n)
    for p in seed_logs():
        lines.append("%s  %s" % (sha256(p), os.path.relpath(p, ROOT)))
        R.add("files_seed-tree_unrecorded")
    for p in d2sio_logs():
        lines.append("%s  %s" % (sha256(p), os.path.relpath(p, ROOT)))
        R.add("files_d2s-io_unrecorded")
    import tc_sweep
    tl = tc_sweep.stock_logs()
    R.add("files_tc_stock_via_tc_sweep", len(tl))
    lines += ["%s  %s" % (h, os.path.relpath(p, ROOT)) for _, p, _, h, _ in tl]
    import sweep_s4a
    ds = sweep_s4a.log_set("preset") + sweep_s4a.log_set("acts35")
    R.add("files_preset_acts35_via_sweep_s4a", len(ds))
    lines += ["%s  %s" % (sha256(p), os.path.relpath(p, ROOT)) for p in ds]
    R.add("total", len(lines))
    if a.write:
        with open(a.write, "w") as f:
            f.write("\n".join(lines) + "\n")
        R.note("manifest written: %s (sha256 %s)" % (a.write, sha256(a.write)))
    return R.done()


# ------------------------------------------------------------------------------------------------------------- arch
def mirror(dst, src_root, overrides):
    """A symlink tree of src_root at dst, with overrides {relative lower-case path: absolute path} replacing files.
    Returns the number of files overridden. Rebuilt when it exists."""
    import shutil
    if os.path.exists(dst):
        shutil.rmtree(dst)
    n = 0
    for r, _, fs in os.walk(src_root):
        rel = os.path.relpath(r, src_root)
        os.makedirs(os.path.join(dst, rel), exist_ok=True)
        for f in fs:
            key = os.path.normpath(os.path.join(rel, f)).lower()
            src = overrides.get(key, os.path.join(r, f))
            n += key in overrides
            os.symlink(src, os.path.join(dst, rel, f))
    return n


def differing(layer, sub, ext, base=MERGED):
    """{relative lower path: layer file} for the files under sub/ with extension ext that the layer holds with other
    bytes than the merged tree."""
    L = os.path.join(MPQ, layer)
    lw = walk_lower(L)
    mw = walk_lower(base)
    out = {}
    for rel, p in lw.items():
        if rel.startswith(sub) and rel.endswith(ext) and rel in mw:
            if open(p, "rb").read() != open(mw[rel], "rb").read():
                out[rel] = p
    return out


def ds1_replay(root):
    """tools/drlg.py gen over the preset and acts-3-5 logs (sweep_s4a.run_gen) with the data root `root`."""
    import sweep_s4a
    old = sweep_s4a.DATA
    sweep_s4a.DATA = root
    try:
        paths = sweep_s4a.log_set("preset") + sweep_s4a.log_set("acts35")
        m, rk, bad = sweep_s4a.run_gen(paths)
    finally:
        sweep_s4a.DATA = old
    return len(paths), len(m.prooms), bad


def strings_check(lng):
    import tbl
    with quiet() as buf:
        tbl.check(lng, strings_logs())
    line = [ln for ln in buf.getvalue().splitlines() if ln.startswith("CHECK strings")][-1]
    c = dict(kv.split("=") for kv in line.split()[2:])
    c = {k: int(v) for k, v in c.items()}
    return c["sidx"] + c["skey"], c["sidx"] - c["sidx_ok"] + c["skey"] - c["skey_ok"]


def cmd_arch(a):
    """data/README row 1; data/excel rows 11, 19, 21, 23, 28 (archive order, file layer)."""
    R = Report("arch")
    # (1) excel .bin: the copies d2exp and patch_d2 both hold, against the record size the loaders' consumers use
    D = os.path.join(MPQ, "d2exp", "data", "global", "excel")
    P = os.path.join(MPQ, "patch_d2", "data", "global", "excel")
    pf = {f.lower(): f for f in os.listdir(P)}
    for f in sorted(os.listdir(D), key=str.lower):
        lf = f.lower()
        if not lf.endswith(".bin") or lf not in pf:
            continue
        dn, drs, _ = bin_recs(os.path.join(D, f))
        pn, prs, _ = bin_recs(os.path.join(P, pf[lf]))
        mn, mrs, _ = bin_recs(excel_file(EXCEL, lf[:-4]))
        R.add("bins_in_both")
        R.expect((pn, prs) == (mn, mrs), "%s: merged copy is not patch_d2's" % lf)
        if open(os.path.join(D, f), "rb").read() == open(os.path.join(P, pf[lf]), "rb").read():
            R.add("bins_identical")
        elif drs != prs:
            R.add("bins_d2exp_record_size_differs")
        else:
            R.add("bins_d2exp_same_size_other_bytes")
    R.add("d2data_bins", sum(1 for f in os.listdir(os.path.join(MPQ, "d2data", "data", "global", "excel"))
                             if f.lower().endswith(".bin")))
    # (2) DS1 counterfactuals: drlg.py gen (preset units and rooms) over the preset and acts-3-5 logs
    nlogs, prooms, bad = ds1_replay(MERGED)
    R.add("ds1_logs", nlogs)
    R.add("ds1_merged_mismatches", bad)
    R.add("ds1_preset_rooms", prooms)
    R.expect(bad == 0, "the merged tree does not reproduce the preset logs")
    patch = walk_lower(os.path.join(MPQ, "patch_d2"))
    for layer in ("d2data", "d2exp"):
        ov = differing(layer, os.path.join("data", "global", "tiles"), ".ds1")
        if layer == "d2data":
            # only the files whose merged copy is d2exp's (patch_d2 does not hold them): d2exp against d2data
            ov = {k: v for k, v in ov.items() if k not in patch}
        root = os.path.join(SCRATCH, "cf-ds1-" + layer)
        mirror(root, MERGED, ov)
        _, _, cbad = ds1_replay(root)
        R.add("cf_ds1_%s_files" % layer, len(ov))
        R.add("cf_ds1_%s_mismatches" % layer, cbad)
        R.expect(cbad > 0, "cf %s: the lower archive's DS1 copies reproduce the logs too" % layer)
    # (3) string tables: patchstring.tbl from d2exp in place of patch_d2's, over the strings run
    n, bad = strings_check(ENG)
    R.add("strings_lines", n)
    R.add("strings_merged_mismatches", bad)
    R.expect(bad == 0, "the merged eng tables do not reproduce the strings run")
    lw = walk_lower(os.path.join(MPQ, "d2exp"))
    dps = lw.get(os.path.join("data", "local", "lng", "eng", "patchstring.tbl"))
    if dps and open(dps, "rb").read() != open(os.path.join(ENG, "patchstring.tbl"), "rb").read():
        cf = os.path.join(SCRATCH, "cf-lng-d2exp")
        mirror(cf, os.path.join(MERGED, "data", "local"), {os.path.join("lng", "eng", "patchstring.tbl"): dps})
        _, cbad = strings_check(os.path.join(cf, "lng", "eng"))
        R.add("cf_patchstring_d2exp_mismatches", cbad)
        R.expect(cbad > 0, "cf: d2exp's patchstring.tbl reproduces the strings run too")
    else:
        R.note("d2exp holds no differing eng patchstring.tbl")
    # (4) equal-priority bands: a file two archives of one band hold with different bytes
    bands = [["d2data", "d2sfx", "d2speech", "d2char", "d2music", "d2video"],
             ["d2exp", "d2xmusic", "d2xtalk", "d2xvideo"]]
    W = {x: walk_lower(os.path.join(MPQ, x)) for b in bands for x in b}
    for b in bands:
        for i, x in enumerate(b):
            for y in b[i + 1:]:
                for rel in set(W[x]) & set(W[y]):
                    R.add("tie_files_shared")
                    if open(W[x][rel], "rb").read() != open(W[y][rel], "rb").read():
                        R.add("tie_files_differing")
                        R.note("tie: %s in %s and %s" % (rel, x, y))
    # (5) the game directory of every stock run: no d2kfixup.mpq or d2delta.mpq
    have = {f.lower() for f in os.listdir(GAME)}
    R.set("game_dir_has_d2kfixup", int("d2kfixup.mpq" in have))
    R.set("game_dir_has_d2delta", int("d2delta.mpq" in have))
    R.set("game_dir_has_d2exp", int("d2exp.mpq" in have))
    return R.done()


# ---------------------------------------------------------------------------------------------------------- compile
# data/0001 section 3: the 15 code-list tables DATATBLS_LoadCodeLists skips without -txt, and compcode (always)
CODE_LISTS = ["playerclass", "bodylocs", "storepage", "elemtypes", "hitclass", "colors", "hiredesc", "monmode",
              "plrmode", "monai", "monplace", "skillcalc", "misscalc", "skills", "events"]
CODE_BINS = ["itemscode", "misscode", "skillscode", "skilldesccode"]
NO_LOADER = ["treasureclass", "aiparms", "monname", "weaponclass"]


def cmd_compile(a):
    """data/excel rows 10, 26, 29, 30 (and the monstats NameStr cell of data/0004's open question)."""
    R = Report("compile")
    written = {f.lower(): os.path.join(PROBE, f) for f in os.listdir(PROBE) if f.lower().endswith(".bin")}
    shipped = {f.lower(): os.path.join(EXCEL, f) for f in os.listdir(EXCEL) if f.lower().endswith(".bin")}
    R.add("bins_written", len(written))
    R.add("txt_in_probe_dir", sum(1 for f in os.listdir(PROBE) if f.lower().endswith(".txt")))
    for f, p in sorted(written.items()):
        if f not in shipped:
            R.add("written_not_shipped")
            R.note("written, not shipped: " + f)
        elif open(p, "rb").read() == open(shipped[f], "rb").read():
            R.add("written_byte_identical")
        else:
            R.add("written_differs")
            a_, b_ = open(p, "rb").read(), open(shipped[f], "rb").read()
            if len(a_) == len(b_):
                n, rs, _ = bin_recs(p)
                d = [i for i in range(len(a_)) if a_[i] != b_[i]]
                R.note("%s: %d bytes differ, records %s, offsets %s" % (
                    f, len(d), sorted({(i - 4) // rs for i in d}), sorted({hex((i - 4) % rs) for i in d})))
                if f == "monstats.bin":
                    for r in sorted({(i - 4) // rs for i in d}):
                        o = 4 + r * rs
                        R.note("  monstats record %d %s: NameStr u16 at +0x006 compiled %d, shipped %d" % (
                            r, a_[o:o + 0].decode() or "", struct.unpack_from("<H", a_, o + 6)[0],
                            struct.unpack_from("<H", b_, o + 6)[0]))
            else:
                R.note("%s: %d bytes written, %d shipped (the probe's own cubemain.txt)" % (f, len(a_), len(b_)))
    for f in sorted(set(shipped) - set(written)):
        R.add("shipped_not_written")
        R.note("shipped, not written: " + f)
    for t in NO_LOADER:
        R.add("no_loader_bin_written", int((t + ".bin") in written))
        R.expect((t + ".bin") not in written, t + ".bin was written")
        R.add("no_loader_txt_in_archives", int(any(excel_file(os.path.join(MPQ, x, "data", "global", "excel"), t, ".txt")
                                                  for x in ("d2data", "d2exp", "patch_d2"))))
    for t in CODE_LISTS:
        R.add("codelist_bin_written", int((t + ".bin") in written))
        inarch = [x for x in ("d2data", "d2exp", "patch_d2")
                  if excel_file(os.path.join(MPQ, x, "data", "global", "excel"), t)]
        R.add("codelist_bin_in_stock_archives", int(bool(inarch)))
    for t in CODE_BINS:
        R.add("codebin_written", int((t + ".bin") in written))
    return R.done()


# ----------------------------------------------------------------------------------------------------------- survey
def survey_counts(excel):
    import excel_bin
    with quiet() as buf:
        rc = excel_bin.cmd_survey(excel)
    last = [ln for ln in buf.getvalue().splitlines() if ln.startswith("SURVEY")][-1]
    c = dict(kv.split("=") for kv in last.split()[2:])
    return rc, {k: int(v) for k, v in c.items() if v.lstrip("-").isdigit()}


def cmd_survey(a):
    """data/excel rows 41 (F), 55 (language), 61, 62, 63, 67, 68 (J)."""
    import excel_bin
    import excel_layouts
    import tbl
    R = Report("survey")
    rc, c = survey_counts(EXCEL)
    for k in ("tables", "records", "cells", "unexplained", "explained", "errors"):
        R.add("shipped_" + k, c.get(k, 0))
    R.expect(rc == 0 and c.get("unexplained", 1) == 0, "survey of the shipped tables")
    # the same survey on the .bin files the pinned game compiled (cubemain excepted: the probe's own .txt)
    croot = os.path.join(SCRATCH, "compiled", "data")
    comp = os.path.join(croot, "global", "excel")
    ov = {f.lower(): os.path.join(PROBE, f) for f in os.listdir(PROBE)
          if f.lower().endswith(".bin") and f.lower() != "cubemain.bin"}
    mirror(comp, EXCEL, ov)
    if not os.path.lexists(os.path.join(croot, "local")):
        os.symlink(os.path.join(MERGED, "data", "local"), os.path.join(croot, "local"))
    rc2, c2 = survey_counts(comp)
    for k in ("tables", "records", "cells", "unexplained", "explained", "errors"):
        R.add("compiled_" + k, c2.get(k, 0))
    R.expect(c2.get("unexplained", 1) == 0, "survey of the game-compiled tables")
    # lookup cells over the laid-out tables: code lookups (code4) and name lookups (nocase), by width
    refs = excel_bin.Refs(EXCEL)
    for tname, lay in sorted(excel_layouts.LAYOUTS.items()):
        tp = excel_bin.find_file(EXCEL, lay.get("txt", tname), ".txt")
        if not tp:
            continue
        header, rows = excel_bin.read_txt(tp)
        for f in lay["fields"]:
            if f.get("type") != "ref" or f.get("col") not in header:
                continue
            kind = "code" if f.get("code4") else ("name" if f.get("nocase") else "other")
            ci = header.index(f["col"])
            spec = f["ref"]
            keys = refs.names(spec)
            lower = collections.Counter(k.lower() for k in keys)
            for r in rows:
                cell = r[ci] if ci < len(r) else ""
                if not cell:
                    continue
                R.add("cells_%s_%s" % (kind, f.get("int", "u16")))
                if kind == "name":
                    if cell.lower() in lower and cell not in keys:
                        R.add("name_cells_case_differs_from_key")
                    if len(cell) > 31:
                        R.add("name_cells_over_31")
                    if lower.get(cell.lower(), 0) > 1:
                        R.add("name_cells_duplicated_key")
                if kind == "code":
                    if len(cell) > 4:
                        R.add("code_cells_over_4")
                    if len(cell) < 4:
                        R.add("code_cells_padded")
    # the language: every string-key cell against the deu / fra tables in place of eng
    eng = tbl.Strings(ENG)
    for lang in ("deu", "fra"):
        L = os.path.join(MERGED, "data", "local", "lng", lang)
        if not os.path.exists(os.path.join(L, "string.tbl")):
            continue
        cfdir = os.path.join(SCRATCH, "lng-" + lang)
        import shutil
        if os.path.exists(cfdir):
            shutil.rmtree(cfdir)
        os.makedirs(cfdir)
        for t in ("string.tbl", "patchstring.tbl", "expansionstring.tbl"):
            src = os.path.join(L, t) if os.path.exists(os.path.join(L, t)) else os.path.join(ENG, t)
            os.symlink(src, os.path.join(cfdir, t))
        other = tbl.Strings(cfdir)
        R.add("%s_string_entries" % lang, tbl.Tbl(os.path.join(L, "string.tbl")).count)
        diff = tot = 0
        for tname, lay in sorted(excel_layouts.LAYOUTS.items()):
            tp = excel_bin.find_file(EXCEL, lay.get("txt", tname), ".txt")
            if not tp:
                continue
            header, rows = excel_bin.read_txt(tp)
            for f in lay["fields"]:
                if f.get("type") != "tbl" or f.get("col") not in header:
                    continue
                ci = header.index(f["col"])
                for r in rows:
                    cell = r[ci] if ci < len(r) else ""
                    if not cell:
                        continue
                    tot += 1
                    diff += eng.index(cell) != other.index(cell)
        R.add("string_key_cells", tot)
        R.add("cf_%s_cells_differ" % lang, diff)
        R.expect(diff > 0, "cf %s: the %s tables compile every string-key cell as eng does" % (lang, lang))
    R.add("eng_string_entries", tbl.Tbl(os.path.join(ENG, "string.tbl")).count)
    return R.done()


# --------------------------------------------------------------------------------------------------------------- tc
def tc_indices(path):
    """Counter of (kind, index) of the TC indices the tc-drops lines name: TCR tc=, SUB tc=, DROP base=."""
    out = collections.Counter()
    with open(path, errors="replace") as f:
        for ln in f:
            if ln.startswith(("TCR ", "SUB ", "DROP ")):
                m = re.search(r"\b(?:tc|base)=(\d+)", ln)
                if m:
                    out[(ln.split()[0], int(m.group(1)))] += 1
    return out


def cmd_tc(a):
    """data/excel rows 9, 13 (with static), 14, 42, 45, 78: the runtime TC array of tools/tc.py against every logged
    TC visit of the stock item runs (the S2a log set)."""
    import tc
    import tc_sweep
    R = Report("tc")
    T = tc.Tables(EXCEL)
    R.set("model_tcs", len(T.tcs))
    R.set("model_auto_types", T.n_auto_types)
    R.set("model_auto_tcs", sum(1 for i in range(1, len(T.tcs)) if i <= 32 * T.n_auto_types))
    R.set("model_tcex_loaded", len(T.tcs) - 1 - 32 * T.n_auto_types)
    rows, _ = tc_sweep.excel_bin.read_bin(tc_sweep.excel_bin.find_file(EXCEL, "treasureclassex", ".bin"))
    R.set("tcex_records", len(rows))
    first_empty = next((i for i, r in enumerate(rows) if not r[0:32].split(b"\0")[0]), None)
    R.set("tcex_first_empty_record", -1 if first_empty is None else first_empty)
    quoted = [(161 + i, k) for i, r in enumerate(rows[:first_empty]) for k in range(10)
              if b'"' in r[0x38 + 64 * k: 0x78 + 64 * k].split(b"\0")[0]]
    R.set("tcex_cells_with_quote", len(quoted))
    groups = collections.Counter(struct.unpack_from("<H", r, 0x24)[0] for r in rows[:first_empty])
    R.set("tcex_groups_nonzero", sum(1 for g in groups if g))
    # the replay: every stock call (S2a: 9390), with the quality roll modelled where S2a modelled it
    S = tc_sweep.Sweep(EXCEL)
    visits = collections.Counter()
    for run, path, mf, _, _ in tc_sweep.stock_logs(check=False):
        ok, bad = S.run(run, path, mf, quiet=True, collect=False)
        R.add("calls_reproduced", ok)
        R.add("calls_failed", bad)
        visits.update(tc_indices(path))
    R.expect(S.fail == 0, "tc replay failures")
    idx = collections.Counter()
    for (tag, i), n in visits.items():
        idx[i] += n
    auto = sorted(i for i in idx if 1 <= i <= 32 * T.n_auto_types)
    tcex = sorted(i for i in idx if i > 32 * T.n_auto_types)
    R.set("distinct_tc_indices_logged", len(idx))
    R.set("auto_tcs_logged", len(auto))
    R.set("tcex_tcs_logged", len(tcex))
    R.set("max_tc_index_logged", max(idx) if idx else 0)
    R.set("index0_logged", int(0 in idx))
    R.set("auto_levels_logged", len({(i - 1) % 32 for i in auto}))
    R.set("auto_types_logged", len({(i - 1) // 32 for i in auto}))
    R.set("quoted_cells_in_logged_tcs", sum(1 for i, k in quoted if i in idx))
    R.set("grouped_tcs_logged", sum(1 for i in tcex if T.tcs[i]["group"]))
    for i in auto[:3] + auto[-3:]:
        R.note("auto %d = %s (%d entries)" % (i, T.tcs[i]["name"], len(T.tcs[i]["entries"])))
    R.note("highest logged: %d = %s" % (max(idx), T.tcs[max(idx)]["name"]))
    for i, k in quoted[:5]:
        R.note("quoted cell: TC %d %s Item%d%s" % (i, T.tcs[i]["name"], k + 1, " (logged)" if i in idx else ""))
    return R.done()


# ------------------------------------------------------------------------------------------------------------ items
def combined_items():
    """[(code bytes, version)] of weapons ++ armor ++ misc, in file order."""
    out = []
    for t in ("weapons", "armor", "misc"):
        _, _, recs = bin_recs(excel_file(EXCEL, t))
        out += [(r[0x80:0x84], r[0xFD]) for r in recs]
    return out


def cmd_items(a):
    """data/excel rows 12, 34, 38, 73, 77: logged (code, item index) pairs against the combined position; the gamble
    list."""
    R = Report("items")
    items = combined_items()
    pos = {}
    for i, (c, _) in enumerate(items):
        pos.setdefault(c, i)
    R.set("items_combined", len(items))
    R.set("codes_distinct", len(pos))
    n = {t: len(bin_recs(excel_file(EXCEL, t))[2]) for t in ("weapons", "armor", "misc")}
    R.set("weapons", n["weapons"])
    R.set("armor", n["armor"])
    R.set("misc", n["misc"])
    for t in ("weapons", "armor", "misc"):
        R.expect(bin_recs(excel_file(EXCEL, t))[1] == 0x1A8, t + " record size is not 0x1A8")
    pairs = collections.Counter()
    # vendors: CSW {want: code, idx: item index} (VENDOR_CreateStockItem: the chosen code and its index)
    for p in vendor_logs():
        for tag, d in jlines(p, ("CSW",)):
            pairs[("CSW", d["want"].encode("latin-1"), d["idx"])] += 1
    # quest drops: QDI {code} followed by the IC0 of the created item {cls}
    for p in quest_logs():
        want = None
        for tag, d in jlines(p, ("QDI", "IC0")):
            if tag == "QDI":
                want = d["code"].encode("latin-1")
            elif want is not None:
                pairs[("QDI", want, d["cls"])] += 1
                want = None
    # save I/O run: item units logged with their class and the 4 bytes at g_pItems + cls * 0x1A8 + 0x80, read from
    # the game's memory (tools/gdb/d2s-io.py item_fields)
    for p in d2sio_logs():
        with open(p, errors="replace") as f:
            for ln in f:
                for m in re.finditer(r'"cls":(-?\d+),[^{}]*?"code":"(.{4})"', ln):
                    pairs[("MEM", m.group(2).encode("latin-1"), int(m.group(1)))] += 1
    regions = collections.Counter()
    for (src, code, idx), k in pairs.items():
        R.add("pairs_%s" % src, k)
        ok = pos.get(code) == idx
        R.add("pairs_ok" if ok else "pairs_bad", k)
        if not ok:
            R.bad("%s %r logged index %d, combined position %s" % (src, code, idx, pos.get(code)))
        regions["weapons" if idx < n["weapons"] else "armor" if idx < n["weapons"] + n["armor"] else "misc"] += 1
    R.set("distinct_pairs", len(pairs))
    for k, v in sorted(regions.items()):
        R.set("distinct_pairs_in_%s" % k, v)
    # u32 code reading: "hax " little-endian
    R.set("hax_u32", struct.unpack("<I", b"hax ")[0])
    R.expect(struct.unpack("<I", items[0][0])[0] == 0x20786168, "item 0 code u32 is not 0x20786168")
    # the gamble list: VGL items are the gamble codes' combined positions, ordered by base level (+0xFD)
    gb = [r[0:4] for r in bin_recs(excel_file(EXCEL, "gamble"))[2]]
    lists = set()
    for p in vendor_logs():
        for tag, d in jlines(p, ("VGL",)):
            lists.add((tuple(d["items"]), tuple(d["cnt"])))
    R.set("gamble_rows", len(gb))
    R.set("gamble_list_dumps_distinct", len(lists))
    for items_, cnt in lists:
        want = sorted(pos[c] for c in gb)
        R.expect(sorted(items_) == want, "VGL members are not the gamble codes' positions")
        lv = [items[i][1] for i in items_]
        R.expect(lv == sorted(lv), "VGL not sorted by base level")
        cu = [sum(1 for x in lv if x <= L) for L in range(1, 100)]
        R.expect(list(cnt[1:]) == cu, "VGL countUpTo is not the count of base levels <= L")
        R.set("gamble_list_len", len(items_))
        R.set("gamble_equal_level_runs", sum(1 for i in range(1, len(lv)) if lv[i] == lv[i - 1]))
    return R.done()


# ---------------------------------------------------------------------------------------------------------- strings
RA = {0x00524E35: "GetStringByKey", 0x0063721C: "GEMS_Load", 0x006341F4: "LoadRareAffixes", 0x00639C68: "RUNES_Load"}


def cmd_strings(a):
    """data/strings rows 1, 3, 11, 21, 31, 33; data/excel rows 57, 72, 75, 76."""
    import tbl
    R = Report("strings")
    n, bad = strings_check(ENG)
    R.set("lines", n)
    R.set("model_mismatches", bad)
    R.expect(bad == 0, "tbl.py check")
    by = collections.defaultdict(list)
    sidx = []
    for p in strings_logs():
        for tag, d in jlines(p, ("SKEY", "SIDX")):
            if tag == "SKEY":
                by[d["ra"]].append(d)
            else:
                sidx.append(d)
    for ra, name in RA.items():
        R.set("skey_%s" % name, len(by.get(ra, [])))
    # GetStringByKey: the text it returns is GetByKey's (model) text
    m = tbl.GameStrings(ENG, "spx")
    gsk = by.get(0x00524E35, [])
    R.set("getstringbykey_not_found", sum(1 for d in gsk if d["idx"] == 0))
    R.set("getstringbykey_found", sum(1 for d in gsk if d["idx"] != 0))
    # gems: keys = record bytes +0x28..+0x2A with 0x20 -> 0, every lookup returns 0
    gems = bin_recs(excel_file(EXCEL, "gems"))[2]
    gkeys = set()
    for r in gems:
        k = bytes(0 if b == 0x20 else b for b in r[0x28:0x2B]).split(b"\0")[0]
        gkeys.add(k)
    lg = {d["key"].encode("latin-1") for d in by.get(0x0063721C, [])}
    R.set("gems_rows", len(gems))
    R.set("gems_keys_distinct", len(gkeys))
    R.set("gems_logged_keys_distinct", len(lg))
    R.expect(lg == gkeys, "gem keys differ from the record bytes: %r" % sorted(lg ^ gkeys)[:5])
    R.set("gems_idx_nonzero", sum(1 for d in by.get(0x0063721C, []) if d["idx"] != 0))
    R.expect(R.c["gems_idx_nonzero"] == 0, "a gem key was found")
    # rare names: key = record +0x26 (the name), records of rareprefix then raresuffix
    rk = []
    for t in ("rareprefix", "raresuffix"):
        rk += [r[0x26:].split(b"\0")[0] for r in bin_recs(excel_file(EXCEL, t))[2]]
    lr = {d["key"].encode("latin-1"): d["idx"] for d in by.get(0x006341F4, [])}
    R.set("rare_rows", len(rk))
    R.set("rare_keys_distinct", len(set(rk)))
    R.set("rare_logged_keys_distinct", len(lr))
    allk = {d["key"].encode("latin-1") for v in by.values() for d in v}
    miss = set(rk) - set(lr)
    R.set("rare_keys_logged_by_other_caller", sum(1 for k in miss if k in allk))
    R.expect(set(lr) <= set(rk) and miss <= allk, "rare keys differ from the record names: %r" % sorted(miss - allk))
    for k in sorted(miss):
        R.note("rare key %r: logged first through another caller (one line per distinct key)" % k)
    R.set("rare_idx_eq_model", sum(1 for k, i in lr.items() if m.by_key(k)[0] == i))
    # runes: key = record +0x00 (Name); the two Runeword95 rows share one key and so one index
    rn = [r[0:].split(b"\0")[0] for r in bin_recs(excel_file(EXCEL, "runes"))[2]]
    lrn = {d["key"].encode("latin-1"): d["idx"] for d in by.get(0x00639C68, [])}
    R.set("runes_rows", len(rn))
    R.set("runes_keys_distinct", len(set(rn)))
    R.set("runes_logged_keys_distinct", len(lrn))
    miss = set(rn) - set(lrn)
    R.expect(set(lrn) <= set(rn) and miss <= allk, "rune keys differ from the record names")
    dup = [k for k, v in collections.Counter(rn).items() if v > 1]
    R.set("runes_duplicated_names", len(dup))
    for k in dup:
        R.note("runes name %r on rows %s, logged index %s" % (k, [i for i, x in enumerate(rn) if x == k], lrn.get(k)))
    # the font map (latin) and the two-byte 0x7F
    ranges = tbl.read_font_map(os.path.join(MERGED, "data", "local", "font", "latin", "default.map"))
    R.note("latin font map ranges: %s" % [(hex(lo), hex(hi)) for lo, hi in ranges])
    k7f = [d for d in by.get(0x0063721C, []) if d["key"].encode("latin-1").startswith(b"\x7f")]
    for d in k7f[:1]:
        raw = d["key"].encode("latin-1") + tbl.NOT_XLATED
        R.set("key_7f_len_logged", d["len"])
        R.set("key_7f_raw_bytes", len(raw))
        R.set("key_7f_chars_lost", len(raw) - d["len"])
    R.set("key_7f_lines", len(k7f))
    # case: a logged key that a table holds only under another case, and the game's answer
    tables = {t: tbl.Tbl(os.path.join(ENG, f)) for t, f in (("p", "patchstring.tbl"), ("x", "expansionstring.tbl"),
                                                             ("s", "string.tbl"))}
    lowkeys = collections.defaultdict(set)
    for t, T in tables.items():
        for e in range(T.count):
            node = T.index[e]
            ko = T.nodes[node][3]
            lowkeys[T.data[ko:T.data.index(b"\0", ko)].lower()].add(T.data[ko:T.data.index(b"\0", ko)])
    case_only = 0
    for ra, lst in by.items():
        for d in lst:
            k = d["key"].encode("latin-1")
            if k and k.lower() in lowkeys and k not in lowkeys[k.lower()]:
                case_only += 1
                R.note("case-only key %r -> logged index %d" % (k, d["idx"]))
    R.set("keys_present_only_under_other_case", case_only)
    # the worked example's index rows
    for want in (21796, 5382):
        hits = [d for d in sidx if d["idx"] == want]
        R.set("sidx_%d_lines" % want, len(hits))
        for d in hits[:1]:
            R.note("SIDX %d ld=%s t=%s entry=%d node=%d text=%r" % (want, d["ld"], d["t"], d["entry"], d["node"],
                                                                     d["text"]))
    # duplicates: over every key of the three eng tables, the probe walk returns the lowest entry of that key
    gs = tbl.GameStrings(ENG, "spx")
    for t, T in tables.items():
        first = {}
        for e in range(T.count):
            node = T.index[e]
            ko = T.nodes[node][3]
            first.setdefault(T.data[ko:T.data.index(b"\0", ko)], e)
        for key, e in first.items():
            R.add("keys_walked")
            home, probes, entry, slot = gs.find(t, key)
            if entry != e:
                R.bad("%s key %r: walk gives %r, lowest entry %d" % (t, key, entry, e))
            if len(probes) > T.max_probes:
                R.bad("%s key %r beyond max_probes" % (t, key))
        R.add("dup_entries_%s" % t, T.count - len(first))
    # logged keys that a table holds more than once: the logged entry is the lowest
    lowest = {}
    for t, T in tables.items():
        cnt = collections.Counter()
        first = {}
        for e in range(T.count):
            ko = T.nodes[T.index[e]][3]
            k = T.data[ko:T.data.index(b"\0", ko)]
            cnt[k] += 1
            first.setdefault(k, e)
        lowest[t] = {k: first[k] for k, n in cnt.items() if n > 1}
    base = {"p": 10000, "x": 20000, "s": 0}
    seen = set()
    for lst in by.values():
        for d in lst:
            k = d["key"].encode("latin-1")
            hit = [f for f in d["f"] if f["res"] is not None]
            if not hit or (k, hit[0]["t"]) in seen:
                continue
            t = hit[0]["t"]
            if k in lowest[t]:
                seen.add((k, t))
                ok = d["idx"] == base[t] + lowest[t][k]
                R.add("logged_dup_keys_lowest" if ok else "logged_dup_keys_other")
                R.expect(ok, "dup key %r: logged %d, lowest %d" % (k, d["idx"], base[t] + lowest[t][k]))
    R.set("logged_dup_keys", len(seen))
    nu = [d for d in by.get(0x00524E35, []) + [x for v in by.values() for x in v] if d["key"] == "not used"][:1]
    st = tables["s"]
    ents = [e for e in range(st.count)
            if st.data[st.nodes[st.index[e]][3]:st.data.index(b"\0", st.nodes[st.index[e]][3])] == b"not used"]
    R.set("not_used_entries", len(ents))
    R.set("not_used_lowest_entry", min(ents) if ents else -1)
    if nu:
        R.set("not_used_logged_index", nu[0]["idx"])
        R.expect(nu[0]["idx"] == min(ents), "'not used' resolved to %d, lowest entry %d" % (nu[0]["idx"], min(ents)))
    return R.done()


# ------------------------------------------------------------------------------------------------------------- calc
POOL_FUNCS = {"skillscode": (0x00745774, 7), "skilldesccode": (0x00745774, 7), "misscode": (0x00745828, 4),
              "itemscode": (0x0074463C, 4)}
CALL_SITES = {"misscode": {0x0064B1A4: "MISS_GetElemMin", 0x0064B274: "MISS_GetElemMax"},
              "itemscode": {0x005BEE04: "len", 0x005BEF16: "calc1..3"}}


def cmd_calc(a):
    """data/calc rows 1, 2, 6, 7, 18, 19; data/excel row 31."""
    R = Report("calc")
    sizes = {p: os.path.getsize(excel_file(EXCEL, p)) for p in POOL_FUNCS}
    bases = collections.defaultdict(set)
    ra2 = collections.defaultdict(collections.Counter)
    item_ctx = []
    for path in calc_logs():
        for tag, d in jlines(path, ("CE",)):
            pool = d.get("pool")
            if pool not in POOL_FUNCS:
                R.add("ce_outside_pools")
                continue
            R.add("ce_%s" % pool)
            fn, nf = POOL_FUNCS[pool]
            if (d["funcs"], d["nf"]) != (fn, nf):
                R.bad("%s: funcs %x/%d, expected %x/%d" % (pool, d["funcs"], d["nf"], fn, nf))
            if d["off"] + d["len"] != sizes[pool]:
                R.bad("%s: off + len = %d, file size %d" % (pool, d["off"] + d["len"], sizes[pool]))
            else:
                R.add("ce_whole_file_%s" % pool)
            bases[(os.path.basename(path), pool)].add(d["code"] - d["off"])
            if pool in CALL_SITES:
                ra2[pool][d["ra2"]] += 1
            if pool == "itemscode":
                item_ctx.append((os.path.basename(path), d["c"], d.get("u", {})))
    R.set("pool_bases_constant", sum(1 for v in bases.values() if len(v) == 1))
    R.set("pool_bases_varying", sum(1 for v in bases.values() if len(v) != 1))
    R.expect(R.c["pool_bases_varying"] == 0, "a pool's base moved within a log")
    for pool, cnt in ra2.items():
        for ra, n in sorted(cnt.items()):
            R.set("ra2_%s_%08X" % (pool, ra), n)
            R.expect(ra in CALL_SITES[pool], "%s evaluated from 0x%08X" % (pool, ra))
    # item context: word 0 is the context unit of the session's skill evaluations (the player), word 1 another pointer
    players = collections.defaultdict(set)
    for path in calc_logs():
        for tag, d in jlines(path, ("CE",)):
            if d.get("pool") == "skillscode":
                players[os.path.basename(path)].add(d["c"][0])
    for log, c, u in item_ctx:
        R.add("item_ctx")
        R.add("item_ctx_unit_is_player" if c[0] in players[log] and u.get("type") == 0 else "item_ctx_unit_other")
        R.add("item_ctx_word1_differs_from_unit", int(c[1] != c[0]))
    R.set("item_ctx_word1_distinct", len({(log, c[1]) for log, c, _ in item_ctx}))
    R.expect(R.c["item_ctx_unit_other"] == 0, "an item evaluation's unit is not the player")
    # static: the function tables and their counts in the image
    for name, (tab, cnt_va, n) in {"miss": (0x00745828, 0x00745848, 4), "items": (0x0074463C, 0x0074465C, 4)}.items():
        R.set("image_%s_count" % name, S4.dword(cnt_va))
        R.expect(S4.dword(cnt_va) == n, "%s count dword" % name)
        ents = [(S4.dword(tab + 8 * k), S4.dword(tab + 8 * k + 4)) for k in range(n)]
        R.note("%s table: %s" % (name, ", ".join("(0x%08X, %d)" % e for e in ents)))
        R.set("image_%s_entries_in_text" % name, sum(1 for f, _ in ents if S4.section_of(f) == ".text"))
    # static: each logged return address follows a call of the entry point
    A = S4.asm()
    for pool, sites in CALL_SITES.items():
        target = 0x0064B7C0 if pool == "misscode" else 0x00627C20
        for ra in sites:
            prev = max(v for v in A.ins if v < ra)
            mn, ops = A.ins[prev]
            ok = mn == "call" and S4.branch_target(ops) == target
            R.add("callsite_ok" if ok else "callsite_bad")
            R.expect(ok, "0x%08X is not after a call of 0x%08X" % (ra, target))
    for ra, fn in ((0x0064B1A4, 0x0064B100), (0x0064B274, 0x0064B1D0), (0x005BEE04, 0x005BEDA0),
                   (0x005BEF16, 0x005BEDA0)):
        vas, _, _ = S4.body(A, fn)
        R.add("callsite_in_body" if max(v for v in A.ins if v < ra) in vas else "callsite_outside_body")
    # g_ItemUseFns: entry pSpell 9 uses 0x005BEDA0; entry 6's use function calls it
    use9 = S4.dword(0x00741790 + 9 * 8 + 4)
    use6 = S4.dword(0x00741790 + 6 * 8 + 4)
    R.note("g_ItemUseFns[9].use = 0x%08X, [6].use = 0x%08X" % (use9, use6))
    R.set("itemuse9_is_timedstate", int(use9 == 0x005BEDA0))
    _, calls6, _ = S4.body(A, use6)
    R.set("itemuse6_calls_timedstate", int(any(t == 0x005BEDA0 for _, t in calls6)))
    return R.done()


# ----------------------------------------------------------------------------------------------------------- static
# (row, address, mnemonic, operand regex): instructions the batch cites, decoded by objdump
PINNED = [
    # data/excel 35: the link object, one layout in all its functions
    ("excel35", 0x006BD04D, "mov", r"edx,0x10$"),
    ("excel35", 0x006BD05B, "mov", r"DWORD PTR \[eax\],ecx"),
    ("excel35", 0x006BD063, "mov", r"DWORD PTR \[eax\+0xc\],ecx"),
    ("excel35", 0x006BD138, "mov", r"esi,DWORD PTR \[eax\]$"),
    ("excel35", 0x006BD13F, "mov", r"edi,DWORD PTR \[eax\+0x8\]"),
    ("excel35", 0x006BD152, "mov", r"edx,DWORD PTR \[edi\+eax\*8\]"),
    ("excel35", 0x006BD170, "mov", r"eax,DWORD PTR \[edi\+eax\*8\+0x4\]"),
    ("excel35", 0x006BD25C, "cmp", r"DWORD PTR \[ebx\+0xc\],0x0"),
    ("excel35", 0x006BD269, "mov", r"eax,DWORD PTR \[ebx\+0x4\]"),
    ("excel35", 0x006BD26C, "cmp", r"eax,DWORD PTR \[ebx\]"),
    ("excel35", 0x006BD27A, "lea", r"esi,\[eax\+0x40\]"),
    ("excel35", 0x006BD3F3, "mov", r"esi,DWORD PTR \[eax\+0xc\]"),
    ("excel35", 0x006BD450, "mov", r"esi,DWORD PTR \[esi\+0x24\]"),
    ("excel35", 0x006BD455, "mov", r"esi,DWORD PTR \[esi\+0x28\]"),
    ("excel35", 0x006BD473, "mov", r"eax,DWORD PTR \[esi\+0x20\]"),
    ("excel35", 0x006BD52B, "cmp", r"DWORD PTR \[edi\+0x8\],0x0"),
    ("excel35", 0x006BD579, "lea", r"eax,\[edi\+0xc\]"),
    ("excel35", 0x006BD57E, "mov", r"DWORD PTR \[esi\+0x20\],ecx"),
    ("excel35", 0x006BD5C9, "cmp", r"DWORD PTR \[edi\+0x8\],0x0"),
    ("excel35", 0x006BD625, "lea", r"eax,\[edi\+0xc\]"),
    # data/excel 13 and 42 (Alloc): the TC array stride, writer and reader
    ("excel13", 0x00653FB8, "add", r"eax,0x10$"),
    ("excel13", 0x00653FBB, "imul", r"eax,eax,0x2c$"),
    ("excel13", 0x00653FDC, "imul", r"eax,eax,0x2c$"),
    ("excel13", 0x00654E0F, "cmp", r"eax,DWORD PTR ds:0x96c5f0"),
    ("excel13", 0x00654E17, "imul", r"eax,eax,0x2c$"),
    ("excel13", 0x00654E1A, "add", r"eax,DWORD PTR ds:0x96c5ec"),
    ("excel13", 0x00654E4E, "add", r"ecx,0x2c$"),
    # data/excel 12: ITEMS_GetByCode's record stride
    ("excel12", 0x00633650, "call", r"0x6bd130$"),
    ("excel12", 0x0063366D, "imul", r"eax,eax,0x1a8$"),
    # rng/seeds 1: g_SeedOverride, read and compared with -1, written only by GAME_SetSeedOverride
    ("seeds1", 0x0052C283, "mov", r"eax,ds:0x731004$"),
    ("seeds1", 0x0052C28B, "cmp", r"eax,0xffffffff$"),
    ("seeds1", 0x0052C326, "mov", r"ds:0x731004,eax$"),
    # data/strings 1/3: GetStringByKey = GetByKey(key, &text), returns the text
    ("strings1", 0x00524E29, "mov", r"DWORD PTR \[ebp-0x4\],0x0"),
    ("strings1", 0x00524E30, "call", r"0x524d30$"),
    ("strings1", 0x00524E35, "mov", r"eax,DWORD PTR \[ebp-0x4\]"),
    # data/excel 72 / strings 21, 75, 76: the return value of GetByKey stored into the record
    ("excel72", 0x006371D6, "movzx", r"eax,BYTE PTR \[esi\+edi\*1\+0x28\]"),
    ("excel72", 0x006371FA, "movzx", r"eax,BYTE PTR \[esi\+edi\*1\+0x2a\]"),
    ("excel72", 0x00637217, "call", r"0x524d30$"),
    ("excel72", 0x00637225, "mov", r"WORD PTR \[esi\+edx\*1\+0x2c\],ax"),
    ("excel75", 0x006341EA, "lea", r"edx,\[esi\+ecx\*1\+0x26\]"),
    ("excel75", 0x006341EF, "call", r"0x524d30$"),
    ("excel75", 0x006341FA, "mov", r"WORD PTR \[esi\+ecx\*1\+0xc\],ax"),
    ("excel75", 0x00634202, "add", r"esi,0x48$"),
    ("excel76", 0x00639C63, "call", r"0x524d30$"),
    ("excel76", 0x00639C6E, "mov", r"WORD PTR \[ecx\+esi\*1\+0x82\],ax"),
    # rng/seeds 16: the client creator sends type 1 to 0x00466360, others to UnitInit
    ("seeds16", 0x0046675C, "cmp", r"edi,0x1$"),
    ("seeds16", 0x0046675F, "jne", r"0x4667a4$"),
    ("seeds16", 0x00466796, "call", r"0x466360$"),
    ("seeds16", 0x004667D6, "call", r"0x465fd0$"),
]


def cmd_static(a):
    R = Report("static")
    A = S4.asm()
    for row, va, mn, rx in PINNED:
        ins = A.at(va)
        ok = ins is not None and ins[0] == mn and re.search(rx, ins[1]) is not None
        R.add("pinned_%s_%s" % (row, "ok" if ok else "bad"))
        if not ok:
            R.bad("0x%08X: %r, expected %s %s" % (va, ins, mn, rx))
    # rng/seeds 1: the sentinel's bytes and every reference to the variable
    off = S4.va_off(0x00731004)
    R.set("seed_override_initial", S4.dword(0x00731004))
    R.set("seed_override_section_data", int(S4.section_of(0x00731004) == ".data"))
    R.set("seed_override_file_backed", int(off is not None))
    refs = sorted(va for va, (m, o) in A.ins.items() if "0x731004" in o)
    R.set("seed_override_operands", len(refs))
    R.set("seed_override_raw_abs", len(S4.raw_abs(0x00731004)))
    R.note("g_SeedOverride operands: %s" % ", ".join("0x%08X %s %s" % ((v,) + A.ins[v]) for v in refs))
    writes = [v for v in refs if re.match(r"(DWORD PTR )?ds:0x731004,", A.ins[v][1])]
    R.set("seed_override_writes", len(writes))
    R.expect(writes == [0x0052C326], "writers of g_SeedOverride: %s" % [hex(v) for v in writes])
    R.set("setseedoverride_raw_callers", len(S4.raw_callers(0x0052C320)))
    # data/excel 49: every operand naming g_MonStatsLink
    refs = sorted(va for va, (m, o) in A.ins.items() if "0x96c6ac" in o)
    R.set("monstatslink_operands", len(refs))
    R.set("monstatslink_raw_abs", len(S4.raw_abs(0x0096C6AC)))
    kinds = collections.Counter()
    for v in refs:
        m, o = A.ins[v]
        if re.match(r"DWORD PTR \[ebp-0x[0-9a-f]+\],0x96c6ac$", o) or o in ("edx,0x96c6ac", "ecx,0x96c6ac"):
            kinds["descriptor_link_field"] += 1
        elif o == "ds:0x96c6ac,eax":
            kinds["store_after_LinkCreate"] += 1
        else:
            nxt = [A.ins[x] for x in sorted(x for x in A.ins if v < x <= v + 16)]
            tgt = [S4.branch_target(op) for mm, op in nxt if mm == "call"]
            kinds["load_then_call_%s" % ("LinkFree" if 0x006BD0B0 in tgt else "FindName" if 0x006BD3C0 in tgt
                                         else "other")] += 1
        R.note("g_MonStatsLink 0x%08X %s %s" % (v, m, o))
    for k, n in kinds.items():
        R.set("monstatslink_" + k, n)
    # the FindName site's function: who references it
    fn = 0x00659990
    R.set("findname_site_fn_raw_callers", len(S4.raw_callers(fn)))
    R.set("findname_site_fn_raw_abs", len(S4.raw_abs(fn)))
    R.note("0x00659990 (FindName through g_MonStatsLink at 0x006599D6) is referenced only at %s" %
           [hex(v) for v in S4.raw_abs(fn)])
    # rng/seeds 3, 15: the room allocators and the client item-data helpers draw nothing (objdump closure)
    for name, roots in (("room_alloc", [0x0067D6D0, 0x00666630]), ("item_data", [0x00627C90, 0x00627DC0])):
        for r in roots:
            _, calls, icalls = S4.body(A, r)
            R.note("%s 0x%08X: direct callees %s, indirect %d" % (name, r, sorted({"0x%08X" % t for _, t in calls}),
                                                                  len(icalls)))
        G = S4.graph(roots)
        Rf = S4.rng_functions(G)
        draws = {e: v for e, v in Rf.items()
                 if v[0] or any(n not in ("RNG_SeedInit", "RNG_SeedInitOne") for _, n in v[1])}
        inits_only = [e for e in Rf if e not in draws]
        R.set("%s_functions" % name, len(G))
        R.set("%s_draw_functions" % name, len(draws))
        R.set("%s_init_only_functions" % name, len(inits_only))
        ind = [ic for v in G.values() for ic in v[4]]
        R.set("%s_indirect_calls_iat" % name, sum(1 for ic in ind if re.match(r"DWORD PTR ds:0x6cc", A.ins[ic][1])))
        R.set("%s_indirect_calls_other" % name, sum(1 for ic in ind if not re.match(r"DWORD PTR ds:0x6cc", A.ins[ic][1])))
        R.expect(not draws, "%s: drawing functions %s" % (name, [hex(e) for e in draws]))
        for e in inits_only:
            R.note("%s: 0x%08X only initialises a seed (%s)" % (name, e, [c[1] for c in Rf[e][1]]))
    # rng/seeds 16: callers of the client UnitInit and of the client monster creator
    R.note("UnitInit 0x00465FD0 raw callers: %s" % [hex(v) for v in S4.raw_callers(0x00465FD0)])
    R.note("ClientMonCreate 0x00466360 raw callers: %s" % [hex(v) for v in S4.raw_callers(0x00466360)])
    # data/excel 33: the logger reads of the data-tables globals (tools/gdb/*.py and *.gdb)
    glob_ = {0x0096C5EC: "g_pTreasureClasses", 0x0096C5F0: "g_nTreasureClasses", 0x0096CA5C: "g_pItems",
             0x0096CA58: "g_nItems", 0x0096C6A8: "g_pMonStats", 0x0096C888: "g_pLevels", 0x0096C828: "g_pItemTypes",
             0x0096CC4C: "g_pItemRatio", 0x0096C890: "g_pLevelDefs", 0x0096C5E8: "g_TCLink", 0x0096BCC4: "g_ItemCodeLink",
             0x0096C6B0: "nMonStats", 0x0096C88C: "nLevels", 0x0096C82C: "nItemTypes", 0x0096CC48: "nItemRatio",
             0x0096C6AC: "g_MonStatsLink", 0x0096CA64: "nWeapons", 0x0096CA6C: "nArmor", 0x0096CA74: "nMisc"}
    gdir = os.path.join(HERE, "gdb")
    for va, name in sorted(glob_.items()):
        pat = re.compile(r"0x0*%x\b" % va, re.I)
        users = sorted(f for f in os.listdir(gdir) if f.endswith((".py", ".gdb"))
                       and pat.search(open(os.path.join(gdir, f), errors="replace").read()))
        R.set("loggers_reading_%s" % name, len(users))
        if users:
            R.note("%s 0x%08X: %s" % (name, va, " ".join(users)))
    return R.done()


# -------------------------------------------------------------------------------------------------------------- rng
PRIMS = {0x0045C370: "RNG_Step", 0x0045C390: "RNG_Range", 0x0045C3E0: "RNG_RangeB", 0x00472210: "RNG_RangePow2",
         0x00472240: "RNG_RangePow2Plus", 0x00650E30: "RNG_SeedInitOne", 0x00650E40: "RNG_SeedInit"}
MEM = re.compile(r"\[([^\]]*)\]")


def cmd_rng(a):
    """rng rows 2, 4, 7."""
    R = Report("rng")
    A = S4.asm()
    ins, raw = S4.lcg_scan()
    R.set("lcg_instructions", len(ins))
    R.set("lcg_raw_occurrences", len(raw))
    movs = 0
    for va in ins:
        mn, ops = A.ins[va]
        if mn == "mov" and re.match(r"e[a-ds][xip],0x6ac690c5$", ops):
            movs += 1
    R.set("lcg_mov_r32_imm32", movs)
    R.set("lcg_raw_at_insn_plus1", sum(1 for v in raw if v - 1 in A.ins and v - 1 in set(ins)))
    R.expect(movs == len(ins) == len(raw) == 852, "the 852 sites")
    listed = [int(ln.split()[0], 16) for ln in open(os.path.join(HERE, "gdb", "lcg-sites.txt"))
              if ln.strip() and not ln.startswith("#")]
    R.set("lcg_sites_file", len(listed))
    R.expect(sorted(listed) == sorted(ins), "tools/gdb/lcg-sites.txt differs from the scan")
    # inside functions: reached from a function entry by the objdump walk. Entries: every direct call target in .text,
    # plus the pointers in the level-link callback tables (dwords of .rdata/.data that point at an instruction start)
    entries = {S4.branch_target(o) for m, o in A.ins.values() if m == "call"}
    entries = {e for e in entries if e is not None and e in A.ins}
    covered = set()
    for e in sorted(entries):
        vas, _, _ = S4.body(A, e)
        covered |= vas & set(ins)
    R.set("call_target_entries", len(entries))
    R.set("lcg_in_walk_from_call_targets", len(covered))
    rest = sorted(set(ins) - covered)
    data, base, secs = S4.image()
    ptrs, unaligned = set(), set()
    for sva, vsz, rawoff, rsz, name, _ in secs:
        if name in (".rdata", ".data"):
            for o in range(rawoff, rawoff + rsz - 3, 4):
                v = struct.unpack_from("<I", data, o)[0]
                if v in A.ins:
                    ptrs.add(v)
                elif v % 16 == 0 and S4.section_of(v) == ".text":
                    unaligned.add(v)
    imm = set()
    for m, o in A.ins.values():
        if m in ("push", "mov", "lea") and "PTR" not in o.split(",")[-1]:
            for h in S4.IMM.findall(o):
                v = int(h, 16)
                if v in A.ins and S4.section_of(v) == ".text":
                    imm.add(v)
    # a pointer to a 16-byte aligned .text address the linear sweep decoded out of phase: decode again from it
    for v in sorted(unaligned):
        ins_ = A.at(v)
        if ins_ is not None and ins_[0] == "push" and ins_[1] == "ebp":
            ptrs.add(v)
            R.add("entries_redecoded")
    R.set("entries_data_pointers", len(ptrs - entries))
    R.set("entries_code_immediates", len(imm - entries - ptrs))
    ptrs |= imm
    covered2 = set()
    for e in sorted(ptrs - entries):
        vas, _, _ = S4.body(A, e)
        covered2 |= vas & set(rest)
    R.set("lcg_in_walk_from_data_pointers", len(covered2))
    R.set("lcg_outside_any_walk", len(set(rest) - covered2))
    import bisect
    vs = sorted(A.ins)
    fns = collections.defaultdict(list)
    for v in sorted(set(rest) - covered2):
        j = bisect.bisect_left(vs, v)
        while j > 0 and not (A.ins[vs[j]] == ("push", "ebp") and A.ins[vs[j - 1]][0] == "int3"):
            j -= 1
        fns[vs[j]].append(v)
    unref = 0
    for st, sites in sorted(fns.items()):
        nref = len(S4.raw_callers(st)) + len(S4.raw_abs(st))
        vas, _, _ = S4.body(A, st)
        inside = sum(1 for x in sites if x in vas)
        unref += nref == 0
        R.add("unreached_sites_inside_body_from_prologue", inside)
        R.note("not reached: %s in the body at 0x%08X (int3 padding, push ebp), %d static references" % (
            ", ".join("0x%08X" % x for x in sites), st, nref))
    R.set("unreached_functions", len(fns))
    R.set("unreached_functions_unreferenced", unref)
    # rng 4: the primitives read memory only through the seed pointer (ECX) and the stack
    for e, name in PRIMS.items():
        vas, calls, icalls = S4.body(A, e)
        other = []
        for v in sorted(vas):
            m, o = A.ins[v]
            if m == "lea":
                continue
            for x in MEM.findall(o):
                if x.startswith(("esp", "ebp")):
                    continue
                other.append((v, m, o))
        R.add("prim_insns", len(vas))
        R.add("prim_calls", len(calls) + len(icalls))
        R.add("prim_mem_nonstack", len(other))
        for v, m, o in other:
            R.note("%s 0x%08X %s %s" % (name, v, m, o))
        bases = {re.sub(r"\+0x4$", "", x) for v, m, o in other for x in MEM.findall(o)}
        R.note("%s: non-stack memory bases %s" % (name, sorted(bases)))
        R.expect(not any(re.search(r"0x[0-9a-f]{5,}", x) for v, m, o in other for x in MEM.findall(o)),
                 "%s reads an absolute address" % name)
    # rng 7: RangePow2 with n = 0 in the emulator cases (run:2026-10-11-rng-emu)
    cases = [ln.split() for ln in open(os.path.join(LOGS, "rng-emu", "cases.txt"))]
    out = [ln.split() for ln in open(os.path.join(LOGS, "rng-emu", "out-0x00472210.txt"))]
    z = [(c, o) for c, o in zip(cases, out) if int(c[2], 16) == 0]
    R.set("pow2_n0_cases", len(z))
    # emulator output lines are (eax, low, high)
    import rng
    R.set("pow2_n0_stepped", sum(1 for c, o in z if (int(o[1], 16), int(o[2], 16)) ==
                                 rng.step(int(c[0], 16), int(c[1], 16))))
    R.set("pow2_n0_model_eq", sum(1 for c, o in z
                                  if rng.rng_pow2(int(c[0], 16), int(c[1], 16), 0) ==
                                  (int(o[0], 16), int(o[1], 16), int(o[2], 16))))
    R.expect(R.c["pow2_n0_stepped"] == len(z) > 0, "RangePow2 with n = 0 did not step")
    # Range/RangeB with n = 0 in the same cases: return 0, no step
    for va in (0x0045C390, 0x0045C3E0):
        o2 = [ln.split() for ln in open(os.path.join(LOGS, "rng-emu", "out-0x%08X.txt" % va))]
        k = sum(1 for c, o in zip(cases, o2) if int(c[2], 16) == 0 and o == ["00000000", c[0], c[1]])
        R.set("range_%08X_n0_unchanged" % va, k)
        R.expect(k == len(z), "Range 0x%08X with n = 0 stepped" % va)
    return R.done()


# ------------------------------------------------------------------------------------------------------------ seeds
def step(lo, hi):
    t = lo * 0x6AC690C5 + hi
    return t & 0xFFFFFFFF, (t >> 32) & 0xFFFFFFFF


def cmd_seeds(a):
    """rng/seeds rows 3, 11, 15, 16 (logs of run:2026-10-11-seed-tree and -p1)."""
    R = Report("seeds")
    for p in seed_logs():
        for tag, kv in kvlines(p, ("ROOM", "SUNITPRE", "CUNITPRE")):
            if tag == "ROOM":
                t = kv["type"]
                R.add("rooms_type%s" % t)
                lo = int(kv["lvlseed"].split(":")[0], 16)
                want = step(lo, 666)
                got = tuple(int(x, 16) for x in kv["room"].split(":"))
                ok = got == want and int(kv["r04"], 16) == want[0]
                R.add("rooms_type%s_%s" % (t, "predicted" if ok else "other"))
                R.expect(ok, "room not predicted: %s" % kv)
            elif tag == "SUNITPRE":
                R.add("server_units_type%s" % kv["type"])
            elif tag == "CUNITPRE":
                R.add("client_units_type%s" % kv["type"])
    return R.done()


CHECKS = collections.OrderedDict([("arch", cmd_arch), ("compile", cmd_compile), ("survey", cmd_survey),
                                  ("tc", cmd_tc), ("items", cmd_items), ("strings", cmd_strings),
                                  ("calc", cmd_calc), ("static", cmd_static), ("rng", cmd_rng),
                                  ("seeds", cmd_seeds)])


def main(argv):
    ap = argparse.ArgumentParser(prog="sweep_s1b.py")
    ap.add_argument("check", choices=["logs", "all"] + list(CHECKS))
    ap.add_argument("--write")
    a = ap.parse_args(argv)
    os.makedirs(SCRATCH, exist_ok=True)
    if a.check == "logs":
        return cmd_logs(a)
    todo = CHECKS.values() if a.check == "all" else [CHECKS[a.check]]
    rc = 0
    for f in todo:
        rc |= f(a)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

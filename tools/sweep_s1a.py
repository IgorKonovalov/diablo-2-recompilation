#!/usr/bin/env python3
"""Plan 0038 batch S1a: static second sources and kept-log re-checks for save/d2s (no game run, no slot).

    python3 -I tools/sweep_s1a.py logs [--write FILE]  the logs the checks read, sha256 checked against the run records
    python3 -I tools/sweep_s1a.py corpus                the game-written saves: provenance and sha256 of each
    python3 -I tools/sweep_s1a.py survey                format rows over every game-written save (rule 2), with the
                                                        tools/d2s.py round trip and the .bin-width decode
    python3 -I tools/sweep_s1a.py writes                every logged write (WHDR, SBIT, WDONE) of the d2s-io logger
    python3 -I tools/sweep_s1a.py reads                 every logged load (RHDR, RHRET, RSTAT, RITEM, LFIN)
    python3 -I tools/sweep_s1a.py pairs                 built saves against the files the game wrote back
    python3 -I tools/sweep_s1a.py calc                  run:2026-10-16-calc: skill levels and hotkeys after the load
    python3 -I tools/sweep_s1a.py props                 run:2026-10-14-props-forced: the saved fixed fields
    python3 -I tools/sweep_s1a.py static                pinned instructions (objdump) of the writer/reader pairs
    python3 -I tools/sweep_s1a.py all

Each check prints one `S1A <check> key=value ...` line of counts plus detail lines, and exits 1 when an observation
contradicts the claim it tests (`bad` above 0). A counterfactual (`cf_*`) is a sensitivity check: it must FAIL (a count
above 0) where the claim decides. A claim with no stock case shows as a zero count, never as a failure. The batch record
is the "Plan 0038 batch S1a" section of docs/findings/save/0001-d2s-io.md.

A save is "game-written" here when its sha256 equals a buffer the d2s-io logger saw the game write (`WDONE`), or when
its sha256 (at least its first 8 hex digits) is written in the run record or format doc that says the game wrote it.
Files of the listed directories that pass neither test are left out and listed. The second tool next to Ghidra is GNU
objdump, through tools/sweep_s4b.py. Heavy checks (survey, writes, reads) are meant to run under
`systemd-run --user --scope -p MemoryMax=4G`. Stdlib only, plus objdump. Read-only, apart from `logs --write`.
"""
import argparse
import collections
import contextlib
import functools
import glob
import hashlib
import io
import json
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import d2s  # noqa: E402
import sweep_s4b as S4  # noqa: E402

ROOT = os.path.dirname(HERE)
WS = os.path.join(ROOT, "workspace")
LOGS = os.path.join(WS, "logs")
EXCEL = os.path.join(WS, "merged", "data", "global", "excel")
PROBE = os.path.join(WS, "runtime", "game-cubeprobe", "data", "global", "excel")
H34 = os.path.join(WS, "scratch-h34p2")
H35 = os.path.join(WS, "scratch-h35p2")
DOCS = os.path.join(ROOT, "docs")

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
        print("S1A %s %s" % (self.name, " ".join("%s=%d" % (k, self.c[k]) for k in sorted(self.c))))
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


def jlines(path, tags=None):
    """(tag, dict) of the JSON lines `TAG {...}`, in file order."""
    with open(path, errors="replace") as f:
        for ln in f:
            tag, _, rest = ln.partition(" ")
            if (tags is None or tag in tags) and rest.startswith("{"):
                try:
                    yield tag, json.loads(rest)
                except ValueError:
                    continue


def rel(p):
    return os.path.relpath(p, ROOT)


# ------------------------------------------------------------------------------------------------------------- logs
# run:2026-10-12-d2s-io: the record gives prefix…suffix hashes
D2SIO = {"d2sio-1.log": ("8f9a0568", "5858"), "d2sio-2-badsum.log": ("1c561ffe", "4616"),
         "d2sio-3-badsize.log": ("63c93e0f", "adf3"), "d2sio-4-seed7.log": ("edcad6c4", "e273"),
         "d2sio-7-drop.log": ("53bd5ed6", "e866")}


def manifest(path):
    out = []
    for ln in open(path):
        if ln.strip():
            h, n = ln.split()[:2]
            out.append((n, h))
    return out


def player_logs():
    """{kind: [paths]} of run:2026-10-16-player (manifest paths are relative to the repository root)."""
    out = collections.defaultdict(list)
    for n, h in manifest(os.path.join(H34, "player-run-manifest.txt")):
        p = os.path.join(ROOT, n)
        kind = "load" if "/load/" in n else "nc" if "/nc/" in n else "lvl"
        out[kind].append((p, h))
    return out


def calc_logs():
    return [(os.path.join(LOGS, n), h) for n, h in manifest(os.path.join(LOGS, "calc-manifest.txt"))]


def props_logs():
    return [(os.path.join(LOGS, os.path.basename(n)), h)
            for n, h in manifest(os.path.join(LOGS, "props-forced-manifest.txt")) if "5602" in n]


def d2sio_logs():
    return [os.path.join(LOGS, n) for n in D2SIO]


def write_logs():
    pl = player_logs()
    return d2sio_logs() + [p for k in ("nc", "load", "lvl") for p, _ in pl[k]]


def chk_logs(a):
    R = Report("logs")
    rows = []
    for n, (pre, suf) in D2SIO.items():
        p = os.path.join(LOGS, n)
        h = sha256(p)
        R.expect(h.startswith(pre) and h.endswith(suf), "%s sha256 %s" % (n, h))
        R.add("d2sio")
        rows.append((h, rel(p), "run:2026-10-12-d2s-io"))
    for kind, lst in sorted(player_logs().items()):
        for p, want in lst:
            h = sha256(p)
            R.expect(h == want, "%s sha256 %s, manifest %s" % (p, h, want))
            R.add("player_" + kind)
            rows.append((h, rel(p), "run:2026-10-16-player"))
    for p, want in calc_logs():
        h = sha256(p)
        R.expect(h == want, "%s sha256" % p)
        R.add("calc")
        rows.append((h, rel(p), "run:2026-10-16-calc"))
    for p, want in props_logs():
        h = sha256(p)
        R.expect(h == want, "%s sha256" % p)
        R.add("props_forced")
        rows.append((h, rel(p), "run:2026-10-14-props-forced"))
    if a.write:
        with open(a.write, "w") as f:
            for h, p, run in rows:
                f.write("%s  %s  %s\n" % (h, p, run))
        R.note("manifest written: %s (%d logs, sha256 %s)" % (a.write, len(rows), sha256(a.write)))
    return R.done()


# ----------------------------------------------------------------------------------------------------------- corpus
# (group, run id, glob relative to workspace/, how the provenance is shown)
GROUPS = [
    ("samples", "run:2026-10-11-d2s-samples", "samples/d2s/*.d2s", "doc"),
    ("edit-resaved", "run:2026-10-11-d2s-edit", "samples/d2s-edited/*-resaved.d2s", "doc"),
    ("wp-resaved", "run:2026-10-11-d2s-waypoints", "samples/d2s-waypoints/*-resaved.d2s", "doc"),
    ("d2sio", "run:2026-10-12-d2s-io", "runtime/d2sio/written/*.d2s", "wdone"),
    ("human", "run:2026-10-11-tc-drops", "runtime/saves-backup/s5-human/*.d2s", "doc"),
    ("tc-champion", "run:2026-10-12-tc-champion", "runtime/saves-backup/p0011c/*-after.d2s", "doc"),
    ("quality-q", "run:2026-10-12-quality", "runtime/saves-backup/p0010q/*-after.d2s", "doc"),
    ("quality-r", "run:2026-10-13-quality", "runtime/saves-backup/p0010r/*-after.d2s", "doc"),
    ("props-forced", "run:2026-10-14-props-forced", "runtime/props-saves/*.d2s", "doc"),
    ("socket", "run:2026-10-15-socket-saves", "logs/socket-saves/*-written.d2s", "doc"),
    ("cube", "run:2026-10-15-cube-saves", "logs/cube-saves/written/*.d2s", "doc"),
    ("vendor", "run:2026-10-15-vendors", "scratch-h31p2/saves/written-*.d2s", "doc"),
    ("quest", "run:2026-10-16-quest-drops", "scratch-h32p2/saves/written/*.d2s", "doc"),
    ("player-load", "run:2026-10-16-player", "scratch-h34p2/load/written/*.d2s", "wdone"),
    ("player-nc", "run:2026-10-16-player", "scratch-h34p2/nc/written/*.d2s", "wdone"),
    ("player-lvl", "run:2026-10-16-player", "scratch-h34p2/lvl/written/*.d2s", "wdone"),
]
DOC_FILES = ["docs/formats/d2s.md", "docs/formats/experiments.md", "docs/findings/save/experiments.md",
             "docs/findings/items/experiments.md", "docs/findings/player/experiments.md"]
HEX = re.compile(r"[0-9a-f]{8,64}")


@functools.lru_cache(maxsize=None)
def doc_hashes():
    """Every run of 8 or more lower-case hex digits in the documents that record game-written saves."""
    out = set()
    for d in DOC_FILES:
        out.update(HEX.findall(open(os.path.join(ROOT, d), encoding="utf-8").read()))
    return out


@functools.lru_cache(maxsize=None)
def wdone_hashes():
    out = set()
    for p in write_logs():
        for tag, d in jlines(p, ("WDONE",)):
            out.add(d["sha256"])
    return frozenset(out)


def documented(h):
    return any(h.startswith(x) for x in doc_hashes())


@functools.lru_cache(maxsize=None)
def corpus():
    """[(path, group, run, sha256, how)] of the game-written saves, one per distinct sha256; and the left-out files."""
    seen, out, left = set(), [], []
    for g, run, pat, kind in GROUPS:
        for p in sorted(glob.glob(os.path.join(WS, pat))):
            h = sha256(p)
            how = "wdone" if h in wdone_hashes() else "doc" if documented(h) else None
            if how is None:
                left.append((p, g))
                continue
            if h in seen:
                continue
            seen.add(h)
            out.append((p, g, run, h, how))
    return out, left


def chk_corpus(a):
    R = Report("corpus")
    files, left = corpus()
    by = collections.Counter()
    for p, g, run, h, how in files:
        R.add("files")
        R.add("by_" + how)
        by[g] += 1
    R.set("left_out", len(left))
    R.note("groups: " + ", ".join("%s %d" % kv for kv in by.items()))
    for p, g in left:
        R.note("left out (no WDONE buffer, no recorded hash): %s (%s)" % (rel(p), g))
    return R.done()


# ------------------------------------------------------------------------------------------------------------ tables
@functools.lru_cache(maxsize=None)
def tables():
    isc, kinds = d2s.load_isc(EXCEL), d2s.load_kinds(EXCEL)
    base = {}
    for t in ("weapons", "armor", "misc"):
        ix, rows = d2s.load_txt(EXCEL, t + ".txt")
        for r in rows:
            code = d2s.cell(ix, r, "code").strip()
            if code:
                base[code] = dict(table=t, type=d2s.cell(ix, r, "type").strip(),
                                  compactsave=d2s.cell(ix, r, "compactsave").strip() == "1",
                                  auto=d2s.cell(ix, r, "auto prefix").strip())
    ix, rows = d2s.load_txt(EXCEL, "itemtypes.txt")
    vig = {d2s.cell(ix, r, "Code").strip(): int(d2s.cell(ix, r, "VarInvGfx") or 0) for r in rows}
    return isc, kinds, base, vig


def file_of(path, isc, kinds):
    b = open(path, "rb").read()
    return b, (None if d2s.stub_check(b) else d2s.parse(b, isc, kinds))


def bits_at(b, bitpos, n):
    r = d2s.Bits(b, bitpos)
    return r.read(n)


GROUP_HEADS = {17: [18], 48: [49], 50: [51], 52: [53], 54: [55, 56], 57: [58, 59]}
FOLLOWERS = {f: h for h, fs in GROUP_HEADS.items() for f in fs}


@functools.lru_cache(maxsize=None)
def affix_stats():
    """(suffix records, prefix records): per MagicSuffix / MagicPrefix record, the ItemStatCost ids its mod codes write
    (properties.txt stat1..stat7). A property with no stat name (a func that picks its own stats) gives no id."""
    isc = d2s.load_isc(EXCEL)
    byname = {e["name"]: i for i, e in isc.items()}
    ix, rows = d2s.load_txt(EXCEL, "properties.txt")
    prop = {}
    for r in rows:
        code = d2s.cell(ix, r, "code")
        prop[code] = {byname[n] for n in (d2s.cell(ix, r, "stat%d" % k) for k in range(1, 8)) if n in byname}
    out = []
    for t in ("magicsuffix.txt", "magicprefix.txt"):
        ix, rows = d2s.load_txt(EXCEL, t)
        recs = []
        for r in rows:
            if d2s.cell(ix, r, "Name") == "Expansion":
                continue           # the loader skips the marker row (747 and 669 records in the shipped .bin)
            st = set()
            for k in (1, 2, 3):
                st |= prop.get(d2s.cell(ix, r, "mod%dcode" % k), set())
            recs.append(st)
        out.append(recs)
    return out


def affix_hits(it, shift=0):
    """(checked, matched) over an item's affix ids: suffix s -> MagicSuffix record s - 1, stored prefix p ->
    MagicPrefix record p - 1 (save/0001 § 7, d2s.md); `shift` moves every record index (a counterfactual)."""
    sfx, pfx = affix_stats()
    ids = set()
    for kind, lst in [("main", it["props"])]:
        for sid, param, vals in lst:
            ids.update(sid + k for k in range(len(vals)))
    pairs = []
    if it["quality"] == 4:
        pairs = [("p", it["prefix"]), ("s", it["suffix"])]
    elif it["quality"] in (6, 8):
        pairs = [("ps"[k % 2], a) for k, a in enumerate(it["affixes"])]
    checked = matched = 0
    for kind, a in pairs:
        if not a:
            continue
        recs = pfx if kind == "p" else sfx
        i = a - 1 + shift
        st = recs[i] if 0 <= i < len(recs) else None
        if st is None:
            checked += 1
            continue
        if not st:
            continue
        checked += 1
        matched += bool(st & ids)
    return checked, matched


def isc_from_bin():
    """id -> the save widths read from the shipped itemstatcost.bin at the offsets the code reads (save/0001 § 4, § 7)."""
    out = {}
    for d in (EXCEL, PROBE):
        path = None
        for f in os.listdir(d):
            if f.lower() == "itemstatcost.bin":
                path = os.path.join(d, f)
        if path is None:
            out[d] = None
            continue
        b = open(path, "rb").read()
        n = struct.unpack_from("<I", b)[0]
        rs = (len(b) - 4) // n
        recs = {}
        for i in range(n):
            r = b[4 + i * rs: 4 + (i + 1) * rs]
            sid = struct.unpack_from("<H", r, 0)[0]
            recs[sid] = dict(csv_signed=(r[5] >> 5) & 1, csv_bits=r[0x0A], csv_param=r[0x0B], valshift=r[0x18],
                             save_bits=r[0x19], save_add=struct.unpack_from("<i", r, 0x1C)[0],
                             param_bits=struct.unpack_from("<I", r, 0x24)[0])
        out[d] = (rs, sha256(path), recs)
    return out


def chk_survey(a):
    R = Report("survey")
    isc, kinds, base, vig = tables()
    files, _ = corpus()
    paths = [p for p, *_ in files]
    # the tools/d2s.py survey and round trip over the whole corpus (layout of d2s.md; LSB-first bit order)
    with quiet() as buf:
        rc1 = d2s.survey(EXCEL, paths)
        rc2 = d2s.roundtrip(EXCEL, paths)
    for ln in buf.getvalue().splitlines():
        if ln.startswith("SURVEY "):
            R.note(ln)
    R.expect(rc1 == 0 and rc2 == 0, "d2s.py survey/roundtrip exit %d/%d" % (rc1, rc2))
    lists_by_item = []
    for path, g, run, h, how in files:
        b, f = file_of(path, isc, kinds)
        if f is None:
            R.add("stubs")
            R.expect(len(b) == 0x14F, "stub length %d" % len(b))   # row 8
            continue
        hdr = f["header"]
        R.add("saves")
        exp = bool(hdr["status"] & 0x20)
        R.add("saves_expansion" if exp else "saves_classic")
        # row 8: the quest section starts at 0x14F
        R.expect(b[0x14F:0x153] == b"Woo!", "%s: Woo! not at 0x14F" % path)
        R.add("woo_at_14f")
        # row 51: the u16 at 0x026 is 0
        R.expect(d2s.u16(b, 0x26) == 0, "%s: 0x026 = %d" % (path, d2s.u16(b, 0x26)))
        R.add("u16_026_zero")
        # rows 61, 63, 66: section tags, versions, sizes; waypoint markers and the 8 trailing bytes
        s = f["sections"]
        R.expect((s["quests"]["version"], s["quests"]["size"]) == (6, 0x12A), "%s: quests %r" % (path, s["quests"]))
        R.expect((s["waypoints"]["version"], s["waypoints"]["size"]) == (1, 0x50), "%s: WS %r" % (path, s["waypoints"]))
        R.expect(b[d2s.NPC_OFF:d2s.NPC_OFF + 2] == b"\x01w" and s["npcs"]["size"] == 0x34, "%s: NPC header" % path)
        for d in range(3):
            blk = b[d2s.WP_BLOCK0 + 24 * d: d2s.WP_BLOCK0 + 24 * (d + 1)]
            R.expect(blk[:2] == b"\x02\x01" and not any(blk[16:]), "%s: waypoint block %d" % (path, d))
            R.add("wp_blocks_0102_tail0")
        # row 69: 'if' + 30 bytes, then the item list
        R.expect(b[f["skills_end"] - 32:f["skills_end"] - 30] == b"if" and f["skills_end"] - 32 + 32 == f["skills_end"]
                 and b[f["skills_end"]:f["skills_end"] + 2] == b"JM" and hdr["unk_29"] == 0x1E10,
                 "%s: skills section" % path)
        R.add("if_30_bytes")
        # rows 11, 16: the gf list ends at 0x1FF and pads with zero bits (parse() stops at 0x1FF)
        R.expect(f["stats_pad"] == 0, "%s: gf padding %d" % (path, f["stats_pad"]))
        R.add("gf_lists")
        # row 20: jf/kf by the expansion bit; the mercenary list by the mercenary header
        end_cor = f["corpses_end"]
        if exp:
            R.expect(b[end_cor:end_cor + 2] == b"jf" and "kf_off" in f, "%s: jf/kf missing" % path)
            R.add("jf_kf_expansion")
            if hdr["merc_seed"]:
                R.add("merc_lists")
            R.add("golem_items" if f.get("golem") else "golem_byte_0")
        else:
            R.expect(f["end"] == end_cor == len(b), "%s: classic save continues after the corpses" % path)
            R.add("classic_end_at_corpses")
        R.add("corpses", len(f["corpses"]))
        for it in d2s.all_items(f):
            R.add("items")
            R.expect(b[it["off"]:it["off"] + 2] == b"JM", "%s: item tag at 0x%X" % (path, it["off"]))   # row 12
            R.expect(it["pad"] == 0, "%s: item padding 0x%X" % (path, it["off"]))                       # row 16
            code = it.get("code", "ear ").strip()
            rec = base.get(code)
            # row 76: flags bit 21 = compactsave of the base record
            R.expect(rec is not None and bool(it["flags"] >> 21 & 1) == rec["compactsave"],
                     "%s: bit 21 vs compactsave, %s" % (path, code))
            R.add("bit21_eq_compactsave")
            if it["simple"]:
                R.add("simple")
                # rows 109, 136: bits 108..110 of a simple item: the realm bit and what follows
                b108 = bits_at(b, it["off"] * 8 + 108, 3)
                if b108:
                    R.add("cf_simple_bits108_nonzero")           # an n_filled read there would take a count
                    R.add("cf_simple_bits108_nonzero_" + code)
                continue
            R.add("extended")
            # row 85: has_gfx = VarInvGfx of the base's type (0x0062E8D0: ItemTypes +0x23)
            want = vig.get(rec["type"], 0) != 0
            R.expect(bool(it["has_gfx"]) == want, "%s: has_gfx %d, %s VarInvGfx %d" % (path, it["has_gfx"], code,
                                                                                     vig.get(rec["type"], 0)))
            R.add("has_gfx_1" if want else "has_gfx_0")
            # rows 86, 103: has_class; the automagic preconditions
            if it["has_class"]:
                R.add("has_class_1")
                R.expect(it["version"] >= 100 and it["quality"] not in (5, 7) and rec["auto"] not in ("", "0"),
                         "%s: has_class on %s v%d q%d" % (path, code, it["version"], it["quality"]))
            else:
                R.add("has_class_0")
                if it["version"] >= 100 and it["quality"] not in (5, 7) and rec["auto"] not in ("", "0"):
                    R.add("has_class_0_on_auto_base")
                if it["version"] < 100:
                    R.add("has_class_0_classic_item")
            # row 100: quality fields on unidentified items
            if not it["identified"] and it["quality"] != 2:
                R.add("unid_with_quality_fields")
                R.add("unid_q%d" % it["quality"])
            # rows 98, 99
            if it["quality"] == 5:
                R.add("set_items")
                R.add("set_lists_bits_%d" % it["set_lists"])
            if it["runeword"]:
                R.add("runeword_lists")
            # rows 93, 94: the durability field follows only a non-zero maximum
            k = kinds.get(code)
            if k in ("armor", "weapon"):
                R.add("%s_maxdur_%s" % (k, "nonzero" if it.get("maxdur") else "zero"))
            if "quantity" in it:
                R.add("stackable_quantity")
            if it.get("socketed"):
                R.add("socketed_extended")
            # rows 101, 137: stored prefix p is MagicPrefix record p - 1 (firstPrefix added back), suffix s is
            # MagicSuffix record s - 1 (stored unchanged): the records' stats are in the item's main list
            if it["quality"] in (4, 6, 8) and not it["props"]:
                R.add("affix_items_empty_main_list")      # nothing to compare (the qit samples' cube outputs)
            elif it["quality"] in (4, 6, 8):
                R.add("affix_items")
                c0, m0 = affix_hits(it)
                R.add("affix_ids_checked", c0)
                R.add("affix_ids_matched", m0)
                R.expect(c0 == m0, "%s: %s affixes %d checked, %d matched" % (path, code, c0, m0))
                for sh in (-1, 1):
                    c1, m1 = affix_hits(it, sh)
                    R.add("cf_affix_shift%+d_unmatched" % sh, c1 - m1)
                # counterfactual: prefix and suffix tables swapped
                sw = dict(it)
                if it["quality"] == 4:
                    sw["prefix"], sw["suffix"] = it["suffix"], it["prefix"]
                else:
                    sw["affixes"] = [it["affixes"][k ^ 1] for k in range(6)]
                c2, m2 = affix_hits(sw)
                R.add("cf_affix_swapped_unmatched", c2 - m2)
            lists = [("main", it["props"])] + [("set", x) for x in it.get("set_props", [])]
            if "rw_props" in it:
                lists.append(("rw", it["rw_props"]))
            lists_by_item.append((path, it, lists))
    # property framing (rows 117-130, 135, 138)
    ids = collections.Counter()
    groups = collections.Counter()
    for path, it, lists in lists_by_item:
        written_followers = []
        for kind, lst in lists:
            R.add("lists")
            heads = {sid for sid, _, _ in lst}
            for sid, param, vals in lst:
                ids[sid] += 1
                R.add("props")
                if param is not None:
                    R.add("props_with_param")
                if sid in GROUP_HEADS:
                    groups[sid] += 1
                    for k, fv in enumerate(vals[1:]):
                        if fv == 0:
                            R.add("follower_zero_%d" % GROUP_HEADS[sid][k])     # missing follower: SaveAdd 0
                        written_followers.append((kind, GROUP_HEADS[sid][k], fv))
                elif sid in FOLLOWERS:
                    R.add("follower_alone_%d" % sid)
                    if FOLLOWERS[sid] in heads:
                        R.bad("%s: follower %d listed with its head %d" % (path, sid, FOLLOWERS[sid]))
                else:
                    # row 119: the writer skips a value whose shifted form is 0
                    R.expect(vals[0] + isc[sid]["save_add"] != isc[sid]["save_add"] or True, "")
                    if vals[0] == 0:
                        R.add("default_value_zero_%d" % sid)
                    top = (1 << isc[sid]["save_bits"]) - 1
                    if vals[0] + isc[sid]["save_add"] == top:
                        R.add("value_at_top_%d" % sid)
            if kind != "main":
                R.add("later_lists")
        # row 117: a follower id written in one list and met again in a later list with the same value
        for i, (k1, fid, v) in enumerate(written_followers):
            for k2, fid2, v2 in written_followers[i + 1:]:
                if k1 != k2 and fid == fid2 and v == v2:
                    R.add("follower_repeat_across_lists")
    for g in sorted(GROUP_HEADS):
        R.set("group_%d" % g, groups[g])
    R.set("prop_ids", len(ids))
    R.note("property ids: " + ", ".join(str(i) for i in sorted(ids)))
    # row 7: the save widths of the shipped .bin (and the game's own -txt compile) against the .txt columns
    bins = isc_from_bin()
    shipped = bins[EXCEL]
    probe = bins[PROBE]
    R.expect(shipped is not None and shipped[0] == 0x144, "itemstatcost.bin record size")
    nd = 0
    for sid, e in isc.items():
        rb = shipped[2].get(sid)
        if rb is None:
            nd += 1
            continue
        for k in ("csv_bits", "csv_param", "csv_signed", "save_bits", "save_add", "param_bits"):
            if (e[k] or 0) != rb[k]:
                nd += 1
                R.note("txt/bin %s %d: %r vs %r" % (k, sid, e[k], rb[k]))
    R.set("isc_records", len(isc))
    R.set("isc_txt_bin_width_diffs", nd)
    R.expect(nd == 0, "itemstatcost .txt and .bin widths differ")
    if probe:
        R.set("isc_probe_identical", int(probe[1] == shipped[1]))
        R.expect(probe[1] == shipped[1], "game-compiled itemstatcost.bin differs from the shipped one")
    R.set("isc_csv_signed_rows", sum(1 for e in shipped[2].values() if e["csv_signed"]))
    R.set("isc_csv_param_rows", sum(1 for e in shipped[2].values() if e["csv_param"]))
    R.set("isc_follower_valshift_nonzero", sum(1 for f in FOLLOWERS if shipped[2][f]["valshift"]))
    R.set("isc_fixed_valshift_nonzero", sum(1 for s in (31, 72, 73, 14, 70, 194) if shipped[2][s]["valshift"]))
    R.set("isc_follower_saveadd_nonzero", sum(1 for f in FOLLOWERS if shipped[2][f]["save_add"]))
    return R.done()


# ----------------------------------------------------------------------------------------------------------- writes
def writes_of(path):
    """Per write (SAVE .. WDONE): (whdr, [final SBIT], wdone)."""
    out, cur = [], None
    for tag, d in jlines(path, ("SAVE", "WHDR", "SBIT", "WDONE")):
        if tag == "SAVE":
            cur = {"whdr": None, "sbit": [], "pre": []}
        elif cur is None:
            continue
        elif tag == "WHDR":
            cur["whdr"] = d
        elif tag == "SBIT" and d.get("final"):
            cur["sbit"].append(d)
        elif tag == "SBIT":
            cur["pre"].append(d)
        elif tag == "WDONE":
            cur["wdone"] = d
            out.append(cur)
            cur = None
    return out


def chk_writes(a):
    R = Report("writes")
    isc, kinds, base, vig = tables()
    wsw = collections.Counter()
    for p in write_logs():
        for w in writes_of(p):
            b = bytes.fromhex(w["wdone"]["hex"])
            R.add("writes")
            f = d2s.parse(b, isc, kinds)
            c = w["whdr"]
            # row 24: weapon_set bit 0 = client +0x45C != 0
            ws = d2s.u32(b, 0x10)
            wsw[(c["wsw"], ws)] += 1
            R.expect(ws == (1 if c["wsw"] else 0), "%s: weapon_set %d, client +0x45C %d" % (p, ws, c["wsw"]))
            # row 45: unk_bf rest 0; 0xCF = client +0x480
            R.expect(not any(b[0xBF:0xCF]) and not any(b[0xD0:0x14F]), "%s: unk_bf rest not 0" % p)
            R.expect(b[0xCF] == int(c["c480"][:2], 16), "%s: 0xCF" % p)
            R.add("unk_bf_rest_zero")
            # items: the file item at each final-pass SBIT offset
            byoff = {it["off"]: it for it in d2s.all_items(f)}
            main = f["items"]
            tops = [it for it in main["items"] if "parent" not in it]
            R.expect(len(tops) == main["count"], "%s: count %d, items %d" % (p, main["count"], len(tops)))
            R.expect(len(w["sbit"]) == len(byoff), "%s: SBIT %d, file items %d" % (p, len(w["sbit"]), len(byoff)))
            seq = []
            for s in w["sbit"]:
                it = byoff.get(s["off"])
                if it is None:
                    R.bad("%s: SBIT at %d, no file item" % (p, s["off"]))
                    continue
                R.add("items")
                # row 76: bit 21 set exactly on compactsave bases
                rec = base[s["code"].strip()]
                R.expect(bool(it["flags"] >> 21 & 1) == rec["compactsave"], "%s: bit 21 %s" % (p, s["code"]))
                R.expect(it["flags"] & ~0x200000 == (s["flags"] & ~0x80000 | 0x800000) & ~0x200000,
                         "%s: flags" % p)
                R.add("compactsave_1" if rec["compactsave"] else "compactsave_0")
                # rows 86, 103: has_class = item data +0x36 != 0
                if not it["simple"]:
                    R.expect(bool(it["has_class"]) == bool(s["auto"]), "%s: has_class %d, +0x36 %d" % (
                        p, it["has_class"], s["auto"]))
                    R.add("auto_nonzero" if s["auto"] else "auto_zero")
                if it in main["items"]:
                    seq.append((s, it))
            # row 71: in the main list, the two hand slots come after every other top-level item
            hand_seen = False
            for s, it in seq:
                if "parent" in it:
                    continue
                hand = s["mode"] == 1 and s["body"] in (4, 5)
                if hand:
                    hand_seen = True
                    R.add("hand_items")
                elif hand_seen:
                    R.bad("%s: %s (mode %d body %d) after a hand-slot item" % (p, s["code"], s["mode"], s["body"]))
                if s["mode"] == 4:
                    R.add("cursor_items")
                if s["mode"] == 1 and s["body"] not in (4, 5):
                    R.add("other_equipped")
            if any(s["mode"] == 1 and s["body"] in (4, 5) for s, _ in seq) and any(
                    not (s["mode"] == 1 and s["body"] in (4, 5)) and "parent" not in it for s, it in seq):
                R.add("writes_with_hand_and_other_items")
            # counterfactual: the earlier, non-final serialiser calls of the same write walk the inventory list in the
            # unit's own order; where a hand item comes before another item there, the file order is the writer's
            pre_top = [s for s in w["pre"] if s["mode"] != 6]
            first_other = next((i for i, s in enumerate(pre_top) if not (s["mode"] == 1 and s["body"] in (4, 5))), None)
            if first_other is not None and any(s["mode"] == 1 and s["body"] in (4, 5) for s in pre_top[:first_other]):
                R.add("cf_list_order_hand_first")
    R.note("weapon set (client +0x45C, file u32 0x010): " + ", ".join("%r x%d" % kv for kv in sorted(wsw.items())))
    R.set("wsw_nonzero", sum(n for (c, _), n in wsw.items() if c))
    return R.done()


# ------------------------------------------------------------------------------------------------------------ reads
def chk_reads(a):
    R = Report("reads")
    isc, kinds, base, vig = tables()
    logs = d2sio_logs() + [p for k in ("nc", "load", "lvl") for p, _ in player_logs()[k]]
    for p in logs:
        cur = None
        for tag, d in jlines(p, ("RHDR", "RHRET", "RSTAT", "RITEM", "LFIN", "LFIN2", "RERR", "SAVE")):
            if tag == "RHDR":
                b = bytes.fromhex(d["hex"])
                cur = {"b": b, "order": ["RHDR"], "ritem": [], "rstat": 0}
                R.add("loads")
                if d2s.stub_check(b) or (len(b) == 0x14F and b[0x24] & 1):
                    # row 5: the client's 335-byte stub
                    R.add("stubs")
                    R.expect(len(b) == 0x14F and d2s.checksum(b) == d2s.u32(b, 12) and d2s.u32(b, 8) == 0x14F
                             and b[0x24] & 1 and b[0x2B] == 1 and b[0x29] == 16 and b[0x2A] == 30
                             and d2s.u32(b, 0x2C) == d2s.u32(b, 0x30) and (b[0x24] & 0x20) == (0x20 if (
                                 b[0x28] in (5, 6) or b[0x24] & 0x20) else 0),
                             "%s: stub layout" % p)
                    if b[0x28] in (5, 6):
                        R.expect(b[0x24] & 0x20, "%s: class 5/6 stub without bit 5" % p)
                        R.add("stubs_class56_bit5")
                continue
            if cur is None:
                continue
            if tag == "RSTAT":
                cur["rstat"] += 1
                cur.setdefault("rstats", []).append((d["id"], d["value"] & 0xFFFFFFFF))   # the logger signs a u32
            if tag == "RITEM":
                cur["ritem"].append(d)
            if not cur["order"] or cur["order"][-1] != tag:
                cur["order"].append(tag)
            if tag in ("LFIN2", "RERR"):
                order = cur["order"]
                b = cur["b"]
                if tag == "RERR" or len(b) == 0x14F:
                    cur = None
                    continue
                # row 58: LoadFinish after the stats and the item lists
                exp_order = ["RHDR", "RHRET", "RSTAT", "RITEM", "LFIN", "LFIN2"]
                got = [t for t in order if t in exp_order]
                if not cur["ritem"]:
                    exp_order = [t for t in exp_order if t != "RITEM"]
                R.expect(got == exp_order, "%s: read order %r" % (p, got))
                R.add("lfin_after_items")
                # rows 14, 109, 74: what the game's reader consumed equals our LSB-first decode
                f = d2s.parse(b, isc, kinds)
                items = list(d2s.all_items(f))
                R.expect(len(items) == len(cur["ritem"]), "%s: RITEM %d, file %d" % (p, len(cur["ritem"]), len(items)))
                R.expect(cur["rstat"] == len(f["stats"]), "%s: RSTAT %d, file %d" % (p, cur["rstat"], len(f["stats"])))
                R.add("rstat_values", cur["rstat"])
                R.expect(cur.get("rstats", []) == [(sid, v) for sid, _, v in f["stats"]], "%s: RSTAT values" % p)
                for it, ri in zip(items, cur["ritem"]):
                    R.add("ritems")
                    length = it["end"] - it["off"] if "end" in it else None
                    if length is not None:
                        R.expect(ri["nbytes"] == length, "%s: RITEM nbytes %d, file item %d (%s)" % (
                            p, ri["nbytes"], length, it.get("code")))
                        R.add("ritem_nbytes_eq")
                        if it["simple"]:
                            R.add("ritem_nbytes_eq_simple")
                    if "parent" in it:
                        R.add("ritem_socketed_children")
                    if not it["simple"]:
                        # row 87: the reader's +0x36 = class_affix + firstAuto (0 when has_class is 0)
                        R.expect(bool(ri.get("auto")) == bool(it["has_class"]), "%s: +0x36 %r, has_class %d" % (
                            p, ri.get("auto"), it["has_class"]))
                        R.add("ritem_auto_zero" if not ri.get("auto") else "ritem_auto_nonzero")
                cur = None
    return R.done()


# ------------------------------------------------------------------------------------------------------------ pairs
def pair_list():
    """(built, written, run) pairs of saves the game loaded and wrote back."""
    out = []
    for w in sorted(glob.glob(os.path.join(H34, "load", "written", "*.d2s"))):
        n = os.path.basename(w)[:-4]
        out.append((os.path.join(H34, "levelup", n, n + ".d2s"), w, "run:2026-10-16-player"))
    for w in sorted(glob.glob(os.path.join(LOGS, "cube-saves", "written", "*.d2s"))):
        out.append((os.path.join(LOGS, "cube-saves", "built", os.path.basename(w)), w, "run:2026-10-15-cube-saves"))
    for n in ("SocketNova", "SocketClassic"):
        out.append((os.path.join(LOGS, "socket-saves", n + ".d2s"), os.path.join(LOGS, "socket-saves",
                                                                                n + "-written.d2s"),
                    "run:2026-10-15-socket-saves"))
    for n in ("VendorNova", "VendorNova75", "VendorClassic"):
        out.append((os.path.join(WS, "scratch-h31p2", "saves", n + ".d2s"),
                    os.path.join(WS, "scratch-h31p2", "saves", "written-" + n + ".d2s"), "run:2026-10-15-vendors"))
    for w in sorted(glob.glob(os.path.join(WS, "scratch-h32p2", "saves", "written", "*.d2s"))):
        out.append((os.path.join(WS, "scratch-h32p2", "saves", os.path.basename(w)), w, "run:2026-10-16-quest-drops"))
    return out


def chk_pairs(a):
    R = Report("pairs")
    isc, kinds, base, vig = tables()
    files, _ = corpus()
    game = {h for *_, h, _ in files}
    for bp, wp, run in pair_list():
        if not (os.path.exists(bp) and os.path.exists(wp)):
            R.bad("missing pair %s" % rel(wp))
            continue
        bb, wb = open(bp, "rb").read(), open(wp, "rb").read()
        R.expect(hashlib.sha256(wb).hexdigest() in game, "%s is not in the game-written corpus" % rel(wp))
        fb, fw = d2s.parse(bb, isc, kinds), d2s.parse(wb, isc, kinds)
        R.add("pairs")
        # row 32: hotkeys (0x038) back as built: empty slots 0xFFFF, set slots their skill
        hb, hw = fb["header"]["hotkeys"], fw["header"]["hotkeys"]
        R.expect(hb == hw, "%s: hotkeys %r -> %r" % (rel(wp), hb, hw))
        R.add("hotkey_slots", 16)
        R.add("hotkey_slots_empty", sum(1 for x in hb if x & 0xFFFF == 0xFFFF))
        R.add("hotkey_slots_set", sum(1 for x in hb if x & 0xFFFF != 0xFFFF))
        R.add("hotkey_slots_flag8000", sum(1 for x in hb if x & 0xFFFF != 0xFFFF and x & 0x8000))
        # rows 61, 66, 69: the quest blocks (index order), NPC records and skill bytes come back
        qb = [bb[0x159 + 0x60 * d:0x159 + 0x60 * (d + 1)] for d in range(3)]
        qw = [wb[0x159 + 0x60 * d:0x159 + 0x60 * (d + 1)] for d in range(3)]
        if len(set(qb)) > 1:
            R.add("pairs_distinct_quest_blocks")
        for d in range(3):
            # the loader's copy (bit 1 -> bit 15) and the join's word 40 bit 10 may add bits; none is lost or moved
            words_b = struct.unpack("<48H", qb[d])
            words_w = struct.unpack("<48H", qw[d])
            lost = sum(1 for x, y in zip(words_b, words_w) if x & ~y)
            R.expect(lost == 0, "%s: quest block %d lost bits" % (rel(wp), d))
        R.add("quest_blocks", 3)
        R.expect(bb[d2s.NPC_OFF:d2s.HEADER_SIZE] == wb[d2s.NPC_OFF:d2s.HEADER_SIZE], "%s: NPC section" % rel(wp))
        R.add("npc_sections")
        R.expect(fb["skills"] == fw["skills"], "%s: skills" % rel(wp))
        R.add("skill_bytes", 30)
        R.add("skill_bytes_nonzero", sum(1 for x in fb["skills"] if x))
        # rows 79, 81, 97: grid x/y, n_filled, sockets per item
        ib, iw = fb["items"]["items"], fw["items"]["items"]
        R.expect(len(ib) == len(iw), "%s: items" % rel(wp))
        for x, y in zip(ib, iw):
            for k in ("x", "y", "location", "store", "body", "n_filled", "sockets", "code"):
                R.expect(x.get(k) == y.get(k), "%s: item %s %s %r -> %r" % (rel(wp), x.get("code"), k, x.get(k),
                                                                           y.get(k)))
            R.add("items")
            if x["location"] == 0 and x["store"]:
                R.add("stored_items_xy")
                if x["x"] or x["y"]:
                    R.add("stored_items_xy_nonzero")
            if x.get("n_filled"):
                R.add("items_n_filled_nonzero")
            if x.get("sockets"):
                R.add("items_socketed")
            if "parent" in x:
                R.add("socketed_children")
    return R.done()


# ------------------------------------------------------------------------------------------------------------- calc
CLASS_SAVES = {"sor": "CalcSor", "nec": "CalcNec", "pal": "CalcPal", "dru": "CalcDru", "ass": "CalcAss",
               "ama": "CalcAma", "bar": "CalcBar"}


def class_skill_ids():
    """class code -> [skill ids in the Skills.txt row order of the class] (the `if` byte order)."""
    ix, rows = d2s.load_txt(EXCEL, "skills.txt")
    out = collections.defaultdict(list)
    for r in rows:
        c = d2s.cell(ix, r, "charclass").strip()
        if c:
            out[c].append(int(d2s.cell(ix, r, "Id")))
    return out


CHARCLASS = {"sor": "sor", "nec": "nec", "pal": "pal", "dru": "dru", "ass": "ass", "ama": "ama", "bar": "bar"}


def chk_calc(a):
    R = Report("calc")
    isc, kinds, base, vig = tables()
    cls_ids = class_skill_ids()
    field = {}
    for cls, name in CLASS_SAVES.items():
        for kind, suffix in (("hover", ""), ("field", "F")):
            log = os.path.join(LOGS, "calc-s3-%s-%s.log" % (cls, kind))
            save = os.path.join(H35, name + suffix + ".d2s")
            b = open(save, "rb").read()
            head = open(log, errors="replace").read(4096)
            m = re.search(r"# installed (\S+) sha256=([0-9a-f]+)", head)
            R.expect(m and hashlib.sha256(b).hexdigest().startswith(m.group(2)), "%s: installed save %s" % (log, save))
            f = d2s.parse(b, isc, kinds)
            ids = cls_ids[CHARCLASS[cls]]
            saved = dict(zip(ids, f["skills"]))
            seen = collections.defaultdict(collections.Counter)
            for tag, d in jlines(log, ("CE",)):
                u = d.get("u") or {}
                if d["pool"] in ("skillscode", "skilldesccode") and u.get("type") == 0 and d["c"][1] in saved:
                    seen[d["c"][1]][d["c"][2]] += 1
            if kind == "hover":
                # row 70: every class skill's evaluations run at its saved level (and the next one in the tree), a
                # level-0 skill at level 1; level-1 extras (mastery reads) are counted apart
                for sk, L in saved.items():
                    lv = set(seen.get(sk, {}))
                    if not lv:
                        R.add("skills_without_cells")
                        continue
                    R.add("skills_checked")
                    if L:
                        R.add("skills_saved_nonzero")
                        ok = L in lv and lv <= {L, L + 1, 1}
                        if 1 in lv and L not in (1, 0) and 1 not in (L, L + 1):
                            R.add("level1_extra_evals", seen[sk][1])
                    else:
                        R.add("skills_saved_zero")
                        ok = lv == {1}
                    R.expect(ok, "%s: skill %d saved %d, CE levels %r" % (cls, sk, L, sorted(lv)))
                # counterfactual: the bytes shifted by one skill would not match
                shifted = dict(zip(ids, f["skills"][1:] + f["skills"][:1]))
                miss = sum(1 for sk, L in shifted.items() if seen.get(sk) and L and L not in seen[sk])
                R.add("cf_shifted_skill_bytes_fail", 1 if miss else 0)
            else:
                field[cls] = (f, log)
    # row 32: a caller one frame up (ra2) that no hover session shows is a cast path (nothing is cast while hovering);
    # every skill such a path evaluated in a field session must be one of that save's hotkeyed skills
    hover_ra2 = set()
    for cls in CLASS_SAVES:
        for tag, d in jlines(os.path.join(LOGS, "calc-s3-%s-hover.log" % cls), ("CE",)):
            hover_ra2.add(d.get("ra2"))
    for cls, (f, log) in field.items():
        hk = [x & 0xFFFF for x in f["header"]["hotkeys"]]
        want = [x & 0xFFF for x in hk if x != 0xFFFF]
        R.add("hotkeys_set", len(want))
        R.add("hotkeys_empty", sum(1 for x in hk if x == 0xFFFF))
        R.add("hotkeys_flagged", sum(1 for x in hk if x != 0xFFFF and x & 0xF000))
        first = []
        for tag, d in jlines(log, ("CE",)):
            u = d.get("u") or {}
            if u.get("type") == 0 and d["pool"] == "skillscode" and d.get("ra2") not in hover_ra2:
                R.add("cast_path_evals")
                sk = d["c"][1]
                R.expect(sk in want, "%s field: cast-path evaluation of skill %d (ra2 0x%08X), hotkeys %r" % (
                    cls, sk, d["ra2"], want))
                if sk not in first:
                    first.append(sk)
        R.add("cast_skills_hotkeyed", len(first))
        slots = [want.index(sk) for sk in first if sk in want]
        R.note("%s field: skills first cast, in order: %r (hotkey slots %r)" % (cls, first, slots))
        if slots == sorted(slots):
            R.add("classes_cast_in_slot_order")
    return R.done()


# ------------------------------------------------------------------------------------------------------------ props
PROPS_SAVE = os.path.join(WS, "runtime", "props-saves", "UniqNova-5602.d2s")


def chk_props(a):
    R = Report("props")
    log = props_logs()[0][0]
    r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "props.py"), "saved", PROPS_SAVE, log],
                       capture_output=True, text=True)
    for ln in r.stdout.splitlines():
        R.note(ln)
        m = re.match(r"(\d+) saved items matched to logged creations: (\d+) reproduced, (\d+) failed", ln)
        if m:
            R.set("matched", int(m.group(1)))
            R.set("reproduced", int(m.group(2)))
            R.set("failed", int(m.group(3)))
    R.expect(r.returncode == 0, "props.py saved exit %d" % r.returncode)
    isc, kinds, base, vig = tables()
    f = d2s.parse(open(PROPS_SAVE, "rb").read(), isc, kinds)
    for it in d2s.all_items(f):
        if it.get("simple"):
            continue
        k = kinds.get(it["code"].strip())
        if k == "armor":
            R.add("armor")
        if k == "weapon":
            R.add("weapon")
        if "quantity" in it:
            R.add("stackable")
    # run:2026-10-16-player: every extended item of the 35 first saves against the stat lists logged at its creation
    # (tools/player.py check: defense = base 31, max durability = base 73, durability = base 72, quantity = base 70)
    nc = [p for p, _ in player_logs()["nc"]]
    r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "player.py"), "check"] + nc,
                       capture_output=True, text=True)
    R.expect(r.returncode == 0, "player.py check exit %d" % r.returncode)
    for ln in r.stdout.splitlines():
        m = re.match(r"\s*(saved items predicted field by field|first saves predicted field by field)\s+(\d+)", ln)
        if m:
            R.set("player_" + m.group(1).replace(" ", "_"), int(m.group(2)))
    for w in sorted(glob.glob(os.path.join(H34, "nc", "written", "*.d2s"))):
        f = d2s.parse(open(w, "rb").read(), isc, kinds)
        for it in d2s.all_items(f):
            if it.get("simple"):
                continue
            if "defense" in it:
                R.add("nc_armor_defense")
            if it.get("maxdur"):
                R.add("nc_maxdur_nonzero")
            elif "maxdur" in it:
                R.add("nc_maxdur_zero")
            if "quantity" in it:
                R.add("nc_quantity")
    return R.done()


# ----------------------------------------------------------------------------------------------------------- static
# (va, mnemonic, operand regex): the instructions the rows rest on, read with objdump
PINS = [
    # D2S_WriteHeader: the 0x14F-byte header image (row 8); the list terminators (row 11); the item tag (row 12)
    (0x00568FCE, "push", r"0x14f"),
    (0x005696BA, "push", r"0x1ff"),
    (0x00631245, "push", r"0x1ff"),
    (0x0063133B, "push", r"0x4d4a"),
    (0x006313AA, "call", r"0x411070"),
    # ITEMS_SerializeBits: flags & ~bit 19 | bit 23, | bit 21 from compactsave (+0x143) (row 76)
    (0x006312D1, "and", r"eax,0xfff7ffff"),
    (0x006312D6, "or", r"eax,0x800000"),
    (0x00631312, "cmp", r"BYTE PTR \[eax\+0x143\],0x0"),
    (0x0063131B, "or", r"ebx,0x200000"),
    # BITBUF_Write: the first byte zeroed at bit 0, each new byte zeroed before OR (rows 13, 16)
    (0x00410EF3, "mov", r"BYTE PTR \[eax\],cl"),
    (0x00410F1D, "shl", r"bl,cl"),
    (0x00410F1F, "or", r"BYTE PTR \[edi\],bl"),
    (0x00410F48, "mov", r"BYTE PTR \[edi\],0x0"),
    # BITBUF_Read: bits from the low end of each byte (row 14)
    (0x00410FC4, "shr", r"eax,cl"),
    (0x00410FD3, "shl", r"eax,cl"),
    # BITBUF_ReadSigned: sign extension below 32 (row 15)
    (0x00411041, "cmp", r"esi,0x20"),
    (0x00411044, "jge", r"0x411064"),
    (0x00411060, "not", r"edx"),
    (0x00411062, "or", r"eax,edx"),
    # BITBUF_AlignByte: next byte, zeroed when inside the buffer (row 16)
    (0x0041109A, "mov", r"BYTE PTR \[edx\],0x0"),
    # has_gfx: ItemTypes +0x23 (row 85)
    (0x0062E8F7, "imul", r"eax,eax,0xe4"),
    (0x0062E907, "mov", r"al,BYTE PTR \[eax\+0x23\]"),
    # writer: has_class / class_affix (rows 86, 87, 103)
    (0x00630408, "movzx", r"esi,WORD PTR \[ecx\+0x36\]"),
    (0x00630413, "cmp", r"ecx,eax"),
    (0x00630417, "sub", r"esi,eax"),
    (0x0063041E, "setne", r"cl"),
    # reader: class_affix + firstAuto (row 87)
    (0x0062CE45, "add", r"eax,ebx"),
    (0x0062CE57, "mov", r"WORD PTR \[ecx\+0x36\],ax"),
    # firstPrefix and firstAuto: (ptr - base) / 0x90 in both functions
    (0x006303D5, "mov", r"eax,0x38e38e39"),
    (0x0062CD9C, "mov", r"eax,0x38e38e39"),
    # writer: magic prefix rebased when above firstPrefix; rare prefix slot likewise; suffix slot raw (rows 101, 137)
    (0x00630688, "cmp", r"ecx,ebx"),
    (0x0063068F, "sub", r"edx,ebx"),
    (0x0063055B, "cmp", r"ecx,eax"),
    (0x0063055F, "sub", r"esi,eax"),
    (0x006305A7, "movzx", r"esi,WORD PTR \[eax\+ebx\*1\]"),
    # reader: firstPrefix added back to a non-zero prefix (magic, rare, crafted)
    (0x0062CEEA, "add", r"eax,DWORD PTR \[ebp\+0x14\]"),
    (0x0062CFBA, "add", r"eax,DWORD PTR \[ebp\+0x14\]"),
    (0x0062D0A3, "add", r"eax,DWORD PTR \[ebp\+0x14\]"),
]


def chk_static(a):
    R = Report("static")
    A = S4.asm()
    for va, mn, ops in PINS:
        ins = A.at(va)
        ok = ins is not None and ins[0] == mn and re.fullmatch(ops, ins[1]) is not None
        R.expect(ok, "0x%08X: %r, want %s %s" % (va, ins, mn, ops))
        R.add("pins")
    # BITBUF_ReadSigned's callers (rows 15)
    callers = S4.raw_callers(0x00411030)
    R.set("readsigned_callers", len(callers))
    R.note("BITBUF_ReadSigned callers: " + " ".join("0x%08X" % c for c in callers))
    # BITBUF_AlignByte's only caller (row 16)
    al = S4.raw_callers(0x00411070)
    R.set("alignbyte_callers", len(al))
    R.note("BITBUF_AlignByte callers: " + " ".join("0x%08X" % c for c in al))
    # the set-state table the writer's 5 bits index (row 98)
    st = S4.dwords(0x006E90B8, 5)
    R.note("set states at 0x006E90B8: %r" % (st,))
    R.expect(list(st) == [0xA5, 0xA6, 0xA7, 0xA8, 0xA9], "set-state table %r" % (st,))
    return R.done()


CHECKS = collections.OrderedDict([("logs", chk_logs), ("corpus", chk_corpus), ("survey", chk_survey),
                                  ("writes", chk_writes), ("reads", chk_reads), ("pairs", chk_pairs),
                                  ("calc", chk_calc), ("props", chk_props), ("static", chk_static)])


def main(argv):
    ap = argparse.ArgumentParser(prog="sweep_s1a.py")
    ap.add_argument("check", choices=list(CHECKS) + ["all"])
    ap.add_argument("--write", help="logs: write the manifest of the logs read")
    a = ap.parse_args(argv)
    if a.check == "all":
        rc = 0
        for name, fn in CHECKS.items():
            rc |= fn(a)
        return rc
    return CHECKS[a.check](a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Docs gate (ADR-0006, plan 0007): mechanical checks on docs/ and re/.

Usage: python3 -I tools/gate.py [--root DIR] [--no-warnings] [--full[=TOOL,...]] [--require-workspace]
       python3 -I tools/gate.py --staged [--also PATH ...] [--root DIR] [--no-warnings]

Implements the fast tier of `.claude/skills/architect/references/evidence-rules.md`
§ Mechanical checks, rule for rule:

  errors   E1 fn:/data: anchors vs re/symbols.csv (name, address, kind)
           E2 src:<id> vs the docs/sources.md table
           E3 run:<id> vs `## run:<id>` headings in docs/findings/*/experiments.md and
              docs/formats/experiments.md; an id defined twice is an error
           E4 tbl:/fmt:/struct: vs docs/tables/, docs/formats/, re/types/*.h
           E5 [L] in a spec only under `## Open questions`
           E6 spec front-matter `tags:` counts vs the body
           E7 re/symbols.csv well-formed
           E8 relative markdown links (file and #fragment) resolve, in every tracked .md
              except tools/gate/fixtures/
           E9 every ```mermaid block under docs/ parses (Mermaid's own parser, see below)
  warnings W1 a [C]/[I] line or table row with no anchor
           W2 a table with a Tag column has a row with an empty tag cell
           W3 a re/symbols.csv row cited by no spec or finding

A finding is a .md under docs/findings/ other than README.md.

E9 runs `node tools/mermaid_check.mjs` once over all blocks (well under a second for ~90 blocks). The
parser is the Mermaid build VS Code ships (MERMAID_SRC below, or $GATE_MERMAID_SRC), copied and
patched to load without a DOM into <checkout>/workspace/cache/mermaid/ (re-copied when the source
changes); nothing is downloaded. A failure is reported at the block's fence line plus the line the
parser names. When node, the bundle, workspace/ or a patch point is missing, E9 is skipped with one
warning and the gate stays usable; $GATE_NO_MERMAID=1 skips it the same way.

Reads only files under docs/ and re/, plus tracked .md files elsewhere for E8 (and the list of
tracked paths, from `git ls-files` when
--root is a git checkout, else a directory walk). The fast tier never reads workspace/ data; E9 only
keeps its parser cache there. Exit 1 on any error,
0 otherwise; warnings never fail. Stdlib only.

Full tier (--full): also runs every registered parser survey (SURVEYS below) against
<root>/workspace/ and compares the last line of its output, `SURVEY <tool> key=value ...` (integer
counts only), key by key with tools/gate/baselines/<tool>.txt. Any difference, a missing baseline,
a missing input path or a survey without its SURVEY line is an error. --full=TOOL[,TOOL] runs only
those surveys, opt-in ones included; --full=all runs every survey. With workspace/ absent it prints
`SKIPPED: workspace absent` and stays green, unless --require-workspace is given.

Staged mode (--staged): check what a commit would contain instead of the working tree. The git index
of --root is exported to a temporary directory (`git checkout-index -a`), each --also PATH (relative to
--root; the paths a chained `git add` names before the commit runs) is copied over it from the working
tree, or removed from it if absent there, and the fast tier runs on that snapshot, listing its files by
a directory walk. Unstaged edits of other files are therefore not seen. Not combinable with --full.
"""
import argparse
import collections
import csv
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from urllib.parse import unquote

# Pinned Game.exe: image base 0x400000, last section .reloc VA 0x00997000 + 0x23000
# (docs/inventory.md, section table).
IMAGE_LO = 0x00400000
IMAGE_HI = 0x009BA000

FIXTURES = "tools/gate/fixtures/"
BASELINES = "tools/gate/baselines"

# ---------------------------------------------------------------- full tier: survey registry
#
# One line per survey. argv is relative to the root: argv[0] is the script (run as
# `python3 -I <root>/<script>`), and every argument starting with "workspace/" is a workspace input,
# resolved under the root and glob-expanded (sorted). Each input must exist. The survey's last
# stdout line must be `SURVEY <tool> ...`. opt_in=True keeps a slow survey (over 60 s) out of a
# bare --full; it runs with --full=<tool> or --full=all.
Survey = collections.namedtuple("Survey", "tool argv opt_in", defaults=(False,))

SURVEYS = [
    Survey("ds1", ["tools/ds1.py", "survey", "workspace/merged"]),
    # plan 0016 P0: preset units, paths, groups and LvlPrest records by generator kind (docs/formats/ds1.md)
    Survey("ds1_units", ["tools/ds1.py", "units", "workspace/merged"]),
    Survey("dt1", ["tools/dt1.py", "survey", "workspace/merged"]),
    # plan 0017 P0: sub-tile flag bits per orientation, position and LvlType (docs/formats/dt1.md)
    Survey("dt1_subtiles", ["tools/dt1.py", "subtiles", "workspace/merged"]),
    # plan 0017 P0: MonStats2 SizeX/spawnCol/objCol over the pool classes (docs/tables/MonStats2.md)
    Survey("mon_collision", ["tools/mon_survey.py", "collision", "workspace/merged/data/global/excel"]),
    # samples hashed in docs/formats/d2s.md; d2s-edited/smpsor.d2s is corrupted on purpose, left out
    Survey("d2s", ["tools/d2s.py", "survey", "workspace/merged/data/global/excel",
                   "workspace/samples/d2s/*.d2s",
                   "workspace/samples/d2s-edited/smpbar.d2s", "workspace/samples/d2s-edited/smpsor-fixed.d2s",
                   "workspace/samples/d2s-edited/smpbar-resaved.d2s",
                   "workspace/samples/d2s-edited/smpsor-resaved.d2s"]),
    # the d2s writer (tools/d2s.py build) re-encodes the same saves byte for byte
    Survey("d2s_roundtrip", ["tools/d2s.py", "roundtrip", "workspace/merged/data/global/excel",
                             "workspace/samples/d2s/*.d2s",
                             "workspace/samples/d2s-edited/smpbar.d2s", "workspace/samples/d2s-edited/smpsor-fixed.d2s",
                             "workspace/samples/d2s-edited/smpbar-resaved.d2s",
                             "workspace/samples/d2s-edited/smpsor-resaved.d2s"]),
    Survey("excel", ["tools/excel_survey.py", "workspace/merged", "workspace/logs/merged-manifest.tsv"]),
    # per-column layout diffs behind the table docs' [C] layout tags: every table in tools/excel_layouts.py,
    # cells and unexplained mismatches per table (a broken offset shows as <table>_bad > 0)
    Survey("excel_layout", ["tools/excel_bin.py", "survey", "workspace/merged/data/global/excel"]),
    Survey("dc6", ["tools/dc6.py", "survey", "workspace/merged"]),
    # full bit-level decode of 21 717 files, about 2.5 min on 16 cores (already parallel): opt-in
    Survey("dcc", ["tools/dcc.py", "survey", "workspace/merged"], opt_in=True),
    # leftover_bytes=9: three objects/f9 files with 3 unexplained bytes (docs/formats/cof.md)
    Survey("cof", ["tools/cof.py", "survey", "workspace/merged"]),
    Survey("tbl", ["tools/tbl.py", "survey", "workspace/merged"]),
    # items/palette/*.dat: 21 x 256 split, colors.txt row count, colour-family soft check
    # (family_bad=9: muted grey2/invgrey reds and purples, docs/formats/item-palette.md)
    Survey("itempal", ["tools/palette.py", "itempal", "workspace/merged"]),
    # plan 0022 P0: LvlMaze rows vs maze levels, maze preset ranges, Vis/Warp links, LvlWarp Direction
    # (docs/tables/LvlMaze.md, LvlPrest.md, Levels.md)
    Survey("maze", ["tools/maze_survey.py", "workspace/merged/data/global/excel", "--quiet"]),
    # plan 0026 P0: outdoor levels per generator act, the preset families each act can place (survey rule),
    # the LvlSub records each level rolls, LvlSub DS1 headers (docs/tables/Levels.md, LvlPrest.md, LvlSub.md)
    Survey("outdoor", ["tools/outdoor_survey.py", "workspace/merged", "--quiet"]),
]

# E9: Mermaid parser shipped with VS Code (no download); cache under the checkout's workspace/
MERMAID_SRC = "/usr/share/code/resources/app/extensions/markdown-language-features/markdown-editor-out"
MERMAID_HELPER = "tools/mermaid_check.mjs"
MERMAID_CACHE = "workspace/cache/mermaid"
MERMAID_TIMEOUT = 120
RE_MERMAID_OPEN = re.compile(r"^(\s*)(`{3,}|~{3,})\s*mermaid\s*$")

SLOW_SECONDS = 60
SURVEY_TIMEOUT = 1800
RE_SURVEY_LINE = re.compile(r"SURVEY ([a-z0-9_]+)((?: [a-z0-9_]+=-?[0-9]+)+)")

SYMBOLS_HEADER = ["address", "kind", "name", "signature", "confidence", "subsystem", "evidence"]

RE_FNDATA = re.compile(r"\b(fn|data):([A-Za-z_][A-Za-z0-9_]*)@(0x[0-9A-Fa-f]+)")
RE_SRC = re.compile(r"\bsrc:([A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?)")
RE_RUN = re.compile(r"\brun:(\d{4}-\d{2}-\d{2}-[A-Za-z0-9-]*[A-Za-z0-9])")
RE_TBL = re.compile(r"\btbl:([A-Za-z0-9_]+)\.txt\b")
RE_FMT = re.compile(r"\bfmt:([A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?)")
RE_STRUCT = re.compile(r"\bstruct:([A-Za-z_][A-Za-z0-9_]*)")
RE_ANY_ANCHOR = re.compile(r"\b(?:fn|data|struct|tbl|fmt|run|src):[A-Za-z0-9_]|\b0x00[0-9A-Fa-f]{6}\b")
RE_TAG = re.compile(r"\[([CIL])\]")
RE_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
RE_FENCE = re.compile(r"^\s*(```|~~~)")
RE_CODESPAN = re.compile(r"(`+)(.+?)\1")
RE_INLINE_LINK = re.compile(r"\[(?:[^\[\]]|\[[^\[\]]*\])*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
RE_REF_DEF = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]*>|\S+)")
RE_HTML_ANCHOR = re.compile(r"<a\s+(?:[^>]*\s)?(?:id|name)=[\"']([^\"']+)[\"']", re.I)
RE_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
RE_FRONT_TAGS = re.compile(r"^tags:\s*\{([^}]*)\}\s*$", re.M)


class Report:
    def __init__(self):
        self.errors = {}    # rule -> [msg]
        self.warnings = {}
        self.checked = {}   # rule -> count of items checked

    def err(self, rule, path, line, msg):
        self.errors.setdefault(rule, []).append(f"{path}:{line}: {rule} {msg}")

    def warn(self, rule, path, line, msg):
        self.warnings.setdefault(rule, []).append(f"{path}:{line}: {rule} {msg}")

    def count(self, rule, n=1):
        self.checked[rule] = self.checked.get(rule, 0) + n


# ---------------------------------------------------------------- files

def tracked_files(root):
    """All tracked paths (posix, relative to root). git index if a checkout, else a walk."""
    if os.path.exists(os.path.join(root, ".git")):
        try:
            out = subprocess.run(["git", "-C", root, "ls-files", "-z"], capture_output=True,
                                 check=True).stdout
            return {p for p in out.decode("utf-8").split("\0") if p and os.path.isfile(os.path.join(root, p))}
        except (OSError, subprocess.CalledProcessError):
            pass
    found = set()
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        dirnames[:] = [d for d in dirnames
                       if not (rel == "." and d in ("workspace", ".git")) and d != "__pycache__"]
        for f in filenames:
            p = os.path.normpath(os.path.join(rel, f)).replace(os.sep, "/")
            found.add(p)
    return found


def read_text(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


def split_front_matter(text):
    """Return (front_matter or None, body, body_first_line_number)."""
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[1:i]), "\n".join(lines[i + 1:]), i + 2
    return None, text, 1


def is_spec(rel, text):
    if not rel.startswith("docs/specs/"):
        return False
    fm, _, _ = split_front_matter(text)
    return fm is not None and re.search(r"^spec:", fm, re.M) is not None


# ---------------------------------------------------------------- markdown helpers

def iter_lines_outside_fences(text):
    """Yield (lineno, line, in_fence)."""
    in_fence = None
    for n, line in enumerate(text.split("\n"), 1):
        m = RE_FENCE.match(line)
        if m:
            if in_fence is None:
                in_fence = m.group(1)
                yield n, line, True
                continue
            if m.group(1) == in_fence:
                in_fence = None
                yield n, line, True
                continue
        yield n, line, in_fence is not None


def headings(text):
    """[(lineno, level, raw text)] outside code fences."""
    out = []
    for n, line, fenced in iter_lines_outside_fences(text):
        if fenced:
            continue
        m = RE_HEADING.match(line)
        if m:
            out.append((n, len(m.group(1)), m.group(2)))
    return out


def gh_slug(heading_text):
    """GitHub heading anchor: render inline markup, lowercase, keep letters/digits/marks/_/-/space."""
    t = re.sub(r"!?\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\([^)]*\)", r"\1", heading_text)
    parts = re.split(r"(`+)(.+?)\1", t)
    # re.split yields text, ticks, code, text, ticks, code, ...: drop tags only in text parts
    t = "".join(re.sub(r"<[^>]+>", "", p) if k % 3 == 0 else (p if k % 3 == 2 else "")
                for k, p in enumerate(parts))
    t = t.lower()
    kept = []
    for c in t:
        cat = unicodedata.category(c)
        if c in "-_ " or cat[0] in "LNM" or cat == "Pc":
            kept.append(c)
    return "".join(kept).replace(" ", "-")


def heading_slugs(text):
    slugs, seen = set(), {}
    for _, _, h in headings(text):
        s = gh_slug(h)
        if s in seen:
            seen[s] += 1
            slugs.add(f"{s}-{seen[s]}")
        else:
            seen[s] = 0
            slugs.add(s)
    for m in RE_HTML_ANCHOR.finditer(text):
        slugs.add(m.group(1))
    return slugs


def strip_codespans(line):
    return RE_CODESPAN.sub(lambda m: " " * len(m.group(0)), line)


def table_cells(line):
    s = line.strip()
    if not s.startswith("|"):
        return None
    s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    # split on unescaped pipes outside code spans
    cells, cur, tick = [], [], False
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and not tick and i + 1 < len(s):
            cur.append(s[i:i + 2])
            i += 2
            continue
        if c == "`":
            tick = not tick
        if c == "|" and not tick:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def is_separator_row(cells):
    return bool(cells) and all(re.fullmatch(r":?-{1,}:?", c) for c in cells if c) and any(cells)


# ---------------------------------------------------------------- registries

def load_symbols(root, rep):
    """E7. Returns {name: (address_int, kind, line)}. Rows E7 rejects are still returned when their
    name and address parse, so a citation of them doesn't add a misleading E1."""
    rel = "re/symbols.csv"
    path = os.path.join(root, rel)
    syms = {}
    if not os.path.isfile(path):
        rep.err("E7", rel, 1, "re/symbols.csv missing")
        return syms
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    if not rows or rows[0] != SYMBOLS_HEADER:
        rep.err("E7", rel, 1, f"header is not {','.join(SYMBOLS_HEADER)}")
        return syms
    by_addr, names_seen = {}, set()
    for i, row in enumerate(rows[1:], 2):
        rep.count("E7")
        if len(row) != len(SYMBOLS_HEADER):
            rep.err("E7", rel, i, f"row has {len(row)} fields, expected {len(SYMBOLS_HEADER)}")
            continue
        r = dict(zip(SYMBOLS_HEADER, row))
        if not re.fullmatch(r"0x00[0-9A-F]{6}", r["address"]):
            rep.err("E7", rel, i, f"address {r['address']!r} does not match 0x00[0-9A-F]{{6}}")
        elif not IMAGE_LO <= int(r["address"], 16) < IMAGE_HI:
            rep.err("E7", rel, i, f"address {r['address']} outside the image "
                                  f"[0x{IMAGE_LO:08X}, 0x{IMAGE_HI:08X})")
        if r["kind"] not in ("func", "data"):
            rep.err("E7", rel, i, f"kind {r['kind']!r} not in {{func, data}}")
        if r["confidence"] not in ("C", "I", "L"):
            rep.err("E7", rel, i, f"confidence {r['confidence']!r} not in {{C, I, L}}")
        ev = r["evidence"].split("#", 1)[0]
        if not ev or not os.path.exists(os.path.join(root, ev)):
            rep.err("E7", rel, i, f"evidence {r['evidence']!r} is not an existing path")
        if not r["name"]:
            rep.err("E7", rel, i, "empty name")
        if r["name"] in names_seen:
            rep.err("E7", rel, i, f"duplicate name {r['name']}")
        names_seen.add(r["name"])
        if r["address"] in by_addr:
            rep.err("E7", rel, i, f"duplicate address {r['address']} (first at line {by_addr[r['address']][1]})")
        else:
            by_addr[r["address"]] = (r["name"], i)
        if r["name"] and r["name"] not in syms and re.fullmatch(r"0x[0-9A-Fa-f]+", r["address"]):
            syms[r["name"]] = (int(r["address"], 16), r["kind"], i)
    return syms


def load_sources(root):
    ids = set()
    path = os.path.join(root, "docs/sources.md")
    if not os.path.isfile(path):
        return ids
    for line in read_text(root, "docs/sources.md").split("\n"):
        cells = table_cells(line)
        if not cells or is_separator_row(cells):
            continue
        m = re.fullmatch(r"`?([^`\s]+)`?", cells[0])
        if m and m.group(1) != "id":
            ids.add(m.group(1))
    return ids


RE_EXPERIMENTS = re.compile(r"docs/findings/[^/]+/experiments\.md|docs/formats/experiments\.md")


def load_runs(root, files, rep):
    """run id -> (file, line) of its `## run:<id>` heading. A second definition is an E3 error."""
    runs = {}
    for rel in files:
        if RE_EXPERIMENTS.fullmatch(rel):
            for n, level, h in headings(read_text(root, rel)):
                m = re.match(r"run:(\S+)", h)
                if level == 2 and m:
                    rid = m.group(1)
                    if rid in runs:
                        rep.err("E3", rel, n, f"run:{rid}: defined twice (first at "
                                              f"{runs[rid][0]}:{runs[rid][1]})")
                    else:
                        runs[rid] = (rel, n)
    return runs


def load_struct_types(root, files):
    names = set()
    for rel in files:
        if re.fullmatch(r"re/types/[^/]+\.h", rel):
            t = read_text(root, rel)
            t = re.sub(r"/\*.*?\*/", " ", t, flags=re.S)
            t = re.sub(r"//[^\n]*", " ", t)
            names.update(re.findall(r"\b(?:struct|union|enum)\s+([A-Za-z_]\w*)", t))
            names.update(re.findall(r"\}\s*([A-Za-z_]\w*)\s*[,;]", t))
            names.update(re.findall(r"\btypedef\s+[^;{}]*?\b([A-Za-z_]\w*)\s*;", t))
    return names


# ---------------------------------------------------------------- checks

def check_anchors(rel, text, kind, ctx, rep):
    """E1-E4 on one doc. kind in {spec, finding, format, table}."""
    lines = text.split("\n")
    for n, line in enumerate(lines, 1):
        if kind in ("spec", "finding"):
            for m in RE_FNDATA.finditer(line):
                rep.count("E1")
                pre, name, addr = m.group(1), m.group(2), int(m.group(3), 16)
                want = "func" if pre == "fn" else "data"
                s = ctx["symbols"].get(name)
                if len(m.group(3)) != 10:
                    rep.err("E1", rel, n, f"{m.group(0)}: address must be 0x + 8 hex digits")
                elif s is None:
                    rep.err("E1", rel, n, f"{m.group(0)}: name {name} not in re/symbols.csv")
                elif s[0] != addr:
                    rep.err("E1", rel, n, f"{m.group(0)}: re/symbols.csv has {name} at 0x{s[0]:08X}")
                elif s[1] != want:
                    rep.err("E1", rel, n, f"{m.group(0)}: {name} is a {s[1]} row, {pre}: needs {want}")
            for m in RE_RUN.finditer(line):
                rep.count("E3")
                if m.group(1) not in ctx["runs"]:
                    rep.err("E3", rel, n, f"run:{m.group(1)}: no `## run:{m.group(1)}` heading in "
                                          f"docs/findings/*/experiments.md or "
                                          f"docs/formats/experiments.md")
            for m in RE_TBL.finditer(line):
                rep.count("E4")
                if m.group(1).lower() not in ctx["tables"]:
                    rep.err("E4", rel, n, f"tbl:{m.group(1)}.txt: no docs/tables/{m.group(1)}.md")
            for m in RE_FMT.finditer(line):
                rep.count("E4")
                if m.group(1) not in ctx["formats"]:
                    rep.err("E4", rel, n, f"fmt:{m.group(1)}: no docs/formats/{m.group(1)}.md")
            for m in RE_STRUCT.finditer(line):
                rep.count("E4")
                if m.group(1) not in ctx["structs"]:
                    rep.err("E4", rel, n, f"struct:{m.group(1)}: type not declared in re/types/*.h")
        for m in RE_SRC.finditer(line):
            rep.count("E2")
            if m.group(1) not in ctx["sources"]:
                rep.err("E2", rel, n, f"src:{m.group(1)}: id not in the docs/sources.md table")


def check_spec_tags(rel, text, rep):
    """E5 and E6."""
    fm, body, first = split_front_matter(text)
    counts = {"C": 0, "I": 0, "L": 0}
    in_oq = False
    for n, line, fenced in iter_lines_outside_fences(body):
        ln = n + first - 1
        if not fenced:
            m = RE_HEADING.match(line)
            if m and len(m.group(1)) <= 2:
                in_oq = len(m.group(1)) == 2 and m.group(2).strip() == "Open questions"
        for t in RE_TAG.findall(line):
            counts[t] += 1
            if t == "L":
                rep.count("E5")
                if not in_oq:
                    rep.err("E5", rel, ln, "[L] outside `## Open questions`")
    rep.count("E6")
    m = RE_FRONT_TAGS.search(fm or "")
    if not m:
        rep.err("E6", rel, 1, "front matter has no `tags: {C: n, I: n, L: n}`")
        return
    declared = {}
    for part in m.group(1).split(","):
        kv = part.split(":")
        if len(kv) == 2 and kv[0].strip() in counts and kv[1].strip().isdigit():
            declared[kv[0].strip()] = int(kv[1].strip())
    fm_line = 1 + (fm or "").split("\n").index(m.group(0)) + 1
    if set(declared) != set(counts):
        rep.err("E6", rel, fm_line, f"tags: must give C, I and L; got {m.group(0)!r}")
        return
    for k in "CIL":
        if declared[k] != counts[k]:
            rep.err("E6", rel, fm_line, f"tags: {k}: {declared[k]} but the body has {counts[k]} [{k}]")


def check_links(rel, text, ctx, rep):
    """E8."""
    base = os.path.dirname(rel)
    for n, line, fenced in iter_lines_outside_fences(text):
        if fenced:
            continue
        s = strip_codespans(line)
        targets = [m.group(1) for m in RE_INLINE_LINK.finditer(s)]
        m = RE_REF_DEF.match(s)
        if m:
            targets.append(m.group(1))
        for t in targets:
            t = t.strip()
            if t.startswith("<") and t.endswith(">"):
                t = t[1:-1]
            if not t or RE_SCHEME.match(t) or t.startswith("//"):
                continue
            rep.count("E8")
            path, _, frag = t.partition("#")
            path = unquote(path)
            if path:
                target = os.path.normpath(path.lstrip("/") if path.startswith("/")
                                          else os.path.join(base, path)).replace(os.sep, "/")
                if target.startswith("../") or target == "..":
                    rep.err("E8", rel, n, f"link {t}: points outside the repository")
                    continue
                if target not in ctx["tracked"]:
                    prefix = target.rstrip("/") + "/"
                    if not any(p.startswith(prefix) for p in ctx["tracked"]) or target == ".":
                        if target != ".":
                            rep.err("E8", rel, n, f"link {t}: {target} is not a tracked file")
                            continue
                    continue  # a directory with tracked files; no fragment check
            else:
                target = rel
            if frag and target.endswith(".md"):
                slugs = ctx["slug_cache"].get(target)
                if slugs is None:
                    slugs = heading_slugs(read_text(ctx["root"], target))
                    ctx["slug_cache"][target] = slugs
                if unquote(frag) not in slugs:
                    rep.err("E8", rel, n, f"link {t}: no heading with slug #{frag} in {target}")


def logical_units(text):
    """(lineno, text) statements for W1: a table row, or a paragraph / list item with its
    continuation lines (a tag at the start of a wrapped bullet, anchors at its end)."""
    units, cur, start = [], [], 0

    def flush():
        if cur:
            units.append((start, " ".join(cur)))
        cur.clear()

    for n, line, fenced in iter_lines_outside_fences(text):
        st = line.strip()
        if fenced:
            flush()
            if st and not RE_FENCE.match(line):
                units.append((n, line))
            continue
        if not st or RE_HEADING.match(line):
            flush()
            if st:
                units.append((n, line))
            continue
        if st.startswith("|"):
            flush()
            units.append((n, line))
            continue
        if re.match(r"^\s*(?:[-*+]|\d+[.)])\s", line) or not cur:
            flush()
            start = n
        cur.append(line)
    flush()
    return units


def check_warnings_doc(rel, text, rep):
    """W1 and W2 on a spec or finding."""
    _, body, first = split_front_matter(text)
    off = first - 1
    for n, unit in logical_units(body):
        if re.search(r"\[[CI]\]", unit):
            rep.count("W1")
            if not RE_ANY_ANCHOR.search(unit):
                rep.warn("W1", rel, n + off, "[C]/[I] statement without an anchor")
    tag_col = None
    for n, line, fenced in iter_lines_outside_fences(body):
        cells = None if fenced else table_cells(line)
        if cells is None:
            tag_col = None
            continue
        if tag_col is None:
            lowered = [c.strip("`* ").lower() for c in cells]
            tag_col = lowered.index("tag") if "tag" in lowered else -1
            continue
        if tag_col < 0 or is_separator_row(cells):
            continue
        rep.count("W2")
        if tag_col >= len(cells) or not cells[tag_col].strip():
            rep.warn("W2", rel, n + off, "table row with an empty Tag cell")


# ---------------------------------------------------------------- full tier

def parse_survey_line(line, tool):
    """`SURVEY <tool> k=v ...` -> {k: int}, or raise ValueError naming what is wrong."""
    m = RE_SURVEY_LINE.fullmatch(line.strip())
    if not m:
        raise ValueError(f"not a `SURVEY {tool} key=<int> ...` line: {line.strip()[:120]!r}")
    if m.group(1) != tool:
        raise ValueError(f"SURVEY line names tool {m.group(1)!r}, expected {tool!r}")
    out = {}
    for kv in m.group(2).split():
        k, v = kv.split("=")
        if k in out:
            raise ValueError(f"key {k} repeated")
        out[k] = int(v)
    return out


def select_surveys(spec, registry):
    """--full value -> the surveys to run. 'default': all but opt-in; 'all'; or a comma list."""
    if spec == "default":
        return [sv for sv in registry if not sv.opt_in]
    if spec == "all":
        return list(registry)
    names = [n for n in spec.split(",") if n]
    known = {sv.tool: sv for sv in registry}
    unknown = [n for n in names if n not in known]
    if unknown:
        raise ValueError(f"unknown survey(s) {', '.join(unknown)}; registered: {', '.join(known)}")
    return [known[n] for n in names]


def resolve_argv(root, sv):
    """Survey argv -> (command, missing inputs)."""
    cmd, missing = [sys.executable, "-I", os.path.join(root, sv.argv[0])], []
    for a in sv.argv[1:]:
        if not a.startswith("workspace/"):
            cmd.append(a)
            continue
        path = os.path.join(root, a)
        if glob.has_magic(a):
            hits = sorted(glob.glob(path))
            if not hits:
                missing.append(a)
            cmd.extend(hits)
        elif os.path.exists(path):
            cmd.append(path)
        else:
            missing.append(a)
    return cmd, missing


def run_survey(root, sv):
    """Run one survey and diff its SURVEY line with the baseline. -> (errors, seconds, line)."""
    errs = []
    base_rel = f"{BASELINES}/{sv.tool}.txt"
    base_path = os.path.join(root, base_rel)
    baseline = None
    if not os.path.isfile(base_path):
        errs.append(f"{base_rel}: no baseline")
    else:
        lines = [ln for ln in read_text(root, base_rel).splitlines() if ln.strip()]
        try:
            if len(lines) != 1:
                raise ValueError(f"{len(lines)} non-empty lines, expected 1")
            baseline = parse_survey_line(lines[0], sv.tool)
        except ValueError as e:
            errs.append(f"{base_rel}: {e}")
    cmd, missing = resolve_argv(root, sv)
    if missing:
        errs.append(f"{sv.tool}: input missing under the root: {', '.join(missing)}")
        return errs, 0.0, None
    t0 = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=root, capture_output=True, timeout=SURVEY_TIMEOUT)
    except subprocess.TimeoutExpired:
        errs.append(f"{sv.tool}: timed out after {SURVEY_TIMEOUT} s")
        return errs, time.monotonic() - t0, None
    dt = time.monotonic() - t0
    out = proc.stdout.decode("utf-8", "replace").splitlines()
    last = out[-1] if out else ""
    if proc.returncode != 0:
        tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()
        errs.append(f"{sv.tool}: survey exit {proc.returncode}" + (f" ({tail[-1][:160]})" if tail else ""))
    try:
        now = parse_survey_line(last, sv.tool)
    except ValueError as e:
        errs.append(f"{sv.tool}: last output line: {e}")
        return errs, dt, None
    if baseline is not None:
        for k in list(baseline) + [k for k in now if k not in baseline]:
            if k not in now:
                errs.append(f"{sv.tool}: {k}: baseline {baseline[k]}, survey has no such key")
            elif k not in baseline:
                errs.append(f"{sv.tool}: {k}: not in baseline, survey {now[k]}")
            elif baseline[k] != now[k]:
                errs.append(f"{sv.tool}: {k}: baseline {baseline[k]}, survey {now[k]} ({now[k] - baseline[k]:+d})")
    return errs, dt, last.strip()


def run_full(root, spec="default", require_workspace=False, registry=None, out=None):
    """Full tier. Prints its own lines; returns the number of errors."""
    out = out or sys.stdout
    registry = SURVEYS if registry is None else registry
    print("\nFull tier (survey baselines):", file=out)
    try:
        chosen = select_surveys(spec, registry)
    except ValueError as e:
        print(f"  ERROR {e}", file=out)
        print("gate full tier: RED, 1 errors", file=out)
        return 1
    if not os.path.isdir(os.path.join(root, "workspace")):
        print("SKIPPED: workspace absent", file=out)
        if require_workspace:
            print("gate full tier: RED, workspace absent and --require-workspace given", file=out)
            return 1
        print("gate full tier: SKIPPED", file=out)
        return 0
    nerr, total = 0, 0.0
    skipped = [sv.tool for sv in registry if sv not in chosen and sv.opt_in]
    for sv in chosen:
        errs, dt, line = run_survey(root, sv)
        total += dt
        nerr += len(errs)
        slow = f" (over {SLOW_SECONDS} s: mark it opt_in in SURVEYS)" if dt > SLOW_SECONDS and not sv.opt_in else ""
        print(f"S {sv.tool:6} {'FAIL' if errs else 'ok':4} {dt:7.2f} s{slow}", file=out)
        for e in errs:
            print(f"  {e}", file=out)
        if errs and line:
            print(f"  now: {line}", file=out)
    if skipped:
        print(f"opt-in, not run: {', '.join(skipped)} (use --full=<tool> or --full=all)", file=out)
    print(f"gate full tier: {'RED' if nerr else 'GREEN'}, {len(chosen)} surveys, {nerr} errors, "
          f"{total:.2f} s", file=out)
    return nerr


# ---------------------------------------------------------------- E9 mermaid blocks

def mermaid_blocks(text):
    """Yield (fence_lineno, body) for each ```mermaid block; the fence's indent is stripped."""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = RE_MERMAID_OPEN.match(lines[i])
        fm = m or re.match(r"^(\s*)(`{3,}|~{3,})", lines[i])
        if not fm:
            i += 1
            continue
        indent, fence = fm.group(1), fm.group(2)
        close = re.compile(r"^\s*" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*$")
        j = i + 1
        while j < len(lines) and not close.match(lines[j]):
            j += 1
        if m:
            body = [ln[len(indent):] if ln.startswith(indent) else ln.lstrip() for ln in lines[i + 1:j]]
            yield i + 1, "\n".join(body)
        i = j + 1


def check_mermaid(blocks, cache_root, rep):
    """blocks: [(rel, fence_lineno, body)]. One helper run; skip with one E9 warning if unavailable."""
    if not blocks:
        return

    def skip(why):
        rep.warn("E9", MERMAID_HELPER, 0, f"skipped, {len(blocks)} mermaid blocks not parsed: {why}")
    if os.environ.get("GATE_NO_MERMAID"):
        return skip("GATE_NO_MERMAID is set")
    node = shutil.which("node")
    if not node:
        return skip("node not on PATH")
    src = os.environ.get("GATE_MERMAID_SRC", MERMAID_SRC)
    if not os.path.isdir(src):
        return skip(f"Mermaid bundle not found at {src}")
    helper = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mermaid_check.mjs")
    if not os.path.isdir(os.path.join(cache_root, "workspace")):
        return skip("no workspace/ for the parser cache")
    payload = json.dumps({"blocks": [{"id": k, "text": b[2]} for k, b in enumerate(blocks)]})
    try:
        proc = subprocess.run([node, helper, "--src", src, "--cache", os.path.join(cache_root, MERMAID_CACHE)],
                              input=payload, capture_output=True, text=True, timeout=MERMAID_TIMEOUT)
        res = json.loads(proc.stdout.strip().splitlines()[-1])
    except (OSError, subprocess.TimeoutExpired, ValueError, IndexError) as e:
        return skip(f"helper failed ({type(e).__name__})")
    if "skip" in res:
        return skip(res["skip"])
    rep.count("E9", len(res.get("results", [])))
    for r in res.get("results", []):
        if r["ok"]:
            continue
        rel, fence, _ = blocks[r["id"]]
        line = fence + r["line"] if r.get("line") else fence
        rep.err("E9", rel, line, f"mermaid parse error: {r['message']}")


# ---------------------------------------------------------------- driver

RULES = [
    ("E1", "fn:/data: anchors resolve in re/symbols.csv"),
    ("E2", "src: anchors in docs/sources.md"),
    ("E3", "run: anchors have an experiments.md heading"),
    ("E4", "tbl:/fmt:/struct: anchors have a doc or type"),
    ("E5", "[L] only under Open questions (specs)"),
    ("E6", "front-matter tag counts (specs)"),
    ("E7", "re/symbols.csv rows well-formed"),
    ("E8", "relative links and #fragments resolve"),
    ("E9", "mermaid blocks parse"),
    ("W1", "[C]/[I] statements carry an anchor"),
    ("W2", "Tag cells filled"),
    ("W3", "symbols cited by a spec or finding"),
]


def run_gate(root, cache_root=None):
    """cache_root: the checkout whose workspace/ holds the E9 parser cache (default root)."""
    rep = Report()
    tracked = tracked_files(root)
    scoped = sorted(p for p in tracked if p.startswith(("docs/", "re/")))
    mds = [p for p in scoped if p.endswith(".md")]
    # E8 covers every tracked .md except the gate's own test fixtures
    link_mds = sorted(p for p in tracked if p.endswith(".md") and not p.startswith(FIXTURES))
    texts = {p: read_text(root, p) for p in set(mds) | set(link_mds)}
    ctx = {
        "root": root,
        "tracked": tracked,
        "symbols": load_symbols(root, rep),
        "sources": load_sources(root),
        "runs": load_runs(root, scoped, rep),
        "tables": {os.path.basename(p)[:-3].lower() for p in scoped
                   if re.fullmatch(r"docs/tables/[^/]+\.md", p)},
        "formats": {os.path.basename(p)[:-3] for p in scoped
                    if re.fullmatch(r"docs/formats/[^/]+\.md", p)},
        "structs": load_struct_types(root, scoped),
        "slug_cache": {},
    }
    cited = []
    for rel in mds:
        text = texts[rel]
        if is_spec(rel, text):
            kind = "spec"
        elif rel.startswith("docs/findings/") and os.path.basename(rel) != "README.md":
            kind = "finding"
        elif rel.startswith("docs/formats/"):
            kind = "format"
        elif rel.startswith("docs/tables/"):
            kind = "table"
        else:
            kind = None
        if kind:
            check_anchors(rel, text, kind, ctx, rep)
        if kind == "spec":
            check_spec_tags(rel, text, rep)
        if kind in ("spec", "finding"):
            check_warnings_doc(rel, text, rep)
            cited.append(text)
    for rel in link_mds:
        check_links(rel, texts[rel], ctx, rep)
    check_mermaid([(rel, n, body) for rel in mds if rel.startswith("docs/")
                   for n, body in mermaid_blocks(texts[rel])], cache_root or root, rep)
    # W3: a symbol is cited when its name appears in some spec or finding
    corpus = "\n".join(cited)
    for name, (_, _, line) in sorted(ctx["symbols"].items(), key=lambda kv: kv[1][2]):
        rep.count("W3")
        if not re.search(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])", corpus):
            rep.warn("W3", "re/symbols.csv", line, f"{name} is cited by no doc")
    return rep


def staged_snapshot(root, also, dest):
    """Export root's git index into dest, then overlay the working-tree copies of `also`."""
    subprocess.run(["git", "-C", root, "checkout-index", "-a", "-f", "--prefix=" + dest.rstrip("/") + "/"],
                   check=True, capture_output=True)
    for rel in also:
        rel = os.path.normpath(rel)
        if rel.startswith("..") or os.path.isabs(rel):
            raise ValueError(f"--also path outside the root: {rel}")
        src, dst = os.path.join(root, rel), os.path.join(dest, rel)
        if os.path.isdir(src):
            for dirpath, _, filenames in os.walk(src):
                for f in filenames:
                    r = os.path.relpath(os.path.join(dirpath, f), root)
                    os.makedirs(os.path.dirname(os.path.join(dest, r)), exist_ok=True)
                    shutil.copy2(os.path.join(root, r), os.path.join(dest, r))
        elif os.path.isfile(src):
            os.makedirs(os.path.dirname(dst) or dest, exist_ok=True)
            shutil.copy2(src, dst)
        elif os.path.isfile(dst):
            os.remove(dst)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    help="repository root to check (default: this checkout)")
    ap.add_argument("--no-warnings", action="store_true", help="print warning counts only")
    ap.add_argument("--full", nargs="?", const="default", metavar="TOOL[,TOOL]",
                    help="also run the survey baselines (all but opt-in; or the named ones; or 'all')")
    ap.add_argument("--require-workspace", action="store_true",
                    help="with --full, fail when workspace/ is absent instead of skipping")
    ap.add_argument("--staged", action="store_true",
                    help="check the git index (plus --also paths) instead of the working tree")
    ap.add_argument("--also", nargs="+", default=[], metavar="PATH",
                    help="with --staged: working-tree paths to overlay on the index (a chained git add)")
    args = ap.parse_args(argv)
    if args.also and not args.staged:
        ap.error("--also needs --staged")
    if args.staged and args.full is not None:
        ap.error("--staged checks the fast tier only; run --full separately")
    t0 = time.monotonic()
    if args.staged:
        with tempfile.TemporaryDirectory(prefix="gate-staged-") as tmp:
            try:
                staged_snapshot(os.path.abspath(args.root), args.also, tmp)
            except (OSError, ValueError, subprocess.CalledProcessError) as e:
                print(f"gate --staged: cannot build the snapshot: {e}", file=sys.stderr)
                return 2
            rep = run_gate(tmp, cache_root=os.path.abspath(args.root))
    else:
        rep = run_gate(os.path.abspath(args.root))
    for rule, desc in RULES:
        bucket = rep.errors if rule.startswith("E") else rep.warnings
        n = len(bucket.get(rule, []))
        word = "errors" if rule.startswith("E") else "warnings"
        status = ("FAIL" if n else "ok") if rule.startswith("E") else ("warn" if n else "ok")
        if rule.startswith("E") and not n and rep.warnings.get(rule):
            status = "skip"
        print(f"{rule} {status:4} {desc}: {rep.checked.get(rule, 0)} checked, {n} {word}")
    nerr = sum(len(v) for v in rep.errors.values())
    nwarn = sum(len(v) for v in rep.warnings.values())
    if nwarn and not args.no_warnings:
        print("\nWarnings:")
        for rule, _ in RULES:
            for msg in rep.warnings.get(rule, []):
                print("  " + msg)
    if nerr:
        print("\nErrors:")
        for rule, _ in RULES:
            for msg in rep.errors.get(rule, []):
                print("  " + msg)
    dt = time.monotonic() - t0
    print(f"\ngate fast tier: {'RED' if nerr else 'GREEN'}, {nerr} errors, {nwarn} warnings, {dt:.2f} s")
    if args.full is not None:
        nerr += run_full(os.path.abspath(args.root), args.full, args.require_workspace)
    elif args.require_workspace:
        print("--require-workspace has no effect without --full", file=sys.stderr)
    return 1 if nerr else 0


if __name__ == "__main__":
    sys.exit(main())

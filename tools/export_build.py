#!/usr/bin/env python3
"""Cut the public export (plan 0070 Phase 3; ADR-0009, ADR-0035, ADR-0036) into workspace/export/.

Usage:
  python3 -I tools/export_build.py [--out DIR] [--manifest FILE] [--root DATA_ROOT] [--date YYYY-MM-DD]
                                   [--allow-hex FILE] [--no-illustrations]

Reads docs/export/manifest.txt (the allowlist: a page reaches the export only by being named there) and writes a
Markdown tree shaped for the export repository's Starlight project:
  <out>/site/src/content/docs/<route>.md   one page per `page` line; `title` and `sidebar.order` front matter
  <out>/site/src/cut.json                  {"date": ..., "groups": [{"slug", "label"}, ...]}
  <out>/site/public/illustrations/<id>/    each ```illustration block, run by its tool in --schematic mode only
  <out>/report.txt                         every drop and every residue item (never published)
Nothing else is written. --out is refused unless it is workspace/export or workspace/export-<name>; the builder
renders no HTML and makes no network request (the export repository's CI draws the Mermaid fences).

Per page, in this order:
  1. redactor    front matter; *Open questions* sections; evidence parentheticals made only of anchors, run ids,
                 addresses and finding links; anchor-only table columns; the address column of pseudocode lines;
                 `sub_XXXXXXXX_` prefixes.
  2. simplifier  runs export_check's text rules (X1-X5, X9, with the hex allowance) on each unit (a sentence of a
                 paragraph, a list item, a table row, a fenced block) and drops a unit that fails; a unit with an
                 `[L]` tag goes too. A section goes when its heading fails or nothing is left under it. It never
                 rewrites a word of a unit it keeps. Every drop is a report line: page, heading, rule, text.
  3. link rewriter  a link to a page of the manifest becomes a link to its route, relative to the linking page
                 (the heading anchor kept when the heading is still there); a link to a page an `alias` line of
                 the manifest names goes to that line's page; any other link keeps its text and loses its target.
  4. illustrations  each block runs `tools/<tool> <root> <args> --schematic --out <folder>` (only the tools that
                 have the mode); the page gets a link to the GIF, a link to the step-through page and the caption,
                 simplified like page text. A block whose tool has no schematic mode is dropped.
The GIF is linked, not embedded: an inline image of a public file needs the base path, which the cut does not know.
Stdlib only.
"""
import argparse
import datetime
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import export_check as ec  # noqa: E402

REPO = os.path.normpath(os.path.join(HERE, ".."))
DOCS = os.path.join(REPO, "docs")
WS = os.path.join(REPO, "workspace")
ILLUS_TIMEOUT = 600
SCHEMATIC_TOOLS = ("maze_anim.py", "tc_anim.py")
ILLUS_KEYS = ("id", "tool", "args", "seed", "illustrates", "caption")

RE_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
RE_FENCE = re.compile(r"^(\s*)(```+|~~~+)\s*([\w-]*)")
RE_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")
RE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
RE_LINK = re.compile(r"(?<!!)\[((?:[^\[\]]|\[[^\]]*\])*)\]\(\s*<?([^)\s>]*)>?(?:\s+\"[^\"]*\")?\s*\)")
RE_ILLUS_LINK = re.compile(r"^(?:\.\./)*(?:\./)?illustrations/[\w.-]+/[\w.-]+$")
RE_SUB = re.compile(r"\bsub_[0-9A-Fa-f]{8}_")
RE_ADDR_COL = re.compile(r"^(\s*)(?:0x)?[0-9A-Fa-f]{8}\s*[:|]?\s+")
# an evidence token: an anchor, a run id, an address, a finding link or id, a repository reference
EVIDENCE = [
    re.compile(r"\[[^\]]*\]\([^)]*\)"),
    re.compile(r"\b(?:fn|data|struct|tbl|fmt|src|run):[^\s,;()\]]+"),
    re.compile(r"@?0x[0-9A-Fa-f]{6,8}\b"),
    re.compile(r"\b[a-z]+/\d{4}(?:-[\w-]+)?(?:#[\w-]+)?"),
    re.compile(r"\b(?:ADR|plan|finding|run|backlog)[- ]?[\w-]*\d+[\w-]*", re.I),
    re.compile(r"\baddendum\b|\bsee\b|\band\b|\bat\b", re.I),
    re.compile(r"\b\d{4}-\d\d-\d\d\b"),
    re.compile(r"\bsub_[0-9A-Fa-f]+\w*"),
    re.compile(r"`[\w.>*-]*\+0x[0-9A-Fa-f]+(?:\s*\+\s*0x[0-9A-Fa-f]+)?`"),   # an in-memory offset, `ItemData+0x10`
]


# ---------------------------------------------------------------- manifest

def parse_manifest(path):
    groups, pages, aliases = [], [], []
    for raw in open(path, encoding="utf-8"):
        f = raw.split("#", 1)[0].split()
        if not f:
            continue
        if f[0] == "group" and len(f) >= 4:
            groups.append({"slug": f[1], "order": int(f[2]), "label": " ".join(f[3:])})
        elif f[0] == "page" and len(f) >= 4:
            stem = os.path.splitext(os.path.basename(f[1]))[0]
            pages.append({"path": f[1], "group": f[2], "order": int(f[3]),
                          "route": stem if f[2] == "-" else f"{f[2]}/{stem}"})
        elif f[0] == "alias" and len(f) >= 3:
            aliases.append((f[1], f[2]))        # a link to f[1] (not exported) goes to the page f[2] (Phase 6 review)
    return groups, pages, aliases


def safe_out(out):
    """workspace/export or workspace/export-<name> only (the builder writes nowhere else)."""
    real = os.path.realpath(out)
    rel = os.path.relpath(real, os.path.realpath(WS))
    top = rel.split(os.sep)[0]
    if rel.startswith("..") or not (top == "export" or top.startswith("export-")):
        raise SystemExit(f"export_build: --out {out} refused: only workspace/export or workspace/export-<name>")
    return real


# ---------------------------------------------------------------- Markdown into blocks

def strip_front_matter(lines):
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return lines[i + 1:]
    return lines


def parse_blocks(lines):
    """-> [dict(kind, lines, ...)]: heading, fence, table, item, quote, para, blank."""
    blocks, i, n = [], 0, len(lines)
    while i < n:
        ln = lines[i]
        m = RE_FENCE.match(ln)
        if m:
            j = i + 1
            while j < n:
                m2 = RE_FENCE.match(lines[j])
                if m2 and m2.group(2)[0] == m.group(2)[0] and not m2.group(3):
                    break
                j += 1
            blocks.append({"kind": "fence", "info": m.group(3).lower(), "lines": lines[i:j + 1]})
            i = j + 1
            continue
        if not ln.strip():
            blocks.append({"kind": "blank", "lines": [""]})
            i += 1
            continue
        h = RE_HEADING.match(ln)
        if h:
            blocks.append({"kind": "heading", "level": len(h.group(1)), "text": h.group(2), "lines": [ln]})
            i += 1
            continue
        if ln.lstrip().startswith("|") and i + 1 < n and RE_SEP.match(lines[i + 1]):
            j = i
            while j < n and lines[j].lstrip().startswith("|"):
                j += 1
            blocks.append({"kind": "table", "lines": lines[i:j]})
            i = j
            continue
        if ln.startswith(">"):
            j = i
            while j < n and lines[j].startswith(">"):
                j += 1
            blocks.append({"kind": "quote", "lines": lines[i:j]})
            i = j
            continue
        m = RE_ITEM.match(ln)
        if m:
            j = i + 1
            while j < n and lines[j].strip() and not RE_ITEM.match(lines[j]) and not RE_FENCE.match(lines[j]) \
                    and not RE_HEADING.match(lines[j]):
                j += 1
            blocks.append({"kind": "item", "indent": len(m.group(1).expandtabs(4)), "lines": lines[i:j]})
            i = j
            continue
        j = i
        while j < n and lines[j].strip() and not RE_HEADING.match(lines[j]) and not RE_FENCE.match(lines[j]) \
                and not RE_ITEM.match(lines[j]) and not lines[j].startswith(">") \
                and not (lines[j].lstrip().startswith("|") and j + 1 < n and RE_SEP.match(lines[j + 1])):
            j += 1
        j = max(j, i + 1)
        blocks.append({"kind": "para", "lines": lines[i:j]})
        i = j
    return blocks


# ---------------------------------------------------------------- redactor

def parenthetical_spans(text):
    """Spans (start, end) of the outermost balanced (...) groups."""
    spans, stack = [], []
    for i, c in enumerate(text):
        if c == "(":
            stack.append(i)
        elif c == ")" and stack:
            s = stack.pop()
            if not stack:
                spans.append((s, i + 1))
    return spans


def evidence_only(inner):
    s = inner
    for rx in EVIDENCE:
        s = rx.sub(" ", s)
    return not re.sub(r"[\s,;:.\-–—/#()\[\]]+", "", s)


RE_PUNCT_AFTER = re.compile(r"[ \t]*(?:\n[ \t]*)?(?=[.,;:!?])")


def drop_evidence_parens(text):
    out, last = [], 0
    for s, e in parenthetical_spans(text):
        inner = text[s + 1:e - 1]
        if inner.strip() and evidence_only(inner):
            # a parenthetical on a line of its own leaves its closing punctuation on the next line; join it back, so
            # the page does not read "confirmed ." (Phase 6 review, 2026-11-17)
            m = RE_PUNCT_AFTER.match(text, e)
            if m:
                out.append(text[last:s].rstrip(" \t\n"))
                last = m.end()
            else:
                out.append(text[last:s].rstrip(" "))
                last = e
    out.append(text[last:])
    return "".join(out)


# a "See <link>." sentence whose links are all labelled by a repository path (`specs/items/tc`, `findings/rng/0001`):
# an evidence pointer like a parenthetical, dropped whole (architect review 2026-11-17)
RE_SEE_PATHS = re.compile(r"(?:(?<=\s)|^)See\s+(?:\[[^\]\s]*/[^\]]*\]\([^)]*\)\s*(?:,\s*|and\s+)?)+\.")


def redact_text(text):
    t = drop_evidence_parens(text)
    if RE_SEE_PATHS.search(t):
        t = re.sub(r"[ \t]+$", "", RE_SEE_PATHS.sub("", t), flags=re.M)
    return RE_SUB.sub("", t)


def is_evidence_cell(cell):
    c = cell.strip()
    if not c or c in ("-", "—", "–"):
        return True
    return evidence_only(c) and bool(re.search(r"fn:|data:|struct:|tbl:|run:|src:|0x|findings|/\d{4}", c))


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return re.split(r"(?<!\\)\|", s)


def redact_table(lines):
    """Drop a column whose body cells are all anchors, addresses or links to findings (and at least one is)."""
    rows = [split_row(x) for x in lines]
    if len(rows) < 3:
        return lines
    ncol = len(rows[0])
    drop = []
    for c in range(ncol):
        body = [r[c] for r in rows[2:] if c < len(r)]
        if body and all(is_evidence_cell(x) for x in body) and any(x.strip() for x in body):
            drop.append(c)
    if not drop or len(drop) == ncol:
        return lines
    return ["| " + " | ".join(x.strip() for k, x in enumerate(r) if k not in drop) + " |" for r in rows]


# ---------------------------------------------------------------- simplifier

def strip_links(text):
    return RE_LINK.sub(lambda m: m.group(1), text)


def split_sentences(text):
    return [p for p in re.split(r"(?<=[.!?])\s+(?=(?!\[[CIL]\])[A-Z\[`(*\"'_|])", text) if p.strip()]


class Page:
    def __init__(self, spec):
        self.spec = spec
        self.path, self.route = spec["path"], spec["route"]
        self.title = ""
        self.drops = []          # (heading, rules, kind, text)
        self.units = 0           # units seen: sentences, items, rows, quotes, fences, captions
        self.dropped = 0         # units dropped (children of a dropped item included)
        self.headings = set()


def slug(text):
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text.lower().replace("`", ""))
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", t, flags=re.U).strip())


def unit_fails(text, allow, sect=False, pins=()):
    rules = ec.text_rules(strip_links(text), allow=allow, sect=sect, pins=pins)
    if "[L]" in text:
        rules = rules | {"XL"}
    return rules


def simplify(page, blocks, allow):
    """blocks -> kept blocks, logging every drop. A section goes when its heading fails."""
    out = []
    heading = ""
    skip_level = None
    dropped_indent = None
    tr = ec.SectionTracker(allow, page.path)
    pins = allow.pins.get(page.path, {})
    for b in blocks:
        k = b["kind"]
        if k == "heading":
            if skip_level is not None and b["level"] > skip_level:
                continue                      # inside a dropped section
            skip_level = None
            heading = b["text"]
            r = unit_fails(b["text"], allow, tr.heading(b["level"], b["text"]), pins)
            if r:
                page.drops.append((heading, ",".join(sorted(r)), "section", b["text"][:200]))
                skip_level = b["level"]
                continue
            out.append(b)
            continue
        if skip_level is not None:
            continue
        if k != "item":
            dropped_indent = None
        if k == "blank":
            out.append(b)
        elif k == "para":
            text = " ".join(x.strip() for x in b["lines"])
            sents = split_sentences(text)
            kept = []
            for s in sents:
                page.units += 1
                r = unit_fails(s, allow, tr.on, pins)
                if r:
                    page.dropped += 1
                    page.drops.append((heading, ",".join(sorted(r)), "sentence", s[:200]))
                else:
                    kept.append(s)
            if kept:
                out.append(b if len(kept) == len(sents) else {"kind": "para", "lines": [" ".join(kept)]})
        elif k == "item":
            page.units += 1
            if dropped_indent is not None and b["indent"] > dropped_indent:
                page.dropped += 1
                page.drops.append((heading, "parent", "item", "child of a dropped item: " + b["lines"][0].strip()[:120]))
                continue
            dropped_indent = None
            r = unit_fails("\n".join(b["lines"]), allow, tr.on, pins)
            if r:
                page.dropped += 1
                dropped_indent = b["indent"]
                page.drops.append((heading, ",".join(sorted(r)), "item", " ".join(x.strip() for x in b["lines"])[:200]))
            else:
                out.append(b)
        elif k == "table":
            lines = b["lines"]
            nrows = max(1, len(lines) - 2)
            head = unit_fails("\n".join(lines[:2]), allow, tr.on, pins)
            if head:
                page.units += nrows
                page.dropped += nrows
                page.drops.append((heading, ",".join(sorted(head)), "table", "header failed: " + lines[0][:160]))
                continue
            keep, nbody = lines[:2], 0
            for row in lines[2:]:
                page.units += 1
                r = unit_fails(row, allow, tr.on, pins)
                if r:
                    page.dropped += 1
                    page.drops.append((heading, ",".join(sorted(r)), "row", row[:200]))
                else:
                    keep.append(row)
                    nbody += 1
            if nbody:
                out.append({"kind": "table", "lines": keep})
        elif k in ("quote", "fence"):
            page.units += 1
            r = unit_fails("\n".join(b["lines"]), allow, tr.on, pins)
            if r:
                page.dropped += 1
                page.drops.append((heading, ",".join(sorted(r)), k, " ".join(x.strip() for x in b["lines"])[:200]))
            else:
                out.append(b)
        else:
            out.append(b)
    return prune_empty(out)


def prune_empty(blocks):
    """Drop a heading with no content below it up to the next heading of its level or higher (a subsection with
    content counts as content); collapse blank runs."""
    res = []
    for i, b in enumerate(blocks):
        if b["kind"] == "heading":
            has = False
            for c in blocks[i + 1:]:
                if c["kind"] == "heading" and c["level"] <= b["level"]:
                    break
                if c["kind"] not in ("blank", "heading"):
                    has = True
                    break
            if not has:
                continue
        if b["kind"] == "blank" and res and res[-1]["kind"] == "blank":
            continue
        res.append(b)
    while res and res[0]["kind"] == "blank":
        res.pop(0)
    return res


# ---------------------------------------------------------------- illustrations

def parse_illustration(text):
    d, key, err = {}, None, []
    for ln in text.split("\n"):
        m = re.match(r"^([a-z]+):\s*(.*)$", ln)
        if m and not ln.startswith((" ", "\t")):
            key = m.group(1)
            d[key] = m.group(2).strip()
        elif key and ln.strip() and ln.startswith((" ", "\t")):
            d[key] += " " + ln.strip()
        elif ln.strip():
            err.append("line not 'key: value'")
    for k in ILLUS_KEYS:
        if k not in d or (k != "args" and not d[k]):
            err.append(f"missing key {k}")
    if d.get("id") and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", d["id"]):
        err.append("bad id")
    if d.get("tool") and not re.fullmatch(r"[A-Za-z0-9_]+\.py", d["tool"]):
        err.append("bad tool")
    return d, "; ".join(err)


def tool_has_schematic(tool):
    p = os.path.join(HERE, tool)
    return tool in SCHEMATIC_TOOLS and os.path.isfile(p) and "--schematic" in open(p, encoding="utf-8").read()


def run_illustration(d, root, out):
    """Run the tool, in schematic mode only, into <out>/site/public/illustrations/<id>/. -> (gif name, error)."""
    dest = os.path.join(out, "site", "public", "illustrations", d["id"])
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    cmd = [sys.executable, "-I", os.path.join(HERE, d["tool"]), root] + shlex.split(d.get("args", "")) \
        + ["--schematic", "--out", dest]
    try:
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=ILLUS_TIMEOUT)
    except subprocess.TimeoutExpired:
        return None, "tool timed out"
    if r.returncode != 0:
        return None, "tool failed: " + ((r.stderr.strip() or r.stdout.strip() or "no output").split("\n")[-1][:160])
    gifs = sorted(f for f in os.listdir(dest) if f.endswith(".gif")) if os.path.isdir(dest) else []
    if not gifs or not os.path.isfile(os.path.join(dest, "index.html")):
        return None, "tool wrote no GIF or no step-through page"
    return gifs[0], ""


def illustration_block(page, b, root, out, allow, heading, run=True):
    """-> the blocks that replace an illustration block (possibly none)."""
    d, err = parse_illustration("\n".join(b["lines"][1:-1]))
    page.units += 1
    page.dropped += 1

    def gone(why, rule="illustration"):
        page.drops.append((heading, rule, "illustration", why))
        return []
    if err:
        return gone("block does not parse: " + err)
    if not tool_has_schematic(d["tool"]):
        return gone(f"{d['id']}: {d['tool']} has no schematic mode")
    if not run:
        return gone(f"{d['id']}: not run (--no-illustrations)")
    gif, e = run_illustration(d, root, out)
    if e:
        return gone(f"{d['id']}: {e}")
    page.dropped -= 1
    up = "../" * len(page.route.split("/")) if page.route != "index" else ""
    base = f"{up}illustrations/{d['id']}/"
    root_abs = f"/illustrations/{d['id']}/{gif}"      # root-absolute: the site's rehype step prefixes its base
    cap = []
    for s in split_sentences(d["caption"]):
        page.units += 1
        r = unit_fails(s, allow, pins=allow.pins.get(page.path, {}))
        if r:
            page.dropped += 1
            page.drops.append((heading, ",".join(sorted(r)), "caption sentence", s[:200]))
        else:
            cap.append(s)
    cap.append("Seed: illustrative, an input of our own. Every value shown is computed by our model, not observed "
               "in the game.")
    blank = {"kind": "blank", "lines": [""]}
    return [{"kind": "para", "lines": [f"![Animation: {d['id']}]({root_abs})"]}, blank,
            {"kind": "para", "lines": [f"[Step through {d['id']}]({base}index.html)"]}, blank,
            {"kind": "para", "lines": [" ".join(cap)]}]


# ---------------------------------------------------------------- link rewriting

def route_dir(route):
    return "" if route == "index" else route


def rewrite_links(text, page, by_path):
    here = os.path.dirname(page.path)

    def sub(m):
        label, target = m.group(1), m.group(2)
        if RE_ILLUS_LINK.match(target):
            return m.group(0)
        if not target or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target) or target.startswith("//"):
            return label
        if target.startswith("#"):
            return f"[{label}]({target})" if target[1:] in page.headings else label
        path, _, frag = target.partition("#")
        tgt = by_path.get(os.path.normpath(os.path.join(here, path)).replace(os.sep, "/"))
        if tgt is None or (tgt is page and not frag):
            return label
        rel = os.path.relpath(route_dir(tgt.route) or ".", route_dir(page.route) or ".")
        rel = "./" if rel == "." else rel + "/"
        return f"[{label}]({rel}{'#' + frag if frag and frag in tgt.headings else ''})"
    return RE_LINK.sub(sub, text)


# ---------------------------------------------------------------- build

def render_blocks(blocks):
    return "\n".join("\n".join(b["lines"]) for b in blocks).rstrip("\n") + "\n"


def redact(pg, blocks):
    """The redactor's pass over a page's blocks. Illustration fences pass through for the illustration step."""
    red, skip_level = [], None
    for b in blocks:
        k = b["kind"]
        if k == "heading":
            if skip_level is not None and b["level"] > skip_level:
                continue
            skip_level = None
            if re.match(r"(?i)open questions?\b", b["text"]):
                skip_level = b["level"]
                pg.drops.append((b["text"], "open-questions", "section", b["text"][:120]))
                continue
            t = redact_text(b["text"])
            b = dict(b, text=t, lines=["#" * b["level"] + " " + t])
        elif skip_level is not None:
            continue
        elif k == "fence" and b["info"] != "illustration":
            ls = b["lines"]
            if b["info"] != "mermaid":
                ls = [ls[0]] + [RE_ADDR_COL.sub(r"\1", x) for x in ls[1:-1]] + ls[-1:]
            b = dict(b, lines=[RE_SUB.sub("", x) for x in ls])
        elif k == "table":
            b = dict(b, lines=[redact_text(x) for x in redact_table(b["lines"])])
        elif k in ("para", "item", "quote"):
            b = dict(b, lines=redact_text("\n".join(b["lines"])).split("\n"))
        red.append(b)
    return red


def build(out, manifest, root, date, allow, run_illus=True):
    out = safe_out(out)
    groups, specs, aliases = parse_manifest(manifest)
    shutil.rmtree(os.path.join(out, "site"), ignore_errors=True)
    if os.path.isfile(os.path.join(out, "report.txt")):
        os.remove(os.path.join(out, "report.txt"))
    pages = []
    for sp in specs:
        src = os.path.join(DOCS, sp["path"])
        pg = Page(sp)
        if not os.path.isfile(src):
            pg.drops.append(("", "missing", "page", f"{sp['path']} does not exist"))
            pages.append((pg, None))
            continue
        blocks = parse_blocks(strip_front_matter(open(src, encoding="utf-8").read().split("\n")))
        for i, b in enumerate(blocks):                       # the title: the first `# ` heading, removed
            if b["kind"] == "heading" and b["level"] == 1:
                pg.title = redact_text(b["text"])
                del blocks[i]
                break
        tr = unit_fails(pg.title, allow) if pg.title else {"notitle"}
        if tr:
            pg.drops.append(("", ",".join(sorted(tr)), "page", f"page dropped: title {pg.title!r}"))
            pages.append((pg, None))
            continue
        mid, heading = [], ""
        for b in redact(pg, blocks):
            if b["kind"] == "heading":
                heading = b["text"]
            if b["kind"] == "fence" and b["info"] == "illustration":
                mid.extend(illustration_block(pg, b, root, out, allow, heading, run_illus))
            else:
                mid.append(b)
        kept = simplify(pg, mid, allow)
        pg.headings = {slug(b["text"]) for b in kept if b["kind"] == "heading"}
        pages.append((pg, kept))
    by_path = {p.path: p for p, k in pages if k is not None}
    for src, dst in aliases:
        if src not in by_path and dst in by_path:
            by_path[src] = by_path[dst]
    docs_out = os.path.join(out, "site", "src", "content", "docs")
    for pg, kept in pages:
        if kept is None:
            continue
        title = pg.title.replace("\\", "\\\\").replace('"', '\\"')
        fm = f'---\ntitle: "{title}"\nsidebar:\n  order: {pg.spec["order"]}\n---\n\n'
        dest = os.path.join(docs_out, pg.route + ".md")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(fm + rewrite_links(render_blocks(kept), pg, by_path))
    cut = {"date": date, "groups": [{"slug": g["slug"], "label": g["label"]}
                                    for g in sorted(groups, key=lambda g: g["order"])]}
    with open(os.path.join(out, "site", "src", "cut.json"), "w", encoding="utf-8") as f:
        json.dump(cut, f, indent=2)
        f.write("\n")
    write_report(out, pages, date)
    return pages


def write_report(out, pages, date):
    rule_n, rows, lines = {}, [], []
    for pg, kept in pages:
        for h, r, kind, t in pg.drops:
            for x in r.split(","):
                rule_n[x] = rule_n.get(x, 0) + 1
            lines.append(f"DROP {pg.path} | {h or '-'} | {r} | {kind} | {t}")
        rows.append((pg.path, pg.units, pg.dropped, len(pg.drops), kept is None))
    with open(os.path.join(out, "report.txt"), "w", encoding="utf-8") as f:
        f.write(f"export_build report, cut {date}\n")
        f.write("drops per rule: " + ", ".join(f"{k} {v}" for k, v in sorted(rule_n.items())) + "\n")
        f.write("page | units | units dropped | share | report lines\n")
        for p, u, d, nl, gone in rows:
            f.write(f"{p} | {u} | {d} | {100.0 * d / u if u else 0:.1f}% | {nl}{' | PAGE DROPPED' if gone else ''}\n")
        f.write("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(WS, "export"))
    ap.add_argument("--manifest", default=os.path.join(DOCS, "export", "manifest.txt"))
    ap.add_argument("--root", default=os.path.join(WS, "merged"), help="the merged data tree the illustration tools read")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--allow-hex", default=os.path.join(DOCS, "export", "allow-hex.txt"))
    ap.add_argument("--no-illustrations", action="store_true")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"\d{4}-\d\d-\d\d", a.date):
        ap.error("--date is YYYY-MM-DD")
    try:
        allow = ec.load_allow(a.allow_hex) if os.path.isfile(a.allow_hex) else ec.Allow()
    except ValueError as e:
        print(f"export_build: {e}", file=sys.stderr)
        return 2
    ec.set_allow(allow)
    pages = build(a.out, a.manifest, os.path.realpath(a.root), a.date, allow, not a.no_illustrations)
    gone = sum(1 for _, k in pages if k is None)
    print(f"export_build: {len(pages) - gone} pages written ({gone} dropped), "
          f"{sum(len(p.drops) for p, _ in pages)} report lines, into {safe_out(a.out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

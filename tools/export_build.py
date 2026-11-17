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
  <out>/site/public/widgets/<id>/          each ```widget block (ADR-0037): widget.js, widget.json, widget.list.json, fallback picture
  <out>/report.txt                         every drop and every residue item (never published)
Nothing else is written. --out is refused unless it is workspace/export or workspace/export-<name>; the builder
renders no HTML and makes no network request (the export repository's CI draws the Mermaid fences).

Per page, in this order:
  1. redactor    front matter; *Open questions* sections; evidence parentheticals made only of anchors, run ids,
                 addresses and finding links; anchor-only table columns; the address column of pseudocode lines;
                 `sub_XXXXXXXX_` prefixes.
     anchor rewrite  inside any unit (sentence, list item, table cell, heading, caption sentence) before the simplifier
                 sees it: `fn:Name@0x...`, `data:`, `tbl:`, `fmt:` anchors become `Name` when the name is clean (no hex
                 run of 6+ digits, no `sub_`, no `DAT_`, nothing X1-X5 would fail), else the token goes; `struct:`
                 tokens, `run:` ids, finding ids, links into findings/ and `src:` ids go; a spec citation with a folder
                 (`drlg/maze.md § 3`) is reduced to `maze.md § 3` or removed; what the removal leaves (empty cell,
                 empty list or parenthetical, a dangling "at"/"see"/"per"/"of"/"in") is cleaned. A unit left with no
                 words is dropped (`empty`), and so is one whose removed token it can't read without: its head before a
                 colon, a possessive, the object of a preposition or determiner (`broken`). A citation into findings/,
                 plans/, adrs/ and the other working-tree folders is never reduced to its file name. Every rewrite is a
                 REWRITE report line (tab-separated: page, heading, before, after).
     second round (plan 0070 Phase 9): inside the same rewrite, a code-image address (`0x00...`, `@0x...`, a bare 8-digit or
                 6-digit hex in the image's range, a partial `0x0063xxxx`; one the page pins stays), a plan, ADR or lane
                 reference and a repository path or `.py`/`.csv`/`.log` name are removed as tokens, with the same `broken`
                 test (a removed subject, a token before a dash or `=`, a determiner or `run`/`using` before it); a cell
                 made only of them is an em dash, a statement cell they break drops its row. A `struct:Name+0x10` anchor
                 becomes `Name+0x10`. A pseudocode line's tail (`[C] (fn:..., run:...)`, `; ... 0x...`) is
                 rewritten, a comment left empty goes and the tag stays; a removed token in its code part leaves the
                 line as it was (the block then drops). An in-memory offset `Name+0x10` is content and stays.
                 Words and fenced blocks are counted per page and in the report (`words dropped`, `fenced blocks kept`).
  2. simplifier  runs export_check's text rules (X1-X5, X9, with the hex allowance) on each unit (a sentence of a
                 paragraph, a list item, a table row, a fenced block) and drops a unit that fails; a unit with an
                 `[L]` tag goes too. A section goes when its heading fails or nothing is left under it. It never
                 rewrites a word of a unit it keeps (the anchor rewrite above ran first). Every drop is a report line: page, heading, rule, text.
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
import hashlib
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
SCHEMATIC_TOOLS = ("maze_anim.py", "tc_anim.py", "rng_anim.py", "seedtree_anim.py")
ILLUS_KEYS = ("id", "tool", "args", "seed", "illustrates", "caption")
WIDGET_KEYS = ("id", "widget", "illustrates", "caption", "fallback")
WIDGETS_SRC = os.path.join(HERE, "widgets")        # tools/widgets/<name>/: the reviewed sources (tests override)

RE_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
RE_FENCE = re.compile(r"^(\s*)(```+|~~~+)\s*([\w-]*)")
RE_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")
RE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
RE_LINK = re.compile(r"(?<!!)\[((?:[^\[\]]|\[[^\]]*\])*)\]\(\s*<?([^)\s>]*)>?(?:\s+\"[^\"]*\")?\s*\)")
RE_WIDGET_LINK = re.compile(r"^/widgets/[\w-]+/widget\.js$")
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
    # an in-memory offset `ItemData+0x10` is content, not evidence (owner decision 2026-11-17, plan 0070 Phase 9)
]


# ---------------------------------------------------------------- manifest

def parse_manifest(path):
    groups, pages, aliases, tables = [], [], [], {}
    for raw in open(path, encoding="utf-8"):
        f = raw.split("#", 1)[0].split()
        if not f:
            continue
        if f[0] == "group" and len(f) >= 4:
            groups.append({"slug": f[1], "order": int(f[2]), "label": " ".join(f[3:])})
        elif f[0] == "page" and len(f) >= 4:
            # an optional fifth field names the route's last segment (a spec `README.md` reads `overview`; Phase 9)
            stem = f[4] if len(f) >= 5 else os.path.splitext(os.path.basename(f[1]))[0]
            pages.append({"path": f[1], "group": f[2], "order": int(f[3]),
                          "route": stem if f[2] == "-" else f"{f[2]}/{stem}"})
        elif f[0] == "alias" and len(f) >= 3:
            aliases.append((f[1], f[2]))        # a link to f[1] (not exported) goes to the page f[2] (Phase 6 review)
        elif f[0] == "table" and len(f) >= 3 and f[2].isdigit():
            tables.setdefault(f[1], set()).add(int(f[2]))   # the source line of the table's header row
    for p in pages:
        p["tables"] = tables.get(p["path"], set())
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


TABLE_LIMIT = ec.TABLE_LIMIT


def parse_blocks(lines, line0=1):
    """-> [dict(kind, lines, ...)]: heading, fence, table, item, quote, para, blank. A table also carries `line`,
    the source line of its header row (`line0` is the line number of lines[0]), which a manifest `table` line names."""
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
            blocks.append({"kind": "table", "lines": lines[i:j], "line": line0 + i})
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


RE_HAS_EVIDENCE = re.compile(r"\b(?:fn|data|struct|tbl|fmt|src|run):|0x[0-9A-Fa-f]{6}|findings/|[a-z]+/\d{4}")


RE_TAG_BEFORE = re.compile(r"\[[CI]\][ \t]*(?:\n[ \t]*)?$")


def drop_evidence_parens(text, strict=False):
    """`strict` (pseudocode lines): only a parenthetical that holds a real evidence token goes, never `(and)`."""
    out, last = [], 0
    for s, e in parenthetical_spans(text):
        inner = text[s + 1:e - 1]
        # a parenthetical right after a `[C]`/`[I]` tag is the tag's evidence: when it fails a text rule (a tool name, an
        # address, a run or a path in it), it goes whole and the statement stays (plan 0070 Phase 9 review)
        after_tag = bool(RE_TAG_BEFORE.search(text, 0, s)) and bool(inner.strip()) \
            and bool(ec.text_rules(rewrite_text(inner, plain=True, lenient=True).replace(BROKEN, ""), ()))
        if after_tag or inner.strip() and evidence_only(inner) and (not strict or RE_HAS_EVIDENCE.search(inner)):
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


def redact_text(text, rw=None, sub=True):
    """Evidence parentheticals and "See <path link>." sentences go; `rw` (the anchor rewrite) runs next, then the
    `sub_XXXXXXXX_` prefixes go (after it, so `fn:sub_..._x` is removed whole, not turned into `x`)."""
    t = drop_evidence_parens(text)
    if RE_SEE_PATHS.search(t):
        t = re.sub(r"[ \t]+$", "", RE_SEE_PATHS.sub("", t), flags=re.M)
    if rw:
        t = rw(t)
    return RE_SUB.sub("", t) if sub else t


# ---------------------------------------------------------------- anchor rewrite (Phase 9 prerequisite)

SENT = "\x00"           # marks where a token was removed, so the clean-up touches only what the removal left
BROKEN = "\x01"         # rewrite_text's result for a unit whose removed token was a part it can't read without
_NAME = r"[A-Za-z0-9_](?:[\w.:]*\w)?"
_OPEN = r"(?:(?<![\w`/])(`)|(?<![\w`/]))"
RE_ANCHOR = re.compile(_OPEN + r"(?:fn|data|tbl|fmt):(" + _NAME + r")(?:@0x[0-9A-Fa-f]+)?(?(1)`)")
# a struct anchor is an in-memory offset, content since the owner's decision (2026-11-17; review of lane/x70b2):
# `struct:Unit+0x20` -> `Unit+0x20`, as an anchor becomes its name; one with hex in its name or a 6+ digit offset goes
RE_STRUCT = re.compile(_OPEN + r"struct:([A-Za-z0-9_]+(?:\+0x[0-9A-Fa-f]+|\.\w+)*)(?(1)`)")
RE_REMOVE = re.compile(_OPEN + r"(?:run:[\w.-]*\w|src:[\w.-]*\w"
                       r"|[a-z]+/\d{4}(?!\d)(?:-[\w-]*\w)?(?:\.md)?(?:#[\w-]+)?)(?(1)`)")
# a spec citation with a folder: `drlg/maze.md § 3` -> `maze.md § 3`; without a section it goes (with a "spec" before it)
RE_CITE = re.compile(r"(?<![\w/.:~-])(?:\bspec\s+)?(`)?(?:\.\./|\./)*(?:[\w.-]+/)+([\w.-]+\.md)(?(1)`)", re.I)
RE_README = re.compile(r"(?<![\w/.:~-])(?:\bspec\s+)?(`)?README\.md(?(1)`)(?!\s*§)")
RE_AT = re.compile(r"(?i)(?:[ \t]*\n[ \t]*)?\bat\s+\x00")             # "at 0x..." goes with its address
RE_DANGLE = re.compile(r"(?i)\b(?:at|see|per|and|or|of|from|in|by|via|as|cf)\b"
                       r"[\s,;:]*\x00(?=\s*(?:[.,;:)\]|]|$))", re.M)
# a removed token the unit can't do without (review of lane/x70a): the unit's head before a colon, a possessive
# ("'s"), the object of a preposition or a determiner with words after it, a label whose whole list went
_LEAD = r"^[\s>*+-]*(?:\d+\.\s+)?(?:\*\*)?"
RE_BROKEN = re.compile(_LEAD + r"\x00\s*:|\x00\s*['\u2019]s\b|" + _LEAD + r"\x00\s*(?=[A-Za-z`(])|\x00\s*[\u2013\u2014=]"
                       r"|(?i:\b(?:run|runs|running|using|uses?|above|below|past|until|beyond|after|before|near|outside|inside|within)\s+\x00)"
                       r"|(?i:\b(?:of|from|in|by|via|at|as|per|see|cf)\s+\x00[\s\x00]*(?=[\w`(\[]))"
                       r"|(?i:\b(?:with|to|under|on|for|into|through|between|than|the|a|an|its|their|each|every|this"
                       r"|that|these|those|is|are|was|were|be)\s+\x00)"
                       r"|\w:\s*\x00[\s\x00]*[.;]?\s*$|\w:\s*\x00\s*[;,:]|\x00[ \t]*\((?!\s*\x00)")
# Phase 9 second round: code-image addresses, partial addresses, plan/ADR/lane references and repository paths or tool
# and data file names are removed as tokens (the `broken` test below drops a unit that can't be read without one)
_ADDR = (r"@?0x[0-9A-Fa-f]{6,8}\b|@?0x(?:00)?[4-9][0-9A-Fa-f]{0,5}[xX?]+[0-9A-Fa-f]*\b"
         r"|(?<![A-Za-z0-9._])(?:00[4-9][0-9]{5}|(?=[0-9A-Fa-f]*[0-9])(?=[0-9A-Fa-f]*[A-Fa-f])[0-9A-Fa-f]{6,8})(?![\w.])")
RE_ADDR = re.compile(r"(?<![\w+/@])(?:" + _ADDR + ")")
RE_ADDR_SPAN = re.compile(r"`\x00(?:\s*[\u2013\u2014-]\s*\x00)*`")
RE_ADDR_RANGE = re.compile(r"\x00(?:\s*[\u2013\u2014-]\s*\x00)+")
RE_PLAN = re.compile(_OPEN + r"(?:(?:\u00a7\s*)?\b(?i:plans?)\s+\d{4}(?:\s*(?:,|and|/)\s*\d{4})*(?:\s+(?:Phase|phase|P)\s*\d+[a-z]?(?:\.\d+)?)?"
                     r"(?:\s+batch\s+\w+(?:\s+rows?\s+\d+)?)?"
                     r"|\bADR-\d+(?:\s*\u00a7\s*[\w.]+)?|(?<![A-Za-z0-9])lane/[\w-]+)(?(1)`)")
_PATH = (r"(?:(?:\.\./|\./)*(?<![\w/])(?:docs|re|tools|workspace|\.claude)/[\w./~-]*[\w/]|(?<![\w/.-])[\w-]+\.(?:py|csv|log)\b"
         r"|(?<![\w])\.claude\b)")
RE_PATH_SPAN = re.compile(r"`[^`\n]*?" + _PATH + r"[^`\n]*`")
RE_PATH = re.compile(_PATH)
# an address the page pins (a computed value, never an address of the image) stays: set by the builder per page
PAGE_PINS = {}
# working-tree folders: a citation into them is never reduced to its file name (review of lane/x70a)
RE_WORK_SEG = re.compile(r"(?:^|[/`\s])(?:findings|plans|done|adrs|backlog|archive|re|tools|workspace|\.claude|skills"
                         r"|references|export)/")
RE_EMPTY_PAREN = re.compile(r"(?i)\((?=[^()]*\x00)(?:\b(?:at|see|per|and|or)\b|[\s,;:\x00])*\)")


def clean_name(name):
    if "sub_" in name or "DAT_" in name or re.search(r"[0-9A-Fa-f]{6,}", name):
        return False
    return not ec.text_rules("`" + name + "`")


def _anchor(m):
    return "`" + m.group(2) + "`" if clean_name(m.group(2)) else SENT


def _cite(m):
    if RE_WORK_SEG.search(m.group(0)) or re.match(r"\d", m.group(2)):
        # a finding, plan, ADR, backlog or tool file: its name is a tie to the working tree. Without a section it
        # goes like a finding id; with one the unit can't be read without it and drops (`broken`), check or no check.
        return BROKEN if re.match(r"\s*§", m.string[m.end():]) else SENT
    if re.match(r"\s*§", m.string[m.end():]):
        bt = "`" if m.group(1) else ""
        return bt + m.group(2) + bt
    return SENT


def _addr(m):
    t = m.group(0).lstrip("@")
    if re.search(r"[xX?]", t[2:] if t[:2].lower() == "0x" else t):
        return SENT                                       # a partial address, `0x0063xxxx`
    v = ec.hex_value(t)
    return SENT if ec.in_image(v) and v not in PAGE_PINS else m.group(0)


def _rw_plain(s, plain=False):
    s = RE_ANCHOR.sub((lambda m: m.group(2) if clean_name(m.group(2)) else SENT) if plain else _anchor, s)
    s = RE_STRUCT.sub((lambda m: m.group(2) if clean_name(m.group(2)) else SENT) if plain else _anchor, s)
    s = RE_REMOVE.sub(SENT, s)
    s = RE_CITE.sub(_cite, s)
    s = RE_README.sub(SENT, s)
    s = RE_PLAN.sub(SENT, s)
    s = RE_PATH_SPAN.sub(SENT, s)
    s = RE_PATH.sub(SENT, s)
    if "0x" in s or re.search(r"[0-9A-Fa-f]{6}", s):
        s = RE_ADDR.sub(_addr, s)
        s = RE_ADDR_SPAN.sub(SENT, s)
        s = RE_ADDR_RANGE.sub(SENT, s)
    return s


def _del_sent(m):
    s = m.string
    b = s[m.start() - 1] if m.start() > 0 else ""
    a = s[m.end()] if m.end() < len(s) else ""
    if m.group(0) == SENT or b in "(\n" or a in ")]\n.,;:!?":
        return ""
    return " "


def sent_cleanup(t, lenient=False):
    """What a removed token leaves behind: runs of separators, empty or dangling parentheticals, "see"/"at"/"per"
    before nothing, doubled spaces. Touches only the text next to a removal mark."""
    if lenient:
        t = t.replace(BROKEN, SENT)
    if BROKEN in t:
        return BROKEN
    if SENT not in t:
        return t
    for _ in range(3):
        t = re.sub(r"\x00(?:\s*(?:[,;]|\b(?:and|or)\b)\s*\x00)+", SENT, t)
        t = re.sub(r"\x00(?:[ \t]*\x00)+", SENT, t)
        t = RE_EMPTY_PAREN.sub(SENT, t)
        t = RE_AT.sub(SENT, t)
        t = RE_DANGLE.sub(SENT, t)
    if RE_BROKEN.search(t) and not lenient:
        return BROKEN
    t = re.sub(_LEAD.replace("^", "^(") + r")\x00\s*[,;]\s*", r"\1", t)        # a list's first slot went
    t = re.sub(r"((?:^|[\].!?*])[ \t]*)\x00\s*[,;]\s*", r"\1", t)          # after a tag or a sentence's end
    t = re.sub(r"\(\s*\x00\s*:\s*", "(", t)                                    # `(run:…: detail)` -> `(detail)`
    t = re.sub(r"[,;]\s*\x00(?=\s*[,;])", "", t)
    t = re.sub(r"\s*[,;]\s*\x00(?=\s*(?:[.)\]:]|$))", "", t, flags=re.M)
    t = re.sub(r"\(\s*\x00\s*[,;]\s*", "(", t)
    t = re.sub(r"[ \t]*\x00[ \t]*", _del_sent, t)
    return re.sub(r"[ \t]+$", "", t, flags=re.M)


def rewrite_text(text, plain=False, lenient=False):
    """The anchor rewrite over one unit's text (links: a link into findings/ goes whole, the target of any other
    stays, its label is rewritten). `plain`: anchors become bare names (pseudocode lines)."""
    out, last = [], 0
    for m in RE_LINK.finditer(text):
        out.append(_rw_plain(text[last:m.start()], plain))
        if "findings/" in m.group(2):
            out.append(SENT)
        else:
            lab = _rw_plain(m.group(1), plain)
            if lab.replace(SENT, "").strip():
                out.append(text[m.start():m.start(1)] + lab + text[m.end(1):m.end()])
            else:
                out.append(SENT)
        last = m.end()
    out.append(_rw_plain(text[last:], plain))
    return sent_cleanup("".join(out), lenient)


RE_TAIL = re.compile(r"\s{2,};\s|\s//\s|\s{2,}(?=\[[CI]\])|\s{2,}(?=\()")


def rewrite_fence_line(line):
    """A pseudocode line. Its code part (before a `;` comment, a `//` comment or the `[C]`/`[I]` tag, split at the first)
    is rewritten strictly: a removed token it cannot be read without leaves the line as it was (the block then fails
    the check and drops). Its tail (the tag, `(fn:..., run:...)`, `; ... 0x...`) is rewritten leniently: evidence
    parentheticals and anchors, addresses, runs and references go, a label or comment marker left with nothing goes, the
    tag stays."""
    m = RE_TAIL.search(line)
    code, tail = (line[:m.start()], line[m.start():]) if m else (line, "")
    if code.strip():
        c = rewrite_text(drop_evidence_parens(code, strict=True), plain=True)
        if BROKEN in c:
            return line
    else:
        c = code
    t = tail
    if t.strip():
        t = rewrite_text(drop_evidence_parens(t, strict=True), plain=True, lenient=True)
        if t != tail:
            t = re.sub(r"[ \t]*[:,;][ \t]*$", "", t)
            t = re.sub(r"[ \t]+(?://|;|#)[ \t]*$", "", t)
            t = re.sub(r"\(\s*\)", "", t).rstrip()
    return (c + t).rstrip() if (c != code or t != tail) else line


RE_TAG_CELL = re.compile(r"^\s*((?:\[[CI]\][ ,;]*)+?)\s*([^\s\[].*?)\s*$")


def rewrite_row(line, row_breaks=True):
    """A table row, cell by cell: a cell the rewrite empties becomes an em dash. A broken cell that carried a
    statement of its own (3+ words besides its anchors, and not opening with its evidence) makes the row broken: an em
    dash would read as "none"
    (review of lane/x70b2: "The collision test `0x0064FF90`'s result per crossed subtile" became `—`)."""
    if RE_SEP.match(line):
        return line
    cells, changed = split_row(line), False
    new = []
    for c in cells:
        m = RE_TAG_CELL.match(c)
        if m and ec.text_rules(rewrite_text(m.group(2), lenient=True).replace(BROKEN, ""), ()):
            # a cell that opens with its tag and goes on with evidence a text rule fails keeps the tag alone (Phase 9 review)
            changed = True
            new.append(m.group(1).strip(" ,;"))
            continue
        r = rewrite_text(c.strip())
        if r != c.strip():
            changed = True
            if row_breaks and BROKEN in r and not RE_EVID_START.match(c) and cell_words(c) >= 3:
                return BROKEN
            if BROKEN in r or not re.search(r"[A-Za-z0-9]", r):
                r = "—"
        new.append(r if r != c.strip() else c.strip())
    return "| " + " | ".join(new) + " |" if changed else line


# a cell that opens with its evidence (a tag, an anchor, a run id, an address) is an evidence cell: broken, it is a dash
RE_EVID_START = re.compile(r"\s*(?:\[[CIL]\]|\(?`?(?:(?:fn|data|struct|tbl|fmt|src|run):|@?0x[0-9A-Fa-f]{6}))")


def cell_words(c):
    """Words of a cell besides its evidence: anchors, links into findings/ and every removed token count none."""
    t = RE_LINK.sub(lambda m: "" if "findings/" in m.group(2) else m.group(1), drop_evidence_parens(c))
    t = _rw_plain(RE_ANCHOR.sub(SENT, t)).replace(SENT, " ")
    return len(re.findall(r"[A-Za-z][A-Za-z'-]*", t))


def has_words(t):
    return bool(re.search(r"[A-Za-z]", re.sub(r"\[[CIL]\]", "", t)))


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


def prose_words(text):
    """Words of body text: evidence tokens (anchors, run and finding ids, links into findings/, addresses, plan and
    ADR references, repository paths) are not words, an anchor counts as the name it becomes."""
    t = RE_LINK.sub(lambda m: "" if "findings/" in m.group(2) else m.group(1), text)
    t = _rw_plain(t).replace(SENT, " ")
    return len(re.findall(r"[A-Za-z][A-Za-z'-]*", t))


class Page:
    def __init__(self, spec):
        self.spec = spec
        self.path, self.route = spec["path"], spec["route"]
        self.title = ""
        self.drops = []          # (heading, rules, kind, text)
        self.rewrites = []       # (heading, before, after): units the anchor rewrite changed
        self.units = 0           # units seen: sentences, items, rows, quotes, fences, captions
        self.dropped = 0         # units dropped (children of a dropped item included)
        self.headings = set()
        self.dropped_page = False
        self.words = self.words_kept = 0        # words of the body text (fences not counted), source and kept
        self.fences = self.fences_kept = 0      # fenced blocks other than illustrations, source and kept

    @staticmethod
    def _count(blocks):
        w = f = 0
        for b in blocks:
            if b["kind"] == "fence":
                if b["info"] not in ("illustration", "widget") and not b.get("illus"):
                    f += 1
            elif b["kind"] != "blank" and not b.get("illus"):
                w += prose_words("\n".join(b["lines"]))
        return w, f

    def count_source(self, blocks):
        self.words, self.fences = self._count(blocks)

    def count_kept(self, blocks):
        self.words_kept, self.fences_kept = self._count(blocks)


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
                out.append(b if len(kept) == len(sents) else dict(b, lines=[" ".join(kept)]))
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
            if nbody > TABLE_LIMIT and b.get("line") not in page.spec.get("tables", ()):
                # X6: a table over the limit that no manifest `table` line names goes whole (Phase 9 review)
                page.dropped += nbody
                page.drops.append((heading, "X6", "table", f"{nbody} body rows, source line {b.get('line')}, "
                                   f"not named in the manifest: " + lines[0][:120]))
            elif nbody:
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


def caption_sentences(page, heading, caption, allow):
    """The caption's sentences that pass the redactor and the text rules, drops logged (illustrations, widgets)."""
    cap = []
    for s in split_sentences(caption):
        r0 = RE_SUB.sub("", rewrite_text(s))
        if r0 != s:
            note_rewrite(page, heading, s, r0)
            if not has_words(r0):
                note_empty(page, heading, "caption sentence", s, r0)
                continue
            s = r0
        page.units += 1
        r = unit_fails(s, allow, pins=allow.pins.get(page.path, {}))
        if r:
            page.dropped += 1
            page.drops.append((heading, ",".join(sorted(r)), "caption sentence", s[:200]))
        else:
            cap.append(s)
    return cap


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
    cap = caption_sentences(page, heading, d["caption"], allow)
    cap.append("Seed: illustrative, an input of our own. Every value shown is computed by our model, not observed "
               "in the game.")
    blank = {"kind": "blank", "lines": [""]}
    return [{"kind": "para", "lines": [f"![Animation: {d['id']}]({root_abs})"], "illus": True}, blank,
            {"kind": "para", "lines": [f"[Step through {d['id']}]({base}index.html)"], "illus": True}, blank,
            {"kind": "para", "lines": [" ".join(cap)], "illus": True}]


# ---------------------------------------------------------------- widgets (ADR-0037)

def parse_widget(text):
    d, err = {}, []
    key = None
    for ln in text.split("\n"):
        m = re.match(r"^([a-z]+):\s*(.*)$", ln)
        if m and not ln.startswith((" ", "\t")):
            key = m.group(1)
            d[key] = m.group(2).strip()
        elif key and ln.strip() and ln.startswith((" ", "\t")):
            d[key] += " " + ln.strip()
        elif ln.strip():
            err.append("line not 'key: value'")
    for k in WIDGET_KEYS:
        if not d.get(k):
            err.append(f"missing key {k}")
    if d.get("id") and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", d["id"]):
        err.append("bad id")
    if d.get("widget") and not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", d["widget"]):
        err.append("bad widget name")
    if d.get("fallback") and d["fallback"] != "text" and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", d["fallback"]):
        err.append("bad fallback")
    return d, "; ".join(err)


def _sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def widget_block(page, b, out, allow, heading):
    """-> the blocks that replace a ```widget block (possibly none). Copies tools/widgets/<widget>/widget.js and
    widget.json into <out>/site/public/widgets/<id>/ with the list file and the fallback image (the first picture of
    the illustration `fallback` names, built earlier in this cut) or, for `fallback: text`, writes the fixture's
    shown case as a table. The folder is verified with the publish check's X13 and removed when it fails."""
    d, err = parse_widget("\n".join(b["lines"][1:-1]))
    page.units += 1
    page.dropped += 1

    def gone(why, rule="widget"):
        page.drops.append((heading, rule, "widget", why))
        return []
    if err:
        return gone("block does not parse: " + err)
    wid, name = d["id"], d["widget"]
    src = os.path.join(WIDGETS_SRC, name)
    if not all(os.path.isfile(os.path.join(src, f)) for f in ("widget.js", "widget.json", "fixture.json")):
        return gone(f"{wid}: tools/widgets/{name}/ has no widget.js, widget.json and fixture.json")
    dest = os.path.join(out, "site", "public", "widgets", wid)
    if os.path.exists(dest):
        return gone(f"{wid}: id used twice in this cut")
    os.makedirs(dest)
    for f in ("widget.js", "widget.json"):
        shutil.copyfile(os.path.join(src, f), os.path.join(dest, f))
    table = None
    if d["fallback"] == "text":
        sys.path.insert(0, WIDGETS_SRC)
        import twins                                   # tools/widgets/twins.py: the fallback table of each widget
        fx = json.load(open(os.path.join(src, "fixture.json"), encoding="utf-8"))
        table = twins.fallback_table(name, fx)
        if not table:
            shutil.rmtree(dest)
            return gone(f"{wid}: no text fallback for the widget {name}")
        ext = None
    else:
        fdir = os.path.join(out, "site", "public", "illustrations", d["fallback"])
        pics = sorted(f for f in os.listdir(fdir) if f.endswith((".gif", ".png"))) if os.path.isdir(fdir) else []
        if not pics:
            shutil.rmtree(dest)
            return gone(f"{wid}: fallback illustration {d['fallback']} is not in the cut (place the widget block after it)")
        ext = os.path.splitext(pics[0])[1]
        shutil.copyfile(os.path.join(fdir, pics[0]), os.path.join(dest, "fallback" + ext))
    files = ["widget.js", "widget.json"] + (["fallback" + ext] if ext else [])
    with open(os.path.join(dest, "widget.list.json"), "w", encoding="utf-8") as f:
        json.dump({"marker": ec.WIDGET_MARKER, "files": {x: _sha_file(os.path.join(dest, x)) for x in files}}, f, indent=2)
        f.write("\n")
    probs, _ok = ec.verify_widget(dest, ec.git_identity(), WIDGETS_SRC)
    if probs:
        shutil.rmtree(dest)
        return gone(f"{wid}: fails X13: {probs[0][:160]}", "X13")
    page.dropped -= 1
    cap = caption_sentences(page, heading, d["caption"], allow)
    cap.append("Computed by our model of the rule, not observed in the game; the starting values are illustrative.")
    blank = {"kind": "blank", "lines": [""]}
    res = []
    if ext:
        res += [{"kind": "para", "lines": [f"![Widget fallback: {wid}](/widgets/{wid}/fallback{ext})"], "illus": True}, blank]
    else:
        head, rows, note = table
        res += [{"kind": "para", "lines": [note], "illus": True}, blank,
                {"kind": "table", "lines": ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
                 + ["| " + " | ".join(str(x) for x in r) + " |" for r in rows], "illus": True}, blank]
    res += [{"kind": "para", "lines": [" ".join(cap)], "illus": True}, blank,
            {"kind": "para", "lines": [f"[Try it: change the inputs (needs JavaScript)](/widgets/{wid}/widget.js)"], "illus": True}]
    return res


# ---------------------------------------------------------------- link rewriting

def route_dir(route):
    return "" if route == "index" else route


def rewrite_links(text, page, by_path):
    here = os.path.dirname(page.path)

    def sub(m):
        label, target = m.group(1), m.group(2)
        if RE_ILLUS_LINK.match(target) or RE_WIDGET_LINK.match(target):
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
        keep = frag and frag in tgt.headings and not ec.text_rules(frag)    # a slug that carries a seed fails the check
        return f"[{label}]({rel}{'#' + frag if keep else ''})"
    return RE_LINK.sub(sub, text)


# ---------------------------------------------------------------- build

def render_blocks(blocks):
    return "\n".join("\n".join(b["lines"]) for b in blocks).rstrip("\n") + "\n"


def _flat(t, n=160):
    return " ".join(t.split())[:n]


def note_rewrite(pg, heading, before, after):
    pg.rewrites.append((heading, _flat(before), "(dropped: broken)" if BROKEN in after else _flat(after)))


def note_empty(pg, heading, kind, before, after=""):
    """A unit the rewrite left with no words (`empty`), or one whose removed token was a part it can't read without
    (`broken`): dropped, and counted like any other drop."""
    pg.units += 1
    pg.dropped += 1
    pg.drops.append((heading, "broken" if BROKEN in after else "empty", kind, _flat(before, 200)))


def rewrite_sentences(pg, heading, text, kind="sentence"):
    """Per sentence: the anchor rewrite and the `sub_` strip. -> the text, or None when nothing changed."""
    sents = split_sentences(text)
    new, changed = [], False
    for s in sents:
        r = RE_SUB.sub("", rewrite_text(s))
        if r == RE_SUB.sub("", s):
            new.append(s)
            continue
        changed = True
        note_rewrite(pg, heading, s, r)
        if has_words(r):
            new.append(r)
        else:
            note_empty(pg, heading, kind, s, r)
    return " ".join(new) if changed else None


def redact(pg, blocks):
    """The redactor's pass over a page's blocks. Illustration fences pass through for the illustration step."""
    red, skip_level, heading = [], None, ""
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
            t0 = redact_text(b["text"])
            t = redact_text(b["text"], rw=lambda x: rewrite_text(x, lenient=True))   # a heading keeps its words
            if t != t0:
                note_rewrite(pg, heading, b["text"], t)
                if not has_words(t):
                    note_empty(pg, heading, "section", b["text"], t)
                    skip_level = b["level"]
                    continue
            heading = t
            b = dict(b, text=t, lines=["#" * b["level"] + " " + t])
        elif skip_level is not None:
            continue
        elif k == "fence" and b["info"] not in ("illustration", "widget"):
            ls = b["lines"]
            if b["info"] != "mermaid":
                ls = [ls[0]] + [RE_ADDR_COL.sub(r"\1", x) for x in ls[1:-1]] + ls[-1:]
                tail = [rewrite_fence_line(x) for x in ls[1:-1]]
                ch = [(x, y) for x, y in zip(ls[1:-1], tail) if x != y]
                if ch:
                    note_rewrite(pg, heading, ch[0][0].strip(), ch[0][1].strip() + (f"  (+{len(ch) - 1} lines)" if len(ch) > 1 else ""))
                ls = [ls[0]] + tail + ls[-1:]
            b = dict(b, lines=[RE_SUB.sub("", x) for x in ls])
        elif k == "table":
            rows = redact_table(b["lines"])
            lines = []
            for i, ln in enumerate(rows):
                pre = redact_text(ln, sub=False)
                r = RE_SUB.sub("", rewrite_row(pre, row_breaks=i >= 2)) if i != 1 else RE_SUB.sub("", pre)
                if i >= 2 and r != RE_SUB.sub("", pre):
                    note_rewrite(pg, heading, b["lines"][i], r)
                    if BROKEN in r:
                        note_empty(pg, heading, "row", b["lines"][i], r)
                        continue
                    if all(c.strip() in ("", "—") for c in split_row(r)):
                        note_empty(pg, heading, "row", b["lines"][i])
                        continue
                elif i == 0 and r != RE_SUB.sub("", pre):
                    note_rewrite(pg, heading, b["lines"][i], r)
                lines.append(r)
            if len(lines) <= 2:
                continue
            b = dict(b, lines=lines)
        elif k == "para":
            x = "\n".join(b["lines"])
            pre = redact_text(x, sub=False)
            new = rewrite_sentences(pg, heading, " ".join(l.strip() for l in pre.split("\n")))
            if new is None:
                b = dict(b, lines=redact_text(x).split("\n"))
            elif not new.strip():
                continue
            else:
                b = dict(b, lines=[new])
        elif k in ("item", "quote"):
            x = "\n".join(b["lines"])
            t0, t = redact_text(x), redact_text(x, rw=rewrite_text)
            if t != t0:
                note_rewrite(pg, heading, x, t)
                body = RE_ITEM.sub("", t.split("\n")[0], count=1) + " ".join(t.split("\n")[1:])
                if not has_words(body.lstrip("> ")):
                    note_empty(pg, heading, k, x, t)
                    continue
            b = dict(b, lines=t.split("\n"))
        red.append(b)
    return red


def build(out, manifest, root, date, allow, run_illus=True):
    global PAGE_PINS
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
        raw = open(src, encoding="utf-8").read().split("\n")
        body = strip_front_matter(raw)
        blocks = parse_blocks(body, line0=len(raw) - len(body) + 1)
        for ln in sorted(sp.get("tables", set()) - {b["line"] for b in blocks if b["kind"] == "table"}):
            pg.drops.append(("", "unmatched", "manifest", f"a `table` line names line {ln}, where no table starts"))
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
        PAGE_PINS = allow.pins.get(sp["path"], {})
        pg.count_source(blocks)
        for b in redact(pg, blocks):
            if b["kind"] == "heading":
                heading = b["text"]
            if b["kind"] == "fence" and b["info"] == "illustration":
                mid.extend(illustration_block(pg, b, root, out, allow, heading, run_illus))
            elif b["kind"] == "fence" and b["info"] == "widget":
                mid.extend(widget_block(pg, b, out, allow, heading))
            else:
                mid.append(b)
        kept = simplify(pg, mid, allow)
        pg.count_kept(kept)
        pg.headings = {slug(b["text"]) for b in kept if b["kind"] == "heading"}
        pages.append((pg, kept))
    for pg, kept in pages:
        pg.dropped_page = kept is None
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
        for h, before, after in pg.rewrites:
            lines.append("\t".join(("REWRITE", pg.path, h or "-", before.replace("\t", " "), after.replace("\t", " "))))
        rows.append(pg)

    def pct(a, b):
        return 100.0 * a / b if b else 0.0

    def tot(sel):
        ps = [p for p in rows if sel(p)]
        u, d = sum(p.units for p in ps), sum(p.dropped for p in ps)
        w, wk = sum(p.words for p in ps), sum(p.words_kept for p in ps)
        f, fk = sum(p.fences for p in ps), sum(p.fences_kept for p in ps)
        return (f"{len(ps)} pages: units dropped {d}/{u} ({pct(d, u):.1f}%), words dropped {w - wk}/{w} "
                f"({pct(w - wk, w):.1f}%), fenced blocks kept {fk}/{f}")
    with open(os.path.join(out, "report.txt"), "w", encoding="utf-8") as f:
        f.write(f"export_build report, cut {date}\n")
        f.write("drops per rule: " + ", ".join(f"{k} {v}" for k, v in sorted(rule_n.items())) + "\n")
        f.write(f"rewrites: {sum(len(pg.rewrites) for pg in rows)}\n")
        f.write("total: " + tot(lambda p: True) + "\n")
        if any(p.path.startswith("specs/") for p in rows):
            f.write("specs: " + tot(lambda p: p.path.startswith("specs/")) + "\n")
        f.write("page | units | units dropped | share | words | words dropped | share | fenced blocks kept/total | report lines\n")
        for p in rows:
            gone = " | PAGE DROPPED" if p.dropped_page else ""
            f.write(f"{p.path} | {p.units} | {p.dropped} | {pct(p.dropped, p.units):.1f}% | {p.words} | "
                    f"{p.words - p.words_kept} | {pct(p.words - p.words_kept, p.words):.1f}% | "
                    f"{p.fences_kept}/{p.fences} | {len(p.drops)}{gone}\n")
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
          f"{sum(len(p.drops) + len(p.rewrites) for p, _ in pages)} report lines "
          f"({sum(len(p.rewrites) for p, _ in pages)} rewrites), into {safe_out(a.out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

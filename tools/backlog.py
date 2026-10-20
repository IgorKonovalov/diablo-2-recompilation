#!/usr/bin/env python3
"""The backlog as one file per entry (ADR-0018): docs/backlog/YYYY-MM-DD-<from>-<to>-<slug>.md.
Open entries live in docs/backlog/, closed ones (done, moved, dropped) in docs/backlog/archive/ (ADR-0019).

    python3 -I tools/backlog.py new --from LANE --to LANE[,LANE] [--slug S] [--context PATH ...] [--text T]
    python3 -I tools/backlog.py list [--to LANE] [--from LANE] [--status open|done|moved|dropped|all]
    python3 -I tools/backlog.py close FILE [--status done|moved|dropped] --resolution TEXT
    python3 -I tools/backlog.py migrate [--dry-run]
    python3 -I tools/backlog.py archive [--no-migrate] [--dry-run]

Every command takes --root DIR (default: this checkout) and --today YYYY-MM-DD (default: today).

Entry file:

    ---
    from: reverser
    to: spec-writer, archivist
    date: 2026-10-17
    status: open
    context:
      - ../findings/items/0001-quality.md#3-the-roll
    resolution: ""
    ---

    The request. Later lanes add dated annotations below it, never edit it.

`context` holds repository links relative to docs/backlog/ (a block list, or `[]`); `resolution` is one
line, required once `status` is not `open`. String values may be written plain or as a JSON
(= YAML double-quoted) string.

migrate: the frozen archive docs/backlog.md keeps entries filed before the switch. Every unstruck entry
(`- [YYYY-MM-DD] from <lane> → <lane>: …`, with its indented continuation lines) moves to its own file, its
relative links rebased onto docs/backlog/, and the archive entry becomes one struck pointer line
(`- ~~[date] from a → b: <first 80 characters>…~~ Moved to [file](backlog/file).`). Safe to re-run after every lane merge:
  - an entry that already has a file (same date, lanes and first 60 characters of the request, link
    targets and ~~ ignored) is not moved twice; text a later merge added to it becomes a dated annotation;
  - a struck archive entry whose file exists (a lane struck it in place) closes the file: status done,
    its resolution text, then the archive copy becomes the pointer (or is dropped when a pointer is
    already there, e.g. after a merge kept both sides);
  - a closed file is never reopened; struck entries with no file stay in the archive untouched.
archive (ADR-0019): the post-merge sweep, idempotent. Runs migrate first (unless --no-migrate), then
moves every closed entry still in docs/backlog/ into docs/backlog/archive/ (a lane on an older branch
closed it in place) and every open entry found in archive/ back out, with `git mv` when the file is
tracked. Then it rewrites relative links so they resolve again: links from any .md under docs/, re/,
.claude/ or the root (and entry `context` items) that point at an entry's old place, and a moved entry's
own links (one more or one fewer `../`). An entry link that does not resolve from where the entry sits but
does from the other folder (an annotation written on an old branch) is healed the same way. `close` moves
the entry it closes the same way.

Stdlib only.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

LANES = ("architect", "archivist", "reverser", "spec-writer", "human")
STATUSES = ("open", "done", "moved", "dropped")
KEYS = ("from", "to", "date", "status", "context", "resolution")
REQUIRED = ("from", "to", "date", "status")

ARCHIVE = "docs/backlog.md"
DIR = "docs/backlog"
ARCHIVED = "docs/backlog/archive"   # closed entries (ADR-0019)
INDEX = "README.md"          # docs/backlog/README.md: the format note, not an entry

RE_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
RE_FILENAME = re.compile(r"(\d{4}-\d{2}-\d{2})-[a-z0-9+-]+\.md")
RE_HEADER = re.compile(r"\[(\d{4}-\d{2}-\d{2})\] from (.+?) → (.+?):(?=\s|$)")
RE_ENTRY_START = re.compile(r"^(?:- )?(?:~~)?\[\d{4}-\d{2}-\d{2}\] from ")
RE_POINTER = re.compile(r"^- ~~\[\d{4}-\d{2}-\d{2}\][^~]*~~ Moved to \[[^\]]*\]\(backlog/(?:archive/)?([^/)#\s]+\.md)\)\.?\s*$")
RE_LINK = re.compile(r"(\]\()(\s*<?)([^)\s>]+)")
RE_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
KEY_CHARS = 60
POINTER_CHARS = 80


def default_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------- front matter

def parse_entry(text):
    """-> (fields dict, body, [(lineno, message)]). Fields hold str values; `to` and `context` lists."""
    errs = []
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text, [(1, "no front matter (the file must start with ---)")]
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, text, [(1, "front matter not closed by ---")]
    fields, i = {}, 1
    while i < end:
        n, line = i + 1, lines[i]
        i += 1
        if not line.strip():
            continue
        m = re.match(r"^([a-z_]+):(?:\s+(.*?))?\s*$", line)
        if not m:
            errs.append((n, f"malformed front-matter line {line!r}"))
            continue
        key, raw = m.group(1), m.group(2) or ""
        if key not in KEYS:
            errs.append((n, f"unknown key {key!r} (allowed: {', '.join(KEYS)})"))
            continue
        if key in fields:
            errs.append((n, f"duplicate key {key!r}"))
            continue
        if key == "context":
            if raw in ("", "[]"):
                items = []
                while i < end and re.match(r"^\s+-\s+", lines[i]):
                    items.append(lines[i].split("-", 1)[1].strip())
                    i += 1
            elif raw.startswith("[") and raw.endswith("]"):
                items = [x.strip() for x in raw[1:-1].split(",") if x.strip()]
            else:
                errs.append((n, "context: expected a block list of `  - path` lines or `[]`"))
                continue
            vals = []
            for it in items:
                try:
                    vals.append(unquote_value(it))
                except ValueError as e:
                    errs.append((n, f"context item {it!r}: {e}"))
            fields[key] = vals
            continue
        try:
            val = unquote_value(raw)
        except ValueError as e:
            errs.append((n, f"{key}: {e}"))
            continue
        if key == "to":
            fields[key] = [x.strip() for x in val.split(",") if x.strip()]
        else:
            fields[key] = val
    body = "\n".join(lines[end + 1:])
    return fields, body, errs


def unquote_value(raw):
    raw = raw.strip()
    if raw.startswith('"'):
        try:
            v = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"bad double-quoted string ({e.msg})") from None
        if not isinstance(v, str):
            raise ValueError("not a string")
        return v
    if raw in ("null", "~"):
        return ""
    return raw


def quote_value(v):
    if v and re.fullmatch(r"[A-Za-z0-9.][A-Za-z0-9 ._/+,#-]*", v) and not v.endswith(" "):
        return v
    return json.dumps(v, ensure_ascii=False)


def render_entry(fields, body):
    out = ["---",
           f"from: {fields['from']}",
           f"to: {', '.join(fields['to'])}",
           f"date: {fields['date']}",
           f"status: {fields['status']}"]
    ctx = fields.get("context") or []
    if ctx:
        out.append("context:")
        out += [f"  - {quote_value(c)}" for c in ctx]
    else:
        out.append("context: []")
    out.append(f"resolution: {quote_value(fields.get('resolution') or '')}")
    out.append("---")
    return "\n".join(out) + "\n\n" + body.strip("\n") + "\n"


def check_entry(name, fields, errs):
    """Gate rule E13 on one parsed entry: -> [(lineno, message)] (parse errors first)."""
    out = list(errs)
    if not fields and errs:
        return out
    for k in REQUIRED:
        if not fields.get(k):
            out.append((1, f"missing or empty `{k}:`"))
    frm = fields.get("from")
    if frm and frm not in LANES:
        out.append((1, f"from: {frm!r} is not a lane ({', '.join(LANES)})"))
    for t in fields.get("to") or []:
        if t not in LANES:
            out.append((1, f"to: {t!r} is not a lane ({', '.join(LANES)})"))
    st = fields.get("status")
    if st and st not in STATUSES:
        out.append((1, f"status: {st!r} is not one of {', '.join(STATUSES)}"))
    if st and st != "open" and not (fields.get("resolution") or "").strip():
        out.append((1, f"status {st} without a `resolution:`"))
    if st == "open" and (fields.get("resolution") or "").strip():
        out.append((1, "status open with a resolution (close it, or empty the resolution)"))
    date = fields.get("date")
    m = RE_FILENAME.fullmatch(name)
    if not m:
        out.append((1, f"file name {name!r} is not YYYY-MM-DD-<from>-<to>-<slug>.md (lower case)"))
    elif date and date != m.group(1):
        out.append((1, f"date {date} does not match the file name's {m.group(1)}"))
    if date and not RE_DATE.fullmatch(date):
        out.append((1, f"date {date!r} is not YYYY-MM-DD"))
    return out


# ---------------------------------------------------------------- archive parsing

class Block:
    """A run of archive lines: kind 'entry' (with its continuation lines), 'blank' or 'other'."""

    def __init__(self, kind, lines, lineno):
        self.kind, self.lines, self.lineno = kind, lines, lineno

    @property
    def text(self):
        return "\n".join(self.lines)

    def struck(self):
        return self.lines[0].startswith(("- ~~[", "~~["))

    def pointer(self):
        m = RE_POINTER.match(self.lines[0]) if len(self.lines) == 1 else None
        return m.group(1) if m else None


def parse_archive(text):
    """-> (preamble lines, [Block]). An entry starts at column 0 with `- [date] from`, `- ~~[date] from`
    or `~~[date] from`; indented non-blank lines continue it."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    pre, blocks, i = [], [], 0
    while i < len(lines) and not RE_ENTRY_START.match(lines[i]):
        pre.append(lines[i])
        i += 1
    while i < len(lines):
        line, start = lines[i], i
        if RE_ENTRY_START.match(line):
            i += 1
            while i < len(lines) and lines[i][:1] in (" ", "\t") and lines[i].strip():
                i += 1
            blocks.append(Block("entry", lines[start:i], start + 1))
        else:
            blocks.append(Block("blank" if not line.strip() else "other", [line], start + 1))
            i += 1
    return pre, blocks


def entry_body(block):
    """The entry text without the list marker, continuation lines dedented by two."""
    first = block.lines[0]
    first = first[2:] if first.startswith("- ") else first
    rest = [ln[2:] if ln.startswith("  ") else ln.lstrip() for ln in block.lines[1:]]
    return "\n".join([first] + rest)


def split_struck(body):
    """A struck entry `~~request~~ resolution` -> (request, resolution); unstruck -> (body, None)."""
    if not body.startswith("~~"):
        return body, None
    end = body.find("~~", 2)
    if end < 0:
        return body[2:], ""
    return body[2:end], body[end + 2:].strip()


def collapse(s):
    return re.sub(r"\s+", " ", s).strip()


def norm(s):
    """For comparison: no ~~, no link targets, whitespace collapsed."""
    s = s.replace("~~", "")
    s = re.sub(r"\]\([^)]*\)", "]", s)
    return collapse(s)


def header(request):
    """-> (date, from text, to text, rest) or None."""
    m = RE_HEADER.match(request.lstrip())
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3), request.lstrip()[m.end():]


def entry_key(request):
    h = header(norm(request))
    if not h:
        return None
    date, frm, to, rest = h
    return f"{date}|{frm.strip()}|{to.strip()}|{rest.strip()[:KEY_CHARS]}"


def lanes_of(text):
    """Lane names in a header's from or to text: `reverser (harness, 1 slot)`, `architect (+human)`,
    `reverser (plan 0030 Phase 2), spec-writer`, `human (owner)`."""
    plus = re.findall(r"\(\+([a-z-]+)\)", text)
    bare = re.sub(r"\([^)]*\)", " ", text)
    found = []
    for w in re.findall(r"[a-z][a-z-]*", bare) + plus:
        if w in LANES and w not in found:
            found.append(w)
    return found


# ---------------------------------------------------------------- links

def rebase_links(text, src_dir="docs", dst_dir=DIR):
    """Rewrite relative markdown link targets written from src_dir so they resolve from dst_dir."""
    def fix(m):
        t = m.group(3)
        if RE_SCHEME.match(t) or t.startswith(("/", "//")):
            return m.group(0)
        path, sep, frag = t.partition("#")
        if not path:
            new = os.path.relpath(ARCHIVE, dst_dir).replace(os.sep, "/") + "#" + frag
        else:
            target = os.path.normpath(os.path.join(src_dir, path))
            new = os.path.relpath(target, dst_dir).replace(os.sep, "/") + (sep + frag if sep else "")
        return m.group(1) + m.group(2) + new
    return RE_LINK.sub(fix, text)


def link_targets(text):
    out = []
    for m in RE_LINK.finditer(text):
        t = m.group(3)
        if RE_SCHEME.match(t) or t.startswith(("/", "//")):
            continue
        if t not in out:
            out.append(t)
    return out


# ---------------------------------------------------------------- entry files

def slugify(text, words=6):
    s = re.sub(r"\]\([^)]*\)", "]", text)
    s = re.sub(r"[`*_~\[\]]", "", s).lower()
    toks = re.findall(r"[a-z0-9]+", s)[:words]
    slug = "-".join(toks)[:50].strip("-")
    return slug or "entry"


def file_name(date, frm, to, slug):
    return f"{date}-{frm}-{'+'.join(to)}-{slug}.md"


def unique_path(root, name):
    base, n = name[:-3], 1
    while any(os.path.exists(os.path.join(root, d, name)) for d in (DIR, ARCHIVED)):
        n += 1
        name = f"{base}-{n}.md"
    return name


def _md_names(d):
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if f.endswith(".md") and f != INDEX
                  and os.path.isfile(os.path.join(d, f)))


def entry_files(root):
    """Entry names in docs/backlog/ itself (the open ones, once swept)."""
    return _md_names(os.path.join(root, DIR))


def archived_files(root):
    """Entry names in docs/backlog/archive/."""
    return _md_names(os.path.join(root, ARCHIVED))


def entry_locations(root):
    """-> {name: repo-relative path} for every entry, docs/backlog/ first (it wins on a duplicate name)."""
    out = {}
    for d, names in ((DIR, entry_files(root)), (ARCHIVED, archived_files(root))):
        for n in names:
            out.setdefault(n, f"{d}/{n}")
    return out


def entry_path(root, name):
    """Absolute path of entry `name`, wherever it sits (docs/backlog/ when it does not exist yet)."""
    rel = entry_locations(root).get(name, f"{DIR}/{name}")
    return os.path.join(root, rel)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def first_paragraph(body):
    para = []
    for ln in body.strip("\n").split("\n"):
        if not ln.strip():
            break
        para.append(ln)
    return "\n".join(para)


def load_entries(root):
    """-> {name: (fields, body)} for every entry file, open and archived."""
    out = {}
    for name, rel in sorted(entry_locations(root).items()):
        fields, body, _ = parse_entry(read(os.path.join(root, rel)))
        out[name] = (fields, body)
    return out


# ---------------------------------------------------------------- migrate

def pointer_line(request, name, sub=""):
    """sub: "" or "archive/", where the entry file sits under docs/backlog/."""
    h = header(norm(request))
    if not h:
        return f"- ~~{norm(request)[:80].replace('~', '')}…~~ Moved to [{name}](backlog/{sub}{name})."
    rest = h[3].strip().replace("~", "")
    rest = rest if len(rest) <= POINTER_CHARS else rest[:POINTER_CHARS].rstrip() + "…"
    return f"- ~~[{h[0]}] from {h[1]} → {h[2]}: {rest}~~ Moved to [{name}](backlog/{sub}{name})."


def annotation(today, old_first, new_request):
    """Text the archive copy holds beyond the file's request, or None."""
    new_f = rebase_links(new_request)
    a, b = collapse(old_first.replace("~~", "")), collapse(new_f.replace("~~", ""))
    if a == b or a.startswith(b):
        return None
    extra = b[len(a):].strip() if b.startswith(a) else b
    return f"*Annotation (archive copy, migrated {today}):* {extra}"


def migrate(root, today, dry_run=False, log=print):
    """-> dict of counts. See the module docstring."""
    apath = os.path.join(root, ARCHIVE)
    pre, blocks = parse_archive(read(apath))
    entries = load_entries(root)
    locs = entry_locations(root)
    by_key = {}
    for name, (fields, body) in entries.items():
        k = entry_key(first_paragraph(body))
        if k:
            by_key.setdefault(k, name)
    pointed = {b.pointer() for b in blocks if b.kind == "entry" and b.pointer()}
    counts = dict(moved=0, closed=0, annotated=0, deduped=0, kept_struck=0, pointers=len(pointed))
    changed_files = {}
    out_blocks = []
    for b in blocks:
        if b.kind != "entry" or b.pointer():
            out_blocks.append(b)
            continue
        body = entry_body(b)
        request, resolution = split_struck(body)
        key = entry_key(request)
        name = by_key.get(key) if key else None
        if name is None:
            if resolution is not None or key is None:
                if resolution is None:
                    log(f"warning: {ARCHIVE}:{b.lineno}: unstruck entry without a `[date] from a → b:` header, left")
                counts["kept_struck"] += 1
                out_blocks.append(b)
                continue
            # an unstruck entry with no file: move it
            date, frm, to, rest = header(collapse(request))
            fl, tl = lanes_of(frm), lanes_of(to)
            if len(fl) != 1 or not tl:
                log(f"warning: {ARCHIVE}:{b.lineno}: cannot read the lanes of `from {frm} → {to}`, left")
                out_blocks.append(b)
                continue
            text = rebase_links(request)
            links = link_targets(text)
            ci = request.rfind("Context:")
            ctx = link_targets(rebase_links(request[ci:])) if ci >= 0 else links[:5]
            fields = dict({"from": fl[0], "to": tl, "date": date, "status": "open",
                           "context": ctx, "resolution": ""})
            name = unique_path(root, file_name(date, fl[0], tl, slugify(rest)))
            changed_files[name] = (fields, text)
            entries[name] = (fields, text)
            by_key[key] = name
            counts["moved"] += 1
            log(f"moved   {ARCHIVE}:{b.lineno} -> {DIR}/{name}")
        else:
            fields, fbody = changed_files.get(name) or entries[name]
            fields = dict(fields)
            note = annotation(today, first_paragraph(fbody), request)
            if note and note not in fbody:
                fbody = fbody.rstrip("\n") + "\n\n" + note + "\n"
                counts["annotated"] += 1
                log(f"annotated {DIR}/{name} from {ARCHIVE}:{b.lineno}")
            if resolution is not None and fields.get("status") == "open":
                fields["status"] = "done"
                fields["resolution"] = collapse(rebase_links(resolution)) or "struck in the archive with no text"
                counts["closed"] += 1
                log(f"closed  {DIR}/{name} (struck in {ARCHIVE}:{b.lineno})")
            if (fields, fbody) != entries[name]:
                changed_files[name] = (fields, fbody)
                entries[name] = (fields, fbody)
        if name in pointed:
            counts["deduped"] += 1
            log(f"dropped {ARCHIVE}:{b.lineno}: a pointer to {name} is already there")
            continue
        pointed.add(name)
        sub = "archive/" if locs.get(name, "").startswith(ARCHIVED + "/") else ""
        out_blocks.append(Block("entry", [pointer_line(request, name, sub)], b.lineno))
    counts["pointers"] = len(pointed)
    # drop blank runs left by removed entries
    lines = list(pre)
    for b in out_blocks:
        if b.kind == "blank" and lines and not lines[-1].strip():
            continue
        lines += b.lines
    new_archive = "\n".join(lines).rstrip("\n") + "\n"
    if not dry_run:
        for name, (fields, body) in changed_files.items():
            write(entry_path(root, name), render_entry(fields, body))
        if new_archive != read(apath):
            write(apath, new_archive)
    counts["files_written"] = len(changed_files)
    return counts


# ---------------------------------------------------------------- archive (ADR-0019)

LINK_DIRS = ("docs", "re", ".claude")    # trees whose .md files may link entries (plus root *.md)
RE_ENTRY_REL = re.compile(r"docs/backlog/(?:archive/)?([^/]+\.md)")


def is_closed(fields):
    return fields.get("status", "open") != "open"


def linking_files(root):
    """Repo-relative .md files whose links archive keeps resolving."""
    out = sorted(f for f in os.listdir(root) if f.endswith(".md") and os.path.isfile(os.path.join(root, f)))
    for top in LINK_DIRS:
        for dp, dns, fns in os.walk(os.path.join(root, top)):
            dns[:] = sorted(d for d in dns if d not in (".git", "workspace", "node_modules"))
            rel = os.path.relpath(dp, root).replace(os.sep, "/")
            out += [f"{rel}/{f}" for f in sorted(fns) if f.endswith(".md")]
    return out


def _git_tracked(root, rel):
    if not os.path.isdir(os.path.join(root, ".git")) and not os.path.isfile(os.path.join(root, ".git")):
        return False
    try:
        r = subprocess.run(["git", "-C", root, "ls-files", "--error-unmatch", "--", rel],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False
    return r.returncode == 0


def move_file(root, src, dst):
    """git mv when src is tracked, else a rename. src, dst repo-relative."""
    os.makedirs(os.path.dirname(os.path.join(root, dst)), exist_ok=True)
    if _git_tracked(root, src):
        subprocess.run(["git", "-C", root, "mv", "--", src, dst], check=True,
                       stdout=subprocess.DEVNULL)
    else:
        os.rename(os.path.join(root, src), os.path.join(root, dst))


def remap_target(root, old_rel, new_rel, target, locs, is_entry):
    """A relative link target written in the file that sat at old_rel and now sits at new_rel -> the
    target to write, or None to leave it as it is."""
    if not target or RE_SCHEME.match(target) or target.startswith(("/", "//", "#")):
        return None
    path, sep, frag = target.partition("#")
    lead = ""
    if path.startswith("<"):
        lead, path = "<", path[1:]
    tgt = os.path.normpath(os.path.join(os.path.dirname(old_rel), path)).replace(os.sep, "/")
    m = RE_ENTRY_REL.fullmatch(tgt)
    if m and m.group(1) in locs and locs[m.group(1)] != tgt:
        tgt = locs[m.group(1)]                         # an entry that moved
    elif is_entry and not os.path.exists(os.path.join(root, tgt)):
        other = ARCHIVED if os.path.dirname(old_rel) == DIR else DIR
        alt = os.path.normpath(os.path.join(other, path)).replace(os.sep, "/")
        m = RE_ENTRY_REL.fullmatch(alt)
        if m and m.group(1) in locs:
            alt = locs[m.group(1)]
        if os.path.exists(os.path.join(root, alt)):
            tgt = alt                                  # written as if the entry sat in the other folder
        elif old_rel == new_rel:
            return None
    elif old_rel == new_rel:
        return None
    new = os.path.relpath(tgt, os.path.dirname(new_rel)).replace(os.sep, "/")
    if new == path:
        return None
    return lead + new + (sep + frag if sep else "")


def rewrite_links_in(root, old_rel, new_rel, text, locs, is_entry):
    def fix(m):
        new = remap_target(root, old_rel, new_rel, m.group(3), locs, is_entry)
        return m.group(0) if new is None else m.group(1) + m.group(2) + new
    text = RE_LINK.sub(fix, text)
    if not is_entry or not text.startswith("---"):
        return text
    lines = text.split("\n")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    in_ctx = False
    for i in range(1, end or 0):
        if re.match(r"^context:", lines[i]):
            in_ctx = True
            continue
        if not in_ctx:
            continue
        m = re.match(r"^(\s+-\s+)(.*?)\s*$", lines[i])
        if not m:
            in_ctx = False
            continue
        try:
            val = unquote_value(m.group(2))
        except ValueError:
            continue
        new = remap_target(root, old_rel, new_rel, val, locs, True)
        if new is not None:
            lines[i] = m.group(1) + quote_value(new)
    return "\n".join(lines)


def archive(root, dry_run=False, only=None, log=print):
    """Move closed entries into docs/backlog/archive/ and open ones out of it, then rewrite the links.
    only: entry names to consider (default all). -> dict of counts."""
    locs = entry_locations(root)
    moves = {}                                         # old rel -> new rel
    for name, rel in sorted(locs.items()):
        if only is not None and name not in only:
            continue
        fields, _, errs = parse_entry(read(os.path.join(root, rel)))
        if errs and not fields:
            log(f"warning: {rel}: {errs[0][1]}, left")
            continue
        want = f"{ARCHIVED if is_closed(fields) else DIR}/{name}"
        if want == rel:
            continue
        if os.path.exists(os.path.join(root, want)):
            log(f"warning: {rel}: {want} exists too, left")
            continue
        moves[rel] = want
    counts = dict(archived=sum(1 for v in moves.values() if v.startswith(ARCHIVED + "/")),
                  unarchived=sum(1 for v in moves.values() if not v.startswith(ARCHIVED + "/")),
                  links_files=0)
    for old, new in moves.items():
        log(f"{'archived' if new.startswith(ARCHIVED) else 'reopened'} {old} -> {new}")
    new_locs = dict(locs)
    for old, new in moves.items():
        new_locs[os.path.basename(new)] = new
    if not dry_run:
        for old, new in moves.items():
            move_file(root, old, new)
    back = {v: k for k, v in moves.items()}
    entry_rels = set(locs.values()) | set(new_locs.values())
    for rel in linking_files(root):
        if dry_run:                                    # files still sit at their old place
            old_rel, new_rel = rel, moves.get(rel, rel)
        else:
            old_rel, new_rel = back.get(rel, rel), rel
        is_entry = rel in entry_rels
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        text = read(path)
        out = rewrite_links_in(root, old_rel, new_rel, text, new_locs, is_entry)
        if out != text:
            counts["links_files"] += 1
            log(f"links   {new_rel}")
            if not dry_run:
                write(path, out)
    return counts


# ---------------------------------------------------------------- commands

def cmd_new(args):
    fields = {"from": args.frm, "to": [t.strip() for t in args.to.split(",") if t.strip()],
              "date": args.today, "status": "open", "context": args.context or [], "resolution": ""}
    errs = check_entry(file_name(args.today, args.frm, fields["to"], "x"), fields, [])
    if errs:
        for _, msg in errs:
            print(f"backlog new: {msg}", file=sys.stderr)
        return 2
    slug = slugify(args.slug or args.text or "", words=8)
    name = unique_path(args.root, file_name(args.today, args.frm, fields["to"], slug))
    body = args.text or "The request: what is needed, from whom, and why. Not blocking / blocking <what>."
    write(os.path.join(args.root, DIR, name), render_entry(fields, body))
    print(f"{DIR}/{name}")
    return 0


def cmd_list(args):
    n = 0
    for name, (fields, body) in load_entries(args.root).items():
        if args.status != "all" and fields.get("status") != args.status:
            continue
        if args.to and args.to not in (fields.get("to") or []):
            continue
        if args.frm and fields.get("from") != args.frm:
            continue
        n += 1
        summary = norm(first_paragraph(body))
        h = header(summary)
        summary = h[3].strip() if h else summary
        print(f"{DIR}/{name}\t{fields.get('status')}\t{fields.get('from')} → {', '.join(fields.get('to') or [])}"
              f"\t{summary[:100]}")
    print(f"{n} entries", file=sys.stderr)
    return 0


def cmd_close(args):
    path = args.file if os.path.isabs(args.file) else os.path.join(args.root, args.file)
    if not os.path.exists(path):
        path = entry_path(args.root, os.path.basename(args.file))
    fields, body, errs = parse_entry(read(path))
    if errs:
        print(f"backlog close: {path}: {errs[0][1]}", file=sys.stderr)
        return 2
    fields["status"] = args.status
    fields["resolution"] = collapse(args.resolution)
    write(path, render_entry(fields, body))
    name = os.path.basename(path)
    changed = []
    archive(args.root, only={name},
            log=lambda m: changed.append(m.split(None, 1)[1]) if m.startswith("links ") else None)
    new = os.path.relpath(entry_path(args.root, name), args.root)
    print(new)
    for rel in changed:                 # other files whose links now follow the entry: stage them too
        if rel != new:
            print(rel)
    return 0


def cmd_archive(args):
    if not args.no_migrate:
        cmd_migrate(args)
    c = archive(args.root, dry_run=args.dry_run)
    print("archive: " + ", ".join(f"{k} {v}" for k, v in c.items()) + (" (dry run)" if args.dry_run else ""))
    return 0


def cmd_migrate(args):
    c = migrate(args.root, args.today, dry_run=args.dry_run)
    print("migrate: " + ", ".join(f"{k} {v}" for k, v in c.items()) + (" (dry run)" if args.dry_run else ""))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=default_root())
    ap.add_argument("--today", default=datetime.date.today().isoformat())
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new", help="scaffold an entry file")
    p.add_argument("--from", dest="frm", required=True, choices=LANES)
    p.add_argument("--to", required=True, help="lane, or lanes separated by commas")
    p.add_argument("--slug")
    p.add_argument("--context", nargs="+", action="extend", metavar="PATH",
                   help="links relative to docs/backlog/, e.g. ../plans/0039-x.md#log")
    p.add_argument("--text", help="the request (default: a placeholder to edit)")
    p = sub.add_parser("list", help="list entries (default: open)")
    p.add_argument("--to")
    p.add_argument("--from", dest="frm")
    p.add_argument("--status", default="open", choices=STATUSES + ("all",))
    p = sub.add_parser("close", help="set status and resolution, move the entry into archive/")
    p.add_argument("file")
    p.add_argument("--status", default="done", choices=STATUSES[1:])
    p.add_argument("--resolution", required=True)
    p = sub.add_parser("migrate", help="move unstruck archive entries to files (idempotent)")
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("archive", help="migrate, then sweep closed entries into archive/ and fix links (idempotent)")
    p.add_argument("--no-migrate", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    args.root = os.path.abspath(args.root)
    if not RE_DATE.fullmatch(args.today):
        ap.error("--today must be YYYY-MM-DD")
    return {"new": cmd_new, "list": cmd_list, "close": cmd_close, "migrate": cmd_migrate,
            "archive": cmd_archive}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())

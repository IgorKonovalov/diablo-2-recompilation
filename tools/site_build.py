"""Build the local documentation site (ADR-0034) into workspace/site/ from the repository's Markdown.

Usage:
  python3 -I tools/site_build.py [<root>] [--only <glob>] [--no-illustrations] [--out DIR]
  python3 -I tools/site_build.py check [<docs-dir>]

<root> is the merged data tree (default workspace/merged); the illustration tools read it. The site holds
docs/wiki/, docs/specs/, docs/glossary.md and every other docs/ Markdown page they link, transitively, so that
every relative link between pages resolves (a link to anything that is not a built page, such as a file under
tools/ or re/, is shown as plain text). Open workspace/site/index.html from disk. Nothing is fetched: the pages
carry their own CSS (system fonts, light and dark through prefers-color-scheme) and no http(s) reference.

  --only GLOB         build only the pages whose docs-relative path matches GLOB (fnmatch, e.g. 'wiki/*'); the
                      link set, the index and the section pages are still computed from the whole set
  --no-illustrations  leave each ```illustration block as its note (no tool is run)
  --docs DIR          Markdown tree to build instead of docs/ (for tests)
  --out DIR           output directory; refused unless it is under workspace/ (anim_common.safe_out)

Mermaid: every ```mermaid block is drawn at build time by tools/site_mermaid.mjs, which runs the same pinned
Mermaid bundle (workspace/cache/mermaid-render/, fetched by the gate's E17) in the system's Chromium-family
browser, with no network. The SVGs are cached by sha256 of the block under workspace/cache/site-mermaid/. With
no Node, bundle or browser the block is shown as its source in a <pre> with a note.

Illustrations ("```illustration" blocks; ADR-0034): keys id, tool, args, seed, illustrates, caption. The builder
runs `python3 -I tools/<tool> <root> <args> --out workspace/site/illustrations/<id>/` and embeds the tool's
index.html (iframe) or, failing that, its GIF, with the caption, the seed label and the illustrated sections.
A missing tool or a failing run leaves the block's note and a visible warning on the page; the build goes on.
A run is skipped when the output directory's stamp (command line and tool mtime) is unchanged.

Widgets ("```widget" blocks; ADR-0037): keys id, widget, illustrates, caption, fallback. No script runs on the local site:
the block is drawn as its fallback, the named illustration's picture or, for `fallback: text`, the widget twin's table,
with the caption and a note that the interactive element is on the published site.

`check` is the gate's rule E19 for the blocks: every ```illustration block under docs/ parses (all six keys,
no unknown key), ids are unique, `tool` names a script in the tools/ beside the docs directory (this script's
tools/ when there is none), and every `illustrates` link resolves (file exists, #anchor is a heading of it). Every
```widget block parses (the export builder's parse_widget), its id is unique among widgets, `widget` names a folder
tools/widgets/<name>/ with a widget.js, its `fallback` is `text` or the id of an illustration block under docs/, and its
`illustrates` links resolve.
One line per problem, exit 1 when there is one; last line `CHECK illustrations: N blocks, M problems`.

Stdlib only. Everything written goes under workspace/ and never into git.
"""
import fnmatch
import hashlib
import html
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
REPO = os.path.dirname(HERE)
DOCS = os.path.join(REPO, "docs")
WS = os.path.join(REPO, "workspace")

import anim_common  # noqa: E402

FOOTER = "Built locally from your own game files; not to be shared."
ILLUS_KEYS = ("id", "tool", "args", "seed", "illustrates", "caption")
MERMAID_CACHE = os.path.join(WS, "cache", "site-mermaid")
BUNDLE_DIR = os.path.join(WS, "cache", "mermaid-render")
ILLUS_TIMEOUT = 600


# ---------------------------------------------------------------- Markdown: inline

def slugify(text):
    """GitHub heading anchor: lowercase, drop everything but letters, digits, space, hyphen and underscore, spaces to hyphens."""
    s = re.sub(r"[^\w\- ]", "", text.strip().lower(), flags=re.UNICODE)
    return s.replace(" ", "-")


def plain(md):
    """Heading text without inline markup, for the slug and the title."""
    s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", md)
    s = re.sub(r"[`*]", "", s)
    s = re.sub(r"(?<!\w)_|_(?!\w)", "", s)
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


class Ctx:
    """What the inline converter needs: the page's source path and the set of built pages."""

    def __init__(self, src, pages):
        self.src = src            # docs-relative path of the page being converted
        self.pages = pages        # set of docs-relative md paths that become pages
        self.broken = []


def href_for(ctx, target):
    """(href or None, kind). Relative .md links to built pages become .html links; anchors stay."""
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
        return None, "ext"
    path, _, frag = target.partition("#")
    if not path:
        return "#" + frag, "self"
    cand = os.path.normpath(os.path.join(os.path.dirname(ctx.src), path)).replace(os.sep, "/")
    hit = None
    if cand.endswith(".md") and cand in ctx.pages:
        hit = cand
    elif os.path.isdir(os.path.join(DOCS, cand)):
        for idx in (cand + "/README.md", cand + "/index.md"):
            if idx in ctx.pages:
                hit = idx
                break
    if hit:
        up = os.path.relpath(hit[:-3] + ".html", os.path.dirname(ctx.src) or ".").replace(os.sep, "/")
        return up + ("#" + frag if frag else ""), "page"
    return None, "none"


LINK_RE = re.compile(r"(!?)\[((?:[^\[\]]|\[[^\]]*\])*)\]\(\s*(<[^>]*>|[^()\s]*(?:\([^()]*\)[^()\s]*)*)(?:\s+\"[^\"]*\")?\s*\)")
CODE_RE = re.compile(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)", re.S)
ALLOWED_TAG = re.compile(r"<(br\s*/?|/?(?:sub|sup|kbd|b|i|em|strong))>", re.I)


def inline(s, ctx, stash=None):
    stash = [] if stash is None else stash

    def put(h):
        stash.append(h)
        return "\x00%d\x00" % (len(stash) - 1)

    s = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|<>~])", lambda m: put(html.escape(m.group(1))), s)
    s = CODE_RE.sub(lambda m: put("<code>%s</code>" % html.escape(m.group(2).strip() or m.group(2))), s)

    def link(m):
        bang, text, target = m.group(1), m.group(2), m.group(3).strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        if bang:
            return put('<span class="img" title="%s">[image: %s]</span>' % (html.escape(target), html.escape(plain(text))))
        label = inline(text, ctx, stash)
        href, kind = href_for(ctx, target)
        if kind in ("page", "self"):
            return put('<a href="%s">%s</a>' % (html.escape(href), label))
        if kind == "ext":
            return put('<span class="ext">%s <small>(%s)</small></span>' % (label, html.escape(target)))
        ctx.broken.append(target)
        return put('<span class="nolink" title="%s">%s</span>' % (html.escape(target), label))
    s = LINK_RE.sub(link, s)
    s = re.sub(r"<(https?://[^>\s]+)>", lambda m: put('<span class="ext">%s</span>' % html.escape(m.group(1))), s)
    s = ALLOWED_TAG.sub(lambda m: put("<" + re.sub(r"[\s/]+$", "", m.group(1)) + ">"), s)
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = html.escape(s, quote=False)
    s = re.sub(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1", r"<strong>\2</strong>", s, flags=re.S)    # emphasis may wrap a line
    s = re.sub(r"(?<![\w*])\*(?!\s|\*)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s, flags=re.S)
    s = re.sub(r"(?<![\w])_(?!\s|_)(.+?)(?<!\s)_(?![\w])", r"<em>\1</em>", s, flags=re.S)
    s = re.sub(r"(?<!~)~~(?=\S)(.+?)(?<=\S)~~(?!~)", r"<del>\1</del>", s, flags=re.S)
    for _ in range(6):
        if "\x00" not in s:
            break
        s = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], s)
    return s


# ---------------------------------------------------------------- Markdown: blocks

RE_FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([^`]*)$")
RE_HEAD = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
RE_HR = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
RE_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
RE_TSEP = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$")


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    cells, cur = [], ""
    i = 0
    while i < len(line):
        c = line[i]
        if c == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            cur += "|"
            i += 2
            continue
        if c == "`":
            j = re.match(r"`+", line[i:]).end() + i
            tick = line[i:j]
            k = line.find(tick, j)
            if k >= 0:
                cur += line[i:k + len(tick)]
                i = k + len(tick)
                continue
        if c == "|":
            cells.append(cur.strip())
            cur = ""
        else:
            cur += c
        i += 1
    cells.append(cur.strip())
    return cells


class Page:
    def __init__(self, src, text, pages):
        self.src = src
        self.ctx = Ctx(src, pages)
        self.title = None
        self.slugs = {}
        self.mermaid = []       # blocks, in order
        self.illus = []         # (dict, error, line)
        self.widgets = []       # (dict, error, line): ```widget blocks, shown as their fallback (ADR-0037)
        self.warnings = []
        self.body = self.render(text)

    def slug(self, text):
        s = slugify(text)
        n = self.slugs.get(s, 0)
        self.slugs[s] = n + 1
        return s if n == 0 else "%s-%d" % (s, n)

    def render(self, text):
        lines = text.replace("\r\n", "\n").split("\n")
        front = ""
        if lines and lines[0].strip() == "---":
            for j in range(1, len(lines)):
                if lines[j].strip() == "---":
                    front = '<details class="fm"><summary>Front matter</summary><pre>%s</pre></details>\n' % html.escape(
                        "\n".join(lines[1:j]))
                    lines = lines[j + 1:]
                    break
        return front + self.blocks(lines)

    def blocks(self, lines):
        out, i, n = [], 0, len(lines)
        while i < n:
            ln = lines[i]
            if not ln.strip():
                i += 1
                continue
            m = RE_FENCE.match(ln)
            if m:
                indent, fence, info = m.group(1), m.group(2), m.group(3).strip()
                close = re.compile(r"^\s*" + re.escape(fence[0]) + "{%d,}\\s*$" % len(fence))
                j = i + 1
                while j < n and not close.match(lines[j]):
                    j += 1
                body = [x[len(indent):] if x.startswith(indent) else x.lstrip() for x in lines[i + 1:j]]
                out.append(self.fenced(info, body, i + 1))
                i = j + 1
                continue
            m = RE_HEAD.match(ln)
            if m:
                lvl, txt = len(m.group(1)), m.group(2)
                slug = self.slug(plain(txt))
                if self.title is None and lvl == 1:
                    self.title = plain(txt)
                out.append('<h%d id="%s">%s</h%d>' % (lvl, slug, inline(txt, self.ctx), lvl))
                i += 1
                continue
            if RE_HR.match(ln):
                out.append("<hr>")
                i += 1
                continue
            if ln.lstrip().startswith("<!--"):
                while i < n and "-->" not in lines[i]:
                    i += 1
                i += 1
                continue
            if ln.lstrip().startswith(">"):
                j = i
                q = []
                while j < n and (lines[j].lstrip().startswith(">") or (lines[j].strip() and q and not self.starts_block(lines[j]))):
                    q.append(re.sub(r"^\s*>\s?", "", lines[j]) if lines[j].lstrip().startswith(">") else lines[j])
                    j += 1
                out.append("<blockquote>%s</blockquote>" % self.blocks(q))
                i = j
                continue
            if "|" in ln and i + 1 < n and RE_TSEP.match(lines[i + 1]) and "-" in lines[i + 1]:
                head = split_row(ln)
                aligns = []
                for c in split_row(lines[i + 1]):
                    aligns.append("center" if c.startswith(":") and c.endswith(":") else "right" if c.endswith(":") else "")
                j = i + 2
                rows = []
                while j < n and lines[j].strip() and "|" in lines[j]:
                    rows.append(split_row(lines[j]))
                    j += 1

                def cell(tag, txt, k):
                    al = aligns[k] if k < len(aligns) and aligns[k] else ""
                    return "<%s%s>%s</%s>" % (tag, ' style="text-align:%s"' % al if al else "", inline(txt, self.ctx), tag)
                t = ['<div class="tw"><table><thead><tr>%s</tr></thead><tbody>' % "".join(cell("th", c, k) for k, c in enumerate(head))]
                for r in rows:
                    t.append("<tr>%s</tr>" % "".join(cell("td", c, k) for k, c in enumerate(r)))
                t.append("</tbody></table></div>")
                out.append("".join(t))
                i = j
                continue
            if RE_ITEM.match(ln):
                i = self.list(lines, i, out)
                continue
            if re.match(r"^\s*</?(details|summary)\b[^>]*>\s*$", ln, re.I):
                out.append(ln.strip())
                i += 1
                continue
            j = i
            para = []
            while j < n and lines[j].strip() and (j == i or not self.starts_block(lines[j])):
                para.append(lines[j].strip())
                j += 1
            hard = [re.sub(r"(  |\\)$", "<br>", p) if k < len(para) - 1 else p for k, p in enumerate(para)]
            out.append("<p>%s</p>" % inline("\n".join(hard), self.ctx))
            i = j
        return "\n".join(out)

    @staticmethod
    def starts_block(ln):
        return bool(RE_FENCE.match(ln) or RE_HEAD.match(ln) or RE_HR.match(ln) or RE_ITEM.match(ln)
                    or ln.lstrip().startswith(">"))

    def list(self, lines, i, out):
        n = len(lines)
        m = RE_ITEM.match(lines[i])
        base = len(m.group(1).expandtabs(4))
        ordered = m.group(2)[0].isdigit()
        items = []
        while i < n:
            m = RE_ITEM.match(lines[i])
            if not m or len(m.group(1).expandtabs(4)) != base or m.group(2)[0].isdigit() != ordered:
                break
            content_col = base + len(m.group(2)) + 1
            item = [m.group(3)]
            i += 1
            blank = False
            while i < n:
                x = lines[i].expandtabs(4)
                if not x.strip():
                    blank = True
                    item.append("")
                    i += 1
                    continue
                ind = len(x) - len(x.lstrip())
                if ind >= content_col:
                    item.append(x[content_col:])
                elif ind > base and not blank and not RE_ITEM.match(x):
                    item.append(x.strip())              # lazy continuation of the item's paragraph
                elif ind > base and RE_ITEM.match(x):
                    item.append(x[base + 2:])           # a nested item indented less than the content column
                else:
                    break
                blank = False
                i += 1
            while item and not item[-1].strip():
                item.pop()
            items.append(item)
            j = i                                       # blank lines between items do not end the list
            while j < n and not lines[j].strip():
                j += 1
            if j < n and j > i:
                m2 = RE_ITEM.match(lines[j])
                if m2 and len(m2.group(1).expandtabs(4)) == base and m2.group(2)[0].isdigit() == ordered:
                    i = j
        tag = "ol" if ordered else "ul"
        html_items = []
        for item in items:
            task = ""
            if item and re.match(r"^\[[ xX]\]\s", item[0]):
                task = "&#9745; " if item[0][1] in "xX" else "&#9744; "
                item[0] = item[0][4:]
            inner = self.blocks(item)
            single = re.fullmatch(r"<p>(.*)</p>", inner, re.S)
            if single and "<p>" not in single.group(1):
                inner = single.group(1)
            html_items.append("<li>%s%s</li>" % (task, inner))
        out.append("<%s>%s</%s>" % (tag, "\n".join(html_items), tag))
        return i

    def fenced(self, info, body, lineno):
        kind = info.split()[0].lower() if info else ""
        text = "\n".join(body)
        if kind == "mermaid":
            self.mermaid.append(text)
            return "<!--MM:%s-->" % hashlib.sha256(text.encode()).hexdigest()[:24]
        if kind == "illustration":
            d, err = parse_illustration(text)
            self.illus.append((d, err, lineno))
            return "<!--ILL%d-->" % (len(self.illus) - 1)
        if kind == "widget":
            d, err = parse_widget(text)
            self.widgets.append((d, err, lineno))
            return "<!--WID%d-->" % (len(self.widgets) - 1)
        return "<pre><code%s>%s</code></pre>" % (' class="lang-%s"' % html.escape(kind) if kind else "", html.escape(text))


def parse_widget(text):
    """-> (dict, error): a ```widget block (ADR-0037), by the export builder's own parser (one list of keys)."""
    import export_build    # noqa: E402 (stdlib only)
    return export_build.parse_widget(text)


def parse_illustration(text):
    """-> (dict, error). A value may continue on following indented lines."""
    d, key, err = {}, None, []
    for ln in text.split("\n"):
        m = re.match(r"^([a-z]+):\s*(.*)$", ln)
        if m and not ln.startswith((" ", "\t")):
            key = m.group(1)
            if key in d:
                err.append("key '%s' twice" % key)
            d[key] = m.group(2).strip()
        elif key and ln.strip() and ln.startswith((" ", "\t")):
            d[key] += " " + ln.strip()
        elif ln.strip():
            err.append("line not 'key: value': %r" % ln[:40])
    for k in ILLUS_KEYS:
        if k not in d or (k != "args" and not d[k]):
            err.append("missing key '%s'" % k)
    for k in d:
        if k not in ILLUS_KEYS and k != "values":
            err.append("unknown key '%s'" % k)
    if d.get("values", "computed") not in ("computed", "restated", "recorded"):
        err.append("values '%s' is not computed, restated or recorded" % d["values"])
    if d.get("id") and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", d["id"]):
        err.append("id '%s' is not [A-Za-z0-9_-]+" % d["id"])
    if d.get("tool") and not re.fullmatch(r"[A-Za-z0-9_]+\.py", d["tool"]):
        err.append("tool '%s' is not a script name in tools/" % d["tool"])
    return d, "; ".join(err)


# ---------------------------------------------------------------- pages and links

def all_md():
    out = []
    for dp, dn, fn in os.walk(DOCS):
        dn.sort()
        for f in sorted(fn):
            if f.endswith(".md"):
                out.append(os.path.relpath(os.path.join(dp, f), DOCS).replace(os.sep, "/"))
    return out


def md_links(text):
    """Relative link targets (path part) of every link outside fenced blocks."""
    out, fence = [], None
    for ln in text.split("\n"):
        m = RE_FENCE.match(ln)
        if m:
            if fence is None:
                fence = m.group(2)[0]
            elif m.group(2)[0] == fence and not m.group(3).strip():
                fence = None
            continue
        if fence:
            continue
        for lm in LINK_RE.finditer(CODE_RE.sub("", ln)):
            if lm.group(1):
                continue
            t = lm.group(3).strip("<>").split("#")[0]
            if t and not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", t):
                out.append(t)
    return out


def page_set():
    """Seeds docs/wiki, docs/specs, docs/glossary.md, then every .md they link, transitively."""
    avail = set(all_md())
    seeds = [p for p in avail if p.startswith(("wiki/", "specs/")) or p == "glossary.md"]
    seeds = seeds or sorted(avail)                      # --docs on a directory without wiki/ and specs/
    seen, todo = set(seeds), list(seeds)
    while todo:
        p = todo.pop()
        with open(os.path.join(DOCS, p), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for t in md_links(text):
            c = os.path.normpath(os.path.join(os.path.dirname(p), t)).replace(os.sep, "/")
            if os.path.isdir(os.path.join(DOCS, c)):
                c += "/README.md"
            if c in avail and c not in seen:
                seen.add(c)
                todo.append(c)
    return seen


# ---------------------------------------------------------------- illustrations

def run_illustration(d, root, out_root, no_run):
    """-> (kind, path under the site root or None, warning or '')."""
    iid, tool = d["id"], d["tool"]
    odir = os.path.join(out_root, "illustrations", iid)
    script = os.path.join(HERE, tool)
    if no_run:
        return None, None, "illustrations not built (--no-illustrations)"
    if not os.path.isfile(script):
        return None, None, "tool tools/%s does not exist" % tool
    cmd = [sys.executable, "-I", script, root] + shlex.split(d.get("args", "")) + ["--out", odir]
    stamp = hashlib.sha256((" ".join(cmd) + str(os.path.getmtime(script)) + str(os.path.getmtime(anim_common.__file__))).encode()).hexdigest()
    sf = os.path.join(odir, ".stamp")
    fresh = False
    try:
        with open(sf) as fh:
            fresh = fh.read() == stamp
    except OSError:
        pass
    if not fresh:
        try:
            if os.path.isdir(odir):
                shutil.rmtree(odir)
            r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=ILLUS_TIMEOUT)
        except subprocess.TimeoutExpired:
            return None, None, "tool %s timed out after %d s" % (tool, ILLUS_TIMEOUT)
        if r.returncode != 0:
            tail = (r.stderr.strip() or r.stdout.strip() or "no output").split("\n")[-1][:200]
            return None, None, "tool %s failed (exit %d): %s" % (tool, r.returncode, tail)
        os.makedirs(odir, exist_ok=True)
        with open(sf, "w") as fh:
            fh.write(stamp)
    ipage = os.path.join(odir, "index.html")
    if os.path.isfile(ipage):
        add_footer(ipage)
        return "iframe", "illustrations/%s/index.html" % iid, ""
    gifs = sorted(f for f in os.listdir(odir) if f.endswith(".gif")) if os.path.isdir(odir) else []
    if gifs:
        return "gif", "illustrations/%s/%s" % (iid, gifs[0]), ""
    return None, None, "tool %s wrote neither index.html nor a GIF" % tool


def add_footer(path):
    """ADR-0034: every built page carries the footer, the tool's own step-through page too (idempotent)."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    if FOOTER in text:
        return
    foot = '<footer style="margin:2em 0 1em;font:13px system-ui,sans-serif;text-align:center;opacity:.75">%s</footer>' % FOOTER
    i = text.lower().rfind("</body>")
    text = text[:i] + foot + text[i:] if i >= 0 else text + foot
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def illus_html(page, d, err, rel, out_root, root, no_run):
    if err:
        page.warnings.append("illustration block: " + err)
        return '<div class="warn">Illustration not built: %s</div>' % html.escape(err)
    kind, path, warn = run_illustration(d, root, out_root, no_run)
    if warn and not no_run:
        page.warnings.append("illustration %s: %s" % (d["id"], warn))
    links = []
    for part in re.split(r"[,\s]+", d["illustrates"].strip()):
        if part:
            href, k = href_for(page.ctx, part)
            links.append('<a href="%s">%s</a>' % (html.escape(href), html.escape(part)) if href else html.escape(part))
    meta = ("Seed: %s. Illustrates: %s. Generated by tools/%s from your own game files; the values are computed by our model, "
            "not observed from the game." % (html.escape(d["seed"]), ", ".join(links), html.escape(d["tool"])))
    cap = "<figcaption><strong>%s</strong><br><small>%s</small></figcaption>" % (html.escape(d["caption"]), meta)
    if kind == "iframe":
        media = '<iframe class="illus" src="%s%s" title="%s" loading="lazy"></iframe>' % (rel, path, html.escape(d["id"]))
    elif kind == "gif":
        media = '<img class="illus" src="%s%s" alt="%s">' % (rel, path, html.escape(d["caption"]))
    else:
        media = ('<div class="warn">Illustration %s not built: %s. To build it: <code>python3 -I tools/%s &lt;data root&gt; %s '
                 '--out workspace/site/illustrations/%s</code></div>' % (
                     html.escape(d["id"]), html.escape(warn), html.escape(d["tool"]), html.escape(d.get("args", "")),
                     html.escape(d["id"])))
    return '<figure class="illfig">%s%s</figure>' % (media, cap)


def widget_html(page, d, err, rel, out_root, root, no_run, illus_by_id):
    """A ```widget block on the local site (ADR-0037): no script runs here, so the block shows what the published page shows
    when JavaScript is off: its fallback (the named illustration's picture, or the twin's text table) and its caption."""
    if err:
        page.warnings.append("widget block: " + err)
        return '<div class="warn">Widget not shown: %s</div>' % html.escape(err)
    wid, name, fb = d["id"], d["widget"], d["fallback"]
    media = ""
    if fb == "text":
        wdir = os.path.join(HERE, "widgets")
        fixture = os.path.join(wdir, name, "fixture.json")
        table = None
        if os.path.isfile(fixture):
            sys.path.insert(0, wdir)
            import twins    # noqa: E402 (tools/widgets/twins.py: the fallback table of each widget)
            with open(fixture, encoding="utf-8") as fh:
                table = twins.fallback_table(name, json.load(fh))
        if table:
            head, rows, note = table
            media = "<p>%s</p><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
                html.escape(note), "".join("<th>%s</th>" % html.escape(str(h)) for h in head),
                "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % html.escape(str(c)) for c in r) for r in rows))
        else:
            page.warnings.append("widget %s: no text fallback for the widget %s" % (wid, name))
            media = '<div class="warn">Widget %s: no text fallback for %s.</div>' % (html.escape(wid), html.escape(name))
    else:
        ill = illus_by_id.get(fb)
        kind = path = None
        warn = "fallback illustration %s is not on a built page" % fb
        if ill is not None:
            kind, path, warn = run_illustration(ill, root, out_root, no_run)
            if kind == "iframe":      # the picture: the GIF beside the step-through page, when the tool wrote one
                odir = os.path.join(out_root, "illustrations", fb)
                gifs = sorted(f for f in os.listdir(odir) if f.endswith(".gif")) if os.path.isdir(odir) else []
                kind, path = ("gif", "illustrations/%s/%s" % (fb, gifs[0])) if gifs else (None, None)
                warn = "" if gifs else "no picture beside the step-through page"
        if kind == "gif":
            media = '<img class="illus" src="%s%s" alt="%s">' % (rel, path, html.escape(d["caption"]))
        else:
            page.warnings.append("widget %s: %s" % (wid, warn))
            media = '<div class="warn">Widget %s: fallback picture %s not shown: %s.</div>' % (
                html.escape(wid), html.escape(fb), html.escape(warn))
    links = []
    for part in re.split(r"[,\s]+", d["illustrates"].strip()):
        if part:
            href, _k = href_for(page.ctx, part)
            links.append('<a href="%s">%s</a>' % (html.escape(href), html.escape(part)) if href else html.escape(part))
    meta = ("Widget %s: the interactive element runs only on the published site; this page shows its fallback, with no script. "
            "Illustrates: %s. The values are computed by our model of the rule, not observed from the game." % (
                html.escape(name), ", ".join(links)))
    return '<figure class="illfig">%s<figcaption><strong>%s</strong><br><small>%s</small></figcaption></figure>' % (
        media, html.escape(d["caption"]), meta)


# ---------------------------------------------------------------- Mermaid

def draw_mermaid(blocks):
    """blocks: {key: text} -> ({key: svg}, {key: error}, skip reason or '')."""
    os.makedirs(MERMAID_CACHE, exist_ok=True)
    svgs, errs, todo = {}, {}, {}
    for k, t in blocks.items():
        f = os.path.join(MERMAID_CACHE, k + ".svg")
        if os.path.isfile(f):
            with open(f, encoding="utf-8") as fh:
                svgs[k] = fh.read()
        else:
            todo[k] = t
    if not todo:
        return svgs, errs, ""
    node = shutil.which("node")
    if not node:
        return svgs, errs, "node not found"
    payload = json.dumps({"blocks": [{"id": k, "text": t} for k, t in todo.items()]})
    try:
        r = subprocess.run([node, os.path.join(HERE, "site_mermaid.mjs"), "--dir", BUNDLE_DIR], input=payload,
                           capture_output=True, text=True, timeout=600)
        res = json.loads(r.stdout.strip().split("\n")[-1])
    except (subprocess.TimeoutExpired, ValueError, OSError) as e:
        return svgs, errs, "mermaid helper failed: %s" % e
    if "skip" in res:
        return svgs, errs, res["skip"]
    for k, s in res.get("svgs", {}).items():
        s = re.sub(r'\sxmlns(:\w+)?="[^"]*"', "", s)      # namespace URIs are not requests, but keep the pages free of http
        svgs[k] = s
        with open(os.path.join(MERMAID_CACHE, k + ".svg"), "w", encoding="utf-8") as fh:
            fh.write(s)
    errs.update(res.get("errors", {}))
    return svgs, errs, ""


# ---------------------------------------------------------------- site layout

CSS = """
:root{--bg:#fbfbfa;--fg:#1d1f23;--mut:#5f6670;--line:#dcdfe3;--card:#f1f2f4;--link:#0b5cad;--code:#eceef1;--warn:#fff3cd;--warnfg:#5c4400;--mm:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#15171a;--fg:#dfe2e6;--mut:#9aa1ab;--line:#2c3036;--card:#1d2024;--link:#7db4ee;--code:#23272c;--warn:#3d3210;--warnfg:#f0d98a;--mm:#f4f5f7}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
a{color:var(--link)}
.top{display:flex;flex-wrap:wrap;gap:4px 18px;align-items:baseline;padding:10px 16px;border-bottom:1px solid var(--line);background:var(--card);font-size:.92rem}
.top b{margin-right:8px}.top a{text-decoration:none}
.wrap{display:flex;align-items:flex-start;max-width:90rem;margin:0 auto}
nav.side{flex:0 0 17rem;position:sticky;top:0;max-height:100vh;overflow:auto;padding:14px 12px 24px 16px;font-size:.85rem;border-right:1px solid var(--line)}
nav.side h2{font-size:.8rem;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);margin:.4rem 0;border:0}
nav.side ul{list-style:none;margin:0;padding:0}nav.side li{margin:2px 0}nav.side li.cur>a{font-weight:700;color:var(--fg);text-decoration:none}
main{flex:1;min-width:0;padding:8px 24px 40px;max-width:60rem}
@media (max-width:820px){.wrap{display:block}nav.side{position:static;max-height:none;border-right:0;border-bottom:1px solid var(--line)}main{padding:8px 16px 32px}}
h1,h2,h3,h4{line-height:1.25;margin:1.6em 0 .5em}h1{font-size:1.9rem;margin-top:.8em}h2{font-size:1.4rem;border-bottom:1px solid var(--line);padding-bottom:.2em}h3{font-size:1.15rem}
code,pre{font:.88em/1.45 ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}
code{background:var(--code);padding:.1em .3em;border-radius:4px}pre{background:var(--code);padding:12px 14px;border-radius:6px;overflow:auto}pre code{background:none;padding:0}
blockquote{margin:1em 0;padding:.1em 1em;border-left:4px solid var(--line);color:var(--mut)}
.tw{overflow-x:auto;margin:1em 0}table{border-collapse:collapse;font-size:.92rem}th,td{border:1px solid var(--line);padding:5px 9px;vertical-align:top;text-align:left}th{background:var(--card)}
hr{border:0;border-top:1px solid var(--line);margin:2em 0}
details.fm{font-size:.85rem;color:var(--mut);margin:0 0 1em}details.fm pre{margin:.4em 0}
.nolink{border-bottom:1px dotted var(--mut);cursor:help}.ext small,.img{color:var(--mut)}
figure.mm{margin:1.2em 0;padding:10px;background:var(--mm);color:#222;border-radius:6px;overflow-x:auto;text-align:center}figure.mm svg{max-width:100%;height:auto}
.warn{background:var(--warn);color:var(--warnfg);padding:8px 12px;border-radius:6px;margin:1em 0;font-size:.92rem}
figure.illfig{margin:1.4em 0;border:1px solid var(--line);border-radius:8px;overflow:hidden;background:var(--card)}
iframe.illus{display:block;width:100%;height:860px;border:0;resize:vertical;background:#111}img.illus{display:block;max-width:100%;margin:0 auto}
figcaption{padding:10px 14px;font-size:.92rem}figcaption small{color:var(--mut)}
footer{margin:2.5rem 0 0;padding:14px 16px;border-top:1px solid var(--line);color:var(--mut);font-size:.85rem;text-align:center}
ul.pl{columns:2;column-gap:2rem}@media (max-width:820px){ul.pl{columns:1}}
"""

TOP = [("Home", "index.html"), ("Wiki", "wiki/README.html"), ("Specs", "specs/README.html"), ("Glossary", "glossary.html"),
       ("Tables", "tables/index.html"), ("Formats", "formats/index.html"), ("Findings", "findings/index.html"),
       ("ADRs", "adrs/index.html"), ("All pages", "all.html")]


def shell(title, body, rel, side=""):
    """rel: path prefix from the page to the site root ('' or '../')."""
    top = "".join('<a href="%s%s">%s</a>' % (rel, h, t) for t, h in TOP)
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s</title><link rel="stylesheet" href="%sassets/site.css"></head><body>'
            '<div class="top"><b>d2-recon (local build)</b>%s</div><div class="wrap">%s<main>%s'
            '<footer>%s</footer></main></div></body></html>\n' % (html.escape(title), rel, top, side, body, FOOTER))


_wiki_order = None


def wiki_order():
    global _wiki_order
    if _wiki_order is None:
        _wiki_order = {}
        try:
            with open(os.path.join(DOCS, "wiki", "README.md"), encoding="utf-8") as fh:
                for t in md_links(fh.read()):
                    _wiki_order.setdefault("wiki/" + os.path.normpath(t).replace(os.sep, "/"), len(_wiki_order))
        except OSError:
            pass
    return _wiki_order


def side_nav(src, titles, pages):
    d = os.path.dirname(src)
    sibs = sorted(p for p in pages if os.path.dirname(p) == d)
    if len(sibs) < 2:
        return ""
    if src.startswith("wiki/"):
        order = wiki_order()
        sibs.sort(key=lambda p: (order.get(p, 999), p))
    items = []
    for p in sibs[:80]:
        items.append('<li%s><a href="%s">%s</a></li>' % (' class="cur"' if p == src else "", os.path.basename(p)[:-3] + ".html",
                                                         html.escape(titles[p])))
    if len(sibs) > 80:
        items.append('<li><a href="%sindex.html">all %d in this section</a></li>' % ("../" * (src.count("/") - 1) if False else "", len(sibs)))
    return '<nav class="side"><h2>%s</h2><ul>%s</ul></nav>' % (html.escape(d), "".join(items))


def dir_index(d, pages, titles):
    ps = sorted(p for p in pages if p.startswith(d + "/"))
    items = ['<li><a href="%s">%s</a> <small>%s</small></li>' % (p[len(d) + 1:-3] + ".html", html.escape(titles[p]), html.escape(p))
             for p in ps]
    return '<h1>%s</h1><p>%d pages.</p><ul class="pl">%s</ul>' % (html.escape(d), len(ps), "\n".join(items))


# ---------------------------------------------------------------- build

def build(argv):
    only, no_ill, out, root = None, False, os.path.join(WS, "site"), None
    a = list(argv)
    while a:
        x = a.pop(0)
        if x == "--only" and a:
            only = a.pop(0)
        elif x == "--no-illustrations":
            no_ill = True
        elif x == "--out" and a:
            out = a.pop(0)
        elif x == "--docs" and a:
            global DOCS
            DOCS = os.path.realpath(a.pop(0))
        elif x.startswith("--"):
            raise SystemExit("unknown option %s\n\n%s" % (x, __doc__.split("\n\n")[0]))
        elif root is None:
            root = x
        else:
            raise SystemExit("unexpected argument %s" % x)
    out = anim_common.safe_out(out)
    root = os.path.realpath(root or os.path.join(WS, "merged"))
    t0 = time.time()
    pages = page_set()
    texts, titles = {}, {}
    for p in sorted(pages):
        with open(os.path.join(DOCS, p), encoding="utf-8", errors="replace") as fh:
            texts[p] = fh.read()
        m = re.search(r"^#\s+(.*?)\s*$", re.sub(r"\A---\n.*?\n---\n", "", texts[p], flags=re.S), re.M)
        titles[p] = plain(m.group(1)) if m else os.path.basename(p)[:-3]
    want = sorted(p for p in pages if not only or fnmatch.fnmatch(p, only))
    os.makedirs(os.path.join(out, "assets"), exist_ok=True)
    with open(os.path.join(out, "assets", "site.css"), "w") as fh:
        fh.write(CSS.strip() + "\n")
    rendered, mm_blocks, warnings, broken, n_ill = {}, {}, [], 0, 0
    for p in want:
        pg = rendered[p] = Page(p, texts[p], pages)
        for t in pg.mermaid:
            mm_blocks[hashlib.sha256(t.encode()).hexdigest()[:24]] = t
        broken += len(pg.ctx.broken)
    illus_by_id = {d["id"]: d for pg in rendered.values() for d, err, _ in pg.illus if not err and d.get("id")}
    svgs, errs, skip = draw_mermaid(mm_blocks)
    if skip:
        warnings.append("Mermaid not drawn: %s (blocks shown as source)" % skip)

    for p, pg in rendered.items():
        rel = "../" * p.count("/")

        def mm(m, pg=pg):
            k = m.group(1)
            if k in svgs:
                return '<figure class="mm">%s</figure>' % svgs[k]
            why = errs.get(k) or skip or "not drawn"
            return '<div class="warn">Mermaid diagram not drawn (%s); source:</div><pre><code>%s</code></pre>' % (
                html.escape(why), html.escape(mm_blocks[k]))

        def il(m, pg=pg, rel=rel):
            d, err, _ = pg.illus[int(m.group(1))]
            return illus_html(pg, d, err, rel, out, root, no_ill)

        def wd(m, pg=pg, rel=rel):
            d, err, _ = pg.widgets[int(m.group(1))]
            return widget_html(pg, d, err, rel, out, root, no_ill, illus_by_id)
        n_ill += len(pg.illus)
        body = re.sub(r"<!--WID(\d+)-->", wd, re.sub(r"<!--ILL(\d+)-->", il, re.sub(r"<!--MM:([0-9a-f]+)-->", mm, pg.body)))
        warnings += ["%s: %s" % (p, w) for w in pg.warnings]
        dst = os.path.join(out, p[:-3] + ".html")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write(shell(titles[p] + " - d2-recon", body, rel, side_nav(p, titles, pages)))

    secs = sorted({p.split("/")[0] for p in pages if "/" in p})
    for s in secs:
        os.makedirs(os.path.join(out, s), exist_ok=True)
        with open(os.path.join(out, s, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(shell(s, dir_index(s, pages, titles), "../"))
    rows = "".join('<h2><a href="%s/index.html">%s</a> <small>(%d)</small></h2>' % (s, s, sum(1 for p in pages if p.startswith(s + "/")))
                   for s in secs)
    with open(os.path.join(out, "all.html"), "w", encoding="utf-8") as fh:
        fh.write(shell("All pages", "<h1>All pages</h1>" + rows, ""))
    home = ("<h1>Diablo II: Lord of Destruction 1.14d, documented</h1>"
            '<p>A local build of the d2-recon documentation: how the game builds a level, fills it with monsters and decides what drops. '
            'Start with the <a href="wiki/README.html">wiki</a> (plain prose), then the <a href="specs/README.html">specs</a> '
            '(the reimplementation-grade statements with their evidence), and the <a href="glossary.html">glossary</a>.</p>'
            '<ul><li><a href="wiki/README.html">Wiki</a>, %d pages</li><li><a href="specs/README.html">Specs</a>, %d pages</li>'
            '<li><a href="tables/index.html">Table docs</a>, <a href="formats/index.html">format docs</a>, '
            '<a href="findings/index.html">findings</a>, <a href="adrs/index.html">decisions</a>: the pages the specs link</li>'
            '<li><a href="all.html">Every page</a>, by section</li></ul>'
            "<p>Illustrations (a maze growing, a drop resolving) appear where a page names one and are drawn from your own game files "
            "at build time.</p>" % (sum(1 for p in pages if p.startswith("wiki/")), sum(1 for p in pages if p.startswith("specs/"))))
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(shell("d2-recon", home, ""))
    print("built %d pages (of %d in the set) into %s in %.1f s; %d mermaid blocks (%d drawn, %d errors); %d illustration blocks; "
          "%d links to non-pages shown as text" % (len(rendered), len(pages), out, time.time() - t0, len(mm_blocks), len(svgs),
                                                   len(errs), n_ill, broken))
    for w in warnings:
        print("WARNING " + w)
    return 0


# ---------------------------------------------------------------- check

def heading_slugs(path):
    """The set of heading anchors of a Markdown file as the gate's E8 computes them, or None when unreadable."""
    import gate    # noqa: E402 (stdlib only; one slug rule for E8 and E19)
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return set(gate.heading_slugs(fh.read()))
    except OSError:
        return None


def check(argv):
    docs = os.path.realpath(argv[0]) if argv else DOCS
    tools = os.path.join(os.path.dirname(docs), "tools")    # the checkout's own tools/ (gate --root, --staged)
    tools = tools if os.path.isdir(tools) else HERE
    seen, problems, nblocks, heads = {}, [], 0, {}
    seen_w, wfall, ill_ids = {}, [], set()

    def check_links(d, path, where):
        """Every `illustrates` link of a block resolves: a relative link to a file that exists, its #anchor a heading of it."""
        for part in re.split(r"[,\s]+", d.get("illustrates", "").strip()):
            if not part:
                continue
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", part):
                problems.append("%s: illustrates '%s' is not a relative link" % (where, part))
                continue
            tpath, _, frag = part.partition("#")
            target = os.path.normpath(os.path.join(os.path.dirname(path), tpath)) if tpath else path
            if not os.path.exists(target):
                problems.append("%s: illustrates '%s' does not resolve" % (where, part))
            elif frag and target.endswith(".md"):
                if target not in heads:
                    heads[target] = heading_slugs(target)
                if heads[target] is not None and frag not in heads[target]:
                    problems.append("%s: illustrates '%s': no heading with that anchor" % (where, part))
    for dp, dn, fn in os.walk(docs):
        dn.sort()
        for f in sorted(fn):
            if not f.endswith(".md"):
                continue
            path = os.path.join(dp, f)
            rel = os.path.relpath(path, docs).replace(os.sep, "/")
            with open(path, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().split("\n")
            i = 0
            while i < len(lines):
                m = RE_FENCE.match(lines[i])
                if not m:
                    i += 1
                    continue
                fence, indent, info = m.group(2), m.group(1), m.group(3).strip()
                close = re.compile(r"^\s*" + re.escape(fence[0]) + "{%d,}\\s*$" % len(fence))
                j = i + 1
                while j < len(lines) and not close.match(lines[j]):
                    j += 1
                if info == "illustration":
                    nblocks += 1
                    body = "\n".join(x[len(indent):] if x.startswith(indent) else x.lstrip() for x in lines[i + 1:j])
                    d, err = parse_illustration(body)
                    where = "%s:%d" % (rel, i + 1)
                    if err:
                        problems.append("%s: %s" % (where, err))
                    if d.get("id"):
                        if d["id"] in seen:
                            problems.append("%s: id '%s' also at %s" % (where, d["id"], seen[d["id"]]))
                        seen.setdefault(d["id"], where)
                    tool = d.get("tool", "")
                    if re.fullmatch(r"[A-Za-z0-9_]+\.py", tool) and not os.path.isfile(os.path.join(tools, tool)):
                        problems.append("%s: tool '%s' is not in tools/" % (where, tool))
                    check_links(d, path, where)
                    ill_ids.add(d.get("id"))
                elif info == "widget":
                    nblocks += 1
                    body = "\n".join(x[len(indent):] if x.startswith(indent) else x.lstrip() for x in lines[i + 1:j])
                    d, err = parse_widget(body)
                    where = "%s:%d" % (rel, i + 1)
                    if err:
                        problems.append("%s: %s" % (where, err))
                    if d.get("id"):
                        if d["id"] in seen_w:
                            problems.append("%s: widget id '%s' also at %s" % (where, d["id"], seen_w[d["id"]]))
                        seen_w.setdefault(d["id"], where)
                    name = d.get("widget", "")
                    if re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name) and not os.path.isfile(
                            os.path.join(tools, "widgets", name, "widget.js")):
                        problems.append("%s: widget '%s' is not in tools/widgets/" % (where, name))
                    if d.get("fallback") and d["fallback"] != "text":
                        wfall.append((where, d["fallback"]))
                    check_links(d, path, where)
                i = j + 1
    for where, fb in wfall:
        if fb not in ill_ids:
            problems.append("%s: widget fallback '%s' is not an illustration id under docs/" % (where, fb))
    for p in problems:
        print("ILLUSTRATION " + p)
    print("CHECK illustrations: %d blocks, %d problems" % (nblocks, len(problems)))
    return 1 if problems else 0


def main(argv):
    if argv and argv[0] == "check":
        return check(argv[1:])
    return build(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

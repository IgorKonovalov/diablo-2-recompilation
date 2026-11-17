#!/usr/bin/env python3
"""Publish check for the public export (plan 0070 Phase 2; ADR-0009, ADR-0035, ADR-0036).

Usage:
  python3 -I tools/export_check.py CUT_DIR [--manifest FILE] [--identity STR ...] [--no-git-identity]
  python3 -I tools/export_check.py --repo REPO_DIR [CUT_DIR]

Read-only, standard library only. CUT_DIR is the builder's output (workspace/export/): Markdown pages
under site/src/content/docs/, site/src/cut.json, and schematic illustration folders under
site/public/illustrations/<id>/. REPO_DIR is the export repository's own files (workspace/export-repo/).
Exit 0 only when no rule fails; X12 is a warning for the review and never fails.

Rules (plan 0070 § Publish check):
  X1  address 0x00XXXXXX, other hex of 6+ digits, sub_XXXXXXXX, +0x offset
  X2  anchor fn:/data:/struct:/tbl:/fmt:/src:; run: only in its id form (run:<id char>)
  X3  repository reference: findings/, finding id (items/0002), ADR-NNNN, plan NNNN, lane/, docs/, re/,
      tools/, workspace/, .py/.csv name, commit hash
  X4  identity: the working repository's name and remote URL, the git user.email (all read from git at run
      time, never stored), /home/ or /Users/ anywhere, or any absolute path. The lockfile gets X4 (and X7) only. The owner's name and account pass.
  X5  decompiler-like fenced block (mermaid fences exempt from X5 only)
  X6  table over 20 body rows that the manifest does not name (matched by page route, not line number:
      the redactor moves lines)
  X7  cut: http(s)/ftp/mailto/javascript/file:/ or protocol-relative link, raw HTML (<script> <iframe> <link> <style> ...), @import, url(.
      repo: a URL outside the allowlist, an action outside actions/*
  X8  any image: Markdown image, <img>, <video>, an image file; except a root-absolute /illustrations/<id>/<file> target under a verified
      illustrations/<id>/ folder (ADR-0036)
  X9  banned topics (copy protection, CD key, Battle.net, Warden) and tool names (Ghidra, gdb, decompile*,
      disassembl*, harness, logger, "logged run"); emulation/emulated/breakpoint pass
  X10 footer component differs from the footer word for word or is unregistered; cut.json without a date
  X11 cut: a file other than .md, cut.json and the schematic allowlist (folder with schematic.json: marker,
      sha256 list, nothing else, index.html with no URL/request; the text of steps.json, index.html and
      schematic.json passes X1-X4 and X9, and no file holds an identity string or a home path). repo: a path outside the plan's table
      (plus the lockfile); a .git directory anywhere.
  X12 (warning) quoted run over 12 words; capitalised name matching no table row name of the cut.

The schematic marker (Phase 2b's generators must write it): the byte string `schematic-only/1` inside
every .gif, .png, index.html and steps.json of the folder; `schematic.json` is
{"marker": "schematic-only/1", "files": {"<relative path>": "<sha256 hex>", ...}} and lists every
file of the folder but itself.

Text rules as a function: `check_text(unit, identity=None)` returns [(rule, line, detail)] for X1-X5 and X9
on one unit of text (a sentence, list item, table row or fenced block); `text_rules(unit)` returns the set
of rule ids. The builder's simplifier calls these.
"""
import argparse
import functools
import hashlib
import json
import os
import re
import subprocess
import sys

MARKER = "schematic-only/1"
TEXT_RULES = ("X1", "X2", "X3", "X4", "X5", "X9")
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tga", ".pcx", ".dc6", ".dcc",
             ".avif", ".tif", ".tiff", ".mp4", ".webm", ".ogv"}
FOOTER = ("An unofficial, non-commercial preservation project. Not affiliated with or endorsed by Blizzard "
          "Entertainment. Diablo and Blizzard Entertainment are trademarks of Blizzard Entertainment, Inc. No "
          "game files, art, text dumps or code are included. Descriptions of behaviour are written in our own "
          "words. Cut on {cut.date}.")
# the export repository and its Pages site pass (ADR-0035, plan 0070 Phase 7); everything else is a failure.
# GitHub names are case-insensitive, so the match is too. The name ends at `/`, `#`, `?`, `.git` or the end of the
# URL: `arpg-1-14d-notes-old` fails. The bare Pages host (no path) is the site's own `site:` setting.
EXPORT_REPO = "arpg-1-14d-notes"
RE_URL_ALLOW = re.compile(
    r"https://github\.com/igorkonovalov/" + re.escape(EXPORT_REPO) + r"(?:\.git)?(?:[/#?]|$)"
    r"|https://igorkonovalov\.github\.io(?:/" + re.escape(EXPORT_REPO) + r"(?:[/#?]|$))?$"
    r"|https://igorkonovalov\.github\.io/" + re.escape(EXPORT_REPO) + r"(?:[/#?]|$)",
    re.I)
# `https://github.com/${` is a template literal in the site's JS (the account and name join at build time), not a URL
URL_ALLOW = ("https://github.com/${", "https://creativecommons.org/", "https://wiki.creativecommons.org/")
URL_ALLOW_LOCKFILE = ("https://registry.npmjs.org/",)
REPO_PATHS = {"site/package.json", "site/package-lock.json", "site/astro.config.mjs", "site/src/content.config.ts",
              "site/src/components/Footer.astro", "site/scripts/check-site-links.mjs", "site/public/favicon.svg", "site/src/styles/site.css",
              ".github/workflows/pages.yml", "README.md", "LICENSE", ".gitignore"}
TABLE_LIMIT = 20

# ---------------------------------------------------------------- text rules

RE_X1 = [
    (re.compile(r"\b0x[0-9A-Fa-f]{6,}\b"), "address / hex of 6+ digits"),
    # other spellings of a value of 6+ hex digits (review of lane/x70b2): `0X4A1B20`, `0x0045_1B20`, MASM `4A1B20h`
    (re.compile(r"\b0X[0-9A-Fa-f]{6,}\b|\b0[xX](?=(?:[0-9A-Fa-f][_']?){6})[0-9A-Fa-f]+(?:[_'][0-9A-Fa-f]+)+\b"
                r"|(?<![\w.])(?=[0-9A-Fa-f]*[0-9])[0-9A-Fa-f]{6,}[hH]\b"), "hex of 6+ digits, other spelling"),
    (re.compile(r"\bsub_[0-9A-Fa-f]{6,8}"), "sub_ name"),
    # an in-memory struct offset `Name+0x10`, `Name+0x10+0x4`, or a bare `+0x1C` passes (owner decision 2026-11-17,
    # plan 0070 Phase 9; ADR-0009 risk (1) weighed by the owner): up to 5 hex digits. 6+ digits is a code-image
    # shaped value and fails as ever, and so does an offset on a `sub_`/`DAT_` name
    (re.compile(r"\+0x[0-9A-Fa-f]{6,}"), "+0x offset of 6+ digits"),
    (re.compile(r"\b(?:sub|DAT|FUN|PTR)_\w*(?:\+0x[0-9A-Fa-f]+)+"), "offset on a code name"),
    # an offset from the image or a module is an address (`Game.exe+0x5C00`, `image base + 0x1A2B3`; review of lane/x70b2)
    (re.compile(r"(?i)(?:\.exe|\.dll|\bimage(?:\s*base)?|\bimagebase|\bmodule|\brva)`?\s*\+\s*0x[0-9A-Fa-f]+"),
     "offset from the image or a module"),
    # a partial address, `0x0063xxxx`: a hex prefix with placeholder digits
    # (6 to 8 places; placeholders `x` or `??`: a flag in a question, `0x40000?`, is no partial address; review of lane/x70b2)
    (re.compile(r"\b0[xX](?=[0-9A-Fa-fxX?]{6,8}(?![\w?]))(?:00)?[4-9][0-9A-Fa-f]{0,5}(?:[xX]+|\?{2,})[0-9A-Fa-fxX?]*(?![\w?])"),
     "partial address"),
    # bare hex, also after `_` (DAT_00556F60, a name with an address in it); architect review 2026-11-17
    (re.compile(r"(?<![A-Za-z0-9.])(?=[0-9A-Fa-f]*[0-9])(?=[0-9A-Fa-f]*[A-Fa-f])[0-9A-Fa-f]{6,}(?![\w.])"),
     "hex of 6+ digits"),
    (re.compile(r"(?<![A-Za-z0-9.])00[4-9][0-9]{5}(?![\w.])"), "bare address of the code image"),
]
RE_X2 = [
    (re.compile(r"(?<![\w])(?:fn|data|struct|tbl|fmt|src):(?=[A-Za-z0-9_])"), "anchor"),
    (re.compile(r"(?<![\w])run:(?=[A-Za-z0-9_])"), "run id"),
    # a lead tag never reaches the export (it lives under Open questions); the check guards it, not only the
    # builder's XL rule (architect review 2026-11-17)
    (re.compile(r"\[L\]"), "lead tag [L]"),
]
RE_X3 = [
    (re.compile(r"findings/"), "findings/ path"),
    (re.compile(r"(?<![\w])[a-z]+/\d{4}\b"), "finding id"),
    (re.compile(r"\bADR-\d+", re.I), "ADR reference"),
    (re.compile(r"\bplans? \d{4}\b", re.I), "plan reference"),
    (re.compile(r"(?<![A-Za-z0-9])lane/"), "lane/ reference"),
    # `../docs/` fails; only the export repository's own `content/docs/` passes (architect review 2026-11-17)
    (re.compile(r"(?<![A-Za-z0-9])(?<!content/)(?:docs|re|tools|workspace)/"), "repository path"),
    (re.compile(r"(?<![\w-])(?!console\.log\b)[\w-]+\.(?:py|csv|log)\b"), ".py/.csv/.log name"),   # JS `console.log` is no file name
    (re.compile(r"(?<![\w])\.claude\b"), ".claude path"),
    # the working docs' trees, written as a path (`specs/items/tc`); architect review 2026-11-17
    (re.compile(r"(?<![\w/.-])(?:specs|tables|formats|findings|plans|adrs|backlog)/[\w-]"), "working-docs path"),
    (re.compile(r"(?<![\w.])(?=[0-9a-f]*[0-9])(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}(?![\w.])"), "commit hash"),
]
RE_HOME = re.compile(r"/(?:home|Users)/|\bfile:/", re.I)
# a Markdown image target `](/illustrations/<id>/<file>)` is no absolute path here: X8 verifies it against the folder.
# Only that shape: right after `](`, two segments that don't start with a dot, the closing parenthesis.
RE_ABS = re.compile(r"(?:(?<=[\s`\"'(\[])|^)/(?!(?<=\]\(/)illustrations/[\w-][\w.-]*/[\w-][\w.-]*\))(?:home|usr|etc|tmp|var|opt|mnt|root|srv|media|proc|dev|Users|[a-z][\w.-]*/[\w.-]+)"
                    r"(?:/[\w.\-]*)*|\b[A-Za-z]:\\[\w.]")
RE_X9 = [
    (re.compile(r"copy[- ]?protection|\bcd[- ]?key", re.I), "copy protection / CD key"),
    (re.compile(r"battle[-. ]?net|\bbnet\b", re.I), "Battle.net"),
    (re.compile(r"\bwarden\b", re.I), "Warden"),
    (re.compile(r"\bghidra\b|\bgdb\b|\bdecompil\w*|\bdisassembl\w*|\bharness\b|\blogger\b|\blogged runs?\b"
                r"|\bradare2?\b|\brizin\b|\bx64dbg\b|\bollydbg\b|\bIDA Pro\b|\bwine\b", re.I),
     "tool name"),
]
RE_FENCE = re.compile(r"^\s*(```+|~~~+)\s*([\w-]*)")
RE_BLOCK_BAD = [
    # a C statement: `;`-terminated and assigned with `=`, typed, or compared with `==`/`!=`/`&&`. Our pseudocode uses `;` as a
    # separator and `=` as equality, so a bare `;` at the end of a line is not C
    # review of lane/x70b2: a compound assignment (`x += 3;`), `unsigned`/`signed`/`struct` declarations, `DWORD`, `--`, a
    # bare call or `return` statement (the `;` ends the line: our `;` also opens a comment), and a C comment after the `;` (`x = 1; // c`) count too
    (re.compile(r"^(?=.*;\s*(?://.*|/\*.*\*/\s*)?$)(?:\s*(?:[A-Za-z]*\d+[a-z]?\.\s+)?[\w.\[\]*()]+\s*(?:[-+*/%&|^]|<<|>>)?=\s*[^=\s]"
                r"|\s*(?:const\s+)?(?:(?:un)?signed|struct\s+\w+|u?int\d*(?:_t)?|char|short|long|byte|bool|float|double|void|D?WORD|BYTE"
                r"|undefined\d?)\b[\s*]+\w"
                r"|\s*(?:return\b[^;:]*|[A-Za-z_][\w.]*\([^;:]*\))\s*;\s*(?://.*|/\*.*\*/\s*)?$"
                r"|.*(?:==|!=|&&|\|\||\+\+|--\w|\w--))"), "C statement ending in ;"),
    # a C block on one line: braces around a `;`-terminated assignment or call (`if (x) { y = 1; }`); `{ low: u32; high: u32 }` passes
    (re.compile(r"\{[^{}]*(?:[\w\]]\s*(?:[-+*/%&|^]|<<|>>)?=\s*[^=\s][^{};]*|\w\([^{};]*\)|\breturn\b[^{};]*);\s*\}"), "C block on one line"),
    # C braces: a lone `{`, a line starting with `}`, a line ending in `{`. Our set notation `{a, b}`, `{hi:lo}` passes
    (re.compile(r"^\s*\{\s*$|^\s*\}|\{\s*$"), "brace"),
    (re.compile(r"->"), "-> pointer form"),
    (re.compile(r"\*\(\s*(?:const\s+)?(?:u?int\d*(?:_t)?|char|short|long|byte|bool|float|double|void|[A-Z_]\w*)\s*\*"), "*( pointer form"),
    # a C cast: a pointer cast, or a cast glued to its operand. An integer-semantics note `(unsigned)`, `(int32)` passes
    (re.compile(r"\((?:u?int|short|long|char|byte|word|dword|bool|float|double|void|unsigned|signed|size_t"
                r"|u?int\d+_t|[A-Z]{3,})\s*\*+\s*\)|\((?:u?int|short|long|char|byte|word|dword|bool|float|double|void"
                r"|unsigned|signed|size_t|u?int\d+_t|[A-Z]{3,})\)(?=[\w(*&-])"), "C cast"),
    (re.compile(r"\bgoto\s+LAB_\w*|\bLAB_\w+"), "goto / label"),   # our pseudocode's `goto next`, `goto retry` is notation
    (re.compile(r"^\s*(?:[a-z]+_\w+|\w*_r0x\w*):\s*$"), "label"),
    (re.compile(r"__\w+"), "calling-convention word"),
    (re.compile(r"\b(?:param_\d+|local_[0-9A-Fa-f]+|[a-z]?[uibcsl]Var\d+|FUN_\w*|DAT_\w*|PTR_\w*)"), "decompiler name"),
]


def _run_git(*args):
    try:
        out = subprocess.run(["git", "-C", os.path.dirname(os.path.abspath(__file__)), *args],
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


@functools.lru_cache(maxsize=1)
def git_identity():
    """Identity strings of this machine and working repository, read from git at run time (never stored)."""
    ids = set()
    for line in _run_git("remote", "-v").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            url = parts[1]
            ids.add(url)
            name = re.sub(r"\.git$", "", url.rstrip("/").rsplit("/", 1)[-1])
            ids.add(name)
    ids.add(_run_git("config", "user.email"))
    for d in (_run_git("rev-parse", "--show-toplevel"),
              os.path.dirname(_run_git("rev-parse", "--path-format=absolute", "--git-common-dir"))):
        if d:
            ids.add(os.path.basename(d.rstrip("/")))
            ids.add(re.sub(r"-[a-z0-9]+$", "", os.path.basename(d.rstrip("/"))))
    return tuple(sorted(i for i in ids if len(i) >= 4))


# ---------------------------------------------------------------- the hex allowance (owner decision, 2026-11-17)
# Game math that is written in hex is not a code address: RNG seeds used as illustrative examples, the RNG
# multiplier and similar named constants (a short reviewed list, docs/export/allow-hex.txt, each entry with a
# reason), and the draw values in the calculation panels of a schematic illustration folder (a scoped rule).
# Never allowed by a wildcard (a section, a `lo =`/`seed`/`draw` shape): a value in the code image's range, the
# pinned Game.exe's whole mapped image 0x00400000-0x009B9FFF (image base 0x400000 + SizeOfImage 0x5BA000; .text,
# .rdata, .data/.bss, .rsrc, .reloc), a `sub_`/`DAT_` name, a `+0x` offset, a hex after `_` or `+`. A value in
# that range passes only by name: a `pin` entry (one value, one page, a reason; architect review 2026-11-17) or a
# brace seed state `{hi:lo}` / `{start, 666}` printed by a schematic generator. (ADR-0031: it lists constants of the
# code image; the allowlist names only values that are our model's own inputs or game-math constants, never a
# table's contents or an address.)
IMAGE_LO, IMAGE_HI = 0x00400000, 0x009B9FFF
RE_HEXTOK = re.compile(r"(?:0x)?[0-9A-Fa-f]+$")
HEX_WHATS = ("address / hex of 6+ digits", "hex of 6+ digits", "commit hash")
# the shapes the schematic generators print for a draw: a seed state {hi:lo}, `{start, 666} = {hex, 666}`,
# and `lo = 0x...`, `lo 0x...`, `seed 0x...` inside a calculation line
RE_DRAW_CTX = [
    re.compile(r"\{[0-9a-f]{8}:[0-9a-f]{8}\}"),
    re.compile(r"\{[0-9a-f]{8}, \d+\}"),
    re.compile(r"\b(?:lo|seed|draw)\s*=?\s*0x[0-9a-f]{1,8}\b"),
]


def hex_value(tok):
    return int(tok[2:] if tok[:2].lower() == "0x" else tok, 16)


def in_image(v):
    return IMAGE_LO <= v <= IMAGE_HI


class Allow:
    """values: {int: reason}; sections: {(docs path, heading prefix): reason}; pins: {docs path: {int: reason}}
    (values in the code image's range, each allowed on one page only) of the allowlist file."""

    def __init__(self, values=None, sections=None, pins=None):
        self.values = dict(values or {})
        self.sections = dict(sections or {})
        self.pins = {k: dict(v) for k, v in (pins or {}).items()}


class SectionTracker:
    """Which lines of a page sit under an allowed section (a worked example whose values are illustrative game
    math). Feed each heading as it comes; `.on` says whether the text after it is in scope."""

    def __init__(self, allow, path):
        self.prefixes = [h.lower() for (p, h) in allow.sections if p == path]
        self.level = None
        self.on = False

    def heading(self, level, text):
        if self.on and level <= self.level:
            self.on = False
        if not self.on and any(text.lower().startswith(h) for h in self.prefixes):
            self.on, self.level = True, level
        return self.on


def load_allow(path):
    """Read docs/export/allow-hex.txt: `<hex value> <one-line reason>` per line, `#` comments. Raises ValueError
    on a malformed line, an entry without a reason, or a value entry in the code image's range. A value in that range
    may be named only by `pin <hex> <docs path> :: <reason>` (that page only), and never one re/symbols.csv names."""
    vals, secs, pins = {}, {}, {}
    syms = symbol_values()
    for n, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.split(" # ", 1)[0].strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("section "):
            m = re.fullmatch(r"section\s+(\S+)\s+(.+?)\s+::\s+(.+)", line)
            if not m:
                raise ValueError(f"{path}:{n}: want `section <docs path> <heading start> :: <reason>`")
            secs[(m.group(1), m.group(2))] = m.group(3)
            continue
        if line.startswith("pin "):
            m = re.fullmatch(r"pin\s+(\S+)\s+(\S+)\s+::\s+(.+)", line)
            if not m or not RE_HEXTOK.match(m.group(1)) or len(re.sub(r"^0[xX]", "", m.group(1))) < 6:
                raise ValueError(f"{path}:{n}: want `pin <hex of 6+ digits> <docs path> :: <reason>`")
            v = hex_value(m.group(1))
            if v in syms:
                raise ValueError(f"{path}:{n}: {m.group(1)} is a named address in re/symbols.csv; refused")
            pins.setdefault(m.group(2), {})[v] = m.group(3)
            continue
        f = line.split(None, 1)
        if len(f) < 2 or not RE_HEXTOK.match(f[0]) or len(re.sub(r"^0[xX]", "", f[0])) < 6:
            raise ValueError(f"{path}:{n}: want `<hex of 6+ digits> <reason>`")
        v = hex_value(f[0])
        if in_image(v):
            raise ValueError(f"{path}:{n}: {f[0]} is in the code image's range; refused")
        vals[v] = f[1].strip()
    return Allow(vals, secs, pins)


def symbol_values():
    """The addresses re/symbols.csv names (empty when the file is not there): a pin may not name one."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "re", "symbols.csv")
    if not os.path.isfile(p):
        return set()
    return {int(m.group(1), 16) for m in re.finditer(r"^0x([0-9A-Fa-f]{6,8}),", open(p, encoding="utf-8").read(), re.M)}


ACTIVE_ALLOW = Allow()


def set_allow(allow):
    global ACTIVE_ALLOW
    ACTIVE_ALLOW = allow if allow is not None else Allow()


def _allowed_hex(line, m, what, allow, scoped, sect=False, pins=()):
    """True when the hex-shaped match m of rule text `what` is game math the allowance admits."""
    if what not in HEX_WHATS:
        return False
    tok = m.group(0)
    if not RE_HEXTOK.match(tok):
        return False
    before = line[m.start() - 1] if m.start() else ""
    if before and before in "_+":
        return False
    v = hex_value(tok)
    if scoped:
        for k, rx in enumerate(RE_DRAW_CTX):
            for cm in rx.finditer(line):
                if cm.start() <= m.start() and m.end() <= cm.end() and (k < 2 or not in_image(v)):
                    return True
    if v in pins:
        return True
    if in_image(v):
        return False
    return sect or v in allow.values


def check_text(text, identity=None, line0=1, allow=None, scoped=False, sect_lines=None, sect=False, pins=()):
    """X1-X5 and X9 on one unit of text. Returns [(rule, line, detail)]; line counts from line0.
    A fenced block in the unit is tracked: X5 applies to its lines unless the fence is `mermaid`.
    `allow` (default: the one set with set_allow) admits listed game-math hex values; `scoped` also admits the
    draw shapes of a schematic illustration folder's calculation panels (RE_DRAW_CTX); `sect` (every line) or
    `sect_lines` (line numbers) admit any hex of a worked example's section (Allow.sections), image range aside."""
    if identity is None:
        identity = git_identity()
    if allow is None:
        allow = ACTIVE_ALLOW
    hits = []
    fence = None  # (marker char run, lang)
    for i, line in enumerate(text.split("\n")):
        n = line0 + i
        m = RE_FENCE.match(line)
        if m and fence is None:
            fence = (m.group(1)[0], m.group(2).lower())
        elif m and fence is not None and m.group(1)[0] == fence[0] and not m.group(2):
            fence = None
        elif fence is not None and fence[1] != "mermaid":
            for rx, what in RE_BLOCK_BAD:
                if rx.search(line):
                    hits.append(("X5", n, f"decompiler-like block line ({what}): {line.strip()[:60]}"))
                    break
        for rule, table in (("X1", RE_X1), ("X2", RE_X2), ("X3", RE_X3), ("X9", RE_X9)):
            for rx, what in table:
                mm = next((x for x in rx.finditer(line) if not _allowed_hex(line, x, what, allow, scoped, sect or (sect_lines is not None and n in sect_lines), pins)), None)
                if mm:
                    hits.append((rule, n, f"{what}: {mm.group(0)[:40]}"))
                    break
        low = line.lower()
        for ident in identity:
            if ident and ident.lower() in low:
                hits.append(("X4", n, "identity string of this machine or repository"))
                break
        else:
            mm = RE_HOME.search(line) or RE_ABS.search(line)
            if mm:
                hits.append(("X4", n, f"absolute path: {mm.group(0)[:40]}"))
    return hits


def text_rules(unit, identity=None, allow=None, sect=False, pins=()):
    """The set of rule ids (X1-X5, X9) that one unit of text fails. For the builder's simplifier; `sect` when the
    unit sits in an allowed worked-example section, `pins` the page's pinned values."""
    return {h[0] for h in check_text(unit, identity, allow=allow, sect=sect, pins=pins)}


# ---------------------------------------------------------------- page rules

RE_RAW_HTML = re.compile(r"<\s*(?:script|iframe|link|style|object|embed|form|meta|base)\b", re.I)
RE_IMG = re.compile(r"!\[[^\]]*\](\(([^)\s]*)[^)]*\))?|<\s*(?:img|video|picture|source)\b", re.I)
RE_ILLUS = re.compile(r"^/illustrations/([\w.-]+)/([\w./-]+)$")   # root-absolute only: the site prefixes its base
RE_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def tables(text):
    """Yield (header line number, body row count) of each pipe table outside fences."""
    lines = text.split("\n")
    fence = False
    i = 0
    while i < len(lines):
        if RE_FENCE.match(lines[i]):
            fence = not fence
        if (not fence and lines[i].lstrip().startswith("|") and i + 1 < len(lines)
                and RE_TABLE_SEP.match(lines[i + 1]) and "|" in lines[i + 1]):
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
            yield i + 1, j - i - 2
            i = j
            continue
        i += 1


def table_row_names(text):
    names = set()
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("|") and not RE_TABLE_SEP.match(s):
            cells = [c.strip().strip("`").strip() for c in s.strip("|").split("|")]
            if cells and cells[0]:
                names.add(cells[0].lower())
    return names


def parse_manifest(path):
    """Return (routes of pages, {route: number of oversized tables the manifest allows})."""
    groups, routes, allowed = {}, {}, {}
    if not path or not os.path.isfile(path):
        return routes, allowed
    pages, tabs = [], []
    for raw in open(path, encoding="utf-8"):
        f = raw.split("#", 1)[0].split()
        if not f:
            continue
        if f[0] == "page" and len(f) >= 3:
            pages.append(f[1:])
        elif f[0] == "table" and len(f) >= 3:
            tabs.append(f[1])
    for p in pages:
        stem = os.path.splitext(os.path.basename(p[0]))[0]
        route = stem if p[1] == "-" else f"{p[1]}/{stem}"
        routes[p[0]] = route
    for t in tabs:
        route = routes.get(t)
        if route:
            allowed[route] = allowed.get(route, 0) + 1
    return routes, allowed


def section_lines(text, path, allow):
    """Line numbers (1-based) of a page that sit under one of the allowlist's sections for `path`."""
    tr, lines, fence = SectionTracker(allow, path), set(), False
    if not allow.sections:
        return lines
    for n, line in enumerate(text.split("\n"), 1):
        if RE_FENCE.match(line):
            fence = not fence
        h = None if fence else re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if h:
            tr.heading(len(h.group(1)), h.group(2))
        if tr.on:
            lines.add(n)
    return lines


def check_page(text, rel, route, allowed_tables, illus_ok, identity, path=None):
    """All rules that apply to one Markdown page of the cut. Returns [(rule, line, detail)]."""
    hits = list(check_text(text, identity, sect_lines=section_lines(text, path, ACTIVE_ALLOW) if path else None,
                           pins=ACTIVE_ALLOW.pins.get(path, {}) if path else ()))
    over = [(ln, n) for ln, n in tables(text) if n > TABLE_LIMIT]
    for ln, n in over[allowed_tables:]:
        hits.append(("X6", ln, f"table of {n} body rows (limit {TABLE_LIMIT}) not named in the manifest"))
    for n, line in enumerate(text.split("\n"), 1):
        mm = re.search(r"\b(?:https?|ftp|mailto|javascript):|\bfile:/"
                       r"|\]\(\s*<?//|(?:href|src)\s*=\s*[\"']?//", line, re.I)
        if mm:
            hits.append(("X7", n, f"external link or scheme: {mm.group(0)[:20]}"))
        mm = RE_RAW_HTML.search(line)
        if mm:
            hits.append(("X7", n, f"raw HTML: {mm.group(0)}"))
        if re.search(r"@import|\burl\(", line, re.I):
            hits.append(("X7", n, "@import / url("))
        for im in RE_IMG.finditer(line):
            target = im.group(2)
            m2 = RE_ILLUS.search(target) if target else None
            if not (m2 and (m2.group(1), m2.group(2)) in illus_ok):
                hits.append(("X8", n, f"image: {im.group(0)[:50]}"))
    return hits


def x12(text, rel, known):
    out = []
    fence = False
    for n, line in enumerate(text.split("\n"), 1):
        if RE_FENCE.match(line):
            fence = not fence
            continue
        if fence or line.lstrip().startswith("#"):
            continue
        for q in re.finditer(r"\"([^\"]{20,})\"|“([^”]{20,})”", line):
            body = q.group(1) or q.group(2)
            if len(body.split()) > 12:
                out.append((n, f"quoted run of {len(body.split())} words"))
        plain = re.sub(r"`[^`]*`", " ", line)
        for m in re.finditer(r"(?:[A-Z][a-z']+(?: [A-Z][a-z']+)+)", plain):
            words = m.group(0).split()
            if m.start() == 0 or re.search(r"[.!?:]\s$|^\s*(?:[-*>|]|\d+\.)\s$", plain[:m.start()]):
                words = words[1:]
            name = " ".join(words)
            if len(words) >= 2 and name.lower() not in known:
                out.append((n, f"capitalised name not in any table row: {name}"))
    return out


# ---------------------------------------------------------------- schematic folders

def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def verify_illustration(folder, identity=()):
    """Check one site/public/illustrations/<id>/ folder (ADR-0036).
    Returns (problems [str], allowed relative files set)."""
    probs = []
    files = []
    for dp, dns, fns in os.walk(folder):
        for dn in list(dns):
            if dn == ".git" or os.path.islink(os.path.join(dp, dn)):
                probs.append(f"{dn}: .git directory or symlink")
                dns.remove(dn)
        for fn in fns:
            full = os.path.join(dp, fn)
            files.append(os.path.relpath(full, folder).replace(os.sep, "/"))
    listing = None
    sj = os.path.join(folder, "schematic.json")
    if not os.path.isfile(sj):
        return ["no schematic.json"], set()
    try:
        data = json.load(open(sj, encoding="utf-8"))
        if data.get("marker") != MARKER or not isinstance(data.get("files"), dict):
            raise ValueError
        if "tool" in data:
            return ["schematic.json names a tool (the published file must not tie to the working repository)"], set()
        listing = data["files"]
    except (ValueError, OSError, AttributeError):
        return ["schematic.json unreadable or wrong marker"], set()
    # schematic.json is published too: its arguments pass the text rules (hashes aside)
    meta = dict(data, files=sorted(listing))
    for r_, ln, d in [h for h in check_text(json.dumps(meta, indent=1), identity) if h[0] != "X5"][:5]:
        probs.append(f"schematic.json:{ln}: {r_} {d}")
    ok = set()
    for rel in sorted(files):
        if rel == "schematic.json":
            continue
        full = os.path.join(folder, rel)
        base = os.path.basename(rel)
        ext = os.path.splitext(base)[1].lower()
        if os.path.islink(full):
            probs.append(f"{rel}: symlink")
            continue
        if not (ext in (".gif", ".png") or rel in ("index.html", "steps.json")):
            probs.append(f"{rel}: file type not allowed in an illustration folder")
            continue
        if rel not in listing:
            probs.append(f"{rel}: not in schematic.json (extra file)")
            continue
        if _sha(full) != str(listing[rel]).lower():
            probs.append(f"{rel}: sha256 differs from schematic.json")
            continue
        with open(full, "rb") as f:
            data_b = f.read()
        if MARKER.encode() not in data_b:
            probs.append(f"{rel}: no schematic marker")
            continue
        # captions and calculation text pass the check like page text (plan 0070 design); hex colours aside.
        # Every file's bytes are also searched for identity strings and home paths (architect review 2026-11-17).
        low_b = data_b.lower()
        if any(i and i.lower().encode() in low_b for i in identity) or RE_HOME.search(
                data_b.decode("latin-1")):
            probs.append(f"{rel}: identity string or home path in the file")
            continue
        if rel in ("index.html", "steps.json"):
            txt = re.sub(r"#[0-9A-Fa-f]{3,8}\b", "#", data_b.decode("utf-8", "replace"))
            bad = [h for h in check_text(txt, identity, scoped=True) if h[0] != "X5"]
            if bad:
                probs.extend(f"{rel}:{ln}: {r_} {d}" for r_, ln, d in bad[:5])
                continue
        if rel == "index.html":
            for p in html_problems(data_b.decode("utf-8", "replace"), set(files)):
                probs.append(f"index.html: {p}")
            if any(p.startswith("index.html") for p in probs):
                continue
        ok.add(rel)
    for rel in listing:
        if rel not in files:
            probs.append(f"{rel}: listed in schematic.json but missing")
    return probs, ok


def html_problems(html, files):
    out = []
    if re.search(r"(?:https?|ftp|wss?):|//[\w-]+\.[a-z]{2,}", html, re.I):
        out.append("external URL")
    if re.search(r"\bfetch\s*\(|XMLHttpRequest|WebSocket|sendBeacon|EventSource|importScripts|\bimport\s*\(|@import",
                 html):
        out.append("network request or import")
    if re.search(r"<\s*(?:iframe|link|object|embed|form|meta|base)\b", html, re.I):
        out.append("forbidden element")
    for m in re.finditer(r"""\b(?:src|href|action|poster|data|srcset)\s*=\s*["']([^"']*)["']""", html, re.I):
        v = m.group(1).strip()
        if v.startswith("#") or v == "":
            continue
        if re.match(r"^[a-z][a-z0-9+.-]*:", v, re.I) or v.startswith("/") or ".." in v.split("/") \
                or v.split("#")[0].split("?")[0] not in files:
            out.append(f"src/href outside the folder: {v[:40]}")
    for m in re.finditer(r"\burl\(\s*([^)]*)\)", html, re.I):
        out.append(f"url( reference: {m.group(1)[:30]}")
    return out


# ---------------------------------------------------------------- cut mode

def check_cut(cut, manifest=None, identity=None):
    """Return (failures, warnings), each [(rule, path, line, detail)]."""
    fails, warns = [], []
    if identity is None:
        identity = git_identity()
    routes, allowed = parse_manifest(manifest)
    route_path = {v: k for k, v in routes.items()}
    docs_root = "site/src/content/docs/"
    illus_root = "site/public/illustrations/"
    rels = []
    for dp, dns, fns in os.walk(cut):
        for dn in list(dns):
            full = os.path.join(dp, dn)
            if dn == ".git":
                fails.append(("X11", os.path.relpath(full, cut), 0, ".git directory"))
                dns.remove(dn)
            elif os.path.islink(full):
                fails.append(("X11", os.path.relpath(full, cut), 0, "symlink"))
                dns.remove(dn)
        for fn in fns:
            rels.append(os.path.relpath(os.path.join(dp, fn), cut).replace(os.sep, "/"))
    illus_ok = set()
    folders = {}
    for rel in rels:
        if rel.startswith(illus_root) and rel.count("/") >= illus_root.count("/") + 1:
            folders.setdefault(rel[len(illus_root):].split("/", 1)[0], []).append(rel)
    for fid in sorted(folders):
        probs, ok = verify_illustration(os.path.join(cut, illus_root + fid), identity)
        for p in probs:
            fails.append(("X11", f"{illus_root}{fid}/", 0, p))
        for rel in ok:
            illus_ok.add((fid, rel))
    cut_json_seen = False
    known, pages = set(), []
    for rel in sorted(rels):
        full = os.path.join(cut, rel)
        if rel == "report.txt":
            continue
        if os.path.islink(full):
            fails.append(("X11", rel, 0, "symlink"))
            continue
        if rel.startswith(illus_root) and rel.count("/") >= illus_root.count("/") + 1:
            continue
        ext = os.path.splitext(rel)[1].lower()
        if rel == "site/src/cut.json":
            cut_json_seen = True
            try:
                d = json.load(open(full, encoding="utf-8"))
                if not re.fullmatch(r"\d{4}-\d\d-\d\d", str(d.get("date", ""))):
                    raise ValueError
            except (ValueError, OSError, AttributeError):
                fails.append(("X10", rel, 0, "cut.json has no date (YYYY-MM-DD)"))
            continue
        if ext == ".md":
            text = open(full, encoding="utf-8", errors="replace").read()
            pages.append((rel, text))
            known |= table_row_names(text)
            continue
        if ext in IMAGE_EXT:
            fails.append(("X8", rel, 0, "image file outside an illustration folder"))
        fails.append(("X11", rel, 0, "file type not allowed in the cut"))
    if not cut_json_seen:
        fails.append(("X10", "site/src/cut.json", 0, "cut.json missing"))
    for rel, text in pages:
        route = rel[len(docs_root):-3] if rel.startswith(docs_root) else rel[:-3]
        for rule, ln, d in check_page(text, rel, route, allowed.get(route, 0), illus_ok, identity, route_path.get(route)):
            fails.append((rule, rel, ln, d))
        for ln, d in x12(text, rel, known):
            warns.append(("X12", rel, ln, d))
    return fails, warns


# ---------------------------------------------------------------- repo mode

def norm_ws(s):
    return re.sub(r"\s+", " ", s).strip()


FAVICON = "site/public/favicon.svg"
FAVICON_MAX = 2048
SVG_NS = 'xmlns="http://www.w3.org/2000/svg"'


def favicon_problems(raw):
    """The favicon passes only as a small plain SVG of our own: ASCII, one root <svg> with the SVG namespace and
    nothing but svg/rect/path/circle/g elements; no link, script, style, embedded image, URL or event handler."""
    out = []
    if len(raw) > FAVICON_MAX:
        out.append("favicon over %d bytes" % FAVICON_MAX)
    try:
        t = raw.decode("ascii")
    except UnicodeDecodeError:
        return out + ["favicon is not ASCII"]
    if not t.lstrip().startswith("<svg") or t.count(SVG_NS) != 1:
        out.append("favicon is not one <svg> root with the SVG namespace")
    rest = t.replace(SVG_NS, "")
    if re.search(r"href|url\(|<script|<style|<image|<foreignObject|\bon\w+\s*=|://|data:|<!|<\?", rest, re.I):
        out.append("favicon holds a link, URL, script, style, embedded image or declaration")
    bad = sorted(set(re.findall(r"</?\s*([A-Za-z][\w:-]*)", rest)) - {"svg", "rect", "path", "circle", "g"})
    if bad:
        out.append("favicon element(s) outside svg/rect/path/circle/g: " + ", ".join(bad))
    return out


def check_repo(repo, identity=None):
    fails = []
    if identity is None:
        identity = git_identity()
    present = set()
    for dp, dns, fns in os.walk(repo):
        for dn in list(dns):
            full = os.path.join(dp, dn)
            if dn == ".git":
                fails.append(("X11", os.path.relpath(full, repo), 0, ".git directory"))
                dns.remove(dn)
            elif os.path.islink(full):
                fails.append(("X11", os.path.relpath(full, repo), 0, "symlink"))
                dns.remove(dn)
        for fn in fns:
            present.add(os.path.relpath(os.path.join(dp, fn), repo).replace(os.sep, "/"))
    for rel in sorted(present):
        full = os.path.join(repo, rel)
        if os.path.islink(full):
            fails.append(("X11", rel, 0, "symlink"))
            continue
        if rel == FAVICON:
            # the site's own icon (Starlight links /favicon.svg from every page): our own drawing, checked by shape
            # instead of by the text rules (its namespace URL and colours would trip X1, X3, X7)
            fails.extend(("X8", rel, 0, d) for d in favicon_problems(open(full, "rb").read()))
            continue
        if os.path.splitext(rel)[1].lower() in IMAGE_EXT:
            fails.append(("X8", rel, 0, "image file"))
        if rel not in REPO_PATHS:
            fails.append(("X11", rel, 0, "path outside the export repository's file list"))
            continue
        raw = open(full, "rb").read()
        if b"\0" in raw:
            fails.append(("X11", rel, 0, "binary file"))
            continue
        text = raw.decode("utf-8", "replace")
        for rule, ln, d in check_text(text, identity):
            # repo files are not pseudocode (no X5); the lockfile gets X4 only (its hashes are hex)
            if rule != "X5" and (rel != "site/package-lock.json" or rule == "X4"):
                fails.append((rule, rel, ln, d))
        lock = rel == "site/package-lock.json"
        for n, line in enumerate(text.split("\n"), 1):
            for m in re.finditer(r"https?://[^\s\"'<>)\]`]+|http:", line, re.I):
                u = m.group(0).lower()
                ok = u.startswith(URL_ALLOW) or bool(RE_URL_ALLOW.match(u)) or (lock and u.startswith(URL_ALLOW_LOCKFILE))
                if not ok:
                    fails.append(("X7", rel, n, f"URL outside the allowlist: {m.group(0)[:60]}"))
            u = re.match(r"\s*-?\s*uses:\s*(\S+)", line)
            if u and not u.group(1).startswith("actions/"):
                fails.append(("X7", rel, n, f"action outside actions/*: {u.group(1)}"))
    fp = os.path.join(repo, "site/src/components/Footer.astro")
    if os.path.isfile(fp):
        m = re.search(r"<p\b[^>]*>(.*?)</p>", open(fp, encoding="utf-8").read(), re.S)
        if not m or norm_ws(re.sub(r"<[^>]+>", "", m.group(1))) != norm_ws(FOOTER):
            fails.append(("X10", "site/src/components/Footer.astro", 0, "footer differs from the footer word for word"))
    else:
        fails.append(("X10", "site/src/components/Footer.astro", 0, "footer component missing"))
    cp = os.path.join(repo, "site/astro.config.mjs")
    if not os.path.isfile(cp) or not re.search(r"Footer\s*:\s*['\"]\./src/components/Footer\.astro['\"]",
                                               open(cp, encoding="utf-8").read()):
        fails.append(("X10", "site/astro.config.mjs", 0, "footer component not registered"))
    return fails


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cut", nargs="?", help="the cut directory (workspace/export/)")
    ap.add_argument("--repo", help="the export repository's files (workspace/export-repo/)")
    ap.add_argument("--manifest", help="manifest.txt (default docs/export/manifest.txt of this repository)")
    ap.add_argument("--identity", action="append", default=[], help="extra identity string (tests)")
    ap.add_argument("--allow-hex", help="the hex allowlist (default docs/export/allow-hex.txt of this repository)")
    ap.add_argument("--no-allow-hex", action="store_true", help="no hex allowlist (the scoped rule for illustration "
                    "folders stays)")
    ap.add_argument("--no-git-identity", action="store_true", help="do not read identity from git (tests)")
    a = ap.parse_args(argv)
    if not a.cut and not a.repo:
        ap.error("give a cut directory, --repo, or both")
    identity = tuple(a.identity) if a.no_git_identity else tuple(a.identity) + git_identity()
    manifest = a.manifest or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "export",
                                          "manifest.txt")
    if not a.no_allow_hex:
        ap_ = a.allow_hex or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "export",
                                          "allow-hex.txt")
        try:
            set_allow(load_allow(ap_) if os.path.isfile(ap_) else Allow())
        except ValueError as e:
            print(f"export_check: {e}", file=sys.stderr)
            return 2
    fails, warns = [], []
    if a.cut:
        if not os.path.isdir(a.cut):
            print(f"export_check: {a.cut} is not a directory", file=sys.stderr)
            return 2
        f, w = check_cut(a.cut, manifest, identity)
        fails += [("cut",) + x for x in f]
        warns += [("cut",) + x for x in w]
    if a.repo:
        if not os.path.isdir(a.repo):
            print(f"export_check: {a.repo} is not a directory", file=sys.stderr)
            return 2
        fails += [("repo",) + x for x in check_repo(a.repo, identity)]
    for kind, rule, path, ln, d in fails:
        print(f"FAIL {rule} {kind}:{path}:{ln}: {d}")
    for kind, rule, path, ln, d in warns:
        print(f"WARN {rule} {kind}:{path}:{ln}: {d}")
    by = {}
    for x in fails:
        by[x[1]] = by.get(x[1], 0) + 1
    print(f"CHECK export: {len(fails)} failures, {len(warns)} warnings"
          + (" (" + ", ".join(f"{k} {v}" for k, v in sorted(by.items(), key=lambda kv: int(kv[0][1:]))) + ")" if by else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Clean-room sandbox for plan 0064 / ADR-0032: build it, score a candidate in it, audit a lane's transcript.

    python3 -I tools/cleanroom.py make SLICE [--out DIR] [--set SET.jsonl] [--game DATA_DIR] [--force]
    python3 -I tools/cleanroom.py score SLICE CANDIDATE.jsonl [--out DIR] [--set SET.jsonl] [--limit N]
    python3 -I tools/cleanroom.py audit TRANSCRIPT.jsonl [--slice SLICE | --sandbox DIR] [--allow PATH ...] [--cwd DIR]
    python3 -I tools/cleanroom.py reference SLICE OUT.jsonl [--set SET.jsonl] [--excel DIR]   # the project's own model
    python3 -I tools/cleanroom.py slices

Slices (plan 0064): S1 seeds (chain.A, chain.B), S2 drops (chain.G1), S3 pools (monsters.pool), S4 DRLG (drlg.maze,
drlg.outdoor). Built sandboxes live under workspace/cleanroom/<slice>/ (gitignored) and are never committed.

make: a plain directory (with an empty git repository of its own: without one git finds the project's history above the
  sandbox) holding the tracked files of docs/specs, docs/tables,
  docs/formats (without docs/formats/golden/, which holds expected values) and docs/glossary.md, as of the working
  tree; data/ with the extracted excel tables (S4 adds the DS1 and DT1 files, hard links else copies; excel files are copied);
  cases.jsonl, the slice's cases with inputs only; score.sh; MANIFEST.json. It checks that docs/findings, re, tools,
  .claude and any Game.exe are absent. An existing tree is rebuilt only with --force (code and candidates stay).
score: the full set is cut to the slice (its case types, its field prefixes, nothing else), then `tools/golden.py
  check` runs on the cut; every call appends a line to <sandbox>/score-log.jsonl (the first line is the first pass).
audit: reads a Claude Code subagent transcript and lists every path the lane touched outside its sandbox. Exit 0
  clean, 1 with violations. Shape assumed (Claude Code session JSONL): one JSON object per line; an assistant line
  {"type":"assistant","cwd":"...","message":{"content":[{"type":"tool_use","name":T,"input":{...}}]}}; a bare
  {"type":"tool_use","name":T,"input":{...}} line is read too, and so is a JSON array of lines. Inputs read:
  Read/Write/Edit/MultiEdit `file_path`, NotebookEdit `notebook_path`, Grep/Glob/LS `path` (absent means the cwd),
  Glob `pattern` and Grep `glob` when absolute or naming a project folder, Bash `command` (every path-like word,
  `cd` tracked, `-c` code scanned for absolute paths). A relative word is judged against the line's `cwd`
  (--cwd when the line has none); it counts only if it exists or starts with a project folder name. Allowed besides
  the sandbox: system library paths and --allow. Running `python3 .../tools/golden.py check|...` or
  `.../tools/cleanroom.py score` is allowed (the script word only); reading either is not.
reference: writes the project's own candidate for a world slice (S1, S3) from tools/chain.py (via golden.py), to test
  that `score` passes on a correct candidate. Reads the game's excel tables.

Stdlib only.
"""
import argparse
import collections
import datetime
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_SET = os.path.join(ROOT, "workspace", "golden-v1-full.jsonl")
DEFAULT_DATA = os.path.join(ROOT, "workspace", "merged", "data")

ALLOWED_DOCS = ("docs/specs", "docs/tables", "docs/formats", "docs/glossary.md")
EXCLUDED_DOCS = ("docs/formats/golden/",)       # the committed sample holds expected values
FORBIDDEN = ("docs/findings", "re", "tools", ".claude", "game.exe")     # names that must be absent from a sandbox
PROJECT_DIRS = {"docs", "re", "tools", ".claude", "workspace", "findings", "game.exe", "specs", "tables", "formats"}

# slice -> (case types, field prefixes, ds1/dt1 wanted, what it is)
SLICES = collections.OrderedDict([
    ("S1", (("world",), ("chain.A", "chain.B"), False, "seeds")),
    ("S2", (("drop",), ("chain.G1",), False, "drops")),
    ("S3", (("world",), ("monsters.pool",), False, "pools")),
    ("S4", (("drlg",), ("drlg.maze", "drlg.outdoor"), True, "DRLG")),
])
INPUT_KEYS = ("id", "kind", "type", "inputs")   # what cases.jsonl keeps of a case

SYSTEM_OK = ("/usr/", "/lib/", "/lib64/", "/bin/", "/sbin/", "/dev/null", "/dev/stdin", "/dev/stdout", "/dev/stderr",
             "/etc/localtime", "/etc/os-release", "/proc/cpuinfo", "/proc/meminfo")


def stable_tool_path():
    """Path of cleanroom.py that score.sh runs. A lane worktree is removed after its merge, so prefer the main
    checkout (the parent of git's common dir) when it holds a cleanroom.py with a score command; else this file."""
    here = os.path.join(HERE, "cleanroom.py")
    try:
        out = subprocess.run(["git", "-C", HERE, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                             capture_output=True, text=True, check=True).stdout.strip()
        cand = os.path.join(os.path.dirname(out), "tools", "cleanroom.py")
        if out.endswith(".git") and os.path.isfile(cand):
            with open(cand, errors="replace") as fh:
                if "def cmd_score" in fh.read():
                    return cand
    except (OSError, subprocess.CalledProcessError):
        pass
    return here


def die(msg):
    sys.stderr.write("cleanroom: %s\n" % msg)
    raise SystemExit(2)


def slice_of(name):
    s = name.upper()
    if s not in SLICES:
        die("unknown slice %r (have %s)" % (name, ", ".join(SLICES)))
    return s


def sandbox_dir(s, out=None):
    return os.path.abspath(out) if out else os.path.join(ROOT, "workspace", "cleanroom", s)


# --- make -----------------------------------------------------------------------------------------------------------
def tracked_docs(root):
    r = subprocess.run(["git", "-C", root, "ls-files", "-z", "--"] + list(ALLOWED_DOCS), capture_output=True)
    if r.returncode != 0:
        die("git ls-files failed in %s: %s" % (root, r.stderr.decode(errors="replace").strip()))
    files = [f for f in r.stdout.decode().split("\0") if f]
    return [f for f in files if not any(f.startswith(x) for x in EXCLUDED_DOCS) and os.path.isfile(os.path.join(root, f))]


def link_or_copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.lexists(dst):
        os.remove(dst)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def read_cases(setpath):
    if not os.path.isfile(setpath):
        die("golden set not found: %s (regenerate it with tools/golden.py emit, docs/formats/golden-trace.md)" % setpath)
    with open(setpath) as fh:
        lines = [json.loads(x) for x in fh if x.strip()]
    if not lines or lines[0].get("golden") != "trace":
        die("%s: no golden-trace header on line 1" % setpath)
    return lines[0], lines[1:]


def slice_cases(cases, s):
    """The set cut to the slice: its case types, expected restricted to its prefixes, cases left empty dropped."""
    types, prefixes, _ds, _w = SLICES[s]
    out = []
    for c in cases:
        if c.get("type") not in types:
            continue
        exp = {k: v for k, v in c.get("expected", {}).items() if k.startswith(prefixes)}
        if exp:
            out.append((c, exp))
    return out


def check_clean(sb):
    """Raise on a forbidden name anywhere in the sandbox's docs/data trees (code and candidates are the lane's own)."""
    bad = []
    real_sb = os.path.realpath(sb)
    for top in ("docs", "data"):
        base = os.path.join(sb, top)
        for dp, dn, fn in os.walk(base):
            for n in dn + fn:
                full = os.path.join(dp, n)
                rel = os.path.relpath(full, sb).replace(os.sep, "/")
                if n.lower() == "game.exe" or rel in ("docs/findings",) or n == ".claude":
                    bad.append(rel)
                elif os.path.islink(full):          # a link can point at findings, re or the golden set
                    bad.append(rel + " (symlink)")
    for top in ("re", "tools", ".claude", "Game.exe", "game.exe"):
        if os.path.lexists(os.path.join(sb, top)):
            bad.append(top)
    # git walks up to the project's own repository (and its whole history) when the sandbox has none: the sandbox
    # carries an empty repository of its own, and its top level must be the sandbox itself
    r = subprocess.run(["git", "-C", sb, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if r.returncode != 0 or os.path.realpath(r.stdout.strip()) != real_sb:
        bad.append(".git (git from the sandbox reaches %s)" % (r.stdout.strip() or "no repository"))
    if bad:
        raise SystemExit("cleanroom: forbidden paths in the sandbox: %s" % ", ".join(bad))


def cmd_make(ns):
    s = slice_of(ns.slice)
    sb = sandbox_dir(s, ns.out)
    if os.path.exists(os.path.join(sb, "docs")) and not ns.force:
        die("%s already built (use --force to rebuild docs/, data/, cases.jsonl; your code stays)" % sb)
    for sub in ("docs", "data"):
        shutil.rmtree(os.path.join(sb, sub), ignore_errors=True)
    os.makedirs(sb, exist_ok=True)
    files = tracked_docs(ROOT)
    if not files:
        die("no tracked files under %s" % ", ".join(ALLOWED_DOCS))
    for f in files:
        dst = os.path.join(sb, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, f), dst)
    # game data
    gdata = ns.game or DEFAULT_DATA
    excel = os.path.join(gdata, "global", "excel")
    if not os.path.isdir(excel):
        die("no excel directory at %s (use --game DATA_DIR)" % excel)
    n_excel = 0
    for n in sorted(os.listdir(excel)):
        p = os.path.join(excel, n)
        if os.path.isfile(p):
            dst = os.path.join(sb, "data", "global", "excel", n)      # copies: a write in the sandbox must not change the master
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(p, dst)
            n_excel += 1
    n_tiles = 0
    if SLICES[s][2]:
        tiles = os.path.join(gdata, "global", "tiles")
        for dp, _dn, fn in os.walk(tiles):
            for n in sorted(fn):
                if n.lower().endswith((".ds1", ".dt1")):
                    rel = os.path.relpath(os.path.join(dp, n), gdata)
                    link_or_copy(os.path.join(dp, n), os.path.join(sb, "data", rel))
                    n_tiles += 1
    # cases, inputs only
    header, cases = read_cases(ns.set or DEFAULT_SET)
    cut = slice_cases(cases, s)
    with open(os.path.join(sb, "cases.jsonl"), "w") as fh:
        for c, _e in cut:
            fh.write(json.dumps({k: c[k] for k in INPUT_KEYS if k in c}, sort_keys=True, separators=(",", ":")) + "\n")
    tool = stable_tool_path()
    score_sh = os.path.join(sb, "score.sh")
    with open(score_sh, "w") as fh:
        fh.write("#!/bin/sh\n# Score a candidate (JSON Lines, docs/formats/golden-trace.md § Checking) for slice %s.\n"
                 "exec python3 -I %s score %s \"$@\"\n" % (s, shlex.quote(tool), s))
    os.chmod(score_sh, 0o755)
    man = {"slice": s, "what": SLICES[s][3], "case_types": list(SLICES[s][0]), "field_prefixes": list(SLICES[s][1]),
           "cases": len(cut), "excel_files": n_excel, "tile_files": n_tiles, "doc_files": len(files),
           "set_tables_digest": header.get("tables_digest"), "tool": tool}
    with open(os.path.join(sb, "MANIFEST.json"), "w") as fh:
        json.dump(man, fh, indent=1, sort_keys=True)
        fh.write("\n")
    if not os.path.isdir(os.path.join(sb, ".git")):
        subprocess.run(["git", "init", "-q", "--template=", sb], check=True, capture_output=True)
    check_clean(sb)
    print("built %s: %d doc files, %d excel files, %d tile files, %d cases (inputs only)" % (
        sb, len(files), n_excel, n_tiles, len(cut)))
    return 0


# --- score ----------------------------------------------------------------------------------------------------------
def cmd_score(ns):
    s = slice_of(ns.slice)
    if not os.path.isfile(ns.candidate):
        die("candidate not found: %s" % ns.candidate)
    sb = sandbox_dir(s, ns.out)
    with open(ns.candidate) as fh:                  # a malformed candidate is not a run: it is not logged
        for ln, x in enumerate(fh, 1):
            if not x.strip():
                continue
            try:
                o = json.loads(x)
            except ValueError as e:
                die("%s line %d: not JSON (%s); a line is {\"id\": ..., \"outputs\": {field: value}}" % (ns.candidate, ln, e))
            if not isinstance(o, dict) or ("id" not in o and o.get("golden") != "trace"):
                die("%s line %d: no \"id\"; a line is {\"id\": ..., \"outputs\": {field: value}}" % (ns.candidate, ln))
    header, cases = read_cases(ns.set or DEFAULT_SET)
    cut = slice_cases(cases, s)
    if not cut:
        die("the set has no %s cases (fields %s)" % (s, ", ".join(SLICES[s][1])))
    tdir = tempfile.mkdtemp(prefix="cleanroom-score-")      # the cut set holds expected values: never inside the sandbox
    tmp = os.path.join(tdir, "set.jsonl")
    try:
        with open(tmp, "w") as fh:
            fh.write(json.dumps(header, sort_keys=True, separators=(",", ":")) + "\n")
            for c, exp in cut:
                c2 = dict(c)
                c2["expected"] = exp
                fh.write(json.dumps(c2, sort_keys=True, separators=(",", ":")) + "\n")
        r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "golden.py"), "check", tmp, ns.candidate,
                            "--limit", str(ns.limit)], capture_output=True, text=True)
    finally:
        shutil.rmtree(tdir, ignore_errors=True)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    compared = sum(int(m.group(1)) for m in re.finditer(r"^\s+\S+\s+(\d+) compared\s+\d+ different", r.stdout, re.M))
    different = sum(int(m.group(1)) for m in re.finditer(r"^\s+\S+\s+\d+ compared\s+(\d+) different", r.stdout, re.M))
    mm = re.search(r"MISSING (\d+) cases", r.stdout)
    missing = int(mm.group(1)) if mm else 0
    entry = {"time": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             "candidate_sha256": hashlib.sha256(open(ns.candidate, "rb").read()).hexdigest()[:16],
             "fields_compared": compared, "fields_different": different, "cases_missing": missing, "exit": r.returncode}
    if os.path.isdir(sb):
        logp = os.path.join(sb, "score-log.jsonl")
        n = sum(1 for _ in open(logp)) + 1 if os.path.exists(logp) else 1
        entry["run"] = n
        with open(logp, "a") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
        print("cleanroom: slice %s run %d%s: %d fields compared, %d different, %d cases missing" % (
            s, n, " (first pass)" if n == 1 else "", compared, different, missing))
    else:
        print("cleanroom: slice %s: %d fields compared, %d different, %d cases missing (no sandbox, not logged)" % (
            s, compared, different, missing))
    return r.returncode


# --- reference ------------------------------------------------------------------------------------------------------
def cmd_reference(ns):
    s = slice_of(ns.slice)
    if SLICES[s][0] != ("world",):
        die("reference candidates exist for world slices only (S1, S3)")
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import golden
    excel = ns.excel or golden.DEFAULT_EXCEL
    _h, cases = read_cases(ns.set or DEFAULT_SET)
    n = 0
    with open(ns.out, "w") as fh:
        for c, _e in slice_cases(cases, s):
            i = c["inputs"]
            diff = i.get("difficulty")
            exp = i.get("expansion")
            out = golden.world_expected(i["seed"], diff or 0, 1 if exp is None else exp, excel, i.get("levels"))
            fh.write(golden.canon({"id": c["id"], "outputs": out}) + "\n")
            n += 1
    print("reference: %d cases written to %s" % (n, ns.out))
    return 0


# --- audit ----------------------------------------------------------------------------------------------------------
def under(path, root):
    return path == root or path.startswith(root.rstrip("/") + "/")


class Auditor:
    def __init__(self, sandboxes, allow, default_cwd):
        roots = set()
        for sb in list(sandboxes) + list(allow):
            roots.add(os.path.normpath(sb))
            roots.add(os.path.realpath(sb))
        self.roots = sorted(roots)
        self.cwd = default_cwd
        self.hits = []          # (line, tool, path, why)
        self.n_calls = 0

    def inside(self, p):
        a = os.path.normpath(p)
        b = os.path.realpath(p)          # the real target decides: a symlink inside the sandbox may point out of it
        return any(under(b, r) for r in self.roots) or any(a.startswith(x) for x in SYSTEM_OK)

    def resolve(self, p, cwd):
        p = os.path.expanduser(p)
        return os.path.normpath(p if os.path.isabs(p) else os.path.join(cwd, p))

    def check_path(self, line, tool, p, cwd, strict=True):
        """strict: the word is certainly a path (a tool's path argument). Else a Bash word: relative ones count only
        if they exist or start with a project folder name."""
        if not p:
            return
        base = re.split(r"[*?\[{]", p, maxsplit=1)[0] or "."         # a glob: judge the part before the first wildcard
        r = self.resolve(base, cwd)
        if self.inside(r):
            return
        if not strict and not os.path.isabs(os.path.expanduser(p)):
            names = {x.lower() for x in p.replace("\\", "/").split("/")}
            if not names & PROJECT_DIRS and not os.path.exists(r):
                return
        self.hits.append((line, tool, p if os.path.isabs(p) else "%s (= %s)" % (p, r), "outside the sandbox"))

    @staticmethod
    def strip_heredocs(cmd):
        """Drop heredoc bodies (their text is data, not a command): keep the line with `<<WORD`, skip to the delimiter."""
        out = []
        pending = []                    # (delimiter, tabs stripped) in order of appearance on the opening line
        for ln in cmd.split("\n"):
            if pending:
                d, dash = pending[0]
                if (ln.strip("\t") if dash else ln) == d:
                    pending.pop(0)
                continue
            out.append(ln)
            pending = [(m.group(2), m.group(1) == "-")
                       for m in re.finditer(r"<<(-?)\s*['\"\\]?([A-Za-z_][A-Za-z0-9_]*)['\"]?", ln)]
        return "\n".join(out)

    def bash(self, line, cmd, cwd):
        cmd = self.strip_heredocs(cmd)
        try:
            lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
            lex.whitespace_split = True
            words = list(lex)
        except ValueError:
            words = cmd.split()
        seg = []
        segs = []
        for w in words:
            if w and set(w) <= set("();<>|&"):
                segs.append(seg)
                seg = []
                if w in (">", ">>", "<"):
                    seg.append(w)
                continue
            seg.append(w)
        segs.append(seg)
        for seg in segs:
            if seg and seg[0] in (">", ">>", "<"):
                seg = seg[1:]
            if not seg:
                continue
            if seg[0] == "cd":
                if len(seg) > 1:
                    self.check_path(line, "Bash", seg[1], cwd, strict=True)
                    cwd = self.resolve(seg[1], cwd)
                continue
            if os.path.basename(seg[0]) == "git":       # `git show REV:docs/findings/x`: a path inside a revision
                for w in seg[1:]:
                    m = re.match(r"^[^/\s:]*:(?:\./)?(.+)$", w)
                    if m and m.group(1).split("/")[0].lower() in PROJECT_DIRS:
                        self.hits.append((line, "Bash", w, "a path inside a git revision"))
            exempt = self.exempt_script(seg)
            code = False
            for i, w in enumerate(seg):
                if i == exempt:
                    continue
                if code:
                    for m in re.finditer(r"""(?:(?<=^)|(?<=[\s'"=(,\[]))(/[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]*)*)""", w):
                        self.check_path(line, "Bash", m.group(1), cwd, strict=False)
                    code = False
                    continue
                if w in ("-c", "-e") and i > 0:
                    code = True
                    continue
                v = w
                if v.startswith("-"):
                    if "=" not in v:
                        continue
                    v = v.split("=", 1)[1]
                if re.search(r"[\s{}$`]", v) and not v.startswith(("/", "./", "../", "~")):
                    continue
                if v.startswith(("/", "~", "./", "../")) or "/" in v or v.lower() in PROJECT_DIRS:
                    self.check_path(line, "Bash", v, cwd, strict=False)
        return cwd

    @staticmethod
    def exempt_script(seg):
        """Index of the script word of `python3 [-I] .../tools/golden.py check|... ` or `.../cleanroom.py score`."""
        if not seg or not re.match(r"^python3?(\.\d+)?$", os.path.basename(seg[0])):
            return -1
        for i in range(1, len(seg)):
            if seg[i].startswith("-"):
                continue
            b = os.path.basename(seg[i])
            rest = seg[i + 1:i + 2]
            if b == "golden.py" and rest and rest[0] == "check":
                return i
            if b == "cleanroom.py" and rest and rest[0] == "score":
                return i
            return -1
        return -1

    @staticmethod
    def harness_result(p):
        """The harness's own persisted tool output: ~/.claude/projects/<proj>/<session>/tool-results/<file>."""
        r = os.path.realpath(os.path.expanduser(p))
        base = os.path.join(os.path.realpath(os.path.expanduser("~")), ".claude", "projects") + os.sep
        parts = r[len(base):].split(os.sep) if r.startswith(base) else []
        return len(parts) == 4 and parts[2] == "tool-results" and parts[3].endswith((".txt", ".json"))

    def call(self, line, cwd, name, inp):
        self.n_calls += 1
        if not isinstance(inp, dict):
            return cwd
        if name == "Bash":
            return self.bash(line, str(inp.get("command", "")), cwd) or cwd
        for k in ("file_path", "notebook_path"):
            if k in inp:
                if name == "Read" and self.harness_result(self.resolve(str(inp[k]), cwd)):
                    continue
                self.check_path(line, name, str(inp[k]), cwd, True)
        if name in ("Grep", "Glob", "LS", "Search") or ("path" in inp and name not in ("Read", "Write", "Edit")):
            self.check_path(line, name, str(inp["path"]) if inp.get("path") else cwd, cwd, True)
            for k in ("glob", "pattern"):
                if name in ("Grep", "Glob") and isinstance(inp.get(k), str) and (
                        k == "glob" or name == "Glob") and (inp[k].startswith(("/", "~")) or inp[k].split("/")[0].lower() in PROJECT_DIRS):
                    self.check_path(line, name, inp[k], cwd, True)
        return cwd


def iter_calls(obj):
    """Yield every tool_use dict in a transcript line, whatever its nesting."""
    if isinstance(obj, dict):
        if obj.get("type") == "tool_use" and "name" in obj:
            yield obj
            return
        for v in obj.values():
            yield from iter_calls(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_calls(v)


def audit_file(path, sandboxes, allow, default_cwd):
    a = Auditor(sandboxes, allow, default_cwd)
    bad_lines = 0
    with open(path, errors="replace") as fh:
        text = fh.read()
    records = []
    st = text.lstrip()
    if st.startswith("["):
        try:
            records = [(i + 1, o) for i, o in enumerate(json.loads(st))]
        except ValueError:
            pass
    if not records:
        for i, x in enumerate(text.splitlines(), 1):
            if not x.strip():
                continue
            try:
                records.append((i, json.loads(x)))
            except ValueError:
                bad_lines += 1
    cwd = default_cwd
    for ln, o in records:
        if isinstance(o, dict) and isinstance(o.get("cwd"), str):
            cwd = o["cwd"]
        for c in iter_calls(o):
            cwd_after = a.call(ln, cwd, c.get("name"), c.get("input"))
            # a Bash `cd` carries only inside its own call (the harness resets the shell between calls)
            del cwd_after
    return a, bad_lines


def cmd_audit(ns):
    if ns.sandbox:
        sbs = [os.path.abspath(ns.sandbox)]
    elif ns.slice:
        sbs = [sandbox_dir(slice_of(ns.slice))]
    else:
        sbs = [os.path.join(ROOT, "workspace", "cleanroom")]
    if not os.path.isfile(ns.transcript):
        die("transcript not found: %s" % ns.transcript)
    a, bad = audit_file(ns.transcript, sbs, [os.path.abspath(p) for p in ns.allow], os.path.abspath(ns.cwd or os.getcwd()))
    seen = set()
    print("audit: %d tool calls read, allow-list %s%s" % (a.n_calls, ", ".join(sorted(set(sbs + ns.allow))),
                                                         "; %d unparsable lines skipped" % bad if bad else ""))
    n = 0
    for ln, tool, p, why in a.hits:
        k = (tool, p)
        if k in seen:
            continue
        seen.add(k)
        n += 1
        print("VIOLATION line %d %s: %s (%s)" % (ln, tool, p, why))
    if a.n_calls == 0:
        print("audit: no tool calls found: wrong file or an unknown transcript shape (not clean)")
        return 2
    print("audit: %s" % ("clean" if not n else "VOID, %d paths outside the allow-list" % n))
    return 0 if not n else 1


def cmd_slices(_ns):
    for s, (types, prefixes, ds, what) in SLICES.items():
        print("%s  %-6s types %-6s fields %s%s" % (s, what, ",".join(types), ",".join(prefixes),
                                                  "  (+ ds1/dt1 files)" if ds else ""))
    return 0


def build_parser():
    ap = argparse.ArgumentParser(prog="cleanroom.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("slice")
    m.add_argument("--out")
    m.add_argument("--set")
    m.add_argument("--game")
    m.add_argument("--force", action="store_true")
    sc = sub.add_parser("score")
    sc.add_argument("slice")
    sc.add_argument("candidate")
    sc.add_argument("--out")
    sc.add_argument("--set")
    sc.add_argument("--limit", type=int, default=20)
    au = sub.add_parser("audit")
    au.add_argument("transcript")
    au.add_argument("--slice")
    au.add_argument("--sandbox")
    au.add_argument("--allow", action="append", default=[])
    au.add_argument("--cwd")
    r = sub.add_parser("reference")
    r.add_argument("slice")
    r.add_argument("out")
    r.add_argument("--set")
    r.add_argument("--excel")
    sub.add_parser("slices")
    return ap


def main(argv):
    ns = build_parser().parse_args(argv)
    return {"make": cmd_make, "score": cmd_score, "audit": cmd_audit, "reference": cmd_reference,
            "slices": cmd_slices}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

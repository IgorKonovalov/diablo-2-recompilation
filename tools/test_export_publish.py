#!/usr/bin/env python3
"""Self-tests of tools/export_publish.py (ADR-0038, plan 0070).

Usage: python3 -I tools/test_export_publish.py

Fake target repository with a bare origin, a fake export-repository tree and injected build/check/npm runners.
Prints `TEST export_publish: N checks, M failed`.
"""
import contextlib
import io
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import export_publish as ep  # noqa: E402

checks, failed = 0, []


def ok(cond, what):
    global checks
    checks += 1
    if not cond:
        failed.append(what)
        print(f"FAIL {what}")


def sh(*cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()


def put(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def g(t, *a):
    return sh("git", "-C", t, *a)


class Env:
    def __init__(self, tmp, pages=("a.md",), reviewed=("a.md",), check_rc=0):
        self.tmp = tmp
        ws, docs = os.path.join(tmp, "ws"), os.path.join(tmp, "docs")
        ep.WS, ep.DOCS = ws, docs
        put(os.path.join(docs, "export", "manifest.txt"), "".join(f"page {p} - 1\n" for p in pages))
        put(os.path.join(docs, "export", "reviewed-pages.txt"), "# c\n\n" + "".join(f"{p}  # r\n" for p in reviewed))
        put(os.path.join(ws, "export-repo", "README.md"), "readme\n")
        put(os.path.join(ws, "export-repo", "site", "src", "components", "Footer.astro"), "f\n")
        self.origin = os.path.join(tmp, "origin.git")
        sh("git", "init", "-q", "--bare", "-b", "main", self.origin)
        self.t = os.path.join(tmp, "target")
        sh("git", "init", "-q", "-b", "main", self.t)
        for k, v in (("user.name", "t"), ("user.email", "t@t")):
            g(self.t, "config", k, v)
        put(os.path.join(self.t, ".gitignore"), "node_modules/\ndist/\n")
        put(os.path.join(self.t, "site", "src", "components", "Old.astro"), "old\n")
        put(os.path.join(self.t, "site", "src", "content", "docs", "gone.md"), "gone\n")
        g(self.t, "add", ".")
        g(self.t, "commit", "-qm", "init")
        g(self.t, "remote", "add", "origin", self.origin)
        g(self.t, "push", "-q", "origin", "main")
        put(os.path.join(self.t, "site", "node_modules", "x", "i.js"), "x\n")
        self.calls, self.check_rc, self.body = [], check_rc, "one\n"

    def run(self, cmd, cwd=None, env=None, log=None):
        self.calls.append(cmd)
        name = os.path.basename(cmd[2]) if len(cmd) > 2 and cmd[1] == "-I" else cmd[0]
        if name == "export_build.py":
            cut = cmd[cmd.index("--out") + 1]
            put(os.path.join(cut, "site", "src", "cut.json"), '{"date": "2026-01-02"}')
            put(os.path.join(cut, "site", "src", "content", "docs", "a.md"), self.body)
            put(os.path.join(cut, "site", "public", "illustrations", "i.svg"), "<svg/>")
            put(os.path.join(cut, "site", "public", "widgets", "w1", "widget.js"), "// widget\n")
            put(os.path.join(cut, "report.txt"), "r")
        if name == "export_check.py":
            return self.check_rc, "CHECK export: 1 failures"
        return 0, "all resolve"

    def go(self, *args, run=None, env=None):
        out, err = io.StringIO(), io.StringIO()
        old = dict(os.environ)
        for k in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT"):
            os.environ.pop(k, None)
        os.environ.update(env or {})
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = ep.main(["--target", self.t, "--date", "2026-01-02"] + list(args), run=run or self.run)
        finally:
            os.environ.clear()
            os.environ.update(old)
        return rc, out.getvalue(), err.getvalue()


def main():
    # push guard
    with tempfile.TemporaryDirectory() as tmp:
        e = Env(tmp)
        for var in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT"):
            rc, _, err = e.go("--push", env={var: "1"})
            ok(rc == 2 and "own terminal" in err, f"{var} refuses --push")
        ok(g(e.t, "log", "--oneline").count("\n") == 0 and not e.calls, "refusal changed nothing")
        rc, out, _ = e.go(env={"CLAUDECODE": "1"})
        ok(rc == 0, "agent run without --push is fine")
        ok(g(e.origin, "log", "--oneline", "main").count("\n") == 0, "no push under CLAUDECODE")
    # target refusals
    with tempfile.TemporaryDirectory() as tmp:
        e = Env(tmp)
        put(os.path.join(e.t, "dirty.txt"), "x")
        rc, _, err = e.go()
        ok(rc == 1 and "not clean" in err, "dirty tree refused")
        os.remove(os.path.join(e.t, "dirty.txt"))
        g(e.t, "switch", "-q", "-c", "other")
        rc, _, err = e.go()
        ok(rc == 1 and "not main" in err, "not on main refused")
        sh("git", "init", "-q", os.path.join(tmp, "plain"))
        e.t = os.path.join(tmp, "plain")
        rc, _, err = e.go()
        ok(rc == 1, "repo with no main refused")
        e.t = os.path.join(tmp, "nogit")
        os.makedirs(e.t)
        rc, _, err = e.go()
        ok(rc == 1 and "not a git repository" in err, "non-repo refused")
    # diverged and behind
    with tempfile.TemporaryDirectory() as tmp:
        e = Env(tmp)
        other = os.path.join(tmp, "other")
        sh("git", "clone", "-q", e.origin, other)
        for k, v in (("user.name", "t"), ("user.email", "t@t")):
            g(other, "config", k, v)
        put(os.path.join(other, "o.txt"), "o")
        g(other, "add", "o.txt")
        g(other, "commit", "-qm", "remote")
        g(other, "push", "-q", "origin", "main")
        rc, out, _ = e.go()
        ok(rc == 0 and "fast-forwarded 1" in out and os.path.exists(os.path.join(e.t, "o.txt")), "behind: fast-forward")
        put(os.path.join(other, "o2.txt"), "o")
        g(other, "add", "o2.txt")
        g(other, "commit", "-qm", "remote2")
        g(other, "push", "-q", "origin", "main")
        put(os.path.join(e.t, "l.txt"), "l")
        g(e.t, "add", "l.txt")
        g(e.t, "commit", "-qm", "local")
        rc, _, err = e.go()
        ok(rc == 1 and "diverged" in err, "diverged refused")
    # reviewed pages and check failure
    with tempfile.TemporaryDirectory() as tmp:
        e = Env(tmp, pages=("a.md", "b.md"), reviewed=("a.md",))
        rc, _, err = e.go()
        ok(rc == 1 and "b.md" in err and "a.md," not in err and not e.calls, "unreviewed page refused, named, before building")
    with tempfile.TemporaryDirectory() as tmp:
        e = Env(tmp, check_rc=1)
        rc, _, err = e.go()
        ok(rc == 1 and "export_check failed" in err, "check failure stops")
        ok(not os.path.exists(os.path.join(e.t, "README.md")) and not any(c[0] == "npm" for c in e.calls),
           "nothing copied or built after a failed check")
    # full run
    with tempfile.TemporaryDirectory() as tmp:
        e = Env(tmp)
        rc, out, err = e.go()
        ok(rc == 0, "full run exits 0: " + err)
        read = lambda *p: open(os.path.join(e.t, *p)).read()
        ok(read("README.md") == "readme\n" and os.path.exists(os.path.join(e.t, "site/src/components/Footer.astro")),
           "project files copied")
        ok(not os.path.exists(os.path.join(e.t, "site/src/components/Old.astro")), "deletion mirrored in components")
        ok(not os.path.exists(os.path.join(e.t, "site/src/content/docs/gone.md")), "content folder replaced wholesale")
        ok(read("site/src/content/docs/a.md") == "one\n" and os.path.exists(os.path.join(e.t, "site/public/illustrations/i.svg"))
           and os.path.exists(os.path.join(e.t, "site/src/cut.json")), "cut copied")
        ok(not os.path.exists(os.path.join(e.t, "report.txt")), "report.txt not copied")
        ok(read("site/public/widgets/w1/widget.js") == "// widget\n", "widget folders copied from the cut")
        ok("site/public/widgets/w1/widget.js" in g(e.t, "show", "--name-only", "--format=", "HEAD"), "widget folders committed")
        ok(os.path.exists(os.path.join(e.t, "site/node_modules/x/i.js")), "node_modules left alone")
        ok(os.path.isdir(os.path.join(e.t, ".git")), ".git left alone")
        ok(g(e.t, "log", "-1", "--format=%s") == "docs: cut 2026-01-02", "commit message")
        body = g(e.t, "log", "-1", "--format=%B")
        ok("Co-Authored" not in body and "Generated" not in body, "no trailers")
        ok(g(e.t, "status", "--porcelain") == "", "tree clean after commit")
        ok("site/src/components/Old.astro" in g(e.t, "show", "--name-only", "--format=", "HEAD"), "deletion committed")
        ok(g(e.origin, "log", "--oneline", "main").count("\n") == 0, "no push without --push")
        ok(not any(c[:2] == ["npm", "ci"] for c in e.calls), "npm ci skipped with lock unchanged")
        ok(any(c[:3] == ["npm", "run", "build"] for c in e.calls), "site build ran")
        ok("git -C" in out and "--push" in out, "push instructions printed")
        n = len(e.calls)
        rc, out, _ = e.go()
        ok(rc == 0 and "nothing to publish" in out and g(e.t, "rev-list", "--count", "HEAD") == "2", "unchanged cut: nothing to publish")
        e.body = "two\n"
        rc, out, _ = e.go("--skip-site-build")
        ok(rc == 0 and g(e.t, "rev-list", "--count", "HEAD") == "3" and "7 site build: skipped" in out, "changed cut: second commit")
        rc, out, _ = e.go("--push")
        ok(rc == 0 and "Pages URL" in out, "owner --push")
        ok(g(e.origin, "rev-parse", "main") == g(e.t, "rev-parse", "HEAD"), "push reached origin")
    # npm ci when node_modules missing
    with tempfile.TemporaryDirectory() as tmp:
        e = Env(tmp)
        sh("rm", "-rf", os.path.join(e.t, "site", "node_modules"))
        e.go()
        ok(any(c[:2] == ["npm", "ci"] for c in e.calls), "npm ci when node_modules missing")
    print(f"TEST export_publish: {checks} checks, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

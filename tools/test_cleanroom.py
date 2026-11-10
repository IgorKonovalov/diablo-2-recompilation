"""No-game tests for tools/cleanroom.py (plan 0064 Phase 1): python3 -I tools/test_cleanroom.py

A synthetic git repo stands in for the project, a synthetic set and excel folder for the game's data. Checks:
  - make: the tree holds docs/specs, tables, formats, glossary and no findings, re, tools, .claude, Game.exe, no .git,
    no docs/formats/golden; cases.jsonl has no `expected`, `source` or `quirks`; S4 adds the DS1/DT1 files;
  - score: a correct candidate passes, a changed field fails, a missing case fails, only the slice's fields count,
    a malformed candidate is refused and not logged, the first run is logged as the first pass;
  - audit: a planted Read of docs/findings, a Bash cat of re/, a Grep with no path from a project cwd, a Glob under
    tools, a relative `docs/findings` word are flagged; sandbox reads, system paths and `python3 -I .../golden.py check`
    are not; both transcript shapes (nested message content and bare tool_use) are read; no tool calls is exit 2.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cleanroom  # noqa: E402
import golden  # noqa: E402


class NS:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def sh(*a, cwd=None):
    subprocess.run(a, cwd=cwd, check=True, capture_output=True)


def jl(path, rows):
    with open(path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        t = os.path.realpath(self.td.name)
        self.t = t
        self.repo = os.path.join(t, "repo")
        for f in ("docs/specs/chain/README.md", "docs/specs/rng.md", "docs/tables/Levels.md", "docs/formats/ds1.md",
                  "docs/formats/golden/sample-v1.jsonl", "docs/glossary.md", "docs/findings/f.md", "docs/plans/p.md",
                  "re/symbols.csv", "tools/golden.py", ".claude/skills/x.md", "README.md"):
            p = os.path.join(self.repo, f)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w").write("x\n")
        sh("git", "init", "-q", cwd=self.repo)
        sh("git", "add", "-A", cwd=self.repo)
        sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "t", cwd=self.repo)
        self.data = os.path.join(t, "data")
        os.makedirs(os.path.join(self.data, "global", "excel"))
        os.makedirs(os.path.join(self.data, "global", "tiles", "act1"))
        open(os.path.join(self.data, "global", "excel", "levels.txt"), "w").write("a\n")
        open(os.path.join(self.data, "global", "tiles", "act1", "a.ds1"), "w").write("d\n")
        open(os.path.join(self.data, "global", "tiles", "act1", "a.dt1"), "w").write("d\n")
        open(os.path.join(self.data, "global", "tiles", "act1", "a.dat"), "w").write("d\n")
        self.header = {"golden": "trace", "version": 1, "set": "t", "scope": "world,drops,drlg",
                       "game_exe_sha256": None, "tables_digest": "abc", "case_kinds": ["observed", "predicted"]}
        self.cases = [
            {"id": "w1", "kind": "predicted", "type": "world", "source": {"model": "m"}, "quirks": [],
             "inputs": {"seed": 5}, "expected": {"chain.A1.map_seed": 5, "chain.B2.level_seed.1": "00000001:00000002",
                                                  "monsters.pool.mlvl.1": 3}},
            {"id": "w2", "kind": "observed", "type": "world", "source": {"log": "l"}, "quirks": [],
             "inputs": {"seed": 6}, "expected": {"chain.A1.map_seed": 6}},
            {"id": "d1", "kind": "observed", "type": "drop", "source": {"log": "l"}, "quirks": [],
             "inputs": {"tc": "x"}, "expected": {"chain.G1.count": 2}},
            {"id": "r1", "kind": "observed", "type": "drlg", "source": {"log": "l"}, "quirks": [],
             "inputs": {"level": 3}, "expected": {"drlg.maze.room_count": 4}},
        ]
        self.set = os.path.join(t, "set.jsonl")
        golden.write_set(self.set, self.header, self.cases)
        cleanroom.ROOT = self.repo
        self.sb = os.path.join(t, "sb")

    def tearDown(self):
        self.td.cleanup()
        cleanroom.ROOT = os.path.dirname(HERE)

    def make(self, s, **kw):
        cleanroom.cmd_make(NS(slice=s, out=self.sb, set=self.set, game=self.data, force=kw.get("force", False)))


class Make(Base):
    def test_tree(self):
        self.make("S1")
        top = set(os.listdir(self.sb))
        self.assertTrue({"docs", "data", "cases.jsonl", "score.sh", "MANIFEST.json"} <= top)
        self.assertFalse({"re", "tools", ".claude"} & top)
        self.assertEqual(sorted(os.listdir(os.path.join(self.sb, "docs"))), ["formats", "glossary.md", "specs", "tables"])
        self.assertFalse(os.path.exists(os.path.join(self.sb, "docs", "formats", "golden")))
        self.assertTrue(os.path.exists(os.path.join(self.sb, "docs", "specs", "chain", "README.md")))
        names = [n.lower() for _dp, dn, fn in os.walk(self.sb) for n in dn + fn]
        self.assertNotIn("game.exe", names)
        self.assertNotIn("findings", names)
        self.assertFalse(os.path.exists(os.path.join(self.sb, "data", "global", "tiles")))
        self.assertTrue(os.path.exists(os.path.join(self.sb, "data", "global", "excel", "levels.txt")))

    def test_cases_inputs_only(self):
        self.make("S1")
        rows = [json.loads(x) for x in open(os.path.join(self.sb, "cases.jsonl"))]
        self.assertEqual([r["id"] for r in rows], ["w1", "w2"])
        for r in rows:
            self.assertEqual(set(r), {"id", "kind", "type", "inputs"})
        self.assertNotIn("expected", open(os.path.join(self.sb, "cases.jsonl")).read())

    def test_slices_cut(self):
        self.make("S3")
        self.assertEqual([json.loads(x)["id"] for x in open(os.path.join(self.sb, "cases.jsonl"))], ["w1"])
        self.make("S2", force=True)
        self.assertEqual([json.loads(x)["id"] for x in open(os.path.join(self.sb, "cases.jsonl"))], ["d1"])

    def test_s4_tiles_and_refuse_rebuild(self):
        self.make("S4")
        t = os.path.join(self.sb, "data", "global", "tiles", "act1")
        self.assertEqual(sorted(os.listdir(t)), ["a.ds1", "a.dt1"])
        with self.assertRaises(SystemExit):
            self.make("S4")

    def test_force_keeps_code(self):
        self.make("S1")
        open(os.path.join(self.sb, "mine.py"), "w").write("1\n")
        self.make("S1", force=True)
        self.assertTrue(os.path.exists(os.path.join(self.sb, "mine.py")))

    def test_own_empty_git_repo(self):
        # without a repository of its own, git run in the sandbox finds the project's (and its history) above it
        self.make("S1")
        top = subprocess.run(["git", "-C", self.sb, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        self.assertEqual(os.path.realpath(top.stdout.strip()), os.path.realpath(self.sb))
        r = subprocess.run(["git", "-C", self.sb, "log", "--oneline"], capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "")
        self.make("S1", force=True)           # a rebuild keeps it
        import shutil
        shutil.rmtree(os.path.join(self.sb, ".git"))
        with self.assertRaises(SystemExit):   # a sandbox under another repository is refused
            cleanroom.check_clean(self.sb)

    def test_symlink_refused(self):
        self.make("S1")
        os.symlink("/etc", os.path.join(self.sb, "docs", "specs", "link"))
        with self.assertRaises(SystemExit):
            cleanroom.check_clean(self.sb)

    def test_forbidden_detected(self):
        self.make("S1")
        os.makedirs(os.path.join(self.sb, "docs", "findings"))
        with self.assertRaises(SystemExit):
            cleanroom.check_clean(self.sb)


class Score(Base):
    def cand(self, rows, name="c.jsonl"):
        p = os.path.join(self.t, name)
        jl(p, rows)
        return p

    def score(self, s, cand):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cleanroom.cmd_score(NS(slice=s, candidate=cand, out=self.sb, set=self.set, limit=5))
        return rc, buf.getvalue()

    def test_pass_fail_and_log(self):
        self.make("S1")
        good = [{"id": "w1", "outputs": {"chain.A1.map_seed": 5, "chain.B2.level_seed.1": "00000001:00000002"}},
                {"id": "w2", "outputs": {"chain.A1.map_seed": 6}}]
        rc, out = self.score("S1", self.cand(good))
        self.assertEqual(rc, 0, out)
        self.assertIn("run 1 (first pass)", out)
        self.assertNotIn("monsters.pool", out)           # the pool field is not S1's
        bad = [dict(good[0], outputs={"chain.A1.map_seed": 9, "chain.B2.level_seed.1": "00000001:00000002"}), good[1]]
        rc, out = self.score("S1", self.cand(bad))
        self.assertEqual(rc, 1)
        self.assertIn("chain.A1.map_seed", out)
        self.assertIn("run 2", out)
        rc, out = self.score("S1", self.cand(good[:1]))
        self.assertEqual(rc, 1)
        self.assertIn("1 cases missing", out)
        log = [json.loads(x) for x in open(os.path.join(self.sb, "score-log.jsonl"))]
        self.assertEqual([r["run"] for r in log], [1, 2, 3])
        self.assertEqual(log[0]["fields_different"], 0)
        self.assertEqual(log[1]["fields_different"], 1)

    def test_other_slice_unaffected(self):
        self.make("S2")
        rc, out = self.score("S2", self.cand([{"id": "d1", "outputs": {"chain.G1.count": 2}}]))
        self.assertEqual(rc, 0, out)

    def test_malformed_not_logged(self):
        self.make("S1")
        p = os.path.join(self.t, "bad.jsonl")
        open(p, "w").write("{}\n")
        with self.assertRaises(SystemExit):
            self.score("S1", p)
        self.assertFalse(os.path.exists(os.path.join(self.sb, "score-log.jsonl")))


def tu(name, **inp):
    return {"type": "assistant", "cwd": "/w", "message": {"role": "assistant", "content": [
        {"type": "text", "text": "hi"}, {"type": "tool_use", "id": "x", "name": name, "input": inp}]}}


class ScoreSh(unittest.TestCase):
    def test_tool_path_is_main_checkout(self):
        with tempfile.TemporaryDirectory() as t:
            main = os.path.realpath(os.path.join(t, "main"))
            os.makedirs(main + "/tools")
            open(main + "/tools/cleanroom.py", "w").write("def cmd_score(): pass\n")
            sh("git", "init", "-q", main)
            sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", main, "add", "tools/cleanroom.py")
            sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", main, "commit", "-qm", "x")
            wt = os.path.join(t, "wt")
            sh("git", "-C", main, "worktree", "add", "-q", "-b", "lane/x", wt)
            old = cleanroom.HERE
            try:
                cleanroom.HERE = wt + "/tools"
                self.assertEqual(cleanroom.stable_tool_path(), main + "/tools/cleanroom.py")
                open(main + "/tools/cleanroom.py", "w").write("nothing\n")      # main lacks the score command: fall back
                self.assertEqual(cleanroom.stable_tool_path(), wt + "/tools/cleanroom.py")
            finally:
                cleanroom.HERE = old


class Audit(unittest.TestCase):
    SB = "/w/workspace/cleanroom/S1"

    def run_audit(self, rows, cwd=None, allow=(), bare=False):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "t.jsonl")
            if bare:
                rows = [c["message"]["content"][1] for c in rows]
            jl(p, rows)
            a, _bad = cleanroom.audit_file(p, [self.SB], list(allow), cwd or self.SB)
            return a

    def flagged(self, rows, **kw):
        return sorted({h[2].split(" ")[0] for h in self.run_audit(rows, **kw).hits})

    def test_clean(self):
        rows = [tu("Read", file_path=self.SB + "/docs/specs/rng.md"),
                tu("Bash", command="cd %s/data && ls global/excel | head; python3 -I code.py > out.txt" % self.SB),
                tu("Grep", pattern="Init", path=self.SB + "/docs"),
                tu("Glob", pattern="**/*.md", path=self.SB),
                tu("Write", file_path=self.SB + "/s1.py", content="x"),
                tu("Bash", command="python3 -I /w/tools/golden.py check set.jsonl cand.jsonl", cwd=None) | {"cwd": self.SB},
                tu("Bash", command="python3 /usr/lib/python3/x.py; cat /dev/null; echo a/b; sed -n 's/a/b/p' f", )
                | {"cwd": self.SB}]
        rows[5]["cwd"] = self.SB
        a = self.run_audit(rows)
        self.assertEqual(a.hits, [])
        self.assertEqual(a.n_calls, 7)

    def test_planted_reads(self):
        self.assertEqual(self.flagged([tu("Read", file_path="/w/docs/findings/chain/0001.md")]), ["/w/docs/findings/chain/0001.md"])
        self.assertEqual(self.flagged([tu("Bash", command="cat /w/re/symbols.csv | head")]), ["/w/re/symbols.csv"])
        self.assertEqual(self.flagged([tu("Bash", command="cd /w && ls")]), ["/w"])
        self.assertEqual(self.flagged([tu("Grep", pattern="x")], cwd="/w"), ["/w"])          # no path: the cwd
        self.assertEqual(self.flagged([tu("Glob", pattern="**/*.py", path="/w/tools")]), ["/w/tools"])
        self.assertEqual(self.flagged([tu("Glob", pattern="/w/tools/*.py", path=self.SB)]), ["/w/tools/*.py"])
        self.assertEqual(self.flagged([tu("Edit", file_path="/w/docs/specs/rng.md", old_string="a", new_string="b")]),
                         ["/w/docs/specs/rng.md"])           # the main tree's specs are not the sandbox's
        self.assertEqual(self.flagged([tu("Bash", command="grep -r Init docs/findings")], cwd="/w"), ["docs/findings"])
        self.assertEqual(self.flagged([tu("Bash", command="python3 -I /w/tools/golden.py emit --out x")]),
                         ["/w/tools/golden.py"])
        self.assertEqual(self.flagged([tu("Bash", command="cat /w/tools/golden.py")]), ["/w/tools/golden.py"])
        self.assertEqual(self.flagged([tu("Bash", command="python3 -c \"print(open('/w/workspace/golden-v1-full.jsonl').read())\"")]),
                         ["/w/workspace/golden-v1-full.jsonl"])
        self.assertEqual(self.flagged([tu("Bash", command="cat ../../../docs/findings/a.md")]), [
            "../../../docs/findings/a.md"])
        self.assertEqual(self.flagged([tu("Bash", command="ls Game.exe")], cwd="/w"), ["Game.exe"])

    def test_symlink_and_git_escapes(self):
        with tempfile.TemporaryDirectory() as td:
            sb = os.path.join(td, "sb")
            os.makedirs(sb)
            link = os.path.join(sb, "lnk")
            os.symlink("/w", link)
            tr = os.path.join(td, "t.jsonl")
            jl(tr, [tu("Read", file_path=link + "/docs/findings/x.md"), tu("Read", file_path=sb + "/ok.py")])
            a, _bad = cleanroom.audit_file(tr, [sb], [], sb)
            self.assertEqual([h[2] for h in a.hits], [link + "/docs/findings/x.md"])
        for cmd in ("git show HEAD:docs/findings/x.md", "git log -p HEAD~3:re/symbols.csv", "git cat-file -p main:tools/golden.py"):
            self.assertTrue(any(h[3] == "a path inside a git revision" for h in self.run_audit([tu("Bash", command=cmd)]).hits), cmd)
        self.assertEqual(self.run_audit([tu("Bash", command="git -C %s status" % self.SB)]).hits, [])

    def test_allow_and_sibling(self):
        self.assertEqual(self.flagged([tu("Read", file_path="/tmp/tr/out.txt")], allow=["/tmp/tr"]), [])
        self.assertEqual(self.flagged([tu("Read", file_path="/tmp/tr2/out.txt")], allow=["/tmp/tr"]), ["/tmp/tr2/out.txt"])
        self.assertEqual(self.flagged([tu("Read", file_path="/w/workspace/cleanroom/S10/x")]), ["/w/workspace/cleanroom/S10/x"])

    def test_bare_tool_use_shape(self):
        self.assertEqual(self.flagged([tu("Read", file_path="/w/docs/findings/x.md")], bare=True), ["/w/docs/findings/x.md"])
        self.assertEqual(self.flagged([tu("Read", file_path=self.SB + "/a")], bare=True), [])

    def test_heredoc_bodies_not_scanned(self):
        cmd = ("cd %s && python3 -I - <<'PY'\nimport os\nprint('/home/x/docs/findings and re/ tools/ .claude')\nPY\n"
               "cat >> ledger.md <<EOF\nsee docs/findings/x.md, /etc/passwd and re/symbols.csv\nEOF\nls docs/specs" % self.SB)
        self.assertEqual(self.flagged([tu("Bash", command=cmd)]), [])
        # the command part around a heredoc is still judged, before and after the body
        self.assertEqual(self.flagged([tu("Bash", command="cat re/x <<EOF\nbody\nEOF\n")]), ["re/x"])
        self.assertEqual(self.flagged([tu("Bash", command="cat <<EOF\nbody\nEOF\ncat docs/findings/y.md")]),
                         ["docs/findings/y.md"])
        # an unterminated heredoc swallows the rest, like the shell
        self.assertEqual(self.flagged([tu("Bash", command="cat <<EOF\ncat re/x")]), [])
        # a quoted literal is not a path
        self.assertEqual(self.flagged([tu("Bash", command="echo 'see docs/findings/x.md and re/y'")]), [])

    def test_harness_tool_results_read(self):
        home = os.path.expanduser("~")
        ok = home + "/.claude/projects/-p/abc-123/tool-results/b9k.txt"
        self.assertEqual(self.flagged([tu("Read", file_path=ok)]), [])
        self.assertEqual(self.flagged([tu("Read", file_path=home + "/.claude/projects/-p/abc-123/other/b9k.txt")]),
                         [home + "/.claude/projects/-p/abc-123/other/b9k.txt"])
        self.assertEqual(self.flagged([tu("Read", file_path=home + "/.claude/projects/-p/abc-123/tool-results/../x/f.txt")]),
                         [home + "/.claude/projects/-p/abc-123/tool-results/../x/f.txt"])
        self.assertEqual(self.flagged([tu("Read", file_path=home + "/.claude/settings.json")]), [home + "/.claude/settings.json"])

    def test_cli(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "t.jsonl")
            jl(p, [tu("Read", file_path="/w/docs/findings/x.md")])
            r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "cleanroom.py"), "audit", p, "--sandbox", self.SB],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("VIOLATION line 1 Read: /w/docs/findings/x.md", r.stdout)
            self.assertIn("VOID", r.stdout)
            jl(p, [{"type": "user", "message": {"content": "hello"}}])
            r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "cleanroom.py"), "audit", p, "--sandbox", self.SB],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            jl(p, [tu("Read", file_path=self.SB + "/a")])
            with open(p, "a") as fh:
                fh.write("not json\n")
            r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "cleanroom.py"), "audit", p, "--sandbox", self.SB],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertIn("1 unparsable", r.stdout)


if __name__ == "__main__":
    unittest.main()

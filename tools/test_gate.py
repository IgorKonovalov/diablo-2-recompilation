"""Self-test for tools/gate.py: python3 -I tools/test_gate.py
(or python3 -I -m unittest discover -s tools -p test_gate.py; `-m unittest tools/test_gate.py`
imports it as tools.test_gate, which needs the cwd on sys.path, and -I removes it).

FullTierTest runs the --full tier with a stub
survey in a scratch root, so it needs no workspace/.

tools/gate/fixtures/base/ is a small green repository. Each other fixture directory is an overlay
named after the rule it breaks: copied over base, it must raise that rule (an error naming the
file, the line and the rule, or a warning for W rules) and nothing else from the error list.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gate  # noqa: E402

FIX = os.path.join(HERE, "gate", "fixtures")
REPO = os.path.dirname(HERE)   # E9 keeps its parser cache under this checkout's workspace/

# rule -> (file, line) the fixture must report
EXPECT = {
    "E1": ("docs/specs/rng/core.md", 13),
    "E2": ("docs/formats/ds1.md", 5),
    "E3": ("docs/findings/rng/0001-core.md", 5),
    "E4": ("docs/findings/rng/0001-core.md", 7),
    "E5": ("docs/specs/rng/core.md", 15),
    "E6": ("docs/specs/rng/core.md", 4),
    "E7": ("re/symbols.csv", 3),
    "E8": ("docs/specs/rng/core.md", 18),
    "E9": ("docs/formats/diagram.md", 13),   # needs node and the Mermaid bundle, else skipped
    "E10": ("docs/wiki/randomness.md", 10),   # a confidence tag in a wiki page
    "E11": ("docs/wiki/saves.md", 1),         # no based_on front matter
    "E12": ("docs/wiki/randomness.md", 16),   # a `##` section with no link into docs/specs/
    "W1": ("docs/findings/rng/0001-core.md", 5),
    "W2": ("docs/specs/rng/core.md", 13),
    "W3": ("re/symbols.csv", 4),
    "W4": ("docs/wiki/randomness.md", 2),     # based_on date older than the spec's updated:
}

# overlay -> (rule, file, line), for overlays that test a second case of a rule
EXPECT_MORE = {
    "E3-dup": ("E3", "docs/formats/experiments.md", 7),   # id already defined in a findings experiments.md
    "E10-anchor": ("E10", "docs/wiki/randomness.md", 14),  # an fn: anchor and an address in a code span
    "E11-path": ("E11", "docs/wiki/saves.md", 2),          # based_on names a finding, not a spec
    "E11-status": ("E11", "docs/wiki/core.md", 2),         # based_on names a draft spec
}


def build(overlay=None):
    tmp = tempfile.mkdtemp(prefix="gate-")
    shutil.copytree(os.path.join(FIX, "base"), tmp, dirs_exist_ok=True)
    if overlay:
        shutil.copytree(os.path.join(FIX, overlay), tmp, dirs_exist_ok=True)
    return tmp


class GateTest(unittest.TestCase):
    def run_on(self, overlay=None):
        root = build(overlay)
        self.addCleanup(shutil.rmtree, root)
        return gate.run_gate(root, cache_root=REPO)

    def test_base_is_green_and_clean(self):
        rep = self.run_on()
        self.assertEqual(rep.errors, {})
        self.assertEqual(rep.warnings, {})
        for rule in ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E10", "E11", "E12", "W4"):
            self.assertGreater(rep.checked.get(rule, 0), 0, rule)

    def test_each_fixture_raises_its_rule(self):
        cases = [(rule, rule, path, line) for rule, (path, line) in EXPECT.items()]
        cases += [(ov, rule, path, line) for ov, (rule, path, line) in EXPECT_MORE.items()]
        for overlay, rule, path, line in cases:
            with self.subTest(overlay=overlay):
                rep = self.run_on(overlay)
                if rule == "E9" and rep.warnings.get("E9"):
                    self.skipTest(rep.warnings["E9"][0])
                bucket = rep.errors if rule.startswith("E") else rep.warnings
                msgs = bucket.get(rule, [])
                self.assertTrue(msgs, f"{rule} fixture raised no {rule}")
                self.assertTrue(any(m.startswith(f"{path}:{line}: {rule} ") for m in msgs), msgs)
                if rule.startswith("W"):
                    self.assertEqual(rep.errors, {}, "warning fixtures must stay green")
                else:
                    self.assertEqual(set(rep.errors), {rule}, rep.errors)

    def test_exit_codes(self):
        for overlay, code in ((None, 0), ("W1", 0), ("E1", 1)):
            with self.subTest(overlay=overlay):
                root = build(overlay)
                self.addCleanup(shutil.rmtree, root)
                with open(os.devnull, "w") as null:
                    old, sys.stdout = sys.stdout, null
                    try:
                        self.assertEqual(gate.main(["--root", root]), code)
                    finally:
                        sys.stdout = old

    def test_e9_skips_with_one_warning(self):
        root = build("E9")
        self.addCleanup(shutil.rmtree, root)
        old = os.environ.get("GATE_MERMAID_SRC")
        os.environ["GATE_MERMAID_SRC"] = os.path.join(root, "no-such-bundle")
        try:
            rep = gate.run_gate(root, cache_root=REPO)
        finally:
            if old is None:
                del os.environ["GATE_MERMAID_SRC"]
            else:
                os.environ["GATE_MERMAID_SRC"] = old
        self.assertEqual(rep.errors, {})
        self.assertEqual(len(rep.warnings.get("E9", [])), 1, rep.warnings)

    def test_e3_reads_formats_experiments(self):
        # base's finding cites run:2026-10-11-ds1-load, defined only in docs/formats/experiments.md
        rep = self.run_on()
        self.assertNotIn("E3", rep.errors)
        root = build()
        self.addCleanup(shutil.rmtree, root)
        os.remove(os.path.join(root, "docs/formats/experiments.md"))
        rep = gate.run_gate(root)
        self.assertEqual(set(rep.errors), {"E3"})
        self.assertIn("run:2026-10-11-ds1-load", rep.errors["E3"][0])

    def test_e1_needs_eight_hex_digits(self):
        root = build()
        self.addCleanup(shutil.rmtree, root)
        with open(os.path.join(root, "docs/findings/rng/0001-core.md"), "a", encoding="utf-8") as fh:
            fh.write("\n- [I] Short address. (data:g_pLevels@0x96C888)\n")
        rep = gate.run_gate(root)
        self.assertEqual(set(rep.errors), {"E1"})
        self.assertIn("8 hex digits", rep.errors["E1"][0])

    def test_backslash_in_code_span_is_not_an_escape(self):
        # base's finding has a Tag table row `DATA\GLOBAL\EXCEL\` that must not raise W2
        self.assertEqual(gate.table_cells(r"| `A\B\` x | [I] |"), [r"`A\B\` x", "[I]"])
        self.assertNotIn("W2", self.run_on().warnings)

    def test_table_names_case_insensitive(self):
        # base cites tbl:monstats.txt against docs/tables/MonStats.md
        rep = self.run_on()
        self.assertNotIn("E4", rep.errors)

    def test_github_slugs(self):
        cases = {
            "Open questions": "open-questions",
            "0001 — RNG core: `Seed` · step → range — notes §1": "0001--rng-core-seed--step--range--notes-1",
            "MPQ integrity: comparison with the 1.14b reference": "mpq-integrity-comparison-with-the-114b-reference",
            "run:2026-10-11-rng-emu": "run2026-10-11-rng-emu",
            "Phase 1 — Fast tier": "phase-1--fast-tier",
            "snake_case [link](x.md)": "snake_case-link",
            "`<T>` angle": "t-angle",
            "<a id=\"x\"></a>Plain": "plain",
        }
        for text, slug in cases.items():
            self.assertEqual(gate.gh_slug(text), slug)
        self.assertEqual(gate.heading_slugs("# A\n## A\n## A\n```\n# B\n```\n"), {"a", "a-1", "a-2"})


STUB = """import sys
print("histogram noise 1.5 x=y")
n = len(sys.argv) - 1
print("SURVEY stub files=%d errors=0 leftover_bytes=0" % n)
sys.exit(int(sys.argv[1].endswith("fail")) if n else 0)
"""


class StagedTest(unittest.TestCase):
    """--staged: the gate sees the git index plus --also paths, not the working tree."""

    def setUp(self):
        import subprocess
        self.sp = subprocess
        self.root = build()
        self.addCleanup(shutil.rmtree, self.root)
        g = ["git", "-C", self.root, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
        try:
            subprocess.run(g[:3] + ["init", "-q"], check=True, capture_output=True)
            subprocess.run(g[:3] + ["add", "."], check=True, capture_output=True)
            subprocess.run(g + ["commit", "-q", "-m", "base"], check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError) as e:
            self.skipTest(f"git unavailable: {e}")
        self.spec = os.path.join(self.root, "docs", "specs", "rng", "core.md")

    def code(self, *args):
        with open(os.devnull, "w") as null:
            old, sys.stdout = sys.stdout, null
            try:
                return gate.main(["--root", self.root] + list(args))
            finally:
                sys.stdout = old

    def test_unstaged_edit_is_not_seen(self):
        # (a): another writer's uncommitted broken link does not block this commit
        with open(self.spec, "a", encoding="utf-8") as fh:
            fh.write("\nSee [gone](nope.md).\n")
        self.assertEqual(self.code(), 1)
        self.assertEqual(self.code("--staged"), 0)
        self.assertEqual(self.code("--staged", "--also", "docs/specs/rng/core.md"), 1)

    def test_chained_add_of_a_new_doc(self):
        # (b): a link to a doc the same command line adds resolves through --also
        with open(os.path.join(self.root, "docs", "specs", "rng", "new.md"), "w", encoding="utf-8") as fh:
            fh.write("# New\n")
        self.sp.run(["git", "-C", self.root, "add", "docs/specs/rng/core.md"], check=True)
        with open(self.spec, "a", encoding="utf-8") as fh:
            fh.write("\nSee [new](new.md).\n")
        self.sp.run(["git", "-C", self.root, "add", "docs/specs/rng/core.md"], check=True)
        self.assertEqual(self.code("--staged"), 1)
        self.assertEqual(self.code("--staged", "--also", "docs/specs/rng/new.md"), 0)

    def test_flag_combinations(self):
        with open(os.devnull, "w") as null:
            old, sys.stderr = sys.stderr, null
            try:
                with self.assertRaises(SystemExit):
                    gate.main(["--root", self.root, "--also", "x.md"])
                with self.assertRaises(SystemExit):
                    gate.main(["--root", self.root, "--staged", "--full"])
            finally:
                sys.stderr = old


class FullTierTest(unittest.TestCase):
    """--full with a stub survey in a scratch root: no workspace/ data needed."""

    def make_root(self, workspace=True, baseline="SURVEY stub files=2 errors=0 leftover_bytes=0\n"):
        root = tempfile.mkdtemp(prefix="gate-full-")
        self.addCleanup(shutil.rmtree, root)
        os.makedirs(os.path.join(root, "tools", "gate", "baselines"))
        with open(os.path.join(root, "tools", "stub.py"), "w") as fh:
            fh.write(STUB)
        if baseline is not None:
            with open(os.path.join(root, "tools", "gate", "baselines", "stub.txt"), "w") as fh:
                fh.write(baseline)
        if workspace:
            os.makedirs(os.path.join(root, "workspace", "in"))
            for n in ("a.bin", "b.bin"):
                open(os.path.join(root, "workspace", "in", n), "w").close()
        return root

    REG = [gate.Survey("stub", ["tools/stub.py", "workspace/in/*.bin"])]

    def full(self, root, spec="default", require=False, reg=None):
        buf = io.StringIO()
        n = gate.run_full(root, spec, require, reg or self.REG, out=buf)
        return n, buf.getvalue()

    def test_baseline_reproduced(self):
        n, text = self.full(self.make_root())
        self.assertEqual(n, 0, text)
        self.assertIn("gate full tier: GREEN, 1 surveys, 0 errors", text)

    def test_changed_count_is_red_key_by_key(self):
        root = self.make_root(baseline="SURVEY stub files=3 errors=0 leftover_bytes=0\n")
        n, text = self.full(root)
        self.assertEqual(n, 1, text)
        self.assertIn("stub: files: baseline 3, survey 2 (-1)", text)
        self.assertIn("now: SURVEY stub files=2 errors=0 leftover_bytes=0", text)

    def test_missing_and_extra_keys(self):
        root = self.make_root(baseline="SURVEY stub files=2 errors=0 blocks=7\n")
        n, text = self.full(root)
        self.assertEqual(n, 2, text)
        self.assertIn("blocks: baseline 7, survey has no such key", text)
        self.assertIn("leftover_bytes: not in baseline, survey 0", text)

    def test_baseline_must_be_integers(self):
        for bad in ("SURVEY stub files=2 errors=0 leftover_bytes=0.5\n", "SURVEY stub files=x\n",
                    "SURVEY other files=2\n", "", "SURVEY stub files=2\nSURVEY stub files=2\n"):
            with self.subTest(baseline=bad):
                n, text = self.full(self.make_root(baseline=bad))
                self.assertGreaterEqual(n, 1, text)
                self.assertIn("tools/gate/baselines/stub.txt:", text)

    def test_missing_baseline(self):
        n, text = self.full(self.make_root(baseline=None))
        self.assertEqual(n, 1, text)
        self.assertIn("stub.txt: no baseline", text)

    def test_workspace_absent(self):
        root = self.make_root(workspace=False)
        n, text = self.full(root)
        self.assertEqual(n, 0)
        self.assertIn("SKIPPED: workspace absent", text)
        n, text = self.full(root, require=True)
        self.assertEqual(n, 1)
        green = build()  # the green base fixture has no workspace/
        self.addCleanup(shutil.rmtree, green)
        with open(os.devnull, "w") as null:
            old, sys.stdout = sys.stdout, null
            try:
                self.assertEqual(gate.main(["--root", green, "--full"]), 0)
                self.assertEqual(gate.main(["--root", green, "--full", "--require-workspace"]), 1)
            finally:
                sys.stdout = old

    def test_missing_input_is_red(self):
        reg = [gate.Survey("stub", ["tools/stub.py", "workspace/in/*.dat"])]
        n, text = self.full(self.make_root(), reg=reg)
        self.assertEqual(n, 1, text)
        self.assertIn("input missing under the root: workspace/in/*.dat", text)

    def test_survey_failure_and_missing_line(self):
        root = self.make_root()
        os.rename(os.path.join(root, "workspace", "in", "b.bin"), os.path.join(root, "workspace", "in", "fail"))
        reg = [gate.Survey("stub", ["tools/stub.py", "workspace/in/fail", "workspace/in/a.bin"])]
        n, text = self.full(root, reg=reg)
        self.assertIn("stub: survey exit 1", text)
        with open(os.path.join(root, "tools", "stub.py"), "w") as fh:
            fh.write("print('no summary')\n")
        n, text = self.full(root)
        self.assertEqual(n, 1, text)
        self.assertIn("last output line: not a `SURVEY stub", text)

    def test_opt_in_selection(self):
        reg = [gate.Survey("stub", ["tools/stub.py", "workspace/in/*.bin"]),
               gate.Survey("slow", ["tools/stub.py"], opt_in=True)]
        self.assertEqual([s.tool for s in gate.select_surveys("default", reg)], ["stub"])
        self.assertEqual([s.tool for s in gate.select_surveys("slow", reg)], ["slow"])
        self.assertEqual([s.tool for s in gate.select_surveys("all", reg)], ["stub", "slow"])
        with self.assertRaises(ValueError):
            gate.select_surveys("nope", reg)
        n, text = self.full(self.make_root(), reg=reg)
        self.assertEqual(n, 0, text)
        self.assertIn("opt-in, not run: slow", text)

    def test_registry_and_committed_baselines(self):
        tools = [s.tool for s in gate.SURVEYS]
        self.assertEqual(len(tools), len(set(tools)))
        for sv in gate.SURVEYS:
            self.assertTrue(os.path.isfile(os.path.join(HERE, "..", sv.argv[0])), sv.argv[0])
            path = os.path.join(HERE, "gate", "baselines", sv.tool + ".txt")
            with open(path, encoding="utf-8") as fh:
                lines = [ln for ln in fh.read().splitlines() if ln.strip()]
            self.assertEqual(len(lines), 1, path)
            gate.parse_survey_line(lines[0], sv.tool)  # integer counts only, or ValueError


if __name__ == "__main__":
    unittest.main()

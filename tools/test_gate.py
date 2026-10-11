"""Self-test for tools/gate.py: python3 -I tools/test_gate.py
(or python3 -I -m unittest discover -s tools -p test_gate.py; `-m unittest tools/test_gate.py`
imports it as tools.test_gate, which needs the cwd on sys.path, and -I removes it).

tools/gate/fixtures/base/ is a small green repository. Each other fixture directory is an overlay
named after the rule it breaks: copied over base, it must raise that rule (an error naming the
file, the line and the rule, or a warning for W rules) and nothing else from the error list.
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gate  # noqa: E402

FIX = os.path.join(HERE, "gate", "fixtures")

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
    "W1": ("docs/findings/rng/0001-core.md", 5),
    "W2": ("docs/specs/rng/core.md", 13),
    "W3": ("re/symbols.csv", 4),
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
        return gate.run_gate(root)

    def test_base_is_green_and_clean(self):
        rep = self.run_on()
        self.assertEqual(rep.errors, {})
        self.assertEqual(rep.warnings, {})
        for rule in ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"):
            self.assertGreater(rep.checked.get(rule, 0), 0, rule)

    def test_each_fixture_raises_its_rule(self):
        for rule, (path, line) in EXPECT.items():
            with self.subTest(rule=rule):
                rep = self.run_on(rule)
                bucket = rep.errors if rule.startswith("E") else rep.warnings
                msgs = bucket.get(rule, [])
                self.assertTrue(msgs, f"{rule} fixture raised no {rule}")
                self.assertTrue(any(m.startswith(f"{path}:{line}: {rule} ") for m in msgs), msgs)
                if rule.startswith("W"):
                    self.assertEqual(rep.errors, {}, "warning fixtures must stay green")

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
        }
        for text, slug in cases.items():
            self.assertEqual(gate.gh_slug(text), slug)
        self.assertEqual(gate.heading_slugs("# A\n## A\n## A\n```\n# B\n```\n"), {"a", "a-1", "a-2"})


if __name__ == "__main__":
    unittest.main()

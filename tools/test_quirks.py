"""Tests of tools/quirks.py's check Q4 and `list` (plan 0057 Phase 3). Run: python3 -I tools/test_quirks.py"""
import argparse
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quirks as Q  # noqa: E402

FINDING = """## Verdicts

| # | Claim | Source | Verdict | Tag | Anchor | Owning |
|---|---|---|---|---|---|---|
| 1 | a | s | confirmed: as read | [I] | 0x00400000 | none |
| 2 | b | s | contradicted by a spec | [C] | 0x00400000 | none |
| 3 | c | s | not in 1.14d, on these rows | [C] | 0x00400000 | none |
| 4 | d | s | not found: *Open questions* 1 | [L] | 0x00400000 | none |

## Leads used
"""

GOOD = """## Community claims

| Row | Verdict | Where |
|---|---|---|
| 1 | confirmed | Q1 |
| 2 | contradicted | [does not hold](#x) |
| 3 | not in 1.14d | [does not hold](#x) |
| 4 | not found | [open question 1](#y) |

### Community claims that do not hold

| Row | The claim | What the code does | Tag | Anchors | Statement |
|---|---|---|---|---|---|
| 2 | b | x | [C] | 0x00400000 | s |
| 3 | c | x | [C] | 0x00400000 | s |

## Evidence
"""

PAGE = """### 9. Deliberate oddities

| Id | Quirk | Tag | Anchors | Source |
|---|---|---|---|---|
| Q7 | a quirk | [I] | 0x00400000, fn:F@0x00400010 | [s](../combat/damage.md#a-b) n3 |
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        os.makedirs(os.path.join(self.root, "docs", "findings", "quirks"))
        os.makedirs(os.path.join(self.root, "docs", "specs", "quirks"))
        with open(os.path.join(self.root, Q.FINDING), "w", encoding="utf-8") as fh:
            fh.write(FINDING)


class Q4(Base):
    def errs(self, body, ids=("Q1",)):
        return Q.check_community(self.root, body, set(ids))

    def one(self, body, ids=("Q1",)):
        e = self.errs(body, ids)
        self.assertEqual(len(e), 1, e)
        return e[0]

    def test_good(self):
        self.assertEqual(self.errs(GOOD), [])

    def test_verdict_differs(self):
        self.assertIn("verdict", self.one(GOOD.replace("| 2 | contradicted |", "| 2 | not in 1.14d |")))

    def test_row_missing(self):
        self.assertIn("row 4 has no row", self.one(GOOD.replace("| 4 | not found | [open question 1](#y) |\n", "")))

    def test_row_not_in_finding(self):
        self.assertIn("not in the finding", self.one(GOOD.replace("| 1 | confirmed | Q1 |", "| 1 | confirmed | Q1 |\n| 9 | confirmed | Q1 |")))

    def test_confirmed_needs_an_entry(self):
        self.assertIn("confirmed needs", self.one(GOOD, ids=()))

    def test_contradicted_needs_the_table(self):
        self.assertIn("do-not-hold", self.one(GOOD.replace("| 2 | b | x | [C] | 0x00400000 | s |\n", "")))

    def test_not_found_needs_an_open_question(self):
        self.assertIn("not found needs", self.one(GOOD.replace("[open question 1](#y)", "Q1")))

    def test_held_row_not_compared(self):
        body = GOOD.replace("| 3 | c | x |", "| 8 | c | x |\n| 3 | c | x |")
        self.assertIn("do-not-hold row 8", self.one(body))


class List(Base):
    def test_list(self):
        with open(os.path.join(self.root, "docs", "specs", "quirks", "README.md"), "w", encoding="utf-8") as fh:
            fh.write(PAGE)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(Q.cmd_list(argparse.Namespace(root=self.root)), 0)
        rows = [json.loads(x) for x in out.getvalue().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["id"], rows[0]["class"], rows[0]["tag"]), ("Q7", 9, "I"))
        self.assertEqual(rows[0]["sources"], [{"spec": "combat/damage.md", "fragment": "a-b", "notes": [3]}])
        self.assertIn("0x00400000", rows[0]["anchors"])


if __name__ == "__main__":
    unittest.main()

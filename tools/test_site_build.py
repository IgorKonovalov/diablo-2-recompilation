"""Tests of the local site builder's widget handling (tools/site_build.py; backlog 2026-11-17, plan 0070 Phase 11).

Run: python3 -I tools/test_site_build.py

A page with a ```widget block is built into workspace/render/test-site/: with `fallback: text` the page holds the twin's
table, the caption and the note, and no script and no raw block keys; with `fallback: <illustration id>` it holds the
illustration's picture (the rng_anim.py illustration on the same page); a fallback that names no illustration is a
warning, not a crash. The check (the gate's E19) accepts these blocks and reports a block that does not parse, a widget
that does not exist, a fallback that is no illustration, a duplicated widget id and an illustrates link that does not
resolve; the repository's own docs/ pass it.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "workspace", "render", "test-site")
SB = os.path.join(HERE, "site_build.py")

WIDGET = """```widget
id: rng-stepper
widget: rng
illustrates: ../specs/rng/README.md#algorithm
caption: The generator to try by hand, with a seed and a range.
fallback: %s
```
"""
ILLUS = """```illustration
id: rng-seed-12345
tool: rng_anim.py
args: 12345 --count 3 --range 100
seed: illustrative
illustrates: ../specs/rng/README.md#algorithm
caption: Three draws on the seed 12345.
```
"""


def write(docs, rel, text):
    p = os.path.join(docs, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)


def tree(tmp, page_text):
    docs = os.path.join(tmp, "docs")
    write(docs, "specs/rng/README.md", "# RNG\n\n## Algorithm\n\ntext\n")
    write(docs, "wiki/page.md", "# Page\n\n" + page_text)
    return docs


def build(docs, *extra):
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    r = subprocess.run([sys.executable, "-I", SB, "--docs", docs, "--out", OUT] + list(extra), capture_output=True, text=True)
    return r


def page():
    with open(os.path.join(OUT, "wiki", "page.html"), encoding="utf-8") as fh:
        return fh.read()


def check(docs):
    r = subprocess.run([sys.executable, "-I", SB, "check", docs], capture_output=True, text=True)
    return r.returncode, r.stdout


class Widget(unittest.TestCase):
    def test_text_fallback_is_a_table_with_the_caption_and_no_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = build(tree(tmp, WIDGET % "text"), "--no-illustrations")
            self.assertEqual(r.returncode, 0, r.stderr[-400:])
            h = page()
            self.assertIn("<table>", h)
            self.assertIn("The generator to try by hand, with a seed and a range.", h)
            self.assertIn("no script", h)
            self.assertNotIn("<script", h.split("</style>")[-1])
            self.assertNotIn("lang-widget", h)
            self.assertNotIn("fallback: text", h)
            self.assertIn("12345", h)                                    # the twin's table starts from the fixture's seed

    def test_picture_fallback_names_the_illustration_gif(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = build(tree(tmp, ILLUS + "\n" + WIDGET % "rng-seed-12345"))
            self.assertEqual(r.returncode, 0, r.stderr[-400:])
            h = page()
            self.assertIn('<img class="illus" src="../illustrations/rng-seed-12345/', h)
            self.assertIn(".gif", h)
            self.assertIn("The generator to try by hand", h)
            self.assertNotIn("lang-widget", h)

    def test_unknown_fallback_and_broken_block_are_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = build(tree(tmp, WIDGET % "nowhere" + "\n```widget\nid: x\n```\n"), "--no-illustrations")
            self.assertEqual(r.returncode, 0, r.stderr[-400:])
            self.assertIn("WARNING wiki/page.md: widget rng-stepper: fallback illustration nowhere is not on a built page", r.stdout)
            self.assertIn("WARNING wiki/page.md: widget block: missing key", r.stdout)
            self.assertIn("Widget not shown", page())

    def test_check_accepts_and_rejects(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, out = check(tree(tmp, ILLUS + "\n" + WIDGET % "rng-seed-12345" + "\n" + WIDGET % "text"))
            self.assertIn("widget id 'rng-stepper' also at", out)        # the second one repeats the id
            self.assertEqual(rc, 1)
            rc, out = check(tree(tmp, ILLUS + "\n" + WIDGET % "rng-seed-12345"))
            self.assertEqual((rc, out.strip().splitlines()[-1]), (0, "CHECK illustrations: 2 blocks, 0 problems"))
            rc, out = check(tree(tmp, WIDGET % "nowhere"))
            self.assertIn("widget fallback 'nowhere' is not an illustration id", out)
            rc, out = check(tree(tmp, (WIDGET % "text").replace("widget: rng", "widget: nope")))
            self.assertIn("widget 'nope' is not in tools/widgets/", out)
            rc, out = check(tree(tmp, (WIDGET % "text").replace("#algorithm", "#nothing")))
            self.assertIn("no heading with that anchor", out)
            rc, out = check(tree(tmp, "```widget\nid: y\nwidget: rng\n```\n"))
            self.assertIn("missing key caption", out)

    def test_the_repository_docs_pass(self):
        rc, out = check(os.path.join(ROOT, "docs"))
        self.assertEqual(rc, 0, out[-400:])


if __name__ == "__main__":
    unittest.main()

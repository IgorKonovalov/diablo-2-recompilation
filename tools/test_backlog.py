"""Tests of tools/backlog.py (ADR-0018). Run: python3 -I tools/test_backlog.py"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backlog as B  # noqa: E402

PRE = """# Backlog — cross-lane requests and open questions

Format: `- [YYYY-MM-DD] from <lane> → <lane>: <request>. Context: <link>`

"""
STRUCK = ("- ~~[2026-10-11] from archivist → reverser: an old answered request about the MPQ order, with "
          "enough words to pass sixty characters.~~ Answered in [data/0002](findings/data/0002-mpq.md).\n")
BULLETLESS = ("~~[2026-10-15] from architect → reverser: a struck entry written without its list marker, kept as it "
              "is.~~ Done.\n")
OPEN_MULTI = ("- [2026-10-16] from reverser → spec-writer (Phase 3 of plan 0038, after the H4b review): corrections from\n"
              "  run:2026-10-16-sweep-monsters-b. (a) [monsters/special](specs/monsters/special.md#restore) restore;\n"
              "  (b) the anchor [here](#format) and [skill](../.claude/skills/reverser/SKILL.md).\n"
              "  - a nested item\n")
OPEN_ONE = ("- [2026-10-17] from architect → reverser, spec-writer: plan 0041 P1 review follow-ups (static, not blocking). "
            "Context: [plan 0041](plans/0041-stats.md#log)\n")


def silent():
    return contextlib.redirect_stdout(io.StringIO())


class Repo:
    def __init__(self, archive):
        self.root = tempfile.mkdtemp(prefix="backlog-")
        os.makedirs(os.path.join(self.root, "docs"))
        self.write_archive(archive)

    def write_archive(self, text):
        B.write(os.path.join(self.root, B.ARCHIVE), text)

    def archive(self):
        return B.read(os.path.join(self.root, B.ARCHIVE))

    def files(self):
        return B.entry_files(self.root)

    def entry(self, name):
        return B.parse_entry(B.read(os.path.join(self.root, B.DIR, name)))

    def migrate(self, today="2026-10-17"):
        return B.migrate(self.root, today, log=lambda *a: None)


class FrontMatterTest(unittest.TestCase):
    def test_roundtrip(self):
        f = {"from": "reverser", "to": ["spec-writer", "archivist"], "date": "2026-10-17", "status": "done",
             "context": ["../plans/0039-x.md#log"], "resolution": "Done in [x](../specs/x.md): \"quoted\""}
        text = B.render_entry(f, "The request.")
        g, body, errs = B.parse_entry(text)
        self.assertEqual(errs, [])
        self.assertEqual(g, f)
        self.assertEqual(body.strip(), "The request.")
        self.assertEqual(B.check_entry("2026-10-17-reverser-spec-writer+archivist-x.md", g, errs), [])

    def test_check_entry_errors(self):
        base = {"from": "reverser", "to": ["spec-writer"], "date": "2026-10-17", "status": "open",
                "context": [], "resolution": ""}
        name = "2026-10-17-reverser-spec-writer-x.md"
        self.assertEqual(B.check_entry(name, base, []), [])
        cases = [({"from": "wizard"}, "not a lane"), ({"to": ["spec-writer", "nobody"]}, "not a lane"),
                 ({"status": "closed"}, "not one of"), ({"status": "done"}, "without a `resolution:`"),
                 ({"resolution": "x"}, "status open with a resolution"), ({"date": "2026-10-16"}, "does not match"),
                 ({"from": ""}, "missing")]
        for change, msg in cases:
            with self.subTest(change=change):
                errs = B.check_entry(name, dict(base, **change), [])
                self.assertTrue(any(msg in m for _, m in errs), errs)
        self.assertTrue(B.check_entry("notes.md", base, []))

    def test_parse_errors(self):
        self.assertTrue(B.parse_entry("no front matter")[2])
        self.assertTrue(B.parse_entry("---\nfrom: a\n")[2])
        _, _, errs = B.parse_entry("---\nfrom: reverser\nowner: x\nbad line\nresolution: \"unclosed\n---\n")
        self.assertEqual(len(errs), 3, errs)


class ArchiveTest(unittest.TestCase):
    def test_blocks(self):
        pre, blocks = B.parse_archive(PRE + STRUCK + "\n" + OPEN_MULTI + BULLETLESS)
        entries = [b for b in blocks if b.kind == "entry"]
        self.assertEqual(len(pre), 4)
        self.assertEqual([len(b.lines) for b in entries], [1, 4, 1])
        self.assertEqual([b.struck() for b in entries], [True, False, True])
        req, res = B.split_struck(B.entry_body(entries[0]))
        self.assertTrue(req.startswith("[2026-10-11]"))
        self.assertTrue(res.startswith("Answered"))

    def test_lanes_of(self):
        self.assertEqual(B.lanes_of("architect (+human)"), ["architect", "human"])
        self.assertEqual(B.lanes_of("reverser (harness, 1 slot)"), ["reverser"])
        self.assertEqual(B.lanes_of("reverser (plan 0030 Phase 2), spec-writer"), ["reverser", "spec-writer"])
        self.assertEqual(B.lanes_of("human (owner)"), ["human"])

    def test_rebase_links(self):
        self.assertEqual(B.rebase_links("[a](findings/x.md#y) [b](#z) [c](https://e.org/a) [d](../tools/t.py)"),
                         "[a](../findings/x.md#y) [b](../backlog.md#z) [c](https://e.org/a) [d](../../tools/t.py)")


class MigrateTest(unittest.TestCase):
    def setUp(self):
        self.r = Repo(PRE + STRUCK + "\n" + OPEN_MULTI + BULLETLESS + OPEN_ONE)
        self.addCleanup(shutil.rmtree, self.r.root)

    def test_moves_open_entries_and_leaves_pointers(self):
        c = self.r.migrate()
        self.assertEqual((c["moved"], c["closed"], c["pointers"]), (2, 0, 2))
        names = self.r.files()
        self.assertEqual(len(names), 2)
        multi = next(n for n in names if n.startswith("2026-10-16-reverser-spec-writer-"))
        f, body, errs = self.r.entry(multi)
        self.assertEqual(errs, [])
        self.assertEqual(B.check_entry(multi, f, errs), [])
        self.assertEqual((f["from"], f["to"], f["status"]), ("reverser", ["spec-writer"], "open"))
        self.assertIn("](../specs/monsters/special.md#restore)", body)
        self.assertIn("](../backlog.md#format)", body)
        self.assertIn("](../../.claude/skills/reverser/SKILL.md)", body)
        self.assertIn("\n- a nested item", body)
        one = next(n for n in names if n.startswith("2026-10-17-architect-reverser+spec-writer-"))
        f1, _, _ = self.r.entry(one)
        self.assertEqual(f1["to"], ["reverser", "spec-writer"])
        self.assertEqual(f1["context"], ["../plans/0041-stats.md#log"])
        arch = self.r.archive()
        self.assertIn(STRUCK, arch)
        self.assertIn(BULLETLESS, arch)
        self.assertNotIn("- [20", arch)
        self.assertIn(f"~~ Moved to [{multi}](backlog/{multi}).", arch)
        self.assertIn("- ~~[2026-10-16] from reverser → spec-writer (Phase 3 of plan 0038, after the H4b review): "
                      "corrections from", arch)

    def test_idempotent(self):
        self.r.migrate()
        arch, files = self.r.archive(), {n: self.r.entry(n) for n in self.r.files()}
        c = self.r.migrate()
        self.assertEqual((c["moved"], c["closed"], c["annotated"], c["deduped"], c["files_written"]), (0, 0, 0, 0, 0))
        self.assertEqual(self.r.archive(), arch)
        self.assertEqual({n: self.r.entry(n) for n in self.r.files()}, files)

    def test_later_merge_appends_an_entry(self):
        self.r.migrate()
        new = "- [2026-10-18] from spec-writer → architect: review the combat wiki page on `lane/wiki6`, please.\n"
        self.r.write_archive(self.r.archive() + new)
        c = self.r.migrate("2026-10-18")
        self.assertEqual((c["moved"], c["pointers"]), (1, 3))
        self.assertEqual(len(self.r.files()), 3)
        self.assertNotIn(new, self.r.archive())

    def _replace_pointer(self, name, replacement, keep_pointer=False):
        lines = self.r.archive().split("\n")
        i = next(i for i, ln in enumerate(lines) if f"(backlog/{name})" in ln)
        lines[i:i + 1] = ([lines[i]] if keep_pointer else []) + replacement.rstrip("\n").split("\n")
        self.r.write_archive("\n".join(lines))

    def test_struck_in_archive_after_migration(self):
        self.r.migrate()
        multi = next(n for n in self.r.files() if n.startswith("2026-10-16-"))
        struck = OPEN_MULTI.replace("- [2026", "- ~~[2026", 1).rstrip("\n") + "~~ Done in [special](specs/monsters/special.md).\n"
        for keep in (False, True):   # the merge took the lane's side, or kept both sides
            with self.subTest(keep_pointer=keep):
                f, body, _ = self.r.entry(multi)
                B.write(os.path.join(self.r.root, B.DIR, multi), B.render_entry(dict(f, status="open", resolution=""), body))
                self._replace_pointer(multi, struck, keep_pointer=keep)
                c = self.r.migrate()
                self.assertEqual((c["moved"], c["closed"], c["deduped"]), (0, 1, 1 if keep else 0))
                f, body2, errs = self.r.entry(multi)
                self.assertEqual(f["status"], "done")
                self.assertEqual(f["resolution"], "Done in [special](../specs/monsters/special.md).")
                self.assertEqual(B.check_entry(multi, f, errs), [])
                self.assertEqual(body2, body)
                arch = self.r.archive()
                self.assertEqual(arch.count(f"(backlog/{multi})"), 1)
                self.assertNotIn("corrections from\n  run:", arch)
                self.assertEqual(len(self.r.files()), 2)

    def test_annotated_copy_is_not_duplicated(self):
        self.r.migrate()
        one = next(n for n in self.r.files() if n.startswith("2026-10-17-"))
        self._replace_pointer(one, OPEN_ONE.rstrip("\n") + " **Update:** narrowed to (a) by [P2](plans/0041-stats.md#log).")
        c = self.r.migrate("2026-10-18")
        self.assertEqual((c["moved"], c["annotated"], c["closed"]), (0, 1, 0))
        self.assertEqual(len(self.r.files()), 2)
        _, body, _ = self.r.entry(one)
        self.assertIn("*Annotation (archive copy, migrated 2026-10-18):* **Update:** narrowed to (a) by "
                      "[P2](../plans/0041-stats.md#log).", body)
        self.assertEqual(self.r.migrate("2026-10-18")["files_written"], 0)

    def test_closed_file_is_not_reopened(self):
        self.r.migrate()
        one = next(n for n in self.r.files() if n.startswith("2026-10-17-"))
        with silent():
            B.main(["--root", self.r.root, "close", f"docs/backlog/{one}", "--resolution", "Done in P2."])
        self._replace_pointer(one, OPEN_ONE, keep_pointer=True)
        c = self.r.migrate()
        self.assertEqual((c["moved"], c["deduped"]), (0, 1))
        f, _, _ = self.r.entry(one)
        self.assertEqual((f["status"], f["resolution"]), ("done", "Done in P2."))


class CommandTest(unittest.TestCase):
    def setUp(self):
        self.r = Repo(PRE)
        self.addCleanup(shutil.rmtree, self.r.root)

    def run_cmd(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = B.main(["--root", self.r.root, "--today", "2026-10-17", *argv])
        return code, out.getvalue()

    def test_new_list_close(self):
        code, out = self.run_cmd("new", "--from", "reverser", "--to", "spec-writer,archivist",
                                 "--text", "Fold the P1c answers into the table docs.", "--context", "../plans/x.md")
        self.assertEqual(code, 0)
        path = out.strip()
        self.assertEqual(path, "docs/backlog/2026-10-17-reverser-spec-writer+archivist-fold-the-p1c-answers-into-the-table-docs.md")
        f, body, errs = B.parse_entry(B.read(os.path.join(self.r.root, path)))
        self.assertEqual(B.check_entry(os.path.basename(path), f, errs), [])
        self.assertEqual(f["context"], ["../plans/x.md"])
        self.run_cmd("new", "--from", "architect", "--to", "reverser", "--slug", "review follow-ups")
        self.assertEqual(len(self.run_cmd("list")[1].splitlines()), 2)
        self.assertEqual(len(self.run_cmd("list", "--to", "archivist")[1].splitlines()), 1)
        self.assertEqual(len(self.run_cmd("list", "--from", "architect")[1].splitlines()), 1)
        self.assertEqual(self.run_cmd("close", path, "--resolution", "Done in [x](../tables/x.md).")[0], 0)
        self.assertEqual(len(self.run_cmd("list")[1].splitlines()), 1)
        self.assertEqual(len(self.run_cmd("list", "--status", "done")[1].splitlines()), 1)
        self.assertEqual(len(self.run_cmd("list", "--status", "all")[1].splitlines()), 2)

    def test_new_rejects_unknown_lane(self):
        self.assertEqual(self.run_cmd("new", "--from", "reverser", "--to", "wizard", "--text", "x")[0], 2)
        self.assertEqual(self.r.files(), [])


if __name__ == "__main__":
    unittest.main()

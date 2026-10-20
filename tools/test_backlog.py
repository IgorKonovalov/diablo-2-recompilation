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

    def archived(self):
        return B.archived_files(self.root)

    def entry(self, name):
        return B.parse_entry(B.read(B.entry_path(self.root, name)))

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
        i = next(i for i, ln in enumerate(lines) if f"(backlog/{name})" in ln or f"(backlog/archive/{name})" in ln)
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
        self.assertEqual(self.r.archived(), [one])
        self.assertIn(f"(backlog/archive/{one})", self.r.archive())   # the pointer follows the file


class ArchiveSweepTest(unittest.TestCase):
    """ADR-0019: closed entries live in docs/backlog/archive/."""

    def setUp(self):
        self.r = Repo(PRE + OPEN_MULTI + OPEN_ONE)
        self.addCleanup(shutil.rmtree, self.r.root)
        self.r.migrate()
        self.multi = next(n for n in self.r.files() if n.startswith("2026-10-16-"))
        self.one = next(n for n in self.r.files() if n.startswith("2026-10-17-"))
        root = self.r.root
        B.write(os.path.join(root, "docs/plans/0041-stats.md"),
                f"# Plan\n\nSee [the entry](../backlog/{self.one}#x) and [other](../backlog/{self.multi}).\n")
        B.write(os.path.join(root, ".claude/skills/a/SKILL.md"), f"[e](../../../docs/backlog/{self.one})\n")
        # the multi entry links the other entry and gets an extra context item pointing at it
        f, body = B.load_entries(root)[self.multi]
        f = dict(f, context=list(f["context"]) + [self.one])
        B.write(B.entry_path(root, self.multi), B.render_entry(f, body + f"\nSee [one]({self.one})."))

    def close_in_place(self, name, resolution="Done in [plan](../plans/0041-stats.md)."):
        """What a lane on an older branch does: status set, the file left in docs/backlog/."""
        f, body = B.load_entries(self.r.root)[name]
        B.write(B.entry_path(self.r.root, name), B.render_entry(dict(f, status="done", resolution=resolution), body))

    def sweep(self, **kw):
        return B.archive(self.r.root, log=lambda *a: None, **kw)

    def test_sweep_moves_closed_and_rewrites_links(self):
        self.close_in_place(self.one)
        c = self.sweep()
        self.assertEqual((c["archived"], c["unarchived"]), (1, 0))
        self.assertEqual(self.r.files(), [self.multi])
        self.assertEqual(self.r.archived(), [self.one])

        root = self.r.root
        plan = B.read(os.path.join(root, "docs/plans/0041-stats.md"))
        self.assertIn(f"](../backlog/archive/{self.one}#x)", plan)
        self.assertIn(f"](../backlog/{self.multi})", plan)
        self.assertIn(f"](../../../docs/backlog/archive/{self.one})", B.read(os.path.join(root, ".claude/skills/a/SKILL.md")))
        self.assertIn(f"(backlog/archive/{self.one})", self.r.archive())
        f, body, errs = self.r.entry(self.one)
        self.assertEqual(errs, [])
        self.assertEqual(f["resolution"], "Done in [plan](../../plans/0041-stats.md).")
        self.assertEqual(f["context"], ["../../plans/0041-stats.md#log"])
        fm, bm, _ = self.r.entry(self.multi)
        self.assertEqual(fm["context"][-1], f"archive/{self.one}")
        self.assertIn(f"See [one](archive/{self.one}).", bm)
        self.assertIn("](../specs/monsters/special.md#restore)", bm)       # untouched
        # idempotent
        before = {n: self.r.entry(n) for n in self.r.files() + self.r.archived()}
        self.assertEqual(self.sweep(), dict(archived=0, unarchived=0, links_files=0))
        self.assertEqual({n: self.r.entry(n) for n in self.r.files() + self.r.archived()}, before)
        # close prints the entry's new path, then the other files whose links it rewrote
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            B.main(["--root", self.r.root, "close", f"docs/backlog/{self.multi}", "--resolution", "Done."])
        lines = out.getvalue().split()
        self.assertEqual(lines[0], f"docs/backlog/archive/{self.multi}")
        self.assertIn("docs/plans/0041-stats.md", lines)
        self.assertIn("docs/backlog.md", lines)

    def test_archived_entry_links_back_and_reopen(self):
        self.close_in_place(self.one)
        self.close_in_place(self.multi)
        self.sweep()
        _, bm, _ = self.r.entry(self.multi)
        self.assertIn(f"See [one]({self.one}).", bm)                      # siblings in archive/
        self.assertIn("](../../specs/monsters/special.md#restore)", bm)
        # reopened by hand: the sweep moves it back out
        f, body = B.load_entries(self.r.root)[self.one]
        B.write(B.entry_path(self.r.root, self.one), B.render_entry(dict(f, status="open", resolution=""), body))
        self.assertEqual(self.sweep()["unarchived"], 1)
        self.assertEqual(self.r.files(), [self.one])
        f, _, _ = self.r.entry(self.one)
        self.assertEqual(f["context"], ["../plans/0041-stats.md#log"])
        _, bm, _ = self.r.entry(self.multi)
        self.assertIn(f"See [one](../{self.one}).", bm)

    def test_heals_an_annotation_written_from_the_old_place(self):
        self.close_in_place(self.one)
        self.sweep()
        path = B.entry_path(self.r.root, self.one)
        B.write(path, B.read(path) + "\n*2026-10-20 (reverser):* see [plan](../plans/0041-stats.md).\n")
        self.assertEqual(self.sweep()["links_files"], 1)
        self.assertIn("see [plan](../../plans/0041-stats.md).", B.read(path))

    def test_list_and_migrate_see_archived_entries(self):
        self.close_in_place(self.one)
        self.sweep()
        self.assertIn(self.one, B.load_entries(self.r.root))
        c = self.r.migrate()
        self.assertEqual((c["moved"], c["files_written"]), (0, 0))
        self.assertEqual(B.unique_path(self.r.root, self.one), self.one[:-3] + "-2.md")

    def test_dry_run_changes_nothing(self):
        self.close_in_place(self.one)
        plan = B.read(os.path.join(self.r.root, "docs/plans/0041-stats.md"))
        c = self.sweep(dry_run=True)
        self.assertEqual(c["archived"], 1)
        self.assertGreater(c["links_files"], 0)
        self.assertEqual(self.r.archived(), [])
        self.assertEqual(B.read(os.path.join(self.r.root, "docs/plans/0041-stats.md")), plan)


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
        code, out = self.run_cmd("close", path, "--resolution", "Done in [x](../tables/x.md).")
        self.assertEqual(code, 0)
        self.assertEqual(out.split("\n")[0], path.replace("docs/backlog/", "docs/backlog/archive/"))
        f, _, _ = B.parse_entry(B.read(os.path.join(self.r.root, out.split("\n")[0])))
        self.assertEqual((f["resolution"], f["context"]), ("Done in [x](../../tables/x.md).", ["../../plans/x.md"]))
        self.assertFalse(os.path.exists(os.path.join(self.r.root, path)))
        self.assertEqual(len(self.run_cmd("list")[1].splitlines()), 1)
        self.assertEqual(len(self.run_cmd("list", "--status", "done")[1].splitlines()), 1)
        self.assertEqual(len(self.run_cmd("list", "--status", "all")[1].splitlines()), 2)

    def test_archive_command_runs_migrate_first(self):
        self.r.write_archive(PRE + OPEN_ONE)
        code, out = self.run_cmd("archive")
        self.assertEqual(code, 0)
        self.assertIn("migrate: moved 1", out)
        self.assertIn("archive: archived 0", out)
        self.assertEqual(len(self.r.files()), 1)

    def test_new_rejects_unknown_lane(self):
        self.assertEqual(self.run_cmd("new", "--from", "reverser", "--to", "wizard", "--text", "x")[0], 2)
        self.assertEqual(self.r.files(), [])


if __name__ == "__main__":
    unittest.main()

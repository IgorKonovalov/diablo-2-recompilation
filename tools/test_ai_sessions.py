"""No-game tests of tools/ai_sessions.py (plan 0052 Phase 2, lane/p52d): python3 -I tools/test_ai_sessions.py.

A pinned map seed is kept on a rerun, a `players` argument reaches the pilot's farm command, the Countess case's
descents are skipped by level, and tools/gdb/ai-skills.gdb loads the AI and the skills loggers once each and writes
nothing. Nothing is launched.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai_sessions as S  # noqa: E402


class PinnedSeed(unittest.TestCase):
    def test_unpinned_moves_with_the_launch_number(self):
        self.assertEqual(S.launch_seed("a1-jail", 5201, 0), 5201)
        self.assertEqual(S.launch_seed("a1-jail", 5201, 3), 5204)

    def test_pinned_case_keeps_its_seed_on_every_launch(self):
        for launches in (0, 1, 2, 7):             # the first try, a rerun after a failed launch, later launches
            self.assertEqual(S.launch_seed("d-duriel", 5201, launches), 3364)
            self.assertEqual(S.launch_seed("fresh:d-duriel", 5201, launches), 3364)

    def test_pinned_cases_are_cases(self):
        for name in S.PINNED:
            self.assertIn(name, S.CASES)

    def test_a_rerun_of_a_pinned_case_in_a_batch(self):
        # the batch's launch counter moves by one per launch: replay it the way run() does for [d-duriel (fails),
        # d-duriel again] after one other launch, with a seed0 that is not the pin
        seeds, launches = [], 1
        for case in ("fresh:d-duriel", "fresh:d-duriel"):
            seeds.append(S.launch_seed(case, 3364 - 1, launches))
            launches += 1
        self.assertEqual(seeds, [3364, 3364])
        self.assertNotEqual(3364 - 1 + 2, 3364)   # the old rule gave 3363 + 2 = 3365 on the rerun

    def test_custom_pin_table(self):
        self.assertEqual(S.launch_seed("x", 10, 4, {"x": 99}), 99)
        self.assertEqual(S.launch_seed("y", 10, 4, {"x": 99}), 14)


class Cases(unittest.TestCase):
    def test_stage_players(self):
        args = S.stage("3,4", 240, players=8)[0][0]
        self.assertEqual(args[args.index("--players") + 1], "8")
        self.assertNotIn("--players", S.stage("3,4")[0][0])
        self.assertEqual(S.stage("3,4")[0][1], 280)

    def test_fetish_p8_case(self):
        diff, steps, what, save = S.case_of("a3-flayer-p8")
        self.assertEqual(diff, "normal")
        self.assertIn("--players", steps[0][0])
        self.assertIn("--wp", steps[0][0])

    def test_countess_route(self):
        diff, steps, what, save = S.case_of("a1-countess")
        self.assertEqual(save, S.CHAR)
        rows = [s[0][s[0].index("--descend") + 1] for s in steps if "--descend" in s[0]]
        self.assertEqual(rows, ["10", "12", "9", "9", "9", "9"])     # levels 20, 21, 22, 23, 24, 25
        self.assertIn("1,5", steps[0][0])
        last = steps[-1][0]
        self.assertEqual(last[0], "hunt")
        self.assertEqual(last[last.index("--mon-cls") + 1], "45")
        self.assertEqual(last[len(last) - 1 - last[::-1].index("--radius") + 1], "1")   # the last --radius wins: held alive
        # every descent has a skip set ending at level 25; the hunt has none
        for s in steps[:-1]:
            self.assertEqual(max(s[2]), 25)
        self.assertEqual(len(steps[-1]), 2)

    def test_skipped(self):
        self.assertTrue(S.skipped(37, 37))
        self.assertFalse(S.skipped(36, 37))
        self.assertTrue(S.skipped(24, (24, 25)))
        self.assertFalse(S.skipped(23, (24, 25)))
        self.assertFalse(S.skipped(None, (24, 25)))
        self.assertFalse(S.skipped(24, None))


class GdbScript(unittest.TestCase):
    def test_ai_skills_gdb(self):
        with open(os.path.join(HERE, "gdb", "ai-skills.gdb")) as fh:
            text = fh.read()
        src = [ln.split()[1] for ln in text.splitlines() if ln.startswith("source ")]
        self.assertEqual(src, ["tools/gdb/pilot.py", "tools/gdb/ai.py", "tools/gdb/skills.py"])
        self.assertTrue(text.rstrip().endswith("continue"))
        for f in src:
            self.assertTrue(os.path.exists(os.path.join(HERE, "..", f)))

    def test_default_gdb_unchanged(self):
        self.assertEqual(S.GDB, "tools/gdb/ai-g4.gdb")

    def test_no_global_name_shared(self):
        import ast
        names = []
        for f in ("pilot.py", "ai.py", "skills.py"):
            with open(os.path.join(HERE, "gdb", f)) as fh:
                t = ast.parse(fh.read())
            n = set()
            for node in t.body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    n.add(node.name)
                elif isinstance(node, ast.Assign):
                    n |= {x.id for x in node.targets if isinstance(x, ast.Name)}
            names.append(n)
        self.assertFalse(names[0] & names[1] or names[0] & names[2] or names[1] & names[2])


if __name__ == "__main__":
    unittest.main()

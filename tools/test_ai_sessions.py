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

    def test_run_takes_its_seed_from_launch_seed(self):
        # lane/p52d review: the tests above hold with run() still at seed0 + launches
        src = open(os.path.join(HERE, "ai_sessions.py")).read()
        body = src[src.index("    def launch(case, diff, save):"):]
        self.assertIn("seed = launch_seed(case, seed0, pr.launches)", body[:300])
        self.assertNotIn("seed = seed0 + pr.launches", src)

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


class Tour(unittest.TestCase):
    """plan 0069 Phase 1a: the t-* and nm-* cases of tools/ai_tour.py's TOUR."""

    def setUp(self):
        import ai_tour
        self.T = ai_tour

    def test_every_tour_case_is_a_case_and_pinned(self):
        for name, t in self.T.TOUR.items():
            self.assertIn(name, S.CASES)
            seed = self.T.seed_of(t["group"])
            self.assertIsInstance(seed, int)
            self.assertEqual(S.launch_seed(name, 5201, 3), seed)
            self.assertEqual(S.launch_seed("fresh:" + name, 5201, 0), seed)
            self.assertEqual(S.case_of(name)[0], t.get("diff", "normal"))

    def test_nightmare_cases(self):
        self.assertEqual(S.case_of("nm-a5-wsk")[0], "nightmare")
        self.assertEqual(S.case_of("t-a5-wsk")[0], "normal")
        self.assertTrue(all(n.startswith("nm-") == (S.case_of(n)[0] == "nightmare") for n in self.T.TOUR))

    def test_descent_skip_sets(self):
        steps = S.case_of("t-a2-oasis")[1]
        d = [s for s in steps if s[0][0] == "farm" and "--descend" in s[0]]
        self.assertEqual([s[0][s[0].index("--descend-to") + 1] for s in d], ["62", "63", "64"])
        self.assertEqual([s[2] for s in d], [(62, 63, 64), (63, 64), (64,)])
        self.assertEqual([s[0][s[0].index("--descend") + 1] for s in d], ["47", "49", "49"])

    def test_hunt_holds_the_target(self):
        last = S.case_of("t-a3-durance")[1][-1][0]
        self.assertEqual(last[:3], ["hunt", "--mon-cls", "242"])
        self.assertEqual(last[len(last) - 1 - last[::-1].index("--radius") + 1], "1")

    def test_border_and_town_steps(self):
        steps = S.case_of("t-a1-town")[1]
        self.assertEqual(steps[0], ("wp", "1", "1"))
        self.assertIn("--any-level", steps[1][0])
        self.assertNotIn("--nova-key", S.case_of("t-a2-town")[1][1][0])     # no Nova in a town walk
        self.assertIn("--walk", S.case_of("t-a2-town")[1][1][0])

    def test_stay_case_gate(self):
        self.assertEqual(S.STAY, {"t-a4-town"})
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as fh:
            fh.write('PLR {"lid":103,"x":1,"y":2}\n')
        try:
            self.assertEqual(S.stayed(fh.name, 103), (True, ""))
            self.assertFalse(S.stayed(fh.name, 1)[0])
            self.assertFalse(S.left_start(fh.name, 103)[0])          # the ordinary gate would refuse it
        finally:
            os.unlink(fh.name)

    def test_reruns_keep_the_kept_case_steps_seed_and_save(self):
        for name, kept, seed in (("t-h1h-a1-stony", "a1-stony", 5803), ("t-h1h-a3-flayer-p8", "a3-flayer-p8", 5602),
                                 ("t-h1h-s-barb-flayer", "s-barb-flayer", 5401),
                                 ("t-h1h-s-necro-curse", "s-necro-curse", 5802)):
            self.assertEqual(S.case_of(name)[1], S.case_of(kept)[1])
            self.assertEqual(S.case_of(name)[3], S.case_of(kept)[3])
            self.assertEqual(S.PINNED[name], seed)

    def test_loot_step(self):
        steps = S.case_of("t-a5-crystal")[1]
        self.assertTrue(any("--loot" in s[0] for s in steps if isinstance(s[0], list)))


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

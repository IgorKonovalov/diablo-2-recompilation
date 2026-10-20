"""Synthetic tests for tools/chain.py (plan 0048 Phase 1): python3 -I tools/test_chain.py

No game file is read.
  - chain.game_seeds and rng.act_seeds on the rng/seeds worked example (-seed 12345 and -seed 34844169): the game seed,
    the act bases, the Act II tombs, level 1's and level 134's create seeds;
  - the four game-creation draws are consecutive steps of Init(N), each the Init of its low word;
  - chain.line_sets on synthetic logs: affix lines, property lines, world lines, none;
  - the items oracle switch: chain.py check's default is the staff-mods model (oracle 2 retired).
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import chain  # noqa: E402
import rng  # noqa: E402


class GameSeeds(unittest.TestCase):
    def test_worked_example(self):
        g = chain.game_seeds(12345)
        self.assertEqual(g["game_seed"], (0x3039, 0x29A))
        self.assertEqual(g["map_seed"], 0x3039)
        base = rng.act_seeds(12345, 0)[0]
        self.assertEqual(base, 0x015B2E77)
        self.assertEqual((base + 1) & rng.MASK, 0x015B2E78)               # level 1 seed (rng/seeds step 4)
        a2 = rng.act_seeds(12345, 1)
        self.assertEqual((a2[3], a2[4]), (72, 71))
        self.assertEqual((a2[1], a2[2]), (0xB7A5C418, 0x63A93A78))
        self.assertEqual((rng.act_seeds(34844169, 0)[0] + 134) & rng.MASK, 0x0000000D)

    def test_draw_order(self):
        for n in (1, 12345, 0x7FFFFFFF):
            g = chain.game_seeds(n)
            s = (n, rng.INIT_HIGH)
            for k in ("monster_regions", "object_region", "store", "quest"):
                s = rng.step(*s)
                self.assertEqual(g[k], (s[0], rng.INIT_HIGH))
            self.assertEqual(g["game_seed_after_creation"], s)
        # draw 1 of the game seed equals the act base under an override (the same Init(N))
        self.assertEqual(chain.game_seeds(12345)["monster_regions"][0], rng.act_seeds(12345, 0)[0])


class LineSets(unittest.TestCase):
    def sets(self, text):
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
            f.write(text)
        try:
            return chain.line_sets(f.name)
        finally:
            os.unlink(f.name)

    def test_sets(self):
        self.assertEqual(self.sets('AF0 {"x":1}\n'), (True, False, False))
        self.assertEqual(self.sets('APE {"x":1}\nICJ {}\n'), (False, True, False))
        self.assertEqual(self.sets('RW1 {"room":1}\n'), (False, False, True))
        self.assertEqual(self.sets('RL {"room":1}\nICJ {}\nSTF0 {}\n'), (False, False, False))
        self.assertEqual(self.sets('APR0 {}\nSLOT {}\nP0 {}\n'), (True, True, True))


class Switches(unittest.TestCase):
    def test_staff_default(self):
        ns = chain.build_parser().parse_args(["check", "a.log"])
        self.assertEqual(ns.staff, "model")
        ns = chain.build_parser().parse_args(["check", "a.log", "--staff", "oracle"])
        self.assertEqual(ns.staff, "oracle")


if __name__ == "__main__":
    unittest.main()

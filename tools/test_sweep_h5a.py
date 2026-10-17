"""Unit tests for the pure helpers of tools/sweep_h5a.py (plan 0038 batch H5a): python3 -I tools/test_sweep_h5a.py.

They need no game data. Stdlib only.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sweep_h5a as S  # noqa: E402


class ChoiceKey(unittest.TestCase):
    def test_no_choice(self):
        self.assertIsNone(S.choice_key(0x6760F0, -1, -1, -1))
        self.assertIsNone(S.choice_key(0x6768C0, 0, -1, -1))

    def test_cycling_and_flip(self):
        self.assertEqual(S.choice_key(0x676150, 1, -1, 0), 1)
        self.assertEqual(S.choice_key(0x676450, 2, 0, 1), (2, 0))
        self.assertEqual(S.choice_key(0x676650, 1, 1, 0), (1, 1))

    def test_arreat_k(self):
        # k = b + 2 dir[anchor] (anchor = Rigid Highlands)
        self.assertEqual(S.choice_key(0x67D980, 1, -1, 1), 3)
        self.assertEqual(S.choice_key(0x67D980, 0, -1, 1), 2)

    def test_outer_steppes_from_rect(self):
        P = [100, 200, 50, 60]
        h = 40
        self.assertEqual(S.choice_key(0x676C00, 3, -1, -1, [150, 200 - 8, 30, h], P), 0)
        self.assertEqual(S.choice_key(0x676C00, 3, -1, -1, [150, 200 + 60 - h + 8, 30, h], P), 1)


class TouchClass(unittest.TestCase):
    def test_edges(self):
        a = [0, 0, 10, 10]
        self.assertEqual(S.touch_class(a, [10, 2, 5, 5]), "edge gx=0")
        self.assertEqual(S.touch_class(a, [2, 10, 5, 5]), "edge gy=0")

    def test_false_branches(self):
        a = [0, 0, 10, 10]
        self.assertEqual(S.touch_class(a, [10, 10, 5, 5]), "corner")
        self.assertEqual(S.touch_class(a, [20, 0, 5, 5]), "apart")
        self.assertEqual(S.touch_class(a, [10, 12, 5, 5]), "apart")     # gx = 0, gy > 0
        self.assertEqual(S.touch_class(a, [2, 2, 5, 5]), "overlap")


class Cover(unittest.TestCase):
    def test_greedy(self):
        sets = {1: {"a", "b"}, 2: {"b", "c", "d"}, 3: {"a"}}
        picks, left = S.greedy(sets, {"a", "b", "c", "d", "e"})
        self.assertEqual([s for s, _ in picks], [2, 1])
        self.assertEqual(left, {"e"})

    def test_target_key(self):
        self.assertEqual(S.target_key("final 0x00676150 level 3 choice 1"), "final 0x00676150 choice 1")
        self.assertEqual(S.target_key("reject 1a level 1: Rogue table 0 entry (index 12)"),
                         "reject 1a level 1: Rogue table 0 entry")

    def test_seed_of(self):
        self.assertEqual(S.seed_of("0000002a:00000666"), (42, 0x666))


if __name__ == "__main__":
    unittest.main()

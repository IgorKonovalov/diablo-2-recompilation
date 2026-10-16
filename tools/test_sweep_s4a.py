"""Unit tests for the pure helpers of tools/sweep_s4a.py (plan 0038 batch S4a): python3 -I tools/test_sweep_s4a.py.

They need no game data: the tile choice of DRLG_PickTileByRarity (3d), RectGapTest, RectContainsIncl, and the
logic-region merge (LOGIC_NeighbourMerge / EdgeMerge / RegionRelabel as read from the disassembly) on small synthetic
rooms. Stdlib only.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sweep_s4a as S  # noqa: E402


class Choice(unittest.TestCase):
    def test_single_candidate(self):
        # n = 1: the walk never runs, whatever r
        self.assertEqual(S.choose([("a", 5)], 5, 3), "a")

    def test_walk(self):
        c = [("a", 2), ("b", 3), ("c", 5)]          # total 10
        self.assertEqual(S.choose(c, 10, 0), "a")    # c = 1: a takes it
        self.assertEqual(S.choose(c, 10, 1), "a")    # c = 2: a's 2 brings it to 0
        self.assertEqual(S.choose(c, 10, 2), "b")
        self.assertEqual(S.choose(c, 10, 4), "b")
        self.assertEqual(S.choose(c, 10, 5), "c")
        self.assertEqual(S.choose(c, 10, 9), "c")

    def test_zero_total(self):
        # total 0: no draw and the first candidate
        self.assertEqual(S.choose([("a", 0), ("b", 0)], 0, 0), "a")


class Rects(unittest.TestCase):
    def test_gap(self):
        A = [0, 0, 8, 8]
        self.assertEqual(S.rect_gap_test(A, [8, 0, 8, 8], 1), 0)      # touching: both gaps <= 0
        self.assertEqual(S.rect_gap_test(A, [9, 0, 8, 8], 1), 1)      # one tile apart
        self.assertEqual(S.rect_gap_test(A, [8, 8, 8, 8], 1), 0)      # corner
        self.assertEqual(S.rect_gap_test(A, [8, 0, 8, 8], 0), 1)      # threshold 0: touching is not overlap

    def test_contains_incl(self):
        rc = [10, 20, 8, 8]
        self.assertTrue(S.contains_incl(rc, 18, 28))
        self.assertFalse(S.contains_incl(rc, 19, 28))


class Merge(unittest.TestCase):
    def rooms(self):
        # R (0, 0, 2, 1) and N (2, 0, 2, 1) share column x = 2; one box each, same level
        R = S.LogicRoom([0, 0, 2, 1], 7, ["R", "N"], False, [dict(id=5, kind=0, r0=[0, 0, 3, 2], b=1)])
        N = S.LogicRoom([2, 0, 2, 1], 7, ["N", "R"], False, [dict(id=3, kind=0, r0=[2, 0, 5, 2], b=2)])
        return {"R": R, "N": N}

    def test_relabel_to_neighbour_id(self):
        rooms = self.rooms()
        st = __import__("collections").Counter()
        S.neighbour_merge(rooms, "R", st)
        self.assertEqual(rooms["R"].boxes[0]["id"], 3)                # R's id takes N's
        self.assertEqual(rooms["N"].boxes[0]["id"], 3)

    def test_kind_and_level_block(self):
        rooms = self.rooms()
        rooms["N"].boxes[0]["kind"] = 1
        S.neighbour_merge(rooms, "R", __import__("collections").Counter())
        self.assertEqual(rooms["R"].boxes[0]["id"], 5)
        rooms = self.rooms()
        rooms["N"].level = 8
        S.neighbour_merge(rooms, "R", __import__("collections").Counter())
        self.assertEqual(rooms["R"].boxes[0]["id"], 5)

    def test_single_box_not_renamed(self):
        rooms = self.rooms()
        rooms["R"] = S.LogicRoom([0, 0, 2, 1], 7, ["R", "N"], True, [dict(id=1, kind=0, r0=None)])
        S.neighbour_merge(rooms, "R", __import__("collections").Counter())
        self.assertEqual(rooms["R"].boxes[0]["id"], 1)

    def test_recursive_relabel(self):
        rooms = self.rooms()
        # a third room Q, a near room of R only, with R's old id: renamed by the recursion
        rooms["Q"] = S.LogicRoom([0, 1, 2, 1], 7, ["Q", "R"], False, [dict(id=5, kind=0, r0=[0, 1, 3, 3], b=3)])
        rooms["R"].nb = ["R", "N", "Q"]
        S.neighbour_merge(rooms, "R", __import__("collections").Counter())
        self.assertEqual(rooms["Q"].boxes[0]["id"], 3)


if __name__ == "__main__":
    unittest.main()

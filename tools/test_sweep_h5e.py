"""Unit tests for the pure helpers of tools/sweep_h5e.py (plan 0038 batch H5e): python3 -I tools/test_sweep_h5e.py.

They need no game data. Stdlib only.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sweep_h5e as S  # noqa: E402


class ScanOrder(unittest.TestCase):
    def test_rows_outer(self):
        # 0x00680200 with r & 1 = 0: for y, for x -> x moves first
        self.assertEqual(S.scan_order([(0, 0), (1, 0), (2, 0)]), "rows")

    def test_columns_outer(self):
        # r & 1 = 1: for x < ch, for y < cw -> y moves first
        self.assertEqual(S.scan_order([(0, 0), (0, 1)]), "columns")

    def test_one_probe(self):
        self.assertIsNone(S.scan_order([(0, 0)]))
        self.assertIsNone(S.scan_order([]))


class EndpointSources(unittest.TestCase):
    def test_split(self):
        cw, ch = 4, 3
        defg = [[0] * cw for _ in range(ch)]
        cell = [[0] * cw for _ in range(ch)]
        defg[0][1], cell[0][1] = 5, 0x30000        # opening, index 3
        defg[1][0], cell[1][0] = 6, 0x20000        # border piece, index 2: not an opening
        defg[2][1] = 51                            # cave
        defg[1][2], cell[1][2] = 28, 0x10000       # bridge at x = cw - 2
        defg[1][1], cell[1][1] = 28, 0x10000       # bridge piece elsewhere: not counted
        adj = [{"nbr": 1}, {"nbr": 26}, {"nbr": 3}]
        self.assertEqual(S.endpoint_sources(adj, defg, cell, cw, ch), (1, 1, 1, 1, 1))


class FreeInterior(unittest.TestCase):
    def test_ring_ignored(self):
        cell = [[0x100] * 4 for _ in range(4)]
        cell[1][1] = 0
        cell[2][2] = 0x2                           # not in 0x1B81
        cell[1][2] = 0x800
        cell[0][0] = 0                             # ring cell: never counted
        self.assertEqual(S.free_interior(cell, 4, 4), 2)


class TombRole(unittest.TestCase):
    def test_roles(self):
        tombs = (70, 71)
        self.assertEqual(S.tomb_role(70, tombs), "true")
        self.assertEqual(S.tomb_role(71, tombs), "kaa")
        self.assertEqual(S.tomb_role(66, tombs), "plain")
        self.assertIsNone(S.tomb_role(57, tombs))
        self.assertIsNone(S.tomb_role(73, tombs))


if __name__ == "__main__":
    unittest.main()

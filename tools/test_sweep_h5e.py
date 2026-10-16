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

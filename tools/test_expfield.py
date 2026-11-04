#!/usr/bin/env python3
"""Tests of tools/expfield.py: python3 -I tools/test_expfield.py"""
import os
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import expfield as ef  # noqa: E402


def make(rows, cols, cells, unk=266):
    return struct.pack("<HII", unk, rows, cols) + bytes(cells)


class T(unittest.TestCase):
    def test_parse(self):
        unk, r, c, cells = ef.parse(make(3, 3, [3, 4, 5, 2, 8, 6, 1, 0, 7]))
        self.assertEqual((unk, r, c, len(cells)), (266, 3, 3, 9))

    def test_parse_size_mismatch(self):
        with self.assertRaises(ValueError):
            ef.parse(make(3, 3, [8] * 8))
        with self.assertRaises(ValueError):
            ef.parse(b"\x00" * 5)

    def test_walk_reaches_centre(self):
        # byte d steps (DX[d], DY[d]): 3 is down-right, 7 up-left; centre in the middle
        d = make(3, 3, [3, 4, 5, 2, 8, 6, 1, 0, 7])
        _u, r, c, cells = ef.parse(d)
        self.assertEqual(ef.walk(cells, r, c, 0, 0), [(0, 0), (1, 1)])
        self.assertEqual(ef.walk(cells, r, c, 2, 1), [(2, 1), (1, 1)])
        self.assertEqual(ef.walk(cells, r, c, 1, 2), [(1, 2), (1, 1)])

    def test_walk_leaves_table_and_loops(self):
        _u, r, c, cells = ef.parse(make(1, 2, [1, 8]))   # byte 1 from (0,0) goes to (1,-1)
        self.assertIsNone(ef.walk(cells, r, c, 0, 0))
        _u, r, c, cells = ef.parse(make(1, 2, [2, 6]))   # east then west, forever
        self.assertIsNone(ef.walk(cells, r, c, 0, 0, limit=50))
        _u, r, c, cells = ef.parse(make(1, 1, [9]))
        self.assertIsNone(ef.walk(cells, r, c, 0, 0))

    def test_step_tables(self):
        self.assertEqual(len(ef.DX), 9)
        self.assertEqual(ef.DX[ef.CENTRE], 0)
        self.assertEqual(ef.DY[ef.CENTRE], 0)
        self.assertEqual(sorted(zip(ef.DX[:8], ef.DY[:8])), sorted((a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a, b) != (0, 0)))

    def test_check_synthetic(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "f.d2")
            open(p, "wb").write(make(3, 3, [3, 4, 5, 2, 8, 6, 1, 0, 7]))
            self.assertEqual(ef.check(p), 0)
            open(p, "wb").write(make(3, 3, [3, 4, 5, 2, 8, 6, 1, 0, 9]))
            self.assertNotEqual(ef.check(p), 0)


if __name__ == "__main__":
    unittest.main()

"""Tests for tools/room_extent.py (synthetic inputs, no game data). Run: python3 -I tools/test_room_extent.py"""
import os
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import room_extent as R  # noqa: E402


class Rules(unittest.TestCase):
    def test_maze_room(self):
        self.assertEqual(R.maze_room(12, 12), (12, 12))
        self.assertEqual(R.maze_room(10, 14), (8, 8))        # one side past 12: the 8 x 8 split
        self.assertEqual(R.maze_room(13, 13), (8, 8))
        self.assertEqual(R.maze_room(8, 8), (8, 8))
        self.assertEqual(R.maze_room(64, 64), (8, 8))

    def test_split(self):
        self.assertEqual(R.split_room(56, 40), (8, 8))
        self.assertEqual(R.split_room(5, 20), (5, 8))

    def test_threshold(self):
        # path/0002 § 9: 197 x 197 fits, 198 x 198 overruns, both pass the assert
        a = R.rect_numbers_sub(197, 197)
        b = R.rect_numbers_sub(198, 198)
        self.assertEqual((a["clear"], a["overruns"], a["asserts"]), (223 * 223, False, False))
        self.assertEqual((b["clear"], b["overruns"], b["asserts"]), (224 * 224, True, False))
        self.assertEqual(R.threshold_square(), 198)

    def test_largest_stock_room(self):
        n = R.rect_numbers(12, 12)
        self.assertEqual(n["room"], (60, 60))
        self.assertEqual(n["rect"], (80, 80))
        self.assertEqual(n["clear"], 86 * 86)
        self.assertFalse(n["overruns"])

    def test_threshold_band(self):
        # 198..203 pass the assert and overrun, 204 asserts first (rectangle 224 x 224, path/0002 § 9)
        self.assertTrue(R.rect_numbers_sub(203, 203)["overruns"])
        self.assertFalse(R.rect_numbers_sub(203, 203)["asserts"])
        self.assertTrue(R.rect_numbers_sub(204, 204)["asserts"])

    def test_pair_bounds(self):
        self.assertEqual(R.pair_side_near(12), 145)
        self.assertEqual(R.pair_side_window(12), 220)
        near = R.rect_numbers_sub(145 - R.MARGIN, 145 - R.MARGIN)
        win = R.rect_numbers_sub(220 - R.MARGIN, 220 - R.MARGIN)
        self.assertEqual((near["clear"], near["overruns"]), (151 * 151, False))
        self.assertEqual((win["clear"], win["overruns"], win["asserts"]), (226 * 226, True, False))

    def test_small_maze_records(self):
        recs = [dict(defn=d, sx=12, sy=12) for lo, hi in R.SMALL_MAZE_DEFS.values() for d in range(lo, hi + 1)]
        self.assertTrue(all(v[1] == 12 for v in R.small_maze_records(recs).values()))
        recs[0]["sx"] = 16
        self.assertEqual(R.small_maze_records(recs)["4 Crypt"][1], 16)


def rec(size, fields):
    b = bytearray(size)
    for off, fmt, v in fields:
        struct.pack_into(fmt, b, off, v)
    return bytes(b)


class Scan(unittest.TestCase):
    def test_scan_and_report(self):
        with tempfile.TemporaryDirectory() as root:
            ex = os.path.join(root, "data", "global", "excel")
            os.makedirs(ex)

            def put(name, recs):
                open(os.path.join(ex, name + ".bin"), "wb").write(struct.pack("<I", len(recs)) + b"".join(recs))
            put("leveldefs", [rec(156, [(0x30, "<I", 1), (0x0C, "<i", 0)]),
                              rec(156, [(0x30, "<I", 3), (0x0C, "<i", 80), (0x18, "<i", 80)])])
            put("lvlmaze", [rec(28, [(0, "<I", 0), (0x10, "<i", 12), (0x14, "<i", 12)])])
            put("lvlprest", [rec(432, [(0, "<i", d), (0x28, "<i", 40), (0x2C, "<i", 24)])
                             for lo, hi in R.SMALL_MAZE_DEFS.values() for d in (lo, hi)])
            open(os.path.join(ex, "levels.txt"), "wb").write(b"Name\tId\r\nA\t0\r\nB\t1\r\n")
            L, rooms, lv, maze, prest = R.report(root)
            self.assertTrue(any("LARGEST ROOM 12x12 tiles = 60x60 subtiles" in x for x in L))
            self.assertEqual(sorted(set(r[0] for r in rooms)), ["maze", "outdoor", "preset"])
            self.assertTrue(any("a record larger than the 12 x 12 test in those blocks: True" in x for x in L))


if __name__ == "__main__":
    unittest.main()

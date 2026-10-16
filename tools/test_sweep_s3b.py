"""Unit tests of the pure helpers of tools/sweep_s3b.py (no game files needed). Run: python3 -I tools/test_sweep_s3b.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweep_s3b as S  # noqa: E402
import sweep_s4b as S4  # noqa: E402

LISTING = """
00401000 <.text>:
  401000:\tcall   0x402000
  401005:\ttest   BYTE PTR [esi+0x34],0x1
  401009:\tjne    0x401020
  40100b:\tcall   0x403000
  401010:\tcall   0x404000
  401015:\tret
  401020:\tcall   0x405000
  401025:\ttest   eax,eax
  401027:\tjne    0x401015
  401029:\tcall   0x404000
  40102e:\tjmp    0x401015
"""


class FakeAsm:
    def __init__(self, ins):
        self.ins = ins
        self._s = sorted(ins)

    def at(self, va):
        return self.ins.get(va)

    def next_va(self, va):
        for x in self._s:
            if x > va:
                return x
        return None


class T(unittest.TestCase):
    def test_comp_count(self):
        self.assertEqual(S.comp_count(""), 0)
        self.assertEqual(S.comp_count("lit"), 1)
        self.assertEqual(S.comp_count('"lit,med,hvy"'), 3)
        self.assertEqual(S.comp_count("a,toolong,b"), 1)          # a token over 4 characters stops the list
        self.assertEqual(S.comp_count("a,,b"), 1)                 # an empty token stops it
        self.assertEqual(S.comp_count(",".join(["x"] * 15)), 12)  # at most 12

    def test_comp_sum(self):
        self.assertEqual(S.comp_sum([0, 1, 1] + [0] * 13), 0)
        self.assertEqual(S.comp_sum([3, 2, 1, 0] + [0] * 12), 3)
        self.assertEqual(S.comp_sum([12] * 16), 0xB0)
        self.assertEqual(S.comp_sum([255] * 16), 0xFE)            # the cap

    def test_shift_count(self):
        self.assertEqual(S.shift_count(1024), 11)
        self.assertEqual(S.shift_count(1023), 10)
        self.assertEqual(S.shift_count(5), 10)
        self.assertEqual(S.shift_count(0), 10)

    def test_greatest_band(self):
        rows = [{"Id": 1, "Version": 0, "Level": 5}, {"Id": 1, "Version": 0, "Level": 20},
                {"Id": 1, "Version": 100, "Level": 9}, {"Id": 2, "Version": 0, "Level": 1}]
        self.assertEqual(S.greatest_band(rows, 0, 1, 3), 0)       # below every band: the first row
        self.assertEqual(S.greatest_band(rows, 0, 1, 19), 0)
        self.assertEqual(S.greatest_band(rows, 0, 1, 20), 1)
        self.assertEqual(S.greatest_band(rows, 1, 1, 50), 2)
        self.assertIsNone(S.greatest_band(rows, 1, 2, 5))
        self.assertIsNone(S.greatest_band(rows, 0, 300, 5))

    def test_region_act_class(self):
        self.assertEqual(S.region_act_class([39, 22, 384], 0), 383)
        self.assertEqual(S.region_act_class([172, 384], 0), 170)  # the first entry in a range decides
        self.assertEqual(S.region_act_class([7], 0), 5)
        self.assertEqual(S.region_act_class([7], 1), S.REGION_DEFAULT)   # Act II uses the 0x60 range instead
        self.assertEqual(S.region_act_class([98], 1), 0x60)
        self.assertEqual(S.region_act_class([], 0), S.REGION_DEFAULT)

    def test_call_paths(self):
        A = FakeAsm(S4.parse_listing(LISTING))
        self.assertEqual(S.call_paths(A, 0x401000), {
            (0x402000, 0x403000, 0x404000), (0x402000, 0x405000), (0x402000, 0x405000, 0x404000)})
        self.assertEqual(S.call_paths(A, 0x401020, stop={0x401015}), {(0x405000,), (0x405000, 0x404000)})


if __name__ == "__main__":
    unittest.main()

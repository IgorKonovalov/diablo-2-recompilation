"""Unit tests of the pure helpers of tools/sweep_s4b.py (no game files needed). Run: python3 -I tools/test_sweep_s4b.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweep_s4b as S  # noqa: E402

LISTING = """
00401000 <.text>:
  401000:\tpush   ebp
  401001:\tcall   0x401020
  401006:\tje     0x401010
  401008:\tmov    ecx,0x6ac690c5
  40100d:\tjmp    0x401012
  40100f:\t(bad)
  401010:\tcall   DWORD PTR [eax+0x4]
  401012:\tret
  401020:\tcall   0x45c390
  401025:\tret
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
    def setUp(self):
        self.ins = S.parse_listing(LISTING)

    def test_parse_drops_bad_and_headers(self):
        self.assertNotIn(0x40100F, self.ins)
        self.assertEqual(self.ins[0x401001], ("call", "0x401020"))
        self.assertEqual(len(self.ins), 9)

    def test_branch_target_and_imm(self):
        self.assertEqual(S.branch_target("0x401020"), 0x401020)
        self.assertIsNone(S.branch_target("DWORD PTR [eax+0x4]"))
        self.assertTrue(S.has_imm("ecx,0x6ac690c5", S.LCG_MUL))
        self.assertFalse(S.has_imm("ecx,0x6ac690c6", S.LCG_MUL))

    def test_body_follows_branches_and_records_calls(self):
        A = FakeAsm(self.ins)
        vas, calls, icalls = S.body(A, 0x401000)
        self.assertEqual(calls, [(0x401001, 0x401020)])
        self.assertEqual(icalls, [0x401010])
        self.assertIn(0x401012, vas)            # reached by both the jcc path and the jmp
        self.assertNotIn(0x401020, vas)         # a call target is another body

    def test_rng_sites(self):
        A = FakeAsm(self.ins)
        vas, _, _ = S.body(A, 0x401000)
        lcg, rc = S.rng_sites(A, vas)
        self.assertEqual(lcg, [0x401008])
        vas2, _, _ = S.body(A, 0x401020)
        self.assertEqual(S.rng_sites(A, vas2)[1], [(0x401020, "RNG_Range")])


if __name__ == "__main__":
    unittest.main()

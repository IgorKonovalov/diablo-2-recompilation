"""Unit tests of the pure models of tools/sweep_s1f.py (no game files, no Ghidra). Run: python3 -I tools/test_sweep_s1f.py"""
import collections
import os
import random
import struct
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweep_s1f as S  # noqa: E402

M32 = 0xFFFFFFFF


class T(unittest.TestCase):
    def test_validid(self):
        self.assertEqual(S.validid_model(0, 734), 0)
        self.assertEqual(S.validid_model(733, 734), 733)
        self.assertEqual(S.validid_model(734, 734), -1)
        self.assertEqual(S.validid_model(-1, 734), -1)
        self.assertEqual(S.validid_model(5, -1), -1)               # signed compare against the count
        self.assertEqual(S.validid_model(734, 734, neg=True), 734)

    def test_muldiv_branches(self):
        br = collections.Counter()
        self.assertEqual(S.muldiv_model(7, 9, 0, br=br)[0], 0)
        self.assertEqual(S.muldiv_model(10000, 9981, 100, br=br)[0], 998100)         # the creation branch
        self.assertEqual(S.muldiv_model(0x200000, 3, 7, br=br)[0], (0x200000 // 7) * 3)  # truncates first
        q = (0x200000 * 3) // 0x100000
        self.assertEqual(S.muldiv_model(0x200000, 3, 0x100000, br=br)[0], q)          # c > a >> 4: 64-bit
        self.assertEqual(S.muldiv_model(5, 0x20000, 3, br=br)[0], (0x20000 // 3) * 5)
        self.assertEqual(S.muldiv_model(-7, 2, 2, br=br)[0], (-7) & M32)              # toward zero
        self.assertEqual(S.muldiv_model(-7, 1, 2, br=br)[0], (-3) & M32)
        eax, edx = S.muldiv_model(0x7FFFFFFF, 0x7FFFFFFF, 0x7FFFFFFF)
        self.assertEqual(eax, 0x7FFFFFFF)                                              # a > 2^20, c > a >> 4
        with self.assertRaises(S.Fault):
            S.muldiv_model(-0x80000000, 1, -1)
        self.assertIn("a_big_div_first", br)
        self.assertIn("b_big_div_first", br)

    def test_candadd_cap(self):
        win = bytes(48)
        base = (S.ARR + 8 * 510 - 16) & M32
        n, w = S.candadd_model(win, base, 510, 0x11111111, 0x22222222)
        self.assertEqual(n, 511)
        self.assertEqual(w[16:24], struct.pack("<II", 0x22222222, 0x11111111))
        base = (S.ARR + 8 * 511 - 16) & M32
        n, w = S.candadd_model(win, base, 511, 1, 2)
        self.assertEqual((n, w), (511, win))                                          # the 512th is dropped
        n, w = S.candadd_model(win, base, 511, 1, 2, neg=True)
        self.assertEqual(n, 512)

    def test_bands(self):
        b = [1, 10, 100, 1000, 10000]
        self.assertEqual(S.ElemWorld.bands(1, b), 0)
        self.assertEqual(S.ElemWorld.bands(8, b), 7)
        self.assertEqual(S.ElemWorld.bands(16, b), 7 + 80)
        self.assertEqual(S.ElemWorld.bands(22, b), 7 + 80 + 600)
        self.assertEqual(S.ElemWorld.bands(28, b), 7 + 80 + 600 + 6000)
        self.assertEqual(S.ElemWorld.bands(30, b), 7 + 80 + 600 + 6000 + 20000)

    def test_descmissile_index(self):
        w = S.ElemWorld(random.Random(5))
        sk = bytearray(w.sk[0])
        struct.pack_into("<h", sk, 0x194, 0)
        w.sk[0] = bytes(sk)
        sd = bytearray(w.sd[0])
        struct.pack_into("<3h", sd, 0x3C, 2, 3, 4)
        w.sd[0] = bytes(sd)
        for m in (2, 3, 4):
            r = bytearray(w.mi[m])
            struct.pack_into("<I", r, 0x118, M32)
            r[0x196] = 0
            struct.pack_into("<i", r, 0xE8, 1000 * m)
            struct.pack_into("<i", r, 0xEC, 1000 * m + 1)
            w.mi[m] = bytes(r)
        got = [w.calcvar43(c, 0, 1) for c in range(43, 49)]
        self.assertEqual(got, [2000, 2001, 2000, 2001, 3000, 3001])                   # m2eo/m2ey read missile 1
        self.assertEqual(w.calcvar43(46, 0, 1, neg=True), 3001)

    def test_varroll_tries_negative(self):
        w = S.RollWorld()
        ms = bytearray(0x1A8)
        m2 = bytearray(0x134)
        m2[0x15] = 2
        m2[0x25] = 2
        w.ms, w.m2 = [bytes(ms)], [bytes(m2)]
        e = bytearray(0x34)
        e[3] = 2                                                                       # set 0 == set 1 (all zero)
        found = None
        for seed in range(1, 2000):                                                   # (0, 0) is the LCG's fixed point
            br = collections.Counter()
            lo, hi, out = w.roll(seed, 0, bytes(e), 1, br=br)
            if br["tries_went_negative"]:
                found = (seed, out)
                break
        self.assertIsNotNone(found)
        seed, out = found
        self.assertEqual(out[3], 3)
        self.assertEqual(out[4 + 32], 1)                                               # ran on to a non-duplicate
        lo, hi, alt = w.roll(seed, 0, bytes(e), 1, neg=True)
        self.assertEqual(alt[4 + 32], 0)                                               # a <= 0 test stops at -1

    def test_setpick_weight0(self):
        w = S.SetWorld()
        w.codes = [7]
        rec = bytearray(0x1B8)
        struct.pack_into("<I", rec, 0x28, 7)
        sets = [bytes(rec), bytes(rec)]                                                 # weights 0, 0
        it = {"seed": [1, 666], "fi": 0, "flags": 0x10, "ver": 101, "code": 7, "ilvl": 50}
        r = w.pick(sets, it, {"f40": 0, "f80": 0})
        self.assertEqual(r[0], 1)                                                       # 0 counts as 1: W = 2
        self.assertEqual(r[3], S.RNG.step(1, 666)[0] % 2)
        self.assertEqual(r[4], 0)
        self.assertEqual(w.pick(sets, it, {"f40": 0, "f80": 0}, neg=True)[0], 0)       # W = 0: no pick
        neg = bytearray(rec)
        struct.pack_into("<i", neg, 0x34, -5)
        r = w.pick([bytes(neg)], it, {"f40": 0, "f80": 0})
        self.assertEqual(r[:3], (0, 1, 666))                                            # W < 0: no draw, walk fails


if __name__ == "__main__":
    unittest.main()

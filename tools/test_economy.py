#!/usr/bin/env python3
"""Tests for tools/economy.py (plan 0043 Phase 2): the integer helpers against the instruction forms they model, and
the price model on the stock tables (skipped without workspace/). Run: python3 -I tools/test_economy.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import economy  # noqa: E402

EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")


def sar_div(x, k):
    """cdq; and edx, 2^k - 1; add eax, edx; sar eax, k  (the compiler's signed x / 2^k)."""
    x = economy.w32(x)
    if x < 0:
        x += (1 << k) - 1
    return x >> k


class Helpers(unittest.TestCase):
    def test_d1024_matches_sar_form(self):
        for x in (0, 1, 1023, 1024, 1025, -1, -1023, -1024, -1025, 0x7FFFFFFF, -0x80000000, 123456789, -98765):
            self.assertEqual(economy.d1024(x), sar_div(x, 10), x)
            self.assertEqual(economy.d4096(x), sar_div(x, 12), x)

    def test_tdiv_truncates(self):
        self.assertEqual(economy.tdiv(-7, 2), -3)
        self.assertEqual(economy.tdiv(7, -2), -3)
        self.assertEqual(economy.tdiv(-7, -2), 3)

    def test_imul_wraps(self):
        self.assertEqual(economy.imul(0x10000, 0x10000), 0)
        self.assertEqual(economy.imul(0x7FFFFFFF, 2), -2)

    def test_udiv_add_treats_negative_as_unsigned(self):
        # PriceStatTerms adds dP / n with `div` (unsigned): a negative sum over n = 2 adds 0x7FFFFFFF.. not -x/2
        self.assertEqual(economy.udiv_add(10, -2, 2), economy.w32(10 + 0x7FFFFFFF))
        self.assertEqual(economy.udiv_add(10, -2, 1), 8)

    def test_muldiv_branches(self):
        self.assertEqual(economy.muldiv(1000, 25, 0), 0)
        self.assertEqual(economy.muldiv(1000, 25, 100), 250)                    # plain (a*b)/c
        self.assertEqual(economy.muldiv(0x200000, 25, 100), (0x200000 // 100) * 25)   # a large, c <= a >> 4
        self.assertEqual(economy.muldiv(0x200000, 25, 0x30000), 0x200000 * 25 // 0x30000)   # 64-bit path
        self.assertEqual(economy.muldiv(7, 0x20000, 100), (0x20000 // 100) * 7)  # b large, c <= b >> 4

    def test_rangeb_power_of_two_masks(self):
        r, lo, hi = economy.rng_rangeb(1, 666, 8)
        self.assertEqual(r, lo & 7)
        r, lo2, hi2 = economy.rng_rangeb(1, 666, 7)
        self.assertEqual((lo2, hi2), (lo, hi))
        self.assertEqual(r, lo % 7)


@unittest.skipUnless(os.path.isdir(EXCEL), "no workspace/ (game data)")
class PriceModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.T = economy.Tables(EXCEL)
        cls.M = economy.Model(cls.T)

    def item(self, code, **kw):
        c = self.T.by_code[code.ljust(4).encode()]
        d = {"u": 1, "t": 4, "c": c, "q": 2, "fl": 0x10, "fi": -1, "v": 101, "aa": 0, "pre": [0, 0, 0],
             "suf": [0, 0, 0], "ear": 0, "lf": 0x80000000, "own": [], "cache": [], "ch": []}
        d.update(kw)
        return d

    def payload(self, it, mode, npc=154, d=0, plv=30, prp=0):
        return {"m": mode, "d": d, "npc": npc, "plv": plv, "prp": prp, "pt": 0, "qb": None, "it": it}

    def test_starting_item_is_one(self):
        it = self.item("rin", fl=0x10 | 0x20000)
        for mode in (0, 1, 3):
            self.assertEqual(self.M.price(self.payload(it, mode)), 1 if mode != 3 else 0)

    def test_ethereal_quarter_on_sell_only(self):
        """Required case 2 (items/0011 Leads used): S / 4 for an ethereal item, P unchanged."""
        plain = self.item("rin")
        eth = self.item("rin", fl=0x10 | 0x400000)
        self.assertEqual(self.M.price(self.payload(eth, 0)), self.M.price(self.payload(plain, 0)))
        s_plain, s_eth = self.M.price(self.payload(plain, 1)), self.M.price(self.payload(eth, 1))
        self.assertTrue(s_eth < s_plain)

    def test_gamble_ring_is_gamble_cost(self):
        it = self.item("rin")
        b = self.T.base(it["c"])
        self.assertEqual(self.M.price(self.payload(it, 2)), economy.s32(b, 0xD4))


if __name__ == "__main__":
    unittest.main()

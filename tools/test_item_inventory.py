#!/usr/bin/env python3
"""Tests of tools/item_inventory.py: python3 -I tools/test_item_inventory.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import item_inventory as inv  # noqa: E402


def rec(ln, state, slots, isc=None):
    return {"len": ln, "state": state, "slots": slots + [(-1, 0)] * (3 - len(slots)), "isc": isc or {}}


class T(unittest.TestCase):
    def test_class_tables(self):
        self.assertEqual([inv.life_mul(0, c, 100) for c in range(7)], [150, 100, 100, 150, 200, 100, 150])
        self.assertEqual([inv.mana_mul(0, c, 100) for c in range(7)], [150, 200, 200, 150, 100, 200, 150])
        self.assertEqual(inv.life_mul(1, 0, 100), 200)
        self.assertEqual(inv.mana_mul(1, 1, 100), 100)
        self.assertEqual(inv.life_mul(0, 0, -3), -5)  # shift floors

    def test_no_draw_at_zero_vitality(self):
        u = inv.Unit(typ=0, cls=4, low=5, high=7, stats={inv.VIT: 0})
        inv.potion_scale(u, inv.HPREGEN, 30)
        self.assertEqual((u.low, u.high), (5, 7))

    def test_two_draws_and_doubling(self):
        for low in range(1, 2000):
            u = inv.Unit(typ=0, cls=1, low=low, high=3, stats={inv.VIT: 50})
            v = inv.potion_scale(u, inv.HPREGEN, 1)
            self.assertIn(v, (256, 512))
            w = inv.Unit(low=low, high=3)
            r1 = w.range(50)
            r2 = w.range(100)
            self.assertEqual(v == 512, r2 < r1 >> 1)
            self.assertEqual((u.low, u.high), (w.low, w.high))

    def test_refill_rate(self):
        u = inv.Unit(typ=1, slist={"end": 150, "base": {inv.MANAREC: 7}})
        r = rec(100, 5, [(-1, 0)])
        r["slots"][0] = (9, 0)
        r["slots"][1] = (inv.MANAREC, 10)
        self.assertEqual(inv.use_stat_entry(4, u, r, 100, 0, 400, 192), ("setstat", 26, (7 * 50 + 2560) // 150, 250))

    def test_rejuv_percent_and_cap(self):
        isc = {inv.LIFE: (8, inv.MAXLIFE)}
        r = rec(0, 0, [(inv.LIFE, 35)], isc)
        u = inv.Unit(typ=1, stats={inv.LIFE: 100, inv.MAXLIFE: 25600})
        self.assertEqual(inv.use_stat_entry(5, u, r, 1, 0, 400, 192), ("addstat", 6, 8960))
        u = inv.Unit(typ=1, stats={inv.LIFE: 20000, inv.MAXLIFE: 25600})
        self.assertEqual(inv.use_stat_entry(5, u, r, 1, 0, 400, 192), ("addstat", 6, 5600))

    def test_entry3_breaks_entry5_continues(self):
        r = rec(0, 0, [(-1, 0), (inv.MANA, 35)], {inv.MANA: (8, inv.MAXMANA)})
        u = inv.Unit(typ=1, stats={inv.MAXMANA: 25600})
        self.assertEqual(inv.use_stat_entry(3, u, r, 1, 0, 400, 192), ("ret", 0))
        self.assertEqual(inv.use_stat_entry(5, u, r, 1, 0, 400, 192), ("addstat", 8, 8960))

    def test_chance(self):
        self.assertEqual(inv.double_chance(0), (0, 1))
        self.assertEqual(inv.double_chance(4), (0 + 0 + 1 + 1, 400))

    def test_stock_total(self):
        self.assertEqual(inv.potion_total(4, inv.HPREGEN, 30), 15360)
        self.assertEqual(inv.potion_total(1, inv.MANAREC, 20), 10240)


if __name__ == "__main__":
    unittest.main()

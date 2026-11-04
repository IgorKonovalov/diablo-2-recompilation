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

    def test_chance_published_closed_forms(self):
        # items/0017 H0: the forms src:arreat-summit-character-basics publishes, as exact fractions
        from fractions import Fraction as F

        def published(n):
            if n <= 200:
                return F(n - 2, 4) if n % 2 == 0 else F((n - 1) ** 2, 4 * n)
            return F(100 * (n - 101), n)

        for n in range(2, 5001):
            hits, cases = inv.double_chance(n)
            self.assertEqual(F(hits * 100, cases), published(n), n)

    def test_stock_total(self):
        self.assertEqual(inv.potion_total(4, inv.HPREGEN, 30), 15360)
        self.assertEqual(inv.potion_total(1, inv.MANAREC, 20), 10240)

    def test_score_corner_and_enclosed(self):
        g = inv.InvGrid(10, 4)
        self.assertEqual(g.score(0, 0, 1, 1), 2)
        self.assertEqual(inv.InvGrid(1, 1).score(0, 0, 1, 1), 255)
        self.assertEqual(g.score(5, 1, 1, 1), 0)

    def test_search_orders(self):
        g = inv.InvGrid(10, 4)
        self.assertEqual(inv.spot_find(g, 1, 1, True), (9, 3))
        self.assertEqual(inv.spot_find(g, 2, 2, True), (0, 0))
        self.assertEqual(inv.spot_find(g, 1, 1, False), (9, 0))
        self.assertEqual(inv.spot_find(g, 2, 2, False), (0, 0))
        self.assertIsNone(inv.spot_find(inv.InvGrid(1, 1, [(0, 0)]), 1, 1, True))

    def test_search_prefers_contact(self):
        g = inv.InvGrid(10, 4, [(0, 2)])
        self.assertEqual(inv.spot_find(g, 2, 2, True), (0, 0))
        g = inv.InvGrid(3, 3, [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)])
        self.assertEqual(inv.spot_find(g, 2, 2, True), (1, 1))

    def test_inv_row(self):
        self.assertEqual([inv.inv_row(0, c, 0, 1) for c in range(7)], [0, 1, 2, 3, 4, 14, 15])
        self.assertEqual(inv.inv_row(0, 0, 4, 1), 12)
        self.assertEqual(inv.inv_row(0, 0, 4, 0), 8)
        self.assertEqual([inv.inv_row(0, 0, p, 1) for p in (1, 2, 3)], [6, 7, 9])
        self.assertEqual(inv.inv_row(1, 271, 0, 1), 5)
        self.assertEqual((inv.inv_row(2, 0x152, 0, 1), inv.inv_row(2, 0x153, 0, 1), inv.inv_row(2, 3, 0, 1)), (10, 11, -1))

    def test_belt(self):
        boxes = [None] * 16
        self.assertEqual(inv.belt_slot(4, boxes, "hp1 ", set(), 1), 0)
        self.assertIsNone(inv.belt_slot(4, boxes, "tsc ", set(), 0))
        boxes[0] = "hp3 "
        self.assertEqual(inv.belt_slot(8, boxes, "hp1 ", set(), 1), 4)
        boxes[4] = "hp3 "
        self.assertEqual(inv.belt_slot(8, boxes, "hp1 ", set(), 1), 1)
        self.assertEqual(inv.belt_slot(8, boxes, "mp1 ", set(), 1), 1)
        self.assertIsNone(inv.belt_slot(4, ["hp1 "] * 4 + [None] * 12, "hp1 ", set(), 1))

    def test_stack(self):
        a = dict(cls=7, d0=2, file=5, stackable=1, eth=0, stats={})
        self.assertTrue(inv.stack_ok(a, dict(a)))
        self.assertFalse(inv.stack_ok(a, dict(a, eth=1)))
        self.assertFalse(inv.stack_ok(dict(a, d0=4), dict(a, d0=4)))
        self.assertTrue(inv.stack_ok(dict(a, d0=10), dict(a, d0=10)))
        self.assertFalse(inv.stack_ok(a, dict(a, stats={194: 1})))
        self.assertTrue(inv.stack_ok(dict(a, stats={194: 256}), dict(a, stats={194: 256})))
        self.assertEqual(inv.max_stack(500, 11), 511)
        self.assertEqual(inv.max_stack(500, 10), 510)
        self.assertEqual(inv.merge_first_set(5, 5, 8), (70, 8))
        self.assertEqual(inv.merge_first_set(3, 5, 8, 2, 9), (72, 2))
        self.assertEqual(inv.merge_first_set(3, 5, 8, 9, 2), (70, 8))


    # ---- P1.3: the ground drop's cell search over a toy field, the expiry, the distance, the line ends

    @staticmethod
    def toy_field():
        """A field with each cell pointing straight along its larger axis, then diagonally: enough for short walks."""
        out = bytearray(65536)
        for y in range(256):
            for x in range(256):
                dx, dy = 128 - x, 128 - y
                sx, sy = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
                out[y * 256 + x] = next(i for i in range(9) if (inv.DIR_DX[i], inv.DIR_DY[i]) == (sx, sy))
        return bytes(out)

    def test_drop_offset_and_rings(self):
        f = self.toy_field()
        r = inv.Room(0, 0, 20, 20, {})
        self.assertEqual(inv.ground_drop_cell(r, 5, 5, f)[1:], (7, 8))
        r.cells[(7, 8)] = 0x200
        self.assertEqual(inv.ground_drop_cell(r, 5, 5, f)[1:], (6, 8), "ring 1: lowest distance, sides by row, left first")
        # an off-room offset cell starts at the position
        self.assertEqual(inv.ground_drop_cell(inv.Room(0, 0, 6, 6, {}), 5, 5, f)[1:], (5, 5))

    def test_line_mask_and_origin(self):
        f = self.toy_field()
        cells = {(6, 7): 0x800}
        self.assertEqual(inv.line_cells(f, 5, 5, 7, 8)[0], (7, 8))
        self.assertNotIn((5, 5), inv.line_cells(f, 5, 5, 7, 8))
        self.assertEqual(inv.line_blocked(f, 5, 5, inv.Room(0, 0, 20, 20, cells), 7, 8, 0x801), 1)
        self.assertEqual(inv.line_blocked(f, 5, 5, inv.Room(0, 0, 20, 20, {(6, 7): 0x200}), 7, 8, 0x801), 0)

    def test_fallback_and_base_room(self):
        f = self.toy_field()
        full = {(x, y): 0x200 for x in range(100) for y in range(100)}
        r = inv.Room(0, 0, 100, 100, full)
        self.assertEqual(inv.ground_drop_cell(r, 50, 50, f, 1)[0], r)
        self.assertEqual(inv.ground_drop_cell(r, 50, 50, f, 1)[1:], (52, 53))
        self.assertIsNone(inv.ground_drop_cell(r, 50, 50, f, 0)[0])
        # the base moves to a room whose near list lacks the first: the fallback's lookup returns None
        a, b = inv.Room(0, 0, 10, 10, {(x, y): 1 for x in range(10) for y in range(10)}), inv.Room(10, 0, 10, 10, {(x, y): 1 for x in range(10, 20) for y in range(10)})
        a.near = [b]
        self.assertIsNone(inv.ground_drop_cell(a, 2, 2, f, 1)[0])

    def test_expiry(self):
        self.assertEqual(inv.ground_expiry(10, 1, 7, 9, None, False), 0)
        self.assertEqual(inv.ground_expiry(10, 0, 4, 9, None, False), 30010)
        self.assertEqual(inv.ground_expiry(10, 0, 5, 9, None, False), 45010)
        self.assertEqual(inv.ground_expiry(10, 0, 2, 4, 10000, False), 15010)
        self.assertEqual(inv.ground_expiry(10, 0, 2, 4, 10001, False), 45010)
        self.assertEqual(inv.ground_expiry(10, 0, 2, 9, None, True), 30010)
        self.assertEqual(inv.ground_expiry(10, 0, 3, 9, None, False), 15010)

    def test_sweep(self):
        self.assertIsNone(inv.sweep_first([(4, 0), (1, 5), (4, 11)], 10))
        self.assertEqual(inv.sweep_first([(4, 0), (1, 5), (4, 10)], 10), 2)

    def test_line_ends(self):
        self.assertIsNone(inv.line_ends(0, 0, 2, 1, 1, 1))
        self.assertEqual(inv.line_ends(0, 0, 2, 5, 1, 1), ((2, 0), (4, 1)))
        self.assertEqual(inv.line_ends(0, 0, 2, 3, 3, 1), ((2, 2), (2, 2)))

    def test_dispatch_gate(self):
        self.assertEqual(inv.dispatch_gate(0, True, 1, 0), "bad")
        self.assertEqual(inv.dispatch_gate(0x20, True, 0x11, 0), "gate")
        self.assertEqual(inv.dispatch_gate(0x14, True, 0x11, 0), "handler")
        self.assertEqual(inv.dispatch_gate(0x41, True, 0x11, 0), "handler")

if __name__ == "__main__":
    unittest.main()
